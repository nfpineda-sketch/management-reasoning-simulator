"""A proposed score is checked against the words and the minute it cites.

Score reproducibility, 2026-09-24. Replaying the same orders gives the same
record: the encounter is deterministic (see ``test_same_script_same_record``
below). Two readings of one record still differed -- one domain named the same
omission both times and scored it 3 and then 2. Nothing here chooses between
readings. It shows the reviewer where a score and its own anchor disagree:

* words quoted as the learner's that are not in the decision cited, or a
  quotation dated at a minute that is not that decision's;
* the maximum proposed while naming what the record lacks for the level;
* a level below the maximum that names nothing missing for the next one.

The marks change no proposal and no decision; they print where the other
marks already print.
"""
import json
from copy import deepcopy

import pytest

import rubric_screening
from rubric_presentation import record_check
from tools_rubric_runs import BY_ID, play_orders

SECOND = ("Creo que es una crisis asmatica severa, porque tiene sibilancias difusas, habla en frases "
          "cortas")


@pytest.fixture(scope="module")
def record():
    played, _ = play_orders(BY_ID["asthma_24f"])
    return played


def proposal(*rows, version="1.1"):
    return {"prompt_version": version, "proposal": {"domains": list(rows)}}


def domain(domain_id="D1", score=2, quote=SECOND, minute=2, ref="trace:1",
           gap="No contingency was stated for a failed first nebulisation."):
    row = {"domain_id": domain_id, "score": score, "evidence_refs": [ref],
           "learner_evidence": [{"evidence_ref": ref, "minute": minute, "quote": quote}],
           "rationale": "x", "contrary_evidence": "", "limits": ""}
    if gap is not None:
        row["next_level_gap"] = gap
    return row


def kinds(flags):
    return [flag["kind"] for flag in flags]


# --- the encounter is not where the variability comes from ---------------------

def test_same_script_same_record():
    first, _ = play_orders(BY_ID["opioid_67f"])
    second, _ = play_orders(BY_ID["opioid_67f"])
    canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    assert canonical(first) == canonical(second)


# --- quotations ---------------------------------------------------------------

def test_a_verbatim_quote_however_it_is_transcribed_raises_nothing(record):
    for quote in (SECOND, SECOND.upper(), "  creo que es una crisis asmática severa, porque tiene "
                                          "sibilancias difusas  ",
                  "“Creo que es una crisis asmatica severa”"):
        assert rubric_screening.anchor_flags(proposal(domain(quote=quote)), record) == []


def test_an_ellipsis_may_skip_words_but_not_reorder_them(record):
    ok = "Creo que es una crisis asmatica severa ... Doy salbutamol 5 mg nebulizado"
    assert rubric_screening.anchor_flags(proposal(domain(quote=ok)), record) == []
    backwards = "Doy salbutamol 5 mg nebulizado ... Creo que es una crisis asmatica severa"
    assert kinds(rubric_screening.anchor_flags(proposal(domain(quote=backwards)), record)) == [
        "domain_quote_not_in_record"]


@pytest.mark.parametrize("quote", [
    "I think this is a severe asthma attack",                   # a translation
    "Creo que es un asma grave, con sibilancias",               # a paraphrase
    "Doy hidrocortisona 200 mg ev",                             # another decision's words
])
def test_words_that_are_not_in_the_decision_cited_are_marked(record, quote):
    [flag] = rubric_screening.anchor_flags(proposal(domain(quote=quote)), record)
    assert flag["kind"] == "domain_quote_not_in_record" and flag["domain_id"] == "D1"
    assert flag["quote"] == quote and flag["refs"] == ["trace:1"]
    assert flag["facts"][0]["en"] == "Quoted from decision D2 at 2 min; those words are not in it."
    assert flag["facts"][0]["es"] == "Citado de la decisión D2, a los 2 min; esas palabras no están en ella."


def test_a_quotation_dated_at_another_minute_is_marked(record):
    assert rubric_screening.anchor_flags(proposal(domain(minute=17)), record) == []  # its response
    [flag] = rubric_screening.anchor_flags(proposal(domain(minute=40)), record)
    assert flag["kind"] == "domain_quote_minute_mismatch"
    assert flag["facts"][0]["en"] == "Dated 40 min; it is from decision D2 at 2 min."


def test_a_quotation_from_the_reflection_is_checked_against_the_reflection(record):
    row = domain(quote="Una caida de la saturacion o un torax silencioso me habrian hecho escalar",
                 ref="reflection:decision_1", minute=0)
    assert rubric_screening.anchor_flags(proposal(row), record) == []
    row["learner_evidence"][0]["quote"] = "Habria pedido ayuda antes"
    assert kinds(rubric_screening.anchor_flags(proposal(row), record)) == ["domain_quote_not_in_record"]


# --- the level and what it says is missing ------------------------------------

@pytest.mark.parametrize("score,gap,expected", [
    (3, "maximum level reached", []),
    (3, "Maximum level reached.", []),
    (3, "Nivel máximo alcanzado", []),
    (3, "No contingency was stated.", ["domain_gap_at_maximum"]),
    (2, "No contingency was stated.", []),
    (2, "", ["domain_gap_missing"]),
    (2, "maximum level reached", ["domain_gap_missing"]),
    (0, "   ", ["domain_gap_missing"]),
    ("not_assessable", "", []),
])
def test_a_level_names_what_the_next_one_needs(record, score, gap, expected):
    flags = rubric_screening.anchor_flags(proposal(domain(score=score, gap=gap)), record)
    assert kinds(flags) == expected


def test_a_proposal_written_before_the_gap_existed_is_not_marked_for_it(record):
    legacy = proposal(domain(score=2, gap=None), version="1.0")
    assert rubric_screening.anchor_flags(legacy, record) == []


# --- where the marks are read ---------------------------------------------------

def test_the_marks_reach_the_reviewer_in_their_language(record):
    body = proposal(domain(quote="I think this is a severe asthma attack"),
                    domain("D2", score=3, gap="No trend was documented."))
    for language, label in (("en", "The words quoted as the learner's are not in the decision cited"),
                            ("es", "Las palabras citadas como del residente no están en la decisión citada")):
        check = record_check(body, record, language)
        marks = [flag for flag in check["flags"] if flag["kind"].startswith("domain_")]
        assert [flag["kind"] for flag in marks] == ["domain_quote_not_in_record", "domain_gap_at_maximum"]
        assert marks[0]["label"] == label
        assert all(isinstance(fact, str) for fact in marks[0]["facts"])


def test_the_marks_print_in_the_rubric_document(record):
    from rubric_report import render_rubric_report_pdf
    from test_rubric_reports import review, text_of
    body = proposal(domain(quote="I think this is a severe asthma attack"))
    reviewed = review()
    reviewed["case_id"] = "asthma_24f"
    for language, words in (("en", "The words quoted as the learner's are not in the decision cited"),
                            ("es", "Las palabras citadas como del residente no están en la decisión")):
        text = text_of(render_rubric_report_pdf(reviewed, body, record, language=language))
        assert words in text, text[:600]


def test_the_resident_s_copy_carries_no_mark_addressed_to_the_faculty(record):
    from rubric_report import render_rubric_report_pdf
    from test_rubric_reports import review, text_of
    body = proposal(domain(quote="I think this is a severe asthma attack"))
    reviewed = review()
    reviewed["case_id"] = "asthma_24f"
    for language, words in (("en", "CHECK BEFORE DECIDING"), ("es", "REVISAR ANTES DE DECIDIR")):
        faculty = text_of(render_rubric_report_pdf(reviewed, body, record, language=language))
        learner = text_of(render_rubric_report_pdf(reviewed, body, record, language=language,
                                                   audience="learner"))
        assert words in faculty and words not in learner


def test_the_marks_change_nothing_they_point_at(record):
    body = proposal(domain(quote="I think this is a severe asthma attack", score=3, gap="x"))
    before = deepcopy(body)
    rubric_screening.anchor_flags(body, record)
    record_check(body, record)
    assert body == before
