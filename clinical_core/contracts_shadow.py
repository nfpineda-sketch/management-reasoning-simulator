"""The golden comparison routed through the final Phase-1 Contracts v2 (P2B-4).

    python -m clinical_core.contracts_shadow

The same 10 scenarios x 2 cases as ``shadow``, with the inputs and outputs going through
Contracts v2:
1. the family engine runs through the page's order path, keeping each turn's contracts
   (``contracts_legacy``);
2. the core's interventions come from those contracts alone (``contracts_input``);
3. the core's result is emitted as shadow Contracts v2 records (``contracts_output``).

The report this produces must equal the committed golden. One renaming is made before
comparing: each intervention is named by the ledger's ``order_id``, written in the
legacy adapter's naming (``m<minute>-<index>-<type>``). Nothing is tuned. The comparison
writes nothing.

Two quantities the contracts do not carry are rebuilt by the input adapter:
- a queued bag's start;
- an oxygen device's FiO2.

Both are checked against what the engine itself did (its per-action summary and its
FiO2), and the run fails closed on any difference.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

from .comparison import compare, summarize
from .contracts_input import AdaptedInputs, adapt
from .contracts_legacy import ContractRun, run_contract_legacy
from .contracts_output import shadow_trace
from .integration import Trajectory, run
from .interventions import Oxygen
from .legacy_adapter import UnsupportedScenario, anchors_from_legacy, haemorrhage_from_legacy
from .shadow import GOLDEN, SCENARIOS, VARIANTS, golden_report


@dataclass(frozen=True)
class ContractShadowResult:
    variant_id: str
    scenario: str
    legacy: ContractRun
    adapted: AdaptedInputs
    core: Trajectory
    rows: dict
    summary: dict

    @property
    def key(self) -> str:
        return f"{self.variant_id}/{self.scenario}"

    def trace(self):
        """The shadow TraceProvenance v2 record of this run."""
        return shadow_trace(self.core, self.adapted)


def run_contract_shadow(variant_id: str, scenario: str) -> ContractShadowResult:
    import family_engine
    spec = SCENARIOS[scenario]
    legacy = run_contract_legacy(variant_id, spec["orders"], spec["minutes"])
    adapted = adapt(legacy.actions(), legacy.fates(), [turn.time for turn in legacy.turns],
                    [turn.events for turn in legacy.turns], gi_bleed=family_engine.GI_BLEED,
                    devices=family_engine._DEVICES)
    check_rebuilt_against_engine(legacy, adapted)
    contributors = (haemorrhage_from_legacy(legacy.arrival),) + adapted.contributors
    core = run(anchors_from_legacy(legacy.arrival), contributors, spec["minutes"])
    rows = compare(legacy.snapshots, core.states, core.derived())
    return ContractShadowResult(variant_id, scenario, legacy, adapted, core, rows, summarize(rows))


def check_rebuilt_against_engine(legacy: ContractRun, adapted: AdaptedInputs) -> None:
    """What the contracts do not carry, rebuilt by rule, must be what the engine did."""
    for turn in legacy.turns:
        for kind in ("fluid", "blood"):
            # The engine writes one summary per action of a kind, in order (stops included).
            actions = [a for a in turn.actions if a.action_class == kind]
            summaries = [s for s in turn.phase0_summaries if s.get("type") == kind]
            if len(actions) != len(summaries):
                raise UnsupportedScenario(f"turn {turn.submission_id}: {len(actions)} {kind} orders but "
                                          f"{len(summaries)} engine summaries")
            for action, summary in zip(actions, summaries):
                if action.fields.get("operation") is not None:
                    continue
                engine_start = summary.get("delivery_starts_at_min", turn.minute)
                rebuilt = adapted.binding(action.order_id).start_minute
                if float(rebuilt) != float(engine_start):
                    raise UnsupportedScenario(f"order {action.order_id}: rebuilt start {rebuilt} but the engine "
                                              f"started it at {engine_start}")
    for contributor in adapted.contributors:
        if isinstance(contributor, Oxygen):
            engine_fio2 = legacy.snapshots[contributor.start_minute + 1]["oxygen_fio2"]
            if abs(contributor.fio2 - engine_fio2) > 1e-12:
                raise UnsupportedScenario(f"order {contributor.id}: rebuilt FiO2 {contributor.fio2} but the engine "
                                          f"set {engine_fio2}")


def legacy_names(legacy: ContractRun) -> dict:
    """Each ledger order_id in the legacy adapter's naming (the turn's minute and position)."""
    return {action.order_id: f"m{turn.minute:03d}-{index}-{action.fields['type']}"
            for turn in legacy.turns for index, action in enumerate(turn.actions)}


def contract_golden_report(results) -> dict:
    """The golden report of the contract-routed runs, with ledger ids renamed to the legacy naming.

    The core runs its contributors sorted by (source kind, id), and the report lists them in
    that order; after renaming they are listed again in that order, as the legacy ids sort.
    """
    report = golden_report(results)
    for result in results:
        names = legacy_names(result.legacy)
        listed = []
        for contributor, spec in zip(result.core.contributors, report["scenarios"][result.key]["core_inputs"]):
            for field in ("id", "stopped_by"):
                if spec.get(field) in names:
                    spec[field] = names[spec[field]]
            listed.append(((contributor.source.kind.value, spec["id"]), spec))
        report["scenarios"][result.key]["core_inputs"] = [spec for _, spec in sorted(listed, key=lambda item: item[0])]
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    results = [run_contract_shadow(v, s) for v in VARIANTS for s in SCENARIOS]
    produced = json.loads(json.dumps(contract_golden_report(results), allow_nan=False))
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key, entry in produced["scenarios"].items():
        print(key, "mismatching:", ", ".join(f"{k} ({v})" for k, v in entry["mismatching"].items()) or "none")
    same = produced == golden
    print("golden through Contracts v2:", "IDENTICAL to the committed golden" if same else "DIFFERENT")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
