"""Level 2 of the P2C calibration: probes across families, prepared for faculty bands.

    python -m clinical_core.bands

Each probe is a synthetic patient, from one neutral synthetic arrival (not a bank case),
driven by declared channel changes and the case declarations the core holds. The report
shows what the core reads at the provisional parameters, so that faculty can set the
plausible band each probe must fall in. Each family probes the chain the decisions name:
- GI bleed / trauma: V, D and Hb;
- sepsis: D and T (metabolic demand has no channel yet);
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

from .derived import derive
from .integration import Contribution, Contributor, step
from .provenance import ChannelDelta, SourceKind
from .state import Anchors, Channel, RhythmState, UnresolvedBoundary, initial_state

#: A neutral synthetic arrival shared by every probe, so that each probe's effect stands alone.
ARRIVAL = dict(case_id="band_probe", sbp=120.0, dbp=75.0, hr=80.0, spo2=97.0, respiratory_rate=16.0, crt_s=2.0,
               lactate=1.0, hb=13.0, glucose=100.0, k=4.0, fio2=0.21, rhythm=RhythmState.sinus(80.0),
               consciousness_level=0)


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


def _bolus(id_, minute, ml):
    return Drift(id_, "V", minute - 1, minute, ml)


#: probe -> (family, what it drives, case declarations, contributors, minutes read)
PROBES = {
    "haemorrhage": ("GI bleed / trauma", "V -10 mL/min and Hb -0.02 g/dL/min for 60 min", {},
                    (Drift("bleed_v", "V", 0, 60, -10.0), Drift("bleed_hb", "hb", 0, 60, -0.02)), (0, 30, 60)),
    "vasodilation": ("sepsis", "T -0.01/min for 40 min (to 0.6)", {},
                     (Drift("tone", "T", 0, 40, -0.01),), (0, 20, 40, 60)),
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

COLUMNS = ("map", "pulse_rate_bpm", "respiratory_rate", "lactate", "crt_s", "output_rel")


def probe(name: str) -> list[dict]:
    """The readings at the probe's minutes. A probe that reaches an unresolved boundary (P2D-2)
    stops there, and its last row says so instead of carrying an impossible state forward."""
    family, drives, declared, contributors, minutes = PROBES[name]
    anchors = Anchors(**{**ARRIVAL, **declared})
    states, stopped = [initial_state(anchors)], None
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
                         "D": state.D, "L": state.L, "V": state.V})
    return rows + ([stopped] if stopped else [])


def report() -> str:
    lines = ["| Probe | Family | Drives | Min | MAP | HR | RR | Lactate | CRT | Output | D | L | Band |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, (family, drives, _, _, _) in PROBES.items():
        for index, row in enumerate(probe(name)):
            head = (name, family, drives) if index == 0 else ("", "", "")
            if "stopped" in row:
                lines.append("| " + " | ".join(head + (str(row["minute"]),) + ("",) * 8
                                               + ("stopped: unresolved boundary (P2D-2)",)) + " |")
                continue
            values = [f"{row['minute']}", f"{row['map']:.0f}", f"{row['pulse_rate_bpm']:.0f}",
                      f"{row['respiratory_rate']:.0f}", f"{row['lactate']:.1f}", f"{row['crt_s']:.1f}",
                      f"{row['output_rel']:.2f}", f"{row['D']:.2f}", f"{row['L']:.2f}",
                      "TBD" if BANDS[name] is None else str(BANDS[name])]
            lines.append("| " + " | ".join(head + tuple(values)) + " |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
