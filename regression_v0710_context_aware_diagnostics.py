import ast
import math
import random
import re
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text()
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert "diagnostics = _trace_diagnostic_results(event)" in source

tree = ast.parse(source)
nodes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in {"INITIAL_STATE", "PRESENTATION", "PS002_PRESENTATION", "CASE_CONFIGS"} for name in names):
            nodes.append(node)


class SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class FakeStreamlit:
    def __init__(self):
        self.session_state = SessionState()


st = FakeStreamlit()
namespace = {"st": st, "re": re, "math": math, "random": random, "deepcopy": deepcopy}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0710_subset", "exec"), namespace)
st.session_state.state = namespace["build_ps002_state"]()
st.session_state.last_executed_action = None


# Numeric decimals and their units must survive sentence-boundary matching.
reasoning_text = (
    "Despite adequate oxygenation, the patient has worsening shock with BP 94/54, capillary refill "
    "7 seconds, very cold extremities, and lactate 5.4 mmol/L. My priority is to improve perfusion. "
    "Increase norepinephrine to 0.2 mcg/kg/min and reassess perfusion in 10 minutes."
)
parsed = namespace["clinical_interpreter"](reasoning_text)
assert parsed["reasoning"]["problem_representation"] == (
    "worsening shock with BP 94/54, capillary refill 7 seconds, very cold extremities, "
    "and lactate 5.4 mmol/L"
), parsed["reasoning"]
assert parsed["reasoning"]["management_priority"] == "improve perfusion"


# POCUS must describe the IVC in the context in which it was acquired.
spontaneous = namespace["build_ps002_state"]()
spontaneous["hidden"]["preload_state"] = 0.40
spontaneous_pocus = namespace["pocus_transition"](spontaneous)["result"]
assert "with >50% respiratory variation" in spontaneous_pocus["ivc"], spontaneous_pocus

niv = namespace["build_ps002_state"]()
niv["hidden"]["preload_state"] = 0.40
niv["treatments"].update({"niv": True, "niv_mode": "BiPAP", "niv_ipap_cmh2o": 18.0, "niv_epap_cmh2o": 6.0})
niv_pocus = namespace["pocus_transition"](niv)["result"]
assert "noninvasive positive-pressure support" in niv_pocus["ivc"], niv_pocus
assert "standalone preload marker" in niv_pocus["ivc"], niv_pocus

ventilated = namespace["build_ps002_state"]()
ventilated["hidden"]["preload_state"] = 0.40
ventilated["treatments"].update({
    "invasive_ventilation": True,
    "ventilator_mode": "VC/AC",
    "ventilator_fio2_percent": 60.0,
    "ventilator_peep_cmh2o": 14.0,
})
ventilated["sim_time"] = 80
pocus_summary = namespace["pocus_transition"](ventilated)
ivc_text = pocus_summary["result"]["ivc"]
assert "positive-pressure ventilation" in ivc_text, ivc_text
assert "PEEP 14 cm H₂O" in ivc_text, ivc_text
assert "standalone preload marker" in ivc_text, ivc_text
assert ">50% respiratory variation" not in ivc_text, ivc_text


# Results belong to the same decision's Observed response, including the last
# decision in a trace where no subsequent state card exists.
lactate_summary = namespace["lactate_transition"](ventilated)
abg_summary = namespace["abg_transition"](ventilated)
event = {
    "response_time_min": 85,
    "action_summaries": [pocus_summary, lactate_summary, abg_summary],
}
diagnostic_results = namespace["_trace_diagnostic_results"](event)
rendered = " ".join(text for _, text in diagnostic_results)
assert len(diagnostic_results) == 3, diagnostic_results
assert "POCUS:" in rendered and "PEEP 14 cm H₂O" in rendered, rendered
assert "Lactate:" in rendered and "mmol/L" in rendered, rendered
assert "ABG:" in rendered and "P/F ratio" in rendered, rendered
assert all(time_text.startswith("01:") for time_text, _ in diagnostic_results), diagnostic_results

print("PASS: v0.7.10 decimal-safe reasoning and context-aware diagnostic responses")
