"""The five domains drawn as a shape: one geometry, two renderers.

A radar reads a profile at a glance, which is the point: where the shape is
pulled in is where the training is. It is not a new measurement. Every value
comes from a rubric assessment that a faculty member already decided, and the
arithmetic stays in ``rubric``.

Two rules the drawing keeps, because they are the rubric's own:

  * **A domain that is not assessable is drawn as a gap, never at the centre.**
    A point at the centre reads as a zero, and "not assessable" is not a zero:
    it is an encounter that offered no opportunity to observe. The outline
    stops at the edge of the gap and the axis is labelled.
  * **A shape is not a total.** The penalty for a confirmed critical event is
    not subtracted from any axis; it belongs to the headline beside the chart.

``geometry`` computes the points once. ``svg`` draws them for the screen and
``drawing`` for the page, so the chart a faculty member reads and the chart
they print cannot differ.
"""

import math
from xml.sax.saxutils import escape

import report_palette as palette
from rubric import DOMAIN_IDS, DOMAINS, MAX_DOMAIN_SCORE, NOT_ASSESSABLE


RINGS = MAX_DOMAIN_SCORE
# A short label fits on an axis; the full title does not. These are the domain
# titles cut to their subject, not new names for the domains.
SHORT = {
    "D1": ("Severity", "Gravedad"),
    "D2": ("Assessment", "Evaluación"),
    "D3": ("Management", "Manejo"),
    "D4": ("Follow-up", "Seguimiento"),
    "D5": ("Continuity", "Continuidad"),
}
SERIES_COLOURS = (palette.BLUE, palette.ORANGE)


def short_label(domain_id, language="en"):
    spanish = language == "es"
    return SHORT[domain_id][1 if spanish else 0]


def _value(raw):
    """A score a shape can use, or None for an axis that carries no point."""
    if isinstance(raw, bool) or raw is None or raw == NOT_ASSESSABLE:
        return None
    if isinstance(raw, (int, float)) and 0 <= raw <= MAX_DOMAIN_SCORE:
        return float(raw)
    return None


def _runs(values):
    """Contiguous stretches of assessable axes, around the circle.

    A closed polygon over a gap would draw a straight line across the missing
    axis, which is exactly the claim the gap exists to avoid.
    """
    present = [index for index, value in enumerate(values) if value is not None]
    if not present:
        return [], False
    if len(present) == len(values):
        return [present], True
    runs, current = [], [present[0]]
    for index in present[1:]:
        if index == current[-1] + 1:
            current.append(index)
        else:
            runs.append(current)
            current = [index]
    runs.append(current)
    # The circle wraps: a run ending at the last axis continues into one that
    # starts at the first.
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(values) - 1:
        runs[0] = runs[-1] + runs[0]
        runs.pop()
    return runs, False


def geometry(series, *, size=260, language="en", label_room=74):
    """Points for every axis and every series, in one coordinate system.

    ``size`` is the diameter of the chart itself. The box around it is wider,
    because the labels on the left and right axes sit outside the outer ring
    and a square box cuts them in half.

    ``series`` is a sequence of mappings with ``values`` (a domain -> score
    mapping, where a missing domain or ``not_assessable`` is a gap), a
    ``label``, and optionally a ``colour`` and an ``opacity``.
    """
    radius = size / 2
    width = size + 2 * label_room
    height = size + 34
    centre_x, centre_y = width / 2, height / 2
    axes = []
    for index, domain in enumerate(DOMAIN_IDS):
        # Start at the top and go clockwise, which is how the domains are read.
        angle = -math.pi / 2 + index * 2 * math.pi / len(DOMAIN_IDS)
        cos, sin = math.cos(angle), math.sin(angle)
        axes.append({
            "domain_id": domain,
            "title": DOMAINS[domain]["title_es" if language == "es" else "title"],
            "short": short_label(domain, language),
            "angle": angle,
            "x": centre_x + radius * cos, "y": centre_y + radius * sin,
            "label_x": centre_x + (radius + (6 if abs(cos) < 0.2 else 9)) * cos,
            "label_y": centre_y + (radius + (17 if abs(cos) < 0.2 else 13)) * sin,
            "anchor": "middle" if abs(cos) < 0.2 else ("start" if cos > 0 else "end"),
        })
    rings = [{
        "level": level,
        "points": [(centre_x + radius * level / RINGS * math.cos(axis["angle"]),
                    centre_y + radius * level / RINGS * math.sin(axis["angle"]))
                   for axis in axes],
    } for level in range(1, RINGS + 1)]

    drawn = []
    for index, item in enumerate(series):
        values = [_value((item.get("values") or {}).get(domain)) for domain in DOMAIN_IDS]
        runs, closed = _runs(values)
        points = []
        for run in runs:
            points.append([
                (centre_x + radius * values[position] / RINGS * math.cos(axes[position]["angle"]),
                 centre_y + radius * values[position] / RINGS * math.sin(axes[position]["angle"]))
                for position in run])
        drawn.append({
            "key": item.get("key", f"series{index}"),
            "label": item.get("label", ""),
            "colour": item.get("colour") or SERIES_COLOURS[index % len(SERIES_COLOURS)],
            "opacity": float(item.get("opacity", 0.16)),
            "note": item.get("note", ""),
            "closed": closed,
            "runs": points,
            "values": {domain: values[position]
                       for position, domain in enumerate(DOMAIN_IDS)},
            "gaps": [domain for position, domain in enumerate(DOMAIN_IDS)
                     if values[position] is None],
        })
    return {"width": width, "height": height, "size": size,
            "centre": (centre_x, centre_y), "radius": radius,
            "rings": rings, "axes": axes, "series": drawn, "levels": RINGS}


def _path(run, closed):
    body = " ".join(f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
                    for index, (x, y) in enumerate(run))
    return body + (" Z" if closed else "")


def svg(series, *, size=260, language="en", title=None):
    """The same chart as an inline SVG, for the application."""
    plan = geometry(series, size=size, language=language)
    centre_x, centre_y = plan["centre"]
    label = title or ("Perfil por dominio" if language == "es" else "Profile by domain")
    parts = [f'<svg viewBox="0 0 {plan["width"]:.0f} {plan["height"]:.0f}" role="img" '
             f'aria-label="{escape(label)}" xmlns="http://www.w3.org/2000/svg" '
             f'preserveAspectRatio="xMidYMid meet">']
    for ring in plan["rings"]:
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in ring["points"])
        width = 1.1 if ring["level"] == plan["levels"] else 0.7
        parts.append(f'<polygon points="{points}" fill="none" stroke="{palette.LINE}" '
                     f'stroke-width="{width}"/>')
    for axis in plan["axes"]:
        parts.append(f'<line x1="{centre_x:.2f}" y1="{centre_y:.2f}" '
                     f'x2="{axis["x"]:.2f}" y2="{axis["y"]:.2f}" '
                     f'stroke="{palette.LINE}" stroke-width="0.7"/>')
    for item in plan["series"]:
        for run in item["runs"]:
            if len(run) == 1:
                x, y = run[0]
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.4" fill="{item["colour"]}"/>')
                continue
            # An open run carries no fill. A filled open path is closed by the
            # renderer, and that closing line crosses the axis the gap exists
            # to leave empty.
            fill = (f'fill="{item["colour"]}" fill-opacity="{item["opacity"]:.2f}"'
                    if item["closed"] else 'fill="none"')
            parts.append(f'<path d="{_path(run, item["closed"])}" {fill} '
                         f'stroke="{item["colour"]}" stroke-width="2" stroke-linejoin="round" '
                         f'stroke-linecap="round"/>')
            for x, y in run:
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="{item["colour"]}"/>')
    for axis in plan["axes"]:
        missing = all(axis["domain_id"] in item["gaps"] for item in plan["series"])
        colour = palette.MUTED if missing else palette.INK
        parts.append(f'<text x="{axis["label_x"]:.2f}" y="{axis["label_y"]:.2f}" '
                     f'text-anchor="{axis["anchor"]}" dominant-baseline="middle" '
                     f'font-size="10.5" fill="{colour}">{escape(axis["short"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def drawing(series, *, size=150, language="en"):
    """The same chart as a ReportLab drawing, for the documents."""
    from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, PolyLine, String
    from reportlab.lib import colors

    plan = geometry(series, size=size, language=language, label_room=size * 0.34)
    centre_x, centre_y = plan["centre"]
    art = Drawing(plan["width"], plan["height"])

    def point(x, y):
        # ReportLab measures from the bottom; the geometry measures from the top.
        return x, plan["height"] - y

    for ring in plan["rings"]:
        flat = [coordinate for x, y in ring["points"] for coordinate in point(x, y)]
        art.add(Polygon(flat, fillColor=None, strokeColor=colors.HexColor(palette.LINE),
                        strokeWidth=1.0 if ring["level"] == plan["levels"] else 0.5))
    for axis in plan["axes"]:
        start = point(centre_x, centre_y)
        end = point(axis["x"], axis["y"])
        art.add(Line(start[0], start[1], end[0], end[1],
                     strokeColor=colors.HexColor(palette.LINE), strokeWidth=0.5))
    for item in plan["series"]:
        colour = colors.HexColor(item["colour"])
        for run in item["runs"]:
            flat = [coordinate for x, y in run for coordinate in point(x, y)]
            if len(run) > 2 and item["closed"]:
                art.add(Polygon(flat, fillColor=colors.Color(
                    colour.red, colour.green, colour.blue, item["opacity"]),
                    strokeColor=colour, strokeWidth=1.6))
            elif len(run) > 1:
                # Open, and therefore unfilled: see the note in ``svg``.
                art.add(PolyLine(flat, strokeColor=colour, strokeWidth=1.6))
            for x, y in run:
                cx, cy = point(x, y)
                art.add(Circle(cx, cy, 2.0, fillColor=colour, strokeColor=None))
    for axis in plan["axes"]:
        missing = all(axis["domain_id"] in item["gaps"] for item in plan["series"])
        x, y = point(axis["label_x"], axis["label_y"])
        text = String(x, y - 2.6, axis["short"], fontName="FacultySans", fontSize=6.6,
                      fillColor=colors.HexColor(palette.MUTED if missing else palette.INK))
        text.textAnchor = axis["anchor"]
        art.add(text)
    return art


def series_from_review(review, *, label=None, language="en"):
    """One encounter's confirmed profile, as a series."""
    scores = (review or {}).get("scores", {}) or {}
    return {
        "key": "encounter",
        "label": label or ("Este encuentro" if language == "es" else "This encounter"),
        "values": {domain: scores.get(domain) for domain in DOMAIN_IDS},
        "colour": SERIES_COLOURS[0],
        "opacity": 0.18,
    }
