"""P-07 (faculty, 2026-09-30): pulmonary_edema_75f arrives with the neutral view, and V34 stays.

Until an approved image adequately shows her respiratory distress, the room shows the neutral view and
the written examination on arrival. The faculty's clinical approval of V34 for this state goes back to
pending, recorded in the image pack under the account that decided it, beside the approvals it had;
nothing is deleted, the clinical state does not change and no image is generated. The pilot requires
both reviews (MRS_IMAGE_REQUIRE_REVIEW=on), so a pending photograph is never shown there.

The import runs on SQLite always, and on PostgreSQL when ``MRS_TEST_POSTGRES_URL`` names a throwaway
database (every run drops and recreates its public schema).
"""
import os

import pytest

import image_bank
import image_pack
import image_scene
from account_store import AccountStore
from image_bank import ImageBank
from image_selection import human_approved, usable
from test_the_image_bank import _faculty

V34 = "906790d456124104932a98e703780238"
FACULTY = "npinedafaculty"
URL = os.environ.get("MRS_TEST_POSTGRES_URL", "")


def _v34_entries():
    approvals = image_pack.read_approvals(image_pack.PACK_DIR)
    return [entry for entry in approvals if entry["asset_id"] == V34]


def test_the_pack_keeps_what_was_approved_and_adds_the_pending_decision_last():
    entries = _v34_entries()
    assert [(e["field"], e["value"]) for e in entries] == [
        ("visual_review", "approved"), ("clinical_review", "approved"), ("clinical_review", "pending")]
    decision = entries[-1]
    assert decision["username"] == FACULTY and decision["role"] == "state" and decision["identity_id"] == "V34"
    assert "P-07" in decision["note"] and "2026-09-30" in decision["note"]
    # Nothing was removed from the pack: the photograph and its earlier approvals stay.
    manifest = image_pack.read_manifest(image_pack.PACK_DIR)
    assert any(asset["id"] == V34 and not asset["excluded"] for asset in manifest["assets"])


def _bank(tmp_path, backend):
    if backend == "sqlite":
        return ImageBank(AccountStore(f"sqlite:///{tmp_path / 'p07.sqlite3'}", allow_sqlite=True))
    if not URL.startswith("postgres"):
        pytest.skip("MRS_TEST_POSTGRES_URL is not set")
    import psycopg
    with psycopg.connect(URL, autocommit=True) as connection:
        connection.execute("DROP SCHEMA public CASCADE")
        connection.execute("CREATE SCHEMA public")
    AccountStore.forget_schemas()
    image_bank.forget_cache()
    return ImageBank(AccountStore(URL))


@pytest.mark.parametrize("backend", ["sqlite", "postgres"])
def test_after_the_import_v34_is_usable_but_not_approved_so_the_pilot_shows_the_neutral_view(
        tmp_path, monkeypatch, backend):
    bank = _bank(tmp_path, backend)
    _faculty(bank.accounts, FACULTY)
    result = image_pack.import_pack(bank)
    assert result["assets"] > 0 and result["approvals"].get("added", 0) > 0
    asset = bank.asset(V34)
    assert asset["visual_review"] == "approved" and asset["clinical_review"] == "pending"
    assert not human_approved(asset)
    # Still a usable photograph: nothing asks for a new one, so nothing is generated or paid for.
    assert usable(asset)
    # The pilot's configuration requires both reviews, and a pending one is not shown (REVIEW_PENDING).
    monkeypatch.setenv("MRS_IMAGE_REQUIRE_REVIEW", "on")
    assert image_scene.review_required()
    # Every decision stays in the record, under the account that made it.
    with bank.accounts._transaction() as connection:
        rows = bank.accounts._execute(connection, """SELECT r.field, r.value, u.username FROM mrs_image_reviews r
            JOIN mrs_users u ON u.id = r.actor_id WHERE r.asset_id = ? ORDER BY r.created_at, r.id""",
            (V34,)).fetchall()
    assert [(row["field"], row["value"]) for row in rows] == [
        ("visual_review", "approved"), ("clinical_review", "approved"), ("clinical_review", "pending")]
    assert {row["username"] for row in rows} == {FACULTY}
    # A second import changes nothing: each decision is recorded once.
    again = image_pack.import_pack(bank)
    assert set(again["approvals"]) <= {"known", "no_account"}
    assert bank.asset(V34)["clinical_review"] == "pending"


def test_the_clinical_state_of_the_case_is_unchanged():
    import clinical_cases
    case = clinical_cases.variant_by_id("pulmonary_edema_75f")
    assert case["observable"]["spo2"] == 84 and case["observable"]["work_of_breathing"] == "Markedly increased"
    assert case["observable"]["respiratory_rate"] == 32
