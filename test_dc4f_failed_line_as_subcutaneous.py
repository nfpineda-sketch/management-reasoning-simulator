"""DC4-F, option B minimal (faculty, 2026-09-29, cycle 10, C10-09).

Glucagon or octreotide given through the cannula that is not in the vein is absorbed from the
tissue as a subcutaneous dose -- a route both drugs have -- so it acts as the same dose given
subcutaneously. In this engine neither drug's onset or effect depends on its route, so the
decision changes no trajectory: what changes is what the technical record says about the dose
(``glucose_rescue.effect_rule``). The share recorded as reaching the circulation directly stays
the configuration's 15 %; a dose through a working line keeps "as modelled".
"""
import pytest

import glucose_rescue
import hypoglycemia_catalog as catalog
from catalog_trajectories import launch
from family_engine import execute_family_bundle
from family_parser import parse_family_actions

FAILED_LINE = [c["id"] for c in catalog.configurations() if c["conditions"]["iv_access_failed"]]
DOSES = {"glucagon": "glucagon 1 mg", "octreotide": "octreotide 50 mcg"}


def _played(configuration_id, order):
    state = launch(configuration_id, "hypoglycemia", allow_review_candidates=True)
    summaries = []
    for text in (order, "Reassess in 30 minutes.", "Reassess in 60 minutes."):
        result = execute_family_bundle(state, parse_family_actions(text))
        assert result["executed"], (text, result["clarification"])
        summaries += result["action_summaries"]
    return state, summaries


def test_six_configurations_run_through_a_failed_line():
    assert len(FAILED_LINE) == 6


@pytest.mark.parametrize("configuration_id", FAILED_LINE)
@pytest.mark.parametrize("kind", sorted(DOSES))
def test_a_dose_through_the_failed_line_acts_as_the_same_dose_given_subcutaneously(configuration_id, kind):
    through_line, summaries = _played(configuration_id, f"Give {DOSES[kind]} IV.")
    under_skin, _ = _played(configuration_id, f"Give {DOSES[kind]} SC.")
    line, skin = through_line["family_state"], under_skin["family_state"]
    assert line["glucose"] == pytest.approx(skin["glucose"])
    assert line.get(kind + "_at") == skin.get(kind + "_at")
    assert through_line["observable"]["mental_status"] == under_skin["observable"]["mental_status"]
    delivery = next(s for s in summaries if s.get("type") == kind)["delivery"]
    assert delivery["share_to_circulation"] == glucose_rescue.FAILED_ACCESS_SHARE
    assert delivery["effect"] == glucose_rescue.FAILED_LINE_EFFECT[kind]
    assert "pending" not in delivery["effect"]


@pytest.mark.parametrize("kind", sorted(DOSES))
def test_through_a_working_line_the_record_says_as_modelled(kind):
    working = next(c["id"] for c in catalog.configurations() if not c["conditions"]["iv_access_failed"])
    _, summaries = _played(working, f"Give {DOSES[kind]} IV.")
    delivery = next(s for s in summaries if s.get("type") == kind)["delivery"]
    assert (delivery["share_to_circulation"], delivery["effect"]) == (1.0, "as modelled")
