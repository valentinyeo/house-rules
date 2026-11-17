import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReconcileVerdictTests(unittest.TestCase):
    def verdict(self, text):
        workflow = (ROOT / '.github/workflows/fleet-reconcile-verifier.yml').read_text()
        script = workflow.split('          script: |\n', 1)[1]
        script = '\n'.join(line[12:] for line in script.splitlines())
        harness = """
const script = JSON.parse(process.argv[1]);
const text = JSON.parse(process.argv[2]);
const events = [{type: 'message_end', message: {role: 'assistant',
  content: [{type: 'text', text}]}}];
const fs = {readFileSync: () => events.map(x => JSON.stringify(x)).join('\\n')};
const comments = [], failures = [];
const context = {serverUrl: 'https://github.com', repo: {owner: 'fixture', repo: 'repo'},
  runId: 1, issue: {number: 1}, payload: {pull_request: {head: {sha: 'fixture-sha'}}}};
const github = {rest: {issues: {createComment: async args => comments.push(args.body)}}};
const core = {setFailed: message => failures.push(message)};
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
new AsyncFunction('require', 'context', 'github', 'core', script)(
  () => fs, context, github, core
).then(() => process.stdout.write(JSON.stringify({comments, failures})))
 .catch(error => {process.stderr.write(error.message); process.exitCode = 1;});
"""
        return subprocess.run(['node', '-e', harness, json.dumps(script), json.dumps(text)],
                              capture_output=True, text=True)

    def test_trace_verdict_prefix_is_accepted(self):
        result = self.verdict('VERDICT: PASS+NOTES\n\nGoal: keep board 2060 columns true.')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['failures'], [])
        self.assertIn('fixture-sha', json.loads(result.stdout)['comments'][0])

    def test_failure_still_fails_and_missing_verdict_is_rejected(self):
        for text in ('FAIL', 'VERDICT: FAIL'):
            with self.subTest(text=text):
                result = self.verdict(text)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(json.loads(result.stdout)['failures'])
        self.assertNotEqual(self.verdict('No verdict here').returncode, 0)

    def test_bare_pass_remains_accepted(self):
        result = self.verdict('PASS\n\nEvidence')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['failures'], [])
