#!/usr/bin/env python3
"""Phase 1 WP0: deterministic contract baseline and equivalence harness.

Observational only: no simulator runtime changes.

Usage:
    python tools_contract_baseline.py --write
    python tools_contract_baseline.py --check
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

BASE_SHA = "49ee2267c40550ef263fd8a99724eb991d29c5a6"
BASE_SHORT = BASE_SHA[:8]
ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "test_data" / f"contracts_baseline_{BASE_SHORT}.json"
SCHEMA = "contracts_baseline_v1"
ORDER_READING_SEED = 3000

NORMALIZATION = [
    "Acceptance submissions use pilot_acceptance's deterministic tN ids; no random submission id is recorded.",
    "Order-reading uses tools_order_reading.compact_entry, which omits account/session/attempt ids and wall-clock timestamps.",
    "Rehearsal wall-clock duration ('seconds') is omitted.",
    "JSON object keys are sorted; list order is preserved because it is behavioral.",
    "Trace code_version is normalized at comparison time because every later Phase-1 commit has a new SHA.",
]

GAPS = [
    (
        "pilot_acceptance is an engine-level battery and does not construct the full app Management Trace. "
        "WP0 records its Phase-0-equivalent turn fields (orders, events, observations, limitations, versions). "
        "The real-page Trace is additionally exercised by the bilingual tools_order_reading rehearsal and the "
        "existing test_phase0_acceptance_page.py; no runtime change was made merely to expose more state."
    ),
    (
        "The acceptance battery's authored management scripts are English canonical inputs. Bilingual reader "
        "equivalence is measured separately by the existing 20-script Spanish/English tools_order_reading rehearsal. "
        "WP0 does not invent a new Spanish translation corpus."
    ),
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _runtime_diff() -> list[str]:
    out = _git("diff", "--name-only", BASE_SHA, "--", ".").splitlines()
    allowed = {
        "CLAUDE.md",
        "tools_contract_baseline.py",
        "test_contract_equivalence.py",
    }
    return [
        path for path in out
        if path
        and path not in allowed
        and not path.startswith("docs/")
        and not path.startswith("test_data/contracts_baseline_")
    ]


def _assert_runtime_clean(*, mutation_probe=False):
    changed = _runtime_diff()
    if changed and not mutation_probe:
        raise RuntimeError(
            "WP0 STOP: runtime or existing-test files differ from the frozen pilot before baseline capture: "
            + ", ".join(changed)
        )
    if changed and mutation_probe:
        print("MUTATION PROBE: allowing deliberate runtime diff: " + ", ".join(changed), flush=True)


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def _json_bytes(payload) -> bytes:
    return (json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _present_findings(state, variant):
    import case_text
    import family_engine
    import language

    language.set_narrative({})
    language.narrate(None)
    case_text._INSTALLED.clear()
    case_text.install(None, now=0)

    findings = family_engine.current_findings(state)
    shown = {}
    with language.narrating(variant):
        for code in ("en", "es"):
            shown[code] = {
                region: language.say(str(text), code)
                for region, text in sorted(findings.items())
            }
    return shown


@contextmanager
def _capture_acceptance_turns():
    import family_engine
    import order_ledger
    import pilot_acceptance as acceptance
    import trace_phase0

    original_order = acceptance.Encounter.order
    original_engine = family_engine.execute_family_bundle
    active = {"encounter": None}
    run_counters: dict[str, int] = {}
    turns: dict[str, list[dict]] = {}

    def engine_wrapper(state, parsed):
        encounter = active["encounter"]
        if encounter is not None:
            encounter._wp0_engine_calls.append({
                "actions": [
                    order_ledger.strip_tags(deepcopy(action))
                    for action in (parsed or {}).get("actions", [])
                    if isinstance(action, dict)
                ],
                "bundle_fields": {
                    key: deepcopy(value)
                    for key, value in (parsed or {}).items()
                    if key != "actions" and not str(key).startswith("_")
                },
            })
        return original_engine(state, parsed)

    def order_wrapper(self, text):
        if not hasattr(self, "_wp0_run_id"):
            number = run_counters.get(self.variant, 0) + 1
            run_counters[self.variant] = number
            self._wp0_run_id = number
            self._wp0_turn_id = 0
        self._wp0_turn_id += 1
        self._wp0_engine_calls = []
        active["encounter"] = self
        try:
            entry = original_order(self, text)
        finally:
            active["encounter"] = None

        orders = deepcopy(entry.get("orders") or [])
        turn = {
            "run": self._wp0_run_id,
            "turn": self._wp0_turn_id,
            "input": str(text),
            "engine_calls": deepcopy(self._wp0_engine_calls),
            "orders": orders,
            "fates": [
                {
                    "order_id": order.get("order_id"),
                    "class": order.get("class"),
                    "fate": order.get("fate"),
                    "reason": order.get("reason"),
                    "receipt": order.get("receipt"),
                }
                for order in orders
            ],
            "receipt_lines": order_ledger.receipt_lines(orders),
            "time": {
                "before_min": entry.get("decision_time_min"),
                "after_min": entry.get("response_time_min"),
                "interrupted": deepcopy(entry.get("interrupted")),
            },
            "events": deepcopy(entry.get("events") or []),
            "observation_snapshot": deepcopy(entry.get("observation_snapshot") or {}),
            "current_findings": _present_findings(self.state, self.variant),
            "trace_fields": {
                "executed": bool(entry.get("executed")),
                "terminal_locked": bool(entry.get("terminal_locked")),
                "clarification": deepcopy(entry.get("clarification")),
                "limitations": deepcopy(entry.get("limitations") or []),
                "action_summaries": deepcopy(entry.get("action_summaries") or []),
                "ledger_problems": deepcopy(entry.get("ledger_problems") or []),
                "inconsistencies": deepcopy(entry.get("inconsistencies") or []),
                "versions": trace_phase0.versions(self.state),
            },
        }
        turns.setdefault(self.variant, []).append(turn)
        return entry

    acceptance.Encounter.order = order_wrapper
    family_engine.execute_family_bundle = engine_wrapper
    try:
        yield turns
    finally:
        acceptance.Encounter.order = original_order
        family_engine.execute_family_bundle = original_engine


def acceptance_snapshot():
    import pilot_acceptance as acceptance
    import pilot_freeze

    accepted = list(pilot_freeze.accepted_variants())
    results = {}
    with _capture_acceptance_turns() as turns:
        for index, variant in enumerate(accepted, 1):
            acceptance.battery.cache_clear()
            result = acceptance.battery(variant)
            if not all(item.get("ok") for item in result.values()):
                failed = [name for name, item in result.items() if not item.get("ok")]
                raise RuntimeError(f"{variant}: acceptance battery failed before baseline capture: {failed}")
            results[variant] = {
                "battery": deepcopy(result),
                "turns": turns.get(variant, []),
            }
            print(f"acceptance {index:>2}/{len(accepted)} {variant}: {len(results[variant]['turns'])} turns",
                  flush=True)
    return results


def _stable_rehearsal_result(run):
    result = deepcopy(run.get("result") or {})
    result.pop("seconds", None)
    return {
        "result": result,
        "stored": deepcopy(run.get("stored") or {}),
    }


def order_reading_snapshot():
    import tools_order_reading as reading

    if {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"} & set(os.environ):
        raise RuntimeError(
            "Provider key visible in the environment. WP0 order-reading must run offline; unset it and retry."
        )
    with tempfile.TemporaryDirectory(prefix="mrs-wp0-order-reading-") as tmp:
        root = Path(tmp)
        for code in ("es", "en"):
            reading.play(code, list(range(1, 21)), root, ORDER_READING_SEED)
        out = {}
        for code in ("es", "en"):
            runs = reading._load(root / code)
            out[code] = {
                f"{number:02d}": _stable_rehearsal_result(run)
                for number, run in sorted(runs.items())
            }
        out["paired_differences"] = reading.paired_differences(
            reading._load(root / "es"), reading._load(root / "en")
        )
        return out


def build_snapshot():
    _assert_runtime_clean()
    started = time.monotonic()
    payload = {
        "schema": SCHEMA,
        "baseline_sha": BASE_SHA,
        "seed": {
            "pilot_acceptance": 17,
            "order_reading": ORDER_READING_SEED,
        },
        "normalization": NORMALIZATION,
        "wp0_gaps": GAPS,
        "acceptance": acceptance_snapshot(),
        "order_reading": order_reading_snapshot(),
    }
    elapsed = time.monotonic() - started
    return payload, elapsed


def _comparison_view(value):
    if isinstance(value, dict):
        return {
            key: ("<normalized:code_version>" if key == "code_version" else _comparison_view(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_comparison_view(item) for item in value]
    return value


def contract_difference(expected, actual, path="$"):
    return first_difference(_comparison_view(expected), _comparison_view(actual), path)


def first_difference(expected, actual, path="$"):
    if type(expected) is not type(actual):
        return path, expected, actual
    if isinstance(expected, dict):
        ekeys, akeys = set(expected), set(actual)
        if ekeys != akeys:
            return path + ".keys", sorted(ekeys), sorted(akeys)
        for key in sorted(expected):
            diff = first_difference(expected[key], actual[key], f"{path}.{key}")
            if diff:
                return diff
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return path + ".length", len(expected), len(actual)
        for index, (left, right) in enumerate(zip(expected, actual)):
            diff = first_difference(left, right, f"{path}[{index}]")
            if diff:
                return diff
        return None
    if expected != actual:
        return path, expected, actual
    return None


def load_baseline(path=BASELINE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_baseline(path=BASELINE):
    payload, seconds = build_snapshot()
    blob = _json_bytes(payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    print(f"WROTE {path.relative_to(ROOT)} · {len(blob)} bytes · sha256 {_sha256_bytes(blob)} "
          f"· {seconds:.1f} s · 0 app AI calls")
    return payload


def _report_difference(diff):
    where, left, right = diff
    print(f"DIFFERENCE at {where}")
    print("baseline:", json.dumps(left, ensure_ascii=False, sort_keys=True, default=str)[:2000])
    print("current :", json.dumps(right, ensure_ascii=False, sort_keys=True, default=str)[:2000])


def _acceptance_variant_snapshot(variant):
    import pilot_acceptance as acceptance

    with _capture_acceptance_turns() as turns:
        acceptance.battery.cache_clear()
        result = acceptance.battery(variant)
        if not all(item.get("ok") for item in result.values()):
            failed = [name for name, item in result.items() if not item.get("ok")]
            raise RuntimeError(f"{variant}: acceptance battery failed during equivalence check: {failed}")
        return {
            "battery": deepcopy(result),
            "turns": turns.get(variant, []),
        }


def check_baseline(path=BASELINE):
    import pilot_freeze

    changed = _runtime_diff()
    if changed:
        print("CHECKING CURRENT PHASE-1 RUNTIME DIFF: " + ", ".join(changed), flush=True)
    expected = load_baseline(path)
    started = time.monotonic()

    for index, variant in enumerate(pilot_freeze.accepted_variants(), 1):
        actual_case = _acceptance_variant_snapshot(variant)
        diff = contract_difference(
            expected["acceptance"][variant],
            actual_case,
            f"$.acceptance.{variant}",
        )
        if diff:
            _report_difference(diff)
            return 1
        print(f"check acceptance {index:>2}/30 {variant}: MATCH", flush=True)

    actual_reading = order_reading_snapshot()
    diff = contract_difference(expected["order_reading"], actual_reading, "$.order_reading")
    if diff:
        _report_difference(diff)
        return 1

    seconds = time.monotonic() - started
    blob = Path(path).read_bytes()
    print(f"MATCH {Path(path).relative_to(ROOT)} · sha256 {_sha256_bytes(blob)} "
          f"· {seconds:.1f} s · 0 app AI calls")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    args = parser.parse_args(argv)
    if args.write:
        write_baseline(args.baseline)
        return 0
    return check_baseline(args.baseline)


if __name__ == "__main__":
    raise SystemExit(main())

