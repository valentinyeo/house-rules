import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/hypertask-triage/scripts/board-health"


def load():
    loader = importlib.machinery.SourceFileLoader("board_health", str(SCRIPT))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("board_health", loader))
    loader.exec_module(mod)
    return mod


class OwnerRoles(unittest.TestCase):
    def test_outside_row_with_lead_role_still_owns_its_tickets(self):
        """SOFT-2785: kind outside keeps solo-wake away; the lead role keeps board-health sendback away."""
        bh = load()
        rows = [{"login": "Self Waker", "kind": "outside", "roles": ["lead", "expert"]},
                {"login": "Plain Outside", "kind": "outside"},
                {"login": "Lead By Kind", "kind": "lead"}]
        with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(rows))):
            owners = bh.roster_owners()
        self.assertEqual(owners, {"self waker", "lead by kind"})

    def test_real_roster_keeps_ht_product_lead_exempt(self):
        self.assertIn("ht product lead", load().QUEUE_EXEMPT)


if __name__ == "__main__":
    unittest.main()
