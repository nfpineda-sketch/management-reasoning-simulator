"""Every regression script is active or retired with its reason (faculty decision P-11 B, 2026-09-30).

The ten scripts diagnosed in C10-01 fail on code or texts that no longer exist and add no coverage. They
are kept in the repository, never run, and named in ``run_regressions.RETIRED_REGRESSIONS`` with why. A
script added later has to be placed in one list or the other, so a report can always say how many active
regressions passed and how many are retired, never "56 of 66".
"""
from pathlib import Path

import run_regressions

ROOT = Path(__file__).resolve().parent


def test_every_script_is_active_or_retired_and_never_both():
    present = {path.name for path in ROOT.glob("regression_*.py")}
    active = set(run_regressions.ACTIVE_REGRESSIONS)
    retired = set(run_regressions.RETIRED_REGRESSIONS)
    assert len(active) == len(run_regressions.ACTIVE_REGRESSIONS), "a script is listed twice as active"
    assert not active & retired
    assert present == active | retired, sorted(present ^ (active | retired))


def test_every_retired_script_says_why_and_is_kept():
    assert len(run_regressions.RETIRED_REGRESSIONS) == 10
    for name, reason in run_regressions.RETIRED_REGRESSIONS.items():
        assert (ROOT / name).exists(), name
        assert isinstance(reason, str) and len(reason.strip()) > 40, name


def test_the_runner_reports_active_and_retired_apart(monkeypatch, capsys):
    ran = []

    class Done:
        returncode = 0

    monkeypatch.setattr(run_regressions.subprocess, "run", lambda args, check: ran.append(args[1]) or Done())
    run_regressions.main()
    assert ran == run_regressions.ACTIVE_REGRESSIONS
    assert not set(ran) & set(run_regressions.RETIRED_REGRESSIONS)
    printed = capsys.readouterr().out
    total = len(run_regressions.ACTIVE_REGRESSIONS)
    assert f"PASS: {total}/{total} active regression scripts; 10 retired" in printed
