"""P3-227: every route by which a GI encounter's clock moves reaches the dormant site, held-order releases included, and with the evaluation off it is the legacy.

TEST-SIDE. The routes were inventoried in P3-215 (``test_phase3_clock_routes.py``); this file adds what the inventory could not show by itself:

* 227 held orders: the engine releases a held order only INSIDE one of the two functions that move the clock (a release at an information activity and a release
  inside an order turn), both hooked; the order is NOT applied at its placement; the site evaluates the turn that released it.
* 227A: the writer-inventory guard FAILS on a new, unwired writer of ``sim_time`` (a synthetic one is detected), instead of passing unseen.
* 227B: with the evaluation off, or on, the legacy encounter is exactly the same: the same state and the same ledger after every step of a mixed script.
"""
import ast
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pair_site as site_module
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_phase3_clock_routes as routes
from family_engine import advance_clinical_time
from test_phase3_clock_routes import CASE, OTHER_GI
from test_shadow_resolution import GI, HELD

ROOT = Path(__file__).resolve().parent
DRY = {rs.FLAG: rs.MODE_SHADOW_COMPARE, pair.DRY_FLAG: pair.DRY_ON}


class Page:
    """The page's two clock routes, as the headless harness can play them, with the page's ONE hook (``runtime_authority.after_clock_moved`` -> the pair layer)."""

    def __init__(self, case, *, hook):
        self.encounter = acceptance.Encounter(case)
        self.hook, self.store, self.sequence = hook, {}, 0
        self.trail = []

    @property
    def site(self):
        held = self.store.get(pair.DRY_KEY)
        return None if held is None else held[1]

    def _record(self, label):
        self.trail.append((label, ra.digest_of(self.encounter.state)))

    def order(self, text):
        encounter = self.encounter
        before = encounter.shadow.capture(encounter.state)
        entry = encounter.order(text)
        ran = [dict(item) for item in entry["orders"]]
        self.sequence += 1
        if self.hook:
            pair.after_clock_moved(self.store, encounter.shadow, before, encounter.state, ran, f"s{self.sequence}", ra.ORDER_TURN, environ=DRY)
            pair.after_orders_settled(self.store, encounter.shadow, ran, environ=DRY)
        self._record(f"order: {text}")
        return entry

    def spend(self, minutes, label="history question"):
        encounter = self.encounter
        before = encounter.shadow.capture(encounter.state)
        result = advance_clinical_time(encounter.state, minutes, label=label)
        encounter.shadow.observe_time(before, encounter.state, result)
        self.sequence += 1
        if self.hook:
            pair.after_clock_moved(self.store, encounter.shadow, before, encounter.state, None, f"s{self.sequence}", ra.CLINICAL_TIME, environ=DRY)
        self._record(f"spend {minutes}: {label}")
        return result


# -- 227: held orders -----------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", (CASE, OTHER_GI))
@pytest.mark.parametrize("kind", ("blood", "fluid", "oxygen"))
def test_h1_a_held_order_released_during_an_information_activity_is_evaluated_at_the_clinical_time_route_and_not_applied_at_its_placement(case, kind):
    text, _ = HELD[GI][kind]
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        page = Page(case, hook=True)
        page.order(text)
        shadow, site = page.encounter.shadow, page.site
        assert isinstance(site, site_module.DormantPairSite)
        assert [item for item in shadow.mirrored if item.kind == kind] == [], "a held order does not act at its placement"
        assert shadow.held and shadow.held[0]["state"] == rs.ORDER_HELD
        placed = len(site.records)
        page.spend(14)
    entry = shadow.held[0]
    assert entry["state"] == rs.ORDER_EXECUTED and entry["placed_minute"] < entry["executed_minute"] <= 15
    activity = site.records[placed:]
    assert [(record["route"], record["verdict"]) for record in activity] == [(ra.CLINICAL_TIME, pair.WOULD_COMMIT)]
    assert [row["minute"] for row in activity[0]["interval"]] == list(range(site.records[placed - 1]["minute"] + 1, 16))
    assert entry["executed_minute"] in [row["minute"] for row in activity[0]["interval"]], "the release minute is one of the minutes the interval validated"
    assert site.state == site_module.WOULD_COMMIT and site.halt is None


@pytest.mark.parametrize("case", (CASE, OTHER_GI))
def test_h2_a_held_order_released_inside_an_order_turn_is_evaluated_at_the_order_route(case):
    text, _ = HELD[GI]["blood"]
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        page = Page(case, hook=True)
        page.order(text)
        site, shadow = page.site, page.encounter.shadow
        placed = len(site.records)
        page.order("Give 500 mL normal saline over 12 minutes.")                  # a turn that spends time: the engine releases the held order inside it
    entry = shadow.held[0]
    assert entry["state"] == rs.ORDER_EXECUTED and entry["executed_minute"] > entry["placed_minute"]
    turn = site.records[placed]
    assert turn["route"] == ra.ORDER_TURN and turn["verdict"] == pair.WOULD_COMMIT and entry["executed_minute"] in [row["minute"] for row in turn["interval"]]
    assert site.halt is None and "blood" in [item.kind for item in shadow.mirrored]


def test_h3_the_engine_releases_a_held_order_only_inside_the_two_functions_that_move_the_clock_and_both_are_hooked():
    """Static: the release functions have exactly the two callers the hook covers, so a release cannot happen on a route the site does not see."""
    tree = ast.parse((ROOT / "family_engine.py").read_text(encoding="utf-8"))
    for target in ("_release_due_orders", "_release_due_diagnostics"):
        callers = {function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
                   for node in ast.walk(function) if isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] == target}
        assert callers == {"advance_clinical_time", "execute_family_bundle"}, (target, callers)
    for target in ("_release_due_orders", "_release_due_diagnostics"):
        for path in sorted(ROOT.glob("*.py")):
            if path.name.startswith(("test_", "regression_")) or path.name == "family_engine.py":
                continue
            assert target not in path.read_text(encoding="utf-8"), (path.name, target)       # nothing outside the engine releases an order
    page = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    hooked = routes._functions_calling(page, "_after_the_clock_moved")
    assert hooked == {"spend_clinical_time"} | routes._functions_calling(page, "execute_bundle"), hooked


# -- 227A: the inventory guard ------------------------------------------------------------------------------------------------------------------------------------

def test_w1_a_new_writer_of_the_clock_is_detected_and_would_fail_the_inventory(monkeypatch):
    """Negative control of the guard itself: a repository with one more function that assigns ``state["sim_time"]`` yields a different inventory, so
    ``test_t1`` (which pins the exact set) fails instead of passing unseen."""
    known = routes._writers_of_the_clock()
    directory = Path(tempfile.mkdtemp(prefix="phase3-routes-"))
    for name in ("family_engine.py",):
        (directory / name).write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
    (directory / "new_clock_writer.py").write_text("def quietly_advance(state):\n    state['sim_time'] = state['sim_time'] + 1\n", encoding="utf-8")
    monkeypatch.setattr(routes, "ROOT", directory)
    found = routes._writers_of_the_clock()
    assert ("new_clock_writer.py", "quietly_advance") in found and found != known
    assert {("family_engine.py", "advance_clinical_time"), ("family_engine.py", "execute_family_bundle")} <= found


def test_w2_the_inventory_still_names_exactly_the_five_known_writers_and_only_two_reach_a_gi_case():
    assert routes._writers_of_the_clock() == {("family_engine.py", "advance_clinical_time"), ("family_engine.py", "execute_family_bundle"),
                                              ("app.py", "_advance_with_timed_fluids"), ("coupled_encounter.py", "tick"), ("generated_engine.py", "_minute")}
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    block = source[source.index("def execute_bundle("):]
    # the legacy page writer is reached only from the page's own non-family branch, which a GI case (engine_family gi_bleed) never takes
    assert block.count("_advance_with_timed_fluids(") >= 1 and "execute_family_bundle" in block


# -- 227B: off (or dormant-on) = the legacy, exactly ---------------------------------------------------------------------------------------------------------------------

SCRIPT = (("order", "Place an IV line."), ("order", "Give 500 mL normal saline over 10 minutes."), ("spend", 5), ("order", "Order a lactate, wait for the result, then give oxygen 15 L/min by non-rebreather mask."),
          ("spend", 12), ("order", "Order a type and crossmatch."), ("order", "Transfuse 2 units of packed red cells."), ("spend", 20, "examination"), ("order", "Reassess in 10 minutes."))


def _play(case, hook):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        page = Page(case, hook=hook)
        ledgers = []
        for step in SCRIPT:
            if step[0] == "order":
                entry = page.order(step[1])
                ledgers.append(ra.digest_of([{key: value for key, value in dict(item).items()} for item in entry["orders"]]))
            else:
                page.spend(*step[1:])
    return page, ledgers


@pytest.mark.parametrize("case", (CASE, OTHER_GI))
def test_o1_with_the_dormant_evaluation_on_the_legacy_encounter_is_exactly_what_it_is_with_it_off(case):
    """227B. Same state digest after EVERY step and the same order ledger: the dormant site observes, evaluates a copy, and changes nothing."""
    off, ledgers_off = _play(case, hook=False)
    on, ledgers_on = _play(case, hook=True)
    assert off.trail == on.trail and ledgers_off == ledgers_on and off.site is None
    site = on.site
    assert isinstance(site, site_module.DormantPairSite) and site.violations == [] and len(site.records) >= 6
    assert ra.digest_of(on.encounter.state) == ra.digest_of(off.encounter.state)
    assert [item["to"] for item in site.transitions][0] == "NOT_STARTED"


def test_o2_with_every_flag_off_the_hook_builds_nothing_at_all():
    """The default: no dry flag, no site, no store key. One dictionary lookup per turn."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        before = encounter.shadow.capture(encounter.state)
        entry = encounter.order("Give 500 mL normal saline over 10 minutes.")
        held = {}
        for environ in ({}, {rs.FLAG: rs.MODE_SHADOW_COMPARE}, {pair.DRY_FLAG: pair.DRY_ON}):
            assert pair.after_clock_moved(held, encounter.shadow, before, encounter.state, [dict(i) for i in entry["orders"]], "s1", ra.ORDER_TURN, environ=environ) is None
            assert held == {}, environ
