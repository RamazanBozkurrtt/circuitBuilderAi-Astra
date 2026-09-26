"""R1 requirements-control and phase-scoped gate validation."""

from __future__ import annotations

import hashlib
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


def check_status(report: dict, name: str, expected: str) -> None:
    actual = next(c["status"] for c in report["checks"] if c["gate"] == name)
    assert actual == expected, (name, expected, actual, report)


def main() -> int:
    checks: dict[str, str] = {}
    state = gate.load_json(ROOT, gate.STATE_FILE)
    definitions = gate.load_json(ROOT, gate.PHASE_FILE)
    contract = gate.load_json(ROOT, state["architecture"]["interface_contract"])
    gate.require_shape(state, definitions)
    assert state["current_phase"] == "R1"
    assert state["previous_gate"]["phase"] == "R0.5"
    assert state["previous_gate"]["result"] == "PASS"
    assert state["current_kicad_projects"] == []
    assert [d["id"] for d in state["open_decisions"]] == [f"D{i}" for i in range(1, 8)]
    assert all(d["status"] == "open" for d in state["open_decisions"])
    checks["state"] = "PASS: R1 checkpoint, previous R0.5 PASS, seven open decisions, no Product V1 KiCad claim"

    spec_path = gate.repo_path(ROOT, state["authoritative_product_spec"])
    digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    assert digest == "df537a98c9bbfdef1dd5bf8447441946985fb8e6b438e1ae9e7990510d5c6f44"
    checks["product_source"] = "PASS: authoritative Product V1 DOCX matches R0 hash"

    schema = gate.load_json(ROOT, gate.FINDING_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    finding_paths = sorted((ROOT / "validation" / "findings").glob("*.json"))
    findings = [json.loads(p.read_text(encoding="utf-8")) for p in finding_paths]
    assert len(findings) == 13
    for finding in findings:
        validator.validate(finding)
        assert finding["phase"] == "R1"
        assert finding["status"] == "open" and finding["blocking"] is True
        assert finding["evidence"] and finding["closure_criterion"]
    expected = {f["id"]: f["blocks_from_phase"] for f in findings}
    checkpoint = {x["id"]: x["blocks_from_phase"] for x in state["open_blockers"]}
    assert checkpoint == expected
    assert all(gate.PHASE_ORDER.index(p) > gate.PHASE_ORDER.index("R2") for p in expected.values())
    checks["findings"] = "PASS: 13 schema-valid evidenced findings, exact state sync, all due after R2"

    assert contract["boards"] == ["board_a", "board_b"]
    assert contract["connector_part"] is None and contract["pin_assignment"] is None
    assert contract["contract_status"] == "r1_signal_classes_controlled_electrical_open"
    assert len(contract["signals"]) == 12
    required = {
        "5V", "GND_RETURN", "BCLK", "LRCLK", "AUDIO_DATA", "MCLK",
        "I2C_SDA", "I2C_SCL", "AMP_MUTE", "AMP_FAULT", "PGOOD", "REVISION_OR_SERVICE",
    }
    assert {s["signal"] for s in contract["signals"]} == required
    assert all(s["required_count"] is None and s["voltage_domain"] is None for s in contract["signals"])
    assert next(s for s in contract["signals"] if s["signal"] == "MCLK")["inclusion"] == "optional_pending_R2"
    assert next(s for s in contract["signals"] if s["signal"] == "GND_RETURN")["inclusion"] == "product_required"
    checks["interface"] = "PASS: both boards, required signal classes, optional MCLK and unfrozen electrical/mechanical values"

    report_path = ROOT / "docs" / "product_v1" / "phase_r1_product_requirements.md"
    report = report_path.read_text(encoding="utf-8")
    assert all(f"| D{i} |" in report for i in range(1, 8))
    assert all(s in report for s in ("Board A", "Board B", "CONFIRMED", "PROVISIONAL", "OPEN", "CONFLICTING"))
    matrix = report.split("## 1. Product V1 acceptance matrix", 1)[1].split("## 2. Seven open decisions", 1)[0]
    matrix_rows = [line for line in matrix.splitlines() if line.startswith("| ") and not line.startswith(("| ID |", "| --- |"))]
    assert len(matrix_rows) >= 40
    for row in matrix_rows:
        cells = [part.strip() for part in row.strip("|").split("|")]
        assert len(cells) == 7, row
        assert any(status in cells[2] for status in ("CONFIRMED", "PROVISIONAL", "OPEN", "CONFLICTING")), row
    assert (ROOT / "validation" / "r1_product_requirements_validation.md").is_file()
    checks["reports"] = f"PASS: {len(matrix_rows)} classified acceptance rows, seven decisions and validation report present"

    current = gate.evaluate(ROOT, next_phase="R2")
    assert current["machine_result"] == "PASS", current
    check_status(current, "documentation_contract", "PASS")
    check_status(current, "blocking_findings", "PASS")
    check_status(current, "product_architecture", "PASS")
    assert current["human_gate"]["status"] == "NOT_EVALUATED"
    checks["r1_gate"] = "PASS: R1 machine gate permits only separately authorized R2; human gate remains separate"

    r3 = gate.evaluate(ROOT, phase_id="R3")
    check_status(r3, "blocking_findings", "BLOCKED")
    assert "PV1-R1-002" in next(c for c in r3["checks"] if c["gate"] == "blocking_findings")["detail"]
    checks["future_due_gate"] = "PASS: R3 gate sees its due boot/interface/ANC blockers"

    r6 = gate.evaluate(ROOT, phase_id="R6")
    assert r6["machine_result"] == "BLOCKED"
    for item in r6["checks"]:
        if item["gate"] in gate.HOOK_NAMES:
            assert item["status"] == "NOT_AVAILABLE"
    checks["future_kicad"] = "PASS: unimplemented KiCad hooks remain NOT_AVAILABLE; no false ERC/DRC PASS"

    with tempfile.TemporaryDirectory(prefix="astra_r1_gate_") as directory:
        fixture = Path(directory)
        for relative in (
            gate.STATE_FILE,
            gate.PHASE_FILE,
            gate.FINDING_SCHEMA,
            state["architecture"]["interface_contract"],
            state["authoritative_product_spec"],
            "docs/product_v1/phase_r1_product_requirements.md",
            "validation/r1_product_requirements_validation.md",
        ):
            put(fixture / relative, (ROOT / relative).read_bytes())
        for path in finding_paths:
            put(fixture / "validation" / "findings" / path.name, path.read_bytes())
        assert gate.evaluate(fixture, next_phase="R2")["machine_result"] == "PASS"
        changed = json.loads((fixture / "validation/findings/PV1-R1-002.json").read_text(encoding="utf-8"))
        changed["blocks_from_phase"] = "R2"
        (fixture / "validation/findings/PV1-R1-002.json").write_text(json.dumps(changed), encoding="utf-8")
        fixture_state = json.loads((fixture / gate.STATE_FILE).read_text(encoding="utf-8"))
        next(x for x in fixture_state["open_blockers"] if x["id"] == "PV1-R1-002")["blocks_from_phase"] = "R2"
        (fixture / gate.STATE_FILE).write_text(json.dumps(fixture_state), encoding="utf-8")
        injected = gate.evaluate(fixture, next_phase="R2")
        assert injected["machine_result"] == "BLOCKED", injected
        check_status(injected, "blocking_findings", "BLOCKED")
        checks["r2_blocker_injection"] = "PASS: a finding newly due at R2 blocks R1-to-R2 progression"

    for board in ("board_a_controller_afe", "board_b_power_amp"):
        assert not list((ROOT / "hardware" / "product_v1" / board).glob("*.kicad_*"))
    checks["kicad_scope"] = "PASS: no Product V1 KiCad artifacts exist"

    out = ROOT / "validation" / "r1" / "verification_results.json"
    out.write_text(json.dumps({"result": "PASS", "checks": checks}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
