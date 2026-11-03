# Diagram spec format

One JSON object. Keep labels short (a few words).

```json
{
  "title": "Target architecture",
  "level": "summary",
  "direction": "LR",
  "groups": [
    {"id": "aws", "label": "AWS", "kind": "cloud"},
    {"id": "prod", "label": "Production", "parent": "aws"}
  ],
  "nodes": [
    {"id": "users", "label": "Customers", "kind": "actor"},
    {"id": "web", "label": "Web tier", "kind": "compute", "group": "prod"}
  ],
  "edges": [
    {"from": "users", "to": "web", "label": "HTTPS"}
  ]
}
```

| Field | Values |
| --- | --- |
| `level` | `summary` (default, for customer-facing documents) or `detailed` |
| `direction` | `LR` left to right (default) or `TB` top to bottom |
| group `kind` | `environment` (default), `cloud`, `network`, `onprem` |
| group `parent` | id of another group, to nest groups |
| node `kind` | `service` (default), `compute`, `database`, `storage`, `network`, `security`, `actor`, `external` |
| node `group` | id of the group the node sits in |
| node `icon` | optional draw.io shape name, for example `mxgraph.aws4.ec2` (see below) |
| edge `from`, `to` | ids of nodes (or groups) |
| ids | lowercase letters, digits, `-` and `_`, starting with a letter |

**Layout.** The script places things from left to right (or top to bottom) following the arrows between nodes, and sizes the groups around what they contain. Connect nodes, not groups, when you want the layout to follow the flow. Arrows are routed by draw.io when the file is opened.

**Summary level** rejects instance types, IP addresses and network ranges, resource counts such as "2 x EC2", account numbers, and words such as subnet, availability zone and security group. It also rejects more than 15 nodes. `--allow-detail` switches this off.

**Icons.** `icon` passes a draw.io shape name through. The AWS shape names are not checked by this script: if a box shows up empty in draw.io, look the name up in draw.io's shape search and correct it. Without `icon`, nodes use plain coloured shapes, which always work.
