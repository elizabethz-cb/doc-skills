---
name: add-doctype
description: Builds a new document type folder, with fields, rules and a fictional example, from a Word template file. Use when the user invokes /docs-skills:add-doctype.
argument-hint: <new type name> <path to template .docx>
disable-model-invocation: true
---

# Add a document type

Arguments: `$ARGUMENTS` (new type name, then the path to the template). If either is missing, ask. The name is lowercase letters, digits and hyphens.

1. Check this folder is the plugin repo (`skills/drafting-documents/doctypes/` exists) and `doctypes/<name>/` does not. Never overwrite an existing type.
2. Ask me to confirm the file is a blank template with no customer data. If I say no, stop and do not open it.
3. Read the template with python-docx (headings, paragraphs, tables). Propose the fields and where each placeholder goes, following "Add a document type" in the README. Keep fixed legal and commercial wording as plain text. Wait for my approval.
4. Copy the template to `doctypes/<name>/template.docx` and put the placeholders in the copy only, one run per placeholder, keeping styles. The original stays as it is.
5. Write `fields.json` (copy the shape of `doctypes/assessment/fields.json`). Ask me the document's purpose and detail level, then write `rules.md`. Add an empty `lessons.md` with the header used in the other types.
6. Write `example-notes.md` and `example-draft.json`, fictional, with placeholders instead of names.
7. Run `python skills/drafting-documents/scripts/fill.py check skills/drafting-documents/doctypes/<name>` until it says OK, then `python tests/smoke.py`. Change no script.
8. Tell me what to review (the template in Word, `rules.md`), then to add a CHANGELOG line saying who approved it or that it is a draft, raise the version, commit and push. Do not do those yourself.
