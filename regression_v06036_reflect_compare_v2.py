import ast
import re
from pathlib import Path
src=Path('app.py').read_text()
tree=ast.parse(src)
names={'sim_time_label','_trace_time','_reasoning_present','_perfusion_response_direction','_expected_response_prompt','_model_shift_prompt','_critical_adaptation_prompt','_reasoning_data_alignment_prompt','_reflect_compare_items'}
# Review matching now resolves explicit expectation clauses and antibiotic-only
# timing using these production helpers. Keep this isolated AST harness complete.
names.update({'_review_expectation_text', '_immediate_expectation_text', '_action_types_for_event', '_trace_observable_delta'})
module=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns={'re': re}
exec(compile(module,'reflect_extract','exec'),ns)

def state(sbp,dbp,crt,ext='warm',mental='alert'):
    return {'observable':{'sbp':sbp,'dbp':dbp,'crt':crt,'extremities':ext,'mental_status':mental}}
trace=[
 {'execution_status':'executed','decision_time_min':5,'reasoning':{'problem_representation':'remaining perfusion abnormality with reduced effective circulating volume','rationale':'reduced effective circulating volume is contributing'},'state_before':state(121,76,2),'state_after':state(118,74,2)},
 {'execution_status':'executed','decision_time_min':15,'reasoning':{'management_priority':'determine whether the patient remains fluid responsive','expected_effect':'further improvement in perfusion','reassessment_target':'perfusion'},'state_before':state(118,74,2),'state_after':state(111,70,3)},
 {'execution_status':'executed','decision_time_min':25,'reasoning':{'problem_representation':'ongoing hypoperfusion with another cause of shock','rationale':'another cause of shock is driving the ongoing hypoperfusion'},'state_before':state(111,70,3),'state_after':state(102,65,4)},
]
items=ns['_reflect_compare_items'](trace)
text=' '.join(str(x) for x in items)
assert 'Expected effect vs observed response' in text, items
assert 'blood pressure decreased from 118/74 to 111/70' in text, items
assert 'capillary refill prolonged from 2 to 3 seconds' in text, items
assert 'Working model shift' in text, items
assert 'subsequently available diagnostic information' in text, items
assert 'correct' not in text.lower() and 'incorrect' not in text.lower(), items
print('PASS v0.6.0.36 Reflect & Compare v2')
