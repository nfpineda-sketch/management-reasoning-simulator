"""The batch runner's test accounts: from the environment, or from a local file.

On a person's own computer the passwords can live in a file that is never
committed (local-data/ is ignored), so that they need not be typed into a chat
or into a shell profile. The environment still comes first.
"""
import pytest

import tanda20_runner


@pytest.fixture
def stored(tmp_path, monkeypatch):
    path = tmp_path / "credentials.env"
    monkeypatch.setattr(tanda20_runner, "CREDENTIALS_FILE", path)
    for name in ("MRS_BATCH_RESIDENT_USER", "MRS_BATCH_RESIDENT_PASSWORD", "MRS_BATCH_STAFF_USER",
                 "MRS_BATCH_STAFF_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    return path


def test_the_local_file_supplies_what_the_environment_does_not(stored, monkeypatch):
    stored.write_text("# test accounts\nMRS_BATCH_RESIDENT_PASSWORD=resident-secret\n"
                      'MRS_BATCH_STAFF_USER="docente_prueba"\nMRS_BATCH_STAFF_PASSWORD=staff-secret\n')
    assert tanda20_runner.credentials() == ("residente_prueba_r3", "resident-secret", "docente_prueba",
                                            "staff-secret")
    monkeypatch.setenv("MRS_BATCH_STAFF_USER", "from_environment")
    assert tanda20_runner.credentials()[2] == "from_environment"


def test_nothing_anywhere_stops_before_anything_is_opened(stored):
    with pytest.raises(SystemExit, match="credentials.env"):
        tanda20_runner.credentials()


def test_the_file_is_never_committed():
    from pathlib import Path
    ignored = Path(tanda20_runner.ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "local-data/" in ignored
    assert tanda20_runner.CREDENTIALS_FILE.relative_to(tanda20_runner.ROOT).parts[0] == "local-data"


def test_the_file_is_read_for_the_batch_s_names_only(stored):
    stored.write_text("OPENAI_API_KEY=sk-not-for-this\nMRS_BATCH_RESIDENT_PASSWORD=r\n"
                      "MRS_BATCH_STAFF_USER=s\nMRS_BATCH_STAFF_PASSWORD=p\n")
    assert "OPENAI_API_KEY" not in tanda20_runner._stored_credentials()
    assert tanda20_runner.credentials()[1:] == ("r", "s", "p")
