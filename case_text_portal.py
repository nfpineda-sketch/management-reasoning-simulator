"""The faculty's review of each bank case's Spanish narrative (faculty, 2026-09-26).

A case's Spanish reaches the room and the documents only once a faculty
member approves it here (``case_text``). The review is recorded with the
account that records it, names the exact version read, and a later edit to
either language shows the case as pending again.
"""
from datetime import datetime, timezone

import streamlit as st

from account_store import AccountError

SECTIONS = (
    ("/presentation", "Presentation · Presentación"),
    ("/history_source", "Who gives the history · Quién da la historia"),
    ("/history/", "History · Anamnesis"),
    ("/examination/", "Examination · Examen físico"),
    ("/investigations/", "Study reports · Informes de exámenes"),
)
STATUS = {
    "approved": "Approved · Aprobado",
    "changes_requested": "Changes requested · Cambios pedidos",
    "pending": "Pending review · Pendiente de revisión",
    "outdated": "Changed since it was approved · Cambió desde su aprobación",
}


def render_case_text_review(context):
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
    import case_text
    with st.expander("Case narrative in Spanish (faculty review) · Narrativa de los casos en español"):
        st.caption(
            "Draft Spanish of what each bank case says: the presentation, the history answers, the "
            "examination and the study reports. It reaches the room and the documents only after you "
            "approve it, case by case; until then the case stays in English, whole. Your review is recorded "
            "with your account, and an edit to either language after an approval shows the case as pending "
            "again. · Borrador en español; se usa sólo después de tu aprobación, caso por caso.")
        reviews = case_text.CaseTextReviews(context["store"])
        latest = reviews.latest()
        pack = case_text.pack_approvals()
        drafts = case_text.passages()
        if not drafts:
            st.caption("No translation is on file.")
            return
        english = case_text.current_english()
        states = {variant: case_text.status(variant, rows, latest, pack) for variant, rows in drafts.items()}
        counts = {key: sum(1 for value in states.values() if value == key) for key in STATUS}
        st.markdown(" · ".join(f"**{counts[key]}** {STATUS[key].split(' · ')[0].lower()}" for key in STATUS))
        choice = st.selectbox("Case to review · Caso a revisar", sorted(drafts),
                              format_func=lambda variant: f"{variant} · {STATUS[states[variant]]}",
                              key="_case_text_choice")
        rows = drafts[choice]
        usable = case_text.usable_rows(choice, rows, english)
        review = latest.get(choice)
        if review:
            st.caption(f"Last review: {review['decision'].replace('_', ' ')} by {review['reviewer']} "
                       f"on {_when(review['created_at'])}" + (f" — “{review['note']}”" if review.get("note") else ""))
        for prefix, title in SECTIONS:
            section = [(path, row) for path, row in rows.items() if path.startswith(prefix)]
            if not section:
                continue
            st.markdown(f"**{title}**")
            for path, row in section:
                left, right = st.columns(2)
                where = path.rsplit("/", 2)[-2:] if prefix != "/presentation" else []
                label = " · ".join(part.replace("_", " ") for part in where if not part.isdigit())
                left.caption(label) if label else None
                left.write(row.get("en", ""))
                right.write(row.get("es", "") or "—")
                if path not in usable:
                    right.caption("The English changed after this translation: it is not used until redone.")
        note = st.text_area("Note · Nota (required to request changes · necesaria para pedir cambios)",
                            key=f"_case_text_note_{choice}")
        approve, change = st.columns(2)
        if approve.button("Approve this case's Spanish · Aprobar", key=f"_case_text_approve_{choice}",
                          disabled=states[choice] == "approved"):
            reviews.record(context["token"], choice, "approved", note)
            st.success("Approved. The room and the documents use this case's Spanish from the next page load.")
        if change.button("Request changes · Pedir cambios", key=f"_case_text_changes_{choice}"):
            reviews.record(context["token"], choice, "changes_requested", note)
            st.success("Recorded. The case stays in English until its corrected Spanish is approved.")
