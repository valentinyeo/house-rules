import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


CHECKS_BUDGET = runpy.run_path(str(Path(__file__).resolve().parents[1] / "fleet/checks-budget"))


class ChecksBudgetTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name)
        self.run = subprocess.run
        self.git("init", "-b", "trunk")
        self.git("remote", "add", "origin", "https://github.com/owner/repo.git")
        self.workflows = self.path / ".github/workflows"
        self.workflows.mkdir(parents=True)
        self.workflow = self.workflows / "ci.yml"
        self.workflow.write_text("on: pull_request\nconcurrency: {group: ci, cancel-in-progress: true}\n")
        self.commit_workflows()
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")

    def git(self, *args):
        return self.run(["git", "-C", str(self.path), *args], check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5,
                        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}).stdout

    def commit_workflows(self):
        self.git("add", ".github/workflows")
        self.git("-c", "user.name=Checks Budget Test", "-c", "user.email=test@users.noreply.github.com",
                 "-c", "commit.gpgsign=false", "commit", "-m", "Workflow fixture")

    def inspect(self):
        def command(args, **kwargs):
            if args[0] != "gh":
                return self.run(args, **kwargs)
            endpoint = args[-1]
            if endpoint == "repos/owner/repo":
                data = {"default_branch": "trunk"}
            elif "actions/workflows?" in endpoint:
                data = {"workflows": []}
            elif "actions/runs?" in endpoint:
                data = {"workflow_runs": []}
            else:
                self.fail(f"Unexpected GitHub request: {endpoint}")
            return subprocess.CompletedProcess(args, 0, json.dumps(data))

        stderr = io.StringIO()
        with patch.object(subprocess, "run", side_effect=command), contextlib.redirect_stderr(stderr):
            output = CHECKS_BUDGET["inspect_repo"](str(self.path), debug=True)
        return output, stderr.getvalue()

    def test_untracked_workflow_is_ignored(self):
        (self.workflows / "stray.yml").write_text("on: pull_request\njobs: {}\n")
        output, debug = self.inspect()
        self.assertEqual(output, "")
        self.assertIn("workflows missing cancel-in-progress=0/1", debug)

    def test_locally_modified_workflow_is_ignored(self):
        self.workflow.write_text("on: pull_request\njobs: {}\n")
        output, debug = self.inspect()
        self.assertEqual(output, "")
        self.assertIn("workflows missing cancel-in-progress=0/1", debug)

    def test_remote_default_branch_takes_precedence_over_head(self):
        self.workflow.write_text("on: pull_request\njobs: {}\n")
        self.commit_workflows()
        output, debug = self.inspect()
        self.assertEqual(output, "")
        self.assertIn("workflows missing cancel-in-progress=0/1", debug)

    def test_missing_remote_ref_falls_back_to_head(self):
        self.git("update-ref", "-d", "refs/remotes/origin/trunk")
        self.workflow.write_text("on: pull_request\njobs: {}\n")
        output, debug = self.inspect()
        self.assertEqual(output, "")
        self.assertIn("workflows missing cancel-in-progress=0/1", debug)

    def test_tracked_workflow_without_concurrency_is_reported(self):
        self.workflow.write_text("on: pull_request\njobs: {}\n")
        self.commit_workflows()
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        output, debug = self.inspect()
        self.assertIn("1/1 workflows lack concurrency group with cancel-in-progress true", output)
        self.assertIn("workflows missing cancel-in-progress=1/1", debug)

    def test_non_ascii_workflow_is_counted(self):
        (self.workflows / "café.yaml").write_text("on: pull_request\njobs: {}\n")
        self.commit_workflows()
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        output, debug = self.inspect()
        self.assertIn("1/2 workflows lack concurrency group with cancel-in-progress true", output)
        self.assertIn("workflows missing cancel-in-progress=1/2", debug)

    def test_existing_regressions(self):
        CHECKS_BUDGET["self_test"]()


if __name__ == "__main__":
    unittest.main()
