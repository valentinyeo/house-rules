#!/usr/bin/env python3
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import time


def atomic_write(path, text):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "check", "end"))
    parser.add_argument("--role", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--context", type=int)
    parser.add_argument("--handover", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", args.role):
        parser.error("role must be lowercase words joined by hyphens")
    if not args.session.strip() or "\n" in args.session:
        parser.error("session must be a nonempty single line")
    if args.action == "check" and (args.context is None or args.context < 0):
        parser.error("check needs a nonnegative --context token count")
    root = Path.home() / ".local/state/manager-shifts"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / f"{args.role}.json"
    handover = Path.home() / "poteto-handover" / f"{args.role}-shift.md"
    with (root / f"{args.role}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(path.read_text()) if path.exists() else None
        if args.action == "start":
            if state and not state["closed"]:
                if state["session"] != args.session:
                    raise ValueError("active shift belongs to another session; hand over first")
                print("shift already active; age preserved")
                return 0
            if state:
                print(handover.read_text())
                if state["session"] == args.session:
                    raise ValueError("clear context and use a fresh session id before restarting")
            atomic_write(path, json.dumps({"session": args.session, "started": time.time(),
                                           "context": 0, "closed": False}))
            print("shift started; read current board before work")
            return 0
        if not state or state["session"] != args.session:
            raise ValueError("no active shift for this session")
        if args.action == "end":
            if not args.handover:
                parser.error("end needs --handover FILE")
            text = args.handover.read_text()
            sections = re.split(r"(?m)^## ", text)
            contents = {section.partition("\n")[0]: section.partition("\n")[2].strip()
                        for section in sections[1:]}
            for heading in ("Role", "Open work", "Decisions", "Next actions", "Last digest"):
                if not contents.get(heading):
                    raise ValueError(f"handover needs a nonempty ## {heading} section")
            handover.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_write(handover, text)
            state["closed"] = True
            atomic_write(path, json.dumps(state))
            print(f"handover saved: {handover}; clear this session now")
            return 0
        if state["closed"]:
            raise ValueError("shift ended; clear context before resuming")
        state["context"] = max(state["context"], args.context)
        atomic_write(path, json.dumps(state))
        if state["context"] >= 120000 or time.time() - state["started"] >= 14400:
            print("HANDOVER REQUIRED: stop new work; save handover, then clear")
            return 3
        print("WARN: prepare handover" if state["context"] >= 100000 else "shift ok")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"shift refused: {error}")
        raise SystemExit(1)
