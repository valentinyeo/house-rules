"""Scopes: the board, or board view, one lead owns, and the workers that build its tickets."""
import json
import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCOPES = {k: v for k, v in json.loads((HERE / "scopes.json").read_text()).items() if not k.startswith("_")}
VIEW_CACHE = {}


def get(key):
    key = str(key)
    if key not in SCOPES:
        raise SystemExit(f"unknown scope {key}: add it to scopes.json ({', '.join(SCOPES)})")
    return dict(SCOPES[key], key=key)


def for_board(board):
    return [k for k, s in SCOPES.items() if s["board"] == int(board)]


def sessions():
    return set(subprocess.run(["tmux", "ls", "-F", "#S"], capture_output=True, text=True).stdout.split())


def _pattern(agent):
    return re.compile(re.escape(agent).replace(r"\{n\}", r"(\d+)").replace(r"\{x\}", r"([a-z])"), re.I)


def _state_rows(path, agent=None):
    try:
        data = json.loads(Path(os.path.expanduser(path)).read_text())
    except (OSError, ValueError):
        return []
    rows = data.items() if isinstance(data, dict) else enumerate(data)
    # mp-runners/runners.json names the pane "tmux", older state files "session".
    # Its "name" is the display tab ("[MB] Runner 1"); the board login comes from the
    # scope's "agent" template ("MP Runner {n}", {n} = the row's key) when given.
    rows = [dict(r, key=str(k), session=r.get("session") or r.get("tmux")) for k, r in rows if isinstance(r, dict)]
    return [r for r in rows if r["session"] and (r.get("name") or agent)]


POOL = []


def pool_live():
    """The shared pool's runners that work right now, as fleet/pick sees them: the pacer has not stopped Runner N, or it
    still runs the ticket it had when the stop came. A tmux session alone is no worker: stopped runners keep theirs."""
    if not POOL:
        from importlib.machinery import SourceFileLoader
        pick = SourceFileLoader("fleet_pick", str(HERE.parents[2] / "fleet" / "pick")).load_module()
        POOL.append({f"runner {n}" for n in range(1, pick.RUNNERS + 1) if pick.live_runner(f"runner {n}")})
    return POOL[0]


def workers(scope, live_sessions=None):
    """Returns (patterns that name a worker, live worker names lowered, always-on names lowered)."""
    live_sessions = sessions() if live_sessions is None else live_sessions
    patterns, live, always = [], set(), set()
    for w in scope["workers"]:
        if w.get("pool"):
            patterns.append(_pattern(w["agent"]))
            live |= pool_live()
            continue
        if w.get("state"):
            for r in _state_rows(w["state"], w.get("agent")):
                name = w["agent"].replace("{n}", r["key"]) if w.get("agent") else r["name"]
                patterns.append(_pattern(name))
                if r["session"] in live_sessions:
                    live.add(name.lower())
            continue
        patterns.append(_pattern(w["agent"]))
        if w.get("always"):
            always.add(w["agent"].lower())
        elif w.get("tmux"):
            if w["tmux"] in live_sessions:
                live.add(w["agent"].lower())
        else:
            for s in live_sessions:
                m = re.fullmatch(re.escape(w["tmux_prefix"]) + r"(\d+|[a-z])", s)
                if m:
                    live.add(w["agent"].replace("{n}", m.group(1)).replace("{x}", m.group(1).upper()).lower())
    return patterns, live, always


def is_worker(name, patterns):
    return any(p.fullmatch(name or "") for p in patterns)


def view_labels(scope, ht):
    """Label ids of the scope's view filter (views match ANY label), or None for a whole board."""
    view = scope.get("view")
    if not view:
        return None
    if view not in VIEW_CACHE:
        d = ht("view", "get", view)
        v = d.get("view", d)
        ids = {p["id"] for f in (v.get("board_filters") or {}).get("addedFilters") or []
               if f.get("type") == "Labels" for p in f.get("searchPayload") or []}
        VIEW_CACHE[view] = ids
    return VIEW_CACHE[view]


def in_view(task, labels):
    return labels is None or bool(labels & {l.get("id") for l in task.get("labels") or []})
