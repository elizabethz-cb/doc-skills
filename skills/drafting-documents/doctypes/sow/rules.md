# Rules for a Statement of Work

**Purpose.** Agree what will be delivered, at what level, with which assumptions. The customer may show this document to other suppliers, so it must not contain the technical design.

**Keep it at business level.**
- Allowed: outcomes, service categories (compute, database, storage, networking, security, monitoring), environments (production, test), phases, deliverables, durations, responsibilities, assumptions, and prices stated in the notes.
- Not allowed: instance types and sizes, the number of servers or resources, network ranges and IP addresses, configuration values, software versions below the major version, account numbers, step-by-step procedures, tool-level detail.
- Technical detail belongs in the design document that is written after the SOW is agreed. If the notes contain detail, leave it out of the SOW and mention in the open questions only what affects price, scope or schedule.

Wrong level: "Migrate 14 servers to 2 x m5.large and a db.r6i.xlarge Multi-AZ database in subnet 10.0.0.0/16."
Right level: "Move the customer's web, application and database systems to AWS in a highly available setup, with separate production and test environments."

**Structure.** Follow the fields in fields.json. Objectives are outcomes, not tasks. "Out of scope" must list the things the customer is likely to assume are included (for example application changes, training beyond what is agreed, ongoing operations).

**Dates and money.** Where a date or price is not settled, write "To be confirmed".

**Length.** The whole document should read in about 10 minutes.
