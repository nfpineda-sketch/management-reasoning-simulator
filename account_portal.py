"""English account UI for the simulator's optional persistent account mode.

The legacy shared-password gate remains the default in ``app.py``. Selecting
``MRS_AUTH_MODE = "accounts"`` replaces it with this gate; configuration errors
never fall through to shared or anonymous access. Roles are read from the store
for every rerun and administrative mutations also require authorization there.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st

from account_store import AccountError, AccountStore


_TOKEN_KEY = "_account_token"
_IDENTITY_KEY = "_account_user_id"
_ROLES = ("resident", "faculty", "admin")


def _setting(name: str, default: str = "") -> str:
    """Read only named configuration; missing Streamlit secrets are normal locally."""
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None
    if value is None:
        value = os.environ.get(name, default)
    return str(value).strip()


def _closed(message: str) -> None:
    st.title("Management Reasoning Simulator")
    st.error(message)
    st.stop()


def accounts_enabled() -> bool:
    """Return the selected gate, failing closed for a misspelled or unknown mode."""
    mode = _setting("MRS_AUTH_MODE", "shared").lower()
    if mode not in ("shared", "accounts"):
        _closed("Access is temporarily closed. The account mode is not configured correctly.")
    return mode == "accounts"


def _on_streamlit_cloud() -> bool:
    # Community Cloud runs repository checkouts beneath /mount/src. Local SQLite
    # is only a development option because that cloud filesystem is ephemeral.
    cloud_values = ("1", "true", "yes")
    return (
        str(Path.cwd()).startswith("/mount/src/")
        or str(Path(__file__).resolve()).startswith("/mount/src/")
        or os.environ.get("STREAMLIT_CLOUD", "").lower() in cloud_values
        or os.environ.get("STREAMLIT_SHARING", "").lower() in cloud_values
    )


def _clear_identity() -> None:
    """Remove the whole clinical session as well as credentials and role caches."""
    st.session_state.clear()


def _start_session(token: str, user: dict[str, Any]) -> None:
    _clear_identity()
    st.session_state[_TOKEN_KEY] = token
    st.session_state[_IDENTITY_KEY] = user["id"]
    st.rerun()


@st.cache_resource(show_spinner=False)
def _configured_store(url: str, allow_sqlite: bool, username: str, password_hash: str) -> AccountStore:
    """Cache connection configuration only; identities and permissions are never cached.

    AccountStore opens a separate transaction/connection for each operation and
    holds no session-specific state. This avoids running schema initialization
    on every Streamlit rerun without sharing a learner's authentication result.
    """
    store = AccountStore(url, allow_sqlite=allow_sqlite)
    if username and password_hash:
        store.bootstrap_admin(username, password_hash)
    return store


def _open_store() -> AccountStore:
    url = _setting("MRS_DATABASE_URL")
    if not url:
        _closed("Account access is temporarily unavailable. Ask the administrator to configure persistent account storage.")
    allow_sqlite = _setting("MRS_ALLOW_LOCAL_SQLITE", "false").lower() in ("1", "true", "yes")
    if url.lower().startswith("sqlite:") and (not allow_sqlite or _on_streamlit_cloud()):
        _closed("Account access requires persistent database storage. Local test storage is not enabled for this deployment.")
    username = _setting("MRS_ADMIN_USERNAME")
    password_hash = _setting("MRS_ADMIN_PASSWORD_HASH")
    if bool(username) != bool(password_hash):
        _closed("Account access is temporarily unavailable. The administrator account configuration is incomplete.")
    try:
        return _configured_store(url, allow_sqlite and not _on_streamlit_cloud(), username, password_hash)
    except Exception:
        # Database exceptions may contain connection strings or credentials.
        # Never show exception text, repr, traceback, or secrets to the browser.
        _closed("Account access is temporarily unavailable. Please contact the application administrator.")


def require_account_access() -> dict[str, Any]:
    """Render a login gate or return an authenticated store, token, and user.

    Call this before rendering any clinical data or privileged controls. An
    expired, revoked, deactivated, or identity-mismatched session loses all local
    clinical state before another account can enter.
    """
    if not accounts_enabled():
        _closed("Individual accounts are not enabled for this deployment.")
    store = _open_store()
    token = st.session_state.get(_TOKEN_KEY)
    if token:
        try:
            user = store.get_user(token)
        except Exception:
            _closed("Account access is temporarily unavailable. Please try again later.")
        if user and user.get("active") and user.get("role") in _ROLES:
            known_id = st.session_state.get(_IDENTITY_KEY)
            if known_id is not None and known_id != user["id"]:
                _clear_identity()
            else:
                st.session_state[_IDENTITY_KEY] = user["id"]
                return {"store": store, "token": token, "user": user}
        else:
            _clear_identity()
        st.warning("Your session has ended. Please sign in again.")

    st.title("Management Reasoning Simulator")
    st.caption("Sign in to continue your training. New accounts require an invitation.")
    sign_in, register = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("account_login", clear_on_submit=True):
            username = st.text_input("Username", max_chars=80)
            password = st.text_input("Password", type="password", max_chars=256)
            submit = st.form_submit_button("Sign in", type="primary")
        if submit:
            try:
                new_token = store.authenticate(username, password)
                user = store.get_user(new_token)
                if not user:
                    raise AccountError("Sign in failed.")
            except AccountError:
                st.error("Unable to sign in. Check your credentials or try again later.")
            except Exception:
                st.error("Account access is temporarily unavailable. Please try again later.")
            else:
                _start_session(new_token, user)
    with register:
        with st.form("account_register", clear_on_submit=True):
            invite = st.text_input("Invitation code", type="password", max_chars=256)
            new_username = st.text_input("Choose a username", max_chars=80)
            new_password = st.text_input("Choose a password", type="password", max_chars=256)
            confirmed_password = st.text_input("Confirm password", type="password", max_chars=256)
            st.caption("Use a unique password with at least 12 characters. Your invitation determines your role and training year.")
            create = st.form_submit_button("Create account", type="primary")
        if create:
            if new_password != confirmed_password:
                st.error("The passwords do not match.")
            elif len(new_password) < 12:
                st.error("Choose a password with at least 12 characters.")
            else:
                try:
                    new_token = store.register(new_username, new_password, invite)
                    user = store.get_user(new_token)
                    if not user:
                        raise AccountError("Registration failed.")
                except AccountError:
                    st.error("Unable to create this account. Check that your username is available and your invitation is valid.")
                except Exception:
                    st.error("Account access is temporarily unavailable. Please try again later.")
                else:
                    _start_session(new_token, user)
    st.stop()


def _sign_out(context: dict[str, Any]) -> None:
    try:
        context["store"].revoke_session(context["token"])
    except Exception:
        # Local credential removal must succeed even during a database outage.
        pass
    _clear_identity()
    st.rerun()


def _render_admin_controls(context: dict[str, Any]) -> None:
    store, token = context["store"], context["token"]
    with st.sidebar.expander("Account administration"):
        st.caption("Invitations define access privileges. Send each invitation privately to its intended user.")
        with st.form("account_invite", clear_on_submit=True):
            role = st.selectbox("Invite role", _ROLES)
            year = st.selectbox("Training year", (1, 2, 3), key="_invite_year")
            create_invite = st.form_submit_button("Create invitation")
        if create_invite:
            try:
                invitation = store.create_invite(token, role, int(year))
            except AccountError:
                st.error("Unable to create an invitation. Check your administrator access.")
            except Exception:
                st.error("Account storage is temporarily unavailable.")
            else:
                st.session_state["_created_account_invite"] = invitation
        if st.session_state.get("_created_account_invite"):
            st.caption("Copy this invitation and share it privately:")
            st.code(st.session_state["_created_account_invite"], language=None)
            if st.button("Hide invitation", key="_hide_account_invite"):
                del st.session_state["_created_account_invite"]
                st.rerun()

        try:
            users = store.list_users(token)
        except AccountError:
            st.error("Administrator access is required to manage accounts.")
            return
        except Exception:
            st.error("Account storage is temporarily unavailable.")
            return
        if not users:
            return
        users_by_id = {user["id"]: user for user in users}
        selected_id = st.selectbox(
            "Manage an account", list(users_by_id),
            format_func=lambda user_id: str(users_by_id[user_id]["username"]),
            key="_managed_account_id",
        )
        selected = users_by_id[selected_id]
        # The user-specific form key prevents another account's values from
        # lingering in role/year widgets when the selection changes.
        with st.form(f"account_edit_{selected_id}"):
            selected_role = st.selectbox("Role", _ROLES, index=_ROLES.index(selected["role"]))
            selected_year = st.selectbox("Resident year", (1, 2, 3), index=max(0, min(2, int(selected.get("training_year") or 1) - 1)))
            selected_active = st.checkbox("Account active", value=bool(selected.get("active")))
            st.caption("Changing access invalidates this user's existing sessions.")
            save = st.form_submit_button("Save account")
        if save:
            try:
                store.update_user(token, selected_id, role=selected_role, training_year=int(selected_year), active=selected_active)
            except AccountError:
                st.error("Unable to update this account. At least one active administrator must remain.")
            except Exception:
                st.error("Account storage is temporarily unavailable.")
            else:
                if selected_id == context["user"]["id"]:
                    _clear_identity()
                else:
                    st.session_state["_account_admin_notice"] = "Account updated. The user must sign in again."
                st.rerun()


def render_account_sidebar(context: dict[str, Any]) -> None:
    """Show identity and role-appropriate account controls after the access gate."""
    user = context["user"]
    st.sidebar.caption("Signed in")
    st.sidebar.write(str(user["username"]))
    st.sidebar.caption(str(user["role"]).capitalize())
    if st.sidebar.button("Sign out", key="_account_sign_out"):
        _sign_out(context)
    if user["role"] == "admin":
        if st.session_state.get("_account_admin_notice"):
            st.sidebar.success(st.session_state.pop("_account_admin_notice"))
        _render_admin_controls(context)
