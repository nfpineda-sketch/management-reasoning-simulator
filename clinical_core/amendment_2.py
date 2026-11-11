"""PHASE2_AMENDMENT_2: the formal successor stage of PHASE2_AMENDMENT_1 (shadow only).

The historical Phase-2 closure (d2cca46, digest 22b90a6f...) and PHASE2_AMENDMENT_1 (digest 10b45ce2..., certified) are NOT
rewritten here. This stage follows the first amendment the way it followed the closure: it DECLARES what it inserted into
the four common files it changed (``derived.py``, ``state.py``, ``integration.py``, ``decision_pack.py``), so the first
amendment's files are rebuilt from the live ones by reversing those insertions and proven by their SHA, and the closure's
files are rebuilt from those by the first amendment's own declared reversal. The historical closure, the first amendment and
every stage in between therefore keep reconstructing exactly, and each digest recomputes to the value it was certified at.

What the stage adds to the physiology is ``systemic_consciousness`` (its own file): the reversible systemic encephalopathy
burden F, the mechanistic consciousness impairment that replaces the direct SBP / SpO2 ladders, and the soft circulatory
collapse state, all behind ``CoreProfile.amendment_2`` (None by default: every committed behaviour is unchanged bit for bit).

The view this module installs (``tree`` / ``chain``) is for the closed packages' test fixtures and for the historical
verification of the closure: it shows them the tree as the closure left it, by composing this stage's reversal with the
first amendment's. It changes no behaviour: a view of the source, not of the physiology. ``amendment_1_tree`` shows the tree
as the FIRST amendment left it, for that amendment's own tests.

The amended core's own digest lives OUTSIDE this package (the amendment record and the runtime's lineage), because it
covers this file too.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import amendment_1 as a1
from . import calibration as _calibration
from . import derived as _dv
from . import state as _state
from . import tone_domain as x1

ROOT = a1.ROOT
CORE_DIR = a1.CORE_DIR
REVISION = "PHASE2_AMENDMENT_2"
PREDECESSOR = "PHASE2_AMENDMENT_1"
DECIDED = "2026-11-10"
OWN = ("clinical_core/amendment_2.py", "clinical_core/systemic_consciousness.py")
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_2.json"
#: The first amendment's certified digest: immutable, named here to be VERIFIED, never to be replaced.
AMENDMENT_1_DIGEST = "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635"
#: What the stage registers, as each stage did: its own modules are not sources of the decision pack.
TUPLES_ADDED = {"PACK_DIGEST_EXCLUDED": OWN}

#: What this stage inserted, as (live text, text before): reversing them in order gives the first amendment's file.
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/amendment_1.py", '
                                     '"clinical_core/amendment_2.py")\n',
                                     '                        "clinical_core/amendment_1.py")\n'),),
 'clinical_core/derived.py': (('    def to_dict(self) -> dict:\n'
                               '        data = {item.name: (list(map(list, getattr(self, item.name))) if '
                               'isinstance(getattr(self, item.name), tuple)\n'
                               '                            else getattr(self, item.name)) for item in '
                               'fields(self)}\n'
                               '        if data.get("amendment_2") is not None:\n'
                               '            # PHASE2_AMENDMENT_2: a declared profile travels as plain data, like '
                               'every other field.\n'
                               '            data["amendment_2"] = data["amendment_2"].to_dict()\n'
                               '        return data\n',
                               '    def to_dict(self) -> dict:\n'
                               '        return {item.name: (list(map(list, getattr(self, item.name))) if '
                               'isinstance(getattr(self, item.name), tuple)\n'
                               '                            else getattr(self, item.name)) for item in '
                               'fields(self)}\n'),
                              ('            if item.name == "amendment_2":\n'
                               '                # PHASE2_AMENDMENT_2: a declared Amendment2Profile validates itself '
                               '(it is not a numeric gain), must be one,\n'
                               '                # and cannot be combined with the inherited collapse rule: the '
                               'reused collapse_burden slot is a 0-1 share\n'
                               "                # there, not the inherited rule's severity-time burden, and the soft "
                               'path never stops an encounter.\n'
                               '                if value is not None:\n'
                               '                    from .systemic_consciousness import Amendment2Profile\n'
                               '                    if not isinstance(value, Amendment2Profile):\n'
                               '                        raise CoreInvariantError("amendment_2 is None or an '
                               'Amendment2Profile")\n'
                               '                    if (self.collapse_output_threshold is not None or '
                               'self.collapse_burden_limit is not None\n'
                               '                            or self.collapse_repayment_tau_min is not None):\n'
                               '                        raise CoreInvariantError("amendment_2 cannot be declared '
                               'with the inherited collapse rule")\n'
                               '                continue\n'
                               '            if isinstance(value, (tuple, str)) or value is None:\n'
                               '                continue\n',
                               '            if isinstance(value, (tuple, str)) or value is None:\n'
                               '                continue\n'),
                              ('    hypoventilation_oxygenation_transmission_fraction: float | None = None\n'
                               '    # PHASE2_AMENDMENT_2: the declared magnitudes of the mechanistic systemic '
                               'consciousness (the reversible systemic\n'
                               '    # encephalopathy burden F) and of the soft circulatory-collapse state, as a '
                               '``systemic_consciousness.\n'
                               '    # Amendment2Profile``. None (every committed profile) is the amendment OFF: '
                               'consciousness stays the certified\n'
                               "    # direct ladder, F is not tracked and the collapse rule stays P2E-3's. Declared, "
                               'the direct pressure and SpO2\n'
                               '    # ladders no longer reach consciousness, which is the maximum of the primary '
                               'neurologic state, F and an\n'
                               '    # established circulatory collapse, and the existing collapse burden is fed by '
                               'the conjunction of a perfusion\n'
                               '    # failure and a delivery failure. Development behavioural regions, never a '
                               'calibration. No value is chosen here.\n'
                               '    amendment_2: object | None = None\n',
                               '    hypoventilation_oxygenation_transmission_fraction: float | None = None\n'),
                              ('    "amendment_2": (\n'
                               '        PROVISIONAL, "OFF (PHASE2_AMENDMENT_2): the magnitudes of the mechanistic '
                               'systemic consciousness and the soft "\n'
                               '                     "circulatory collapse, a '
                               'systemic_consciousness.Amendment2Profile; None by default, which keeps the "\n'
                               '                     "certified direct ladder and the P2E-3 collapse rule bit for '
                               'bit. Faculty-defined DEVELOPMENT "\n'
                               '                     "behavioural regions (LOW / CENTER_REFERENCE / HIGH witnesses), '
                               'never a clinical calibration, a "\n'
                               '                     "production threshold or a resident-facing safety threshold; GI '
                               'first, no opioid mechanism"),\n'
                               '    "hypoventilation_oxygenation_transmission_fraction": (\n',
                               '    "hypoventilation_oxygenation_transmission_fraction": (\n'),
                              ('    if profile.amendment_2 is not None:\n'
                               '        # PHASE2_AMENDMENT_2: the soft path -- the conjunction of a perfusion '
                               'failure and a delivery failure -- feeds\n'
                               '        # this same slot, as a share of the combined signal with a slower clearance '
                               'than rise. Low output alone is not\n'
                               '        # a collapse and neither is a failure of one channel alone.\n'
                               '        from . import systemic_consciousness as _amendment_2\n'
                               '        return _amendment_2.collapse_burden_after(state, anchors, profile)\n'
                               '    burden = state.aux.collapse_burden\n'
                               '    threshold = profile.collapse_output_threshold\n',
                               '    burden = state.aux.collapse_burden\n'
                               '    threshold = profile.collapse_output_threshold\n'),
                              ('    if profile.amendment_2 is None:\n'
                               '        level = max(anchors.consciousness_level, _level(sbp, '
                               'profile.pressure_levels),\n'
                               '                    _level(spo2, profile.oxygen_levels))\n'
                               '    else:\n'
                               '        # PHASE2_AMENDMENT_2: the direct SBP and SpO2 ladders are duplicative and no '
                               'longer reach consciousness; the level\n'
                               '        # is the observable category of the maximum of the primary neurologic state, '
                               'F and an established collapse.\n'
                               '        from . import systemic_consciousness as _amendment_2\n'
                               '        level = _amendment_2.consciousness_level(state, anchors, profile)\n',
                               '    level = max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), '
                               '_level(spo2, profile.oxygen_levels))\n')),
 'clinical_core/integration.py': (('        profile_data[name] = tuple(tuple(pair) for pair in profile_data[name])\n'
                                   '    if profile_data.get("amendment_2") is not None:\n'
                                   '        # PHASE2_AMENDMENT_2: the declared profile of the amendment, rebuilt '
                                   'from the plain data it travelled as.\n'
                                   '        from .systemic_consciousness import Amendment2Profile\n'
                                   '        profile_data["amendment_2"] = '
                                   'Amendment2Profile(**profile_data["amendment_2"])\n'
                                   '    return (Anchors.from_dict(',
                                   '        profile_data[name] = tuple(tuple(pair) for pair in profile_data[name])\n'
                                   '    return (Anchors.from_dict('),
                                  ('def _systemic_burden_after(state: CoreState, anchors: Anchors, profile: '
                                   'CoreProfile) -> float | None:\n'
                                   '    """PHASE2_AMENDMENT_2: F after the minute, or None (not tracked) where the '
                                   'profile does not declare the amendment."""\n'
                                   '    if profile.amendment_2 is None:\n'
                                   '        return None\n'
                                   '    from . import systemic_consciousness as _amendment_2\n'
                                   '    return _amendment_2.systemic_burden_after(state, anchors, profile)\n'
                                   '\n'
                                   '\n'
                                   'def _no_repayment_across(debt: ChannelDelta,',
                                   'def _no_repayment_across(debt: ChannelDelta,'),
                                  ('                         vasodilatory_burden=_vasodilation_after(state, '
                                   'vasodilation, profile, minute),\n'
                                   '                         '
                                   'systemic_encephalopathy_burden=_systemic_burden_after(state, anchors, '
                                   'profile))\n',
                                   '                         vasodilatory_burden=_vasodilation_after(state, '
                                   'vasodilation, profile, minute))\n')),
 'clinical_core/state.py': (('    vasodilatory_burden: float = 0.0\n'
                             '    # PHASE2_AMENDMENT_2: the reversible systemic encephalopathy burden F, a share of '
                             'the maximal impairment in [0, 1]. None\n'
                             '    # is NOT TRACKED (every committed profile), and then the state serializes exactly '
                             'as it did: this field is not one of\n'
                             '    # AUXILIARY_FIELDS, so no digest of a state that does not carry it changes. It is '
                             'distinct from D, from N and from\n'
                             '    # the collapse burden, and only a profile that declares the amendment writes it.\n'
                             '    systemic_encephalopathy_burden: float | None = None\n'
                             '\n'
                             '    def __post_init__(self):\n'
                             '        for name in AUXILIARY_FIELDS:\n'
                             '            _finite(getattr(self, name), name)\n'
                             '        if self.systemic_encephalopathy_burden is not None:\n'
                             '            _finite(self.systemic_encephalopathy_burden, '
                             '"systemic_encephalopathy_burden")\n'
                             '            if not 0.0 <= self.systemic_encephalopathy_burden <= 1.0:\n'
                             '                raise CoreInvariantError("the systemic encephalopathy burden is a '
                             'share between 0 and 1")\n',
                             '    vasodilatory_burden: float = 0.0\n'
                             '\n'
                             '    def __post_init__(self):\n'
                             '        for name in AUXILIARY_FIELDS:\n'
                             '            _finite(getattr(self, name), name)\n'),
                            ('    def to_dict(self) -> dict:\n'
                             '        data = {name: getattr(self, name) for name in AUXILIARY_FIELDS}\n'
                             '        if self.systemic_encephalopathy_burden is not None:\n'
                             '            data["systemic_encephalopathy_burden"] = '
                             'self.systemic_encephalopathy_burden\n'
                             '        return data\n'
                             '\n'
                             '    @classmethod\n'
                             '    def from_dict(cls, data: Mapping) -> "AuxiliaryState":\n'
                             '        optional = {"systemic_encephalopathy_burden"}\n'
                             '        if not set(AUXILIARY_FIELDS) <= set(data) <= set(AUXILIARY_FIELDS) | '
                             'optional:\n'
                             '            raise CoreInvariantError(f"auxiliary state names exactly '
                             '{sorted(AUXILIARY_FIELDS)} (and, only where it is "\n'
                             '                                     f"tracked, {sorted(optional)}), not '
                             '{sorted(data)}")\n'
                             '        return cls(**{name: data[name] for name in set(data)})\n',
                             '    def to_dict(self) -> dict:\n'
                             '        return {name: getattr(self, name) for name in AUXILIARY_FIELDS}\n'
                             '\n'
                             '    @classmethod\n'
                             '    def from_dict(cls, data: Mapping) -> "AuxiliaryState":\n'
                             '        if set(data) != set(AUXILIARY_FIELDS):\n'
                             '            raise CoreInvariantError(f"auxiliary state names exactly '
                             '{sorted(AUXILIARY_FIELDS)}, not {sorted(data)}")\n'
                             '        return cls(**{name: data[name] for name in AUXILIARY_FIELDS})\n'))}

#: The changed files as the first amendment left them (its certified tree's own SHAs).
CORE_AT_AMENDMENT_1 = {'clinical_core/decision_pack.py': '4ae02acf603893ffb4ef561a10dcc97e4400aa99ec97d3a6e205fbda2406aecf',
 'clinical_core/derived.py': 'd6b19c75044da476735f42fc113fe6fb6896a45da54fb3e66fb44f1945cce545',
 'clinical_core/integration.py': 'e59949b9f708db5834cb0a80ab5205098f307adf1d80f637df0899554baaaf23',
 'clinical_core/state.py': '74bc9337c523590fe89d9fae0e23bf77d8bad25454c5eec586aa1ef919fae093'}
#: Files this stage changed that the first amendment did not: their first-amendment text IS the closure's.
NEW_COMMON = tuple(sorted(set(REVERSAL) - set(a1.REVERSAL)))


def _live_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _live(relative: str) -> str:
    """Indirect on purpose, as in every stage: a probe replaces this to mutate a protected source."""
    return _live_text(relative)


def _reverse(relative: str, text: str) -> tuple[str, list]:
    problems = []
    for live, before in REVERSAL[relative]:
        if text.count(live) != 1:
            problems.append(f"{relative}: a declared replacement occurs {text.count(live)} times")
            continue
        text = text.replace(live, before)
    return text, problems


def proved(relative: str, text: str | None = None) -> bool:
    back, problems = _reverse(relative, _live(relative) if text is None else text)
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_AMENDMENT_1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def a1_text(relative: str) -> str:
    """The first amendment's file: the live one with this stage's declared insertions reversed (proven)."""
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the first amendment's file plus PHASE2_AMENDMENT_2's insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def a1_bytes(relative: str) -> bytes:
    return a1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def a1_sources(sources: dict) -> dict:
    """A ``path -> sha256`` map of the live package, as the FIRST amendment's tree would hold it."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_AMENDMENT_1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def live_core_sources() -> dict:
    return _A1_LIVE_CORE_SOURCES()


def amended_core_digest_now() -> str:
    """The digest of the amended tree, this stage's files included. Its certified value is recorded outside the package."""
    return a1.core_digest(live_core_sources())


def amendment_1_digest_now() -> str:
    """The FIRST amendment's digest RECOMPUTED from the live tree by reversing this stage's declared insertions. It equals
    AMENDMENT_1_DIGEST only while the reversal is exact and nothing else in the package moved."""
    return a1.core_digest(a1_sources(live_core_sources()))


def _extended_closure_view() -> tuple[dict, dict]:
    """The first amendment's declared reversal widened to the files this stage changed: their reversal to the closure is
    empty (the first amendment did not touch them) and their closure SHA is the closure record's."""
    closure = a1.closure_sources()
    reversal = dict(a1.REVERSAL)
    shas = dict(a1.CORE_AT_P2X1A)
    for relative in NEW_COMMON:
        reversal[relative] = ()
        shas[relative] = closure[relative]
    return reversal, shas


def _closure_standing() -> dict:
    """The historical closure rebuilt through BOTH reversals, with the first amendment's own functions reading the first
    amendment's text (``a1_text``) and the widened reversal. Never raises."""
    patcher = x1._Patcher()
    try:
        _install_a1_functions(patcher)
        return a1.historical_closure_verifies()
    finally:
        patcher.restore()


_A1_LIVE_CORE_SOURCES = a1.live_core_sources
_A1_COMMON_UNTOUCHED = a1.common_untouched


def _install_a1_functions(patch) -> None:
    reversal, shas = _extended_closure_view()
    # A closure view may be installed INSIDE the first amendment's own view (that amendment's tests compare both): the
    # first amendment's reading of the live tree and its path views are put back first, then the closure's go on top.
    patch.setattr(a1, "live_core_sources", _A1_LIVE_CORE_SOURCES)
    patch.setattr(a1, "common_untouched", _A1_COMMON_UNTOUCHED)
    for module in a1._imported_closed_modules() + [_calibration]:
        for attribute in a1._PATH_ATTRIBUTES:
            value = getattr(module, attribute, None)
            if isinstance(value, _A1Dir):
                patch.setattr(module, attribute, value.path)
    patch.setattr(a1, "_live", a1_text)
    patch.setattr(a1, "REVERSAL", reversal)
    patch.setattr(a1, "CORE_AT_P2X1A", shas)
    patch.setattr(a1, "OWN", tuple(a1.OWN) + OWN)
    patch.setattr(a1, "_NEW_FILES", tuple(a1._NEW_FILES) + OWN)


def closure_sources_of(sources: dict) -> dict:
    """The closure's sources rebuilt from a dict of the LIVE sources' hashes, through both declared reversals."""
    patcher = x1._Patcher()
    try:
        _install_a1_functions(patcher)
        return a1.p2x1a_sources(sources)
    finally:
        patcher.restore()


def historical_closure_verifies() -> dict:
    """The four things that together mean the historical closure still stands under this stage. It answers, and never
    raises, with the same keys the runtime's lineage gate reads from every successor."""
    try:
        own = proofs()
        standing = _closure_standing()
    except Exception:
        return {"reversal_proven": False, "common_untouched": False, "touched": [], "closure_digest_recomputes": False,
                "closure_record_states_it": False}
    return {"reversal_proven": all(own.values()) and bool(standing["reversal_proven"]),
            "common_untouched": bool(standing["common_untouched"]),
            "touched": list(standing["touched"]),
            "closure_digest_recomputes": bool(standing["closure_digest_recomputes"]),
            "closure_record_states_it": bool(standing["closure_record_states_it"])}


def historical_closure_digest_now() -> str:
    """The closure digest RECOMPUTED from the live tree through both reversals."""
    patcher = x1._Patcher()
    try:
        _install_a1_functions(patcher)
        return a1.historical_closure_digest_now()
    finally:
        patcher.restore()


def amendment_1_verifies() -> dict:
    """The first amendment stands under this stage: its digest recomputes to the certified value and its own declared
    reversal still rebuilds the closure from the text this stage reverses to."""
    try:
        digest = amendment_1_digest_now()
        proven = all(proofs().values())
    except Exception:
        return {"digest_recomputes": False, "reversal_proven": False}
    return {"digest_recomputes": digest == AMENDMENT_1_DIGEST, "reversal_proven": proven}


# The views for the closed packages and for the first amendment's own tests ------------------------------------------

_NAMES = (a1.NEW_PROFILE_FIELD, "amendment_2")


def _without_the_new_names(mapping):
    return {k: v for k, v in mapping.items() if k not in _NAMES}


def _lists_a_new_name(module) -> bool:
    held = getattr(module, "PARAMETERS", None)
    if held is a1._PARAMETERS:
        return True
    return (isinstance(held, dict) and any(name in held for name in _NAMES)
            and str(getattr(module, "__name__", "")).startswith("clinical_core"))


def _lists_the_second_name(module) -> bool:
    held = getattr(module, "PARAMETERS", None)
    return (isinstance(held, dict) and "amendment_2" in held
            and str(getattr(module, "__name__", "")).startswith("clinical_core"))


def _closure_repr(self) -> str:
    """The profile's ``repr`` as the closure's dataclass generated it: without either amendment's field."""
    shown = ", ".join(f"{name}={getattr(self, name)!r}" for name, field in a1._PROFILE_FIELDS.items()
                      if name not in _NAMES and field.repr)
    return f"{type(self).__qualname__}({shown})"


_AUX_NAMES = ("systemic_encephalopathy_burden",)
_AUX_FIELDS = _state.AuxiliaryState.__dataclass_fields__


def _aux_repr(self) -> str:
    """The auxiliary state's ``repr`` as the earlier trees' dataclass generated it: without this stage's memory."""
    shown = ", ".join(f"{name}={getattr(self, name)!r}" for name, field in _AUX_FIELDS.items()
                      if name not in _AUX_NAMES and field.repr)
    return f"{type(self).__qualname__}({shown})"


def _hide_the_aux_field(patch) -> None:
    """The auxiliary state's field list as the earlier trees had it: without this stage's memory."""
    patch.setattr(_state.AuxiliaryState, "__repr__", _aux_repr)
    patch.setattr(_state.AuxiliaryState, "__dataclass_fields__",
                  {k: v for k, v in _AUX_FIELDS.items() if k not in _AUX_NAMES})


def _widen_a1_view(patch) -> None:
    """Everything the first amendment's own view needs to read THROUGH this stage: its text, its widened reversal, and a
    profile listing without this stage's name too."""
    _install_a1_functions(patch)
    patch.setattr(a1, "_without_the_new_name", _without_the_new_names)
    patch.setattr(a1, "_lists_the_new_name", _lists_a_new_name)
    patch.setattr(a1, "_closure_repr", _closure_repr)
    _hide_the_aux_field(patch)


def chain(patch) -> None:
    """For the closed packages' test fixtures: the Phase-2 closure's view, as the first amendment installs it, read
    through this stage (the closure text of every file either amendment changed, the registry and the profile's fields
    without either amendment's name, and every closed listing of clinical_core without either amendment's files)."""
    _widen_a1_view(patch)
    a1.chain(patch)


def tree(patch) -> None:
    """The whole closure tree for the closed packages' own analysis and tests, read through this stage."""
    _widen_a1_view(patch)
    a1.tree(patch)


class closure_view:
    """The whole closure tree while a historical verification runs, outside a test (no monkeypatch there)."""

    def __enter__(self):
        self.patch = x1._Patcher()
        try:
            tree(self.patch)
        except BaseException:
            self.patch.restore()
            raise
        return self

    def __exit__(self, *exc):
        self.patch.restore()
        return False


def _a1_common_untouched() -> dict:
    """Every other source of the closure, as the first amendment's tree holds it."""
    return {relative: hashlib.sha256(a1_bytes(relative)).hexdigest() == sha
            for relative, sha in a1.closure_sources().items() if relative not in a1.REVERSAL}


class _A1File:
    """A file this stage changed, as the FIRST amendment left it, for an audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return a1_text(self.relative)

    def read_bytes(self):
        return a1_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


class _A1Dir:
    """The repository or package directory as the first amendment left it: its text of the files this stage changed, and
    its listings without this stage's own files."""

    def __init__(self, path=CORE_DIR):
        self.path = path

    def __truediv__(self, name):
        target = self.path / name
        relative = target.relative_to(ROOT).as_posix() if ROOT in target.parents or target == ROOT else None
        if relative in REVERSAL:
            return _A1File(relative)
        return _A1Dir(target) if target.is_dir() else target

    def _listing(self, paths):
        return iter([p for p in paths if p.relative_to(ROOT).as_posix() not in OWN])

    def glob(self, pattern):
        return self._listing(sorted(self.path.glob(pattern)))

    def rglob(self, pattern):
        return self._listing(sorted(self.path.rglob(pattern)))

    def __getattr__(self, name):
        return getattr(self.path, name)

    def __fspath__(self):
        return str(self.path)

    def __str__(self):
        return str(self.path)


def amendment_1_tree(patch) -> None:
    """The tree as the FIRST amendment left it, for that amendment's own tests: its files by text, its digest by its
    own definition, and the closure's other files as the closure left them."""
    patch.setattr(a1, "_live", a1_text)
    patch.setattr(a1, "live_core_sources", lambda: a1_sources(live_core_sources()))
    patch.setattr(a1, "common_untouched", _a1_common_untouched)
    patch.setattr(a1, "OWN", tuple(a1.OWN))
    patch.setattr(a1, "_NEW_FILES", tuple(a1._NEW_FILES) + OWN)
    for module in a1._imported_closed_modules() + [_calibration, a1.bf]:
        for attribute in a1._PATH_ATTRIBUTES:
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                patch.setattr(module, attribute, _A1Dir(value))
    # The first amendment's own shape: its profile field is there, this stage's field and memory are not.
    patch.setattr(_dv.CoreProfile, "__dataclass_fields__",
                  {k: v for k, v in a1._PROFILE_FIELDS.items() if k != "amendment_2"})
    for module in [m for m in list(a1.sys.modules.values()) if _lists_the_second_name(m)]:
        patch.setattr(module, "PARAMETERS", {k: v for k, v in module.PARAMETERS.items() if k != "amendment_2"})
    for module_name, attribute in a1.CLOSED_SNAPSHOTS:
        module = __import__(f"clinical_core.{module_name}", fromlist=[attribute])
        patch.setattr(module, attribute, {k: v for k, v in getattr(module, attribute).items() if k != "amendment_2"})
    _hide_the_aux_field(patch)


def non_regression() -> dict:
    """The first amendment reproduces on its own tree, the historical closure recomputes, and nothing else moved."""
    standing = historical_closure_verifies()
    first = amendment_1_verifies()
    return {"amendment_1": first, "historical_closure": standing,
            "pass": first["digest_recomputes"] and first["reversal_proven"] and standing["reversal_proven"]
            and standing["common_untouched"] and standing["closure_digest_recomputes"]
            and standing["closure_record_states_it"]}
