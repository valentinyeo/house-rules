"""hosted_chats must list a headless Multibot chat (no tmux session) while its host process lives."""
import json
import sys
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fleet"))
import roster  # noqa: E402


def fake_mp(root, tmux_sessions, alive_pids):
    mp = types.SimpleNamespace()
    mp.PROVIDERS = ("claude", "codex")
    mp.state_root = lambda: root
    mp.published_names = lambda: {}
    mp.tmux_names = lambda: set(tmux_sessions)
    mp.read_json = lambda p: json.loads(Path(p).read_text()) if Path(p).exists() else None
    mp.pid_alive = lambda pid: pid in alive_pids
    return mp


def write_chat(root, key, tmux, pid):
    host = root / "agent-host"
    host.mkdir(parents=True, exist_ok=True)
    (host / f"{key}.config.json").write_text(json.dumps({"tmux": tmux, "enabled": True}))
    (host / f"{key}.state.json").write_text(json.dumps({"sid": f"sid-{key}", "provider": "claude", "pid": pid}))


class HostedChats(unittest.TestCase):
    def test_headless_chat_counts_only_while_its_host_lives(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_chat(root, "a", "live-headless", 101)
            write_chat(root, "b", "live-dead", 102)
            write_chat(root, "c", "live-tmux", 103)
            with mock.patch.object(roster, "_mp_send", lambda: fake_mp(root, {"live-tmux"}, {101})):
                chats = roster.hosted_chats()
        self.assertEqual(set(chats), {"live-headless", "live-tmux"})
        self.assertEqual(chats["live-headless"]["state"], "idle")
        self.assertEqual(chats["live-tmux"]["state"], "stopped")


class NamePatterns(unittest.TestCase):
    def test_wildcard_covers_a_new_hosted_chat_id(self):
        rows = [{"name": "live-chromescribe-{*}"}]
        self.assertEqual(roster.row_for(rows, "live-chromescribe-mwmmhm4f")["name"], "live-chromescribe-{*}")
        self.assertEqual(roster.row_for(rows, "live-chromescribe-9f2a1c")["name"], "live-chromescribe-{*}")
        self.assertIsNone(roster.row_for(rows, "live-screencast2-mwmmhm4f"))
        self.assertIsNone(roster.row_for(rows, "live-chromescribex-mwmmhm4f"))

    def test_number_and_letter_placeholders_still_apply(self):
        self.assertEqual(roster.row_for([{"name": "ht-or-runner-{n}"}], "ht-or-runner-7")["name"],
                         "ht-or-runner-{n}")
        self.assertIsNone(roster.row_for([{"name": "ht-or-runner-{n}"}], "ht-or-runner-x"))
        self.assertEqual(roster.row_for([{"name": "multibot-runner-{x}"}], "multibot-runner-a")["name"],
                         "multibot-runner-{x}")


if __name__ == "__main__":
    unittest.main()
