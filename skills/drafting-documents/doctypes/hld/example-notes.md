# Example input for a High-Level Design (already redacted, fictional)

## Kickoff call, 2026-11-02
Attendees: PERSON_001 (CFO, CUSTOMER_001), PERSON_002 (IT manager, CUSTOMER_001), PERSON_003 (solution architect, us)
- CUSTOMER_001 runs sales and stock reports from an on-premises database and Qlik scripts. Project name: "Sales Insight".
- Reports are often late: managers get the daily sales report around 11:00. They want it by 08:00.
- Finance and operations see different numbers for the same month. PERSON_001 wants "one version of the truth".
- The on-premises server is out of support next year.
- Sources: the ERP (SOURCE_001) and the CRM (SOURCE_002).

## Design call, 2026-11-16
- Proposed: a data platform on AWS. Data lands in Amazon S3, is processed with AWS Glue, and is queried with Amazon Athena from the existing BI tool.
- Access through the customer's existing company login (single sign-on). Data encrypted. Daily backups.
- Phases agreed in principle: design (2 weeks), build (6 weeks), testing (2 weeks), go-live and Hyper-Care (2 weeks).
- New dashboards are not part of this project. Migrating historical data older than 5 years is not included.
- Cloud cost estimate not made yet. Project effort to be priced in the SOW.
- The business logic is in the Qlik scripts. PERSON_002 says only one person knows them well.
- The customer asked whether data must stay in one country. No answer yet.
- Next: PERSON_001 to approve the HLD by 2026-12-01, then we send the SOW.
