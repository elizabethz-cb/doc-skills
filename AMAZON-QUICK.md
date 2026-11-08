# Using the skills in Amazon Quick (desktop)

Amazon Quick takes **skills**: a folder with a `SKILL.md` at its root. It has no plugins or marketplaces, so you **cannot install this plugin** there. What you can add are the four skills. The six `/docs-skills:...` commands stay in Claude Code.

Based on the Amazon Quick user guide ([Skills](https://docs.aws.amazon.com/quick/latest/userguide/skills-desktop.html), [usage limits](https://docs.aws.amazon.com/quick/latest/userguide/usage-limits-desktop.html)). **Not yet tried here.** Steps marked *(unverified)* are not in those pages.

## What works and what does not

| In this repo | In Quick |
| --- | --- |
| `drafting-documents`, `drawing-diagrams`, `learning-from-accepted-documents`, `redacting-customer-files` | Add each as a skill (below). Each folder is self-contained. |
| `draft`, `update`, `learn`, `apply-lessons`, `add-doctype`, `update-template` | Not available. They need the Claude Code plugin (`/docs-skills:` names, `${CLAUDE_PLUGIN_ROOT}`). Do not add them. |
| Python scripts (`fill.py`, `diagram.py`, `compare.py`) | Quick lists "code execution" as a built-in skill, but the pages do not say how it works. If it cannot run the scripts, the skills fall back to giving you the draft as text and say the Word file was not built *(unverified)*. |

## Before you start

- A skill is limited to 6 MB and a reference file to 50 MB. The four folders are well under that (about 350 KB for `drafting-documents`, less for the rest).
- Quick is a different service from Claude: check your organisation's data policy before putting customer material in it (README section 1).
- Add the folders as they are. Open `skills/drafting-documents/doctypes/` first and check it holds only the document types you want colleagues to get.

## Add a skill

1. In Amazon Quick, open **Customize > Skills** and choose **Create**.
2. Choose **From folder**, and select one skill folder, for example `skills/drafting-documents`. The folder must have `SKILL.md` at its root.
3. Review and edit the skill, then save it. It appears under **My skills**.
4. Repeat for `drawing-diagrams` and `learning-from-accepted-documents`. Add `redacting-customer-files` only if you want it; Claude must never be given the original files to redact, so keep running the script yourself.
5. **Publish** each skill. Changes are saved to a draft and do not affect how the skill runs until you publish. Publishing does not share it.

Prefer **From folder** over a zip: the pages do not say whether a zip needs the folder name at the top *(unverified)*. If you use one, `python tools/package.py` makes `dist/<skill>.zip` the same way as for chat.

## Share with colleagues

1. Open the skill's detail panel and choose **Share**.
2. Pick specific people or groups, or **Share with all** for the whole account. Your Quick admin may require approval to share.
3. Colleagues find it in **Add to Quick** under **Shared with me**. They are viewers: they cannot edit or re-share, and they stay in sync with your published version.

## Use it

Mention the skill by name in chat, or let Quick pick it:

```
Use the drafting-documents skill to draft a SOW from these notes.
```

Upload the notes in the chat, since the engagement folders and `input/` and `output/` rules belong to the Claude Code commands and do not apply here.

## Update it

After a change in this repo (a new lesson, template or rule), add the changed skill folder again and publish. Whether re-adding replaces the skill or makes a copy is not documented *(unverified)*: edit the existing skill if it lets you, and check the version colleagues see. Quick does not read this repo's version number or CHANGELOG, so tell colleagues what changed.

## Test it once

1. Add `drafting-documents` and ask for a SOW from the fictional notes in `skills/drafting-documents/doctypes/sow/example-notes.md`.
2. Check that you get a draft, open questions and, ideally, a Word file. If you get text only, Quick could not run `fill.py`; the skill still works as a drafting aid.
3. Share with one colleague and ask them to run the same request.

## Not verified

- How Quick runs code, and whether it can run `python-docx` or create `.docx` files.
- Which operating systems the desktop app runs on.
- Which `SKILL.md` frontmatter fields Quick reads. The skills use `name` and `description`, the standard pair.
- Whether a zip works, and how to replace a skill with a newer folder.
