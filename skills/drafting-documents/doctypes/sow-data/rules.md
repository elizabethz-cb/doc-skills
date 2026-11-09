# Rules for a data project Statement of Work

**Purpose.** The customer and AWS both read this document to approve a project run by the data team. It fixes the scope, the milestones, the tests that prove each milestone is done, the effort and the estimated AWS costs. It sits between a business SOW and a design document.

**Detail level: business and service level.**
- Allowed: AWS service names (S3, Glue, Athena, Lake Formation and so on), data sources, extraction modes (full, incremental), schedules such as "once a day", milestones, use cases with a definition of done, durations, hours, prices stated in the notes.
- Not allowed: instance types and sizes, the number of servers or resources, IP addresses and network ranges, account numbers, access keys, credentials, configuration values, step-by-step procedures. These belong in the design document written after approval. The check blocks the first four patterns and the keys.
- If the notes contain such detail, leave it out and mention it in an open question only when it affects price, scope or schedule.

Wrong level: "Extract the orders table to s3://bucket-1 using a Glue job on 10 G.1X workers, 2 x m5.large for the connector, from 10.1.2.3."
Right level: "Extract the orders table in full mode from the customer's ERP to the raw layer in S3 using AWS Glue. This will run once a day."

**Fixed wording.** The template holds the company text, the standard milestones, scope changes, design review, customer responsibilities and the payment note. Do not rewrite or work around it. Fill only the fields.

**Fields.**
- Lists with a definition of done (`extraction_dod`, `processing_dod`, `consumer_dod`, `deliverables`): one item per use case, written as "Use case name - done when ...". The done condition must be something a person can check.
- `extraction_plan`: one item per extraction: what, from where, to where, with which service, how often.
- Money, percentages, hours, weeks and days: use only figures in the notes. Otherwise write "To be confirmed". Write a total only when every figure above it is known.
- `milestone_share`: list the milestones in the template order that apply to this project. Percentages are shares of the total project.
- Cost tables: list only services the notes mention or clearly follow from the scope. Costs are estimates, so say so in `details` only if the notes do.
- `architecture_note` describes the diagram in one sentence. The user adds the diagram in Word.
- The Gantt table in the template is edited by hand in Word.

**Length.** Short items. No marketing words.
