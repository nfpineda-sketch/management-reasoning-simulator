# Borrador · Oportunidad de observar TD1, F1, C1, C3 y C4 en los 31 casos del banco

Ciclo 5 del AI Advisor · instrucciones docentes 59B, 59C y 59D · 2026-09-28.

**Estado: BORRADOR. NO APROBADO. NADA DE ESTO ESTÁ EN EL BANCO.**

- **Un borrador no es una oportunidad aprobada** (DRAFT ≠ APPROVED OPPORTUNITY).
- **Ningún caso declara TD1, F1, C1, C3 ni C4.** Los cinco siguen con la regla de
  transición: observables en todo encuentro hasta que usted revise y apruebe
  (`observation_opportunities.TRANSITION_OBJECTIVES`).
- **No se cambió ningún dato clínico, evento ni puntaje.** No se llamó a ningún
  proveedor de IA ni se corrió el motor: lo que se cita del motor sale de leer
  su código y sus constantes.
- **Las dudas están agrupadas en 8 decisiones clínicas** (TDFC-1 a TDFC-8) en
  `DECISIONES_TDFC.md`. Se numeran para no confundirlas con las letras A–H de
  C14.
- **La matriz de cobertura del banco** está en `MATRIZ_OPORTUNIDADES.md`, generada
  por `generar_matriz.py` a partir de la tabla de estados de este documento.

## Resumen

| Objetivo | YES | NO | UNCERTAIN | Decisiones que resuelven las dudas |
|---|---|---|---|---|
| TD1 · Reconocer la inestabilidad e iniciar soporte | 26 | 2 | 3 | TDFC-1 |
| F1 · Iniciar la reanimación del paciente crítico | 23 | 5 | 3 | TDFC-2 |
| C1 · Manejar la reanimación del paciente crítico | 18 | 8 | 5 | TDFC-3, TDFC-4, TDFC-5 |
| C3 · Manejar vía aérea y ventilación | 6 | 18 | 7 | TDFC-5, TDFC-6 |
| C4 · Manejar sedación y analgesia procedimental | 0 | 27 | 4 | TDFC-7, TDFC-8 |
| **Total** | **73** | **60** | **22** | 8 decisiones |

155 combinaciones (31 casos × 5 objetivos). Las 22 dudas se reducen a 8
preguntas; ninguna combinación depende de más de una.

## Método

### Qué se preguntó en cada objetivo

El principio docente de C14, adaptado: **¿existe en este encuentro una decisión o
acción clínicamente relevante que pueda razonablemente observarse para este
objetivo?** No basta con que algo pueda ocurrir: la oportunidad tiene que venir
del diseño del caso.

| Objetivo | Pregunta adaptada | Alcance local (`objectives.py`) | Referencia Royal College |
|---|---|---|---|
| **TD1** | ¿Llega el paciente inestable, o se vuelve inestable por diseño, de modo que reconocerlo e iniciar el soporte sea una decisión real? | Reconocer la inestabilidad en los hallazgos entregados y justificar el soporte inicial y su reevaluación. No evalúa activar ayuda real, trabajo en equipo ni soporte vital básico manual. | EPA Guide 2018 v1.1, p. 4–5: paro cardiorrespiratorio, arritmia inestable, shock, dificultad respiratoria y compromiso neurológico; hito 8 (ECG con condiciones que exigen intervención inmediata). |
| **F1** | ¿Exige el paciente priorizar e iniciar intervenciones de reanimación (oxigenación y ventilación, presión, arritmia crítica) y valorar su respuesta? | Priorizar e iniciar la reanimación disponible y valorar su respuesta. No evalúa asistir a un equipo real ni procedimientos. | p. 10: etapas iniciales de la reanimación; excluye la reanimación compleja una vez tratadas las amenazas iniciales. |
| **C1** | ¿Trae el caso una condición que amenaza la vida (shock, insuficiencia respiratoria, sepsis grave, paro) cuya reanimación exige integrar varias decisiones, reevaluar y revisar el modelo de trabajo? | Integrar decisiones de reanimación, reevaluación y revisión del modelo de trabajo. No evalúa liderazgo real ni toda la amplitud de la enfermedad crítica. | p. 18: condición médica o quirúrgica que amenaza la vida. El trauma es C2 (p. 20), deshabilitada. |
| **C3** | ¿Hay una decisión real sobre oxígeno, preparación de la vía aérea o soporte ventilatorio, con respuesta que reevaluar? | Razonar sobre oxígeno, preparación de la vía aérea y soporte ventilatorio, y reevaluar. No evalúa laringoscopía, intubación ni ventilación manual. | p. 22: intubación en vía aérea normal o difícil prevista, estrategia ventilatoria en falla hipoxémica o ventilatoria, cuidado posintubación. |
| **C4** | ¿Trae el caso un procedimiento que exija decidir sedación o analgesia, anticipar sus efectos y reevaluar? | Justificar la sedación procedimental disponible, anticipar sus consecuencias y reevaluar. Contexto de sedación limitado. | p. 23: sedación y analgesia sistémica para procedimientos diagnósticos o terapéuticos. |

Las páginas son las de la edición de 59 páginas (v1.1), la misma que verificó
`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md`. `objectives.TARGET_SOURCE` cita la
edición de 51 páginas; ya está documentado que sólo cambia la paginación.

**Un vacío de definición.** En `objectives.py`, TD1, F1, C1, C3 y C4 tienen
título, meta, alcance, limitación y fuente de la meta. **No tienen
`observable_behaviors` ni `evidence_requirements`**: esos campos existen sólo
para los objetivos R* (`competency_mapping`). El borrador usó el alcance, la
limitación y los rasgos clave de la EPA.

### De dónde sale cada fila

Sólo del diseño clínico del caso, nunca de resultados futuros (lo que hagan los
residentes del piloto no dice si la oportunidad existía):

- **Lo que el caso trae:** `clinical_cases.py` (presentación, historia, examen,
  observables de llegada, estudios, diagnóstico, rasgos clave, foco de manejo y
  declaraciones del motor) y `hypoglycemia_catalog.py` para las tres
  hipoglicemias.
- **Lo que el motor modela:** `family_engine.py` y sus módulos
  (`acs_reperfusion`, `asthma_complications`, `pe_obstruction`, `opioid_reversal`,
  `glucose_rescue`, `anaphylaxis_reaction`, `trauma_hemorrhage`,
  `bradycardia_support`, `analgesia`, `airway_pharmacology`).
- **Lo que la declaración espera:** `case_assessment_bank.py` (D1–D5 con sus
  ventanas, eventos críticos y límites del motor).

### Reglas del borrador

- **Una oportunidad no es una observación.** YES sólo haría evaluable el objetivo
  en encuentros nuevos; la evidencia la produce el residente y la observación la
  confirma la docencia.
- **NO significa no evaluable**, nunca una falla ni un cero.
- **La evidencia esperable orienta; no es una lista cerrada.**
- **Diseño y consecuencia se separan.** Cuenta lo que el paciente trae al llegar
  y lo que el motor produce con un manejo correcto cuando el caso y su
  declaración lo sostienen (decisión TDFC-5). No crea oportunidad lo que sólo
  aparece tras un error: FV por reperfusión tardía, agotamiento del asma
  subtratada, barotrauma, abstinencia por naloxona, sobrecarga transfusional.
- **TD1, F1 y C1 se separan así.** TD1: reconocer la inestabilidad y dar el primer
  paso. F1: las intervenciones iniciales de reanimación y su respuesta. C1: más
  de un problema de reanimación, o una segunda fase que obliga a revisar el
  plan. Una misma decisión puede ser evidencia para más de un objetivo; lo
  valora la docencia.
- **Cifras del motor.** Cuando una fila cita una evolución («SpO₂ bajo 90 % hacia
  el minuto 60»), es un cálculo desde las constantes del código, no una
  medición.

### Límites del motor que pesan en estas filas

- **Ventilador:** la intubación es ejecutable en todas las familias, pero ajustar
  el ventilador después sólo existe en asma.
- **Sedación procedimental:** fuera de la intubación sólo cobra presión
  (propofol, midazolam). No modela profundidad, depresión respiratoria ni el
  dolor del procedimiento.
- **Nombre de acción compartido:** la acción `procedural_sedation` también
  registra la inducción de la intubación.
- **Anafilaxia:** el estridor resta 6 puntos de SpO₂ y sólo la adrenalina lo
  alivia. No hay obstrucción completa ni intubación difícil modeladas.

## Estados por caso

La tabla que lee `generar_matriz.py`. Entre paréntesis, la decisión que resuelve
cada duda.

<!-- estados-tdfc:inicio -->
| Case ID | Familia | TD1 | F1 | C1 | C3 | C4 |
|---|---|---|---|---|---|---|
| `acs_54m_inferior` | acs | YES | YES | UNCERTAIN (TDFC-5) | NO | NO |
| `acs_66f_nonst` | acs | UNCERTAIN (TDFC-1) | NO | NO | NO | NO |
| `acs_61m_posterior` | acs | UNCERTAIN (TDFC-1) | NO | NO | NO | NO |
| `acs_52m_de_winter` | acs | UNCERTAIN (TDFC-1) | NO | NO | NO | NO |
| `acs_48m_wellens` | acs | NO | NO | NO | NO | NO |
| `acs_70f_left_main` | acs | YES | YES | YES | UNCERTAIN (TDFC-5) | NO |
| `anaphylaxis_29f` | anaphylaxis | YES | YES | YES | YES | NO |
| `anaphylaxis_63m_betablocked` | anaphylaxis | YES | YES | YES | UNCERTAIN (TDFC-6) | NO |
| `asthma_24f` | asthma | YES | YES | UNCERTAIN (TDFC-3) | UNCERTAIN (TDFC-6) | NO |
| `asthma_49m` | asthma | YES | YES | YES | YES | NO |
| `bradycardia_ccb_68m` | bradycardia | YES | YES | YES | NO | NO |
| `bradycardia_avb3_78f` | bradycardia | YES | YES | YES | NO | UNCERTAIN (TDFC-7) |
| `bradycardia_bb_54f` | bradycardia | YES | YES | YES | NO | NO |
| `bradycardia_hyperk_63m` | bradycardia | YES | YES | YES | NO | NO |
| `gi_bleed_57m` | gi_bleed | YES | YES | YES | NO | NO |
| `gi_bleed_72f` | gi_bleed | YES | YES | YES | NO | NO |
| `hypoglycemia_28m` | hypoglycemia | YES | UNCERTAIN (TDFC-2) | NO | NO | NO |
| `hypoglycemia_76f` | hypoglycemia | YES | UNCERTAIN (TDFC-2) | NO | NO | NO |
| `hypoglycemia_54m_thiamine` | hypoglycemia | YES | UNCERTAIN (TDFC-2) | NO | NO | NO |
| `opioid_35m` | opioid | YES | YES | YES | YES | NO |
| `opioid_67f` | opioid | YES | YES | YES | YES | NO |
| `pneumonia_46f` | pneumonia | YES | YES | YES | UNCERTAIN (TDFC-6) | NO |
| `pneumonia_83m` | pneumonia | YES | YES | YES | UNCERTAIN (TDFC-6) | NO |
| `pulmonary_edema_58m` | pulmonary_edema | YES | YES | YES | YES | NO |
| `pulmonary_edema_75f` | pulmonary_edema | YES | YES | YES | YES | NO |
| `pulmonary_embolism_33f` | pulmonary_embolism | YES | YES | UNCERTAIN (TDFC-3) | UNCERTAIN (TDFC-6) | NO |
| `pulmonary_embolism_61m` | pulmonary_embolism | YES | YES | YES | UNCERTAIN (TDFC-6) | NO |
| `renal_colic_34m` | renal_colic | NO | NO | NO | NO | UNCERTAIN (TDFC-8) |
| `obstructive_pyelonephritis_58f` | renal_colic | YES | YES | YES | NO | NO |
| `trauma_limb_hemorrhage_27m` | trauma | YES | YES | UNCERTAIN (TDFC-4) | NO | UNCERTAIN (TDFC-7) |
| `trauma_hemothorax_41m` | trauma | YES | YES | UNCERTAIN (TDFC-4) | NO | UNCERTAIN (TDFC-7) |
<!-- estados-tdfc:fin -->

## Detalle por caso

Cada bloque es la fila del caso. Componente y evidencia se dan para YES y
UNCERTAIN. Abreviaturas: PAS (presión sistólica), FC, FR, SpO₂, llene (capilar),
VMNI, VD/VI, HDA, TEP.

### 1. `acs_54m_inferior` · acs

IAM inferior con compromiso del VD. Llegada: 100/64 · FC 58 · SpO₂ 96 % · FR 22 ·
llene 3 s · extremidades frías · diaforesis marcada.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Perfusión límite (PAS 100 con FC 58, frialdad, llene 3 s) en un IAM inferior con VD. El motor produce un bloqueo AV completo a los 45 min de oclusión, antes de que la arteria pueda abrirse (puerta-balón 90 min). | Reconocer la hipoperfusión incipiente y la bradiarritmia, e iniciar soporte y vigilancia. | Nombra la perfusión límite y el riesgo del VD; monitoriza; ante el bloqueo, lo nombra como inestable y actúa; fija cuándo reevaluar. |
| F1 | YES | La presión depende de la precarga: el nitrato la desploma (100/64 → 67/45 en 10 min, según la auditoría del caso) y el volumen la recupera. El bloqueo exige manejar una arritmia crítica. | Priorizar volumen prudente sobre el nitrato y tratar el bloqueo, valorando la respuesta. | Evita el nitrato por el VD; bolo acotado y reevalúa la PA; atropina y, si no basta, marcapaso con salida y captura confirmada. |
| C1 | UNCERTAIN (TDFC-5) | No llega en shock. El shock aparece por diseño con el bloqueo y la deriva del VD mientras espera la reperfusión, si el encuentro sigue abierto. | Integrar ritmo, precarga del VD y reperfusión pendiente, y revisar el plan según la respuesta. | Relaciona la caída de PA con el bloqueo y el VD; ajusta volumen, atropina o marcapaso; sostiene la reperfusión; dice qué vigila hasta hemodinamia. |
| C3 | NO | SpO₂ 96 % y pulmones limpios; un infarto inferior con VD casi no congestiona en el motor. No hay decisión de oxígeno ni de ventilación. | — | — |
| C4 | NO | Ningún procedimiento con sedoanalgesia en el diseño. La morfina está modelada (caída de precarga ×2,2 en el VD), pero es analgesia del cuadro. | — | — |

**Nota.** Se sugiere no activar ninguna fila de este caso antes de decidir la
auditoría del VD (`docs/AUDITORIA_ACS_54M_INFERIOR.md`): el POCUS dice VD normal
y puede llevar a un modelo de trabajo equivocado en F1 y C1.

### 2. `acs_66f_nonst` · acs

SCA sin supradesnivel. Llegada: 146/86 · FC 102 · SpO₂ 95 % · FR 24 · troponina
180 ng/L · síntomas persistentes.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | UNCERTAIN (TDFC-1) | Estable, con infradesnivel del ST y síntomas en curso: hay isquemia que exige tratamiento inmediato (hito 8), pero no inestabilidad fisiológica. | Reconocer en el ECG la isquemia en curso e iniciar tratamiento y monitorización. | Nombra la isquemia sin supradesnivel como amenaza; indica antiagregante y monitorización; dice qué cambiaría la urgencia. |
| F1 | NO | Normotensa, bien perfundida y sin hipoxemia: el antiagregante y la evaluación monitorizada no son reanimación. | — | — |
| C1 | NO | Sin shock, falla respiratoria ni sepsis. Es un SCA sin oclusión con angiografía diferible, contenido de C5 (no habilitada). | — | — |
| C3 | NO | SpO₂ 95 % con esfuerzo leve; el oxígeno no es una decisión del caso. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 3. `acs_61m_posterior` · acs

Oclusión posterior que el ECG estándar muestra en espejo. Llegada: 132/80 · FC 88 ·
SpO₂ 96 % · FR 20.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | UNCERTAIN (TDFC-1) | Hemodinámicamente estable. La condición que exige intervención inmediata (reperfusión) está en un ECG que sólo la muestra en espejo; no hay inestabilidad fisiológica. | Reconocer la oclusión posterior en el ECG e iniciar la reperfusión con monitorización. | Nombra el patrón posterior como oclusión o pide derivadas posteriores; activa la reperfusión sin esperar supradesnivel; monitoriza. |
| F1 | NO | No requiere reanimación. Con la arteria cerrada, el motor agrega poca congestión en este territorio (2 a 3 puntos de SpO₂ hacia el minuto 90). | — | — |
| C1 | NO | Sin condición de reanimación crítica: el caso enseña a reconocer la oclusión (C5). | — | — |
| C3 | NO | SpO₂ 96 %, sin esfuerzo. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 4. `acs_52m_de_winter` · acs

Oclusión proximal de la DA con patrón de De Winter. Llegada: 128/78 · FC 96 ·
SpO₂ 95 % · FR 24 · frío y sudoroso.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | UNCERTAIN (TDFC-1) | Estable al llegar. La intervención inmediata es la reperfusión que el ECG exige antes del supradesnivel; el sudor y la frialdad son autonómicos, no shock. | Reconocer la oclusión en el ECG y activar la reperfusión con monitorización. | Compara las derivadas y nombra el equivalente de oclusión; activa la reperfusión ahora; monitoriza. |
| F1 | NO | No requiere reanimación al llegar. El modelo general congestiona el pulmón mientras espera (SpO₂ bajo 90 % sólo pasado el minuto 80), sin apoyo en el caso ni en la declaración. Se revisó en TDFC-5 y quedó fuera. | — | — |
| C1 | NO | Sin shock ni falla respiratoria; la congestión tardía del modelo no configura una reanimación crítica. | — | — |
| C3 | NO | SpO₂ 95 % al llegar; la hipoxemia tardía queda fuera por la razón dada en F1. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 5. `acs_48m_wellens` · acs

Estenosis crítica de la DA, transitoriamente reperfundida. Llegada: 138/84 · FC 76 ·
SpO₂ 97 % · sin dolor.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | NO | Sin dolor, signos normales y arteria abierta: no hay inestabilidad que reconocer. La decisión es angiografía programada y no provocar; la FV sólo aparece tras una prueba de esfuerzo, que es un error. | — | — |
| F1 | NO | Nada que reanimar. | — | — |
| C1 | NO | Sin condición crítica. | — | — |
| C3 | NO | Sin compromiso respiratorio. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 6. `acs_70f_left_main` · acs

Lesión de tronco o de tres vasos con hipoperfusión. Llegada: 104/66 · FC 112 ·
SpO₂ 94 % · FR 26 · llene 3 s · lactato 3,1 · crépitos basales.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Hipoperfusión (frialdad, llene 3 s, lactato 3,1, PAS 104 con FC 112) y congestión en una lesión proximal: preshock cardiogénico. | Reconocer el preshock cardiogénico e iniciar soporte y vigilancia mientras se organiza la reperfusión. | Nombra la hipoperfusión y su origen isquémico; monitoriza; indica soporte; fija la reevaluación. |
| F1 | YES | La declaración espera «addresses the hypoperfusion» y acepta oxígeno y volumen prudente; el motor responde mal al volumen en este perfil. | Priorizar un soporte hemodinámico prudente y valorar la respuesta. | Limita o evita el volumen por la congestión, o da un bolo acotado; considera soporte; compara PA, perfusión y respiración tras cada medida. |
| C1 | YES | Shock cardiogénico en evolución: con cada minuto de oclusión el motor baja la PAS (unos 9 mmHg a los 90 min) y congestiona el pulmón, aun con activación inmediata. | Integrar soporte, congestión y reperfusión, y revisar el plan según la respuesta. | Relaciona hipoperfusión y congestión con el tronco; ajusta volumen, oxígeno o VMNI y soporte; sostiene la urgencia invasiva; dice qué vigila. |
| C3 | UNCERTAIN (TDFC-5) | Llega con SpO₂ 94 % y crépitos. Por diseño (solicitud docente del 2026-09-22) la congestión progresa con la arteria cerrada (SpO₂ bajo 90 % hacia el minuto 60) y la VMNI la alivia en el motor. La declaración nombra el oxígeno. | Decidir oxígeno o VMNI ante la congestión que progresa, y reevaluar. | Nombra la congestión (crépitos, radiografía, caída de SpO₂); indica oxígeno con meta o VMNI; reevalúa SpO₂, FR y PA. |
| C4 | NO | Sin procedimiento. | — | — |

### 7. `anaphylaxis_29f` · anaphylaxis

Anafilaxia con compromiso de vía aérea superior, broncoespasmo y shock
distributivo. Llegada: 84/46 · FC 126 · SpO₂ 91 % · FR 28 · estridor.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock (84/46) con estridor, sibilancias y SpO₂ 91 % minutos después de una exposición. Sin adrenalina, el motor la lleva al paro en unos 25 min. | Reconocer la anafilaxia con compromiso de vía aérea y circulación, e iniciar el tratamiento. | Nombra la reacción y su gravedad; indica adrenalina IM con dosis antes que otra cosa; fija la reevaluación al plazo de la vía IM. |
| F1 | YES | Adrenalina, volumen y oxígeno son las intervenciones iniciales declaradas (D3); el motor muestra el efecto de la vía IM a los 4 min, aproximadamente. | Priorizar adrenalina IM y sumar volumen y oxígeno, valorando la respuesta a tiempo. | Adrenalina 0,5 mg IM; volumen y oxígeno junto a ella, no en su lugar; reevalúa PA, SpO₂ y estridor tras la dosis. |
| C1 | YES | Shock con vía aérea comprometida: puede requerir otra dosis o una infusión, y el motor trae una reacción bifásica 75 min después de estabilizada. | Integrar la respuesta a la adrenalina, la vía aérea y el volumen, y reconocer el retorno. | Compara la respuesta con la esperada; escala a infusión si no alcanza; decide observación; reconoce y trata el retorno. |
| C3 | YES | Amenaza de vía aérea superior (estridor, angioedema de labios) que el motor cobra en SpO₂ y que sólo la adrenalina alivia. La declaración nombra la vía aérea (D1, D4) y el oxígeno (D3); preparar la vía aérea es ejecutable. No hay obstrucción completa ni intubación difícil modeladas. | Anticipar una vía aérea difícil, dar oxígeno y reevaluar la vía aérea tras la adrenalina. | Nombra el estridor como amenaza; indica oxígeno; prepara la vía aérea o pide ayuda; reevalúa el estridor tras la dosis. |
| C4 | NO | Sin procedimiento. | — | — |

### 8. `anaphylaxis_63m_betablocked` · anaphylaxis

Anafilaxia refractaria en un paciente betabloqueado. Llegada: 76/42 · FC 64 ·
SpO₂ 89 % · FR 26 · somnoliento.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock (76/42) sin taquicardia compensadora, somnolencia y SpO₂ 89 % tras una picadura. | Reconocer el shock anafiláctico con una FC inapropiadamente normal e iniciar el tratamiento. | Nombra el shock y la reacción; adrenalina con dosis y vía; reevalúa. |
| F1 | YES | Adrenalina, volumen y oxígeno son ejecutables y declarados; el motor responde a un tercio por el betabloqueo. | Priorizar adrenalina y volumen, y valorar una respuesta que se queda corta. | Adrenalina IM, volumen y oxígeno; compara PA y FC tras la dosis. |
| C1 | YES | Anafilaxia refractaria: la adrenalina rinde un tercio y la palanca del caso es la historia (atenolol) y el glucagón. Obliga a revisar el modelo de trabajo. | Integrar la falta de respuesta, buscar su causa y cambiar de estrategia. | Compara lo esperado con lo observado; identifica el betabloqueo; da glucagón o inicia infusión; pide ayuda nombrando la refractariedad. |
| C3 | UNCERTAIN (TDFC-6) | Hipoxemia (SpO₂ 89 %, PaO₂ 57 mmHg) con sibilancias, sin estridor ni hipercapnia (PaCO₂ 36); la D3 de la familia espera oxígeno. | Titular oxígeno y reevaluar. | Indica oxígeno con dispositivo y flujo; reevalúa SpO₂ y esfuerzo. |
| C4 | NO | Sin procedimiento. | — | — |

### 9. `asthma_24f` · asthma

Crisis asmática grave. Llegada: 138/84 · FC 126 · SpO₂ 90 % · FR 34 · PEF 35 % ·
habla en frases · PaO₂ 59 · PaCO₂ 31.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Dificultad respiratoria grave (FR 34, SpO₂ 90 %, PEF 35 %, habla en frases). | Reconocer la gravedad de la obstrucción e iniciar tratamiento y reevaluación. | Nombra la obstrucción grave por el esfuerzo o el PEF; trata antes de completar el estudio; fija la reevaluación. |
| F1 | YES | Broncodilatador, corticoide y oxígeno son ejecutables y declarados; el motor mueve el esfuerzo y la SpO₂ con cada uno. | Priorizar broncodilatación, corticoide y oxígeno, y valorar la respuesta. | Broncodilatador repetido o continuo; corticoide; oxígeno; reevalúa esfuerzo y SpO₂. |
| C1 | UNCERTAIN (TDFC-3) | Hipoxemia sin hipercapnia ni shock; la primera línea suele estabilizarla. La falla ventilatoria sólo llega si el tratamiento es insuficiente (fatiga modelada). | Integrar la escalada terapéutica según la respuesta. | Compara la respuesta; agrega magnesio o adrenalina si no alcanza; decide escalar o mantener; define destino. |
| C3 | UNCERTAIN (TDFC-6) | SpO₂ 90 % con oxígeno declarado; el motor castiga la intubación prematura (alerta, SpO₂ ≥ 92 % y mejorando) y la tardía. | Titular oxígeno y decidir si escalar el soporte o no intubar. | Oxígeno con meta; reevalúa; justifica no intubar mientras mejora, o escalar si se agota. |
| C4 | NO | Sin procedimiento. | — | — |

### 10. `asthma_49m` · asthma

Asma casi fatal con falla ventilatoria. Llegada: 142/86 · FC 132 · SpO₂ 89 % ·
FR 30 · somnoliento · pH 7,30 · PaCO₂ 51.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Falla ventilatoria: somnolencia, entrada de aire muy pobre, pH 7,30 y PaCO₂ 51. | Reconocer la fatiga y la hipercapnia como amenaza e iniciar soporte. | Nombra la falla ventilatoria, no sólo la obstrucción; actúa con esa urgencia; fija la reevaluación. |
| F1 | YES | Broncodilatador, corticoide y soporte ventilatorio están declarados (D3); el motor responde por separado a la obstrucción y al soporte. | Priorizar el soporte ventilatorio sin dejar el tratamiento de la obstrucción, y valorar la respuesta. | Broncodilatador y corticoide; VMNI o preparación de la intubación; reevalúa esfuerzo, gases y SpO₂. |
| C1 | YES | Falla ventilatoria: decidir VMNI o intubación a tiempo (el motor la califica de prematura, oportuna o tardía), programar el ventilador y manejar la hipotensión posintubación y el barotrauma. | Integrar soporte, ventilación y complicaciones, y revisar el plan según la respuesta. | Relaciona gases y conciencia con la decisión de intubar; ajusta el ventilador ante auto-PEEP o hipotensión; reevalúa. |
| C3 | YES | El soporte ventilatorio es «the decision the case turns on» (D3) y tiene evento crítico propio. En el banco, sólo esta familia permite ajustar el ventilador después de intubar. | Decidir VMNI o intubación a tiempo, programar la ventilación para el atrapamiento aéreo y reevaluar. | Nombra fatiga e hipercapnia; prepara volumen e inducción (ketamina); intuba a tiempo o justifica VMNI; frecuencia baja y espiración larga; revisa plateau y PA. |
| C4 | NO | La inducción y la sedación posintubación son parte de C3 (hito 5 de C3). El motor registra la ketamina de inducción como `procedural_sedation`: una propuesta de C4 por esa acción sería contenido de C3. | — | — |

### 11. `bradycardia_ccb_68m` · bradycardia

Intoxicación por verapamilo con bradicardia y shock. Llegada: 74/44 · FC 38 ·
SpO₂ 96 % · llene 4 s · glicemia 214.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Bradicardia inestable: FC 38, PAS 74, frialdad y llene 4 s tras un colapso. | Reconocer la bradicardia con shock e iniciar soporte mientras se busca la causa. | Nombra la inestabilidad; actúa antes de completar el estudio; fija la reevaluación. |
| F1 | YES | Atropina, calcio y glucagón son ejecutables; el motor responde según la causa. | Priorizar el soporte del ritmo y el antídoto, y valorar la respuesta. | Atropina y, al no responder, calcio con dosis y vía; reevalúa FC, PA y perfusión tras cada intento. |
| C1 | YES | Shock tóxico sostenido: el antídoto correcto responde y se desvanece, y el motor no ofrece la terapia definitiva. Obliga a reevaluar, repetir y pedir ayuda. | Integrar antídoto, soporte y su desvanecimiento, y decidir continuidad. | Reconoce que la atropina no basta; da el antídoto de la causa; lo repite o agrega soporte; pide toxicología o UCI. |
| C3 | NO | SpO₂ 96 %, respiración normal. | — | — |
| C4 | NO | El marcapaso no es la respuesta del diseño; la sedoanalgesia dependería de que el residente lo eligiera. | — | — |

### 12. `bradycardia_avb3_78f` · bradycardia

Bloqueo AV completo infranodal. Llegada: 78/46 · FC 32 · SpO₂ 95 % · FR 20 ·
somnolienta · síncopes repetidos.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Bradiarritmia inestable: FC 32, PAS 78, somnolencia y síncopes. | Reconocer el bloqueo con hipoperfusión e iniciar el soporte del ritmo. | Nombra el bloqueo como inestable; actúa; fija la reevaluación. |
| F1 | YES | Atropina (que no responde en un bloqueo infranodal) y marcapaso transcutáneo con salida y umbral de captura (70 mA). | Priorizar el soporte eléctrico del ritmo y valorar la respuesta. | Atropina o marcapaso de inicio; frecuencia y salida; confirma captura con pulso y PA. |
| C1 | YES | Shock por bloqueo: revisar el plan cuando la atropina no responde, confirmar la captura mecánica (evento crítico) y organizar el marcapaso definitivo. | Integrar la falta de respuesta, la captura y la continuidad. | Deja la atropina tras su fracaso; confirma captura con pulso y PA; ajusta salida; pide marcapaso definitivo y dice qué vigila. |
| C3 | NO | SpO₂ 95 % y FR 20; somnolienta sin compromiso de la vía aérea. | — | — |
| C4 | UNCERTAIN (TDFC-7) | El caso trae un procedimiento doloroso (marcapaso transcutáneo) en una paciente somnolienta con PAS 78. La sedoanalgesia es ejecutable, pero la declaración no la espera y el motor no modela el dolor del marcapaso. | Elegir y dosificar analgesia o sedación para el marcapaso sin agravar la hipotensión, y reevaluar. | Indica analgésico o sedante con dosis; justifica la elección por la PA y la conciencia; reevalúa PA, FR y conciencia. |

### 13. `bradycardia_bb_54f` · bradycardia

Intoxicación por propranolol. Llegada: 80/48 · FC 40 · SpO₂ 97 % · FR 16 ·
llene 4 s.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Bradicardia con shock (FC 40, PAS 80, frialdad) tras ingesta de propranolol; el examen la describe somnolienta. | Reconocer la bradicardia con shock e iniciar soporte. | Nombra la inestabilidad; actúa; fija la reevaluación. |
| F1 | YES | Glucagón, calcio y atropina son ejecutables; el motor responde según la causa. | Priorizar el antídoto de esta causa y valorar la respuesta. | Glucagón con dosis y vía; reevalúa FC, PA y perfusión. |
| C1 | YES | Shock por betabloqueador: el antídoto no es el del caso anterior, se desvanece y hay que pedir ayuda. La intención suicida entra en la continuidad. | Integrar antídoto, soporte y continuidad. | Distingue esta intoxicación; da glucagón; lo repite o agrega soporte; pide toxicología, UCI y salud mental. |
| C3 | NO | SpO₂ 97 %, respiración lenta pero regular, sin hipercapnia (PaCO₂ 40). | — | — |
| C4 | NO | Sin procedimiento propio del diseño. | — | — |

### 14. `bradycardia_hyperk_63m` · bradycardia

Hiperkalemia grave con bradicardia de QRS ancho. Llegada: 84/50 · FC 38 · QRS
180 ms · potasio 7,6.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | FC 38 con QRS de 180 ms y PAS 84: el trazado da la gravedad antes que el potasio. | Reconocer la bradicardia de QRS ancho como amenaza e iniciar tratamiento por sospecha. | Nombra el QRS ancho y la bradicardia; actúa antes del resultado; fija la reevaluación. |
| F1 | YES | Calcio por sospecha antes del laboratorio (evento crítico), más medidas que desplazan el potasio. | Priorizar el calcio y el desplazamiento, y valorar la respuesta. | Calcio con dosis y vía; salbutamol nebulizado o glucosa; reevalúa FC, QRS y PA. |
| C1 | YES | Secuencia calcio, desplazamiento y remoción: el potasio sigue subiendo, el calcio se desvanece y el motor no dializa. | Integrar protección, desplazamiento y remoción, y decidir continuidad. | Repite el calcio si el QRS vuelve a ensancharse; agrega desplazamiento; pide diálisis o nefrología; dice qué vigila. |
| C3 | NO | SpO₂ 96 %, pulmones limpios. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 15. `gi_bleed_57m` · gi_bleed

HDA con shock hemorrágico. Llegada: 88/54 · FC 124 · SpO₂ 97 % · llene 5 s ·
Hb 6,7 · lactato 4,4.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock hemorrágico (88/54, FC 124, llene 5 s) con melena. | Reconocer el shock hemorrágico y reanimar antes de completar el estudio. | Nombra sangrado e hipoperfusión; inicia reposición; fija la reevaluación. |
| F1 | YES | Sangre, volumen, IBP y consulta son ejecutables; el motor rinde menos con cristaloide que con sangre. | Priorizar la reposición con sangre y valorar la respuesta. | Transfunde; cristaloide sólo como puente; reevalúa PA y perfusión tras el volumen. |
| C1 | YES | Reanimación sostenida: el sangrado continúa hasta la endoscopía, que el motor sólo realiza con PAS ≥ 90 y Hb ≥ 7, o con sangre en curso. | Integrar reposición, hemostasia y reevaluación. | Relaciona la respuesta con el sangrado activo; ajusta la reposición; pide endoscopía; define destino y qué vigila. |
| C3 | NO | SpO₂ 97 %, sin esfuerzo. | — | — |
| C4 | NO | Sin procedimiento dentro del encuentro; la endoscopía ocurre fuera. | — | — |

### 16. `gi_bleed_72f` · gi_bleed

HDA con anemia sintomática e hipoperfusión. Llegada: 98/62 · FC 112 · SpO₂ 96 % ·
llene 4 s · Hb 6,4 · lactato 3,4.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Hipoperfusión de presentación silenciosa (98/62, FC 112, llene 4 s, frialdad); D1 pide reconocerla sin un síntoma dramático. | Reconocer la hipoperfusión por sangrado pese a una queja poco llamativa. | Nombra el sangrado relevante y su consecuencia; actúa sobre la perfusión; fija la reevaluación. |
| F1 | YES | Las mismas intervenciones y el mismo modelo que en 57m. | Priorizar la reposición con sangre y valorar la respuesta. | Transfunde; cristaloide sólo como puente; reevalúa PA y perfusión. |
| C1 | YES | Shock compensado con Hb 6,4 y la misma endoscopía condicionada a la reanimación que en 57m. | Integrar reposición, hemostasia y reevaluación. | Relaciona la respuesta con el sangrado; ajusta la reposición; pide endoscopía; define destino. |
| C3 | NO | SpO₂ 96 %, sin esfuerzo. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 17. `hypoglycemia_28m` · hypoglycemia

Hipoglicemia por insulina con neuroglucopenia. Llegada: 128/76 · FC 112 ·
SpO₂ 98 % · glicemia 34 · somnoliento y confuso.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Compromiso de conciencia con glicemia 34 mg/dL; con 20 min bajo 40 mg/dL, el motor produce una convulsión. | Reconocer la causa reversible del compromiso de conciencia y corregirla primero. | Pide glicemia capilar; nombra la neuroglucopenia; da glucosa; fija el control. |
| F1 | UNCERTAIN (TDFC-2) | Vía aérea, ventilación y circulación conservadas; la única intervención es la glucosa. F1 incluye el compromiso de conciencia, pero no hay oxigenación, presión ni arritmia que manejar. | Priorizar la glucosa sobre el estudio y verificar la respuesta. | Glucosa IV con dosis; control de glicemia y conciencia en un plazo fijado. |
| C1 | NO | Una corrección resuelve la amenaza. No hay shock, falla respiratoria ni sepsis, ni recurrencia en el diseño. | — | — |
| C3 | NO | Vía aérea y ventilación conservadas (SpO₂ 98 %). | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 18. `hypoglycemia_76f` · hypoglycemia

Hipoglicemia por sulfonilurea con riesgo de recurrencia. Llegada: 134/78 · FC 96 ·
SpO₂ 97 % · glicemia 38 · obnubilada.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Obnubilada (abre los ojos sólo a estímulo firme) con glicemia 38 mg/dL. | Reconocer la causa reversible del compromiso de conciencia y corregirla primero. | Pide glicemia capilar; nombra la neuroglucopenia; da glucosa; fija el control. |
| F1 | UNCERTAIN (TDFC-2) | ABC conservado; la reanimación es la glucosa, y el motor hace recurrir la hipoglicemia. | Priorizar la glucosa y verificar la respuesta y su recurrencia. | Glucosa IV; controles seriados; infusión de glucosa u octreótido ante la recaída. |
| C1 | NO | La recurrencia (infusión, octreótido, observación) es vigilancia y continuidad, lo que busca R1-06. La hipoglicemia no es una condición de C1. | — | — |
| C3 | NO | SpO₂ 97 % y FR 18. El motor rechaza la vía oral mientras no esté alerta, pero la vía aérea no es una decisión del caso. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 19. `hypoglycemia_54m_thiamine` · hypoglycemia

Hipoglicemia con déficit probable de tiamina y vía venosa fallida. Llegada:
118/70 · FC 104 · SpO₂ 97 % · glicemia 32 · somnoliento · nistagmo.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Somnolencia con glicemia 32 mg/dL, nistagmo y marcha inestable. | Reconocer la causa reversible del compromiso de conciencia y corregirla primero. | Pide glicemia capilar; nombra la neuroglucopenia; da glucosa; fija el control. |
| F1 | UNCERTAIN (TDFC-2) | La vía con que llega no está en la vena: el bolo casi no sube la glicemia y hay que verificar la entrega (D4). Es la valoración de la respuesta que pide F1, sin amenaza ABC. | Priorizar la glucosa, comprobar que llegó y restablecer una vía que funcione. | Glucosa IV; control de glicemia; reconoce la falla de la vía; instala otra vía (o glucagón, sabiendo que moviliza poco); tiamina como segundo objetivo. |
| C1 | NO | La vía fallida y la tiamina son un segundo paso del mismo problema, no una reanimación crítica. | — | — |
| C3 | NO | Vía aérea y ventilación conservadas. | — | — |
| C4 | NO | Sin procedimiento. | — | — |

### 20. `opioid_35m` · opioid

Depresión ventilatoria por un comprimido de contenido incierto. Llegada: 106/64 ·
FC 68 · SpO₂ 80 % · FR 6 · obnubilado · pH 7,21 · PaCO₂ 69.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | FR 6, SpO₂ 80 %, PaCO₂ 69 y obnubilación. Si nadie ventila, el motor produce un paro respiratorio a los 20 min. | Reconocer la depresión ventilatoria y sostener la ventilación primero. | Nombra la hipoventilación, no sólo la SpO₂; ventila o revierte; fija la reevaluación. |
| F1 | YES | Bolsa-mascarilla, oxígeno y naloxona son ejecutables; el motor separa ventilar de revertir. | Priorizar ventilación y naloxona, y valorar la respuesta. | Bolsa-mascarilla; naloxona con dosis y vía, titulada a la FR; reevalúa FR y SpO₂. |
| C1 | YES | Insuficiencia respiratoria hipercápnica. Un tercio del comprimido aún se absorbe y la naloxona dura unos 27 min: la re-sedación obliga a reevaluar y revisar. | Integrar ventilación, titulación y recurrencia, y decidir la observación. | Titula la naloxona a la ventilación, no a la conciencia; reevalúa al pasar el efecto; repite o inicia infusión; decide observación. |
| C3 | YES | Ventilar con bolsa-mascarilla mientras se revierte es la decisión central (evento crítico); la intubación es ejecutable si no revierte. | Decidir el soporte ventilatorio y reevaluar la ventilación. | Indica ventilación asistida antes o junto a la naloxona; reevalúa FR, SpO₂ o gases; justifica no intubar si revierte. |
| C4 | NO | Sin procedimiento. | — | — |

### 21. `opioid_67f` · opioid

Depresión ventilatoria por morfina de liberación prolongada, con ERC. Llegada:
104/62 · FC 62 · SpO₂ 84 % · FR 8 · obnubilada · pH 7,25 · PaCO₂ 61.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | FR 8, SpO₂ 84 %, PaCO₂ 61 y obnubilación. | Reconocer la depresión ventilatoria y sostener la ventilación primero. | Nombra la hipoventilación; ventila o revierte; fija la reevaluación. |
| F1 | YES | Bolsa-mascarilla, oxígeno y naloxona son ejecutables; el motor separa ventilar de revertir. | Priorizar ventilación y naloxona, y valorar la respuesta. | Bolsa-mascarilla; naloxona titulada a la FR; reevalúa FR y SpO₂. |
| C1 | YES | El opioide de acción prolongada sobrevive a la naloxona: los bolos no bastan y el motor hace de la infusión el tratamiento. D1: «the first correction will not be the last». | Integrar la recurrencia en el plan: infusión y observación. | Reconoce la re-sedación; inicia infusión con dosis; reevalúa; no da el alta con la primera respuesta. |
| C3 | YES | Ventilar mientras se revierte es la decisión central (evento crítico); la intubación es ejecutable. | Decidir el soporte ventilatorio y reevaluar la ventilación. | Ventilación asistida antes o junto a la naloxona; reevalúa FR, SpO₂ o gases. |
| C4 | NO | Sin procedimiento. | — | — |

### 22. `pneumonia_46f` · pneumonia

Neumonía con hipoxemia e hipoperfusión. Llegada: 92/58 · FC 118 · SpO₂ 89 % ·
FR 30 · llene 4 s · lactato 3,8 · PaO₂ 58.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock séptico con hipoxemia (PAS 92, llene 4 s, lactato 3,8, SpO₂ 89 %). | Reconocer hipoxemia e hipoperfusión y tratar antes de las imágenes. | Nombra ambas amenazas; inicia oxígeno y volumen; fija la reevaluación. |
| F1 | YES | Antibiótico, oxígeno y volumen están declarados; el motor responde a cada uno. | Priorizar oxígeno, volumen y antibiótico, y valorar la respuesta. | Oxígeno; bolo de volumen; antibiótico con dosis; reevalúa SpO₂, PA y perfusión. |
| C1 | YES | Sepsis grave: pulmón y circulación empeoran hasta que el antibiótico actúa (60 min). Volumen, vasopresor y reevaluación. | Integrar volumen, vasopresor, oxígeno y antibiótico, y revisar según la respuesta. | Relaciona la respuesta al volumen con la decisión de vasopresor; reevalúa lactato o perfusión; define el nivel de atención. |
| C3 | UNCERTAIN (TDFC-6) | PaO₂ 58 mmHg y FR 30; la D3 espera «addresses the oxygenation». El motor deja un cortocircuito (60 %) que el oxígeno no corrige del todo, y permite escalar a VMNI. | Titular oxígeno y decidir si escalar el soporte, reevaluando. | Oxígeno con dispositivo, flujo y meta; reevalúa SpO₂ y esfuerzo; escala o justifica no escalar. |
| C4 | NO | Sin procedimiento. | — | — |

### 23. `pneumonia_83m` · pneumonia

Neumonía con encefalopatía e hipoperfusión, derivada como «deshidratación».
Llegada: 96/60 · FC 108 · SpO₂ 91 % · FR 28 · llene 4 s · somnoliento ·
lactato 3,1 · PaO₂ 62.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Hipoperfusión (96/60, llene 4 s, lactato 3,1), somnolencia nueva y SpO₂ 91 %; D1 pide no atribuirla a la edad. | Reconocer el compromiso de conciencia y la hipoperfusión como amenaza e iniciar soporte. | Nombra el estado alterado como algo que explicar; inicia volumen y oxígeno; fija la reevaluación. |
| F1 | YES | Antibiótico, oxígeno y volumen están declarados; el motor responde a cada uno. | Priorizar volumen, oxígeno y antibiótico, y valorar la respuesta. | Bolo de volumen; oxígeno; antibiótico; reevalúa PA, perfusión, SpO₂ y conciencia. |
| C1 | YES | Sepsis con encefalopatía: reanimar e investigar el compromiso de conciencia en paralelo (evento crítico). | Integrar la reanimación con el estudio del estado alterado, y revisar el modelo de trabajo. | Pide glicemia o examen neurológico; relaciona la respuesta al volumen con la conciencia; ajusta y define destino. |
| C3 | UNCERTAIN (TDFC-6) | SpO₂ 91 %, PaO₂ 62 mmHg, FR 28 y somnolencia; oxígeno declarado. | Titular oxígeno y reevaluar. | Oxígeno con meta; reevalúa SpO₂, esfuerzo y conciencia. |
| C4 | NO | Sin procedimiento. | — | — |

### 24. `pulmonary_edema_58m` · pulmonary_edema

Edema pulmonar agudo hipertensivo. Llegada: 218/116 · FC 126 · SpO₂ 81 % · FR 38 ·
pH 7,29 · PaCO₂ 49.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Insuficiencia respiratoria (SpO₂ 81 %, FR 38, acidosis respiratoria) con PAS 218. | Reconocer la falla respiratoria de causa cardíaca y sostener la respiración primero. | Nombra la falla y su causa; inicia soporte antes de completar el estudio; fija la reevaluación. |
| F1 | YES | VMNI, nitrato y diurético son acciones definitivas; cargar volumen es evento crítico. | Priorizar VMNI y nitrato, y valorar la respuesta. | VMNI con EPAP y FiO₂; nitrato con dosis; reevalúa SpO₂, FR y PA. |
| C1 | YES | Falla respiratoria con emergencia hipertensiva: VMNI y nitrato vigilando la PA, y decidir si continuar, escalar o reducir. | Integrar soporte y descarga, y revisar según la respuesta. | Ajusta EPAP o nitrato a la respuesta; vigila la PA con el nitrato; decide continuar, escalar o reducir. |
| C3 | YES | La VMNI es acción definitiva y el motor la modela en detalle (EPAP, reclutamiento, efecto en la PA); evento `edema_no_ventilatory_support`. | Decidir y titular la VMNI, y reevaluar. | VMNI con modo, EPAP y FiO₂; reevalúa SpO₂, FR y PA; ajusta o escala. |
| C4 | NO | Sin procedimiento. | — | — |

### 25. `pulmonary_edema_75f` · pulmonary_edema

Insuficiencia cardíaca descompensada con FE reducida y ERC. Llegada: 164/92 ·
FC 114 · SpO₂ 84 % · FR 32 · llene 3 s.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | SpO₂ 84 %, FR 32 y esfuerzo marcado. | Reconocer la falla respiratoria de causa cardíaca y sostener la respiración primero. | Nombra la falla y su causa; inicia soporte; fija la reevaluación. |
| F1 | YES | VMNI, diurético y nitrato están declarados; cargar volumen es evento crítico. | Priorizar VMNI y descarga, y valorar la respuesta. | VMNI con EPAP y FiO₂; nitrato o diurético con dosis; reevalúa SpO₂, FR y PA. |
| C1 | YES | Falla respiratoria en una paciente cuya PA y función renal limitan el nitrato y el diurético. | Integrar soporte, descarga y los límites de PA y riñón. | Ajusta nitrato o diurético a la PA y la función renal; reevalúa; define destino. |
| C3 | YES | La VMNI es acción definitiva y está modelada en detalle; evento `edema_no_ventilatory_support`. | Decidir y titular la VMNI, y reevaluar. | VMNI con modo, EPAP y FiO₂; reevalúa SpO₂, FR y PA. |
| C4 | NO | Sin procedimiento. | — | — |

### 26. `pulmonary_embolism_33f` · pulmonary_embolism

TEP sin hipotensión, con el ancla de la «ansiedad». Llegada: 110/70 · FC 124 ·
SpO₂ 90 % · FR 30 · PaO₂ 59.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Taquicardia 124, SpO₂ 90 % y FR 30 en una paciente que ofrece la ansiedad como explicación; D1 pide reconocer la amenaza contra ese ancla. | Reconocer la hipoxemia y la taquicardia como amenaza e iniciar soporte. | Nombra hipoxemia y taquicardia como amenaza; indica oxígeno y monitorización; no acepta la ansiedad sin evidencia. |
| F1 | YES | El oxígeno es acción definitiva y la D3 espera «addresses the oxygenation»; F1 incluye el plan inicial de oxigenación. | Priorizar oxigenación y monitorización, y valorar la respuesta. | Oxígeno con meta; reevalúa SpO₂, FC y PA. |
| C1 | UNCERTAIN (TDFC-3) | Normotensa, con hipoxemia que corrige el oxígeno. Las decisiones del caso son anticoagular y no trombolizar (evento crítico), más que reanimar. | Integrar oxigenación, anticoagulación y vigilancia del deterioro. | Anticoagula o lo deja pendiente con razón; no tromboliza sin hipotensión; dice qué cambiaría el plan. |
| C3 | UNCERTAIN (TDFC-6) | SpO₂ 90 % y PaO₂ 59 mmHg; oxígeno declarado y la titulación aceptada como alternativa (D3). | Titular oxígeno y reevaluar. | Oxígeno con meta; reevalúa SpO₂ y esfuerzo. |
| C4 | NO | Sin procedimiento. | — | — |

### 27. `pulmonary_embolism_61m` · pulmonary_embolism

TEP de alto riesgo con shock obstructivo. Llegada: 86/54 · FC 132 · SpO₂ 88 % ·
FR 32 · llene 5 s · lactato 4,8 · PaO₂ 55.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock obstructivo (86/54, llene 5 s, lactato 4,8) con SpO₂ 88 %. | Reconocer el shock obstructivo y actuar antes de la angioTC. | Nombra el shock y su causa obstructiva; inicia soporte; fija la reevaluación. |
| F1 | YES | Oxígeno declarado. El motor castiga el volumen rápido (el VD distendido baja el gasto) y tolera volumen lento y acotado. | Priorizar oxigenación y un soporte de la PA que no sobrecargue el VD. | Oxígeno; volumen lento y acotado o vasopresor; reevalúa PA y perfusión. |
| C1 | YES | Shock obstructivo: decidir la reperfusión sin esperar la angioTC (20 min), limitar el volumen, anticoagular y decidir el traslado según la PA. | Integrar reperfusión, soporte y traslado, y revisar según la PA. | Reconoce la hipotensión sostenida; decide trombólisis o equipo de reperfusión; ajusta el soporte; define traslado. |
| C3 | UNCERTAIN (TDFC-6) | SpO₂ 88 %, PaO₂ 55 mmHg y esfuerzo marcado; oxígeno declarado. El motor cobra la presión positiva en la obstrucción: una vía aérea fisiológicamente difícil. | Titular oxígeno y decidir si evitar o preparar la intubación. | Oxígeno de alto flujo; reevalúa; si plantea intubar, nombra el riesgo hemodinámico y lo prepara. |
| C4 | NO | Sin procedimiento. | — | — |

### 28. `renal_colic_34m` · renal_colic

Cólico ureteral no complicado. Llegada: 142/84 · FC 94 · SpO₂ 98 % · 36,8 °C ·
dolor 9/10.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | NO | Perfusión conservada y afebril; por diseño, el motor no inventa deterioro. El dolor intenso no es inestabilidad. | — | — |
| F1 | NO | Nada que reanimar: la intervención es la analgesia. | — | — |
| C1 | NO | Sin condición crítica. | — | — |
| C3 | NO | SpO₂ 98 %. | — | — |
| C4 | UNCERTAIN (TDFC-8) | La analgesia es la decisión central (D1, D3 y D4; el motor mueve el dolor), pero es analgesia del cuadro, no para un procedimiento. | Elegir y dosificar analgesia sistémica y reevaluar el dolor. | Analgésico con dosis y vía compatibles con los vómitos; reevalúa dolor y signos. |

### 29. `obstructive_pyelonephritis_58f` · renal_colic

Pielonefritis obstructiva con sepsis. Llegada: 94/54 · FC 118 · SpO₂ 95 % ·
38,9 °C · llene 4 s · lactato 4,2.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Sepsis con hipoperfusión (94/54, llene 4 s, lactato 4,2) y lentitud. | Reconocer la sepsis y su foco urinario y actuar primero sobre la circulación. | Nombra la sepsis y el foco; inicia volumen y antibiótico; fija la reevaluación. |
| F1 | YES | Volumen, cultivos y antibiótico son las acciones iniciales declaradas (D1, D3). | Priorizar volumen, cultivos y antibiótico, y valorar la respuesta. | Bolo de volumen; cultivos y antibiótico; reevalúa PA, perfusión y lactato. |
| C1 | YES | Sepsis con foco obstruido: el antibiótico enlentece el curso pero no lo revierte sin descompresión. Volumen, vasopresor y urología (evento crítico). | Integrar reanimación, control del foco y continuidad. | Reconoce que el antibiótico no basta; vasopresor si el volumen no alcanza; pide urología o descompresión; define destino. |
| C3 | NO | SpO₂ 95 % y FR 24, sin esfuerzo. | — | — |
| C4 | NO | Dolor 7, pero la prioridad declarada es la sepsis; la descompresión la hace urología fuera del encuentro. | — | — |

### 30. `trauma_limb_hemorrhage_27m` · trauma

Hemorragia externa exsanguinante del muslo. Llegada: 96/54 · FC 132 · SpO₂ 97 % ·
llene 4 s · dolor 8/10.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock hemorrágico con sangrado externo visible. | Reconocer la hemorragia exsanguinante y controlarla primero. | Controla la hemorragia en ≤ 10 min; nombra el shock; fija la reevaluación. |
| F1 | YES | Control de la hemorragia antes que todo (la x del xABCDE), sangre y ácido tranexámico. | Priorizar el control y la reposición con sangre, y valorar la respuesta. | Torniquete o presión con el sitio; sangre antes que cristaloide; reevalúa PA y perfusión. |
| C1 | UNCERTAIN (TDFC-4) | Reanimación de trauma: el Royal College la ubica en C2, que está deshabilitada. | Integrar control, reposición y continuidad. | Controla dentro de la ventana; transfunde; reevalúa; entrega con el tiempo de torniquete. |
| C3 | NO | SpO₂ 97 % y vía aérea indemne. El motor cobra intubar antes de controlar la hemorragia, pero eso es secuencia de trauma, no manejo de la vía aérea. | — | — |
| C4 | UNCERTAIN (TDFC-7) | Torniquete doloroso en un paciente alerta y en shock. La analgesia es ejecutable y el motor modela el dolor de llegada, pero la declaración no la espera. | Elegir una analgesia que respete la PA y reevaluar. | Analgésico con dosis; justifica la elección por la PA; reevalúa dolor y PA. |

### 31. `trauma_hemothorax_41m` · trauma

Hemotórax masivo con hemorragia intratorácica activa. Llegada: 88/50 · FC 126 ·
SpO₂ 91 % · FR 28 · matidez izquierda.

| Obj. | Estado | Racional | Componente observable | Evidencia esperable en el Trace |
|---|---|---|---|---|
| TD1 | YES | Shock (88/50) con dificultad respiratoria (SpO₂ 91 %, FR 28) y matidez izquierda. | Reconocer el hemotórax con shock y actuar. | Nombra la amenaza; drena y reanima a la vez; fija la reevaluación. |
| F1 | YES | Drenaje y reanimación simultáneos (D1), sangre y ácido tranexámico. | Priorizar pleurostomía y sangre, y valorar la respuesta. | Pleurostomía del lado correcto; sangre; reevalúa PA y perfusión tras el drenaje. |
| C1 | UNCERTAIN (TDFC-4) | Hemotórax masivo: drenar, reevaluar, buscar otra fuente y decidir pabellón. Es contenido de C2. | Integrar drenaje, reposición y búsqueda de otra fuente. | Tras el drenaje, reconoce la inestabilidad; repite E-FAST o radiografía de pelvis; pide cirugía. |
| C3 | NO | La pleurostomía, un procedimiento, resuelve la hipoxemia (SpO₂ 91 %). Ni el caso ni la declaración ponen el oxígeno o la ventilación como decisión. | — | — |
| C4 | UNCERTAIN (TDFC-7) | La pleurostomía en un paciente alerta exige analgesia (dolor 7). Es ejecutable, pero no está declarada y el motor no modela el dolor del procedimiento. | Elegir analgesia para la pleurostomía que respete la PA, y reevaluar. | Analgésico con dosis; justifica por la PA; reevalúa dolor y PA. |

## Notas transversales

- **`acs_54m_inferior`.** Sus filas se proponen, pero se sugiere no activarlas
  antes de decidir la auditoría del VD, como se hizo con C14.
- **Lo que el banco no trae para estos objetivos.** Es contenido del banco, no
  cobertura del constructo de ningún residente:
  - ningún caso de paro cardiorrespiratorio (presentación del formulario de TD1,
    F1 y C1);
  - ninguna vía aérea difícil prevista por anatomía (C3 pide 5 observaciones de
    vía aérea difícil prevista);
  - ningún contexto de sedación procedimental (C4);
  - ningún caso pediátrico, que las cinco EPA exigen en parte.
- **Hallazgos para revisión, sin cambios.** Tres posibles inconsistencias de
  datos (De Winter, `bradycardia_bb_54f` y `anaphylaxis_63m_betablocked`) están
  descritas en `DECISIONES_TDFC.md`.

## Cómo se activaría lo que se apruebe

1. **Registrar el caso aprobado.** Por cada caso y objetivo aprobados, se escribe
   la entrada en el bloque `objectives` de su declaración, con estado,
   racional, componente, evidencia esperable y procedencia (quién, cuándo,
   decisión). `case_assessment.verify` la valida.
2. **Sólo encuentros nuevos.** Los encuentros anteriores conservan la base
   congelada con que empezaron.
3. **Rechazados y no revisados.** Un NO deja el objetivo fuera de los encuentros
   nuevos de ese caso. Uno sin revisar sigue con la regla de transición.
4. **Retiro de la transición.** Objetivo por objetivo: cuando los 31 casos de un
   objetivo estén revisados, sale de `TRANSITION_OBJECTIVES`.
