"""The extended FAST, as the faculty wrote it on 2026-09-23.

Five windows, and every case reports all five including the normal ones, for the
same reason every case reports the whole POCUS protocol: a window that is
missing from a report is a window nobody looked at, and the record must not let
that read as a negative finding.

The faculty's own protocol, in their order:

1. **Right upper quadrant** -- free fluid in Morison's (hepatorenal) pouch, the
   subdiaphragmatic space and the pleural recess.
2. **Left upper quadrant** -- free fluid in the splenorenal space, the
   subdiaphragmatic space and the pleural recess.
3. **Suprapubic**, longitudinal and transverse -- free fluid between the bladder
   and the bowel; in women, the pouch of Douglas.
4. **Subxiphoid** -- free fluid in the pericardium.
5. **Lung** -- lung sliding; on M-mode the seashore sign, on B-mode comet tails.
   Their presence excludes a pneumothorax.

And one rule about the order, which is assessed rather than enforced:

> **In open or penetrating trauma the cardiac windows are done first.**

The engine does not refuse a resident who starts elsewhere. It records what they
did first, and the rubric reads it, because the order is a decision and not a
setting.
"""

#: (window, [(field, label)]) in the order the faculty listed them.
SECTIONS = (
    ("Right upper quadrant", (
        ("ruq_morison", "Morison's pouch (hepatorenal)"),
        ("ruq_subdiaphragmatic", "Right subdiaphragmatic space"),
        ("ruq_pleural", "Right pleural recess"),
    )),
    ("Left upper quadrant", (
        ("luq_splenorenal", "Splenorenal space"),
        ("luq_subdiaphragmatic", "Left subdiaphragmatic space"),
        ("luq_pleural", "Left pleural recess"),
    )),
    ("Suprapubic", (
        ("suprapubic_longitudinal", "Longitudinal view"),
        ("suprapubic_transverse", "Transverse view"),
    )),
    ("Subxiphoid", (
        ("pericardium", "Pericardium"),
    )),
    ("Lung", (
        ("lung_sliding_right", "Right lung sliding"),
        ("lung_sliding_left", "Left lung sliding"),
        ("lung_m_mode", "M-mode"),
    )),
)

KEYS = tuple(key for _, items in SECTIONS for key, _ in items)
LABELS = {key: label for _, items in SECTIONS for key, label in items}
NOT_DOCUMENTED = "Not documented"

#: The windows that answer the question a penetrating wound asks first.
CARDIAC_WINDOWS = ("pericardium",)

#: What a normal window says. Findings, never interpretation: none of these
#: sentences says "no tamponade" or "negative FAST".
NORMAL = {
    "ruq_morison": "No free fluid in the hepatorenal recess",
    "ruq_subdiaphragmatic": "No free fluid above the liver",
    "ruq_pleural": "No fluid in the right pleural recess",
    "luq_splenorenal": "No free fluid in the splenorenal recess",
    "luq_subdiaphragmatic": "No free fluid above the spleen",
    "luq_pleural": "No fluid in the left pleural recess",
    "suprapubic_longitudinal": "No free fluid behind or around the bladder",
    "suprapubic_transverse": "No free fluid behind or around the bladder",
    "pericardium": "No pericardial fluid",
    "lung_sliding_right": "Sliding present",
    "lung_sliding_left": "Sliding present",
    "lung_m_mode": "Seashore sign bilaterally; comet tails seen",
}


def study(**findings):
    """One E-FAST result: every window, with the normal finding where unstated."""
    unknown = sorted(set(findings) - set(KEYS))
    if unknown:
        raise ValueError(f"Not windows of this protocol: {', '.join(unknown)}")
    return {key: str(findings.get(key, NORMAL[key])) for key in KEYS}


def missing_windows(result):
    """Windows this result does not document. Empty is a complete study."""
    result = result if isinstance(result, dict) else {}
    return [key for key in KEYS if not str(result.get(key, "")).strip()]


def free_fluid(result):
    """The windows reporting free fluid, by the words the result uses.

    A reading of the report, not an interpretation of the patient: it says which
    windows were positive, and nothing about what that means for this patient.
    """
    found = []
    for key in KEYS:
        text = str((result or {}).get(key, "")).lower()
        if not text or key.startswith("lung"):
            continue
        if "free fluid" in text and not text.startswith("no "):
            found.append(key)
        elif "pericardial fluid" in text and not text.startswith("no "):
            found.append(key)
        elif "fluid in the" in text and not text.startswith("no "):
            found.append(key)
    return found


def pneumothorax_windows(result):
    """The sides where sliding is reported absent."""
    sides = []
    for key in ("lung_sliding_right", "lung_sliding_left"):
        text = str((result or {}).get(key, "")).lower()
        if "absent" in text or "no sliding" in text:
            sides.append(key)
    return sides


def cardiac_first(order):
    """True when the subxiphoid window was the first one recorded.

    ``order`` is the sequence of window keys as the record has them. An empty
    sequence is not a yes: nobody looked.
    """
    sequence = [key for key in (order or ()) if key in KEYS]
    return bool(sequence) and sequence[0] in CARDIAC_WINDOWS
