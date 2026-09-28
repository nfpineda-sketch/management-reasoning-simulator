# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** lo que requiere una decisión del docente, más el estado de
  lo ya decidido.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-09-28, al abrir el ciclo 4 con las decisiones docentes
  de ese día (sección «Decisiones del 2026-09-28»).

## Pendientes de decisión

| ID | Clase | Tema | Estado |
|---|---|---|---|
| DF-13 | HIGH VALUE · CLINICAL REVIEW | Activar C14 caso por caso | **No activar todavía** · el ciclo 4 prepara A–H para una decisión rápida |
| DF-15 | HIGH VALUE · METHODOLOGICAL REVIEW | Piloto del validation corpus, Fase 1 | **Aprobado con modificaciones** · el ciclo 4 lo deja listo para distribuir |
| DF-16 | HIGH (2) · MEDIUM (2) · LOW | Defectos del lector encontrados en el ciclo 3 | **a y b autorizados** para el ciclo 4 · el resto se documenta |
| DF-14 | METHODOLOGICAL REVIEW | Vínculos PARTIAL inactivos de R1-03, R1-04 y R2-01 | **Confirmado: siguen inactivos** · documentados para revisión posterior |
| DF-12 | STRUCTURAL | Regla de transición para objetivos NOT REVIEWED | **Aprobada como transitoria**, no permanente |
| DF-17 | METHODOLOGICAL REVIEW | *Faculty override*: registrar que una oportunidad no ocurrió | **DEFERRED:** se diseña después del piloto C14 |
| DF-4 | CLINICAL + METHODOLOGICAL REVIEW | C2 y los casos trauma | C2 deshabilitada · se revisa cuando haya un banco de trauma más amplio |
| DF-18 | LOW PRIORITY | Evidencia de fuentes externas (multisource) | Registrado · sin acción |
| DF-9 | METHODOLOGICAL REVIEW | −3, doble efecto de safety y varios eventos por una conducta | Registrado · sin decisión ahora |
| DF-11 | LOW PRIORITY | Residuos menores de la lectura | Registrado |
| DF-5 | — | C15 | Deshabilitada, sin acción |

## Decisiones del 2026-09-28 (apertura del ciclo 4)

- **DF-12 · aprobada como regla TRANSITORIA.**
  - Mientras un caso u objetivo siga NOT REVIEWED, conserva el comportamiento
    previo para no perder oportunidades antes de la revisión clínica.
  - **No es la arquitectura final.** El estado objetivo es: CASO → OPORTUNIDADES
    REVISADAS EXPLÍCITAMENTE → SOLO LAS OPORTUNIDADES REALES SON EVALUABLES.
  - El fallback se retira progresivamente: C14 primero y después TD/F/C, a
    medida que se aprueben sus oportunidades. No se retiran otros fallbacks sin
    revisión clínica.
- **DF-14 · confirmado.**
  - Los 9 vínculos PARTIAL siguen inactivos y documentados para revisión
    posterior.
  - PARTIAL IS NOT A DEFECT: los PARTIAL activos y defendibles siguen activos.
  - Se prioriza lo significativo, interpretable y trazable sobre la cobertura
    máxima.
- **DF-16 · a y b autorizados para el ciclo 4**, por clase, EN/ES, con frases
  nuevas y BEFORE/AFTER.
  - Los residuos MEDIUM/LOW se corrigen solo si son deterministas, pequeños, de
    bajo riesgo y del mismo mecanismo: vía compartida, listas de órdenes,
    variantes comunes.
  - Los independientes («si» = «whether», texto tomado como respuesta,
    traducciones, «OK to discharge») se documentan primero. Si alguno resulta de
    alto valor y barato, se propone para el ciclo 5.
- **DF-13 · C14 no se activa todavía**, ni siquiera los 6 YES y 6 NO claros.
  - El ciclo 4 prepara las decisiones A–H agrupadas y puede mejorar el borrador.
  - C14 es el primer objetivo con el flujo: BORRADOR DEL AI ADVISOR → REVISIÓN
    CLÍNICA HUMANA → METADATA APROBADA.
- **DF-17 · DEFERRED / DESIGN AFTER C14 PILOT.**
  - Debe seguir siendo posible que el docente indique que la oportunidad
    declarada no ocurrió, o que reconozca una observación incidental.
  - No se agrega interfaz ni lógica.
- **DF-4 · C2 sigue deshabilitada.** No se fija un número artificial de casos;
  se revisa con un banco de trauma más amplio. No se trabaja en C2 en el ciclo 4.
- **DF-15 · piloto aprobado con modificaciones.**
  - 6 médicos de urgencia × 3 casos, unos 18 documentos. Cada idioma, escrito
    por quien lo escribe naturalmente; no se traduce.
  - Los seis casos propuestos.
  - Instrucción breve, alineada con la guía del residente: interpretación,
    acción, expectativa y reevaluación, en texto libre y sin cajas obligatorias.
  - **VC-1:** aprobado. Dejar listos los 18 documentos; el docente recluta y
    distribuye.
  - **VC-2:** anotación primaria por un clínico, 20 % doble por un segundo
    clínico, y desacuerdo por un tercero o por consenso explícito.
  - **VC-3:** las indicaciones de regreso son FOLLOW-UP / DISPOSITION SAFETY
    PLAN. Cuentan como contingencia solo si traen una condición explícita que
    modifica el plan.
  - **VC-4:** revisar de nuevo los textos en español y verificar los DOCX
    estructuralmente. La verificación visual en Word la hace el docente.
  - **Split development/sealed:** no se sortea antes de que vuelvan los
    documentos; el ciclo 4 define el procedimiento, reproducible y auditable.

## Decidido e implementado

| ID | Tema | Estado al cerrar el ciclo 3 |
|---|---|---|
| DF-1 | Observation opportunities (D-1 a D-6) | **Implementado y testeado.** C14 no activado: pasa a DF-13 |
| DF-2 | R1-03, R1-04 y R2-01 con contribución DIRECT/PARTIAL | **Implementado y testeado.** PARTIAL inactivos en DF-14 |
| DF-6 | Validation corpus | **Diseño cambiado por el docente** (Fase 1 en Word) · herramienta implementada · piloto en DF-15 |
| DF-10 | Seguimiento pegado al alta, EN/ES | **Implementado y testeado** |
| DOC-1 | §51 del charter | **Cerrado:** termina en «…del desempeño del residente.» |
| DF-7 | Fidelidad del razonamiento en el Management Trace | Cerrado en el ciclo 2 |
| DF-3 | MK1 | Cerrado; se usa como PARTIAL en R2-01 |

---

## Pendientes

### [HIGH VALUE · CLINICAL REVIEW] DF-13 · Activar C14 caso por caso

**PROBLEM**

C14 sigue observable en todo encuentro por la regla de transición (DF-12).
Ningún caso del banco declara todavía su oportunidad.

**EVIDENCE**

`docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md`:

- **Filas del borrador:** 31 casos: 6 YES, 6 NO y 19 UNCERTAIN.
- **Qué trae cada fila:** racional, componente observable, evidencia esperable
  y nota de revisión.
- **Las 19 dudas:** se reducen a 8 preguntas (A–H), más una verificación
  técnica en `bradycardia_avb3_78f`.

**RECOMMENDATION**

1. Responder A–H.
2. Aprobar, modificar o rechazar fila por fila.
3. El AI Advisor escribe en el bloque `objectives` sólo lo aprobado, con quién
   lo revisó y cuándo.

**ALTERNATIVES**

- Activar sólo las 12 filas YES/NO ya claras y dejar las UNCERTAIN en
  transición.
- Mantener la transición completa.

**COST / EFFORT**

- **Docente:** minutos por caso.
- **AI Advisor:** una sesión corta para escribir y verificar.

**RISK**

- Un YES sin oportunidad real haría evaluable algo que el caso no ofrece.
- Un NO erróneo quitaría una oportunidad.
- Ambos riesgos se acotan a encuentros nuevos: la declaración se congela.

**DECISION NEEDED**

- Respuestas a A–H.
- Aprobación de las filas.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-15 · Piloto del validation corpus, Fase 1

**PROBLEM**

Hace falta lenguaje clínico auténtico, independiente del lector, para medir su
generalización (DF-6 modificado por el docente).

**EVIDENCE**

`docs/VALIDATION_CORPUS_FASE1.md`:

- plantilla Word ES/EN: 12 documentos del piloto en `validation/plantillas_v1/`;
- ingesta DOCX determinista por la página real;
- anotación ciega, adjudicación, clases y métricas;
- 25 tests;
- una corrida sintética de punta a punta.

**RECOMMENDATION** (piloto, §96)

- **Médicos y casos:**
  - 6 médicos en español, en 3 pares;
  - 3 casos cada uno, de C01–C06;
  - 45–60 min por médico;
  - 18 documentos, unas 150–270 entradas.
- **Inglés:** sólo con médicos que escriban naturalmente en inglés.
- **Subconjuntos:**
  - development y sealed 50/50 por médico;
  - sorteo dentro de cada par, después de recibir y antes de leer.
- **Anotación:**
  - ciega, antes de correr el motor;
  - doble en el 20 %;
  - adjudicación con propuesta determinista.

**ALTERNATIVES**

- Todo el piloto como development, sellando recién en la fase siguiente: más
  datos para diagnosticar y ninguna medición de generalización.
- 4 médicos: menos carga y menos variabilidad.

**COST / EFFORT**

- **Médicos:** unas 5–6 h en total.
- **Custodio:** 1,5–2 h.
- **Anotación:** 3–4,5 h, más ~1 h de doble anotación.
- **Adjudicación:** ~1–1,5 h por subconjunto.
- **IA:** US$0.

**RISK**

- **Texto del caso en español:** no confirmado aprobado.
- **Word real:** sin probar; se validó con python-docx, no con Word.
- **n chico:** las métricas del piloto son descriptivas.

**DECISION NEEDED**

- **VC-1.** ¿Aprueba el piloto (médicos, casos, pares, sorteo, inglés)?
- **VC-2.** ¿Quién anota y quién adjudica? Recomendación: un clínico que no
  dirija las correcciones del lector.
- **VC-3.** ¿Las indicaciones de regreso al alta cuentan como contingencia o
  como seguimiento? La guía propone seguimiento, por coherencia con DF-10.
- **VC-4.** Confirmar la aprobación del texto en español de los seis casos y
  abrir un documento en Word antes de enviarlo.

El AI Advisor no contacta a nadie ni envía nada (§97).

---

### [HIGH · MEDIUM · LOW] DF-16 · Defectos del lector encontrados en el ciclo 3

**PROBLEM**

Al probar DF-10 y la ingesta del validation corpus con frases sintéticas
escritas para las pruebas (no del corpus), aparecieron defectos distintos de los
autorizados. Por control de alcance se registran y no se corrigen (§63).

**EVIDENCE**

Cada fila se reprodujo con `parse_family_actions` o por la página real.

| # | Prioridad | Defecto | Ejemplo sintético |
|---|---|---|---|
| a | **HIGH** | Una lista de preparación pierde miembros según cómo empiece | «Monitor, vía venosa y oxígeno por mascarilla a 8 L/min» → sólo acceso venoso; sin «Monitor,» → sólo oxígeno |
| b | **HIGH** | Una cláusula de repetición condicional vuelve condicional la orden entera, y la orden queda como modelo de trabajo | «Salbutamol 5 mg + ipratropio 0.5 mg nebulizados ahora, repetir cada 20 minutos por 3 veces si persiste…» → nada se ejecuta ahora |
| c | MEDIUM | «nebulizados» (masculino plural) no se lee como vía; una vía compartida al final de una lista queda sólo en el último fármaco | «salbutamol + ipratropio … nbz» → salbutamol sin vía; se pide aclaración |
| d | MEDIUM | Un texto escrito con una aclaración pendiente se toma como su respuesta: la orden que trae no se ejecuta y su vía se asigna a la orden retenida | Aclaración de vía pendiente + «Hidrocortisona 200 mg ev» → salbutamol «IV», que se vuelve a rechazar; la hidrocortisona no se ordena |
| e | LOW | «si» como «whether» se lee como condicional | «reevaluar … si puede hablar frases completas» → plan condicional |
| f | MEDIUM | «OK to discharge with…» no se reconoce como alta | Registrado en DF-10 |
| g | MEDIUM | Una receta unida al alta con «with/con» se pierde | «con paracetamol», «with ibuprofen» |
| h | LOW | «con hora en policlínico» no se lee como cita | — |
| i | LOW | Cuatro líneas del mensaje de la orden retenida sin traducción | «I recognised…», «Still to state…», «In your own words…», «What you already wrote is kept.» |

**Qué no es un defecto.** Oxígeno sin flujo absoluto («O2 por mascarilla para
saturar sobre 94 %») se retiene por diseño. El piloto medirá si los clínicos lo
consideran una aclaración innecesaria.

**RECOMMENDATION**

- **a y b:** corregir por clase en el ciclo 4, con pruebas de frases nuevas.
  Ninguno viene del corpus, así que corregirlos no lo contamina.
- **d:** revisarlo junto con la Fase 2, porque es interacción en vivo.
- **Resto:** según capacidad.

**ALTERNATIVES**

- Esperar al piloto para dimensionarlos. Así el piloto mide un motor con
  defectos ya conocidos.

**COST / EFFORT**

- a y b: una sesión cada uno.
- c, e, f, g y h: horas.
- i: minutos.

**RISK**

- Tocar el lector compartido: se mitiga con regresiones, el corpus de ensayo
  EN/ES y la suite completa.

**DECISION NEEDED**

¿Autoriza corregir a y b, y cuáles más, en el ciclo 4?

---

### [METHODOLOGICAL REVIEW] DF-14 · Vínculos PARTIAL inactivos

**PROBLEM**

La verificación del ciclo 2 encontró vínculos textuales cuya contribución no se
puede describir con claridad. Por la regla de §93 no se activaron.

**EVIDENCE**

`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md` §6 lista 9 inactivos:

- **R1-03:** PC5 L3, ME 2.2 vía TD1 h8, ME 2.4.
- **R1-04:** PC6 L1/L4, ME 4.1 vía TP6 h4 y C1 h6, ME 2.4.
- **R2-01:** PC1 L3 (segunda oración), MK1 L3, ME 2.4.

Cada uno trae el motivo.

**RECOMMENDATION**

Mantenerlos inactivos. Activar alguno sólo si el docente puede enunciar el
componente observado y lo que queda fuera.

**ALTERNATIVES**

- Activar PC5 en R1-03 como PARTIAL condicionado a que la prioridad sea un
  fármaco. Exigiría una condición por encuentro que hoy no existe.

**COST / EFFORT**

- Revisión docente: minutos.
- Activar uno: una línea de datos y su test.

**RISK**

Evidencia más débil presentada como contribución.

**DECISION NEEDED**

¿Se mantienen inactivos?

---

### [STRUCTURAL] DF-12 · Regla de transición para objetivos NOT REVIEWED

**Qué se implementó** (§56, el mecanismo más conservador y reversible):

- Un objetivo sin declaración en un caso conserva la regla anterior, rotulada
  `transition_fallback`: TD1, F1, C1, C3, C4 y C14 en todo encuentro, y un
  Decision Challenge sólo en el encuentro generado para él.
- NOT REVIEWED nunca es NO.
- Los registros legados reciben la misma regla y nunca las declaraciones
  actuales.

**Evidencia:**

- `observation_opportunities.py`;
- `test_observation_opportunities.py` (19 tests);
- `docs/OBSERVATION_OPPORTUNITIES.md` §3.

**Efecto hoy:** ninguno sobre la elegibilidad, porque ningún caso declara
todavía.

**Cómo se retira:** caso por caso, al aprobar su declaración (DF-13).

**DECISION NEEDED:** confirmar la regla. Alternativa: cerrar C14 a los casos
no revisados, lo que quitaría oportunidades antes de revisarlas.

---

### [METHODOLOGICAL REVIEW] DF-17 · *Faculty override*: registrar que una oportunidad no ocurrió

**Hoy:**

- La evidencia esperable es guía, no lista blanca.
- El docente puede reconocer evidencia no prevista o simplemente no valorar.
- No hay un registro explícito de «la oportunidad declarada no ocurrió en este
  encuentro».

**No se implementó.** No hacía falta para el piloto (§ «no implementes
mecanismos complejos de override»).

**RECOMMENDATION:** esperar a que la activación de C14 muestre si hace falta.
Si hace falta, el diseño mínimo es un desenlace de valoración «oportunidad no
ocurrida», con motivo y auditado, que no cuente como observación.

**DECISION NEEDED:** ¿se necesita, y cuándo?

---

### [CLINICAL + METHODOLOGICAL REVIEW] DF-4 · C2

- **Sin cambios en el ciclo 3.** C2 sigue deshabilitada (`objective_not_enabled`
  en la resolución de oportunidades).
- **Evidencia:**
  - `docs/AUDITORIA_OPORTUNIDAD_C2.md`;
  - EPA Guide v1.1, p. 20: C2 pide variedad, incluido el trauma penetrante,
    el entorno clínico y los casos pediátricos;
  - el banco tiene 2 casos adultos.
- **RECOMMENDATION:** mantenerla deshabilitada. Si se habilita, que sea caso por
  caso mediante declaraciones de oportunidad.
- **DECISION NEEDED:** ¿qué amplitud de casos trauma consideraría suficiente? Es
  una decisión clínica; el AI Advisor no propone un número.

---

### [LOW PRIORITY] DF-18 · Evidencia de fuentes externas (multisource)

- **Por qué hoy no cabe:** la unidad de evidencia es una fila de
  `mrs_progress_observations`, con `attempt_id NOT NULL`. Sólo el simulador
  produce evidencia (`evidence_source: management_reasoning_simulator`).
- **Qué haría falta:** otra fuente (observación directa, OSCE) necesitaría su
  propia tabla con el mismo formato de contribución y su propio
  `evidence_source`.
- **No se implementó** (fuera de alcance, §52).
- **DECISION NEEDED:** ninguna ahora.

---

### [METHODOLOGICAL REVIEW] DF-9 · Penalidad −3, doble efecto de safety y varios eventos por una conducta

- **Se mantiene sin cambios** (charter §19 a §22 y §47):
  `max(0, base − 3 × eventos confirmados)`, el doble efecto sobre D3 y el total,
  y la acumulación de eventos.
- **Los eventos críticos siguen siendo una señal independiente.**
- **DECISION NEEDED:** ninguna ahora.

---

### [LOW PRIORITY] DF-11 · Residuos menores de la lectura

- **«since» en inglés.** No se lee como razón, porque también es temporal.
- **En inglés, «and I will».** «to reduce the congestion and I will recheck…»
  registra «and I will» dentro de la expectativa.
- **Hiperkalemia.** «Hyperkalemia with peaked T waves» e «Hiperkalemia con T
  picudas» no se leen como modelo: el vocabulario de hallazgos es cerrado.
- **Ortografía corregida en las citas.** «rythm» → «rhythm» y «urianalysis» →
  «urinalysis»; lo fijan las regresiones v0814 y v0816.
- **Guion 5, decisión 9.** «por» en español no se lee como causal.
- **`objectives.TARGET_SOURCE`.** Cita las páginas de la edición v1.0 de la EPA
  Guide.
- Los defectos nuevos del ciclo 3 están en DF-16.
- **DECISION NEEDED:** ninguna urgente.

---

### DF-5 · C15

Deshabilitada, sin cambios. No hay encuentros diseñados para cuidados al final
de la vida.

---

## Decidido en el ciclo 3 · registro

### DF-1 · Observation opportunities · IMPLEMENTADO

**Decisiones D-1 a D-6, como se aprobaron:**

- el bloque `objectives` en la declaración del caso;
- tres estados (YES / NO+RAZÓN / NOT REVIEWED);
- congelado con el encuentro;
- evidencia esperable como guía;
- borrador de C14 para revisión docente;
- observaciones incidentales posibles.

**Detalle:** `docs/OBSERVATION_OPPORTUNITIES.md`.

**Tests:**

- 19 en `test_observation_opportunities.py`;
- 15 en `test_foundation_challenges_as_objectives.py`;
- tests previos actualizados donde la especificación aprobada cambia la regla,
  con comentario.

### DF-2 · R1-03, R1-04 y R2-01 · IMPLEMENTADO

- **Vínculos:** 12 activos, cada uno con tipo, componente observado, lo que queda
  fuera, fuente, versión y página.
- **Etiquetas:** DIRECT y PARTIAL son etiquetas, no pesos.
- **Unidad de evidencia:** una observación confirmada, con sus contribuciones en
  la columna nueva `provenance_json`. No hay tabla nueva.
- **Automatismo:** el encuentro generado para el desafío es oportunidad, no
  evidencia.
- **Brief:** prompt 1.6. Los briefs anteriores conservan su lista de objetivos.
- **Inactivos:** en DF-14.

### DF-6 · Validation corpus · DISEÑO CAMBIADO E IMPLEMENTADO

- **Diseño:** el docente reemplazó las 240 frases por la Fase 1: médicos que
  escriben en Word a partir de casos.
- **Implementado:**
  - plantilla;
  - ingesta DOCX determinista por la página real, sin parser paralelo;
  - hojas de anotación y adjudicación;
  - métricas y trazabilidad;
  - guarda del sellado fuera del repositorio;
  - versionado y procedencia.
- **Complejidad de la ingesta:** no resultó mayor que lo previsto. El único
  hallazgo fue que el harness del ensayo resolvía una sola retención por paso.
  Se agregó `resolve_until_clear`, opcional; los 20 guiones no cambian.
- **Piloto:** en DF-15.

### DF-10 · Seguimiento pegado al alta · IMPLEMENTADO

- **Resultado:**
  - el seguimiento se conserva en EN y ES;
  - también las indicaciones de regreso;
  - el alta se ejecuta;
  - sin duplicarse, en el orden del texto y sin aclaraciones nuevas.
- **Antes/después:** de 10 altas con plan, el seguimiento se perdía en 7 y ahora
  se conserva en 9. La décima («OK to discharge») es otro defecto (DF-16 f).
- **Tests:** 17 nuevos.
- **Detalle:** `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, «Ciclo 3».
- **Test en rojo que se pasó por alto:** un test del ensayo esperaba el orden
  anterior del plan. Llegó en rojo al commit `9d35b00`, ya empujado. Se corrigió
  en `e54b919`, porque la secuencia aprobada es la del texto.

### DOC-1 · §51 · CERRADO

Se completó sólo con «residente.». Ningún otro bloque literal del charter
cambió. El addendum A1 (§102–§109) se agregó después de la §101.
