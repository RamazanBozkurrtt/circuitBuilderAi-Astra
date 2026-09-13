# Phase 4C — Microphones / analog front end validation

Date: 2026-09-14. **BLOCKED before electrical implementation.** Sheet 3 remains its existing empty hierarchy placeholder. No schematic, symbol, Sheet 1/2, ADC, connector, DSP, amplifier, or PCB file was changed. This report is the only file created by this task. Existing working-tree changes were preserved.

## Evidence and scope

Reviewed AGENTS.md, [Phase 3](../docs/phases/phase_3_schematic_readiness.md) §§9, 14–17, its relevant Phase 3D rail and Phase 3E/3F safe-state contracts, the [evidence index](../docs/evidence/component_evidence_index.md), and the existing Sheet 2/3/root interfaces. The current Phase 4C authorization supersedes AGENTS.md's stale Phase 0 status; the stop-on-conflict rules still apply. Graphify MCP was not available; direct inspection was used.

Primary implementation evidence:

- [IM73A135V01 V1.20](../datasheets/microphone/im73a135_datasheet_v1_20.pdf), pp.6–11, Tables 3/6/7/8 and Fig.11: sensitivity, loading, startup, differential outputs and package pins. The local official PDF was read; the official web endpoint timed out.
- [OPA165x SBOS477B](../datasheets/afe/opa1654_datasheet_rev_b.pdf), pp.3–7: packages, pins, limits and electrical table; [official PDF](https://www.ti.com/lit/ds/symlink/opa1654.pdf) checked.
- [ADAU1978 Rev.B](../datasheets/adc/adau1978_datasheet_rev_b.pdf), pp.3, 15–16: reference limits, input scale/impedance and analog connections; [official PDF](https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU1978.pdf) checked.
- [TMUX2821 SCDS488](../datasheets/logic/tmux2821_datasheet_dec_2025.pdf), as specified by [Phase 3E §7.1](../docs/phases/phase_3e_shutdown_safe_state_correction.md); [official PDF](https://www.ti.com/lit/ds/symlink/tmux2821.pdf) checked. No broad component research or substitution was performed.

## Blocking contradictions

| ID | Evidence / consequence | Required resolution |
| --- | --- | --- |
| B1 — CONFLICTING microphone isolation contract | MIC Table 8 defines OUT+ pin 1 and OUT− pin 3. Phase 3 §9.2 requires both legs through identical gain/coupling paths. Phase 3E §7.1 instead specifies four **single-ended** microphone paths using four dual switches. Sheet 2 implements precisely four paths in U240–U243, exporting `MIC1_AFTER_100R` … `MIC4_AFTER_100R` and `AFE1_BEFORE_4u7` … `AFE4_BEFORE_4u7`, with no second leg per microphone. Four differential microphones need eight isolated legs. A bypassed second leg would violate the required isolation and matching; shorting legs would destroy the signal. | Correct the approved isolation contract and its Sheet 2/root interfaces for both polarities. Applying the existing paired-domain strategy to all eight legs requires eight microphone-side dual devices, four more than frozen, increasing the overall total from 14 to 18. This is a correction requirement, not an approved BOM change; update rail loads and verification with it. |
| B2 — CONFLICTING headroom conclusion | Phase 3 §9.3 uses nominal sensitivity and nominal VREF to justify a minimum output of 0.825 V against its stated 0.8 V limit. MIC sensitivity reaches −37 dBV/Pa and ADC VREF reaches 1.47 V. With approved resistor corners, the required minimum becomes **0.711582 V**, outside that screen, before offsets and drift. Even nominal microphone sensitivity/gain with minimum VREF gives 0.795055 V. Furthermore, OPA165x §6.6 specifies its table at ±15 V unless otherwise noted; the output-swing row does not independently establish a 5 V guarantee. | Correct the gain/headroom contract using applicable supply/load/temperature evidence and all relevant corners. Retaining 0.8 V as the screening boundary allows at most 3.36194 V/V at −37 dBV/Pa and VREF=1.47 V before offsets/margins. This is a diagnostic ceiling, not a selected replacement gain. A topology/VCM/device change is not authorized here. |

These findings invalidate implementation readiness for this interface; this report does not rewrite prior phase gates. B2 establishes inadequate proof of linearity, not a claim that every physical OPA1654 clips at 0.8 V. Sheet 2 changes are permitted for genuine interface contradictions, but cannot resolve the conflicting frozen device count or independent headroom blocker without a corrected contract. No speculative partial circuit was created.

## Numerical contract checks

Calculated in Python with `math` from the cited values; balanced differential legs are assumed, matching Phase 3.

| Check | Calculation / result | Disposition |
| --- | --- | --- |
| Gain and matching | `G=1+Rf/Rg=3.8`; independent 0.1% corners give `3.794406…3.805606` (0.295% maximum span relative to nominal). | Frozen values reproduced; no resistors implemented. |
| Microphone nominal | `10^(-38/20)=0.0125893 Vrms` at 94 dBSPL; multiply by `10^(26/20)` for `0.251189 Vrms` at 120 dBSPL. | Differential sensitivity assumption reproduced. |
| ADC drive | Nominal: 0.0478392 Vrms at 94 dBSPL, 0.954517 Vrms at 120 dBSPL; sensitivity/gain high corner: 1.072565 Vrms. | Ideal pre-loading values; 2 Vrms ADC scale is typical, not a guaranteed minimum. |
| ADC-scale margin | `20 log10(2/Vdiff)` = 6.42493 dB nominal, 5.41212 dB at the high corner. | Does not establish op-amp headroom or worst-case ADC clipping margin. |
| Output swing | `Vleg,pk=Vdiff/sqrt(2)` = 0.674945 V nominal, 0.758418 V at high corner. `VREFmin−Vleg,pk=0.711582 V`. | **BLOCKING B2**; offsets and reference loading not included. |
| Coupling HPF | `fc=1/(2πRC)`: 100 kΩ / 4.7 µF gives 0.338628 Hz; 100 kΩ / 2.2 µF gives 0.723432 Hz. | Meets 0.73 Hz screen only with adequate actual R/C bounds. |
| Low-frequency contribution | At 20 Hz and 0.723432 Hz corner: −0.005679 dB, +2.07158°, 0.287468 ms group delay. | Coupling contribution only; microphone itself has a typical 20 Hz −3 dB corner (MIC p.6). |
| Bias tolerance condition | With exactly 2.2 µF effective, `Rmin ≥ 1/(2π·0.73·2.2µ)=99.1002 kΩ`. | Bias resistor tolerance and effective capacitor bounds must be selected/verified; nominal 100 kΩ alone is insufficient. |
| ADC RF network | Frozen 47 Ω per leg plus 1 nF differential: `1/(2π·94·1n)=1.69314 MHz`, before switch/loading effects. | RF isolation only; internal ADC antialiasing remains required. |

## Remaining implementation checks

- **Active devices / symbols:** intended 4 × IM73A135V01, 2 × OPA1654AIPW and 1 × OPA1652AIDR; existing TMUX devices remain on Sheet 2. Manufacturer microphone mapping confirmed: 1 OUT+, 2 VDD, 3 OUT−, 4/5 GND. No new KiCad symbol exists, so full symbol-to-pin and polarized-passive audits are **NOT PERFORMED**.
- **Noise:** OPA165x publishes typical 4.5 nV/√Hz and 3 fA/√Hz at 1 kHz. `sqrt(4kT(Rg||Rf))` is 3.494 nV/√Hz at 300 K. MIC normal-mode output impedance is 250 Ω typical; required load is ≥25 kΩ, with Fig.11 capacitive limits. These facts do not validate the complete switched network or the 1.5 µVrms allocation. Noise/stability/CMRR analysis is **UNKNOWN**, pending corrected topology and actual passives.
- **ADC interface:** intended P→AINxP, N→AINxN, buffered VREF common mode, 47 Ω on each leg and 1 nF C0G across each ADC pair. No ADC-side circuit or hierarchical output wiring implemented. Full-scale, source impedance, protection and settling acceptance remain **UNKNOWN**.
- **Power / safe state:** retain Sheet 2 `2V8_MIC` (2.758–2.842 V), `5V_AFE` (4.858943–5.157889 V), qualified `ANALOG_PWR_EN`, and Phase 3E/3F independent analog shutdown and explicit rearm. Both rail operating ranges fit the intended microphone/op-amp supply ranges. No shutdown bypass introduced. Complete back-power and transient safety cannot pass with B1 unresolved.
- **Channel consistency / passives:** no four-channel topology exists to compare. Gain-resistor tolerance is frozen at 0.1%; coupling/filter part numbers, effective capacitance, leakage, protection capacitance and channel phase matching remain unverified. No precision or protection part was invented.
- **Save/reload / ERC:** **NOT RUN** because no schematic was changed and implementation stopped on electrical-contract blockers. No ERC PASS, new ERC violation classification, suppression or waiver is claimed. B1/B2 are **BLOCKING engineering issues**, not ERC findings. KiCad CLI availability was not established.
- **Future physical validation:** microphone noise, acoustic gain, CMRR, distortion, balanced-source noise, switch leakage, ADC settling, op-amp stability, all rail permutations, startup/shutdown transients and channel matching remain unmeasured.

PHASE 4C: BLOCKED
