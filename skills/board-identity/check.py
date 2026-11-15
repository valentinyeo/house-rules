#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess


ROLES = {
    "HT Support Lead": ("ht-support-lead", {10450, 15},
                        ("ai-chatbot", "HypertaskDocs", "hypertask"),
                        "Hypertask fleet; HEFE 10450; see support-manager/runners.md"),
    "HT Design Lead": ("ht-design-lead", {15}, ("hypertask",),
                       "Hypertask fleet; HTPR 15; see design-lead/runners.md"),
    "HT Growth Lead": ("ht-growth-lead", {2108, 15}, ("hypertask-astro",),
                       "Hypertask fleet; MARK 2108; see marketing-lead/SKILL.md"),
    "HT Finance Lead": ("ht-finance-lead", {2462}, ("pecunia",),
                        "No finance runners; code requests go to HT Product Lead"),
    "CI Boss": ("ci-boss", {15, 2060}, ("ci-boss",),
                "CI and infra service, both fleets; owns no board: infra work is the infra label on 15 and 2060; pool runners via fleet/pick"),
}


def run(*args, env=None):
    return subprocess.run(args, env=env or {**os.environ, "GIT_TERMINAL_PROMPT": "0"}, capture_output=True, text=True,
                          timeout=30, check=True).stdout.strip()


def check_identity(name, slug, boards, home):
    token_file = home / ".config/hypertask-agents/credentials/sessions" / f"{slug}-agent-token"
    if token_file.stat().st_mode & 0o077:
        raise RuntimeError("token permissions must be 0600")
    token = token_file.read_text().strip()
    if not token:
        raise RuntimeError("token missing; complete board-identity first")
    env = {**os.environ, "HYPERTASKS_JWT_TOKEN": token}
    context = json.loads(run("hypertask", "--json", "context", env=env))
    if context.get("connected_agent", {}).get("displayName") != name:
        raise RuntimeError("wrong agent; complete board-identity first")
    actual = {project["id"] for project in context.get("projects", [])}
    if not boards <= actual:
        raise RuntimeError("required boards missing: " + ", ".join(map(str, sorted(boards - actual))))
    return "identity: PASS " + name + "; boards " + ", ".join(map(str, sorted(boards)))


def check_repo(repo):
    if not repo.is_dir():
        raise RuntimeError("checkout missing")
    if Path(run("git", "-C", str(repo), "rev-parse", "--show-toplevel")).resolve() != repo.resolve():
        raise RuntimeError("not a checkout root")
    if run("git", "-C", str(repo), "status", "--porcelain"):
        raise RuntimeError("checkout dirty; leave changes intact")
    upstream = run("git", "-C", str(repo), "rev-parse", "--abbrev-ref", "@{upstream}")
    remote, branch = upstream.split("/", 1)
    tip = run("git", "-C", str(repo), "ls-remote", "--exit-code", remote,
              f"refs/heads/{branch}").split()[0]
    run("git", "-C", str(repo), "merge-base", "--is-ancestor", "HEAD", tip)
    return "PASS clean, fast-forwardable"


def main():
    name = os.environ.get("SHIP_SESSION_NAME", "")
    if name not in ROLES:
        print("setup: FAIL use the lead's own named session")
        return 1
    slug, boards, repos, runners = ROLES[name]
    home = Path.home()
    failed = False
    try:
        print(check_identity(name, slug, boards, home))
    except RuntimeError as error:
        print(f"identity: FAIL {error}")
        failed = True
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError):
        print("identity: FAIL cannot verify own token and context; run board-identity")
        failed = True
    for repo in repos:
        try:
            result = check_repo(home / "projects" / repo)
        except RuntimeError as error:
            result = f"FAIL {error}"
            failed = True
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            result = "FAIL cannot prove fast-forward; inspect upstream, fetch freshness and remote access"
            failed = True
        print(f"repo {repo}: {result}")
    print("runners: PASS " + runners)
    print("setup: FAIL" if failed else "setup: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
