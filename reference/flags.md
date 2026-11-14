# Flags and releases

Read when you switch a feature flag, move a ticket between flag columns, or write a release note.

- Every board 15 ticket with a flag shows its flag link first. Top line of the description: the admin flag URL and its mode. Merged work in QA or a flag column needs a flag. No flag on purpose goes to No Flag.
- The flag column follows the live flag. Flag at Everyone: card in Flag: Everyone. No proof step for that move.
- Every flag goes to Everyone. Only can't-undo harm waits at Owner + QA: charges money, leaks data, deletes for good, emails customers.
- Failed live check: roll the change back, flag stays on. Never switch Off, never park a flag.
- Valentin asks for a flag switch, in chat or on a ticket: do it that turn. His ask is the approval. Never ask him back. Thumbs up only for a switch you propose unasked. Runners never switch Off on their own.
- Exception: design and visible UI changes ship at Owner + QA. Everyone only after another runner's side-by-side Figma QA passes. The lead switches it. Never cut a theme, option or icon set the ticket does not name.
- Software Factory: every changelog line names its ticket, with ticket number and ticket title. No filler like "Checks and fixes". Each app's release check refuses a line without both.
- Releases reach his desktop through the app's in-app update. Never hand-replace a running exe.
- Runners may read prod logs, health checks and flag state. Read only, for own work.
