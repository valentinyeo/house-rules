import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FleetLiveBoardsTest(unittest.TestCase):
    def test_no_archived_board_references(self):
        hits = []
        for path in sorted((ROOT / "fleet").rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if "11514" in line:
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual(hits, [], "Archived board references: " + ", ".join(hits))

    def test_hyci_park_uses_real_scope(self):
        loader = importlib.machinery.SourceFileLoader("fleet_park", str(ROOT / "fleet/park"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        park = importlib.util.module_from_spec(spec)
        loader.exec_module(park)
        scopes = json.loads((ROOT / "skills/hypertask-triage/scripts/scopes.json").read_text())
        lead, board = park.lead_for("HYCI-1")
        self.assertEqual(lead, scopes[board]["lead"])
        self.assertEqual(str(scopes[board]["board"]), board)
