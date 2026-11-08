# docs-skills

**New here? Read `START-HERE.md`: a checklist from unzip to first real document.**

A Claude Code plugin for customer documents: four skills that do the work, and six commands that run them for you. Everything is plain files: no servers, no Docker, no database.

**Skills** (Claude uses them when you ask, in Claude Code or chat):

| Skill | What it does |
| --- | --- |
| `redacting-customer-files` | **Optional.** Replaces names, IPs, domains, account numbers, emails and keys with placeholders. You run it in a terminal. |
| `drafting-documents` | Reads the notes, writes a draft, fills the Word template, and lists the open questions. SOW and assessment are included; you add more by adding a folder. |
| `drawing-diagrams` | Writes a draw.io (`.drawio`) architecture or flow diagram from notes, laid out automatically. At summary level it blocks detail you should not show a customer. |
| `learning-from-accepted-documents` | Compares a draft with its accepted final version and proposes short, generic lessons for you to approve. |

**Commands** (Claude Code only, they run only when you type them; details in section 16):

| Command | Run it in | What it does |
| --- | --- | --- |
| `/docs-skills:draft` | an engagement folder | First version of a document plus a summary diagram. |
| `/docs-skills:update` | an engagement folder | Next numbered version after new files arrive. |
| `/docs-skills:learn` | an engagement folder | Proposes lessons from an accepted final. |
| `/docs-skills:apply-lessons` | the plugin repo | Adds the approved lessons to a document type's `lessons.md`. |
| `/docs-skills:add-doctype` | the plugin repo | Builds a new document type from a Word template. |
| `/docs-skills:update-template` | the plugin repo | Swaps in a new Word template for an existing type. |

You need Python 3 and `pip install python-docx`. Pillow (`pip install pillow`) is needed only for the diagram preview image.

## 1. Customer data and your Claude plan

Redaction is **optional** in this pack: nothing requires it. Know the trade-off, though: a personal Claude subscription is not covered by your company's data protection, so check your organisation's policy and your customer contracts before putting customer material into it. If you want customer values replaced first, use the `redacting-customer-files` skill (section 4). Whatever you decide, never commit customer material to this repo: it is shared with colleagues.

## 2. Install

**Claude Code (plugin, one command per person):**
```
/plugin marketplace add <your-github-user>/docs-skills
/plugin install docs-skills@docs-skills-marketplace
```
To try it without installing, start Claude Code with `claude --plugin-dir <path to this repo>`. Copying the four skill folders into `.claude/skills/` of a project (or `~/.claude/skills/`) also works, but then you get the skills only: the six commands need the plugin.

**Amazon Quick:** the four skills (not the commands) can be added as skills there. See `AMAZON-QUICK.md`.

**Chat (claude.ai):** open Customize > Skills, add a skill, and upload a zip made by `python tools/package.py` (the skill folder zipped, with the folder name at the top; one zip per skill, for example `drafting-documents.zip`). Turn on "Code execution and file creation" in Settings. Chat cannot reach your laptop, so you upload the notes you want it to use. The six commands are not in the zips.

*Not yet tested here: the plugin install and the chat upload. If either complains, check the current Claude Code plugin docs and the skill upload rules (folder name must match the skill name, `SKILL.md` must exist).*

## 3. Daily use

**In Claude Code**, with the commands (section 16):

```
# 1. Make an engagement folder with input/ (copies of the notes, never originals) and output/ (empty).
#    (Optional: redact first, see section 4.)
# 2. Start Claude Code in that folder and run:
/docs-skills:draft SOW "Acme Ltd"
# 3. Review the Word file and the open questions in output/. Send the questions to the customer.
# 4. Edit the Word file, add new files to input/, then run /docs-skills:update for the next version.
# 5. When the document is accepted, run /docs-skills:learn, then /docs-skills:apply-lessons (section 14).
```

**In chat**, or without the commands, ask directly with the notes available: *"Use the drafting-documents skill to draft a SOW from these notes."*

**Optional redaction commands** (in your own terminal):
```
python skills/redacting-customer-files/scripts/redact.py run ~/private/acme --engagement acme --names names.txt --out ~/engagements/acme/notes
python skills/redacting-customer-files/scripts/redact.py restore acme-sow-v2.docx --engagement acme --out ~/final
```

`names.txt` example (companies and people cannot be found by patterns, so list them):
```
customer: Example Corp Ltd | Example Corp
person: Dana Levi | Dana
project: Project Lighthouse
term: ex-*          # every word starting with ex-, each gets its own placeholder
```

## 4. Optional: what redaction does and does not do

Replaces: emails, IPv4 addresses and ranges, domains and host names, AWS account numbers, ARNs, access keys, secret keys (when labelled), phone numbers, and everything in `names.txt`. The same value always gets the same placeholder.

Handles text files and `.docx`. It **skips and lists** anything else, refuses a `.docx` with comments, and refuses one with images unless you pass `--allow-images`. It clears author properties in `.docx`. After redacting a `.docx` it **re-scans every part of the file**, including tracked changes, text boxes, footnotes and file properties, and refuses the file if anything sensitive-looking is left. So accept all tracked changes before redacting.

Limits, so you know what to check by eye:
- It cannot know a name that is not in `names.txt`. The summary lists capitalised words still in the text, but it will miss some.
- No IPv6. No text inside images, PDFs or spreadsheets.
- It may replace version numbers that look like IP addresses.

## 5. Add a document type (about an hour)

A document type is one folder in `skills/drafting-documents/doctypes/`. You do not change any script.

1. **Copy** an existing folder, for example `assessment`, and name it after the new type (`handover`).
2. **Edit `fields.json`:** the `name` (same as the folder), and the fields Claude must fill in. A field is `text`, a `list` of text, or a `table` with columns. Add `forbidden_patterns` if the document must not contain certain details (the SOW blocks instance types and IP addresses).
3. **Edit the template:** open `template.docx` in Word and put placeholders where the content goes:
   - `{{name}}` for a text field
   - `{{list:name}}` alone in a paragraph (for example a bullet) for a list; the paragraph repeats for each item
   - `{{table.column}}` in the cells of **one** row of a table; that row repeats for each row
4. **Write `rules.md`** (what the document is for, the detail level, one wrong and one right example) and an empty `lessons.md`.
5. **Write `example-notes.md` and `example-draft.json`:** fictional, with placeholders instead of real names.
6. **Check it:** `python skills/drafting-documents/scripts/fill.py check skills/drafting-documents/doctypes/handover`. Each message says what to fix. When it prints OK, the template, fields and example all match.
7. **Try it** on a fictional engagement, look at the Word file, and run `python tests/smoke.py`.

**Shortcut:** from the plugin repo, run `/docs-skills:add-doctype <type name> <path to template.docx>`. Claude reads the blank template (you confirm it holds no customer data), proposes the fields and placeholders for your approval, puts the placeholders in a copy, writes the other files and runs the checks above. You review the result in Word. Not yet tried in a real session.

**Replacing the template of an existing type:** from the plugin repo, run `/docs-skills:update-template <type> <path to new template.docx>`. It stops if the type's folder has uncommitted changes (so the old template stays in git), proposes how the placeholders map to the existing fields for your approval, updates `fields.json` and the example, and runs the checks. Documents already drafted keep the old layout, and renaming or removing a field stops old `draft.json` files from building. Not yet tried in a real session.

Tips: type each placeholder in one go (Word sometimes splits text into pieces, which loses formatting inside that paragraph), and keep fonts and headings the way your company wants them, because the tool only fills text.

## 6. Improve it over time

See `IMPROVING.md`: a five-minute note after each real document, and a monthly tidy-up. Lessons go in `doctypes/<type>/lessons.md`, which Claude reads on every run. `/docs-skills:learn` and `/docs-skills:apply-lessons` do the two steps (section 14).

## 7. Folder map

```
.claude-plugin/              plugin and marketplace files
shared/folder-rules.md       the folder rules for the engagement commands, written once
skills/
  redacting-customer-files/  SKILL.md, scripts/redact.py
  drafting-documents/        SKILL.md, shared/rules-common.md, scripts/fill.py
    doctypes/<type>/           template.docx, fields.json, rules.md, lessons.md, example-*
                               (sow and assessment ship with the pack; one folder per type)
  drawing-diagrams/          SKILL.md, spec-format.md, rules.md, scripts/diagram.py, example-spec.json, example.drawio
  learning-from-accepted-documents/  SKILL.md, scripts/compare.py
  draft/ update/ learn/      the engagement commands (SKILL.md only)
  apply-lessons/ add-doctype/ update-template/   the plugin-repo commands (SKILL.md only)
examples/                    a fictional original and a names.txt to try redaction
tools/                       lint_skills.py (authoring rules), package.py (zips for chat)
tests/smoke.py               checks redaction, restore, document types, the detail guard, the learning helper and the lint
CHANGELOG.md                 one line per release, with approvals
START-HERE.md                definition of done and the steps to get there
```

The templates here are **starter templates**. Replace `template.docx` with your company's and update `fields.json` to match.

## 8. Commands

```
python skills/drafting-documents/scripts/fill.py check <doctype-folder>
python skills/drafting-documents/scripts/fill.py build <doctype-folder> <draft.json> <out.docx> [--allow-detail]
python skills/redacting-customer-files/scripts/redact.py run <file-or-folder> --engagement <name> [--names names.txt] --out <folder> [--allow-images]
python skills/redacting-customer-files/scripts/redact.py restore <file-or-folder> --engagement <name> --out <folder>
python skills/drawing-diagrams/scripts/diagram.py build <spec.json> <out.drawio> [--png preview.png] [--allow-detail]
python skills/drawing-diagrams/scripts/diagram.py check <spec.json>
python tools/lint_skills.py          # checks names, descriptions and size of every skill
python tools/package.py              # makes dist/<skill>.zip for chat upload (the six commands are left out)
python tests/smoke.py
```
Each script also has `--help`. The `/docs-skills:...` commands are in section 16.

## 9. Sharing it with colleagues

Keep **one plugin with many skills**. A new skill is a new folder under `skills/`, not a new package.

| For | How |
| --- | --- |
| Colleagues using Claude Code | They add your GitHub repo as a plugin marketplace once (section 2) and install the plugin. They need read access to the repo. Third-party marketplaces do not auto-update by default, so each person either turns on auto-update for the marketplace (in `/plugin`, Marketplaces tab) or runs `claude plugin marketplace update docs-skills-marketplace`, then `claude plugin update docs-skills@docs-skills-marketplace`, then `/reload-plugins` in the session. |
| Colleagues using chat | Run `python tools/package.py`, attach the zips in `dist/` to a GitHub Release (or put them on a shared drive). Each person uploads the zip in Customize > Skills. On personal accounts there is no sharing, so they re-upload to update. |

**Releasing a new or changed skill (5 steps):**
1. Add or edit the folder in `skills/<name>/` (the folder name and the `name:` in `SKILL.md` must be identical, lowercase with hyphens).
2. Run `python tests/smoke.py`. It runs the skill lint and the other checks.
3. Raise `version` in `.claude-plugin/plugin.json` on every release (0.1.0 to 0.1.1 for a wording fix, 0.2.0 for a new rule or document type, 1.0.0 for a change that breaks old drafts) and add a line to `CHANGELOG.md`. Claude Code compares the version string, not the content: push without raising it and colleagues keep the old copy.
4. Commit and push. For chat users, run `python tools/package.py` and attach the new zips to a release.
5. Tell colleagues what changed in one line.

*Plugin commands and settings change between Claude Code versions. If an update does not arrive, run `claude plugin validate .` here and check the current plugin docs. If you ever add a version to the plugin entry in `marketplace.json`, keep it identical to `plugin.json`.*

## 10. Authoring rules this pack follows

- A skill's name and description are all Claude sees until the skill is used, so descriptions say what the skill does and when to use it, in the third person.
- `SKILL.md` stays short (under 500 lines). Detail lives in other files that it points to: rules, templates and examples.
- One folder per skill, name identical to the folder.
- A command you invoke by name is a skill with `disable-model-invocation: true`, so Claude never loads it on its own. The lint leaves these out of the always-loaded count, and `tools/package.py` leaves them out of the chat zips.
- `tools/lint_skills.py` checks these rules, and `tests/smoke.py` runs it.

## 11. Where each rule belongs (four layers)

Skills are only one of four layers. Put each rule in the layer where it applies, and only there. A rule written in two places costs tokens twice and drifts apart.

| Layer | Question | Where it lives |
| --- | --- | --- |
| 1. Context | Who are we? Company, language, tone | `CLAUDE.md` in the engagement folder (Claude Code), or Project instructions (chat) |
| 2. Global preferences | How should answers look everywhere? | Your Claude preferences or settings |
| 3. Project | What are we working on? | One folder or one Claude Project per engagement, holding the redacted notes and what is known so far |
| 4. Skills | How is this kind of task done? | This repo |

Inside this repo: a rule for every document goes in `shared/rules-common.md`, a rule for one document type goes in that type's `rules.md`, and a one-off lesson goes in `lessons.md`.

## 12. Keeping it cheap

Claude sees only each skill's name and description until it uses the skill. The rest costs tokens only when needed. This pack keeps it that way:

- **Narrow descriptions.** Each says what the skill does and when to use it, and nothing that another skill could match. Skills with overlapping descriptions fire together and load twice. `tools/lint_skills.py` warns when two descriptions overlap.
- **One place per rule.** No copy of a rule in two files.
- **The rule, not the explanation.** "No more than two em dashes" instead of a paragraph about why. Claude already knows the reason.
- **Do not read what is not needed.** The skill reads `example-draft.json` but not `example-notes.md`.
- **Keep `lessons.md` short.** It is read on every run. The lint warns above 40 lines.
- **Measure after each change.** `python tools/lint_skills.py` prints rough estimates (about 4 characters per token): what is always loaded, and what one run reads for each document type. In Claude Code, `/cost` shows real usage for before and after comparisons.

Current estimates: about 350 tokens always loaded for the four skills (the six commands add nothing, because they load only when you type them), about 3,200 tokens for a SOW run and 2,700 for an assessment run.

## 13. Draft and approved

Two kinds of content, with different rules:

| Content | Needs approval? | Why |
| --- | --- | --- |
| `template.docx` and any fixed legal or commercial wording | **Yes**, by whoever owns it in your organisation | It is the company's voice and commitments. |
| `rules.md` for customer-facing documents (especially the detail level of a SOW) | **Yes**, by a senior reviewer | It decides what the customer sees. |
| `lessons.md`, prompt wording, `shared/rules-common.md` | No, review after the fact | Working instructions that improve with use. |

- **Use the organisation's approved template** as `template.docx` and keep fixed legal and commercial text as plain text in the template, never in a field, so Claude cannot change it. The starter templates in this repo are **not approved**: replace them.
- **Record approvals** in `CHANGELOG.md`: what changed, "approved by NAME on DATE" or "draft".
- **Keep draft work off the branch colleagues install from.** Work on a branch, merge when approved.
- **Promote a draft document type** when it has been used on two or three real engagements, someone senior has reviewed the output, no redaction misses were found, and the time per document is known.
- Keep the repo private and in a company-controlled place if the templates are internal documents. Check your policy first.

## 14. Learning from accepted documents

Skills do not learn by themselves. People improve them, and this loop makes that quick and safe:

1. The document is accepted (by the customer or internally). If it has tracked changes, accept them first.
2. In the engagement folder, run `/docs-skills:learn <type> <accepted final>` (or ask Claude to use `learning-from-accepted-documents` with the draft and the final). `compare.py` prints only what changed, so Claude does not need to read both documents.
3. Claude ignores customer-specific facts and proposes up to three short, generic lessons. **Read each one**: lessons are shared with everyone who installs the plugin, so they must not contain names, places, numbers or amounts from the documents. The command saves the approved ones to `output/lessons-proposed.md`.
   Then, in the plugin repo, run `/docs-skills:apply-lessons <type> <path to lessons-proposed.md>`. It adds them to that document type's `lessons.md`.
4. Run `python tests/smoke.py`. It checks that no lesson contains an email, IP address, domain, account number, key or placeholder. It cannot catch a company or person name, so your reading in step 3 matters.
5. Raise the version, add a `CHANGELOG.md` line, push.
6. Once a lesson has repeated three times, move it into `rules.md`. For a customer-facing document that is an approval step (section 13).

What it never does: edit `rules.md`, templates or `fields.json`, or save anything without your approval.

## 15. Diagrams

The `drawing-diagrams` skill makes a draw.io file from your notes. Claude writes a small spec (boxes, groups, arrows), and `diagram.py` checks it, lays it out and writes the `.drawio` file, so nobody writes coordinates or XML.

`/docs-skills:draft` draws a summary diagram for you. To draw one on its own:

1. Ask Claude: *"Use the drawing-diagrams skill to draw the target architecture from these notes."*
2. Open `diagram.drawio` at app.diagrams.net or in the draw.io desktop app. Adjust boxes and arrows by hand if you want.
3. Export a PNG from draw.io and put it in the Word document.

- **Levels.** A diagram for a SOW is `summary`: business-level boxes only. The script rejects instance types, IP addresses and ranges, resource counts, account numbers, subnets and availability zones, and more than 15 boxes. A design document can use `detailed`. This is the same rule the SOW follows, so a diagram cannot give away what the SOW keeps out.
- **Spec format and rules:** `skills/drawing-diagrams/spec-format.md` and `rules.md`. A working example is `example-spec.json` and its result `example.drawio`.
- **Limits.** It creates new diagrams only and does not edit existing draw.io files. The preview PNG is a rough drawing made by the script, not what draw.io shows. Arrows are routed by draw.io when it opens the file, so some may overlap and need a drag. The tests check the file's structure (unique ids, arrows point at real boxes, boxes sit inside their groups, no overlaps), but **how the file looks inside draw.io has not been checked here**. AWS icon names (`icon`) are optional and unverified: an empty box means the name is wrong. Putting the picture into the Word template automatically is not built yet.

## 16. Commands

Six commands run the skills for you. Claude Code only (plugin install or `--plugin-dir`), not chat. Each runs only when you type it, so it adds nothing to what Claude loads every session. All start with `/docs-skills:`.

**Engagement commands.** Make a folder with `input/` (copies of the customer files, never originals) and `output/` (empty), start Claude Code in it, and run:

```
/docs-skills:draft SOW "Acme Ltd"                  # v1 of the document and a summary diagram
/docs-skills:update SOW acme-sow-v1-edited.docx    # next version after you add files to input/
/docs-skills:learn SOW acme-sow-final.docx         # lessons from the accepted final
```

| Command | Uses | Writes to `output/` |
| --- | --- | --- |
| `draft <type> <customer>` | `drafting-documents`, `drawing-diagrams` | `<type>-v1.json`, `<type>-v1.docx`, `diagram.drawio`, `diagram-preview.png` |
| `update <type> <edited file>` | `drafting-documents` | the next unused `<type>-v<N>.json` and `.docx` |
| `learn <type> <accepted final>` | `learning-from-accepted-documents` | `lessons-proposed.md`, only lessons you approve |

All three first read `shared/folder-rules.md`, the one place the folder rules are written. They stop if `input/` or `output/` is missing, and ask you to confirm `input/` holds copies. To change a rule, edit that file only. They never write to the plugin.

**Plugin-repo commands.** Start Claude Code in the plugin repo and run:

```
/docs-skills:apply-lessons SOW C:\engagements\acme\output\lessons-proposed.md
/docs-skills:add-doctype handover C:\Templates\handover.docx
/docs-skills:update-template sow C:\Templates\new-sow.docx
```

| Command | What it does |
| --- | --- |
| `apply-lessons <type> <path to lessons-proposed.md>` | Second step of learning. Checks the lessons are generic, skips repeats, adds the rest to `doctypes/<type>/lessons.md`, runs the smoke test. |
| `add-doctype <name> <path to template.docx>` | Section 5 shortcut. You confirm the template holds no customer data, approve the proposed fields and placeholders, and Claude builds the type's folder and runs the checks. |
| `update-template <type> <path to new template.docx>` | Replaces a type's template. Stops if the type's folder has uncommitted changes, proposes how placeholders map to existing fields, updates `fields.json` and the example, runs the checks. Old drafts keep the old layout, and renaming or removing a field stops old `draft.json` files from building. |

None of these three commits or pushes. Each ends by telling you to review `git diff`, add a CHANGELOG line, raise the version, commit and push.

*None of the six has been tried in a real Claude Code session yet. If one does not appear or run, check `claude plugin validate .` and the current plugin docs.*
