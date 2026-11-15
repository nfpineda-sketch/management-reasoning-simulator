#!/usr/bin/env python3
"""UX-010 · Capture the stored review set of the FACULTY TRAJECTORY REVIEW. OPERATOR / DEVELOPMENT TOOL, never run by a reviewer.

It runs the seven scripted review encounters ONCE on the real page (``app.py``, Streamlit AppTest, individual accounts, the pressure authority under its registered grant -- exactly what the certified
review environment already does), takes each encounter's review bundle through the unchanged bundle layer, and freezes bundle + what the resident saw (arrival and the vital signs at each step) in
``docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json``. Nothing in physiology, authority, grant or snapshot is changed or re-derived: the output is only what the certified path already produces,
and every scenario is checked against the certified series (``PHASE3_PRESSURE_AUTHORITY_SERIES.json``) before it is written. A reviewer's session never runs this: it only reads the stored file.

    python3 faculty_review_kit/tools/capture_trajectory_review_set.py            # writes the set (refuses when a scenario does not match the certified series)
    python3 faculty_review_kit/tools/capture_trajectory_review_set.py --check    # re-captures into memory and compares with the stored set (drift detection); writes nothing
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

import faculty_trajectory_review as ftr  # noqa: E402
import runtime_faculty_bundle as bundles  # noqa: E402
import runtime_faculty_review as fr  # noqa: E402
import test_phase3_faculty_review_page as page  # noqa: E402  (the certified page helpers: environment, account, scripted drive)
from account_store import AccountStore, hash_password  # noqa: E402


def _map(sbp: float, dbp: float) -> int:
    return int(round((float(sbp) + 2 * float(dbp)) / 3))


def _capture_one(world: dict, scenario_id: str) -> dict:
    scenario = fr.scenario(scenario_id)
    at = page._open(world)
    page._begin(at, scenario_id)
    page._drive(at, scenario["steps"])
    panel = page._panel(at)
    if at.session_state.get(page.ui.BUNDLE_KEY) is None:
        next(button for button in panel.button if button.label == "Create review bundle").click().run()
    bundle = at.session_state[page.ui.BUNDLE_KEY]["bundle"]
    trace = list(at.session_state["management_trace"] or [])
    first = dict(dict(trace[0].get("state_before") or {}).get("observable") or {})
    arrival = {"sbp": first["sbp"], "dbp": first["dbp"], "map": _map(first["sbp"], first["dbp"]), "hr": first.get("hr"), "rr": first.get("respiratory_rate"), "spo2": first.get("spo2"), "crt": first.get("crt")}
    vitals, seen = [{"minute": 0, "hr": arrival["hr"], "rr": arrival["rr"], "spo2": arrival["spo2"], "crt": arrival["crt"]}], {0}
    for entry in trace:
        if entry.get("execution_status") != "executed":
            continue
        after = dict(entry.get("state_after") or {})
        minute, observed = int(after.get("sim_time_min")), dict(after.get("observable") or {})
        if minute in seen:
            continue
        seen.add(minute)
        vitals.append({"minute": minute, "hr": observed.get("hr"), "rr": observed.get("respiratory_rate"), "spo2": observed.get("spo2"), "crt": observed.get("crt")})
    spec = dict(at.session_state["state"].get("encounter_spec") or {})
    return {"scenario_id": scenario_id, "case_id": scenario["case_id"], "series": scenario["series"], "title": scenario["title"], "reason": scenario["reason"],
            "clinical_context": str(spec.get("presentation") or ""), "script": [list(step) for step in scenario["steps"]], "arrival": arrival, "context_vitals": vitals, "bundle": bundle}


def capture() -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="ftr_capture_"))
    url = "sqlite:///" + str(tmp / "accounts.sqlite3")
    accounts = AccountStore(url, allow_sqlite=True)
    accounts.bootstrap_admin(page.ADMIN[0], hash_password(page.ADMIN[1]))
    token = accounts.authenticate(*page.ADMIN)
    accounts.register(page.RESIDENT[0], page.RESIDENT[1], accounts.create_invite(token, "resident", 1))
    secrets = {"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url, "MRS_ALLOW_LOCAL_SQLITE": True, "MRS_ADMIN_USERNAME": page.ADMIN[0], "MRS_ADMIN_PASSWORD_HASH": hash_password(page.ADMIN[1])}
    items = []
    try:
        with pytest.MonkeyPatch.context() as patch:
            page._review_env(patch, tmp / "store")
            world = {"mp": patch, "tmp": tmp, "store": tmp / "store", "secrets": secrets, "accounts": accounts, "runs": {}, "creds": {}, "admin_token": token, "count": [0]}
            for scenario in fr.SCENARIOS:
                print(f"capturing {scenario['id']} ...", flush=True)
                items.append(_capture_one(world, scenario["id"]))
    finally:
        fr.release_for_tests()
    series = json.loads(ftr.SERIES_PATH.read_text(encoding="utf-8"))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    configuration = dict(items[0]["bundle"].get("faculty_review_configuration") or {})
    body = {"record_type": ftr.SET_TYPE, "version": ftr.VERSION,
            "what_it_is": ("The stored, certified trajectories of the seven scripted faculty review scenarios, captured once from the real page through the unchanged review bundle layer. The faculty trajectory review "
                           "reads this file; it never runs a physiology, an authority, a grant or an encounter."),
            "captured_from": {"git_head": head, "method": "REAL_PAGE_SCRIPTED_ENCOUNTERS_THROUGH_THE_UNCHANGED_BUNDLE_LAYER", "series_record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json",
                              "series_record_digest": series.get("record_digest"), "grant_id": configuration.get("grant_id"), "snapshot_id": items[0]["bundle"]["authority_view"].get("snapshot_id")},
            "items": items,
            "statement": "Synthetic development cases. Not a clinical validation, a resident pilot or a production record."}
    return {**body, "record_digest": ftr._digest(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="re-capture into memory and compare with the stored set; writes nothing")
    args = parser.parse_args()
    record = capture()
    series_runs = list(json.loads(ftr.SERIES_PATH.read_text(encoding="utf-8"))["runs"])
    failed = {item["scenario_id"]: ftr.item_problems(item, bundles=bundles, scenario_of=fr.scenario, series_runs=series_runs) for item in record["items"]}
    failed = {key: value for key, value in failed.items() if value}
    if failed:
        print("REFUSED: a captured scenario does not verify:", json.dumps(failed, indent=1))
        return 2
    if args.check:
        stored = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
        same = all(
            [dict(row)["authoritative_pressure_timeline"] for row in [dict(a["bundle"]["authority_view"])]] == [dict(row)["authoritative_pressure_timeline"] for row in [dict(b["bundle"]["authority_view"])]]
            and a["arrival"] == b["arrival"] and a["context_vitals"] == b["context_vitals"]
            and a["bundle"]["comparator"]["legacy_counterfactual_pressure_timeline"] == b["bundle"]["comparator"]["legacy_counterfactual_pressure_timeline"]
            for a, b in zip(record["items"], stored["items"]))
        print("DRIFT CHECK:", "the stored set reproduces (trajectories, comparator, arrival, vital signs)" if same and len(record["items"]) == len(stored["items"]) else "DIFFERS from the stored set")
        return 0 if same else 1
    ftr.SET_PATH.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {ftr.SET_PATH.relative_to(ROOT)}: {len(record['items'])} scenarios, digest {record['record_digest'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
