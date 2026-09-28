# Mapa de fuentes de verdad

Ciclo 5 del AI Advisor (59AL), 2026-09-28.

**Para qué sirve:** que una función nueva lea la fuente primaria y no una copia
derivada. Describe el código de `3745b0f`; no cambia nada.

**La regla general:**

- lo que un encuentro fue se lee de lo que el encuentro guardó al empezar y al
  jugarse;
- lo que el docente decidió se lee de las tablas del docente;
- todo lo demás es una vista.

| Concepto | Fuente autoritativa | Copias o vistas derivadas (no leer como fuente) | Nota |
|---|---|---|---|
| **Estado clínico del caso (en un encuentro)** | `mrs_attempts.encounter_json` → `encounter_spec.clinical_case`, congelado al iniciar | `clinical_cases.py`, que sólo sirve para encuentros **nuevos**; `case_text/es` es la traducción | El motor lee el caso desde el encuentro (`family_engine._case`, `acs_reperfusion.coronary`). Cambiar el banco no cambia un encuentro ya iniciado |
| **Management Trace** | `mrs_attempts.payload_json` → `session.management_trace` (índices crudos `trace:N`) | brief docente, PDF/MD de Decision Review, portal del residente, `mrs_learner_trace_analyses` | Una referencia de evidencia es el índice crudo, estable al agregar eventos (`objectives.evidence_items`) |
| **Rúbrica (D1–D5)** | `mrs_rubric_reviews` con `status = 'confirmed'`, la última revisión por encuentro | `mrs_rubric_proposals` (propuesta de IA), perfil y radar (`rubric_progress.aggregate`), PDF | Una propuesta nunca es resultado. Un borrador nunca entra al perfil |
| **Eventos críticos** | Declarados: `evaluation_basis` congelada en `encounter_json`. Confirmados: la revisión de rúbrica confirmada | `case_assessment_bank.py` (sólo encuentros nuevos), `docs/COBERTURA_CASOS.md` | Se cuentan aparte; nunca se promedian en un dominio |
| **Observation opportunity** | La declaración congelada (`encounter_json.evaluation_basis.declaration.objectives`), resuelta por `observation_opportunities.resolve` | `case_assessment_bank.C14_DECLARATIONS` (sólo encuentros nuevos), `docs/C14_TABLA_FINAL.md` | Sin copia congelada → regla de transición, nunca las declaraciones actuales |
| **Confirmación docente (de una observación)** | `mrs_progress_observations`: la fila no anulada, con `assessor_id`, `evidence_json`, `provenance_json` | `mrs_progress_drafts` (borrador, nunca cuenta), `mrs_progress_audit` (bitácora), sugerencia de IA | Una sola fila activa por encuentro y objetivo: índice único parcial `mrs_progress_current_observation` |
| **Confirmación de un objetivo** | `mrs_progress_confirmations` (una fila por residente y objetivo, con los IDs revisados) | el estado «confirmed» del portal | Es una decisión docente distinta de observar |
| **Objective Progress** | Calculado al leer (`ProgressStore.get_progress`) desde las observaciones y la meta vigente (`mrs_progress_targets`) | cualquier número mostrado («C14 3/50») | No se guarda un total: se recalcula |
| **Framework mapping** | `competency_mapping.py` (`MAPPING_VERSION`) y, para cada observación, `provenance_json.contributions` al confirmarla | `objectives.OBJECTIVES` (definición actual), docs de verificación de fuentes | Una observación antigua conserva los vínculos con que se confirmó |
| **Perfil del residente** | Derivado: `rubric_progress.aggregate` sobre las revisiones confirmadas; `get_progress` para los objetivos | radar, tablas y PDFs | No hay tabla de perfil. `mrs_resident_profiles` guarda el año y los datos de cuenta, no el desempeño |
| **Validation corpus** | Los DOCX devueltos, tal como llegaron, y `manifest.json` / `split.json` del corpus, fuera del repositorio | `entries.json`, hojas CSV y reportes, todos regenerables | SEALED nunca entra al repositorio. El baseline de cada corrida lo nombra `validation/baselines.json` |

## Tres trampas a evitar

- **Leer `clinical_cases.py` o `case_assessment_bank.py` para un encuentro ya
  jugado.** Hay que leer el `encounter_json` del encuentro. La única excepción
  es la reevaluación explícita (`evaluation_basis.reevaluation`), que guarda
  las dos bases.
- **Contar desde el brief de IA, la propuesta de rúbrica o un borrador.**
  Sólo cuenta lo confirmado por un docente.
- **Tratar un total mostrado como dato.** Objective Progress y el perfil se
  recalculan; guardarlos como número los desincronizaría.
