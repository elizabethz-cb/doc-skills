---
name: draft
description: Creates version 1 of a SOW or assessment and a summary architecture diagram from the files in input/. Use when the user invokes /docs-skills:draft.
argument-hint: <SOW|assessment> <customer name>
disable-model-invocation: true
---

# Draft workflow

Arguments: `$ARGUMENTS` (document type, then customer name). If either is missing, ask.

1. Read `${CLAUDE_PLUGIN_ROOT}/shared/folder-rules.md` and follow it first.
2. List the files in `input/` and wait for me to confirm which to use. That is the one confirmation the `drafting-documents` skill asks for.
3. Use the `drafting-documents` skill for that type and customer, with the confirmed files. Save the draft and the Word file as `output/<type>-v1.json` and `output/<type>-v1.docx`.
4. Use the `drawing-diagrams` skill to draw the target architecture at summary level. Save it as `output/diagram.drawio`, with the spec as `output/diagram.json` and the preview as `output/diagram-preview.png`.
5. Finish with: the files used, the assumptions made, and the open questions as a short table (id, question, impact, what you assume meanwhile).
