"""The pilot tool never repeats a failed request on its own, forced or not (2026-09-26).

A forced retry once ran four equivalent paid attempts, because the loop that
waits for a new person's anchor forced every round. These run the tool against
the simulated provider of ``test_the_image_bank``.
"""
import pytest

import image_broker
import tools_image_bank
from test_the_image_bank import Provider, mismatch, passing


@pytest.fixture
def url(tmp_path):
    return f"sqlite:///{tmp_path / 'pilot.sqlite3'}"


def run_with(monkeypatch, provider, url, *args):
    monkeypatch.setattr(image_broker, "_client", lambda api_key, client_factory: provider)
    monkeypatch.setattr(image_broker, "RETRY_PAUSE_SECONDS", 0.0)
    tools_image_bank.main(["run", "--database-url", url, "--batch", "1", "--proxy-credentials", *args])
    image_broker.wait(30)


def test_a_forced_retry_is_one_attempt_whatever_the_screen_says(monkeypatch, url):
    # Anchor accepted, then the state rejected twice (the edit and its correction).
    provider = Provider(screens=[passing(), mismatch(), mismatch()])
    run_with(monkeypatch, provider, url)
    assert provider.kinds().count("edit") == 1 and provider.kinds().count("repair") == 1
    before = len(provider.calls)
    provider.screens = [mismatch(), mismatch(), mismatch(), mismatch()]
    run_with(monkeypatch, provider, url, "--force")
    # One edit and its one correction: nothing more, although it failed again.
    assert provider.kinds()[before:] == ["edit", "screen", "repair", "screen"]


def test_without_force_a_failed_state_is_not_asked_for_again(monkeypatch, url):
    provider = Provider(screens=[passing(), mismatch(), mismatch()])
    run_with(monkeypatch, provider, url)
    before = len(provider.calls)
    run_with(monkeypatch, provider, url)
    assert len(provider.calls) == before
