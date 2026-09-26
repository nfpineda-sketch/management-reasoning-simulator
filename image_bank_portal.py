"""The image bank for faculty and administrators: what exists, what it cost, and the reviews (2026-09-26).

The automated screen is not an approval. The two reviews that are -- a
person's visual review and the clinical review -- are recorded here, with the
account of whoever records them; nothing marks them for anyone else. An image
can be excluded (and brought back) with its reason, and stays in the record.
"""
from __future__ import annotations

import streamlit as st

from account_store import AccountError

_SCREEN = {"accepted": "Accepted", "accepted_with_limitations": "Accepted, with limitations",
           "rejected": "Rejected", "not_screened": "Not screened yet"}
_REVIEW = {"pending": "Pending", "approved": "Approved", "rejected": "Rejected"}
_LIMITS = {"mild_skin_moisture": "mild sweat not discernible", "mild_skin_color": "mild pallor not discernible",
           "breathing_effort": "breathing effort not discernible"}


def _dollars(micro):
    # Escaped: Streamlit's markdown reads the text between two dollar signs as a
    # formula, and the budget line came out as one in a browser (2026-09-26).
    from image_pricing import usd
    return f"US\\${usd(micro):.2f}"


def _state_line(contract):
    parts = [contract.get("mental_status", ""), contract.get("expression", ""),
             f"sweat {contract.get('diaphoresis', '')}", contract.get("skin_color", ""),
             f"breathing {contract.get('work_of_breathing', '')}"]
    if contract.get("mottling"):
        parts.append("mottling")
    support = contract.get("respiratory_support", "none")
    parts.append("no respiratory support" if support == "none" else support)
    return " · ".join(part for part in parts if part)


def render_image_bank(context):
    """Faculty and administrators: the bank, its budget, and the two human reviews."""
    try:
        _render_image_bank(context)
    except AccountError as error:
        # The rest of the dashboard stays usable when the bank cannot be read.
        st.caption(str(error))


def _render_image_bank(context):
    from image_bank import ImageBank
    from image_identities import BY_ID, describe
    from image_pricing import configured_budget
    from image_selection import usable
    import image_pack
    from clinical_scene import setting
    with st.expander("Patient image bank (faculty)"):
        st.caption("Synthetic people and the photographs the encounter room shows. The automated screen is a "
                   "check, not an approval: the visual and clinical reviews below are recorded with the "
                   "account that records them. Nothing here is a real patient.")
        try:
            bank = ImageBank(context["store"])
            image_pack.ensure_imported(bank)
            budget = configured_budget(setting)
            summary = bank.budget_summary(budget)
            assets = bank.assets()
        except (AccountError, ValueError) as error:
            st.caption(str(error))
            return
        st.markdown(
            f"**Budget `{summary['budget_id']}`** · committed {_dollars(summary['committed'])} of "
            f"{_dollars(summary['limit_micro'])} ({_dollars(summary['from_usage'])} from the provider's "
            f"reported usage, {_dollars(summary['estimated'])} estimated, {_dollars(summary['in_flight'])} "
            f"reserved in flight) · image requests {summary['requests']} of {summary['limit_requests']} · "
            f"retries {summary['retries']}")
        show_all = st.toggle("Show rejected and excluded images too", value=False, key="_image_bank_all")
        by_person = {}
        for asset in assets:
            by_person.setdefault(asset["identity_id"], []).append(asset)
        if not by_person:
            st.caption("The bank is empty.")
            return
        choices = []
        for person_id in sorted(by_person):
            person = BY_ID.get(person_id)
            st.markdown(f"**{person_id}** · {describe(person) if person else 'unknown identity'}")
            shown = [a for a in sorted(by_person[person_id], key=lambda a: (a["role"] != "anchor", a["created_at"]))
                     if show_all or usable(a)]
            if not shown:
                st.caption("No usable photograph of this person.")
                continue
            columns = st.columns(3)
            for index, asset in enumerate(shown):
                with columns[index % 3]:
                    raw = bank.blob(asset["display_sha256"])
                    if raw is not None:
                        st.image(raw, width="stretch")
                    limitations = ", ".join(_LIMITS.get(item, item) for item in
                                            (asset.get("screen_details") or {}).get("limitations", []))
                    st.caption(
                        f"{'Anchor' if asset['role'] == 'anchor' else 'State'} · {_state_line(asset['contract'])}  \n"
                        f"Screen: {_SCREEN.get(asset['screen'], asset['screen'])}"
                        f"{' (' + limitations + ')' if limitations else ''} · visual review "
                        f"{_REVIEW.get(asset['visual_review'], asset['visual_review'])} · clinical review "
                        f"{_REVIEW.get(asset['clinical_review'], asset['clinical_review'])}"
                        + ("  \nIn use: approved in the visual and clinical reviews over the automated screen"
                           if asset["excluded"] and usable(asset) else
                           f"  \nExcluded: {asset['exclusion_reason']}" if asset["excluded"] else "")
                        + "".join(f"  \nScreen found: {item.get('finding', '')}"
                                  for item in (asset.get("screen_details") or {}).get("evidence", []))
                        + f"  \n`{asset['id'][:10]}` · {asset['generation'].get('model', '')} · "
                          f"{(asset['generation'].get('versions') or {}).get('prompt', '')}")
                    choices.append(asset)
        if not choices:
            return
        with st.form("_image_bank_review", clear_on_submit=True):
            chosen = st.selectbox("Image", [a["id"] for a in choices],
                                  format_func=lambda key: next(f"{a['identity_id']} · {key[:10]} · "
                                                               f"{_state_line(a['contract'])}"
                                                               for a in choices if a["id"] == key))
            action = st.radio("Record", ["Visual review", "Clinical review", "Exclude", "Bring back"],
                              horizontal=True)
            decision = st.radio("Decision (for a review)", ["approved", "rejected", "pending"], horizontal=True)
            note = st.text_area("What you looked at and why", max_chars=1000)
            if st.form_submit_button("Record"):
                try:
                    if action == "Visual review":
                        bank.review(context["token"], chosen, "visual_review", decision, note)
                    elif action == "Clinical review":
                        bank.review(context["token"], chosen, "clinical_review", decision, note)
                    else:
                        bank.exclude(context["token"], chosen, note, excluded=action == "Exclude")
                    st.success("Recorded with your account.")
                except AccountError as error:
                    st.error(str(error))


def render_image_record(context, record):
    """Faculty review of one encounter: which photograph the room showed, when, or why none."""
    from image_bank import ImageBank
    try:
        rows = ImageBank(context["store"]).displays(context["token"], record["id"])
    except AccountError:
        return
    if not rows:
        return
    with st.expander(f"Patient image · what the room showed ({len(rows)})"):
        st.caption("Each change in what the encounter room showed. Without a photograph the room showed its "
                   "neutral view, with the monitor and the examination current; a finding the photograph "
                   "could not show was stated beside it.")
        st.dataframe([{
            "Minute": row["sim_time"], "Shown": {"image": "Photograph", "pending": "Being prepared",
                                                 "failed": "None (failed)", "unavailable": "None"}[row["outcome"]],
            "Why none": row["code"], "Person": row["identity_id"], "State": _state_line(row["contract"]),
            "Not discernible": ", ".join(_LIMITS.get(item, item) for item in row["limitations"]),
        } for row in rows], hide_index=True)
