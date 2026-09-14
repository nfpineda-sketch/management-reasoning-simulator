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
    for kind, pattern in [('cardioversion', r'cardioversion|cardiovert'), ('niv', r'bipap|cpap|niv'), ('intubation', r'intubation|intubate'), ('norepinephrine', r'norepinephrine|noradrenalina')]:
        if re.search(r'\b(?:' + pattern + r')\b', paths) and kind not in kinds:
            missing.append(kind)
    return [{'code': 'MANAGEMENT_COVERAGE', 'path': 'engine.response_rules',
             'message': 'The new case is missing executable responses for plausible or explicitly authored management paths. Author patient-specific effects, including harm or no benefit where appropriate.',
             'details': {'missing': missing}}] if missing else []
