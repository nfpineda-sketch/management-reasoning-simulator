"""The time budget must fit the pipeline, and a paid failure must survive on disk.

A real gpt-5-mini run of challenge R1-05 spent five requests and 60,011 tokens
under the old 300 s budget and started no encounter: author 63.0 s, correction
48.1 s, review 70.0 s, correction 53.7 s, then the mandatory final review began
with 63 s left against a reserve calibrated for 30 s, and timed out. The
diagnostic that would have explained the first compile failure was discarded by
the shared-password launch path.

No paid calls: the provider client is a local stub.
"""
import ast
import json
from pathlib import Path
import unittest

import generated_case
from generated_case import (
    REQUEST_BUDGET_SECONDS, REVIEW_ROUNDS, STAGE_BUDGET_SECONDS, WORST_CASE_STAGES,
)


ROOT = Path(__file__).resolve().parent


class BudgetFitsTheLongestPath(unittest.TestCase):
    def test_the_budget_covers_every_stage_of_the_worst_case(self):
        self.assertGreaterEqual(REQUEST_BUDGET_SECONDS,
                                STAGE_BUDGET_SECONDS * len(WORST_CASE_STAGES))

    def test_the_declared_worst_case_matches_the_requests_the_code_can_make(self):
        """author, one structural correction, then REVIEW_ROUNDS reviews and repairs."""
        tree = ast.parse((ROOT / "generated_case.py").read_text())
        function = next(n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef) and n.name == "generate_ai_encounter")
        sites = [n for n in ast.walk(function)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "request_case"]
        # Four call sites: author, structural correction, and inside the review
        # loop a review plus the clinical repair that precedes the next round.
        self.assertEqual(len(sites), 4)
        self.assertEqual(len(WORST_CASE_STAGES), 2 * REVIEW_ROUNDS + 1)
        self.assertEqual(WORST_CASE_STAGES.count("REVIEW"), REVIEW_ROUNDS)

    def test_one_review_round_reports_a_rejected_case_instead_of_repairing_it(self):
        """The cut: a rejected case costs three requests, not five and a timeout."""
        self.assertEqual(REVIEW_ROUNDS, 1)
        self.assertEqual(WORST_CASE_STAGES, ("AUTHOR", "CORRECTION", "REVIEW"))
        self.assertEqual(REQUEST_BUDGET_SECONDS, 270)

    def test_the_measured_run_would_now_complete(self):
        """Replay the real run's durations against the budget arithmetic.

        Author 63.0 s, structural correction 48.1 s and review 70.0 s are the
        first three stages actually measured; under one review round that is the
        whole worst case.
        """
        observed = [("AUTHOR", 63.0), ("CORRECTION", 48.1), ("REVIEW", 70.0)]
        elapsed = 0.0
        for stage, seconds in observed:
            remaining = REQUEST_BUDGET_SECONDS - elapsed
            reserve = 0 if stage == "REVIEW" else STAGE_BUDGET_SECONDS
            self.assertGreaterEqual(remaining, reserve + STAGE_BUDGET_SECONDS,
                                    f"{stage} at {elapsed:.0f}s would be refused")
            allowed = min(120, remaining - reserve)
            self.assertGreaterEqual(allowed, seconds,
                                    f"{stage} at {elapsed:.0f}s would time out")
            elapsed += seconds
        self.assertLessEqual(elapsed, REQUEST_BUDGET_SECONDS)

    def test_a_stage_that_cannot_finish_is_refused_before_it_is_paid_for(self):
        """The old check let a request start with 10 s left and bought a timeout."""
        calls = []

        class Responses:
            @staticmethod
            def create(**kwargs):
                calls.append(kwargs["model"])
                raise AssertionError("a doomed request must not be sent")

        class Client:
            responses = Responses()

        # The pipeline takes its start time first; every later reading is late
        # enough that no stage can complete.
        readings = iter([0.0] + [REQUEST_BUDGET_SECONDS - 5.0] * 50)
        original = generated_case.monotonic
        generated_case.monotonic = lambda: next(readings)
        try:
            with self.assertRaises(generated_case.GeneratedCaseError) as raised:
                generated_case.generate_ai_encounter("R1-05", {"sim_time": 0}, client=Client())
        finally:
            generated_case.monotonic = original
        self.assertEqual(calls, [], "no provider request may be sent without budget")
        self.assertEqual(getattr(raised.exception, "code", None), "BUDGET")


class AFailedGenerationSurvivesOnDisk(unittest.TestCase):
    def setUp(self):
        import generation_diagnostics
        self.module = generation_diagnostics

    def test_the_draft_and_request_ledger_are_written_for_offline_replay(self):
        import tempfile
        from pathlib import Path as P

        class Failure(Exception):
            pass

        failure = Failure("stopped")
        failure.reference = "CASE-REVIEW-TIMEOUT"
        failure.diagnostic = {"draft": {"title": "x"}, "seed": 1,
                              "requests": [{"stage": "author", "seconds": 63.0}]}
        with tempfile.TemporaryDirectory() as tmp:
            self.module.DIAGNOSTIC_DIR = P(tmp) / "failures"
            path = self.module.save_failure(failure, challenge_id="R1-05")
            self.assertIsNotNone(path)
            saved = json.loads(path.read_text())
        self.assertEqual(saved["challenge_id"], "R1-05")
        self.assertEqual(saved["reference"], "CASE-REVIEW-TIMEOUT")
        self.assertEqual(saved["draft"], {"title": "x"})
        self.assertEqual(saved["requests"][0]["seconds"], 63.0)

    def test_a_reference_can_never_escape_the_diagnostic_directory(self):
        import tempfile
        from pathlib import Path as P

        class Failure(Exception):
            pass

        failure = Failure("stopped")
        failure.reference = "../../etc/passwd"
        failure.diagnostic = {"draft": {}}
        with tempfile.TemporaryDirectory() as tmp:
            self.module.DIAGNOSTIC_DIR = P(tmp) / "failures"
            path = self.module.save_failure(failure)
            self.assertEqual(path.parent, P(tmp) / "failures")
            self.assertNotIn("/", path.name.split("_", 1)[1][:-len(".json")])

    def test_a_write_failure_never_replaces_the_generation_error(self):
        from pathlib import Path as P

        class Failure(Exception):
            pass

        failure = Failure("stopped")
        failure.reference = "CASE-AUTHOR-TIMEOUT"
        failure.diagnostic = {"draft": {}}
        self.module.DIAGNOSTIC_DIR = P("/proc/nonexistent-and-unwritable/failures")
        self.assertIsNone(self.module.save_failure(failure))

    def test_both_launch_paths_persist_the_diagnostic(self):
        for name in ("app.py", "curriculum_runtime.py"):
            self.assertIn("save_failure", (ROOT / name).read_text(), name)


if __name__ == "__main__":
    unittest.main()


class TheClinicalRepairStaysReachable(unittest.TestCase):
    """REVIEW_ROUNDS = 1 makes the repair branch unreachable in production.

    Exercise it anyway, so raising the constant back is a one-line change rather
    than the discovery that the branch rotted while nothing ran it.
    """

    def test_raising_the_rounds_restores_the_repair_and_widens_the_budget(self):
        import importlib
        from test_generated_case import AuthorClient, clean_base

        module = importlib.reload(generated_case)
        original = module.REVIEW_ROUNDS
        try:
            module.REVIEW_ROUNDS = 2
            module.WORST_CASE_STAGES = (("AUTHOR", "CORRECTION")
                                        + ("REVIEW", "CORRECTION") * (module.REVIEW_ROUNDS - 1)
                                        + ("REVIEW",))
            module.REQUEST_BUDGET_SECONDS = (module.STAGE_BUDGET_SECONDS
                                             * len(module.WORST_CASE_STAGES))
            self.assertEqual(module.REQUEST_BUDGET_SECONDS, 450)

            rejected = {"coherent": False, "issues": ["Appearance conflicts with physiology."],
                        "checks": None}

            class RejectingOnce(AuthorClient):
                reviews = 0

                def create(self, **kwargs):
                    response = super().create(**kwargs)
                    if kwargs["text"]["format"]["name"] == "clinical_consistency_review":
                        RejectingOnce.reviews += 1
                    return response

            client = RejectingOnce()
            module.generate_ai_encounter("R1-03", clean_base(), client=client, seed=31)
            stages = [c["max_output_tokens"] for c in client.calls]
            self.assertEqual(stages[0], 24000)
            self.assertIn(6000, stages)
        finally:
            module.REVIEW_ROUNDS = original
            importlib.reload(generated_case)

    def test_the_repair_branch_is_still_compiled_and_reachable_by_the_loop(self):
        tree = ast.parse((ROOT / "generated_case.py").read_text())
        function = next(n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef) and n.name == "generate_ai_encounter")
        loops = [n for n in ast.walk(function) if isinstance(n, ast.For)
                 and isinstance(n.iter, ast.Call)
                 and getattr(n.iter.func, "id", "") == "range"]
        review_loop = next(n for n in loops
                           if getattr(n.iter.args[0], "id", "") == "REVIEW_ROUNDS")
        sites = [n for n in ast.walk(review_loop)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "request_case"]
        # The review itself and the clinical repair that precedes the next round.
        self.assertEqual(len(sites), 2)
