"""Reorganising the hypoglycaemia code changed nothing it was not meant to change.

Regression, not acceptance (hypoglycemia_preservation): the record of
2026-09-25 is today's behaviour before the catalogue existed. A difference is
accepted only when the corrections registry declares it; anything else is a
change nobody decided.
"""
import pytest

import corrections_registry
import hypoglycemia_preservation as preservation


@pytest.fixture(scope="module")
def record():
    return preservation.load_golden()["variants"]


@pytest.fixture(scope="module")
def now():
    return preservation.capture()


def _differences(old, new, path=""):
    if isinstance(old, dict) and isinstance(new, dict):
        found = []
        for key in sorted(set(old) | set(new)):
            found += _differences(old.get(key, "<missing>"), new.get(key, "<missing>"), f"{path}/{key}")
        return found
    return [path] if old != new else []


def test_the_record_covers_the_three_cases_and_twenty_scripts(record):
    assert set(record) == set(preservation.VARIANTS)
    for variant in record.values():
        assert set(variant["scripts"]) == set(preservation.SCRIPTS)


def test_bank_cases_match_the_record_except_declared_corrections(record, now):
    allowed = corrections_registry.preserved_differences()
    for variant_id in preservation.VARIANTS:
        differences = _differences(record[variant_id]["variant"], now[variant_id]["variant"])
        assert set(differences) <= allowed["variant_fields"].get(variant_id, set()), (variant_id, differences)
        assert record[variant_id]["launch"] == now[variant_id]["launch"], variant_id


def test_every_trajectory_matches_the_record_except_declared_corrections(record, now):
    allowed = corrections_registry.preserved_differences()["scripts"]
    for variant_id in preservation.VARIANTS:
        changed = {name for name in preservation.SCRIPTS
                   if [s["fingerprint"] for s in record[variant_id]["scripts"][name]]
                   != [s["fingerprint"] for s in now[variant_id]["scripts"][name]]}
        assert changed == allowed.get(variant_id, set()), (variant_id, sorted(changed))


def test_declarations_match_the_record_except_the_new_version(record, now):
    new_versions = corrections_registry.preserved_differences()["declarations"]
    for variant_id in preservation.VARIANTS:
        same = record[variant_id]["declaration"] == now[variant_id]["declaration"]
        assert same is (variant_id not in new_versions), variant_id


def test_the_previous_declaration_of_the_changed_case_is_kept_for_its_encounters(record):
    import evaluation_basis
    legacy = evaluation_basis.legacy()["declarations"]
    for variant_id in preservation.VARIANTS:
        assert legacy[variant_id] == record[variant_id]["declaration"], variant_id


def test_every_declared_difference_actually_occurs(record, now):
    """A registry entry that promises a change nobody can see is a stale entry."""
    allowed = corrections_registry.preserved_differences()
    for variant_id, fields in allowed["variant_fields"].items():
        differences = set(_differences(record[variant_id]["variant"], now[variant_id]["variant"]))
        assert fields <= differences, (variant_id, sorted(fields - differences))
    for variant_id, scripts in allowed["scripts"].items():
        for name in scripts:
            assert ([s["fingerprint"] for s in record[variant_id]["scripts"][name]]
                    != [s["fingerprint"] for s in now[variant_id]["scripts"][name]]), (variant_id, name)
