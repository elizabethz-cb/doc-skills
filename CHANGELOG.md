# Changelog

One line per release. Say what changed, and whether a template or customer-facing rule was approved (by whom, when) or is still a draft.

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
