---
name: figma-design
description: How design agents use Figma for Valentin's apps. Connect through the claude.ai Figma connector, work only in the Yeo UX team, rebuild real captures, propose by cloning, keep one design system page per app, and hand frames plus keyframes to tickets. Use for any Figma mockup, wireframe, icon, design system or design hand-off.
---

# Figma for design agents

Learned by SF Design Lead on Multiprompt, 2026-10-26. Valentin approved this way of working.

## Connect
- Use the claude.ai Figma connector. Load tools with ToolSearch `select:mcp__claude_ai_Figma__use_figma,...`.
- If the tools are missing, restart the session once so claude.ai connectors load. Do not use mcp-remote (403) or a personal access token (401).
- Before the first `use_figma`, read `skill://figma/figma-use/SKILL.md` (ReadMcpResourceTool, server "claude.ai Figma"). Pass `skillNames: "resource:figma-use"` on every call.
- Create files only in the **Yeo UX** team (paid, planKey `team::653929828954513812`). Never Valentin Yeo's free team: it allows only one variable mode.
- Call `create_session` once per file and reuse the session id.
- Keep a ledger file of page and node ids next to your notes, so later calls never search blind.

## Structure each app file
- Pages: Reference captures, Foundations, Components, one page per platform (Desktop, Mobile), App icon, and a **design system page**.
- Design system page: colours as Figma variables (each names its code constant), type scale, spacing and corners, real components with properties and variants, and the rules in one paragraph. Runners build only from it.

## Work
1. **Capture first.** Rebuild the current screen from his screenshot (screencast2 link) and trace every value to code. Real app colours can differ from the code theme; sample the capture.
2. **Propose by cloning** the capture frame. Name it `... / PROPOSAL <what>`. Subtract before adding: "Everything needs to earn its place."
3. **Show options.** Give two to six variants side by side, plus your pick with a one-line reason.
4. **Screenshot every change** with `get_screenshot` and look at it before you show him. Fix clipping, overlap and colour emoji yourself.
5. **Keyframe.** Download the screenshots and stitch them into one PNG (Python PIL) for the ticket.

## Show Valentin
- He is often on his phone. Send the image with SendUserFile, and give the Figma link `https://www.figma.com/design/<fileKey>?node-id=<a-b>`. A link alone gets missed.
- If he is at the desktop, open the frame with `zsb navigate`.

## Hand off
- Post one ticket comment: Figma frame links, exact values (hex, dp or px, radius), what stays the same, and the keyframe attached with `--attach`.
- Record his yes on the ticket in his own words before builders start.
- Split approved work into build tickets, one per repo, under a parent ticket, with the app label.
- Superseded frames: delete them, so runners never build the wrong one.

## Gotchas
- `resize()` on an auto-layout frame fixes both axes. Set `primaryAxisSizingMode` or `counterAxisSizingMode` back to `AUTO` afterwards, or content overlaps.
- A frame with `clipsContent` hides children you position by hand. Turn it off on message columns.
- Some symbols (⏸ ⏰ ⚙ 🔒) render as colour emoji. Use plain glyphs.
- Short bubble text: set `textAutoResize` to `WIDTH_AND_HEIGHT`, then cap at the max width, so bubbles hug their text.
- The secrets-guard hook can block heredocs that write JSON or Python. Use the Write tool instead.
