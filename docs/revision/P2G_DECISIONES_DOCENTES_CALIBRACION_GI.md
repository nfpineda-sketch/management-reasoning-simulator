# P2G · Paquete de decisiones docentes para calibrar el núcleo en sombra (GI)

Apoyo a decisiones, no decisiones. Nada de este documento aprueba un número, marca un parámetro como
FACULTY_APPROVED, migra el GI, toca el tiempo de ejecución ni cambia lo que ve el residente. Todos los valores
siguen CANDIDATE.

- **Generado desde:** el congelamiento de calibración `a7436fe8e8cb73b2a391035f28f7f98bea8049049b0cfa2f4938bcbc45137d39` y el paquete `61872b9dde96fd72b585e420cb5327bb7c056471ad952b3fe23ebb7fe234c158`
  (`python -m clinical_core.decision_pack`; las tablas, con `python -m clinical_core.decision_pack_markdown`).
  Los números están en `docs/revision/P2G_decision_pack.json`. Una prueba falla si el código o las entradas cambian
  sin regenerarlos.
- **Base:** la región estructuralmente admisible de P2F (`docs/PHASE2_SHADOW_CORE.md` §12.7): 1054 de los 1217
  conjuntos GI. Quedan fuera los 162 con τ_D 30 y D de llegada 60, y el de precarga 0,2 en 57m.
- **Cómo leer las tablas:**
  - **«mínimo – mediana – máximo»** recorre toda la región admisible.
  - **«bajo», «medio» y «alto»** son posiciones dentro de esa región para una lectura concreta. No son preferencias.
  - **Una fila de efecto** cambia un solo factor alrededor del conjunto con todas las bandas en su punto medio.
    Muestra dirección y tamaño, no interacciones.
  - **«Región admisible»** es el diseño GI de P2F menos sus 163 rechazos: 1054 conjuntos. Un conjunto fuera de ese
    diseño (por ejemplo, otra escala de la curva de precarga) puede ser *admisible* para las reglas congeladas sin
    pertenecer a la región. El diseño sólo varía las tres cinéticas (τ_D, G, τ_L) y combinaciones fijas de las bandas
    del caso, así que la mayoría de las filas de efecto quedan fuera: cada fila de efecto lo marca («fuera del diseño
    de P2F») y la tabla de volumen lo dice en su propia columna.
  - **El estado de cada fila:**
    - *admisible*: las reglas congeladas lo aceptan (no implica que P2F lo haya barrido);
    - *rechazado*: las reglas congeladas lo rechazan;
    - *no evaluado*: ninguna regla congelada lee ese parámetro;
    - *sonda de sensibilidad*: el parámetro no tiene banda candidata.
- **Toda la evidencia numérica es del modelo.** La evidencia del repositorio (lo que dicen los casos) va aparte, en la
  tabla maestra (§13). Las trayectorias del motor heredado no se usan como referencia.

## 1. Reproducibilidad (P2G-1)

El congelamiento de calibración cubre ahora todo lo que puede cambiar las entradas de los escenarios o la aceptación:
el camino del motor de familias, el adaptador de órdenes, el banco de casos, las entradas materializadas y los
archivos del arnés completos (`calibration.py`, `bands.py`). El digest del paquete suma a eso cada fuente del núcleo
en sombra (`clinical_core/**/*.py`), salvo el renderizador de este documento, que no cambia ningún número. El detalle
está en `docs/PHASE2_SHADOW_CORE.md` §13.1.

## 2. Decisión 1 · Lactato (P2G-2)

El lactato de llegada (4,4 mmol/L en 57m; 3,4 en 72f) se reparte en una basal de aclaramiento y un exceso
aclarable (banda candidata). Lo producido después depende de la D de llegada, de la razón de entrega y de la ganancia
D → lactato (G); lo que se aclara depende de τ_L.

- **Sin tratamiento, en el centro de la región el lactato no sube en una hora.** Baja algo: el exceso declarado se
  aclara más rápido de lo que el déficit en curso produce lactato nuevo.
  - A los 60 min, la mediana es 3,8 (57m) y 3,1 (72f).
  - El rango va de 1,8 a 9,6 en 57m y de 1,5 a 9,2 en 72f.
  - A los 60 min queda por encima del de llegada en el 25 % de la región (57m) y el 34 % (72f), y más de 1 mmol/L
    por encima en el 10 % y el 12 % (tabla «Proporción de la región admisible»).
  - El conjunto con la subida más alta (representante «alto») combina G 12, τ_L 45, D de llegada 60 y entrega 0,6.
    Por separado, lo que más sube el lactato a los 60 min es G y la D de llegada (filas de efecto).
  - El sangrado sin tratamiento es lento (2,5 mL/min; decisión 3), y eso también limita la producción.
- **Lo que más empuja hacia arriba** es la D de llegada y la ganancia G.
  - τ_L actúa en los dos sentidos: aclara antes el exceso, pero también deja ver antes la producción nueva.
  - Un exceso aclarable menor deja el lactato más alto, porque la basal a la que tiende es mayor.
- **Con manejo definitivo**, a los 30 min el lactato ya está por debajo del de llegada en el 79 % de la región (57m) y
  el 68 % (72f); a los 120 min, en el 91 % y el 84 %.
  - A los 120 min queda entre 1,0 y 6,0 (57m), con mediana 3,0.
  - Que vuelva a la basal (0,8–2,0, sin dato en el caso) depende sobre todo de τ_L y de la D de llegada.

<!-- generado:lactato -->
**gi_bleed_57m** — lactato (mmol/L), mínimo – mediana – máximo en la región admisible:

| Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| sin tratamiento | 4,40 – 4,40 – 4,40 | 2,64 – 4,04 – 8,35 | 1,79 – 3,80 – 9,58 | 1,37 – 3,91 – 10,42 |
| manejo definitivo (GR + IBP + endoscopia) | 4,40 – 4,40 – 4,40 | 2,63 – 4,00 – 8,12 | 1,73 – 3,65 – 8,24 | 1,04 – 3,00 – 6,00 |

Representantes (posición del lactato a los 60 min sin tratamiento; no son preferencias):

| Región | Conjunto | Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|---|
| bajo | τ_D 120 · τ_L 45 · G 2 · exceso sup. · intrínseca inf. · D inf. · entrega sup. | sin tratamiento | 4,40 | 2,64 | 1,79 | 1,37 |
| bajo | τ_D 120 · τ_L 45 · G 2 · exceso sup. · intrínseca inf. · D inf. · entrega sup. | manejo definitivo (GR + IBP + endoscopia) | 4,40 | 2,63 | 1,73 | 1,04 |
| medio | τ_D 60 · τ_L 120 · G 6 · resto medio | sin tratamiento | 4,40 | 4,05 | 3,80 | 3,78 |
| medio | τ_D 60 · τ_L 120 · G 6 · resto medio | manejo definitivo (GR + IBP + endoscopia) | 4,40 | 4,00 | 3,56 | 2,73 |
| alto | τ_D 60 · τ_L 45 · G 12 · exceso inf. · intrínseca sup. · D sup. · entrega inf. | sin tratamiento | 4,40 | 8,35 | 9,58 | 10,42 |
| alto | τ_D 60 · τ_L 45 · G 12 · exceso inf. · intrínseca sup. · D sup. · entrega inf. | manejo definitivo (GR + IBP + endoscopia) | 4,40 | 8,12 | 8,24 | 5,71 |

Proporción de la región admisible a cada lado de las preguntas docentes (sólo modelo):

| Lectura | Conjuntos | Proporción |
|---|---|---|
| sin tratamiento, 60′ por encima de la llegada | 1054 | 25 % |
| sin tratamiento, 60′ más de 1 mmol/L por encima | 1054 | 10 % |
| manejo definitivo, 30′ por debajo de la llegada | 1054 | 79 % |
| manejo definitivo, 120′ por debajo de la llegada | 1054 | 91 % |

Efecto de cada factor alrededor del punto medio:

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `arrival_oxygen_debt` | inf. | admisible · fuera del diseño de P2F | 3,71 | 3,32 | 3,31 | 3,66 | 3,07 | 2,26 |
| `arrival_oxygen_debt` | medio | admisible | 4,05 | 3,80 | 3,78 | 4,00 | 3,56 | 2,73 |
| `arrival_oxygen_debt` | sup. | admisible · fuera del diseño de P2F | 4,75 | 4,76 | 4,71 | 4,70 | 4,52 | 3,66 |
| `arrival_lactate_excess` | inf. | admisible | 4,28 | 4,19 | 4,41 | 4,23 | 3,95 | 3,36 |
| `arrival_lactate_excess` | medio | admisible | 4,05 | 3,80 | 3,78 | 4,00 | 3,56 | 2,73 |
| `arrival_lactate_excess` | sup. | admisible | 4,01 | 3,72 | 3,65 | 3,96 | 3,48 | 2,60 |
| `lactate_per_output_deficit` | 2 | admisible | 3,78 | 3,30 | 2,76 | 3,76 | 3,22 | 2,41 |
| `lactate_per_output_deficit` | 6 | admisible | 4,05 | 3,80 | 3,78 | 4,00 | 3,56 | 2,73 |
| `lactate_per_output_deficit` | 12 | admisible | 4,46 | 4,54 | 5,31 | 4,36 | 4,05 | 3,21 |
| `lactate_clearance_tau_min` | 45 | admisible | 3,63 | 3,28 | 3,70 | 3,51 | 2,75 | 1,77 |
| `lactate_clearance_tau_min` | 120 | admisible | 4,05 | 3,80 | 3,78 | 4,00 | 3,56 | 2,73 |
| `lactate_clearance_tau_min` | 240 | admisible | 4,22 | 4,06 | 3,99 | 4,19 | 3,93 | 3,39 |

**gi_bleed_72f** — lactato (mmol/L), mínimo – mediana – máximo en la región admisible:

| Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| sin tratamiento | 3,40 – 3,40 – 3,40 | 2,13 – 3,21 – 7,83 | 1,52 – 3,12 – 9,22 | 1,21 – 3,28 – 9,85 |
| manejo definitivo (GR + IBP + endoscopia) | 3,40 – 3,40 – 3,40 | 2,12 – 3,18 – 7,66 | 1,48 – 2,96 – 8,17 | 0,98 – 2,52 – 5,83 |

Representantes (posición del lactato a los 60 min sin tratamiento; no son preferencias):

| Región | Conjunto | Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|---|
| bajo | τ_D 120 · τ_L 45 · G 2 · exceso sup. · intrínseca inf. · D inf. · entrega sup. | sin tratamiento | 3,40 | 2,13 | 1,52 | 1,21 |
| bajo | τ_D 120 · τ_L 45 · G 2 · exceso sup. · intrínseca inf. · D inf. · entrega sup. | manejo definitivo (GR + IBP + endoscopia) | 3,40 | 2,12 | 1,48 | 0,98 |
| medio | τ_D 60 · τ_L 120 · G 6 · resto medio | sin tratamiento | 3,40 | 3,27 | 3,16 | 3,22 |
| medio | τ_D 60 · τ_L 120 · G 6 · resto medio | manejo definitivo (GR + IBP + endoscopia) | 3,40 | 3,23 | 2,96 | 2,37 |
| alto | τ_D 60 · τ_L 45 · G 12 · exceso inf. · intrínseca sup. · D sup. · entrega inf. | sin tratamiento | 3,40 | 7,83 | 9,22 | 9,85 |
| alto | τ_D 60 · τ_L 45 · G 12 · exceso inf. · intrínseca sup. · D sup. · entrega inf. | manejo definitivo (GR + IBP + endoscopia) | 3,40 | 7,66 | 8,17 | 5,83 |

Proporción de la región admisible a cada lado de las preguntas docentes (sólo modelo):

| Lectura | Conjuntos | Proporción |
|---|---|---|
| sin tratamiento, 60′ por encima de la llegada | 1054 | 34 % |
| sin tratamiento, 60′ más de 1 mmol/L por encima | 1054 | 12 % |
| manejo definitivo, 30′ por debajo de la llegada | 1054 | 68 % |
| manejo definitivo, 120′ por debajo de la llegada | 1054 | 84 % |

Efecto de cada factor alrededor del punto medio:

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `arrival_oxygen_debt` | inf. | admisible · fuera del diseño de P2F | 2,92 | 2,68 | 2,76 | 2,88 | 2,48 | 1,90 |
| `arrival_oxygen_debt` | medio | admisible | 3,27 | 3,16 | 3,22 | 3,23 | 2,96 | 2,37 |
| `arrival_oxygen_debt` | sup. | admisible · fuera del diseño de P2F | 3,97 | 4,12 | 4,16 | 3,93 | 3,92 | 3,30 |
| `arrival_lactate_excess` | inf. | admisible | 3,49 | 3,55 | 3,86 | 3,45 | 3,35 | 3,00 |
| `arrival_lactate_excess` | medio | admisible | 3,27 | 3,16 | 3,22 | 3,23 | 2,96 | 2,37 |
| `arrival_lactate_excess` | sup. | admisible | 3,23 | 3,08 | 3,10 | 3,19 | 2,88 | 2,24 |
| `lactate_per_output_deficit` | 2 | admisible | 3,00 | 2,69 | 2,33 | 2,99 | 2,62 | 2,04 |
| `lactate_per_output_deficit` | 6 | admisible | 3,27 | 3,16 | 3,22 | 3,23 | 2,96 | 2,37 |
| `lactate_per_output_deficit` | 12 | admisible | 3,67 | 3,87 | 4,57 | 3,59 | 3,46 | 2,86 |
| `lactate_clearance_tau_min` | 45 | admisible | 3,11 | 2,95 | 3,27 | 3,01 | 2,51 | 1,71 |
| `lactate_clearance_tau_min` | 120 | admisible | 3,27 | 3,16 | 3,22 | 3,23 | 2,96 | 2,37 |
| `lactate_clearance_tau_min` | 240 | admisible | 3,33 | 3,27 | 3,27 | 3,31 | 3,16 | 2,78 |
<!-- /generado:lactato -->

**Preguntas para la docencia**
1. ¿Cuánto debería subir, de forma plausible, el lactato tras una hora de hemorragia digestiva activa sin tratar?
2. Tras controlar el sangrado y reanimar con éxito, ¿con qué rapidez debería empezar a bajar un lactato elevado?
3. ¿Debe poder volver a la basal dentro del horizonte de la simulación, o seguir elevado por la deuda previa?

## 3. Decisión 2 · Frecuencia cardíaca (P2G-3)

**Descomposición.**
- FC = frecuencia intrínseca + 25 × (1 − β) × impulso simpático.
- β = 0: ningún caso declara betabloqueo (§8).
- En estas corridas no hay ninguna otra fuente cronotrópica, y la prueba lo comprueba: la parte «otra» es 0 en cada
  punto.

**Hallazgo sobre la frecuencia intrínseca.**
- La parte simpática de llegada es la FC de llegada menos la intrínseca. Por eso la intrínseca no cambia la
  trayectoria de la FC mientras el impulso siga por encima de cero: la parte de llegada lo compensa.
- Sólo fija el piso al que puede bajar en la recuperación. En 72f, con manejo definitivo, la FC queda en 100 con
  intrínseca 100 y baja a 95 con intrínseca 60.

**Trayectorias (mediana).**
- **Sin tratamiento**, la FC sube: 57m va de 124 a 134 a los 60 min y a 147 a los 120; 72f, de 112 a 119 y a 127.
- **Sólo cristaloides:** baja durante el bolo y vuelve a subir. A los 60 min supera la de llegada (126 en 57m)
  por tres motivos:
  - el cristaloide se redistribuye fuera de los vasos;
  - el sangrado sigue;
  - la dilución de la Hb baja la entrega de O2.
- **Sólo GR y manejo definitivo:** baja.
  - 57m: 104 a los 60 min y 103 a los 120 (rango 93–110).
  - 72f: 99 y 99 (rango 88–101).
  - A los 120 min queda unos 20 lpm sobre la intrínseca media, porque la presión no vuelve del todo y queda deuda.

**Rapidez de la resolución** (tabla «Velocidad de resolución», con manejo definitivo). Hay dos lecturas y sólo una
no depende de la intrínseca:
- **Mitad de la caída:** el minuto en que la FC recorre la mitad de su propia caída hasta los 120 min. Es igual para
  toda intrínseca mientras el impulso no llegue a cero: 28 (τ 2), 31 (τ 5) y 41 min (τ 15) en 57m; 29, 32 y 41 en
  72f. Con intrínseca 100, en 72f la FC se detiene en 100 (el impulso llega a ~0), la caída es más corta y su mitad
  llega antes (21–33 min).
- **Mitad simpática:** el minuto en que la parte simpática cae a la mitad de la de llegada. Depende de la intrínseca,
  porque ésta fija cuánto de la FC de llegada es simpático: con intrínseca 60 no ocurre en 120 min; con la media,
  59–82 min (57m) y 65–95 (72f); con 100, 29–42 (57m) y 21–33 (72f).
- La constante de decaimiento (2–15 min) mueve la mitad de la caída 12–13 min.
- El factor más fuerte es la ganancia por déficit de presión: en 57m a los 120 min con manejo definitivo, 81 lpm con
  ganancia 2 y 110 con ganancia 0,5.

<!-- generado:fc -->
**gi_bleed_57m** — FC de llegada 124 lpm = intrínseca 60–100 (medio 80) + parte simpática 24–64 (medio 44); betabloqueo 0 (factor 1 − β = 1); ninguna otra fuente cronotrópica en estas corridas.

| Corrida | Intrínseca | 30′ (FC = intr. + simp.) | 60′ | 120′ | Región admisible (mín – mediana – máx) |
|---|---|---|---|---|---|
| manejo definitivo (GR + IBP + endoscopia) | intrínseca inf. | 112,6 = 60 + 52,6 | 102,4 = 60 + 42,4 | 100,5 = 60 + 40,5 |  |
| manejo definitivo (GR + IBP + endoscopia) | intrínseca sup. | 112,6 = 100 + 12,6 | 102,4 = 100 + 2,4 | 100,5 = 100 + 0,5 |  |
| manejo definitivo (GR + IBP + endoscopia) | medio | 112,6 = 80 + 32,6 | 102,4 = 80 + 22,4 | 100,5 = 80 + 20,5 | 30′ 109,3 – 113,6 – 117,3; 60′ 97,3 – 104,1 – 111,3; 120′ 93,4 – 102,8 – 109,7 |
| sólo cristaloides (2 L en 20 min) | intrínseca inf. | 117,6 = 60 + 57,6 | 124,5 = 60 + 64,5 | — |  |
| sólo cristaloides (2 L en 20 min) | intrínseca sup. | 117,6 = 100 + 17,6 | 124,5 = 100 + 24,5 | — |  |
| sólo cristaloides (2 L en 20 min) | medio | 117,6 = 80 + 37,6 | 124,5 = 80 + 44,5 | — | 30′ 113,7 – 118,5 – 121,7; 60′ 118,2 – 125,5 – 130,5 |
| sólo GR (2 U en 60 min) | intrínseca inf. | 113,2 = 60 + 53,2 | 103,3 = 60 + 43,3 | — |  |
| sólo GR (2 U en 60 min) | intrínseca sup. | 113,2 = 100 + 13,2 | 103,3 = 100 + 3,3 | — |  |
| sólo GR (2 U en 60 min) | medio | 113,2 = 80 + 33,2 | 103,3 = 80 + 23,3 | — | 30′ 109,9 – 114,2 – 117,6; 60′ 98,2 – 105,1 – 111,8 |
| sin tratamiento | intrínseca inf. | 127,9 = 60 + 67,9 | 133,3 = 60 + 73,3 | 147,2 = 60 + 87,2 |  |
| sin tratamiento | intrínseca sup. | 127,9 = 100 + 27,9 | 133,3 = 100 + 33,3 | 147,2 = 100 + 47,2 |  |
| sin tratamiento | medio | 127,9 = 80 + 47,9 | 133,3 = 80 + 53,3 | 147,2 = 80 + 67,2 | 30′ 124,0 – 128,6 – 132,1; 60′ 127,1 – 134,0 – 139,3; 120′ 136,0 – 147,2 – 153,8 |

Velocidad de resolución con manejo definitivo, por decaimiento simpático (τ) e intrínseca: minuto en que la parte simpática cae a la mitad de la de llegada («mitad simpática», depende de la intrínseca) y minuto en que la FC recorre la mitad de su propia caída hasta los 120′ («mitad de la caída»):

| τ simpático (min) | Intrínseca | Mitad simpática (min) | Mitad de la caída (min) | FC 120′ | Caída (lpm) | Parte simpática 120′ (lpm) |
|---|---|---|---|---|---|---|
| 2 | inf. | nunca | 28 | 100,5 | 23,5 | 40,5 |
| 2 | medio | 59 | 28 | 100,5 | 23,5 | 20,5 |
| 2 | sup. | 29 | 28 | 100,5 | 23,5 | 0,5 |
| 5 | inf. | nunca | 31 | 100,5 | 23,5 | 40,5 |
| 5 | medio | 62 | 31 | 100,5 | 23,5 | 20,5 |
| 5 | sup. | 32 | 31 | 100,5 | 23,5 | 0,5 |
| 15 | inf. | nunca | 41 | 100,6 | 23,4 | 40,6 |
| 15 | medio | 82 | 41 | 100,6 | 23,4 | 20,6 |
| 15 | sup. | 42 | 41 | 100,6 | 23,4 | 0,6 |

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `intrinsic_sinus_rate` | inf. | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `intrinsic_sinus_rate` | medio | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `intrinsic_sinus_rate` | sup. | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `sympathetic_decay_tau_min` | 2 | admisible · fuera del diseño de P2F | 127,9 | 133,3 | 147,2 | 111,4 | 101,5 | 100,5 |
| `sympathetic_decay_tau_min` | 5 | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `sympathetic_decay_tau_min` | 15 | admisible · fuera del diseño de P2F | 127,9 | 133,3 | 147,2 | 116,1 | 105,7 | 100,6 |
| `sympathetic_per_pressure_deficit` | 0,5 | admisible · fuera del diseño de P2F | 125,7 | 128,7 | 137,1 | 117,6 | 112,0 | 110,5 |
| `sympathetic_per_pressure_deficit` | 1 | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `sympathetic_per_pressure_deficit` | 2 | admisible · fuera del diseño de P2F | 132,3 | 142,5 | 167,3 | 102,6 | 83,2 | 80,6 |
| `sympathetic_per_debt` | 0,25 | admisible · fuera del diseño de P2F | 128,1 | 133,2 | 145,6 | 113,3 | 103,6 | 102,3 |
| `sympathetic_per_debt` | 0,5 | admisible | 127,9 | 133,3 | 147,2 | 112,6 | 102,4 | 100,5 |
| `sympathetic_per_debt` | 1 | admisible · fuera del diseño de P2F | 127,5 | 133,5 | 150,2 | 111,3 | 99,9 | 97,0 |

**gi_bleed_72f** — FC de llegada 112 lpm = intrínseca 60–100 (medio 80) + parte simpática 12–52 (medio 32); betabloqueo 0 (factor 1 − β = 1); ninguna otra fuente cronotrópica en estas corridas.

| Corrida | Intrínseca | 30′ (FC = intr. + simp.) | 60′ | 120′ | Región admisible (mín – mediana – máx) |
|---|---|---|---|---|---|
| manejo definitivo (GR + IBP + endoscopia) | intrínseca inf. | 104,1 = 60 + 44,1 | 97,0 = 60 + 37,0 | 95,3 = 60 + 35,3 |  |
| manejo definitivo (GR + IBP + endoscopia) | intrínseca sup. | 104,1 = 100 + 4,1 | 100,0 = 100 + 0,0 | 100,0 = 100 + 0,0 |  |
| manejo definitivo (GR + IBP + endoscopia) | medio | 104,1 = 80 + 24,1 | 97,0 = 80 + 17,0 | 95,3 = 80 + 15,3 | 30′ 100,8 – 105,1 – 107,3; 60′ 91,8 – 99,4 – 102,7; 120′ 88,2 – 98,9 – 101,3 |
| sólo cristaloides (2 L en 20 min) | intrínseca inf. | 107,7 = 60 + 47,7 | 112,4 = 60 + 52,4 | — |  |
| sólo cristaloides (2 L en 20 min) | intrínseca sup. | 107,7 = 100 + 7,7 | 112,4 = 100 + 12,4 | — |  |
| sólo cristaloides (2 L en 20 min) | medio | 107,7 = 80 + 27,7 | 112,4 = 80 + 32,4 | — | 30′ 103,7 – 108,5 – 111,9; 60′ 106,1 – 113,3 – 118,3 |
| sólo GR (2 U en 60 min) | intrínseca inf. | 104,5 = 60 + 44,5 | 97,6 = 60 + 37,6 | — |  |
| sólo GR (2 U en 60 min) | intrínseca sup. | 104,5 = 100 + 4,5 | 100,0 = 100 + 0,0 | — |  |
| sólo GR (2 U en 60 min) | medio | 104,5 = 80 + 24,5 | 97,6 = 80 + 17,6 | — | 30′ 101,2 – 105,5 – 107,8; 60′ 92,4 – 100,0 – 103,1 |
| sin tratamiento | intrínseca inf. | 114,3 = 60 + 54,3 | 117,8 = 60 + 57,8 | 126,9 = 60 + 66,9 |  |
| sin tratamiento | intrínseca sup. | 114,3 = 100 + 14,3 | 117,8 = 100 + 17,8 | 126,9 = 100 + 26,9 |  |
| sin tratamiento | medio | 114,3 = 80 + 34,3 | 117,8 = 80 + 37,8 | 126,9 = 80 + 46,9 | 30′ 110,4 – 115,0 – 118,5; 60′ 111,5 – 118,6 – 123,7; 120′ 118,7 – 127,5 – 133,6 |

Velocidad de resolución con manejo definitivo, por decaimiento simpático (τ) e intrínseca: minuto en que la parte simpática cae a la mitad de la de llegada («mitad simpática», depende de la intrínseca) y minuto en que la FC recorre la mitad de su propia caída hasta los 120′ («mitad de la caída»):

| τ simpático (min) | Intrínseca | Mitad simpática (min) | Mitad de la caída (min) | FC 120′ | Caída (lpm) | Parte simpática 120′ (lpm) |
|---|---|---|---|---|---|---|
| 2 | inf. | nunca | 29 | 95,3 | 16,7 | 35,3 |
| 2 | medio | 65 | 29 | 95,3 | 16,7 | 15,3 |
| 2 | sup. | 21 | 21 | 100,0 | 12,0 | 0,0 |
| 5 | inf. | nunca | 32 | 95,3 | 16,7 | 35,3 |
| 5 | medio | 71 | 32 | 95,3 | 16,7 | 15,3 |
| 5 | sup. | 24 | 24 | 100,0 | 12,0 | 0,0 |
| 15 | inf. | nunca | 41 | 95,5 | 16,5 | 35,5 |
| 15 | medio | 95 | 41 | 95,5 | 16,5 | 15,5 |
| 15 | sup. | 33 | 33 | 100,0 | 12,0 | 0,0 |

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `intrinsic_sinus_rate` | inf. | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 97,0 | 95,3 |
| `intrinsic_sinus_rate` | medio | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 97,0 | 95,3 |
| `intrinsic_sinus_rate` | sup. | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 100,0 | 100,0 |
| `sympathetic_decay_tau_min` | 2 | admisible · fuera del diseño de P2F | 114,3 | 117,8 | 126,9 | 103,3 | 96,3 | 95,3 |
| `sympathetic_decay_tau_min` | 5 | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 97,0 | 95,3 |
| `sympathetic_decay_tau_min` | 15 | admisible · fuera del diseño de P2F | 114,3 | 117,8 | 126,9 | 106,5 | 99,2 | 95,5 |
| `sympathetic_per_pressure_deficit` | 0,5 | admisible · fuera del diseño de P2F | 112,9 | 114,7 | 120,3 | 107,4 | 103,3 | 101,9 |
| `sympathetic_per_pressure_deficit` | 1 | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 97,0 | 95,3 |
| `sympathetic_per_pressure_deficit` | 2 | admisible · fuera del diseño de P2F | 117,2 | 123,8 | 140,2 | 97,5 | 84,4 | 82,2 |
| `sympathetic_per_debt` | 0,25 | admisible · fuera del diseño de P2F | 114,6 | 117,9 | 126,1 | 104,7 | 98,2 | 97,1 |
| `sympathetic_per_debt` | 0,5 | admisible | 114,3 | 117,8 | 126,9 | 104,1 | 97,0 | 95,3 |
| `sympathetic_per_debt` | 1 | admisible · fuera del diseño de P2F | 113,7 | 117,5 | 128,6 | 102,8 | 94,5 | 91,8 |
<!-- /generado:fc -->

**Preguntas para la docencia**
1. Tras una hemostasia y una reanimación exitosas, ¿qué rango de FC cabe esperar?
2. ¿Cuánto puede bajar razonablemente la FC por debajo de la taquicardia de llegada?
3. ¿Con qué rapidez debería resolverse la taquicardia compensadora?
4. ¿La frecuencia intrínseca se especifica mejor por caso o con un valor por defecto aprobado para la familia GI?

## 4. Decisión 3 · Caída de la presión sin tratamiento (P2G-4)

**Qué mueve la caída.** Sin tratamiento, la caída sólo la empuja la fuente hemorrágica: 2,5 mL-eq/min, el literal de
la familia (§8). La región admisible varía la posición de precarga en un solo conjunto, así que el rango es
estrecho. PAS mínima – máxima:

| | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| 57m | 88 | 80–84 | 72–79 | 26–69 |
| 72f | 98 | 93–95 | 87–92 | 71–85 |

- **La caída se acelera bajo la rodilla de presión (0,5).** En 57m, al punto medio, la PAS pasa de 72 a los 60 min a
  26 a los 120.
- **Con el colapso apagado, la corrida se detiene** en el minuto 144: el gasto llega a 0 con pulso.

**Efectos (filas de abajo).**
- Más fuerte:
  - la tasa de la fuente (× 2: 26 a los 60 min; × 0,5: 80);
  - la posición de precarga (superior: 79 a los 60 min);
  - la escala de la curva (600 mL: 62 a los 60 min y se detiene en el 104; 1500 mL: 79).
- Más débil: la ganancia de PAS (35–55: 75–68 a los 60 min) y la rodilla, que sólo actúa bajo ella.
- **Sin efecto en estas corridas:** el acoplamiento bomba/precarga, la sensibilidad a la poscarga y la reserva de
  bomba (la bomba y el tono no se mueven), y la ganancia de PAD sobre la PAS.

<!-- generado:presion -->
**gi_bleed_57m** — sin tratamiento, mínimo – mediana – máximo en la región admisible:

|  | 0′ | 15′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| SBP | 88,0 – 88,0 – 88,0 | 84,2 – 84,2 – 85,9 | 80,1 – 80,1 – 83,8 | 71,5 – 71,5 – 79,1 | 25,6 – 25,6 – 68,5 |
| MAP | 65,3 – 65,3 – 65,3 | 62,6 – 62,6 – 63,9 | 59,8 – 59,8 – 62,4 | 53,7 – 53,7 – 59,1 | 19,3 – 19,3 – 51,6 |

| Factor | Nivel | Estado | 15′ PAS/PAM | 30′ | 60′ | 120′ | Se detiene en |
|---|---|---|---|---|---|---|---|
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×0,5 | sonda de sensibilidad · fuera del diseño de P2F | 86 / 64 | 84 / 63 | 80 / 60 | 72 / 54 |  |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×1 | sonda de sensibilidad | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×2 | sonda de sensibilidad · fuera del diseño de P2F | 80 / 60 | 72 / 54 | 26 / 19 | — / — | 72 |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×4 | sonda de sensibilidad · fuera del diseño de P2F | 72 / 54 | 26 / 19 | — / — | — / — | 36 |
| `preload_fraction` | inf. | rechazado por las reglas congeladas | 80 / 60 | 71 / 53 | 28 / 21 | — / — | 75 |
| `preload_fraction` | medio | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `preload_fraction` | sup. | admisible | 86 / 64 | 84 / 62 | 79 / 59 | 69 / 52 |  |
| `preload_curve_scale_ml` | 600 | admisible · fuera del diseño de P2F | 83 / 62 | 77 / 58 | 62 / 47 | — / — | 104 |
| `preload_curve_scale_ml` | 833 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `preload_curve_scale_ml` | 1500 | admisible · fuera del diseño de P2F | 86 / 64 | 84 / 62 | 79 / 59 | 69 / 52 |  |
| `pump_preload_coupling` | 0 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `pump_preload_coupling` | 0,5 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `pump_preload_coupling` | 1 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `afterload_sensitivity` | 0,1 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `afterload_sensitivity` | 0,3 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `afterload_sensitivity` | 0,5 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `pump_reserve` | 0,7 | no evaluado (ninguna regla congelada lo lee) · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `pump_reserve` | 1 | no evaluado (ninguna regla congelada lo lee) | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `low_output_pressure_knee` | 0,3 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 37 / 28 |  |
| `low_output_pressure_knee` | 0,5 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `low_output_pressure_knee` | 0,6 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 60 | 72 / 54 | 23 / 17 |  |
| `sbp_per_pressure_deficit` | 35 | admisible · fuera del diseño de P2F | 85 / 63 | 82 / 60 | 75 / 55 | 28 / 20 |  |
| `sbp_per_pressure_deficit` | 45 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `sbp_per_pressure_deficit` | 55 | admisible · fuera del diseño de P2F | 83 / 62 | 78 / 59 | 68 / 53 | 24 / 19 |  |
| `dbp_per_pressure_deficit` | 15 | admisible · fuera del diseño de P2F | 84 / 63 | 80 / 61 | 72 / 56 | 26 / 21 |  |
| `dbp_per_pressure_deficit` | 25 | admisible | 84 / 63 | 80 / 60 | 72 / 54 | 26 / 19 |  |
| `dbp_per_pressure_deficit` | 30 | admisible · fuera del diseño de P2F | 84 / 62 | 80 / 59 | 72 / 53 | 26 / 19 |  |

**gi_bleed_72f** — sin tratamiento, mínimo – mediana – máximo en la región admisible:

|  | 0′ | 15′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| SBP | 98,0 – 98,0 – 98,0 | 95,5 – 95,5 – 96,6 | 92,8 – 92,8 – 95,2 | 87,2 – 87,2 – 92,1 | 71,0 – 71,0 – 85,0 |
| MAP | 74,0 – 74,0 – 74,0 | 72,2 – 72,2 – 73,0 | 70,4 – 70,4 – 72,0 | 66,4 – 66,4 – 69,8 | 54,7 – 54,7 – 64,9 |

| Factor | Nivel | Estado | 15′ PAS/PAM | 30′ | 60′ | 120′ | Se detiene en |
|---|---|---|---|---|---|---|---|
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×0,5 | sonda de sensibilidad · fuera del diseño de P2F | 97 / 73 | 95 / 72 | 93 / 70 | 87 / 66 |  |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×1 | sonda de sensibilidad | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×2 | sonda de sensibilidad · fuera del diseño de P2F | 93 / 70 | 87 / 66 | 71 / 55 | — / — | 100 |
| `volume_loss_ml_per_min` y `hb_loss_g_dl_per_min` (× tasa) | ×4 | sonda de sensibilidad · fuera del diseño de P2F | 87 / 66 | 71 / 55 | — / — | — / — | 50 |
| `preload_fraction` | inf. | rechazado por las reglas congeladas | 93 / 71 | 88 / 67 | 77 / 59 | — / — | 119 |
| `preload_fraction` | medio | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `preload_fraction` | sup. | admisible | 97 / 73 | 95 / 72 | 92 / 70 | 85 / 65 |  |
| `preload_curve_scale_ml` | 600 | admisible · fuera del diseño de P2F | 94 / 72 | 91 / 69 | 82 / 63 | 31 / 24 |  |
| `preload_curve_scale_ml` | 833 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `preload_curve_scale_ml` | 1500 | admisible · fuera del diseño de P2F | 97 / 73 | 95 / 72 | 92 / 70 | 86 / 65 |  |
| `pump_preload_coupling` | 0 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `pump_preload_coupling` | 0,5 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `pump_preload_coupling` | 1 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `afterload_sensitivity` | 0,1 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `afterload_sensitivity` | 0,3 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `afterload_sensitivity` | 0,5 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `pump_reserve` | 0,7 | no evaluado (ninguna regla congelada lo lee) · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `pump_reserve` | 1 | no evaluado (ninguna regla congelada lo lee) | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `low_output_pressure_knee` | 0,3 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 74 / 57 |  |
| `low_output_pressure_knee` | 0,5 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `low_output_pressure_knee` | 0,6 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 63 / 48 |  |
| `sbp_per_pressure_deficit` | 35 | admisible · fuera del diseño de P2F | 96 / 72 | 94 / 71 | 90 / 67 | 76 / 56 |  |
| `sbp_per_pressure_deficit` | 45 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `sbp_per_pressure_deficit` | 55 | admisible · fuera del diseño de P2F | 95 / 72 | 92 / 70 | 85 / 66 | 66 / 53 |  |
| `dbp_per_pressure_deficit` | 15 | admisible · fuera del diseño de P2F | 95 / 73 | 93 / 71 | 87 / 68 | 71 / 58 |  |
| `dbp_per_pressure_deficit` | 25 | admisible | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 55 |  |
| `dbp_per_pressure_deficit` | 30 | admisible · fuera del diseño de P2F | 95 / 72 | 93 / 70 | 87 / 66 | 71 / 53 |  |
<!-- /generado:presion -->

**Pregunta para la docencia:** ¿qué grado de deterioro hipotensivo sin tratamiento, a lo largo de una hora, debería
representar cada caso?

## 5. Decisión 4 · Colapso terminal (P2G-5)

**Estado en GI.** El colapso terminal está apagado en todas las corridas GI canónicas
(`collapse_output_threshold = None`) y así sigue. Esta sección es sintética, sobre la llegada neutra de las sondas.

**Mecanismo (P2E-3).**
- **Severidad:** bajo el umbral, la severidad es (umbral − gasto) / umbral.
- **Acumulación:** cada minuto la carga suma ganancia × severidad.
- **Transición:** la transición terminal ocurre cuando la carga llega al límite.
- **Repago:** sobre el umbral, la carga se repaga con su τ.

**Resultados.**
- La primera tabla da los minutos de acumulación hasta el límite con un gasto constante, en aritmética exacta. Una
  corrida simulada para un minuto después (el minuto en que cae el gasto), y uno más cuando la cuenta es entera,
  porque la suma en coma flotante del modelo queda justo bajo el límite.
- Los patrones muestran, con la regla en sus puntos medios:
  - un flujo moderado breve no para;
  - uno moderado sostenido para a los 92 min;
  - uno profundo, a los 24 min.
- **El repago decide los episodios repetidos.** Sin repago, el segundo episodio para en el minuto 62; con τ 30, no
  para.
- **Ritmo terminal:** es el que declara el perfil (AESP o asistolia). No depende de la causa ni del estado.

**Sin el colapso.** Una hemorragia GI sin tratar no termina en paro: termina en una corrida detenida (57m al punto
medio, en el minuto 144).

<!-- generado:colapso -->
Minutos de acumulación hasta el límite con gasto constante, en aritmética exacta: ⌈límite × umbral / (ganancia × (umbral − gasto))⌉. Un paro simulado llega un minuto después (el minuto en que cae el gasto), y uno más cuando el cociente es entero, porque la suma en coma flotante del modelo queda justo bajo el límite:

| Umbral | Ganancia | Límite | gasto 0,05 | gasto 0,1 | gasto 0,15 | gasto 0,2 | gasto 0,25 | gasto 0,35 |
|---|---|---|---|---|---|---|---|---|
| 0,2 | 0,5 | 5 | 14 | 20 | 40 | nunca | nunca | nunca |
| 0,2 | 0,5 | 15 | 40 | 60 | 120 | nunca | nunca | nunca |
| 0,2 | 0,5 | 30 | 80 | 120 | 240 | nunca | nunca | nunca |
| 0,2 | 1,0 | 5 | 7 | 10 | 20 | nunca | nunca | nunca |
| 0,2 | 1,0 | 15 | 20 | 30 | 60 | nunca | nunca | nunca |
| 0,2 | 1,0 | 30 | 40 | 60 | 120 | nunca | nunca | nunca |
| 0,2 | 2,0 | 5 | 4 | 5 | 10 | nunca | nunca | nunca |
| 0,2 | 2,0 | 15 | 10 | 15 | 30 | nunca | nunca | nunca |
| 0,2 | 2,0 | 30 | 20 | 30 | 60 | nunca | nunca | nunca |
| 0,3 | 0,5 | 5 | 12 | 15 | 20 | 30 | 60 | nunca |
| 0,3 | 0,5 | 15 | 36 | 45 | 60 | 90 | 180 | nunca |
| 0,3 | 0,5 | 30 | 72 | 90 | 120 | 180 | 360 | nunca |
| 0,3 | 1,0 | 5 | 6 | 8 | 10 | 15 | 30 | nunca |
| 0,3 | 1,0 | 15 | 18 | 23 | 30 | 45 | 90 | nunca |
| 0,3 | 1,0 | 30 | 36 | 45 | 60 | 90 | 180 | nunca |
| 0,3 | 2,0 | 5 | 3 | 4 | 5 | 8 | 15 | nunca |
| 0,3 | 2,0 | 15 | 9 | 12 | 15 | 23 | 45 | nunca |
| 0,3 | 2,0 | 30 | 18 | 23 | 30 | 45 | 90 | nunca |
| 0,4 | 0,5 | 5 | 12 | 14 | 16 | 20 | 27 | 80 |
| 0,4 | 0,5 | 15 | 35 | 40 | 48 | 60 | 80 | 240 |
| 0,4 | 0,5 | 30 | 69 | 80 | 96 | 120 | 160 | 480 |
| 0,4 | 1,0 | 5 | 6 | 7 | 8 | 10 | 14 | 40 |
| 0,4 | 1,0 | 15 | 18 | 20 | 24 | 30 | 40 | 120 |
| 0,4 | 1,0 | 30 | 35 | 40 | 48 | 60 | 80 | 240 |
| 0,4 | 2,0 | 5 | 3 | 4 | 4 | 5 | 7 | 20 |
| 0,4 | 2,0 | 15 | 9 | 10 | 12 | 15 | 20 | 60 |
| 0,4 | 2,0 | 30 | 18 | 20 | 24 | 30 | 40 | 120 |

Patrones sobre la llegada sintética neutra, con la regla en sus puntos medios (umbral 0,3, ganancia 1, límite 15, repago 60 min):

| Patrón | Paro (min) | Carga máx. | carga 10′ | 26′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|---|---|---|
| flujo moderado transitorio (0,25 durante 10 min) | no | 1,7 | 1,5 | 1,3 | 0,7 | 0,3 | 0,0 |
| flujo moderado sostenido (0,25) | 92 | 15,2 | 1,5 | 4,2 | 9,8 | 15,2 | 15,2 |
| flujo profundo sostenido (0,1) | 24 | 15,3 | 6,0 | 15,3 | 15,3 | 15,3 | 15,3 |
| recuperación antes de una carga sustancial (0,15 durante 10 min) | no | 5,0 | 4,5 | 3,9 | 2,2 | 0,8 | 0,1 |
| recuperación tras una carga sustancial (0,15 durante 26 min) | no | 13,0 | 4,5 | 12,5 | 7,5 | 2,8 | 0,4 |

Repago entre episodios (0,15 durante 26 min; recuperado 30 min; 0,15 durante 15 min):

| τ de repago (min) | Paro en el 2.º episodio (min) | Carga 34 min después del 1.º |
|---|---|---|
| sin repago | 62 | 13,0 |
| 30 | no | 4,3 |
| 60 | 72 | 7,5 |
| 240 | 65 | 11,3 |

Ritmo terminal según la política declarada: `asystole` → `asystole`; `pea` → `pea`. La regla no mira la causa ni el estado: el ritmo es el que declara el perfil.
<!-- /generado:colapso -->

**Preguntas para la docencia**
1. ¿Con qué grado de flujo bajo sostenido debería volverse posible el colapso terminal?
2. ¿Aproximadamente cuánto debe persistir un shock profundo antes de que la AESP o la asistolia sean plausibles en
   este simulador?
3. ¿El ritmo debe depender de la causa o del estado, o seguir siendo una política declarada del caso o del módulo?

## 6. Decisión 5 · Volumen agresivo y techo de presión (P2G-6)

`aggressive_volume`: 4 U de GR en 60 min más 2 L de SF en 30 min. Todas las configuraciones reciben las mismas
entradas, un V neto de +1088 mL-eq.

**Presión y gasto.** Los dimensiona la posición y la escala de la curva de precarga.
- **Pico de PAS dentro del diseño de P2F** (escala de la curva por defecto, 833 mL): 122–151 (57m) y 121–140 (72f).
  La precarga inferior con esa escala la rechazan las reglas congeladas (picos de 225 y 178).
- **Con otras escalas**, que P2F no barrió pero las reglas congeladas aceptan: 113–186 (57m) y 114–155 (72f). La
  precarga inferior con escala 600 se rechaza y llega a 243 (57m).
- **No hay techo de presión por encima de la llegada.** PAS = llegada + ganancia × (gasto relativo − 1), y el gasto
  llega a 1,4–4,4 veces el de llegada. Esa falta de techo es la que permite los picos altos; si son plausibles lo
  decide la docencia (FD-14).

**Cuándo deja de servir el líquido.** La respuesta marginal final (lo que darían 500 mL más, frente a los primeros
500) es exp(−1088 / escala): 0,16 con 600 mL, 0,27 con 833 y 0,48 con 1500. La escala decide cuándo el líquido se
vuelve mayormente ineficaz.

**Congestión.**
- Con reserva 1 no aparece L. Con reserva 0,7 llega a 1,1 (57m) y 1,3 (72f).
- L todavía no alimenta la SpO2. Su lectura clínica depende de una decisión pendiente.

**FC.** Con precarga baja, la FC cae hasta la intrínseca (80).

<!-- generado:volumen -->
**gi_bleed_57m** — volumen agresivo (90 min). Lo que mueve la presión es la posición y la escala de la curva; la rodilla y la ganancia de congestión y la reserva sólo cambian L (rango en «L final»). «Estado» aplica las reglas congeladas al conjunto completo (el mismo nivel en los dos casos) con esa escala; «En el diseño de P2F» dice si P2F barrió esa celda (sólo con la escala por defecto).

| Precarga | Escala (mL) | V neto (mL-eq) | PAS llegada → pico | PAM pico | Gasto pico (× llegada) | Posición llegada → final | Respuesta marginal final | FC final | L final | Estado | En el diseño de P2F |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inf. | 600 | 1088 | 88 → 243 | 174 | 4,44 | 0,20 → 0,87 | 0,16 | 80 | 0,000 – 0,677 | rechazado por las reglas congeladas | no |
| inf. | 833 | 1088 | 88 → 225 | 161 | 4,03 | 0,20 → 0,78 | 0,27 | 80 | 0,000 – 0,191 | rechazado por las reglas congeladas | sí |
| inf. | 1500 | 1088 | 88 → 186 | 134 | 3,18 | 0,20 → 0,61 | 0,48 | 80 | 0,000 – 0,000 | admisible | no |
| medio | 600 | 1088 | 88 → 160 | 116 | 2,60 | 0,35 → 0,89 | 0,16 | 82 | 0,000 – 0,863 | admisible | no |
| medio | 833 | 1088 | 88 → 151 | 110 | 2,41 | 0,35 → 0,82 | 0,27 | 87 | 0,000 – 0,403 | admisible | sí |
| medio | 1500 | 1088 | 88 → 134 | 97 | 2,01 | 0,35 → 0,69 | 0,48 | 97 | 0,000 – 0,000 | admisible | no |
| sup. | 600 | 1088 | 88 → 127 | 93 | 1,86 | 0,50 → 0,92 | 0,16 | 100 | 0,000 – 1,082 | admisible | no |
| sup. | 833 | 1088 | 88 → 122 | 89 | 1,76 | 0,50 → 0,86 | 0,27 | 103 | 0,000 – 0,682 | admisible | sí |
| sup. | 1500 | 1088 | 88 → 113 | 83 | 1,55 | 0,50 → 0,76 | 0,48 | 108 | 0,000 – 0,062 | admisible | no |

**gi_bleed_72f** — volumen agresivo (90 min). Lo que mueve la presión es la posición y la escala de la curva; la rodilla y la ganancia de congestión y la reserva sólo cambian L (rango en «L final»). «Estado» aplica las reglas congeladas al conjunto completo (el mismo nivel en los dos casos) con esa escala; «En el diseño de P2F» dice si P2F barrió esa celda (sólo con la escala por defecto).

| Precarga | Escala (mL) | V neto (mL-eq) | PAS llegada → pico | PAM pico | Gasto pico (× llegada) | Posición llegada → final | Respuesta marginal final | FC final | L final | Estado | En el diseño de P2F |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inf. | 600 | 1088 | 98 → 188 | 138 | 3,01 | 0,30 → 0,89 | 0,16 | 80 | 0,000 – 0,798 | rechazado por las reglas congeladas | no |
| inf. | 833 | 1088 | 98 → 178 | 130 | 2,77 | 0,30 → 0,81 | 0,27 | 80 | 0,000 – 0,326 | rechazado por las reglas congeladas | sí |
| inf. | 1500 | 1088 | 98 → 155 | 114 | 2,27 | 0,30 → 0,66 | 0,48 | 80 | 0,000 – 0,000 | admisible | no |
| medio | 600 | 1088 | 98 → 145 | 107 | 2,05 | 0,45 → 0,91 | 0,16 | 83 | 0,000 – 1,005 | admisible | no |
| medio | 833 | 1088 | 98 → 140 | 103 | 1,93 | 0,45 → 0,85 | 0,27 | 87 | 0,000 – 0,582 | admisible | sí |
| medio | 1500 | 1088 | 98 → 128 | 95 | 1,67 | 0,45 → 0,73 | 0,48 | 93 | 0,000 – 0,000 | admisible | no |
| sup. | 600 | 1088 | 98 → 124 | 92 | 1,57 | 0,60 → 0,93 | 0,16 | 95 | 0,000 – 1,255 | admisible | no |
| sup. | 833 | 1088 | 98 → 121 | 90 | 1,51 | 0,60 → 0,89 | 0,27 | 97 | 0,000 – 0,910 | admisible | sí |
| sup. | 1500 | 1088 | 98 → 114 | 86 | 1,36 | 0,60 → 0,81 | 0,48 | 100 | 0,000 – 0,319 | admisible | no |

Estado de los parámetros de congestión: `congestion_per_excess_preload` 0,02 admisible, 0,05 admisible, 0,1 admisible; `congestion_preload_knee` 0,75 admisible, 0,85 admisible, 0,92 admisible.
<!-- /generado:volumen -->

**Preguntas para la docencia**
1. ¿Cuánto puede subir la PA con volumen solo, repetido?
2. ¿A partir de qué punto el líquido adicional debería volverse mayormente ineficaz?
3. ¿Cuánta congestión se tolera antes de que la trayectoria sea clínicamente inverosímil?

## 7. Decisión 6 · Frecuencia respiratoria (P2G-7)

**Descomposición.** FR = parte ventilatoria + parte metabólica.
- **Parte ventilatoria:** la FR de llegada menos su parte metabólica, × (1 + W) si W > 0.
- **Parte metabólica:** el impulso acidémico, que satura en `rr_metabolic_max`.

En GI no hay mecanismo W ni N, así que la parte ventilatoria es constante y fija el piso de la recuperación: 13,2
(57m) y 15,4 (72f).

**Rango.**
- En la región va de 13 a 36 (57m) y de 15 a 38 (72f).
- La dispersión viene sobre todo de la trayectoria del lactato (decisión 1). Recorriendo su banda con lo demás en el
  punto medio, un parámetro de FR cambia la FR, como máximo:
  - `rr_per_lactate`: 5,2 resp/min (72f, manejo definitivo, 120 min) y 3,8 (57m);
  - `rr_metabolic_max` y `lactate_drive_threshold_mmol_l`: 2,6 (57m, manejo definitivo);
  - `rr_ventilatory_floor`: 0,5 o menos.
  Sin tratamiento, ninguno pasa de 1,1.
- **Techo teórico** (lactato sin límite): FR de llegada − impulso metabólico de llegada + `rr_metabolic_max`, y
  luego `rr_max`. Lo lee la tabla de cotas, generada desde `derived.respiratory_rate`.
  - Al punto medio es 13,2 + 25 = 38,2 en 57m.
  - Sobre la cuadrícula de bandas de FR: 27,5–36,3 con `rr_metabolic_max` 15, 32,2–45,9 con 25 y 35,4–50,8 con 30
    (57m); 27,3–36,5, 34,0–46,4 y 38,0–51,4 (72f). Con `rr_max` 40 el techo no pasa de 40.
  - En las corridas no se alcanza: el máximo observado es 36 (57m) y 38 (72f).
- **El reparto de la FR de llegada también fija el piso de la recuperación** (lactato bajo el umbral). Sobre la
  cuadrícula va de 10,0 a 21,3 (57m) y de 10,0 a 21,5 (72f): con un reparto metabólico pequeño (`rr_per_lactate` 3)
  la parte ventilatoria sube a ~20 resp/min, y ése es el nuevo piso.

**Por gravedad del shock de llegada, sin tratamiento:**
- leve: la FR baja de 26 a 20, porque el lactato se aclara;
- moderado: de 26 a 23,5;
- grave: sube de 26 a 28.

**Con mejoría** (manejo definitivo, 57m a los 120 min): 15–24.

<!-- generado:fr -->
**gi_bleed_57m** — FR de llegada 26 resp/min con lactato 4,4 mmol/L. Cotas del modelo sobre la cuadrícula de bandas de FR (`rr_per_lactate` × `lactate_drive_threshold_mmol_l` × `rr_ventilatory_floor`, por `rr_metabolic_max`): techo con lactato sin límite, antes y después de `rr_max`, y piso con lactato bajo el umbral (mínimo – máximo):

| `rr_metabolic_max` | techo con `rr_max` 40 | techo con `rr_max` 60 | piso |
|---|---|---|---|
| 15 | 27,5 – 36,3 | 27,5 – 36,3 | 12,5 – 21,3 |
| 25 | 32,2 – 40,0 | 32,2 – 45,9 | 10,0 – 20,9 |
| 30 | 35,4 – 40,0 | 35,4 – 50,8 | 10,0 – 20,8 |

En las corridas del paquete, FR observada entre 13,2 y 36,2. Mínimo – mediana – máximo en la región admisible:

| Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| sin tratamiento | 26,0 – 26,0 – 26,0 | 17,6 – 24,6 – 34,5 | 13,2 – 23,6 – 35,6 | 13,2 – 24,1 – 36,2 |
| manejo definitivo (GR + IBP + endoscopia) | 26,0 – 26,0 – 26,0 | 17,5 – 24,5 – 34,2 | 13,2 – 22,9 – 34,3 | 13,2 – 19,6 – 30,6 |

| Shock | Corrida | 0′ (FR = ventilatoria + metabólica) | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| leve (D 0, entrega 1,0) | sin tratamiento | 26,0 = 13,2 + 12,8 | 23,0 = 13,2 + 9,8 | 20,7 = 13,2 + 7,5 | 20,1 = 13,2 + 6,9 |
| leve (D 0, entrega 1,0) | mejoría (manejo definitivo) | 26,0 = 13,2 + 12,8 | 22,9 = 13,2 + 9,7 | 20,0 = 13,2 + 6,8 | 14,9 = 13,2 + 1,8 |
| moderado (D 20, entrega 0,85) | sin tratamiento | 26,0 = 13,2 + 12,8 | 24,7 = 13,2 + 11,5 | 23,6 = 13,2 + 10,4 | 23,5 = 13,2 + 10,3 |
| moderado (D 20, entrega 0,85) | mejoría (manejo definitivo) | 26,0 = 13,2 + 12,8 | 24,5 = 13,2 + 11,3 | 22,5 = 13,2 + 9,3 | 18,1 = 13,2 + 4,9 |
| grave (D 60, entrega 0,6) | sin tratamiento | 26,0 = 13,2 + 12,8 | 27,4 = 13,2 + 14,3 | 27,9 = 13,2 + 14,7 | 28,3 = 13,2 + 15,2 |
| grave (D 60, entrega 0,6) | mejoría (manejo definitivo) | 26,0 = 13,2 + 12,8 | 27,3 = 13,2 + 14,1 | 26,9 = 13,2 + 13,7 | 23,6 = 13,2 + 10,5 |

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `rr_per_lactate` | 3 | admisible · fuera del diseño de P2F | 25,2 | 24,6 | 24,6 | 25,1 | 24,0 | 21,8 |
| `rr_per_lactate` | 7,5 | admisible | 24,7 | 23,6 | 23,5 | 24,5 | 22,5 | 18,1 |
| `rr_per_lactate` | 12 | admisible · fuera del diseño de P2F | 24,8 | 23,8 | 23,8 | 24,6 | 22,8 | 18,0 |
| `rr_metabolic_max` | 15 | admisible · fuera del diseño de P2F | 25,1 | 24,4 | 24,4 | 25,0 | 23,6 | 20,1 |
| `rr_metabolic_max` | 25 | admisible | 24,7 | 23,6 | 23,5 | 24,5 | 22,5 | 18,1 |
| `rr_metabolic_max` | 30 | admisible · fuera del diseño de P2F | 24,5 | 23,3 | 23,2 | 24,3 | 22,1 | 17,5 |
| `rr_ventilatory_floor` | 10 | admisible · fuera del diseño de P2F | 24,7 | 23,6 | 23,5 | 24,5 | 22,5 | 18,1 |
| `rr_ventilatory_floor` | 12 | admisible | 24,7 | 23,6 | 23,5 | 24,5 | 22,5 | 18,1 |
| `rr_ventilatory_floor` | 14 | admisible · fuera del diseño de P2F | 24,8 | 23,7 | 23,7 | 24,6 | 22,7 | 18,6 |
| `lactate_drive_threshold_mmol_l` | 1,5 | admisible · fuera del diseño de P2F | 24,9 | 24,0 | 23,9 | 24,7 | 23,1 | 19,4 |
| `lactate_drive_threshold_mmol_l` | 2 | admisible | 24,7 | 23,6 | 23,5 | 24,5 | 22,5 | 18,1 |
| `lactate_drive_threshold_mmol_l` | 2,5 | admisible · fuera del diseño de P2F | 24,5 | 23,2 | 23,1 | 24,2 | 21,9 | 16,8 |

**gi_bleed_72f** — FR de llegada 24 resp/min con lactato 3,4 mmol/L. Cotas del modelo sobre la cuadrícula de bandas de FR (`rr_per_lactate` × `lactate_drive_threshold_mmol_l` × `rr_ventilatory_floor`, por `rr_metabolic_max`): techo con lactato sin límite, antes y después de `rr_max`, y piso con lactato bajo el umbral (mínimo – máximo):

| `rr_metabolic_max` | techo con `rr_max` 40 | techo con `rr_max` 60 | piso |
|---|---|---|---|
| 15 | 27,3 – 36,5 | 27,3 – 36,5 | 12,3 – 21,5 |
| 25 | 34,0 – 40,0 | 34,0 – 46,4 | 10,0 – 21,4 |
| 30 | 38,0 – 40,0 | 38,0 – 51,4 | 10,0 – 21,4 |

En las corridas del paquete, FR observada entre 15,4 y 38,1. Mínimo – mediana – máximo en la región admisible:

| Corrida | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| sin tratamiento | 24,0 – 24,0 – 24,0 | 16,4 – 23,1 – 36,1 | 15,4 – 22,6 – 37,6 | 15,4 – 23,4 – 38,1 |
| manejo definitivo (GR + IBP + endoscopia) | 24,0 – 24,0 – 24,0 | 16,3 – 22,9 – 35,9 | 15,4 – 21,7 – 36,5 | 15,4 – 19,1 – 32,5 |

| Shock | Corrida | 0′ (FR = ventilatoria + metabólica) | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| leve (D 0, entrega 1,0) | sin tratamiento | 24,0 = 15,4 + 8,6 | 21,2 = 15,4 + 5,8 | 19,3 = 15,4 + 3,8 | 18,8 = 15,4 + 3,4 |
| leve (D 0, entrega 1,0) | mejoría (manejo definitivo) | 24,0 = 15,4 + 8,6 | 21,2 = 15,4 + 5,7 | 18,6 = 15,4 + 3,2 | 15,4 = 15,4 + 0,0 |
| moderado (D 20, entrega 0,85) | sin tratamiento | 24,0 = 15,4 + 8,6 | 23,4 = 15,4 + 7,9 | 22,8 = 15,4 + 7,3 | 23,1 = 15,4 + 7,7 |
| moderado (D 20, entrega 0,85) | mejoría (manejo definitivo) | 24,0 = 15,4 + 8,6 | 23,1 = 15,4 + 7,7 | 21,7 = 15,4 + 6,2 | 18,0 = 15,4 + 2,6 |
| grave (D 60, entrega 0,6) | sin tratamiento | 24,0 = 15,4 + 8,6 | 26,8 = 15,4 + 11,4 | 28,0 = 15,4 + 12,6 | 29,0 = 15,4 + 13,6 |
| grave (D 60, entrega 0,6) | mejoría (manejo definitivo) | 24,0 = 15,4 + 8,6 | 26,7 = 15,4 + 11,3 | 27,1 = 15,4 + 11,7 | 24,5 = 15,4 + 9,1 |

| Factor | Nivel | Estado | sin trat. 30′ | sin trat. 60′ | sin trat. 120′ | definitivo 30′ | definitivo 60′ | definitivo 120′ |
|---|---|---|---|---|---|---|---|---|
| `rr_per_lactate` | 3 | admisible · fuera del diseño de P2F | 23,7 | 23,4 | 23,5 | 23,6 | 22,8 | 21,2 |
| `rr_per_lactate` | 7,5 | admisible | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `rr_per_lactate` | 12 | admisible · fuera del diseño de P2F | 23,2 | 22,5 | 22,9 | 22,9 | 21,0 | 16,0 |
| `rr_metabolic_max` | 15 | admisible · fuera del diseño de P2F | 23,5 | 23,0 | 23,3 | 23,3 | 22,1 | 19,0 |
| `rr_metabolic_max` | 25 | admisible | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `rr_metabolic_max` | 30 | admisible · fuera del diseño de P2F | 23,3 | 22,7 | 23,0 | 23,1 | 21,5 | 17,8 |
| `rr_ventilatory_floor` | 10 | admisible · fuera del diseño de P2F | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `rr_ventilatory_floor` | 12 | admisible | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `rr_ventilatory_floor` | 14 | admisible · fuera del diseño de P2F | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `lactate_drive_threshold_mmol_l` | 1,5 | admisible · fuera del diseño de P2F | 23,4 | 22,9 | 23,2 | 23,3 | 22,0 | 18,9 |
| `lactate_drive_threshold_mmol_l` | 2 | admisible | 23,4 | 22,8 | 23,1 | 23,1 | 21,7 | 18,0 |
| `lactate_drive_threshold_mmol_l` | 2,5 | admisible · fuera del diseño de P2F | 23,2 | 22,6 | 23,0 | 23,0 | 21,3 | 18,1 |
<!-- /generado:fr -->

**Preguntas para la docencia**
1. ¿Qué rango de FR es plausible en un shock hemorrágico digestivo no complicado?
2. ¿Qué taquipnea metabólica máxima debería permitir el núcleo sin enfermedad respiratoria?
3. ¿Qué límite inferior es aceptable durante la recuperación cuando no hay ningún mecanismo depresor (W o N)?

## 8. Valores por defecto de la familia (P2G-8)

Nombres exactos y valores actuales. «Categoría» es sólo una categoría de recomendación: la docencia decide. En
particular, «no listado» no significa β = 0 salvo que la docencia adopte esa convención de autoría.

| Parámetro | Valor actual | Significado fisiológico | Evidencia en la verdad del caso | Si se adopta un valor de familia | Si se exige declararlo por caso | Categoría |
|---|---|---|---|---|---|---|
| `beta_blockade` (caso) | 0,0 neutro (`default_unmapped`) | cuánto atenúa el betabloqueo la respuesta cronotrópica: FC = intrínseca + 25 × (1 − β) × impulso | 57m ibuprofeno (`clinical_cases.py:889`), 72f naproxeno (`:918`); ningún betabloqueador listado, pero ningún caso dice que no lo toma | una convención «no listado ⇒ 0»; si un caso omite un betabloqueador, la FC responde de más sin aviso | cada caso declara β, también el 0: más trabajo de autoría, explícito y auditable | FACULTY_DECISION_REQUIRED |
| `pump_reserve` (caso) | 1,0 neutro | fracción de la reserva cardíaca normal; en el núcleo sólo la lee la congestión (déficit = 1 − reserva × P) | VI hiperdinámico (`:154`, `:156`), radiografía sin edema (`:903`, `:932`), troponina bajo el límite; «sin líneas B» es el valor por defecto de `_pocus` (`:69`, `:83`); ninguna cardiopatía mencionada | 1,0 sin hallazgos cardíacos: el volumen agresivo no congestiona (decisión 5); la edad (72f) no la baja | permite una reserva menor con hallazgos; alguien debe autorizarla en cada caso | SAFE_FAMILY_DEFAULT_CANDIDATE (queda abierto si la edad sola debe bajarla) |
| `volume_loss_ml_per_min` (`GIHaemorrhage`; registro `gi_volume_loss_ml_per_min`) | 2,5 mL-eq/min (literal del motor: 0,003 de circulación/min × 833 mL-eq; `family_engine.py:2169`) | sangrado sin tratar, en volumen circulante efectivo | melena desde ayer (57m, `:890`); tres días y otro episodio hoy (72f, `:921`); ninguna tasa | ambos casos sangran igual; la caída de PA sin tratamiento la fijan la posición y la curva de precarga (decisión 3) | permite distinguir un sangrado activo; nada en los casos dice la tasa | FACULTY_DECISION_REQUIRED (depende de la decisión 3) |
| `hb_loss_g_dl_per_min` (`gi_hb_loss_g_dl_per_min`) | 0,009 g/dL/min (`family_engine.py:2170`) | caída de Hb por minuto sin tratar | Hb de llegada 6,7 y 6,4; ninguna tasa | la Hb sigue la aritmética del motor que ve el residente (A9: coincidencia exacta) | debe seguir coherente con `volume_loss_ml_per_min` | SAFE_FAMILY_DEFAULT_CANDIDATE, si se mantiene coherente con la tasa de volumen |
| `fraction_with_ppi` (`gi_fraction_with_ppi`) | 0,8 (`family_engine.py:202`) | fracción del sangrado que sigue con IBP | ninguna: es una respuesta al tratamiento, no un dato del caso | igual en todos los casos GI | sin base en la verdad del caso | SAFE_FAMILY_DEFAULT_CANDIDATE |
| `fraction_after_hemostasis` (`gi_fraction_after_hemostasis`) | 0,1 (`family_engine.py:201`) | sangrado residual tras la hemostasia endoscópica | ninguna, por la misma razón | igual en todos los casos GI | sin base en la verdad del caso | SAFE_FAMILY_DEFAULT_CANDIDATE |

## 9. PL2 (P2G-9)

**Regla congelada (§12.6).** «Una bomba deprimida limita el rescate con volumen» (P2D-5). Se prueba en la llegada
neutra de las sondas, a la posición por defecto del perfil:
- **cláusula 1:** con P 0,6, 500 mL no ganan más gasto que con P 1;
- **cláusula 2:** con P 0,6, 500 mL no devuelven el gasto de llegada (el gasto queda < 1).

**Razón fisiológica.** La cláusula 1 es Frank–Starling con una curva más plana. La cláusula 2 supone que el gasto de
llegada es el normal.

**Qué rechaza.**
- En P2F: 18 conjuntos, todos con la posición 0,3 y escala de 600 u 833 mL.
- Todos los rechazos son por la cláusula 2. La cláusula 1 se cumple en todo el rango probado.
- Por encima y por debajo del borde (tabla), la cláusula 2 falla con posiciones bajas, escalas cortas y poco
  acoplamiento: la curva es empinada y el volumen sí rescata.

**¿Vale en un paciente dependiente de precarga?**
- La regla nunca prueba las llegadas GI: su posición (0,2–0,6) es la del caso, no la del perfil.
- Una llegada GI con precarga baja es justamente el caso en que una bomba moderadamente deprimida puede recuperar con
  volumen el gasto (bajo) de llegada.

**Opciones** (no se elige ninguna):

| Opción | Consecuencia |
|---|---|
| `KEEP_PL2` | sigue rechazando las curvas empinadas; las bandas de escala quedan acotadas por una regla que no describe la dependencia de precarga |
| `REVISE_PL2` | por ejemplo, conservar sólo la cláusula 1, medir la cláusula 2 frente a una referencia previa al shock, o aplicarla sólo cerca de la meseta; requiere reescribir la regla y volver a congelar |
| `REMOVE_PL2` | la limitación por la bomba queda sólo en la forma de la curva (escala × P^c); PL3 sigue cubriendo la bomba muy deprimida |

<!-- generado:pl2 -->
| Posición | Escala (mL) | Acoplamiento | Ganancia bomba normal | Ganancia bomba 0,6 | Gasto bomba 0,6 tras 500 mL | Cláusula 1 | Cláusula 2 | Punto del registro |
|---|---|---|---|---|---|---|---|---|
| 0,30 | 600 | 0,0 | 1,319 | 0,792 | 1,392 | sí | no | sí |
| 0,30 | 600 | 1,0 | 1,319 | 0,555 | 1,155 | sí | no | sí |
| 0,30 | 700 | 0,0 | 1,191 | 0,715 | 1,315 | sí | no | no |
| 0,30 | 700 | 1,0 | 1,191 | 0,514 | 1,114 | sí | no | no |
| 0,30 | 833 | 0,0 | 1,053 | 0,632 | 1,232 | sí | no | sí |
| 0,30 | 833 | 1,0 | 1,053 | 0,467 | 1,067 | sí | no | sí |
| 0,30 | 1000 | 0,0 | 0,918 | 0,551 | 1,151 | sí | no | no |
| 0,30 | 1000 | 1,0 | 0,918 | 0,418 | 1,018 | sí | no | no |
| 0,30 | 1200 | 0,0 | 0,795 | 0,477 | 1,077 | sí | no | no |
| 0,30 | 1200 | 1,0 | 0,795 | 0,370 | 0,970 | sí | sí | no |
| 0,30 | 1500 | 0,0 | 0,661 | 0,397 | 0,997 | sí | sí | sí |
| 0,30 | 1500 | 1,0 | 0,661 | 0,315 | 0,915 | sí | sí | sí |
| 0,35 | 600 | 0,0 | 1,050 | 0,630 | 1,230 | sí | no | no |
| 0,35 | 600 | 1,0 | 1,050 | 0,429 | 1,029 | sí | no | no |
| 0,35 | 700 | 0,0 | 0,948 | 0,569 | 1,169 | sí | no | no |
| 0,35 | 700 | 1,0 | 0,948 | 0,398 | 0,998 | sí | sí | no |
| 0,35 | 833 | 0,0 | 0,838 | 0,503 | 1,103 | sí | no | no |
| 0,35 | 833 | 1,0 | 0,838 | 0,361 | 0,961 | sí | sí | no |
| 0,35 | 1000 | 0,0 | 0,731 | 0,438 | 1,038 | sí | no | no |
| 0,35 | 1000 | 1,0 | 0,731 | 0,323 | 0,923 | sí | sí | no |
| 0,35 | 1200 | 0,0 | 0,633 | 0,380 | 0,980 | sí | sí | no |
| 0,35 | 1200 | 1,0 | 0,633 | 0,286 | 0,886 | sí | sí | no |
| 0,35 | 1500 | 0,0 | 0,526 | 0,316 | 0,916 | sí | sí | no |
| 0,35 | 1500 | 1,0 | 0,526 | 0,244 | 0,844 | sí | sí | no |
| 0,40 | 600 | 0,0 | 0,848 | 0,509 | 1,109 | sí | no | no |
| 0,40 | 600 | 1,0 | 0,848 | 0,335 | 0,935 | sí | sí | no |
| 0,40 | 700 | 0,0 | 0,766 | 0,459 | 1,059 | sí | no | no |
| 0,40 | 700 | 1,0 | 0,766 | 0,311 | 0,911 | sí | sí | no |
| 0,40 | 833 | 0,0 | 0,677 | 0,406 | 1,006 | sí | no | no |
| 0,40 | 833 | 1,0 | 0,677 | 0,282 | 0,882 | sí | sí | no |
| 0,40 | 1000 | 0,0 | 0,590 | 0,354 | 0,954 | sí | sí | no |
| 0,40 | 1000 | 1,0 | 0,590 | 0,253 | 0,853 | sí | sí | no |
| 0,40 | 1200 | 0,0 | 0,511 | 0,307 | 0,907 | sí | sí | no |
| 0,40 | 1200 | 1,0 | 0,511 | 0,224 | 0,824 | sí | sí | no |
| 0,40 | 1500 | 0,0 | 0,425 | 0,255 | 0,855 | sí | sí | no |
| 0,40 | 1500 | 1,0 | 0,425 | 0,190 | 0,790 | sí | sí | no |
<!-- /generado:pl2 -->

## 10. Alcanzabilidad de la D de llegada (P2G-10)

**Qué significa.** En el modelo, dD/dt = g × max(0, demanda − entrega) − D / τ_D.
- **Sobre la cota g × demanda × τ_D, D baja sea cual sea la entrega**, incluso sin entrega.
- **Debajo de la cota**, un déficit sostenido puede llevarla hasta ella.
- Una D de llegada sobre la cota es, por eso, un estado que este modelo no habría podido producir.

**Supuestos para que valga.**
- El modelo rige antes de la llegada.
- La demanda previa no pasó de 1: no hubo fiebre, agitación ni otro multiplicador antes.
- g y τ_D fueron constantes.
- El repago es de primer orden y no depende de la entrega.

**Por qué una llegada real no necesita estar en estado estacionario.** La llegada se declara: es un estado de un
paciente con una historia previa desconocida. No se reconstruye esa historia (P2F).

**¿Condición física o propiedad del modelo?** Es una propiedad del modelo. El término −D / τ_D repaga la deuda
incluso sin entrega. En la fisiología, la deuda no se repaga sin un exceso de entrega, así que una deuda mayor no es
imposible en un paciente real.

**Qué excluiría.** En el diseño GI de P2F, los 162 conjuntos que HR1 ya rechazó. Con g 0,5 excluiría más (tabla).

**Opciones** (no se elige ninguna):

| Opción | Consecuencia |
|---|---|
| `NO_REACHABILITY_RULE` | se aceptan llegadas que el modelo no habría producido; en ellas la deuda se repaga durante el sangrado y la FC baja (HR1 las sigue rechazando) |
| `MODEL_REACHABILITY_RULE` | se excluyen de antemano por consistencia con la dinámica del modelo; acopla la banda de D de llegada a τ_D y g |
| `REVISE_FORMULATION` | por ejemplo, un repago que dependa del exceso de entrega; desaparece la cota, pero cambia la dinámica de D y exige reabrir las reglas y los barridos |

<!-- generado:alcanzabilidad -->
| τ_D (min) | g | Cota g × 1 × τ_D | Niveles de D de llegada (0 / 20 / 60) excluidos |
|---|---|---|---|
| 30 | 0,5 | 15 | medio, sup. |
| 30 | 1,0 | 30 | sup. |
| 30 | 2,0 | 60 | ninguno |
| 60 | 0,5 | 30 | sup. |
| 60 | 1,0 | 60 | ninguno |
| 60 | 2,0 | 120 | ninguno |
| 120 | 0,5 | 60 | ninguno |
| 120 | 1,0 | 120 | ninguno |
| 120 | 2,0 | 240 | ninguno |

En el diseño GI de P2F (g = 1) la cota excluiría 162 conjuntos; todos son los que P2F ya rechazó por HR1.
<!-- /generado:alcanzabilidad -->

## 11. El borde de precarga 0,2 en 57m (P2G-11)

El conjunto de P2F con la posición de precarga en su límite inferior (0,2) en 57m se detuvo en el minuto 24 de la sonda
HR1 (8 mL/min).

**Lo que muestra la tabla.**
- A 0,2 con escala de 833 mL, la llegada está 186 mL-eq sobre el punto vacío de la curva.
- Con la sonda de 8 mL/min se vacía en el minuto 24. Con 4 mL/min, no se vacía en 30 min.
- **El propio sangrado del caso (2,5 mL/min) la vacía en el minuto 75.** Un 57m a 0,2 sin tratar también se detiene,
  con el colapso apagado.
- Con escala de 1500 mL no se vacía en ninguna de las tres.

**Qué causa la falla.**
- **A. ¿Estado de llegada fisiológicamente imposible?** No: un VI casi obliterado con contracción hiperdinámica es lo
  que describe el POCUS de 57m (`clinical_cases.py:154`).
- **B. ¿Sonda demasiado agresiva?** En parte: 8 mL/min es tres veces el sangrado del caso, pero el sangrado del caso
  también llega al vacío.
- **C. ¿Formulación de la curva?** En parte: la curva tiene un punto vacío a volumen finito (posición 0 con
  llenado 0), y sin una regla de colapso no hay transición terminal, así que la corrida se detiene.
- **D. ¿Interacción?** La evidencia apunta a D: una llegada baja, una curva con vacío finito, el colapso apagado y la
  tasa de pérdida.

**Pregunta para la docencia:** ¿0,2 es una posición de llegada permitida para 57m, dado su POCUS? Y, si lo es, ¿qué
debe pasar cuando el ventrículo se vacía?
- encender el colapso (decisión 4);
- una curva asintótica;
- subir el límite inferior;
- una sonda a la tasa del caso.

No se quita el conjunto ni se cambia la prueba.

<!-- generado:precarga_02 -->
| Posición | Escala (mL) | Llenado sobre el vacío (mL-eq) | Sonda HR1 8 mL/min: vacío en | Sonda 4 mL/min | Sangrado del caso 2,5 mL/min |
|---|---|---|---|---|---|
| 0,18 | 600 | 119 | 15 | 30 | 48 |
| 0,18 | 833 | 165 | 21 | no | 67 |
| 0,18 | 1500 | 298 | no | no | 120 |
| 0,20 | 600 | 134 | 17 | no | 54 |
| 0,20 | 833 | 186 | 24 | no | 75 |
| 0,20 | 1500 | 335 | no | no | no (120 min) |
| 0,22 | 600 | 149 | 19 | no | 60 |
| 0,22 | 833 | 207 | 26 | no | 83 |
| 0,22 | 1500 | 373 | no | no | no (120 min) |
| 0,25 | 600 | 173 | 22 | no | 70 |
| 0,25 | 833 | 240 | 30 | no | 96 |
| 0,25 | 1500 | 432 | no | no | no (120 min) |
| 0,30 | 600 | 214 | 27 | no | 86 |
| 0,30 | 833 | 297 | no | no | 119 |
| 0,30 | 1500 | 535 | no | no | no (120 min) |
| 0,35 | 600 | 258 | no | no | 104 |
| 0,35 | 833 | 359 | no | no | no (120 min) |
| 0,35 | 1500 | 646 | no | no | no (120 min) |
<!-- /generado:precarga_02 -->

## 12. Hoja de trabajo A9 (P2G-12)

Las 19 variables del marco A9 (`clinical_core/a9.py`). Ninguna tolerancia numérica está fijada: «X» y «N» las fija la
docencia.

| Grupo | Variable | Visible | Tipo de comparación | Tipo de tolerancia candidata | Ejemplo de equivalencia clínica | Decisión |
|---|---|---|---|---|---|---|
| A | `pulse_arrest_state` | sí | coincidencia exacta | ninguna | pulso presente en los mismos minutos y la misma categoría de ritmo | PENDIENTE |
| A | `event_timing` | sí | momento exacto | ninguna (mismo minuto) | la endoscopia, la transfusión completa o el paro, en el mismo minuto | PENDIENTE |
| A | `hb` | sí | coincidencia exacta | ninguna | la misma Hb que el motor en cada minuto (aritmética adoptada) | PENDIENTE |
| B | `sbp` | sí | diferencia absoluta acotada; categoría | ± X mmHg y mismo lado de 90/80/65 | ambas bajo 90 en los mismos minutos y la diferencia dentro de X | PENDIENTE |
| B | `dbp` | sí | diferencia absoluta acotada | ± X mmHg | la diferencia dentro de X en todo el recorrido | PENDIENTE |
| B | `map` | sí | diferencia absoluta acotada; categoría | ± X mmHg y mismo lado de 65 | ambas cruzan 65 en el mismo sentido | PENDIENTE |
| B | `hr` | sí | diferencia absoluta acotada; tendencia | ± X lpm y misma dirección por ventana | ambas bajan tras la hemostasia y la diferencia queda dentro de X | PENDIENTE |
| B | `respiratory_rate` | sí | diferencia absoluta acotada; categoría | ± X resp/min y misma categoría (< 10, taquipnea marcada) | ninguna cruza a bradipnea si la otra no lo hace | PENDIENTE |
| B | `spo2` | sí | diferencia absoluta acotada; categoría | ± X % y mismo lado de 94/87/80 | las dos sobre 94 o las dos bajo 94 | PENDIENTE |
| B | `crt_s` | sí | diferencia absoluta acotada; categoría | ± X s y mismo lado de 3 s | relleno retardado en los mismos minutos | PENDIENTE |
| B | `lactate` | sí | diferencia relativa acotada; tendencia | ± X % y misma dirección del aclaramiento | ambos bajan tras la reanimación y la diferencia relativa queda dentro de X | PENDIENTE |
| C | `consciousness_level` | sí | categoría clínica | el mismo nivel, o un desfase de N min en las transiciones | el mismo nivel de la escala 0–3 minuto a minuto | PENDIENTE |
| D | `V` | no | divergencia estructural aprobada; exacta dentro de la pinza | ninguna dentro de la pinza; divergencia aceptada fuera | igual al volumen del motor mientras éste no toca su pinza | PENDIENTE |
| D | `D` | no | tendencia | signo y dirección | monótona en el déficit, repago gradual, nunca negativa | PENDIENTE |
| D | `L` | no | tendencia | signo y dirección | aparece con exceso de precarga y reserva limitada, y se aclara lentamente | PENDIENTE |
| D | `effective_output` | no | tendencia | dirección | sube y baja cuando sube y baja la circulación del motor | PENDIENTE |
| D | `oxygen_demand` | no | coincidencia exacta | ninguna (contabilidad) | basal declarada × modificadores | PENDIENTE |
| D | `sympathetic_drive` | no | tendencia | signo y dirección | sube con los estímulos declarados, decae con su memoria, nunca negativo | PENDIENTE |
| D | `collapse_burden` | no | tendencia; momento exacto | dirección; la transición, en el mismo minuto | se acumula con severidad × duración | PENDIENTE |

**Grupos:**
- **A:** invariantes exactos de seguridad y semántica.
- **B:** observables continuos visibles para el residente.
- **C:** observables categóricos visibles.
- **D:** estado oculto o interno.

Las categorías de los observables de B (umbrales de PAS, SpO2 y TLC) son las que ya usa el motor. No son
tolerancias.

## 13. Tabla maestra de decisiones (P2G-13)

Todas las decisiones necesarias antes de declarar calibrado el GI. «Selección docente» queda en blanco; el estado
es ABIERTA mientras la docencia no decida. Las consecuencias citan las tablas de este documento (evidencia sólo del
modelo); la evidencia del repositorio es lo que dicen los casos.

| ID | Decisión | Opciones o rango candidato | Afecta | Si se elige bajo | Si se elige alto | Evidencia del repositorio | Evidencia sólo del modelo | Selección docente | Estado |
|---|---|---|---|---|---|---|---|---|---|
| FD-01 | Subida del lactato en 1 h sin tratar | `arrival_oxygen_debt` 0–20–60; `arrival_lactate_excess` (banda por caso); `lactate_per_output_deficit` 2–6–12; `lactate_clearance_tau_min` 45–120–240 | lactato visible; FR; impulso | el lactato baja en 1 h aunque siga el sangrado | sube hasta ~9,6 (57m) | lactato 4,4 / 3,4 (`clinical_cases.py:900`, `:929`); ninguna duración | §2 | | ABIERTA |
| FD-02 | Rapidez del descenso tras el control | `lactate_clearance_tau_min`; `debt_clearance_tau_min` 30–60–120 | lactato tras el manejo; FR | descenso rápido; vuelve cerca de la basal en 2 h | descenso lento; sigue elevado a las 2 h | ninguna | §2 (manejo definitivo) | | ABIERTA |
| FD-03 | ¿Vuelta a la basal en el horizonte o lactato persistente por la deuda? | basal 0,8–2,0 (implícita en `arrival_lactate_excess`); τ_L | lactato final | basal alta: el lactato no baja de ~2 | basal baja: puede bajar a ~1 | la basal no figura en el caso | §2 | | ABIERTA |
| FD-04 | Rango de FC tras hemostasia y reanimación | `sympathetic_per_pressure_deficit` 0,5–1–2; `sympathetic_per_debt`; intrínseca | FC visible | ganancia baja: FC alta tras la hemostasia (110) | ganancia alta: FC cerca de la intrínseca (81) | FC 124 / 112 (`:881`, `:910`) | §3 | | ABIERTA |
| FD-05 | Cuánto puede bajar la FC bajo la taquicardia de llegada | `intrinsic_sinus_rate` 60–80–100 (piso) | FC en la recuperación | piso bajo: puede bajar mucho | piso alto: la FC no baja de la intrínseca | ninguna FC basal autorizada | §3 (la intrínseca fija sólo el piso) | | ABIERTA |
| FD-06 | Rapidez de la resolución de la taquicardia | `sympathetic_decay_tau_min` 2–5–15; ganancias | curso de la FC | τ 2: la FC recorre la mitad de su caída en 28–29 min | τ 15: en 41 min; con intrínseca 100 en 72f, 21 y 33 min (la «mitad simpática» depende además de la intrínseca: §3) | ninguna | §3 (resolución por τ e intrínseca) | | ABIERTA |
| FD-07 | ¿Intrínseca por caso o valor por defecto de familia? | por caso / familia GI | `intrinsic_sinus_rate` | — | — | ninguna FC basal ni betabloqueador autorizado | §3 | | ABIERTA |
| FD-08 | Caída de la PA en 1 h sin tratamiento | `volume_loss_ml_per_min`; `preload_fraction`; `preload_curve_scale_ml` 600–833–1500; `sbp_per_pressure_deficit` 35–45–55 | PAS/PAM; conciencia; logística | PAS 80 a los 60 min (57m) | PAS 26–62 a los 60 min o detención | PAS 88 / 98; POCUS (`:154-156`) | §4 | | ABIERTA |
| FD-09 | Umbral de flujo bajo para el colapso | `collapse_output_threshold` 0,2–0,3–0,4 | paro | sólo el flujo muy bajo acumula | el flujo moderado ya acumula | ninguna | §5 | | ABIERTA |
| FD-10 | Permanencia antes de la AESP o la asistolia | `collapse_burden_per_minute` 0,5–1–2; `collapse_burden_limit` 5–15–30 | paro | paro en minutos | paro en horas | ninguna | §5 (minutos exactos) | | ABIERTA |
| FD-11 | Repago de la carga de colapso | `collapse_repayment_tau_min` 30–60–240 o sin repago | episodios repetidos | el segundo episodio no para | el segundo episodio para | ninguna | §5 | | ABIERTA |
| FD-12 | Política del ritmo terminal | `collapse_terminal_rhythm`: según la causa o el estado / declarada (`pea`, `asystole`) | ritmo del paro | — | — | ninguna | §5 | | ABIERTA |
| FD-13 | ¿Encender el colapso en las corridas GI? | apagado (hoy) / encendido con FD-09–FD-11 | final de la hemorragia sin tratar | detención en vez de paro | paro con la regla elegida | ninguna | §5, §11 | | ABIERTA |
| FD-14 | Subida máxima de la PA con volumen solo | `preload_curve_scale_ml`; `preload_fraction`; ¿techo de presión? | PAS/PAM con volumen | en el diseño de P2F, PAS pico 122 (57m) y 121 (72f); fuera de él, 113 | en el diseño, 151 y 140; fuera de él, 186 (243 rechazado); no hay techo | ninguna | §6 | | ABIERTA |
| FD-15 | Desde dónde el líquido se vuelve ineficaz | `preload_curve_scale_ml` | respuesta al volumen | escala corta: ineficaz pronto (0,16) | escala larga: sigue respondiendo (0,48) | ninguna | §6 | | ABIERTA |
| FD-16 | Congestión tolerada | `congestion_preload_knee` 0,75–0,85–0,92; `congestion_per_excess_preload` 0,02–0,05–0,1; `lung_water_clearance_tau_min`; `pump_reserve` | L (aún sin SpO2) | sin congestión | L hasta ~1,3 con reserva 0,7 | sin edema ni líneas B en la llegada | §6 | | ABIERTA |
| FD-17 | Rango plausible de FR en el shock GI no complicado | sigue al lactato (FD-01–FD-03) | FR visible | 13–15 | 36–38 | FR 26 / 24 (`:881`, `:910`) | §7 | | ABIERTA |
| FD-18 | Taquipnea metabólica máxima | `rr_metabolic_max` 15–25–30; `rr_per_lactate` 3–7,5–12; `lactate_drive_threshold_mmol_l` 1,5–2–2,5 | techo de la FR | máximo 15: techo teórico 27,5–36,3 (57m) y 27,3–36,5 (72f) | máximo 30: 35,4–50,8 (57m) y 38,0–51,4 (72f), recortado a 40 si `rr_max` es 40 | gasometría (`:901`, `:930`) | §7 (cotas del modelo) | | ABIERTA |
| FD-19 | Límite inferior de la FR en la recuperación | `rr_ventilatory_floor` 10–12–14 y `rr_per_lactate`, `lactate_drive_threshold_mmol_l`, `rr_metabolic_max` (que reparten la FR de llegada) | piso de la FR | piso 10–13 (reparto metabólico grande) | piso hasta 21,3 (57m) y 21,5 (72f) (reparto metabólico pequeño) | ninguna | §7 (cotas del modelo) | | ABIERTA |
| FD-20 | `beta_blockade` | convención «no listado ⇒ 0» / declarado por caso | FC | — | — | medicación sin betabloqueador listado (`:889`, `:918`) | §8 | | ABIERTA |
| FD-21 | `pump_reserve` | 1,0 de familia sin hallazgos / por caso | congestión | reserva 0,7: congestión con volumen | 1,0: sin congestión | §8 | §6 | | ABIERTA |
| FD-22 | `volume_loss_ml_per_min` (`gi_volume_loss_ml_per_min`) | 2,5 de familia / por caso / otra tasa | caída de la PA, lactato, FC | × 0,5: PAS 80 a los 60 min | × 2: PAS 26 a los 60 min | ninguna tasa (`:890`, `:921`) | §4, §8 | | ABIERTA |
| FD-23 | `hb_loss_g_dl_per_min` (`gi_hb_loss_g_dl_per_min`) | 0,009 de familia / coherente con FD-22 | Hb | — | — | Hb 6,7 / 6,4 | §8 | | ABIERTA |
| FD-24 | `fraction_with_ppi` (`gi_fraction_with_ppi`) | 0,8 de familia / otro | sangrado con IBP | — | — | ninguna | §8 | | ABIERTA |
| FD-25 | `fraction_after_hemostasis` (`gi_fraction_after_hemostasis`) | 0,1 de familia / otro | sangrado tras la hemostasia | — | — | ninguna | §8 | | ABIERTA |
| FD-26 | PL2 | `KEEP_PL2` / `REVISE_PL2` / `REMOVE_PL2` | bandas de escala de precarga | — | — | ninguna | §9 | | ABIERTA |
| FD-27 | Alcanzabilidad de la D de llegada | `NO_REACHABILITY_RULE` / `MODEL_REACHABILITY_RULE` / `REVISE_FORMULATION` | banda de `arrival_oxygen_debt` | — | — | ninguna duración | §10 | | ABIERTA |
| FD-28 | Precarga 0,2 en 57m | permitida / límite inferior mayor / curva asintótica / sonda a la tasa del caso | `preload_fraction` de 57m | — | — | POCUS (`:154`) | §11 | | ABIERTA |
| FD-29 | `arrival_oxygen_debt` por caso | banda 0–20–60 | D, lactato, FC | — | — | ninguna duración | §2, §10 | | ABIERTA |
| FD-30 | `arrival_lactate_excess` por caso | 57m 2,4–3,4–3,6; 72f 1,4–2,4–2,6 | lactato, FR | — | — | lactato de llegada | §2 | | ABIERTA |
| FD-31 | `arrival_delivery_ratio` por caso | 0,6–0,85–1,0 | D, lactato | — | — | TLC, perfusión, Hb (`:881-882`, `:900`) | §2, §7 | | ABIERTA |
| FD-32 | `intrinsic_sinus_rate` por caso | 60–80–100 | FC | — | — | ninguna FC basal | §3 | | ABIERTA |
| FD-33 | `preload_fraction` por caso | 57m 0,2–0,35–0,5; 72f 0,3–0,45–0,6 | PA, gasto, volumen | — | — | POCUS (`:154-156`) | §4, §6 | | ABIERTA |
| FD-34 | `metabolic_demand_baseline` | 1 (ningún modificador respaldado) / valor de familia | D | — | — | afebril, alerta, dolor leve | P2F §12.3 | | ABIERTA |
| FD-35 | `crt_per_output_deficit_s` | 3–4–5 | TLC visible | TLC responde poco al gasto | TLC responde mucho | TLC 5 / 4 | P2F §12.5 | | ABIERTA |
| FD-36 | `spo2_per_fio2` | 20–30–40 | SpO2 con oxígeno | — | — | SpO2 97 / 96 en aire ambiente | P2F §12.4 | | ABIERTA |
| FD-37 | Tolerancias A9, grupo A (invariantes exactos) | confirmar «sin tolerancia» | pulso y paro, eventos, Hb | — | — | — | §12 | | ABIERTA |
| FD-38 | Tolerancias A9, grupo B (continuos visibles) | X por variable | PAS, PAD, PAM, FC, FR, SpO2, TLC, lactato | — | — | — | §12 | | ABIERTA |
| FD-39 | Tolerancias A9, grupo C (categóricos visibles) | mismo nivel / desfase N | conciencia | — | — | — | §12 | | ABIERTA |
| FD-40 | Criterios A9, grupo D (estado interno) | signo y dirección | V, D, L, gasto, demanda, impulso, carga | — | — | — | §12 | | ABIERTA |
| FD-41 | Ganancia del déficit de entrega en la deuda | `debt_per_delivery_deficit` 0,5–1–2 | D, lactato, impulso; cota de alcanzabilidad (§10) | la D crece despacio con el déficit; cota g × τ_D de 15 a 60 | la D crece rápido; cota de 60 a 240 | ninguna | §10 (no se varió en el diseño de P2F: g = 1) | | ABIERTA |
| FD-42 | Rodilla de presión con gasto bajo | `low_output_pressure_knee` 0,3–0,5–0,6 | PAS/PAM bajo la rodilla | 0,3: PAS 37 a los 120 min sin tratamiento (57m) | 0,6: PAS 23 | ninguna | §4 | | ABIERTA |
| FD-43 | Ganancia de PAD por déficit de presión | `dbp_per_pressure_deficit` 15–25–30 | PAD y PAM | 15: PAM 58 a los 120 min (72f) | 30: PAM 53 | PA de llegada 88/54, 98/62 (`:881`, `:910`) | §4 | | ABIERTA |
| FD-44 | Acoplamiento bomba/precarga | `pump_preload_coupling` 0–0,5–1 | gasto con bomba deprimida | sin efecto en las corridas GI (la bomba no se mueve) | sin efecto en GI; PL2 lo lee (§9) | ninguna | §4, §9 | | ABIERTA |
| FD-45 | Sensibilidad a la poscarga | `afterload_sensitivity` 0,1–0,3–0,5 | gasto con cambios de tono | sin efecto en las corridas GI (el tono no se mueve) | sin efecto en GI | ninguna | §4 | | ABIERTA |
| FD-46 | Posición de precarga de las sondas neutras | `arrival_preload_fraction` 0,3–0,5–0,7 | reglas congeladas que leen la llegada neutra (PL2) | 0,3: PL2 falla su cláusula 2 con escala 600 u 833 (§9) | 0,5 y 0,7: PL2 se cumple | ninguna (no es un dato de caso) | §9 | | ABIERTA |
| FD-47 | Lpm por unidad de impulso simpático | `hr_per_sympathetic_drive` 25 (banda de un punto: el literal del motor, adoptado en P2C) | escala de la parte simpática de la FC | — | — | literal del motor de familias | §3 | | ABIERTA |
| FD-48 | Tope de seguridad de la FR | `rr_max` 40–60 | techo de la FR | 40: recorta el techo teórico cuando `rr_metabolic_max` ≥ 25 | 60: no recorta ningún punto de la cuadrícula | ninguna (no es fisiología) | §7 | | ABIERTA |
| FD-49 | Verificación de la procedencia en la puerta de migración | confiar en la fuente declarada (hoy: reetiquetar todo como `explicit_case`, también los parámetros de familia, pasa la puerta) / verificar `explicit_case` contra la verdad del caso (`gi_reference`) / exigir un registro docente por valor | puerta de migración (no los números) | — | — | — | §14 (límite de la puerta) | | ABIERTA |

**Decisiones abiertas: 49.**

**Parámetros del registro fuera de esta tabla, con el motivo.** Cada nombre del registro está en la tabla o aquí; una
prueba lo comprueba.
- `arrival_sympathetic_drive`: no es libre; es la FC de llegada menos la intrínseca, sobre la ganancia (FD-05, FD-32,
  FD-47).
- `reference_preload_fraction`: referencia euvolémica sólo diagnóstica; ninguna regla ni corrida la lee.
- `sympathetic_per_hypoxaemia_point`, `hypoxaemia_threshold_spo2`: ninguna llegada GI está hipoxémica (SpO2 97 y 96).
- `sympathetic_per_hypoglycaemia_mg_dl`, `hypoglycaemia_threshold_mg_dl`: ninguna llegada GI está hipoglucémica
  (118 y 130 mg/dL).
- `sepsis_demand_multiplier`, `fever_demand_multiplier`, `seizure_demand_multiplier`,
  `agitation_pain_demand_multiplier`: DEFAULT_UNMAPPED, sin módulo ni evidencia GI; la demanda GI es FD-34.
- `collapse_rule_test_values`, `vasodilation_with_demand_probe_factor`: SYNTHETIC_ONLY, valores de prueba y de sonda;
  nunca valores de caso.

## 14. Puerta de migración (P2G-14)

- **Ensayo en seco:** `migration.gate_dry_run` se repitió al cierre de P2G, tras las correcciones de la segunda
  revisión. Los dos casos GI siguen fallando, cada uno
  con 12 bloqueos:
  - los 6 parámetros de caso que requieren decisión docente;
  - `beta_blockade` y `pump_reserve`;
  - los 4 de la fuente hemorrágica.
- **Ningún valor aprobado:**
  - FACULTY_APPROVED: 0 entradas en el registro;
  - `APPROVED_FAMILY_DEFAULTS` está vacío.
- **Lo que las pruebas comprueban** (`test_clinical_core_decision_pack.py`):
  - declarar todos los candidatos como `synthetic_probe` no pasa la puerta;
  - reclamar el punto medio de una banda CANDIDATE como `approved_family_default` tampoco, porque no hay ninguno
    registrado;
  - usar «CANDIDATE» como fuente de procedencia se rechaza;
  - ningún módulo del núcleo en sombra, salvo el vocabulario de la puerta (`state.py`, `derived.py`, `migration.py`),
    escribe `explicit_case` ni `approved_family_default`: nada del núcleo etiqueta un CANDIDATE como verdad del caso.
- **Límite de la puerta (anterior a P2G):** la puerta confía en la fuente declarada y no compara el valor con la
  verdad del caso. Un llamador fuera del núcleo que declare los valores CANDIDATE como `explicit_case` (los
  parámetros de caso y también los 4 de la fuente hemorrágica, que así no pasan por `APPROVED_FAMILY_DEFAULTS`) haría
  pasar la puerta completa: una sonda lo comprobó en 57m. La prueba de que reclamar `approved_family_default` no
  pasa no cubre ese camino. Ninguna ruta de código actual lo hace, y cambiar la puerta es una decisión de
  arquitectura: queda como FD-49, sin implementar.
- **El GI no se declara migrado** ni calibrado.
