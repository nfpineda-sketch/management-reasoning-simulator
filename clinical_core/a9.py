"""P2F-10: the Appendix A9 comparison framework, without numbers.

For every variable compared between the core and the family engine (or, for internal state
with no engine counterpart, between the core and its approved qualitative behaviour), the
recommended comparison TYPE and why. Every numerical tolerance is TBD: none is chosen here.
Hidden internal state is not held to the tolerance logic of a displayed observable.
"""
from __future__ import annotations

from dataclasses import dataclass

EXACT_STATE = "exact semantic/state match"
EXACT_EVENT_TIMING = "exact event timing"
BOUNDED_ABSOLUTE = "bounded absolute numerical difference"
BOUNDED_RELATIVE = "bounded relative numerical difference"
TREND = "direction/trend equivalence"
CATEGORY = "clinically equivalent category"
STRUCTURAL = "approved structural divergence"
COMPARISON_TYPES = (EXACT_STATE, EXACT_EVENT_TIMING, BOUNDED_ABSOLUTE, BOUNDED_RELATIVE, TREND, CATEGORY, STRUCTURAL)


@dataclass(frozen=True)
class Comparison:
    variable: str
    resident_visible: bool
    comparison: str
    also: tuple[str, ...]
    rationale: str
    tolerance: None = None      # TBD: no tolerance is approved

    def __post_init__(self):
        if self.comparison not in COMPARISON_TYPES or any(item not in COMPARISON_TYPES for item in self.also):
            raise ValueError(f"{self.variable}: unknown comparison type")
        if self.tolerance is not None:
            raise ValueError(f"{self.variable}: tolerances are TBD until faculty approve them")


A9 = {row.variable: row for row in (
    Comparison("sbp", True, BOUNDED_ABSOLUTE, (CATEGORY,),
               "read in mmHg as shown; the 90/80/65 thresholds gate consciousness and logistics, so a crossing is "
               "compared as a category too"),
    Comparison("dbp", True, BOUNDED_ABSOLUTE, (), "mmHg as shown; no gating threshold of its own"),
    Comparison("map", True, BOUNDED_ABSOLUTE, (CATEGORY,), "mmHg; 65 mmHg is a clinical target, so its side matters"),
    Comparison("hr", True, BOUNDED_ABSOLUTE, (TREND,),
               "bpm as shown; the sympathetic drive's memory (KD-S2) makes the course matter as much as the minute"),
    Comparison("respiratory_rate", True, BOUNDED_ABSOLUTE, (CATEGORY,),
               "breaths/min; bradypnoea (< 10) and marked tachypnoea are categories a resident acts on"),
    Comparison("spo2", True, BOUNDED_ABSOLUTE, (CATEGORY,),
               "%; the 94/87/80 levels gate the hypoxaemic drive and consciousness"),
    Comparison("crt_s", True, BOUNDED_ABSOLUTE, (CATEGORY,), "seconds; delayed refill (> 3 s) is the category read"),
    Comparison("consciousness_level", True, CATEGORY, (),
               "the 0-3 ladder: the same level, minute by minute; the engine's DC1 anchoring belongs to Observation v2"),
    Comparison("lactate", True, BOUNDED_RELATIVE, (TREND,),
               "a relative difference at high values, and the clearance direction after resuscitation (KD-S1)"),
    Comparison("hb", True, STRUCTURAL, (TREND,),
               "since P2I-2T the core derives Hb from the shared blood state (red-cell content over circulating "
               "volume), by faculty decision, instead of the engine's fixed drifts: the difference from the engine is "
               "structural; the direction is compared (refill and crystalloid dilute, red cells raise it, acute "
               "whole-blood loss leaves it), its size is TBD"),
    Comparison("event_timing", True, EXACT_EVENT_TIMING, (),
               "an endoscopy, a completed transfusion or an arrest happens in the same minute, or the difference is "
               "a decision"),
    Comparison("pulse_arrest_state", True, EXACT_STATE, (),
               "pulse present or absent, and the rhythm category, agree minute by minute"),
    Comparison("V", False, STRUCTURAL, (),
               "kappa x the shared blood state's circulating-volume deviation (P2I-2T): it differs from the engine's "
               "volume by plasma refill, and past the engine's circulation clamp the core keeps no clamp (KD-S4); "
               "with refill off it equals the engine's volume within the clamp"),
    Comparison("D", False, TREND, (),
               "no engine counterpart: judged against the approved qualitative behaviour (monotonic in the deficit, "
               "gradual repayment, never negative)"),
    Comparison("L", False, TREND, (), "no GI engine counterpart: probes only (P2D-6, P2E-5)"),
    Comparison("effective_output", False, TREND, (), "follows the engine's circulation in direction, not in size"),
    Comparison("oxygen_demand", False, EXACT_STATE, (),
               "the product of the declared baseline and modifiers: exact, because it is bookkeeping"),
    Comparison("sympathetic_drive", False, TREND, (),
               "rises with the declared stimuli, decays with its memory, never negative; no engine counterpart"),
    Comparison("collapse_burden", False, TREND, (EXACT_EVENT_TIMING,),
               "accrues with severity x duration; the terminal transition is compared as an event"),
)}

RESIDENT_VISIBLE = tuple(name for name, row in A9.items() if row.resident_visible)
INTERNAL = tuple(name for name, row in A9.items() if not row.resident_visible)


def table() -> list[dict]:
    return [{"variable": row.variable, "resident_visible": row.resident_visible, "comparison": row.comparison,
             "also": list(row.also), "rationale": row.rationale, "tolerance": "TBD"} for row in A9.values()]
