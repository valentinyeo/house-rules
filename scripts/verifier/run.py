#!/usr/bin/env python3
"""pstack verifier for house-rules.

DeepSeek Flash through Pi is the only model. The workflow passes this file and
brief.md from the base commit when that commit has them, so a pull request
cannot swap its judge. Any error fails closed. One comment per head sha, and
the process exit code is the check conclusion: 0 for PASS and PASS+NOTES, 1
for FAIL.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

PI_PACKAGE = "@earendil-works/pi-coding-agent@1.5.2"
PI_PROVIDER = "opencode-go"
PI_MODEL = "deepseek-v4.1-flash"
PI_THINKING = "medium"
LOGIN_VAR = "OPENCODE_API_KEY"
VERDICTS = ("PASS+NOTES", "PASS", "FAIL")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FIRST_LINE_RE = re.compile(r"^pstack-verifier: (PASS\+NOTES|PASS|FAIL) @ ([0-9a-f]{40})$")
TRAILER_RE = re.compile(
    r"(?im)^(co-authored-by|authored-by|signed-off-by|generated-by|made-by)\s*:\s*(.+?)\s*$"
)
AUTHOR_MODEL_RE = re.compile(r"(?im)^\s*author-model\s*:\s*(.+?)\s*$")
WROTE_RE = re.compile(
    r"(?i)(\b(deepseek|pi)\b[^\n]{0,80}\b(wrote|authored)\b|"
    r"\b(written|authored|co-authored)\s+by\s+\b(deepseek|pi)\b)"
)
FAMILY_RE = re.compile(r"(?i)deepseek|\bpi\b")
BIN_PATH_RE = re.compile(r"^bin/[A-Za-z0-9._/-]+$")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

REQUIRED_COMMANDS = (
    "python3 scripts/rules-lint --self-test",
    "python3 scripts/rules-lint house-rules.md",
    "python3 scripts/rules-lint --diff origin/main",
    "python3 -m unittest discover -s tests -q",
)

MODEL_TIMEOUT_S = 15 * 60
COMMAND_TIMEOUT_S = 10 * 60


class VerifierError(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def pi_command(brief_text):
    return [
        "npx", "-y", PI_PACKAGE,
        "-p",
        "--provider", PI_PROVIDER,
        "--model", PI_MODEL,
        "--thinking", PI_THINKING,
        brief_text,
    ]


def first_line(verdict, sha):
    if verdict not in VERDICTS:
        raise VerifierError("unknown verdict %s" % verdict)
    if not SHA_RE.match(sha or ""):
        raise VerifierError("head sha is not 40 lowercase hex characters")
    return "pstack-verifier: %s @ %s" % (verdict, sha)


def redact(text, secret):
    if not text:
        return ""
    out = text
    if secret and len(secret) >= 4:
        out = out.replace(secret, "[redacted]")
    return out


def norm_cmd(cmd):
    return re.sub(r"\s+", " ", (cmd or "").strip())


def trailers_say_same_family(message):
    return any(FAMILY_RE.search(match.group(2)) for match in TRAILER_RE.finditer(message or ""))


def body_says_same_family(body):
    text = body or ""
    for match in AUTHOR_MODEL_RE.finditer(text):
        if FAMILY_RE.search(match.group(1)):
            return True
    if trailers_say_same_family(text):
        return True
    return bool(WROTE_RE.search(text))


def same_family(commit_messages, pr_body):
    if body_says_same_family(pr_body):
        return True
    return any(trailers_say_same_family(message) for message in commit_messages)


def render_brief(template, mapping):
    out = template
    for key, value in mapping.items():
        out = out.replace("{{%s}}" % key, value)
    left = PLACEHOLDER_RE.findall(out)
    if left:
        raise VerifierError("brief still has placeholders: %s" % ", ".join(left))
    return out


def extract_json(text):
    decoder = json.JSONDecoder()
    best = None
    for index, char in enumerate(text or ""):
        if char != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "commands" in obj:
            best = obj
    if best is None:
        raise VerifierError("model answer has no JSON object with commands")
    return best


def _exit_code(row, cmd):
    if not isinstance(row, dict):
        raise VerifierError("command row is not an object")
    code = row.get("exit", row.get("exit_code"))
    if isinstance(code, bool) or not isinstance(code, int):
        raise VerifierError("exit code missing for %s" % cmd)
    return code


def _rows_by_cmd(rows, label):
    if rows is None:
        raise VerifierError("answer has no %s" % label)
    if not isinstance(rows, list):
        raise VerifierError("%s is not a list" % label)
    found = {}
    for row in rows:
        cmd = norm_cmd(row.get("cmd") if isinstance(row, dict) else "")
        if not cmd:
            raise VerifierError("a %s row has no cmd" % label)
        found[cmd] = row
    return found


def combine(ground, answer, bootstrap, extra_notes):
    """Ground-truth command exits decide command failure. The model must still report each command."""
    commands = _rows_by_cmd(answer.get("commands"), "commands")
    bins = answer.get("bin_scripts", [])
    if bins is None:
        bins = []
    bin_rows = _rows_by_cmd(bins, "bin_scripts")
    reasons = []
    for row in ground["commands"]:
        cmd = row["cmd"]
        if cmd not in commands:
            reasons.append("command not run: %s" % cmd)
        else:
            _exit_code(commands[cmd], cmd)
        if row["exit"] != 0:
            reasons.append("command failed: %s exit %s" % (cmd, row["exit"]))
    for row in ground["bin_scripts"]:
        cmd = row["cmd"]
        if cmd not in bin_rows:
            reasons.append("bin script not run: %s" % cmd)
        else:
            _exit_code(bin_rows[cmd], cmd)
        if row["flag"] == "--self-test" and row["exit"] != 0:
            reasons.append("bin self-test failed: %s exit %s" % (cmd, row["exit"]))
        elif row["flag"] == "--help" and row["exit"] not in (0, 1, 2):
            reasons.append("bin script did not run: %s exit %s" % (cmd, row["exit"]))
    rules = answer.get("rules")
    if not isinstance(rules, list):
        raise VerifierError("answer rules is not a list")
    unexplained = []
    explained = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise VerifierError("a rule row is not an object")
        quote = str(rule.get("quote") or "").strip()
        if not quote:
            raise VerifierError("a rule row has no quote")
        if rule.get("why_covers") is True:
            explained.append(quote)
        else:
            unexplained.append(quote)
    if unexplained:
        reasons.append("house rule lost or changed in meaning")
    mismatch = answer.get("goal_mismatch", "")
    if not isinstance(mismatch, str):
        raise VerifierError("goal_mismatch is not a string")
    if mismatch.strip():
        reasons.append("diff does not match the stated goal")
    notes = answer.get("notes", [])
    if notes is None:
        notes = []
    if isinstance(notes, str):
        notes = [notes] if notes.strip() else []
    if not isinstance(notes, list):
        raise VerifierError("notes is not a list")
    note_lines = [str(item).strip() for item in notes if str(item).strip()]
    note_lines.extend(extra_notes)
    for row in ground["bin_scripts"]:
        if row["flag"] == "--help" and row["exit"] != 0:
            note_lines.append("%s exited %s" % (row["cmd"], row["exit"]))
    if reasons:
        return "FAIL", reasons[0], note_lines, unexplained + explained
    if note_lines or explained or bootstrap:
        return "PASS+NOTES", "", note_lines, explained
    return "PASS", "", note_lines, explained


def comment_text(verdict, sha, reason, detail_lines):
    lines = [first_line(verdict, sha), ""]
    if reason == "same family":
        lines.append("same family")
        lines.append("")
        lines.append(
            "The pull request commits or body say DeepSeek or Pi wrote the change. "
            "This verifier is DeepSeek through Pi, so it does not check its own family. "
            "Grok and Codex are not available on GitHub yet."
        )
    elif reason:
        lines.append("Reason: %s" % reason)
    for line in detail_lines:
        if lines[-1] != "" and line == "":
            lines.append("")
        elif line != "" or lines[-1] != "":
            lines.append(line)
    text = "\n".join(lines).rstrip() + "\n"
    if len(text) > 60000:
        text = text[:60000] + "\n\n(truncated)\n"
    return text


def verdict_of(text):
    line = (text or "").splitlines()[0].strip() if text else ""
    match = FIRST_LINE_RE.match(line)
    if not match:
        raise VerifierError("comment first line is not a verdict")
    return match.group(1), match.group(2)


def comment_id_for_sha(comments, sha):
    found = None
    for comment in comments:
        body = comment.get("body") or ""
        line = body.splitlines()[0].strip() if body else ""
        match = FIRST_LINE_RE.match(line)
        if match and match.group(2) == sha:
            found = comment.get("id")
    return found


def bin_plan(head_dir, paths):
    planned = []
    notes = []
    for path in paths:
        if not BIN_PATH_RE.match(path):
            raise VerifierError("unsafe bin path: %s" % path)
        full = Path(head_dir) / path
        if not full.is_file():
            notes.append("%s is not a file on the head commit, so it was not run" % path)
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        flag = "--self-test" if "--self-test" in text else "--help"
        planned.append({"path": path, "cmd": "%s %s" % (path, flag), "flag": flag})
    return planned, notes


def run_one(cmd, cwd, timeout):
    proc = subprocess.run(
        shlex.split(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONUNBUFFERED": "1",
        },
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    rows = [line.strip() for line in blob.splitlines() if line.strip()]
    summary = rows[-1] if rows else ""
    return proc.returncode, summary[:300]


def detail_from_ground(ground, source, notes, rules):
    lines = [
        "Scripts and brief: %s." % ("the head commit (bootstrap; the base commit has no verifier)" if source == "head" else "the base commit"),
        "Verifier: %s via Pi, provider %s." % (PI_MODEL, PI_PROVIDER),
        "",
        "Commands:",
    ]
    for row in ground["commands"]:
        lines.append("- `%s` exit %s: %s" % (row["cmd"], row["exit"], row["summary"] or "(no output)"))
    lines.append("")
    lines.append("Bin scripts:")
    if ground["bin_scripts"]:
        for row in ground["bin_scripts"]:
            lines.append("- `%s` exit %s: %s" % (row["cmd"], row["exit"], row["summary"] or "(no output)"))
    else:
        lines.append("- none")
    lines.append("")
    lines.append("House rules lost or changed:")
    if rules:
        for quote in rules:
            lines.append("- %s" % quote)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Notes:")
    if notes:
        for note in notes:
            lines.append("- %s" % note)
    else:
        lines.append("- none")
    return lines


def gh_env():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise VerifierError("GH_TOKEN is not set")
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "GH_TOKEN": token,
        "GH_REPO": os.environ["GITHUB_REPOSITORY"],
        "GIT_TERMINAL_PROMPT": "0",
    }


def run_checked(argv, env, timeout, cwd=None):
    proc = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + (proc.stdout or "")).strip().splitlines()
        detail = tail[-1] if tail else "exit %s" % proc.returncode
        raise VerifierError("%s failed: %s" % (argv[0], detail[:300]))
    return proc.stdout


def fetch_main(head_dir, repo):
    url = "https://github.com/%s.git" % repo
    run_checked(
        ["git", "-C", head_dir, "fetch", "--no-tags", url, "+refs/heads/main:refs/remotes/origin/main"],
        {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "GIT_TERMINAL_PROMPT": "0"},
        120,
    )


def merge_base(head_dir):
    out = run_checked(
        ["git", "-C", head_dir, "merge-base", "HEAD", "origin/main"],
        {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "GIT_TERMINAL_PROMPT": "0"},
        60,
    )
    sha = out.strip()
    if not SHA_RE.match(sha):
        raise VerifierError("merge-base is not a sha")
    return sha


def read_pr(pr_number, env):
    raw = run_checked(
        ["gh", "pr", "view", str(pr_number), "--json", "body,title"],
        env,
        60,
    )
    data = json.loads(raw)
    return data.get("title") or "", data.get("body") or ""


def commit_messages(head_dir, base):
    out = run_checked(
        ["git", "-C", head_dir, "log", "--format=%B%x1e", "%s..HEAD" % base],
        {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "GIT_TERMINAL_PROMPT": "0"},
        60,
    )
    return [part for part in out.split("\x1e") if part.strip()]


def changed_bin_paths(head_dir, base):
    out = run_checked(
        ["git", "-C", head_dir, "diff", "--name-only", base, "HEAD", "--", "bin"],
        {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "GIT_TERMINAL_PROMPT": "0"},
        60,
    )
    return [line for line in out.splitlines() if line.strip()]


def write_diff(head_dir, base, dest):
    proc = subprocess.run(
        ["git", "-C", head_dir, "diff", base, "HEAD"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "GIT_TERMINAL_PROMPT": "0"},
    )
    if proc.returncode != 0:
        raise VerifierError("git diff failed")
    text = proc.stdout or ""
    if len(text) > 200000:
        text = text[:200000] + "\n\n[diff truncated]\n"
    dest.write_text(text, encoding="utf-8")


def list_comments(repo, pr_number, env):
    raw = run_checked(
        [
            "gh", "api", "--paginate",
            "repos/%s/issues/%s/comments" % (repo, pr_number),
            "--jq", ".[] | {id, body} | @json",
        ],
        env,
        60,
    )
    comments = []
    decoder = json.JSONDecoder()
    text = raw.strip()
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        try:
            obj, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            raise VerifierError("could not read pull request comments")
        index += end
        if isinstance(obj, list):
            comments.extend(obj)
        elif isinstance(obj, dict):
            comments.append(obj)
    return comments


def post_comment(repo, pr_number, sha, text, env, scratch):
    comments = list_comments(repo, pr_number, env)
    existing = comment_id_for_sha(comments, sha)
    payload = scratch / "comment-payload.json"
    payload.write_text(json.dumps({"body": text}), encoding="utf-8")
    if existing:
        run_checked(
            ["gh", "api", "-X", "PATCH", "repos/%s/issues/comments/%s" % (repo, existing), "--input", str(payload)],
            env,
            60,
        )
        return existing
    raw = run_checked(
        ["gh", "api", "-X", "POST", "repos/%s/issues/%s/comments" % (repo, pr_number), "--input", str(payload)],
        env,
        60,
    )
    created = json.loads(raw) if raw.strip() else {}
    return created.get("id")


def annotate_check(repo, sha, title, summary, env, scratch):
    try:
        raw = run_checked(
            [
                "gh", "api",
                "repos/%s/commits/%s/check-runs" % (repo, sha),
                "--jq", '.check_runs[] | select(.name=="pstack-verifier") | .id',
            ],
            env,
            60,
        )
    except VerifierError as exc:
        sys.stderr.write("check annotate skipped: %s\n" % exc.reason)
        return
    payload = scratch / "check-payload.json"
    payload.write_text(json.dumps({"output": {"title": title, "summary": summary[:60000]}}), encoding="utf-8")
    for cid in raw.split():
        if not cid.strip().isdigit():
            continue
        try:
            run_checked(
                ["gh", "api", "-X", "PATCH", "repos/%s/check-runs/%s" % (repo, cid.strip()), "--input", str(payload)],
                env,
                60,
            )
        except VerifierError as exc:
            sys.stderr.write("check annotate skipped: %s\n" % exc.reason)


def call_model(brief_text, scratch, secret):
    home = scratch / "pi-home"
    home.mkdir(parents=True, exist_ok=True)
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "TMPDIR": str(scratch),
        LOGIN_VAR: secret,
    }
    proc = subprocess.Popen(
        pi_command(brief_text),
        cwd=str(scratch),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=MODEL_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, 15)
            time.sleep(1)
            os.killpg(proc.pid, 9)
        except ProcessLookupError:
            pass
        raise VerifierError("model timed out")
    (scratch / "model-stdout.txt").write_text(redact(stdout or "", secret), encoding="utf-8")
    (scratch / "model-stderr.txt").write_text(redact(stderr or "", secret), encoding="utf-8")
    if secret and secret in (stdout or "") + (stderr or ""):
        raise VerifierError("model output contained the login")
    if proc.returncode != 0:
        tail = [line.strip() for line in (stderr or "").splitlines() if line.strip()]
        detail = redact(tail[-1], secret) if tail else "exit %s" % proc.returncode
        raise VerifierError("pi exited %s: %s" % (proc.returncode, detail[:300]))
    if not (stdout or "").strip():
        raise VerifierError("model answer was empty")
    return stdout


def require_actions(env=None):
    env = os.environ if env is None else env
    if env.get("GITHUB_ACTIONS") != "true":
        sys.stderr.write("pstack verifier runs on GitHub-hosted runners only\n")
        return False
    return True


def require_sha(name):
    sha = os.environ.get(name, "")
    if not SHA_RE.match(sha):
        raise VerifierError("%s is not a sha" % name)
    return sha


def run_ground(head_dir, planned):
    commands = []
    for cmd in REQUIRED_COMMANDS:
        code, summary = run_one(cmd, head_dir, COMMAND_TIMEOUT_S)
        commands.append({"cmd": cmd, "exit": code, "summary": summary})
        sys.stdout.write("ran %s exit %s\n" % (cmd, code))
    bins = []
    for row in planned:
        code, summary = run_one(row["cmd"], head_dir, 120)
        bins.append({**row, "exit": code, "summary": summary})
        sys.stdout.write("ran %s exit %s\n" % (row["cmd"], code))
    return {"commands": commands, "bin_scripts": bins}


def publish(verdict, sha, text, scratch, repo, pr_number, env):
    secret = os.environ.get(LOGIN_VAR, "")
    text = redact(text, secret)
    verdict_of(text)
    comment_path = scratch / "comment.md"
    comment_path.write_text(text, encoding="utf-8")
    post_comment(repo, pr_number, sha, text, env, scratch)
    (scratch / "posted").write_text(verdict, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(text)
    annotate_check(repo, sha, first_line(verdict, sha), text, env, scratch)
    sys.stdout.write("%s\n" % first_line(verdict, sha))
    return 0 if verdict != "FAIL" else 1


def fail(reason, sha, scratch, repo, pr_number, env, extra=None):
    lines = list(extra or [])
    text = comment_text("FAIL", sha, reason, lines)
    return publish("FAIL", sha, text, scratch, repo, pr_number, env)


def evaluate():
    sha = require_sha("HEAD_SHA")
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    head_dir = os.environ["HEAD_DIR"]
    source = os.environ.get("VERIFIER_SOURCE", "head")
    scratch = Path(os.environ["PSTACK_SCRATCH"])
    scratch.mkdir(parents=True, exist_ok=True)
    env = gh_env()
    brief_path = Path(os.environ["VERIFIER_DIR"]) / "brief.md"
    if not brief_path.is_file():
        return fail("verifier brief is missing", sha, scratch, repo, pr_number, env)

    sys.stdout.write("fetch origin/main\n")
    fetch_main(head_dir, repo)
    base = merge_base(head_dir)
    messages = commit_messages(head_dir, base)
    _title, body = read_pr(pr_number, env)
    (scratch / "pr-body.md").write_text(body, encoding="utf-8")
    if same_family(messages, body):
        sys.stdout.write("same family, model not called\n")
        return fail("same family", sha, scratch, repo, pr_number, env)

    secret = os.environ.get(LOGIN_VAR, "")
    if not secret:
        return fail("missing login", sha, scratch, repo, pr_number, env)

    write_diff(head_dir, base, scratch / "diff.txt")
    paths = changed_bin_paths(head_dir, base)
    planned, bin_notes = bin_plan(head_dir, paths)
    bin_text = "\n".join(row["cmd"] for row in planned) if planned else "(none)"
    commands_text = "\n".join(REQUIRED_COMMANDS)
    brief = render_brief(brief_path.read_text(encoding="utf-8"), {
        "HEAD_DIR": head_dir,
        "HEAD_SHA": sha,
        "WHY_FILE": str(scratch / "pr-body.md"),
        "DIFF_FILE": str(scratch / "diff.txt"),
        "COMMANDS": commands_text,
        "BIN_COMMANDS": bin_text,
    })
    (scratch / "brief.txt").write_text(brief, encoding="utf-8")

    sys.stdout.write("run the change\n")
    ground = run_ground(head_dir, planned)
    (scratch / "ground.json").write_text(json.dumps(ground), encoding="utf-8")

    sys.stdout.write("call pi\n")
    try:
        answer_text = call_model(brief, scratch, secret)
        answer = extract_json(answer_text)
        verdict, reason, notes, rules = combine(ground, answer, source == "head", bin_notes)
    except VerifierError as exc:
        # Commands already ran. A model failure still fails closed, and the comment shows those exits.
        lines = detail_from_ground(ground, source, bin_notes, [])
        return fail(exc.reason, sha, scratch, repo, pr_number, env, lines)
    lines = detail_from_ground(ground, source, notes, rules)
    text = comment_text(verdict, sha, reason, lines)
    return publish(verdict, sha, text, scratch, repo, pr_number, env)


def ensure_comment():
    if not require_actions():
        return 1
    sha = require_sha("HEAD_SHA")
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    scratch = Path(os.environ["PSTACK_SCRATCH"])
    scratch.mkdir(parents=True, exist_ok=True)
    env = gh_env()
    posted = scratch / "posted"
    comment = scratch / "comment.md"
    if not comment.is_file() or comment.stat().st_size == 0:
        comment.write_text(comment_text("FAIL", sha, "The verifier produced no comment.", []), encoding="utf-8")
        posted.unlink(missing_ok=True)
    text = comment.read_text(encoding="utf-8")
    verdict, found_sha = verdict_of(text)
    if found_sha != sha:
        text = comment_text("FAIL", sha, "The verifier comment named a different sha.", [])
        verdict = "FAIL"
        comment.write_text(text, encoding="utf-8")
    if not posted.is_file():
        post_comment(repo, pr_number, sha, text, env, scratch)
        posted.write_text(verdict, encoding="utf-8")
    sys.stdout.write("%s\n" % first_line(verdict, sha))
    return 0 if verdict != "FAIL" else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--ensure-comment":
        try:
            return ensure_comment()
        except Exception as exc:
            sys.stderr.write("ensure-comment failed: %s\n" % exc)
            return 1
    if not require_actions():
        return 1
    try:
        return evaluate()
    except Exception as exc:
        reason = exc.reason if isinstance(exc, VerifierError) else "verifier error: %s" % exc
        sys.stderr.write("%s\n" % reason)
        try:
            sha = os.environ.get("HEAD_SHA", "")
            if not SHA_RE.match(sha):
                return 1
            scratch = Path(os.environ.get("PSTACK_SCRATCH", "/tmp/pstack"))
            scratch.mkdir(parents=True, exist_ok=True)
            return fail(str(reason), sha, scratch, os.environ["GITHUB_REPOSITORY"], os.environ["PR_NUMBER"], gh_env())
        except Exception as inner:
            sys.stderr.write("could not post the fail comment: %s\n" % inner)
            return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
