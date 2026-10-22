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
from .comparison import compare, mismatching, summarize
from .derived import PARAMETERS
from .integration import CHANNEL_BOUNDS, Trajectory, run
from .legacy_adapter import LEGACY_LITERALS, LegacyRun, anchors_from_legacy, contributors_from_legacy, run_legacy
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
              "thresholds, sympathetic decay time, withdrawal limit"),
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
_STRUCTURAL = {"lactate_mmol_l": "KD-S1", "respiratory_rate": "KD-S1", "hr": "KD-S2", "sbp": "KD-S4", "dbp": "KD-S4",
               "map": "KD-S4", "crt_s": "KD-S4"}
EXPECTED_DIFFERENCES = {
    f"{variant}/{scenario}": dict(_STRUCTURAL) for variant in VARIANTS for scenario in SCENARIOS}
# The oxygen runs last 20 minutes and V moves only with the bleeding, so the curve changes the
# pressures by one display step at most, and not every one of them.
del EXPECTED_DIFFERENCES["gi_bleed_57m/oxygen_non_rebreather"]["crt_s"]
for _name in ("map", "crt_s"):
    del EXPECTED_DIFFERENCES["gi_bleed_72f/oxygen_non_rebreather"][_name]
for _variant in VARIANTS:
    # Past the engine's circulation clamp, the rate follows the core's pressure (KD-S4) as well as
    # its sympathetic memory (KD-S2); it is listed under the larger cause.
    EXPECTED_DIFFERENCES[f"{_variant}/aggressive_volume"].update(
        {name: "KD-S4" for name in ("V_ml_eq", "hr")})
# The core reads the 80 mmHg threshold on its raw SBP (KD-S3, unchanged in P2C). Since the preload
# curve (KD-S4) lowers that SBP by under 1 mmHg, the crossing comes at minute 55 instead of 60:
# minutes 55-57 are the raw-versus-rounded reading alone, 58-60 also a lower displayed SBP.
EXPECTED_DIFFERENCES["gi_bleed_57m/untreated_60"]["consciousness_level"] = "KD-S3"

#: The decision behind each known difference (P2C, 2026-10-22). A difference whose decision is
#: approved is an APPROVED DIFFERENCE: the physiology that produces it was approved, while its
#: size still rests on the provisional (TBD) parameters.
DECISIONS = {
    "KD-S1": ("approved", "REVISE CORE: D with memory produces lactate; RR from W plus a saturating metabolic drive"),
    "KD-S2": ("approved", "ADOPT CORE DIRECTION: HR from R plus one common sympathetic drive plus modulators"),
    "KD-S3": ("approved", "RESOLVED, not changed in P2C: physiology reads the unrounded state; display and gating "
                          "read Observation v2"),
    "KD-S4": ("approved", "REVISE CORE: one smooth, saturating preload curve; no clamp"),
}
MATCH, APPROVED_DIFFERENCE, UNRESOLVED_DIFFERENCE = "MATCH", "APPROVED DIFFERENCE", "UNRESOLVED DIFFERENCE"


def classify(key: str, summary: dict) -> dict:
    """Level 3: MATCH, APPROVED DIFFERENCE or UNRESOLVED DIFFERENCE for every compared variable of a run.

    A rounding tie (the same raw value on a .5 boundary) is a MATCH of the physiology; its
    minutes stay listed in the summary.
    """
    classes = {}
    for name, entry in summary.items():
        if not entry["compared"]:
            continue
        reason = EXPECTED_DIFFERENCES[key].get(name)
        if not entry["mismatched"]:
            classes[name] = MATCH
        elif reason in DECISIONS and DECISIONS[reason][0] == "approved":
            classes[name] = APPROVED_DIFFERENCE
        else:
            classes[name] = UNRESOLVED_DIFFERENCE
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
        "scenarios": {result.key: {"minutes": SCENARIOS[result.scenario]["minutes"],
                                   "orders": {str(m): t for m, t in SCENARIOS[result.scenario]["orders"].items()},
                                   "core_inputs": [item.to_spec() for item in result.core.contributors],
                                   "mismatching": {name: EXPECTED_DIFFERENCES[result.key].get(name, "UNEXPLAINED")
                                                   for name in mismatching(result.summary)},
                                   "classification": classify(result.key, result.summary),
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
