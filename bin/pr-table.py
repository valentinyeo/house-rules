#!/usr/bin/env python3
"""Fleet status for /pr-check: plain bullet lines, no tables (mobile harness)."""
import json,subprocess,datetime,os,glob,sqlite3
REPO="hypertask-ai/hypertask"
NAMES={'desktop-developer':'Dev Agent','cli-mcp-ai-chat':'CLI Agent',
       'speed-engineer':'Speed Engineer','qa-agent':'QA Agent'}
def gh(*a):
    return subprocess.run(["gh",*a],capture_output=True,text=True,timeout=120).stdout
now=datetime.datetime.now(datetime.timezone.utc)
def ts(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def age(p): return (now-ts(p['mergedAt'])).total_seconds()/3600
merged=json.loads(gh("pr","list","--repo",REPO,"--state","merged","--base","production",
                     "--limit","100","--json","number,headRefName,mergedAt") or "[]")
def counts(rows): return [sum(1 for p in rows if age(p)<=h) for h in (1,2,12,24)]
BLOCKED_SECTION='Agent Blocked (Infra)'

def conf_value(slug,key,ext='conf'):
    """Read one HT_* value out of the agent's .conf or .env; '' when absent."""
    try:
        for line in open(os.path.expanduser(f'~/.config/hypertask-agents/{slug}.{ext}')):
            if line.startswith(key+'='):
                return line.split('=',1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ''

def board_id(slug):
    """The agent's Hypertask id. Queue counts match on this, never on the
    display name: Valentin renamed two agents in the app and every name-based
    count silently went to zero."""
    return conf_value(slug,'HT_AGENT_ID','env')

_board_cache={}
def board_tasks(pid):
    """Every task on one board. The CLI caps a page at 100, so page until short.

    Cached per board: agents do not all live on board 15 (the feedback agent is
    on 2101, the dashboard agent on 3247), and counting their queue against 15
    reports a permanent zero for work that is really sitting there."""
    if pid in _board_cache: return _board_cache[pid]
    out,off=[],0
    while True:
        raw=subprocess.run(['hypertask','tasks','list','--project',str(pid),'--limit','100',
                            '--offset',str(off),'--json'],capture_output=True,text=True,
                           timeout=120).stdout
        try: page=json.loads(raw).get('tasks',[])
        except Exception: break
        out+=page
        if len(page)<100 or off>600: break
        off+=100
    _board_cache[pid]=out
    return out

def agent_ids(t):
    return {a['agent']['id'] for a in t.get('assignees') or [] if a.get('agent')}

def queue_line(slug,agent_id):
    """Board-side depth: what this agent can pull, plus what is parked on it.

    The delivery queue in sqlite only shows work already handed to the worker,
    which is why an agent with eight tickets waiting on the board still read
    'queue empty'."""
    starts=[x.strip() for x in conf_value(slug,'HT_START_SECTIONS').split(',') if x.strip()]
    tasks=board_tasks(conf_value(slug,'HT_PROJECT_ID') or '15')
    mine=[t for t in tasks if agent_id and agent_id in agent_ids(t)]
    # An agent pulls anything sitting in its start sections, assigned or not.
    waiting=[t for t in tasks if t.get('section') in starts
             and ((agent_id and agent_id in agent_ids(t)) or not agent_ids(t))]
    blocked=[t for t in mine if t.get('section')==BLOCKED_SECTION]
    review=[t for t in mine if t.get('section') in ('Checks','Verifier','AI Review','Valentin Review')]
    return waiting,blocked,review

agents={}
agents_display={}
for f in sorted(glob.glob(os.path.expanduser('~/.config/hypertask-agents/*.env'))):
    slug=os.path.basename(f)[:-4]
    if os.system(f'systemctl --user is-active --quiet hypertask-agent-worker@{slug}')!=0: continue
    agents[slug]=NAMES.get(slug,slug)
    agents_display[slug]=board_id(slug)
def turns_done(slug,hours):
    """QA and other non-shipping agents are measured in tickets processed."""
    db=os.path.expanduser(f'~/.local/state/hypertask-{slug}/queue.sqlite3')
    out=[]
    try:
        con=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
        for h in hours:
            cut=(now-datetime.timedelta(hours=h)).isoformat()
            out.append(con.execute("SELECT count(DISTINCT ticket) FROM deliveries "
                                   "WHERE state='done' AND updated_at>=?",(cut,)).fetchone()[0])
        con.close()
    except sqlite3.Error:
        return None
    return out
t=counts(merged)
print("MERGED LIVE")
print(f"- All agents: {t[0]} in 1h, {t[1]} in 2h, {t[2]} in 12h, {t[3]} in 24h")
for slug,name in agents.items():
    if slug=='qa-agent':
        q=turns_done(slug,(1,2,12,24))
        if q: print(f"- {name} (tickets checked): {q[0]} / {q[1]} / {q[2]} / {q[3]}")
        continue
    c=counts([p for p in merged if p['headRefName'].startswith(f'agent/{slug}-')])
    print(f"- {name}: {c[0]} / {c[1]} / {c[2]} / {c[3]}")
print()
print("DOING NOW")
for slug,name in agents.items():
    st=os.path.expanduser(f'~/.local/state/hypertask-{slug}')
    try:
        con=sqlite3.connect(f'file:{st}/queue.sqlite3?mode=ro',uri=True)
        rows=con.execute("SELECT ticket,state,created_at FROM deliveries WHERE state IN "
                         "('running','claiming','pending')").fetchall()
        # A single slow turn is the usual reason a merge window reads zero, so
        # surface how long the current ticket has been running.
        started={t:c for t,s,c in rows if s!='pending'}
        rows=[(t,s) for t,s,_ in rows]
        con.close()
    except sqlite3.Error as e:
        print(f"- {name}: queue unreadable ({e.__class__.__name__})"); continue
    # Autonomous cycle deliveries carry no ticket; label them so the join
    # below never sees a None.
    rows=[(t or 'self-directed cycle',s) for t,s in rows]
    run=[t for t,s in rows if s!='pending']; pend=[t for t,s in rows if s=='pending']
    waiting,blocked,review=queue_line(slug,agents_display.get(slug,name))
    parts=[f"queue {len(waiting)}"]
    if pend: parts.append(f"{len(pend)} handed to worker")
    if blocked: parts.append(f"{len(blocked)} blocked")
    if review: parts.append(f"{len(review)} in review")
    q=", ".join(parts)
    if run:
        held=''
        for t in dict.fromkeys(run):
            c=started.get(t)
            if not c: continue
            try: mins=(now-ts(c)).total_seconds()/60
            except ValueError: continue
            if mins>90: held=f", on it {int(mins//60)}h{int(mins%60):02d}m"
        print(f"- {name}: working {', '.join(dict.fromkeys(run))}{held}, {q}")
    elif os.path.exists(f'{st}/wip.lock'):
        prs=open(f'{st}/wip.lock').read().split()
        print(f"- {name}: IDLE, blocked by its own open PR {' '.join('#'+p for p in prs)}, {q}")
    elif pend:
        print(f"- {name}: IDLE, {q}, none started, worker may be stuck")
    else:
        print(f"- {name}: IDLE, {q}")
