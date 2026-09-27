# Verificación documental · R1-03, R1-04, R2-01 y MK1 contra las fuentes oficiales

Ciclo 2 del AI Advisor, paso A (2026-09-27). Reemplaza la versión del ciclo 1,
que se había hecho sin acceso a los PDF.

**Qué se hizo.** Se verificó contra los tres documentos oficiales que aportó el
docente. No se agregó, cambió ni retiró ningún mapping. R1-03, R1-04 y R2-01 no
se incorporaron a Objective Progress.

**Convención de citas.**

- **ACGME:** se cita textual, porque su licencia permite el uso educativo.
- **Royal College:** se usan paráfrasis fieles, con el código, el número de hito
  y la página exactos. Su licencia prohíbe compartir el material con terceros, y
  el repositorio ya usa rótulos propios (`competency_mapping.py`).
- **Los PDF no se incluyen en el repositorio.**

## 1. Fuentes primarias procesadas

| | ACGME | Royal College · EPA Guide | Royal College · Pathway to Competence |
|---|---|---|---|
| Institución | Accreditation Council for Graduate Medical Education | Royal College of Physicians and Surgeons of Canada, Emergency Medicine Specialty Committee | Ídem |
| Título oficial | *Emergency Medicine Milestones* | *Entrustable Professional Activity Guide: Emergency Medicine* | *Pathway to Competence: Emergency Medicine* («Pathway to Competence in the Specialty of Emergency Medicine (2018)») |
| Versión y fecha | Version 2.1 (ACGME Report Worksheet); Second Revision February 2021; Implementation July 1, 2021 | 2018 VERSION 1.1, editorial revision November 1, 2018 | 2018 VERSION 1.0, efectiva para residentes que ingresan desde el 1 de julio de 2018 |
| Páginas | 28 | 59 | 61 |
| Estructura relevante | Una subcompetencia por página, niveles 1 a 5 en columnas | Una EPA por entrada: key features, plan de observación, número de observaciones y «Relevant milestones» numerados con código CanMEDS | Tabla por rol CanMEDS: competencia clave → competencia habilitante → hitos por etapa (TTD, Foundations, Core, TTP), con etiquetas de la EPA que observa cada hito |
| Nomenclatura | PC1–PC8, MK1–MK2, SBP, PBLI, PROF, ICS | TD1–3, F1–4, C1–15, TP1–6; hitos «ME 1.6», «ME 2.2»… | Códigos CanMEDS (ME, COM, COL, L, HA, S, P) con número de competencia |
| Archivo y huella | `emergencymedicinemilestones.pdf`, sha256 `6b926c54…` | `epa-guide-emergency-med-e.pdf`, sha256 `5d10cd58…` | `pathway-to-competence-emergency-medecine-e.pdf`, sha256 `e0443443…` |

### 1.1 Lo que el código ya usaba (VERIFIED)

- **`competency_mapping._ACGME`.** Las 7 entradas coinciden con el PDF de ACGME en
  página, página impresa y título: PC1 p. 7 (1), PC2 p. 8 (2), PC3 p. 9 (3),
  PC4 p. 10 (4), PC5 p. 11 (5), PC6 p. 12 (6) y MK2 p. 16 (10). La numeración
  impresa desplaza 6 páginas en todo el documento.
- **`competency_mapping._RC`.** Las 10 entradas coinciden con la EPA Guide v1.1:
  - C5 en p. 25, hitos 1 (ME 1.6); 2, 3, 4 y 5 (ME 2.2); 6 (ME 2.4); 8 (COM 2.3);
  - TP6 en p. 57, hitos 2 (ME 2.1), 3 (ME 3.3) y 4 (ME 4.1).
- **`objectives.TARGET_SOURCE`.** Los 8 conteos se repiten en la v1.1: TD1 10,
  F1 15, C1 40, C2 25, C3 20, C4 20, C14 50 y C15 5.
  - En la v1.1 las páginas son TD1 4, F1 10, C1 18, C2 20, C3 22, C4 23, C14 42
    y C15 44.
  - `TARGET_SOURCE` cita las páginas de la edición de 51 páginas (v1.0), que es
    otra edición. No es un error, y no se modificó.
- **`docs/CURRICULUM_PILOT.md:61-62`.** Las páginas de Pathway que cita son
  exactas: ME 1.6 pp. 9–10, ME 2.2 pp. 11–14, ME 2.4 pp. 15–17 y ME 4.1
  pp. 22–23.

## 2. MK1 · DF-3 cerrado documentalmente

- **Código y título:** ACGME Medical Knowledge 1, *Scientific Knowledge*.
- **Ubicación:** PDF p. 15, hoja impresa 9, Version 2.1.
- **Estado de la fuente:** **VERIFIED**. El título, la página, la página impresa y
  la versión coinciden con lo que citaba `docs/CURRICULUM_PILOT.md:61`.
- **Texto de los niveles:**
  - L1 «Demonstrates scientific knowledge of common presentations and
    conditions»;
  - L2 «Demonstrates scientific knowledge of complex presentations and
    conditions»;
  - L3 «Integrates scientific knowledge of comorbid conditions for complex
    presentations»;
  - L4 «Integrates scientific knowledge of uncommon, atypical, or complex
    comorbid conditions for complex presentations»;
  - L5 «Pursues and integrates new and emerging knowledge».
- **El vínculo R2-01 → MK1 queda PARTIAL (sección 3.3).** MK1 describe
  conocimiento, no una conducta. El simulador sólo observa su aplicación en el
  mecanismo que el residente declara. Usarlo es una decisión metodológica
  (DF-2).

## 3. Mappings: trazabilidad y estado

**Estados:**

- **VERIFIED:** el elemento existe en la fuente citada, y su lenguaje oficial
  describe directamente una conducta observable del desafío, en un contexto
  clínico compatible con sus encuentros.
- **PARTIAL:** el elemento existe, pero su lenguaje describe esa conducta sólo en
  parte o indirectamente, o el contexto de la EPA es incompatible.
- **UNVERIFIED:** no se encontró en las fuentes.
- **UNSUPPORTED:** existe, pero su lenguaje no describe lo que el desafío
  observa.

**Conductas de cada desafío.** Se tomaron del texto de `curriculum.py:12-27` y de
`docs/CURRICULUM_PILOT.md:13-15`.

**Lectura de las columnas RC.**

- **(A) Pathway:** el hito por etapa de Pathway to Competence.
- **(B) EPA Guide:** el mismo hito dentro de una EPA de la EPA Guide.

### 3.1 R1-03 · Relacionar la taquicardia con el estado del paciente (año 1)

**Conductas:**

- explicar una hipótesis causal con hallazgos;
- vincular la prioridad con esa hipótesis;
- anticipar cambios en la perfusión además del ritmo;
- comparar la respuesta observada.

| Framework | Elemento exacto | Documento · página | Lenguaje de apoyo | Estado |
|---|---|---|---|---|
| ACGME | PC4 Diagnosis, L3 | Milestones v2.1 · p. 10 (4) | «demonstrates the ability to modify a diagnosis based on a patient’s clinical course and additional data» | **VERIFIED** |
| ACGME | PC5 Pharmacotherapy, L3 | Milestones v2.1 · p. 11 (5) | «selects appropriate agent based on mechanism of action and intended effect»: aplica sólo si la prioridad elegida es un fármaco, y el desafío no lo exige | **PARTIAL** |
| ACGME | MK2 Treatment and Clinical Reasoning, L4 | Milestones v2.1 · p. 16 (10) | «Continually re-appraises one’s clinical reasoning…»: corresponde a comparar la respuesta con la explicación | **VERIFIED** |
| RC · ME 2.2 | (A) Foundations: construir un diagnóstico de trabajo y diferencial mientras se trata el síntoma | Pathway v1.0 · p. 11 | Describe la hipótesis causal ligada a la conducta terapéutica | **VERIFIED** |
| RC · ME 2.2 | (B) Mismo hito como F1, hito 3 | EPA Guide v1.1 · p. 10 | F1 incluye explícitamente el manejo de disritmias críticas, y el contexto es compatible | **VERIFIED** |
| RC · ME 2.2 | (B) TD1, hito 8: interpretar el ECG reconociendo condiciones que requieren intervención inmediata, incluida la disritmia | EPA Guide v1.1 · p. 4 | Sólo reconocer; no explicar la contribución del ritmo | **PARTIAL** |
| RC · ME 2.4 | (A) Foundations: elaborar e implementar planes iniciales de manejo para problemas comunes | Pathway v1.0 · p. 15 | Plan de manejo genérico; no describe ligar la prioridad a una hipótesis | **PARTIAL** |
| RC · ME 2.4 | (B) TD1, hito 9 (iniciar monitorización e intervenciones urgentes en el inestable) · C5, hito 6 (planes que consideran todos los problemas, con paciente, familia y equipo) | EPA Guide v1.1 · pp. 5 y 25 | Cubren parte: la colaboración de C5 no es observable | **PARTIAL** |

### 3.2 R1-04 · Anticipar y comprobar el efecto de una intervención (año 1)

**Conductas:**

- formular una expectativa verificable;
- elegir variables y un momento de reevaluación;
- distinguir la orden de su ejecución;
- comparar lo observado con lo esperado.

| Framework | Elemento exacto | Documento · página | Lenguaje de apoyo | Estado |
|---|---|---|---|---|
| ACGME | PC1 Emergency Stabilization, L3 | Milestones v2.1 · p. 7 (1) | «Reassesses the patient’s status after implementing a stabilizing intervention» | **VERIFIED** |
| ACGME | PC6 Reassessment and Disposition, L1, L3 y L4 | Milestones v2.1 · p. 12 (6) | «Identifies the need for patient re-evaluation»; «evaluates the effectiveness of diagnostic and therapeutic interventions»; «Evaluates changes in clinical status…» | **VERIFIED** |
| RC · ME 4.1 | (A) Foundations: reevaluar al paciente y seguir los resultados de las investigaciones y la respuesta al tratamiento | Pathway v1.0 · pp. 22–23 | Describe directamente reevaluar y comparar con la respuesta | **VERIFIED** |
| RC · ME 4.1 | (B) Mismo hito como F2, hito 6 | EPA Guide v1.1 · p. 11 | Lenguaje idéntico, pero F2 se limita a presentaciones urgentes **no complicadas**. Los encuentros de R1-04 (perfiles PS001: fibrilación auricular con respuesta ventricular rápida en sepsis de origen urinario, con perfusión incompleta; `app.py:128`) no calzan con ese contexto | **PARTIAL** |
| RC · ME 4.1 | (B) TP6, hito 4 (plan seguro ante incertidumbre que sostiene el seguimiento de la respuesta) · C1, hito 6 (planes de cuidado continuo) | EPA Guide v1.1 · pp. 57 y 18 | Relacionados, pero centrados en planes, no en comprobar el efecto esperado | **PARTIAL** |
| RC · ME 2.4 | (A/B) TTD, iniciar monitorización e intervenciones urgentes en el inestable (TD1, hito 9) | Pathway v1.0 · pp. 15–16 · EPA Guide v1.1 · p. 5 | Monitorizar sí; formular una expectativa y compararla, no | **PARTIAL** |

### 3.3 R2-01 · Separar presión, flujo y perfusión (año 2)

**Conductas:**

- integrar varios datos circulatorios;
- proponer un mecanismo y una acción dirigida;
- revisar el mecanismo y la prioridad según la respuesta.

| Framework | Elemento exacto | Documento · página | Lenguaje de apoyo | Estado |
|---|---|---|---|---|
| ACGME | PC1 Emergency Stabilization, L3 | Milestones v2.1 · p. 7 (1) | «Identifies a patient with occult presentation that is at risk for instability or deterioration»; «Reassesses the patient’s status after implementing a stabilizing intervention» | **VERIFIED** |
| ACGME | PC4 Diagnosis, L3 | Milestones v2.1 · p. 10 (4) | «…modify a diagnosis based on a patient’s clinical course and additional data» | **VERIFIED** |
| ACGME | MK1 Scientific Knowledge, L2 y L3 | Milestones v2.1 · p. 15 (9) | «Demonstrates scientific knowledge of complex presentations and conditions»: describe conocimiento, y sólo se observa su aplicación en el mecanismo declarado | **PARTIAL** |
| ACGME | MK2 Treatment and Clinical Reasoning, L4 | Milestones v2.1 · p. 16 (10) | «Continually re-appraises one’s clinical reasoning…» | **VERIFIED** |
| RC · ME 1.6 | (A) Core: adaptar el cuidado a medida que evoluciona la complejidad o incertidumbre; usar razonamiento y juicio clínico aun sin información completa | Pathway v1.0 · p. 9 | Describe revisar mecanismo y prioridad según la evolución | **VERIFIED** |
| RC · ME 1.6 | (B) C1, hito 1 (razonamiento y juicio clínico aun sin información completa) | EPA Guide v1.1 · p. 18 | C1 incluye el shock, y el contexto es compatible | **VERIFIED** |
| RC · ME 2.4 | (A) Foundations o Core: planes de manejo · (B) C5, hito 6 | Pathway v1.0 · pp. 15–16 · EPA Guide v1.1 · p. 25 | Plan de manejo genérico; no describe proponer una acción dirigida a un mecanismo | **PARTIAL** |

## 4. Royal College: opciones A, B y C

- **A. Pathway to Competence como segunda fuente, a nivel de hito por etapa.**
  - Hay un vínculo VERIFIED para cada desafío: ME 2.2 para R1-03, ME 4.1 para
    R1-04 y ME 1.6 para R2-01.
  - No obliga a afirmar que el encuentro sea una instancia de una EPA concreta.
  - Coste estructural: una fuente nueva en `competency_mapping.SOURCES` y un
    tipo de vínculo sin EPA.
- **B. Hitos de la EPA Guide.**
  - Es VERIFIED sólo donde el contexto de la EPA calza: R1-03 → F1 hito 3, y
    R2-01 → C1 hito 1.
  - Para R1-04, el único hito con el lenguaje exacto está en F2, cuyo contexto
    (presentaciones no complicadas) contradice el encuentro. Queda PARTIAL.
  - Es el patrón que ya usan los 8 desafíos de sesgo (C5 y TP6).
- **C. Sólo ACGME al inicio.**
  - Siempre es posible.
  - Es la salida correcta para los códigos RC que quedan PARTIAL.

**Recomendación (METHODOLOGICAL REVIEW):**

1. **A como fuente RC primaria para estos tres desafíos locales**, sólo con los
   vínculos VERIFIED de la sección 3:
   - R1-03 → ME 2.2 Foundations (p. 11);
   - R1-04 → ME 4.1 Foundations (pp. 22–23);
   - R2-01 → ME 1.6 Core (p. 9).
2. **La EPA que observa cada hito queda como dato informativo, no como
   contribución a esa EPA.** Pathway marca esa EPA con sus etiquetas.
3. **C para los códigos RC PARTIAL.** ME 2.4 en los tres desafíos no se incorpora.
   Queda visible como no respaldado, en lugar de mantenerse para completar
   cobertura.
4. **B sólo como anotación opcional donde el contexto calza** (R1-03 → F1 h3;
   R2-01 → C1 h1), y sólo si el docente quiere esa lectura por EPA.
5. **Vínculos ACGME:** se incorporan los VERIFIED. PC5 en R1-03 y MK1 en R2-01
   son PARTIAL, y su uso lo decide el docente.

**Por qué no B como regla general.** Una EPA agrega condiciones que el desafío
local no controla: el foco de sus key features, el tipo de presentación y la
proporción de observaciones clínicas frente a simuladas. Afirmar la contribución
a una EPA cuyo contexto no coincide sería forzar cobertura (charter §9 y §43.11).

## 5. Qué no se hizo

- No se implementó ningún mapping.
- No se tocó `CHALLENGE_MAPPINGS`, `_ACGME` ni `_RC`.
- No se incorporaron R1-03, R1-04 ni R2-01 a Objective Progress.
- MK1 sigue sin usarse.
- La decisión está en DF-2 de `docs/COLA_DECISIONES_AI_ADVISOR.md`.
