# Phase 1 - Component and Datasheet Verification

Repository: `circuitBuilderAi-Astra`  
Review dates: 2026-09-06 to 2026-09-07 (Europe/Istanbul)  
Scope: documentary component verification, interface analysis and bounded feasibility calculations.

## 1. Executive summary

**The candidate chain is not approved for progression to architecture design.** Four-channel 96 kHz / 24-bit transport is supported at the format and bandwidth level, but the TAS6424-Q1 clock requirements contain an unresolved primary-source conflict. Unqualified direct digital connections also fail a worst-case logic-high guarantee check over the complete permitted supply ranges. A narrower supply envelope or verified interface drivers could address the latter; neither is selected here.

Recommendations: IM73A135, ADAU1978 and ADSP-21569 are **PROVISIONALLY APPROVED**; TAS6424-Q1 is **BLOCKED BY MISSING EVIDENCE**. No candidate has been proved unable to meet a confirmed product requirement, so none is rejected merely for an unanswered product requirement. Specific unsupported connection/clock hypotheses are rejected below. No replacement is approved.

Key findings:

- The microphone is the differential analog **IM73A135V01**, not a digital microphone. Its two supply modes are disjoint. Direct ADC drive is outside its specified load envelope; the intended AFE must buffer and reconcile bias, levels and noise.
- Four 32-bit slots at 96 kHz require **12.288 MHz BCLK**. The ADC and DSP have explicit support for this arrangement. Separate DSP receive/transmit SPORT halves allow different output framing.
- TAS6424-Q1 supports four-channel TDM, but §9.3.1.4 permits tied MCLK/SCLK while §9.3.1.5 forbids an in-phase relationship. No authoritative correction with a quantitative safe phase window was found. TDM8 is documented more explicitly and used at 96 kHz by an official reference design, but does not resolve this conflict.
- The published ADC and amplifier delay contributions sum to approximately **364.4 microseconds at 96 kHz**, before microphone/AFE phase delay, DSP scheduling and other unaccounted stages. This is a screening calculation, not a guaranteed system bound.
- DSP core power can substantially exceed its room-temperature typical figure. Five DSP supply domains, 1.8 V clock-input signaling, startup I/O glitches, and silicon-specific boot/DMC/accelerator workarounds matter.
- All 44 Phase 0 UNKNOWN requirements and five X-items were reviewed. Component subquestions were narrowed; **no complete U01-U44 product requirement is closed by datasheets alone**.

No schematic, PCB, footprint, regulator, AFE or firmware implementation was created. No Phase 2 work is authorized by this report.

## 2. Sources reviewed

Read repository inputs: `AGENTS.md`, `MASTER_SPEC.md`, `README.md`, `docs/architecture.md`, `docs/decisions.md`, and [Phase 0 freeze](phase_0_requirements_freeze.md). The master/architecture/decision files remain placeholders. The Phase 0 description of AGENTS.md as a placeholder is historical: the current substantive AGENTS.md governs this review. The user's Phase 1 instruction supersedes the earlier C10 stop-at-Phase-0 task boundary; C01-C09 are unchanged. An existing user modification to AGENTS.md was preserved.

No `graphify-out/graph.json` exists and no Graphify MCP was available. Navigation used file inventory, `rg`, PDF text search and targeted page inspection. Graph results were not fabricated.

The [component evidence index](../evidence/component_evidence_index.md) identifies official URLs, local files, revisions, exact review regions and acquisition limitations. Sixteen official PDFs were obtained. Main sources are:

| ID | Document actually inspected | Revision/date inside document |
| --- | --- | --- |
| MIC | Infineon IM73A135V01 datasheet | V1.20, 2021-07-07 |
| ADC | ADAU1978 datasheet | B, August 2024 |
| DSP | ADSP-21562/3/5/6/7/9 family datasheet | D, June 2023 |
| HRM | ADSP-2156x SHARC+ Processor Hardware Reference | 1.1, October 2022 |
| ANOM | ADSP-2156x Silicon Anomaly List, NR004735J | J, 2026-01-29 |
| POWER | EE-470, ADSP-2156x Power Sequencing Requirements | 1, 2025-02-17 |
| DSPPOWER | EE-414, Estimating Power for ADSP-2156x | 2, 2021-03-15 |
| BOOT | EE-447, Processor Boot ROM | V01, 2023-05-11 |
| JTAG | EE-68, Analog Devices JTAG Emulation Technical Reference | 10, 2008-04-15; historical probe examples |
| SOM / SOMSCH | EV-21569-SOM manual / schematic | Manual 1.0, September 2020 / schematic A, title sheet 2020-01-29 |
| ADCEVAL | UG-600, Evaluating ADAU1977/1978/1979 | 0, 2014 |
| AMP | TAS6424-Q1, SLOS870B | B, October 2017; current download also has newer ordering addenda |
| AMPEVAL | TAS6424-Q1 EVM, SLOU453A | A, October 2017 |
| INDUCTOR | SLOA242, Inductor Selection Guide for 2.1 MHz Class-D Amplifiers | A, September 2019 |
| REF733 | TIDA-00733 design guide, TIDUCZ2 | December 2017 |

Current manufacturer product indexes were checked for the main datasheet revisions and lifecycle. DSP index metadata dates disagree with document dates for ANOM, DSPPOWER and BOOT; this index preserves both provenance and the actual PDF revision. These are metadata discrepancies, not evidence of a different silicon behavior. No claim of exhaustive manufacturer-private documentation access is made.

Local references below use these IDs. Page numbers are printed PDF pages, except HRM citations which use chapter-page labels and optionally physical PDF page numbers. Document facts are **CONFIRMED** only under the stated source conditions; calculations are **derived**, and proposed configurations are **PROVISIONAL**. UNKNOWN and CONFLICTING have the Phase 0 meanings. Interface status uses the requested four-value vocabulary.

## 3. Microphone verification

| Item | Verified finding / remaining boundary | Evidence |
| --- | --- | --- |
| Exact identity | IM73A135V01; ordering code SP003803274; official product OPN IM73A135V01XTSA1. Package PG-LLGA-5-2. Active/preferred on manufacturer product page at review. | MIC p.1 Table 1; official product index |
| Interface | Active differential analog OUT+/OUT-, internal preamplifier and MEMS bias generation. No PDM/I2S/TDM interface and no external electret-bias assumption. | MIC pp.1-2 |
| Supply modes | Normal: 2.3-3.0 V, 2.75 V typical; low power: 1.52-1.8 V, 1.6 V typical. The gap between 1.8 and 2.3 V is not a documented operating mode. 3.3 V supply is prohibited: 3.0 V is also the stated absolute maximum. | MIC p.8 Tables 5-6 |
| Current | Normal 170 microamp typical / 230 microamp maximum; low power 70 / 80 microamp. Table 7 condition: input <=94 dBSPL, otherwise default 25 C conditions. High-SPL loaded worst-case current is UNKNOWN. | MIC p.10 Table 7 |
| Bias distinction | Output DC: 1.35 V normal / 0.9 V low power, typical. Separately, the *undriven AFE input* VCM in the specified load network is 1.17-1.43 V normal or 0.765-0.935 V low power. These are not interchangeable specifications. | MIC pp.8-10, Table 6, Fig.11, Table 7 |
| Loading | Rp and Rn each >=25 kilohm; Ca, Cb and differential Cd each <=100 pF in Fig.11. Output impedance maximum 250 ohm normal / 500 ohm low power. Include cable, protection and AFE capacitance. | MIC Tables 6-7; Fig.11 visually inspected |
| Sensitivity | -39 to -37 dBV, typical -38 dBV at 1 kHz, 94 dBSPL, unloaded; tolerance +/-1 dB. | MIC p.6 Table 3 |
| AOP / distortion | Typical normal AOP 135 dBSPL at 10% THD; 132 dBSPL at 1% THD. Low power 130 and 124 dBSPL respectively. AOP is not a clean linear headroom target. | MIC p.6 Table 3 |
| Noise | Typical SNR 73 dB(A) normal / 71 dB(A) low power; noise floor -111 / -109 dBV(A). Derived equivalent acoustic noise: 94-SNR = 21 / 23 dBSPL(A). Broadband unweighted input noise density is not specified by these A-weighted numbers. | MIC p.6; derivation |
| Frequency / latency | Typical -3 dB roll-off 20 Hz. Table 4 response limits include -4.5 to -1.5 dB at 20 Hz, -1.5 to +0.5 dB at 50 Hz, rising HF response through 15 kHz. Typical group delay: 52 us at 250 Hz, 7 us at 600 Hz, 2 us at 1 kHz, 0.5 us at 4 kHz. Cannot apply 2 us across the ANC band. | MIC pp.4, 6-7 |
| Startup | VDD ramp-up <=5 ms as defined in Table 6; startup 10 ms typical / 30 ms maximum after VDDmin, mode-change output undefined for 10 ms typical; brownout threshold 1.2 V typical. | MIC pp.8, 10 |
| External components / mechanics | 100 nF close to VDD. Bottom sound port; nominal 4 x 3 x 1.2 mm body, drawing max height 1.28 mm. PCB acoustic hole recommendation 0.8 mm diameter; protect the port from vacuum, blown air, ultrasonic cleaning and contamination. No product enclosure/port design is frozen. | MIC pp.8, 11-15 |
| Exact pinout | 1 OUT+; 2 VDD; 3 OUT-; 4 GND; 5 GND (port-surround pad). Bottom-view package drawing must not be mirrored into a future symbol/footprint. | MIC p.11 Fig.12, Table 8; visually checked |

**Four microphones through a practical AFE: PROVISIONAL feasibility, not signal-quality approval.** The microphone's >=25 kilohm per-leg load does not match the ADC's typical 14.3 kilohm per-leg input resistance. AC coupling alone does not remove that AC load. Furthermore, the ADC's typical 1.5 V input bias is not the MIC Table 6 normal-mode AFE VCM range. An independently biased buffer and appropriate coupling/level translation can separate these requirements; an exact AFE device and fault-safe implementation have not been verified.

Future AFE requirements, not a design:

1. Preserve four independent differential signals; satisfy MIC Fig.11 resistive/capacitive loading, including remote cables and protection. Do not ground one driven microphone output.
2. Accept microphone DC bias and worst-case signal swing without clipping, and present the proper undriven input VCM where that microphone load configuration is used. Reconcile power-off/back-drive cases before selecting DC coupling.
3. Drive ADC differential inputs, their resistance and external network while maintaining common-mode and input-voltage limits. The ADC VREF is a decoupled reference, not a general load-driving AFE supply.
4. Set gain from U05/U09 headroom and noise requirements. Derived nominal microphone output at 94 dBSPL is 12.59 mVrms; at 135 dBSPL a linear extrapolation is 1.413 Vrms, already at the specified distorted AOP. Gain selected to fill 2 Vrms at 94 dBSPL would overload badly at higher SPL.
5. Budget input-referred AFE noise against approximately 2.82 microVrms(A) normal microphone self-noise and ADC noise, using matching bandwidth/weighting. From ADC 109 dB(A) typical dynamic range, the screening equivalent noise is 7.10 microVrms(A) at 2 Vrms full scale. Gain can improve ADC utilization, but the acceptable noise penalty and SPL envelope are UNKNOWN.
6. Define combined LF amplitude/phase and anti-alias/RF response from U01/U10. Do not choose a coupling corner, filter order, gain or op amp in this phase.

## 4. ADC verification

| Item | Finding | Evidence |
| --- | --- | --- |
| Identity / package | ADAU1978WBCPZ or -RL packing variant, 40-lead 6 x 6 mm LFCSP, CP-40-10; production on official page. Exposed pad connects to PCB ground plane. | ADC pp.8-9, 44 |
| Conversion | Four multibit sigma-delta ADCs with continuous-time front end, 24-bit outputs; 8-192 kHz supported rate range. Summing modes sacrifice independent channels and are inappropriate for C02/C03. | ADC pp.1, 3, 16, 40 |
| Analog inputs | Differential or pseudo-differential/single-ended. Typical differential full scale 2 Vrms; single-ended capability 1 Vrms. Per-leg resistance 14.3 kilohm / differential 28.6 kilohm typical. Typical input common mode 1.5 V. | ADC Table 1, pp.14-15 |
| Common-mode/headroom limits | Differential DC-coupled example swings each input about 0.086-2.914 V around 1.5 V at full scale. This example is not a guaranteed arbitrary common-mode range. Absolute input limit -0.3 to +3.6 V is a stress limit, not the linear input contract. AC-coupled operation with internal bias is the provisional path; precise DC-coupled tolerance and powered-off injection remain UNKNOWN. | ADC pp.7, 14-15 |
| Analog network / references | Differential AC coupling illustrated; capacitance depends on chosen LF corner and input resistance. VREF: 1.47-1.54 V, typical 1.50 V, 20 kilohm typical output impedance; decouple with 10 uF parallel 100 nF. DVDD: 10 uF parallel 100 nF, with reset-discharge provision. AVDD/IOVDD decoupling and PLL filter are shown in Fig.44. | ADC pp.3, 8, 12-15, 43 |
| Audio ports | I2S, LJ, RJ; TDM2/4/8/16 slots, with four actual ADC channels; 16/24-bit significant data, 16/24/32-bit slots subject to fit. MSB/LSB order selectable. Pulse or nonpulse framing. Output pin and channel-slot map selectable. | ADC pp.17-19, 31-36 |
| Clocks | Master or slave for BCLK/LRCLK; master BCLK maximum 24.576 MHz. In slave mode Table 5 requires BCLK high/low >=10 ns, LRCLK setup >=10 ns and hold >=5 ns. SDATAOUT delay <=18 ns from falling BCLK. | ADC pp.5, 18-19 |
| PLL / MCLK | PLL source MCLKIN or LRCLK; LRCLK mode 32-192 kHz and serial slave only. At 96 kHz, 24.576 MHz is explicitly supported with MCS=011; 12.288 MHz uses MCS=001. Do not apply the 48-kHz register ratio wording directly to 96 kHz. | ADC Table 9 pp.13-14, Table 18 p.29 |
| PLL external filter | MCLK-mode Fig.15 uses 1 kilohm, 5.6 nF and 390 pF; LRCLK-mode uses 4.87 kilohm, 39 nF and 2.2 nF. Preserve the actual topology and return to AVDD; C0G/NP0 recommended. These are device reference networks, not selected production parts. | ADC p.14 Fig.15 |
| Digital filtering / latency | Linear-phase antialias/decimation filter; 79 dB stop-band attenuation. Table 4 gives 22.9844/fs for 8-96 kHz, or 239.4208 us at 96 kHz. No verified low-latency bypass at 96 kHz was found. | ADC pp.4, 16 |
| HPF discrepancy | Table 4: 0.9375 Hz at 48 kHz; p.14: 1.4 Hz and proportional scaling with fs. **CONFLICTING**. At 96 kHz the two extrapolations are 1.875 and 2.8 Hz; neither is confirmed. HPF can explicitly be disabled per channel through 0x1A bits 3:0. Bypass is an available capability, not acceptance of the system's LF/DC behavior. | ADC pp.4, 14, 42 |
| Rails / thermal | AVDD 3.0-3.6 V; IOVDD 1.62-3.6 V; internal DVDD 1.8 V nominal. Ambient -40 to +105 C; junction -40 to +125 C; JEDEC thetaJA 32.8 C/W, thetaJC 1.93 C/W. Do not infer enclosure temperature from these alone. | ADC pp.3-4, 7 |
| Control | I2C slave <=400 kHz, 7-bit addresses 0x11/0x31/0x51/0x71; SPI slave <=10 MHz, selected by three CLATCH low assertions. Default control mode I2C. Pull-ups to IOVDD, sized for capacitance/sink capability. | ADC pp.5, 21-25 |
| Reset / startup | Active-low PD/RST. The 15 ns input pulse specification alone does not reset a charged core. DVDD must discharge below the POR threshold (0.48 V conservative threshold from the specified tolerance). With the illustrative 10 uF and 3 kilohm discharge network, nominal reset discharge is 37.8 ms; tolerances must be added. In MCLK mode assert PWUP only >=10 ms after DVDD >1.2 V and stable clocks; verify PLL lock. | ADC Rev.B pp.12-13, Table 5 |

Pinout verification: ADC Table 8/Fig.5 covers all 40 leads. Supply/reference/reset pins: AVDD2=4, AVDD3=31, AVDD1=40, IOVDD=12, DVDD=10, VREF=2, PLL_FILT=3, PD/RST=6, MCLKIN=7, SA_MODE=9. Digital audio: SDATAOUT1=13, SDATAOUT2=14, LRCLK=15, BCLK=16. Control: SDA/COUT=17, SCL/CCLK=18, ADDR0/CLATCH=19, ADDR1/CIN=20. AIN1 P/N=33/32; AIN2=35/34; AIN3=37/36; AIN4=39/38. Grounds=1, 5, 11, 21, 22, 28, 29 and EP. NC=8, 23-27, 30; leave open. No symbol was created or certified.

SA_MODE's documented 10 kilohm pull-up invokes standalone mode; register-controlled operation must use the proper non-standalone state from the application circuit. Do not inherit standalone straps while assuming software configuration. References to a boost converter/microphone bias in generic control prose are not authority to add ADAU1977-only circuitry to this ADC; the actual ADAU1978 pinout and application circuit control.

**Can it produce four channels at 96 kHz / 24-bit for the DSP?** Yes at the documented protocol/capacity level. The explicit candidate is 4 slots x 32 BCLK x 96,000 frames/s = 12.288 MHz, one 24-bit sample per slot. Full electrical connection approval remains PROVISIONAL under Section 7.

## 5. DSP verification

| Item | Finding | Evidence |
| --- | --- | --- |
| Identity / grades | ADSP-21569 is a single SHARC+ SIMD core. Exact orderables include ADSP-21569BBCZ10 (industrial, up to 1 GHz), BBCZ8 (800 MHz), and KBCZ10/KBCZ8 consumer variants. BBCZ10 is a provisional analysis example, not a purchased/frozen grade. | DSP Table 1, p.102 |
| Package | **400-ball CSP_BGA only for this candidate**, 17 x 17 mm, 0.8 mm pitch, BC-400-3. Family LQFP claims cannot be transferred to ADSP-21569. | DSP pp.89-94, 99,102 |
| Core / arithmetic | Operating CCLK range 400 MHz to grade limit, SYSCLK=CCLK/2; 32-bit fixed and 32/40/64-bit floating point. Two SIMD processing elements; core speed is not a measured ANC MAC rate. | DSP pp.3-7, 44-46 |
| Internal memory | 640 KiB L1 SRAM with parity, 1024 KiB L2 SRAM with ECC. L1 contains code/data/cache allocations; total SRAM is not all available for filter history. L2/DMA coherency and bank contention require budgeting. | DSP pp.3-8; HRM memory/DMA sections |
| External memory | One 16-bit DDR3/DDR3L controller; 1.5/1.35 V signaling domains respectively. SPI/OSPI nonvolatile boot supported. External RAM need is UNKNOWN; it is not required solely because the SOM has it. | DSP pp.3, 11, 18, 44; HRM Ch.8/40 |
| SPORTs | Eight full SPORTs, each with two configurable halves, primary/secondary data lines and one DMA channel per half. A half is Tx or Rx; use distinct halves for simultaneous input and output. SPORT0A receive and SPORT0B transmit are resource examples only. | DSP p.13; HRM Ch.23, pp.23-1 onward |
| TDM | Up to 128 selected channels within a 1024-channel frame; serial words up to 32 bits. MFD permits 0-15 bit-clock delay, WSIZE=channels-1, channel mask selects active slots. Programmable drive/sample edge and frame polarity. Four 32-bit words are supported explicitly by these fields. | HRM pp.23-24, 23-33 to 23-35 |
| Audio rates / DMA | SPORT does not impose an audio-rate whitelist: derive rate from word/frame clocks within electrical limits. 12.288 MHz and 24.576 MHz are below the relevant 31.25 MHz external-Tx and 62.5 MHz external-Rx limits, provided peripheral clocks and timing are valid. DMA can move framed audio to/from SRAM; separate descriptor/buffer ownership and overflow/underflow handling required. | DSP Tables 19, 36-37; HRM Ch.23/27 (DMA Table 27-2, p.27-4) |
| Clocking | SYS_CLKIN0 crystal or external source 20-30 MHz, referenced to **1.8 V VDD_REF**, not the 3.3 V DAI domain. PCGs can divide SYS_CLKIN0, SCLK0 or external DAI sources. Core PLL is not characterized as a precision converter clock source. | DSP pp.18, 44, 54; HRM pp.24-1 to 24-9 |
| Other peripherals | Three SPI controllers, with quad modes on SPI1/2; an additional OSPI controller; six TWI/I2C and three UARTs. Pin multiplexing constrains simultaneous allocation. JTAG, watchdogs and system fault/reset facilities are present. | DSP pp.3, 13-18, 24-28 |
| Boot / reset | No boot, SPI2 flash, SPI2 host, UART0 host, LP0 host, OSPI flash modes. SYS_BMODE pins select boot. HWRST release after all rails and input clock valid; at least 11 input-clock periods. Ramp-up/down specification is >=100 us. Revision-specific ROM limitations apply. | DSP Tables 7, 32-33; BOOT; ANOM |
| Power / thermal | VDD_INT=1.00 V, VDD_EXT=3.30 V, VDD_REF/VDD_ANA=1.80 V; VDD_DMC for memory domain. Exact tolerances in Section 10. Industrial junction -40 to +125 C; consumer 0 to +110 C. Thermal/system model needed. | DSP pp.44, 47-53, 88; POWER |

Exact pin information is available in DSP signal/multiplex tables pp.21-43 and full BGA assignments pp.89-94. Automated comparison found **400 distinct balls in each of the numerical/alphabetical lists and zero normalized mapping differences**. This check does not preserve overbar typography and is not independent symbol verification. Original PDF drawings and active-low annotations remain authoritative.

### Initial FxLMS feasibility envelope

This is a hypothetical direct time-domain implementation consistent with Phase 0's workload model. Let R=reference signals, E=error signals, S=4 independent outputs, Lw=controller taps and Ls=secondary-path model taps. If all references/errors are physical, R+E=4; a different allocation requires explicit requirements.

Derived multiply-accumulate-equivalent count per sample:

```text
output filtering     = R*S*Lw
filtered references  = R*S*E*Ls
weight adaptation    = R*S*E*Lw
MACeq/s              = 96000 * [R*S*Lw + R*S*E*(Ls+Lw)]
coefficient bytes    = 4 * [R*S*Lw + S*E*Ls]      (hypothetical float32)
filtered-history bytes ~ 4 * R*S*E*Lw            (straightforward storage)
```

These counts exclude normalization, leakage, clipping guards, path identification, conversion, indexing, buffers, code, telemetry, cache stalls and interrupts. MACeq is algorithm arithmetic, not a guaranteed DSP instruction/cycle ratio. No ASRC, lower processing rate or reduced adaptation rate is assumed.

| Illustrative R=2, E=2, S=4; Lw=Ls | MACeq/sample | MMACeq/s | Maximum cycles/MACeq at 1 GHz with hypothetical 70% core allocation | Coefficients + filtered history only |
| --- | ---: | ---: | ---: | ---: |
| 64 | 2560 | 245.76 | 2.848 | 8 KiB |
| 128 | 5120 | 491.52 | 1.424 | 16 KiB |
| 256 | 10240 | 983.04 | 0.712 | 32 KiB |

Available raw core cycles/sample: 10,416.7 at 1 GHz or 8,333.3 at 800 MHz. The 70% allocation is a sensitivity example, not an approved reserve requirement. The larger workload needs a measured implementation with sufficient SIMD/accelerator throughput; generic processor marketing cannot establish this. Accelerators have setup, memory and completion-interrupt overhead and ANOM 20000128 applies. No accelerator credit is included in the table.

Provisional DMA arrangement: Rx and Tx SPORT halves, one primary data line each, circular/ping-pong DMA buffers in SRAM; process an acquired block and queue the next playback block. At four 32-bit memory words/frame, traffic is 1.536 MB/s each direction, 3.072 MB/s total payload. Two buffers per direction consume 64*N bytes for block length N; descriptors and alignment are extra. A 32-bit Rx word must discard ADC non-data padding before signed 24-bit interpretation.

At 96 kHz, N=1/4/8/16/32 corresponds to 10.42/41.67/83.33/166.67/333.33 us per whole-block interval. Actual delay depends on interrupt, processing and Tx handoff schedules and can include more than one interval. Small blocks increase deadline/interrupt pressure. A three-word SPORT receive pipeline is described in HRM p.23-19; do not count it as an additional fixed three-*frame* delay. Exact filter architecture, code size, sustained execution time and total latency remain **UNKNOWN** until U02/U11-U15/U18 are defined and later benchmarked.

## 6. Amplifier verification

| Item | Finding | Evidence |
| --- | --- | --- |
| Exact variant | TAS6424-Q1, e.g. TAS6424QDKQRQ1, 56-pin DKQ HSSOP. This review does not substitute TAS6424E/L/MS variants. Current official ordering addendum lists production/active orderables, including suffix variants whose procurement identity must be retained. | AMP pp.1, 4-6; ordering addendum |
| Channels / input | Four independent digital-input Class-D BTL channels. PBTL combines outputs and cannot replace four independent channels. Slave audio clock inputs only. | AMP §§9.1, 9.3.1, 9.3.6; pin types |
| Formats | I2S/LJ/RJ and TDM. TDM4/TDM8 stated; 16/24-bit use unambiguously selected through SAP control. Prose mentions 32-bit input, but this report uses 24 significant bits in 32-bit slots and claims no 32-bit conversion precision. | AMP §§9.3.1.1-4, 9.6.4 |
| Rates / slots | 44.1/48/96 kHz. TDM4 x 32 ->128fs; TDM8 x 32 ->256fs. SAP 0x03 selects sample rate, TDM, slot-size category and first/last four slots/channel-pair swap. SDIN1=15, unused SDIN2=16 recommended grounded in TDM. | AMP p.19 Tables 1-2, pp.34-35 |
| Clocks / timing | MCLK 128/256/512fs, maximum 25 MHz; at 96 kHz, 512fs=49.152 MHz is prohibited. SCLK period >=40 ns, high/low >=16 ns; data setup/hold >=8 ns; FS edge spacing >=8 ns around rising SCLK; rise/fall <=4 ns. | AMP p.10, Fig.36 |
| Logic / control | VDD=3.0-3.5 V; VIH>=0.7VDD, VIL<=0.3VDD. I2C slave 100/400 kHz. Derived 7-bit addresses 0x6A/6B/6C/6D from Table 8 write bytes D4/D6/D8/DA; do not pass the write byte as a 7-bit address. | AMP pp.7-8, 28 |
| Supplies | PVDD 4.5-26.4 V high current; VBAT 4.5-18 V; VDD 3.0-3.5 V. PVDD/VBAT can share nominal 12 V if its full envelope meets both. AVDD, GVDD, VREG, VCOM are internal bypass nodes, not external power-tree outputs. | AMP pp.5-8, §§9.3.9, 11 |
| Load / power | BTL nominal load minimum 2 ohm, nominal 4 ohm; actual impedance/reactance and cable unknown. At 14.4 V, 4 ohm, TC=75 C: 20 W minimum /22 W typical at 1% THD+N; 25/27 W at 10%. At 25 V: 50/55 W at 1%, 70/75 W at 10%. None is a 12 V guarantee. | AMP p.7 |
| 12 V envelope | Ideal unboosted sine ceiling into 4 ohm is 12^2/(2*4)=18 W/channel, before losses/clipping criterion. Published graphs are typical; no guaranteed production 12 V/4 ohm output rating was extracted. Output target and simultaneous power budget remain UNKNOWN. | Phase 0 derivation; AMP typical curves |
| Latency / LF | Input-output latency 12 FS periods at 96 kHz ->125 us; no worst-case tolerance stated. Default digital HPF approximately 8 Hz at 96 kHz, versus 4 Hz at 44.1/48 kHz. Its LF phase response belongs in the ANC budget. | AMP p.10, §9.3.2 |
| Thermal | External heatsink required; pad is exposed upward. Thermal pad/heatsink must connect to GND, never another node. Ambient -40 to +125 C, operating junction up to150 C with adequate cooling. Protection trip temperatures are not operating targets. | AMP p.7 note 3; §§12.1.1, 12.1.3, 12.2 |
| Protection | Overcurrent/current limiting, global/channel temperature protection/warnings, over/undervoltage, DC detection, clock-error Hi-Z, load diagnostics, clipping warning. These do not establish board-level or acoustic fault acceptance. | AMP §§9.3.7-10, 9.4 |
| Mute / standby | MUTE and STANDBY active low, internal 100 kilohm pulldowns. MUTE continues switching; Hi-Z and STANDBY differ. STANDBY stops I2C; outputs ramp down in <5 ms if not already Hi-Z. FAULT/WARN active-low open drain with internal 100 kilohm pull-ups. | AMP pp.27-28 |
| Startup / shutdown | Battery-supply operation can accept any rail order, with recommended PVDD/VBAT then VDD for low pop; remove VDD first. Separate boosted supplies require VBAT, then VDD, then PVDD and reverse shutdown. Wait I2C POR startup >=12 ms; configure before MUTE/PLAY, clear/read faults. Default DC diagnostics take 230 ms typical and can be bypassed only by an explicit policy. | AMP pp.9-10, 23, 27, 52 |
| External components / EMI | LC reconstruction on each BTL leg is required. Bootstrap capacitor from each OUT to matching BST: reference 1 uF, X7R or better, >=16 V; below 30 Hz near clipping may require 2.2 uF. Output inductance must remain >=1 uH at shutdown current, with capacitance limits linked to diagnostics. Values/filter response must be chosen for actual load and PWM rate. | AMP pp.7, 23, 52; INDUCTOR |

Exact signal pins: MCLK12, SCLK13, FSYNC14, SDIN1/2=15/16, VDD19, SCL20, SDA21, ADDR0/1=22/23, STANDBY24, MUTE25, FAULT26, WARN27. Power/bypass: PVDD2/29/30/42/43/55/56; VBAT3; AREF4; VREG5; VCOM6; AVSS7; AVDD8; GVDD9/10. OUT P/M by channel: 34/32, 40/38, 47/45, 53/51; corresponding BST P/M:35/31, 41/37, 48/44, 54/50. Grounds1/11/17/18/28/33/36/39/46/49/52 plus thermal pad. AMP pp.4-6 were inspected; a future symbol must independently retain all power pins and active-low annotations.

The 96-kHz PWM frequency row in Table 3 matches the 48-kHz switching choices; do not multiply 96 kHz by 44 to claim 4.224 MHz. Layout lessons: close PVDD decoupling and LC return paths, continuous return plane, compact switching loops, separation from analog inputs; reference board layer count/copper are not project constraints.

## 7. ADC -> DSP compatibility

### Candidate interface contract A

| Field | Provisional configuration / evidence |
| --- | --- |
| Transmitter / receiver | ADAU1978 SDATAOUT1 (13) -> ADSP-21569 receive half SPORT0A primary data through DAI/SRU. SPORT/DAI assignment is a resource example, not final pin allocation. |
| Clock master / slave | DSP PCG supplies BCLK/FS; ADC slave and DSP SPORT consume that common PCG clock. A PCG-sourced SPORT clock is distinct from the SPORT's own internal divider; use external-clock SPORT timing until exact routing is verified. |
| Sample/frame rate | 96,000 frames/s; frame duration 10.4167 us. |
| Sample / slots | Signed 24-bit MSB-first samples; four 32-bit slots; slot 1->ADC 1 through slot 4->ADC 4. |
| Frame format | Active-high single-BCLK pulse; data delayed one BCLK (I2S-style TDM); launch falling/sample rising. Match ADC LR_POL/LR_MODE and SPORT LFS/MFD explicitly. |
| BCLK | 96,000*4*32=12,288,000 Hz; period 81.3802 ns, ideal half 40.6901 ns. |
| ADC MCLK | 24.576 MHz, MCS=011 at 96 kHz; MCLK-source PLL, CLK_S=0. |
| ADC fields | SAI_CTRL0: FS=011, SAI=010, SDATA_FMT=00. SAI_CTRL1: DATA_WIDTH=0, SLOT_WIDTH=00, LR_MODE=1, SAI_MSB=0, SAI_MS=0, SDATA_SEL=0. BCLKEDGE=0; channel map 0/1/2/3. Enable four ADCs; disable summing; follow Rev.B initialization. No full register write sequence is asserted. |
| DSP fields | TDM multichannel, receive, MSB first, 32-bit serial word (SLEN=31), WSIZE=3, WOFFSET=0, MFD=1, channels 0-3 enabled, CKRE=1, active-high FS. Program before enabling SPORT; DMA word layout/masking must be verified. |
| Padding | ADC inactive/non-data positions can be Hi-Z per Fig.27. Never treat the lower 8 sampled padding bits as audio or assume they are zero. Define idle bias/loading and discard them. |
| Logic | ADC IOVDD near 3.3 V and DSP VDD_EXT 3.3 V domain, with constrained maxima as below. ADC 1.8 V direct signaling is INCOMPATIBLE with DSP guaranteed VIH 2.0 V. |
| Compatibility status | **PROVISIONAL**: protocol and bandwidth established; full PVT/load/rail timing and startup contract not closed. |

Evidence: ADC Tables 5, 9-10, 19-23/Figs.25-27; DSP Tables 19, 36-37; HRM pp.23-24, 23-33 to 23-35 and Ch.22/24.

### Electrical margin, not just protocol names

ADC VOH minimum is IOVDD-0.6 V; DSP VIH minimum 2.0 V. For a constrained ADC IOVDD minimum of 3.0 V, raw high margin is 0.4 V; low margin is 0.8-0.4=0.4 V. This direction has a feasible stated-level envelope.

DSP VOH minimum 2.4 V (specified load/drive conditions), whereas ADC VIH=0.7*IOVDD. At ADC maximum 3.6 V, the guarantee misses by 0.12 V. Even a shared DSP rail at its maximum 3.47 V requires 2.429 V, above 2.4 V. Therefore **unqualified direct DSP->ADC clock/control push-pull wiring over the full allowed ranges is not approved**. Necessary high-level condition is IOVDDmax<2.4/0.7=3.42857 V for positive raw margin; required noise margin makes the ceiling lower. A hypothetical 3.3 V +/-1% rail leaves only 66.9 mV. Pull-up-driven I2C highs require their own bus analysis and do not inherit the push-pull VOH calculation.

At ideal 50% duty and 12.288 MHz, ADC data setup screening margin to an external-clock SPORT is 40.6901-18-2=20.6901 ns. If DSP generates FS using externally-clocked SPORT switching, FS setup at ADC is 40.6901-11-10=19.6901 ns. PCG/SRU delay, duty tolerance, PCB skew, jitter and capacitive derating must be subtracted; these figures are not guaranteed board margins. ADC Table 5 has no separate minimum output-delay/hold limit; do not invent one. Check the complete valid-data window and startup/high-Z behavior in later electrical verification.

Alternative: ADC owns BCLK/LRCLK from 24.576 MHz MCLK and DSP receives as slave, using the same clock reference for playback. This avoids DSP-generated ADC audio clocks but changes startup/master ownership. It does not resolve amplifier clock conflicts or the control/power contract.

## 8. DSP -> amplifier compatibility

| Field | Candidate B4 | Candidate B8 |
| --- | --- | --- |
| Transmitter / receiver | DSP Tx half SPORT0B primary via DAI -> TAS6424 SDIN1(15) | Same, separate from acquisition data |
| Master / slave | DSP PCG audio clock master; TAS6424 clock slave | Same |
| Samples / frame | Four independent 24-bit samples, MSB first | Four useful 24-bit samples in first four slots; remaining slots transmit defined zero data |
| Slot count/width | 4 x 32 | 8 x 32 |
| Frame frequency | 96 kHz | 96 kHz |
| BCLK/SCLK | 12.288 MHz =128fs | 24.576 MHz =256fs |
| Frame shape | Provisional active-high pulse, one BCLK before first MSB; TDM4 prose supports mode but no dedicated TDM4 waveform | Active-high pulse and one-BCLK-delayed data as AMP Fig.39 TDM8 waveform |
| DSP setup | SLEN31, WSIZE3, MFD1, Tx, CKRE1, four slots | SLEN31, WSIZE7, MFD1, Tx, CKRE1, eight slots; four zero-padding slots |
| TAS6424 setup | SAP sample-rate10, format110, slot-size bit0, normal channel-pair order, first four slots; SDIN2 grounded per guidance | Same SAP fields; first-four-slot selection |
| MCLK | Possible 12.288 or 24.576 MHz; phase relationship **CONFLICTING** |24.576 MHz; tied-clock permission **CONFLICTING** with adjacent section |
| Logic | DSP 3.3 V domain -> amplifier 3.3 V domain, conditional rail/noise margin | Same |
| Compatibility status | **UNKNOWN** complete compatibility: clock conflict unresolved | **UNKNOWN** complete compatibility: same conflict; stronger reference-design mode evidence |

TDM-specific §9.3.1.4 and register Table 13 support 128/256 clocks, whereas §9.3.1.5 lists only 32/48/64fs SCLK. The mode-specific interpretation is reasonable and supported by Fig.39 and REF733, but is recorded as a **PROVISIONAL interpretation**, not an official correction. Packed four 24-bit slots (9.216 MHz, 96fs) are **not established** for this amplifier; do not assume ADC support transfers to it.

More consequentially, §9.3.1.4 permits tied MCLK/SCLK and §9.3.1.5 disallows in-phase MCLK/SCLK. A tied clock is necessarily in phase. This is **CONFLICTING source evidence**. Separate phase-offset clocks are a candidate mitigation, but no guaranteed minimum/maximum phase separation was located. Neither a forum response nor a working reference board resolves a conflicting device limit across operating corners. Required closure: manufacturer-controlled clarification for the exact variant/revision, or a formally accepted and justified alternate component/mode with a complete clock contract. No external inquiry was sent.

DSP VOH 2.4 V versus AMP VIH 0.7*VDD requires VDDmax<3.42857 V before noise margin; full AMP 3.5 V maximum gives 2.45 V VIH and a 50 mV shortfall. ADC and amplifier can potentially share a tightly bounded logic rail with the DSP, or use verified drivers. **No generic 1.8 V direct interface is acceptable.** DSP timing uses nominal 6 pF reference loads, while AMP audio input capacitance can be 10 pF plus routing; apply DSP pp.87-88 derating or IBIS analysis before timing sign-off.

Nominal externally-clocked SPORT Tx data setup screening:

| BCLK | Ideal half-cycle | Half - DSP tDDTE 11 ns - AMP setup 8 ns |
| --- | ---: | ---: |
|12.288 MHz|40.6901 ns|21.6901 ns|
|24.576 MHz|20.3451 ns|1.3451 ns|

The B8 residual is particularly small before loading/skew/jitter. Internal-divider SPORT timing has a different 3.5 ns output-delay specification, but cannot simply be substituted for PCG routing. Final hold/FS margin and <=4 ns AMP edge requirements remain to be closed. Consequently **B4 is the first candidate to clarify**, because it has lower clock rate and more timing room; B8 is a documented comparison, not an approved fallback.

Two stereo I2S data lines could carry four channels at 6.144 MHz BCLK with 32-bit slots, using SPORT primary/secondary Tx paths. This changes the provisional TDM-only path and still needs MCLK phase closure. No alternate architecture is silently adopted.

## 9. Clock feasibility

| Candidate | Frequency feasibility | Unresolved cost/constraint |
| --- | --- | --- |
| K1: one 24.576 MHz source; DSP PCG clock master |24.576 MHz meets DSP 20-30 MHz SYS_CLKIN0 and ADC Table 9. PCG divide 2 for 12.288 MHz and divide 256 for 96 kHz; pulse width 2 input clocks makes one-BCLK FS. Phase must put FS transitions on the drive edge. | DSP SYS_CLKIN0 is 1.8 V; ADC/AMP/DAI are proposed 3.3 V. A single oscillator requires suitable verified output domains/fanout, not one unqualified wire. AMP phase conflict and endpoint timing open. |
| K2: separate DSP 25 MHz system source + shared audio 24.576 MHz source | PCG can consume the audio source through DAI; CPU can run a separately selected valid clock. Audio Rx/Tx remain frequency coherent. | Extra source/fanout; synchronize DMA/software crossings, but no asynchronous *audio sample-rate* domain is needed. No claimed exact CPU multiplier program. |
| K3: ADC audio master, shared 24.576 MHz reference | ADC emits 12.288 MHz/96 kHz; DSP Rx slave and Tx uses coherent reference/FS. | ADC initialization becomes upstream dependency; return/control levels and amp phase still open. |
| K4: DSP master; ADC LRCLK PLL | ADC supports96 kHz LRCLK-derived PLL; ADC MCLK routing can be omitted. | Different PLL filter; MCLK-mode 10 ms lock guarantee must not be applied to LRCLK mode. LRCLK lock time/jitter and robust startup remain UNKNOWN; characterize before selection. |

K1 is a **PROVISIONAL preferred investigation**, supported by HRM Ch.24 divider capability and ADC Table 9. It is not the selected network. Separate SPORT interfaces can use different slot counts/BCLKs derived from the same source and same 96 kHz frame reference. Independent free-running audio oscillators are not recommended: drift eventually requires dropped/repeated samples, elastic buffers or ASRC, none approved under U18. CPU/audio clock separation is different from independent acquisition/playback sample clocks.

The HRM warns that the core PLL is not specified for precision converters (p.24-5). Prefer investigating direct audio-source PCG division over generating ADC clocks from an arbitrary core PLL. Oscillator jitter/accuracy, fanout loading, clock duty, absolute phase, startup, lock loss and restart sequencing remain requirements, not assumed values. MCLK, BCLK and FS continuity must be maintained or their loss handled deliberately before enabling outputs. A 24.576 MHz source alone does not prove an exact 1 GHz core clock; the maximum-grade compute table is a separate envelope.

## 10. Preliminary power inventory

Currents below retain their original conditions. UNKNOWN design maxima must be closed before regulator sizing; an idle/typical current is not a regulator rating. No regulator or power tree is selected.

| Device/domain | Nominal / permitted voltage | Typical current | Maximum or design-discovery bound | Startup/sequencing/noise and source |
| --- | --- | --- | --- | --- |
| Four microphones, normal |2.75 V example /2.3-3.0 V|4*170=680 uA|4*230=920 uA only at MIC Table 7 conditions; high-SPL/load corner UNKNOWN|Separate low-noise rail/filtering; 100 nF/device, ramp/startup constraints. MIC Tables 5-7. |
| Four microphones, low-power alternative |1.6 V /1.52-1.8 V|280 uA|320 uA at table conditions|Lower SNR/AOP; unselected. A nominal 1.8 V tolerance can exceed maximum. MIC Tables 3, 6-7. |
| ADC AVDDx with internal LDO |3.3 V /3.0-3.6 V|14 mA at default 48 kHz conditions|96-kHz worst-case and added DVDD discharge load UNKNOWN|Quiet analog supply; reference/LDO bypass and POR discharge. ADC pp.4, 12-13. |
| ADC IOVDD |3.3 V example /1.62-3.6 V device limit|0.88 mA at 96 kHz, 256fs MCLK table conditions|Full loading/tolerance maximum UNKNOWN|Logic ceiling must be narrowed for direct DSP drive. ADC Tables 2-3. |
| ADC DVDD |1.8 V internal /1.62-1.98 V|External-DVDD mode table gives 4.5 mA at 48 kHz; not an extra external rail in preferred internal-LDO mode|Bleeder current 1.8/3000=0.6 mA in illustrative reset network, plus core load|Do not tie internal regulator output to DSP reference rail. External-DVDD mode requires separate verification. ADC pp.4, 12-13. |
| DSP VDD_INT |1.00 V /0.95-1.05 V|1.157 A at 1 GHz, 25 C, documented activity/DMA; 0.946 A at 800 MHz|Illustrative 1 GHz, 1.05 V, 125 C subtotal **2.0605 A before DMA/accelerator/DCLK/OCLK contributions**, below; final peak/transient rating UNKNOWN|Supply dynamic demand and supervisor behavior matter; DSP pp.47-50, DSPPOWER. |
| DSP VDD_EXT |3.30 V /3.13-3.47 V|UNKNOWN until pin loads/toggle counts allocated|Use EE-414 sum over C*V*f, activity, output count; do not use SOM regulator rating as load|Must track REF/ANA delta; push-pull receiver maximum may force tighter rail. DSP p.44; POWER. |
| DSP VDD_REF |1.80 V /1.71-1.89 V|EE-414 model:0.4 mA per switching I/O <=32 MHz, plus 5 mA oscillator contribution|Additional 18 mA OTP contribution per model; exact scenario/population maximum UNKNOWN|Mandatory decoupling at least 10 nF and 100 nF; SYS_CLKIN0 domain; source/sink and sequence matter. DSP Table 8; DSPPOWER p.9. |
| DSP VDD_ANA |1.80 V /1.71-1.89 V|HADC 2.0 mA idle/2.5 mA converting, 40 uA powered down, typical|Complete ANA/TMU corner maximum UNKNOWN|Can potentially source from REF as DSP Table 18 permits; filter and maintain delta. Revision 0.0 TMU/HADC unusable. DSP pp.43, 51; ANOM. |
| DSP VDD_DMC |1.35 V /1.283-1.418 V DDR3L; or 1.50 V /1.425-1.575 V DDR3|UNKNOWN|Activity/load-dependent; external DDR memory consumption additional|Keep domain in inventory even if RAM omitted. Unused-DMC supply/reference disposition must be verified, not grounded by assumption. DSP pp.44, 53. |
| DDR reference if used |0.5*VDD_DMC /0.49-0.51*VDD_DMC|UNKNOWN|Receiver reference; no load budget yet|Memory choice and clock/termination constraints unselected. DSP p.44. |
| AMP PVDD |Nominal 12 V project /4.5-26.4 V|75 mA idle, all channels play/no audio at 14.4 V|90 mA idle maximum; audio current depends on four-channel output, efficiency, load and transients|High-current local bypass/bulk, switching return management. AMP p.7, §11. |
| AMP VBAT |Nominal 12 V project /4.5-18 V|90 mA idle at 14.4 V|100 mA idle maximum under table conditions; full operating budget not closed|Gate-drive source; may share PVDD only within VBAT limit. AMP pp.5, 7. |
| AMP VDD |3.3 V /3.0-3.5 V|15 mA, channels play at-60 dB|18 mA under table conditions; add external pulls/drivers separately|Narrow high-voltage bound for DSP drive; POR/I2C delay and silent startup. AMP pp.7, 10, 27. |
| AMP bypass nodes |GVDD/AVDD/VREG/VCOM internal|Not external load rails|No external fanout approved|Required bypass returns and bootstrap network; AMP pp.5-8, 23. |
| AFE, oscillator/fanout, flash, debug, protection |UNKNOWN|UNKNOWN|UNKNOWN|Must be added to total input budget after requirements/component choices. |

DSP high-corner subtotal derivation (not a complete maximum): DSP Table 21 leakage 880 mA + Table 23 dynamic 749 mA*ASF1.09 + EE-414 clock terms 1.05*(0.626*500 +0.23*125 +0.02*250)=**2060.4975 mA**. This uses allowed 1 GHz/500 MHz/125 MHz/250 MHz conditions at 125 C, leaving DCLK/OCLK/accelerators and DMA outside the subtotal. It demonstrates why 1.157 A typical alone is inadequate. Junction temperature and workload are not approved product assumptions.

Potential sharing: ADC I/O, DSP EXT, amplifier logic and compatible flash could use one tightly specified domain after logic-margin and sequencing review. ADC analog 3.3 V may need separate filtering from that domain; microphone normal supply cannot share 3.3 V. DSP REF/ANA can potentially share 1.8 V per manufacturer guidance, while ADC internal DVDD is not a distribution source. PVDD/VBAT may share the nominal 12 V input only when U22 transients/range are bounded. Switching-power filtering/isolation means controlled current paths; no arbitrary ground-plane split is prescribed.

Mandatory DSP relationship throughout startup, reset and shutdown: abs(VDD_EXT-VDD_REF)<=1.89 V and abs(VDD_EXT-VDD_ANA)<=1.89 V. EE-470 recommends bringing REF up before EXT to mitigate indeterminate I/O drive, while preserving these inequalities. A logic output may drive during ramp even while nominally a reset input. Cross-device powered-off inputs, pull-ups, mute and flash selects need a system state matrix.

## 11. Boot/debug findings

| SYS_BMODE[2:0] | Documented mode |
| --- | --- |
|000|No boot|
|001|SPI2 flash|
|010|External SPI2 host|
|011|External UART0 host|
|100|External LP0 host|
|101|Octal SPI flash|
|110/111|Reserved|

Source: DSP p.18 Table 7, HRM Ch.40 and BOOT. SPI2 flash boot is the **provisional production/development recommendation**, with JTAG and recoverable UART0/host access. Boot ROM loads executable images into memory; it does not supply an ANC application. Flash capacity, image layout, interrupted-update recovery, authentication and calibration retention require U26/U27 decisions. No OTP/fuse provisioning is proposed.

The official SOM demonstrates **ISSI IS25LP512M serial flash on SPI2**, with quad data pins. This is compatible-reference evidence, not approval of that exact production flash suffix/capacity or its current lifecycle. A production alternative must match boot read protocol, initial bus mode/addressing, reset/power timing, voltage and loader image expectations. BOOT discusses init blocks, boot streams and second-stage/customization options; exact flash verification must accompany later selection.

Critical DSP ball/peripheral mapping, from DSP pp.27-28, 89-94:

| Function | Signal / ball |
| --- | --- |
| Boot straps | BMODE0 B10; BMODE1 B09; BMODE2 A 08 |
| Reset / status | SYS_HWRST A 09; SYS_RESOUT C10; SYS_FAULT A 11 |
| System clock | SYS_CLKIN0 N01; SYS_XTAL0 L01 (leave XTAL unconnected for external oscillator) |
| JTAG | TCK B11; TMS C12; TDI C13; TDO C11; TRST A 10 |
| SPI2 flash | CLK PA04/R01; MISO PA00/N03; MOSI PA01/P03; SEL1 PA05/T02; quad D2 PA02/P02 and D3 PA03/R03 |
| UART0 | TX PA06/T03; RX PA07/V01; these share other peripheral functions |

JTAG uses VDD_EXT 3.3 V signaling, target voltage reference, grounds and appropriate probe reset access. EE-68 p.6 requires 4.7 kilohm TRST pulldown for its ordinary single-target arrangement; its old 14-pin/probe examples must not be silently mapped to a modern 10-pin header. The SOM manual documents a 10-pin0.05-inch header and ICE-1000/ICE-2000 use. Select and verify the actual probe, header pinout, adapters and CCES license under U29 before schematic entry. JTAG halting interrupts real-time control, so future output-safe debug behavior must be defined. UART logic is not RS-232/USB without the appropriate interface circuitry.

For the control plane, ADC and amplifier have nonoverlapping selectable 7-bit address sets. A DSP TWI master is feasible in principle; reserve boot SPI2 and UART0 recovery pins before multiplexing. No bus ownership, connector or pin assignment is approved. Reset/clock availability must allow ADC PLL initialization and amplifier configuration without accidentally enabling output.

## 12. Reference-design findings

| Reference | Inspected lessons | Device-required versus board-specific |
| --- | --- | --- |
| MIC datasheet + official KIT_IM73A135V01_FLEX product page | Load/bypass/port drawings; kit supplies five single-mic flex boards and adapter for evaluation. | MIC loading, supply and handling constraints apply. Flex cable capacitance and adapter network require verification; separate kit schematic was not obtained. Product page alone is not electrical proof. |
| ADCEVAL UG-600 pp.3-7, schematics pp.10-15, ADC Fig.44 p.43 | Configurable input coupling, references, clock/control selection; buffered and unbuffered digital outputs. | ADAU1977 boost/mic-bias/10 Vrms circuits and optional +/-20 V test rails are **not** ADAU1978 requirements. ADAU1978-specific coupling selection is documented on p.7. Rev.B reset changes postdate the 2014 guide. |
| SOM manual and Rev.A schematic (especially sheets 7-11) | Power domains, SI5356A clock generator with 25 MHz system and 24.576 MHz audio outputs, SPI2 flash, DDR3L, UART and JTAG access; sheets distinguish rails/reset/boot from connector functions. | RAM size, USB bridge, power parts and 25 MHz oscillator are evaluation choices. DSP pin/rail limits and EE-470/anomalies override older board practice. |
| AMPEVAL SLOU453A pp.20-26 (schematics pp.22-23) + AMP Figs.79/82 | Heatsink, bypass, bootstrap capacitors, LC components, high-current returns and audio/control interface. | Heatsink and output filtering follow device requirements. Evaluation board copper, layer count, connectors, source current and filtering are not automatically this product's specification. |
| REF733 TIDA-00733 §§2.3.3-2.3.4, pp.18-23 |96 kHz TDM8 with 32-bit words and 24.576 MHz bit clock; buffered clocks/data; enclosure used for cooling/shielding and power-input filtering. | Establishes an official implemented mode; uses different ADCs and eight outputs. Buffer/fanout and source/output phase still require independent timing review. Its test results cannot certify this board or resolve AMP's conflicting clock text. |
| INDUCTOR SLOA242A pp.1-8 | Inductance under current, saturation behavior, winding resistance and thermal loss matter at high PWM frequency. | Device minimum inductance/current constraints apply; exact inductor/filter choice depends on U19-U21/U38/U39. |

TIDA-00743 was also located on TI's official design page; it is indexed as an additional reference, not claimed as a fully reviewed design. No reference hardware was copied into production KiCad files.

## 13. Errata findings

**DSP:** NR004735J, January 2026, was checked for all 21 listed anomalies and revisions 0.0/0.2. The product-page date is older than the actual document. Read the branded revision and TAPC0_IDCODE.REVID; ordering speed/package alone does not establish silicon revision. No sample/device was interrogated in this task.

| Anomaly IDs | Revisions | Impact / required disposition |
| --- | --- | --- |
|20000002, 20000069, 20000096|0.0, 0.2|Core instruction/register hazards with stalls or non-L1 accesses; apply compiler/toolchain workarounds or specified instruction separation; affects trustworthy DSP results. ANOM pp.3-5.|
|20000003|0.0, 0.2|Nonsecure SPU/SMPU MMR access can error; respect restricted access regions. p.3.|
|20000031|0.0, 0.2|First external-clock timer event one edge late; relevant if used for timing/measurement. Adjust initial period as documented. p.4.|
|20000062|0.0, 0.2|SPI_SLVSEL writes require duplicate back-to-back write; control/flash driver implications. p.4.|
|20000072|0.0, 0.2|Floating-point F0 instruction sequence can stall; execution budget/toolchain impact. p.5.|
|20000097|0.0, 0.2|SMPU11 reports but does not block writes to SPI flash mapped space; use OSPI protection and register protection if relying on it. p.5.|
|20000098, 20000099|0.0|ROM error fault not raised; OSPI DTR boot timing failure. Use documented init/error hook and STR-first/read-delay workaround if relevant. p.6.|
|20000100|0.2|Incorrect HADC channel-mask reset; explicitly initialize supported channels before use. p.6.|
|20000103|0.0, 0.2|S/PDIF Rx clock pulse width unreliable above 96 kHz. Proposed direct clock path does not use this output; do not inherit it from eval routing. p.7.|
|20000104|0.0, 0.2|Stale L2/L3 reads with cache disabled and prefetch enabled; memory/DMA ownership and configuration matter. p.7.|
|20000105|0.0|HADC/TMU nonfunctional. Do not rely on internal thermal monitor for protection on this revision. p.7.|
|20000106|0.0, 0.2|DCLK from CGU1 unreliable; generate DCLK from CGU0. p.7.|
|20000117, 20000124|0.0, 0.2|DMC PHY calibration issue; ROM DMC-init routine unusable. Use current documented calibration in initcode/application; old evaluation initialization is not sufficient evidence. pp.8-11.|
|20000123|0.0, 0.2|Page-mode/secure boot ignore blocks can fail across 1024-byte boundaries; avoid affected ignore blocks. p.11.|
|20000128|0.0, 0.2|IRPTL writes can clear pending FIR/IIR completion interrupts. Avoid offending writes or use SEC routing as documented. Critical if accelerator compute is credited. p.12.|
|20000129|0.0, 0.2|ROM OTP write API can fail with leaky bit; obtain updated ADI OTP service library before any eventual provisioning. p.12.|
|20000134|0.0|DCLK above 500 MHz unreliable; limit accordingly if DDR used. p.12.|

**Additional DSP documentation inconsistency:** DSP p.17 describes eight SPORTs and HRM Table 27-2 lists SPORT0 through SPORT7 DMA channels, but DSP Tables 36-37 (pp.57-58) footnotes say their specifications apply to four SPORTs. The scope of those timing guarantees across all eight is **CONFLICTING/UNKNOWN**. The current resource example uses SPORT0A/B; no additional high-numbered SPORT is needed or approved. Obtain clarification before extending the timing contract to SPORT4-7.

No listed anomaly was found that categorically prohibits the proposed 96 kHz SPORT/DMA transport. This is not a claim that all operating modes are anomaly-free. Silicon revision and toolchain support are open production controls.

**ADC:** No separate official silicon-errata publication was located in the product index/search. Rev.B changes to reset/PLL initialization are materially relevant and were reviewed. HPF conflicting values remain unresolved; a stray p.22 I2C prose discussion around 1 Mbps does not authorize exceeding Table 5's400 kHz maximum. Do not import boost/bias features from reused prose. Absence of a separate errata file is not confirmation that no anomalies exist.

**Amplifier:** No separate official errata publication was located in the product index/search. SLOS870B revision history, clock conflict, startup, 96-kHz PWM behavior, protection and external networks were reviewed. Rev.B's two MCLK/SCLK instructions remain unresolved; no forum assertion is accepted as an electrical limit. SAP 32-bit prose/register wording is avoided by selecting the documented 24-bit use case.

**Microphone:** No separate official errata found in the reviewed product index/search; MIC revision history and operating/assembly limits inspected. Supply-mode gaps and upper supply stress limit must be respected. Qualification/lifecycle requirements remain project choices; component ingress rating does not certify an assembled product.

## 14. Phase 0 unknowns resolved or narrowed

The frozen Phase 0 artifact is preserved as historical baseline. This table is the Phase 1 delta record; it does not silently overwrite a product requirement. Every U-row previously had status UNKNOWN. A confirmed subfact below does **not** close the whole requirement. No U-row becomes CONFIRMED; all 44 remain UNKNOWN at requirement level, with the following closure work recorded.

| ID | Previous -> new requirement state | Component evidence gained / reason still open; closure needed |
| --- | --- | --- |
|U01|UNKNOWN -> UNKNOWN|MIC 20 Hz roll-off and AMP HPF constrain band; product must define ANC band/cancellation/test method.|
|U02|UNKNOWN -> UNKNOWN|Four physical inputs verified; approve reference/error role map. No assumed four references plus four errors.|
|U03|UNKNOWN -> UNKNOWN|Datasheets cannot supply geometry/preview/path responses; acoustics evidence needed.|
|U04|UNKNOWN -> UNKNOWN|MIC port/100 pF loading constrains remote placement; installation and board deliverable decision needed.|
|U05|UNKNOWN -> UNKNOWN|MIC sensitivity/AOP and ADC full scale confirmed; acoustic SPL/crest/headroom budget still needed.|
|U06|UNKNOWN -> UNKNOWN|MIC disjoint supply/current/startup/decoupling confirmed; choose mode and noise/tolerance/loaded-current budget.|
|U07|UNKNOWN -> UNKNOWN|MIC >=25 kilohm/<=100 pF and VCM load network confirmed; actual gain/noise/coupling/fault-safe AFE unresolved.|
|U08|UNKNOWN -> UNKNOWN|ADC bias/full-scale/resistance/reference/network known; DC tolerance/powered-off injection and gain/headroom contract incomplete.|
|U09|UNKNOWN -> UNKNOWN|Published MIC/ADC performance inspected; approved system SNR/THD/calibration acceptance absent.|
|U10|UNKNOWN -> UNKNOWN|ADC HPF conflict remains; documented HPF disable option and AMP 96-kHz 8 Hz default identified; product phase/amplitude mask needed.|
|U11|UNKNOWN -> UNKNOWN|Derived 239.42 us ADC +125 us AMP; no worst-case complete delay/preview/jitter/skew limit supplied.|
|U12|UNKNOWN -> UNKNOWN|Parametric workload envelope supplied; tap lengths/topology/update/block size need approved definition.|
|U13|UNKNOWN -> UNKNOWN|DSP storage/resources available; path-identification method/excitation/storage policy not a datasheet decision.|
|U14|UNKNOWN -> UNKNOWN|Hardware protection documented; convergence/adaptation/clipping and acoustic limits require controls requirements.|
|U15|UNKNOWN -> UNKNOWN|Core cycles/SRAM/DMA/errata confirmed; full worst-case cycles and reserve await workload/toolchain/benchmark.|
|U16|UNKNOWN -> UNKNOWN|Explicit TDM4/TDM8 hypotheses and fields documented; AMP clock conflict and final electrical/frame contract open.|
|U17|UNKNOWN -> UNKNOWN|24.576 MHz/PCG/ADC PLL options established; source, phase, jitter, loading and startup not selected.|
|U18|UNKNOWN -> UNKNOWN|DSP supports ASRC but permission/latency effect is a project decision; no lower rate assumed.|
|U19|UNKNOWN -> UNKNOWN|AMP power ratings tied to supply/load/distortion confirmed; required 12 V simultaneous output envelope missing.|
|U20|UNKNOWN -> UNKNOWN|AMP BTL2 ohm minimum nominal load and 4 ohm ratings known; real speaker impedance/excursion/ratings needed.|
|U21|UNKNOWN -> UNKNOWN|LC/diagnostic/load constraints documented; cable/hot-plug/connector requirements needed.|
|U22|UNKNOWN -> UNKNOWN|PVDD/VBAT and mic/DSP limits constrain input conversion; actual source min/max/transients missing.|
|U23|UNKNOWN -> UNKNOWN|Idle/current and power calculation framework known; source capacity/inrush/peak duration not specified.|
|U24|UNKNOWN -> UNKNOWN|All major device rails and critical DSP sequencing inventoried; AFE/flash/load currents, rail margins and power-off matrix incomplete.|
|U25|UNKNOWN -> UNKNOWN|Unboosted 12 V ideal 4 ohm ceiling18 W; no boost requirement/permission can be inferred without output target.|
|U26|UNKNOWN -> UNKNOWN|SPI2/host/OSPI boot verified; SPI2+recovery recommendation is provisional, startup policy undefined.|
|U27|UNKNOWN -> UNKNOWN|SOM flash example/ROM image and anomaly requirements known; image size/update/security/endurance unknown.|
|U28|UNKNOWN -> UNKNOWN|1664 KiB total internal SRAM and DDR support confirmed; external RAM necessity depends on U12/U15.|
|U29|UNKNOWN -> UNKNOWN|JTAG pins/domain/SOM header/probe examples verified; actual tooling/license/header/access decision open.|
|U30|UNKNOWN -> UNKNOWN|UART0 and multiplexed pins known; console/service/electrical-interface specification absent.|
|U31|UNKNOWN -> UNKNOWN|ADC I2C/SPI, AMP I2C, address sets and DSP TWI resources verified; ownership/pulls/mux/speed allocation open.|
|U32|UNKNOWN -> UNKNOWN|ADC discharge/PLL timing, DSP I/O glitch and AMP automatic clock recovery known; supervisor/watchdog/fault states need approval.|
|U33|UNKNOWN -> UNKNOWN|AMP protection categories and device absolute limits known; external fault severity/duration/recovery criteria absent.|
|U34|UNKNOWN -> UNKNOWN|Actual packages/port/heatsink constrain mechanics; board/enclosure dimensions remain product input.|
|U35|UNKNOWN -> UNKNOWN|BGA 0.8 mm pitch verified; fabrication/stackup decision out of scope.|
|U36|UNKNOWN -> UNKNOWN|Four BTL speaker pairs plus mic/debug/control functions known; connector/harness requirements absent.|
|U37|UNKNOWN -> UNKNOWN|Device ambient/junction limits documented; product environmental qualification/duty not specified.|
|U38|UNKNOWN -> UNKNOWN|AMP requires top heatsink; DSP high-corner power material; ambient/airflow/enclosure cooling decision needed.|
|U39|UNKNOWN -> UNKNOWN|Manufacturer EMI references located; product markets/standards/test setup remain unspecified.|
|U40|UNKNOWN -> UNKNOWN|Manufacturer return/filter/isolation practices identified; coexistence/noise floor acceptance requires product limit and measurements.|
|U41|UNKNOWN -> UNKNOWN|Current manufacturer lifecycle checked; volume/budget/horizon/alternate strategy unspecified.|
|U42|UNKNOWN -> UNKNOWN|Mic port/reflow/cleaning and DSP/AMP package constraints known; assembler process/capability/inspection acceptance needed.|
|U43|UNKNOWN -> UNKNOWN|Boot/debug and diagnostic capabilities known; factory test/calibration coverage and limits remain to define.|
|U44|UNKNOWN -> UNKNOWN|Device protections cannot define safety/acoustic malfunction acceptance; product obligations/limits needed.|

| Conditional/conflict ID | Previous -> new | Disposition |
| --- | --- | --- |
|X01|UNKNOWN applicability -> UNKNOWN applicability|Eight physical microphones would exceed baseline; no role map requiring them established.|
|X02|UNKNOWN applicability -> UNKNOWN applicability|Delay screening confirmed as calculation; suitability requires U11 and acoustic preview.|
|X03|UNKNOWN applicability -> CONFIRMED direct-load mismatch|MIC Table 6 versus ADC Table 1/Fig.16 rejects direct drive within documented load envelope. Intended buffered AFE remains PROVISIONAL, not rejected.|
|X04|UNKNOWN applicability -> UNKNOWN applicability|12 V headline-wattage/heatsink conditions still depend on U19/U25/U38; no invented conflict.|
|X05|CONFLICTING -> CONFLICTING|ADC HPF mismatch persists. AMP general/TDM SCLK ratio discrepancy narrowed by mode-specific evidence; additionally tied-clock versus non-in-phase conflict recorded. Manufacturer clarification or accepted alternate needed.|

## 15. Remaining unknowns

All U01-U44 retain closure actions above. Important component-level unknowns and their resolution:

| ID | Unknown | Required evidence |
| --- | --- | --- |
|E01|TAS6424 MCLK/SCLK permitted phase and TDM ratios|Manufacturer-controlled correction/clarification for exact variant/revision, including valid edge separation and duty; or verified alternate.|
|E02|Final digital I/O noise and timing margins|Bound rail maxima, loading, driver strength, PCG/SRU path, jitter/skew and hold; use official timing/IBIS and later measured corners.|
|E03|ADC configured LF transfer function|ADI clarification of Table 4 versus p.14 or formally planned characterization; decide whether documented bypass is acceptable under U10.|
|E04|AFE worst-case analog and off-state compatibility|Approved SPL/noise/bandwidth requirements, then AFE device limits and analog/power-off interface proof in authorized phase.|
|E05|Actual DSP silicon/toolchain anomaly disposition|Procurement revision constraints and toolchain support matrix; hardware ID check and relevant validation later.|
|E06|Complete currents, unused-DMC treatment and thermal budget|Allocate peripherals/AFE/flash/RAM, close unused-domain guidance, use EE-414 worst-corner models and actual load/ambient.|
|E07|Production flash/probe exact compatibility|Select exact nonvolatile and tool/header variants; inspect manufacturer timing/protocol and supported recovery/update path.|
|E08|ANC computational/latency feasibility|Approved signal roles, tap counts and causal acoustic budget; subsequent measured worst-case benchmark, not processor marketing.|

## 16. Component decision matrix

These are exactly one recommendation per candidate, not approved project decisions.

| Component | Recommendation | Reason / critical evidence | Unresolved issues / downstream impact |
| --- | --- | --- | --- |
|Infineon IM73A135V01|**PROVISIONALLY APPROVED**|Exact analog differential identity, pinout, supply modes, noise/headroom/loading available (MIC Tables 1, 3, 6-8).|Buffering required; SPL/noise/band/placement and loaded-current envelope incomplete. No direct ADC connection approved.|
|Analog Devices ADAU1978|**PROVISIONALLY APPROVED**|Four-channel 96 kHz/24-bit TDM4 capability, pinout, clocks and reset documented (ADC Tables 1, 5, 9-10, 19-23).|AFE and logic/clock contract incomplete; HPF conflict and latency acceptance open.|
|Analog Devices ADSP-21569|**PROVISIONALLY APPROVED**|SPORT/TDM/DMA resources, pin map, SRAM, boot and supply conditions support continued candidate evaluation (DSP/HRM/ANOM/POWER).|Exact workload feasibility and silicon/grade/boot/thermal/power corner decisions open; no FxLMS throughput guarantee.|
|Texas Instruments TAS6424-Q1|**BLOCKED BY MISSING EVIDENCE**|TDM/96 kHz/24-bit and power/package documented, but complete clock contract cannot be approved because AMP §§9.3.1.4-5 conflict.|Resolve clock phase/ratio rules and full timing/logic margins before architectural selection; load/power/cooling and latency still conditional.|

Rejected hypotheses: MIC on 3.3 V; a continuous 1.52-3.0 V microphone operating range; direct MIC->ADC drive within present load specifications; ADC 1.8 V->DSP direct signaling; 49.152 MHz amplifier MCLK at 96 kHz; unsupported 96fs packed24-bit AMP TDM; full-range nominal 3.3 V compatibility without threshold analysis; 75 W at 12 V as an amplifier guarantee. None of these rejection decisions changes a confirmed requirement.

## 17. Architecture blockers and acceptance review

**B1 - Critical component-selection blocker:** unresolved TAS6424-Q1 MCLK/SCLK contradictory requirements (E01). This prevents the acceptance condition that no critical component-level uncertainty obstructs architectural work. Documented mode support alone is insufficient.

**B2 - Electrical contract blocker:** no approved supply/load/noise-margin and timing envelope for direct DSP->ADC/AMP drive (E02). This is a resolvable constraint, not proof that the candidates' voltage domains are inherently incompatible. The unrestricted full-range direct-connection hypothesis is rejected; narrower rails or qualified drivers need explicit verification.

**B3 - Filter-response blocker for architecture freeze:** ADC HPF source conflict (E03) and missing U10 mask. The verified bypass capability is an option requiring explicit acceptance and a DC/low-frequency plan, not silent closure.

Phase 0 acoustic, power/load, DSP workload, boot/recovery and production requirements remain schematic-entry blockers. They are distinguished from B1: product questions are not all prerequisites for a bounded architecture study, but **this gate cannot pass while B1 remains**. No unsafe value or alternative component has been chosen to remove a blocker on paper.

| Phase 1 acceptance criterion | Result |
| --- | --- |
|Exact major component identities verified|PASS at device/orderable-family level; procurement grade/suffix not frozen.|
|Authoritative documentation inspected|PASS for cited review regions; all main datasheets and DSP HRM acquired.|
|Exact pinout/package available|PASS: manufacturer maps inspected; 400-ball numerical/alphabetical comparison completed; no symbol certification.|
|Required power rails understood|PASS for major-device inventory/mandatory relationships; final currents and unused-domain disposition explicitly UNKNOWN.|
|Major clock requirements understood|UNKNOWN for conflicting amplifier constraints.|
|ADC->DSP established or clearly blocked|PROVISIONAL candidate defined; B2 electrical closure clearly identified.|
|DSP->AMP established or clearly blocked|Clearly blocked by B1/B2.|
|Boot/debug sufficient for architectural discussion|PASS at capability/pin/boot-method level; exact production flash/probe/update policy unselected.|
|Relevant major errata reviewed|PASS for public retrieved evidence; DSP 21-item list reviewed; other-device standalone errata not found, absence not certified.|
|Unsuitable components rejected|No confirmed-requirement component failure proved; unsupported connection hypotheses rejected.|
|Uncertainties explicit|PASS: Sections 14-15 and B1-B3.|
|No critical component uncertainty prevents architecture work|NOT SATISFIED: B1.|

Verification executed: PDF identity/page-count/SHA-256 integrity; targeted table, waveform and pin/package visual inspection using PyMuPDF; 400-ball dual-list consistency; reproducible clock/logic/latency/workload/power arithmetic and Phase 0 row coverage. See `validation/phase_1/verification_results.json` and `verify_evidence.py`. Automated results establish only their stated checks. ERC/DRC: **NOT APPLICABLE**, no KiCad files created or modified. Oscilloscope testing, acoustic characterization, SPICE/IBIS simulation, thermal simulation, hardware boot and DSP benchmarking: **NOT EXECUTED**.

## 18. Risks

| Risk | Cause -> consequence | Evidence | Mitigation / residual uncertainty |
| --- | --- | --- | --- |
|Critical: clock interpretation|Conflicting MCLK rules -> clock faults, unintended restart or absent audio|AMP p.19|Close B1 with manufacturer evidence; bench success alone does not define silicon limits.|
|High: digital logic/timing|Insufficient guaranteed VOH or small 24.576 MHz margin -> corrupt/misaligned samples|DSP pp.44, 47, 57, 87; ADC p.3; AMP pp.8, 10|Tighter rails/qualified drivers and full timing analysis; final margins UNKNOWN.|
|Critical: power/reset glitches|DSP domain differential or ramp I/O drive -> damage, boot faults, unintended amplifier control|POWER; DSP p.53|Sequence/supervise domains and design safe pin states; system response UNKNOWN.|
|High: AFE loading/noise|Unbuffered microphone/incorrect bias or gain -> reduced SNR, overload, LF phase error|MIC Tables 6-7; ADC Table 1|Close analog contract and product SPL/band requirements; topology not designed.|
|Critical: acoustic feasibility|Converter/amplifier delay plus insufficient preview -> ineffective/unstable ANC|ADC Table 4; AMP p.10; U01-U03/U11|Define acoustic geometry/band/latency before sign-off; no generic delay target.|
|High: compute deadline|Undefined taps/workload, memory stalls or accelerator interrupts -> missed deadlines|HRM; ANOM; Section 5 envelope|Worst-case budget/benchmark with toolchain workarounds; exact feasibility UNKNOWN.|
|High: output power/thermal|Unknown load/source and top-heatsink envelope -> clipping or shutdown|AMP pp.7, 52, 56-57|Four-channel power and cooling assessment at minimum input/maximum ambient; U19-U23/U38 open.|
|High: power under-sizing|Typical DSP current used as maximum -> core rail collapse|DSP p.50; DSPPOWER|Complete worst-corner/peak model, including flash/AFE/clock loads; current subtotal is not final.|
|High: Class-D interference|High-current switching/cables contaminate mic/ADC or emissions|AMP Ch.12; REF733; INDUCTOR|Return-path, filtering and coexistence validation; no EMC claim.|
|High: boot/update recovery|Unmanaged ROM/silicon/flash behavior -> unbootable product|BOOT; ANOM IDs20000123/124/129|Revision-aware boot image and recovery requirements; no irreversible provisioning.|
|High: low-frequency output|Small bootstrap reserve near clipping, HPF conflict -> distortion/phase mismatch|AMP p.52; ADC pp.4, 14|Define LF envelope and verify capacitor/HPF behavior; ANC band still UNKNOWN.|
|High: manufacturing|BGA escape, mic contamination, top heatsink incompatible with process|DSP package; MIC Ch.7; AMP Ch.12|Assembler/fabricator/mechanical review before schematic entry; no stackup selected.|

## 19. Recommended Phase 2 scope

**Recommendation only, conditional on closing Phase 1 blockers and explicit authorization.** First continue Phase 1 closure: obtain controlled amplifier clock clarification or verify an alternate candidate; establish a defensible logic/timing envelope; disposition the ADC HPF conflict. Do not reinterpret this section as permission to enter Phase 2 while blocked.

Once separately authorized and the gate is cleared, Phase 2 should define the system architecture: approved input role/acoustic/latency and output-load envelopes; selected coherent clock topology; signed block interface contracts; preliminary AFE requirements and gain/noise/phase budget; full power/current/sequencing/reset domain matrix; boot/debug/update/recovery architecture; DSP cycle/memory/block-size envelope; and planned validation/acceptance criteria. Regulator detail, AFE circuit design, schematic entry and PCB work need their own later authorization and resolved schematic-entry blockers.

Files created by this review: this report; `docs/evidence/component_evidence_index.md`; authoritative PDFs listed in the index under `datasheets/` and `references/`; source manifest and reproducible verification script/results under `validation/phase_1/`. Existing confirmed requirements and production hardware were not changed. Temporary extracted text, rendered inspection pages and report-assembly helpers remain under `tmp/phase_1/`: automatic approval review rejected their recursive cleanup with "blocked by policy". These are scratch material, not authoritative evidence or additional deliverables.

The phase stops at this gate.

PHASE 1: BLOCKED
