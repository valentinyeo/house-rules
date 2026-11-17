import json
import os
import subprocess
import uuid
from pathlib import Path

MODEL = 'deepseek-v4.1-flash'
OUT = Path('evidence')
OUT.mkdir(exist_ok=True)
SESSION = str(uuid.uuid4())
prompt = '''Read the worker instructions below before anything else.
You are the independent DeepSeek Flash verifier for SOFT-2579, authored by Codex.
Goal: the shared drain rule follows pstack 0.15.43 Autonomous run. Checkable goal,
watcher wakes on worker finished / CI result / verdict posted, slow timer backup,
one checkpoint per round, no plateau stop. solo-wake must accept real event turns.
Do not edit either candidate, commit, push or merge. You are running on GitHub-hosted
Ubuntu, not the author's server. Use run_command to inspect and drive the actual
scripts. Judge each repository separately: PASS, PASS+NOTES, FAIL. No extra gates.

Worker instructions: open PRs ready, never merge. Hold only for a bug users hit or
failing run at current head. Baseline bugs get one note. Do not ask humans questions.

Checkouts:
  house-rules/ = PR 594, 4a667d4 (base 314afbe)
  vstack/ = PR 107, 5183546 (base 1c8bbb4)
Author observed native Claude transcript records with type=user and
turnOrigin=task_notification on this real server. The previous parser accepted only
the exact serialized string "turnOrigin":"scheduled". Author's six focused tests
failed three cases before the fix, then passed. The vstack contract failed first.
Author ran both original and candidate solo-wake --dry-run against real server state.
Your host has no live Hypertask login or session roster. Do not contact those systems.
Reproduce baseline failures yourself by using a temporary base worktree with candidate
test files copied into it, then test candidates. Test-first commits precede fixes.

pstack Autonomous run 0.15.43:
1. State a checkable exit predicate before iteration.
2. Watch events through watcher subagents, long timer fallback. No events: fixed heartbeat.
3. Smallest justified change, verify predicate, keep progress, discard failures.
4. Own reversible discoveries; return to predicate after side fixes.
5. One decision trail checkpoint per iteration.
6. Stop on predicate. Plateau is not a stop. Pivot. Surface genuine dead ends.

Use at least three independent adversarial attempts. Inspect code for missed behavior
and test loopholes. Drive last_loop_fire/loop_watch using your own inputs as needed.
Run changed real script --self-test, regression tests, vstack contract and installer.
Before verdict, inspect added comments/docstrings per pstack no-comments. Remove
nothing; report only actionable issues. Audit author evidence claims above, naming
unsupported ones. You cannot independently prove server-only observations.
No feature map or verification skill tests needed for these non-app changes.

Return final JSON object, with keys house_rules and vstack. Each value has verdict,
head_sha, evidence, notes, break_attempts. Include an attention array for audit flags.
Write prose for Valentin: answer first, eight words maximum per sentence. Commands,
outputs and facts are preserved verbatim. No general praise or filler.
'''
messages = [{'role': 'system', 'content': 'You are an independent skeptical verification agent. Use tools to establish evidence. Never claim unrun tests.'},
            {'role': 'user', 'content': prompt}]
tool = {'type': 'function', 'function': {'name': 'run_command', 'description': 'Run read-only inspection or verification on the GitHub runner. Temporary test files/worktrees allowed. Never push, merge or modify candidate checkouts.',
        'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}, 'required': ['command']}}}
for iteration in range(24):
    body = {'model': MODEL, 'messages': messages, 'tools': [tool], 'max_tokens': 6500}
    headers = ['Authorization: Bearer ' + os.environ['OPENCODE_API_KEY'],
               'Content-Type: application/json', 'x-opencode-session: ' + SESSION,
               'x-opencode-client: vstack-verifier']
    config = '\n'.join('header = ' + json.dumps(h) for h in headers)
    config += '\ndata = ' + json.dumps(json.dumps(body)) + '\n'
    response = subprocess.run(['curl', '--silent', '--show-error', '--fail-with-body',
                               '--max-time', '240', '--config', '-',
                               'https://opencode.ai/zen/go/v1/chat/completions'],
                              input=config, capture_output=True, text=True)
    if response.returncode:
        detail = (response.stdout + response.stderr).replace(os.environ['OPENCODE_API_KEY'], '<redacted>')
        print('Provider request failed:', detail[:1000])
        raise SystemExit(1)
    result = json.loads(response.stdout)
    msg = result['choices'][0]['message']
    messages.append(msg)
    calls = msg.get('tool_calls') or []
    if not calls:
        content = msg.get('content') or ''
        (OUT / 'verdict.txt').write_text(content)
        (OUT / 'transcript.json').write_text(json.dumps(messages, indent=2))
        print(content)
        break
    for call in calls:
        command = json.loads(call['function']['arguments'])['command']
        env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('TOKEN', 'SECRET', 'KEY'))}
        try:
            run = subprocess.run(['bash', '-lc', command], capture_output=True, text=True, timeout=180, env=env)
            output = f'$ {command}\nexit={run.returncode}\n{run.stdout}{run.stderr}'
        except subprocess.TimeoutExpired:
            output = f'$ {command}\nTIMEOUT after 180 seconds'
        print(output[:24000], flush=True)
        with (OUT / 'commands.log').open('a') as fh:
            fh.write(output + '\n')
        messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': output[:36000]})
    (OUT / 'transcript.json').write_text(json.dumps(messages, indent=2))
else:
    raise SystemExit('Verifier reached tool-turn limit without verdict')
