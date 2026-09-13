# Cognitive challenge catalog

This catalog adds eight local formative objectives to the three existing
management-reasoning objectives. Each new objective can select more than one
clinical family. A bias label describes the teaching opportunity; it does not
establish that a learner displayed that bias. Year assignments are local exposure
settings, not ACGME milestones, Royal College stages, or certification thresholds.

Initial automatic assignment prioritizes unseen objectives from this varied-case
catalog within the learner's assigned year. The three earlier circulatory
foundations remain selectable and are assigned after the new eligible objectives
have been encountered. Subsequent assignment retains the existing latest-evidence
gap and interleaving rules.

## Catalog mapping

`Yes` means the pairing is declared in `cognitive_catalog.py`. The case bank,
generator, examination, investigations, and treatment engine must support a
pairing before an encounter can be delivered. This table is not evidence of
clinical validation or of successful publication.

| Challenge | Pneumonia | Pulmonary edema | ACS | Pulmonary embolism | Asthma | GI bleed | Hypoglycemia | Opioid |
|---|---|---|---|---|---|---|---|---|
| R1-05 · Anchoring | Yes | Yes | — | — | — | — | — | — |
| R1-06 · Premature closure | — | — | — | — | — | — | Yes | Yes |
| R2-02 · Confirmation | — | — | Yes | Yes | — | — | — | — |
| R2-03 · Availability | Yes | — | — | Yes | — | — | — | — |
| R1-07 · Framing | — | — | Yes | — | — | — | Yes | — |
| R2-04 · Representativeness | — | — | Yes | Yes | — | — | — | — |
| R2-05 · Search satisficing | Yes | — | — | — | — | Yes | — | — |
| R3-01 · Action bias | — | Yes | — | — | Yes | — | — | — |

The families have distinct patient histories, clinical findings, investigation
patterns, and management needs. Selecting a different diagnosis label without
changing those elements does not create a different clinical family.

## Learning objectives

| Challenge | Observable reasoning opportunity |
|---|---|
| R1-05 | Compare later observations with the first explanation and revise management when needed. |
| R1-06 | Reassess residual abnormalities and recurrence risk after an initial explanation or response. |
| R2-02 | Seek and interpret findings that could weaken the current hypothesis. |
| R2-03 | Distinguish the current encounter from an explicitly supplied recent-case context. |
| R1-07 | Separate handover observations from interpretations and establish current priorities. |
| R2-04 | Evaluate consequential explanations when the presentation does not match a familiar prototype. |
| R2-05 | Continue addressing unexplained findings after the first abnormality is identified. |
| R3-01 | Compare another intervention with reassessment or monitored observation, while preserving timely indicated care. |

Premature closure and search satisficing overlap conceptually. Here their
instructional emphasis differs: the former focuses on declaring the immediate
problem addressed after an explanation or initial response; the latter focuses on
whether finding one abnormality ends the search for remaining clinical needs.
They are not asserted to be independent psychometric constructs.

## Encounter and review rules

- Keep bias labels, objectives, family identifiers, and expected diagnoses out of
  the active learner encounter. The learner receives the presenting concern,
  visible patient state, and information obtained through the encounter.
- Availability includes a short, explicitly fictional shift exposure. It must
  never invent the learner's real clinical experience. A recent respiratory
  infection context may lead to either pneumonia or pulmonary embolism; the
  context is not automatically wrong.
- Handover impressions must be marked as impressions. Do not fabricate
  contradictory facts, introduce demographic stereotypes, or withhold available
  answers to clinically directed questions.
- Patient evolution depends on the clinical scenario, elapsed simulation time,
  and executed actions. The bias label must not worsen the patient or reward a
  particular wording.
- Preserve the information available before each decision, the stated working
  explanation, priorities, expected effect, executed actions, observed response,
  and later reflection. An outcome alone cannot identify the reasoning process.
- Review evidence descriptively and use the catalog's open debrief questions.
  Presence of a reasoning field does not establish its quality. Do not produce an
  automated diagnosis of bias, a learner trait score, or a competence decision.

## Evidence informing the educational design

An experiment with internal medicine residents found that knowledge of
discriminating clinical features predicted resistance to anchoring; spending
longer deliberating did not by itself explain the performance differences. This
supports teaching concrete comparisons between plausible explanations, alongside
reflection. It does not validate this simulator or its family mappings.
[Mamede et al., BMJ Quality & Safety, 2024](https://pubmed.ncbi.nlm.nih.gov/38365449/).

The availability experiment deliberately exposed participants to earlier cases
before testing superficially similar cases with different diagnoses. Its design
supports supplying an actual simulated prior exposure rather than retrospectively
calling an incorrect answer "availability bias." Structured reflection improved
diagnostic accuracy within that experimental task.
[Mamede et al., JAMA, 2010](https://jamanetwork.com/journals/jama/fullarticle/186585).

A study of bias recognition in case workups found disagreement between observers
and a strong effect of outcome information on retrospective bias attribution.
The simulator therefore preserves the pre-outcome reasoning record and treats
bias labels as discussion topics, not automated findings about the learner.
[Zwaan et al., BMJ Quality & Safety, 2017](https://pubmed.ncbi.nlm.nih.gov/26825476/).

The mappings, prompts, and year assignments above are local educational design
choices. They require faculty review with actual encounters; the cited studies
do not establish their reliability, transfer to clinical practice, or clinical
validity.
