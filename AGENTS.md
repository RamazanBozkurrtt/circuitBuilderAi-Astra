# AGENTS.md

## Product V1 authority

- At task start: read `state/project_state.json`; inspect unresolved blocking records in `validation/findings/`; read the active contract in `workflow/phase_definitions/product_v1.json`; use Graphify for navigation if available; then open only the authoritative source files needed for the task. The gate runner is `workflow/gates/run.py`. Do not reread the entire repository by default.
- Product V1 is one ANC system made from **Board A (Controller + Audio AFE)** and **Board B (Power + Stereo Class-D)**, with four analog microphone inputs and two secondary speaker outputs.
- Read `docs/product/ANC_B2B_Custom_PCB_2_Kart_Mimari_Tasarim_Dokumani_v1.0.docx` completely before product architecture decisions. It is the primary **product-level** source. Its two-board architecture is frozen; named devices are targets, not schematic-level approvals. Preserve every decision it leaves open.
- `docs/rebaseline/phase_r0_b2b_two_board_rebaseline.md` records the migration and the current gate. Do not start a later phase without explicit authorization.
- The ADAU1978 / ADSP-21569 / TAS6424E-Q1 four-speaker design, `hardware/kicad/` project, and its Phase 0–4 records are **legacy reference only**. Preserve their history. Their rails, circuits, interface values, clock/TDM topology, connector pinout, sheets, and validation gates do not carry into Product V1.

## Evidence and phase discipline

- Product decisions define intent; verify every frozen device/interface choice independently against official manufacturer datasheets, manuals, errata, and applicable reference material before schematic entry. Official device limits outrank product preferences.
- Never invent electrical values, pins, modes, timing, sequencing, or requirements. Mark claims `CONFIRMED`, `PROVISIONAL`, `UNKNOWN`, or `CONFLICTING`; cite evidence and state the resolution path. Do not turn an open item into a decision silently.
- Treat Board A and Board B as one product with a versioned, controlled electrical and mechanical interface contract. Verify power/return currents, logic levels, audio/clock timing, control and fault polarity, startup/shutdown, disconnected-board behavior, and connector constraints. Optional signals remain optional until justified.
- Verify exact parts, packages, symbols, supplies, analog interfaces, reset/boot/debug, clocking, serial audio, external networks, thermal/load limits, and availability before schematic entry. Track ANC latency, compute/memory feasibility, microphone roles, acoustic safety, and worst-case power/tolerance margins.
- Work only inside the authorized phase. R0 is documentation only: no KiCad changes, schematic, or PCB layout. Resolve or formally accept schematic-entry blockers before a later authorized schematic phase. Run ERC after schematic edits and DRC after PCB edits; record meaningful waivers. A clean check is not proof of electrical or product correctness.

## Repository and reporting

- Keep future Product V1 KiCad work separate under `hardware/product_v1/board_a_controller_afe/` and `hardware/product_v1/board_b_power_amp/`, with a shared interface contract. Label the existing `hardware/kicad/` project as legacy in navigation; do not overwrite it. Keep product sources in `docs/product/`, rebaseline records in `docs/rebaseline/`, manufacturer documents in `datasheets/`, and validation under `validation/`.
- Use Graphify for navigation when a valid graph exists; verify conclusions against source files. At task end report changes, evidence checked, unknowns, blockers, and the phase gate. Stop at the gate.
