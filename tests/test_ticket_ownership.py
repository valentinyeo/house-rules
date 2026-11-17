import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

FLEET = Path(__file__).resolve().parents[1] / "fleet"
sys.path.insert(0, str(FLEET))
from ticket_owner import Owners


def load(name):
    loader = importlib.machinery.SourceFileLoader("ownership_" + name, str(FLEET / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.roster = self.state / "roster.json"
        self.roster.write_text('{"runners": 17}')
        self.owners = Owners(self.state, self.roster)
        self.ticket = {"key": "HYCI-404", "idx": 404, "board": "2060", "section": "Doing",
                       "title": "Keep the owner", "holders": [["runner 6", True]], "created": "2026-11-13",
                       "waiting": False, "labels": ["brain-hard"], "prio": "Urgent", "updated": "2026-11-13T10:00:00Z"}
        self.selection = {"engine": "codex", "model": "gpt-6.1-sol", "effort": "high"}

    def test_wait_and_assignment_loss_do_not_release_ownership(self):
        self.owners.bind("HYCI-404", 6, self.selection)
        self.ticket["holders"] = []
        self.owners.prepare([self.ticket])
        pick = load("pick")
        self.assertFalse(pick.orphan(self.ticket))
        self.assertFalse(pick.free_for(self.ticket, "runner 7"))
        self.assertTrue(pick.free_for(self.ticket, "runner 6"))
        with self.assertRaisesRegex(RuntimeError, "Runner 6"):
            Owners(self.state, self.roster).bind("HYCI-404", 7)
        with patch.object(pick, "ship_claim") as claim, patch.object(pick, "adopt") as adopt:
            for source in ("orphan", "board", "incident-takeover", "pr-queue"):
                self.assertFalse(pick.try_claim(7, self.ticket, source, False))
            claim.assert_not_called()
            adopt.assert_not_called()

    def test_temporary_stops_and_model_changes_keep_the_same_selection(self):
        self.owners.bind("HYCI-404", 6, self.selection)
        self.owners.bind("HYCI-404", 6, {"engine": "claude", "model": "sonnet", "effort": "medium"})
        self.owners.prepare([self.ticket])
        pick = load("pick")
        pick.set_engine("codex")
        with patch.object(pick, "paced_models", return_value={"hard": ("different-model", "medium")}):
            result = pick.render(6, self.ticket, "own")
        self.assertEqual({k: result[k] for k in self.selection}, self.selection)
        with patch.object(pick, "paced_off", return_value=True), patch.object(pick, "running", return_value=None):
            self.assertFalse(pick.orphan(self.ticket))
            self.assertFalse(pick.free_for(self.ticket, "runner 7"))

    def test_removed_owner_allows_recovery_but_bad_state_fails_closed(self):
        self.owners.bind("HYCI-404", 17, self.selection)
        self.roster.write_text('{"runners": 16}')
        self.ticket["holders"] = [["runner 17", True]]
        self.owners.prepare([self.ticket])
        self.assertIsNone(self.ticket["_owner"])
        result = self.owners.bind("HYCI-404", 6, self.selection)
        self.assertEqual(result["runner"], 6)
        (self.owners.directory / "HYCI-404").write_text("bad json")
        with self.assertRaises(ValueError):
            self.owners.prepare([self.ticket])

    def test_owner_resumes_home_column_before_new_work_and_waits_without_a_park_job(self):
        self.owners.bind("HYCI-404", 6, self.selection)
        self.owners.prepare([self.ticket])
        pick = load("pick")
        pick.SNAP = {"tickets": [self.ticket], "incidents": [], "prs": []}
        with patch.object(pick, "resting", return_value=set()), \
                patch.object(pick, "skipped", return_value=False), \
                patch.object(pick, "held_back", return_value=False), \
                patch.object(pick, "open_blocked_by", return_value=False), \
                patch.object(pick, "incident_step", return_value=None), \
                patch.object(pick, "second_ticket", return_value=None), \
                patch.object(pick, "open_prs", return_value=[]):
            self.assertEqual(pick.choose(6, True), (self.ticket, "own"))
            self.ticket["waiting"] = True
            with self.assertRaisesRegex(SystemExit, "keeps HYCI-404"):
                pick.choose(6, True)
        pick.SNAP["tickets"] = []
        with patch.object(pick, "incident_step", return_value=(None, "new-work")) as incident:
            self.assertEqual(pick.choose(6, True), (None, "new-work"))
            incident.assert_called_once()

    def test_park_keeps_assignment_and_leaves_in_progress(self):
        park = load("park")
        ticket = {"projectId": 2060, "section": "Doing", "pullRequests": [{"number": 12}],
                  "assignees": [{"agent": {"displayName": "Runner 6"}}]}
        with patch.dict(os.environ, {"SHIP_SESSION_NAME": "RUNNER 6"}), \
                patch.object(park, "store", return_value=self.owners), \
                patch.object(park, "blockers", return_value=[]), patch.object(park, "free_claim"), \
                patch.object(park, "note"), patch.object(park, "record_event"), patch.object(park, "vcc") as api:
            result = park.park_hand_back("HYCI-404", "checks pending; recheck later", ticket)
            self.assertIn("Runner 6 retained", result)
            api.assert_called_once_with("task", "move", "HYCI-404", "--section", "Checks")
            park.release("HYCI-404", ticket)
            self.assertEqual(api.call_count, 1)
            self.assertEqual(self.owners.read("HYCI-404")["runner"], 6)

    def test_software_factory_pr_opens_in_checks_and_keeps_its_owner(self):
        park = load("park")
        for column in ("Doing", "Building"):
            ticket = {"projectId": 2060, "section": column, "pullRequests": [{"number": 12}],
                      "assignees": [{"agent": {"displayName": "Runner 6"}}]}
            with patch.dict(os.environ, {"SHIP_SESSION_NAME": "RUNNER 6"}), \
                    patch.object(park, "preserve_owner", return_value={"runner": 6}), \
                    patch.object(park, "blockers", return_value=[]), patch.object(park, "free_claim"), \
                    patch.object(park, "note"), patch.object(park, "record_event"), patch.object(park, "vcc") as api:
                result = park.park_hand_back("SOFT-2446", "checks pending; recheck later", ticket)
                self.assertIn("Runner 6 retained", result)
                api.assert_called_once_with("task", "move", "SOFT-2446", "--section", "Checks")

    def test_last_good_picker_keeps_its_ownership_dependency(self):
        gate = load("tool-gate.py")
        source = self.state / "source"
        source.mkdir()
        script = source / "pick"
        script.write_text("print('fixture')\n")
        dependency = source / "ticket_owner.py"
        dependency.write_text("VERSION = 1\n")
        columns = source / "workflow_columns.py"
        columns.write_text("VERSION = 1\n")
        destination = self.state / "lkg"
        gate.PICK_SRC, gate.LKG_DIR = script, destination
        gate.LKG_PICK, gate.RUNNER_STATE = destination / "pick", self.state / "runner"
        gate.FSW = self.state / "watch"

        def hosted_check(served, extra):
            self.assertEqual(served.with_name("ticket_owner.py").read_text(), dependency.read_text())
            self.assertEqual(served.with_name("workflow_columns.py").read_text(), columns.read_text())
            return True, "passed"

        with patch.object(gate, "run_self_test", side_effect=hosted_check) as check:
            self.assertEqual(gate.ensure_pick(), 0)
            self.assertEqual(gate.ensure_pick(), 0)
            self.assertEqual(check.call_count, 1)
            dependency.write_text("VERSION = 2\n")
            self.assertEqual(gate.ensure_pick(), 0)
            self.assertEqual(check.call_count, 2)
            self.assertEqual((destination / "ticket_owner.py").read_text(), "VERSION = 2\n")
        dependency.unlink()
        with patch.object(gate, "file_broken_picker_incident"), patch.object(gate, "run_self_test") as check:
            self.assertEqual(gate.ensure_pick(), 0)
            check.assert_not_called()
            self.assertEqual((destination / "ticket_owner.py").read_text(), "VERSION = 2\n")

    def test_read_only_prepare_does_not_write(self):
        self.owners.prepare([self.ticket], write=False)
        self.assertEqual(self.ticket["_owner"]["runner"], 6)
        self.assertFalse(self.owners.directory.exists())


if __name__ == "__main__":
    unittest.main()
