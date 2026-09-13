# Phase 3B - Power supervisor contract correction

Date: 2026-09-13  
Scope: downstream rail supervision, sequencing, reset, and watchdog contract only. No KiCad file was created or modified.

**Phase 3D amendment (2026-09-13):** the [final Sheet 2 audit](phase_3d_final_power_contract_audit.md) retains every LTC2964 divider and fault threshold below, but corrects the realized 1.8 V, core, and DMC regulator ranges. The resulting release margins are +19.462 mV, +20.072 mV, and +13.314 mV respectively; the Phase 3C `3V3_SYS` margin remains +54.202 mV. The tables below preserve the Phase 3B decision basis and are historical where they use the then-approved regulator ranges.

## 1. Discovered contradiction and root cause

Phase 4B found that the Phase 3 `TPS386000RGPR` analysis bounded only the falling threshold. The device adds positive-going hysteresis before releasing each reset output. TI specifies a 396-404 mV negative threshold and 3.5 mV typical, 10 mV maximum positive hysteresis, with no guaranteed positive minimum. The prior contract therefore could detect an undervoltage but could not guarantee that a valid rail would ever cross the worst-case release boundary [SUPV pp.7, 9, 23].

For an external divider, the rail-referred corner is

`Vrail = Vsense * (1 + Rtop/Rbottom) + Isense * Rtop`.

The calculations below use 0.1% resistor corners and the specified +/-25 nA TPS386000 sense current. Where a minimum hysteresis is not guaranteed, the rising lower bound conservatively equals the falling lower bound; the rising upper bound uses the 10 mV maximum. `Release margin = approved rail minimum - rising maximum`. `Fault margin = falling minimum - device safe minimum`.

## 2. Existing four-channel contract

| Rail / old channel | Nominal; approved range | Device safe minimum | Old divider; nominal fall / typical rise | Guaranteed fall range | Guaranteed rise range | Guaranteed rail hysteresis | Release margin | Fault margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `1V8_DSP_REF_ANA` / SENSE1 | 1.82 V; 1.775-1.866 V | 1.710 V | 33.8k/10.0k; 1.752 / 1.767 V | 1.730962-1.773100 V | 1.730962-1.816967 V | 0-43.868 mV | **-41.967 mV** | +20.962 mV |
| `1V0_DSP_CORE` / SENSE2 | 1.00 V; 0.990-1.010 V | 0.950 V | 14.3k/10.0k; 0.972 / 0.981 V | 0.960791-0.983235 V | 0.960791-1.007563 V | 0-24.329 mV | **-17.563 mV** | +10.791 mV |
| `1V35_DSP_DMC` / SENSE3 | 1.36 V; 1.325-1.393 V | 1.283 V | 22.5k/10.0k; 1.300 / 1.311 V | 1.284658-1.315383 V | 1.284658-1.347928 V | 0-32.545 mV | **-22.928 mV** | +1.658 mV |
| `3V3_SYS` / SENSE4L | 3.30 V; 3.267-3.333 V | 3.130 V | 69.8k/10.0k; 3.192 / 3.220 V | 3.152814-3.231312 V | 3.152814-3.311252 V | 0-79.940 mV | **-44.252 mV** | +22.814 mV |

All four release margins are negative. The DMC falling margin is also only 1.658 mV after guaranteed corners. This is an architectural failure, not a startup-delay issue: a delay cannot begin until the comparator has released.

Changing only the TPS386000 divider values cannot fix it. Even before resistor and input-current errors, its guaranteed ratio between the maximum release boundary and minimum falling boundary is `414/396 = 1.04545`. A feasible threshold window would require `approved minimum / safe minimum > 1.04545`; the four ratios are only 1.0380, 1.0421, 1.0327, and 1.0438. No divider can place both guaranteed boundaries inside any of these windows.

## 3. Correction options

| Option | Finding | Decision |
| --- | --- | --- |
| A - correct TPS386000 dividers | Mathematically infeasible for all four rails because the threshold/hysteresis span exceeds each available supervision window. | Reject. |
| B - regulator-native PGOOD | TPS62135 PGOOD is open drain and asserts at 93%-98% of output, with 3%-4.5% falling hysteresis. Release margin is positive for 1.0 V and 3.3 V, but the lowest fault points are 0.885 V and 2.9205 V, below the 0.950 V and 3.130 V safe minima. TPS7A4901 and TPS7A20 provide no PGOOD output. | Reject as the safety supervisor; native PGOOD may remain diagnostic only. |
| C - replacement supervisor | TPS3704 offers four channels but groups the quad configuration into two outputs and has no watchdog. Four TPS3890 devices would meet accuracy needs but multiply parts and still need aggregation and a watchdog. LTC2964 provides four independently configurable +/-0.5% comparators, individual outputs, and one delayed aggregate reset. | Select LTC2964 plus a separate watchdog. |
| D - native-PGOOD hybrid | Native signals do not remove the need for accurate supervision of all four DSP rails, so aggregation becomes more complex without adding guaranteed fault margin. | Reject. |

## 4. Selected architecture and thresholds

**TPS386000 classification: REPLACE.** Use `LTC2964HUDC#PBF` (H grade, -40 C to +125 C, 20-lead 3 mm x 4 mm UDC QFN) as the four-channel supervisor and `TPS3431SDRBR` as the watchdog [SUPV4 pp.1-4; WDT pp.1-3]. The Phase 3 regulators, rail ranges, and Phase 3A TPS3760 `PGOOD_12V` contract do not change.

Power LTC2964 from `3V8_PRE` and bypass VCC with at least 0.1 uF. Tie `PG1`-`PG4` directly to `REF`, selecting +ADJ mode; do not add PG capacitance. Each channel uses a 0.1% divider with a 10.0 kohm bottom resistor. The device uses a 497.5-502.5 mV threshold and specifies +/-15 nA monitor input current over the H-grade range. It intentionally uses comparator filtering without threshold hysteresis, so the guaranteed rising and falling threshold ranges are identical [SUPV4 pp.3, 8, 12-16].

The new corner equations are:

- `Vfall,min = 0.4975 * (1 + 0.999*Rtop / (1.001*Rbottom)) - 15 nA * 0.999*Rtop`
- `Vfall,max = 0.5025 * (1 + 1.001*Rtop / (0.999*Rbottom)) + 15 nA * 1.001*Rtop`
- `Vrise,min/max = Vfall,min/max`; guaranteed hysteresis is 0 V.

| Channel / rail | Divider top/bottom | Nominal threshold | Guaranteed falling threshold | Guaranteed rising threshold | Guaranteed hysteresis | Release margin | Fault margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 / `1V8_DSP_REF_ANA` | 24.9k / 10.0k, 0.1% | 1.7450 V | 1.733427-1.756604 V | 1.733427-1.756604 V | 0 V | **+18.396 mV** | **+23.427 mV** |
| V2 / `1V0_DSP_CORE` | 9.31k / 10.0k, 0.1% | 0.9655 V | 0.959608-0.971404 V | 0.959608-0.971404 V | 0 V | **+18.596 mV** | **+9.608 mV** |
| V3 / `1V35_DSP_DMC` | (15.8k + 280) / 10.0k, all 0.1% | 1.3040 V | 1.295641-1.312379 V | 1.295641-1.312379 V | 0 V | **+12.621 mV** | **+12.641 mV** |
| V4 / `3V3_SYS` | 53.6k / 10.0k, 0.1% | 3.1800 V | 3.157969-3.202097 V | 3.157969-3.202097 V | 0 V | **+64.903 mV** | **+27.969 mV** |

Every channel has a positive guaranteed release allowance and a separate positive fault-detection allowance after all specified threshold, temperature, divider, and input-current corners. The smallest allowance is 0.89% of its adjacent safe/valid boundary, so none is a zero or rounding-only result. Divider current is approximately 50 uA per channel at threshold, so monitor loading is negligible relative to the approved rail allocations.

## 5. Startup, reset, brownout, and recovery contract

1. Phase 3A `PGOOD_12V` becomes valid only after `12V_PROTECTED` crosses its guaranteed rising boundary. It enables `1V8_DSP_REF_ANA`; the hardware-safe latch remains asserted.
2. LTC2964 V1 observes the 1.8 V rail. Its real-time open-drain `OUT1` releases at the corrected threshold and directly enables `1V0_DSP_CORE`, `1V35_DSP_DMC`, `3V3_ADC_A`, and `2V8_MIC`. Per Phase 3C, `3V3_SYS` enables through its local `OUT1 AND PGOOD_12V` gate.
3. V2, V3, and V4 verify the three remaining DSP rails. The common open-drain `RST` remains asserted while any channel is invalid.
4. Tie LTC2964 `RT` to VCC for the manufacturer-guaranteed 160-240 ms release delay. All four rails must remain valid for this full interval; any invalid channel restarts the timer. The open-drain `RST` output then releases the separate `RAILS_OK` node.
5. `RAILS_OK` enables TPS3431. Its open-drain `ENOUT`, wired with `WDO` at `SYS_HWRST`, adds 170-230 ms, so DSP reset releases 330-470 ms after all rail thresholds became valid. This provides deterministic anti-chatter behavior and covers the 3 ms maximum clock-fanout startup. DSP boot then begins. ADC and amplifier initialization proceeds under the existing Phase 3 safe-state sequence; no amplifier PLAY state is restored automatically.

If V1 fails, `OUT1` immediately disables the downstream regulator fanout and common RST asserts. If V2, V3, or V4 fails, common RST and the hardware-safe latch assert while rails remain enabled for controlled recovery. At 10% overdrive the specified comparator-to-output delay is 20-40 us; reset release always waits 160-240 ms. On recovery, every rail must again remain above its threshold for the full delay. Phase 3A `PGOOD_12V` low or eFuse FLT independently asserts hardware safe state and disables the downstream sequence. Commanded power-down retains the Phase 3 order, with DSP reset asserted before downstream rails and the 1.8 V rail removed last [SUPV4 pp.3, 5, 8, 11, 15-16].

## 6. Watchdog contract

Use `TPS3431SDRBR`, powered from `3V3_SYS` with 0.1 uF bypass. Its `EN` input is driven only by the separate LTC2964 `RAILS_OK` node, so WDO assertion cannot disable its own timer. Tie `SET1` high; drive `WDI` from the DSP and never leave it at an intermediate level. Leave `CWD` unconnected for the factory-guaranteed 1.36-1.84 s timeout. Tie open-drain `ENOUT` and `WDO` together at `SYS_HWRST` with one 10.0 kohm pullup to `3V3_SYS`; also feed WDO into the hardware-safe latch. ENOUT adds 170-230 ms between RAILS_OK and reset release. Because the watchdog starts when RAILS_OK rises, firmware retains at least `1.36 s - 0.23 s = 1.13 s` after SYS_HWRST release to issue its first valid WDI falling edge. A timeout holds WDO low for 170-230 ms while EN remains high [WDT pp.3, 9-14].

## 7. Exact Phase 4B implementation instructions

- Remove TPS386000 and its four dividers, CT connections, and integrated watchdog wiring. Do not change Sheet 1 or the Phase 3A TPS3760 network.
- Create or verify the LTC2964 symbol against this UDC pin map: 1 RDIS, 2 MR, 3 DVCC, 4 VCC, 5 RST, 6 GND, 7 OUT1, 8 OUT2, 9 OUT3, 10 OUT4, 11 RT, 12 PG4, 13 PG3, 14 PG2, 15 PG1, 16 REF, 17 V4, 18 V3, 19 V2, 20 V1, exposed pad 21 GND. Connect pad 21 to ground even though the datasheet permits it to be open.
- Tie RDIS, MR, and RT to VCC; tie DVCC to ground; tie PG1-PG4 to REF; add the four exact 0.1% dividers above and Kelvin-ground their bottoms. Realize the V3 16.08 kohm top value as series 15.8 kohm and 280 ohm, both 0.1%. Pull OUT1 to `3V8_PRE` through 10.0 kohm. Pull RST to `3V3_SYS` through 10.0 kohm and name this isolated node `RAILS_OK`; do not connect it directly to `SYS_HWRST`. Leave OUT2-OUT4 unconnected except optional labeled test points.
- Verify the TPS3431 symbol against: 1 VDD, 2 CWD, 3 EN, 4 GND, 5 SET1, 6 WDI, 7 WDO, 8 ENOUT; connect the thermal pad to ground. Leave CWD unconnected, drive EN from RAILS_OK, tie SET1 to VDD, tie ENOUT and WDO at SYS_HWRST, and populate the bypass/pullup in section 6.
- Preserve the Phase 3C local `OUT1 AND PGOOD_12V` gate on the `3V3_SYS` enable; do not join the two open-drain status nodes. Preserve the hardware-safe latch dominance: low `PGOOD_12V`, eFuse FLT, low LTC2964 RST, or low TPS3431 WDO asserts safe state. Recovery may restart rails through the sequence but may not restore amplifier PLAY.
- ERC and bench/transient validation remain Phase 4B work. Bench validation must sweep input/load/temperature corners and show all four monitored rails cross their release thresholds and assert reset before their device minima.

## 8. Evidence and gate

The correction uses the existing TPS386000, TPS62135, TPS7A49, and TPS7A20 documents plus newly introduced official LTC2962/LTC2963/LTC2964 Rev.0, TPS3431 Rev.A, TPS3704 Rev.E, and TPS3890 Rev.A evidence indexed under `SUPV4`, `WDT`, `SUPV_ALT4`, and `SUPV_ALT1`. The LTC2964 official PDF was reviewed through the manufacturer's published PDF endpoint; repeated attempts to persist a local copy timed out, so the evidence index records that boundary. No unofficial source was used.

All four channels now have guaranteed positive release and fault margins, no positive-going hysteresis is hidden, and reset/brownout recovery is deterministic. Phase 4B may resume only under this corrected contract.

PHASE 3B: PASS
