# Phase 4A power-input validation

**Current result: see the resumed Phase 3A implementation record below.** The original BLOCKED snapshot and its validation artifacts are retained as history.

Date: 2026-09-09. **Hierarchy initialized; electrical implementation blocked.**

## Implemented scope

- Created `hardware/kicad/circuitBuilderAi-Astra.kicad_pro`, its root schematic, and all seven logical sheets from Phase 3 section 14. The root is page 1; logical sheets 1-7 are pages 2-8.
- Sheet 1 contains the blocking finding only. Sheets 2-7 are intentionally empty placeholders. No components, electrical nets, hierarchical signal pins, PCB, placement, or routing were created.
- Components added: **none**. Symbol/pin/package/rating verification: **NOT APPLICABLE to this snapshot**; no component implementation is approved.

## Blocking electrical conflict

**CONFLICTING:** Phase 3 sections 3.1 and 5.1 permit `12V_PROTECTED = 10.4 V` during normal operation (10.8 V connector minimum, up to 0.4 V path drop at 4 A). Sections 4.2 and 6.2 require the frozen PGOOD divider to qualify the downstream sequence and state that operation remains enabled at the normal minimum.

TI requires PGTH to sense **OUT**, and PGOOD deasserts when that monitored voltage crosses its falling threshold [TPS2663, SLVSE94G, section 8.3.2/8.3.2.1, p.19; Figure 9-2, p.30]. With the frozen 468 kohm / 56.0 kohm divider:

| Check | Result |
| --- | --- |
| Nominal falling threshold | `1.123 * (1 + 468/56) = 10.5081 V` |
| Maximum using p.8 threshold and 0.1% resistor bounds | `1.15 * (1 + 468*1.001/(56*0.999)) = 10.7800 V` |
| Allowed normal protected minimum | `10.8 - 0.4 = 10.4000 V`, below both thresholds |
| Even with other path losses set to zero | `10.8 - 4*0.053 = 10.5880 V`, below the upper threshold; 53 milliohms is the eFuse maximum RON at the specified temperature range, p.7 |

These are counterexamples to guaranteed normal operation, not a claim that every unit will fail. The threshold bound reproduces Phase 3's calculation without pin leakage; the conflict already exists before that additional uncertainty. No hardware test was performed.

**Required resolution:** approve a consistent PGOOD/UVLO threshold and input/path-drop operating contract, including load, tolerance, and cold-start margins. Moving PGTH to raw input is not adopted: TI also uses it to distinguish charged-output recovery from a startup requiring dVdT limiting (p.19). Frozen resistor values and Phase 3 documents were not changed. The conflict prevents faithful Sheet 1 implementation and subsequent power-sequencing implementation.

## Evidence and validation

- Authority: `AGENTS.md`, [Phase 3](../docs/phases/phase_3_schematic_readiness.md) sections 3.1, 4, 5.1, 6.2, 14-15; [evidence index](../docs/evidence/component_evidence_index.md), PWRIN.
- Official local evidence: [TPS2663 Rev.G](../datasheets/power/tps2663_datasheet_rev_g.pdf), targeted pin/limit/function inspection on pp.3-9, 19-21, 27-32; pp.19 and 30 visually inspected. No new manufacturer research or part selections. Graphify tools unavailable.
- KiCad **10.0.5**: all eight schematics loaded and force-resaved using `sch upgrade --force`; hierarchy then reopened by ERC and SVG export. All eight pages exported; root and Sheet 1 visually inspected. Interactive GUI opening was not exercised.
- **ERC: PASS for the empty hierarchy only**, zero reported violations across eight sheets; [raw report](phase_4a/erc.json). No exclusions or severity overrides added. KiCad's four default ignored categories remain listed in the report; none has relevant objects in this empty snapshot. This result does not validate a protection circuit or satisfy the Phase 4A implementation gate.
- Reproduce hierarchy/ERC and numerical checks: `python validation/phase_4a/verify_phase_4a.py [path-to-kicad-cli]`. Results: [verification_results.json](phase_4a/verification_results.json).
- Unknown/unperformed: concrete component selection, symbol audit, electrical connections, protection behavior, and loaded/ripple/startup performance. Resolve the identified contract conflict before continuing circuit work.

## Files created

- `hardware/kicad/`: `circuitBuilderAi-Astra.kicad_pro`, `circuitBuilderAi-Astra.kicad_sch`, `power_input.kicad_sch`, `power_regulation.kicad_sch`, `microphones_afe.kicad_sch`, `adau1978_adc.kicad_sch`, `adsp21569_dsp.kicad_sch`, `tas6424e_amplifier.kicad_sch`, `system_interfaces.kicad_sch`.
- This record; `validation/phase_4a/{verify_phase_4a.py,verification_results.json,erc.json}`; root/Sheet 1 SVG previews in `validation/phase_4a/rendered/`.
- Existing Phase 0-3 work and evidence left unchanged. Phase 4B not begun.

PHASE 4A: BLOCKED

---

## Resumed implementation — 2026-09-09

**Scope completed:** reused the existing project and seven-sheet hierarchy; implemented only Sheet 1 against [Phase 3A](../docs/phases/phase_3a_pgood_contract_correction.md). Sheets 2–7 are byte-identical to their pre-implementation snapshots. No board, placement, routing, or Phase 4B work.

- Power path: keyed J1 → F1 → CSD19537Q3 reverse blocker → TPS26630 → `12V_PROTECTED`; BSS138 follows TI Figure 9-2. Entry/local ceramics, one shared 470 uF bulk, and the approved **DNP** bidirectional TVS position are present.
- Preserved 12 V nominal, 10.8–13.2 V connector range, 11.5 V cold start, 4 A continuous/5 A short peak, +24 V/−14 V bounded faults, MODE-open latch-off, 3.24 k ILIM, and 47 nF dVdT. The revised ladder is 316 k/13.3 k/30.4 k, 0.1%.
- U1 PGTH is grounded; native PGOOD is explicitly unused. U2 `TPS3760A012DYYR` monitors protected OUT through 115 k/10.0 k, 0.1%, with 100 nF bypass; its RESET is `PGOOD_12V`, pulled up by 10.0 k to `3V8_PRE`. Both U2 grounds are connected; CTR/MR, CTS and reserved pins are explicitly NC.
- Five matching hierarchical ports expose protected power, return, 3V8_PRE, PGOOD and separate raw open-drain FLT. Root-boundary NC markers mean **later circuitry is absent**, not that these functions are optional. Sheet 2 must supply 3V8_PRE without PGOOD gating, provide the FLT pullup/conditioning and hardware-safe latch, and retain the frozen startup/reset rules. Neither status output connects directly to DSP logic here.

### Components and symbol verification

Exact orderable parts, packages and source URLs are in [Sheet 1 BOM](phase_4a/sheet1_bom.json). All symbols are cached in the schematic and in project-local `Astra_Power.kicad_sym`; no third-party pin map is accepted on trust.

| Ref | Manufacturer part / package | Authoritative check |
| --- | --- | --- |
| U1 | TI TPS26630RGER, RGE0024H 24-pin + EP25 | [SLVSE94G](../datasheets/power/tps2663_datasheet_rev_g.pdf), pp.3–9, 19–21, 27–32: all 25 pins, 4.5–60 V operation, −60/+67 V IN_SYS absolute limits, current/ramp and reverse topology. 53 mΩ maximum internal RON; nominal ILIM 5.556 A, tolerance screen 5.162–5.950 A. |
| U2 | TI TPS3760A012DYYR, DYY0014A 14-pin | [SBVS420A](../datasheets/power/tps3760_datasheet_rev_a.pdf), pp.4–8, 12–21 and ordering/package tables: VDD1, SENSE3, RESET6, GND8/13, CTR/MR9, CTS10; NC2/4/5/7/11/12/14. 2.7–65 V operation, 70 V absolute; 3.8 V/10 k pullup sinks only 0.38 mA versus 5 mA recommended limit. |
| Q1 | TI CSD19537Q3, SON 3.3 × 3.3 mm | [SLPS549B](../datasheets/power/csd19537q3_datasheet_rev_b.pdf), pp.1–3 and package drawing: **S1–3, G4, D5–8/EP**, visually checked. Symbol/common footprint pad 5 represents all drain contacts. 100 V VDS, ±20 V VGS; 9.7 A board-condition rating is not a thermal guarantee for the future PCB. |
| Q2 | onsemi BSS138LT1G, SOT-23 CASE318 style21 | [BSS138LT1/D Rev.14](../datasheets/power/bss138lt1_onsemi.pdf), pp.1–3, 7: **G1, S2, D3**, visually checked. 50 V VDS, ±20 V VGS; gate-discharge service, not the load-current path. |
| J1 | AMASS XT30PW-M30.G.Y, keyed horizontal THT, 3 mm tails | [Official catalog](../datasheets/power/amass_xt30_catalog.pdf), p.10, and retained product drawings: 2 contacts, 20 A maximum rating with stated temperature-rise condition; catalog specifies 500 V DC withstand. Logical schematic **1=+, 2=return** is a project assignment, not invented manufacturer numbering. Mechanical mating/pad mapping remains a pre-PCB check. |
| F1 | Littelfuse 0451010.MRL, Nano2 451, 6.10 × 2.69 mm | [451/453 official datasheet](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1), revised 12/01/25, pp.1–4: 10 A, 125 VDC, 400 A interrupt at 32 VDC, 5.6 mΩ **nominal** cold resistance; nonpolar terminals 1/2. Backup fault protection; U1 provides load limiting. |
| R1–R7 | Vishay TNPW0805…BYEA; exact seven MPNs in BOM | [Doc.28758, 10-Apr-2026](../datasheets/power/tnpw_resistors.pdf), pp.1–4: 0805, 0.1%, 10 ppm/K, 150 V, 0.14 W general mode. Nonpolar pins 1/2. Worst resistor dissipation is below 2 mW in the bounded input envelope. |
| C1–C3 | TDK C3216X7R1H105K160AB, 1206 | [Official part data](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R1H105K160AB): 1 uF, ±10%, X7R, 50 V, 3.2 × 1.6 × 1.6 mm; nonpolar pins 1/2. |
| C4 | Rubycon 25ZLH470MEFC10X12.5, radial D10 × 12.5 mm, pitch 5 mm | [ZLH official catalog](../datasheets/power/rubycon_zlh.pdf), pp.1–2: 470 uF ±20%, 25 V, 1.33 A ripple at 100 kHz/105°C, 0.039 Ω impedance at 20°C. **Pin1 positive, pin2 striped negative**; one bulk allocation shared with later amplifier circuitry. |
| C5 / C6 | KEMET C1206C473J5GACTU / C1210C104J5GACTU, 1206 / 1210 | [C1003 C0G, 20-Feb-2025](../datasheets/power/kemet_c0g.pdf), pp.1–3, 6, 8: 47 nF / 100 nF, ±5%, 50 V, C0G; selection tables visually checked; nonpolar pins 1/2. |
| D1 / TP1–TP6 | DNP SMC TVS reservation / bare copper test pads | No actual TVS or purchased test-point component selected. D1 has nonpolar A1/A2 terminals; test pads have one terminal. This preserves the explicit Phase 3 TVS decision. |

Custom U1/U2 pin tables and flattened Q1/Q2 mappings were checked against the official tables/drawings and independently checked against both local and schematic-cached symbols by [the audit script](phase_4a/verify_phase_4a_current.py). U1 pins 1/2=IN, 3=B_GATE, 4=DRV, 5=IN_SYS, 6=UVLO, 7=OVP, 8=GND, 9=dVdT, 10=ILIM, 11=MODE, 12=SHDN, 13=IMON, 14=FLT, 15=PGTH, 16=native PGOOD, 17/18=OUT, 19–24=NC, 25=grounded EP. U2 and J1 footprints are deliberately unassigned pending mechanical footprint verification; their schematic package/pin contracts are explicit.

### Validation result

- **KiCad 10.0.5 reload/resave and parsing: PASS.** Root and Sheet 1 were force-upgraded/resaved, then the entire hierarchy reopened by netlist, ERC and eight-page SVG export. Root and Sheet 1 previews were visually inspected. No interactive GUI-open claim is made.
- **ERC: PASS, 0 violations on 8 sheets**, [current raw report](phase_4a/erc_current.json). ERC exposed an accidental TVS-terminal connection during authoring; it was corrected and the complete exported netlist rechecked. No severity overrides or exclusions were added. Four stock ignored checks remain: single global label, four-way junction, schematic SPICE model and footprint filter. Explicit net/pin audit covers electrical connectivity; the separate transient fixture is not a schematic SPICE model.
- **Independent connection audit: PASS**, all 15 connected nets, 19 intentional device NC pins, five matching hierarchical interfaces, and unchanged later sheets. Source/post-passive power flags describe the external feed; they do not introduce a fictitious downstream supply.
- **Phase 3A corners: PASS**, including all resistor and independent leakage extrema. PGOOD fall **9.870314–10.130114 V**, rise **10.066952–10.333488 V**, hysteresis **0.196638–0.203374 V**. UVLO rise **9.582514–10.173066 V**, fall **8.875881–9.562892 V**; OVP rise **13.792560–14.606094 V**, fall **12.776849–13.728903 V**. Normal hold/assertion margins **269.886/66.512 mV**; separation before UVLO **307.422 mV**. The approved **10.4 V** minimum is unchanged.
- **Contract-level transient simulation: PASS**, ngspice-47, [fixture](phase_4a/power_input_transient.cir), [log](phase_4a/transient.log), [trace](phase_4a/transient_trace.csv). Each nominal/extreme PGOOD fixture asserts once during an 11.5 V startup, remains high at 10.4 V, and deasserts before UVLO opens; latest modeled safe request at 0.48305 s precedes UVLO at 0.55375 s. Recovery has the imposed nominal 1063.8 V/s dVdT slew. This validates the contract's ordering using ideal hysteretic switches and an imposed ramp, **not** transistor behavior, near-threshold delay over PVT, load dynamics, the absent downstream latch, or bench performance. Grounded PGTH and TI p.19 independently establish the selected controlled-recovery mode.
- Reproduce: `python validation/phase_4a/verify_phase_4a_current.py [kicad-cli] [ngspice]` (Python + sexpdata). [Machine results and artifact hashes](phase_4a/verification_current.json). Earlier `verify_phase_4a.py`, `erc.json` and `verification_results.json` remain historical empty-hierarchy evidence, not current circuit checks.

### Remaining limits and files

No unresolved Sheet 1 electrical connection or corrected-PGOOD issue prevents subsequent power-regulation implementation. **Pre-PCB/bench qualifications remain open:** total hot source-to-OUT drop ≤0.4 V at 4 A (U1 alone budgets 0.212 V; Q1, fuse, both connector contacts and copper must fit the remaining 0.188 V), connector temperature rise/mating, source short-circuit coordination, MLCC effective capacitance, bulk ripple, thermal behavior, and real fault/ramp timing. These were not replaced by typical-only numbers. AMASS's retained page prints contact resistance as `1.5 MΩ` and 600 V withstand while its catalog lists 500 V: the resistance entry is unusable and no milliohm guarantee is inferred. The insulation withstand exceeds the 30 V prototype requirement, but does not establish a separate certified working-voltage classification. Retain the connector as a provisional mechanical selection; qualify contact drop and the selected mate before PCB release. TVS/surge compliance remains intentionally undefined under Phase 3.

Files changed for this resumed implementation: `hardware/kicad/{power_input.kicad_sch,circuitBuilderAi-Astra.kicad_sch}`; added `Astra_Power.kicad_sym` and `sym-lib-table`. Current supporting artifacts are `validation/phase_4a/{build_power_input.py,verify_phase_4a_current.py,sheet1_bom.json,later_sheet_hashes.json,erc_current.json,power_input.net.xml,power_input_transient.cir,transient.log,transient_trace.csv,verification_current.json,rendered_current/}` and this appended record. Targeted new manufacturer files used above are retained under `datasheets/power/`; [source notes](../datasheets/power/phase_4a_source_notes.md) record web-only evidence and document identity. No Phase 3 contract or later sheet was edited by this implementation.

PHASE 4A: PASS
