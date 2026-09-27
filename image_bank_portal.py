"""The image bank for faculty and administrators: what exists, what it cost, and the reviews (2026-09-26).

The automated screen is not an approval. The two reviews that are -- a
person's visual review and the clinical review -- are recorded here, with the
account of whoever records them; nothing marks them for anyone else. An image
can be excluded (and brought back) with its reason, and stays in the record.
"""
from __future__ import annotations

import streamlit as st

from account_store import AccountError
from screen_language import rows as _rows, t as _t

_SCREEN = {"accepted": "Accepted", "accepted_with_limitations": "Accepted, with limitations",
           "rejected": "Rejected", "not_screened": "Not screened yet"}
_REVIEW = {"pending": "Pending", "approved": "Approved", "rejected": "Rejected"}
_LIMITS = {"mild_skin_moisture": "mild sweat not discernible", "mild_skin_color": "mild pallor not discernible",
           "breathing_effort": "breathing effort not discernible", "skin_color": "skin colour not shown",
           "sweating": "sweating not shown", "distress": "degree of distress not shown",
           "consciousness": "level of consciousness not shown"}


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
    with st.expander(_t("Patient image bank (faculty)")):
        st.caption(_t("Synthetic people and the photographs the encounter room shows. The automated screen is a "
                   "check, not an approval: the visual and clinical reviews below are recorded with the "
                   "account that records them. Nothing here is a real patient."))
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
            _t("**Budget `{v0}`** · committed {v1} of {v2} ({v3} from the provider's reported usage, {v4} estimated, {v5} reserved in flight) · image requests {v6} of {v7} · retries {v8}", v0=summary['budget_id'], v1=_dollars(summary['committed']), v2=_dollars(summary['limit_micro']), v3=_dollars(summary['from_usage']), v4=_dollars(summary['estimated']), v5=_dollars(summary['in_flight']), v6=summary['requests'], v7=summary['limit_requests'], v8=summary['retries']))
        # Every other authorization recorded here, such as the reviewed batches run
        # outside the app: its spending is in the same ledger and stays visible.
        for other in bank.budgets():
            if other["id"] == summary["budget_id"]:
                continue
            spent = bank.budget_summary(other)
            st.markdown(
                _t("Budget `{v0}` (not the one this app spends from) · committed {v1} of {v2} ({v3} from the provider's reported usage, {v4} estimated) · image requests {v5} of {v6} · retries {v7}", v0=other['id'], v1=_dollars(spent['committed']), v2=_dollars(spent['limit_micro']), v3=_dollars(spent['from_usage']), v4=_dollars(spent['estimated']), v5=spent['requests'], v6=spent['limit_requests'], v7=spent['retries']))
        show_all = st.toggle(_t("Show rejected and excluded images too"), value=False, key="_image_bank_all")
        observed = image_pack.read_observations()
        by_person = {}
        for asset in assets:
            by_person.setdefault(asset["identity_id"], []).append(asset)
        if not by_person:
            st.caption(_t("The bank is empty."))
            return
        choices = []
        for person_id in sorted(by_person):
            person = BY_ID.get(person_id)
            st.markdown(f"**{person_id}** · {describe(person) if person else _t('unknown identity')}")
            shown = [a for a in sorted(by_person[person_id], key=lambda a: (a["role"] != "anchor", a["created_at"]))
                     if show_all or usable(a)]
            if not shown:
                st.caption(_t("No usable photograph of this person."))
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
                        _t('{v0} · {v1}  \nScreen: {v2}{v3} · visual review {v4} · clinical review {v5}', v0=_t('Anchor' if asset['role'] == 'anchor' else 'State'), v1=_state_line(asset['contract']), v2=_SCREEN.get(asset['screen'], asset['screen']), v3=' (' + limitations + ')' if limitations else '', v4=_REVIEW.get(asset['visual_review'], asset['visual_review']), v5=_REVIEW.get(asset['clinical_review'], asset['clinical_review']))
                        + ("  \n" + _t("In use: approved in the visual and clinical reviews over the automated screen")
                           if asset["excluded"] and usable(asset) else
                           "  \n" + _t("Excluded: ") + str(asset['exclusion_reason']) if asset["excluded"] else "")
                        + "".join("  \n" + _t("Screen found: ") + str(item.get('finding', ''))
                                  for item in (asset.get("screen_details") or {}).get("evidence", []))
                        + ("  \n" + _t("Not shown, on a reading of the photograph (not a review): ")
                           + ', '.join(_LIMITS[code] for code in observed.get(asset['id'], ()))
                           if observed.get(asset["id"]) else "")
                        + f"  \n`{asset['id'][:10]}` · {asset['generation'].get('model', '')} · "
                          f"{(asset['generation'].get('versions') or {}).get('prompt', '')}")
                    choices.append(asset)
        if not choices:
            return
        with st.form("_image_bank_review", clear_on_submit=True):
            chosen = st.selectbox(_t("Image"), [a["id"] for a in choices],
                                  format_func=lambda key: next(f"{a['identity_id']} · {key[:10]} · "
                                                               f"{_state_line(a['contract'])}"
                                                               for a in choices if a["id"] == key))
            action = st.radio(_t("Record"), ["Visual review", "Clinical review", "Exclude", "Bring back"], format_func=_t,
                              horizontal=True)
            decision = st.radio(_t("Decision (for a review)"), ["approved", "rejected", "pending"], horizontal=True)
            note = st.text_area(_t("What you looked at and why"), max_chars=1000)
            if st.form_submit_button(_t("Record")):
                try:
                    if action == "Visual review":
                        bank.review(context["token"], chosen, "visual_review", decision, note)
                    elif action == "Clinical review":
                        bank.review(context["token"], chosen, "clinical_review", decision, note)
                    else:
                        bank.exclude(context["token"], chosen, note, excluded=action == "Exclude")
                    st.success(_t("Recorded with your account."))
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
    with st.expander(_t('Patient image · what the room showed ({v0})', v0=len(rows))):
        st.caption(_t("Each change in what the encounter room showed. Without a photograph the room showed its "
                   "neutral view, with the monitor and the examination current; a finding the photograph "
                   "could not show was stated beside it."))
        st.dataframe(_rows([{
            "Minute": row["sim_time"], "Shown": _t({"image": "Photograph", "pending": "Being prepared",
                                                    "failed": "None (failed)", "unavailable": "None"}[row["outcome"]]),
            "Why none": row["code"], "Person": row["identity_id"], "State": _state_line(row["contract"]),
            "Not discernible": ", ".join(_LIMITS.get(item, item) for item in row["limitations"]),
        } for row in rows]), hide_index=True)
