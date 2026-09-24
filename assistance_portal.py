"""The resident's own word about help received, asked once, at the close.

Faculty specification of 2026-09-24, section 3. One short question when the
encounter closes -- no external help, external help, or not reported -- with
room to say what the help was and which decisions it touched. It never stands
between the resident and a clinical decision, never blocks closing, saving or
the documents, and can be answered or changed later; every answer is kept.
"""
from __future__ import annotations

import os

import streamlit as st

from account_store import AccountError


def _secret(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.environ.get(name, "") or "").strip()


def synthetic_accounts():
    """Test accounts allowed to say "this run was an automated agent's".

    ``MRS_SYNTHETIC_ACCOUNTS``, comma-separated usernames. A synthetic run is
    recorded as the execution of a test, apart from the assistance context,
    and demonstrates nothing about a resident's autonomy.
    """
    return {name.strip() for name in _secret("MRS_SYNTHETIC_ACCOUNTS").split(",") if name.strip()}


_TEXT = {
    "en": {
        "title": "Did you receive any external help during this encounter?",
        "why": ("Optional, and it blocks nothing: you can close, reflect and download your documents "
                "without answering, and change it later. External help means someone or something "
                "outside the simulator guiding your decisions -- a colleague, a teacher, a reference "
                "you looked up. The simulator's own questions to complete your reasoning do not count."),
        "choice": "Help received", "what": "What help (optional)",
        "which": "Decisions it influenced (optional)",
        "synthetic": "This encounter was run by an automated agent (synthetic test)",
        "save": "Save my answer", "saved": "Saved. You can change it at any time; every answer is kept.",
        "current": "Your current answer: {label}.", "none_yet": "Not answered yet.",
        "choose": "Choose an answer, or simply leave this question.",
    },
    "es": {
        "title": "¿Recibiste ayuda externa durante este encuentro?",
        "why": ("Es opcional y no bloquea nada: puedes cerrar, reflexionar y descargar tus documentos "
                "sin responder, y cambiarlo después. Ayuda externa es alguien o algo fuera del "
                "simulador que orientó tus decisiones: un compañero, un docente, una referencia que "
                "consultaste. Las preguntas del propio simulador para completar tu razonamiento no "
                "cuentan."),
        "choice": "Ayuda recibida", "what": "¿Qué ayuda? (opcional)",
        "which": "Decisiones en que influyó (opcional)",
        "synthetic": "Este encuentro lo ejecutó un agente automatizado (prueba sintética)",
        "save": "Guardar mi respuesta",
        "saved": "Guardado. Puedes cambiarlo cuando quieras; cada respuesta queda registrada.",
        "current": "Tu respuesta actual: {label}.", "none_yet": "Todavía sin responder.",
        "choose": "Elige una respuesta, o simplemente deja esta pregunta.",
    },
}


def render_closing_question(context, attempt_id, trace, *, language="en"):
    """The question, in a bordered box beside the review. Returns the current declaration."""
    if not context or not attempt_id:
        return None
    import encounter_context
    from objectives import evidence_items
    words = _TEXT["es" if language == "es" else "en"]
    lang = "es" if language == "es" else "en"
    store = encounter_context.EncounterContextStore(context["store"])
    try:
        current = store.current(context["token"], attempt_id)
    except AccountError:
        return None
    decisions = {item["ref"]: item["label"] for item in
                 evidence_items({"session": {"management_trace": trace or []}})
                 if item["kind"] == "decision"}
    test_account = context["user"].get("username") in synthetic_accounts()
    with st.container(border=True):
        st.markdown("**" + words["title"] + "**")
        st.caption(words["why"])
        if current["assistance"]:
            st.caption(words["current"].format(
                label=encounter_context.label("assistance", current["assistance"]["value"], lang)))
        else:
            st.caption(words["none_yet"])
        with st.form("closing_assistance_" + attempt_id):
            choice = st.radio(words["choice"], list(encounter_context.ASSISTANCE), index=None,
                              format_func=lambda key: encounter_context.label("assistance", key, lang),
                              horizontal=True)
            description = st.text_area(words["what"], max_chars=1000)
            affected = st.multiselect(words["which"], list(decisions), format_func=decisions.get)
            synthetic = st.checkbox(words["synthetic"]) if test_account else False
            submitted = st.form_submit_button(words["save"])
        if submitted:
            if choice is None and not synthetic:
                st.info(words["choose"])
                return current
            try:
                if choice is not None:
                    store.declare(context["token"], attempt_id, value=choice,
                                  description=description if choice == "external_help" else "",
                                  affected_refs=affected if choice == "external_help" else ())
                if synthetic and current["execution"] is None:
                    store.declare(context["token"], attempt_id, field="execution",
                                  value="synthetic_agent", synthetic_accounts=synthetic_accounts())
            except AccountError as error:
                st.warning(str(error))
                return current
            st.success(words["saved"])
            current = store.current(context["token"], attempt_id)
    return current
