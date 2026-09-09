# Phase 3A - PGOOD Contract Correction

Date: 2026-09-09 (Europe/Istanbul)

## 1. Original contradiction

Phase 3 approved `12V_PROTECTED = 10.4 V` as the minimum normal voltage but assigned downstream sequencing to the TPS26630 PGOOD output using `PGTH = 468 kohm / 56.0 kohm`. That divider has a nominal falling threshold of `10.508 V` and a threshold/resistor-only maximum of `10.780 V`; Phase 4A therefore proved that PGOOD can deassert while `12V_PROTECTED` is still within its approved normal range. Including the TPS26630 guaranteed `+/-150 nA` PGTH leakage widens the same falling range to approximately `10.111-10.850 V`, so leakage cannot rescue the contract.

## 2. Root cause

The TPS26630 PGTH comparator was asked to serve two different purposes with insufficient tolerance budget: output-state/recovery sensing inside the eFuse and a precise system-valid boundary only `0.301 V` above the previously calculated worst-case eFuse UVLO falling boundary (`10.099 V`). Its guaranteed PGTH falling reference spans `1.09-1.15 V`, before divider tolerance or leakage. No divider ratio can place that full span both below `10.4 V` and with useful guaranteed separation above the old UVLO boundary. The error was freezing typical-centered divider values without proving the complete guaranteed interval against both adjacent limits.

## 3. Corrected PGOOD architecture

The corrected architecture is **CONFIRMED for Phase 4A implementation**:

- Keep `TPS26630RGER` as the eFuse, but tie its `PGTH` pin directly to `POWER_GND`. Do not use or rename its native `PGOOD` output as the system-valid signal. TI states that grounding PGTH pulls native PGOOD low and disables fast recovery; every UVLO/OVP recovery therefore uses the selected `CdVdT=47 nF` controlled ramp. This removes the recovery-mode ambiguity while preserving inrush control [TI TPS2663x, SLVSE94G, Rev.G, sections 8.3.2 and 8.3.2.1, p.19](../../datasheets/power/tps2663_datasheet_rev_g.pdf).
- Add `TPS3760A012DYYR` as the protected-rail supervisor. This exact active-production variant is adjustable `0.8 V`, undervoltage, active-low, open-drain, with `2%` hysteresis. Power `VDD` from `12V_PROTECTED`, bypass it locally with `0.1 uF`, and sense `12V_PROTECTED` through `Rtop=115 kohm` and `Rbottom=10.0 kohm`, both `0.1%`. Pull its `RESET` output up to `3V8_PRE` with `10.0 kohm`; name that active-high system-valid node `PGOOD_12V`. Leave `CTS` and `CTR/MR` open for the manufacturer-defined fastest assertion/release behavior. `PGOOD_12V` replaces every downstream use of the former eFuse PGOOD [TI TPS3760, SBVS420A, Rev.A, sections 5, 6, 7.3-7.6, 8.3.3-8.3.5, 8.4 and 9.2, pp.3-9, 17-28](https://www.ti.com/lit/ds/symlink/tps3760.pdf).
- Replace the TPS26630 shared UVLO/OVP ladder with `R1=316 kohm`, `R2=13.3 kohm`, and `R3=30.4 kohm`, all `0.1%`, in TI order `IN_SYS -> R1 -> UVLO -> R2 -> OVP -> R3 -> POWER_GND`. `R1` exceeds TI's `300 kohm` minimum for reverse-polarity applications. The revised UVLO is a secondary hard cutoff below `PGOOD_12V`; OVP remains above the `13.2 V` normal maximum.
- Preserve the existing hardware-safe latch. Low `PGOOD_12V` or low eFuse `FLT` asserts the safe state. Recovery may re-enable rails only through the existing startup state machine; it may never restore amplifier PLAY automatically.

Because the supervisor is powered directly from `12V_PROTECTED`, it is functional before `3V8_PRE` can pull `PGOOD_12V` high. On startup its open-drain output holds the node low until both its supply/startup condition and rising sense threshold are satisfied. On shutdown it pulls the node low at the falling threshold; the eFuse UVLO and `FLT` remain an independent secondary shutdown path. No circular enable dependency is introduced.

## 4. Threshold calculations

For the TPS3760 divider, with `Rt=115 kohm`, `Rb=10.0 kohm`, sense current `Is`, and sense threshold `Vs`:

`V12 = Vs * (1 + Rt/Rb) + Is * Rt`

The nominal divider factor is `12.5`. Worst cases use the TPS3760 guaranteed `VITN=0.792-0.808 V`, `ISENSE <= 100 nA` conservatively treated as `+/-100 nA`, `2%` hysteresis with `+/-1.5%` hysteresis accuracy, and opposite-direction `0.1%` resistor limits.

| `PGOOD_12V` event | Nominal | Worst-case minimum | Worst-case maximum |
| --- | ---: | ---: | ---: |
| Deassert while falling | `0.800 * 12.5 = 10.000 V` | `9.870 V` | `10.130 V` |
| Assert while rising | `(0.800 + 0.016) * 12.5 = 10.200 V` | `10.067 V` | `10.333 V` |
| Hysteresis | `0.016 * 12.5 = 0.200 V` | `0.197 V` | `0.203 V` |

For the revised TPS26630 ladder, nominal divider factors are `8.231121` at UVLO and `11.832237` at OVP. The bounds below include `0.1%` tolerance on all three resistors, guaranteed comparator thresholds (`1.176-1.224 V` rising and `1.09-1.15 V` falling), and independent `+/-150 nA` UVLO/OVP pin leakage:

| eFuse event at `IN_SYS` | Nominal | Worst-case minimum | Worst-case maximum |
| --- | ---: | ---: | ---: |
| UVLO turn-on, rising | `9.877 V` | `9.583 V` | `10.173 V` |
| UVLO turn-off, falling | `9.235 V` | `8.876 V` | `9.563 V` |
| OVP turn-off, rising | `14.199 V` | `13.793 V` | `14.606 V` |
| OVP recovery, falling | `13.276 V` | `12.777 V` | `13.729 V` |

The TPS3760 timing behavior is deterministic in ordering: the active-low open-drain output asserts on undervoltage and releases only after crossing `VITN + VHYS`; with delay pins open, TI specifies `8-17 us` sense-detect delay at the stated `20%` overdrive test condition and a fastest reset-release mode. The existing downstream supervisor delays, DSP reset, audio-safe latch, and no-automatic-PLAY rules remain unchanged.

## 5. Worst-case margins

| Margin check | Guaranteed result | Disposition |
| --- | ---: | --- |
| Normal-range hold: `10.400 - PGOOD_fall,max` | `10.400 - 10.130 = 0.270 V` | PGOOD cannot deassert anywhere in the approved normal protected-rail range. |
| Normal-range cold assertion: `10.400 - PGOOD_rise,max` | `10.400 - 10.333 = 0.067 V` | Even a monotonic ramp to exactly `10.4 V` crosses the worst-case assertion threshold; the separate connector cold-start requirement remains `11.5 V`. |
| Fault separation: `PGOOD_fall,min - UVLO_fall,max` | `9.870 - 9.563 = 0.307 V` | System safe-state authorization is removed before the eFuse's secondary hard cutoff at every combined tolerance corner. |
| OVP separation from normal maximum | `13.793 - 13.200 = 0.593 V` | Revised shared ladder cannot create OVP inside the normal input range. |
| Guaranteed PGOOD hysteresis | `0.197-0.203 V` | The release boundary is separated from the trip boundary; threshold chatter is prevented without relying on a typical-only value. |

The `0.270 V` low-side normal margin and `0.307 V` fault-boundary margin are both larger than rounding, leakage, and resistor effects already included in the bounds. The fault-separation comparison is conservative: `PGOOD_12V` senses eFuse OUT while UVLO senses `IN_SYS`, and any positive forward path drop makes the OUT threshold occur at a still-higher `IN_SYS` voltage. No downstream rail is disabled at `12V_PROTECTED >= 10.4 V`, while an actual brownout first asserts the hardware-safe path and subsequently reaches the independent eFuse cutoff if the input continues to fall.

## 6. Required Phase 3 contract amendment

Phase 3 sections 4.1, 4.2, 5.1, 6.2, 6.3, and 14 are amended as follows; all unrelated Phase 3 decisions remain frozen:

- Replace the TPS26630 `468 kohm / 56.0 kohm` PGTH-based sequencing requirement with the TPS3760A012DYYR `115 kohm / 10.0 kohm` `PGOOD_12V` contract above.
- Tie TPS26630 PGTH low and treat native PGOOD as unused, not as a sequencing or safe-state signal.
- Replace the UVLO/OVP ladder `1.05 Mohm / 35.2 kohm / 100 kohm` with `316 kohm / 13.3 kohm / 30.4 kohm`, all `0.1%`, and use the bounded thresholds in section 4.
- Keep `12V_PROTECTED = 10.4-13.2 V` normal and the connector cold-start requirement of at least `11.5 V`; neither is raised to preserve the former implementation.
- `PGOOD_12V` low and TPS26630 `FLT` low remain hardware-dominant inputs to the existing safe-state latch. The safe state and ordered restart requirements are unchanged.

## 7. Exact instructions for Phase 4A implementation

1. On Sheet 1, delete the planned `468 kohm / 56.0 kohm` PGTH divider. Wire TPS26630 `PGTH` directly to `POWER_GND`. Leave the TPS26630 native `PGOOD` output electrically unused and explicitly mark it unused; do not connect it to `PGOOD_12V`.
2. Implement the TPS26630 shared ladder exactly as `IN_SYS -> 316 kohm -> UVLO -> 13.3 kohm -> OVP -> 30.4 kohm -> POWER_GND`; use `0.1%` resistors. Do not change `RILIM=3.24 kohm`, `CdVdT=47 nF`, MODE-open latch behavior, reverse-polarity parts, or the remaining Phase 3 protection topology.
3. Add `TPS3760A012DYYR` on Sheet 1. Connect pin 1 `VDD` to `12V_PROTECTED` with a local `0.1 uF` ceramic to `POWER_GND`; pins 8 and 13 to `POWER_GND`; pin 3 `SENSE` to the midpoint of `115 kohm` from `12V_PROTECTED` and `10.0 kohm` to `POWER_GND`, both `0.1%`; pin 6 active-low open-drain `RESET` to `PGOOD_12V`; leave pin 10 `CTS` and pin 9 `CTR/MR` open; leave pins 2, 4, 5, 7, 11, 12, and 14 unconnected as the datasheet requires.
4. Pull `PGOOD_12V` up to `3V8_PRE` with `10.0 kohm`. Route `PGOOD_12V` to every downstream enable qualifier and hardware-safe input previously assigned to eFuse PGOOD. Retain TPS26630 `FLT` as a separate wired hardware-fault input. Provide labeled test points for `12V_PROTECTED`, TPS3760 `SENSE`, `PGOOD_12V`, and TPS26630 `FLT`.
5. Preserve passive-safe defaults: before `PGOOD_12V` is high, hold `1V8_DSP_REF_ANA` and all later rails disabled, assert DSP/ADC reset, disable clock/audio buffer outputs, and hold amplifier MUTE/STANDBY low. `3V8_PRE` alone may start directly from `12V_PROTECTED` as already frozen.
6. In the Phase 4A calculation/validation artifact, reproduce all section 4 bounds including resistor and input-leakage corners. Verify by ERC and transient simulation or bench test, as applicable to Phase 4A, that a monotonic startup at the `11.5 V` connector condition releases `PGOOD_12V` once, operation down to `12V_PROTECTED=10.4 V` never deasserts it, a falling ramp asserts safe state before UVLO opens, and recovery uses the TPS26630 dVdT ramp. Do not proceed to Phase 4B under this authorization.

PHASE 3A: PASS
