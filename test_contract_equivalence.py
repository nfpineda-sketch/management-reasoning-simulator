"""Phase 1 WP0: the frozen pilot's contract behavior is unchanged."""
from copy import deepcopy

import tools_contract_baseline as contracts


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
    assert contracts.check_baseline() == 0

def test_contract_comparison_normalizes_only_the_commit_version():
    left = {"versions": {"code_version": "aaaaaaaaaaaa", "ledger_schema": "order_ledger_v1"}}
    right = {"versions": {"code_version": "bbbbbbbbbbbb", "ledger_schema": "order_ledger_v1"}}
    assert contracts.contract_difference(left, right) is None
    right["versions"]["ledger_schema"] = "changed"
    diff = contracts.contract_difference(left, right)
    assert diff and diff[0] == "$.versions.ledger_schema"

