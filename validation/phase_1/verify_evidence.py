"""Reproduce Phase 1 document-integrity checks and engineering arithmetic.

Run from any working directory with Python + PyMuPDF installed.
This audit does not simulate hardware, certify symbols, or approve the phase.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import fitz


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'docs/phases/phase_1_component_datasheet_verification.md'
INDEX = ROOT / 'docs/evidence/component_evidence_index.md'
MANIFEST = OUT / 'source_manifest.json'


def main() -> int:
    results = {
        'executed_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version.split()[0],
        'pymupdf': fitz.VersionBind,
        'scope': 'Local source integrity, document consistency and arithmetic only',
        'checks': [],
    }

    def check(name: str, ok: bool, details) -> None:
        results['checks'].append({
            'name': name, 'status': 'PASS' if ok else 'FAIL', 'details': details,
        })

    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources = {item['id']: item for item in manifest}
    check('source_manifest_ids', len(sources) == len(manifest) == 16,
          sorted(sources))
    for item in manifest:
        path = ROOT / item['path']
        try:
            data = path.read_bytes()
            with fitz.open(path) as doc:
                pages = len(doc)
                identity = doc[0].get_text()
            digest = hashlib.sha256(data).hexdigest()
            ok = (data.startswith(b'%PDF-') and pages == item['pages']
                  and len(data) == item['bytes'] and digest == item['sha256']
                  and identity.startswith(item['identity_excerpt'])
                  and item['status'] == 'acquired')
            check('source_' + item['id'], ok, {
                'path': item['path'], 'pages': pages, 'bytes': len(data),
                'sha256': digest, 'identity_prefix_matches': identity.startswith(item['identity_excerpt']),
            })
        except Exception as exc:
            check('source_' + item['id'], False, str(exc))

    # Compare independent numerical and alphabetical lists in the same official
    # datasheet. Overbars, mux functions and footprint orientation are outside
    # this text-level comparison and still require future symbol review.
    ball = r'[A-HJ-NPRTUVWY](?:0[1-9]|1[0-9]|20)'
    with fitz.open(ROOT / sources['DSP']['path']) as doc:
        numerical_text = '\n'.join(doc[p].get_text(sort=True) for p in (88, 89, 90))
        alphabetical_text = '\n'.join(doc[p].get_text(sort=True) for p in (91, 92, 93))
    numerical = re.findall(r'\b(' + ball + r')\s+(\w+)', numerical_text)
    alphabetical = [(b, name) for name, b in re.findall(
        r'\b(\w+)\s+(' + ball + r')\b', alphabetical_text)]
    n_counts = Counter(b for b, _ in numerical)
    a_counts = Counter(b for b, _ in alphabetical)
    differences = sorted(set(numerical) ^ set(alphabetical))
    check('dsp_400_ball_dual_list',
          len(numerical) == len(alphabetical) == 400
          and len(n_counts) == len(a_counts) == 400
          and not differences,
          {'numerical_entries': len(numerical), 'alphabetical_entries': len(alphabetical),
           'unique_balls_numerical': len(n_counts), 'unique_balls_alphabetical': len(a_counts),
           'differences': differences,
           'boundary': 'Same-document text consistency; not independent package or symbol certification'})

    mapping = dict(numerical)
    expected = {
        'A08': 'SYS_BMODE2', 'B09': 'SYS_BMODE1', 'B10': 'SYS_BMODE0',
        'A09': 'SYS_HWRST', 'C10': 'SYS_RESOUT', 'A11': 'SYS_FAULT',
        'N01': 'SYS_CLKIN0', 'L01': 'SYS_XTAL0',
        'B11': 'JTG_TCK', 'C12': 'JTG_TMS', 'C13': 'JTG_TDI',
        'C11': 'JTG_TDO', 'A10': 'JTG_TRST',
        'R01': 'PA_04', 'N03': 'PA_00', 'P03': 'PA_01', 'T02': 'PA_05',
        'P02': 'PA_02', 'R03': 'PA_03', 'T03': 'PA_06', 'V01': 'PA_07',
    }
    check('dsp_boot_debug_base_signals', all(mapping.get(k) == v for k, v in expected.items()),
          {'expected': expected, 'boundary': 'Peripheral mux functions checked manually against signal tables'})

    fs = 96000
    clocks = {str(slots): {
        'sample_rate_hz': fs, 'slot_count': slots, 'slot_bits': 32,
        'bclk_hz': fs * slots * 32, 'frame_hz': fs,
        'period_ns': 1e9 / (fs * slots * 32),
        'half_period_ns_ideal_50_percent': 0.5e9 / (fs * slots * 32),
    } for slots in (4, 8)}
    half4 = clocks['4']['half_period_ns_ideal_50_percent']
    half8 = clocks['8']['half_period_ns_ideal_50_percent']
    latency = {
        'adc_typical_us': 22.9844 / fs * 1e6,
        'amplifier_us_from_12_frames': 12 / fs * 1e6,
        'sum_us_screening_only': (22.9844 + 12) / fs * 1e6,
    }
    margins = {
        'adc_to_external_sport_setup_ns_128fs': half4 - 18 - 2,
        'external_sport_fs_to_adc_setup_ns_128fs': half4 - 11 - 10,
        'external_sport_to_amp_setup_ns_128fs': half4 - 11 - 8,
        'external_sport_to_amp_setup_ns_256fs': half8 - 11 - 8,
        'dsp_voh_minus_adc_vih_at_3p6_v': 2.4 - 0.7 * 3.6,
        'dsp_voh_minus_amp_vih_at_3p5_v': 2.4 - 0.7 * 3.5,
        'dsp_voh_minus_receiver_vih_at_shared_3p47_v': 2.4 - 0.7 * 3.47,
        'receiver_max_voltage_at_zero_raw_high_margin': 2.4 / 0.7,
        'dsp_voh_minus_receiver_vih_at_3p3_plus_1_percent_v': 2.4 - 0.7 * 3.3 * 1.01,
        'boundary': 'Screening only; no load/skew/jitter/noise or hold closure; DSP external SPORT timing used',
    }
    workloads = []
    r, e, s = 2, 2, 4
    for taps in (64, 128, 256):
        macs = r * s * taps + r * s * e * (taps + taps)
        coefficients = 4 * (r * s * taps + s * e * taps)
        filtered_history = 4 * r * s * e * taps
        workloads.append({
            'assumptions': {'references': r, 'errors': e, 'outputs': s, 'Lw': taps, 'Ls': taps},
            'mac_equivalents_per_sample': macs,
            'mac_equivalents_per_second': macs * fs,
            'cycles_per_mac_equivalent_at_70_percent_of_1GHz': 0.7e9 / (macs * fs),
            'coefficient_bytes': coefficients,
            'filtered_history_bytes': filtered_history,
            'subtotal_KiB': (coefficients + filtered_history) / 1024,
        })
    results['calculations'] = {
        'clocks': clocks,
        'packed_4x24_bclk_hz_not_approved_amp_mode': fs * 4 * 24,
        'amp_512fs_mclk_hz_exceeds_25MHz': fs * 512,
        'latency': latency, 'interface_screening': margins,
        'microphone': {
            'normal_equivalent_input_noise_dBSPLA': 94 - 73,
            'low_power_equivalent_input_noise_dBSPLA': 94 - 71,
            'normal_noise_uVrmsA': 10 ** (-111 / 20) * 1e6,
            'signal_at_94dBSPL_mVrms': 10 ** (-38 / 20) * 1e3,
            'linear_extrapolation_at_135dBSPL_Vrms_not_clean_headroom': 10 ** ((-38 + 135 - 94) / 20),
        },
        'adc_input_referred_noise_uVrmsA_typical': 2 * 10 ** (-109 / 20) * 1e6,
        'workload_envelope_not_benchmarked': workloads,
        'cycles_per_sample': {'1GHz': 1e9 / fs, '800MHz': 0.8e9 / fs},
        'audio_dma_bytes_per_second_per_direction': 4 * 4 * fs,
        'audio_dma_bytes_per_second_both_directions': 2 * 4 * 4 * fs,
        'blocks': [{'frames': n, 'duration_us': n / fs * 1e6, 'duplex_pingpong_bytes': 64 * n}
                   for n in (1, 4, 8, 16, 32)],
        'dsp_core_mA_incomplete_worst_corner_subtotal':
            880 + 749 * 1.09 + 1.05 * (0.626 * 500 + 0.23 * 125 + 0.02 * 250),
        'ideal_unboosted_12V_4ohm_sine_ceiling_W_not_delivered_power': 12 ** 2 / (2 * 4),
        'adc_10uF_discharge_example': {
            '64k_only_seconds_to_0p48_from_1p8': 64000 * 10e-6 * math.log(1.8 / 0.48),
            'with_3k_bleeder_seconds': (1 / (1 / 64000 + 1 / 3000)) * 10e-6 * math.log(1.8 / 0.48),
            'bleeder_current_mA_at_1p8': 1.8 / 3000 * 1000,
            'boundary': 'Nominal RC example, not a guaranteed reset interval',
        },
    }
    check('calculation_landmarks',
          clocks['4']['bclk_hz'] == 12288000 and clocks['8']['bclk_hz'] == 24576000
          and math.isclose(latency['sum_us_screening_only'], 364.4208333333333)
          and [w['mac_equivalents_per_sample'] for w in workloads] == [2560, 5120, 10240],
          'Arithmetic reproduces report examples; no execution-throughput or hardware-margin test')

    report = REPORT.read_text(encoding='utf-8')
    phase0 = (ROOT / 'docs/phases/phase_0_requirements_freeze.md').read_text(encoding='utf-8')
    delta = report.split('## 14.', 1)[1].split('## 15.', 1)[0]
    before = re.findall(r'^\|\s*(U\d{2})\s*\|', phase0, re.M)
    after = re.findall(r'^\|\s*(U\d{2})\s*\|', delta, re.M)
    conflicts_before = re.findall(r'^\|\s*(X\d{2})\s*\|', phase0, re.M)
    conflicts_after = re.findall(r'^\|\s*(X\d{2})\s*\|', delta, re.M)
    check('phase0_unknown_and_conflict_row_coverage',
          len(before) == len(after) == 44 and Counter(before) == Counter(after)
          and len(conflicts_before) == len(conflicts_after) == 5
          and Counter(conflicts_before) == Counter(conflicts_after),
          {'unknown_ids': after, 'conditional_conflict_ids': conflicts_after,
           'boundary': 'Coverage only; classifications assessed in report'})
    matrix = report.split('## 16.', 1)[1].split('## 17.', 1)[0]
    decisions = re.findall(r'\*\*(APPROVED FOR ARCHITECTURE|PROVISIONALLY APPROVED|REJECTED|BLOCKED BY MISSING EVIDENCE)\*\*', matrix)
    check('four_component_recommendations',
          len(decisions) == 4 and Counter(decisions) == {
              'PROVISIONALLY APPROVED': 3, 'BLOCKED BY MISSING EVIDENCE': 1}, decisions)
    check('single_final_phase1_gate',
          re.findall(r'^PHASE 1: (?:PASS|BLOCKED)$', report, re.M) == ['PHASE 1: BLOCKED']
          and report.rstrip().endswith('PHASE 1: BLOCKED'), 'PHASE 1: BLOCKED')
    missing_links = []
    # Output JSON itself is about to be created and is a valid generated target.
    for document in (REPORT, INDEX):
        for target in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            if target.startswith(('https://', 'http://', '#')):
                continue
            linked = (document.parent / target.split('#', 1)[0]).resolve()
            if not linked.exists() and linked != (OUT / 'verification_results.json').resolve():
                missing_links.append({'document': str(document.relative_to(ROOT)), 'target': target})
    check('local_markdown_links', not missing_links, missing_links)
    hardware_files = [str(p.relative_to(ROOT)) for suffix in ('*.kicad_sch', '*.kicad_pcb', '*.kicad_sym', '*.kicad_mod', '*.kicad_pro')
                      for p in (ROOT / 'hardware/kicad').rglob(suffix)]
    check('no_phase1_kicad_artifacts', not hardware_files, hardware_files)
    results['not_executed'] = [
        'Hardware measurements', 'SPICE or IBIS simulation', 'Acoustic characterization',
        'DSP/FxLMS benchmark', 'Thermal simulation', 'Boot programming',
    ]
    results['erc_drc'] = 'NOT APPLICABLE: no KiCad hardware created or modified'
    results['engineering_phase_gate'] = 'PHASE 1: BLOCKED'
    failed = [entry['name'] for entry in results['checks'] if entry['status'] == 'FAIL']
    results['audit_status'] = 'FAIL' if failed else 'PASS'
    results['audit_status_meaning'] = 'Document/arithmetic audit only; does not supersede engineering phase gate'
    (OUT / 'verification_results.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Evidence audit: {results['audit_status']}; {len(results['checks'])} checks; failed: {failed}")
    print('Engineering gate remains PHASE 1: BLOCKED')
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
