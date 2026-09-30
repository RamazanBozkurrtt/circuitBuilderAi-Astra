# R4 schematic-readiness validation

Date: 2026-09-28. R3 human gate: **APPROVED** by the project owner's R4 instruction; recorded in `state/project_state.json` and `validation/r3_system_architecture_validation.md`. R3→R4 entry machine gate: **PASS** with `python workflow/gates/run.py --phase R3 --next-phase R4`. The runner was corrected so findings due during R4 block R4 completion, not R4 entry.

R4 was evaluated with `python workflow/gates/run.py --phase R4 --next-phase R5`. The machine result is **BLOCKED**. Its detailed result and the no-KiCad check are recorded below. The report and all three R4 machine contracts parse; the R4 engineering proof is incomplete. A parseable file is not evidence of an electrically ready sheet.

| R4 gate | Result | Meaning |
| --- | --- | --- |
| Documentation contract | **PASS** | All 19 required references exist. |
| Blocking findings | **BLOCKED** | `PV1-R1-001`, `002`, `004`, `009`, `011`, `012`, `013` are due by R4. All 13 records and state agree. |
| Product architecture | **PASS** | Board A/B and the controlled B2B signal inventory remain coherent. |
| Strict R4 schematic gate | **BLOCKED** | All 12 planned sheets are BLOCKED; full MCU pin map and loaded B2B DC/timing/off-domain proof are incomplete. Listed provisional MCU pads/balls are unique and avoid reserved boot/debug pads. |
| R4→R5 transition | **PASS as allowed route only** | The phase definition permits R5 after completed R4 and human approval; the runner made no transition. |

No KiCad file was created or modified. Product V1 ERC, DRC, hierarchical interface, pin and BOM adapters remain `NOT_AVAILABLE`; no electrical simulation, physical measurement or acoustic test is claimed. The R3 conceptual dependency graph is acyclic, but the actual circuit graph, threshold/hysteresis margins, loaded B2B timing and powered-off drive are not proven. R5 is not authorized.

Additional consistency check: all six machine JSON files parse; 23 provisional RT1062 allocations have 23 unique pads and balls; the unresolved finding set exactly matches `state/project_state.json`; `hardware/product_v1` contains no KiCad artifact and the Git diff lists no modified `*.kicad_*` file. The runner JSON reports `machine_result: BLOCKED` and returned a nonzero shell status. The R3→R4 gate was also rerun from the present R4 state and remained **PASS**.
 
## R4 closure-pass rerun, 2026-09-28

The original BLOCKED result above is preserved. This pass added official-document screening and `validation/r4_closure_calculations.py` for conditional audio-buffer DC/timing and rail calculations. The script ran successfully; its results are conditional on stated load, rail and interconnect bounds and do **not** establish R5 readiness. The seven original R4 findings received appended evidence entries without deletion or status downgrades. Board A/B contracts and the B2B interface retain `BLOCKED` / `r5_ready=false` for unproven circuits.

`python workflow/gates/run.py --phase R4 --next-phase R5` returned exit code **1** and `machine_result: BLOCKED`. Documentation contract **PASS** (19 references), product architecture **PASS**, blocking findings **BLOCKED** (PV1-R1-001, 002, 004, 009, 011, 012, 013), strict R4 schematic-readiness **BLOCKED** (all 12 R5 sheets, RT1062 fixed resources, Board A/B guaranteed circuits, B2B DC/timing/off-state). The route definition allows R5 only after a completed R4 and human approval; the runner made `phase_state_changed: false`. No ERC claim was made.

The current NXP RT1060 Reference Manual Rev 4 and Hardware Design Guide Rev 7 are account-required; the owner has no authorized copies. Exact missing chapters/sections and all seven closure criteria are listed in the R4 report section 9. Adapter range/current and safety response target were requested from the owner but were not presumed. No Product V1 KiCad file was created or modified; `hardware/product_v1` has no `*.kicad_*` artifact and `git diff --name-only -- '*.kicad_*'` is empty. Product V1 KiCad hooks remain `NOT_AVAILABLE`. R5 was not started.

## Owner-input and authorized-NXP-manual rerun, 2026-09-30

The two preceding R4 BLOCKED results remain historical. The owner supplied authorized local NXP `IMXRT1060RM` Rev. 4 and `MIMXRT105060HDUG` Rev. 7 copies; they are now indexed in `docs/product_v1/component_evidence_index.md`. The earlier **access-based** `MISSING_AUTHORITATIVE_EVIDENCE` reason is retired. The owner also classified 12 V nominal as provisional, removed the PoC 10-A assumption, supplied a provisional engineering mute target of <=10 ms, and explicitly kept production response/SPL acceptance open for later safety testing. Section 10 of the R4 report records the bounded calculations and per-finding gap.

`python validation/r4_closure_calculations.py` passed. It calculated PLL4 VCO 786.432 MHz, post-divider 196.608 MHz, SAI1/SAI2 roots 24.576 MHz, ADC BCLK 12.288 MHz and amplifier BCLK 6.144 MHz from the current NXP RM. Its ADC receive setup margin is **7.69 ns before skew** at TI's 25 °C/20-pF condition, **2.69 ns at the proposed 5-ns skew**. Those figures are conditional, not loaded or full-temperature signoff. The provisional 8–18-V input screen yields assumed-load currents of 7.922 A at 12 V and 10.862 A at 18 V; these are not adapter ratings because Board A load and power efficiency were assumed. A fastest screened watchdog timeout up to 9.3 ms leaves only 0.7 ms against the owner's provisional fault-to-mute target, with no proved output-decay time.

The calculation script also checks a **non-frozen** 24-bit TDM mitigation at 9.216-MHz ADC BCLK. It raises conditional 25 °C/20-pF setup room to about 16.25 ns after the proposed 5-ns skew while preserving a 6.144-MHz amplifier BCLK with a different PLL divider profile. The current machine contracts retain the R3 four-by-32-bit baseline until the entire framing and loaded timing proof is complete.

After correcting an initially added finding metadata field that the repository schema disallows, `python workflow/gates/run.py --phase R4 --next-phase R5` returned exit code **1** and `machine_result: BLOCKED`: documentation **PASS**, findings **BLOCKED** (the same seven original IDs), architecture **PASS**, strict schematic gate **BLOCKED**, and allowed-route definition **PASS** without a transition (`phase_state_changed: false`). All seven findings have appended evidence and unchanged blocking statuses. No R5 sheet was promoted because its exact analog, boot, power, safety or interface circuit is still incomplete. The current phase and machine result in `state/project_state.json` remain R4/BLOCKED; R5 remains unauthorized.

No Product V1 KiCad artifact was created or modified: recursive `hardware/product_v1` `*.kicad_*` search returned no file and `git diff --name-only -- '*.kicad_*'` was empty. Product V1 KiCad hooks remain `NOT_AVAILABLE`; ERC was neither run nor claimed.
