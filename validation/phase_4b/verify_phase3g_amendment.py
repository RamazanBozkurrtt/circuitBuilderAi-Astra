"""Check the Phase 3G Sheet 2 amendment against native KiCad exports."""
from collections import Counter
from pathlib import Path
import json
import xml.etree.ElementTree as ET

import sexpdata as sx

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "validation/phase_4b/phase3g_amendment"
OLD = BASE / "validation/phase_4b/phase3f_completion"


def children(obj, key):
    return [x for x in obj if isinstance(x, list) and x and str(x[0]) == key]


def netlist(path):
    tree = ET.parse(path).getroot()
    values = {c.get("ref"): c.findtext("value") for c in tree.find("components")}
    pins = {(p.get("ref"), p.get("pin")): n.get("name").split("/")[-1]
            for n in tree.find("nets") for p in n.findall("node")}
    members = {n.get("name").split("/")[-1]: {(p.get("ref"), p.get("pin"))
               for p in n.findall("node")} for n in tree.find("nets")}
    return values, pins, members


def findings(path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    return sorted((v["severity"], v["type"],
                   tuple(i["uuid"] for i in v["items"]))
                  for s in obj["sheets"] for v in s["violations"])


checks = {}


def check(name, condition):
    checks[name] = bool(condition)


old_values, old_pins, _ = netlist(OLD / "sheet2_project.net.xml")
values, pins, members = netlist(OUT / "sheet2_project.net.xml")
check("TMUX1574 population", {r for r, v in values.items() if v == "TMUX1574PWR"} ==
      {"U240", "U241", "U242", "U243"})
check("TMUX2821 retained population", {r for r, v in values.items() if v == "TMUX2821DSGR"} ==
      {f"U{x}" for x in range(230, 240)})

for group, first in enumerate((1, 3)):
    ra, rb = f"U{240 + 2 * group}", f"U{241 + 2 * group}"
    check(f"group {group + 1} supply domains",
          pins[ra, "16"] == "2V8_MIC" and pins[rb, "16"] == "5V_AFE")
    for ref in (ra, rb):
        check(f"{ref} SEL EN ground", all(pins[ref, p] == "POWER_GND" for p in ("1", "15")))
        check(f"{ref} GND and spare sources", all(pins[ref, p] == "POWER_GND"
              for p in ("3", "6", "8", "10", "13")))
    for j, (src, drain) in enumerate(((2, 4), (5, 7), (11, 9), (14, 12))):
        ch, pol = first + j // 2, "PN"[j % 2]
        raw, mid, iso = (f"MIC{ch}_{pol}_{suffix}" for suffix in ("RAW", "MID", "ISO"))
        check(f"MIC{ch}_{pol} two-switch path", all((
            pins[ra, str(src)] == raw, pins[ra, str(drain)] == mid,
            pins[rb, str(src)] == mid, pins[rb, str(drain)] == iso)))
        check(f"MIC{ch}_{pol} no unintended component on isolation nets",
              members[mid] == {(ra, str(drain)), (rb, str(src))}
              and members[raw] == {(ra, str(src))}
              and members[iso] == {(rb, str(drain))})

for i, (ref, rail) in enumerate((("C360", "2V8_MIC"), ("C361", "5V_AFE"),
                                  ("C362", "2V8_MIC"), ("C363", "5V_AFE"))):
    check(f"{ref} bypass", values[ref] == "100n" and pins[ref, "1"] == rail
          and pins[ref, "2"] == "POWER_GND")

root = sx.loads((BASE / "hardware/kicad/circuitBuilderAi-Astra.kicad_sch").read_text(encoding="utf-8"))
sheet = sx.loads((BASE / "hardware/kicad/power_regulation.kicad_sch").read_text(encoding="utf-8"))
box = next(s for s in children(root, "sheet") if any(
    p[1] == "Sheetfile" and p[2] == "power_regulation.kicad_sch"
    for p in children(s, "property")))
root_ports = {p[1] for p in children(box, "pin")}
sheet_ports = {p[1] for p in children(sheet, "hierarchical_label")}
required = {f"MIC{ch}_{pol}_{edge}" for ch in range(1, 5)
            for pol in "PN" for edge in ("RAW", "ISO")}
check("all 16 microphone hierarchy ports", required <= root_ports and required <= sheet_ports)
check("no obsolete microphone ports", not any("AFTER_100R" in p or "BEFORE_4u7" in p
      for p in root_ports | sheet_ports))
check("Sheet 3 corrected AFE return ports", all(f"AFE{ch}_{pol}_RAW" in root_ports & sheet_ports
      for ch in range(1, 5) for pol in "PN"))
check("corrected VREF and ADC interface ports", all(x in root_ports & sheet_ports for x in
      ["ADC_VREF_RAW", "AFE_VCM_ISO"] + [f"ADC{ch}_{pol}_ISO" for ch in range(1, 5) for pol in "PN"]))

renames = {"ADC_VREF": "ADC_VREF_RAW", "AFE_VCM_INPUT": "AFE_VCM_ISO"}
for ch in range(1, 5):
    for pol in "PN":
        renames[f"AFE{ch}{pol}_AFTER_47R"] = f"AFE{ch}_{pol}_RAW"
        renames[f"ADC_AIN{ch}{pol}"] = f"ADC{ch}_{pol}_ISO"
unchanged = {key: old for key, old in old_pins.items()
             if key[0] not in {"U240", "U241", "U242", "U243", "C360", "C361", "C362", "C363"}}
check("all unrelated exported pin nets preserved", all(pins.get(key) == renames.get(old, old)
      for key, old in unchanged.items()))
old_findings = findings(OLD / "sheet2_erc_final.json")
new_findings = findings(OUT / "sheet2_erc.json")
check("ERC findings unchanged", new_findings == old_findings)
check("ERC baseline 3 errors and 5 warnings", Counter(f[0] for f in new_findings) ==
      {"error": 3, "warning": 5})

result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
          "unchanged_non_microphone_pins": len(unchanged),
          "erc": {"errors": 3, "warnings": 5, "new_findings": len(set(new_findings) - set(old_findings))},
          "manufacturer_pin_source": "TI TMUX1574 SCDS391C pp.3-6,24,26",
          "limits": "Physical signal/cable capacitance, leakage and rail-off tests await populated hardware."}
(OUT / "amendment_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
if result["status"] != "PASS":
    raise SystemExit(1)
