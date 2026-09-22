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
