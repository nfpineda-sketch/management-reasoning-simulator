"""PHASE 3 -- the SUCCESSION of the order reader: two successors and THREE readers, each independently reconstructable (faculty decisions FD-TARGET-01 to FD-TARGET-11, 2026-11-20, and FD-ORDER-01 to FD-ORDER-11, 2026-11-21).

The reader (``family_parser.py``) was frozen at the accepted post-V3 state (``test_prephase1_reader_freeze``) and sits in the input path of the Phase-2 calibration freeze
(``clinical_core.calibration.INPUT_PATH_SOURCES``). The faculty has lifted that freeze twice, each time ONLY for one narrowly scoped safety correction, and the reader therefore has three states, all kept:

  1. THE PHASE-2 CLOSURE reader      git blob ``1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0``   the reader the closure and the V3 baselines were computed with;
  2. THE TARGET-SAFETY successor     git blob ``7a85714eb2b6fccb47507384a71fe91451e71ecb``   (2026-11-20, FD-TARGET-01 to 11: a physiologic target is never a drug rate);
  3. THE ORDER-SAFETY successor      the live file                                             (2026-11-21, FD-ORDER-01 to 11: a rate and a stop belong to one drug; restart and continue are not silent).

Each earlier reader is rebuilt, byte for byte, from the live file by REVERSING declared hunks (the repository's own precedent: the amendments' reversible hunks): ``REVERSAL_ORDER_SAFETY`` takes the live file to
state 2 and ``REVERSAL`` takes state 2 to state 1. The two are composed, so each reader is proven against its pinned identity and none depends on a record being re-generated:

* ``target_safety_reader_bytes()`` / ``historical_reader_bytes()`` rebuild states 2 and 1; ``target_safety_reader_module()`` / ``historical_reader_module()`` RUN them (their behavior is reconstructable too);
* ``install(patch)`` / ``historical_reader_view`` make every Phase-2 digest -- and every digest built on them (the lactate slice, the decision pack, the blood anchors and probes) -- recompute from state 1, on top of
  the closure view of ``clinical_core.amendment_3``; ``install_target_safety(patch)`` / ``target_safety_reader_view`` do the same for state 2, so the records of the first succession still regenerate to the same content.
  ``clinical_core/`` is NOT edited and no sealed record is rewritten.

Nothing here changes an order, a physiology constant or an authority; it only says which reader a historical digest is computed from. The sealed records are
``docs/revision/PHASE3_READER_SUCCESSION_TARGET_SAFETY.json`` (state 1 -> 2, never regenerated) and ``docs/revision/PHASE3_READER_SUCCESSION_ORDER_SAFETY.json`` (state 2 -> 3).
"""
from __future__ import annotations

import hashlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READER = "family_parser.py"
#: State 1: the reader as the Phase-2 closure and the pre-Phase-1 freeze accepted it.
HISTORICAL_GIT_BLOB = "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0"
HISTORICAL_SHA256 = "7157bd8682f2d9e98bf5c41fdf94de42623baf84d18402147d666074d453ae58"
#: State 2: the reader after the target-safety repair (the first successor).
TARGET_SAFETY_GIT_BLOB = "7a85714eb2b6fccb47507384a71fe91451e71ecb"
TARGET_SAFETY_SHA256 = "a1f5dd86780956430224257e05108b1c81b9ffee0908f1c8b3e78dd936ced2ee"
#: State 3: the live reader after the order-safety hardening (the successor pin of ``test_prephase1_reader_freeze``).
SUCCESSOR_GIT_BLOB = "a71a3888bc687a17a9eea24a6b06096ad58ae448"
SUCCESSOR_SHA256 = "39308bfd456f3b8443d9050bf9917ed3d7c47cd2a0086484dae113417b50d1c5"
#: (text in state 2, the text of state 1 it replaced). Each ``new`` text is unique in state 2 and the hunks reverse in order.
REVERSAL = (
    ('\n# FD-TARGET-01 to FD-TARGET-10 (2026-11-20): a physiologic TARGET is never a DRUG RATE. A number that carries no rate unit\n# ("titrate norepinephrine to MAP 65", "nitroglycerin to keep SBP 120", "increase norepinephrine to 12") is not a rate, and a\n# relative change with no rate at all ("increase norepinephrine", "wean norepinephrine off") has nothing to execute: the order is\n# INCOMPLETE and is asked for, never completed from the running infusion or from the number beside it. The message names no\n# number, so it cannot suggest that a detected target is a dose. The reader gives no rate at all unless one is written with its\n# unit; the order pipeline holds the same orders again when they arrive as structured actions (defense in depth).\nINCOMPLETE_EXPLICIT_RATE = ("The order specifies a target or an incomplete rate. Specify an explicit rate with its units to continue.")\n\n\ndef _incomplete_explicit_rate(agent, operation, reason):\n    """The non-executable representation of an infusion order that gave no explicit rate with units."""\n    return {**_clarification(INCOMPLETE_EXPLICIT_RATE),\n            "incomplete_explicit_rate": {"agent": agent, "operation": operation, "reason": reason}}\n\n\n# An explicit instruction to wait for a result before acting. Deliberately\n',
     '\n# An explicit instruction to wait for a result before acting. Deliberately\n'),
    ('\n_RESTART_INFUSION = re.compile(\n    r"^(?P<lead>(?:(?:i\\s+(?:will|want to)|i\'ll|i am going to|voy a|quiero|vamos a|i|we)\\s+)?)"\n    r"(?:restart|re-start|resume|reinicia(?:r|mos)?|reinicio|reanuda(?:r|mos)?|retoma(?:r|mos)?)\\s+"\n    r"(?=(?:(?:the|la|el)\\s+)?(?:norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|"\n    r"dobutamine|dobutamina|epinephrine|epinefrina|adrenaline|adrenalina|epi)\\b)", re.I)\n#: What a restart of one of the four infusions can be read as. A restart that reads as anything else ("restart epinephrine 0.3 mg IM", "restart nitroglycerin 1000 mcg IV bolus") is a\n#: one-shot dose, not an infusion: it is left exactly as the historical reader left it (not read), never turned into a START of that dose (adversarial review, FD-TARGET-07).\n_INFUSION_TYPES = frozenset({"norepinephrine", "epinephrine", "dobutamine", "nitroglycerin"})\n\n\ndef _reads_as_an_infusion(actions):\n    return bool(actions) and all(action.get("type") in _INFUSION_TYPES or action.get("incomplete_explicit_rate") for action in actions)\n\n\ndef _parse_piece_core(piece, inherited=None):\n',
     '\ndef _parse_piece_core(piece, inherited=None):\n'),
    ('        return [{"type": "monitoring", "operation": "start"}], "monitor"\n    # FD-TARGET-07: "restart norepinephrine at 10 mcg/min" is a START with an explicit rate; "restart norepinephrine" is a start with no\n    # rate, which is asked for. The previous rate is never reused. Only the four vasoactive infusions the engine runs are read this\n    # way, so no other family\'s wording changes.\n    restarted = _RESTART_INFUSION.match(text)\n    if restarted:\n        actions, as_verb = _parse_piece_core(restarted["lead"] + "start " + text[restarted.end():], inherited)\n        if _reads_as_an_infusion(actions):\n            return actions, as_verb\n    command = _COMMAND.match(text)\n',
     '        return [{"type": "monitoring", "operation": "start"}], "monitor"\n    command = _COMMAND.match(text)\n'),
    ('        if not rate_match:\n            # A number without a rate unit is NOT a rate (FD-TARGET-02/05/06). It used to become ``rate`` here, so a pressure target\n            # ("MAP 65", "SBP 120") was read as 65 or 120 and, for an adjustment, completed with the running infusion\'s units.\n            bare_rates = re.findall(r"(?<![\\w.])(-?(?:\\d+(?:\\.\\d+)?|\\.\\d+))(?![\\w.])", body)\n',
     '        if not rate_match:\n            bare_rates = re.findall(r"(?<![\\w.])(-?(?:\\d+(?:\\.\\d+)?|\\.\\d+))(?![\\w.])", body)\n'),
    ('            bare_rates = re.findall(r"(?<![\\w.])(-?(?:\\d+(?:\\.\\d+)?|\\.\\d+))(?![\\w.])", body)\n            time_word = re.search(r"\\b(?:minutes?|mins?|hours?|horas?|minutos?)\\b", body)\n            if _operation(verb) in {"start", "adjust"} and len(bare_rates) == 1 and not time_word:\n                return [_incomplete_explicit_rate(kind, _operation(verb), "NUMBER_WITHOUT_RATE_UNITS")], verb\n            if _operation(verb) == "adjust":\n                return [_incomplete_explicit_rate(kind, "adjust", "NO_EXPLICIT_RATE")], verb\n        if rate_match:\n',
     '            bare_rates = re.findall(r"(?<![\\w.])(-?(?:\\d+(?:\\.\\d+)?|\\.\\d+))(?![\\w.])", body)\n            if len(bare_rates) == 1 and not re.search(r"\\b(?:minutes?|mins?|hours?|horas?|minutos?)\\b", body):\n                rate = float(bare_rates[0])\n        if rate_match:\n'),
    ('        if not command:\n            # "My priority is perfusion, restart norepinephrine at 5 mcg/min": the restart verbs are not in _COMMAND, and the order must not be dropped as reasoning.\n            if _RESTART_INFUSION.match(rest) and _reads_as_an_infusion(_parse_piece(re.split(r"\\s*(?:,|\\+|\\band\\b|\\by\\b|\\bthen\\b|\\bluego\\b)\\s*", rest, maxsplit=1)[0])[0]):\n                return rest\n            continue\n',
     '        if not command:\n            continue\n'),
    ('        parsed, _ = _parse_piece(first)\n        # An infusion order that is INCOMPLETE (a target, a number with no rate unit, a relative change with no rate) is still an order that must be asked for: "my priority is perfusion, titrate norepinephrine to\n        # MAP 65" used to execute 65 mcg/min; read as reasoning only, it would be dropped without telling the resident that nothing ran (FD-TARGET-06).\n        if not any(action["type"] != "clarification" or action.get("incomplete_explicit_rate") for action in parsed):\n            continue\n',
     '        parsed, _ = _parse_piece(first)\n        if not any(action["type"] != "clarification" for action in parsed):\n            continue\n'),
)
#: (text in the live reader, the text of state 2 it replaced). Each ``new`` text is unique in the live reader and the hunks reverse in order.
REVERSAL_ORDER_SAFETY = (
    ('\n# FD-ORDER-01 to FD-ORDER-06 (2026-11-21): WHO a rate and a stop belong to. A rate belongs to AT MOST ONE drug and a stop to at most one drug; an ambiguity is never\n# settled by the number that happens to be nearest, it is asked.\n#  * RATE. When the piece of the order names no other medication, the rate written in it is this drug\'s, as before. When it names another medication too, a rate belongs to\n#    the drug NAMED JUST BEFORE it (through the connectors of a dose only: "at", "to", "rate of", ...) or just after it ("5 mcg/min of propofol"). A piece in which a rate is\n#    claimed by ANOTHER drug, or by no one, is held WHOLE and asked (nothing runs, no number is kept, and no other medicine\'s order is dropped in silence).\n#  * STOP. A stop belongs to a vasoactive drug only when the stop verb governs that drug\'s NAME: the verb is written in the same piece with no exception between them ("stop all\n#    except norepinephrine", "stop NS but keep norepinephrine" never stop it), or the piece is a BARE name in a list the verb distributes over ("stop NS, norepinephrine"). A\n#    piece that says anything more ("norepinephrine to MAP 65", "norepinephrine at 12") does not inherit the stop: it is read as the order it is, which asks for its rate.\n_VASOACTIVE_ALIASES = {\n    "norepinephrine": r"norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed",\n    "epinephrine": r"epinephrine|epinefrina|adrenaline|adrenalina|(?<!nor-)(?<!nor )epi",\n    "dobutamine": r"dobutamine|dobutamina",\n    "nitroglycerin": r"nitroglycerin|nitroglicerina|nitro",\n}\n_ANY_VASOACTIVE = "|".join(_VASOACTIVE_ALIASES.values())\n# Other ways a resident writes the four infusions that this reader does NOT read as orders ("NTG", "GTN", "NE", "nor-epi", "levo"). RECOGNITION ONLY, like the list below: they make a piece\n# that names the drug that way see that someone is named, so a rate written beside such a name is never read as another infusion\'s (adversarial review F09, F13). They are the\n# drug\'s own name inside a piece of that drug and another medicine\'s name in every other piece.\n_RECOGNISED_ALIASES = {\n    "norepinephrine": r"ne|nor[\\s-]?epi|nore|noradr|norad|levo|norepinephrine?s?",\n    "epinephrine": r"adrenalin|epipen|adr",\n    "dobutamine": r"dobuta|dobutrex|dobu",\n    "nitroglycerin": r"ntg|gtn|tng|glyceryl\\s+trinitrate|nitroglycerine|nitroglicerine|nitroglic|nitros",\n}\n# Names of other medicines a resident writes beside a vasoactive infusion. It is RECOGNITION ONLY (it supports nothing and gives no medicine a rate): it lets this reader see that\n# a piece names someone else. The reader\'s own agents (``_AGENTS``) and the other three infusions are added to it.\n_OTHER_INFUSION_AGENTS = (r"vasopressin|vasopresina|terlipressin\\w*|dopamine|dopamina|phenylephrine|fenilefrina|milrinone|milrinona|esmolol|nicardipine|nicardipino|clevidipine|"\n                          r"nitroprusside|nitroprusiato|labetalol|isoproterenol|isoprenalina|lidocaine|lidocaina|adenosine|adenosina|insulin|insulina|heparin|heparina|"\n                          r"octreotide|octreotido|levosimendan|angiotensin\\w*|methylene\\s+blue|azul\\s+de\\s+metileno|oxytocin|oxitocina|magnesium|magnesio|potassium|potasio|"\n                          r"bicarbonate|bicarbonato|amiodarone|amiodarona|diltiazem|propofol|midazolam|fentanyl|fentanilo|ketamine|ketamina|dexmedetomidine|dexmedetomidina|"\n                          r"morphine|morfina|naloxone|naloxona|furosemide|furosemida|atropine|atropina|dextrose|glucosa|aminophylline|aminofilina|procainamide|procainamida|"\n                          r"alteplase|tenecteplase|tpa|remifentanil|remifentanilo|sufentanil|sufentanilo|rocuronium|rocuronio|vecuronium|vecuronio|cisatracurium|cisatracurio|"\n                          r"treprostinil|treprostinilo|epoprostenol|epoprostenolo|ephedrine|efedrina|nesiritide|nesiritida|alprostadil|prostaglandin\\w*|hydralazine|hidralazina|enalaprilat|"\n                          r"propranolol|metoprolol|verapamil|verapamilo|digoxin|digoxina|lorazepam|diazepam|haloperidol|bivalirudin|argatroban|tirofiban|eptifibatide|cangrelor|"\n                          r"nimodipine|nimodipino|neosynephrine|pitressin|giapreza|phentolamine|fentolamina|methylergonovine|terbutaline|terbutalina|salbutamol|albuterol|"\n                          r"aminocaproic|tranexamic|tranexamico|amiodarone|ibutilide|vasopresor\\w*|vasopressor\\w*|inotrope\\w*|inotropo\\w*|sildenafil|iloprost|inhaled\\s+nitric\\s+oxide|nitric\\s+oxide")\n# What may stand between a drug\'s name and the number that is its rate: only the connectors of a dose.\n_DOSE_CONNECTORS = re.compile(r"(?:[\\s:=@(-]|\\b(?:at|to|a|en|de|del|of|rate|tasa|dose|dosis|infusion|infusión|drip|gtt|goteo|iv|ev|up|hasta|titrated?|titulad[oa]|for)\\b)*", re.I)\n# An EXCEPTION to a stop ("all except", "but keep") or a negation placed directly before the infusion\'s name ("stop NS not norepinephrine"): the stop does not govern that name. It counts only BEFORE the name\n# (between the verb and its object): "stop norepinephrine but keep the saline" and "stop norepinephrine to keep MAP above 65" stop the infusion. The class is closed: a reason that merely contains "not"\n# ("stop norepinephrine, the pressure is not low") is not an exception and the stop stands.\n_STOP_EXCEPTION = re.compile(r"\\b(?:except|excepting|excluding|exclude|but|other\\s+than|besides|apart\\s+from|aside\\s+from|keep|maintain|leave|"\n                             r"excepto|exceptuando|menos|salvo|pero|mantener|manten|mantenga|mantengo|deja|dejar|deje)\\b"\n                             r"|\\b(?:not|don\'t|dont|never|no|nunca|ni)\\s+(?:the\\s+|la\\s+|el\\s+)?(?:" + _ANY_VASOACTIVE + r")\\b", re.I)\n_BARE_NAME_FILLERS = re.compile(r"\\b(?:the|el|la|los|las|this|that|esta|este|esa|ese|su|his|her|its|a|an|un|una|infusion|infusions|infusión|infusiones|drip|drips|gtt|goteo|"\n                                r"perfusion|perfusión|bomba|pump|order|orden|please|por\\s+favor|now|ahora|also|too|tambien|también)\\b", re.I)\n\n\ndef _drug_name_spans(body, own, own_kind=None):\n    """``[(start, end, "own" | "other")]`` for each medicine name in the piece: the words this piece\'s order is about (``own``), and every other medicine the reader can see."""\n    own_names = own + (r"|" + _RECOGNISED_ALIASES[own_kind] if own_kind in _RECOGNISED_ALIASES else "")\n    spans = [(m.start(), m.end(), "own") for m in re.finditer(r"\\b(?:" + own_names + r")\\b", body)]\n    others = [r"(?:" + pattern + r")" for other, pattern in _VASOACTIVE_ALIASES.items() if other != own_kind]\n    others += [r"(?:" + pattern + r")" for other, pattern in _RECOGNISED_ALIASES.items() if other != own_kind]\n    others.append(r"(?:" + _OTHER_INFUSION_AGENTS + r")")\n    others += [r"(?:" + pattern + r")" for agents in _AGENTS.values() for pattern in agents.values()]\n    spans += [(m.start(), m.end(), "other") for m in re.finditer(r"\\b(?:" + "|".join(others) + r")\\b", body)]\n    return sorted(spans)\n\n\ndef _rate_claimant(body, literal, spans):\n    """Which drug a written rate belongs to: ``"own"``, ``"other"`` or ``None`` (no drug claims it). Never the nearest name by distance: the drug named just before the number\n    with only the connectors of a dose between them, or the drug a trailing "of <drug>" names."""\n    trailing = re.match(r"\\s*(?:of|de|del)\\s+(?:the\\s+|la\\s+|el\\s+)?", body[literal.end():])\n    if trailing:\n        begins = literal.end() + trailing.end()\n        for start, end, who in spans:\n            if start == begins:\n                # "12 mcg/min of propofol" is propofol\'s, whatever is written before the number (adversarial review F10).\n                return who\n    before = [span for span in spans if span[1] <= literal.start()]\n    if before:\n        start, end, who = before[-1]\n        if _DOSE_CONNECTORS.fullmatch(body[end:literal.start()]):\n            return who\n    return None\n\n\ndef _own_rate_literals(body, own, own_kind, literals):\n    """``(mine, foreign, ambiguous)``: the rate literals of the piece split by who they belong to. A piece that names no other medicine keeps every literal as before."""\n    spans = _drug_name_spans(body, own, own_kind)\n    if not any(who == "other" for _, _, who in spans):\n        return list(literals), [], []\n    mine, foreign, ambiguous = [], [], []\n    for literal in literals:\n        who = _rate_claimant(body, literal, spans)\n        (mine if who == "own" else foreign if who == "other" else ambiguous).append(literal)\n    return mine, foreign, ambiguous\n\n\ndef _bare_vasoactive_name(body):\n    """Whether the piece is only the NAME of an infusion (with its article or the word "infusion"): the only piece that takes a stop from the list before it."""\n    rest = _BARE_NAME_FILLERS.sub(" ", re.sub(r"\\b(?:" + _ANY_VASOACTIVE + r")\\b", " ", body))\n    return not re.sub(r"[\\s.,;:!?()\\-]+", "", rest)\n\n\n# An explicit instruction to wait for a result before acting. Deliberately\n',
     '\n# An explicit instruction to wait for a result before acting. Deliberately\n'),
    ('    r"(?=(?:(?:the|la|el)\\s+)?(?:norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|"\n    r"dobutamine|dobutamina|epinephrine|epinefrina|adrenaline|adrenalina|(?<!nor-)(?<!nor )epi)\\b)", re.I)\n#: What a restart of one of the four infusions can be read as. A restart that reads as anything else ("restart epinephrine 0.3 mg IM", "restart nitroglycerin 1000 mcg IV bolus") is a\n',
     '    r"(?=(?:(?:the|la|el)\\s+)?(?:norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|"\n    r"dobutamine|dobutamina|epinephrine|epinefrina|adrenaline|adrenalina|epi)\\b)", re.I)\n#: What a restart of one of the four infusions can be read as. A restart that reads as anything else ("restart epinephrine 0.3 mg IM", "restart nitroglycerin 1000 mcg IV bolus") is a\n'),
    ('\n_AMBIGUOUS_RATE = "Specify a single absolute target infusion rate; a relative change or several rates is ambiguous."\n\n\ndef _reads_as_an_infusion(actions):\n',
     '\ndef _reads_as_an_infusion(actions):\n'),
    ('def _reads_as_an_infusion(actions):\n    return bool(actions) and all(action.get("type") in _INFUSION_TYPES or action.get("incomplete_explicit_rate") or action.get("message") == _AMBIGUOUS_RATE for action in actions)\n\n\ndef _restart_needs_a_rate(action):\n    """A restart that carries no explicit rate: the approved incomplete-rate question, with no number (the engine\'s own question for it says the same in other words)."""\n    if action.get("type") in _INFUSION_TYPES and action.get("operation") == "start" and action.get("rate") is None and action.get("rate_mcg_min") is None:\n        return _incomplete_explicit_rate(action["type"], "start", "NO_EXPLICIT_RATE")\n    return action\n\n',
     'def _reads_as_an_infusion(actions):\n    return bool(actions) and all(action.get("type") in _INFUSION_TYPES or action.get("incomplete_explicit_rate") for action in actions)\n\n'),
    ("        if _reads_as_an_infusion(actions):\n            # FD-ORDER-05: a restart with no explicit rate is the approved incomplete-rate question, not the engine's own; the previous rate is never reused.\n            return [_restart_needs_a_rate(action) for action in actions], as_verb\n    command = _COMMAND.match(text)\n",
     '        if _reads_as_an_infusion(actions):\n            return actions, as_verb\n    command = _COMMAND.match(text)\n'),
    ('            and not re.search(_NAMED_INFUSION, body)):\n        rate_units = r"mcg\\s*/\\s*kg\\s*/\\s*min|mcg\\s*/\\s*min|ug\\s*/\\s*kg\\s*/\\s*min|ug\\s*/\\s*min|ml\\s*/\\s*h(?:r|ora)?"\n        # FD-ORDER-02: the rate another medicine of the same piece claims is not the running infusion\'s ("increase the infusion to MAP 65 with propofol 5 mcg/min").\n        written = list(re.finditer(r"(?<![\\w.])(-?(?:\\d+(?:\\.\\d+)?|\\.\\d+))\\s*(" + rate_units + r")\\b", body))\n        mine, foreign, unclaimed = _own_rate_literals(body, r"infusion|drip|goteo|bomba", None, written)\n        if foreign or unclaimed:\n            return [_clarification("Specify a single absolute target infusion rate; a relative change or several rates is ambiguous.")], verb\n        rate, units = _amount(body, rate_units)\n        return [{"type": "infusion_adjustment", "operation": _operation(verb),\n',
     '            and not re.search(_NAMED_INFUSION, body)):\n        rate, units = _amount(body, r"mcg\\s*/\\s*kg\\s*/\\s*min|mcg\\s*/\\s*min|ug\\s*/\\s*kg\\s*/\\s*min|ug\\s*/\\s*min|ml\\s*/\\s*h(?:r|ora)?")\n        return [{"type": "infusion_adjustment", "operation": _operation(verb),\n'),
    ('        return [{"type": "niv", "mode": mode, "ipap_cmh2o": ipap, "epap_cmh2o": epap, "fio2_percent": _settings(body, "fio2"), "operation": _operation(verb)}], verb\n    if re.search(r"\\b(?:dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|epinephrine|epinefrina|adrenaline|adrenalina|(?<!nor-)(?<!nor )epi)\\b", body):\n        kind = ("epinephrine" if re.search(r"\\b(?:epinephrine|epinefrina|adrenaline|adrenalina|(?<!nor-)(?<!nor )epi)\\b", body)\n                else "nitroglycerin" if re.search(r"\\b(?:nitroglycerin|nitroglicerina|nitro)\\b", body)\n',
     '        return [{"type": "niv", "mode": mode, "ipap_cmh2o": ipap, "epap_cmh2o": epap, "fio2_percent": _settings(body, "fio2"), "operation": _operation(verb)}], verb\n    if re.search(r"\\b(?:dobutamine|dobutamina|norepinephrine|noradrenaline|noradrenalina|norepinefrina|norepi|levophed|nitroglycerin|nitroglicerina|nitro|epinephrine|epinefrina|adrenaline|adrenalina|epi)\\b", body):\n        kind = ("epinephrine" if re.search(r"\\b(?:epinephrine|epinefrina|adrenaline|adrenalina|epi)\\b", body)\n                else "nitroglycerin" if re.search(r"\\b(?:nitroglycerin|nitroglicerina|nitro)\\b", body)\n'),
    ('                else "dobutamine" if re.search(r"\\b(?:dobutamine|dobutamina)\\b", body) else "norepinephrine")\n        # FD-ORDER-03: a STOP belongs to this infusion only if the verb governs its name. A stop inherited from a list is taken only by a piece that is the bare name; anything\n        # more ("norepinephrine to MAP 65") is read as the order it is, without the verb; an exception ("all except norepinephrine", "NS but keep norepinephrine") is not read.\n        if _operation(verb) == "stop":\n            if command is None and not _bare_vasoactive_name(body):\n                return _parse_piece_core(text, None)\n            named = re.search(r"\\b(?:" + _VASOACTIVE_ALIASES[kind] + r")\\b", body)\n            if named and _STOP_EXCEPTION.search(body[:named.end()]):\n                # What an exception keeps is not stopped by the pieces after it either: the verb ends here ("stop all except dobutamine and norepinephrine").\n                return [_unreadable(text)], None\n            if sum(1 for pattern in _VASOACTIVE_ALIASES.values() if re.search(r"\\b(?:" + pattern + r")\\b", body)) > 1:\n                # One stop that names two infusions does not say which one it governs ("stop norepinephrine while dobutamine continues"): it is never settled by the reader\'s fixed\n                # priority between them (adversarial review F08).\n                return [_unreadable(text)], None\n        # A rate may be written with a slash or in words: "20 mcg/min",\n',
     '                else "dobutamine" if re.search(r"\\b(?:dobutamine|dobutamina)\\b", body) else "norepinephrine")\n        # A rate may be written with a slash or in words: "20 mcg/min",\n'),
    ('            r"(min(?:ute)?s?|minutos?|h(?:r|our)?s?|horas?)\\b", body))\n        # FD-ORDER-02: a rate belongs to at most ONE drug. One that another medicine of the same piece claims is not this infusion\'s; one that no one claims is asked.\n        rate_matches, foreign_rates, unclaimed_rates = _own_rate_literals(body, _VASOACTIVE_ALIASES[kind], kind, rate_matches)\n        if foreign_rates or unclaimed_rates:\n            # The whole piece is held, as it always was for two rates: reading only this infusion\'s part would drop the other medicine\'s order in silence.\n            return [_clarification("Specify a single absolute target infusion rate; a relative change or several rates is ambiguous.")], verb\n        if len(rate_matches) > 1 or (_operation(verb) == "adjust" and re.search(r"\\b(?:by|en)\\s+-?\\d", body)):\n',
     '            r"(min(?:ute)?s?|minutos?|h(?:r|our)?s?|horas?)\\b", body))\n        if len(rate_matches) > 1 or (_operation(verb) == "adjust" and re.search(r"\\b(?:by|en)\\s+-?\\d", body)):\n'),
    ('            time_word = re.search(r"\\b(?:minutes?|mins?|hours?|horas?|minutos?)\\b", body)\n            # FD-ORDER-06: a number beside "continue" is no rate either ("continue norepinephrine at 12" used to continue the running rate in silence): it is asked.\n            if _operation(verb) in {"start", "adjust", "continue"} and len(bare_rates) == 1 and not time_word:\n                return [_incomplete_explicit_rate(kind, _operation(verb), "NUMBER_WITHOUT_RATE_UNITS")], verb\n',
     '            time_word = re.search(r"\\b(?:minutes?|mins?|hours?|horas?|minutos?)\\b", body)\n            if _operation(verb) in {"start", "adjust"} and len(bare_rates) == 1 and not time_word:\n                return [_incomplete_explicit_rate(kind, _operation(verb), "NUMBER_WITHOUT_RATE_UNITS")], verb\n'),
    ('                parsed, inherited = _parse_piece(piece, inherited)\n                if inherited in _STOP_VERBS and _STOP_EXCEPTION.search(piece):\n                    # An exception ("all except", "but keep") ends the stop: the items listed after it are what is kept (adversarial review F07).\n                    inherited = None\n            if waiting and any(action.get("type") == "blood" for action in parsed):\n',
     '                parsed, inherited = _parse_piece(piece, inherited)\n            if waiting and any(action.get("type") == "blood" for action in parsed):\n'),
    ('            if action.get("type") in {"clarification", "reassessment"}:\n                if action.get("incomplete_explicit_rate") or action.get("message") == _AMBIGUOUS_RATE:\n                    # An infusion order with no explicit rate is asked even when it waits: dropping it would lose what was written with no word (adversarial review F06).\n                    actions.append(action)\n                continue\n',
     '            if action.get("type") in {"clarification", "reassessment"}:\n                continue\n'),
)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _reverse(text: str, hunks, what: str) -> str:
    for new, old in hunks:
        if text.count(new) != 1:
            raise ValueError(f"the reader changed after the succession was declared: a hunk of {what} is no longer unique")
        text = text.replace(new, old)
    return text


def _prove(data: bytes, blob: str, sha256: str, what: str) -> bytes:
    if git_blob(data) != blob or hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"the reversal does not rebuild {what}")
    return data


def target_safety_reader_bytes(live: bytes | None = None) -> bytes:
    """State 2, the reader of the first successor, rebuilt from ``live`` (default: the file on disk) by reversing the order-safety hunks."""
    text = (live if live is not None else (ROOT / READER).read_bytes()).decode("utf-8")
    return _prove(_reverse(text, REVERSAL_ORDER_SAFETY, "the order-safety succession").encode("utf-8"), TARGET_SAFETY_GIT_BLOB, TARGET_SAFETY_SHA256, "the reader of the target-safety successor")


def historical_reader_bytes(live: bytes | None = None) -> bytes:
    """State 1, the reader of the Phase-2 closure, rebuilt from ``live`` through state 2 (default: the file on disk) by reversing the declared hunks of both successions."""
    text = target_safety_reader_bytes(live).decode("utf-8")
    return _prove(_reverse(text, REVERSAL, "the target-safety succession").encode("utf-8"), HISTORICAL_GIT_BLOB, HISTORICAL_SHA256, "the reader of the Phase-2 closure")


_MODULES: dict = {}


def _module(name: str, data_of) -> types.ModuleType:
    """A reader as a module of its own: it never replaces ``family_parser`` in ``sys.modules``."""
    if name not in _MODULES:
        module = types.ModuleType(name)
        module.__file__ = str(ROOT / READER)
        sys.modules.setdefault(name, module)
        exec(compile(data_of().decode("utf-8"), str(ROOT / READER), "exec"), module.__dict__)
        _MODULES[name] = module
    return _MODULES[name]


def historical_reader_module() -> types.ModuleType:
    """The Phase-2-closure reader (state 1) as a module of its own (``family_parser_phase2_closure``)."""
    return _module("family_parser_phase2_closure", historical_reader_bytes)


def target_safety_reader_module() -> types.ModuleType:
    """The reader of the first successor (state 2) as a module of its own (``family_parser_target_safety``)."""
    return _module("family_parser_target_safety", target_safety_reader_bytes)


class _Bytes:
    def __init__(self, data: bytes):
        self._data = data

    def read_bytes(self) -> bytes:
        return self._data

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._data.decode(encoding)


class _Overlay:
    """A directory-like wrapper around a closed package's ``REPOSITORY``: the bytes of an earlier reader, the wrapped object for everything else."""

    def __init__(self, inner, data_of=historical_reader_bytes):
        self.inner = inner
        self.data_of = data_of

    def __truediv__(self, name):
        if str(name) == READER:
            return _Bytes(self.data_of())
        return self.inner / name

    def relative_to(self, *args, **kwargs):
        return self.inner.relative_to(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def __fspath__(self):
        return str(self.inner)

    def __str__(self):
        return str(self.inner)

    def __eq__(self, other):
        return self.inner == getattr(other, "inner", other)

    def __hash__(self):
        return hash(self.inner)


def _closed_modules():
    return [module for name, module in list(sys.modules.items()) if name.startswith("clinical_core") and hasattr(module, "REPOSITORY")]


def install(patch) -> None:
    """Make every Phase-2 digest read the reader of the closure. ``patch`` is a ``pytest.MonkeyPatch`` (or the amendments' ``_Patcher``); install it AFTER the closure view, so it wraps what the view set."""
    for module in _closed_modules():
        patch.setattr(module, "REPOSITORY", _Overlay(module.REPOSITORY, historical_reader_bytes))


def install_target_safety(patch) -> None:
    """The same for the reader of the first successor (state 2): what the records of the first succession were computed with."""
    for module in _closed_modules():
        patch.setattr(module, "REPOSITORY", _Overlay(module.REPOSITORY, target_safety_reader_bytes))


class historical_reader_view:
    """The same, outside a test: ``with historical_reader_view(): ...`` (compose it INSIDE the closure view of the amendment stage for a closure digest)."""
    DATA = staticmethod(historical_reader_bytes)

    def __enter__(self):
        self._saved = [(module, module.REPOSITORY) for module in _closed_modules()]
        for module, current in self._saved:
            module.REPOSITORY = _Overlay(current, self.DATA)
        return self

    def __exit__(self, *exc):
        for module, current in self._saved:
            module.REPOSITORY = current
        return False


class target_safety_reader_view(historical_reader_view):
    """``with target_safety_reader_view(): ...``: every Phase-2 digest reads the reader of the first successor (state 2)."""
    DATA = staticmethod(target_safety_reader_bytes)


def verify() -> dict:
    """The succession as it stands: the live reader is the declared successor and each earlier reader is rebuilt from it."""
    live = (ROOT / READER).read_bytes()
    return {"live_is_the_successor": git_blob(live) == SUCCESSOR_GIT_BLOB and hashlib.sha256(live).hexdigest() == SUCCESSOR_SHA256,
            "target_safety_rebuilt": git_blob(target_safety_reader_bytes(live)) == TARGET_SAFETY_GIT_BLOB, "historical_rebuilt": git_blob(historical_reader_bytes(live)) == HISTORICAL_GIT_BLOB,
            "hunks": len(REVERSAL), "order_safety_hunks": len(REVERSAL_ORDER_SAFETY)}
