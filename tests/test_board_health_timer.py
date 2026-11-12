import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / "systemd/ht-board-health.service").read_text()
TIMER = (ROOT / "systemd/ht-board-health.timer").read_text()
SCOPES = {k: v for k, v in json.loads(
    (ROOT / "skills/hypertask-triage/scripts/scopes.json").read_text()).items() if not k.startswith("_")}

HOURLY = ["15", "11514", "2060", "2060/multi-bot", "2060/postbox", "2060/multi-bot-android", "8525"]


def targets():
    found = set()
    for line in SERVICE.splitlines():
        if "board-health" not in line or "ExecStart" not in line:
            continue
        words = line.split()
        for flag in ("--board", "--scope"):
            if flag in words:
                found.add(words[words.index(flag) + 1])
    return found


class BoardHealthTimerTest(unittest.TestCase):
    def test_every_fleet_board_runs_hourly(self):
        self.assertEqual(sorted(targets()), sorted(HOURLY))

    def test_targets_are_known_scopes(self):
        for target in targets():
            self.assertIn(target, SCOPES)

    def test_faceless_board_is_covered(self):
        self.assertIn("8525", targets())
        self.assertIn("8525", SCOPES)

    def test_timer_is_hourly_and_enabled(self):
        self.assertIn("OnCalendar=*-*-* *:05:00", TIMER)
        self.assertIn("WantedBy=timers.target", TIMER)
        self.assertIn("Unit=ht-board-health.service", TIMER)

    def test_installer_ships_both_units(self):
        installer = (ROOT / "bin/install-board-health.sh").read_text()
        self.assertIn("ht-board-health.service", installer)
        self.assertIn("ht-board-health.timer", installer)
        self.assertIn("enable --now ht-board-health.timer", installer)


if __name__ == "__main__":
    unittest.main()
