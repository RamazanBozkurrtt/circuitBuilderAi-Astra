## Context efficiency

Use the smallest context necessary for the task.

For repository discovery and dependency/navigation questions:
1. Use the Graphify MCP first.
2. Prefer `graphify_rank_files` or `query_graph` to identify relevant files.
3. Read only the files/sections returned as relevant.
4. Do not recursively scan or reread the repository unless Graphify is unavailable or insufficient.

Graphify is a navigation/indexing tool, not an electrical source of truth.

For electrical claims:
- locate the relevant source with Graphify when useful;
- then verify the claim from the exact authoritative manufacturer document/section.

Do not reread completed phase reports unless the active task explicitly depends on them.
Do not reread legacy hardware by default.
Do not spawn subagents unless explicitly requested.

Start each engineering task from:
`state/project_state.json`

Then read only the active findings and contracts required by that task.