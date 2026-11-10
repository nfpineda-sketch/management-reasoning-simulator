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
from pathlib import Path
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


@pytest.fixture(autouse=True, scope="session")
def _no_machine_wide_streamlit_files(tmp_path_factory):
    """``~/.streamlit`` never configures the app under test; a test's own settings do.

    Streamlit reads ``~/.streamlit/secrets.toml`` before the project's file,
    ``account_portal._setting`` prefers ``st.secrets`` to the environment, and
    Streamlit also copies each value into ``os.environ``. A ``MRS_DATABASE_URL``
    in that file therefore outranks the ``monkeypatch.setenv`` of a test that
    sets no ``at.secrets``. In the B-1 rehearsal (2026-10-07) the Phase 0 test
    on PostgreSQL created its account tables in the database that file named,
    not in ``MRS_TEST_POSTGRES_URL``. For the whole session Streamlit's per-user
    folder is an empty temporary one, so neither its config.toml nor its
    secrets.toml is read. The project's own ``.streamlit`` still is, and
    ``at.secrets`` still wins.
    """
    from streamlit import config, file_util
    import streamlit as st

    folder = tmp_path_factory.mktemp("streamlit-user-folder")

    def forget_what_was_read():
        st.secrets._reset()
        config.get_config_options(force_reparse=True)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(file_util, "get_streamlit_file_path", lambda *path: str(folder.joinpath(*path)))
        forget_what_was_read()
        yield folder
    forget_what_was_read()


_PROVIDER_SECRETS = ("OPENAI_API_KEY",)


def _configured_provider_key():
    """The provider key configured on this machine, read once and never logged."""
    path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if not path.exists():
        return ""
    import tomllib
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(loaded.get("OPENAI_API_KEY") or "")


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
    # Clearing the environment was only half of it: the docstring above already
    # said Streamlit reads the file, and it was still being read. The day a real
    # key was configured on this machine (2026-09-22) the suite started seeing
    # it, and a test that asserts what the app does without a provider failed.
    # Only the value that is actually on disk is blanked, so a test that sets a
    # fictional key on its own AppTest instance still exercises the AI path.
    on_disk = _configured_provider_key()
    if not on_disk:
        return
    import streamlit as st
    secrets_type = type(st.secrets)
    original = secrets_type.get

    def without_the_real_key(self, key, default=None):
        value = original(self, key, default)
        return "" if key in _PROVIDER_SECRETS and value == on_disk else value

    monkeypatch.setattr(secrets_type, "get", without_the_real_key, raising=False)


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


def onboarded(store, token):
    """A resident who has already been through the one-time account setup.

    Since 2026-09-23 the first thing a resident sees is the photograph
    agreement, before any encounter. That is deliberate and it is what a real
    first sign-in looks like, so a test that drives a resident *past* that
    point has to go through it the way a person would. Declining is the
    cheapest honest answer: it records the decision, stores nothing, and costs
    nothing.

    A test about the setup screen itself does not call this.
    """
    from resident_profile import ProfileStore
    ProfileStore(store).decline(token)
    return token


# PHASE2_AMENDMENT_1: the certification preview --------------------------------------------------------------------
#
# A successor of the Phase-2 closure is accepted by the runtime only once its own record says CERTIFIED, and that
# record is promoted only AFTER a green certification. So the certification run itself has to exercise the runtime
# as it will be once promoted, while the real, unpromoted lineage must go on refusing. This is how both are true:
#
#   * the preview exists ONLY here, in the test harness. No runtime module reads the flag below, so nothing outside
#     a test run can be previewed into acceptance;
#   * it does one thing: for the ONE version the flag names, a status of CANDIDATE reads as CERTIFIED. It cannot
#     invent a lineage entry, bind a record to a digest it does not state, or repair a broken historical closure;
#   * a test marked ``real_core_lineage`` always sees the real status, so the negative controls and the test of
#     the real gate are never previewed.
#
# After promotion the record itself says CERTIFIED and the flag changes nothing.
CORE_CERTIFICATION_PREVIEW_FLAG = "MRS_CORE_CERTIFICATION_PREVIEW"


def pytest_configure(config):
    config.addinivalue_line("markers", "real_core_lineage: the test reads the real certified-core lineage, never "
                                       "the certification preview")


@pytest.fixture(autouse=True, scope="session")
def _core_certification_preview():
    wanted = os.environ.get(CORE_CERTIFICATION_PREVIEW_FLAG, "").strip()
    if not wanted:
        yield
        return
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    real = ev.successor_status

    def previewed(entry):
        status = real(entry)
        return rs.CERTIFIED if entry.version_id == wanted and status == rs.CANDIDATE else status

    previewed.real = real
    ev.successor_status = previewed
    yield
    ev.successor_status = real


@pytest.fixture(autouse=True)
def _real_core_lineage(request, monkeypatch):
    if request.node.get_closest_marker("real_core_lineage") is not None:
        import runtime_shadow_evidence as ev
        real = getattr(ev.successor_status, "real", None)
        if real is not None:
            monkeypatch.setattr(ev, "successor_status", real)
    yield
