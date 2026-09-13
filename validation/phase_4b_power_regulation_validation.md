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


## Resumed under Phase 3D + Phase 3E ? 2026-09-13

**Result: BLOCKED before new schematic changes by the exact MCLK/safe-arm dependency.** The previous direct-OUT1 shutdown blocker is resolved at the contract level by Phase 3E. It is not the reason for this new gate. Existing Sheet 2 remains the previously recorded partial entry; none of the new Phase 3E circuitry is claimed as implemented.

### Concrete implementation contradiction: pre-arm ADC checks require a post-arm clock

**CONFLICTING:** while assigning the required tenth SN74LV1T08 (audio/MCLK release) and its startup default, these mandatory dependencies meet at the same signal:

| Controlling requirement | Consequence at the proposed Sheet 2 control interface |
| --- | --- |
| [Phase 3E section 6](../docs/phases/phase_3e_shutdown_safe_state_correction.md): audio and MCLK OEs release only through `HW_RUN_LATCHED AND AUDIO_OE_CMD`, with passive-disabled OE/NMOS topology | With the safe latch cleared, setting `AUDIO_OE_CMD=1` cannot enable the ADC MCLK translator or serial-clock buffer. |
| Phase 3E section 3.4: the deliberate arm edge follows boot and rail/clock/ADC/amplifier checks; section 5.1 step 7 initializes/verifies ADC before `SAFE_ARM_CMD` | Firmware cannot arm first and then perform the required initial ADC checks without changing the prescribed sequence. |
| [Current Phase 3D section 9.1 item 9](../docs/phases/phase_3d_final_power_contract_audit.md): arming follows successful PLL/configuration checks; [current Phase 3 section 10.1 step 6](../docs/phases/phase_3_schematic_readiness.md): provide MCLK/BCLK/FSYNC and poll PLL lock, **then** pulse `SAFE_ARM_CMD` | The retained ADC check explicitly includes PLL lock, rather than merely an I2C register read. Phase 3E also retains the pre-arm ADC-check requirement. |
| [ADAU1978 Rev.B](../datasheets/adc/adau1978_datasheet_rev_b.pdf), pp.12?14,29 | Stable input clocks are required for PLL startup. The selected MCLK mode takes its reference from MCLKIN (pin 7); PLL_LOCK is register 0x01 bit 7, reset value zero. |

The dependency is `arm -> enable MCLK -> acquire/check ADC PLL lock -> permission to arm`. Starting from the specified cleared latch, both possible values of `AUDIO_OE_CMD` leave the translated MCLK disabled. Waiting longer cannot supply a missing input clock. The same required reinitialization/rearm relationship applies after the safe latch is cleared by a fault. The root oscillator being operational does not deliver its clock through a disabled translator. No alternate clock mode or clock path is authorized here.

This is an implementation prerequisite conflict, established without a new rail or power-architecture audit. No alternative component or substitute logic was researched or entered to resolve it. It is not a shortage of physical measurements. In accordance with the task's prohibition on new sequencing decisions and AGENTS.md section 25, schematic entry stopped rather than silently changing the arm order or the prescribed OE equation.

**Resolution required:** an authoritative correction must define a realizable relationship between initial ADC clock/PLL validation and hardware-safe arming, including startup and fault recovery, while retaining default mute/standby/analog-off behavior. That sequencing decision cannot be supplied by ERC or a passive-value change. This record does not approve a replacement sequence.

### Checks actually executed on this resume

- Read the five requested governing files and targeted manufacturer sections for new symbol pins, timer/translator/switch behavior, and the concrete ADC clock dependency. No Phase 3B/3C document or evidence-index content was consulted on this resume.
- Executed [verify_phase3e_startup_dependency.py](phase_4b/verify_phase3e_startup_dependency.py). Its necessary-condition reachability model grants all rails, reset, oscillator and other prerequisites valid, and even permits instantaneous PLL verification once clocks arrive. The only reachable `(HW_RUN_LATCHED, PLL_check_passed)` state is `(0,0)`. This is a contract logic check, **not SPICE, a final implemented-netlist sequencing test, or a physical transient measurement**.
- KiCad 10.0.6 natively loaded/resaved Sheet 2 and the hierarchy root in a temporary project copy. No temporary saved design was copied back. Fresh ERC and XML export then loaded the unchanged production project. The newly created local-preference cache was removed; all production hardware files remain byte-identical.
- Compared values, footprints and connected pin/net assignments for **all 124 previously entered Sheet 2 components** against the preserved manifest. They agree. Existing feedback/preload/supervisor networks therefore remain unchanged from the earlier 286-check Phase 3D validation; no new rail-bound or architecture audit was substituted for that result. The existing enable circuitry still needs the Phase 3E replacement and is not certified by this comparison.
- [Results and per-item ERC dispositions](phase_4b/phase3e_resume/startup_dependency_results.json), [fresh raw ERC](phase_4b/phase3e_resume/existing_sheet2_erc.json), [fresh exported netlist](phase_4b/phase3e_resume/existing_project.net.xml), and [resume baseline hashes](phase_4b/phase3e_resume/resume_baseline.json) preserve the evidence. All previous validation bytes and historical artifacts are hash-checked and preserved.

### Re-evaluation of the previous 3 errors / 5 warnings

Fresh ERC again reports **3 errors and 5 warnings** on the existing partial design. Each remaining item is classified below and individually recorded with its original UUID in the results JSON. None was suppressed, retyped or disconnected to obtain a lower count.

| Remaining ERC item | Classification | Engineering disposition |
| --- | --- | --- |
| U201 pin 4 FB2 to ground power output | JUSTIFIED / INTENTIONAL | Phase 3D section 8 mandates grounded FB2 with VSEL low; the Sheet 1 ground power flag triggers the output-type check. |
| U202 pin 4 FB2 to ground power output | JUSTIFIED / INTENTIONAL | Same mandatory FB2 configuration. |
| U203 pin 4 FB2 to ground power output | JUSTIFIED / INTENTIONAL | Same mandatory FB2 configuration. |
| Root `12V_PROTECTED` interface wire endpoint off grid | JUSTIFIED / INTENTIONAL | Preserves the existing Sheet 1 port position; exported connectivity agrees. |
| Root `POWER_GND` interface wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same retained Sheet 1 geometry and verified connectivity. |
| Root `3V8_PRE` interface wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same retained Sheet 1 geometry and verified connectivity. |
| Root `PGOOD_12V` interface wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same retained Sheet 1 geometry and verified connectivity. |
| Root `EFUSE_FLT_N` interface wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same retained Sheet 1 geometry and verified connectivity. |

Newly FIXED items on this resume: **none**. Unresolved BLOCKING ERC items in this fresh report: **none**. The **blocking contract dependency and incomplete safe-state implementation remain**, irrespective of ERC. This is explicitly not the requested post-completion ERC acceptance: the missing circuitry could not be completed under the contradictory clock/arm requirements.

### Scope, outstanding work and files

No production KiCad file, Sheet 1, later sheet, symbol, footprint, or authoritative phase document was modified. The user's pre-existing document and datasheet changes were preserved. No PCB, placement, routing, Phase 4C work, or Git commit was created.

Modified on this resume: this append-only validation record. Added: `validation/phase_4b/verify_phase3e_startup_dependency.py` and the three reports plus baseline under `validation/phase_4b/phase3e_resume/`. Previous BLOCKED history and artifacts are unchanged.

Still unimplemented: the Phase 3E retained latch/timer, independent microphone/AFE gating, command translator, safe latch/fault aggregation, endpoint-release controls and fourteen paired-domain analog switches. Accordingly, complete startup/shutdown/brownout/watchdog safety, powered-off-domain behavior, and the **20.415?40.946 ms implemented post-reset hold are not verified**. Exact CTS effective-capacitance qualification, populated load totals and the remaining physical validations remain outstanding; absence of hardware is not the cause of this gate.

PHASE 4B: BLOCKED


## Resumed under Phase 3D + Phase 3E + Phase 3F - 2026-09-14

**PHASE 4B: PASS for Sheet 2 regulation/sequencing and its controlled interfaces.** Phase 3F resolves the previous MCLK/arming dependency. All prior BLOCKED entries remain historical and are preserved byte-for-byte. No rail, feedback ratio, preload, supervisor threshold or regulator was changed to obtain this result.

### Implemented scope and later-sheet boundary

[Sheet 2](../hardware/kicad/power_regulation.kicad_sch) contains **248 components plus three power flags**: 43 ICs, 3 OE-sink MOSFETs, 3 inductors, 68 resistors, 75 capacitors and 56 test points. The root hierarchy connects the five existing Sheet 1 power/status interfaces. Future endpoint interfaces terminate explicitly at the root.

The requested control and isolation circuits are consolidated on Sheet 2: the command translator, ADC reset assertion buffer, OE sinks and fourteen TMUX2821 devices accompany the rail/sequencing hardware. This implements their approved electrical functions without adding microphone, op-amp, ADC, DSP or amplifier load circuitry. Later implementation must use these existing interface circuits rather than duplicate them from the earlier sheet-plan component lists.

**The Sheet 2-only boundary matters:** ASDLJ/LMK clock generation, SN74AXC2T245 MCLK translation, SN74LVC244A clock/data banks, ADC DVDD CEXT/REXT, ADC PLL registers, flash/boot straps and endpoint clock/DVDD test points remain assigned to later sheets. They were not implemented here. Sheet 2 implements the sources, gate equations, passive defaults and named OE/reset connections that those circuits require. Its drawing records the exact ADC DVDD/reset constraints. The resulting clock/startup verification is a control-interface dependency verification, not a claim that an unimplemented ADC or clock buffer has produced a waveform. No Sheet 3-7 schematic file was modified; no PCB, placement, routing or Phase 4C work occurred.

### Rail, passive and supervision acceptance

The native exported netlist was checked against the Phase 3D contract, including complete series feedback arms, regulator pin assignments, enable nets, polarity, permanent preloads, NR/SS/CFF networks and supply sources.

| Rail | Feedback or fixed setting; permanent preload | Static output bounds, V | Result |
| --- | --- | --- | --- |
| `3V8_PRE` | 44.2k / 10.0k; forced PWM | 3.746849-3.841293 | PASS |
| `1V0_DSP_CORE` | 4.32k / 10.0k; forced PWM | 0.991476-1.013338 | PASS |
| `3V3_SYS` | 37.1k / 10.0k; forced PWM from `12V_PROTECTED` | 3.256299-3.337821 | PASS |
| `1V8_DSP_REF_ANA` | (54.2k + 100 ohm) / 100k; 1.69k preload | 1.776066-1.875487 | PASS |
| `1V35_DSP_DMC` | 14.9k / 100k; 1.24k preload | 1.325693-1.395966 | PASS |
| `5V_AFE` | 324k / 100k; 4.70k preload | 4.858943-5.157889 | PASS |
| `3V3_ADC_A` | TPS7A2033PDBVR; 3.01k preload | 3.250500-3.349500 | PASS |
| `2V8_MIC` | TPS7A2028PDBVR; 2.55k preload | 2.758000-2.842000 | PASS |

All feedback, supervision and preload resistors retain 0.1% tolerance. The five preload minimum currents remain 1.050/1.068/1.033/1.079/1.080 mA. Buck MODE/VSEL/FB2/VOS, 1 uH inductors, 10 nF independent soft starts and specified capacitor banks remain intact. TPS7A49 NR/SS is 47 nF for reference/DMC and 10 nF for AFE; every adjustable LDO retains 10 nF across its complete upper feedback arm. Consumer-side ferrite/decoupling networks remain later-sheet work; their absence does not change a Sheet 2 rail definition.

LTC2964 divider/threshold checks remain unchanged:

| Channel | Upper/lower divider | Rise = fall bounds, V | Release / fault margin, mV |
| --- | --- | --- | --- |
| V1, reference | 24.9k / 10.0k | 1.733427-1.756604 | 19.462 / 23.427 |
| V2, core | 9.31k / 10.0k | 0.959608-0.971404 | 20.072 / 9.608 |
| V3, DMC | (15.8k + 280 ohm) / 10.0k | 1.295641-1.312379 | 13.314 / 12.641 |
| V4, system | 53.6k / 10.0k | 3.157969-3.202097 | 54.202 / 27.969 |

Phase 3B/3D margin floors are preserved; the Phase 3C system source/divider architecture is preserved. Phase 3E's 100k destination EN pulldown supersedes the earlier 1M system EN pulldown. The Sheet 1 protected-input thresholds and PGOOD pullup are untouched. R382 supplies the required 10k eFuse-fault pullup on Sheet 2; native connectivity showed that this pullup was not already on Sheet 1.

### Implemented sequencing and safe defaults

- U221 (`U_SEQ_RUN`) and U225 (`U_DOWN_DELAY`) retain commanded service-off independently of DSP/system power. U224's two open-drain channels assert `SYS_HWRST` from the retained state or low PGOOD. No pre-powered output sources current into the system reset node.
- U211/U212 implement `DOWNSTREAM_EN = OUT1 AND PGOOD_CLEAN AND DOWNSTREAM_RUN_DELAYED`. It drives core, DMC, system and ADC-analog EN, each with a local 100k pulldown. No regulator EN remains directly on `OUT1`. Pre stays enabled directly; reference/analog stays enabled by raw `PGOOD_12V`.
- U222 is the hardware-safe latch. U214-U216 produce `SAFE_HW_CLEAR_N`; U228 adds continuous `RUN_HEALTH_OK_3V8` to form final `SAFE_CLEAR_N`. Low PGOOD, system reset, eFuse fault, amplifier fault or run health clears authorization. U217 qualifies the deliberate arm edge. Recovery of a fault/health level does not itself SET the latch.
- U226 implements all eight exact Phase 3F command/status channel assignments, VCCA=`3V3_SYS`, VCCB=`3V8_PRE`, fixed A-to-B direction, grounded OE, both supply bypasses and all stated A/B pulldowns. U223 Schmitt-conditions raw PGOOD/eFuse fault. Raw reset/amplifier-fault nodes have their 10k pullups and 100k pulldowns.
- U218/U219 implement `ANALOG_PWR_EN = DOWNSTREAM_EN AND HW_RUN_LATCHED AND ANALOG_PWR_CMD_3V8`. Both microphone and AFE EN have separate 100k pulldowns. Either can be forced into the shared analog-OFF state while core/DMC remain enabled; firmware cannot override a cleared safe latch.
- U227 independently qualifies amplifier MUTE/STANDBY releases with the latch. Their command and release nodes have passive LOW defaults. Clock availability cannot assert either release.
- U228 implements pre-arm `CLOCK_STARTUP_EN`; U220 implements post-arm `AUDIO_DATA_OE_RELEASE`. Q201 sinks MCLK OE from `RAILS_OK` alone. Q202 sinks the clock-bank OE from `CLOCK_STARTUP_EN`; Q203 sinks the data-bank OE from `AUDIO_DATA_OE_RELEASE`. Each has a 100k gate pulldown and the exact destination-rail 10k OE pullup.
- U229 implements the two-source open-drain ADC reset: LOW on either `SYS_HWRST` or `ADC_RST_RELEASE_CMD` asserts `ADC_PD_RST_N`. The command defaults LOW. ADC reset release has no safe-latch prerequisite.

| Sheet 2 output | Required later connection; do not duplicate its Sheet 2 pull/sink |
| --- | --- |
| `MCLK_OE_N` | SN74AXC2T245 pin 2; pullup already to `1V8_DSP_REF_ANA` |
| `AUDIO_CLOCK_OE_N` | SN74LVC244A pin 1, BCLK/FSYNC bank; pullup already to `3V3_SYS` |
| `AUDIO_DATA_OE_N` | SN74LVC244A pin 19, serial-data bank; pullup already to `3V3_SYS` |
| `ADC_PD_RST_N` | ADAU1978 PD/RST pin 6; reset release only after stable MCLK |
| `AMP_MUTE_RELEASE`, `AMP_STBY_RELEASE` | Amplifier functional releases; remain LOW before arm |
| Paired analog interfaces | After existing 100-ohm microphone RF/47-ohm AFE drive resistors, before coupling/ADC inputs; ADC VREF through its paired path |

### Timing, startup dependency and event verification

C340 is the exact **KEMET C1210C224J3GACTU**, 220 nF, 5%, C0G, 25 V, 1210. Its [manufacturer specsheet](../datasheets/power/kemet_C1210C224J3GACTU.pdf), p.1, and [C0G family specification](../datasheets/power/kemet_c0g.pdf), pp.1-2, support 30 ppm/C, zero aging loss and no DC-bias capacitance change. Including initial tolerance and the maximum 100 C displacement from 25 C across -40 to +125 C gives **208.373-231.693 nF**, inside the frozen 198-242 nF acceptance range.

Using TPS3760 Rev.A timing resistance/delay bounds, the frozen effective range reproduces **20.415-40.946 ms** to displayed rounding. The selected part gives **21.484-39.203 ms**, leaving more than 1 ms minimum slack for the nanosecond-scale latch/reset propagation relationship. CTR/MR is intentionally open. The 330 ms minimum reset/boot qualification exceeds the timer's worst 10%-discharge interval. Bench verification of actual reset/rail waveforms remains required.

The checker reconstructs the combinational equations from the **KiCad-exported pins**, checks the latch/timer/translator connections, and topologically sorts the startup dependency graph. The chain is:

`power valid -> reference/OUT1 -> DOWNSTREAM_EN -> monitored rails -> RAILS_OK -> MCLK OE release -> DSP reset/boot -> CLOCK_STARTUP_EN -> ADC reset/startup/PLL validation -> run health + deliberate arm edge -> HW_RUN_LATCHED -> data/analog/amplifier permissions`.

No implemented bootstrap or downstream-enable logic cone contains `HW_RUN_LATCHED`. The graph includes explicitly marked future endpoint/firmware steps, whose required wiring is the Phase 3F interface contract. ADC PLL lock does not require analog power or serial data. Amplifier active clock checks occur after arm in programmed Hi-Z, before analog settling/MUTE/PLAY; STANDBY fault monitoring is not assumed.

**Executed digital event checks:** cold startup, pre-arm clocks with functional releases blocked, explicit health/arm SET, asynchronous clearing by each of the five sources, recovery without automatic rearm, all four individual monitored-rail failures, watchdog reset/reboot, ADC-PLL health withdrawal, and commanded service-off retention after DSP/system power disappears. V1 failure disables downstream power; V2/V3/V4 failure holds reset without circularly disabling their own regulators. Brownout removes downstream enable immediately. Healthy-rail watchdog reset retains MCLK availability while clearing data/analog/amplifier authorization and BCLK/FSYNC release.

Commanded shutdown remains: MUTE/Hi-Z/STANDBY LOW >=15 ms; analog OFF and >=1 ms guard; data OFF and ADC reset; run health LOW; clock-startup command LOW; retained shutdown pulse; post-reset hold; downstream OFF. Pre/reference remain intentionally on in service-off until an external PGOOD-low power cycle; full power-off removes reference last. Abrupt loss does not claim graceful ride-through. The ADC interface note retains CEXT=10 uF X7R, effective maximum <=12 uF, REXT=3.00k 1%, >=50 ms in-place reset, and the stable-clock/DVDD wait before PWUP. These endpoint parts/registers are not entered on Sheet 2.

These are netlist and bounded digital timing/state checks, **not analog SPICE or oscilloscope tests**. ADC-only PLL loss has no direct hardware status pin: Phase 3F's mandatory PLL automute, firmware health withdrawal and watchdog policy remain the exact integration requirement.

### Cross-domain, load and component verification

The fourteen TMUX2821 devices form **13 paired-domain paths**: eight differential legs, one ADC-VREF path, and four microphone paths. Each crossing has two series switches powered from the adjacent rails; both used SELs follow `ANALOG_PWR_EN`. The VREF pair's unused SELs are grounded and unused S/D pins are NC. All VDD pins have 100 nF bypass, all EPs are grounded. Native pin tracing verifies that no analog crossing bypasses either switch.

The microphone/ADC/AFE rail bounds lie inside the switch's 1.8-5.5 V supply range; the pre-domain SEL high is below its 5.5 V fail-safe limit. Powered-off switch isolation, translator supply isolation/Ioff, destination-domain reset/OE pullups, grounded NMOS sources, and the amplifier gate's tolerant inputs prevent an intended powered driver from sourcing an absent domain. Leakage is not claimed to be zero. Future external debug/pullup connections and loaded rail-collapse permutations still require the frozen physical checks.

The implementation screen places all Sheet 2 control-resistor currents conservatively at 3.9 V, even for system-domain and series networks, and adds manufacturer quiescent terms: approximately **7.045 mA** versus the existing 20 mA control allowance. This is a DC allocation screen; transition-current and complete-board workload claims are not inferred. TMUX maxima add 0.28 mA microphone, 0.70 mA ADC and 0.98 mA AFE. Microphone fixed/max-current subtotal is 2.316 mA within 5 mA; AFE quiescent/preload/switch subtotal is 30.091 mA within 50 mA. ADC fixed support, including the future DVDD discharge resistor, is 2.481 mA, leaving 27.519 mA of its existing 30 mA allocation for the ADC and remaining support. Full DSP/ADC/amplifier workload, output-drive and transient totals remain the populated-board audit; frozen allocations were not increased.

All new critical pin numbers, polarities and package assignments were checked against the specific local manufacturer evidence before entry. The cached symbols, instance wiring and footprint pad-number sets were checked after native save:

| New device | Pin/package evidence |
| --- | --- |
| SN74LVC1G74DCUR | Rev.G p.4: CLK1/D2, inverted Q3, GND4, Q5, CLR6, PRE7, VCC8; DCU0008A pp.22-24 |
| SN74LVC2G07DBVR / SN74LVC2G17DBVR | Rev.L / Rev.N p.3: inputs1/3, outputs6/4, GND2/VCC5; DBV SOT-23-6 |
| SN74LVC2G08DCUR | Rev.N p.3: 1/2->7, 5/6->3, GND4/VCC8; DCU |
| SN74LXC8T245PWR | Rev.A p.3: exact PW A/B pairs, DIR/OE and all supply/ground pins; PW TSSOP-24 |
| TPS3760E012DYYR | Rev.A pp.3-5: OV adjustable active-low open-drain option, SENSE3/RESET6/CTS10/CTR9, grounds8/13; DYY0014A pp.41-43 |
| TMUX2821DSGR | December 2025 p.3: S1/D1=1/2, S2/D2=5/6, SEL1/SEL2=7/3, GND4/VDD8; DSG0008A EP9, p.30 |
| BSS138LT1G | onsemi Rev.14 pp.1-2: gate1/source2/drain3; SOT-23; OE sink polarity and gate/drain limits |
| C340 | KEMET part specsheet p.1 plus family C0G pp.1-2; nonpolar 1210/25 V/5% |

The added DYY0014A footprint reproduces TI's 14-pad, 0.5 mm pitch, 3.0 mm row-spacing, 1.05 x 0.30 mm land pattern. It is a package library artifact, not PCB placement or layout. Earlier regulator/supervisor packages and their verified pin maps remain unchanged. All test points now have explicit pad footprints.

### Native KiCad and ERC disposition

Executed KiCad **10.0.6** native `sch upgrade --force` for Sheet 2 and the hierarchy root in a complete temporary project copy, copied back only those authorized schematics, then ran ERC and XML/PDF exports on the final project. **1,734 checks passed** in [verify_sheet2_final.py](phase_4b/verify_sheet2_final.py). [Full results](phase_4b/phase3f_completion/sheet2_verification_results.json), [raw ERC](phase_4b/phase3f_completion/sheet2_erc_final.json), [exported netlist](phase_4b/phase3f_completion/sheet2_project.net.xml), [review PDF](phase_4b/phase3f_completion/sheet2_review.pdf), [component manifest](phase_4b/phase3f_completion/sheet2_components.json), and [pin map](phase_4b/phase3f_completion/sheet2_symbol_pin_audit.json) are retained separately from all earlier artifacts.

Final ERC remains **3 errors / 5 warnings**, with **zero unresolved BLOCKING items**. Every item is individually recorded with its UUID and disposition in the results JSON:

| Item | Classification | Reason |
| --- | --- | --- |
| U201 FB2 pin 4 to ground power output | JUSTIFIED / INTENTIONAL | Phase 3D requires grounded FB2 with VSEL low; ground power flag triggers an output-type conflict |
| U202 FB2 pin 4 to ground power output | JUSTIFIED / INTENTIONAL | Same required manufacturer/configuration connection |
| U203 FB2 pin 4 to ground power output | JUSTIFIED / INTENTIONAL | Same required manufacturer/configuration connection |
| Root `12V_PROTECTED` wire endpoint off grid | JUSTIFIED / INTENTIONAL | Original Sheet 1 port position preserved; exported connectivity checked |
| Root `POWER_GND` wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same preserved geometry and verified connection |
| Root `3V8_PRE` wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same preserved geometry and verified connection |
| Root `PGOOD_12V` wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same preserved geometry and verified connection |
| Root `EFUSE_FLT_N` wire endpoint off grid | JUSTIFIED / INTENTIONAL | Same preserved geometry and verified connection |

No previous raw ERC item is classified FIXED on this resume; their intentional connectivity remains. The missing eFuse pullup was **FIXED by netlist/contract review**, not detected by ERC. No warning/error severity was suppressed and no global exclusion was added. The same four KiCad default ignored checks are recorded; they do not constitute simulation or electrical validation. Source-page/package inspection and review of the exported schematic supplement ERC.

### Reproduction, protected files and remaining validation

From repository root, run `python validation/phase_4b/verify_sheet2_final.py` to reload/save, export and check the final design. Re-entry is reproducible with `build_sheet2_final.py`, then `integrate_sheet2_final.py`, then `verify_sheet2_final.py`, all under `validation/phase_4b/`. Historical scripts reproduce historical states and must not be run to regenerate the final design.

Modified by this resume: `hardware/kicad/power_regulation.kicad_sch`, the hierarchy root, `hardware/kicad/Astra_Sequencing.kicad_sym`, and this append-only validation record. Added: the DYY package library file, KEMET CTS specsheet, three final entry/integration/verification scripts, and `validation/phase_4b/phase3f_completion/` artifacts. The user's pre-existing phase/evidence document changes and untracked manufacturer files were preserved. No Git commit was created.

Baseline hashes confirm **Sheet 1, its symbol library, project settings, and every later schematic are unchanged**. All prior validation bytes are preserved. The root's Sheet 2 box was enlarged/repositioned to make the expanded interface list readable; Sheet 1 geometry was retained. No replacement components or architecture were selected.

Remaining nonblocking future validation: actual rail ramps and >=100 us DSP rise/fall; regulator MLCC effective capacitance/ESR and inductor bias/saturation qualification; loaded ripple/stability/thermal performance; analog switch noise/CMRR/settling/leakage and powered-off permutations; loaded OE edge/timing quality; complete workload-dependent BOM currents; endpoint clock generation, ADC DVDD/reset/PLL sequence and fault response; firmware graceful waits and amplifier active Hi-Z-before-PLAY checks; oscilloscope confirmation of the post-reset hold. These are explicitly unperformed and do not block the completed Sheet 2 schematic merely because hardware or later sheets do not yet exist.

PHASE 4B: PASS
