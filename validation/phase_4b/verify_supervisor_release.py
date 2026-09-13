"""Reproduce the Phase 4B blocking supervisor threshold check; no circuit edits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "datasheets/power/tps386000_datasheet_rev_f.pdf"
EXPECTED_SHA256 = "02e788626e1d8d546ada465dc63703635834e41ee109d6c9fc6970a26fb62e98"


def main():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError("Supervisor evidence differs from the approved evidence index")
    # Phase 3 section 6.1 minima; deliberately do not reduce these further
    # for regulator feedback-resistor, feedback-current, ripple or trace losses.
    rails = [
        ("1V8_DSP_REF_ANA", "SENSE1", 33800, 1.775),
        ("1V0_DSP_CORE", "SENSE2", 14300, 0.990),
        ("1V35_DSP_DMC", "SENSE3", 22500, 1.325),
        ("3V3_SYS", "SENSE4L", 69800, 3.267),
    ]
    results = []
    for name, channel, rt, rail_min in rails:
        rt_hi, rb_lo = rt * 1.001, 10000 * 0.999
        ratio = 1 + rt_hi / rb_lo
        # TI SBVS105F p.7: VITN max 404 mV, VHYSN max 10 mV.
        # Figure 3 p.9 and section 8.3.4 p.23 establish rising behavior.
        rise_zero_leakage = (0.404 + 0.010) * ratio
        # Additional screen with p.7 +/-25 nA ISENSE (specified at 0.42 V).
        rise_leakage_screen = rise_zero_leakage + 25e-9 * rt_hi
        results.append({
            "rail": name,
            "channel": channel,
            "top_ohm_nominal": rt,
            "bottom_ohm_nominal": 10000,
            "phase3_rail_min_V": rail_min,
            "fall_max_zero_leakage_V": 0.404 * ratio,
            "rise_max_zero_leakage_V": rise_zero_leakage,
            "release_margin_zero_leakage_V": rail_min - rise_zero_leakage,
            "rise_max_with_25nA_screen_V": rise_leakage_screen,
            "guaranteed_release": rail_min > rise_zero_leakage,
        })
    report = {
        "source": str(SOURCE.relative_to(ROOT)),
        "sha256": digest,
        "source_identity": "TI TPS386000/TPS386040, SBVS105F, October 2018",
        "scope": "Static guaranteed-release screen, not simulation or bench validation",
        "results": results,
        "gate": "PHASE 4B: PASS" if all(r["guaranteed_release"] for r in results) else "PHASE 4B: BLOCKED",
    }
    output = Path(__file__).with_name("supervisor_release_results.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
