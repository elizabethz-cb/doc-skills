---
name: redacting-customer-files
description: Guides the user through replacing company names, people, IP addresses, domains, account numbers, emails and keys in customer files with placeholders. Use when the user explicitly asks to redact, anonymise or sanitise files, or says the files are not redacted yet. Not for drafting. Claude never runs the script on original files.
---

# Redacting customer files

This step is optional. Use it when you want customer values replaced before they reach Claude. Personal Claude subscriptions are not covered by company data protection, and redaction reduces what Claude sees.

## Rules for Claude

- **Never open, read or ask for the original files.** Never run `redact.py` on them. The user runs it.
- If the user has already pasted original data into the conversation, say so plainly, do not repeat the data, and suggest they redact first and start a new conversation.

## What to tell the user

1. Put the original files in a private folder that is **outside** the project and outside any folder used with Claude.
2. Create `names.txt` for this customer. Names of companies and people cannot be found by patterns, so they must be listed:

   ```
   customer: Example Corp Ltd | Example Corp
   person: Dana Levi | Dana
   project: Project Lighthouse
   term: ex-*
   ```
3. Run it in a terminal (the script is in the `scripts` folder of this skill):

   ```
   python redact.py run <originals-folder> --engagement <name> --names names.txt --out <redacted-folder>
   ```
4. Read the output. The summary shows how many values of each kind were replaced and lists capitalised words that are still in the text. Those may be names, places or products: add them to `names.txt` and run again.
5. **Read the redacted files yourself** before using them with Claude. Automatic redaction misses things.
6. Use only the redacted folder with Claude. The mapping that allows restoring real values is stored in `~/.docs-skills/mappings/` and must stay out of the project.
7. For the finished document, the user can restore real values locally with `python redact.py restore <file> --engagement <name> --out <folder>`. The restored file contains real data and stays away from AI tools.

## What it does and does not do

Handles text files and `.docx`. Anything else is skipped and listed. A `.docx` with comments or images is refused (images only with `--allow-images`). It does not read text inside images, PDFs or spreadsheets, and it may replace version numbers that look like IP addresses.
