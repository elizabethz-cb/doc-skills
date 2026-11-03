---
name: learn
description: Turns an accepted final into a few approved lessons saved for review. Use when the user invokes /docs-skills:learn.
argument-hint: <document type> <accepted final in input/>
disable-model-invocation: true
---

# Learn workflow

Arguments: `$ARGUMENTS` (document type, then the name of the accepted final). If either is missing, ask.

1. Read `${CLAUDE_PLUGIN_ROOT}/shared/folder-rules.md` and follow it first.
2. Check that the accepted final is in `input/` and the original draft, `output/<type>-v1.docx`, exists. If not, stop and say which is missing.
3. Use the `learning-from-accepted-documents` skill on those two files. Propose up to three generic lessons, with no names, places, numbers or amounts from this customer, and wait for my approval.
4. Save only the approved lessons to `output/lessons-proposed.md`, not to the plugin's `lessons.md`. Skip that skill's closing reminders (smoke test, version, push). Tell me to paste the lessons into `doctypes/<type>/lessons.md` myself.
