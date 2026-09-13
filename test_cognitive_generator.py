"""Frozen, varied case generation and strict model-selection boundaries."""
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from cognitive_catalog import BIAS_CHALLENGES, BIAS_CONTEXTS, FAMILY_LABELS
from cognitive_generator import GENERATOR_VERSION, SPEC_VERSION, generate_cognitive_encounter


def base_state():
    """Deliberately contaminated legacy fields must not enter a new family."""
    return {
        "case_id": "PS001", "sim_time": 0,
        "observable": {"rhythm": "AF", "hr": 174, "sbp": 94, "dbp": 56, "crt": 4, "spo2": 93},
        "hidden": {"infection_burden": .95, "rhythm_coupling_v2": True,
                   "vasoplegia_severity": .9, "source": "urinary", "adrenergic_drive": .8},
        "treatments": {"norepinephrine": True, "norepinephrine_rate": .2,
                       "invasive_ventilation": True, "oxygen_device": "Non-rebreather mask",
                       "administered_medications": [{"agent": "amiodarone"}]},
        "diagnostics": {"urinalysis": "legacy infection"},
        "diagnostic_history": [{"diagnostic": "urinalysis", "content": "legacy infection"}],
        "encounter_facts": {"legacy_fact": "70-year-old man with urinary infection"},
        "encounter_spec": {"case_family": "PS001", "patient_facts": {"legacy_fact": True}},
    }


class SelectionClient:
    def __init__(self, payload=None, *, status="completed", failure=None, refusal=False):
        self.payload = payload
        self.status = status
        self.failure = failure
        self.refusal = refusal
        self.calls = []
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure
        output = [SimpleNamespace(content=[SimpleNamespace(type="refusal")])] if self.refusal else []
        return SimpleNamespace(status=self.status,
                               output_text=self.payload if isinstance(self.payload, str) else json.dumps(self.payload),
                               output=output,
                               usage=SimpleNamespace(input_tokens=18, output_tokens=7, total_tokens=25))


@pytest.mark.parametrize("challenge_id", list(BIAS_CHALLENGES))
def test_every_challenge_uses_only_compatible_distinct_family_variants(challenge_id):
    from clinical_cases import FAMILIES
    challenge = BIAS_CHALLENGES[challenge_id]
    for family_id in challenge["families"]:
        for variant in FAMILIES[family_id]["variants"]:
            original = base_state()
            untouched = deepcopy(original)
            result = generate_cognitive_encounter(challenge_id, original, seed=13,
                                                 family_id=family_id, variant_id=variant["id"])
            state, spec = result["state"], result["spec"]
            assert original == untouched
            assert state["engine_family"] == spec["case_family"] == family_id
            assert spec["variant_id"] == variant["id"]
            assert spec["clinical_case"] == variant
            assert state["observable"] == spec["initial_observable"] == variant["observable"]
            assert state["encounter_facts"] == spec["patient_facts"] == variant["patient"]
            assert spec["visual_profile"] == variant["visual_profile"]
            assert spec["ecg_profile"] == state["ecg_profile"] == variant["ecg_profile"]
            assert spec["schema_version"] == SPEC_VERSION
            assert spec["generator_version"] == GENERATOR_VERSION
            assert variant["presentation"] in result["presentation"]
            assert state["case_id"].startswith("CE-")
            assert state["sim_time"] == 0
            assert state["family_state"] == {}
            assert not state["diagnostics"] and not state["diagnostic_history"]
            assert not state["treatments"]["administered_medications"]
            assert not state["treatments"]["norepinephrine"]
            assert not state["treatments"]["invasive_ventilation"]
            assert not state["hidden"]["rhythm_coupling_v2"]
            assert not state["hidden"]["infection_burden"]
            assert state["hidden"]["source"] is None
            assert "legacy_fact" not in state["encounter_facts"]


def test_seed_reproducibility_and_variety_are_not_only_af_variants():
    from clinical_cases import FAMILIES
    selected = set()
    for challenge_id in BIAS_CHALLENGES:
        for seed in range(24):
            first = generate_cognitive_encounter(challenge_id, base_state(), seed=seed)
            second = generate_cognitive_encounter(challenge_id, base_state(), seed=seed)
            assert first == second
            selected.add((first["spec"]["case_family"], first["spec"]["variant_id"]))
    assert {family for family, _ in selected} == set(FAMILY_LABELS)
    assert len(selected) == sum(len(family["variants"]) for family in FAMILIES.values())


def test_saved_identity_and_spec_do_not_alias_global_case_bank_or_each_other():
    from clinical_cases import FAMILIES
    result = generate_cognitive_encounter("R1-05", base_state(), seed=5)
    frozen = deepcopy(result["spec"])
    family = result["spec"]["case_family"]
    global_before = deepcopy(FAMILIES[family])
    result["state"]["encounter_facts"]["private_test"] = "changed"
    result["state"]["observable"]["hr"] = 999
    result["state"]["encounter_spec"]["clinical_case"]["presentation"] = "changed"
    assert result["spec"] == frozen
    assert FAMILIES[family] == global_before
    result["spec"]["clinical_case"]["patient"]["private_test"] = "changed"
    assert "private_test" not in result["spec"]["patient_facts"]
    assert FAMILIES[family] == global_before


def test_content_digest_matches_frozen_serialized_spec():
    result = generate_cognitive_encounter("R2-02", base_state(), seed=17)
    spec = deepcopy(result["spec"])
    checksum = spec.pop("content_sha256")
    assert checksum == hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def test_valid_ai_selects_only_identifiers_without_rewriting_clinical_facts():
    from clinical_cases import FAMILIES
    family_id = BIAS_CHALLENGES["R2-02"]["families"][-1]
    case = FAMILIES[family_id]["variants"][-1]
    client = SelectionClient({"family_id": family_id, "variant_id": case["id"]})
    result = generate_cognitive_encounter("R2-02", base_state(), client=client, model="test-selector", seed=7)
    assert result["source"] == "ai" and result["warning"] is None
    assert result["spec"]["clinical_case"] == case
    assert result["spec"]["provenance"]["model"] == "test-selector"
    assert result["spec"]["provenance"]["usage"] == {"input_tokens": 18, "output_tokens": 7, "total_tokens": 25}
    call = client.calls[0]
    assert call["store"] is False
    schema = call["text"]["format"]["schema"]
    assert call["text"]["format"]["strict"] is True
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"family_id", "variant_id"}
    assert set(schema["properties"]) == {"family_id", "variant_id"}
    payload = json.loads(call["input"])
    assert set(payload) == {"objective", "variation_seed", "choices"}
    assert all(set(choice) == {"family_id", "variant_id", "presentation"} for choice in payload["choices"])
    assert "legacy infection" not in call["input"]
    assert "hidden" not in call["input"]


@pytest.mark.parametrize("client", [
    SelectionClient({"family_id": "PS001", "variant_id": "legacy"}),
    SelectionClient({"family_id": "acs", "variant_id": "missing"}),
    SelectionClient({"family_id": "acs", "variant_id": "missing", "new_vitals": {"hr": 50}}),
    SelectionClient("not valid json"), SelectionClient("x" * 2001),
    SelectionClient({"family_id": "acs", "variant_id": "missing"}, status="incomplete"),
    SelectionClient({}, refusal=True), SelectionClient(failure=RuntimeError("provider credential secret")),
])
def test_invalid_or_failed_ai_selection_falls_back_to_same_coherent_seed(client):
    fallback = generate_cognitive_encounter("R2-02", base_state(), seed=11)
    result = generate_cognitive_encounter("R2-02", base_state(), seed=11, client=client)
    assert result["source"] == "fallback"
    assert result["warning"]
    assert result["spec"]["clinical_case"] == fallback["spec"]["clinical_case"]
    assert result["state"]["observable"] == fallback["state"]["observable"]
    assert result["spec"]["provenance"]["fallback_reason"] == "provider_or_selection_unavailable"
    assert "credential secret" not in json.dumps(result)


def test_valid_but_cross_family_variant_pair_cannot_override_challenge_scope():
    from clinical_cases import FAMILIES
    families = BIAS_CHALLENGES["R1-05"]["families"]
    client = SelectionClient({"family_id": families[0], "variant_id": FAMILIES[families[1]]["variants"][0]["id"]})
    result = generate_cognitive_encounter("R1-05", base_state(), seed=13, client=client)
    assert result["source"] == "fallback"


def test_availability_prime_is_only_context_and_does_not_mutate_patient():
    family_id = "pneumonia"
    first = generate_cognitive_encounter("R1-05", base_state(), seed=3, family_id=family_id)
    primed = generate_cognitive_encounter("R2-03", base_state(), seed=3, family_id=family_id)
    assert first["spec"]["clinical_case"] == primed["spec"]["clinical_case"]
    assert first["state"]["observable"] == primed["state"]["observable"]
    assert primed["presentation"].startswith(BIAS_CONTEXTS["availability"]["prime_text"])
    assert "bias" not in primed["presentation"].lower()


@pytest.mark.parametrize("kwargs", [
    {"challenge_id": "PS001"}, {"challenge_id": "unknown"},
    {"seed": -1}, {"seed": 2**31}, {"seed": True}, {"seed": 1.2},
    {"family_id": "opioid"}, {"variant_id": "unknown"},
])
def test_invalid_explicit_selection_is_not_silently_replaced(kwargs):
    args = {"challenge_id": "R1-05", "seed": 1, **kwargs}
    with pytest.raises(ValueError):
        generate_cognitive_encounter(base_state=base_state(), **args)


def test_active_encounter_cannot_be_regenerated_in_place():
    base = base_state()
    base["sim_time"] = 5
    with pytest.raises(ValueError):
        generate_cognitive_encounter("R1-05", base, seed=1)
