---
name: drawing-diagrams
description: Creates draw.io (diagrams.net) architecture and flow diagrams as .drawio files from notes or a short description, with a summary level that is safe for customer-facing documents. Use when the user asks for a diagram, architecture drawing or flow chart. Does not edit existing draw.io files.
---

# Drawing diagrams

Claude writes a small spec of boxes, groups and arrows. A script checks it, lays it out and writes the `.drawio` file, so no coordinates or XML are written by hand.

## Steps
1. Read `rules.md`. Read `spec-format.md` for the fields and `example-spec.json` for the shape.
2. Decide the level: `summary` for a SOW or other customer-facing document, `detailed` only for a design document. If unsure, use `summary`.
3. Take the components from the notes only. Do not add boxes the notes do not support. Ask about anything unclear.
4. Write `spec.json`, then run this from the folder where this skill is installed:

   ```
   python scripts/diagram.py build <path>/spec.json <path>/diagram.drawio --png <path>/preview.png
   ```
5. If it prints problems, fix the spec and run it again. Do not use `--allow-detail` unless the user asks for it.
6. Tell the user where the files are and how to use them: open `diagram.drawio` at app.diagrams.net or in the draw.io desktop app to adjust it, then export a PNG to put in the Word document. The preview image is only a rough check, not how draw.io draws it.
7. If a box shows up empty in draw.io, the `icon` name is wrong. Remove it or correct it.

If `Pillow` is missing the preview is skipped; the `.drawio` file is still written. If the script cannot run at all, give the user the spec as text and say the file was not built.
