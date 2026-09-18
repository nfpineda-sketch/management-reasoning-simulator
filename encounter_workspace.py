"""Read-only encounter presentation; source text and event order are preserved."""
import streamlit as st


def encounter_sections(events):
    """Group existing events without inventing patient speech or clinical facts.

    The latest exchange begins at the most recent learner submission. Results
    remain in both that exchange and the complete chronological record.
    """
    events = list(events)
    arrival = [event for event in events if event.get("kind") == "presentation"]
    exchanges = [event for event in events if event.get("kind") != "presentation"]
    latest_start = max(
        (index for index, event in enumerate(exchanges) if event.get("kind") == "you"),
        default=0,
    )
    results = [event for event in events if event.get("kind") == "diagnostic_result"]
    return arrival, exchanges[latest_start:], results, events


def render_encounter_workspace(events, render_event):
    arrival, latest, results, record = encounter_sections(events)
    st.subheader("Clinical Encounter")
    with st.container(border=True):
        st.markdown("#### Arrival & handover")
        st.caption("At arrival · the bedside monitor shows the current observations.")
        for event in arrival:
            st.write(event["text"])
        if not arrival:
            st.caption("No arrival note is recorded for this encounter.")

    bedside, investigations, chart = st.tabs([
        "Current exchange", "Investigation reports", "Complete encounter record",
    ])
    with bedside:
        if latest:
            for event in latest:
                render_event(event)
        else:
            st.write("You are at the bedside. Assess the patient and enter your questions, orders, or management below.")
    with investigations:
        st.caption("All reports received during this encounter, in time order. Earlier reports describe the patient at that time.")
        if not results:
            st.write("No investigation reports have been received yet.")
        for event in results:
            render_event(event)
    with chart:
        st.caption("The complete record, including your entries and all patient updates.")
        for event in record:
            render_event(event)
