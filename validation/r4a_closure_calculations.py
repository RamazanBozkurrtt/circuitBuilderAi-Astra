"""Focused Board A R4-A corner calculations. Assumptions are named, not certified."""

from math import atan, degrees, pi


def calculate_load_power() -> dict:
    """Board A sizing envelope; design allocations are not device current maxima."""
    # NXP IMXRT1060CEC Rev 4 Table 12, p.28. The I/O banks are excluded.
    mcu_pins_ma = {"DCDC_IN": 110, "VDD_HIGH_IN": 50,
                   "VDDA_ADC_3P3": 40, "VDD_SNVS_IN": 0.25}
    # Infineon v1.20 Table 7 p.10: 230 uA only for input <=94 dBSPL.
    # TI SBOS513F p.9: OPA2320 1.7 mA/channel, no output load, -40..125 C.
    # LDO tolerance specifies IOUT >=1 mA. 2.2k/1.5k/2.7k, 1% bleeders
    # on MIC/FLASH/ADC guarantee the minimum load even with ICs asleep.
    mic_ma = 4 * 1.0 + 1.31 + 1.69
    opa_iq_ma = 8 * 1.7
    adc_afe_ma = 50 + opa_iq_ma + 4 + 2 + 5.4
    flash_ma = 30 + 15 + 15  # ISSI core max + SD1 I/O and transient allocations
    assert adc_afe_ma == 75 and flash_ma == 60
    # NVCC_GPIO/EMC switched load, ADC IOVDD, straps, supervisor, downstream
    # LDO input and buck output transient. No unstated USB bus-power load.
    ldo_gnd_ma = 2  # engineering bound per LDO; TI 2 mA is typical at 300 mA
    mcu_buck_ma = (sum(mcu_pins_ma.values()) + 20 + 5 + 5 + 1
                   + mic_ma + flash_ma + 2 * ldo_gnd_ma + 20)
    buck_ceiling_ma = 350  # below output capability and above itemized allocation
    assert mcu_buck_ma <= buck_ceiling_ma
    buck_vmax = 3.4259
    adc_vmin = 3.2505
    ldo_theta = 166.1
    buck_theta = 38.4
    ambient = 85
    eta_floor = .70  # imposed design acceptance floor, not TI guarantee
    buck_pout_w = buck_vmax * buck_ceiling_ma / 1000
    buck_loss_w = buck_pout_w * (1 / eta_floor - 1)
    input_ma = buck_pout_w / (eta_floor * 4.5) * 1000 + adc_afe_ma + ldo_gnd_ma + 25 + 10
    adc_loss_w = (5.5 - adc_vmin) * adc_afe_ma / 1000 + 5.5 * ldo_gnd_ma / 1000
    mic_loss_w = (3.4259 - 2.758) * mic_ma / 1000 + 3.4259 * ldo_gnd_ma / 1000
    flash_loss_w = (3.4259 - 1.770) * flash_ma / 1000 + 3.4259 * ldo_gnd_ma / 1000
    mcu_pkg_w = buck_vmax * (110 + 50 + 40 + .25 + 20) / 1000
    adc_pkg_w = 3.3495 * (50 + 5) / 1000
    opa_pkg_w = 3.3495 * (2 * 1.7 + 1) / 1000
    return {
        "mcu_pin_max_ma": mcu_pins_ma,
        "mcu_io_and_misc_design_ma": {"gpio_emc_switching": 20, "adc_iovdd": 5,
            "boot_pulls_and_debug": 5, "supervisor": 1,
            "mic_ldo_output": mic_ma, "flash_ldo_output": flash_ma,
            "two_ldo_ground_current": 2 * ldo_gnd_ma,
            "output_transient": 20},
        "mcu_buck_itemized_ma": mcu_buck_ma,
        "mcu_buck_design_ceiling_ma": buck_ceiling_ma,
        "mcu_buck_unallocated_ma": round(buck_ceiling_ma - mcu_buck_ma, 2),
        "mic_design_ceiling_ma": mic_ma,
        "opa_eight_channel_iq_max_ma": opa_iq_ma,
        "adc_afe_design_ceiling_ma": adc_afe_ma,
        "flash_design_ceiling_ma": flash_ma,
        "adc_afe_tj_c_at_85c": round(ambient + adc_loss_w * ldo_theta, 2),
        "adc_afe_tj_margin_to_125c": round(125 - ambient - adc_loss_w * ldo_theta, 2),
        "mic_ldo_tj_c_at_85c": round(ambient + mic_loss_w * ldo_theta, 2),
        "flash_ldo_tj_c_at_85c": round(ambient + flash_loss_w * ldo_theta, 2),
        "mcu_pkg_tj_c_at_85c_reference_39p1cw": round(ambient + mcu_pkg_w * 39.1, 2),
        "adc_pkg_tj_c_at_85c_reference_32p6cw": round(ambient + adc_pkg_w * 32.6, 2),
        "opa_pkg_tj_c_at_85c_reference_174p8cw": round(ambient + opa_pkg_w * 174.8, 2),
        "gpio_25pins_30pf_12p288mhz_ma": round(25 * 30e-12 * buck_vmax * .5 * 12.288e6 * 1000, 2),
        "sd1_6pins_30pf_30mhz_ma": round(6 * 30e-12 * 1.83 * .5 * 30e6 * 1000, 2),
        "buck_output_w": round(buck_pout_w, 4),
        "buck_loss_w_at_assumed_70pct_eta": round(buck_loss_w, 4),
        "buck_tj_c_at_85c_assumed_eta": round(ambient + buck_loss_w * buck_theta, 2),
        "buck_tj_margin_to_125c_assumed_eta": round(125 - ambient - buck_loss_w * buck_theta, 2),
        "input_design_ma_at_4p5v": round(input_ma, 2),
        "input_margin_to_750ma_ma": round(750 - input_ma, 2),
        "input_startup_and_step_extra_design_ma": 200,
        "input_design_with_startup_ma": round(input_ma + 200, 2),
        "input_margin_with_startup_to_750ma_ma": round(750 - input_ma - 200, 2),
        "mic_bleeder_min_ma": round(2.758 / (2200 * 1.01) * 1000, 3),
        "flash_bleeder_min_ma": round(1.770 / (1500 * 1.01) * 1000, 3),
        "adc_bleeder_min_ma": round(3.2505 / (2700 * 1.01) * 1000, 3),
        "adc_ldo_dissipation_w": round(adc_loss_w, 4),
        "mic_ldo_dissipation_w": round(mic_loss_w, 4),
        "flash_ldo_dissipation_w": round(flash_loss_w, 4),
        "efficiency_floor_is_manufacturer_guaranteed": False,
        "thermal_resistance_is_product_board_guaranteed": False,
    }


def calculate() -> dict[str, float]:
    # TPS62135 SLVSBH3B pp.5-6: PWM VFB +/-1% only if VIN >= VOUT+1 V.
    # 1% divider and 70-nA maximum FB leakage, taken with adverse polarity.
    top, bottom = 255_000.0, 68_100.0
    buck_min = 0.693 * (1 + top * .99 / (bottom * 1.01)) - 70e-9 * top * 1.01
    buck_max = 0.707 * (1 + top * 1.01 / (bottom * .99)) + 70e-9 * top * 1.01
    assert 3.0 < buck_min < buck_max < 3.6

    # NXP HW7 pp.4-6: RC nominal 5-15 ms. Values are component tolerances,
    # not proof of the required >=1 ms delay from DCDC_IN reaching 3.0 V.
    rc_min_ms = 30_000 * .99 * 0.22e-6 * .90 * 1000
    rc_max_ms = 30_000 * 1.01 * 0.22e-6 * 1.10 * 1000
    assert 5 <= rc_min_ms and rc_max_ms <= 15

    # TI TPS7A20 SBVS338H p.6: guaranteed accuracy within stated VIN/load/TJ.
    mic_min, mic_max = 2.8 * .985, 2.8 * 1.015
    flash_min, flash_max = 1.8 - .03, 1.8 + .03
    adc_min, adc_max = 3.3 * .985, 3.3 * 1.015
    assert 2.3 <= mic_min and mic_max <= 3.0
    assert 1.65 <= flash_min and flash_max <= 1.95
    assert 3.0 <= adc_min and adc_max <= 3.6
    assert buck_min >= 3.1  # 2.8-V LDO accuracy VIN condition
    assert buck_min >= 2.3  # 1.8-V LDO accuracy VIN condition

    # TI TPS389030 SLVSD65A pp.3,5: fixed 3.0-V-rail threshold, +/-1%
    # over specified supply and temperature. NXP HW7 p.11 requires reset
    # before its 2.6-V internal DCDC low-voltage detection on power-down.
    por_fall_min = 2.89 * .99
    por_rise_max = 2.907 * 1.01
    assert por_fall_min > 2.6 and buck_min > por_rise_max
    por_ct_delay_min_ms = 9e-9 * 1.17 / 1.35e-6 * 1000
    por_ct_delay_max_ms = 11e-9 * 1.29 / .90e-6 * 1000

    # 10-uF +/-5% film and 20-kohm ADC input: ADC resistance is TYPICAL,
    # so this is a nominal topology calculation, never a worst-case proof.
    coupling_fc_typ_hz = 1 / (2 * pi * 20_000 * 10e-6)
    coupling_fc_5pct_hz = 1 / (2 * pi * 20_000 * 9.5e-6)
    phase_20hz_5pct_deg = degrees(atan(coupling_fc_5pct_hz / 20))

    # Infineon v1.20 pp.6,8,10: sensitivity -37 dBV maximum at 94 dBSPL;
    # extrapolation to 135 dBSPL is a linear-only headroom SCREEN because
    # 135 dBSPL AOP and output DC are typical, not guaranteed bounds.
    mic_135vrms_screen = 10 ** (-37 / 20) * 10 ** ((135 - 94) / 20)
    adc_headroom_db_screen = 20 * __import__("math").log10(2 / mic_135vrms_screen)

    # TPS7A20 DQN thetaJA 166.1 C/W, 3.3-V ADC/AFE LDO design reserve
    # 100 mA, assumed Board A 5-V max 5.5 V, 85 C ambient. This is a
    # reserve check; TI's ADC data gives only typical current at 48 kHz.
    adc_ldo_tj_reserve_c = 85 + (5.5 - adc_min) * .100 * 166.1
    # TI SBAA379 Table 1: a contextual 96-kHz, 4-channel, PLL-on,
    # DRE-off, linear-phase point uses BCLK/FSYNC=96, whereas this board's
    # 12.288-MHz/96-kHz plan uses 128. Its 25.68 mA is typical AVDD only.
    adc_matrix_typical_ma = 25.68

    # NXP CEC Rev 4 Table 22 pp.37-38: GPIO VIH >=0.7 NVCC, VIL <=0.3
    # NVCC; opposing on-chip 100-k pull current <=48 uA plus 1 uA input
    # leakage. External 4.7-k/1-k 1% networks use the worst resistor
    # ratios and opposing 49-uA current. This covers static levels only.
    rail_min, rail_max = buck_min, buck_max
    strap_r_hi, strap_r_lo = 4700 * 1.01, 4700 * .99
    fixture_r_hi, fixture_r_lo = 1000 * 1.01, 1000 * .99
    oppose_a = 49e-6
    normal_high_ratio_min = 1 - oppose_a * strap_r_hi / rail_min
    normal_low_ratio_max = oppose_a * strap_r_hi / rail_min
    recovery_high_v = (rail_min / fixture_r_hi - oppose_a) / (1 / fixture_r_hi + 1 / strap_r_lo)
    recovery_low_v = (rail_max / strap_r_lo + oppose_a) / (1 / strap_r_lo + 1 / fixture_r_lo)
    recovery_high_ratio_min = recovery_high_v / rail_min
    recovery_low_ratio_max = recovery_low_v / rail_max
    assert normal_high_ratio_min > .7 and normal_low_ratio_max < .3
    assert recovery_high_ratio_min > .7 and recovery_low_ratio_max < .3
    fixture_current_max_ma = rail_max / (strap_r_lo + fixture_r_lo) * 1000

    # ISSI IS25WP064A Rev A11, section 9.3 p.94: 30-mA max at 125 C for
    # program, status-write and erase; NORD 50-MHz active read <=12 mA.
    # The output-switching current is explicitly excluded from ICC1, so
    # neither number closes the total 1.8-V rail load budget.
    flash_core_program_erase_max_ma = 30.0
    flash_core_nord_50mhz_max_ma = 12.0

    return {
        "load_power": calculate_load_power(),
        "mcu_3v3_min_v": round(buck_min, 4),
        "mcu_3v3_max_v": round(buck_max, 4),
        "board_a_input_min_for_buck_pwm_v": round(buck_max + 1, 4),
        "dcdc_rc_min_ms": round(rc_min_ms, 4),
        "dcdc_rc_max_ms": round(rc_max_ms, 4),
        "dcdc_in_3v_deadline_at_rc_min_ms": round(.3 * rc_min_ms, 4),
        "mic_2v8_min_v": round(mic_min, 4),
        "mic_2v8_max_v": round(mic_max, 4),
        "flash_1v8_min_v": round(flash_min, 4),
        "flash_1v8_max_v": round(flash_max, 4),
        "adc_3v3_min_v": round(adc_min, 4),
        "adc_3v3_max_v": round(adc_max, 4),
        "por_fall_min_v": round(por_fall_min, 4),
        "por_rise_max_v": round(por_rise_max, 4),
        "por_healthy_rise_margin_v": round(buck_min - por_rise_max, 4),
        "por_dcdc_low_detect_margin_v": round(por_fall_min - 2.6, 4),
        "por_ct_delay_component_min_ms": round(por_ct_delay_min_ms, 3),
        "por_ct_delay_component_max_ms": round(por_ct_delay_max_ms, 3),
        "coupling_fc_typical_adc_hz": round(coupling_fc_typ_hz, 4),
        "coupling_fc_5pct_cap_typical_adc_hz": round(coupling_fc_5pct_hz, 4),
        "coupling_phase_20hz_5pct_cap_typical_adc_deg": round(phase_20hz_5pct_deg, 4),
        "mic_135dbspl_linear_extrapolation_vrms": round(mic_135vrms_screen, 4),
        "adc_135dbspl_headroom_screen_db": round(adc_headroom_db_screen, 4),
        "adc_ldo_tj_at_100ma_reserve_c": round(adc_ldo_tj_reserve_c, 2),
        "adc_ldo_tj_margin_at_100ma_reserve_c": round(125 - adc_ldo_tj_reserve_c, 2),
        "adc_ldo_reserve_to_unlike_clock_typical_ratio": round(100 / adc_matrix_typical_ma, 2),
        "adc_power_matrix_bclk_ratio": 96,
        "selected_audio_bclk_ratio": 128,
        "flash_03h_rom_to_rated_fmax_ratio": round(30 / 50, 2),
        "boot_normal_high_nvcc_ratio_min": round(normal_high_ratio_min, 4),
        "boot_normal_low_nvcc_ratio_max": round(normal_low_ratio_max, 4),
        "boot_fixture_high_nvcc_ratio_min": round(recovery_high_ratio_min, 4),
        "boot_fixture_low_nvcc_ratio_max": round(recovery_low_ratio_max, 4),
        "boot_fixture_opposing_strap_current_max_ma": round(fixture_current_max_ma, 4),
        "flash_core_program_erase_max_ma_at_125c": flash_core_program_erase_max_ma,
        "flash_core_nord_50mhz_max_ma_excluding_io": flash_core_nord_50mhz_max_ma,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(calculate(), indent=2))
