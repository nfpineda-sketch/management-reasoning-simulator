"""How an encounter ended, as the resident says it ended.

Faculty decision 9 of 2026-09-25 ("Cierre temprano: opción B"). Closing without
a destination gets a brief warning that never blocks -- "No has registrado un
destino. ¿Quieres continuar o finalizar?" -- and the kind of close is recorded:
a clinical close, an interruption, or an early finish. Nothing here invents a
destination, and nothing erases an omission the record already showed before
the close: the trace is frozen exactly as it stood.
"""
from __future__ import annotations

KINDS = ("clinical_close", "interruption", "early_finish")
LABELS = {
    "clinical_close": "Clinical close: my management is complete",
    "interruption": "Interruption: I have to stop here",
    "early_finish": "Early finish: I am ending before its natural end",
}
WARNING = "You have not recorded a destination. Do you want to continue or finish?"


def has_destination(trace, state):
    """Whether a destination stands at the close: the engine's, or the record's."""
    if isinstance(state, dict) and "disposition" in state:
        return bool(state.get("disposition"))
    return any(summary.get("type") == "disposition"
               for entry in trace or [] if entry.get("execution_status") == "executed"
               for summary in entry.get("action_summaries") or [] if isinstance(summary, dict))


def record(kind, *, destination_recorded, warned, minute):
    if kind not in KINDS:
        raise ValueError(f"Unknown kind of close: {kind!r}")
    return {"kind": kind, "destination_recorded": bool(destination_recorded), "warned": bool(warned),
            "at_min": minute}
