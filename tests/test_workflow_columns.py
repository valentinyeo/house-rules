import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'fleet'))


def load(path):
    loader = importlib.machinery.SourceFileLoader('columns_' + Path(path).name.replace('-', '_'), str(ROOT / path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


class ColumnMigrationTests(unittest.TestCase):
    def test_broken_picker_drill_never_files_a_live_incident(self):
        import os
        import tempfile
        from types import SimpleNamespace
        drill = load('fleet/drill')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            watch, runner = root / 'watch', root / 'runner'
            fake_bin = root / '.local/bin'
            for path in (watch, runner, fake_bin):
                path.mkdir(parents=True)
            calls = root / 'vcc-calls'
            fake = fake_bin / 'vcc'
            fake.write_text('#!/bin/sh\necho called >> "' + str(calls) + '"\n')
            fake.chmod(0o755)
            env = dict(os.environ, HOME=str(root), FLEET_PICK_LKG=str(root / 'lkg'),
                       FLEET_RUNNER_STATE=str(runner), FLEET_WATCH_STATE=str(watch))
            ctx = SimpleNamespace(root=root, watch_state=watch, runner_state=runner,
                                  env=lambda: env)
            result = drill.drill_broken_picker(ctx)
            self.assertTrue(result['pass'], result)
            self.assertFalse(calls.exists(), 'sandbox attempted to file a live incident')
            self.assertEqual((root / 'lkg/workflow_columns.py').read_bytes(),
                             (ROOT / 'fleet/workflow_columns.py').read_bytes())

    def test_runner_briefs_do_not_send_new_prs_to_the_legacy_review_column(self):
        infra = (ROOT / 'fleet/briefs/infra.txt').read_text()
        self.assertNotIn('AI Review when the PR opens', infra)
        for name in ('ci', 'infra'):
            text = (ROOT / ('fleet/briefs/' + name + '.txt')).read_text()
            self.assertIn('Move Software Factory tickets', text)
            self.assertIn('PR opened -> Checks', text)
            self.assertIn('checks green -> Verifier', text)

    def test_picker_keeps_every_inflight_stage_and_alias(self):
        pick = load('fleet/pick')
        self.assertTrue({'Building', 'Doing', 'Checks', 'Verifier', 'AI Review'} <= set(pick.BOARDS['2060'][1]))
        self.assertEqual(pick.BOARDS['15'][1], ('In Progress', 'AI Review', 'QA'))

    def test_solo_wake_resumes_new_columns(self):
        solo = load('fleet/solo-wake')
        for name in ('Building', 'Doing', 'Checks', 'Verifier', 'AI Review'):
            ticket = {'section': name, 'assignees': [{'displayName': 'Me'}]}
            self.assertEqual(solo.candidates([ticket], 'Me'), [ticket], name)

    def test_pr_queue_recognizes_new_columns(self):
        queue = load('skills/hypertask-triage/scripts/pr-queue')
        self.assertTrue({'building', 'checks', 'verifier'} <= queue.BUILD)

    def test_review_without_pr_is_reported(self):
        wrong = load('skills/hypertask-triage/scripts/wrong-status')
        self.assertEqual(wrong.verdict('Verifier', [], {}), 'NO-PR')

    def test_release_watch_accepts_aliases_without_finishing_building(self):
        watch = load('fleet/sf-release-watch')
        self.assertTrue({'Building', 'Doing', 'Checks', 'Verifier', 'AI Review'} <= set(watch.COLUMNS))

    def test_real_move_command_prefers_new_name_and_preserves_human_review(self):
        import json
        merge = load('fleet/pr-merge')
        pr = {'state': 'OPEN', 'statusCheckRollup': [
            {'name': 'unit', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}]}
        for current, sections, expected in (
                ('Doing', ['Doing', 'Checks', 'AI Review'], 'AI Review'),
                ('Building', ['Building', 'Checks', 'Verifier', 'AI Review'], 'Verifier'),
                ('Valentin Review', ['Verifier'], None)):
            calls = []
            def api(cmd, *args, **kwargs):
                calls.append(cmd)
                if 'get' in cmd:
                    data = {'tasks': [{'projectId': 2060, 'section': current}]}
                elif 'list' in cmd:
                    data = {'sections': [{'name': name} for name in sections]}
                else:
                    data = {'success': True}
                return 0, json.dumps(data), ''
            with patch.object(merge, 'sh', side_effect=api):
                merge.sync_column('valentinyeo/house-rules', 'SOFT-2446', pr, {})
            moves = [cmd for cmd in calls if 'move' in cmd]
            self.assertEqual([cmd[-1] for cmd in moves], [expected] if expected else [])

    def test_merged_pass_stays_in_review_until_live_proof(self):
        import json
        merge = load('fleet/pr-merge')
        pr = {'state': 'MERGED', 'headRefOid': 'a' * 40}
        comments = [{'body': 'pstack-verifier: PASS @ ' + 'a' * 40,
                     'user': {'login': 'github-actions[bot]'}}]
        for current, review in (('Checks', 'AI Review'), ('Building', 'Verifier')):
            calls = []
            def api(cmd, *args, **kwargs):
                calls.append(cmd)
                if 'get' in cmd:
                    data = {'tasks': [{'projectId': 2060, 'section': current}]}
                elif 'list' in cmd:
                    data = {'sections': [{'name': name} for name in (current, review, 'Done')]}
                else:
                    data = {'success': True}
                return 0, json.dumps(data), ''
            with self.subTest(current=current), patch.object(merge, 'sh', side_effect=api):
                merge.sync_column('valentinyeo/house-rules', 'SOFT-2446', pr, {}, comments=comments)
            self.assertEqual([cmd[-1] for cmd in calls if 'move' in cmd], [review])

    def test_parking_preserves_the_actual_pr_stage(self):
        park = load('fleet/park')
        cases = [({'state': 'MERGED'}, 'Verifier'),
                 ({'state': 'OPEN'}, 'Checks'),
                 ({'state': 'OPEN', 'statusCheckRollup': [
                     {'name': 'unit', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}]}, 'Verifier'),
                 ({'number': 1}, 'Building'),
                 ({'state': 'OPEN', 'isDraft': True}, 'Building'),
                 ({'state': 'CLOSED'}, 'Todo')]
        for pr, expected in cases:
            for review in ('Verifier', 'AI Review'):
                want = review if expected == 'Verifier' else expected
                ticket = {'projectId': 2060, 'section': 'Building', 'title': 'work',
                          'pullRequests': [pr], 'labels': [{'name': 'brain-medium'}],
                          'assignees': [{'agent': {'displayName': 'Runner 6'}}]}
                sections = [{'name': n} for n in ('Todo', 'Building', 'Checks', review)]
                with self.subTest(pr=pr, review=review), \
                        patch.dict(park.os.environ, {'SHIP_SESSION_NAME': 'RUNNER 6'}), \
                        patch.object(park, 'blockers', return_value=[]), \
                        patch.object(park, 'preserve_owner', return_value={'runner': 6}), \
                        patch.object(park, 'free_claim'), patch.object(park, 'note'), \
                        patch.object(park, 'record_event'), \
                        patch.object(park, 'vcc', return_value={'sections': sections}) as api:
                    result = park.park_hand_back('SOFT-1', 'awaiting next run', ticket)
                    moves = [c.args[-1] for c in api.call_args_list if c.args[:2] == ('task', 'move')]
                    self.assertEqual(moves, [] if want == 'Building' else [want])
                    self.assertIn('-> ' + want, result)
                    result = park.park_too_hard('SOFT-1', 'needs stronger runner', ticket, dry=True)
                    self.assertIn('column ' + want, result)

    def test_latest_failure_overrules_a_pass_and_red_checks_return_to_checks(self):
        from workflow_columns import passed, stage
        pr = {'state': 'OPEN', 'headRefOid': 'a' * 40, 'statusCheckRollup': [
            {'name': 'unit', 'status': 'COMPLETED', 'conclusion': 'FAILURE'}]}
        comments = [{'body': 'pstack-verifier: ' + verdict + ' @ ' + 'a' * 40,
                     'user': {'login': 'github-actions[bot]'}} for verdict in ('PASS', 'FAIL')]
        self.assertFalse(passed(pr, comments))
        self.assertEqual(stage(pr, comments), 'Checks')
        pr['state'] = 'MERGED'
        self.assertEqual(stage(pr, comments), 'Verifier')

    def test_empty_checks_cannot_merge_even_with_a_current_pass(self):
        import tempfile
        from unittest.mock import Mock
        merge = load('fleet/pr-merge')
        for key in ('SOFT-2446', 'HYCI-2446'):
            pr = {'number': 7, 'state': 'OPEN', 'title': key + ' fix',
                  'baseRefName': 'main', 'headRefOid': 'a' * 40, 'mergeStateStatus': 'CLEAN',
                  'statusCheckRollup': [], 'updatedAt': '2020-01-01T00:00:00Z'}
            comments = [{'body': 'pstack-verifier: PASS @ ' + 'a' * 40,
                         'user': {'login': 'github-actions[bot]'}}]
            with tempfile.TemporaryDirectory() as directory:
                hooks = {'env': {}, 'pr': lambda: pr, 'comments': lambda *a: comments,
                         'sync': lambda *a: None, 'merge': Mock(return_value=(0, '', '')),
                         'ticket': lambda key: {'section': 'Checks', 'assignees': ['Runner 1']},
                         'owner': lambda key: None}
                with patch.object(merge, 'STATE', Path(directory)), \
                        patch.object(merge, 'FREEZE', Path(directory) / 'freeze'):
                    self.assertEqual(merge.one('valentinyeo/house-rules', 7, hooks=hooks), 'wait')
                hooks['merge'].assert_not_called()

    def test_successful_check_rerun_replaces_its_older_failure(self):
        from workflow_columns import stage
        pr = {'state': 'OPEN', 'statusCheckRollup': [
            {'name': 'unit', 'status': 'COMPLETED', 'conclusion': 'FAILURE', 'startedAt': '2026-11-17T10:00:00Z'},
            {'name': 'unit', 'status': 'COMPLETED', 'conclusion': 'SUCCESS', 'startedAt': '2026-11-17T11:00:00Z'}]}
        self.assertEqual(stage(pr, []), 'Verifier')

    def test_column_resolution_and_progression(self):
        from workflow_columns import resolve, stage, passed
        old = [{'name': 'Doing'}, {'name': 'AI Review'}, {'name': 'Checks'}]
        new = [{'name': 'Building'}, {'name': 'Verifier'}, {'name': 'Checks'}]
        self.assertEqual(resolve('Building', old), 'Doing')
        self.assertEqual(resolve('Building', old + new), 'Building')
        self.assertEqual(resolve('Verifier', old), 'AI Review')
        with self.assertRaises(ValueError):
            resolve('Verifier', [])
        pr = {'state': 'OPEN', 'headRefOid': 'a' * 40, 'statusCheckRollup': [
            {'name': 'unit', 'status': 'IN_PROGRESS'}]}
        self.assertEqual(stage(pr, []), 'Checks')
        pr['statusCheckRollup'][0].update(status='COMPLETED', conclusion='SUCCESS')
        self.assertEqual(stage(pr, []), 'Verifier')
        comment = {'body': 'pstack-verifier: PASS @ ' + 'a' * 40, 'user': {'login': 'github-actions[bot]'}}
        self.assertTrue(passed(pr, [comment]))
        self.assertEqual(stage(pr, [comment]), 'Verifier')
        pr['state'] = 'MERGED'
        self.assertEqual(stage(pr, [comment]), 'Verifier')
        self.assertEqual(stage(pr, []), 'Verifier')
        comment['body'] = comment['body'].replace('a' * 40, 'b' * 40)
        self.assertEqual(stage(pr, [comment]), 'Verifier')
        comment['body'] = 'pstack-verifier: PASS @ ' + 'a' * 40
        comment['user']['login'] = 'someone'
        self.assertFalse(passed(pr, [comment]))
        pr['state'] = 'OPEN'
        pr['statusCheckRollup'] = []
        self.assertEqual(stage(pr, []), 'Checks')


if __name__ == '__main__':
    unittest.main()
