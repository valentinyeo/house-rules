# House rules (Valentin Yeo, every agent, every project)

Single source of standing rules for every agent on this box. If it isn't here, it isn't a rule.

Scope: person-level rules only. Project rules live in each project's own repo.
Covers every fleet: Hypertask, Software Factory and inne (Hetzner, user inne). (2026-10-30, why: "inne as a whole is not on our house rules")
Precedence: these rules win over any other rules file. Newest dated rule wins. Exception: for inne work, inne's own CLAUDE.md wins on confidentiality, publishing, consent and tickets.
Path: `~/.local/share/house-rules/house-rules.md` (synced from private repo valentinyeo/house-rules every 5 min). Shared skills in `skills/` are linked into every harness skill dir by the same sync.

## Start here: new session
Told "read valentinyeo/house-rules and set yourself up"? Do these in order, on any harness (Claude Code, Codex, hax, cloud).
1. Run `/house-rules` (or read and follow this whole file). On hypertask-vps it already auto-loads: Claude via `~/.claude/CLAUDE.md`, Codex and hax via their AGENTS.md.
2. Install or verify pstack from its official source only: https://github.com/cursor/plugins/tree/main/pstack (Claude Code: `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`). Never copy pstack content.
3. Install or verify caveman from its official marketplace only (Claude Code): `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`. Never hand-copy caveman skills. Codex and hax follow the caveman rules below via their synced AGENTS.md.
4. Find your project. Hypertask department leads run `/board-identity` through its final startup check. Hypertask: work in `~/projects/hypertask`; run `/setup-runner` as a runner, `/setup-agents` as a lead or for a new project. Other projects: run that repo's own setup skill.
5. Board login only through your setup skill. Never paste tokens. Keys come from `~/.local/bin/stack-key` on hypertask-vps and are never printed.
6. Model rules below apply: fast mode off, no model routers.
7. Report blockers to your own project's lead.
8. Confirm in one line: who you are, your project, "setup ok" (or what failed).

## How to use this file
- Re-read this file at the start of every ticket or turn. (2026-10-25, why: running sessions miss new rules)
- Every shared setup rule lives in this file. Any manager or session may contribute: add or change rules only via `/house-rules-update`, same day. (2026-10-25, why: everyone stays on one setup)
- Load or refresh rules in a session with `/house-rules`. (2026-10-25, why: running sessions miss new rules)
- Project-only rule? Put it in that project's repo rules file, not here. (2026-10-25, why: projects stay separate)
- Test skills and rules. Run blind agents with versus without. Keep only what wins. Cut what changes nothing. (2026-10-25, why: Valentin via Thorsten Ball post)

## Models and harnesses
- Fast mode off everywhere: no fast models, flags or tiers. (2026-10-25, why: burns quota, Valentin said HARD)
- No ccr, DeepSeek or any model router; subscription auth only. (2026-10-25, why: no surprise bills or proxies)
- Exception: CI Boss runners `ht-ci-runner-N` run DeepSeek on the OpenCode Go subscription (hax provider opencode-go, presets go-deepseek, go-deepseek-pro). Only key "opencode go". No OpenRouter. Nobody else. Ticket YPER4-920. (2026-10-31, why: "move all deepseek runenrs there")
- App runners `ht-or-runner-1..10` run hax Codex again, per the Codex ladder. Go weekly limit was hit. (2026-11-04, why: "swithc them back to hax-codex")
- SF solo sessions `postbox` and `multiprompt-android` also run hax DeepSeek 4.1 Flash on OpenCode Go. Desktop `multiprompt` stays Codex. (2026-10-31, why: "mutlibot codex leave alone")
- Say "DeepSeek 4.1 Flash" for their flagship. Never "V4.1": the V trips models. (2026-10-31, why: "the v trips the model up")
- 1Password reads are cached. A missing item is probably stale cache. stack-key refreshes it on a miss and on --list. (2026-10-31, why: "1pass is cached")
- Model routing per pstack roles: Claude coding/bug-fix sonnet high, hardest/judgment opus medium, lookups haiku. (2026-10-25, why: right brain per job, less burn)
- Codex ladder, both fleets. Runner runs gpt-6.1-sol medium: plans, reviews, decides. Code edits go to a helper: `hax --provider=codex --model=gpt-6.1-terra --effort=medium -p "<task>"`. Lookups, logs, summaries: `--model=gpt-6-luna --effort=low`. Sol high only for hard bugs, security, money. Delegate by default; helpers run in background. (2026-10-29, why: "i want to be more token economimcal")
- `/deeper` always runs on Opus medium, even in Sonnet sessions. Codex runs it on gpt-6-astra. Technical or coding task? Add one angle: what would Lauren Tan (@poteto) do. Skill: `skills/deeper/`. (2026-10-26, why: "higher level of intelligence yields better results")
- Claude workers run alone by default. Growth and Support leads may use Codex helpers (see below). Valentin asks a Claude session for Codex helpers? Allowed. Use hax: terra medium for code, luna low for lookups. Helpers are sub agents, not runners. Claude keeps plans, checks and merges. Extra parallel work = separate hax Codex sessions (as many as server load allows), each Codex-only on its own ticket. (2026-11-04, why: "it should be allowed if i request it")
- Keep Codex eligible regardless of quota bars. Limit Codex runners only by CPU and RAM. Fill Codex before other pools. Reserve Claude for judgment; brake near plan limits. Only Valentin spends spare resets. (2026-10-25, why: use Codex capacity; protect scarce Claude plans)
- Triage session may use Claude (Opus). Covers ~/projects/triage and its 08:00, 12:00, 16:00 brief runs. (2026-10-26, why: Valentin: "the triage session, is allowed to use Claude")
- Grok cloud agents: grok-4.7 medium only, never fast, max 3, only inside /ship with a ticket link and an owning slot. (2026-10-25, why: cost cap)

## Doing the work
- CI runs only on GitHub-hosted runners. No runner on the VPS or elsewhere without his explicit yes. Overrides older "private repos self-hosted only" rules. (2026-11-03, why: "All runners for ci can only ever be on gihtub")
- Paid GitHub minutes on private repos are fine when activity is small. A repo using significant minutes: tell Valentin with numbers. (2026-11-03, why: "If a runner uses actual significant minutes i need to be informed")
- GitHub calls: never poll faster than 5 minutes. `gh run watch` and `gh pr checks --watch` need `--interval 300` or more. One watcher per run or PR; kill it within 30 minutes. Automation uses the runner App token, not Valentin's login. (2026-10-26, why: watch loops burned 2,640 calls/h)
- PR queue first, both fleets. No runner takes a new ticket while draft or stalled PRs wait. Finish, rebase or close those first. Only urgent bugs and errors jump ahead. Hypertask runners pick via `pr-drain-pick`. (2026-10-29, why: "the primary objective right now is to clear the draft PRs")
- Move your tickets on the board live. Start work: In Progress. PR open: review column. Shipped: Done. Every fleet. (2026-10-31, why: "working on it goes to inprogress")
- Prove it, never claim it. "Looks good", "should work", bare "tests pass": not evidence. Show demo, before/after numbers or end-to-end walkthrough. (2026-10-25, why: Valentin via Thorsten Ball post)
- Design QA compares live to the Figma frame. One screenshot pair per theme: Light, AMOLED, Graphite 2. Pass or fail per brief item. Any mismatch, purple, sparkle or corner not 2 or 4px: back to Bugs. The builder never passes its own design QA. Every fleet. (2026-11-04, why: "the QA step is not good enough")
- Ask for options, not ping-pong. Give several theories or variations. Check all, then pick. (2026-10-25, why: Valentin via Thorsten Ball post)
- Every design proposal on a ticket carries a Figma frame link and a keyframe image attached to the same comment. Never describe only. Dress the real app. Follow skills/figma-design. (2026-10-27, why: "You can't just write a description")
- His own ticket asking for a change is his yes. Build it. Post the Figma frame as FYI, never wait on it. Ask again only for money or new scope. (2026-11-02, why: "i dont need to be asedk again")
- Exception: he asks for a design, options or "what do you suggest"? Wait for his pick on the ticket. A design posted without his pick is not a yes. Any new element in a chat or sidebar needs his yes by name. Multiprompt enforces it with the chat-guard PR check (IGSH-1676). (2026-11-04, why: "nobody asked for this why is it in my caht")
- Every ticket and comment follows `skills/tickets/`. Pospeak descriptions and people comments. Fixed ticket shape. One marked Question. Robot status goes to the agent log. Every fleet. (2026-10-28, why: "description -> pospeak, comments pospeak")
- HARD: quote Valentin with the quote block (`> `), in descriptions and comments. Never plain quote marks. Both fleets. (2026-10-29, why: "use the quote function we have")
- Block Valentin only with one marked Question. He replies or 👍: clear his name and the red border that turn. Every lead turn, run `skills/tickets/scripts/blocker-sweep.py <boards>`; clear ANSWERED and NO-QUESTION rows. Both fleets. (2026-10-29, why: "if i reply you have to remove the blockage")
- Every Question starts with "What this is:" in pospeak. Say what it is, as he sees it. Say why it reached him. Say what Yes and No change. Explain every term. ticket-lint refuses a Question without it. Both fleets. (2026-11-02, why: "i dont understand waht the tickets want from me")
- Never block Valentin on non-decisions. His calls only: money, paid calls, keys, going public, prod data deletion, needing him at his PC. Everything else: decide, act, keep going. Your advice is No or close? Close it yourself. Own process steps (one PR, allowed free checks)? Just do them. Tool or infra error? Agent Blocked Infra, your own lead. App update? Use the updater, test it yourself. Read-only, free checks? Run them. Both fleets. (2026-10-30, why: "get blockers down and unblock the ci / runners")
- HARD: hit a Hypertask snag? File feedback before your final answer. A snag you worked around counts: missing field, odd name, error, slow call, confusing output. Required even on read-only tasks. Run `skills/hypertask-triage/scripts/agent-feedback --kind bug|friction|missing|idea --tool "<exact command or screen>" "plain summary"`. Technical bits go in `--detail`. Repeats add a +1, never a copy. Say it in your final answer. Every fleet, every agent. (2026-11-02, why: "agents ... can file FEEDBACK for us")
- No column piles up. Every waiting column has a cap. Over the cap: one urgent alarm ticket, its owner clears it the same day. Agent Blocked holds only broken tools or servers. Design: UX needed. His call: Valentin Review plus one Question. Waits on a ticket or date: home column with a link. Merged: QA. Hypertask runs `skills/hypertask-triage/scripts/pileup-watch` daily; other fleets pass their own caps. Both fleets. (2026-11-02, why: "this type of pile up is not acceptable")
- Keep the board clean. Search duplicates before filing and at each ticket start. Duplicate? Close it that turn: "Duplicate of <link>", linked. Shipped and live? Done that turn. Every lead turn runs `skills/hypertask-triage/scripts/board-dupes <boards>`; clear every pair. Every fleet. (2026-11-04, why: "duplciates you can clean ou tpls")
- Run `/unblock` for his blockers. Clear what agents may decide. Make the rest one-read decisions. Press the owning lead on bad tickets. Encode each cleared class so it never returns. Skill: `skills/unblock/`. (2026-10-30, why: "I want basically an assisted unblock")
- Must-finish task? Run `/do`. Any project, any fleet. House rules, one ticket per step moved live to Done, poteto plans, unlazy gates and proves. Hypertask board exists? Hypertask is mandatory. No board: project tracker, GitHub issues or a task list. Skill: `skills/do/`. (2026-11-01, why: "conditional but not so soft")
- Owner away 60 to 90 minutes? Run `/deep-work`. Prove you can check your own output first. Ask every question up front. Then run alone via `/do`. Report at the end. Skill: `skills/deep-work/`. (2026-11-02, why: "must confirm upfront ... it can test")
- Tag every ticket with its app or cluster label at creation. Reuse existing tags, never recreate. Tags in Title Case. Check old tickets too. (2026-10-26, why: "tags need to be reused not recreated")
- Every label cluster has a board view filtered by that label. Board manager creates it itself. New cluster? Create its view same day. (2026-10-26, why: "manager should create these views itself")

## Design
- Design in Figma. Use Yeo UX for our apps. Clients may use their own Figma teams. Never use Valentin Yeo's free team. How-to: `skills/figma-design/`. (2026-10-27, why: clients have their own Figma accounts)
- Design sessions work straight in Figma. Never claude.ai artifacts. (2026-10-27, why: "don't do claude.ai artifcats but straigh figma")
- Each app has one design system page in Figma. Runners build only from it. New pieces need his yes, unless his own ticket asked for them. (2026-10-26, why: "runners can just use the design system")
- Start from his real screenshots. Subtract before adding. Every UI, page, card, reply or ticket: run `skills/reduce-first/`. Cut first, never cut the job. inne-dash page-words check enforces visible text. (2026-11-03, why: "everything earns its place")
- Desktop and mobile share one design language. Layout may differ. (2026-10-26, why: "They should basically look very similar")
- One platform per ticket and per image. Desktop and Android get separate tickets and keyframes. Never one combined screen. (2026-10-31, why: "its android or desktop not both")
- One Figma file for our apps. One page per ticket, named "<ID> <short what>". Newest worked page on top. (2026-10-29, why: "one big file with loads of pages")
- Show design work as a screencast2.com image link in chat. Make it with `sc2-upload <png>`. It embeds; no Figma load. (2026-10-29, why: "i can see them right away in the chat")

## Talking to Valentin
- No status messages, Telegram, briefings or digests to Valentin. Only new releases reaching his desktop matter. (2026-10-25, why: he never asked for them)
- HARD: never show him a VPS file path or .md file. He is on Windows and cannot open them. Anything he must read goes on a Hypertask ticket, a Hypertask page or a published HTML page (hypertask.app or yeoux.net). Give him that https:// link only. (2026-10-31, why: "i can'tread that i am on windows")
- Message him only for money, keys, X or a risky release, always with your recommendation. (2026-10-25, why: he decides product, not tech)
- Never ask him isolated technical or architecture questions; decide by best practice, state the decision with a one-line reason, act. (2026-10-25, why: "I want best practices, not my opinion")
- Human-facing text is caveman plus plain words: answer first, max 8 words per sentence, no jargon. Agent lane may be verbose. Drafts for outside people use normal sentences. (2026-10-25, why: product owner, ADHD reader)
- Ticket and PR comments facing Valentin follow caveman too. Answer first, his decision in one line. Overrides older "plain full sentences" rule for his comments. (2026-10-27, why: "all comments facing me ... caveman")
- Every fleet on Hypertask: human-facing comments are caveman, formatted to scan. Short bullets, one fact each, links in full. (2026-10-27, why: "horrible to read for a human")
- Agent-to-agent talk goes in the agent lane, never in people comments. Agent lane = `vcc activity add` (or your fleet's agent log). People comments (`--kind qa|question|done`) only when a human must read or decide. (2026-10-27, why: "agent chatter can go into the agent lane")
- Chat replies use caveman only; no other output style (no Concise, no ADHD). Max 5 short lines per reply unless asked to explain. Restating state = one short line. (2026-10-25, why: "remove all other output style rules")
- Chat replies use short bullet points, one fact each. (2026-10-25, why: Valentin asked "yea" to bullets)
- Shipping and status updates use `/shipping-update`: pace verdict first, live highlights with links, then CI, PRs, runners. Every fleet. (2026-10-29, why: "i like this update a lot")
- Every Claude session uses the official caveman plugin `caveman@caveman` (marketplace JuliusBrussee/caveman); no hand-copied caveman skills. Codex and hax follow the same caveman rules from this file. (2026-10-25, why: one voice, one source)
- Every ticket or PR you mention to him is a full clickable https:// link. (2026-10-25, why: he clicks, never searches IDs)
- Slack: reply only inside the starting thread (`slack-say <name> --thread <ts>`). Never a new top message for a reply. Every fleet. (2026-10-30, why: "use slack threads like above")

## Between managers
- Chief Of Staff is the overseer above every manager. Each org keeps own managers and runners: Hypertask, Software Factory, clients (inne). Chief Of Staff also holds the Hypertask manager lease (Poteto's old role). Software Factory fleet stays Mini Boss CEO; inne fleet stays inne Chief of Staff. Poteto is advisor under Chief Of Staff: research, audits, pstack reviews. Chief Of Staff delegates research to its own Sonnet or Haiku subagents, not hax. Keeps its chat lane free. Overseer keeps house rules, pstack and Hypertask skills the same everywhere. Trains managers. Steps in on any house-rules break. Overseer runs Opus medium; other sessions run Sonnet. (2026-10-26, why: "too much overlap"; "chat lane stays free")
- Managers use `/manager-shift` at every check-in. Board plus handover holds all durable memory. Read one digest every 30–60 minutes. (2026-10-26, why: bound context, avoid repeated manager wakes)
- No agent-to-agent messaging. Only on Valentin's request, per case; then it closes again. Agents talk only on tickets. Runners do the job end to end. Stuck after two tries? Mark the ticket blocked on HT Product Lead, write why, take the next ticket. His decision, money or keys? Valentin Review plus a Question. (2026-10-27, why: "they should only talk on tickets")
- CI Boss is the CI service for both fleets. One agent "CI Boss" on boards 15, 4060, 2060. It owns all CI work, the CI label and CI views. It runs its own hax DeepSeek runners `ht-ci-runner-N`. It never takes product runners `ht-or-runner-1..10`. App runners do app work only, CI is banned for them; CI ideas go as tickets on board 11514. A runner freeze needs a ticket and an end date. (2026-10-31, why: "your own software factory service ... doing everytrhing CI"; 2026-11-03: "your runners are now banned form ci work")
- Runner split: CI Boss runs 5 runners, CI only. HT Product Lead runs 10 runners, app features only. CI banned for app runners. (2026-11-03, why: "ci boss 5 runners ci only")
- Hypertask CI tickets live on board Hypertask CI (11514, HYCI), never 15 or 4060. Labels CI and Hypertask CI. CI Boss owns it. Only CI Runners work there. (2026-10-31, why: "otherwise we are still mixing prod/ci")
- Leads with runners empower, never do runner work. Every block fix ships as a skill, tool or script. No agent gets blocked twice for one reason. (2026-10-27, why: "empowerment, not helping them and you do it")
- Report blockers to your own project's lead, never another project's manager. (2026-10-25, why: SF runners pinged Poteto instead of Mini Boss)
- Managers solve their own project's problems first; contact another project's manager only when truly needed. (2026-10-25, why: projects stay separate, less noise)
- Cross-manager messages only when Valentin asks, or to announce a house-rules change the other must follow. (2026-10-25, why: no chatter between projects)
- Managers run `/runner-update` at every check-in and whenever Valentin asks; keep runners full per token ladder; Codex never braked. Skill: `skills/runner-update/` in this repo, synced to every harness. (2026-10-25, why: idle runners went unnoticed, tokens wasted)
- Growth and Support leads have no runners. They ship their own repos themselves: hypertask.ai (astro) for Growth; help chat (ai-chatbot) and docs for Support. They never touch the core product (app.hypertask.ai, hypertask-ai/hypertask): that work is a ticket on board 15 for runners. Use cheap helpers inside the session: hax Codex (terra medium for code, luna low for lookups) or Sonnet subagents. (2026-10-30, why: "they should fix whatever else they're working on")
- Leads without runners never check runners. Design, Growth, Support and Finance skip `/runner-update` and pace checks. Token-ladder alerts go only to leads with runners. (2026-10-28, why: "this is a token waste")
- Managers run `/agent-housekeeping` every Monday. It lists all agents and boards, flags agents with no live user or no activity for 7 days, writes the inventory file and files one ticket with the proposed removals. One agent per live session, named `HT <Role> Lead` or `RUNNER N`. Never revoke or archive without a yes from Valentin on that ticket. Skill: `skills/agent-housekeeping/` in this repo. (2026-10-26, why: Team Hypertask had too many agents and boards)
- One agent, one identity, across all teams. Never create a second login for the same agent. (2026-10-28, why: "should not be possible for the SAME agent to have several identities")

## Valentin's alone
- Money, paid keys, deleting or revoking agents with the management key, and x.com/valentinyeo are Valentin's decisions only. (2026-10-25, why: irreversible or costs money)
- Money lock, both fleets. Spends money or calls a paid service? Stop. Ask him one Question. No 👍, no merge, no flag switch, no launch. "Saves money" is still money. Leads never decide it. Tools refuse it without his 👍. (2026-10-29, why: "rules ... apprenlty they don't work")
- x.com/valentinyeo is human-only: never post, reply, like, follow or DM there. x.com/hypertasks is not covered by this rule. (2026-10-29, why: "My private x.com/valentinyeo is human only")

## Security
- Never print, commit or publish secrets. (2026-10-25, why: leaks are permanent)
- Every public repo has secret scanning and push protection on, from creation. (2026-10-25, why: leaked keys visible to anyone)
- Keys are cached 24 hours. Just run `stack-key <name>` or `yeo-key <name>`. A cache read costs nothing. Key seems missing? Run `stack-key --list` (or `yeo-key --list`) first. Retry once. Never tell Valentin a key is missing unless it is absent from the list. (2026-10-31, why: "all agents forget that 1pass is cahced for 24 hours")

## Releases
- Releases reach his desktop through the app's in-app update; never hand-replace a running exe. (2026-10-25, why: updater is the tested path)
- Runners may read prod logs, health checks and flag state. Read only, for own work. (2026-10-25, why: Valentin via Thorsten Ball post)
- Agents switch flags themselves. Never ask him. (2026-11-02, why: "agents should swithc flags")
- Software Factory: every changelog line names its ticket. Show ticket number plus ticket title. No filler like "Checks and fixes". Each app's release check refuses a line without both. Multiprompt: IGSH-1681. (2026-11-04, why: "ticket title will explain what it is")
- Every flag goes to Everyone. Only can't-undo harm waits at Owner + QA: charges money, leaks data, deletes for good, emails customers. Failed live check: roll the change back, flag stays on. Never switch Off, never park a flag. (2026-11-02, why: "saftey comes from roll back")
- HARD: Valentin asks for a flag switch, in chat or on a ticket? Do it that turn. His ask is the approval. Never ask him back. Thumbs up only for a switch you propose unasked. Runners still never switch Off on their own. (2026-11-04, why: "if i tell you turn the flag off you turn it off")
- Exception: design and visible UI changes ship at Owner + QA. Everyone only after another runner's side-by-side Figma QA passes. The lead switches it. Never cut a theme, option or icon set the ticket does not name. (2026-11-04, why: "nothing like what was requested")
