#!/usr/bin/env python3
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile


SKILL = """---
name: house-rules
description: Load and apply the local house rules at session start or when asked.
---

# /house-rules

1. Read all of `~/.local/share/house-rules/house-rules.md`.
2. Apply its voice, models, security and release rules.
3. Complete any missing Start here steps.
4. Confirm: `house rules loaded, <newest rule date>`.

This read-only copy updates every five minutes.
Never run git pull or request GitHub access.
Never edit this copy; changes need a source PR.
"""

SECRET = re.compile(
    r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\b(?:sk|rk)[-_](?:live_|test_|ant-|proj-)?[A-Za-z0-9_-]{20,}"
    r"|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"
    r"|\bxox[abposr]-[A-Za-z0-9-]{10,}"
    r"|\bAIza[A-Za-z0-9_-]{35}"
    r"|\b\d{8,12}:AA[A-Za-z0-9_-]{30,}"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|(?i:\b(?:api[_ -]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_+/=-]{16,})"
)


def filtered(text):
    output = []
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line
        if line.startswith("Path:"):
            continue
        if section == "## Start here: new session" and re.match(r"[145]\. ", line):
            continue
        if section == "## Between managers" and ("Poteto" in line or "/runner-update" in line):
            continue
        output.append(line)
    return "\n".join(output) + "\n"


def publish(source, destination):
    text = (source / "house-rules.md").read_text()
    source_skill = (source / "skills/house-rules/SKILL.md").read_text()
    if not text.strip() or "# House rules" not in text:
        raise ValueError("Missing house rules")
    if SECRET.search(text) or SECRET.search(source_skill) or SECRET.search(SKILL):
        raise ValueError("Secret pattern detected; previous copy retained")
    rules = filtered(text)
    digest = hashlib.sha256((rules + SKILL).encode()).hexdigest()
    destination.mkdir(mode=0o755, parents=True, exist_ok=True)
    release = destination / digest
    if not release.exists():
        with tempfile.TemporaryDirectory(dir=destination) as temporary:
            stage = Path(temporary) / "release"
            (stage / "skills/house-rules").mkdir(parents=True)
            (stage / "house-rules.md").write_text(rules)
            (stage / "skills/house-rules/SKILL.md").write_text(SKILL)
            for path in stage.rglob("*"):
                path.chmod(0o755 if path.is_dir() else 0o644)
            stage.chmod(0o755)
            stage.rename(release)
    link = destination / ".current"
    link.unlink(missing_ok=True)
    link.symlink_to(digest, target_is_directory=True)
    link.replace(destination / "current")
    print(f"INNE_SYNC_OK digest={digest}")


if __name__ == "__main__":
    source = Path("/home/valentin/.local/state/house-rules-inne-source")
    subprocess.run([
        "runuser", "-u", "valentin", "--", "git", "-c",
        "credential.helper=!/home/valentin/.local/bin/gh auth git-credential",
        "-C", str(source), "pull", "--ff-only", "--quiet",
    ], check=True)
    publish(source, Path("/var/lib/house-rules-inne"))
