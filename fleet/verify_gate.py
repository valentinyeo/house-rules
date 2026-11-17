"""Binary verification checks. No repository code executes here."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

CHECKS = {
    'real-app': 'Agent drives the real app',
    'agent-verifier': 'Human is not the verifier',
    'feature-map': 'Feature map',
    'repro-first': 'Reproduce bug first',
    'test-first': 'Failing test first',
    'adversary': 'Agents try to break it',
    'skill-tests': 'Tests for the verify skill',
    'hard-rules': 'Hard rules in checks',
    'current-head': 'Auto-merge only once earned',
    'real-size': 'Real-size data',
    'github-run': 'Verifier runs on GitHub',
    'release-proof': 'Video or trace before release',
    'seen-failing': 'Check seen failing',
}
KINDS = ('screen', 'route', 'button', 'menu', 'shortcut', 'command', 'setting', 'endpoint', 'job')
REGISTRATIONS = {kind: kind for kind in KINDS}
REGISTRATIONS.update({f'register_{kind}': kind for kind in KINDS})
REGISTRATIONS.update({'add_parser': 'command', 'add_command': 'command', 'add_url_rule': 'route',
                      'add_api_route': 'endpoint', 'get': 'endpoint', 'post': 'endpoint',
                      'put': 'endpoint', 'patch': 'endpoint', 'delete': 'endpoint'})


class Missing(ValueError):
    pass


def require(condition, artifact):
    if not condition:
        raise Missing(artifact)


def contained(root, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute(),
            'relative artifact path')
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f'artifact inside {root}: {name}')
    return path


def document(path):
    return json.loads(path.read_text())


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    require(result.returncode == 0, 'git history: ' + ' '.join(args))
    return result.stdout.strip()


def ancestor(repo, before, after):
    require(re.fullmatch(r'[0-9a-f]{40}', before or '') and
            re.fullmatch(r'[0-9a-f]{40}', after or ''), 'full commit SHA')
    require(before != after, 'distinct earlier commit')
    git(repo, 'merge-base', '--is-ancestor', before, after)


def source_entries(repo, config, policy):
    require(config.get('adapter') == 'python-registration-v1', 'supported source adapter python-registration-v1')
    roots = config.get('source_roots', [])
    require(roots, '.verify/config.json source_roots')
    entries = set()
    supported = {'.py', '.js', '.jsx', '.ts', '.tsx', '.sh', '.go', '.rs', '.java', '.kt',
                 '.swift', '.vue', '.svelte', '.html', '.json', '.yaml', '.yml'}
    exclusions = policy.get('source_exclusions', {})
    resolved_roots = [contained(repo, name) for name in roots]
    for name in git(repo, 'ls-files').splitlines():
        path = contained(repo, name)
        if path.suffix not in supported and not (path.is_file() and path.stat().st_mode & 0o111):
            continue
        if name in exclusions and isinstance(exclusions[name], str) and exclusions[name].strip():
            continue
        require(any(path == root or path.is_relative_to(root) for root in resolved_roots),
                f'tracked source entry scan coverage: {name}')
    for root_name in roots:
        root = contained(repo, root_name)
        require(root.exists(), f'source root {root_name}')
        paths = sorted(root.rglob('*')) if root.is_dir() else [root]
        for path in paths:
            if not path.is_file() or path.suffix == '.pyc':
                continue
            require(path.suffix == '.py', f'source adapter for {path.relative_to(repo)}')
            tree = ast.parse(path.read_text(), filename=str(path))
            decorators = {id(decorator) for owner in ast.walk(tree) if isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for decorator in owner.decorator_list}
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else '')
                if name in {'get', 'post', 'put', 'patch', 'delete'}:
                    if id(node) in decorators:
                        require(isinstance(node.func, ast.Attribute), f'HTTP decorator receiver at {path.relative_to(repo)}:{node.lineno}')
                    elif not isinstance(node.func, ast.Attribute) or not isinstance(node.func.value, ast.Name) or node.func.value.id not in {'app', 'router', 'api'}:
                        continue
                kind = REGISTRATIONS.get(name)
                if not kind:
                    continue
                value = node.args[0] if node.args else None
                require(isinstance(value, ast.Constant) and isinstance(value.value, str),
                        f'literal {kind} registration at {path.relative_to(repo)}:{node.lineno}')
                entries.add((kind, value.value, str(path.relative_to(repo))))
    require(entries, 'discoverable code entry points, extend the source adapter')
    return entries


class Gate:
    def __init__(self, repo, context, evidence):
        self.repo = repo.resolve()
        self.context = context
        self.evidence = evidence.resolve()
        self.config = document(repo / '.verify/config.json') if (repo / '.verify/config.json').is_file() else {}
        require(isinstance(context, dict) and isinstance(self.config, dict), 'JSON object configuration/context')
        self.policy = context.get('policy', {})
        require(isinstance(self.policy, dict), 'JSON object policy')
        self.verdict = context.get('verdict', {})
        require(isinstance(self.verdict, dict), 'JSON object verdict')
        self.head = context.get('head_sha')
        self.manifest = document(evidence / 'verification.json') if (evidence / 'verification.json').is_file() else {}

        require(isinstance(self.manifest, dict), 'JSON object verification manifest')

    def artifact(self, key, suffixes=None):
        name = self.manifest.get(key)
        require(name, f'{key}: manifest artifact path')
        path = contained(self.evidence, name)
        require(path.is_file() and path.stat().st_size > 0, f'{key}: {name}')
        if suffixes:
            require(path.suffix in suffixes, f'{key} format: {sorted(suffixes)}')
        require(self.manifest.get('head_sha') == self.head, f'{key} manifest for current head SHA')
        expected = self.manifest.get('sha256', {}).get(name)
        require(expected == hashlib.sha256(path.read_bytes()).hexdigest(), f'{key} SHA256 digest')
        return path

    def run(self, item):
        try:
            require(not self.context.get('collection_error'), f"GitHub evidence collection: {self.context.get('collection_error')}")
            getattr(self, 'check_' + item.replace('-', '_'))()
            return {'id': item, 'name': CHECKS[item], 'pass': True, 'missing': None}
        except (Missing, OSError, ValueError, KeyError, TypeError, AttributeError, SyntaxError, yaml.YAMLError) as error:
            return {'id': item, 'name': CHECKS[item], 'pass': False, 'missing': str(error)}

    def check_real_app(self):
        require(self.config.get('skill'), '.verify/config.json skill path')
        skill = contained(self.repo, self.config.get('skill'))
        body = skill.read_text()
        frontmatter = re.match(r'---\s*\n(.*?)\n---', body, re.S)
        require(frontmatter, f'{skill.relative_to(self.repo)} YAML frontmatter')
        metadata = yaml.safe_load(frontmatter[1])
        require(isinstance(metadata, dict) and isinstance(metadata.get('name'), str)
                and metadata['name'].startswith('verify-') and metadata.get('description'),
                f'{skill.relative_to(self.repo)} name/description frontmatter')
        for section in ('Launch', 'Doctor', 'Drive', 'Evidence', 'Cleanup', 'Helpers'):
            require(f'**{section}:**' in body, f'verify skill {section} section')
        self.artifact('drive', {'.txt', '.log', '.json', '.zip'})
        require(self.manifest.get('driver') == 'agent', 'agent real-app driver identity')
        require(self.manifest.get('surface') and self.manifest.get('command'),
                'real-app surface and drive command')

    def check_agent_verifier(self):
        login = self.verdict.get('login')
        require(login and login in self.policy.get('verifiers', {}), 'allowlisted agent verdict comment')
        require(login != self.context.get('author_login'), 'verifier separate from PR author')
        require(self.verdict.get('comment_id') and self.verdict.get('comment_url') ==
                f"https://github.com/{self.context['repository']}/pull/{self.context['pr_number']}#issuecomment-{self.verdict['comment_id']}",
                'posted verdict comment on this PR')

    def check_feature_map(self):
        code = source_entries(self.repo, self.config, self.policy)
        require(self.config.get('features'), '.verify/config.json features path')
        feature_dir = contained(self.repo, self.config.get('features'))
        readme = feature_dir / 'README.md'
        require(readme.is_file(), 'features/README.md')
        mapped = set()
        for path in sorted(feature_dir.glob('*.md')):
            if path.name == 'README.md':
                continue
            body = path.read_text()
            headings = re.findall(r'^## (.+)$', body, re.M)
            require(len(headings) == 4 and headings[:2] == ['Sub-features', 'How to get to it (user POV)']
                    and headings[2].startswith('Driving it with ') and headings[3] == 'Gotchas',
                    f'{path.name}: four book feature sections')
            require(f'({path.name})' in readme.read_text(), f'feature index link: {path.name}')
            for kind, value, source in re.findall(r'<!-- entry: (\w+)\|([^|]+)\|([^>]+) -->', body):
                mapped.add((kind, value, source.strip()))
        missing = sorted(code - mapped)
        extra = sorted(mapped - code)
        require(not missing and not extra, f'code/map entry mismatch; missing={missing}; dead={extra}')

    def history(self, kind):
        history = self.manifest.get('history', {})
        fix = history.get('fix_sha')
        before = history.get(kind + '_sha')
        ancestor(self.repo, before, fix)
        require(fix == self.head or git(self.repo, 'merge-base', fix, self.head) == fix,
                'fix commit in PR head history')
        fix_files = git(self.repo, 'diff-tree', '--no-commit-id', '--name-only', '-r', fix).splitlines()
        roots = [contained(self.repo, root) for root in self.config.get('source_roots', [])]
        require(any(any(contained(self.repo, name) == root or contained(self.repo, name).is_relative_to(root) for root in roots) for name in fix_files),
                'application source changed in named fix commit')
        base = self.context.get('base_sha')
        require(base != before and git(self.repo, 'merge-base', base, before) == base,
                f'{kind} commit introduced after PR base')
        name = history.get(kind + '_path')
        contained(self.repo, name)
        content = git(self.repo, 'show', f'{before}:{name}')
        require(content, f'{kind} artifact committed before fix')
        changed = git(self.repo, 'diff-tree', '--no-commit-id', '--name-only', '-r', before).splitlines()
        require(name in changed, f'{kind} artifact introduced in {kind} commit')
        return history, before, content

    def check_repro_first(self):
        require('labels' in self.context, 'GitHub PR labels for bug-history decision')
        if 'bug' not in self.context.get('labels', []):
            return
        _, _, content = self.history('repro')
        repro = json.loads(content)
        require(repro.get('command') and repro.get('output') and repro.get('exit_code', 0) != 0,
                'committed failing repro command, output and exit code')

    def check_test_first(self):
        require('labels' in self.context, 'GitHub PR labels for bug-history decision')
        if 'bug' not in self.context.get('labels', []):
            return
        _, sha, _ = self.history('test')
        run = self.context.get('test_run', {})
        self.validate_run(run, sha, 'failure')
        require(run.get('test_path') == self.manifest['history'].get('test_path'),
                'failed run identifies the committed regression test')
        require(run.get('output') and run.get('command'), 'failing test command and output')

    def check_adversary(self):
        self.check_agent_verifier()
        verifier = self.policy['verifiers'][self.verdict['login']]
        author_family = self.policy.get('authors', {}).get(self.context.get('author_login'))
        require(author_family, 'trusted author model family policy')
        require(verifier.get('family') and verifier['family'] != author_family,
                'verdict from a different model family')
        require(self.verdict.get('status') in ('PASS', 'PASS+NOTES', 'FAIL'), 'PASS, PASS+NOTES or FAIL verdict')
        require(self.verdict.get('status') != 'FAIL', 'passing adversarial verdict; latest verdict is FAIL')
        self.artifact('adversarial_report', {'.txt', '.md', '.json'})

    def check_skill_tests(self):
        tests = self.manifest.get('skill_tests', {})
        require(tests.get('command') and tests.get('passed', 0) > 0 and tests.get('failed', 0) == 0,
                'executed verify skill pass/fail fixture tests')
        self.artifact('skill_test_output', {'.txt', '.log'})
        require(tests.get('fixtures') == {'pass': True, 'fail': True}, 'both verify skill fixture outcomes')

    def check_hard_rules(self):
        path = self.repo / '.github/workflows/verify.yml'
        workflow = yaml.safe_load(path.read_text())
        jobs = workflow.get('jobs', {})
        required = self.policy.get('gate_workflow')
        require(isinstance(required, str) and re.fullmatch(r'valentinyeo/house-rules/\.github/workflows/verify-gate\.yml@[0-9a-f]{40}', required), 'immutable gate workflow SHA pin')
        require(required and any(job.get('uses') == required and
                job.get('with', {}).get('pr-number') == '${{ github.event.pull_request.number }}' for job in jobs.values()),
                'pinned reusable verify-gate workflow for this PR')
        require(not any(job.get('continue-on-error') or job.get('if') for job in jobs.values()
                        if job.get('uses') == required), 'unconditional blocking verify-gate job')
        events = workflow.get('on', workflow.get(True, {}))
        require('pull_request' in events, 'verify workflow pull_request trigger')
        trigger = events['pull_request']
        require(not trigger or not trigger.get('types') or
                {'opened', 'synchronize', 'reopened'}.issubset(trigger['types']),
                'verify trigger for opened, synchronize and reopened')
        require(not trigger or not any(key in trigger for key in ('paths', 'paths-ignore', 'branches', 'branches-ignore')),
                'unfiltered pull_request verification trigger')
        rules = (self.repo / 'AGENTS.md').read_text()
        for item in CHECKS:
            require(f'| {item} | verify-gate / {item} |' in rules,
                    f'AGENTS.md enforcement row: {item}')

    def check_current_head(self):
        require(git(self.repo, 'rev-parse', 'HEAD') == self.head, 'checkout matching current PR head SHA')
        require(self.verdict.get('head_sha') == self.head and re.fullmatch(r'[0-9a-f]{40}', self.head or ''),
                'verdict covering current PR head SHA before auto-merge')
        require(self.verdict.get('status') in ('PASS', 'PASS+NOTES'), 'passing verdict before auto-merge')

    def check_real_size(self):
        dataset = self.verdict.get('dataset', {})
        require(isinstance(dataset.get('count'), int) and not isinstance(dataset.get('count'), bool)
                and dataset['count'] > 0 and dataset.get('unit') and dataset.get('production_comparison'),
                'verdict dataset count, unit and production-size comparison')

    def validate_run(self, run, sha, conclusion='success'):
        repo = self.context.get('repository')
        require(isinstance(run.get('id'), int) and run.get('html_url') ==
                f"https://github.com/{repo}/actions/runs/{run['id']}", 'GitHub Actions run URL')
        require(run.get('head_sha') == sha and run.get('conclusion') == conclusion,
                f'{conclusion} GitHub run for evidence SHA')
        require(run.get('id') != self.context.get('gate_run_id'), 'independent verifier run, not this gate run')
        jobs = run.get('jobs', [])
        require(jobs and all(job.get('runner_name', '').startswith('GitHub Actions') and
                'self-hosted' not in job.get('labels', []) for job in jobs), 'GitHub-hosted verifier jobs')

    def check_github_run(self):
        self.validate_run(self.context.get('run', {}), self.head)
        require(self.verdict.get('run_url') == self.context['run']['html_url'], 'verdict links its GitHub Actions run')
        verifier = self.policy.get('verifiers', {}).get(self.verdict.get('login'), {})
        require(self.context['run'].get('path') == verifier.get('workflow') and verifier.get('workflow'),
                'allowlisted verifier workflow path')

    def check_release_proof(self):
        self.artifact('release_proof', {'.mp4', '.webm', '.zip', '.trace'})
        release_files = self.policy.get('release_workflows', [])
        require(release_files, 'trusted release workflow list')
        for name in release_files:
            workflow = yaml.safe_load(contained(self.repo, name).read_text())
            jobs = workflow.get('jobs', {})
            guards = {key for key, job in jobs.items() if job.get('uses') == self.policy.get('gate_workflow')
                      and job.get('with', {}).get('mode') == 'release'
                      and job.get('with', {}).get('release-sha') == '${{ github.sha }}'
                      and not job.get('if') and not job.get('continue-on-error')}
            require(guards, f'{name}: blocking release verification job')
            for key, job in jobs.items():
                if key in guards:
                    continue
                needs = job.get('needs', [])
                needs = [needs] if isinstance(needs, str) else needs
                require(guards.intersection(needs) and not job.get('if') and not job.get('continue-on-error'),
                        f'{name}: {key} depends on successful release verification')
        if self.context.get('mode') == 'release':
            require(self.context.get('release_sha') == self.head, 'release SHA covered by current verdict')

    def check_seen_failing(self):
        output = self.artifact('seen_failing_output', {'.txt', '.log'}).read_text()
        for item in CHECKS:
            require(f'BROKEN {item}: FAIL' in output and f'VALID {item}: PASS' in output,
                    f'broken-first and passing fixture execution: {item}')
            require(output.index(f'BROKEN {item}: FAIL') < output.index(f'VALID {item}: PASS'),
                    f'broken variant before passing fixture: {item}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', nargs='?', type=Path, default=Path.cwd())
    parser.add_argument('--context', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--check', choices=CHECKS)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    selected = [args.check] if args.check else CHECKS
    try:
        context = document(args.context) if args.context else {}
        evidence = args.evidence or args.repo / '.verify/evidence'
        gate = Gate(args.repo, context, evidence)
        results = [gate.run(item) for item in selected]
    except (OSError, ValueError, TypeError, AttributeError) as error:
        results = [{'id': item, 'name': CHECKS[item], 'pass': False,
                    'missing': f'valid gate configuration/context: {error}'} for item in selected]
    if args.json:
        print(json.dumps({'items': results}, indent=2))
    else:
        for result in results:
            print(f"{'PASS' if result['pass'] else 'FAIL'} {result['name']}" +
                  (f" | missing artifact: {result['missing']}" if not result['pass'] else ''))
    return int(any(not result['pass'] for result in results))
