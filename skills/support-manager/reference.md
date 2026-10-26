# Support reference

Facts as of 26 Oct 2026. Recheck code before you trust a number.

## Repos and surfaces
| Surface | Repo (VPS checkout) | Deploy | CI |
|---|---|---|---|
| help.hypertask.ai chat, articles, admin `/admin`, widget `/widget/widget.js` | valentinyeo/ai-chatbot, base `master` (`~/projects/ai-chatbot`, stale: pull first) | Manual `npm run deploy` (wrangler, worker `ai-chatbot`, D1 `chatbot-db`). No deploy on merge. | `ci.yml`: test, typecheck, replay. Automerge on. |
| docs.hypertask.ai (Astro/MDX) | hypertask-ai/docs, base `main` (`~/projects/HypertaskDocs`) | `deploy.yml` on push to main | build-check, docs-refs, gitleaks. Automerge on. |
| Docs into the chat (D1 articles) | ai-chatbot `scripts/sync-docs.mjs` | `sync-docs.yml`, manual dispatch, runs `--prune` | Snapshot articles first. First prune run per change needs Valentin's go. |
| hypertask.ai chat embed | hypertask-ai/astro, default branch `feature/v2-homepage` (`~/projects/hypertask-astro`) | Cloudflare Pages | claude-review, gitleaks. Automerge OFF. Owner: HT Growth Lead. |
| In-app help search, app AI sidebar | hypertask-ai/hypertask | /ship as usual | Not your board. File on board 15 as HTPR. |
| Old memory and rules | hypertask-ai/support-bot | none | read only |

Chat code map (ai-chatbot):
- Retrieval: `src/ai/rag.ts`. Prompt: `src/routes/chat.ts` `buildSystemPrompt`.
- Model: Claude Haiku 5.5 only, via Cloudflare AI Gateway `hypertask-ai`, prompt caching on.
- Debug retrieval: `https://help.hypertask.ai/api/chat/debug-rag?q=<question>`.
- Article list: `https://help.hypertask.ai/api/articles`.
- Rules for agents live in the repo's `CLAUDE.md` (AGENTS.md points to it).

App help search lives in `src/lib/help-docs/searchHelpDocs.ts` and
`src/lib/ai/tools/searchHelpDocs.ts` in the app repo.

## Board
Help Feedback, key HEFE, project 10450, team Hypertask.
- URL: https://app.hypertask.ai/project?id=10450
- Ticket URL: `https://app.hypertask.ai/detail/project-10450/<n>`
- Columns: Inbox 29693, Triage 29694, Ticketed 29695, Answered 29696, Done 29697, plus In Progress and In Review.
- Never work in "Valentin Yeo's Team".
- Read only: in-app Feedback board 2101 (intake), Marketing board 2108 (MARK).

## Intake
All read only. Never reply to a customer.
- Help chat conversations: help.hypertask.ai/admin (inbox). Skip `is_eval` rows.
- In-app feedback: board 2101.
- Email: the three support inboxes via Superhuman/Gmail tooling if this
  session has it. If not, note "email not read" in your report.
- X mentions of @hypertask: only if this session has an X read tool.
- Marketing board 2108 once a day: flag claims that clash with help or
  pricing. Clashes go to HT Product Lead, never edit MARK cards.

## Product rules
- Help chat is AI-first. No prominent Human button. Human handoff offered only inside the chat.
- Sales = education. No pushy pitches.
- hypertask.ai: floating chat icon only. Docked chat stays on docs and help.
- The same help chat should power the app's AI sidebar (future).
- Included AI allowance: never state a dollar value to customers.
- Prices (per user per month, yearly/monthly): BYOK $8/$10, Pro $16/$20.
  Source of truth: app `src/lib/subscriptionPlans.ts`. Recheck before use.
- Free plan: generous; unlimited members, boards, tickets. Storage numbers
  (25 MB/file, 2 GB) are NOT final. Valentin decides.
- Test chats: delete only recorded chat ids, never by time window.

## Credentials (names only)
Get values with `stack-key <item> <VAR>` into a chmod 600 file. Never echo.
- `anthropic`: ANTHROPIC_API_KEY (primary key, chat only).
- `cloudflare`: CLOUDFLARE_API_TOKEN (wrangler deploy, D1).
- `Help admin CLI - Support bot (Cloudflare Access service token)`: for
  help.hypertask.ai `/admin/api` (Access app "helpdesk", policy "Support bot
  CLI"). Expires 2027-10-25.
- Worker secrets (set in Cloudflare, never in git): ANTHROPIC_API_KEY,
  ANTHROPIC_MODEL, ADMIN_PASSWORD, EVAL_INGEST_SECRET.
- GitHub Actions secrets: CLOUDFLARE_API_TOKEN (docs), CLOUDFLARE_D1_TOKEN
  (ai-chatbot sync).
- Board identity: needs a session token, see takeover.md.
Rotation, new keys and paid keys: Valentin only.
