# Phase 1B - Blocker Resolution

Repository: `circuitBuilderAi-Astra`  
Review date: 2026-09-07  
Scope: Phase 1 blockers B1-B3 only; documentary verification and calculations.

## 1. Executive summary

**The component-level gate remains BLOCKED.** The stored evidence establishes clock frequencies, conditional DC compatibility, serial timing constraints, and ADC filter defaults. It does **not** reconcile the TAS6424-Q1 tied-clock/phase contradiction or establish complete guaranteed timing for the proposed connections. No candidate is proved incompatible with a confirmed product requirement; TAS6424-Q1 remains **BLOCKED BY MISSING EVIDENCE**, not REJECTED.

| Blocker | Phase 1B finding | Disposition |
| --- | --- | --- |
| B1: amplifier clocks | External clock must reach MCLK during audio playback; a separate oscillator is not necessarily required. TDM4 with 24-bit data in 32-bit slots requires 12.288 MHz BCLK at 96 kHz. Tied-clock permission conflicts with the adjacent phase restriction. | **CONFLICTING; unresolved** |
| B2: digital compatibility | Full-range direct wiring fails DC guarantees. A bounded I/O rail gives positive calculated margins. TDM8 external-SPORT timing fails the setup screen at 45% BCLK duty; TDM4 has useful conditional margin. ADC minimum output hold and actual clock-route/load timing remain unclosed. | ADC -> DSP **PROVISIONAL**; DSP -> amplifier **UNKNOWN** |
| B3: ADC filters | HPF is independently configurable per channel and **off at reset**. Decimation remains active; documented 96-kHz group delay is about 239.4 us. HPF cutoff values still conflict. | Defaults/delay interpretation resolved; enabled-HPF response and system acceptance remain open |

Read: `AGENTS.md`, `MASTER_SPEC.md`, [Phase 0](phase_0_requirements_freeze.md), [Phase 1](phase_1_component_datasheet_verification.md), [evidence index](../evidence/component_evidence_index.md), and architecture/decision placeholders. The current AGENTS.md governs; Phase 0's placeholder description is historical. No valid Graphify graph exists. C01-C09 and all unresolved product requirements are preserved.

Evidence keys below retain the index meanings: **ADC** = ADAU1978 Rev.B (August 2024); **DSP** = ADSP-2156x Rev.D (June 2023); **HRM** = ADSP-2156x Hardware Reference Rev.1.1 (October 2022); **AMP** = TAS6424-Q1 SLOS870B (October 2017); **REF733** = TI TIDUCZ2 (December 2017). Pages are printed pages; HRM uses chapter-page labels. All electrical conclusions use existing local PDFs. Targeted searches for corrections, justified by the unresolved contradictions, found no controlled correction; the [TI index](https://www.ti.com/product/TAS6424-Q1) still lists Rev.B and the [ADI index](https://www.analog.com/en/products/adau1978.html) lists the existing ADC documentation. Forum results were not accepted as electrical evidence. No additional document was downloaded or new authoritative source introduced; the evidence index and original Phase 1 report are unchanged.

## 2. TAS6424-Q1 clock resolution

**MCLK input versus independent source.** AMP pin table pp.5-6 identifies MCLK(12), SCLK(13), FSYNC(14) as inputs. Sections 9.3.1.5-6, pp.19-20, specify MCLK ratios and clock-loss/ratio-fault handling. No MCLK-pin-free I2S/LJ/RJ/TDM playback mode, internal BCLK-to-MCLK replacement, or enable bit for such a mode is documented. TDM's permission to connect SCLK and MCLK together would remove the need for an independent MCLK signal source, **not the clock at the MCLK pin**. Its applicability is disputed below. DC load diagnostics explicitly work without audio clocks (p.24); that is not a playback mode. AC diagnostics using externally supplied audio still need that audio interface.

| Topic | Official evidence | Reconciliation / boundary |
| --- | --- | --- |
| MCLK at 96 kHz | AMP p.19: 128/256/512 times fs; maximum 25 MHz | **CONFIRMED frequency limits:** 128fs = 12.288 MHz; 256fs = 24.576 MHz. 512fs = 49.152 MHz is **INCOMPATIBLE** with the limit. Frequency compliance alone does not settle phase. |
| SCLK ratios | Section 9.3.1.4 says TDM uses 128 or 256; section 9.3.1.5 lists 32/48/64fs | Mode-specific TDM text, Fig.39 (p.22), SAP Table 13 (pp.34-35), and REF733 section 2.3.3 support TDM operation beyond 64fs. The 32/48/64fs list fits stereo framing, not all TDM. Treat it as an incomplete general list; this is an engineering interpretation, not a TI correction. |
| MCLK/SCLK phase | Section 9.3.1.4 permits tying pins; section 9.3.1.5 prohibits an in-phase relationship | **CONFLICTING.** No explicit TDM exception, phase window, applicable silicon revision, or correction reconciles these instructions. Neither interpreting the phrase as “need not be synchronized” nor inventing a delay is justified. |
| Duty/edges | AMP p.10: MCLK/SCLK duty 45%-55%; SCLK period >=40 ns; high/low >=16 ns; rise/fall <=4 ns. Page 19 additionally requires 50% duty at 128fs | Retain the stricter 128fs duty statement; its allowable tolerance is **UNKNOWN**. For 256fs, lack of an exact-50% requirement does not remove the p.10 duty bounds. |

**Supported payload and explicit BCLK calculation.** Use 24 significant bits in **32-bit slots**: ADC Table 21 p.32 expressly permits this; HRM pp.23-33 to 23-35 and SPORT word-length fields support it; AMP Table 13 and Fig.39 show this payload/slot combination. Do not confuse sample precision with slot length.

| Configuration evaluated, fs = 96,000 Hz | Calculation | Period / ideal half-period | Disposition |
| --- | --- | --- | --- |
| Four useful channels, TDM4 | 96,000 x 4 x 32 = **12,288,000 Hz** = 128fs | 81.3802 / 40.6901 ns | Supported format/rate candidate; full clock contract **UNKNOWN** |
| Four useful channels in TDM8, four padding slots | 96,000 x 8 x 32 = **24,576,000 Hz** = 256fs | 40.6901 / 20.3451 ns | Documented comparison, not an approved fallback; timing limitation in section 4 |
| Packed four 24-bit slots | 96,000 x 4 x 24 = 9.216 MHz = 96fs | 108.5069 / 54.2535 ns | **Not established** for AMP: its slot-size field mentions 24 bits but its TDM SCLK list does not include 96fs. Do not select. |

AMP candidate fields, **not a register-write sequence**: SAP 0x03 sample-rate `[7:6]=10`, format `[2:0]=110`, slot-size bit4=0, first-four selection bit5=0, normal channel-pair order bit3=0. Use SDIN1(15); TI recommends grounding unused SDIN2(16). TDM8 Fig.39 shows an active-high single-clock FS pulse and one-bit-delayed MSB-first data. TDM4 is stated explicitly, but has no separate waveform; its detailed framing remains conditional. PBTL is not used.

**Can ADSP-21569 supply these clocks directly?** Its PCG/SRU/DAI resources can generate and output the required frequencies: a 24.576 MHz reference divided by 2 gives TDM4 BCLK, divided by 256 gives 96-kHz FS, with pulse width two reference cycles and appropriate FS phase. A second PCG can provide MCLK; a divide-by-1 output is bypass mode. HRM pp.24-1 to 24-9 establish these capabilities. DSP Table 19 p.45 allows external-clock SPORT receive up to 62.5 MHz and transmit up to 31.25 MHz, also bounded by SCLK0. These are capability findings, not an implemented clock tree.

Direct electrical/timing approval is **UNKNOWN**: SYS_CLKIN0 is a 1.8-V-domain input, whereas DAI audio pins use VDD_EXT; raw fanout of a 3.3-V oscillator to SYS_CLKIN0 is invalid. DSP Table 50 p.75 guarantees PCG timing **only for DAI-pin input and DAI-pin output routing**, explicitly withholding timing for other routes. Its normal-mode input-period constraint implies SCLK0 >=49.152 MHz for a 24.576 MHz input; its 2-10 ns output delay does not certify an internal PCG-to-SPORT route or bypass timing. HRM's FS phase adjustment is not a guaranteed solution to TI's MCLK/SCLK phase requirement. No fully valid 96-kHz clock configuration can therefore be certified from these sources.

REF733 pp.18-23 demonstrates buffered 96-kHz, eight-slot, 32-bit transport with different ADCs; AMPEVAL SLOU453A pp.22-23 supplies evaluation wiring. Neither supplies an authoritative correction to the device phase restriction. **B1 remains open.** Required closure is controlled TI evidence for the exact TAS6424-Q1 mode/revision, including tied-clock applicability, permitted phase/edge separation and 128fs duty tolerance. Incompatibility of every permissible configuration is not proved, so rejecting the component itself would overstate the evidence.

## 3. ADC -> DSP electrical/timing compatibility

Candidate only: ADC SDATAOUT1(13) -> SPORT0A receive through DAI0; DSP supplies BCLK(16)/LRCLK(15) to the ADC. Four 32-bit slots, 24 valid bits, 96 kHz, 12.288 MHz BCLK, active-high one-BCLK FS, one-bit-delayed MSB-first data. ADC tables 20-21 pp.31-32 select FS=011, TDM4, 24-bit data/32-bit slots, slave/pulse mode; Fig.26 p.18 supports falling-edge launch with BCLKEDGE=0. HRM p.23-33 gives SPORT CKRE=1 for falling-edge drive/rising-edge sample, with MFD=1 and four enabled channels. SPORT0 avoids the unresolved timing-footnote scope for SPORT4-7 noted in Phase 1.

The following limits cover both interfaces. A receiver's **VIL(max)** is the highest voltage guaranteed LOW; “VIL(min)” in a worst-case margin calculation means the minimum of that allowable threshold over receiver supply corners, not a minimum valid input voltage.

| Device / relevant pins | I/O supply range | VOH(min) / VOL(max) | VIH(min) / VIL(max) | Absolute input range |
| --- | --- | --- | --- | --- |
| ADC SDATAOUT1/2; BCLK/LRCLK bidirectional; MCLKIN input | IOVDD 1.62-3.6 V | IOVDD-0.60 V / 0.4 V at 1 mA | 0.7 IOVDD / 0.3 IOVDD | -0.3 to +3.6 V |
| DSP DAI0 pins used for SPORT/PCG | VDD_EXT 3.13-3.47 V | 2.4 V / 0.4 V; DS1 at +/-2 mA for <=62.5 MHz | 2.0 V / 0.8 V | -0.3 to +3.47 V while powered within specification |
| AMP MCLK/SCLK/FSYNC/SDIN1/2 | VDD 3.0-3.5 V | **NOT APPLICABLE:** audio pins are inputs | 0.7 VDD / 0.3 VDD | -0.3 to VDD+0.5 V |

Sources: ADC Tables 2/3/6 pp.3/4/7; DSP pp.44/47/49/52; AMP pp.6-8. DSP's below-specification supply condition restricts inputs to that domain voltage +/-0.2 V (Table 29 footnote 1); do not drive a powered-off DSP. AMP's limits likewise track its supply. ADC absolute limits do not establish powered-off functional tolerance. Overshoot, ground offset and sequencing must be budgeted separately; absolute maxima are not valid operating targets. ADC specifications use 20-pF output loading and their stated conditions; DSP timing uses a 6-pF reference load. AMP electrical/timing tables specify TC=25 C and default test conditions unless overridden; they do not establish an unstated full-temperature system guarantee.

**Worst-case DC arithmetic** (volts; guaranteed limit values, not typical output curves):

| Direction / envelope | HIGH = VOH(min) - VIH(min) | LOW = VIL(max at lowest receiver rail) - VOL(max) | Result |
| --- | --- | --- | --- |
| ADC -> DSP, entire ADC IOVDD range | (1.62-0.60)-2.0 = **-0.980** | 0.8-0.4 = **+0.400** | Full-range direct hypothesis **INCOMPATIBLE**; ADC output near 3.6 V also cannot be assumed safe for a 3.47-V-limited DSP input |
| DSP -> ADC clocks, entire ADC range | 2.4-(0.7 x 3.6) = **-0.120** | (0.3 x 1.62)-0.4 = **+0.086** | Full-range direct hypothesis **INCOMPATIBLE** |
| ADC -> DSP, illustrative 3.168-3.232 V I/O envelope | (3.168-0.60)-2.0 = **+0.568** | 0.8-0.4 = **+0.400** | Positive conditional DC margins |
| DSP -> ADC clocks, same envelope | 2.4-(0.7 x 3.232) = **+0.1376** | (0.3 x 3.168)-0.4 = **+0.5504** | Positive conditional DC margins |

The illustrative envelope is 3.2 V +/-1% at the pins, encompassing static tolerance, ripple and transients; it fits all three I/O supply ranges. It is an **analysis proposal**, not a new approved requirement or selected regulator. For required high noise margin M, DSP-driven ADC/AMP supplies must satisfy `Vreceiver_max <= (2.4-M)/0.7`; even zero-margin compatibility requires <=3.42857 V. A nominal 3.3 V +/-1% leaves only 0.0669 V high margin. Required noise reserve is UNKNOWN.

**Level shifting:** not inherently required for ADC data or DSP clocks under a qualified common envelope such as the example. It **is required for a retained incompatible voltage arrangement**, or must be replaced by a different verified rail/master arrangement. No translator/buffer is selected. Changing the ADC to audio-clock master avoids DSP-to-ADC audio-clock thresholds but needs a new clock/FS contract and does not close B1.

**Serial timing:** define L as falling-launch to next rising-sample time and H as rising-sample to next falling-launch time at the reference pins. Ideal L=H=40.6901 ns. A *proposed* 45%-55% BCLK envelope gives each >=36.6211 ns before source-period error. This is an analysis envelope, not an ADC duty guarantee. Actual margin must subtract adverse clock/data path skew, jitter and load/threshold derating.

| Check | Guaranteed device values / derived screen | Disposition |
| --- | --- | --- |
| BCLK frequency/width | ADC slave high/low >=10 ns; 12.288 MHz ideal halves exceed this. DSP Tables 19/36 limits must also hold; Table 36 footnote 3 references ideal **maximum** SPORT frequency, not an arbitrary chosen frequency. | Frequency/width feasible; actual waveform unverified |
| ADC data setup at DSP | ADC tABDD <=18 ns from falling BCLK; DSP tSDRE >=2 ns before rising sample. `L-18-2` = **20.6901 ns** ideal; **16.6211 ns** at 45% | Positive conditional setup budget |
| ADC data hold at DSP | DSP tHDRE requires 3 ns; margin is `H+tADC_min-3` minus adverse skew. ADC Table 5 supplies no minimum delay/hold guarantee. Figures 2/26 show edge relationships, not a quantified minimum through final-bit/Hi-Z transitions. | **UNKNOWN** guaranteed hold; do not silently set tADC_min=0 |
| FS at ADC | tALS >=10 ns before / tALH >=5 ns after rising BCLK. If an externally clocked SPORT generates FS, tDFSE <=11 ns and tHOFSE >=2 ns give `L-11-10` and `H+2-5`: **15.6211 / 33.6211 ns** at 45% | Conditional alternative-source screen only |
| FS at SPORT | External FS needs tSFSE >=2 ns and tHFSE >=3 ns about sample edge | Actual PCG/FS-to-SPORT timing **UNKNOWN**; SPORT-generated-FS numbers cannot be substituted for PCG output timing |

Sources: ADC Table 5/Fig.2 pp.5-6 and Figs.26-27 pp.18-19; DSP Table 36 p.57, Table 50 p.75, loading pp.87-88. ADC padding/unused positions may be Hi-Z; discard the eight non-audio bits and verify the last valid bit's hold before approving the connection. **Interface classification: PROVISIONAL.** DC/format feasibility is established conditionally; complete guaranteed timing is not.

## 4. DSP -> amplifier electrical/timing compatibility

Use SPORT0B transmit -> SDIN1, rising-edge sampling at AMP (Fig.36 p.20), falling-edge DSP drive (HRM p.23-33). The proposed TDM4 framing and unresolved mode constraints are in section 2. All audio clock/data inputs use AMP VDD; there is no AMP audio VOH/VOL to compare.

| DSP -> AMP DC envelope | HIGH margin | LOW margin | Disposition |
| --- | --- | --- | --- |
| Full AMP VDD range | 2.4-(0.7 x 3.5) = **-0.050 V** | (0.3 x 3.0)-0.4 = **+0.500 V** | Unrestricted direct hypothesis **INCOMPATIBLE** |
| 3.168-3.232 V example from section 3 | **+0.1376 V** | **+0.5504 V** | Conditional positive margins on data, BCLK, FS and DSP-driven MCLK |

**Level shifting:** not intrinsically required within a verified bounded rail envelope, but full-range direct drive cannot be approved. A buffer/translator is required if incompatible rails are retained; it must also meet clock duty, edge-rate, propagation/skew, startup and load constraints. This is not approval of any interface component.

For an **externally clocked SPORT**, DSP Table 36 guarantees transmit data/FS valid <=11 ns after the drive edge and held >=2 ns after it. AMP p.10/Fig.36 requires data setup/hold >=8 ns and FS separation >=8 ns on both sides of rising SCLK. Thus data and SPORT-generated-FS screens are `setup=L-11-8`, `hold=H+2-8`, before path/load deductions:

| Frame | 50% duty setup / hold | 45%-55% worst-half setup / hold | Implication |
| --- | --- | --- | --- |
| TDM4 x 32, 12.288 MHz | **21.6901 / 34.6901 ns** | **17.6211 / 30.6211 ns** | Useful conditional budget; the 45% calculation does not waive AMP's stricter 128fs duty wording |
| TDM8 x 32, 24.576 MHz | **1.3451 / 14.3451 ns** | **-0.6895 / 12.3105 ns** | External-clock direct-drive hypothesis over the full 45%-55% duty envelope is **INCOMPATIBLE** even before board effects |

At 256fs, the minimum 45% half-cycle is 18.3105 ns: it exceeds AMP's 16 ns pulse-width requirement but fails the combined 19 ns setup requirement. Positive setup at TDM8 would need `L>19 ns`, i.e. low duty >46.6944% before any additional reserve. This rejects that unconstrained interface hypothesis, not TAS6424-Q1 or all possible TDM8 implementations.

The SPORT internal-divider specification (Table 37 p.58) is different: data/FS delay <=3.5 ns and hold >=-3 ns from the drive edge. It cannot replace Table 36 just because a PCG is on the same chip. No exact core/peripheral clock selection or internally clocked SPORT implementation is approved here. Likewise, PCG-sourced FS requires its own path proof; the table above is not that proof.

Remaining timing constraints: AMP MCLK/SCLK duty, <=4 ns rise/fall, >=40 ns SCLK period, phase conflict, clock continuity, and actual fanout. AMP audio inputs can load each DSP output by 10 pF before routing, exceeding DSP's 6-pF timing reference load. DSP pp.87-88 require delay/hold derating and recommend IBIS for the actual system. No guaranteed edge-rate or loaded timing closure is claimed. **Interface classification: UNKNOWN**, principally B1 plus these timing gaps; conditional DC compatibility alone cannot establish it.

## 5. ADAU1978 filter/latency resolution

| Question | Official finding / interpretation | Evidence |
| --- | --- | --- |
| Available conversion filter modes | Onboard linear-phase antialias/decimation filtering, with sample-rate-dependent behavior. No selectable minimum-phase/fast/low-latency filter or decimator bypass at 96 kHz is documented. HPF control is separate. | ADC Table 4 p.4; ADC description p.16; register map pp.26-42 |
| Default behavior | Register 0x1A resets to 0x00: all four HPFs **OFF**, all four calibrated-DC subtraction enables OFF. This is the register-controlled reset state, not a claim that conversion is already running. Default FS range is 32-48 kHz; 96 kHz requires FS=011. | Tables 20/31 pp.31/42 |
| HPF configuration | Bits 3:0 independently enable channel 4 through channel 1 HPFs (0=off, 1=on). No corner-coefficient selection is exposed. Calibration enable at 0x0E and subtraction bits 7:4 at 0x1A are separate functions, not decimator bypass. | Tables 29/31 pp.40/42 |
| 96-kHz decimator | Falls in the explicitly stated 8-96 kHz delay range: **22.9844/fs**. Derived delay = 22.9844/96,000 = **239.4208 us**. Table 4's 479 us is the rounded 48-kHz typical example, not a fixed delay at all rates. | Table 4 p.4 |
| Other rate behavior | Table 4 separately lists **35 us typical at 192 kHz**. This is a different sample-rate case, not permission to select that delay at 96 kHz or to change C06. | Table 4 p.4; Table 20 p.31 |
| HPF cutoff contradiction | Table 4: **0.9375 Hz** at 48 kHz. Page 14: **1.4 Hz**, 6 dB/octave, scaling with fs. Scaling the competing values to 96 kHz gives **1.875 versus 2.8 Hz**. Neither is confirmed. | Table 4 p.4 versus Analog Inputs p.14 |
| Correct boundary of the conflict | This is the optional low-frequency/DC filter's numerical response, not evidence of two selectable decimation modes. No source distinguishes the two cutoff figures by mode, revision or definition. The table specifies -3 dB; no supported alternative definition reconciles the prose. | Same sources; UG-600 supplies no corrective specification |
| Delay guarantee | Decimator group delay and HPF phase/settling entries are typical/documented response data, not worst-case end-to-end bounds. HPF's listed 10 degrees at 20 Hz and 1 s settling at 48 kHz do not define its complete 96-kHz phase response. | Table 4 p.4 |

**ANC implication:** HPF-off avoids dependence on its conflicting corner but retains the approximately 239.4-us decimation contribution. It requires an accepted DC/headroom and low-frequency response plan; leaving a reset bit clear is not system acceptance. Adding AMP's **typical** 12/fs =125 us at 96 kHz gives a **364.4208-us screening subtotal**, not a guaranteed total, before microphone/AFE response, DSP buffering/execution, transport not already included in the stated endpoints, and output-filter/acoustic delay. Do not double-count manufacturer measurement endpoints.

**ADAU1978 suitability: PROVISIONALLY SUITABLE.** Four-channel 96-kHz/24-bit conversion is documented. Definitive ANC suitability is **UNKNOWN** until U01-U03/U10-U11 define band, geometry/preview, permitted phase response, and maximum latency. The HPF-enabled numerical contradiction remains open; controlled ADI clarification or an explicitly accepted characterization/HPF-off disposition is required. No bypass policy is silently adopted.

## 6. Resolved blockers

No complete B1-B3 blocker can honestly be marked closed. The following **subquestions are resolved**:

- MCLK must be clocked for playback; sharing its source with BCLK is distinct from omitting the input clock. DC diagnostics are the documented clock-free exception.
- 24-bit data in four supported 32-bit slots requires **12.288 MHz**, not 9.216 MHz. 49.152-MHz AMP MCLK at 96 kHz is prohibited.
- Worst-case DC failures and a conditional positive-margin rail envelope are explicit, including both audio data and reverse-direction ADC clocks. A generic 1.8-V direct audio interface is not valid.
- TDM8 external-SPORT setup fails at the allowed 45% duty corner; a nominal half-cycle check alone is insufficient.
- ADC HPF is optional and off at reset. HPF-off does not remove the decimator; 96-kHz documented group delay is **239.4208 us**, with no verified selectable fast mode.

## 7. Remaining blockers

| ID / severity | Cause and consequence | Evidence needed / next bounded action |
| --- | --- | --- |
| B1 / critical component-selection blocker | AMP tied-clock permission versus phase restriction; an assumed relationship can cause clock faults and Hi-Z output. | Controlled TI clarification for exact variant/mode/revision, TDM4 framing/ratios, phase window and 128fs duty tolerance; otherwise a separately authorized alternative evaluation. Existing references cannot close it. |
| B2 / electrical contract blocker | Unapproved rail/noise/load envelope, absent ADC minimum output hold and unverified PCG/SPORT route/loaded timing; possible overstress or corrupt samples. | Accept rail/noise/environment limits; obtain ADC minimum valid-data/Hi-Z timing evidence or a justified accepted verification method; close exact source/FS/clock path with applicable manufacturer bounds, loading and skew. No blanket direct-interface approval. |
| B3 / filter-response freeze blocker | Conflicting enabled-HPF cutoff plus unknown U10/U11; LF phase and causality acceptance cannot be decided. | ADI correction or explicitly accepted HPF-off/characterization disposition; system DC/phase and latency budget. Product input cannot retroactively correct a datasheet. |

**B1 alone prevents Phase 2 architecture progression under the requested gate.** B2 remains unclosed. B3's enabled-HPF response and product acceptance remain conditional; the existence of an HPF-off mode reduces its scope but does not constitute an approved resolution. Phase 1's other product/schematic-entry blockers remain unchanged and were not re-researched.

## 8. Updated component status

These are Phase 1B engineering recommendations, not approval for schematic entry.

| Component | Status | Basis / boundary |
| --- | --- | --- |
| IM73A135 | **PROVISIONALLY APPROVED** | Phase 1 evidence retained: analog differential microphone, documented supply/load limits; requires buffered AFE and product SPL/band/noise/installation requirements. No new microphone investigation. |
| ADAU1978 | **PROVISIONALLY APPROVED** | PROVISIONALLY SUITABLE as above; 96-kHz data transport and filter defaults documented. Guaranteed interface timing, AFE contract and ANC latency/HPF acceptance remain open. |
| ADSP-21569 | **PROVISIONALLY APPROVED** | Required SPORT/PCG frequencies and formats are feasible; exact route/rail/timing proof and previously recorded compute, boot, silicon, power and thermal decisions remain open. |
| TAS6424-Q1 | **BLOCKED BY MISSING EVIDENCE** | MCLK/SCLK contract remains contradictory. No evidence proves all supported modes incompatible with confirmed requirements, so component REJECTED is not justified. |

Verification performed: all **16 local manufacturer PDF SHA-256 hashes match** the Phase 1 manifest; targeted table/waveform pages were rendered with PyMuPDF and visually checked; DC, clock, duty-corner timing and latency arithmetic was executed in Python. This is documentary verification, not a full-temperature hardware guarantee. No IBIS simulation, bench timing, acoustic testing or firmware benchmark was executed. ERC/DRC: **NOT APPLICABLE**. Only this report is a new deliverable; inspection scratch files are under `tmp/phase_1b/`. Original phase reports, evidence index and manufacturer files are preserved. No schematic, PCB or KiCad file was created, and Phase 2 was not begun.

## 9. Minimum requirements still needed from the product/system side

| Required input | Existing Phase 0 IDs | Decision enabled |
| --- | --- | --- |
| ANC band/cancellation target, reference/error map, geometry and acoustic preview | U01-U03 | Causality and component-path feasibility |
| Maximum worst-case latency with measurement endpoints, jitter and channel-skew limits | U11 | Acceptance or rejection of converter/amplifier delay and DSP scheduling budget |
| LF amplitude/phase mask, DC/overload limits, acceptable HPF-off or characterization policy; microphone SPL and AFE headroom | U05-U10 | Defensible B3 disposition and analog interface requirements |
| Required digital noise reserve, I/O rail tolerance/transients, temperature envelope, permitted buffering, clock/master/framing and startup/loss behavior | U16-U17, U24, U32, U37, U40 | Closure of B2's conditional electrical/timing envelope |
| FxLMS configuration, filter lengths, update/block sizes, concurrent workload and reserve | U12-U15, U18 | DSP compute/memory and maximum delay feasibility |
| Speaker impedance/load curves, simultaneous output power/duty, input-source envelope and cooling constraints | U19-U23, U25, U38 | Final amplifier/power/thermal suitability |

These answers cannot replace the missing manufacturer clock/hold evidence. Other Phase 0 schematic-entry requirements remain open. Stop at this gate.

PHASE 1B: BLOCKED
