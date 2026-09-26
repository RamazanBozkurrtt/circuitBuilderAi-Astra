# Product V1 — Phase R1 requirements and open-decision control

**Authority:** [Product two-board architecture v1.0](../product/ANC_B2B_Custom_PCB_2_Kart_Mimari_Tasarim_Dokumani_v1.0.docx), draft 26 September 2026, SHA-256 `df537a98c9bbfdef1dd5bf8447441946985fb8e6b438e1ae9e7990510d5c6f44`. [R0 rebaseline](../rebaseline/phase_r0_b2b_two_board_rebaseline.md) and [R0.5 workflow](../rebaseline/phase_r0_5_workflow_infrastructure.md) were reviewed. The unchanged product document was previously read in full and its relevant sections/tables were reinspected for R1. The source's other named PoC, speaker, certification and market documents were not available here. Legacy IC architecture supplies no Product V1 evidence.

**Classification:** `CONFIRMED` means an explicit product-level requirement in the architecture source, **not** verified electrical feasibility. `PROVISIONAL` means a stated target or starting choice requiring later verification/approval. `OPEN` means a missing decision or quantitative contract. `CONFLICTING` is reserved for real disagreement; none was established in the product source during R1. Requirements are not silently relaxed to retain a target component.

## 1. Product V1 acceptance matrix

The matrix is the controlled R1 baseline. “Due” is the earliest phase gate requiring closure or a formally bounded disposition; later physical/production proof can remain open as separately identified. Product owner, controls/acoustic lead, mechanical partner and safety lab are **resolution sources**, not assigned named people.

| ID | Requirement / decision | Status | Board | Owner / evidence source | Due | Closure criterion |
| --- | --- | --- | --- | --- | --- | --- |
| SYS-01 | One product, Board A Controller + Audio AFE and Board B Power + Stereo Class-D | **CONFIRMED** | System | Product doc §1.1 | R0 | Two-board boundary retained. |
| SYS-02 | Four simultaneous analog microphone inputs and two secondary speaker outputs | **CONFIRMED** | A+B | Product doc §§1.1, 2.2 | R0 | Preserve counts; no old four-output path. |
| SYS-03 | Real-time, low-latency ANC/FxLMS processing | **CONFIRMED** intent | System | Product doc §2.2 | R3/R12 | Define measurable target and later prove feasibility; see SYS-04. |
| SYS-04 | Quantitative ANC band, attenuation and latency acceptance | **OPEN** | System | Product owner + controls/acoustic lead; §2.2 and figure 1 | R3 | Approve measurable target or bounded prototype envelope; [finding 010](../../validation/findings/PV1-R1-010.json). |
| SYS-05 | External low-voltage DC; no mains routed into crib | **CONFIRMED** | B | Product doc §2.2 and figure 1 | R3 | Maintain protected external-DC architecture. |
| SYS-06 | No Wi-Fi/Bluetooth or OTA requirement in v1 | **CONFIRMED** | System | Product doc §§1.1, 7.2 | R1 | Do not add wireless as a default requirement. |
| SYS-07 | Hardware-safe mute during power-off, boot, reset and critical fault; software is not sole safety layer | **CONFIRMED** | A+B | Product doc §§2.2, 6, 7.1 | R4 | Define default states and response target; see SYS-08. |
| SYS-08 | Quantified mute/fault timing and cross-board safe-state contract | **OPEN** | Interface | Product/safety input + §9 EOL | R4 | Approved default/polarity/dependency/response contract; [finding 011](../../validation/findings/PV1-R1-011.json). |
| SYS-09 | B2B embedded integration, factory/service access and paired-board traceability/EOL | **CONFIRMED** | System | Product doc §§1, 8–9 | R14 | Production records link Board A/B pair, firmware and calibration. |
| SYS-10 | POWER_OFF, BOOT_SAFE, SELF_TEST, READY, ANC_ACTIVE and FAULT_MUTE behavior | **CONFIRMED** product behavior; timing **OPEN** | System | Product doc §7.1 | R4/R12 | Preserve silent boot/self-test/fault states; define timing and validate fault response. |
| SYS-11 | Remove PoC-only microSD, headphone, potentiometers, extra codec/DAC, primary and spare outputs | **CONFIRMED** | System | Product doc §§1–2, 11 | R1 | Do not reintroduce without a new product decision. |
| SYS-12 | EVT→DVT→PVT and fixture-based EOL with channel, boot, fault/mute and paired-board records | **CONFIRMED** process; sample counts **PROVISIONAL** | System | Product doc §§8–10 | R14 | Retain physical evidence and factory test limits before release. |
| SYS-13 | Cost reduction must retain protection, watchdog, mute, ESD/EMI and EOL test | **CONFIRMED** constraint | System | Product doc §11 | R13 | Cost-down review cannot remove these functions. |
| SYS-14 | 400 units/year and four 100-unit releases are planning assumptions, not supplier commitments | **PROVISIONAL** | System | Product doc §§8, 11 | R13 | Confirm demand, RFQ and manufacturing plan before commercial release. |
| A-01 | Four electrically equivalent IM73A135 microphone interface channels | **PROVISIONAL** target IC; **CONFIRMED** equality | A | Product doc §§1.1, 2.1, 3.1 | R2/R4 | Verify exact device/interface; do not preassign acoustic roles. |
| A-02 | TLV320ADC5140 for four-channel acquisition | **PROVISIONAL** | A | Product doc §§1.1, 3.1 | R2 | Verify exact variant, mode, latency and analog/digital limits. |
| A-03 | i.MX RT1062 as production ANC controller | **PROVISIONAL** | A | Product doc §§1.1, 3.1 | R2 | Verify capability, boot, memory/compute and interfaces. |
| A-04 | External QSPI NOR for boot/application; calibration storage as needed | **CONFIRMED** function; MPN/capacity **OPEN** | A | Product doc §3.1, Appendix A | R3 | Choose supported flash/partition strategy after boot decision. |
| A-05 | Clock, reset/boot straps and recovery path | **CONFIRMED** function; implementation **OPEN** | A | Product doc §3.1 | R3/R4 | Verify clock ownership, startup and recoverable boot. |
| A-06 | Independent hardware watchdog can force amplifier safe state | **CONFIRMED** | A | Product doc §§3.1, 6 | R4 | Demonstrate hardware path independent of normal ANC firmware. |
| A-07 | USB service/programming and SWD/JTAG/pogo production access | **CONFIRMED** access requirement; exact routing **OPEN** | A | Product doc §§2.2, 3.1, 7.2 | R3/R4 | Approve factory/recovery workflow and accessible test interface. |
| A-08 | Low-noise analog rails and separate digital regulation/filtering | **CONFIRMED** function; values **OPEN** | A | Product doc §3.1 | R4 | Verify full rail tree, noise/load and sequencing against device limits; [finding 012](../../validation/findings/PV1-R1-012.json). |
| A-09 | Differential mic cable entry, ESD/EMI provisions and exact ADC input network | **OPEN** circuit; provisions **CONFIRMED** | A | Product doc §3.1 and AFE note | R4 | Evidence-backed network and bench check; [finding 001](../../validation/findings/PV1-R1-001.json). |
| A-10 | ADC→RT1062 serial audio and Board A→B audio/control | **PROVISIONAL** formats | A/interface | Product doc §§2.1, 3.1, 5.1 | R3 | Validate end-to-end modes, timing and levels; [finding 013](../../validation/findings/PV1-R1-013.json). |
| A-11 | Quiet AFE placement/continuous returns, test access and an initial six-layer planning target | **CONFIRMED** placement/test intent; layer count **PROVISIONAL** | A | Product doc §3.2 | R7/R12 | Approve stackup/DFM/EMC constraints; four layers only after EVT evidence. |
| B-01 | Protected nominal 12 V input as initial product target | **PROVISIONAL** | B | Product doc §§4.1–4.2 | R4 | Bound electrical envelope; final adequacy stays open. |
| B-02 | Reverse-polarity, OVP, OCP/short and eFuse/electronic-fuse strategy | **CONFIRMED** functions; topology **OPEN** | B | Product doc §§4.1, 6 | R4 | Select/verify protected power path and fault behavior; [finding 012](../../validation/findings/PV1-R1-012.json). |
| B-03 | Efficient 12 V→5 V conversion feeding Board A | **CONFIRMED** product rail class; parts/limits **OPEN** | B/interface | Product doc §§4.1, 5.1 | R3/R4 | Contract source/load/current/returns and verify converter; [finding 012](../../validation/findings/PV1-R1-012.json). |
| B-04 | TAS5825M stereo digital-input Class-D target | **PROVISIONAL** | B | Product doc §§1.1, 4.1 | R2 | Verify exact mode, supplies, audio, load, protection and thermal limits. |
| B-05 | Two BTL speaker outputs; neither negative terminal is ground | **CONFIRMED** | B | Product doc §§2.2, 4.1 | R5 | Preserve BTL marking and connection contract. |
| B-06 | Hardware MUTE/ENABLE defaults to mute on MCU failure | **CONFIRMED** | B/interface | Product doc §§4.1, 6–7 | R4 | Close SYS-08 and verify unpowered/brownout behavior. |
| B-07 | AMP_FAULT/thermal and PGOOD feedback to Board A | **CONFIRMED** function; levels/polarity **OPEN** | B/interface | Product doc §§4.1, 5.1 | R3 | Close shared status contract. |
| B-08 | EMI/output network and bulk-decoupling provisions | **CONFIRMED** provisions; values **OPEN** | B | Product doc §§4.1–4.2 | R5/R12 | Device-backed design, then physical EMI/output validation. |
| B-09 | High-current loops, connector capacity and thermal path handled on Board B | **CONFIRMED** design constraint; limits **OPEN** | B | Product doc §§4.1–4.2, 6 | R7/R12 | Worst-case current/thermal/return analysis, then measurement. |
| B-10 | Initial four-layer planning target, compact switching loops and accessible power/fault test points | **CONFIRMED** layout/test intent; layer count **PROVISIONAL** | B | Product doc §4.2 | R7/R12 | Fabricator stackup, DRC and physical thermal/EMI checks. |
| IF-01/02 | Board B→A 5 V and multiple low-impedance GND/return contacts | **CONFIRMED** classes; counts/tolerance **OPEN** | Interface | Product doc §§5.1, 6 | R3 | Verified current, drop and return-contact allocation. |
| IF-03/05 | BCLK, LRCLK/FSYNC and audio data from A→B | **PROVISIONAL** serial contract | Interface | Product doc §5.1 | R3 | Exact mastership, format, levels, edges and timing. |
| IF-06 | Forwarded MCLK only if required | **OPEN/optional** | Interface | Product doc §5.1 | R3 | R2 endpoint/clock evidence establishes inclusion or omission. |
| IF-07 | I²C SDA/SCL for amplifier control/status | **PROVISIONAL** electrical bus | Interface | Product doc §5.1 | R3 | Voltage, pullups, addressing and unpowered behavior. |
| IF-08/10 | AMP_MUTE, AMP_FAULT and PGOOD cross-board safety/status | **CONFIRMED** classes; electrical behavior **OPEN** | Interface | Product doc §§4.1, 5.1 | R3/R4 | Direction, polarity, fault defaults and sequencing. |
| IF-11 | Revision detect/spare service contacts only if justified | **OPEN/optional** | Interface | Product doc §5.1 | R3 | Document need or omit; no reserved pinout by habit. |
| IF-12 | Keyed mezzanine and initial 10–15 mm stack class; exact connector/outline open | **PROVISIONAL** concept; mechanics **OPEN** | Interface | Product doc §5.2 | R7 | Obtain crib volume/routes and verify part, stack, mounting and contacts. |
| D1 | IM73A135→ADC analog network | **OPEN** | A | Engineering + bench; product doc §12.1 | R4 | See [finding 001](../../validation/findings/PV1-R1-001.json). |
| D2 | Native RT1062 versus Teensy-compatible boot/update | **OPEN** | A | Product owner + R2 engineering; §12.2 | R3 | See [finding 002](../../validation/findings/PV1-R1-002.json). |
| D3 | CE70PR-4 versus SLS-65 final speaker | **OPEN** | B/external | Real-crib A/B; §12.3 | R13 | See [finding 003](../../validation/findings/PV1-R1-003.json). |
| D4 | Final 12 V amplifier headroom | **OPEN**; 12 V starting target **PROVISIONAL** | B | Electrical bound + EVT; §12.4 | R4 bound; R13 final | See [provisional bound](../../validation/findings/PV1-R1-004.json) and [physical proof](../../validation/findings/PV1-R1-005.json). |
| D5 | Board dimensions and connector mechanics | **OPEN** | Interface | Crib maker + engineering; §12.5 | R7 | See [finding 006](../../validation/findings/PV1-R1-006.json). |
| D6 | Microphone roles/placement | **OPEN** | A/external | Acoustic geometry/testing; §12.6 | R13 | See [finding 007](../../validation/findings/PV1-R1-007.json). |
| D7 | Acoustic safety/SPL acceptance criteria | **OPEN** | System | Independent expert/lab; §12.7 | R14 | See [finding 008](../../validation/findings/PV1-R1-008.json). |

The table’s mixed-status rows distinguish a confirmed **function** from an unverified **implementation**; no target IC, frequency, tolerance, connector series or SPL number is approved here. The product document's preliminary cost and board-layer figures are planning targets, not supplier quotations or frozen stackups.

## 2. Seven open decisions — controlled disposition

| Decision | R1 disposition | What the next evidence must establish |
| --- | --- | --- |
| D1 analog network | **REQUIRES R2 ENGINEERING VERIFICATION**, then targeted bench/reference-circuit check by R4; stays OPEN. | Source/output and ADC input topology, differential/single-ended mode, coupling, common mode, bias, gain, clipping/headroom, anti-alias filtering, noise and low-frequency amplitude/phase for the approved ANC band. R1 defines no component values or circuit. |
| D2 boot/programming | **Product decision + R2 engineering verification**; stays OPEN. | Product owner chooses native RT1062 production flow or an explicit Teensy-compatibility requirement by R3, with flash, recovery, factory programming, field service, licensing/dependency and BOM consequences documented. |
| D3 speakers | **REQUIRES BENCH / ACOUSTIC TEST**; stays OPEN. | In the real crib, compare CE70PR-4 and SLS-65 under recorded mounting/microphone geometry and controlled stereo stimuli at **80/100/125/160/250/500/800 Hz**; record impedance versus frequency, attenuation, Vrms/Irms, THD, excursion, thermal/fault observations and repeatability. Selection needs a separately approved acoustic target, not a new number from R1. |
| D4 headroom | **PROVISIONALLY BOUNDED** as a 12 V starting architecture, with final adequacy **REQUIRING BENCH / ACOUSTIC TEST**. | Before R4, establish a worst-case provisional electrical envelope. In EVT-1 with chosen speakers, measure required Vrms and Irms, attenuation, impedance, THD, excursion, simultaneous stereo loading and ANC reserve at minimum supply. If 12 V fails, formally reopen R3/R4 and affected hardware; do not silently adopt 24 V. |
| D5 dimensions/connector | **REQUIRES MECHANICAL INPUT**; stays OPEN. | Crib maker supplies allowable volume, mounting datum, stack height, cable routes, access and retention constraints before R7. Independently, R3 can freeze signal classes, levels, current/return needs and fault defaults without choosing a connector series or pin numbers. |
| D6 mic roles/placement | **REQUIRES BENCH / ACOUSTIC TEST**; stays OPEN. | Keep **four electrically equivalent input channels**. Assign reference/error/monitoring only after real geometry, harness and algorithm tests; record channel map before final validation. |
| D7 safety SPL | **REQUIRES EXTERNAL SAFETY / COMPLIANCE INPUT**; stays OPEN. | Independent acoustic expert/lab supplies written limit, peak/duration and fault/instability test method before sales release (R14). No SPL limit is inferred from the diagram’s preliminary 100–500 Hz label. Safe mute/fault handling must be defined earlier at R4. |

No D1–D7 final decision is **CLOSED NOW**. The product document already closes the two-board architecture, I/O counts and exclusion of v1 wireless; those confirmed requirements do not close the seven listed decisions.

### D2 product-level boot comparison

This is a direction-setting comparison, **not RT1062 pin/boot-circuit verification**. NXP documents a BootROM plus factory flashloader route for external flash programming; PJRC documents a preprogrammed MKL02 bootloader chip for a DIY Teensy 4.x-compatible RT1062 board. [NXP manufacturing guide](https://docs.mcuxpresso.nxp.com/mcuxsdk/latest/html/middleware/mcu_bootloader/docs/iMXRT1060_Manufacturing_User_Guide/topics/introduction.html), [NXP programming flow](https://docs.mcuxpresso.nxp.com/mcuxsdk/latest/html/middleware/mcu_bootloader/docs/iMXRT1060_Manufacturing_User_Guide/topics/program_bootable_image.html), [PJRC bootloader-chip documentation](https://www.pjrc.com/store/ic_mkl02_t4.html).

| Consequence | A. Native production RT1062 flow | B. Preserve Teensy compatibility |
| --- | --- | --- |
| Hardware / flash | Custom RT1062/QSPI design and validated recovery access; flash choice follows NXP boot support. | Additional PJRC bootloader-chip dependency and its supported RT1062/flash combinations; verify exact board compatibility. |
| Bootloader / programming | Project owns image, factory flashing, recovery and any field-update procedure; NXP provides documented ROM/manufacturing path. | Teensy loader behavior is tied to PJRC bootloader ecosystem; verify production fixture and image workflow. |
| Licensing / dependency | Review NXP tools/SDK and project firmware terms; project maintains its own flow. | Obtain written commercial-use/support/licensing terms for the PJRC path and any reused firmware/libraries; R1 makes no legal claim. |
| BOM / maintainability | Avoids a Teensy-specific bootloader IC **if** native flow is approved, but adds project-owned software/test maintenance. | Adds a sourced preprogrammed IC and vendor dependency; may reduce migration work if exact Teensy behavior is a product requirement. |
| Field service | Define authorized USB/pogo recovery and rollback policy; exact implementation remains open. | Define how the PJRC loader fits B2B service, firmware versioning and recovery; compatibility alone does not define the policy. |

**Recommendation, not approval:** prefer **A, a native RT1062 production flow**, because the product document already prefers its own flow and removes PoC-specific hardware; this reduces dependence on Teensy compatibility while retaining a documented NXP manufacturing route. That benefit is an inference from the two primary sources. The product owner must approve this direction before R3; R2 must verify the exact RT1062/flash/boot/recovery implementation and software/licensing implications. If Teensy tool or binary compatibility is a real product requirement, reopen the comparison explicitly.

## 3. Board-to-board requirement contract

The updated [machine-readable interface](../../state/board_to_board_interface.json) carries stable IDs `IF-01`–`IF-11` for 5 V, multiple GND returns, BCLK, LRCLK/FSYNC, A→B audio data, optional MCLK, I²C SDA/SCL, AMP_MUTE, AMP_FAULT, PGOOD and optional revision/service. `SDOUT` is retained only as the product document's alias; the actual endpoint pin naming is unverified. Board B is the intended 5 V source and status source; Board A is the intended audio/mute controller. I²C is shared. These are product-level roles, not verified pin mappings.

Exact connector pin numbers, part/stack, contact allocation, rail tolerances, logic levels, pullups, audio format/mastership, MCLK need, fault polarity, startup/shutdown and unplugged-board behavior remain explicitly open. `required_count` and `voltage_domain` remain `null` in the JSON; multiple return contacts are nonetheless an explicit requirement. The electrical contract can close at R3 before the mechanical connector choice at R7, provided current/contact/return constraints are defined so a later connector can be checked against them. [Finding 009](../../validation/findings/PV1-R1-009.json) blocks R3 until that contract is evidenced.

## 4. Human decision register

| Decision class | Who/what closes it | Examples and boundary |
| --- | --- | --- |
| Engineering-verifiable | R2/R3/R4 manufacturer evidence, calculations and reference circuits; bench where source-only proof is insufficient | D1 electrical compatibility; clock/audio, flash/boot feasibility, cross-board levels and provisional power envelope. |
| Physical-test | Controlled prototype/real-crib measurement | D3 speaker A/B, D4 final headroom, D6 microphone-role/geometry proof, noise/latency and fault response. |
| Product choice | Explicit project-owner approval | D2 native versus Teensy flow; quantitative ANC target and service policy; whether a provisional envelope is acceptable for prototype work. |
| External input | Crib/mechanical partner, independent acoustic expert/lab, relevant compliance assessor | D5 dimensions/harness/connector mechanics; D7 written safety SPL and test method. |

An engineering calculation does not authorize a product choice; a recommended option is not a decision. Physical-test and external-input items cannot be closed by plausible datasheet numbers or AI inference.

## 5. Schematic-entry and release blocker map

The structured [findings](../../validation/findings/) use `blocks_from_phase`. R1 extended the finding schema and gate runner to check the phase being entered and require exact synchronization with `state.open_blockers`; otherwise future blockers would incorrectly fail R1. All 13 current blockers start **after R2**. Their closure criteria are in their JSON records. A later PASS does not remove the duty to run the stated physical test.

| Gate / milestone | Blocking items due there | What remains legitimately open |
| --- | --- | --- |
| **R2 component verification** | None from R1. R2 may begin with the documented targets and open questions. | All seven product decisions; R2 must report unsuitable devices or new blockers if found. |
| **R3 architecture/interface freeze** | [002](../../validation/findings/PV1-R1-002.json) boot choice; [009](../../validation/findings/PV1-R1-009.json) cross-board electrical contract; [010](../../validation/findings/PV1-R1-010.json) measurable ANC target/bounded envelope; [013](../../validation/findings/PV1-R1-013.json) end-to-end audio/clock contract. | Final speaker, 12 V physical proof, board dimensions and SPL sales criteria. |
| **R4 schematic readiness** | [001](../../validation/findings/PV1-R1-001.json) analog network; [004](../../validation/findings/PV1-R1-004.json) provisional power/headroom envelope; [011](../../validation/findings/PV1-R1-011.json) safe-mute response contract; [012](../../validation/findings/PV1-R1-012.json) power/protection/rail contract. | Final crib measurements and connector series if interfaces retain a manufacturable envelope. |
| **R5 schematic implementation** | No new R1 finding if R4 passed; any failed R4 closure blocks R5 too. | Physical A/B and final safety tests. |
| **R7 PCB constraints/stackup; R8–R12 layout/verification** | [006](../../validation/findings/PV1-R1-006.json) mechanical board/connector envelope from R7 onward; earlier unresolved findings remain blocking. | EVT speaker choice and final acoustic claims, with controlled rework risk. |
| **EVT-0 / EVT-1 physical work** | Test plan must measure D1 implementation, boot/recovery, audio latency, safe mute, D3 speaker A/B, D4 headroom and D6 role/geometry. | No acoustic/12 V compliance claim before data; failures reopen affected earlier gates. |
| **R13 DFM/DFA** | [003](../../validation/findings/PV1-R1-003.json) final speaker; [005](../../validation/findings/PV1-R1-005.json) measured 12 V headroom; [007](../../validation/findings/PV1-R1-007.json) mic roles/placement. | Written sales-release SPL criterion still due at R14. |
| **R14 manufacturing/production release** | [008](../../validation/findings/PV1-R1-008.json) independent acoustic safety/SPL criteria and proof; all earlier findings must also be resolved. | None of these open decisions may remain unapproved for release. |

The phase roadmap is not an EVT authorization. If physical evidence invalidates an earlier architecture choice, return to its gate and update dependent contracts rather than recording a convenient waiver.

## 6. R1 disposition and next phase

R1 classifies the product baseline and records 13 future-gate findings with exact closure criteria. There is **no unresolved blocker due before R2** in the current source record. The [R1 validation](../../validation/r1_product_requirements_validation.md) checks JSON/schema integrity, state/findings synchronization, Board A/B and interface scope, phase-scoped gate behavior and unchanged KiCad scope. The R1 engineering review confirmed the statuses and phase dependencies; the runner's human field remains `NOT_EVALUATED` because it never records review approval automatically. R1 does not approve target ICs, boot circuits, speaker performance, electrical values or SPL limits.

**Recommended next phase:** separately authorize R2 component verification. R2 should use official manufacturer evidence to test the target parts and the questions above, report conflicts, and leave physical/product/external decisions open.

PHASE R1: PASS
