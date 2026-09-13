# Phase 3 - Schematic Readiness and Detailed Electrical Architecture

Date: 2026-09-09 (Europe/Istanbul)

Scope: documentary verification, calculations, component-level electrical architecture, and a contract for a later schematic phase. No KiCad, schematic, PCB placement, routing, firmware, or Phase 4 work was created.

Evidence notation such as `DSP p.53` refers to the source IDs and local manufacturer documents in the [component evidence index](../evidence/component_evidence_index.md). `CONFIRMED` means device evidence or an already approved project decision; `PROVISIONAL` is a bounded Phase 3 engineering decision; `UNKNOWN` and `CONFLICTING` retain their Phase 0 meanings.

**Phase 3B amendment (2026-09-13):** the former TPS386000 rail-supervision and watchdog contract was invalid because its guaranteed rising hysteresis was omitted. [Phase 3B](phase_3b_power_supervisor_correction.md) replaces only that contract; the rail voltages, regulators, Phase 3A `PGOOD_12V`, and all unrelated Phase 3 decisions remain unchanged.

**Phase 3C amendment (2026-09-13):** the former `3V8_PRE -> TPS62135 -> 3V3_SYS` contract did not satisfy the input-headroom condition attached to the converter's accuracy guarantee. [Phase 3C](phase_3c_3v3_regulator_correction.md) retains TPS62135 but powers only the `3V3_SYS` instance from `12V_PROTECTED`, uses a lower-impedance 0.1% divider, and supersedes the 3.3 V realized range and associated margin calculations below. All unrelated Phase 3/3A/3B decisions remain unchanged.

**Phase 3D amendment (2026-09-13):** the remaining buck dividers omitted external-divider and FB-leakage corners, and the LDO ranges omitted divider/FB-current and guaranteed-minimum-load conditions. The [final Sheet 2 audit](phase_3d_final_power_contract_audit.md) supersedes the pre/core dividers and realized ranges, approves a 3.700-3.900 V intermediate pre operating band, supersedes the 1.8 V/DMC dividers and ranges and the 5 V realized range, and adds deterministic LDO preloads. Phase 3A, Phase 3C `3V3_SYS`, and the Phase 3B supervisor thresholds remain unchanged.

**Phase 3E amendment (2026-09-13):** the direct shared `OUT1` fanout could not turn microphone/AFE power off before DSP core/DMC and could not retain the commanded sequence after DSP reset. The [shutdown/safe-state correction](phase_3e_shutdown_safe_state_correction.md) supersedes the affected enable, shutdown, safe-state, and powered-off analog-interface text below. It adds a pre-powered retained downstream-run latch, a guaranteed post-reset delay, an independently qualified microphone/AFE enable, a non-auto-rearming hardware-safe latch, and TMUX2821 powered-off analog isolation. Phase 3D rail sources, dividers, preloads, thresholds, allocations, and voltage/margin calculations remain unchanged.

**Phase 3F amendment (2026-09-13):** the Phase 3E combined post-arm audio/MCLK OE requirement prevented the ADAU1978 PLL from locking before the arm edge. The [clock startup correction](phase_3f_clock_startup_correction.md) supersedes the affected clock-OE, ADC-reset, arming, startup, shutdown, and clock-fault text below. It adds a pre-arm `CLOCK_STARTUP_EN`, separates clock and data buffer banks, and preserves all rail and Phase 3E functional safe-state decisions.

**Phase 3G amendment (2026-09-14):** Phase 4C proved that the four differential microphones require eight, not four, independently isolated legs and that the former OPA165x 0.8 V headroom claim was not guaranteed at the actual 5 V operating point. The [remaining-sheet preflight](phase_3g_remaining_schematic_implementation_preflight.md) supersedes the microphone-isolation device/count, VREF-buffer, signal-amplifier, gain/headroom/noise, Sheet 3 ownership, and Sheets 3-7 implementation-inventory text below. Unrelated Phase 3 through Phase 3F decisions remain unchanged.

## 1. Executive summary

The four Phase 2 hard schematic-entry blockers have been resolved or bounded without weakening them. The resulting prototype design point is:

- four nominal 4-ohm BTL speakers, 6 W continuous per channel with all four channels active, and 7.03 W sine-equivalent full-scale/short-peak power per channel;
- a regulated 12 V nominal input, 10.8 V to 13.2 V normal operating range, 4 A continuous and 5 A short-peak source capability;
- input cutoff, reverse-polarity, overcurrent, inrush, brownout, and hardware-safe mute behavior based on TPS26630;
- a deterministic `3V8_PRE` intermediate rail and sequenced 1.0 V, 1.35 V, 1.8 V, 2.8 V, 3.3 V, and 5.0 V rails;
- ADSP-21569 `VDD_REF/VDD_ANA` before `VDD_EXT`, all five DSP domains monitored, all DSP rails and the 24.576 MHz clock valid before reset release, and explicit power-down behavior;
- one 24.576 MHz, 1.8 V oscillator, a 1:3 low-skew clock fanout, and two 1.8-to-3.3 V MCLK translators;
- separate buffered 3.3 V serial-audio paths instead of the Phase 2 conditional direct-drive assumption;
- a two-op-amp-per-microphone AC-coupled differential AFE using OPA4192, gain 1.453571 V/V, a worst-case coupling corner below 0.73 Hz, and ADC HPFs plus amplifier HPF disabled;
- SPI2 boot from a selected 64 MB serial flash, fixed boot straps, JTAG, logic-level UART, and a hardware-dominant safe-state path.

The architecture deliberately does not claim automotive transient compliance, final acoustic performance, final thermal compliance, EMC compliance, or a completed ANC compute budget. Those remain product/validation work. They do not require a different basic schematic architecture under the bounded prototype assumptions below.

## 2. Phase 2 blocker resolution

### 2.1 Exact blockers extracted before new work

The following are faithful summaries of the four items in Phase 2 section 13; none has been downgraded:

| # | Phase 2 hard blocker | Why it blocked schematic entry | Needed evidence or decision | Origin | Phase 3 disposition |
| --- | --- | --- | --- | --- | --- |
| 1 | **AFE contract closure:** approve the ANC passband/phase mask, microphone SPL/crest envelope, ADC utilization/clipping margin, noise target, gain range, coupling/DC policy, powered-off behavior, and exact AFE part/rails. | Gain, topology, coupling capacitors, op amp, rail, and protection could not be selected safely without a bounded signal and low-frequency envelope. | Product-level signal/passband bounds plus device-backed AFE calculations and component selection. | Mixed product- and device-derived. | **ACCEPTED PROVISIONALLY.** A safe prototype passband/SPL/noise contract and a deterministic circuit architecture are frozen in section 9. |
| 2 | **Clock implementation closure:** select the exact 24.576 MHz oscillator/fanout, mixed-voltage outputs, jitter/accuracy/startup/loading/skew/duty/edge budget, SPORT/SRU route, and loaded-PVT timing; close the ADC minimum data-hold evidence gap by clarification or a formally approved verification method. | Clock pins, rails, output enables, SPORT pins, timing polarity, and series elements were otherwise undefined; an unsafe sampling edge could corrupt all channels. | Exact clock parts and domains, arithmetic, pin route, timing budget, and a controlled validation method for the missing ADC minimum hold number. | Device/implementation-derived. | **RESOLVED for schematic entry.** Exact parts, routes, margins, loading limits, and the mandatory PVT/bench method are in sections 7 and 15. |
| 3 | **Power and sequencing closure:** define the nominal-12-V envelope, worst-case rail loads/margins, no-DDR `VDD_DMC`, supervisor thresholds, discharge behavior, and a power-up/down/back-drive matrix satisfying DSP delta limits. | Regulators, enable topology, protection ratings, bulk capacitance, reset, and even whether every DSP supply pin was powered were not deterministic. | Product input/output decisions and manufacturer-backed regulator/supervisor architecture with explicit state sequencing. | Mixed product- and device-derived. | **ACCEPTED PROVISIONALLY.** The product envelope is bounded and the hardware architecture is deterministic; rail-ramp measurements remain a mandatory validation, not an architectural choice. See sections 4-6 and 10. |
| 4 | **Conditional direct-I/O closure:** prove every Phase 2 bounded-rail condition or select qualified buffers/translators with safe output-enable behavior. | The direct DSP high-level margin was too small to approve over PVT and unpowered-device states could back-drive endpoints. | Worst-case DC margins or concrete translators/buffers and safe OE control. | Device-derived. | **RESOLVED.** Strategy B is selected: SN74LVC244A buffering for audio, SN74AXC2T245 for MCLK translation, and a common 3.3 V control domain. See section 8. |

### 2.2 Gate interpretation

`ACCEPTED PROVISIONALLY` is used only for product choices whose bounds are safe for the prototype and whose later adjustment changes passive values, gain settings, connector series, or thermal hardware rather than the basic signal/power architecture. Device absolute limits, DSP supply sequencing, amplifier BTL handling, and powered-off I/O isolation are not provisionally waived.

## 3. Speaker/output design point

### 3.1 Frozen prototype requirement

| Item | Phase 3 value | Classification |
| --- | --- | --- |
| Channel count | Four independent BTL channels; all four may operate simultaneously | **CONFIRMED** architecture |
| Speaker nominal impedance | 4 ohms | **PROVISIONAL** product decision |
| Speaker minimum impedance | Target at least 3.2 ohms throughout the driven band; the amplifier's 2-ohm device capability is not the product load target | **PROVISIONAL** |
| Continuous output target | 6 W/channel, four channels simultaneous, sine-equivalent electrical test | **PROVISIONAL** |
| Short peak target | 7.03 W/channel, four channels, less than 1 s; limited by selected gain rather than the datasheet headline maximum | **PROVISIONAL** |
| Amplifier supply in normal operation | 10.4-13.2 V at `12V_PROTECTED`; the input path is allocated at most 0.4 V drop at 4 A from the 10.8 V connector minimum | **PROVISIONAL** |
| Amplifier gain | TAS6424E-Q1 gain level 1, register 0x01 `GAIN=00`, 7.5 V peak at 0 dBFS | **PROVISIONAL**, device-defined setting |
| Clipping policy | Firmware limiter must keep normal program/ANC output at or below 6 W/channel; clipping is not a normal operating mode | **PROVISIONAL** |
| Low-frequency policy | Digital HPF bypassed (`0x01[7]=1`); 2.2 uF bootstrap capacitors fitted; final acoustic excursion limit remains speaker-specific | **PROVISIONAL** |

The exact production speaker remains `UNKNOWN`. A Phase 4 schematic may use this load contract without knowing its mechanical model. Before a speaker is connected, its datasheet must confirm nominal 4 ohms, the minimum-impedance target, at least 10 W thermal rating, excursion suitability for the intended low-frequency content, and BTL isolation from chassis/ground.

### 3.2 Power, voltage, and current calculations

The chosen amplifier setting limits a full-scale sine to 7.5 V peak. For a 4-ohm resistive load:

`PFS = Vpk^2 / (2R) = 7.5^2 / (2 x 4) = 7.03125 W/channel`.

At the 6 W continuous target:

- `Vrms = sqrt(PR) = 4.899 V`, `Vpk = 6.928 V`;
- `Irms = sqrt(P/R) = 1.225 A`, `Ipk = 1.732 A` per channel;
- four-channel acoustic-output-stage electrical power is 24 W.

At the selected full-scale short peak:

- `Vrms = 5.303 V`, `I rms = 1.326 A`, `Ipk = 1.875 A` per channel;
- simultaneous four-channel output is 28.125 W.

The ideal single-supply BTL ceiling at 12 V and 4 ohms is `12^2/(2x4)=18 W/channel`, but output-stage losses and distortion make that an upper geometric ceiling, not a target. At the 10.4 V minimum protected amplifier rail, 7.5 V peak retains 2.9 V of ideal rail headroom. TI only guarantees the published 4-ohm power points at 14.4 V and 25 V; those headline values are not transposed to this 12 V product [AMPE pp.8-10, 63-69].

### 3.3 Supply-current envelope

For a conservative architecture screen, use 80% amplifier efficiency rather than a typical plot:

- continuous: `4x6 W / 0.80 = 30 W` amplifier input;
- add a 5 W conservative auxiliary-electronics allowance: 35 W total;
- at 10.8 V: `35/10.8 = 3.24 A`.

At the four-channel 7.031 W short peak, `(28.125/0.80 + 5)/10.8 = 3.72 A`. The product input therefore requires 4 A continuous and 5 A for less than 1 s. The 5 A figure includes converter transients and is not a promise of higher speaker output. The amplifier's maximum idle PVDD/VBAT currents are also included in rail budgeting [AMPE pp.7-10].

### 3.4 Amplifier electrical contract

- Exact device: `TAS6424EQDKQRQ1`, HSSOP-56 with exposed top thermal pad [AMPE pp.3-6; AMPEEVAL BOM].
- `PVDD` and `VBAT`: direct from protected input; `VDD`: `3V3_SYS`.
- Four BTL channels; neither output terminal may connect to ground.
- Serial audio: register 0x03 = `0x86` for 96 kHz, first four TDM slots, 24/32-bit slots, DSP/TDM format. `SDIN2` is grounded as TI recommends.
- Gain and protection: register 0x01 = `0xE0` selects HPF bypass, 110 C overtemperature warning, level-1 overcurrent, one-FSYNC volume steps, and gain level 1. This value must be read back before PLAY.
- Output phase: retain register 0x02 low bits `10`; write register 0x28 = `0x2A` so mandatory `PHASE_SEL=1` before leaving STANDBY. Spread spectrum remains disabled [AMPE pp.42, 59].
- Register 0x26 remains `0x40`; `BCLK_INV=0`. Its HPF corner field is inactive because HPF bypass is selected [AMPE pp.25, 40, 58].
- Per BTL leg, use the TI baseline 3.3 uH series inductor and 1 uF shunt capacitor, plus 1 nF local EMI capacitor where shown. Each inductor must retain at least 1 uH at the level-1 7 A shutdown current and have DCR no greater than 50 milliohms; exact magnetics require Phase 4 manufacturer verification [AMPE pp.63-69; INDUCTOR].
- Fit 2.2 uF X7R, at least 16 V, for each bootstrap capacitor because the prototype preserves content below 30 Hz. Fit 2.2 uF on each GVDD pin and all other mandatory bypass networks from the TI application schematic [AMPE pp.5-6, 27, 63-64].
- Provide 470 uF low-ESR bulk at the amplifier power region in addition to local 10 uF and 100 nF PVDD capacitors. The bulk capacitor must be rated at least 25 V and for the measured ripple current.

## 4. System input-power envelope

### 4.1 Product-level envelope

| Requirement | Phase 3 value | Behavior/classification |
| --- | --- | --- |
| Nominal input | 12.0 V regulated DC | **PROVISIONAL** |
| Normal operating input | 10.8 V to 13.2 V at the connector under load | **PROVISIONAL**; represents +/-10% supply |
| Cold start/restart | At least 11.5 V | **PROVISIONAL**; exceeds the Phase 3A worst-case 10.333 V `PGOOD_12V` rising point and 10.173 V eFuse UVLO rising point |
| Ripple in normal operation | No more than 200 mV peak-to-peak below 100 kHz at the connector | **PROVISIONAL** source requirement |
| Positive abnormal input | +24 V DC may be applied indefinitely without damage; downstream power is cut off and audio stops | **PROVISIONAL**, not an operating point |
| Negative abnormal input | -14 V DC may be applied indefinitely without damage or output energization | **PROVISIONAL** |
| Fast transients | Connector ESD/EFT and cable-induced spikes require bench characterization; the board is not assigned an automotive load-dump class | **UNKNOWN** compliance; protected topology retained |
| Reverse polarity | No damage, no powered output | **PROVISIONAL** product requirement |
| Overvoltage | Hardware cutoff nominal 14.199 V rising/13.276 V falling; bounded rising cutoff 13.793-14.606 V; system safe-state remains latched after the event | **PROVISIONAL** setting, amended by [Phase 3A](phase_3a_pgood_contract_correction.md) |
| Undervoltage | Phase 3A `PGOOD_12V` hardware-mutes at 10.000 V nominal falling, bounded 9.870-10.130 V, and reasserts at 10.200 V nominal, bounded 10.067-10.333 V; eFuse UVLO is the secondary cutoff at 9.877 V nominal rising/9.235 V nominal falling; restart of system rails waits for valid `PGOOD_12V` | **PROVISIONAL**, amended by [Phase 3A](phase_3a_pgood_contract_correction.md) |
| Source current | 4 A continuous, 5 A for less than 1 s | **PROVISIONAL** |
| Input connector | Two power contacts, keyed/polarized, at least 6 A continuous per contact pair and at least 30 V DC | **PROVISIONAL** mechanical requirement |

The TAS6424E-Q1's automotive qualification does not classify this board as automotive. No ISO 7637, ISO 16750, load-dump, cranking, jump-start, or automotive EMC compliance is claimed.

### 4.2 Protection implementation

Use `TPS26630RGER` with the manufacturer reverse-polarity topology: `CSD19537Q3` blocking NFET and `BSS138` fast gate-pulldown transistor. Leave `MODE` open for latch-off after sustained overload/thermal fault. Hardware reset of the latch is by a deliberate `SHDN` cycle or input power cycle [PWRIN pp.3-9, 20-28, 30-34].

Fit at least 1 uF ceramic at the input entry and reserve a DNP bidirectional TVS footprint after the fuse and before `IN_SYS`. TVS working/standoff voltage is intentionally not populated until the cable/EFT/surge class is defined; the TPS26630 and reverse FET themselves satisfy the bounded steady +24 V/-14 V prototype requirement. This preserves a deterministic protection location without inventing automotive transient compliance [PWRIN pp.5, 38-39].

Use one three-resistor UVLO/OVP ladder, 0.1%, as amended by Phase 3A:

- `R1=316 kohm`, `R2=13.3 kohm`, `R3=30.4 kohm` in the TI order from `IN_SYS` through UVLO/OVP to ground;
- `VOVP = 1.2(R1+R2+R3)/R3 = 14.199 V` nominal;
- `VUVLO = 1.2(R1+R2+R3)/(R2+R3) = 9.877 V` nominal;
- divider current at 12 V is 33.36 uA, and `R1` exceeds TI's 300-kohm minimum for reverse-polarity applications [PWRIN pp.19-20, 30-31].

Use `RILIM=3.24 kohm`, giving `18/3.24=5.56 A` nominal and approximately 5.17-5.95 A across the specified +/-7% limit. Use `CdVdT=47 nF`; the datasheet relation gives approximately 9.0 ms for a 10%-90% rise at 12 V and about 0.5 A into 470 uF. Per Phase 3A, tie TPS26630 `PGTH` to ground so native PGOOD remains low and all fault recoveries use the controlled dVdT ramp. Add `TPS3760A012DYYR`, powered from `12V_PROTECTED`, with a `115 kohm / 10.0 kohm` 0.1% sense divider and `2%` internal hysteresis. Its active-low open-drain RESET, pulled up to `3V8_PRE` through `10.0 kohm`, is the active-high `PGOOD_12V` signal. It falls at 10.000 V nominal (9.870-10.130 V bounded), rises at 10.200 V nominal (10.067-10.333 V bounded), and has 0.197-0.203 V guaranteed rail-referred hysteresis. `PGOOD_12V` and FLT feed the hardware safe-state logic as well as DSP-visible status [Phase 3A](phase_3a_pgood_contract_correction.md).

Including comparator threshold limits, 0.1% resistor limits, and independent +/-150 nA UVLO/OVP pin leakage, the Phase 3A ladder bounds are: UVLO rising 9.583-10.173 V and falling 8.876-9.563 V; OVP rising 13.793-14.606 V and falling 12.777-13.729 V. `PGOOD_12V` always removes downstream authorization before UVLO opens, remains asserted throughout the 10.4-13.2 V protected-rail normal range, and OVP cannot trip within the 13.2 V connector normal maximum. OVP recovery may re-enable the eFuse when input returns below its falling threshold, but grounded PGTH forces a controlled dVdT recovery and the separate hardware safe-state latch still requires an explicit restart sequence before audio PLAY.

The eFuse, external NFET, connector, copper, and any fuse must be rated for at least 6 A continuous. At 4 A and the eFuse's 53 milliohm worst-case on-resistance, the first-order internal-FET loss is 0.85 W; its exposed pad and input copper are thermal features, not merely routing conveniences.

## 5. Detailed power tree

```text
12V_IN
  -> TPS26630 protection -> 12V_PROTECTED -> TAS6424E PVDD/VBAT
                                      |----> TPS7A4901 -> 5V_AFE
                                      |----> TPS62135  -> 3V3_SYS
                                      `----> TPS62135  -> 3V8_PRE
                                                        |-> TPS7A4901 -> 1V8_DSP_REF_ANA
                                                        |-> TPS62135  -> 1V0_DSP_CORE
                                                        |-> TPS7A4901  -> 1V35_DSP_DMC
                                                        |-> TPS7A2033P -> 3V3_ADC_A
                                                        `-> TPS7A2028P -> 2V8_MIC
```

### 5.1 Rail contract

Loads are design allocations, not measured consumption. They include margin and must be replaced by populated-BOM worst-case calculations in Phase 4 without exceeding the allocations.

| Rail | Required range / selected source | Maximum-load allocation and startup | Noise/filtering | Sequencing and architectural decoupling |
| --- | --- | --- | --- | --- |
| `12V_PROTECTED` | 10.4-13.2 V normal at the load; TPS26630 direct protected input; connector-to-load path drop no more than 0.4 V at 4 A | 4 A continuous, 5 A less than 1 s; 470 uF amplifier bulk dominates inrush | High-current/switching domain; do not feed microphone/ADC directly except through regulators | First rail. Local 1 uF at eFuse, 470 uF/25 V near amplifier, and TI per-PVDD local networks. Phase 3A `PGOOD_12V` defines system validity. |
| `3V8_PRE` | Approved operating band 3.700-3.900 V; TPS62135 forced PWM; `R1=44.2 kohm`, `R2=10.0 kohm`, 0.1%; 3.794 V nominal and guaranteed static **3.746849-3.841293 V** | 1.8 A design allocation; startup is regulator/capacitor charging | Switching pre-rail; keep away from AFE inputs and post-filter sensitive branches | Enabled directly whenever `12V_PROTECTED` is present; this avoids a PGOOD/pullup circular dependency. `CSS=10 nF` for approximately 2.8 ms programmed ramp; 1 uH class inductor, at least 5 A saturation, no more than 30 milliohms DCR; at least 22 uF effective output. [Phase 3D](phase_3d_final_power_contract_audit.md). |
| `1V0_DSP_CORE` | Required 0.95-1.05 V; TPS62135 forced PWM; `R1=4.32 kohm`, `R2=10.0 kohm`, 0.1%; 1.0024 V nominal and guaranteed static **0.991476-1.013338 V** | 3.0 A design maximum. Phase 1 high-corner subtotal was 2.0605 A but incomplete; regulator is 4 A | Moderate sensitivity/high di/dt; compact hot loop and uninterrupted local plane | Enabled only after 1.8 V valid through Phase 3E `DOWNSTREAM_EN`. `CSS=10 nF`; at least 100 uF effective domain bulk plus the per-ball network, with no more than 200 uF effective directly connected. Supervisor monitored. [Phase 3D; Phase 3E]. |
| `1V8_DSP_REF_ANA` | Required 1.71-1.89 V; TPS7A4901DGNR from corrected pre; `(54.2 kohm + 100 ohm)/100 kohm` feedback, all 0.1%; 1.828455 V nominal and guaranteed static **1.776066-1.875487 V** | 75 mA total allocation including 1.69 kohm 0.1% preload: VDD_REF model terms, clock fanout/oscillator, OTP allowance, VDD_ANA/HADC/TMU margin | Highest DSP clock/PLL sensitivity; one quiet regulator, VDD_ANA branch through ferrite with local bulk | First DSP rail. Enabled by Phase 3A `PGOOD_12V` after `3V8_PRE` is present; `CNR/SS=47 nF` gives about 65.8 ms nominal soft start; 10 uF input/output and 10 nF feed-forward. VDD_REF has at least 10 nF plus 100 nF and per-ball decoupling [DSP pp.18, 53; HVLDO pp.12-17; Phase 3D]. |
| `1V35_DSP_DMC` | Required 1.283-1.418 V; TPS7A4901DGNR from corrected pre; 14.9 kohm/100 kohm feedback, 0.1%; 1.361565 V nominal and guaranteed static **1.325693-1.395966 V** | 50 mA total allocation including 1.24 kohm 0.1% preload, with DMC disabled and no external DDR | Quiet/local domain | Enabled after 1.8 V valid through Phase 3E `DOWNSTREAM_EN`; `CNR/SS=47 nF` gives about 65.8 ms nominal soft start. Use 10 uF input/output plus at least 22 uF domain bulk and per-ball capacitors. The preload supplies the explicit passive discharge path. [Phase 3D; Phase 3E]. |
| `3V3_SYS` | 3.30 V; required DSP 3.13-3.47 V, ADC IOVDD 1.62-3.6 V, amplifier 3.0-3.5 V; TPS62135 forced PWM from `12V_PROTECTED`; guaranteed static 3.256299-3.337821 V; `Rtop=37.1 kohm`, `Rbottom=10.0 kohm`, 0.1%, gives 3.297 V nominal | 200 mA allocation: DSP I/O, amplifier maximum 18 mA, flash maximum 80 mA write-status/chip-erase case, buffers, pullups, debug; regulator rating 4 A | Digital/switching rail; ferrite-isolate only local consumers, never create a different DC logic voltage | Enabled after 1.8 V valid through Phase 3E `DOWNSTREAM_EN`, with a 1.0 Mohm EN pulldown. `CSS=10 nF`; 1.0 uH nominal/at least 0.8 uH effective inductor; local input capacitor at least 10 uF nominal, 3 uF effective, 25 V; local output bank at least 22 uF effective and no more than 200 uF directly connected. Powers DSP VDD_EXT, ADC IOVDD, amplifier VDD, flash, both LVC buffers, I2C/JTAG/UART. Active discharge and supervisor [Phase 3C; Phase 3E]. |
| `3V3_ADC_A` | 3.30 V; ADAU1978 AVDD required 3.0-3.6 V; `TPS7A2033PDBVR` from corrected pre; guaranteed static **3.2505-3.3495 V** | 30 mA total allocation including 3.01 kohm 0.1% preload; ADC AVDD is 14 mA typical; five TMUX2821 devices add at most 0.70 mA; the Phase 3G OPA320 VREF buffer adds at most 1.85 mA | Very sensitive; no other digital loads. Optional ferrite before LDO input, solid analog return | Enabled through Phase 3E `DOWNSTREAM_EN`. 10 uF plus 100 nF at regulator; each AVDD pin receives local 100 nF and shared local bulk per ADC guidance. [Phase 3D; Phase 3E; Phase 3G]. |
| `2V8_MIC` | 2.80 V; microphone normal mode requires 2.3-3.0 V; `TPS7A2028PDBVR` from corrected pre; guaranteed static **2.758-2.842 V** | 5 mA total allocation including 2.55 kohm 0.1% preload; four microphones require 0.92 mA maximum; two TMUX1574 devices add at most 0.136 mA | Very sensitive; star/ferrite branches to connectors | Enabled only by Phase 3E `ANALOG_PWR_EN`, together with AFE and independently of core/DMC. At least 10 uF controller bulk, 1 uF per connector branch, and 100 nF at each microphone as required [MIC; Phase 3D; Phase 3G]. |
| `5V_AFE` | OPAx192 required 4.5-36 V; TPS7A4901DGNR from protected input, 324 kohm/100 kohm 0.1% feedback; 5.0244 V nominal and guaranteed static **4.858943-5.157889 V** | 50 mA total allocation including 4.70 kohm 0.1% preload; ten OPAx192 channels add at most 15 mA; five TMUX2821 plus two TMUX1574 devices add at most 0.836 mA | Very sensitive; 10 nF NR/SS and feed-forward, 10 uF input/output; each op amp gets 100 nF plus local 1 uF | Enabled only by Phase 3E `ANALOG_PWR_EN`, together with microphones after ADC validation; disabled before ADC/DSP shutdown. Phase 3G paired-domain switches isolate every adjacent domain during unequal ramps/failures. About 14 ms soft start. Worst allocated LDO dissipation at 13.2 V is about 0.419 W. [Phase 3D; Phase 3G]. |

The `5V_AFE` 324-kohm/100-kohm pair is frozen. Phase 3D's complete resistor/feedback-current calculation gives 4.858943-5.157889 V, inside the OPAx192 4.5-36 V supply range. Phase 4 verifies trace drop and dynamic behavior but does not choose a new nominal rail.

### 5.2 No-DDR DMC disposition

External DDR is omitted. All ADSP-21569 `VDD_DMC` balls still connect to `1V35_DSP_DMC`; they are not grounded or left open. Both `DMC0_VREF` inputs connect to a filtered `0.5 x VDD_DMC` node (about 0.680 V at the 1.359 V nominal rail) made by equal 10.0 kohm, 0.1% resistors and 1 uF to ground. `DMC0_RZQ` retains the datasheet-required 34-ohm pulldown. All other DMC signal balls are no-connects and firmware must leave DMC disabled [DSP pp.21, 37-44, 53]. This conservative choice removes the supply-pin uncertainty without adding DDR or claiming a known zero-current DMC domain.

### 5.3 Decoupling rule

Each power pin receives a local high-frequency ceramic capacitor with the shortest possible return, and each domain receives bulk capacitance at its regulator/plane entry. The exact capacitor count follows the verified ball map. The EV-21569-SOM sheet 6 is a placement/count reference for 0.22/0.47/1 uF per-ball networks and 10 uF domain bulk, but is not copied blindly. Effective capacitance after DC-bias and tolerance, regulator stability, anti-resonance, and mounted impedance must be checked in Phase 4 [SOMSCH sheet 6; DSP p.18].

## 6. ADSP-21569 power and sequencing contract

### 6.1 Exact processor and rails

Use `ADSP-21569BBCZ10`, 1000 MHz, -40 C to +125 C junction, BC-400-3 400-ball CSP_BGA. The base design intentionally retains the 1 GHz option for compute headroom; this does not establish FxLMS feasibility [DSP pp.99-102].

| Domain | Allowed device range | Selected realized range | Corrected supervisor nominal threshold |
| --- | --- | --- | --- |
| VDD_INT | 0.95-1.05 V | 0.991476-1.013338 V static | 0.9655 V (`9.31k/10.0k`) |
| VDD_EXT | 3.13-3.47 V | 3.256299-3.337821 V | 3.180 V (`53.6k/10.0k`) |
| VDD_REF | 1.71-1.89 V | 1.776066-1.875487 V static | 1.745 V (`24.9k/10.0k`) |
| VDD_ANA | 1.71-1.89 V | same DC rail as VDD_REF after local filter | monitored with VDD_REF; no independent source |
| VDD_DMC | 1.283-1.418 V DDR3L range | 1.325693-1.395966 V static | 1.304 V (`(15.8k+280)/10.0k`) |

Use `LTC2964HUDC#PBF`, powered from `3V8_PRE`, for the four rail comparators and common reset. Configure all four channels in +ADJ mode by tying `PG1`-`PG4` directly to `REF`; use the 0.1% top/bottom dividers shown in the table and Kelvin-connect each divider bottom to supervisor ground. The bounded falling and rising thresholds are identical because this device deliberately filters glitches without adding hysteresis: 0.959608-0.971404 V (core), 3.157969-3.202097 V (3.3 V I/O), 1.733427-1.756604 V (1.8 V reference/analog), and 1.295641-1.312379 V (DMC). These ranges include the 497.5-502.5 mV +ADJ threshold, +/-15 nA monitor input current, and worst-direction 0.1% resistor tolerances. With the Phase 3D regulator ranges, guaranteed release margins are respectively 20.072 mV (core), 54.202 mV (3.3 V I/O), 19.462 mV (1.8 V reference/analog), and 13.314 mV (DMC); fault margins remain 9.608, 27.969, 23.427, and 12.641 mV [SUPV4 pp.2-4, 8-16; Phase 3C; Phase 3D].

Assign `V1=1V8_DSP_REF_ANA`, `V2=1V0_DSP_CORE`, `V3=1V35_DSP_DMC`, and `V4=3V3_SYS`. Pull `OUT1` up to `3V8_PRE` with 10.0 kohm, but do not connect it directly to any regulator EN. Phase 3E Schmitt-conditions PGOOD and forms `DOWNSTREAM_EN = OUT1 AND PGOOD_CLEAN AND DOWNSTREAM_RUN_DELAYED` in pre-powered hardware; that node drives core, DMC, `3V3_SYS`, and ADC analog EN. Microphone and AFE EN use the separate `ANALOG_PWR_EN` contract. Leave `OUT2`-`OUT4` unconnected except optional test points because the common `RST` provides the required aggregate. Ground `DVCC` for open-drain `RST`, pull `RST` up to `3V3_SYS` with 10.0 kohm, name that separate active-high rail-valid node `RAILS_OK`, and use it to drive watchdog `EN`. Tie `RDIS` and `MR` to `VCC`, tie `RT` to `VCC` for the guaranteed 160-240 ms common release delay, bypass `VCC` with at least 0.1 uF, and connect exposed pad 21 to ground. No capacitor is permitted on the PG pins [SUPV4 pp.2-4, 8-16; Phase 3E].

### 6.2 Power-up sequence

1. Input protection ramps `12V_PROTECTED`; amplifier MUTE and STANDBY remain low through their internal pulldowns and external hardware pulldowns.
2. `3V8_PRE` starts directly from `12V_PROTECTED`. The Phase 3A TPS3760 output is pulled up to this now-valid rail; once `12V_PROTECTED` passes its bounded rising threshold, `PGOOD_12V` enables `1V8_DSP_REF_ANA`. The 1.8 V rail starts first with a 65.8 ms nominal soft start. The oscillator and fanout start from this rail while the DSP remains held in reset.
3. When supervisor channel 1 observes valid 1.8 V, its real-time `OUT1` releases. Phase 3E pre-powered logic combines `OUT1`, `PGOOD_12V`, and the normal output of the retained shutdown timer to enable `1V0_DSP_CORE`, `1V35_DSP_DMC`, `3V3_SYS`, and `3V3_ADC_A`. `2V8_MIC` and `5V_AFE` remain off behind the cleared hardware-safe latch. This follows EE-470's VDD_REF-before-VDD_EXT mitigation [POWER pp.1-9; SUPV4 pp.8, 11; Phase 3E].
4. The 1.0 V and 3.3 V TPS62135 rails use 10 nF soft-start capacitors; both TPS7A49 DSP rails use 47 nF NR/soft-start capacitors. Each realized DSP supply ramp must be at least 100 us.
5. The LMK clock fanout starts with the 1.8 V rail and makes `SYS_CLKIN0` valid before reset release. The endpoint MCLK translator remains passive-disabled until both its rails exist and LTC2964 `RAILS_OK` asserts; MCLK is therefore available before DSP reset release without firmware or `HW_RUN_LATCHED`. Phase 3F `CLOCK_STARTUP_EN` controls only the later BCLK/FSYNC bank.
6. The supervisor's common open-drain `RST` keeps `RAILS_OK` low until all four channels are valid continuously for its guaranteed 160-240 ms release delay. `RAILS_OK` then enables the TPS3431; its open-drain `ENOUT`, wired with `WDO` at `SYS_HWRST`, releases after a further guaranteed 170-230 ms. Reset therefore releases 330-470 ms after all rail thresholds are valid. This exceeds the clock fanout's 3 ms maximum startup without inferring clock validity from regulator timing; at 24.576 MHz, the DSP minimum is only `11/24.576 MHz = 447.6 ns` [DSP p.53; CLKBUF; SUPV4 pp.3, 9, 11, 15; WDT pp.3, 9-13].

The worst static voltage difference is less than 1.563 V (`3.337821-1.775=1.562821 V`) and an isolated reference/analog rail is at most 1.866 V. Therefore `|VDD_EXT-VDD_REF|` and `|VDD_EXT-VDD_ANA|` remain below 1.89 V for monotonic ramps even if one side is at zero. Overshoot beyond the stated regulator bounds is prohibited [DSP pp.44, 52-53; POWER].

### 6.3 Power-down and brownout sequence

On commanded shutdown: assert amplifier MUTE, command all channels Hi-Z, assert STANDBY for at least 15 ms, set `ANALOG_PWR_CMD=0`, and wait at least 1 ms. The Phase 3E branch-local gate opens the analog switches and disables microphone/AFE EN while core/DMC remain powered. Then disable serial data, assert ADC reset, clear `RUN_HEALTH_OK_CMD`, and deassert `CLOCK_STARTUP_CMD`; BCLK/FSYNC stop while MCLK remains available. Pulse `SHUTDOWN_REQ`; the retained pre-powered latch asserts DSP reset immediately and the TPS3760E012 delay holds core/DMC/3.3 V/ADC power enabled for a guaranteed 20.415-40.946 ms before `DOWNSTREAM_EN` falls. The resulting low `RAILS_OK` then stops endpoint MCLK, after the devices are safe. Remove 1.8 V last on full source removal, then protected amplifier power collapses. Every DSP supply must still fall in at least 100 us and stay within 1.89 V of the others; Phase 4 must verify the loaded waveforms without changing the ordered groups [DSP pp.44, 52-53; Phase 3D; Phase 3E; Phase 3F].

On abrupt input loss: Phase 3A `PGOOD_12V` falls at 10.000 V nominal, bounded 9.870-10.130 V, and directly clears hardware-safe authorization without waiting for firmware. PGOOD is also a direct `DOWNSTREAM_EN` term and asserts `SYS_HWRST`; this pulls MUTE/STANDBY low, disables serial data and BCLK/FSYNC, asserts ADC/DSP reset, and disables all downstream and analog regulators before the revised eFuse UVLO opens. Rail invalidity pulls `RAILS_OK` low and disables endpoint MCLK; the independent root clock lasts only while 1.8 V remains valid. No graceful 15-ms/20-ms interval is claimed during abrupt energy loss. Recovery repeats hardware startup but cannot restore analog power or PLAY until firmware revalidates clocks and issues a new safe-arm edge.

TPS62135 active discharge and TPS7A20 active-discharge variants provide a defined off state. The populated schematic must include test points and DNP capacitance banks; oscilloscope verification must show every DSP domain rise and fall is at least 100 us at minimum/maximum input, 0/40 C prototype ambient, reset and maximum-load cases. A failed ramp test is a hardware stop requiring capacitor/discharge adjustment before DSP population. This is the formally approved verification method for the load-dependent falling ramps; it is not a waiver of the DSP limit.

## 7. Clock contract

### 7.1 Root and distribution

- Oscillator: `ASDLJ-D-24.576MHz-X-R-T`, 1.8 V +/-5%, -40 C to +105 C, +/-25 ppm, LVCMOS, 45-55% duty, 1 ms maximum startup, 15 pF load, 150 fs maximum integrated jitter over the stated band. Its OE is pulled up to 1.8 V so it starts with the rail [CLKOSC pp.1-4].
- Fanout: `LMK1C1103PWR`, powered from `1V8_DSP_REF_ANA`, one input and three 1.8 V LVCMOS outputs, no more than 50 ps output skew, 50 fs maximum additive jitter, 3 ns maximum propagation delay, and 3 ms maximum startup. Tie its active-high `1G` to its own 1.8 V rail through 10 kohm; do not expose this pin to the 3.8 V `OUT1`/enable node [CLKBUF].
- Output 0 goes through a 22-33 ohm source resistor to ADSP-21569 `SYS_CLKIN0` ball N01. `SYS_XTAL0` is left unconnected for external-clock mode [DSP pp.42, 54, 92; Phase 1 pin map].
- Outputs 1 and 2 separately feed the A ports of `SN74AXC2T245RSWR`; VCCA=1.8 V, VCCB=3.3 V, DIR1/DIR2 high for A-to-B. B1 drives ADAU1978 MCLKIN pin 7; B2 drives TAS6424E-Q1 MCLK pin 12. OE has a 10-kohm pullup to VCCA and an exact BSS138LT1G pull-down sink driven directly by `RAILS_OK`, with a 100-kohm gate pulldown. The device's Ioff, VCC isolation, and glitch-free supply sequencing prevent back-powering or an unintended output while a supply is absent [CLKXLAT pp.2-5, 18-23; Phase 3F].
- The oscillator drives only the LMK input. At worst rail bounds, its guaranteed high/low margins are `0.9x1.71 - 0.75x1.89 = 0.1215 V` and `0.25x1.71 - 0.1x1.89 = 0.2385 V`; the LMK's 7 pF input is below the oscillator's 15 pF load limit. Each fanout output then drives one CMOS input. The AXC data-I/O capacitance is 5.1 pF at its stated measurement condition, close to the LMK's 5 pF switching-characterization load; model that exact load and route before closing the schematic review. Use one source resistor per output and no unterminated branched MCLK trace.

### 7.2 Clock arithmetic and roles

| Quantity | Contract |
| --- | --- |
| Root/MCLK | 24.576 MHz; period 40.6901 ns |
| Sample rate | 96 kHz; `24.576 MHz / 256` |
| Slots/frame | 4 |
| Slot width | 32 bits |
| Payload | 24-bit two's-complement, MSB first, one-BCLK delay |
| BCLK/SCLK | `96 kHz x 4 x 32 = 12.288 MHz`; period 81.3802 ns |
| FSYNC | Active high, one BCLK wide (81.3802 ns), 96 kHz |
| ADC role | MCLK/BCLK/LRCLK slave; TDM transmitter |
| DSP role | Root-clock receiver; SPORT0 BCLK/FSYNC master; SPORT0A receiver and SPORT0B transmitter |
| Amplifier role | MCLK/SCLK/FSYNC slave; TDM receiver |

DSP CGU0 uses 24.576 MHz with `MSEL=80`: PLLCLK=1966.08 MHz, CCLK=983.04 MHz, SYSCLK=491.52 MHz, SCLK0=122.88 MHz. SPORT0 internal divide by 10 creates 12.288 MHz; its 128-bit frame creates 96 kHz. SPORT0, not an externally routed PCG, owns BCLK and FSYNC so the applicable internally clocked SPORT timing is retained [DSP pp.54-58; HRM chapters 23-24].

SRU/pin allocation is frozen:

- DAI0_PIN01, ball Y08: SPORT0 BCLK output;
- DAI0_PIN02, ball V09: SPORT0 FSYNC output;
- DAI0_PIN03, ball W09: SPORT0A primary receive data from ADC;
- DAI0_PIN04, ball Y09: SPORT0B primary transmit data to amplifier.

The ADAU1978 uses the MCLK-input PLL with MCS=`011` for 24.576 MHz at 96 kHz, FS=`011`, TDM4, 32-bit slots, and remains software-powered down until at least 10 ms after DVDD exceeds 1.2 V and stable MCLK is present; firmware then polls PLL lock before arming or enabling conversion [ADC pp.5, 12-16, 28-31; Phase 3F]. BCLK/LRCLK is not a PLL prerequisite in MCLK mode, but Phase 3F makes it available before arm for complete serial-clock validation.

The amplifier uses 24.576 MHz MCLK and 12.288 MHz SCLK, so the tied/equal-clock special case does not apply. `BCLK_INV=0`. Phase 3F supplies MCLK/SCLK/FSYNC before arm so any pre-existing sticky fault can be cleared and clock presence can be established without a latch dependency. Because active clock-fault monitoring in STANDBY is not guaranteed by the datasheet, validate it only after arm with the channels programmed Hi-Z and before MUTE/PLAY. Loss of a monitored valid clock drives outputs Hi-Z and asserts `FAULT_N`; clocks alone never authorize PLAY [AMPE pp.11, 22-25, 33-35, 49, 58].

### 7.3 Loaded timing closure

At the amplifier's 45% minimum clock phase, the short half-cycle is `0.45 x 81.3802 = 36.6211 ns`. With the LVC buffer's 7.2 ns maximum -40 C to +125 C propagation, a 2 ns board/skew allowance, DSP 3.5 ns maximum output delay, and amplifier 15 ns setup:

`36.6211 - 3.5 - 7.2 - 2 - 15 = 8.9211 ns` setup margin.

The corresponding conservative hold margin is `36.6211 - 3 - 7.2 - 2 - 15 = 9.4211 ns`, retaining the Phase 1C interpretation of the SPORT -3 ns figure [AMPE p.11; DSP pp.57-58; LVBUF pp.6-8].

For ADC data to DSP, using the ADC's 18 ns maximum data-valid time and DSP 2 ns setup:

`36.6211 - 18 - 7.2 - 2 - 2 = 7.4211 ns`.

ADAU1978 does not publish a minimum output-hold value. The formally accepted closure method is: capture the exact buffer/package and extracted trace loads in an IBIS or vendor timing simulation at voltage/temperature corners; preserve opposite-edge launch/sample; then measure ADC SDATAOUT versus the DSP sampling edge at 10.8/12/13.2 V, rail tolerance corners, 0 C and 40 C, and maximum configured cable/noise operation. Acceptance requires at least 3 ns measured hold and setup margin after probe uncertainty. Failure blocks board release; polarity may be changed only if all endpoint setup/hold calculations are repeated. The schematic is deterministic because the parts, edge relationship, test points, and pass criterion are fixed.

## 8. Logic-level contract

Strategy **B**, buffered/translated interfaces, replaces Phase 2's conditional direct-drive strategy.

### 8.1 Serial audio

Use one `SN74LVC244APWR` at 3.3 V and keep its two OE banks independent. Bank 1 contains exactly the two duplicated clock inputs/four outputs: DSP BCLK to ADC and amplifier, and DSP FSYNC to ADC and amplifier. Its active-low OE has a 10-kohm pullup to 3.3 V and an exact BSS138LT1G sink driven by Phase 3F `CLOCK_STARTUP_EN`, with a 100-kohm gate pulldown. Bank 2 contains ADC data to DSP and DSP data to amplifier; tie its two unused inputs low and leave their outputs open. Its OE has the same pullup/sink topology but is driven by `AUDIO_DATA_OE_RELEASE = HW_RUN_LATCHED AND AUDIO_DATA_OE_CMD_3V8`. Source-terminate every driven trace with 22-33 ohms. Low reset/PGOOD removes `CLOCK_STARTUP_EN`; the latch and command independently disable data [Phase 3F].

Worst-case input margins into the buffer are:

- DSP high: `2.4-2.0=0.4 V`; DSP low: `0.8-0.4=0.4 V`;
- ADC high at minimum 3.256299 V IOVDD: `(3.256299-0.6)-2.0=0.656299 V`; ADC low: `0.8-0.4=0.4 V`.

At light CMOS load the LVC output guarantees at -40 C to +125 C `VOH >= VCC-0.3`; with 3.256299 V minimum this is 2.956299 V. The worst receiver requirement is `0.7 x 3.337821=2.336475 V`, leaving 0.619824 V. Its `VOL <=0.3 V` leaves at least `0.3 x 3.256299-0.3=0.676890 V` [LVBUF pp.6-8; ADC pp.5-8; AMPE pp.7-11; DSP pp.44-48].

### 8.2 MCLK, control, memory, and debug

| Interface | Voltage/direction strategy | Contract |
| --- | --- | --- |
| Clock fanout to DSP | Direct 1.8 V | LMK output to SYS_CLKIN0; worst high margin is `0.8x1.71 - 0.65x1.89 = 0.1395 V`, low margin is `0.35x1.71 - 0.2x1.89 = 0.2205 V`. Keep load 5 pF and edge under device limit. |
| MCLK to ADC/amplifier | 1.8-to-3.3 V AXC translation | One channel per endpoint; A-to-B; passive-disabled OE is released automatically by hardware `RAILS_OK`, never by firmware or `HW_RUN_LATCHED`. Light-load output margins exceed 0.8 V high and low from CLKXLAT and endpoint thresholds. |
| I2C/TWI | Direct open-drain on common `3V3_SYS` | DSP master; ADC address 0x11, amplifier address 0x6A. Use 2.2 kohm pullups and limit total bus capacitance to 150 pF for 400 kHz; expose test points. No hot-plug. At the bounded rail, static HIGH margin is at least `3.256299-max(2.0, 0.7x3.337821)=0.919824 V`; with `VOL<=0.4 V`, LOW margin is at least `min(0.8, 0.3x3.256299)-0.4=0.4 V`. Pullup current is at most 1.52 mA. |
| SPI2 boot flash | Buffered 3.3 V, single-SPI | A second `SN74LVC244APWR` buffers DSP CLK/MOSI/CS toward the flash and flash MISO toward the DSP. Both sides share `3V3_SYS`; the buffer converts the DSP's guaranteed 2.4/0.4 V outputs into the rail-relative levels required by the flash and prevents powered-off injection. Buffer outputs leave at least 0.619824 V HIGH and 0.5 V LOW margin at either endpoint; flash MISO into the buffer leaves at least `(3.256299-0.2)-2.0=1.056299 V` HIGH and `0.8-0.2=0.6 V` LOW margin [FLASH p.171; LVBUF]. Its OEs are pulled low/enabled whenever 3.3 V is valid, independent of firmware. Use 22-33-ohm source resistors after the active driver and a 10-kohm CE pullup at the flash. Quad data pins are not part of the boot contract. |
| JTAG | Direct 3.3 V target domain | Use the official EV-21569-SOM 10-pin mapping below. The header carries target reference; the probe must not drive an unpowered target. TRST has the EE-68-required 4.7 kohm pulldown [SOMSCH sheet 9; JTAG p.6]. |
| UART0 | Direct 3.3 V CMOS | Logic-level only. External USB, RS-232, or RS-485 equipment requires an external adapter/transceiver. |
| Reset/mute/standby | Hardware-dominant open drain / gated release | DSP reset retains the Phase 3E hardware path. Phase 3F adds a dual open-drain ADC-reset buffer so `SYS_HWRST` or default-low `ADC_RST_RELEASE_CMD` asserts `ADC_PD_RST_N`, independently of the latch. A pre-powered latch clears on PGOOD, reset, eFuse fault, amplifier fault, or low run-health permit. Amplifier MUTE/STANDBY stay low by pulldowns; each release is `HW_RUN_LATCHED AND DSP command`. |
| Retained-domain commands | Isolated DSP command plus pre-powered qualification | One `SN74LXC8T245PWR` translates/power-isolates six commands (`ANALOG_PWR`, `SAFE_ARM`, `SHUTDOWN`, `CLOCK_STARTUP`, `AUDIO_DATA_OE`, `RUN_HEALTH_OK`) and Schmitt-conditions `SYS_HWRST`/`AMP_FAULT_N` on the remaining two A-to-B channels. Phase 3E/3F safe pulldowns make analog, clocks, data, health, arm, and shutdown-command edges deterministic. |

## 9. Analog front-end architecture

### 9.1 Bounded ANC prototype input contract

Because the final acoustic installation remains unknown, Phase 3 adopts the following safe, change-tolerant prototype point:

- electrical passband: 20 Hz to 20 kHz;
- initial ANC development band: 20 Hz to 1 kHz;
- crest-inclusive maximum microphone stimulus for linear design: 120 dBSPL sine-equivalent;
- AFE-only input-referred noise target: no more than 1.5 uVrms over 20 Hz-20 kHz, unweighted screening;
- ADC HPFs disabled; amplifier HPF bypassed;
- gain changes are made only by matched feedback resistors, not by topology changes.

This is **PROVISIONAL** and does not approve an ANC cancellation target or acoustic safety level. A later lower corner can be supported by increasing coupling capacitance; a later lower SPL ceiling can increase gain without changing the architecture.

### 9.2 Per-channel topology and values

The exact corrected implementation is frozen by [Phase 3G section 3](phase_3g_remaining_schematic_implementation_preflight.md): two `OPA4192IPWR` signal amplifiers, one `OPA2192IDR` AFE VCM buffer, and one `OPA320AIDBVR` ADC-local VREF buffer. For each of the eight legs use 4.7 uF nominal coupling (at least 2.2 uF effective), 100 kohm 0.1% bias to VCM, `Rg=2.80 kohm` and `Rf=1.27 kohm` 0.1% thin-film, and 47 ohms at the output. Retain one balanced 1 nF C0G differential capacitor at each ADC pair. Sheet 7 owns the connector-edge protection and matched 100-ohm RF resistors.

### 9.3 Gain and headroom

Nominal gain is 1.453571 V/V and the 0.1% corners are 1.452665-1.454479 V/V. The full-band worst case uses -37 dBV/Pa sensitivity, 120 dBSPL, the microphone's +9 dB maximum normalized response, VREF=1.47-1.54 V and a +/-2 mV combined dc-error allocation. It requires 0.651055-2.358945 V at each op-amp output. OPAx192 guarantees the applicable 0.6 V to `V+ - 0.6 V` open-loop region at 4.5-8 V, `RL=2 kohm`, over -40 C to +125 C. At the 4.858943 V minimum AFE rail, margins are 51.055 mV low and 1.900 V high. Full-band ADC amplitude is 1.155334 Vrms differential, leaving 4.766 dB relative to the ADC's typical 2 Vrms full scale [Phase 3G].

### 9.4 Low-frequency response, noise, and aliasing

The coupling high-pass corner per leg is:

- nominal: `1/(2pi x 100k x 4.7uF) = 0.339 Hz`;
- worst effective capacitance: `1/(2pi x 100k x 2.2uF) = 0.723 Hz`.

At 20 Hz, the worst pole contributes about 0.006 dB loss, 2.07 degrees phase lead, and 0.287 ms group delay. These terms must remain in the later ANC loop model; they are not “zero.” ADC register 0x1A channel HPF bits remain zero because the published enabled cutoff is conflicting. TAS6424E register 0x01 bit 7 bypasses its digital HPF [ADC pp.4, 14, 42; AMPE pp.25, 40].

A first-order 300 K screen for the corrected OPAx192/resistor/switch network gives approximately 1.423 uVrms differential input-referred over 20 Hz-20 kHz. This remains inside the 1.5 uVrms AFE allocation but is not a guaranteed built-board result. Phase 4 must simulate input noise, stability and CMRR; bench validation must use shorted/balanced inputs and a microphone-equivalent source [Phase 3G].

The ADAU1978's internal switched-capacitor antialias/decimation filter remains active. The 47-ohm/1 nF differential network has an approximate MHz-range RF pole and does not replace the ADC filter or alter the 20 Hz-20 kHz contract. No external audio-band low-pass is added because it would add unbudgeted ANC phase.

### 9.5 Powered-off and protection behavior

AC coupling prevents the microphone's 1.35 V DC bias from defining ADC common mode. Use the Phase 3G paired-domain population: four `TMUX1574PWR` packages provide 16 switch elements across all eight microphone legs, and ten `TMUX2821DSGR` packages provide the eight-leg AFE/ADC and one-leg VREF boundaries. Every crossing has one series element powered from each adjacent domain. External microphone cables use shield/chassis termination at the connector edge; cable shields do not carry signal return [Phase 3G].

## 10. Reset, supervision, and startup architecture

Use `LTC2964HUDC#PBF` plus `TPS3431SDRBR` and the exact Phase 3E retained-run/safe-state logic. The four-channel supervisor provides individual 1.8 V sequencing status and a common rail-valid reset; the separate watchdog preserves catastrophic-software supervision. Two `SN74LVC1G74DCUR` devices powered from `3V8_PRE` retain commanded-shutdown and hardware-safe state independently of the rails they control. Software cannot guarantee rail validity, power-failure response, or the five-domain reset condition [Phase 3B; Phase 3E].

### 10.1 Normal startup state machine

1. **Power applied:** TPS26630 validates voltage/polarity and limits inrush; the Phase 3A TPS3760 holds `PGOOD_12V` low. Amplifier MUTE/STANDBY, ADC reset, run health, and endpoint clock/data OEs remain in their passive safe states.
2. **Regulators start:** `3V8_PRE` starts from the protected rail; valid `PGOOD_12V` presets the downstream-run latch and enables 1.8 V; `OUT1` plus the pre-powered Phase 3E qualification then enables core, DMC, 3.3 V, and ADC analog. Microphone/AFE power remains off.
3. **Root and MCLK valid:** oscillator and LMK fanout settle; the DSP clock output is enabled independently. When the four monitored rails qualify, `RAILS_OK` automatically enables ADC/amplifier MCLK before DSP reset release. BCLK/FSYNC remain disabled until the later bootstrap command.
4. **DSP reset:** LTC2964 releases `RAILS_OK` only after every monitored rail has remained valid for 160-240 ms; TPS3431 `ENOUT` then adds 170-230 ms before `SYS_HWRST` releases. The 330-470 ms total also covers bounded clock startup. Low `SYS_HWRST` asynchronously clears `HW_RUN_LATCHED`.
5. **DSP boot:** ROM boots SPI2 flash. Earliest code establishes safe GPIO, watchdog, CGU, SRU/SPORT clock generation, DMA, and TWI; amplifier remains in STANDBY.
6. **Bootstrap serial clocks:** confirm the already-running endpoint MCLK, then assert `CLOCK_STARTUP_CMD`. `CLOCK_STARTUP_EN` releases only the SN74LVC244A BCLK/FSYNC bank. Serial data, analog power, and amplifier releases remain blocked.
7. **ADC safe initialization:** with MCLK stable, release the independent `ADC_PD_RST_N`; observe the Phase 3F DVDD/reset timing, configure 96 kHz/TDM4/MCLK PLL/HPF-off while PWUP remains controlled, wait the manufacturer interval, and poll PLL lock. A missing response or lock leaves health and the latch LOW.
8. **Amplifier pre-arm configuration:** after its 12 ms I2C startup and with all three clocks present, write/read back phase, TDM, gain, HPF, OC, and warning settings; clear faults and confirm no presently asserted fault while STANDBY remains LOW. Do not infer active clock monitoring in STANDBY because TI does not specify that boundary.
9. **Arm and active amplifier check:** assert `RUN_HEALTH_OK_CMD`, then pulse `SAFE_ARM_CMD`. Enable the data bank and release STANDBY only into the programmed Hi-Z channel state; verify active clock ratios/status and no `FAULT_N`. A fault clears the latch and returns STANDBY LOW before MUTE/PLAY. Clearing a fault or restoring health without a new arm edge cannot restore functional audio.
10. **Analog/mute release:** after the active amplifier check, assert `ANALOG_PWR_CMD`; wait for the microphone's 30 ms maximum startup and AFE/ADC DC settling, valid DMA frames, valid coefficients, and no FAULT/WARN; enter MUTE state, ramp volume, then PLAY.
11. **Normal operation:** hardware watchdog, eFuse FLT, `PGOOD_12V`, amplifier FAULT/WARN, ADC PLL state, rail test points, and clipping counters remain monitored. Firmware drops run health before any clock/ADC requalification.

### 10.2 Fault behavior

| Event | Required response |
| --- | --- |
| Brownout/OVP/eFuse fault | Low PGOOD/fault asynchronously clears safe authorization, forces analog EN and `DOWNSTREAM_EN` low, asserts amplifier MUTE/STANDBY and DSP/ADC reset, and removes serial-data and endpoint-clock OEs. No automatic PLAY. |
| DSP reset/watchdog/JTAG halt | Low `SYS_HWRST` clears safe authorization, turns microphone/AFE power off, asserts ADC reset, removes BCLK/FSYNC/data, and forces amplifier safe. Endpoint MCLK and the root clock remain on while `RAILS_OK`/1.8 V are healthy for deterministic reboot. A new arm edge is mandatory. |
| Missing common/amplifier MCLK/SCLK/FSYNC while amplifier monitoring is active | Amplifier enters Hi-Z and asserts sticky `FAULT_N`, clearing the latch. ADAU1978 retains `PLL_MUTE=1`; firmware drops run health on ADC-only MCLK/PLL loss. Full clock/PLL/configuration recheck and a new arm edge are mandatory. |
| Amplifier FAULT | Low `AMP_FAULT_N` clears the hardware-safe latch, forces MUTE/STANDBY and microphone/AFE power off, but retains DSP rails for fault-register access. Repeated OC/thermal/DC fault requires user/service clear or power cycle. |
| ADC PLL unlock/data framing error | ADAU1978 hardware automute remains enabled. Drop run health, data OE and amplifier releases; reset/reinitialize ADC/SPORT and discard buffers. Keep bootstrap clocks only as needed for diagnosis; issue a new arm edge after complete revalidation. |
| Commanded shutdown | Ordered sequence in section 6.3 and Phase 3E; the retained latch completes DSP reset and the >=20 ms downstream hold after firmware stops. |

Use `TPS3431SDRBR` at `3V3_SYS` for the catastrophic-software watchdog. Drive `EN` only from the separate LTC2964 `RAILS_OK` node so WDO assertion cannot disable its own timer; tie `SET1` high to prevent firmware from defeating it. Leave `CWD` unconnected for the factory-guaranteed 1.36-1.84 s timeout. Tie open-drain `ENOUT` and `WDO` together at `SYS_HWRST` with one 10.0 kohm pullup to `3V3_SYS`; Phase 3E adds the defined pulldown and pre-powered open-drain shutdown assertion. Low `SYS_HWRST` asynchronously clears the hardware-safe latch. ENOUT holds reset low for 170-230 ms after RAILS_OK; a watchdog timeout holds WDO low for 170-230 ms while EN remains high. Firmware must issue its first valid WDI falling edge within at least `1.36 s - 0.23 s = 1.13 s` after reset release. Bypass `VDD` with 0.1 uF. This watchdog is not the real-time ANC deadline monitor; the DSP's internal watchdog and audio-frame deadline logic must react faster [WDT pp.3, 9-14; Phase 3E].

## 11. Boot, memory, and debug architecture

| Item | Frozen contract |
| --- | --- |
| Boot mode | `SYS_BMODE=001`, SPI2 flash master boot [DSP p.18; BOOT; HRM ch.40]. |
| Flash | `IS25LP512M-RMLE`, 512 Mbit/64 MB, 2.3-3.6 V, 16-pin SOIC, dedicated RESET, extended -40 C to +105 C [FLASH pp.2, 7-9, 170-185]. |
| Capacity | Minimum PCB design capacity 16 MB; selected 64 MB supports two firmware images, boot metadata, coefficients, calibration, and logs. Exact partition/authentication policy remains `UNKNOWN`. |
| Interface | Dedicated buffered single-SPI2: CLK PA04/R01, MISO PA00/N03, MOSI PA01/P03, CS PA05/T02. A dedicated `SN74LVC244APWR` provides the fixed directions in section 8.2; use 22-33-ohm source resistors after each driver and a 10-kohm CE pullup at the flash. IO2/WP and IO3/HOLD use their datasheet-safe 10-kohm defaults and are not routed as quad data. Tie every unused buffer input to a defined level. Phase 3E uses a separate dual-supply translator for its three retained-domain commands. CE remains high until at least 300 us after flash VCC reaches minimum [FLASH p.177; Phase 3E]. |
| Reset | Flash dedicated RESET joins the system reset policy; do not reset during program/erase. |
| Straps | Three populated 10-kohm strap positions default to `001` (SPI2 flash); resistor-option pads select `000` for no boot or `011` for external UART0 host recovery. `010` SPI2-host and other modes are not populated. No strap state may float [DSP p.18]. |
| JTAG | 10-pin, 0.05-inch keyed ADI/SOM mapping: 1 target `3V3_SYS` reference, 2 TMS, 3 GND, 4 TCK, 5 GND, 6 TDO, 7 TRST, 8 TDI, 9 GND, 10 `SYS_HWRST` through a zero-ohm series footprint. Fit the required 4.7-kohm TRST pulldown; no EMU signal is invented. Keep the single-DSP route short and provide optional source-series footprints [SOMSCH sheet 9; SOM; JTAG p.6]. |
| UART | UART0 TX PA06/T03 and RX PA07/V01 plus optional RTS/CTS on reserved GPIO; 3.3 V CMOS header. Default 115200-8-N-1 is a firmware convention, not a silicon requirement. |
| Programming | Primary: CCES/ADI ICE through JTAG and CLDP-compatible SPI flash loader. Recovery: force UART0 host boot with strap option. Blank flash and interrupted update must be demonstrably recoverable before production. |

The ROM anomaly/workaround set in `ANOM` remains binding, including silicon-revision-specific DMC and boot behavior. No OTP security provisioning is authorized in Phase 3.

## 12. Connector requirements

| Function | Minimum connector contract | Electrical/shielding requirements |
| --- | --- | --- |
| 12 V input | 2 power pins: `12V_IN`, `POWER_GND`; keyed; at least 6 A/contact pair, 30 V DC | Short return; chassis/shield bond, if provided, is a separate mechanical terminal near entry. No signal current through chassis. |
| Microphone 1-4 | Four identical 5-pin ports: `2V8_MIC`, `MIC_OUT+`, `MIC_OUT-`, `MIC_GND`, shield/chassis | At least 30 V contact rating, low-level balanced pair, shield terminates at entry, cable target below 0.5 m for prototype. Do not combine shield and analog return in the cable pinout. |
| Speaker 1-4 | Four 2-pin ports: `SPKn+`, `SPKn-` | At least 3 A continuous/contact and 7 A fault withstand, 30 V DC; keyed; twisted pair. Both pins are switching BTL outputs; neither may be grounded, chassis-bonded, or shared. |
| JTAG | 10-pin keyed 0.05-inch ADI/SOM mapping | Exact pin map is frozen in section 11; three ground contacts, target-voltage reference and reset access are retained; no external power injection. |
| UART/debug | 6 pins: 3V3 reference, GND, TX, RX, RTS, CTS | Logic level only; keyed or clearly marked; no 5 V tolerance claim. |
| Service I2C | Optional DNP 4 pins: 3V3 reference, GND, SCL, SDA | 400 kHz maximum, no hot-plug, no external pullups unless internal pullups are disconnected. |
| Test/service | Test points for every rail, `PGOOD_12V`, TPS26630 FLT, all resets/OEs, MCLK/BCLK/FSYNC, TDM RX/TX, amplifier FAULT/WARN | Test points must not create long stubs on clock/audio nets. |

Physical connector series and enclosure feedthrough remain mechanical selections. They must satisfy these pin/current/isolation requirements and do not alter the schematic architecture.

## 13. Thermal requirements

### 13.1 Prototype boundary

Assume 0 C to 40 C ambient, open bench or vented prototype, no credited forced airflow, and permission for a grounded external heatsink. Final enclosure, airflow, touch temperature, and acoustic duty cycle remain `UNKNOWN`; therefore final thermal compliance is not claimed.

### 13.2 Amplifier

TI's four-channel example at 4 x 10 W dissipates 8 W in the IC and reaches about 115 C junction at 25 C ambient with a 10.45 C/W heatsink path and 11.24 C/W system RthetaJA. The package exposes its thermal pad upward and requires a grounded heatsink/thermal interface [AMPE pp.68-69]. Although this design targets only 4 x 6 W, use 8 W IC dissipation as the schematic/PCB thermal design case until a measured efficiency/loss model exists.

At 40 C ambient and a 110 C design junction target, allowable total junction-to-ambient path is `(110-40)/8 = 8.75 C/W`. Reserve an exposed-top grounded heatsink and interface whose sink-to-ambient contribution is no more than 7.5 C/W, subject to the complete interface/case calculation. Place temperature-sensor/test access near the amplifier. Do not locate ADC, microphone AFE, oscillator, or VREF circuitry in the amplifier heat plume.

### 13.3 DSP, regulators, and board

- The DSP core regulator is sized for 3 A and the processor for the industrial 125 C junction grade. Board design target is at most 105 C measured/estimated junction at the 40 C prototype ambient. The datasheet explicitly requires system-level 3D thermal analysis; JEDEC theta values alone are not compliance [DSP p.88].
- Place `1V0_DSP_CORE` regulator and bulk capacitance close to the BGA power region with a wide plane and dense ground stitching, but outside the AFE quiet area.
- TPS26630 may dissipate about 0.85 W at 4 A using worst-case RON; solder its exposed pad to a multi-layer copper/via heat spreader [PWRIN pp.4, 6-7].
- `5V_AFE` worst allocated loss is about 0.41 W. With the TPS7A49 DGN JEDEC 63.4 C/W metric, the first-order rise is 26 C; provide PowerPAD copper and keep the device away from the microphone inputs [HVLDO p.6].
- Converter inductor and MOSFET loss, amplifier output-inductor heating, bulk-capacitor ripple, and connector temperature rise require BOM-level calculation and thermocouple/IR validation at four-channel continuous load.

PCB planning requirements are therefore: dedicated amplifier thermal/heatsink zone; uninterrupted ground reference; short high-current PVDD/BTL loops; no speaker switching under analog/clock areas; exposed-pad via arrays for eFuse/regulators/ADC as applicable; thermal keepout around microphone/AFE; and temperature measurement points. These are requirements for later layout, not authorization to place or route.

## 14. Schematic sheet plan

### Sheet 1 - Power input / protection

- Major parts: input connector, fuse footprint, 1 uF entry capacitor, DNP bidirectional TVS footprint, TPS26630RGER, TPS3760A012DYYR, CSD19537Q3, BSS138, 470 uF bulk, PGOOD/FLT conditioning.
- Rails: `12V_IN`, `12V_PROTECTED`, `POWER_GND`.
- Critical values: UV/OV ladder 316 k/13.3 k/30.4 k, all 0.1%; `RILIM=3.24 k`; `CdVdT=47 nF`; TPS26630 PGTH grounded; TPS3760 sense divider 115 k/10.0 k, both 0.1%; TPS3760 RESET pullup 10.0 k to `3V8_PRE`; MODE open.
- Interfaces/dependencies: the protected rail starts `3V8_PRE`; Phase 3A `PGOOD_12V` is then pulled up to 3.8 V, qualifies the remaining Sheet 2 sequence, and drives conditioned hardware safe state; TPS26630 FLT separately feeds the DSP and latch; 6 A copper/connector contract.
- Evidence: PWRIN pp.3-34, [Phase 3A](phase_3a_pgood_contract_correction.md), AMPE pp.63-69.

### Sheet 2 - Power regulation / sequencing

- Major parts: three TPS62135 converters (`3V8_PRE`, `1V0_DSP_CORE`, `3V3_SYS`); three TPS7A4901 (`1V8_DSP_REF_ANA`, `1V35_DSP_DMC`, `5V_AFE`); TPS7A2033P, TPS7A2028P; `LTC2964HUDC#PBF`; `TPS3431SDRBR`; two `SN74LVC1G74DCUR`; one `TPS3760E012DYYR`; one `SN74LVC2G07DBVR`; one `SN74LVC2G17DBVR`; **two** `SN74LVC2G08DCUR`; ten `SN74LV1T08DBVR`; ten `TMUX2821DSGR`; and four `TMUX1574PWR`. The second dual AND implements final safe clear and `CLOCK_STARTUP_EN`; Phase 3G corrects the analog-isolation population [Phase 3F; Phase 3G].
- Rails: every rail in section 5.
- Critical values: TPS62135 feedback pairs 44.2 k/10.0 k (pre), 4.32 k/10.0 k (core), and 37.1 k/10.0 k (`3V3_SYS`), all 0.1%; TPS7A4901 feedback pairs (54.2 k + 100 ohm)/100 k, 14.9 k/100 k, and 324 k/100 k, all 0.1%; LDO preloads 1.69 k, 1.24 k, 4.70 k, 3.01 k, and 2.55 k, all 0.1%, as mapped in Phase 3D. Use 10 nF buck soft starts, 47 nF DSP-rail and 10 nF AFE TPS7A49 NR/SS capacitors, Phase 3D passive limits, and the Phase 3E `DOWNSTREAM_EN`/`ANALOG_PWR_EN` architecture. `U_DOWN_DELAY` CTS is 220 nF nominal and must remain 198-242 nF effective. Fit every specified EN/pull/reset network and test point.
- Interfaces/dependencies: `PGOOD_12V`, `OUT1`, `DOWNSTREAM_RUN_DELAYED`, `DOWNSTREAM_EN`, `ANALOG_PWR_EN`, `SYS_HWRST`, `SAFE_HW_CLEAR_N`, `SAFE_CLEAR_N`, safe arm, run health, clock-startup/data-OE commands, shutdown request, regulator EN/PG, ADC reset, separate clock/data buffer OEs, amplifier MUTE/STANDBY/FAULT.
- Evidence: BUCK, LDO, HVLDO, SUPV4, WDT, PGSUP, SEQLATCH, RSTBUF, SCHMITT, AMPGATE, CMDXLAT, ENLOGIC, DSP pp.44, 52-53, POWER, and Phase 3B through Phase 3F.

### Sheet 3 - Microphones / AFE

- Major parts: two `OPA4192IPWR` signal amplifiers and one `OPA2192IDR` VCM buffer. The microphone modules/connectors and edge protection belong to Sheet 7; the analog-isolation devices belong to Sheet 2.
- Rails: `5V_AFE`, isolated buffered 1.5 V VCM, solid ground reference.
- Critical values: 4.7 uF coupling (2.2 uF effective minimum), 100 k bias, 2.80 k/1.27 k 0.1% gain, 47 ohm ADC drive, 1 nF C0G differential.
- Interfaces/dependencies: eight isolated microphone legs in, eight raw AFE legs out, and the isolated VCM feed. Exact scalar hierarchy count is 18; see Phase 3G section 4.1.
- Evidence: MIC, ADC, AFE3G, VREFBUF3G, MICISO3G, ANISO, and Phase 3G.

### Sheet 4 - ADAU1978 ADC

- Major parts: `ADAU1978WBCPZ`, one `OPA320AIDBVR` VREF buffer, and one additional `SN74LVC2G07DBVR` for the two-source open-drain reset assertion.
- Rails: AVDD=`3V3_ADC_A`, IOVDD=`3V3_SYS`, internal DVDD decoupling, VREF/PLL filter.
- Interfaces: AIN1-4 from Sheet 3 through paired-domain TMUX2821 isolation; locally buffered VREF through the paired ADC/AFE-powered TMUX2821 path; MCLKIN pin 7 from clock translator; LRCLK pin 15/BCLK pin 16 from buffer; SDATAOUT1 pin 13 to buffer; I2C pins 17/18; PD/RST pin 6. Exact scalar hierarchy count is 18 [Phase 3G].
- Critical configuration: I2C address 0x11; 96 kHz, MCLK PLL MCS=011, `PLL_MUTE=1`, TDM4/32-bit slots, one-bit delay, HPFs off; SDATAOUT2 unused per documented pin policy. Fit 3.00-kohm 1% DVDD `REXT`, 10-uF nominal X7R CEXT with effective maximum no more than 12 uF, and require at least 50 ms PD/RST LOW for in-place reset.
- Dependencies: Phase 3F MCLK before reset release; manufacturer DVDD/POR wait; at least 10 ms after DVDD >1.2 V and stable MCLK before PWUP; PLL-lock poll before run health/arm; BCLK/FSYNC and data are not PLL prerequisites in MCLK mode.
- Evidence: ADC pp.3-16, 21-31, 40-44.

### Sheet 5 - ADSP-21569 DSP / boot / debug / clocks

- Major parts: ADSP-21569BBCZ10, ASDLJ oscillator, LMK1C1103, SN74AXC2T245, one bank-partitioned SN74LVC244A for audio and one SN74LVC244A for boot SPI, Phase 3E/3F `SN74LXC8T245PWR` command translator, three exact BSS138LT1G OE sinks, IS25LP512M-RMLE, JTAG/UART/strap headers.
- Rails: all five DSP domains, 1.8 V clock, 3.3 V flash/debug.
- Interfaces: fixed DAI0 pins from section 7; SPI2 pins, UART0 pins, TWI, all POR/watchdog/fault signals.
- Critical configuration: SYS_BMODE=001; 24.576 MHz CGU contract; SPORT0A RX/SPORT0B TX; no DDR, powered DMC domain and half-rail VREF; TRST 4.7 k pulldown.
- Dependencies: Sheet 2 POR and safe-state; Sheet 4/6 control and audio; root clock and `RAILS_OK`-enabled MCLK precede reset release; Phase 3F `CLOCK_STARTUP_EN` may release only BCLK/FSYNC before arm; serial data remains latch-gated.
- Evidence: DSP, POWER, HRM, BOOT, ANOM, SOM/SOMSCH, JTAG, CLKOSC, CLKBUF, CLKXLAT, FLASH.

### Sheet 6 - TAS6424E-Q1 amplifier

- Major parts: TAS6424EQDKQRQ1, four pairs of output inductors, shunt/EMI capacitors, bootstrap/GVDD/rail capacitors, hardware mute/standby/fault network.
- Rails: `12V_PROTECTED` PVDD/VBAT and `3V3_SYS` VDD.
- Interfaces: MCLK pin 12; buffered SCLK pin 13, FSYNC pin 14, SDIN1 pin 15; SDIN2 pin 16 grounded; I2C 20/21; control/status 24-27; eight BTL outputs.
- Critical configuration: 0x03=0x86, 0x01=0xE0, 0x02 low bits=10, 0x28=0x2A, 0x26=0x40; gain level 1; four BTL channels; HPF bypass; level-1 OC; hardware remains Hi-Z until checks pass.
- Dependencies: grounded heatsink, 470 uF bulk, Phase 3F pre-arm valid-clock/fault verification, 12 ms I2C delay, 15 ms standby shutdown, and Phase 3E `HW_RUN_LATCHED AND DSP command` gates for MUTE/STANDBY release.
- Evidence: AMPE pp.3-11, 22-29, 33-44, 58-69; AMPEEVAL; INDUCTOR.

### Sheet 7 - Connectors / system interfaces

- Major items: power, four microphone, four speaker, JTAG, UART, optional service-I2C connectors and labeled test points.
- Rails/interfaces: only those explicitly assigned in section 12; no generic “ground” on BTL output connectors.
- Critical values: 6 A input, 3 A continuous/7 A fault speaker contacts, 3.3 V-only debug, separate shield/chassis pins.
- Dependencies: final connector series/mechanics; all protective and safe-state circuits remain on their functional sheets.
- Evidence: section 12 plus component current/voltage sources above.

## 15. Schematic implementation contract

The Phase 4 schematic agent shall implement the seven sheets above without changing these architectural decisions. In particular:

1. Preserve exact main-device variants and packages: IM73A135V01, ADAU1978WBCPZ, ADSP-21569BBCZ10, TAS6424EQDKQRQ1.
2. Preserve the 4-ohm/6 W/four-channel design point and 7.5 V-peak amplifier gain limit.
3. Preserve the input range/cutoffs, TPS26630 latch-off topology, 5.56 A nominal current limit, and hardware safe-state behavior.
4. Implement every rail and every ADSP supply ball under the Phase 3D regulator/divider/preload/passive contract; do not omit or merge `VDD_DMC`; do not add DDR.
5. Implement the Phase 3E correction as amended by Phase 3F/3G: no direct `OUT1` regulator EN connections; retained `DOWNSTREAM_EN`; shared qualified microphone/AFE enable; hardware-safe latch with final run-health clear; TPS3760E012 post-reset delay; open-drain shutdown/ADC reset; and the exact ten-`TMUX2821DSGR` plus four-`TMUX1574PWR` paired-domain analog isolation population. Preserve VDD_REF-before-VDD_EXT sequencing, the 100 us minimum rail-rise/fall requirement, all-rail reset monitoring, and 1.8 V-last ordered shutdown.
6. Preserve the exact 24.576 MHz oscillator/fanout/translator tree, one load per fanout output, DAI0_PIN01-04 allocation, automatic `RAILS_OK` MCLK enable, and Phase 3F pre-arm BCLK/FSYNC `CLOCK_STARTUP_EN`. Neither DSP primary clock nor endpoint bootstrap clocks may depend on `HW_RUN_LATCHED`.
7. Preserve the opposite-edge TDM timing, Phase 3F separate LVC clock/data banks, passive-disabled OEs, exact OE sinks, and test points. Before schematic review closes, run the loaded timing and clock/startup dependency methods.
8. Preserve Phase 3G AFE gain 1.453571 nominal, sub-0.73 Hz worst coupling pole, the two-stage OPA320/OPA2192 VREF-common-mode chain, and HPF-off/bypass policy. Provide resistor/capacitor tuning footprints without changing topology.
9. Preserve active-low annotation and passive-safe defaults for reset, MUTE, STANDBY, OEs, microphone/AFE enables, flash CE/RESET, and boot straps. No safe-state fault clear may automatically restore analog power or PLAY.
10. Verify every symbol pin number against the cited official document; third-party symbols are not accepted without an independent pin table. Run ERC and retain outputs under `validation/`.

The following analyses are required during Phase 4 but are not invitations to invent architecture: regulator inductor/capacitor manufacturer-part selection against the frozen Phase 3D electrical limits; full populated-BOM rail loads; reproduction of the frozen power-divider corners and tolerance/Monte Carlo for the remaining protection and AFE networks; input/clock/audio IBIS or equivalent timing; reset/power transient simulation; op-amp stability/noise; and symbol-pin audit.

## 16. Remaining unknowns

| Item | Status | Resolution path / effect |
| --- | --- | --- |
| Final ANC cancellation band, phase mask, geometry, reference/error microphone assignment, acoustic preview | **UNKNOWN** | Controls/acoustic definition and prototype measurement. Does not change four-channel AFE topology; may change gain/coupling or firmware. |
| Final speaker model, enclosure, excursion and acoustic safety | **UNKNOWN** | Select a speaker meeting section 3 before energized acoustic testing. May change passive output filter/heatsink, not basic BTL architecture within 4-ohm bound. |
| Complete FxLMS cycle/memory/block-size budget | **UNKNOWN** | Firmware benchmark at 983.04 MHz using L1/L2. If external DDR becomes necessary, architecture must return to a new gate; DDR is not silently added. |
| Final product ambient/enclosure/airflow/touch-temperature limits | **UNKNOWN** | Product/mechanical decision plus 3D thermal simulation and four-channel thermal test. Current open-bench assumption is only for prototype planning. |
| EMC, cable ESD/EFT, emissions and immunity class | **UNKNOWN** | Define product standard and validate later. No automotive compliance inferred. |
| ADC enabled-HPF numerical cutoff discrepancy | **CONFLICTING** | Irrelevant to current HPF-off implementation; manufacturer clarification is needed before enabled use. |
| Exact flash partition, authentication, rollback and calibration retention | **UNKNOWN** | Firmware/product security decision; selected hardware capacity and recovery access remain sufficient. |
| Exact connector series and production availability | **UNKNOWN** | Mechanical/procurement selection within section 12 ratings. |

## 17. Remaining schematic blockers

### 17.1 Review of all four hard blockers

| Phase 2 blocker | Final status | Basis |
| --- | --- | --- |
| AFE contract closure | **RESOLVED by Phase 3G** | Eight differential legs, exact paired-domain isolation, corrected VREF buffers, OPAx192 population, 1.453571 nominal gain, guaranteed low-supply headroom, noise/pole calculations and sheet ownership are deterministic. Remaining simulation/bench work is physical validation. |
| Clock implementation closure | **RESOLVED as corrected by Phase 3F** | Exact oscillator, fanout, translators, rails, loading rule, DAI/SPORT allocation, clock arithmetic, timing margins, pre-arm bootstrap OE, separate post-arm data OE, ADC reset sequence, and formal ADC-hold validation method are defined without a latch cycle. |
| Power and sequencing closure | **ACCEPTED PROVISIONALLY** | Input envelope, all rail sources/loads, DMC disposition, Phase 3B supervisor thresholds, Phase 3C system-rail reroute, Phase 3D static-bound/current/headroom/passive audit, and the Phase 3E independent shutdown/safe-state/back-power correction are defined. Later physical validation must satisfy the frozen limits and does not authorize architectural substitution. |
| Conditional direct-I/O closure | **RESOLVED** | Direct-drive assumption is replaced by qualified buffering/translation; common-domain buses have explicit voltage limits and margins. |

There are **no remaining blockers to schematic entry** within the Phase 3 prototype bounds. There are substantial blockers to PCB release, acoustic operation, final thermal claims, and product compliance; they are listed in sections 15-16 and may not be treated as completed work.

## 18. Phase 4 recommendation

Proceed only to a separately authorized Phase 4 schematic implementation. Phase 4 may create the hierarchical schematic described here, verify every symbol pin, complete component/passive/tolerance and populated-load calculations, run ERC, and execute the pre-PCB timing/power/AFE checks in section 15. It is not authorization for PCB placement, routing, production release, or a claim that ANC performance has been validated.

PHASE 3: PASS
