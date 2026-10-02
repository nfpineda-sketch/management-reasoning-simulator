"""What the simulator cannot show or treat in a case, shown where the faculty judges the encounter.

Pre-pilot closure (2026-10-02, D-3 and D-8). The limits are the case's own declaration
(``engine_limits``), read from the copy the encounter froze when it started
(``evaluation_basis``), so a later change to the case never changes what an earlier
encounter is read against. The rubric (``rubric_portal``) and the objectives
(``progress_portal``) show them the same way, and neither portal imports the other:
the evidence is read against them, a resident is never charged for them, and a measure
written for one of them is never an omission.
"""
import streamlit as st

import evaluation_basis
from screen_language import t as _t


def render(record, case_id):
    """The frozen limits of this encounter's case, or nothing when it declares none."""
    declaration = evaluation_basis.resolve(record)["declaration"] if case_id else None
    limits = tuple((declaration or {}).get("engine_limits") or ())
    if not limits:
        return
    st.markdown("**" + _t("What the simulator cannot show or treat in this case") + "**")
    st.caption(_t("Never count these against the resident: what the simulator cannot show is not evidence, "
                  "and a measure written for it is not an omission."))
    for limit in limits:
        # The declaration's own words, as frozen with the encounter.
        st.caption("· " + str(limit))
