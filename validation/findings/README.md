# Product V1 engineering findings

Place one JSON file per actual finding here, validated against
`workflow/schemas/engineering_finding.schema.json`. Use a stable ID and cite
the source and location. Markdown reports may explain the finding, but the JSON
record carries its machine-readable blocking status.

The R0 product document's seven OPEN decisions are tracked in
`state/project_state.json`. R1 added only unresolved items that can block a
specified later phase, each with evidence and a closure criterion. A finding
with `blocking: true` blocks from its `blocks_from_phase` onward; keep the
state checkpoint synchronized. Product decisions remain open even when an
earlier provisional engineering bound clears one related finding.
