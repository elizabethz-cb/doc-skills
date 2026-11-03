# Notes for Claude when working on this repo

- This repo holds skills only. No real customer data ever goes in it. Examples are fictional.
- Never open, read or run the redaction script on original customer files. The user does that.
- A document type is a folder under skills/drafting-documents/doctypes/. Do not change the scripts to add one.
- Before finishing any change run: python tests/smoke.py
- Keep rules short. Prefer deleting a rule to adding one. Lessons go in lessons.md.
- No Claude attribution in commit messages.
