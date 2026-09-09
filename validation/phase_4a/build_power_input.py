"""Build only the existing Sheet 1 and its root interface; KiCad CLI resaves it.

Requires sexpdata. No later sheet or board is authored. Pin audit is independent
in verify_phase_4a_current.py. UUIDs of the existing root, child and hierarchy are retained.
"""
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from copy import deepcopy
import hashlib
import json
import math
import sexpdata as sx

ROOT = Path(__file__).resolve().parents[2]
HW = ROOT / 'hardware/kicad'
VAL = ROOT / 'validation/phase_4a'
LIBS = Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
S = sx.Symbol
def key(x): return str(x[0]) if isinstance(x,list) and x else ''
def one(x,k): return next(a for a in x if key(a)==k)
def all_(x,k): return [a for a in x if key(a)==k]
def parse(s): return sx.loads(s)
def uid(s): return str(uuid5(NAMESPACE_URL,'circuitBuilderAi-Astra/phase4a/'+s))
def q(s): return json.dumps(s)
def f(n): return round(n,5)
def write(path,obj): path.write_text(sx.dumps(obj)+'\n',encoding='utf-8')
def effects(size=1.27,justify='left',hide=False):
 return parse(f'(effects (font (size {size} {size}))'+(f' (justify {justify})' if justify else '')+(' (hide yes)' if hide else '')+')')
def prop(name,value,x=0,y=0,hide=False,size=1.27):
 return [S('property'),name,value,[S('at'),f(x),f(y),0],effects(size,'left',hide)]

root = sx.loads((HW/'circuitBuilderAi-Astra.kicad_sch').read_text(encoding='utf-8'))
old = sx.loads((HW/'power_input.kicad_sch').read_text(encoding='utf-8'))
rootid=one(root,'uuid')[1]; childid=one(old,'uuid')[1]
sheet=next(a for a in all_(root,'sheet') if any(p[1:3]==['Sheetfile','power_input.kicad_sch'] for p in all_(a,'property')))
sheetid=one(sheet,'uuid')[1]
baseline=VAL/'later_sheet_hashes.json'
if not baseline.exists():
 baseline.write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HW.glob('*.kicad_sch') if p.name not in ['power_input.kicad_sch','circuitBuilderAi-Astra.kicad_sch']},indent=2)+'\n')

cache={}; library={}
def stock(file,name,newname=None):
 if file not in cache:
  cache[file]={a[1]:a for a in sx.loads((LIBS/(file+'.kicad_sym')).read_text(encoding='utf-8')) if key(a)=='symbol'}
 data=deepcopy(cache[file][name]); ext=all_(data,'extends')
 if ext:
  parent=deepcopy(cache[file][ext[0][1]])
  data=[a for a in data if key(a)!='extends']
  present={a[1] for a in all_(data,'property')}
  data.extend(a for a in parent[2:] if key(a)!='property' or a[1] not in present)
 newname=newname or name
 data[1]=newname
 for a in all_(data,'symbol'): a[1]=newname+'_'+a[1].rsplit('_',2)[-2]+'_'+a[1].rsplit('_',1)[-1]
 data=[a for a in data if not (key(a)=='property' and a[1] in ['ki_keywords','ki_fp_filters'])]
 library[newname]=data
 return data

for n in ['R','C','C_Polarized','Fuse','D_TVS']: stock('Device',n)
stock('Connector','TestPoint'); stock('power','PWR_FLAG')
stock('Transistor_FET','BSS138','BSS138LT1G')
stock('Transistor_FET','CSD19537Q3')

def ic(name,pins,w,h):
 data=parse(f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes))')
 data += [prop('Reference','U'),prop('Value',name),prop('Footprint','',hide=True),prop('Datasheet','',hide=True)]
 data.append(parse(f'(symbol "{name}_0_1" (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background))))'))
 unit=[S('symbol'),name+'_1_1']
 for num,pname,typ,x,y,angle in pins:
  unit.append(parse(f'(pin {typ} line (at {x} {y} {angle}) (length 5.08) (name {q(pname)} (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))'))
 data.append(unit);library[name]=data

# Coordinates are symbol-local; pin numbers verified against official drawings.
pins1=[(1,'IN','power_in',-25.4,35.56,0),(2,'IN','power_in',-25.4,30.48,0),
 (5,'IN_SYS','power_in',-25.4,20.32,0),(3,'B_GATE','output',-25.4,10.16,0),
 (4,'DRV','output',-25.4,0,0),(6,'UVLO','input',-25.4,-15.24,0),(7,'OVP','input',-25.4,-30.48,0),
 (17,'OUT','power_out',25.4,35.56,180),(18,'OUT','passive',25.4,30.48,180),
 (15,'PGTH','input',25.4,15.24,180),(16,'PGOOD_NATIVE','open_collector',25.4,5.08,180),
 (14,'~{FLT}','open_collector',25.4,-5.08,180),(12,'~{SHDN}','input',25.4,-15.24,180),
 (13,'IMON','output',25.4,-25.4,180),(11,'MODE','input',25.4,-35.56,180),
 (8,'GND','power_in',-12.7,-50.8,90),(25,'EP_GND','passive',-5.08,-50.8,90),
 (9,'dVdT','passive',7.62,-50.8,90),(10,'ILIM','passive',17.78,-50.8,90)]
pins1 += [(n,'NC','no_connect',-15.24+(n-19)*5.08,50.8,270) for n in range(19,25)]
ic('TPS26630RGER',pins1,20.32,45.72)
pins2=[(1,'VDD','power_in',-25.4,15.24,0),(3,'SENSE','input',-25.4,0,0),
 (6,'~{RESET}','open_collector',25.4,10.16,180),(9,'CTR/~{MR}','passive',25.4,-5.08,180),
 (10,'CTS','passive',25.4,-15.24,180),(8,'GND','power_in',-5.08,-30.48,90),(13,'GND','passive',5.08,-30.48,90)]
pins2 += [(n,'NC','no_connect',-15.24+i*5.08,30.48,270) for i,n in enumerate([2,4,5,7,11,12,14])]
ic('TPS3760A012DYYR',pins2,20.32,25.4)
ic('Power_Input_2pin',[(1,'+','passive',10.16,0,180),(2,'-','passive',10.16,-5.08,180)],5.08,7.62)

doc=[S('kicad_sch'),[S('version'),20250114],[S('generator'),'eeschema'],[S('generator_version'),'9.0'],
 [S('uuid'),childid],[S('paper'),'A3'],parse('(title_block (title "1 - Power Input / Protection") (date "2026-09-09") (rev "4A") (company "circuitBuilderAi-Astra") (comment 1 "Phase 3 + Phase 3A contract. Sheet 1 only; not a board-release approval."))')]
embedded=[S('lib_symbols')]
for name,data in library.items():
 a=deepcopy(data);a[1]='Astra_Power:'+name;embedded.append(a)
doc.append(embedded)
instances={}; bom=[]; counter=0
def append(raw): doc.append(parse(raw))
def note(text,x,y,size=1.27):
 append(f'(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{uid("text:"+text)}"))')
def wire(a,b):
 if a==b:return
 append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{uid("wire:"+str(a)+str(b))}"))')
def chain(*points):
 for a,b in zip(points,points[1:]):wire(a,b)
def dot(p):append(f'(junction (at {p[0]} {p[1]}) (diameter 0) (color 0 0 0 0) (uuid "{uid("dot:"+str(p))}"))')
def label(name,p):append(f'(label {q(name)} (at {p[0]} {p[1]} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid("label:"+name+str(p))}"))')
def nc(p):append(f'(no_connect (at {p[0]} {p[1]}) (uuid "{uid("nc:"+str(p))}"))')
def part(ref,name,value,x,y,angle=0,mpn='',manufacturer='',footprint='',evidence='',dnp=False,package=''):
 a=parse(f'(symbol (lib_id "Astra_Power:{name}") (at {x} {y} {angle}) (unit 1) (in_bom {"no" if ref.startswith("#") or ref.startswith("TP") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp {"yes" if dnp else "no"}) (uuid "{uid(ref)}"))')
 if name in ['R','C','C_Polarized','D_TVS']:
  px,py=x+3.81,y-1.27
 elif ref.startswith('U'):
  px,py=x-17.78,y-20.32 if ref=='U2' else y-40.64
 elif name=='TestPoint':px,py=x+2.54,y-5.08
 else:px,py=x-3.81,y-10.16
 if ref=='J1':px,py=20.32,45.72
 a.extend([prop('Reference',ref,px,py,ref.startswith('#')),prop('Value',value,px,py+2.54),prop('Footprint',footprint,hide=True),prop('Datasheet',evidence,hide=True),prop('MPN',mpn,hide=True),prop('Manufacturer',manufacturer,hide=True),prop('Package',package,hide=True)])
 for field in all_(a,'property')[:2]:one(field,'at')[3]=angle%180
 pins={}
 for unit in all_(library[name],'symbol'):
  for p in all_(unit,'pin'):
   num=one(p,'number')[1];ax,ay=one(p,'at')[1:3];r=math.radians(angle)
   pins[num]=(f(x+ax*math.cos(r)-ay*math.sin(r)),f(y-ax*math.sin(r)-ay*math.cos(r)))
   a.append(parse(f'(pin "{num}" (uuid "{uid(ref+":"+num)}"))'))
 a.append(parse(f'(instances (project "circuitBuilderAi-Astra" (path "/{rootid}/{sheetid}" (reference "{ref}") (unit 1))))'))
 doc.append(a);instances[ref]=pins
 if not ref.startswith('#'):
  bom.append(dict(reference=ref,value=value,mpn=mpn,manufacturer=manufacturer,package=package,footprint=footprint,evidence=evidence,dnp=dnp))
 return pins
def stub(ref,pin,net,dx=0,dy=5.08):
 p=instances[ref][str(pin)];end=(f(p[0]+dx),f(p[1]+dy));wire(p,end);label(net,end);return end
def resistor(ref,value,x,y,code):
 return part(ref,'R',value+' 0.1%',x,y,mpn='TNPW0805'+code+'BYEA',manufacturer='Vishay',footprint='Resistor_SMD:R_0805_2012Metric',package='0805; 0.1%; 10 ppm/K; 150 V; 0.14 W general mode',evidence='https://www.vishay.com/docs/28758/tnpw_e3.pdf')
def cap(ref,value,x,y,mpn,fp,package,url,polar=False):
 return part(ref,'C_Polarized' if polar else 'C',value,x,y,mpn=mpn,manufacturer='Rubycon' if polar else ('TDK' if mpn.startswith('C3216') else 'KEMET'),footprint=fp,package=package,evidence=url)

note('REGULATED 12 V INPUT | 10.8-13.2 V normal | cold start >=11.5 V | 4 A continuous / 5 A <1 s',20.32,17.78,1.52)
note('Bounded faults: +24 V DC and -14 V DC. No automotive surge class. TVS intentionally DNP.',20.32,25.4)
note('INPUT / FUSE',20.32,40.64,1.52)
note('REVERSE POLARITY / INRUSH / UV-OV CUTOFF',111.76,33.02,1.52)
note('PROTECTED POWER / HOLD-UP',271.78,40.64,1.52)

part('J1','Power_Input_2pin','XT30PW-M30.G.Y',25.4,60.96,mpn='XT30PW-M30.G.Y',manufacturer='AMASS',package='2-pin keyed horizontal THT; 3.0 mm tails',evidence='https://www.china-amass.com/biao/273.html')
part('F1','Fuse','10 A / 125 VDC',58.42,60.96,90,mpn='0451010.MRL',manufacturer='Littelfuse',footprint='Fuse:Fuse_Littelfuse-NANO2-451_453',package='6.10 x 2.69 mm Nano2; nonpolar',evidence='https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1')
chain(instances['J1']['1'],(45.72,60.96),instances['F1']['1']);label('12V_IN',(40.64,60.96))
stub('J1',2,'POWER_GND',0,12.7)
note('J1: pin 1 = +12 V; pin 2 = return',20.32,91.44)
note('Mate polarity must match molded + / -.',20.32,96.52)
note('F1 is backup protection; U1 limits load current.',20.32,106.68)
note('Source contract: 4 A continuous / 5 A short peak.',20.32,111.76)

part('Q1','CSD19537Q3','CSD19537Q3',132.08,58.42,270,mpn='CSD19537Q3',manufacturer='Texas Instruments',footprint='Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET',package='SON 3.3 x 3.3 mm; drain pins 5-8/EP represented by common pad 5',evidence='https://www.ti.com/lit/ds/symlink/csd19537q3.pdf')
chain(instances['F1']['2'],(78.74,60.96),(101.6,60.96),instances['Q1']['1']);label('IN_SYS',(86.36,60.96))
part('Q2','BSS138LT1G','BSS138LT1G',142.24,86.36,mpn='BSS138LT1G',manufacturer='onsemi',footprint='Package_TO_SOT_SMD:SOT-23',package='SOT-23 CASE318 style21',evidence='https://www.onsemi.com/download/data-sheet/pdf/bss138lt1-d.pdf')
stub('Q1',4,'B_GATE',0,-5.08)
stub('Q2',3,'B_GATE',0,-5.08);stub('Q2',1,'DRV',-10.16,0);stub('Q2',2,'IN_SYS',0,5.08)
note('Q1 S(1-3) -> IN_SYS; D(5-8/EP) -> EFUSE_IN',106.68,111.76)
note('Q2 source returns to IN_SYS, not ground.',106.68,116.84)

u1=part('U1','TPS26630RGER','TPS26630RGER',215.9,96.52,mpn='TPS26630RGER',manufacturer='Texas Instruments',footprint='Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm',package='RGE0024H VQFN-24 + EP25',evidence='https://www.ti.com/lit/ds/symlink/tps2663.pdf')
chain(instances['Q1']['5'],(175.26,60.96),u1['1']);chain((175.26,60.96),(175.26,66.04),u1['2']);dot((175.26,60.96));label('EFUSE_IN',(157.48,60.96))
for pin,net in [(5,'IN_SYS'),(3,'B_GATE'),(4,'DRV'),(6,'UVLO_SET'),(7,'OVP_SET')]:stub('U1',pin,net,-12.7,0)
for pin in [11,12,13,16,19,20,21,22,23,24]:nc(u1[str(pin)])
stub('U1',15,'POWER_GND',12.7,0);stub('U1',14,'EFUSE_FLT_N',12.7,0)
chain(u1['8'],(203.2,152.4),(210.82,152.4),u1['25']);label('POWER_GND',(203.2,152.4))
note('PGTH = GND: every recovery uses dVdT.',251.46,124.46)
note('Native PGOOD and IMON unused. MODE open = latch-off.',251.46,132.08)
note('SHDN open: internal pullup. Reset overload by input power cycle.',251.46,139.7)

urltdk='https://product.tdk.com/en/documents/chara_sheet/C3216X7R1H105K160AB.pdf'
for ref,x,net in [('C1',78.74,'IN_SYS'),('C2',157.48,'EFUSE_IN'),('C3',284.48,'12V_PROTECTED')]:
 cap(ref,'1 uF / 50 V',x,73.66,'C3216X7R1H105K160AB','Capacitor_SMD:C_1206_3216Metric','1206 X7R +/-10%',urltdk)
 chain((x,60.96),instances[ref]['1']);dot((x,60.96));stub(ref,2,'POWER_GND')
part('D1','D_TVS','DNP - BIDIR TVS',101.6,73.66,270,dnp=True,footprint='Diode_SMD:D_SMC',package='Reserved DO-214AB/SMC; nonpolar; no device selected',evidence='Phase 3 section 4.2')
chain((101.6,60.96),instances['D1']['1']);dot((101.6,60.96));stub('D1',2,'POWER_GND')
chain(u1['17'],(261.62,60.96),(284.48,60.96),(317.5,60.96),(350.52,60.96));chain(u1['18'],(261.62,66.04),(261.62,60.96));dot((261.62,60.96));label('12V_PROTECTED',(271.78,60.96))
cap('C4','470 uF / 25 V',317.5,73.66,'25ZLH470MEFC10X12.5','Capacitor_THT:CP_Radial_D10.0mm_P5.00mm','10 x 12.5 mm; pitch 5 mm; +/-20%; polarized','https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLH.pdf',True)
wire((317.5,60.96),instances['C4']['1']);dot((317.5,60.96));stub('C4',2,'POWER_GND')
note('C4 is the single 470 uF hold-up / amplifier bulk.',271.78,99.06)
note('Locate near amplifier later; do not duplicate on Sheet 6.',271.78,104.14)
note('Protected rail: 10.4-13.2 V normal; path <=0.4 V at 4 A.',271.78,111.76)

note('UVLO / OVP LADDER - PHASE 3A',20.32,127,1.52)
for ref,value,y,code in [('R1','316k',139.7,'316K'),('R2','13.3k',160.02,'13K3'),('R3','30.4k',180.34,'30K4')]:resistor(ref,value,60.96,y,code)
stub('R1',1,'IN_SYS',0,-5.08)
chain(instances['R1']['2'],(60.96,149.86),instances['R2']['1']);label('UVLO_SET',(60.96,149.86))
chain(instances['R2']['2'],(60.96,170.18),instances['R3']['1']);label('OVP_SET',(60.96,170.18));stub('R3',2,'POWER_GND')
note('UVLO fall: 8.876-9.563 V',20.32,203.2)
note('OVP rise: 13.793-14.606 V',20.32,208.28)
note('R1 >=300k required for reverse input.',20.32,213.36)
note('CURRENT LIMIT / RAMP',162.56,190.5,1.52)
cap('C5','47 nF / 50 V C0G',223.52,162.56,'C1206C473J5GACTU','Capacitor_SMD:C_1206_3216Metric','1206 C0G +/-5%','https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf')
resistor('R4','3.24k',259.08,162.56,'3K24')
wire(u1['9'],instances['C5']['1']);chain(u1['10'],(233.68,154.94),(259.08,154.94),instances['R4']['1'])
stub('C5',2,'POWER_GND');stub('R4',2,'POWER_GND')
note('RILIM: 5.56 A nominal; MODE open latch-off.',162.56,198.12)
note('CdVdT: ~9.0 ms 10-90% at 12 V; ~0.50 A into 470 uF.',162.56,203.2)

note('SYSTEM PGOOD - INDEPENDENT PRECISION SUPERVISOR',104.14,218.44,1.52)
u2=part('U2','TPS3760A012DYYR','TPS3760A012DYYR',259.08,251.46,mpn='TPS3760A012DYYR',manufacturer='Texas Instruments',package='DYY0014A SOT-23-THIN-14, 0.5 mm pitch; footprint assignment deferred',evidence='https://www.ti.com/lit/ds/symlink/tps3760.pdf')
stub('U2',1,'12V_PROTECTED',-12.7,0);stub('U2',3,'PGOOD_SENSE',-12.7,0)
chain(u2['8'],(254,284.48),(264.16,284.48),u2['13']);label('POWER_GND',(254,284.48))
for pin in [2,4,5,7,9,10,11,12,14]:nc(u2[str(pin)])
stub('U2',6,'PGOOD_12V',12.7,0)
resistor('R5','115k',152.4,236.22,'115K');resistor('R6','10.0k',152.4,261.62,'10K0')
stub('R5',1,'12V_PROTECTED',0,-5.08);chain(instances['R5']['2'],(152.4,248.92),instances['R6']['1']);label('PGOOD_SENSE',(152.4,248.92));stub('R6',2,'POWER_GND')
cap('C6','100 nF / 50 V C0G',198.12,266.7,'C1210C104J5GACTU','Capacitor_SMD:C_1210_3225Metric','1210 C0G +/-5%','https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf')
stub('C6',1,'12V_PROTECTED',0,-5.08);stub('C6',2,'POWER_GND')
resistor('R7','10.0k',322.58,236.22,'10K0');stub('R7',1,'3V8_PRE',0,-5.08);stub('R7',2,'PGOOD_12V',0,5.08)
note('0.8 V adjustable UV; active-low open-drain RESET; 2% hysteresis.',20.32,236.22)
note('PGOOD_12V fall: 9.870-10.130 V',20.32,246.38)
note('PGOOD_12V rise: 10.067-10.333 V',20.32,251.46)
note('CTS and CTR/MR open: fastest device modes.',20.32,261.62)
note('RESET is named PGOOD_12V: high means rail valid.',20.32,271.78)

# Test pads are copper-only features, not purchased components.
for ref,net,x,y in [('TP1','12V_PROTECTED',350.52,60.96),('TP2','PGOOD_SENSE',190.5,248.92),('TP3','PGOOD_12V',350.52,241.3),('TP4','EFUSE_FLT_N',281.94,154.94),('TP5','12V_IN',40.64,60.96),('TP6','POWER_GND',281.94,175.26)]:
 part(ref,'TestPoint',net,x,y,footprint='TestPoint:TestPoint_Pad_D2.0mm',package='Bare PCB pad; no purchased part')
 if ref in ['TP1','TP5']:dot((x,y))
 else:stub(ref,1,net,0,5.08)

# Ports have matching root pins. They end at the phase boundary, not fake sources.
ports=[('12V_PROTECTED','output',355.6,190.5),('POWER_GND','passive',355.6,198.12),('3V8_PRE','input',355.6,205.74),('PGOOD_12V','output',355.6,213.36),('EFUSE_FLT_N','output',355.6,220.98)]
for net,typ,x,y in ports:
 append(f'(hierarchical_label {q(net)} (shape {typ}) (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid("port:"+net)}"))')
 wire((x-50.8,y),(x,y));label(net,(x-50.8,y))
note('TO SHEET 2 (not yet implemented)',335.28,180.34,1.27)
note('3V8_PRE starts directly from protected rail.',307.34,149.86,1.016)
note('PGOOD is 3.8 V: condition before DSP.',307.34,154.94,1.016)
note('FLT: pull up to 3V3_SYS on later sheet.',307.34,160.02,1.016)
note('Either low must assert hardware safe latch.',307.34,165.1,1.016)
note('Never resume amplifier PLAY automatically.',307.34,170.18,1.016)

# Real external source and its post-passive feeds; flags describe power intent.
for ref,net,x,y in [('#FLG01','12V_IN',20.32,154.94),('#FLG02','POWER_GND',20.32,172.72),('#FLG03','IN_SYS',20.32,190.5),('#FLG04','EFUSE_IN',111.76,162.56)]:
 part(ref,'PWR_FLAG','PWR_FLAG',x,y);stub(ref,1,net,0,2.54)
note('Flags: external source and feeds through F1/Q1.',91.44,180.34,1.016)

write(HW/'power_input.kicad_sch',doc)
lib=[S('kicad_symbol_lib'),[S('version'),20250114],[S('generator'),'kicad_symbol_editor']]+list(library.values())
write(HW/'Astra_Power.kicad_sym',lib)
(HW/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Astra_Power") (type "KiCad") (uri "${KIPRJMOD}/Astra_Power.kicad_sym") (options "") (descr "Phase 4A verified local symbols")))\n',encoding='utf-8')

# Update only root annotations and the already-existing Sheet 1 block.
for t in all_(root,'text'):
 if 'PHASE 4A: BLOCKED' in t[1]:t[1]='PHASE 4A - Sheet 1 implemented to Phase 3A; Sheets 2-7 remain placeholders.'
 elif 'Power-input blocker:' in t[1]:t[1]='Sheet 1 interfaces terminate here until later-phase authorization. No PCB created.'
 elif t[1]=='BLOCKED - see validation record':t[1]='IMPLEMENTED - Phase 3A PGOOD correction'
tb=one(root,'title_block');one(tb,'rev')[1]='4A'
for c in all_(tb,'comment'):c[2]='Sheet 1 only. Later circuitry and PCB implementation are not authorized.'
# The root port stubs are intentionally unconnected and honestly reported by ERC.
root=[a for a in root if not (key(a)=='no_connect' and str(one(a,'uuid')[1]).startswith('unused'))]
sheet[:]=[a for a in sheet if key(a)!='pin']
for i,(net,typ,_,_) in enumerate(ports):
 x=195;y=f(70.08+i*3.81)
 sheet.append(parse(f'(pin {q(net)} {typ} (at {x} {y} 0) (effects (font (size 1.016 1.016)) (justify right)) (uuid "{uid("rootport:"+net)}"))'))
 # Deliberate no-connect only at the unimplemented system boundary.
 marker=parse(f'(no_connect (at {x} {y}) (uuid "{uid("rootnc:"+net)}"))')
 if not any(key(a)=='no_connect' and one(a,'uuid')[1]==one(marker,'uuid')[1] for a in root):root.append(marker)
write(HW/'circuitBuilderAi-Astra.kicad_sch',root)
(VAL/'sheet1_bom.json').write_text(json.dumps(bom,indent=2)+'\n',encoding='utf-8')
print(f'Updated Sheet 1: {len(bom)} objects, root ports, local symbols. Later sheets untouched.')
