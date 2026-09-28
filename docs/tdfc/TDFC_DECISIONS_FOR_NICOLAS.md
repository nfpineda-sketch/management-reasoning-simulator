# TDFC · Decisiones para Nicolás

Ciclo 6 · 2026-09-28 · oportunidades de TD1, F1, C1, C3 y C4 en los 31 casos
del banco.

- **TDFC-7 · C4 = NO está decidido.** El motor no modela adecuadamente el
  componente relevante del dolor procedural, y pedir un procedimiento no es una
  oportunidad de C4. No se pregunta de nuevo.
- **Nada se escribe en el banco en este ciclo.** Se sigue el camino de C14:
  auditoría de IA, luego su decisión, luego la implementación.
  - Mientras tanto, la transición mantiene los cinco objetivos valorables en
    todo encuentro, C4 incluido (`observation_opportunities.py:70`).
- **`acs_54m_inferior` sigue NOT REVIEWED para C14.** Ninguna de sus filas
  TD/F/C se activa antes de DF-20. En el ciclo 6 DF-20 quedó en «sin cambio de
  datos ni de fisiología» (`COLA_DECISIONES_AI_ADVISOR.md`); la auditoría DF-23
  recomienda C14 NO y deja el caso NOT REVIEWED hasta su confirmación. Sus filas
  TD/F/C ya no dependen de un cambio del caso.
- **C4 = NO todavía no rige en el código.** Mientras no se escriba en el banco
  (lo que este ciclo no hace, por decisión), la transición mantiene C4
  valorable en todo encuentro. Si el piloto con residentes empieza antes de
  implementar TD/F/C, conviene decidir si C4 = NO se escribe antes: es la única
  fila ya decidida.
- **El umbral de C14, aplicado a cada decisión.** Una herramienta disponible o
  una acción posible no crean oportunidad. Hace falta una situación
  clínicamente significativa en la que el objetivo pueda manifestarse de
  verdad. No basta con que se pueda pedir un examen o un procedimiento, ni con
  que el diagnóstico pertenezca a una categoría.
- **Una oportunidad YES observa un componente de la EPA, nunca la EPA
  completa.** Es la lógica DIRECT/PARTIAL de R1-03, R1-04 y R2-01: cada YES dice
  qué componente observa y qué queda fuera. En TD/F/C, que no tienen vínculos
  de marco, el componente irá en el campo `observable_component` de cada
  declaración, como en C14.

## Las 7 decisiones

| Decisión | Objetivo | Pregunta, en corto | Combinaciones | Borrador | Recomendación | Respuesta sugerida |
|---|---|---|---|---|---|---|
| TDFC-1 | TD1 | SCA estable con un ECG que exige intervención inmediata | 3 | UNCERTAIN | NO en los 3 | approve |
| TDFC-2 | F1 | Hipoglicemia con vía aérea, ventilación y circulación conservadas | 3 | UNCERTAIN | YES en los 3 | approve |
| TDFC-3 | C1 | Hipoxemia grave sin shock, que la primera línea estabiliza | 2 | UNCERTAIN | NO en los 2 | approve |
| TDFC-4 | C1 | Trauma mientras C2 está deshabilitada | 2 | UNCERTAIN | NO en los 2 | approve |
| TDFC-5 | C1 · C3 | Deterioro por diseño mientras se espera la reperfusión | 2 | UNCERTAIN | YES en los 2 (54m sólo tras DF-20) | approve |
| TDFC-6 | C3 | Oxígeno ante hipoxemia sin falla ventilatoria | 6 | UNCERTAIN | YES en 3 y NO en 3 (**difiere del borrador**) | approve, como aquí |
| TDFC-8 | C4 | Analgesia del cuadro, sin procedimiento | 1 | UNCERTAIN | NO | approve |

Son 19 combinaciones. Con las 3 de TDFC-7, ya NO, completan las 22 dudosas del
borrador.

**Qué dejarían estas recomendaciones** (YES / NO sobre 31 casos):

| Objetivo | Borrador hoy (YES / NO / duda) | Con estas recomendaciones | Si aprobara las 8 del borrador |
|---|---|---|---|
| TD1 | 26 / 2 / 3 | 26 / 5 | 26 / 5 |
| F1 | 23 / 5 / 3 | 26 / 5 | 26 / 5 |
| C1 | 18 / 8 / 5 | 19 / 12 | 19 / 12 |
| C3 | 6 / 18 / 7 | **10 / 21** | 13 / 18 |
| C4 | 0 / 27 / 4 | 0 / 31 | 0 / 31 |

Las 5 filas de `acs_54m_inferior` están contadas, pero esperan a DF-20.

## Hechos en que se apoyan

El motor se corrió en memoria, sin base de datos ni red, sobre el árbol de
trabajo del 2026-09-28. Dos corridas dieron las mismas cifras, aunque otra
sesión editaba `family_engine.py` y `family_parser.py`. Los guiones quedaron
fuera del repositorio.

| Afirmación | Estado | Detalle |
|---|---|---|
| 54m: bloqueo AV completo a los ~45 min, aun con hemodinamia activada al llegar | **Verificado** | Activación en el minuto 0: bloqueo a los 45, FC 42, PA 100/64 → 84/55 (min 50) → 82/53 (min 70). La arteria abre a los 90 y vuelve el ritmo sinusal. Con trombólisis en el minuto 0: bloqueo a los 45 y apertura a los 60. `acs_reperfusion.py:24-26, 63-64, 211-219, 252-259` |
| 70f: la congestión empeora con manejo correcto, y la VMNI la alivia | **Verificado, con matiz** | SpO₂ 94 → 90 % (min 60) → 89 % (min 80) → 88 % (min 90). FR 26 → 33. Esfuerzo «Exhausted» a los 80 min. PAS 104 → 95 a los 90 (−9). Con VMNI desde el minuto 40: SpO₂ 99 %. El borrador decía «bajo 90 % hacia el minuto 60»: es 90 % a los 60, y bajo 90 % desde los 80. `acs_reperfusion.py:79-113` |
| De Winter: la congestión del modelo llega tarde | **Verificado, con matiz** | Aun con hemodinamia en el minuto 0: SpO₂ 90 % a los 80–90 min y FR 24 → 30, y el esfuerzo se rotula «Exhausted» a los 80 min. El borrador no menciona el rótulo |
| El oxígeno solo corrige la hipoxemia de llegada en los 6 casos de TDFC-6 | **Verificado (hecho nuevo)** | Mascarilla con reservorio a 15 L/min: SpO₂ 98–99 % a los 15 min en los seis. Cánula a 3 L/min: 91–94 % |
| Las neumonías empeoran hasta que actúa el antibiótico | **Verificado** | Con cánula a 3 L/min, antibiótico y 1 L: esfuerzo «Markedly increased» entre los minutos 60 y 80; SpO₂ 90–92 % (46f) y 92–94 % (83m) |
| TEP: intubar cuesta circulación mientras dura la obstrucción | **Verificado en el código** | Sólo la ventilación invasiva, y el costo se desvanece con la lisis. `pe_obstruction.py:47-49, 145-155` |
| Asma: el motor juzga la intubación prematura o tardía, y 24f mejora con el tratamiento | **Verificado** | `asthma_complications.py:35-48, 114-122`. 24f con salbutamol y corticoide: SpO₂ 99 % con 3 L/min a los 20 min; FR 34 → 20 a los 40 |
| Anafilaxia 63m: la hipoxemia depende de controlar la reacción | **Verificado** | Con glucagón 5 mg IV e infusión de adrenalina: SpO₂ 99 % y FR 15 a los 15 min. Si la reacción no se controla: 82–86 % |
| Hipoglicemia: convulsión tras 20 min bajo 40 mg/dL; vía oral rechazada si no está alerta; vía venosa que no entrega (54m); recurrencia (76f) | **Verificado en el código** (no corrido) | `glucose_rescue.py:43, 61-62, 102, 110, 161-171, 181-185`; `family_engine.py:642-646` |
| 28m se presenta como un posible ACV | **Verificado** | «sudden confusion and difficulty finding words» (`hypoglycemia_catalog.py:330`) |
| D1 del SCA («Names the ischaemic pattern…») y D5 («what happens while that is arranged», 15–180 min) | **Verificado** | `case_assessment_bank.py:74-80, 98-125` |
| La analgesia del cólico está en D1, D3 y D4 | **Verificado** | `case_assessment_bank.py:911-935` |
| Ninguna fila TD/F/C está en el banco, y C4 sigue abierto por la transición | **Verificado** | Resolución ejecutada en memoria; `observation_opportunities.py:70, 189-191` |
| Páginas y texto de la EPA Guide | **No verificado aquí** | Se usa la lectura del borrador (`docs/tdfc/BORRADOR_TDFC.md`, «Método») |

**Hallazgo menor.** `test_acs_reperfusion.py:86` se llama «reperfusion
prevents the block and the arrest», pero en su propio escenario el bloqueo
ocurre en el minuto 45. La prueba sólo comprueba la FV.

---

## TDFC-1 · TD1 en el SCA estable con un ECG que exige intervención inmediata

**Objetivo.** TD1: reconocer la inestabilidad e iniciar soporte.

**Pregunta clínica.** ¿Crea oportunidad TD1 un SCA hemodinámicamente estable
cuyo ECG exige intervención inmediata?

**Casos (3 combinaciones).**

- `acs_61m_posterior`: 132/80, FC 88.
- `acs_52m_de_winter`: 128/78, FC 96, frialdad y sudoración.
- `acs_66f_nonst`: 146/86, FC 102, síntomas en curso, troponina 180 ng/L.

**Borrador.** TD1 UNCERTAIN en los tres. F1, C1, C3 y C4: NO en los tres.

**Recomendación.** NO en los tres.

**Racional.**

- Sin inestabilidad fisiológica, lo que TD1 observa no puede manifestarse.
  Contarlo porque el ECG pertenece a la categoría «exige intervención
  inmediata» es justo lo que excluye el umbral de C14.
- Reconocer el patrón ya lo observa el D1 de la rúbrica del SCA. Además es
  contenido de C5, que no está habilitada.
- TD1 queda para los SCA que llegan o se vuelven inestables:
  `acs_70f_left_main`, y `acs_54m_inferior` tras DF-20.

**Si se aprueba.** TD1 NO en los tres: TD1 queda en 26 YES / 5 NO.

**Si se rechaza.** TD1 YES en los tres (29 / 2).

- Componente: reconocer en el ECG una oclusión que exige reperfusión inmediata
  (hito 8 de TD1), e iniciarla con monitorización.
- Queda fuera: toda la inestabilidad fisiológica, el soporte vital, la
  activación de ayuda real y el trabajo en equipo.

**Duda que queda.** El hito 8 nombra la isquemia, y el patrón posterior es el
que más se pasa por alto. `acs_48m_wellens` queda NO con cualquier respuesta.

## TDFC-2 · F1 en la hipoglicemia con vía aérea, ventilación y circulación conservadas

**Objetivo.** F1: iniciar la reanimación crítica («Initiate critical patient
resuscitation»).

**Pregunta clínica.** ¿Es reanimación (F1) corregir una causa reversible de
compromiso de conciencia cuando vía aérea, ventilación y circulación están
conservadas?

**Casos (3 combinaciones).**

- `hypoglycemia_28m`: glicemia 34, somnolencia, confusión y dificultad para
  encontrar palabras.
- `hypoglycemia_76f`: glicemia 38 y obnubilación, por sulfonilurea.
- `hypoglycemia_54m_thiamine`: glicemia 32 y somnolencia; la vía venosa con que
  llega no está en la vena.

**Borrador.** F1 UNCERTAIN en los tres. TD1 YES; C1, C3 y C4 NO.

**Recomendación.** YES en los tres.

**Racional.**

- Es una situación clínicamente significativa, no una categoría: una
  neuroglucopenia que el motor convierte en convulsión tras 20 min bajo
  40 mg/dL.
- Lo propio de F1 puede manifestarse:
  - priorizar la glucosa sobre el estudio (28m se presenta como un posible
    ACV);
  - elegir una vía que entregue (la oral se rechaza sin alerta; en 54m, la
    venosa no entrega);
  - valorar la respuesta (en 76f, la recurrencia).
- No duplica TD1. TD1 es reconocer e iniciar; F1 exige además valorar la
  respuesta, y su evidencia esperable debe incluir esa valoración.

**Componente observable.** Priorizar e iniciar la corrección de una causa
reversible de compromiso de conciencia, por una vía que entregue, y valorar la
respuesta en glicemia y conciencia. Incluye reconocer una vía que falla o una
recurrencia.

**Queda fuera de la EPA.**

- Oxigenación y ventilación, soporte de presión y arritmias críticas: estos
  casos no las tienen.
- Asistir a un equipo de reanimación real.
- Destrezas como el acceso venoso o intraóseo.
- El paro y la pediatría.
- El contexto clínico real, con varios observadores.

**Si se aprueba.** F1 YES en los tres: F1 queda en 26 / 5.

**Si se rechaza.** F1 NO en los tres (23 / 8). TD1 sigue YES.

**Duda que queda.** En 28m la respuesta es simple: es la más débil de las tres.

## TDFC-3 · C1 en la hipoxemia grave sin shock

**Objetivo.** C1: manejar la reanimación crítica («Manage critical patient
resuscitation»).

**Pregunta clínica.** ¿Alcanza C1 una dificultad respiratoria grave con
PaO₂ < 60 mmHg, sin shock ni falla ventilatoria, que la primera línea suele
estabilizar?

**Casos (2 combinaciones).**

- `pulmonary_embolism_33f`: 110/70, FC 124, SpO₂ 90 %, PaO₂ 59.
- `asthma_24f`: SpO₂ 90 %, FR 34, PEF 35 %, PaO₂ 59, PaCO₂ 31.

**Borrador.** C1 UNCERTAIN en ambos. TD1 y F1 YES; C3 lo decide TDFC-6.

**Recomendación.** NO en ambos.

**Racional.**

- Con manejo correcto no hay una segunda fase por diseño (verificado). El TEP
  sigue estable 80 min con oxígeno y heparina. El asma mejora con broncodilatador
  y corticoide.
- Las decisiones que el caso pone al frente son otras: anticoagular y no
  trombolizar en el TEP (evento crítico), y escalar según la respuesta en el
  asma.
- «Insuficiencia respiratoria por definición» es una categoría. La integración
  propia de C1 sólo aparecería tras un error: tratamiento insuficiente, volumen
  rápido o trombólisis sin indicación.

**Si se aprueba.** C1 NO en ambos.

**Si se rechaza.** C1 YES en ambos.

- Componente: integrar oxigenación, tratamiento específico y reevaluación, y
  decir qué cambiaría el plan.
- Queda fuera: el liderazgo real, la amplitud de la enfermedad crítica y las
  destrezas.

**El argumento en contra más fuerte.** Según los criterios británicos de asma
aguda (BTS/SIGN, fuera del repositorio), una SpO₂ < 92 % o una PaO₂ < 8 kPa
hacen de `asthma_24f` un asma con riesgo vital. Si usted lo pondera así,
responda «modify: 24f YES».

## TDFC-4 · C1 en trauma mientras C2 está deshabilitada

**Objetivo.** C1. TD1 y F1 no cambian: son YES en ambos por la fisiología.

**Pregunta clínica.** ¿Cuentan para C1 los casos de trauma mientras C2 está
deshabilitada?

**Casos (2 combinaciones).**

- `trauma_limb_hemorrhage_27m`: 96/54, FC 132, dolor 8.
- `trauma_hemothorax_41m`: 88/50, FC 126, SpO₂ 91 %.

**Borrador.** C1 UNCERTAIN en ambos.

**Recomendación.** NO en ambos.

**Racional.** Es un criterio de alcance.

- El Royal College ubica la reanimación del trauma grave en C2.
- Contarla en C1 observaría contenido de C2 con otro nombre: la x del xABCDE,
  la pleurostomía, el pabellón.
- Rodearía DF-4, que mantuvo C2 deshabilitada por amplitud insuficiente
  (`objectives.py:71-84`).

**Si se aprueba.** C1 NO en ambos.

**Si se rechaza.** C1 YES en ambos: controlar o drenar en la ventana,
transfundir, reevaluar y pedir cirugía. Queda fuera todo lo que define a C2:
la amplitud de mecanismos, las destrezas y el equipo de trauma.

**Duda que queda.** El shock hemorrágico es shock, y C1 incluye lo quirúrgico.
Si C2 se habilita, estos serían sus candidatos.

## TDFC-5 · Deterioro por diseño mientras se espera la reperfusión

**Objetivos.** C1 en `acs_54m_inferior`; C3 en `acs_70f_left_main`.

**Pregunta clínica.** ¿Crea oportunidad un deterioro que el motor produce con
manejo correcto mientras se espera la reperfusión, si el encuentro sigue
abierto?

**Casos (2 combinaciones).** `acs_54m_inferior` · C1 y `acs_70f_left_main` ·
C3.

**Borrador.** UNCERTAIN en ambas. En 54m, TD1 y F1 son YES. En 70f, TD1, F1 y
C1 son YES.

**Qué hace el motor (verificado).**

- **54m:** bloqueo AV completo a los 45 min, aun con hemodinamia activada al
  llegar. FC 42 y PA entre 84/55 y 82/53 hasta que la arteria abre, en el
  minuto 90.
- **70f:** SpO₂ 94 → 88 %, FR 26 → 33 y esfuerzo «Exhausted» a los 80 min. La
  VMNI lo revierte (SpO₂ 99 %).

**Recomendación.** YES en ambas. La fila de 54m no se activa antes de DF-20.

**Racional.**

- Es diseño, no consecuencia de un error. Aparece con manejo correcto, dentro
  de la ventana que la declaración espera: D5, de 15 a 180 min, «what happens
  while that is arranged».
- El caso lo sostiene:
  - 70f llega con crépitos y congestión en la radiografía, y su D3 nombra el
    oxígeno;
  - en 54m, el bloqueo es decisión docente: «conditional, but it must not be
    rare» (`acs_reperfusion.py:60-62`).
- Son situaciones clínicamente significativas en las que el objetivo puede
  manifestarse:
  - una bradiarritmia con hipotensión, que se integra con la precarga del VD y
    la reperfusión pendiente (C1);
  - una congestión que progresa y obliga a decidir oxígeno o VMNI (C3).
- Si el encuentro se cierra antes, la docencia no valora, como hoy. No existe
  un estado «condicional» (DF-17, diferido).

**Componente observable.**

- **54m · C1:** integrar el bloqueo AV, la precarga del VD y la reperfusión
  pendiente, y revisar el plan según la respuesta: atropina o marcapaso,
  volumen, evitar nitratos.
- **70f · C3:** decidir oxígeno o VMNI ante una congestión que progresa en un
  shock cardiogénico en evolución, y reevaluar SpO₂, FR, esfuerzo y PA.

**Queda fuera de la EPA.**

- **C1:** el liderazgo real del equipo, la amplitud de la enfermedad crítica y
  las destrezas, como instalar el marcapaso.
- **C3:** intubar en vía aérea normal o difícil, el cuidado posintubación, el
  ajuste del ventilador (fuera del asma no se ajusta) y las destrezas
  manuales.

**Si se aprueba.** YES en ambas: C1 queda en 19 / 12, con la fila de 54m
inactiva hasta DF-20, y C3 suma una.

**Si se rechaza.** NO en ambas: cuentan sólo los estados de llegada.

**Considerado y dejado fuera.** En `acs_52m_de_winter` el motor también
congestiona: SpO₂ 90 % y esfuerzo «Exhausted» a los 80 min. Ni el caso ni su
declaración lo plantean, así que queda NO.

- Si usted juzga que ese deterioro es de diseño, entraría en esta misma
  lógica.
- Si no, es una pregunta de coherencia del motor (DF-23).

## TDFC-6 · C3 ante hipoxemia sin falla ventilatoria ni amenaza de vía aérea

**Objetivo.** C3: manejar vía aérea y ventilación.

**Pregunta clínica.** ¿Crea oportunidad C3 una hipoxemia de llegada (SpO₂ < 92 %
al aire, con trabajo respiratorio aumentado) cuyo manejo es titular oxígeno y
decidir si escalar?

**Casos (6 combinaciones).**

| Caso | SpO₂ · PaO₂ al aire | En el motor, con cánula a 3 L/min y su tratamiento | Recomendación |
|---|---|---|---|
| `pneumonia_46f` | 89 % · 58 | SpO₂ 90–92 %; el esfuerzo sube a «Markedly increased» a los 60–80 min, hasta que actúa el antibiótico | YES |
| `pneumonia_83m` | 91 % · 62 | SpO₂ 92–94 %; el mismo aumento del esfuerzo | YES |
| `pulmonary_embolism_61m` | 88 % · 55 | SpO₂ 91 % con heparina, en shock obstructivo y con esfuerzo marcado; intubar cuesta circulación | YES |
| `pulmonary_embolism_33f` | 90 % · 59 | SpO₂ 93 %, estable | NO |
| `asthma_24f` | 90 % · 59 | SpO₂ 99 % a los 20 min, con el broncodilatador | NO |
| `anaphylaxis_63m_betablocked` | 89 % · 57 | SpO₂ 99 % al controlar la reacción (glucagón y adrenalina); 82–86 % si no se controla | NO |

**Borrador.** UNCERTAIN en los seis, con recomendación YES en los seis. F1, que
ya incluye el oxígeno, es YES en los seis.

**Recomendación.** Modificar el borrador:

- YES en `pneumonia_46f`, `pneumonia_83m` y `pulmonary_embolism_61m`;
- NO en `pulmonary_embolism_33f`, `asthma_24f` y
  `anaphylaxis_63m_betablocked`.

**La regla, en una línea.** C3 cuenta cuando el soporte de oxígeno o
ventilatorio tiene que ajustarse o escalarse por diseño, con manejo correcto, o
cuando la vía aérea es un riesgo propio del caso. No cuenta cuando dar oxígeno
a una meta resuelve la hipoxemia de llegada: eso ya lo observa F1.

**Racional.**

- El borrador apoya su YES en dos argumentos que el umbral de C14 no acepta por
  sí solos: que cinco de seis tienen PaO₂ < 60 (una categoría), y que escalar
  «es posible» (una acción disponible).
- Verificado: el oxígeno solo corrige la hipoxemia de llegada en los seis. Con
  reservorio a 15 L/min, 98–99 % a los 15 min.
- **Neumonías:** la necesidad cambia por diseño. Pulmón y circulación empeoran
  hasta que actúa el antibiótico, y hay que retitular o escalar.
- **`pulmonary_embolism_61m`:** en un shock obstructivo con esfuerzo marcado,
  evitar, diferir o preparar la intubación es una decisión real de vía aérea
  fisiológicamente difícil, y el motor cobra el error
  (`pe_obstruction.py:47-49, 145-155`).
- **NO en los otros tres:**
  - en el TEP 33f, la hipoxemia se corrige y no evoluciona;
  - en el asma 24f, la corrige el broncodilatador;
  - en la anafilaxia refractaria, la palanca es farmacológica y el oxígeno se
    da igual, como en la decisión C de C14.

**Componente observable.**

- **Neumonías:** elegir dispositivo, flujo y meta de oxígeno en una falla
  hipoxémica que empeora hasta que actúa el antibiótico. Reevaluar y decidir
  si escalar a alto flujo o VMNI.
- **61m:** titular oxígeno en un shock obstructivo, y decidir evitar, diferir o
  preparar la intubación, nombrando el riesgo hemodinámico.

**Queda fuera de la EPA.**

- Intubar, en vía aérea normal o difícil prevista por la anatomía.
- El cuidado posintubación y el ajuste del ventilador.
- La ventilación manual y la laringoscopía.
- La pediatría y el contexto clínico real.

**Resultado en C3,** con TDFC-5 aprobada:

- **como se recomienda:** 10 YES / 21 NO;
- **si prefiere el borrador** (YES en los seis): 13 / 18. Serían observaciones
  de poca profundidad, y la misma orden de oxígeno contaría para TD1, F1 y C3;
- **si la rechaza** (NO en los seis): 7 / 24.

**Duda que queda.** 83m es la más débil de las tres YES: 92–94 % con 3 L/min.
Se trató igual que 46f, como hizo C14 con las dos neumonías.

## TDFC-8 · C4 y la analgesia del cuadro, sin procedimiento

**Objetivo.** C4: sedación y analgesia procedural.

**Pregunta clínica.** ¿Cuenta como C4 la analgesia sistémica del cuadro, sin
procedimiento, cuando es la decisión central del caso?

**Caso (1 combinación).** `renal_colic_34m`: dolor 9/10 con perfusión
conservada. La analgesia está en D1, D3 y D4.

**Borrador.** UNCERTAIN.

**Recomendación.** NO.

**Racional.**

- El alcance local y la EPA atan la analgesia a un procedimiento. Contar la de
  un cólico sería un YES por categoría («analgesia»).
- Su decisión sobre C4, «mantener C4 = NO hasta que exista una oportunidad real
  y observable», apunta en la misma dirección.
- La analgesia del cólico ya la observa la rúbrica del caso (D1, D3 y D4).

**Si se aprueba.** C4 NO: ningún caso del banco ofrece C4. La brecha queda
registrada en la priorización de brechas (sección 6 de
`docs/AUDITORIA_BRECHAS_BANCO_CICLO5.md`).

**Si se rechaza.** C4 YES sólo en `renal_colic_34m`.

- Componente: elegir y dosificar analgesia sistémica y reevaluar el dolor.
- Queda fuera todo lo procedural: la sedación, su profundidad, la depresión
  respiratoria y el procedimiento.

---

## Plantilla de respuesta

«Approve» aplica la recomendación de este documento. En TDFC-6 esa
recomendación difiere del borrador, así que equivale a un «modify» del
borrador.

```
TDFC · respuesta de Nicolás · fecha: ________

TDFC-1  TD1 · SCA estable ................. approve / modify: ______ / reject
TDFC-2  F1 · hipoglicemia ................. approve / modify: ______ / reject
TDFC-3  C1 · hipoxemia sin shock .......... approve / modify: ______ / reject
TDFC-4  C1 · trauma ....................... approve / modify: ______ / reject
TDFC-5  C1 54m · C3 70f ................... approve / modify: ______ / reject
TDFC-6  C3 · oxígeno ...................... approve (YES 46f, 83m, 61m)
                                            / borrador (YES en los 6)
                                            / modify: ______ / reject (NO en los 6)
TDFC-8  C4 · analgesia sin procedimiento .. approve / modify: ______ / reject
```

**Respuesta recomendada, en una línea:** «1 approve / 2 approve / 3 approve /
4 approve / 5 approve (54m tras DF-20) / 6 approve / 8 approve».

**Qué pasa después.**

1. `generar_matriz.py` rederiva las filas con sus respuestas. Un «modify» se
   escribe antes en la decisión.
2. Usted aprueba las filas, si quiere objetivo por objetivo.
3. En un ciclo posterior se escriben en el banco, con procedencia, como se hizo
   con C14.
4. La transición se retira objetivo por objetivo, cuando sus 31 casos estén
   revisados.
