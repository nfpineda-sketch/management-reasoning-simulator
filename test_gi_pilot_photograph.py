"""P3-556 (faculty request of 2026-11-26): the bedside photograph of the GI development pilot.

The pilot's room shows ONE photograph already in the repository's image pack and already approved by the faculty (visual and clinical review), for
the whole encounter, labelled as the patient ON ARRIVAL -- never the current state, so it never follows the earlier model's appearance (H2). The image
bank stays off, nothing is generated or requested, and every check fails closed to the neutral view the room showed before.
"""
import base64
import copy
import hashlib
import json
import shutil

import pytest

import clinical_scene
import gi_pilot as gp
import image_pack
from image_bank import contract_key
from image_identities import compatible_identities, near
from image_selection import best_asset, choose_identity
from patient_appearance import appearance_state
from test_gi_pilot_page import ORDERS, _account, _begin, _sign_in, world  # noqa: F401  (world is the module-scoped fixture)

pytestmark = pytest.mark.ordinary_configuration
PIN = gp.ARRIVAL_PHOTOGRAPH


@pytest.fixture(scope="module")
def arrival_state():
    import pilot_acceptance as acceptance
    return copy.deepcopy(acceptance.Encounter(PIN["case_id"]).state)


def _pack_assets():
    approvals = image_pack.read_approvals()
    assets = []
    for asset in image_pack.read_manifest()["assets"]:
        record = dict(asset)
        for approval in approvals:
            if approval["asset_id"] == record["id"] and approval["field"] in ("visual_review", "clinical_review"):
                record[approval["field"]] = approval["value"]
        assets.append(record)
    return assets


def _arrival(state):
    spec = state["encounter_spec"]
    return {"observable": spec["initial_observable"], "encounter_spec": spec, "treatments": {}}


# -- the photograph is the one the bank's own rule picks, approved, of this case's arrival -----------------------------------------------------

def test_u1_the_pinned_photograph_is_the_bank_s_own_choice_for_the_case_s_arrival(arrival_state):
    patient = arrival_state["encounter_spec"]["clinical_case"]["patient"]
    assert (patient["age_years"], patient["sex"]) == (57, "male")
    arrival = appearance_state(_arrival(arrival_state))
    assert arrival == {"mental_status": "alert", "work_of_breathing": "normal", "expression": "uncomfortable", "skin_color": "mild pallor",
                       "diaphoresis": "mild", "mottling": False, "respiratory_support": "none"}, "awake, pale, uncomfortable, mildly diaphoretic"
    key, assets = contract_key(arrival), _pack_assets()
    candidates = compatible_identities(patient)
    ready = {c["id"] for c in candidates if best_asset([a for a in assets if a["identity_id"] == c["id"] and a["state_key"] == key])}
    chosen, why = choose_identity(candidates, ready=ready, nearness={c["id"]: near(c, patient) for c in candidates}, seed="any")
    assert chosen["id"] == PIN["identity_id"] and PIN["identity_id"] in why["ready"]
    picked = best_asset([a for a in assets if a["identity_id"] == PIN["identity_id"] and a["state_key"] == key])
    assert picked["id"] == PIN["asset_id"] and picked["display"]["sha256"] == PIN["sha256"]
    assert picked["visual_review"] == picked["clinical_review"] == "approved" and picked["technical_check"] == "passed" and not picked["excluded"]


def test_u2_the_real_encounter_gets_the_pinned_bytes_from_the_local_pack(arrival_state):
    assert gp.arrival_photograph_problems(arrival_state) == []
    image = gp.arrival_photograph(arrival_state)
    assert image is not None and image.mime == "image/webp" and image.asset_id == PIN["asset_id"] and image.identity_id == PIN["identity_id"]
    assert hashlib.sha256(base64.b64decode(str(image))).hexdigest() == PIN["sha256"]


def test_u3_the_photograph_is_static_whatever_the_current_state(arrival_state):
    later = copy.deepcopy(arrival_state)
    later["observable"].update({"mental_status": "Drowsy", "sbp": 70, "dbp": 40, "hr": 130})
    later.setdefault("family_state", {})["norepinephrine"] = 12.0
    later["sim_time"] = 75
    assert str(gp.arrival_photograph(later)) == str(gp.arrival_photograph(arrival_state)), "only the arrival is drawn; the current state never changes it"


@pytest.mark.parametrize("change, problem", [
    (lambda s: s["encounter_spec"].update(variant_id="gi_bleed_72f"), "not the pilot case"),
    (lambda s: s["encounter_spec"]["initial_observable"].update(mental_status="Drowsy"), "arrival appearance"),
    (lambda s: s["encounter_spec"]["clinical_case"]["patient"].update(sex="female"), "not compatible with the chart"),
    (lambda s: s["encounter_spec"]["clinical_case"]["patient"].update(age_years=30), "not compatible with the chart"),
])
def test_u4_a_photograph_that_does_not_fit_the_encounter_is_not_shown(arrival_state, change, problem):
    state = copy.deepcopy(arrival_state)
    change(state)
    assert any(problem in item for item in gp.arrival_photograph_problems(state))
    assert gp.arrival_photograph(state) is None


def test_u5_a_rejected_review_keeps_the_photograph_out(arrival_state, monkeypatch):
    approvals = image_pack.read_approvals() + [{"asset_id": PIN["asset_id"], "field": "clinical_review", "value": "rejected"}]
    monkeypatch.setattr(image_pack, "read_approvals", lambda directory=None: approvals)
    assert gp.arrival_photograph(arrival_state) is None


def test_u6_altered_or_missing_bytes_are_never_shown(arrival_state, tmp_path, monkeypatch):
    for name in (image_pack.MANIFEST, image_pack.APPROVALS):
        shutil.copy(image_pack.PACK_DIR / name, tmp_path / name)
    manifest = json.loads((tmp_path / image_pack.MANIFEST).read_text(encoding="utf-8"))
    record = next(a for a in manifest["assets"] if a["id"] == PIN["asset_id"])
    raw = (image_pack.PACK_DIR / record["display"]["file"]).read_bytes()
    reads = {"manifest": image_pack.read_manifest, "approvals": image_pack.read_approvals}
    monkeypatch.setattr(image_pack, "PACK_DIR", tmp_path)
    monkeypatch.setattr(image_pack, "read_manifest", lambda directory=None: reads["manifest"](tmp_path))
    monkeypatch.setattr(image_pack, "read_approvals", lambda directory=None: reads["approvals"](tmp_path))
    monkeypatch.setattr(gp, "_ARRIVAL_BYTES", {})
    assert gp.arrival_photograph(arrival_state) is None, "missing"
    (tmp_path / record["display"]["file"]).write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    assert gp.arrival_photograph(arrival_state) is None, "altered"
    (tmp_path / record["display"]["file"]).write_bytes(raw)
    assert gp.arrival_photograph(arrival_state) is not None, "intact"


# -- the room says what the photograph is -------------------------------------------------------------------------------------------------------

def test_u7_the_room_labels_it_on_arrival_and_keeps_the_current_appearance_line(arrival_state):
    image = gp.arrival_photograph(arrival_state)
    html = clinical_scene.scene_html(image, "<div>monitor</div>", current=True, observations="Appearance now.", arrival_label=gp.ARRIVAL_PHOTOGRAPH_LABEL)
    assert "ED / Bed 03 · Patient on arrival" in html and "current state" not in html and "unavailable" not in html
    assert f"base64,{image}" in html and clinical_scene.STILL_VIEW_NOTE in html and "Appearance now." in html
    without = clinical_scene.scene_html(None, "<div>monitor</div>", current=False, observations="Appearance now.",
                                        image_status={"state": "unavailable", "code": "NOT_ALLOWED"}, arrival_label=gp.ARRIVAL_PHOTOGRAPH_LABEL)
    assert "Current patient image unavailable" in without and "Patient on arrival" not in without, "no photograph: the neutral view, as before"
    # Every other room is untouched: no arrival label, the same bed space as before P3-556.
    assert clinical_scene.scene_html(image, "m", current=True, observations="x") == clinical_scene.scene_html(image, "m", current=True, observations="x", arrival_label=None)
    assert "Patient illustration · current state" in clinical_scene.scene_html(image, "m", current=True, observations="x")


def test_u8_the_image_bank_stays_off_in_the_pilot():
    assert any("MRS_IMAGE_BANK must be off" in item for item in gp.evaluate({gp.FLAG: gp.MODE_ON}, accounts=True, on_cloud=False)["problems"])
    assert any("MRS_IMAGE_BANK must be off" in item for item in gp.evaluate({gp.FLAG: gp.MODE_ON, "MRS_IMAGE_BANK": "on"}, accounts=True, on_cloud=False)["problems"])


# -- on the real page ---------------------------------------------------------------------------------------------------------------------------

def _room_markdown(at):
    return "\n".join(str(item.value) for item in at.markdown if "clinical-scene" in str(item.value))


@pytest.fixture(scope="module")
def walk(world):
    """A resident encounter on the real page with no generation path at all: the room never asks clinical_scene.scene_image, and no provider client is built."""
    with pytest.MonkeyPatch.context() as mp:
        def refused(*args, **kwargs):
            raise AssertionError("the pilot room must not ask for a generated photograph")
        mp.setattr(clinical_scene, "scene_image", refused)
        import openai
        mp.setattr(openai, "OpenAI", refused)
        at = _sign_in(world, _account(world, "resident"))
        _begin(at)
        arrival = _room_markdown(at)
        import test_phase3_pair_page as page
        page._order(at, ORDERS[0])
        page._order(at, ORDERS[1])                                     # norepinephrine
        later = _room_markdown(at)
        return {"at": at, "arrival": arrival, "later": later}


def test_p1_the_pilot_room_shows_the_patient_on_arrival(walk):
    room = walk["arrival"]
    assert "Patient on arrival" in room and "data:image/webp;base64," in room
    assert "Current patient image unavailable" not in room and "No photograph is prepared" not in room
    assert clinical_scene.STILL_VIEW_NOTE in room and "BEDSIDE MONITOR" in room, "the monitor and the layout are kept"


def test_p2_after_norepinephrine_the_same_photograph_and_no_mental_status_in_the_room(walk):
    def photo(room):
        return room.split("base64,", 1)[1].split(")", 1)[0]
    assert photo(walk["later"]) == photo(walk["arrival"]) == str(gp.arrival_photograph(walk["at"].session_state["state"]))
    assert "Patient on arrival" in walk["later"]
    import re
    lines = re.findall(r'<div class="scene-observations">(.*?)</div>', walk["later"])
    assert lines and gp.APPEARANCE_MENTAL_WITHHELD in lines[0], "the current appearance line stays on screen, with mental status withheld"
    for word in ("Alert", "Drowsy", "Obtunded", "Confused", "Lethargic", "Unresponsive"):
        assert word not in lines[0]
