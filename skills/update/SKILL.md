---
name: update
description: Produces the next numbered version of a document, its diagram, or both, after new files or manual edits. Use when the user invokes /docs-skills:update.
argument-hint: <document type> <edited .docx or .drawio in output/>
disable-model-invocation: true
---

# Update workflow

Arguments: `$ARGUMENTS` (document type, then the name of my edited file, a `.docx` or a `.drawio`). If either is missing, ask.

1. Read `${CLAUDE_PLUGIN_ROOT}/shared/folder-rules.md` and follow it first.
2. Check that the edited file is in `output/`. Ask what to update: the document, the diagram or both, and what is wrong or should change. My answer is a source, like the notes. Skip what I already said. List the files in `input/` and wait for me to confirm which to use. That is the one confirmation the `drafting-documents` skill asks for.
3. Document: use the `drafting-documents` skill, in its "Updating a document" mode, with the confirmed files, my edited file and my answer. Save the next version as `output/<type>-v<N>.json` and `output/<type>-v<N>.docx`.
4. Diagram: use the `drawing-diagrams` skill at summary level, with the latest `output/diagram*.json` spec, my edited `.drawio` if I gave one (read its boxes and arrows) and my answer. That skill cannot edit a draw.io file, so write a new spec and rebuild; say that positions and styling I set by hand are lost. Save the next version as `output/diagram-v<N>.json`, `.drawio` and `-preview.png`. The first diagram counts as v1.
5. N is the first number not yet used in `output/`. Never overwrite an earlier file.
6. Tell me what changed, and which open questions are now answered.
