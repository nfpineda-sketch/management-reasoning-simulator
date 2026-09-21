"""Keep the test suite offline. A test must never buy a provider request.

The suite reads deployment secrets the same way the app does, so an
``OPENAI_API_KEY`` present in the environment or in ``.streamlit/secrets.toml``
silently turns AI language normalization on and every simulated learner
submission becomes a real, billed request. That happened during this repository's
own audit. Tests that need a provider pass an explicit stub client or an
``httpx.MockTransport``; neither opens a socket.

Set ``MRS_ALLOW_NETWORK_TESTS=1`` to opt out, for a deliberate paid run.
"""
import os
import socket

import pytest


_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1", ""}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


class BlockedNetworkCall(RuntimeError):
    """A test tried to open a socket, which for this suite means a paid call."""


def _address_host(address):
    if isinstance(address, tuple) and address:
        return str(address[0])
    return ""


def _blocked(original):
    def guard(self, address, *args, **kwargs):
        if _address_host(address) in _ALLOWED_HOSTS:
            return original(self, address, *args, **kwargs)
        raise BlockedNetworkCall(
            f"The test suite must stay offline; a socket to {_address_host(address)} "
            "was refused. Pass a stub client or an httpx.MockTransport, or set "
            "MRS_ALLOW_NETWORK_TESTS=1 for a deliberate paid run."
        )
    return guard


@pytest.fixture(autouse=True, scope="session")
def _offline_suite():
    if os.environ.get("MRS_ALLOW_NETWORK_TESTS") == "1":
        yield
        return
    socket.socket.connect = _blocked(_real_connect)
    socket.socket.connect_ex = _blocked(_real_connect_ex)
    try:
        yield
    finally:
        socket.socket.connect = _real_connect
        socket.socket.connect_ex = _real_connect_ex


@pytest.fixture(autouse=True)
def _no_deployment_key(monkeypatch):
    """A real key on this machine must not reach the app under test.

    ``_runtime_secret`` falls back to the environment, and Streamlit reads
    ``.streamlit/secrets.toml`` from disk. Individual tests that want the AI path
    set their own fictional key on the AppTest instance.
    """
    if os.environ.get("MRS_ALLOW_NETWORK_TESTS") == "1":
        return
    for name in ("OPENAI_API_KEY", "MRS_FACULTY_MODEL", "MRS_IMAGE_MODEL",
                 "MRS_IMAGE_REVIEW_MODEL", "MRS_GENERATOR_MODEL", "OPENAI_MODEL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _diagnostics_stay_out_of_the_project(tmp_path, monkeypatch):
    """A test that exercises a failed generation must not write into the repo.

    ``save_failure`` is wired into both launch paths, so the AppTest suite began
    dropping stub-client diagnostics into ``local-data/generation_failures``
    beside the real ones kept for replay.
    """
    import generation_diagnostics

    monkeypatch.setattr(generation_diagnostics, "DIAGNOSTIC_DIR",
                        tmp_path / "generation_failures")


@pytest.fixture(autouse=True)
def _streamlit_layout_context_is_not_inherited():
    """One AppTest must not leave a form open for the next one.

    Streamlit keeps the open layout containers in a ContextVar and the current
    form on the singleton main DeltaGenerator, which every AppTest in the
    process shares. A test whose app run ends inside ``st.form`` leaves
    ``FormData(form_id='learner_form')`` on that singleton, and the next
    AppTest raises "st.button() can't be used in an st.form()" while rendering
    an ordinary page. The suite then passes or fails by file order. Clearing
    both around every test keeps each one independent.
    """
    from streamlit.delta_generator_singletons import (
        context_dg_stack, get_default_dg_stack_value, get_dg_singleton_instance,
    )

    def reset():
        try:
            get_dg_singleton_instance().main_dg._form_data = None
            context_dg_stack.set(get_default_dg_stack_value())
        except RuntimeError:
            pass  # The singleton is created on the first AppTest; nothing to reset yet.

    reset()
    yield
    reset()
