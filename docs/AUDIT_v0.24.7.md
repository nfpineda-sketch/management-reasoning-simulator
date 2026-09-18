# Offline generator/compiler audit — v0.24.7 (prepared, not deployed)

## Confirmed discrepancies

1. The engine automatically binds all modeled diagnostic numbers to baseline physiology, even when the author omits result_bindings. Earlier clinical collectors only inspected explicit bindings. A conflicting unbound glucose result reached the final fallback and became CONTRACT_UNCLASSIFIED. Regression reproduction now receives DIAGNOSTIC_BINDING with the investigation path and original message before repair. No acceptance check is removed.
2. Author instructions require volume_model=null while the full response schema offers volume compartment conditions, volume_basis and diuresis_ml_min, which the engine rejects without a volume model. The compact author schema excludes those unavailable choices. Existing full runtime specs remain supported.
3. The same baseline measurements and fixed engine constants were requested repeatedly from the author. A new compact API contract keeps clinical source values and derives technical duplication locally. It fills schema/core versions, engine model, null legacy volume/terminal configurations, empty untreated drift and laboratory bindings. A modeled result is selected by field name; its value is copied from observable/initial_labs. pH uses the existing gas equation. Nonmodeled results remain authored. Shared CO2 across VBG/ABG is an explicit limitation, not a claim of clinical equivalence.

## Preservation

Patient facts, full history, examination, objective, diagnosis, management dilemma, extension responses and native phenotype inputs remain authored. The expanded case passes the existing runtime schema, compiler and independent reviewer before launch. Duplicate fields and incompatible values still reject. Existing saved case execution is unchanged. Legacy full draft responses remain parseable; new provider requests use the compact schema. Corrections use the same compact output schema.

## Verification and limits

Four standard-library unittest regressions pass: expansion plus compilation and data preservation; omitted-binding conflict rejection; malformed/injected values and duplicates rejected; mocked end-to-end author -> expansion -> independent review -> encounter initialization. Python compilation and git diff checks pass. The full pytest/UI suite was unavailable in this environment. No paid API calls, latency benchmark, production deployment or provider switch were performed.

The actual earlier CONTRACT_UNCLASSIFIED draft is unavailable; the confirmed code discrepancy is not proof that it caused that specific historical failure. The supplied latest report contains only a 120-second author timeout and no draft. Request-size reduction is not evidence of improved acceptance or lower billing until measured with controlled real requests.
