"""The names of the history topics a case can author. Data, with no imports.

A leaf on purpose. These labels are needed by the PDF renderers, by the rubric
declarations and by the coverage matrix, none of which should have to import
Streamlit and PIL -- which is what reaching them through ``clinical_scene``
costs, and which deadlocked a test run on 2026-09-23 when one thread imported
that module while another already held its import lock.

``clinical_scene`` re-exports these, so every existing reader is unchanged.
"""

# Only recorded patient-history topics are exposed to conversational retrieval.
# The full case specification also includes diagnoses and teaching objectives.
HISTORY_TOPIC_LABELS = {
    'chief_complaint': 'Presenting symptoms',
    'onset': 'Onset and course',
    'associated_symptoms': 'Associated symptoms',
    'medical_history': 'Previous health',
    'medications': 'Medications',
    'allergies': 'Allergies',
    'risk_factors': 'Relevant exposures and risk factors',
    'chest_pain': 'Chest discomfort',
    'breathing': 'Breathing symptoms',
    'bleeding': 'Bleeding symptoms',
    'oral_intake': 'Eating and drinking',
    'exposure': 'Recent exposures',
    'urinary_symptoms': 'Urinary symptoms',
    'neurological_symptoms': 'Neurological symptoms',
    'leg_symptoms': 'Leg symptoms',
}
