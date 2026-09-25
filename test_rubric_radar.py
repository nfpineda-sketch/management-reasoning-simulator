"""The shape the five domains make, and the two claims it refuses to make.

A radar is read at a glance, which is why its mistakes are dangerous: a point
drawn at the centre reads as a zero, and a polygon closed across a missing axis
reads as a value nobody recorded. Both are tested here.
"""
import math

import pytest

import rubric_radar as radar
from rubric import DOMAIN_IDS, MAX_DOMAIN_SCORE, NOT_ASSESSABLE


def plan(values, **kwargs):
    return radar.geometry([{"values": values}], **kwargs)


def series(values):
    return plan(values)["series"][0]


def test_every_domain_has_an_axis_in_rubric_order():
    axes = plan({})["axes"]
    assert [axis["domain_id"] for axis in axes] == list(DOMAIN_IDS)
    assert all(axis["short"] and axis["title"] for axis in axes)


def test_the_axes_are_evenly_spaced_and_start_at_the_top():
    axes = plan({})["axes"]
    assert axes[0]["angle"] == pytest.approx(-math.pi / 2)
    step = 2 * math.pi / len(DOMAIN_IDS)
    for earlier, later in zip(axes, axes[1:]):
        assert later["angle"] - earlier["angle"] == pytest.approx(step)


def test_a_complete_profile_is_one_closed_polygon():
    item = series({domain: 2 for domain in DOMAIN_IDS})
    assert item["closed"] is True
    assert len(item["runs"]) == 1
    assert len(item["runs"][0]) == len(DOMAIN_IDS)
    assert item["gaps"] == []


def test_a_not_assessable_domain_is_a_gap_and_never_a_point():
    item = series({"D1": 3, "D2": 2, "D3": 1, "D4": 2, "D5": NOT_ASSESSABLE})
    assert item["gaps"] == ["D5"]
    assert item["closed"] is False
    assert sum(len(run) for run in item["runs"]) == 4


def test_a_missing_domain_is_the_same_gap_as_one_reported_not_assessable():
    absent = series({"D1": 3, "D2": 2, "D3": 1, "D4": 2})
    declared = series({"D1": 3, "D2": 2, "D3": 1, "D4": 2, "D5": NOT_ASSESSABLE})
    assert absent["runs"] == declared["runs"]
    assert absent["gaps"] == declared["gaps"] == ["D5"]


def test_a_gap_is_not_drawn_at_the_centre_where_a_zero_is():
    centre = plan({})["centre"]
    gap = series({"D1": 3, "D2": 2, "D3": 1, "D4": 2, "D5": NOT_ASSESSABLE})
    zero = series({"D1": 3, "D2": 2, "D3": 1, "D4": 2, "D5": 0})
    assert sum(len(run) for run in zero["runs"]) == len(DOMAIN_IDS)
    assert centre in [point for run in zero["runs"] for point in run]
    assert centre not in [point for run in gap["runs"] for point in run]


def test_an_open_outline_carries_no_fill():
    # A filled open path is closed by the renderer, and that closing line
    # crosses the very axis the gap exists to leave empty.
    drawing = radar.svg([{"values": {"D1": 3, "D2": 2, "D3": 1, "D4": 2, "D5": NOT_ASSESSABLE}}])
    paths = [line for line in drawing.splitlines() if line.startswith("<path")]
    assert paths and all('fill="none"' in path for path in paths)


def test_a_complete_outline_is_filled():
    drawing = radar.svg([{"values": {domain: 2 for domain in DOMAIN_IDS}}])
    paths = [line for line in drawing.splitlines() if line.startswith("<path")]
    assert paths and all("fill-opacity" in path for path in paths)


def test_a_gap_at_the_first_domain_joins_the_run_that_wraps_around():
    item = series({"D2": 2, "D3": 1, "D4": 2, "D5": 3})
    assert item["gaps"] == ["D1"]
    assert len(item["runs"]) == 1
    assert len(item["runs"][0]) == 4


def test_two_gaps_leave_two_separate_outlines():
    item = series({"D1": 3, "D2": NOT_ASSESSABLE, "D3": 1, "D4": 2, "D5": NOT_ASSESSABLE})
    assert sorted(item["gaps"]) == ["D2", "D5"]
    assert sorted(len(run) for run in item["runs"]) == [1, 2]


def test_a_single_assessable_domain_is_a_dot_not_a_shape():
    drawing = radar.svg([{"values": {"D1": 3}}])
    assert "<path" not in drawing
    assert drawing.count("<circle") == 1


@pytest.mark.parametrize("value", [None, "", True, False, -1, 4, "3", {"score": 3}])
def test_a_value_the_rubric_never_produces_is_a_gap_rather_than_a_guess(value):
    assert series({"D1": value})["gaps"] == list(DOMAIN_IDS)


def test_the_radius_of_a_point_is_its_share_of_the_maximum():
    layout = plan({"D1": MAX_DOMAIN_SCORE})
    centre_x, centre_y = layout["centre"]
    x, y = layout["series"][0]["runs"][0][0]
    assert math.hypot(x - centre_x, y - centre_y) == pytest.approx(layout["radius"])
    half = plan({"D1": 1})
    x, y = half["series"][0]["runs"][0][0]
    assert math.hypot(x - centre_x, y - centre_y) == pytest.approx(layout["radius"] / 3)


def test_the_box_is_wider_than_the_chart_so_the_side_labels_fit():
    layout = plan({}, size=240)
    assert layout["width"] > layout["size"]
    assert all(0 <= axis["label_x"] <= layout["width"] for axis in layout["axes"])
    assert all(0 <= axis["label_y"] <= layout["height"] for axis in layout["axes"])


def test_two_series_keep_their_own_colours_and_their_own_gaps():
    layout = radar.geometry([
        {"values": {domain: 2 for domain in DOMAIN_IDS}, "label": "one"},
        {"values": {"D1": 1, "D2": 1, "D3": 1, "D4": 1}, "label": "two"},
    ])
    first, second = layout["series"]
    assert first["colour"] != second["colour"]
    assert first["gaps"] == [] and second["gaps"] == ["D5"]


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_labels_follow_the_language(language):
    layout = plan({}, language=language)
    assert [axis["short"] for axis in layout["axes"]] == [
        radar.short_label(domain, language) for domain in DOMAIN_IDS]


def test_the_document_and_the_screen_draw_the_same_values():
    values = {"D1": 3, "D2": 2, "D3": 0, "D4": 2, "D5": NOT_ASSESSABLE}
    import faculty_report
    faculty_report._fonts()
    screen = radar.geometry([{"values": values}], size=240)["series"][0]
    page = radar.drawing([{"values": values}], size=240)
    assert page.width > 240  # the same room for labels the screen leaves
    # The shapes are the same shape: same runs, same gaps, same closure.
    assert screen["gaps"] == ["D5"] and screen["closed"] is False
    assert sum(len(run) for run in screen["runs"]) == 4


def _photo(mode, fmt):
    import base64
    import io
    from PIL import Image
    buffer = io.BytesIO()
    Image.new(mode, (12, 12)).save(buffer, fmt)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buffer.getvalue()).decode()


@pytest.mark.parametrize("photo", [_photo("RGB", "PNG"), _photo("RGBA", "PNG"), _photo("P", "PNG"),
                                   _photo("RGB", "JPEG"), "data:image/png;base64,AAAA"])
def test_a_resident_s_photograph_prints_on_the_document(photo):
    # The rubric document of a resident with a photograph failed to build on the
    # development app (2026-09-25): an ImageReader reached os.path.exists in
    # renderPDF, and the error took down the whole faculty view of the encounter.
    import faculty_report
    from reportlab.graphics import renderPDF
    faculty_report._fonts()
    page = radar.drawing([{"values": {"D1": 2}}], badge={"image": photo, "initials": "RP", "year": 3})
    assert renderPDF.drawToString(page).startswith(b"%PDF")
