# Start here

## Definition of done

- [ ] **1. It is a plugin I can use.** Installed in Claude Code, and I have drafted a real document with it.
- [ ] **2. I can add templates.** The organisation's approved SOW template is in, and a second document type (for example an assessment) is added from a folder, without changing any script.
- [ ] **3. It improves with approved documents.** I have run the learning loop on one accepted document, and the lessons it produced are in `lessons.md`.
- [ ] **4. A colleague can use it.** One colleague has installed it from the repo and drafted a document.

## Steps, in order

Rough time is for one person who has done none of this yet.

### Step 1. Get it running locally (30 minutes)
1. Unzip, and check you have Python 3 and `pip install python-docx`.
2. `python tests/smoke.py` should end with "All checks passed".
3. Create a **private** repo on GitHub (use the account that has access, or your clone and push will fail), push this folder to `main`. While it is only you, commit straight to `main`.

### Step 2. Load it as a plugin (30 minutes)
1. In this folder, start Claude Code with `claude --plugin-dir .` to load the plugin without installing it.
2. Check that the three skills are listed (`/skills`, or ask Claude which skills it has).
3. Try it: *"Use the drafting-documents skill to draft a SOW from skills/drafting-documents/doctypes/sow/example-notes.md"*. Open the Word file it produces.
4. If the plugin does not load, run `claude plugin validate .`, read what it says, and fix `.claude-plugin/plugin.json` and `marketplace.json` (put your name in both). This part is untested, so expect to adjust.

### Step 3. Put in the approved SOW template (half a day)
1. Get the approved Word template from your organisation.
2. Replace `skills/drafting-documents/doctypes/sow/template.docx` with it. Put placeholders where the content goes (README section 5, step 3): `{{name}}`, `{{list:name}}`, `{{table.column}}`. Keep fixed legal and commercial wording as plain text.
3. Edit `fields.json` and `rules.md` so they match the template and the level of detail your organisation allows.
4. `python skills/drafting-documents/scripts/fill.py check skills/drafting-documents/doctypes/sow` until it says OK, then build the example and look at the Word file.
5. Record in `CHANGELOG.md`: "SOW template approved by NAME on DATE", or "draft".

### Step 4. First real document (a few hours)
1. Draft a real SOW from real notes. Time it.
2. Edit the Word file as you normally would. Note what you had to change.

### Step 5. Add a second document type (one hour)
Follow README section 5. Copy `assessment` (or the type you need), rename it, edit `fields.json`, the template, `rules.md` and the example, then run `fill.py check` until it says OK. Put in the approved template when you have it.

### Step 6. First learning loop (30 minutes)
1. When the document from step 4 is accepted, accept any tracked changes in the final.
2. Ask Claude to use `learning-from-accepted-documents` with the draft and the final.
3. Read each proposed lesson. Keep only generic ones (no names, numbers, amounts). They go into `lessons.md`.
4. `python tests/smoke.py`, raise the version in `.claude-plugin/plugin.json`, add a `CHANGELOG.md` line, push.

### Step 7. One colleague (30 minutes)
Ask one colleague to add your repo as a marketplace and install the plugin (README section 2 and 9), draft a document, and tell you what was confusing. Fix that before inviting anyone else.

## What is not tested yet

- Installing the plugin from a marketplace, and updating it.
- Uploading the skills in chat.
- The learning skill on a real accepted document.
- Your real company template: placeholders, fonts, tables and layout.
- How the generated `.drawio` file looks when opened in draw.io (open `skills/drawing-diagrams/example.drawio` once and check it).

Each of these gets tested by the steps above. Fix what breaks, then update the README so the next person does not hit it.

## Decisions only you can make

- Where the repo lives (a company-controlled place if the templates are internal).
- Who approves the SOW template and its detail rules.
- Whether to use redaction for customer material (it is optional, see README section 1).
