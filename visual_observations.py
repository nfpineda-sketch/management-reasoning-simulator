"""Case-authored visible findings, independent of diagnosis and learner choices.

The physiology engine owns peripheral_perfusion, mentation and respiratory work.
This module only translates an explicitly authored visual phenotype into drawable
findings. A phenotype is not a general diagnostic rule: cool skin is a tactile
finding, and neither low BP nor a warm hand defines the patient's visible color.
The skin observations remain separate, as in the ESICM shock consensus
(https://doi.org/10.1007/s00134-014-3525-z). The pilot visual mapping itself still
requires faculty review; it is not a clinically validated severity scale.
"""
from copy import deepcopy
import math


VISUAL_CONTRACT_VERSION = 2
PERFUSION_CATEGORIES = (
    "preserved", "mildly impaired", "impaired", "severely impaired", "critical",
)
VISUAL_CHOICES = {
    "mental_status": (
        "alert", "drowsy", "obtunded", "unresponsive", "sedated", "not recorded",
    ),
    "work_of_breathing": (
        "normal", "reduced", "mildly increased", "increased", "moderately increased",
        "markedly increased", "severe", "ventilator-supported", "not recorded",
    ),
    "expression": (
        "neutral", "uncomfortable", "markedly uncomfortable", "passive",
        "sedated", "not recorded",
    ),
    "skin_color": ("natural", "mild pallor", "pallor", "not recorded"),
    "diaphoresis": ("absent", "mild", "marked", "not recorded"),
}
_PILOT_CHALLENGES = ("R1-03", "R1-04", "R2-01")
_PILOT_PROFILES = ("volume_limited", "rhythm_contributor", "mixed_low_flow")


def hypoperfusion_visual_profile():
    """An explicit visual phenotype for this pilot's uncomfortable patient.

    It adds subtle pallor as an authored case fact, not as an inference from
    tachycardia, pressure, temperature, suspected sepsis or treatment. Changes
    follow the engine's existing peripheral-flow categories. Diaphoresis is not
    authored in this pilot and must not be invented by the image renderer.
    """
    return {
        "id": "peripheral_hypoperfusion_v1",
        "baseline": {"expression": "uncomfortable", "skin_color": "mild pallor"},
        "perfusion_appearance": {
            "preserved": {"expression": "neutral", "skin_color": "natural"},
            "mildly impaired": {"expression": "uncomfortable", "skin_color": "mild pallor"},
            "impaired": {"expression": "uncomfortable", "skin_color": "mild pallor"},
            "severely impaired": {"expression": "markedly uncomfortable", "skin_color": "pallor"},
            "critical": {"expression": "markedly uncomfortable", "skin_color": "pallor"},
        },
    }


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _known(value, field):
    normalized = value.strip().lower() if isinstance(value, str) else ""
    return normalized if normalized in VISUAL_CHOICES[field] else "not recorded"


def _legacy_pilot_spec(spec):
    return (
        "visual_profile" not in spec
        and spec.get("schema_version") == "mrs.ps001.encounter.v1"
        and spec.get("case_family") == "PS001"
        and spec.get("challenge_id") in _PILOT_CHALLENGES
        and spec.get("profile_id") in _PILOT_PROFILES
    )


def visual_profile(state):
    """Return an isolated profile, including a narrowly scoped legacy migration.

    Only known pre-visual-profile generated pilot specifications are migrated.
    An explicit empty profile is respected. No free text or case diagnosis is
    parsed, and this function never changes the saved specification/hash.
    """
    spec = _mapping(state.get("encounter_spec"))
    if "visual_profile" in spec:
        return deepcopy(_mapping(spec["visual_profile"]))
    if _legacy_pilot_spec(spec):
        return hypoperfusion_visual_profile()
    return {}


def _legacy_perfusion_category(state, observable):
    """Recover a missing surface from an old pilot's already computed flow.

    This migration never recalculates physiology. It uses exactly the current
    engine's existing flow bands, only for recognized generated pilot snapshots
    that predate visual profiles. Fresh legacy entries use their authored entry
    category because inherited base-state flow may not describe the new variant.
    """
    if not _legacy_pilot_spec(_mapping(state.get("encounter_spec"))):
        return None
    if observable.get("pulse_present") is False:
        return "critical"
    if state.get("sim_time") == 0:
        return "impaired"
    flow = _mapping(state.get("hidden")).get("peripheral_flow")
    if isinstance(flow, bool) or not isinstance(flow, (int, float)):
        return None
    if not math.isfinite(flow) or not 0 <= flow <= 1:
        return None
    return (
        "preserved" if flow >= .70 else
        "mildly impaired" if flow >= .52 else
        "impaired" if flow >= .23 else
        "severely impaired" if flow >= .08 else "critical"
    )


def visual_observations(state):
    """Pure, bounded visible contract for prompts, examination and consistency QA.

    Current ``observable.visual`` findings take precedence over profile defaults
    and category-specific findings. Unknown values never become model instructions.
    Reduced alertness changes engagement, not skin perfusion. Sedation does not
    imply recovery. Alertness never implies comfort or permission to smile.
    """
    state = _mapping(state)
    o = _mapping(state.get("observable"))
    profile = visual_profile(state)
    authored = dict(_mapping(profile.get("baseline")))
    category = o.get("peripheral_perfusion")
    if "peripheral_perfusion" not in o:
        category = _legacy_perfusion_category(state, o)
    if category in PERFUSION_CATEGORIES:
        authored.update(_mapping(_mapping(profile.get("perfusion_appearance")).get(category)))
    current_visual = _mapping(o.get("visual"))
    authored.update(current_visual)
    if isinstance(current_visual.get("mottling"), bool):
        mottling = current_visual["mottling"]
    else:
        mottling = authored.get("mottling") is True or str(
            o.get("extremities", "")
        ).strip().lower() in {"mottled", "mottled/cold"}

    result = {
        "mental_status": _known(o.get("mental_status"), "mental_status"),
        "work_of_breathing": _known(o.get("work_of_breathing"), "work_of_breathing"),
        "expression": _known(authored.get("expression", "neutral"), "expression"),
        "skin_color": _known(authored.get("skin_color"), "skin_color"),
        "diaphoresis": _known(authored.get("diaphoresis"), "diaphoresis"),
        "mottling": mottling,
    }
    # A passive or pharmacologically relaxed face is not evidence that the
    # patient is better perfused. Keep color/mottling/diaphoresis independent.
    if result["mental_status"] == "sedated":
        result["expression"] = "sedated"
    elif result["mental_status"] in {"obtunded", "unresponsive"}:
        result["expression"] = "passive"
    # Persistent respiratory effort can coexist with restored peripheral flow.
    # Do not portray an effortlessly comfortable face merely because perfusion
    # reached the profile's neutral baseline.
    elif result["expression"] == "neutral" and result["work_of_breathing"] in {
        "increased", "moderately increased", "markedly increased", "severe",
    }:
        result["expression"] = "uncomfortable"
    return result
