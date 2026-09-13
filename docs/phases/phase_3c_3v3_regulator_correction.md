# Phase 3C - 3.3 V regulator contract correction

Date: 2026-09-13  
Scope: correction of the `3V3_SYS` regulator branch only. No KiCad file was created or modified, and Phase 4B was not resumed.

**Phase 3D amendment (2026-09-13):** the [final Sheet 2 audit](phase_3d_final_power_contract_audit.md) changes the pre-rail static range to 3.746849-3.841293 V inside a 3.700-3.900 V approved operating band. The `3V3_SYS` TPS62135 input, divider, static range, and supervision margins below remain unchanged. Only the enable-gate high-level arithmetic is updated to the corrected pre operating minimum.

## 1. Original contradiction

Phase 3 selected TPS62135 in forced-PWM mode for `3V8_PRE -> 3V3_SYS` and treated the output as 3.267-3.333 V. Phase 4B found that this range was not manufacturer-backed. TI guarantees the TPS62135 feedback-voltage accuracy of +/-1% in PWM mode only when `VIN >= VOUT + 1 V`. The then-approved `3V8_PRE` range was 3.762-3.838 V, only about 0.5 V above the 3.3 V output. Even its maximum input could not meet the condition for any output near 3.3 V [TI TPS62135, SLVSBH3B Rev.B, section 7.5 p.6 and sections 9.4.1-9.4.3 pp.10-11](https://www.ti.com/lit/ds/symlink/tps62135.pdf).

The 100%-duty discussion explains typical low-headroom operation but does not replace the missing guaranteed accuracy limit. The old branch therefore had an `UNKNOWN` guaranteed minimum, and its Phase 3B supervisor-release margin could not be claimed.

## 2. Root cause

The regulator was applied in a permitted operating mode but outside the condition attached to the required accuracy guarantee. The prior calculation also treated +/-1% feedback accuracy as a complete output tolerance without including the external divider and the 70 nA maximum FB input-leakage specification. Both issues must be closed to obtain a guaranteed rail contract.

## 3. Evaluated corrections

| Option | Finding | Decision |
| --- | --- | --- |
| Keep `3V8_PRE -> TPS62135 -> 3V3_SYS` | Under the then-approved range, the input remained at least 0.419 V short of the condition even if the lowest corrected output corner was used: `3.762 < 3.256299 + 1`. No substitute low-headroom accuracy guarantee is published. | Reject. |
| Feed TPS62135 from `12V_PROTECTED` | The approved 10.4-13.2 V input is inside the 3-17 V recommended range. At the maximum corrected output, the accuracy condition requires only 4.337821 V, leaving 6.062179 V of additional margin at the 10.4 V minimum input. TI also shows a 12 V to 3.3 V TPS62135 application and publishes 3.3 V/12 V forced-PWM characterization [BUCK pp.4-6, 15, 18, 25, 30]. | **Select.** |
| Replace TPS62135 with a low-headroom buck or LDO from `3V8_PRE` | Feasible in principle, but it adds a new component contract and offers no correctness advantage after the existing converter is moved to its explicitly guaranteed 12 V operating condition. | Do not select. |
| Raise `3V8_PRE` | It would have to exceed 4.337821 V at its minimum corner and would change the input, loss, and startup contracts of every existing 3.8 V-fed branch. | Reject; disproportionate and creates downstream re-verification. |
| Use a boost-buck or other topology | There is no need to both step up and step down when a protected 10.4-13.2 V source is already present. | Reject. |

## 4. Component decision and exact configuration

**TPS62135 classification: RETAIN WITH CORRECTED INPUT.**

Retain exact orderable `TPS62135RGXR` in the RGX 11-pin VQFN package and change only the `3V3_SYS` instance as follows:

- connect VIN to `12V_PROTECTED`, not `3V8_PRE`;
- add exact `SN74LV1T08DBVR` as a branch-local two-input positive-AND gate, powered from `3V8_PRE` and bypassed with 0.1 uF. Connect input A to LTC2964 `OUT1`, input B to `PGOOD_12V`, output Y to this TPS62135 EN, and add 1.0 Mohm from EN to ground. This preserves the logical enable condition `OUT1 AND PGOOD_12V` without joining the two open-drain status nodes;
- tie MODE high for forced PWM; tie VSEL low and FB2 to ground; leave native PG intentionally open because LTC2964 remains the safety supervisor;
- connect VOS directly to the positive terminal of the local output-capacitor bank;
- set the output with `Rtop=37.1 kohm` from VOS/output to FB and `Rbottom=10.0 kohm` from FB to ground, both 0.1%; Kelvin-return the bottom resistor to regulator ground;
- retain `CSS=10 nF` from SS/TR to ground;
- use a 1.0 uH nominal inductor whose effective inductance is at least 0.8 uH across tolerance and bias, saturation-current rating is at least 5 A, and DCR is no more than 30 milliohms;
- place at least 10 uF nominal X7R/X5R input capacitance rated at least 25 V directly at VIN-GND and guarantee at least 3 uF effective after DC bias and tolerance;
- provide at least 22 uF effective X7R/X5R local output capacitance after DC bias and tolerance. Directly connected effective output capacitance must remain at or below the datasheet's 200 uF limit; any additional distributed capacitance must satisfy TI's series-resistance/multiple-load guidance.

The AND gate's supply range is 1.6-5.5 V and both inputs accept up to 5.5 V. The two inputs are either pulled to `3V8_PRE` or asserted low. The most conservative published LV1T high threshold is 2.11 V, below the Phase 3D 3.700 V operating minimum. With the output load limited to the 1.0 Mohm pulldown plus the TPS62135 100 nA maximum EN leakage, it is below 20 uA: TI guarantees `VOH >= VCC-0.1 V` and `VOL <= 0.1 V`. Thus EN is at least 3.600 V when enabled, well above its 0.83 V maximum rising threshold, and at most 0.1 V when disabled, below its 0.67 V minimum falling threshold [TI SN74LV1T08, SCLS739F Rev.F, sections 6.1-6.5 pp.5-7](https://www.ti.com/lit/ds/symlink/sn74lv1t08.pdf).

The local gate also prevents a new power-down overstress. `PGOOD_12V` must fall by 9.870 V at the latest approved falling corner, so the gate drives EN low while TPS62135 VIN is still far above the 3.8 V enable level. If `3V8_PRE` is absent, the AND output is not driven high and the 1.0 Mohm resistor holds EN low. The TPS62135 `EN <= VIN + 0.3 V` absolute limit is therefore preserved through normal startup and the approved shutdown/brownout sequence.

This preserves the rail voltage requirement, regulator, enable order, active discharge, supervisor, and all downstream loads. Only the regulator input source, its feedback/input network, and branch-local enable qualification change.

The normal regulator input is 10.4-13.2 V. The upstream eFuse's bounded maximum OVP rising point is 14.606 V, still below the TPS62135 17 V recommended maximum; a sustained +24 V abnormal connector input is cut off upstream and is not a TPS62135 operating point. The device's 20 V absolute maximum is not used as a functional rating.

## 5. Guaranteed output range

TI specifies `VFB=0.7 V`, +/-1% in PWM mode when `VIN >= VOUT + 1 V`, and FB input leakage no greater than 70 nA over the -40 C to +125 C electrical-characteristics envelope. For a conservative result, the unspecified leakage direction is allowed to take either sign. With 0.1% divider corners:

`VOUT = VFB * (1 + Rtop/Rbottom) +/- |IFB| * Rtop`

`VOUT,min = 0.7*0.99*(1 + 37.1k*0.999/(10.0k*1.001)) - 70nA*(37.1k*0.999) = 3.256299 V`

`VOUT,max = 0.7*1.01*(1 + 37.1k*1.001/(10.0k*0.999)) + 70nA*(37.1k*1.001) = 3.337821 V`

The nominal divider result is 3.297 V. The guaranteed static DC range is therefore **3.256299-3.337821 V** across the TPS62135 specified junction-temperature range, the approved 10.4-13.2 V input, the 0-200 mA load allocation, and the stated component tolerances, provided forced PWM and the capacitor/inductor contract above are implemented. This range is inside every frozen destination limit: ADSP-21569 VDD_EXT 3.13-3.47 V, ADAU1978 IOVDD 1.62-3.6 V, and TAS6424E-Q1 VDD 3.0-3.5 V.

At the worst headroom corner:

- required input for the accuracy guarantee: `3.337821 + 1 = 4.337821 V`;
- available minimum input: `10.4 V`;
- margin beyond the required 1 V headroom: `10.4 - 4.337821 = 6.062179 V`.

The result is not based on the 100%-duty/dropout mode and remains valid throughout the approved input range.

## 6. Load, current, efficiency, and thermal contract

| Item | Corrected contract / result | Status |
| --- | --- | --- |
| Maximum required load | 200 mA, unchanged from Phase 3 | **CONFIRMED project allocation** |
| Converter capability | 4 A continuous; 4.8 A minimum high- and low-side current limit | **CONFIRMED manufacturer limit** |
| DC current margin | 3.8 A to the 4 A rating; converter rating is 20x the allocation | **PASS** |
| Inductor ripple screen | At 13.2 V and 0.8 uH effective, TI equation 10 gives at most 1.65 A peak-to-peak. At 200 mA, the screened positive peak is 1.025 A; at no load the 0.825 A negative half-ripple remains below the 1.5 A typical negative-current limit. The frozen 5 A saturation constraint is ample. | **PASS for schematic contract; verify the selected inductor curve in Phase 4B** |
| Efficiency | TI Figure 13 shows approximately mid-60% typical efficiency at 12 V, 3.3 V, 200 mA, forced PWM, 25 C. The adjacent 10 V and 15 V curves bound the approved input range at roughly 60%-70% typical. TI publishes no guaranteed minimum efficiency. | **PROVISIONAL typical-data estimate** |
| Thermal dissipation | At 3.337821 V and 200 mA, output power is 0.6676 W. Using 60% as a conservative reading of the adjacent typical curve gives about 0.445 W converter loss. A 0.50 W schematic thermal allocation and TI's 38.4 C/W JEDEC `RthetaJA` imply a first-order 19.2 C rise, or about 59 C junction at the approved 40 C prototype ambient. | **PASS as a feasibility screen; PCB/bench thermal validation remains required** |

The typical efficiency curve is not converted into a false guarantee. The large temperature margin shows that the reroute is thermally practical at the frozen 200 mA allocation; Phase 4B must still select the exact inductor/capacitors, implement TI's exposed-pad/thermal-via layout, and confirm dissipation and junction estimate on hardware.

## 7. Startup, enable, and shutdown behavior

- VIN is present whenever `12V_PROTECTED` is present, but the converter remains off until both `PGOOD_12V` and LTC2964 `OUT1` are high through the local SN74LV1T08 gate. `OUT1` still cannot release until `1V8_DSP_REF_ANA` is valid, so the VDD_REF-before-VDD_EXT sequence is unchanged.
- TI guarantees a maximum 300 us delay from EN high to first switching when VIN is already applied. The 10 nF SS/TR capacitor gives approximately `10 nF * 0.7 V / 2.5 uA = 2.8 ms` nominal ramp; the 2.5 uA source tolerance is +/-0.2 uA. The existing requirement to verify at least 100 us realized rise/fall time remains.
- When EN is low, TPS62135 enters shutdown and turns off both power FETs. Its approximately 100 ohm active output-discharge path is available after the device has been enabled once, preserving the defined 3.3 V off state.
- On input UVLO or thermal shutdown, switching stops and a new soft-start occurs on recovery. `PGOOD_12V`, LTC2964, and the hardware-safe latch retain their existing dominance; no amplifier PLAY state is restored automatically.

## 8. Phase 3B supervision recalculation

The LTC2964 V4 configuration does not change: +ADJ mode, `Rtop=53.6 kohm`, `Rbottom=10.0 kohm`, both 0.1%. Its guaranteed falling and rising threshold range remains 3.157969-3.202097 V.

| Check | Calculation | Corrected margin | Result |
| --- | --- | ---: | --- |
| Supervisor release | `guaranteed rail minimum - maximum rising threshold = 3.256299 - 3.202097` | **+54.202 mV** | **PASS** |
| Fault detection | `minimum falling threshold - ADSP-21569 VDD_EXT minimum = 3.157969 - 3.130000` | **+27.969 mV** | **PASS** |

The threshold does not need to change. Phase 3B's original +64.903 mV release calculation is preserved as historical reasoning for its then-assumed 3.267 V rail minimum; this Phase 3C value supersedes only that margin. The fault-detection margin is unchanged.

## 9. Schematic-ready implementation delta

When Phase 4B is separately authorized:

1. For only the `3V3_SYS` TPS62135 instance, connect VIN and its local input capacitor to `12V_PROTECTED`.
2. Use the exact configuration and passive electrical limits in section 4, including the 25 V input-capacitor rating and `37.1 kohm / 10.0 kohm` 0.1% feedback divider.
3. Preserve the existing LTC2964 `OUT1`, V4 divider, `RAILS_OK`, TPS3431, and hardware-safe-state wiring. Add the exact local SN74LV1T08 AND-gate network in section 4; do not connect `OUT1` and `PGOOD_12V` together.
4. Recalculate the populated load without exceeding 200 mA; verify output ripple/transients remain inside 3.13-3.47 V and that the DC value remains inside 3.256299-3.337821 V at input/load/temperature corners.
5. Perform the already-required ramp, thermal, and transient checks. No result in this document claims that those Phase 4B implementation tests were executed.

## 10. Evidence, unknowns, and gate

Primary evidence is the official [TI TPS62135/TPS621351 datasheet, SLVSBH3B Rev.B](https://www.ti.com/lit/ds/symlink/tps62135.pdf), also retained locally as [`datasheets/power/tps62135_datasheet_rev_b.pdf`](../../datasheets/power/tps62135_datasheet_rev_b.pdf). Relevant material was checked in sections 7.3-7.5 (pp.4-6), 9.3-9.4 (pp.9-12), 10.1 (pp.13-16), Figure 13 (p.18), 3.3 V transient plots (pp.25-26), and the 12 V/3.3 V stability plot (Figure 82, p.30). TI's current [TPS62135 product page](https://www.ti.com/product/TPS62135) lists the device as active. The branch-local enable gate is supported by the official [TI SN74LV1T08 datasheet, SCLS739F Rev.F](https://www.ti.com/lit/ds/symlink/sn74lv1t08.pdf), sections 5-6, 8, and 9.1 (pp.4-7, 10-14); TI lists exact orderable `SN74LV1T08DBVR` as active.

Remaining `UNKNOWN` items are limited to populated-BOM load confirmation, guaranteed ripple/transient containment, exact capacitor DC-bias curves, exact inductor loss/saturation curve, and measured thermal performance. These are implementation validations already assigned to Phase 4B; they do not leave the regulator choice, input source, divider, guaranteed static DC range, or supervisor threshold undecided.

No KiCad file was modified. Phase 4B remains stopped and was not resumed by this correction.

PHASE 3C: PASS
