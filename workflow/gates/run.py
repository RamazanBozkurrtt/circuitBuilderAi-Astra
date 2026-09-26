"""Machine checks for Product V1 phase readiness; human approval is separate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


GATE_NAMES = {"documentation_contract", "blocking_findings", "product_architecture"}
HOOK_NAMES = {
    "erc": "Product V1 ERC adapter and verified report are not implemented.",
    "drc": "Product V1 DRC adapter and verified report are not implemented.",
    "hierarchical_interface_audit": "Product V1 interface audit is not implemented.",
    "pin_audit": "Product V1 pin audit is not implemented.",
    "bom_validation": "Product V1 BOM validation is not implemented.",
}
PHASE_FILE = "workflow/phase_definitions/product_v1.json"
STATE_FILE = "state/project_state.json"
FINDING_SCHEMA = "workflow/schemas/engineering_finding.schema.json"
PHASE_ORDER = ["R0", "R0.5"] + [f"R{i}" for i in range(1, 15)]


class GateError(Exception):
    """Invalid or unsafe machine-readable gate input."""


def repo_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise GateError(f"Expected a nonempty relative repository path: {relative!r}")
    base = root.resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base):
        raise GateError(f"Path escapes repository: {relative}")
    return path


def load_json(root: Path, relative: str) -> Any:
    path = repo_path(root, relative)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"Cannot read valid JSON at {relative}: {exc}") from exc


def result(name: str, status: str, detail: str) -> dict[str, str]:
    return {"gate": name, "status": status, "detail": detail}


def require_shape(state: Any, definitions: Any) -> None:
    if not isinstance(state, dict) or not isinstance(definitions, dict):
        raise GateError("Project state and phase definitions must be JSON objects.")
    required_state = {
        "product", "architecture", "current_phase", "previous_gate",
        "board_a_status", "board_b_status", "interface_status",
        "open_blockers", "authoritative_product_spec", "current_contracts",
        "current_kicad_projects", "latest_validation", "last_verified_commit",
    }
    missing = required_state - state.keys()
    if missing:
        raise GateError(f"Project state lacks fields: {', '.join(sorted(missing))}")
    if not isinstance(state["open_blockers"], list) or not isinstance(state["current_contracts"], list):
        raise GateError("open_blockers and current_contracts must be arrays.")
    if not isinstance(state["current_kicad_projects"], list):
        raise GateError("current_kicad_projects must be an array.")
    phases = definitions.get("phases")
    if not isinstance(phases, list) or not phases:
        raise GateError("Phase definitions must contain a nonempty phases array.")
    ids = [p.get("id") for p in phases if isinstance(p, dict)]
    if len(ids) != len(phases) or len(ids) != len(set(ids)):
        raise GateError("Phase IDs must be present and unique.")
    for phase in phases:
        for key in ("objective", "human_gate"):
            if not isinstance(phase.get(key), str) or not phase[key]:
                raise GateError(f"{phase['id']} lacks {key}.")
        for key in ("required_inputs", "required_outputs", "machine_gates", "allowed_next_phase"):
            if not isinstance(phase.get(key), list):
                raise GateError(f"{phase['id']} lacks array {key}.")
        if any(target not in ids for target in phase["allowed_next_phase"]):
            raise GateError(f"{phase['id']} has an unknown allowed next phase.")
        if any(g not in GATE_NAMES | HOOK_NAMES.keys() for g in phase["machine_gates"]):
            raise GateError(f"{phase['id']} has an unknown machine gate.")


def documentation_gate(root: Path, phase: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    paths = phase["required_inputs"] + phase["required_outputs"] + state["current_contracts"]
    missing = [p for p in paths if not repo_path(root, p).is_file()]
    if missing:
        return result("documentation_contract", "BLOCKED", "Missing required files: " + ", ".join(missing))
    return result("documentation_contract", "PASS", f"{len(paths)} required file references exist.")


def findings_gate(root: Path, state: dict[str, Any], gate_phase: str) -> dict[str, str]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return result("blocking_findings", "FAIL", "Install workflow/requirements.txt to validate findings.")

    schema = load_json(root, FINDING_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    directory = repo_path(root, "validation/findings")
    if not directory.is_dir():
        return result("blocking_findings", "FAIL", "Finding directory is missing.")
    unresolved: dict[str, str] = {}
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        finding = load_json(root, path.relative_to(root.resolve()).as_posix())
        errors = list(validator.iter_errors(finding))
        if errors:
            return result("blocking_findings", "FAIL", f"{path.name} violates finding schema: {errors[0].message}")
        if finding["id"] in seen:
            return result("blocking_findings", "FAIL", f"Duplicate finding ID: {finding['id']}")
        seen.add(finding["id"])
        if finding["blocking"] and finding["status"] != "resolved":
            unresolved[finding["id"]] = finding["blocks_from_phase"]
    checkpoint: dict[str, str] = {}
    for entry in state["open_blockers"]:
        if not isinstance(entry, dict) or set(entry) != {"id", "blocks_from_phase"}:
            return result("blocking_findings", "FAIL", "Each state blocker must have id and blocks_from_phase.")
        if entry["id"] in checkpoint:
            return result("blocking_findings", "FAIL", f"Duplicate state blocker: {entry['id']}")
        checkpoint[entry["id"]] = entry["blocks_from_phase"]
    if checkpoint != unresolved:
        return result("blocking_findings", "FAIL", "State open_blockers must exactly match unresolved blocking findings.")
    if gate_phase not in PHASE_ORDER:
        return result("blocking_findings", "FAIL", f"Unknown gate phase: {gate_phase}")
    due = sorted(
        finding_id for finding_id, start in unresolved.items()
        if PHASE_ORDER.index(start) <= PHASE_ORDER.index(gate_phase)
    )
    if due:
        return result("blocking_findings", "BLOCKED", f"Blockers due by {gate_phase}: " + ", ".join(due))
    return result(
        "blocking_findings", "PASS",
        f"No blockers due by {gate_phase}; {len(unresolved)} later blockers tracked among {len(seen)} findings."
    )


def architecture_gate(root: Path, state: dict[str, Any]) -> dict[str, str]:
    architecture = state.get("architecture")
    if not isinstance(architecture, dict):
        return result("product_architecture", "FAIL", "Architecture must be an object.")
    boards = architecture.get("boards")
    if not isinstance(boards, list) or {b.get("id") for b in boards if isinstance(b, dict)} != {"board_a", "board_b"}:
        return result("product_architecture", "FAIL", "Product V1 must identify exactly Board A and Board B.")
    contract_ref = architecture.get("interface_contract")
    if not isinstance(contract_ref, str):
        return result("product_architecture", "FAIL", "No controlled interface contract path.")
    if contract_ref not in state["current_contracts"]:
        return result("product_architecture", "FAIL", "Interface contract is absent from current_contracts.")
    contract = load_json(root, contract_ref)
    if (
        not isinstance(contract, dict)
        or not contract.get("schema_version")
        or contract.get("product") != state["product"]
        or set(contract.get("boards", [])) != {"board_a", "board_b"}
        or not isinstance(contract.get("signals"), list)
        or not contract["signals"]
        or not contract.get("contract_status")
        or not isinstance(contract.get("source"), dict)
    ):
        return result("product_architecture", "FAIL", "Interface contract lacks the two-board identity, source or signal inventory.")
    source = contract["source"].get("path")
    if not isinstance(source, str) or source != state["authoritative_product_spec"]:
        return result("product_architecture", "FAIL", "Interface source must match the authoritative product spec.")
    if not repo_path(root, source).is_file():
        return result("product_architecture", "BLOCKED", "Authoritative product spec is missing.")
    required_signal_fields = {
        "signal", "source_board", "destination_board", "direction",
        "voltage_domain", "signal_type", "required_count", "status", "evidence",
    }
    names: set[str] = set()
    for signal in contract["signals"]:
        if not isinstance(signal, dict) or required_signal_fields - signal.keys():
            return result("product_architecture", "FAIL", "A contract signal lacks required fields.")
        if signal["signal"] in names or not signal["evidence"]:
            return result("product_architecture", "FAIL", "Contract signal names must be unique and evidenced.")
        names.add(signal["signal"])
    if not {"5V", "GND_RETURN", "BCLK", "LRCLK", "AUDIO_DATA", "I2C_SDA", "I2C_SCL", "AMP_MUTE", "AMP_FAULT", "PGOOD"} <= names:
        return result("product_architecture", "BLOCKED", "Required Product V1 interface signal classes are missing.")
    for project in state["current_kicad_projects"]:
        path = repo_path(root, project)
        if not path.is_relative_to(repo_path(root, "hardware/product_v1")):
            return result("product_architecture", "FAIL", "Product V1 project path points outside hardware/product_v1.")
        if not path.is_file():
            return result("product_architecture", "BLOCKED", f"Claimed Product V1 KiCad project is missing: {project}")
    if state["current_kicad_projects"]:
        return result("product_architecture", "PASS", "Two-board architecture and controlled interface identified; listed project paths exist.")
    return result("product_architecture", "PASS", "Two-board architecture and controlled placeholder interface identified; no Product V1 KiCad claim.")


def evaluate(root: Path, phase_id: str | None = None, next_phase: str | None = None) -> dict[str, Any]:
    try:
        state = load_json(root, STATE_FILE)
        definitions = load_json(root, PHASE_FILE)
        require_shape(state, definitions)
        selected = phase_id or state["current_phase"]
        phase = next((p for p in definitions["phases"] if p["id"] == selected), None)
        if phase is None:
            raise GateError(f"Unknown phase: {selected}")
        checks = []
        for gate in phase["machine_gates"]:
            if gate == "documentation_contract":
                checks.append(documentation_gate(root, phase, state))
            elif gate == "blocking_findings":
                checks.append(findings_gate(root, state, next_phase or selected))
            elif gate == "product_architecture":
                checks.append(architecture_gate(root, state))
            else:
                checks.append(result(gate, "NOT_AVAILABLE", HOOK_NAMES[gate]))
        if next_phase is not None:
            if next_phase not in phase["allowed_next_phase"]:
                checks.append(result("allowed_next_phase", "FAIL", f"{selected} cannot advance to {next_phase}."))
            else:
                checks.append(result("allowed_next_phase", "PASS", f"{selected} may advance to {next_phase} after human approval."))
        statuses = {c["status"] for c in checks}
        machine_result = "FAIL" if "FAIL" in statuses else "BLOCKED" if statuses & {"BLOCKED", "NOT_AVAILABLE"} else "PASS"
        return {
            "phase": selected,
            "machine_result": machine_result,
            "checks": checks,
            "human_gate": {"status": "NOT_EVALUATED", "criterion": phase["human_gate"]},
            "phase_state_changed": False,
        }
    except Exception as exc:
        return {
            "phase": phase_id,
            "machine_result": "FAIL",
            "checks": [result("framework", "FAIL", str(exc))],
            "human_gate": {"status": "NOT_EVALUATED"},
            "phase_state_changed": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--phase", help="Evaluate a phase; defaults to state.current_phase.")
    parser.add_argument("--next-phase", help="Check the phase's allowed next phase; never changes project state.")
    args = parser.parse_args()
    report = evaluate(args.root, args.phase, args.next_phase)
    print(json.dumps(report, indent=2))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["machine_result"]]


if __name__ == "__main__":
    sys.exit(main())
