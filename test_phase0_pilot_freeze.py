"""Phase 0 (0K): the freeze manifest is the one the code enforces.

Generated, like the hypoglycaemia catalogue: an edit made by hand would drift from the
decisions ``pilot_freeze`` holds and the battery ``pilot_acceptance`` runs.
"""
import pilot_freeze


def test_the_published_manifest_is_the_one_the_code_produces():
    import tools_pilot_freeze
    assert tools_pilot_freeze.TARGET.read_text(encoding="utf-8") == tools_pilot_freeze.build(), (
        "docs/revision/PILOT_FREEZE_MANIFEST.md is out of date; run tools_pilot_freeze.py --write")


def test_the_manifest_names_every_case_versions_flags_and_legacy_routes():
    import tools_pilot_freeze
    text = tools_pilot_freeze.build()
    for variant in pilot_freeze.CASES:
        assert f"`{variant}`" in text, variant
    for flag in pilot_freeze.RUNTIME_FLAGS:
        assert flag in text
    assert "R1-03" in text and "R2-01" in text and "fastReruns" in text
    assert pilot_freeze.FREEZE_ID in text
    import curriculum
    allowed = text.split("## Desafíos permitidos")[1].split("## Casos")[0]
    for challenge in curriculum.assignable_challenges(3):
        assert f"| {challenge} |" in allowed
    assert not [legacy for legacy in pilot_freeze.EXCLUDED_LEGACY_CHALLENGES if legacy in allowed]
    for variant in pilot_freeze.accepted_variants():
        version = pilot_freeze.case_versions(variant)
        assert f"| `{variant}` | `{version['case']}` | `{version['declaration']}` |" in text


def test_the_declaration_the_freeze_names_is_the_one_an_encounter_freezes():
    import evaluation_basis
    for variant in pilot_freeze.accepted_variants():
        frozen = evaluation_basis.freeze(variant)
        assert frozen["fingerprint"].startswith(pilot_freeze.case_versions(variant)["declaration"]), variant


def test_an_encounter_keeps_the_case_and_the_code_it_started_with():
    """Each turn records the code it ran on; the case travels inside the encounter's state."""
    import trace_phase0
    from test_phase0_observation_and_provenance import _state
    state = _state("acs_54m_inferior")
    versions = trace_phase0.versions(state)
    assert versions["variant_id"] == "acs_54m_inferior" and versions["code_version"]
    assert versions["case_bank_version"] == pilot_freeze.versions()["case_bank"]
