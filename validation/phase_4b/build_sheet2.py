"""Reproducible Sheet 2 entry. Does not edit Sheet 1 or later sheets.

Authority: Phase 3D §§5,8,9,11; Phase 3B §§6,7; Phase 3C §4.
Run from repository root. Generated symbols use manufacturer pin numbers.
"""
from pathlib import Path
import copy, json, uuid, hashlib
import sexpdata as sx

ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware/kicad'
OUT=ROOT/'validation/phase_4b'
S=sx.Symbol
def node(k,*v): return [S(k),*v]
def tag(a,k): return next((x for x in a if isinstance(x,list) and x and str(x[0])==k),None)
def children(a,k): return [x for x in a if isinstance(x,list) and x and str(x[0])==k]
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,'astra/phase4b/'+k))
def effects(size=1.016,hide=False,justify=None):
    e=node('effects',node('font',node('size',size,size)))
    if hide:e.append(node('hide',S('yes')))
    if justify:e.append(node('justify',S(justify)))
    return e
def prop(k,v,x=0,y=0,hide=False):return node('property',k,str(v),node('at',x,y,0),effects(hide=hide))
def save(p,a): p.write_text(sx.dumps(a)+'\n',encoding='utf-8')

baseline=OUT/'sheet2_baseline_hashes.json'
if not baseline.exists():
    baseline.write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HW.glob('*') if p.is_file()},indent=2)+'\n')

# Separate library keeps every Sheet 1 library definition untouched.
old=sx.loads((HW/'Astra_Power.kicad_sym').read_text(encoding='utf-8'))
libs={x[1]:copy.deepcopy(x) for x in children(old,'symbol') if x[1] in ['R','C','TestPoint','PWR_FLAG']}
maps={}
def ic(name,fp,pins,left,right,source):
    """pins: number -> (name,electrical type); left/right determine drawing only."""
    h=max(len(left),len(right))*2.54+2.54
    a=node('symbol',name,node('pin_names',node('offset',0.762)),node('in_bom',S('yes')),node('on_board',S('yes')),
           prop('Reference','U'),prop('Value',name),prop('Footprint',fp,hide=True),prop('Datasheet',source,hide=True))
    a.append(node('symbol',name+'_0_1',node('rectangle',node('start',-17.78,h/2),node('end',17.78,-h/2),node('stroke',node('width',0.254),node('type',S('default'))),node('fill',node('type',S('background'))))))
    unit=node('symbol',name+'_1_1')
    for side,seq in [('L',left),('R',right)]:
        for j,num in enumerate(seq):
            nm,typ=pins[str(num)]; x=-22.86 if side=='L' else 22.86; y=h/2-3.81-j*2.54
            unit.append(node('pin',S(typ),S('line'),node('at',x,y,0 if side=='L' else 180),node('length',5.08),node('name',nm,effects()),node('number',str(num),effects())))
    assert sorted(str(n) for n in left+right)==sorted(pins)
    a.append(unit); libs[name]=a; maps[name]={'pins':pins,'footprint':fp,'evidence':source}

ic('TPS62135RGXR','Astra_Sequencing:Texas_RGX0011A',
   {str(n):(nm,t) for n,nm,t in [(1,'VIN','power_in'),(2,'SW','power_out'),(3,'GND','power_in'),(4,'FB2','open_collector'),(5,'FB','input'),(6,'VOS','input'),(7,'PG','open_collector'),(8,'EN','input'),(9,'SS/TR','passive'),(10,'MODE','input'),(11,'VSEL','input')]},
   [1,8,10,11,9,3],[2,6,5,4,7],'https://www.ti.com/lit/ds/symlink/tps62135.pdf')
ic('TPS7A4901DGNR','Package_SO:Texas_DGN0008D_VSSOP-8-1EP_3x3mm_P0.65mm_EP2x2.94mm_Mask1.57x1.89mm',
   {str(n):(nm,t) for n,nm,t in [(1,'OUT','power_out'),(2,'FB','input'),(3,'NC','no_connect'),(4,'GND','power_in'),(5,'EN','input'),(6,'NR/SS','passive'),(7,'DNC','no_connect'),(8,'IN','power_in'),(9,'EP','passive')]},
   [8,5,6,4,9],[1,2,3,7],'https://www.ti.com/lit/ds/symlink/tps7a49.pdf')
for name in ['TPS7A2033PDBVR','TPS7A2028PDBVR']:
    ic(name,'Package_TO_SOT_SMD:SOT-23-5',{'1':('IN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('NC','no_connect'),'5':('OUT','power_out')},[1,3,2],[5,4],'https://www.ti.com/lit/ds/symlink/tps7a20.pdf')
ic('LTC2964HUDC_PBF','Package_DFN_QFN:QFN-20-1EP_3x4mm_P0.5mm_EP1.65x2.65mm',
   {str(n):(nm,t) for n,nm,t in [(1,'RDIS','input'),(2,'MR','input'),(3,'DVCC','power_in'),(4,'VCC','power_in'),(5,'RST','open_collector'),(6,'GND','power_in'),(7,'OUT1','open_collector'),(8,'OUT2','open_collector'),(9,'OUT3','open_collector'),(10,'OUT4','open_collector'),(11,'RT','passive'),(12,'PG4','input'),(13,'PG3','input'),(14,'PG2','input'),(15,'PG1','input'),(16,'REF','output'),(17,'V4','input'),(18,'V3','input'),(19,'V2','input'),(20,'V1','input'),(21,'EP','passive')]},
   [4,20,19,18,17,1,2,11,3,6,21],[7,5,8,9,10,16,15,14,13,12],'https://www.analog.com/media/en/technical-documentation/data-sheets/ltc2962-2963-2964.pdf')
ic('TPS3431SDRBR','Package_DFN_QFN:Texas_DRB0008A',
   {'1':('VDD','power_in'),'2':('CWD','no_connect'),'3':('EN','input'),'4':('GND','power_in'),'5':('SET1','input'),'6':('WDI','input'),'7':('WDO','open_collector'),'8':('ENOUT','open_collector'),'9':('EP','passive')},
   [1,3,5,6,4,9],[7,8,2],'https://www.ti.com/lit/ds/symlink/tps3431.pdf')
ic('SN74LV1T08DBVR','Package_TO_SOT_SMD:SOT-23-5',{'1':('A','input'),'2':('B','input'),'3':('GND','power_in'),'4':('Y','output'),'5':('VCC','power_in')},[5,1,2,3],[4],'https://www.ti.com/lit/ds/symlink/sn74lv1t08.pdf')

# Symbols for passives whose topology is unambiguous; both terminals nonpolar.
for name,ref in [('L','L'),('Ferrite_Bead','FB')]:
    ic(name,'',{'1':('1','passive'),'2':('2','passive')},[1],[2],'')
    a=libs[name]; a[:]=[x for x in a if not (isinstance(x,list) and str(x[0])=='symbol')]
    a.append(node('symbol',name+'_0_1',node('rectangle',node('start',-2.54,1.27),node('end',2.54,-1.27),node('stroke',node('width',0.254),node('type',S('default'))),node('fill',node('type',S('none'))))))
    a.append(node('symbol',name+'_1_1',*[node('pin',S('passive'),S('line'),node('at',x,0,ang),node('length',1.27),node('name','',effects()),node('number',str(n),effects())) for n,x,ang in [(1,-3.81,0),(2,3.81,180)]]))
    tag(a,'property')[2]=ref
    maps[name]['pins']={'1':('','passive'),'2':('','passive')}

if 'TestPoint' not in libs:
    a=node('symbol','TestPoint',node('in_bom',S('yes')),node('on_board',S('yes')),prop('Reference','TP'),prop('Value','TestPoint'),prop('Footprint','TestPoint:TestPoint_Pad_D1.0mm',hide=True),prop('Datasheet','',hide=True),node('symbol','TestPoint_0_1',node('circle',node('center',0,1.27),node('radius',0.762),node('stroke',node('width',0.254),node('type',S('default'))),node('fill',node('type',S('none'))))),node('symbol','TestPoint_1_1',node('pin',S('passive'),S('line'),node('at',0,0,90),node('length',0.508),node('name','',effects()),node('number','1',effects()))))
    libs['TestPoint']=a

sch=node('kicad_sch',node('version',20260306),node('generator','eeschema'),node('generator_version','10.0'),node('uuid','f112a293-11b0-41c6-a5f9-a9a8679bfc7b'),node('paper','User',841,750),node('title_block',node('title','2 - Power Regulation / Sequencing'),node('date','2026-09-13'),node('rev','4B-BLOCKED'),node('company','circuitBuilderAi-Astra'),node('comment',1,'Partial entry only. Commanded-shutdown enable conflict; hardware-safe path incomplete.')))
parts={}; used=set(); tpnum=201
def wire(a,b):
    if a==b:return
    sch.append(node('wire',node('pts',node('xy',*a),node('xy',*b)),node('stroke',node('width',0),node('type',S('default'))),node('uuid',uid('w'+str(a)+str(b)))))
def label(net,x,y):sch.append(node('label',net,node('at',x,y,0),effects(0.889,justify='left'),node('uuid',uid('label'+net+str((x,y))))))
def note(txt,x,y,size=1.27):sch.append(node('text',txt,node('at',x,y,0),effects(size,justify='left'),node('uuid',uid('text'+txt))))
def pins_for(lib):
    return [p for sub in children(libs[lib],'symbol') for p in children(sub,'pin')]
def part(ref,lib,value,x,y,nets,fp=None,attrs=None,dnp=False):
    x=round(round(x/1.27)*1.27,5);y=round(round(y/1.27)*1.27,5)
    assert ref not in parts
    used.add(lib); sym=node('symbol',node('lib_id','Astra_Sequencing:'+lib),node('at',x,y,0),node('unit',1),node('in_bom',S('yes')),node('on_board',S('yes')),node('dnp',S('yes' if dnp else 'no')),node('uuid',uid(ref)))
    pdefs={p[1]:p[2] for p in children(libs[lib],'property')}
    fp=fp if fp is not None else pdefs.get('Footprint','')
    for k,v in {'Reference':ref,'Value':value,'Footprint':fp,'Datasheet':pdefs.get('Datasheet',''),**(attrs or {})}.items():
        if lib in ['R','C']:
            px,py=x+6.35,y+(-1.27 if k=='Reference' else 1.27)
        elif lib in ['L','Ferrite_Bead','TestPoint','PWR_FLAG']:
            px,py=x,y+(-6.35 if k=='Reference' else -3.81)
        else:px,py=x,y-22.86+(0 if k=='Reference' else 2.54)
        sym.append(prop(k,v,px,py,k not in ['Reference','Value']))
    sym.append(node('instances',node('project','circuitBuilderAi-Astra',node('path','/a89958ad-9daf-4465-87fb-0da6e733aead/c46ad3ab-53c4-4782-9638-c5343c581d6a',node('reference',ref),node('unit',1)))))
    pinpts={}
    for p in pins_for(lib):
        num=tag(p,'number')[1]; at=tag(p,'at'); px=round(x+at[1],5);py=round(y-at[2],5);ang=at[3];net=nets.get(num)
        pinpts[num]=[px,py]
        sym.append(node('pin',num,node('uuid',uid(ref+'.'+num))))
        if net is None:sch.append(node('no_connect',node('at',px,py),node('uuid',uid('nc'+ref+num))))
        else:
            dx,dy={0:(-5.08,0),180:(5.08,0),90:(0,2.54),270:(0,-2.54)}[ang]
            ex,ey=round(px+dx,5),round(py+dy,5);wire((px,py),(ex,ey));label(net,ex,ey)
    sch.append(sym);parts[ref]={'symbol':lib,'value':value,'footprint':fp,'nets':nets,'attributes':attrs or {},'dnp':dnp,'pin_positions':pinpts}
    return pinpts
def r(ref,value,x,y,a,b,tol='0.1%'):return part(ref,'R',value,x,y,{'1':a,'2':b},'Resistor_SMD:R_0603_1608Metric',{'Tolerance':tol,'Power rating':'0.1 W minimum','Polarity':'Nonpolar'})
def c(ref,value,x,y,a,b='POWER_GND',rating='25 V',extra='',dnp=False):return part(ref,'C',value,x,y,{'1':a,'2':b},'Capacitor_SMD:C_1206_3216Metric' if value in ['47u','22u','10u'] else 'Capacitor_SMD:C_0603_1608Metric',{'Voltage rating':rating,'Dielectric':'X7R/X5R' if value in ['47u','22u','10u','1u','100n'] else 'C0G','Tolerance':'10%' if value in ['47u','22u','10u','1u','100n'] else '5%','Acceptance':extra,'Polarity':'Nonpolar'},dnp)
def tp(net,x,y):
    global tpnum
    part('TP'+str(tpnum),'TestPoint',net,x,y,{'1':net});tpnum+=1

# Sheet 2 regulator sections. No load-device circuitry is entered.
for i,(rail,vin,en,rt,x) in enumerate([('3V8_PRE','12V_PROTECTED','12V_PROTECTED','44.2k',100),('1V0_DSP_CORE','3V8_PRE','OUT1','4.32k',365),('3V3_SYS','12V_PROTECTED','EN_3V3_SYS','37.1k',630)]):
    base=201+i*10; y=76.2; fb=rail+'_FB';sw=rail+'_SW';ss=rail+'_SS'
    note(rail+'  |  TPS62135 forced PWM',x-76.2,25.4,2)
    part('U'+str(201+i),'TPS62135RGXR','TPS62135RGXR',x,y,{'1':vin,'2':sw,'3':'POWER_GND','4':'POWER_GND','5':fb,'6':rail,'7':None,'8':en,'9':ss,'10':vin,'11':'POWER_GND'})
    part('L'+str(201+i),'L','1u',x+66.04,y-8.89,{'1':sw,'2':rail},'Inductor_SMD:L_Coilcraft_XAL4020-XXX',{'Acceptance':'L_eff >=0.8uH over tolerance/bias; Isat and Irms >=5A; DCR <=30mOhm','Polarity':'Nonpolar','Nominal inductance':'1.0 uH','Candidate MPN':'XAL4020-102MEC; effective-L qualification required'})
    r('R'+str(base),rt,x+73.66,y+17.78,rail,fb);r('R'+str(base+1),'10.0k',x+114.3,y+17.78,fb,'POWER_GND')
    c('C'+str(base),'10u',x-63.5,y,vin,extra='CIN effective >=3uF; local VIN-GND')
    c('C'+str(base+1),'10n',x-63.5,y+35.56,ss,extra='Independent soft start; no external feed-forward')
    for j in range(3 if i==1 else 2):c('C'+str(base+2+j),'47u' if i==1 else '22u',x+55.88+j*30.48,y+53.34,rail,rating='16 V',extra='Total directly connected COUT: 100..200uF effective' if i==1 else 'Total COUT: 22..200uF effective; VOS Kelvin at local positive bank')
    c('C'+str(base+5),'22u',x+147.32,y+53.34,rail,rating='16 V',extra='DNP ramp tuning only; do not exceed total 200uF effective',dnp=True)
    tp(rail,x+66.04,y-22.86);tp(fb,x+114.3,y+40.64);tp(ss,x-63.5,y+55.88)
    note('MODE=VIN; VSEL=0; FB2=0; native PG intentionally NC.\nKelvin FB bottom to GND; VOS to local COUT positive.\nL/C qualification and distributed capacitance remain board validation.',x-76.2,y+76.2)

for i,(rail,vin,en,tops,pre,nr,x) in enumerate([('1V8_DSP_REF_ANA','3V8_PRE','PGOOD_12V',['54.2k','100'],'1.69k','47n',100),('1V35_DSP_DMC','3V8_PRE','OUT1',['14.9k'],'1.24k','47n',365),('5V_AFE','12V_PROTECTED','AFE_EN',['324k'],'4.70k','10n',630)]):
    base=231+i*10; y=220.98; fb=rail+'_FB';ss=rail+'_NR'; topmid=rail+'_FB_TOP_MID'
    note(rail+'  |  TPS7A4901DGNR',x-76.2,177.8,2)
    part('U'+str(204+i),'TPS7A4901DGNR','TPS7A4901DGNR',x,y,{'1':rail,'2':fb,'3':None,'4':'POWER_GND','5':en,'6':ss,'7':None,'8':vin,'9':'POWER_GND'})
    r('R'+str(base),tops[0],x+66.04,y+5.08,rail,topmid if len(tops)==2 else fb)
    if len(tops)==2:r('R'+str(base+1),tops[1],x+106.68,y+5.08,topmid,fb)
    r('R'+str(base+2),'100k',x+66.04,y+38.1,fb,'POWER_GND')
    r('R'+str(base+3),pre,x+147.32,y+38.1,rail,'POWER_GND')
    c('C'+str(base),'10u',x-63.5,y,vin,extra='CIN effective >=2.2uF')
    c('C'+str(base+1),'10u',x+147.32,y+5.08,rail,rating='16 V',extra='COUT effective >=2.2uF; ESR <200mOhm')
    c('C'+str(base+2),nr,x-63.5,y+33.02,ss,extra='NR/SS per Phase 3D')
    c('C'+str(base+3),'10n',x+106.68,y+38.1,rail,fb,extra='CFF across complete upper feedback arm')
    if i==1:c('C'+str(base+4),'47u',x+55.88,y+71.12,rail,rating='16 V',extra='DMC domain bulk >=22uF effective; Phase 3 section 5.1')
    c('C'+str(base+5),'10u',x+147.32,y+71.12,rail,rating='16 V',extra='DNP ramp adjustment bank',dnp=True)
    tp(rail,x+147.32,y-15.24);tp(fb,x+66.04,y+58.42);tp(ss,x-63.5,y+55.88)
    note('DNC pin 7 and NC pin 3 open; EP pin 9 grounded.\nPreload is permanent, included in total rail allocation.\nCFF spans OUT to FB (including series top-arm resistors).',x-76.2,y+91.44)

for i,(rail,lib,pre,x) in enumerate([('3V3_ADC_A','TPS7A2033PDBVR','3.01k',100),('2V8_MIC','TPS7A2028PDBVR','2.55k',365)]):
    base=261+i*10;y=378.46
    note(rail+'  |  '+lib,x-76.2,y-40.64,2)
    part('U'+str(207+i),lib,lib,x,y,{'1':'3V8_PRE','2':'POWER_GND','3':'OUT1','4':None,'5':rail})
    c('C'+str(base),'10u',x-63.5,y,'3V8_PRE',extra='Effective >=0.47uF')
    c('C'+str(base+1),'10u',x+66.04,y,rail,rating='16 V',extra='COUT effective 0.47..200uF; ESR <=100mOhm')
    c('C'+str(base+2),'100n',x+106.68,y,rail)
    r('R'+str(base),pre,x+147.32,y,rail,'POWER_GND')
    tp(rail,x+66.04,y-20.32)
    note('P variant: active output discharge. EN=OUT1.\nNo startup-time guarantee extrapolated to this capacitor bank.\nConsumer-side filtering/decoupling belongs to the later load sheets.',x-76.2,y+30.48)

# Supervisor: explicit Kelvin sense nets, exact compound DMC upper arm.
x=100;y=495.3
note('Four DSP rail comparators / first-rail qualification',23.8,444.5,2)
part('U209','LTC2964HUDC_PBF','LTC2964HUDC#PBF',x,y,{'1':'3V8_PRE','2':'3V8_PRE','3':'POWER_GND','4':'3V8_PRE','5':'RAILS_OK','6':'POWER_GND','7':'OUT1','8':None,'9':None,'10':None,'11':'3V8_PRE','12':'SUP_REF','13':'SUP_REF','14':'SUP_REF','15':'SUP_REF','16':'SUP_REF','17':'SENSE_3V3','18':'SENSE_DMC','19':'SENSE_CORE','20':'SENSE_1V8','21':'POWER_GND'})
c('C281','100n',36.5,480.06,'3V8_PRE');r('R281','10.0k',36.5,518.16,'3V8_PRE','OUT1');r('R282','10.0k',166.04,518.16,'3V3_SYS','RAILS_OK')
for i,(rail,sense,top) in enumerate([('1V8_DSP_REF_ANA','SENSE_1V8','24.9k'),('1V0_DSP_CORE','SENSE_CORE','9.31k'),('1V35_DSP_DMC','SENSE_DMC','15.8k'),('3V3_SYS','SENSE_3V3','53.6k')]):
    xx=270+i*66.04; yy=480.06
    r('R'+str(291+i*3),top,xx,yy,rail,'SENSE_DMC_MID' if i==2 else sense)
    if i==2:r('R303','280',xx,yy+25.4,'SENSE_DMC_MID',sense)
    r('R'+str(292+i*3),'10.0k',xx,yy+50.8,sense,'POWER_GND')
    tp(sense,xx+25.4,yy+50.8)
note('PG1..PG4 = REF (+ADJ); no PG capacitors. RT=VCC: 160..240ms.\nRST=RAILS_OK, isolated from SYS_HWRST.\nDo not substitute regulator PG; sense returns Kelvin to supervisor GND.',23.8,561.34)

# Watchdog and branch-local gate.
part('U210','TPS3431SDRBR','TPS3431SDRBR',630,485.14,{'1':'3V3_SYS','2':None,'3':'RAILS_OK','4':'POWER_GND','5':'3V3_SYS','6':'DSP_WDI','7':'SYS_HWRST','8':'SYS_HWRST','9':'POWER_GND'})
note('TPS3431: independent watchdog / delayed reset',553.8,444.5,2)
c('C282','100n',566.5,497.84,'3V3_SYS');r('R283','10.0k',711.28,495.3,'3V3_SYS','SYS_HWRST')
r('R284','10.0k',566.5,528.32,'DSP_WDI','POWER_GND')
tp('RAILS_OK',711.28,520.7);tp('SYS_HWRST',752,520.7);tp('OUT1',711.28,548.64);tp('DSP_WDI',752,548.64)
note('CWD NC; SET1=VDD; WDO and ENOUT wired open drain.\n330..470ms total rail-valid to reset release; WDT 1.36..1.84s.\nFirst DSP falling WDI edge <=1.13s after reset release.\nDSP WDI default low; firmware services during boot.',553.8,571.5)
part('U211','SN74LV1T08DBVR','SN74LV1T08DBVR',630,378.46,{'1':'OUT1','2':'PGOOD_12V','3':'POWER_GND','4':'EN_3V3_SYS','5':'3V8_PRE'})
c('C283','100n',566.5,378.46,'3V8_PRE');r('R285','1.0M',711.28,378.46,'EN_3V3_SYS','POWER_GND')
tp('EN_3V3_SYS',752,393.7)
note('3V3_SYS EN = OUT1 AND PGOOD_12V\n1.0M EN pulldown; inputs remain separate status nets.',553.8,416.56)

r('R310','100k',630,635,'AFE_EN','POWER_GND')
tp('AFE_EN',680,635)
tp('PGOOD_12V',30.48,635);tp('EFUSE_FLT_N',100.33,635)
tp('12V_PROTECTED',171.45,635);tp('POWER_GND',241.3,635)
tp('SUP_REF',311.15,635)
tp('AFE_EN_CMD',381,635)
note('AFE EN held off by R310. Command and fault override NOT connected.\nNo power-up / reset / safe-state implementation approval is implied.\nHardware-safe latch, dominance, commanded shutdown, and AFE override are incomplete.',23.8,688.34,1.5)

# Controlled stop: Phase 3D's common OUT1 enable cannot independently remove
# microphone power before core/DMC in the retained commanded-shutdown order.
# Do not invent extra enables, load switches, or a different shutdown order.
# AFE_EN_CMD is the already-buffered Sheet 5 interface in Phase 3 §§8.2,11.
# Interface contacts use hierarchical labels. Root integration is separate.
interfaces={'12V_PROTECTED':'input','POWER_GND':'passive','3V8_PRE':'output','PGOOD_12V':'input','EFUSE_FLT_N':'input','1V8_DSP_REF_ANA':'output','1V0_DSP_CORE':'output','1V35_DSP_DMC':'output','3V3_SYS':'output','3V3_ADC_A':'output','2V8_MIC':'output','5V_AFE':'output','RAILS_OK':'output','SYS_HWRST':'bidirectional','DSP_WDI':'input','AFE_EN_CMD':'input'}
note('PHASE 4B BLOCKED: common OUT1 cannot turn microphones off while retaining core/DMC power.\nPhase 3D section 9.1(5), 11(6) versus section 9.2 commanded-shutdown order. No enable relation changed.',23.8,586.74,1.5)
for i,(net,direction) in enumerate(interfaces.items()):
    xx=20.32+i*49.53; yy=10.16
    sch.append(node('hierarchical_label',net,node('shape',S(direction)),node('at',xx,yy,0),effects(0.889,justify='left'),node('uuid',uid('hier'+net))))
    wire((xx,yy),(xx,yy+2.54));label(net,xx,yy+2.54)

# Regulated outputs are behind inductors, which ERC does not treat as power
# drivers. These flags declare the verified upstream converter sources only.
for i,net in enumerate(['3V8_PRE','1V0_DSP_CORE','3V3_SYS']):
    part('#FLG'+str(201+i),'PWR_FLAG','PWR_FLAG',460+i*55.88,635,{'1':net},attrs={'Reason':'Regulated output behind series inductor; TPS62135 source shown on this sheet'})

embedded=node('lib_symbols')
for name in sorted(used):
    a=copy.deepcopy(libs[name]);a[1]='Astra_Sequencing:'+name;embedded.append(a)
sch.insert(7,embedded)
save(HW/'Astra_Sequencing.kicad_sym',node('kicad_symbol_lib',node('version',20250114),node('generator','kicad_symbol_editor'),*[libs[n] for n in sorted(used)]))
table=sx.loads((HW/'sym-lib-table').read_text())
if not any(tag(x,'name') and tag(x,'name')[1]=='Astra_Sequencing' for x in children(table,'lib')):
    table.append(node('lib',node('name','Astra_Sequencing'),node('type','KiCad'),node('uri','${KIPRJMOD}/Astra_Sequencing.kicad_sym'),node('options',''),node('descr','Phase 4B manufacturer pin-verified Sheet 2 symbols')))
save(HW/'sym-lib-table',table)
save(HW/'power_regulation.kicad_sch',sch)
(OUT/'sheet2_components.json').write_text(json.dumps(parts,indent=2)+'\n')
(OUT/'sheet2_symbol_pin_audit.json').write_text(json.dumps({k:v for k,v in maps.items() if k in used},indent=2)+'\n')
print(f'Generated {len(parts)} components; circuit is incomplete until safety integration and KiCad validation.')
