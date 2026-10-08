"""Where each event of the patient's course comes from, and which ones stop a wait (Phase 0, 0F/0H).

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§5.4) found that no event
interrupted a turn: in the inferior STEMI, one "Reassess in 120 minutes" returned once, at
minute 120, reporting the AV block of minute 45 and the VF of minute 120 together. Nor did the
record say whether an event came from the disease, from the resident's treatment, or from a
course the case scripts whatever is done -- so an analysis could hold a scripted AV block
against the resident.

Each event the family engine already produces is declared here once, by the flag the engine
sets when it happens (no new physiology):

* ``cause_class``: NATURAL_DISEASE, RESIDENT_TREATMENT, SCRIPTED_NATURAL_HISTORY, LOGISTIC,
  ENGINE_LIMITATION or TERMINAL;
* ``preventability``: PREVENTABLE, NOT_PREVENTABLE_IN_SIMULATOR or UNKNOWN, with the reason;
* ``severity``: minor, significant, critical or terminal;
* ``interrupt``: whether it stops a wait at its minute (loss of pulse, VF/pVT/asystole/PEA, a
  new significant arrhythmia, a seizure, airway compromise, a major collapse, a major fall in
  oxygenation).

Two changes the engine does not flag are watched on the vital signs, with severity, change
and persistence together, so that an artefact of one minute never stops a wait: a systolic
pressure below 70 mmHg that has fallen at least 20 mmHg since the wait began, for two
consecutive minutes; and a saturation below 85 % that has fallen at least 5 points, for two
consecutive minutes. Their cause is not known to the engine: UNKNOWN, and never held against
the resident on its own.
"""
from __future__ import annotations

from copy import deepcopy

CAUSE_CLASSES = ("NATURAL_DISEASE", "RESIDENT_TREATMENT", "SCRIPTED_NATURAL_HISTORY", "LOGISTIC",
                 "ENGINE_LIMITATION", "TERMINAL")
PREVENTABILITY = ("PREVENTABLE", "NOT_PREVENTABLE_IN_SIMULATOR", "UNKNOWN")
SEVERITY = ("minor", "significant", "critical", "terminal")
SCHEMA = "event_provenance_v1"

#: Engine flags whose first setting is an event, with their declared provenance.
FLAG_EVENTS = {
    "av_block_at": {
        "kind": "av_block", "label": "complete atrioventricular block",
        "cause_class": "SCRIPTED_NATURAL_HISTORY", "preventability": "NOT_PREVENTABLE_IN_SIMULATOR",
        "severity": "critical", "interrupt": True,
        "why": ("the inferior infarct takes the AV node at ischemic minute 45; the earliest reperfusion the "
                "simulator can deliver (thrombolysis +60 min, PCI +90 min) cannot come before it"),
    },
    "vf_at": {
        "kind": "ventricular_fibrillation", "label": "ventricular fibrillation, pulse lost",
        "cause_class": "SCRIPTED_NATURAL_HISTORY", "preventability": "PREVENTABLE",
        "severity": "terminal", "interrupt": True, "terminal": True,
        "why": ("scripted at ischemic minute 120 for an artery still closed (or a provocative test in ACS); "
                "reperfusion decided early enough prevents it"),
    },
    "arrest_at": {
        "kind": "cardiac_arrest", "label": "cardiac arrest, pulse lost",
        "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
        "severity": "terminal", "interrupt": True, "terminal": True,
        "why": "the untreated course reaches arrest (opioid apnoea unsupported for 20 minutes, or the "
               "family's own arrest); the treatment that reverses the cause prevents it",
    },
    "hemorrhage_arrest": {
        "kind": "cardiac_arrest", "label": "cardiac arrest from uncontrolled haemorrhage",
        "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
        "severity": "terminal", "interrupt": True, "terminal": True,
        "why": "the blood loss reaches the arrest threshold while the source is still open; controlling it prevents it",
    },
    "arrested": {
        # K-E5 (faculty, 2026-10-07): true whether no adrenaline was given or a dose did not control the
        # reaction; «untreated» is not the general label. K-21 stays the truly untreated sentence.
        "kind": "cardiac_arrest", "label": "circulatory arrest from anaphylaxis without effective adrenaline",
        "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
        "severity": "terminal", "interrupt": True, "terminal": True,
        "why": "25 minutes without effective adrenaline; adrenaline prevents it",
    },
    "bradycardia_arrest": {
        # K-E6 (faculty, 2026-10-07): the same terminal event, named clearly; trigger, preventability and
        # physiology unchanged.
        "kind": "cardiac_arrest", "label": "circulatory arrest from profound bradycardia",
        "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
        "severity": "terminal", "interrupt": True, "terminal": True,
        "why": "the rate falls below what keeps an output; pacing or the antidote prevents it",
    },
    "seizure_at": {
        "kind": "seizure", "label": "generalized seizure",
        "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
        "severity": "critical", "interrupt": True,
        "why": "twenty minutes with glucose below 40 mg/dL; glucose given in time prevents it",
    },
    "biphasic_at": {
        "kind": "biphasic_reaction", "label": "the anaphylactic reaction returns",
        "cause_class": "SCRIPTED_NATURAL_HISTORY", "preventability": "NOT_PREVENTABLE_IN_SIMULATOR",
        "severity": "critical", "interrupt": True,
        "why": "scripted 75 minutes after the first reaction settled; nothing in the simulator prevents it",
    },
    "pneumothorax_at": {
        "kind": "tension_pneumothorax", "label": "tension pneumothorax on the ventilator",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "critical", "interrupt": True,
        "why": "sustained plateau pressures above 30 cmH2O; ventilator settings that keep the plateau lower prevent it",
    },
    "major_bleed_reported": {
        "kind": "major_bleeding_after_lysis", "label": "major bleeding after thrombolysis",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "UNKNOWN",
        "severity": "critical", "interrupt": True,
        "why": "a declared bleeding risk and thrombolysis given; whether lysis was right is the faculty's to judge",
    },
    "dobutamine_arrhythmia_reported": {
        "kind": "ventricular_ectopy", "label": "frequent ventricular ectopy on dobutamine",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "significant", "interrupt": True,
        "why": "a dobutamine rate above the arrhythmia threshold; a lower rate prevents it",
    },
    "rv_strain_reported": {
        "kind": "rv_failure_from_volume", "label": "right ventricle failing under fast volume",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "critical", "interrupt": True,
        "why": "fluid given faster than an obstructed right ventricle accepts; slow, small volumes prevent it",
    },
    "hypotension_reported": {
        "kind": "sustained_hypotension", "label": "sustained hypotension from the obstruction",
        "cause_class": "NATURAL_DISEASE", "preventability": "UNKNOWN",
        "severity": "critical", "interrupt": True,
        "why": "15 consecutive minutes with the systolic pressure below the threshold; it defines the shock, "
               "whatever was done",
    },
    "transfusion_overload_at": {
        "kind": "transfusion_overload", "label": "volume overload from transfusion",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "significant", "interrupt": False,
        "why": "blood given above the haemoglobin threshold; its effect on oxygenation is watched on the vital signs",
    },
    "withdrawal_reported": {
        "kind": "opioid_withdrawal", "label": "acute opioid withdrawal",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "significant", "interrupt": False,
        "why": "more naloxone than the opioid on board; titrated doses prevent it",
    },
    "rebound_at": {
        "kind": "glucose_overshoot", "label": "glucose overshoot above 200 mg/dL",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "PREVENTABLE",
        "severity": "minor", "interrupt": False,
        "why": "more dextrose than the deficit in a patient with a working pancreas",
    },
    "artery_open_at": {
        "kind": "reperfusion", "label": "the artery is open",
        "cause_class": "RESIDENT_TREATMENT", "preventability": "UNKNOWN",
        "severity": "minor", "interrupt": False,
        "why": "the reperfusion the resident decided",
    },
    "endoscopy_at": {
        "kind": "endoscopy", "label": "endoscopy performed",
        "cause_class": "LOGISTIC", "preventability": "UNKNOWN",
        "severity": "minor", "interrupt": False,
        "why": "the consult's fixed delay, once the patient is resuscitated",
    },
    "discharge_return_reported": {
        "kind": "return_after_discharge", "label": "brought back after discharge",
        "cause_class": "LOGISTIC", "preventability": "PREVENTABLE",
        "severity": "significant", "interrupt": True,
        "why": "an unstable patient was discharged",
    },
}

SBP_COLLAPSE = {"below": 70, "fall": 20, "minutes": 2}
SPO2_FALL = {"below": 85, "fall": 5, "minutes": 2}

#: The ledger classes of the orders a treatment-caused event follows (0H, 0J). The page's
#: orders reach the engine without their ids, so the event names them from the encounter's
#: ledger by what caused it: every executed order of these classes written before the event.
SOURCE_CLASSES = {
    "pneumothorax_at": ("intubation", "respiratory_adjustment"),
    "major_bleed_reported": ("thrombolysis",),
    "dobutamine_arrhythmia_reported": ("dobutamine",),
    "rv_strain_reported": ("fluid", "blood"),
    "transfusion_overload_at": ("blood",),
    "withdrawal_reported": ("naloxone", "naloxone_infusion"),
    "rebound_at": ("dextrose", "dextrose_infusion", "oral_carbohydrate"),
    "artery_open_at": ("reperfusion_referral", "consult", "thrombolysis"),
}

#: Bleeding sources whose definitive control (an operating theatre) this engine does not
#: run: a drain or a binder slows them and nothing stops them (trauma_hemorrhage).
UNCONTROLLABLE_SOURCES = ("thoracic", "abdominal")


def _refined(spec, flag, state):
    """A declaration that depends on the case (0J): the arrest from a source nothing here stops."""
    if flag == "hemorrhage_arrest":
        import trauma_hemorrhage
        if any(source in UNCONTROLLABLE_SOURCES for source in trauma_hemorrhage.sources(state)):
            return {**spec, "cause_class": "ENGINE_LIMITATION", "preventability": "NOT_PREVENTABLE_IN_SIMULATOR",
                    "why": "the definitive control of this source, an operating theatre, is not modelled in this "
                           "pilot: a drain slows the bleeding and no order in the simulator stops it"}
    return spec


def attribute(events, orders):
    """Name, for each treatment-caused event that names none, the executed orders it follows."""
    for event in events or []:
        if event.get("cause_class") != "RESIDENT_TREATMENT" or event.get("source_order_ids"):
            continue
        classes = SOURCE_CLASSES.get(event.get("flag"), ())
        minute = _number(event.get("minute"))
        seen = []
        for order in orders or []:
            written = _number(order.get("written_at_min"))
            if (order.get("class") in classes and order.get("fate") in ("EXECUTED", "SCHEDULED")
                    and (minute is None or written is None or written <= minute)
                    and order.get("order_id") not in seen):
                seen.append(order.get("order_id"))
        event["source_order_ids"] = seen
    return events


def _flags(state):
    f = (state or {}).get("family_state") or {}
    return {key: f.get(key) for key in FLAG_EVENTS}


def _is_set(value):
    return value is not None and value is not False


def declared(kind_or_flag):
    """The declaration for an event kind or engine flag, or None."""
    if kind_or_flag in FLAG_EVENTS:
        return FLAG_EVENTS[kind_or_flag]
    return next((spec for spec in FLAG_EVENTS.values() if spec["kind"] == kind_or_flag), None)


def _event(spec, *, flag, minute, source_order_ids=(), observed=None):
    return {
        "schema": SCHEMA,
        "kind": spec["kind"],
        "label": spec["label"],
        "flag": flag,
        "minute": int(minute),
        "cause_class": spec["cause_class"],
        "severity": spec["severity"],
        "preventability": spec["preventability"],
        "preventability_reason": spec["why"],
        "interrupt": bool(spec.get("interrupt")),
        "terminal": bool(spec.get("terminal")),
        "source_order_ids": list(source_order_ids),
        "observed": observed or {},
    }


class Watch:
    """Watches one turn's minutes for the events declared above.

    ``step`` is called after each simulated minute; it returns the events that happened in
    that minute, each with its provenance. Events already present when the turn began are
    not reported again.
    """

    def __init__(self, state, *, source_order_ids=()):
        self.before = _flags(state)
        observable = (state or {}).get("observable") or {}
        self.start_sbp = _number(observable.get("sbp"))
        self.start_spo2 = _number(observable.get("spo2"))
        self.low_sbp = 0
        self.low_spo2 = 0
        self.seen_vitals = set()
        self.source_order_ids = list(source_order_ids)
        self.events = []

    def step(self, state):
        found = []
        now = _flags(state)
        minute = int((state or {}).get("sim_time", 0) or 0)
        for flag, value in now.items():
            if _is_set(value) and not _is_set(self.before.get(flag)):
                spec = _refined(FLAG_EVENTS[flag], flag, state)
                treatment = spec["cause_class"] == "RESIDENT_TREATMENT"
                found.append(_event(spec, flag=flag, minute=minute,
                                    source_order_ids=self.source_order_ids if treatment else ()))
        self.before = now
        # One arrest, one event: a family's own arrest sets the engine's with it.
        if any(event["flag"] in ("arrested", "hemorrhage_arrest", "bradycardia_arrest") for event in found):
            found = [event for event in found if event["flag"] != "arrest_at"]
        observable = (state or {}).get("observable") or {}
        pulse = observable.get("pulse_present", True)
        sbp, spo2 = _number(observable.get("sbp")), _number(observable.get("spo2"))
        if pulse and sbp is not None and self.start_sbp is not None:
            low = sbp < SBP_COLLAPSE["below"] and self.start_sbp - sbp >= SBP_COLLAPSE["fall"]
            self.low_sbp = self.low_sbp + 1 if low else 0
            if self.low_sbp >= SBP_COLLAPSE["minutes"] and "sbp" not in self.seen_vitals:
                self.seen_vitals.add("sbp")
                found.append(_event({
                    "kind": "circulatory_collapse", "label": f"systolic pressure {int(sbp)} mmHg and falling",
                    "cause_class": "NATURAL_DISEASE", "preventability": "UNKNOWN", "severity": "critical",
                    "interrupt": True,
                    "why": "a fall the vital signs show for two minutes; the engine does not say its cause",
                }, flag=None, minute=minute, observed={"sbp": sbp, "sbp_at_start": self.start_sbp}))
        if pulse and spo2 is not None and self.start_spo2 is not None:
            low = spo2 < SPO2_FALL["below"] and self.start_spo2 - spo2 >= SPO2_FALL["fall"]
            self.low_spo2 = self.low_spo2 + 1 if low else 0
            if self.low_spo2 >= SPO2_FALL["minutes"] and "spo2" not in self.seen_vitals:
                self.seen_vitals.add("spo2")
                found.append(_event({
                    # K-E16 (faculty, 2026-10-07): «84%» as the rest of the English room writes it.
                    "kind": "oxygenation_fall", "label": f"saturation {int(spo2)}% and falling",
                    "cause_class": "NATURAL_DISEASE", "preventability": "UNKNOWN", "severity": "critical",
                    "interrupt": True,
                    "why": "a fall the vital signs show for two minutes; the engine does not say its cause",
                }, flag=None, minute=minute, observed={"spo2": spo2, "spo2_at_start": self.start_spo2}))
        self.events.extend(found)
        return found


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def interruption(events, *, requested_until, started_at):
    """The first event that stops the wait, as the turn records it; None if none does."""
    for event in events:
        if event.get("interrupt") and int(event["minute"]) < int(requested_until):
            return {
                "minute": int(event["minute"]),
                "after_min": int(event["minute"]) - int(started_at),
                "requested_until_min": int(requested_until),
                "kind": event["kind"],
                "label": event["label"],
                "cause_class": event["cause_class"],
                "severity": event["severity"],
                "preventability": event["preventability"],
            }
    return None


def snapshot(events):
    return [deepcopy(event) for event in events]
