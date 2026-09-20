"""Private compiler feedback and an allowlisted, nonclinical logging summary.

Issue details belong only in the author/correction request. They must never be
rendered to learners or copied into application logs.
"""
from copy import deepcopy


CLINICAL_ISSUE_CODES = frozenset({
    "MANAGEMENT_COVERAGE", "DUPLICATE_FIELD", "DUPLICATE_STUDY", "INITIAL_CIRCULATION",
    "PATIENT_PRONOUNS", "EXAMINATION_INCOMPLETE", "ESSENTIAL_STUDY_MISSING",
    "BEDSIDE_MEASUREMENT_MISSING", "DIAGNOSTIC_BINDING",
    "DIAGNOSTIC_NUMERIC", "DIAGNOSTIC_BASELINE", "BLOOD_GAS_NUMERIC",
    "BLOOD_GAS_CONSISTENCY", "ECG_UNREPRESENTABLE", "HISTORY_SOURCE",
    "VISUAL_PERFUSION", "NEUROLOGICAL_UPDATE", "UNEXECUTABLE_MANAGEMENT_PATH",
    "UNMANAGEABLE_DIAGNOSIS", "UNTREATED_COLLAPSE_TOO_FAST", "POCUS_INCOMPLETE",
    "NITRATE_HAZARD_UNDISCOVERABLE", "NITRATE_HAZARD_UNDECLARED", "POCUS_CORE_MISMATCH", "RESPIRATORY_CORE_MISMATCH",
    "CORONARY_UNDECLARED", "CORONARY_ECG_MISMATCH", "CORONARY_UNDISCOVERABLE",
    "AIRWAY_OBSTRUCTION_UNDECLARED", "AIRWAY_OBSTRUCTION_UNDISCOVERABLE",
    "PULMONARY_OBSTRUCTION_UNDECLARED", "PULMONARY_OBSTRUCTION_UNDISCOVERABLE",
    "GLUCOSE_FAILURE_UNDECLARED", "GLUCOSE_FAILURE_UNDISCOVERABLE",
    "OPIOID_TOXIDROME_UNDECLARED", "OPIOID_TOXIDROME_UNDISCOVERABLE",
    "CONTRACT_UNCLASSIFIED",
})


class ContractValidationError(ValueError):
    """All independent compiler issues for a structurally valid authored draft."""

    def __init__(self, issues):
        self.issues = deepcopy(list(issues))
        first = self.issues[0]["message"] if self.issues else "Clinical contract validation failed."
        suffix = f" ({len(self.issues)} issues in total.)" if len(self.issues) > 1 else ""
        super().__init__(first + suffix)


def safe_validation_codes(error):
    """Return only static rule codes; exclude paths, patient facts and messages."""
    from generated_engine_diagnostics import ENGINE_ISSUE_CODES
    allowed = CLINICAL_ISSUE_CODES | ENGINE_ISSUE_CODES
    codes = {
        issue.get("code") for issue in getattr(error, "issues", ())
        if isinstance(issue, dict) and isinstance(issue.get("code"), str) and issue["code"] in allowed
    }
    return sorted(codes) or ["CONTRACT_UNCLASSIFIED"]
