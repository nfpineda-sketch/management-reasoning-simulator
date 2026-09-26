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
medium and a dark skin tone, and builds and hair vary independently of tone.
``distribution()`` shows it. Nothing here is a clinical fact, and none of these
people exists.

Body habitus (faculty request of 2026-09-26: "todos se ven demasiado
atléticos"). The first 30 were drawn slim or fit whatever their build word
said, while about three adults in four who come to an emergency department in
Cleveland or Santiago are overweight or obese (NHANES 2021-23: 40% obese, 32%
overweight; Cleveland 45% obese; Chile ENS 2016-17: 34% obese, 40%
overweight). Version 1.1 names the habitus in every prompt, adds ten people,
most of them heavier and most of them with the light olive and warm tones of
Santiago and of Hispanic Cleveland, and gives the fourteen people not yet drawn
the habitus the target needs. Habitus is independent of tone and of the
diagnosis: a photograph must not become a cue for either.

A body must not contradict the chart (faculty, 2026-09-27). The room frames
the patient from the chest up, in bed, under a blanket, so a photograph shows
face, neck, shoulders, arms and hands; height cannot be judged lying down, and
no weight is read from a picture. A person fits a case unless the body the
photograph shows clearly contradicts the weight and height in the chart
(``compatible``): the ranges are wide on purpose. The 15 kg rule of 2026-09-26 is
retired. Between two people who both fit, the one whose build is nearer the
chart comes first (``image_selection``). A case whose chart has no weight (an
encounter launched before 2026-09-27, which the engine computes at 70 kg) is not
shown a visibly obese person.
"""
from __future__ import annotations

IDENTITIES_VERSION = "1.1"

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

# What the prompt says about the body, and the body-mass index it stands for.
# Plain clinical words; realistic and dignified, never exaggerated. "normal"
# says "not athletic" because the generator draws fit bodies by default.
HABITUS = {
    "normal": {"bmi": 22.0, "words": "an ordinary untoned body of average weight, not athletic or muscular"},
    "overweight": {"bmi": 27.5,
                   "words": "overweight, with a soft rounded belly under the gown and a fuller face and neck"},
    "obese": {"bmi": 34.0,
              "words": ("obese, with a large rounded abdomen that raises the blanket, heavy upper arms and a "
                        "full face and neck, drawn realistically and with dignity, never exaggerated")},
    "severely obese": {"bmi": 44.0,
                       "words": ("severely obese, with a very large abdomen that raises the blanket, broad heavy "
                                 "arms and a full face and neck, filling most of the bed's width, drawn "
                                 "realistically and with dignity, never exaggerated")},
}
# A chart with a weight and no height (a generated case) is read at an ordinary
# adult height, the mean of Chilean and US adults.
TYPICAL_HEIGHT_M = {"female": 1.61, "male": 1.74}

# How a body looks in the room's photograph, from slim to severely obese.
APPARENT_BUILDS = ("slim", "average", "heavier", "obese", "severely obese")
# The body-mass indices each apparent build can stand for in that framing. Wide on
# purpose: a range closes only where the contradiction would be plain -- a slim
# person for an overweight-to-obese chart, an average one for obesity class II,
# an obese one for a normal weight.
BUILD_BMI = {"slim": (0.0, 28.0), "average": (17.0, 35.0), "heavier": (22.0, 40.0),
             "obese": (27.0, 99.0), "severely obese": (33.0, 99.0)}
# The ranges guide which candidate comes first; they are not an automatic test
# of incompatibility (faculty instruction of 2026-09-26, point 6). A chart
# within this many BMI units of a build's range is a small difference around a
# limit: the photograph is kept usable -- ranked after every better fit, and
# never a reason to pay for a replacement -- and only past it is the
# contradiction plain.
EDGE_BMI = 2.0
# Where each build looks most at home; between two people who both fit, the one
# in their core comes first.
BUILD_CORE = {"slim": (0.0, 25.0), "average": (18.5, 30.0), "heavier": (25.0, 35.0),
              "obese": (30.0, 40.0), "severely obese": (35.0, 99.0)}
# How the people already photographed look in their reference photograph, read
# by eye (agent, 2026-09-27) and listed for the faculty's review in
# docs/PESOS_CASOS.md: a reading of a picture, not a weight. The first sixteen
# were drawn slim or fit whatever their build word said. A person not yet
# photographed is taken to look as the prompt asks, until a photograph shows it.
APPARENT_BUILD = {
    "V01": "heavier", "V02": "slim", "V03": "slim", "V05": "slim", "V08": "heavier", "V09": "slim", "V11": "average",
    "V12": "average", "V14": "slim", "V17": "slim", "V18": "average", "V19": "heavier", "V21": "slim",
    "V22": "average", "V23": "average", "V24": "average", "V26": "average", "V27": "average", "V29": "slim",
    "V33": "obese", "V35": "obese", "V38": "severely obese",
}
_REQUESTED_BUILD = {"normal": "average", "overweight": "heavier", "obese": "obese",
                    "severely obese": "severely obese"}


def _identity(number, sex, band, tone, hair, build, face="", habitus="normal"):
    return {"id": f"V{number:02d}", "sex": sex, "band": band,
            "apparent_age": AGE_BANDS[band]["apparent"], "ages": AGE_BANDS[band]["ages"],
            "skin_tone": tone, "hair": hair, "build": build, "face": face, "habitus": habitus}


# Neutral identifiers: an id says nothing about how the person looks.
IDENTITIES = (
    # women
    _identity(1, "female", "young", 2, "shoulder-length straight brown hair tied back", "average",
              habitus="overweight"),
    _identity(2, "female", "young", 4, "long dark wavy hair in a low bun", "sturdy"),
    _identity(3, "female", "young", 6, "short natural coily black hair", "average"),
    _identity(4, "female", "adult", 1, "chin-length light brown hair", "average", habitus="obese"),
    _identity(5, "female", "adult", 3, "long straight black hair in a loose braid", "slim"),
    _identity(6, "female", "adult", 5, "black hair in short locs", "average", habitus="overweight"),
    _identity(7, "female", "middle", 2, "shoulder-length auburn hair with some gray", "average",
              habitus="obese"),
    _identity(8, "female", "middle", 4, "short dark curly hair with gray at the temples", "average",
              habitus="overweight"),
    _identity(9, "female", "middle", 6, "cropped salt-and-pepper hair", "slim"),
    _identity(10, "female", "older", 1, "short white hair", "average", habitus="overweight"),
    _identity(11, "female", "older", 3, "gray hair pulled back in a bun", "sturdy"),
    _identity(12, "female", "older", 5, "short gray coily hair", "average"),
    _identity(13, "female", "elderly", 2, "thin white hair, short", "average"),
    _identity(14, "female", "elderly", 4, "silver hair in a low bun", "slim"),
    _identity(15, "female", "elderly", 6, "short white curly hair", "average", habitus="overweight"),
    # men
    _identity(16, "male", "young", 1, "short sandy hair", "average", "clean-shaven", habitus="overweight"),
    _identity(17, "male", "young", 3, "short black straight hair", "slim", "light stubble"),
    _identity(18, "male", "young", 5, "close-cropped black hair", "sturdy", "a short trimmed beard"),
    _identity(19, "male", "adult", 2, "short dark brown hair", "average", "a short trimmed beard",
              habitus="obese"),
    _identity(20, "male", "adult", 4, "short black wavy hair", "average", "clean-shaven", habitus="overweight"),
    _identity(21, "male", "adult", 6, "shaved head", "slim", "a thin mustache"),
    _identity(22, "male", "middle", 1, "thinning gray-blond hair", "average", "clean-shaven"),
    _identity(23, "male", "middle", 3, "short black hair graying at the sides", "sturdy", "gray stubble"),
    _identity(24, "male", "middle", 5, "short gray-black coily hair", "slim", "a gray goatee"),
    _identity(25, "male", "older", 2, "bald with a fringe of white hair", "average", "clean-shaven",
              habitus="obese"),
    _identity(26, "male", "older", 4, "short gray hair", "slim", "a white mustache"),
    _identity(27, "male", "older", 6, "very short white hair", "average", "a short white beard"),
    _identity(28, "male", "elderly", 3, "sparse white hair combed back", "slim", "clean-shaven"),
    _identity(29, "male", "elderly", 5, "short white coily hair", "average", "white stubble"),
    _identity(30, "male", "elderly", 1, "white hair, mostly bald on top", "average", "a short white beard",
              habitus="overweight"),
    # Version 1.1: heavier bodies, mostly in the tones of Santiago and of Hispanic Cleveland.
    _identity(31, "female", "young", 3, "long dark brown hair in a ponytail", "average", habitus="obese"),
    _identity(32, "female", "adult", 3, "shoulder-length black hair", "average", habitus="severely obese"),
    _identity(33, "female", "middle", 3, "dark hair with gray streaks in a low bun", "average", habitus="obese"),
    _identity(34, "female", "older", 2, "short permed gray hair", "average", habitus="obese"),
    _identity(35, "female", "middle", 5, "short black hair with gray at the temples", "average", habitus="obese"),
    _identity(36, "male", "young", 6, "short black hair", "average", "a thin beard", habitus="obese"),
    _identity(37, "male", "adult", 3, "short black hair", "average", "a black mustache", habitus="overweight"),
    _identity(38, "male", "middle", 5, "short gray-black hair", "average", "clean-shaven",
              habitus="severely obese"),
    _identity(39, "male", "middle", 4, "short black hair graying at the temples", "average", "gray stubble",
              habitus="obese"),
    _identity(40, "male", "older", 3, "combed-back gray hair", "average", "a gray mustache",
              habitus="overweight"),
)

BY_ID = {identity["id"]: identity for identity in IDENTITIES}

_AGE_WORDS = {27: "in their late twenties", 40: "around forty", 55: "in their mid-fifties",
              68: "in their late sixties", 81: "in their early eighties"}


def identity(identity_id):
    try:
        return BY_ID[identity_id]
    except KeyError:
        raise KeyError(f"Unknown visual identity {identity_id!r}.") from None


def apparent_build(identity_record):
    """How this person's body looks in the room's photograph (or will, as asked)."""
    return APPARENT_BUILD.get(identity_record["id"]) or _REQUESTED_BUILD[identity_record.get("habitus", "normal")]


def case_bmi(patient):
    """The body-mass index of the chart, or None when the chart has no weight."""
    import patient_body
    value = patient_body.bmi(patient)
    if value is not None:
        return value
    recorded = patient_body.body(patient)
    if recorded and recorded.get("weight_kg") and patient.get("sex") in TYPICAL_HEIGHT_M:
        return round(recorded["weight_kg"] / TYPICAL_HEIGHT_M[patient["sex"]] ** 2, 1)
    return None


def compatible(identity_record, patient):
    """Whether this person can be the case's patient: age, sex, and no plain bodily contradiction.

    The BMI ranges guide the choice among candidates (``near``); they exclude a
    photograph only when the contradiction would be plain -- more than
    ``EDGE_BMI`` beyond the build's range. A chart sitting just past a limit is
    a small difference, not a contradiction, and never a reason to regenerate
    (faculty instruction of 2026-09-26, point 6).
    """
    if not isinstance(patient, dict):
        return False
    age, sex = patient.get("age_years"), patient.get("sex")
    if type(age) is not int or sex not in ("male", "female"):
        return False
    low, high = identity_record["ages"]
    if identity_record["sex"] != sex or not low <= age <= high:
        return False
    weight = patient.get("weight_kg")
    if weight is not None and (isinstance(weight, bool) or not isinstance(weight, (int, float))):
        return False
    build = apparent_build(identity_record)
    bmi = case_bmi(patient)
    if bmi is None:
        # No weight in the chart: the engine computes at 70 kg.
        return build not in ("obese", "severely obese")
    lowest, highest = BUILD_BMI[build]
    return lowest - EDGE_BMI <= bmi < highest + EDGE_BMI


def near(identity_record, patient):
    """How far the chart sits from this person's build: 0 in its core, 1 in its range, 2 at the range's edge."""
    bmi = case_bmi(patient)
    if bmi is None:
        return 0
    build = apparent_build(identity_record)
    core_low, core_high = BUILD_CORE[build]
    if core_low <= bmi < core_high:
        return 0
    lowest, highest = BUILD_BMI[build]
    return 1 if lowest <= bmi < highest else 2


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
    habitus = identity_record.get("habitus", "normal")
    parts.append(identity_record["build"] + " build" if habitus == "normal" and identity_record["id"] in _DRAWN_AS_BUILT
                 else HABITUS[habitus]["words"])
    return f"a fictional {noun} {age}: " + "; ".join(parts)


# Photographed under version 1.0 with their build word; their photographs are
# what they look like, so their description stays as it was.
_DRAWN_AS_BUILT = frozenset({"V02", "V03", "V05", "V09", "V11", "V12", "V14", "V17", "V18", "V21", "V22", "V23",
                             "V24", "V26", "V27", "V29"})


def person_phrase(identity_record):
    """The person as the photograph prompts name them: 'man in his late sixties (…)'."""
    noun = "woman" if identity_record["sex"] == "female" else "man"
    age = _AGE_WORDS[identity_record["apparent_age"]].replace(
        "their", "her" if identity_record["sex"] == "female" else "his")
    return f"{noun} {age} ({describe(identity_record).split(': ', 1)[1]})"


def distribution(records=IDENTITIES):
    """How the bank is spread: tones per band and sex, builds per tone. For the report."""
    tones, builds, bands, habitus = {}, {}, {}, {}
    for record in records:
        tones.setdefault((record["sex"], record["band"]), []).append(record["skin_tone"])
        builds.setdefault(record["skin_tone"], []).append(record["build"])
        habitus.setdefault(record.get("habitus", "normal"), []).append(record["skin_tone"])
        bands.setdefault(record["band"], 0)
        bands[record["band"]] += 1
    return {"tones_by_sex_and_band": {f"{sex}/{band}": sorted(values)
                                      for (sex, band), values in sorted(tones.items())},
            "builds_by_tone": {tone: sorted(values) for tone, values in sorted(builds.items())},
            "tones_by_habitus": {name: sorted(values) for name, values in sorted(habitus.items())},
            "identities_by_band": bands}
