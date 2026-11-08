# Changelog

One line per release. Say what changed, and whether a template or customer-facing rule was approved (by whom, when) or is still a draft.

## 0.9.0 (draft)
- /docs-skills:update now asks what to update (document, diagram or both) and can rebuild the diagram as a numbered version from your edited .drawio or your instructions. /docs-skills:draft also saves the diagram spec. Not yet tried in a real Claude Code session.

## 0.8.0 (draft)
- New command /docs-skills:update-template, run from the plugin repo: swaps in a new Word template for an existing document type and realigns its fields and example, with your approval before anything changes. Not yet tried in a real Claude Code session.

## 0.7.0 (draft)
- New command /docs-skills:add-doctype, run from the plugin repo: builds a new document type folder from a Word template file, with your approval before the template is changed. Not yet tried in a real Claude Code session.

## 0.6.0 (draft)
- New command /docs-skills:apply-lessons, run from the plugin repo: adds the lessons approved by /docs-skills:learn to a document type's lessons.md and runs the smoke test. Not yet tried in a real Claude Code session.

## 0.5.0 (draft)
- New commands /docs-skills:draft, :update and :learn (skills that run only when invoked) for an engagement folder with input/ and output/. The folder rules live in shared/folder-rules.md. Not yet tried in a real Claude Code session.

## 0.4.0 (draft)
- New skill drawing-diagrams: spec to .drawio with automatic layout, summary level that blocks low-level detail (same rule as the SOW), optional preview image. Not yet checked inside draw.io.

## 0.3.0 (draft)
- Redaction is optional: the drafting and learning skills no longer require redacted files. The redaction skill and its checks remain available. Lessons are still checked for customer-looking values, because they are shared with colleagues.

## 0.2.0 (draft)
- New skill learning-from-accepted-documents (compare a draft with the accepted final, propose generic lessons).
- Redaction now re-scans Word files after redacting and refuses any that still hold sensitive-looking text in tracked changes, text boxes, footnotes or file properties. Before this, text inside tracked changes was not redacted.
- Tests check lessons files for customer-looking values.

## 0.1.0 (draft)
- First version: redacting-customer-files and drafting-documents with starter SOW and assessment templates. Templates are NOT approved: replace them with the organisation's approved versions.
