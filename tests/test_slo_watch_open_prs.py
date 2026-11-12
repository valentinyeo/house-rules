import importlib.machinery
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "fleet/slo-watch.py"
loader = importlib.machinery.SourceFileLoader("slo_watch", str(SCRIPT))
spec = importlib.util.spec_from_loader("slo_watch", loader)
slo = importlib.util.module_from_spec(spec)
loader.exec_module(slo)


def pull(number, base="production"):
    return {"number": number, "baseRefName": base, "statusCheckRollup": []}


class Fake:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def copy_body(*prs):
    return Fake(stdout=json.dumps({"fields": ["number", "baseRefName", "statusCheckRollup"], "prs": list(prs)}))


class OpenPrsTest(unittest.TestCase):
    def read(self, shared, live=None):
        calls = []

        def snapshot(args, **kwargs):
            calls.append(("snapshot", args))
            return shared

        def gh(args, **kwargs):
            calls.append(("live", args))
            return live if live is not None else Fake(stdout="[]")

        with patch.object(slo, "subprocess", SimpleNamespace(run=snapshot, SubprocessError=subprocess.SubprocessError)), patch.object(slo, "gh_out", side_effect=gh):
            return slo.open_prs(), calls

    def test_shared_copy_answer_is_production_only(self):
        rows, calls = self.read(copy_body(pull(1), pull(2, base="staging"), pull(3)))
        self.assertEqual([row["number"] for row in rows], [1, 3])
        self.assertEqual([kind for kind, _ in calls], ["snapshot"])

    def test_copy_without_production_rows_reads_live(self):
        live = Fake(stdout=json.dumps([pull(4)]))
        rows, calls = self.read(copy_body(pull(2, base="staging")), live)
        self.assertEqual([row["number"] for row in rows], [4])
        self.assertEqual([kind for kind, _ in calls], ["snapshot", "live"])

    def test_bad_copy_reads_live(self):
        live = Fake(stdout=json.dumps([pull(5)]))
        rows, calls = self.read(Fake(returncode=2, stdout='{"prs": []}'), live)
        self.assertEqual([row["number"] for row in rows], [5])
        self.assertEqual([kind for kind, _ in calls], ["snapshot", "live"])

    def test_unavailable_live_returns_none(self):
        rows, _ = self.read(Fake(returncode=2, stdout='{"prs": []}'), Fake(returncode=1, stdout=""))
        self.assertIsNone(rows)

    def test_malformed_copy_reads_live(self):
        live = Fake(stdout=json.dumps([pull(6)]))
        rows, calls = self.read(Fake(stdout="not json"), live)
        self.assertEqual([row["number"] for row in rows], [6])
        self.assertEqual([kind for kind, _ in calls], ["snapshot", "live"])


if __name__ == "__main__":
    unittest.main()
