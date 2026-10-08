"""The faculty's approvals of the Spanish narrative and rubric, as the pilot candidate carries them (B-5, IG-0).

The faculty reviewed the Spanish of the 30 pilot cases and of the five rubric
domains outside the app, against exact versions (``case_text.version``,
``rubric_text.version``), and approved each one at the version it read
(docs/revision/B5_RELATO_*.md, 2026-10-07 and 2026-10-08; RUB, 2026-10-07). A
fresh pilot database holds no review, so the candidate carries those approvals
in the repository (``case_text/es/approvals.json`` and
``rubric_text/es/approvals.json``, path a, faculty decision of 2026-10-07).

This tool checks and writes those two files. It fails closed:

* it never edits a translation, and never approves anything the faculty did
  not approve: the approved versions below are the faculty's, copied from the
  review documents once, and a test keeps them equal to those documents;
* ``--check`` compares the version on file of every case (or domain) with its
  approved version and exits non-zero on the first difference, naming it;
* ``--write`` writes the file only when every case (or domain) matches, every
  passage still translates what the case says today, and the set is exactly
  the pilot's 30 cases (or the five domains) -- no missing, no extra (the
  faculty sandbox case ``trauma_hemothorax_41m`` is not one), no duplicate;
* ``--verify`` reads the committed file and checks its shape and content the
  same way, without writing anything.

The files carry only ``variant_id`` (or ``domain_id``), ``version`` and
``decision``: no reviewer, no name, no personal identifier.

Usage::

    python3 tools_case_text_approvals.py --check            # the narrative
    python3 tools_case_text_approvals.py --write
    python3 tools_case_text_approvals.py --verify
    python3 tools_case_text_approvals.py --rubric --check   # the rubric
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: The version of each pilot case's narrative the faculty approved (B-5; lot documents
#: docs/revision/B5_RELATO_R1A.md to B5_RELATO_R6.md and B5_RELATO_INTEGRIDAD_30.md). R1A
#: to R4A were approved on 2026-10-07 and 2026-10-08; R4B, R5 and R6 on 2026-10-08.
APPROVED_NARRATIVE = {
    "acs_54m_inferior": "e1afcda52d3e3fab6853c2b1bd44bf07c4e6ef04296cdde9f7fe87723a48076a",
    "acs_61m_posterior": "a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890",
    "acs_66f_nonst": "d64dc72663d6d94f4b919ab8529e2314263cbb010d4de66e52738a1221eb95c1",
    "acs_48m_wellens": "13a569872e3a88cf1f01537ee50544f5057cc21942bd10d4e3b3ba03681ab04d",
    "acs_52m_de_winter": "daf766118b4ae254ae6fa4261bebb40a96eb3ce6d3a4d92f3048d0f5acdc4056",
    "acs_70f_left_main": "c94b56ee409f799557c53b017e5144c4c076549426d9a75aaec6cd314bddb552",
    "pneumonia_46f": "d16cb3330fc87b73abb6d2e03eae76b428b4f61c0c33b9848cff27caa22977ca",
    "pneumonia_83m": "45a84e879f0a33e8167bf2de5937d23d7eb8ef4068439f77f162563640cd0c1b",
    "pulmonary_edema_58m": "dffcae29509ba47cbea4b30959c62e9093d6bce2df1099d724495a6238f804ae",
    "pulmonary_edema_75f": "4695ee50cfa00208c0c9fa70b527e7495119392cf279487b72a5880d25d2d06c",
    "asthma_24f": "844d280d53271a3444adc8293a73f42ec5aac090a08d4af839d5100a5fbc4615",
    "asthma_49m": "6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540",
    "pulmonary_embolism_33f": "d3a826e9c4679a8944e2a5eb5e174f36ba800ca0c91a48bd7a14f8afbe05e5ab",
    "pulmonary_embolism_61m": "71c15c2b2811acd747993f8bb4e5d6f0cad5083ceaf035655fe7aba055ebd714",
    "bradycardia_ccb_68m": "10b926936212c922ccd2a3ce699c4d87df4f76d4c50e456bbf0c628d3f8932c4",
    "bradycardia_avb3_78f": "677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7",
    "bradycardia_bb_54f": "45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9",
    "bradycardia_hyperk_63m": "89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8",
    "hypoglycemia_28m": "65cae7edde83847fd6641ca77a94b034da1ced9e1228df8894f9cbe09ab61950",
    "hypoglycemia_76f": "a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845",
    "hypoglycemia_54m_thiamine": "cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a",
    "opioid_35m": "a130f860dd36d35d309fb845cd389aa59551bc6a95643b2324900bc05649ad12",
    "opioid_67f": "6f065b332e31a608efe54e082265f310eeebfff5aecbc06898905faa0aba2568",
    "gi_bleed_57m": "5d758337c68f1c59fea20607c1d65cd939dcf8953a4ff85cc5b1867a7e9abcca",
    "gi_bleed_72f": "9c6d28681ed8084f616d940bfe16d3475aec1a724f656a43f177930b82dd634b",
    "anaphylaxis_29f": "7ea433dc65d28ee292505e42846080aef573ba0175f327179bf696843567a237",
    "anaphylaxis_63m_betablocked": "c153cc253f35dc6509d059ec916100362f97c02616eac022c3a66f4a5b266200",
    "renal_colic_34m": "ec65504955b7c09e9028358d829d377d4b7a96f8f3d9246b335d44e333f710fa",
    "obstructive_pyelonephritis_58f": "3a98131bf83b59dd084ce0b1a2a9ad8f3d93d404372e81260254a1e9f5c50c65",
    "trauma_limb_hemorrhage_27m": "58187a00974b8795cd1da0d72e99da0e7c65162bfeeca1531da1db19c11536e7",
}

#: The version of each rubric domain's descriptors the faculty approved (RUB, 2026-10-07): D1 to D3 as
#: drafted; D4 with R-1 (revisar = check, vigilar = watch); D5 with option (b), «un control posterior».
APPROVED_RUBRIC = {
    "D1": "552618f3085a42ae3d6e13d8be3338a60ce3fb713f1a223eb74825e505fe1369",
    "D2": "0393ca0dd6717a6a54b649541e7f140c1d0dd822cbf8e98e205f8456df6763c4",
    "D3": "bf7395c34d28bce676adfc5bad71f5a6d4a1dbdced9952c64dda64f52284a191",
    "D4": "041597d975468e31bdf8d6c1d1ddd35e289b98fa05b5e8d3b9106db0c36e2dad",
    "D5": "52958f1cdcd83dc9e7f4535c9ae65862f0f4ab829d230ac4bd8eff617abbdac4",
}

LANGUAGE = "es"
FIELDS = {"narrative": ("variant_id", "version", "decision"), "rubric": ("domain_id", "version", "decision")}


class ApprovalError(Exception):
    """The approvals cannot be written or are not what the faculty approved."""


def pilot_cases():
    """The 30 resident-pilot cases, in the manifest's order (the sandbox case is not one)."""
    import pilot_freeze
    return list(pilot_freeze.accepted_variants())


def narrative_rows(language=LANGUAGE):
    """[{variant_id, version, approved, passages, translated, problem}] for every pilot case."""
    import case_text
    drafts = case_text.passages(language)
    english = case_text.current_english()
    rows = []
    for variant in pilot_cases():
        drafted = drafts.get(variant) or {}
        version = case_text.version(drafted, language) if drafted else None
        usable = case_text.usable_rows(variant, drafted, english, language)
        approved = APPROVED_NARRATIVE.get(variant)
        if not drafted:
            problem = "no Spanish draft on file"
        elif approved is None:
            problem = "no faculty approval for this case"
        elif version != approved:
            problem = f"version on file {version} is not the approved {approved}"
        elif set(drafted) != set(english.get(variant) or {}):
            problem = "the drafted passages are not exactly the passages the case has today"
        elif set(usable) != set(drafted):
            problem = "a passage no longer translates what the case says today"
        else:
            problem = None
        rows.append({"variant_id": variant, "version": version, "approved": approved,
                     "passages": len(drafted), "translated": len(usable), "problem": problem})
    return rows


def narrative_problems(language=LANGUAGE):
    """Every reason the narrative pack cannot be written. Empty means it can."""
    problems = [f"{row['variant_id']}: {row['problem']}" for row in narrative_rows(language) if row["problem"]]
    pilot = set(pilot_cases())
    problems += [f"{case}: approved but not a pilot case" for case in sorted(set(APPROVED_NARRATIVE) - pilot)]
    if len(pilot) != 30:
        problems.append(f"the pilot has {len(pilot)} cases, not 30")
    return problems


def rubric_rows(language=LANGUAGE):
    """[{domain_id, version, approved, current, problem}] for every rubric domain."""
    import rubric
    import rubric_text
    drafts = rubric_text.drafts(language)
    rows = []
    for domain in rubric.DOMAINS:
        drafted = drafts.get(domain) or {}
        version = rubric_text.version(domain, drafted, language) if drafted else None
        current = bool(drafted) and rubric_text.current(domain, drafted, language)
        approved = APPROVED_RUBRIC.get(domain)
        if not drafted:
            problem = "no Spanish draft on file"
        elif approved is None:
            problem = "no faculty approval for this domain"
        elif version != approved:
            problem = f"version on file {version} is not the approved {approved}"
        elif not current:
            problem = "the draft no longer translates what the rubric says today"
        else:
            problem = None
        rows.append({"domain_id": domain, "version": version, "approved": approved, "current": current,
                     "problem": problem})
    return rows


def rubric_problems(language=LANGUAGE):
    import rubric
    problems = [f"{row['domain_id']}: {row['problem']}" for row in rubric_rows(language) if row["problem"]]
    problems += [f"{domain}: approved but not a rubric domain"
                 for domain in sorted(set(APPROVED_RUBRIC) - set(rubric.DOMAINS))]
    if len(rubric.DOMAINS) != 5:
        problems.append(f"the rubric has {len(rubric.DOMAINS)} domains, not 5")
    return problems


def pack(kind):
    """The rows the file carries, in a fixed order: only the three fields the runtime reads."""
    if kind == "narrative":
        return [{"variant_id": case, "version": APPROVED_NARRATIVE[case], "decision": "approved"}
                for case in pilot_cases()]
    import rubric
    return [{"domain_id": domain, "version": APPROVED_RUBRIC[domain], "decision": "approved"}
            for domain in rubric.DOMAINS]


def path(kind, language=LANGUAGE):
    import case_text
    import rubric_text
    return (case_text.ROOT if kind == "narrative" else rubric_text.ROOT) / language / "approvals.json"


def serialize(rows):
    return json.dumps(rows, ensure_ascii=False, indent=2) + "\n"


def problems(kind, language=LANGUAGE):
    return narrative_problems(language) if kind == "narrative" else rubric_problems(language)


def write(kind, language=LANGUAGE, target=None):
    """Write the pack, or raise without writing anything when a single check fails."""
    found = problems(kind, language)
    if found:
        raise ApprovalError("Nothing was written. " + "; ".join(found))
    target = Path(target) if target else path(kind, language)
    target.write_text(serialize(pack(kind)), encoding="utf-8")
    return target


def verify_file(kind, file_path=None, language=LANGUAGE):
    """Every way the committed file differs from what the faculty approved. Empty is good."""
    import rubric
    file_path = Path(file_path) if file_path else path(kind, language)
    key = FIELDS[kind][0]
    expected = APPROVED_NARRATIVE if kind == "narrative" else APPROVED_RUBRIC
    wanted = pilot_cases() if kind == "narrative" else list(rubric.DOMAINS)
    if not file_path.exists():
        return [f"{file_path.name} does not exist"]
    try:
        rows = json.loads(file_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        return [f"{file_path.name} is not valid JSON: {error}"]
    if not isinstance(rows, list):
        return [f"{file_path.name} is not a list"]
    found, seen = [], []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            found.append(f"row {index} is not an object")
            continue
        if set(row) != set(FIELDS[kind]):
            found.append(f"row {index} has the fields {sorted(row)}, not {list(FIELDS[kind])}")
        ident = row.get(key)
        if row.get("decision") != "approved":
            found.append(f"{ident}: the decision is {row.get('decision')!r}, not 'approved'")
        if ident in seen:
            found.append(f"{ident}: duplicated")
        seen.append(ident)
        if ident not in expected:
            found.append(f"{ident}: not one the faculty approved for the pilot")
        elif row.get("version") != expected[ident]:
            found.append(f"{ident}: version {row.get('version')} is not the approved {expected[ident]}")
    found += [f"{ident}: missing" for ident in wanted if ident not in seen]
    if not found and file_path.read_text(encoding="utf-8") != serialize(pack(kind)):
        found.append(f"{file_path.name} is not written as this tool writes it")
    return found + problems(kind, language)


def report(kind, language=LANGUAGE):
    """The table the tool prints: one line per case or domain, and the verdict."""
    rows = narrative_rows(language) if kind == "narrative" else rubric_rows(language)
    key = FIELDS[kind][0]
    lines = [f"{'ID':32} {'VERSION ON FILE':18} {'APPROVED':18} RESULT"]
    for row in rows:
        lines.append(f"{row[key]:32} {str(row['version'])[:16]:18} {str(row['approved'])[:16]:18} "
                     + ("OK" if not row["problem"] else "STOP: " + row["problem"]))
    found = problems(kind, language)
    lines.append("")
    lines.append(f"{len(rows) - sum(1 for r in rows if r['problem'])} of {len(rows)} match the approved versions."
                 + (" Approvals can be written." if not found else " STOP: return to the faculty before writing."))
    return "\n".join(lines), not found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rubric", action="store_true", help="the rubric domains instead of the narrative")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    kind = "rubric" if args.rubric else "narrative"
    if args.check:
        text, ok = report(kind)
        print(text)
        return 0 if ok else 1
    if args.write:
        try:
            target = write(kind)
        except ApprovalError as error:
            print(error)
            return 1
        print(f"Wrote {target.relative_to(ROOT)}: {len(pack(kind))} approvals.")
        return 0
    found = verify_file(kind)
    print("\n".join(found) if found else f"{path(kind).relative_to(ROOT)}: as the faculty approved.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
