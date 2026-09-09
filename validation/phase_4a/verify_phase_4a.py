"""Reproduce the blocked Phase 4A hierarchy/ERC check and PGOOD counterexample.

Run from any directory; optionally pass the path to kicad-cli.
This checks the intentionally unimplemented snapshot, not an electrical design.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
HW = ROOT / "hardware/kicad"
cli = sys.argv[1] if len(sys.argv) > 1 else shutil.which("kicad-cli")
if not cli:
    cli = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
project = HW / "circuitBuilderAi-Astra.kicad_sch"
files = sorted(HW.glob("*.kicad_sch"))
assert len(files) == 8, "Expected root and seven child sheets"
text = project.read_text(encoding="utf-8")
children = re.findall(r'\(property\s+"Sheetfile"\s+"([^"]+)"', text)
assert len(children) == len(set(children)) == 7
assert all((HW / child).is_file() for child in children)
for path in files:
    content = path.read_text(encoding="utf-8")
    assert not re.search(r'\((symbol|wire|hierarchical_label|global_label|label|pin)\s', content), path
    assert "4A-BLOCKED" in content
assert not list(HW.glob("*.kicad_pcb"))
json.loads((HW / "circuitBuilderAi-Astra.kicad_pro").read_text(encoding="utf-8"))
subprocess.run([cli, "sch", "erc", "--format", "json", "--severity-all",
                "--exit-code-violations", "--output", str(OUT / "erc.json"),
                str(project)], check=True)
erc = json.loads((OUT / "erc.json").read_text(encoding="utf-8"))
assert len(erc["sheets"]) == 8
assert not any(sheet["violations"] for sheet in erc["sheets"])

# Phase 3 sections 3.1/4.2/5.1; TI SLVSE94G pp.7-8,19.
# Same resistor/threshold bound as Phase 3; pin leakage is not included.
pg_fall_nom = 1.123 * (1 + 468 / 56)
pg_fall_max = 1.15 * (1 + (468 * 1.001) / (56 * 0.999))
protected_min = 10.8 - 0.4
out_efuse_only = 10.8 - 4 * 0.053
assert protected_min < pg_fall_nom < pg_fall_max
assert out_efuse_only < pg_fall_max
result = {
    "hierarchy_check": "PASS (placeholders only)",
    "erc": "PASS (zero violations; no circuit populated)",
    "schematic_files": [p.name for p in files],
    "components_added": 0,
    "pgood_falling_nominal_V": pg_fall_nom,
    "pgood_falling_upper_bound_V": pg_fall_max,
    "allowed_protected_rail_minimum_V": protected_min,
    "output_at_10V8_4A_53mohm_efuse_only_V": out_efuse_only,
    "other_path_drop_in_that_counterexample_V": 0,
    "threshold_bound_includes_pin_leakage": False,
    "engineering_gate": "PHASE 4A: BLOCKED",
}
(OUT / "verification_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
