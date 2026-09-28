# Diccionario de datos

Ciclo 5 del AI Advisor (59BN), 2026-09-28.

**Qué define:** los conceptos persistidos principales, tal como existen en el
código de `3745b0f`. No se inventa ningún campo. Lo que todavía no existe dice
**CONCEPTUAL ONLY**.

**Las fuentes de verdad** están en `SOURCE_OF_TRUTH_MAP.md`.

| Concepto | Significado | Fuente de verdad | Dónde se guarda | ¿Versionado? | Relaciones |
|---|---|---|---|---|---|
| **ENCOUNTER** | Un intento de un usuario sobre un Decision Challenge: el caso jugado, sus turnos y su cierre | la fila del intento | `mrs_attempts`: `id`, `user_id`, `challenge_id`, `encounter_json`, `payload_json`, `status` (active/completed/abandoned), `is_sandbox`, `revision`, `created_at`, `updated_at` | `revision` crece con cada guardado; `encounter_json` queda fijo desde el inicio | tiene un CASE congelado, un MANAGEMENT TRACE, revisiones de RUBRIC y OBSERVATIONS |
| **CASE** | Un caso clínico del banco (31) o generado | para un encuentro: `encounter_json` → `encounter_spec.clinical_case` | banco: `clinical_cases.py` y `case_assessment_bank.py`; su texto en español en `case_text/es`, aprobado en `mrs_case_text_reviews` | por encuentro, congelado | lo usan los ENCOUNTERS |
| **CASE VERSION** | Qué versión del caso y de su declaración vio un encuentro | `evaluation_basis`: `versions` (cobertura, rúbrica, motor, oportunidades, catálogo) + `fingerprint` + `code_version` | dentro de `encounter_json` | sí: la huella de la declaración congelada | **No hay un número de versión del caso clínico** aparte del commit (`code_version`) |
| **MANAGEMENT TRACE** | La lista ordenada de decisiones del residente: texto, interpretación, estado de ejecución, razonamiento y estado antes y después | `payload_json.session.management_trace` | `mrs_attempts.payload_json` | con la revisión del intento | una EVIDENCE UNIT la cita por índice crudo (`trace:N`) |
| **RUBRIC** | La evaluación D1–D5 de un encuentro, propuesta por IA o decidida por un docente | la revisión confirmada | propuestas: `mrs_rubric_proposals`; revisiones (borrador o confirmada): `mrs_rubric_reviews` (`review_json`, `base_score`, `adjusted_score`, `penalty`, `domains_assessed`, `rubric_version`, `source_hash`, `attempt_revision`) | sí: `rubric_version`, `sequence`; nada se sobrescribe | por ENCOUNTER; alimenta el perfil |
| **DOMAIN SCORE** | 0–3 por dominio, o «no evaluable», con su razón | la revisión confirmada | dentro de `review_json` | con la revisión | «No evaluable» no es cero y no entra en promedios |
| **CRITICAL EVENT** | Un evento de seguridad declarado para el caso; si el docente lo confirma, resta 3 | declarado: `evaluation_basis` congelada; confirmado: la revisión de rúbrica | `encounter_json` y `review_json` | con la base y con la revisión | se cuenta aparte del radar |
| **OBSERVATION OPPORTUNITY** | Si un encuentro ofrecía observar un objetivo: `yes`, `no` o `not_reviewed`, más la regla aplicada (generation_target, declared, transition_fallback) | la declaración congelada, resuelta por `observation_opportunities.resolve` | no se guarda como fila: se lee de `encounter_json`. En cada observación se copia a `provenance_json.opportunity` | `observation_opportunities.VERSION` y la huella de la base | hace evaluable un OBJECTIVE; nunca lo observa |
| **OBSERVATION** | Un componente simulado que un docente valoró en un encuentro: satisfactorio o no, profundidad, autonomía, contexto, evidencia y notas | la fila no anulada | `mrs_progress_observations` (un índice único parcial: una activa por encuentro y objetivo; `voided_at` para anular) | `source_revision` y `payload_sha` del encuentro; `provenance_json` | por ENCOUNTER y OBJECTIVE; es la EVIDENCE UNIT |
| **EVIDENCE UNIT** | Una observación con su evidencia citada y su procedencia; la unidad que se cuenta | la OBSERVATION | `evidence_json` (ítems del trace citados) + `provenance_json` (schema `mrs.observation_provenance.v1`) | sí, por esquema | varios vínculos de marco son varias CONTRIBUTIONS de la misma unidad, nunca varias unidades |
| **EVIDENCE CONTRIBUTION** | Lo que la unidad aporta a un vínculo de marco (ACGME o Royal College) | `provenance_json.contributions` al confirmar | dentro de la observación | `mapping_version` | una por vínculo activo del objetivo |
| **DIRECT** | La contribución observa el componente del vínculo | `competency_mapping` (`contribution: DIRECT`) | vínculo del objetivo; copia en la procedencia | `MAPPING_VERSION` | no cambia puntajes ni cuentas |
| **PARTIAL** | La contribución observa parte del componente y dice qué queda fuera (`limitation`) | `competency_mapping` | ídem | ídem | es válida, no es un defecto; 9 vínculos PARTIAL siguen inactivos por decisión docente |
| **COMPONENT** | La parte observable de un objetivo o de un vínculo (`component_observed`, `observable_component` de una oportunidad) | la definición del vínculo o de la declaración | `competency_mapping`, declaraciones del caso | con el mapping o la base | **No hay tabla de componentes**: es texto dentro de vínculos y declaraciones |
| **FRAMEWORK TARGET** | El hito o EPA de un marco externo al que apunta un vínculo (p. ej. EPA C14, PC6) | `competency_mapping` / `objectives` | código | `MAPPING_VERSION` | **CONCEPTUAL ONLY** como meta del residente: no hay seguimiento por hito ni por EPA completa |
| **OBJECTIVE PROGRESS** | Por objetivo: cuántas observaciones satisfactorias cumplen la autonomía exigida, frente a la meta | calculado al leer | `mrs_progress_targets` (meta vigente, con revisión) + observaciones | la meta tiene `revision` | no se guarda el total; «C14 3/50» se recalcula |
| **FACULTY CONFIRMATION** | Dos cosas distintas: (1) confirmar una observación, (2) confirmar que un objetivo está logrado | (1) la fila de observación, (2) `mrs_progress_confirmations` | `mrs_progress_observations` (`assessor_id`) y `mrs_progress_confirmations` (`confirmed`, `reason`, `actor_id`, `count_at_confirmation`, `observation_ids_json`) | (2) guarda la cuenta y los IDs al confirmar | una confirmación de objetivo no cuenta observaciones por sí misma |

## Lo que no está

- **Versión numerada del caso clínico.** Hoy se identifica por el commit
  (`code_version`) y por la huella de la declaración congelada.
- **Tabla de componentes y de metas por marco.** Están como texto en el código.
- **Clave de idempotencia por envío** del residente.
  - Una orden reenviada es un turno nuevo del Trace. Si el motor la repite
    depende del fármaco: una dosis única ya dada no se repite
    (`family_engine.py:1074`).
  - El doble clic no duplica: el formulario se vacía al enviar y un envío
    vacío se ignora.
  - Ver `AUDITORIA_NOCTURNA_CICLO5.md`, sección 1.
