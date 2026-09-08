# AGENTS.md

## 1. Mission

* Repository: `circuitBuilderAi-Astra`.
* Goal: develop a production-oriented 4-input / 4-output Active Noise Control controller.
* Scope includes hardware, DSP, firmware, validation, and engineering documentation.
* Primary PCB tool: KiCad.
* Primary repository-graph tool: Graphify when a valid graph exists.
* The design is clean-sheet.
* Previous CircuitBuilderAI projects are not authoritative.
* Correctness, traceability, electrical safety, manufacturability, and explicit uncertainty handling outrank speed.
* Do not optimize for creating files quickly.
* Optimize for defensible engineering decisions.

## 2. Current State

* Phase 0 is complete.
* Current gate: `PHASE 0: PASS`.
* Phase 0 permits component and datasheet verification.
* Phase 0 does not permit schematic design.
* The Phase 0 requirements freeze contains unresolved items.
* At Phase 0 completion, 44 requirements were classified UNKNOWN.
* Treat schematic-entry blockers as real blockers.
* The next expected phase is `PHASE 1 — Component and Datasheet Verification`.
* Do not skip phases.
* Do not begin a later phase unless explicitly authorized.

## 3. Intended Architecture

* Intended path: `4 × analog microphones → low-noise AFE → 4-channel ADC → TDM4 → DSP → TDM4 → 4-channel digital-input Class-D amplifier → 4 × speakers`.
* Candidate microphone: Infineon IM73A135.
* Candidate ADC: Analog Devices ADAU1978.
* Candidate DSP: Analog Devices ADSP-21569.
* Candidate amplifier: Texas Instruments TAS6424E-Q1.
* These parts remain candidates until verified.
* Candidate status is not approval.

## 4. Core Engineering Rules

* Never invent an electrical value, pin function, package mapping, register value, timing requirement, sequencing rule, or operating mode.
* Never invent a missing requirement.
* Never silently resolve a contradiction.
* Never convert UNKNOWN into CONFIRMED without evidence.
* Never use plausibility as a substitute for evidence.
* If evidence is insufficient, report `UNKNOWN`.
* If sources disagree, report `CONFLICTING`.
* If a requirement is tentative, report `PROVISIONAL`.
* Use `CONFIRMED` only when authoritative evidence or an approved project decision supports it.

## 5. Evidence Priority

* Prefer official manufacturer datasheets first.
* Then official hardware reference manuals.
* Then official application notes.
* Then official evaluation-board schematics and design files.
* Then official reference designs.
* Then approved project requirement documents.
* Then independently verified engineering references.
* Blogs, forums, distributor text, search snippets, and AI summaries are not authoritative electrical evidence.
* Secondary sources may be used only to locate stronger primary sources.
* Prefer the newest applicable official document revision.
* Record revision and exact section/page for critical claims when practical.

## 6. Repository Authority

* Read relevant repository documents before making design decisions.
* Inspect `MASTER_SPEC.md` when present.
* Inspect `docs/phases/phase_0_requirements_freeze.md`.
* Inspect the active phase document, relevant decisions, validation reports, datasheets, and KiCad files.
* Do not assume an old document is current merely because it exists.
* If repository documents conflict, identify the conflict explicitly.
* Do not silently choose the convenient value.
* Confirmed project requirements outrank provisional design preferences.
* Official device limits outrank project preferences.
* If a requested design violates an official limit, flag it immediately.

## 7. Graphify Usage

* Graphify is a repository navigation and impact-analysis aid.
* Graphify is not an engineering source of truth.
* A graph may be unavailable in early phases.
* Graph unavailability must not block legitimate datasheet or documentation work.
* If no valid graph exists, use normal repository inspection.
* Do not fabricate graph results.
* When `graphify-out/graph.json` exists and MCP is available, use Graphify for structural questions.
* Prefer `query_graph` for natural-language architectural questions.
* Prefer `get_node` for a known graph entity.
* Prefer `get_neighbors` for direct dependencies.
* Prefer `shortest_path` to trace relationships between two concepts.
* Use graph results to locate source files, then verify important conclusions against those files.
* Treat inferred or ambiguous graph edges cautiously.
* The graph is a snapshot; do not assume it includes later changes.
* Refresh the graph after meaningful structural changes when practical.
* Prefer incremental graph updates where appropriate.
* Do not spend engineering time repeatedly repairing Graphify during phases that do not require it.
* Once hardware, firmware, scripts, and KiCad structure become substantial, use Graphify as the default navigation layer.

## 8. Phase Discipline

* Every phase has a bounded scope.
* Work only inside the authorized phase.
* A phase prompt may narrow these rules but must not silently remove evidence or safety requirements.
* Each phase must end with a clear gate.
* Typical gate states are `PASS`, `BLOCKED`, `FAIL`, and `UNKNOWN`.
* Do not declare PASS merely because files were created.
* PASS requires phase acceptance criteria to be satisfied.
* If blockers prevent safe progression, do not claim readiness.
* Do not continue automatically after a phase gate unless explicitly authorized.

## 9. Requirement Classification

* `CONFIRMED`: supported by authoritative evidence or an approved project decision.
* `PROVISIONAL`: selected for now but still subject to verification or tradeoff.
* `UNKNOWN`: insufficient information exists for a defensible decision.
* `CONFLICTING`: relevant sources or requirements disagree.
* Every important UNKNOWN should state what would resolve it.
* Every CONFLICTING item should identify both sides.
* Do not hide unknowns inside narrative text.
* Make blockers easy to find.

## 10. Component Verification

* Verify every major candidate before schematic entry.
* Verify exact part number, package, pinout, supplies, absolute maximums, recommended operating conditions, reset, clocking, interfaces, thermal constraints, external components, decoupling, grounding, straps, boot requirements, and relevant errata.
* Check lifecycle and availability when relevant.
* Locate official evaluation-board or reference-design material when available.
* Do not approve a part based only on headline specifications.
* Verify the exact intended operating mode.
* If a part cannot meet a confirmed requirement, mark it unsuitable.
* Do not distort requirements merely to preserve a candidate component.

## 11. Interface Contracts

* Every major block-to-block connection must have an interface contract.
* For analog interfaces verify voltage range, common-mode range, topology, source/input impedance, bias, signal amplitude, headroom, bandwidth, and noise implications.
* For digital audio verify protocol, master/slave roles, sample rate, bit depth, slot width/count, frame format, BCLK, frame sync, logic levels, and timing margins.
* Do not assume two devices are compatible merely because both support TDM.
* For control interfaces verify voltage levels and pull requirements.
* For power interfaces verify nominal, minimum, maximum, transient, and peak current needs.

## 12. ANC-Specific Rules

* This board exists for real-time multichannel ANC.
* Hardware decisions must consider control-loop latency.
* Do not optimize audio quality while ignoring latency.
* Do not optimize latency while violating converter or DSP limits.
* Track ADC delay, serial-audio buffering, DSP block size, algorithm execution, and amplifier processing when data exists.
* FxLMS capability must not be assumed from generic DSP performance claims.
* DSP feasibility must eventually include compute and memory budgets.
* Reference and error microphone roles must be explicit before algorithm-dependent hardware is frozen.

## 13. Power and Clock Rules

* Verify power architecture before schematic implementation.
* Every rail must eventually define source, voltage, tolerance, expected load, peak load, startup, sequencing, decoupling, and fault behavior.
* Do not size regulators using typical current alone.
* Use worst-case or defensible margins.
* Do not ignore Class-D transient demand or DSP startup/peak load.
* Ground strategy must follow current-return behavior, not labels alone.
* Clock architecture is a critical design item.
* Establish clock sources, frequencies, master relationships, PLL usage, jitter sensitivity, startup, distribution, and synchronization before schematic freeze.
* Avoid unnecessary asynchronous clock domains.
* Do not embed unverified clock assumptions into the schematic.

## 14. Schematic Rules

* Do not create schematic files until the active phase authorizes schematic work.
* Resolve or formally accept schematic-entry blockers first.
* Use verified symbols and verify symbol pin numbers against official datasheets.
* Use explicit net names and show power intent clearly.
* Place required decoupling logically.
* Annotate configuration straps.
* Expose debug access intentionally.
* Document intentional no-connect pins.
* Avoid hidden assumptions.
* Never trust a third-party KiCad symbol without pin verification.
* Independently verify custom symbols before reuse.

## 15. PCB Rules

* Do not start placement before schematic review and ERC acceptance.
* Do not start routing before placement and constraint definition.
* Define layer count, stackup, outline, copper thickness, trace/space, via, high-current, differential-pair, keepout, thermal, connector, and manufacturing constraints before layout freeze.
* Critical placement precedes convenience placement.
* Keep sensitive analog paths compact.
* Keep high-current switching loops compact.
* Keep clock paths controlled.
* Protect ADC inputs from Class-D and noisy power regions.
* Do not split ground planes without a current-return reason.
* Prefer continuous return paths.

## 16. Class-D and EMI

* Treat the Class-D area as an EMI-critical power stage.
* Do not route speaker switching nodes through sensitive analog regions.
* Keep switching loops short.
* Follow manufacturer layout guidance.
* Account for output filtering, real speaker load, thermal dissipation, and connector current.
* Consider conducted and radiated emissions.
* Do not claim EMC compliance from a clean DRC.

## 17. KiCad and Validation

* KiCad files are engineering artifacts, not text-generation targets.
* Prefer KiCad-compatible editing workflows.
* Never intentionally generate syntactically invalid KiCad files.
* After schematic changes, run applicable ERC checks.
* After PCB changes, run applicable DRC checks.
* Do not suppress violations merely to get a clean report.
* Every waiver requires an engineering reason.
* Record significant waivers.
* Clean ERC does not prove electrical correctness.
* Clean DRC does not prove manufacturability, SI, PI, thermal performance, or EMC.
* A validation check may be `PASS`, `FAIL`, `UNKNOWN`, or `NOT APPLICABLE`.
* Do not report PASS when the required tool was not actually executed.
* If a tool is unavailable, state that explicitly.
* Keep automated checks reproducible and preserve useful outputs under `validation/`.

## 18. Change Discipline

* Make the smallest change that fully satisfies the active task.
* Do not refactor unrelated project content.
* Do not rename or move authoritative files casually.
* Preserve traceability.
* Record why a confirmed requirement changed.
* Record why a candidate component was replaced.
* Capture important architecture choices under `docs/decisions/` when appropriate.
* Avoid duplicate sources of truth.
* Update dependent documentation when an authoritative decision changes.

## 19. Risk Management

* Keep major engineering risks explicit.
* Prioritize overstress, unstable power, sequencing, interface compatibility, ADC performance, DSP feasibility, latency, clock integrity, thermal load, Class-D EMI, high-current routing, boot, availability, and manufacturing risks.
* For each major risk record cause, consequence, evidence, mitigation, and residual uncertainty.
* Do not bury severe risks in general notes.

## 20. Context Efficiency

* Search before reading entire large datasheets.
* Inspect targeted sections deeply.
* For critical conclusions, inspect surrounding conditions and footnotes.
* Do not repeatedly reread unchanged files without reason.
* Use Graphify for structural navigation when available.
* Use direct source inspection for authoritative engineering evidence.
* Prefer concise engineering notes over narrative summaries.
* Do not create documentation merely to demonstrate activity.

## 21. External Research

* Prefer manufacturer domains.
* Persist authoritative documents in the repo when the active task needs durable evidence.
* Do not rely on search snippets for electrical specifications.
* Verify document identity before trusting a downloaded PDF.
* Avoid unofficial mirrors when official copies exist.
* Record unresolved revision or access issues.

## 22. File Organization

* Keep phase documents under `docs/phases/`.
* Keep architecture decisions under `docs/decisions/` when created.
* Keep manufacturer documents under `datasheets/`.
* Keep donor and external examples under `references/`.
* Keep production KiCad files under `hardware/kicad/`.
* Keep firmware under `firmware/`.
* Keep validation artifacts under `validation/`.
* Keep Graphify output under `graphify-out/`.
* Keep donor designs separate from production design files.

## 23. Donor and Reference Designs

* Reference boards are evidence, not mandatory templates.
* Use them to study topology, decoupling, power, clocking, placement, routing, thermal practice, and EMI mitigation.
* Verify device revision and operating mode before transferring a design choice.
* Do not inherit unexplained components.
* Do not inherit legacy compromises.
* Never present a modified donor board as the clean-sheet design.

## 24. Task Output

* At task end, report what changed.
* Report what was verified.
* Report what remains unknown.
* Report what is blocking.
* Report files created or modified.
* Report the phase gate when applicable.
* Keep summaries compact.
* Do not claim work that was not performed.
* Distinguish findings from recommendations.
* Distinguish recommendations from approved decisions.

## 25. Stop Conditions

* Stop instead of guessing when an authoritative pinout cannot be verified.
* Stop when component revisions materially conflict.
* Stop when consequential voltage compatibility is uncertain.
* Stop when a confirmed requirement cannot be met.
* Stop when unresolved blockers prevent the requested next phase.
* Stop when a required official source cannot be located.
* Stop when a schematic symbol cannot be trusted.
* Stop when tool results contradict design assumptions.
* Stop when ERC or DRC exposes a material unresolved issue.
* Stop when the task would require unauthorized phase progression.
* A controlled stop is better than an unjustified decision.

## 26. Phase 1 Guidance

* Phase 1 reduces uncertainty; it does not create the schematic.
* Prioritize blockers with the greatest downstream impact.
* Verify microphone electrical requirements.
* Verify ADC compatibility.
* Verify DSP capability and boot requirements.
* Verify TDM compatibility end-to-end.
* Verify amplifier digital-audio compatibility.
* Verify amplifier load and power requirements.
* Verify clock dependencies.
* Verify power-rail requirements.
* Verify debug/programming requirements.
* Verify relevant errata and reference designs.
* Do not spend Phase 1 polishing layout choices that depend on unresolved architecture.

## 27. Responsible Progress

* Progress means reducing uncertainty with evidence.
* More files do not necessarily mean more progress.
* A verified incompatibility is useful progress.
* An explicit blocker is useful progress.
* A justified component rejection is useful progress.
* Confirmed facts are more valuable than convenient assumptions.
* The goal is not to reach routing quickly.
* The goal is to reach routing with a design that deserves to be routed.

## 28. Final Rule

* If uncertain, do not guess.
* Find evidence.
* If evidence is unavailable, preserve the uncertainty.
* If evidence conflicts, expose the conflict.
* If a phase is blocked, stop at the gate.
* Engineering traceability is mandatory.
