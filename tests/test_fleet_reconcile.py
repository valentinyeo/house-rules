import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


r = load('fleet_reconcile', ROOT / 'fleet/reconcile')
lease = load('fleet_lease', ROOT / 'fleet/lease')
NOW = 1800000000
HEAD = 'a' * 40
POLICY = {'authors': {'writer': 'openai'}, 'verifiers': {'verifier': {
    'family': 'anthropic', 'workflow': '.github/workflows/pstack-verifier.yml'}}}


def task(column='Doing'):
    return {'ticketNumber': 'SOFT-1', 'section': column, 'projectId': 2060,
            'updatedAt': NOW - 8000, 'assignees': [{'displayName': 'Runner 9'}]}


def pull(state='OPEN', checks='green', passed=False):
    return r.Pull('https://github.com/valentinyeo/another-repo/pull/1', state, checks, passed)


def comment(status='PASS', head=HEAD, when='2026-01-01', number=1):
    verdict = {'status': status, 'head_sha': head,
               'run_url': 'https://github.com/valentinyeo/another-repo/actions/runs/9'}
    return {'user': {'login': 'verifier'}, 'body': '```verify-verdict\n' + json.dumps(verdict) + '\n```',
            'updated_at': when, 'id': number}


class ReconcileTest(unittest.TestCase):
    def test_idle_doing_returns_todo(self):
        self.assertEqual(r.target(r.Facts('Doing', 7201)), ('Todo', 'no live lease and no PR'))

    def test_table(self):
        cases = [
            (r.Facts('Todo', 8000, True), 'Doing'),
            (r.Facts('Doing', 8000, True, (pull(checks='red'),)), 'Doing'),
            (r.Facts('Doing', 8000, False, (pull(checks='running'),)), 'Checks'),
            (r.Facts('Doing', 8000, False, (pull(checks='red'),)), 'Checks'),
            (r.Facts('Doing', 8000, False, (pull(checks='missing'),)), 'Checks'),
            (r.Facts('Doing', 8000, False, (pull(),)), 'AI Review'),
            (r.Facts('Checks', 8000, False, (pull(passed=True),)), 'AI Review'),
            (r.Facts('Doing', 8000, False, (pull('MERGED', passed=True),)), 'Done'),
            (r.Facts('Doing', 8000, False, (pull('MERGED'),)), 'AI Review'),
            (r.Facts('Doing', 8000, False, (pull('MERGED', passed=True), pull(checks='red'))), 'Checks'),
            (r.Facts('Doing', 7199), 'Doing'),
            (r.Facts('Doing', 7200), 'Todo'),
            (r.Facts('Valentin Review', 8000, True), 'Valentin Review'),
            (r.Facts('Done', 8000, True), 'Done'),
        ]
        for facts, expected in cases:
            with self.subTest(facts=facts):
                self.assertEqual(r.target(facts)[0], expected)

    def test_no_writes_by_default_then_one_move_and_log(self):
        t = task()
        facts = r.Facts('Doing', 8000)
        with patch.object(r, 'api') as api, patch.object(r, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(r.reconcile(t, facts), 'Todo')
            api.assert_not_called()
            run.assert_not_called()
            r.reconcile(t, facts, apply=True)
            api.assert_called_once_with('task', 'move', 'SOFT-1', '--section', 'Todo')
            self.assertEqual(run.call_count, 1)
            self.assertIn('no live lease and no PR', run.call_args.args[-1])
            self.assertEqual(t['assignees'], [{'displayName': 'Runner 9'}])
            api.reset_mock()
            run.reset_mock()
            r.reconcile(task('Todo'), r.Facts('Todo', 8000), apply=True)
            api.assert_not_called()
            run.assert_not_called()

    def test_other_board_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside board'):
            r.reconcile({**task(), 'projectId': 15}, r.Facts('Doing', 8000), True)

    def test_check_rollup(self):
        self.assertEqual(r.check_state([]), 'missing')
        self.assertEqual(r.check_state([{'status': 'IN_PROGRESS', 'conclusion': ''}]), 'running')
        self.assertEqual(r.check_state([{'status': 'COMPLETED', 'conclusion': 'FAILURE'}]), 'red')
        self.assertEqual(r.check_state([{'status': 'COMPLETED', 'conclusion': 'CANCELLED'}]), 'red')
        self.assertEqual(r.check_state([{'status': 'COMPLETED', 'conclusion': 'SUCCESS'}, {'state': 'SUCCESS'}]), 'green')
        self.assertEqual(r.check_state([{'state': 'PENDING'}]), 'running')

    def test_boundary_and_link_ticket_names(self):
        self.assertTrue(r.names_ticket({'title': 'fix SOFT-1', 'body': ''}, 'SOFT-1'))
        self.assertTrue(r.names_ticket({'body': 'https://app.hypertask.ai/detail/project-2060/1'}, 'SOFT-1'))
        self.assertFalse(r.names_ticket({'title': 'SOFT-10 SOFT-1-extra xSOFT-1'}, 'SOFT-1'))
        self.assertFalse(r.names_ticket({'body': 'project-2060/10'}, 'SOFT-1'))

    def test_discovery_other_repository_and_closed_pr(self):
        p = {'title': 'SOFT-1 fix', 'body': '', 'url': pull().url, 'state': 'OPEN',
             'repository': {'nameWithOwner': 'valentinyeo/another-repo'}, 'number': 1}
        result = {'data': {'q0': {'pageInfo': {'hasNextPage': False}, 'nodes': [p, {**p, 'state': 'CLOSED'}, {**p, 'title': 'SOFT-10 fix'}]}}}
        with patch.object(r, 'run', return_value=json.dumps(result)) as run:
            self.assertEqual(r.discover(['SOFT-1']), {'SOFT-1': [p]})
            self.assertIn('user:hypertask-ai', run.call_args.args[-1])
        result['data']['q0']['pageInfo']['hasNextPage'] = True
        with patch.object(r, 'run', return_value=json.dumps(result)), self.assertRaisesRegex(ValueError, 'truncated'):
            r.discover(['SOFT-1'])

    def test_board_paginates_server_clamped_pages(self):
        with patch.object(r, 'api', side_effect=[{'tasks': [task()], 'total': 2, 'nextCursor': 'next'},
                                               {'tasks': [{**task(), 'ticketNumber': 'SOFT-2'}], 'total': 2, 'nextCursor': None}]) as api:
            self.assertEqual(len(r.tickets()), 2)
            self.assertIn('--cursor', api.call_args.args)
        with patch.object(r, 'api', return_value={'tasks': [task()], 'total': 2}), self.assertRaisesRegex(ValueError, 'incomplete'):
            r.tickets()

    def test_current_head_cross_family_actions_verdict(self):
        workflow = {'head_sha': HEAD, 'status': 'completed', 'conclusion': 'success',
                    'path': '.github/workflows/pstack-verifier.yml'}
        jobs = [{'jobs': [{'runner_name': 'GitHub Actions 7', 'labels': ['ubuntu-latest']}]}]
        with patch.object(r, 'run', side_effect=[json.dumps(workflow), json.dumps(jobs)]):
            self.assertTrue(r.pass_on_head([comment()], HEAD, 'writer', 'valentinyeo/another-repo', POLICY))
        for comments, policy in [([comment(head='b' * 40)], POLICY),
                                 ([comment(), comment('FAIL', when='2026-02-01', number=2)], POLICY),
                                 ([comment()], {}),
                                 ([comment()], {**POLICY, 'authors': {'writer': 'anthropic'}}),
                                 ([{'user': {'login': 'verifier'}, 'body': 'PASS ' + HEAD}], POLICY)]:
            with self.subTest(comments=comments, policy=policy), patch.object(r, 'run') as run:
                self.assertFalse(r.pass_on_head(comments, HEAD, 'writer', 'valentinyeo/another-repo', policy))
                run.assert_not_called()
        for bad in [{**workflow, 'head_sha': 'b' * 40}, {**workflow, 'path': '.github/workflows/verify-gate.yml'}]:
            with patch.object(r, 'run', return_value=json.dumps(bad)):
                self.assertFalse(r.pass_on_head([comment()], HEAD, 'writer', 'valentinyeo/another-repo', POLICY))
        jobs[0]['jobs'][0]['labels'] = ['self-hosted']
        with patch.object(r, 'run', side_effect=[json.dumps(workflow), json.dumps(jobs)]):
            self.assertFalse(r.pass_on_head([comment()], HEAD, 'writer', 'valentinyeo/another-repo', POLICY))


class LeaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.path = self.directory / 'SOFT-1.json'

    def seed(self, **overrides):
        value = dict(pid=os.getpid(), host=socket.gethostname(), started=NOW - 100, last_beat=NOW)
        self.path.write_text(json.dumps({**value, **overrides}))

    def test_live_stale_crashed_and_foreign(self):
        self.assertFalse(r.live_lease('SOFT-1', NOW, self.directory))
        self.seed()
        self.assertTrue(r.live_lease('SOFT-1', NOW, self.directory))
        self.seed(last_beat=NOW - 900)
        self.assertFalse(r.live_lease('SOFT-1', NOW, self.directory))
        self.seed(pid=999999999)
        self.assertFalse(r.live_lease('SOFT-1', NOW, self.directory))
        self.seed(host='other-host')
        with self.assertRaisesRegex(ValueError, 'another host'):
            r.live_lease('SOFT-1', NOW, self.directory)
        self.seed(host='other-host', last_beat=NOW - 900)
        self.assertFalse(r.live_lease('SOFT-1', NOW, self.directory))
        self.seed(last_beat=NOW + 1)
        self.assertFalse(r.live_lease('SOFT-1', NOW, self.directory))

    def test_start_beat_end_atomic_and_idempotent(self):
        pid = os.getpid()
        lease.write('SOFT-1', 'start', pid, self.directory, NOW)
        lease.write('SOFT-1', 'start', pid, self.directory, NOW + 1)
        lease.write('SOFT-1', 'beat', pid, self.directory, NOW + 2)
        record = json.loads(self.path.read_text())
        self.assertEqual(record['started'], NOW)
        self.assertEqual(record['last_beat'], NOW + 2)
        lease.write('SOFT-1', 'end', pid + 1, self.directory, NOW + 3)
        self.assertTrue(self.path.exists())
        lease.write('SOFT-1', 'end', pid, self.directory, NOW + 3)
        lease.write('SOFT-1', 'end', pid, self.directory, NOW + 3)
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.directory.glob('SOFT-1.*')), [self.directory / 'SOFT-1.lock'])

    def test_other_worker_cannot_overwrite_live_lease(self):
        self.seed(host='other-host')
        with self.assertRaisesRegex(ValueError, 'another live worker'):
            lease.write('SOFT-1', 'start', os.getpid(), self.directory, NOW)
        self.assertEqual(json.loads(self.path.read_text())['host'], 'other-host')
        self.seed(pid=999999999)
        lease.write('SOFT-1', 'start', os.getpid(), self.directory, NOW)
        self.assertEqual(json.loads(self.path.read_text())['pid'], os.getpid())

    def test_wrapper_fast_command_and_exit_status(self):
        env = {**os.environ, 'FLEET_LEASE_DIR': str(self.directory)}
        for code in (0, 7):
            result = subprocess.run([str(ROOT / 'fleet/lease'), 'SOFT-1', 'run', '--', sys.executable, '-c', f'raise SystemExit({code})'], env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertFalse(self.path.exists())

    def test_child_exits_between_spawn_and_first_lease(self):
        child = Mock(pid=999999999, returncode=0)
        child.poll.return_value = 0
        with patch.object(sys, 'argv', ['lease', 'SOFT-1', 'run', '--', 'true']), \
                patch.object(lease.subprocess, 'Popen', return_value=child), \
                patch.object(lease, 'write', side_effect=[ValueError('worker PID does not exist'), None]):
            self.assertEqual(lease.main(), 0)
        child.terminate.assert_not_called()

    def test_child_exits_between_poll_and_beat(self):
        child = Mock(pid=999999999, returncode=0)
        child.poll.side_effect = [None, 0]
        with patch.object(sys, 'argv', ['lease', 'SOFT-1', 'run', '--', 'true']), \
                patch.object(lease.subprocess, 'Popen', return_value=child), \
                patch.object(lease, 'write', side_effect=[None, ValueError('worker PID does not exist'), None]):
            self.assertEqual(lease.main(), 0)
        child.terminate.assert_not_called()

    def test_wrapper_registers_running_child(self):
        env = {**os.environ, 'FLEET_LEASE_DIR': str(self.directory)}
        code = "import json,os,pathlib; p=pathlib.Path(os.environ['FLEET_LEASE_DIR'])/'SOFT-1.json'; import time; time.sleep(.2); d=json.loads(p.read_text()); assert d['pid']==os.getpid()"
        result = subprocess.run([str(ROOT / 'fleet/lease'), 'SOFT-1', 'run', '--', sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
