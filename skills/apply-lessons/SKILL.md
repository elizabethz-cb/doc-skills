---
name: apply-lessons
description: Adds lessons approved in an engagement to this plugin's lessons file for a document type. Use when the user invokes /docs-skills:apply-lessons from the plugin repo.
argument-hint: <document type> <path to lessons-proposed.md>
disable-model-invocation: true
---

# Apply lessons workflow

Arguments: `$ARGUMENTS` (document type, then the path to `lessons-proposed.md`). If either is missing, ask.

1. Check that this folder is the plugin repo: `skills/drafting-documents/doctypes/<type>/lessons.md` must exist. If not, stop and tell me to run this from the plugin repo.
2. Read only the given file. Open nothing else from that engagement folder.
3. Each lesson must be generic, with no names, places, numbers or amounts. If one is not, show it to me and ask. Skip any lesson already in that type's `lessons.md` or `rules.md`, and say which.
4. Add the rest to `lessons.md` in its existing format. Change no other file.
5. Run `python tests/smoke.py` and show me the result. Fix only the lessons if it fails.
6. Tell me to check `git diff`, raise the version in `.claude-plugin/plugin.json`, add a CHANGELOG line, then commit and push. Do not do those yourself.
