"""Roster data: the static rows in roster.json plus what live sessions announced about themselves (HYCI-214).

roster.json holds decisions and changes only by PR. Announcements are observations: one JSON file per session under
~/.local/state/roster/announce/ (ROSTER_ANNOUNCE_DIR overrides), written by fleet/roster-announce. Separate files, so
concurrent session starts never write the same file and the synced house-rules checkout stays clean.

Session discovery covers both shapes on this VPS: tmux panes that run an agent (claude, hax, codex, cursor-agent)
and Multibot hosted chats (agent-host config whose tmux session is alive; the agent may be idle-stopped).
"""
import importlib.util
import json
import os
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path.home()
ROSTER = HERE / "roster.json"
ANNOUNCE = Path(os.environ.get("ROSTER_ANNOUNCE_DIR", HOME / ".local/state/roster/announce"))
MP_SEND = HOME / ".local/share/multiprompt-talk/mp_send.py"
AGENT = re.compile(r"(^|/)(claude|hax|codex|cursor-agent)( |$)")
FIELDS = ("name", "multibot", "tmux", "sid", "cwd", "kind", "board", "view", "app", "client", "harness", "take")


def static_rows():
    return json.loads(ROSTER.read_text())["rows"]


def pattern(name):
    return re.compile("^" + re.escape(name).replace(r"\{n\}", r"\d+").replace(r"\{x\}", "[a-z]") + "$")


def row_for(rows, tmux=None, name=None):
    """The static row a session belongs to: pinned tmux first, then the row name as a tmux pattern, then the
    Multibot chat name. None when nothing matches."""
    for r in rows:
        if tmux and r.get("tmux") == tmux:
            return r
    for r in rows:
        if tmux and pattern(r["name"]).match(tmux):
            return r
    for r in rows:
        if name and r.get("multibot") and r["multibot"].casefold() == name.casefold():
            return r
    return None


def key_of(entry):
    raw = entry.get("tmux") or entry.get("sid") or entry.get("name") or ""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", raw)[:80]


def announced():
    out = []
    for f in sorted(ANNOUNCE.glob("*.json")) if ANNOUNCE.is_dir() else []:
        try:
            out.append(json.loads(f.read_text()))
        except (OSError, ValueError):
            continue
    return out


def write_announce(entry):
    """Idempotent upsert of one session's file: same session, same file, newest fields win."""
    key = key_of(entry)
    if not key:
        raise ValueError("announce needs a tmux session, a session id or a name")
    ANNOUNCE.mkdir(parents=True, exist_ok=True)
    path = ANNOUNCE / f"{key}.json"
    try:
        old = json.loads(path.read_text())
    except (OSError, ValueError):
        old = {}
    merged = dict(old, **{k: v for k, v in entry.items() if v is not None})
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(merged, indent=1, sort_keys=True))
    os.replace(tmp, path)
    return merged


def rows():
    """Static rows plus announced sessions that no static row covers, as rows of the same shape."""
    static = static_rows()
    extra = []
    for a in announced():
        if row_for(static, a.get("tmux"), a.get("multibot")) is None:
            extra.append(dict({k: a.get(k) for k in FIELDS}, name=a.get("name") or a.get("tmux") or a.get("sid"),
                              status="announced", seen=a.get("seen")))
    return static + extra


def _mp_send():
    spec = importlib.util.spec_from_file_location("mp_send", MP_SEND)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chat_state(state, alive):
    """busy while a turn is in flight, idle while the agent waits, stopped when the host idle-stopped it."""
    if not alive:
        return "stopped"
    return "busy" if state.get("inflight") else "idle"


def hosted_chats():
    """Every enabled Multibot chat whose tmux session is alive, keyed by tmux, including idle-stopped agents.
    mp_send.live_chats() drops stopped ones; a send still reaches them because dispatch restarts the host."""
    mp = _mp_send()
    names, sessions, best = mp.published_names(), mp.tmux_names() or set(), {}
    for config_path in sorted((mp.state_root() / "agent-host").glob("*.config.json")):
        config = mp.read_json(config_path)
        state = mp.read_json(config_path.with_name(config_path.name[: -len(".config.json")] + ".state.json"))
        if not config or not state or config.get("enabled") is False:
            continue
        tmux, sid, provider = config.get("tmux"), state.get("sid"), state.get("provider")
        if not isinstance(tmux, str) or tmux not in sessions or not isinstance(sid, str) or provider not in mp.PROVIDERS:
            continue
        started = state.get("started") if isinstance(state.get("started"), (int, float)) else 0
        if tmux in best and started < best[tmux]["started"]:
            continue
        best[tmux] = dict(tmux=tmux, sid=sid, provider=provider, name=names.get(tmux), cwd=config.get("cwd"),
                          state=chat_state(state, mp.pid_alive(state.get("pid"))), started=started)
    return best


def tmux_agents():
    """tmux sessions with an agent process under one of their panes: {session: harness}."""
    ps = subprocess.run(["ps", "-eo", "pid=,ppid=,args="], capture_output=True, text=True).stdout.splitlines()
    kids, args = {}, {}
    for line in ps:
        parts = line.split(None, 2)
        if len(parts) == 3:
            kids.setdefault(int(parts[1]), []).append(int(parts[0]))
            args[int(parts[0])] = parts[2]

    def harness(pid):
        stack = [pid]
        while stack:
            p = stack.pop()
            m = AGENT.search(args.get(p, ""))
            if m:
                return m.group(2)
            stack += kids.get(p, [])
        return None

    panes = subprocess.run(["tmux", "list-panes", "-a", "-F", "#{session_name} #{pane_pid}"],
                           capture_output=True, text=True).stdout.split("\n")
    out = {}
    for line in panes:
        if line.strip():
            s, pid = line.split()
            h = harness(int(pid))
            if h:
                out[s] = h
    return out


def live_sessions():
    """[{tmux, name, sid, harness, via}] for every agent session alive on this VPS now."""
    chats = hosted_chats()
    out = [dict(tmux=t, name=c["name"], sid=c["sid"], harness=c["provider"], via="multibot") for t, c in chats.items()]
    out += [dict(tmux=t, name=None, sid=None, harness=h, via="tmux") for t, h in tmux_agents().items() if t not in chats]
    return out


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
