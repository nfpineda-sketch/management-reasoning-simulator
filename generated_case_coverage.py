"""Authoring-only checks for missing executable management paths.

Reject incomplete new cases rather than fabricate response curves at runtime.
Saved earlier case records remain intact; production requires a native profile.
"""
import re
from family_parser import _AGENTS, _normalize


def coverage_issues(case):
    rules = case.get('engine', {}).get('response_rules', [])
    if case.get('engine',{}).get('core_profile'):
        from coupled_encounter import native
        paths=_normalize(' '.join(case.get('faculty',{}).get('anticipated_management_paths',[])))
        missing=[]
        for kind,agents in _AGENTS.items():
            for agent,pattern in agents.items():
                if native({'type':kind,'agent':agent,'route':'IV'}):
                    continue
                if re.search(r'\b(?:'+pattern+r')\b',paths) and not any(r.get('action_type')==kind and r.get('agent')==agent for r in rules):
                    missing.append(kind+': '+agent)
        return [{'code':'MANAGEMENT_COVERAGE','path':'engine.response_rules','message':'Declare responses for disease-specific treatments outside the shared main/IA core.','details':{'missing':missing}}] if missing else []
    kinds = {r.get('action_type') for r in rules}
    missing = []
    engine = case.get('engine',{})
    if 'pocus' in case.get('investigations',{}) and 'pocus' not in engine.get('stable_diagnostics',[]) and not any('pocus' in (r.get('diagnostic_updates') or {}) for r in engine.get('state_rules',[])):
        missing.append('POCUS: author state-dependent findings or explicitly declare stable_diagnostics')
    for r in rules:
        if r.get('action_type') == 'cardioversion' and (not r.get('rhythm_before') or not r.get('rhythm_after')):
            missing.append('cardioversion: explicit pre- and post-shock rhythms')
        if r.get('action_type') in {'norepinephrine','dobutamine','nitroglycerin'} and r.get('washout_min') is None:
            missing.append(r['action_type'] + ': explicit infusion washout')
        if r.get('action_type') in {'beta_blocker','diltiazem','amiodarone'} and r.get('recovery_min') is None:
            missing.append(r['action_type'] + ': explicit recovery')
        if r.get('action_type') == 'fluid' and r.get('state_gain') is None:
            missing.append('fluid: explicit state-dependent response curve')
        if r.get('action_type') == 'procedural_sedation' and any(r.get(k) is None for k in ('recovery_min','mental_status_during','mental_status_threshold')):
            missing.append('sedation: explicit recovery, mental status and exposure threshold')
    if engine.get('volume_model') is None:
        missing.append('fluid: explicit volume compartments')
    elif not {'circulating','extravascular'} <= {r.get('volume_basis') for r in rules if r.get('action_type') == 'fluid'}:
        missing.append('fluid: circulating and extravascular responses')
    for r in rules:
        if r.get('action_type') in {'beta_blocker','diltiazem','amiodarone'} and r.get('exposure_curve') is None:
            missing.append(r['action_type'] + ': active-load response curve')
        if r.get('action_type') == 'diuretic' and r.get('diuresis_ml_min') is None:
            missing.append('diuretic: volume removal and recovery')
    from generated_rhythm import rhythm_key
    shocks = [r for r in rules if r.get('action_type') == 'cardioversion']
    shock_keys = [(rhythm_key(r.get('rhythm_before')), (r.get('settings') or {}).get('energy_j')) for r in shocks]
    if len(shock_keys) != len(set(shock_keys)):
        missing.append('cardioversion: one unambiguous response per starting rhythm and energy')
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


# Therapies clinicians name constantly and this engine does not execute. A case
# whose expected paths rest on one of them cannot be practised: four paid
# generations built a pulmonary-embolism dilemma around systemic thrombolysis
# and catheter-directed therapy, and the reviewer rejected every one. Naming a
# therapy is fine when the path is to consult, refer or transfer for it, which
# the engine does execute.
UNMODELLED_THERAPIES = {
    'thrombolysis': ('thrombolysis', 'thrombolytic', 'thrombolytics', 'fibrinolysis',
                     'fibrinolytic', 'alteplase', 'tenecteplase', 'tpa', 't-pa', 'streptokinase'),
    'catheter-directed or surgical reperfusion': ('catheter-directed', 'catheter directed',
                                                  'embolectomy', 'thrombectomy'),
    'percutaneous coronary intervention': ('percutaneous coronary intervention', 'primary pci',
                                           'cath lab', 'catheterisation lab', 'catheterization lab'),
    'renal replacement therapy': ('dialysis', 'haemodialysis', 'hemodialysis',
                                  'renal replacement'),
    'chest drainage or pericardial drainage': ('chest tube', 'thoracostomy', 'thoracentesis',
                                               'pericardiocentesis', 'needle decompression'),
    'extracorporeal support': ('ecmo', 'extracorporeal', 'balloon pump', 'impella'),
    'transvenous or transcutaneous pacing': ('transvenous pacing', 'transcutaneous pacing',
                                             'pacing wire', 'pacemaker insertion'),
    'surgery': ('laparotomy', 'thoracotomy', 'craniotomy', 'operating theatre',
                'operating room', 'emergency surgery'),
    'blood components other than packed red cells': ('fresh frozen plasma', 'platelet transfusion',
                                                     'cryoprecipitate', 'prothrombin complex'),
}
# The engine does execute the decision to involve someone else.
_REFERRAL_WORDS = ('consult', 'refer', 'referral', 'transfer', 'disposition', 'admit',
                   'activate', 'call ', 'escalate', 'arrange', 'request', 'organise',
                   'organize', 'not available', 'unavailable',
                   'cannot be performed', 'outside this simulation')


def unexecutable_path_issues(case):
    """The dilemma and its expected paths must be practisable, or be referrals.

    Checking the paths alone was not enough: one paid case framed every path as a
    consult or transfer while its management_dilemma still turned on whether to
    thrombolyse, a decision the learner cannot carry out.
    """
    faculty = case.get('faculty') or {}
    entries = [(f'case.faculty.anticipated_management_paths[{i}]', text)
               for i, text in enumerate(faculty.get('anticipated_management_paths') or [])]
    entries += [(f'case.faculty.{field}', faculty.get(field))
                for field in ('management_focus', 'management_dilemma')]
    issues = []
    for index, path in entries:
        if not isinstance(path, str):
            continue
        lowered = path.lower()
        if any(word in lowered for word in _REFERRAL_WORDS):
            continue
        for therapy, terms in sorted(UNMODELLED_THERAPIES.items()):
            matched = [term for term in terms if term in lowered]
            if not matched:
                continue
            issues.append({'code': 'UNEXECUTABLE_MANAGEMENT_PATH',
                           'path': index,
                           'message': ('This rests on a therapy the engine cannot execute, so the learner '
                                       'cannot practise it. Build the dilemma from executable treatments, '
                                       'or make it the decision to consult, refer, arrange or transfer for '
                                       'that therapy, which the engine does execute.'),
                           'details': {'therapy': therapy, 'matched_terms': sorted(matched),
                                       'referral_actions': ['consult', 'reperfusion_referral', 'disposition']}})
            break
    return issues
