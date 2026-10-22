"""Run the family engine and the shadow core side by side on golden scenarios.

    python -m clinical_core.shadow --out <directory outside the repository>
    python -m clinical_core.shadow --write-golden

The family engine runs first and alone; the core then runs from the same relevant
inputs read off the engine's run (``legacy_adapter``). The comparison writes nothing
anywhere except the files asked for on the command line. This module is not imported
by the application.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from . import CORE_VERSION
from .comparison import _display, compare, mismatching, summarize
from .derived import PARAMETERS, _level, case_parameter_provenance
from .integration import CHANNEL_BOUNDS, Trajectory, run
from .legacy_adapter import (FAMILY_CASE_PARAMETER_RULES, LEGACY_LITERALS, LegacyRun, anchors_from_legacy,
                             contributors_from_legacy, run_legacy)
from .state import digest

GOLDEN = Path(__file__).with_name("golden") / "gi_bleed_shadow.json"
VARIANTS = ("gi_bleed_57m", "gi_bleed_72f")
SCENARIOS = {
    "untreated_60": {"minutes": 60, "orders": {}},
    "saline_2l_over_20": {"minutes": 60, "orders": {0: "Give 2000 mL normal saline IV over 20 minutes."}},
    "prbc_2u_over_60": {"minutes": 90, "orders": {0: "Transfuse 2 units packed red blood cells over 60 minutes."}},
    "oxygen_non_rebreather": {"minutes": 20, "orders": {0: "Give oxygen 15 L/min via non-rebreather mask."}},
    "definitive_management": {"minutes": 120, "orders": {0: (
        "Transfuse 2 units packed red blood cells over 60 minutes. Give pantoprazole 80 mg IV. "
        "Consult gastroenterology for urgent endoscopy.")}},
    "saline_then_blood": {"minutes": 120, "orders": {
        0: "Give 1000 mL normal saline IV.",
        30: "Transfuse 2 units packed red blood cells. Give pantoprazole 80 mg IV."}},
    # Delivery as the engine runs it: untimed orders share one line, a second timed bag in one
    # order queues behind the first, and a stop closes every running crystalloid.
    "untimed_shared_line": {"minutes": 90, "orders": {
        0: "Give 1000 mL normal saline IV.", 5: "Give 1000 mL normal saline IV.",
        10: "Transfuse 1 unit packed red blood cells.", 20: "Transfuse 1 unit packed red blood cells."}},
    "queued_timed_bags": {"minutes": 45, "orders": {0: (
        "Give 1000 mL normal saline IV over 15 minutes. Give 1000 mL normal saline IV over 15 minutes.")}},
    "stop_fluids": {"minutes": 60, "orders": {
        0: "Give 2000 mL normal saline IV over 60 minutes. Give 1000 mL normal saline IV.",
        20: "Stop IV fluids."}},
    # Beyond what the family engine's circulation clamp and transfusion rule allow: the
    # differences this produces are reported, not tuned away.
    "aggressive_volume": {"minutes": 90, "orders": {0: (
        "Transfuse 4 units packed red blood cells over 60 minutes. "
        "Give 2000 mL normal saline IV over 30 minutes.")}},
}


#: Every difference the comparison finds, with its reason. The golden test fails on any
#: difference not listed here and on any entry here that no longer occurs. Nothing in
#: either engine was changed to make a difference disappear.
DIFFERENCES = {
    "KD-S1": ("lactate and respiratory rate (approved revision, P2C-1): the core accumulates an oxygen-delivery "
              "debt D (tau provisional), produces lactate from D and clears it with its own memory, and reads RR as "
              "ventilation (W) plus a saturating metabolic drive anchored to arrival, so clearing lactate never "
              "causes bradypnoea; the family engine sets both instantly from circulation, with an RR floor of 14 "
              "in this family", "TBD: tau_D, D->lactate gain, lactate clearance, metabolic drive gain, RR bounds"),
    "KD-S2": ("heart rate (adopted direction, P2C-2): the core reads sinus rate as the intrinsic rate plus the "
              "chronotropic response to one common sympathetic drive, blunted by beta-blockade; the drive answers "
              "to the pressure deficit, the oxygen-delivery debt D, hypoxaemia and hypoglycaemia, rises at once and "
              "decays with its own memory, and no disease module writes it, so hemostasis lowers the rate only "
              "through recovered pressure and repaid debt; the family engine sets HR instantly from circulation and "
              "subtracts 20 bpm x hemostasis_relief from the displayed HR (a module writing an observable, which "
              "§8.1 rules out)", "TBD: pressure/output deficit and D gains, hypoxaemia and hypoglycaemia gains and "
              "thresholds, sympathetic decay time"),
    "KD-S3": ("consciousness at the 80 mmHg threshold: the family engine compares the rounded SBP (80), the core the "
              "raw value (79.9)", "Observation v2 (Phase 1): thresholds on raw state or on the displayed value"),
    "KD-S4": ("volume, pressure and refill (approved revision, P2C-3): the core reads output from one smooth, "
              "saturating preload curve (V -> effective preload -> stroke volume -> output -> pressure), concave "
              "everywhere, with arrival placed on it by a case position (provisional default 0.5, where its slope "
              "equals the family engine's linear gain) and output lowered by tone above arrival; the family engine "
              "is linear in volume and clamps circulation to [.25, 1.9] (+625 mL-eq). So pressure, refill and the "
              "rate differ wherever V leaves arrival: a little below it (the curve is steeper there), more above it "
              "(the curve saturates), and past the clamp the core's V keeps rising while its output barely moves",
              "TBD: curve form and scale, arrival position, P sensitivity, afterload sensitivity, congestion knee "
              "and gain"),
}
#: Candidate causes of each expected difference (P2D-9): the decided mechanisms on the variable's
#: causal path in that run. They are candidates, not a measure of how much each contributes;
#: where more than one mechanism lies on the path, all are listed:
#: - lactate and RR: KD-S1 kinetics, and KD-S4 through output and so through D;
#: - HR: the KD-S2 drive, and KD-S4 through the pressure deficit and D;
#: - SBP, DBP, MAP and CRT: KD-S4 (output and pressure from the preload curve);
#: - V: KD-S4 (no clamp on volume);
#: - consciousness: KD-S3 and/or KD-S4, minute by minute (``consciousness_attribution``).
#: Every run bleeds, so V leaves arrival and KD-S4 lies on every path through output.
_STRUCTURAL = {"lactate_mmol_l": ("KD-S1", "KD-S4"), "respiratory_rate": ("KD-S1", "KD-S4"),
               "hr": ("KD-S2", "KD-S4"), "sbp": ("KD-S4",), "dbp": ("KD-S4",), "map": ("KD-S4",),
               "crt_s": ("KD-S4",)}
EXPECTED_DIFFERENCES = {
    f"{variant}/{scenario}": dict(_STRUCTURAL) for variant in VARIANTS for scenario in SCENARIOS}
# The oxygen runs last 20 minutes and V moves only with the bleeding, so the curve changes the
# pressures by one display step at most, and not every one of them.
del EXPECTED_DIFFERENCES["gi_bleed_57m/oxygen_non_rebreather"]["crt_s"]
for _name in ("map", "crt_s"):
    del EXPECTED_DIFFERENCES["gi_bleed_72f/oxygen_non_rebreather"][_name]
for _variant in VARIANTS:
    # Past the engine's circulation clamp the core's V keeps rising (KD-S4).
    EXPECTED_DIFFERENCES[f"{_variant}/aggressive_volume"]["V_ml_eq"] = ("KD-S4",)
# The 80 mmHg threshold, read on the core's raw SBP (KD-S3, unchanged) and on a pressure that the
# preload curve lowers by under 1 mmHg (KD-S4): see consciousness_attribution, minute by minute.
EXPECTED_DIFFERENCES["gi_bleed_57m/untreated_60"]["consciousness_level"] = ("KD-S3", "KD-S4")

#: The decision behind each known difference. "approved" means its physiological direction is
#: approved (P2C); its magnitude is not, until the Level-2 bands and the Appendix A9 tolerances
#: are approved. Hence APPROVED_DIRECTION_MAGNITUDE_TBD, never an approved size (P2D-9).
DECISIONS = {
    "KD-S1": ("approved", "REVISE CORE: D with memory produces lactate; RR from W plus a saturating metabolic drive"),
    "KD-S2": ("approved", "ADOPT CORE DIRECTION: HR from R plus one common sympathetic drive plus modulators"),
    "KD-S3": ("approved", "RESOLVED, not changed in P2C: physiology reads the unrounded state; display and gating "
                          "read Observation v2"),
    "KD-S4": ("approved", "REVISE CORE: one smooth, saturating preload curve; no clamp"),
}
MATCH, APPROVED_DIRECTION, UNRESOLVED = "MATCH", "APPROVED_DIRECTION_MAGNITUDE_TBD", "UNRESOLVED"


def consciousness_attribution(result) -> list[dict]:
    """Minute by minute, which decision can produce each consciousness difference (P2D-9).

    Only a difference the pressure threshold explains is attributed: both engines read the same
    oxygen level, and with the engine's own SpO2 the core's raw pressure still gives a level
    other than the engine's. Then two
    counterfactual readings of the same minute, against the engine's level:
    - KD-S3 alone: the engine's own pressure (its circulation change since arrival, through
      the adopted relation) read raw, as the core reads it;
    - KD-S4 alone: the core's pressure read on its displayed (rounded) value, as the engine
      reads it.
    Each that still differs from the engine's level is sufficient alone; when neither does,
    both are needed together. A minute without a pulse on either side, or one the pressure
    does not explain, gets no candidate cause: it stays unresolved.
    """
    anchors, profile = result.core.anchors, result.core.profile
    derived = result.core.derived()

    def level(sbp, spo2):
        return max(anchors.consciousness_level, _level(sbp, profile.pressure_levels),
                   _level(spo2, profile.oxygen_levels))

    rows = []
    for row in result.rows["consciousness_level"]:
        if row["status"] != "mismatch":
            continue
        minute, values = row["minute"], derived[row["minute"]]
        snap = result.legacy.snapshots[minute]
        entry = {"minute": minute, "legacy": row["legacy"], "core": row["core"]}
        if not values.pulse_present or not snap["pulse_present"] or snap["spo2"] is None:
            rows.append({**entry, "candidate_causes": [], "mode": "pulseless: not attributed"})
            continue
        engine_spo2 = float(snap["spo2"])
        # The engine's circulation grows with the deficit (V = (1 - circulation) x 833 mL-eq).
        deficit = snap["circulation"] - result.legacy.snapshots[0]["circulation"]
        engine_raw_sbp = anchors.sbp - profile.sbp_per_pressure_deficit * deficit
        shown = _display(values)
        entry.update({"core_raw_sbp": round(values.sbp, 3), "core_displayed_sbp": shown["sbp"],
                      "legacy_displayed_sbp": snap["sbp"], "legacy_raw_sbp": round(engine_raw_sbp, 3)})
        if _level(values.spo2, profile.oxygen_levels) != _level(engine_spo2, profile.oxygen_levels) \
                or level(values.sbp, engine_spo2) == row["legacy"]:
            rows.append({**entry, "candidate_causes": [], "mode": "not explained by the pressure threshold"})
            continue
        s3_alone = level(engine_raw_sbp, engine_spo2) != row["legacy"]
        s4_alone = level(shown["sbp"], engine_spo2) != row["legacy"]
        if s3_alone and s4_alone:
            causes, mode = ["KD-S3", "KD-S4"], "each_sufficient"
        elif s3_alone or s4_alone:
            causes, mode = ["KD-S3" if s3_alone else "KD-S4"], "sufficient_alone"
        else:
            causes, mode = ["KD-S3", "KD-S4"], "jointly_necessary"
        rows.append({**entry, "candidate_causes": causes, "mode": mode})
    return rows


def classify(key: str, summary: dict, attribution: list | None = None) -> dict:
    """Level 3 (P2D-9): for every compared variable of a run, its class and its candidate causes.

    - MATCH: no difference. A rounding tie with no mismatch (the same raw value on a .5
      boundary) is a MATCH of the physiology; the summary still lists its minutes apart and
      never counts them as matches.
    - APPROVED_DIRECTION_MAGNITUDE_TBD: every candidate cause has an approved direction; the size
      of the difference is not approved.
    - UNRESOLVED: no approved decision explains it.

    The candidates follow ``EXPECTED_DIFFERENCES`` (the causal path), and for consciousness the
    minute-by-minute ``attribution`` when given. The committed golden freezes the sizes, so any
    change to them fails the golden test and has to be reviewed.
    """
    classes = {}
    for name, entry in summary.items():
        if not entry["compared"]:
            continue
        if not entry["mismatched"]:
            classes[name] = {"classification": MATCH, "candidate_causes": []}
            continue
        expected = list(EXPECTED_DIFFERENCES[key].get(name, ()))
        causes, item, explained = expected, {}, True
        if name == "consciousness_level" and attribution:
            # Minute by minute; any minute left without a cause leaves the variable unresolved,
            # and so does a difference the run was not expected to have.
            causes = sorted({cause for row in attribution for cause in row["candidate_causes"]})
            item["by_minute"] = attribution
            explained = bool(expected) and all(row["candidate_causes"] for row in attribution) \
                and set(causes) <= set(expected)
        approved = explained and bool(causes) and all(DECISIONS.get(cause, ("",))[0] == "approved"
                                                      for cause in causes)
        classes[name] = {"classification": APPROVED_DIRECTION if approved else UNRESOLVED,
                         "candidate_causes": causes, **item}
    return classes


@dataclass(frozen=True)
class ShadowResult:
    variant_id: str
    scenario: str
    legacy: LegacyRun
    core: Trajectory
    rows: dict
    summary: dict

    @property
    def key(self) -> str:
        return f"{self.variant_id}/{self.scenario}"


def run_shadow(variant_id: str, scenario: str) -> ShadowResult:
    spec = SCENARIOS[scenario]
    legacy = run_legacy(variant_id, spec["orders"], spec["minutes"])
    core = run(anchors_from_legacy(legacy.arrival), contributors_from_legacy(legacy), spec["minutes"])
    rows = compare(legacy.snapshots, core.states, core.derived())
    return ShadowResult(variant_id, scenario, legacy, core, rows, summarize(rows))


def golden_report(results=None) -> dict:
    """The committed golden summary. Platform-dependent full-precision digests are left out."""
    import family_engine
    results = results if results is not None else [run_shadow(v, s) for v in VARIANTS for s in SCENARIOS]
    return {
        "core_version": CORE_VERSION,
        "legacy": {"family_engine_version": family_engine.FAMILY_ENGINE_VERSION,
                   "execution_version": family_engine.EXECUTION_VERSION},
        "parameters": {name: list(value) for name, value in PARAMETERS.items()},
        "legacy_literals": {name: list(value) for name, value in LEGACY_LITERALS.items()},
        "channel_bounds": {channel.value: list(bounds) for channel, bounds in CHANNEL_BOUNDS.items()},
        "differences": {key: list(value) for key, value in DIFFERENCES.items()},
        "decisions": {key: list(value) for key, value in DECISIONS.items()},
        "case_parameter_rules": dict(FAMILY_CASE_PARAMETER_RULES),
        "scenarios": {result.key: {"minutes": SCENARIOS[result.scenario]["minutes"],
                                   "orders": {str(m): t for m, t in SCENARIOS[result.scenario]["orders"].items()},
                                   "core_inputs": [item.to_spec() for item in result.core.contributors],
                                   "mismatching": {name: list(EXPECTED_DIFFERENCES[result.key].get(name, ()))
                                                   or "UNEXPLAINED" for name in mismatching(result.summary)},
                                   "classification": classify(result.key, result.summary,
                                                              consciousness_attribution(result)),
                                   "case_parameters": case_parameter_provenance(result.core.anchors,
                                                                                result.core.profile),
                                   "variables": result.summary}
                      for result in results},
    }


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="write per-minute rows and digests here")
    parser.add_argument("--write-golden", action="store_true", help=f"rewrite {GOLDEN.name}")
    args = parser.parse_args(argv)
    results = [run_shadow(v, s) for v in VARIANTS for s in SCENARIOS]
    report = golden_report(results)
    if args.out:
        for result in results:
            _write(args.out / f"{result.variant_id}__{result.scenario}.json",
                   {"rows": result.rows, "core_digest": result.core.digest(),
                    "legacy_digest": digest(list(result.legacy.snapshots)),
                    "core_trajectory": result.core.to_dict()})
        _write(args.out / "summary.json", report)
    if args.write_golden:
        _write(GOLDEN, report)
    for key, entry in report["scenarios"].items():
        print(key, "mismatching:", ", ".join(f"{k} ({v})" for k, v in entry["mismatching"].items()) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
