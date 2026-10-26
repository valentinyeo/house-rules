---
name: board-identity
description: First step of every lead role (support-manager, design-lead, marketing-lead, finance-lead). Gives the session its own Hypertask board login "HT <Role> Lead" with the right boards, without asking Valentin. Use at session start, when told "you are HT <Role> Lead", or when ship-identity prints "Valentins Claude Code".
---

# Board identity

Get your own board login. Do it yourself. Never ask Valentin. Never print a token.

## Board map

| Role skill | Name | Slug | Boards |
|---|---|---|---|
| support-manager | HT Support Lead | ht-support-lead | 10450, 15 |
| design-lead | HT Design Lead | ht-design-lead | 15 |
| marketing-lead | HT Growth Lead | ht-growth-lead | 2108, 15 |
| finance-lead | HT Finance Lead | ht-finance-lead | 2462 |

Set these for your row, in every shell call below:

```bash
NAME="HT Finance Lead"; SLUG=ht-finance-lead; BOARDS="2462"
C=~/.config/hypertask-agents/credentials; S=$C/sessions; export PATH=$HOME/.local/bin:$PATH
```

## 1. Token already there?

`[ -s $S/$SLUG-agent-token ] && echo have`. If yes, go to 5.

## 2. Find your agent

Admin calls use `ht` (Valentin's saved CLI login; it can manage agents). Setup only. Board writes never use it.

```bash
ht GET "/mcp/admin/agents?limit=200" | python3 -c "import json,sys,os
w=os.environ['NAME'].lower().replace(' lead','')
for a in json.load(sys.stdin)['agents']:
  if not a['revoked'] and a['display_name'].lower().replace(' lead','')==w: print(a['id'],a['display_name'],[b['id'] for b in a['boards']])"
```

Run it with `NAME` exported. "HT Finance" matches "HT Finance Lead". Several matches: take the oldest one with boards, and say so. No match: go to 4.

## 3. Reuse a token file you already have

Look for a token file for that agent id. This prints file names only:

```bash
ID=<agent id>; for f in $C/*-agent-token $S/*-agent-token; do python3 - "$f" "$ID" <<'P'
import sys,json,base64
t=open(sys.argv[1]).read().strip(); p=t.split('.')[1]; p+='='*(-len(p)%4)
if json.loads(base64.urlsafe_b64decode(p)).get('agentId')==sys.argv[2]: print(sys.argv[1])
P
done 2>/dev/null
```

Found one: `mkdir -p $S/<role> && ln -sfn <that file> $S/<role>/$SLUG-agent-token`, then go to 5. Do not rotate. Rotating kills the token in that other file.

## 4. Mint (no token file anywhere)

Existing agent, no token file: rotate.
`ht POST /mcp/admin/agents/$ID/token '{}'`

No agent at all: create.
`ht POST /mcp/admin/agents "{\"display_name\":\"$NAME\",\"project_ids\":[${BOARDS// /,}]}"`

Never let the token reach the screen. Pipe the response straight into the file:

```bash
umask 077; mkdir -p $S/<role>; ht POST ... | python3 -c "import json,sys;d=json.load(sys.stdin);t=d.get('token') or d.get('agent',{}).get('token');open('$S/<role>/$SLUG-agent-token','w').write(t);print('saved',d.get('agent',{}).get('id',''))"
chmod 600 $S/<role>/$SLUG-agent-token
```

## 5. Flat link, name, boards

- ship-identity reads only the flat file `$S/$SLUG-agent-token`:
  `[ -e $S/$SLUG-agent-token ] || ln -sfn <role>/$SLUG-agent-token $S/$SLUG-agent-token`
- Rename to `$NAME` if the agent has another name:
  `ht PATCH /mcp/agents/$ID "{\"display_name\":\"$NAME\"}"`
- Add any board from the map that it lacks:
  `ht PATCH /mcp/agents/$ID '{"add_project_ids":[2462]}'`

Do one change per PATCH.

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
`SHIP_SESSION_NAME="$NAME" ship-identity` must print `$NAME`.

## Report

Print one line, for example: `identity: HT Finance Lead, boards 2462, read ok, write ok`. Nothing else, and never the token.

## Stop rules

- Never revoke, archive or delete an agent.
- Never copy tokens from Grok Bot or another machine.
- Never print a token, the key or `ht` output that holds one.
- A step fails: report the exact error in the identity line, then carry on with the role.
