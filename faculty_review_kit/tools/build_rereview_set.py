#!/usr/bin/env python3
"""P3-351 · Build the stored review set of the FACULTY TRAJECTORY RE-REVIEW. OPERATOR / DEVELOPMENT TOOL, never run by a reviewer.

It does NOT run an encounter, an authority or a physiology. It reads three files that are already certified and pinned -- the candidate review set (the certified static kit's source), the first review's set
(only for the two marker flags of each timeline row) and the blind key (only for its digest) -- and writes the first set of the candidate review set, unchanged, in the shape the review page draws, to
``docs/revision/PHASE3_JOINT_REGION_V1_FACULTY_REREVIEW_SET.json``.

    python3 faculty_review_kit/tools/build_rereview_set.py            # writes the set and prints its digest (pin it in faculty_trajectory_rereview.PINNED_SET_DIGEST)
    python3 faculty_review_kit/tools/build_rereview_set.py --check    # rebuilds into memory and compares with the stored set; writes nothing
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import faculty_trajectory_review as ftr  # noqa: E402
import faculty_trajectory_rereview as rr  # noqa: E402


def build() -> dict:
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))  # noqa: E731
    return rr.build_set(load(rr.CANDIDATE_SET_PATH), load(ftr.SET_PATH), load(rr.BLIND_KEY_PATH))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="rebuild into memory and compare with the stored set; writes nothing")
    args = parser.parse_args()
    record = build()
    if args.check:
        stored = json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
        same = stored == json.loads(json.dumps(record))
        print("CHECK:", "the stored re-review set is what the certified sources produce" if same else "DIFFERS from what the certified sources produce")
        return 0 if same else 1
    rr.SET_PATH.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {rr.SET_PATH.relative_to(ROOT)}: {len(record['items'])} scenarios, digest {record['record_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
