"""Focused, read-only R4-A Board A closure gate; writes its validation result."""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from r4a_closure_calculations import calculate


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def run() -> dict:
    state = read("state/project_state.json")
    active = read("state/active_task.json")
    board = read("state/board_a_schematic_contract.json")
    pins = read("state/rt1062_pin_resource_map.json")
    findings = {n: read(f"validation/findings/PV1-R1-{n}.json") for n in ("001", "002", "012")}
    calc = calculate()
    checks = {
        "scope_is_board_a_001_002_012": (
            active.get("phase") in {"R4-A", "R4-A2"}
            and active.get("scope") == "board_a"
            and (
                active.get("findings") == ["001", "002", "012"]
                or set(active.get("blockers", [])) == {
                    "AFE electrical bounds", "boot hardware",
                    "hardware-relevant recovery policy", "Board A load and thermal proof",
                    "startup and POR proof",
                }
            )
        ),
        "no_kicad_authority": not active.get("constraints", {}).get("modify_kicad") and not state.get("current_kicad_projects"),
        "r5_unauthorized": state.get("current_gate", {}).get("r5_authorized") is False,
        "four_dual_buffers_selected": board.get("microphone_afe", {}).get("r4a_selected_circuit", {}).get("buffer_mpn") == "OPA2320AIDGKR" and board["microphone_afe"]["r4a_selected_circuit"].get("buffer_quantity") == 4,
        "flash_matches_pin_map": board.get("components", {}).get("flash", {}).get("mpn") == pins.get("r4a_board_a_selection", {}).get("flash", {}).get("mpn") == "IS25WP064AJBLE",
        "power_parts_selected": all(x.get("regulator_mpn") for x in board.get("power_tree", {}).get("rails", []) if x.get("name") != "RT1062_CORE_INTERNAL_DCDC"),
        "rail_voltage_corners_in_device_ranges": 3 <= calc["mcu_3v3_min_v"] < calc["mcu_3v3_max_v"] <= 3.6 and 2.3 <= calc["mic_2v8_min_v"] < calc["mic_2v8_max_v"] <= 3 and 1.65 <= calc["flash_1v8_min_v"] < calc["flash_1v8_max_v"] <= 1.95,
        "finding_identity": all(findings[n].get("id") == f"PV1-R1-{n}" and findings[n].get("blocks_from_phase") == "R4" for n in findings),
        "pin_allocations_collision_free": pins.get("collision_check", {}).get("duplicate_pads") is False and pins.get("collision_check", {}).get("duplicate_balls") is False and pins.get("collision_check", {}).get("reserved_overlap") is False,
    }
    requirements = state.get("r4a_closure", {}).get("requirements", [])
    expected = {
        "001_afe_electrical": "SCHEMATIC_ENTRY_BLOCKER",
        "001_afe_bench": "PHYSICAL_BENCH_VALIDATION",
        "002_boot_hardware": "SCHEMATIC_ENTRY_BLOCKER",
        "002_recovery_policy": "SCHEMATIC_ENTRY_BLOCKER",
        "002_tested_boot_image": "FIRMWARE_BRINGUP_VALIDATION",
        "002_recovery_test": "FIRMWARE_BRINGUP_VALIDATION",
        "002_clock_usb_bench": "PHYSICAL_BENCH_VALIDATION",
        "012_a_load_power": "SCHEMATIC_ENTRY_BLOCKER",
        "012_a_startup": "SCHEMATIC_ENTRY_BLOCKER",
        "012_a_bench": "PHYSICAL_BENCH_VALIDATION",
        "012_board_b_interface": "LATER_BOARD_B_OR_INTERFACE_WORK",
    }
    classes = {
        "SCHEMATIC_ENTRY_BLOCKER", "FIRMWARE_BRINGUP_VALIDATION",
        "PHYSICAL_BENCH_VALIDATION", "LATER_BOARD_B_OR_INTERFACE_WORK",
    }
    checks["requirements_classified_once"] = (
        len(requirements) == len(expected)
        and {item.get("id") for item in requirements} == set(expected)
        and all(
            item.get("classification") in classes
            and item.get("classification") == expected.get(item.get("id"))
            and item.get("finding") in findings
            and item.get("id", "").startswith(item.get("finding", "") + "_")
            for item in requirements
        )
    )
    checks["phase_boundary"] = all(
        (item.get("classification") == "SCHEMATIC_ENTRY_BLOCKER")
        == (item.get("blocks_r4a") is True)
        and item.get("required_by_phase") == (
            "R4" if item.get("classification") in {
                "SCHEMATIC_ENTRY_BLOCKER", "LATER_BOARD_B_OR_INTERFACE_WORK"
            } else "R14"
        )
        for item in requirements
    )
    open_schematic = {
        item.get("finding")
        for item in requirements
        if item.get("classification") == "SCHEMATIC_ENTRY_BLOCKER"
        and item.get("status") != "closed"
    }
    power = board.get("power_tree", {})
    load = power.get("load_budget_a") or {}
    lp = calc["load_power"]
    load_rails = {item.get("name"): item for item in load.get("rails", [])}
    checks["012_load_all_rails_itemized"] = (
        set(load_rails) == {"MCU_3V3", "ADC_AVDD_3V3", "MIC_2V8", "FLASH_SD1_1V8"}
        and load_rails["MCU_3V3"].get("itemized_ma") == lp["mcu_buck_itemized_ma"]
        and load_rails["MCU_3V3"].get("design_ceiling_ma") == lp["mcu_buck_design_ceiling_ma"]
        and load_rails["ADC_AVDD_3V3"].get("design_ceiling_ma") == lp["adc_afe_design_ceiling_ma"]
        and load_rails["MIC_2V8"].get("design_ceiling_ma") == lp["mic_design_ceiling_ma"]
        and load_rails["FLASH_SD1_1V8"].get("design_ceiling_ma") == lp["flash_design_ceiling_ma"]
    )
    five = load.get("five_volt_input", {})
    checks["012_input_and_thermal_screen_consistent"] = (
        five.get("calculated_ma_at_4p5v_and_70pct_buck_efficiency") == lp["input_design_ma_at_4p5v"]
        and five.get("calculated_with_startup_ma") == lp["input_design_with_startup_ma"]
        and five.get("margin_to_design_ceiling_ma") == lp["input_margin_with_startup_to_750ma_ma"]
        and lp["adc_afe_tj_c_at_85c"] < 125
        and lp["buck_tj_c_at_85c_assumed_eta"] < 125
        and lp["efficiency_floor_is_manufacturer_guaranteed"] is False
        and lp["thermal_resistance_is_product_board_guaranteed"] is False
        and load.get("status") == "CALCULATED_ENGINEERING_ENVELOPE_PENDING_COMPONENT_AND_THERMAL_PROOF"
    )
    checks["contract_readiness_consistent"] = (
        ("001" in open_schematic or board.get("microphone_afe", {}).get("status") == "READY")
        and ("002" in open_schematic or pins.get("status") == "READY")
        and (
            "012" in open_schematic
            or (
                power.get("load_budget_a") is not None
                and all(rail.get("status") == "READY" for rail in power.get("rails", []))
                and power.get("sequence_verified") is True
            )
        )
    )
    checks["finding_readiness_consistent"] = all(
        n in open_schematic or findings[n].get("blocking") is False
        for n in ("001", "002")
    )
    policy = pins.get("r4a_board_a_selection", {}).get("boot_straps", {}).get("v1_policy", {})
    recovery_closed = any(
        item.get("id") == "002_recovery_policy" and item.get("status") == "closed"
        for item in requirements
    )
    checks["closed_recovery_policy_frozen"] = not recovery_closed or policy == {
        "boot_fuse_select": 0,
        "otp_programming": False,
        "hab_closed": False,
        "factory_route": "rom_lpuart1_powered_fixture",
        "field_route": "rom_lpuart1_powered_service_fixture",
        "ota_update": False,
        "usb_recovery_required": False,
    }
    errors = [name for name, passed in checks.items() if not passed]
    blockers = {
        item["id"]: item["requirement"]
        for item in requirements
        if item.get("blocks_r4a") is True and item.get("status") != "closed"
    }
    if "012_a_load_power" in blockers and load.get("unclosed_exact_items"):
        blockers["012_a_load_power"] = " ".join(load["unclosed_exact_items"])
    result = "FAIL" if errors else "BLOCKED" if blockers else "PASS"
    return {
        "phase": "R4-A",
        "result": result,
        "scope": "Board A findings 001, 002 and Board A portion of 012",
        "checks": checks,
        "errors": errors,
        "blockers": blockers,
        "requirements": requirements,
        "calculations": calc,
        "r5_authorized": False,
    }


if __name__ == "__main__":
    report = run()
    target = ROOT / "validation/r4a_gate_result.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"R4-A: {report['result']}")
    for value in report["errors"]:
        print(f"ERROR: {value}")
    for key, value in report["blockers"].items():
        print(f"{key}: {value}")
    raise SystemExit(0 if report["result"] == "PASS" else 1)
