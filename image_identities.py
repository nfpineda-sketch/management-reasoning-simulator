"""The synthetic people the patient photographs may show (faculty request of 2026-09-26).

An identity is the stable part of a patient photograph: apparent age, skin
tone, hair, build. It is chosen for an encounter from the case's demographics,
never the other way round -- no case is changed to fit a picture. The same
identity keeps its face through every state of that encounter, because every
state is an edit of one reference photograph of it (``image_broker``).

The descriptions are visual and nothing else. There is no racial or ethnic
label: a skin tone is described as what a camera sees. No identity carries a
trait about behaviour, hygiene, income, adherence, schooling or substance use,
and every one of them wears the same gown under the same blanket in the same
bay. What distinguishes a sick patient from a well one is the state the engine
recorded, drawn on whichever identity the encounter drew.

The bank is spread on purpose: each age band of each sex has a light, a
medium and a dark skin tone, the six tones appear the same number of times,
and builds and hair vary independently of tone. ``distribution()`` shows it.
Nothing here is a clinical fact, and none of these people exists.
"""
from __future__ import annotations

IDENTITIES_VERSION = "1.0"

# Visual descriptors only, lightest to deepest. The index is what the
# distribution checks count; the words are what a prompt says.
SKIN_TONES = {
    1: "very fair skin",
    2: "light skin with warm undertones",
    3: "light olive skin",
    4: "medium brown skin",
    5: "dark brown skin",
    6: "deep brown skin",
}

# Apparent age of the person drawn, and the case ages that person can stand for.
AGE_BANDS = {
    "young": {"apparent": 27, "ages": (18, 36)},
    "adult": {"apparent": 40, "ages": (32, 48)},
    "middle": {"apparent": 55, "ages": (46, 63)},
    "older": {"apparent": 68, "ages": (60, 77)},
    "elderly": {"apparent": 81, "ages": (74, 110)},
}

BUILDS = ("slim", "average", "sturdy")


def _identity(number, sex, band, tone, hair, build, face=""):
    return {"id": f"V{number:02d}", "sex": sex, "band": band,
            "apparent_age": AGE_BANDS[band]["apparent"], "ages": AGE_BANDS[band]["ages"],
            "skin_tone": tone, "hair": hair, "build": build, "face": face}


# Neutral identifiers: an id says nothing about how the person looks.
IDENTITIES = (
    # women
    _identity(1, "female", "young", 2, "shoulder-length straight brown hair tied back", "slim"),
    _identity(2, "female", "young", 4, "long dark wavy hair in a low bun", "sturdy"),
    _identity(3, "female", "young", 6, "short natural coily black hair", "average"),
    _identity(4, "female", "adult", 1, "chin-length light brown hair", "average"),
    _identity(5, "female", "adult", 3, "long straight black hair in a loose braid", "slim"),
    _identity(6, "female", "adult", 5, "black hair in short locs", "sturdy"),
    _identity(7, "female", "middle", 2, "shoulder-length auburn hair with some gray", "sturdy"),
    _identity(8, "female", "middle", 4, "short dark curly hair with gray at the temples", "average"),
    _identity(9, "female", "middle", 6, "cropped salt-and-pepper hair", "slim"),
    _identity(10, "female", "older", 1, "short white hair", "slim"),
    _identity(11, "female", "older", 3, "gray hair pulled back in a bun", "sturdy"),
    _identity(12, "female", "older", 5, "short gray coily hair", "average"),
    _identity(13, "female", "elderly", 2, "thin white hair, short", "average"),
    _identity(14, "female", "elderly", 4, "silver hair in a low bun", "slim"),
    _identity(15, "female", "elderly", 6, "short white curly hair", "sturdy"),
    # men
    _identity(16, "male", "young", 1, "short sandy hair", "average", "clean-shaven"),
    _identity(17, "male", "young", 3, "short black straight hair", "slim", "light stubble"),
    _identity(18, "male", "young", 5, "close-cropped black hair", "sturdy", "a short trimmed beard"),
    _identity(19, "male", "adult", 2, "short dark brown hair", "sturdy", "a short trimmed beard"),
    _identity(20, "male", "adult", 4, "short black wavy hair", "average", "clean-shaven"),
    _identity(21, "male", "adult", 6, "shaved head", "slim", "a thin mustache"),
    _identity(22, "male", "middle", 1, "thinning gray-blond hair", "average", "clean-shaven"),
    _identity(23, "male", "middle", 3, "short black hair graying at the sides", "sturdy", "gray stubble"),
    _identity(24, "male", "middle", 5, "short gray-black coily hair", "slim", "a gray goatee"),
    _identity(25, "male", "older", 2, "bald with a fringe of white hair", "sturdy", "clean-shaven"),
    _identity(26, "male", "older", 4, "short gray hair", "slim", "a white mustache"),
    _identity(27, "male", "older", 6, "very short white hair", "average", "a short white beard"),
    _identity(28, "male", "elderly", 3, "sparse white hair combed back", "slim", "clean-shaven"),
    _identity(29, "male", "elderly", 5, "short white coily hair", "average", "white stubble"),
    _identity(30, "male", "elderly", 1, "white hair, mostly bald on top", "sturdy", "a short white beard"),
)

BY_ID = {identity["id"]: identity for identity in IDENTITIES}

_AGE_WORDS = {27: "in their late twenties", 40: "around forty", 55: "in their mid-fifties",
              68: "in their late sixties", 81: "in their early eighties"}


def identity(identity_id):
    try:
        return BY_ID[identity_id]
    except KeyError:
        raise KeyError(f"Unknown visual identity {identity_id!r}.") from None


def compatible(identity_record, patient):
    """Whether this person can be the case's patient. The case's demographics decide."""
    if not isinstance(patient, dict):
        return False
    age, sex = patient.get("age_years"), patient.get("sex")
    if type(age) is not int or sex not in ("male", "female"):
        return False
    low, high = identity_record["ages"]
    return identity_record["sex"] == sex and low <= age <= high


def compatible_identities(patient):
    return [record for record in IDENTITIES if compatible(record, patient)]


def describe(identity_record):
    """What a prompt says about the person: visual, and nothing about who they are."""
    noun = "woman" if identity_record["sex"] == "female" else "man"
    age = _AGE_WORDS[identity_record["apparent_age"]].replace(
        "their", "her" if identity_record["sex"] == "female" else "his")
    parts = [SKIN_TONES[identity_record["skin_tone"]], identity_record["hair"]]
    if identity_record.get("face"):
        parts.append(identity_record["face"])
    parts.append(identity_record["build"] + " build")
    return f"a fictional {noun} {age}: " + "; ".join(parts)


def person_phrase(identity_record):
    """The person as the photograph prompts name them: 'man in his late sixties (…)'."""
    noun = "woman" if identity_record["sex"] == "female" else "man"
    age = _AGE_WORDS[identity_record["apparent_age"]].replace(
        "their", "her" if identity_record["sex"] == "female" else "his")
    return f"{noun} {age} ({describe(identity_record).split(': ', 1)[1]})"


def distribution(records=IDENTITIES):
    """How the bank is spread: tones per band and sex, builds per tone. For the report."""
    tones, builds, bands = {}, {}, {}
    for record in records:
        tones.setdefault((record["sex"], record["band"]), []).append(record["skin_tone"])
        builds.setdefault(record["skin_tone"], []).append(record["build"])
        bands.setdefault(record["band"], 0)
        bands[record["band"]] += 1
    return {"tones_by_sex_and_band": {f"{sex}/{band}": sorted(values)
                                      for (sex, band), values in sorted(tones.items())},
            "builds_by_tone": {tone: sorted(values) for tone, values in sorted(builds.items())},
            "identities_by_band": bands}
