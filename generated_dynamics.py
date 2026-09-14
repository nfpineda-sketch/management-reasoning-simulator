"""Case-authored state coupling and gradual replacement of active drug effects."""
from copy import deepcopy
from generated_response import response_progress

INFUSIONS = {"norepinephrine", "dobutamine", "nitroglycerin"}


def event_progress(event, elapsed):
    if event.get("withdrawal"):
        return max(0.0, 1 - (elapsed - event["started_at"]) / event["duration_min"])
    return response_progress(elapsed-event["started_at"], event["onset_min"], event["duration_min"], event.get("recovery_min"), event.get("immediate", False))


def gain_at(curve, values):
    if not curve:
        return 1.0
    points, value = curve["points"], values[curve["field"]]
    if value <= points[0]["value"]:
        return points[0]["factor"]
    for low, high in zip(points, points[1:]):
        if value <= high["value"]:
            fraction = (value-low["value"]) / (high["value"]-low["value"])
            return low["factor"] + fraction*(high["factor"]-low["factor"])
    return points[-1]["factor"]


def retire_active_events(events, elapsed, transition_min=None):
    retired = []
    for event in events:
        duration = transition_min or event.get("washout_min")
        if not duration:
            continue
        exposure = event["exposure"] * event_progress(event, elapsed)
        if exposure <= 0:
            continue
        tail = deepcopy(event)
        tail.update(withdrawal=True, started_at=elapsed, duration_min=duration, onset_min=0,
                    exposure=exposure, recovery_min=None, immediate=False)
        retired.append(tail)
    return retired
