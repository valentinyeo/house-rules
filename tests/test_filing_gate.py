import importlib.machinery
import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader(
    "filing_gate", str(ROOT / "skills/hypertask-triage/scripts/filing-gate"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
GATE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(GATE)


class FilingGateTest(unittest.TestCase):
    def run_gate(self, payload=None, error=None, returncode=0, board=2060, raw=None):
        argv = ["filing-gate", "--", "task", "create", "--project", str(board),
                "--title", "HYCI-233 regression", "--labels", "Incident"]
        result = subprocess.CompletedProcess(
            ["hypertask", "project", "show", str(board), "--json"],
            returncode, json.dumps(payload) if raw is None else raw,
            "lookup failed" if returncode else "")
        output, warning = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", argv), \
                patch.object(GATE.subprocess, "run", return_value=result, side_effect=error) as lookup, \
                patch.object(GATE, "ready_warning", return_value="ticket readiness warning") as readiness, \
                redirect_stdout(output), redirect_stderr(warning):
            code = GATE.main()
        return code, output.getvalue(), warning.getvalue(), lookup, readiness

    def test_unreadable_board_refuses_before_readiness(self):
        for error in (OSError("offline"), subprocess.TimeoutExpired("hypertask", 30)):
            with self.subTest(error=type(error).__name__):
                code, output, warning, _, readiness = self.run_gate(error=error)
                self.assertEqual(code, 5)
                self.assertIn("REFUSE board 2060", output)
                self.assertIn("read failed", warning)
                readiness.assert_not_called()

    def test_failed_lookup_refuses(self):
        code, output, _, _, readiness = self.run_gate(returncode=1)
        self.assertEqual(code, 5)
        self.assertIn("REFUSE board 2060", output)
        readiness.assert_not_called()

    def test_missing_or_unknown_status_refuses(self):
        for payload in ({}, {"project": {}}, {"project": None},
                        {"project": {"status": None}}, {"project": {"status": ""}},
                        {"project": {"status": "Unexpected"}},
                        {"project": {"status": []}}, []):
            with self.subTest(payload=payload):
                code, output, _, _, readiness = self.run_gate(payload=payload)
                self.assertEqual(code, 5)
                self.assertIn("REFUSE board 2060", output)
                readiness.assert_not_called()

    def test_malformed_json_refuses(self):
        code, output, _, _, readiness = self.run_gate(raw="not-json")
        self.assertEqual(code, 5)
        self.assertIn("REFUSE board 2060", output)
        readiness.assert_not_called()

    def test_archived_incident_refuses(self):
        code, output, _, lookup, readiness = self.run_gate(
            payload={"project": {"status": "Archive"}}, board=11514)
        self.assertEqual(code, 5)
        self.assertIn("REFUSE board 11514 is archived", output)
        self.assertEqual(lookup.call_args.args[0],
                         ["hypertask", "project", "show", "11514", "--json"])
        readiness.assert_not_called()

    def test_active_board_allows_readiness_warning(self):
        code, output, warning, _, readiness = self.run_gate(
            payload={"project": {"status": "Normal"}})
        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertIn("ticket readiness warning", warning)
        readiness.assert_called_once()

    def test_retired_board_refuses_without_lookup(self):
        code, output, _, lookup, readiness = self.run_gate(error=OSError("offline"), board=4060)
        self.assertEqual(code, 5)
        self.assertIn("REFUSE board 4060 is archived", output)
        lookup.assert_not_called()
        readiness.assert_not_called()


if __name__ == "__main__":
    unittest.main()
