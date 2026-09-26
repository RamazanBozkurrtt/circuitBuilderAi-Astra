# Phase R0 — B2B two-board Product V1 rebaseline

**Source reviewed:** [ANC B2B Custom PCB two-board architecture v1.0](../product/ANC_B2B_Custom_PCB_2_Kart_Mimari_Tasarim_Dokumani_v1.0.docx), draft dated 26 September 2026; complete document, tables, diagram, appendices, header, and footer read. SHA-256: `df537a98c9bbfdef1dd5bf8447441946985fb8e6b438e1ae9e7990510d5c6f44`. Section references below refer to this document. Earlier project records were inspected to identify their scope, not to adopt their circuit decisions.

**R0 meaning:** Product V1 is rebaselined at product and repository level. This gate does **not** approve the target ICs electrically, close the product document's OPEN decisions, or authorize schematic or PCB work. No KiCad file was modified and no broad component verification was performed.

The product document names four earlier PoC, certification, speaker and market documents (§1; Appendix B). Those supporting documents are not in this repository and were not reviewed in R0. Claims that depend on them remain subject to later evidence checks.

## 1. New Product V1 baseline

Section 1.1 **freezes the two-board architecture**: Board A is Controller + Audio AFE; Board B is Power + Stereo Class-D. The product has **four equivalent analog microphone input channels** and **two secondary speaker outputs**. The intended chain in §2.1 is:

`4 × IM73A135 → differential analog input / AFE → TLV320ADC5140 → TDM/I²S → i.MX RT1062 / FxLMS → stereo I²S → TAS5825M → 2 × secondary speakers`

The microphone, ADC, MCU and amplifier entries are marked **HEDEF (target)** in §1.1 and Appendix A. They are Product V1 targets, **not verified component approvals**. The speakers are candidates. The product document is the authority for product intent; official device evidence and a later gate must establish circuit feasibility. Four microphones may eventually be assigned reference, error or monitoring roles; §2.1 leaves that allocation open.

The product excludes the PoC's MAX4466 modules, two SGTL5000/Audio Shield boards, primary/noise speaker, spare output, microSD, headphone jack and development controls (§§1–2, 11). Wireless/OTA is outside v1 scope (§§1.1, 7.2). The product uses external low-voltage DC; mains is not taken into the crib (figure 1; §2.2).

## 2. Board A architecture

Board A owns the sensitive analog and controller functions (§3). Functional blocks are four external IM73A135 microphone ports; cable-entry ESD/EMI provisions; four differential analog AFE paths; TLV320ADC5140; i.MX RT1062; external QSPI NOR; clock/reset/boot straps and production recovery; low-noise analog and separate digital regulation/filtering; independent hardware watchdog and fail-safe amplifier control; USB service/programming; and SWD/JTAG/pogo test access. An extra identity EEPROM is **optional** if flash can hold the required board/revision/serial data (§3.1).

**Power domains:** Board B supplies the cross-board 5 V rail. Board A generates its required analog and digital rails locally; exact voltages, loads, topology and sequencing are **UNKNOWN**. **Clock domains:** MCU/boot clock, ADC sampling/serial audio, and any forwarded amplifier clock need one verified clock plan; §3 requires a clock circuit but gives no frequency or master assignment. **Digital audio:** ADC-to-RT1062 TDM/I²S is a target, with format, pin mux, SAI/DMA use and latency **UNKNOWN**. **Safety:** hardware watchdog must be able to force the amplifier MUTE/ENABLE path safe even when firmware fails (§§3.1, 6–7).

The exact IM73A135-to-TLV320ADC5140 coupling, common mode, gain, bias, headroom and filtering network is explicitly **OPEN** (§3.1 AFE note; §12 item 1). Board A's six-layer stack is an **initial target**, with four-layer cost reduction conditional on EVT/DFM/EMC results (§3.2), not a frozen stackup.

## 3. Board B architecture

Board B owns the high-current and switching functions (§4): external 12 V entry and harness; reverse-polarity, OVP, OCP/short and eFuse/electronic-fuse strategy; 12 V-to-5 V high-efficiency buck; TAS5825M stereo digital-input Class-D; hardware MUTE/ENABLE with a default-muted MCU-failure state; amplifier fault/thermal and power-good feedback; two BTL speaker connectors; and bulk decoupling plus EMI/output-network provisions. Speaker negative terminals are **BTL switching outputs, not GND** (§4.1).

**Power domains:** protected 12 V/amplifier supply and generated 5 V; exact protection thresholds, rail tolerance, peak current and conversion topology remain **UNKNOWN**. **Clock/audio domain:** stereo I²S is intended for the amplifier, subject to end-to-end device verification. **Safety interface:** Board B must hold or enter mute during power-off, boot, resets and critical faults (§§4.1, 6–7); default levels, latching and response time need an electrical contract. Its four-layer PCB is an **initial target** (§4.2), not layout authorization.

The 12 V amplifier supply is a **target with a decision gate**, not a guaranteed final voltage (§4.2). Actual speaker Vrms/Irms, THD, excursion and ANC headroom in the crib must be measured. A move to 24 V is considered only if measurement requires it. No 12 V output-power claim is made in R0.

## 4. Board-to-board interface

Section 5.1 proposes these **signal classes**. It does not freeze connector pin assignments or all optional contacts. The final contract must treat both boards as one product, including signal directions, power-off behavior, return currents, fault response, startup order, contact ratings and mechanics.

| Class | Document direction and role | Required closure |
| --- | --- | --- |
| 5 V; multiple GND/return contacts | B → A; power and low-impedance signal/power returns | Worst-case load/peak current, contact allocation, drop, grounding and disconnect behavior |
| BCLK, LRCLK, audio data labelled `SDOUT` | A → B; stereo I²S from controller to amplifier | Exact protocol, transmitter/receiver pin naming, master/slave, rates, slots, logic levels, edge/timing margins and latency |
| MCLK | **Optional** A → B | Include only if verified amplifier/clock mode requires it; do not freeze a contact now |
| I²C SDA/SCL | Bidirectional; amplifier configuration/status | Voltage and pullups, addresses, reset/boot availability and unpowered leakage |
| AMP_MUTE, AMP_FAULT, PGOOD | A ↔ B as a group; request and feedback | Exact direction per signal, polarity, wired/active state without power or firmware, watchdog interaction and recovery policy |
| Revision detect / spare GPIO | Optional, minimum service only | Justify function, direction, voltage and contact before inclusion |

§5.2 proposes a keyed mezzanine connector, an initial 10–15 mm stack-distance class, common mounting datum, and opposite-edge placement of microphone versus power/speaker connectors. **Board dimensions and connector series remain OPEN** pending actual crib mechanics and harness routing. The Class-D/DC-DC region should not sit directly beneath Board A's microphone/ADC region (§5). These are future mechanical/EMC constraints, not a pinout or placement.

## 5. Legacy architecture disposition

The legacy single-board chain `IM73A135 → ADAU1978 → ADSP-21569 → TAS6424E-Q1 → four speakers` is **OBSOLETE FOR PRODUCT V1**. This includes the existing [KiCad project](../../hardware/kicad/), seven-sheet hierarchy and old four-channel TDM output contract. The old Phase 0–3 documents and Phase 4 validation records remain historical; their PASS/BLOCKED statements describe their original scope and do not authorize Product V1 schematic entry. Keep all history and evidence intact.

| Previous work | Classification for Product V1 | Reason |
| --- | --- | --- |
| Phase/gate and evidence process | **REUSABLE PRINCIPLE** | Method is independent of the IC set |
| IM73A135 findings and analog design methods | **REQUIRES REVALIDATION** | Microphone target recurs, but its ADC, AFE, cable and acoustic context changed |
| ADSP-21569, ADAU1978 and TAS6424E-Q1 approvals, symbols, circuits and rail tree | **OBSOLETE FOR PRODUCT V1** | Different controller, ADC, amplifier, power split and output count |
| Old supervisor thresholds, feedback networks, isolation parts, clock/TDM topology, connector map and sheet structure | **OBSOLETE FOR PRODUCT V1** | No new-product evidence supports their transfer |
| Old ERC/validation outputs | **REQUIRES REVALIDATION** if a method is reused; **OBSOLETE** as Product V1 circuit approval | They verify the legacy artifact only |

## 6. Reusable engineering lessons

**REUSABLE PRINCIPLE:** authoritative-source indexing; explicit `CONFIRMED / PROVISIONAL / UNKNOWN / CONFLICTING` decisions; worst-case tolerance and supervisor hysteresis checks; startup/shutdown dependency analysis; hardware-safe defaults; independent symbol-pin audit; ERC/DRC discipline; fault injection; physical validation tracking; traceable waivers and phase gates.

**REQUIRES REVALIDATION:** ANC latency/compute-budget method, microphone noise/headroom method, power/thermal/EMC calculation methods and connector current-return analysis when applied to the new blocks. Existing numeric results are not Product V1 limits.

**OBSOLETE FOR PRODUCT V1:** legacy IC selections, rail voltages, resistor/capacitor values, sequencing circuitry, isolation devices, four-output TDM/clock plan, amplifier/output network, exact connector pinout and seven-sheet KiCad partition.

## 7. Product-level open decisions

The following are explicitly **AÇIK (OPEN)** in §12; §1.1 also identifies boot/update as open and the speaker as a candidate. Preserve these statuses until their stated closure evidence exists.

| Open decision | Required closure from product document |
| --- | --- |
| IM73A135 → TLV320ADC5140 exact analog input network | Reference-circuit and bench validation before schematic freeze; verify coupling, bias, common mode, gain, headroom and filtering (§3.1; §12 item 1) |
| RT1062 boot/programming model | Decide a proprietary production boot/update flow versus Teensy compatibility, including licensing/extra parts if relevant (§§1.1, 7; §12 item 2) |
| Final secondary speakers | CE70PR-4 is a candidate; compare with SLS-65 in real-crib A/B testing at 80/100/125/160/250/500/800 Hz for THD, excursion and Vrms/Irms (§§1.1, 10; §12 item 3) |
| 12 V amplifier headroom | Measure attenuation target and actual speaker/electrical demand in crib; freeze supply only after that evidence (§4.2; §12 item 4) |
| Board dimensions and connector | Obtain crib maker's mechanical volume and cable routes; verify stack, keying, retention and current capacity (§5.2; §12 item 5) |
| Microphone role and placement | Assign reference/error/monitoring roles using acoustic geometry and algorithm tests (§2.1; §12 item 6) |
| Acoustic safety/SPL acceptance | Obtain written limit and test method from an independent acoustic expert/lab before sale (§6; §12 item 7) |

Other **UNKNOWN** implementation contracts include exact IC suffixes/packages, 5 V and local rail loads, audio clocking and latency, pin mux/DMA resources, production recovery, watchdog response time, speaker impedance/power envelope, EMC and thermal test limits. The diagram's 100–500 Hz main ANC target is a preliminary product graphic, **not** a complete cancellation or acoustic-safety acceptance mask.

## 8. Proposed schematic sheet structure — planning only

No sheets are implemented. Functional grouping may change after the document's OPEN items and device evidence are resolved.

### Board A

| Proposed sheet | Main blocks and interfaces |
| --- | --- |
| A1 Microphone ports and AFE | Four external IM73A135 ports, cable-entry ESD/EMI, differential conditioning, low-noise supply; ADC analog input contract |
| A2 ADC and audio clocks | TLV320ADC5140, reference/decoupling, conversion clock, ADC control, TDM/I²S to RT1062 |
| A3 RT1062, boot and memory | RT1062, QSPI NOR, boot/reset/recovery, MCU clock, SAI/DMA resources, watchdog interaction |
| A4 Board A power and supervision | Board B 5 V entry, local analog/digital rails, reset/PGOOD qualification and power sequencing |
| A5 Service, debug and safety | USB, SWD/JTAG/pogo, factory identity/test access, MUTE request, FAULT/PGOOD monitoring, hardware fail-safe path |
| A6 Board interface | Controlled mezzanine connection, multiple returns, audio/control/status signals and only justified service contacts |

### Board B

| Proposed sheet | Main blocks and interfaces |
| --- | --- |
| B1 12 V input and protection | External DC connector, reverse-polarity, OVP/OCP/eFuse strategy, protected rail and fault sensing |
| B2 5 V conversion and power status | Buck, local/bulk decoupling, PGOOD and Board A power feed |
| B3 Stereo Class-D and safety | TAS5825M, I²S/I²C, MUTE/ENABLE defaults, amplifier fault/thermal feedback and clock dependencies |
| B4 Speaker outputs and EMI | Two BTL output paths, network/filter provisions, speaker connectors, current/thermal test points |
| B5 Board interface | Keyed mezzanine, rail and return contacts, audio/control/status and connector test access |

The shared interface contract must own cross-board net names, direction, rail and clock domains, default states, sequencing and connector pin assignment. Functional sheets do not freeze those choices.

## 9. Proposed repository structure and migration

```text
docs/product/                                  primary product architecture document
docs/rebaseline/                               R0 report and later controlled updates
hardware/product_v1/
  board_a_controller_afe/                      future separate Board A KiCad project
  board_b_power_amp/                           future separate Board B KiCad project
  interface/                                   versioned cross-board contract
hardware/kicad/                                LEGACY single-board KiCad project
docs/phases/                                   prior phase history retained
validation/                                    retain old evidence; scope future results by product/board
```

This is a **proposed future structure**, not a KiCad migration in R0. The existing project stays at its path, explicitly labelled LEGACY in repository navigation. Product V1 gets separate projects only when schematic work is authorized; no old project is overwritten. Prior documents are preserved for traceability. `MASTER_SPEC.md`, `docs/architecture.md` and `docs/decisions.md` are placeholders; neither they nor old phase records supersede the product document.

## 10. Required verification before schematic work

1. Establish a controlled Product V1 requirements/interface register from the complete product document, retaining each OPEN item and tracing any approved closure.
2. Verify exact IM73A135, TLV320ADC5140, i.MX RT1062, QSPI NOR and TAS5825M variants against official device documents: pins, packages, supplies, reset/boot, clocks, serial audio, analog and power/output limits, reference circuits and errata.
3. Close the microphone-to-ADC analog contract with electrical/reference-circuit checks and targeted bench evidence; define ANC passband, latency, mic roles and FxLMS compute/memory budget.
4. Prove ADC → RT1062 → TAS5825M audio and clock compatibility end-to-end: TDM/I²S mode, mastership, sample/slot format, voltage domains, loaded timing and latency. Include MCLK only if required.
5. Define worst-case 12 V/5 V and local-rail envelopes; protection, current, return-contact, startup/shutdown, unplugged-board and back-power behavior. Make mute a hardware-safe state during boot, brownout, watchdog and critical faults.
6. Close speaker/load/headroom, acoustic safety/SPL, mechanical/connector, thermal and EMC acceptance inputs. Use real-crib speaker A/B and fault testing as specified in §§6, 10 and 12.
7. Verify symbol pins and footprint/package mappings independently and pass a separately authorized schematic-entry gate. ERC and PCB rules apply only after their respective implementation phases.

## 11. Recommended next phase

Authorize a bounded **Product V1 component and interface verification phase**. Prioritize the seven OPEN decisions, analog input, RT1062 boot/recovery, end-to-end digital audio and clocking, 12 V speaker/amplifier headroom, and the Board A–Board B power/safety contract. Produce an evidence-backed interface specification and schematic-entry gate. Schematic and PCB implementation require separate authorization.

**R0 gate:** The correct two-board product baseline, legacy disposition and repository authority are documented; the primary product document was read in full. OPEN product decisions remain OPEN, as intended. R0 does not claim electrical feasibility.

PHASE R0: PASS
