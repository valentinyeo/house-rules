import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/manager-shift/shift.py"
HANDOVER = """## Role
HT Support Lead, CODEX mode
## Open work
https://app.hypertask.ai/detail/project-4060/819 — In Progress
https://github.com/valentinyeo/house-rules/pull/24 — review
## Decisions
Await HT Product Lead rollout agreement; no new question.
## Next actions
Read ticket replies, then verify the existing PR.
## Last digest
2026-10-26T13:00:00Z; next read 13:45Z; runner 8 active.
"""


class ManagerShiftTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.env = {**os.environ, "HOME": self.home.name}
        self.state = Path(self.home.name) / ".local/state/manager-shifts/support.json"
        self.note = Path(self.home.name) / "draft.md"
        self.note.write_text(HANDOVER)

    def run_shift(self, action, *args, session="first", code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), action, "--role", "support",
                                 "--session", session, *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout

    def test_context_warning_and_cap_survive_wakes(self):
        self.run_shift("start")
        self.assertIn("shift ok", self.run_shift("check", "--context", "99999"))
        self.assertIn("WARN", self.run_shift("check", "--context", "100000"))
        self.assertIn("HANDOVER REQUIRED", self.run_shift("check", "--context", "120000", code=3))
        self.run_shift("start")
        self.assertIn("HANDOVER REQUIRED", self.run_shift("check", "--context", "0", code=3))

    def test_four_hour_cap_survives_repeated_start(self):
        self.run_shift("start")
        state = json.loads(self.state.read_text())
        state["started"] = time.time() - 14400
        self.state.write_text(json.dumps(state))
        self.run_shift("start")
        self.assertEqual(json.loads(self.state.read_text())["started"], state["started"])
        self.assertIn("HANDOVER REQUIRED", self.run_shift("check", "--context", "1", code=3))

    def test_fresh_process_recovers_complete_handover(self):
        self.run_shift("start")
        self.run_shift("end", "--handover", str(self.note))
        saved = Path(self.home.name) / "poteto-handover/support-shift.md"
        self.assertEqual(saved.read_text(), HANDOVER)
        self.run_shift("check", "--context", "1", code=1)
        self.run_shift("start", code=1)
        output = self.run_shift("start", session="after-clear")
        self.assertIn(HANDOVER, output)
        self.assertIn("shift started", output)
        self.assertIn("shift ok", self.run_shift("check", "--context", "1", session="after-clear"))
        self.run_shift("end", "--handover", str(self.note), code=1)
        self.assertEqual(saved.read_text(), HANDOVER)

    def test_other_session_cannot_reset_or_close_shift(self):
        self.run_shift("start")
        original = self.state.read_text()
        self.run_shift("start", session="other", code=1)
        self.run_shift("end", "--handover", str(self.note), session="other", code=1)
        self.assertEqual(self.state.read_text(), original)
        self.run_shift("end", "--handover", str(self.note))
        self.run_shift("end", "--handover", str(self.note))

    def test_missing_or_empty_handover_section_keeps_shift_active(self):
        self.run_shift("start")
        for note in ("## Role\nSupport\n", HANDOVER.replace("Await HT Product Lead rollout agreement; no new question.\n", "\n")):
            with self.subTest(note=note):
                self.note.write_text(note)
                self.run_shift("end", "--handover", str(self.note), code=1)
                self.assertIn("shift ok", self.run_shift("check", "--context", "1"))
        self.assertFalse((Path(self.home.name) / "poteto-handover/support-shift.md").exists())

    def test_roles_do_not_share_shift_or_handover(self):
        self.run_shift("start")
        result = subprocess.run([sys.executable, str(SCRIPT), "start", "--role", "design",
                                 "--session", "design-session"], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.run_shift("end", "--handover", str(self.note))
        design = self.state.parent / "design.json"
        self.assertFalse(json.loads(design.read_text())["closed"])
        self.assertFalse((Path(self.home.name) / "poteto-handover/design-shift.md").exists())

    def test_every_shared_lead_loads_the_shift_skill(self):
        root = SCRIPT.parents[2]
        for role in ("design-lead", "finance-lead", "marketing-lead", "support-manager"):
            text = (root / "skills" / role / "SKILL.md").read_text()
            self.assertIn("[manager-shift](../manager-shift/SKILL.md)", text)
        self.assertIn("Managers use `/manager-shift` at every check-in.",
                      (root / "house-rules.md").read_text())

    def test_unknown_context_and_missing_state_fail_closed(self):
        self.run_shift("check", "--context", "1", code=1)
        self.run_shift("start")
        self.run_shift("check", code=2)
        self.run_shift("check", "--context", "-1", code=2)
        self.state.write_text("not valid json")
        self.run_shift("start", code=1)


if __name__ == "__main__":
    unittest.main()
