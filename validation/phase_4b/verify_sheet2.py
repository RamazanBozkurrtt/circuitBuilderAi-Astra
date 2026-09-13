"""Audit the KiCad-exported connectivity against the frozen Sheet 2 values.

This deliberately returns a BLOCKED engineering result: the retained shutdown
order is not realizable with the frozen common OUT1 connection. It does not
simulate regulators or claim physical validation. Run from any directory.
"""
from pathlib import Path
import json, hashlib, itertools, os, subprocess, shutil, tempfile
import xml.etree.ElementTree as ET
import sexpdata as sx

ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware/kicad'; OUT=ROOT/'validation/phase_4b'
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

buck=[('U201','3V8_PRE','12V_PROTECTED','12V_PROTECTED',201,'44.2k',44200),('U202','1V0_DSP_CORE','3V8_PRE','OUT1',211,'4.32k',4320),('U203','3V3_SYS','12V_PROTECTED','EN_3V3_SYS',221,'37.1k',37100)]
realized={}
for u,rail,vin,en,b,rt,rtv in buck:
    resistor('R'+str(b),rt,rail,rail+'_FB');resistor('R'+str(b+1),'10.0k',rail+'_FB','POWER_GND')
    expected={1:vin,2:rail+'_SW',3:'POWER_GND',4:'POWER_GND',5:rail+'_FB',6:rail,8:en,9:rail+'_SS',10:vin,11:'POWER_GND'}
    check(u+'_pin_nets',all(net(u,n)==v for n,v in expected.items()))
    check(u+'_part',value(u)=='TPS62135RGXR')
    cap('C'+str(b+1),'10n',rail+'_SS');cap('C'+str(b),'10u',vin)
    check(u+'_inductor',net('L'+u[1:],1)==rail+'_SW' and net('L'+u[1:],2)==rail and value('L'+u[1:])=='1u')
    realized[rail]=[.7*.99*(1+rtv*.999/(10000*1.001))-70e-9*rtv*.999,.7*1.01*(1+rtv*1.001/(10000*.999))+70e-9*rtv*1.001]

ldos=[('U204','1V8_DSP_REF_ANA','3V8_PRE','PGOOD_12V',231,54300,'1.69k',1690,'47n'),('U205','1V35_DSP_DMC','3V8_PRE','OUT1',241,14900,'1.24k',1240,'47n'),('U206','5V_AFE','12V_PROTECTED','AFE_EN',251,324000,'4.70k',4700,'10n')]
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
    check(u+'_pin_nets',all(net(u,n)==vv for n,vv in {1:'3V8_PRE',2:'POWER_GND',3:'OUT1',5:rail}.items()))
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
check('system_and_gate',all(net('U211',p)==v for p,v in {1:'OUT1',2:'PGOOD_12V',3:'POWER_GND',4:'EN_3V3_SYS',5:'3V8_PRE'}.items()))
for ref,val,a,b in [('R281','10.0k','3V8_PRE','OUT1'),('R282','10.0k','3V3_SYS','RAILS_OK'),('R283','10.0k','3V3_SYS','SYS_HWRST'),('R285','1.0M','EN_3V3_SYS','POWER_GND'),('R310','100k','AFE_EN','POWER_GND')]:resistor(ref,val,a,b)

# Independent audit of native cached symbols against the manufacturer pin maps.
sch=sx.loads((HW/'power_regulation.kicad_sch').read_text(encoding='utf-8'))
audit=json.loads((OUT/'sheet2_symbol_pin_audit.json').read_text())
libs={x[1].split(':')[-1]:x for x in kids(tag(sch,'lib_symbols'),'symbol')}
for name,entry in audit.items():
    actual={tag(p,'number')[1]:[tag(p,'name')[1],str(p[1])] for sub in kids(libs[name],'symbol') for p in kids(sub,'pin')}
    check(name+'_pin_map',actual==entry['pins'])
    check(name+'_footprint_name',next(p[2] for p in kids(libs[name],'property') if p[1]=='Footprint')==entry['footprint'])
libroot=CLI.parents[1]/'share/kicad/footprints'
for ref,c in comps.items():
    if not ref.startswith(('U2','R2','R3','C2','L2','TP2')):continue
    fp=c.findtext('footprint')
    if not fp:continue
    lib,fn=fp.split(':',1)
    path=(HW/(lib+'.pretty') if lib=='Astra_Sequencing' else libroot/(lib+'.pretty'))/(fn+'.kicad_mod')
    check(ref+'_footprint_exists',path.exists())
    if ref in ['U201','U202','U203','U204','U205','U206','U207','U208','U209','U210','U211']:
        footprint=sx.loads(path.read_text(encoding='utf-8'))
        pads={x[1] for x in kids(footprint,'pad') if x[1]}
        expected=set(audit[json.loads((OUT/'sheet2_components.json').read_text())[ref]['symbol']]['pins'])
        check(ref+'_package_pad_numbers',pads==expected)

baseline=json.loads((OUT/'sheet2_baseline_hashes.json').read_text())
unchanged={name:sha(HW/name)==digest for name,digest in baseline.items() if name.endswith('.kicad_sch') and name not in ['circuitBuilderAi-Astra.kicad_sch','power_regulation.kicad_sch']}
unchanged['Astra_Power.kicad_sym']=sha(HW/'Astra_Power.kicad_sym')==baseline['Astra_Power.kicad_sym']
check('Sheet1_later_sheets_and_Sheet1_library_unchanged',all(unchanged.values()))

# Actual common enable net is the blocker; stored truth table is exhaustive.
check('frozen_common_enable_is_implemented',len({net('U208',3),net('U207',3),net('U202',8),net('U205',5)})==1)
truth=[{'OUT1':v,'microphone_enable':v,'ADC_enable':v,'core_enable':v,'DMC_enable':v,'microphones_off_while_core_DMC_enabled':v==0 and v==1} for v in [0,1]]
check('required_commanded_shutdown_state_unreachable',not any(r['microphones_off_while_core_DMC_enabled'] for r in truth))
erc=json.loads((OUT/'sheet2_erc_final.json').read_text(encoding='utf-8'))
violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
result={'phase_gate':'PHASE 4B: BLOCKED','implemented_component_count_excluding_power_flags':sum(not ref.startswith('#') for ref in json.loads((OUT/'sheet2_components.json').read_text())),'checks':checks,'configured_static_rail_bounds_V':realized,'supervision':supervision,'permanent_preloads':preloads,'unchanged_files':unchanged,'commanded_shutdown_truth_table':truth,'blocking_finding':'Shared OUT1 cannot disable microphone power before core and DMC; Phase 3D 9.1(5)/11(6) conflicts with retained 9.2/Phase 3 6.3 order. No separate shutdown controls are approved.','incomplete':['hardware-safe latch and independent fault aggregation','AFE buffered-command / open-drain override','commanded-shutdown control','consumer-side filtering and loads on unimplemented later sheets'],'physical_validation':'NOT PERFORMED; not the reason for this gate','erc':{'errors':sum(v['severity']=='error' for v in violations),'warnings':sum(v['severity']=='warning' for v in violations),'excluded_checks':erc.get('ignored_checks',[])},'native_tool_calls':logs,'final_sheet2_sha256':sha(HW/'power_regulation.kicad_sch')}
prior_path=OUT/'sheet2_verification_results.json'
if prior_path.exists():
    history=json.loads(prior_path.read_text()).get('validation_history_preservation')
    if history:
        prefix=(ROOT/'validation/phase_4b_power_regulation_validation.md').read_bytes()[:history['prior_bytes']]
        assert hashlib.sha256(prefix).hexdigest()==history['prior_sha256']
        result['validation_history_preservation']=history
prior_path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'ERC':result['erc'],'phase_gate':result['phase_gate'],'unchanged':unchanged},indent=2))
