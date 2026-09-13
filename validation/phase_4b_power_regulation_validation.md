# Phase 4B power regulation / sequencing validation

Date: 2026-09-13. **Implementation stopped before schematic changes.**

## Blocking finding: supervisor release margins

**CONFLICTING:** [Phase 3](../docs/phases/phase_3_schematic_readiness.md) sections 6.1-6.2 freeze TPS386000RGPR dividers and require deterministic startup. Section 6.1 checks falling thresholds against the realized rail minima, but omits positive-going hysteresis from the startup qualification. [TI TPS386000/TPS386040, SBVS105F Rev.F](../datasheets/power/tps386000_datasheet_rev_f.pdf), section 6.5 p.7, specifies `VITN = 396-404 mV` and `VHYSN = 3.5 mV typical, 10 mV maximum`. Figure 3 p.9 and section 8.3.4 p.23 establish release at the upper hysteresis boundary. The 14-24 ms delay begins after qualification; waiting longer cannot qualify a rail below that boundary. The electrical table and timing diagram were visually inspected.

For each frozen 0.1% divider, even with **zero sense current**:

`Vrelease,max = (0.404 + 0.010) * (1 + Rtop*1.001/(Rbottom*0.999))`.

| Monitored rail / channel | Frozen divider, top/bottom | Phase 3 minimum rail | Maximum release threshold, zero leakage | Startup margin |
| --- | --- | ---: | ---: | ---: |
| `1V8_DSP_REF_ANA` / SENSE1 | 33.8 k / 10.0 k | 1.775 V | 1.816121 V | -41.121 mV |
| `1V0_DSP_CORE` / SENSE2 | 14.3 k / 10.0 k | 0.990 V | 1.007205 V | -17.205 mV |
| `1V35_DSP_DMC` / SENSE3 | 22.5 k / 10.0 k | 1.325 V | 1.347365 V | -22.365 mV |
| `3V3_SYS` / SENSE4L | 69.8 k / 10.0 k | 3.267 V | 3.309505 V | -42.505 mV |

These allowed tolerance combinations defeat a guaranteed-startup claim; they do not predict that every unit will fail. No threshold/hysteresis correlation excluding these combinations is specified. The additional p.7 sense-current screen (`+25 nA`, specified at 0.42 V) raises the respective release bounds to 1.816967, 1.007563, 1.347928 and 3.311252 V. The blocker does not depend on extrapolating that current specification: it already exists at zero leakage. Regulator divider errors, feedback current, ripple and trace drops were not needed to establish it.

**Consequence:** RESET1 can remain asserted with a valid 1.8 V rail, keeping all five dependent regulators disabled. Even if it releases, the other channels can prevent DSP reset release with otherwise valid rails. A deterministic startup cannot be implemented with the frozen guaranteed ranges.

**Required resolution:** an approved correction to the Phase 3 rail/supervisor contract that demonstrates both falling fault thresholds above device minima and rising release thresholds below worst-case realized rails, including tolerances, hysteresis and sense current. Recheck restart/shutdown and power margins against that correction before resuming Sheet 2. No replacement part, divider or rail value was selected or approved here.

## Implementation and validation status

- Implemented rails/components: **none in Phase 4B**. Sheet 2 remains its existing placeholder. Planned sources remain TPS62135 for `3V8_PRE`, `1V0_DSP_CORE`, `3V3_SYS`; TPS7A4901 for `1V8_DSP_REF_ANA`, `1V35_DSP_DMC`, `5V_AFE`; TPS7A2033PDBVR for `3V3_ADC_A`; TPS7A2028PDBVR for `2V8_MIC`.
- Phase 3 load allocations (not newly verified populated loads): pre-rail 1.8 A, core 3.0 A, reference/analog 75 mA, DMC 50 mA, system 200 mA, ADC analog 30 mA, microphones 5 mA, AFE 50 mA. Full regulator load/current, feedback, headroom, dissipation, passive selection and symbol/pin checks remain **NOT PERFORMED** after the blocking finding. No component implementation approval is implied.
- Power sequencing: **BLOCKED** by the release margins above. No startup/shutdown circuit, hardware-safe latch, reset/enable interface or simulation was created. Bench ramp validation remains unperformed.
- System PGOOD: [Phase 3A](../docs/phases/phase_3a_pgood_contract_correction.md) and the resumed [Phase 4A PASS record](phase_4a_power_input_validation.md) remain controlling: protected minimum 10.4 V; PGOOD falling 9.870314-10.130114 V and rising 10.066952-10.333488 V. Sheet 1's threshold network and hierarchical signal are unchanged. The new blocker is downstream TPS386000 qualification, not TPS3760 PGOOD.
- **ERC/reload: NOT RUN for Phase 4B**, because no KiCad artifact was changed and implementation stopped. KiCad CLI exists at `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe`; this is not tool inability. The historical Phase 4A ERC result is not a Phase 4B circuit validation.
- Evidence scope: only the requested authoritative documents, the existing evidence index and targeted local TPS386000/TPS7A49 sections were read. No broad datasheet research. Graphify tools unavailable. An attempt to open the official TI supervisor URL through the web tool failed; the retained PDF hash matches the evidence index, and its local contents support this finding.
- Reproduce numerical checks and evidence hash: `python validation/phase_4b/verify_supervisor_release.py`. [Results](phase_4b/supervisor_release_results.json) preserve all four failed margins. Successful execution reproduces a **BLOCKED** engineering result.

## Files changed

Created this record and `validation/phase_4b/{verify_supervisor_release.py,supervisor_release_results.json,tps386000_p7.png,tps386000_p9.png}`. All KiCad files, Sheet 1, Phase 3/3A documents and later sheets remain unchanged. No PCB, placement, routing or Phase 4C work.

PHASE 4B: BLOCKED

## Resumed under Phase 3B — 2026-09-13

The original TPS386000 blocker above is **resolved by the approved [Phase 3B correction](../docs/phases/phase_3b_power_supervisor_correction.md)**. LTC2964HUDC#PBF and TPS3431SDRBR remain selected. No alternative supervision architecture was evaluated. Implementation stopped before schematic edits on the separate regulator finding below.

### Blocking finding: system buck accuracy condition

**CONFLICTING:** Phase 3 sections 5.1/6.1 freeze TPS62135, forced PWM, from `3V8_PRE` to `3V3_SYS`, and claim a 3.267–3.333 V realized output. [TI TPS62135, SLVSBH3B Rev.B](../datasheets/power/tps62135_datasheet_rev_b.pdf), section 7.5 p.6, guarantees +/-1% **feedback** accuracy only with `VIN >= VOUT + 1 V`. Even granting the frozen pre-rail's 3.80 V +/-1% range, its maximum 3.838 V is below `3.267 + 1 = 4.267 V` by 429 mV. The entire frozen system-rail operating interval misses that condition. Section 9.4.3 pp.10–11 describes small-headroom/100%-duty operation but supplies no replacement guaranteed accuracy bound for this branch. This establishes an evidence gap, not a prediction that the converter cannot regulate. The table and its footnote were visually checked; [p.6 image](phase_4b/tps62135_p6.png) retained. The official TI online Rev.B also agrees.

**Consequence:** the system rail's guaranteed minimum is **UNKNOWN** for the frozen implementation. Consequently the Phase 3B V4 release allowance cannot yet be certified in hardware. A typical curve, nominal dropout estimate, or ERC cannot supply the missing guaranteed bound. Changing the regulator, input connection, rail setting, or approved margins here would change the frozen contract.

**Resolution required:** manufacturer-backed guaranteed output bounds for the exact branch over its approved load/temperature/input envelope, including feedback-network errors, or an approved power-contract correction establishing those bounds. No correction was selected in this task.

### Corrected supervision and validation status

The following are the **unchanged approved Phase 3B values**, not new calculations or implemented-circuit results:

| Rail | Guaranteed fall = rise range | Release / fault margin |
| --- | ---: | ---: |
| `1V8_DSP_REF_ANA` | 1.733427–1.756604 V | +18.396 / +23.427 mV |
| `1V0_DSP_CORE` | 0.959608–0.971404 V | +18.596 / +9.608 mV |
| `1V35_DSP_DMC` | 1.295641–1.312379 V | +12.621 / +12.641 mV |
| `3V3_SYS` | 3.157969–3.202097 V | +64.903 / +27.969 mV |

- Four-rail implementation/margin retention and DSP startup/reset sequencing: **BLOCKED / not implemented**. The 330–470 ms reset-release contract remains frozen; no transient or bench validation was performed.
- Component/package/symbol and complete external-network verification: **incomplete**; no newly implemented components or symbols. No implementation approval is implied by the targeted datasheet checks.
- Save/reload and ERC: **NOT RUN**, because no schematic was changed before the controlled stop; no new ERC result or waiver is claimed.
- Scope: read only the five requested repository documents and targeted referenced manufacturer datasheets. No Sheet 1 contradiction was found. All KiCad files remain unchanged; no later-sheet, PCB, placement, routing, or Phase 4C work.
- Files changed in this resume: appended this validation record; created `validation/phase_4b/tps62135_p6.png`. Original BLOCKED history and artifacts preserved.

PHASE 4B: BLOCKED

## Resumed under Phase 3C — 2026-09-13

The previous system-buck blocker is **resolved by [Phase 3C](../docs/phases/phase_3c_3v3_regulator_correction.md)**. Its corrected input, divider, SN74LV1T08 enable gate, static range, and +54.202/+27.969 mV supervision margins remain approved and unchanged. The remaining feedback/output-bound check found a separate **CONFLICTING** pre/core contract before schematic entry.

### Blocking finding: remaining buck output bands and core release margin

[TPS62135 Rev.B](../datasheets/power/tps62135_datasheet_rev_b.pdf), section 7.5 p.6, specifies +/-1% feedback accuracy and 70 nA maximum FB leakage; section 10.1.1 p.13 defines the divider transfer. Applying the Phase 3C conservative leakage-sign treatment to the other frozen 0.1% dividers gives:

`Vmin = 0.7*0.99*(1 + Rt*0.999/(Rb*1.001)) - 70nA*Rt*0.999`

`Vmax = 0.7*1.01*(1 + Rt*1.001/(Rb*0.999)) + 70nA*Rt*1.001`

| Rail / frozen top-bottom divider | Approved band | Calculated static feedback-network bounds |
| --- | ---: | ---: |
| `3V8_PRE` / 442k-100k | 3.762–3.838 V | 3.719031–3.869167 V |
| `1V0_DSP_CORE` / 42.7k-100k | 0.990–1.010 V | 0.985334–1.012485 V |

Even at **zero leakage**, the lower corners are 3.749940 V and 0.988320 V, respectively, below the approved minima. Thus the discrepancy does not depend on assuming negative leakage. Divider error and nominal set-point offset were not included in the frozen output bands.

With the **unchanged** approved LTC2964 core rising maximum of 0.971404 V, calculated release allowance becomes `0.985333758 - 0.971404 = 13.929758 mV`, below the required **18.596 mV**. It remains positive, and the static core bounds remain inside 0.95–1.05 V, but the required margin-preservation check fails. The +9.608 mV comparator fault margin is unchanged. No supervisor threshold was recalculated or changed.

**Required resolution:** an approved correction to the pre/core feedback networks or their realized-range/margin contracts, with dependent rail and enable bounds checked. These calculated bounds are findings, not newly approved rail ranges. No alternative architecture or replacement values were selected.

### Validation and scope

- **Calculated:** pre/core accuracy headroom remains sufficient, with 5.530833 V and 1.706546 V beyond the required 1 V, using the wider calculated bounds. Executed `python validation/phase_4b/verify_remaining_buck_bounds.py`; [results](phase_4b/remaining_buck_bounds_results.json) retain numerical precision and the source PDF hash. Successful script execution records a **BLOCKED** engineering result.
- **Not completed after the stop:** populated-load margins, LDO bounds/losses, buck thermal/ripple/transient checks, inductor and capacitor selection/bias checks, symbol audits, implemented sequencing and all-rail margin retention. No physical performance was measured.
- **Implementation, save/reload, ERC:** not performed; no KiCad file changed. Sheet 1, all later sheets, and Phase 3/3B/3C records remain untouched. No PCB or Phase 4C work.
- **Files changed:** appended this record; added `validation/phase_4b/verify_remaining_buck_bounds.py` and `validation/phase_4b/remaining_buck_bounds_results.json`. All previous BLOCKED history preserved.

PHASE 4B: BLOCKED


## Resumed under Phase 3D ? 2026-09-13

**Result: partial Sheet 2 entry; BLOCKED by a commanded-shutdown connectivity conflict.** The three earlier electrical-bound blockers above are resolved by the approved Phase 3D correction. Their history is preserved. No rail, divider, supervisor threshold, input source, or enable dependency was changed to obtain a pass.

### New implementation blocker: shared enable versus ordered microphone power-off

**CONFLICTING:** [Phase 3D](../docs/phases/phase_3d_final_power_contract_audit.md) sections 9.1(5) and 11(6) require LTC2964 `OUT1` to directly enable core, DMC, ADC, and microphone regulators. Section 9.2 retains commanded shutdown with microphones off before ADC reset, DSP reset, the >=20 ms wait, and core/DMC power-off. [Phase 3 section 6.3](../docs/phases/phase_3_schematic_readiness.md) explicitly calls this step disabling **microphone power**, not merely ignoring microphone samples.

The exported Sheet 2 netlist establishes the problem at the actual device pins:

| Required connection | Implemented pin | Net |
| --- | --- | --- |
| Core buck EN | U202.8 | `OUT1` |
| DMC LDO EN | U205.5 | `OUT1` |
| ADC LDO EN | U207.3 | `OUT1` |
| Microphone LDO EN | U208.3 | `OUT1` |

With `OUT1=1`, all four regulators are enabled. With `OUT1=0`, all four are disabled. There is no control state that disables microphone power while retaining core/DMC enable for the subsequent reset/wait steps. Output capacitance or unequal discharge rates do not provide independent enable control or a guaranteed commanded sequence. Firmware delays cannot create the missing control state.

**Resolution required:** approve the explicit commanded-shutdown controls and their relationship to the frozen `OUT1` fanout, or formally correct the shutdown requirement. The correction must specify default states and hardware-fault dominance while preserving the approved rail/supervisor margins. No extra enable gate, load switch, shutdown signal, or replacement shutdown order was selected here. This is an implementation connectivity finding; the power-architecture audit was not repeated. Absence of physical hardware is **not** the blocker.

### Entered circuitry and checks

[Sheet 2](../hardware/kicad/power_regulation.kicad_sch) now contains **124 components plus three power flags**, explicitly marked `4B-BLOCKED`. The hierarchy root connects the five existing Sheet 1 ports to Sheet 2. Future load-sheet ports remain terminated at the root. This is an incomplete circuit, not schematic-completion approval.

- **Entered and checked:** all eight regulators, exact Phase 3D feedback networks, all five permanent 0.1% preloads, local regulator capacitors, three 1 uH buck filter positions, independent 10 nF buck soft starts, LDO CFF/NR networks, DMC domain bulk, six DNP adjustment capacitors, LTC2964 configuration/sense dividers/pullups, TPS3431 configuration/reset pullup, SN74LV1T08 system enable gate and 1.0 MOhm pulldown, and rail/sense/enable/status/reset test access.
- **Pin/package checks:** TPS62135 pp.3/44?46 (RGX0011A, 11 pads, no invented EP); TPS7A49 pp.4/33?35 (DGN0008D, EP numbered 9 in the library); TPS7A20 p.4 (DBV); LTC2964 Rev.0 pp.2/8?9/19 (UDC, EP21); TPS3431 pp.3/28?30 (DRB0008A, EP9); SN74LV1T08 Rev.F pp.4/24?26 (DBV). Cached symbol pin names/numbers/types and footprint pad-number sets were checked. TPS7A49 DNC7 remains unconnected; all required thermal/ground pads connect to `POWER_GND`. Dividers, preloads, inductors, and ceramic capacitors are nonpolar; every feedback and supervisor arm was checked by net identity.
- **Configured rail bounds:** all eight populated feedback/fixed-output settings reproduce Phase 3D to its displayed rounding precision. These are conditional regulation bounds, not measured outputs; AFE remains deliberately disabled in this partial entry.

| Monitored rail | Configured static min/max, V | Unchanged fall = rise limits, V | Release / fault allowance, mV |
| --- | ---: | ---: | ---: |
| `1V8_DSP_REF_ANA` | 1.776066 / 1.875487 | 1.733427 / 1.756604 | 19.462 / 23.427 |
| `1V0_DSP_CORE` | 0.991476 / 1.013338 | 0.959608 / 0.971404 | 20.072 / 9.608 |
| `1V35_DSP_DMC` | 1.325693 / 1.395966 | 1.295641 / 1.312379 | 13.314 / 12.641 |
| `3V3_SYS` | 3.256299 / 3.337821 | 3.157969 / 3.202097 | 54.202 / 27.969 |

The other configured ranges are `3V8_PRE=3.746849?3.841293 V`, `3V3_ADC_A=3.2505?3.3495 V`, `2V8_MIC=2.758?2.842 V`, and `5V_AFE=4.858943?5.157889 V`. The pre operating band remains 3.700?3.900 V. The five preload minimum currents are respectively **1.050, 1.068, 1.033, 1.079, and 1.080 mA** for reference/analog, DMC, AFE, ADC, and microphones; maximum dissipation is below 5.67 mW, within the specified 0.1 W resistor rating. Full-precision results are retained in [the verification JSON](phase_4b/sheet2_verification_results.json).

**Incomplete after the controlled stop:** hardware-safe fault aggregation/latching; buffered AFE command/open-drain override; commanded-shutdown control; complete populated-load/BOM confirmation; and final passive-orderable qualification. `AFE_EN` has its required 100 kOhm pulldown and test point but is intentionally not driven by `AFE_EN_CMD`; U206 is held off. `EFUSE_FLT_N` is exposed but not yet aggregated into reset/safe-state logic. Do not infer complete fault dominance from the populated supervisor/watchdog alone. No later-sheet buffer, DSP, ADC, microphone, amplifier, or consumer-side filter circuit was entered.

Local capacitor nominal values and procurement limits are annotated: 10 uF inputs; two 22 uF output positions on pre/system; three 47 uF on core; 10 uF LDO outputs; 47 uF DMC bulk; and the exact frozen timing/feed-forward values. The selected capacitor voltage ratings meet the contract. Effective capacitance, ESR, aging, bias, distributed-capacitance totals, and exact orderables are **not fully qualified**. The inductor footprint and 1 uH/5 A/30 mOhm/effective-inductance requirements are entered; the XAL4020-102MEC note is a **candidate**, not a claim that its tolerance/bias envelope has passed. This partial entry is not a procurement BOM. No thermal, ripple, PSRR, transient, back-powering, or rail-ramp simulation/measurement was performed. Those future physical validations are not used as a reason to block this schematic task.

### Native KiCad reload, ERC, and retained findings

The previously recorded `C:/Program Files/KiCad/10.0` path was absent. Official KiCad **10.0.6** was installed through its signed/hash-verified Windows distribution and used at `%LOCALAPPDATA%/Programs/KiCad/10.0/bin/kicad-cli.exe`. Native `sch upgrade --force` loaded/resaved the complete hierarchy in an isolated copy; only the authorized root and Sheet 2 were copied back. ERC and XML-netlist/PDF exports then reloaded the actual final project. Sheet 1 and later sheets remain byte-identical to their pre-task hashes.

**ERC was executed; it is not reported as clean.** The [initial report](phase_4b/sheet2_erc_initial.json) had 118 findings. Registering the installed standard footprint libraries corrected 109 environment-related link warnings. Adding explicit power flags on the actual buck output sides of the series inductors corrected the reported missing power driver; the flags represent shown regulator sources and do not invent supply circuitry. The [final raw report](phase_4b/sheet2_erc_final.json) retains **3 errors and 5 warnings**:

- Three `pin_to_pin` errors: U201/U202/U203 FB2 open-drain pins connect to ground, which includes Sheet 1's ground power flag. **Reviewed intentional connection:** Phase 3D section 8 explicitly requires `FB2 grounded` and `VSEL low`; TPS62135 p.3 defines FB2 as the internal ground-switch drain. Disconnecting FB2 to silence ERC would violate the contract. This record documents the engineering disposition; no GUI exclusion or global severity suppression was added, and the raw errors remain visible.
- Five `endpoint_off_grid` warnings: root-level wires connect the pre-existing off-grid Sheet 1 hierarchy port positions to Sheet 2. Connectivity is present in KiCad's exported netlist. These are drawing-grid findings, not PCB/clearance findings. The original Sheet 1 port geometry was retained.

No new ERC rule exclusions were introduced. KiCad's four default ignored checks (single global label, four-way junction, simulation model, footprint filter) are listed in the results JSON; they are not evidence of analog simulation or complete electrical correctness. ERC cannot detect the contradictory commanded sequence or prove the still-missing safe-state circuit.

Reproduce: `python validation/phase_4b/verify_sheet2.py` (requires `sexpdata` and the recorded KiCad installation). The script exports the real netlist, checks configured values/connectivity/pin and package mappings/margins/preloads, verifies unchanged protected files, and stores the exhaustive two-state common-enable truth table. Its successful execution reproduces **BLOCKED**, not a phase PASS. [Sheet 2 review PDF](phase_4b/sheet2_review.pdf) and [component manifest](phase_4b/sheet2_components.json) expose the partial implementation for review.

### Files and scope

Modified: `hardware/kicad/power_regulation.kicad_sch`, the hierarchy root `hardware/kicad/circuitBuilderAi-Astra.kicad_sch`, `hardware/kicad/sym-lib-table`, and this append-only validation record. Added: `hardware/kicad/Astra_Sequencing.kicad_sym`, `hardware/kicad/fp-lib-table`, the verified RGX package-library file under `hardware/kicad/Astra_Sequencing.pretty/`, `datasheets/power/sn74lv1t08_datasheet_rev_f.pdf`, and the `validation/phase_4b/` build/integration/check scripts, manifests, native reports, netlist, PDF, source-page images, and hashes. The package-library file is not a PCB layout.

Manufacturer sources were consulted only for the Phase 3D-required pin/package/passive/control implementation detail. The LTC2964 official PDF was readable through the manufacturer endpoint in the web tool, but attempts to retain its PDF locally timed out; the same source limitation noted in Phase 3B remains explicit. No alternative regulator was selected. Sheet 1, its symbol library, all later sheets, the existing phase contracts, and the user's pre-existing document edits were not modified. No PCB, placement, routing, Phase 4C, or Git commit was created.

PHASE 4B: BLOCKED
