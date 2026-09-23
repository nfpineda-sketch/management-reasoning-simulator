"""The deployment diagnostic says what is wrong without printing the URL.

The application hides its database errors because a connection failure can
carry the host, the user and the password. This tool exists to say the same
thing in words, and it must not leak what the application refuses to show.
"""
import pytest

import check_database


@pytest.mark.parametrize("url, needle", [
    ("", "empty or unset"),
    ("sqlite:///accounts.sqlite3", "postgresql://"),
    ("postgresql://USUARIO:CLAVE@HOST:5432/BASE?sslmode=require", "example word"),
    ("postgresql://user:secret@host:5432/?sslmode=require", "names no database"),
    ("postgresql://user:secret@host:5432/app", "sslmode"),
])
def test_it_names_the_fault_in_the_url(url, needle):
    complaint = check_database.describe(url)
    assert complaint and needle in complaint


def test_a_usable_url_has_no_complaint():
    assert check_database.describe("postgresql://user:secret@host:5432/app?sslmode=require") is None


def test_the_complaint_never_repeats_the_password():
    for url in ("postgresql://user:hunter2hunter2@host:5432/app",
                "postgresql://user:hunter2hunter2@host:5432/?sslmode=require"):
        assert "hunter2hunter2" not in (check_database.describe(url) or "")


def test_the_postgres_alias_is_accepted():
    assert check_database.describe("postgres://user:secret@host:5432/app?sslmode=require") is None


def test_it_names_what_is_wrong_with_a_bootstrap_hash():
    from account_store import PASSWORD_ROUNDS, hash_password
    good = hash_password("una-clave-suficientemente-larga")
    assert check_database.describe_admin_hash(good) is None
    salt, digest = good.split("$")[2], good.split("$")[3]
    cases = [
        ("", "empty or unset"),
        ("EL_HASH_QUE_GENERA_EL_COMANDO", "placeholder"),
        (f'"{good}"', "wrapped in quotes"),
        (good[:40] + " " + good[40:], "space or a line break"),
        (good.replace("pbkdf2_sha256", "bcrypt", 1), "pbkdf2_sha256"),
        (f"pbkdf2_sha256$many${salt}${digest}", "not a number"),
        (f"pbkdf2_sha256$1000${salt}${digest}", str(PASSWORD_ROUNDS)),
        (f"pbkdf2_sha256${PASSWORD_ROUNDS}${salt[:20]}${digest}", "salt"),
        (f"pbkdf2_sha256${PASSWORD_ROUNDS}${salt}${digest[:40]}", "digest"),
        (f"pbkdf2_sha256${PASSWORD_ROUNDS}$zz{salt[2:]}${digest}", "not hexadecimal"),
    ]
    for value, needle in cases:
        complaint = check_database.describe_admin_hash(value)
        assert complaint and needle in complaint, (value[:30], complaint)


def test_the_complaint_never_repeats_the_hash():
    from account_store import hash_password
    good = hash_password("una-clave-suficientemente-larga")
    for value in (f'"{good}"', good[:40] + "\n" + good[40:], good.replace("pbkdf2_sha256", "bcrypt", 1)):
        complaint = check_database.describe_admin_hash(value) or ""
        assert good.split("$")[3] not in complaint
        assert good.split("$")[2] not in complaint


def _store(tmp_path):
    from account_store import AccountStore, hash_password
    url = "sqlite:///" + str(tmp_path / "accounts.sqlite3")
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("npineda", hash_password("una-clave-larga-de-prueba"))
    return url, store


def test_it_separates_a_missing_account_from_a_throttled_one(tmp_path, capsys, monkeypatch):
    from account_store import AccountError
    url, store = _store(tmp_path)
    monkeypatch.setenv("MRS_DATABASE_URL", url)

    assert check_database.main(["--account", "npineda"]) == 0
    reported = capsys.readouterr().out
    assert "exists" in reported and "admin" in reported and "active" in reported
    assert "throttle" not in reported

    assert check_database.main(["--account", "otronombre"]) == 0
    reported = capsys.readouterr().out
    assert "No account named" in reported
    assert "1 administrator account(s)" in reported
    assert "npineda" in reported          # the name to type is what is missing

    for _ in range(6):
        with pytest.raises(AccountError):
            store.authenticate("npineda", "la-clave-equivocada")
    assert check_database.main(["--account", "npineda"]) == 0
    reported = capsys.readouterr().out
    assert "locked by the sign-in throttle" in reported
    assert "minute(s)" in reported


def test_it_says_when_no_administrator_was_ever_created(tmp_path, capsys, monkeypatch):
    from account_store import AccountStore
    url = "sqlite:///" + str(tmp_path / "empty.sqlite3")
    AccountStore(url, allow_sqlite=True)
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    assert check_database.main(["--account", "npineda"]) == 0
    reported = capsys.readouterr().out
    assert "0 administrator account(s)" in reported
    assert "MRS_ADMIN_USERNAME" in reported


def test_the_account_report_never_prints_a_hash(tmp_path, capsys, monkeypatch):
    url, store = _store(tmp_path)
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    check_database.main(["--account", "npineda"])
    assert "pbkdf2_sha256" not in capsys.readouterr().out
