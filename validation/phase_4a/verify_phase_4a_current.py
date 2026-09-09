"""Independent Sheet 1 net/pin/corner audit and actual KiCad ERC + ngspice run.

Usage: python validation/phase_4a/verify_phase_4a_current.py [kicad-cli] [ngspice]
Requires sexpdata. Original empty-hierarchy verification is preserved separately.
"""
from pathlib import Path
import csv
import hashlib
import itertools as it
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import sexpdata as sx

ROOT = Path(__file__).resolve().parents[2]
VAL = ROOT / 'validation/phase_4a'
HW = ROOT / 'hardware/kicad'
CLI = sys.argv[1] if len(sys.argv)>1 else 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
SPICE = sys.argv[2] if len(sys.argv)>2 else 'C:/Spice64/bin/ngspice_con.exe'
SCH = HW / 'circuitBuilderAi-Astra.kicad_sch'
def run(*args, cwd=ROOT):
    return subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True, check=True).stdout
def key(x): return str(x[0]) if isinstance(x,list) and x else ''
def children(x,k): return [a for a in x if key(a)==k]
def one(x,k): return children(x,k)[0]
def read(p): return sx.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
results = {}

# These two files are opened and resaved by KiCad, not merely a text parser.
for p in [SCH,HW/'power_input.kicad_sch']:
    run(CLI,'sch','upgrade','--force',p)
run(CLI,'sch','erc','--format','json','--severity-all','--exit-code-violations','--output',VAL/'erc_current.json',SCH)
erc=json.loads((VAL/'erc_current.json').read_text())
assert len(erc['sheets'])==8
assert not any(s['violations'] for s in erc['sheets'])
results['ERC']={'version':erc['kicad_version'],'sheets':8,'violations':0,'ignored_checks':erc['ignored_checks']}
run(CLI,'sch','export','netlist','--format','kicadxml','--output',VAL/'power_input.net.xml',SCH)
run(CLI,'sch','export','svg','--output',VAL/'rendered_current',SCH)

baseline=json.loads((VAL/'later_sheet_hashes.json').read_text())
assert len(baseline)==6
for file,digest in baseline.items():
    p=HW/file
    assert sha(p)==digest, file+' changed outside scope'
    assert not children(read(p),'symbol'), file+' contains circuitry'
assert not list(HW.glob('*.kicad_pcb'))
root=read(SCH)
assert len(children(root,'sheet'))==7
results['scope']='Existing hierarchy reused; six later sheets byte-identical; no PCB'

# Hand-entered connection contract, independent of authoring coordinates.
expected={
 '12V_IN':'F1.1 J1.1 TP5.1',
 'IN_SYS':'C1.1 D1.1 F1.2 Q1.1 Q1.2 Q1.3 Q2.2 R1.1 U1.5',
 'EFUSE_IN':'C2.1 Q1.5 U1.1 U1.2',
 'B_GATE':'Q1.4 Q2.3 U1.3', 'DRV':'Q2.1 U1.4',
 '12V_PROTECTED':'C3.1 C4.1 C6.1 R5.1 TP1.1 U1.17 U1.18 U2.1',
 'UVLO_SET':'R1.2 R2.1 U1.6', 'OVP_SET':'R2.2 R3.1 U1.7',
 'PGOOD_SENSE':'R5.2 R6.1 TP2.1 U2.3',
 'PGOOD_12V':'R7.2 TP3.1 U2.6', '3V8_PRE':'R7.1',
 'EFUSE_FLT_N':'TP4.1 U1.14',
 'POWER_GND':'C1.2 C2.2 C3.2 C4.2 C5.2 C6.2 D1.2 J1.2 R3.2 R4.2 R6.2 TP6.1 U1.15 U1.25 U1.8 U2.13 U2.8',
 'Net-(U1-ILIM)':'R4.1 U1.10', 'Net-(U1-dVdT)':'C5.1 U1.9'}
xml=ET.parse(VAL/'power_input.net.xml')
nets={n.get('name').removeprefix('/1 - Power Input / Protection/'):set(x.get('ref')+'.'+x.get('pin') for x in n) for n in xml.findall('./nets/net')}
for name,nodes in expected.items(): assert nets[name]==set(nodes.split()), (name,nets[name])
nc_expected={f'U1.{p}' for p in [11,12,13,16,19,20,21,22,23,24]}|{f'U2.{p}' for p in [2,4,5,7,9,10,11,12,14]}
nc_actual=set().union(*(v for k,v in nets.items() if k.startswith('unconnected-')))
assert nc_actual==nc_expected
assert len(nets)==len(expected)+len(nc_expected)

# Official pin tables: TPS2663 p3, TPS3760 p4, CSD19537Q3 p1 drawing,
# onsemi BSS138LT1 p7 CASE318 style21. Q1 common drain pad5 = physical5-8/EP.
pinmaps={
 'TPS26630RGER':dict(enumerate(['IN','IN','B_GATE','DRV','IN_SYS','UVLO','OVP','GND','dVdT','ILIM','MODE','~{SHDN}','IMON','~{FLT}','PGTH','PGOOD_NATIVE','OUT','OUT','NC','NC','NC','NC','NC','NC','EP_GND'],1)),
 'TPS3760A012DYYR':dict(enumerate(['VDD','NC','SENSE','NC','NC','~{RESET}','NC','GND','CTR/~{MR}','CTS','NC','NC','GND','NC'],1)),
 'CSD19537Q3':{1:'S',2:'S',3:'S',4:'G',5:'D'},
 'BSS138LT1G':{1:'G',2:'S',3:'D'}, 'Power_Input_2pin':{1:'+',2:'-'}}
library={s[1]:s for s in children(read(HW/'Astra_Power.kicad_sym'),'symbol')}
sheet=read(HW/'power_input.kicad_sch')
cached={s[1].split(':')[-1]:s for s in children(one(sheet,'lib_symbols'),'symbol')}
def pins(symbol):
    return {int(one(p,'number')[1]):one(p,'name')[1] for u in children(symbol,'symbol') for p in children(u,'pin')}
for name,mapping in pinmaps.items():
    assert pins(library[name])==mapping
    assert pins(cached[name])==mapping
for name in ['R','C','C_Polarized','Fuse','D_TVS']:
    assert set(pins(library[name]))=={1,2}
    assert pins(library[name])==pins(cached[name])
assert pins(library['TestPoint'])=={1:'1'}
ports={'12V_PROTECTED':'output','POWER_GND':'passive','3V8_PRE':'input','PGOOD_12V':'output','EFUSE_FLT_N':'output'}
assert {s[1]:str(one(s,'shape')[1]) for s in children(sheet,'hierarchical_label')}==ports
power_sheet=next(s for s in children(root,'sheet') if any(p[1:3]==['Sheetfile','power_input.kicad_sch'] for p in children(s,'property')))
assert {p[1]:str(p[2]) for p in children(power_sheet,'pin')}==ports
results['net_and_symbol_audit']='PASS: all 15 connected nets, 19 intentional NC pins, critical pin maps and five hierarchical ports'

def limits(values):
    v=list(values); return {'min':min(v),'max':max(v)}
pgfall=[];pgrise=[];hysteresis=[]
for rt,rb,vs,leak,hy in it.product([115e3*.999,115e3*1.001],[10e3*.999,10e3*1.001],[.792,.808],[-100e-9,100e-9],[.016*.985,.016*1.015]):
    pgfall.append(vs*(1+rt/rb)+leak*rt)
    pgrise.append((vs+hy)*(1+rt/rb)+leak*rt)
    hysteresis.append(hy*(1+rt/rb))
bounds={'PGOOD_fall':limits(pgfall),'PGOOD_rise':limits(pgrise),'PGOOD_hysteresis':limits(hysteresis)}
for function in ['UVLO','OVP']:
    for direction,vsrange in [('rise',[1.176,1.224]),('fall',[1.09,1.15])]:
        values=[]
        for r1,r2,r3,iu,io,vs in it.product([316e3*.999,316e3*1.001],[13.3e3*.999,13.3e3*1.001],[30.4e3*.999,30.4e3*1.001],[-150e-9,150e-9],[-150e-9,150e-9],vsrange):
            if function=='UVLO':
                vu=vs; vo=(vu/r2-io)/(1/r2+1/r3)
            else:
                vo=vs; vu=vo+r2*(vo/r3+io)
            values.append(vu+r1*((vu-vo)/r2+iu))
        bounds[function+'_'+direction]=limits(values)
for name,expected_bound in {'PGOOD_fall':[9.870,10.130],'PGOOD_rise':[10.067,10.333],'PGOOD_hysteresis':[.197,.203],'UVLO_rise':[9.583,10.173],'UVLO_fall':[8.876,9.563],'OVP_rise':[13.793,14.606],'OVP_fall':[12.777,13.729]}.items():
    assert all(abs(bounds[name][k]-e)<.00051 for k,e in zip(['min','max'],expected_bound)), (name,bounds[name])
results['threshold_bounds_V']=bounds
results['margins_V']={'normal_hold':10.4-max(pgfall),'normal_assert':10.4-max(pgrise),'before_UVLO':min(pgfall)-bounds['UVLO_fall']['max'],'OVP_above_normal':bounds['OVP_rise']['min']-13.2}
assert min(results['margins_V'].values())>0
results['ILIM_A']={'nominal':18e3/3240,'min':18e3/(3240*1.001)*.93,'max':18e3/(3240*.999)*1.07}

# Run in a temporary directory: preserve a compact trace, not a large raw dump.
with tempfile.TemporaryDirectory(prefix='astra_phase4a_') as td:
    run(SPICE,'-b','-o',VAL/'transient.log',VAL/'power_input_transient.cir',cwd=td)
    rows=[[float(x) for x in line.split()] for line in (Path(td)/'transient_waveforms.txt').read_text().splitlines()[1:]]
assert len(rows)>1000
def edges(column,rising=True):
    return [b for a,b in zip(rows,rows[1:]) if (a[column]<1<=b[column] if rising else a[column]>=1>b[column])]
events={}
for col,name in [(4,'nominal'),(5,'high_bound'),(6,'low_bound')]:
    ups=edges(col);downs=edges(col,False)
    assert len(ups)==2 and len(downs)==1,(name,len(ups),len(downs))
    assert ups[0][0]<.3 and ups[1][0]>1.55
    assert all(r[col]>3.7 for r in rows if .34<r[0]<.43)
    events[name]={'assert_s':[r[0] for r in ups],'deassert_s':downs[0][0],'deassert_protected_V':downs[0][2]}
uvfalls=[b for a,b in zip(rows,rows[1:]) if a[7]>.5>=b[7]]
assert len(uvfalls)==1
assert events['low_bound']['deassert_s']<uvfalls[0][0]
assert abs(min(r[2] for r in rows if .34<r[0]<.43)-10.4)<.001
slopes=[(b[2]-a[2])/(b[0]-a[0]) for a,b in zip(rows,rows[1:]) if a[0]>1.55 and 2<a[2]<9]
assert 1060<max(slopes)<1070
results['transient']={'simulator':'ngspice-47','scope':'Behavioral contract fixture; ideal threshold switches and imposed dVdT slew, not a silicon/PVT model or implemented downstream latch','events':events,'UVLO_open_s':uvfalls[0][0],'recovery_max_slew_V_per_s':max(slopes),'normal_hold_min_V':min(r[2] for r in rows if .34<r[0]<.43)}
keep={0,len(rows)-1}|set(range(0,len(rows),10))
for i,(a,b) in enumerate(zip(rows,rows[1:])):
    if any((a[c]>1)!=(b[c]>1) for c in [4,5,6,8]) or (a[7]>.5)!=(b[7]>.5):keep.update([i,i+1])
with (VAL/'transient_trace.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['time_s','IN_SYS_V','protected_V','sense_V','PG_nom_V','PG_high_V','PG_low_V','UVLO_enabled','safe_request']);w.writerows(rows[i] for i in sorted(keep))
results['artifact_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in [SCH,HW/'power_input.kicad_sch',HW/'Astra_Power.kicad_sym',HW/'sym-lib-table',VAL/'power_input_transient.cir']}
(VAL/'verification_current.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
