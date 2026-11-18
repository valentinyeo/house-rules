import os
from pathlib import Path
import subprocess
import tempfile
import unittest


FACTS = Path(os.environ.get('FACTS_SCRIPT',
                           Path(__file__).resolve().parents[1] / 'skills/verification-check/facts.sh'))
DRIFT_FILES = [
    'create-verification-skill/SKILL.md',
    'maintain-verification-skill/SKILL.md',
    'create-formal-verification-skill/SKILL.md',
    'maintain-formal-verification-skill/SKILL.md',
    'poteto-mode/playbooks/shipping.md',
    'poteto-mode/playbooks/bug-fix.md',
    'poteto-mode/playbooks/eval.md',
    'principle-prove-it-works/SKILL.md',
]


class VerificationCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.home = self.root / 'home'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        PATH=f'{self.bin}:{os.environ["PATH"]}')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('remote', 'add', 'origin', str(self.repo))
        self.put('README.md', '# App\n')
        self.put('.github/workflows/verify.yml', '''name: verifier
on: [pull_request]
concurrency:
  group: verify-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  verifier:
    runs-on: ubuntu-latest
    steps:
      - run: ./verify --base --head --touched --reuse-base
''')
        self.commit()
        gh = self.bin / 'gh'
        gh.write_text('''#!/usr/bin/env python3
import json, os, sys
args = ' '.join(sys.argv[1:])
if 'repo view' in args:
    print('PRIVATE')
elif 'headRefOid' in args:
    print(json.dumps([{'number': n, 'headRefOid': f'sha{n}'} for n in (3, 2, 1)]))
elif 'pr list' in args:
    print('no verifier comment')
elif '/runs/11/jobs' in args:
    if os.environ.get('FAIL_JOBS'):
        sys.exit(1)
    print(json.dumps({'jobs': [{'id': 101}, {'id': 102}]}))
elif '/runs/12/jobs' in args:
    print(json.dumps({'jobs': [{'id': 103}]}))
elif '/actions/runs?' in args:
    print(json.dumps({'workflow_runs': [{'id': 11, 'name': 'verify', 'status': os.environ.get('RUN_STATUS', 'completed')}, {'id': 12, 'name': 'lint', 'status': 'completed'}]}))
elif 'rules' in args:
    print('[]')
elif 'required_status_checks' in args:
    print('{"contexts":["pstack-verifier"],"checks":[]}')
else:
    print('[]')
''')
        gh.chmod(0o755)
        for version in ('0.15.42', '0.15.43'):
            for name in DRIFT_FILES:
                f = self.home / '.claude/plugins/cache/test/pstack' / version / 'skills' / name
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(f'# {name}\n')
        changed = self.home / '.claude/plugins/cache/test/pstack/0.15.43/skills' / DRIFT_FILES[4]
        changed.write_text('# Shipping\nVerify each PR independently.\n')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       stderr=subprocess.DEVNULL, text=True).strip()

    def put(self, name, text):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')

    def run_facts(self):
        result = subprocess.run(['bash', str(FACTS), str(self.repo)],
                                env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_missing_skill_still_prints_ci_and_jobs(self):
        out = self.run_facts()
        self.assertIn('NO VERIFY SKILL', out)
        self.assertIn('cancel-in-progress: true', out)
        self.assertIn('PR #3 sha3: 3 jobs', out)
        self.assertIn('PR #2 sha2: 3 jobs', out)
        self.assertIn('PR #1 sha1: 3 jobs', out)
        self.assertIn('## CI playbook evidence', out)

    def test_drift_shows_diff_for_recorded_version(self):
        self.put('.claude/skills/verify-app/SKILL.md', '# Verify\npstack: 0.15.42\n')
        self.commit()
        out = self.run_facts()
        self.assertIn('PSTACK CHANGED', out)
        self.assertIn('0.15.42 -> 0.15.43', out)
        self.assertIn('+Verify each PR independently.', out)
        self.assertIn('unchanged: create-verification-skill/SKILL.md', out)

    def test_no_pin_is_a_gap_not_alignment(self):
        self.put('.agents/skills/verify-app/SKILL.md', '# Verify\n')
        self.commit()
        self.assertIn('pstack: MISSING', self.run_facts())

    def test_api_failure_is_unknown_not_zero_jobs(self):
        self.env['FAIL_JOBS'] = '1'
        out = self.run_facts()
        self.assertIn('PR #3 sha3: UNKNOWN', out)
        self.assertNotIn('PR #3 sha3: 0 jobs', out)

    def test_audit_does_not_fetch_or_change_repo(self):
        before = self.git('show-ref')
        self.run_facts()
        self.assertFalse((self.repo / '.git/FETCH_HEAD').exists())
        self.assertEqual(before, self.git('show-ref'))
        self.assertEqual('', self.git('status', '--porcelain'))

    def test_highest_version_across_plugin_caches(self):
        p = self.home / '.claude/plugins/cache/zzz/pstack/0.9.0/skills'
        p.mkdir(parents=True)
        out = self.run_facts()
        self.assertIn('installed pstack: 0.15.43', out)

    def test_unfinished_runs_do_not_prove_job_budget(self):
        self.env['RUN_STATUS'] = 'in_progress'
        out = self.run_facts()
        self.assertIn('PR #3 sha3: UNKNOWN (3 known jobs', out)
        self.assertIn('in_progress', out)

    def test_conflicting_pins_are_a_gap(self):
        self.put('.claude/skills/verify-app/SKILL.md',
                 '# Verify\npstack: 0.15.42\npstack: 0.15.43\n')
        self.commit()
        self.assertIn('conflicting pstack versions', self.run_facts())

    def test_current_pin_does_not_claim_drift(self):
        self.put('.claude/skills/verify-app/SKILL.md', '# Verify\npstack: 0.15.43\n')
        self.commit()
        out = self.run_facts()
        self.assertIn('recorded version matches installed', out)
        self.assertNotIn('PSTACK CHANGED', out)

    def test_recorded_version_unavailable_is_explicit(self):
        self.put('.claude/skills/verify-app/SKILL.md', '# Verify\npstack: 0.14.0\n')
        self.commit()
        out = self.run_facts()
        self.assertIn('PSTACK CHANGED', out)
        self.assertIn('recorded version not installed', out)


if __name__ == '__main__':
    unittest.main()
