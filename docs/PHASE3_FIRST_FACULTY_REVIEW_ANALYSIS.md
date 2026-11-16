# Fase 3 · Primera revisión docente humana y análisis del FR-G (P3-301 a P3-313, 2026-11-15)

> **Veredicto de causa raíz: `B · CLOSED_VOLUME_REGION_TOO_PROTECTIVE_FOR_SLOW_INFUSION`.**
> **Punto de control: `B · FR_G_REQUIRES_NEW_FACULTY_VOLUME_DECISION`.**
> **El paso P3-306 se DETIENE aquí, como el encargo ordena para B: no se cambió nada ejecutable y se pide una decisión docente exacta (§8).**

Evidencia, sin mezclar clases (la primera es de personas; las demás son del modelo y de las pruebas):

| Clase | Qué es | Dónde |
|---|---|---|
| `HUMAN_FACULTY_REVIEW` | lo que la persona revisora juzgó y escribió | `docs/revision/PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json` y FD-REVIEW-01 a FD-REVIEW-06 |
| `MODEL_ANALYSIS` | lo que se calculó del modelo ejecutable; explica, no juzga | `test_gi_frg_crystalloid_analysis.py` *(antes `frg_crystalloid_analysis.py`; renombrado en P3-348)* y `docs/revision/PHASE3_FRG_CRYSTALLOID_ANALYSIS.json` |
| `TEST_RESULT` | lo que una prueba afirmó | `test_phase3_first_review_analysis.py` |
| `LEGACY_COMPARATOR` | la trayectoria heredada, mostrada tras el bloqueo de la primera impresión | sin cambio; la revisora informó que **no cambió ningún juicio** |

**Qué NO se hizo (confirmado por prueba o por diff):** no se editó `clinical_core/`, `family_engine.py` ni la fisiología; no se añadió control de fuente ni norepinefrina; no se tocó
la autoridad, el piloto, la puntuación, los baselines ni el lector; no se escribió un `FR-G_V2_CANDIDATE` (no existe una corrección autorizada de la que salga); no se cambió ninguna
respuesta humana ni el conjunto de revisión fijado por digesto. **No hay validación clínica.**

## §1 · P3-301 · El registro de la revisión humana

Siete escenarios (cinco obligatorios y dos opcionales). Resultado global: `ACCEPT` 1 (FR-E), `ACCEPT_WITH_LIMITATION` 5 (FR-B, FR-A, FR-F, FR-D, FR-C), `RECALIBRATE` 1 (FR-G),
`REJECT` 0. **El comparador heredado no cambió el juicio en ninguno de los siete.** El comentario del FR-G se conserva **textual**.

Lo que el registro **no** lleva, y por qué: el nombre de la persona (rol `faculty`, sin identidad), y las respuestas ciegas Q1–Q5 (viven en el almacén propio de la revisora y no se
entregaron a este repositorio: `NOT_TRANSCRIBED`, nada se infiere). El conjunto revisado queda **intacto** (digesto `f65d1127…`, ahora también anotado por escenario) y el punto de
control P3-300 sigue siendo byte a byte el mismo (`45b62670…`). Una trayectoria corregida sería un elemento **nuevo y versionado** con su propia revisión ciega; el original no se reescribe.

## §2 · P3-302 · Reconstrucción de FR-G (sólo lectura)

La reconstrucción corre el encuentro heredado real y el adaptador real, con el tiempo de turno de la página (una orden que no es una reevaluación lleva una reevaluación implícita de
5 min; poner una vía no lleva ninguna). **Validación del arnés antes de leer cualquier número:** reproduce las presiones comprometidas por la autoridad en **seis de las siete**
trayectorias que la revisora vio (FR-A, FR-B, FR-C, FR-D, FR-E y FR-G; FR-F no tiene serie, su único compromiso es la parada), en todos sus minutos. Para el FR-G: 92/58 al minuto 60 y
88/56 al 70.

| min | sangrado mL/min | sangrado acum. mL | ganancia efectiva mL/min | redistribución mL/min | cristaloide retenido mL | V (mL-eq) | precarga | flujo anterógrado | PAS/PAD |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0,00 | 0,0 | 0,000 | 0,000 | 0,0 | 0,0 | 0,5000 | 1,0000 | 98,0/62,0 |
| 5 | 2,50 | 12,5 | 2,083 | 0,192 | 9,8 | −2,6 | 0,4985 | 0,9969 | 97,7/61,8 |
| 10 | 2,50 | 25,0 | 2,083 | 0,354 | 18,8 | −5,8 | 0,4965 | 0,9931 | 97,3/61,6 |
| 15 | 2,50 | 37,5 | 2,083 | 0,492 | 27,0 | −9,4 | 0,4943 | 0,9886 | 96,9/61,3 |
| 30 | 2,50 | 75,0 | 2,083 | 0,790 | 48,3 | −22,5 | 0,4863 | 0,9726 | 95,3/60,3 |
| 45 | 2,50 | 112,5 | 2,083 | 0,971 | 66,1 | −37,2 | 0,4772 | 0,9543 | 93,5/59,2 |
| 60 | 2,50 | 150,0 | 2,083 | 1,081 | 81,9 | −52,4 | 0,4676 | 0,9351 | 91,6/58,0 |
| 70 | 2,50 | 175,0 | 0,000 | 0,774 | 72,8 | −81,2 | 0,4488 | 0,8976 | 88,0/55,7 |

Por qué la curva queda casi plana: cada mL infundido (16,67 mL/min) entra al círculo como **0,125 mL efectivos** (2,083 mL/min), y el sangrado resta **2,5 mL/min**. Durante la
infusión la ganancia efectiva compensa el 83 % del sangrado minuto a minuto, y lo que ya se redistribuyó (1,08 mL/min al final) apenas lo recorta. Al terminar la infusión (minuto 60)
la pérdida neta pasa a −3,05 mL/min (sangrado + fuga − relleno) y la presión cae de golpe: 91,6 → 88,0 en 10 min.

## §3 · P3-302A · El sangrado sigue activo

`whole_blood_loss` vale **2,5 mL/min en todos los minutos** de FR-G, del encuentro sin tratar de 72 f y de FR-B (hasta 240 min): un solo valor, sin paradas ni cambios, y ninguna de
esas corridas lleva un contribuyente de hemostasia. No hubo nada que detener.

## §4 · P3-303 y P3-303A · Balance de masa y convolución

El modelo **no** trata 1 L en 60 min como un bolo con redistribución tardía. Integra, cada minuto, la entrada de ese minuto y la fuga simultánea de cada porción anterior (el
reservorio transitorio pierde `1 − exp(−1/τ)` por minuto, incluido el minuto en que entró; la fracción permanente `1 − s` no sale nunca). La prueba independiente: la convolución
`retenido(t) = Σ entrada(s) · e · [(1−s) + s·exp(−edad/τ)]`, escrita desde la definición y **no** desde el código que corre, coincide con el cristaloide neto del núcleo (entrada −
salida) **a 0,0000 mL** en cada minuto, para infusiones de 5, 15, 20 y 60 min. La ganancia total es `1000·e = 125 mL` en todas. Descartada «doble redistribución» y «masa que aparece o
desaparece».

Cristaloide retenido (mL) con el núcleo vigente `(e, s, τ) = (0,125; 0,6; 30)`:

| minuto | 1 L instantáneo | 1 L en 15 min | 1 L en 20 min | 1 L en 60 min |
|---|---|---|---|---|
| 5 | 113,5 | 39,3 | 29,5 | 9,8 |
| 10 | 103,7 | 75,1 | 56,4 | 18,8 |
| 15 | 95,5 | **108,0 (pico)** | 81,0 | 27,0 |
| 30 | 77,6 | 85,2 | 88,6 | 48,3 |
| 60 | 60,2 | 63,0 | 64,2 | **81,9 (pico)** |
| 70 | 57,3 | 59,3 | 60,2 | 72,8 |
| 120 | 51,4 | 51,8 | 51,9 | 54,3 |

Picos retenidos: 118 (5 min) > 108 (15) > 104 (20) > 82 (60). **La infusión lenta sí se comporta como lenta:** expande menos y más tarde. Alcanza al bolo de 15 min sólo hacia el minuto
48, porque sus porciones tardías tuvieron menos tiempo de salir. Todas convergen al mismo piso permanente (`1000·e·(1−s) = 50 mL`).

## §5 · P3-304 · Compatibilidad con la región cerrada

La región de comportamiento (V-2, FD-BLD-04/05/06) se expresa sobre una **bolsa de 1 L en 20 min**: `Rpico ∈ [0,15; 0,27072]`, `R30 ∈ [0,15; 0,25]`, `R60 ∈ [0,10; 0,20]`,
`R120 ∈ [0,05; 0,15]` (fracción de lo infundido retenida). Resultados medidos:

| lectura (bolsa de 20 min) | núcleo vigente | rango cerrado | situación |
|---|---|---|---|
| Rpico | 0,1038 | [0,15; 0,27072] | **por debajo** |
| R30 | 0,0886 | [0,15; 0,25] | **por debajo** |
| R60 | 0,0642 | [0,10; 0,20] | **por debajo** |
| R120 | 0,0519 | [0,05; 0,15] | dentro |

Esto **no es nuevo**: es el punto provisional `HISTORICAL_PROVISIONAL_NON_SURVIVING_REFERENCE` ya documentado en `docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md` §2.4 y §6.2 (TD-88). El
tiempo de ejecución sigue con ese punto porque la región es una **región**, no un punto aprobado. **El FR-G se revisó con un núcleo que retiene MENOS de lo que la región exige.**

¿Predice la región un efecto más débil de la infusión lenta, que el tiempo de ejecución implementaría mal? **No: predice uno más fuerte.** Para 1 L en 60 min al minuto 60:

| | retenido a los 60 min | cociente con el vigente | parte del sangrado concurrente (150 mL) |
|---|---|---|---|
| núcleo vigente | 81,9 mL | 1,00 | 55 % |
| punto menos protector de la familia (e,s,τ) dentro de la región | 134,6 mL | 1,64 | 90 % |
| **cota para cualquier núcleo que no suba con la edad** dentro de las bandas cerradas | **≥ 125,0 mL** | ≥ 1,53 | **≥ 83 %** |
| punto más protector de la familia | 234,0 mL | 2,86 | 156 % |

La cota general no depende de la familia de tres parámetros: con `K(a)` la fracción retenida de un mL a `a` minutos y `K` no creciente, `R30` da `Σ K(11..30) ≥ 20·0,15` y por tanto
`K(1..10) ≥ 0,15`; `R60` da `Σ K(41..60) ≥ 20·0,10` y por tanto `K(31..40) ≥ 0,10`; la suma de las cuatro ventanas es ≥ `(1000/60)·(30·0,15 + 30·0,10) = 125 mL`. El modelo y
`volume_behaviour_record` comparten la propiedad (`UNREACHABLE_THE_MODEL_ONLY_DECAYS`).

Pasadas por el núcleo real (presión sistólica al minuto 60; sin tratar 80,9; llegada 98,0):

| núcleo | PAS a 60 min | % de la caída sin tratar que evita |
|---|---|---|
| vigente (e=0,125; s=0,6; τ=30) | 91,6 | **63 %** |
| punto menos protector dentro de la región (e=0,2017; s=0,865; τ=57,5) | 97,2 | **95 %** |

**Mover el modelo hacia la región hace que el FR-G proteja MÁS, no menos.** Ninguna corrección «general» del cristaloide que reduzca la protección puede satisfacer a la vez FD-REVIEW-04.

## §6 · P3-305 · Veredicto

| clase | resultado | por qué |
|---|---|---|
| A · error de integración de la infusión continua | **descartada** | el núcleo coincide con la convolución independiente a 0,0000 mL en todos los minutos y duraciones; la infusión lenta expande menos y más tarde que la rápida |
| **B · región cerrada demasiado protectora para infusión lenta** | **respaldada** | todo núcleo dentro de las bandas cerradas retiene al menos 125 mL de 1 L en 60 min (≥ 83 % del sangrado concurrente); el vigente (55 %) ya está por debajo de la región |
| C · acoplamiento de presión amplifica un volumen pequeño | **descartada** | la parte de la caída de presión que se evita (62,9 %) sigue a la parte del déficit de volumen que se evita (61,0 %); la pendiente es 0,12–0,14 mmHg/mL al perder y 0,11 al ganar volumen |
| D · tasa o momento del sangrado explican la protección aparente | **factor de escala, no defecto** | el sangrado es constante y activo en todos los minutos (sin artefacto de momento); la tasa fija la **escala** (§7), pero está acoplada al curso sin tratar que la docencia aceptó (FD-REVIEW-01) |
| E · mecanismos múltiples | no | un mecanismo (B) explica el hallazgo; D es un factor de escala |

Sensibilidad a la tasa de sangrado (**sensibilidad, no objetivo ni corrección**): % de la caída sin tratar que evita 1 L en 60 min, al minuto 60:

| tasa (mL/min) | núcleo vigente | punto menos protector de la región |
|---|---|---|
| 2,5 (la vigente) | 63 % | 95 % |
| 3,5 | 46 % | 74 % |
| 5,0 | 34 % | 54 % |

## §7 · P3-306 · Parada, y la decisión docente exacta

El encargo ordena, para B: **DETENERSE antes de cambiar la región cerrada y decir la decisión docente exacta que se necesita.** No se tocó la región, no se movió el núcleo y no se
ajustó nada al FR-G (FD-REVIEW-03 y P3-306A).

Tres anclas son verdad a la vez en el repositorio, y la expectativa del FR-G no cabe con las tres:

* **(a)** la región de volumen cerrada y las bandas `R30/R60/R120/Rpico` (FD-REVIEW-04);
* **(b)** el curso sin tratar aceptado, con su tasa de sangrado de 2,5 mL/min (una coordenada **candidata** acoplada a `U-OUT`, que los dos casos cruzan en 2,75: §7.2 de la calibración) y el acoplamiento de presión (FD-REVIEW-01);
* **(c)** la expectativa del FR-G: atenuación modesta y transitoria, trayectoria más cerca de la no tratada que de una reanimada (FD-REVIEW-02).

**La decisión (una sola; el repositorio no elige).** Con (a) y (b) fijos, 1 L en 60 min evita entre el 83 % y más del 100 % del sangrado concurrente. Cumplir (c) exige que la
docencia ceda **una** de las tres:

1. **Ceder (b), reabrir la tasa de sangrado:** decir qué intensidad pretende para «hemorragia activa» en los dos casos (mL/min o % de volemia/h). Cambia el curso sin tratar y toca FR-A, FR-C, FR-D, FR-E y `U-OUT`.
2. **Ceder (a) sólo para infusión lenta:** definir una restricción nueva de retención para infusiones lentas (p. ej., el volumen efectivo retenido a los 60 y 120 min de 1 L en 60 min, o qué fracción del sangrado concurrente debe compensar), o rebajar los pisos `R30/R60/Rpico`. Una restricción que dependa de la velocidad **no cabe en un núcleo invariante en el tiempo**: exige física nueva en un sucesor certificado del núcleo («Enmienda 3», en su propia rama), porque `clinical_core/` no se edita desde la Fase 3.
3. **Aceptar el modelo:** reclasificar el FR-G como `ACCEPT_WITH_LIMITATION`, dejando escrito que «1 L en 60 min compensa más de la mitad de un sangrado de 150 mL/h».

**Recomendación:** formular primero la pregunta en volumen efectivo, que es la coordenada propia del modelo y la que la calibración ya recomendaba (§7.3), sin objetivo en mmHg:
*«Con sangrado continuo, ¿qué fracción del volumen perdido en esos 60 min debe compensar 1 L en 60 min al minuto 60 y al 120?»* El modelo da hoy el 55 % (82 de 150 mL) y ninguna región
cerrada da menos del 83 %. La respuesta decide cuál de las tres salidas aplica sin ajustar la curva.

## §8 · P3-307, P3-308, P3-310 y P3-312 · Lo que no corresponde hacer, y su razón

* **P3-307 (recertificación de volumen):** no cambió ningún comportamiento ejecutable, así que no hay nada que recertificar. Lo que sí se verificó (ya en §4): balance de masa, monotonía (el pico baja al alargar la infusión) y orden por velocidad (a igual volumen, la bolsa corta expande más y antes; la lenta la alcanza hacia el minuto 48 y todas convergen al mismo piso).
* **P3-308 (no regresión de GI):** sin cambios ejecutables la no regresión es por construcción; además el arnés **reproduce las presiones comprometidas de FR-A, FR-B, FR-C, FR-D, FR-E y FR-G**, y el conjunto fijado por digesto y el punto de control P3-300 siguen idénticos. FR-F no cambia: la parada es la misma.
* **P3-310 (`FR-G_V2_CANDIDATE`):** **no se generó.** Una trayectoria V2 sale de una corrección ejecutable y ninguna está autorizada hasta que la docencia decida (§7). Un V2 inventado para tener algo que mostrar sería exactamente el ajuste directo que FD-REVIEW-03 prohíbe.
* **P3-312 (certificación):** el encargo la pide si cambia `clinical_core/` o la física de ejecución; no cambió, así que no corresponde congelar un candidato ni correr la suite completa. Se corrieron las pruebas focalizadas de lo tocado y las guardas dependientes (ver el cierre del informe).

## §9 · P3-309 · Sangrado continuo y control de fuente (sólo lectura)

¿Sigue activo el sangrado tras cristaloide, glóbulos o ambos? **Sí, a 2,5 mL/min en todos los minutos** (la hemostasia del módulo GI sólo existe si el motor heredado decidió una
endoscopia, y ningún escenario revisado la lleva). Pregunta docente principal: ¿la mejoría temprana se estabiliza o se revierte bajo sangrado continuo? **Se revierte, lentamente.**
Órdenes de FR-B (vía, 1 L en 15 min, 2 U de glóbulos, reevaluar 20 min) llevadas a 400 min, sin control de fuente:

| caso | llegada PAS | PAS 30 | PAS 60 | pico (minuto) | PAS 90 | PAS 120 | PAS 180 | PAS 240 | PAS 360 | pendiente tras el pico | cruza por debajo de la llegada | sin tratar a 60 / 120 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 57 m (FR-B) | 88 | 111,6 | 125,5 | 127,6 (65) | 123,5 | 118,3 | 106,8 | 93,1 | 84,9 | −0,20 mmHg/min | minuto 261 | 72,6 / 57,9 |
| 72 f (mismas órdenes) | 98 | 124,3 | 139,8 | 142,1 (65) | 137,5 | 131,7 | 118,9 | 103,7 | 94,6 | −0,22 mmHg/min | minuto 261 | 80,9 / 64,5 |

La mejoría tiene un pico hacia el minuto 65 y desde entonces cae sin parar al ritmo del sangrado: no hay meseta. Sigue por encima de la llegada más de cuatro horas y la cruza hacia el
minuto 261 en los dos casos. Respecto de la limitación docente del FR-B («la trayectoria no debe sugerir que la reanimación sola trata una hemorragia no controlada»): el modelo **ya**
respeta la dirección —la mejoría se revierte y acaba por debajo de la llegada—, pero la **escala de tiempo** es lenta (más de 4 h) y la mejoría inicial es grande (+24 mmHg sobre la
llegada a los 30 min en el 57 m; +44 en el pico del 72 f). Eso es un hallazgo, no una corrección: la docencia no pidió cambiarlo y FD-REVIEW-05 prohíbe inventar control de fuente.

## §10 · P3-311 · Revisión adversarial (del análisis; no hay cambio ejecutable que atacar)

Cada ataque se resolvió con un hecho medido, no con un argumento:

| ataque | resultado |
|---|---|
| la infusión lenta sigue tratada como bolo | refutado: convolución independiente = núcleo a 0,0000 mL; pico 82 vs 108 mL |
| rápida y lenta idénticas | refutado: picos 118 / 108 / 104 / 82 mL; orden temprano verificado |
| la masa aparece o desaparece | refutado: ganancia total `1000·e` en todas las velocidades; neto = analítico |
| redistribución aplicada dos veces | refutado: una sola fuga coincide con el analítico; dos la romperían |
| el sangrado se detiene sin querer | refutado: 2,5 mL/min en todos los minutos de FR-G, sin tratar y FR-B a 240 min |
| rama específica del FR-G | ausente: guarda sobre todos los fuentes de ejecución y de `clinical_core/` |
| región de volumen violada | **el vigente ya está por debajo de la región** (documentado desde P3-82); este trabajo no lo cambia |
| FR-B / tratamiento tardío rotos | nada cambió; el arnés reproduce FR-B, FR-C y FR-E al compromiso de la autoridad |
| artefacto de autoridad o réplica no coinciden | sin cambio ejecutable; el arnés reproduce las presiones comprometidas de las seis trayectorias |
| se sobrescribió el historial humano | refutado: digestos del conjunto y de cada escenario fijados y comprobados; P3-300 byte a byte igual |

Ataques contra **mi propio análisis**: (1) *el arnés podría no ser lo que vio la revisora* → primera corrida con `Encounter.order` pelado reprodujo FR-G pero **no** FR-B (esperaba la
infusión completa entre órdenes); se descubrió y se corrigió con la regla de turnos de la página, y la reproducción de las seis trayectorias pasó a ser una prueba. (2) *la
conclusión podría depender de la familia de tres parámetros* → se añadió la cota general para cualquier núcleo no creciente. (3) *los escenarios de presión se miden sobre el núcleo
por omisión, no sobre la instantánea de presión* → las presiones reproducidas coinciden con las comprometidas por la autoridad al redondeo.

## §11 · Norepinefrina: hoja de ruta (no implementada)

Registrada en `TD-147` como trabajo futuro de alta prioridad (FD-REVIEW-06): norepinefrina → tono vascular común `T` → presión y perfusión → entrega y deuda posteriores, con la
interacción de volumen y bomba. Hoy el simulador **se detiene** ante la orden (FR-F, parada correcta aceptada por la revisora). No se creó ningún contribuyente ni se tocó la parada.

## §12 · Punto de control P3-313

Ver `docs/revision/PHASE3_FIRST_FACULTY_REVIEW_CHECKPOINT.json`. `FIRST_HUMAN_FACULTY_REVIEW_RECORDED: SÍ` · `FR_G_ROOT_CAUSE: B` · `VOLUME_REGION_STATUS: cerrada e intacta; el punto
de ejecución vigente está fuera de ella por debajo` · `GI_NONREGRESSION: sin cambio ejecutable; presiones comprometidas reproducidas` · `SOURCE_CONTROL_ANALYSIS: el sangrado sigue
activo; la mejoría se revierte lentamente` · `FR_G_V2_READY_FOR_HUMAN_REVIEW: NO (no hay corrección autorizada)` · **global: `B · FR_G_REQUIRES_NEW_FACULTY_VOLUME_DECISION`.**

## §13 · Límites de este análisis

* Es `MODEL_ANALYSIS`: explica el modelo, no lo valida clínicamente. Los números son del modelo vigente y de sus parámetros históricos.
* El arnés reproduce las presiones comprometidas redondeadas de seis trayectorias; no es un reemplazo de la página real.
* El barrido de la región usa una malla de 100 × 121 puntos (s, τ) con el intervalo exacto de `e`; la cota general de 125 mL no depende de ella, pero **supone** que la fracción retenida de un mL no sube con su edad.
* Las sensibilidades a la tasa de sangrado son contrafactuales dentro de este proceso; no son una propuesta ni un objetivo.
* El FR-G sólo tiene dos puntos comprometidos (60 y 70 min); la curva de 0 a 70 min sale del núcleo, no de lo que la revisora vio.
