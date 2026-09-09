import ast
import re
from pathlib import Path

src = Path("app.py").read_text()
assert 'Complete Encounter & Begin Review' in src
assert '## Management Trace' in src
assert 'st.session_state.encounter_ended = False' in src
assert '"Management reasoning"' in src
assert '"Observed response"' in src
assert 'reasoning you explicitly stated' in src
assert 'does not score decisions' in src

tree=ast.parse(src)
names={"_trace_time","_trace_state_text","_trace_reasoning_text","_trace_action_text","_summary_source_position","_summaries_in_learner_order","management_trace_rows"}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={"sim_time_label": lambda m: f"{m//60:02d}:{m%60:02d}", "re": re}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"trace_subset","exec"),ns)

event={
 "execution_status":"executed","decision_time_min":15,
 "reasoning":{"problem_representation":"cold and poorly perfused","management_priority":"improve forward flow","expected_effect":"improve cardiac output"},
 "action_summaries":[{"support_type":"dobutamine","operation":"start","rate":5,"units":"mcg/kg/min"}],
 "state_before":{"observable":{"sbp":130,"dbp":87,"hr":97,"rhythm":"Sinus rhythm","crt":2,"extremities":"Warm","mental_status":"Alert","spo2":93},
               "physiology":{"forward_flow_state":0.1,"tissue_perfusion":0.1}},
 "state_after":{"observable":{"sbp":116,"dbp":69,"hr":98,"rhythm":"Sinus rhythm","crt":2,"extremities":"Warm","mental_status":"Alert","spo2":93},
              "physiology":{"forward_flow_state":0.9,"tissue_perfusion":0.9}},
}
rows=ns["management_trace_rows"]([event])
assert len(rows)==1
r=rows[0]
assert r["Time"]=="00:15"
assert "130/87" in r["Patient state"]
assert "cold and poorly perfused" in r["Management reasoning"]
assert "improve forward flow" in r["Management reasoning"]
assert "dobutamine 5 mcg/kg/min" in r["Action"]
assert "116/69" in r["Observed response"]
# Hidden physiology must never leak to learner row.
rendered=" ".join(r.values())
assert "forward_flow_state" not in rendered and "tissue_perfusion" not in rendered
assert "0.9" not in rendered
# No stated reasoning remains blank/dash.
event2=dict(event); event2["reasoning"]={}
assert ns["_trace_reasoning_text"]({})=="—"
print("PASS: v0.6.0.24 learner-facing post-encounter Management Trace")
