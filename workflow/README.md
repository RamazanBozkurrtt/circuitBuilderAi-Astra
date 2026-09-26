# Product V1 workflow

This directory holds process contracts, not electrical design. The controlled
checkpoint is `state/project_state.json`; the shared Board A/B signal-class
contract is `state/board_to_board_interface.json`. Actual findings go under
`validation/findings/`. Phase outputs remain in the normal `docs/`,
`hardware/` and `validation/` trees.

Install once: `python -m pip install -r workflow/requirements.txt`.

Run the current phase's machine checks:

```text
python workflow/gates/run.py
```

Preview a specific phase or a permitted transition without changing state:

```text
python workflow/gates/run.py --phase R6
python workflow/gates/run.py --next-phase R1
```

Exit code 0 means machine `PASS`, 2 means `BLOCKED`, and 1 means `FAIL`.
`PASS` means only that configured machine checks passed; the human/engineering
gate remains `NOT_EVALUATED`. A phase changes only after its human gate is
recorded and `state/project_state.json` is deliberately updated. The runner
does not advance phases or edit files.

The ERC, DRC, interface, pin and BOM hooks currently return
`NOT_AVAILABLE`. When one is required by a phase, the machine result is
`BLOCKED` until a real adapter and scoped verification artifact exist. Do not
replace `NOT_AVAILABLE` with a synthetic PASS.

The finding schema allows `accepted` and `deferred` statuses for review
history. A finding with `blocking: true` stops progression from its
`blocks_from_phase` onward until its status is `resolved`; acceptance or
deferral alone does not clear it. Each unresolved blocker must also appear in
the `open_blockers` state checkpoint with the same phase. This keeps later
blockers visible without blocking earlier verification work. The seven
product OPEN decisions are tracked separately from findings.
