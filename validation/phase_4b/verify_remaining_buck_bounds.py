"""Check frozen pre/core feedback networks; does not approve revised rail ranges.

Evidence: TPS62135 SLVSBH3B Rev.B, section 7.5 p.6 and 10.1.1 p.13.
Same conservative +/-70 nA leakage treatment approved in Phase 3C.
Run: python validation/phase_4b/verify_remaining_buck_bounds.py
"""

from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "datasheets/power/tps62135_datasheet_rev_b.pdf"


def bounds(top, bottom):
    rt, rb = D(top), D(bottom)
    lo_zero = D("0.7") * D("0.99") * (1 + rt * D("0.999") / (rb * D("1.001")))
    hi_zero = D("0.7") * D("1.01") * (1 + rt * D("1.001") / (rb * D("0.999")))
    return {
        "top_ohm": rt,
        "bottom_ohm": rb,
        "minimum_V": lo_zero - D("70e-9") * rt * D("0.999"),
        "maximum_V": hi_zero + D("70e-9") * rt * D("1.001"),
        "minimum_at_zero_leakage_V": lo_zero,
    }


pre = bounds("442000", "100000")
core = bounds("42700", "100000")
core["approved_minimum_V"] = D("0.990")
core["approved_maximum_V"] = D("1.010")
core["approved_release_margin_mV"] = D("18.596")
# Copy the approved Phase 3B threshold; do not redesign or recalculate it.
core["approved_supervisor_rise_max_V"] = D("0.971404")
core["calculated_release_margin_mV"] = (core["minimum_V"] - D("0.971404")) * 1000
core["release_margin_preserved"] = core["calculated_release_margin_mV"] >= D("18.596")
pre["approved_minimum_V"] = D("3.762")
pre["approved_maximum_V"] = D("3.838")
pre["accuracy_headroom_extra_V"] = D("10.4") - pre["maximum_V"] - 1
core["accuracy_headroom_extra_V"] = pre["minimum_V"] - core["maximum_V"] - 1
for rail in (pre, core):
    rail["approved_output_band_preserved"] = (
        rail["minimum_V"] >= rail["approved_minimum_V"]
        and rail["maximum_V"] <= rail["approved_maximum_V"]
    )

result = {
    "gate": "BLOCKED",
    "scope": "Static feedback-network calculation only; no measured or transient result",
    "evidence": str(SOURCE.relative_to(ROOT)),
    "evidence_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
    "3V8_PRE": pre,
    "1V0_DSP_CORE": core,
}
output = Path(__file__).with_name("remaining_buck_bounds_results.json")
output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
print(output.read_text(encoding="utf-8"))
