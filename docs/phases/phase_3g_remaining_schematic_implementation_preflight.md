# PHASE 3G — Remaining schematic implementation preflight

Date: 2026-09-14

Scope: documentary correction of the microphone/AFE/isolation contract and a focused implementation-readiness audit of Sheets 3 through 7. No KiCad file was created or modified. Phase 4C was not resumed.

This document supersedes the microphone-isolation count and OPA165x/gain/headroom portions of Phase 3 §5.1, §9, §14, §16 and Phase 3E §7. It does not reopen the passed Phase 4A/4B implementation except that the later Sheet 2 correction must replace the four incomplete microphone isolation devices and update the affected hierarchy pins before Sheet 3 is connected.

## 1. Evidence used

Evidence IDs are from the [component evidence index](../evidence/component_evidence_index.md).

- `MIC`: IM73A135V01 V1.20, pp.6-10: differential sensitivity, frequency-response limits, 100 pF output-load limits, supply, output dc level/impedance, and startup.
- `ADC`: ADAU1978 Rev.B, pp.3-9, 12-18, 21-22, 27-31 and 43: input range/common mode, exact pins, supplies/decoupling, PLL filter/startup, serial/control ports, register fields and typical application.
- `ANISO`: TMUX2821 SCDS488, pp.1-8, 18-25: dual SPST pin map, signal/supply ranges, leakage, powered-off isolation, bandwidth and audio performance.
- `MICISO3G`: TMUX1574 SCDS391C, Rev.C, pp.1, 3-8 and 22-26: quad SPDT pin map, 1.5-5.5 V operation, 0 V to `2 x VDD` signal range, 3.6 V powered-off protection, fail-safe controls, maximum capacitance/leakage/RON and truth table.
- `AFE3G`: OPA192/2192/4192 SBOS620E, Rev.E, pp.4-11 and current orderable addendum: exact packages/pins, 4.5-8 V electrical table, input range/noise/offset, and guaranteed open-loop output regions at 2 kohm and 10 kohm.
- `VREFBUF3G`: OPA320 SBOS513F, Rev.F, pp.4 and 6-9 plus current orderable addendum: exact SOT-23 pin map, 1.8-5.5 V operation, RRIO limits, offset/drift, output/load limits and active orderable.
- `DSP`, `POWER`, `HRM`, `BOOT`, `ANOM`, `SOMSCH`, `JTAG`, `FLASH`, `AMPE`, `AMPEVM`, `LVBUF`, `CLKOSC`, `CLKBUF`, and `CLKXLAT`: only the already indexed sections directly needed for the sheet preflight.

## 2. Phase 4C blocker disposition

| Phase 4C finding | Disposition | Status |
| --- | --- | --- |
| Four differential microphones need eight conductors, but the microphone boundary switched only four paths | Replace the four microphone-side `TMUX2821DSGR` packages with four `TMUX1574PWR` quad packages. Two packages are powered from `2V8_MIC`, two from `5V_AFE`; every one of the eight legs passes through one device in each adjacent power domain. | **RESOLVED** |
| The former 0.8 V OPA165x boundary was not guaranteed at 5 V and the old 3.8 V/V gain demanded about 0.7116 V at the low output | Replace the signal amplifiers with two `OPA4192IPWR`, replace the AFE VCM buffer with `OPA2192IDR`, add `OPA320AIDBVR` at the ADC VREF source, and reduce each leg's gain to the exact resistor-defined value below. The applicable low-supply guaranteed output region is used. | **RESOLVED** |
| Prior calculation considered only the 1 kHz sensitivity | Include the microphone's guaranteed/limited +9 dB normalized response at 15 kHz in the full 20 Hz-20 kHz electrical-range calculation. | **RESOLVED** |

The result deliberately does not retain the 0.8 V boundary. The new lower output boundary is **0.6 V**, taken from the OPAx192 4.5-8 V open-loop-gain condition at `RL=2 kohm` over -40 C to +125 C. The calculated minimum is 0.651 V after an explicit 2 mV dc-error allocation.

## 3. Corrected microphone-to-ADC contract

### 3.1 Physical microphone ownership and polarity

The four IM73A135V01 microphones are on external microphone modules, not duplicated as main-controller PCB components. Sheet 7 owns the four five-pin board connectors and their connector-edge protection/100-ohm resistors. Each external module owns its IM73A135V01 and required local 100 nF VDD capacitor. Sheet 3 begins at the already-isolated differential inputs and owns coupling, bias, gain and ADC-drive circuitry.

IM73A135V01 pin 1 `OUT+` maps without inversion to ADAU1978 `AINxP`; pin 3 `OUT-` maps without inversion to `AINxN`. The complete channel mapping is:

| Channel | External microphone | Sheet 7 after edge network | Sheet 2 after paired-domain isolation | Sheet 3 AFE output | Sheet 2 after paired-domain isolation | ADAU1978 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 + | pin 1 `OUT+` | `MIC1_P_RAW` | `MIC1_P_ISO` | `AFE1_P_RAW` | `ADC1_P_ISO` | pin 33 `AIN1P` |
| 1 - | pin 3 `OUT-` | `MIC1_N_RAW` | `MIC1_N_ISO` | `AFE1_N_RAW` | `ADC1_N_ISO` | pin 32 `AIN1N` |
| 2 + | pin 1 `OUT+` | `MIC2_P_RAW` | `MIC2_P_ISO` | `AFE2_P_RAW` | `ADC2_P_ISO` | pin 35 `AIN2P` |
| 2 - | pin 3 `OUT-` | `MIC2_N_RAW` | `MIC2_N_ISO` | `AFE2_N_RAW` | `ADC2_N_ISO` | pin 34 `AIN2N` |
| 3 + | pin 1 `OUT+` | `MIC3_P_RAW` | `MIC3_P_ISO` | `AFE3_P_RAW` | `ADC3_P_ISO` | pin 37 `AIN3P` |
| 3 - | pin 3 `OUT-` | `MIC3_N_RAW` | `MIC3_N_ISO` | `AFE3_N_RAW` | `ADC3_N_ISO` | pin 36 `AIN3N` |
| 4 + | pin 1 `OUT+` | `MIC4_P_RAW` | `MIC4_P_ISO` | `AFE4_P_RAW` | `ADC4_P_ISO` | pin 39 `AIN4P` |
| 4 - | pin 3 `OUT-` | `MIC4_N_RAW` | `MIC4_N_ISO` | `AFE4_N_RAW` | `ADC4_N_ISO` | pin 38 `AIN4N` |

Each microphone therefore requires exactly **two analog conductors** and the four-channel system requires exactly **eight independently preserved signal legs**. Shields and `MIC_GND` are returns/mechanical conductors, not substitutes for either differential leg.

### 3.2 Exact microphone-boundary isolation

Use four exact `TMUX1574PWR` TSSOP-16 packages:

- two packages powered from `2V8_MIC`, one handling channels 1/2 (`P`, `N`, `P`, `N`) and one handling channels 3/4;
- two corresponding packages powered from `5V_AFE`;
- cascade one selected switch in the 2.8 V device and one selected switch in the 5 V device for every leg;
- tie `EN` pin 15 and `SEL` pin 1 directly to ground, selecting `SxA <-> Dx`; ground every unused `SxB` pin as TI requires; and fit 0.1 uF from pin 16 VDD to pin 8 GND at each package;
- use the `S1A/D1`, `S2A/D2`, `S3A/D3`, and `S4A/D4` pairs in that order. Do not parallel channels.

This implements **16 independently operating series switch elements** for the microphone boundary: eight legs times two adjacent power domains. It uses four IC packages, not four signal paths.

The AFE-to-ADC boundary retains eight `TMUX2821DSGR` packages, using both SPST channels in every device: four powered from `5V_AFE` and four from `3V3_ADC_A`, for 16 series switch elements across eight legs. The VREF boundary retains two more `TMUX2821DSGR`, one powered from `3V3_ADC_A` and one from `5V_AFE`, using one SPST channel in each; disable the unused channels as previously specified.

The corrected isolation population is therefore:

| Boundary | Signal legs | Series elements per leg | Used switch elements | Packages |
| --- | ---: | ---: | ---: | ---: |
| Microphone to AFE | 8 | 2 | 16 | 4 x `TMUX1574PWR` |
| AFE to ADC | 8 | 2 | 16 | 8 x `TMUX2821DSGR` |
| ADC VREF to AFE VCM | 1 | 2 | 2 | 2 x `TMUX2821DSGR` |
| **Total** | **17** | — | **34** | **14 packages** |

This preserves the former total package count only because each replacement microphone device has four independently routed channels. A four-package count must never again be interpreted as four microphone signal legs.

### 3.3 Isolation electrical checks

| Property | Corrected contract and conclusion |
| --- | --- |
| Signal range/common mode | Microphone-boundary signals remain approximately 1.35 V dc with a worst calculated 0.788-1.912 V leg range. TMUX1574 permits 0 V to `2 x VDD` (5.5 V maximum) while powered and 0-3.6 V while powered off. AFE/ADC TMUX2821 paths remain within their -5.5 V to +5.5 V range. **PASS**. |
| Polarity | Every `P` leg stays on its own channel and reaches `AINxP`; every `N` leg reaches `AINxN`. All AFE stages are noninverting. **PASS**. |
| Powered/unpowered behavior | Both switch families specify powered-off high impedance. Loss of either adjacent rail opens at least one series element; neither the microphone, AFE, ADC input nor VREF is used to back-power an absent domain. **PASS**. |
| Off leakage | TMUX1574 powered-off I/O leakage is at most +/-2 uA over its specified 0-3.6 V condition; powered off-channel leakage is at most +/-100 nA. TMUX2821 retains its indexed maximum leakage limits. Leakage cannot authorize operation and is included in off-state bench checks. **PASS for architecture; measurement retained**. |
| Capacitance | TMUX1574 specifies at most 12 pF on-state and 6 pF off-state source/drain capacitance, removing the TMUX2821 70 pF typical off-capacitance concern at the microphone. The complete assembled `Ca`, `Cb`, and `Cd` load at each microphone must each remain no more than 100 pF: allocate no more than 24 pF to the two switches, 5 pF to protection, 6 pF to controller parasitics, and 65 pF to connector/cable/module parasitics. **Schematic-ready; extracted/bench capacitance is a physical validation**. |
| Bandwidth | TMUX1574 specifies 2 GHz typical bandwidth into its test load and TMUX2821 specifies 100 MHz typical; both are far above 20 kHz. The exact switched AFE still requires AC simulation. **PASS for architecture**. |
| RON/distortion/noise | Two TMUX1574 elements contribute at most 9 ohms total RON and 3.6 ohms summed flatness. Against the 100 kohm AFE input bias path this is negligible gain modulation; their added thermal-noise density is below 0.4 nV/sqrt(Hz). No guaranteed system THD is inferred from those figures; simulation and a 20 Hz-20 kHz two-tone/THD bench test remain mandatory. **PASS for schematic; physical performance open**. |
| Control/startup | The microphone switches are connected only when their own rails are valid: `EN=SEL=0` selects the A path when powered, and powered-off protection isolates when either rail is absent. The rails still share `ANALOG_PWR_EN`; no new control signal or circular dependency is introduced. **PASS**. |

### 3.4 Corrected VREF/common-mode path

Do not connect the high-impedance switched path directly to ADAU1978 VREF. Its approximately 20 kohm typical output impedance and the switch leakage would make the previous error budget indefensible.

On Sheet 4, buffer ADAU1978 pin 2 VREF locally with one exact `OPA320AIDBVR` powered from `3V3_ADC_A`: pin 5 to supply, pin 2 to analog ground, pin 3 to VREF, and pin 4 tied to pin 1 as a unity follower. Use the required 10 uF plus 100 nF directly at ADC VREF and 100 nF at the OPA320 supply. Route the OPA320 output as `ADC_VREF_RAW` through the paired TMUX2821 devices on Sheet 2. On Sheet 3, buffer `AFE_VCM_ISO` again with one channel of exact `OPA2192IDR` powered from `5V_AFE`; configure the unused second channel as a unity follower at the same VCM rather than leaving inputs open.

The OPA320 input load is sub-nanoampere at 25 C and bounded in the datasheet across temperature; the ADC sees the locally decoupled high-impedance buffer input rather than switch leakage or eight AFE bias networks. Allocate +/-1 mV total dc error to the complete VREF-copy chain for the headroom calculation. The actual production calibration records the measured VCM.

### 3.5 Exact AFE topology and parts

Use two `OPA4192IPWR` quad amplifiers for the eight signal legs and one `OPA2192IDR` for AFE VCM buffering. All are powered from `5V_AFE`, with 100 nF at every package and 1 uF local bulk per two packages.

For every `MICn_[P/N]_ISO` leg:

1. Fit 4.7 uF nominal nonpolar or correctly biased low-leakage coupling capacitance, retaining at least 2.2 uF effective.
2. Fit 100 kohm, 0.1%, low-noise thin-film bias from the post-coupling node to `AFE_VCM`.
3. Use a noninverting OPA4192 stage with `Rg=2.80 kohm` to `AFE_VCM` and `Rf=1.27 kohm`, both 0.1% thin-film.
4. Fit 47.0 ohms, 0.1%, thin-film in series at the op-amp output.
5. On Sheet 4, retain one 1 nF C0G differential capacitor across each post-isolation ADC input pair and place it at the ADC; do not fit unequal single-ended audio-band capacitors.

Nominal gain is `1 + 1.27/2.80 = 1.453571 V/V`; the independent 0.1% resistor corners bound it to approximately 1.452665-1.454479 V/V. The feedback branch is at least 4.066 kohm. With the ADAU1978's 14.3 kohm typical per-input resistance, the small-signal effective output load is approximately 3.17 kohm. At the worst calculated waveform the larger source/sink demand is approximately 0.258 mA, below the approximately 0.409 mA corresponding to the OPAx192 2 kohm output test at the 0.817 V excursion. Phase 4C must still verify the populated macromodel and dc operating point because the ADC input resistance is published as typical, not a guaranteed minimum.

### 3.6 Worst-case range and headroom

The complete full-band screen uses the direction that maximizes amplitude:

- microphone sensitivity: -37 dBV/Pa maximum;
- acoustic level: 120 dBSPL, 26 dB above 94 dBSPL;
- microphone normalized response: +9 dB maximum at 15 kHz;
- gain: 1.454479 V/V maximum;
- VREF: 1.47 V minimum and 1.54 V maximum (not 1.53 V);
- common-mode copy error: +/-1 mV;
- signal-stage offset/bias allocation: +/-1 mV per leg;
- `5V_AFE`: 4.858943-5.157889 V.

Calculations:

`Vin,1k = 10^(-37/20) x 10^(26/20) = 0.281838 Vrms differential`

`Vin,max-band = 0.281838 x 10^(9/20) = 0.794328 Vrms differential`

`VADC,max-band = 0.794328 x 1.454479 = 1.155334 Vrms differential`

`Vleg,pk = 1.155334 / sqrt(2) = 0.816945 V`

`VOUT,min = 1.47 - 0.816945 - 0.002 = 0.651055 V`

`VOUT,max = 1.54 + 0.816945 + 0.002 = 2.358945 V`

OPAx192's applicable low-supply, full-temperature 2 kohm open-loop-gain region is 0.6 V to `V+ - 0.6 V`. At the minimum AFE supply, the upper bound is 4.258943 V. The required 0.651055-2.358945 V range leaves **51.055 mV low-side** and **1.900 V high-side** margin. Its common-mode input range includes 1.47-1.54 V, and that common mode lies in the lower-noise input region at the minimum 5 V rail. **The op-amp headroom conflict is closed using guaranteed low-supply limits.**

Against the ADAU1978's 2 Vrms typical differential full scale, the full-band amplitude margin is `20 log10(2/1.155334) = 4.766 dB`; at 1 kHz it is 13.766 dB. Because the ADC specifies full-scale input as typical rather than a production minimum, Phase 4C must measure clipping onset across prototypes and temperature. That is a physical validation item, not an unresolved schematic choice.

The coupling poles remain 0.339 Hz nominal and 0.723 Hz at 2.2 uF effective with the 100 kohm bias. A first-order white-noise screen using OPAx192 5.5 nV/sqrt(Hz), a 359-ohm screening source-series value (250-ohm typical microphone output, 100 ohms RF and 9 ohms maximum switch resistance), and `Rf || Rg = 873.7 ohms` gives approximately **1.423 uVrms differential input-referred over 20 Hz-20 kHz**. This remains inside the 1.5 uVrms AFE screening allocation, but it is not a guaranteed built-board noise result.

## 4. Remaining-sheet implementation preflight

### 4.1 Sheet 3 — microphones / AFE

| Audit item | Frozen implementation | Result |
| --- | --- | --- |
| Channel/conductor count | Four differential channels, eight independently named legs; `P` and `N` never share a switch channel. | PASS |
| Isolation count/location | Microphone and AFE/ADC isolation devices are on Sheet 2. Sheet 3 receives eight `MICn_[P/N]_ISO` and returns eight `AFEn_[P/N]_RAW`. | PASS |
| Gain/headroom/common mode | Exact OPAx192 population, 1.453571 nominal gain and OPA320/OPA2192 VCM chain in §3. | PASS |
| LF corner | 4.7 uF nominal, >=2.2 uF effective, 100 kohm; 0.339/0.723 Hz. | PASS |
| Load/stability | `Rg+Rf>=4.066 kohm` and matched 47.0-ohm output isolation; Sheet 4 owns the balanced 1 nF C0G differential ADC capacitors. Macromodel/noise/CMRR tests retained. | PASS for schematic |
| Noise-critical resistors | 100 kohm bias, 2.80 kohm Rg, 1.27 kohm Rf, all 0.1% thin-film; 47 ohm output and Sheet 7 100 ohm RF resistors matched within each pair. | PASS |
| Power-off behavior | Paired-domain powered-off switches; no direct VREF or charged output path across an absent rail. | PASS |
| ADC interface | Eight outputs map one-to-one and polarity-correct to ADAU1978 AIN1-4. | PASS |
| Sheet 3 hierarchy count | **18 scalar pins:** eight mic inputs, eight AFE outputs, `AFE_VCM_ISO`, and `5V_AFE`. Ground is a global power net; no microphone connector is instantiated here. | PASS |

`ANALOG_PWR_EN` must not be added as an unused hierarchy pin or directly switch an op-amp signal pin. Power removal and Sheet 2 isolation establish the safe state.

### 4.2 Sheet 4 — ADAU1978 ADC

| Audit item | Frozen implementation | Result |
| --- | --- | --- |
| Analog inputs/polarity | Pins 33/32, 35/34, 37/36 and 39/38 receive channel 1-4 `P/N` respectively. Fit one 1 nF C0G differential capacitor directly across each input pair after isolation. | PASS |
| Supplies/grounds | Pins 4, 31, 40 `AVDD2/3/1` to `3V3_ADC_A`; pin 12 IOVDD to `3V3_SYS`; pin 10 DVDD is an output only; all six AGND, DGND and exposed pad to the solid ground system with analog return placement. | PASS |
| Decoupling | 100 nF at each AVDD pin plus at least 10 uF shared ADC analog bulk; IOVDD 100 nF; DVDD 100 nF + 10 uF nominal X7R (effective maximum 12 uF) and 3.00 kohm 1% REXT; VREF 100 nF + 10 uF. | PASS |
| Reference/PLL | Local `OPA320AIDBVR` VREF follower; MCLK-mode PLL filter exactly 1.00 kohm, 5.6 nF and 390 pF, NPO/C0G capacitors placed at pin 3. | PASS |
| Clocks/data | Pin 7 24.576 MHz MCLK; pin 16 12.288 MHz BCLK input; pin 15 96 kHz LRCLK input; pin 13 TDM4 data out; pin 14 SDATAOUT2 left electrically unconnected and explicitly marked NC-by-design. | PASS |
| Reset/startup | Pin 6 `ADC_PD_RST_N`; 3.00 kohm/10 uF DVDD discharge contract; >=50 ms low for in-place reset; PWUP remains 0 until >=10 ms after DVDD>1.2 V and stable MCLK, then poll PLL lock. | PASS |
| Control/address | Pin 9 SA_MODE 10 kohm to GND for control mode; pins 19 ADDR0 and 20 ADDR1 each 10 kohm to GND for 7-bit address 0x11; pins 17/18 on shared 3.3 V I2C with one bus-level pair of 2.2 kohm pullups. | PASS |
| Configuration | Slave, MCLK PLL, MCS=`011`, 96 kHz, TDM4, 32-bit slots, 24-bit two's-complement, MSB first, one-BCLK delay, `PLL_MUTE=1`, channel HPFs off. | PASS |
| NC policy | Pins 8, 23-27 and 30 open; no test pads or copper. | PASS |
| Sheet 4 hierarchy count | **18 pins:** eight analog inputs, `ADC_VREF_RAW`, MCLK, BCLK, FSYNC, TDM data, SDA, SCL, reset, `3V3_ADC_A`, and `3V3_SYS`. Ground is a global power net, not a hierarchy signal. | PASS |

### 4.3 Sheet 5 — ADSP-21569 DSP / boot / debug / clocks

All 400 balls of `ADSP-21569BBCZ10` must exist in the verified symbol. The exact power inventory is 66 `VDD_INT`, 26 `VDD_EXT`, 19 `VDD_REF`, one `VDD_ANA`, 25 `VDD_DMC`, 122 GND, two `DMC0_VREF`, one `DMC0_RZQ`, HADC VREFP/VREFN and four HADC inputs. Connect every supply/ground ball; no power ball is hidden or intentionally omitted.

- `VDD_INT -> 1V0_DSP_CORE`; `VDD_EXT -> 3V3_SYS`; `VDD_REF -> 1V8_DSP_REF_ANA`; `VDD_ANA ->` the same 1.8 V source after its local filter; `VDD_DMC -> 1V35_DSP_DMC`.
- Both `DMC0_VREF` balls use the frozen 10.0 kohm/10.0 kohm, 1 uF half-rail; `DMC0_RZQ` uses 34 ohms to ground. All unused DMC signal balls are explicit no-connects and firmware leaves DMC disabled.
- Tie HADC0_VREFN to ground, HADC0_VREFP to the filtered 1.8 V analog rail, and each unused HADC0_VIN0-3 to ground. Add 100 nF at VDD_ANA and 100 nF at HADC0_VREFP. Do not leave analog inputs floating.
- Replicate the EV-21569-SOM domain capacitor inventory as the schematic count/placement starting point, while retaining Phase 3's regulator-domain bulk limits: VDD_DMC 2 x 1 uF, 9 x 0.22 uF, 9 x 0.1 uF, 4 x 0.47 uF and 3 x 1 nF; VDD_EXT 2 x 10 uF, 8 x 0.47 uF, 9 x 0.22 uF, 1 x 0.1 uF and 7 x 10 nF; VDD_INT 2 x 10 uF, 4 x 1 uF, 10 x 0.47 uF, 5 x 0.22 uF, 5 x 0.1 uF and 6 x 10 nF; VDD_REF 2 x 10 uF, 9 x 0.1 uF and 12 x 10 nF. Capacitor reference designators need not match the SOM, but value/count/domain and BGA placement intent must. A later PI review may add capacitance within regulator limits; it may not silently delete the required VDD_REF 10 nF + 100 nF minimum.

The resource allocation is frozen and conflict-free:

| Function | Processor resource | Ball | Direction |
| --- | --- | --- | --- |
| SPORT0 BCLK | DAI0_PIN01 | Y08 | out |
| SPORT0 FSYNC | DAI0_PIN02 | V09 | out |
| ADC TDM receive | DAI0_PIN03 / SPORT0A primary | W09 | in |
| Amplifier TDM transmit | DAI0_PIN04 / SPORT0B primary | Y09 | out |
| SPI2 MISO/MOSI/CLK/CS | PA00/PA01/PA04/PA05 | N03/P03/R01/T02 | in/out/out/out |
| UART0 TX/RX/RTS/CTS | PA06/PA07/PA08/PA09 | T03/V01/U03/V02 | out/in/out/in |
| TWI0 SCL/SDA | PA10/PA11 | U02/V08 | open-drain |
| `AMP_MUTE_CMD` | PA12 | W06 | out |
| `AMP_STBY_CMD` | PA13 | Y06 | out |
| `ADC_RST_RELEASE_CMD` | PA14 | W07 | out |
| watchdog `WDI` | PA15 | W08 | out |
| `ANALOG_PWR_CMD` | PB00 | A07 | out |
| `SAFE_ARM_CMD` | PB01 | C09 | out |
| `SHUTDOWN_REQ` | PB02 | B08 | out |
| `CLOCK_STARTUP_CMD` | PB03 | C07 | out |
| `AUDIO_DATA_OE_CMD` | PB04 | B07 | out |
| `RUN_HEALTH_OK_CMD` | PB05 | C08 | out |
| `AMP_FAULT_N` | PB06 | V05 | in |
| `AMP_WARN_N` | PB07 | W04 | in |
| `RAILS_OK` | PB08 | W03 | in |

PA02, PA03, PB09-PB15 and PC00-PC07 remain spare. They are not assigned by Astra opportunistically. This allocation consumes no boot, JTAG or SPORT pin twice.

Additional fixed items: SYS_CLKIN0 N01 from the 1.8 V fanout; SYS_XTAL0 L01 open; SYS_HWRST A09 from the hardware reset node; BMODE2/1/0 A08/B09/B10 strapped `001`; JTAG B11/C12/C13/C11/A10; exact `IS25LP512M-RMLE` boot flash and buffered SPI2 contract; TRST 4.7 kohm pulldown; and the existing UART/JTAG headers. Package and all named balls are available in the BC-400-3 option.

Sheet 5 has **37 scalar hierarchy pins**: four rail nets; ten command/watchdog outputs and `RAILS_OK`/`SYS_HWRST` inputs to/from Sheet 2; two amplifier status inputs; eight endpoint audio-clock/data nets; two shared TWI nets; four UART nets; and five JTAG nets. Ground is a global power net. `SYS_HWRST` is already counted as the common root reset net and branches to the JTAG header. Root hierarchy must use those exact counts rather than a generic `TDM` bus.

### 4.4 Sheet 6 — TAS6424E-Q1 amplifier

| Audit item | Frozen implementation | Result |
| --- | --- | --- |
| Exact device/power pins | `TAS6424EQDKQRQ1`; PVDD pins 2, 29, 30, 42, 43, 55, 56 and VBAT pin 3 to `12V_PROTECTED`; VDD pin 19 to `3V3_SYS`; all eleven GND pins and top thermal pad to ground. VDD arrives after PVDD/VBAT as already sequenced. | PASS |
| Internal-regulator bypass | 1 uF at PVDD pin 2 and VBAT pin 3 to ground; 1 uF VREG pin 5 to AREF pin 4; 1 uF VCOM pin 6 to AREF; 1 uF AVDD pin 8 to AVSS pin 7; 2.2 uF from each GVDD pin 9/10 to ground; 1 uF at VDD pin 19. Do not use these pins as supplies. | PASS |
| PVDD decoupling | At each paired PVDD cluster 29/30, 42/43 and 55/56 fit 100 nF + 10 uF to its adjacent ground returns. Retain 470 uF/25 V system bulk plus 1 uF and 1 nF high-frequency PVDD capacitors at the amplifier entry. | PASS |
| Audio/control | MCLK 12, SCLK 13, FSYNC 14, SDIN1 15; ground unused SDIN2 pin 16. SDA/SCL pins 21/20 use the shared bus. I2C_ADDR0/1 pins 22/23 each 10 kohm to ground, selecting 7-bit 0x6A. | PASS |
| TDM | 96 kHz, 128 x fs SCLK, TDM4, 32-bit slots, 24-bit data in slots 1-4, one-bit delay, rising-edge sampling, `BCLK_INV=0`. | PASS |
| Safe state/status | External 10 kohm pulldowns at active-low MUTE pin 25 and STANDBY pin 24; release only from the existing hardware AND gates. External 10 kohm pullups to 3.3 V at open-drain FAULT pin 26 and WARN pin 27. FAULT fans out to Sheet 2 hardware clear and DSP PB06; WARN goes to PB07. | PASS |
| Bootstrap | Eight 1 uF X7R, >=16 V capacitors, each from BST_1M/1P/2M/2P/3M/3P/4M/4P to its corresponding OUT pin. Reserve 2.2 uF alternatives only for a later sub-30 Hz requirement; do not substitute now. | PASS |
| Output filter | Eight 3.3 uH series inductors, one per BTL leg; inductance must remain >=1 uH at the selected OC shutdown current. After each inductor fit 1 uF and 1 nF to the local power-stage ground, matching TI Figure 10-2. DCR target 40-50 milliohms for 4 ohm loads. | PASS for schematic; exact magnetic/EMI validation remains |
| Output/load | OUT1M/P pins 32/34, OUT2M/P 38/40, OUT3M/P 45/47 and OUT4M/P 51/53 remain independent BTL pairs to Sheet 7. Minimum configured load 4 ohms for this prototype; neither leg is ground. | PASS |
| Startup/shutdown | Wait >=12 ms after VDD POR before I2C; set register 0x28 bit 5 before leaving STANDBY; configure TDM/phase/gain/HPF/OC while safe; release STANDBY only into Hi-Z; hold STANDBY low >=15 ms before any supply removal. | PASS |
| Thermal | Top exposed pad and heatsink electrically grounded; retain <=7.5 C/W sink-to-ambient design target and the existing 8 W IC-loss validation case. | PASS for schematic/mechanical interface |
| Sheet 6 hierarchy count | **20 scalar pins:** `12V_PROTECTED`, `3V3_SYS`; MCLK/SCLK/FSYNC/SDIN1; SDA/SCL; MUTE/STANDBY/FAULT/WARN; and eight filtered speaker legs. Ground is global and is not counted as a hierarchy pin. | PASS |

### 4.5 Sheet 7 — connectors / system interfaces

| Interface | Required physical inventory | Result |
| --- | --- | --- |
| Power input | One keyed 2-pin power connector: `12V_IN`, `POWER_GND`, >=6 A/contact pair and 30 Vdc; separate optional chassis lug, never a signal return. | PASS |
| Microphones | Four keyed 5-pin connectors: `2V8_MIC`, `MIC_OUT+`, `MIC_OUT-`, `MIC_GND`, shield/chassis. Total 20 contacts: four supply, eight analog signals, four returns, four shields. Connector-edge protection and matched 100.0-ohm, 0.1%, thin-film RF resistors are on this sheet; external modules contain the microphones/100 nF local bypass. | PASS |
| Speakers | Four keyed 2-pin connectors, eight contacts total: `SPKn+`, `SPKn-`; >=3 A continuous and 7 A fault withstand. No ground/chassis pin in a BTL pair. | PASS |
| UART | One keyed 6-pin 3.3 V logic header: reference, GND, TX, RX, RTS, CTS. External voltage-standard conversion is not on this board. | PASS |
| JTAG/programming | One keyed 10-pin 0.05-inch ADI/SOM header with the frozen section 11 mapping, three grounds, target reference and reset. This is the primary programming interface. | PASS |
| Recovery/service | UART boot straps provide recovery. Optional DNP service I2C is four pins: 3V3 reference, GND, SCL, SDA; no external pullups and no hot-plug. | PASS |
| Optional controls | No unapproved external control is required. Provide labeled test pads, not a populated connector, for safe-arm/analog/clock/data-OE/run-health commands. Any future switch or off-board pullup is a new interface requiring a back-power/safety review. | PASS |

Exact connector series and enclosure mechanics remain procurement/mechanical selections within these fixed counts and ratings. They do not change schematic architecture.

## 5. Cross-sheet hierarchy inventory

The following inventory is the root-sheet contract. Counts are scalar nets; rails and grounds are listed where crossing ownership matters.

| Source | Destination | Signal bundle | Direction | Count |
| --- | --- | --- | --- | ---: |
| Sheet 7 | Sheet 2 | `MIC1..4_[P/N]_RAW` after edge protection/100 ohms | 7 -> 2 | 8 |
| Sheet 2 | Sheet 3 | `MIC1..4_[P/N]_ISO` | 2 -> 3 | 8 |
| Sheet 3 | Sheet 2 | `AFE1..4_[P/N]_RAW` | 3 -> 2 | 8 |
| Sheet 2 | Sheet 4 | `ADC1..4_[P/N]_ISO` | 2 -> 4 | 8 |
| Sheet 4 | Sheet 2 | `ADC_VREF_RAW` | 4 -> 2 | 1 |
| Sheet 2 | Sheet 3 | `AFE_VCM_ISO` | 2 -> 3 | 1 |
| Sheet 2 | Sheets 3/4/5/6/7 | Frozen rails and enables: 5V AFE; 3V3 ADC; DSP rails; 3V3 SYS; 12V protected; 2V8 MIC | 2 -> loads | 8 named rails plus returns |
| Sheet 5 | Sheet 4 | ADC MCLK, BCLK, FSYNC | 5 -> 4 | 3 |
| Sheet 4 | Sheet 5 | ADC TDM data | 4 -> 5 | 1 |
| Sheet 5 | Sheet 6 | amplifier MCLK, SCLK, FSYNC, TDM data | 5 -> 6 | 4 |
| Sheet 5 | Sheets 4/6 | shared SDA, SCL | bidirectional | 2 |
| Sheet 5 | Sheet 2 | six retained-domain commands, MUTE command, STANDBY command, ADC reset-release command, WDI | 5 -> 2 | 10 |
| Sheet 2 | Sheet 5 | `RAILS_OK`, `SYS_HWRST` (dedicated reset, not GPIO) | 2 -> 5 | 2 |
| Sheet 6 | Sheets 2/5 | `AMP_FAULT_N` fanout | 6 -> 2 and 5 | 1 source, 2 sinks |
| Sheet 6 | Sheet 5 | `AMP_WARN_N` | 6 -> 5 | 1 |
| Sheet 6 | Sheet 7 | four filtered BTL `SPKn+/-` pairs | 6 -> 7 | 8 |
| Sheet 5 | Sheet 7 | UART TX/RX/RTS/CTS | mixed | 4 |
| Sheet 5 | Sheet 7 | JTAG TMS/TCK/TDO/TRST/TDI | mixed | 5 |
| Sheet 2 | Sheet 7 | common `SYS_HWRST` branch to JTAG reset contact | 2 -> 7 | 1 |
| Sheet 5 | Sheet 7 | optional service SDA/SCL | bidirectional | 2 |

No net in this table is a vector placeholder whose width may be chosen during schematic entry. The exact scalar labels and polarity are part of the contract.

## 6. Remaining non-architectural validation

The following are explicitly **physical-validation items**, not choices left to Astra:

- SPICE/macromodel DC, AC, noise, stability, CMRR and overload recovery for the exact OPA320/OPAx192/switch/ADC network at rail, resistor, temperature and microphone corners.
- Extracted plus measured microphone `Ca`, `Cb`, and `Cd`, each <=100 pF with the production cable/module.
- ADC full-scale/clipping onset because 2 Vrms is published as typical, plus complete channel gain/phase matching.
- ADC data hold timing using exact IBIS/trace extraction and the already frozen >=3 ns measured acceptance criterion.
- DSP rail transient/PI and BGA escape review; decoupling may be augmented within the frozen regulator limits.
- Exact amplifier inductor part, saturation/DCR/temperature, EMI filter optimization, heatsink/interface, load diagnostics and conducted/radiated emissions.
- Exact production connector series, creepage/mechanics, mating-cycle and cable strain relief.

None of these items changes a signal count, polarity, component function, voltage domain, boot resource, protocol, connector pin inventory or safe-state architecture.

## 7. Controlled implementation order

1. Do not resume Phase 4C yet. First revise the Sheet 2 microphone isolation block and root hierarchy to the four exact TMUX1574 packages and eight-leg mapping in §3.2; retain the ten TMUX2821 devices for the other two boundaries.
2. Re-run the Phase 4B structural/ERC checks for only the affected Sheet 2/root interface and record the amendment. Do not redesign passed power/sequencing circuits.
3. Resume Phase 4C using the exact Sheet 3 parts/values and hierarchy in §3.5/§4.1.
4. Implement Sheets 4-7 only from their frozen inventories above. A mismatch against any scalar-net count or resource allocation is a stop condition, not an invitation to choose a substitute during entry.

## 8. Gate

Both Phase 4C blockers are resolved. Every remaining sheet has a fixed component/interface/safe-state contract, the four-channel DSP resource map has no collision, connector counts include required returns/shields, and the remaining unknowns are physical validation or mechanical procurement items rather than schematic-architecture blockers.

PHASE 3G: PASS
