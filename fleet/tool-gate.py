#!/usr/bin/env python3
"""Self-test fleet tools on change; keep last-known-good copies (YPER4-1386).

    python3 fleet/tool-gate.py pick [--json]     # path to runnable pick on stdout
    python3 fleet/tool-gate.py --self-test       # built-in self tests for gated tools

pick: when fleet/pick changes, run fleet/pick --self-test. Pass promotes the copy to
~/.local/state/fleet-pick/lkg/pick and records pick-lkg.sha under FLEET_RUNNER_STATE.
Fail keeps the last copy, files one checks-board incident per bad sha, runners keep picking.
"""
import hashlib
import json
import os
import shutil
import tempfile
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PICK_SRC = Path(os.environ.get("FLEET_PICK_SOURCE", str(HERE / "pick")))
LKG_DIR = Path(os.environ.get("FLEET_PICK_LKG", Path.home() / ".local/state/fleet-pick/lkg"))
LKG_PICK = LKG_DIR / "pick"
RUNNER_STATE = Path(os.environ.get("FLEET_RUNNER_STATE", Path.home() / ".local/state/ht-or-runners"))
FSW = Path(os.environ.get("FLEET_WATCH_STATE", Path.home() / ".local/state/fleet-switch"))
CI_BOARD = "11514"


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def note(msg):
    print(msg, file=sys.stderr)
    os.makedirs(FSW, exist_ok=True)
    with open(FSW / "log.txt", "a") as f:
        f.write(f"{stamp()} tool-gate: {msg}\n")


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_self_test(script, extra=()):
    r = subprocess.run(
        [sys.executable, str(script), *extra],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(REPO),
    )
    tail = (r.stderr or r.stdout or "").strip()[-400:]
    return r.returncode == 0, tail


def ci_vcc(*args):
    env = dict(os.environ, SHIP_SESSION_NAME="Chief Of Staff", PATH=os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", ""))
    return subprocess.run(["vcc", *args], capture_output=True, text=True, env=env, timeout=300)


def file_broken_picker_incident(sha, detail):
    body = (
        "<h2>Problem</h2><ul>"
        "<li>A new fleet/pick copy failed its self-test.</li>"
        f"<li>Runners rolled back to the last good copy (sha {sha[:12]}).</li></ul>"
        f"<h2>Fix</h2><ul><li>Repair fleet/pick and merge to house-rules.</li>"
        f"<li>Detail: {detail[:500]}</li></ul>"
        "<h2>Done when</h2><ul><li>fleet/pick --self-test passes on main.</li>"
        "<li>broken-picker drill passes.</li></ul>"
        "<h2>Risk</h2><ul><li>A good picker fix waits on the repair.</li></ul>"
        "<h2>Decision</h2><p>None.</p>")
    dedupe = FSW / "broken-picker-incident.json"
    try:
        last = json.loads(dedupe.read_text()).get("sha", "")
    except (OSError, ValueError):
        last = ""
    if last == sha:
        note(f"broken-picker: incident already filed for sha {sha[:12]}")
        return
    path = FSW / "broken-picker.html"
    os.makedirs(FSW, exist_ok=True)
    path.write_text(body)
    title = f"Picker self-test failed; rolled back (sha {sha[:12]})"
    r = ci_vcc(
        "task", "create", "--project", CI_BOARD, "--title", title, "--description-file", str(path),
        "--priority", "urgent", "--labels", "CI,Hypertask CI,incident,brain-medium", "--section", "Backlog",
    )
    if r.returncode == 0:
        json.dump({"sha": sha, "at": time.time()}, open(dedupe, "w"))
        note(f"broken-picker: filed {title}")
    else:
        note(f"broken-picker: file failed {(r.stderr or r.stdout)[-160:]}")


def promote_lkg(sha):
    LKG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PICK_SRC, LKG_PICK)
    shutil.copy2(PICK_SRC.with_name("ticket_owner.py"), LKG_DIR / "ticket_owner.py")
    os.chmod(LKG_PICK, 0o755)
    RUNNER_STATE.mkdir(parents=True, exist_ok=True)
    (RUNNER_STATE / "pick-lkg.sha").write_text(sha + "\n")


def ensure_pick(as_json=False):
    if not PICK_SRC.is_file():
        note(f"pick gate: missing source {PICK_SRC}")
        return 1
    owner_src = PICK_SRC.with_name("ticket_owner.py")
    dependency_sha = file_sha(owner_src) if owner_src.is_file() else "missing ticket_owner.py"
    sha = hashlib.sha256((file_sha(PICK_SRC) + dependency_sha).encode()).hexdigest()
    lkg_sha = ""
    lkg_path = RUNNER_STATE / "pick-lkg.sha"
    if lkg_path.exists():
        lkg_sha = lkg_path.read_text().strip()
    if lkg_sha == sha and LKG_PICK.exists():
        out = str(LKG_PICK)
        if as_json:
            print(json.dumps({"path": out, "sha": sha, "rolled_back": False}))
        else:
            print(out)
        return 0
    with tempfile.TemporaryDirectory() as alone:
        served = Path(alone) / "pick"
        shutil.copy2(PICK_SRC, served)
        if owner_src.is_file():
            shutil.copy2(owner_src, Path(alone) / "ticket_owner.py")
            ok, detail = run_self_test(served, ("--self-test",))
        else:
            ok, detail = False, "missing ticket_owner.py"
    if ok:
        promote_lkg(sha)
        out = str(LKG_PICK)
        if as_json:
            print(json.dumps({"path": out, "sha": sha, "rolled_back": False, "promoted": True}))
        else:
            print(out)
        return 0
    if not LKG_PICK.exists():
        note(f"pick gate: self-test failed and no lkg: {detail}")
        return 1
    bad_path = RUNNER_STATE / "pick-bad.sha"
    last_bad = bad_path.read_text().strip() if bad_path.exists() else ""
    if sha != last_bad:
        file_broken_picker_incident(sha, detail)
        bad_path.write_text(sha + "\n")
    out = str(LKG_PICK)
    if as_json:
        print(json.dumps({"path": out, "sha": lkg_sha, "rolled_back": True, "bad_sha": sha}))
    else:
        print(out)
    note(f"pick gate: rolled back to lkg {lkg_sha[:12]} (bad {sha[:12]})")
    return 0


def gate_self_test():
    checks = [
        (HERE / "pick", ("--self-test",)),
        (HERE / "park", ("--self-test",)),
        (HERE / "runner-state.py", ("--self-test",)),
    ]
    slo = HERE / "slo-watch.py"
    if slo.is_file():
        checks.append((slo, ("--self-test",)))
    failed = []
    for script, extra in checks:
        ok, detail = run_self_test(script, extra)
        if not ok:
            failed.append(f"{script.name}: {detail}")
    if failed:
        for line in failed:
            print(line, file=sys.stderr)
        return 1
    print("fleet/tool-gate self-test ok")
    return 0


def main():
    args = sys.argv[1:]
    if args == ["--self-test"]:
        sys.exit(gate_self_test())
    if not args or args[0] != "pick":
        sys.exit("usage: fleet/tool-gate.py pick [--json] | fleet/tool-gate.py --self-test")
    as_json = "--json" in args[1:]
    sys.exit(ensure_pick(as_json=as_json))


if __name__ == "__main__":
    main()
