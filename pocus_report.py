"""One fixed structure for every emergency POCUS report.

Faculty specification: every POCUS examination reports the same structures in
the same order, normal findings included, so the resident reads a complete
examination rather than only its positive findings.

Findings, not interpretation. The report states what is seen -- "IVC 1.1 cm,
>50% inspiratory collapse", "right atrial systolic collapse" -- and never the
conclusion the resident is expected to draw, such as "preload responsive" or
"tamponade". The LV is described qualitatively; ejection fraction and other
quantitative LV measures are not used at this level. The IVC keeps its diameter
and collapse, which is how it is assessed at the bedside.

A structure a case does not document is shown as "Not documented". It is never
filled in as normal.
"""

SECTIONS = (
    ("Heart", (
        ("lv", "LV contractility"),
        ("rv", "RV size and relation to LV"),
        ("pericardium", "Pericardium"),
    )),
    ("Inferior vena cava", (
        ("ivc", "IVC"),
    )),
    ("Lungs", (
        ("lung_sliding", "Pleural sliding"),
        ("lungs", "B-lines"),
        ("lung_consolidation", "Consolidation and pleural effusion"),
    )),
    ("Aorta", (
        ("aorta_root", "Aortic root"),
        ("aorta_descending", "Descending thoracic aorta"),
        ("aorta_abdominal", "Abdominal aorta"),
    )),
    ("Veins · compression", (
        ("dvt_femoral", "Femoral veins"),
        ("dvt_popliteal", "Popliteal veins"),
    )),
)
POCUS_KEYS = tuple(key for _, items in SECTIONS for key, _ in items)
LABELS = {key: label for _, items in SECTIONS for key, label in items}
NOT_DOCUMENTED = "Not documented"


def missing_sections(result):
    """Structures a POCUS result does not document."""
    result = result if isinstance(result, dict) else {}
    return [key for key in POCUS_KEYS
            if not (isinstance(result.get(key), str) and result[key].strip())]


def format_pocus(result, *, heading="POCUS", compact=False):
    """Render a POCUS result in the fixed protocol order.

    The default puts each structure on its own line under its section title,
    which reads well in the narrow bedside panel. ``compact`` gives one line per
    section, for places that hold several results side by side, such as the
    Management Trace state summary.

    Items start with "· " rather than indentation: markdown, the PDF and the
    HTML review all strip leading spaces.
    """
    result = result if isinstance(result, dict) else {}
    lines = []
    header = heading
    collected = result.get("collected_at_min", result.get("time_min"))
    if type(collected) in {int, float} and not isinstance(collected, bool):
        # A scan is performed, not sampled.
        header += f" · performed at minute {collected:g}"
    lines.append(header)
    for section, items in SECTIONS:
        parts = []
        for key, label in items:
            value = result.get(key)
            text = value.strip() if isinstance(value, str) and value.strip() else NOT_DOCUMENTED
            parts.append(f"{label}: {text}")
        if compact:
            lines.append(section.upper() + " — " + " · ".join(parts))
        else:
            lines.append(section.upper())
            lines.extend("· " + part for part in parts)
    # Legacy saved encounters carried free prose; keep it rather than drop it.
    if isinstance(result.get("report"), str) and result["report"].strip():
        additional = "Additional findings — " + result["report"].strip()
        lines.append(additional if compact else "ADDITIONAL FINDINGS\n· " + result["report"].strip())
    return "\n".join(lines)
