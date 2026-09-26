"""The synthetic people of the image bank: body habitus follows the case (faculty, 2026-09-26)."""
import image_identities as I


def _patient(age, sex, weight=None):
    patient = {"age_years": age, "sex": sex}
    if weight is not None:
        patient["weight_kg"] = weight
    return patient


def test_a_case_without_a_weight_shows_only_a_body_that_could_weigh_the_engines_70_kg():
    # The engine computes a case that states no weight at 70 kg: a visibly obese
    # patient would lead a resident to estimate a weight the engine does not use.
    for sex in ("female", "male"):
        fits = [habitus for habitus in I.HABITUS if I.habitus_fits(habitus, sex)]
        assert fits == ["normal", "overweight"]
    shown = {record["habitus"] for record in I.compatible_identities(_patient(55, "female"))}
    assert shown <= {"normal", "overweight"} and "overweight" in shown


def test_a_heavier_case_draws_a_heavier_person():
    assert {record["habitus"] for record in I.compatible_identities(_patient(55, "female", 90))} == {"obese"}
    assert "obese" in {record["habitus"] for record in I.compatible_identities(_patient(40, "male", 105))}
    assert {record["habitus"] for record in I.compatible_identities(_patient(55, "male", 140))} == {"severely obese"}
    # Beyond the ends of the scale the nearest end fits: no case is left without a person.
    assert I.compatible_identities(_patient(30, "female", 38))
    assert I.compatible_identities(_patient(55, "male", 190))


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
