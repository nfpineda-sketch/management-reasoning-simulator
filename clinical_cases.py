"""Authored clinical constraints for the cognitive-challenge encounter generator.

These are fictional teaching cases, not records of real patients or a validated
physiology model. AI may select and narrate a case within these constraints; it
must not invent a different diagnosis, contradictory examination, or treatment
response. Faculty-only fields must never be included in the live handover.

References inform the clinical problem and management priorities. Patient details,
numerical observations, test values, delays and review questions are authored for
simulation and are not quoted observations or guideline-prescribed trajectories.
"""
from copy import deepcopy

from visual_observations import distributive_visual_profile, hypoperfusion_visual_profile


CASE_BANK_VERSION = "1.0.0"
SOURCE_URLS = {
    "pneumonia": "https://www.idsociety.org/practice-guideline/community-acquired-pneumonia-cap-in-adults",
    "pulmonary_edema": "https://doi.org/10.1093/eurheartj/ehab368",
    "acs": "https://www.escardio.org/guidelines/clinical-practice-guidelines/all-esc-practice-guidelines/acute-coronary-syndromes/",
    "pulmonary_embolism": "https://www.escardio.org/guidelines/clinical-practice-guidelines/all-esc-practice-guidelines/acute-pulmonary-embolism/",
    "asthma": "https://ginasthma.org/wp-content/uploads/2026/07/GINA-Summary-Guide-2026-WEB-WMS.pdf",
    "gi_bleed": "https://pubmed.ncbi.nlm.nih.gov/33929377/",
    "hypoglycemia": "https://abcd.care/sites/default/files/site_uploads/JBDS_Guidelines_Current/JBDS_01_Hypo_Guideline_with_QR_code_January_2023.pdf",
    "opioid": "https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-and-pediatric-special-circumstances-of-resuscitation",
    "anaphylaxis": "https://www.worldallergy.org/wao-journal/anaphylaxis-guidance-2020",
    "renal_colic": "https://uroweb.org/guidelines/urolithiasis",
    "bradycardia": "https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-and-advanced-life-support",
}
INVESTIGATION_IDS = (
    "pocus", "lactate", "vbg", "abg", "basic_labs", "temperature",
    "poc_glucose", "chest_xray", "urinalysis", "blood_cultures",
    "troponin", "ctpa", "hemoglobin",
    # The first test of the embolism algorithm (faculty decision, 2026-09-22).
    "d_dimer",
    # The additional leads of a coronary case (faculty decision 7, 2026-09-21).
    "ecg_right", "ecg_posterior",
    # The study of the flank-pain family (2026-09-23). It is a formal renal
    # ultrasound and not part of the emergency POCUS protocol, which is why it
    # is its own investigation the way the angiogram is for the embolism family.
    "renal_ultrasound",
)


# ---------------------------------------------------------------------------
# POCUS findings -- DRAFT PENDING FACULTY REVIEW
#
# Every case reports every structure of the faculty's emergency POCUS protocol,
# normal findings included, in the order pocus_report.SECTIONS renders them.
# Findings, not interpretation: nothing here says "preload responsive" or
# "tamponade". The LV is qualitative; the IVC keeps diameter and collapse.
#
# These were drafted to be consistent with each case's diagnosis, vital signs,
# history and examination. They have not been clinically reviewed. See
# docs/POCUS_DRAFT_FINDINGS.md, which lists what to check.
# ---------------------------------------------------------------------------
POCUS_DRAFT_PENDING_FACULTY_REVIEW = True

_RV_NORMAL = "Smaller than the LV; no septal flattening (no D-sign); no McConnell sign"
_PERICARDIUM_NORMAL = "No pericardial effusion"
_SLIDING_NORMAL = "Present bilaterally; no pneumothorax"
_B_LINES_NONE = "No B-lines; A-line pattern bilaterally"
_CONSOLIDATION_NONE = "No consolidation or pleural effusion"
_AORTA_NORMAL = {
    "aorta_root": "Not dilated",
    "aorta_descending": "Not dilated in the visible segment",
    "aorta_abdominal": "Normal calibre from the diaphragm to the iliac bifurcation",
}
_VEINS_COMPRESSIBLE = {
    "dvt_femoral": "Compressible bilaterally",
    "dvt_popliteal": "Compressible bilaterally",
}


def _pocus(*, lv, ivc, rv=_RV_NORMAL, pericardium=_PERICARDIUM_NORMAL,
           lung_sliding=_SLIDING_NORMAL, lungs=_B_LINES_NONE,
           lung_consolidation=_CONSOLIDATION_NONE, aorta=None, veins=None):
    return {"lv": lv, "rv": rv, "pericardium": pericardium, "ivc": ivc,
            "lung_sliding": lung_sliding, "lungs": lungs,
            "lung_consolidation": lung_consolidation,
            **(aorta or _AORTA_NORMAL), **(veins or _VEINS_COMPRESSIBLE)}


POCUS = {
    "pneumonia": (
        _pocus(lv="Preserved, vigorous contraction",
               ivc="1.0 cm; >50% inspiratory collapse",
               lungs="Focal B-lines at the right base; no diffuse bilateral B-lines",
               lung_consolidation="Right basal subpleural consolidation with dynamic air bronchograms; no pleural effusion"),
        _pocus(lv="Preserved contraction",
               ivc="1.2 cm; >50% inspiratory collapse",
               lungs="Focal B-lines at the left base; no diffuse bilateral B-lines",
               lung_consolidation="Left basal consolidation with air bronchograms; no pleural effusion"),
    ),
    "pulmonary_edema": (
        _pocus(lv="Moderately reduced global contraction",
               ivc="2.4 cm; <50% inspiratory collapse",
               lungs="Diffuse bilateral B-lines in the anterior and lateral zones"),
        _pocus(lv="Severely reduced global contraction",
               ivc="2.5 cm; minimal inspiratory collapse",
               lungs="Diffuse bilateral B-lines in the anterior and lateral zones",
               lung_consolidation="No consolidation; small bilateral pleural effusions"),
    ),
    "acs": (
        _pocus(lv="Reduced contraction of the inferior wall; the other walls contract normally",
               rv="Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign",
               ivc="1.8 cm; about 50% inspiratory collapse"),
        _pocus(lv="Mild hypokinesis of the inferolateral wall; global contraction otherwise preserved",
               ivc="1.7 cm; about 50% inspiratory collapse"),
        # Posterior occlusion: the wall the standard 12-lead sees only as a mirror image.
        _pocus(lv="Hypokinesis of the posterior wall; the anterior and lateral walls contract normally",
               ivc="1.6 cm; about 50% inspiratory collapse"),
        # de Winter: a proximal anterior occlusion, with the apex already failing.
        _pocus(lv="Akinesis of the anterior wall and apex; the inferior wall contracts normally",
               ivc="1.5 cm; about 50% inspiratory collapse"),
        # Wellens: the artery is open at this moment, so the wall still moves.
        _pocus(lv="Normal wall motion in every segment at rest",
               ivc="1.5 cm; >50% inspiratory collapse"),
        # Diffuse subendocardial ischaemia of a left main or three-vessel lesion.
        _pocus(lv="Globally reduced contraction without a single focal defect",
               ivc="1.9 cm; about 50% inspiratory collapse"),
    ),
    "pulmonary_embolism": (
        _pocus(lv="Preserved contraction",
               rv="Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign",
               ivc="2.0 cm; <50% inspiratory collapse",
               veins={"dvt_femoral": "Compressible bilaterally",
                      "dvt_popliteal": "Non-compressible on the operated (symptomatic) side, with echogenic intraluminal material; compressible on the other side"}),
        _pocus(lv="Small, underfilled cavity with vigorous contraction",
               rv="Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing (McConnell sign)",
               ivc="2.3 cm; minimal inspiratory collapse",
               veins={"dvt_femoral": "Compressible bilaterally",
                      "dvt_popliteal": "Left popliteal vein non-compressible; right popliteal vein compressible"}),
    ),
    "asthma": (
        _pocus(lv="Preserved contraction", ivc="1.4 cm; >50% inspiratory collapse"),
        _pocus(lv="Preserved contraction", ivc="1.6 cm; >50% inspiratory collapse"),
    ),
    "gi_bleed": (
        _pocus(lv="Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole",
               ivc="0.9 cm; near-complete inspiratory collapse"),
        _pocus(lv="Hyperdynamic contraction", ivc="1.1 cm; >50% inspiratory collapse"),
    ),
    "hypoglycemia": (
        _pocus(lv="Preserved, mildly hyperdynamic contraction",
               ivc="1.1 cm; >50% inspiratory collapse"),
        _pocus(lv="Preserved contraction", ivc="1.7 cm; about 50% inspiratory collapse"),
        _pocus(lv="Preserved contraction", ivc="1.8 cm; about 50% inspiratory collapse"),
    ),
    "opioid": (
        _pocus(lv="Preserved contraction", ivc="1.8 cm; minimal respiratory variation with shallow breaths"),
        _pocus(lv="Preserved contraction", ivc="1.9 cm; minimal respiratory variation with shallow breaths"),
    ),
    "renal_colic": (
        _pocus(lv="Preserved, vigorous contraction", ivc="1.4 cm; >50% inspiratory collapse"),
        _pocus(lv="Preserved, vigorous contraction", ivc="1.0 cm; >50% inspiratory collapse"),
    ),
    # The study does not name the poison either. A slow, poorly contracting
    # ventricle looks the same whatever stopped it.
    "bradycardia": (
        _pocus(lv="Globally reduced contraction at a slow rate; no regional difference identified",
               ivc="1.9 cm; <50% inspiratory collapse"),
        _pocus(lv="Preserved contraction at a slow, regular ventricular rate independent of the atria",
               ivc="1.7 cm; <50% inspiratory collapse"),
    ),
    # Distributive shock: the ventricle is full and fast and the vein is empty,
    # which is what separates it on the screen from the congested ones. The
    # study does not say "anaphylaxis" and nothing here interprets it.
    "anaphylaxis": (
        _pocus(lv="Vigorous, hyperdynamic contraction with near-obliteration in systole",
               ivc="0.9 cm; >50% inspiratory collapse"),
        _pocus(lv="Preserved contraction without the hyperdynamic pattern",
               ivc="1.1 cm; >50% inspiratory collapse"),
    ),
}


def _observable(sbp, dbp, hr, spo2, rr, *, wob="Normal", crt=2,
                extremities="Warm", mental="Alert", temperature=36.8,
                glucose=110, perfusion="preserved", pain_score=None):
    # A case whose presentation says the patient is comfortable has to say so
    # here too. Without it the family default applies, and the Wellens patient
    # who "feels fine" was reported in severe pain (played 2026-09-22).
    return {
        "sbp": sbp, "dbp": dbp, "hr": hr, "spo2": spo2,
        "respiratory_rate": rr, "work_of_breathing": wob,
        "crt": crt, "extremities": extremities, "mental_status": mental,
        "rhythm": ("Sinus tachycardia" if hr > 100 else
                   "Sinus bradycardia" if hr < 60 else "Sinus rhythm"),
        "pulse_present": True, "temperature_c": temperature,
        "glucose_mg_dl": glucose, "peripheral_perfusion": perfusion,
        **({} if pain_score is None else {"pain_score": float(pain_score)}),
    }


def _visual(*, shock=False, distributive=False, expression="uncomfortable",
            skin="natural", sweating="absent"):
    if shock or distributive:
        profile = (distributive_visual_profile() if distributive
                   else hypoperfusion_visual_profile())
        profile["baseline"]["diaphoresis"] = sweating
        return profile
    return {
        "id": "authored_case_appearance_v1",
        "baseline": {"expression": expression, "skin_color": skin,
                     "diaphoresis": sweating, "mottling": False},
        "perfusion_appearance": {},
    }


def _history(chief, symptoms, medical, medications, onset, risks, **focused):
    def sentences(value):
        return [value] if isinstance(value, str) else list(value)
    history = {
        "chief_complaint": sentences(chief),
        "associated_symptoms": sentences(symptoms),
        "medical_history": sentences(medical),
        "medications": sentences(medications),
        "allergies": ["No known medication allergies are reported."],
        "onset": sentences(onset), "risk_factors": sentences(risks),
    }
    history.update({key: sentences(value) for key, value in focused.items()})
    return history


def _gas(ph, co2, oxygen=None):
    result = {"ph": ph, "paco2_mm_hg" if oxygen is not None else "pco2_mm_hg": co2,
              "bicarbonate_mmol_l": round(.03 * co2 * 10 ** (ph - 6.1), 1)}
    if oxygen is not None:
        result.update({"pao2_mm_hg": oxygen, "fio2_percent": 21})
    return result


def _study(result, duration=5):
    return {"duration_min": duration,
            "result": {"report": result} if isinstance(result, str) else result}


AGE_ADJUSTED_D_DIMER_FROM = 50
D_DIMER_FIXED_LIMIT = 500


def age_adjusted_d_dimer_limit(age_years):
    """The upper reference of a D-dimer for this patient, in ng/mL FEU.

    Fixed at 500 up to fifty years and age x 10 above it. The adjustment exists
    because the fixed limit turns positive with age and loses the ability to
    exclude that the test is ordered for (faculty decision, 2026-09-22). The
    limit is derived from the case's own age, never written beside it, so the
    two cannot drift apart.
    """
    age = int(age_years)
    return D_DIMER_FIXED_LIMIT if age <= AGE_ADJUSTED_D_DIMER_FROM else age * 10


def _with_age_adjusted_d_dimer(investigations, age_years):
    study = investigations.get("d_dimer")
    if not study:
        return investigations
    limit = age_adjusted_d_dimer_limit(age_years)
    value = study["result"]["d_dimer_ng_ml_feu"]
    study["result"]["upper_reference_ng_ml_feu"] = limit
    study["result"]["report"] = (
        f"Age-adjusted upper reference: {D_DIMER_FIXED_LIMIT} ng/mL FEU up to "
        f"{AGE_ADJUSTED_D_DIMER_FROM} years, age x 10 above it. "
        + ("Above the limit: this does not establish a diagnosis and does not exclude one."
           if value > limit else
           "At or below the limit for this age.")
    )
    return investigations


def _investigations(o, *, lactate, hemoglobin, wbc, creatinine, abg, vbg,
                    pocus, chest_xray, troponin=8, sodium=138, potassium=4.1,
                    bun=18, ctpa=None, d_dimer=None, renal_ultrasound=None,
                    urinalysis=None):
    # An unauthored study is absent, never silently reported as a negative test.
    result = {
        "pocus": _study(pocus, 2),
        "lactate": _study({"lactate_mmol_l": lactate}),
        "abg": _study(_gas(*abg)), "vbg": _study(_gas(*vbg)),
        "basic_labs": _study({
            "hemoglobin_g_dl": hemoglobin, "wbc_k_ul": wbc,
            "sodium_mmol_l": sodium, "potassium_mmol_l": potassium,
            "creatinine_mg_dl": creatinine, "bun_mg_dl": bun,
            "glucose_mg_dl": o["glucose_mg_dl"],
        }, 10),
        "temperature": _study({"temperature_c": o["temperature_c"]}, 1),
        "poc_glucose": _study({"glucose_mg_dl": o["glucose_mg_dl"]}, 1),
        "chest_xray": _study(chest_xray, 8),
        "hemoglobin": _study({"hemoglobin_g_dl": hemoglobin}, 5),
        "troponin": _study({"value_ng_l": troponin,
                              "upper_reference_ng_l": 19,
                              "report": "Single sample; interpret with symptoms and ECG. Serial testing requires a new sample."}, 10),
        "urinalysis": _study(
            urinalysis or "No leukocyte esterase, nitrite or blood detected.", 8),
        "blood_cultures": _study("Samples collected; culture identification and susceptibility results are pending.", 2),
    }
    if renal_ultrasound is not None:
        result["renal_ultrasound"] = _study(renal_ultrasound, 15)
    if ctpa is not None:
        result["ctpa"] = _study(ctpa, 20)
    if d_dimer is not None:
        # The upper reference is filled in from the case's age by _case.
        result["d_dimer"] = _study({"d_dimer_ng_ml_feu": d_dimer}, 10)
    return result


def _with_additional_leads(investigations, coronary):
    """A coronary case can record right-sided and posterior leads; others cannot.

    Faculty decision 7 of 2026-09-21. Where the data does not exist the study
    stays absent, and the encounter says it is not available, rather than
    handing back a standard twelve-lead in its place.
    """
    if coronary is None:
        return investigations
    result = dict(investigations)
    result["ecg_right"] = _study({"report": "Right-sided leads."}, 2)
    result["ecg_posterior"] = _study({"report": "Posterior leads."}, 2)
    return result


def _case(identifier, family, age, sex, comorbidities, presentation, history,
          examination, observable, investigations, diagnosis, findings, focus,
          questions, actions, *, ecg="baseline", visual=None, recurrence=False,
          history_source="Patient", congestion=None, coronary=None, lysis_bleeding_risk=None,
          thiamine_deficient=False, endogenous_insulin=False, opioid_depot=0.0,
          iv_access_failed=False, glycogen_depleted=False, anaphylaxis=None, renal=None,
          bradycardia=None):
    return {
        "id": identifier,
        "patient": {"age_years": age, "sex": sex,
                    "pronouns": "she/her" if sex == "female" else "he/him",
                    "comorbidities": list(comorbidities)},
        "presentation": presentation, "history": history, "history_source": history_source,
        "examination": examination, "observable": observable,
        "ecg_profile": ecg, "investigations": _with_age_adjusted_d_dimer(
            _with_additional_leads(investigations, coronary), age),
        "visual_profile": visual or _visual(),
        "engine": {
            "family": family, "definitive_actions": list(actions),
            "baseline_glucose": observable["glucose_mg_dl"],
            "baseline_hemoglobin": investigations["hemoglobin"]["result"]["hemoglobin_g_dl"],
            "baseline_lactate": investigations["lactate"]["result"]["lactate_mmol_l"],
            "recurrence_risk": recurrence,
            **({"opioid_depot": opioid_depot} if opioid_depot else {}),
            **({"congestion": dict(congestion)} if congestion else {}),
            **({"coronary": dict(coronary)} if coronary else {}),
            **({"lysis_bleeding_risk": lysis_bleeding_risk} if lysis_bleeding_risk else {}),
            **({"thiamine_deficient": True} if thiamine_deficient else {}),
            **({"iv_access_failed": True} if iv_access_failed else {}),
            **({"glycogen_depleted": True} if glycogen_depleted else {}),
            **({"endogenous_insulin": True} if endogenous_insulin else {}),
            **({"anaphylaxis": dict(anaphylaxis)} if anaphylaxis else {}),
            **({"renal": dict(renal)} if renal else {}),
            **({"bradycardia": dict(bradycardia)} if bradycardia else {}),
        },
        "faculty": {"diagnosis": diagnosis, "discriminating_findings": list(findings),
                    "management_focus": focus, "review_questions": list(questions),
                    "sources": [SOURCE_URLS[family]]},
    }


FAMILIES = {
    "pneumonia": {"label": "Infection with respiratory compromise", "variants": []},
    "pulmonary_edema": {"label": "Acute respiratory distress with congestion", "variants": []},
    "acs": {"label": "Acute chest or upper-abdominal discomfort", "variants": []},
    "pulmonary_embolism": {"label": "Acute dyspnea or presyncope", "variants": []},
    "asthma": {"label": "Worsening breathlessness with airflow limitation", "variants": []},
    "gi_bleed": {"label": "Weakness or syncope with blood loss", "variants": []},
    "hypoglycemia": {"label": "Acute altered behavior or consciousness", "variants": []},
    "opioid": {"label": "Reduced consciousness with slow breathing", "variants": []},
    # The label says what arrives, not what it is: a resident who reads
    # "anaphylaxis" on the door has been given the diagnosis.
    "anaphylaxis": {"label": "Acute rash, swelling or breathlessness after an exposure", "variants": []},
    # The two variants arrive with the same complaint and the same ultrasound.
    # What separates them is everything else, and the label says neither.
    "renal_colic": {"label": "Acute flank pain", "variants": []},
    # The monitor says the rate. It does not say what took it, and that is the
    # whole of this family.
    "bradycardia": {"label": "Slow heart rate with poor perfusion", "variants": []},
}


# PNEUMONIA: different presentations and demographics, with respiratory findings
# that remain true even when the arrival story initially emphasizes something else.
_o = _observable(92, 58, 118, 89, 30, wob="Increased", crt=4,
                 extremities="Cool", temperature=39.1, glucose=152, perfusion="impaired")
FAMILIES["pneumonia"]["variants"].append(_case(
    "pneumonia_46f", "pneumonia", 46, "female", ["rheumatoid arthritis"],
    "A 46-year-old woman presents with breathlessness and worsening weakness. She is awake and pauses between sentences.",
    _history("I feel short of breath and too weak to stand for long.",
        ["I have had a cough with yellow sputum and shaking chills.", "It hurts on the right when I take a deep breath."],
        "I have rheumatoid arthritis; I have not previously needed oxygen.",
        "I take methotrexate weekly and folic acid; no antibiotic has been started.",
        "The cough began three days ago; the breathing and weakness worsened today.",
        "I receive methotrexate and have eaten and drunk little since yesterday.",
        chest_pain="The right-sided pain occurs with coughing or deep inspiration, not as a central pressure.",
        breathing="The shortness of breath is now present while sitting still.",
        oral_intake="I have had very little to eat or drink since yesterday.",
        urinary_symptoms="I have no burning or frequency when passing urine.",
        bleeding="I have not coughed blood, vomited blood or passed black stools."),
    {"Cardiac": "Rapid regular pulse; no new murmur heard.",
     "Respiratory": "Increased respiratory effort; focal crackles and bronchial breathing at the right base.",
     "Abdomen": "Soft; no focal tenderness or guarding.",
     "Neurological": "Awake, oriented and moving all limbs symmetrically."}, _o,
    _investigations(_o, lactate=3.8, hemoglobin=12.2, wbc=19.4, creatinine=1.4,
        abg=(7.42, 31, 58), vbg=(7.38, 38),
        pocus=POCUS["pneumonia"][0],
        chest_xray="Right lower-lobe air-space opacity. No pulmonary edema or pneumothorax.", troponin=12),
    "Community-acquired pneumonia with hypoxemia and impaired perfusion",
    ["Focal pulmonary findings", "Fever and productive cough", "Hypoxemia and delayed capillary refill"],
    "Address oxygenation and perfusion while arranging antimicrobial treatment and reassessing response.",
    ["Which observations required action before diagnostic certainty?", "What changed after support, and what remained untreated?"],
    ["antibiotics", "oxygen", "fluid"], visual=_visual(shock=True)))

_o = _observable(96, 60, 108, 91, 28, wob="Increased", crt=4,
                 extremities="Cool", mental="Drowsy", temperature=37.8, glucose=126, perfusion="impaired")
FAMILIES["pneumonia"]["variants"].append(_case(
    "pneumonia_83m", "pneumonia", 83, "male", ["hypertension", "hearing impairment"],
    "An 83-year-old man is brought by his daughter after becoming unusually sleepy and nearly falling at home.",
    _history("His daughter reports that he has become sleepy and much less steady on his feet.",
        ["His daughter noticed a new cough and reduced appetite over two days.", "He has been breathing faster today."],
        "His daughter reports hypertension and hearing impairment; he normally walks independently and converses clearly.",
        "His daughter lists amlodipine as his only regular prescription.",
        "The cough began two days ago; sleepiness and near-fall occurred this morning.",
        "He is independently mobile at baseline and has had poor oral intake during this illness.",
        breathing="His daughter says the faster breathing began before the near-fall.",
        oral_intake="His daughter says he has taken only small sips and little food today.",
        exposure="There was no witnessed head strike, seizure or new sedative exposure.",
        urinary_symptoms="His daughter reports no preceding urinary complaints."),
    {"Cardiac": "Rapid regular pulse; no new murmur heard.",
     "Respiratory": "Tachypnea with focal crackles and reduced air entry at the left base.",
     "Abdomen": "Soft and non-tender; no suprapubic tenderness.",
     "Neurological": "Opens eyes to voice, follows simple commands slowly, and moves all limbs without an obvious focal deficit."}, _o,
    _investigations(_o, lactate=3.1, hemoglobin=13.1, wbc=15.6, creatinine=1.6,
        abg=(7.41, 33, 62), vbg=(7.37, 40),
        pocus=POCUS["pneumonia"][1],
        chest_xray="Left lower-lobe consolidation without diffuse edema.", troponin=17),
    "Pneumonia presenting with acute encephalopathy and impaired perfusion",
    ["New tachypnea and hypoxemia", "Focal consolidation", "New mental-status change from an independent baseline"],
    "Stabilize physiology and investigate the new altered state despite a nonspecific arrival complaint.",
    ["Did the initial story account for the respiratory findings?", "How did you check the response to treatment?"],
    ["antibiotics", "oxygen", "fluid"], visual=_visual(shock=True)))


# PULMONARY EDEMA: hypertensive redistribution versus established congestive HF.
_o = _observable(218, 116, 126, 81, 38, wob="Severe", temperature=36.6, glucose=148)
FAMILIES["pulmonary_edema"]["variants"].append(_case(
    "pulmonary_edema_58m", "pulmonary_edema", 58, "male", ["hypertension"],
    "A 58-year-old man arrives with rapidly worsening breathlessness. He remains upright and can speak only a few words at a time.",
    _history("I suddenly cannot catch my breath, especially if I lie back.",
        ["I woke up gasping and have been coughing up a small amount of frothy sputum.", "I have not had fever or a preceding productive cough."],
        "I have high blood pressure; I have never been told I have asthma.",
        "I ran out of my usual antihypertensive medication four days ago.",
        "Severe breathlessness began about an hour ago and worsened rapidly.",
        "My blood pressure has been high and I have missed several days of treatment.",
        breathing="Lying flat makes my breathing markedly worse.",
        chest_pain="I feel chest tightness with the effort of breathing, without a separate persistent crushing pain.",
        oral_intake="I have eaten and drunk normally.",
        urinary_symptoms="I have no urinary burning or frequency."),
    {"Cardiac": "Rapid regular pulse; elevated jugular venous pressure.",
     "Respiratory": "Severe respiratory effort with widespread bilateral crackles and some expiratory wheeze.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Awake, oriented and distressed; answers are brief because of breathlessness."}, _o,
    _investigations(_o, lactate=2.8, hemoglobin=14.3, wbc=10.8, creatinine=1.2,
        abg=(7.29, 49, 46), vbg=(7.25, 56),
        pocus=POCUS["pulmonary_edema"][0],
        chest_xray="Bilateral perihilar air-space and interstitial opacities with vascular congestion.", troponin=28),
    "Hypertensive acute cardiogenic pulmonary edema",
    ["Marked hypertension", "Orthopnea and diffuse congestion", "Severe hypoxemia"],
    "Support breathing and reduce excessive cardiac loading with close blood-pressure reassessment.",
    ["How did wheeze fit with the other examination findings?", "Which changes would prompt you to adjust respiratory support or vasodilation?"],
    ["niv", "nitroglycerin", "diuretic"],
    visual=_visual(expression="markedly uncomfortable", sweating="marked"),
    # Hypertensive redistribution: little excess circulating volume.
    congestion={"fluid_sensitivity": 1.0, "volume_overload": False}))

_o = _observable(164, 92, 114, 84, 32, wob="Markedly increased", crt=3,
                 extremities="Cool", temperature=36.7, glucose=132, perfusion="mildly impaired")
FAMILIES["pulmonary_edema"]["variants"].append(_case(
    "pulmonary_edema_75f", "pulmonary_edema", 75, "female", ["heart failure with reduced ejection fraction", "chronic kidney disease"],
    "A 75-year-old woman presents with breathlessness that is now preventing her from resting in bed.",
    _history("My breathing has become so bad that I have to sit up all the time.",
        ["My ankles have become more swollen and my clothes feel tighter.", "I have no fever, rigors or new sputum."],
        "I have heart failure with an ejection fraction around 30% and chronic kidney disease.",
        "I take a loop diuretic and heart-failure medicines, but missed the diuretic for three days while travelling.",
        "The swelling increased over four days; my breathing became much worse overnight.",
        "I have known reduced cardiac function and missed my usual diuretic.",
        breathing="I have slept sitting up for the last two nights.",
        chest_pain="I have not had a new focal or pressure-like chest pain.",
        urinary_symptoms="I have passed less urine but have no dysuria."),
    {"Cardiac": "Regular tachycardia, elevated jugular venous pressure and bilateral pitting ankle edema.",
     "Respiratory": "Marked respiratory effort with bilateral crackles extending to the mid-zones.",
     "Abdomen": "Soft; no focal tenderness.",
     "Neurological": "Awake and oriented, speaking in short phrases."}, _o,
    _investigations(_o, lactate=2.3, hemoglobin=11.7, wbc=9.3, creatinine=1.8,
        abg=(7.34, 43, 51), vbg=(7.30, 50), bun=34,
        pocus=POCUS["pulmonary_edema"][1],
        chest_xray="Cardiomegaly, bilateral vascular and interstitial congestion, and small pleural effusions.", troponin=35),
    "Acute decompensated systolic heart failure with pulmonary edema",
    ["Orthopnea and edema", "Diffuse B-lines with reduced LV contraction", "Recent interruption of diuretic therapy"],
    "Treat respiratory distress and congestion, checking renal function, pressure and the evolving response.",
    ["Which finding supported congestion rather than a need for more fluid?", "What would establish that the response was adequate?"],
    ["niv", "diuretic", "nitroglycerin"],
    visual=_visual(expression="markedly uncomfortable", sweating="mild"),
    # HFrEF with missed diuretic: expanded circulating volume, more fluid-sensitive.
    congestion={"fluid_sensitivity": 1.5, "volume_overload": True}))


# ACS: the diagnostic ECG and biomarker findings are authored, never invented
# from a cognitive label. Both variants require a definitive-care pathway.
_o = _observable(100, 64, 58, 96, 22, crt=3, extremities="Cool",
                 temperature=36.8, glucose=156, perfusion="mildly impaired")
FAMILIES["acs"]["variants"].append(_case(
    "acs_54m_inferior", "acs", 54, "male", ["hypertension", "dyslipidemia"],
    "A 54-year-old man presents with persistent upper-abdominal discomfort and nausea. He looks uncomfortable and sweaty.",
    _history("I have a heavy discomfort high in my abdomen that will not go away.",
        ["The discomfort sometimes extends into my chest and jaw.", "I feel nauseated and have broken into a sweat."],
        "I have high blood pressure and high cholesterol, but no previous heart attack.",
        "I take losartan and atorvastatin; I have not taken an antiplatelet today.",
        "The discomfort started 75 minutes ago while walking and has persisted at rest.",
        "I smoke, and my father had coronary disease in his fifties.",
        chest_pain="The upper-abdominal heaviness extends behind the sternum and into my jaw; it is not reproduced by touching my chest.",
        breathing="I feel mildly short of breath, without pleuritic pain.",
        bleeding="I have no hematemesis or black stool."),
    {"Cardiac": "Slow regular pulse; no new murmur heard.",
     "Respiratory": "No increased respiratory effort; lungs are clear on auscultation.",
     "Abdomen": "Soft, with no focal tenderness or guarding despite the reported discomfort.",
     "Neurological": "Awake, oriented and moving all limbs normally."}, _o,
    _investigations(_o, lactate=2.1, hemoglobin=14.1, wbc=10.5, creatinine=1.0,
        abg=(7.43, 35, 83), vbg=(7.39, 42),
        pocus=POCUS["acs"][0],
        chest_xray="No focal consolidation or pulmonary edema.", troponin=95),
    "Inferior ST-elevation myocardial infarction",
    ["Persistent exertional discomfort with autonomic symptoms", "Inferior ST elevation with reciprocal changes", "Regional LV wall-motion abnormality"],
    "Recognize the time-critical ischemic pattern and arrange reperfusion while monitoring hemodynamics.",
    ["How did the pain location influence your initial explanation?", "Which finding changed the urgency of definitive management?"],
    ["aspirin", "consult", "reperfusion_referral"], ecg="st_elevation_inferior",
    # An inferior occlusion with right ventricular involvement: the artery has to be
    # opened, and nitroglycerin can collapse a preload-dependent circulation.
    coronary={"omi": True, "territory": "inferior", "rv_involvement": True, "pci_capable": True,
              "symptom_onset_min": 75},
    visual=_visual(skin="mild pallor", sweating="marked")))

_o = _observable(146, 86, 102, 95, 24, wob="Mildly increased", temperature=36.9, glucose=184)
FAMILIES["acs"]["variants"].append(_case(
    "acs_66f_nonst", "acs", 66, "female", ["type 2 diabetes", "hypertension"],
    "A 66-year-old woman reports new breathlessness and a persistent heavy sensation across her upper chest.",
    _history("I feel unusually short of breath and there is a weight across my upper chest.",
        ["I have been nauseated and more tired than usual.", "I have not had fever, sputum or pain on deep inspiration."],
        "I have diabetes and high blood pressure; these symptoms are new for me.",
        "I take metformin, losartan and a statin.",
        "The symptoms started about three hours ago during light activity and have not fully resolved.",
        "I have diabetes and hypertension; my sister has coronary disease.",
        chest_pain="The heaviness is persistent, not positional and not reproduced by pressing on the chest.",
        breathing="I become breathless with much less activity than usual.",
        bleeding="I have no recent bleeding or black stools."),
    {"Cardiac": "Regular mildly rapid pulse; no new murmur.",
     "Respiratory": "Mildly increased effort; no focal crackles or wheeze.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert, oriented and conversant."}, _o,
    _investigations(_o, lactate=1.6, hemoglobin=12.8, wbc=9.6, creatinine=1.1,
        abg=(7.43, 35, 78), vbg=(7.39, 42),
        pocus=POCUS["acs"][1],
        chest_xray="No acute focal pulmonary abnormality.", troponin=180),
    "Non-ST-elevation acute coronary syndrome",
    ["Persistent ischemic symptoms", "ST depression", "Elevated troponin requiring contextual and serial assessment"],
    "Recognize acute ischemia without ST elevation and establish monitored specialist assessment and reassessment.",
    ["What did the absence of ST elevation establish, and what did it not establish?", "How did ongoing symptoms affect your next action?"],
    ["aspirin", "consult"], ecg="st_depression",
    # Ischaemia without an occlusion pattern: antiplatelet and anticoagulant
    # treatment with a monitored bed, and angiography that can wait.
    coronary={"omi": False, "territory": "subendocardial", "rv_involvement": False, "pci_capable": True,
              "symptom_onset_min": 180},
    visual=_visual(sweating="mild")))


# PE: one normotensive and one hypotensive case. ECG/oxygenation cannot alone
# exclude PE, and anticoagulation does not immediately normalize RV physiology.
# The three ECG patterns that carry no ST elevation yet mean an occluded artery,
# plus the pattern that means an unstable proximal lesion (faculty, 2026-09-19).
_o = _observable(132, 80, 88, 96, 20, crt=2, temperature=36.7, glucose=126)
FAMILIES["acs"]["variants"].append(_case(
    "acs_61m_posterior", "acs", 61, "male", ["hypertension", "former smoker"],
    "A 61-year-old man reports two hours of pressure across his chest and back, with nausea.",
    _history("There is a pressure in my chest that goes through to my back.",
        ["I feel sick and clammy.", "I have no fever, cough or pain on breathing."],
        "I have high blood pressure and I stopped smoking five years ago; I have had no heart attack.",
        "I take amlodipine; I have not taken an antiplatelet today.",
        "The pressure started two hours ago while I was at rest and has not eased.",
        "I have high blood pressure and a smoking history.",
        chest_pain="The pressure is central and goes through to the back; it does not change with breathing or position.",
        breathing="I am not especially short of breath.",
        bleeding="I have had no bleeding."),
    {"Cardiac": "Regular pulse at a normal rate; no new murmur.",
     "Respiratory": "No increased effort; lungs clear.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert, oriented and moving all limbs normally."}, _o,
    _investigations(_o, lactate=1.9, hemoglobin=14.6, wbc=9.4, creatinine=1.0,
        abg=(7.41, 38, 84), vbg=(7.37, 44),
        pocus=POCUS["acs"][2],
        chest_xray="No focal consolidation or pulmonary edema.", troponin=140),
    "Isolated posterior ST-elevation-equivalent myocardial infarction (occlusion MI)",
    ["Persistent rest pressure with autonomic symptoms",
     "ST depression maximal in V2-V3 with an R/S ratio above one and upright T waves: the mirror image of posterior injury",
     "Posterior wall hypokinesis on POCUS"],
    "Recognize an occlusion that the standard 12-lead shows only as a mirror image, and open the artery.",
    ["What did you conclude from the absence of ST elevation?", "Which finding made this an occlusion rather than a non-occlusion syndrome?"],
    ["aspirin", "consult", "reperfusion_referral"], ecg="posterior_infarct",
    coronary={"omi": True, "active_occlusion": True, "territory": "posterior", "rv_involvement": False,
              "pci_capable": True, "symptom_onset_min": 120},
    visual=_visual(sweating="mild")))

_o = _observable(128, 78, 96, 95, 24, wob="Mildly increased", crt=2, temperature=36.8, glucose=138)
FAMILIES["acs"]["variants"].append(_case(
    "acs_52m_de_winter", "acs", 52, "male", ["dyslipidemia"],
    "A 52-year-old man arrives with 40 minutes of heavy central chest pain and sweating.",
    _history("My chest feels crushed and I am sweating.",
        ["I feel short of breath and nauseated.", "I have no cough, fever or pleuritic pain."],
        "I have high cholesterol; I have never had a heart attack.",
        "I take atorvastatin only; I have not taken an antiplatelet today.",
        "The pain began 40 minutes ago at rest and has been constant since.",
        "I smoke and my brother had a stent at 55.",
        chest_pain="The pain is central, heavy, and radiates to both arms; it is not positional.",
        breathing="I am mildly short of breath with the pain.",
        bleeding="I have had no bleeding."),
    {"Cardiac": "Regular pulse; no new murmur; skin is cool and damp.",
     "Respiratory": "Mildly increased effort; no crackles or wheeze.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert and oriented."}, _o,
    _investigations(_o, lactate=2.2, hemoglobin=15.1, wbc=11.2, creatinine=.9,
        abg=(7.39, 36, 80), vbg=(7.35, 43),
        pocus=POCUS["acs"][3],
        chest_xray="No focal consolidation or pulmonary edema.", troponin=60),
    "Proximal anterior occlusion with de Winter T waves (occlusion MI)",
    ["Ongoing rest pain with autonomic features",
     "Upsloping ST depression at the J point with tall symmetric T waves in V2-V4 and ST elevation in aVR",
     "Anterior and apical akinesis on POCUS"],
    "Recognize a proximal anterior occlusion whose ECG pattern precedes ST elevation, and open the artery now.",
    ["Which parts of the ECG did you compare, and in which leads?", "What would waiting for ST elevation have cost?"],
    ["aspirin", "consult", "reperfusion_referral"], ecg="de_winter",
    coronary={"omi": True, "active_occlusion": True, "territory": "anterior", "rv_involvement": False,
              "pci_capable": True, "symptom_onset_min": 40},
    visual=_visual(skin="mild pallor", sweating="marked")))

_o = _observable(138, 84, 76, 97, 18, crt=2, temperature=36.6, glucose=112, pain_score=0)
FAMILIES["acs"]["variants"].append(_case(
    "acs_48m_wellens", "acs", 48, "male", ["smoking"],
    "A 48-year-old man is pain-free now after three episodes of chest pressure today, the last one an hour ago.",
    _history("I had three episodes of chest pressure today; right now I feel fine.",
        ["Each episode came with sweating and settled on its own.", "I have no fever, cough or pleuritic pain."],
        "I have no diagnosed heart disease and take no regular medicines.",
        "I take no regular medicines and have not taken an antiplatelet.",
        "The episodes began this morning; the last one ended an hour ago and lasted twenty minutes.",
        "I smoke twenty cigarettes a day.",
        chest_pain="During the episodes the pressure was central and heavy; between them I have no pain at all.",
        breathing="My breathing is normal now.",
        bleeding="I have had no bleeding."),
    {"Cardiac": "Regular pulse at a normal rate; no murmur; skin warm and dry.",
     "Respiratory": "Normal effort; lungs clear.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert, oriented and comfortable."}, _o,
    _investigations(_o, lactate=1.4, hemoglobin=15.3, wbc=8.8, creatinine=1.0,
        abg=(7.42, 39, 88), vbg=(7.38, 45),
        pocus=POCUS["acs"][4],
        chest_xray="No acute cardiopulmonary abnormality.", troponin=12),
    "Wellens syndrome: critical proximal anterior stenosis, transiently reperfused",
    ["Resolved episodes of rest pain in a patient who now looks well",
     "Biphasic or deeply inverted T waves in V2-V4 with preserved R waves and no ST shift",
     "A troponin below the reference limit, which is what the pattern requires and what "
     "separates it from an infarction without ST elevation",
     "Normal resting wall motion, which does not exclude the lesion"],
    "Recognize a pattern that demands scheduled angiography, and never provocation testing.",
    ["What did feeling well and an unraised troponin establish at this moment, and what did they not?",
     "What would a raised troponin have changed about the urgency of angiography?",
     "Which investigation would have been unsafe here, and why?"],
    ["aspirin", "consult", "reperfusion_referral"], ecg="wellens",
    coronary={"omi": True, "active_occlusion": False, "territory": "anterior", "rv_involvement": False,
              # The pattern is defined by a troponin that is not raised. A raised
              # one makes this an infarction without ST elevation, whose urgency
              # and whose answer are different (faculty, 2026-09-22).
              "myocardial_injury": False,
              "pci_capable": True, "symptom_onset_min": 180},
    visual=_visual()))

_o = _observable(104, 66, 112, 94, 26, wob="Mildly increased", crt=3, extremities="Cool",
                 temperature=36.9, glucose=168, perfusion="mildly impaired")
FAMILIES["acs"]["variants"].append(_case(
    "acs_70f_left_main", "acs", 70, "female", ["type 2 diabetes", "hypertension", "chronic kidney disease"],
    "A 70-year-old woman presents with chest pressure, breathlessness and sweating that began an hour ago.",
    _history("My chest is tight and I cannot catch my breath.",
        ["I feel sick and very sweaty.", "I have no fever or productive cough."],
        "I have diabetes, high blood pressure and kidney disease; I have had no heart attack.",
        "I take metformin, losartan and a statin; I have not taken an antiplatelet today.",
        "The tightness and breathlessness began an hour ago at rest.",
        "I have diabetes, high blood pressure and kidney disease.",
        chest_pain="The tightness is central and constant, with sweating; it does not change with breathing.",
        breathing="The breathlessness came with the chest tightness.",
        bleeding="I have had no bleeding."),
    {"Cardiac": "Regular tachycardia; no new murmur; extremities are cool.",
     "Respiratory": "Mildly increased effort; scattered basal crackles.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert and oriented."}, _o,
    _investigations(_o, lactate=3.1, hemoglobin=12.2, wbc=10.8, creatinine=1.6,
        abg=(7.36, 33, 72), vbg=(7.32, 40),
        pocus=POCUS["acs"][5],
        chest_xray="Mild pulmonary congestion without focal consolidation.", troponin=260),
    "Left main or severe three-vessel ischemia with diffuse ST depression and ST elevation in aVR",
    ["Ongoing rest pain with hypoperfusion and congestion",
     "Diffuse ST depression with ST elevation in aVR, which points to the proximal lesion rather than one wall",
     "Globally reduced contraction on POCUS"],
    "Recognize a proximal lesion behind a diffuse ECG pattern and arrange immediate invasive assessment.",
    ["What did the elevation in aVR add to the diffuse depression?", "How did the perfusion findings change your urgency?"],
    ["aspirin", "consult", "reperfusion_referral"], ecg="diffuse_st_depression_avr",
    coronary={"omi": True, "active_occlusion": True, "territory": "left_main", "rv_involvement": False,
              "pci_capable": True, "symptom_onset_min": 60},
    visual=_visual(skin="mild pallor", sweating="marked")))


_o = _observable(110, 70, 124, 90, 30, wob="Increased", crt=3, temperature=37.1, glucose=108)
FAMILIES["pulmonary_embolism"]["variants"].append(_case(
    "pulmonary_embolism_33f", "pulmonary_embolism", 33, "female", ["recent ankle fracture repair"],
    "A 33-year-old woman arrives with sudden breathlessness and sharp right-sided chest discomfort.",
    _history("I suddenly became short of breath and it hurts on the right when I breathe in.",
        ["I have felt my heart racing and a little lightheaded.", "I have no fever or productive cough."],
        "I had surgery for an ankle fracture 12 days ago and have been much less mobile.",
        "I use an estrogen-containing contraceptive and occasional acetaminophen.",
        "The breathing and chest discomfort started abruptly about two hours ago.",
        "I have recent surgery, reduced mobility and use an estrogen-containing contraceptive.",
        chest_pain="The pain is sharp and worsens with inspiration; it is not relieved by rest.",
        breathing="The breathlessness started suddenly while I was sitting.",
        bleeding="I have not coughed blood or had other recent bleeding.",
        leg_symptoms="My operated leg has been more swollen, including the calf, since yesterday."),
    {"Cardiac": "Regular tachycardia; no new murmur.",
     "Respiratory": "Increased effort; breath sounds are equal without focal crackles or wheeze.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Alert and oriented.",
     "Extremities": "Unilateral calf swelling and tenderness on the operated side."}, _o,
    _investigations(_o, lactate=2.0, hemoglobin=12.6, wbc=10.2, creatinine=.8,
        abg=(7.47, 30, 59), vbg=(7.43, 37),
        pocus=POCUS["pulmonary_embolism"][0],
        chest_xray="No focal consolidation, edema or pneumothorax.", troponin=31,
        ctpa="Acute lobar and segmental filling defects in the right and left pulmonary arteries. Mild RV enlargement.",
        d_dimer=2400),
    "Acute pulmonary embolism with hypoxemia, initially without hypotension",
    ["Abrupt pleuritic dyspnea", "Thromboembolic risk factors", "Confirmed pulmonary arterial filling defects"],
    "Establish the thromboembolic diagnosis and treatment plan while monitoring for deterioration.",
    ["Which findings were not explained by a reassuring chest radiograph?", "What would change the level of monitoring or escalation?"],
    # Surgery twelve days ago: a reason to bleed if anyone thrombolyses her.
    ["anticoagulation", "consult", "oxygen"], lysis_bleeding_risk="recent_surgery", visual=_visual()))

_o = _observable(86, 54, 132, 88, 32, wob="Markedly increased", crt=5,
                 extremities="Cool", temperature=36.7, glucose=136, perfusion="impaired")
FAMILIES["pulmonary_embolism"]["variants"].append(_case(
    "pulmonary_embolism_61m", "pulmonary_embolism", 61, "male", ["colon cancer receiving chemotherapy"],
    "A 61-year-old man is brought in after nearly collapsing. He is breathless and says he feels faint even while lying on the trolley.",
    _history("I suddenly felt breathless and nearly passed out.",
        ["I have felt my heart racing and had discomfort when taking a deep breath.", "I have no fever, sputum or recent vomiting."],
        "I am receiving chemotherapy for colon cancer; I have not previously had a clot.",
        "I receive scheduled chemotherapy and as-needed anti-nausea medication; I do not take an anticoagulant.",
        "The severe breathlessness and near-collapse began about 45 minutes ago.",
        "I have active cancer and have spent much of the last week in bed because of fatigue.",
        chest_pain="There is mild chest discomfort on a deep breath, without a sustained crushing pressure.",
        bleeding="I have no recent black stool, rectal bleeding or hematemesis.",
        leg_symptoms="My left calf has been swollen for several days."),
    {"Cardiac": "Rapid regular pulse; elevated jugular venous pressure.",
     "Respiratory": "Marked respiratory effort with equal breath sounds and no widespread crackles.",
     "Abdomen": "Soft, without guarding or focal tenderness.",
     "Neurological": "Awake and answers appropriately, but reports persistent faintness.",
     "Extremities": "Left calf swelling and tenderness."}, _o,
    _investigations(_o, lactate=4.8, hemoglobin=11.6, wbc=8.7, creatinine=1.3,
        abg=(7.43, 28, 55), vbg=(7.39, 35),
        pocus=POCUS["pulmonary_embolism"][1],
        chest_xray="No focal consolidation or pulmonary edema.", troponin=76,
        ctpa="Extensive acute bilateral main and lobar pulmonary arterial filling defects with RV enlargement and septal flattening.",
        d_dimer=5200),
    "High-risk pulmonary embolism with obstructive shock",
    ["Hypotension with impaired perfusion", "Acute RV pressure overload", "Active cancer and venous thrombosis findings"],
    "Support the patient and rapidly involve a reperfusion-capable team; reassess transport and imaging feasibility.",
    ["Could the patient tolerate your proposed diagnostic pathway?", "What required escalation beyond anticoagulation alone?"],
    ["anticoagulation", "consult", "oxygen"], ecg="right_strain", visual=_visual(shock=True)))


# ASTHMA: audible wheeze versus limited air movement and tiring; a quieter chest
# is not authored as recovery unless the evolving physiology supports recovery.
_o = _observable(138, 84, 126, 90, 34, wob="Markedly increased", temperature=36.8, glucose=116)
FAMILIES["asthma"]["variants"].append(_case(
    "asthma_24f", "asthma", 24, "female", ["asthma", "allergic rhinitis"],
    "A 24-year-old woman presents with worsening breathlessness and chest tightness. She is sitting forward and speaking in short phrases.",
    _history("My chest is tight and I cannot get my breathing under control.",
        ["I have a dry cough and can hear myself wheezing.", "I have no fever, productive sputum, rash or lip swelling."],
        "I have asthma and allergic rhinitis; I have previously needed an emergency visit but have never been intubated.",
        "I have used my reliever repeatedly today; my preventer inhaler ran out last week.",
        "Symptoms worsened over eight hours after a day outdoors with heavy pollen exposure.",
        "I have been without my inhaled controller and have needed frequent reliever use.",
        breathing="It is difficult to breathe out, and the reliever only helps briefly.",
        chest_pain="The sensation is tightness with breathing, not a separate focal or crushing pain.",
        exposure="There was heavy pollen exposure; no food exposure or new medication preceded the symptoms."),
    {"Cardiac": "Regular tachycardia; no new murmur.",
     "Respiratory": "Marked effort, prolonged expiration and widespread expiratory wheeze with reduced air entry. Peak expiratory flow is 35% of her documented personal best.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Awake, oriented and cooperative, but speech is limited by breathing."}, _o,
    _investigations(_o, lactate=2.1, hemoglobin=13.0, wbc=9.8, creatinine=.8,
        abg=(7.45, 31, 59), vbg=(7.41, 38),
        pocus=POCUS["asthma"][0],
        chest_xray="Hyperinflation without focal consolidation or pneumothorax."),
    "Acute severe asthma exacerbation",
    ["Prolonged expiration and widespread wheeze", "Reduced peak expiratory flow", "Controller interruption and repeated reliever use"],
    "Treat airflow obstruction and inflammation while tracking work of breathing and response.",
    ["Which changes would indicate relief rather than fatigue?", "How did you decide when to repeat or escalate treatment?"],
    ["bronchodilator", "steroid", "oxygen"], visual=_visual(expression="markedly uncomfortable")))

_o = _observable(142, 86, 132, 89, 30, wob="Severe", mental="Drowsy", temperature=37.0, glucose=121)
FAMILIES["asthma"]["variants"].append(_case(
    "asthma_49m", "asthma", 49, "male", ["asthma", "prior intensive care admission for asthma"],
    "A 49-year-old man is brought in with persistent breathing difficulty. He appears tired and responds to questions only briefly.",
    _history("His partner reports worsening breathing difficulty and increasing exhaustion.",
        ["His partner says the wheeze was louder earlier and he is now finding it difficult to speak.", "There has been a dry cough without fever, purulent sputum or a rash."],
        "His partner reports asthma and a previous intensive care admission requiring ventilation.",
        "He uses an inhaled corticosteroid/long-acting bronchodilator and has repeatedly used his rescue inhaler today.",
        "Breathing worsened through the day after cleaning a dusty storage room; he became sleepier over the last hour.",
        "He has a previous near-fatal exacerbation and little response to repeated home reliever use.",
        breathing="His partner says he is moving less air and can no longer complete a sentence.",
        exposure="Dust exposure preceded the symptoms; there was no witnessed aspiration or new medication.",
        chest_pain="Before becoming sleepy he described diffuse tightness rather than a focal chest pain."),
    {"Cardiac": "Regular tachycardia.",
     "Respiratory": "Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Drowsy, opens eyes to voice and follows simple commands briefly; no lateralizing motor deficit."}, _o,
    _investigations(_o, lactate=2.6, hemoglobin=14.2, wbc=10.6, creatinine=1.0,
        abg=(7.30, 51, 57), vbg=(7.26, 58),
        pocus=POCUS["asthma"][1],
        chest_xray="Hyperinflation without pneumothorax or focal air-space opacity."),
    "Life-threatening asthma with fatigue and hypercapnia",
    ["Reduced air movement despite persistent effort", "Drowsiness", "Hypercapnia with respiratory acidemia"],
    "Recognize ventilatory failure and escalate airway support while continuing obstruction-directed treatment.",
    ["How did you interpret the quieter chest?", "What evidence supported urgent escalation rather than waiting for another routine reassessment?"],
    ["bronchodilator", "steroid", "oxygen"], visual=_visual(expression="markedly uncomfortable", sweating="mild")))


# GI BLEED: relevant blood loss is discoverable through the encounter. A normal
# pulse-oximeter reading is deliberately retained despite low oxygen-carrying mass.
_o = _observable(88, 54, 124, 97, 26, crt=5, extremities="Cool",
                 temperature=36.5, glucose=118, perfusion="impaired")
FAMILIES["gi_bleed"]["variants"].append(_case(
    "gi_bleed_57m", "gi_bleed", 57, "male", ["knee osteoarthritis"],
    "A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak.",
    _history("I nearly passed out when I stood up and still feel very weak.",
        ["I have had dark, sticky stools since yesterday.", "I have felt mild burning high in my abdomen and become breathless on walking."],
        "I have knee arthritis and intermittent indigestion; no known liver disease.",
        "I have taken ibuprofen most days for my knee over the last two weeks.",
        "The dark stools began yesterday; the near-faint occurred this morning.",
        "I have used regular anti-inflammatory tablets and have new dark stools.",
        bleeding="The stools are black and sticky, not just dark brown; I have not vomited blood.",
        chest_pain="I have no central chest pressure.",
        oral_intake="I have had less appetite but have not had vomiting or diarrhea.",
        urinary_symptoms="I have no urinary burning or frequency."),
    {"Cardiac": "Regular tachycardia with weak peripheral pulses.",
     "Respiratory": "No increased effort; lungs clear on auscultation despite tachypnea.",
     "Abdomen": "Mild epigastric tenderness without guarding. Rectal examination reveals black tarry stool.",
     "Neurological": "Awake and oriented, reporting persistent faintness."}, _o,
    _investigations(_o, lactate=4.4, hemoglobin=6.7, wbc=11.1, creatinine=1.3, bun=48,
        abg=(7.37, 31, 91), vbg=(7.33, 38),
        pocus=POCUS["gi_bleed"][0],
        chest_xray="No focal consolidation or pulmonary edema.", troponin=16),
    "Upper gastrointestinal bleeding with hemorrhagic hypoperfusion",
    ["Melena", "Low hemoglobin", "Delayed refill and hypotension despite normal oxygen saturation"],
    "Restore circulating volume and oxygen-carrying capacity while arranging hemostasis and monitoring ongoing blood loss.",
    ["Did oxygen saturation describe oxygen delivery adequately?", "What separated temporary stabilization from control of the bleeding?"],
    ["blood", "ppi", "consult"], visual=_visual(shock=True, sweating="mild")))

_o = _observable(98, 62, 112, 96, 24, crt=4, extremities="Cool",
                 temperature=36.6, glucose=130, perfusion="impaired")
FAMILIES["gi_bleed"]["variants"].append(_case(
    "gi_bleed_72f", "gi_bleed", 72, "female", ["previous peptic ulcer", "osteoarthritis"],
    "A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint.",
    _history("I am unusually tired and keep feeling lightheaded when I move.",
        ["My stools have become black and sticky over several days.", "I have little abdominal pain and have not vomited blood."],
        "I had a stomach ulcer years ago and have arthritis.",
        "I have recently been taking naproxen for arthritis; I am not taking a stomach-protecting medicine.",
        "Fatigue began four days ago; the lightheadedness is much worse today.",
        "I have a prior ulcer and recent regular anti-inflammatory use.",
        bleeding="I have passed black, sticky stool for three days, with another episode this morning.",
        chest_pain="I have not had new central chest pain.",
        oral_intake="I have been drinking normally, without diarrhea or repeated vomiting.",
        urinary_symptoms="I have no urinary symptoms."),
    {"Cardiac": "Rapid regular pulse; no new murmur.",
     "Respiratory": "No increased respiratory effort; breath sounds clear bilaterally.",
     "Abdomen": "Soft without guarding or significant tenderness. Rectal examination reveals melena.",
     "Neurological": "Alert, oriented and moving all limbs symmetrically."}, _o,
    _investigations(_o, lactate=3.4, hemoglobin=6.4, wbc=10.3, creatinine=1.2, bun=43,
        abg=(7.40, 33, 84), vbg=(7.36, 40),
        pocus=POCUS["gi_bleed"][1],
        chest_xray="No acute cardiopulmonary abnormality.", troponin=17),
    "Upper gastrointestinal bleeding presenting with symptomatic anemia and hypoperfusion",
    ["Melena on targeted history and examination", "Severe anemia", "Postural symptoms with delayed refill"],
    "Recognize clinically important bleeding despite limited pain and establish resuscitation and definitive evaluation.",
    ["Which findings challenged an explanation based only on fatigue or age?", "What did you need to reassess while arranging hemostasis?"],
    ["blood", "ppi", "consult"], visual=_visual(shock=True)))


# HYPOGLYCEMIA: mentation and sweating are independent of perfusion. The arrival
# story does not supply the glucose; the learner can obtain it at the bedside.
_o = _observable(128, 76, 112, 98, 20, mental="Drowsy", temperature=36.7, glucose=34)
FAMILIES["hypoglycemia"]["variants"].append(_case(
    "hypoglycemia_28m", "hypoglycemia", 28, "male", ["type 1 diabetes"],
    "A 28-year-old man is brought from work after becoming confused and having difficulty answering simple questions.",
    _history("His coworker reports sudden confusion and difficulty finding words.",
        ["His coworker noticed shaking and sweating before he became confused.", "There was no witnessed seizure, fall or head injury."],
        "His coworker reports type 1 diabetes; his emergency information confirms this.",
        "His medication record lists basal and mealtime insulin.",
        "He was well at the start of work and became confused over the last 20 minutes.",
        "His coworker reports that he took his usual mealtime insulin but was called away before eating lunch.",
        oral_intake="His lunch was left uneaten after he took his mealtime insulin.",
        exposure="His coworker reports no known alcohol or sedative exposure during the shift.",
        neurological_symptoms="He became confused and had difficulty speaking; no one saw a persistent one-sided weakness."),
    {"Cardiac": "Regular tachycardia with palpable peripheral pulses.",
     "Respiratory": "Normal effort; clear bilateral breath sounds.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Drowsy and confused, but opens eyes to voice; speech is slow and all limbs move symmetrically. Pupils are equal and reactive."}, _o,
    _investigations(_o, lactate=1.7, hemoglobin=14.8, wbc=8.2, creatinine=.9,
        abg=(7.41, 39, 96), vbg=(7.37, 46),
        pocus=POCUS["hypoglycemia"][0],
        chest_xray="No acute pulmonary abnormality.", troponin=6),
    "Severe insulin-associated hypoglycemia with neuroglycopenia",
    ["Low bedside glucose", "Autonomic symptoms before confusion", "Insulin-meal mismatch"],
    "Correct the reversible metabolic threat and verify neurological and glucose recovery.",
    ["Which bedside check could change immediate management?", "Did the neurological findings resolve with correction?"],
    ["dextrose", "reassessment"],
    visual=_visual(skin="mild pallor", sweating="marked")))

_o = _observable(134, 78, 96, 97, 18, mental="Obtunded", temperature=36.5, glucose=38)
FAMILIES["hypoglycemia"]["variants"].append(_case(
    "hypoglycemia_76f", "hypoglycemia", 76, "female", ["type 2 diabetes", "chronic kidney disease"],
    "A 76-year-old woman is brought by her son because she has become difficult to wake this morning.",
    _history("Her son reports that she has become unusually difficult to wake.",
        ["Her son noticed sweating and reduced interaction.", "There was no witnessed seizure or head injury."],
        "Her son reports type 2 diabetes and chronic kidney disease; she is normally alert and independent at home.",
        "Her medication list includes glimepiride; she continued taking it despite eating very little.",
        "Her intake has been poor for two days; she was markedly less responsive this morning.",
        "She has continued a sulfonylurea during poor intake and has impaired renal function.",
        oral_intake="Her son reports that she has eaten little for two days but continued her usual tablets.",
        exposure="Her son reports no new sedatives or known alcohol ingestion.",
        neurological_symptoms="Her son describes a generalized reduction in responsiveness rather than a witnessed focal weakness."),
    {"Cardiac": "Regular pulse with preserved peripheral volume.",
     "Respiratory": "Normal effort and clear bilateral breath sounds.",
     "Abdomen": "Soft without focal tenderness.",
     "Neurological": "Opens eyes only briefly to a firm stimulus and localizes with both arms. Pupils are equal and reactive."}, _o,
    _investigations(_o, lactate=1.8, hemoglobin=11.8, wbc=8.6, creatinine=2.1, bun=36,
        abg=(7.39, 40, 91), vbg=(7.35, 47),
        pocus=POCUS["hypoglycemia"][1],
        chest_xray="No focal consolidation or edema.", troponin=12),
    "Sulfonylurea-associated hypoglycemia with recurrence risk",
    ["Low bedside glucose", "Continued sulfonylurea with reduced intake", "Impaired renal function"],
    "Correct glucose, reassess consciousness and plan continued monitoring for recurrent hypoglycemia.",
    ["Did an initial recovery establish that the cause had ended?", "What informed your monitoring and specialist-support plan?"],
    # Type 2 diabetes on a sulfonylurea: the pancreas still answers to an overshoot.
    ["dextrose", "reassessment"], recurrence=True, endogenous_insulin=True,
    visual=_visual(skin="mild pallor", sweating="mild")))


# The brain that is short of glucose and of thiamine at the same time: giving one
# without the other is the error the case exists to teach (faculty, 2026-09-20).
_o = _observable(118, 70, 104, 97, 18, mental="Drowsy", temperature=36.2, glucose=32,
                 crt=3, extremities="Cool")
FAMILIES["hypoglycemia"]["variants"].append(_case(
    "hypoglycemia_54m_thiamine", "hypoglycemia", 54, "male", ["alcohol use disorder", "poor oral intake"],
    "A 54-year-old man is brought from a shelter after being found drowsy and unsteady. He has eaten almost nothing for days.",
    _history("His speech is muddled and he says he feels shaky.",
        ["He has been unsteady on his feet.", "He has had no fever, cough or vomiting."],
        "He drinks heavily every day and has eaten very little for a week; he is not diabetic.",
        "He takes no regular medicines and has received no vitamins.",
        "The confusion and unsteadiness came on through this morning.",
        "He drinks heavily and has eaten almost nothing for days.",
        oral_intake="He has had almost nothing to eat for about a week, and alcohol most days.",
        neurological_symptoms="His walking has been unsteady and he says his vision feels unfocused.",
        chest_pain="He reports no chest pain."),
    {"Cardiac": "Regular mildly rapid pulse; no murmur.",
     "Respiratory": "Normal effort; clear breath sounds.",
     "Abdomen": "Soft, without tenderness or organomegaly.",
     "Neurological": "Drowsy but rousable; gaze is unsteady with a few beats of nystagmus, and gait could not be tested safely. Pupils are equal and reactive."}, _o,
    _investigations(_o, lactate=2.4, hemoglobin=12.9, wbc=6.2, creatinine=.8,
        abg=(7.44, 36, 92), vbg=(7.40, 42),
        pocus=POCUS["hypoglycemia"][0],
        chest_xray="No focal consolidation.", troponin=9, potassium=3.4),
    "Hypoglycemia in a thiamine-depleted patient, at risk of Wernicke encephalopathy",
    ["Neuroglycopenia with a capillary glucose of 32 mg/dL",
     "Weeks of alcohol use with almost no food: depleted thiamine",
     "Unsteady gaze and nystagmus, which glucose alone will not correct"],
    "Correct the glucose without precipitating an encephalopathy, and treat the deficiency that made it possible.",
    ["What did the gaze findings add to the glucose result?", "Which treatment did the glucose itself make urgent?"],
    # Faculty decision 8 of 2026-09-21: the case is about recognising the
    # hypoglycaemia and getting the treatment into the patient. The line he
    # arrives with is not in the vein, which is a state of the case and is
    # visible at the bedside. Thiamine stays as the second objective.
    ["dextrose", "thiamine", "reassessment"], thiamine_deficient=True, endogenous_insulin=True,
    iv_access_failed=True, glycogen_depleted=True,
    visual=_visual(skin="mild pallor", sweating="mild")))


# OPIOID: intentionally different contexts without stereotyped appearance.
# Slow shallow breathing is explicitly authored; no cyanosis is inferred from SpO2.
_o = _observable(106, 64, 68, 80, 6, wob="Reduced", mental="Obtunded", temperature=36.4, glucose=106)
FAMILIES["opioid"]["variants"].append(_case(
    "opioid_35m", "opioid", 35, "male", ["recent lumbar strain"],
    "A 35-year-old man is brought by a friend because he is difficult to wake and is breathing slowly.",
    _history("His friend says he became difficult to wake and started breathing very slowly.",
        ["His friend noticed increasing sleepiness after he took a tablet for back pain.", "There was no witnessed seizure, fall or trauma."],
        "His friend reports a recent back strain and no known chronic neurological disorder.",
        "He took a tablet obtained from an acquaintance for pain; its contents are not confirmed.",
        "Increasing sleepiness began within the last hour after the tablet.",
        "There is a recent exposure to a medication of uncertain contents.",
        exposure="His friend reports one pain tablet from an acquaintance; the drug identity and amount are not established.",
        breathing="His friend counted long pauses between small, shallow breaths.",
        neurological_symptoms="He became progressively sleepy without a witnessed focal deficit."),
    {"Cardiac": "Regular palpable pulse.",
     "Respiratory": "Very slow, shallow breaths with reduced chest excursion; breath sounds are equal when air enters.",
     "Abdomen": "Soft without focal tenderness.",
     "Neurological": "Obtunded, with small reactive pupils and brief bilateral withdrawal to firm stimulation; no visible head injury."}, _o,
    _investigations(_o, lactate=2.6, hemoglobin=14.5, wbc=8.9, creatinine=1.0,
        abg=(7.21, 69, 45), vbg=(7.17, 76),
        pocus=POCUS["opioid"][0],
        chest_xray="No focal infiltrate or pulmonary edema.", troponin=7),
    "Opioid toxidrome with respiratory depression following an uncertain tablet exposure",
    ["Slow shallow ventilation", "Reduced responsiveness with small pupils", "Recent uncertain medication exposure"],
    "Support ventilation promptly and reassess response to an opioid antagonist without relying on exposure labels alone.",
    ["What was the immediate physiological threat?", "How did you assess ventilation rather than oxygen saturation alone?"],
    ["naloxone", "bag_mask", "reassessment"],
    # An immediate-release tablet taken about an hour ago: a third of it has not
    # been absorbed yet, so the concentration is still climbing when the
    # resident meets him (faculty decision 3b, 2026-09-21).
    opioid_depot=.33,
    visual=_visual(expression="passive")))

_o = _observable(104, 62, 62, 84, 8, wob="Reduced", mental="Obtunded", temperature=36.3, glucose=112)
FAMILIES["opioid"]["variants"].append(_case(
    "opioid_67f", "opioid", 67, "female", ["chronic musculoskeletal pain", "chronic kidney disease"],
    "A 67-year-old woman is brought from home with increasing sleepiness and slow breathing noticed by her spouse.",
    _history("Her spouse reports that she has become increasingly sleepy and is breathing slowly.",
        ["Her spouse has struggled to keep her awake this morning.", "There was no witnessed seizure, head injury or febrile illness."],
        "Her spouse reports chronic pain and chronic kidney disease; she normally converses clearly and manages at home.",
        "Her medication list includes sustained-release morphine; her spouse is uncertain whether today's dose was repeated.",
        "She became progressively sleepier during the morning after taking her regular medication.",
        "She receives a long-acting opioid and has impaired renal function.",
        exposure="Sustained-release morphine is prescribed; a possible repeated dose is unconfirmed, and no intent is established.",
        breathing="Her spouse noticed unusually slow shallow breathing with occasional pauses.",
        oral_intake="She has eaten little today because she has been too sleepy."),
    {"Cardiac": "Regular palpable pulse.",
     "Respiratory": "Slow shallow breathing with reduced chest excursion; no focal wheeze or crackles.",
     "Abdomen": "Soft and non-tender.",
     "Neurological": "Obtunded with small reactive pupils, briefly withdrawing both arms to a firm stimulus."}, _o,
    _investigations(_o, lactate=2.2, hemoglobin=12.4, wbc=8.1, creatinine=2.2, bun=38,
        abg=(7.25, 61, 50), vbg=(7.21, 68),
        pocus=POCUS["opioid"][1],
        chest_xray="No focal consolidation or edema.", troponin=11),
    "Long-acting opioid-associated ventilatory depression with recurrence risk",
    ["Hypoventilation and reduced responsiveness", "Long-acting opioid exposure", "Impaired renal function"],
    "Restore ventilation and arrange observation for recurrent respiratory depression after an initial response.",
    ["What was the endpoint of antagonist treatment?", "Why might an early improvement require continued monitoring?"],
    ["naloxone", "bag_mask", "reassessment"], recurrence=True,
    visual=_visual(expression="passive")))


# ANAPHYLAXIS: one reaction, two circulations. The first answers to adrenaline
# and shows what the intramuscular route costs in minutes; the second answers a
# third as well because of a beta blocker nobody asked about, and the information
# that says so is in the medication history.
_o = _observable(84, 46, 126, 91, 28, wob="Increased", crt=3,
                 extremities="Warm", temperature=36.7, glucose=108,
                 perfusion="impaired", pain_score=2)
FAMILIES["anaphylaxis"]["variants"].append(_case(
    "anaphylaxis_29f", "anaphylaxis", 29, "female", ["seasonal rhinitis"],
    "A 29-year-old woman arrives from a restaurant with a spreading rash, a swollen face and noisy breathing. She is anxious and speaks in short phrases.",
    _history("My face and throat feel like they are closing and my whole body is itching.",
        ["The rash came up everywhere within minutes and my lips are swollen.",
         "I feel light-headed and my chest is tight."],
        "I have hay fever; I have never had a reaction like this and I have no asthma.",
        "I take no regular medication. I have no adrenaline autoinjector.",
        "It began about fifteen minutes into the meal and has worsened since.",
        "I ate a dish with a satay sauce; I have avoided peanuts since childhood without ever being tested.",
        exposure="The meal contained a peanut sauce; there was no sting, no new medicine and no contrast.",
        breathing="My chest feels tight and my throat feels narrow when I breathe in.",
        chest_pain="There is tightness across the chest but no crushing central pain.",
        oral_intake="I had eaten only a few mouthfuls when it started.",
        urinary_symptoms="I have no burning or frequency when passing urine.",
        bleeding="I have not coughed or vomited blood."),
    {"Cardiac": "Rapid regular pulse; the peripheries are warm and well filled.",
     "Respiratory": "Increased effort with widespread expiratory wheeze and audible inspiratory stridor.",
     "Abdomen": "Soft; mild diffuse discomfort without guarding.",
     "General appearance": "Widespread urticarial wheals, flushing and periorbital and lip swelling.",
     "Neurological": "Awake, oriented and anxious; answers are short because of the breathing."}, _o,
    _investigations(_o, lactate=3.4, hemoglobin=13.4, wbc=11.2, creatinine=0.9,
        abg=(7.34, 33, 61), vbg=(7.31, 40),
        pocus=POCUS["anaphylaxis"][0],
        chest_xray="Hyperinflated lung fields without consolidation, edema or pneumothorax.", troponin=9),
    "Anaphylaxis with upper-airway involvement, bronchospasm and distributive shock",
    ["Urticaria and angioedema minutes after a food exposure",
     "stridor with wheeze", "hypotension with warm peripheries"],
    "Give intramuscular adrenaline first and reassess the airway, the breathing and the pressure on the interval that route needs.",
    ["What did you expect the first dose to have done, and when did you look?",
     "What told you the reaction was still going, or had settled?"],
    ["epinephrine_im", "fluid", "oxygen"],
    visual=_visual(distributive=True, sweating="mild"),
    anaphylaxis={"severity": 1.0, "beta_blocked": False, "biphasic": True}))

_o = _observable(76, 42, 64, 89, 26, wob="Increased", crt=4,
                 extremities="Warm", mental="Drowsy", temperature=36.4, glucose=132,
                 perfusion="impaired")
FAMILIES["anaphylaxis"]["variants"].append(_case(
    "anaphylaxis_63m_betablocked", "anaphylaxis", 63, "male",
    ["hypertension", "atrial fibrillation"],
    "A 63-year-old man is brought in after a wasp sting in his garden. He is flushed, wheezing and difficult to rouse fully.",
    _history("His wife says he was stung, came inside saying he felt strange, and then became grey and floppy.",
        ["His wife reports a rash over his chest and arms within minutes.",
         "He complained of tightness in the throat before he stopped speaking clearly."],
        "His wife reports high blood pressure and an irregular heart rhythm. He has been stung before without a reaction.",
        "His wife lists atenolol and apixaban, taken every morning; he took both today.",
        "The sting was about twenty minutes ago and he deteriorated within ten.",
        "He keeps bees at the end of the garden and has been stung several times over the years.",
        exposure="His wife saw the wasp and the sting site on the forearm; no new medicine and no food were involved.",
        breathing="His wife says the wheeze began before he became drowsy.",
        chest_pain="His wife reports no complaint of chest pain before he stopped speaking.",
        neurological_symptoms="There was no witnessed seizure, head strike or focal weakness.",
        oral_intake="He had eaten breakfast several hours earlier.",
        bleeding="There is no bleeding from the sting site or elsewhere."),
    {"Cardiac": "Irregular pulse at a rate that does not rise with the low pressure; peripheries warm.",
     "Respiratory": "Increased effort with widespread wheeze; no stridor heard.",
     "Abdomen": "Soft and non-tender.",
     "General appearance": "Flushing over the chest and arms with scattered wheals; a sting site on the right forearm.",
     "Neurological": "Opens eyes to voice and follows simple commands slowly; moves all limbs."}, _o,
    _investigations(_o, lactate=4.6, hemoglobin=14.1, wbc=12.8, creatinine=1.3,
        abg=(7.29, 36, 57), vbg=(7.26, 43),
        pocus=POCUS["anaphylaxis"][1],
        chest_xray="No consolidation, edema or pneumothorax.", troponin=22),
    "Anaphylaxis refractory to adrenaline in a beta-blocked patient",
    ["Reaction minutes after a sting", "shock with warm peripheries and no compensatory tachycardia",
     "beta blockade in the medication history"],
    "Give adrenaline, and when the response is smaller than it should be, ask what is blunting it rather than only repeating the dose.",
    ["What did you expect after the adrenaline, and what did you actually see?",
     "What in the history explains the difference?"],
    ["epinephrine_im", "glucagon", "fluid"],
    visual=_visual(distributive=True, sweating="mild"),
    anaphylaxis={"severity": 1.15, "beta_blocked": True, "biphasic": False,
                 # A blocked receptor does not mount the tachycardia of shock
                 # either, and the rate that never rises is the finding.
                 "hr_response": 0.25}))


# RENAL COLIC: the same complaint and the same dilatation on the ultrasound.
# What separates them is the temperature, the urine, the perfusion and the
# lactate -- and asking. The study does not decide; the resident does.
_RENAL_US_MILD = ("Mild right pelvicalyceal dilatation with a 5 mm calculus at the "
                  "vesicoureteric junction. The left kidney is normal. No perinephric "
                  "collection. The bladder is not distended.")
_RENAL_US_MODERATE = ("Moderate left pelvicalyceal dilatation with a dilated proximal "
                      "ureter and a 9 mm calculus at the pelviureteric junction. The right "
                      "kidney is normal. No perinephric collection is demonstrated. The "
                      "bladder is not distended.")

_o = _observable(142, 84, 94, 98, 18, crt=2, extremities="Warm", temperature=36.8,
                 glucose=104, perfusion="preserved", pain_score=9)
FAMILIES["renal_colic"]["variants"].append(_case(
    "renal_colic_34m", "renal_colic", 34, "male", [],
    "A 34-year-old man arrives with severe right-sided flank pain that comes in waves. He cannot stay still on the trolley.",
    _history("The pain grips my right side and goes down into my groin, in waves.",
        ["I have vomited twice with the pain.", "There is no fever and no burning when I pass urine."],
        "I have never had a stone or a kidney problem and I take nothing regularly.",
        "I have taken paracetamol at home with no relief. No antibiotics.",
        "The pain started abruptly four hours ago and comes and goes every few minutes.",
        "I have been drinking little in the heat and I work outdoors.",
        urinary_symptoms="There is no burning, no frequency and no visible blood, but the urine looks concentrated.",
        exposure="There has been no instrumentation, no catheter and no recent hospital stay.",
        oral_intake="I have been drinking very little water for several days.",
        breathing="My breathing is normal; it is the pain that makes me restless.",
        chest_pain="There is no chest pain."), 
    {"Cardiac": "Regular pulse at a normal rate; peripheries warm and well filled.",
     "Respiratory": "Normal effort with clear breath sounds.",
     "Abdomen": "Soft, with right renal angle tenderness; no guarding, rebound or palpable mass.",
     "General appearance": "Restless and in evident pain, moving constantly; no rash and no pallor.",
     "Neurological": "Awake, oriented and fully cooperative."}, _o,
    _investigations(_o, lactate=1.4, hemoglobin=15.1, wbc=9.8, creatinine=1.1,
        abg=(7.41, 38, 92), vbg=(7.38, 44),
        pocus=POCUS["renal_colic"][0],
        chest_xray="Clear lung fields; no free subdiaphragmatic air.", troponin=4,
        renal_ultrasound=_RENAL_US_MILD,
        urinalysis="Blood +++. No leukocyte esterase and no nitrite. Few red cells; no white cells or bacteria."),
    "Uncomplicated ureteric colic from a distal calculus",
    ["Colicky loin-to-groin pain with a normal temperature",
     "haematuria without pyuria or nitrite", "preserved perfusion and a normal lactate"],
    "Relieve the pain, confirm there is no infection or obstruction requiring admission, and define the follow-up and the reasons to return.",
    ["What made you confident this was not an infected obstruction?",
     "What did you tell the patient would bring them back?"],
    ["antipyretic", "opioid_analgesia", "disposition"],
    visual=_visual(expression="markedly uncomfortable"),
    renal={"infected": False, "side": "right"}))

_o = _observable(94, 54, 118, 95, 24, crt=4, extremities="Cool", temperature=38.9,
                 glucose=138, perfusion="impaired", pain_score=7)
FAMILIES["renal_colic"]["variants"].append(_case(
    "obstructive_pyelonephritis_58f", "renal_colic", 58, "female", ["type 2 diabetes"],
    "A 58-year-old woman arrives with left-sided flank pain and fever. She is flushed, shivering and slow to answer.",
    _history("My left side has ached for two days and today I started shaking with fever.",
        ["I have been burning when I pass urine and going very often.",
         "I have vomited and I feel weak standing up."],
        "I have type 2 diabetes. I had a stone on the left three years ago that passed by itself.",
        "I take metformin. I have taken no antibiotic for this.",
        "The pain began two days ago and the fever and shaking started this morning.",
        "I have diabetes and a previous stone on the same side.",
        urinary_symptoms="The urine burns, I go constantly and it has looked cloudy and smelt strong since yesterday.",
        exposure="I have had no catheter, no procedure and no recent hospital admission.",
        oral_intake="I have kept almost nothing down since yesterday.",
        breathing="My breathing feels faster than usual but I am not short of breath.",
        bleeding="I have not seen blood in the urine or anywhere else."),
    {"Cardiac": "Rapid regular pulse; peripheries cool with delayed capillary refill.",
     "Respiratory": "Mildly increased rate with clear breath sounds.",
     "Abdomen": "Marked left renal angle tenderness; the abdomen is otherwise soft without guarding.",
     "General appearance": "Flushed and shivering; looks unwell and answers slowly.",
     "Neurological": "Awake and oriented but slowed; moves all limbs normally."}, _o,
    _investigations(_o, lactate=4.2, hemoglobin=12.4, wbc=19.8, creatinine=1.9,
        abg=(7.33, 31, 78), vbg=(7.30, 38),
        pocus=POCUS["renal_colic"][1],
        chest_xray="Clear lung fields; no consolidation and no free subdiaphragmatic air.", troponin=14,
        renal_ultrasound=_RENAL_US_MODERATE,
        urinalysis="Leukocyte esterase +++ and nitrite positive. Blood ++. Numerous white cells and bacteria."),
    "Obstructive pyelonephritis: an infected, obstructed collecting system with sepsis",
    ["Fever and rigors with flank pain", "pyuria with nitrite on a pelvicalyceal dilatation",
     "tachycardia, delayed refill and a raised lactate"],
    "Treat the sepsis and recognise that an obstructed infected kidney is not treated by antibiotics alone: involve urology for decompression and say what is watched until it happens.",
    ["What did the ultrasound change, and what did it not settle?",
     "Who had to be involved for this to be treated, and when did you involve them?"],
    ["antibiotics", "fluid", "consult"],
    visual=_visual(shock=True, sweating="marked"),
    renal={"infected": True, "side": "left"}))


# BRADYCARDIA: the monitor says the rate and does not say what took it. Both
# arrive slow and underperfused; one answers to a drug the resident has to ask
# for the reason to give, and the other answers to a wire.
_o = _observable(74, 44, 38, 96, 18, crt=4, extremities="Cool", temperature=36.2,
                 glucose=214, perfusion="impaired")
FAMILIES["bradycardia"]["variants"].append(_case(
    "bradycardia_ccb_68m", "bradycardia", 68, "male", ["hypertension", "atrial fibrillation"],
    "A 68-year-old man is brought in after collapsing at home. He is pale, cold and very slow on the monitor.",
    _history("His daughter says he has felt dizzy and weak all afternoon and then slumped in his chair.",
        ["His daughter reports no chest pain and no breathlessness before the collapse.",
         "He has been nauseated and vomited once."],
        "His daughter reports high blood pressure and an irregular heart rhythm treated for years.",
        "His daughter brought the boxes: verapamil, which he doubled last week on advice, and enalapril. "
        "She thinks he may have taken extra today because of palpitations.",
        "The dizziness began this afternoon; the collapse was about forty minutes ago.",
        "He lives alone and manages his own medication; the doses were changed last week.",
        neurological_symptoms="There was no seizure, no head strike and no focal weakness afterwards.",
        chest_pain="His daughter reports no chest pain before or after the collapse.",
        breathing="His daughter says the breathing has looked normal throughout.",
        oral_intake="He has eaten little today and vomited once.",
        exposure="There is no other medicine in the house and no alcohol or drug use she knows of."),
    {"Cardiac": "Very slow regular pulse; peripheries cool with delayed capillary refill; no murmur.",
     "Respiratory": "Normal rate and effort with clear breath sounds.",
     "Abdomen": "Soft and non-tender.",
     "General appearance": "Pale and cold; alert but slow to answer, with no rash or swelling.",
     "Neurological": "Awake, oriented and moving all limbs; no focal deficit."}, _o,
    _investigations(_o, lactate=3.9, hemoglobin=13.8, wbc=9.1, creatinine=1.5,
        abg=(7.31, 34, 84), vbg=(7.28, 41), potassium=4.4,
        pocus=POCUS["bradycardia"][0],
        chest_xray="Clear lung fields; no consolidation, edema or pneumothorax.", troponin=26),
    "Calcium-channel blocker poisoning with bradycardia and vasodilatory shock",
    ["Profound bradycardia with a normal potassium",
     "hyperglycaemia without a diabetic history", "the changed verapamil dose in the medication history"],
    "Recognise that the rate is a symptom of a poisoning, treat it with the antidote the cause calls for, and ask for the help that this engine cannot give.",
    ["What made you look past the rate for a cause?",
     "Which finding pointed at the poison rather than at the heart?"],
    ["calcium", "glucagon", "consult"],
    visual=_visual(shock=True),
    history_source="Daughter",
    bradycardia={"cause": "ccb", "block": False, "av_block_location": "infranodal",
                 "escape_rate": 38, "target_rate": 75}))

_o = _observable(78, 46, 32, 95, 20, crt=4, extremities="Cool", mental="Drowsy",
                 temperature=36.5, glucose=104, perfusion="impaired")
_o["rhythm"] = "Complete AV block"
FAMILIES["bradycardia"]["variants"].append(_case(
    "bradycardia_avb3_78f", "bradycardia", 78, "female", ["hypertension", "chronic kidney disease"],
    "A 78-year-old woman is brought in after repeated blackouts at home. She is grey, cold and difficult to keep awake.",
    _history("Her son says she has blacked out three times today, each time without warning.",
        ["Her son reports no chest pain and no palpitations that she described.",
         "She has been increasingly breathless on stairs for a fortnight."],
        "Her son reports high blood pressure and kidney disease; she has never had a heart attack.",
        "Her son lists amlodipine and atorvastatin. He is certain there is no beta blocker and no digoxin, "
        "and the doses have not changed.",
        "The blackouts began this morning and have become more frequent through the day.",
        "She has had two weeks of exertional breathlessness before today.",
        neurological_symptoms="The episodes were sudden, brief and without shaking, tongue-biting or confusion afterwards.",
        chest_pain="Her son reports no chest pain at any point.",
        breathing="The breathlessness on exertion has been building for a fortnight.",
        exposure="There is no new medicine, no overdose and no herbal preparation.",
        oral_intake="She has been eating and drinking normally."),
    {"Cardiac": "Very slow regular pulse with cannon waves in the neck; peripheries cool.",
     "Respiratory": "Normal effort with clear breath sounds.",
     "Abdomen": "Soft and non-tender.",
     "General appearance": "Grey and cold; rouses to voice and drifts back.",
     "Neurological": "Opens eyes to voice, follows simple commands slowly, moves all limbs."}, _o,
    _investigations(_o, lactate=3.4, hemoglobin=11.6, wbc=8.4, creatinine=2.1,
        abg=(7.33, 33, 82), vbg=(7.30, 40), potassium=4.8,
        pocus=POCUS["bradycardia"][1],
        chest_xray="Clear lung fields; no consolidation or edema.", troponin=31),
    "Complete infranodal atrioventricular block with an inadequate escape rhythm",
    ["Complete atrioventricular dissociation on the tracing",
     "cannon waves with recurrent syncope", "no drug and no electrolyte cause in the history or the laboratory"],
    "Recognise that no dose of atropine treats an infranodal block, support the rate electrically, and arrange the definitive pacing this engine does not perform.",
    ["What did the response to the atropine tell you?",
     "How did you confirm that the pacing was capturing?"],
    ["atropine", "transcutaneous_pacing", "consult"],
    visual=_visual(shock=True),
    history_source="Son",
    bradycardia={"cause": "avb3", "block": True, "av_block_location": "infranodal",
                 "escape_rate": 32, "target_rate": 70}))


_COLLATERAL_SOURCES = {
    "pneumonia_83m": "Daughter",
    "asthma_49m": "Partner",
    "hypoglycemia_28m": "Coworker and emergency medication information",
    "hypoglycemia_76f": "Son and medication list",
    "hypoglycemia_54m_thiamine": "Shelter staff and the paramedic record",
    "opioid_35m": "Accompanying friend",
    "opioid_67f": "Spouse and medication list",
    "anaphylaxis_63m_betablocked": "Wife",
    "bradycardia_ccb_68m": "Daughter",
    "bradycardia_avb3_78f": "Son",
}
_HANDOVER_CONTEXT = {
    "pneumonia_83m": "The referral note suggests possible dehydration after poor intake; no diagnosis has been established.",
    "acs_54m_inferior": "The triage note records 'indigestion?' as an unconfirmed impression.",
    "pulmonary_embolism_33f": "She wonders whether anxiety could explain the episode; this has not been assessed.",
    "asthma_49m": "Handover notes that the wheeze sounds quieter than it did earlier.",
    "anaphylaxis_63m_betablocked": "Handover notes a sting and a rash; the medication list came with the family, not with the patient.",
    "bradycardia_ccb_68m": "Handover notes a collapse and a slow rate; the boxes came in with the daughter.",
}
for _family in FAMILIES.values():
    for _variant in _family["variants"]:
        _variant["history_source"] = _COLLATERAL_SOURCES.get(_variant["id"], "Patient")
        if _variant["id"] in _HANDOVER_CONTEXT:
            _variant["presentation"] += " " + _HANDOVER_CONTEXT[_variant["id"]]


def variant_by_id(identifier):
    """Return an isolated case; caller changes must never mutate the bank."""
    for family in FAMILIES.values():
        for variant in family["variants"]:
            if variant["id"] == identifier:
                return deepcopy(variant)
    raise KeyError(f"Unknown clinical case variant: {identifier}")


del _o, _family, _variant
