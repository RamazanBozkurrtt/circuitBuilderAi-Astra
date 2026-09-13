"""Connect existing Sheet 1 ports to Sheet 2 at the hierarchy root only.

Sheet 1 itself is never opened for editing. Future-sheet ports are explicitly
terminated at the root; later circuitry remains unimplemented.
"""
from pathlib import Path
import uuid
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'hardware/kicad/circuitBuilderAi-Astra.kicad_sch'
S=sx.Symbol
def n(k,*v):return [S(k),*v]
def child(a,k):return next((x for x in a if isinstance(x,list) and x and str(x[0])==k),None)
def children(a,k):return [x for x in a if isinstance(x,list) and x and str(x[0])==k]
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,'astra/phase4b/root/'+k))
def fx():return n('effects',n('font',n('size',1.016,1.016)))
a=sx.loads(p.read_text(encoding='utf-8'))
sheet=next(x for x in children(a,'sheet') if any(q[1]=='Sheetfile' and q[2]=='power_regulation.kicad_sch' for q in children(x,'property')))
assert not children(sheet,'pin'),'Run integration once; do not duplicate ports'
child(sheet,'size')[2]=38.1
for q in children(sheet,'property'):
    if q[1]=='Sheetfile':child(q,'at')[2]=104.6
for x in children(a,'text'):
    if x[1]=='PLACEHOLDER - not implemented in Phase 4A' and child(x,'at')[1:3]==[230,80]:
        x[1]='4B BLOCKED - rails entered; safe-state / shutdown incomplete'
        child(x,'at')[1:3]=[225,56]
    elif x[1].startswith('PHASE 4A - Sheet 1 implemented'):
        x[1]='Sheet 1: Phase 4A PASS. Sheet 2: Phase 4B BLOCKED, partial entry. Sheets 3-7: placeholders.'
    elif x[1].startswith('Sheet 1 interfaces terminate'):
        x[1]='Sheet 1 / Sheet 2 power interfaces connected. Future consumer interfaces terminate here. No PCB.'
tb=child(a,'title_block');child(tb,'rev')[1]='4B-BLOCKED'
for c in children(tb,'comment'):
    if c[1]==1:c[2]='Sheet 2 partially entered; Phase 4B BLOCKED. Later circuitry remains unimplemented.'
common=[('12V_PROTECTED','input',70.08),('POWER_GND','passive',73.89),('3V8_PRE','output',77.7),('PGOOD_12V','input',81.51),('EFUSE_FLT_N','input',85.32)]
for net,d,y in common:
    sheet.append(n('pin',net,S(d),n('at',225,y,180),n('uuid',uid('pin'+net)),fx()))
    a[:]=[x for x in a if not (isinstance(x,list) and str(x[0])=='no_connect' and child(x,'at')[1:]==[195,y])]
    a.append(n('wire',n('pts',n('xy',195,y),n('xy',225,y)),n('stroke',n('width',0),n('type',S('default'))),n('uuid',uid('wire'+net))))
for i,net in enumerate(['DSP_WDI','AFE_EN_CMD']):
    y=round(89.13+i*3.81,2)
    sheet.append(n('pin',net,S('input'),n('at',225,y,180),n('uuid',uid('pin'+net)),fx()))
    a.append(n('no_connect',n('at',225,y),n('uuid',uid('future'+net))))
for i,net in enumerate(['1V8_DSP_REF_ANA','1V0_DSP_CORE','1V35_DSP_DMC','3V3_SYS','3V3_ADC_A','2V8_MIC','5V_AFE','RAILS_OK','SYS_HWRST']):
    y=round(70.08+i*3.81,2)
    sheet.append(n('pin',net,S('bidirectional' if net=='SYS_HWRST' else 'output'),n('at',395,y,0),n('uuid',uid('pin'+net)),fx()))
    a.append(n('no_connect',n('at',395,y),n('uuid',uid('future'+net))))
p.write_text(sx.dumps(a)+'\n',encoding='utf-8')
print('Root hierarchy connected; Sheet 1 file untouched; future interfaces terminated.')
