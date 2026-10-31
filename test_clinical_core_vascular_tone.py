"""Phase 2 shadow core, P2J-2: the dynamic vascular-tone response and the pressure decision surface.

These tests pin the tone response in the core (the target, its arrival normalization, the explicit one-minute timing,
gain 0 writing nothing, the contraction bound, the fail-closed guard and second writer), the structural probes 1-8, the
analytic prefilter of the frozen surface, the exact reconstruction against the core, what P2J-2 changed outside its
module (and the closed packages' guards that rest on it), and the policy: nothing approved, no pressure feedback, no
pressure -> HR.
"""
import ast
import hashlib
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import bands, decision_pack, lactate_slice
from clinical_core import baroreflex as br
from clinical_core import blood_fluid_calibration as bf
from clinical_core import derived as dv
from clinical_core import hr_primary as hp
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr
from clinical_core import pressure_tone as pt
from clinical_core import vascular_tone as vt
from clinical_core.derived import (DEFAULT_PROFILE, PARAMETERS, CoreProfile, acute_deficit_signal, arrival_state,
                                   arrival_tone_signal, tone_target)
from clinical_core.integration import VASCULAR_TONE, step
from clinical_core.state import CoreInvariantError

ROOT = vt.ROOT
SOURCE = ROOT / "clinical_core" / "vascular_tone.py"
#: The P2J-2 freeze: faculty decisions, the P2J-1 record, the tone equation, timing, feedback and arrival rules, the
#: gains, the afterload points, the analytic and simulation rules, the design, the reconstruction rule, the probes, the
#: trade-off, envelope, identifiability and verdict rules, the baroreflex plan, the policy and every clinical_core
#: source but the downstream reports, committed before any clinical trajectory was evaluated.
FROZEN_DIGEST = "baa2ee124decc7c84a48b0b8fe5031a9dab774e3587176c79e1907df94904545"
#: P2J-2 is closed (P2J-3): its module and its record are pinned byte for byte, and its freeze is recomputed from the
#: live sources without the later modules, with the two tuple-only files at their P2J-2 hashes while only their tuples
#: changed (pressure_tone_filter.p2j2_sources).
P2J2_MODULE_SHA = "8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5"
P2J2_RECORD_SHA = "0c5c9feda158d9d799a0d12f900a9776fcca917ea0b80bfd7b580ec604031924"
LATER_MODULES = ("clinical_core/pressure_tone_filter.py", "clinical_core/baroreflex.py", "clinical_core/rr_audit.py",
                 "clinical_core/acid_base.py",
                 "clinical_core/ventilation.py", "clinical_core/ventilation_surface.py")
#: derived.py, integration.py and shadow.py as the latest package leaves them (derived.py: P2J-4, proven by
#: baroreflex.P2J4_CHANGES; integration.py and shadow.py: P2J-2): the AST proofs cover the declared statements; these pins
#: make any later change of the three files fail the closed packages' guards until it is proven again.
P2J2_SOURCES = {"clinical_core/derived.py": "87f773f54d6bc4d125ef7817eb79383e7b77d792d9879a9a90d8caa82efe275c",
                "clinical_core/integration.py": "cb54d2eec3754eecdd7267dba58b0389203b233b16a86455f5280d1eafa520f0",
                "clinical_core/shadow.py": "66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35"}
C57, C72 = vt.C57, vt.C72


def _ab():
    from clinical_core import acid_base as ab
    return ab

@pytest.fixture(scope="module")
def source():
    record = la.record_p2i2ab()
    return la.source_space(record), record["crystalloid_support"]


# The frozen package ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/vascular_tone.py" in sources
    assert "clinical_core/vascular_tone_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/vascular_tone.py", "clinical_core/vascular_tone_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert vt.p2j1_record()["freeze_digest"] == vt.P2J1_DIGEST
    from clinical_core import pressure_tone_filter as pf
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == P2J2_MODULE_SHA, "the closed P2J-2 module changed"
    assert hashlib.sha256(RECORD.read_bytes()).hexdigest() == P2J2_RECORD_SHA
    sources = {k: v for k, v in sources.items() if k not in LATER_MODULES}
    text = json.dumps({"revision": vt.REVISION, "p2j1": hashlib.sha256(vt.P2J1_RECORD.read_bytes()).hexdigest(),
                       "design": vt.design(), "sources": pf.p2j2_sources(_ab().p2j3_sources(sources))}, sort_keys=True,
                      default=str)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == FROZEN_DIGEST, "a source P2J-2 froze changed"


def test_the_faculty_decisions_are_recorded():
    assert set(vt.FACULTY) == {"decided", "structure", "tone", "semantics", "no_pressure_driver", "no_memory", "timing",
                               "loop", "range", "afterload", "arrival", "demand", "hr", "lactate", "scope"}
    assert "STRUCTURE_APPROVED" in vt.FACULTY["structure"] and "retired" in vt.FACULTY["structure"]
    assert "not authorized" in vt.FACULTY["timing"] and "no iterative solver" in vt.FACULTY["loop"]
    assert "88/54" in vt.FACULTY["arrival"] and "98/62" in vt.FACULTY["arrival"]


# The tone response in the core --------------------------------------------------------------------------------------

def test_the_gain_defaults_to_zero_and_then_writes_nothing():
    assert DEFAULT_PROFILE.deficit_to_tone_gain == 0.0
    assert PARAMETERS["deficit_to_tone_gain"][0] == dv.PROVISIONAL
    anchors = vt.tone_anchors(C57, "lower", 1.0)
    profile = vt.tone_profile(0.0, 0.3)
    state = arrival_state(anchors, profile).evolve(P=0.5)
    after, record = step(state, (), anchors, profile)
    assert after.T == 1.0 and not any(delta.source == VASCULAR_TONE for delta in record.deltas)


@pytest.mark.parametrize("case,level,factor", [(C57, "lower", 1.0), (C72, "midpoint", 1.1), (C57, "upper", 1.0)])
def test_the_arrival_is_the_targets_fixed_point_and_no_deficit_is_the_unstressed_tone(case, level, factor):
    anchors = vt.tone_anchors(case, level, factor)
    for gain in vt.GAINS:
        profile = vt.tone_profile(gain, 0.3)
        start = arrival_state(anchors, profile)
        s0 = arrival_tone_signal(anchors, profile)
        assert acute_deficit_signal(start, anchors, profile) == s0
        assert tone_target(start, anchors, profile) == 1.0
        resolved = start.evolve(P=3.0)
        assert acute_deficit_signal(resolved, anchors, profile) == 0.0
        assert tone_target(resolved, anchors, profile) * (1.0 + gain * s0) == pytest.approx(1.0, abs=1e-12)


def test_the_target_never_falls_as_the_deficit_grows_and_reads_no_pressure_debt_lactate_or_rate():
    anchors = vt.tone_anchors(C57, "midpoint", 1.0)
    profile = vt.tone_profile(1.5, 0.3)
    values = [(acute_deficit_signal(s, anchors, profile), tone_target(s, anchors, profile))
              for s in (arrival_state(anchors, profile).evolve(P=p) for p in (2.0, 1.5, 1.0, 0.7, 0.4, 0.2))]
    assert all(b[0] >= a[0] and b[1] >= a[1] for a, b in zip(values, values[1:]))
    forbidden = {"D", "lactate", "lactate_excess", "sympathetic_drive", "rate_bpm", "pressure_rel", "sbp", "dbp", "map",
                 "arterial_pressures", "sympathetic_target"}
    for function in (dv.tone_target, dv.arrival_tone_signal, dv.acute_deficit_signal, dv.delivery_rel_of):
        tree = ast.parse(inspect.getsource(function))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert not names & forbidden, function.__name__


def test_the_profile_refuses_a_loop_without_contraction():
    with pytest.raises(CoreInvariantError, match="below 1"):
        CoreProfile(deficit_to_tone_gain=2.0, afterload_sensitivity=0.5)
    with pytest.raises(CoreInvariantError):
        CoreProfile(deficit_to_tone_gain=-0.1)
    CoreProfile(deficit_to_tone_gain=1.9, afterload_sensitivity=0.5)


def test_a_target_outside_the_guard_and_a_second_tone_writer_fail_closed():
    anchors = vt.tone_anchors(C57, "lower", 1.0)
    profile = replace(vt.tone_profile(0.0, 0.3), deficit_to_tone_gain=2.5)
    with pytest.raises(CoreInvariantError, match="guard"):
        step(arrival_state(anchors, profile), (), anchors, profile)
    profile = vt.tone_profile(1.0, 0.3)
    drift = bands.Drift("tone", "T", 0, 40, -0.01)
    with pytest.raises(CoreInvariantError, match="compose"):
        step(arrival_state(anchors, profile), (drift,), anchors, profile)
    # At gain 0 the synthetic tone drift still writes T, as before P2J-2.
    plain = vt.tone_profile(0.0, 0.3)
    after, _ = step(arrival_state(anchors, plain), (drift,), anchors, plain)
    assert after.T == pytest.approx(0.99)


def test_the_core_writes_tone_only_in_its_own_coupling():
    """The only ChannelDelta on T built in clinical_core outside the synthetic bands is the integrator's tone response."""
    found = set()
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for top in tree.body:
            for node in ast.walk(top):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ChannelDelta" and node.args and \
                        isinstance(node.args[0], ast.Attribute) and node.args[0].attr == "T":
                    found.add((path.relative_to(ROOT).as_posix(), getattr(top, "name", "<module>")))
    assert found == {("clinical_core/integration.py", "_vascular_tone")}


# Probes, prefilter, timing ---------------------------------------------------------------------------------------------

def test_the_structural_probes_hold():
    probes = vt.probes()
    assert probes["checks"] == {str(n): True for n in range(1, 9)}
    for base in probes["bases"].values():
        for item in base["steady"].values():
            assert item["monotone"] and item["settled"] and item["largest_ratio"] <= item["bound"] + 1e-9
            assert item["bound"] < 1.0
        assert all(base["arrival_minute_1"].values())
    assert set(probes["bases"]) == {"neutral (s0 = 0)", "57m lower x1 (s0 = 0.4)"}


def test_the_surface_is_frozen_and_screened_before_any_simulation():
    assert vt.GAINS == (0.0, 0.25, 0.5, 1.0, 1.5, 2.0) and vt.AFTERLOAD == (0.1, 0.3, 0.5)
    assert vt.PRIMARY_AFTERLOAD == 0.3 and vt.REFERENCE_GAIN == 0.0
    screen = vt.analytic_screen()
    rejected = {k: v["reasons"] for k, v in screen.items() if v["status"] == "ANALYTIC_REJECTION"}
    assert rejected == {"g2 a0.5": ["NO_CONTRACTION"]} and len(vt.admissible()) == 17
    assert all(1.0 + g <= vt.T_UPPER and 1.0 / (1.0 + g) >= vt.T_LOWER for g in vt.GAINS)
    literal = vt.literal_alternative({"x": 0.4, "zero": 0.0})
    assert literal["x g1 a0.3"]["T_minute_1"] == 1.4 and literal["x g1 a0.3"]["map_factor"] > 1.2
    assert all(item["map_factor"] == 1.0 for key, item in literal.items() if key.startswith("zero"))


def test_the_timing_is_explicit_one_minute_behind_with_no_solver():
    from clinical_core import integration
    source = inspect.getsource(integration._vascular_tone)
    assert "tone_target(state, anchors, profile) - state.T" in source
    for function in (integration._vascular_tone, dv.tone_target, dv.arrival_tone_signal, dv.acute_deficit_signal):
        tree = ast.parse(inspect.getsource(function))
        assert not any(isinstance(n, (ast.While, ast.For)) for n in ast.walk(tree)), function
    assert vt.FEEDBACK["classification"] == "EXPLICIT_LAGGED_FEEDBACK"
    # The tone delta is added once per minute, after the contributions and before the channels are summed.
    body = inspect.getsource(integration.step)
    assert body.count("_vascular_tone(") == 1 and body.index("_vascular_tone(") < body.index("for channel in SCALAR")


# The reconstruction ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("gain,a", [(1.0, 0.3), (2.0, 0.1), (1.5, 0.5)])
def test_the_reconstruction_equals_the_core(source, gain, a):
    src, support = source
    arrivals = lr.arrival_table()
    for case, index, name, entry, bag, scenario in (
            (C57, 3, "P1", src["p1"][0], None, vt.L1), (C72, 1, "P2", src["p1"][0], support[0]["bag"], vt.L2),
            (C57, 0, "P4", src["p3"][0], None, vt.L3)):
        _, blood = vt._blood_task(((name, case, 0), entry, case, scenario, bag))
        rebuilt = vt.rebuild(blood, vt.tone_anchors(case, vt.level_of(index), 1.1), gain, a)
        series = vt.debt_and_lactate(blood, rebuilt, case, index, 1.1, arrivals)
        core = pt.full_run(entry, case, scenario, 1.1, vt.LAMBDAS[index], bag, "midpoint",
                           {"deficit_to_tone_gain": gain, "afterload_sensitivity": a})
        assert len(core["rows"]) == len(rebuilt["rows"]) and core["stop"] == rebuilt["stop"]
        for row, mine in zip(core["rows"], rebuilt["rows"]):
            assert all(row[f] == mine[f] for f in ("T", "output", "p", "sbp", "dbp", "map", "deficit")), row["minute"]
            assert row["D"] == series["D"][row["minute"]] and row["lactate"] == series["lactate"][row["minute"]]
        assert rebuilt["rows"][1]["T"] == 1.0 and rebuilt["rows"][2]["T"] != 1.0


# What P2J-2 changed outside its module --------------------------------------------------------------------------------

def test_p2j2_changed_only_the_declared_statements():
    # P2J-4 changed derived.py again (the baroreflex): its proof is baroreflex's, over P2J-2's and P2J-4's statements.
    # P2K-2 changed derived.py and integration.py once more, only by its off-by-default insertions: the proofs read the
    # live files with them removed (acid_base.p2k1_text); a mutation is made on the live file first.
    ab = _ab()
    integration_item = vt.P2J2_CHANGES[vt.INTEGRATION]
    stripped = ab.p2k1_text(vt.INTEGRATION)
    assert vt.outside_digest(stripped, integration_item["changed"]) == integration_item["outside_p2j1"]
    assert vt.outside_digest(stripped, integration_item["since_p2i2ak"]) == integration_item["outside_p2i2ak"]
    item = br.P2J4_CHANGES[vt.DERIVED]
    assert vt.outside_digest(ab.p2k1_text(vt.DERIVED), item["since_p2j1"]) == item["outside_p2j1"]
    assert vt.outside_digest(ab.p2k1_text(vt.DERIVED), item["since_p2i2ak"]) == item["outside_p2i2ak"]
    derived = vt._live(vt.DERIVED)
    mutated = ab.stripped_text(vt.DERIVED, derived.replace("OUTPUT_EPSILON = 1e-9", "OUTPUT_EPSILON = 1e-8"))
    assert vt.outside_digest(mutated, vt.P2J2_CHANGES[vt.DERIVED]["changed"]) != \
        vt.P2J2_CHANGES[vt.DERIVED]["outside_p2j1"], "the proof must notice a change outside the tone statements"
    integration = vt._live(vt.INTEGRATION)
    mutated = ab.stripped_text(vt.INTEGRATION, integration.replace("CONSERVATION_TOLERANCE = 1e-9",
                                                                   "CONSERVATION_TOLERANCE = 1e-8"))
    assert vt.outside_digest(mutated, vt.P2J2_CHANGES[vt.INTEGRATION]["changed"]) != \
        vt.P2J2_CHANGES[vt.INTEGRATION]["outside_p2j1"]
    for relative, item in vt.TUPLE_CHANGES.items():
        assert vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]
    assert all(ab.proofs().values())
    assert {k: (ab.CORE_AT_P2K1[k] if k in ab.CORE_FILES and ab.proved(k)
                else hashlib.sha256((ROOT / k).read_bytes()).hexdigest()) for k in P2J2_SOURCES} == P2J2_SOURCES
    for name in ("deficit_to_tone_gain",):
        assert name in {f.name for f in __import__("dataclasses").fields(CoreProfile)}


#: Inside the statements P2J-2 declared, nothing but the tone (adversarial review of P2J-2): each statement's AST with
#: the tone field, the tone check, the tone PARAMETERS entry, the tone branch of step and the tone_target import removed
#: equals its AST at P2J-1 (f6b4cd0), digest by digest. P2J-4: the baroreflex fields, check and entries, the amended
#: relative-pressure text and the sympathetic_target line are removed first (baroreflex.StripP2J4), on both sides.
INSIDE_AT_P2J1 = {("clinical_core/derived.py", "CoreProfile"): "da3e103747d4d0c1302bbb1413397b7e64e75cd22e38d3abf8630e8e7001a52e",
                  ("clinical_core/derived.py", "PARAMETERS"): "288f89278c8fefb8d290c40ad69972569c4d09d99109936cfbf108d3d464fe61",
                  ("clinical_core/integration.py", "step"): "a0b51f40ca0ae6a52acd4fa75b8e1decc5bcbafcaf689e219e955b386c6c5386",
                  ("clinical_core/integration.py", "from .derived"):
                      "cdcf016cb56ff945da0ee7d278430f04c6152deb54d52625de6df1d061cfd1ee"}
TONE_NAME = "deficit_to_tone_gain"


def _mentions(node, name):
    return any((isinstance(n, ast.Name) and n.id == name) or (isinstance(n, ast.Attribute) and n.attr == name)
               for n in ast.walk(node))


class _StripTone(ast.NodeTransformer):
    def generic_visit(self, node):
        super().generic_visit(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                setattr(node, field, [v for v in value if not (
                    isinstance(v, ast.AnnAssign) and isinstance(v.target, ast.Name) and v.target.id == TONE_NAME)
                    and not (isinstance(v, ast.If) and _mentions(v.test, TONE_NAME))])
        if isinstance(node, ast.Dict):
            pairs = [(k, v) for k, v in zip(node.keys, node.values)
                     if not (isinstance(k, ast.Constant) and k.value == TONE_NAME)]
            node.keys, node.values = [k for k, _ in pairs], [v for _, v in pairs]
        if isinstance(node, ast.ImportFrom):
            node.names = [a for a in node.names if a.name != "tone_target"]
        return node


def _inside_digest(text, name):
    for node in ast.parse(text).body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(
            node, ast.AnnAssign) else []
        if getattr(node, "name", None) == name or any(isinstance(t, ast.Name) and t.id == name for t in targets) or (
                isinstance(node, ast.ImportFrom) and name == f"from .{node.module}"):
            return hashlib.sha256(ast.dump(_StripTone().visit(br.StripP2J4().visit(node))).encode("utf-8")).hexdigest()
    raise KeyError(name)


def test_inside_the_declared_statements_p2j2_changed_only_the_tone():
    # P2K-2: read on the live files with its insertions removed (acid_base.p2k1_text); mutations on the live file first.
    ab = _ab()
    for (relative, name), expected in INSIDE_AT_P2J1.items():
        assert _inside_digest(ab.p2k1_text(relative), name) == expected, (relative, name)
    derived = vt._live(vt.DERIVED)
    assert _inside_digest(ab.stripped_text(vt.DERIVED, derived.replace("debt_to_lactate_gain: float = 2.0 / 3600.0",
                                                                       "debt_to_lactate_gain: float = 2.0 / 3000.0")),
                          "CoreProfile") != \
        INSIDE_AT_P2J1[(vt.DERIVED, "CoreProfile")], "a changed default inside CoreProfile must be noticed"
    integration = vt._live(vt.INTEGRATION)
    assert _inside_digest(ab.stripped_text(vt.INTEGRATION, integration.replace(
        "withdrawn = _no_repayment_across(debt, new_state, anchors, profile, demand)", "withdrawn = None")), "step") != \
        INSIDE_AT_P2J1[(vt.INTEGRATION, "step")], "a change inside step must be noticed"


def test_the_closed_p2j1_freeze_recomputes_from_the_proven_sources():
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in vt.OWN + LATER_MODULES}
    text = json.dumps({"revision": pt.REVISION, "p2i2ak": hashlib.sha256(pt.P2I2AK_RECORD.read_bytes()).hexdigest(),
                       "design": pt.design(), "sources": _ab().p2j1_sources(sources)}, sort_keys=True, default=str)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == vt.P2J1_DIGEST


# Policy ---------------------------------------------------------------------------------------------------------------

def test_no_legacy_no_p2f_no_pressure_feedback_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"shadow", "legacy_adapter", "comparison", "family_engine", "contracts_shadow",
                           "contracts_legacy", "hemodynamic_probes"}
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(vt.run)
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    assert vt.BAROREFLEX_PLAN["status"].startswith("DEFERRED")
    text = json.dumps(vt.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


# The evaluation, on the frozen package (freeze b3b63b1) ---------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2J2_vascular_tone.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2J2_TONO_VASCULAR_DINAMICO.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == vt.P2J1_DIGEST
    # The trajectories are not re-run here; the screen, the probes and the arrival signals are.
    assert record["screen"] == _json(vt.analytic_screen()) and record["probes"] == _json(vt.probes())
    signals = {f"{case} {level} x{f:g}": arrival_tone_signal(vt.tone_anchors(case, level, f), vt.tone_profile(0.0, 0.3))
               for case in vt.CASES for level in vt.LEVELS for f in vt.DEMANDS}
    assert record["arrival_signals"] == _json(signals)
    assert record["literal_alternative"] == _json(vt.literal_alternative(signals))
    assert record["gains"] == list(vt.GAINS) and record["afterload"] == list(vt.AFTERLOAD)


def test_the_verdict_follows_its_checks_on_the_recorded_inputs(record):
    inputs = dict(probe=record["probes"], flags=record["flags"], sample_flags=record["sample_flags"],
                  fd=record["fd_lac"], tables=record["trajectories"], validation=record["validation"],
                  reuse=record["reuse"], reference_equal=record["reference_equals_p2j1"],
                  deterministic=record["deterministic"], trade=record["tradeoff"],
                  gains=[g for g, a in vt.admissible() if a == vt.PRIMARY_AFTERLOAD])
    assert _json(vt.verdict(**inputs)) == record["verdict"]
    assert record["verdict"]["verdict"] == vt.READY and record["verdict"]["approved"] == []
    broken = vt.verdict(**{**inputs, "validation": {**record["validation"], "equal": False}})
    assert broken["verdict"] == f"{vt.NOT_READY} — reconstruction_exact"
    lost = json.loads(json.dumps(record["fd_lac"]))
    for item in lost.values():
        for g in item["gains"].values():
            g["candidates"] = 0
    assert vt.verdict(**{**inputs, "fd": lost})["verdict"].endswith("lactate_satisfiable")


def test_the_reuse_validation_and_stability_the_report_states(record):
    assert record["reuse"]["units_digests"] == {"1": vt.UNITS[1.0], "1.1": vt.UNITS[1.1]}
    assert record["units"] == {"1": 18, "1.1": 37} and record["keys"] == 1866
    assert record["validation"]["equal"] and record["validation"]["compared"] == 816
    assert record["deterministic"] and record["reference_equals_p2j1"]
    for by_gain in (record["flags"], *record["sample_flags"].values()):
        for flag in by_gain.values():
            assert flag["arrival_kept"] and not any(flag[k] for k in ("GUARD_CONTACT", "OSCILLATION", "STOP",
                                                                      "negative_pressure"))
    assert {f: v["gains"]["0"]["candidates"] for f, v in record["fd_lac"].items()} == {"1": 216, "1.1": 1092}
    assert {f: v["reference_candidates"] for f, v in record["fd_lac"].items()} == {"1": 216, "1.1": 1092}
    assert not any(item["class"] == "UNSTABLE_FEEDBACK" for item in record["tradeoff"].values())
    assert record["tradeoff"]["g2 a0.5"]["class"] == "ANALYTIC_REJECTION"


def test_the_trajectories_the_report_states(record):
    t = record["trajectories"]
    p1, p4 = t["P1 gi_bleed_57m x1"]["gains"], t["P4 gi_bleed_57m x1"]["gains"]
    assert p1["0"]["at"]["120"]["map"]["median"] == pytest.approx(32.35, abs=0.01)
    assert p1["2"]["at"]["120"]["map"]["median"] == pytest.approx(39.91, abs=0.01)
    assert p4["0"]["at"]["120"]["map"]["median"] == pytest.approx(100.66, abs=0.01)
    assert p4["1"]["at"]["120"]["T"]["median"] == pytest.approx(0.714, abs=0.001)
    for table in t.values():
        for gain in table["gains"].values():
            assert gain["at"]["0"]["T"]["low"] == gain["at"]["0"]["T"]["high"] == 1.0   # minute 1: the flags
    # Untreated: tone never lowers pressure against T = 1; resuscitated: T_abs back to 1.
    assert all(g["at"]["120"]["map_change"]["low"] >= 0.0 for k, v in t.items() if k.startswith("P1")
               for g in v["gains"].values())
    assert all(abs(g["at"]["120"]["T_abs"]["median"] - 1.0) < 0.01 for k, v in t.items() if k.startswith("P4")
               for g in v["gains"].values())
    assert all(item["status"] == "PROPOSED_NOT_APPROVED" for item in record["envelopes"].values())
    assert set(record["envelopes"]) == set("ABCDEFGHI")


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import vascular_tone_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    vascular_tone_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"
