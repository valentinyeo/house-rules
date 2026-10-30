---
name: board-identity
description: First step of every lead role (support-manager, design-lead, marketing-lead, finance-lead). Gives the session its own Hypertask board login "HT <Role> Lead" with the right boards, without asking Valentin. Use at session start, when told "you are HT <Role> Lead", or when ship-identity prints "Valentins Claude Code".
---

# Board identity

Get your own board login. Do it yourself. Never ask Valentin: this rule already allows finding, renaming, creating and boarding your own role agent. Never print a token.

## Board map

| Role skill | Name | Slug | Boards |
|---|---|---|---|
| support-manager | HT Support Lead | ht-support-lead | 10450, 15 |
| design-lead | HT Design Lead | ht-design-lead | 15 |
| marketing-lead | HT Growth Lead | ht-growth-lead | 2108, 15 |
| finance-lead | HT Finance Lead | ht-finance-lead | 2462 |

Set these for your row, in every shell call below (`h` is `ht` with a retry on "Rate limit"):

```bash
NAME="HT Finance Lead"; SLUG=ht-finance-lead; BOARDS="2462"; export NAME BOARDS
C=~/.config/hypertask-agents/credentials; S=$C/sessions; export PATH=$HOME/.local/bin:$PATH
h(){ for i in 1 2 3 4 5 6; do r=$(ht "$@"); case $r in *"Rate limit"*) timeout 20 tail -f /dev/null;; *) printf '%s\n' "$r"; return;; esac; done; echo "rate limited"; }
```

## 1. Token already there?

`[ -s $S/$SLUG-agent-token ] && echo have`. If yes, read its agent id (step 3 decode) and go to 5.

## 2. Find your agent

Admin calls use `ht` (Valentin's saved CLI login; it can manage agents). Setup only. Board writes never use it.

```bash
h GET "/mcp/admin/agents?limit=200" | python3 -c "import json,sys,os
w=os.environ['NAME'].lower().replace(' lead',''); B={int(x) for x in os.environ['BOARDS'].split()}
for a in json.load(sys.stdin)['agents']:
  if a['revoked'] or a['display_name'].lower().replace(' lead','')!=w: continue
  b={x['id'] for x in a['boards']}; print(a['id'],a['display_name'],sorted(b),'MINE' if b&B or not b else 'OTHER BOARDS')"
```

"HT Finance" matches "HT Finance Lead". Use only a `MINE` row (it already has one of your boards, or no boards). An `OTHER BOARDS` row belongs to another team or session: leave it alone, do not rename it, do not reuse its token. No `MINE` row: go to 4 and create.

## 3. Reuse a token file you already have

Look for a token file for your agent id. This prints file names only:

```bash
ID=<agent id>; for f in $C/*-agent-token $S/*-agent-token $S/*/*-agent-token; do python3 - "$f" "$ID" <<'P'
import sys,json,base64
t=open(sys.argv[1]).read().strip(); p=t.split('.')[1]; p+='='*(-len(p)%4)
if json.loads(base64.urlsafe_b64decode(p)).get('agentId')==sys.argv[2]: print(sys.argv[1])
P
done 2>/dev/null
```

Found one: `mkdir -p $S/<role> && ln -sfn <that file> $S/<role>/$SLUG-agent-token`, then go to 5. Do not rotate. Rotating kills the token in that other file.

## 4. Mint (no token file anywhere)

Never let the token reach the screen. Both commands write it straight into a chmod 600 file and print only the agent id.

```bash
umask 077; mkdir -p $S/<role>; F=$S/<role>/$SLUG-agent-token
save(){ python3 -c "import json,sys
d=json.load(sys.stdin); a=d.get('agent') or {}
t=d.get('token') or d.get('bearer_token') or a.get('token') or a.get('bearer_token')
if not t: print('no token in reply, keys:',list(d)); sys.exit(1)
open('$F','w').write(t); print('saved',a.get('id') or d.get('id',''))"; chmod 600 $F; }
```

- `MINE` agent, no token file: rotate. `h POST /mcp/admin/agents/$ID/token '{}' | save`
- No `MINE` agent: create it on your boards (repeat `--project` per board):
  `hypertask --json agents create --name "$NAME" --project 2462 | save`

## 5. Flat link, boards, name

- ship-identity reads only the flat file `$S/$SLUG-agent-token`:
  `[ -e $S/$SLUG-agent-token ] || ln -sfn <role>/$SLUG-agent-token $S/$SLUG-agent-token`
- Add any board from the map that it lacks, one PATCH each:
  `h PATCH /mcp/agents/$ID '{"add_project_ids":[2462]}'`
  "Agents can only belong to boards in one team": this agent is not yours. Remove only the links you made in 3 and 5, then go to 4 and create.
- Then rename to `$NAME` if needed: `h PATCH /mcp/agents/$ID "{\"display_name\":\"$NAME\"}"`

## 6. Verify (read and write)

```bash
T=$(cat $S/$SLUG-agent-token)
hypertask --json --token "$T" context | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['connected_agent']['displayName'],[p['id'] for p in d['projects']])"
```

Pass means the name is `$NAME` and every board from the map is listed.

Write check, per board: make a draft comment on any ticket there, then delete it. If the board has no tickets, write "write: no ticket to test".

```bash
K=$(hypertask --json --token "$T" tasks list --project <board> --limit 1 | python3 -c "import json,sys;d=json.load(sys.stdin);t=d.get('tasks') or [{}];print(t[0].get('ticketNumber',''))")
hypertask --json --token "$T" draft create $K --comment --text "identity check" | python3 -c "import json,sys;print(json.load(sys.stdin)['draft']['id'])"
hypertask --json --token "$T" draft delete <draft id> --project <board>
```

## 7. Write as yourself

If the session has no `/rename` name, ship-identity falls back to Valentins Claude Code. Fix it by prefixing writes with `SHIP_SESSION_NAME="$NAME"`:
`SHIP_SESSION_NAME="$NAME" ~/.claude/skills/ship/scripts/ship-identity` must print `$NAME` (it is not on PATH).

## 8. One startup check

Run this in the lead's own named session:

```bash
python3 ~/.agents/skills/board-identity/check.py
```

Set `SHIP_SESSION_NAME` to your role above. Never another role.
The check reads only that role's flat token.
It verifies the real agent name and boards.
No tokens appear in arguments or output.

It checks these checkouts without changing them:

| Lead | Repos under `~/projects/` | Runner path |
|---|---|---|
| Support | `ai-chatbot`, `HypertaskDocs`, `hypertask` | No runners; ships itself, HEFE 10450; core product via HTPR 15; [contract](../support-manager/runners.md) |
| Design | `hypertask` | Hypertask fleet, HTPR 15; [contract](../design-lead/runners.md) |
| Growth | `hypertask-astro` | No runners; ships itself, MARK 2108; core product via HTPR 15; [contract](../marketing-lead/SKILL.md) |
| Finance | `pecunia` | No finance runners; code through HT Product Lead |

Clean means no tracked or untracked changes.
Fast-forwardable means local HEAD precedes the remote tip.
The check reads the live upstream, never pulls.
Unknown remote commits require fetching before retrying.
Ahead, diverged, missing and unavailable checkouts fail.
Preserve existing work; never reset or stash.

`setup: PASS` means all four checks passed.
Any failure exits nonzero; readiness stays blocked.
Fix setup through the existing steps, then rerun.
Never start role work on failed setup.

## Report

Print one line, for example: `identity: HT Finance Lead, boards 2462, read ok, write ok`. Nothing else, and never the token.

## Stop rules

- Never revoke, archive or delete an agent.
- Never rename or re-board an `OTHER BOARDS` agent.
- Never copy tokens from Grok Bot or another machine.
- Never print a token, the key or `ht` output that holds one.
- A failed step blocks readiness and board work. Report its safe error through HT Product Lead. Fix it, then rerun the startup check.
