"""Reproducible R0.5 workflow validation; fixtures stay outside the repository."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "workflow" / "gates"))
import run as gate  # noqa: E402


def put(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    checks: dict[str, str] = {}
    json_paths = sorted(
        list((ROOT / "workflow").rglob("*.json"))
        + list((ROOT / "state").rglob("*.json"))
        + list((ROOT / "validation" / "findings").glob("*.json"))
    )
    for path in json_paths:
        json.loads(path.read_text(encoding="utf-8"))
    checks["json_parse"] = f"PASS: {len(json_paths)} JSON files"

    schema = gate.load_json(ROOT, gate.FINDING_SCHEMA)
    Draft202012Validator.check_schema(schema)
    template = gate.load_json(ROOT, "workflow/templates/engineering_finding.template.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(template)
    checks["finding_schema"] = "PASS: Draft 2020-12 schema and template validate"

    state = gate.load_json(ROOT, gate.STATE_FILE)
    definitions = gate.load_json(ROOT, gate.PHASE_FILE)
    contract = gate.load_json(ROOT, state["architecture"]["interface_contract"])
    gate.require_shape(state, definitions)
    ids = [phase["id"] for phase in definitions["phases"]]
    assert ids == ["R0", "R0.5"] + [f"R{i}" for i in range(1, 15)]
    assert len(state["open_decisions"]) == 7
    assert state["current_kicad_projects"] == []
    assert contract["boards"] == ["board_a", "board_b"]
    assert contract["connector_part"] is None and contract["pin_assignment"] is None
    assert all(s["voltage_domain"] is None and s["required_count"] is None for s in contract["signals"])
    checks["state_and_interface"] = "PASS: R0 baseline, seven open decisions, unfrozen signal values"

    for phase in definitions["phases"]:
        for relative in phase["required_inputs"] + phase["required_outputs"]:
            path = gate.repo_path(ROOT, relative)
            if path.suffix in {".kicad_sch", ".kicad_pcb"}:
                assert path.is_relative_to(ROOT / "hardware" / "product_v1")
        assert phase["human_gate"]
    try:
        gate.repo_path(ROOT, "../outside")
    except gate.GateError:
        pass
    else:
        raise AssertionError("A path escaping the repository was accepted.")
    checks["phase_paths"] = "PASS: all 16 phase contracts use safe repository paths"

    assert (ROOT / "hardware" / "kicad" / "circuitBuilderAi-Astra.kicad_pro").is_file()
    for board in ("board_a_controller_afe", "board_b_power_amp"):
        directory = ROOT / "hardware" / "product_v1" / board
        assert directory.is_dir() and (directory / "README.md").is_file()
        assert not list(directory.glob("*.kicad_*"))
    checks["hardware_scope"] = "PASS: legacy retained; Product V1 directories contain no KiCad artifacts"

    with tempfile.TemporaryDirectory(prefix="astra_r05_gate_") as temporary:
        fixture_root = Path(temporary)
        for relative in (
            gate.PHASE_FILE,
            gate.FINDING_SCHEMA,
            state["architecture"]["interface_contract"],
        ):
            put(fixture_root / relative, (ROOT / relative).read_bytes())
        fixture_state = dict(state)
        fixture_state["current_phase"] = "R0.5"
        fixture_state["previous_gate"] = {"phase": "R0", "result": "PASS", "report": "docs/rebaseline/phase_r0_b2b_two_board_rebaseline.md"}
        fixture_state["open_blockers"] = []
        fixture_state["current_contracts"] = ["state/board_to_board_interface.json"]
        (fixture_root / gate.STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        (fixture_root / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        phase = next(p for p in definitions["phases"] if p["id"] == "R0.5")
        required = phase["required_inputs"] + phase["required_outputs"] + [
            state["authoritative_product_spec"]
        ]
        for relative in required:
            if not (fixture_root / relative).exists():
                put(fixture_root / relative, b"fixture: path presence only\n")
        (fixture_root / "validation" / "findings").mkdir(parents=True)

        clean = gate.evaluate(fixture_root)
        assert clean["machine_result"] == "PASS", clean
        checks["baseline_gate"] = "PASS: clean R0.5 machine gate passes; human gate stays NOT_EVALUATED"
        assert clean["human_gate"]["status"] == "NOT_EVALUATED"
        assert clean["phase_state_changed"] is False

        finding = dict(template)
        finding["id"] = "R05-TEST-001"
        finding["blocks_from_phase"] = "R0.5"
        fixture_state["open_blockers"] = [{"id": finding["id"], "blocks_from_phase": "R0.5"}]
        (fixture_root / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        finding_path = fixture_root / "validation" / "findings" / "R05-TEST-001.json"
        finding_path.write_text(json.dumps(finding), encoding="utf-8")
        blocked = gate.evaluate(fixture_root)
        assert blocked["machine_result"] == "BLOCKED", blocked
        assert "R05-TEST-001" in next(c for c in blocked["checks"] if c["gate"] == "blocking_findings")["detail"]
        checks["unresolved_finding"] = "PASS: blocking=true/open prevents advancement"

        finding["status"] = "accepted"
        finding_path.write_text(json.dumps(finding), encoding="utf-8")
        assert gate.evaluate(fixture_root)["machine_result"] == "BLOCKED"
        finding["status"] = "deferred"
        finding_path.write_text(json.dumps(finding), encoding="utf-8")
        assert gate.evaluate(fixture_root)["machine_result"] == "BLOCKED"
        checks["accepted_deferred"] = "PASS: accepted/deferred blocking findings still block"

        finding["status"] = "resolved"
        finding["resolved_by"] = "test fixture"
        finding["resolution"] = "Test-only closure."
        finding_path.write_text(json.dumps(finding), encoding="utf-8")
        fixture_state["open_blockers"] = []
        (fixture_root / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        assert gate.evaluate(fixture_root)["machine_result"] == "PASS"
        checks["resolved_finding"] = "PASS: evidenced resolution clears fixture blocker"

        finding["severity"] = "invalid_severity"
        finding_path.write_text(json.dumps(finding), encoding="utf-8")
        assert gate.evaluate(fixture_root)["machine_result"] == "FAIL"
        finding_path.unlink()
        checks["invalid_finding"] = "PASS: schema-invalid finding fails gate"

        future_finding = dict(template)
        future_finding["id"] = "R05-FUTURE-001"
        future_finding["blocks_from_phase"] = "R4"
        finding_path.write_text(json.dumps(future_finding), encoding="utf-8")
        fixture_state["open_blockers"] = [{"id": future_finding["id"], "blocks_from_phase": "R4"}]
        (fixture_root / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        assert gate.evaluate(fixture_root)["machine_result"] == "PASS"
        assert next(c for c in gate.evaluate(fixture_root, phase_id="R4")["checks"] if c["gate"] == "blocking_findings")["status"] == "BLOCKED"
        finding_path.unlink()
        fixture_state["open_blockers"] = []
        (fixture_root / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        checks["phase_scoped_blocker"] = "PASS: R4 finding is tracked but does not block R0.5"

        future = gate.evaluate(fixture_root, phase_id="R6")
        assert future["machine_result"] == "BLOCKED", future
        assert all(
            c["status"] == "NOT_AVAILABLE"
            for c in future["checks"]
            if c["gate"] in gate.HOOK_NAMES
        )
        checks["future_kicad"] = "PASS: absent Product V1 KiCad hooks report NOT_AVAILABLE and block R6"

        bad_transition = gate.evaluate(fixture_root, next_phase="R5")
        assert bad_transition["machine_result"] == "FAIL"
        good_transition = gate.evaluate(fixture_root, next_phase="R1")
        assert good_transition["machine_result"] == "PASS"
        checks["transition"] = "PASS: only the declared next phase is machine-permitted"

    output = ROOT / "validation" / "r0_5" / "verification_results.json"
    output.write_text(json.dumps({"result": "PASS", "checks": checks}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
