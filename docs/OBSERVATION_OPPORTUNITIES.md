# Observation opportunities y contribuciones de evidencia

Ciclo 3 del AI Advisor. Decisiones docentes del 2026-09-27 sobre:

- DF-1 (D-1 a D-6);
- DF-2 (R1-03, R1-04 y R2-01 con contribuciones con alcance).

**Estado:** IMPLEMENTED y TESTED, con commits en `clinical-encounter-v0.13`.

**Documentos relacionados:**

- `docs/PROPUESTA_OBSERVATION_OPPORTUNITIES.md`: la propuesta de los ciclos 1 y
  2, que esto implementa;
- `docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md`: el borrador C14;
- `docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md` §6: los vínculos activos e
  inactivos.

## 1. Modelo y terminología (§80, §81)

Estas palabras no son sinónimos y el código las mantiene separadas:

| Término | Qué es | Dónde vive |
|---|---|---|
| **CASE TARGET** | El objetivo para el que se generó o asignó el encuentro. Es una fuente de oportunidad, no la única. | `competency_mapping.record_challenge_id` |
| **OBSERVATION OPPORTUNITY** | Lo que el caso permite observar, declarado antes del encuentro y congelado con él. | `observation_opportunities.resolve` |
| **OBSERVATION** (observed performance) | Lo que el residente realmente hizo y quedó registrado: decisiones, razonamiento y reflexión. | El Management Trace del encuentro |
| **CONFIRMED OBSERVATION** | La valoración docente de ese desempeño para un objetivo, con la evidencia citada. | Una fila de `mrs_progress_observations` |
| **EVIDENCE CONTRIBUTION** | La relación entre una observación confirmada y un componente de un framework: directa o parcial, con el componente observado y lo que queda fuera. | `provenance_json.contributions` |
| **CONSTRUCT COVERAGE** | La acumulación de contribuciones sobre distintas partes del constructo. **No se calcula** (§6). | — |
| **COMPETENCY / ENTRUSTMENT DETERMINATION** | Una decisión posterior, humana, que este sistema **no** realiza. | — |

**Cadena:**

- una oportunidad hace que un objetivo sea evaluable;
- una observación existe cuando el docente valora el desempeño registrado,
  nunca antes;
- una contribución describe qué aporta esa observación;
- la cobertura del constructo y la determinación de competencia quedan fuera
  del sistema.

**Dos afirmaciones que el código garantiza con tests:**

- **AUSENCIA DE OPORTUNIDAD ≠ FALLA.** Un objetivo sin oportunidad no es
  evaluable en ese encuentro y no genera una observación negativa.
- **OPORTUNIDAD YES ≠ OBJETIVO DEMOSTRADO.** Nada se registra hasta la
  valoración docente. Un encuentro generado para un desafío tampoco crea
  evidencia por sí mismo.

## 2. Dónde se declara y cómo se congela

**Dónde se declara.** El bloque opcional `objectives` va dentro de la
declaración de rúbrica del caso (`case_assessment_bank`), junto a sus dominios y
eventos críticos. Es la estructura existente; no hay un sistema paralelo.

```python
"objectives": {
    "C14": {"opportunity": "yes",
            "rationale": "por qué el caso realmente lo ofrece",
            "observable_component": "qué parte del objetivo puede verse",
            "expected_evidence": ("qué mostraría el Management Trace", ...),
            "reviewed": {"by": "quién lo revisó clínicamente", "on": "AAAA-MM-DD"}},
    "C3": {"opportunity": "no", "reason": "por qué no",
           "reviewed": {"by": "...", "on": "AAAA-MM-DD"}},
}
```

**Cómo se congela.** El bloque viaja en la declaración que
`evaluation_basis.freeze` copia al encuentro cuando empieza, con su huella.
Después solo se lee esa copia:

- un cambio posterior del caso nunca cambia lo que ofreció un encuentro anterior;
- `evaluation_basis.versions()` agrega `"opportunities": "1.0"`, de modo que una
  base congelada antes de las oportunidades se distingue de un caso que
  simplemente no declara ninguna.

**Validación.**

- `case_assessment.verify` revisa la forma: `yes` necesita razón, componente
  observable y evidencia esperada; `no` necesita razón; ambos dicen quién lo
  revisó y cuándo.
- `observation_opportunities.verify_bank` revisa además que cada objetivo
  exista.
- La separación se mantiene: la rúbrica no importa el catálogo de objetivos
  (`test_rubric_is_separate_from_challenges`).

## 3. Estados, reglas y transición

**Tres estados, nunca fusionados:**

- `yes`: el caso declara una oportunidad real, y por qué;
- `no`: el caso declara que no la hay, y por qué;
- `not_reviewed`: nadie lo declaró. **Nunca se lee como `no`.**

**Reglas, en este orden:**

1. **`generation_target`.** El encuentro se generó para ese Decision Challenge.
   Lo ofrece.
2. **`declared`.** El caso congelado lo declara `yes` o `no`; si el caso no lo
   declara, cuenta lo que declara el **entorno de observación** congelado con
   el encuentro (ciclo 7, abajo).
3. **`transition_fallback`** (DF-12). Nadie lo revisó para este caso y se
   mantiene la regla anterior, rotulada: TD1, F1, C1, C3, C4 y C14 en todo
   encuentro, y un Decision Challenge solo en el encuentro generado para él.
4. **`objective_not_enabled`** y **`unknown_objective`.** Un objetivo reservado
   (C2, C15) o inexistente nunca es evaluable.

**Por qué esta transición.**

- **No quita ni agrega nada a un caso sin revisar.** Cada encuentro de ese
  caso conserva exactamente la elegibilidad que tenía. Es el mecanismo más
  conservador y reversible (§56).
- **Se retira caso por caso.** Cuando el docente aprueba la declaración de un
  caso, ese caso deja de usar la transición.

**Dónde está hoy (ciclo 7, 2026-09-28).**

- **C14 está declarado en los 31 casos:** 14 YES y 17 NO, con su procedencia
  (`reviewed`: `by`, `on`, `source`, `decision_group`, `version`). La tabla
  está en `docs/C14_TABLA_FINAL.md`. `acs_54m_inferior` es NO desde el ciclo 7
  (DF-20, revisión `C14-REVIEW-2`): la razón es sobre la oportunidad de
  observación, no sobre lo que el POCUS puede mostrar.
- **C4 es NO en todo el entorno de observación** (TDFC-7/8 y H4 del ciclo 7):
  - cada caso del banco lo declara, con su razón
    (`case_assessment_bank.C4_DECLARATIONS`);
  - el entorno lo declara una vez (`observation_opportunities.ENVIRONMENT`), y
    `evaluation_basis.freeze` copia esa declaración en todo encuentro nuevo:
    también en los casos generados y en los encuentros sin caso autorado
    (PS001), que no tienen declaración propia;
  - la declaración de un caso gana a la del entorno;
  - **es prospectiva:** un encuentro congelado antes no trae el bloque del
    entorno y conserva la transición con que empezó; una observación C4 ya
    confirmada no se pierde ni se relee. Por eso C4 sigue en
    `TRANSITION_OBJECTIVES`, aunque ningún encuentro nuevo llegue a esa regla;
  - el motor no se tocó; la evidencia C4 vendrá de simulación procedural u
    observación en el lugar de trabajo (`test_c4_is_not_observable_in_this_environment.py`).
- **TD1, F1, C1 y C3 siguen sin revisar en todos los casos** (TDFC aprobado
  conceptualmente, sin escribir). En los casos generados y en PS001, C14 y
  TD/F/C conservan la transición (DF-12, L-F07 B).
- **Las pruebas** están en `test_c14_opportunities.py`:
  - YES es evaluable y NO no lo es;
  - NOT REVIEWED conserva sólo la transición;
  - nada se observa sin el docente;
  - C14 incidental bajo otro objetivo;
  - los encuentros históricos y las declaraciones congeladas no cambian;
  - varios hallazgos de POCUS en un encuentro son una sola observación.

**La transición es TRANSITORIA** (decisión docente del 2026-09-28, DF-12). No
es la arquitectura final ni debe convertirse en una regla permanente.

- **Estado objetivo:** CASO → OPORTUNIDADES REVISADAS EXPLÍCITAMENTE → SOLO LAS
  OPORTUNIDADES REALES SON EVALUABLES.
- **Qué es la regla:** NOT REVIEWED → LEGACY FALLBACK es solo la estrategia
  para no perder oportunidades antes de que exista revisión clínica.
- **Orden de retiro:**
  - primero C14, el primer objetivo con el flujo BORRADOR → REVISIÓN CLÍNICA →
    METADATA APROBADA (DF-13);
  - después TD/F/C, objetivo por objetivo, a medida que se aprueben sus
    oportunidades.
- **Lo que no se hace:** no se retira ningún otro fallback de TD/F/C sin
  revisión clínica.
- **Cómo se retira en el código.** Hay dos caminos:
  - un caso con declaración aprobada deja de pasar por `transition_fallback`
    para ese objetivo;
  - cuando todos los casos de un objetivo estén revisados, el objetivo sale de
    `TRANSITION_OBJECTIVES`, y un caso no declarado deja entonces de ofrecerlo.

**Qué ven el docente y el brief.**

- El portal muestra al docente la nota de oportunidad (de dónde viene) y, si el
  caso la declara, la razón y la evidencia esperada «como guía».
- El brief de IA (prompt 1.6) recibe la oportunidad declarada como guía, nunca
  como prueba de que ocurrió.
- La evidencia esperada **no es una lista blanca**: el docente puede reconocer
  evidencia válida no prevista, rechazar lo que propone la IA o juzgar que la
  oportunidad no ocurrió.

**Observación incidental (D-6).** Un encuentro generado para un desafío puede
ofrecer otros objetivos que su caso declare. El modelo no supone un objetivo por
encuentro; el test lo cubre con R1-05 declarado en un caso de trauma.

## 4. Unidad de evidencia y procedencia (§58, §79)

**La unidad de evidencia es la observación confirmada:** una fila de
`mrs_progress_observations` por encuentro y objetivo. Una observación con seis
contribuciones sigue siendo **una** observación y se cuenta una vez; no se crean
observaciones duplicadas por vínculo.

**No hay tabla nueva.** Se agregó una columna anulable, `provenance_json`, con
migración para bases existentes. `NULL` se lee como legado: a las
observaciones anteriores no se les infiere nada.

```json
{
  "schema": "mrs.observation_provenance.v1",
  "evidence_source": "management_reasoning_simulator",
  "opportunity": {"objective_id": "R2-01", "version": "1.0", "state": "yes", "eligible": true,
                  "rule": "generation_target", "basis_status": "frozen", "case_id": "…",
                  "basis_fingerprint": "…", "declaration_source": "…", "note": "…"},
  "mapping_version": "1.1.0",
  "contributions": [
    {"framework": "ACGME", "code": "MK1", "contribution": "partial",
     "element": "Demonstrates scientific knowledge of complex presentations and conditions.",
     "component_observed": "Applying physiological knowledge of pressure, flow and perfusion…",
     "limitation": "MK1 describes scientific knowledge itself…",
     "evidence_condition": "…", "level_described": 2,
     "source_id": "acgme_em_2021", "source_version": "…", "pdf_page": 15, "source_url": "…#page=15"}
  ]
}
```

**Qué conserva cada observación nueva (§79).** Sin duplicar lo que ya tienen las
estructuras relacionadas:

- encuentro (`attempt_id`);
- caso y versión de la declaración (`case_id` y `basis_fingerprint`);
- objetivo;
- estado, regla y versión de la oportunidad;
- evidencia (`evidence_json`);
- confirmación docente (asesor, fecha y tabla de confirmaciones);
- por vínculo: tipo de contribución, componente, limitación, elemento del
  framework, y fuente, versión y página del mapping.

**Auditoría.** La auditoría de cada valoración registra el estado y la regla de
la oportunidad.

**Multisource (§107).**

- `attempt_id` es `NOT NULL`: hoy solo el simulador produce evidencia.
- Una fuente externa futura (observación directa, OSCE) necesitaría su propia
  tabla con el mismo formato de contribución y `evidence_source` propio.
- **No se implementó**; queda registrado en la cola de decisiones.

## 5. Contribución directa y parcial (DF-2)

**Qué significa cada tipo:**

- **`direct`**: la observación representa el elemento vinculado.
- **`partial`**: aporta evidencia válida sobre una parte identificable del
  elemento, y dice qué queda fuera. PARTIAL no es un defecto.

**Son etiquetas.** Ninguno es un puntaje, un peso ni un nivel, y nada cuenta uno
como la mitad del otro (`test_direct_and_partial_are_labels_never_weights`).

**Campos de cada vínculo:**

- `contribution`, `element`, `component_observed`, `limitation` y
  `evidence_condition`;
- **ACGME:** el nivel donde el comportamiento está descrito (`level_described`),
  sin asignar nivel a nadie;
- **Royal College:** la etapa y el hito de Pathway to Competence, parafraseados.
  `epa_context` nombra la EPA bajo la que la EPA Guide lista el hito, como
  contexto y **nunca** como contribución a esa EPA completa.

**Vínculos activos (versión de mapping 1.1.0):**

| Desafío | Vínculos |
|---|---|
| R1-03 | PC4 L3 directa · MK2 L4 parcial · ME 2.2 Foundations parcial (contexto F1 hito 3) |
| R1-04 | PC1 L3 directa · PC6 L3 parcial · ME 4.1 Foundations parcial (sin EPA: F2 contradice el contexto) |
| R2-01 | PC1 L3 directa · PC4 L3 directa · MK1 L2 parcial · MK2 L4 parcial · ME 1.6 Core directa ×2 (contexto C1 hito 1 en la primera) |

**Vínculos inactivos.** Los que existen textualmente pero cuya contribución no
se puede describir con claridad (§93) quedan documentados y **no activos**; ver
`VERIFICACION_MAPPINGS_FUNDACIONALES.md` §6. Los ocho Decision Challenges de
sesgo conservan sus vínculos sin cambios.

## 6. Construct coverage: qué queda disponible y qué no se construyó

**Qué queda disponible.** Por cada observación confirmada, el sistema guarda lo
necesario para calcular cobertura del constructo más adelante:

- qué parte de qué elemento se observó (`component_observed`), en qué
  framework, con qué fuente y versión;
- si fue directa o parcial, y qué quedó fuera;
- bajo qué oportunidad y en qué encuentro, con qué evidencia y quién la
  confirmó.

**Qué no se construyó (§52).** Ningún algoritmo de cobertura:

- ni porcentaje ni puntaje;
- ni semáforo ni «completo/incompleto»;
- ni umbral ni ponderación temporal;
- ninguna determinación de competencia o entrustment.

Tampoco un motor de competencias ni un servicio de ontología (§82 y §94).

## 7. Compatibilidad hacia atrás (§78)

- **Registros legados sin copia congelada, o con copia anterior a las
  oportunidades:** reciben la regla de transición, es decir, la elegibilidad
  que ya tenían, y nunca las declaraciones actuales.
- **Observaciones anteriores:** `provenance` es `NULL` (legacy) y se muestran
  como antes.
- **Briefs guardados:** un brief de prompt ≤ 1.5 se sigue leyendo con la lista
  de objetivos contra la que se escribió. `_OBJECTIVE_SINCE` excluye R1-03,
  R1-04 y R2-01 de esas versiones.
- **Esquema:** la columna nueva se agrega con `ALTER TABLE` si falta, en SQLite
  y en PostgreSQL. El test de migración parte de una base con el esquema
  anterior.

## 8. Qué queda para decisión docente

Detalle en `docs/COLA_DECISIONES_AI_ADVISOR.md`:

- C14 en `acs_54m_inferior`, después de decidir sus datos (las otras 30 filas se
  activaron en el ciclo 5);
- la revisión de TD1, F1, C1, C3 y C4, objetivo por objetivo;
- los vínculos PARTIAL inactivos;
- el *faculty override*: registrar explícitamente que una oportunidad declarada
  no ocurrió. **No implementado**; hoy el docente simplemente no valora;
- una fuente de evidencia externa.
