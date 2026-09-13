# Phase 3E - Shutdown / safe-state contract correction

Date: 2026-09-13 (Europe/Istanbul)  
Scope: documentary correction of the enable, shutdown, safe-state, and powered-off interface contract. No KiCad file was created or modified, Phase 4B was not resumed, and the Phase 3D rail/divider/margin audit was not repeated.

Evidence notation uses the IDs in the [component evidence index](../evidence/component_evidence_index.md). This correction uses the already-selected power, supervisor, watchdog, regulator, ADC, AFE, DSP, amplifier, buffer, and translator documentation, plus the newly selected `SN74LVC1G74DCUR`, `SN74LVC2G07DBVR`, `SN74LVC2G17DBVR`, `SN74LVC2G08DCUR`, `SN74LXC8T245PWR`, and `TMUX2821DSGR` manufacturer documents. `CONFIRMED` means a device fact supported by that evidence. The topology and timing choices frozen here are approved project decisions for schematic implementation.

**Phase 3F amendment (2026-09-13):** the Phase 3E requirement that MCLK/audio OEs release only through `HW_RUN_LATCHED` created a circular prerequisite because ADAU1978 PLL lock was itself required before arming. The [clock startup correction](phase_3f_clock_startup_correction.md) supersedes only the affected clock-OE, ADC-reset, safe-clear, startup, shutdown, and fault text below. It adds a pre-arm `CLOCK_STARTUP_EN`, separates the SN74LVC244A clock and data banks, adds continuous `RUN_HEALTH_OK`, and leaves all Phase 3E analog-power, mute/standby, retained-shutdown, and powered-off-isolation decisions in force.

**Phase 3G amendment (2026-09-14):** the four differential microphones require eight independently isolated signal legs, while this document's original microphone boundary covered only four. The [remaining-sheet preflight](phase_3g_remaining_schematic_implementation_preflight.md) replaces that population with four `TMUX1574PWR` packages while retaining ten `TMUX2821DSGR` packages for the AFE/ADC and VREF boundaries. Phase 3G also replaces the former OPA165x/VREF-buffer contract. All unrelated retained-run, safe-latch, sequencing and digital-isolation decisions remain in force.

## 1. Disposition of the Phase 4B blocker

The former enable contract is rejected. A direct `OUT1` fanout cannot implement the approved commanded power-down sequence:

- `OUT1` is the LTC2964 channel-1 output and is released only while `1V8_DSP_REF_ANA` is valid.
- The former contract connected `OUT1` to the enable pins for `1V0_DSP_CORE`, `1V35_DSP_DMC`, `3V3_ADC_A`, and `2V8_MIC`; only `3V3_SYS` added `PGOOD_12V` qualification.
- Therefore microphone power, core power, and DMC power had the same single on/off state. Turning off the microphone branch by that path necessarily turned off core and DMC at the same time.
- Conversely, keeping core/DMC alive for DSP reset and the required post-reset hold also kept the microphone regulator enabled.
- The separate firmware-controlled `5V_AFE` enable did not correct the microphone dependency, and the former unspecified hardware override could not retain an ordered shutdown after the DSP had been reset.

This is the exact shared dependency that caused Phase 4B to stop. Phase 3E replaces it with (1) a retained downstream-run latch and hardware delay, and (2) a branch-local analog-power qualification path. The LTC2964 thresholds and `OUT1` function remain unchanged, but `OUT1` is no longer a direct downstream regulator-enable fanout.

## 2. Reconstructed pre-correction control topology

| Source / node | Pre-correction destination and behavior |
| --- | --- |
| `12V_PROTECTED` | Directly starts `3V8_PRE`; supplies amplifier PVDD/VBAT and the `3V3_SYS` input branch. |
| TPS3760A012 output | Open-drain `PGOOD_12V`, pulled to `3V8_PRE`; qualifies the system before the eFuse UVLO cutoff. |
| `PGOOD_12V` | Directly enables `1V8_DSP_REF_ANA`; one input of the `3V3_SYS` AND gate; hardware-safe input. |
| LTC2964 `OUT1` | Pulled to `3V8_PRE`; asserted/released from V1=`1V8_DSP_REF_ANA`; directly enabled core, DMC, ADC analog, and microphone rails. |
| `OUT1 AND PGOOD_12V` | `SN74LV1T08DBVR` output that enabled `3V3_SYS`. |
| LTC2964 common `RST` | `RAILS_OK`, pulled to `3V3_SYS`; asserted until V1/V2/V3/V4 are all valid for 160-240 ms; enables TPS3431. |
| TPS3431 `ENOUT` and `WDO` | Wired open drain at `SYS_HWRST`, pulled to `3V3_SYS`; hold/reset the DSP and contribute to the audio-safe state. |
| Buffered `AFE_EN_CMD` | Intended to enable only `5V_AFE`, with a 100-kohm pulldown and an unspecified hardware-fault override. |
| Amplifier MUTE/STANDBY | Passive pulldowns defined the safe state; release was intended to require both DSP command and a hardware-safe latch, but that latch/gating was not yet concrete. |
| Audio/MCLK output enables | Passive-disabled and intended to release only after DSP initialization and hardware-safe qualification. |

The supervisor and watchdog did provide valid reset behavior, but they did not provide an independent, retained, commanded downstream-off state. `OUT1` cannot be commanded low while V1 remains valid, and firmware cannot continue an ordered sequence after its own reset has asserted.

## 3. Corrected control architecture

The evaluated options were:

| Approach | Disposition |
| --- | --- |
| Preserve shared `OUT1` plus firmware order | Rejected: microphone and core/DMC remain inseparable, and firmware cannot finish after DSP reset. |
| Use another LTC2964 output | Rejected: `OUT2`-`OUT4` report their individual monitored rails; they do not provide commanded state retention or an independent analog override. |
| Open-drain wired logic only | Insufficient alone: it provides fault dominance but neither a retained normal-shutdown request nor a guaranteed post-reset hold. |
| Add a microcontroller/CPLD | Rejected as unnecessary additional boot/software/programming dependency. |
| Add separate load switches | Not required: the selected regulators already expose compatible EN pins. Analog signal isolation is still required independently. |
| Split regulator EN branches plus pre-powered latch/timer and fault latch | **Selected:** minimum deterministic hardware that preserves startup, survives DSP reset, permits analog-first shutdown, and defaults safe before firmware. |

Before using the retained-domain open-drain signals in latches or ordinary CMOS gates, condition raw `PGOOD_12V` and `EFUSE_FLT_N` through one exact `SN74LVC2G17DBVR` powered from `3V8_PRE`, with 0.1 uF bypass, to create `PGOOD_CLEAN` and `EFUSE_FLT_CLEAN_N`. The device operates from 1.65-5.5 V, has 5.5-V-tolerant Schmitt inputs and partial-power-down `Ioff`, and the exact SOT-23-6 orderable is fixed [SCHMITT]. Raw PGOOD still drives the 1.8-V regulator EN. The 3.3-V reset/amplifier-fault nodes are Schmitt-conditioned while crossing through `U_CMD_XLAT` below. This prevents unspecified slow open-drain edges from being applied directly to the D-flip-flop asynchronous input or non-Schmitt AND gates.

### 3.1 Retained downstream-run state

Fit one exact `SN74LVC1G74DCUR` (`U_SEQ_RUN`) powered from `3V8_PRE`, with 0.1 uF local bypass:

- `/PRE = PGOOD_CLEAN`;
- `/CLR = 3V8_PRE`;
- `D = GND`;
- `CLK = SHUTDOWN_CLK_3V8`;
- `Q = SEQ_RUN_Q`;
- `/Q = SEQ_SHUT`.

When `PGOOD_CLEAN` is low, asynchronous preset forces `SEQ_RUN_Q=1` and `SEQ_SHUT=0`. When PGOOD rises, that normal-run state is retained. A rising edge on `SHUTDOWN_CLK_3V8` captures D=0, so `SEQ_RUN_Q=0` and `SEQ_SHUT=1` remain stored after the DSP and `3V3_SYS` stop. The part operates from 1.65-5.5 V, accepts inputs to 5.5 V, provides partial-power-down `Ioff`, and the DCU VSSOP-8 orderable is fixed by `SN74LVC1G74DCUR` [SEQLATCH].

Carry `SHUTDOWN_REQ`, `SAFE_ARM_CMD`, `ANALOG_PWR_CMD`, Phase 3F `CLOCK_STARTUP_CMD`, `AUDIO_DATA_OE_CMD`, `RUN_HEALTH_OK_CMD`, raw `SYS_HWRST`, and raw `AMP_FAULT_N` from the 3.3-V domain through one exact `SN74LXC8T245PWR` (`U_CMD_XLAT`): VCCA=`3V3_SYS`, VCCB=`3V8_PRE`, DIR tied high to VCCA for A-to-B, `/OE=GND`, and 0.1 uF at each supply. All six DSP-command A inputs and all eight B outputs have 100-kohm pulldowns. The raw reset/fault A inputs retain their 10-kohm pullups plus 100-kohm pulldowns; their B outputs are `SYS_HWRST_CLEAN` and `AMP_FAULT_CLEAN_N`. All eight channels are used. The translator has Schmitt-trigger inputs, operates across 1.08-5.5 V on either rail, is specified from -40 C to +125 C, and provides `Ioff`, VCC-disconnect/isolation, and high-impedance I/O when either supply is absent [CMDXLAT; Phase 3F].

Qualify translated `SHUTDOWN_REQ_3V8` with `PGOOD_CLEAN` in an exact `SN74LV1T08DBVR`, powered and bypassed from `3V8_PRE`, to form `SHUTDOWN_CLK_3V8`. Thus an unpowered DSP or missing 3.3-V translator rail cannot create a shutdown clock, cannot back-power the pre domain, and brownout uses the separate immediate PGOOD path instead.

Fit one exact `SN74LVC2G07DBVR` powered from `3V8_PRE`, with 0.1 uF bypass. Channel 1 buffers `SEQ_RUN_Q` to the open-drain `SYS_HWRST` node: Q high releases the output and Q low pulls reset low. Channel 2 buffers `PGOOD_CLEAN` to that same wired open-drain node: PGOOD high releases it and PGOOD low asserts reset immediately, independent of downstream rail decay. The part is specified for 1.65-5.5 V operation, open-drain output, 5.5-V-tolerant inputs, and `Ioff`; no unpowered 3.3-V reset-domain injection is created [RSTBUF].

### 3.2 Guaranteed post-reset downstream hold

Fit one exact `TPS3760E012DYYR` (`U_DOWN_DELAY`), using the already-approved TPS3760 family evidence, powered from `3V8_PRE`:

- `SENSE = SEQ_SHUT`;
- use the adjustable 0.8-V overvoltage, active-low, open-drain selection;
- `CTS = 220 nF` nominal, required effective range 198-242 nF over tolerance, DC bias, temperature, and aging;
- `CTR/MR` open;
- pull `RESET` up to `3V8_PRE` with 10.0 kohm and name it `DOWNSTREAM_RUN_DELAYED`.

During normal run, `SEQ_SHUT=0` and `DOWNSTREAM_RUN_DELAYED=1`. After the shutdown latch changes state, the overvoltage sense timer pulls `DOWNSTREAM_RUN_DELAYED` low. Using the published CTS resistance and no-cap delay bounds, the required capacitor range gives:

```text
tCTS(min) = -ln(0.31) * 88 kohm * 198 nF + 8 us  = 20.415 ms
tCTS(max) = -ln(0.25) * 122 kohm * 242 nF + 17 us = 40.946 ms
```

The hardware therefore guarantees at least 20 ms between `SYS_HWRST` assertion and downstream-regulator disable. `U_DOWN_DELAY` can add up to its documented 2 ms startup delay during power-up; this occurs before the downstream rails start and does not reduce the later 330-470 ms reset-release interval [PGSUP]. The datasheet requires at least 10% of the programmed sense delay between fault events for complete CTS discharge; the 330-ms minimum reset/boot qualification before any new commanded shutdown is far longer than the 4.095-ms worst-case requirement.

### 3.3 Downstream enable fanout

Create:

```text
DOWNSTREAM_EN = OUT1 AND PGOOD_CLEAN AND DOWNSTREAM_RUN_DELAYED
```

Use two cascaded exact `SN74LV1T08DBVR` gates, each powered from `3V8_PRE`, each with 0.1 uF bypass, and no floating input. Add a 100-kohm pulldown at every destination EN pin. `DOWNSTREAM_EN` replaces the former direct `OUT1` connection at:

- `1V0_DSP_CORE` TPS62135 EN;
- `1V35_DSP_DMC` TPS7A4901 EN;
- `3V3_SYS` TPS62135 EN;
- `3V3_ADC_A` TPS7A2033P EN.

It does **not** drive `2V8_MIC` or `5V_AFE`. `1V8_DSP_REF_ANA` remains enabled directly by `PGOOD_12V`, and `3V8_PRE` remains enabled directly from `12V_PROTECTED`. This preserves VDD_REF-before-VDD_EXT startup and provides a retained downstream-off state without making a monitored rail control itself.

### 3.4 Hardware-safe authorization latch

Fit a second exact `SN74LVC1G74DCUR` (`U_SAFE_LATCH`) powered from `3V8_PRE`, with 0.1 uF bypass:

- `/PRE = 3V8_PRE`;
- `/CLR = SAFE_CLEAR_N`;
- `D = 3V8_PRE`;
- `CLK = SAFE_ARM_3V8`;
- `Q = HW_RUN_LATCHED`.

Form the four-hardware-input term with three cascaded `SN74LV1T08DBVR` gates powered from `3V8_PRE`:

```text
SAFE_HW_CLEAR_N = PGOOD_CLEAN AND SYS_HWRST_CLEAN AND EFUSE_FLT_CLEAN_N AND AMP_FAULT_CLEAN_N
SAFE_CLEAR_N = SAFE_HW_CLEAR_N AND RUN_HEALTH_OK_3V8
```

Raw `PGOOD_12V` and `EFUSE_FLT_N` use 10-kohm pullups to `3V8_PRE`. Raw `SYS_HWRST` and `AMP_FAULT_N` use 10-kohm pullups to `3V3_SYS` plus 100-kohm pulldowns to ground so absence of the 3.3-V domain is a defined LOW. At the Phase 3D rail bounds, the 10-kohm/100-kohm network is at least 2.960 V at nominal 3.256 V minimum, above the Schmitt buffer's required high threshold; its current is included in the existing rail load allowance. Phase 3F adds a second `SN74LVC2G08DCUR` at `3V8_PRE`: one channel forms final `SAFE_CLEAR_N`, and the other forms `CLOCK_STARTUP_EN = SYS_HWRST_CLEAN AND CLOCK_STARTUP_CMD_3V8`. A low on any conditioned hardware input or `RUN_HEALTH_OK_3V8` asynchronously clears `HW_RUN_LATCHED`.

Create `SAFE_ARM_3V8` from translated `SAFE_ARM_CMD_3V8 AND SYS_HWRST_CLEAN` in an `SN74LV1T08DBVR`. The DSP must first establish Phase 3F bootstrap clocks, verify ADC PLL/configuration, complete amplifier I2C configuration/readback with no presently asserted fault, and assert `RUN_HEALTH_OK_CMD`; it then generates a deliberate arm edge. Active amplifier clock validation follows in Hi-Z before MUTE/PLAY. Bootstrap clocks do not require the arm edge. Clearing a fault or restoring health never recreates it, so the system cannot return automatically to analog-on or PLAY.

## 4. Dedicated microphone / AFE override

Rename the former single-branch `AFE_EN_CMD` concept to `ANALOG_PWR_CMD`. Use the translated and passively pulled-down `ANALOG_PWR_CMD_3V8` from `U_CMD_XLAT`, then create:

```text
ANALOG_PWR_EN = DOWNSTREAM_EN AND HW_RUN_LATCHED AND ANALOG_PWR_CMD_3V8
```

Use two cascaded exact `SN74LV1T08DBVR` gates powered from `3V8_PRE`. Drive both of these enable pins from `ANALOG_PWR_EN`, each with a local 100-kohm pulldown:

- `TPS7A2028PDBVR` EN for `2V8_MIC`;
- `TPS7A4901DGNR` EN for `5V_AFE`.

This is the dedicated override. It can force both microphone and AFE power off while core, DMC, ADC, 3.3 V, and 1.8 V remain on. It cannot be defeated by firmware because `HW_RUN_LATCHED=0` dominates the AND chain.

Electrical checks:

| Check | Result |
| --- | --- |
| Polarity | Both regulator EN pins are active high; `ANALOG_PWR_EN=0` is OFF. |
| Startup default | The command pulldown and cleared safe latch hold both rails off until DSP boot and an explicit arm/command. |
| PGOOD absent / brownout | `DOWNSTREAM_EN=0` immediately and `HW_RUN_LATCHED` asynchronously clears; both EN pins are low. |
| DSP unpowered | Command-translator VCC isolation plus A/B-side pulldowns and the hardware AND terms prevent a false enable or back-power path. |
| Logic voltage | Gate output is 0 to `3V8_PRE` (3.746849-3.841293 V). TPS7A20 EN allows 0-6 V recommended and 6.5 V absolute maximum; TPS7A49 EN permits up to VIN and 36 V absolute maximum, with VIN=`12V_PROTECTED`. HIGH exceeds both maximum VIH requirements and LOW is ground [LDO; HVLDO]. |
| Back-powering through EN | The command translator isolates if either logic rail is absent; the pre-powered gate drives only regulator EN inputs whose input rails remain present whenever PGOOD is accepted. Local pulldowns define OFF during collapse. |
| Power-down | TPS7A20 P has output discharge; TPS7A49 does not. Phase 3D preloads remain mandatory. The analog isolation switches below open with the enable command, including the microphone-to-AFE paths, so safety does not depend on unequal regulator ramp/discharge time. |

No additional load switch is required. The existing regulator enables now provide the independent control; the exact logic parts are fixed here and are not left for Phase 4B selection. Retain ten `SN74LV1T08DBVR`: one shutdown-clock qualifier, two downstream-enable gates, three `SAFE_HW_CLEAR_N` gates, one safe-arm gate, two analog-enable gates, and one serial-data-OE release gate. Phase 3F adds a second `SN74LVC2G08DCUR` for final safe clear and bootstrap-clock enable; the original dual gate still implements the two amplifier releases. Use one 0.1 uF local bypass per logic device.

## 5. Frozen event sequences

### 5.1 Normal startup

1. TPS26630 validates and ramps `12V_PROTECTED`; passive pulldowns hold amplifier MUTE/STANDBY low, endpoint clock/data OEs disabled, ADC reset asserted, run health low, and analog power off.
2. `3V8_PRE` starts directly. The input TPS3760 then releases `PGOOD_12V` after its protected-input threshold is valid.
3. `PGOOD_12V` asynchronously presets `U_SEQ_RUN` to run and enables `1V8_DSP_REF_ANA`. `U_SAFE_LATCH` remains cleared because `SYS_HWRST` is low.
4. Valid V1 releases LTC2964 `OUT1`. With PGOOD high and the downstream-delay supervisor in its normal state, `DOWNSTREAM_EN` starts core, DMC, `3V3_SYS`, and ADC analog power.
5. The oscillator/fanout settle and provide `SYS_CLKIN0`. LTC2964 holds `RAILS_OK` low until all four monitored rails are valid for 160-240 ms; TPS3431 then holds `SYS_HWRST` low for another 170-230 ms.
6. DSP reset releases and ROM boots SPI2. Firmware establishes safe GPIO, configures SPORT clock generation, TWI, DMA, and watchdog service. Analog power, serial data, and amplifier release remain hardware-blocked.
7. `RAILS_OK` has already released ADC/amplifier MCLK before DSP reset release. Firmware asserts `CLOCK_STARTUP_CMD`; Phase 3F `CLOCK_STARTUP_EN` releases only the BCLK/FSYNC buffer bank. With clocks stable, firmware releases the independently controlled ADC reset, observes the ADAU1978 DVDD/timing contract, and configures/verifies its PLL. It configures/read backs the amplifier over I2C while STANDBY remains LOW and confirms no presently asserted fault; no unsupported claim is made that clock monitoring is active in STANDBY.
8. Firmware asserts `RUN_HEALTH_OK_CMD` and then pulses `SAFE_ARM_CMD`. After `HW_RUN_LATCHED=1`, it may enable serial data and release amplifier STANDBY only into programmed Hi-Z. It verifies active clocks/no fault there; any `FAULT_N` clears the latch before MUTE/PLAY.
9. Only after that active amplifier check may firmware set `ANALOG_PWR_CMD=1`. After microphone startup and AFE/ADC settling, valid DMA frames, coefficients, and no fault, firmware may release MUTE in the approved ramp-to-PLAY order.

### 5.2 Normal commanded shutdown

1. Assert amplifier MUTE, command all channels Hi-Z, then assert STANDBY low. Keep STANDBY low for at least 15 ms before amplifier VDD removal.
2. Set `ANALOG_PWR_CMD=0`. This opens the analog isolation switches and disables both `2V8_MIC` and `5V_AFE` while DSP core/DMC remain powered. Wait at least 1 ms before step 3 so the ordered command state is unambiguous; physical rail decay remains a Phase 4 transient measurement.
3. Disable the serial-data bank and assert ADC PD/RST. Drop `RUN_HEALTH_OK_CMD` so `HW_RUN_LATCHED` clears, then deassert `CLOCK_STARTUP_CMD`; BCLK/FSYNC stop. MCLK remains until the later downstream-rail removal makes `RAILS_OK` fall, so every endpoint clock stops only after the ADC and amplifier are safe.
4. Pulse `SHUTDOWN_REQ`. `U_SEQ_RUN` immediately asserts `SYS_HWRST` through the open-drain buffer and retains the shutdown state after the DSP stops.
5. `U_DOWN_DELAY` holds `DOWNSTREAM_RUN_DELAYED` high for 20.415-40.946 ms, then deasserts `DOWNSTREAM_EN`. `3V3_SYS`, DMC, core, and ADC analog regulators turn off together.
6. The state after step 5 is a latched service-off state: `3V8_PRE` and `1V8_DSP_REF_ANA` remain on, but in-place restart is intentionally prohibited. For full normal power-off, the external source removes `12V_IN` only after step 5; PGOOD then falls and disables 1.8 V last while presetting the run latch for the next cold start. Amplifier VDD is therefore removed before protected PVDD/VBAT. Restart from service-off requires a deliberate PGOOD-low power cycle and then follows the full startup sequence.

The normal sequence depends on firmware only to request a graceful shutdown while it is healthy. The latch and timer complete the reset/rail removal portion after firmware execution has ceased. Any failure to perform the graceful preliminaries enters the fault-safe behavior below, not an unsafe PLAY state.

### 5.3 Brownout or abrupt input loss

1. The Phase 3A TPS3760 pulls `PGOOD_12V` low at its 9.870-10.130 V falling bound, before the eFuse reaches its lower cutoff bound.
2. Low PGOOD immediately clears `HW_RUN_LATCHED`, forces `DOWNSTREAM_EN=0`, asserts amplifier MUTE/STANDBY and ADC/DSP reset through their hardware paths, disables serial data, and makes `SYS_HWRST_CLEAN=0`, which removes `CLOCK_STARTUP_EN` from BCLK/FSYNC. Rail invalidity then pulls `RAILS_OK` low and disables the MCLK translator; both analog regulators turn off.
3. `PGOOD_12V` also disables `1V8_DSP_REF_ANA`; protected/pre power may collapse afterward. No ordered 15-ms or 20-ms ride-through is claimed during an abrupt energy loss.
4. On voltage recovery the hardware repeats normal rail/reset startup, but `HW_RUN_LATCHED` remains zero. Firmware must boot, revalidate every endpoint, and issue a new arm edge; automatic PLAY is prohibited.

### 5.4 DSP reset, watchdog timeout, or JTAG reset/halt

1. `SYS_HWRST` asserts low first and asynchronously clears `HW_RUN_LATCHED`.
2. Analog power turns off, analog switches open, amplifier MUTE/STANDBY assert, serial-data OE disables, and low `SYS_HWRST_CLEAN` removes `CLOCK_STARTUP_EN` from BCLK/FSYNC. `RAILS_OK` remains high on healthy rails, so endpoint MCLK and the independent DSP root clock remain active for deterministic recovery.
3. Core, DMC, 3.3 V, ADC analog, and 1.8 V remain enabled if their rails and PGOOD remain valid. This permits a supervised reboot and fault diagnosis; a watchdog event is not treated as an input-power failure.
4. TPS3431 provides the already-approved 170-230 ms reset assertion. Recovery requires complete initialization and a new `SAFE_ARM_CMD` edge before analog/audio release.

### 5.5 System or amplifier fault

- eFuse fault: `EFUSE_FLT_N=0` clears the safe latch immediately. PGOOD loss then shuts down the rail tree as in brownout.
- amplifier `FAULT_N=0`: clears the safe latch, forces MUTE/STANDBY and analog power off, but does not by itself remove DSP rails or assert DSP reset. The DSP may read the sticky amplifier fault registers from the safe state. Recovery requires fault clearance, complete checks, and a new arm edge.
- monitored rail failure: LTC2964 common `RST` asserts `RAILS_OK=0`; TPS3431/SYS_HWRST asserts, clearing the safe latch. If V1 fails, `OUT1` also disables all downstream rails. If V2, V3, or V4 fails, its regulator remains enabled for recovery while reset stays asserted; feeding `RAILS_OK` back into those EN pins is prohibited because that would make a rail control itself.
- ADC PLL/data fault: mandatory `PLL_MUTE=1` mutes ADAU1978 data in hardware. Firmware immediately drops `RUN_HEALTH_OK_CMD`, serial data, and amplifier releases, then resets/reinitializes ADC/SPORT while bootstrap clocks may remain present. If firmware fails, watchdog reset clears the latch and endpoint clocks. A new arm edge is mandatory [Phase 3F].

## 6. Hardware-safe defaults

| Domain | Before DSP boot | Normal enabled state | Reset/watchdog/fault state |
| --- | --- | --- | --- |
| Microphones | `2V8_MIC` EN low; regulator output discharge and preload fitted | Enabled only by safe latch plus explicit analog command | EN forced low independently of core/DMC |
| AFE | `5V_AFE` EN low; TMUX paths open | Enabled with microphones only after arm/command | EN low; preload discharges rail; analog paths open |
| ADC | AVDD/IOVDD may be present; PD/RST asserted; MCLK becomes active after `RAILS_OK`; BCLK/FSYNC and data remain disabled | BCLK/FSYNC may be enabled before arm; reset then releases for PLL/configuration checks; data and analog inputs remain isolated | Reset asserted on system reset; data/BCLK/FSYNC disabled; MCLK remains while rails are valid for deterministic recovery; AINs isolated if AFE or ADC domain is off |
| DSP | Held in reset until the 330-470 ms rail-valid chain completes | Runs only with all monitored rails valid and watchdog active | Reset asserted by rail supervisor, watchdog, JTAG, or retained shutdown path |
| Amplifier | MUTE and STANDBY low by passive pulldowns; endpoint clocks/data initially disabled; outputs Hi-Z | MCLK/BCLK/FSYNC may precede arm so clock presence can be established; active fault validation occurs after arm in programmed Hi-Z and before MUTE/PLAY, while data and each functional release require the safe latch | Hardware removes release, returns outputs to mute/Hi-Z, and prohibits automatic PLAY; clocks may remain for diagnosis only while DSP/reset/rails are healthy |
| Speakers | Both BTL legs remain undriven/Hi-Z | Energized only after full initialization and ramp-to-PLAY | Hi-Z; neither terminal is grounded |

Implement `AMP_MUTE_RELEASE = HW_RUN_LATCHED AND AMP_MUTE_CMD` and `AMP_STBY_RELEASE = HW_RUN_LATCHED AND AMP_STBY_CMD` with one exact `SN74LVC2G08DCUR` powered from `3V3_SYS`, with 0.1 uF bypass; retain external amplifier-pin pulldowns. Its inputs tolerate the pre-domain `HW_RUN_LATCHED` high level, and its specified `Ioff` prevents that retained high from back-powering an absent 3.3-V domain [AMPGATE]. Phase 3F supersedes the former combined audio/MCLK OE: `RAILS_OK` controls the MCLK translator, `CLOCK_STARTUP_EN` controls only the BCLK/FSYNC bank before arm, and `AUDIO_DATA_OE_RELEASE = HW_RUN_LATCHED AND AUDIO_DATA_OE_CMD_3V8` controls only the serial-data bank. All OEs retain pullup-disabled defaults and separate NMOS sinks.

## 7. Cross-domain back-power audit and correction

The digital isolation already frozen in Phase 3 remains valid, but the former assertion that sequencing plus 47-ohm AFE output resistors prevented all analog back-power was insufficient. Abrupt loss can leave `5V_AFE` charged while `3V3_ADC_A` is off, and ADC VREF could drive an unpowered AFE VCM input. Series resistance alone is not an authorization to drive an unpowered device.

### 7.1 Required analog isolation

Fit the exact Phase 3G population: ten `TMUX2821DSGR` dual SPST devices and four `TMUX1574PWR` quad SPDT devices [ANISO; MICISO3G]. Every analog crossing uses two series switches, one powered from each adjacent domain, so loss of either rail opens at least one switch:

- AFE-to-ADC: use eight devices for eight differential legs. In every leg place one `5V_AFE`-powered switch and one `3V3_ADC_A`-powered switch in series after the 47-ohm resistor and before the ADAU1978 AIN pin. Four devices belong to each supply domain.
- ADC-VREF-to-AFE: use two TMUX2821 devices and one channel of each in series, one device powered from `3V3_ADC_A` and one from `5V_AFE`, between the Sheet 4 OPA320-buffered VREF and the Sheet 3 OPA2192 VCM-buffer input. Tie each unused-channel SEL low and leave its S/D pins unconnected.
- Microphone-to-AFE: use four TMUX1574 devices for eight differential legs. Two devices are powered from `2V8_MIC` and two from `5V_AFE`; each package carries four independently preserved `P/N/P/N` legs. In every leg cascade one selected switch from each adjacent domain between the Sheet 7 100-ohm RF resistor and the Sheet 3 4.7-uF coupling capacitor. Tie `EN` and `SEL` low, use the `SxA-Dx` paths, and ground unused `SxB` pins exactly as Phase 3G specifies.
- Bypass every switch VDD with 0.1 uF. TMUX2821 used SEL inputs follow `ANALOG_PWR_EN`; TMUX1574 paths use their powered-domain loss for isolation and are statically selected as above.
- Keep the paired AIN switch routing and parasitics symmetrical. Phase 4 must verify AFE settling, noise, CMRR, and ADC drive stability with the switch included.

TMUX2821 operates from 1.8-5.5 V, accepts analog signals from -5.5 V to +5.5 V independent of VDD, provides fail-safe SEL inputs to 5.5 V, has a defined SEL pulldown, and specifies powered-off high-impedance behavior [ANISO]. TMUX1574 operates from 1.5-5.5 V, accepts the bounded microphone range on both powered domains, has fail-safe controls and provides powered-off high impedance for the bounded 0-3.6 V microphone signal [MICISO3G]. Each selected rail minimum is inside the relevant VDD range. Paired devices therefore isolate charged AFE outputs, buffered ADC VREF, and microphone outputs for failure or discharge of either adjacent rail. Published typical on-resistance is not used to waive the required analog simulation and bench validation.

### 7.2 Remaining crossings

| Crossing | Back-power disposition |
| --- | --- |
| DSP/ADC/amplifier TDM | Existing `SN74LVC244A` has partial-power-down `Ioff`; its clock and data banks have independent passive-disabled OEs. Phase 3F permits only BCLK/FSYNC before arm and retains data isolation. |
| MCLK | Existing `SN74AXC2T245` power-supply isolation remains mandatory. Its OE sink is driven directly by `RAILS_OK`, not firmware or `HW_RUN_LATCHED`; either missing supply still makes the I/O high impedance. |
| I2C/TWI | DSP, ADC IOVDD, and amplifier VDD share `3V3_SYS` and the pullups are on that same rail. No hot-plug or pullup to a retained rail is permitted. |
| SPI boot | Both endpoints and boot buffer share `3V3_SYS`; the buffer has `Ioff`. The separate command translator isolates the three DSP-to-pre controls if either logic rail is absent. External debug equipment must not drive an unpowered target. |
| Reset/fault | Open-drain nodes use destination-domain pullups. The pre-powered `SN74LVC2G07` is open drain and has `Ioff`; it never sources `SYS_HWRST`. |
| Enables | Pre-powered `SN74LV1T08` outputs remain within each EN pin's documented limits. EN pulldowns prevent floating during collapse. |
| DSP root clock | DSP and LMK use the same retained 1.8-V domain; there is no separate powered-off crossing. |
| Microphone to AFE | AC coupling and series resistance remain, but equal EN commands do not guarantee equal rail ramps. Paired series TMUX1574 switches cover all eight differential legs and are powered from `2V8_MIC` and `5V_AFE`, so loss of either rail opens every leg. |
| AFE to ADC / buffered ADC VREF to AFE | Paired series TMUX2821 switches are powered from both adjacent domains, so loss of either side opens the path. No clamp-diode tolerance is assumed. |

No additional series resistor or digital isolator is required for the defined power states. Any later connector or off-board pullup creates a new interface state and requires a new back-power review.

## 8. End-to-end sequencing audit

| Audit item | Result | Basis |
| --- | --- | --- |
| Startup ordering | PASS as amended by Phase 3F | Pre -> PGOOD -> 1.8 V/root clock -> `OUT1`/downstream -> all-rail delay/MCLK -> watchdog delay -> DSP boot -> BCLK/FSYNC -> ADC PLL and amplifier pre-arm configuration -> explicit arm -> amplifier Hi-Z clock check -> data/analog/MUTE/PLAY release. |
| Normal shutdown | PASS as amended by Phase 3F | Amplifier/analog/data safe first; run authorization clears; endpoint clocks stop; retained latch asserts DSP reset; hardware timer preserves >=20 ms; downstream rails then turn off; 1.8 V is last on full source removal. |
| Brownout | PASS | Schmitt-conditioned PGOOD is a direct term in downstream and analog control and asynchronously clears safe authorization before eFuse cutoff. |
| Watchdog / DSP reset | PASS | Safe latch clears, BCLK/FSYNC/data and analog/audio enter safe state, while endpoint MCLK and the independent root clock remain available on healthy rails for supervised reboot. |
| Rail failure / recovery | PASS | Common reset dominates; V1 can remove downstream; no V2/V3/V4 enable is qualified by its own `RAILS_OK`; rearm is explicit. |
| Circular dependency | **Superseded by Phase 3F** | The power-enable graph here is acyclic, but the former post-arm MCLK gate was circular with the pre-arm ADC PLL check. Phase 3F enables MCLK from `RAILS_OK`, uses independent `CLOCK_STARTUP_EN` for BCLK/FSYNC, and audits amplifier clock-fault arming as well. |
| Enable overstress | PASS | `SN74LV1T08` output is bounded by `3V8_PRE`; TPS62135, TPS7A20, and TPS7A49 enable limits remain satisfied. |
| Powered-off interfaces | PASS for schematic entry | Concrete `Ioff` digital parts and powered-off analog switches are defined; physical leakage/settling tests remain required. |
| Phase 3D voltage/margin calculations | UNCHANGED | No rail source, divider, preload, LTC2964 threshold, input range, or allocated load maximum is changed. Added pre-rail logic remains below the existing 20 mA supervisor/logic allocation. Phase 3G totals are at most 0.136 mA of TMUX1574 on the 5 mA microphone allocation; 0.70 mA of TMUX2821 plus 1.85 mA OPA320 on the 30 mA ADC allocation; and 0.70 mA TMUX2821 plus 0.136 mA TMUX1574 plus 15 mA OPAx192 on the 50 mA AFE allocation. Populated-BOM totals must remain within those frozen limits. |

The architecture has no stored state powered by a rail it controls. Both D flip-flops, the shutdown timer, and all upstream enable qualification are powered from unconditional `3V8_PRE`. The shutdown latch is preset by low PGOOD; the safe latch is cleared by low PGOOD/reset/fault. Recovery therefore has a defined state even after arbitrary loss of downstream rails.

## 9. Exact superseding implementation instructions

These instructions supersede only the conflicting enable/safe-state portions of Phase 3 and Phase 3D. All regulator variants, rail sources, feedback dividers, preloads, capacitance limits, supervisor dividers/delays, and voltage/margin calculations remain frozen.

1. Do not connect `OUT1` directly to any regulator EN. Implement `DOWNSTREAM_EN` exactly as section 3.3 and use it for core, DMC, `3V3_SYS`, and ADC analog EN.
2. Implement `U_SEQ_RUN`, `U_DOWN_DELAY`, and the open-drain reset buffer exactly as sections 3.1-3.2. Preserve the effective 198-242 nF CTS bound.
3. Implement `U_SAFE_LATCH`, Phase 3F final `SAFE_CLEAR_N` including `RUN_HEALTH_OK_3V8`, all stated pull networks, and the explicit firmware rearm edge. No fault or health recovery may automatically restore analog or PLAY.
4. Implement `U_CMD_XLAT` with all eight Phase 3F channel assignments; do not route those signals through spare boot-buffer channels or directly into a pre-powered LV1T input.
5. Drive both microphone and AFE regulator EN pins from `ANALOG_PWR_EN`; do not preserve the former direct microphone-on-`OUT1` or AFE-only command paths.
6. Implement the Phase 3G exact ten-`TMUX2821DSGR` plus four-`TMUX1574PWR` analog-isolation population and paired-domain assignments before connecting microphone outputs, AFE outputs, or buffered ADC VREF across independently powered domains.
7. Preserve passive-safe defaults for ADC/DSP reset, amplifier MUTE/STANDBY, endpoint clock/data OEs, run-health and clock commands, flash pins, and boot straps. Implement the exact Phase 3F ADC reset and split MCLK/serial-clock/data OE circuits; `RAILS_OK` is the sole MCLK translator enable source.
8. Expose the Phase 3E test points plus `SAFE_HW_CLEAR_N`, `CLOCK_STARTUP_EN`, `RUN_HEALTH_OK_3V8`, the separate MCLK/clock/data OEs, `ADC_PD_RST_N`, and ADAU1978 DVDD.
9. During a separately authorized Phase 4B continuation, verify every new symbol pin/package against its cited manufacturer document, run ERC, and perform transient checks for startup, graceful shutdown, brownout, watchdog, each monitored-rail failure, clock/PLL loss, and recovery. KiCad work remains unauthorized in Phase 3E/3F.

## 10. Remaining unknowns and validation boundary

The control-component selections and topology are no longer unknown. The following are implementation/physical-validation items and do not authorize a component substitution:

- effective CTS capacitor value must be proven within 198-242 nF over its selected part's tolerance, bias, temperature, and aging;
- populated rail loads must include every new logic gate, TMUX2821, TMUX1574, OPA320 and OPAx192 without exceeding the existing Phase 3D allocations;
- oscilloscope evidence must verify reset assertion precedes rail invalidity, the normal-shutdown 20-ms minimum, DSP rail rise/fall >=100 us, the 1.8-V-last relationship, and no restart into PLAY;
- simulation and bench work must verify AFE stability, ADC settling, CMRR/noise impact, switch leakage, and absence of back-power in every power permutation;
- amplifier fault-pin startup behavior and all passive safe defaults must be confirmed on the populated assembly;
- Phase 3F ADAU1978 CEXT effective maximum, 3.00-kohm discharge path, at least 50 ms in-place reset pulse, DVDD charge/readiness behavior, and PLL lock sequence must be reproduced on the populated assembly;
- the MCLK, BCLK/FSYNC, and data OE transitions must be checked over loaded PVT, and firmware/watchdog tests must demonstrate that ADC-only PLL loss drops run health and cannot return automatically to PLAY;
- abrupt source removal cannot guarantee the graceful 15-ms/20-ms waits; safety in that case is mute/reset/Hi-Z and immediate enable removal, not audio ride-through.

The clock/arm contradiction discovered after this document is resolved by Phase 3F at the contract level. Neither Phase 3E nor Phase 3F authorizes Phase 4B continuation.

PHASE 3E: PASS
