---
name: deck
description: Builds a first-version slide deck for a customer from the notes in input/. Use when the user invokes /docs-skills:deck.
argument-hint: <deck type> <customer name>
disable-model-invocation: true
---

# Deck workflow

Arguments: `$ARGUMENTS` (deck type, then customer name). If either is missing, ask.

1. Read `${CLAUDE_PLUGIN_ROOT}/shared/folder-rules.md` and follow it first.
2. List the files in `input/` and wait for me to confirm which to use. That is the one confirmation the `building-decks` skill asks for.
3. Use the `building-decks` skill for that type and customer, with the confirmed files. Save the deck as `output/deck-v1.json` and `output/deck-v1.pptx`.
4. Finish with: the files used, the assumptions made, and the red to-dos as a short table (slide, what is missing, what you assume meanwhile).
