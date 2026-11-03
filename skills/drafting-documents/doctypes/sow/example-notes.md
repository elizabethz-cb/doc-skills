# Example input for a SOW (already redacted, fictional)

## Kickoff call, 2026-09-02
Attendees: PERSON_001 (CTO, CUSTOMER_001), PERSON_002 (IT manager, CUSTOMER_001), PERSON_003 (solutions architect, us)
- CUSTOMER_001 runs freight tracking and invoicing for about 300 business customers from two server rooms. Hardware leases end on 2027-03-31.
- Goal: move the web, application, database and batch systems and one Windows file server to AWS. Production plus one test environment.
- No application changes. Active Directory stays on-premises.
- Region: "Frankfurt is fine for us" (PERSON_001).
- Go-live: "end of Q4 2026".
- Disaster recovery is needed, details to follow.

## Technical workshop, 2026-09-16
- Change freeze from 2026-11-20 to 2027-01-05.
- Load roughly doubles in the peak season (November to January). A sixth application server may be needed then.
- The database includes about 300 GB of old archive data that may be dropped. PERSON_002 will check.
- The file server is used by finance and by warehouse scanners. The customer asks for our recommendation.
- Windows licences come through Software Assurance. PERSON_002 is not sure they can move.
- The security officer said some customer contracts may require data to stay in Israel. Details by email.

## Follow-up call, 2026-09-30
- Disaster recovery for production: at most 15 minutes of data loss, restored within 4 hours. Test environment: no recovery setup.
- The board wants production on AWS before 2026-12-15. PERSON_001 will talk to the board.
- Budget expectation: under USD 9,000 per month for AWS, production and test together. Approximate.
- Training: one half-day for the administrators. Support after go-live: 4 weeks.
- The test environment should run during working hours only.
