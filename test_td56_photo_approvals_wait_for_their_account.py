"""TD-56 (pre-pilot closure, 2026-10-02): a photo approval is recorded under its own account, or waits.

The pack's approvals name the staff account of the person who gave them. The faculty page opens
the image bank as soon as an administrator signs in -- before the approving faculty account can
exist, since it needs the administrator's invitation -- and the pack used to count as imported
then: every approved photograph stayed in the neutral view until a restart or a manual import.
Now an approval waits for its account, is never recorded under anybody else, and is recorded at
the first opening after that account exists. ``check_database.py --photo-approvals`` says which,
reading only, before any encounter opens.
"""
import json

import image_pack
from account_store import AccountStore, hash_password
from image_bank import ImageBank
from image_pricing import DEFAULT_BUDGET
from test_the_image_bank import ARRIVAL, Provider, bank, quick_retries, settle  # noqa: F401  (fixtures)

APPROVER = "approving_faculty"


def pack_with_approvals(bank, tmp_path, username=APPROVER):
    settle(bank, Provider(), ARRIVAL, person="V22")
    pack = tmp_path / "pack"
    image_pack.export_pack(bank, pack, budget=dict(DEFAULT_BUDGET))
    anchor = bank.current_anchor("V22")
    approvals = [{"id": f"approval-{field}", "asset_id": anchor["id"], "field": field, "value": "approved",
                  "username": username, "note": "Approved by the faculty, recorded by the agent.",
                  "created_at": 1790000000} for field in ("visual_review", "clinical_review")]
    (pack / image_pack.APPROVALS).write_text(json.dumps(approvals), encoding="utf-8")
    return pack, anchor


def pilot(tmp_path):
    """The pilot's database as the runbook leaves it at step 5: only its administrator."""
    url = f"sqlite:///{tmp_path / 'pilot.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    accounts.bootstrap_admin("pilot_admin", hash_password("pilot-only-admin-password"))
    return url, ImageBank(accounts), accounts.authenticate("pilot_admin", "pilot-only-admin-password")


def register(target, admin, username, role="faculty"):
    accounts = target.accounts
    accounts.register(username, f"{username}-only-password",
                      accounts.create_invite(admin, role, 1 if role == "resident" else None))


def test_an_approval_waits_for_its_account_and_is_recorded_once_it_exists(bank, tmp_path, monkeypatch):
    pack, anchor = pack_with_approvals(bank, tmp_path)
    _, target, admin = pilot(tmp_path)
    # The administrator signs in first, and the faculty page opens the bank.
    first = image_pack.ensure_imported(target, pack)
    assert first["assets"] > 0 and first["approvals"] == {"no_account": 2} and first["waiting_for"] == [APPROVER]
    assert target.asset(anchor["id"])["visual_review"] == "pending"
    assert image_pack.approval_status(target, pack)["waiting"] == {APPROVER: 2}

    # While the account is missing, an opening reads the staff accounts once and imports nothing.
    counted = []
    original = AccountStore._transaction

    def counting(self, write=False):
        counted.append(write)
        return original(self, write)

    with monkeypatch.context() as patch:
        patch.setattr(AccountStore, "_transaction", counting)
        assert image_pack.ensure_imported(target, pack) is None
    assert counted == [False]

    # The person who gave the approvals registers their own account under that username.
    register(target, admin, APPROVER)
    again = image_pack.ensure_imported(target, pack)
    assert again["approvals"] == {"added": 2} and again["waiting_for"] == [] and again["assets"] == 0
    asset = target.asset(anchor["id"])
    assert asset["visual_review"] == asset["clinical_review"] == "approved"
    status = image_pack.approval_status(target, pack)
    assert status["recorded"] == 2 and status["waiting"] == {} and status["elsewhere"] == 0
    assert status["holders"] == {APPROVER: "faculty"}
    # Imported now, for this process: one more opening costs nothing.
    assert image_pack.ensure_imported(target, pack) is None


def test_an_account_that_is_not_staff_never_receives_an_approval(bank, tmp_path):
    pack, anchor = pack_with_approvals(bank, tmp_path)
    _, target, admin = pilot(tmp_path)
    register(target, admin, APPROVER, role="resident")
    result = image_pack.ensure_imported(target, pack)
    assert result["approvals"] == {"no_account": 2} and result["waiting_for"] == [APPROVER]
    assert target.asset(anchor["id"])["clinical_review"] == "pending"
    status = image_pack.approval_status(target, pack)
    assert status["holders"] == {APPROVER: "resident"} and status["waiting"] == {APPROVER: 2}


def test_the_runbook_check_says_whether_the_order_held(bank, tmp_path, capsys):
    import check_database
    pack, _ = pack_with_approvals(bank, tmp_path)
    url, target, admin = pilot(tmp_path)
    image_pack.ensure_imported(target, pack)
    assert check_database.report_photo_approvals(url, pack) == 2
    said = capsys.readouterr().out
    assert f"2 wait for the staff account {APPROVER!r}" in said and "open no encounter" in said

    register(target, admin, APPROVER)
    # The account is there; nothing has opened the bank since, so nothing is recorded yet.
    assert check_database.report_photo_approvals(url, pack) == 2
    assert "have their account here and are not recorded yet" in capsys.readouterr().out

    image_pack.ensure_imported(target, pack)
    assert check_database.report_photo_approvals(url, pack) == 0
    said = capsys.readouterr().out
    assert "All 2 approvals are recorded under the accounts they name." in said
    assert f"account {APPROVER!r} is here, as faculty" in said


def test_the_repository_pack_names_one_staff_account_for_every_approval():
    """What the runbook asks for: one account, the approving faculty member's own, under this username."""
    approvals = image_pack.read_approvals()
    if not approvals:
        return
    assert len({entry["id"] for entry in approvals}) == len(approvals)
    assert len({entry["username"] for entry in approvals}) == 1
