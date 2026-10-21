"""The family engine through the Phase-0 order path, offline, with each turn's Contracts v2 (P2B-4).

``legacy_adapter.run_legacy`` drives the engine directly. This driver drives it the way
the encounter page does, through ``pilot_acceptance.Encounter``, the page's order path
without Streamlit:
1. the frozen reader;
2. the time words;
3. the safe defaults and the ledger tags;
4. the bundle rule;
5. the engine;
6. the ledger settling every order.

For each turn it keeps the contracts Phase 1 builds in shadow at the same points of the
live path:
- ``OrderAction`` v2 once the turn is opened and tagged;
- ``FateReceipt``, ``TurnTime``, ``EventInterruption`` and ``ObservationSnapshot`` v2
  once it is settled.

It works on its own copy of the case, one minute per turn. It writes no session, Trace or
persistence. The engine's per-action summaries are kept beside the contracts
(``phase0_summaries``). They are not a contract: they serve only to check what the input
adapter rebuilds.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

import pilot_acceptance
from contracts_v2 import events as event_contracts
from contracts_v2 import fates as fate_contracts
from contracts_v2 import observations as observation_contracts
from contracts_v2 import orders as order_contracts
from contracts_v2 import timing as time_contracts

from .legacy_adapter import UnsupportedScenario, scenario_case, snapshot

#: What the driver writes after each order so that the turn advances exactly one minute.
ONE_MINUTE = "Reassess in 1 minute."


@dataclass(frozen=True)
class ContractTurn:
    minute: int
    text: str
    submission_id: str
    actions: tuple
    fates: tuple
    time: time_contracts.TurnTime
    events: event_contracts.EventInterruption
    observation: observation_contracts.ObservationSnapshot
    phase0_summaries: tuple


@dataclass(frozen=True)
class ContractRun:
    variant_id: str
    arrival: dict
    snapshots: tuple
    turns: tuple
    final_state: dict

    def actions(self) -> tuple:
        return tuple(action for turn in self.turns for action in turn.actions)

    def fates(self) -> tuple:
        return tuple(fate for turn in self.turns for fate in turn.fates)


class _ContractEncounter(pilot_acceptance.Encounter):
    """The page's order path on a given case. It keeps the turn's OrderAction v2 when the turn opens."""

    def __init__(self, variant_id: str, state: dict):
        self.variant = variant_id
        self.state = state
        self.arrival = deepcopy(state.get("observable") or {})
        self.ledger, self.entries, self._turns = [], [], 0
        self.opened, self.submission = None, None

    def _execute(self, parsed, text):
        # Called by ``Encounter.order`` right after ``order_pipeline.open_turn`` tagged the
        # turn (submission ``t<n>``): the point where the live path builds OrderAction v2.
        self.submission = f"t{self._turns - 1}"
        self.opened = order_contracts.shadow_from_reader(parsed, submission_id=self.submission)
        return super()._execute(parsed, text)


def run_contract_legacy(variant_id: str, orders: Mapping[int, str], minutes: int, *,
                        state: Mapping | None = None) -> ContractRun:
    """One turn per minute; an order is written at its minute, followed by a one-minute reassessment.

    The run fails closed if any of these happens:
    - a turn did not execute;
    - a turn advanced other than one minute;
    - a turn was interrupted;
    - the ledger found an inconsistency.
    """
    current = scenario_case(variant_id, orders, minutes, state)
    arrival = deepcopy(current)
    encounter = _ContractEncounter(variant_id, current)
    snapshots, turns = [snapshot(current)], []
    for minute in range(minutes):
        text = f"{orders[minute]} {ONE_MINUTE}" if orders.get(minute) else ONE_MINUTE
        encounter.opened = None
        entry = encounter.order(text)
        if not entry["executed"] or entry["response_time_min"] - entry["decision_time_min"] != 1 \
                or entry["interrupted"] or entry["ledger_problems"] or encounter.opened is None:
            raise UnsupportedScenario(f"the page's order path did not run {text!r} as one plain minute")
        turns.append(ContractTurn(
            minute=minute, text=text, submission_id=encounter.submission, actions=encounter.opened,
            fates=fate_contracts.shadow_from_legacy_orders(entry["orders"]),
            time=time_contracts.shadow_from_legacy_turn(entry),
            events=event_contracts.shadow_from_legacy_turn(entry),
            observation=observation_contracts.shadow_from_legacy_turn(entry),
            phase0_summaries=tuple(deepcopy(entry["action_summaries"]))))
        snapshots.append(snapshot(encounter.state))
    return ContractRun(variant_id, arrival, tuple(snapshots), tuple(turns), deepcopy(encounter.state))
