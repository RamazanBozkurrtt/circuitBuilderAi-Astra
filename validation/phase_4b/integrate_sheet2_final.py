"""Update only the hierarchy root's Sheet 2 interfaces; no later circuits."""
from pathlib import Path
import json,uuid
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware/kicad';OUT=ROOT/'validation/phase_4b/phase3f_completion'
S=sx.Symbol
def n(k,*v):return [S(k),*v]
def t(a,k):return next((x for x in a if isinstance(x,list) and str(x[0])==k),None)
def kids(a,k):return [x for x in a if isinstance(x,list) and str(x[0])==k]
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,'astra/phase4b/finalroot/'+k))
def fx():return n('effects',n('font',n('size',1.016,1.016)))
p=HW/'circuitBuilderAi-Astra.kicad_sch';a=sx.loads(p.read_text(encoding='utf-8'))
sh=next(x for x in kids(a,'sheet') if any(q[1]=='Sheetfile' and q[2]=='power_regulation.kicad_sch' for q in kids(x,'property')))
oldpoints=[t(pin,'at')[1:3] for pin in kids(sh,'pin')]
a[:]=[x for x in a if not(isinstance(x,list) and str(x[0])=='no_connect' and t(x,'at')[1:3] in oldpoints)]
# Remove only wires attached to this sheet's previous five power ports.
a[:]=[x for x in a if not(isinstance(x,list) and str(x[0])=='wire' and any(q[1:3] in oldpoints for q in kids(t(x,'pts'),'xy')))]
sh[:]=[x for x in sh if not(isinstance(x,list) and str(x[0])=='pin')]
t(a,'paper')[1]='A1';t(sh,'at')[1:3]=[450,65];t(sh,'size')[1:3]=[350,290]
for q in kids(sh,'property'):
    t(q,'at')[1:3]=[450,63 if q[1]=='Sheetname' else 357]
common={'12V_PROTECTED':70.08,'POWER_GND':73.89,'3V8_PRE':77.7,'PGOOD_12V':81.51,'EFUSE_FLT_N':85.32}
ports=json.loads((OUT/'sheet2_interfaces.json').read_text());left=right=0
for net,direction in ports.items():
    if net in common:
        x,y,ang=450,common[net],180
        a.append(n('wire',n('pts',n('xy',195,y),n('xy',450,y)),n('stroke',n('width',0),n('type',S('default'))),n('uuid',uid('wire'+net))))
    elif direction=='input':
        x,y,ang=450,round(100.33+left*5.08,2),180;left+=1
    else:
        x,y,ang=800,round(71.12+right*5.08,2),0;right+=1
    sh.append(n('pin',net,S(direction),n('at',x,y,ang),n('uuid',uid('pin'+net)),fx()))
    if net not in common:a.append(n('no_connect',n('at',x,y),n('uuid',uid('future'+net))))
for q in kids(a,'text'):
    if '4B BLOCKED - rails entered' in q[1]:
        q[1]='Sheet 2: Phase 3D/3E/3F implementation; validation record controls gate';t(q,'at')[1:3]=[450,48]
    elif 'Sheet 1: Phase 4A PASS. Sheet 2:' in q[1]:
        q[1]='Sheet 1: Phase 4A. Sheet 2: regulation / retained sequencing / bootstrap controls. Sheets 3-7: future endpoints.'
tb=t(a,'title_block');t(tb,'rev')[1]='4B'
for c in kids(tb,'comment'):
    if c[1]==1:c[2]='Sheet 2 Phase 3D/3E/3F controls. Later-sheet circuitry remains unimplemented.'
p.write_text(sx.dumps(a)+'\n',encoding='utf-8')
print('Sheet 2 ports integrated; future endpoints explicitly terminated; Sheet 1 untouched.')
