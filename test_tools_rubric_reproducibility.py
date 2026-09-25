"""The reproducibility harness, run against a scripted evaluator: nothing is sent.

What it has to get right is what the report of 2026-09-24 asked for: the
encounter and the evaluator measured apart, every run a fresh request about
the same frozen record, no cache standing in for a second reading, never more
requests than evaluations, and no claim of stability that the runs do not all
support.
"""
import json

import pytest

import rubric
import tools_rubric_reproducibility as harness

CASE = "opioid_67f"


class Evaluator:
    """Answers each request from the next script in line, and counts the requests."""

    def __init__(self, *scripts, fail_on=()):
        self.scripts = list(scripts)
        self.calls = []
        self.fail_on = set(fail_on)
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) in self.fail_on:
            raise TimeoutError("scripted provider timeout")
        schema = kwargs["text"]["format"]["schema"]
        scores, occurred = self.scripts[(len(self.calls) - 1) % len(self.scripts)]
        refs = schema["properties"]["domains"]["items"]["properties"]["evidence_refs"]["items"]["enum"]
        body = {"domains": [], "concerns_for_review": [], "assistance_recorded": [],
                "record_limits": []}
        for domain in rubric.DOMAIN_IDS:
            score = scores.get(domain, 2)
            body["domains"].append({
                "domain_id": domain, "score": score,
                "evidence_refs": [] if score == rubric.NOT_ASSESSABLE else refs[:1],
                "learner_evidence": [], "rationale": "From the record.", "contrary_evidence": "None.",
                "limits": "None.", "opportunity": ("no_opportunity" if score == rubric.NOT_ASSESSABLE
                                              else "observed"),
                "next_level_gap": "maximum level reached" if score == 3 else "Targets were not set."})
        events = schema["properties"].get("event_verdicts", {}).get("properties", {})
        if events:
            body["event_verdicts"] = {event_id: {
                "verdict": "occurred" if event_id in occurred else "did_not_occur",
                "evidence_refs": refs[:1], "trigger_evidence": "x", "exclusions_checked": "x"}
                for event_id in events}
        return type("Response", (), {"status": "completed", "output_text": json.dumps(body)})()


@pytest.fixture(scope="module")
def record():
    return harness.frozen(CASE)


def test_the_same_script_is_the_same_encounter():
    result = harness.check_encounter(CASE, plays=3)
    assert result["identical"] and len(set(result["digests"])) == 1


def test_every_evaluation_is_its_own_request_about_the_same_record(record):
    evaluator = Evaluator(({"D2": 3}, ()), ({"D2": 2}, ()), ({"D2": 3}, ()))
    evaluation = harness.evaluate(record, 3, model="scripted", client=evaluator, api_key="")
    assert len(evaluator.calls) == 3 and len(evaluation["reports"]) == 3
    # The same question each time: same record, instructions, schema and model.
    assert len({json.dumps(call, sort_keys=True, default=str) for call in evaluator.calls}) == 1
    assert {item["report"]["source_hash"] for item in evaluation["reports"]} == {evaluation["fingerprint"]}


def test_a_disagreement_is_measured_and_never_called_stable(record):
    evaluator = Evaluator(({"D2": 3}, ()), ({"D2": 2}, ()), ({"D2": 3}, ()))
    summary = harness.summarize(record, harness.evaluate(record, 3, model="scripted",
                                                         client=evaluator, api_key=""))
    assert summary["all_runs_agreed"] is False
    assert summary["varying_domains"] == ["D2"]
    assert summary["domains"]["D2"] == {"scores": [3, 2, 3], "range": 1, "modal": "3",
                                        "agreement": 0.67, "not_assessable": 0,
                                        "opportunities": ["observed"] * 3}
    assert summary["adjusted_range"] == 1
    markdown = harness.as_markdown(summary)
    assert "The runs did not agree: D2" in markdown and "All runs agreed" not in markdown


def test_agreement_is_claimed_only_when_every_run_agreed(record):
    evaluator = Evaluator(({"D1": 3}, ()),)
    summary = harness.summarize(record, harness.evaluate(record, 2, model="scripted",
                                                         client=evaluator, api_key=""))
    assert summary["all_runs_agreed"] is True
    assert all(row["agreement"] == 1.0 for row in summary["domains"].values())


def test_an_event_verdict_that_changes_between_runs_is_reported(record):
    event_id = "opioid_no_ventilatory_support"
    evaluator = Evaluator(({}, (event_id,)), ({}, ()))
    summary = harness.summarize(record, harness.evaluate(record, 2, model="scripted",
                                                         client=evaluator, api_key=""))
    assert summary["events"][event_id] == ["occurred", "did_not_occur"]
    assert summary["all_runs_agreed"] is False
    penalties = [total["penalty"] for total in summary["totals"]]
    assert penalties == [3, 0]


def test_not_assessable_is_counted_apart_and_never_as_a_zero(record):
    evaluator = Evaluator(({"D5": rubric.NOT_ASSESSABLE}, ()), ({"D5": 0}, ()))
    summary = harness.summarize(record, harness.evaluate(record, 2, model="scripted",
                                                         client=evaluator, api_key=""))
    row = summary["domains"]["D5"]
    assert row["scores"] == [rubric.NOT_ASSESSABLE, 0] and row["not_assessable"] == 1
    assert row["range"] == 0  # only one numeric score to compare
    assert summary["totals"][0]["base"] is None and summary["totals"][0]["assessed"] == 4


def test_a_failed_run_is_reported_and_not_replaced(record):
    evaluator = Evaluator(({}, ()), fail_on={2})
    evaluation = harness.evaluate(record, 3, model="scripted", client=evaluator, api_key="")
    assert len(evaluator.calls) == 3 and len(evaluation["reports"]) == 2
    assert evaluation["failures"][0]["run"] == 2


def test_it_refuses_to_send_without_a_count_or_a_yes(record, capsys):
    assert harness.main(["--case", CASE, "--times", "3", "--dry-run"]) == 0
    assert "3 evaluation(s) = 3 paid request(s)" in capsys.readouterr().out
    assert harness.main(["--case", CASE, "--times", "3"]) == 2
    assert harness.main(["--case", CASE]) == 2
    with pytest.raises(ValueError):
        harness.evaluate(record, 0, client=Evaluator(({}, ())), api_key="")
    with pytest.raises(ValueError):
        harness.evaluate(record, harness.MAX_TIMES + 1, client=Evaluator(({}, ())), api_key="")


def test_two_saved_runs_are_compared_record_first(record, tmp_path):
    from copy import deepcopy
    evaluator = Evaluator(({"D2": 3}, ()), ({"D2": 2}, ()))
    first, second = (item["report"] for item in harness.evaluate(
        record, 2, model="scripted", client=evaluator, api_key="")["reports"])
    same = harness.compare(first, second, record, record)
    assert same["same_record"] is True and same["first_difference"] is None
    assert same["domains"]["D2"]["scores"] == [3, 2] and same["domains"]["D2"]["differs"]
    assert not same["domains"]["D1"]["differs"]
    # Another encounter: the comparison says so, and where it parted.
    other = deepcopy(record)
    other["payload"]["session"]["management_trace"][1]["decision_time_min"] += 5
    parted = harness.compare(first, second, record, other)
    assert parted["first_difference"]["index"] == 1
    # The files tools_rubric_runs writes, read back.
    for name, report in (("a", first), ("b", second)):
        (tmp_path / f"{name}.json").write_text(json.dumps({"usage": {}, "report": report}))
        (tmp_path / f"{name}.record.json").write_text(json.dumps(record))
    assert harness.main(["--compare", str(tmp_path / "a.json"), str(tmp_path / "b.json")]) == 0


# --- faculty decision 11 of 2026-09-25: measure first, never adapt the criterion ----

def _two_readings(record, first, second):
    evaluator = Evaluator(first, second)
    return [item["report"] for item in harness.evaluate(
        record, 2, model="scripted", client=evaluator, api_key="")["reports"]]


def test_the_comparison_says_first_whether_the_readings_read_the_same_thing(record):
    a, b = _two_readings(record, ({"D2": 3}, ()), ({"D2": 2}, ()))
    same = harness.identity(a, b)
    assert same["differing"] == [] and "every difference below is the evaluator's" in same["conclusion"]
    other_prompt = dict(b, prompt_version="1.0")
    changed = harness.identity(a, other_prompt)
    assert changed["differing"] == ["prompt"]
    assert "cannot be attributed to the evaluator's reading alone" in changed["conclusion"]
    other_record = dict(b, source_hash="0" * 64)
    assert "Not the same record" in harness.identity(a, other_record)["conclusion"]


def test_a_difference_in_the_total_is_decomposed_and_must_be_explained(record):
    event_id = "opioid_no_ventilatory_support"
    a, b = _two_readings(record, ({"D2": 3, "D3": 3}, ()), ({"D2": 2, "D3": 2}, (event_id,)))
    difference = harness.explain_difference(a, b)
    assert difference["points"] == 5 and difference["needs_explanation"]
    assert [(row["domain"], row["points"]) for row in difference["domains"]] == [("D2", -1), ("D3", -1)]
    assert difference["events"] == [{"event_id": event_id, "a": "did_not_occur", "b": "occurred"}]
    assert difference["penalty"] == [0, 3] and difference["critical_events"] == [0, 1]
    text = harness.compare_markdown(harness.compare(a, b, record, record))
    assert "| Record |" in text and "every difference below is the evaluator's reading" in text
    assert harness.UNEXPLAINED.format(points=5) in text
    assert "- D2: 3 and 2 (-1)" in text and f"- {event_id}: did_not_occur and occurred" in text


def test_a_domain_scored_once_and_not_assessable_once_is_not_the_same_total(record):
    a, b = _two_readings(record, ({"D5": 2}, ()), ({"D5": rubric.NOT_ASSESSABLE}, ()))
    difference = harness.explain_difference(a, b)
    assert not difference["comparable"] and difference["needs_explanation"]
    assert difference["not_assessable"] == [0, 1]
    assert any("not totals of the same thing" in line for line in harness.explanation_lines(difference))


def test_agreeing_readings_need_no_explanation(record):
    a, b = _two_readings(record, ({"D1": 3}, ()), ({"D1": 3}, ()))
    assert harness.explain_difference(a, b)["needs_explanation"] is False


def test_the_summary_compares_totals_critical_events_and_not_assessable_and_calls_itself_exploration(record):
    evaluator = Evaluator(({"D2": 3}, ()), ({"D2": 2}, ()), ({"D2": 3}, ()))
    summary = harness.summarize(record, harness.evaluate(record, 3, model="scripted",
                                                         client=evaluator, api_key=""))
    assert summary["not_assessable"] == [0, 0, 0] and summary["critical_events"] == [0, 0, 0]
    assert summary["difference"]["points"] == 1
    markdown = harness.as_markdown(summary)
    assert harness.UNEXPLAINED.format(points=1) in markdown
    assert "Exploration, not validation: 3 reading(s) of 1 record(s)" in markdown


def test_every_reading_is_on_a_ledger_of_its_own(record, tmp_path):
    ledger = harness.ledger_path(tmp_path / "reproducibility")
    evaluator = Evaluator(({}, ()), fail_on={2})
    harness.evaluate(record, 3, model="scripted", client=evaluator, api_key="", ledger=ledger, batch="b1")
    entries = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert [entry["event"] for entry in entries] == ["started", "finished"] * 3
    assert {entry["kind"] for entry in entries} == {"evaluator_reading"}
    assert not any(entry["paid_encounter"] for entry in entries)
    assert [entry.get("outcome") for entry in entries if entry["event"] == "finished"] == ["ok", "failed", "ok"]
    # A scripted evaluator sends nothing to the provider: nothing is spent.
    assert harness.spent(ledger) == {"readings": 3, "requests": 0, "unfinished": 0}
    # A reading that started and never finished is counted as spent.
    with ledger.open("a") as handle:
        handle.write(json.dumps({"event": "started", "batch": "b2", "record_fingerprint": "x", "run": 1}) + "\n")
    assert harness.spent(ledger) == {"readings": 4, "requests": 1, "unfinished": 1}


def test_one_exploration_sends_at_most_ten_requests_across_records(capsys, tmp_path):
    assert harness.main(["--case", "opioid_35m", "--case", CASE, "--times", "6", "--dry-run"]) == 2
    assert harness.main(["--case", "opioid_35m", "--case", CASE, "--times", "5", "--dry-run",
                         "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "10 paid request(s) in all" in out and "apart from any encounter" in out
    assert harness.main(["--spent", "--out", str(tmp_path)]) == 0
    assert '"requests": 0' in capsys.readouterr().out
