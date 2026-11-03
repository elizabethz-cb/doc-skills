# Rules for every document type

1. **Never invent facts.** Every statement comes from the notes or the files, or it is written as an assumption.
2. **Unknown or unclear points become open questions**, not guesses. Each open question has an id (Q1, Q2, ...), a question in business wording that could be sent to the customer as it is, an impact (price, scope, schedule, design or risk), and what you assume until it is answered.
3. **When sources disagree**, the latest dated source wins. Raise the conflict as an open question and say which two sources disagree. Never silently pick one. When something was unclear earlier and a later source answers it, it is answered, not open.
4. **Use names, numbers and wording exactly as in the notes.** If the notes use placeholders such as CUSTOMER_001, keep them as written and never guess what is behind them.
5. **Never copy credentials** (keys, passwords, tokens) into a draft. If the notes contain any, leave them out and tell the user.
6. **Prices:** use only figures that appear in the notes. Never estimate prices from memory.
7. **Write in plain business language.** Short sentences. No filler. No marketing words.
8. **Output** is one JSON object (draft.json) with exactly the fields in fields.json. No text outside the JSON when writing the file.
9. **At the end**, show the user: the files you used, the assumptions you made, and the open questions as a short table.
10. **Read the document type's `lessons.md`** before you start. Lessons are added only after a document is accepted, by the learning skill.
