"""Reproducible conditional R4 calculations, not an R5 readiness certificate.

Source limits: NXP IMXRT1060CEC Rev 4 Tables 22 and 50 (pp.37, 61);
NXP IMXRT1060RM Rev 4 pp.1028, 1052, 1056-1058, 1104-1106,
1977-1978, 2000, 2016; NXP HW Guide Rev 7 pp.3-7, 9-15;
TI SN74LVC1G125 SCES223U Tables 5.3, 5.5, 5.8 (pp.5-7);
TI TAS5825M SLASEH7H Tables 7.3, 7.5 and 7.6 (pp.6-10);
TI TLV320ADC5140 SBAS892A pp.12, 21-22, 26;
TI TPS7A20 SBVS338H (fixed output accuracy at its specified conditions).
"""

from math import pi


def main() -> None:
    fs = 96_000
    adc_bclk = fs * 4 * 32
    amp_bclk = fs * 2 * 32
    assert (adc_bclk, amp_bclk) == (12_288_000, 6_144_000)

    # RT1062 current reference manual Rev 4: fractional PLL4 and the two SAI
    # roots share the 24-MHz reference. Separate SAI blocks do not support
    # hardware-synchronous mode, so this proves frequency, not frame phase.
    pll4_vco = 24_000_000 * (32 + 96 / 125)
    pll4_post = pll4_vco / 4
    sai_root = pll4_post / 2 / 4
    assert (pll4_vco, pll4_post, sai_root) == (786_432_000, 196_608_000, 24_576_000)
    assert sai_root / (2 * (0 + 1)) == adc_bclk
    assert sai_root / (2 * (1 + 1)) == amp_bclk

    # These DC figures are conditional on both 3.3-V domains meeting 3.0-3.6 V,
    # NXP source IOH/IOL <= 1 mA and buffer output IOH/IOL <= 100 uA.
    nxp_voh_min, nxp_vol_max = 3.0 - 0.15, 0.15
    lvc_vih_min, lvc_vil_max = 2.0, 0.8
    buf_input_high = nxp_voh_min - lvc_vih_min
    buf_input_low = lvc_vil_max - nxp_vol_max
    buf_voh_min, buf_vol_max = 3.0 - 0.1, 0.1
    # Buffer and TAS must share the SAME local B 3V3 rail. Independent
    # supplies at 3.0 V and 1.62 V would violate TAS DVDD+0.5-V abs max.
    tas_vih_worst, tas_vil_worst = 0.7 * 3.0, 0.3 * 3.0
    amp_high = buf_voh_min - tas_vih_worst
    amp_low = tas_vil_worst - buf_vol_max
    assert min(buf_input_high, buf_input_low, amp_high, amp_low) > 0

    # Conditional timing: use shortest 40%-duty half cycle, NXP maximum
    # clock-to-data-valid 15 ns, TI 125 C / 50 pF maximum buffer delay 4.7 ns,
    # TI minimum buffer delay 1 ns, TAS setup/hold 8 ns, and a *proposed*
    # 5-ns total clock/data interconnect skew. Board length/load is not frozen.
    period_ns = 1e9 / amp_bclk
    shortest_phase_ns = 0.4 * period_ns
    setup_margin_ns = shortest_phase_ns - 15 - (4.7 - 1) - 5 - 8
    hold_margin_ns = shortest_phase_ns - (4.7 - 1) - 5 - 8
    assert setup_margin_ns > 0 and hold_margin_ns > 0

    # ADC-side half-cycle from ADC SDOUT launch to RT1062 SAI1 RX sample:
    # TI SDOUT delay <=18 ns at 25 C / 20-pF load; NXP RX setup >=15 ns.
    # The 5-ns skew is a proposed board-level bound, not verified hardware.
    adc_period_ns = 1e9 / adc_bclk
    adc_setup_before_skew_ns = adc_period_ns / 2 - 18 - 15
    adc_setup_at_5ns_skew_ns = adc_setup_before_skew_ns - 5

    # Explicit R4 mitigation candidate, NOT a change to the R3 baseline:
    # ADC 24-bit words in four 24-bit TDM slots are supported by E-ADC
    # pp.20-22. A new PLL4 profile can preserve the 96-kHz amp rate.
    alt_pll4_vco = 24_000_000 * (36 + 108 / 125)
    alt_pll4_post = alt_pll4_vco / 4
    alt_sai1_root = alt_pll4_post / 3 / 4
    alt_sai2_root = alt_pll4_post / 3 / 3
    alt_adc_bclk = alt_sai1_root / 2
    assert (round(alt_pll4_vco), round(alt_pll4_post)) == (884_736_000, 221_184_000)
    assert tuple(round(x) for x in (alt_sai1_root, alt_sai2_root, alt_adc_bclk)) == (18_432_000, 24_576_000, 9_216_000)
    assert round(alt_sai2_root / 4) == amp_bclk
    alt_adc_setup_at_5ns_skew_ns = 1e9 / alt_adc_bclk / 2 - 18 - 15 - 5

    # These RC values are illustrative only. The ADC 20-kohm setting is
    # typical, not a guaranteed lower input resistance; capacitor derating
    # has not been fixed. They cannot approve the microphone network.
    fc_1uf_typ_hz = 1 / (2 * pi * 20_000 * 1e-6)
    fc_10uf_typ_hz = 1 / (2 * pi * 20_000 * 10e-6)

    # Fixed 2.8-V TPS7A20 accuracy is guaranteed only within TI's stated
    # VIN (at least VOUT_NOM + 0.3 V = 3.1 V for this fixed 2.8-V part),
    # load, junction-temperature, and output-capacitance conditions.
    # A generic 3.0-V-min 3V3 rail alone does not meet the guaranteed VIN.
    mic_rail_min, mic_rail_max = 2.8 * 0.985, 2.8 * 1.015
    assert 2.3 <= mic_rail_min and mic_rail_max <= 3.0

    # Owner permits an engineering sizing screen, not a final adapter rating.
    # Assumed 3.2-ohm minimum load, 70% amp efficiency, 10-W Board A,
    # 85% buck efficiency and 25% allowance must be independently verified.
    def input_current_screen(v: float) -> float:
        return 1.25 * (v / (3.2 * 0.70) + 10 / (0.85 * v))

    input_12v_a = input_current_screen(12)
    input_18v_a = input_current_screen(18)
    assert 7.9 < input_12v_a < 8.0
    assert 10.8 < input_18v_a < 11.0

    # E-WATCHDOG TPS3431 minimum recommended-capacitor typical timeout is
    # 62.74 ms. Even E-WATCHDOG-FAST-SCREEN W option can take 9.3 ms,
    # leaving <=0.7 ms for all remaining fault-to-silence paths at 10 ms.
    fast_wdt_remaining_ms = 10 - 9.3
    assert fast_wdt_remaining_ms < 1

    for key, value in {
        "adc_bclk_hz": adc_bclk,
        "amp_bclk_hz": amp_bclk,
        "pll4_vco_hz": int(pll4_vco),
        "pll4_post_hz": int(pll4_post),
        "sai1_sai2_root_hz": int(sai_root),
        "adc_setup_before_skew_ns_25c_only": round(adc_setup_before_skew_ns, 3),
        "adc_setup_at_5ns_skew_ns_25c_only": round(adc_setup_at_5ns_skew_ns, 3),
        "candidate_24bit_adc_bclk_hz_not_frozen": round(alt_adc_bclk),
        "candidate_24bit_setup_at_5ns_skew_ns_25c_only": round(alt_adc_setup_at_5ns_skew_ns, 3),
        "amp_bclk_period_ns": round(period_ns, 3),
        "amp_shortest_phase_ns": round(shortest_phase_ns, 3),
        "buffer_input_high_margin_v": round(buf_input_high, 3),
        "buffer_input_low_margin_v": round(buf_input_low, 3),
        "amp_high_margin_v": round(amp_high, 3),
        "amp_low_margin_v": round(amp_low, 3),
        "conditional_amp_setup_margin_ns": round(setup_margin_ns, 3),
        "conditional_amp_hold_margin_ns": round(hold_margin_ns, 3),
        "typical_only_20k_1uf_fc_hz": round(fc_1uf_typ_hz, 3),
        "typical_only_20k_10uf_fc_hz": round(fc_10uf_typ_hz, 3),
        "conditional_mic_2v8_min_v": round(mic_rail_min, 3),
        "conditional_mic_2v8_max_v": round(mic_rail_max, 3),
        "assumption_only_input_current_screen_12v_a": round(input_12v_a, 3),
        "assumption_only_input_current_screen_18v_a": round(input_18v_a, 3),
        "fast_watchdog_remaining_response_ms": round(fast_wdt_remaining_ms, 3),
    }.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
