---
name: building-decks
description: Builds branded slide decks (.pptx) from meeting notes with the company PowerPoint template, marking missing facts as red to-dos. Use when the user asks for a presentation, slides or a deck. Not for Word documents.
---

# Building decks from notes

This skill turns meeting notes into a branded `.pptx`. Each deck type is a folder under `decktypes/` next to this file: `template.potx`, `fields.json` (layout and icon names), `rules.md`, `icons/`. `scripts/fill_deck.py` draws the slides, so no coordinates or XML are written by hand.

## Before you start

- Find the deck type: list the folders in `decktypes/`. If the user did not say which one, ask.
- Redaction is optional. If the user wants customer values replaced first, point them to the `redacting-customer-files` skill.

## Steps

1. Read `lessons.md`, then the type's `rules.md` and `fields.json`.
2. List the files you will read and ask the user to confirm the list. One confirmation only.
3. Read the files. Note the dates: the latest dated source wins when sources disagree. Never invent facts, customers, numbers or prices. What the notes do not settle becomes a `[bracketed]` to-do. Never copy credentials.
4. Plan one message per slide and vary the slide kinds: not every section on bullets. Write `deck.json` (kinds below). Put speaker notes in `notes`, never on the slide.
5. Build from the folder where this skill is installed:

   ```
   python scripts/fill_deck.py build decktypes/<type> <path>/deck.json <path>/deck-v1.pptx
   ```

   - Fix any problem it prints and run it again. A "may not fit" warning means shorten the text.
   - If `python-pptx` is missing, run `pip install python-pptx`.
   - If you cannot run the script, give the user the outline as text and say plainly that the deck was not built.
6. Check the result: render the slides to images if you can (PowerPoint or LibreOffice) and look at every slide for overflow and overlap. The script lists every red to-do.
7. Tell the user, briefly: which files you used, the assumptions you made, the to-dos as a short table, and where the `.pptx` is.
8. Lessons come from the accepted deck, through the `learning-from-accepted-documents` skill. Do not invent lessons.

## Slide kinds

| kind | fields |
| --- | --- |
| `title` | `title`, `subtitle`, `aws` (`true` puts the Amazon arrow under the title; needs `icons/amazon_arrow.png` in the deck type, an image the user supplies) |
| `closing` | `title`, `subtitle` |
| `section` | `kicker` ("Section 01"), `title` |
| `agenda` | `title`, `items` (1 to 5) |
| `bullets` | `title`, `bullets` (1 to 8) |
| `two_column` | `title`, `left`, `right` |
| `cards` | `title`, `cards` (2 to 3): `icon`, `heading`, `items` (`{"label", "text"}`) |
| `process` | `title`, `steps` (1 to 3): `activity`, `outputs` |
| `stats` | `title`, `stats` (2 to 3): `value`, `label`; optional `detail` (lines) |
| `table` | `title`, `columns` (2 to 7), `rows` (1 to 7): a list of cells, or `{"cells": [...], "total": true}` (highlighted) or `{"cells": [...], "extra": true}` (a detached row below the table); `bold_columns` (column names); `footnotes` (up to 3) |
| `cases` | `title`, `cases` (2 to 3): `customer`, `challenge`, `solution`, `outcome` |
| `timeline` | `title`, `programme`, `start` (`2027-01`, a quarter's first month), `months` (multiple of 3, default 24), `phases` (up to 6): `name`, `start`, `end`; `milestones` (up to 3): `label`, `date` |

Any slide, card, step, stat, case, phase or milestone can carry `"todo": true`. A list item can be `{"text": "...", "todo": true}` (also a step's `outputs`). On a stat, `todo` marks the value only. In `bullets` and `two_column`, a line can be `{"text": "...", "heading": true}` (bold, no bullet) or `{"text": "...", "bold": true}`. Icon names are in `fields.json`.

## House style

- Never touch, recolour or move the logo or the cloud art: they live in the template's layouts.
- Cards navy and rounded with no outline; white text, muted blue-grey for secondary text, teal accent, orange only for milestones; Arial; titles left-aligned. No edge stripes, no underline bars.
- Only company-owned or code-generated images. No stock or web images, no third-party logos unless the user supplies them.
- Red highlight means an open to-do for the team. Anything in `[brackets]`, or marked `todo`, gets it. Leave none unmarked.

## Updating a deck

When the user brings new notes or an edited deck: read both, produce the next version (`deck-v2.pptx`, and so on) and never overwrite an earlier one. The deck is rebuilt from `deck.json`, so layout changes made by hand in PowerPoint are lost: say so. Say what changed and which to-dos are now answered.

## Adding a deck type

Copy a folder in `decktypes/`, replace `template.potx`, edit `fields.json` (layout names must match the template's) and `rules.md`, then run `python scripts/fill_deck.py check decktypes/<new-type>`. It tells you what does not match.
