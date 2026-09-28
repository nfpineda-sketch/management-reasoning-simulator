# ACEP 2016 · Marco POCUS para el simulador

**Estado:** fuente metodológica y de diseño, incorporada al repositorio en el
ciclo 7 (decisión docente del 2026-09-28). **No cambia nada por sí misma.**

- No cambia C14, casos, imágenes ni informes POCUS, mappings ni scoring.
- No es una rúbrica POCUS nueva ni un sistema de mapping: no hay puntajes,
  progreso, certificación ni estado de competencia ACEP.
- No debe usarse para modificar automáticamente casos, C14, imágenes, mappings
  ni scoring.
- Puede informar C14, el diseño POCUS futuro, las descripciones de componentes
  de la evidencia y la biblioteca visual futura
  (`docs/ARQUITECTURA_POCUS_OBJETIVO.md`).
- **ACEP 2016 es una fuente metodológica importante, pero no es
  automáticamente la definición única ni final de la competencia POCUS
  contemporánea** (sección 10).

**Resultado conceptual aceptado por el docente (ciclo 7).** ACEP concibe la
competencia en EUS como INDICATION → ACQUISITION → INTERPRETATION →
INTEGRATION INTO MANAGEMENT. El simulador actual observa:

| Componente | Hoy |
|---|---|
| Indicación / selección | Potencialmente observable |
| Interpretación clínica de un hallazgo POCUS **descrito** | Observable |
| Integración al manejo | Observable |
| Adquisición de la imagen / desempeño psicomotor | **No observable** |
| Reconocimiento directo en la imagen | **No observable de verdad**: el simulador entrega un informe escrito, no la imagen ni el video |

Por eso **la evidencia POCUS actual del simulador es una contribución PARCIAL a
la competencia POCUS, nunca la competencia completa.**

**Terminología (decisión docente).** Mientras el POCUS se entregue como texto,
no se escribe «resident recognized the ultrasound finding on imaging» si sólo
leyó un informe. Se escribe «resident interpreted the provided POCUS finding»
o «resident integrated the provided POCUS information into management». Vale
para documentación, faculty briefs y afirmaciones metodológicas futuras; no se
reescriben los textos históricos.

**Fuente única de las afirmaciones ACEP:** *Ultrasound Guidelines: Emergency,
Point-of-care, and Clinical Ultrasound Guidelines in Medicine*, policy
statement del American College of Emergency Physicians.

- Aprobado en junio de 2016. Versiones anteriores de 2001 y 2008 (p1).
- 46 páginas. © 2016 ACEP.
- El PDF no está en el repositorio y no debe agregarse.

**Cómo se cita:** «(p25, Appendix 1)» es la página del PDF y su sección. Las
citas textuales son breves; lo demás es paráfrasis.

**Tres rótulos:**

| Rótulo | Qué significa |
|---|---|
| **ESTABLISHED BY THIS SOURCE** | El texto lo nombra como uso, objetivo de aprendizaje o expectativa |
| **NOT ESTABLISHED BY THIS SOURCE** | El texto no lo nombra. **No significa que ACEP lo prohíba ni que sea inapropiado**: ACEP aclara que no incluir algo como core no le quita importancia ni implica que el médico de urgencia no pueda usarlo (p3–4, §2) |
| **INTERPRETACIÓN / PROPUESTA** | Lo que este documento o el proyecto agregan. Nunca se presenta como requisito ACEP |

**Cómo se leyó.**

- Texto extraído del PDF subido, página por página (pymupdf).
- Se leyeron completas las pp1–37 y las referencias 99–116 (pp42–43).
- Las figuras 1–3 (pp21–23) se renderizaron y se miraron.
- Se buscaron en todo el texto los términos que decide este análisis. Por
  ejemplo, «wall motion», «McConnell» e «hypokines» no aparecen ni una vez;
  «right ventric» aparece una sola vez, en el título de la referencia 114.
  «inferior vena cava» sí aparece (siete veces), aunque nunca la sigla «IVC».

---

## Resumen: qué es razonable esperar de un residente de urgencia según ACEP 2016

La pregunta docente se responde en cuatro pasos: SHOW → RECOGNIZE → INTERPRET
→ USE IN MANAGEMENT.

| Paso | Lo que establece la fuente | Página |
|---|---|---|
| **SHOW** (qué puede presentar un caso) | Hallazgos de las 12 aplicaciones core, dentro del alcance que ACEP describe para cada una. Lo mínimo para todo médico de urgencia: física, instrumentación, guía de procedimientos y FAST | p3, §2 · Figura 1, p21 |
| **RECOGNIZE** | Los hallazgos que cada aplicación enumera bajo «Recognize … findings and pitfalls» | pp28–31, Appendix 2 |
| **INTERPRET** | Distinguir lo normal, las variantes comunes y la patología, «from obvious to subtle». En el corazón, estimar cualitativamente la función del VI y la presión venosa central | p5, §3 · p29 |
| **USE IN MANAGEMENT** | Integrar los hallazgos «into individual patient care plans and management», incluido conocer la exactitud de cada examen. Repetir el examen ante deterioro o para monitorizar | p5, §3 · pp28–31 · p3–4 |

**Tres límites de la respuesta:**

- **No todo residente es experto en cada aplicación.** ACEP dice que no es
  obligatorio usar ni dominar cada aplicación core (p3, §2).
- **La competencia es por aplicación y requiere adquisición.** Por eso el
  simulador **nunca** puede afirmar competencia POCUS completa (sección 5).
- **El documento no menciona ni el VD ni la motilidad regional.** No los
  establece como expectativa del médico de urgencia (sección 4).

---

## 1. Modelo de competencia ACEP

### 1.1 Cuatro componentes, en secuencia (p5, §3 «Competency and Curriculum Recommendations»)

ACEP define la competencia en EUS (*emergency ultrasound*) con cuatro
componentes. Deben mantenerse **separados**:

| # | Componente | Qué incluye según la fuente |
|---|---|---|
| 1 | **Indications and contraindications** | Reconocer cuándo está indicado el examen y cuándo no |
| 2 | **Image acquisition** | Adquirir imágenes adecuadas: física, manejo del equipo («knobology») y protocolos en pacientes con distintas condiciones y hábitos corporales |
| 3 | **Image interpretation** | Simultánea con la adquisición. Distinguir anatomía normal, variantes comunes y patología «from obvious to subtle» |
| 4 | **Integration into management** | Integrar los hallazgos en el plan y el manejo de cada paciente. Una integración eficaz incluye conocer la exactitud de cada examen, además de documentación, control de calidad y reembolso |

La competencia exige desarrollar progresivamente conocimiento y habilidades
psicomotoras «for an expanding number of EUS applications». Es decir, se
construye **aplicación por aplicación** (p5, §3).

### 1.2 La misma secuencia en cada aplicación (Appendix 2, pp28–31)

Cada aplicación core repite cinco objetivos de aprendizaje:

1. Describir indicaciones, algoritmo clínico y limitaciones.
2. Realizar el protocolo (**adquisición**).
3. Identificar la anatomía relevante.
4. Reconocer los hallazgos patológicos y sus trampas (*pitfalls*).
5. Integrar los hallazgos en el manejo del paciente y del servicio.

### 1.3 Categorías funcionales (p3, §2 · Tabla 1, p19 · Figura 1, p21)

- **Resucitativa:** en una reanimación aguda.
- **Diagnóstica.**
- **Basada en síntoma o signo:** dentro de una vía clínica, por ejemplo disnea.
- **Guía de procedimientos.**
- **Terapéutica y de monitorización.**

**Vías integradas.** Una vía por síntoma o signo, como *Shock* o *Dyspnea*,
puede considerarse una aplicación integrada que combina varias aplicaciones
(p3, §2). Ejemplos: el POCUS cardíaco combinado con el abdominal, el aórtico o
el torácico en el shock no traumático indiferenciado, y el FAST o el E-FAST en
el trauma (p4, §2).

**Repetición y monitorización.** Un examen puede hacerse una vez, repetirse
«due to clinical need or deterioration» o usarse para monitorizar cambios
fisiológicos o patológicos (p2–3, §2). El POCUS cardíaco puede monitorizar el
corazón durante la reanimación, en respuesta a fluidos o fármacos (p4, §2).

### 1.4 El flujo clínico (Figura 3, p23)

Cinco pasos:

1. Evaluación inicial: decisión de hacer US y orden.
2. Preparación del equipo.
3. Adquisición.
4. Interpretación: interpretación inicial registrada y comunicación de los
   hallazgos al paciente.
5. Documentación: informe, archivo de imágenes y gestión de datos.

### 1.5 Cómo evalúa ACEP la competencia (pp6–8, §3; Appendix 3, pp32–33)

- **Métodos:**
  - supervisión en tiempo real;
  - sesiones de control de calidad con revisión de imágenes;
  - evaluaciones estandarizadas de conocimiento;
  - OSCE;
  - observación directa estandarizada (SDOT);
  - evaluaciones con simulación (p6).
- **Umbrales:**
  - 25–50 exámenes revisados por aplicación;
  - 150–300 exámenes en total;
  - 5 procedimientos guiados, o un módulo en simulador de tareas (p7).
- **Milestone.** ACEP cita el *Patient Care Milestone 12* de ACGME/ABEM
  (edición 2013) como descripción de la secuencia de aprendizaje (p8).
- **Simulación.** ACEP dice que «appropriately designed cases» evalúan
  reconocer indicaciones, demostrar adquisición e interpretación y aplicar los
  hallazgos al manejo (p6, §3).
  - El contexto es el de los simuladores de ultrasonido de alta fidelidad
    (p6). **No valida un simulador de manejo sin imágenes como éste**
    (sección 10).

---

## 2. Aplicaciones core relevantes

**Las 12 aplicaciones core** (p3, §2 · Figura 1, p21 · §9, p18):

1. Trauma
2. Embarazo (intrauterine pregnancy)
3. Cardíaca/evaluación hemodinámica
4. Aorta abdominal
5. Tórax/vía aérea
6. Vía biliar
7. Vía urinaria
8. TVP
9. Partes blandas/musculoesquelético
10. Ocular
11. Intestino
12. Guía de procedimientos

**Criterios para ser core** (p3, §2): uso extendido, base de evidencia
significativa, singularidad diagnóstica o para decidir, importancia en el
diagnóstico y la atención de urgencia, o avance tecnológico.

**Otras aplicaciones, complementarias o emergentes** (Tabla 2, p20):

- *Advanced Echo*
- ecocardiografía transesofágica
- anexos
- testículo
- Doppler transcraneal
- vascular
- estudios con contraste
- ORL
- infectología

**Relevancia para el banco actual (INTERPRETACIÓN):**

| Aplicación | Relevancia | Dónde aparece en el simulador |
|---|---|---|
| **Trauma (FAST/E-FAST)** | Alta | Informe E-FAST de cinco ventanas (`efast_report.py`); 2 casos de trauma |
| **Cardíaca/hemodinámica** | Alta | Corazón y VCI del protocolo POCUS fijo (`pocus_report.SECTIONS`) en los 31 casos |
| **Tórax/vía aérea** | Alta | Deslizamiento pleural, líneas B, consolidación y derrame en los 31 casos |
| **TVP** | Media | Compresión femoral y poplítea en los 31 casos; determinante en los 2 TEP |
| **Vía urinaria** | Media | La ecografía renal es un **estudio formal**, no POCUS (`clinical_cases.py:42-45`; decisión H) |
| **Guía de procedimientos** | Baja hoy | Ningún procedimiento guiado por US está modelado; C4 = NO |
| **Aorta abdominal** | Contexto | Tres líneas de aorta, normales en todos los casos (`clinical_cases.py:71-75`) |
| **Embarazo** | Contexto | No modelado (TD-22; `AUDITORIA_DF23_CICLO6.md` §4) |
| **Biliar, partes blandas, ocular, intestino** | Sin representación | — |

**El protocolo POCUS fijo del simulador** (corazón, VCI, pulmón, aorta y venas)
se parece a las vías integradas de ACEP para *Shock* o *Dyspnea* (p3–4, §2),
más que a un ecocardiograma completo.

---

## 3. Matriz de aplicaciones

**Sólo con lo que dice el documento.** ACEP no enumera las trampas de cada
aplicación: para las indicaciones, limitaciones y protocolos detallados remite
al *Emergency Ultrasound Imaging Criteria Compendium* (2014), que no se tuvo a
la vista (p3 §2, p28 y referencia 6). La columna de limitaciones recoge, por
eso, las características de prueba que el texto sí da.

| APPLICATION | ACEP CORE? | INDICATIONS | EXPECTED ACQUISITION | EXPECTED RECOGNITION / INTERPRETATION | EXPECTED MANAGEMENT INTEGRATION | LIMITATIONS / PITFALLS | SOURCE PAGE / SECTION |
|---|---|---|---|---|---|---|---|
| **Trauma / FAST / E-FAST** | Sí | Líquido o aire anormal en el torso; trauma cerrado y penetrante, todas las edades. El neumotórax se sumó como E-FAST | Realizar el protocolo de trauma. Anatomía: pleura, diafragma, VCI, pericardio, hígado, bazo, riñones, vejiga, próstata, útero | Neumotórax, hemotórax, hemopericardio, actividad cardíaca, estado de volumen, hemoperitoneo, con sus trampas | En el manejo del paciente, del servicio y de desastres. En un ECA, el grupo con FAST fue antes a pabellón, con menos TC | FAST: sensibilidad 90 % y especificidad 99 % en trauma cerrado; 91 % y 100 % en penetrante. Trampas: no enumeradas | p24 (Appendix 1, Trauma) · p28 (Appendix 2, Trauma) |
| **Cardíaca / hemodinámica** | Sí | Derrame y taponamiento, actividad cardíaca, contractilidad global, volumen venoso central. Hipotensión indiferenciada; insuficiencia cardíaca y disnea; reanimación y paro | Ventanas subcostal, paraesternal y apical; planos de cuatro cámaras, eje largo y eje corto. Anatomía: pericardio, cavidades, válvulas, aorta y VCI | Paro cardíaco; derrame con o sin taponamiento; dilatación de la raíz aórtica o de la aorta descendente. **Estimar** cualitativamente la función del VI y la PVC | Guiar la evaluación hemodinámica. Monitorizar la respuesta a fluidos o fármacos. Guiar la pericardiocentesis. Precarga, función y poscarga como herramienta diagnóstica y de monitorización | Derrame: sensibilidad 96–100 %, especificidad 98–100 %. En un estudio, la asistolia ecográfica predijo mortalidad en el paro (VPP 100 %). Trampas: no enumeradas | p4 (§2) · p25 (Appendix 1, Emergent Echocardiography and Hemodynamic Assessment) · p29 (Appendix 2, Echocardiography and HD Assessment) |
| **Tórax / vía aérea** | Sí | Derrame pleural, neumotórax, trastornos intersticiales e inflamatorios. Tráquea y vía aérea; confirmación de intubación en el paro | Protocolos para neumotórax, derrame pleural y síndromes alvéolo-intersticiales | Hallazgos de patología torácica y sus trampas. Anatomía traqueal y esofágica en los procedimientos | En el manejo del paciente y del servicio | Neumotórax en trauma torácico cerrado: sensibilidad 92–98 %, especificidad 99 %. La consolidación no es un objetivo nombrado; la neumonía se menciona sólo en niños (p4) | p4 · p26 (Appendix 1, Thoracic-Airway) · p30 (Appendix 2, Thoracic-Airway) |
| **TVP** | Sí | TVP por compresión multinivel de venas proximales, sobre todo de la extremidad inferior | Extremidades superiores e inferiores: identificar el vaso, comprimirlo, Doppler de variación respiratoria y aumento | Hallazgos de TVP y sus trampas | En el manejo del paciente y del servicio. Disposición más rápida que con el estudio radiológico (95 frente a 225 min) | Revisión sistemática: sensibilidad 95 % y especificidad 96 %. Trampas: no enumeradas | p25 (Appendix 1, DVT) · pp29–30 (Appendix 2, DVT) |
| **Vía urinaria** | Sí | Hidronefrosis y estado vesical. Junto con el examen de orina y la clínica, ayuda a diferenciar el cólico renal | Realizar el protocolo. Anatomía: corteza y pelvis renal, uréter, vejiga, hígado, bazo | Hidronefrosis, cálculos renales, masas renales, volumen vesical | En el manejo del paciente y del servicio | Sensibilidad 75–87 % y especificidad 82–89 % frente a TC | p25 (Appendix 1, Urinary Tract) · p29 (Appendix 2, Urinary Tract) |
| **Guía de procedimientos** | Sí | Acceso vascular; drenajes (tóraco-, pericardio-, para- y artrocentesis); bloqueos nerviosos | Abordajes transversal y longitudinal. Lista: acceso venoso central y periférico, confirmación de intubación, pericardiocentesis, paracentesis, toracocentesis, cuerpo extraño, aspiración vesical, artrocentesis, **marcapasos y captura**, absceso | Hallazgos y trampas de cada procedimiento | En el manejo del paciente y del servicio | Cateterismo central: éxito 98 % con guía dinámica, 82 % estática y 64 % por reparos. Umbral: 5 procedimientos revisados o un módulo en simulador | p4 (§2) · p7 (§3) · p27 (Appendix 1) · p31 (Appendix 2) |
| **Aorta abdominal** *(contexto)* | Sí | Aneurisma; ocasionalmente disección | Protocolo con técnica de medición. Anatomía: aorta y ramas, VCI, cuerpos vertebrales | Aneurisma y disección | En el manejo del paciente y del servicio | Sensibilidad 100 % en dos estudios | p24 (Appendix 1, AAA) · p29 (Appendix 2, Abdominal Aorta) |
| **Embarazo** *(contexto)* | Sí | Embarazo intrauterino, ectópico, frecuencia cardíaca fetal, edad gestacional, líquido libre | Vistas transabdominal y transvaginal | Estructuras embrionarias y su ubicación; hallazgos de ectópico | En el manejo del paciente y del servicio | Ectópico: sensibilidad 76–90 % y especificidad 88–92 % | p24 (Appendix 1, Pregnancy) · pp28–29 (Appendix 2, First-Trimester Pregnancy) |

---

## 4. Expectativas cardíacas y hemodinámicas

**La regla de esta sección:** sólo cuenta lo que el texto nombra. Lo que es
técnicamente posible pero no aparece queda como NOT ESTABLISHED BY THIS SOURCE.

| Ítem | Veredicto | Fuente |
|---|---|---|
| Ventanas estándar | **ESTABLISHED.** Subcostal, paraesternal y apical; cuatro cámaras, eje largo y eje corto | p29 |
| Derrame pericárdico | **ESTABLISHED** | p25 · p29 · p28 (hemopericardio en trauma) |
| Taponamiento | **ESTABLISHED.** «pericardial effusions with or without tamponade»; guía de la pericardiocentesis | p25 · p29 · p4 · p31 |
| Actividad cardíaca | **ESTABLISHED.** Reconocer el paro; distinguir la AESP verdadera de la hipovolemia profunda | p25 · p29 · p28 · p4 |
| Función cualitativa del VI | **ESTABLISHED.** «global assessment of contractility»; «Estimate qualitative left ventricular function» | p25 · p29 |
| Volumen o presión venosa central | **ESTABLISHED.** «detection of central venous volume status», precarga, «central venous pressure» | p25 · p29 · p28 (estado de volumen en trauma) |
| VCI | **ESTABLISHED como anatomía a identificar.** El método (diámetro, colapso) **no se especifica**. La literatura citada para la evaluación hemodinámica usa el índice de cava (referencias 108, 110 y 116, p43): es una cita, no el texto | p29 · p28 · p25 |
| Anormalidades groseras de las cavidades | **NOT ESTABLISHED BY THIS SOURCE.** Las cavidades aparecen sólo como anatomía que identificar | p29 |
| Dilatación o disfunción del VD | **NOT ESTABLISHED BY THIS SOURCE.** El texto no nombra el VD. Lo único es el título de la referencia 114 (marcadores de disfunción del VD en TEP normotenso), citada para la evaluación hemodinámica: una cita, no una expectativa | p25 · p43 |
| Motilidad regional | **NOT ESTABLISHED BY THIS SOURCE.** No aparece en ninguna parte | — |
| Ecocardiografía cuantitativa avanzada | **NOT ESTABLISHED como core.** *Advanced Echo* y la transesofágica son aplicaciones complementarias o emergentes. Las aplicaciones cardiopulmonares avanzadas se integran en cuidados críticos. La medición automática de parámetros es un tema futuro. La función del VI es cualitativa en los objetivos | p20 (Tabla 2) · p4 · p17 · p29 |
| *(Extra)* Dilatación de la raíz aórtica o de la aorta descendente | **ESTABLISHED** | p29 |
| *(Extra)* Monitorizar la respuesta a fluidos o fármacos | **ESTABLISHED** | p4 · p25 · p3 |

### El protocolo del simulador frente a ACEP y frente a la lista de la EPA C14

- **Protocolo del simulador:** `pocus_report.SECTIONS`.
- **Lista de la EPA C14:** la del Royal College (EPA Guide v1.1, p. 42), según
  `docs/C14_DECISIONES_A_H.md`. No se volvió a verificar aquí.

| Estructura del informe POCUS | ACEP 2016 | Lista de la EPA C14 |
|---|---|---|
| Contractilidad del VI, cualitativa | ESTABLISHED | Sí (función global del VI) |
| Motilidad regional (en los informes de SCA) | **NOT ESTABLISHED** | No |
| Tamaño del VD y su relación con el VI; signo D; McConnell | **NOT ESTABLISHED** | No |
| Pericardio | ESTABLISHED | Sí |
| VCI (diámetro y colapso) | ESTABLISHED (PVC y volumen; método no especificado) | **No** |
| Deslizamiento pleural (neumotórax) | ESTABLISHED | Sí |
| Líneas B (síndrome alvéolo-intersticial) | ESTABLISHED | No |
| Consolidación | Parcial: «inflammatory disorders» (p26); no es un objetivo nombrado (p30) | No |
| Derrame pleural y hemotórax | ESTABLISHED | Sí |
| Raíz aórtica y aorta descendente | ESTABLISHED | No (sí el aneurisma abdominal) |
| Aorta abdominal | ESTABLISHED | Sí (aneurisma) |
| Compresión femoral y poplítea | ESTABLISHED | No |

**Cómo se marcan las diferencias (decisión docente).** Lo que esta fuente no
establece como expectativa general del residente de urgencia (motilidad
regional, el VD tal como lo usan algunos casos, eco cuantitativa avanzada) se
marca **SOURCE LIMITATION / REVIEW NEEDED**. No se eliminan capacidades del
simulador sólo porque no aparezcan en este documento.

**Qué muestra la triangulación (INTERPRETACIÓN):**

- **ACEP respalda cosas que la lista de la EPA no incluye:** la VCI y el
  volumen, la monitorización, las líneas B y la TVP. Con eso, la decisión C
  (volumen) y la parte de TVP de la decisión G quedan dentro de lo que ACEP
  espera de un médico de urgencia.
- **Ninguna de las dos fuentes respalda** la motilidad regional (decisión A) ni
  el VD (parte de la decisión G y todo `acs_54m_inferior`).
- **Eso ya se sabía de la lista de la EPA.** La facultad aprobó esas filas con
  el principio del alcance local (`C14_DECISIONES_A_H.md`, «Una pregunta de
  fondo común…»). ACEP no las invalida, pero tampoco las sostiene.

---

## 5. Lo que el simulador puede y no puede observar

**Hecho del repositorio.** El simulador **no muestra imágenes ni clips de
ultrasonido.**

- El POCUS es un informe escrito con una estructura fija.
  - Dice hallazgos, no conclusiones: «Findings, not interpretation»
    (`pocus_report.py:7-12`).
  - Lo que el caso no documenta sale como «Not documented».
- El E-FAST es un informe escrito de cinco ventanas (`efast_report.py`); el
  motor registra qué ventana se miró primero (`efast_report.cardiac_first`).
- La limitación declarada de C14 ya lo dice: *«Does not assess probe handling,
  image acquisition, or independent interpretation of a complete ultrasound
  study.»* (`objectives.py:104`).
- Las «imágenes» del banco son fotos del paciente, no ultrasonido.

**Una precisión que el docente aceptó (ciclo 7).** La interpretación que el
simulador observa es la **interpretación clínica de un hallazgo POCUS
descrito**: el residente interpreta lo que significa el hallazgo escrito, pero
no reconoce la patología en una imagen, que es la parte visual de lo que ACEP
llama interpretación (p5).

| Componente ACEP | ¿Observable en el simulador? | Qué se observa | Qué queda fuera |
|---|---|---|---|
| 1 · Indicación / contraindicación (p5; pp28–31) | **SÍ, directo** para decidir pedir el estudio | Pedir POCUS o E-FAST, cuándo, y la pregunta clínica si se escribe (Management Trace). En el E-FAST, el orden de las ventanas | Contraindicaciones (no modeladas). Elegir ventanas o transductor: el protocolo es fijo y siempre informa todo |
| 2 · Adquisición (p5) | **NO** | Nada | Todo: física, equipo, protocolo, calidad de imagen, hábito corporal |
| 3 · Interpretación (p5) | **SÍ** como interpretación clínica de un hallazgo descrito. **NO** como reconocimiento directo en la imagen | Si el residente nombra el hallazgo relevante del informe y dice qué implica (por ejemplo, «VCI 1.0 cm con colapso >50 %» leída como poco llena) | Reconocer en la imagen lo normal, las variantes y la patología «from obvious to subtle» |
| 4 · Integración al manejo (p5; pp28–31) | **SÍ, directo** en lo simulado | Relacionar el hallazgo con el modelo de trabajo; la orden que sigue por el hallazgo; la reevaluación con un POCUS repetido **donde el motor hace evolucionar el hallazgo** | Documentación, control de calidad, comunicación al paciente, reembolso (p5; Figura 3, p23) |
| 4b · Exactitud del examen (p5, dentro de la integración) | **PARCIAL**, sólo en casos con un hallazgo normal o discordante plausible | No tranquilizarse con un POCUS normal (Wellens; el VD de `acs_54m_inferior`) | La facultad decidió que no tranquilizarse es razonamiento diagnóstico y no C14 (decisión B). Ver sección 8 |
| Umbrales, credencialización, milestone (pp7–8, p11) | **NO APLICA** | — | Un encuentro simulado no es un examen de US revisado; nunca cuenta para los 25–50 exámenes por aplicación |

**Consecuencia (coherente con DIRECT/PARTIAL).**

- La contribución del simulador a la competencia POCUS es, como máximo,
  **PARCIAL**: indicación, interpretación clínica de hallazgos descritos e
  integración al manejo.
- **La adquisición y la interpretación de imágenes quedan siempre fuera**.
- El simulador no puede afirmar competencia POCUS, ni por aplicación ni en
  general.

---

## 6. Propuesta de operacionalización de C14 (NO implementada)

**Qué no es:**

- No es un puntaje.
- No cambia la meta de 50 (EPA Guide, p.36; `objectives.py:24`).
- No cambia Objective Progress.
- No cambia qué casos son YES o NO.
- No agrega una rúbrica.

**Qué es.** Una forma de **describir** qué componentes mostró una observación
C14 confirmada por la facultad, con rótulos y nunca con pesos, igual que
DIRECT/PARTIAL (`docs/OBSERVATION_OPPORTUNITIES.md` §5).

| # | Componente | Ancla ACEP | Evidencia posible en el Trace | Qué queda fuera |
|---|---|---|---|---|
| 1 | **Indicación / selección** | «recognize the indications and contraindications» (p5); «Describe the indications…» en cada aplicación (pp28–31) | Pide POCUS o E-FAST cuando el cuadro lo justifica, y dice para qué | Contraindicaciones; elegir ventana o transductor |
| 2 | **Reconocimiento / interpretación del hallazgo** | Interpretación (p5); «Recognize…» (pp28–31) | Nombra el hallazgo relevante del informe y su significado | El reconocimiento visual: el simulador da el hallazgo escrito |
| 3 | **Integración clínica** | «integrate EUS exam findings into individual patient care plans» (p5), incluida la exactitud del examen | Relaciona el hallazgo con el diagnóstico de trabajo o el modelo hemodinámico, y con sus límites | Documentación, control de calidad, comunicación |
| 4 | **Consecuencia de manejo** | «…and management» (p5); «Integrate…» (pp28–31) | Una orden, o una orden retenida, **por** el hallazgo: volumen, vasopresor, drenaje, reperfusión | — |
| 5 | **Reevaluación / monitorización** | «repeated due to clinical need or deterioration, or used for monitoring» (p2–3); respuesta a fluidos o fármacos (p4); herramienta de monitorización (p25) | Repite el POCUS tras la intervención y decide con el resultado | Sólo es observable donde el motor mueve el hallazgo (`AUDITORIA_DF23_CICLO6.md` §5, columna C) |

**Relación con lo que ya existe (INTERPRETACIÓN).** La columna «EXPECTED TRACE
EVIDENCE» de cada fila YES ya sigue este patrón.

- «requests POCUS and names…» cubre los componentes 1 y 2.
- «…because of them» cubre el 4.
- «reassesses with POCUS…» cubre el 5.
- El componente 3 queda implícito.

La operacionalización, por lo tanto, sería sobre todo **rotular lo que ya se
pide**, no pedir algo nuevo.

**Dónde está disponible hoy el componente 5.** Según la columna C de
`AUDITORIA_DF23_CICLO6.md` §5:

- **Sí:** las neumonías, los edemas pulmonares y el hemotórax.
- **Limitado:** las HDA (el VI no cambia), la pielonefritis (la VCI no cambia),
  el trauma de extremidad y las paredes del SCA.

**Si la facultad la quisiera, haría falta decidir:**

1. Si los rótulos se agregan a la confirmación de C14. Eso toca la estructura
   de evidencia: es una decisión metodológica, no una corrección.
2. Si el componente 4b, la exactitud del examen, pertenece a C14 aunque la
   decisión B lo dejó en el razonamiento diagnóstico.
3. Cómo se nombra, en cada fila, la aplicación ACEP y si el hallazgo está
   ESTABLISHED.

---

## 7. Principios de diseño del POCUS del caso

En el simulador, la «imagen» POCUS es el **texto del informe**
(`clinical_cases.POCUS`, `efast_report`). Los principios valen para ese texto y
para imágenes futuras, si las hubiera.

| # | Principio | Origen |
|---|---|---|
| P1 | **Mostrar la mínima información clínicamente plausible necesaria para crear la oportunidad de observación buscada** | Principio docente (2026-09-28). No es de ACEP |
| P2 | **POCUS de urgencias, no ecocardiograma completo.** Hallazgos focalizados y cualitativos | ACEP: examen «focused, goal-directed» (p13); función del VI cualitativa (p29); eco avanzada como complementaria (p20); el estándar se juzga «within the limits of the clinical scenario» y no se compara con otras especialidades (p15) |
| P3 | **Lo normal, lo no diagnóstico, lo limitado y lo ambiguo son válidos** cuando son plausibles | Principio docente. ACEP: la interpretación abarca lo normal, las variantes y la patología «from obvious to subtle» (p5). La documentación puede ser breve y registrar presencia o ausencia (p13). Las sensibilidades por debajo de 100 % muestran que hay falsos negativos (pp24–26) |
| P4 | **Hallazgos, no conclusiones.** El residente interpreta e integra | Regla del proyecto (`pocus_report.py:7-12`). Coherente con separar adquisición, interpretación e integración (p5) |
| P5 | **Lo que no se documenta sale como «Not documented»**, nunca como normal | Regla del proyecto (`pocus_report.py:14-15`). Coherente con documentar presencia o ausencia (p13) |
| P6 | **Un estudio repetido cambia sólo si cambia la fisiología que el motor modela** | Criterio C de `AUDITORIA_DF23_CICLO6.md` §5. Coherente con la monitorización (p3–4, p25) |
| P7 | **La palanca de una oportunidad C14 debería estar dentro de lo que ACEP establece**, o su fila debería decir explícitamente que no lo está | **PROPUESTA** de este documento. Extiende la recomendación común de `C14_DECISIONES_A_H.md` («cada fila dirá si el hallazgo es de la lista o no») a ACEP |

**Una tensión, sin acción (REVIEW, no cambio).**

- El protocolo fijo del simulador siempre informa el VD («RV size and relation
  to LV»), y los informes de SCA describen la motilidad regional.
- Ninguna de las dos cosas está establecida por ACEP para urgencias.
- Con P1–P3, una redacción más conservadora sería una decisión de contenido
  futura, por ejemplo «not assessed» o «limited views».
  - Exigiría aprobación docente y volver a aprobar el texto en español del caso.
  - **No se propone para el ciclo 7 sin su decisión**, y no se toca nada aquí.

---

## 8. Implicaciones para los casos actuales

**Qué se reutiliza.** La auditoría C14 existente: `C14_TABLA_FINAL.md`, las
decisiones A–H y `AUDITORIA_DF23_CICLO6.md` §5–6. **No se re-audita** y **no se
cambia ningún caso.**

**Qué se clasifica.** Sólo los casos en que ACEP cambia o toca un supuesto,
con cuatro clases:

- CONSISTENT WITH ACEP;
- REVIEW NEEDED;
- OUTSIDE EXPECTED SCOPE;
- TOO ADVANCED.

**Decisión docente (ciclo 7).** Los casos REVIEW NEEDED (`acs_61m_posterior`,
`acs_52m_de_winter`, `pulmonary_embolism_61m`, `renal_colic_34m`,
`bradycardia_avb3_78f` y `acs_48m_wellens`) **no se cambian automáticamente**
por este análisis. Quedan para una revisión metodológica posterior, en la cola
de decisiones, y no bloquean TD-21 ni TD-26. El C14 actual se evalúa con la
capacidad actual del simulador (POCUS en texto); la biblioteca visual futura
exigirá revisarlo aparte.

**Ningún caso es TOO ADVANCED.** Nada del banco es cuantitativo: no hay TAPSE
ni fracción de eyección (`pocus_report.py:10-11`). Además, ACEP no dice qué
hallazgos pertenecen a *Advanced Echo* (p20). Llamar «avanzados» al signo D o
al de McConnell sería inferencia.

| Caso | C14 hoy | Hallazgo que lleva la oportunidad | Clase ACEP | Lectura |
|---|---|---|---|---|
| `acs_61m_posterior` | YES (A) | Hipocinesia posterior | **OUTSIDE EXPECTED SCOPE → REVIEW NEEDED** | La palanca es la motilidad regional, no establecida por ACEP (ni por la lista de la EPA; ya se sabía en la decisión A). El residente no tiene que detectarla, porque recibe el hallazgo escrito. Lo que ACEP pone en duda es que un POCUS de urgencias lo informe con fiabilidad. **Sin cambio**; decisión docente futura: mantener por alcance local o restringir |
| `acs_52m_de_winter` | YES (A) | Acinesia anterior y apical | **OUTSIDE EXPECTED SCOPE → REVIEW NEEDED** | Igual que el anterior |
| `acs_54m_inferior` | NOT REVIEWED → **NO** (decidido) | VD «free wall contracts normally»; pared inferior | **OUTSIDE EXPECTED SCOPE — respalda C14 NO** | Ver 8.1 |
| `acs_66f_nonst` | NO (A) | Hipocinesia inferolateral leve (texto) | OUTSIDE EXPECTED SCOPE (el hallazgo) | Sin efecto sobre C14 |
| `acs_48m_wellens` | NO (B) | «Normal wall motion in every segment at rest» | OUTSIDE EXPECTED SCOPE (el hallazgo) · **REVIEW NEEDED (baja)** | ACEP pone la exactitud del examen dentro de la integración (p5). Es un argumento débil para revisar la decisión B; no alcanza para reabrirla |
| `acs_70f_left_main` | YES (clara) | Función global del VI | **CONSISTENT WITH ACEP** | ACEP establece reconocer el síndrome intersticial (p30) y la insuficiencia cardíaca con disnea (p25). La fila 4 de DF-23 (pulmón «No B-lines» con congestión) gana peso: al informe le falta un hallazgo ACEP que la fisiología del caso implica |
| `pulmonary_embolism_61m` | YES (G) | VD > VI, signo D, McConnell; TVP poplítea | **REVIEW NEEDED** | La TVP es CONSISTENT: compresión proximal, core (p25, pp29–30). El VD, que es lo que en shock empuja a reperfundir, está OUTSIDE EXPECTED SCOPE. La fila acepta «…or the DVT», así que la evidencia ACEP queda disponible |
| `pulmonary_embolism_33f` | YES (G) | VD levemente dilatado; TVP poplítea | **CONSISTENT (TVP) · REVIEW NEEDED (baja, parte VD)** | TVP → anticoagular antes de confirmar es integración ACEP. «Withholds thrombolysis… with the RV stated» depende del VD |
| `gi_bleed_57m`, `gi_bleed_72f`, `pneumonia_46f`, `pneumonia_83m`, `obstructive_pyelonephritis_58f` | YES (C) | VCI y VI cualitativo | **CONSISTENT WITH ACEP** | ACEP **refuerza** la decisión C más allá de la lista de la EPA: PVC, volumen y monitorización (p25, p29, pp3–4). La reevaluación (componente 5) es limitada en las HDA y en la pielonefritis (§5 de DF-23) |
| `pulmonary_edema_58m`, `pulmonary_edema_75f` | YES (claras) | Líneas B, VI, VCI | **CONSISTENT WITH ACEP** | p25 (insuficiencia cardíaca y disnea) · p30 · p29 |
| `trauma_limb_hemorrhage_27m`, `trauma_hemothorax_41m` | YES (claras) | E-FAST | **CONSISTENT WITH ACEP** | p24 · p28 |
| `renal_colic_34m` | NO (H) | La ecografía renal modelada como estudio formal | **REVIEW NEEDED** | ACEP cuenta la ecografía urinaria al lado de la cama (hidronefrosis, vejiga) como aplicación core (p25, p29). La premisa de la decisión H («estudio formal, no POCUS») es una elección de modelado. Con el marco ACEP, la ecografía que decide esta disposición sería EUS, y eso empujaría a YES. En contra: C14 es la EPA del Royal College, cuya lista no incluye la hidronefrosis. **Decisión docente; sin cambio** |
| `obstructive_pyelonephritis_58f` | YES (C) | *(parte renal)* | REVIEW NEEDED (baja) | La palanca VCI es CONSISTENT. La ecografía renal plantea la misma pregunta que en `renal_colic_34m` |
| `bradycardia_avb3_78f` | NO (E) | Captura del marcapasos | **REVIEW NEEDED (baja)** | ACEP lista «pacemaker placement and capture» en la guía de procedimientos (p31). El NO descansa en que el motor no refleja la captura en el POCUS, un límite del motor y no una ausencia clínica de oportunidad. Sigue NO con el motor actual |
| `asthma_24f`, `asthma_49m` | NO (D) | Neumotórax tras ventilar | **CONSISTENT (el NO se sostiene)** | ACEP establece detectar el neumotórax como core (p24, p26, p30). Eso sube el valor educativo del rediseño que la decisión D ya separó como decisión aparte. No está autorizado: es contenido nuevo del caso |

**Sin cambio de supuesto (los otros 10 casos; 21 + 10 = 31):**

- `anaphylaxis_29f`, `anaphylaxis_63m_betablocked`;
- `bradycardia_ccb_68m`, `bradycardia_bb_54f`, `bradycardia_hyperk_63m`;
- `hypoglycemia_28m`, `hypoglycemia_76f`, `hypoglycemia_54m_thiamine`;
- `opioid_35m`, `opioid_67f`.

En ellos, los hallazgos están dentro del alcance ACEP, pero el manejo no
depende de ellos: es el criterio §33, y ACEP no lo cambia.

### 8.1 `acs_54m_inferior` bajo ACEP

**Pregunta 1.** ¿Es razonable esperar que un residente de urgencia identifique
el compromiso del VD con el POCUS mostrado?

- **Con esta fuente, no es una expectativa establecida.** El texto no nombra
  el VD: ni en la aplicación cardíaca (p25) ni en sus objetivos (p29).
- **La referencia 114 no la establece.** Es un estudio de disfunción del VD en
  TEP normotenso, no en infarto del VD, y aparece como cita (p43).
- **Además, el simulador no pide reconocer imágenes.** El residente recibe el
  texto «RV free wall contracts normally». La pregunta práctica es cuánto
  creerle, y ya la analizó `AUDITORIA_DF23_CICLO6.md` §6.2–6.3.

**Pregunta 2.** ¿Crea ese POCUS una oportunidad C14?

- **No hay evidencia fuerte para reabrir. C14 = NO se sostiene.**
- **Lo que ACEP sí establece en este caso no cambia el manejo propio del caso:**
  - la función cualitativa del VI: la pared inferior la decide el ECG;
  - la VCI: indeterminada, y en el motor no cambia con volumen ni con nitrato;
  - la ausencia de derrame y una raíz aórtica normal (p29).
- **ACEP sí refuerza un componente.** El argumento más fuerte por YES era
  excluir disección o derrame antes de los antitrombóticos (DF-23 §6.4). ACEP
  lo vuelve una expectativa establecida (p29).
  - Pero vale para todo SCA, y las decisiones A–H no lo contaron: no es una
    palanca propia de este caso.
- **Un matiz, sin fuerza suficiente para reabrir.** Que un VD de aspecto normal
  no excluye su compromiso es «conocer la exactitud del examen», que ACEP pone
  dentro de la integración (p5). No basta:
  - ACEP no establece la evaluación del VD, así que conocer sus límites
    tampoco es una expectativa ACEP;
  - el manejo lo deciden el V4R y la hemodinamia, no el POCUS (DF-23 §6.4).
- **No se fuerzan anormalidades del VD ni de la VCI.** Con P1–P3, el POCUS
  actual es admisible como hallazgo cualitativo no contributivo.

**Fundamento sugerido** para escribir el NO. La redacción final es docente; se
agrega la frase ACEP a la de `AUDITORIA_DF23_CICLO6.md` §6.4:

> *Inferior STEMI with right ventricular involvement: the ECG, the right-sided
> leads and the haemodynamic response decide the antiplatelet, the nitrate and
> the cautious volume. The qualitative POCUS shows the inferior wall and a right
> ventricle that looks normal, which cannot exclude its involvement; right
> ventricular assessment is not among the emergency echocardiography
> expectations of the ACEP 2016 guideline (pp25, 29), and in the engine its RV
> and IVC do not change with volume or nitrate. Not being reassured by it is
> diagnostic reasoning, not C14 (decisions A and B).*

### 8.2 Cobertura de las aplicaciones core en el banco (INTERPRETACIÓN; no es una propuesta de casos)

| Representadas como palanca C14 | Presentes sólo como contexto | Ausentes |
|---|---|---|
| Trauma; cardíaca/hemodinámica; tórax (líneas B, hemotórax); TVP (en los TEP) | Aorta (siempre normal); vía urinaria (estudio formal); tórax en el asma (el neumotórax, nombrado por el evento) | Embarazo (TD-22), biliar, partes blandas, ocular, intestino, guía de procedimientos. **Tampoco hay un caso de derrame o taponamiento ni de paro**, los hallazgos cardíacos más establecidos por ACEP (p25, p29) |

Crear casos no está autorizado. Esta tabla sólo sirve para priorizar las
brechas del banco (DF-25).

---

## 9. Implicaciones para la evidencia por componente

**Cadena evaluada:**

> ENCOUNTER → POCUS OPPORTUNITY → RESIDENT ACTION / INTERPRETATION →
> MANAGEMENT INTEGRATION → FACULTY CONFIRMATION → EVIDENCE UNIT →
> C14 / FRAMEWORK CONTRIBUTION

| Eslabón | En el sistema hoy | Encaje con ACEP |
|---|---|---|
| Encounter | Encuentro con su base congelada | — |
| POCUS opportunity | Fila C14 del banco, congelada con el encuentro (`OBSERVATION_OPPORTUNITIES.md` §1–2) | Bueno. Falta, opcionalmente, nombrar la aplicación ACEP y si el hallazgo está ESTABLISHED (P7) |
| Resident action / interpretation | Management Trace: el pedido, lo que nombra, lo que razona | Indicación: directa. Interpretación: **sólo del hallazgo descrito**. Adquisición: ausente |
| Management integration | Órdenes y reevaluación en el Trace | Directa, dentro de lo que el motor modela |
| Faculty confirmation | Obligatoria: nada se registra sin la valoración docente (§1) | Coherente con la revisión de calidad de ACEP (pp6–7, p14) en espíritu. **No la reemplaza** |
| Evidence unit | Una observación confirmada por encuentro y objetivo (`mrs_progress_observations`), con procedencia | Bueno |
| C14 / framework contribution | Las R* llevan contribuciones DIRECT/PARTIAL con componente y limitación. **C14 no lleva contribuciones por componente**: su limitación está en el objetivo (`objectives.py:104`) | **Brecha descriptiva.** Una observación C14 no dice qué componentes mostró. Ver la propuesta de la sección 6 |

**Evidencia de adquisición frente a evidencia de interpretación y manejo.**

- **La evidencia de adquisición sólo puede venir de otras fuentes:**
  - escaneo supervisado con revisión de calidad;
  - SDOT;
  - OSCE;
  - simuladores de ultrasonido con transductor (pp6–8, pp32–33).
- **El modelo ya previó ese camino.** Una fuente externa futura necesitaría su
  propia tabla, con `evidence_source` propio (`OBSERVATION_OPPORTUNITIES.md`
  §4, «Multisource»). No se implementó y **no se propone implementarlo ahora**.
- **La contribución del simulador a C14 debe describirse como PARCIAL** frente
  a la EPA completa y frente a la competencia ACEP.

**Tres cuidados:**

1. **Nunca contar encuentros simulados como exámenes ACEP.** No son los 25–50
   por aplicación, ni los 150–300 en total, ni la credencialización
   (pp7–8, p11).
2. **La meta de 50 es la de la EPA del Royal College (p.36)**, con condiciones
   que el simulador no reproduce (`objectives.py:21-28`). ACEP cuenta por
   aplicación; si interesara describir por aplicación, sería un rótulo, no una
   meta nueva. **La meta no cambia.**
3. **El milestone PC12 que cita ACEP (p8) es de la edición 2013.** El proyecto
   usa ACGME EM 2021 (`acgme_em_2021`). Todo vínculo POCUS con un milestone
   habría que verificarlo contra el documento vigente. Sería un mapping no
   aprobado: **no se activa**.

---

## 10. Limitaciones de usar este documento de 2016

0. **No es la definición única ni final.** ACEP 2016 es una fuente
   metodológica importante, pero no es automáticamente la definición única ni
   final de la competencia POCUS contemporánea. Más adelante podrá
   contrastarse con guías ACEP más nuevas, ACGME, ABEM, SAEM/AEUS y otros
   marcos validados de competencia POCUS. En el ciclo 7 no se abre una
   revisión bibliográfica nueva (decisión docente).
1. **Fecha.** Aprobado en junio de 2016, con evidencia citada hasta ese año. La
   práctica POCUS evolucionó después.
   - Esta sesión **no verificó** si existe una revisión posterior.
   - Si existe, prevalece donde difiera.
2. **Naturaleza.** Es una declaración de política sobre alcance, formación,
   credencialización, calidad y reembolso, no un instrumento de evaluación.
   - Los objetivos del Appendix 2 son «recommended learning objectives» para un
     currículo completo (p28), no mínimos para cada médico.
   - No es obligatorio dominar cada aplicación (p3).
3. **Silencio no es exclusión.** Que el texto no establezca el VD o la
   motilidad regional no significa que ACEP los desaconseje (p3–4).
   - «NOT ESTABLISHED BY THIS SOURCE» limita lo que puede **afirmarse como
     expectativa**, no lo que un médico puede hacer.
4. **Faltan los detalles.** Las indicaciones, limitaciones y protocolos
   detallados, incluidas las trampas, están en el *Imaging Criteria Compendium*
   (2014), que no se revisó (p28; referencia 6).
5. **La simulación que ACEP valida es otra.** Lo que el documento dice de la
   simulación (p6) se refiere a simuladores de ultrasonido. No valida un
   simulador de manejo sin imágenes.
6. **Contexto estadounidense.** ACGME, ABEM, CPT y la Joint Commission (pp8,
   p12, pp15–16). Trasladarlo a otro programa exige juicio local.
7. **No habla de C14 ni del Royal College.** La correspondencia entre los
   componentes ACEP y la EPA C14 es de este documento. Es una interpretación
   que requiere aprobación docente.
8. **Cifras no re-verificadas.** Las características de prueba (pp24–27) se
   transcriben como las da el texto, sin verificar sus estudios originales.
9. **Derechos.** © 2016 ACEP. Las citas son breves y el PDF queda fuera del
   repositorio.
