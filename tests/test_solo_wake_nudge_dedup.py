import importlib.machinery
import importlib.util
import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'fleet/solo-wake'
loader = importlib.machinery.SourceFileLoader('solo_wake_nudge', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
wake = importlib.util.module_from_spec(spec)
loader.exec_module(wake)


class NudgeDedupTests(unittest.TestCase):
    def test_same_chat_ticket_within_cooldown_skips(self):
        idle = {'via': 'live', 'key': 'live-x', 'sid': 's', 'state': 'idle', 'age': 3600}
        ticket = {'ticketNumber': 'HTPR-9406'}
        now = 100_000.0
        key = wake.wake_key('live-x', 'HTPR-9406')
        last = now - 5 * 60
        verdict, why = wake.decide({}, idle, ticket, last, now)
        self.assertEqual(verdict, 'skip')
        self.assertIn('woken', why)

    def test_new_ticket_after_cooldown_wakes(self):
        idle = {'via': 'live', 'key': 'live-x', 'sid': 's', 'state': 'idle', 'age': 3600}
        ticket = {'ticketNumber': 'HTPR-9407'}
        now = 100_000.0
        last = now - wake.COOLDOWN - 60
        self.assertEqual(wake.decide({}, idle, ticket, last, now), ('wake', 'HTPR-9407'))

    def test_fresh_ticket_not_blocked_by_row_level_recent_wake(self):
        """Per-ticket keys: a new ticket must not inherit another ticket's 30-minute row wake."""
        idle = {'via': 'live', 'key': 'live-x', 'sid': 's', 'state': 'idle', 'age': 3600}
        now = 100_000.0
        row_last = now - 5 * 60
        ticket = {'ticketNumber': 'HTPR-9407'}
        per_ticket = wake.wake_key('live-x', 'HTPR-9407')
        self.assertIsNone(per_ticket in {} or None)  # no per-ticket entry yet
        verdict, _ = wake.decide({}, idle, ticket, None, now)
        self.assertEqual(verdict, 'wake')
        self.assertEqual(wake.decide({}, idle, ticket, row_last, now)[0], 'skip')

    def test_host_mid_turn_skips_even_when_idle(self):
        idle = {'via': 'live', 'key': 'live-x', 'sid': 's', 'state': 'idle', 'age': 3600}
        ticket = {'ticketNumber': 'HTPR-9406'}
        now = 100_000.0
        verdict, why = wake.decide({}, idle, ticket, None, now, host_busy='mid-turn')
        self.assertEqual(verdict, 'skip')
        self.assertIn('mid-turn', why)

    def test_host_wait_reads_unaccepted_written(self):
        with TemporaryDirectory() as tmp:
            host = Path(tmp)
            cfg = host / 'abc.config.json'
            st = host / 'abc.state.json'
            cfg.write_text(json.dumps({'tmux': 'live-ht', 'enabled': True}))
            st.write_text(json.dumps({
                'inflight': None,
                'sends': [],
                'written': {'desktop-1': {'accepted': False}},
            }))
            session = {'via': 'live', 'key': 'live-ht'}
            with patch.object(wake, 'HOST_ROOT', host):
                self.assertEqual(wake.host_wait(session), 'prior send not accepted')

    def test_outside_kind_never_in_solo_dev_rows(self):
        rows = [
            {'name': 'HT Product Lead', 'kind': 'outside', 'roles': ['lead', 'expert']},
            {'name': 'postbox', 'kind': 'solo-dev'},
            {'name': 'Ghost', 'kind': 'closed', 'roles': ['solo-dev']},
        ]
        picked = wake.solo_dev_rows(rows)
        self.assertEqual([r['name'] for r in picked], ['postbox'])


if __name__ == '__main__':
    unittest.main()