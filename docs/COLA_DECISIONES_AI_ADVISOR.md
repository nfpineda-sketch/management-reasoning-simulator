# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** sólo lo que requiere una decisión del docente, más el estado
  de lo ya decidido.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-09-27, al cerrar el ciclo 2.

| ID | Clase | Tema | Estado |
|---|---|---|---|
| DF-7 | CRITICAL | Razonamiento del residente alterado o mal atribuido en el Management Trace | **Implementado y verificado** en el ciclo 2 · queda DF-10 |
| DF-1 | CRITICAL · STRUCTURAL | Observation opportunities para TD/F/C | Arquitectura aprobada · **D-1 a D-6 pendientes** |
| DF-2 | CRITICAL · METHODOLOGICAL REVIEW | R1-03, R1-04 y R2-01 al pipeline observacional | Verificado contra los PDF · **decisión pendiente** |
| DF-6 | HIGH VALUE · METHODOLOGICAL REVIEW | Corpus de validación EN/ES independiente | Diseño entregado · **decisión pendiente** |
| DF-10 | HIGH VALUE | Seguimiento pegado al alta, perdido en ambos idiomas | **Nuevo** · decisión pendiente |
| DF-4 | CLINICAL + METHODOLOGICAL REVIEW | C2 y los casos trauma | Texto obsoleto corregido · C2 deshabilitada · **amplitud pendiente** |
| DOC-1 | Documentación | §51 del charter, truncada | **Pendiente del texto del docente** |
| DF-3 | — | MK1 de R2-01 | **Cerrado documentalmente** (fuente verificada); su uso pasa a DF-2 |
| DF-9 | METHODOLOGICAL REVIEW | −3, doble efecto de safety y varios eventos por una conducta | Registrado · sin decisión ahora |
| DF-11 | LOW PRIORITY | Residuos menores de la lectura | Registrado |
| DF-5 | — | C15 | Deshabilitada, sin acción |

---

### [CRITICAL] DF-7 · Fidelidad del razonamiento en el Management Trace · IMPLEMENTADO Y VERIFICADO

**Qué se hizo.** Se corrigieron en la fuente, por clase y no por frase:

- «im» ya no se reescribe como «I'm»;
- las palabras terminadas en «-so» ya no se truncan;
- una orden ya no se registra como modelo de trabajo;
- se eliminaron las asimetrías EN/ES del razonamiento registrado.

Detalle en `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, sección «Ciclo 2».

**Resultado sobre el mismo corpus** (antes → después):

- **Citas alteradas:** ES 4 → 0.
- **Órdenes como modelo de trabajo:** ES 5 → 0 y EN 1 → 0.
- **Rationale declarado en ES:** 0 → 21, igual que el inglés.
- **Diferencias pareadas EN/ES:** 62 → 1. La que queda es la ambigüedad de
  «por» en español, fiel en ambos idiomas.
- **Capa de órdenes:** sin cambios en órdenes, tiempos, retenciones ni cierres,
  salvo las 3 correcciones buscadas.
- **Suite completa.** La primera corrida encontró 13 fallas: 12 órdenes
  compactas que el gate volvía a retener y una lectura de claves en la
  herramienta del ciclo 1. Se corrigieron por clase y la medición se repitió con
  el código final: mismos números, ninguna decisión cambiada.
- **Pruebas:** 32 nuevas, 366 focalizadas, 56 regresiones y la suite completa
  (4696) pasan.
- **Latencia:** unos 1 ms más por orden (3,4 → 4,1–4,4 ms); el tiempo por
  encuentro no cambió.

**Sin decisión pendiente.** Lo que no se corrigió está en DF-10 y DF-11.

---

### [CRITICAL · STRUCTURAL] DF-1 · Observation opportunities: D-1 a D-6

**PROBLEM**

La elegibilidad de TD1, F1, C1, C3, C4 y C14 es una lista fija
(`competency_mapping.py:259`).

**EVIDENCE**

- `docs/PROPUESTA_OBSERVATION_OPPORTUNITIES.md`, §9, trae el análisis de cada
  decisión, con lo que dicen las EPAs en la v1.1.
- Por ejemplo, C14 (p. 42) exige adquirir imagen y nombra los estados clínicos
  que el POCUS determina.

**WHY IT MATTERS**

Es la integridad de la evidencia longitudinal (§8, §10, §96).

**RECOMMENDATION**

| Decisión | Recomendación |
|---|---|
| D-1 | (a) bloque `objectives` en la declaración del caso |
| D-2 | (c) tres estados, activación objetivo por objetivo |
| D-3 | (a) prospectivo + (c) reevaluación a pedido |
| D-4 | (a) evidencia exigida por declaración |
| D-5 | (a) el AI Advisor redacta y el docente aprueba; C14 primero, sobre los 31 casos |
| D-6 | (b) por ahora; (a) después del piloto |

**ALTERNATIVES**

Están en la §9 de la propuesta, para cada decisión.

**COST / EFFORT**

- Mecanismo: una sesión.
- Borradores de C14: una sesión.
- Revisión docente: unos minutos por caso.

**RISK**

- Declaraciones incompletas.
- Convivencia de dos reglas durante la transición: se mitiga con la activación
  por objetivo.

**DECISION NEEDED**

¿Aprueba D-1 a D-6 como se recomiendan, o con cambios?

La elegibilidad no se tocará hasta esa aprobación.

---

### [CRITICAL · METHODOLOGICAL REVIEW] DF-2 · R1-03, R1-04 y R2-01 al pipeline

**PROBLEM**

Estos tres desafíos se asignan y se juegan, pero no pueden convertirse en
evidencia.

**EVIDENCE**

`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md`, verificado contra los tres PDF:

| Desafío | ACGME | Royal College |
|---|---|---|
| R1-03 | PC4 y MK2 VERIFIED · PC5 PARTIAL | ME 2.2 VERIFIED: Pathway Foundations p. 11 = F1 hito 3 · ME 2.4 PARTIAL |
| R1-04 | PC1 y PC6 VERIFIED | ME 4.1 VERIFIED en Pathway Foundations pp. 22–23; como EPA sólo PARTIAL (F2 es de presentaciones no complicadas) · ME 2.4 PARTIAL |
| R2-01 | PC1, PC4 y MK2 VERIFIED · MK1 PARTIAL | ME 1.6 VERIFIED: Pathway Core p. 9 y C1 hito 1 · ME 2.4 PARTIAL |

**WHY IT MATTERS**

Hoy es evidencia perdida (§9).

**RECOMMENDATION**

- **Lado Royal College:**
  - **A.** *Pathway to Competence* como fuente primaria para estos tres
    desafíos, sólo con los vínculos VERIFIED.
  - **C.** Para los PARTIAL: no se incorporan. ME 2.4 en los tres no entra, en
    lugar de mantenerse sólo para completar cobertura.
  - **B.** Sólo como anotación opcional, donde el contexto de la EPA calza.
- **Lado ACGME:** los vínculos VERIFIED. PC5 y MK1 quedan a decisión del
  docente.
- **Diseño:** las conductas observables se adaptan de `docs/CURRICULUM_PILOT.md`.

**ALTERNATIVES**

- **B como regla general.** Descartada: en R1-04 obligaría a una EPA cuyo
  contexto contradice el encuentro.
- **Sólo ACGME.**

**COST / EFFORT**

Una sesión, más la revisión docente de las conductas.

**RISK**

- **Estructural:** una segunda fuente del Royal College sin EPA en
  `competency_mapping`.
- **Si se aprueban vínculos PARTIAL:** evidencia más débil.

**DECISION NEEDED**

1. ¿A + C como se recomienda?
2. ¿Incorporar PC5 (R1-03) y MK1 (R2-01), que son PARTIAL?
3. ¿Aprueba adaptar las conductas documentadas?

Nada se incorpora a Objective Progress hasta esa aprobación.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-6 · Corpus de validación EN/ES independiente

**PROBLEM**

El único corpus disponible es la muestra con la que se ajustó el lector.

**EVIDENCE**

`docs/DISENO_VALIDATION_CORPUS.md`.

**WHY IT MATTERS**

Sin datos externos no se sabe cuántas órdenes reales se leen mal (§37, §90).

**RECOMMENDATION**

- 60 intenciones × 2 redacciones × 2 idiomas = 240 entradas.
- Escritores nativos independientes, que no conocen el lector.
- Mitad visible y mitad sellada.
- Métricas de la §90 más fidelidad de las categorías y paridad EN/ES.
- Herramienta determinista.

**ALTERNATIVES**

- Paráfrasis generadas por IA: tienen costo y un estilo que no es el de un
  clínico.
- Encuentros reales: requieren autorización y revisión de privacidad.

**COST / EFFORT**

- Unas 9 a 12 h humanas, entre 3 y 5 personas.
- Una sesión de herramienta.
- US$0 en IA.

**RISK**

- Contaminación: se mitiga con la mitad sellada y la regla de corregir sólo
  por clase.
- Tamaño inicial limitado.

**DECISION NEEDED**

- ¿Aprueba el diseño?
- ¿Quién escribe las tarjetas y quién redacta en cada idioma?
- ¿Dónde se custodia la mitad sellada?

---

### [HIGH VALUE] DF-10 · Un seguimiento pegado a la orden de alta se pierde, en ambos idiomas

**PROBLEM**

«Discharge her with cardiology follow-up» y «La doy de alta con control en
policlínico» ejecutan el alta, pero el seguimiento no queda registrado como
indicación. Sí queda cuando va como elemento aparte de una lista
(«…, urology follow-up», «…, control urologico»).

**EVIDENCE**

- Se reprodujo con `parse_family_actions` durante DF-7.
- No es una asimetría EN/ES: falla igual en ambos idiomas.
- Por eso no se corrigió en el ciclo 2 (§85, control de alcance).

**WHY IT MATTERS**

El plan de continuidad es evidencia de D5 y del evento crítico de alta sin
seguimiento. Perderlo empobrece el registro de lo que el residente decidió.

**RECOMMENDATION**

En `family_parser`, cuando la orden de alta trae un complemento «with/con» que
empieza como una indicación («follow-up», «control», «cita», «seguimiento»),
separarlo como indicación. Es la misma clase que ya se corrigió para las listas.

**ALTERNATIVES**

Ninguna razonable: hoy se pierde en silencio.

**COST / EFFORT**

Bajo: unas horas, con pruebas en ambos idiomas.

**RISK**

Bajo. Debe verificarse que no parta órdenes de alta con complementos que no son
indicaciones, como «con analgesia».

**DECISION NEEDED**

¿Autoriza corregirlo en el ciclo 3?

---

### [CLINICAL + METHODOLOGICAL REVIEW] DF-4 · C2

**PROBLEM**

C2 está deshabilitada. Existen casos trauma, pero no se ha establecido que su
amplitud represente la EPA.

**EVIDENCE**

- `docs/AUDITORIA_OPORTUNIDAD_C2.md`.
- **EPA Guide v1.1, p. 20:** C2 se centra en liderar un equipo en el trauma
  grave de uno o varios sistemas. Pide 25 observaciones: al menos 5 adultos
  con trauma penetrante, al menos 10 adultos en entorno clínico (no simulado) y
  al menos 5 presentaciones pediátricas.
- **Qué ofrece el banco:** 2 casos adultos, uno penetrante y uno contuso.

**WHY IT MATTERS**

Habilitarla con evidencia estrecha acreditaría una EPA sin la variedad que
implica (§11).

**RECOMMENDATION**

- Mantener C2 deshabilitada.
- Si se habilita algún día, que sea mediante DF-1, sólo en los casos
  declarados.

**Hecho en el ciclo 2.** El texto obsoleto se corrigió en dos lugares:

- `objectives.py`, en el alcance y la limitación de C2;
- la tabla de progreso: «Not enabled: current encounters are not established as
  offering enough opportunities…», con su versión en español.

No se fijó ningún número mínimo.

**ALTERNATIVES**

Habilitarla para los 2 casos. No se recomienda.

**COST / EFFORT**

Clínico: decidir la amplitud.

**RISK**

Acreditar con evidencia estrecha.

**DECISION NEEDED**

¿Qué amplitud de casos trauma consideraría suficiente para habilitar C2? Es
una decisión clínica y metodológica. El AI Advisor no propone un número.

---

### DOC-1 · §51 del charter, truncada

- **Qué llegó.** El texto de la §51 («DEFINICIÓN FINAL DEL PRODUCTO») termina en
  «…y construir progresivamente una representación multidimensional y
  longitudinal del desempeño del», y la línea siguiente ya es la §52.
- **Qué se hizo.** Nada se completó ni se infirió. Es la única sección cortada:
  se revisaron las otras 100 más la §101.
- **DECISION NEEDED:** ¿el texto final de la §51?

---

### DF-3 · MK1 · CERRADO DOCUMENTALMENTE

- **Fuente verificada:** ACGME *Emergency Medicine Milestones* v2.1, PDF p. 15
  (hoja impresa 9), «Medical Knowledge 1: Scientific Knowledge».
- **Vínculo R2-01 → MK1:** PARTIAL. MK1 describe conocimiento, y el simulador
  sólo ve su aplicación.
- **Su uso se decide en DF-2.**

---

### [METHODOLOGICAL REVIEW] DF-9 · Penalidad −3, doble efecto de safety y varios eventos por una conducta

- **Se mantiene sin cambios**, como pide el charter (§19 a §22 y §47):
  `max(0, base − 3 × eventos confirmados)`, el doble efecto sobre D3 y el total,
  y la acumulación de eventos.
- **Los eventos críticos siguen siendo una señal independiente**, que no
  modifica los promedios D1–D5.
- **Acción del AI Advisor:** registrar ejemplos reales cuando aparezcan en
  encuentros confirmados.
- **DECISION NEEDED:** ninguna ahora.

---

### [LOW PRIORITY] DF-11 · Residuos menores de la lectura

- **«since» en inglés.** No se lee como razón porque también es temporal.
- **Encontrado al probar DF-7, anterior al ciclo:**
  - en inglés, «to reduce the congestion and I will recheck…» registra «and I
    will» dentro de la expectativa;
  - «Hyperkalemia with peaked T waves» e «Hiperkalemia con T picudas» no se leen
    como modelo en ninguno de los dos idiomas, porque el vocabulario de
    hallazgos es una lista cerrada.
- **Correcciones ortográficas en las citas.** «rythm» → «rhythm» y
  «urianalysis» → «urinalysis» cambian la palabra citada, no su sentido. Las
  fijan las regresiones v0814 y v0816.
- **Guion 5, decisión 9.** «por» en español no se lee como causal; queda una
  diferencia pareada fiel en ambos idiomas.
- **`objectives.TARGET_SOURCE`.** Cita las páginas de la edición de 51 páginas
  (v1.0). La edición verificada en `SOURCES` es la v1.1 de 59 páginas, con otras
  páginas pero los mismos conteos. Aclararlo modificaría el texto de un objetivo.
- **DECISION NEEDED:** ninguna urgente. Se pueden atender en un ciclo con
  capacidad libre.

---

### DF-5 · C15

Deshabilitada, sin cambios. No hay encuentros diseñados para cuidados al final
de la vida (§11).
