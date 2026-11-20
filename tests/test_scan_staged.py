import os
import secrets
import shutil
import string
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin" / "scan-staged"


def tool_ready(name):
    found = shutil.which(name)
    if found and os.access(found, os.X_OK):
        return True
    fallback = Path.home() / ".local" / "bin" / name
    return fallback.is_file() and os.access(fallback, os.X_OK)


MISSING = [name for name in ("gitleaks", "trufflehog") if not tool_ready(name)]

GIT_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
}


def git(cwd, *args):
    run = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            *args,
        ],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        raise RuntimeError(run.stderr.strip() or "git failed")
    return run.stdout.strip()


def scan(cwd, *args):
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
    )


def github_token():
    alphabet = string.ascii_letters + string.digits
    return "ghp_" + "".join(secrets.choice(alphabet) for _ in range(36))


def commit_sha():
    return secrets.token_hex(20)


def fixture_uri(host):
    return "https://" + "user" + ":" + "password" + "@" + host


def combined(result):
    return result.stdout + result.stderr


@unittest.skipIf(bool(MISSING), "%s is not installed" % " and ".join(MISSING))
class ScanStagedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self):
        path = self.root / ("r" + secrets.token_hex(3))
        git(self.root, "init", "-q", "-b", "main", str(path))
        return path

    def stage(self, repo, rel, text):
        dest = repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
        git(repo, "add", "--", rel)

    def commit(self, repo, message):
        git(repo, "commit", "-qm", message)
        return git(repo, "rev-parse", "HEAD")

    def assert_key_hidden(self, key, result):
        if key in combined(result):
            self.fail("scanner printed the key")

    def assert_blocked(self, result, key):
        self.assert_key_hidden(key, result)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("--no-verify", combined(result))
        self.assertIn("1Password", result.stderr)
        self.assertIn("stack-key", result.stderr)
        self.assertIn("yeo-key", result.stderr)
        self.assertIn("trufflehog:ignore", result.stderr)

    def assert_passed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("trufflehog:ignore", combined(result))
        self.assertNotIn("--no-verify", combined(result))

    def test_a_new_github_token_blocks(self):
        repo = self.repo()
        key = github_token()
        self.stage(repo, "notes.txt", "export GH=" + key + "\n")
        self.assert_blocked(scan(repo), key)

    def test_b_new_line_in_existing_file_blocks(self):
        repo = self.repo()
        self.stage(repo, "app.txt", "hello\n")
        self.commit(repo, "base")
        key = github_token()
        self.stage(repo, "app.txt", "hello\nexport GH=" + key + "\n")
        self.assert_blocked(scan(repo), key)

    def test_c_unchanged_template_lines_pass(self):
        repo = self.repo()
        digest = commit_sha()
        files = {
            "apps/cli/test/intake.test.ts": 'import { x } from "./old";\nexport const url = "%s";\n'
            % fixture_uri("operator.example.test"),
            "apps/cli/test/intake-erase.test.ts": 'import { y } from "./old";\nexport const url = "%s";\n'
            % fixture_uri("operator.example.test"),
            "packages/core/test/view.test.ts": 'import { z } from "./old";\nexpect(view).toContain("%s");\n'
            % digest,
        }
        for rel, text in files.items():
            self.stage(repo, rel, text)
        self.commit(repo, "template")
        for rel, text in files.items():
            self.stage(repo, rel, text.replace('from "./old"', 'from "./new"'))
        self.assert_passed(scan(repo))

    def test_d_reserved_uri_passes_real_host_blocks(self):
        repo = self.repo()
        hosts = [
            "operator.example.test",
            "localhost",
            "example.com",
            "example.org",
            "example.net",
            "api.example",
            "foo.invalid",
            "bar.localhost",
        ]
        body = "".join('export const url = "%s";\n' % fixture_uri(host) for host in hosts)
        self.stage(repo, "fixture.ts", body)
        self.assert_passed(scan(repo))

        other = self.repo()
        raw = fixture_uri("db.acme-prod.io")
        self.stage(other, "prod.ts", 'export const url = "%s";\n' % raw)
        result = scan(other)
        self.assert_key_hidden(raw, result)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"DetectorName":"URI"', result.stderr)

    def test_e_github_commit_link_passes(self):
        repo = self.repo()
        digest = commit_sha()
        self.stage(
            repo,
            "note.md",
            "see https://github.com/acme/widgets/commit/%s for the pin\n" % digest,
        )
        self.assert_passed(scan(repo))

    def test_spaced_path_does_not_rescan_old_key(self):
        repo = self.repo()
        key = github_token()
        self.stage(repo, "sub/my file.txt", "export GH=" + key + "\nkeep\n")
        self.commit(repo, "old key")
        self.stage(repo, "sub/my file.txt", "export GH=" + key + "\nhello\n")
        result = scan(repo)
        self.assert_key_hidden(key, result)
        self.assert_passed(result)

    def test_f_pure_rename_passes(self):
        repo = self.repo()
        key = github_token()
        self.stage(repo, "old.txt", "export GH=" + key + "\n")
        self.commit(repo, "old key")
        git(repo, "mv", "old.txt", "new.txt")
        result = scan(repo)
        self.assert_key_hidden(key, result)
        self.assert_passed(result)

    def test_g_range_new_token_blocks_and_template_replay_passes(self):
        repo = self.repo()
        self.stage(repo, "clean.txt", "hello\n")
        base = self.commit(repo, "base")
        key = github_token()
        self.stage(repo, "leak.txt", "export GH=" + key + "\n")
        head = self.commit(repo, "leak")
        self.assert_blocked(scan(repo, "--range", "%s...%s" % (base, head)), key)

        digest = commit_sha()
        files = {
            "apps/cli/test/intake.test.ts": 'import { x } from "./old";\nexport const url = "%s";\n'
            % fixture_uri("operator.example.test"),
            "apps/cli/test/intake-erase.test.ts": 'import { y } from "./old";\nexport const url = "%s";\n'
            % fixture_uri("operator.example.test"),
            "packages/core/test/view.test.ts": 'import { z } from "./old";\nexpect(view).toContain("%s");\n'
            % digest,
        }
        for rel, text in files.items():
            self.stage(repo, rel, text)
        template = self.commit(repo, "template")
        for rel, text in files.items():
            self.stage(repo, rel, text.replace('from "./old"', 'from "./new"'))
        renamed = self.commit(repo, "rename import")
        self.assert_passed(scan(repo, "--range", "%s...%s" % (template, renamed)))

    def test_ignore_requires_a_reason(self):
        host = "db.acme-prod.io"
        reasoned = self.repo()
        self.stage(
            reasoned,
            "a.ts",
            'export const url = "%s"; // trufflehog:ignore -- fixture, not a key\n' % fixture_uri(host),
        )
        self.assert_passed(scan(reasoned))

        bare = self.repo()
        raw = fixture_uri(host)
        self.stage(bare, "b.ts", 'export const url = "%s"; // trufflehog:ignore\n' % raw)
        result = scan(bare)
        self.assert_key_hidden(raw, result)
        self.assertNotEqual(result.returncode, 0)
