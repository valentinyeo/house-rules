---
name: join-slack
description: "join slack;join the fleet chat;get on slack;slack setup. /join-slack: put this lead session in Slack #fleet with the other leads. Reuses the lead's bot if it exists, points Slack mentions at this tmux session, checks read and reply. Use at lead startup, after a lead moves to a new session, or when Valentin says join Slack."
---

# Join Slack #fleet

Every lead lives in #fleet. Valentin starts threads there. Leads reply inside them.

Tools are in `~/.local/bin`. Run `export PATH=$HOME/.local/bin:$PATH` first.
Never print a token.

## 1. Who am I

- Session: `tmux display -p '#S'`.
- Members list: `~/.config/fleet-slack/members.tsv`.
  Columns: name, aliases, token var, uid var, delivery, target.
- Your row has your lead name (for example `cos`, `mini-boss`, `ci-boss`).

## 2. Row exists

Target is not your session? Repoint it. This keeps the bot token:

```bash
fleet-slack-add <KEY> "<Display Name>" <your tmux session> session-say
```

`KEY` is your row name in capitals (`COS`, `CIBOSS`).
The tool restarts the relay and prints `relay up`.
Delivery `none` means you only post, mentions never reach you. Repoint with the line above.

## 3. No row yet

- Check for a bot token: `grep -c "^SLACK_<KEY>_BOT_TOKEN=" ~/.config/fleet-slack/env`.
- Missing? Look in 1Password: `stack-key --list | grep -i slack`.
  Found: `stack-key <item> | fleet-slack-set-token <KEY>`.
- Still missing: a new Slack app is needed. That is a key.
  Ask Valentin with one Question on your own lead ticket.
- Then run the step 2 line.

## 4. Check

- Read: `slack-read 10` shows the last messages.
- Reply test, posts nothing:
  `SLACK_SAY_DRY_RUN=1 slack-say <name> --thread <ts> "test"`.
  Take `<ts>` from any thread Valentin started.
- Relay: `systemctl --user is-active fleet-slack-relay` says `active`.

## Rules

- Reply only inside Valentin's threads: `slack-say <name> --thread <ts> "<msg>"`.
- No top-level, status or bot-to-bot posts. slack-say refuses them.
- `--alarm` only for a real alarm, max one per 2 hours.
- Caveman voice, full https links.
- Never take another lead's row or bot.

## Report

One line: `slack: <name> -> <session>, relay up, read ok, reply dry-run ok`.
