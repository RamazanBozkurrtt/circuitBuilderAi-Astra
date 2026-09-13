# Phase 3D - Final power-contract audit and pre/core correction

Date: 2026-09-13 (Europe/Istanbul)  
Scope: documentary worst-case correction and final audit of the frozen Sheet 2 power tree. No KiCad file was created or modified, and Phase 4B was not resumed.

Evidence notation uses the IDs in the [component evidence index](../evidence/component_evidence_index.md). Only the already-selected power, supervisor, watchdog, enable-logic, and load-device manufacturer documents were used. Static limits below are calculated contract limits; ripple, transients, temperature rise, and ramp behavior remain physical-validation items.

**Phase 3E amendment (2026-09-13):** Phase 4B exposed a sequencing contradiction in the shared direct `OUT1` fanout. The [Phase 3E shutdown/safe-state correction](phase_3e_shutdown_safe_state_correction.md) supersedes sections 9.1-9.2 and implementation items 6-7 below wherever they describe direct downstream/microphone enables or an unspecified AFE override. It does not change any Phase 3D rail source, regulator, divider, preload, threshold, load allocation, static range, or margin calculation.

**Phase 3G amendment (2026-09-14):** the [remaining-sheet preflight](phase_3g_remaining_schematic_implementation_preflight.md) replaces the former AFE devices and Phase 3E microphone-isolation population. The corrected consumers remain within the existing `2V8_MIC`, `3V3_ADC_A`, and `5V_AFE` allocations, so no Phase 3D rail, divider, preload, static range or margin changes.

## 1. Original pre/core contradiction

The frozen contract contained two different kinds of voltage range:

| Rail | Existing nominal | Existing approved/load range | Existing selected regulation range | Existing regulator/input | Existing feedback | Phase 3B supervisor | Required Phase 3B release / fault margin |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| `3V8_PRE` | 3.80 V (divider nominal 3.794 V) | 3.762-3.838 V | 3.762-3.838 V was claimed | TPS62135RGXR from `12V_PROTECTED` | 442 kOhm / 100 kOhm, 0.1% | None; this rail powers LTC2964 | N/A |
| `1V0_DSP_CORE` | 1.00 V (divider nominal 0.999 V) | ADSP-21569 VDD_INT 0.950-1.050 V | 0.990-1.010 V target | TPS62135RGXR from `3V8_PRE` | 42.7 kOhm / 100 kOhm, 0.1% | LTC2964 V2, 0.959608-0.971404 V | at least +18.596 mV / +9.608 mV |

TPS62135 specifies `VFB=0.7 V +/-1%` only in PWM mode with `VIN >= VOUT + 1 V`, and specifies 70 nA maximum FB leakage [BUCK section 7.5, p.6]. For either leakage sign and 0.1% resistor corners:

`Vmin = 0.7*0.99*(1 + Rt*0.999/(Rb*1.001)) - 70 nA*Rt*0.999`

`Vmax = 0.7*1.01*(1 + Rt*1.001/(Rb*0.999)) + 70 nA*Rt*1.001`

The old pre divider produces 3.719031-3.869167 V, outside 3.762-3.838 V. The old core divider produces 0.985334-1.012485 V. The latter is safe for the DSP, but its guaranteed release margin is only `0.985334 - 0.971404 = 13.930 mV`, below the frozen +18.596 mV requirement. Both discrepancies remain at zero leakage; they are not artifacts of the conservative leakage sign.

## 2. Corrected pre/core architecture

Retain TPS62135RGXR in forced-PWM mode for both rails. Change only the feedback networks and the intermediate-rail realized-range contract:

| Rail | Corrected feedback, 0.1% | Divider nominal | Guaranteed static range | Approved/load range after correction | Supervisor result |
| --- | --- | ---: | ---: | ---: | --- |
| `3V8_PRE` | 44.2 kOhm top / 10.0 kOhm bottom | 3.794 V | **3.746849-3.841293 V** | **3.700-3.900 V** intermediate operating band | Not directly monitored; static range is inside the corrected band and the full band is valid for every downstream input and LTC2964 VCC |
| `1V0_DSP_CORE` | 4.32 kOhm top / 10.0 kOhm bottom | 1.0024 V | **0.991476-1.013338 V** | DSP requirement remains **0.950-1.050 V** | release **+20.072 mV**; fault **+9.608 mV**; PASS |

The pre-rail +/-1% statement is superseded, not silently stretched. It was an intermediate design target rather than a downstream device limit. The corrected 3.700-3.900 V operating band contains the complete static range with 46.849 mV low-side and 58.707 mV high-side allowance for physically validated ripple/transients. At those operating-band limits, every downstream component remains inside its manufacturer input range; the most restrictive conservative accuracy check is the ADC LDO at `3.700 - 3.3495 - 0.300 = 50.5 mV` additional headroom. The lower-impedance dividers also reduce FB-leakage error without changing topology.

Worst accuracy-headroom checks are:

- pre buck: `10.400 - 3.841293 - 1 = 5.558707 V` beyond the required 1 V;
- core buck over the approved pre operating band: `3.700 - 1.013338 - 1 = 1.686662 V` beyond the required 1 V.

## 3. Complete Sheet 2 rail audit

Loads are total rail allocations and include the Phase 3D preloads below. They are design maxima for schematic implementation, not measured populated-board results. `Static min/max` excludes switching ripple and transient excursion.

| Rail | Nominal | Approved min/max | Source regulator; actual input | Guaranteed operating condition | Feedback; tolerance | Static min/max | Max load | Capability / practical margin | Headroom/dropout | Supervisor | Worst release threshold; margin | Worst fault threshold; margin | Status |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| `12V_PROTECTED` | 12.0 V | 10.4/13.2 V | TPS26630RGER pass path; 10.8-13.2 V connector normal | 4.5-60 V device operation; path drop <=0.4 V at 4 A | No output FB; 316 k/13.3 k/30.4 k 0.1% UV/OV ladder | 10.4/13.2 V system contract | 4 A continuous; 5 A <1 s | 6 A class; ILIM 5.17-5.95 A; +1.17 A continuous and +0.17 A short allocation | <=0.4 V complete path at 4 A; 53 mOhm max internal FET is part of budget | TPS3760A012DYYR | rise max 10.333488 V; **+66.512 mV** to 10.4 V | fall min 9.870314 V; **+307 mV** before eFuse fall max 9.563 V | PASS |
| `3V8_PRE` | 3.794 V | 3.700/3.900 V | TPS62135RGXR; 10.4-13.2 V | PWM, -40 to +125 C, VIN 3-17 V, VIN>=VOUT+1 V, recommended L/C | 44.2 k/10.0 k; 0.1% | 3.746849/3.841293 V | 1.8 A | 4 A; +2.2 A | +5.558707 V beyond accuracy headroom | None; LTC2964 supply-loss behavior holds reset | N/A | N/A | PASS (3D correction) |
| `1V8_DSP_REF_ANA` | 1.828455 V | 1.710/1.890 V | TPS7A4901DGNR; `3V8_PRE` 3.700-3.900 V | VIN>=VOUT+1 V, 1-150 mA, -40 to +125 C, stable C/ESR | (54.2 k + 100 Ohm)/100 k; all 0.1% | 1.776066/1.875487 V | 75 mA total | 150 mA; +75 mA | +0.824513 V beyond accuracy headroom; >600 mV max dropout | LTC2964 V1 | max 1.756604 V; **+19.462 mV** | min 1.733427 V; **+23.427 mV** above 1.710 V | PASS (3D correction) |
| `1V0_DSP_CORE` | 1.0024 V | 0.950/1.050 V | TPS62135RGXR; `3V8_PRE` 3.700-3.900 V | PWM, -40 to +125 C, VIN>=VOUT+1 V, recommended L/C | 4.32 k/10.0 k; 0.1% | 0.991476/1.013338 V | 3.0 A | 4 A; +1.0 A | +1.686662 V beyond accuracy headroom | LTC2964 V2 | max 0.971404 V; **+20.072 mV** | min 0.959608 V; **+9.608 mV** above 0.950 V | PASS (3D correction) |
| `1V35_DSP_DMC` | 1.361565 V | 1.283/1.418 V | TPS7A4901DGNR; `3V8_PRE` 3.700-3.900 V | VIN>=VOUT+1 V, 1-150 mA, -40 to +125 C, stable C/ESR | 14.9 k/100 k; 0.1% | 1.325693/1.395966 V | 50 mA total | 150 mA; +100 mA | +1.304034 V beyond accuracy headroom; >600 mV max dropout | LTC2964 V3 | max 1.312379 V; **+13.314 mV** | min 1.295641 V; **+12.641 mV** above 1.283 V | PASS (3D correction) |
| `3V3_SYS` | 3.297 V | 3.130/3.470 V | TPS62135RGXR; `12V_PROTECTED` | PWM, -40 to +125 C, VIN>=VOUT+1 V, recommended L/C | 37.1 k/10.0 k; 0.1% | 3.256299/3.337821 V | 200 mA | 4 A; +3.8 A | +6.062179 V beyond accuracy headroom | LTC2964 V4 | max 3.202097 V; **+54.202 mV** | min 3.157969 V; **+27.969 mV** above 3.130 V | PASS |
| `3V3_ADC_A` | 3.30 V | 3.00/3.60 V | TPS7A2033PDBVR; `3V8_PRE` 3.700-3.900 V | VIN=VOUTnom+0.3 V to 6 V, 1-300 mA, -40 to +125 C | Internal fixed; preload 3.01 k 0.1% | 3.250500/3.349500 V | 30 mA total | 300 mA; +270 mA | +0.050500 V beyond conservative accuracy condition; 140 mV max dropout at 300 mA | None | N/A | N/A | PASS (3D load correction) |
| `2V8_MIC` | 2.80 V | 2.30/3.00 V | TPS7A2028PDBVR; `3V8_PRE` 3.700-3.900 V | VIN=VOUTnom+0.3 V to 6 V, 1-300 mA, -40 to +125 C | Internal fixed; preload 2.55 k 0.1% | 2.758000/2.842000 V | 5 mA total | 300 mA; +295 mA | +0.558000 V beyond conservative accuracy condition; 140 mV max dropout at 300 mA | None | N/A | N/A | PASS (3D load correction) |
| `5V_AFE` | 5.0244 V | 4.50/5.50 V | TPS7A4901DGNR; `12V_PROTECTED` | VIN>=VOUT+1 V, 1-150 mA, -40 to +125 C, stable C/ESR | 324 k/100 k; 0.1%; preload 4.70 k 0.1% | 4.858943/5.157889 V | 50 mA total | 150 mA; +100 mA | +4.242111 V beyond accuracy headroom; >600 mV max dropout | None | N/A | N/A | PASS (3D bound/load correction) |

No Sheet 2 rail remains `CORRECTION REQUIRED` or `BLOCKED BY MISSING EVIDENCE` after the corrections in this report.

## 4. Regulator guarantee-condition audit

| Regulator / instances | Accuracy guarantee actually used | Conditions that must be implemented | Non-guaranteed data not used for acceptance |
| --- | --- | --- | --- |
| TPS62135 (`3V8_PRE`, core, `3V3_SYS`) | VFB +/-1% | MODE high, forced PWM; VIN 3-17 V and at least VOUT+1 V; TJ -40 to +125 C; output within 0.8-12 V; effective L 0.6-2.9 uH, effective CIN >=3 uF, effective COUT 6-200 uF directly connected; load below 4 A and current limit | Separate 0.05%/A load-regulation and 0.02%/V line-regulation entries are typical only. Typical efficiency, ripple, negative-current limit, frequency, dropout/100%-duty behavior, and thermal curves are not converted into guarantees. |
| TPS7A4901 (`1V8_DSP_REF_ANA`, DMC, AFE) | Overall output accuracy +/-2.5% | VIN from VOUTnom+1 V through 35 V; IOUT 1-150 mA; TJ -40 to +125 C; EN valid; COUT >=2.2 uF and ESR <200 mOhm; feedback divider draws >=5 uA | Typical line/load coefficients, PSRR, noise, and 260/600 mV dropout data are not used as substitutes for the overall-accuracy condition. Explicit preloads enforce the 1 mA lower bound. |
| TPS7A20 fixed P variants (ADC, microphone) | Output tolerance +/-1.5% | VIN from VOUTnom+0.3 V through 6 V; IOUT 1-300 mA; TJ -40 to +125 C; COUT effective 0.47-200 uF and ESR <=100 mOhm; valid EN | Typical line/load, noise, PSRR, and startup waveforms are not acceptance bounds. Explicit preloads enforce the 1 mA lower bound. |
| TPS26630 (`12V_PROTECTED`) | No output-voltage regulation claim; protected pass-path contract | IN_SYS/IN 4.5-60 V, programmed UVLO/OVP/current limit, controlled dVdT, TJ -40 to +125 C, complete connector-to-load drop <=0.4 V at 4 A | No claim that the eFuse regulates 12 V. The 10.4-13.2 V rail is the approved source/path envelope. |

Every switching-regulator accuracy number is therefore used inside its specified input, mode, temperature, and passive-component conditions. There is no PFM instance. No branch relies on the TPS62135 100%-duty mode.

## 5. Feedback-network and fixed-output calculations

### 5.1 TPS62135 adjustable rails

Using the equations in section 1:

| Rail | Rt/Rb | Nominal | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: |
| `3V8_PRE` | 44.2 k/10.0 k | 3.794000 V | 3.746849 V | 3.841293 V |
| `1V0_DSP_CORE` | 4.32 k/10.0 k | 1.002400 V | 0.991476 V | 1.013338 V |
| `3V3_SYS` | 37.1 k/10.0 k | 3.297000 V | 3.256299 V | 3.337821 V |

The result includes VFB accuracy, both resistor tolerances, and either sign of the maximum FB leakage. No nominal ratio is used for acceptance.

### 5.2 TPS7A4901 adjustable rails

TPS7A49 guarantees +/-2.5% overall accuracy only from 1 mA to 150 mA with VIN>=VOUTnom+1 V. Its feedback current is 0-100 nA and positive current flows out of the FB pin [HVLDO section 6.5, p.6]. Conservatively treating the overall-accuracy term as an effective FB scale:

`Vmin = 1.185*0.975*(1 + Rt*0.999/(Rb*1.001)) - 100 nA*Rt*0.999`

`Vmax = 1.185*1.025*(1 + Rt*1.001/(Rb*0.999))`

| Rail | Rt/Rb | Nominal | Minimum | Maximum | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| `1V8_DSP_REF_ANA` | **(54.2 k + 100 Ohm)/100 k** | 1.828455 V | 1.776066 V | 1.875487 V | Replaces 53.6 k/100 k; retains the required release allowance with more upper-rail headroom than 54.9 k/100 k |
| `1V35_DSP_DMC` | **14.9 k/100 k** | 1.361565 V | 1.325693 V | 1.395966 V | Replaces 14.7 k/100 k for the same reason |
| `5V_AFE` | 324 k/100 k | 5.024400 V | 4.858943 V | 5.157889 V | Divider retained; corrected bounds supersede 4.898-5.150 V |

All lower feedback resistors are 100 kOhm, giving about 11.85 uA at FB and satisfying the >=5 uA no-load-stability rule.

### 5.3 Minimum-load corrections

The following 0.1% permanent output-to-ground preloads make the manufacturer accuracy load range deterministic even before any IC load is credited. Their current is included in each rail allocation.

| Rail | Preload | Guaranteed minimum preload current | Maximum resistor dissipation |
| --- | ---: | ---: | ---: |
| `1V8_DSP_REF_ANA` | 1.69 kOhm | 1.050 mA | 2.09 mW |
| `1V35_DSP_DMC` | 1.24 kOhm | 1.068 mA | 1.57 mW |
| `5V_AFE` | 4.70 kOhm | 1.033 mA | 5.67 mW |
| `3V3_ADC_A` | 3.01 kOhm | 1.079 mA | 3.73 mW |
| `2V8_MIC` | 2.55 kOhm | 1.080 mA | 3.17 mW |

TPS7A20 fixed-output bounds are therefore simply 3.30 V +/-1.5% = 3.2505-3.3495 V and 2.80 V +/-1.5% = 2.758-2.842 V under the actual guaranteed conditions.

## 6. Supervisor-margin audit

Phase 3D retains the Phase 3B LTC2964 dividers and exact threshold calculations. LTC2964 has no threshold hysteresis in the selected +ADJ configuration; its filtered rising and falling ranges are identical. Acceptance floors are the release and fault margins approved in Phase 3B, except the Phase 3C +54.202 mV `3V3_SYS` release margin is the controlling floor.

| Monitor | Divider, 0.1% | Falling = rising range | Corrected rail minimum | Release margin | Safe minimum | Fault margin | Required floor | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LTC2964 V1, 1.8 V | 24.9 k/10.0 k | 1.733427-1.756604 V | 1.776066 V | **+19.462 mV** | 1.710 V | **+23.427 mV** | +18.396 / +23.427 mV | PASS |
| LTC2964 V2, core | 9.31 k/10.0 k | 0.959608-0.971404 V | 0.991476 V | **+20.072 mV** | 0.950 V | **+9.608 mV** | +18.596 / +9.608 mV | PASS |
| LTC2964 V3, DMC | 15.8 k + 280 Ohm /10.0 k | 1.295641-1.312379 V | 1.325693 V | **+13.314 mV** | 1.283 V | **+12.641 mV** | +12.621 / +12.641 mV | PASS |
| LTC2964 V4, 3.3 V | 53.6 k/10.0 k | 3.157969-3.202097 V | 3.256299 V | **+54.202 mV** | 3.130 V | **+27.969 mV** | +54.202 / +27.969 mV | PASS |

The TPS3760 upstream calculation also remains valid: rising maximum 10.333488 V leaves +66.512 mV to the 10.4 V protected-rail minimum; falling minimum 9.870314 V precedes the eFuse falling maximum 9.563 V by at least 307 mV. Its 0.197-0.203 V rail-referred hysteresis is explicitly included [Phase 3A; PGSUP].

## 7. Current, headroom, startup, and thermal screen

| Rail/source | Load allocation | Rated capability | Startup/peak and practical screen | First-order thermal result | Status |
| --- | ---: | ---: | --- | --- | --- |
| `12V_PROTECTED` / TPS26630 | 4 A continuous, 5 A <1 s | 6 A class; 5.17 A minimum programmed limit | 470 uF bulk charges on controlled dVdT before PLAY; 5 A short allocation remains 0.17 A below minimum limit; continuous allocation is 1.17 A below | Internal FET <=0.85 W at 4 A using 53 mOhm max; complete path and board copper still require thermal test | PASS |
| `3V8_PRE` / TPS62135 | 1.8 A | 4 A | Equation 10 at 13.2 V/0.8 uH gives 1.65 A p-p. Adding worst 200 uF charge at the fastest 2.593 ms SS-current corner gives 2.921 A peak; TI's +20% margin gives 3.506 A, below the frozen 5 A requirement. | Converter/inductor loss requires hardware validation; no minimum efficiency is published | PASS |
| core / TPS62135 | 3.0 A | 4 A | At the approved 3.900 V/0.8 uH corner, ripple is 0.488 A p-p. Adding worst 200 uF startup charge gives 3.322 A peak; with +20%, 3.987 A, below 5 A. | DSP load/transient and junction temperature require validation | PASS |
| `3V3_SYS` / TPS62135 | 0.2 A | 4 A | At 13.2 V/0.8 uH, ripple is 1.65 A p-p. Adding worst 200 uF startup charge gives 1.282 A peak; with +20%, 1.539 A, below 5 A. | Phase 3C's 0.50 W thermal allocation remains a conservative typical-efficiency screen | PASS |
| 1.8 V / TPS7A49 | 75 mA | 150 mA | Preload included; programmed soft start; accuracy and dropout conditions satisfied across the full pre band | <=0.160 W first order at maximum approved input/load, about 10.2 C rise with DGN JEDEC 63.4 C/W | PASS |
| DMC / TPS7A49 | 50 mA | 150 mA | Preload is also a defined discharge path; accuracy/dropout conditions satisfied across the full pre band | <=0.130 W first order, about 8.3 C JEDEC rise | PASS |
| ADC / TPS7A20 | 30 mA | 300 mA | Preload included. The 1.15 ms maximum startup is specified only with 1 uF COUT and is not applied to the larger populated bank; ADC readiness/fail-safe behavior does not depend on that time. | About 20 mW first order and 3.7 C using DBV JEDEC RthetaJA | PASS |
| microphone / TPS7A20 | 5 mA | 300 mA | Preload included; microphone maximum 0.92 mA plus preload leaves about 3 mA allocation. The 1.15 ms maximum startup is not applied outside its 1 uF test condition. | About 5.8 mW first order and 1.1 C using DBV JEDEC RthetaJA | PASS |
| AFE / TPS7A49 | 50 mA | 150 mA | Preload included; firmware enable occurs only after power/reset qualification | <=0.419 W first order, about 26.6 C with DGN JEDEC RthetaJA | PASS |

The 1.8 A pre-rail and 3.0 A core figures remain allocations pending the populated-BOM DSP workload calculation. As a peak-demand screen, core output at 3.0 A and 1.013338 V is 3.040 W. Even using a deliberately conservative 70% conversion-efficiency planning factor rather than a manufacturer guarantee, its pre input is 1.174 A at the 3.700 V operating-band corner; adding all four pre-fed LDO allocations (160 mA) and 20 mA supervisor/logic allowance gives 1.354 A, leaving 0.446 A to the 1.8 A allocation. The 70% factor is a calculated planning screen only; populated-BOM and thermal validation remain mandatory. The allocations fit the selected regulator ratings and passive peak-current requirements and are not claims of measured consumption or transient response.

## 8. Passive-component implementation requirements

| Regulator family | Deterministic implementation contract | Basis/classification |
| --- | --- | --- |
| Every TPS62135 | 1.0 uH nominal inductor, >=0.8 uH effective over tolerance/bias, saturation/thermal-current rating >=5 A, DCR <=30 mOhm. Local X7R/X5R CIN: 10 uF nominal and >=3 uF effective; 25 V minimum on the two `12V_PROTECTED` inputs and 6.3 V minimum on core input. COUT: >=22 uF effective for pre and `3V3_SYS`, >=100 uF effective for core; total directly connected effective COUT <=200 uF. MODE high, VSEL low, FB2 grounded, VOS at positive local output bank, SS/TR=10 nF. No bootstrap capacitor. Internal compensation and internal 15 pF VOS-FB feed-forward are used; no external compensation or feed-forward capacitor is required. | L/C ranges, 22 uF nominal recommendation, ceramic/DC-bias warning, internal compensation, and 20% inductor-current margin are **datasheet-backed** [BUCK pp.4, 13-16]. Peak-current figures in section 7 are **calculated**. Exact MLCC bias curves, magnetics loss/saturation curves, ripple, transient response, stability with distributed capacitance, and temperature are **requires physical validation**. |
| Every TPS7A4901 | Exact orderable TPS7A4901DGNR. Local 10 uF nominal X7R/X5R input and output capacitors, each selected to remain >=2.2 uF effective; output-capacitor ESR <200 mOhm. CFF=10 nF on every instance. CNR/SS=47 nF on 1.8 V and DMC, 10 nF on AFE. Feedback and preload values are those in section 5. No bootstrap or external compensation. | Minimum capacitance, ESR, CFF/CNR recommendations and soft-start relation are **datasheet-backed** [HVLDO pp.5-6, 14-17]. Effective capacitance and thermal behavior are **requires physical validation**. |
| TPS7A2033P/TPS7A2028P | Exact DBV orderables. Local 10 uF nominal X7R/X5R input/output capacitors, each selected to retain >=0.47 uF effective; COUT effective 0.47-200 uF and ESR <=100 mOhm. Use the section 5 preloads. No bootstrap or compensation. | Stability range and DC-bias warning are **datasheet-backed** [LDO pp.5-7, 26-31]. Ripple/transients and mounted capacitance are **requires physical validation**. |

The Phase 4B BOM may choose manufacturer part numbers only by satisfying these frozen electrical limits; it may not change topology, nominal values, or calculated minimum ratings.

## 9. Enable and sequencing audit

### 9.1 Power-up

1. TPS26630 validates `12V_IN` and ramps `12V_PROTECTED`; amplifier MUTE/STANDBY remain passively asserted.
2. `3V8_PRE` TPS62135 EN is tied directly to its `12V_PROTECTED` VIN and starts whenever that source is present. This is the sole unqualified Sheet 2 rail and breaks the pull-up dependency.
3. TPS3760 is already powered from `12V_PROTECTED`; its open-drain output can pull low before `3V8_PRE` exists. Once pre is present and `12V_PROTECTED` exceeds the rising threshold, its 10 kOhm pull-up creates `PGOOD_12V`.
4. `PGOOD_12V` drives the 1.8 V TPS7A49 EN. EN is never above its IN rail because both the pull-up and LDO input are `3V8_PRE`.
5. LTC2964 is powered by `3V8_PRE`. Valid V1 releases open-drain `OUT1`, pulled to the same rail. Phase 3E uses `OUT1` only as one input to pre-powered enable qualification; it is not connected directly to any regulator EN.
6. Phase 3E Schmitt-conditions PGOOD and forms `DOWNSTREAM_EN = OUT1 AND PGOOD_CLEAN AND DOWNSTREAM_RUN_DELAYED` with exact SN74LV1T08 gates powered from `3V8_PRE`. That node enables core, DMC, `3V3_SYS`, and ADC analog power. A retained `SN74LVC1G74` shutdown latch and `TPS3760E012` timer keep the node high for 20.415-40.946 ms after commanded DSP reset. Their logic levels remain within every regulator EN limit established by this audit.
7. LTC2964 common `RST` holds `RAILS_OK` low until all four DSP rails are valid for 160-240 ms. `RAILS_OK`, pulled only to `3V3_SYS`, drives TPS3431 EN; no pin exceeds TPS3431 VDD+0.3 V.
8. TPS3431 ENOUT adds 170-230 ms. `SYS_HWRST` therefore releases 330-470 ms after all rail thresholds are valid. The 1.8 V clock source/fanout maximum 3 ms startup is covered.
9. `2V8_MIC` and `5V_AFE` stay off through local 100-kohm EN pulldowns and `ANALOG_PWR_EN = DOWNSTREAM_EN AND HW_RUN_LATCHED AND ANALOG_PWR_CMD_3V8`. Phase 3E's dual-supply translator isolates this command from an unpowered DSP domain. Firmware may arm and assert the node only after DSP/ADC reset release, the mandatory >=10 ms ADC wait, and successful PLL/configuration checks. A missing or slow ADC analog rail prevents successful ADC readiness and leaves both analog rails off; no unsupported TPS7A20 startup-time extrapolation is used.

There is no enable cycle: pre permits `PGOOD_12V` pull-up; `PGOOD_12V` permits 1.8 V; 1.8 V permits `OUT1`; `OUT1` plus pre-powered retained qualification permits the remaining monitored rails; those rails permit reset release. The safe latch then requires an explicit post-boot arm before analog/audio release. No monitored rail is required to be valid before its own source can start, and no retained state is powered by a rail it controls.

### 9.2 Brownout and power-down

- Falling `PGOOD_12V` immediately clears the Phase 3E hardware-safe latch and drives `DOWNSTREAM_EN` and `ANALOG_PWR_EN` low while the eFuse remains on. Microphone/AFE enables, amplifier MUTE/STANDBY, reset, and OE defaults assert, and automatic PLAY recovery remains prohibited.
- The 1.8 V LDO also disables from `PGOOD_12V`. `OUT1` subsequently falls as V1 decays. This is a feed-forward shutdown path, not a circular dependency.
- TPS62135 active discharge is effective while its source remains above about 2 V. TPS7A20 P variants actively discharge; the Phase 3D preloads provide deterministic passive discharge for every LDO rail, including TPS7A49, which has no active-discharge output.
- Commanded shutdown is now implemented by Phase 3E: mute/Hi-Z, STANDBY >=15 ms, microphone/AFE command low, >=1 ms command guard, ADC reset and buffer OEs off, retained DSP reset, a guaranteed 20.415-40.946 ms hardware hold, then 3.3 V/DMC/core/ADC analog off, and 1.8 V last. Amplifier VDD is removed before protected PVDD/VBAT.
- Abrupt removal, output-capacitance spread, load-dependent ramps, and DSP rail-difference waveforms still require oscilloscope verification. Safe-state assertion does not depend on firmware.

With the Phase 3E amendment, the brownout and shutdown relationships are deterministic at the contract level and expose no enable-pin overstress.

## 10. Additional corrections found by the all-rail audit

1. The 1.8 V TPS7A49 top divider changes from 53.6 k to **54.2 k + 100 Ohm in series**, with the 100 k bottom and all resistors 0.1%, because the former fully calculated minimum left only 11.460 mV of release margin.
2. The DMC TPS7A49 divider changes from 14.7 k/100 k to **14.9 k/100 k**, both 0.1%, because the former fully calculated minimum left only 11.028 mV, below the prior 12.621 mV release allowance.
3. The 5 V divider remains 324 k/100 k, but its guaranteed static range is corrected to **4.858943-5.157889 V** after divider and FB-current terms. It remains inside the Phase 3G OPAx192 4.5-36 V rail requirement.
4. TPS7A49 and TPS7A20 accuracy specifications require at least 1 mA load. The five exact preloads in section 5.3 are added; normal consumer current is not used as an undocumented minimum-load assumption.
5. TPS7A2033P and TPS7A2028P output bounds are now explicitly tied to their VIN headroom, load, temperature, capacitance, and ESR conditions.
6. Directly connected TPS62135 output capacitance is explicitly capped at 200 uF effective, and every capacitor requirement is an effective-after-bias requirement.

The LTC2964 thresholds, TPS3431 watchdog timing, Phase 3A TPS3760/eFuse thresholds, Phase 3C `3V3_SYS` input reroute/divider/gate, and all downstream device rail limits remain unchanged.

## 11. Exact Phase 4B implementation contract

Phase 4B may resume only under separate authorization. When authorized, Astra shall implement Sheet 2 without selecting a different architecture:

1. Use three TPS62135RGXR instances. `3V8_PRE`: VIN=`12V_PROTECTED`, EN tied directly to VIN, Rt/Rb=44.2 k/10.0 k. Core: VIN=`3V8_PRE`, Rt/Rb=4.32 k/10.0 k. `3V3_SYS`: VIN=`12V_PROTECTED`, Rt/Rb=37.1 k/10.0 k. All feedback resistors are 0.1%. Use the common buck passive/configuration contract in section 8.
2. Use three TPS7A4901DGNR instances. 1.8 V: (54.2 k + 100 Ohm)/100 k, CNR/SS=47 nF, preload 1.69 k. DMC: 14.9 k/100 k, CNR/SS=47 nF, preload 1.24 k. AFE: 324 k/100 k, CNR/SS=10 nF, preload 4.70 k. All divider/preload resistors are 0.1%; fit 10 nF CFF and section 8 capacitance on every instance.
3. Use TPS7A2033PDBVR with 3.01 kOhm 0.1% preload and TPS7A2028PDBVR with 2.55 kOhm 0.1% preload, both from `3V8_PRE`, with the section 8 capacitance contract.
4. Implement LTC2964HUDC#PBF, its four Phase 3B dividers, pin straps, pull-ups, and `RAILS_OK` exactly as Phase 3B. Do not substitute native regulator PGOOD for safety supervision.
5. Implement TPS3431SDRBR and `SYS_HWRST` exactly as Phase 3B. Preserve low `PGOOD_12V`, eFuse FLT, low LTC2964 RST, and low TPS3431 WDO as hardware-dominant safe-state inputs.
6. Superseded by Phase 3E: implement its retained `DOWNSTREAM_EN` architecture for core, DMC, `3V3_SYS`, and ADC analog. Do not connect any regulator EN directly to `OUT1`. Keep the 1.8 V regulator on `PGOOD_12V` and pre enabled directly.
7. Superseded by Phase 3E and corrected by Phase 3G: drive both microphone and AFE regulator EN pins from the exact `ANALOG_PWR_EN` logic, implement the safe latch and shutdown timer, and fit ten `TMUX2821DSGR` plus four `TMUX1574PWR` paired-domain analog-isolation packages. No firmware state may bypass the safe-state inputs.
8. Keep all load allocations in section 3 as total maxima including dividers/preloads. Recalculate the populated BOM without exceeding them.
9. Provide all rail, sense, enable, PGOOD, reset, and fault test points. Run ERC, startup/shutdown transient checks, full rail/load calculations, and the physical validations below. Do not alter a rail, divider, supervisor threshold, input source, enable relation, or regulator part to make implementation convenient.

## 12. Remaining physical-validation items

These are required implementation/board validations, not unresolved component or architecture selections:

- verify exact selected MLCC effective capacitance across voltage, tolerance, aging, and temperature;
- verify exact inductor effective inductance, saturation/thermal current, DCR, core/copper loss, and temperature;
- measure switching ripple and line/load transients so instantaneous rails stay inside device limits; the static ranges above do not claim this;
- confirm TPS62135 loop behavior with the complete local and distributed capacitance and any series resistance;
- complete populated-BOM steady/peak loads, especially the workload-dependent DSP core demand, without exceeding allocations;
- simulate and measure all rail ramps at minimum/maximum input, minimum/maximum load, 0/40 C prototype ambient, commanded shutdown, brownout, restart, and abrupt input removal;
- demonstrate every DSP rise and fall is at least 100 us, all inter-rail delta limits are met, and reset/safe state asserts before a monitored rail crosses its device minimum;
- validate eFuse, regulator, inductor, capacitor, connector, and copper temperature at continuous and short-peak cases;
- verify AFE/ADC settling, regulator noise/PSRR, and no back-powering under every power state;
- verify symbol pins and packages against the cited official documents and retain ERC/validation artifacts.

With the Phase 3E amendment, no known frozen-contract contradiction remains in the Sheet 2 power tree. The regulator choices, input sources, divider values, preload values, supervision thresholds, corrected enable dependencies, and passive electrical limits are deterministic for implementation.

PHASE 3D: PASS
