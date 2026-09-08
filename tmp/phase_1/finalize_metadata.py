from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[2]
manifest_path = root / 'validation/phase_1/source_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
metadata = {
    'MIC': ('IM73A135V01 datasheet', 'V1.20; 2021-07-07', 'pp.1-15: identity, acoustic/electrical tables, load network, pin/package and handling; revision history.'),
    'ADC': ('ADAU1978 datasheet', 'Rev.B; August 2024', 'pp.1-9: electrical/timing/pins; pp.12-23: reset, PLL, analog, filtering and serial interfaces; pp.26-42: relevant register fields; p.43 Fig.44; p.44 package/orderables.'),
    'DSP': ('ADSP-21562/3/5/6/7/9 datasheet', 'Rev.D; June 2023', 'pp.1-25: architecture, clocks, peripherals and boot; pp.26-43: signals; pp.44-58: rails, power, sequencing and SPORT timing; p.87 loading; pp.89-94: both 400-ball lists; pp.99-102: package/orderables.'),
    'AMP': ('TAS6424-Q1 datasheet, SLOS870B', 'Rev.B; October 2017; newer ordering addenda in current download', 'pp.1-10: identity, pins, limits, currents and timing; pp.18-26: formats/clocks/operating modes; pp.27-49: relevant control fields; pp.50-57: application, filters, power, thermal and layout; package addenda.'),
    'ANOM': ('ADSP-2156x Silicon Anomaly List, NR004735J', 'Rev.J; 2026-01-29', 'All 21 anomalies, pp.2-12; applicability to silicon 0.0/0.2, workarounds and revised DMC calibration.'),
    'POWER': ('EE-470: ADSP-2156x Power Sequencing Requirements', 'Rev.1; 2025-02-17', 'pp.1-14: rail differential restrictions, sequencing, ramp I/O behavior and example mitigation. No example power circuit adopted.'),
    'BOOT': ('EE-447: ADSP-2156x Processor Boot ROM', 'V01; 2023-05-11', 'Boot modes/streams, init code, boot customization and recovery implications; cross-checked against current silicon anomalies. No boot image implemented.'),
    'DSPPOWER': ('EE-414: Estimating Power for ADSP-2156x Processors', 'Rev.2; 2021-03-15', 'Core static/dynamic, activity factor, clock/DMA/accelerator and peripheral power models; especially pp.3-9. No selected full-system workload.'),
    'SOM': ('EV-21569-SOM Evaluation Board Manual', 'Rev.1.0; September 2020; 82-EV-21569-SOM-01', 'Functional blocks, power, boot/flash, clocks, reset, UART/JTAG and connectors; development example only.'),
    'SOMSCH': ('EV-21569-SOM schematic', 'Rev.A; title sheet 2020-01-29', 'Sheets 2-6: DSP/RAM/rails/decoupling; 7: clocks/boot; 8: SPI2 flash; 9: UART/JTAG; 10: reset; 11: power sequence. Targeted visual review of sheets 7,9,11.'),
    'ADCEVAL': ('UG-600: Evaluating ADAU1977/ADAU1978/ADAU1979', 'Rev.0; August 2014', 'pp.3-7: supply, jumpers and variant-specific analog coupling; pp.10-15: schematics (drawings identify ADAU1977). Do not transfer ADAU1977 boost/bias or 10 Vrms capabilities.'),
    'AMPEVAL': ('SLOU453A: TAS6424-Q1 Evaluation Module', 'Rev.A; October 2017', 'pp.1-3: operation/block diagram; pp.20-26: board layouts, schematics (22-23) and BOM. Exact TAS6424-Q1, not TAS6424L-Q1.'),
    'INDUCTOR': ('SLOA242A: Inductor Selection Guide for 2.1-MHz Class-D Amplifiers', 'Rev.A; September 2019', 'pp.1-8: saturation/current/inductance, losses and thermal selection considerations. No part/filter selected.'),
    'HRM': ('ADSP-2156x SHARC+ Processor Hardware Reference', 'Rev.1.1; October 2022; 82-100137-01', 'Targeted chapters: clock/reset, SRU/DAI, SPORT Ch.23 (especially 23-33 to 23-35; PDF1122-1124), PCG Ch.24 (24-1 to 24-9; PDF1189-1197), DMA and boot Ch.40. Not a cover-to-cover review of 2453 pages.'),
    'JTAG': ('EE-68: Analog Devices JTAG Emulation Technical Reference', 'Rev.10; 2008-04-15', 'p.6 target TRST practice and reference-interface discussion. Historical probes/14-pin examples do not validate a modern 10-pin header.'),
    'REF733': ('TIDA-00733: TIDUCZ2 design guide', 'December 2017', 'Targeted architecture and clock/audio implementation, sections 2.3.3-2.3.4, pp.18-23; power, thermal/EMI and test context. 96 kHz TDM8 reference, not this project circuit.'),
}
old = root / 'datasheets/dsp/ev-21569-som-schematic.pdf'
new = root / 'references/ev-21569-som/ev-21569-som-schematic.pdf'
new.parent.mkdir(parents=True, exist_ok=True)
if old.exists():
    if new.exists():
        raise RuntimeError('Refusing to overwrite an existing reference')
    old.rename(new)
for item in manifest:
    item['document_name'], item['document_revision_date'], item['review_scope'] = metadata[item['id']]
    if item['id'] == 'SOMSCH':
        item['path'] = new.relative_to(root).as_posix()
    if 'error' in item:
        item['initial_download_error'] = item.pop('error')
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

intro = '''# Component evidence index - Phase 1

Review: 2026-09-06 to 2026-09-07 (Europe/Istanbul). Electrical findings and their conditions are in the [Phase 1 report](../phases/phase_1_component_datasheet_verification.md). IDs below are the report's source keys. Page numbers are printed pages unless explicitly marked physical PDF pages.

Sixteen authoritative PDFs are stored locally. The [source manifest](../../validation/phase_1/source_manifest.json) records official requested/final URLs, acquisition UTC timestamps, byte counts, page counts, SHA-256 hashes, document identity excerpts and review scope. Initial download failures are retained separately from the successful final acquisition status. No unofficial mirrors were used. Manufacturer evaluation schematics remain external references, not production hardware.

| ID | Local authoritative copy / official source | Revision/date in document | Inspected region / boundary |
| --- | --- | --- | --- |
'''
rows = []
for item in manifest:
    name, revision, scope = metadata[item['id']]
    rows.append(f"| {item['id']} | [{name}](../../{item['path']}) · [Manufacturer PDF]({item['url']}) | {revision} | {scope} |")
tail = '''

## Official indexes and references located

These web indexes were checked on 2026-09-06. Lifecycle is a dated manufacturer statement, not an availability or procurement guarantee. Webpage summaries were not substituted for electrical tables.

| Index | Finding / limitation |
| --- | --- |
| [Infineon IM73A135](https://www.infineon.com/part/IM73A135) | Active/preferred; OPN IM73A135V01XTSA1, PG-LLGA-5-2. Official linked PDF is V1.20. |
| [Infineon microphone evaluation kit](https://www.infineon.com/evaluation-board/KIT-IM73A135V01-FLEX) | Five single-microphone flex boards and adapter. Separate electrical schematic/design package not acquired; product registration/access restrictions were not bypassed. |
| [ADI ADAU1978](https://www.analog.com/en/products/adau1978.html) | Production; Rev.B datasheet and UG-600 located. No separate official silicon errata found in reviewed index/search. |
| [ADI ADSP-21569](https://www.analog.com/en/products/adsp-21569.html) | Recommended for new designs; current family datasheet Rev.D, HRM, anomaly list and application notes located. Exact speed/temperature suffix remains a project choice. Older ADZS-21569-EZKIT is obsolete; EV-21569-SOM is the development reference reviewed. |
| [TI TAS6424-Q1](https://www.ti.com/product/TAS6424-Q1) | Active; linked SLOS870B acquired. TAS6424L-Q1 evaluation links are a different device and were not used to establish exact-variant limits. Exact TAS6424-Q1 EVM guide acquired separately. |
| [TI TIDA-00733](https://www.ti.com/tool/TIDA-00733) | Official design guide acquired and targeted sections reviewed. Demonstrates 96 kHz TDM8; does not repair the datasheet clock wording conflict. |
| [TI TIDA-00743](https://www.ti.com/tool/TIDA-00743) | Additional official reference located only. Its electrical design is not claimed as inspected or used to approve a device. |

## Revision and access limitations

- The DSP product index labels the anomaly document November 26, 2025, whereas the retrieved PDF is NR004735J dated January 29, 2026. PDF identity/revision controls this review.
- Product-index metadata for EE-414 is February 2020, while the PDF is Rev.2, March 15, 2021; EE-447 index metadata is June 28, 2023, while the PDF states May 11, 2023. SOM schematic index metadata is December 18, 2020; its title sheet states January 29, 2020. These discrepancies are retained rather than silently normalized.
- No standalone official IM73A135, ADAU1978 or TAS6424-Q1 silicon errata was located through the respective product indexes and targeted manufacturer-domain searches. This does not certify absence of errata. The current downloaded datasheet revision histories and relevant operating cautions were reviewed.
- ADC Table 4 versus p.14 HPF values, and TAS6424-Q1 sections 9.3.1.4 versus 9.3.1.5 clock instructions, remain **CONFLICTING**. Neither an evaluation board nor a forum reply overrides these statements.
- Critical PDF tables, pin maps, waveforms and selected reference diagrams were rendered and visually inspected with PyMuPDF. DSP numerical/alphabetical ball lists also underwent an automated 400-entry comparison. This is documentary consistency checking, not future KiCad symbol/footprint validation.
- No manufacturer was contacted, no private support result was invented, and no exhaustive review of the entire DSP manual is claimed.

## Reproduce the local audit

Requires Python with PyMuPDF (`fitz`). From repository root:

```powershell
python validation/phase_1/verify_evidence.py
```

The script checks local PDF hashes/page counts/identity, compares both DSP ball lists, calculates the stated interface/latency/workload/power examples, checks Phase 0 coverage and verifies report links and scope. Results are in [verification_results.json](../../validation/phase_1/verification_results.json). A passing evidence-integrity check does not change the engineering gate or establish hardware compatibility. The Phase 1 report is the gate authority for this task.
'''
out = root / 'docs/evidence/component_evidence_index.md'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(intro + '\n'.join(rows) + tail, encoding='utf-8')

report_path = root / 'docs/phases/phase_1_component_datasheet_verification.md'
report = report_path.read_text(encoding='utf-8')
report = report.replace('Review date: 2026-09-06', 'Review dates: 2026-09-06 to 2026-09-07 (Europe/Istanbul)')
report = report.replace('AMPEVAL SLOU453A pp.20-29', 'AMPEVAL SLOU453A pp.20-26 (schematics pp.22-23)')
# Restore spaces in prose without changing part numbers, register fields or URLs.
words = ['Phase', 'Table', 'Tables', 'Section', 'Sections', 'January', 'channel', 'channels', 'four', 'with', 'and', 'at', 'on', 'above', 'below', 'across', 'before', 'after', 'requires', 'required', 'all', 'the', 'small', 'typical', 'nominal', 'minimum', 'maximum', 'continuous', 'selected', 'documented', 'proposed', 'unsupported', 'Derived', 'derived', 'unboosted', 'Unboosted', 'old', 'modern', 'per', 'a', 'an', 'from', 'using', 'DSP', 'MIC', 'AMP', 'ADC', 'BGA', 'VDD_EXT']
pattern = r'\b(' + '|'.join(sorted(words, key=len, reverse=True)) + r')(?=\d)'
report = re.sub(pattern, r'\1 ', report)
report = re.sub(r'(?<=[,;])(?=[A-Za-z0-9])', ' ', report)
report = report.replace('Four-channel96', 'Four-channel 96').replace('32-bitwords', '32-bit words').replace('24-bituse', '24-bit use')
report = report.replace('SOM manual and Rev.A schematic', 'SOM manual and Rev.A schematic (especially sheets 7-11)')
report = report.replace('Power domains, 25 MHz source, SPI2 flash', 'Power domains, SI5356A clock generator with 25 MHz system and 24.576 MHz audio outputs, SPI2 flash')
report_path.write_text(report, encoding='utf-8')
print('Finalized manifest, evidence index and report presentation.')
