"""Column and owner of a Software Factory ticket, derived from one event.

The table is the whole machine. A worker start, a pull request, and a verifier
verdict all go through it, so the column does not depend on an agent remembering.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BOARD = 2060
FORBIDDEN_BOARDS = {15, 4060}

# section, what to do with assignees: sole (this agent only, humans stay),
# keep, or clear (nobody left on the ticket).
EVENTS = {
    "start": ("Doing", "sole"),
    "pr_opened": ("AI Review", "keep"),
    "verifier_pass": ("Valentin Review", "keep"),
    "pr_merged": ("Done", "keep"),
    "pr_closed": ("Todo", "clear"),
}

KEY = re.compile(
    r"\b(?!(?:UTF|SHA|ISO|GPT|RFC|CVE|ES|TLS|HTTP)-)"
    r"([A-Z][A-Z0-9]{1,9})-(\d+)\b"
)
BRANCH_KEY = re.compile(r"(?:^|[/_])([A-Za-z][A-Za-z0-9]{1,9})-(\d+)(?=$|[/_-])")
NOT_A_TICKET = {"UTF", "SHA", "ISO", "GPT", "RFC", "CVE", "ES", "TLS", "HTTP"}
VERDICT_PASS = re.compile(r"(?i)^PASS(\+NOTES)?\b")
SEGMENT = re.compile(r"&&|\|\||[;|\n]|\$\(")
PREFIX = re.compile(r"^(?:\s*(?:[A-Z_][A-Z0-9_]*=\S*|timeout\s+\S+|nohup|exec|env|sudo)\s+)*")
WORKER_HEAD = re.compile(
    r"^(?:\S*/)?(?:spawn-worker|cursor-agent|hax)\s+\S|"
    r"^(?:\S*/)?codex\s+exec\b|"
    r"^(?:\S*/)?pi\s+(?:.*\s)?(?:-p|--print)\b"
)
BRIEF = re.compile(r"\$\(\s*cat\s+([^\s)]+)\s*\)")


def ticket_key(text):
    """First uppercase ticket key in text, or None."""
    match = KEY.search(text or "")
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def ticket_key_branch(ref):
    """Ticket key written into a branch name, any case. `soft-9-fix` is SOFT-9."""
    match = BRANCH_KEY.search(ref or "")
    if not match or match.group(1).upper() in NOT_A_TICKET:
        return None
    return f"{match.group(1).upper()}-{match.group(2)}"


def ticket_from_pr(head, title, body):
    return ticket_key_branch(head) or ticket_key(title) or ticket_key(body)


def _heads(cmd):
    for seg in SEGMENT.split(cmd or ""):
        yield PREFIX.sub("", seg.strip().lstrip("({ "))


def _command_name(head):
    token = (head or "").split()[:1]
    if not token:
        return ""
    return token[0].rsplit("/", 1)[-1]


def worker_ticket(cmd):
    """Ticket to claim after a worker start that is not spawn-worker.

    spawn-worker claims itself. A dry run, a help line, or an explicit
    NO_TICKET_REASON does not claim.
    """
    if not cmd or "NO_TICKET_REASON=" in cmd or "--dry-run" in cmd or "--help" in cmd:
        return None
    heads = list(_heads(cmd))
    if any(_command_name(head) == "spawn-worker" for head in heads):
        return None
    if not any(WORKER_HEAD.search(head) for head in heads):
        return None
    extra = []
    for path in BRIEF.findall(cmd):
        try:
            extra.append(Path(path).expanduser().read_text(errors="ignore")[:20000])
        except OSError:
            pass
    return ticket_key(cmd + "\n" + "\n".join(extra))


def plan_github(event_name, payload):
    """(event, ticket) for a GitHub webhook payload, or None when nothing moves."""
    if not isinstance(payload, dict):
        return None
    if event_name == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request") or {}
        if not isinstance(pr, dict):
            return None
        head = (pr.get("head") or {}).get("ref") if isinstance(pr.get("head"), dict) else None
        key = ticket_from_pr(head, pr.get("title"), pr.get("body"))
        if not key:
            return None
        if action in ("opened", "reopened"):
            return "pr_opened", key
        if action == "closed":
            return ("pr_merged" if pr.get("merged") else "pr_closed"), key
        return None
    if event_name == "check_run":
        run = payload.get("check_run") or {}
        if not isinstance(run, dict):
            return None
        if run.get("name") != "pstack-verifier" or run.get("conclusion") != "success":
            return None
        for pr in run.get("pull_requests") or []:
            if not isinstance(pr, dict):
                continue
            head = (pr.get("head") or {}).get("ref") if isinstance(pr.get("head"), dict) else None
            key = ticket_from_pr(head, pr.get("title"), None)
            if key:
                return "verifier_pass", key
        return None
    if event_name == "issue_comment" and payload.get("action") == "created":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        if not isinstance(issue, dict) or not issue.get("pull_request"):
            return None
        body = comment.get("body") if isinstance(comment, dict) else ""
        if not VERDICT_PASS.search((body or "").strip()):
            return None
        return _pair("verifier_pass", ticket_key(issue.get("title")) or ticket_key(issue.get("body")))
    return None


def _pair(event, key):
    if not key:
        return None
    return event, key


def _loads(stdout):
    try:
        return json.loads(stdout or "")
    except ValueError:
        return {}


def assignees_from(stdout):
    data = _loads(stdout)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    task = tasks[0] if isinstance(tasks, list) and tasks else data.get("task") if isinstance(data, dict) else None
    if not isinstance(task, dict):
        task = data if isinstance(data, dict) else {}
    rows = task.get("assignees") or []
    return [row for row in rows if isinstance(row, dict)]


def self_id_from(stdout):
    data = _loads(stdout)
    agent = data.get("connected_agent") if isinstance(data, dict) else None
    if not isinstance(agent, dict):
        return None
    value = agent.get("id") or agent.get("agentId")
    return str(value) if value else None


def hypertask_base():
    token = os.environ.get("HYPERTASK_TOKEN") or ""
    if token:
        return ["hypertask", "--token", token]
    return ["hypertask"]


def commands_for(event, ticket, rows, keep_id, explicit_agent):
    """Argv lists (without the token flag) that bring the ticket to this event."""
    section, policy = EVENTS[event]
    update = ["hypertask", "task", "update", ticket, "--section", section]
    if policy == "clear":
        return [update + ["--clear-assignees"]]
    if policy == "keep":
        return [update]
    out = [update]
    for row in rows:
        agent_id = row.get("agentId")
        if not agent_id:
            continue
        if keep_id and str(agent_id) == str(keep_id):
            continue
        out.append(["hypertask", "task", "unassign", ticket, "--agent", str(agent_id)])
    if explicit_agent:
        out.append(["hypertask", "task", "assign", ticket, "--agent", explicit_agent])
    else:
        out.append(["hypertask", "task", "assign", ticket, "--self"])
    return out


def _run(argv):
    """Run hypertask. The token, when set, is an argument and is never printed."""
    base = hypertask_base()
    full = base + argv[1:]
    done = subprocess.run(full, capture_output=True, text=True)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout or "").strip()
        token = os.environ.get("HYPERTASK_TOKEN") or ""
        if token:
            detail = detail.replace(token, "[redacted]")
        print(f"ticket-board: hypertask exited {done.returncode}: {detail}", file=sys.stderr)
    return done.returncode, done.stdout


def apply_event(event, ticket, agent=None, run=_run):
    if event not in EVENTS:
        print(f"ticket-board: unknown event {event}", file=sys.stderr)
        return 2
    if ticket_key(ticket) != ticket:
        print(f"ticket-board: {ticket} is not a ticket key", file=sys.stderr)
        return 2
    _, policy = EVENTS[event]
    rows = []
    keep_id = agent
    if policy == "sole":
        if not keep_id:
            code, out = run(["hypertask", "--json", "context"])
            if code != 0:
                return code
            keep_id = self_id_from(out)
        code, out = run(["hypertask", "--json", "task", "get", ticket])
        if code != 0:
            return code
        rows = assignees_from(out)
    for argv in commands_for(event, ticket, rows, keep_id, agent):
        code, _out = run(argv)
        if code != 0:
            return code
    return 0


def _views(run):
    offset = 0
    found = []
    total = None
    while total is None or offset < total:
        code, out = run(["hypertask", "--json", "view", "list", "--project", str(BOARD),
                         "--limit", "100", "--offset", str(offset)])
        if code != 0:
            return code, []
        data = _loads(out)
        page = data.get("views") if isinstance(data, dict) else None
        if not isinstance(page, list):
            return 1, []
        found.extend(page)
        total = data.get("total") if isinstance(data, dict) else None
        if not isinstance(total, int):
            break
        offset += len(page) or 100
        if not page:
            break
    return 0, found


def view_matches(views, name):
    want = name.strip().lower()
    for view in views:
        if not isinstance(view, dict):
            continue
        title = str(view.get("title") or "").strip().lower()
        slug = str(view.get("slug") or "").strip().lower()
        if want and want in (title, slug):
            return view
    return None


def ensure_view(name, agent, project=BOARD, run=_run):
    try:
        project_id = int(project)
    except (TypeError, ValueError):
        print(f"ticket-board: bad project {project}", file=sys.stderr)
        return 2
    if project_id in FORBIDDEN_BOARDS:
        print(f"ticket-board: board {project_id} is not ours", file=sys.stderr)
        return 2
    if project_id != BOARD:
        print(f"ticket-board: views for this command are on board {BOARD}", file=sys.stderr)
        return 2
    if not name or not agent:
        print("ticket-board: ensure-view needs a name and an agent id", file=sys.stderr)
        return 2
    code, views = _views(run)
    if code != 0:
        return code
    existing = view_matches(views, name)
    if existing:
        print(f"view {existing.get('slug') or name} already on board {BOARD}")
        return 0
    code, _out = run([
        "hypertask", "view", "create",
        "--project", str(BOARD),
        "--title", name,
        "--visibility", "Public",
        "--assignee", agent,
    ])
    if code != 0:
        return code
    print(f"view {name} created on board {BOARD}")
    return 0


def apply_github():
    token = os.environ.get("HYPERTASK_TOKEN") or ""
    if not token:
        print("HYPERTASK_TOKEN is not set. Board move skipped.")
        return 0
    event_name = os.environ.get("GITHUB_EVENT_NAME") or ""
    path = os.environ.get("GITHUB_EVENT_PATH") or ""
    if not path:
        print("ticket-board: no GitHub event payload. Board move skipped.")
        return 0
    try:
        payload = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        print(f"ticket-board: cannot read the GitHub event: {exc}", file=sys.stderr)
        return 0
    planned = plan_github(event_name, payload)
    if not planned:
        print(f"ticket-board: {event_name or 'event'} does not move a ticket")
        return 0
    event, ticket = planned
    print(f"ticket-board: {ticket} -> {EVENTS[event][0]}")
    return apply_event(event, ticket)


def claim_command(data):
    if not isinstance(data, dict):
        return 0
    tool = str(data.get("tool_name") or "")
    if tool not in ("Bash", ""):
        return 0
    inp = data.get("tool_input") or {}
    cmd = inp.get("command") if isinstance(inp, dict) else ""
    ticket = worker_ticket(cmd or "")
    if not ticket:
        return 0
    print(f"ticket-board: claim {ticket}", file=sys.stderr)
    return apply_event("start", ticket)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: ticket-board apply --event EVENT --ticket KEY [--agent UUID]")
        print("       ticket-board apply-github")
        print("       ticket-board claim-command")
        print("       ticket-board ensure-view --name NAME --agent UUID")
        return 0
    cmd = argv[0]
    if cmd == "apply-github":
        return apply_github()
    if cmd == "claim-command":
        try:
            data = json.load(sys.stdin)
        except ValueError:
            return 0
        return claim_command(data)
    if cmd == "apply":
        event = ticket = agent = None
        i = 1
        while i < len(argv):
            if argv[i] == "--event" and i + 1 < len(argv):
                event = argv[i + 1]
                i += 2
            elif argv[i] == "--ticket" and i + 1 < len(argv):
                ticket = argv[i + 1]
                i += 2
            elif argv[i] == "--agent" and i + 1 < len(argv):
                agent = argv[i + 1]
                i += 2
            else:
                print(f"ticket-board: unknown argument {argv[i]}", file=sys.stderr)
                return 2
        if not event or not ticket:
            print("ticket-board: apply needs --event and --ticket", file=sys.stderr)
            return 2
        return apply_event(event, ticket, agent)
    if cmd == "ensure-view":
        name = agent = None
        project = BOARD
        i = 1
        while i < len(argv):
            if argv[i] == "--name" and i + 1 < len(argv):
                name = argv[i + 1]
                i += 2
            elif argv[i] == "--agent" and i + 1 < len(argv):
                agent = argv[i + 1]
                i += 2
            elif argv[i] == "--project" and i + 1 < len(argv):
                project = argv[i + 1]
                i += 2
            else:
                print(f"ticket-board: unknown argument {argv[i]}", file=sys.stderr)
                return 2
        return ensure_view(name, agent, project)
    print(f"ticket-board: unknown command {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
