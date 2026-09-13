"""Reproducible Sheet 2 entry. Does not edit Sheet 1 or later sheets.

Authority: Phase 3F and Phase 3E supersede controls; Phase 3D §§5,8,9,11; Phase 3B §§6,7; Phase 3C §4.
Run from repository root. Generated symbols use manufacturer pin numbers.
"""
from pathlib import Path
import copy, json, uuid, hashlib
import sexpdata as sx

ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware/kicad'
OUT=ROOT/'validation/phase_4b/phase3f_completion'
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

sch=node('kicad_sch',node('version',20260306),node('generator','eeschema'),node('generator_version','10.0'),node('uuid','f112a293-11b0-41c6-a5f9-a9a8679bfc7b'),node('paper','User',1700,1189),node('title_block',node('title','2 - Power Regulation / Sequencing'),node('date','2026-09-14'),node('rev','4B'),node('company','circuitBuilderAi-Astra'),node('comment',1,'Phase 3D rails; Phase 3E retained shutdown; Phase 3F bootstrap and functional authorization.')))
parts={}; used=set(); tpnum=201
def wire(a,b):
    if a==b:return
    sch.append(node('wire',node('pts',node('xy',*a),node('xy',*b)),node('stroke',node('width',0),node('type',S('default'))),node('uuid',uid('w'+str(a)+str(b)))))
def label(net,x,y,justify='left'):sch.append(node('label',net,node('at',x,y,0),effects(0.889,justify=justify),node('uuid',uid('label'+net+str((x,y))))))
def note(txt,x,y,size=1.27):sch.append(node('text',txt,node('at',x,y,0),effects(size,justify='left'),node('uuid',uid('text'+txt))))
def pins_for(lib):
    return [p for sub in children(libs[lib],'symbol') for p in children(sub,'pin')]
def part(ref,lib,value,x,y,nets,fp=None,attrs=None,dnp=False):
    x=round(round(x/1.27)*1.27,5);y=round(round(y/1.27)*1.27,5)
    assert ref not in parts
    used.add(lib); sym=node('symbol',node('lib_id','Astra_Sequencing:'+lib),node('at',x,y,0),node('unit',1),node('in_bom',S('yes')),node('on_board',S('yes')),node('dnp',S('yes' if dnp else 'no')),node('uuid',uid(ref)))
    pdefs={p[1]:p[2] for p in children(libs[lib],'property')}
    fp=fp if fp is not None else pdefs.get('Footprint','')
    if lib=='TestPoint': fp='TestPoint:TestPoint_Pad_D1.0mm'
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
            ex,ey=round(px+dx,5),round(py+dy,5);wire((px,py),(ex,ey));label(net,ex,ey,justify='right' if ang==0 else 'left')
    sch.append(sym);parts[ref]={'symbol':lib,'value':value,'footprint':fp,'nets':nets,'attributes':attrs or {},'dnp':dnp,'pin_positions':pinpts}
    return pinpts
def r(ref,value,x,y,a,b,tol='0.1%'):return part(ref,'R',value,x,y,{'1':a,'2':b},'Resistor_SMD:R_0603_1608Metric',{'Tolerance':tol,'Power rating':'0.1 W minimum','Polarity':'Nonpolar'})
def c(ref,value,x,y,a,b='POWER_GND',rating='25 V',extra='',dnp=False):return part(ref,'C',value,x,y,{'1':a,'2':b},'Capacitor_SMD:C_1206_3216Metric' if value in ['47u','22u','10u'] else 'Capacitor_SMD:C_0603_1608Metric',{'Voltage rating':rating,'Dielectric':'X7R/X5R' if value in ['47u','22u','10u','1u','100n'] else 'C0G','Tolerance':'10%' if value in ['47u','22u','10u','1u','100n'] else '5%','Acceptance':extra,'Polarity':'Nonpolar'},dnp)
def tp(net,x,y):
    global tpnum
    part('TP'+str(tpnum),'TestPoint',net,x,y,{'1':net});tpnum+=1

# Sheet 2 regulator sections. No load-device circuitry is entered.
for i,(rail,vin,en,rt,x) in enumerate([('3V8_PRE','12V_PROTECTED','12V_PROTECTED','44.2k',100),('1V0_DSP_CORE','3V8_PRE','DOWNSTREAM_EN','4.32k',365),('3V3_SYS','12V_PROTECTED','DOWNSTREAM_EN','37.1k',630)]):
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

for i,(rail,vin,en,tops,pre,nr,x) in enumerate([('1V8_DSP_REF_ANA','3V8_PRE','PGOOD_12V',['54.2k','100'],'1.69k','47n',100),('1V35_DSP_DMC','3V8_PRE','DOWNSTREAM_EN',['14.9k'],'1.24k','47n',365),('5V_AFE','12V_PROTECTED','ANALOG_PWR_EN',['324k'],'4.70k','10n',630)]):
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
    part('U'+str(207+i),lib,lib,x,y,{'1':'3V8_PRE','2':'POWER_GND','3':'DOWNSTREAM_EN' if i==0 else 'ANALOG_PWR_EN','4':None,'5':rail})
    c('C'+str(base),'10u',x-63.5,y,'3V8_PRE',extra='Effective >=0.47uF')
    c('C'+str(base+1),'10u',x+66.04,y,rail,rating='16 V',extra='COUT effective 0.47..200uF; ESR <=100mOhm')
    c('C'+str(base+2),'100n',x+106.68,y,rail)
    r('R'+str(base),pre,x+147.32,y,rail,'POWER_GND')
    tp(rail,x+66.04,y-20.32)
    note('P variant: active output discharge. Qualified branch EN.\nNo startup-time guarantee extrapolated to this capacitor bank.\nConsumer-side filtering/decoupling belongs to the later load sheets.',x-76.2,y+30.48)

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

# Phase 3E/F additions. Pin lists independently transcribed from manufacturer
# tables (not inferred from a third-party symbol). Every instance has bypass.
dcufp='Package_SO:VSSOP-8_2.3x2mm_P0.5mm'
ic('SN74LVC1G74DCUR',dcufp,{'1':('CLK','input'),'2':('D','input'),'3':('~{Q}','output'),'4':('GND','power_in'),'5':('Q','output'),'6':('~{CLR}','input'),'7':('~{PRE}','input'),'8':('VCC','power_in')},[8,7,6,2,1,4],[5,3],'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf')
for name,typ in [('SN74LVC2G07DBVR','open_collector'),('SN74LVC2G17DBVR','output')]:
    ic(name,'Package_TO_SOT_SMD:SOT-23-6',{'1':('1A','input'),'2':('GND','power_in'),'3':('2A','input'),'4':('2Y',typ),'5':('VCC','power_in'),'6':('1Y',typ)},[5,1,3,2],[6,4],'https://www.ti.com/lit/ds/symlink/'+name[:11].lower()+'.pdf')
ic('SN74LVC2G08DCUR',dcufp,{'1':('1A','input'),'2':('1B','input'),'3':('2Y','output'),'4':('GND','power_in'),'5':('2A','input'),'6':('2B','input'),'7':('1Y','output'),'8':('VCC','power_in')},[8,1,2,5,6,4],[7,3],'https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf')
xlatpins={'1':('VCCA','power_in'),'2':('DIR','input'),'22':('~{OE}','input'),'23':('VCCB','power_in'),'24':('VCCB','power_in'),**{str(n):('GND','power_in') for n in [11,12,13]}}
for n in range(1,9):
    xlatpins[str(n+2)]=('A'+str(n),'bidirectional');xlatpins[str(22-n)]=('B'+str(n),'bidirectional')
ic('SN74LXC8T245PWR','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',xlatpins,[1,2,3,4,5,6,7,8,9,10,22,11,12,13],[23,24,21,20,19,18,17,16,15,14],'https://www.ti.com/lit/ds/symlink/sn74lxc8t245.pdf')
timerpins={str(n):('NC','no_connect') for n in [2,4,5,7,11,12,14]}
timerpins.update({'1':('VDD','power_in'),'3':('SENSE','input'),'6':('~{RESET}','open_collector'),'8':('GND','power_in'),'9':('CTR/MR','passive'),'10':('CTS','passive'),'13':('GND','power_in')})
ic('TPS3760E012DYYR','Astra_Sequencing:Texas_DYY0014A',timerpins,[1,3,10,9,8,13],[6,2,4,5,7,11,12,14],'https://www.ti.com/lit/ds/symlink/tps3760.pdf')
ic('TMUX2821DSGR','Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm',{'1':('S1','passive'),'2':('D1','passive'),'3':('SEL2','input'),'4':('GND','power_in'),'5':('S2','passive'),'6':('D2','passive'),'7':('SEL1','input'),'8':('VDD','power_in'),'9':('EP','passive')},[8,7,3,1,5,4,9],[2,6],'https://www.ti.com/lit/ds/symlink/tmux2821.pdf')
ic('BSS138LT1G','Package_TO_SOT_SMD:SOT-23',{'1':('G','input'),'2':('S','passive'),'3':('D','open_collector')},[1,2],[3],'https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf')
tag(libs['BSS138LT1G'],'property')[2]='Q'

# DYY0014A package library only: TI TPS3760 Rev.A pp.41-43; 0.5mm pitch,
# pad centers 3.0mm apart, 14 pads 1.05 x 0.30mm. No board is created.
fp=node('footprint','Texas_DYY0014A',node('version',20241229),node('generator','pcbnew'),node('layer','F.Cu'),node('descr','TI DYY0014A; TPS3760 Rev.A pp.41-43; manufacturer recommended land pattern'),node('attr',S('smd')))
for n in range(1,15):
    xx=-1.5 if n<=7 else 1.5; yy=-1.5+(n-1)*.5 if n<=7 else 1.5-(n-8)*.5
    fp.append(node('pad',str(n),S('smd'),S('roundrect'),node('at',xx,yy),node('size',1.05,.3),node('layers','F.Cu','F.Paste','F.Mask'),node('roundrect_rratio',.16)))
fp.append(node('fp_rect',node('start',-1,-2.1),node('end',1,2.1),node('stroke',node('width',.1),node('type',S('solid'))),node('fill',S('none')),node('layer','F.Fab')))
fp.append(node('fp_rect',node('start',-2.28,-2.35),node('end',2.28,2.35),node('stroke',node('width',.05),node('type',S('solid'))),node('fill',S('none')),node('layer','F.CrtYd')))
fp.append(node('fp_circle',node('center',-2.2,-1.5),node('end',-2.05,-1.5),node('stroke',node('width',.12),node('type',S('solid'))),node('fill',S('none')),node('layer','F.SilkS')))
save(HW/'Astra_Sequencing.pretty/Texas_DYY0014A.kicad_mod',fp)

control_pos={};idx=0
def ctrl(ref,lib,nets,role,supply='3V8_PRE'):
    global idx
    x=950+280*(idx%3); y=80+96.52*(idx//3);idx+=1
    control_pos[ref]=(x,y)
    part(ref,lib,lib,x,y,nets,attrs={'Function':role,'Authority':'Phase 3E + Phase 3F'})
    c('C'+str(300+int(ref[1:])-211),'100n',x-65,y,supply)
    note(role,x-85,y-33,1.5)
    return x,y

def gate(ref,a,b,out,role):
    return ctrl(ref,'SN74LV1T08DBVR',{'1':a,'2':b,'3':'POWER_GND','4':out,'5':'3V8_PRE'},role)

gate('U211','OUT1','PGOOD_CLEAN','DOWNSTREAM_VALID','Downstream qualification 1/2')
gate('U212','DOWNSTREAM_VALID','DOWNSTREAM_RUN_DELAYED','DOWNSTREAM_EN','Downstream qualification 2/2')
gate('U213','SHUTDOWN_REQ_3V8','PGOOD_CLEAN','SHUTDOWN_CLK_3V8','Commanded shutdown clock')
gate('U214','PGOOD_CLEAN','SYS_HWRST_CLEAN','SAFE_PWR_RESET','Hardware safe clear 1/3')
gate('U215','EFUSE_FLT_CLEAN_N','AMP_FAULT_CLEAN_N','SAFE_FAULTS','Hardware safe clear 2/3')
gate('U216','SAFE_PWR_RESET','SAFE_FAULTS','SAFE_HW_CLEAR_N','Hardware safe clear 3/3')
gate('U217','SAFE_ARM_CMD_3V8','SYS_HWRST_CLEAN','SAFE_ARM_3V8','Explicit post-check arm edge')
gate('U218','DOWNSTREAM_EN','HW_RUN_LATCHED','ANALOG_PERMIT','Analog qualification 1/2')
gate('U219','ANALOG_PERMIT','ANALOG_PWR_CMD_3V8','ANALOG_PWR_EN','Analog qualification 2/2')
gate('U220','HW_RUN_LATCHED','AUDIO_DATA_OE_CMD_3V8','AUDIO_DATA_OE_RELEASE','Data authorization; no bootstrap gating')
ctrl('U221','SN74LVC1G74DCUR',{'1':'SHUTDOWN_CLK_3V8','2':'POWER_GND','3':'SEQ_SHUT','4':'POWER_GND','5':'SEQ_RUN_Q','6':'3V8_PRE','7':'PGOOD_CLEAN','8':'3V8_PRE'},'U_SEQ_RUN: retained service-off state')
ctrl('U222','SN74LVC1G74DCUR',{'1':'SAFE_ARM_3V8','2':'3V8_PRE','3':None,'4':'POWER_GND','5':'HW_RUN_LATCHED','6':'SAFE_CLEAR_N','7':'3V8_PRE','8':'3V8_PRE'},'U_SAFE_LATCH: functional authorization')
ctrl('U223','SN74LVC2G17DBVR',{'1':'PGOOD_12V','2':'POWER_GND','3':'EFUSE_FLT_N','4':'EFUSE_FLT_CLEAN_N','5':'3V8_PRE','6':'PGOOD_CLEAN'},'Raw PGOOD / eFuse Schmitt conditioning')
ctrl('U224','SN74LVC2G07DBVR',{'1':'SEQ_RUN_Q','2':'POWER_GND','3':'PGOOD_CLEAN','4':'SYS_HWRST','5':'3V8_PRE','6':'SYS_HWRST'},'Retained shutdown / immediate brownout reset')
timer={'1':'3V8_PRE','3':'SEQ_SHUT','6':'DOWNSTREAM_RUN_DELAYED','8':'POWER_GND','10':'DOWN_CTS','13':'POWER_GND'}
xx,yy=ctrl('U225','TPS3760E012DYYR',timer,'U_DOWN_DELAY: OV / active-low / open drain')
part('C340','C','220n',xx+70,yy,{'1':'DOWN_CTS','2':'POWER_GND'},'Capacitor_SMD:C_1210_3225Metric',{'MPN':'C1210C224J3GACTU','Tolerance':'5%','Dielectric':'C0G','Voltage rating':'25 V','Effective range':'208.373..231.693nF at -40..125C; inside required 198..242nF','Polarity':'Nonpolar','Evidence':'KEMET specsheet + C1003_C0G 2025-02-20; 30ppm/C; no bias or aging change'})
r('R340','10.0k',xx+110,yy,'3V8_PRE','DOWNSTREAM_RUN_DELAYED')
note('CTS 198..242nF acceptance: hold 20.415..40.946ms.\nCTR/MR open. Cold-start reset may add <=2ms.',xx-85,yy+40)

commands=['SHUTDOWN_REQ','SAFE_ARM_CMD','ANALOG_PWR_CMD','CLOCK_STARTUP_CMD','AUDIO_DATA_OE_CMD','RUN_HEALTH_OK_CMD','SYS_HWRST','AMP_FAULT_N']
translated=['SHUTDOWN_REQ_3V8','SAFE_ARM_CMD_3V8','ANALOG_PWR_CMD_3V8','CLOCK_STARTUP_CMD_3V8','AUDIO_DATA_OE_CMD_3V8','RUN_HEALTH_OK_3V8','SYS_HWRST_CLEAN','AMP_FAULT_CLEAN_N']
xn={'1':'3V3_SYS','2':'3V3_SYS','22':'POWER_GND','23':'3V8_PRE','24':'3V8_PRE','11':'POWER_GND','12':'POWER_GND','13':'POWER_GND'}
for i,(a,b) in enumerate(zip(commands,translated)):xn[str(3+i)]=a;xn[str(21-i)]=b
xx,yy=ctrl('U226','SN74LXC8T245PWR',xn,'U_CMD_XLAT: eight isolated A-to-B controls')
c('C341','100n',xx-105,yy,'3V3_SYS')
ctrl('U227','SN74LVC2G08DCUR',{'1':'HW_RUN_LATCHED','2':'AMP_MUTE_CMD','3':'AMP_STBY_RELEASE','4':'POWER_GND','5':'HW_RUN_LATCHED','6':'AMP_STBY_CMD','7':'AMP_MUTE_RELEASE','8':'3V3_SYS'},'Amplifier MUTE / STANDBY authorization','3V3_SYS')
ctrl('U228','SN74LVC2G08DCUR',{'1':'SYS_HWRST_CLEAN','2':'CLOCK_STARTUP_CMD_3V8','3':'SAFE_CLEAR_N','4':'POWER_GND','5':'SAFE_HW_CLEAR_N','6':'RUN_HEALTH_OK_3V8','7':'CLOCK_STARTUP_EN','8':'3V8_PRE'},'U_BOOT_GATES: clock bootstrap / health clear')
ctrl('U229','SN74LVC2G07DBVR',{'1':'SYS_HWRST','2':'POWER_GND','3':'ADC_RST_RELEASE_CMD','4':'ADC_PD_RST_N','5':'3V3_SYS','6':'ADC_PD_RST_N'},'ADC reset: system reset AND deliberate release','3V3_SYS')

# All eight translated outputs and every raw command have the frozen LOW
# defaults. Raw PGOOD pullup is on immutable Sheet 1; eFuse pullup is here.
for i,net in enumerate(commands+translated+['AMP_MUTE_CMD','AMP_STBY_CMD','ADC_RST_RELEASE_CMD','AMP_MUTE_RELEASE','AMP_STBY_RELEASE']):
    r('R'+str(350+i),'100k',850+38.1*(i%21),755+25.4*(i//21),net,'POWER_GND')
r('R380','10.0k',550,635,'3V3_SYS','AMP_FAULT_N')
r('R381','10.0k',610,635,'3V3_SYS','ADC_PD_RST_N')
r('R382','10.0k',680,635,'3V8_PRE','EFUSE_FLT_N')
# Separate physical pulldown at each regulator EN destination, even on a
# common logical net. Phase 3F/3E 100k supersedes old system 1M requirement.
for ref,net,x,y in [('R310','ANALOG_PWR_EN',730,300),('R311','ANALOG_PWR_EN',520,410),('R312','DOWNSTREAM_EN',220,410),('R313','DOWNSTREAM_EN',470,110),('R314','DOWNSTREAM_EN',470,300),('R315','DOWNSTREAM_EN',790,110)]:r(ref,'100k',x,y,net,'POWER_GND')

# Sheet 2 owns the three OE sinks and destination-rail pullups. Endpoint
# translators/audio banks and ADC DVDD components stay on their assigned
# later sheets; these hierarchical contracts are their only hookup paths.
for i,(enable,oe,supply) in enumerate([('RAILS_OK','MCLK_OE_N','1V8_DSP_REF_ANA'),('CLOCK_STARTUP_EN','AUDIO_CLOCK_OE_N','3V3_SYS'),('AUDIO_DATA_OE_RELEASE','AUDIO_DATA_OE_N','3V3_SYS')]):
    x=100+240*i;y=710
    part('Q'+str(201+i),'BSS138LT1G','BSS138LT1G',x,y,{'1':enable,'2':'POWER_GND','3':oe},attrs={'Authority':'Phase 3F section 9.2/9.4','Polarity':'N-channel; source grounded; drain only sinks destination-domain OE'})
    r('R'+str(390+2*i),'10.0k',x+65,y,supply,oe)
    r('R'+str(391+2*i),'100k',x-65,y,enable,'POWER_GND')
    tp(oe,x+100,y+20)
note('MCLK /OE from RAILS_OK only. Clock bank /1OE from CLOCK_STARTUP_EN.\nData bank /2OE from AUDIO_DATA_OE_RELEASE only.\nSN74AXC2T245, LVC244A, ASDLJ/LMK and endpoints: later-sheet contracts.\nADC sheet: DVDD CEXT=10uF X7R, Ceff<=12uF, REXT=3.00k 1%;\nPD/RST LOW >=50ms for in-place reset; PWUP only after DVDD+clock >=10ms.',23.8,770,1.5)

# Fourteen paired-domain analog isolators are explicitly required by Phase
# 3E/3F for Sheet 2. Only switch networks: no microphone/AFE/ADC load circuitry.
analog_interfaces=[]
def pair(index,supply_a,supply_b,paths,title):
    x=100+400*(index%4);y=890+160*(index//4)
    note(title,x-76,y-43,1.6)
    nets_a={'8':supply_a,'4':'POWER_GND','9':'POWER_GND'}
    nets_b={'8':supply_b,'4':'POWER_GND','9':'POWER_GND'}
    for ch,(ps,pd,sel) in enumerate([('1','2','7'),('5','6','3')]):
        if ch<len(paths):
            start,end=paths[ch];mid='ISO_'+str(index)+'_'+str(ch)
            nets_a.update({ps:start,pd:mid,sel:'ANALOG_PWR_EN'})
            nets_b.update({ps:mid,pd:end,sel:'ANALOG_PWR_EN'})
            analog_interfaces.extend([start,end])
        else:nets_a[sel]='POWER_GND';nets_b[sel]='POWER_GND'
    for j,(supply,nets) in enumerate([(supply_a,nets_a),(supply_b,nets_b)]):
        num=230+2*index+j
        part('U'+str(num),'TMUX2821DSGR','TMUX2821DSGR',x+140*j,y,nets,attrs={'Function':title+'; '+supply+' side','Authority':'Phase 3E section 7.1'})
        c('C'+str(350+2*index+j),'100n',x+140*j-65,y,supply)
    note('Used SEL = ANALOG_PWR_EN; either adjacent rail absent isolates path.\nNo endpoint load circuitry. Keep differential switch paths symmetrical.',x-76,y+47)
for i in range(4):pair(i,'5V_AFE','3V3_ADC_A',[(f'AFE{i+1}P_AFTER_47R',f'ADC_AIN{i+1}P'),(f'AFE{i+1}N_AFTER_47R',f'ADC_AIN{i+1}N')],f'AFE channel {i+1} -> ADC, two differential legs')
pair(4,'3V3_ADC_A','5V_AFE',[('ADC_VREF','AFE_VCM_INPUT')],'ADC VREF -> AFE VCM buffer; spare channels OFF')
for i in range(2):pair(5+i,'2V8_MIC','5V_AFE',[(f'MIC{2*i+j+1}_AFTER_100R',f'AFE{2*i+j+1}_BEFORE_4u7') for j in range(2)],f'Microphone pair {i+1} -> AFE coupling capacitors')

for i,net in enumerate(['PGOOD_12V','PGOOD_CLEAN','EFUSE_FLT_N','EFUSE_FLT_CLEAN_N','OUT1','DOWNSTREAM_RUN_DELAYED','DOWNSTREAM_EN','SEQ_RUN_Q','SEQ_SHUT','SYS_HWRST','SYS_HWRST_CLEAN','AMP_FAULT_N','AMP_FAULT_CLEAN_N','SAFE_HW_CLEAR_N','SAFE_CLEAR_N','HW_RUN_LATCHED','ANALOG_PWR_EN','CLOCK_STARTUP_EN','AUDIO_DATA_OE_RELEASE','RUN_HEALTH_OK_3V8','ADC_PD_RST_N','SHUTDOWN_REQ_3V8','SAFE_ARM_3V8','3V8_PRE','POWER_GND']):
    tp(net,25+65*(i%25),820)
note('START: RAILS_OK -> MCLK -> DSP boot -> CLOCK_STARTUP_CMD -> ADC reset/config/PLL -> RUN_HEALTH_OK + arm edge.\nOnly after arm: data, amplifier Hi-Z clock check, analog settling, then MUTE/PLAY. ADC-only PLL loss: hardware automute + firmware health withdrawal.\nSTOP: MUTE/Hi-Z/STANDBY >=15ms -> analog OFF, >=1ms -> data OFF + ADC reset -> health LOW -> clock command LOW -> SHUTDOWN_REQ.\nRetained reset -> 20.415..40.946ms -> downstream OFF. Service-off retains pre + 1V8 until external power cycle; no in-place restart.',840,1150,1.5)

interfaces={'12V_PROTECTED':'input','POWER_GND':'passive','3V8_PRE':'output','PGOOD_12V':'input','EFUSE_FLT_N':'input','1V8_DSP_REF_ANA':'output','1V0_DSP_CORE':'output','1V35_DSP_DMC':'output','3V3_SYS':'output','3V3_ADC_A':'output','2V8_MIC':'output','5V_AFE':'output','RAILS_OK':'output','SYS_HWRST':'bidirectional','DSP_WDI':'input'}
interfaces.update({s:'input' for s in commands if s not in interfaces})
interfaces.update({s:'input' for s in ['ADC_RST_RELEASE_CMD','AMP_MUTE_CMD','AMP_STBY_CMD']})
interfaces.update({s:'output' for s in ['ADC_PD_RST_N','AMP_MUTE_RELEASE','AMP_STBY_RELEASE','MCLK_OE_N','AUDIO_CLOCK_OE_N','AUDIO_DATA_OE_N','CLOCK_STARTUP_EN','HW_RUN_LATCHED','ANALOG_PWR_EN','RUN_HEALTH_OK_3V8','SAFE_CLEAR_N']})
interfaces.update({s:'passive' for s in analog_interfaces})
for i,(net,direction) in enumerate(interfaces.items()):
    xx=20.32+(i%21)*78.74;yy=10.16+(i//21)*6.35
    sch.append(node('hierarchical_label',net,node('shape',S(direction)),node('at',xx,yy,0),effects(.889,justify='left'),node('uuid',uid('hier'+net))))
    wire((xx,yy),(xx,yy+2.54));label(net,xx,yy+2.54)
for i,net in enumerate(['3V8_PRE','1V0_DSP_CORE','3V3_SYS']):
    part('#FLG'+str(201+i),'PWR_FLAG','PWR_FLAG',450+i*55.88,610,{'1':net},attrs={'Reason':'Shown regulated buck source behind series inductor'})

embedded=node('lib_symbols')
for name in sorted(used):
    a=copy.deepcopy(libs[name]);a[1]='Astra_Sequencing:'+name;embedded.append(a)
sch.insert(7,embedded)
save(HW/'Astra_Sequencing.kicad_sym',node('kicad_symbol_lib',node('version',20250114),node('generator','kicad_symbol_editor'),*[libs[n] for n in sorted(used)]))
save(HW/'power_regulation.kicad_sch',sch)
(OUT/'sheet2_components.json').write_text(json.dumps(parts,indent=2)+'\n')
(OUT/'sheet2_symbol_pin_audit.json').write_text(json.dumps({k:v for k,v in maps.items() if k in used},indent=2)+'\n')
(OUT/'sheet2_interfaces.json').write_text(json.dumps(interfaces,indent=2)+'\n')
print(f'Generated {len(parts)} components; native KiCad and engineering verification pending.')
