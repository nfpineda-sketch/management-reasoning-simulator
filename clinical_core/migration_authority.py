"""Where migration authority lives (P2H-0, FD-49): outside the candidate, in trusted sources.

A case parameter's value and its provenance claim are supplied by whoever builds the anchors;
neither can authorize itself. This module is the only authority the migration gate consults,
and it never sees a claim: ``AuthoritySession.authorize`` takes the parameter and its value,
nothing else. It resolves authorization from two trusted sources only:

A. repository case truth (``clinical_cases.py``), read here, through a mapping registered in
   ``TRUSTED_CASE_MAPPINGS``: this module reads the source fields itself, checks the
   mapping's preconditions, recomputes the value with the registered rule and compares it
   with the value supplied;
B. ``APPROVED_FAMILY_DEFAULTS``: an approved record for this family and parameter whose
   value or range holds the value supplied.

Both registries are empty: no case parameter is mapped from case truth yet and no family
default is approved.

Nothing the candidate supplies is trusted beyond exact primitive values: a value counts only
as an exact ``int`` or ``float`` (never a subclass, whose ``__float__`` or ``__eq__`` the
candidate controls); the case is verified on a canonical, exact-typed form of its authored
arrival; and after verification only the bank's own case id is used. Every applicable trusted
source must agree: one that holds a different value blocks (a mapping whose precondition is not
met does not apply). Every failure is closed.
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .state import ARRIVAL_LAYERS, Anchors, FrozenRecord, RhythmCode, RhythmState

#: Kinds of trusted authority.
CASE_MAPPING = "case_mapping"
FAMILY_DEFAULT_REGISTRY = "family_default_registry"
#: The only approval status that authorizes.
APPROVED = "approved"


def exact_number(value) -> float | None:
    """``value`` as a float when it is an exact, finite ``int`` or ``float``; ``None`` otherwise.

    Subclasses are refused: they could report one number to this check and carry another.
    """
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def _text(value) -> bool:
    return type(value) is str and bool(value)


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
        if not callable(self.precondition) or not callable(self.rule):
            raise ValueError("a case mapping carries its precondition and rule as code")


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


#: Trusted registry A. Empty: no case parameter is mapped from case truth yet (P2F-11).
TRUSTED_CASE_MAPPINGS: tuple[CaseMapping, ...] = ()
#: Trusted registry B. Empty: no family default is approved.
APPROVED_FAMILY_DEFAULTS: tuple[ApprovedDefault, ...] = ()


@dataclass(frozen=True)
class Confirmation:
    """One trusted source that confirms the value supplied."""

    kind: str
    reference: str
    version: str
    source_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class Authority:
    """What the trusted sources say about one parameter's value: the confirmations, or why none."""

    confirmations: tuple[Confirmation, ...]
    reason: str

    @property
    def authorized(self) -> bool:
        return bool(self.confirmations)


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
        return CaseVerification(False, f"{case_id!r} is not a repository case id")
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

#: A mapping's verdict on one case: it confirms, it holds another value, or it does not apply.
CONFIRMS, DIFFERS, NOT_APPLICABLE, BROKEN = "confirms", "differs", "not applicable", "broken"


def _apply(mapping: CaseMapping, case_id: str, value: float) -> tuple[str, Confirmation | None, str]:
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
    if recomputed != value:
        return DIFFERS, None, f"{mapping.mapping_id}: case truth maps to {recomputed!r}, not {value!r}"
    return CONFIRMS, Confirmation(CASE_MAPPING, mapping.mapping_id, mapping.version, mapping.source_fields), ""


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

        Every applicable trusted source must agree with the value: a mapping or an approved
        default that holds another value, or a broken mapping, blocks; a mapping whose
        precondition the case does not meet does not apply.
        """
        mappings = [item for item in TRUSTED_CASE_MAPPINGS if item.family == self.family and item.parameter == parameter]
        defaults = [item for item in APPROVED_FAMILY_DEFAULTS
                    if item.family == self.family and item.parameter == parameter]
        if not mappings and not defaults:
            return Authority((), "no trusted source holds this parameter: no registered case mapping and no "
                                 "approved family default")
        number = exact_number(value)
        if number is None:
            return Authority((), f"{value!r} is not an exact finite int or float")
        verification = self.verification()
        if not verification.verified:
            return Authority((), f"case not verified: {verification.reason}")
        confirmations, against, reasons = [], [], []
        for mapping in mappings:
            verdict, confirmation, reason = _apply(mapping, verification.case_id, number)
            if verdict == CONFIRMS:
                confirmations.append(confirmation)
            else:
                reasons.append(reason)
                if verdict in (DIFFERS, BROKEN):
                    against.append(reason)
        for record in defaults:
            if record.status != APPROVED:
                reasons.append(f"{record.approval_id}: status {record.status!r} does not authorize")
            elif not record.holds(number):
                reason = f"{record.approval_id}: the approved default does not hold {number!r}"
                reasons.append(reason)
                against.append(reason)
            else:
                confirmations.append(Confirmation(FAMILY_DEFAULT_REGISTRY, record.approval_id, record.version))
        if against:
            return Authority((), "the trusted sources do not all agree with this value: " + "; ".join(against))
        return Authority(tuple(confirmations), "; ".join(reasons) or "confirmed")
