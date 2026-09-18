# Development ECG waveform model

`ecg12.py` provides calibrated, deterministic **educational** recordings. It is not a recording from a real patient, a validated electrophysiology model, or a complete reproduction of every finding obtainable from a clinical ECG. Numerical consistency tests do not establish diagnostic accuracy. The module is a foundation for faculty-reviewed case-specific ECGs; the current clinical-problem generator does not suddenly gain ACS, pulmonary embolism, or every arrhythmia scenario by importing it.

## Acquisition and reproducibility

- `acquire_ecg(state)` returns a JSON-serializable snapshot under 1.5 KB, without mutating `state`. Store the returned snapshot in the encounter's ECG investigation record.
- The snapshot freezes acquisition simulation time, heart rate, rhythm, explicit morphology profile, encounter seed and model version. It contains no image and no sample arrays. A recording remains unchanged after later interventions; repeat acquisition captures the new state.
- `ecg_signals(snapshot)` reconstructs all twelve simultaneous 10-second sample arrays in mV at 500 samples/second. A different model version must retain its own decoder; silently regenerating old recordings with a changed model is not permitted.
- `render_ecg_svg(snapshot)` displays a conventional 3×4 sequential layout: I/aVR/V1/V4; II/aVL/V2/V5; III/aVF/V3/V6. Successive columns show 0–2.5, 2.5–5, 5–7.5 and 7.5–10 seconds, with a continuous 10-second II strip below. Labels explicitly identify sequential panels.
- All plots share 25 mm/s and 10 mm/mV geometry. A small square is 40 ms by 0.1 mV; the calibration pulse is 0.2 seconds by 1 mV. SVG physical dimensions preserve these ratios, while browser resizing scales the entire chart together. A screen's physical millimetres depend on zoom and hardware; measure against the grid.
- `monitor_wave_svg(observable, profile="baseline", seed=0)` shows a dark bedside lead II with a moving sweep. Pass the same profile and encounter seed as acquisition. The sweep is a display animation; it does not advance simulation time or autonomously change physiology.

The calibration and repeat-recording design follows [PiCSA, Adult & Paediatric Electrocardiography guideline, §4.7.4](https://picsa.org.au/wp-content/uploads/2023/01/PICSA-Clinical-Practice-Guidelines-ECG-compressed.pdf). The signal source is synthetic; no acquisition-device filtering, artefact or diagnostic bandwidth compliance is claimed.

## Shared electrical source

Every lead uses the same ventricular activation times and temporal P/Q/R/S/T/ST components. AF varies the single ventricular clock, so leads cannot disagree about RR timing. I and II are independent frontal projections; the other limb leads are algebraically derived sample by sample:

- III = II − I
- aVR = −(I + II)/2
- aVL = I − II/2
- aVF = II − I/2

Precordial electrode weights vary for the same components, giving distinct V1–V6 morphology and R/S progression. This is a low-dimensional illustrative source model, not a three-dimensional torso/heart forward solution. Interval definitions and lead orientations follow the [University of Utah ECG Learning Center, Standard 12 Lead ECG](https://ecg.utah.edu/lesson/1). We use compact-support wave components so P onset, QRS boundaries and T offset are measurable. The chosen coefficients are authored model parameters, not patient-derived statistics.

## Supported rhythm templates

| Explicit rhythm | Representation |
|---|---|
| Sinus rhythm, sinus tachycardia, sinus bradycardia | One P wave before each narrow QRS; state heart rate controls RR |
| AF / atrial fibrillation | Irregular RR intervals; fibrillatory baseline; no organized P waves |
| SVT | Regular narrow QRS; no separable P-wave template |
| Atrial flutter | Illustrative fixed 2:1 conduction; atrial frequency twice ventricular rate |
| Complete heart block | Independent 75/min atrial clock and state ventricular escape rate |
| Junctional rhythm | Narrow regular QRS without a visible P-wave template |
| VT | Illustrative broad monomorphic ventricular complexes with discordant T waves |
| VF | Coarse disorganized ventricular activity, without organized QRS complexes |
| Asystole | No modeled electrical activity |

Organized rhythms are supported only from 20 to 300/min. Unknown rhythms or invalid rates return `status="unavailable"` with a reason; they never silently become sinus rhythm. `PEA` must include `observable.electrical_rhythm`: pulseless electrical activity does not specify one ECG morphology. Pulse absence never turns an organized rhythm into a flat line. These simplified rhythm templates require clinical review before using them as scored diagnostic exemplars.

## Explicit morphology profiles

The source is `state.ecg_profile`, then `state.encounter_spec.ecg_profile`, otherwise `baseline`. Changing haemodynamics or asking about a disease cannot select a profile. Only the underlying case physiology/author may change this field during an encounter.

| Profile | Illustrative feature |
|---|---|
| `baseline` | No authored ST shift; baseline precordial R/S progression |
| `st_elevation_anterior` | Anterior contiguous ST elevation, largest in V2–V4 |
| `st_elevation_inferior` | Inferior ST elevation and reciprocal high lateral depression |
| `st_elevation_lateral` | Lateral ST elevation, including I/aVL and V5–V6 |
| `st_depression` | Multilead ST depression; aVR follows the limb-lead identities |
| `right_strain` | Rightward frontal forces, altered V1 R/S and T inversion V1–V4/inferiorly |

Topographic ST patterns were checked against the [University of Utah ECG Learning Center, Myocardial Infarction](https://ecg.utah.edu/lesson/9); the implemented amplitudes and waveform shapes remain our own unvalidated examples. Right-sided repolarization/force features are described in [University of Utah, Ventricular Hypertrophy](https://ecg.utah.edu/lesson/8). These are electrical patterns, not diagnoses: `right_strain` does not establish pulmonary embolism, and `st_depression` does not establish NSTEMI. Ischaemia and pulmonary embolism can have other or nondiagnostic ECG appearances. A baseline recording must not exclude either clinical condition in the simulator's reasoning engine.

For clinical source review, the 2023 ESC ACS guideline (doi: [10.1093/eurheartj/ehad191](https://doi.org/10.1093/eurheartj/ehad191)) and the 2019 ESC pulmonary embolism guideline (doi: [10.1093/eurheartj/ehz405](https://doi.org/10.1093/eurheartj/ehz405)) discuss ECG findings in their broader clinical context. Full publisher texts were not retrievable in this development environment; these citations are references for faculty review, not claims that this model has been validated against the guidelines.

## Remaining clinical scope

Not implemented: patient-specific conduction anatomy, bundle/fascicular blocks, graded AV blocks, ectopy/capture/fusion, pre-excitation, pacing, long-QT/drug/electrolyte effects, infarct evolution/Q waves, reciprocal patterns for every territory, posterior/right-sided additional leads, artefact, lead reversal, diagnostic filter effects or a validated automated interval/axis interpretation. Mixed VT/VF/asystole plus ST profiles are refused rather than composed misleadingly. The default numerical QT rate adaptation is illustrative and must not be used to teach a drug's QT response.

The learner sees the tracing and acquisition time, without an automatic diagnosis label. Before claiming the information content of a real ECG, add de-identified licensed reference recordings or a validated signal library, map them to reviewed clinical states, and have clinicians review morphology, intervals, ST/T distributions and serial evolution. Keep that clinical review distinct from the regression tests.

## Verification

`python -m unittest test_ecg12 -v` covers frozen compact snapshots, serial changes, sample-level limb identities, shared activation times, distinct precordials, AF irregularity/rate, measurable ST polarity, right-sided T inversion, unsupported states, pulse/electrical separation, 3×4 layout and exact calibration geometry. These tests verify software properties only.
