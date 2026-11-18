#!/usr/bin/env bash
set -uo pipefail

[ $# -ge 1 ] || { echo "usage: facts.sh <repo-path | session-name>"; exit 2; }
target="$1"
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ -d "$target" ]; then
  repo="$target"
else
  line=$("$HOME/.local/share/house-rules/fleet/roster-live" 2>/dev/null | tr ';' '\n' | grep -i -F "$target" | head -1)
  cwd=$(printf '%s' "$line" | grep -o '[~]/[^ )]*' | head -1)
  repo="${cwd/#\~/$HOME}"
  if [ -z "$repo" ] || [ ! -d "$repo" ]; then
    echo "no repo path in roster for session '$target'; pass its repo path"
    exit 2
  fi
fi
repo=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || { echo "not a git repo: $target"; exit 2; }
cd "$repo" || exit 2
base=""
for b in $(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null) origin/main origin/master; do
  git rev-parse -q --verify "$b^{commit}" >/dev/null && { base=$b; break; }
done
[ -n "$base" ] || base=HEAD
slug=$(git remote get-url origin 2>/dev/null | sed 's#.*github.com[:/]##;s#\.git$##')
files=$(git ls-tree -r --name-only "$base")
show() { git show "$base:$1" 2>/dev/null; }

echo "## Repo"
echo "slug: $slug"
echo "path: $repo"
echo "branch: $base @ $(git rev-parse --short "$base") (local snapshot; no fetch)"
echo "visibility: $(gh repo view "$slug" --json visibility -q .visibility 2>/dev/null || echo unknown)"
printf 'surface hints:'
grep -q -E '(^|/)build\.zig$' <<<"$files" && printf ' zig'
grep -q -E '\.ps1$' <<<"$files" && printf ' windows-powershell'
grep -q -E '(^|/)AndroidManifest\.xml$' <<<"$files" && printf ' android'
grep -q -E '\.xcodeproj/|(^|/)Package\.swift$' <<<"$files" && printf ' ios'
grep -q -E '(^|/)wrangler\.(toml|jsonc?)$' <<<"$files" && printf ' cloudflare-worker'
grep -q -E '^package\.json$' <<<"$files" && printf ' node:%s' "$(show package.json | grep -o -E '"(next|react|vite|astro|svelte|vue|expo|electron)"' | tr -d '"' | sort -u | tr '\n' ',')"
grep -q -E '^Cargo\.toml$' <<<"$files" && printf ' rust'
echo

echo
echo "## Verify skills"
skills=$(echo "$files" | grep -E '^\.(claude|cursor|agents)/skills/verify-[^/]+/SKILL\.md$')
[ -z "$skills" ] && echo "NO VERIFY SKILL: run /pstack:create-verification-skill before anything else."
for s in $skills; do
  d=${s%/SKILL.md}
  echo "- $s ($(show "$s" | wc -l) lines)"
  echo "  headings: $(show "$s" | grep -E '^#{1,3} ' | sed 's/^#* //' | tr '\n' '|' | cut -c1-300)"
  echo "  feature files: $(echo "$files" | grep -F "$d/features/" | grep -c -E '\.md$')"
  echo "  helper scripts: $(echo "$files" | grep -F "$d/" | grep -c -E '/[^/]+\.(sh|ps1|mjs|js|py|ts)$')"
done

echo
echo "## Formal verification"
python3 "$script_dir/formal_facts.py" "$repo" "$base" || echo "formal facts UNKNOWN (collector failed)"
echo
echo "Risk source hints (first 5 matches per area; inspect actual behavior and formal coverage):"
while IFS='|' read -r label pattern; do
  echo "### $label"
  matches=$(git grep -n -i -E "$pattern" "$base" -- '*.zig' '*.kt' '*.kts' '*.swift' '*.rs' '*.py' '*.ts' '*.tsx' '*.js' '*.mjs' '*.c' '*.cpp' '*.h' '*.go' '*.java' '*.sql' \
    ':!**/tests/**' ':!**/test/**' ':!**/androidTest/**' ':!**/node_modules/**' ':!**/vendor/**' ':!third_party/**' ':!**/build/**' 2>/dev/null | head -5 | cut -c1-220)
  echo "${matches:-no matching source hint (not proof that this risk is absent)}"
done <<'RISKS'
Money|\b(payment|billing|currency|invoice|ledger|money)\b
Cross-device sync|\bcross.device\b|\bmulti.device\b|\bdevice\b.{0,30}\bsync\b|\bsync\b.{0,30}\bdevice\b|\breplica\b
Retries or queues|retry|retries|backoff|queue|outbox
RISKS

echo
echo "## Pstack version and drift"
installed=$(for p in "$HOME"/.claude/plugins/cache/*/pstack/*; do
  [ -d "$p/skills" ] || continue
  v=${p##*/}
  [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && printf '%s\t%s\n' "$v" "$p"
done | sort -t $'\t' -k1,1V | tail -1)
latest=${installed%%$'\t'*}
pstack=${installed#*$'\t'}
echo "installed pstack: ${latest:-UNKNOWN (no installed pstack)}"
[ -n "$pstack" ] && echo "installed path: $pstack"
for s in $skills; do
  recorded=$(show "$s" | sed -nE 's/^pstack:[[:space:]]*([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]*$/\1/p' | sort -u)
  echo "$s pstack: ${recorded:-MISSING (version gap)}"
  if [ "$(printf '%s\n' "$recorded" | wc -l)" -gt 1 ]; then
    echo "conflicting pstack versions; version gap (cannot compare)"
    continue
  fi
  if [ -z "$recorded" ] || [ -z "$latest" ]; then continue; fi
  if [ "$(printf '%s\n' "$recorded" "$latest" | sort -Vu | tail -1)" != "$latest" ]; then
    echo "recorded pstack is newer than installed; cannot assess alignment"
    continue
  fi
  [ "$recorded" != "$latest" ] || { echo "recorded version matches installed"; continue; }
  echo "PSTACK CHANGED: $recorded -> $latest; repo must re-align."
  old=""
  for p in "$HOME"/.claude/plugins/cache/*/pstack/"$recorded"; do
    [ -d "$p/skills" ] && { old=$p; break; }
  done
  if [ -z "$old" ]; then
    echo "recorded version not installed; diff unavailable (not evidence of no changes)"
    continue
  fi
  for f in create-verification-skill/SKILL.md maintain-verification-skill/SKILL.md \
    create-formal-verification-skill/SKILL.md maintain-formal-verification-skill/SKILL.md \
    poteto-mode/playbooks/shipping.md poteto-mode/playbooks/bug-fix.md \
    poteto-mode/playbooks/eval.md principle-prove-it-works/SKILL.md; do
    if [ ! -f "$old/skills/$f" ] || [ ! -f "$pstack/skills/$f" ]; then
      echo "diff unavailable (source missing): $f"
    elif cmp -s "$old/skills/$f" "$pstack/skills/$f"; then
      echo "unchanged: $f"
    else
      echo "changed: $f"
      diff -u --label "$recorded/$f" --label "$latest/$f" "$old/skills/$f" "$pstack/skills/$f" || true
    fi
  done
done

echo
echo "## Workflows (source facts, not compliance verdicts)"
for f in $(echo "$files" | grep -E '^\.github/workflows/.+\.ya?ml$'); do
  t=$(show "$f" | awk '/^(on|"on"|\047on\047):/{p=1;if ($0 !~ /:[[:space:]]*(#.*)?$/) {print;p=0};next} p&&/^[^ #]/{exit} p&&(/^  [a-z_]+:/ || /cron:|branches:/){print}' | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g')
  c=$(show "$f" | grep -n -E '(^[[:space:]]*concurrency:|^[[:space:]]*group:|cancel-in-progress:)' | tr '\n' '|')
  echo "- ${f#.github/workflows/}: ${t:-triggers UNKNOWN} | ${c:-no concurrency declaration}"
done

echo
echo "## CI playbook evidence"
echo "Read the sources to judge: independent base/head verifier and PASS/PASS+NOTES/FAIL; touched-feature journeys plus repro; reused base results; cheap PR checks, scheduled heavy UI on default branch; revert first."
echo "Source excerpts per item (first 8 matches, 220 characters per line; absence is not proof):"
while IFS='|' read -r label pattern; do
  echo "### $label"
  matches=$(git grep -n -i -E "$pattern" "$base" -- .github AGENTS.md CLAUDE.md docs \
    '.claude/skills/verify-*' '.cursor/skills/verify-*' '.agents/skills/verify-*' 2>/dev/null | head -8 | cut -c1-220)
  echo "${matches:-no matching source excerpt; inspect workflows and policy directly}"
done <<'ITEMS'
Independent verifier and base/head verdict|independent|PASS\+NOTES|pstack-verifier|base.{0,30}head
Touched journeys and reused base results|touched.{0,30}(feature|journey)|repro|cache.{0,30}base|reuse.{0,30}base
Cheap PR checks and scheduled heavy UI|full.suite|nightly|schedule:|playwright|emulator|unit|secret.scan
Emergency revert first|revert|emergency
ITEMS

echo
echo "## Required checks on $base (classic protection and active rulesets)"
gh api "repos/$slug/branches/${base#origin/}/protection/required_status_checks" 2>/dev/null || echo "classic protection UNKNOWN (missing or no access)"
gh api --paginate "repos/$slug/rules/branches/${base#origin/}" 2>/dev/null || echo "active rulesets UNKNOWN (missing or no access)"

echo
echo "## Jobs for last 3 PR head commits (all workflow runs and attempts at each head)"
prs=$(gh pr list --repo "$slug" --state all --limit 3 --json number,headRefOid 2>/dev/null) || prs=""
if [ -z "$prs" ]; then
  echo "PR job counts UNKNOWN (PR list unavailable)"
elif [ "$(printf '%s' "$prs" | jq 'length')" = 0 ]; then
  echo "no PRs found; budget not proven"
else
  while IFS=$'\t' read -r number sha; do
    runs=$(gh api --paginate "repos/$slug/actions/runs?head_sha=$sha&per_page=100" 2>/dev/null | jq -sc '[.[].workflow_runs[]] | unique_by(.id)') || runs=""
    if [ -z "$runs" ] || [ "$runs" = '[]' ]; then
      echo "PR #$number $sha: UNKNOWN (no runs or API unavailable)"
      continue
    fi
    total=0
    known=yes
    while IFS=$'\t' read -r id name status created updated; do
      [ "$status" = completed ] || known=no
      jobs=$(gh api --paginate "repos/$slug/actions/runs/$id/jobs?filter=all&per_page=100" 2>/dev/null | jq -sc '[.[].jobs[]] | unique_by(.id) | length') || jobs=""
      if [ -z "$jobs" ] || [ "$jobs" = 0 ]; then
        known=no
        echo "  run $id $name: jobs UNKNOWN (no jobs or API unavailable)"
      else
        total=$((total + jobs))
        echo "  run $id $name: $jobs jobs; $status; $created -> $updated"
      fi
    done < <(printf '%s' "$runs" | jq -r '.[] | [.id, .name, (.status // "UNKNOWN"), (.created_at // "UNKNOWN"), (.updated_at // "UNKNOWN")] | @tsv')
    if [ "$known" = yes ]; then
      echo "PR #$number $sha: $total jobs (must be under 20)"
    else
      echo "PR #$number $sha: UNKNOWN ($total known jobs; incomplete API results or unfinished runs)"
    fi
  done < <(printf '%s' "$prs" | jq -r '.[] | [.number, .headRefOid] | @tsv')
fi

echo
echo "## Agent rule files"
for f in CLAUDE.md AGENTS.md; do
  show "$f" >/dev/null && echo "- $f: $(show "$f" | wc -l) lines, rule-table rows: $(show "$f" | grep -c -E '^\|.*\|.*\|$')"
done

echo
echo "## Recent PR verdicts (last 10 merged)"
gh pr list --repo "$slug" --state merged --limit 10 --json number,title,comments -q '.[]|"#\(.number) \(.title[0:60]) | \([.comments[].body|select(test("pstack-verifier:|PASS\\+NOTES|(^|\\n)(PASS|FAIL)(\\n|$)"))]|last|.[0:160]? // "no verifier comment")"' 2>/dev/null || echo "verdicts UNKNOWN (API unavailable)"
