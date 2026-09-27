# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** sólo las recomendaciones que requieren una decisión del
  docente. No es un backlog.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-09-27, al cerrar el ciclo 1. Ninguna entrada está
  implementada.

| ID | Clase | Tema | Estado |
|---|---|---|---|
| DF-7 | CRITICAL | Razonamiento del residente alterado o mal atribuido en el Management Trace | Abierta · nueva |
| DF-1 | CRITICAL · STRUCTURAL | Oportunidades de observación para TD/F/C (propuesta de mecanismo) | Abierta · propuesta entregada |
| DF-2 | CRITICAL · METHODOLOGICAL REVIEW | R1-03, R1-04 y R2-01 al pipeline observacional | Abierta · verificación documental hecha |
| DF-6 | HIGH VALUE · METHODOLOGICAL REVIEW | Fuente de datos para medir el lector de órdenes EN/ES fuera de la muestra de ajuste | Abierta · nueva |
| DF-3 | METHODOLOGICAL REVIEW | MK1 de R2-01 | Abierta · fuente exacta identificada |
| DF-4 | CLINICAL REVIEW | C2 y los casos trauma | Abierta · auditoría hecha |
| DF-9 | METHODOLOGICAL REVIEW | −3, doble efecto de safety y varios eventos por una conducta | Registrada · sin decisión ahora |
| DF-5 | — | C15 | Cerrada por el charter (sin acción) |

---

### [CRITICAL] DF-7 · El Trace altera o atribuye mal el razonamiento del residente

**PROBLEM**

La extracción determinista de las cuatro categorías
(`app.py`, `extract_explicit_reasoning`) produce tres tipos de error:

- cambia palabras del residente;
- trunca otras;
- guarda órdenes como si fueran su «modelo de trabajo».

Además, capta actualizaciones del modelo de forma distinta según el idioma.

**EVIDENCE**

Todo es KNOWN y reproducible (`docs/MEDICION_RECONOCIMIENTO_ORDENES.md`):

- **«im» pasa a «I'm» (`app.py:5687`).** «Doy adrenalina 0.5 mg im» queda
  registrado como modelo de trabajo declarado: «Doy adrenalina 0.5 mg I'm».
  Ocurre en 3 decisiones.
- **Truncamiento antes de «so» (`app.py:5708` y siguientes).** La expresión
  busca «so» sin límite de palabra previo: «compromiso» queda como «compromi».
  En inglés afectaría a «also».
- **Una orden como modelo de trabajo.** Pasa en 5 de 30 modelos declarados en
  español y en 1 de 29 en inglés. Ejemplo: «inicio adrenalina en infusion…»,
  donde el residente había escrito «Toma betabloqueador, por eso no responde».
- **Diferencias pareadas EN/ES en el razonamiento.** 6 de 119 decisiones, con
  déficits en ambos sentidos. Por ejemplo, el español no registra «falla
  ventilatoria inminente» y el inglés no registra «glimepiride… cannot go home».
- **Menores, en la capa de órdenes:**
  - el inglés pierde «urology follow-up» y recorta las indicaciones de regreso;
  - en español «PA, FC» se lee como foco `general`, cuando en inglés el
    equivalente se lee como `perfusion`.

**WHY IT MATTERS**

- El brief, la propuesta de rúbrica y los PDF leen esas categorías como
  razonamiento del residente (§33).
- Atribuirle lo que no escribió va contra la §62.
- Es fidelidad del Management Trace: CRITICAL según la §3.

**RECOMMENDATION**

Corregir en la fuente, en el ciclo 2, por clase de error y no por frase (§57):

- reescribir sólo para buscar patrones, y citar siempre desde el texto original
  del residente;
- exigir límite de palabra antes de los marcadores de cláusula;
- no aceptar como modelo de trabajo una cláusula que el lector ejecuta como
  orden;
- añadir pruebas pareadas EN/ES de las cuatro categorías, además de las de
  acciones.

**ALTERNATIVES**

- Corregir sólo los dos errores de expresión regular: bajo costo, pero deja la
  atribución.
- Marcar las categorías dudosas en la interfaz docente en vez de corregir: agrega
  fricción y no arregla la fuente.

**COST / EFFORT**

- Medio: una sesión.
- Sin costo de IA: se verifica con `tools_order_reading.py` y pruebas
  focalizadas.

**RISK**

- Tocar el lector puede cambiar lo que se retiene o se pregunta en otros
  guiones.
- Mitigación: repetir la medición pareada completa antes y después.
- Los encuentros históricos no cambian (§75).

**DECISION NEEDED**

¿Autoriza corregir estos defectos en el ciclo 2, con la medición pareada como
criterio de aceptación?

---

### [CRITICAL · STRUCTURAL] DF-1 · Oportunidades de observación para TD1, F1, C1, C3, C4 y C14

**PROBLEM**

`objective_is_eligible` devuelve verdadero para estos seis en todo encuentro
completado (`competency_mapping.py:259`). Pueden acreditarse sin oportunidad
real (§10).

**EVIDENCE**

- La lista fija está en el código.
- El brief propone sobre 6 o 7 objetivos en todo encuentro.
- Los 31 casos traen POCUS, así que la disponibilidad de un estudio no sirve como
  regla.
- Detalle en `docs/PROPUESTA_OBSERVATION_OPPORTUNITIES.md`.

**WHY IT MATTERS**

- Es la integridad de la evidencia longitudinal.
- Ausencia de oportunidad ≠ desempeño insuficiente (§8, §63).

**RECOMMENDATION**

Mecanismo (a) de la propuesta:

- **Declarar:** un bloque `objectives` en la declaración de cada caso, al lado de
  D1–D5.
- **Verificar:** con `case_assessment.verify`.
- **Congelar:** con `evaluation_basis`.
- **Leer:** `objective_is_eligible` usa esa copia congelada.
- **Piloto:** C14, con declaraciones redactadas por el AI Advisor y aprobadas por
  un docente.

**ALTERNATIVES**

- (b) Un registro paralelo de oportunidades.
- (c) Una heurística sobre el Trace.
- (d) Que la IA decida la oportunidad al analizar.

Las tres se desaconsejan; las razones están en la propuesta, §5.

**COST / EFFORT**

- Mecanismo: medio, una sesión.
- Declaraciones: trabajo clínico por caso. Es el costo dominante.
- El brief baja de costo, porque sólo propone sobre objetivos declarados.

**RISK**

- Declaraciones incompletas: se mitiga con la matriz de cobertura.
- Encuentros históricos: requieren una decisión explícita.

**DECISION NEEDED**

Las decisiones D-1 a D-6 de la propuesta, §8:

- el mecanismo;
- qué significa que un caso no declare un objetivo;
- los encuentros históricos;
- si la evidencia citada debe incluir el elemento de la oportunidad;
- el piloto de C14;
- las observaciones incidentales.

---

### [CRITICAL · METHODOLOGICAL REVIEW] DF-2 · R1-03, R1-04 y R2-01 generan encuentros que no pueden convertirse en evidencia

**PROBLEM**

Estos tres desafíos se asignan y se juegan, sobre los perfiles PS001, pero no
existen como objetivo. El docente no puede confirmar nada de ellos (§9).

**EVIDENCE**

`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md`:

- **Lado ACGME:** todos sus códigos, salvo MK1, están en la tabla verificada del
  código.
- **Lado Royal College:** cita competencias CanMEDS de *Pathway to Competence*,
  que no está en `SOURCES` y no tiene el nivel de hito de EPA que exige el
  pipeline.
- **Diseño:** faltan conductas observables, frase de oportunidad y condiciones de
  evidencia. Las conductas existen en español en `docs/CURRICULUM_PILOT.md`.

**WHY IT MATTERS**

- Cada uno de estos encuentros es hoy evidencia perdida.
- Es incoherente con la arquitectura objetivo (§8).

**RECOMMENDATION**

Incorporarlos con el patrón de los 8 desafíos de sesgo:

- **Lado ACGME:** los códigos ya verificados.
- **Lado Royal College:** la opción (c); queda pendiente y visible hasta decidir
  entre (a) y (b).
- **Diseño:** adaptar las conductas documentadas a `CHALLENGE_MAPPINGS`.
- **MK1:** fuera hasta resolver DF-3.

**ALTERNATIVES**

- **(a)** Registrar *Pathway to Competence* como segunda fuente del Royal
  College, a nivel de competencia.
- **(b)** Anclarlos a hitos ya verificados de la *EPA Guide* que llevan los
  mismos códigos CanMEDS (C5, TP6). Es un mapping nuevo.

**COST / EFFORT**

- Medio: una sesión de código simétrico al existente, más la revisión docente de
  las conductas.

**RISK**

- Bajo si se usa sólo lo verificado.
- Anclar a EPA sin juicio docente sería inventar un mapping (§43.11).

**DECISION NEEDED**

- ¿(c) ahora, y (a) o (b) después?
- ¿Aprueba adaptar las conductas de `docs/CURRICULUM_PILOT.md:13-15` como sus
  conductas observables?

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-6 · ¿Con qué datos se mide de verdad el lector EN/ES?

**PROBLEM**

El único corpus disponible es la muestra con la que se ajustó el lector. Da
96/96 en ambos idiomas, pero no estima fallas reales (§57). Por instrucción, la
medición de órdenes se detuvo aquí.

**EVIDENCE**

- `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`.
- `test_the_twenty_in_english.py` exige paridad sobre esos mismos textos.
- El corpus no incluye la familia trauma.

**WHY IT MATTERS**

Es la prioridad 1 del charter (§37). Sin una muestra independiente no se puede
saber cuántas órdenes reales se leen mal ni en qué idioma (§90).

**RECOMMENDATION**

- **(a)** Un corpus nuevo, escrito por docentes o residentes que no conozcan el
  lector: las mismas situaciones en EN y ES, incluida trauma, con la intención
  clínica anotada por quien escribe. Esa anotación es el estándar que falta para
  medir interpretación parcial o incorrecta.
- **(b)** Después, si se aprueba con revisión de privacidad (§76), encuentros
  reales de residentes desidentificados.

**ALTERNATIVES**

Paráfrasis generadas por IA:

- baratas de producir;
- pero con estilo de modelo y no de clínico;
- tienen costo de IA y requieren autorización de presupuesto.

**COST / EFFORT**

- (a) Tiempo docente, sin costo de IA. La herramienta ya existe.
- (b) Revisión de privacidad y acceso a datos.

**RISK**

- (a) Un corpus pequeño puede no generalizar.
- (b) Datos personales.

**DECISION NEEDED**

¿(a), (b), ambas o ninguna por ahora? Si (a): ¿quién escribe el corpus y de qué
tamaño?

---

### [METHODOLOGICAL REVIEW] DF-3 · MK1 de R2-01

**PROBLEM**

R2-01 cita ACGME MK1, que no está en la tabla verificada del código. Por
instrucción, no se usa mientras siga UNVERIFIED.

**EVIDENCE**

- `docs/CURRICULUM_PILOT.md:61` cita «MK1 *Scientific Knowledge*, p. 15» de la
  edición aportada al inicio del proyecto.
- La búsqueda anterior no la había encontrado porque cubría sólo el código.
- La página es coherente con la tabla verificada (INFERRED).
- `www.acgme.org` está bloqueado desde este entorno.

**WHY IT MATTERS**

Un código sin fuente verificada rompe el estándar de trazabilidad que el resto
cumple (§43.11).

**RECOMMENDATION**

Verificar contra la fuente exacta:

- **Documento:** ACGME *Emergency Medicine Milestones*, Worksheet 2.1, segunda
  revisión de febrero de 2021, vigente desde el 1 de julio de 2021.
- **Archivo:** `emergencymedicinemilestones.pdf`.
- **Ubicación:** subcompetencia *Medical Knowledge 1*, PDF p. 15, hoja impresa 9
  (INFERRED).
- **Qué leer:** título, páginas, texto de los niveles 1 a 5 y versión en la
  portada.
- **Después:** decidir si las conductas de R2-01 son evidencia de MK1.

**ALTERNATIVES**

- (a) Habilitar `www.acgme.org` en la red del entorno.
- (b) Que el docente aporte las páginas.
- (c) Retirar MK1 de R2-01 y dejar PC1, PC4 y MK2.

**COST / EFFORT**

Bajo.

**RISK**

Bajo. Sin la fuente, el vínculo sigue excluido.

**DECISION NEEDED**

¿(a), (b) o (c)?

---

### [CLINICAL REVIEW] DF-4 · C2 y los casos trauma

**PROBLEM**

C2 está deshabilitada con un texto que dice que no existen encuentros de trauma.
Desde el 2026-09-23 existen dos.

**EVIDENCE**

`docs/AUDITORIA_OPORTUNIDAD_C2.md`:

- **Los dos casos sí son resucitación de trauma:** xABCDE, control de hemorragia,
  sangre frente a cristaloide, drenaje y búsqueda de otra fuente.
- **Tienen el soporte del motor:** reloj de sangrado, acciones ejecutables, D1–D5
  declarados y eventos críticos propios.
- **La amplitud no alcanza:** 2 mecanismos aislados, adultos, sin equipo, sin
  quirófano, sin pelvis, abdomen, TCE ni pediatría.
- **Exposición:** llegan a un residente 1 de cada 7 veces por R2-04 y 1 de cada 4
  por R2-05.
- **Fuente oficial sin leer:** el criterio del Royal College para C2 (EPA Guide
  2018, p. 19 de la edición de 51 páginas) no se pudo consultar desde este
  entorno.

**WHY IT MATTERS**

- Habilitarla por la mera presencia de un paciente traumatizado acreditaría una
  EPA sin la variedad que implica (§11).
- Con 2 casos y una meta de 25 observaciones, se mezcla evidencia nueva con
  memoria del caso.

**RECOMMENDATION**

- Mantener C2 deshabilitada.
- Si se habilita, que sea sólo mediante DF-1: declarada en los casos que la
  ofrecen, con un alcance acotado al componente simulado de manejo, como C1 y
  C3.
- Actualizar el texto de C2 para que diga por qué sigue deshabilitada.

**ALTERNATIVES**

- Habilitarla ya para los dos casos.
- Esperar a tener más mecanismos: pelvis, abdomen, multisistémico.

**COST / EFFORT**

- Bajo para el texto.
- Clínico para decidir la amplitud mínima.

**RISK**

Acreditar una EPA con evidencia estrecha.

**DECISION NEEDED**

- ¿Qué amplitud mínima de casos trauma exige para habilitar C2?
- ¿Autoriza corregir el texto de C2?

---

### [METHODOLOGICAL REVIEW] DF-9 · Penalidad −3, doble efecto de safety y varios eventos por una conducta

Registro pedido por las §20 a §22 y las preguntas 1 a 3 de la §48.

- **Qué se mantiene:** el charter conserva por ahora `max(0, base − 3 × eventos
  confirmados)`, el doble efecto sobre D3 y el total, y la acumulación de eventos.
  Nada de esto se modificó.
- **Qué falta:** estos tres puntos no se consideran validados. Faltan ejemplos
  reales:
  - encuentros confirmados donde una sola conducta active dos eventos;
  - o donde el doble efecto cambie la interpretación.
- **Acción del AI Advisor:** registrar esos ejemplos cuando aparezcan en
  encuentros confirmados.
- **DECISION NEEDED:** ninguna ahora.

---

### DF-5 · C15 (sin acción)

- El charter (§11) decide mantener C15 deshabilitada mientras no existan
  encuentros que creen oportunidad de cuidados al final de la vida.
- El banco sigue sin esa familia.
- Queda registrada para que la cola cubra los cinco vacíos de la §7.
