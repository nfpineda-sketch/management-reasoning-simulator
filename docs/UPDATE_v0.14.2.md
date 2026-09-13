# R1-03: management remains unresolved after the history

The patient gives short, source-grounded positive symptoms to broad questions.
Urinary symptoms are available immediately; they are not delayed until a treatment.
Negatives, intake and chronology remain available to specific questions. The
History topics shortcut no longer returns the entire review of systems. A short
management prompt remains visible while exploring: what needs action now, what
can occur in parallel or wait, and what response changes the plan.

## Model correction, new R1-03 encounters only

The generated inflammatory profiles inherited zero vasoplegia from the legacy
case. Untreated pressure rebounded toward the legacy equilibrium. The existing
AF causal weight affected an immediate small pressure increment but not the
stroke-volume rhythm penalty. Newly generated R1-03 states now include explicit
vasoplegia (volume-limited .35, rhythm-contributor .25, mixed-low-flow .30) and
an opt-in rhythm penalty proportional to AF causal weight. Old saved encounters,
R1-04, R2-01 and fixed classroom states retain their existing coupling.

These values are teaching-model calibration, not validated clinical parameters.
No best treatment, diagnosis or automatic competence score is inferred from them.

## Equal-time counterfactual check

Same history, seed 17; compare observation alone with the existing sedation /
cardioversion bundle, both at simulation minute 3:

| Profile | Observation BP | Rhythm bundle BP | Post-bundle CRT |
|---|---|---|---|
| Volume-limited | 91/50 | 102/58 | 3 s |
| Rhythm contributor | 97/56 | 114/68 | 2 s |
| Mixed low flow | 88/50 | 98/58 | 4 s |

The bundle includes sedation; its effect is not attributed solely to cardioversion.
Conversion is not equivalent to full recovery. These examples are software
regressions, not thresholds for grading learners or clinical recommendations.
Tests repeat at seeds 17 and 83, preserve source history, check untreated drift,
residual perfusion and stronger rhythm-bundle response in the rhythm-contributor.

## Faculty review focus

Assess the learner's recorded causal explanation, priority, parallel/deferred
steps, expected effect, reassessment and adaptation. Finding a possible infection
source does not establish the relative contribution of the rhythm. Appropriate
information gathering must never be penalized. Distinguish the proposed model
from what the subsequent observed response supports; do not prescribe a single
sequence from a profile label. Existing evidence-based assessment remains manual.

## Deploy and try

Reboot only the development app to refresh imported generator modules, then start
a NEW R1-03 encounter. Old cases are intentionally not recalibrated retrospectively.
No new secrets are required. Public main and IA branches are not changed.

For local use, unzip management_reasoning_simulator_v0.14.2.zip in ~/Downloads,
enter its directory, install requirements.txt, configure existing private secrets,
and run `python -m streamlit run app.py`.
