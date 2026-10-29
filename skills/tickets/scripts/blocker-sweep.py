#!/usr/bin/env python3
"""Read-only. Lists blocked tickets that drifted on the given boards.

usage: blocker-sweep.py <boardId> [<boardId> ...] [--owner "Valentin Yeo"]

Prints one line per blocked ticket:
  ANSWERED     the owner replied or reacted after the marked comment: clear it now
  NO-QUESTION  the marked comment has no "Question:": clear it or post one
  WAITING      a real open question: leave it
"""
import json, re, subprocess, sys

args = sys.argv[1:]
owner = "Valentin Yeo"
if "--owner" in args:
    i = args.index("--owner")
    owner = args[i + 1]
    del args[i:i + 2]
if not args:
    sys.exit(__doc__)


def cli(*a):
    r = subprocess.run(["hypertask", *a, "--json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {}


def text(s):
    return re.sub(r"<[^>]+>", " ", s or "").strip()


def by_owner(c):
    return not c.get("agent") and (c.get("creator") or {}).get("displayName") == owner


counts = {"ANSWERED": 0, "NO-QUESTION": 0, "WAITING": 0}
for board in args:
    tasks, offset = [], 0
    while True:
        page = cli("task", "list", "--project", board, "--limit", "200", "--offset", str(offset)).get("tasks", [])
        tasks += page
        if len(page) < 200:
            break
        offset += 200
    for t in tasks:
        marked = t.get("blockerCommentId")
        if not marked:
            continue
        cs = cli("comments", "list", t["ticketNumber"])
        cs = sorted(cs.get("comments", []) if isinstance(cs, dict) else cs, key=lambda c: c.get("createdAt", ""))
        q = next((c for c in cs if c.get("id") == marked), {})
        after = [c for c in cs if c.get("createdAt", "") > q.get("createdAt", "") and by_owner(c)]
        reacted = any((r.get("user") or {}).get("displayName") == owner for r in q.get("reactions") or [])
        if after or reacted:
            kind = "ANSWERED"
        elif "Question:" not in text(q.get("text")):
            kind = "NO-QUESTION"
        else:
            kind = "WAITING"
        counts[kind] += 1
        reply = text(after[-1]["text"])[:120] if after else ("reacted" if reacted else "")
        print(f"{kind}\t{t['ticketNumber']}\t{t.get('id')}\tcomment {marked}\t{t.get('title', '')[:60]}\t{reply}")
print(" ".join(f"{k}={v}" for k, v in counts.items()), file=sys.stderr)
