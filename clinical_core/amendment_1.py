"""PHASE2_AMENDMENT_1: the formal successor stage of the closed Phase-2 common core (shadow only).

Phase 2 closed at d2cca46 with the digest 22b90a6f... over 141 sources, and that closure is NOT rewritten here.
This stage follows it the way every stage of the chain followed its predecessor: it DECLARES what it inserted
into the one common file it changed (``derived.py``), so the predecessor's file is rebuilt from the live one by
reversing those insertions and proven by its SHA. Every historical reconstruction further down the chain
(P2X-1, P2W-1, ... P2O-1) then reads the closure text again, and every historical freeze digest recomputes to
the value it was pinned at.

What the stage adds to the physiology is one explicit control and nothing else:
``CoreProfile.hypoventilation_oxygenation_transmission_fraction``, the share of the already-existing P2T-5
relative alveolar-gas link that is expressed (delta_PaO2 = share x (-delta_PaCO2 / R)). None is UNSCALED and
reproduces the certified behaviour bit for bit; 0 expresses nothing, in every state; 1 is the certified full
transmission. No committed profile declares it, so no committed behaviour changes.

The view this module installs (``chain`` / ``tree``) is for the closed packages' test fixtures and for the
historical verification of the closure: it shows them the tree as P2X-1A left it -- the closure text of
``derived.py`` by ``_live``, by path and by ``inspect``, the parameter registry and the profile's field list
without this stage's name, and the listings of ``clinical_core`` without this stage's file. It changes no
behaviour: a view of the source, not of the physiology.

The amended core's own digest lives OUTSIDE this package (the amendment record and the runtime's certified
lineage), because it covers this file too.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
import types
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import closure_guard as cg
from . import derived as dv
from . import distributive_tone as dt
from . import tone_domain as x1

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "PHASE2_AMENDMENT_1"
PREDECESSOR = "P2X-1A"
DECIDED = "2026-11-10"
OWN = ("clinical_core/amendment_1.py",)
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_1.json"
CLOSURE_RECORD = ROOT / "docs" / "revision" / "P2X3_phase2_closure.json"
#: What the stage registers, as each stage did: its own module is not a source of the decision pack.
TUPLES_ADDED = {"PACK_DIGEST_EXCLUDED": OWN}
#: The one name this stage adds to the live module: a profile field and its entry in the parameter registry.
NEW_PROFILE_FIELD = "hypoventilation_oxygenation_transmission_fraction"
#: The historical closure this stage succeeds. Immutable: named here to be VERIFIED, never to be replaced.
HISTORICAL_CLOSURE_HEAD = "d2cca46626ed5d45a792ec9456d46fb75fe87731"
HISTORICAL_CLOSURE_DIGEST = "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
#: The predecessor's own freeze digest, as the closure record holds it (freeze_digests.closure_guard_P2X1A).
P2X1A_FREEZE_DIGEST = "eca47d357674ec56fe489c30f1757cf940c55a4e5d5edb2a9ffb9fac0213e853"

#: What this stage inserted, as (live text, text before): reversing them in order gives the closure file.
REVERSAL = {
    'clinical_core/decision_pack.py': (
        (('                        "clinical_core/closure_guard.py", "clinical_core/closure_guard_report.py",\n'
          '                        "clinical_core/amendment_1.py")\n'),
         ('                        "clinical_core/closure_guard.py", "clinical_core/closure_guard_report.py")\n')),
    ),
    'clinical_core/derived.py': (
        (('    # PHASE2_AMENDMENT_1: how much of the P2T-5 relative alveolar-gas link is EXPRESSED. The link itself is\n'
          '    # declared by respiratory_quotient; this scales what it transmits:\n'
          '    #     delta_PaO2 = fraction x (-delta_PaCO2 / respiratory_quotient)\n'
          "    # 0 transmits nothing (SpO2 is P2O-3's exactly), 1 is the certified full transmission, between is a\n"
          '    # partial structural transmission. None means UNSCALED, so a profile that does not opt in reproduces\n'
          '    # the certified P2T-5 behaviour bit for bit -- it is NOT a second off switch for the link. It is not a\n'
          '    # respiratory quotient, not a shunt fraction, not an FiO2 gain, not G retention, not a mechanics\n'
          '    # efficiency and not a central availability: it never multiplies retained(G) and never touches RR, W,\n'
          '    # PaCO2, the drive, L or the tone. Declared only together with the link it scales. No value is chosen\n'
          '    # here.\n'
          '    hypoventilation_oxygenation_transmission_fraction: float | None = None\n'),
         ''),
        (('        share = self.hypoventilation_oxygenation_transmission_fraction\n'
          '        if share is not None:\n'
          '            if isinstance(share, bool) or not isinstance(share, (int, float)) or not math.isfinite(share) \\\n'
          '                    or not 0.0 <= share <= 1.0:\n'
          '                # PHASE2_AMENDMENT_1: UNSCALED is None (the certified full transmission); declared, it is a\n'
          '                # share of that transmission, so it lives in [0, 1] and nowhere else.\n'
          '                raise CoreInvariantError("hypoventilation_oxygenation_transmission_fraction is None "\n'
          '                                         "(UNSCALED: the certified full transmission) or a share in [0, 1]")\n'
          '            if rq is None:\n'
          '                # A share of a link that is not declared is half-defined, like the hypoxaemic pair below.\n'
          '                raise CoreInvariantError("hypoventilation_oxygenation_transmission_fraction scales the "\n'
          '                                         "hypoventilation -> oxygenation link, so it is declared only with it")\n'),
         ''),
        (('    "hypoventilation_oxygenation_transmission_fraction": (\n'
          '        PROVISIONAL, "UNSCALED (PHASE2_AMENDMENT_1): the share of the common relative alveolar link that is "\n'
          '                     "EXPRESSED, delta_PaO2 = fraction x (-delta_PaCO2 / R); None by default, which "\n'
          '                     "reproduces the certified P2T-5 full transmission bit for bit, 0 transmits nothing and "\n'
          '                     "1 is that full transmission. It controls how much the RELATIVE alveolar-gas link is "\n'
          '                     "expressed and is NOT a respiratory quotient, a shunt fraction, an FiO2 gain, a G "\n'
          '                     "retention, a mechanics efficiency or a central availability; it never multiplies "\n'
          '                     "retained(G) and has no direct effect on RR, W, PaCO2, the drive, L or the tone. "\n'
          '                     "Declared only with the link it scales; no value is approved"),\n'),
         ''),
        (('    # PHASE2_AMENDMENT_1: the share of that transmission the profile expresses. A share of 0 expresses nothing,\n'
          '    # so it needs no PaCO2 and is decided FIRST: SpO2_base itself comes back in every state, the unventilated\n'
          '    # boundary included, which is what makes "share 0" the same as "link not declared" and not merely close\n'
          '    # to it (no read of the respiration, no round trip through the dissociation relation).\n'
          '    share = profile.hypoventilation_oxygenation_transmission_fraction\n'
          '    if share == 0.0:\n'
          '        return spo2_base\n'),
         ''),
        (('    # None is UNSCALED, so the certified behaviour is reproduced exactly (1.0 x d == d in IEEE 754). Nothing\n'
          "    # else in the chain changes: G, FiO2, the latent PaO2 and the ODC are P2T-5's.\n"
          '    if share is None:\n'
          '        share = 1.0\n'
          '    return oxygen_saturation_from_pao2(pao2_from_oxygen_saturation(spo2_base)\n'
          '                                       - share * delta / profile.respiratory_quotient)\n'),
         ('    return oxygen_saturation_from_pao2(pao2_from_oxygen_saturation(spo2_base) - delta / profile.respiratory_quotient)\n')),
    ),
}

#: The changed files as the closure left them (the closure record's own SHAs): the one common source of the
#: physiology, and the registration every stage makes in the pack's exclusion tuple.
CORE_AT_P2X1A = {'clinical_core/decision_pack.py': '4f35b6989b9778d3df8cdfa9c1ba239e6df46de127416921797b5e2114a03c62',
                 'clinical_core/derived.py': '61f02bef25e7c330e1c8d1b725a22b8dc479b6c96ac0c2d0360bc11351336936'}


def core_digest(sources: dict) -> str:
    """The digest of a ``path -> sha256`` map of the package's sources, as the closure record defines it."""
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def closure_sources() -> dict:
    """The closure record's own source map: the immutable statement this stage reverses to. The record is read,
    never trusted blindly: it must still state the historical closure, or nothing here is a proof of it."""
    record = json.loads(CLOSURE_RECORD.read_text(encoding="utf-8"))
    sources = dict(record["sources"])
    if record.get("phase2_digest") != HISTORICAL_CLOSURE_DIGEST or core_digest(sources) != HISTORICAL_CLOSURE_DIGEST:
        raise AssertionError("the Phase-2 closure record no longer states the historical closure")
    return sources


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2X1A[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    """Every other source of the closure is byte for byte what the closure record says."""
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in closure_sources().items() if relative not in REVERSAL}


def p2x1a_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2X-1A file plus PHASE2_AMENDMENT_1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2x1a_bytes(relative: str) -> bytes:
    return p2x1a_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2x1a_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2X1A.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def live_core_sources() -> dict:
    """The package's sources as the tree stands, by the closure record's own definition of a source."""
    paths = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "clinical_core").rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}


def amended_core_digest_now() -> str:
    """The digest of the amended tree, this file included. Its certified value is recorded outside the package."""
    return core_digest(live_core_sources())


def historical_closure_digest_now() -> str:
    """The closure digest RECOMPUTED from the live tree by reversing this stage's declared insertions. It equals
    HISTORICAL_CLOSURE_DIGEST only while the reversal is exact and nothing else in the package moved."""
    return core_digest(p2x1a_sources(live_core_sources()))


def historical_closure_verifies() -> dict:
    """The four things that together mean the historical closure still stands under this stage."""
    untouched = common_untouched()
    return {"reversal_proven": all(proofs().values()),
            "common_untouched": all(untouched.values()),
            "touched": sorted(relative for relative, same in untouched.items() if not same),
            "closure_digest_recomputes": historical_closure_digest_now() == HISTORICAL_CLOSURE_DIGEST,
            "closure_record_states_it": core_digest(closure_sources()) == HISTORICAL_CLOSURE_DIGEST}


# The view of the P2X-1A tree, for the closed packages --------------------------------------------------------------

#: The closed package whose own list of untouched files still reads the live bytes: P2X-1A's.
CLOSED_COMMON = ("closure_guard",)
PATH_READERS = cg.PATH_READERS
_NEW_FILES = OWN
#: The names under which a closed package holds the repository or the package directory. ``REPOSITORY`` is the
#: calibration harness's: the lactate slice and the decision pack hash the sources through it, and no earlier stage
#: had to redirect it because each regenerated those two documents in place. This one leaves them as the closure
#: recorded them, so their digests are recomputed on the closure tree like every other.
_PATH_ATTRIBUTES = ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE", "REPOSITORY")
_FREEZE_SOURCES = bf.freeze_sources
#: The closed packages' own import-time copies of a live listing (the precedent is P2W-1's ``CLOSED_SNAPSHOTS``):
#: taken when the module loads, before any view, so each carries this stage's name until it is dropped here.
CLOSED_SNAPSHOTS = (("oxygenation_link", "P2T3_PARAMETERS"),)
_PARAMETERS = dv.PARAMETERS
_PROFILE_FIELDS = dv.CoreProfile.__dataclass_fields__


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2x1a_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


class _InspectView:
    """``inspect`` for a closed package reading the live core by source: the closure text of the file this stage
    changed, the real thing for everything else."""

    def getsource(self, obj):
        if isinstance(obj, types.ModuleType):
            relative = f"{getattr(obj, '__name__', '').replace('.', '/')}.py"
            if relative in REVERSAL:
                return p2x1a_text(relative)
        return inspect.getsource(obj)

    def __getattr__(self, name):
        return getattr(inspect, name)


def _old_only(paths) -> list:
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in _NEW_FILES]


class _TreeFile:
    """The file this stage changed as the closure left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2x1a_text(self.relative)

    def read_bytes(self):
        return p2x1a_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


class _TreeDir:
    """A closed package's ``ROOT`` or ``CORE_DIR``: the closure text of this stage's changed file, the live path of
    anything else, and its listings without this stage's new file."""

    def __init__(self, path=CORE_DIR):
        self.path = path

    def __truediv__(self, name):
        target = self.path / name
        relative = target.relative_to(ROOT).as_posix() if ROOT in target.parents or target == ROOT else None
        if relative in REVERSAL:
            return _TreeFile(relative)
        return _TreeDir(target) if target.is_dir() else target

    def glob(self, pattern):
        return iter(_old_only(sorted(self.path.glob(pattern))))

    def rglob(self, pattern):
        return iter(_old_only(sorted(self.path.rglob(pattern))))

    def __getattr__(self, name):
        return getattr(self.path, name)

    def __fspath__(self):
        return str(self.path)

    def __str__(self):
        return str(self.path)


def _carries(value, kind=None) -> bool:
    kind = _TreeDir if kind is None else kind
    while value is not None and not isinstance(value, Path):
        if isinstance(value, kind):
            return True
        value = getattr(value, "path", None)
    return False


def _rebuilt(value):
    if isinstance(value, Path):
        return _TreeDir(value)
    inner = getattr(value, "path", None)
    rebuilt = None if inner is None else _rebuilt(inner)
    return None if rebuilt is None else type(value)(rebuilt)


def _imported_closed_modules() -> list:
    return [__import__(f"clinical_core.{name}", fromlist=["ROOT"]) for name in PATH_READERS] + [dt, x1, cg]


def _without_the_new_name(mapping):
    return {k: v for k, v in mapping.items() if k != NEW_PROFILE_FIELD}


def _lists_the_new_name(module) -> bool:
    """Whether a module's ``PARAMETERS`` is the live registry, or a clinical_core copy of it that still carries
    this stage's name."""
    held = getattr(module, "PARAMETERS", None)
    if held is _PARAMETERS:
        return True
    return (isinstance(held, dict) and NEW_PROFILE_FIELD in held
            and str(getattr(module, "__name__", "")).startswith("clinical_core"))


def _closure_repr(self) -> str:
    """The profile's ``repr`` as the closure's dataclass generated it: the same text, without this stage's field.
    A closed probe (P2X-1's X12) hashes ``str(profile)`` inside its course digests, so the representation is part
    of what the closure froze -- and the generated ``__repr__`` names every field of the live class."""
    shown = ", ".join(f"{name}={getattr(self, name)!r}" for name, field in _PROFILE_FIELDS.items()
                      if name != NEW_PROFILE_FIELD and field.repr)
    return f"{type(self).__qualname__}({shown})"


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2X-1A's view reads the closure file (proven), by ``_live``, by path
    and by source; the parameter registry and the profile's field list are the closure's; and every closed listing
    of clinical_core leaves this stage's file out. The stage adds one UNSET control: no behaviour changes."""
    patch.setattr(cg, "_live", p2x1a_text)
    patch.setattr(cg, "_FREEZE_SOURCES", lambda: p2x1a_sources(_FREEZE_SOURCES()))
    patch.setattr(cg, "inspect", _InspectView())
    for module_name in CLOSED_COMMON:
        module = __import__(f"clinical_core.{module_name}", fromlist=["common_untouched"])
        patch.setattr(module, "common_untouched", _closed_common_untouched(module))
    for module in _imported_closed_modules():
        for attribute in _PATH_ATTRIBUTES:
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                patch.setattr(module, attribute, _TreeDir(value))
            elif value is not None and not _carries(value):
                rebuilt = _rebuilt(value)
                if rebuilt is not None:
                    patch.setattr(module, attribute, rebuilt)
    # The live module's own listings, at their root, so every closed reader sees the closure's whatever view of
    # its own it installs on top: the registry by identity (a module may hold its own reference to the mapping),
    # and the profile's fields on the class itself (``dataclasses.fields``, ``replace`` and ``to_dict`` read it).
    # Another chain may have run first and left its own copy of the registry in place (they are applied in no
    # fixed order), so the name is dropped from whatever each module holds now, not only from the original.
    for module in [m for m in list(sys.modules.values()) if _lists_the_new_name(m)]:
        patch.setattr(module, "PARAMETERS", _without_the_new_name(module.PARAMETERS))
    for module_name, attribute in CLOSED_SNAPSHOTS:
        module = __import__(f"clinical_core.{module_name}", fromlist=[attribute])
        patch.setattr(module, attribute, _without_the_new_name(getattr(module, attribute)))
    patch.setattr(dv.CoreProfile, "__dataclass_fields__", _without_the_new_name(_PROFILE_FIELDS))
    patch.setattr(dv.CoreProfile, "__repr__", _closure_repr)
    from . import decision_pack
    patch.setattr(decision_pack, "PACK_DIGEST_EXCLUDED",
                  tuple(name for name in decision_pack.PACK_DIGEST_EXCLUDED if name not in OWN))


_CG_TREE = cg.tree


def _cg_tree(patch) -> None:
    """P2X-1A's own whole-tree view, nested inside this stage's."""
    _CG_TREE(patch)
    for module in _imported_closed_modules():
        if module is cg:
            continue
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if _carries(value) and not _carries(value, cg._TreeDir):
                patch.setattr(module, attribute, cg._TreeDir(value))


def tree(patch) -> None:
    """The whole P2X-1A tree -- the closure's -- for P2X-1A's own analysis and tests."""
    chain(patch)
    patch.setattr(cg, "tree", _cg_tree)
    patch.setattr(bf, "freeze_sources", lambda: p2x1a_sources(_FREEZE_SOURCES()))


class closure_view:
    """The whole closure tree while a historical verification runs, outside a test (no monkeypatch there)."""

    def __enter__(self):
        self.patch = x1._Patcher()
        tree(self.patch)
        return self

    def __exit__(self, *exc):
        self.patch.restore()
        return False


def p2x1a_digest() -> str:
    """P2X-1A's own freeze digest, computed on the tree it was frozen against."""
    with closure_view():
        return cg.freeze_digest()


def non_regression() -> dict:
    """The predecessor reproduces on its own tree; the closure digest recomputes; nothing else moved."""
    standing = historical_closure_verifies()
    return {"p2x1a_freeze_digest": p2x1a_digest() == P2X1A_FREEZE_DIGEST,
            "historical_closure": standing,
            "pass": p2x1a_digest() == P2X1A_FREEZE_DIGEST and standing["reversal_proven"]
            and standing["common_untouched"] and standing["closure_digest_recomputes"]
            and standing["closure_record_states_it"]}
