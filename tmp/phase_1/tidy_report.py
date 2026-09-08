from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[2]
p = root / 'docs/phases/phase_1_component_datasheet_verification.md'
t = p.read_text(encoding='utf-8')
t = re.sub(r'(?<=\d), (?=\d{3}(?:\D|$))', ',', t)
t = t.replace('HRM Ch.23/28', 'HRM Ch.23/27 (DMA Table 27-2, p.27-4)')
t = t.replace('At ADC IOVDD minimum 3.0 V', 'For a constrained ADC IOVDD minimum of 3.0 V')
t = t.replace('PPM', 'PPM')
words = ['duration', 'period', 'half', 'slot', 'map', 'lower', 'near', 'is', 'by', 'hypothetical', 'only', 'ideal', 'independent', 'useful', 'Possible', 'or', 'amplifier', 'support', 'generic', 'be', 'different', 'one', 'divide', 'for', 'width', 'audio', 'shared', 'emits', 'mode', 'same', 'A', 'exact', 'default', 'gives', 'current', 'Illustrative', 'model', 'plus', 'Additional', 'least', 'Revision', 'Nominal', 'at', 'leakage', 'dynamic', 'terms', 'allowed', 'why', 'analog', 'share', 'selectable', 'a', 'all', 'revisions', 'around', 'SAP', 'Table', 'Tables', 'Section', 'Sections']
t = re.sub(r'\b(' + '|'.join(sorted(words, key=len, reverse=True)) + r')(?=\d)', r'\1 ', t)
t = t.replace('4 x32', '4 x 32').replace('8 x32', '8 x 32').replace('to23-', 'to 23-')
t = t.replace('fspacked', 'fs packed').replace('24-bitAMP', '24-bit AMP')
t = t.replace('HADC2.0', 'HADC 2.0').replace('VOH2.4', 'VOH 2.4').replace('VIH2.0', 'VIH 2.0').replace('VIH0.7', 'VIH 0.7')
t = t.replace('tDDTE11', 'tDDTE 11').replace('setup8', 'setup 8').replace('MCLK-mode10', 'MCLK-mode 10')
t = t.replace('96-kHz8', '96-kHz 8').replace('ASIC', 'ASIC')
needle = 'No listed anomaly was found that categorically prohibits'
note = ('**Additional DSP documentation inconsistency:** DSP p.17 describes eight SPORTs and HRM Table 27-2 lists SPORT0 through SPORT7 DMA channels, but DSP Tables 36-37 (pp.57-58) footnotes say their specifications apply to four SPORTs. The scope of those timing guarantees across all eight is **CONFLICTING/UNKNOWN**. The current resource example uses SPORT0A/B; no additional high-numbered SPORT is needed or approved. Obtain clarification before extending the timing contract to SPORT4-7.\n\n')
t = t.replace(needle, note + needle)
p.write_text(t, encoding='utf-8')

idx = root / 'docs/evidence/component_evidence_index.md'
s = idx.read_text(encoding='utf-8').replace('DMA and boot Ch.40', 'DMA Ch.27 (especially 27-1 to 27-4; PDF1296-1299) and boot Ch.40')
s = s.replace('- No manufacturer was contacted', '- DSP Tables 36-37 footnotes refer to four SPORTs, while the feature description and HRM DMA list establish eight. Timing-guarantee scope for additional SPORTs remains unresolved; the report uses SPORT0.\n- No manufacturer was contacted')
idx.write_text(s, encoding='utf-8')
m = root / 'validation/phase_1/source_manifest.json'
items = json.loads(m.read_text(encoding='utf-8'))
for item in items:
    if item['id'] == 'HRM':
        item['review_scope'] = item['review_scope'].replace('DMA and boot Ch.40', 'DMA Ch.27 (especially 27-1 to 27-4; PDF1296-1299) and boot Ch.40')
m.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Updated citations, source conflict note and prose spacing.')
