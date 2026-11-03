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



def test_order_reading_snapshot_leaves_offline_mode_as_it_found_it(monkeypatch):
    # play() used to set MRS_OFFLINE_CASES and keep it, so every later test in the
    # same process ran offline (test_tools_image_bank failed after this file).
    import tools_order_reading as reading
    import tools_tanda20

    seen = []

    def rehearse(script, folder, seed):
        seen.append(reading.os.environ.get("MRS_OFFLINE_CASES"))
        return {"stopped": False, "seconds": 0, "steps": []}

    monkeypatch.setattr(tools_tanda20, "_scripts",
                        lambda language: ({n: {"case_id": f"case-{n}", "steps": []} for n in range(1, 21)}, None))
    monkeypatch.setattr(tools_tanda20, "rehearse", rehearse)
    monkeypatch.setattr(reading, "stored_encounter", lambda database: {})
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    # setenv first so monkeypatch records the original state and restores it even if this fails.
    monkeypatch.setenv("MRS_OFFLINE_CASES", "placeholder")

    monkeypatch.delenv("MRS_OFFLINE_CASES")
    contracts.order_reading_snapshot()
    assert "MRS_OFFLINE_CASES" not in reading.os.environ

    monkeypatch.setenv("MRS_OFFLINE_CASES", "0")
    contracts.order_reading_snapshot()
    assert reading.os.environ.get("MRS_OFFLINE_CASES") == "0"

    assert seen == ["1"] * 80
