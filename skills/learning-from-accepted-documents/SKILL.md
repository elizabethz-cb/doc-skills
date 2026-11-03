---
name: learning-from-accepted-documents
description: Compares a drafted document with its accepted final version and proposes a few short, generic lessons for that document type. Use when the user says a document was accepted or finalised and wants the skills to learn from what people changed. Not for drafting or redacting.
---

# Learning from an accepted document

Skills do not learn by themselves. This skill turns what people changed into short lessons, and the user approves each one.

## Safety
- Lessons are shared with every colleague who installs the plugin, so they must be **generic**. No customer, company or person names, places, numbers, dates, amounts or placeholders such as CUSTOMER_001. Rewrite as a pattern ("the customer's go-live date") or skip it. If a change is specific to one customer, ignore it.
- The user reads each lesson before it is saved.
- Write only to `skills/drafting-documents/doctypes/<type>/lessons.md`. Never edit `rules.md`, templates or `fields.json`; suggest those changes to the user as text.
- If the final has tracked changes, the user accepts them first.

## Steps
1. Ask for the document type, the draft (the Word file Claude produced) and the accepted final.
2. Run `python scripts/compare.py <draft.docx> <final.docx>` from this skill's folder and read its output instead of both documents.
3. Sort the changes. Ignore customer-specific facts. Keep patterns: detail added or cut, sections added, removed or reordered, wording or tone, assumptions that were wrong, open questions that were missing.
4. Read the type's `lessons.md` and `rules.md`. Skip what they already say. If a lesson is already in `lessons.md`, tell the user it has repeated and suggest moving it to `rules.md` (their decision).
5. Propose at most three lessons: one or two lines each, generic, starting with today's date, with a one-line reason. Add only the ones the user accepts. In chat, give the text to paste instead.
6. Remind the user to run `python tests/smoke.py` (it checks lessons for leaked customer values), raise the version, add a CHANGELOG line and push.
7. If nothing generic changed, say so and add nothing.
