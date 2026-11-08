---
name: update-template
description: Swaps in a new Word template for an existing document type and realigns its fields and example. Use when the user invokes /docs-skills:update-template.
argument-hint: <existing type> <path to new template .docx>
disable-model-invocation: true
---

# Update a document type's template

Arguments: `$ARGUMENTS` (existing type, then the path to the new template). If either is missing, ask.

1. Check this folder is the plugin repo and `skills/drafting-documents/doctypes/<type>/` exists. Run `git status --short` on that folder: if it has uncommitted changes, stop, so the old template stays recoverable.
2. Ask me to confirm the file is a blank template with no customer data. If I say no, stop and do not open it.
3. Read the new template with python-docx and the type's `fields.json`. Propose where each existing field's placeholder goes, and any fields to add, rename or remove. Say that removing or renaming a field stops old `draft.json` files from building. Wait for my approval.
4. Replace `template.docx` with a copy of the new file, adding the placeholders to the copy only, one run per placeholder, keeping styles. The original stays as it is.
5. Update `fields.json` and `example-draft.json` to match. Suggest `rules.md` changes as text and make them only if I agree. Do not edit `lessons.md`.
6. Run `python skills/drafting-documents/scripts/fill.py check skills/drafting-documents/doctypes/<type>` until it says OK, then `python tests/smoke.py`. Change no script.
7. Tell me to open the built example in Word and check fonts, tables and layout, then to add a CHANGELOG line saying who approved the template or that it is a draft, raise the version, commit and push. Do not do those yourself.
