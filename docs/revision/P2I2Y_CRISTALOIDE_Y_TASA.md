# P2I-2Y · Superficie de calibración del cristaloide y robustez de la tasa de sangrado

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución, no migra GI ni otra familia, no refiltra el lactato (P2I-2R sigue en pausa);
- no calibra la presión ni la FC, ni activa el colapso;
- no se ajusta al motor heredado y no elige ningún conjunto final de parámetros ocultos;
- no cambia ninguna restricción docente: usa exactamente las de P2I-2V-R.

Código: `clinical_core/blood_fluid_calibration.py` (diseños, grilla, reglas, política y evaluación; congelado antes de
evaluar) y `clinical_core/blood_fluid_report.py` (sólo este informe). Números:
`docs/revision/P2I2Y_blood_fluid_calibration.json`. Registros de partida, cerrados: P2I-2V-R (`a9ab10d8…`), P2I-2W
(`5257b233…`) y P2I-2X (`668bad99…`).

## 1. Robustez de la tasa de sangrado frente a la extensión del relleno (P2I-2Y-1)

<!-- generado:tasa -->
Congelamiento de P2I-2Y: `67e5b80a5a96f526fc2f9e5b2c721026f3ac71ba612fe9cb3e06f23106f4a8d4`, comprometido antes de evaluar (una prueba lo fija). Registros: P2I-2V-R `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893`, P2I-2X `668bad9903da9a4ee1d49a5e2be06f7be7795140091b98d898a169b8682c67a5`.

Registro docente de P2I-2X: TESTED_VIABLE_RATE_REGION = {5, 6}; FIRST_TESTED_NONVIABLE_RATE = 7. No es una tasa aprobada.

Diseño: tasas 5, 6, 7; meta del relleno 0,5, 0,75, 1; τ del relleno 120, 240, 480 (9 pares, 5 nuevos); las demás dimensiones con sus valores supervivientes de P2I-2V-R (118098 conjuntos compartidos); posiciones compatibles de cada caso: 57m 0,2, 0,35, 0,5; 72f 0,3, 0,45, 0,6.

| Tasa | Rechazo analítico 57m / 72f | Simulados 57m / 72f | Falla U-OUT 57m / 72f | 57m solo | 72f solo | Sobrevivientes conjuntos | Conjuntos ilegibles |
|---|---|---|---|---|---|---|---|
| 5 | 338256 / 337770 | 16038 / 16524 | 11664 / 12393 | 3531 | 3591 | 3423 | 0 |
| 6 | 338256 / 337770 | 16038 / 16524 | 13122 / 12393 | 2340 | 3603 | 2268 | 0 |
| 7 | 338256 / 337770 | 16038 / 16524 | 16038 / 15606 | 0 | 798 | 0 | 0 |

«57m solo» y «72f solo»: cada caso con su propio prefiltro, en cualquiera de sus posiciones compatibles (sensibilidad).

Sobrevivientes conjuntos por par de relleno (meta, τ):

| Meta | τ (min) | Nuevo | Tasa 5 | Tasa 6 | Tasa 7 |
|---|---|---|---|---|---|
| 0,5 | 120 | no | 1134 | 756 | 0 |
| 0,5 | 240 | no | 0 | 0 | 0 |
| 0,5 | 480 | sí | 0 | 0 | 0 |
| 0,75 | 120 | no | 378 | 0 | 0 |
| 0,75 | 240 | no | 756 | 756 | 0 |
| 0,75 | 480 | sí | 0 | 0 | 0 |
| 1 | 120 | sí | 399 | 0 | 0 |
| 1 | 240 | sí | 0 | 0 | 0 |
| 1 | 480 | sí | 756 | 756 | 0 |

Sobrevivientes conjuntos por posición de llegada (cada caso):

| Tasa | 57m 0,2 | 57m 0,35 | 57m 0,5 | 72f 0,3 | 72f 0,45 | 72f 0,6 |
|---|---|---|---|---|---|---|
| 5 | 0 | 0 | 3423 | 0 | 0 | 3423 |
| 6 | 0 | 0 | 2268 | 0 | 0 | 2268 |
| 7 | 0 | 0 | 0 | 0 | 0 | 0 |

**Conclusión: ROBUST_BOUNDARY.**
<!-- /generado:tasa -->

### 1.1 Lectura

- **Pregunta primaria. ¿La tasa 7 se vuelve viable en conjunto en algún lado? No.**
  - Con los 9 pares de relleno, los 5 nuevos incluidos, la tasa 7 deja 0 sobrevivientes conjuntos y 0 conjuntos
    ilegibles.
  - 57m no sobrevive solo en ningún lado: sus 16038 combinaciones simuladas fallan U-OUT.
  - 72f solo sobrevive en 798, pero la tasa es común a los dos casos.
- **Pregunta secundaria. ¿La tasa 6 deja de ser viable en algún lado relevante? No.**
  - Los dos pares que la sostenían en P2I-2X (0,5|120 y 0,75|240) conservan sus 756 sobrevivientes cada uno.
  - Se suma un par nuevo, 1|480, con otros 756: la extensión amplía la tasa 6, no se la quita.
  - Con 6 quedan sin sobrevivientes conjuntos 0,75|120 y 1|120, que sí los tienen con 5.
- **Efecto de la meta 1,0.**
  - Agrega sobrevivientes con 5 (1|120: 399; 1|480: 756) y con 6 (1|480: 756). Con 7 no agrega ninguno.
  - Es un candidato en DOMAIN_UPPER_BOUND, no un valor aprobado; no se exploró por encima de 1.
- **Efecto de τ 480.**
  - Sólo con la meta 1,0 deja sobrevivientes (756 con 5 y 756 con 6). Con las metas 0,5 y 0,75 deja 0, y con la tasa 7
    deja 0 en todos los pares.
  - Con la meta 1,0 y la tasa 5, τ 240 deja 0 mientras que τ 120 y 480 dejan sobrevivientes (399 y 756): ahí el efecto
    de τ no es monótono. Con la tasa 6 es 0, 0 y 756.
  - El registro no desglosa por par qué restricción falla (sólo cuenta U-OUT por caso y tasa), así que este patrón se
    informa sin interpretarlo.
- **Posiciones.** Todos los sobrevivientes conjuntos, con 5 y con 6, están en el borde superior de la banda compatible
  de cada caso (57m 0,5; 72f 0,6), como en P2I-2X.
- **Reproducción de P2I-2X.** En los 4 pares ya certificados, los recuentos son exactamente los de P2I-2X: 2268 con 5,
  1512 con 6 y 0 con 7. La corrida lo comprueba antes de seguir y una prueba lo fija.
- **Qué fija el límite.** Lo fija U-OUT en 57m: con 7 falla en las 16038 combinaciones simuladas. U-OUT lee la corrida
  sin tratamiento, que no lleva bolsa, así que este límite no depende del cristaloide. Los recuentos con 5 y 6 sí leen
  FD-BLD-06 con los valores supervivientes del cristaloide de P2I-2V-R, en la parametrización anterior (§6).
- **Conclusión: ROBUST_BOUNDARY.**
  - El límite entre 6 y 7 resiste la extensión del relleno a la meta 1,0 y τ 480.
  - Es condicional:
    - a las demás dimensiones de sangre en sus valores supervivientes de P2I-2V-R;
    - a las posiciones de la banda compatible de cada caso;
    - a los puntos explorados: no se densificó entre 6 y 7, por decisión docente.
  - Queda el registro docente: TESTED_VIABLE_RATE_REGION = {5, 6}; FIRST_TESTED_NONVIABLE_RATE = 7. Ninguno de los
    dos es una tasa aprobada.

## 2. Cristaloide: superficie F0 / Finf / τ y filtro (P2I-2Y-2 a 5, 9)

### 2.1 Semántica de F0, Finf y τ (P2I-2Y-2)

- **Qué es cada parámetro.**
  - **F0**, la fracción circulante efectiva inicial: la parte de cada mL infundido que entra en el volumen circulante al
    administrarse.
  - **Finf**, la fracción retenida a largo plazo: la parte de cada mL que sigue en la circulación cuando termina la
    redistribución.
  - **τ**, la constante de tiempo (min) con que sale la diferencia F0 − Finf.
- **Mapa exacto a los parámetros existentes** (`bag`):
  - `effective_ml_per_ml = F0`;
  - `transient_share = 1 − Finf / F0`;
  - `leak_tau_min = τ`.

  No cambia `interventions/fluids.py` ni el contribuyente `Crystalloid`. La inversa (`surface`) es
  Finf = F0 × (1 − `transient_share`), y una prueba comprueba la ida y la vuelta.
- **Ecuación** (`Crystalloid.contribute`), por minuto:
  - entra `ganancia = mL administrados × F0`;
  - `transient_share × ganancia` pasa a un compartimento transitorio, que pierde cada minuto la fracción 1 − e^(−1/τ);
  - el resto no sale.

  Para un bolo, la fracción retenida a los t minutos es Finf + (F0 − Finf) · e^(−t/τ), con el desfase de un minuto del
  paso: empieza en F0 y tiende a Finf. Con la infusión de 20 min de las restricciones, la redistribución empieza
  mientras corre la bolsa.
- **Qué leen las restricciones.** Ninguna lee F0 ni Finf solos:
  - FD-BLD-04 lee el máximo retenido en los primeros 30 min, que queda por debajo de F0 cuando hay redistribución (por
    ejemplo, 0,35|0|60 da 0,30);
  - FD-BLD-05 lee lo retenido a los 30, 60 y 120 min. A los 120 min no es Finf, salvo que Finf = F0, porque el
    compartimento transitorio todavía no se vació.
- **Dominio.** 0 < F0 ≤ 1; 0 ≤ Finf ≤ F0; τ > 0.
  - Finf > F0 exigiría una fracción transitoria negativa, es decir, una bolsa que gana volumen después de entrar.
  - `bag` lo rechaza y la grilla lo marca `ANALYTIC_REJECTION` sin simular: son 3 combinaciones, F0 0,15 con Finf
    0,20 y los tres τ.
  - Finf = 0 es el borde del dominio, no un borde abierto de la grilla.
- **Grilla.** Es la docente, congelada antes de evaluar (commit `5ae6d70`); no se agregó ningún valor después.

<!-- generado:cristaloide -->
Grilla de exploración docente (congelada antes de evaluar): F0 0,15 a 0,35; Finf 0 a 0,20; τ 15, 30 y 60 min. 75 combinaciones; 3 con Finf > F0 quedan `ANALYTIC_REJECTION` sin simular; se evalúan 72.

Sondas de sangre de FD-BLD-06 (claves B0, tasa, meta, τ, capacidad de sobrevivientes certificados):

| Sonda | B0 | Tasa | Meta | τ | Capacidad |
|---|---|---|---|---|---|
| borde arrival_circulating_volume_ml max | 5000 | 5 | 0,5 | 120 | 100 |
| borde arrival_circulating_volume_ml min | 3000 | 5 | 0,5 | 120 | 100 |
| borde bleed_ml_per_min max | 3000 | 6 | 0,5 | 120 | 500 |
| borde bleed_ml_per_min min | 3000 | 5 | 0,5 | 120 | 100 |
| borde plasma_refill_capacity_ml max | 3000 | 5 | 0,5 | 120 | 1000 |
| borde plasma_refill_capacity_ml min | 3000 | 5 | 0,5 | 120 | 100 |
| borde plasma_refill_target_share max | 3000 | 5 | 1 | 120 | 100 |
| borde plasma_refill_target_share min | 3000 | 5 | 0,5 | 120 | 100 |
| borde plasma_refill_tau_min max | 3000 | 5 | 1 | 480 | 500 |
| borde plasma_refill_tau_min min | 3000 | 5 | 0,5 | 120 | 100 |
| referencia | 4000 | 2,5 | 0,5 | 120 | 1000 |
| representativo alto | 5000 | 2,5 | 0,75 | 240 | 500 |
| representativo bajo | 3000 | 2,5 | 0,5 | 120 | 100 |
| representativo medio | 4000 | 5 | 0,75 | 240 | 1000 |

| Restricción | Sobrevivientes (de los evaluados) |
|---|---|
| FD-BLD-04 (aporte inicial) | 54 |
| FD-BLD-05 (retenido a 30, 60 y 120 min) | 17 |
| FD-BLD-06, en todas | 13 |
| FD-BLD-06, en la referencia | 45 |
| FD-BLD-06, en alguna sonda | 62 |
| **combinado, primario** (FD-BLD-04, 05 y 06 en alguna sonda) | **17** |
| combinado, robusto (FD-BLD-06 en todas las sondas) | 3 |
| combinado, aislado (FD-BLD-06 en la referencia) | 15 |

Sobrevivientes primarios:

| Punto | Aporte inicial 57m | Retenido 30′ / 60′ / 120′ (57m) | Sondas donde falla FD-BLD-06 |
|---|---|---|---|
| F0 0,15 · Finf 0,15 · τ 15 | 0,15 | 0,15 / 0,15 / 0,15 | BOUNDARY arrival_circulating_volume_ml max, REPRESENTATIVE high |
| F0 0,15 · Finf 0,15 · τ 30 | 0,15 | 0,15 / 0,15 / 0,15 | BOUNDARY arrival_circulating_volume_ml max, REPRESENTATIVE high |
| F0 0,15 · Finf 0,15 · τ 60 | 0,15 | 0,15 / 0,15 / 0,15 | BOUNDARY arrival_circulating_volume_ml max, REPRESENTATIVE high |
| F0 0,2 · Finf 0,05 · τ 60 | 0,18 | 0,16 / 0,11 / 0,07 | ninguna |
| F0 0,2 · Finf 0,1 · τ 30 | 0,17 | 0,15 / 0,12 / 0,10 | ninguna |
| F0 0,2 · Finf 0,1 · τ 60 | 0,18 | 0,17 / 0,14 / 0,12 | ninguna |
| F0 0,25 · Finf 0,05 · τ 60 | 0,22 | 0,19 / 0,14 / 0,08 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,25 · Finf 0,1 · τ 30 | 0,21 | 0,18 / 0,13 / 0,10 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,25 · Finf 0,1 · τ 60 | 0,23 | 0,21 / 0,16 / 0,12 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,3 · Finf 0,05 · τ 60 | 0,26 | 0,23 / 0,16 / 0,09 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,3 · Finf 0,1 · τ 15 | 0,21 | 0,15 / 0,11 / 0,10 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,3 · Finf 0,1 · τ 30 | 0,24 | 0,20 / 0,14 / 0,11 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,3 · Finf 0,1 · τ 60 | 0,27 | 0,24 / 0,19 / 0,13 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,35 · Finf 0 · τ 60 | 0,30 | 0,25 / 0,15 / 0,06 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REFERENCE, REPRESENTATIVE low, REPRESENTATIVE middle |
| F0 0,35 · Finf 0,05 · τ 30 | 0,27 | 0,20 / 0,11 / 0,06 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,35 · Finf 0,1 · τ 15 | 0,23 | 0,17 / 0,11 / 0,10 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REPRESENTATIVE low |
| F0 0,35 · Finf 0,1 · τ 30 | 0,28 | 0,23 / 0,15 / 0,11 | BOUNDARY arrival_circulating_volume_ml min, BOUNDARY bleed_ml_per_min max, BOUNDARY bleed_ml_per_min min, BOUNDARY plasma_refill_capacity_ml max, BOUNDARY plasma_refill_capacity_ml min, BOUNDARY plasma_refill_target_share max, BOUNDARY plasma_refill_target_share min, BOUNDARY plasma_refill_tau_min max, BOUNDARY plasma_refill_tau_min min, REFERENCE, REPRESENTATIVE low, REPRESENTATIVE middle |
<!-- /generado:cristaloide -->

### 2.2 Lectura del filtro

- **FD-BLD-04 (aporte inicial 0,15–0,30): quedan 54 de 72.** Lee sólo la bolsa, y da lo mismo en 57m y en 72f. Fallan
  18 puntos:
  - **por debajo de 0,15, son 13:**
    - F0 0,15 con Finf < 0,15 (9 puntos);
    - 0,2|0|15, 0,2|0|30, 0,2|0,05|15 y 0,25|0|15, que pierden mucho durante la infusión;
  - **por encima de 0,30, son 5:** 0,35|0,05|60, 0,35|0,1|60, 0,35|0,15|60, 0,35|0,2|30 y 0,35|0,2|60, con
    redistribución lenta o mucha retención.
- **FD-BLD-05 (retenido a 30, 60 y 120 min): quedan 17**, todos dentro de los 54 de FD-BLD-04. Elimina 37 de esos 54.
- **FD-BLD-06 (dilución de Hb con 1 y 2 L): entre los 17, el veredicto depende sólo de B0.**
  - Las 14 sondas son 10 claves de sangre distintas: cinco sondas de borde (B0, tasa, meta, τ y capacidad mínimos)
    coinciden en 3000|5|0,5|120|100. B0 5000 y B0 4000 se leen en 2 claves cada uno.
  - En esas claves, las demás varían (tasa 2,5–6, meta 0,5–1, τ 120–480, capacidad 100–1000) sin cambiar ningún
    veredicto de esos 17 puntos.
  - Las diluciones citadas abajo no están en el JSON, que guarda sólo los veredictos: se recalcularon con las funciones
    congeladas.

  Por grupos:
  - **Los 0,15|0,15|\* fallan con B0 5000, por diluir de menos.** En la sonda de borde con B0 máximo, con 1 L, el pico
    es 0,19 en 57m y 0,18 en 72f, bajo el piso de 0,2; con 2 L, 0,38 y 0,36, bajo el piso de 0,4.
  - **Los puntos con F0 ≥ 0,25 fallan con B0 3000, por diluir de más.** Por ejemplo, en la sonda de borde con B0
    mínimo, 0,25|0,05|60 da con 2 L 0,86 en 57m y 0,82 en 72f, sobre el techo de 0,8.
  - **0,35|0|60 y 0,35|0,1|30 fallan además con B0 4000**, en la referencia y en el representativo medio. En la referencia,
    0,35|0|60 da con 2 L 0,86 en 57m y 0,82 en 72f.
  - **Los tres de F0 0,2 pasan con B0 3000, 4000 y 5000.**

  Fuera de los 17, sólo 0,25|0,15|15, que ya falla FD-BLD-05, cambia de veredicto entre sondas con el mismo B0.
- **Diferencias entre casos, entre los 17.** 0,25|0,1|30, 0,3|0,1|15 y 0,35|0,1|30 fallan en 57m y pasan en 72f en
  algunas sondas. Fuera de los 17, 0,2|0,05|15 es más estricto en 72f.
  FD-BLD-06 exige los dos casos en la misma sonda, así que decide el más estricto.
- **Combinados.**
  - **Primario** (FD-BLD-04, 05 y 06 en alguna sonda): 17 puntos.
    - Son 15 bolsas distintas: en los tres 0,15|0,15|\*, Finf = F0, la fracción transitoria es 0 y τ no actúa.
    - Rango: F0 0,15–0,35 (los cinco valores), Finf 0–0,15 y τ 15–60.
  - **Robusto** (FD-BLD-06 en todas las sondas): 3 puntos, 0,2|0,05|60, 0,2|0,1|30 y 0,2|0,1|60.
    - Rango: F0 0,2, Finf 0,05–0,1 y τ 30–60.
  - **Aislado** (FD-BLD-06 en la referencia): 15 puntos, los primarios menos 0,35|0|60 y 0,35|0,1|30.
- **Puntos en el borde de las envolventes.** El bajo, 0,15|0,15|\*, queda en el borde de dos envolventes, sin margen:
  - su aporte inicial, 0,15, es el piso exacto de FD-BLD-04;
  - lo retenido, 0,15 a los 30 y a los 120 min, toca el piso y el techo de FD-BLD-05.

  Las envolventes son inclusivas, así que pasa, pero sin margen.

### 2.3 Por qué no hace falta un producto completo con la sangre (P2I-2Y-9)

- **FD-BLD-04 y 05 no leen el estado de sangre.** Leen la tabla «retained», que sólo depende de la bolsa. Una prueba
  las recalcula en vivo con la bolsa sola.
- **FD-BLD-06 es la única que lee sangre**, y sólo lee B0, la tasa, la meta, τ y la capacidad, no la posición ni lo
  demás.
- **El primario no puede cambiar.** Ya vale lo mismo que FD-BLD-04 ∧ 05 (17): ningún punto que cumple FD-BLD-04 y 05
  falla FD-BLD-06 en todas las sondas. Más estados de sangre sólo pueden sumar sondas donde pasa, y el techo ya es 17.
- **El robusto sólo puede achicarse** si se agregan estados.
- **Verificaciones hechas después del congelamiento, fuera del registro y de la inferencia.** FD-BLD-06 sólo lee esas
  cinco claves, y entre los sobrevivientes conjuntos certificados con tasas 5 y 6 hay 45 claves distintas.
  - **De la sesión, en el scratchpad y no en el repositorio:** el producto exacto con esas 45 claves (17 puntos × 45
    claves × 2 casos: 1530 filas, unos 4 min). Da los mismos 3 robustos y los mismos 17 primarios, con 0 ilegibles y
    el mismo patrón por B0.
  - **En el repositorio:** una prueba (`test_the_robust_crystalloid_set_holds_over_the_certified_blood_keys`) lee
    FD-BLD-06 de los 3 robustos con 81 claves, en los dos casos: las 45 anteriores y las 36 de la región de P2I-2V-R con
    su otra tasa superviviente, 2,5, que incluyen a sus sobrevivientes. Como el robusto sólo puede achicarse, esto basta
    para que no cambie.
  - **Conclusión:** con la región certificada (tasas 2,5, 5 y 6), un producto completo no cambia ni el primario ni el
    robusto, y no hay motivo para parar.

## 3. Identificabilidad y bordes del cristaloide (P2I-2Y-8)

<!-- generado:superficie -->
Clase: la regla congelada (cuántos valores de la grilla sobreviven). Borde: cada lado por separado. «Identificado» sólo si la clase es WELL_CONSTRAINED y los dos lados los acotan las restricciones.

**Conjunto primario.**

| Parámetro | Grilla | Sobreviven | Clase | Lado inferior | Lado superior | Borde | Identificado |
|---|---|---|---|---|---|---|---|
| F0 | 0,15, 0,2, 0,25, 0,3, 0,35 | 0,15, 0,2, 0,25, 0,3, 0,35 | POORLY_IDENTIFIED | abierto (borde de la grilla) | abierto (borde de la grilla) | OPEN_BOTH_GRID_EDGES | no |
| Finf | 0, 0,05, 0,1, 0,15, 0,2 | 0, 0,05, 0,1, 0,15 | PARTIALLY_CONSTRAINED | límite del dominio | acotado por restricción | DOMAIN_LOWER_BOUND | no |
| tau | 15, 30, 60 | 15, 30, 60 | POORLY_IDENTIFIED | abierto (borde de la grilla) | abierto (borde de la grilla) | OPEN_BOTH_GRID_EDGES | no |

**Conjunto robusto.**

| Parámetro | Grilla | Sobreviven | Clase | Lado inferior | Lado superior | Borde | Identificado |
|---|---|---|---|---|---|---|---|
| F0 | 0,15, 0,2, 0,25, 0,3, 0,35 | 0,2 | WELL_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | sí |
| Finf | 0, 0,05, 0,1, 0,15, 0,2 | 0,05, 0,1 | PARTIALLY_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | no |
| tau | 15, 30, 60 | 30, 60 | PARTIALLY_CONSTRAINED | acotado por restricción | abierto (borde de la grilla) | OPEN_UPPER_GRID_EDGE | no |

<!-- /generado:superficie -->

### 3.1 Lectura

- **F0.**
  - **Primario:** sobreviven los cinco valores, incluidos los dos bordes de la grilla. Es POORLY_IDENTIFIED y queda
    abierto a ambos lados.
  - **Robusto:** sólo sobrevive 0,2. Ahí es WELL_CONSTRAINED e INTERIOR, y la regla congelada lo marca «identificado».
  - **Cómo leer esa marca.** Vale sólo para el criterio robusto, es decir, FD-BLD-06 con B0 3000, 4000 y 5000, y con
    la resolución de esta grilla: sus vecinos, 0,15 y 0,25, no pasan. Depende del rango de B0 de la región
    certificada. No es un valor aprobado ni elegido.
- **Finf.**
  - **Primario:** sobreviven 0, 0,05, 0,1 y 0,15. El lado superior lo acota una restricción, porque 0,2 no sobrevive
    nunca. El inferior es DOMAIN_LOWER_BOUND: 0 es el límite del dominio, no un borde de la grilla. No está
    identificado.
    - Finf = 0 sólo sobrevive en 0,35|0|60, que falla FD-BLD-06 con B0 3000 y 4000.
  - **Robusto:** 0,05 y 0,1, interior, PARTIALLY_CONSTRAINED.
- **τ.**
  - **Primario:** sobreviven 15, 30 y 60. Es POORLY_IDENTIFIED y queda abierto a ambos lados.
    - En los tres 0,15|0,15|\*, τ no actúa, porque Finf = F0, así que no informan sobre τ.
    - Sin ellos, el 15 sigue sobreviviendo en 0,3|0,1|15 y 0,35|0,1|15, y el lado inferior sigue abierto.
  - **Robusto:** 30 y 60, OPEN_UPPER_GRID_EDGE. 60 es el tope de la grilla, así que no está identificado, y la grilla
    no se extendió.
- **F0 y Finf no se confunden.** Las dos dimensiones tienen grilla, bordes y clase propios. Finf nunca supera a F0: los
  3 puntos que lo harían son rechazos analíticos, sin simular.

## 4. Trayectorias de 1 L y 2 L (P2I-2Y-7)

<!-- generado:trayectorias -->
Representativos (sobrevivientes primarios ordenados por el aporte inicial de 57m; bajo, medio y alto), con la sangre del representativo medio de P2I-2V-R y sangrado en curso. El volumen circulante, el gasto, la DO2 y el déficit son consecuencias secundarias: no filtran.

**Bajo: F0 0,15 · Finf 0,15 · τ 15.**

57m, 1 L en 20 min: aporte inicial 0,15; dilución pico 0,24 g/dL; reversión a los 120 min 6 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,15 | 0,15 | 0,15 | 0,15 |
| dilución de Hb | 0,00 | 0,24 | 0,23 | 0,23 | 0,23 |
| volumen circulante C | 0 | 50 | 0 | -131 | -360 |
| gasto relativo | 1,00 | 1,03 | 1,00 | 0,91 | 0,73 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,30 | 0,23 |
| déficit crítico | 0,15 | 0,15 | 0,18 | 0,26 | 0,42 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

57m, 2 L en 20 min: aporte inicial 0,15; dilución pico 0,47 g/dL; reversión a los 120 min 10 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,15 | 0,15 | 0,15 | 0,15 |
| dilución de Hb | 0,00 | 0,47 | 0,46 | 0,43 | 0,42 |
| volumen circulante C | 0 | 200 | 150 | 0 | -225 |
| gasto relativo | 1,00 | 1,12 | 1,10 | 1,00 | 0,84 |
| DO2 | 0,34 | 0,36 | 0,35 | 0,32 | 0,26 |
| déficit crítico | 0,15 | 0,11 | 0,13 | 0,21 | 0,35 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 1 L en 20 min: aporte inicial 0,15; dilución pico 0,23 g/dL; reversión a los 120 min 6 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,15 | 0,15 | 0,15 | 0,15 |
| dilución de Hb | 0,00 | 0,23 | 0,22 | 0,22 | 0,22 |
| volumen circulante C | 0 | 50 | 0 | -131 | -360 |
| gasto relativo | 1,00 | 1,02 | 1,00 | 0,94 | 0,82 |
| DO2 | 0,34 | 0,33 | 0,33 | 0,31 | 0,26 |
| déficit crítico | 0,15 | 0,16 | 0,18 | 0,23 | 0,34 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 2 L en 20 min: aporte inicial 0,15; dilución pico 0,45 g/dL; reversión a los 120 min 10 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,15 | 0,15 | 0,15 | 0,15 |
| dilución de Hb | 0,00 | 0,45 | 0,44 | 0,41 | 0,40 |
| volumen circulante C | 0 | 200 | 150 | 0 | -225 |
| gasto relativo | 1,00 | 1,08 | 1,06 | 1,00 | 0,89 |
| DO2 | 0,34 | 0,34 | 0,34 | 0,32 | 0,28 |
| déficit crítico | 0,15 | 0,14 | 0,16 | 0,21 | 0,31 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

**Medio: F0 0,25 · Finf 0,05 · τ 60.**

57m, 1 L en 20 min: aporte inicial 0,22; dilución pico 0,35 g/dL; reversión a los 120 min 70 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,22 | 0,19 | 0,14 | 0,08 |
| dilución de Hb | 0,00 | 0,35 | 0,30 | 0,20 | 0,11 |
| volumen circulante C | 0 | 119 | 43 | -146 | -430 |
| gasto relativo | 1,00 | 1,08 | 1,03 | 0,90 | 0,67 |
| DO2 | 0,34 | 0,35 | 0,33 | 0,29 | 0,22 |
| déficit crítico | 0,15 | 0,13 | 0,17 | 0,27 | 0,46 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

57m, 2 L en 20 min: aporte inicial 0,22; dilución pico 0,66 g/dL; reversión a los 120 min 70 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,22 | 0,19 | 0,14 | 0,08 |
| dilución de Hb | 0,00 | 0,66 | 0,58 | 0,38 | 0,20 |
| volumen circulante C | 0 | 337 | 236 | -24 | -359 |
| gasto relativo | 1,00 | 1,20 | 1,15 | 0,98 | 0,73 |
| DO2 | 0,34 | 0,37 | 0,35 | 0,31 | 0,23 |
| déficit crítico | 0,15 | 0,08 | 0,11 | 0,22 | 0,41 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 1 L en 20 min: aporte inicial 0,22; dilución pico 0,33 g/dL; reversión a los 120 min 70 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,22 | 0,19 | 0,14 | 0,08 |
| dilución de Hb | 0,00 | 0,33 | 0,29 | 0,19 | 0,10 |
| volumen circulante C | 0 | 119 | 43 | -146 | -430 |
| gasto relativo | 1,00 | 1,05 | 1,02 | 0,93 | 0,78 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,31 | 0,25 |
| déficit crítico | 0,15 | 0,15 | 0,17 | 0,24 | 0,37 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 2 L en 20 min: aporte inicial 0,22; dilución pico 0,63 g/dL; reversión a los 120 min 70 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,22 | 0,19 | 0,14 | 0,08 |
| dilución de Hb | 0,00 | 0,63 | 0,56 | 0,37 | 0,19 |
| volumen circulante C | 0 | 337 | 236 | -24 | -359 |
| gasto relativo | 1,00 | 1,13 | 1,10 | 0,99 | 0,82 |
| DO2 | 0,34 | 0,35 | 0,34 | 0,31 | 0,26 |
| déficit crítico | 0,15 | 0,13 | 0,15 | 0,21 | 0,34 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

**Alto: F0 0,35 · Finf 0 · τ 60.**

57m, 1 L en 20 min: aporte inicial 0,30; dilución pico 0,46 g/dL; reversión a los 120 min 89 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,30 | 0,25 | 0,15 | 0,06 |
| dilución de Hb | 0,00 | 0,46 | 0,39 | 0,22 | 0,05 |
| volumen circulante C | 0 | 195 | 100 | -135 | -458 |
| gasto relativo | 1,00 | 1,12 | 1,06 | 0,91 | 0,64 |
| DO2 | 0,34 | 0,35 | 0,34 | 0,30 | 0,21 |
| déficit crítico | 0,15 | 0,11 | 0,15 | 0,26 | 0,47 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

57m, 2 L en 20 min: aporte inicial 0,30; dilución pico 0,87 g/dL; reversión a los 120 min 89 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,30 | 0,25 | 0,15 | 0,06 |
| dilución de Hb | 0,00 | 0,87 | 0,74 | 0,42 | 0,10 |
| volumen circulante C | 0 | 490 | 350 | 3 | -414 |
| gasto relativo | 1,00 | 1,28 | 1,21 | 1,00 | 0,68 |
| DO2 | 0,34 | 0,38 | 0,36 | 0,32 | 0,22 |
| déficit crítico | 0,15 | 0,05 | 0,09 | 0,21 | 0,44 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 1 L en 20 min: aporte inicial 0,30; dilución pico 0,44 g/dL; reversión a los 120 min 89 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,30 | 0,25 | 0,15 | 0,06 |
| dilución de Hb | 0,00 | 0,44 | 0,37 | 0,21 | 0,05 |
| volumen circulante C | 0 | 195 | 100 | -135 | -458 |
| gasto relativo | 1,00 | 1,08 | 1,04 | 0,94 | 0,76 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,31 | 0,25 |
| déficit crítico | 0,15 | 0,14 | 0,17 | 0,23 | 0,37 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

72f, 2 L en 20 min: aporte inicial 0,30; dilución pico 0,83 g/dL; reversión a los 120 min 89 %.

| Minuto | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| retenido (fracción) | 0,00 | 0,30 | 0,25 | 0,15 | 0,06 |
| dilución de Hb | 0,00 | 0,83 | 0,71 | 0,40 | 0,09 |
| volumen circulante C | 0 | 490 | 350 | 3 | -414 |
| gasto relativo | 1,00 | 1,19 | 1,14 | 1,00 | 0,79 |
| DO2 | 0,34 | 0,35 | 0,34 | 0,32 | 0,26 |
| déficit crítico | 0,15 | 0,12 | 0,14 | 0,21 | 0,36 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |

<!-- /generado:trayectorias -->

### 4.1 Lectura

- **Contexto.**
  - La sangre es la del representativo medio de P2I-2V-R: B0 4000, tasa 5, meta 0,75, τ 240 y capacidad 1000, en el
    borde superior de la banda (57m 0,5; 72f 0,6).
  - Ese estado ya llega en extracción crítica, con déficit 0,15. Ninguna exposición cambia el estado en 120 min.
  - Los representativos son del conjunto primario, que sólo exige FD-BLD-06 en alguna sonda. Por eso el alto
    (0,35|0|60) excede aquí la envolvente de 2 L de FD-BLD-06, con 0,87 en 57m y 0,83 en 72f frente a 0,4–0,8: es la
    falla con B0 4000 de §2.2.
- **Aporte circulante inicial** (máximo retenido en los primeros 30 min): bajo 0,15, medio 0,22 y alto 0,30. Es igual
  en los dos casos y con 1 o 2 L.
- **Efecto restante** (retenido a los 30, 60 y 120 min):
  - bajo: 0,15, 0,15 y 0,15, sin redistribución;
  - medio: 0,19, 0,14 y 0,08;
  - alto: 0,25, 0,15 y 0,06.
- **Dilución de Hb.**
  - Pico con 1 L: 0,24, 0,35 y 0,46 g/dL en 57m (bajo, medio y alto), y 0,23, 0,33 y 0,44 en 72f.
  - Pico con 2 L: 0,47, 0,66 y 0,87 en 57m, y 0,45, 0,63 y 0,83 en 72f.
  - Reversión a los 120 min: 6–10 % en el bajo, 70 % en el medio y 89 % en el alto.
  - La reversión del bajo no viene de que la bolsa salga, porque su retenido es constante. El registro no desglosa qué
    la produce, así que no se interpreta.
- **Gasto relativo a los 20 min** (fin de la infusión):
  - con 1 L, 1,03, 1,08 y 1,12 en 57m, y 1,02, 1,05 y 1,08 en 72f;
  - con 2 L, 1,12, 1,20 y 1,28 en 57m, y 1,08, 1,13 y 1,19 en 72f.

  A los 120 min, con el sangrado en curso, todos quedan por debajo de la llegada (57m con 1 L: 0,73, 0,67 y 0,64). El
  bajo, que retiene más tarde, es el que conserva más gasto.
- **DO2 y déficit.**
  - Con la bolsa, la DO2 se mueve poco a los 20 min (0,33–0,38, desde 0,34) y baja a 0,21–0,28 a los 120.
  - El déficit mejora mientras dura el efecto (por ejemplo, alto con 2 L en 57m: 0,05 a los 20 min) y empeora después
    con el sangrado (0,31–0,47 a los 120).
- **Alcance.** Son consecuencias secundarias: no filtran ni seleccionan.

## 5. Dependencia del estado (P2I-2Y-6)

<!-- generado:estado -->
La misma exposición en cada posición compatible de cada caso: aumento máximo del gasto en los primeros 30 min (sobre el gasto de llegada).

| Representativo | Caso | Volumen | Posición inferior | Posición media | Posición superior |
|---|---|---|---|---|---|
| bajo | 57m | 1 L | 0,2: 13 % (se detiene en el 113′) | 0,35: 6 % | 0,5: 3 % |
| bajo | 57m | 2 L | 0,2: 50 % | 0,35: 23 % | 0,5: 12 % |
| bajo | 72f | 1 L | 0,3: 8 % | 0,45: 4 % | 0,6: 2 % |
| bajo | 72f | 2 L | 0,3: 29 % | 0,45: 15 % | 0,6: 8 % |
| medio | 57m | 1 L | 0,2: 30 % (se detiene en el 98′) | 0,35: 14 % | 0,5: 8 % |
| medio | 57m | 2 L | 0,2: 81 % (se detiene en el 115′) | 0,35: 37 % | 0,5: 20 % |
| medio | 72f | 1 L | 0,3: 18 % | 0,45: 9 % | 0,6: 5 % |
| medio | 72f | 2 L | 0,3: 47 % | 0,45: 25 % | 0,6: 13 % |
| alto | 57m | 1 L | 0,2: 49 % (se detiene en el 95′) | 0,35: 23 % | 0,5: 12 % |
| alto | 57m | 2 L | 0,2: 112 % (se detiene en el 106′) | 0,35: 52 % | 0,5: 28 % |
| alto | 72f | 1 L | 0,3: 28 % (se detiene en el 139′) | 0,45: 15 % | 0,6: 8 % |
| alto | 72f | 2 L | 0,3: 65 % | 0,45: 34 % | 0,6: 19 % |
<!-- /generado:estado -->

### 5.1 Lectura

- **Qué estados lee.** Las posiciones inferior y media no tienen sobrevivientes conjuntos en ninguna tasa (§1). La
  tabla lee la misma bolsa en estados que el filtro de sangre rechaza, como pide P2I-2Y-6, sólo para mostrar la
  dependencia: no son estados candidatos.
- **La respuesta depende del estado.** Con la misma bolsa, el aumento del gasto es mucho mayor en la posición inferior
  de la banda que en la superior. Por ejemplo, con 1 L en 57m:
  - alto: 49 %, 23 % y 12 % (inferior, media, superior);
  - medio: 30 %, 14 % y 8 %;
  - bajo: 13 %, 6 % y 3 %.
- **Entre casos.** En 72f es menor en cada combinación de representativo, volumen y posición relativa; por ejemplo,
  alto con 1 L: 28 %, 15 % y 8 %.
- **Entre volúmenes.** Con 2 L, el aumento es más del doble del de 1 L en cada posición.
- **No hay una regla fija** de 1 L → X % de gasto: según el representativo, el caso y la posición, 1 L da entre 2 % y
  49 %. Tampoco se calibró ninguna.
- **«Se detiene».** En varias corridas de la posición inferior, el gasto llega a 0 con pulso dentro de la corrida, y la
  corrida se detiene ahí: el colapso está apagado y no se activa. Pasa en:
  - el bajo, en 57m con 1 L, en el 113′;
  - el medio, en 57m con 1 L en el 98′ y con 2 L en el 115′;
  - el alto, en 57m con 1 L en el 95′ y con 2 L en el 106′, y en 72f con 1 L en el 139′.

  El registro no guarda si la misma corrida sin bolsa también se detiene, así que no se le atribuye a la bolsa. El
  aumento del gasto se lee en los primeros 30 min, antes de cualquier detención.

## 6. Interacción con la región de sangre

- **Del cristaloide hacia la sangre.** La única interacción es FD-BLD-06, a través de B0 (§2.2):
  - con B0 5000, la bolsa de menor F0 (aporte inicial 0,15) diluye de menos;
  - con B0 3000, las de F0 ≥ 0,25 diluyen de más;
  - sólo F0 0,2 pasa en todo el rango de B0 de la región certificada (3000–5000).
- **De la sangre hacia la tasa.** La robustez de la tasa (§1) usa los valores supervivientes del cristaloide de
  P2I-2V-R, en la parametrización anterior: `effective` 0,2 y 0,3; `transient` 0,4, 0,6 y 0,8; `leak` 15, 30 y 60.
  - En la superficie nueva, eso es F0 0,2 o 0,3, con Finf entre 0,04 y 0,18.
  - El límite en 7 no depende de esos valores, porque lo fija U-OUT, que no lleva bolsa.
  - Los recuentos con 5 y 6 sí dependen, porque leen FD-BLD-06 con esos valores.
- **No se evaluó la región conjunta** (tasa × superficie nueva del cristaloide × resto de la sangre). Le corresponde al
  refiltrado futuro (§9), no a este paquete.

## 7. Nivel 1 y sondas históricas (P2I-2Y-10)

- Las sondas de nivel 1 siguen siendo SYNTHETIC_STATE_PERTURBATION, y las de nivel 2, HISTORICAL_PROBE. No se cambió
  ninguna.
- Ninguna entra en la inferencia: `blood_fluid_calibration.py` no importa los módulos de sondas ni el motor heredado, ni
  lee lactato, PAS ni PAM. Una prueba lo fija.

## 8. Resúmenes separados (P2I-2Y-11)

No hay un «mejor candidato» único: la tasa y el cristaloide se resumen por separado.

- **Tasa.**
  - ROBUST_BOUNDARY: con la meta 1,0 y τ 480, la tasa 7 sigue sin sobrevivientes conjuntos, y la 6 no pierde ninguno.
  - Se mantiene el registro docente: TESTED_VIABLE_RATE_REGION = {5, 6}; FIRST_TESTED_NONVIABLE_RATE = 7.
  - Es condicional a la región de P2I-2V-R, a la banda compatible y a los puntos explorados. No es una tasa aprobada.
- **Cristaloide.**
  - Primario: 17 puntos (15 bolsas), con F0 0,15–0,35, Finf 0–0,15 y τ 15–60.
  - Robusto: 3, con F0 0,2, Finf 0,05–0,1 y τ 30–60.
  - FD-BLD-05 es la restricción que más recorta (de 54 a 17).
  - FD-BLD-06 separa por B0.
  - F0 sólo queda acotado en el criterio robusto, y Finf tiene el lado inferior en el borde del dominio.
  - Nada está aprobado ni elegido.

## 9. Requisito para el refiltrado futuro del lactato

- El refiltrado futuro del lactato (P2I-2R, hoy en pausa) **debe regenerarse desde la fisiología actual**:
  - el BloodState compartido;
  - la DO2 y la extracción corregidas;
  - la región de sangre restringida por la docencia (P2I-2V-R, con los cierres de P2I-2W y P2I-2X y la robustez de la
    tasa de este paquete);
  - la región del cristaloide calibrada en la superficie F0 / Finf / τ;
  - la región de precarga compatible con el caso (57m 0,2–0,5; 72f 0,3–0,6).
- **No debe reutilizar la región histórica de P2F de 1054 conjuntos.** Se construyó (P2F, 2026-10-23) antes de la
  fisiología de la entrega y la extracción de O2 (P2I-2P) y del BloodState compartido (P2I-2T), sin las restricciones
  docentes de sangre ni la superficie nueva del cristaloide.
- Este paquete no refiltra nada: sólo deja escrito el requisito.

## 10. Qué no hace

- No cambia ninguna restricción docente. `blood_constraints.py` queda igual byte a byte, y una prueba lo fija.
  - FD-BLD-04, 05 y 06 son las de P2I-2V-R.
  - Las bandas de precarga siguen siendo bandas candidatas compatibles con el caso, sin endurecerlas.
- No aprueba, no elige y no interpola ningún parámetro oculto: ni una tasa, ni un F0, ni un Finf, ni un τ.
- No densifica entre 6 y 7, no explora la meta por encima de 1 y no agrega valores a la grilla después de evaluar.
- No refiltra el lactato, y no usa lactato, PAS, PAM ni el motor heredado para filtrar.
- No calibra la presión ni la FC, ni activa el colapso.
- No migra GI ni otra familia, y no integra nada en tiempo de ejecución.
- La deuda TD-88 sigue abierta.

## 11. Decisiones pendientes (docencia)

- **Tasa:** si se acepta ROBUST_BOUNDARY como cierre del límite entre 6 y 7 para esta etapa.
- **Cristaloide:**
  - qué criterio se usa para la región del cristaloide: primario (17), robusto (3) o aislado (15);
  - si 0,15|0,15|\*, en el borde exacto de FD-BLD-04 y 05, se admite;
  - si FD-BLD-06 debe leerse en todo el rango de B0 de la región.
- **Grilla:** si se extiende τ por encima de 60 en un paquete posterior, decidido y congelado antes de evaluar, ya que
  el lado superior de τ queda abierto en el criterio robusto.
- **Lactato:** cuándo se reabre el filtro docente, con la región regenerada de §9.
