"""The faculty's review of the rubric descriptors' Spanish (faculty, 2026-09-27).

A domain's Spanish reaches the rubric screen only once a faculty member
approves it here (``rubric_text``). The review is recorded with the account
that records it, names the exact version read, and a later edit to either
language shows the domain as pending again. The scores and the AI proposal
keep using the English rubric.
"""
from datetime import datetime, timezone

import streamlit as st

from account_store import AccountError

STATUS = {
    "approved": "Approved · Aprobado",
    "changes_requested": "Changes requested · Cambios pedidos",
    "pending": "Pending review · Pendiente de revisión",
    "outdated": "Changed since it was approved · Cambió desde su aprobación",
}


def render_rubric_text_review(context):
    """Faculty and administrators only."""
    if not context or (context.get("user") or {}).get("role") not in {"faculty", "admin"}:
        return
    try:
        _render(context)
    except AccountError as error:
        st.caption(str(error))


def _when(stamp):
    try:
        return datetime.fromtimestamp(int(stamp), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        return ""


def _render(context):
    import rubric_text
    from rubric import DOMAINS
    with st.expander("Rubric descriptors in Spanish (faculty review) · Descriptores de la rúbrica en español"):
        st.caption(
            "Draft Spanish of what each rubric domain asks and of its four level descriptors. It reaches the "
            "rubric screen only after you approve it, domain by domain; until then the domain reads in English, "
            "whole. The scores and the AI proposal keep using the English rubric. Your review is recorded with "
            "your account, and an edit to either language after an approval shows the domain as pending again. "
            "· Borrador en español; se usa sólo después de tu aprobación, dominio por dominio. Los puntajes y la "
            "propuesta de la IA siguen usando la rúbrica en inglés.")
        st.caption(
            "Approving this translation does not validate the instrument, nor does it show that the two "
            "languages are equivalent. · La aprobación de esta traducción no implica validación del "
            "instrumento ni equivalencia demostrada entre idiomas.")
        reviews = rubric_text.RubricTextReviews(context["store"])
        latest = reviews.latest()
        pack = rubric_text.pack_approvals()
        drafts = rubric_text.drafts()
        if not drafts:
            st.caption("No translation is on file.")
            return
        states = {domain: rubric_text.status(domain, rows, latest, pack) for domain, rows in drafts.items()}
        counts = {key: sum(1 for value in states.values() if value == key) for key in STATUS}
        st.markdown(" · ".join(f"**{counts[key]}** {STATUS[key].split(' · ')[0].lower()}" for key in STATUS))
        choice = st.selectbox("Domain to review · Dominio a revisar", sorted(drafts),
                              format_func=lambda domain: (f"{domain} · {DOMAINS[domain]['title_es']} · "
                                                          f"{STATUS[states[domain]]}"),
                              key="_rubric_text_choice")
        rows = drafts[choice]
        review = latest.get(choice)
        if review:
            st.caption(f"Last review: {review['decision'].replace('_', ' ')} by {review['reviewer']} "
                       f"on {_when(review['created_at'])}" + (f" — “{review['note']}”" if review.get("note") else ""))
        if not rubric_text.current(choice, rows):
            st.warning("The rubric's English changed after this translation: it is not used until redone. "
                       "· El inglés de la rúbrica cambió después de esta traducción: no se usa hasta rehacerla.")
        for key, row in rows.items():
            label = ("What the domain asks · Qué evalúa el dominio" if key == "asks"
                     else f"Level {key.split('/', 1)[1]} · Nivel {key.split('/', 1)[1]}")
            st.markdown(f"**{label}**")
            left, right = st.columns(2)
            left.write(row.get("en", ""))
            right.write(row.get("es", "") or "—")
        note = st.text_area("Note · Nota (required to request changes · necesaria para pedir cambios)",
                            key=f"_rubric_text_note_{choice}")
        approve, change = st.columns(2)
        if approve.button("Approve this domain's Spanish · Aprobar", key=f"_rubric_text_approve_{choice}",
                          disabled=states[choice] == "approved"):
            reviews.record(context["token"], choice, "approved", note)
            st.success("Approved. The rubric screen uses this domain's Spanish from the next page load.")
        if change.button("Request changes · Pedir cambios", key=f"_rubric_text_changes_{choice}"):
            reviews.record(context["token"], choice, "changes_requested", note)
            st.success("Recorded. The domain stays in English until its corrected Spanish is approved.")
