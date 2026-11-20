"""PHASE 3 -- the SUCCESSION of the order reader (faculty decisions FD-TARGET-01 to FD-TARGET-11, 2026-11-20).

The reader (``family_parser.py``) was frozen at the accepted post-V3 state (``test_prephase1_reader_freeze``) and sits in the input path of the Phase-2 calibration freeze
(``clinical_core.calibration.INPUT_PATH_SOURCES``). On 2026-11-20 the faculty lifted that freeze ONLY for one narrowly scoped safety correction: a physiologic TARGET is never a DRUG RATE.
The reader is therefore changed, once, and the Phase-2 evidence does not move:

* the reader as the Phase-2 closure froze it (git blob ``1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0``) stays reconstructable, byte for byte, from the live file by REVERSING the 7 declared hunks below
  (the repository's own precedent: the amendments' declared reversible hunks); ``historical_reader_bytes()`` proves it against the pinned identity;
* ``historical_reader_module()`` runs that historical reader, so its BEHAVIOR is reconstructable too (a test compares its answers with what it gave before the repair);
* ``install(patch)`` and ``historical_reader_view`` make the Phase-2 calibration digests -- and every digest built on them (the lactate slice, the decision pack, the blood anchors and probes) --
  recompute from the historical reader, on top of the closure view of ``clinical_core.amendment_3``, WITHOUT editing ``clinical_core/``. The sealed records are never rewritten.

Nothing here changes an order, a physiology constant or an authority; it only says which reader a historical digest is computed from. The successor record is
``docs/revision/PHASE3_READER_SUCCESSION_TARGET_SAFETY.json`` and the decision rows are FD-TARGET-01 to FD-TARGET-11.
"""
from __future__ import annotations

import hashlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READER = "family_parser.py"
#: The reader as the Phase-2 closure and the pre-Phase-1 freeze accepted it.
HISTORICAL_GIT_BLOB = "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0"
HISTORICAL_SHA256 = "7157bd8682f2d9e98bf5c41fdf94de42623baf84d18402147d666074d453ae58"
#: The reader after the target-safety repair (the successor pin of ``test_prephase1_reader_freeze``).
SUCCESSOR_GIT_BLOB = "7a85714eb2b6fccb47507384a71fe91451e71ecb"
SUCCESSOR_SHA256 = "a1f5dd86780956430224257e05108b1c81b9ffee0908f1c8b3e78dd936ced2ee"
#: (text in the repaired reader, the text it replaced). Each ``new`` text is unique in the repaired reader and the hunks reverse in order.
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


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def historical_reader_bytes(live: bytes | None = None) -> bytes:
    """The reader of the Phase-2 closure, rebuilt from ``live`` (default: the file on disk) by reversing the declared hunks."""
    text = (live if live is not None else (ROOT / READER).read_bytes()).decode("utf-8")
    for new, old in REVERSAL:
        if text.count(new) != 1:
            raise ValueError("the reader changed after the succession was declared: a hunk is no longer unique")
        text = text.replace(new, old)
    data = text.encode("utf-8")
    if git_blob(data) != HISTORICAL_GIT_BLOB or hashlib.sha256(data).hexdigest() != HISTORICAL_SHA256:
        raise ValueError("the reversal does not rebuild the reader of the Phase-2 closure")
    return data


_MODULE = None


def historical_reader_module() -> types.ModuleType:
    """The Phase-2-closure reader as a module of its own (``family_parser_phase2_closure``): it never replaces ``family_parser`` in ``sys.modules``."""
    global _MODULE
    if _MODULE is None:
        module = types.ModuleType("family_parser_phase2_closure")
        module.__file__ = str(ROOT / READER)
        sys.modules.setdefault(module.__name__, module)
        exec(compile(historical_reader_bytes().decode("utf-8"), str(ROOT / READER), "exec"), module.__dict__)
        _MODULE = module
    return _MODULE


class _Bytes:
    def __init__(self, data: bytes):
        self._data = data

    def read_bytes(self) -> bytes:
        return self._data

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._data.decode(encoding)


class _Overlay:
    """A directory-like wrapper around a closed package's ``REPOSITORY``: the historical bytes of the reader, the wrapped object for everything else."""

    def __init__(self, inner):
        self.inner = inner

    def __truediv__(self, name):
        if str(name) == READER:
            return _Bytes(historical_reader_bytes())
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
    """Make every Phase-2 digest read the historical reader. ``patch`` is a ``pytest.MonkeyPatch`` (or the amendments' ``_Patcher``); install it AFTER the closure view, so it wraps what the view set."""
    for module in _closed_modules():
        patch.setattr(module, "REPOSITORY", _Overlay(module.REPOSITORY))


class historical_reader_view:
    """The same, outside a test: ``with historical_reader_view(): ...`` (compose it INSIDE the closure view of the amendment stage for a closure digest)."""

    def __enter__(self):
        self._saved = [(module, module.REPOSITORY) for module in _closed_modules()]
        for module, current in self._saved:
            module.REPOSITORY = _Overlay(current)
        return self

    def __exit__(self, *exc):
        for module, current in self._saved:
            module.REPOSITORY = current
        return False


def verify() -> dict:
    """The succession as it stands: the live reader is the declared successor and the historical one is rebuilt from it."""
    live = (ROOT / READER).read_bytes()
    return {"live_is_the_successor": git_blob(live) == SUCCESSOR_GIT_BLOB and hashlib.sha256(live).hexdigest() == SUCCESSOR_SHA256,
            "historical_rebuilt": git_blob(historical_reader_bytes(live)) == HISTORICAL_GIT_BLOB, "hunks": len(REVERSAL)}
