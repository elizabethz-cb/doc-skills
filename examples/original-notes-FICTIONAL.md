# Kickoff call, Example Corp Ltd, Project Lighthouse (FICTIONAL ORIGINAL, for testing redaction)

Date: 2026-09-02
Attendees: Yoav Cohen (CTO, Example Corp), Dana Levi (IT manager), Lior Barak (us)

- Example Corp Ltd runs freight tracking from two server rooms in Haifa. Portal: portal.examplecorp.example
- Network 10.40.0.0/16. Web servers 10.40.1.11 and 10.40.1.12. Office firewall 203.0.113.25.
- Servers: ex-web01.corp.examplecorp.example, ex-db01.corp.examplecorp.example, plus ex-app01 and ex-app02.
- Target AWS account 111122223333 in eu-central-1. Role arn:aws:iam::111122223333:role/ex-migration-admin
- Contact: Dana Levi, dana.levi@examplecorp.example, +972-50-555-0142. Escalation: yoav.cohen@examplecorp.example
- A test key was pasted in chat by mistake: AKIAIOSFODNN7EXAMPLE
  aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
- PostgreSQL 14.9 database, about 1.2 TB. Budget under USD 9,000 per month. Change freeze 2026-11-20 to 2027-01-05.
- Monitoring agent version 2.14.0.3 is installed everywhere.
