"""A resident's portfolio: the finalized documents of their record (cycle 9, §154AG–§154AL, §154DN, §154DO).

Only what is final: the Management Trace of each completed encounter whose
reading was saved, and each rubric assessment a faculty member confirmed, at
its latest confirmed revision. No draft, no AI proposal, no pending, rejected
or superseded assessment: the stores release nothing else. No AI Longitudinal
Review either: that is advice, not the resident's record.

The same documents for the resident and for faculty and administrators: the
resident's own PDFs, rendered by the functions the resident's page always
used. Nothing is generated anew: a Trace is re-rendered from the reading
already saved; an encounter without one says so.

Everything is read with the reader's own token, and every store checks it
again: a resident reaches only their own documents, whatever identifier a
request carries (§154EG). A document says which revision it is, in its name
and in the manifest, so a later confirmed revision never passes for an
earlier one (§154DN).

Building the complete portfolio makes no paid call: its Spanish prose uses the
translations already stored, and a passage never translated stays in English,
as the documents already say (§154DO).
"""
import hashlib
import io
import json
import time
import zipfile

import streamlit as st

from account_store import AccountError
from evidence_views import day, encounter_labels, moment
from screen_language import rows as _rows, t as _t

NOTICE = ("A copy of finalized documents from a pilot simulator: each encounter's Management Trace and every "
          "rubric assessment a faculty member confirmed. It is not a certificate, a transcript, or evidence "
          "that a workplace EPA was achieved. The rubric is a pilot instrument and its scores are not ACGME "
          "Milestone levels, Canadian stages or EPA supervision levels. Drafts, AI proposals and pending "
          "assessments are not included.")


def owner_of(context, user_id=None):
    """The resident the portfolio belongs to: the reader, or one a staff member may read."""
    user = context["user"]
    if user_id in (None, user["id"]):
        return {"id": user["id"], "username": user["username"], "training_year": user.get("training_year"),
                "active": bool(user.get("active", True))}
    from progress_store import ProgressStore
    for person in ProgressStore(context["store"]).list_residents(context["token"]):
        if person["id"] == user_id:
            return {"id": person["id"], "username": person["username"],
                    "training_year": person.get("training_year"), "active": bool(person.get("active", True))}
    raise AccountError("Your account does not have permission for this action.")


#: P-10 (faculty, 2026-09-30): an inactive account's complete portfolio is an official export for
#: delivery to its former user, and only an administrator prepares it. Faculty keep reading the
#: historical record with their usual permissions; nothing in it is removed or changed.
INACTIVE_EXPORT = ("This account is inactive: its complete portfolio, for delivery to its owner, is prepared by "
                   "an administrator. Each encounter's documents stay available above.")


def may_prepare_complete(context, owner):
    """Whether this reader may prepare the complete portfolio of ``owner``: anyone who may read it,
    except that an inactive account's is an administrator's export (P-10). The role is read from the
    store with the reader's token, not from what the page holds."""
    if owner.get("active", True):
        return True
    reader = context["store"].get_user(context["token"]) or {}
    return reader.get("role") == "admin" and bool(reader.get("active"))


def available(context, record):
    """Whether this encounter has a saved reading and a confirmed rubric. Reads only."""
    from management_trace_store import ManagementTraceStore
    from rubric_store import RubricStore
    try:
        trace = ManagementTraceStore(context["store"]).get_latest(context["token"], record["id"]) is not None
    except AccountError:
        trace = False
    try:
        review, _ = RubricStore(context["store"]).released(context["token"], record["id"])
    except AccountError:
        review = None
    return trace, review


def entries(context, user_id=None):
    """Each completed encounter of the resident and which final documents it has. Reads only."""
    owner = owner_of(context, user_id)
    token = context["token"]
    records = sorted((a for a in context["store"].list_attempts(token)
                      if a["user_id"] == owner["id"] and a["status"] == "completed" and not a["is_sandbox"]),
                     key=lambda a: a["updated_at"], reverse=True)
    rows = []
    for record in records:
        trace, review = available(context, record)
        rows.append({"record": record, "trace": trace, "review": review})
    return owner, rows


def _language(record):
    import document_language
    return document_language.default((record.get("payload") or {}).get("session"))


def _stem(record):
    return f"{day(record['created_at'])}_{record['id'][:12]}"


def documents(context, record, owner, *, translate=None, language=None, missing=None):
    """One encounter's final documents as (file name, bytes, provenance) triples.

    With a ``missing`` list, a document that cannot be rebuilt is named there and
    the other still comes; without one, the error reaches the caller.
    """
    import resident_portal
    language = language or _language(record)
    found = []

    def attempt(kind, build):
        try:
            return build()
        except (AccountError, ValueError) as error:
            if missing is None:
                raise
            missing.append({"document": kind, "encounter_id": record["id"],
                            "encounter_date": day(record["created_at"]), "reason": str(error)})
            return None
    trace = attempt("management_trace", lambda: resident_portal._trace_pdf(
        context, record, language, owner=owner, translate=translate))
    if trace:
        found.append((f"Management_Traces/{_stem(record)}_management_trace_{language}.pdf", trace, {
            "document": "management_trace", "language": language}))
    rubric, review = attempt("rubric_assessment", lambda: resident_portal._rubric_pdf(
        context, record, language, owner=owner, translate=translate)) or (None, None)
    if rubric and review:
        found.append((f"Rubrics/{_stem(record)}_rubric_revision{review['sequence']}_{language}.pdf", rubric, {
            "document": "rubric_assessment", "language": language,
            "rubric_version": review.get("rubric_version", ""), "review_id": review["review_id"],
            "review_revision": review["sequence"], "faculty_reviewer": review.get("reviewer", ""),
            "faculty_confirmed_at": day(review.get("created_at"))}))
    for name, data, provenance in found:
        provenance.update({"file": name, "encounter_id": record["id"],
                           "encounter_date": day(record["created_at"]), "resident": owner["username"],
                           "sha256": hashlib.sha256(data).hexdigest()})
    return found


def complete_zip(context, user_id=None):
    """Every final document of one resident in one ZIP, with a manifest. No paid call."""
    import prose_translation
    owner, rows = entries(context, user_id)
    if not may_prepare_complete(context, owner):
        raise AccountError("Only an administrator prepares the complete portfolio of an inactive account.")
    translate = prose_translation.stored_only(context)
    manifest, missing = [], []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        for row in rows:
            if not (row["trace"] or row["review"]):
                continue
            # A document that cannot be rebuilt does not cost the resident the rest; the manifest names it.
            for name, data, provenance in documents(context, row["record"], owner, translate=translate,
                                                    missing=missing):
                bundle.writestr(name, data)
                manifest.append(provenance)
        bundle.writestr("manifest.json", json.dumps({
            "schema": "mrs_portfolio_v1", "resident": owner["username"],
            "exported_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
            "documents": manifest, "not_included": missing, "notice": NOTICE}, ensure_ascii=False, indent=2))
        bundle.writestr("README.txt", NOTICE + "\n")
    return buffer.getvalue(), manifest


def _prepare(context, record, owner, key, language):
    """The documents of one encounter, built when asked for and kept for this session.

    Preparing them reads stored translations only; their reader asks for the rest
    (TD-41, 2026-09-29).
    """
    import prose_translation
    document_key = f"portfolio:{record['id']}:{language}"
    stored = st.session_state.get(key)
    asked_again = document_key in st.session_state.get(prose_translation.ASKED, set())
    if stored is None and (asked_again or st.button(_t("Prepare the documents"), key=key + "_prepare")):
        translation = prose_translation.for_page(context, document_key)
        try:
            stored = [(name, data) for name, data, _ in documents(context, record, owner, language=language,
                                                                  translate=translation)]
        except (AccountError, ValueError) as error:
            st.caption(str(error))
            return
        st.session_state[key] = stored
        st.session_state[key + "_translation"] = translation.status
    if stored is None:
        return
    if not stored:
        st.caption(_t("This encounter has no finalized document yet."))
    for name, data in stored:
        label = (_t("Download the Management Trace (PDF)") if name.startswith("Management_Traces/")
                 else _t("Download the confirmed rubric assessment (PDF)"))
        st.download_button(label, data, file_name=name.split("/")[-1], mime="application/pdf",
                           key=key + "_" + name)
    prose_translation.offer(st.session_state.get(key + "_translation"), document_key,
                            widget_key=key + "_translate", forget=(key,))


def render_encounter_documents(context, record, owner, key, *, has_documents=None, review=None):
    """The individual downloads of one encounter (§154AH), offered only when there is one."""
    if has_documents is None:
        trace, review = available(context, record)
        has_documents = bool(trace or review)
    if not has_documents:
        st.caption(_t("This encounter has no finalized document yet."))
        return
    # The confirmed revision is part of the key (TD-43, cycle 10): documents prepared before
    # a new rubric was confirmed are not offered as if they were current.
    revision = (review or {}).get("review_id") or "none"
    # In the language the encounter was played in, unless its reader chooses the other one
    # (faculty, 2026-09-26). Its own key: the faculty's review area has a choice of its own.
    import document_language
    written_in = document_language.choose(f"_portfolio_language_{key}_{record['id']}",
                                          (record.get("payload") or {}).get("session"))
    _prepare(context, record, owner, f"_documents_{key}_{record['id']}_{written_in}_{revision}", written_in)


def render_portfolio(context, user_id=None, *, heading=True, key="mine"):
    """The portfolio page: what it holds, each encounter's documents, and the whole of it (§154AG–§154AL)."""
    try:
        owner, rows = entries(context, user_id)
    except AccountError as error:
        st.error(str(error))
        return
    if heading:
        st.subheader(_t("My portfolio"))
    st.caption(_t("Finalized documents only: each encounter's Management Trace and every rubric assessment a "
                  "faculty member confirmed. Drafts, AI proposals and pending assessments are never part of it."))
    if not rows:
        st.info(_t("No completed encounter yet. Each one you complete adds its documents here."))
        return
    import resident_portal
    st.dataframe(_rows([{
        "Date": moment(row["record"]["created_at"]),
        "Clinical context": resident_portal._case_label(row["record"]),
        "Management Trace": _t("Available") if row["trace"] else _t("Not saved"),
        "Rubric": (_t("Confirmed (revision {v0})", v0=row["review"]["sequence"]) if row["review"]
                   else _t("Not confirmed yet")),
    } for row in rows]), hide_index=True)
    labels = encounter_labels([row["record"] for row in rows])
    labels = {row["record"]["id"]: labels[row["record"]["id"]] for row in rows}
    chosen = st.selectbox(_t("Encounter"), list(labels), format_func=labels.get, key=f"_portfolio_{key}_encounter")
    row = next(row for row in rows if row["record"]["id"] == chosen)
    render_encounter_documents(context, row["record"], owner, key,
                               has_documents=bool(row["trace"] or row["review"]), review=row["review"])
    st.markdown("**" + _t("Complete portfolio") + "**")
    st.caption(_t("One ZIP with every finalized document, in folders Management_Traces/ and Rubrics/, and a "
                  "manifest naming each document's encounter, date, reviewer and revision. Built from what is "
                  "saved: no AI call is made."))
    st.caption(_t("Each document is in the language its encounter was played in."))
    # What the ZIP holds is part of its key (TD-43, cycle 10): once another document is confirmed,
    # the ZIP prepared before it is dropped and prepared again on request, never offered as current.
    holds = hashlib.sha256(json.dumps([[row["record"]["id"], bool(row["trace"]),
                                        (row["review"] or {}).get("review_id")] for row in rows]).encode()
                           ).hexdigest()[:16]
    prefix = f"_portfolio_{key}_{owner['id']}_zip"
    zipped = f"{prefix}_{holds}"
    for stale in [name for name in list(st.session_state) if str(name).startswith(prefix + "_")
                  and not str(name).startswith(zipped)]:
        st.session_state.pop(stale, None)
    if not may_prepare_complete(context, owner):
        st.info(_t(INACTIVE_EXPORT))
        return
    if st.session_state.get(zipped) is None and st.button(_t("Prepare the complete portfolio"),
                                                          key=zipped + "_prepare"):
        try:
            st.session_state[zipped] = complete_zip(context, owner["id"])
        except (AccountError, ValueError) as error:
            st.error(str(error))
    if st.session_state.get(zipped) is not None:
        data, manifest = st.session_state[zipped]
        st.download_button(_t("Download the complete portfolio (ZIP)"), data,
                           file_name=f"portfolio_{owner['username']}.zip", mime="application/zip",
                           key=zipped + "_download")
        st.caption(_t("{v0} document(s).", v0=len(manifest)))
