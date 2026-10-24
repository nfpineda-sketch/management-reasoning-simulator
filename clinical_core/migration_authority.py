"""Where migration authority lives (P2H-0, FD-49): outside the candidate, in trusted sources.

A case parameter's value and its provenance claim are supplied by whoever builds the anchors;
neither can authorize itself. This module is the only authority the migration gate consults,
and it never sees a claim: ``AuthoritySession.authorize`` takes the parameter and its value,
nothing else. It resolves authorization from two trusted sources only:

A. repository case truth (``clinical_cases.py``), read here, through a mapping registered in
   ``TRUSTED_CASE_MAPPINGS``: this module reads the source fields itself, checks the
   mapping's preconditions and recomputes the value with the registered rule;
B. ``APPROVED_FAMILY_DEFAULTS``: an approved record for this family and parameter, with its
   value or range.

Which source decides is the parameter's authority policy (P2H-1), declared in
``AUTHORITY_POLICIES``, never by the candidate:
- ``CASE_OVERRIDES_FAMILY_DEFAULT``: verified case truth first; the family default is a
  fallback used only when no case mapping applies. A differing default does not veto case
  truth; the difference is reported;
- ``FAMILY_FIXED``: the approved family value is authoritative; case truth that differs is
  an override the policy does not permit, and blocks;
- ``CASE_REQUIRED``: verified case truth is required; a family default is never a fallback.
A parameter with no declared policy fails closed. The supplied value is then compared with
what the selected authority resolves.

All three registries are empty: no policy is declared, no case parameter is mapped from case
truth yet and no family default is approved.

Nothing the candidate supplies is trusted beyond exact primitive values: a value counts only
as an exact ``int`` or ``float`` (never a subclass, whose ``__float__`` or ``__eq__`` the
candidate controls); the case is verified on a canonical, exact-typed form of its authored
arrival; and after verification only the bank's own case id is used. Registered case mappings that
apply must agree with each other, a broken mapping blocks, and a family holds at most one
approved default per parameter. Every failure is closed.
"""
from __future__ import annotations

import enum
import functools
import hashlib
import inspect
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .state import ARRIVAL_LAYERS, Anchors, FrozenRecord, RhythmCode, RhythmState

#: Kinds of trusted authority.
CASE_MAPPING = "case_mapping"
FAMILY_DEFAULT_REGISTRY = "family_default_registry"
#: The only approval status that authorizes.
APPROVED = "approved"
#: Authority policies (P2H-1): which trusted source decides a parameter.
CASE_OVERRIDES_FAMILY_DEFAULT = "CASE_OVERRIDES_FAMILY_DEFAULT"
FAMILY_FIXED = "FAMILY_FIXED"
CASE_REQUIRED = "CASE_REQUIRED"
POLICIES = (CASE_OVERRIDES_FAMILY_DEFAULT, FAMILY_FIXED, CASE_REQUIRED)


def exact_number(value) -> float | None:
    """``value`` as a float when it is an exact, finite ``int`` or ``float``; ``None`` otherwise.

    Subclasses are refused: they could report one number to this check and carry another. An
    ``int`` the float cannot hold exactly is refused too: it would compare equal to its neighbour.
    """
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    if type(value) is int and number != value:
        return None
    return number if math.isfinite(number) else None


def _text(value) -> bool:
    return type(value) is str and bool(value)


def shown(value) -> str:
    """A candidate's object for a message, without calling any method the candidate could redefine."""
    if value is None or type(value) in (bool, int, float, str):
        return repr(value)
    return f"an object of {type.__repr__(type(value))}"


@dataclass(frozen=True)
class CaseMapping:
    """A registered, deterministic mapping from repository case truth to one parameter.

    ``source_fields`` are dotted paths into the bank's case record (``history.medications``);
    ``precondition`` and ``rule`` receive their values, frozen, keyed by path. The rule is
    code in this registry, never supplied by a candidate. ``precondition`` returns exactly
    ``True`` when the mapping applies (for example, a medication source stated to be
    complete); otherwise the mapping does not apply to the case. ``cases`` limits the mapping
    to named cases; ``None`` applies it to every repository case of ``family``.
    """

    mapping_id: str
    version: str
    family: str
    parameter: str
    source_fields: tuple[str, ...]
    precondition: Callable[[Mapping[str, Any]], bool]
    rule: Callable[[Mapping[str, Any]], float]
    requirements: str
    cases: tuple[str, ...] | None = None

    def __post_init__(self):
        for name in ("mapping_id", "version", "family", "parameter", "requirements"):
            if not _text(getattr(self, name)):
                raise ValueError(f"a case mapping names its {name}")
        if type(self.source_fields) is not tuple or not self.source_fields \
                or not all(_text(path) for path in self.source_fields):
            raise ValueError("a case mapping reads a tuple of at least one named source field")
        if self.cases is not None and (type(self.cases) is not tuple or not all(_text(case) for case in self.cases)):
            raise ValueError("a case mapping's cases are a tuple of case ids, or None")
        # Plain functions only: the digest pins their code, defaults, closure and globals; a
        # callable instance, a bound method or a partial carries state the digest cannot see.
        if not inspect.isfunction(self.precondition) or not inspect.isfunction(self.rule):
            raise ValueError("a case mapping carries its precondition and rule as plain Python functions")


@dataclass(frozen=True)
class ApprovedDefault:
    """An approved family default: an exact value or an inclusive range, with its approval identity."""

    family: str
    parameter: str
    approval_id: str
    version: str
    status: str
    value: float | None = None
    low: float | None = None
    high: float | None = None

    def __post_init__(self):
        for name in ("family", "parameter", "approval_id", "version", "status"):
            if not _text(getattr(self, name)):
                raise ValueError(f"an approved default names its {name}")
        given = {name: getattr(self, name) for name in ("value", "low", "high") if getattr(self, name) is not None}
        if set(given) not in ({"value"}, {"low", "high"}):
            raise ValueError("an approved default is one value or one range (low and high), not both or neither")
        if any(exact_number(number) is None for number in given.values()):
            raise ValueError("an approved default's numbers are exact finite ints or floats")
        if "low" in given and not self.low <= self.high:
            raise ValueError("an approved range has low <= high")

    def holds(self, value: float) -> bool:
        if self.value is not None:
            return value == self.value
        return self.low <= value <= self.high


@dataclass(frozen=True)
class AuthorityPolicy:
    """Which trusted source decides one family parameter (P2H-1). Trusted configuration only."""

    family: str
    parameter: str
    policy: str
    version: str
    rationale: str

    def __post_init__(self):
        for name in ("family", "parameter", "policy", "version", "rationale"):
            if not _text(getattr(self, name)):
                raise ValueError(f"an authority policy names its {name}")
        if self.policy not in POLICIES:
            raise ValueError(f"an authority policy is one of {POLICIES}, not {self.policy!r}")


#: Trusted registry of authority policies. Empty: choosing each parameter's policy is a
#: methodological decision still open (P2H-1), so every parameter fails closed.
AUTHORITY_POLICIES: tuple[AuthorityPolicy, ...] = ()
#: Trusted registry A. Empty: no case parameter is mapped from case truth yet (P2F-11).
TRUSTED_CASE_MAPPINGS: tuple[CaseMapping, ...] = ()
#: Trusted registry B. Empty: no family default is approved.
APPROVED_FAMILY_DEFAULTS: tuple[ApprovedDefault, ...] = ()


_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_TYPES = {"AUTHORITY_POLICIES": AuthorityPolicy, "TRUSTED_CASE_MAPPINGS": CaseMapping,
                   "APPROVED_FAMILY_DEFAULTS": ApprovedDefault}


def registry_fault() -> str:
    """Why a trusted registry is unusable (an entry not of its exact record type), or ``""``."""
    for name, record in _REGISTRY_TYPES.items():
        registry = globals()[name]
        if type(registry) is not tuple or any(type(item) is not record for item in registry):
            return f"the trusted registry {name} holds an entry that is not a {record.__name__}"
    return ""


def _json(data) -> str:
    return json.dumps(data, sort_keys=True)


def _repository_source(module) -> str | None:
    """The digest of a repository module's file; ``None`` for a module outside the repository."""
    path = getattr(module, "__file__", None)
    if type(path) is not str:
        return None
    path = Path(path).resolve()
    if _ROOT not in path.parents:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _in_repository(item) -> bool:
    if _repository_source(inspect.getmodule(item)) is None:
        return False
    code = getattr(item, "__code__", None)
    if code is None or code.co_filename.startswith("<"):
        return True
    return _ROOT in Path(code.co_filename).resolve().parents


def _code_form(code, seen: frozenset) -> dict:
    try:
        source = inspect.getsource(code)
    except (OSError, TypeError):
        source = None
    return {"name": code.co_name, "source": source, "bytecode": None if source is not None else code.co_code.hex(),
            "consts": [_digest_form(item, seen) for item in code.co_consts], "names": list(code.co_names),
            "varnames": list(code.co_varnames), "freevars": list(code.co_freevars)}


def _names(code) -> set[str]:
    names = set(code.co_names)
    for item in code.co_consts:
        if inspect.iscode(item):
            names |= _names(item)
    return names


def _function_form(function, seen: frozenset) -> dict:
    name = f"{function.__module__}.{function.__qualname__}"
    if not _in_repository(function):
        return {"external_function": name}
    if function in seen:
        return {"function": name, "recursive": True}
    seen = seen | {function}
    code = function.__code__
    names = _names(code)
    return {"function": name, "code": _code_form(code, seen),
            "defaults": _digest_form(function.__defaults__, seen),
            "kwdefaults": _digest_form(function.__kwdefaults__, seen),
            "closure": [_digest_form(cell.cell_contents, seen) for cell in function.__closure__ or ()],
            "globals": {key: _digest_form(function.__globals__[key], seen)
                        for key in sorted(names) if key in function.__globals__},
            "builtins": sorted(key for key in names if key not in function.__globals__)}


def _digest_form(value, seen: frozenset = frozenset()):
    """Trusted registry content as plain data a digest pins the same way in every interpreter.

    Code is pinned by its source, constants, defaults, closure and the globals it names;
    repository modules and classes by their file. Anything else whose content cannot be pinned
    this way (an object with an address in its repr, a callable instance, a bound method, a
    partial) raises ``TypeError``: it has no place in a trusted registry.
    """
    kind = type(value)
    if value is None or kind in (bool, int, str):
        return value
    if value is Ellipsis:
        return {"ellipsis": True}
    if kind is float:
        return {"float": value.hex()}
    if kind is complex:
        return {"complex": [value.real.hex(), value.imag.hex()]}
    if kind is bytes:
        return {"bytes": value.hex()}
    if kind in (tuple, list):
        return [_digest_form(item, seen) for item in value]
    if kind in (set, frozenset):
        return {"set": sorted((_digest_form(item, seen) for item in value), key=_json)}
    if kind in (dict, FrozenRecord):
        return {"map": sorted(([_digest_form(key, seen), _digest_form(item, seen)] for key, item in value.items()),
                              key=_json)}
    if inspect.isfunction(value):
        return _function_form(value, seen)
    if inspect.iscode(value):
        return _code_form(value, seen)
    if inspect.ismodule(value):
        return {"module": value.__name__, "source": _repository_source(value)}
    if isinstance(value, enum.Enum):
        return {"enum": f"{kind.__module__}.{kind.__qualname__}", "name": value.name}
    if isinstance(value, type):
        return {"class": f"{value.__module__}.{value.__qualname__}", "source": _repository_source(inspect.getmodule(value))}
    if inspect.isbuiltin(value):
        return {"builtin": f"{getattr(value, '__module__', None)}.{value.__qualname__}"}
    wrapped = getattr(value, "__wrapped__", None)
    if callable(value) and inspect.isfunction(wrapped) and kind.__module__ == "functools":
        return {"wrapper": f"functools.{kind.__qualname__}", "wrapped": _function_form(wrapped, seen)}
    raise TypeError(f"a trusted registry holds a {kind.__module__}.{kind.__qualname__}, whose content the digest "
                    "cannot pin")


def _rule_form(function) -> dict:
    """A registered precondition or rule: code of this repository, pinned whole."""
    if not _in_repository(function):
        raise TypeError(f"a registered rule must be defined in the repository: {function.__module__}."
                        f"{function.__qualname__} is not")
    return _function_form(function, frozenset())


def registry_content() -> dict:
    """The three trusted registries as loaded, for the calibration digest (P2H-1).

    The policies are part of the trust boundary: a changed, added or removed policy, mapping or
    approval changes the digest even when it is not a literal of this file. Raises when a registry
    holds an entry of the wrong type or content the digest cannot pin.
    """
    fault = registry_fault()
    if fault:
        raise TypeError(fault)
    return {"policies": [_digest_form([item.family, item.parameter, item.policy, item.version, item.rationale])
                         for item in AUTHORITY_POLICIES],
            "mappings": [{"mapping_id": item.mapping_id, "version": item.version, "family": item.family,
                          "parameter": item.parameter, "source_fields": list(item.source_fields),
                          "requirements": item.requirements, "cases": _digest_form(item.cases),
                          "precondition": _rule_form(item.precondition), "rule": _rule_form(item.rule)}
                         for item in TRUSTED_CASE_MAPPINGS],
            "defaults": [_digest_form([item.family, item.parameter, item.approval_id, item.version, item.status,
                                       item.value, item.low, item.high]) for item in APPROVED_FAMILY_DEFAULTS]}


@dataclass(frozen=True)
class Confirmation:
    """One trusted source that confirms the value supplied."""

    kind: str
    reference: str
    version: str
    source_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class Authority:
    """What the trusted sources say about one parameter's value.

    ``selected`` is the authority the policy selected, if any; ``confirmations`` holds it only
    when it holds the value supplied. ``policy`` and ``resolved`` say which policy applied and
    what the selected authority resolves (a number, or a range for a family default).
    ``not_used`` lists the trusted sources that existed but did not decide, and why;
    ``conflicts`` lists disagreements, also those precedence resolved. Neither is ever silently
    dropped.
    """

    confirmations: tuple[Confirmation, ...]
    reason: str
    policy: str | None = None
    resolved: Any = None
    not_used: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    selected: Confirmation | None = None

    @property
    def authorized(self) -> bool:
        return bool(self.confirmations)

    def report(self) -> dict:
        """The provenance report: the selected authority, whether it holds the value, and why."""
        selected = self.selected
        return {"kind": None if selected is None else selected.kind,
                "reference": None if selected is None else selected.reference,
                "version": None if selected is None else selected.version,
                "confirmed": self.authorized, "policy": self.policy, "resolved": self.resolved,
                "not_used": list(self.not_used), "conflicts": list(self.conflicts)}


@dataclass(frozen=True)
class CaseVerification:
    """``case_id`` is the bank's own id of the verified case, never the candidate's object."""

    verified: bool
    reason: str
    case_id: str = ""
    family: str = ""


class MissingSourceField(LookupError):
    """A mapping names a source field the repository case does not have."""


# Repository case truth -------------------------------------------------------------------------------

def bank_record(case_id: str) -> FrozenRecord | None:
    """The bank's own record of a case, frozen; ``None`` when no repository case has this exact id."""
    if type(case_id) is not str:
        return None
    from clinical_cases import FAMILIES
    for family in FAMILIES.values():
        for case in family["variants"]:
            if case["id"] == case_id:
                return FrozenRecord(case)
    return None


def read_field(record: Mapping, path: str):
    value = record
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise MissingSourceField(path)
        value = value[part]
    return value


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _record_digest(record: FrozenRecord) -> str:
    return hashlib.sha256(json.dumps(_plain(record), sort_keys=True).encode("utf-8")).hexdigest()


@functools.lru_cache(maxsize=None)
def _repository_arrival(case_id: str, record_digest: str) -> tuple:
    """The canonical authored arrival the frozen legacy path builds for this exact bank record.

    Keyed by the record's digest as well, so a changed case truth is never served stale.
    """
    from .legacy_adapter import anchors_from_legacy, run_legacy
    return canonical_arrival(anchors_from_legacy(run_legacy(case_id, {}, 0).arrival))


def canonical_arrival(anchors: Anchors) -> tuple | None:
    """The authored arrival as exact builtin values, or ``None`` when any field is not of an exact type.

    Comparing this form never calls a method the candidate's objects could redefine.
    """
    if type(anchors) is not Anchors:
        return None
    values = []
    for name in ARRIVAL_LAYERS["authored_observation"]:
        value = object.__getattribute__(anchors, name)
        if name == "rhythm":
            if type(value) is not RhythmState or type(value.code) is not RhythmCode \
                    or type(value.pulse_present) is not bool:
                return None
            rate = None if value.rate_bpm is None else exact_number(value.rate_bpm)
            factor = exact_number(value.output_factor)
            if (value.rate_bpm is not None and rate is None) or factor is None:
                return None
            values.append((name, str.__str__(value.code.value), rate, factor, bool(value.pulse_present)))
        elif name == "consciousness_level":
            if type(value) is not int:
                return None
            values.append((name, int(value)))
        else:
            number = exact_number(value)
            if number is None:
                return None
            values.append((name, number))
    return tuple(values)


def verify_case(family: str, anchors: Anchors) -> CaseVerification:
    """The anchors are a repository case of ``family`` with exactly that case's authored arrival."""
    if type(family) is not str:
        return CaseVerification(False, "the family is not a plain string")
    if type(anchors) is not Anchors:
        return CaseVerification(False, "the anchors are not plain Anchors")
    case_id = object.__getattribute__(anchors, "case_id")
    record = bank_record(case_id)
    if record is None:
        return CaseVerification(False, f"{shown(case_id)} is not a repository case id")
    bank_id = read_field(record, "id")
    try:
        actual = read_field(record, "engine.family")
    except MissingSourceField:
        return CaseVerification(False, f"repository case {bank_id!r} names no family")
    if actual != family:
        return CaseVerification(False, f"the repository places {bank_id!r} in family {actual!r}, not {family!r}")
    observed = canonical_arrival(anchors)
    if observed is None:
        return CaseVerification(False, "the authored arrival holds a value that is not of an exact builtin type")
    try:
        expected = _repository_arrival(bank_id, _record_digest(record))
    except Exception as error:  # an arrival the frozen path cannot build is not verified
        return CaseVerification(False, f"the repository arrival of {bank_id!r} cannot be built: {error}")
    if expected is None or observed != expected:
        differing = [item[0] for item, other in zip(observed, expected or ()) if item != other]
        return CaseVerification(False, f"the authored arrival differs from repository case {bank_id!r} in "
                                       f"{differing or 'its form'}")
    return CaseVerification(True, "repository case verified", bank_id, family)


# Authorization ------------------------------------------------------------------------------------

#: A mapping's verdict on one case: it gives a value, it does not apply, or it is broken.
COMPUTED, NOT_APPLICABLE, BROKEN = "computed", "not applicable", "broken"


def _apply(mapping: CaseMapping, case_id: str) -> tuple[str, float | None, str]:
    """The value the mapping recomputes from the case truth, independently of any value supplied."""
    if mapping.cases is not None and case_id not in mapping.cases:
        return NOT_APPLICABLE, None, f"{mapping.mapping_id}: does not apply to {case_id!r}"
    record = bank_record(case_id)
    try:
        fields = FrozenRecord({path: read_field(record, path) for path in mapping.source_fields})
    except MissingSourceField as missing:
        return BROKEN, None, f"{mapping.mapping_id}: source field {missing.args[0]!r} does not exist in {case_id!r}"
    try:
        applies = mapping.precondition(fields)
    except Exception as error:
        return BROKEN, None, f"{mapping.mapping_id}: the precondition failed ({type(error).__name__})"
    if applies is not True:
        return NOT_APPLICABLE, None, (f"{mapping.mapping_id}: the case truth does not meet its precondition "
                                      f"({mapping.requirements})")
    try:
        recomputed = exact_number(mapping.rule(fields))
    except Exception as error:
        return BROKEN, None, f"{mapping.mapping_id}: the rule failed ({type(error).__name__})"
    if recomputed is None:
        return BROKEN, None, f"{mapping.mapping_id}: the rule gives no exact finite number for {case_id!r}"
    return COMPUTED, recomputed, ""


def policy_for(family: str, parameter: str) -> tuple[AuthorityPolicy | None, str]:
    """The one trusted policy declared for this parameter, or why there is none."""
    fault = registry_fault()
    if fault:
        return None, fault
    registered = [item for item in AUTHORITY_POLICIES if item.family == family and item.parameter == parameter]
    if not registered:
        return None, f"no authority policy is declared for {family}/{parameter}"
    if len(registered) > 1:
        return None, f"{len(registered)} authority policies are declared for {family}/{parameter}"
    return registered[0], ""


def _holds(record: ApprovedDefault) -> Any:
    return record.value if record.value is not None else [record.low, record.high]


class AuthoritySession:
    """Authorization for one family and one set of anchors; the case is verified once, when needed."""

    def __init__(self, family: str, anchors: Anchors):
        self.family = family
        self.anchors = anchors
        self._verification: CaseVerification | None = None

    def verification(self) -> CaseVerification:
        if self._verification is None:
            self._verification = verify_case(self.family, self.anchors)
        return self._verification

    def authorize(self, parameter: str, value) -> Authority:
        """Recompute authorization from the trusted sources. No claim is an input.

        The parameter's declared policy selects the authority (see the module docstring); the
        supplied value is authorized only when the selected authority holds it.
        """
        fault = registry_fault()
        if fault:
            return Authority((), fault)
        trusted_policy, why = policy_for(self.family, parameter)
        policy = None if trusted_policy is None else trusted_policy.policy
        mappings = [item for item in TRUSTED_CASE_MAPPINGS if item.family == self.family and item.parameter == parameter]
        defaults = [item for item in APPROVED_FAMILY_DEFAULTS
                    if item.family == self.family and item.parameter == parameter]
        if not mappings and not defaults:
            return Authority((), "no trusted source holds this parameter: no registered case mapping and no "
                                 "approved family default", policy)
        if trusted_policy is None:
            return Authority((), why)
        number = exact_number(value)
        if number is None:
            return Authority((), f"{shown(value)} is not an exact finite int or float", policy)
        verification = self.verification()
        if not verification.verified:
            return Authority((), f"case not verified: {verification.reason}", policy)
        computed, broken, not_used, conflicts = [], [], [], []
        for mapping in mappings:
            verdict, recomputed, reason = _apply(mapping, verification.case_id)
            if verdict == COMPUTED:
                computed.append((mapping, recomputed))
            elif verdict == BROKEN:
                broken.append(reason)
            else:
                not_used.append(reason)
        approved = [item for item in defaults if item.status == APPROVED]
        not_used += [f"{item.approval_id}: status {item.status!r} does not authorize" for item in defaults
                     if item.status != APPROVED]

        def refuse(reason: str, selected: Confirmation | None = None, resolved=None) -> Authority:
            return Authority((), reason, policy, resolved, tuple(not_used), tuple(conflicts), selected)

        if broken:
            return refuse("a registered case mapping is broken: " + "; ".join(broken))
        if len({value_ for _, value_ in computed}) > 1:
            conflicts.append("case mappings disagree: " + ", ".join(f"{item.mapping_id} -> {value_!r}"
                                                                  for item, value_ in computed))
            return refuse("the registered case mappings disagree on the case truth")
        if len(approved) > 1:
            conflicts.append("approved defaults: " + ", ".join(item.approval_id for item in approved))
            return refuse(f"{len(approved)} approved family defaults are registered for this parameter")
        case = computed[0] if computed else None
        default = approved[0] if approved else None
        case_note = ("" if case is None else
                     f"{case[0].mapping_id} v{case[0].version} -> {case[1]!r}")
        default_note = ("" if default is None else
                        f"{default.approval_id} v{default.version} holds {_holds(default)!r}")
        # Mappings that agree with the first: registry order selects one; the others are reported.
        not_used += [f"{item.mapping_id} v{item.version} -> {value_!r}: agrees with {case_note}, which the registry "
                     "order selects" for item, value_ in computed[1:]]
        differ = case is not None and default is not None and not default.holds(case[1])
        if policy == CASE_OVERRIDES_FAMILY_DEFAULT:
            if case is not None:
                selected = Confirmation(CASE_MAPPING, case[0].mapping_id, case[0].version, case[0].source_fields)
                resolved = case[1]
                if default is not None:
                    not_used.append(f"{default_note}: not used, verified case truth takes precedence")
                    if differ:
                        conflicts.append(f"case truth {case_note} differs from the family default {default_note}: "
                                         "resolved by precedence (case overrides the default)")
            elif default is not None:
                selected = Confirmation(FAMILY_DEFAULT_REGISTRY, default.approval_id, default.version)
                resolved = _holds(default)
            else:
                return refuse("no applicable case mapping and no approved family default")
        elif policy == FAMILY_FIXED:
            if default is None:
                if case is not None:
                    not_used.append(f"{case_note}: a case value cannot decide a FAMILY_FIXED parameter")
                return refuse("FAMILY_FIXED: no approved family default")
            selected = Confirmation(FAMILY_DEFAULT_REGISTRY, default.approval_id, default.version)
            resolved = _holds(default)
            if differ:
                conflicts.append(f"case truth {case_note} differs from the fixed family value {default_note}")
                return refuse("FAMILY_FIXED: the case truth differs from the approved family value, and a case "
                              "override is not permitted", selected, resolved)
            if case is not None:
                not_used.append(f"{case_note}: agrees, but the family value is authoritative")
                if number != case[1]:
                    conflicts.append(f"the value supplied, {number!r}, differs from verified case truth {case_note}; "
                                     "the approved family range holds both, and FAMILY_FIXED lets the family value "
                                     "decide")
        elif policy == CASE_REQUIRED:
            if default is not None:
                not_used.append(f"{default_note}: a family default is not a permitted fallback under CASE_REQUIRED")
                if differ:
                    conflicts.append(f"case truth {case_note} differs from the family default {default_note}")
            if case is None:
                return refuse("CASE_REQUIRED: no applicable case mapping gives verified case truth")
            selected = Confirmation(CASE_MAPPING, case[0].mapping_id, case[0].version, case[0].source_fields)
            resolved = case[1]
        else:  # unreachable: AuthorityPolicy validates its policy
            return refuse(f"unknown authority policy {policy!r}")
        holds = number == resolved if selected.kind == CASE_MAPPING else default.holds(number)
        if not holds:
            if selected.kind == CASE_MAPPING:
                reason = f"{selected.reference}: case truth maps to {resolved!r}, not {number!r}"
            else:
                reason = f"{selected.reference}: the approved default does not hold {number!r}"
            return refuse(reason, selected, resolved)
        return Authority((selected,), "confirmed", policy, resolved, tuple(not_used), tuple(conflicts), selected)
