"""The image bank on PostgreSQL, the engine of the development and public databases.

Runs only when ``MRS_TEST_POSTGRES_URL`` names a throwaway database: every test
drops and recreates its public schema. Without it these tests are skipped, and
the SQLite tests in ``test_the_image_bank`` still run.
"""
import os
import threading
import uuid

import pytest

import image_bank
import image_broker
from account_store import AccountStore, hash_password
from image_bank import BudgetRefused, ImageBank
from image_pricing import DEFAULT_BUDGET, MICRO
from test_the_image_bank import ARRIVAL, MASKED, Provider, ask, settle

URL = os.environ.get("MRS_TEST_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgres"), reason="MRS_TEST_POSTGRES_URL is not set")


@pytest.fixture
def bank():
    import psycopg
    with psycopg.connect(URL, autocommit=True) as connection:
        connection.execute("DROP SCHEMA public CASCADE")
        connection.execute("CREATE SCHEMA public")
    AccountStore.forget_schemas()
    image_bank.forget_cache()
    image_broker.wait(30)
    yield ImageBank(AccountStore(URL))
    image_broker.wait(30)


@pytest.fixture(autouse=True)
def quick_retries(monkeypatch):
    monkeypatch.setattr(image_broker, "RETRY_PAUSE_SECONDS", 0.0)


def test_the_whole_first_request_runs_on_postgres(bank):
    provider = Provider()
    _, ready = settle(bank, provider, ARRIVAL)
    assert ready.state == "ready"
    assert provider.kinds() == ["create", "screen", "edit", "screen"]
    assert bank.blob(ready.asset["display_sha256"]).startswith(b"RIFF")
    _, masked = settle(bank, provider, MASKED)
    assert masked.asset["reference_asset_id"] == bank.usable_asset("V27", image_broker.ANCHOR_KEY)["id"]


def test_a_restart_on_postgres_keeps_images_and_budget(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    spent = bank.budget_summary(dict(DEFAULT_BUDGET))
    calls = len(provider.calls)
    AccountStore.forget_schemas()
    image_bank.forget_cache()
    reopened = ImageBank(AccountStore(URL))
    assert ask(reopened, provider, ARRIVAL).state == "ready"
    assert len(provider.calls) == calls
    assert reopened.budget_summary(dict(DEFAULT_BUDGET)) == spent


def test_concurrent_reservations_on_postgres_never_pass_the_limit(bank):
    ceiling = image_broker.ceiling("gpt-image-1.5", "edit")
    budget = {"id": "pg-race", "limit_micro": 3 * ceiling, "limit_requests": 30, "authorization": "test"}
    bank.ensure_budget(budget)
    results = []

    def reserve():
        try:
            results.append(bank.reserve(budget, [("edit", "gpt-image-1.5", ceiling, True, None)],
                                        job_id=uuid.uuid4().hex, identity_id="V27", state_key="k",
                                        requested_by="race"))
        except BudgetRefused as refusal:
            results.append(refusal.reason)

    threads = [threading.Thread(target=reserve) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(1 for result in results if isinstance(result, list)) == 3
    assert results.count("dollars") == 5
    assert bank.budget_summary(budget)["committed"] == 3 * ceiling


def test_encounter_records_on_postgres(bank):
    accounts = bank.accounts
    accounts.bootstrap_admin("pg_admin", hash_password("pg-only-admin-password"))
    admin = accounts.authenticate("pg_admin", "pg-only-admin-password")
    code = accounts.create_invite(admin, "resident", 2)
    token = accounts.register("pg_resident", "pg-only-resident-password", code)
    attempt = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic"})
    first = bank.assign(token, attempt, identity_id="V27", family="hypoglycemia", case_id="hypoglycemia_76f",
                        repeat_kind="none", selection={"reason": "unseen"})
    again = bank.assign(token, attempt, identity_id="V12", family="hypoglycemia", case_id="hypoglycemia_76f",
                        repeat_kind="none", selection={})
    assert again["identity_id"] == first["identity_id"] == "V27"
    bank.log_display(token, attempt, identity_id="V27", contract=ARRIVAL, outcome="pending", sim_time=0)
    bank.log_display(token, attempt, identity_id="V27", contract=ARRIVAL, outcome="image", asset_id="a1",
                     limitations=["mild_skin_moisture"], sim_time=0)
    shown = bank.displays(admin, attempt)
    assert [row["outcome"] for row in shown] == ["pending", "image"]
    assert shown[1]["limitations"] == ["mild_skin_moisture"]
    user = accounts._user_for_token(token) if hasattr(accounts, "_user_for_token") else None
    exposures = bank.exposures(first["user_id"])
    assert set(exposures) == {"V27"} and exposures["V27"]["encounters"] == 1
    assert bank.usage() == {"V27": {"total": 1, "families": {"hypoglycemia": 1}}}
