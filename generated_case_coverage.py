"""Authoring-only checks for missing executable management paths.

Reject incomplete new cases rather than fabricate response curves at runtime.
Frozen earlier cases remain replayable under their original declarations.
"""
import re
from family_parser import _AGENTS, _normalize


def coverage_issues(case):
    rules = case.get('engine', {}).get('response_rules', [])
    kinds = {r.get('action_type') for r in rules}
    missing = []
    engine = case.get('engine',{})
    if 'pocus' in case.get('investigations',{}) and 'pocus' not in engine.get('stable_diagnostics',[]) and not any('pocus' in (r.get('diagnostic_updates') or {}) for r in engine.get('state_rules',[])):
        missing.append('POCUS: author state-dependent findings or explicitly declare stable_diagnostics')
    for r in rules:
        if r.get('action_type') in {'norepinephrine','dobutamine','nitroglycerin'} and r.get('washout_min') is None:
            missing.append(r['action_type'] + ': explicit infusion washout')
        if r.get('action_type') in {'beta_blocker','diltiazem','amiodarone'} and r.get('recovery_min') is None:
            missing.append(r['action_type'] + ': explicit recovery')
        if r.get('action_type') == 'fluid' and r.get('state_gain') is None:
            missing.append('fluid: explicit state-dependent response curve')
        if r.get('action_type') == 'procedural_sedation' and any(r.get(k) is None for k in ('recovery_min','mental_status_during','mental_status_threshold')):
            missing.append('sedation: explicit recovery, mental status and exposure threshold')
    vent = [r for r in rules if r.get('action_type') == 'ventilator_adjustment' and r.get('interpolate_settings') is True]
    if 'intubation' in kinds:
        points = {tuple(sorted((r.get('settings') or {}).items())) for r in vent}
        fi = {dict(point).get('fio2_percent') for point in points}
        peep = {dict(point).get('peep_cmh2o') for point in points}
        if len(fi) < 2 or len(peep) < 2 or None in fi | peep or len(points) != len(fi) * len(peep) or len(vent) != len(points) or len({(r.get('onset_min'), r.get('duration_min'), r.get('max_exposure')) for r in vent}) != 1:
            missing.append('ventilation: at least four response anchors covering an FiO2/PEEP grid')
    if 'fluid' not in kinds:
        missing.append('fluid')
    if case.get('observable', {}).get('spo2', 100) < 94 or 'oxygen' in kinds:
        devices = {str(r.get('device', '')).lower() for r in rules if r.get('action_type') == 'oxygen'}
        missing.extend('oxygen: ' + d for d in ('nasal cannula', 'simple mask', 'non-rebreather mask') if d not in devices)
    # The author's own proposed management paths must be executable. History and
    # learner reasoning are deliberately excluded from this authoring contract.
    paths = _normalize(' '.join(case.get('faculty', {}).get('anticipated_management_paths', [])))
    for kind, agents in _AGENTS.items():
        for agent, pattern in agents.items():
            if re.search(r'\b(?:' + pattern + r')\b', paths) and not any(r.get('action_type') == kind and r.get('agent') == agent for r in rules):
                missing.append(kind + ': ' + agent)
    for kind, pattern in [('cardioversion', r'cardioversion|cardiovert'), ('niv', r'bipap|cpap|niv'), ('intubation', r'intubation|intubate'), ('norepinephrine', r'norepinephrine|noradrenalina'), ('dobutamine', r'dobutamine|dobutamina')]:
        if re.search(r'\b(?:' + pattern + r')\b', paths) and kind not in kinds:
            missing.append(kind)
    return [{'code': 'MANAGEMENT_COVERAGE', 'path': 'engine.response_rules',
             'message': 'The new case is missing executable responses for plausible or explicitly authored management paths. Author patient-specific effects, including harm or no benefit where appropriate.',
             'details': {'missing': missing}}] if missing else []
