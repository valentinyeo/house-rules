#!/usr/bin/env python3
"""Check a Figma design frame against the app's LIVE code, so a design never invents values.

Usage:
  ds-check.py --repo ~/projects/multiprompt --files src/workspace_switcher.zig --frame frame.json

frame.json comes from the dump snippet in ../SKILL.md ("Check values against live code").
Code is read from the remote default branch after a fetch, never the local checkout.
Exit 1 when any frame radius or colour is not used in the touched files or the theme files.
"""
import argparse
import json
import re
import subprocess
import sys

THEME_FILES = ["src/themes.zig", "src/app_state.zig", "src/chat_style.zig"]
RADIUS_LINE = re.compile(r"radius|RoundRect|RADIUS|CornerShape|CircleShape", re.I)
RADIUS_NUM = re.compile(r"(?:scale|uiScaled|scaled)\((\d+)\)|RADIUS\s*[:=][^=]*?(\d+)\s*;|radius:\s*i32\s*=\s*(\d+)|RoundedCornerShape\((\d+)\.dp\)|(?:topStart|topEnd|bottomStart|bottomEnd)\s*=\s*(\d+)\.dp")
PILL_HEIGHT = re.compile(r"height\((\d+)\.dp\)[^\n]*CircleShape")
RGB = re.compile(r"RGB\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
HEX = re.compile(r"(?:#|0x[fF]{2})([0-9a-fA-F]{6})\b")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def live_source(repo, path, ref):
    try:
        return git(repo, "show", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        return ""


def radii(text):
    found = set()
    for line in text.splitlines():
        if RADIUS_LINE.search(line):
            for m in RADIUS_NUM.finditer(line):
                found.add(int(next(g for g in m.groups() if g)))
            for m in PILL_HEIGHT.finditer(line):
                found.add(int(m.group(1)) // 2)
    return found


def colours(text):
    found = {"%02x%02x%02x" % tuple(int(x) for x in m.groups()) for m in RGB.finditer(text)}
    found |= {m.group(1).lower() for m in HEX.finditer(text)}
    return found


def near(hex_value, palette, tol):
    r, g, b = (int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
    for p in palette:
        pr, pg, pb = (int(p[i:i + 2], 16) for i in (0, 2, 4))
        if max(abs(r - pr), abs(g - pg), abs(b - pb)) <= tol:
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--files", nargs="+", required=True, help="source files the design touches")
    ap.add_argument("--frame", required=True, help="JSON dump of the Figma frame")
    ap.add_argument("--ignore", nargs="*", default=[], help="node name substrings to skip, e.g. Today")
    ap.add_argument("--tol", type=int, default=3)
    a = ap.parse_args()

    git(a.repo, "fetch", "-q", "origin")
    ref = git(a.repo, "rev-parse", "--abbrev-ref", "origin/HEAD").strip()
    stamp = git(a.repo, "log", "-1", "--format=%h %cd", "--date=short", ref).strip()

    touched = "".join(live_source(a.repo, f, ref) for f in a.files)
    theme = "".join(live_source(a.repo, f, ref) for f in THEME_FILES)
    code_radii = radii(touched) | radii(theme) | {0}
    # Corners are per component, so only the touched files count; colours are app-wide tokens.
    ext = a.files[0].rsplit(".", 1)[-1]
    app_src = git(a.repo, "grep", "-h", "-E", r"RGB\(|#[0-9a-fA-F]{6}|0x[fF]{2}[0-9a-fA-F]{6}", ref, "--", f"*.{ext}")
    palette = colours(app_src)

    nodes = json.load(open(a.frame))
    bad = []
    for n in nodes:
        if any(s in n.get("path", "") for s in a.ignore):
            continue
        r = n.get("radius")
        if r is not None and round(r) not in code_radii:
            bad.append(f"radius {r} on {n['path']} is not in live code (live: {sorted(code_radii)})")
        for f in n.get("fills", []):
            if not near(f.lower(), palette, a.tol):
                bad.append(f"colour #{f} on {n['path']} is not in live code")

    print(f"live code: {ref} {stamp}; files: {', '.join(a.files)}")
    print(f"checked {len(nodes)} nodes; radii in code: {sorted(code_radii)}")
    if bad:
        print(f"FAIL: {len(bad)} invented or changed values. Each needs a named reason and Valentin's yes, or must match code.")
        for line in sorted(set(bad)):
            print("  " + line)
        sys.exit(1)
    print("PASS: every radius and colour in the frame exists in live code.")


if __name__ == "__main__":
    main()
