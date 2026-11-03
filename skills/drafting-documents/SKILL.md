---
name: drafting-documents
description: Drafts customer documents (statement of work, assessment, other types in its doctypes folder) as Word files from meeting notes and customer files, using the company templates, and lists the open questions. Use when the user asks to draft, update or review a SOW, an assessment or a similar document from notes. Does not redact files.
---

# Drafting documents from notes

This skill turns meeting notes into a Word document. Each document type is a folder under `doctypes/` next to this file, with its own template, rules, fields and example.

## Before you start

- Find the document type. List the folders in `doctypes/`. If the user did not say which one, ask.
- Redaction is optional. If the user wants customer values replaced first, point them to the `redacting-customer-files` skill.

## Steps

1. Read `shared/rules-common.md`, then for the chosen type `doctypes/<type>/rules.md`, `lessons.md` and `fields.json`. Look at `example-draft.json` to see the expected shape and level of detail. Do not read `example-notes.md`; it is for people.
2. List the files you will read and ask the user to confirm the list. One confirmation only.
3. Read the files. Note the dates, because the latest dated source wins when sources disagree.
4. Write `draft.json` with exactly the fields in `fields.json`, as valid JSON. Whatever the notes do not settle becomes an open question, never a guess. Save it next to the notes, for example in an `output/` folder.
5. Build the Word file from the folder where this skill is installed:

   ```
   python scripts/fill.py build doctypes/<type> <path>/draft.json <path>/<type>-v1.docx
   ```

   - If it prints problems, fix `draft.json` and run it again. The "too much detail" check is on purpose. Do not use `--allow-detail` unless the user asks for it.
   - If `python-docx` is missing, run `pip install python-docx`.
   - If you cannot run the script at all, give the user the draft as text plus the open questions, and say plainly that the Word file was not built.
6. Tell the user, briefly: which files you used, the assumptions you made, the open questions as a short table, and where the Word file is.
7. Lessons come from what people change in the accepted document. When the document is accepted, the `learning-from-accepted-documents` skill proposes them. Do not invent lessons from a draft nobody has reviewed.

## Updating a document

When the user brings new notes or an edited version: read both, produce the next version (`<type>-v2.docx`, and so on) and never overwrite an earlier one. Say what changed and which open questions are now answered.

## Adding a new document type

Copy an existing folder in `doctypes/`, edit `fields.json`, `rules.md`, the template and the example, then run `python scripts/fill.py check doctypes/<new-type>`. It tells you what does not match. The README has the full steps.
