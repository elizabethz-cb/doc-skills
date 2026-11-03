# Example input for an assessment (already redacted, fictional)

## Assessment workshop, 2026-10-20
Attendees: PERSON_001 (IT manager, CUSTOMER_001), PERSON_002 (security officer, CUSTOMER_001), PERSON_003 (us)
- Systems run in two server rooms. Backups go to a network storage device once a night. Nobody has tested a restore this year.
- Administrators share two accounts for the database servers. Staff VPN uses multi-factor authentication, but remote access to servers does not.
- Monitoring covers only whether a server is up or down. There are no alerts for disk space or database performance. Customers usually notice outages first (PERSON_001).
- The firewall pair is active/passive and was last updated 18 months ago.
- Monthly infrastructure cost is not tracked per system.
- Load roughly doubles in the peak season (November to January) and the web site slows down.
