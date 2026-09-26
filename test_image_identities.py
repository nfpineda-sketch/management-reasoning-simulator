"""The synthetic people of the image bank: a body the chart does not contradict (faculty, 2026-09-26/27)."""
import image_identities as I


def _patient(age, sex, weight=None, height=None):
    patient = {"age_years": age, "sex": sex}
    if weight is not None:
        patient["body"] = {"weight_kg": weight, "weight_how": "measured", "weight_by": "at triage",
                           "height_m": height, "height_how": "measured", "height_by": "at triage"}
    return patient


def test_a_case_without_a_weight_shows_only_a_body_that_could_weigh_the_engines_70_kg():
    # The engine computes a chart without a weight at 70 kg: a visibly obese person
    # would lead a resident to estimate a weight the engine does not use.
    shown = {I.apparent_build(record) for record in I.compatible_identities(_patient(55, "female"))}
    assert shown and not shown & {"obese", "severely obese"}
    assert "heavier" in shown


def test_a_heavier_case_draws_a_heavier_person():
    # Faculty, 2026-09-27: no weight is read from a photograph, and only a clear
    # contradiction between the body shown and the chart excludes a person.
    def builds(patient):
        return {I.apparent_build(record) for record in I.compatible_identities(patient)}
    at_35 = _patient(55, "female", 90, 1.60)                        # BMI 35.2
    assert builds(at_35) == {"heavier", "obese"}
    assert "average" in builds(_patient(55, "male", 99, 1.72))      # BMI 33.5: not a plain contradiction
    assert builds(_patient(55, "male", 140, 1.74)) == {"obese", "severely obese"}
    assert "slim" not in builds(_patient(24, "female", 83, 1.70))   # BMI 28.7
    # Every chart finds someone: no case is left without a person.
    assert I.compatible_identities(_patient(30, "female", 38, 1.60))
    assert I.compatible_identities(_patient(55, "male", 190, 1.74))


def test_the_rigid_15_kg_rule_is_retired():
    assert not hasattr(I, "WEIGHT_TOLERANCE_KG") and not hasattr(I, "habitus_fits")
    assert not hasattr(I, "habitus_weight")


def test_photographed_people_are_matched_by_how_their_photograph_looks():
    from clinical_cases import variant_by_id
    patient = lambda case: variant_by_id(case)["patient"]
    # The first sixteen were drawn slim or fit, whatever their build word said.
    assert I.apparent_build(I.identity("V03")) == "slim" and I.identity("V03")["habitus"] == "normal"
    assert not I.compatible(I.identity("V03"), patient("asthma_24f"))            # 83 kg at 1.70 m
    assert I.compatible(I.identity("V22"), patient("acs_61m_posterior"))          # 99 kg at 1.72 m: fits
    assert not I.compatible(I.identity("V22"), patient("gi_bleed_57m"))           # 111 kg at 1.76 m: does not
    assert I.compatible(I.identity("V38"), patient("bradycardia_hyperk_63m"))
    # A person not yet photographed is taken as the prompt asks.
    assert I.apparent_build(I.identity("V34")) == "obese"


def test_every_bank_case_has_a_compatible_person():
    from clinical_cases import FAMILIES
    for spec in FAMILIES.values():
        for variant in spec["variants"]:
            assert I.compatible_identities(variant["patient"]), variant["id"]


def test_between_two_who_fit_the_nearer_body_comes_first():
    from image_selection import choose_identity
    patient = _patient(55, "male", 99, 1.72)                          # BMI 33.5
    candidates = [I.identity("V22"), I.identity("V39")]              # average, obese
    nearness = {record["id"]: I.near(record, patient) for record in candidates}
    assert nearness == {"V22": 1, "V39": 0}
    chosen, _ = choose_identity(candidates, nearness=nearness, seed="x")
    assert chosen["id"] == "V39"
    # What is already saved still comes before it: no photograph is paid for to be nearer.
    chosen, _ = choose_identity(candidates, nearness=nearness, ready={"V22"}, seed="x")
    assert chosen["id"] == "V22"


def test_a_malformed_weight_is_not_guessed():
    assert I.compatible_identities({"age_years": 55, "sex": "female", "weight_kg": "heavy"}) == []


def test_the_bank_is_no_longer_all_slim_and_heavier_bodies_span_every_tone():
    records = I.IDENTITIES
    heavier = [record for record in records if record["habitus"] != "normal"]
    assert len(heavier) / len(records) >= 0.5
    # Habitus is independent of tone: every heavier class appears on light, medium and dark skin.
    groups = {"light": (1, 2), "medium": (3, 4), "dark": (5, 6)}
    for name, tones in groups.items():
        assert any(record["skin_tone"] in tones for record in heavier), name
    assert {record["skin_tone"] for record in records if record["habitus"] in ("obese", "severely obese")} & {5, 6}
    # Each age band of each sex still has a light, a medium and a dark skin tone.
    for key, tones in I.distribution()["tones_by_sex_and_band"].items():
        assert min(tones) <= 2 and any(tone in (3, 4) for tone in tones) and max(tones) >= 5, key


def test_the_prompt_names_the_body_and_never_draws_an_athlete():
    assert "not athletic" in I.person_phrase(I.identity("V13"))
    severe = I.person_phrase(I.identity("V38"))
    assert "severely obese" in severe and "never exaggerated" in severe
    # People photographed before version 1.1 keep the description their photographs were drawn from.
    assert I.describe(I.identity("V22")).endswith("average build")
    assert I.describe(I.identity("V18")).endswith("sturdy build")
