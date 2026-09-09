import ast, re
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

source = Path('app.py').read_text()
tree = ast.parse(source)
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
ss = {'state': {'treatments': {'dobutamine': False, 'norepinephrine': False}},
      'last_executed_action': {'type':'fluid','fluid_type':'Normal saline','volume_ml':1000,'rate':'standard'}}
class Session(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
st = SimpleNamespace(session_state=Session(ss))
ns={'re':re,'deepcopy':deepcopy,'st':st}
exec(compile(module,'v06035_extract','exec'),ns)
clinical=ns['clinical_interpreter']; contextual=ns['parse_contextual_followup']

def production_parse(text):
    direct=clinical(text)
    non=[a for a in direct.get('actions',[]) if a.get('type')!='reassessment']
    if non: return direct
    ctx=contextual(text)
    if ctx:
        ctx['reasoning']=direct.get('reasoning',{})
        reassess=[a for a in direct.get('actions',[]) if a.get('type')=='reassessment']
        ctx['actions']=[a for a in ctx.get('actions',[]) if a.get('type')!='reassessment']+reassess
        return ctx
    return direct

text3='The response to the first fluid bolus was limited. My management priority is to determine whether the patient remains fluid responsive. Give another 1000 mL NS IV. I expect further improvement in perfusion if low preload is still important. Reassess perfusion in 10 min.'
p=production_parse(text3)
assert p['reasoning'].get('management_priority')=='determine whether the patient remains fluid responsive', p
assert p['reasoning'].get('expected_effect')=='further improvement in perfusion', p
assert p['reasoning'].get('reassessment_target')=='perfusion', p
assert [a['type'] for a in p['actions']]==['fluid','reassessment'], p
assert p['actions'][0]['volume_ml']==1000, p
assert p['actions'][1]['delay_min']==10, p

text4='The patient is deteriorating despite rhythm control and fluids. My working model is that another cause of shock is driving the ongoing hypoperfusion. Perform POCUS and obtain lactate and basic laboratory tests to better characterize the shock state. Reassess in 10 min.'
p4=production_parse(text4)
assert not any(a['type']=='fluid' for a in p4['actions']), p4
assert [a['type'] for a in p4['actions']]==['reassessment','pocus','lactate','basic_labs'], p4
assert p4['reasoning'].get('problem_representation'), p4
print('PASS: v0.6.0.35 production parse pipeline preserves reasoning + reassessment and isolates turns')
