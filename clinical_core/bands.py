"""Level 2 of the P2C calibration: probes across families, prepared for faculty bands.

    python -m clinical_core.bands

Each probe is a synthetic patient, from one neutral synthetic arrival (not a bank case),
driven by declared channel changes, declared blood flows and the case declarations the core
holds. The report shows what the core reads at the provisional parameters, so that faculty can
set the plausible band each probe must fall in. Each family probes the chain the decisions name:
- haemorrhage (GI bleed / trauma): a SYNTHETIC_CROSS_FAMILY_HAEMORRHAGE_PROBE (P2I-2U): a declared
  whole-blood loss through the shared blood state, from which V, Hb and so D follow; its rate is
  synthetic, not a GI or trauma rate;
- sepsis: D, T and a declared factor on oxygen demand (P2E-2: a synthetic factor; no sepsis
  module is migrated, and the multipliers are TBD; see ``DIAGNOSTICS``);
- ACS, RV and PE: preload and P;
- pulmonary oedema: overload and L;
- asthma and opioids: W and RR.

No band is set here. Every band is TBD and no test compares a value with one: Level 2 is
prepared, not finalized, and the AI does not set clinical bands. Nothing is tuned to these
probes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

from .derived import arrival_state, derive
from .integration import Contribution, Contributor, register, step
from .provenance import BloodFlow, BloodProcess, ChannelDelta, DemandModifier, SourceKind
from .state import Anchors, Channel, RhythmState, UnresolvedBoundary

#: A neutral synthetic arrival shared by every probe, so that each probe's effect stands alone.
ARRIVAL = dict(case_id="band_probe", sbp=120.0, dbp=75.0, hr=80.0, spo2=97.0, respiratory_rate=16.0, crt_s=2.0,
               lactate=1.0, hb=13.0, glucose=100.0, k=4.0, fio2=0.21, rhythm=RhythmState.sinus(80.0),
               consciousness_level=0)


@register
@dataclass(frozen=True)
class Drift(Contributor):
    """A declared change of one channel per minute over an interval (probe only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "band_probe_drift"

    id: str
    channel: str
    start_minute: int
    stop_minute: int
    per_minute: float

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), self.per_minute, self.source, minute,
                                                 f"probe: declared change of {self.channel}"),))


@register
@dataclass(frozen=True)
class Demand(Contributor):
    """A declared factor on metabolic oxygen demand over an interval (probe only, P2E-2)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "band_probe_demand"

    id: str
    start_minute: int
    stop_minute: int
    factor: float
    demand_kind: str = "disease"

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(demand=(DemandModifier(self.factor, self.demand_kind, self.source, minute,
                                                   "probe: declared factor on oxygen demand"),))


@register
@dataclass(frozen=True)
class BloodLoss(Contributor):
    """A declared whole-blood loss over an interval (probe only, P2I-2U).

    One flow out of the shared blood state, as a haemorrhage module's: the core takes volume and
    red cells together at the current composition, and V and Hb follow from the blood state. It
    writes neither V nor Hb.
    """

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "band_probe_blood_loss"

    id: str
    start_minute: int
    stop_minute: int
    ml_per_min: float

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(blood=(BloodFlow(BloodProcess.WHOLE_BLOOD_LOSS, self.ml_per_min, self.source, minute,
                                             "probe: declared whole-blood loss"),))


def _bolus(id_, minute, ml):
    return Drift(id_, "V", minute - 1, minute, ml)


#: probe -> (family, what it drives, case declarations, contributors, minutes read)
PROBES = {
    "haemorrhage": ("GI bleed / trauma", "synthetic whole-blood loss of 10 mL-eq/min for 60 min through the shared "
                    "blood state (a synthetic rate, not a GI or trauma rate); V and Hb follow from it", {},
                    (BloodLoss("blood_loss", 0, 60, 10.0),), (0, 30, 60)),
    "vasodilation": ("sepsis", "T -0.01/min for 40 min (to 0.6)", {},
                     (Drift("tone", "T", 0, 40, -0.01),), (0, 20, 40, 60)),
    "vasodilation_with_preload_loss": ("sepsis", "T -0.01/min and V -5 mL/min for 40 min (venous pooling, leak)",
                                       {}, (Drift("tone", "T", 0, 40, -0.01), Drift("leak", "V", 0, 40, -5.0)),
                                       (0, 20, 40, 60)),
    "vasodilation_with_demand": ("sepsis", "T -0.01/min for 40 min and oxygen demand x1.3 for 60 min (a synthetic "
                                 "factor, not a sepsis multiplier), then demand back to baseline",
                                 {}, (Drift("tone", "T", 0, 40, -0.01), Demand("demand", 0, 60, 1.3)),
                                 (0, 20, 40, 60, 120)),
    "pump_failure_then_bolus": ("ACS", "P -0.01/min for 30 min (to 0.7), then 500 mL at minute 40", {},
                                (Drift("pump", "P", 0, 30, -0.01), _bolus("bolus", 40, 500.0)), (0, 30, 40, 60)),
    "preload_dependent": ("RV infarct / PE", "preload position 0.25: 200 mL lost at minute 1, 250 mL given at 20",
                          {"preload_fraction": 0.25}, (_bolus("loss", 1, -200.0), _bolus("bolus", 20, 250.0)),
                          (0, 1, 20, 40)),
    "overload": ("pulmonary oedema", "preload position 0.8, pump reserve 0.3, P -0.3 at minute 1, then V +20 "
                 "mL/min for 100 min", {"preload_fraction": 0.8, "pump_reserve": 0.3},
                 (Drift("pump", "P", 0, 1, -0.3), Drift("fluid", "V", 1, 101, 20.0)), (0, 1, 50, 100)),
    "bronchospasm": ("asthma", "W +0.5 at minute 1", {}, (Drift("work", "W", 0, 1, 0.5),), (0, 1, 30)),
    "opioid": ("opioid", "W -0.7 at minute 1", {}, (Drift("drive", "W", 0, 1, -0.7),), (0, 1, 30)),
}

#: The plausible band for each probe: set by faculty, never here (Level 2, prepared only).
BANDS = {name: None for name in PROBES}
#: What a probe is, where its kind needs saying (P2I-2U). Until P2I-2U the haemorrhage probe moved V
#: (-10 mL/min) and Hb (-0.02 g/dL/min) by two independent scripted drifts, the physiology the faculty
#: retired with the shared blood state (P2I-2T); it is now one declared whole-blood flow.
PROBE_KINDS = {"haemorrhage": "SYNTHETIC_CROSS_FAMILY_HAEMORRHAGE_PROBE"}

#: P2D-7: what a probe shows that is not a defect to fix, and why. Lower afterload may raise
#: output; it must not by itself normalize pressure, delivery or D. The core lets output rise
#: with vasodilation and keeps MAP low; delivery rises with output (DO2 = flow x content). Since
#: P2E-2, D measures delivery against demand and delivery above demand is no credit: with demand
#: at its baseline D stays at 0, and with a declared rise in demand D accrues although output is
#: higher. Not forced either way; to be calibrated across families.
DIAGNOSTICS = {
    "vasodilation": {
        "classification": "PHYSIOLOGICALLY_PLAUSIBLE_PENDING_MULTI_FAMILY_CALIBRATION",
        "shows": "output up with lower afterload; MAP down and not normalized; delivery up; demand at baseline, "
                 "so D stays at 0 (no credit)",
        "gap": "oxygen extraction has no state; the sepsis demand multiplier is TBD and no sepsis module is migrated",
    },
    "vasodilation_with_preload_loss": {
        "classification": "PHYSIOLOGICALLY_PLAUSIBLE_PENDING_MULTI_FAMILY_CALIBRATION",
        "shows": "with venous pooling or leak, output, delivery and MAP fall and D rises: a rise in output is "
                 "not automatic",
        "gap": "the same",
    },
    "vasodilation_with_demand": {
        "classification": "PHYSIOLOGICALLY_PLAUSIBLE_PENDING_MULTI_FAMILY_CALIBRATION",
        "shows": "output and delivery up, yet D accrues while demand exceeds delivery; once the declared factor "
                 "stops, D repays at its own rate",
        "gap": "the factor 1.3 is synthetic; sepsis, fever and seizure multipliers are TBD",
    },
}

COLUMNS = ("map", "pulse_rate_bpm", "respiratory_rate", "lactate", "crt_s", "output_rel", "delivery_rel")


def probe(name: str) -> list[dict]:
    """The readings at the probe's minutes. A probe that reaches an unresolved boundary (P2D-2)
    stops there, and its last row says so instead of carrying an impossible state forward."""
    family, drives, declared, contributors, minutes = PROBES[name]
    anchors = Anchors(**{**ARRIVAL, **declared, "declared": {name: "synthetic_probe" for name in declared}})
    states, stopped = [arrival_state(anchors)], None
    for _ in range(max(minutes)):
        try:
            states.append(step(states[-1], contributors, anchors)[0])
        except UnresolvedBoundary as boundary:
            stopped = {"minute": states[-1].minute + 1, "stopped": str(boundary)}
            break
    rows = []
    for minute in minutes:
        if minute < len(states):
            state = states[minute]
            derived = derive(state, anchors)
            rows.append({"minute": minute, **{column: getattr(derived, column) for column in COLUMNS},
                         "D": state.D, "L": state.L, "V": state.V, "hb": state.hb, "demand": state.aux.oxygen_demand,
                         "shed_ml": state.blood.shed_ml, "circulating_ml": state.blood.volume_ml,
                         "outside_v": state.blood.outside_v})
    return rows + ([stopped] if stopped else [])


def report() -> str:
    lines = ["| Probe | Family | Drives | Min | MAP | HR | RR | Lactate | CRT | Output | DO2 | Hb | Demand | D | L | "
             "Band |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, (family, drives, _, _, _) in PROBES.items():
        for index, row in enumerate(probe(name)):
            label = f"{name} ({PROBE_KINDS[name]})" if name in PROBE_KINDS else name
            head = (label, family, drives) if index == 0 else ("", "", "")
            if "stopped" in row:
                lines.append("| " + " | ".join(head + (str(row["minute"]),) + ("",) * 11
                                               + ("stopped: unresolved boundary (P2D-2)",)) + " |")
                continue
            values = [f"{row['minute']}", f"{row['map']:.0f}", f"{row['pulse_rate_bpm']:.0f}",
                      f"{row['respiratory_rate']:.0f}", f"{row['lactate']:.1f}", f"{row['crt_s']:.1f}",
                      f"{row['output_rel']:.2f}", f"{row['delivery_rel']:.2f}",
                      f"{row['hb']:.2f}" + ("†" if row["outside_v"] else ""),
                      f"{row['demand']:.2f}", f"{row['D']:.2f}", f"{row['L']:.2f}",
                      "TBD" if BANDS[name] is None else str(BANDS[name])]
            lines.append("| " + " | ".join(head + tuple(values)) + " |")
    lines.append("")
    lines.append("† V written directly by a scripted probe, outside the shared blood state: this Hb does not follow "
                 "that volume, neither diluted nor concentrated (P2I-2U; routing these probes through the blood state "
                 "is open).")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
