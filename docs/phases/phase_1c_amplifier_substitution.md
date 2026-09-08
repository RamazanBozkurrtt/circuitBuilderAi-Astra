# Phase 1C - Amplifier Substitution Validation

Repository: `circuitBuilderAi-Astra`  
Review date: 2026-09-08  
Scope: TAS6424-Q1 -> TAS6424E-Q1 substitution only; documentary verification and calculations.

## 1. Executive summary

**Decision: TAS6424E-Q1 is PROVISIONALLY APPROVED.** It supports four BTL channels, 4-ohm loads, 96-kHz/24-bit TDM4, and the intended nominal 12-V power domain. Its current datasheet explicitly permits SCLK and MCLK to be connected together and provides a control for the inverted same-frequency case. The TAS6424-Q1 MCLK/SCLK phase contradiction therefore does not carry into this replacement.

The selected transport is 96 kHz, four 32-bit slots carrying 24 valid bits, 12.288-MHz SCLK, and a separate 24.576-MHz MCLK. The amplifier and ADSP-21569 have compatible functions and useful timing budget at that rate. Direct wiring remains conditional on a bounded logic rail, loaded signal-integrity verification, and a qualified clock implementation. Those are Phase 2 architecture constraints rather than missing TAS6424E-Q1 evidence.

| Item | Result |
| --- | --- |
| Functional audio/load fit | **CONFIRMED** |
| TAS6424-Q1 phase blocker removed by substitution | **CONFIRMED** |
| ADSP-21569 -> TAS6424E-Q1 DC interface | **PROVISIONAL** |
| ADSP-21569 -> TAS6424E-Q1 serial timing | **PROVISIONAL** |
| Nominal 12-V supply compatibility | **CONFIRMED**, with output-power/current/thermal requirements still undefined |
| Amplifier-level blocker to Phase 2 | **None identified** |

New evidence keys are **AMPE** = TAS6424E-Q1 datasheet SLOSE73A, revised November 2021, and **AMPEEVAL** = TAS6424E-Q1 EVM guide SLOU553, May 2021. Existing **DSP** and **HRM** keys retain the meanings in the [evidence index](../evidence/component_evidence_index.md). The official TI product index was checked for the current document and errata. No forum statement was used as electrical evidence.

## 2. Amplifier capability and load

| Requirement | Official evidence | Finding |
| --- | --- | --- |
| Four channels | AMPE p.1 and Device Options p.3 specify four digital-input Class-D channels and four-channel BTL operation. | **CONFIRMED** |
| 4-ohm speakers | Recommended conditions, AMPE p.6, give a 2-ohm minimum and 4-ohm typical BTL load. Guaranteed output-power rows at 14.4 V also use 4 ohms. | **CONFIRMED** |
| 96 kHz | AMPE pp.1, 23 and SAP register p.43 specify 44.1, 48 and 96 kHz; SAP `[7:6]=10` selects 96 kHz. | **CONFIRMED** |
| 24-bit audio | AMPE pp.1 and 23 specify 16-, 24- and 32-bit TDM input data. | **CONFIRMED** |
| Four-channel TDM | AMPE p.23 explicitly supports four- or eight-channel TDM and assigns amplifier channels 1-4 to TDM slots 1-4 when the first-four selection is used. TDM data uses SDIN1; TI recommends grounding unused SDIN2. | **CONFIRMED** |

No PBTL mode is used. The intended mode is four independent BTL outputs.

## 3. 96-kHz TDM and clock resolution

### Selected configuration

Use 24 significant audio bits in four 32-bit slots. A packed four-by-24-bit frame would require 96fs, which is absent from the device's documented TDM SCLK ratios; it is not selected.

| Parameter | Calculation / setting |
| --- | --- |
| Frame rate | `fs = 96,000 Hz` |
| TDM slots | 4 |
| Slot width | 32 bits, carrying 24 valid bits |
| SCLK/BCLK | `96,000 x 4 x 32 = 12,288,000 Hz = 128fs` |
| SCLK period | `1 / 12.288 MHz = 81.3802 ns` |
| Nominal half-period | `40.6901 ns` |
| Frame period | `1 / 96 kHz = 10.4167 us` |
| MCLK | `256fs = 24.576 MHz` |
| Frame sync | Active high, one SCLK period = 81.3802 ns = two selected MCLK periods; one-bit delay to the first MSB |

AMPE p.23 permits TDM SCLK at 128fs or 256fs, MCLK at 128fs, 256fs or 512fs, and a 25-MHz maximum clock. At 96 kHz, 12.288-MHz SCLK and 24.576-MHz MCLK are therefore valid; 512fs would be 49.152 MHz and is invalid. The mode-specific text calls for 50% duty at 128fs, while the electrical table on p.11 gives the allowable MCLK/SCLK duty range as 45%-55%. The clock source must be configured for nominal 50% duty, and the guaranteed physical waveform must stay inside 45%-55%.

Candidate SAP fields are sample rate `[7:6]=10`, first-four-slot selection bit 5 = 0, 24-/32-bit slot selection bit 4 = 0, normal slot order bit 3 = 0, and DSP/TDM input format `[2:0]=110` (AMPE p.43). These fields document the intended mode; they are not a firmware write sequence.

**MCLK remains a required input during playback.** AMPE identifies MCLK as an input, specifies valid MCLK ratios, and faults on invalid clock ratios. It documents no MCLK-pin-free playback mode. A separate oscillator is not inherently required because the clock may come from the DSP or a shared clock source.

### Equal-clock alternative and prior blocker

AMPE section 9.3.1.4, p.23, explicitly permits SCLK and MCLK to be connected together. If tied or merely equal in frequency, FSYNC must be at least two MCLK periods high. Thus an alternative is:

`MCLK = SCLK = 12.288 MHz`, with `FSYNC high >= 2 x 81.3802 ns = 162.7604 ns`.

Register 0x26 bit 3, `BCLK_INV`, defaults to 0 for all ordinary frequency/phase cases and selects the inverted relationship when MCLK and BCLK run at the same frequency (AMPE p.58). This language is absent from the old TAS6424-Q1 evidence. The TAS6424-Q1 datasheet's permission/prohibition conflict remains historical, but **it does not apply to TAS6424E-Q1**. The replacement removes that component-level blocker; no interpretation of the old contradiction is needed to preserve the new candidate.

The separate 24.576-MHz MCLK configuration is selected because it is directly documented, keeps all clocks below 25 MHz, and permits the ADSP SPORT's normal one-SCLK frame pulse. That 81.3802-ns pulse is also exactly two periods of the selected 24.576-MHz MCLK.

### Can ADSP-21569 provide the clocks?

**Functionally, yes.** HRM chapter 23 permits an ADSP-21569 SPORT to generate TDM SCLK and FSYNC; chapter 24 permits a PCG to generate an additional synchronous clock through the DAI. A PCG with an even divider produces nominal 50% duty. The selected contract can therefore use SPORT-generated 12.288-MHz SCLK/96-kHz FSYNC plus PCG-generated 24.576-MHz MCLK, provided both derive from a qualified synchronous reference.

Direct unbuffered implementation is **PROVISIONAL**. Phase 2 must choose the DSP/system clock and integer divisors, establish jitter suitability, verify the precise SRU/DAI route, and close output loading and edge rate. An external clock fanout remains an acceptable architecture option; none is selected here.

## 4. ADSP-21569 -> TAS6424E-Q1 logic compatibility

The amplifier's audio inputs use its 3.0-3.5-V VDD rail. AMPE p.9 specifies `VIH(min)=0.7 VDD` and `VIL(max)=0.3 VDD`; p.6 specifies an absolute input range of `-0.3 V` to `VDD+0.5 V`. The p.6 unit column prints `A` for this VLOGIC row, an editorial error: the parameter is explicitly input voltage and its maximum tracks VDD. DSP guarantees `VOH(min)=2.4 V` and `VOL(max)=0.4 V` on the relevant VDD_EXT DAI outputs (DSP pp.44, 47 and 49).

| Supply envelope | HIGH margin = `VOH(min)-VIH(min)` | LOW margin = `VIL(max)-VOL(max)` | Result |
| --- | --- | --- | --- |
| Full AMPE VDD range | `2.4-(0.7 x 3.5) = -0.050 V` | `(0.3 x 3.0)-0.4 = +0.500 V` | Direct connection **INCOMPATIBLE** over unrestricted rail ranges |
| Illustrative common 3.168-3.232-V envelope | `2.4-(0.7 x 3.232) = +0.1376 V` | `(0.3 x 3.168)-0.4 = +0.5504 V` | Positive conditional margins |
| Nominal 3.3 V, +/-1% | `2.4-(0.7 x 3.333) = +0.0669 V` | `(0.3 x 3.267)-0.4 = +0.5801 V` | Positive but small HIGH margin |

Zero HIGH margin requires `VDD <= 2.4/0.7 = 3.4286 V`; a real design needs additional noise reserve. **Interface classification: PROVISIONAL.** Level shifting is not inherently required if the amplifier VDD is deliberately bounded and the required margin is met. Otherwise a qualified buffer/translator is required. The clock/data source must also remain off or isolated while amplifier VDD is absent so that `VDD+0.5 V` is not exceeded during sequencing.

## 5. ADSP-21569 -> TAS6424E-Q1 timing compatibility

Use SPORT0 transmit with `CKRE=1`: ADSP output data and internally generated frame sync change on falling SCLK; TAS6424E-Q1 samples on rising SCLK. Use multichannel mode, four 32-bit slots, four active channels, and a one-bit frame delay. This is a mode contract, not a register-write sequence.

AMPE p.11 gives SCLK period >=40 ns, high and low widths >=16 ns, rise/fall <5 ns, FSYNC separation >=8 ns, and SDIN setup/hold >=15 ns in the stricter SDIN rows. DSP Table 37 p.58 gives internally clocked SPORT data/FS delay <=3.5 ns from the falling drive edge and minimum hold of -3 ns relative to that edge. At the 45%-55% AMPE duty limits, the shortest half-cycle is `0.45 x 81.3802 = 36.6211 ns`.

| Check before PCB skew/load/jitter deductions | Calculation | Conditional margin |
| --- | --- | --- |
| SDIN setup | `36.6211-3.5-15` | **18.1211 ns** |
| SDIN hold | `36.6211-3-15` | **18.6211 ns** |
| FSYNC setup | `36.6211-3.5-8` | **25.1211 ns** |
| FSYNC hold | `36.6211-3-8` | **25.6211 ns** |

Frequency, pulse width, edge convention and nominal device timing are compatible. However, AMPE lists 10-pF input capacitance per audio pin while DSP timing uses a 6-pF reference load. DSP requires delay/hold derating and IBIS analysis for the actual load; the AMPE <5-ns input rise/fall requirement must also be met. **Timing classification: PROVISIONAL.** The positive pre-layout budgets permit Phase 2 clock/buffer architecture work, but do not approve direct PCB wiring or schematic freeze.

## 6. Power compatibility with the intended 12-V system

AMPE p.6 permits PVDD from 4.5 to 26.4 V and VBAT from 4.5 to 18 V; nominal 12 V is inside both ranges. PVDD and VBAT may share a source only if the complete source range and transients remain inside both limits. VDD is a separate 3.0-3.5-V logic supply.

Four-ohm BTL operation is supported, but TI's guaranteed output-power rows are specified at 14.4 V and 25 V, not 12 V. The ideal unclipped voltage-source ceiling at 12 V is `12^2/(2 x 4) = 18 W/channel` before device losses and modulation/headroom limits. The project still has no confirmed per-channel acoustic/output-power target, input tolerance, peak current, thermal envelope, or load transient. These product requirements must be set before the power stage can be frozen; they do not show a TAS6424E-Q1 incompatibility today.

## 7. Package, pinout and integration differences

TAS6424E-Q1 orderable `TAS6424EQDKQRQ1` uses the same 56-pin DKQ HSSOP outline, exposed top thermal pad, and numbered pin functions as TAS6424-Q1. TI also identifies it as an upgraded drop-in replacement on the product page. Future schematic work must still use the E-device datasheet and exact orderable rather than reusing an old symbol without verification.

Relevant differences and cautions are:

- AMPE requires 2.2-uF capacitors from each GVDD pin 9 and 10 to ground; the old TAS6424-Q1 table grouped those pins under a 1-uF bypass requirement.
- Register 0x28 bit 5, `PHASE_SEL`, resets to the unsupported value 0 and **must be written to 1 before exiting STANDBY** (AMPE p.59). This is a mandatory firmware initialization requirement.
- The output phase selection spans register 0x05 bits 1:0 and register 0x28 bit 5; only the documented combinations may be used (AMPE p.42).
- Invalid/missing audio clocks force the outputs to high impedance until valid clocks return (AMPE p.24).
- The exposed top thermal pad requires an external grounded heatsink; output filter, thermal and EMI design remain future work.
- AMPEEVAL is an exact-device implementation reference and uses a 12.288-MHz oscillator, but its 14.4-V setup and board circuitry are not adopted as this project's design.

The TI product document index was checked on 2026-09-08. No standalone TAS6424E-Q1 silicon errata was listed or found in a targeted TI-domain search. This does not prove that no errata exist. The datasheet revision history records the change from advance information to production data; all cautions above remain controlling.

## 8. Resolved and remaining items

**Resolved amplifier blockers**

- TAS6424E-Q1 supports the required channel count, load, rate, sample width and TDM4 transport.
- A valid 96-kHz TDM4 clock set is explicit.
- MCLK is required, and valid separate-clock and tied-clock cases are documented.
- The replacement contains no TAS6424-Q1-style instruction prohibiting the expressly permitted tied clocks.
- Nominal 12-V operation is within the device supply ranges.
- No package remapping is required for the substitution.

**Requirements still needed from product/system work**

- Required continuous/peak output power, acoustic SPL, allowed THD and exact 4-ohm speaker impedance envelope.
- Complete 12-V minimum/maximum/transient/current specification and amplifier thermal/EMI limits.
- Required logic noise margin and a bounded amplifier VDD rail, or selection of a level/clock buffer.
- Final synchronous clock source, jitter limit, duty/edge/load/skew budget, and IBIS validation.
- Firmware startup sequencing that sets `PHASE_SEL=1` before leaving STANDBY and handles clock faults.

These are architecture and system-definition tasks. No unresolved TAS6424E-Q1 evidence issue prevents Phase 2 architecture work.

## 9. Updated component status

**TAS6424E-Q1: PROVISIONALLY APPROVED**

The candidate architecture is updated to:

`4 x analog microphones -> low-noise AFE -> ADAU1978 -> TDM4 -> ADSP-21569 -> TDM4 -> TAS6424E-Q1 -> 4 x 4-ohm speakers`

TAS6424-Q1 is superseded as the amplifier candidate because its unresolved clock-phase documentation conflict is avoided by the verified replacement. This decision does not approve a schematic, clock buffer, power stage or PCB implementation.

PHASE 1C: PASS
