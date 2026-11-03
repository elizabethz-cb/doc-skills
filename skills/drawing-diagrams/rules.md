# Rules for diagrams

- **Match the level to the document.** A diagram in a SOW or any customer-facing document is `summary`: boxes for business-level parts (web tier, database, file service), environments and who connects to what. A design document may use `detailed`.
- Do not show what the SOW rules forbid: instance types and sizes, resource counts, IP addresses and network ranges, account numbers, subnets and availability zones. The script rejects these at summary level.
- **At most about 12 boxes.** If it needs more, it belongs in a design document.
- Label boxes with what they do ("Web tier"), not with product names, unless the customer asked for the product by name.
- Label an arrow only when it adds meaning ("HTTPS", "Secure connection").
- Use the customer placeholder or name exactly as in the notes. Never invent components that are not in the notes. If the notes are unclear, leave the box out and tell the user, or add an open question.
- Group by boundary: cloud, environment, network, customer data centre.
