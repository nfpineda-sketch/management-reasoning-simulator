import streamlit as st

st.set_page_config(page_title="Streamlit rerun isolation test", layout="wide")

if "repro_count" not in st.session_state:
    st.session_state.repro_count = 0
    st.session_state.repro_history = []

def _send():
    st.session_state.repro_count += 1
    n = st.session_state.repro_count
    st.session_state.repro_history.append(
        {"n": n, "hr": 100 + n, "bp": f"{120-n}/{75-n}", "rr": 28 + n, "spo2": 92 - n}
    )

st.sidebar.write("Minimal Streamlit rerun reproduction")
st.sidebar.write("No simulator code runs on this branch.")

@st.fragment(key="encounter")
def encounter():
    n = st.session_state.repro_count
    current = (
        st.session_state.repro_history[-1]
        if st.session_state.repro_history
        else {"n": 0, "hr": 100, "bp": "120/75", "rr": 28, "spo2": 92}
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("### BEDSIDE MONITOR")
        st.metric("HR", current["hr"])
        st.metric("SpO₂", current["spo2"])
        st.metric("BP", current["bp"])
        st.metric("RR", current["rr"])

    with right:
        st.markdown("## Management")
        st.radio("Encounter", ["Talk", "Examine", "Tests", "Treat"], index=3, horizontal=True, key="mode")
        if st.session_state.repro_history:
            st.success(
                f'PATIENT RESPONSE #{current["n"]}: HR {current["hr"]}, '
                f'BP {current["bp"]}, SpO₂ {current["spo2"]}, RR {current["rr"]}'
            )

        with st.form("repro_form", clear_on_submit=False):
            st.text_area(
                "Order",
                value="Reassess.",
                key="repro_order",
                label_visibility="collapsed",
            )
            st.form_submit_button("Send", on_click=_send)

    st.caption(f"Fragment render count state: {n}")

encounter()

st.info(
    "Test: click Send 10 times. Expected: exactly one bedside, one Management block, "
    "one form, and the response number increments by one each click."
)
