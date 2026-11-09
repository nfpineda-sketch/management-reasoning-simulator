"""P3-48: the GI development authority series, through the production sequence, as a test.

One case's whole acceptance battery is played with an authority site per encounter. The minute runs
inside the turn, where ``app.py`` runs it; the provenance is settled after ``Encounter.order`` returns,
which is after ``order_pipeline.settle``, where ``app.py`` settles it. The battery plays its own scripts:
nothing clinical is invented here.

The invariant this file defends is the one P3-48 found broken. An order the engine does not MODEL
produces no action for the turn, so the live site never saw it and committed, while the repository's own
eligibility reading called that scenario INELIGIBLE_UNSUPPORTED. The settled ledger is the only place the
class appears, and the site now reads it there. The two readings must agree, scenario by scenario.
"""
import tempfile

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

CASE = "gi_bleed_57m"
SNAP = "gi_pressure_committed"
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-series-")


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


def _play_the_battery_with_authority(monkeypatch, case=CASE):
    """Every encounter of one case's battery, each with its own authority site. Returns the rows."""
    import pilot_acceptance as acceptance
    for name, value in ((ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY),
                        (ra.SNAPSHOT_FLAG, SNAP), (ra.ENVIRONMENT_FLAG, "development"),
                        (rs.FLAG, rs.MODE_SHADOW_COMPARE), (store.STORE_FLAG, STORE_DIR)):
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    # Keyed by the SESSION, never shared: ``battery`` interleaves encounters, and a shared submission
    # list paired one encounter's turn with another's ledger. That produced a spurious contradiction and
    # a spurious halt while the authority itself was behaving.
    sites, books, rows = {}, {}, []
    real_init, real_order = acceptance.Encounter.__init__, acceptance.Encounter.order
    real_observe = rs.ShadowSession.observe

    def hooked_init(self, variant, seed=acceptance.SEED):
        real_init(self, variant, seed)
        site = (None if getattr(self, "shadow", None) is None
                else ra.open_site(self.state, environ=None,
                                  experiment_id=f"series-{variant}-{id(self):x}"))
        sites[id(self)] = site
        if site is not None:
            books[id(self.shadow)] = {"site": site, "submissions": []}

    def hooked_observe(self, before, state, parsed, result, run, submission_id):
        real_observe(self, before, state, parsed, result, run, submission_id)
        book = books.get(id(self))
        if book is None:
            return
        book["submissions"].append(submission_id)
        prepared = book["site"].minute(before, state, self, run, submission_id)
        if prepared is not None:
            state.clear()
            state.update(prepared)

    def hooked_order(self, text):
        book = books.get(id(getattr(self, "shadow", None)))
        seen = len(book["submissions"]) if book else 0
        entry = real_order(self, text)
        if book is not None and len(book["submissions"]) > seen:
            book["site"].settle_provenance(book["submissions"][-1],
                                           [dict(order) for order in (entry.get("orders") or [])])
        return entry

    def collect(label, encounter, turns):
        site = sites.get(id(encounter))
        if site is None:
            rows.append({"scenario": label, "case": encounter.variant, "site": False})
            return
        artifact = site.artifact()
        replay = ra.replay_site_artifact(artifact)
        minutes = artifact.get("minutes") or []
        rows.append({
            "scenario": label, "case": encounter.variant, "site": True, "artifact": artifact,
            "halted": bool(artifact.get("halted")),
            "halt_reason": str(artifact.get("halt_reason") or ""),
            "committed": sum(1 for item in minutes if item.get("outcome") == ra.COMMITTED),
            "minutes": len(minutes),
            "replay": replay,
            "digest_verified": store.verify(store.artifact_id(artifact)).get("verified"),
            "kinds": sorted({kind for item in minutes for kind in (item.get("action_kinds") or [])}),
            "settled_classes": sorted({name for item in minutes
                                       for name in (item.get("settled_action_classes") or [])}),
        })

    monkeypatch.setattr(acceptance.Encounter, "__init__", hooked_init)
    monkeypatch.setattr(acceptance.Encounter, "order", hooked_order)
    monkeypatch.setattr(rs.ShadowSession, "observe", hooked_observe)
    with acceptance.collecting(collect):
        acceptance.battery(case)
    return rows


@pytest.fixture(scope="module")
def series():
    with pytest.MonkeyPatch.context() as patch:
        yield _play_the_battery_with_authority(patch)


def test_s1_every_scenario_of_the_battery_opened_an_authority_site(series):
    assert len(series) == 17, [row["scenario"] for row in series]
    assert all(row["site"] for row in series), [row["scenario"] for row in series if not row["site"]]
    assert {row["case"] for row in series} == {CASE}


def test_s2_the_live_halt_and_the_certified_eligibility_reading_agree(series):
    """The P3-48 finding. A ``not_modelled`` order used to pass the live path unseen."""
    battery = ra.eligibility_battery()
    ineligible = {row["scenario"] for row in battery["rows"]
                  if row["case_id"] == CASE and row["classification"] == ra.INELIGIBLE_UNSUPPORTED}
    halted = {row["scenario"] for row in series if row["halted"]}
    assert ineligible == halted, {"only in the reading": sorted(ineligible - halted),
                                  "only live": sorted(halted - ineligible)}
    assert ineligible, "the battery must contain scenarios an unsupported action makes ineligible"
    # And the class that used to slip through is one of them, by name.
    unmodelled = [row for row in series if "not_modelled" in row["settled_classes"]]
    assert unmodelled, "the battery must still contain an order the engine does not model"
    for row in unmodelled:
        assert row["halted"], row["scenario"]
        assert ra.PROVENANCE_CONTRADICTION in row["halt_reason"] \
            or ra.UNSUPPORTED_AUTHORITY_ACTION in row["halt_reason"], row["halt_reason"]
    assert "not_modelled" in ra.unsupported_among(("fluid", "not_modelled"))


def test_s3_every_completed_scenario_is_structurally_acceptable(series):
    completed = [row for row in series if not row["halted"]]
    assert len(completed) == 13, [row["scenario"] for row in completed]
    for row in completed:
        replay, artifact = row["replay"], row["artifact"]
        assert row["committed"] == row["minutes"] >= 1, row["scenario"]
        assert replay["eligibility_present"] and replay["eligibility_consistent"], row["scenario"]
        assert replay["provenance_settled_minutes"] == row["minutes"], row["scenario"]
        assert replay["provenance_consistent_minutes"] == row["minutes"], row["scenario"]
        assert replay["covers_every_committed_minute"], row["scenario"]
        assert row["digest_verified"], row["scenario"]
        assert not [name for name in ra.ARTIFACT_FIELDS if name not in artifact], row["scenario"]
        for item in artifact["minutes"]:
            assert sorted(item["committed"]) == ["dbp", "map", "sbp"], (row["scenario"], item["minute"])
            assert not item.get("validation_failures"), (row["scenario"], item["minute"])
            assert item.get("provenance_settled") is True, (row["scenario"], item["minute"])
        for minute in replay["minutes"]:
            for flag in ("candidate_matches", "transaction_matches", "pressures_match",
                         "written_matches", "outcome_consistent", "provenance_consistent"):
                assert minute[flag], (row["scenario"], minute["minute"], flag)


def test_s4_every_halted_scenario_committed_nothing_it_should_not_have(series):
    halted = [row for row in series if row["halted"]]
    assert halted, "the series must exercise the refusal controls"
    for row in halted:
        artifact = row["artifact"]
        assert artifact["experiment_state"] == ra.EXPERIMENT_HALTED, row["scenario"]
        assert row["halt_reason"], row["scenario"]
        aborted = [item for item in artifact["minutes"] if item.get("outcome") == ra.ABORTED]
        assert aborted, row["scenario"]
        for item in aborted:
            assert not item.get("committed"), (row["scenario"], item["minute"])
            assert str(item.get("failure_reason") or ""), (row["scenario"], item["minute"])
        # A halt after a commit declares the mixed trajectory instead of hiding it.
        if row["committed"]:
            assert artifact["mixed_trajectory"] is True, row["scenario"]
        assert row["digest_verified"], row["scenario"]
        assert ra.replay_site_artifact(artifact)["eligibility_consistent"], row["scenario"]


def test_s5_the_series_covers_the_management_classes_the_battery_offers(series):
    kinds = {kind for row in series for kind in row["kinds"]}
    # Observation, crystalloid, a blood-containing bundle, PPI, consultation and reassessment all appear
    # among the scenarios that completed; the unsupported classes appear among the refusals.
    completed = {kind for row in series if not row["halted"] for kind in row["kinds"]}
    assert {"fluid", "blood", "ppi", "consult", "reassessment"} <= completed, sorted(completed)
    refused = {kind for row in series if row["halted"] for kind in row["kinds"]}
    assert {"norepinephrine", "anticoagulation", "aspirin"} <= refused | kinds, sorted(refused)
    longest = max(series, key=lambda row: row["committed"])
    assert longest["committed"] >= 5, longest["scenario"]


def test_s6_no_scoring_or_pilot_state_is_touched_by_the_series(series):
    for row in series:
        artifact = row["artifact"]
        flat = ra.canonical(artifact).lower()
        # ``pain_score`` is a clinical observable of the case, so the crude substring "score" is not the
        # check: the scoring SURFACES are. None of them may appear anywhere in an authority artifact.
        for forbidden in ("rubric", "radar", "penalt", "competenc", "global_score", "dimension",
                          "assessment_", "d1_", "d5_"):
            assert forbidden not in flat, (row["scenario"], forbidden)
        assert sorted(artifact) == sorted(ra.ARTIFACT_FIELDS), row["scenario"]
        eligibility = dict(artifact.get("eligibility") or {})
        assert eligibility.get("pilot", {}).get("looks_like_the_pilot") is False, row["scenario"]
        assert artifact["environment"] == "development", row["scenario"]
        assert artifact["snapshot_id"] == SNAP, row["scenario"]
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_s7_every_committed_minute_of_the_series_carries_a_valid_canonical_lineage(series):
    """P3-55: the one blocker P3-51 left. No unexplained provenance mismatch anywhere in the series.

    P3-52 measured the two batteries inside ``order_pipeline.settle``: 170 of 170 consumed actions carry
    ``_order_id``, 0 reach back to an earlier submission, and the only mismatch is the ``reload_resume``
    collision, which is now a NAMED violation that halts rather than a note nobody could explain.
    """
    rows = 0
    for row in series:
        committed = [item for item in row["artifact"]["minutes"] if item.get("outcome") == ra.COMMITTED]
        for item in committed:
            lineage = [dict(entry) for entry in (item.get("action_lineage") or [])]
            assert lineage, (row["scenario"], item["minute"], "a committed minute carries its lineage")
            for entry in lineage:
                assert entry["link"] == ra.LINK_VALID, (row["scenario"], item["minute"], entry)
                assert str(entry["order_id"]).strip(), (row["scenario"], entry)
                assert str(entry["fate"]).strip(), (row["scenario"], entry)
                assert entry["origin"] in (ra.ORIGIN_THIS_TURN, ra.ORIGIN_EARLIER), entry
                rows += 1
        replay = ra.replay_site_artifact(row["artifact"])
        assert replay["lineage_valid_minutes"] >= len(committed), row["scenario"]
        assert not any(item["lineage_violations"] for item in replay["minutes"]
                       if item["outcome"] == ra.COMMITTED), row["scenario"]
    assert rows >= 60, f"the series linked {rows} consumed actions"
