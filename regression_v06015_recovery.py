#!/usr/bin/env python3
import ast
from pathlib import Path
from copy import deepcopy
APP=Path(__file__).with_name("app.py")
tree=ast.parse(APP.read_text()); selected=[]
for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom)):
        if isinstance(node,ast.Import) and any(a.name=="streamlit" for a in node.names): continue
        selected.append(node)
    elif isinstance(node,(ast.FunctionDef,ast.Assign)):
        if isinstance(node,ast.Assign):
            targets=[getattr(x,"id",None) for x in node.targets]
            if not any(x in {"INITIAL_STATE","PRESENTATION"} for x in targets): continue
        selected.append(node)
ns={}; exec(compile(ast.Module(body=selected,type_ignores=[]),str(APP),"exec"),ns)
s=deepcopy(ns["INITIAL_STATE"]); h=s["hidden"]; o=s["observable"]
o.update({"sbp":122,"dbp":84,"hr":101,"rhythm":"Sinus rhythm","crt":5,"extremities":"Cool","mental_status":"Drowsy","spo2":90})
h.update({"tissue_perfusion":0.35,"cardiac_output_index":0.40,"peripheral_recovery_minutes":0.0})
s["treatments"].update({"norepinephrine":True,"norepinephrine_rate":0.4,"norepinephrine_units":"mcg/kg/min","dobutamine":True,"dobutamine_rate":5.0,"dobutamine_units":"mcg/kg/min"})
# Isolate the surface: sustained CRT-4 range should warm only after a delay.
for i in range(17):
    h.update({"tissue_perfusion":0.35,"cardiac_output_index":0.40,"dobutamine_effect":0.7,"vascular_support":0.65})
    ns["update_perfusion_surface"](s)
assert o["extremities"] == "Cool", (o,h["peripheral_recovery_minutes"],h["peripheral_flow"])
h.update({"tissue_perfusion":0.35,"cardiac_output_index":0.40,"dobutamine_effect":0.7,"vascular_support":0.65})
ns["update_perfusion_surface"](s)
assert o["crt"] == 4, (o,h["peripheral_flow"])
assert o["extremities"] == "Warmer", (o,h["peripheral_recovery_minutes"],h["peripheral_flow"])
print("PASS v0.6.0.15 delayed peripheral recovery regression")
