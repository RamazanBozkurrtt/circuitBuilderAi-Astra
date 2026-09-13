# Phase 3F - Clock startup / arming dependency correction

Date: 2026-09-13 (Europe/Istanbul)  
Scope: documentary correction of the clock-bootstrap, ADC-reset, arming, and associated fault/shutdown contracts only. No KiCad file was created or modified, and Phase 4B was not resumed.

Evidence notation uses the existing IDs and local official manufacturer documents already indexed for ADAU1978 Rev. B (`ADC`), ADSP-2156x Rev. D (`DSP`), TAS6424E-Q1 Rev. A (`AMPE`), ASDLJ Rev. A (`CLKOSC`), LMK1C1103 Rev. D (`CLKBUF`), SN74AXC2T245 Rev. A (`CLKXLAT`), SN74LVC244A Rev. AG (`LVBUF`), onsemi BSS138L Rev. 14, and the Phase 3E control logic. No new authoritative source was introduced, so the evidence index is unchanged. Device facts are `CONFIRMED`; the corrected topology and signal equations are approved project decisions.

This document supersedes only the Phase 3/3E statements that placed MCLK or all serial-audio outputs behind `HW_RUN_LATCHED`, and the related startup/fault wording. Phase 3D rail sources, ranges, dividers, preloads, thresholds, delays, and load allocations are unchanged.

## 1. Circular dependency

The pre-correction startup path was:

1. `12V_PROTECTED` becomes valid and `3V8_PRE` starts.
2. `PGOOD_12V` enables `1V8_DSP_REF_ANA`; the oscillator and LMK fanout start.
3. LTC2964 `OUT1`, `PGOOD_CLEAN`, and `DOWNSTREAM_RUN_DELAYED` create `DOWNSTREAM_EN`, which starts DSP core/DMC, `3V3_SYS`, and `3V3_ADC_A`.
4. LTC2964 validates all monitored DSP rails; `RAILS_OK` enables TPS3431; `SYS_HWRST` releases after the 160-240 ms plus 170-230 ms delays.
5. ADSP-21569 boots from its independent `SYS_CLKIN0` clock.
6. Phase 3E required the ADC/amplifier MCLK translator and the SN74LVC244A serial-audio buffer to release only through `HW_RUN_LATCHED AND AUDIO_OE_CMD`.
7. Phase 3/3D/3E required firmware to release/configure the ADAU1978, verify `PLL_LOCK`, and only then pulse `SAFE_ARM_CMD` to set `HW_RUN_LATCHED`.

The exact circular path was therefore:

```text
HW_RUN_LATCHED
  -> MCLK translator enabled
  -> ADAU1978 receives MCLKIN
  -> ADAU1978 PLL can acquire lock
  -> firmware can verify PLL_LOCK
  -> SAFE_ARM_CMD is permitted
  -> HW_RUN_LATCHED
```

With the latch cleared at startup, MCLK could never reach ADAU1978. No delay, register retry, or firmware ordering change could create the missing clock. The Phase 4B reachability result was correct: the contract admitted no reachable `(HW_RUN_LATCHED=1, PLL verified=1)` state.

## 2. Root cause

The root cause was not the oscillator, rail sequence, ADC, or PLL. It was the use of one post-arm functional authorization for two different classes of resource:

- **bootstrap resources**, which must be available to establish whether arming is allowed; and
- **hazardous functional releases**, which must remain blocked until arming is complete.

MCLK and the pre-arm clock-validation path were incorrectly classified as hazardous functional releases. Amplifier MUTE/STANDBY, microphone/AFE power, serial audio data, and PLAY authorization are the actual hazardous releases. Clock availability alone does not authorize TAS6424E-Q1 PLAY: STANDBY low produces Hi-Z outputs, MUTE is independently active low, and channel state defaults to Hi-Z [AMPE pp.33-35, 43].

## 3. Corrected bootstrap clock architecture

### 3.1 Selected option

Select a minimal combination of **Option A for MCLK** and a narrow **Option B for SPORT clocks**:

- the required ADC/amplifier MCLK translator is enabled automatically by existing hardware `RAILS_OK`, independently of firmware and `HW_RUN_LATCHED`; and
- a separate hardware-qualified `CLOCK_STARTUP_EN` permits the DSP-generated BCLK/FSYNC bank before `HW_RUN_LATCHED`, after SPORT pins are configured.

```text
CLOCK_STARTUP_EN = SYS_HWRST_CLEAN AND CLOCK_STARTUP_CMD_3V8
```

`CLOCK_STARTUP_EN` does not depend on `HW_RUN_LATCHED`, `SAFE_ARM_CMD`, ADC `PLL_LOCK`, amplifier `FAULT_N`, microphone power, AFE power, serial data validity, or PLAY state. Its default is LOW. It may be asserted only after the DSP has booted, configured SPORT clock generation, and driven the command deliberately.

There is no additional MCLK-enable state machine or firmware command. `RAILS_OK` is the exact MCLK enable source. It rises only after all four monitored DSP rails, including both SN74AXC2T245 supplies, have remained valid for the LTC2964 160-240 ms delay. It does not control any of those rail enables, so using it for MCLK cannot create a power cycle.

The root-clock sources remain hardware-started:

- ASDLJ OE remains pulled active to `1V8_DSP_REF_ANA`.
- LMK1C1103 `1G` remains pulled high to `1V8_DSP_REF_ANA` through 10 kohm.
- LMK output 0 continues directly to ADSP-21569 `SYS_CLKIN0`; it is never gated by `CLOCK_STARTUP_EN` or `HW_RUN_LATCHED`.
- LMK outputs 1 and 2 continue to the A ports of the dual SN74AXC2T245 for ADC and amplifier MCLK. Its passive-disabled `/OE` sink is driven directly by `RAILS_OK`, so both endpoint MCLKs become available before DSP reset release.

The SN74LVC244A clock-bank `/OE` is released by a separate passive-disabled NMOS sink driven by `CLOCK_STARTUP_EN`. This makes buffered BCLK/FSYNC available after SPORT configuration for endpoint clock qualification. The SN74AXC2T245 remains isolated while either supply is absent and permits either rail order without an output glitch [CLKXLAT pp.18-23].

The SN74LVC244A data bank is separate:

```text
AUDIO_DATA_OE_RELEASE = HW_RUN_LATCHED AND AUDIO_DATA_OE_CMD_3V8
```

It remains disabled before arming. Microphone/AFE power and amplifier release retain their Phase 3E latch qualification. This is not an early enable of the complete audio chain.

### 3.2 Required pre-arm clocks

| Clock | Required before `HW_RUN_LATCHED` | Reason and operating boundary |
| --- | --- | --- |
| ADAU1978 MCLKIN, 24.576 MHz | **Yes; automatic after `RAILS_OK`** | The selected MCLK-input PLL cannot lock or report `PLL_LOCK=1` without stable MCLK. MCS=`011` is the 24.576 MHz setting at 96 kHz [ADC pp.12-14, 29]. |
| ADSP-21569 `SYS_CLKIN0`, 24.576 MHz | **Yes, before DSP reset release** | The processor requires all supplies and `SYS_CLKIN0` stable at least 11 input-clock periods before `SYS_HWRST` deassertion [DSP pp.53-54]. This clock is upstream of all firmware and all arming logic. |
| ADC BCLK/LRCLK, 12.288 MHz/96 kHz | **Not required for PLL lock in selected MCLK mode; enabled before arm by project decision** | ADAU1978 PLL source is MCLKIN, not LRCLK. Pre-arm BCLK/LRCLK permits serial-port/framing checks while ADC data remains isolated by the data-bank OE. |
| TAS6424E-Q1 MCLK, 24.576 MHz | **Not required for I2C access or STANDBY; automatic after `RAILS_OK` by project decision** | The shared dual translator makes it available with ADC MCLK. Hardware STANDBY/MUTE keeps the output safe, and early MCLK removes it as a possible later arm prerequisite without adding another translator. |
| TAS6424E-Q1 SCLK/FSYNC, 12.288 MHz/96 kHz | **Not required for I2C access or STANDBY; enabled before arm by project decision** | The amplifier reports clock errors on `FAULT_N`, and clock error forces Hi-Z [AMPE pp.23-24, 33, 49]. Supplying all three clocks before arm prevents a missing-clock dependency. Because the datasheet does not explicitly guarantee clock-fault monitoring in STANDBY, active validation occurs after arm in Hi-Z and before MUTE/PLAY. |

The TDM data directions, analog rails, ADC analog inputs, amplifier MUTE/STANDBY releases, and PLAY remain unavailable before `HW_RUN_LATCHED`.

## 4. ADAU1978 PLL startup sequence

The deterministic fail-safe sequence is:

1. `PGOOD_12V`, `OUT1`, and `DOWNSTREAM_EN` establish `3V3_SYS` and `3V3_ADC_A`. `ADC_PD_RST_N` remains LOW through its hardware reset path. The ADC cannot arm the system and does not control either rail.
2. The 24.576 MHz ASDLJ/LMK root clock is already stable before DSP reset release. DSP reset release and boot do not depend on the endpoint clocks, although the hardware sequence below makes endpoint MCLK available before reset release as well.
3. LTC2964 `RAILS_OK` has already enabled the ADC/amplifier MCLK translator before DSP reset release. Firmware confirms MCLK, configures the internal SPORT clock generators while external clock/data buffer outputs remain disabled, then asserts `CLOCK_STARTUP_CMD`. `CLOCK_STARTUP_EN` enables only the SN74LVC244A BCLK/FSYNC bank.
4. Confirm MCLK/BCLK/FSYNC at their endpoint test points. Only after ADC MCLK is stable may firmware release `ADC_PD_RST_N`. ADC reset release is independent of `HW_RUN_LATCHED`.
5. PD/RST HIGH enables ADAU1978 DVDD. The internal POR does not release until DVDD reaches 1.2 V. Before I2C, observe the datasheet `tC = ROUT x CEXT` recommendation; `ROUT=20 ohm` is typical and is not treated as a guaranteed maximum [ADC p.12]. A missing I2C response or missing DVDD/PLL readiness is a safe startup failure: keep `RUN_HEALTH_OK_CMD=0`, keep the latch cleared, and do not enable analog/data/amplifier release.
6. Keep M_POWER.PWUP=`0` while writing the intended clock and serial-port configuration. Program PLL_CONTROL for MCLK source (`CLK_S=0`), MCS=`011`, and retain `PLL_MUTE=1`; program 96 kHz, TDM4, 32-bit slots, and the frozen edge/data format. The manufacturer strongly recommends disabling the PLL, reprogramming it, and re-enabling it when changing its setting [ADC pp.13-14, 27-31].
7. Do not assert PWUP until at least 10 ms after both DVDD > 1.2 V and the input clock is stable. Then assert PWUP and poll PLL_CONTROL.PLL_LOCK. The published MCLK-mode maximum lock time is 10 ms once stable clock is supplied [ADC pp.5, 12-14, 28-29]. If lock is absent at the allowed deadline, do not arm.
8. Read back the intended ADC configuration and `PLL_LOCK=1`. ADAU1978 channel conversion/data release may remain disabled until the analog rails and inputs are ready; PLL verification does not require microphone/AFE power.
9. Configure/read back the amplifier over I2C while STANDBY remains LOW, confirm `AMP_FAULT_N` is not presently asserted, assert `RUN_HEALTH_OK_CMD=1`, and generate a new `SAFE_ARM_CMD` rising edge. Do not claim that STANDBY-mode fault status proves active audio-clock monitoring; TI does not state that monitoring boundary explicitly.
10. After arming, enable the SN74LVC244A data bank and release amplifier STANDBY only into the programmed Hi-Z channel state. Verify the active clock ratios/status and confirm no `FAULT_N`; any fault immediately clears the latch and reasserts STANDBY. Only after that check may firmware enable microphone/AFE power, wait for settling, enable required ADC channel operation, prove valid DMA frames, and release MUTE/PLAY in the frozen sequence.

For a hardware-reset reinitialization while the rails remain on, the ADAU1978 datasheet requires PD/RST LOW long enough for DVDD to fall below the reset threshold; the 15 ns table entry alone does not bound that discharge. Retain CEXT=10 uF nominal X7R and fit `REXT=3.00 kohm`, 1%, across DVDD as shown by the manufacturer. Select CEXT so its effective maximum is no more than 12 uF. With the published `RINT=64 kohm +/-20%`, the bounded discharge estimate is:

```text
REQ(max) = 76.8 kohm || 3.03 kohm = 2.915 kohm
tD(max)  = 1.32 x 2.915 kohm x 12 uF = 46.2 ms
```

Require `ADC_PD_RST_N` LOW for at least **50 ms** for an in-place hardware reset. The existing 170-230 ms watchdog reset interval exceeds this. The CEXT effective range and the resulting DVDD/reset waveform remain mandatory schematic/BOM and bench checks; the calculation does not convert the datasheet's typical 20-ohm charge resistance into a guarantee.

At the ADAU1978 DVDD maximum of 1.98 V and `REXT` minimum of 2.97 kohm, the added resistor draws at most 0.667 mA and dissipates at most 1.32 mW. Include that current in the existing 30 mA `3V3_ADC_A` allocation during the populated-BOM audit; the frozen allocation and regulator selection do not change.

## 5. Corrected `HW_RUN_LATCHED` contract

`HW_RUN_LATCHED` is a non-auto-rearming **functional audio authorization**. It is not a rail enable, bootstrap-clock enable, ADC reset release, clock detector, or proof that every runtime variable remains valid forever.

### 5.1 What a HIGH state proves

A HIGH state proves that:

- a deliberate `SAFE_ARM_CMD` rising edge occurred while `PGOOD_CLEAN`, `SYS_HWRST_CLEAN`, `EFUSE_FLT_CLEAN_N`, `AMP_FAULT_CLEAN_N`, and `RUN_HEALTH_OK_3V8` were all HIGH; and
- none of those asynchronous clear conditions has subsequently gone LOW.

`RUN_HEALTH_OK_CMD` is a continuous firmware-owned permit, default LOW. Firmware may assert it only after current ADC PLL lock/configuration, amplifier I2C configuration/readback, and absence of an asserted amplifier fault. The active amplifier clock check is a later pre-PLAY test in Hi-Z because the manufacturer does not explicitly guarantee clock monitoring in STANDBY. Firmware must deassert run health on ADC PLL loss, framing failure, clock-validation failure, or any condition requiring requalification. A new health HIGH level never sets the latch; a new `SAFE_ARM_CMD` edge is still mandatory.

### 5.2 Exact state behavior

| Condition | Required latch behavior |
| --- | --- |
| Startup default | LOW. `RUN_HEALTH_OK_CMD` and `SAFE_ARM_CMD` have passive LOW defaults; low `SYS_HWRST` also holds asynchronous clear active. |
| SET | Rising edge on `SAFE_ARM_3V8 = SAFE_ARM_CMD_3V8 AND SYS_HWRST_CLEAN`, only while final `SAFE_CLEAR_N` is HIGH. D remains tied to `3V8_PRE`. |
| RESET | Asynchronous clear when any of `PGOOD_CLEAN`, `SYS_HWRST_CLEAN`, `EFUSE_FLT_CLEAN_N`, `AMP_FAULT_CLEAN_N`, or `RUN_HEALTH_OK_3V8` is LOW. |
| Brownout / input loss | Low PGOOD clears immediately; no automatic rearm after recovery. |
| Watchdog, DSP reset, JTAG reset/halt | Low `SYS_HWRST` clears immediately. DSP GPIO pulldowns also return health/commands LOW. |
| Common/root clock failure | TAS6424E-Q1 clock error asserts sticky `FAULT_N` and clears the latch when its clock monitor is active; loss of the DSP branch also prevents watchdog service and produces `SYS_HWRST`. No STANDBY-monitoring behavior is assumed. |
| ADC-only MCLK or PLL loss | ADAU1978 `PLL_MUTE=1` automatically mutes ADC data. Firmware drops `RUN_HEALTH_OK_CMD`, data OE and amplifier releases, asserts ADC reset as required, and must not service the external watchdog as healthy until requalification. Recovery requires a new arm edge. ADAU1978 exposes PLL lock only as a register bit, not a hardware pin; no immediate hardware-latch-clear claim is made for an ADC-only branch fault. |
| Amplifier clock or device fault | `FAULT_N` is sticky and asynchronously clears the latch. Clear the amplifier fault only while all releases remain safe; complete checks and issue a new arm edge. |
| Normal shutdown | Firmware first makes the amplifier/analog/data path safe, then drops `RUN_HEALTH_OK_CMD`; the latch clears before endpoint clocks or downstream rails are removed. |
| System fault | Existing PGOOD, eFuse, rail-reset, watchdog, and amplifier-fault paths dominate firmware and clear authorization. |

This separation avoids overloading the latch: it authorizes only analog power, serial data, and amplifier functional release. It does not control the rail tree or either clock needed to establish its SET conditions.

## 6. Safe-state verification

Before `HW_RUN_LATCHED=1`:

- TAS6424E-Q1 STANDBY and MUTE remain LOW through passive pulldowns and the existing `HW_RUN_LATCHED AND command` gates. Its output FETs remain Hi-Z in STANDBY.
- All four amplifier channel-state registers remain Hi-Z while the device is configured and clock faults are cleared/read back.
- The SN74LVC244A data bank stays disabled; only its BCLK/FSYNC bank may be enabled by `CLOCK_STARTUP_EN`.
- `2V8_MIC`, `5V_AFE`, and all paired TMUX2821 paths remain off/open because `ANALOG_PWR_EN` still includes `HW_RUN_LATCHED`.
- ADAU1978 may receive clocks and leave reset for PLL/configuration validation, but its analog sources remain disconnected and its data cannot reach the DSP through the disabled data bank. `PLL_MUTE=1` remains mandatory.
- ADSP-21569 reset/boot remains governed only by the valid-rail, watchdog, and independent root-clock chain.

Therefore early clocks do not imply early audio operation, and no unsafe speaker output depends on firmware establishing the initial safe state.

## 7. Full clock-dependency audit

### 7.1 Resulting acyclic order

```text
12V_IN valid
  -> TPS26630 / 12V_PROTECTED
  -> 3V8_PRE
  -> PGOOD_12V / PGOOD_CLEAN
  -> 1V8_DSP_REF_ANA
     -> ASDLJ oscillator
     -> LMK fanout
     -> ADSP-21569 SYS_CLKIN0
     -> LTC2964 OUT1
  -> DOWNSTREAM_EN
  -> 1V0_DSP_CORE + 1V35_DSP_DMC + 3V3_SYS + 3V3_ADC_A
  -> LTC2964 RAILS_OK delay
     -> ADC/amp MCLK translator enabled
  -> TPS3431 reset delay
  -> SYS_HWRST releases
  -> ADSP-21569 ROM boot
  -> SPORT configured + CLOCK_STARTUP_CMD
  -> CLOCK_STARTUP_EN
  -> ADC/amp BCLK/FSYNC
  -> ADC reset release + DVDD/POR + PLL configuration/lock
  -> amplifier I2C configuration + no asserted fault
  -> RUN_HEALTH_OK_CMD + SAFE_ARM_CMD edge
  -> HW_RUN_LATCHED
  -> serial-data bank + amplifier Hi-Z release
  -> active amplifier clock/fault verification
  -> microphone/AFE power + settled ADC/DMA/audio validation
  -> amplifier MUTE/STANDBY release -> PLAY
```

### 7.2 Dependency checks

| Node | Requires | Must not require | Result |
| --- | --- | --- | --- |
| ASDLJ oscillator OE | Valid `1V8_DSP_REF_ANA` | DSP firmware, `HW_RUN_LATCHED` | PASS |
| LMK `1G` | Valid `1V8_DSP_REF_ANA` | downstream rails, firmware, latch | PASS |
| DSP `SYS_CLKIN0` | Oscillator + LMK + VDD_REF | DSP boot, latch | PASS |
| `DOWNSTREAM_EN` | `OUT1`, PGOOD, retained-run delay | `RAILS_OK`, DSP reset release, clocks, latch | PASS |
| `RAILS_OK` / supervisor reset | Four monitored rails | any enable controlled by `RAILS_OK` | PASS |
| ADC/amplifier MCLK translator | `RAILS_OK`, both translator supplies, root/fanout clock | DSP firmware, ADC lock, amplifier fault-clear, latch | PASS |
| `CLOCK_STARTUP_EN` / BCLK/FSYNC bank | DSP already out of reset + explicit command | ADC lock, amplifier fault-clear, latch | PASS |
| ADC PLL lock | ADC rails, reset release, stable MCLK, correct configuration/time | latch, microphone/AFE power, BCLK/FSYNC in MCLK mode | PASS |
| SPORT BCLK/FSYNC | DSP root/boot/SPORT config + clock bootstrap enable | ADC lock, latch | PASS |
| Amplifier pre-arm access | VDD/PVDD/VBAT, I2C time, clocks already supplied, STANDBY asserted | latch, MUTE/PLAY | PASS |
| `HW_RUN_LATCHED` SET | hardware clears valid + ADC PLL/configuration health + amplifier configuration/no asserted fault + explicit edge | any rail enable, DSP primary clock, bootstrap clock | PASS |
| Active amplifier clock validation | latch permits STANDBY release only into programmed Hi-Z; clocks are already present | MUTE/PLAY, analog power | PASS; it is a PLAY prerequisite, not an arm prerequisite |
| Serial data/analog/PLAY | latch plus separate commands, active amplifier check, and settling checks | creation of latch prerequisites | PASS |

No `A requires B` path returns to `B requires A`. The additional amplifier path is explicitly broken: all amplifier clocks and I2C access exist without the latch; after arming, STANDBY may release only into Hi-Z for the active clock check, and any resulting `FAULT_N` clears the latch before MUTE/PLAY.

## 8. Shutdown and failure behavior

| Event | Endpoint-clock behavior | Safe-state order |
| --- | --- | --- |
| Normal shutdown | MCLK/BCLK/FSYNC remain active temporarily. After MUTE, channel Hi-Z, STANDBY LOW for at least 15 ms, analog off, data OE off, and ADC reset asserted, clear run health and deassert `CLOCK_STARTUP_CMD`; BCLK/FSYNC stop. MCLK remains until the later downstream-rail removal makes `RAILS_OK` fall. | Then pulse `SHUTDOWN_REQ`; retained reset and 20.415-40.946 ms downstream hold remain unchanged. All endpoint clocks stop only after dependents are safe. |
| Brownout / abrupt loss | Low PGOOD clears the latch and asserts `SYS_HWRST`; `CLOCK_STARTUP_EN` falls, disabling BCLK/FSYNC. Rail invalidity makes `RAILS_OK` fall and disables the MCLK translator; the translator also isolates as either supply collapses. Root clock stops only with 1.8 V. | Amplifier MUTE/STANDBY and ADC/DSP reset assert before reliance on clock removal. No graceful hold is claimed. |
| Watchdog timeout / DSP reset | `SYS_HWRST_CLEAN=0` forces `CLOCK_STARTUP_EN=0`; BCLK/FSYNC and data stop. `RAILS_OK` remains high on healthy rails, so ADC/amplifier MCLK and the DSP root oscillator/fanout remain active for deterministic restart. | Latch clears, ADC reset asserts, amplifier returns safe, analog power turns off. Reboot must re-enable SPORT clocks, repeat PLL/endpoint checks, and rearm. |
| ADC PLL loss with clocks present | Keep bootstrap clocks available for diagnosis/relock. ADAU1978 hardware automute remains enabled. | Drop run health, data OE and amplifier releases; reset/reconfigure ADC. New arm edge required. |
| Common MCLK or amplifier-MCLK loss | ADC PLL unlock/automute when its branch is affected; TAS6424E-Q1 detects an affected amplifier clock, forces Hi-Z, and asserts sticky `FAULT_N`. Common-root loss also stops DSP execution and is caught by the watchdog. An ADC-only MCLK loss follows the separate ADC-PLL-loss row. | Latch clears through amplifier fault and/or reset where those hardware paths are affected; ADC-only loss uses run-health withdrawal and the watchdog policy. Do not automatically return to PLAY when clocks recover. |
| DSP root-clock branch loss only | Endpoint clocks can remain briefly, but the DSP stops and cannot service TPS3431. | Watchdog asserts `SYS_HWRST`, clears the latch, and removes BCLK/FSYNC/data. MCLK remains only while `RAILS_OK` stays valid and is harmless with ADC reset and amplifier STANDBY/MUTE asserted. |
| Amplifier/system fault | Clock bootstrap may remain active when rails and DSP reset remain valid, permitting safe I2C diagnosis. | `AMP_FAULT_N` or other hardware clear removes latch authorization; MUTE/STANDBY/data/analog releases fall. |

The controlling rule is safety first, then clock removal. No device supply is removed merely to save clock power before its required reset/standby state is established.

## 9. Exact Phase 4B implementation instructions

Phase 4B remains blocked and may resume only under separate authorization. When it is authorized, Astra shall implement this contract without selecting another startup architecture:

1. Retain ASDLJ and LMK connections from Phase 3. ASDLJ OE is pulled active to `1V8_DSP_REF_ANA`; LMK `1G` has its 10-kohm pullup to that rail. LMK Y0 drives `SYS_CLKIN0`; Y1 and Y2 separately drive SN74AXC2T245 A1/A2.
2. Retain one exact `SN74AXC2T245RSWR`: pin 7 VCCA=`1V8_DSP_REF_ANA`, pin 6 VCCB=`3V3_SYS`, pin 3 ground, DIR1 pin 10 and DIR2 pin 1 to VCCA, A1 pin 8/B1 pin 5=ADC MCLK source/output, and A2 pin 9/B2 pin 4=amplifier MCLK source/output. Pull `/OE` pin 2 up to VCCA with 10 kohm. Fit one exact `BSS138LT1G` (pin 1 gate, pin 2 source, pin 3 drain) with drain at `/OE`, source at ground, gate=`RAILS_OK`, and 100-kohm gate-to-ground pulldown. `RAILS_OK` is the exact automatic MCLK enable source. Do not connect `/OE` to `CLOCK_STARTUP_EN`, any DSP GPIO, or `HW_RUN_LATCHED`.
3. Partition the exact `SN74LVC244APWR` at `3V3_SYS` (pin 20 VCC, pin 10 ground). Bank 1: pin 2/18 DSP BCLK -> ADC BCLK; pin 4/16 DSP BCLK -> amplifier SCLK; pin 6/14 DSP FSYNC -> ADC LRCLK; pin 8/12 DSP FSYNC -> amplifier FSYNC; pin 1 is `/1OE`. Bank 2: pin 11/9 ADC SDATAOUT1 -> DSP SPORT RX; pin 13/7 DSP SPORT TX -> amplifier SDIN1; tie unused inputs pins 15 and 17 to ground and leave outputs pins 5 and 3 unconnected; pin 19 is `/2OE`.
4. Pull each SN74LVC244A active-low OE pin up to `3V3_SYS` with 10 kohm. Each OE gets its own exact `BSS138LT1G` sink (drain=OE, source=ground, 100-kohm gate pulldown). Drive the clock-bank sink gate from `CLOCK_STARTUP_EN`. Drive the data-bank sink gate from `AUDIO_DATA_OE_RELEASE`. Preserve the 22-33-ohm source resistors and one-output-per-clock-route contract.
5. Populate a second exact `SN74LVC2G08DCUR`, named `U_BOOT_GATES`, with pin 8=`3V8_PRE`, pin 4=ground, and 0.1 uF bypass. Channel 1 uses pins 1/2 -> 7 for `SYS_HWRST_CLEAN AND CLOCK_STARTUP_CMD_3V8 -> CLOCK_STARTUP_EN`. Channel 2 uses pins 5/6 -> 3 for `SAFE_HW_CLEAR_N AND RUN_HEALTH_OK_3V8 -> SAFE_CLEAR_N`.
6. Rename the former four-input Phase 3E safe-clear output to `SAFE_HW_CLEAR_N`:

   ```text
   SAFE_HW_CLEAR_N = PGOOD_CLEAN AND SYS_HWRST_CLEAN
                   AND EFUSE_FLT_CLEAN_N AND AMP_FAULT_CLEAN_N
   SAFE_CLEAR_N = SAFE_HW_CLEAR_N AND RUN_HEALTH_OK_3V8
   ```

   Connect final `SAFE_CLEAR_N` to `U_SAFE_LATCH /CLR`. Keep `/PRE=3V8_PRE`, D=`3V8_PRE`, CLK=`SAFE_ARM_3V8`, and Q=`HW_RUN_LATCHED`.
7. Use all eight channels of the existing exact `SN74LXC8T245PWR`: pin 1 VCCA=`3V3_SYS`; pins 23/24 VCCB=`3V8_PRE`; pin 2 DIR=VCCA; pin 22 `/OE`=ground; pins 11/12/13=ground. Assign A/B pairs exactly: A1 pin 3/B1 pin 21=`SHUTDOWN_REQ`; A2 pin 4/B2 pin 20=`SAFE_ARM_CMD`; A3 pin 5/B3 pin 19=`ANALOG_PWR_CMD`; A4 pin 6/B4 pin 18=`CLOCK_STARTUP_CMD`; A5 pin 7/B5 pin 17=`AUDIO_DATA_OE_CMD`; A6 pin 8/B6 pin 16=`RUN_HEALTH_OK_CMD`; A7 pin 9/B7 pin 15=`SYS_HWRST`; A8 pin 10/B8 pin 14=`AMP_FAULT_N`, each A-to-B. Apply the existing 100-kohm safe pulldown policy to every command input and every B-side output; retain the 10-kohm pullups plus 100-kohm pulldowns on the raw reset/fault A inputs. No channel remains unused.
8. The former `HW_RUN_LATCHED AND AUDIO_OE_CMD` gate is retained only as `AUDIO_DATA_OE_RELEASE = HW_RUN_LATCHED AND AUDIO_DATA_OE_CMD_3V8`. It must not control MCLK, BCLK, or FSYNC.
9. Implement `ADC_PD_RST_N` independently of `HW_RUN_LATCHED`. Use an additional exact `SN74LVC2G07DBVR` at `3V3_SYS`: pin 5 VCC, pin 2 ground, 0.1 uF bypass; pin 1 input=`SYS_HWRST` with open-drain pin 6 output; pin 3 input=`ADC_RST_RELEASE_CMD` with open-drain pin 4 output. Wire pins 6 and 4 together at `ADC_PD_RST_N`, with a 10-kohm pullup to `3V3_SYS`. Add a 100-kohm pulldown on `ADC_RST_RELEASE_CMD`. LOW on either input asserts ADC reset; both must be HIGH to release it. Fit the ADAU1978 DVDD `REXT=3.00 kohm`, 1%, and the bounded CEXT contract from section 4.
10. Preserve `AMP_MUTE_RELEASE = HW_RUN_LATCHED AND AMP_MUTE_CMD`, `AMP_STBY_RELEASE = HW_RUN_LATCHED AND AMP_STBY_CMD`, and `ANALOG_PWR_EN = DOWNSTREAM_EN AND HW_RUN_LATCHED AND ANALOG_PWR_CMD_3V8`. Neither clock signal may bypass these functional safety gates.
11. Use hierarchical names `CLOCK_STARTUP_CMD`, `CLOCK_STARTUP_CMD_3V8`, `CLOCK_STARTUP_EN`, `AUDIO_DATA_OE_CMD`, `AUDIO_DATA_OE_CMD_3V8`, `AUDIO_DATA_OE_RELEASE`, `RUN_HEALTH_OK_CMD`, `RUN_HEALTH_OK_3V8`, `SAFE_HW_CLEAR_N`, `SAFE_CLEAR_N`, and `ADC_PD_RST_N`. Retain `RAILS_OK` as the MCLK-enable source, plus `HW_RUN_LATCHED`, `SYS_HWRST`, `SYS_HWRST_CLEAN`, `AMP_FAULT_N`, `AMP_FAULT_CLEAN_N`, `PGOOD_CLEAN`, `DOWNSTREAM_EN`, and all existing clock net names. Do not invent a firmware MCLK-enable signal.
12. Expose test points for ADC and amplifier MCLK, both buffered BCLK/FSYNC destinations, both SN74LVC244A OE pins, SN74AXC2T245 `/OE`, `CLOCK_STARTUP_EN`, `RUN_HEALTH_OK_3V8`, final `SAFE_CLEAR_N`, `HW_RUN_LATCHED`, `ADC_PD_RST_N`, and ADAU1978 DVDD. Verify the sequence and the absence of any latch-to-prerequisite path before claiming Phase 4B completion.

## 10. Acceptance disposition

Remaining implementation/physical uncertainties are not hidden: the ADAU1978 charge-path `ROUT` is published only as typical, so failure to obtain I2C/DVDD/PLL readiness must time out safe rather than arm; CEXT effective capacitance and the 50 ms reset discharge must be verified; clock-OE edge quality and endpoint timing remain bench/PVT items; and ADC-only PLL lock is a register status with no hardware output pin, so its immediate response is the mandatory ADC hardware automute followed by run-health withdrawal/watchdog policy. None of these creates a startup prerequisite cycle or permits pre-arm speaker operation.

- ADAU1978 MCLK and the complete endpoint clock-validation set can be enabled before `HW_RUN_LATCHED`: **PASS**.
- ADSP-21569 can reach deterministic reset release and boot, and endpoint MCLK is available, without firmware or latch assistance: **PASS**.
- ADC PLL verification and amplifier configuration/no-present-fault checks can precede the deliberate arm edge; active amplifier clock verification occurs safely in Hi-Z before MUTE/PLAY: **PASS**.
- No clock, reset, regulator PGOOD, supervisor, watchdog, or amplifier-fault prerequisite is gated by the latch it helps establish: **PASS**.
- Phase 3E hardware mute/standby, analog-off, powered-off isolation, retained shutdown, and non-auto-rearm behavior are preserved: **PASS**.
- Shutdown, brownout, watchdog, ADC PLL loss, MCLK loss, DSP reset, and system-fault behavior are explicitly ordered: **PASS**.
- Exact signals, equations, gates, translator channels, buffer-bank allocation, OE sinks, reset implementation, and test nodes are fixed for a later authorized Phase 4B continuation: **PASS**.

PHASE 3F: PASS
