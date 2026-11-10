# Fase 3 · Generalización de la causalidad de manejo (P3-137 a P3-144)

Rama `phase-3-runtime-integration`, con la enmienda `PHASE2_AMENDMENT_1` **certificada e integrada**. Registro:
`management_generalization_record.py`. Pruebas: `test_management_generalization.py` (79; cada cifra del registro
se recalcula ahí). Este documento resume; no sustituye al registro ni lo duplica.

Todo es **medición de desarrollo** en un simulador educativo. Las regiones son `DEVELOPMENT_TEST_REGION`: no son
verdad clínica, ni dosis, ni recomendación para pacientes reales, ni valores aprobados, y ninguna se adopta en un
perfil comprometido. No hay ajuste de curvas a la salida heredada: se prueba dirección, temporalidad,
especificidad causal, orden de dosis, reversibilidad y coste de esperar.

## 1 · Integración de la enmienda (P3-INTEGRATE-AMEND1)

La base común de las dos ramas era `d087cc3`, y la Fase 3 la había revertido (`e1eb797`). Un merge directo habría
tomado en silencio el lado del revert. Se hizo en dos commits normales: revertir el revert (`601452c`, árbol igual
al de `d087cc3`) y un merge sin *fast-forward* de la rama certificada en su HEAD de promoción `0c230f8` (merge
`534aa50`). **El árbol integrado es el mismo objeto que el de `0c230f8`**, así que el estado ejecutable es, byte a
byte, el certificado (candidato `0b3c443`: 11 195 pruebas, 0 fallas, 0 errores). Por eso la suite completa de la
Fase 2 queda `ALREADY_VALID_ON_EQUIVALENT_CODE` y no se repitió. Sobre la rama integrada, con el linaje real y
sin vista previa: 22 archivos, 602 pruebas, 0 fallos.

Sin cambio: `COMMON_CORE_RUNTIME_AUTHORITY = False`, `LIVE_FAMILIES = ("gi_bleed",)`, residente, puntuación y
primer piloto.

## 2 · Región de transmisión respiratoria (C3)

Objetivo de desarrollo (decisión docente previa): en `opioid_35m`, sin tratar, SpO2(60) ∈ [78, 88] %. La región
de `hypoventilation_oxygenation_transmission_fraction` es la preimagen de ese objetivo bajo la ecuación
certificada, **derivada dos veces** —por la fórmula y por bisección de la simulación— y no copiada:

| Caso | SpO2(60) con f = 0 | ΔPaCO2(60) | Cota de f | SpO2(60) con f = 1 |
|---|---|---|---|---|
| `opioid_35m` | 80,0 | 24,21 | **0,060621** (ata) | 25,25 |
| `opioid_67f` | 84,0 | 21,40 | 0,233153 | 37,22 |
| `asthma_49m` | 89,0 | 10,07 | no ata | 79,65 |
| `asthma_24f` | 90,0 | 10,78 | no ata | 80,88 |

Región común: **f ∈ [0, 0,060621]**, con R = 0,8 declarado. Sólo se identifica el cociente f/R; el techo de 88 %
no ata. Testigos **sólo para prueba**: LOW 0,015 · CENTER_REFERENCE 0,03 · HIGH 0,06 (el central no es preferido).
Veredicto: **`RESPIRATORY_DEVELOPMENT_REGION_REPRODUCED`**.

## 3 · Opioide: seis vías en cada testigo (C4)

Sin tratar · oxígeno · naloxona · ambos · naloxona tardía · esperar, sobre `opioid_35m`, 90 minutos.

- **Sin tratar:** disponibilidad central ↓, FR ↓, ventilación ↓, PaCO2 ↑ y SpO2 ↓, monótonos.
- **Oxígeno:** sube la SpO2 y no toca disponibilidad, FR, ventilación ni PaCO2. En el estado sólo mueve el FiO2.
- **Naloxona:** el único canal de estado que escribe es la disponibilidad central; FR y ventilación suben, el
  PaCO2 baja y la SpO2 sube aguas abajo. Nada se mueve antes del minuto en que se da. A fracción 0 la reversión
  corrige la ventilación y la SpO2 no se mueve: **no hay escritura directa naloxona → SpO2**.
- **Ambos:** la rama ventilatoria es idéntica a la de la naloxona sola y la SpO2 supera a cualquiera de las dos.
- **Tardía:** pierde en la integral de FR, ventilación y SpO2 aunque el punto final se acerque.
- **Esperar:** reevaluar no cambia la fisiología; el tiempo sin acción cuesta.

Cada brazo corre sin huecos y se reproduce digesto a digesto. Veredicto: **`OPIOID_MANAGEMENT_CAUSALITY_READY`**
(`READY_WITH_REGION`). Las lecturas derivadas son función del estado del minuto, así que la cadena se ordena por
el grafo y empieza en el minuto de activación: no hay un retraso de un minuto entre eslabones.

## 4 · Asma con la misma región (C5)

Sin ningún ajuste propio. Con el enlace declarado en cada testigo, en `asthma_49m` y `asthma_24f`:

- eficiencia mecánica, FR, ventilación y PaCO2 **idénticos bit a bit** a la corrida sin enlace;
- la SpO2 se desplaza siempre a la baja, creciendo con el PaCO2 y con la fracción, sin oscilar: como máximo
  −0,84 puntos a 120 minutos en el testigo alto; ningún límite grave nuevo;
- ningún canal de estado se mueve salvo el lector ya certificado de la SpO2; reproducción exacta.

Las diez sondas propias de la etapa P2S-3, vueltas a correr con el enlace: seis pasan sin cambio. En tres cambia
exactamente la afirmación previa al enlace de que «sólo se mueve la mecánica» (ahora la SpO2 sigue a la
ventilación, y por ella la entrega y la FC; el alivio de la mecánica **sube** la SpO2). La décima declara un
impulso hipoxémico y el invariante de P2T-5 la rechaza junto al enlace. Veredicto:
**`RESPIRATORY_TRANSMISSION_GENERALIZES`**, con esa salvedad declarada: leído de forma estricta, esas tres
condiciones dejan de cumplirse con cualquier transmisión no nula; son lo que el enlace sustituye.

## 5 · Contraste educativo (C6)

`opioid_35m`, testigo central. FR · ventilación · PaCO2 · SpO2 · entrega relativa de O2:

| Minuto | Sin tratar | Oxígeno desde 10 | Naloxona en 20 |
|---|---|---|---|
| 15 | 5,57 · 0,54 · 74,4 · 79,8 · 1,00 | 5,57 · 0,54 · 74,4 · **85,6** · 1,07 | igual que sin tratar |
| 30 | 5,16 · 0,50 · 80,2 · 79,6 · 0,99 | 5,16 · 0,50 · 80,2 · **85,4** · 1,07 | **12,00 · 1,16 · 34,5** · 81,3 · 1,02 |
| 60 | 4,44 · 0,43 · 93,2 · 79,0 · 0,99 | 4,44 · 0,43 · 93,2 · **85,1** · 1,06 | **15,12 · 1,46 · 27,4** · 81,5 · 1,02 |
| 90 | 3,82 · 0,37 · 108,3 · 78,4 · 0,98 | 3,82 · 0,37 · 108,3 · **84,6** · 1,06 | **15,23 · 1,47 · 27,2** · 81,5 · 1,02 |

El soporte de oxígeno mejora la saturación mientras la falla ventilatoria persiste (la FR sigue cayendo y el PaCO2
subiendo). La reversión corrige primero la ventilación y la oxigenación aguas abajo. En toda lectura posterior a
ambos, el oxígeno muestra **más** saturación con **peor** ventilación: la saturación sola no distingue. Es una
propiedad del simulador, no una recomendación.

## 6 · Edema pulmonar: descongestión (C7)

Vía existente, sin fisiología común nueva: orden decongestiva → `DecongestiveTreatment(id, begins_at_minute)`
(una señal: no escribe nada) → `EdemaCongestion` deja de progresar y retira agua pulmonar a su tasa, nunca por
debajo de la llegada → **L** → **G** → SpO2 y entrega.

**Región de prueba de desarrollo** para la tasa: **[0,0025; 0,01] por minuto simulado**, con testigos 0,0025 ·
0,005 · 0,01. Confianza **0,82**. Es el tramo de tasas de agua pulmonar que la propia familia declaró en P2P-1
antes de cualquier corrida, y su centro es la única tasa de descongestión que el repositorio enuncia. Los
veredictos del contrato son los mismos en los tres testigos y también a tasas 2,5 veces menores y 2 veces
mayores, así que la conclusión no depende de dónde esté la verdad dentro de la región. **Falsador:** una
observación redactada tras el tratamiento que implique una tasa fuera del intervalo, o que el tratamiento no deba
volver a la congestión de llegada.

**Exposición:** `PulmonaryEdemaAdapter.development(testigo)`, un adaptador aparte y fuera de línea. El adaptador
registrado no lleva tasa y sigue declarando las órdenes decongestivas como hueco: por omisión no cambia nada.

Seis vías, 180 minutos, en cada testigo: sin tratar progresa (SpO2 81,0 → 77,8); la descongestión mueve primero
L (y G con él), la SpO2 vuelve a la de llegada —al minuto 79, 55 y 43 según el testigo— y **nunca la supera**; el
oxígeno sube la saturación y **no toca L**; juntos se suman; la tardía pierde en la integral; esperar no es un
tratamiento. Veredicto: **`PULMONARY_EDEMA_MANAGEMENT_CAUSALITY_READY`** (`READY_WITH_REGION`). Límites: la FR no
lee el agua pulmonar en este perfil; un solo caso; el escritor tiene una sola tasa, así que una segunda orden
decongestiva no añade nada.

**Defecto encontrado y corregido.** Los adaptadores de edema, TEP y asma listaban el oxígeno como mapeado y
heredaban un método base que no construía ningún contribuidor: la orden ni se aplicaba ni se declaraba como
hueco. FD-P3-100 afirmó que el oxígeno estaba mapeado y era causalmente correcto en las tres; por el camino del
adaptador no tenía efecto. El método base construye ahora el oxígeno que declara. Afecta sólo a adaptadores de
sombra fuera de línea.

## 7 · ACS: llegada en vivo (C8)

El único mapeo certificado de estado vivo → anclas (`legacy_adapter.anchors_from_legacy`) rechaza toda familia
que no sea GI: `FAMILY_CASE_PARAMETER_RULES` no tiene regla para ACS. La referencia de ACS devuelve la llegada de
**un** caso redactado y no lee el encuentro; cinco parámetros de caso son sondas sintéticas en bandas de ese
caso. Derivarlos del estado vivo para las variantes que el motor redacta es semántica clínica nueva. Veredicto:
**`ACS_ARRIVAL_MAPPING_REQUIRES_NEW_SEMANTICS`**. ACS no entra en la lista en vivo; su cadena de manejo sigue
completa fuera de línea. (Para el único caso declarado bastaría una identidad vigilada, sin semántica clínica
nueva, pero es una regla de mapeo nueva: decisión metodológica que aquí no se toma.)

## 8 · Suite multifamilia y punto de control (C9, C10)

| Familia | Mecanismo | Intervención que la define | Canal primario | Estado | ¿Completa? |
|---|---|---|---|---|---|
| GI | volumen / hemorragia | transfusión | V | `CAUSALLY_READY` | sí |
| ACS | bomba / reperfusión | reperfusión, en el reloj del motor | P | `CAUSALLY_READY` (fuera de línea) | sí |
| Opioide | impulso central / ventilación | naloxona | disponibilidad central | `READY_WITH_REGION` | sí |
| Edema pulmonar | congestión / descongestión | tratamiento decongestivo | L | `READY_WITH_REGION` | sí |
| Asma | mecánica | broncodilatador | eficiencia mecánica | `MISSING_TREATMENT_WRITER` | no |
| TEP | obstrucción | anticoagulación / trombólisis | P | `MISSING_COMMON_MECHANISM` | no |

Las cuatro completas pasan el contrato genérico entero (dirección, temporalidad, especificidad, plausibilidad,
orden de dosis y reversibilidad donde aplican, tiempo sin acción, seguridad); sus canales primarios son todos
distintos y cada tratamiento mueve primero el suyo. El oxígeno es consistente en las seis y no escribe ningún
canal primario.

**Veredicto: `A · MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT`** — cuatro vías de manejo
mecanísticamente distintas y completas. Es preparación de **simulación** para desarrollo. **No** es preparación
para despliegue con residentes ni validación clínica: dos de las cuatro vías descansan en regiones de prueba sin
aprobación docente, ACS no está en vivo, y sólo GI corre en sombra en vivo.

**Camino hacia una revisión de preparación para piloto (sólo diseño; el primer piloto no se toca).** Quedan
abiertas todas las compuertas: exposición en tiempo de ejecución, exposición en la interfaz, captura de traza,
aislamiento de la puntuación, revisión docente, selección de casos, visibilidad de fallos, vuelta atrás y
salvaguardas frente al residente. El paso siguiente más corto y seguro es una **decisión docente sobre las dos
regiones de desarrollo**, porque todas las demás compuertas dependen de cuál es la fisiología que se expondría.

## 9 · Decisiones docentes del 2026-11-10 y rectificación (posterior a este informe)

Este informe es el del ciclo que terminó en `39dee52`. Después, la docencia decidió sobre él (FD-P3-129 y
FD-P3-130; detalle en `docs/PHASE3_SECOND_LIVE_FAMILY.md` §1–§2):

- **Región respiratoria (§2).** Aprobada como **región matemática de desarrollo** f ∈ [0; 0,060621], con R = 0,8
  declarado, y distinguida de la **región causal activa** f ∈ (0; 0,060621]: f = 0 es un control negativo, no
  un testigo de la cadena. Los testigos siguen siendo sólo de prueba; el central no es preferido; ningún perfil
  comprometido adopta uno. Confianza 0,84.
- **Región del edema (§6).** Aprobada como `DEVELOPMENT_TEST_REGION`, confianza 0,82: para demostrar causalidad
  de manejo en simulación, no como calibración clínica, guía de dosis ni valor de producción.
- **Asma (§4).** La salvedad queda resuelta: las tres condiciones de P2S-3 están **sustituidas** donde chocan
  con el enlace certificado, con invariantes causales que conservan su intención; no se borraron.
- **Testigos.** No entran en los adaptadores registrados de opioide ni de asma; el opioide los corre en vivo
  como conjunto por región.
- **ACS (§7).** El bloqueo de llegada sigue en pie; ACS queda listo fuera de línea.
- **Hito (§8).** `MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT`: GI — V / pérdida de volumen; ACS
  — P / reperfusión — fuera de línea; opioide — disponibilidad central / ventilación — `READY_WITH_REGION`;
  edema pulmonar — L / descongestión — `READY_WITH_REGION`. **No implica preparación del runtime en vivo.**

**Rectificación (FD-P3-134, L1).** La auditoría en vivo encontró que el adaptador del opioide mapeaba la
naloxona al propio minuto del motor. Corregido: una orden ejecutada en el minuto m aparece en el estado m + 1,
como el oxígeno. Las cifras de naloxona de este informe se movieron un minuto —la tabla de §5 y el bloque
`MEASURED` del registro ya llevan las nuevas— y ningún veredicto cambió. La frase de §3 «nada se mueve antes
del minuto en que se da» sigue siendo cierta.

**Numeración.** Este informe llama P3-137 a P3-144 a sus paquetes; el ciclo siguiente recibió del encargo los
números P3-137 a P3-146 para otros. Ver FD-P3-131.
