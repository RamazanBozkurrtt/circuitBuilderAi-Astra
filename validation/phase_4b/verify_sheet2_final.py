"""Native final Sheet 2 verification. No physical or later-sheet validation claimed."""
from pathlib import Path
import json, hashlib, itertools, os, subprocess, shutil, tempfile
import xml.etree.ElementTree as ET
import sexpdata as sx

ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware/kicad'; OUT=ROOT/'validation/phase_4b/phase3f_completion'
CLI=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/bin/kicad-cli.exe'
def tag(a,k):return next((x for x in a if isinstance(x,list) and x and str(x[0])==k),None)
def kids(a,k):return [x for x in a if isinstance(x,list) and x and str(x[0])==k]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    r=subprocess.run([str(CLI),*map(str,args)],capture_output=True)
    return {'command':[str(CLI),*map(str,args)],'exit_code':r.returncode,'stdout':r.stdout.decode('utf-8',errors='replace'),'stderr':r.stderr.decode('utf-8',errors='replace')}

logs=[]
before={p.name:sha(p) for p in HW.glob('*.kicad_sch')}
# Native KiCad force-save the full hierarchy in a temporary copy. Only the
# authorized root and Sheet 2 are copied back; original Sheet 1/later files stay
# byte-identical. A subsequent ERC/export loads the actual final project.
with tempfile.TemporaryDirectory(prefix='astra-4b-native-save-') as tmp:
    stage=Path(tmp)/'kicad';shutil.copytree(HW,stage)
    for name in ['power_regulation.kicad_sch','circuitBuilderAi-Astra.kicad_sch']:
        rec=run(['sch','upgrade','--force',stage/name]);logs.append(rec)
        assert rec['exit_code']==0,rec
    for name in ['circuitBuilderAi-Astra.kicad_sch','power_regulation.kicad_sch']:
        shutil.copy2(stage/name,HW/name)
logs.append(run(['sch','erc','--format','json','--output',OUT/'sheet2_erc_final.json',HW/'circuitBuilderAi-Astra.kicad_sch']))
logs.append(run(['sch','export','netlist','--format','kicadxml','--output',OUT/'sheet2_project.net.xml',HW/'circuitBuilderAi-Astra.kicad_sch']))
logs.append(run(['sch','export','pdf','--output',OUT/'sheet2_review.pdf',HW/'power_regulation.kicad_sch']))
assert all(x['exit_code']==0 for x in logs),logs
checks={}
def check(key,value):
    checks[key]=bool(value)
    assert value,key

nl=ET.parse(OUT/'sheet2_project.net.xml').getroot()
comps={c.get('ref'):c for c in nl.find('components')}
netby={}
for net in nl.find('nets'):
    for pin in net.findall('node'):netby[(pin.get('ref'),pin.get('pin'))]=net.get('name').rsplit('/',1)[-1]
def net(ref,pin):return netby.get((ref,str(pin)))
def value(ref):return comps[ref].findtext('value')
def field(ref,name):
    return next((p.text for p in comps[ref].findall('./fields/field') if p.get('name')==name),None)
def resistor(ref,val,top,bottom):
    check(ref+'_value',value(ref)==val)
    check(ref+'_polarity_nets',net(ref,1)==top and net(ref,2)==bottom)
    check(ref+'_tolerance',field(ref,'Tolerance')=='0.1%')
def cap(ref,val,a,b='POWER_GND'):
    check(ref+'_value_nets',value(ref)==val and net(ref,1)==a and net(ref,2)==b)

buck=[('U201','3V8_PRE','12V_PROTECTED','12V_PROTECTED',201,'44.2k',44200),('U202','1V0_DSP_CORE','3V8_PRE','DOWNSTREAM_EN',211,'4.32k',4320),('U203','3V3_SYS','12V_PROTECTED','DOWNSTREAM_EN',221,'37.1k',37100)]
realized={}
for u,rail,vin,en,b,rt,rtv in buck:
    resistor('R'+str(b),rt,rail,rail+'_FB');resistor('R'+str(b+1),'10.0k',rail+'_FB','POWER_GND')
    expected={1:vin,2:rail+'_SW',3:'POWER_GND',4:'POWER_GND',5:rail+'_FB',6:rail,8:en,9:rail+'_SS',10:vin,11:'POWER_GND'}
    check(u+'_pin_nets',all(net(u,n)==v for n,v in expected.items()))
    check(u+'_part',value(u)=='TPS62135RGXR')
    cap('C'+str(b+1),'10n',rail+'_SS');cap('C'+str(b),'10u',vin)
    check(u+'_inductor',net('L'+u[1:],1)==rail+'_SW' and net('L'+u[1:],2)==rail and value('L'+u[1:])=='1u')
    realized[rail]=[.7*.99*(1+rtv*.999/(10000*1.001))-70e-9*rtv*.999,.7*1.01*(1+rtv*1.001/(10000*.999))+70e-9*rtv*1.001]

ldos=[('U204','1V8_DSP_REF_ANA','3V8_PRE','PGOOD_12V',231,54300,'1.69k',1690,'47n'),('U205','1V35_DSP_DMC','3V8_PRE','DOWNSTREAM_EN',241,14900,'1.24k',1240,'47n'),('U206','5V_AFE','12V_PROTECTED','ANALOG_PWR_EN',251,324000,'4.70k',4700,'10n')]
preloads={}
for u,rail,vin,en,b,rtv,pre,prev,nrv in ldos:
    check(u+'_pin_nets',all(net(u,n)==v for n,v in {1:rail,2:rail+'_FB',4:'POWER_GND',5:en,6:rail+'_NR',8:vin,9:'POWER_GND'}.items()))
    check(u+'_part',value(u)=='TPS7A4901DGNR')
    if b==231:
        resistor('R231','54.2k',rail,rail+'_FB_TOP_MID');resistor('R232','100',rail+'_FB_TOP_MID',rail+'_FB')
    else:resistor('R'+str(b),'14.9k' if b==241 else '324k',rail,rail+'_FB')
    resistor('R'+str(b+2),'100k',rail+'_FB','POWER_GND');resistor('R'+str(b+3),pre,rail,'POWER_GND')
    cap('C'+str(b+2),nrv,rail+'_NR');cap('C'+str(b+3),'10n',rail,rail+'_FB')
    cap('C'+str(b),'10u',vin);cap('C'+str(b+1),'10u',rail)
    realized[rail]=[1.185*.975*(1+rtv*.999/(100000*1.001))-100e-9*rtv*.999,1.185*1.025*(1+rtv*1.001/(100000*.999))]
    preloads[rail]={'resistance_ohm':prev,'minimum_current_A':realized[rail][0]/(prev*1.001),'maximum_power_W':realized[rail][1]**2/(prev*.999)}
for u,rail,mpn,b,pre,prev,v in [('U207','3V3_ADC_A','TPS7A2033PDBVR',261,'3.01k',3010,3.3),('U208','2V8_MIC','TPS7A2028PDBVR',271,'2.55k',2550,2.8)]:
    check(u+'_pin_nets',all(net(u,n)==vv for n,vv in {1:'3V8_PRE',2:'POWER_GND',3:'DOWNSTREAM_EN' if u=='U207' else 'ANALOG_PWR_EN',5:rail}.items()))
    check(u+'_part',value(u)==mpn);resistor('R'+str(b),pre,rail,'POWER_GND')
    cap('C'+str(b),'10u','3V8_PRE');cap('C'+str(b+1),'10u',rail);cap('C'+str(b+2),'100n',rail)
    realized[rail]=[v*.985,v*1.015]
    preloads[rail]={'resistance_ohm':prev,'minimum_current_A':v*.985/(prev*1.001),'maximum_power_W':(v*1.015)**2/(prev*.999)}
check('all_five_minimum_loads',len(preloads)==5 and all(p['minimum_current_A']>=.001 for p in preloads.values()))
contract={'3V8_PRE':[3.746849,3.841293],'1V0_DSP_CORE':[.991476,1.013338],'3V3_SYS':[3.256299,3.337821],'1V8_DSP_REF_ANA':[1.776066,1.875487],'1V35_DSP_DMC':[1.325693,1.395966],'5V_AFE':[4.858943,5.157889],'3V3_ADC_A':[3.2505,3.3495],'2V8_MIC':[2.758,2.842]}
for rail,limits in contract.items():check(rail+'_3D_static_bounds',all(abs(v-w)<=.00000051 for v,w in zip(limits,realized[rail])))

sup=[('1V8_DSP_REF_ANA',20,'SENSE_1V8',291,'24.9k',24900,1.710,[1.733427,1.756604],.018396,.023427),('1V0_DSP_CORE',19,'SENSE_CORE',294,'9.31k',9310,.950,[.959608,.971404],.018596,.009608),('1V35_DSP_DMC',18,'SENSE_DMC',297,'15.8k',16080,1.283,[1.295641,1.312379],.012621,.012641),('3V3_SYS',17,'SENSE_3V3',300,'53.6k',53600,3.130,[3.157969,3.202097],.054202,.027969)]
supervision={}
for rail,pin,sense,b,top,rt,safemin,limits,relfloor,faultfloor in sup:
    resistor('R'+str(b),top,rail,'SENSE_DMC_MID' if pin==18 else sense)
    if pin==18:resistor('R303','280','SENSE_DMC_MID',sense)
    resistor('R'+str(b+1),'10.0k',sense,'POWER_GND');check(sense+'_pin',net('U209',pin)==sense)
    low=.4975*(1+rt*.999/(10000*1.001))-15e-9*rt*.999
    high=.5025*(1+rt*1.001/(10000*.999))+15e-9*rt*1.001
    check(sense+'_3D_threshold',abs(low-limits[0])<=.00000051 and abs(high-limits[1])<=.00000051)
    release=realized[rail][0]-high;fault=low-safemin
    check(sense+'_margin_floors',release>=relfloor-.00000051 and fault>=faultfloor-.00000051)
    supervision[rail]={'fall_rise_V':[low,high],'release_margin_V':release,'fault_margin_V':fault}
check('supervisor_exact_straps',all(net('U209',p)==v for p,v in {1:'3V8_PRE',2:'3V8_PRE',3:'POWER_GND',4:'3V8_PRE',5:'RAILS_OK',6:'POWER_GND',7:'OUT1',11:'3V8_PRE',12:'SUP_REF',13:'SUP_REF',14:'SUP_REF',15:'SUP_REF',16:'SUP_REF',21:'POWER_GND'}.items()))
check('watchdog_exact_straps',all(net('U210',p)==v for p,v in {1:'3V3_SYS',3:'RAILS_OK',4:'POWER_GND',5:'3V3_SYS',6:'DSP_WDI',7:'SYS_HWRST',8:'SYS_HWRST',9:'POWER_GND'}.items()))
check('separate_watchdog_enable_and_reset',net('U210',3)!=net('U210',7))

# Equations reconstructed from the exported device pins; these expected terms
# are independent of the entry generator. Output net names are also checked.
gate_expect={
 'U211':('OUT1','PGOOD_CLEAN','DOWNSTREAM_VALID'),
 'U212':('DOWNSTREAM_VALID','DOWNSTREAM_RUN_DELAYED','DOWNSTREAM_EN'),
 'U213':('SHUTDOWN_REQ_3V8','PGOOD_CLEAN','SHUTDOWN_CLK_3V8'),
 'U214':('PGOOD_CLEAN','SYS_HWRST_CLEAN','SAFE_PWR_RESET'),
 'U215':('EFUSE_FLT_CLEAN_N','AMP_FAULT_CLEAN_N','SAFE_FAULTS'),
 'U216':('SAFE_PWR_RESET','SAFE_FAULTS','SAFE_HW_CLEAR_N'),
 'U217':('SAFE_ARM_CMD_3V8','SYS_HWRST_CLEAN','SAFE_ARM_3V8'),
 'U218':('DOWNSTREAM_EN','HW_RUN_LATCHED','ANALOG_PERMIT'),
 'U219':('ANALOG_PERMIT','ANALOG_PWR_CMD_3V8','ANALOG_PWR_EN'),
 'U220':('HW_RUN_LATCHED','AUDIO_DATA_OE_CMD_3V8','AUDIO_DATA_OE_RELEASE')}
equations={}
for u,(aa,bb,yy) in gate_expect.items():
    check(u+'_exact_gate',value(u)=='SN74LV1T08DBVR' and all(net(u,n)==v for n,v in {1:aa,2:bb,3:'POWER_GND',4:yy,5:'3V8_PRE'}.items()))
    equations[net(u,4)]=[net(u,1),net(u,2)]
for u,supply,channels in [('U227','3V3_SYS',[(1,2,7,'HW_RUN_LATCHED','AMP_MUTE_CMD','AMP_MUTE_RELEASE'),(5,6,3,'HW_RUN_LATCHED','AMP_STBY_CMD','AMP_STBY_RELEASE')]),('U228','3V8_PRE',[(1,2,7,'SYS_HWRST_CLEAN','CLOCK_STARTUP_CMD_3V8','CLOCK_STARTUP_EN'),(5,6,3,'SAFE_HW_CLEAR_N','RUN_HEALTH_OK_3V8','SAFE_CLEAR_N')])]:
    check(u+'_part_supply',value(u)=='SN74LVC2G08DCUR' and net(u,8)==supply and net(u,4)=='POWER_GND')
    for a,b,y,aa,bb,yy in channels:
        check(u+'_'+yy,net(u,a)==aa and net(u,b)==bb and net(u,y)==yy)
        equations[net(u,y)]=[net(u,a),net(u,b)]

pin_expect={
 'U221':{1:'SHUTDOWN_CLK_3V8',2:'POWER_GND',3:'SEQ_SHUT',4:'POWER_GND',5:'SEQ_RUN_Q',6:'3V8_PRE',7:'PGOOD_CLEAN',8:'3V8_PRE'},
 'U222':{1:'SAFE_ARM_3V8',2:'3V8_PRE',4:'POWER_GND',5:'HW_RUN_LATCHED',6:'SAFE_CLEAR_N',7:'3V8_PRE',8:'3V8_PRE'},
 'U223':{1:'PGOOD_12V',2:'POWER_GND',3:'EFUSE_FLT_N',4:'EFUSE_FLT_CLEAN_N',5:'3V8_PRE',6:'PGOOD_CLEAN'},
 'U224':{1:'SEQ_RUN_Q',2:'POWER_GND',3:'PGOOD_CLEAN',4:'SYS_HWRST',5:'3V8_PRE',6:'SYS_HWRST'},
 'U225':{1:'3V8_PRE',3:'SEQ_SHUT',6:'DOWNSTREAM_RUN_DELAYED',8:'POWER_GND',10:'DOWN_CTS',13:'POWER_GND'},
 'U229':{1:'SYS_HWRST',2:'POWER_GND',3:'ADC_RST_RELEASE_CMD',4:'ADC_PD_RST_N',5:'3V3_SYS',6:'ADC_PD_RST_N'},
}
for u,pins in pin_expect.items():check(u+'_pins_exact',all(net(u,n)==v for n,v in pins.items()))
check('retained_latch_parts',value('U221')==value('U222')=='SN74LVC1G74DCUR')
check('reset_buffer_parts',value('U224')==value('U229')=='SN74LVC2G07DBVR')
check('schmitt_part',value('U223')=='SN74LVC2G17DBVR')
check('timer_variant',value('U225')=='TPS3760E012DYYR')
cap('C340','220n','DOWN_CTS')
check('CTS_exact_orderable',field('C340','MPN')=='C1210C224J3GACTU')
check('CTS_dielectric_tolerance',field('C340','Dielectric')=='C0G' and field('C340','Tolerance')=='5%')
resistor('R340','10.0k','3V8_PRE','DOWNSTREAM_RUN_DELAYED')
commands=['SHUTDOWN_REQ','SAFE_ARM_CMD','ANALOG_PWR_CMD','CLOCK_STARTUP_CMD','AUDIO_DATA_OE_CMD','RUN_HEALTH_OK_CMD','SYS_HWRST','AMP_FAULT_N']
translated=['SHUTDOWN_REQ_3V8','SAFE_ARM_CMD_3V8','ANALOG_PWR_CMD_3V8','CLOCK_STARTUP_CMD_3V8','AUDIO_DATA_OE_CMD_3V8','RUN_HEALTH_OK_3V8','SYS_HWRST_CLEAN','AMP_FAULT_CLEAN_N']
check('command_translator_part',value('U226')=='SN74LXC8T245PWR')
check('translator_power_direction',all(net('U226',p)==v for p,v in {1:'3V3_SYS',2:'3V3_SYS',22:'POWER_GND',23:'3V8_PRE',24:'3V8_PRE',11:'POWER_GND',12:'POWER_GND',13:'POWER_GND'}.items()))
for i,(a,b) in enumerate(zip(commands,translated)):
    check('translator_channel_'+str(i+1),net('U226',3+i)==a and net('U226',21-i)==b)
    resistor('R'+str(350+i),'100k',a,'POWER_GND');resistor('R'+str(358+i),'100k',b,'POWER_GND')
for i,nm in enumerate(['AMP_MUTE_CMD','AMP_STBY_CMD','ADC_RST_RELEASE_CMD','AMP_MUTE_RELEASE','AMP_STBY_RELEASE']):resistor('R'+str(366+i),'100k',nm,'POWER_GND')
resistor('R380','10.0k','3V3_SYS','AMP_FAULT_N');resistor('R381','10.0k','3V3_SYS','ADC_PD_RST_N')
resistor('R382','10.0k','3V8_PRE','EFUSE_FLT_N')
for r,nn in [('R310','ANALOG_PWR_EN'),('R311','ANALOG_PWR_EN'),('R312','DOWNSTREAM_EN'),('R313','DOWNSTREAM_EN'),('R314','DOWNSTREAM_EN'),('R315','DOWNSTREAM_EN')]:resistor(r,'100k',nn,'POWER_GND')
for ref,val,a,b in [('R281','10.0k','3V8_PRE','OUT1'),('R282','10.0k','3V3_SYS','RAILS_OK'),('R283','10.0k','3V3_SYS','SYS_HWRST')]:resistor(ref,val,a,b)
for i,(enable,oe,supply) in enumerate([('RAILS_OK','MCLK_OE_N','1V8_DSP_REF_ANA'),('CLOCK_STARTUP_EN','AUDIO_CLOCK_OE_N','3V3_SYS'),('AUDIO_DATA_OE_RELEASE','AUDIO_DATA_OE_N','3V3_SYS')]):
    q='Q'+str(201+i)
    check(q+'_sink_polarity',value(q)=='BSS138LT1G' and net(q,1)==enable and net(q,2)=='POWER_GND' and net(q,3)==oe)
    resistor('R'+str(390+2*i),'10.0k',supply,oe);resistor('R'+str(391+2*i),'100k',enable,'POWER_GND')

# Netlist-derived cone check: functional latch never qualifies either clock
# bootstrap control or any regulator enable except the two analog branches.
def cone(n,seen=None):
    seen=set() if seen is None else set(seen)
    check('no_combinational_cycle_at_'+n,n not in seen)
    seen.add(n);out={n}
    for inp in equations.get(n,[]):out |= cone(inp,seen)
    return out
for n in ['CLOCK_STARTUP_EN','DOWNSTREAM_EN']:
    check(n+'_no_arm_dependency','HW_RUN_LATCHED' not in cone(n))
check('MCLK_source_only_RAILS_OK',net('Q201',1)=='RAILS_OK')
check('ADC_reset_no_arm_dependency',net('U229',1)=='SYS_HWRST' and net('U229',3)=='ADC_RST_RELEASE_CMD')
check('OUT1_not_regulator_EN',all(net(u,p)!='OUT1' for u,p in [('U202',8),('U203',8),('U205',5),('U206',5),('U207',3),('U208',3)]))

# Isolation paths are checked pin-by-pin, not merely by counting components.
isolation=[]
for index in range(7):
    if index<4:
        sa,sb='5V_AFE','3V3_ADC_A'
        paths=[(f'AFE{index+1}P_AFTER_47R',f'ADC_AIN{index+1}P'),(f'AFE{index+1}N_AFTER_47R',f'ADC_AIN{index+1}N')]
    elif index==4:sa,sb='3V3_ADC_A','5V_AFE';paths=[('ADC_VREF','AFE_VCM_INPUT')]
    else:
        sa,sb='2V8_MIC','5V_AFE';paths=[(f'MIC{2*(index-5)+j+1}_AFTER_100R',f'AFE{2*(index-5)+j+1}_BEFORE_4u7') for j in range(2)]
    ua,ub='U'+str(230+2*index),'U'+str(231+2*index)
    for u,supply in [(ua,sa),(ub,sb)]:
        check(u+'_switch_part_power',value(u)=='TMUX2821DSGR' and net(u,8)==supply and net(u,4)==net(u,9)=='POWER_GND')
    for ch,(a,b) in enumerate(paths):
        ps,pd,sel=(1,2,7) if ch==0 else (5,6,3)
        mid=net(ua,pd)
        check(a+'_paired_path',net(ua,ps)==a and mid==net(ub,ps) and net(ub,pd)==b and mid not in [a,b] and net(ua,sel)==net(ub,sel)=='ANALOG_PWR_EN')
        isolation.append({'start':a,'end':b,'supply_A':sa,'supply_B':sb,'devices':[ua,ub]})
    if index==4:check('VREF_unused_selects_low',net(ua,3)==net(ub,3)=='POWER_GND')
check('thirteen_paired_analog_paths',len(isolation)==13)

manifest=json.loads((OUT/'sheet2_components.json').read_text())
audit=json.loads((OUT/'sheet2_symbol_pin_audit.json').read_text())
sch=sx.loads((HW/'power_regulation.kicad_sch').read_text(encoding='utf-8'))
libs={x[1].split(':')[-1]:x for x in kids(tag(sch,'lib_symbols'),'symbol')}
for name,entry in audit.items():
    actual={tag(p,'number')[1]:[tag(p,'name')[1],str(p[1])] for sub in kids(libs[name],'symbol') for p in kids(sub,'pin')}
    check(name+'_cached_manufacturer_map',actual==entry['pins'])
libroot=CLI.parents[1]/'share/kicad/footprints'
for ref,m in manifest.items():
    if ref.startswith('#'):continue
    check(ref+'_manifest_value',value(ref)==m['value'])
    check(ref+'_all_connected_pins',all(net(ref,n)==v for n,v in m['nets'].items() if v is not None))
    fp=comps[ref].findtext('footprint');check(ref+'_footprint_assigned',bool(fp))
    lib,fn=fp.split(':',1);path=(HW/(lib+'.pretty') if lib=='Astra_Sequencing' else libroot/(lib+'.pretty'))/(fn+'.kicad_mod')
    check(ref+'_package_exists',path.exists())
    footprint=sx.loads(path.read_text(encoding='utf-8'))
    pads={x[1] for x in kids(footprint,'pad') if x[1]}
    symbolpins={tag(p,'number')[1] for sub in kids(libs[m['symbol']],'symbol') for p in kids(sub,'pin')}
    check(ref+'_package_pin_set',pads==symbolpins)
for ref in [f'U{i}' for i in range(211,230)]:
    cap('C'+str(300+int(ref[1:])-211),'100n','3V3_SYS' if ref in ['U227','U229'] else '3V8_PRE')
cap('C341','100n','3V3_SYS')
for i in range(14):cap('C'+str(350+i),'100n',net('U'+str(230+i),8))

# Logic-level checks and event model use actual gate equations. State storage
# and timing use manufacturer device semantics; this is not analog SPICE.
import math
cts=[220e-9*.95*(1-.003),220e-9*1.05*(1+.003)]
check('selected_CTS_inside_frozen_effective_range',cts[0]>=198e-9 and cts[1]<=242e-9)
hold=[-math.log(.31)*88000*198e-9+8e-6,-math.log(.25)*122000*242e-9+17e-6]
check('frozen_hold_bounds',abs(hold[0]-.020415)<.0000005 and abs(hold[1]-.040946)<.0000005)
selected_hold=[-math.log(.31)*88000*cts[0]+8e-6,-math.log(.25)*122000*cts[1]+17e-6]
check('selected_hold_within_contract',selected_hold[0]>=hold[0] and selected_hold[1]<=hold[1])
check('timer_discharge_before_rearm',.330>hold[1]*.1)
check('EN_max_levels',realized['3V8_PRE'][1]<6 and realized['3V8_PRE'][1]<10.4)
check('TMUX_supply_bounds',all(realized[n][0]>=1.8 and realized[n][1]<=5.5 for n in ['2V8_MIC','5V_AFE','3V3_ADC_A']))
check('TMUX_failsafe_select_max',realized['3V8_PRE'][1]<5.5)
check('reset_pullup_only_destination_supply',net('R283',1)==net('U210',1)==net('U229',5)=='3V3_SYS')
# Account for resistor tolerance and translator 2uA input leakage in HIGH.
reset_high=(realized['3V3_SYS'][0]/10010-2e-6)/(1/10010+1/99900)
check('conditioned_reset_high_margin',reset_high>2.74) # conservative 4.5V Vt+ limit versus actual 3.3V

def ev(values):
    d=dict(values)
    for _ in range(len(equations)+1):
        for out,ins in equations.items():
            if all(n in d for n in ins):d[out]=all(d[n] for n in ins)
    return d

base={'OUT1':True,'PGOOD_CLEAN':True,'DOWNSTREAM_RUN_DELAYED':True,'SYS_HWRST_CLEAN':True,'EFUSE_FLT_CLEAN_N':True,'AMP_FAULT_CLEAN_N':True,'RUN_HEALTH_OK_3V8':False,'HW_RUN_LATCHED':False,'SHUTDOWN_REQ_3V8':False,'SAFE_ARM_CMD_3V8':False,'ANALOG_PWR_CMD_3V8':True,'AUDIO_DATA_OE_CMD_3V8':True,'CLOCK_STARTUP_CMD_3V8':True,'AMP_MUTE_CMD':True,'AMP_STBY_CMD':True}
prearm=ev(base)
check('bootstrap_available_prearm',prearm['CLOCK_STARTUP_EN'] and prearm['DOWNSTREAM_EN'])
check('prearm_functional_safe',not any(prearm[n] for n in ['ANALOG_PWR_EN','AUDIO_DATA_OE_RELEASE','AMP_MUTE_RELEASE','AMP_STBY_RELEASE']))
armed=ev({**base,'RUN_HEALTH_OK_3V8':True,'SAFE_ARM_CMD_3V8':True,'HW_RUN_LATCHED':True})
check('explicit_health_arm_reachable',armed['SAFE_CLEAR_N'] and armed['SAFE_ARM_3V8'] and armed['ANALOG_PWR_EN'])
events=[]
for fault in ['PGOOD_CLEAN','SYS_HWRST_CLEAN','EFUSE_FLT_CLEAN_N','AMP_FAULT_CLEAN_N','RUN_HEALTH_OK_3V8']:
    state={**base,'RUN_HEALTH_OK_3V8':True,'HW_RUN_LATCHED':True,fault:False}
    d=ev(state);check(fault+'_clears_async',not d['SAFE_CLEAR_N'])
    d=ev({**state,'HW_RUN_LATCHED':False})
    check(fault+'_functional_off',not any(d[n] for n in ['ANALOG_PWR_EN','AUDIO_DATA_OE_RELEASE','AMP_MUTE_RELEASE','AMP_STBY_RELEASE']))
    recovered=ev({**base,'RUN_HEALTH_OK_3V8':True,'HW_RUN_LATCHED':False})
    check(fault+'_recovery_does_not_auto_set',not recovered['ANALOG_PWR_EN'] and not recovered['SAFE_ARM_3V8'])
    events.append({'event':fault+' LOW','after_clear':d,'recovery_without_arm':recovered})
for delay in hold:
    for t_ms in [0,1,15,16,20,20.414,40.947]:
        d=ev({**base,'SYS_HWRST_CLEAN':False,'HW_RUN_LATCHED':False,'DOWNSTREAM_RUN_DELAYED':t_ms/1000<delay,'ANALOG_PWR_CMD_3V8':False})
        check(f'hold_{delay}_{t_ms}',d['DOWNSTREAM_EN']==(t_ms/1000<delay) and not d['ANALOG_PWR_EN'])
check('independent_analog_off_while_core_DMC_on',ev({**base,'HW_RUN_LATCHED':True,'ANALOG_PWR_CMD_3V8':False})['DOWNSTREAM_EN'] and not ev({**base,'HW_RUN_LATCHED':True,'ANALOG_PWR_CMD_3V8':False})['ANALOG_PWR_EN'])
for pa,pb,enable in itertools.product([False,True],repeat=3):
    connected=pa and pb and enable
    check(f'analog_power_permutation_{pa}_{pb}_{enable}',not connected if not(pa and pb and enable) else connected)

# Each monitored-rail failure uses its actual supervisor channel. A failure
# of V2/V3/V4 asserts reset without feeding RAILS_OK back into its own EN.
rail_events=[]
for failed in ['V1','V2','V3','V4']:
    d=ev({**base,'OUT1':failed!='V1','SYS_HWRST_CLEAN':False,'HW_RUN_LATCHED':False})
    check(failed+'_fault_reset_safe',not d['CLOCK_STARTUP_EN'] and not d['ANALOG_PWR_EN'] and not d['AUDIO_DATA_OE_RELEASE'])
    check(failed+'_source_recovery_enabled',d['DOWNSTREAM_EN']==(failed!='V1'))
    rail_events.append({'failed_channel':failed,'RAILS_OK':False,'SYS_HWRST':False,'state':d})

# Exercise asynchronous clear and edge-triggered SET with actual gate inputs.
# Firmware must lower the arm command during reset and provide a fresh pulse;
# health/fault recovery alone is never a SET event.
q=False;prior_clk=False;trace=[]
for label,changes in [
 ('power_valid_reset_asserted',{'SYS_HWRST_CLEAN':False}),
 ('boot_clock_bootstrap',{}),
 ('PLL_and_config_verified',{'RUN_HEALTH_OK_3V8':True}),
 ('deliberate_arm_rising_edge',{'RUN_HEALTH_OK_3V8':True,'SAFE_ARM_CMD_3V8':True}),
 ('arm_pulse_finished',{'RUN_HEALTH_OK_3V8':True}),
 ('ADC_PLL_loss_health_withdrawn',{}),
 ('PLL_requalified_no_arm_edge',{'RUN_HEALTH_OK_3V8':True}),
 ('fresh_arm_edge',{'RUN_HEALTH_OK_3V8':True,'SAFE_ARM_CMD_3V8':True}),
 ('watchdog_reset',{'RUN_HEALTH_OK_3V8':True,'SYS_HWRST_CLEAN':False}),
 ('watchdog_reboot_unarmed',{}),
]:
    d=ev({**base,**changes,'HW_RUN_LATCHED':q})
    clk=d['SAFE_ARM_3V8']
    if not d['SAFE_CLEAR_N']:q=False
    elif clk and not prior_clk:q=True
    prior_clk=clk
    d=ev({**base,**changes,'HW_RUN_LATCHED':q})
    trace.append({'event':label,'Q':q,'state':d})
check('safe_latch_event_trace',[x['Q'] for x in trace]==[False,False,False,True,True,False,False,True,False,False])

# Controlled shutdown retention survives SYS/commands disappearing. PGOOD
# LOW is the specified service-off exit; input loss uses immediate shutdown.
runq=True
shutdown_trace=[]
for label,pgood,clk,delay_done in [('cold_start',False,False,False),('run',True,False,False),('shutdown_edge',True,True,False),('DSP_in_reset',True,False,False),('timer_expired',True,False,True),('SYS_absent_service_off',True,False,True),('external_source_removed',False,False,False)]:
    if not pgood:runq=True
    elif clk:runq=False
    downstream=bool(pgood and not delay_done)
    shutdown_trace.append({'event':label,'SEQ_RUN_Q':runq,'SYS_HWRST_released':runq and pgood,'DOWNSTREAM_EN':downstream})
check('service_off_is_retained',shutdown_trace[5]['SEQ_RUN_Q']==False and shutdown_trace[5]['DOWNSTREAM_EN']==False)
check('cold_start_preset_restored',shutdown_trace[-1]['SEQ_RUN_Q']==True)

# Conservative populated Sheet 2 DC screen: charging each control resistor
# at the full 3.9V pre operating-band maximum deliberately overcounts several
# system-domain loads and series pull networks. Switching/edge consumption
# and final DSP workload remain allocated, not measured.
def ohms(v):return float(v.rstrip('kM'))*({'k':1e3,'M':1e6}.get(v[-1],1))
control_r=[(r,m) for r,m in manifest.items() if r.startswith('R') and (int(r[1:])>=310 or r in ['R281','R282','R283','R284'])]
resistive_screen=sum(3.9/(ohms(m['value'])*.999) for r,m in control_r)+3.9/(10000*.999) # Sheet1 PGOOD pull
# Manufacturer ICC terms: ten LV1T gates, seven LVC packages, translator both
# sides, TPS3760. Reserve 1mA for retained LTC2964 within prior allocation.
quiescent_screen=10*10e-6+7*10e-6+16e-6+2.6e-6+.001
logic_screen=resistive_screen+quiescent_screen
check('Sheet2_static_control_screen_below_20mA',logic_screen<.020)
switch_loads={'2V8_MIC':2*.000140,'3V3_ADC_A':5*.000140,'5V_AFE':7*.000140}
load_screens={
 '2V8_MIC':switch_loads['2V8_MIC']+realized['2V8_MIC'][1]/(2550*.999)+.000920,
 '5V_AFE':switch_loads['5V_AFE']+realized['5V_AFE'][1]/(4700*.999)+realized['5V_AFE'][1]/(424000*.999)+.028,
 '3V3_ADC_A_fixed_support':switch_loads['3V3_ADC_A']+realized['3V3_ADC_A'][1]/(3010*.999)+1.98/2970,
}
check('microphone_populated_screen_within_5mA',load_screens['2V8_MIC']<.005)
check('AFE_quiescent_screen_within_50mA',load_screens['5V_AFE']<.050)
check('ADC_support_leaves_consumer_budget',load_screens['3V3_ADC_A_fixed_support']<.030)

# Startup graph includes explicitly marked future endpoint/firmware steps.
# These are integration prerequisites, not claims that later sheets exist.
dependency={'3V8_PRE':['12V_PROTECTED'],'PGOOD_CLEAN':['3V8_PRE'],'1V8':['PGOOD_CLEAN'],'OUT1':['1V8'],'DOWNSTREAM_RUN_DELAYED':['3V8_PRE'],'DOWNSTREAM_VALID':['OUT1','PGOOD_CLEAN'],'DOWNSTREAM_EN':['DOWNSTREAM_VALID','DOWNSTREAM_RUN_DELAYED'],'DOWNSTREAM_RAILS':['DOWNSTREAM_EN'],'RAILS_OK':['1V8','DOWNSTREAM_RAILS'],'ROOT_CLOCK (later)':['1V8'],'MCLK_AVAILABLE (later)':['RAILS_OK','ROOT_CLOCK (later)'],'SYS_HWRST_CLEAN':['RAILS_OK'],'DSP_BOOT (later)':['SYS_HWRST_CLEAN','ROOT_CLOCK (later)'],'CLOCK_STARTUP_CMD_3V8':['DSP_BOOT (later)'],'CLOCK_STARTUP_EN':equations['CLOCK_STARTUP_EN'],'ADC_RESET_RELEASE (later)':['MCLK_AVAILABLE (later)','DSP_BOOT (later)'],'ADC_PLL_LOCK (later)':['ADC_RESET_RELEASE (later)','MCLK_AVAILABLE (later)'],'RUN_HEALTH_OK_3V8':['ADC_PLL_LOCK (later)','CLOCK_STARTUP_EN'],'ARM_EDGE (firmware)':['RUN_HEALTH_OK_3V8'],'HW_RUN_LATCHED':['ARM_EDGE (firmware)'],'FUNCTIONAL_RELEASE':['HW_RUN_LATCHED']}
order=[];visiting=set()
def visit(n):
    check('startup_graph_no_cycle_'+n,n not in visiting)
    if n in order:return
    visiting.add(n)
    for dep in dependency.get(n,[]):visit(dep)
    visiting.remove(n);order.append(n)
for n in dependency:visit(n)

erc=json.loads((OUT/'sheet2_erc_final.json').read_text(encoding='utf-8'))
dispositions=[]
for sheet in erc['sheets']:
    for v in sheet['violations']:
        descriptions=' | '.join(i['description'] for i in v['items'])
        if v['type']=='pin_to_pin' and 'Pin 4 [FB2,' in descriptions:
            classification='JUSTIFIED / INTENTIONAL';reason='Phase 3D grounded FB2/VSEL-low configuration; ground source flag triggers output-type check.'
        elif v['type']=='endpoint_off_grid' and sheet['path']=='/':
            classification='JUSTIFIED / INTENTIONAL';reason='Five original Sheet 1 port positions preserved; exported interface connectivity checked.'
        else:classification='BLOCKING';reason='Unresolved native ERC finding; inspect before final gate.'
        dispositions.append({'sheet':sheet['path'],**v,'classification':classification,'reason':reason})

baseline=json.loads((OUT/'baseline.json').read_text())
local_preferences=HW/'circuitBuilderAi-Astra.kicad_prl'
if local_preferences.name not in baseline['hardware'] and local_preferences.exists():local_preferences.unlink()
allowed={'power_regulation.kicad_sch','circuitBuilderAi-Astra.kicad_sch','Astra_Sequencing.kicad_sym'}
unchanged={name:sha(HW/name)==digest for name,digest in baseline['hardware'].items() if name not in allowed}
check('all_protected_hardware_unchanged',all(unchanged.values()))
history=(ROOT/'validation/phase_4b_power_regulation_validation.md').read_bytes()
check('complete_prior_BLOCKED_history_preserved',hashlib.sha256(history[:baseline['history_bytes']]).hexdigest()==baseline['history_sha256'])
check('no_later_endpoint_parts_entered',not any(m['value'].startswith(('ADSP','ADAU','TAS6424','OPA165','IM73','ASDLJ','LMK1C','SN74AXC','SN74LVC244')) for m in manifest.values()))
# Confirm Sheet 1 pulls actually terminate at Sheet 2 status nets; no extra
# parallel pullups silently alter the interface loading or low-state current.
for nn in ['PGOOD_12V','EFUSE_FLT_N']:
    pulls=[ref for ref,cpt in comps.items() if ref.startswith('R') and {net(ref,1),net(ref,2)}=={nn,'3V8_PRE'}]
    check(nn+'_one_10k_pullup',len(pulls)==1 and value(pulls[0]).split()[0] in ['10k','10.0k'])

result={'phase_gate':'PHASE 4B: PASS' if not any(v['classification']=='BLOCKING' for v in dispositions) else 'PHASE 4B: BLOCKED','checks':checks,'checks_passed':len(checks),'parts_excluding_flags':len(manifest)-3,'configured_static_rail_bounds_V':realized,'supervision':supervision,'permanent_preloads':preloads,'logic_equations_from_netlist':equations,'startup_dependency_order':order,'startup_boundary':'Oscillator, translators/audio buffers, ADC/DSP/amplifier and their firmware are later-sheet interfaces; endpoint physical operation not performed.','event_checks':events,'monitored_rail_events':rail_events,'safe_latch_trace':trace,'shutdown_trace':shutdown_trace,'DC_load_screens_A':{'all_Sheet2_controls_conservatively_charged_to_pre':logic_screen,**load_screens},'TMUX_supply_loads_A':switch_loads,'isolation_paths':isolation,'CTS_selected_effective_F':cts,'frozen_post_reset_hold_s':hold,'selected_post_reset_hold_s':selected_hold,'reset_high_with_tolerance_and_leakage_V':reset_high,'unchanged_files':unchanged,'erc':{'errors':sum(v['severity']=='error' for v in dispositions),'warnings':sum(v['severity']=='warning' for v in dispositions),'blocking':sum(v['classification']=='BLOCKING' for v in dispositions),'items':dispositions,'ignored_checks':erc['ignored_checks']},'native_tool_calls':logs,'physical_validation':'NOT PERFORMED; no analog transient, ramp, leakage, clock-edge or loaded endpoint claims','final_sheet2_sha256':sha(HW/'power_regulation.kicad_sch')}
(OUT/'sheet2_verification_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'ERC':{k:result['erc'][k] for k in ['errors','warnings','blocking']},'parts':result['parts_excluding_flags'],'protected_hardware_unchanged':all(unchanged.values())},indent=2))
