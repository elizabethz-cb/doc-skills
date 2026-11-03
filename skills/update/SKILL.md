---
name: update
description: Produces the next numbered version of a document after new customer files arrive. Use when the user invokes /docs-skills:update.
argument-hint: <document type> <edited file in output/>
disable-model-invocation: true
---

# Update workflow

Arguments: `$ARGUMENTS` (document type, then the name of my edited file). If either is missing, ask.

1. Read `${CLAUDE_PLUGIN_ROOT}/shared/folder-rules.md` and follow it first.
2. Check that the edited file is in `output/`. List the files in `input/` and wait for me to confirm which to use. That is the one confirmation the `drafting-documents` skill asks for.
3. Use the `drafting-documents` skill, in its "Updating a document" mode, with the confirmed files and my edited file. Save the next version as `output/<type>-v<N>.json` and `output/<type>-v<N>.docx`, where N is the first number not yet used in `output/`. Never overwrite an earlier version.
4. Tell me what changed and which open questions are now answered.
