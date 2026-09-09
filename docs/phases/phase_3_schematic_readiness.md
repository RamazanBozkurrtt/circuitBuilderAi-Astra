# Phase 3 - Schematic Readiness and Detailed Electrical Architecture

Date: 2026-09-09 (Europe/Istanbul)

Scope: documentary verification, calculations, component-level electrical architecture, and a contract for a later schematic phase. No KiCad, schematic, PCB placement, routing, firmware, or Phase 4 work was created.

Evidence notation such as `DSP p.53` refers to the source IDs and local manufacturer documents in the [component evidence index](../evidence/component_evidence_index.md). `CONFIRMED` means device evidence or an already approved project decision; `PROVISIONAL` is a bounded Phase 3 engineering decision; `UNKNOWN` and `CONFLICTING` retain their Phase 0 meanings.

## 1. Executive summary

The four Phase 2 hard schematic-entry blockers have been resolved or bounded without weakening them. The resulting prototype design point is:

- four nominal 4-ohm BTL speakers, 6 W continuous per channel with all four channels active, and 7.03 W sine-equivalent full-scale/short-peak power per channel;
- a regulated 12 V nominal input, 10.8 V to 13.2 V normal operating range, 4 A continuous and 5 A short-peak source capability;
- input cutoff, reverse-polarity, overcurrent, inrush, brownout, and hardware-safe mute behavior based on TPS26630;
- a deterministic `3V8_PRE` intermediate rail and sequenced 1.0 V, 1.35 V, 1.8 V, 2.8 V, 3.3 V, and 5.0 V rails;
- ADSP-21569 `VDD_REF/VDD_ANA` before `VDD_EXT`, all five DSP domains monitored, all DSP rails and the 24.576 MHz clock valid before reset release, and explicit power-down behavior;
- one 24.576 MHz, 1.8 V oscillator, a 1:3 low-skew clock fanout, and two 1.8-to-3.3 V MCLK translators;
- separate buffered 3.3 V serial-audio paths instead of the Phase 2 conditional direct-drive assumption;
- a two-op-amp-per-microphone AC-coupled differential AFE using OPA1654, gain 3.8 V/V, a worst-case coupling corner below 0.73 Hz, and ADC HPFs plus amplifier HPF disabled;
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
                                      `----> TPS62135  -> 3V8_PRE
                                                        |-> TPS7A4901 -> 1V8_DSP_REF_ANA
                                                        |-> TPS62135  -> 1V0_DSP_CORE
                                                        |-> TPS7A4901  -> 1V35_DSP_DMC
                                                        |-> TPS62135  -> 3V3_SYS
                                                        |-> TPS7A2033P -> 3V3_ADC_A
                                                        `-> TPS7A2028P -> 2V8_MIC
```

### 5.1 Rail contract

Loads are design allocations, not measured consumption. They include margin and must be replaced by populated-BOM worst-case calculations in Phase 4 without exceeding the allocations.

| Rail | Required range / selected source | Maximum-load allocation and startup | Noise/filtering | Sequencing and architectural decoupling |
| --- | --- | --- | --- | --- |
| `12V_PROTECTED` | 10.4-13.2 V normal at the load; TPS26630 direct protected input; connector-to-load path drop no more than 0.4 V at 4 A | 4 A continuous, 5 A less than 1 s; 470 uF amplifier bulk dominates inrush | High-current/switching domain; do not feed microphone/ADC directly except through regulators | First rail. Local 1 uF at eFuse, 470 uF/25 V near amplifier, and TI per-PVDD local networks. Phase 3A `PGOOD_12V` defines system validity. |
| `3V8_PRE` | 3.80 V, +/-1%; TPS62135, forced PWM; `R1=442 kohm`, `R2=100 kohm`, 0.1%, gives 3.794 V nominal | 1.8 A design allocation; startup is regulator/capacitor charging | Switching pre-rail; keep away from AFE inputs and post-filter sensitive branches | Enabled directly whenever `12V_PROTECTED` is present; this avoids a PGOOD/pullup circular dependency. `CSS=10 nF` for approximately 2.8 ms programmed ramp; 1 uH class inductor, at least 5 A saturation, no more than 30 milliohms DCR; 22 uF effective output minimum plus 10 uF local bulk. |
| `1V0_DSP_CORE` | 1.00 V, required 0.95-1.05 V; TPS62135, forced PWM, +/-1%; `R1=42.7 kohm`, `R2=100 kohm`, 0.1%, gives 0.999 V nominal | 3.0 A design maximum. Phase 1 high-corner subtotal was 2.0605 A but incomplete; regulator is 4 A | Moderate sensitivity/high di/dt; compact hot loop and uninterrupted local plane | Enabled only after 1.8 V valid. `CSS=10 nF`; at least 100 uF effective domain bulk plus the per-ball network. PGOOD/supervisor monitored. |
| `1V8_DSP_REF_ANA` | 1.82 V set point, required 1.71-1.89 V; TPS7A4901 from 3.8 V, 53.6 kohm/100 kohm feedback gives 1.820 V nominal and +/-2.5% overall | 75 mA allocation: VDD_REF model terms, clock fanout/oscillator, OTP allowance, VDD_ANA/HADC/TMU margin | Highest DSP clock/PLL sensitivity; one quiet regulator, VDD_ANA branch through ferrite with local bulk | First DSP rail. Enabled by Phase 3A `PGOOD_12V` after `3V8_PRE` is present; `CNR/SS=47 nF` gives about 65.8 ms nominal soft start; 10 uF input/output and 10 nF feed-forward. VDD_REF has at least 10 nF plus 100 nF and per-ball decoupling [DSP pp.18, 53; HVLDO pp.12-17]. |
| `1V35_DSP_DMC` | 1.36 V set point, required 1.283-1.418 V; TPS7A4901 from 3.8 V, 14.7 kohm/100 kohm feedback gives 1.359 V nominal and +/-2.5% overall | 50 mA allocation with DMC disabled and no external DDR; startup is rail capacitance only | Quiet/local domain | Enabled after 1.8 V valid; `CNR/SS=47 nF` gives about 65.8 ms nominal soft start. Use 10 uF input/output plus at least 22 uF domain bulk and per-ball capacitors. Discharge is controlled by the ordered shutdown and explicit bleeder/load network. |
| `3V3_SYS` | 3.30 V; required DSP 3.13-3.47 V, ADC IOVDD 1.62-3.6 V, amplifier 3.0-3.5 V; TPS62135, +/-1%; `R1=371 kohm`, `R2=100 kohm`, 0.1%, gives 3.297 V nominal | 200 mA allocation: DSP I/O, amplifier maximum 18 mA, flash maximum 80 mA write-status/chip-erase case, buffers, pullups, debug | Digital/switching rail; ferrite-isolate only local consumers, never create a different DC logic voltage | Enabled after 1.8 V valid. `CSS=10 nF`; 22 uF effective bulk. Powers DSP VDD_EXT, ADC IOVDD, amplifier VDD, flash, both LVC buffers, I2C/JTAG/UART. Active discharge and supervisor. |
| `3V3_ADC_A` | 3.30 V; ADAU1978 AVDD required 3.0-3.6 V; `TPS7A2033PDBVR` from 3.8 V, +/-1.5% | 30 mA allocation; ADC AVDD is 14 mA typical | Very sensitive; no digital loads. Optional ferrite before LDO input, solid analog return | Enabled with downstream rails. 10 uF plus 100 nF at regulator; each AVDD pin receives local 100 nF and shared local bulk per ADC guidance. |
| `2V8_MIC` | 2.80 V; microphone normal mode requires 2.3-3.0 V; `TPS7A2028PDBVR`, +/-1.5% | 5 mA allocation; four microphones require 0.92 mA maximum plus cable/transient margin | Very sensitive; star/ferrite branches to connectors | Enabled with the downstream rails after 1.8 V qualification; AFE remains off until ADC AVDD/VREF is valid. At least 10 uF controller bulk, 1 uF per connector branch, and 100 nF at each microphone as required [MIC]. |
| `5V_AFE` | 5.00 V, +/-2.5%; TPS7A4901 from protected input, 324 kohm/100 kohm feedback gives about 5.02 V nominal | 50 mA allocation; OPA165x maximum quiescent subtotal is below 28 mA for ten channels | Very sensitive; 10 nF NR/SS and feed-forward, 10 uF input/output; each op amp gets 100 nF plus local 1 uF | Enabled only after ADC AVDD/VREF is valid; disabled before ADC power-down. About 14 ms soft start. Worst allocated LDO dissipation at 13.2 V is 0.41 W. |

The `5V_AFE` 324-kohm/100-kohm pair is frozen: it gives 5.024 V nominal from the 1.185 V feedback value and 4.898-5.150 V across the regulator's stated +/-2.5% overall accuracy, inside the OPA165x 4.5-5.5 V supply range. Phase 4 still verifies trace drop and resistor/feedback-current contributions, but does not choose a new nominal rail.

### 5.2 No-DDR DMC disposition

External DDR is omitted. All ADSP-21569 `VDD_DMC` balls still connect to `1V35_DSP_DMC`; they are not grounded or left open. Both `DMC0_VREF` inputs connect to a filtered `0.5 x VDD_DMC` node (about 0.680 V at the 1.359 V nominal rail) made by equal 10.0 kohm, 0.1% resistors and 1 uF to ground. `DMC0_RZQ` retains the datasheet-required 34-ohm pulldown. All other DMC signal balls are no-connects and firmware must leave DMC disabled [DSP pp.21, 37-44, 53]. This conservative choice removes the supply-pin uncertainty without adding DDR or claiming a known zero-current DMC domain.

### 5.3 Decoupling rule

Each power pin receives a local high-frequency ceramic capacitor with the shortest possible return, and each domain receives bulk capacitance at its regulator/plane entry. The exact capacitor count follows the verified ball map. The EV-21569-SOM sheet 6 is a placement/count reference for 0.22/0.47/1 uF per-ball networks and 10 uF domain bulk, but is not copied blindly. Effective capacitance after DC-bias and tolerance, regulator stability, anti-resonance, and mounted impedance must be checked in Phase 4 [SOMSCH sheet 6; DSP p.18].

## 6. ADSP-21569 power and sequencing contract

### 6.1 Exact processor and rails

Use `ADSP-21569BBCZ10`, 1000 MHz, -40 C to +125 C junction, BC-400-3 400-ball CSP_BGA. The base design intentionally retains the 1 GHz option for compute headroom; this does not establish FxLMS feasibility [DSP pp.99-102].

| Domain | Allowed device range | Selected realized range | Supervisor nominal falling threshold |
| --- | --- | --- | --- |
| VDD_INT | 0.95-1.05 V | 0.99-1.01 V regulation target | 0.972 V (`14.3k/10.0k`) |
| VDD_EXT | 3.13-3.47 V | 3.267-3.333 V | 3.192 V (`69.8k/10.0k`) |
| VDD_REF | 1.71-1.89 V | 1.775-1.866 V | 1.752 V (`33.8k/10.0k`) |
| VDD_ANA | 1.71-1.89 V | same DC rail as VDD_REF after local filter | monitored with VDD_REF; no independent source |
| VDD_DMC | 1.283-1.418 V DDR3L range | 1.325-1.393 V | 1.300 V (`22.5k/10.0k`) |

The supervisor is powered from `3V8_PRE`, so it can qualify 1.8 V and sequence the downstream rails without a 3.3 V circular dependency. RESET1 alone pulls up to `3V8_PRE` and drives the downstream regulator EN fanout; 3.8 V is within those EN-pin limits. RESET2/3/4 and WDO pull up only to `3V3_SYS` and enter the 3.3 V safe-state/POR logic, so no DSP pin sees 3.8 V. The thresholds use `TPS386000RGPR` 0.4 V inputs and 0.1% dividers. Including the supervisor's 396-404 mV threshold range and worst-direction 0.1% resistor tolerances, their bounded falling thresholds are 0.9611-0.9829 V (core), 3.1546-3.2296 V (3.3 V I/O), 1.7318-1.7723 V (1.8 V reference/analog), and 1.2852-1.3148 V (DMC). Each range remains above the corresponding device minimum and below the selected rail's minimum realized voltage. Channels are assigned: SENSE1=1.8 V, SENSE2=1.0 V, SENSE3=1.35 V, SENSE4L=3.3 V; SENSE4H is grounded. CT pins are open for the specified 14-24 ms release delay. Outputs are open-drain with at least 10 kohm pullups [SUPV pp.4, 6-8, 23, 27-29].

### 6.2 Power-up sequence

1. Input protection ramps `12V_PROTECTED`; amplifier MUTE and STANDBY remain low through their internal pulldowns and external hardware pulldowns.
2. `3V8_PRE` starts directly from `12V_PROTECTED`. The Phase 3A TPS3760 output is pulled up to this now-valid rail; once `12V_PROTECTED` passes its bounded rising threshold, `PGOOD_12V` enables `1V8_DSP_REF_ANA`. The 1.8 V rail starts first with a 65.8 ms nominal soft start. The oscillator and fanout start from this rail while the DSP remains held in reset.
3. After supervisor channel 1 has observed valid 1.8 V for 14-24 ms, RESET1 enables `1V0_DSP_CORE`, `1V35_DSP_DMC`, `3V3_SYS`, `3V3_ADC_A`, and `2V8_MIC`. This follows EE-470's VDD_REF-before-VDD_EXT mitigation [POWER pp.1-9].
4. The 1.0 V and 3.3 V TPS62135 rails use 10 nF soft-start capacitors; both TPS7A49 DSP rails use 47 nF NR/soft-start capacitors. Each realized DSP supply ramp must be at least 100 us.
5. The LMK clock fanout starts with the 1.8 V rail. `SYS_CLKIN0` becomes valid before reset release. The MCLK translators remain disabled until 3.3 V is valid.
6. Supervisor outputs for 1.0 V, 1.35 V, and 3.3 V feed the wired hardware POR node. The two successive supervisor release intervals provide at least 28 ms after the 1.8 V threshold, exceeding the fanout's 3 ms maximum startup without an inferred clock-good signal. `SYS_HWRST` remains low until all outputs are released. At 24.576 MHz, the device minimum is only `11/24.576 MHz = 447.6 ns`; the selected delay is much longer [DSP p.53; CLKBUF].

The worst static voltage difference is less than 1.56 V (`3.333-1.775`) and an isolated reference/analog rail is at most 1.866 V. Therefore `|VDD_EXT-VDD_REF|` and `|VDD_EXT-VDD_ANA|` remain below 1.89 V for monotonic ramps even if one side is at zero. Overshoot beyond the stated regulator bounds is prohibited [DSP pp.44, 52-53; POWER].

### 6.3 Power-down and brownout sequence

On commanded shutdown: assert amplifier MUTE, command all channels Hi-Z, assert STANDBY for at least 15 ms, disable AFE/microphone power, assert ADC reset, disable serial/MCLK buffer outputs, assert DSP reset, wait at least 20 ms, then disable `3V3_SYS`, `1V35_DSP_DMC`, and `1V0_DSP_CORE`; remove 1.8 V last. Remove amplifier VDD before protected PVDD/VBAT as TI recommends.

On abrupt input loss: Phase 3A `PGOOD_12V` falls at 10.000 V nominal, bounded 9.870-10.130 V, and directly asserts the hardware safe node without waiting for firmware. That node pulls MUTE/STANDBY low, disables clock/audio buffers, asserts ADC reset and DSP reset, and disables downstream regulators before the revised eFuse UVLO opens. The 470 uF input bulk is used as control hold-up after the high-power amplifier is muted, not as audio ride-through.

TPS62135 active discharge and TPS7A20 active-discharge variants provide a defined off state. The populated schematic must include test points and DNP capacitance banks; oscilloscope verification must show every DSP domain rise and fall is at least 100 us at minimum/maximum input, 0/40 C prototype ambient, reset and maximum-load cases. A failed ramp test is a hardware stop requiring capacitor/discharge adjustment before DSP population. This is the formally approved verification method for the load-dependent falling ramps; it is not a waiver of the DSP limit.

## 7. Clock contract

### 7.1 Root and distribution

- Oscillator: `ASDLJ-D-24.576MHz-X-R-T`, 1.8 V +/-5%, -40 C to +105 C, +/-25 ppm, LVCMOS, 45-55% duty, 1 ms maximum startup, 15 pF load, 150 fs maximum integrated jitter over the stated band. Its OE is pulled up to 1.8 V so it starts with the rail [CLKOSC pp.1-4].
- Fanout: `LMK1C1103PWR`, powered from `1V8_DSP_REF_ANA`, one input and three 1.8 V LVCMOS outputs, no more than 50 ps output skew, 50 fs maximum additive jitter, 3 ns maximum propagation delay, and 3 ms maximum startup. Tie its active-high `1G` to its own 1.8 V rail through 10 kohm; do not expose this pin to the 3.8 V RESET1/enable node [CLKBUF].
- Output 0 goes through a 22-33 ohm source resistor to ADSP-21569 `SYS_CLKIN0` ball N01. `SYS_XTAL0` is left unconnected for external-clock mode [DSP pp.42, 54, 92; Phase 1 pin map].
- Outputs 1 and 2 separately feed the A ports of `SN74AXC2T245RSWR`; VCCA=1.8 V, VCCB=3.3 V, DIR1/DIR2 high for A-to-B. B1 drives ADAU1978 MCLKIN pin 7; B2 drives TAS6424E-Q1 MCLK pin 12. OE is pulled high to 1.8 V and is released low only after both rails are valid. The device's Ioff and VCC isolation prevent back-powering [CLKXLAT pp.2-5, 18-23].
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

The ADAU1978 uses the MCLK-input PLL with MCS=`011` for 24.576 MHz at 96 kHz, FS=`011`, TDM4, 32-bit slots, and remains powered down until at least 10 ms after DVDD exceeds 1.2 V and stable clocks are present; firmware polls PLL lock before enabling conversion [ADC pp.12-16, 29-31].

The amplifier uses 24.576 MHz MCLK and 12.288 MHz SCLK, so the tied/equal-clock special case does not apply. `BCLK_INV=0`. Loss of valid clock drives its outputs Hi-Z; clocks alone never authorize PLAY [AMPE pp.11, 22-25, 34, 58].

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

Use one `SN74LVC244APWR` at 3.3 V. Allocate channels so the BCLK and FSYNC source inputs each drive two independent outputs (ADC and amplifier), DSP TDM data drives the amplifier, and ADC data drives the DSP. Keep clock/data in the same package and source-terminate every driven trace with 22-33 ohms. Both active-low OE banks have 10 kohm pullups to 3.3 V and are pulled low by a DSP-controlled NMOS only after clock and endpoint configuration; `PGOOD_12V` or supervisor fault overrides the NMOS and disables outputs.

Worst-case input margins into the buffer are:

- DSP high: `2.4-2.0=0.4 V`; DSP low: `0.8-0.4=0.4 V`;
- ADC high at minimum 3.267 V IOVDD: `(3.267-0.6)-2.0=0.667 V`; ADC low: `0.8-0.4=0.4 V`.

At light CMOS load the LVC output guarantees at -40 C to +125 C `VOH >= VCC-0.3`; with 3.267 V minimum this is 2.967 V. The worst receiver requirement is `0.7 x 3.333=2.333 V`, leaving 0.634 V. Its `VOL <=0.3 V` leaves at least `0.3 x 3.267-0.3=0.680 V` [LVBUF pp.6-8; ADC pp.5-8; AMPE pp.7-11; DSP pp.44-48].

### 8.2 MCLK, control, memory, and debug

| Interface | Voltage/direction strategy | Contract |
| --- | --- | --- |
| Clock fanout to DSP | Direct 1.8 V | LMK output to SYS_CLKIN0; worst high margin is `0.8x1.71 - 0.65x1.89 = 0.1395 V`, low margin is `0.35x1.71 - 0.2x1.89 = 0.2205 V`. Keep load 5 pF and edge under device limit. |
| MCLK to ADC/amplifier | 1.8-to-3.3 V AXC translation | One channel per endpoint; A-to-B, OE high during invalid power. Light-load output margins exceed 0.8 V high and low from CLKXLAT and endpoint thresholds. |
| I2C/TWI | Direct open-drain on common `3V3_SYS` | DSP master; ADC address 0x11, amplifier address 0x6A. Use 2.2 kohm pullups and limit total bus capacitance to 150 pF for 400 kHz; expose test points. No hot-plug. At the bounded rail, static HIGH margin is at least `3.267-max(2.0, 0.7x3.333)=0.934 V`; with `VOL<=0.4 V`, LOW margin is at least `min(0.8, 0.3x3.267)-0.4=0.4 V`. Pullup current is at most 1.52 mA. |
| SPI2 boot flash | Buffered 3.3 V, single-SPI | A second `SN74LVC244APWR` buffers DSP CLK/MOSI/CS toward the flash and flash MISO toward the DSP. Both sides share `3V3_SYS`; the buffer converts the DSP's guaranteed 2.4/0.4 V outputs into the rail-relative levels required by the flash and prevents powered-off injection. Buffer outputs leave at least 0.634 V HIGH and 0.5 V LOW margin at either endpoint; flash MISO into the buffer leaves at least `(3.267-0.2)-2.0=1.067 V` HIGH and `0.8-0.2=0.6 V` LOW margin [FLASH p.171; LVBUF]. Its OEs are pulled low/enabled whenever 3.3 V is valid, independent of firmware. Use 22-33-ohm source resistors after the active driver and a 10-kohm CE pullup at the flash. Quad data pins are not part of the boot contract. |
| JTAG | Direct 3.3 V target domain | Use the official EV-21569-SOM 10-pin mapping below. The header carries target reference; the probe must not drive an unpowered target. TRST has the EE-68-required 4.7 kohm pulldown [SOMSCH sheet 9; JTAG p.6]. |
| UART0 | Direct 3.3 V CMOS | Logic-level only. External USB, RS-232, or RS-485 equipment requires an external adapter/transceiver. |
| Reset/mute/standby | Hardware-dominant open drain | ADC reset and system reset use destination-domain pullups with supervisor/fault pull-down assertion. Amplifier MUTE/STANDBY remain low by internal/external pulldowns; their controlled pullups are released only when both the hardware-safe latch and DSP permit. The DSP never has to source a marginal rail-relative HIGH. |
| AFE power enable | Buffered 3.3 V to TPS7A49 EN | Allocate one otherwise spare channel of the always-enabled boot `SN74LVC244A` to `AFE_EN_CMD`, with a 100-kohm EN pulldown and hardware-fault open-drain override after the buffer. Worst margins are at least `2.967-2.1=0.867 V` HIGH and `0.4-0.3=0.1 V` LOW; default is off. |

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

Use two `OPA1654AIPW` quad op amps for the eight signal legs and one `OPA1652AIDR` dual op amp for VREF buffering. Power all from `5V_AFE`. OPA165x is specified from 4.5 V, has 4.5 nV/sqrt(Hz) noise at 1 kHz, 18 MHz gain bandwidth, 10 V/us slew rate, input common-mode from 0.5 V to 3.0 V on a 5 V supply, and guaranteed output from 0.8 V to 4.2 V at 2 kohm load [AFE pp.1, 5-7, 14-24].

For each IM73A135 output leg:

1. Connector protection footprint with no more than 5 pF added capacitance and a 100-ohm series RF resistor.
2. 4.7 uF nominal nonpolar or correctly biased low-leakage coupling capacitor; the design must retain at least 2.2 uF effective capacitance.
3. 100 kohm bias resistor to buffered ADAU1978 `VREF` (nominal 1.5 V).
4. OPA1654 noninverting stage: `Rg=1.00 kohm` to VCM and `Rf=2.80 kohm`, both 0.1%, gain `1+2.80/1.00=3.80 V/V`.
5. 47-ohm output isolation resistor to the corresponding ADAU1978 AIN pin. A 1 nF C0G differential capacitor across each ADC input pair is fitted for RF/charge-kick isolation; do not add large single-ended capacitors that unbalance CMRR.

The microphone sees approximately 100 kohm per output leg, exceeding its 25 kohm minimum, and connector/protection capacitance must keep each microphone output below the 100 pF maximum [MIC pp.8-10]. VREF is buffered because the ADC VREF pin is a 20 kohm-class reference output, not a rail. The unused OPA1652 half is configured as a unity follower at VCM and not left open [ADC pp.14-16].

### 9.3 Gain and headroom

IM73A135 sensitivity of -38 dBV/Pa gives `12.589 mVrms` differential at 94 dBSPL. At 120 dBSPL, 26 dB higher:

`Vin = 12.589 mV x 10^(26/20) = 0.25119 Vrms`.

After gain 3.8, `VADC = 0.9545 Vrms differential`. Relative to the ADAU1978 2 Vrms differential full scale this leaves:

`20 log10(2/0.9545) = 6.425 dB` ADC headroom.

The ADC full-scale equivalent is about 126.4 dBSPL, still 5.6 dB below the microphone's 132 dBSPL 1% THD acoustic overload point. Each op-amp output moves only 0.675 V peak about 1.5 V, or 0.825-2.175 V, inside the OPA165x guaranteed 0.8-4.2 V output range [MIC pp.4-8; ADC pp.3-5; AFE pp.5-7].

### 9.4 Low-frequency response, noise, and aliasing

The coupling high-pass corner per leg is:

- nominal: `1/(2pi x 100k x 4.7uF) = 0.339 Hz`;
- worst effective capacitance: `1/(2pi x 100k x 2.2uF) = 0.723 Hz`.

At 20 Hz, the worst pole contributes about 0.006 dB loss, 2.07 degrees phase lead, and 0.287 ms group delay. These terms must remain in the later ANC loop model; they are not “zero.” ADC register 0x1A channel HPF bits remain zero because the published enabled cutoff is conflicting. TAS6424E register 0x01 bit 7 bypasses its digital HPF [ADC pp.4, 14, 42; AMPE pp.25, 40].

A first-order 300 K resistor/op-amp noise screen with two uncorrelated legs gives about 1.14 uVrms differential input-referred over 20 Hz-20 kHz. Using the 1.5 uV AFE allocation, the microphone's approximately 2.82 uVrms noise, and about 7.1 uVrms ADC input noise divided by gain 3.8 gives `sqrt(2.82^2+1.5^2+(7.1/3.8)^2)=3.70 uVrms` system input-referred. This is a calculation target, not a guaranteed built-board number. Phase 4 must simulate input noise and CMRR; bench validation must use shorted/balanced inputs and a microphone-equivalent source.

The ADAU1978's internal switched-capacitor antialias/decimation filter remains active. The 47-ohm/1 nF differential network has an approximate MHz-range RF pole and does not replace the ADC filter or alter the 20 Hz-20 kHz contract. No external audio-band low-pass is added because it would add unbudgeted ANC phase.

### 9.5 Powered-off and protection behavior

AC coupling prevents the microphone's 1.35 V DC bias from defining ADC common mode. ADC AVDD and VREF must be valid before `5V_AFE` is enabled; AFE is disabled before ADC reset/power removal. `2V8_MIC` is disabled with AFE on shutdown. The 47-ohm output resistors limit abnormal current, but sequencing—not clamp-diode conduction—is the primary back-drive prevention. External microphone cables use shield/chassis termination at the connector edge; cable shields do not carry signal return.

## 10. Reset, supervision, and startup architecture

Use `TPS386000RGPR` plus wired open-drain safe-state logic. A supervisor is required because software cannot guarantee rail validity, power-failure response, or the five-domain reset condition.

### 10.1 Normal startup state machine

1. **Power applied:** TPS26630 validates voltage/polarity and limits inrush; the Phase 3A TPS3760 holds `PGOOD_12V` low. Amplifier MUTE/STANDBY and buffer OEs remain in their passive safe states.
2. **Regulators start:** `3V8_PRE` starts from the protected rail; valid `PGOOD_12V` then enables 1.8 V; the rail supervisor subsequently enables the remaining DSP/system rails as section 6 defines.
3. **Clocks valid:** oscillator and LMK fanout settle; DSP clock output is enabled. MCLK translation waits for both 1.8 V and 3.3 V.
4. **DSP reset:** supervisor releases `SYS_HWRST` only after every monitored rail and clock delay is valid. Any JTAG halt/reset forces the external audio-safe latch.
5. **DSP boot:** ROM boots SPI2 flash. Earliest code configures safe GPIO, watchdog, CGU, SRU/SPORT, DMA, and TWI; amplifier remains in STANDBY.
6. **ADC initialization:** release PD/RST, ensure MCLK/BCLK/FSYNC, wait at least 10 ms after DVDD threshold, configure 96 kHz/TDM4/MCLK PLL/HPF-off, poll PLL lock, then power up channels.
7. **Amplifier initialization:** after its 12 ms I2C startup, write/read back phase, TDM, gain, HPF, OC, and warning settings; run or explicitly bypass diagnostics under the firmware test policy. Outputs remain Hi-Z.
8. **Mute release:** wait for the microphone's 30 ms maximum startup, AFE/ADC DC settling, valid DMA frames, valid coefficients, and no FAULT/WARN; enter MUTE state, ramp volume, then PLAY.
9. **Normal operation:** hardware watchdog, eFuse FLT, `PGOOD_12V`, amplifier FAULT/WARN, ADC PLL state, rail test points, and clipping counters remain monitored.

### 10.2 Fault behavior

| Event | Required response |
| --- | --- |
| Brownout/OVP/eFuse fault | Hardware asserts amplifier MUTE/STANDBY, disables audio/MCLK buffer OEs, resets DSP/ADC, and latches restart. No automatic PLAY. |
| DSP reset/watchdog/JTAG halt | Same audio-safe latch; amplifier state cannot remain PLAY solely because its last I2C command did. |
| Missing MCLK/SCLK/FSYNC | Amplifier enters Hi-Z per device behavior; firmware records fault and requires a full clock/PLL/configuration recheck before PLAY. |
| Amplifier FAULT | Hardware MUTE immediately; DSP reads fault registers only after safe state. Repeated OC/thermal/DC fault requires user/service clear or power cycle. |
| ADC PLL unlock/data framing error | Maintain amplifier MUTE, reset/reinitialize ADC and SPORT, discard buffers. |
| Commanded shutdown | Ordered sequence in section 6.3; STANDBY held low at least 15 ms before amplifier supplies disappear. |

TPS386000 watchdog timeout is 450-750 ms. It is a catastrophic-software supervisor, not the real-time ANC deadline monitor; the DSP's internal watchdog and audio-frame deadline logic must react faster. WDO is wired into the safe-state/reset logic [SUPV pp.4, 7-8, 23-29].

## 11. Boot, memory, and debug architecture

| Item | Frozen contract |
| --- | --- |
| Boot mode | `SYS_BMODE=001`, SPI2 flash master boot [DSP p.18; BOOT; HRM ch.40]. |
| Flash | `IS25LP512M-RMLE`, 512 Mbit/64 MB, 2.3-3.6 V, 16-pin SOIC, dedicated RESET, extended -40 C to +105 C [FLASH pp.2, 7-9, 170-185]. |
| Capacity | Minimum PCB design capacity 16 MB; selected 64 MB supports two firmware images, boot metadata, coefficients, calibration, and logs. Exact partition/authentication policy remains `UNKNOWN`. |
| Interface | Dedicated buffered single-SPI2: CLK PA04/R01, MISO PA00/N03, MOSI PA01/P03, CS PA05/T02. A dedicated `SN74LVC244APWR` provides the fixed directions in section 8.2; use 22-33-ohm source resistors after each driver and a 10-kohm CE pullup at the flash. IO2/WP and IO3/HOLD use their datasheet-safe 10-kohm defaults and are not routed as quad data. One spare buffer channel implements `AFE_EN_CMD`; remaining spare inputs are tied to a defined level. CE remains high until at least 300 us after flash VCC reaches minimum [FLASH p.177]. |
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

- Major parts: three TPS62135 converters (`3V8_PRE`, `1V0_DSP_CORE`, `3V3_SYS`); three TPS7A4901 (`1V8_DSP_REF_ANA`, `1V35_DSP_DMC`, `5V_AFE`); TPS7A2033P, TPS7A2028P; TPS386000; open-drain safe-state gates.
- Rails: every rail in section 5.
- Critical values: buck feedback pairs 442 k/100 k, 42.7 k/100 k, and 371 k/100 k; 10 nF buck soft starts; 47 nF DSP-rail and 10 nF AFE TPS7A49 NR/SS capacitors; supervisor divider/CT values in section 6; DNP capacitance banks and all rail test points.
- Interfaces/dependencies: `PGOOD_12V`, regulator EN/PG, POR, ADC reset, buffer OEs, amplifier MUTE/STANDBY.
- Evidence: BUCK, LDO, HVLDO, SUPV, DSP pp.44, 52-53, POWER.

### Sheet 3 - Microphones / AFE

- Major parts: four IM73A135V01 microphone connectors/modules, two OPA1654AIPW, one OPA1652AIDR, low-capacitance protection footprints.
- Rails: `2V8_MIC`, `5V_AFE`, buffered 1.5 V VCM, analog ground reference.
- Critical values: 100 ohm input RF, 4.7 uF coupling (2.2 uF effective minimum), 100 k bias, 1.00 k/2.80 k 0.1% gain, 47 ohm ADC drive, 1 nF C0G differential.
- Interfaces/dependencies: ADC VREF and AIN1-4; AFE enable only after ADC/VREF; four shields to entry chassis strategy.
- Evidence: MIC pp.4-10, ADC pp.14-16, AFE.

### Sheet 4 - ADAU1978 ADC

- Major part: `ADAU1978WBCPZ`.
- Rails: AVDD=`3V3_ADC_A`, IOVDD=`3V3_SYS`, internal DVDD decoupling, VREF/PLL filter.
- Interfaces: AIN1-4 from Sheet 3; MCLKIN pin 7 from clock translator; LRCLK pin 15/BCLK pin 16 from buffer; SDATAOUT1 pin 13 to buffer; I2C pins 17/18; PD/RST pin 6.
- Critical configuration: I2C address 0x11; 96 kHz, MCLK PLL MCS=011, TDM4/32-bit slots, one-bit delay, HPFs off; SDATAOUT2 unused per documented pin policy.
- Dependencies: 10 ms clock/DVDD delay and PLL-lock poll before channel power-up.
- Evidence: ADC pp.3-16, 21-31, 40-44.

### Sheet 5 - ADSP-21569 DSP / boot / debug / clocks

- Major parts: ADSP-21569BBCZ10, ASDLJ oscillator, LMK1C1103, SN74AXC2T245, one SN74LVC244A for audio and one SN74LVC244A for boot SPI, IS25LP512M-RMLE, JTAG/UART/strap headers.
- Rails: all five DSP domains, 1.8 V clock, 3.3 V flash/debug.
- Interfaces: fixed DAI0 pins from section 7; SPI2 pins, UART0 pins, TWI, all POR/watchdog/fault signals.
- Critical configuration: SYS_BMODE=001; 24.576 MHz CGU contract; SPORT0A RX/SPORT0B TX; no DDR, powered DMC domain and half-rail VREF; TRST 4.7 k pulldown.
- Dependencies: Sheet 2 POR and safe-state; Sheet 4/6 control and audio; do not release buffer OEs from passive safe state until boot initialization completes.
- Evidence: DSP, POWER, HRM, BOOT, ANOM, SOM/SOMSCH, JTAG, CLKOSC, CLKBUF, CLKXLAT, FLASH.

### Sheet 6 - TAS6424E-Q1 amplifier

- Major parts: TAS6424EQDKQRQ1, four pairs of output inductors, shunt/EMI capacitors, bootstrap/GVDD/rail capacitors, hardware mute/standby/fault network.
- Rails: `12V_PROTECTED` PVDD/VBAT and `3V3_SYS` VDD.
- Interfaces: MCLK pin 12; buffered SCLK pin 13, FSYNC pin 14, SDIN1 pin 15; SDIN2 pin 16 grounded; I2C 20/21; control/status 24-27; eight BTL outputs.
- Critical configuration: 0x03=0x86, 0x01=0xE0, 0x02 low bits=10, 0x28=0x2A, 0x26=0x40; gain level 1; four BTL channels; HPF bypass; level-1 OC; hardware remains Hi-Z until checks pass.
- Dependencies: grounded heatsink, 470 uF bulk, valid clocks, 12 ms I2C delay, 15 ms standby shutdown.
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
4. Implement every rail and every ADSP supply ball; do not omit or merge `VDD_DMC`; do not add DDR.
5. Preserve VDD_REF-before-VDD_EXT sequencing, the 100 us minimum rail-rise/fall requirement, all-rail reset monitoring, and 1.8 V-last ordered shutdown.
6. Preserve the exact 24.576 MHz oscillator/fanout/translator tree, one load per fanout output, and DAI0_PIN01-04 allocation.
7. Preserve the opposite-edge TDM timing, LVC buffered audio paths, passive-disabled OEs, and test points. Before schematic review closes, run the loaded timing method in section 7.3.
8. Preserve AFE gain 3.8, sub-0.73 Hz worst coupling pole, buffered ADC VREF common mode, and HPF-off/bypass policy. Provide resistor/capacitor tuning footprints without changing topology.
9. Preserve active-low annotation and passive-safe defaults for reset, MUTE, STANDBY, OEs, flash CE/RESET, and boot straps.
10. Verify every symbol pin number against the cited official document; third-party symbols are not accepted without an independent pin table. Run ERC and retain outputs under `validation/`.

The following analyses are required during Phase 4 but are not invitations to invent architecture: regulator inductor/capacitor part selection against the stated electrical limits; full populated-BOM rail loads; tolerance/Monte Carlo for protection/supervisor dividers and AFE poles/gain; input/clock/audio IBIS or equivalent timing; reset/power transient simulation; op-amp stability/noise; and symbol-pin audit.

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
| AFE contract closure | **ACCEPTED PROVISIONALLY** | Bounded 20 Hz-1 kHz ANC development band, 120 dBSPL crest-inclusive input, gain/headroom/noise/pole calculations, exact OPA165x topology/rails, and powered-off sequence make the schematic deterministic. |
| Clock implementation closure | **RESOLVED** | Exact oscillator, fanout, translators, rails, loading rule, DAI/SPORT allocation, clock arithmetic, timing margins, safe OE, and formal ADC-hold validation method are defined. |
| Power and sequencing closure | **ACCEPTED PROVISIONALLY** | Input envelope, all rail sources/loads, DMC disposition, supervisor thresholds, reset, startup/shutdown/back-drive behavior and ramp validation are defined. Later passive tuning does not alter the architecture. |
| Conditional direct-I/O closure | **RESOLVED** | Direct-drive assumption is replaced by qualified buffering/translation; common-domain buses have explicit voltage limits and margins. |

There are **no remaining blockers to schematic entry** within the Phase 3 prototype bounds. There are substantial blockers to PCB release, acoustic operation, final thermal claims, and product compliance; they are listed in sections 15-16 and may not be treated as completed work.

## 18. Phase 4 recommendation

Proceed only to a separately authorized Phase 4 schematic implementation. Phase 4 may create the hierarchical schematic described here, verify every symbol pin, complete component/passive/tolerance and populated-load calculations, run ERC, and execute the pre-PCB timing/power/AFE checks in section 15. It is not authorization for PCB placement, routing, production release, or a claim that ANC performance has been validated.

PHASE 3: PASS
