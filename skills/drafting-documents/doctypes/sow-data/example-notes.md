# Example input for a data project SOW (already redacted, fictional)

## Kickoff call, 2026-10-05
Attendees: PERSON_001 (head of BI, CUSTOMER_001), PERSON_002 (data engineer, CUSTOMER_001), PERSON_003 (data architect, us)
- CUSTOMER_001 reports on sales and stock from an on-premises reporting database and Qlik scripts. Project name: "Sales Insight".
- Goal: a data lake on AWS that feeds the existing dashboards. Today everything runs on-premises.
- Sources: the ERP (SOURCE_001) and the CRM (SOURCE_002).

## Design call, 2026-10-19
- ERP tables are extracted in full once a day. CRM data is extracted incrementally every hour.
- Business logic comes from the existing Qlik scripts, which PERSON_002 will share.
- Querying with SQL from the BI tool through a connector.
- Use case A: daily sales report matches the current report to the cent. Use case B: stock levels refresh within 2 hours.
- Data volume: about 40 million rows today, expected to double in two years.
- Hyper-Care: 2 weeks. Support: 4 weeks. Answer to change requests within 5 business days.
- Milestone shares were not agreed. Budget: not discussed. AWS cost estimate still to be made.
- The customer asked whether data must stay in one country. No answer yet.
