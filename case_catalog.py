"""Configurations of a clinical family: one source for execution, checks and evaluation.

A configuration is data: the value of each of the family's axes, the scenario
conditions the engine reads, the narrative it is told with, and where it came
from. The family catalogue (``hypoglycemia_catalog`` is the first) derives
from it the engine flags a case carries, the cues that make a condition
discoverable, the evaluation declarations and the expectations of the
trajectory battery, so that a rule is written once and not restated by hand in
generation, execution and evaluation.

**Whatever its origin, a configuration is checked, never trusted.** A bank case
expressed through the catalogue, a combination the catalogue composes, and --
in a later stage that is *not* built here -- a clinical configuration proposed
by a model outside any resident's session, all go through the same checks
before anything can run them. The data model leaves room for that last one on
purpose: a proposal may bring new combinations of the conditions the engine
already executes, not only a new name or a new story, and it is accepted only
after the checks and a faculty review. Until that circuit exists an
``ai_proposal`` is refused.

**Three states, never merged:**

* *compatible* -- the configuration satisfies the catalogue's rules and the
  case built from it passes the checks the bank itself must pass;
* *tested* -- the trajectory battery ran on the real engine and every
  technical check passed; the state names exactly which scripts and checks,
  and what nobody observed;
* *clinically reviewed* -- a faculty member, identified, reviewed this
  configuration **at a stated version**. No test result produces it and a
  passing battery does not keep it: a clinically relevant change in the rules,
  the parameters, the cues, the narrative or the evaluation marks it as
  needing a new review. A change declared cosmetic in the corrections registry
  does not.
"""
from copy import deepcopy
import ast
import hashlib
import inspect
import json

SCHEMA = "mrs.case_catalog.v1"

RELATION_KINDS = {
    "necessary": {"es": "Necesaria para la coherencia del modelo",
                  "en": "Necessary for the model's coherence"},
    "assumption": {"es": "Supuesto particular de una configuración",
                   "en": "Assumption of one configuration"},
    "simplification": {"es": "Simplificación pendiente de revisión clínica",
                       "en": "Simplification pending clinical review"},
}
ORIGINS = {
    "bank": "A case of the bank, expressed through the catalogue.",
    "composition": "A combination of tested mechanisms composed by the catalogue.",
    # Reserved. The circuit that would let a model propose a configuration
    # outside a resident's session is a later stage; until it exists nothing
    # with this origin passes the checks.
    "ai_proposal": "Proposed by a model outside any resident's session (not accepted yet).",
}
REVIEW_DECISIONS = ("approved", "changes_requested", "rejected")
# What a clinical review is a review *of*. A change in any of them is
# clinically relevant unless the corrections registry declares it cosmetic.
FINGERPRINT_COMPONENTS = ("conditions", "rules", "parameters", "cues", "narrative", "assessment")


class CatalogError(ValueError):
    """A configuration that cannot be built or does not belong to the catalogue."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default)


def _default(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Not serialisable: {type(value).__name__}")


def digest(value, length=16):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()[:length]


def plain(value):
    """JSON-shaped (tuples become lists), so hashes do not depend on container types."""
    return json.loads(canonical(value))


def logic_of(function):
    """A function's logic without its comments or layout: what a review is about."""
    tree = ast.parse(inspect.cleandoc("\n" + inspect.getsource(function)))
    node = tree.body[0]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        node.body = [statement for statement in node.body
                     if not (isinstance(statement, ast.Expr)
                             and isinstance(getattr(statement, "value", None), ast.Constant)
                             and isinstance(statement.value.value, str))]
    return ast.dump(node, include_attributes=False)


def constants_of(module):
    """The upper-case values a module declares: its parameters, not its prose."""
    values = {}
    for name in sorted(vars(module)):
        if not name.isupper() or name.startswith("_"):
            continue
        value = getattr(module, name)
        if isinstance(value, (int, float, str, bool, tuple, list, dict, frozenset, set)) or value is None:
            values[name] = plain(value)
    return values


def check(catalog, configuration):
    """Every way a configuration fails its catalogue's rules. Empty means compatible.

    Assumptions are declared by the configuration that makes them and bind no
    other configuration, so they are listed, not enforced. Necessary relations
    and the simplifications the model still makes are enforced.
    """
    findings = []

    def finding(code, message, relation=None, kind=None):
        findings.append({"code": code, "relation": relation, "kind": kind, "message": message})

    if configuration.get("family") != catalog.FAMILY:
        finding("family", f"The configuration belongs to {configuration.get('family')!r}, not {catalog.FAMILY!r}.")
    origin = configuration.get("origin")
    if origin not in ORIGINS:
        finding("origin", f"Unknown origin {origin!r}.")
    elif origin == "ai_proposal":
        finding("origin", "Configurations proposed by a model are not accepted in this stage: the authoring "
                          "circuit that would check and review them does not exist yet.")
    axes = configuration.get("axes") or {}
    for axis, values in catalog.AXES.items():
        if axis not in axes:
            finding("axis", f"The configuration does not state its {axis}.")
        elif axes[axis] not in values["values"]:
            finding("axis", f"{axes[axis]!r} is not a value of the axis {axis}.")
    for axis in axes:
        if axis not in catalog.AXES:
            finding("axis", f"{axis!r} is not an axis of this catalogue.")
    conditions = configuration.get("conditions") or {}
    for name, value in conditions.items():
        spec = catalog.CONDITIONS.get(name)
        if spec is None:
            finding("condition", f"{name!r} is not a condition this catalogue knows.")
            continue
        if spec.get("status") != "implemented":
            finding("capability", f"{name!r} is a pending capability: {spec.get('status')}.")
        allowed = spec.get("values")
        if allowed is not None and value not in allowed:
            finding("condition", f"{value!r} is not a value of {name}.")
    for name in catalog.CONDITIONS:
        if name not in conditions:
            finding("condition", f"The configuration does not state {name}.")
    if findings:
        return findings
    for relation in catalog.RELATIONS:
        if relation["kind"] == "assumption":
            continue
        problem = relation["check"](configuration)
        if problem:
            finding("relation", problem, relation["id"], relation["kind"])
    return findings


def signature(catalog, configuration):
    """The clinical situation without its surface: what makes two encounters the same challenge.

    The axes and the decision-relevant conditions. A name, an age inside its
    band, the words of the story or which arm the cannula is in change nothing
    here, so two cases that differ only in those have the same signature --
    which is what a later stage needs to tell a repeated situation from a new
    one (not implemented yet).
    """
    relevant = {name: configuration["conditions"][name] for name, spec in catalog.CONDITIONS.items()
                if spec.get("decision_relevant")}
    body = {"family": catalog.FAMILY, "axes": dict(sorted(configuration["axes"].items())),
            "conditions": relevant}
    return {**body, "id": digest(body)}


def fingerprint(catalog, configuration):
    """One hash per clinically relevant component, and the whole."""
    components = catalog.fingerprint_components(configuration)
    missing = set(FINGERPRINT_COMPONENTS) - set(components)
    if missing:
        raise CatalogError("A catalogue must fingerprint " + ", ".join(sorted(missing)) + ".")
    hashes = {name: digest(components[name]) for name in FINGERPRINT_COMPONENTS}
    return {"components": hashes, "whole": digest(hashes), "catalog_version": catalog.VERSION}


def review_status(configuration_id, current, reviews, waivers=()):
    """Where the clinical review of one configuration stands against its current fingerprint.

    ``reviews`` are recorded faculty actions, newest last. ``waivers`` are the
    corrections registry's declarations that a change was cosmetic: each names
    the configuration, the component, and the hashes before and after, so a
    waiver covers exactly one change and not a later one.
    """
    own = [review for review in reviews or () if review.get("configuration_id") == configuration_id]
    if not own:
        return {"state": "not_reviewed", "review": None, "changed": [], "waived": []}
    latest = own[-1]
    reviewed = (latest.get("fingerprint") or {}).get("components") or {}
    changed, waived = [], []
    for component in FINGERPRINT_COMPONENTS:
        before, after = reviewed.get(component), current["components"][component]
        if before == after:
            continue
        if any(w.get("configuration_id") == configuration_id and w.get("component") == component
               and w.get("from") == before and w.get("to") == after for w in waivers):
            waived.append(component)
        else:
            changed.append(component)
    if changed:
        state = "review_outdated"
    elif latest.get("decision") == "approved":
        state = "reviewed"
    else:
        state = "reviewed_" + str(latest.get("decision"))
    return {"state": state, "review": deepcopy(latest), "changed": changed, "waived": waived}
