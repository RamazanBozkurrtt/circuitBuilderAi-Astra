"""Machine checks for Product V1 phase readiness; human approval is separate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


GATE_NAMES = {"documentation_contract", "blocking_findings", "product_architecture", "r2_component_verification", "r3_system_architecture", "r4_schematic_readiness"}
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
    return result("product_architecture", "PASS", "Two-board architecture and controlled interface identified; no Product V1 KiCad claim.")


def r2_component_gate(root: Path, state: dict[str, Any]) -> dict[str, str]:
    """R2 evidence and decision inventory; does not assert schematic readiness."""
    report_ref = "docs/product_v1/phase_r2_component_verification.md"
    index_ref = "docs/product_v1/component_evidence_index.md"
    contract_ref = "state/product_v1_component_contract.json"
    for ref in (report_ref, index_ref, contract_ref):
        if not repo_path(root, ref).is_file():
            return result("r2_component_verification", "BLOCKED", f"Missing R2 output: {ref}")
    report = repo_path(root, report_ref).read_text(encoding="utf-8")
    index = repo_path(root, index_ref).read_text(encoding="utf-8")
    facts = load_json(root, contract_ref)
    if "## 1. Decision matrix" not in report or "## 5. End-to-end digital audio" not in report:
        return result("r2_component_verification", "FAIL", "R2 report lacks the decision matrix or audio analysis.")
    expected = {"IM73A135V01", "TLV320ADC5140", "IMXRT1062", "TAS5825M"}
    components = facts.get("components", {}) if isinstance(facts, dict) else {}
    if set(components) != expected or set(facts.get("boards", [])) != {"board_a", "board_b"}:
        return result("r2_component_verification", "FAIL", "Four components and both boards must appear in R2 facts.")
    statuses = {"APPROVED FOR ARCHITECTURE", "PROVISIONALLY APPROVED", "REJECTED", "BLOCKED BY MISSING EVIDENCE"}
    if any(components[name].get("architecture_status") not in statuses or name not in report for name in expected):
        return result("r2_component_verification", "FAIL", "A component lacks a valid architecture decision or report row.")
    local_evidence = [
        "datasheets/microphone/im73a135_datasheet_v1_20.pdf",
        "datasheets/product_v1/tlv320adc5140_sbas892a.pdf",
        "datasheets/product_v1/tlv320adcx140_sample_rate_sbaa381b.pdf",
        "datasheets/product_v1/tas5825m_slaseh7h.pdf",
    ]
    if any(not repo_path(root, ref).is_file() for ref in local_evidence):
        return result("r2_component_verification", "BLOCKED", "A controlled local manufacturer PDF is missing.")
    if any(f"{name}" not in index for name in ("Infineon", "NXP", "TLV320ADC5140", "TAS5825M")):
        return result("r2_component_verification", "FAIL", "Evidence index omits a core manufacturer/component.")
    for link in re.findall(r"\]\(([^)]+)\)", index):
        if link.startswith("https://"):
            if not any(link.startswith(f"https://{domain}/") for domain in (
                "www.infineon.com", "www.ti.com", "www.nxp.com", "cache.nxp.com", "docs.mcuxpresso.nxp.com",
                "mcuxpresso.nxp.com", "community.nxp.com", "www.pjrc.com", "www.issi.com",
                "github.com/nxp-mcuxpresso",
            )):
                return result("r2_component_verification", "FAIL", f"Evidence link is not a listed primary source: {link}")
        elif not (repo_path(root, "docs/product_v1/" + link)).is_file():
            return result("r2_component_verification", "FAIL", f"Evidence index local link is missing: {link}")
    for number in range(1, 14):
        ref = f"validation/findings/PV1-R1-{number:03}.json"
        finding = load_json(root, ref)
        if number in {1, 2, 4, 9, 11, 12, 13} and not any(
            "R2" in item.get("note", "") or "phase_r2" in item.get("source", "")
            or item.get("source", "").startswith("datasheets/product_v1/")
            or item.get("source", "").startswith("datasheets/microphone/")
            for item in finding.get("evidence", [])
        ):
            return result("r2_component_verification", "FAIL", f"R2 evidence absent from finding {number:03}.")
    if state.get("current_phase") != "R2" or state.get("current_kicad_projects"):
        return result("r2_component_verification", "FAIL", "R2 phase state or KiCad inventory is incoherent.")
    if any(not isinstance(HOOK_NAMES.get(h), str) for h in ("erc", "drc", "hierarchical_interface_audit", "pin_audit", "bom_validation")):
        return result("r2_component_verification", "FAIL", "Future KiCad hooks lost their NOT_AVAILABLE definitions.")
    return result("r2_component_verification", "PASS", "R2 report/matrix, four component facts, controlled evidence, 13 preserved findings and both boards verified; future KiCad hooks NOT_AVAILABLE. This is not schematic readiness.")


def r3_system_gate(root: Path, state: dict[str, Any]) -> dict[str, str]:
    """Check R3 system structure and dependencies, not detailed circuit correctness."""
    name = "r3_system_architecture"
    report_ref = "docs/product_v1/phase_r3_system_architecture.md"
    architecture_ref = "state/product_v1_architecture_contract.json"
    for ref in (report_ref, architecture_ref):
        if not repo_path(root, ref).is_file():
            return result(name, "BLOCKED", f"Missing R3 output: {ref}")
    report = repo_path(root, report_ref).read_text(encoding="utf-8")
    architecture = load_json(root, architecture_ref)
    interface = load_json(root, "state/board_to_board_interface.json")
    if not isinstance(architecture, dict) or architecture.get("source") != report_ref:
        return result(name, "FAIL", "R3 architecture contract/source is incoherent.")
    if not all(marker in report for marker in ("Functional architecture", "digital-audio", "electrical inventory", "ACYCLIC = true", "Independent safe-state")):
        return result(name, "FAIL", "R3 report lacks a required architecture section.")
    boards = architecture.get("boards", {})
    if not isinstance(boards, dict) or set(boards) != {"board_a", "board_b"}:
        return result(name, "FAIL", "Board A/B ownership is incomplete.")
    for board in boards.values():
        if not isinstance(board, dict) or len(board.get("owns", [])) < 7:
            return result(name, "FAIL", "Board ownership lacks major functions.")
    audio = architecture.get("audio", {})
    expected_links = {"adc_to_mcu": (4, 12288000), "mcu_to_amp": (2, 6144000)}
    for link, (channels, bclk) in expected_links.items():
        record = audio.get(link, {})
        if record.get("rate_hz") != 96000 or record.get("channels") != channels or record.get("bclk_hz") != bclk:
            return result(name, "FAIL", f"Audio baseline mismatch: {link}.")
        if record.get("slot_bits") * record.get("slots") * record.get("rate_hz") != bclk:
            return result(name, "FAIL", f"Audio clock calculation mismatch: {link}.")
    if architecture.get("board_interface") != "state/board_to_board_interface.json":
        return result(name, "FAIL", "Architecture does not identify the controlled B2B contract.")
    signals = interface.get("signals", [])
    if not isinstance(signals, list):
        return result(name, "FAIL", "B2B signals must be a list.")
    by_name = {s.get("signal"): s for s in signals if isinstance(s, dict)}
    if len(by_name) != len(signals):
        return result(name, "FAIL", "Duplicate or malformed B2B signal entry.")
    active = {"5V", "GND_RETURN", "BCLK", "LRCLK", "AUDIO_DATA", "I2C_SDA", "I2C_SCL", "AMP_MUTE", "AMP_FAULT", "PGOOD"}
    if set(by_name) != active | {"MCLK", "REVISION_OR_SERVICE"}:
        return result(name, "FAIL", "Required active/explicitly excluded signal inventory differs.")
    expected_directions = {
        "5V": ("board_b", "board_a", "b_to_a"),
        "GND_RETURN": ("board_b", "board_a", "shared_return"),
        "BCLK": ("board_a", "board_b", "a_to_b"),
        "LRCLK": ("board_a", "board_b", "a_to_b"),
        "AUDIO_DATA": ("board_a", "board_b", "a_to_b"),
        "I2C_SDA": ("board_a", "board_b", "bidirectional"),
        "I2C_SCL": ("board_a", "board_b", "a_to_b"),
        "AMP_MUTE": ("board_a", "board_b", "a_to_b"),
        "AMP_FAULT": ("board_b", "board_a", "b_to_a"),
        "PGOOD": ("board_b", "board_a", "b_to_a"),
    }
    for n, expected in expected_directions.items():
        actual = tuple(by_name[n].get(key) for key in ("source_board", "destination_board", "direction"))
        if actual != expected:
            return result(name, "FAIL", f"Cross-board direction conflicts for {n}.")
    signal_fields = ("nominal_logic_level", "clock_data_relationship", "safe_default_state", "power_off_behavior", "buffer_translation", "return_adjacency")
    for signal in signals:
        n = signal["signal"]
        count = signal.get("required_count")
        if not isinstance(count, int) or count < (1 if n in active else 0) or (n not in active and count != 0):
            return result(name, "FAIL", f"Invalid contact count for {n}.")
        if any(not isinstance(signal.get(field), str) or not signal[field] for field in signal_fields):
            return result(name, "FAIL", f"Electrical behavior missing for {n}.")
        if n in active and (signal.get("voltage_domain") in (None, "none") or signal.get("direction") in (None, "undetermined", "excluded")):
            return result(name, "FAIL", f"Direction or voltage undefined for active signal {n}.")
        if n in active and (signal.get("source_board") not in {"board_a", "board_b"} or signal.get("destination_board") not in {"board_a", "board_b"} or signal["source_board"] == signal["destination_board"]):
            return result(name, "FAIL", f"Endpoint direction undefined for {n}.")
    if sum(s["required_count"] for s in signals) != architecture.get("interface_provisional_minimum_contacts"):
        return result(name, "FAIL", "Interface contact plan conflicts with architecture contract.")
    if architecture.get("interface_active_logical_classes") != len(active) or by_name["MCLK"]["required_count"] != 0:
        return result(name, "FAIL", "MCLK/inventory disposition conflicts with R3 audio path.")
    graph = architecture.get("dependency_graph", {})
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    if not graph.get("acyclic") or not isinstance(edges, list) or not edges:
        return result(name, "FAIL", "Missing dependency graph or acyclic assertion.")
    adjacent: dict[str, set[str]] = {}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or not all(isinstance(node, str) and node for node in edge):
            return result(name, "FAIL", "Malformed dependency edge.")
        adjacent.setdefault(edge[0], set()).add(edge[1])
        adjacent.setdefault(edge[1], set())
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(visit(next_node) for next_node in adjacent[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True
    if not all(visit(node) for node in adjacent):
        return result(name, "FAIL", "Startup dependency graph contains a cycle.")
    previous = state.get("previous_gate", {})
    if state.get("current_phase") not in {"R3", "R4"} or previous.get("phase") not in {"R2", "R3"} or previous.get("human_gate") != "APPROVED" or state.get("current_kicad_projects"):
        return result(name, "FAIL", "R3 state, human-gate approval or no-KiCad scope is incoherent.")
    if any(not HOOK_NAMES.get(h) for h in ("erc", "drc", "hierarchical_interface_audit", "pin_audit", "bom_validation")):
        return result(name, "FAIL", "Future KiCad hooks lost their NOT_AVAILABLE definitions.")
    return result(name, "PASS", "Board A/B ownership, audio clocks, B2B signal/electrical inventory and acyclic dependency graph verified; R4 circuit proofs remain open and KiCad hooks NOT_AVAILABLE.")


def r4_schematic_gate(root: Path, state: dict[str, Any]) -> dict[str, str]:
    """Strict R4 completion check. Parsing a contract is not electrical approval."""
    name = "r4_schematic_readiness"
    refs = (
        "docs/product_v1/phase_r4_schematic_readiness.md",
        "validation/r4_schematic_readiness_validation.md",
        "state/board_a_schematic_contract.json",
        "state/board_b_schematic_contract.json",
        "state/rt1062_pin_resource_map.json",
        "state/board_to_board_interface.json",
    )
    if any(not repo_path(root, ref).is_file() for ref in refs):
        return result(name, "BLOCKED", "At least one R4 report or machine contract is absent.")
    board_a = load_json(root, refs[2])
    board_b = load_json(root, refs[3])
    pins = load_json(root, refs[4])
    interface = load_json(root, refs[5])
    if board_a.get("board") != "board_a" or board_b.get("board") != "board_b":
        return result(name, "FAIL", "Board contract identity mismatch.")
    if board_a.get("interface") != refs[5] or board_b.get("interface") != refs[5]:
        return result(name, "FAIL", "Board contracts do not cite one interface.")
    allocations = pins.get("allocations", [])
    if not isinstance(allocations, list) or not allocations:
        return result(name, "BLOCKED", "RT1062 allocation list is absent.")
    for field in ("pad", "ball", "function", "io_bank", "mux"):
        if any(not isinstance(pin.get(field), str) or not pin[field] for pin in allocations):
            return result(name, "FAIL", f"RT1062 allocation lacks {field}.")
    for field in ("pad", "ball", "function"):
        values = [pin[field] for pin in allocations]
        if len(values) != len(set(values)):
            return result(name, "FAIL", f"Duplicate RT1062 {field} allocation.")
    reserved = {pin.get("pad") for pin in pins.get("reserved", [])}
    if reserved & {pin["pad"] for pin in allocations}:
        return result(name, "FAIL", "An RT1062 allocation overlaps a reserved boot/debug pad.")
    signals = interface.get("signals", [])
    names = [signal.get("signal") for signal in signals]
    if len(names) != len(set(names)):
        return result(name, "FAIL", "Duplicate board-interface signal.")
    expected_active = {"5V", "GND_RETURN", "BCLK", "LRCLK", "AUDIO_DATA", "I2C_SDA", "I2C_SCL", "AMP_MUTE", "AMP_FAULT", "PGOOD"}
    if set(names) != expected_active | {"MCLK", "REVISION_OR_SERVICE"}:
        return result(name, "FAIL", "R4 interface differs from the R3 signal inventory.")
    active = [s for s in signals if s.get("required_count", 0) > 0]
    if {s["signal"] for s in active} != expected_active or any(s.get("direction") in (None, "excluded", "undetermined") or not s.get("voltage_domain") or s.get("source_board") not in {"board_a", "board_b"} or s.get("destination_board") not in {"board_a", "board_b"} for s in active):
        return result(name, "FAIL", "Required cross-board direction or voltage domain is missing.")
    if any(s.get("required_count") != 0 for s in signals if s.get("signal") not in expected_active):
        return result(name, "FAIL", "An excluded interface signal gained a connector contact.")
    architecture = load_json(root, "state/product_v1_architecture_contract.json")
    graph = architecture.get("dependency_graph", {})
    edges = graph.get("edges", [])
    nodes = {node for edge in edges for node in edge}
    adjacent = {node: set() for node in nodes}
    for a, b in edges:
        adjacent[a].add(b)
    visiting: set[str] = set()
    visited: set[str] = set()
    def acyclic(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(acyclic(child) for child in adjacent[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True
    if not graph.get("acyclic") or not all(acyclic(node) for node in nodes):
        return result(name, "FAIL", "Startup dependency graph has a known cycle.")
    if state.get("current_phase") != "R4" or state.get("current_kicad_projects"):
        return result(name, "FAIL", "R4 phase or no-KiCad scope is incoherent.")
    if any(not HOOK_NAMES.get(h) for h in ("erc", "drc", "hierarchical_interface_audit", "pin_audit", "bom_validation")):
        return result(name, "FAIL", "Future KiCad hooks are not NOT_AVAILABLE.")
    incomplete = []
    for board in (board_a, board_b):
        if board.get("readiness") != "READY":
            incomplete.append(f"{board['board']} contract {board.get('readiness')}")
        for sheet in board.get("sheets", []):
            if sheet.get("status") not in {"READY", "READY_WITH_DOCUMENTED_PROVISION"}:
                incomplete.append(f"{board['board']} sheet {sheet.get('name')} {sheet.get('status')}")
            elif sheet["status"] == "READY_WITH_DOCUMENTED_PROVISION" and not sheet.get("provision"):
                incomplete.append(f"{board['board']} sheet {sheet.get('name')} lacks provision")
    if pins.get("status") != "READY" or pins.get("missing_r5_facts"):
        incomplete.append("RT1062 full pin/resource map")
    if any(item.get("status") != "READY" for item in pins.get("fixed_resources", [])):
        incomplete.append("RT1062 fixed USB/reference/reset resources")
    if board_a.get("microphone_afe", {}).get("status") != "READY" or board_a.get("power_tree", {}).get("load_budget_a") is None or any(rail.get("status") != "READY" or not rail.get("regulator_mpn") for rail in board_a.get("power_tree", {}).get("rails", []) if rail.get("name") != "RT1062_CORE_INTERNAL_DCDC"):
        incomplete.append("Board A analog/power guaranteed implementation")
    bparts = board_b.get("components", {})
    if any(not bparts.get(key, {}).get("mpn") for key in ("input_protection", "five_volt_buck", "logic_regulator")) or not board_b.get("power_tree", {}).get("input_envelope_v") or board_b.get("power_tree", {}).get("board_a_current_max_a") is None or not board_b.get("safety", {}).get("watchdog_mpn") or not board_b.get("safety", {}).get("pgood_thresholds"):
        incomplete.append("Board B protected power/safety guaranteed implementation")
    if any(s.get("r4_electrical", {}).get("r5_ready") is not True for s in active):
        incomplete.append("loaded board-interface DC/timing/off-domain proof")
    for signal in active:
        if signal["signal"] in {"5V", "GND_RETURN"}:
            continue
        proof = signal.get("r4_electrical", {})
        if any(not isinstance(proof.get(key), (int, float)) for key in ("source_voh_min_v", "source_vol_max_v", "receiver_vih_min_v", "receiver_vil_max_v", "receiver_abs_max_v", "high_margin_min_v", "low_margin_min_v")) or proof.get("power_off_isolation_proven") is not True:
            incomplete.append(f"{signal['signal']} DC/off-domain corner proof")
        if signal["signal"] in {"BCLK", "LRCLK", "AUDIO_DATA"} and not isinstance(proof.get("timing_margin_ns"), (int, float)):
            incomplete.append(f"{signal['signal']} timing margin")
    if incomplete:
        return result(name, "BLOCKED", "; ".join(incomplete))
    return result(name, "PASS", "R4 contracts, sheets, RT1062 allocation, interface and acyclic dependencies are complete; KiCad hooks remain NOT_AVAILABLE.")


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
                # Entry into the next phase is allowed while its own work is open.
                # Completion of that next phase evaluates blockers due there.
                checks.append(findings_gate(root, state, selected))
            elif gate == "product_architecture":
                checks.append(architecture_gate(root, state))
            elif gate == "r2_component_verification":
                checks.append(r2_component_gate(root, state))
            elif gate == "r3_system_architecture":
                checks.append(r3_system_gate(root, state))
            elif gate == "r4_schematic_readiness":
                checks.append(r4_schematic_gate(root, state))
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
