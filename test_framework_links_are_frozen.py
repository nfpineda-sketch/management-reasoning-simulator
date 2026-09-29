"""An observation keeps the framework links its objective had when it was confirmed (TD-03, cycle 10).

The night audit of cycle 5 (59BG) found that only the mapping's version was frozen with an
observation: a view by milestone would read today's links, so a mapping changed later would move
what an old observation was evidence for. The links are now frozen with each new observation; one
recorded before keeps reading today's links, as it always did.
"""
import evidence_views
from progress_store import ProgressStore
from test_resident_pages import program  # noqa: F401 -- the fixture


def _goal(objective, today, *items):
    return {"objective_id": objective, "competency_mapping": today, "observations": list(items)}


def _item(identifier, links=None):
    provenance = {"contributions": None, **({"links": links} if links is not None else {})}
    return {"id": identifier, "attempt_id": "a-" + identifier, "provenance": provenance}


OLD = {"framework": "ACGME", "code": "PC3", "label": "Diagnostic evaluation"}
NEW = {"framework": "ACGME", "code": "PC4", "label": "Emergency stabilization"}


def test_a_code_the_mapping_dropped_still_holds_the_observation_confirmed_under_it():
    goal = _goal("R1-05", [NEW], _item("frozen", links=[OLD]))
    rows = {row["code"]: row for row in evidence_views.framework_rows([goal], "ACGME")}
    assert [item["id"] for item in rows["PC3"]["observations"]] == ["frozen"]
    # The code the objective reaches today is listed, and the older observation is not moved there.
    assert rows["PC4"]["observations"] == []


def test_an_observation_recorded_before_the_links_were_frozen_reads_todays_links():
    goal = _goal("R1-05", [NEW], _item("legacy"))
    rows = {row["code"]: row for row in evidence_views.framework_rows([goal], "ACGME")}
    assert set(rows) == {"PC4"} and [item["id"] for item in rows["PC4"]["observations"]] == ["legacy"]


def test_an_observation_confirmed_with_no_link_to_the_framework_counts_under_none():
    goal = _goal("R1-05", [NEW], _item("unlinked", links=[]))
    rows = {row["code"]: row for row in evidence_views.framework_rows([goal], "ACGME")}
    assert rows["PC4"]["observations"] == []


def test_an_observation_recorded_today_carries_its_objectives_links(program):  # noqa: F811
    store, _, faculty, people, _ = program
    goals = ProgressStore(store).get_progress(faculty, people["resident-one"]["id"])["objectives"]
    observed = [item for goal in goals for item in evidence_views.recorded(goal)]
    assert observed
    for goal in goals:
        for item in evidence_views.recorded(goal):
            links = item["provenance"]["links"]
            today = [(link["framework"], link["code"]) for link in goal.get("competency_mapping") or []
                     if isinstance(link, dict) and link.get("framework") and link.get("code")]
            assert [(link["framework"], link["code"]) for link in links] == today

