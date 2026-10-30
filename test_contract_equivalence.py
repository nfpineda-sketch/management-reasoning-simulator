"""Phase 1 WP0: the frozen pilot's contract behavior is unchanged."""
from contextlib import contextmanager
from copy import deepcopy
import os

import tools_contract_baseline as contracts


@contextmanager
def environment_restored():
    """The order-reading rehearsal turns MRS_OFFLINE_CASES on and leaves it on
    (tools_order_reading.play). Give the environment back, so later tests in the
    same process do not run offline without asking."""
    saved = dict(os.environ)
    try:
        yield
    finally:
        for name in set(os.environ) - set(saved):
            del os.environ[name]
        os.environ.update(saved)


def test_first_difference_names_case_turn_and_field():
    baseline = {
        "acceptance": {
            "case_x": {
                "turns": [{"time": {"after_min": 15}}]
            }
        }
    }
    changed = deepcopy(baseline)
    changed["acceptance"]["case_x"]["turns"][0]["time"]["after_min"] = 16
    diff = contracts.first_difference(baseline, changed)
    assert diff
    path, expected, actual = diff
    assert path == "$.acceptance.case_x.turns[0].time.after_min"
    assert (expected, actual) == (15, 16)


def test_contract_equivalence():
    assert contracts.BASELINE.exists(), (
        f"WP0 baseline is missing: run `python {contracts.ROOT / 'tools_contract_baseline.py'} --write` first"
    )
    before = dict(os.environ)
    with environment_restored():
        assert contracts.check_baseline() == 0
    assert dict(os.environ) == before


def test_order_reading_rehearsal_leaves_the_environment_as_it_found_it(tmp_path, monkeypatch):
    import tools_order_reading

    monkeypatch.delenv("MRS_OFFLINE_CASES", raising=False)
    before = dict(os.environ)
    with environment_restored():
        tools_order_reading.play("es", [1], tmp_path, contracts.ORDER_READING_SEED)
        assert os.environ["MRS_OFFLINE_CASES"] == "1"
    assert dict(os.environ) == before

def test_contract_comparison_normalizes_only_the_commit_version():
    left = {"versions": {"code_version": "aaaaaaaaaaaa", "ledger_schema": "order_ledger_v1"}}
    right = {"versions": {"code_version": "bbbbbbbbbbbb", "ledger_schema": "order_ledger_v1"}}
    assert contracts.contract_difference(left, right) is None
    right["versions"]["ledger_schema"] = "changed"
    diff = contracts.contract_difference(left, right)
    assert diff and diff[0] == "$.versions.ledger_schema"

