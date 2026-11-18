#!/usr/bin/env python3
"""Read formal coverage and history from the same Git snapshot as facts.sh."""

import json
import posixpath
import re
import subprocess
import sys


FORMAL = re.compile(
    r'formal verification|model.check(?:er|ing)|\bZ3\b|z3-solver|\bSMT\b|'
    r'\bTLC\b|TLA\+|\bApalache\b|\bCBMC\b|\bDafny\b|\bKani\b|'
    r'\bLean\s+(?:prover|proof)|\bCoq\b', re.I)
MODEL = re.compile(r'\.(?:tla|smt2|dfy|lean|v|prism)$', re.I)
SYNC_KEYS = ('sync_commit', 'last_sync_commit', 'verified_commit')
PATH_KEYS = ('file', 'source', 'path', 'files', 'sources', 'covered_files', 'covered_code')


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, *args], text=True, errors='replace',
                          capture_output=True, check=False)


def references(text, owner, files):
    tokens = re.findall(r'`([^`\n]+)`|\]\(([^)\n]+)\)', text)
    candidates = [x for pair in tokens for x in pair if x]
    candidates += re.findall(r'[\w./-]+\.[\w]+', text)
    found = set()
    for token in candidates:
        token = token.split('#', 1)[0]
        for path in (token, posixpath.normpath(posixpath.join(posixpath.dirname(owner), token))):
            if path in files:
                found.add(path)
    return found


def code_paths(value, key=''):
    if isinstance(value, dict):
        return {path for k, v in value.items() for path in code_paths(v, k)}
    if isinstance(value, list):
        return {path for v in value for path in code_paths(v, key)}
    if isinstance(value, str) and key in PATH_KEYS:
        path = posixpath.normpath(value.replace('\\', '/'))
        if path != '..' and not path.startswith(('../', '/')):
            return {path}
    return set()


def main(repo, base):
    tree = git(repo, 'ls-tree', '-r', '--name-only', base)
    if tree.returncode:
        print('formal setup: UNKNOWN (snapshot unavailable)')
        return 1
    files = set(tree.stdout.splitlines())
    all_skills = sorted(f for f in files if re.fullmatch(
        r'\.(?:claude|cursor|agents)/skills/[^/]+/SKILL\.md', f))
    artifacts = {f for f in files if MODEL.search(f)}
    skills = []
    for skill in all_skills:
        text = git(repo, 'show', f'{base}:{skill}').stdout
        refs = references(text, skill, files)
        if FORMAL.search(text) or any(MODEL.search(f) for f in refs):
            skills.append((skill, text, refs))
    print('formal skills: ' + (str(len(skills)) if skills else 'none detected'))
    print('formal model artifacts: ' + (', '.join(sorted(artifacts)) or 'none detected'))
    print('Detection is a source hint, not proof that the checks run or cover every risky feature.')
    for skill, text, refs in skills:
        print(f'### {skill}')
        print('referenced setup files: ' + (', '.join(sorted(refs)) or 'UNKNOWN'))
        records = []
        for ref in sorted(refs):
            if not ref.endswith('.json'):
                continue
            try:
                value = json.loads(git(repo, 'show', f'{base}:{ref}').stdout)
            except (ValueError, TypeError):
                print(f'coverage candidate unreadable: {ref}; inspect it directly')
                continue
            if not isinstance(value, dict):
                continue
            pin = next((value[k] for k in SYNC_KEYS if k in value), None)
            covered = code_paths(value)
            if pin is not None or covered:
                records.append((ref, pin, covered))
        if not records:
            pins = {sha for line in text.splitlines()
                    if re.search(r'(sync|verified|checked).{0,40}commit|commit.{0,40}sync', line, re.I)
                    for sha in re.findall(r'\b[0-9a-f]{7,40}\b', line)}
            covered = {f for f in refs if f != skill and not MODEL.search(f)
                       and not f.endswith(('.md', '.json'))}
            records.append((skill, next(iter(pins)) if len(pins) == 1 else None, covered))
        for record, pin, covered in records:
            print(f'coverage record: {record}')
            print('sync commit: ' + (str(pin) if pin else 'UNKNOWN (missing or conflicting)'))
            print('covered paths: ' + (', '.join(sorted(covered)) or 'UNKNOWN'))
            for path in sorted(covered - files):
                print(f'covered path missing at snapshot: {path}')
            if not isinstance(pin, str) or not re.fullmatch(r'[0-9a-f]{7,40}', pin):
                print('sync history: UNKNOWN (no usable recorded commit)')
                continue
            resolved = git(repo, 'rev-parse', '--verify', f'{pin}^{{commit}}')
            if resolved.returncode or git(repo, 'merge-base', '--is-ancestor', pin, base).returncode:
                print('sync history: UNKNOWN (commit unavailable or not an ancestor; no fetch)')
                continue
            if not covered:
                print('sync history: UNKNOWN (covered paths not recorded)')
                continue
            commits = git(repo, 'rev-list', '--count', f'{pin}..{base}', '--', *sorted(covered))
            if commits.returncode:
                print('sync history: UNKNOWN (cannot read covered history)')
                continue
            print(f'covered code changed since sync: {commits.stdout.strip()} commits')
            changes = git(repo, 'log', '-5', '--format=%H %cs %s', '--name-status',
                          f'{pin}..{base}', '--', *sorted(covered))
            print('recent covered-code commits (up to 5):')
            print(changes.stdout.strip() or 'none')
        print('recent formal setup commits (up to 5):')
        history = git(repo, 'log', '-5', '--format=%H %cs %s', '--name-status',
                      base, '--', *sorted(refs | {skill}))
        print(history.stdout.strip() or 'UNKNOWN (history unavailable)')
    if artifacts and not skills:
        print('Model artifacts exist without a detected formal skill; coverage and sync are UNKNOWN.')
        history = git(repo, 'log', '-5', '--format=%H %cs %s', '--name-status',
                      base, '--', *sorted(artifacts))
        print('recent model artifact commits (up to 5):')
        print(history.stdout.strip() or 'UNKNOWN (history unavailable)')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
