"""SOFT-2716: a dead session's announcement over a day old stops being a roster row; live and static ones stay."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fleet"))
import roster  # noqa: E402

NOW = 1_800_000_000


def iso(age_s):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(NOW - age_s))


class StaleAnnouncements(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        patches = [mock.patch.object(roster, "ANNOUNCE", self.dir),
                   mock.patch.object(roster, "static_rows", lambda: [{"name": "postbox", "kind": "solo-dev"}]),
                   mock.patch.object(roster.time, "time", lambda: NOW),
                   mock.patch.object(roster, "live_keys", lambda: ({"live-alive"}, {"sid-alive"}))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def put(self, tmux, age_s, **extra):
        entry = dict(tmux=tmux, sid=f"sid-{tmux[5:]}", seen=iso(age_s))
        (self.dir / f"{tmux}.json").write_text(json.dumps(dict(entry, **extra)))

    def names(self):
        return {r["name"] for r in roster.rows()}

    def test_fresh_dead_kept_old_dead_dropped_old_live_kept(self):
        self.put("live-fresh-dead", 3600)
        self.put("live-old-dead", 25 * 3600)
        self.put("live-alive", 25 * 3600)
        self.put("live-sid", 30 * 3600, sid="sid-alive")
        self.assertEqual(self.names(), {"postbox", "live-fresh-dead", "live-alive", "live-sid"})

    def test_static_row_never_dropped_even_with_old_dead_announcement(self):
        self.put("postbox", 40 * 3600)
        self.assertEqual(self.names(), {"postbox"})
        self.assertEqual(roster.stale_announcements(), [])

    def test_no_seen_or_unreadable_seen_is_kept(self):
        (self.dir / "live-noseen.json").write_text(json.dumps(dict(tmux="live-noseen")))
        (self.dir / "live-badseen.json").write_text(json.dumps(dict(tmux="live-badseen", seen="yesterday")))
        self.assertEqual(self.names(), {"postbox", "live-noseen", "live-badseen"})

    def test_liveness_unreadable_drops_nothing(self):
        self.put("live-old-dead", 25 * 3600)
        with mock.patch.object(roster, "live_keys", side_effect=RuntimeError("tmux gone")):
            self.assertEqual(self.names(), {"postbox", "live-old-dead"})

    def test_archive_moves_only_stale_files(self):
        self.put("live-fresh-dead", 3600)
        self.put("live-old-dead", 25 * 3600)
        self.put("live-alive", 25 * 3600)
        moved = roster.archive_stale()
        self.assertEqual([p.name for p in moved], ["live-old-dead.json"])
        self.assertTrue((self.dir / "stale" / "live-old-dead.json").is_file())
        self.assertEqual({p.name for p in self.dir.glob("*.json")}, {"live-fresh-dead.json", "live-alive.json"})
        self.assertEqual(len(roster.announced()), 2, "announce/stale/ is not read back")


if __name__ == "__main__":
    unittest.main()
