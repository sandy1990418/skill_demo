---
name: meeting-notes
description: Transforms raw meeting notes or transcripts into a strictly-formatted summary with three sections — Decisions, Action items, and Open questions. Use whenever the user provides meeting notes, a transcript, a standup recap, or asks to "summarize a meeting".
---

# Meeting Notes Skill

## When to use
Activate this skill whenever the user pastes raw meeting notes, a transcript,
standup chatter, or asks you to "summarize a meeting" / "turn this into notes".

## Output format (STRICT — do not deviate)

Produce EXACTLY three sections in this order, with these exact headers:

### Decisions
- `[D1]` one-line decision
- `[D2]` one-line decision

### Action items
| ID | Task | Owner | Due |
|----|------|-------|-----|
| A1 | ...  | @name | YYYY-MM-DD or TBD |

### Open questions
- `[Q1]` question — needs answer from @name

## Rules

1. IDs are `D1, D2, ...`, `A1, A2, ...`, `Q1, Q2, ...`, starting at 1.
2. Owners are ALWAYS prefixed with `@`, even if the raw text uses a bare name.
3. If no due date is mentioned, use the literal string `TBD` — never guess a date.
4. A "decision" is something that was concluded. An "action item" is a commitment
   to do future work. Never put a commitment in Decisions.
5. If a section has no entries, write `(none)` as the only line under the header.
6. Output ONLY the three sections. No preamble ("Here is your summary..."), no
   closing remarks, no extra commentary.
