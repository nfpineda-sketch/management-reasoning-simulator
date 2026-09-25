"""What an encounter is judged against, frozen when it starts.

Faculty instruction of 2026-09-25: an encounter keeps a versioned copy of the
opportunities, critical events and other declarations its evaluation rests on,
with the versions of the catalogue, the engine and the rubric that produced
them. Analysing it, or regenerating its documents, reads that copy. A later
change to a case, a catalogue or a declaration does not silently change how an
earlier encounter is judged.

Where the copy lives: ``record["encounter"]["evaluation_basis"]``, written once
by ``curriculum_runtime.start_encounter`` together with the rest of the
encounter. The account store never updates that column, so the copy cannot be
overwritten afterwards.

Every record resolves to exactly one status, and the statuses are never
merged, because they mean different things to a reviewer:

* ``frozen`` -- the record carries its own basis;
* ``legacy`` -- a bank case saved before copies existed: it is judged with the
  declarations as they stood until 2026-09-25 (``evaluation_bases/``), and the
  limitation says that the version in force when it was launched cannot be
  verified. Nothing attributes a verified version to it;
* ``unfrozen_current`` -- a case the legacy snapshot does not know, saved
  without a copy: the current declarations are used and the limitation says so;
* ``generated`` -- a generated case: nothing was declared before it, so there
  are no opportunities and no critical events to read, and none are invented;
* ``no_authored_case`` -- the encounter names no authored case at all;
* ``unknown_case`` -- the record names a case that no declaration knows: an
  invalid identifier, reported as such;
* ``corrupt`` -- the record, or its frozen copy, cannot be read or does not
  match its own fingerprint.

A re-evaluation with the current criteria is explicit (``reevaluation``): it
needs a reason and a person, it returns a new basis that names the previous
one, and it never replaces the copy the encounter was launched with or any
confirmed faculty decision.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

SCHEMA = "mrs.evaluation_basis.v1"
LEGACY_PATH = Path(__file__).resolve().parent / "evaluation_bases" / "coverage_1.0_legacy.json"
STATUSES = ("frozen", "legacy", "unfrozen_current", "generated", "no_authored_case", "unknown_case",
            "corrupt", "reevaluation")
# The statuses under which the declarations can be read. The others carry no
# declaration, and an analysis must say so rather than score as if there were one.
READABLE = frozenset({"frozen", "legacy", "unfrozen_current", "reevaluation"})
_LEGACY = None


class EvaluationBasisError(ValueError):
    """A basis that cannot be built or read. Never hidden behind a generic failure."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


def fingerprint(declaration):
    return hashlib.sha256(_canonical(_plain(declaration)).encode("utf-8")).hexdigest()


def _tupled(value):
    """Back to the declarations' own shape: every sequence in them is a tuple."""
    if isinstance(value, dict):
        return {key: _tupled(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_tupled(item) for item in value)
    return value


def legacy():
    """The declarations as they stood until 2026-09-25, before copies were frozen."""
    global _LEGACY
    if _LEGACY is None:
        record = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
        if fingerprint(record["declarations"]) != record["fingerprint"]:
            raise EvaluationBasisError("The legacy evaluation snapshot does not match its fingerprint.")
        _LEGACY = record
    return _LEGACY


def _is_generated(case_id, spec=None):
    spec = spec if isinstance(spec, dict) else {}
    return (str(case_id or "").startswith("AI-") or spec.get("case_family") == "generated"
            or (spec.get("provenance") or {}).get("source") == "ai")


def _current(case_id):
    """(declaration, source) from the code as it is now, or (None, None)."""
    from case_assessment_bank import CANDIDATES, CASES
    if case_id in CASES:
        return CASES[case_id], "bank"
    if case_id in CANDIDATES:
        return CANDIDATES[case_id], "catalog_candidate"
    return None, None


def versions(case_id=None):
    """The versions an evaluation of this case depends on, as the code stands."""
    import family_engine
    import glucose_rescue
    import rubric
    from case_assessment import COVERAGE_VERSION
    found = {"coverage": COVERAGE_VERSION, "rubric": rubric.VERSION,
             "engine": {"family_engine": family_engine.FAMILY_ENGINE_VERSION,
                        "execution": family_engine.EXECUTION_VERSION}}
    catalog = catalog_reference(case_id)
    if catalog is not None:
        found["catalog"] = catalog
        found["engine"]["glucose_rescue"] = glucose_rescue.VERSION
    return found


def catalog_reference(case_id):
    """Which catalogue configuration a case is, if it is one."""
    import hypoglycemia_catalog
    return hypoglycemia_catalog.reference(case_id)


def freeze(case_id, *, spec=None, code_version=None, frozen_at=None):
    """The basis an encounter is launched with. Raises for a case no declaration knows."""
    case_id = str(case_id or "")
    basis = {"schema": SCHEMA, "case_id": case_id,
             "frozen_at": frozen_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "code_version": code_version, "versions": versions(case_id)}
    if not case_id:
        return {**basis, "source": "none", "declaration": None, "fingerprint": None}
    if _is_generated(case_id, spec):
        return {**basis, "source": "generated", "declaration": None, "fingerprint": None}
    declaration, source = _current(case_id)
    if declaration is None:
        raise EvaluationBasisError(f"No evaluation declaration exists for the case {case_id!r}.")
    plain = _plain(declaration)
    return {**basis, "source": source, "declaration": plain, "fingerprint": fingerprint(plain)}


def _session(record):
    payload = record.get("payload")
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise EvaluationBasisError("The record's payload is not readable.")
    session = payload.get("session")
    if session is None:
        return {}
    if not isinstance(session, dict):
        raise EvaluationBasisError("The record's session is not readable.")
    return session


def _spec(record):
    session = _session(record)
    for key in ("encounter_closed_state", "state"):
        state = session.get(key)
        if isinstance(state, dict) and isinstance(state.get("encounter_spec"), dict):
            return state["encounter_spec"]
    return None


def _named_case(record):
    from faculty_analysis import case_id_of
    return case_id_of(record)


_LIMITS = {
    "frozen": None,
    "legacy": {
        "en": ("This encounter was saved before evaluation declarations were frozen with each encounter. It is "
               "judged with the declarations as they stood until 2026-09-25 (coverage {coverage}); the version "
               "in force when it was launched cannot be verified."),
        "es": ("Este encuentro se guardó antes de que las declaraciones de evaluación se congelaran con cada "
               "encuentro. Se evalúa con las declaraciones vigentes hasta el 2026-09-25 (cobertura {coverage}); "
               "no se puede verificar la versión vigente cuando se inició."),
    },
    "unfrozen_current": {
        "en": ("This encounter carries no frozen copy of its declarations and the snapshot of 2026-09-25 does "
               "not know its case: the current declarations (coverage {coverage}) are used, and they may not be "
               "the ones in force when it was launched."),
        "es": ("Este encuentro no trae una copia congelada de sus declaraciones y la instantánea del 2026-09-25 "
               "no conoce su caso: se usan las declaraciones actuales (cobertura {coverage}), que pueden no ser "
               "las vigentes cuando se inició."),
    },
    "generated": {
        "en": ("This encounter used a generated case. No opportunities or critical events were declared for it "
               "before the encounter, so none are shown and none are scored; the five domains can still be read "
               "from the record, and no complete or comparable total is implied."),
        "es": ("Este encuentro usó un caso generado. No se declararon oportunidades ni eventos críticos antes "
               "del encuentro, así que no se muestran ni se puntúan; los cinco dominios pueden leerse desde el "
               "registro, sin que eso suponga un total completo o comparable."),
    },
    "no_authored_case": {
        "en": ("This encounter does not name an authored case, so its declared opportunities and critical events "
               "are unavailable. The five domains can still be read from the record."),
        "es": ("Este encuentro no nombra un caso autorado, así que no hay oportunidades ni eventos críticos "
               "declarados. Los cinco dominios pueden leerse desde el registro."),
    },
    "unknown_case": {
        "en": "The record names the case {case_id!r}, which no evaluation declaration knows: an invalid identifier.",
        "es": "El registro nombra el caso {case_id!r}, que ninguna declaración de evaluación conoce: un identificador inválido.",
    },
    "corrupt": {
        "en": "The record's evaluation basis cannot be read: {error}",
        "es": "La base de evaluación del registro no se puede leer: {error}",
    },
    "reevaluation": {
        "en": ("Explicit re-evaluation with the current declarations (coverage {coverage}), requested by "
               "{requested_by}: {reason}. The basis the encounter was launched with is kept."),
        "es": ("Reevaluación explícita con las declaraciones actuales (cobertura {coverage}), pedida por "
               "{requested_by}: {reason}. Se conserva la base con que se inició el encuentro."),
    },
}


def _view(status, case_id, declaration=None, *, versions_=None, fingerprint_=None, error=None,
          source=None, extra=None):
    coverage = ((versions_ or {}).get("coverage")) or "?"
    extra = dict(extra or {})
    limitation = None
    if _LIMITS.get(status):
        fields = {"coverage": coverage, "case_id": case_id, "error": error or "",
                  "requested_by": extra.get("requested_by", ""), "reason": extra.get("reason", "")}
        limitation = {language: text.format(**fields) for language, text in _LIMITS[status].items()}
    declaration = _tupled(declaration) if declaration is not None else None
    return {"status": status, "case_id": case_id, "source": source,
            "declaration": declaration,
            "events": tuple((declaration or {}).get("critical_events", ())),
            "versions": deepcopy(versions_ or {}), "fingerprint": fingerprint_,
            "limitation": limitation, "error": error, **extra}


def resolve(record, case_id=None):
    """The one basis this record is judged against, with its status and limitation.

    ``case_id`` is for callers that already know which case they mean. When
    the record carries its own frozen copy, the two must agree.
    """
    if not isinstance(record, dict):
        return _view("corrupt", str(case_id or ""), error="the record is not an object")
    try:
        _session(record)
        encounter = record.get("encounter")
        if encounter is not None and not isinstance(encounter, dict):
            raise EvaluationBasisError("the record's encounter is not readable")
        frozen = (encounter or {}).get("evaluation_basis")
        if frozen is not None:
            return _from_frozen(frozen, case_id)
        named = str(case_id or _named_case(record) or "")
    except EvaluationBasisError as error:
        return _view("corrupt", str(case_id or ""), error=str(error))
    if not named:
        return _view("no_authored_case", "")
    if _is_generated(named, _spec(record)):
        return _view("generated", named, source="generated")
    snapshot = legacy()
    if named in snapshot["declarations"]:
        return _view("legacy", named, snapshot["declarations"][named], source="legacy_snapshot",
                     versions_={"coverage": snapshot["coverage_version"], "rubric": snapshot["rubric_version"],
                                "snapshot": LEGACY_PATH.name},
                     fingerprint_=fingerprint(snapshot["declarations"][named]))
    declaration, source = _current(named)
    if declaration is not None:
        plain = _plain(declaration)
        return _view("unfrozen_current", named, plain, source=source, versions_=versions(named),
                     fingerprint_=fingerprint(plain))
    return _view("unknown_case", named)


def _from_frozen(frozen, case_id):
    if not isinstance(frozen, dict) or frozen.get("schema") != SCHEMA:
        return _view("corrupt", str(case_id or ""), error="the frozen basis has an unknown format")
    named = str(frozen.get("case_id") or "")
    if case_id and str(case_id) != named:
        return _view("corrupt", str(case_id), error=f"the frozen basis is for {named!r}, not {case_id!r}")
    source = frozen.get("source")
    if source == "none":
        return _view("no_authored_case", "", versions_=frozen.get("versions"))
    if source == "generated":
        return _view("generated", named, source="generated", versions_=frozen.get("versions"))
    declaration = frozen.get("declaration")
    if not isinstance(declaration, dict) or fingerprint(declaration) != frozen.get("fingerprint"):
        return _view("corrupt", named, error="the frozen declarations do not match their fingerprint")
    return _view("frozen", named, declaration, source=source, versions_=frozen.get("versions"),
                 fingerprint_=frozen["fingerprint"],
                 extra={"frozen_at": frozen.get("frozen_at"), "code_version": frozen.get("code_version")})


def reevaluation(record, *, reason, requested_by):
    """An explicit judgement with the current declarations, beside the original one.

    Pure: it returns the new basis and the one it departs from, and stores
    nothing. Whoever persists an analysis made with it keeps both, and a
    confirmed faculty decision is never overwritten by it.
    """
    reason = str(reason or "").strip()
    requested_by = str(requested_by or "").strip()
    if not reason or not requested_by:
        raise EvaluationBasisError("A re-evaluation with new criteria needs a stated reason and who requested it.")
    previous = resolve(record)
    if previous["status"] in ("corrupt", "unknown_case"):
        raise EvaluationBasisError("This record cannot be re-evaluated: " + (previous["limitation"] or {}).get(
            "en", previous["status"]))
    if previous["status"] in ("generated", "no_authored_case"):
        raise EvaluationBasisError("There are no declarations to re-evaluate this encounter against.")
    declaration, source = _current(previous["case_id"])
    if declaration is None:
        raise EvaluationBasisError(f"The case {previous['case_id']!r} has no current declaration.")
    plain = _plain(declaration)
    return _view("reevaluation", previous["case_id"], plain, source=source,
                 versions_=versions(previous["case_id"]), fingerprint_=fingerprint(plain),
                 extra={"reason": reason, "requested_by": requested_by,
                        "requested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "previous": {"status": previous["status"], "fingerprint": previous["fingerprint"],
                                     "versions": previous["versions"]}})
