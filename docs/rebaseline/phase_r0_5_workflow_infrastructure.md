# Phase R0.5 — engineering workflow infrastructure

## 1. Infrastructure created

R0.5 adds a small workflow layer under [`workflow/`](../../workflow/README.md): one engineering-finding JSON Schema, a common Python gate runner, concise Product V1 phase definitions, five rule layers, and two templates. It uses `jsonschema` for finding validation and otherwise stays file-based. No electrical, component, schematic, PCB or KiCad work was performed.

## 2. Repository structure

```text
workflow/
  schemas/engineering_finding.schema.json
  gates/run.py
  rules/{evidence_policy,electrical_worst_case,schematic_implementation,pcb_layout,manufacturing}.md
  templates/{engineering_finding.template.json,phase_gate_report.template.md}
  phase_definitions/product_v1.json
state/{project_state,board_to_board_interface}.json
validation/findings/                 actual Product V1 findings; currently none
validation/r0_5/                     reproducible validation and results
hardware/product_v1/
  board_a_controller_afe/            reserved; no KiCad files
  board_b_power_amp/                 reserved; no KiCad files
hardware/kicad/                      preserved legacy project
```

Historical phase documents and legacy hardware remain where they were. Board A and Board B are separate future implementation directories, but one Product V1 state and one controlled board-to-board interface bind them.

## 3. Finding model

[The finding schema](../../workflow/schemas/engineering_finding.schema.json) requires ID, title, severity, category, board, phase, component/interface, description, evidence, calculation/reference, status, blocking flag, discovery time, resolver and resolution. Severity is `info`, `warning`, `error` or `blocking`; status is `open`, `accepted`, `resolved` or `deferred`. Board scope is Board A, Board B, interface or system. A resolved record must name its resolver and resolution.

An unresolved record with `blocking=true` blocks machine progression from its declared `blocks_from_phase` onward, even if accepted or deferred. R1 added that phase field so later blockers can be tracked without preventing earlier verification. Missing/invalid finding data or a mismatch with the state checkpoint fails the gate. Markdown remains the human explanation; structured records provide machine-readable blocker status. There were no actual R0.5 engineering findings. The seven OPEN product decisions are tracked separately, without inventing failure evidence.

## 4. State/checkpoint model

[`project_state.json`](../../state/project_state.json) records the Product V1 two-board baseline, current R0.5 phase, previous R0 PASS, Board A/B/interface status, open blockers, seven open decisions, authoritative product source, current contract, current KiCad projects, latest validation and last verified commit. `last_verified_commit` is `null` because the rebaseline/workflow working tree has not been recorded as a verified commit. `current_kicad_projects` is empty; legacy KiCad is excluded.

[`board_to_board_interface.json`](../../state/board_to_board_interface.json) is a **controlled placeholder**, sourced to the product document §5.1. It records the proposed 5 V/return, audio, I²C, MUTE/FAULT/PGOOD and optional service/MCLK signal classes. Connector part, pin assignment, voltage domains and contact counts remain `null`. Proposed directions come from the product document; they are not schematic-level compatibility claims. Board A and Board B must be reviewed as one interface before its status changes.

## 5. Gate architecture

[`run.py`](../../workflow/gates/run.py) evaluates the selected phase definition and returns machine `PASS`, `BLOCKED` or `FAIL`. It checks required phase inputs/outputs/current contracts, phase-scoped unresolved structured findings against the state checkpoint, and the Product V1 two-board/interface identity. It checks allowed next phases without changing project state. Exit codes are 0, 2 and 1 respectively.

ERC, DRC, hierarchical interface audit, pin audit and BOM validation are explicit future hooks. Each currently reports `NOT_AVAILABLE`; if required by a phase, the aggregate gate is `BLOCKED`. The runner always reports the human/engineering gate as `NOT_EVALUATED`; a machine PASS cannot approve a phase or advance state by itself. Future adapters must run real tools against scoped Product V1 artifacts and retain verifiable outputs.

## 6. Phase roadmap

[`product_v1.json`](../../workflow/phase_definitions/product_v1.json) defines objective, inputs, outputs, machine gates, human gate and allowed successor for each phase.

| Phase | Scope |
| --- | --- |
| R0; R0.5 | Two-board rebaseline; workflow infrastructure |
| R1; R2 | Requirements/open decisions; component verification |
| R3; R4 | Architecture/interface freeze; schematic readiness |
| R5; R6 | Separate KiCad schematics; schematic verification |
| R7; R8; R9 | PCB constraints/stackup; placement plan; placement |
| R10; R11; R12 | Critical routing; full routing; PCB verification |
| R13; R14 | DFM/DFA; manufacturing package |

The R1–R14 artifact paths are planned contracts, not claims those artifacts exist or that later phases are authorized.

## 7. Product V1 Board A/B handling

Board A is Controller + Audio AFE; Board B is Power + Stereo Class-D. The two reserved directories contain only README markers. Product V1 has no KiCad project. The former `hardware/kicad/` project remains clearly labelled legacy and is not included in `current_kicad_projects`. Interface findings can use the `interface` board scope, preventing cross-board faults from being hidden in one board's report.

## 8. Context/token-efficiency strategy

[`AGENTS.md`](../../AGENTS.md) now directs agents to read project state, inspect open blocking findings, read the active phase definition, use Graphify when available for navigation, then inspect only necessary authoritative sources. The source document is still mandatory for product architecture decisions, and manufacturer evidence remains authoritative for electrical claims. State and graph navigation do not substitute for source review.

## 9. Validation results

[R0.5 validation](../../validation/r0_5_workflow_infrastructure_validation.md) passed JSON/schema checks, phase/path coherence, baseline machine gate, blocker and resolution fixtures, invalid-finding failure, transition checks, and absent-KiCad `NOT_AVAILABLE` behavior. The runner was executed after both required reports existed. No ERC/DRC was run or claimed.

## 10. Next phase recommendation

Request separate authorization for **R1 — Requirements / open decisions**. R1 should turn the product document's seven OPEN decisions into a traceable requirements register and identify which must close before component or schematic gates. R0.5 has not resolved any of those decisions.

**R0.5 gate:** The R0.5 engineering review confirmed that the seven product decisions remain open, both boards share one controlled interface placeholder, and no Product V1 KiCad work was introduced. The machine checks passed; their `NOT_EVALUATED` human field is intentional because the runner does not record review approval. No Product V1 electrical or KiCad gate is implied.

PHASE R0.5: PASS
