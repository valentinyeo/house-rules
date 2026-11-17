"""CLI fixtures reconstruct the reported short-chat message-loss incident."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'fleet'))
from verify_gate import CHECKS, KINDS

GATE = ROOT / 'fleet/verify-score'
PIN = 'a' * 40
USES = f'valentinyeo/house-rules/.github/workflows/verify-gate.yml@{PIN}'


class Fixture:
    def __init__(self, root):
        self.repo = root / 'repo'
        self.repo.mkdir()
        self.evidence = root / 'evidence'
        self.evidence.mkdir()
        self.context_path = root / 'context.json'
        self.git('init', '-q')
        self.git('config', 'user.name', 'Verification fixture')
        self.git('config', 'user.email', 'fixture@users.noreply.github.com')
        self.put('README.md', '# Reported short-chat incident\n\nReconstruction, not historical runtime evidence.\n')
        source = '\n'.join(f'def register_{kind}(name): pass' for kind in KINDS)
        source += '\n' + '\n'.join(f'register_{kind}("short-chat-{kind}")' for kind in KINDS)
        source += '\n\ndef handoff(message):\n    return message\n'
        self.put('app/short_chat.py', source.replace('return message', 'return \"\"'))
        self.commit('base')
        base = self.git('rev-parse', 'HEAD')
        self.put('repro.json', json.dumps({'command': 'send message during short-chat handoff',
                 'output': 'FAIL: expected user message, received empty message', 'exit_code': 1}))
        self.commit('reproduce reported lost message')
        repro_sha = self.git('rev-parse', 'HEAD')
        self.put('test_message.py', 'from app.short_chat import handoff\nassert handoff("hello") == "hello", "user message lost"\nprint("PASS: user message preserved")\n')
        self.commit('failing user-message regression first')
        test_sha = self.git('rev-parse', 'HEAD')
        failing_run = subprocess.run([sys.executable, 'test_message.py'], cwd=self.repo, text=True, capture_output=True)
        assert failing_run.returncode != 0 and 'AssertionError: user message lost' in failing_run.stderr
        self.put('app/short_chat.py', source)
        for cached in (self.repo / 'app/__pycache__').glob('*'):
            cached.unlink()
        self.put('.verify/config.json', json.dumps({'adapter': 'python-registration-v1',
                 'source_roots': ['app'], 'skill': '.cursor/skills/verify-chat/SKILL.md',
                 'features': '.cursor/skills/verify-chat/features'}))
        self.put('.cursor/skills/verify-chat/SKILL.md', '---\nname: verify-chat\ndescription: Drive chat handoff\n---\n' +
                 '\n'.join(f'**{section}:** Run fixture handoff.' for section in
                           ('Launch', 'Doctor', 'Drive', 'Evidence', 'Cleanup', 'Helpers')))
        self.put('.cursor/skills/verify-chat/features/README.md', '# Chat\n\n[Handoff](handoff.md)\n')
        self.feature_body = '# Handoff\n\nPreserve the user message.\n\n' + '\n'.join(
            f'<!-- entry: {kind}|short-chat-{kind}|app/short_chat.py -->' for kind in KINDS)
        self.feature_body += '\n\n## Sub-features\n\nHandoff.\n\n## How to get to it (user POV)\n\nSend a message.\n\n## Driving it with Python\n\nCall handoff.\n\n## Gotchas\n\nPreserve pending messages.\n'
        self.put('.cursor/skills/verify-chat/features/handoff.md', self.feature_body)
        self.workflow = f'on:\n  pull_request:\njobs:\n  verify:\n    uses: {USES}\n    with:\n      pr-number: ${{{{ github.event.pull_request.number }}}}\n'
        self.put('.github/workflows/verify.yml', self.workflow)
        self.release_workflow = f'on:\n  workflow_dispatch:\njobs:\n  verify:\n    uses: {USES}\n    with:\n      pr-number: 12\n      mode: release\n      release-sha: ${{{{ github.sha }}}}\n  publish:\n    needs: verify\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo publish-fixture\n'
        self.put('.github/workflows/release.yml', self.release_workflow)
        self.put('AGENTS.md', '# Enforcement\n\n' + '\n'.join(f'| {item} | verify-gate / {item} |' for item in CHECKS))
        self.commit('fix preserves user message')
        head = self.git('rev-parse', 'HEAD')
        passing_run = subprocess.run([sys.executable, 'test_message.py'], cwd=self.repo, text=True, capture_output=True)
        assert passing_run.returncode == 0, passing_run.stderr
        self.context = {
            'repository': 'example/chat', 'pr_number': 12, 'head_sha': head, 'base_sha': base,
            'author_login': 'writer', 'labels': ['bug'], 'gate_run_id': 999, 'mode': 'pr',
            'policy': {'authors': {'writer': 'openai'},
                       'verifiers': {'verifier-bot': {'family': 'anthropic', 'workflow': '.github/workflows/pstack-verifier.yml'}},
                       'source_exclusions': {name: 'Fixture metadata or regression outside application source.' for name in
                           ('repro.json', 'test_message.py', '.verify/config.json', '.github/workflows/verify.yml', '.github/workflows/release.yml')},
                       'gate_workflow': USES, 'release_workflows': ['.github/workflows/release.yml']},
            'verdict': {'login': 'verifier-bot', 'comment_id': 42,
                        'comment_url': 'https://github.com/example/chat/pull/12#issuecomment-42',
                        'status': 'PASS', 'head_sha': head, 'run_url': 'https://github.com/example/chat/actions/runs/123',
                        'dataset': {'count': 2000, 'unit': 'pending user messages', 'production_comparison': 'Matches busiest observed queue.'}},
            'run': {'id': 123, 'html_url': 'https://github.com/example/chat/actions/runs/123',
                    'head_sha': head, 'conclusion': 'success', 'path': '.github/workflows/pstack-verifier.yml',
                    'jobs': [{'runner_name': 'GitHub Actions 1', 'labels': ['ubuntu-latest']}]},
            'test_run': {'id': 122, 'html_url': 'https://github.com/example/chat/actions/runs/122',
                         'head_sha': test_sha, 'conclusion': 'failure',
                         'test_path': 'test_message.py', 'command': 'python3 test_message.py',
                         'output': failing_run.stderr,
                         'jobs': [{'runner_name': 'GitHub Actions 2', 'labels': ['ubuntu-latest']}]},
        }
        self.manifest = {'head_sha': head, 'driver': 'agent', 'surface': 'chat handoff',
                         'command': 'send message, trigger short-chat, inspect next chat', 'sha256': {},
                         'history': {'fix_sha': head, 'repro_sha': repro_sha, 'repro_path': 'repro.json',
                                     'test_sha': test_sha, 'test_path': 'test_message.py', 'test_run_id': 122},
                         'skill_tests': {'command': 'python3 test_drive.py', 'passed': 2, 'failed': 0,
                                         'fixtures': {'pass': True, 'fail': True}}}
        self.add_artifact('drive', 'drive.log', passing_run.stdout)
        self.add_artifact('adversarial_report', 'adversary.md', '# Findings\n\nDropped 0. Pending-message replay preserved 2000 messages.\n')
        self.add_artifact('skill_test_output', 'skill-tests.log', 'Broken fixture rejected. Valid fixture accepted.\n')
        self.add_artifact('release_proof', 'handoff.trace', 'Trace fixture: message sent, handoff, message received.\n')
        self.add_artifact('seen_failing_output', 'seen-failing.log',
                          '\n'.join(f'BROKEN {item}: FAIL' for item in CHECKS) + '\n' +
                          '\n'.join(f'VALID {item}: PASS' for item in CHECKS) + '\n')
        self.save()

    def put(self, name, body):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git('add', '.')
        self.git('reset', '--', 'app/__pycache__')
        self.git('commit', '-qm', message)

    def add_artifact(self, key, name, body):
        (self.evidence / name).write_text(body)
        self.manifest[key] = name
        self.manifest['sha256'][name] = hashlib.sha256(body.encode()).hexdigest()

    def save(self):
        self.context_path.write_text(json.dumps(self.context))
        (self.evidence / 'verification.json').write_text(json.dumps(self.manifest))

    def run(self, item=None):
        self.save()
        command = [sys.executable, str(GATE), str(self.repo), '--context', str(self.context_path),
                   '--evidence', str(self.evidence), '--json']
        if item:
            command.extend(['--check', item])
        result = subprocess.run(command, text=True, capture_output=True)
        if not result.stdout:
            raise AssertionError(result.stderr)
        return result.returncode, json.loads(result.stdout)['items']

    def break_item(self, item):
        if item == 'real-app':
            (self.evidence / 'drive.log').unlink()
        elif item == 'agent-verifier':
            self.context['verdict']['login'] = 'human-owner'
        elif item == 'feature-map':
            self.put('.cursor/skills/verify-chat/features/handoff.md', self.feature_body.replace(
                '<!-- entry: command|short-chat-command|app/short_chat.py -->', ''))
        elif item == 'repro-first':
            self.manifest['history']['repro_sha'] = self.context['head_sha']
        elif item == 'test-first':
            self.context['test_run']['conclusion'] = 'success'
        elif item == 'adversary':
            self.context['policy']['verifiers']['verifier-bot']['family'] = 'openai'
        elif item == 'skill-tests':
            self.manifest['skill_tests']['fixtures']['fail'] = False
        elif item == 'hard-rules':
            self.put('AGENTS.md', '# Prose cannot enforce a rule.\n')
        elif item == 'current-head':
            self.context['verdict']['head_sha'] = self.context['base_sha']
        elif item == 'real-size':
            del self.context['verdict']['dataset']
        elif item == 'github-run':
            self.context['run']['jobs'][0]['labels'] = ['self-hosted']
        elif item == 'release-proof':
            (self.evidence / 'handoff.trace').unlink()
        elif item == 'seen-failing':
            self.add_artifact('seen_failing_output', 'seen-failing.log', 'VALID real-app: PASS\n')
        else:
            raise AssertionError(item)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(Path(self.temp.name))

    def test_gate_workflows_are_hosted_and_test_changed_code(self):
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/verify-gate.yml').read_text())
        self.assertNotIn('enforce', workflow[True]['workflow_call']['inputs'])
        for job in workflow['jobs'].values():
            self.assertEqual(job['runs-on'], 'ubuntu-latest')
            if 'if' in job:
                self.assertEqual(job['if'], '${{ always() }}')
        self.assertEqual(set(workflow['jobs']['check']['strategy']['matrix']['item']), set(CHECKS))
        steps = workflow['jobs']['collect']['steps']
        self.assertTrue(any('--demonstrate' in step.get('run', '') for step in steps))
        self.assertTrue(any('test_verify_gate.py -v' in step.get('run', '') for step in steps))
        test_workflow = yaml.safe_load((ROOT / '.github/workflows/verify-gate-tests.yml').read_text())
        checkout = test_workflow['jobs']['gate-tests']['steps'][0]
        self.assertEqual(checkout['with']['ref'], '${{ github.sha }}')
        self.assertEqual(test_workflow['jobs']['gate-tests']['runs-on'], 'ubuntu-latest')

    def test_collector_rejects_zip_traversal(self):
        import importlib.machinery
        import zipfile
        module = importlib.machinery.SourceFileLoader('verify_collect', str(ROOT / 'fleet/verify-collect')).load_module()
        api = module.GitHub('example/chat')
        api.pages = lambda *args: [{'id': 7, 'name': 'proof', 'expired': False}]
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('../escaped', 'unsafe')
        api.request = lambda *args, **kwargs: buffer.getvalue()
        with self.assertRaises(ValueError):
            api.artifacts(123, 'proof', self.fixture.evidence)
        self.assertFalse((self.fixture.evidence.parent / 'escaped').exists())

    def test_all_checks_pass_and_no_percentage(self):
        code, items = self.fixture.run()
        self.assertEqual(code, 0, items)
        self.assertEqual({item['id'] for item in items}, set(CHECKS))
        self.assertTrue(all(item['pass'] for item in items))

    def test_short_chat_without_real_app_run_is_blocked(self):
        self.fixture.break_item('real-app')
        code, items = self.fixture.run('real-app')
        self.assertEqual(code, 1)
        self.assertIn('drive.log', items[0]['missing'])

    def test_one_entry_per_kind_can_never_be_omitted(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.fixture.put('.cursor/skills/verify-chat/features/handoff.md',
                                 self.fixture.feature_body.replace(f'<!-- entry: {kind}|short-chat-{kind}|app/short_chat.py -->', ''))
                code, items = self.fixture.run('feature-map')
                self.assertEqual(code, 1)
                self.assertIn(f'short-chat-{kind}', items[0]['missing'])

    def test_unscanned_tracked_source_blocks(self):
        self.fixture.put('outside/new.py', 'register_command("forgotten")\n')
        self.fixture.commit('unmapped command outside roots')
        code, items = self.fixture.run('feature-map')
        self.assertEqual(code, 1)
        self.assertIn('outside/new.py', items[0]['missing'])

    def test_valid_reordered_block_frontmatter(self):
        self.fixture.put('.cursor/skills/verify-chat/SKILL.md', '---\ndescription: >\n  Drive real chat.\nname: verify-chat\n---\n' + '\n'.join(f'**{name}:** drive' for name in ('Launch', 'Doctor', 'Drive', 'Evidence', 'Cleanup', 'Helpers')))
        self.assertEqual(self.fixture.run('real-app')[0], 0)

    def test_one_entry_is_enough_when_complete(self):
        self.fixture.put('app/short_chat.py', 'register_job("short-chat-job")\n')
        body = self.fixture.feature_body
        for kind in KINDS:
            if kind != 'job':
                body = body.replace(f'<!-- entry: {kind}|short-chat-{kind}|app/short_chat.py -->', '')
        self.fixture.put('.cursor/skills/verify-chat/features/handoff.md', body)
        self.assertEqual(self.fixture.run('feature-map')[0], 0)

    def test_unsupported_source_and_dynamic_registration_fail_closed(self):
        self.fixture.put('app/client.ts', 'route("/chat")')
        self.assertEqual(self.fixture.run('feature-map')[0], 1)
        (self.fixture.repo / 'app/client.ts').unlink()
        self.fixture.put('app/short_chat.py', 'register_job(dynamic_name)\n')
        self.assertEqual(self.fixture.run('feature-map')[0], 1)

    def test_blueprint_receiver_route_cannot_be_omitted(self):
        self.fixture.put('app/short_chat.py', '@app.get("/home")\ndef home(): pass\n@admin.get("/admin")\ndef admin_page(): pass\napp.register_blueprint(admin)\n')
        self.fixture.put('.cursor/skills/verify-chat/features/handoff.md',
                         self.fixture.feature_body + '\n<!-- entry: endpoint|/home|app/short_chat.py -->\n')
        code, items = self.fixture.run('feature-map')
        self.assertEqual(code, 1)
        self.assertIn('/admin', items[0]['missing'])

    def test_human_author_fail_stale_and_same_family_verdicts_block(self):
        for change in ('author', 'fail', 'stale', 'same-family'):
            original = copy.deepcopy(self.fixture.context)
            with self.subTest(change=change):
                if change == 'author':
                    self.fixture.context['author_login'] = 'verifier-bot'
                    item = 'agent-verifier'
                elif change == 'fail':
                    self.fixture.context['verdict']['status'] = 'FAIL'
                    item = 'adversary'
                elif change == 'stale':
                    self.fixture.context['verdict']['head_sha'] = self.fixture.context['base_sha']
                    item = 'current-head'
                else:
                    self.fixture.context['policy']['verifiers']['verifier-bot']['family'] = 'openai'
                    item = 'adversary'
                self.assertEqual(self.fixture.run(item)[0], 1)
            self.fixture.context = original

    def test_repro_and_test_must_precede_actual_fix_commit(self):
        for key in ('repro_sha', 'test_sha'):
            self.fixture.manifest['history'][key] = self.fixture.context['head_sha']
            item = 'repro-first' if key == 'repro_sha' else 'test-first'
            self.assertEqual(self.fixture.run(item)[0], 1)

    def test_non_bug_pr_skips_only_history_requirements(self):
        self.fixture.context['labels'] = ['verification']
        self.fixture.manifest.pop('history')
        self.assertEqual(self.fixture.run('repro-first')[0], 0)
        self.assertEqual(self.fixture.run('test-first')[0], 0)
        self.fixture.break_item('real-app')
        self.assertEqual(self.fixture.run('real-app')[0], 1)

    def test_wrong_checkout_cannot_bless_another_head(self):
        self.fixture.context['head_sha'] = self.fixture.context['base_sha']
        self.fixture.context['verdict']['head_sha'] = self.fixture.context['base_sha']
        self.assertEqual(self.fixture.run('current-head')[0], 1)

    def test_paths_cannot_escape_evidence_root(self):
        for path in ('../outside.log', '/etc/passwd'):
            self.fixture.manifest['drive'] = path
            self.assertEqual(self.fixture.run('real-app')[0], 1)
        (self.fixture.evidence / 'link.log').symlink_to(self.fixture.repo / 'README.md')
        self.fixture.manifest['drive'] = 'link.log'
        self.assertEqual(self.fixture.run('real-app')[0], 1)

    def test_arbitrary_run_url_wrong_sha_and_gate_itself_block(self):
        for field, value in [('html_url', 'https://example.com/actions/runs/123'),
                             ('head_sha', self.fixture.context['base_sha']), ('id', 999)]:
            original = self.fixture.context['run'][field]
            self.fixture.context['run'][field] = value
            self.assertEqual(self.fixture.run('github-run')[0], 1)
            self.fixture.context['run'][field] = original

    def test_release_job_cannot_bypass_proof(self):
        self.fixture.put('.github/workflows/release.yml', self.fixture.release_workflow.replace('    needs: verify\n', ''))
        self.assertEqual(self.fixture.run('release-proof')[0], 1)

    def test_release_sha_requires_covered_head(self):
        self.fixture.context.update(mode='release', release_sha=self.fixture.context['base_sha'])
        self.assertEqual(self.fixture.run('release-proof')[0], 1)
        self.fixture.context['release_sha'] = self.fixture.context['head_sha']
        self.assertEqual(self.fixture.run('release-proof')[0], 0)

    def test_workflow_trigger_cannot_skip_verification(self):
        self.fixture.put('.github/workflows/verify.yml', self.fixture.workflow.replace('pull_request:', 'workflow_dispatch:'))
        self.assertEqual(self.fixture.run('hard-rules')[0], 1)

    def test_text_output_names_missing_artifact(self):
        self.fixture.break_item('real-app')
        self.fixture.save()
        run = subprocess.run([sys.executable, str(GATE), str(self.fixture.repo), '--context',
                              str(self.fixture.context_path), '--evidence', str(self.fixture.evidence), '--check', 'real-app'],
                             text=True, capture_output=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn('FAIL Agent drives the real app | missing artifact:', run.stdout)
        self.assertNotIn('Score', run.stdout)


def pair_test(item):
    def test(self):
        self.fixture.break_item(item)
        code, items = self.fixture.run(item)
        self.assertEqual(code, 1, items)
        self.assertFalse(items[0]['pass'])
        self.assertTrue(items[0]['missing'])
        other = Path(self.temp.name) / 'valid'
        other.mkdir()
        passing = Fixture(other)
        code, items = passing.run(item)
        self.assertEqual(code, 0, items)
        self.assertTrue(items[0]['pass'])
    return test


for identifier in CHECKS:
    setattr(GateTests, 'test_fixture_pair_' + identifier.replace('-', '_'), pair_test(identifier))


def demonstrate():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for item in CHECKS:
            directory = root / ('broken-' + item)
            directory.mkdir()
            fixture = Fixture(directory)
            fixture.break_item(item)
            code, checks = fixture.run(item)
            if code != 1 or checks[0]['pass']:
                raise AssertionError(f'Broken fixture passed: {item}')
            print(f"BROKEN {item}: FAIL | missing artifact: {checks[0]['missing']}")
        directory = root / 'valid'
        directory.mkdir()
        fixture = Fixture(directory)
        for item in CHECKS:
            code, checks = fixture.run(item)
            if code != 0:
                raise AssertionError(checks)
            print(f'VALID {item}: PASS')


def incident():
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Fixture(Path(tmp))
        print('Short-chat incident reconstruction, not historical runtime evidence.')
        print('BEFORE FIX: actual failing regression output')
        print(fixture.context['test_run']['output'].rstrip())
        print('AFTER FIX: actual fixture output')
        print((fixture.evidence / 'drive.log').read_text().rstrip())
        fixture.break_item('real-app')
        code, items = fixture.run('real-app')
        assert code == 1
        print(f"MISSING DRIVE: FAIL | missing artifact: {items[0]['missing']}")


if __name__ == '__main__':
    if '--incident' in sys.argv:
        incident()
    elif '--demonstrate' in sys.argv:
        demonstrate()
    else:
        unittest.main()
