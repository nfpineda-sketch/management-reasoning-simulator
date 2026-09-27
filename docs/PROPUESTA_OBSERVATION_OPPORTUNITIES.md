# Propuesta · Observation opportunities como entidad explícita

Ciclo 1 del AI Advisor, punto 4 de la aprobación docente del 2026-09-27.

**Estado: PROPUESTA PARA APROBACIÓN.** Nada de esto está implementado. No hay
lógica específica para C14, ni cambios de elegibilidad, mappings, scoring,
Objective Progress o UX.

Principio pedido por el docente:

```
CASE / ENCOUNTER
→ DECLARED OBSERVATION OPPORTUNITIES
→ ACTUAL RESIDENT PERFORMANCE
→ AI-PROPOSED OBSERVATION
→ FACULTY CONFIRMATION
→ LONGITUDINAL EVIDENCE
```

Referencias del charter: §8, §10, §63, §96, §97, §98 y §99.

## 1. Estado actual, etapa por etapa (KNOWN)

| Etapa | Qué existe hoy | Vacío |
|---|---|---|
| Oportunidad declarada | D1–D5 se declaran por caso con una oportunidad y lo que requiere (`case_assessment_bank.py`); se verifican contra el caso (`case_assessment.verify`) y se congelan al iniciar el encuentro (`evaluation_basis.freeze`) | Los objetivos TD1, F1, C1, C3, C4 y C14 no tienen oportunidad declarada: `objective_is_eligible` devuelve verdadero siempre (`competency_mapping.py:259`) |
| Desempeño real | El Management Trace | — |
| Observación propuesta por IA | El brief docente ya emite una propuesta por objetivo elegible: satisfactory, needs_improvement o insufficient_evidence, con evidence_refs, profundidad y autonomía (`faculty_analysis._analysis_schema`) | Propone también sobre objetivos sin oportunidad real. «insufficient_evidence» mezcla «no hubo oportunidad» con «hubo y no se tomó» (§63) |
| Confirmación docente | `progress_store.assess` exige evidencia citada del encuentro, profundidad y autonomía; el portal muestra sólo objetivos elegibles | Como todo TD/F/C es elegible, el docente ve objetivos que el caso no permitía observar (el ejemplo de C3 de la §10) |
| Evidencia longitudinal | Una fila por observación, con auditoría y sin agregación por código | — |

Los Decision Challenges (R*) ya tienen su forma de oportunidad: el encuentro se
generó para ese desafío (`record_challenge_id == objective_id`). Eso cubre el
«generation target» de la §97, pero no las observaciones incidentales de la §98.

## 2. Propuesta: reutilizar `case_assessment` y `evaluation_basis`, sin sistema paralelo

Se agrega un bloque `objectives` a la declaración de cada caso, al lado de
`domains` y con la misma forma. La misma maquinaria que hoy hace confiables las
oportunidades D1–D5 las hace confiables para los objetivos.

```python
CASES["<case_id>"] = {
    "domains": {...},            # D1–D5, como hoy
    "critical_events": [...],    # como hoy
    "objectives": {              # NUEVO: oportunidades de observación por objetivo
        "<objective_id>": {
            "opportunity": "Qué situación del caso permite observar este objetivo",
            "expected":   ["Conducta observable 1", "..."],
            "window_min": (desde, hasta),
            "requires":   {"studies": [...], "actions": [...], "examination": [...]},
            "evidence":   {"any_of": ["diagnostic:pocus", "action:..."]},   # opcional, ver 2.4
        },
    },
}
```

### 2.1 Verificar

`case_assessment.verify` recorre `objectives` con el mismo código que hoy
recorre `domains`. Comprueba que:

- el objetivo existe en `OBJECTIVES` y está `supported`;
- la oportunidad y lo esperado no están vacíos;
- la ventana es un intervalo válido;
- cada estudio pedido está entre las investigaciones del caso;
- cada acción es una que el motor ejecuta;
- cada región de examen está escrita en el caso.

Una declaración inalcanzable es un defecto de la declaración, nunca un objetivo
que el residente no cumplió. Ése es el principio que el módulo ya escribe para
D1–D5.

### 2.2 Congelar y versionar

- `evaluation_basis.freeze` ya copia la declaración completa del caso, con su
  huella, al iniciar cada encuentro. El bloque nuevo queda congelado sin código
  adicional.
- Se sube `COVERAGE_VERSION` (1.1 → 1.2), por la §66.
- Un cambio posterior en una declaración no cambia cómo se juzga un encuentro
  anterior (§75).

### 2.3 Elegibilidad

`objective_is_eligible(objective_id, record)` pasa a leer la base congelada del
encuentro:

- **Objetivos con oportunidad declarable (TD/F/C):** elegible sólo si la base del
  encuentro es legible (`evaluation_basis.READABLE`) y declara ese objetivo. Si
  no lo declara, el objetivo no aparece para calificar: es NO OBSERVABLE, no un
  cero (§96).
- **Decision Challenges:**
  - la regla actual se mantiene («el encuentro se generó para este desafío»);
  - en una segunda fase, un caso podría declarar también oportunidades
    incidentales de otro desafío (§98), que pasarían por la misma verificación.

El portal docente y el brief ya filtran por `objective_is_eligible`. El efecto
llega a ambos sin tocar su lógica.

### 2.4 Evidencia citada coherente con la oportunidad (opcional)

Hoy `objective_evidence_is_eligible` exige una decisión registrada sólo para los
Decision Challenges. La propuesta es que cada oportunidad pueda nombrar, en
`evidence.any_of`, qué tipo de elemento del Trace debe citar el docente para
confirmar.

- **Ejemplo:** para C14, la solicitud o la lectura del POCUS y una decisión
  posterior.
- **Qué no hace:** no evalúa calidad ni decide si el resultado fue satisfactorio.
  Sólo evita confirmar C14 citando una evidencia que no tiene relación con el
  POCUS.

### 2.5 Propuesta de la IA

- El brief recibe, por objetivo elegible, el texto de la oportunidad declarada y
  lo esperado, como hoy recibe el contexto de los dominios.
- «insufficient_evidence» queda reservado para «hubo oportunidad y la evidencia
  no alcanza» (§63).
- Es una versión nueva del prompt: los briefs guardados se siguen leyendo con su
  versión (§66).
- **Costo (INFERRED):** baja. Hoy el brief escribe una entrada por cada objetivo
  elegible, 6 o 7 en todo encuentro; con oportunidades declaradas escribe
  sólo las del caso.

### 2.6 Confirmación docente y evidencia longitudinal

- **Sin cambio de esquema:** cada observación ya guarda `attempt_id`, y la base
  congelada de ese intento contiene la oportunidad declarada y su huella. La
  cadena «observación → encuentro → oportunidad → evidencia → docente» queda
  trazable (§64, §67).
- **Cambio visible mínimo:** mostrar al docente el texto de la oportunidad
  declarada al lado del objetivo.
- **Oportunidades que dependen de la trayectoria:** el docente puede no registrar
  nada si la oportunidad declarada no llegó a materializarse en ese encuentro.
  - Ejemplo: sólo si el paciente se deteriora.
  - Registrar «no demostrado» queda reservado a una oportunidad que existió
    (§63).

## 3. C14 como prueba conceptual, sin lógica ad hoc

- **Por qué no basta una regla de disponibilidad.** Los 31 casos del banco traen
  POCUS (KNOWN). La regla «hay POCUS ⇒ C14 elegible» reproduciría exactamente el
  problema actual: C14 sería elegible en todos los casos.
- **Qué define la oportunidad de C14.** Que el POCUS de ese caso discrimine una
  decisión de manejo. Por ejemplo:
  - una VCI plana y un VI hiperdinámico frente a un VI hipocontráctil, que
    decide fluidos o vasopresor;
  - una vena llena y congestión, que decide no dar volumen.
  - Es un juicio clínico por caso: se escribe en `opportunity` y lo aprueba un
    docente.
- **Qué verifica el código.**
  - Que `requires.studies` contenga `pocus` y que el caso lo traiga.
  - Opcionalmente, que la evidencia citada incluya el POCUS y una decisión
    posterior.
  - El código no decide si el POCUS era relevante.
- **Resultado esperado.** C14 aparece para calificar sólo en los casos cuya
  declaración aprobada lo diga. En los demás no aparece, y su ausencia no es
  evidencia negativa.

El mismo mecanismo, sin cambiar una línea, sirve para C3 (hay un problema de vía
aérea o ventilación en el caso), C4 (hay una sedación o analgesia
procedimental), TD1, F1 y C1.

## 4. Generalización

| Objetivos | Cómo se declara su oportunidad |
|---|---|
| TD1, F1, C1, C3, C4, C14 | Bloque `objectives` del caso, verificado y congelado |
| C2 y C15 (hoy deshabilitados) | Habilitarlos = `supported: True` + declararlos sólo en los casos que los ofrecen. Así C2 no aparecería en un caso de asma. Es una decisión clínica: `docs/AUDITORIA_OPORTUNIDAD_C2.md` |
| Decision Challenges (R*) | Objetivo de generación: la regla actual. Incidentales: declaración en el caso (fase 2) |
| R1-03, R1-04, R2-01 | Igual que los R*, una vez verificados sus mappings (DF-2, DF-3) |
| D1–D5 | Ya funcionan así; la propuesta unifica el vocabulario |
| Casos generados por IA | Sin declaración previa: ningún TD/F/C elegible (falla cerrada). Que el generador declare y verifique oportunidades sería una fase posterior |

## 5. Alternativas consideradas

- **(a) Recomendada: extender las declaraciones del caso.** Reutiliza la
  verificación, el congelamiento, la huella, el versionado y los estados de
  `evaluation_basis`. No agrega tablas ni flujos.
- **(b) Registro paralelo de oportunidades** (módulo o tabla propios).
  - Duplica congelamiento, versiones y auditoría.
  - Dos fuentes de verdad sobre qué ofrece un caso.
  - Descartada (§53, §54).
- **(c) Heurística sobre el Trace** (por ejemplo, «pidió POCUS ⇒ C14 elegible»).
  - Barata, pero confunde oportunidad con desempeño: el residente que no pidió
    POCUS donde debía quedaría «sin oportunidad» en vez de «oportunidad no
    tomada» (§63).
  - Útil sólo como aviso de consistencia, nunca como regla.
- **(d) La IA decide la oportunidad al analizar.**
  - Rompe «la oportunidad precede a la evaluación» (§43.5) y agrega costo.
  - Descartada.

## 6. Preguntas de la §54

- **Qué resuelve:** que un objetivo sólo pueda acreditarse donde el caso
  permitía observarlo (§10).
- **Por qué el sistema actual no alcanza:** la elegibilidad de TD/F/C es una lista
  fija sin relación con el caso.
- **Valor esperado:** evidencia longitudinal válida y menos ruido para el
  docente y para la IA.
- **Costo de implementación:** mecanismo medio (una sesión, con tests
  focalizados).
- **Costo continuo:** redactar y aprobar declaraciones por caso. Es el costo
  dominante y es clínico.
- **Complejidad agregada:** un bloque más en una estructura existente.
- **Qué se simplifica:** desaparecen la lista fija de `objective_is_eligible` y
  las propuestas de IA sobre objetivos sin oportunidad.

## 7. Riesgos

- **Encuentros históricos.** Tienen base `legacy` o `frozen` sin bloque
  `objectives`. Decidir qué pasa con ellos es una decisión explícita (§75); ver
  D-3.
- **Declaraciones incompletas.** Un objetivo real queda sin declarar y no se
  puede observar.
  - Mitigación: la matriz de cobertura (`case_assessment.matrix`) muestra qué
    casos declaran qué objetivos.
  - Un objetivo sin ningún caso que lo declare es visible como tal.
- **Carga docente.** 31 casos × 6 objetivos. Mitigación: piloto con C14 y
  aprobación por lotes.
- **Sin reglas de unicidad (restricción del docente).** Un mismo encuentro puede
  ofrecer varios objetivos, y un mismo evento del Trace puede sustentar
  observaciones de objetivos distintos. Eso es evidencia convergente, no doble
  conteo (§12).
  - La propuesta no agrega ninguna regla de unicidad.
  - Tampoco agrega puntaje agregado por EPA o Milestone.

## 8. Decisiones necesarias

- **D-1.** ¿Se aprueba el mecanismo (a), extender las declaraciones del caso,
  como base de DF-1?
- **D-2.** ¿Qué significa que un caso no declare un objetivo?
  - Recomendado: «no ofrece oportunidad» (falla cerrada), con la matriz de
    cobertura como control.
  - Alternativa: exigir un sí o no explícito por objetivo y caso.
- **D-3.** ¿Qué pasa con los encuentros anteriores sin declaración?
  - Recomendado: conservar sin cambios las observaciones existentes y, para
    evaluaciones nuevas de esos encuentros, mantener la regla actual marcada como
    «oportunidad no declarada».
  - Alternativa: no permitir observaciones TD/F/C nuevas en ellos.
- **D-4.** ¿Se exige que la evidencia citada incluya el elemento que define la
  oportunidad (2.4)?
- **D-5.** Piloto:
  - ¿Quién redacta y quién aprueba las declaraciones?
  - Propuesta: el AI Advisor redacta borradores de C14 para un lote de casos,
    que un docente revisa y aprueba antes de usarse.
  - Es trabajo clínico: CLINICAL REVIEW.
- **D-6.** Fase 2: ¿se habilitan observaciones incidentales de Decision
  Challenges (§98) con el mismo mecanismo?
