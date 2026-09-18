"""Learner-safe progress for the bounded case preparation pipeline."""
from contextlib import contextmanager
from time import monotonic


STAGE_LABELS = {
    "author": "Creating your patient",
    "validation": "Checking the clinical scenario",
    "correction": "Refining the clinical scenario",
    "review": "Reviewing clinical consistency",
    "complete": "Your encounter is ready",
}


@contextmanager
def encounter_preparation(st):
    """Show fixed stage labels only; never render generated clinical content.

    The elapsed time is updated at stage transitions. Long provider requests
    remain visibly running rather than implying a continuously ticking timer.
    Exceptions are rendered by the caller's existing safe error boundary.
    """
    started = monotonic()
    status = st.status("Preparing your encounter", state="running", expanded=True)
    status.write("Preparation can take a few minutes. The current stage appears below.")
    previous = None

    def progress(stage):
        nonlocal previous
        if not isinstance(stage, str):
            return
        label = STAGE_LABELS.get(stage)
        if label is None or stage == previous:
            return
        previous = stage
        elapsed = max(0, int(monotonic() - started))
        status.write(f"{label} · {elapsed}s elapsed")
        status.update(label=label, state="running")

    try:
        yield progress
    except Exception:
        status.update(label="Encounter preparation stopped", state="error", expanded=False)
        raise
    else:
        status.update(label="Your encounter is ready", state="complete", expanded=False)
