# Fase 3 · P3-16 · Pack de decisión de la instantánea de parámetros para una autoridad de presiones en GI

Sólo lectura. **No aprueba ninguna magnitud, no elige candidato y no concede autoridad.** Prepara la
decisión docente exacta que haría falta antes de que una primera autoridad limitada pudiera correr: un
**punto** nombrado, porque un paciente sigue una sola trayectoria y una autoridad no puede mostrar una
envolvente como vital.

Rama `phase-3-runtime-integration`, sobre la cabeza de cierre de la Fase 2 `d2cca46`, digesto
`22b90a6f7f38…` intacto. Dominio futuro, por decisión docente del 2026-11-07: **SBP, DBP y MAP**, sólo GI,
entorno docente o de desarrollo, con el primer piloto excluido. CRT queda fuera del primer dominio.

## 1 · De ocho parámetros a dos que importan

P3-12 listó ocho magnitudes candidatas. Con CRT fuera del dominio, la pregunta es cuáles hacen falta de
verdad para las presiones. Medido, no supuesto:

| Magnitud | ¿Mueve SBP/DBP/MAP en GI? | Lectura |
|---|---|---|
| `preload_curve_scale_ml` | **sí, mucho** | no tratado m60: SBP 65,9–79,8 · tratado (A) m60: SBP 114,8–140,6 |
| `arrival_preload_fraction` | **sí, mucho** | no tratado m60: SBP 52,1–81,4 · tratado (A) m60: SBP 106,1–186,7 |
| `pump_preload_coupling` | no, en estos cursos | idéntico en los dos bordes de su región |
| `afterload_sensitivity` | no, en estos cursos | idéntico |
| `low_output_pressure_knee` | no, en estos cursos | idéntico |
| `sbp_per_pressure_deficit` | no, en estos cursos | idéntico |
| `dbp_per_pressure_deficit` | no, en estos cursos | idéntico |
| `crt_per_output_deficit_s` | **no, por estructura** | mover su región deja SBP, DBP y MAP **bit a bit iguales** 60 minutos, y sí mueve CRT |

Por qué las cinco inertes lo son: los cursos de la batería GI mantienen la presión **por encima de la
rodilla**, así que el déficit que las dos ganancias traducen a mmHg vale cero y la rodilla no se cruza; y
GI no ejercita el tono ni la bomba (no hay escritor de vasopresor y la bomba está intacta). «Inerte en
estos cursos» **no** es «irrelevante»: la rodilla y las ganancias sí entran en un curso que cae por debajo
de ella —el no tratado llega ahí hacia el minuto 103— y el tono entraría en una familia que lo mueva.

**Consecuencia para la decisión:** la instantánea de autoridad necesita **siete** valores nombrados (CRT
sale, probado arriba), pero sólo **dos** cambian lo que un residente vería en los escenarios de esta
batería. Los otros cinco hay que nombrarlos igual —una autoridad corre un punto, no un hueco— y su
elección es indiferente para estos cursos y decisiva para un curso que cruce la rodilla.

## 2 · De dónde viene la región de cada uno

Todas son `CANDIDATE` en el registro de calibración congelado de la Fase 2
(`clinical_core.calibration.REGISTRY`), **0 de 58 aprobadas por docencia**, y ninguna cota se derivó del
motor heredado.

| Magnitud | Región | Unidad | Restricciones | Dónde cae el punto comprometido | Razón registrada |
|---|---|---|---|---|---|
| `preload_curve_scale_ml` | 600 – 1500 | mL-eq | PL1–PL4 | midpoint (833,3) | escala de la curva saturante de precarga; con κ (P2I-2T) sólo importa la razón escala/volumen |
| `arrival_preload_fraction` | 0,3 – 0,7 | posición (0–1) | PL1–PL3 | midpoint (0,5) | posición de llegada por omisión |
| `pump_preload_coupling` | 0,0 – 1,0 | exponente c | PL2, PL3 | **borde superior (1,0)** | cuánto encoge la curva una bomba deprimida |
| `afterload_sensitivity` | 0,1 – 0,5 | por unidad de tono | PL1 | midpoint (0,3) | el tono sobre el de llegada baja el gasto |
| `low_output_pressure_knee` | 0,3 – 0,6 | presión relativa | PR1–PR3 | midpoint (0,5) | por debajo, la presión es proporcional a flujo × tono |
| `sbp_per_pressure_deficit` | 35 – 55 | mmHg por unidad de déficit | PR1, PR3 | midpoint (45) | **literal del motor heredado, adoptado en P2C** |
| `dbp_per_pressure_deficit` | 15 – 30 | mmHg por unidad de déficit | PR1, PR3 | midpoint (25) | **literal del motor heredado, adoptado en P2C** |

Dos cosas que la docencia debe ver tal cual: el punto comprometido es el **midpoint** del registro en seis
de las siete y el **borde superior** en `pump_preload_coupling`; y las dos ganancias de presión fueron
**adoptadas del literal del motor heredado** en P2C. Lo segundo no es ajustar contra el legado ahora —fue
una adopción declarada de la Fase 2—, pero sí hay que decirlo al aprobar un punto.

Identificabilidad, medida en esta batería: `preload_curve_scale_ml` y `arrival_preload_fraction` son
identificables (mueven la presión en los dos cursos); las otras cinco **no lo son** con los cursos de GI,
así que ninguna evidencia de esta batería puede justificar un valor dentro de su región. Aprobar un punto
para ellas es una decisión clínica sin evidencia de GI que la respalde, y conviene registrarlo así.

## 3 · Los candidatos

Sólo con evidencia de la Fase 2, sin optimizar contra el legado, y cada uno un punto real dentro de todas
las regiones. La variación va por el único eje identificable —el bloque de precarga, sus dos magnitudes al
mismo borde nombrado—, con las otras cinco en su valor comprometido: es una **diagonal de dos**, no un
producto, y son tres candidatos.

| Candidato | `preload_curve_scale_ml` | `arrival_preload_fraction` | Resto |
|---|---|---|---|
| `gi_pressure_preload_low` | 600 | 0,3 | comprometido |
| `gi_pressure_committed` | 833,3 | 0,5 | comprometido |
| `gi_pressure_preload_high` | 1500 | 0,7 | comprometido |

**La esquina de siete parámetros queda descartada como candidata de autoridad**, y conviene decir por qué:
con las siete magnitudes en su borde superior el tratado llega a SBP 210 / MAP 156 mmHg en un sangrado
reanimado. Es un punto dentro de todas las regiones declaradas y, aun así, no es un punto fisiológicamente
sostenible: exactamente el caso que P3-16-3 prohíbe presentar como candidato.

## 4 · Admisibilidad y seguridad cruzada

| Candidato | GI, curso no tratado a 240 min | Batería GI (34 escenarios) | Otras cinco familias (8 casos certificados) |
|---|---|---|---|
| `gi_pressure_preload_low` | **`UnresolvedBoundary` en el minuto 103**: el gasto efectivo llega a cero con pulso presente y ninguna transición terminal declarada se aplica (la regla de colapso está apagada) | la misma frontera en los dos escenarios terminales | sin fallos |
| `gi_pressure_committed` | corre limpio: SBP 80,2 → 72,6 → 57,9 → 28,5 (30/60/120/240 min) | limpio en los 34 | sin fallos |
| `gi_pressure_preload_high` | corre limpio, pero el paciente **no se deteriora**: SBP 86,2 → 84,5 → 81,3 → 75,5 a 240 min sin tratamiento | limpio en los 34 | sin fallos |

**`gi_pressure_preload_low` queda rechazado** por la regla de P3-16-3 y P3-16-4: alcanza una frontera que
la Fase 2 deja sin resolver. No lo rechazo por ser «peor contra el legado»; lo rechaza el propio núcleo.

De `gi_pressure_preload_high` no digo que sea inadmisible: digo lo que hace. Un sangrado no tratado que a
las cuatro horas sigue con SBP 75 contradice el curso que la propia familia GI enseña, y eso es una lectura
clínica, no un número mío.

## 5 · Qué hace cada candidato en la batería de GI (descriptivo)

Los tres candidatos, corridos sobre los **artefactos de replay** de los 34 escenarios —la misma entrada
inmutable, sólo cambia el perfil—, en el último minuto comparado de cada uno:

| Escenario (57m) | `preload_low` | comprometido | `preload_high` | legado (comparador) |
|---|---|---|---|---|
| `A_correct_management` | SBP 210,7 / MAP 156,4 | SBP 130,3 / MAP 96,7 | SBP 99,5 / MAP 73,9 | SBP 117 / MAP 86 |
| `B_delayed_management` | SBP 160,0 / MAP 118,8 | SBP 111,5 / MAP 82,8 | SBP 94,0 / MAP 69,8 | SBP 102 / MAP 75 |
| `C_omission` | SBP 36,5 / MAP 27,1 | SBP 72,6 / MAP 53,9 | SBP 84,5 / MAP 62,7 | SBP 80 / MAP 60 |

El sentido se invierte entre tratado y no tratado, y vale entenderlo antes de decidir: una curva más
pequeña (`preload_low`) deja el mismo volumen más arriba de la saturación cuando se reanima —presiones
altas— y deja menos reserva cuando no se reanima —presiones bajas hasta la frontera—.

Como descripción y **no** como criterio: el valor del legado cae dentro del tramo de los tres candidatos en
**30 de los 32** minutos finales comparables. No ordeno los candidatos por cercanía al legado: el legado es
comparador, no verdad clínica de referencia, y ajustar contra él está prohibido.

## 6 · Tabla de decisión docente

| | `gi_pressure_preload_low` | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|---|
| **Valores** | escala 600 · llegada 0,3 | escala 833,3 · llegada 0,5 | escala 1500 · llegada 0,7 |
| **Procedencia Fase 2** | bordes inferiores del registro congelado (PL1–PL4, PL1–PL3) | punto adoptado; midpoint del registro en 6 de 7 magnitudes | bordes superiores del mismo registro |
| **Ventajas** | representa el extremo pesimista de la reserva | corre limpio en todo lo probado y conserva la semántica del curso | representa el extremo optimista; corre limpio |
| **Riesgos** | **alcanza una frontera no resuelta** (minuto 103) y da presiones muy altas al reanimar | es el punto que la sombra ya midió, así que no añade información nueva sobre la región | un sangrado no tratado que no se deteriora en 4 h |
| **Batería GI** | frontera en 2 escenarios; el resto corre | limpio en 34 | limpio en 34 |
| **Cruzado (5 familias, 8 casos)** | sin fallos | sin fallos | sin fallos |
| **Incertidumbre representada / perdida** | representa el borde bajo; pierde todo lo demás | representa el centro declarado; pierde los dos extremos | representa el borde alto; pierde el resto |

**No elijo.** Las tres columnas están para que la docencia elija una, o pida otra construida con la misma
regla.

## 7 · Lo que esta decisión no resuelve

- Las cinco magnitudes inertes siguen necesitando un valor nombrado y **no hay evidencia de GI que lo
  respalde**; si la primera autoridad se limita a cursos que no cruzan la rodilla, da igual cuál se nombre,
  y eso también es una decisión que conviene escribir.
- El criterio de aceptación sigue siendo estructural: no se inventó ninguna tolerancia numérica.
- Las cuatro diferencias parcialmente declaradas de P3-11 (`hr`, `crt_s`, `V_ml_eq`, `consciousness_level`)
  quedan fuera del dominio de presiones y siguen siendo diagnóstico en sombra.
- Nada de esto concede autoridad: `APPROVED_SNAPSHOTS` sigue vacío y la puerta de nueve condiciones sigue
  refutando.

## Veredicto

**`GI_AUTHORITY_SNAPSHOT_DECISION_READY`** — la decisión está preparada: siete magnitudes a nombrar, dos
de ellas identificables con evidencia de GI, tres candidatos con su procedencia y su conducta medida, uno
de ellos rechazado por el propio núcleo, y la cuenta explícita de lo que cada candidato representa y pierde.
