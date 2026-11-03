# How the skills get better over time

The pack improves through small notes after real use, not through big rewrites.

## After each real document (5 minutes)

1. Note what you changed by hand in the Word file, and what Claude got wrong or missed.
2. Use the `learning-from-accepted-documents` skill with the draft and the accepted final . Keep only the lessons you agree with.
3. Put each lesson in `skills/drafting-documents/doctypes/<type>/lessons.md`, one or two lines with the date. Claude reads this file on every run.

## Once a month

- Move lessons that came up three times into `rules.md`, and delete them from `lessons.md`.
- Delete lessons that no longer apply.
- If the company template changed, update `template.docx`, `fields.json` and `example-draft.json`, then run `python skills/drafting-documents/scripts/fill.py check skills/drafting-documents/doctypes/<type>`.
- Run `python tests/smoke.py`. Raise the version in `.claude-plugin/plugin.json`, commit with a message that says what you learned, and push so colleagues get the update.

## Keep it small

- A new rule needs a reason. If it fixes one odd case, put it in `lessons.md`, not in `rules.md`.
- Prefer shortening a rule to adding one.
- Write down how long each document took. The goal is a draft in minutes and a final in under a few hours.

## Every few months: a cost audit

Run `python tools/lint_skills.py` and read the numbers. Then ask Claude, with the skills installed:

1. "If I ask for a SOW, which skills and files load, and is each one needed for this task?"
2. "Is any rule repeated across my skill files? List the duplicates."
3. "Take the longest rules file and compress it without losing a rule. Show before and after."

Claude's own token counts are approximate. Trust the direction (what loads, what repeats), not the exact numbers, and confirm with `/cost` in Claude Code.
