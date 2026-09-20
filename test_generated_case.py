"""Novel authoring, independent review, hard coherence gates, and frozen replay."""
from copy import deepcopy
from clinical_core_defaults import PHENOTYPE_FIELDS, INITIAL_HIDDEN, CORE_VERSION
import json
from types import SimpleNamespace

import pytest

import generated_case
from generated_case import generate_ai_encounter, GeneratedCaseError, FOUNDATION_OBJECTIVES
from generated_case_schema import (CASE_SCHEMA, REVIEW_SCHEMA, SCHEMA_VERSION, compile_case,
                                   validate_schema, STATE_TEXT)
from cognitive_catalog import BIAS_CHALLENGES
from encounter_generator import generate_encounter


def novel_payload(*, diagnosis="Acute adrenal crisis following glucocorticoid withdrawal", age=42, sex="female"):
    """Mock author output, deliberately outside all eight old clinical families."""
    visual = {"expression": "uncomfortable", "skin_color": "mild pallor", "diaphoresis": "mild", "mottling": False}
    state_changes = lambda **kw: {key: kw.get(key) for key in STATE_TEXT}
    def rule(identifier, action, field, reference, delta, agent=None, route=None):
        return {"id": identifier, "action_type": action, "agent": agent, "route": route,
                "exposure_pool": None, "volume_basis": "circulating" if action == "fluid" else None, "diuresis_ml_min": None, "exposure_curve": None, "units": None, "device": None, "settings": None, "interpolate_settings": None, "washout_min": None, "state_gain": {"field":"fluid_delivered_ml", "points":[{"value":0,"factor":1},{"value":2000,"factor":.5}]} if action == "fluid" else None, "recovery_min": None, "mental_status_during": None, "mental_status_threshold": None, "rhythm_before": None, "recurrence": None, "rhythm_after": None, "dose_field": field, "reference_dose": reference,
                "onset_min": 0 if action == "fluid" else 10, "duration_min": 10 if action == "fluid" else 30,
                "max_exposure": 2, "delta": [{"field": key, "value": value} for key, value in delta.items()],
                "explanation": "A bounded illustrative response to documented exposure, requiring expert validation."}
    def study(identifier, values, bindings=None, duration=2):
        return {"id": identifier, "duration_min": duration,
                "result": [{"field": key, "value": value} for key, value in values.items()],
                "result_bindings": [{"field": key, "observable_field": value} for key, value in (bindings or {}).items()]}
    o = {"sbp": 85, "dbp": 50, "hr": 125, "spo2": 97, "respiratory_rate": 24, "crt": 5,
         "temperature_c": 37.2, "glucose_mg_dl": 95, "rhythm": "sinus tachycardia", "pulse_present": True,
         "mental_status": "Alert", "work_of_breathing": "Mildly increased", "extremities": "Cool",
         "peripheral_perfusion": "impaired", "visual": visual}
    history = {"chief_complaint": ["I feel weak and dizzy when I sit up."],
               "onset": ["The weakness began yesterday and became much worse this morning."],
               "associated_symptoms": ["I have nausea and diffuse aching, without a focal pain."],
               "medical_history": ["I have an inflammatory joint disease treated with steroids."],
               "medications": ["I stopped my long-term prednisone suddenly five days ago when the prescription ran out."],
               "allergies": ["I have no known medication allergies."],
               "risk_factors": ["I have used daily prednisone for several years."],
               "chest_pain": ["I have no chest pain."], "breathing": ["I feel mildly breathless when I try to stand."],
               "bleeding": ["I have had no vomiting of blood or black stool."], "oral_intake": ["I have eaten and drunk little for a day."],
               "exposure": ["I have not taken a new medication or used recreational drugs."],
               "urinary_symptoms": ["I have no urinary burning or frequency."],
               "neurological_symptoms": ["I have no headache, focal weakness or seizure."], "leg_symptoms": ["My legs are not painful or swollen."]}
    return {"schema_version": SCHEMA_VERSION, "title": "Weakness and dizziness",
            "patient": {"age_years": age, "sex": sex, "pronouns": "she/her" if sex == "female" else "he/him",
                        "weight_kg": 72, "comorbidities": ["Inflammatory arthritis"]},
            "presentation": f"A {age}-year-old {'woman' if sex == 'female' else 'man'} arrives with weakness and dizziness. The patient looks uncomfortable and answers questions.",
            "history_source": "Patient", "history": history,
            "examination": [{"area": area, "finding": finding} for area, finding in {
                "Cardiac": "Rapid regular pulse; no murmur.", "Respiratory": "Equal bilateral air entry without crackles.",
                "Abdomen": "Mild diffuse discomfort; no guarding.", "Neurological": "Oriented, follows commands; no focal weakness.",
                "General appearance": "Uncomfortable with subtle pallor.", "Peripheral perfusion": "Cool hands, delayed refill."}.items()],
            "observable": o, "ecg_profile": "baseline",
            "investigations": [study("poc_glucose", {"glucose_mg_dl": 95}, {"glucose_mg_dl": "glucose_mg_dl"}),
                               study("temperature", {"temperature_c": 37.2}, {"temperature_c": "temperature_c"}),
                               study("basic_labs", {"sodium_mmol_l": 126, "potassium_mmol_l": 4.2, "hemoglobin_g_dl": 12.4, "glucose_mg_dl": 95},
                                     {"hemoglobin_g_dl": "hemoglobin_g_dl", "glucose_mg_dl": "glucose_mg_dl"}, 10),
                               study("pocus", {"lv": "Hyperdynamic contraction.", "lungs": "No diffuse B-lines.", "rv": "No enlargement.",
                                              "pericardium": "No pericardial effusion", "ivc": "1.1 cm; >50% inspiratory collapse",
                                              "lung_sliding": "Present bilaterally; no pneumothorax",
                                              "lung_consolidation": "No consolidation or pleural effusion",
                                              "aorta_root": "Not dilated", "aorta_descending": "Not dilated in the visible segment",
                                              "aorta_abdominal": "Normal calibre from the diaphragm to the iliac bifurcation",
                                              "dvt_femoral": "Compressible bilaterally", "dvt_popliteal": "Compressible bilaterally"}),
                               study("cortisol", {"cortisol_ug_dl": 1.2}, duration=60)],
            "engine": {"core_profile":{"version":CORE_VERSION,"infection_active":False,"initial_hidden":{k:INITIAL_HIDDEN[k] for k in PHENOTYPE_FIELDS}}, "nitrate_hazard": None, "coronary": None, "airway_obstruction": None, "volume_model": {"initial_extravascular_ml":0,"redistribution_half_life_min":28,"clearance_half_life_min":120,"extravascular_fraction":.5,"diuresis_extravascular_fraction":.7}, "terminal_rule":None, "model": CORE_VERSION, "horizon_min": 60, "stable_diagnostics": ["pocus"],
                       "initial_labs": {"hemoglobin_g_dl": 12.4, "lactate_mmol_l": 3, "pco2_mm_hg": 35,
                                        "bicarbonate_mmol_l": 22, "pao2_mm_hg": 92},
                       "untreated_drift_per_min": [{"field": "sbp", "value": -.12}, {"field": "dbp", "value": -.05}],
                       "response_rules": [rule("crystalloid_response", "fluid", "volume_ml", 500, {"sbp": 10, "dbp": 5, "crt": -1}),
                                          rule("steroid_response", "steroid", "dose_mg", 100, {"sbp": 12, "dbp": 5, "hr": -10, "crt": -1}, "hydrocortisone", "IV"),
                                          {**rule("extravascular", "fluid", "volume_ml", 500, {}), "volume_basis":"extravascular"}],
                       "state_rules": [{"id": "worsening_flow", "diagnostic_updates": None, "when": [{"field": "sbp", "operator": "lt", "value": 80}],
                                        "set": state_changes(mental_status="Drowsy", peripheral_perfusion="severely impaired",
                                                             visual={**visual, "expression": "markedly uncomfortable", "skin_color": "pallor"}),
                                        "examination": [{"area": "Neurological", "finding": "Opens eyes to voice and follows simple commands slowly."}]},
                                       {"id": "improved_flow", "diagnostic_updates": None, "when": [{"field": "sbp", "operator": "gte", "value": 100}, {"field": "crt", "operator": "lte", "value": 3}],
                                        "set": state_changes(mental_status="Alert", peripheral_perfusion="mildly impaired", extremities="Warm",
                                                             visual={**visual, "skin_color": "natural"}), "examination": None}]},
            "faculty": {"diagnosis": diagnosis, "management_focus": "Treat hypoperfusion while revisiting its cause.",
                        "management_dilemma": "An early volume-based explanation may not account for the full response or steroid history.",
                        "challenge_alignment": "The patient offers a plausible initial model requiring active reassessment.",
                        "discriminating_findings": ["Recent withdrawal of chronic glucocorticoids.", "Hypoperfusion despite relatively preserved oxygenation."],
                        "review_questions": ["What remained unexplained after support?", "How did the response change your model?"],
                        "anticipated_management_paths": ["Give initial circulatory support while obtaining the medication history.", "Start glucocorticoid replacement with concurrent circulatory support once the history is obtained."],
                        "limitations": ["Illustrative short-term trajectories require expert clinical review."]}}


def approval():
    return {"coherent": True, "checks": {key: True for key in REVIEW_SCHEMA["properties"]["checks"]["properties"]}, "issues": []}


class AuthorClient:
    def __init__(self, payload=None, review=None, *, failure=None, status="completed", refusal=False):
        self.payload = novel_payload() if payload is None else payload
        self.review = approval() if review is None else review
        self.failure, self.status, self.refusal = failure, status, refusal
        self.responses = self
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure
        payload = self.review if kwargs["text"]["format"]["name"] == "clinical_consistency_review" else self.payload
        return SimpleNamespace(status=self.status, output_text=payload if isinstance(payload, str) else json.dumps(payload),
                               output=[SimpleNamespace(content=[SimpleNamespace(type="refusal")])] if self.refusal else [],
                               usage=SimpleNamespace(input_tokens=50, output_tokens=500, total_tokens=550))


def clean_base():
    return {"case_id": "PS001", "sim_time": 0, "observable": {"rhythm": "AF"},
            "hidden": {"infection": 1, "legacy": "urinary"}, "treatments": {"norepinephrine": True, "administered_medications": ["old"]},
            "diagnostics": {"urinalysis": "old"}}


def test_ai_authors_new_complete_case_not_in_bank_and_independent_review_is_mandatory():
    client = AuthorClient()
    base = clean_base()
    untouched = deepcopy(base)
    result = generate_encounter("R1-05", base, client=client, seed=6)
    assert base == untouched
    assert len(client.calls) == 2
    assert result["spec"]["clinical_case"]["faculty"]["diagnosis"].startswith("Acute adrenal crisis")
    assert result["state"]["engine_family"] == "generated"
    assert result["state"]["encounter_facts"]["age_years"] == 42
    assert result["state"]["observable"]["rhythm"] != "AF"
    assert not result["state"]["diagnostics"]
    assert not result["state"]["treatments"]["norepinephrine"]
    assert result["spec"]["provenance"]["authoring"] == "novel_structured_case"
    assert "requires_expert_validation" in result["spec"]["provenance"]["clinical_validation"]
    payload = json.loads(client.calls[0]["input"])
    assert "choices" not in payload and "profiles" not in payload
    assert "variant_id" not in client.calls[0]["input"]
    assert "case" in json.loads(client.calls[1]["input"])
    assert all(call["store"] is False and call["text"]["format"]["strict"] for call in client.calls)
    assert "adrenal" not in result["presentation"].lower()
    assert "anchoring" not in result["presentation"].lower()


@pytest.mark.parametrize("challenge", list(BIAS_CHALLENGES) + list(FOUNDATION_OBJECTIVES))
def test_all_selected_challenges_route_to_new_authoring(challenge):
    client = AuthorClient()
    result = generate_encounter(challenge, clean_base(), client=client, seed=9)
    assert result["spec"]["challenge_id"] == challenge
    assert len(client.calls) == 2
    assert result["spec"]["case_family"] == "generated"


def test_authored_new_demographics_diagnosis_and_sources_are_preserved_without_bank_constraints():
    client = AuthorClient(novel_payload(diagnosis="Novel fictional endocrine scenario", age=57, sex="male"))
    result = generate_ai_encounter("R2-02", clean_base(), client=client)
    case = result["spec"]["clinical_case"]
    assert case["faculty"]["diagnosis"] == "Novel fictional endocrine scenario"
    assert case["patient"]["age_years"] == 57
    assert case["history"]["medications"][0].startswith("I stopped")
    assert case["investigations"]["cortisol"]["result"]["cortisol_ug_dl"] == 1.2
    assert case["faculty"]["sources"] == []


@pytest.mark.parametrize("client", [AuthorClient(failure=RuntimeError("provider secret key")),
                                    AuthorClient(status="incomplete"), AuthorClient(refusal=True),
                                    AuthorClient(payload="invalid json"), AuthorClient(payload={"family_id": "acs", "variant_id": "acs_54m"})])
def test_author_failure_does_not_launch_silent_fixed_case_or_expose_provider_errors(client):
    base = clean_base()
    frozen = deepcopy(base)
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", base, client=client)
    assert "secret" not in str(exc.value)
    assert "again" in str(exc.value)
    assert base == frozen
    assert len(client.calls) == 1


def test_missing_key_is_actionable_and_never_substitutes_case():
    with pytest.raises(GeneratedCaseError, match="OPENAI_API_KEY"):
        generate_encounter("R1-05", clean_base(), seed=1)


@pytest.mark.parametrize("review", [{"coherent": False, "checks": approval()["checks"], "issues": ["Contradictory clinical facts"]},
                                    {**approval(), "checks": {**approval()["checks"], "visual_consistency": False}},
                                    {**approval(), "issues": ["A mismatch remains"]}])
def test_independent_review_rejection_blocks_launch(review):
    client = AuthorClient(review=review)
    with pytest.raises(GeneratedCaseError, match="consistency screen"):
        generate_encounter("R1-05", clean_base(), client=client)
    # One review round: the rejection is reported, not repaired and re-reviewed.
    assert len(client.calls) == 2


@pytest.mark.parametrize("mutate", [
    lambda case: case["observable"].update(sbp=40, dbp=50),
    lambda case: case["patient"].update(pronouns="he/him"),
    lambda case: case["observable"].update(mental_status="Unresponsive"),
    lambda case: case["investigations"][0]["result"][0].update(value=250),
    lambda case: case["engine"]["response_rules"][0].update(reference_dose=0),
    lambda case: case["engine"]["response_rules"][0]["delta"].append({"field": "learner_score", "value": -5}),
    lambda case: case["engine"]["response_rules"][1].update(agent=None),
    lambda case: case.update(ecg_profile="hyperkalemia"),
])
def test_hard_structure_gates_reject_even_before_reviewer_can_approve(mutate):
    raw = novel_payload()
    mutate(raw)
    client = AuthorClient(raw)
    with pytest.raises(GeneratedCaseError):
        generate_ai_encounter("R1-05", clean_base(), client=client)
    assert 1 <= len(client.calls) <= 2
    assert all(call["text"]["format"]["name"] == "new_clinical_case" for call in client.calls)


def test_frozen_case_hash_and_deep_copies_support_replay_without_provider():
    result = generate_ai_encounter("R1-05", clean_base(), seed=5, client=AuthorClient())
    import hashlib
    spec = deepcopy(result["spec"])
    digest = spec.pop("content_sha256")
    assert digest == hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    result["state"]["observable"]["sbp"] = 120
    result["state"]["encounter_spec"]["clinical_case"]["history"]["medications"].append("changed")
    assert result["spec"]["initial_observable"]["sbp"] == 85
    assert "changed" not in result["spec"]["clinical_case"]["history"]["medications"]


def test_generated_case_runs_existing_family_entrypoints_and_new_diagnostic_parser():
    from family_engine import execute_family_bundle, current_findings, clinical_update
    from family_parser import parse_family_actions
    state = generate_ai_encounter("R1-05", clean_base(), client=AuthorClient())["state"]
    result = execute_family_bundle(state, {"actions": [{"type": "fluid", "volume_ml": 500, "fluid_type": "normal saline"}]})
    assert result["executed"]
    # Ordering is not administering: the bolus runs on the simulation clock, so
    # nothing is delivered and no pressure has changed before time advances.
    assert state["observable"]["sbp"] == 85
    assert state["family_state"]["fluid_delivered_ml"] == 0
    assert state["family_state"]["pending_fluid_ml"] == 500
    execute_family_bundle(state, {"actions": [{"type": "reassessment", "delay_min": 10}]})
    assert state["family_state"]["fluid_delivered_ml"] == 500
    assert state["treatments"]["cumulative_crystalloid_ml"] == 500
    assert state["observable"]["sbp"] > 85
    assert "Cardiac" in current_findings(state)
    assert "BP" in clinical_update(state)
    parsed = parse_family_actions("Order cortisol")
    assert any(action.get("diagnostic") == "cortisol" for action in parsed["actions"])


def test_diagnostic_binding_cannot_disguise_an_unrelated_measurement():
    raw = novel_payload()
    raw['investigations'][0]['result_bindings'][0]['observable_field'] = 'sbp'
    raw['investigations'][0]['result'][0]['value'] = raw['observable']['sbp']
    with pytest.raises(ValueError, match='different measurement'):
        compile_case(raw)


def test_mental_status_change_cannot_leave_contradictory_baseline_neurological_exam():
    raw = novel_payload()
    raw['engine']['state_rules'][0]['examination'] = None
    with pytest.raises(ValueError, match='neurological examination'):
        compile_case(raw)


def test_duplicate_model_json_fields_cannot_override_a_previous_value():
    raw = json.dumps(novel_payload())
    raw = raw.replace('"age_years": 42', '"age_years": 70, "age_years": 42')
    client = AuthorClient(raw)
    with pytest.raises(GeneratedCaseError):
        generate_ai_encounter('R1-05', clean_base(), client=client)
    assert len(client.calls) == 1


def test_new_case_cannot_inherit_an_existing_native_patient():
    prior=generate_ai_encounter('R1-05',clean_base(),seed=1,client=AuthorClient())['state']
    prior['coupled_state']['hidden']['terminal_collapse']=True
    prior['coupled_state']['treatments']['norepinephrine']=True
    prior['pending_investigations']=[{'diagnostic_type':'old'}]
    prior['rhythm_history']=[{'kind':'old'}]
    before=deepcopy(prior)
    new=generate_ai_encounter('R1-05',prior,seed=2,client=AuthorClient())['state']
    assert prior==before
    assert not new['coupled_state']['hidden'].get('terminal_collapse')
    assert not new['coupled_state']['treatments']['norepinephrine']
    assert new['coupled_state']['seed']==2
    assert new['pending_investigations']==[]
    assert new['rhythm_history']==[]


def test_a_single_rejection_is_terminal_under_the_production_review_budget():
    """The cut to one review round: a rejected case is reported, not repaired.

    This is a real capability loss, taken deliberately. The former second round
    spent a repair and a re-review that the 300 s budget could not finish.
    """
    assert generated_case.REVIEW_ROUNDS == 1
    review = approval()
    review['coherent'] = False
    review['checks']['state_transitions'] = False
    client = AuthorClient(review=review)
    with pytest.raises(GeneratedCaseError, match='consistency screen'):
        generate_ai_encounter('R1-05', clean_base(), client=client, seed=42)
    assert [c['text']['format']['name'] for c in client.calls] == [
        'new_clinical_case', 'clinical_consistency_review']


def test_review_repair_reuses_draft_and_real_objections_before_launch(monkeypatch):
    # Exercised with the repair enabled, so raising REVIEW_ROUNDS stays a
    # one-line change rather than the discovery that the branch rotted.
    monkeypatch.setattr(generated_case, 'REVIEW_ROUNDS', 2)
    class Client(AuthorClient):
        def create(self, **kwargs):
            if kwargs['text']['format']['name']=='clinical_consistency_review':
                count=sum(c['text']['format']['name']=='clinical_consistency_review' for c in self.calls)
                self.review=approval()
                if count==0:
                    self.review['coherent']=False
                    self.review['checks']['state_transitions']=False
                    self.review['issues']=['Baseline blood pressure contradicts native trajectory.']
            return super().create(**kwargs)
    client=Client();scenes=[]
    result=generate_ai_encounter('R1-05',clean_base(),client=client,seed=42,on_case_compiled=lambda *x:scenes.append(len(client.calls)))
    assert len(client.calls)==4 and scenes==[4]
    repair=json.loads(client.calls[2]['input'])
    assert repair['proposed_case']==client.payload
    assert repair['clinical_review']['checks']['state_transitions'] is False
    assert repair['shared_engine_preview']
    assert result['spec']['provenance']['correction_count']==1
    assert result['state']['coupled_state']


def test_persistent_review_failure_retains_private_diagnostic_and_safe_check_names():
    review=approval();review['checks']['state_transitions']=False
    review['issues']=['PRIVATE clinical diagnosis detail']
    with pytest.raises(GeneratedCaseError) as caught:
        generate_ai_encounter('R1-05',clean_base(),client=AuthorClient(review=review),seed=42)
    assert 'state_transitions' in str(caught.value)
    assert 'PRIVATE' not in str(caught.value)
    assert caught.value.diagnostic['review']['issues']==review['issues']
    assert caught.value.diagnostic['draft']
