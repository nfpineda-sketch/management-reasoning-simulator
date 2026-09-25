"""Technical preservation of the three hypoglycaemia cases while their code is reorganised.

Captured on 2026-09-25 from commit d184845, before the configuration catalogue
existed: each case as the bank builds it, its evaluation declaration, its
launched state, and twenty structured-action scripts run on the real engine.
``test_hypoglycemia_preservation`` compares the code of today against that
record.

**Regression, not acceptance.** A match shows that reorganising the code did
not change a trajectory or a declaration by accident. It says nothing about
whether the trajectory is clinically right: the same test would pass on a
behaviour nobody ever reviewed. Clinical acceptance is a separate check, with
criteria of its own (``hypoglycemia_battery``), and several of today's
parameters are still pending faculty review
(``docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md``).

A difference that is *intended* is not hidden: it has to be named in the
corrections registry (``corrections_registry``), with its reason and its
tests, and the preservation test accepts exactly the differences listed there
and nothing else.

Regenerate the record only on purpose: ``python hypoglycemia_preservation.py --write``.
"""
import json
from pathlib import Path

import catalog_trajectories as trajectories

GOLDEN_PATH = Path(__file__).resolve().parent / "test_data" / "hypoglycemia_preservation_2026-09-25.json"
FAMILY = "hypoglycemia"
VARIANTS = ("hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine")

GLUCOSE = {"type": "diagnostic", "diagnostic": "poc_glucose"}
LINE = {"type": "vascular_access", "operation": "start"}
DEXTROSE_IV = {"type": "dextrose", "dose_g": 25.0, "route": "IV"}
DOUBLE_DEXTROSE_IV = {"type": "dextrose", "dose_g": 50.0, "route": "IV"}
DEXTROSE_IO = {"type": "dextrose", "dose_g": 25.0, "route": "IO"}
DEXTROSE_PO = {"type": "dextrose", "dose_g": 15.0, "route": "PO"}
GLUCAGON_IM = {"type": "glucagon", "agent": "glucagon", "dose_mg": 1.0, "route": "IM"}
GLUCAGON_IV = {"type": "glucagon", "agent": "glucagon", "dose_mg": 1.0, "route": "IV"}
INFUSION = {"type": "dextrose_infusion", "rate_ml_h": 100.0, "concentration_percent": 10, "operation": "start"}
OCTREOTIDE_SC = {"type": "octreotide", "agent": "octreotide", "dose_mg": 0.05, "route": "SC"}
OCTREOTIDE_IV = {"type": "octreotide", "agent": "octreotide", "dose_mg": 0.05, "route": "IV"}
THIAMINE_IV = {"type": "thiamine", "agent": "thiamine", "dose_mg": 100.0, "route": "IV"}
ORAL = {"type": "oral_carbohydrate"}
HOME = {"type": "disposition", "destination": "home"}
WARD = {"type": "disposition", "destination": "ward"}
OBSERVATION = {"type": "disposition", "destination": "ED observation", "duration_h": 6.0}
NEUROLOGICAL = {"type": "examination", "region": "Neurological"}
PERFUSION = {"type": "examination", "region": "Peripheral perfusion"}


def wait(minutes):
    return {"type": "reassessment", "delay_min": minutes}


SCRIPTS = {
    "untreated": [[GLUCOSE], [wait(30)], [wait(30)], [wait(30)]],
    "existing_line_dextrose": [[GLUCOSE], [DEXTROSE_IV, wait(10)], [GLUCOSE], [wait(30)], [GLUCOSE],
                               [wait(60)], [GLUCOSE]],
    "new_line_then_dextrose": [[LINE, DEXTROSE_IV, wait(10)], [GLUCOSE], [wait(30)], [GLUCOSE]],
    "glucagon_im": [[GLUCAGON_IM, wait(15)], [GLUCOSE], [GLUCAGON_IM, wait(20)], [GLUCOSE], [wait(30)]],
    "glucagon_iv_existing_line": [[GLUCAGON_IV, wait(15)], [GLUCOSE], [wait(15)]],
    "double_ampoule": [[LINE, DOUBLE_DEXTROSE_IV, wait(10)], [GLUCOSE], [wait(40)], [GLUCOSE], [wait(30)],
                       [GLUCOSE]],
    "infusion_after_ampoule": [[LINE, DEXTROSE_IV, INFUSION, wait(15)], [GLUCOSE], [wait(60)], [GLUCOSE],
                               [wait(60)], [GLUCOSE]],
    "infusion_existing_line": [[INFUSION, wait(30)], [GLUCOSE], [wait(30)], [GLUCOSE]],
    "octreotide_sc": [[LINE, DEXTROSE_IV, OCTREOTIDE_SC, wait(20)], [GLUCOSE], [wait(60)], [GLUCOSE],
                      [wait(120)], [GLUCOSE]],
    "octreotide_iv_existing_line": [[DEXTROSE_IV, OCTREOTIDE_IV, wait(20)], [GLUCOSE], [wait(60)], [GLUCOSE]],
    "thiamine_then_dextrose": [[THIAMINE_IV, DEXTROSE_IV, wait(10)], [GLUCOSE], [NEUROLOGICAL], [wait(30)]],
    "intraosseous_dextrose": [[DEXTROSE_IO, wait(10)], [GLUCOSE]],
    "oral_after_recovery": [[LINE, DEXTROSE_IV, wait(10)], [GLUCOSE], [ORAL, wait(30)], [GLUCOSE]],
    "early_discharge": [[LINE, DEXTROSE_IV, wait(15)], [GLUCOSE], [HOME, wait(60)], [wait(60)], [wait(60)]],
    "admission": [[LINE, DEXTROSE_IV, INFUSION, wait(15)], [GLUCOSE], [WARD, wait(60)]],
    "ed_observation": [[LINE, DEXTROSE_IV, wait(15)], [GLUCOSE], [OBSERVATION, wait(120)], [wait(120)]],
    "examinations": [[NEUROLOGICAL, PERFUSION], [wait(5)]],
    "oral_while_not_alert": [[ORAL]],
    "oral_dextrose_while_not_alert": [[DEXTROSE_PO]],
    "failed_line_then_new_line": [[DEXTROSE_IV, wait(10)], [GLUCOSE], [LINE, DEXTROSE_IV, wait(10)], [GLUCOSE]],
}


def _plain(value):
    """JSON-shaped: tuples become lists, so a comparison is not about container types."""
    return json.loads(trajectories.canonical(value))


def capture(variants=VARIANTS):
    """Everything the preservation test compares, from the code as it is now."""
    from case_assessment_bank import CASES
    from clinical_cases import variant_by_id
    record = {}
    for variant_id in variants:
        state = trajectories.launch(variant_id, FAMILY)
        scripts = {}
        for name, script in SCRIPTS.items():
            rows = trajectories.run(trajectories.launch(variant_id, FAMILY), script)
            scripts[name] = [{"fingerprint": trajectories.digest({"result": row["result"], "state": row["state"]}),
                              "readable": trajectories.readable(row)} for row in rows]
        record[variant_id] = {
            "variant": _plain(variant_by_id(variant_id)),
            "declaration": _plain(CASES[variant_id]),
            "launch": {"moving": trajectories.digest(trajectories.moving_state(state)),
                       "observable": _plain(state["observable"])},
            "scripts": scripts,
        }
    return record


def load_golden():
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="overwrite the recorded golden file")
    args = parser.parse_args(argv)
    captured = capture()
    if not args.write:
        print(json.dumps({key: len(value["scripts"]) for key, value in captured.items()}))
        return 0
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(json.dumps({"captured_from": "d184845", "captured_on": "2026-09-25",
                                       "variants": captured}, sort_keys=True, indent=1,
                                      ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"written {GOLDEN_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
