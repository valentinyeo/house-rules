"""Software Factory column contract during the board 2060 rename."""
import re

INFLIGHT = ('Building', 'Doing', 'Checks', 'Verifier', 'AI Review')
ALIASES = {'Building': ('Building', 'Doing'), 'Verifier': ('Verifier', 'AI Review')}


def resolve(name, sections):
    available = {s.get('name') or s.get('section_title') for s in sections}
    for candidate in ALIASES.get(name, (name,)):
        if candidate in available:
            return candidate
    raise ValueError(f'No column for {name}: {sorted(available)}')


def passed(pr, comments):
    head = pr.get('headRefOid')
    if not re.fullmatch(r'[0-9a-f]{40}', head or ''):
        return False
    verdicts = []
    for comment in comments:
        if (comment.get('user') or {}).get('login') != 'github-actions[bot]':
            continue
        match = re.search(r'^pstack-verifier: (PASS(?:\+NOTES)?|FAIL) @ ' + head + r'\s*$',
                          comment.get('body') or '', re.M)
        if match:
            verdicts.append(match.group(1))
    return bool(verdicts) and verdicts[-1] in ('PASS', 'PASS+NOTES')


def stage(pr, comments):
    if pr.get('state') == 'MERGED':
        return 'Verifier'
    if pr.get('state') != 'OPEN' or pr.get('isDraft'):
        return None
    latest = {}
    for index, check in enumerate(pr.get('statusCheckRollup') or []):
        name = check.get('name') or check.get('context') or ''
        if 'verifier' in name.lower():
            continue
        key = (check.get('workflowName') or '', name)
        order = (check.get('startedAt') or '', index)
        if key not in latest or order >= latest[key][0]:
            latest[key] = (order, check)
    checks = [check for _, check in latest.values()]
    green = bool(checks) and all(
        c.get('state') == 'SUCCESS' if 'context' in c else
        c.get('status') == 'COMPLETED' and c.get('conclusion') in ('SUCCESS', 'NEUTRAL', 'SKIPPED')
        for c in checks)
    return 'Verifier' if green else 'Checks'
