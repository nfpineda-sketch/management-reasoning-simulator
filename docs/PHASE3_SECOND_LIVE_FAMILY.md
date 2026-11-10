# Fase 3 · Segunda familia en sombra en vivo: opioide (ciclo del 2026-11-10)

Rama `phase-3-runtime-integration`, desde `39dee52`. Registro: `second_live_family_record.py`. Pruebas:
`test_indirect_feedback_audit.py` (41) y `test_opioid_live_shadow.py` (88); cada cifra del registro se
recalcula ahí. Este documento resume; no sustituye al registro.

**Numeración.** El encargo de este ciclo numera sus paquetes P3-137 a P3-146. El ciclo anterior había usado
P3-137 a P3-144 como etiquetas propias de otros paquetes (`docs/PHASE3_MANAGEMENT_GENERALIZATION.md`). Ninguna
se reescribe: aquí «P3-13x» es siempre la del encargo de este ciclo, y en código y pruebas lleva una «L»
(`p3l`, `opioid/P3-141L`).

Todo es **sombra de desarrollo sin autoridad**. `COMMON_CORE_RUNTIME_AUTHORITY = False`. Nada de lo que sigue
lo ve un residente, entra en la puntuación ni toca el primer piloto. Las regiones son
`DEVELOPMENT_TEST_REGION`: no son verdad clínica, ni dosis, ni valores de producción. No se afirma validación
clínica y nada se ajusta a las curvas del motor heredado.

## 1 · Decisiones docentes consolidadas (P3-137)

| Decisión | Contenido |
|---|---|
| FD-NEW-1 | **Región matemática** de la fracción de transmisión: f ∈ [0; 0,060621], con R = 0,8 declarado. **Región causal activa:** f ∈ (0; 0,060621]. f = 0 es un control negativo: pertenece a la región representable y no expresa nada aguas abajo del PaCO2, así que no puede mostrar la cadena completa. Testigos **sólo de prueba**: LOW 0,015 · CENTER_REFERENCE 0,03 · HIGH 0,06; el central no es preferido; ningún perfil comprometido adopta uno. Confianza 0,84. |
| FD-NEW-2 | Edema: `decongestion_per_min` ∈ [0,0025; 0,01] como `DEVELOPMENT_TEST_REGION`, confianza 0,82, para demostrar causalidad de manejo en simulación. No es calibración clínica, ni guía de dosis, ni valor de producción. |
| FD-NEW-3 | Las tres condiciones de P2S-3 que exigían «sólo se mueve la mecánica» quedan **sustituidas** donde chocan con el enlace certificado. No se borran (§2). |
| FD-NEW-4 | Los testigos no son valores por omisión de los adaptadores de opioide ni de asma. Donde la sombra en vivo necesita el parámetro, corre un **conjunto por región** y nunca elige el central en silencio. |
| FD-NEW-5 | ACS: no se inventa un mapeo de llegada en vivo. `ACS_ARRIVAL_MAPPING_REQUIRES_NEW_SEMANTICS` sigue en pie; ACS queda causalmente listo **fuera de línea**. |
| FD-NEW-6 | Sin fisiología nueva en este ciclo: ni broncodilatador, ni tratamiento del TEP, ni VNI, ni antiagregación o anticoagulación, ni fisiología común. |
| FD-NEW-7 | `CLAUDE.md` distingue el **cierre histórico de la Fase 2** del **sucesor certificado vigente**, sin borrar la identidad del cierre. |

**Hito sobre el que descansan:** `MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT`, cuatro vías
completas y distintas: GI — V / pérdida de volumen; ACS — P / reperfusión — **fuera de línea**; opioide —
disponibilidad central / ventilación — `READY_WITH_REGION`; edema pulmonar — L / descongestión —
`READY_WITH_REGION`. **Ese hito no implica preparación del runtime en vivo.**

## 2 · Sustitución de las tres sondas de asma (P3-137A)

`PHASE2_AMENDMENT_1` certificó que la ventilación llega a la oxigenación por el PaCO2. Una condición que exigía
que la saturación, y lo que la lee, se quedaran quietas mientras la ventilación se movía sólo es verdad donde
el enlace no expresa nada. Los registros congelados de P2S-3 **no se modificaron**.

| Sonda | Propósito histórico | Expectativa antigua | Por qué cambia | Invariante causal nuevo | Evidencia histórica que sigue reproduciéndose |
|---|---|---|---|---|---|
| `untreated` | una obstrucción sin tratar empeora por la mecánica y por nada más | `only_mechanics_moves` y `states_identical_but_mechanics` (quedan sustituidas: SpO2, FC, índice de entrega y la identidad de estados) | el PaCO2 que sube baja la saturación; la entrega es proporcional a ella y la FC la lee por el término de hipoxemia ya certificado | mecánica → ventilación → PaCO2 → oxigenación, en esa dirección y por ningún otro camino: FR, G, L, D, lactato, consciencia y PAM siguen idénticos; la SpO2 es **exactamente** la de la ecuación certificada sobre el PaCO2; la entrega se mueve sólo en proporción; a fracción 0 la condición antigua se cumple entera | sobre el perfil comprometido del asma (enlace sin declarar) la sonda pasa con todas sus condiciones |
| `relief` | un alivio de la mecánica es representable por el objetivo común | `rr_spo2_hr_unchanged` | el PaCO2 que baja sube la saturación; la FR sigue igual | el alivio sube W, baja el PaCO2 y deja la FR idéntica; la SpO2 **nunca** es menor que sin alivio y es mayor una vez que actuó; nada antes de que empiece; la ganancia es 0 a fracción 0 y crece con la fracción | la sonda pasa sobre el perfil comprometido |
| `heart_rate` | el perfil del asma no añade ninguna ganancia propia | `gains_untouched` | un perfil que declara el enlace difiere en los dos campos del enlace; ninguno es una ganancia | un testigo difiere del perfil comprometido en **exactamente** el cociente respiratorio y la fracción, y la descomposición de la FC de llegada no cambia | la sonda pasa sobre el perfil comprometido |

Además: la fracción **no escribe la mecánica** (eficiencia, FR, W, PaCO2 y pH idénticos bit a bit en todo el
barrido); las seis sondas que nunca chocaron siguen pasando con el enlace; la décima, que declara un impulso
hipoxémico, la rechaza el propio núcleo junto al enlace.

## 3 · Auditoría del lazo indirecto, TD-130 (40) (P3-138)

Grafo ejecutable completo, arista por arista (detalle en `FEEDBACK_GRAPH`):

`SpO2 → entrega → déficit efectivo → carga ácida → impulso → FR → W → PaCO2 → SpO2`

| Arista | Clase | Dónde |
|---|---|---|
| SpO2 → entrega | siempre activa, lineal, mismo minuto | `relative_delivery` |
| entrega → déficit | **umbral**: 0 mientras el índice de entrega supere demanda / reserva = **0,4** | `effective_oxygen_deficit` |
| déficit → carga ácida | retrasada un minuto; acumulador con fuga | `_acid_burden` |
| carga ácida → impulso | siempre activa | `respiratory_drive` |
| impulso → FR | saturante; por la disponibilidad central de la familia | `rate_from_drive` |
| FR → W → PaCO2 | siempre activa; indefinida en apnea (frontera sin resolver) | `alveolar_ventilation`, `respiration` |
| PaCO2 → SpO2 | siempre activa con f > 0; nada a f = 0 | `ventilated_oxygenation` |
| SpO2 → impulso hipoxémico | **deshabilitada**: declararla con el enlace es un error del núcleo | `HYPOXEMIC_FEEDBACK_LOOP_DEFERRED` |
| déficit → D | retrasada, acumulador; D no alimenta la respiración | `_oxygen_debt` |
| déficit → tono | retrasada; rama **positiva** previa al enlace, con la misma compuerta | `tone_target` (P2J-2) |
| SpO2 → impulso simpático → FC | termina en una lectura; la FC no entra en el gasto | `sympathetic_target` |

- **Cuándo puede cerrarse:** sólo con déficit efectivo, es decir con el índice de entrega bajo 0,4.
- **En la región, hasta 240 minutos, no se cierra en ningún caso.** Entrega mínima: 0,773 (`opioid_35m`),
  0,858 (`opioid_67f`), 0,978 y 0,981 (asma). Carga ácida, D y tono son idénticos bit a bit al control negativo.
- **La menor fracción que abre la compuerta** en 240 minutos es 0,1209 (el doble del borde de la región); en
  60 minutos, 0,80.
- En el borde superior la compuerta sí se abre en un curso de opioide sin tratar, pero no antes del **minuto
  346** (391 en `opioid_67f`; nunca en asma hasta 600), y entonces el lazo es monótono: sin oscilación ni
  parpadeo de umbral.
- **Signo cuando está activo** (sondas fijas fuera de la región, f = 1 y 0,5): `MIXED`. La rama ventilatoria
  es realimentación **negativa** —su multiplicador de un paso está entre 0,82 y 0,91, así que ni alterna ni
  diverge—; la rama de tono es **positiva** y acotada, con ganancia de un paso entre 0,07 y 0,12.
- Barrido de la región (f = 0, los tres testigos y 0,060621; cuatro casos; 60, 120 y 240 minutos): sin
  oscilación, sin inversión de signo, sin paso alternante, sin deuda, y el efecto de aumentar la transmisión es
  monótono.

**Veredicto: `A · INDIRECT_FEEDBACK_SAFE_FOR_DEVELOPMENT_REGION`.** Sin restricción adicional de región.
Límite declarado: pasado ese punto un curso sin tratar sigue empeorando sin cota porque estos perfiles no
declaran transición terminal; eso es el escritor de la familia y la capa de colapso sin declarar, no el lazo.

## 4 · Llegada en vivo del opioide (P3-139)

**Veredicto: `OPIOID_LIVE_ARRIVAL_MAPPING_REUSES_EXISTING_SEMANTICS`**, con una condición que se comprueba en
cada encuentro: la llegada en vivo tiene que **ser** el caso redactado, intacto. `OpioidAdapter.arrival_identity`
pregunta tres cosas y exige las tres: **el caso** (cada valor redactado que lee el mapeo certificado de P2U-1
es el mismo en el caso del estado vivo que en el del banco), **la llegada tal como se muestra** (el monitor
enseña esos valores) y **nada todavía** (reloj en 0, ninguna medicación dada, y el estado del motor para este
paciente igual, campo por campo, a una inicialización nueva del mismo caso). Una sola diferencia rechaza el
run, a la vista. Es una comparación: no deriva ningún valor del estado vivo con una regla nueva.

Por qué el opioide sí y ACS no: el motor redacta **dos** variantes de opioide y el adaptador certifica esas
dos; redacta **seis** de ACS y el adaptador certifica una.

| Entrada | Fuente |
|---|---|
| PA, FC, SpO2, FR, llenado capilar, ritmo, consciencia, glucosa, lactato, Hb, FiO2 | `DIRECT_FROM_LIVE_STATE` (iguales al caso redactado, comprobado) |
| K, bicarbonato y PaCO2 de llegada; V, P, T, L, G, D neutros | `FIXED_AUTHORED_CASE_ANCHOR` |
| FR intrínseca, disponibilidad central y eficiencia mecánica de llegada, exceso de lactato, frecuencia sinusal intrínseca | `CERTIFIED_EXISTING_MAPPING` (P2U-1) |
| acción de oxígeno, acción y minuto de naloxona, esperar y demorar | `DIRECT_FROM_LIVE_STATE` |

Entradas de runtime requeridas que falten o sean sólo sintéticas: **ninguna**. Lo que sí es sintético o no se
lee, declarado:

- parámetros del modelo, no entradas del runtime: tasa de profundización 0,005/min y tasa de recuperación de
  la naloxona 0,10/min (puntos `SYNTHETIC_ONLY`, sin región), R = 0,8 declarado y la fracción como región;
- bandas leídas en su punto comprometido: FR intrínseca 16 (de 12/16/20), exceso de lactato y frecuencia
  sinusal intrínseca en el punto medio; no se exploran en vivo;
- la **dosis y la vía** de la naloxona no se leen: el contribuidor certificado tiene una sola tasa;
- sin contribuidor: infusión de naloxona, bolsa-mascarilla, VNI, intubación, más opioide y una dosis repetida;
- sin representar: la recurrencia de `opioid_67f`, la abstinencia por exceso y cualquier transición terminal.

## 5 · Conjunto por región y cableado (P3-140, P3-141)

`LIVE_FAMILIES = ("gi_bleed", "opioid")`. La tupla la lee sólo la función que decide si se abre una sesión de
sombra; la autoridad tiene su propia compuerta, que nombra otra familia y sigue cerrada.

- **Run de la sesión:** el perfil comprometido del opioide, donde el enlace no está declarado. Es, estado por
  estado, el run de fracción 0: el **control negativo**, no un testigo.
- **Conjunto:** `RegionEnsemble`, tres runs —LOW, CENTER_REFERENCE, HIGH— sobre la misma llegada, las mismas
  acciones, el mismo reloj y la misma primitiva de ejecución. Dos testigos difieren en **un** campo del perfil
  y en nada más (también en el artefacto serializado).
- **Salida:** cada testigo entero, con su propio artefacto de replay. La única lectura derivada es una vista de
  mínimo y máximo por minuto junto a los tres valores, y sólo donde están los tres. Ni media, ni mediana, ni
  valor representativo; `selected_witness` es `None`.
- **Falla cerrada en el linaje:** ningún testigo se abre si el núcleo vivo no es un miembro certificado.

Mapeo de acciones reales: oxígeno y retirada de oxígeno → contribuidor certificado con el FiO2 que fijó el
motor; naloxona → la reversión certificada; reevaluación → sin fisiología, nunca un hueco; todo lo demás →
hueco declarado con su razón. Nada se descarta en silencio.

**Defectos encontrados por la auditoría en vivo y corregidos:**

1. **La naloxona reescribía historia.** El adaptador la mapeaba al propio minuto del motor: una orden puesta en
   el minuto m cambiaba el estado del minuto m, que la sombra en vivo ya había registrado, y una orden tardía
   hacía que el run y su replay discreparan. Ahora empieza en m + 1, donde ya caía el oxígeno. Mueve un minuto
   las cifras de naloxona del ciclo anterior (fuera de línea); ningún veredicto cambia.
2. **Una segunda dosis tumbaba el run** (dos contribuidores con la misma fuente). Una reversión empieza una
   vez; la dosis repetida es un hueco declarado.
3. **Una llegada rechazada dejaba el registro vacío sin decir por qué.** El motivo va ahora al registro de la
   sesión (también para GI).
4. **Toda diferencia con el motor se etiquetaba «divergencia estructural inesperada»** en una familia sin
   golden. Ahora es `NOT_COMPARABLE` con su razón; las dos lecturas de seguridad siguen sonando.
5. Un artefacto que no era de GI nombraba la versión del adaptador de GI.

**Guarda nueva:** un run cuyos contribuidores cambiarían un minuto ya registrado se detiene y lo dice
(`HistoryRewritten`).

**Política de fallos.** El encuentro nunca ve un fallo de la sombra: el turno del motor se confirma antes, y la
sombra lee copias. Una llegada rechazada no corre y deja su motivo. Un testigo que no puede correr registra por
qué y se queda en su último minuto verdadero; los otros siguen; **nada lo sustituye**. Cada run se reproduce
desde su propio artefacto hasta su último minuto registrado. Hoy el fallo se ve en el registro de la sesión y
en la traza de investigación; ninguna pantalla lo muestra.

## 6 · Serie de manejo en vivo (P3-142)

`opioid_35m`, jugado por el camino de órdenes de la página (`pilot_acceptance.Encounter`), tres testigos. El
motor heredado detiene al paciente sin revertir en el minuto 20: ese es el reloj real, y la sombra llega hasta
donde llega el encuentro.

| Vía | Acciones (minuto del motor) | Lo que la sombra muestra, en cada testigo |
|---|---|---|
| Sin tratar | — | disponibilidad ↓, FR ↓, W ↓, PaCO2 ↑, SpO2 ↓, monótonos |
| Oxígeno | oxígeno (0) | SpO2 ↑; disponibilidad, FR, W y PaCO2 idénticos; en el estado sólo el FiO2, desde el minuto 1 |
| Naloxona | naloxona (0) | el único canal de estado es la disponibilidad central, desde el minuto 1; FR ↑, W ↑, PaCO2 ↓, SpO2 ↑ |
| Ambos | oxígeno y naloxona (0) | la rama ventilatoria de la naloxona, bit a bit; el FiO2 del oxígeno; SpO2 por encima de las dos |
| Naloxona tardía | naloxona (10) | los diez primeros minutos son, estado por estado, los del brazo sin tratar; efecto desde el 11; pierde en la integral |
| Esperar | cuatro reevaluaciones | idéntico, estado por estado, a sin tratar; ningún hueco |

Minuto 20, testigo central: FR 5,43 sin tratar y 14,23 con naloxona; PaCO2 76,3 y 29,1; SpO2 79,7 · 99,2
(oxígeno) · 81,5 (naloxona) · 99,2 (ambos). La ganancia de saturación de la reversión crece con el testigo y
es **nula** en el control negativo: no hay escritura directa naloxona → SpO2. Una orden ejecutada en el minuto
m aparece en el estado m + 1, en todas las vías y en los cuatro runs.

## 7 · Equivalencia y replay (P3-143)

- **Vivo = fuera de línea**, estado por estado, en las seis vías y los cuatro runs: mismo calendario de
  acciones por el runner fuera de línea (sin sesión, sin motor, con identificadores propios, de un golpe) →
  mismos contribuidores, mismos huecos, mismos digestos, mismas lecturas, mismo orden.
- El testigo en vivo es exactamente el perfil que el ciclo anterior usó fuera de línea.
- **Replay exacto** de cada run desde su propio artefacto, también pasado por JSON.
- **Determinismo:** el mismo encuentro jugado dos veces da el mismo artefacto, byte a byte.
- El almacén de artefactos existente guarda experimentos de autoridad y nada más: **no** acepta una traza de
  sombra, y no se amplió. La traza en vivo no se persiste.

## 8 · Certificación de seguridad (P3-144)

GI en vivo intacto (mismas claves de registro, sin conjunto, vivo = replay) · ninguna otra familia abre sesión
· el registro autoritativo, el libro de órdenes y el destino de cada orden son idénticos con la sombra
encendida y apagada en las seis vías · la compuerta de autoridad sigue cerrada para el opioide · sin la
bandera, un encuentro de opioide es exactamente el motor · una familia nunca corre por el mapeo de otra · todo
artefacto nombra su adaptador y el núcleo certificado.

Veinte mutantes externos (naloxona al minuto del motor, conjunto de un solo testigo, run de la sesión igual al
central, identidad sin comprobar, identidad que sólo lee la línea base guardada, linaje ignorado, ACS en vivo,
guarda de historia apagada, dosis repetida construida dos veces, vista con media, sin golden leído como
inesperado, golden de GI perdido en silencio, testigo que mueve otra ganancia, oxígeno descartado, llegada
rechazada en silencio, lecturas fuera del replay, etiqueta de instantánea equivocada, reloj atrasado tras una
comparación fallida, enlace que escribe la mecánica, compuerta del lazo bajada) hacen fallar las pruebas nuevas.

### Revisión adversarial independiente (antes del commit)

De sólo lectura, sobre el candidato: 1 000 encuentros de opioide y 500 de GI con órdenes aleatorias, 44
escenarios de GI contra los módulos anteriores e inyección de fallos.

**Se sostuvo:** el estado autoritativo, el libro de órdenes y las entradas son idénticos con la sombra encendida
y apagada en todos los encuentros, y nada llegó a levantar dentro de uno; GI conserva las mismas claves,
minutos, clases, huecos y digestos; vivo = replay en el run de la sesión y en cada testigo; ningún testigo se
prefiere, se promedia ni viaja en el adaptador registrado; el primer minuto que cambia es siempre el de la
orden + 1.

**Encontró y se corrigió, cada cosa con su prueba:**

| | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| R1 | MEDIA | la identidad de llegada leía la línea base guardada por el motor y no el monitor ni el estado de tratamiento: tras un turno de **cero minutos** la página reabre la sesión en el minuto 0, y un paciente ya tratado pasaba por «la llegada», con la acción y su hueco perdidos en la sesión descartada | la identidad pregunta las tres cosas de §4; esa sesión se rechaza con su motivo |
| R2 | BAJA | una familia que **debe** tener golden y lo pierde se habría quedado en silencio | sólo una familia declarada sin golden es `NOT_COMPARABLE`; GI conserva la clase que suena |
| R3 | BAJA | una comparación que levantaba dejaba minutos registrados y el reloj atrás; la guarda de historia rechazaba después un run que nadie había reescrito (sólo por inyección de fallos) | minutos y reloj avanzan juntos; la comparación fallida se registra y el minuto queda, sin comparar |
| R4 | BAJA | el registro del opioide nombraba el perfil por omisión de la Fase 2 como su instantánea | un registro ajeno a GI nombra su propia instantánea comprometida |
| R6 | BAJA | con oxígeno los cuatro runs llegan a los mismos estados: comprobar el replay sólo por estados no distinguía un testigo de otro | cada minuto registrado y rejugado lleva también el digesto de sus lecturas |
| R7 | BAJA | el registro de la sesión levantaba si el mapeo del run de la sesión fallaba de plano | el registro lleva el fallo |

**Encontró y queda declarado** (TD-133): la compuerta de linaje está en el conjunto en vivo, no en un adaptador
testigo abierto a mano fuera de línea (R5); el ciclo de vida que reabre la sesión tras un primer turno de cero
minutos es anterior a este ciclo y lo comparte GI, que sí mapea esa sesión (R8); dos cambios de oxígeno dentro
de un mismo minuto del motor detendrían todos los runs, y ninguna orden real produce un turno de oxígeno de
cero minutos (R9); con la bandera puesta un turno de opioide cuesta unos 100 ms en el minuto 99, frente a 2 ms
con ella apagada (R10).

Incidencia de proceso: cuatro búsquedas recursivas de la revisión recorrieron también `validation/`, con la
salida filtrada; no se mostró ni se leyó nada de ahí.

## 9 · Compuertas de preparación (P3-145) y punto de control (P3-146)

| Compuerta | Estado | Lo que falta |
|---|---|---|
| Exposición en tiempo de ejecución | `BLOCKED` | no hay instantánea aprobada; la autoridad es, por diseño, sólo presión de GI |
| Exposición en la interfaz | `BLOCKED` | ninguna pantalla muestra una lectura del núcleo común |
| Captura de traza | `PARTIAL` | la traza en vivo no se persiste |
| Aislamiento de la puntuación | `GREEN` | — |
| Flujo de revisión docente | `PARTIAL` | no hay revisión en la app de una traza ni de una región |
| Selección de casos | `NOT_YET_EVALUATED` | una selección docente, tras revisión |
| Visibilidad de fallos | `PARTIAL` | nada muestra un fallo a un operador |
| Vuelta atrás | `GREEN` | — |
| Seguridad frente al residente | `BLOCKED` | sin transición terminal ni mapeo de consciencia; regiones de desarrollo |

Dos preguntas, sin mezclar:

- **Preparación del motor de simulación:** segunda familia en sombra en vivo validada para desarrollo.
- **Preparación de despliegue con residentes:** **no** lista para una revisión de piloto (2 verdes, 3
  parciales, 3 bloqueadas, 1 sin evaluar).

**Candidata futura para un piloto posterior y no congelado (sólo diseño; el primer piloto ni se elige ni se
toca):** GI > opioide > edema pulmonar > ACS. GI es la más fuerte (golden, mapeo desde el estado, diseño de
autoridad); el opioide es la del contraste docente más nítido —saturación frente a ventilación— y ya corre en
sombra en vivo, con dos tasas sintéticas, una región y sin dosis.

**Veredicto del motor: `A · SECOND_FAMILY_LIVE_SHADOW_VALIDATED`.**
**Veredicto de piloto: `NOT_READY_FOR_RESIDENT_PILOT_REVIEW`.**

**Paquete siguiente más corto:** persistir la traza de sombra en vivo en el almacén docente y de investigación
y mostrarla en una pantalla sólo docente. Cierra captura de traza y visibilidad de fallos, no necesita
fisiología ni autoridad, y es lo que leería una revisión docente de las regiones.
