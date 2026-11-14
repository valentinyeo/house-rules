# Design rules

Read when you design, review a screen, build UI or publish a report page.

- Design in Figma. Use Yeo UX for our apps. Clients may use their own Figma teams. Never use Valentin Yeo's free team. How-to: `skills/figma-design/`.
- Design sessions work straight in Figma. Never claude.ai artifacts. Clickable prototypes go in Figma only, as Figma prototype links. Never an HTML page on hypertask.app or yeoux.net.
- Each app has one Figma design system page: its style guide. Open it before any screen. Build only from it. Never invent a style. New pieces need his yes, unless his own ticket asked. An approved style change updates that page the same turn.
- Design values come from live app code. Fetch first, never a local copy. Keep its corners, colours and sizes. A new or changed value: name it and wait for his yes. Run `skills/figma-design/scripts/ds-check.py` before posting. Post only on PASS.
- "Hypertask" design rules mean app.hypertask.ai only. Not hypertask.app, yeoux.net or crolab.org: those pages keep their own style.
- Desktop and mobile share one design language. Layout may differ. One platform per ticket and per image: desktop and Android get separate tickets and keyframes.
- One Figma file for our apps. One page per ticket, named "<ID> <short what>". Newest worked page on top.
- Every design proposal on a ticket carries a Figma frame link and a keyframe image attached to the same comment. Never describe only. Dress the real app.
- Design QA compares live to the Figma frame. One screenshot pair per theme the app has. Pass or fail per brief item. Any mismatch, purple, sparkle, or corner, colour or size not in that app's own code goes back to Bugs. The builder never passes its own design QA.
- Impeccable skill set is allowed and recommended: critique, audit, polish, distill, clarify, harden, adapt, layout, typeset. The app's style guide is its brief. Style-changing commands (bolder, overdrive, colorize, delight, redesign) need his ticket asking. Results still land in Figma and app code.
- Start from his real screenshots. Subtract before adding. Every UI, page, card, reply or ticket: run `skills/reduce-first/`.
- Show design work as a screencast2.com image link in chat. Make it with `sc2-upload <png>`.
- yeoux.net report pages show data, KPIs and bars only. Labels 1 to 4 words, no prose. No words in chips or boxes. Method goes in one closed Data block. Read the dataviz skill before building. Big-number KPI tiles on top, then bars. Pace is a signed number.
