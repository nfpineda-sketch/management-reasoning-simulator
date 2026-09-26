"""The draw behind the weight and height of the 31 bank cases, and its checks (faculty, 2026-09-27).

    python3 tools_case_bodies.py            # the table, as patient_body.BODIES holds it
    python3 tools_case_bodies.py --check    # the faculty's conditions, one line each

The faculty asked (2026-09-27) for varied bodies without rigid associations:
habitus is not tied to age, diagnosis, severity, response to treatment or
expected conduct; nobody gets a normal weight because of chemotherapy, alcohol or
poor intake; heights vary as adults' do; and no weight is chosen to fit a
photograph or justified by changing a history. The draw below is how that was
done, reproducibly. It never reads a photograph, a history or a comorbidity.

1. Habitus counts, an educational starting point rather than a prevalence to
   reproduce: 8 normal, 11 overweight, 6 obese class I, 4 class II, 2 class III.
2. They are dealt to the cases by a seeded shuffle. A deal is kept only if every
   family has at least two of normal / overweight / obese; obesity appears both
   under 40 and from 70; normal weight appears between 40 and 69; each sex has
   obesity; and the share of obesity among the critically ill and the rest
   differs by no more than 20 points.
3. Height: normal by sex (men 1.72 m, women 1.59 m, SD 7.5 and 7 cm; Chile ENS
   2016-17 and US NHANES sit either side), bounded at 2.2 SD, 1 cm less per decade
   after 50. Body-mass index: uniform within the class. Weight = BMI × height²,
   to the kilogram. No two patients share both height and weight.

``patient_body.BODIES`` adds how each was obtained. The patient on dialysis
records no dry weight: the one once shown was an inference the faculty
withdrew (2026-09-26), pending a defined value.
"""
from __future__ import annotations

import argparse
import random

SEED = "pesos-casos-2026-09-27"
COUNTS = {"normal": 8, "overweight": 11, "obese I": 6, "obese II": 4, "obese III": 2}
BMI_RANGE = {"normal": (19.0, 24.8), "overweight": (25.2, 29.8), "obese I": (30.2, 34.8),
             "obese II": (35.2, 39.8), "obese III": (40.2, 47.0)}
HEIGHT = {"male": (1.72, 0.075), "female": (1.59, 0.07)}
OBESE = ("obese I", "obese II", "obese III")


def coarse(habitus):
    return "obese" if habitus in OBESE else habitus


def cases():
    """What the draw may know about each case: family, age, sex, and whether it arrives critically ill."""
    from clinical_cases import FAMILIES
    out = []
    for family, spec in FAMILIES.items():
        for variant in spec["variants"]:
            o = variant.get("observable", {})
            critical = (o.get("sbp", 120) < 90 or o.get("spo2", 99) < 88 or o.get("mental_status") != "Alert"
                        or o.get("respiratory_rate", 16) <= 8 or o.get("hr", 80) < 45 or o.get("hr", 80) > 130)
            out.append({"case": variant["id"], "family": family, "age": variant["patient"]["age_years"],
                        "sex": variant["patient"]["sex"], "critical": critical})
    return out


def conditions(rows):
    """Each of the faculty's conditions, with whether this deal meets it."""
    by_family = {}
    for row in rows:
        by_family.setdefault(row["family"], set()).add(coarse(row["habitus"]))
    share = lambda group: sum(r["habitus"] in OBESE for r in group) / max(1, len(group))
    critical = [r for r in rows if r["critical"]]
    others = [r for r in rows if not r["critical"]]
    return {
        "every family has at least two of normal / overweight / obese":
            all(len(kinds) >= 2 for kinds in by_family.values()),
        "obesity under 40": any(r["habitus"] in OBESE for r in rows if r["age"] < 40),
        "obesity from 70": any(r["habitus"] in OBESE for r in rows if r["age"] >= 70),
        "normal weight between 40 and 69": any(r["habitus"] == "normal" for r in rows if 40 <= r["age"] < 70),
        "obesity in both sexes": all(any(r["habitus"] in OBESE for r in rows if r["sex"] == sex)
                                     for sex in ("male", "female")),
        "obesity among the critically ill within 20 points of the rest": abs(share(critical) - share(others)) <= .20,
    }


def _bodies(rng, rows):
    for row in rows:
        mean, sd = HEIGHT[row["sex"]]
        z = max(-2.2, min(2.2, rng.gauss(0, 1)))
        height = round(mean + sd * z - 0.01 * max(0, (row["age"] - 50) // 10), 2)
        low, high = BMI_RANGE[row["habitus"]]
        weight = round(rng.uniform(low, high) * height * height)
        row.update(height_m=height, weight_kg=weight)
    pairs = [(row["height_m"], row["weight_kg"]) for row in rows]
    return len(set(pairs)) == len(pairs)


def draw():
    """The table and the number of deals tried before one met every condition."""
    rng = random.Random(SEED)
    base = cases()
    labels = [name for name, count in COUNTS.items() for _ in range(count)]
    for attempt in range(1, 10001):
        rng.shuffle(labels)
        rows = [dict(row, habitus=habitus) for row, habitus in zip(base, labels)]
        if all(conditions(rows).values()) and _bodies(rng, rows):
            return rows, attempt
    raise RuntimeError("No deal met every condition.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, attempt = draw()
    if args.check:
        print(f"seed {SEED}, deal {attempt}")
        for name, met in conditions(rows).items():
            print(f"{'yes' if met else 'NO '}  {name}")
        return
    import patient_body
    for row in rows:
        ideal = patient_body.predicted_weight(row["sex"], row["height_m"])
        print(f"{row['case']:32s} {row['age']:3d} {row['sex'][0]} {row['habitus']:10s} {row['height_m']:.2f} m "
              f"{row['weight_kg']:4d} kg BMI {row['weight_kg'] / row['height_m'] ** 2:4.1f} ideal {ideal:5.1f} kg")


if __name__ == "__main__":
    main()
