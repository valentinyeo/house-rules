import importlib.machinery
import importlib.util
import json
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'fleet/solo-wake'
loader = importlib.machinery.SourceFileLoader('solo_wake_events', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
wake = importlib.util.module_from_spec(spec)
loader.exec_module(wake)


class EventWakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.project = self.home / '.claude/projects/test'
        self.project.mkdir(parents=True)
        self.now = time.time()
        self.row = {'name': 'test-lead', 'kind': 'lead', 'tmux': 'live-test'}
        self.session = {'via': 'live', 'key': 'live-test', 'sid': 'current',
                        'state': 'idle', 'age': 3600}
        self.chats = {'live-test': {'transcript': 'current', 'name': 'Test Lead'}}

    def event(self, origin='task_notification', age=60, **fields):
        return dict(type='user', turnOrigin=origin,
                    timestamp=datetime.fromtimestamp(self.now - age, timezone.utc).isoformat(),
                    message={'role': 'user', 'content': '<task-notification>worker finished</task-notification>'},
                    **fields)

    def run_watch(self, events, other=None, nudges=None):
        (self.project / 'current.jsonl').write_text('\n'.join(json.dumps(e) for e in events) + '\n')
        if other:
            (self.project / 'other.jsonl').write_text(json.dumps(other) + '\n')
        logs, sent = [], []
        state = {'loop:test-lead': nudges or []}
        with (patch.multiple(wake, HOME=self.home, DRY_RUN=False, STATE=self.home / 'state.json',
                            log=logs.append, identity_gap=lambda name: None,
                            send=lambda session, text: (sent.append(text) is None, 'test')),
                patch.object(wake.roster, 'rows', return_value=[self.row]), \
                patch.object(wake, 'session_of', return_value=self.session)):
            wake.loop_watch(self.chats, {}, state, self.now)
        return logs, sent, state

    def test_native_watcher_result_prevents_false_nag_and_clears_nudges(self):
        logs, sent, state = self.run_watch([self.event()], nudges=[self.now - 4000, self.now - 2000])
        self.assertEqual(sent, [], logs)
        self.assertTrue(any('loop: ok' in line for line in logs), logs)
        self.assertEqual(state['loop:test-lead'], [])

    def test_stale_event_still_nags(self):
        logs, sent, _ = self.run_watch([self.event(age=3000)])
        self.assertEqual(len(sent), 1, logs)

    def test_other_chat_event_does_not_hide_dead_loop(self):
        logs, sent, _ = self.run_watch([], other=self.event())
        self.assertEqual(len(sent), 1, logs)

    def test_claim_and_future_event_do_not_hide_dead_loop(self):
        claim = self.event(origin='prompt')
        claim['message']['content'] = 'My event loop is active. "turnOrigin":"task_notification"'
        assistant = self.event()
        assistant['type'] = 'assistant'
        logs, sent, _ = self.run_watch([claim, assistant, self.event(age=-3600)])
        self.assertEqual(len(sent), 1, logs)

    def test_formatted_scheduled_fallback_counts(self):
        logs, sent, _ = self.run_watch([self.event(origin='scheduled')])
        self.assertEqual(sent, [], logs)

    def test_newest_timestamp_wins_over_append_order(self):
        logs, sent, _ = self.run_watch([self.event(), self.event(age=3000)])
        self.assertEqual(sent, [], logs)


if __name__ == '__main__':
    unittest.main()


class NamelessIdentityTests(EventWakeTests):
    def run_nameless(self, name, age=60):
        self.chats = {'live-test': {'transcript': 'current', 'name': name}}
        (self.project / 'current.jsonl').write_text(json.dumps(self.event(age=age)) + '\n')
        logs, sent = [], []
        with (patch.multiple(wake, HOME=self.home, DRY_RUN=False, STATE=self.home / 'state.json',
                            log=logs.append, identity_gap=lambda n: 'a token' if n else 'a Multibot name (the tab has none)',
                            send=lambda session, text: (sent.append(text) is None, 'test')),
                patch.object(wake.roster, 'rows', return_value=[self.row]), \
                patch.object(wake, 'session_of', return_value=self.session)):
            wake.loop_watch(self.chats, {}, {}, self.now)
        return logs, sent

    def test_nameless_chat_is_logged_but_never_asked_to_log_in_as_none(self):
        logs, sent = self.run_nameless(None)
        self.assertTrue(any('identity: gap' in line for line in logs), logs)
        self.assertFalse(any('None' in text for text in sent), sent)
        self.assertEqual(sent, [], sent)

    def test_nameless_tab_with_a_dead_loop_is_not_nudged(self):
        logs, sent = self.run_nameless('', age=3000)
        self.assertEqual(sent, [], logs)
        self.assertTrue(any('no Multibot name' in line for line in logs), logs)

    def test_named_chat_with_a_dead_loop_is_still_nudged(self):
        logs, sent = self.run_nameless('Test Lead', age=3000)
        self.assertEqual(len(sent), 1, logs)

    def test_named_chat_with_a_gap_is_still_asked_to_log_in(self):
        logs, sent = self.run_nameless('Test Lead')
        self.assertTrue(any('Test Lead' in text for text in sent), sent)
