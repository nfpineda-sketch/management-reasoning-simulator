"""The approvals the pilot candidate carries for the Spanish narrative and rubric (B-5, IG-0, TD-81).

The faculty approved the Spanish of the 30 pilot cases and of the five rubric domains at
exact versions. The candidate carries those approvals in the repository, and a fresh pilot
database holds no review: so these tests hold the tool that writes the files to what the
faculty approved, and the runtime to the rule that only the approved words are shown.
"""
import json
import re
from pathlib import Path

import pytest

import case_text
import pilot_freeze
import rubric
import rubric_text
import tools_case_text_approvals as approvals

ROOT = Path(__file__).resolve().parent


def _documented_versions():
    """The target version of each case in the 30-case integrity document (docs/revision)."""
    text = (ROOT / "docs/revision/B5_RELATO_INTEGRIDAD_30.md").read_text(encoding="utf-8")
    found = {}
    for line in text.splitlines():
        cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 7 and re.fullmatch(r"R\d[AB]?", cells[0]) and re.fullmatch(r"[0-9a-f]{64}", cells[6]):
            found[cells[1]] = cells[6]
    return found


def test_the_approved_versions_are_the_ones_the_review_documents_record():
    assert _documented_versions() == approvals.APPROVED_NARRATIVE


def test_exactly_the_thirty_pilot_cases_and_never_the_sandbox_case():
    pilot = pilot_freeze.accepted_variants()
    assert len(pilot) == 30 and len(set(pilot)) == 30
    assert set(approvals.APPROVED_NARRATIVE) == set(pilot)
    assert "trauma_hemothorax_41m" not in approvals.APPROVED_NARRATIVE
    assert [row["variant_id"] for row in approvals.pack("narrative")] == list(pilot)


def test_the_five_rubric_domains_and_only_the_fields_the_runtime_reads():
    assert set(approvals.APPROVED_RUBRIC) == set(rubric.DOMAINS)
    assert [row["domain_id"] for row in approvals.pack("rubric")] == list(rubric.DOMAINS)
    for kind in ("narrative", "rubric"):
        for row in approvals.pack(kind):
            assert list(row) == list(approvals.FIELDS[kind]) and row["decision"] == "approved"


@pytest.mark.parametrize("kind", ["narrative", "rubric"])
def test_a_version_the_faculty_did_not_approve_stops_the_tool_and_writes_nothing(kind, tmp_path, monkeypatch):
    table = "APPROVED_NARRATIVE" if kind == "narrative" else "APPROVED_RUBRIC"
    changed = dict(getattr(approvals, table))
    first = next(iter(changed))
    changed[first] = "0" * 64
    monkeypatch.setattr(approvals, table, changed)
    target = tmp_path / "approvals.json"
    with pytest.raises(approvals.ApprovalError, match=first):
        approvals.write(kind, target=target)
    assert not target.exists()
    text, ok = approvals.report(kind)
    assert not ok and "STOP" in text


@pytest.mark.parametrize("kind", ["narrative", "rubric"])
def test_a_missing_approval_stops_the_tool(kind, tmp_path, monkeypatch):
    table = "APPROVED_NARRATIVE" if kind == "narrative" else "APPROVED_RUBRIC"
    changed = dict(getattr(approvals, table))
    changed.pop(next(iter(changed)))
    monkeypatch.setattr(approvals, table, changed)
    with pytest.raises(approvals.ApprovalError, match="no faculty approval"):
        approvals.write(kind, target=tmp_path / "approvals.json")


def test_a_passage_whose_english_changed_stops_the_narrative(monkeypatch):
    english = case_text.current_english()
    case = next(iter(approvals.APPROVED_NARRATIVE))
    changed = {variant: dict(passages) for variant, passages in english.items()}
    path = next(iter(changed[case]))
    changed[case][path] = changed[case][path] + " (edited)"
    monkeypatch.setattr(case_text, "current_english", lambda: changed)
    assert any(problem.startswith(case) for problem in approvals.narrative_problems())


def _write(path, rows):
    path.write_text(json.dumps(rows) if not isinstance(rows, str) else rows, encoding="utf-8")
    return path


@pytest.mark.parametrize("kind", ["narrative", "rubric"])
def test_the_file_check_rejects_every_way_a_pack_can_go_wrong(kind, tmp_path):
    key = approvals.FIELDS[kind][0]
    good = approvals.pack(kind)
    cases = {
        "missing": good[1:],
        "duplicate": good + [good[0]],
        "stale": [{**good[0], "version": "f" * 64}] + good[1:],
        "not approved": [{**good[0], "decision": "changes_requested"}] + good[1:],
        "extra field": [{**good[0], "reviewer": "someone"}] + good[1:],
        "foreign": good + [{key: "trauma_hemothorax_41m" if kind == "narrative" else "D9",
                            "version": "a" * 64, "decision": "approved"}],
        "not a list": {"rows": good},
        "not JSON": "{not json",
        "not objects": ["approved"] * len(good),
    }
    for name, rows in cases.items():
        found = approvals.verify_file(kind, _write(tmp_path / f"{name}.json", rows))
        assert found, f"{name}: the check let it through"
    assert "does not exist" in approvals.verify_file(kind, tmp_path / "absent.json")[0]


def test_the_runtime_shows_nothing_on_a_stale_or_unapproved_row(tmp_path, monkeypatch):
    case = next(iter(approvals.APPROVED_NARRATIVE))
    rows = case_text.passages("es")[case]
    now = case_text.version(rows)
    (tmp_path / "es").mkdir()
    pack_file = tmp_path / "es" / "approvals.json"
    monkeypatch.setattr(case_text, "ROOT", tmp_path)
    for pack, expected in (
            ([{"variant_id": case, "version": "0" * 64, "decision": "approved"}], "pending"),
            ([{"variant_id": case, "version": now, "decision": "changes_requested"}], "pending"),
            ([{"variant_id": case, "version": now, "decision": "approved"}] * 2, "approved"),
            ([{"variant_id": case, "version": now, "decision": "approved"}], "approved")):
        _write(pack_file, pack)
        assert case_text.status(case, rows, {}, case_text.pack_approvals()) == expected, pack


def test_the_rubric_runtime_shows_nothing_on_a_stale_or_unapproved_row(tmp_path, monkeypatch):
    domain = next(iter(rubric.DOMAINS))
    rows = rubric_text.drafts()[domain]
    now = rubric_text.version(domain, rows)
    (tmp_path / "es").mkdir()
    (tmp_path / "es" / "descriptors.json").write_text(
        (rubric_text.ROOT / "es" / "descriptors.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(rubric_text, "ROOT", tmp_path)
    pack_file = tmp_path / "es" / "approvals.json"
    for pack, expected in (
            ([{"domain_id": domain, "version": "0" * 64, "decision": "approved"}], "pending"),
            ([{"domain_id": domain, "version": now, "decision": "changes_requested"}], "pending"),
            ([{"domain_id": domain, "version": now, "decision": "approved"}], "approved")):
        _write(pack_file, pack)
        assert rubric_text.status(domain, rows, {}, rubric_text.pack_approvals()) == expected, pack
