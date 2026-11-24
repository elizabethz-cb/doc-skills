# Rules for a High-Level Design (HLD)

**Purpose.** Help the customer's managers, who are not technical, understand why the project matters, what it covers and how the solution works at a high level, so they can approve it. It comes before the SOW. Engineers get the detailed design later.

**Length: at most 5 pages.** Stay within the word and row limits in fields.json. If the content does not fit, cut the least important items. Do not shrink fonts or margins, and do not add sections. The architecture diagram takes about half a page.

**Detail level: business first.**
- Allowed: AWS service names in the components table, data sources, schedules such as "once a day", phases, durations, business measures, and prices stated in the notes.
- Not allowed: instance types and sizes, number of servers or resources, IP addresses and network ranges, account numbers, keys, configuration values and step-by-step procedures. These belong in the detailed design. The check blocks most of them.
- Explain each technical term the first time it appears, in a few words, or use a plain word instead.

Wrong level: "Glue jobs on G.1X workers write Parquet to S3 partitioned by date, queried by Athena through the JDBC connector."
Right level: "Every night the sales and stock data is collected in one secure place on AWS, cleaned, and made ready for the existing dashboards."

**Sections.**
- Executive summary: write it last. A manager who reads only this paragraph should know the problem, the proposal and the main benefit.
- Goals: each goal has a measure a manager can check. If the notes give no measure, write "To be confirmed" and raise an open question.
- Components: the business value column says what the business gets, not what the service does a second time.
- Security and operations: say what is protected and how it is checked, not the settings.
- Phases, costs: figures only from the notes, otherwise "To be confirmed". Costs are estimates; detailed pricing is in the SOW.
- Risks: business risks first (schedule, data quality, adoption), then technical ones. Each has a concrete mitigation.
- Next steps: each item says who acts or decides.
- Open questions: at most 5 in the document, the ones with the most impact. List the rest to the user only.
- `architecture_note` describes the diagram in one sentence. The user pastes the summary diagram in Word (use the drawing-diagrams skill at summary level) and removes the yellow marker.

**Tone.** Plain, confident and neutral. Short sentences. No marketing words, no blame.
