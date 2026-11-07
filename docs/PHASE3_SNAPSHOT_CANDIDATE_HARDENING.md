# Fase 3 · P3-21 · Endurecimiento de los candidatos de instantánea y seguridad cruzada

Sólo lectura. **No aprueba ninguna magnitud, no elige candidato y no concede autoridad.** Prepara la mejor
decisión docente posible sin tomarla: reduce el conjunto de parámetros al mínimo que la presión necesita,
descarta lo que el propio núcleo refuta, y mide qué pasa alrededor de cada candidato.

Todo lo de abajo está **medido** sobre la misma entrada inmutable de un encuentro GI real (`gi_bleed_57m`),
cambiando sólo el perfil: un curso tratado (1 L de salino en 15 min) y un curso no tratado, ambos a 240
minutos, más los 10 casos certificados de las seis familias. Las regiones son las del registro de
calibración congelado de la Fase 2 (`clinical_core.calibration.REGISTRY`), 0 de 58 aprobadas por docencia.

## 1 · El conjunto mínimo de parámetros (P3-21A)

Movimos cada magnitud candidata a los dos bordes de su propia región, con el resto en el punto
comprometido, y comparamos SBP, DBP y MAP en los minutos 30, 60, 120 y 240 de los dos cursos:

| Magnitud | Región | ¿Mueve la presión? | ¿Mueve CRT? |
|---|---|---|---|
| `preload_curve_scale_ml` | 600 – 1500 | **sí** | sí |
| `arrival_preload_fraction` | 0,3 – 0,7 | **sí** | sí |
| `pump_preload_coupling` | 0,0 – 1,0 | no | no |
| `afterload_sensitivity` | 0,1 – 0,5 | no | no |
| `low_output_pressure_knee` | 0,3 – 0,6 | no | no |
| `sbp_per_pressure_deficit` | 35 – 55 | no | no |
| `dbp_per_pressure_deficit` | 15 – 30 | no | no |
| `crt_per_output_deficit_s` | 3,0 – 5,0 | **no** | **sí** |

**El parámetro de CRT queda fuera por causalidad, no por conveniencia:** moverlo de un borde a otro de su
región deja SBP, DBP y MAP idénticos en los dos cursos y sí cambia CRT. Es exactamente la prueba que P3-21A
pide antes de excluirlo.

Las cinco inertes siguen necesitando un valor nombrado —una autoridad corre un punto, no un hueco— y su
elección es indiferente **en estos cursos**: la rodilla y las dos ganancias entran en un curso que cae por
debajo de ella, y el tono entra en una familia que lo mueva. Eso no es evidencia de GI y conviene escribirlo
así al aprobar un punto.

## 2 · Los candidatos que sobreviven (P3-21B)

| | `gi_pressure_committed` | `gi_pressure_preload_high` | `gi_pressure_preload_low` |
|---|---|---|---|
| `preload_curve_scale_ml` | 833,33 | 1500 | 600 |
| `arrival_preload_fraction` | 0,5 | 0,7 | 0,3 |
| Procedencia Fase 2 | punto comprometido; midpoint del registro en 6 de 7 magnitudes | borde **superior** de las dos regiones | borde **inferior** de las dos regiones |
| Posición en la región | **interior** en las dos | frontera en las dos | frontera en las dos |
| Identificabilidad | las dos magnitudes son identificables con los cursos de GI; las otras cinco no lo son con esta evidencia | igual | igual |
| Curso tratado a 240 min | SBP 89 → 80 → 65 → 37 | SBP 88 → 86 → 83 → 77 | **`UnresolvedBoundary` en el minuto 131** |
| Curso no tratado a 240 min | SBP 80 → 73 → 58 → 29 | SBP 86 → 84 → 81 → **75** | **`UnresolvedBoundary` en el minuto 103** |
| Batería GI (34 escenarios) | ver P3-22 | ver P3-22 | ver P3-22 |
| Cruzado: 10 casos certificados, 6 familias | sin fallos | sin fallos | sin fallos |
| Depende de magnitudes débilmente identificadas | las cinco inertes, en cursos que cruzan la rodilla | igual | igual |

## 3 · Dominancia (P3-21C)

`gi_pressure_preload_low` **queda retirado de la elección docente**, y la razón no es clínica:

- alcanza una frontera que la Fase 2 deja sin resolver en **los dos** cursos (minutos 103 y 131), no sólo en
  el no tratado como se vio en P3-16;
- está en el borde inferior de las dos regiones, es decir no tiene interior alrededor;
- **todo su vecindario muestreado también alcanza la frontera** (minutos 150 y 152, §4), así que no es un
  punto desafortunado sino una zona que el núcleo no resuelve;
- no aporta ninguna ventaja estructural sobre los otros dos: no corre limpio donde ellos corren limpio.

Esto no es selección clínica: es el propio núcleo negándose a resolver esas corridas. Los otros dos candidatos
quedan en pie, y la elección entre ellos **sigue siendo docente**.

## 4 · Sensibilidad dispersa dentro de la región (P3-21D)

Perturbamos cada magnitud identificable ±10 % del ancho de su región, manteniéndonos dentro, sin rejilla
densa y sin optimizar:

| Candidato | Perturbación | Frontera | Tratado SBP m60 | No tratado SBP m240 | ¿El curso sigue cayendo? |
|---|---|---|---|---|---|
| `gi_pressure_committed` | escala +10 % | no | 80,5 | 35,8 | sí |
| | escala −10 % | no | 78,6 | 19,0 | sí |
| | llegada +10 % | no | 80,9 | 37,3 | sí |
| | llegada −10 % | no | 78,2 | 18,2 | sí |
| `gi_pressure_preload_high` | escala −10 % | no | 85,9 | 74,5 | sí |
| | llegada −10 % | no | 85,7 | 72,9 | sí |
| `gi_pressure_preload_low` | escala +10 % | **sí, minuto 150** | — | — | — |
| | llegada +10 % | **sí, minuto 152** | — | — | — |

Lectura estructural, sin tolerancia numérica: alrededor del punto comprometido el comportamiento es
**estable** —ninguna frontera, el curso no tratado sigue deteriorándose, la respuesta al fluido sigue siendo
positiva— con una dispersión amplia en la presión final (19–37 mmHg a las cuatro horas), que es incertidumbre
de parámetros y no error. Alrededor del borde superior también es estable, con el mismo rasgo que P3-16 ya
señaló: el sangrado no tratado apenas se deteriora. El borde inferior es inestable.

## 5 · Tabla final de decisión docente (P3-21E)

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| **Valores** | escala 833,33 · llegada 0,5 | escala 1500 · llegada 0,7 |
| **Procedencia** | punto adoptado de la Fase 2; midpoint del registro en 6 de 7 magnitudes | bordes superiores del mismo registro congelado |
| **Posición** | **`MOST_INTERIOR`**: estrictamente dentro de las dos regiones | en la frontera superior de las dos |
| **Robustez cruzada** | sin fallos en 10 casos de 6 familias | sin fallos en 10 casos de 6 familias — **empate: ningún candidato es más robusto, y no invento un ganador** |
| **Conservador en términos de parámetros** | **`MOST_CONSERVATIVE_IN_PARAMETER_TERMS`**: es el punto más lejano de cualquier borde | ninguno de sus dos valores tiene margen hacia arriba |
| **Estabilidad del vecindario** | estable en las 4 perturbaciones | estable en las 2 perturbaciones posibles hacia dentro |
| **Lo que cada uno representa** | el centro declarado; no añade información nueva sobre la región | el extremo optimista de la reserva |
| **Lo que cada uno pierde** | los dos extremos | todo lo que no sea el borde alto |
| **Rasgo clínico que la docencia debe leer** | el curso que la familia GI enseña: el sangrado se deteriora | un sangrado **no tratado** que a las 4 h sigue con SBP 75 |

**No elijo.** Las etiquetas `MOST_INTERIOR` y `MOST_CONSERVATIVE_IN_PARAMETER_TERMS` son geométricas, no
clínicas, y están puestas porque la evidencia las sostiene; `MOST_CROSS_FAMILY_ROBUST` **no se adjudica**,
porque los dos candidatos corren igual de limpio en el cruce. Ningún orden de preferencia sale de la cercanía
al motor heredado: el legado es comparador, no verdad de referencia, y ajustar contra él está prohibido.

## Veredicto

**`GI_AUTHORITY_SNAPSHOT_CANDIDATES_HARDENED`** — siete magnitudes a nombrar (CRT excluida con prueba
causal), dos identificables, un candidato retirado por dominancia estructural con su vecindario medido, dos
candidatos en pie con su procedencia, su posición en la región y su conducta, y la decisión entera todavía en
manos de la docencia.
