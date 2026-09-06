# Phase 0 — Requirements Freeze

Repository: `circuitBuilderAi-Astra`  
Review date: 2026-09-06  
Scope: requirements baseline and limited manufacturer evidence checks only.

## Project objective

Develop a production-oriented, clean-sheet custom Active Noise Control (ANC) controller PCB with four analog microphone inputs, a four-channel ADC, a dedicated DSP supporting FxLMS / multichannel FxLMS-class processing, and four independent digital-input Class-D speaker outputs. The required audio operating point is 96 kHz / 24-bit, with operation from a regulated nominal 12 V DC source and development programming/debug access.

This document freezes what is known and records what remains open. It does not freeze component selection or certify ANC feasibility. No schematic, PCB, placement, routing, KiCad artifact, component interconnection, or firmware implementation is specified here. No decisions from another project have been adopted.

## Review basis and status definitions

All repository documentation present at review was read:

| Repository source | Finding |
| --- | --- |
| `AGENTS.md` | Placeholder for project instructions; no additional engineering constraints. |
| `README.md` | Repository identification only. |
| `MASTER_SPEC.md` | Placeholder; no consolidated specification yet. |
| `docs/architecture.md` | Placeholder; no approved architecture. |
| `docs/decisions.md` | Placeholder; no recorded decisions. |
| `docs/phases/phase_0_requirements_freeze.md` | Placeholder before this review; replaced by this document. |

The remaining files outside Git metadata were `.gitkeep` placeholders under `datasheets/`, `hardware/kicad/`, `references/donor_boards/`, and `validation/`. No local datasheets, donor designs, hardware files, or validation results were supplied. Existing untracked repository content was preserved; only this document was changed.

Evidence **U0** means the user's Phase 0 project brief in this session, captured by the objective and confirmed requirements below. Repository placeholders are not evidence of an engineering decision. Manufacturer sources are identified in the candidate evidence section with document revisions and locators; they were accessed on the review date. Their relevant sections were screened, not exhaustively verified. No evaluation-board design was inherited.

- **CONFIRMED**: explicitly required by U0, or an independently sourced component fact clearly identified as such. A confirmed component capability does not confirm component suitability.
- **PROVISIONAL**: user-described candidate/intention, or a clearly labeled engineering proposal awaiting verification and acceptance.
- **UNKNOWN**: absent, unverified, or insufficiently quantified; no default value has been assigned.
- **CONFLICTING**: incompatible explicit statements or conflicting source evidence. A possible future incompatibility is a conditional risk, not a fabricated current requirement.

Requirement IDs below are stable review references. Proposed owners identify needed expertise, not assigned people. No numeric acceptance threshold is implied where one is unknown.

## Confirmed requirements

All entries in this table are **CONFIRMED**, source U0. Their unresolved details are separately classified below.

| ID | Requirement | Boundary of confirmation / material impact |
| --- | --- | --- |
| C01 | Clean-sheet, production-oriented custom ANC controller PCB. | No inherited design authority; production volume, cost, quality and qualification targets remain open. |
| C02 | Four analog microphone input channels. | Electrical levels, physical location, and reference/error assignment are not defined. Affects acquisition and connectors. |
| C03 | Four-channel ADC. | Candidate model and analog interface are unapproved. |
| C04 | Dedicated DSP with real-time, low-latency ANC processing. | Maximum delay and sustained compute requirement are unknown. |
| C05 | FxLMS / multichannel FxLMS-class processing capability. | No algorithm variant, filter lengths, acoustic geometry or proven convergence target supplied. |
| C06 | 96 kHz / 24-bit audio processing. | Does not specify 24 effective analog bits or the DSP arithmetic format. No lower ANC processing rate is authorized as a substitute. |
| C07 | Four independent speaker outputs using digital-input Class-D amplification. | Output power, load and simultaneous duty remain unknown. Combining channels cannot satisfy four independent outputs. |
| C08 | Operation from a regulated nominal 12 V DC source. | No tolerance, current capacity, transient envelope or permission/need for internal boost conversion is established. |
| C09 | Development-suitable debugging and programming interfaces. | Specific probe, connector, UART exposure and production programming method are unknown. |
| C10 | Work stops at Phase 0. | Only this requirements artifact is produced; subsequent scope is recommendation only. |

## Provisional requirements

All entries are **PROVISIONAL**. P01–P02 originate in U0; P03–P07 are review proposals, not approved additions.

| ID | Candidate requirement or proposal | Assumption / evidence needed |
| --- | --- | --- |
| P01 | Four microphones → low-noise analog front end → four-channel ADC → TDM4 → DSP → TDM4 → four-channel amplifier → speakers. | Intended functional path only. Gain, coupling, clock ownership and actual electrical compatibility remain open. |
| P02 | IM73A135, ADAU1978, ADSP-21569, TAS6424-Q1 as major candidates. | Exact orderable variants and suitability require verification against the completed requirements. |
| P03 | Coherent sampling and deterministic channel timing across acquisition and playback. | Proposed ANC requirement; allowable skew, phase error and drift need quantitative limits. |
| P04 | Evaluate four 32-bit TDM slots carrying 24 significant audio bits. | A compatibility hypothesis, not an approved bus configuration; see timing analysis. |
| P05 | Autonomous boot from nonvolatile firmware storage, with a recoverable programming path. | Production use suggests standalone operation, but host dependence and recovery policy require acceptance. No flash type/capacity selected. |
| P06 | Evaluate JTAG development access and a UART service/logging interface. | C09 is confirmed; these particular implementations are proposals pending tool and access requirements. |
| P07 | Define a controlled silent state on boot, reset, clock loss, software failure, and invalid calibration. | Proposed product behavior; output limits, response times, independence from firmware and restart policy are unknown. |

## Unknown requirements

Every entry in the following tables is **UNKNOWN**. The final column states what must be decided or demonstrated before schematic design. These are required clarification topics, not silently selected specifications.

### Acoustics, microphones and acquisition

| ID | Missing requirement | Material impact and closure evidence |
| --- | --- | --- |
| U01 | ANC application, noise spectrum, controlled frequency band, cancellation in dB, protected spatial region and measurement method. | Determines whether the signal path can meet the objective at all. Product/acoustics owner to define representative noise, baseline, measurement locations and pass/fail criteria. |
| U02 | Reference microphone count, error microphone count, feedforward/feedback/hybrid topology, other reference sources. | Determines channel budget and DSP matrix dimensions. Approve a role map for all four physical inputs; identify any synthesized references explicitly. |
| U03 | Microphone/speaker geometry, primary-path preview, secondary-path responses and environmental variation. | Sets causality, filter duration and achievable control band. Supply geometry and representative impulse responses or an approved measurement plan. |
| U04 | On-controller versus remote microphones; whether microphone modules are in the PCB deliverable. | Affects board count, analog cable exposure, supply distribution, connectors and acoustic port design. Specify mounting, cable lengths, shields and installation. |
| U05 | Minimum/nominal/maximum microphone SPL, crest factor, overload recovery, and required signal voltage at microphone and ADC. | Defines headroom and gain. Provide an acoustic-to-electrical level budget including tolerance and desired ADC utilization. |
| U06 | Microphone supply mode, rail tolerance/noise, startup time and power budget; any external bias requirement. | Candidate is an active analog MEMS device, not an unspecified electret interface. Approve a supply specification and interface requirements using E-MIC. |
| U07 | AFE input impedance/capacitance, input common mode, gain/range, noise, distortion, bandwidth, coupling and overload behavior. | Determines buffering/gain stages and rails. Resolve E-LOAD; derive gain and coupling from U01/U05 rather than assume a preamp circuit. |
| U08 | ADC drive requirements, common-mode allowance, full-scale mapping, clipping margin and input fault envelope. | Affects ADC selection and AFE. Complete an analog interface contract, including powered-off behavior; candidate facts in E-ADC are not that contract. |
| U09 | Audio SNR/dynamic range, THD+N, crosstalk, channel matching, calibration accuracy and measurement bandwidth/weighting. | Defines achievable audio performance and component acceptance. 24-bit data alone supplies none of these thresholds. |
| U10 | Analog/digital high-pass and anti-alias response; permissible low-frequency phase shift. | Changes ANC loop response and latency. Approve amplitude/phase masks, including interference outside the control band; resolve E-DOC before using a filter corner. |

### DSP, timing and digital audio

| ID | Missing requirement | Material impact and closure evidence |
| --- | --- | --- |
| U11 | Numeric worst-case end-to-end electrical latency, jitter, channel skew, and measurement endpoints. | Can disqualify ADC/amplifier before DSP selection. Define microphone electrical input-to-speaker-terminal delay separately from acoustic propagation and band-dependent group delay. |
| U12 | FxLMS variant, reference/error/output matrix, control and secondary-path filter lengths, update rate and block size. | Determines compute, memory and delay. Approve workload envelope and maximum supported configuration; no tap count is assumed. |
| U13 | Secondary-path identification/calibration method: online/offline, excitation, amplitude/duration, storage and re-identification triggers. | Adds compute, memory, test access and output behavior. Define all speaker-to-error paths and handling of changed installation. |
| U14 | Convergence time, stability criteria, adaptation limits, leakage/normalization, clipping/divergence detection and reference contamination handling. | Determines actual ANC behavior and output protection. Specify acceptance tests for transients, path changes and microphone/speaker faults. |
| U15 | DSP numeric precision, worst-case cycles, memory footprint, reserve margin and concurrent tasks. | Determines speed grade, internal/external RAM and power. Budget DMA, cache/memory contention, interrupts, diagnostics and telemetry; later benchmark the declared worst case. |
| U16 | Exact TDM framing on each link. | Specify slot count/width, valid bits, signed encoding, alignment, padding, channel map, FSYNC polarity/width, bit-clock edge, inactive data behavior and continuous-clock behavior. Validate all endpoints. |
| U17 | Clock source/ownership, MCLK/BCLK/FSYNC frequencies, oscillator accuracy/jitter, synchronization, lock/startup and loss recovery. | Determines clock architecture and latency consistency. Approve a clock-domain plan with timing margin and startup dependencies; no clock master assigned. |
| U18 | Whether rate conversion or lower-rate adaptation is permitted while meeting C06. | Can change compute and delay substantially. Requires an explicit system interpretation, filter/delay budget and acceptance; no ASRC or decimation is assumed. |

### Outputs, power, boot and service interfaces

| ID | Missing requirement | Material impact and closure evidence |
| --- | --- | --- |
| U19 | Continuous and peak output power per channel, peak duration, crest factor, concurrent channel loading and allowable THD+N. | Drives amplifier, source current, cooling and copper/connector needs. Require a four-channel operating envelope at the minimum input voltage. |
| U20 | Speaker nominal/minimum impedance versus frequency, reactive behavior, power rating, sensitivity, excursion and enclosure. | Defines expected load and acoustic authority. Obtain speaker data and installed load characterization; no 2/4/8-ohm choice made. |
| U21 | Speaker cable lengths/gauge, connector grounding, hot-plug and short/open-load conditions. | Changes output-filter requirements, stability, protection and EMI. Specify independent speaker pairs and installation faults. |
| U22 | Input minimum/maximum steady voltage, ripple spectrum, dropout, ramp rates, transients and source impedance. | Sets regulator headroom, undervoltage behavior and protection. Regulated 12 V is insufficient as a full power-input specification. |
| U23 | Available continuous/peak source current, peak duration, inrush limit, allowable voltage droop and standby budget. | Sets power connector, protection, bulk energy and thermal envelope. Complete total input-power budget including conversion losses. |
| U24 | Complete rail inventory, accuracy/ripple, current, sequencing, discharge and externally driven I/O behavior. | Includes microphone/AFE, ADC analog/I/O, DSP domains, amplifier and storage/debug domains. Produce a domain matrix from selected candidates; see E-POWER. No regulator or shared rail selected. |
| U25 | Internal boost permission/need, isolation, auxiliary outputs and power-off behavior. | Can change architecture, cost, EMI and heat. Decide after U19–U23; nominal input alone does not settle internal topology. |
| U26 | Standalone versus host boot, startup deadline, boot medium and fallback/recovery. | Changes storage and service architecture. Approve boot/update states and recovery following incomplete programming. |
| U27 | Firmware image size, update method, calibration/log retention, endurance, integrity and security requirements. | Sets nonvolatile capacity and access method. Decide secure boot/debug access policy before irreversible provisioning; no fuse settings proposed. |
| U28 | External RAM need/type/capacity. | Can change rails, board area, stackup and real-time behavior. Resolve from U12/U15; an evaluation board's RAM is not a requirement. |
| U29 | JTAG/debug probe, connector standard, target voltage, reset access, development tooling/licenses and enclosure accessibility. | Defines development and factory access. Confirm compatible supported tools and programming workflow, including recovery from a blank device. |
| U30 | UART count, function, baud rate, logic/RS-232/RS-485/USB interface, isolation and exposed connector. | Determines transceivers, buses and pins. No console or USB bridge presumed. |
| U31 | I2C/SPI ownership, peripherals, addresses/chip selects, bus speeds, voltage domains and service access. | Defines control-plane feasibility and boot contention. Amplifier/ADC control capabilities are in E-AMP/E-ADC; system allocation remains open. |
| U32 | Reset/supervision thresholds, watchdog coverage, brownout, power cycling and fault recovery policy. | Can affect reliability and unintended output. Approve power/reset/clock state requirements, maximum recovery time and safe output state; include E-POWER. |
| U33 | Input reverse polarity/overvoltage/overcurrent, ESD/surge, output short/DC/overtemperature and microphone fault protection. | Define applicable fault levels, durations, response times and restart behavior at every external interface. Device protection features do not establish board-level acceptance. |

### Physical, environmental and production constraints

| ID | Missing requirement | Material impact and closure evidence |
| --- | --- | --- |
| U34 | PCB outline, maximum size/height, mounting, keepouts, enclosure and allowable separate boards. | Sets architecture and component feasibility. Supply mechanical envelope and microphone acoustic access constraints. |
| U35 | Allowed layer count, stackup/thickness, copper weight, via technology and fabricator capability. | Determines DSP escape and power/EMI feasibility. Obtain fabrication constraints; no four-, six- or eight-layer assumption. |
| U36 | Connector families, pin counts, mating parts, keying, retention, current/voltage ratings, shielding and service life. | Drives area, harness cost and safety. Approve requirements for DC input, microphones, four speakers and debug/service. Pin assignments remain undesigned. |
| U37 | Operating/storage temperature, humidity, vibration, contamination/ingress, reliability life and duty cycle. | Sets component grades and packaging. Automotive candidates do not imply an automotive product qualification requirement. |
| U38 | Thermal ambient maximum, enclosure airflow, heatsink permission/envelope, touch temperature and derating. | Determines sustained all-channel power and feasibility of E-AMP. Specify thermal acceptance with DSP and amplifier active together. |
| U39 | Target markets and applicable EMI/EMC emission/immunity standards, test levels, cable setup and performance during exposure. | Determines filters, shielding, connectors and stackup. Do not assign automotive or consumer limits without product classification. |
| U40 | Acoustic noise floor with Class-D switching and regulators operating; allowed conducted/radiated interference and grounding/chassis constraints. | Mixed-signal coexistence may dominate microphone performance. Define worst-case operating modes and measurable in-band limits. |
| U41 | Prototype/annual volume, BOM and assembly budgets, sourcing/lifecycle horizon and alternate-part strategy. | Can disqualify packages/components. Obtain commercial limits and supply requirements; distributor stock is not qualification. |
| U42 | Assembly/inspection capability, acceptance class, finish, reflow/cleaning, BGA rework and microphone-port protection. | Determines production yield and serviceability. Review process compatibility with all chosen packages, including X-ray/test needs. |
| U43 | Factory programming, functional coverage, acoustic calibration, test-point access, traceability and acceptance limits. | Determines DFT access and stored calibration. Approve production test requirements and fixture concept before schematic design. |
| U44 | Product safety/regulatory obligations and required behavior upon ANC malfunction, including maximum acoustic output. | Affects protection architecture and verification. Define product classification and output limits; no certification claim is made. |

## Candidate architecture

The following is a functional candidate only (P01), with no physical connections implied:

```text
4 analog microphones
    → 4-channel low-noise analog conditioning (implementation UNKNOWN)
    → 4-channel ADC
    → candidate TDM4 acquisition stream
    → dedicated DSP: ANC control + adaptation + monitoring
    → candidate TDM4 playback stream
    → 4 independent digital-input Class-D channels
    → 4 speakers

Supporting functions to specify:
nominal 12 V input and derived power domains; coherent clocks;
boot/storage; reset/supervision; control buses; programming/debug;
fault handling; thermal management; connectors and production test.
```

The acoustic system closes the control loop through the speakers, environment and error microphones. Four analog inputs do not identify that loop. If all references and errors are separate physical microphones on this ADC, their counts must satisfy `R + E <= 4`. A 2-reference/2-error split is only one possible example. Four physical references plus four physical errors would exceed C02/C03; feedback or synthesized-reference schemes must be explicitly specified before applying a different accounting model.

## Candidate major components and evidence

All four component selections remain **PROVISIONAL**. The evidence below confirms only the stated manufacturer capabilities/constraints. Unchecked operating corners, compatibility and product suitability remain **UNKNOWN**. Sources are paraphrased; published typical values are not worst-case guarantees.

### E-MIC — Infineon IM73A135 / IM73A135V01

The screened V01 microphone has active differential analog outputs. Normal-mode supply is 2.3–3.0 V; low-power mode is 1.52–1.8 V. These are separate ranges, not a continuous operating range. Normal-mode current is 170 µA typical, 230 µA maximum under the stated test conditions. Sensitivity is −38 dBV typical at 94 dB SPL, 1 kHz; normal-mode AOP is 135 dB SPL at 10% THD. Table 6 specifies at least 25 kΩ for each resistive load and up to 100 pF for each illustrated capacitive load. See [Infineon datasheet V1.20, 2021-07-07, Tables 3, 6–7 and Figure 11](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im73a135-datasheet-en.pdf).

Derived level illustration: `10^(-38/20) V ≈ 12.6 mVrms` at the sensitivity test point. This is not the required application level or a gain selection. Peak SPL, tolerances and load must define the gain budget. AOP is not a low-distortion operating target. Exact procurement variant and microphone mode remain open.

### E-ADC — Analog Devices ADAU1978

Four differential inputs support 24-bit, 8–192 kHz conversion. Typical full scale/common mode/per-leg resistance: 2 Vrms differential / 1.5 V / 14.3 kΩ. Interfaces include TDM4 and I2C/SPI. Supplies: 3.3 V analog, internally generated core, selectable 1.8/3.3 V I/O. Decimation delay: `22.9844 / fs` at 8–96 kHz. See [ADAU1978 Rev. B, 2024, Tables 1, 4, 9–10; pp. 12–19](https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU1978.pdf).

Derived delay at the required rate: `22.9844 / 96000 ≈ 239.4 µs`. Suitability depends on U11. AFE gain and drive capability remain unselected; digital gain cannot recover signal-to-noise ratio lost before conversion.

### E-DSP — Analog Devices ADSP-21569

The ADSP-21569 is a single-core SHARC+ DSP, with speed grades up to 1 GHz, 640 kB L1 SRAM and 1024 kB L2 SRAM. Its package is a 400-ball, 17 × 17 mm BGA at 0.8 mm pitch; the family datasheet's LQFP option must not be attributed to this model. SPORT/DAI, DMA, FIR/IIR acceleration, UART, SPI, I2C and JTAG capabilities are present. Boot options include serial flash and external hosts. Multiple supply domains exist, including core, I/O, reference, analog and DMC domains. See [ADSP-2156x Rev. D, June 2023, Table 1, Table 7, System Debug, Operating Conditions and Ordering Guide](https://www.analog.com/media/en/technical-documentation/data-sheets/adsp-21562-21563-21565-21566-21567-21569.pdf).

These capabilities do not establish a sustainable FxLMS workload or eliminate external-memory questions. Speed/temperature grade, memory placement, accelerator usefulness, boot/storage choice and interface resource allocation remain unverified against this project.

### E-AMP — Texas Instruments TAS6424-Q1

The device offers four BTL channels and TDM4/TDM8 input. At 96 kHz, published input-to-output latency is 12 sample periods. TDM clocking calls for 128/256 clocks per frame, with a 25 MHz clock limit; 24-bit input is supported. PVDD operation is 4.5–26.4 V, VBAT 4.5–18 V, with nominal 3.3 V logic supply and I2C control. TI states a heatsink is required. See [TAS6424-Q1 SLOS870B, October 2017, §§7.3–7.6, 9.3.1.4–5 and 9.6.4](https://www.ti.com/lit/ds/symlink/tas6424-q1.pdf).

Derived amplifier delay: `12 / 96000 = 125 µs`. Combined with E-ADC, the published converter/amplifier contributions total approximately **364.4 µs**, excluding other system contributions and worst-case margin. This is a screening estimate, not a guaranteed end-to-end bound.

The advertised 75 W is specified at 25 V into 4 Ω and 10% THD+N; it is not a 12 V output-power guarantee. See [TI product overview, output-power conditions](https://www.ti.com/product/TAS6424-Q1). No output wattage is frozen.

### E-LOAD — Candidate microphone/ADC interface concern

Comparing the per-leg loading constraints in E-MIC and E-ADC indicates that a direct connection may violate the microphone's specified load envelope. This is an engineering inference from those tables, not a claim that the proposed AFE is incompatible. U07 must resolve loading, common mode, noise and gain together. Neither direct drive nor a particular buffer/amplifier topology is approved.

### E-POWER — Supply sequencing and reset requirements

ADI's [EE-470 Rev. 1, 2025-02-17, pp. 1–6](https://www.analog.com/media/en/technical-documentation/application-notes/ee-470.pdf) identifies mandatory DSP domain-voltage relationships during startup, reset and shutdown, including the ±1.89 V inter-domain constraint described there. It also discusses indeterminate reset/I/O behavior during supply transitions. This makes sequencing and supervision a verification requirement; copying a reference regulator circuit is not a resolution.

ADC reset depends on regulator discharge and PLL initialization as well as pulse timing. See [ADAU1978 Rev. B, pp. 12–13](https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU1978.pdf). Full board rail currents, tolerances, sequencing and reset timing remain UNKNOWN.

### E-DOC — Source ambiguities needing closure

ADAU1978 Rev. B Table 4 gives an HPF corner of 0.9375 Hz at 48 kHz, while the Analog Inputs text states 1.4 Hz. This is **CONFLICTING source evidence**; the actual configured response is UNKNOWN pending clarification/measurement. [ADI datasheet, Table 4 and p. 14](https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU1978.pdf).

TAS6424-Q1 §9.3.1.5 lists lower general SCLK ratios than the TDM-specific §9.3.1.4. Use mode-specific timing evidence in the later compatibility review and reconcile the wording; the brief's “TDM4” alone does not settle interoperability. [TI datasheet, §§9.3.1.4–5](https://www.ti.com/lit/ds/symlink/tas6424-q1.pdf).

## Requirements validation and explicit assumptions

### Audio framing

At 96 kHz, the sample period is `1 / 96000 = 10.4167 µs`. Four 24-bit payloads contain `4 × 24 × 96000 = 9.216 Mbit/s` of audio per direction. A candidate four-slot, 32-bit-slot transport requires `4 × 32 × 96000 = 12.288 MHz` BCLK per link. Payload size and slot size are different requirements; 24-bit audio does not mandate a 9.216 MHz physical clock.

P04 is worth investigating against E-ADC/E-AMP, but no complete DSP/ADC/amplifier timing proof has been done. Clocks, frame shape, alignment, I/O thresholds and channel mapping remain U16/U17. Independent transmit and receive data paths and their scheduling must be accounted for without inventing a SPORT allocation.

### FxLMS workload

There is no numerical DSP requirement yet. For sizing only, consider a fully coupled, direct time-domain feedforward implementation with `R` references, `S=4` outputs, `E` errors, `Lw` control taps, `Ls` secondary-path taps, and adaptation each sample. An elementary operation count is:

```text
Control filtering:          R × S × Lw               MAC-like operations/sample
Filtered-reference paths:  R × S × E × Ls
Coefficient-update sums:   R × S × E × Lw
Approximate total rate:     fs × [R S Lw + R S E (Ls + Lw)]
Control coefficients:      R × S × Lw
Secondary-model coefficients: S × E × Ls
```

This is a review derivation for one hypothetical implementation, not a benchmark, minimum CPU specification or selected algorithm. It excludes normalization, scaling, identification, buffers/history, program storage, interrupt/DMA overhead and monitoring. Optimizations change the count. The multiple-reference/multiple-output model and speaker-to-error path dependence are described in [Delft technical report 99-11, §3.2, equations 3–4](https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/99_11.pdf). Algorithm variant and measured execution time must replace this estimate before DSP sign-off.

No reference/error split, tap lengths, block size, floating-point format, update rate, reserve percentage or external RAM requirement is selected. Four inputs/four outputs are insufficient to prove DSP adequacy.

### Latency and acoustic feasibility

The delay budget must cover microphone/AFE response, ADC filtering, serial framing, acquisition buffering, DSP execution/scheduling, playback buffering, amplifier processing and output filtering. Frequency-dependent phase/group delay must be distinguished from fixed transport delay. Avoid double counting stages already included in a manufacturer's measurement endpoints.

For broadband feedforward control, sufficient reference preview relative to the control/secondary path is a feasibility condition to investigate. Geometry, acoustic propagation, band and controller type determine the available margin; a generic “below 1 ms” target cannot be invented. No topology has been approved and no acoustic feasibility is claimed. ADI discusses the dependence of real-time acoustic systems on signal-chain delay in [Planning for Success in Real-Time Acoustic Processing](https://www.analog.com/en/resources/technical-articles/planning-for-success-in-real-time-audio-processing.html).

For illustration only, an additional whole-frame buffer contributes `N / fs` seconds if its scheduling adds N samples; the actual pipeline may differ. Algorithm speed cannot remove converter/amplifier delay already incurred.

### Power, thermal and output feasibility

Input sizing must use the simultaneous output duty and source minimum voltage. A planning relation is `Iin ≈ (sum(Pout_i / eta_i) + Pother_input) / Vin`, where `Pother_input` includes input-referred electronics consumption and remaining conversion losses. Efficiencies, duties, voltage and current margins are UNKNOWN. Peak/inrush energy and reactive speaker current need separate treatment.

For an ideal unboosted full-bridge sinusoidal output limited to a differential peak of `Vin`, the ideal ceiling is `P = Vin² / (2 Rload)`: at nominal 12 V this is 18 W into 4 Ω. This calculation is an illustrative idealization, not a selected load, achievable TAS6424-Q1 rating or production power target. Real voltage loss, distortion limits, source droop, current limits and heat reduce usable output. Requirements exceeding the feasible unboosted envelope would force reconsideration of amplification or internal power conversion.

## Conflicting requirements

No mutually incompatible **confirmed user requirements** are established by the available evidence. Unknown values must not be filled in merely to create or conceal a conflict. The following conditional incompatibilities are recorded for disposition:

| ID | Status | Incompatibility / required disposition |
| --- | --- | --- |
| X01 | UNKNOWN applicability | Four physical references plus four physical errors would conflict with the four-input baseline. Resolve U02; do not assume eight channels. |
| X02 | UNKNOWN applicability | A future total latency limit below the E-ADC/E-AMP screening contribution would invalidate this candidate path. Resolve U11 before component sign-off. |
| X03 | UNKNOWN applicability | Direct microphone-to-ADC drive is not established within the E-LOAD constraints. The stated AFE can address this, but its implementation is unknown. |
| X04 | UNKNOWN applicability | A requirement for headline amplifier wattage at nominal input, or a prohibition on a heatsink, could invalidate E-AMP. Resolve U19/U25/U38. Neither requirement currently exists. |
| X05 | CONFLICTING source evidence | E-DOC records the ADC HPF discrepancy. Resolve it before freezing the filter response; also clarify the separately noted amplifier clock wording before freezing clocking. |

No requirement change, alternate component or undocumented connection has been used to close these issues.

## Requirements that must be resolved before schematic design

The following are schematic-entry blockers even though they do not prevent a bounded component/datasheet investigation. Closure means a recorded value or explicit accepted scope decision, supporting engineering evidence and an acceptance method—not an unsupported assumption.

| Priority | Required closure | Proposed accountable discipline |
| --- | --- | --- |
| 1 | Acoustic use case, cancellation acceptance, input role map and preview/latency envelope (U01–U03, U11). | Product owner + acoustics/controls |
| 2 | Microphone installation, signal/gain/noise/headroom budget and AFE/ADC loading/filter requirements (U04–U10). | Analog/audio engineering |
| 3 | Algorithm workload, path identification, stability/output limits and cycle/memory budget (U12–U15, U18). | DSP/controls + firmware |
| 4 | Full digital-audio/clock contract and compatible I/O domains (U16–U17, U24, E-DOC). | Digital hardware + firmware |
| 5 | Speaker/load/cable data and simultaneous output-power envelope (U19–U21). | Acoustics + power engineering |
| 6 | Source range/current/transients, derived rails, sequencing, reset and protection specification (U22–U25, U32–U33). | Power + system hardware |
| 7 | Boot/storage/RAM, programming recovery and debug/control/service requirements (U26–U31). | Firmware + hardware/test |
| 8 | Mechanical/connector/stackup/fabrication constraints and validated cooling envelope (U34–U38). | Mechanical + PCB/manufacturing |
| 9 | EMI/EMC, coexistence and product safety acceptance (U39–U40, U44). | Product + compliance + hardware |
| 10 | Cost/volume/sourcing and assembly/factory-test requirements (U41–U43). | Product + manufacturing/test |

All listed unknowns affect schematic or component decisions; no unsupported numeric defaults are approved. Changes to C01–C09 require explicit requirements revision. Provisional items may be accepted, revised or rejected with recorded rationale.

## Risk register

All risks are open. Likelihood is UNKNOWN without application/load data or validation. Severity indicates potential consequence, not measured probability.

| Risk | Severity | Cause / consequence | Required mitigation or evidence; proposed owner |
| --- | --- | --- | --- |
| R01 | Critical | Unknown geometry/preview and delay target may make ANC ineffective with this path. | Resolve U01–U03/U11 and assess delay/phase budget first; controls. |
| R02 | High | Undefined reference/error split may exceed acquisition resources. | Approve physical and synthesized signal map; systems. |
| R03 | High | Microphone loading, level or noise mismatch may impair acquisition. | Close E-LOAD and worst-case signal/noise/headroom budget; analog. |
| R04 | High | DSP capability inferred from clock speed may miss real-time deadlines. | Define workload, memory and cycle margins; benchmark after authorization; DSP. |
| R05 | Critical | Invalid secondary-path model, clipping or adaptation divergence may produce excessive output. | Define identification, stability limits and fault response acceptance; controls/product. |
| R06 | High | TDM/clock ambiguity may cause lost, swapped or misaligned channels. | Complete interface timing matrix and reconcile E-DOC; digital. |
| R07 | High | Output power/load undefined; nominal source may be inadequate. | Validate four-channel load/power/current envelope; power/acoustics. |
| R08 | High | Cooling space may be incompatible with amplifier/DSP dissipation. | Resolve heatsink/mechanics and simultaneous thermal envelope; mechanical/power. |
| R09 | High | Power-domain sequencing or reset recovery errors can prevent reliable operation or damage a device. | Domain/reset matrix using E-POWER and operating-corner validation plan; power/firmware. |
| R10 | High | Switching energy and long cables may compromise microphones or EMC. | Define cable/grounding environment, coexistence limits and EMC tests; analog/compliance. |
| R11 | High | Boot/update/debug path may be unavailable in factory or field. | Approve storage, tooling, access and interrupted-update recovery; firmware/test. |
| R12 | High | Package, acoustic port or stackup incompatible with assembly/enclosure limits. | Fabricator/assembler feasibility review and mechanical requirements; manufacturing. |
| R13 | High | Missing production/compliance/cost targets cause late redesign. | Close U37/U39/U41–U44 before schematic entry; product/manufacturing. |
| R14 | Medium | Typical values or inconsistent source text mistaken for guarantees. | Preserve revisions/locators, distinguish conditions and resolve ambiguities; component verification owner. |

## Recommended Phase 1 scope

Recommendation only; no Phase 1 work is authorized or started by this document.

1. Obtain the priority product/acoustic/load answers above. Maintain open requirements explicitly while screening candidates; do not finalize suitability without acceptance limits.
2. Assemble a controlled official evidence set: exact orderable-part datasheets, package/grade details, DSP hardware/core references, current silicon anomalies, boot guidance and power-sequencing documentation. Use evaluation manuals/reference designs only as independently checked evidence. The [ADSP-21569 documentation index](https://www.analog.com/en/products/ADSP-21569.html) identifies these DSP source categories.
3. Produce a candidate compatibility matrix covering microphone/AFE/ADC levels and loading, complete TDM/clock timing, control/debug/boot resources, all power domains and reset behavior. Resolve E-DOC with authoritative clarification or a defined verification experiment.
4. Produce requirements-driven latency/phase, DSP cycle/memory, power/current and thermal feasibility budgets. Mark all unverified performance corners; define later measurement/benchmark procedures without assuming results.
5. Evaluate procurement, fabrication/assembly, connector, cooling and compliance constraints. Recommend retaining or replacing candidates only with traceable evidence and recorded requirement implications.
6. Deliver component verification findings, remaining blockers and a revised requirements baseline for a separate review. Schematic design, PCB creation, placement and routing remain outside that proposed verification scope.

## Gate rationale

Enough is defined to safely begin a bounded component and datasheet verification phase: channel counts, conversion operating point, DSP/algorithm class, output technology, nominal source and development intent are explicit, and candidate constraints and unanswered acceptance criteria are traceable. No confirmed requirement contradiction prevents that investigation.

The result below means readiness for that verification activity only. It does not mean the system performance requirements are fully frozen, the components are approved, or schematic design is ready. The schematic-entry blockers above remain open. This task stops here; Phase 1 has not begun.

PHASE 0: PASS
