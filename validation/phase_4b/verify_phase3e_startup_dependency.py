"""Check the exact pre-arm clock dependency; do not edit any KiCad file.

This is a bounded contract reachability check, not an electrical transient
simulation or a claim that Phase 3E circuitry has been implemented.
Also reload/resave a temporary project copy, run fresh ERC on the unchanged
production project, and compare its exported parts/nets with the prior entry.
"""
from pathlib import Path
from collections import deque
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HW = ROOT / 'hardware/kicad'
OUT = ROOT / 'validation/phase_4b/phase3e_resume'
OUT.mkdir(exist_ok=True)
CLI = Path(os.environ['LOCALAPPDATA']) / 'Programs/KiCad/10.0/bin/kicad-cli.exe'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hardware_hashes():
    return {str(p.relative_to(HW)): sha(p) for p in HW.rglob('*') if p.is_file()}


history = ROOT / 'validation/phase_4b_power_regulation_validation.md'
baseline_path = OUT / 'resume_baseline.json'
if not baseline_path.exists():
    baseline_path.write_text(json.dumps({
        'hardware': hardware_hashes(),
        'history_bytes': len(history.read_bytes()),
        'history_sha256': sha(history),
        'historical_artifacts': {p.name: sha(p) for p in OUT.parent.iterdir()
                                 if p.is_file() and p.name != Path(__file__).name},
    }, indent=2) + '\n')
baseline = json.loads(baseline_path.read_text())

# Check that the dependency cited by the model is actually in these contracts.
phase3 = (ROOT / 'docs/phases/phase_3_schematic_readiness.md').read_text(encoding='utf-8')
phase3d = (ROOT / 'docs/phases/phase_3d_final_power_contract_audit.md').read_text(encoding='utf-8')
phase3e = (ROOT / 'docs/phases/phase_3e_shutdown_safe_state_correction.md').read_text(encoding='utf-8')
assert 'poll PLL lock.' in phase3 and 'Then pulse `SAFE_ARM_CMD`' in phase3
assert 'successful PLL/configuration checks' in phase3d
assert 'after boot, rail/clock/ADC/amplifier checks' in phase3e
assert 'HW_RUN_LATCHED AND AUDIO_OE_CMD' in phase3e
assert 'Release audio and MCLK OEs only' in phase3e

# All rails, reset, source oscillator, and other prerequisites are granted good.
# State = (HW_RUN_LATCHED, PLL_check_passed). PLL check is allowed immediately
# whenever clocks are available: this is more permissive than real lock timing.
# Thus a failure here cannot be fixed by longer delays or faster hardware.
start = (False, False)
seen = {start}
queue = deque([start])
transitions = []
while queue:
    armed, checked = queue.popleft()
    for oe_cmd in (False, True):
        clocks = armed and oe_cmd
        candidates = [('wait_for_PLL', (armed, checked or clocks))]
        if checked:
            candidates.append(('permitted_SAFE_ARM_edge', (True, checked)))
        for action, target in candidates:
            transitions.append({'state': [armed, checked], 'AUDIO_OE_CMD': oe_cmd,
                                'MCLK_enabled': clocks, 'action': action,
                                'next_state': list(target)})
            if target not in seen:
                seen.add(target)
                queue.append(target)
assert seen == {(False, False)}

logs = []


def run(args):
    proc = subprocess.run([str(CLI), *map(str, args)], capture_output=True)
    record = {'command': [str(CLI), *map(str, args)], 'exit_code': proc.returncode,
              'stdout': proc.stdout.decode('utf-8', errors='replace'),
              'stderr': proc.stderr.decode('utf-8', errors='replace')}
    logs.append(record)
    assert proc.returncode == 0, record


with tempfile.TemporaryDirectory(prefix='astra-3e-blocker-') as tmp:
    staged = Path(tmp) / 'kicad'
    shutil.copytree(HW, staged)
    for name in ('power_regulation.kicad_sch', 'circuitBuilderAi-Astra.kicad_sch'):
        run(['sch', 'upgrade', '--force', staged / name])
# No saved copy is copied back: there is no approved schematic correction here.
run(['sch', 'erc', '--format', 'json', '--output', OUT / 'existing_sheet2_erc.json',
     HW / 'circuitBuilderAi-Astra.kicad_sch'])
run(['sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
     OUT / 'existing_project.net.xml', HW / 'circuitBuilderAi-Astra.kicad_sch'])

netlist = ET.parse(OUT / 'existing_project.net.xml').getroot()
components = {c.get('ref'): c for c in netlist.find('components')}
net_by_pin = {(n.get('ref'), n.get('pin')): net.get('name').rsplit('/', 1)[-1]
              for net in netlist.find('nets') for n in net.findall('node')}
manifest = json.loads((OUT.parent / 'sheet2_components.json').read_text())
checked_parts = 0
for ref, entry in manifest.items():
    if ref.startswith('#'):
        continue
    assert components[ref].findtext('value') == entry['value'], ref
    assert (components[ref].findtext('footprint') or '') == entry['footprint'], ref
    for pin, net in entry['nets'].items():
        if net is not None:
            assert net_by_pin.get((ref, pin)) == net, (ref, pin, net)
    checked_parts += 1

erc = json.loads((OUT / 'existing_sheet2_erc.json').read_text(encoding='utf-8'))
items = []
for sheet in erc['sheets']:
    for violation in sheet['violations']:
        desc = ' | '.join(i['description'] for i in violation['items'])
        if violation['type'] == 'pin_to_pin' and 'Pin 4 [FB2,' in desc:
            disposition = 'JUSTIFIED / INTENTIONAL'
            reason = ('Phase 3D section 8 requires FB2 grounded with VSEL low. '
                      'Existing ground power flag causes the output-type conflict. '
                      'No rule suppression or electrical change is appropriate.')
        elif violation['type'] == 'endpoint_off_grid' and sheet['path'] == '/':
            disposition = 'JUSTIFIED / INTENTIONAL'
            reason = ('Existing Sheet 1 hierarchy port geometry is retained. '
                      'Native netlist confirms continuity to Sheet 2.')
        else:
            disposition = 'BLOCKING'
            reason = 'Unrecognized finding; requires individual engineering review.'
        items.append({'sheet': sheet['path'], **violation,
                      'classification': disposition, 'reason': reason})

# Native ERC may create this local-preferences cache. Remove only that exact
# newly-created file, never a pre-existing project preference or design file.
local_preferences = HW / 'circuitBuilderAi-Astra.kicad_prl'
if local_preferences.name not in baseline['hardware'] and local_preferences.exists():
    local_preferences.unlink()
assert hardware_hashes() == baseline['hardware'], 'Hardware changed'
prefix = history.read_bytes()[:baseline['history_bytes']]
assert hashlib.sha256(prefix).hexdigest() == baseline['history_sha256']
assert all(sha(OUT.parent / name) == digest
           for name, digest in baseline['historical_artifacts'].items())

sources = ['docs/phases/phase_3_schematic_readiness.md',
           'docs/phases/phase_3d_final_power_contract_audit.md',
           'docs/phases/phase_3e_shutdown_safe_state_correction.md',
           'datasheets/adc/adau1978_datasheet_rev_b.pdf']
result = {
    'phase_gate': 'PHASE 4B: BLOCKED',
    'blocking_finding': 'MCLK release requires the safe latch armed; permitted arming requires prior ADC PLL verification.',
    'model_type': 'Necessary-condition contract reachability; not SPICE or physical timing validation',
    'reachable_states_armed_PLL_checked': [list(s) for s in sorted(seen)],
    'transitions': transitions,
    'startup_and_post_fault_rearm_reachable': False,
    'source_sha256': {name: sha(ROOT / name) for name in sources},
    'manufacturer_evidence': 'ADAU1978 Rev.B pp.12-14,29: stable PLL input clocks required; MCLK mode selected by contract; PLL_LOCK reset=0.',
    'prior_entry_parts_values_footprints_connected_pins_rechecked': checked_parts,
    'hardware_files_unchanged': True,
    'prior_history_and_artifacts_preserved': True,
    'new_schematic_implementation': 'NONE; stop before committing the conflicting OE-release circuit',
    'erc': {'errors': sum(v['severity'] == 'error' for v in items),
            'warnings': sum(v['severity'] == 'warning' for v in items),
            'blocking_items': sum(v['classification'] == 'BLOCKING' for v in items),
            'items': items, 'ignored_checks': erc['ignored_checks']},
    'native_tool_calls': logs,
}
(OUT / 'startup_dependency_results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('phase_gate', 'reachable_states_armed_PLL_checked',
                                       'prior_entry_parts_values_footprints_connected_pins_rechecked',
                                       'hardware_files_unchanged', 'prior_history_and_artifacts_preserved')}, indent=2))
print('Fresh ERC:', result['erc']['errors'], 'errors,', result['erc']['warnings'],
      'warnings;', result['erc']['blocking_items'], 'blocking ERC items.')
