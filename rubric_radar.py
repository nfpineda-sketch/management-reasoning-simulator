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
            "rings": rings, "axes": axes, "series": drawn, "levels": RINGS,
            # Small enough to sit inside the innermost ring, which is at a
            # third of the radius: the badge must not reach a score of 1.
            "badge_radius": radius * 0.21}


def _badge_svg(badge, centre_x, centre_y, radius):
    """The face, the initials and the year, at the centre and under the data."""
    if not badge:
        return []
    from xml.sax.saxutils import quoteattr
    identifier = f"mrsbadge{abs(hash((badge.get('initials'), badge.get('year')))) % 10 ** 8}"
    parts = []
    if badge.get("image"):
        parts.append(f'<clipPath id="{identifier}"><circle cx="{centre_x:.2f}" '
                     f'cy="{centre_y:.2f}" r="{radius:.2f}"/></clipPath>')
        parts.append(f'<image href={quoteattr(badge["image"])} '
                     f'x="{centre_x - radius:.2f}" y="{centre_y - radius:.2f}" '
                     f'width="{radius * 2:.2f}" height="{radius * 2:.2f}" '
                     f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{identifier})"/>')
    else:
        # No photograph: the initials become the badge, which is what an avatar
        # without a picture looks like anywhere else.
        parts.append(f'<circle cx="{centre_x:.2f}" cy="{centre_y:.2f}" r="{radius:.2f}" '
                     f'fill="{palette.PALE}"/>')
        if badge.get("initials"):
            parts.append(f'<text x="{centre_x:.2f}" y="{centre_y:.2f}" text-anchor="middle" '
                         f'dominant-baseline="central" font-size="{radius * 0.62:.1f}" '
                         f'font-weight="700" fill="{palette.NAVY}">'
                         f'{escape(badge["initials"])}</text>')
    parts.append(f'<circle cx="{centre_x:.2f}" cy="{centre_y:.2f}" r="{radius:.2f}" '
                 f'fill="none" stroke="{palette.LINE}" stroke-width="1.2"/>')
    caption = " · ".join(str(part) for part in (
        (badge.get("initials") if badge.get("image") else ""),
        _year_label(badge.get("year"))) if part)
    if caption:
        parts.append(f'<text x="{centre_x:.2f}" y="{centre_y + radius + 11:.2f}" '
                     f'text-anchor="middle" font-size="9.5" font-weight="700" '
                     f'fill="{palette.INK}">{escape(caption)}</text>')
    return parts


def _year_label(year):
    return f"R{year}" if isinstance(year, int) and not isinstance(year, bool) else ""


def _path(run, closed):
    body = " ".join(f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
                    for index, (x, y) in enumerate(run))
    return body + (" Z" if closed else "")


def svg(series, *, size=260, language="en", title=None, badge=None):
    """The same chart as an inline SVG, for the application.

    ``badge`` optionally puts a face, initials and a training year at the
    centre. It is drawn **under** the outlines, and a domain scored 0 -- whose
    point is the centre itself -- keeps a ring of the page colour around it so
    it stays readable on top of a photograph. A picture must not hide a zero.
    """
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
    parts += _badge_svg(badge, centre_x, centre_y, plan["badge_radius"])
    for item in plan["series"]:
        for run in item["runs"]:
            if len(run) == 1:
                x, y = run[0]
                halo = (' stroke="#FFFFFF" stroke-width="1.6"' if badge else "")
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.4" '
                             f'fill="{item["colour"]}"{halo}/>')
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
                halo = (' stroke="#FFFFFF" stroke-width="1.6"' if badge else "")
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" '
                             f'fill="{item["colour"]}"{halo}/>')
    for axis in plan["axes"]:
        missing = all(axis["domain_id"] in item["gaps"] for item in plan["series"])
        colour = palette.MUTED if missing else palette.INK
        parts.append(f'<text x="{axis["label_x"]:.2f}" y="{axis["label_y"]:.2f}" '
                     f'text-anchor="{axis["anchor"]}" dominant-baseline="middle" '
                     f'font-size="10.5" fill="{colour}">{escape(axis["short"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def drawing(series, *, size=150, language="en", badge=None):
    """The same chart as a ReportLab drawing, for the documents."""
    from reportlab.graphics.shapes import Circle, Drawing, Image, Line, Polygon, PolyLine, String
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
    if badge:
        _badge_drawing(art, badge, point(centre_x, centre_y), plan["badge_radius"])
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
                # A zero is drawn at the centre, on top of the badge; the ring
                # of page colour is what keeps it visible over a photograph.
                art.add(Circle(cx, cy, 2.0, fillColor=colour,
                               strokeColor=colors.white if badge else None,
                               strokeWidth=1.2 if badge else 0))
    for axis in plan["axes"]:
        missing = all(axis["domain_id"] in item["gaps"] for item in plan["series"])
        x, y = point(axis["label_x"], axis["label_y"])
        text = String(x, y - 2.6, axis["short"], fontName="FacultySans", fontSize=6.6,
                      fillColor=colors.HexColor(palette.MUTED if missing else palette.INK))
        text.textAnchor = axis["anchor"]
        art.add(text)
    return art


def _badge_drawing(art, badge, centre, radius):
    """The same badge on the page: a face or the initials, and the year."""
    import base64
    import io
    from reportlab.graphics.shapes import Circle, Image, String
    from reportlab.lib import colors
    from PIL import Image as PILImage
    x, y = centre
    drew_image = False
    uri = str(badge.get("image") or "")
    if uri.startswith("data:image/"):
        try:
            raw = base64.b64decode(uri.split(",", 1)[1])
            # renderPDF draws a shapes.Image from a file name or a PIL image
            # (it tests for ``.mode``); an ImageReader reaches os.path.exists
            # and fails the whole page. Decoded here into pixels detached from
            # the source file (a JPEG would otherwise be re-read from it), so
            # a bad photograph falls back to the initials below.
            face = PILImage.open(io.BytesIO(raw)).convert("RGB")
            art.add(Image(x - radius, y - radius, radius * 2, radius * 2, face))
            drew_image = True
        except Exception:
            # A stored photograph that cannot be decoded is not a reason to
            # withhold the chart; the initials stand in for it.
            drew_image = False
    if not drew_image:
        art.add(Circle(x, y, radius, fillColor=colors.HexColor(palette.PALE), strokeColor=None))
        if badge.get("initials"):
            text = String(x, y - radius * 0.22, str(badge["initials"]),
                          fontName="FacultySans-Bold", fontSize=radius * 0.62,
                          fillColor=colors.HexColor(palette.NAVY))
            text.textAnchor = "middle"
            art.add(text)
    art.add(Circle(x, y, radius, fillColor=None,
                   strokeColor=colors.HexColor(palette.LINE), strokeWidth=1.0))
    caption = " \u00b7 ".join(part for part in (
        (str(badge.get("initials")) if drew_image and badge.get("initials") else ""),
        _year_label(badge.get("year"))) if part)
    if caption:
        label = String(x, y - radius - 9, caption, fontName="FacultySans-Bold",
                       fontSize=6.6, fillColor=colors.HexColor(palette.INK))
        label.textAnchor = "middle"
        art.add(label)


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
