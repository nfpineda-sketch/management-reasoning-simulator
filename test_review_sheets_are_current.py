"""The faculty review sheets are what the code says today (cycle 10, C10-02).

docs/revision/ is written by tools_review_sheets.py; a sheet that lags behind the code would ask
the faculty to sign something the residents no longer see.
"""
import tools_review_sheets as sheets


def test_the_sheets_on_disk_are_the_ones_the_code_writes():
    for path, text in sheets.sheets().items():
        assert path.read_text(encoding="utf-8") == text, f"run: python3 tools_review_sheets.py ({path.name})"


def test_every_row_waits_for_a_signature_and_nothing_is_approved():
    written = sheets.sheets()
    assert written[sheets.DC9_SHEET].count(sheets.REVIEW_LINE) == 36
    assert written[sheets.TD04_SHEET].count(sheets.REVIEW_LINE) == 14
    # R-4: one signature for the engine's sentences and one per bank case for C14.
    assert written[sheets.SPANISH_SHEET].count(sheets.REVIEW_LINE) == 1 + 31
    # R-2 (2026-09-30): each C14 YES case waits for its own decision; the 18 sentences come first in R-4.
    assert written[sheets.R2_SHEET].count(sheets.R2_REVIEW_LINE) == 14
    assert written[sheets.R4_ENGINE_SHEET].count(sheets.REVIEW_LINE) == 1
    assert written[sheets.R4_ENGINE_SHEET].count("☐ Apruebo · ☐ Cambio") == 18
    for text in written.values():
        assert "no aprueba" in text


def test_a_flag_points_at_the_origin_glucose_a_composition_does_not_have():
    origin = {"id": "hypoglycemia_28m", "conditions": {"arrival_glucose": 34, "iv_access_failed": False,
                                                       "sulfonylurea_effect": False}}
    composition = {"conditions": {"arrival_glucose": 52, "iv_access_failed": False, "sulfonylurea_effect": False}}
    row = {"rationale": "Impaired consciousness with a glucose of 34 mg/dL; after 20 min below 40 mg/dL a seizure."}
    flags = sheets.composition_flags(composition, origin, "TD1", row)
    assert flags == ["El texto cita 34 mg/dL, la glucosa de llegada de `hypoglycemia_28m`; esta composición "
                     "llega con 52 mg/dL."]
    same = {"conditions": dict(origin["conditions"])}
    assert sheets.composition_flags(same, origin, "TD1", row) == []
