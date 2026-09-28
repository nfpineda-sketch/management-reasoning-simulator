# TD1 · F1 · C1 · C3 · C4 — Decisiones clínicas TDFC-1 a TDFC-8

Ciclo 5 del AI Advisor · instrucción docente 59C · 2026-09-28.

**Estado al ciclo 8 (2026-09-28): APLICADO en el banco, salvo lo que espera
decisión.** Este documento conserva el borrador tal como se presentó; lo que
sigue lo actualiza.

- **TDFC-1 a 6 y 8 se aprobaron conceptualmente en el ciclo 7 (§28)** «según las
  recomendaciones actuales», y el ciclo 8 las escribió en el banco con el modelo
  de C14 (C-2026-09-28-17). **C4 es NO** en todo el entorno desde el ciclo 7.
- **Lo que no está en el banco:** las filas de `acs_54m_inferior` esperan DF-20,
  como recomendaba TDFC-5; ese caso, los casos generados y PS001 conservan la
  transición.
- **La tabla aplicada** está en `TDFC_TABLA_FINAL.md`, con los conteos y las dudas
  residuales de las filas «claras».

**El borrador original decía:** «BORRADOR PARA DECISIÓN DOCENTE. NADA ESTÁ
ACTIVO.»

- **Ninguna fila estaba en el banco.** TD1, F1, C1, C3 y C4 seguían con la regla de
  transición: observables en todo encuentro.
- **Las filas caso por caso** están en `BORRADOR_TDFC.md`. La matriz de cobertura
  del banco está en `MATRIZ_OPORTUNIDADES.md`.
- **Derivación.** `generar_matriz.py` deriva el estado de cada fila a partir de
  sus respuestas, con la misma lógica que `c14_review.derive`. No escribe en el
  banco.
- **Numeración.** Las decisiones van de TDFC-1 a TDFC-8, para no confundirlas con
  las letras A–H de C14.

**Qué se reduce y qué no.** De 155 combinaciones, 133 son claras y 22 quedan en
duda. Las 22 caben en 8 preguntas, y cada combinación dudosa depende de una sola.
La incertidumbre no se eliminó: queda escrita en cada decisión, y la resuelve su
respuesta, no el borrador.

## El principio, objetivo por objetivo

> ¿Existe en este encuentro una decisión o acción clínicamente relevante que
> pueda razonablemente observarse para este objetivo?

No basta con que algo pueda ocurrir. La oportunidad sale del diseño del caso (lo
que trae, lo que el motor modela, lo que su declaración espera) y nunca de
resultados futuros.

| Objetivo | La pregunta aplicada |
|---|---|
| **TD1** | ¿Llega el paciente inestable, o se vuelve inestable por diseño, de modo que reconocerlo e iniciar el soporte sea una decisión real? |
| **F1** | ¿Exige priorizar e iniciar intervenciones de reanimación (oxigenación y ventilación, presión, arritmia crítica) y valorar su respuesta? |
| **C1** | ¿Hay shock, insuficiencia respiratoria, sepsis grave o paro cuya reanimación exija integrar decisiones, reevaluar y revisar el modelo de trabajo? |
| **C3** | ¿Hay una decisión real de oxígeno, preparación de la vía aérea o soporte ventilatorio, con respuesta que reevaluar? |
| **C4** | ¿Trae el caso un procedimiento que exija decidir sedación o analgesia, anticipar sus efectos y reevaluar? |

## Cómo responder

Una línea basta. Por ejemplo: «1 approve / 2 approve / 3 reject / 4 approve /
5 modify: sólo 54m / 6 approve / 7 approve / 8 approve».

- **Approve:** se aplica la recomendación y las filas quedan como dice «Si se
  aprueba».
- **Reject:** las filas quedan como dice «Si se rechaza».
- **Modify:** se ajusta lo que usted indique.

Después se aprueban o corrigen las filas, si quiere objetivo por objetivo, y
recién entonces podrían escribirse en el banco.

### Una pregunta de fondo común a 1, 3, 4, 7 y 8

**¿Qué pasa con el contenido que la EPA ubica en otra EPA que el simulador no
habilita?**

- El trauma es C2 (EPA Guide v1.1, p. 20), deshabilitada.
- El dolor torácico y el SCA estable son C5 (p. 25).
- Las intoxicaciones, incluidos el toxidrome opioide y la bradicardia tóxica, son
  C8 (p. 30).

**Criterio del borrador.** El contenido de otra EPA no se absorbe en TD1 o C1 por
su tema. Sólo cuenta por la presentación fisiológica que esas EPA nombran: shock,
insuficiencia respiratoria, arritmia inestable, compromiso de conciencia.

- **Por eso sí:** las bradicardias tóxicas y los opioides son C1 YES, porque
  traen shock o insuficiencia respiratoria.
- **Por eso no:** el SCA estable no es TD1 por su ECG (decisión 1), y el trauma
  no entra a C1 por la puerta de atrás (decisión 4).

---

### TDFC-1 · SCA estable con un ECG que exige intervención inmediata

**PREGUNTA CLÍNICA.** ¿Crea oportunidad TD1 un SCA hemodinámicamente estable
cuyo ECG exige intervención inmediata, sin inestabilidad fisiológica?

**OBJETIVOS AFECTADOS.** TD1.

**CASOS AFECTADOS.** `acs_61m_posterior` · `acs_52m_de_winter` · `acs_66f_nonst`.

**POR QUÉ IMPORTA.**

- El alcance local de TD1 es «reconocer la inestabilidad». La EPA (p. 4) enumera
  cinco presentaciones fisiológicas: paro, arritmia inestable, shock,
  dificultad respiratoria y compromiso neurológico.
- Pero su hito 8 es interpretar el ECG reconociendo condiciones que exigen
  intervención inmediata, «incluida la isquemia».
- Los tres llegan estables:
  - 61m: 132/80, FC 88;
  - 52m: 128/78, FC 96, frío y sudoroso;
  - 66f: 146/86, FC 102, síntomas en curso y troponina 180 ng/L.

**BORRADOR ACTUAL.** UNCERTAIN en los tres.

**RECOMENDACIÓN.** Aprobar NO en los tres.

- Sin inestabilidad fisiológica, reconocer el patrón del ECG ya lo observa el D1
  de la rúbrica de SCA («Names the ischaemic pattern…»), y es contenido de C5.
- TD1 queda para los SCA que llegan o se vuelven inestables: `acs_54m_inferior` y
  `acs_70f_left_main`, ambos YES.

**SI SE APRUEBA.** NO: `acs_61m_posterior`, `acs_52m_de_winter`, `acs_66f_nonst`.

**SI SE RECHAZA.** YES en los tres, con esta evidencia esperable: nombra el patrón
como una condición que exige intervención inmediata; inicia antiagregante y
reperfusión o monitorización.

**INCERTIDUMBRE.**

- El hito 8 nombra la isquemia explícitamente.
- El patrón posterior es justamente el que más se pasa por alto.
- `acs_48m_wellens` queda NO con cualquier respuesta: sin isquemia en curso, su
  decisión correcta es angiografía programada, no una intervención inmediata.

### TDFC-2 · Hipoglicemia con vía aérea, ventilación y circulación conservadas

**PREGUNTA CLÍNICA.** ¿Es reanimación (F1) corregir una causa reversible de
compromiso de conciencia cuando el ABC está conservado?

**OBJETIVOS AFECTADOS.** F1.

**CASOS AFECTADOS.** `hypoglycemia_28m` · `hypoglycemia_76f` ·
`hypoglycemia_54m_thiamine`.

**POR QUÉ IMPORTA.**

- La EPA F1 (p. 10) incluye el compromiso de conciencia entre sus
  presentaciones.
- Pero su contenido es oxigenación y ventilación, presión y arritmia crítica, y
  estos casos no necesitan nada de eso: la intervención es la glucosa.

**BORRADOR ACTUAL.** UNCERTAIN en los tres. TD1 es YES en los tres.

**RECOMENDACIÓN.** Aprobar YES en los tres.

- El motor modela lo que hace de esto una reanimación:
  - la urgencia: convulsión tras 20 min bajo 40 mg/dL;
  - la vía: la oral se rechaza mientras no esté alerta, y en 54m la vía venosa
    no funciona;
  - la respuesta: glicemia y conciencia, con recurrencia en 76f.
- La declaración pide recontrolar (D4).
- F1 agrega a TD1 lo que TD1 no pide: valorar la respuesta.

**SI SE APRUEBA.** YES en los tres.

**SI SE RECHAZA.** NO en los tres; TD1 sigue YES.

**INCERTIDUMBRE.**

- La misma primera decisión (dar glucosa) sería evidencia para TD1 y para F1.
- En 28m la respuesta es simple.

### TDFC-3 · Hipoxemia grave sin shock que la primera línea suele estabilizar

**PREGUNTA CLÍNICA.** ¿Alcanza C1 una dificultad respiratoria grave con hipoxemia
(PaO₂ < 60 mmHg al aire), sin shock ni falla ventilatoria, cuando la primera
línea suele estabilizarla?

**OBJETIVOS AFECTADOS.** C1.

**CASOS AFECTADOS.**

- `pulmonary_embolism_33f`: 110/70 · FC 124 · SpO₂ 90 % · PaO₂ 59.
- `asthma_24f`: SpO₂ 90 % · FR 34 · PaO₂ 59 · PaCO₂ 31.

**POR QUÉ IMPORTA.** C1 (p. 18) es la reanimación, estabilización y cuidado
continuo de una condición que amenaza la vida; nombra la insuficiencia
respiratoria. Ambos la tienen por definición, pero la corrigen el oxígeno y el
tratamiento específico.

**BORRADOR ACTUAL.** UNCERTAIN en ambos.

**RECOMENDACIÓN.** Aprobar NO en ambos.

- Las decisiones que el diseño pone al frente son otras: anticoagular y no
  trombolizar en el TEP (evento crítico), y escalar según la respuesta en el
  asma.
- TD1 y F1 ya son YES en ambos, y C3 lo decide TDFC-6.
- Los desafíos R2-02, R2-03 y R3-01 apuntan a lo demás.

**SI SE APRUEBA.** NO: `pulmonary_embolism_33f`, `asthma_24f`.

**SI SE RECHAZA.** YES en ambos, con esta evidencia esperable: integra oxigenación,
tratamiento específico y reevaluación; dice qué cambiaría el plan.

**INCERTIDUMBRE.**

- El asma puede llegar a falla ventilatoria si el tratamiento es insuficiente
  (la fatiga está modelada), pero eso sería consecuencia del desempeño.
- El TEP sólo se deteriora tras un error: volumen rápido o trombólisis sin
  indicación.

### TDFC-4 · Trauma mientras C2 sigue deshabilitada

**PREGUNTA CLÍNICA.** ¿Cuentan para C1 los casos de trauma mientras C2 está
deshabilitada?

**OBJETIVOS AFECTADOS.** C1. TD1 y F1 no cambian: se definen por la presentación
fisiológica, no por el mecanismo, y son YES en ambos casos.

**CASOS AFECTADOS.** `trauma_limb_hemorrhage_27m` · `trauma_hemothorax_41m`.

**POR QUÉ IMPORTA.**

- C1 habla de una condición «médica o quirúrgica». El Royal College ubica la
  reanimación del traumatizado grave en C2.
- DF-4 mantuvo C2 deshabilitada por amplitud insuficiente
  (`docs/AUDITORIA_OPORTUNIDAD_C2.md`).

**BORRADOR ACTUAL.** UNCERTAIN en ambos.

**RECOMENDACIÓN.** Aprobar NO en ambos. Contar estos casos en C1 observaría
contenido de C2 con otro nombre y rodearía la decisión DF-4: la x del xABCDE, la
pleurostomía, el hemotórax masivo, el pabellón.

**SI SE APRUEBA.** NO en ambos.

**SI SE RECHAZA.** YES en ambos, con esta evidencia esperable: controla o drena en
la ventana; transfunde; reevalúa y busca otra fuente; pide cirugía.

**INCERTIDUMBRE.** El shock hemorrágico es shock, y C1 incluye lo quirúrgico. Si C2
se habilitara, estos serían sus candidatos.

### TDFC-5 · Deterioro por diseño durante la espera de la reperfusión

**PREGUNTA CLÍNICA.** ¿Crea oportunidad un deterioro que el motor produce con un
manejo correcto mientras se espera la reperfusión, si el encuentro sigue
abierto?

**OBJETIVOS AFECTADOS.** C1 en `acs_54m_inferior`; C3 en `acs_70f_left_main`.

**CASOS AFECTADOS.** `acs_54m_inferior` (C1) · `acs_70f_left_main` (C3).

**Lo que el motor hace.** Calculado desde las constantes de `acs_reperfusion`; no
se corrió el motor.

- **54m.** Bloqueo AV completo a los 45 min de oclusión: la FC cae a 42 y la PA
  con ella.
  - La arteria abre 90 min después de activar hemodinamia (60 con trombólisis),
    así que el bloqueo aparece aun con una activación inmediata.
  - Decisión docente del 2026-09-20: el bloqueo es condicional, «but it must not
    be rare».
- **70f.** Con cada minuto de oclusión cae la función del VI.
  - La PAS baja unos 9 mmHg hacia el minuto 90.
  - La SpO₂ cae bajo 90 % hacia el minuto 60 y la FR sube.
  - La VMNI alivia la congestión.
  - Solicitud docente del 2026-09-22.
- **La declaración de SCA** espera manejar «what happens while that is arranged»
  (D5, 15–180 min).
- **Pero el cierre lo decide el residente.** Si cierra antes, el evento no ocurre,
  y el esquema no tiene un estado «condicional» (DF-17, diferido).

**BORRADOR ACTUAL.** UNCERTAIN en las dos celdas.

**RECOMENDACIÓN.** Aprobar YES en ambas.

- Son diseño y no consecuencia de un error: aparecen con manejo correcto,
  dentro de la ventana declarada, y el caso y su declaración los sostienen
  (70f: congestión en la radiografía y crépitos al llegar; oxígeno nombrado en
  la D3).
- Si el encuentro se cierra antes, la docencia simplemente no valora, como hoy.

**Considerados y dejados fuera.**

- `acs_52m_de_winter`: la congestión viene del modelo general, llega tarde
  (SpO₂ bajo 90 % pasado el minuto 80) y ni el caso ni su declaración la
  plantean. F1 y C3 quedan NO con cualquier respuesta.
- `acs_61m_posterior`: congestión mínima.
- Los eventos que sólo siguen a un error no crean oportunidad para otro
  objetivo: FV a los 120 min sin reperfusión, agotamiento del asma subtratada,
  barotrauma, abstinencia por naloxona, sobrecarga transfusional.

**SI SE APRUEBA.** YES: `acs_54m_inferior` C1 y `acs_70f_left_main` C3.

**SI SE RECHAZA.** NO en ambas: cuentan sólo los estados de llegada.

**INCERTIDUMBRE.** La fila de 54m depende además de la auditoría del VD
(`docs/AUDITORIA_ACS_54M_INFERIOR.md`).

### TDFC-6 · Oxígeno ante hipoxemia sin falla ventilatoria ni amenaza de vía aérea

**PREGUNTA CLÍNICA.** ¿Crea oportunidad C3 una hipoxemia de llegada (SpO₂ < 92 %
al aire, con trabajo respiratorio aumentado) cuyo manejo es titular oxígeno y
decidir si escalar? Se exige además que la declaración ponga el oxígeno como
acción y que el motor modele la respuesta.

**OBJETIVOS AFECTADOS.** C3.

**CASOS AFECTADOS.**

| Caso | SpO₂ · PaO₂ | Qué agrega el caso |
|---|---|---|
| `pneumonia_46f` | 89 % · 58 | Cortocircuito del 60 % que el oxígeno no corrige del todo; escalar a VMNI es posible |
| `pneumonia_83m` | 91 % · 62 | Somnolencia |
| `pulmonary_embolism_33f` | 90 % · 59 | La D3 acepta titular el oxígeno como alternativa |
| `pulmonary_embolism_61m` | 88 % · 55 | El motor cobra la presión positiva en la obstrucción: vía aérea fisiológicamente difícil |
| `asthma_24f` | 90 % · 59 | El motor castiga la intubación prematura y la tardía |
| `anaphylaxis_63m_betablocked` | 89 % · 57 | La D3 de la familia espera oxígeno |

**POR QUÉ IMPORTA.**

- El alcance local de C3 nombra el oxígeno.
- La EPA C3 (p. 22) nombra la estrategia ventilatoria en la falla hipoxémica,
  pero su centro es la intubación y el cuidado posintubación.

**BORRADOR ACTUAL.** UNCERTAIN en los seis.

**RECOMENDACIÓN.** Aprobar YES en los seis.

- Cinco de seis tienen PaO₂ < 60 mmHg: insuficiencia respiratoria hipoxémica.
- Titular el oxígeno y decidir si escalar es la estrategia ventilatoria al nivel
  que el simulador observa.

**SI SE APRUEBA.** YES en los seis.

**SI SE RECHAZA.** NO en los seis. C3 queda en las seis filas claras, con
decisión de VMNI, intubación o bolsa-mascarilla, o amenaza de vía aérea: los dos
edemas, `asthma_49m`, los dos opioides y `anaphylaxis_29f`.

**Nota.** `trauma_hemothorax_41m` (SpO₂ 91 %) queda NO con cualquier respuesta.

- Ni el caso ni su declaración ponen el oxígeno como decisión.
- La hipoxemia la resuelve la pleurostomía, un procedimiento.
- Si usted quiere contarlo, modifique la regla.

**INCERTIDUMBRE.**

- Serían observaciones de poca profundidad.
- Fuera del asma, el ventilador no se puede ajustar después de intubar.
- En `pulmonary_embolism_61m`, la vía aérea fisiológicamente difícil refuerza
  el YES.

### TDFC-7 · Sedoanalgesia para un procedimiento que el caso trae y no declara

**PREGUNTA CLÍNICA.** ¿Hay oportunidad C4 cuando el caso trae un procedimiento
doloroso, pero su declaración no plantea la sedoanalgesia y el motor no modela
el dolor del procedimiento?

**OBJETIVOS AFECTADOS.** C4.

**CASOS AFECTADOS.**

- `bradycardia_avb3_78f`: marcapaso transcutáneo con PAS 78, paciente somnolienta.
- `trauma_hemothorax_41m`: pleurostomía en shock, dolor 7.
- `trauma_limb_hemorrhage_27m`: torniquete en shock, dolor 8.

**POR QUÉ IMPORTA.**

- La EPA C4 (p. 23) es seleccionar, preparar, monitorizar y administrar
  sedación y analgesia sistémica para facilitar un procedimiento. El alcance
  local pide anticipar sus consecuencias y reevaluar.
- En el motor, la sedoanalgesia es ejecutable en todas las familias. Pero la
  sedación procedimental sólo cobra presión (propofol, midazolam): no modela
  profundidad, depresión respiratoria ni el dolor del procedimiento.
- La morfina sí modela el alivio del dolor de llegada, la caída de precarga y
  la sedación.

**BORRADOR ACTUAL.** UNCERTAIN en los tres.

**RECOMENDACIÓN.** Aprobar NO en los tres, con el diseño actual. Ninguna
declaración lo plantea, y el motor no deja ver las consecuencias que C4 pide
anticipar y reevaluar.

**SI SE APRUEBA.** NO en los tres.

**SI SE RECHAZA.** YES en los tres.

- La evidencia esperable quedaría en el bloque `objectives`.
- La respuesta observable sería hemodinámica y, en trauma, el dolor de llegada.

**INCERTIDUMBRE.**

- ACLS recomienda sedoanalgesia para el marcapaso en un paciente consciente.
- Una pleurostomía en un paciente alerta siempre la requiere.
- Elegir en shock un agente que respete la PA es una decisión real.

**No entra en esta decisión.** La inducción de `asthma_49m` es C3 (hito 5 de C3).
El motor la registra como `procedural_sedation`, así que una propuesta de C4 por
esa acción sería contenido de C3.

### TDFC-8 · Analgesia del cuadro, sin procedimiento

**PREGUNTA CLÍNICA.** ¿Cuenta como C4 la analgesia sistémica del cuadro, sin
procedimiento, cuando es la decisión central del caso?

**OBJETIVOS AFECTADOS.** C4.

**CASOS AFECTADOS.** `renal_colic_34m`: dolor 9/10; la analgesia es D1, D3 y D4.

**POR QUÉ IMPORTA.** El título local («Manage procedural sedation and analgesia»)
admite leer «analgesia» por sí sola. El alcance local y la EPA la atan a un
procedimiento.

**BORRADOR ACTUAL.** UNCERTAIN.

**RECOMENDACIÓN.** Aprobar NO. Tanto el alcance local como la EPA hablan de
analgesia para un procedimiento.

**SI SE APRUEBA.** NO.

**SI SE RECHAZA.** YES en `renal_colic_34m`. Los demás casos con dolor (SCA,
trauma, pielonefritis) siguen NO: en ellos la analgesia no es una decisión que el
diseño ponga al frente.

**INCERTIDUMBRE.** El hito 2 de C4 habla de analgesia multimodal, pero «para el
procedimiento específico».

---

## Si se aprueban las ocho recomendaciones

Derivado por `generar_matriz.py` (YES / NO / UNCERTAIN):

| Objetivo | Borrador actual | Si se aprueban las 8 | Si se rechazan las 8 |
|---|---|---|---|
| TD1 | 26 / 2 / 3 | 26 / 5 / 0 | 29 / 2 / 0 |
| F1 | 23 / 5 / 3 | 26 / 5 / 0 | 23 / 8 / 0 |
| C1 | 18 / 8 / 5 | 19 / 12 / 0 | 22 / 9 / 0 |
| C3 | 6 / 18 / 7 | 13 / 18 / 0 | 6 / 25 / 0 |
| C4 | 0 / 27 / 4 | 0 / 31 / 0 | 4 / 27 / 0 |

Con las recomendaciones aprobadas:

- **TD1:** pasan a NO los tres SCA estables.
- **F1:** pasan a YES las tres hipoglicemias.
- **C1:** pasa a YES `acs_54m_inferior`; pasan a NO `pulmonary_embolism_33f`,
  `asthma_24f` y los dos traumas.
- **C3:** pasan a YES los seis de TDFC-6 y `acs_70f_left_main`.
- **C4:** queda NO en los 31 casos.

## Filas claras (no requieren decisión)

Su racional está en `BORRADOR_TDFC.md`. Tampoco se activan hasta que usted las
apruebe.

| Objetivo | YES claros | NO claros |
|---|---|---|
| **TD1** | 26: todos salvo los de abajo y los tres de TDFC-1 | `acs_48m_wellens`, `renal_colic_34m` |
| **F1** | 23: `acs_54m_inferior`, `acs_70f_left_main`, las dos anafilaxias, los dos asmas, las cuatro bradicardias, las dos HDA, los dos opioides, las dos neumonías, los dos edemas, los dos TEP, `obstructive_pyelonephritis_58f`, los dos traumas | `acs_66f_nonst`, `acs_61m_posterior`, `acs_52m_de_winter`, `acs_48m_wellens`, `renal_colic_34m` |
| **C1** | 18: `acs_70f_left_main`, las dos anafilaxias, `asthma_49m`, las cuatro bradicardias, las dos HDA, los dos opioides, las dos neumonías, los dos edemas, `pulmonary_embolism_61m`, `obstructive_pyelonephritis_58f` | `acs_66f_nonst`, `acs_61m_posterior`, `acs_52m_de_winter`, `acs_48m_wellens`, las tres hipoglicemias, `renal_colic_34m` |
| **C3** | 6: los dos edemas, `asthma_49m`, los dos opioides, `anaphylaxis_29f` | 18: los SCA salvo `acs_70f_left_main` (5), las cuatro bradicardias, las dos HDA, las tres hipoglicemias, los dos casos renales, los dos traumas |
| **C4** | — | 27: todos salvo los cuatro de TDFC-7 y TDFC-8 |

**Dudas residuales en filas claras.** Se mantienen, pero conviene que usted las
mire:

- **`anaphylaxis_29f`, C3 YES.** El motor modela el estridor sólo como una caída
  de SpO₂ que alivia la adrenalina; no hay obstrucción completa ni intubación
  difícil. Es la única C3 YES clara que descansa en una amenaza de vía aérea.
- **Opioides y bradicardias tóxicas, C1 YES.** La EPA propia de estos casos es C8
  (no habilitada). Cuentan porque traen insuficiencia respiratoria o shock, que
  C1 nombra, y porque el motor obliga a revisar el plan: recurrencia, antídoto
  que se desvanece.
- **`hypoglycemia_76f`, C1 NO.** La recurrencia por sulfonilurea podría leerse como
  revisión del modelo de trabajo. Queda NO porque la hipoglicemia no es una
  condición de C1, y la recurrencia es lo que busca R1-06.
- **`acs_52m_de_winter`, F1 y C3 NO.** El modelo general puede llevar la SpO₂ bajo
  90 % pasado el minuto 80 de espera. Se dejó fuera en TDFC-5.
- **`acs_54m_inferior`, todas sus filas.** Se sugiere no activarlas antes de
  decidir la auditoría del VD.
- **Una misma decisión puede alimentar varios objetivos.** Dar glucosa, o ventilar
  con bolsa-mascarilla, puede ser evidencia para TD1, F1 y C3. Cada objetivo
  requiere su propia valoración docente y admite una observación por encuentro
  (`docs/OBJECTIVE_TRACKING.md`).

## Consecuencias que conviene ver antes de responder

- **C4 sin fuente en el banco.** Si aprueba TDFC-7 y TDFC-8, C4 no tendría
  oportunidad en ninguno de los 31 casos. Hoy sigue observable por la
  transición; al retirarla, ningún caso del banco lo ofrecería. El banco no trae
  un contexto de sedación procedimental. Esto es una descripción, no una
  propuesta.
- **C3 depende sobre todo de TDFC-6:** 6 casos si la rechaza, 13 si la aprueba.
- **TD1 y F1 cambian poco.** El banco está hecho de urgencias con inestabilidad,
  así que siguen YES en 23 a 29 casos según las respuestas. El efecto principal
  de revisarlos es sacar los SCA estables, Wellens y el cólico.
- **Límites del motor que afectan la evidencia, no la oportunidad:**
  - fuera del asma, el ventilador no se ajusta después de intubar;
  - la sedación procedimental sólo cobra presión;
  - la acción `procedural_sedation` también registra la inducción.
- **Lo que recibe el brief de IA.** Hoy, para TD1 a C4, recibe sólo título,
  alcance y limitación: no tienen `observable_behaviors` ni
  `evidence_requirements`. Una fila aprobada le agregaría su racional, su
  componente y su evidencia esperable, como guía
  (`faculty_analysis._objective_rubric`).

## Inconsistencias encontradas

Para decisión docente; no se cambió ningún dato.

1. **`acs_52m_de_winter`: el POCUS repetido «mejora» con la arteria cerrada.**
   - El POCUS de llegada dice «Akinesis of the anterior wall and apex».
   - Desde el primer minuto de isquemia, el motor reescribe el VI según
     `lv_function`, que parte en 0,82 en toda oclusión activa
     (`acs_reperfusion.ARRIVAL_LV`).
   - Un POCUS repetido diría «The anterior wall and apex show mildly reduced
     contraction». Sólo volvería a «akinetic» pasados unos 96 min de oclusión.
   - Los otros SCA no tienen este salto. En los demás con oclusión activa, el
     texto de llegada ya equivale a «mildly reduced»; en 66f y en Wellens, el
     motor no reescribe el VI.
   - La fila C14 aprobada de este caso cita que la motilidad evoluciona con los
     minutos de isquemia.
2. **`bradycardia_bb_54f`: el estado de conciencia no coincide con el examen.**
   - La presentación y el examen la describen somnolienta («found drowsy»,
     «Opens eyes to voice»).
   - Pero el observable se construye sin `mental`, así que el motor la reporta
     «Alert». El motor de bradicardia conserva ese valor y fuerza «Alert» con
     PAS ≥ 95.
   - Pesa en TD1: el compromiso de conciencia es una de sus presentaciones.
3. **`anaphylaxis_63m_betablocked`: el ritmo no coincide con la historia.**
   - Tiene fibrilación auricular en tratamiento con apixabán, y el examen dice
     «Irregular pulse».
   - Pero el ritmo del observable se calcula como «Sinus rhythm» (FC 64), con
     perfil de ECG basal.
   - Menor, y en el mismo sentido: `bradycardia_ccb_68m` tiene FA de años y el
     monitor muestra «Sinus bradycardia».
4. **Definición incompleta en `objectives.py`.** TD1, F1, C1, C3 y C4 no tienen
   `observable_behaviors` ni `evidence_requirements`; sólo los R* los tienen.
5. **Ya documentadas, sin cambios:**
   - el VD de `acs_54m_inferior`;
   - el POCUS estático del TEP que se deteriora;
   - el POCUS estático tras la captura en `bradycardia_avb3_78f`;
   - el evento del neumotórax del asma, que nombra el diagnóstico.

## Qué pasa después

1. **Respuesta docente 1–8.** `generar_matriz.py` deriva las filas; una respuesta
   «modify» se escribe en la decisión antes de derivar.
2. **Aprobación de las filas,** con las claras, si prefiere objetivo por objetivo.
3. **Escritura en el banco,** sólo entonces: bloques `objectives` con
   procedencia, que rigen para encuentros nuevos.
4. **Retiro de la transición,** objetivo por objetivo, cuando los 31 casos de un
   objetivo estén revisados.
5. **Nada de esto cambia** datos clínicos, eventos, dominios ni puntajes.
