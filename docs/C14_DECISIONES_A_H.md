# C14 · Decisiones clínicas A–H para la revisión docente

Ciclo 4 del AI Advisor, autorización docente del 2026-09-28 (DF-13, §5–§7 y
§31–§33).

**Estado: PREPARADO PARA DECISIÓN DOCENTE. C14 NO ESTÁ ACTIVO.**

- Nada de esto está escrito en el banco de casos. Ningún caso tiene un bloque
  `objectives`, y una prueba lo verifica (`test_observation_opportunities.py`).
- Mientras la revisión no termine, C14 sigue observable en todos los casos con
  la regla de transición (DF-12).
- Las filas caso por caso siguen en el borrador del ciclo 3
  (`BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md`), con las correcciones de este
  ciclo.
- `c14_review.py` deriva el estado de cada fila a partir de las respuestas.
  No escribe nada.

## El principio aplicado (§33)

> ¿Existe una decisión de manejo clínicamente relevante que pueda razonablemente
> ser guiada, modificada, priorizada o reevaluada mediante POCUS en este
> encuentro?

**No basta** con que haya un POCUS, con que pueda hacerse, con que muestre algo
interesante o con que confirme lo que ya se sabe.

Tampoco se usó ningún resultado futuro: lo que hagan los médicos del piloto no
dice si la oportunidad existía (§68). La clasificación sale sólo del diseño
clínico del caso:

- lo que el caso trae;
- lo que el motor modela;
- lo que la declaración del caso espera.

## Cómo responder

Una línea por decisión basta. Por ejemplo: «A approve / B approve / C modify:
anafilaxia 63m también SÍ / D reject …».

- **Approve**: se aplica la recomendación, y las filas quedan como dice «Si se
  aprueba».
- **Reject**: las filas quedan como dice «Si se rechaza».
- **Modify**: se ajusta lo que se indique.

Después se aprueban o corrigen las filas, y recién entonces se escriben en el
banco (§6).

### Una pregunta de fondo común a A, C, F, G y H

El borrador del ciclo 3 usó como límite los estados que lista la EPA C14 (EPA
Guide v1.1, p. 42):

- derrame pericárdico;
- función global del VI;
- neumotórax;
- hemotórax;
- derrame pleural;
- aneurisma de aorta abdominal;
- líquido libre;
- gestación intrauterina.

La motilidad regional, el VD, la vena cava, la consolidación, la TVP por
compresión y la hidronefrosis no están en esa lista. Cinco decisiones dependen
de esto.

**Recomendación común.** La oportunidad la define el alcance local de C14:
«pedir los hallazgos POCUS que el caso entrega, interpretar su implicancia para
el manejo y relacionarlos con las decisiones siguientes». La lista de la EPA
enumera las aplicaciones que se exigen al adquirir e interpretar la imagen, y
el simulador no evalúa la adquisición.

Por eso, un hallazgo fuera de la lista puede crear oportunidad **si guía una
decisión real del caso**. Cada fila dirá si el hallazgo es de la lista o no,
para que la docencia pondere su contribución a la EPA.

Si se prefiere el límite estricto de la lista, basta con rechazar C, G y la
parte de A que se apoya en la motilidad y el VD.

---

### Decision A — Motilidad regional y ventrículo derecho en el SCA

**CLINICAL QUESTION.** ¿Crea oportunidad C14 la motilidad regional o el VD de
un SCA cuando la reperfusión la decide el ECG?

**WHY IT MATTERS FOR C14.** La motilidad regional puede priorizar la
reperfusión cuando el patrón del ECG se pasa por alto con frecuencia (IAM
posterior, De Winter). El VD decide nitratos y volumen en un IAM inferior. Pero
cuando el diagnóstico ya está establecido, el POCUS sólo lo confirma.

**AFFECTED CASES.**

- `acs_54m_inferior`
- `acs_66f_nonst`
- `acs_61m_posterior`
- `acs_52m_de_winter`
- `acs_48m_wellens` (se decide en B)

**CURRENT DRAFT.** Las cuatro, UNCERTAIN.

**RECOMMENDATION.** Aprobar esta regla: la motilidad regional o el VD cuentan
cuando pueden cambiar o priorizar la decisión de la que depende el caso, no
cuando confirman un diagnóstico ya hecho.

- **`acs_61m_posterior`: SÍ.** Descenso del ST en V1–V3 con hipocinesia
  posterior; el POCUS puede priorizar la activación de la reperfusión.
- **`acs_52m_de_winter`: SÍ.** La acinesia anterior sostiene tratar el patrón
  como oclusión.
- **`acs_66f_nonst`: NO.** El SCA ya está establecido por el ECG y la troponina
  (180 ng/L). La hipocinesia leve no cambia la vía: un caso sin oclusión, con
  una angiografía que puede esperar.
- **`acs_54m_inferior`: sigue UNCERTAIN, por una inconsistencia de datos.** Ver
  «Inconsistencias» abajo. Si se corrige el VD del POCUS para que muestre el
  compromiso que el caso declara, pasa a SÍ: el VD guía nitratos y volumen, y
  el motor castiga el nitrato y premia el volumen.

**RATIONALE.** En estos cuatro casos el motor hace evolucionar la motilidad con
los minutos de isquemia (`acs_reperfusion.wall_motion`). Un POCUS repetido
muestra, entonces, lo que está ocurriendo.

**IF APPROVED.**

- SÍ: `acs_61m_posterior`, `acs_52m_de_winter`.
- NO: `acs_66f_nonst`.
- UNCERTAIN: `acs_54m_inferior`, hasta decidir la corrección de sus datos.

**IF REJECTED.** Los cuatro pasan a NO: sólo cuentan los estados de la lista
de la EPA.

**UNCERTAINTY.**

- En `acs_61m_posterior`, las derivaciones posteriores (2 min) bastan para el
  diagnóstico, así que el POCUS puede ser un segundo apoyo más que la guía.
- En De Winter, el POCUS puede sustituir la lectura del ECG, que es lo que el
  caso enseña.

### Decision B — Un POCUS normal que no debe tranquilizar (Wellens)

**CLINICAL QUESTION.** ¿Es oportunidad C14 observar que un POCUS normal en
reposo no se use para descartar una lesión crítica?

**WHY IT MATTERS FOR C14.** En Wellens la decisión correcta (angiografía, sin
prueba de provocación) no depende del POCUS. El riesgo es tranquilizarse con
él. Observar ese límite es buen juicio, pero no es usar el POCUS para guiar el
manejo.

**AFFECTED CASES.** `acs_48m_wellens`.

**CURRENT DRAFT.** UNCERTAIN.

**RECOMMENDATION.** Aprobar NO. Ninguna decisión de manejo puede razonablemente
guiarse con un POCUS normal en reposo. El mal uso (alta o prueba de esfuerzo
por un POCUS normal) se observa mejor como razonamiento diagnóstico que como
C14.

**RATIONALE.** Cumple la condición «claramente NO» del §33.

**IF APPROVED.** NO: `acs_48m_wellens`.

**IF REJECTED.** SÍ, con esta evidencia esperable: si pide POCUS, no lo usa
para descartar ni para dar el alta.

**UNCERTAINTY.** Parte de la docencia considera que conocer los límites del
POCUS es parte de usarlo para guiar el manejo.

### Decision C — Valoración de volumen para guiar los fluidos

**CLINICAL QUESTION.** ¿Crea oportunidad C14 la valoración de volumen (VCI
colapsada, VI pequeño o hiperdinámico, sin líneas B) cuando la cantidad de
volumen o el paso a vasopresor es una decisión abierta?

**WHY IT MATTERS FOR C14.** En el shock séptico y en el hemorrágico, cuánto
volumen dar y cuándo pasar a vasopresor es una decisión real, y el POCUS la
orienta y la reevalúa. En la anafilaxia, en cambio, la adrenalina y el volumen
se indican igual con o sin POCUS.

**AFFECTED CASES.**

- `pneumonia_46f`, `pneumonia_83m`
- `gi_bleed_57m`, `gi_bleed_72f`
- `obstructive_pyelonephritis_58f` (agregado en este ciclo)
- `anaphylaxis_29f`, `anaphylaxis_63m_betablocked`

**Por qué se agrega `obstructive_pyelonephritis_58f`.** Es un shock séptico
(PAS 94) con la VCI de 1,0 cm colapsable: el mismo hallazgo y la misma
decisión que las neumonías. El borrador lo dejaba sólo en H.

**CURRENT DRAFT.** Las siete, UNCERTAIN.

**RECOMMENDATION.** Aprobar esta regla: cuenta cuando la cantidad de volumen o
el paso a vasopresor es una decisión abierta del caso.

- **SÍ:** las dos neumonías, las dos HDA y la pielonefritis obstructiva.
- **NO:** las dos anafilaxias. La adrenalina y el volumen van igual, y en la
  refractaria (63m) la palanca que el caso diseña es la historia (atenolol) y
  el glucagón, no el POCUS.

**RATIONALE.**

- **Neumonía y HDA.** El motor reporta la VCI según el volumen recibido:
  1,5 cm con 500 mL o más, y 2,0 cm con menos del 50 % de colapso con 1500 mL
  o más. Un POCUS repetido reevalúa de verdad.
- **Pielonefritis.** La VCI queda como a la llegada; la oportunidad descansa en
  el primer examen. Se registra como limitación del motor antes de activar esa
  fila.

**IF APPROVED.**

- SÍ: `pneumonia_46f`, `pneumonia_83m`, `gi_bleed_57m`, `gi_bleed_72f`,
  `obstructive_pyelonephritis_58f`.
- NO: `anaphylaxis_29f`, `anaphylaxis_63m_betablocked`.

**IF REJECTED.**

- Las anafilaxias y las HDA pasan a NO.
- Las neumonías dependen de F.
- La pielonefritis depende de H.

**UNCERTAINTY.**

- La VCI predice mal la respuesta a volumen en respiración espontánea.
- En la HDA manda la transfusión.
- En la anafilaxia refractaria (PAS 76), el POCUS puede apoyar más volumen o
  el glucagón. Es razonable marcarla SÍ si la docencia lo prefiere.

### Decision D — Asma: el neumotórax que sólo aparece si el curso lo trae

**CLINICAL QUESTION.** ¿Hay oportunidad C14 en el asma grave si el POCUS
decide sólo ante un neumotórax, y ese neumotórax depende de lo que haga el
residente?

**WHY IT MATTERS FOR C14.** El POCUS de llegada (deslizamiento presente) no
cambia el tratamiento broncodilatador. En el ventilado, separar el neumotórax
de la hiperinflación dinámica sería una decisión guiada por POCUS.

**AFFECTED CASES.** `asthma_24f`, `asthma_49m`.

**CURRENT DRAFT.** Las dos, UNCERTAIN.

**Lo que el motor hace (verificado en este ciclo).**

- **Cuándo aparece el neumotórax.** Sólo por barotrauma: después de intubar,
  con presión plateau sobre 30 cmH₂O sostenida (`asthma_complications.step`).
  Entonces el POCUS pierde el deslizamiento y muestra el punto pulmonar.
- **Qué lee el residente en ese momento.** El texto del evento ya dice el
  diagnóstico: «this is a tension pneumothorax, not dynamic hyperinflation».
  Describe además los ruidos ausentes y la hiperresonancia.
- **Consecuencia.** El POCUS confirmaría lo que el evento ya anunció.

**RECOMMENDATION.** Aprobar NO para ambos, con el diseño actual. Si se quiere
C14 en el asma, el evento debería describir el deterioro sin nombrar el
diagnóstico. Eso es un cambio del caso que requiere su propia autorización;
después se reconsidera.

**RATIONALE.** Con el diseño actual, el POCUS sólo confirmaría (§33).

**IF APPROVED.** NO: `asthma_24f`, `asthma_49m`.

**IF REJECTED.** SÍ para ambos, con esta evidencia esperable: ante un deterioro
en ventilación mecánica, pide POCUS, nombra la ausencia de deslizamiento o el
punto pulmonar y descomprime.

**UNCERTAINTY.**

- `asthma_49m` (somnoliento, SpO₂ 89 %) tiene más probabilidad de ser
  intubado.
- El esquema no tiene un estado «condicional». Marcar después que una
  oportunidad no ocurrió es DF-17, que está diferido.

### Decision E — Bradicardias: la contractilidad para elegir el soporte

**CLINICAL QUESTION.** ¿Crea oportunidad C14 una contractilidad global
disminuida para elegir el soporte (inótropo, antídoto o marcapaso) en la
bradicardia tóxica? ¿Y en el bloqueo completo, para confirmar la captura?

**WHY IT MATTERS FOR C14.** En la intoxicación por calcioantagonistas o por
betabloqueadores, la contractilidad puede orientar el soporte. En el bloqueo
completo, el POCUS puede confirmar la captura mecánica del marcapaso.

**AFFECTED CASES.**

- `bradycardia_ccb_68m`
- `bradycardia_bb_54f`
- `bradycardia_avb3_78f` (la verificación técnica del borrador)

**CURRENT DRAFT.** Las tres, UNCERTAIN.

**Lo que el motor hace (verificado en este ciclo).**

- **El mismo POCUS en las tres causas.** El calcioantagonista, el
  betabloqueador y la hiperkalemia muestran exactamente el mismo hallazgo:
  «globally reduced contraction at a slow rate». No distingue la causa.
- **Cómo se decide el manejo.** El caso separa las causas por la historia, la
  glucosa y el ECG (`bradycardia_toxicology`). El antídoto responde según la
  causa (calcio o glucagón). La dobutamina tiene en esta familia el efecto
  genérico. La insulina en dosis alta no está modelada.
- **AVB3.** El POCUS no cambia tras la captura: después de marcapasear sigue
  diciendo «a slow, regular ventricular rate independent of the atria», en
  contradicción con el monitor. La captura mecánica la confirman el pulso y la
  presión del evento.

**RECOMMENDATION.** Aprobar NO para las tres con el diseño actual; es coherente
con la hiperkalemia, que ya es NO. El POCUS estático tras la captura queda
registrado como defecto del motor.

**RATIONALE.** El POCUS no discrimina la causa ni cambia la respuesta modelada.
En AVB3 contradiría lo que muestra el monitor.

**IF APPROVED.** NO: `bradycardia_ccb_68m`, `bradycardia_bb_54f`,
`bradycardia_avb3_78f`.

**IF REJECTED.**

- SÍ para calcioantagonista y betabloqueador: la contractilidad disminuida
  orienta a un inótropo o al marcapaso antes que a un vasopresor puro. El
  motor, sin embargo, no premia esa elección.
- AVB3 sigue NO hasta que su POCUS refleje la captura.

**UNCERTAINTY.** En la práctica, la contractilidad sí orienta el soporte
inotrópico y la insulina en dosis alta en estas intoxicaciones. El caso está
diseñado para enseñar a reconocer la causa.

### Decision F — La consolidación vista con POCUS

**CLINICAL QUESTION.** ¿Crea oportunidad C14, por sí sola, la consolidación
vista con POCUS?

**WHY IT MATTERS FOR C14.** El antibiótico no depende del POCUS, y la
radiografía muestra la misma consolidación (8 min frente a 2 min).

**AFFECTED CASES.** `pneumonia_46f`, `pneumonia_83m`.

**CURRENT DRAFT.** UNCERTAIN (preguntas C y F).

**RECOMMENDATION.** Aprobar que **por sí sola no crea oportunidad**: confirma
lo que muestra la radiografía. El estado de las neumonías lo decide C.
Nombrar la consolidación es evidencia bienvenida, no exigida.

**RATIONALE.** Es la confirmación que el §33 excluye.

**IF APPROVED.** No cambia ningún estado por sí sola; las neumonías siguen a C.

**IF REJECTED.** Las neumonías son SÍ aunque C se rechace.

**UNCERTAINTY.** En `pneumonia_83m`, que llega como «deshidratación», una
consolidación temprana podría reorientar el diagnóstico. Eso es razonamiento
diagnóstico más que manejo.

### Decision G — TEP: sobrecarga del VD y TVP proximal por compresión

**CLINICAL QUESTION.** ¿Crean oportunidad C14 la sobrecarga del VD y la TVP
proximal vista por compresión para decidir anticoagulación y reperfusión antes
de la angioTC?

**WHY IT MATTERS FOR C14.**

- **Tiempos.** La angioTC tarda 20 minutos y el encuentro puede cerrarse antes;
  el POCUS tarda 2.
- **La declaración del caso lo espera.**
  - Acepta el POCUS como primera evidencia objetiva cuando el paciente no puede
    moverse.
  - Lo acepta también como evidencia del evento de anticoagulación.
  - Reconoce «reevaluar con POCUS» como alternativa.

**AFFECTED CASES.**

- `pulmonary_embolism_33f`
- `pulmonary_embolism_61m`: el SÍ del borrador descansa en el VD, que es
  justamente esta pregunta, por eso se revisa aquí.

**CURRENT DRAFT.** `pulmonary_embolism_33f` UNCERTAIN; `pulmonary_embolism_61m`
YES.

**Corrección del borrador.** Los dos POCUS traen una vena poplítea no
compresible, es decir, una TVP proximal. El borrador no la mencionaba.

**RECOMMENDATION.** Aprobar SÍ para ambos.

- **61m, en shock.** VD mayor que el VI, signo D y McConnell: justifican tratar
  el cuadro como TEP masivo y decidir la reperfusión sin esperar la angioTC.
- **33f, estable.** La TVP proximal confirma la enfermedad tromboembólica: se
  puede anticoagular antes de la angioTC. El VD apenas dilatado, sin shock,
  sostiene no trombolizar, que el caso declara como acción peligrosa.

**RATIONALE.** Las dos decisiones centrales de los casos (anticoagular ahora,
reperfundir o no) pueden guiarse razonablemente con el POCUS.

**IF APPROVED.** SÍ: `pulmonary_embolism_33f`, `pulmonary_embolism_61m`.

**IF REJECTED.** Ambos pasan a NO; en 61m, el SÍ del borrador cae con esta
decisión.

**UNCERTAINTY.**

- En 33f se puede anticoagular por probabilidad clínica sin el POCUS.
- El VD y la TVP no son estados de la lista de la EPA.
- El POCUS del TEP no cambia con el deterioro, aunque la declaración dice «the
  right ventricle is where deterioration shows first». Queda registrado como
  inconsistencia.

### Decision H — La ecografía renal del caso

**CLINICAL QUESTION.** ¿Cuenta como C14 la ecografía renal de los casos
renales?

**WHY IT MATTERS FOR C14.** La dilatación, leída junto a la orina y la
temperatura, separa el cólico de la obstrucción infectada: decide la
descompresión urgente.

**AFFECTED CASES.**

- `renal_colic_34m`
- `obstructive_pyelonephritis_58f`: su volumen se decide en C.

**CURRENT DRAFT.** Las dos, UNCERTAIN.

**Respuesta a la parte factual del borrador («¿es POCUS o un estudio
formal?»).** En el simulador es un estudio aparte (`renal_ultrasound`, 15 min),
con un informe formal. El POCUS de estos casos no trae vistas renales.

**RECOMMENDATION.** Aprobar NO para C14 por la ecografía renal tal como está
modelada. No es un hallazgo POCUS entregado, y la decisión que guía (la
descompresión) ya se observa en el dominio D3 y en el evento crítico
`pyelo_no_source_control`. La pielonefritis sigue a C.

**RATIONALE.** El alcance local de C14 es el POCUS.

**IF APPROVED.**

- NO: `renal_colic_34m`.
- `obstructive_pyelonephritis_58f` sigue a C.

**IF REJECTED.** Se requiere reetiquetar el estudio como POCUS, que es un
cambio de datos del caso. Entonces:

- `obstructive_pyelonephritis_58f` es SÍ: la dilatación con sepsis obliga a
  descomprimir.
- `renal_colic_34m` es SÍ: la dilatación leve con un cálculo de 5 mm, sin
  infección, orienta el alta con analgesia.

**UNCERTAINTY.** La ecografía renal para buscar hidronefrosis es una aplicación
POCUS habitual en urgencias. El caso la escribió como estudio formal.

---

## Si se aprueban las ocho recomendaciones

`c14_review.derive(c14_review.RECOMMENDED)`:

| Estado | Casos | Cuáles |
|---|---|---|
| SÍ | 14 | los 5 claros + `acs_61m_posterior`, `acs_52m_de_winter`, `pneumonia_46f`, `pneumonia_83m`, `gi_bleed_57m`, `gi_bleed_72f`, `obstructive_pyelonephritis_58f`, `pulmonary_embolism_33f`, `pulmonary_embolism_61m` |
| NO | 16 | los 6 claros + `acs_66f_nonst`, `acs_48m_wellens`, `anaphylaxis_29f`, `anaphylaxis_63m_betablocked`, `asthma_24f`, `asthma_49m`, `bradycardia_ccb_68m`, `bradycardia_bb_54f`, `bradycardia_avb3_78f`, `renal_colic_34m` |
| UNCERTAIN | 1 | `acs_54m_inferior`, por la inconsistencia de sus datos |

La incertidumbre no desaparece: queda escrita en cada decisión. La resuelve la
respuesta docente, no el borrador.

## Casos claros (sin decisión A–H; tampoco se activan todavía, §7)

- **SÍ (5):**
  - `acs_70f_left_main`: la función global del VI, estado de la lista; el
    motor limita el volumen en ese perfil.
  - `pulmonary_edema_58m` y `pulmonary_edema_75f`: líneas B, VI deprimido y
    VCI pletórica; cargar volumen es evento crítico.
  - `trauma_limb_hemorrhage_27m`: E-FAST negativo en shock.
  - `trauma_hemothorax_41m`: hemotórax y drenaje.
- **NO (6):**
  - `bradycardia_hyperk_63m`;
  - las tres hipoglicemias;
  - los dos opioides.
- **Duda residual en un caso claro.** En `trauma_limb_hemorrhage_27m` la lesión
  es aislada, por una máquina en el muslo. El E-FAST descarta una fuente oculta
  y la declaración lo espera, pero en una lesión aislada aporta menos. Sigue SÍ
  en el borrador.

## Inconsistencias encontradas (para decisión docente; no se cambió ningún dato)

1. **`acs_54m_inferior`: el VD declarado y el POCUS se contradicen.**
   - El caso declara compromiso del VD (`rv_involvement: True`, en
     `clinical_cases.py`), y el motor lo modela: el nitrato puede colapsar la
     presión y el volumen ayuda.
   - El POCUS escrito, en cambio, dice «RV free wall contracts normally».
   - Consecuencia: un residente que usa bien el POCUS concluiría que el nitrato
     es seguro, y el motor lo castigaría.
   - Corregirlo es un cambio de datos clínicos: requiere autorización.
2. **POCUS que no cambia con el curso.** El motor actualiza el POCUS en
   neumonía y HDA (VCI), edema pulmonar (pulmón), SCA con oclusión (motilidad)
   y asma (neumotórax). No lo actualiza:
   - en la bradicardia tras la captura;
   - en la VCI de la anafilaxia y de la pielonefritis;
   - en el VD del TEP que se deteriora.

   Importa sólo donde se aprueba reevaluar con POCUS: hoy, la pielonefritis en
   C y el TEP en G.
3. **El evento del neumotórax en el asma nombra el diagnóstico** (Decisión D).
4. **Un comentario del código renal dice «the same dilatation» en ambos
   casos.** Los informes difieren: leve derecha con cálculo de 5 mm, y
   moderada izquierda con cálculo de 9 mm. Es sólo el comentario; los datos
   son correctos.

## Qué pasa después

1. **Respuesta docente A–H.** La herramienta deriva las filas: por
   `c14_review.derive` si la respuesta es approve o reject, o editando la
   decisión si es modify.
2. **Aprobación de las filas.** Se aprueba la tabla resultante, junto con los
   casos claros.
3. **Escritura en el banco.** Recién entonces se escriben los bloques
   `objectives` de C14 en `case_assessment_bank.py`. Cada uno lleva quién lo
   revisó y cuándo, y rige sólo para encuentros nuevos.
4. **Retiro de la regla de transición.** C14 sale de la regla transitoria caso
   a caso (DF-12). Cuando los 31 estén revisados, sale de
   `TRANSITION_OBJECTIVES`.
5. **Defectos del motor.** Si una fila aprobada depende de uno de los defectos
   listados arriba, ese defecto se corrige antes de activar la fila.
