# P2I-2Z · Borde de τ del cristaloide y preparación del lactato con la fisiología actual

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no ejecuta el filtro del lactato;
- no calibra la presión ni la FC, ni activa el colapso;
- no elige parámetros ocultos ni se ajusta al motor heredado;
- no cambia ninguna restricción docente: FD-BLD-04, 05 y 06 son las de P2I-2V-R.

Código: `clinical_core/blood_fluid_readiness.py` (diseño, regla, criterios y evaluación; congelado en `a927301` antes de
evaluar) y `clinical_core/blood_fluid_readiness_report.py` (sólo este informe). Números:
`docs/revision/P2I2Z_blood_fluid_readiness.json`. Registro de partida, cerrado: P2I-2Y (`67e5b80a…`).

**Decisiones docentes aplicadas (2026-10-28):**
- **Tasa de sangrado:** cerrada para esta etapa como ROBUST_BOUNDARY: TESTED_VIABLE_RATE_REGION = {5, 6} y
  FIRST_TESTED_NONVIABLE_RATE = 7. Es información candidata restringida por la docencia, no FACULTY_APPROVED; no se
  densifica, no se interpola y no se vuelve a simular.
- **Cristaloide:** la región ROBUST de P2I-2Y es la base candidata preferida, sin valores aprobados.
- **Regla de calibración:** para el cristaloide isotónico estándar en estos adultos modelados, un candidato activo
  necesita Finf < F0, es decir, un componente transitorio que se redistribuye. Finf = F0 sigue siendo matemáticamente
  válido como estado de referencia o histórico, fuera de la región preferida. No es una ley para otros fluidos.

## 1. Borde de τ (P2I-2Z-1 a 3)

<!-- generado:tau -->
Congelamiento de P2I-2Z: `e89a248ef406acda8c17d95931da98eac9e92d8ab2c1c1fb5bd2e9bf0f20ecf4`, comprometido antes de evaluar (una prueba lo fija). Registro de partida: P2I-2Y `67e5b80a5a96f526fc2f9e5b2c721026f3ac71ba612fe9cb3e06f23106f4a8d4`.

Diseño: F0 0,2; Finf 0,05 y 0,1; τ 60, 90 y 120 min (6 puntos; τ 60 reproduce P2I-2Y). FD-BLD-06 se lee en las 14 sondas de P2I-2Y y en las 45 claves certificadas (tasas 5 y 6): 48 claves de sangre distintas, en los dos casos.

| Punto | Regla | FD-BLD-04 | FD-BLD-05 | FD-BLD-06 referencia | FD-BLD-06 todas las sondas | FD-BLD-06 todas las claves certificadas | Robusto en la región de sangre |
|---|---|---|---|---|---|---|---|
| F0 0,2 · Finf 0,05 · τ 60 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |
| F0 0,2 · Finf 0,05 · τ 90 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |
| F0 0,2 · Finf 0,05 · τ 120 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |
| F0 0,2 · Finf 0,1 · τ 60 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |
| F0 0,2 · Finf 0,1 · τ 90 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |
| F0 0,2 · Finf 0,1 · τ 120 | Finf < F0 | pasa | pasa | pasa | pasa | pasa | **sí** |

Lecturas, por punto (los dos casos):

| Punto | Aporte inicial | Dilución pico 1 L (mín.–máx. en las claves) | Dilución pico 2 L (mín.–máx.) | Claves donde falla FD-BLD-06 |
|---|---|---|---|---|
| F0 0,2 · Finf 0,05 · τ 60 | 0,18 | 0,21–0,37 | 0,42–0,71 | ninguna |
| F0 0,2 · Finf 0,05 · τ 90 | 0,18 | 0,22–0,39 | 0,43–0,74 | ninguna |
| F0 0,2 · Finf 0,05 · τ 120 | 0,19 | 0,22–0,40 | 0,44–0,75 | ninguna |
| F0 0,2 · Finf 0,1 · τ 60 | 0,18 | 0,22–0,39 | 0,43–0,74 | ninguna |
| F0 0,2 · Finf 0,1 · τ 90 | 0,19 | 0,23–0,40 | 0,44–0,76 | ninguna |
| F0 0,2 · Finf 0,1 · τ 120 | 0,19 | 0,23–0,40 | 0,45–0,77 | ninguna |

τ 90 sobrevive: **sí**. τ 120 sobrevive: **sí**. Lado superior de τ: **OPEN_UPPER_GRID_EDGE**. La extensión se detiene aquí: no se agrega ningún τ sin autorización docente.
<!-- /generado:tau -->

### 1.1 Lectura

- **Los 6 puntos sobreviven y son robustos en toda la región de sangre:** FD-BLD-04 y 05 con la bolsa sola, y FD-BLD-06
  en los dos casos en las 48 claves.
- **Alcance de FD-BLD-06, interpretación declarada.** El encargo pedía estados de sangre representativos y de borde.
  - Las 45 claves certificadas son todas las claves distintas de 5 dimensiones de la región, es decir, el producto
    exhaustivo sobre lo único que FD-BLD-06 lee.
  - No es el producto con los 5691 conjuntos de sangre: son 576 filas de FD-BLD-06 y 588 en total.
  - Se eligió así para leer el criterio robusto en toda la región, y quedó congelado antes de evaluar.
- **τ 60 reproduce P2I-2Y.** Coinciden los veredictos de FD-BLD-04 y 05 y los de FD-BLD-06 en las 14 sondas; la
  corrida lo comprueba antes de seguir.
- **τ 90 sobrevive y τ 120 sobrevive.** No aparece un límite superior interior: τ queda **OPEN_UPPER_GRID_EDGE** en
  120. Según la regla congelada, la extensión se detiene aquí y no se agrega ningún τ sin autorización docente.
- **Márgenes.** Las lecturas se acercan a sus bordes a medida que τ sube, pero ninguna los cruza:
  - FD-BLD-05 a los 120 min, con Finf 0,1: retenido 0,116 con τ 60, 0,129 con τ 90 y 0,140 con τ 120 (techo 0,15);
  - FD-BLD-06 con 2 L, pico máximo en la clave 3000|6|1|480|500 (57m): 0,741, 0,759 y 0,768 con Finf 0,1 (techo 0,8);
  - FD-BLD-06 con 1 L, pico mínimo en 5000|5|1|120|100 (72f): de 0,211 a 0,229 (piso 0,2).

  Se informan sin extrapolar: no dicen dónde fallaría un τ mayor.

## 2. Región candidata del cristaloide (P2I-2Z-4)

<!-- generado:region -->
Región robusta (puntos activos, Finf < F0): F0 0,2 · Finf 0,05 · τ 60, F0 0,2 · Finf 0,05 · τ 90, F0 0,2 · Finf 0,05 · τ 120, F0 0,2 · Finf 0,1 · τ 30, F0 0,2 · Finf 0,1 · τ 60, F0 0,2 · Finf 0,1 · τ 90, F0 0,2 · Finf 0,1 · τ 120.

| Parámetro | Explorado | Soporte candidato | Clase | Lado inferior | Lado superior | Borde | Identificado (regla congelada) |
|---|---|---|---|---|---|---|---|
| F0 | 0,15, 0,2, 0,25, 0,3, 0,35 | 0,2 | WELL_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | sí |
| Finf | 0, 0,05, 0,1, 0,15, 0,2 | 0,05, 0,1 | PARTIALLY_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | no |
| tau | 15, 30, 60, 90, 120 | 30, 60, 90, 120 | PARTIALLY_CONSTRAINED | acotado por restricción | abierto (borde de la grilla) | OPEN_UPPER_GRID_EDGE | no |
<!-- /generado:region -->

### 2.1 Lectura

- **Regla Finf < F0.** Los 6 puntos del diseño son candidatos activos.
  - De los 17 primarios de P2I-2Y, los tres 0,15|0,15|\* (Finf = F0) quedan REFERENCE_ONLY_NO_TRANSIENT, fuera de la
    región preferida. Ya no eran robustos.
  - Finf > F0 sigue siendo `ANALYTIC_REJECTION`.
- **Región robusta: 7 puntos**, todos con F0 0,2.
  - Los 6 de τ 60 a 120 se evaluaron aquí.
  - 0,2|0,1|30 viene de P2I-2Y: es robusto ahí, y su prueba comprometida lo lee en las 81 claves.
  - 0,2|0,05|30 falla FD-BLD-05 con la bolsa sola, y τ 15 falla FD-BLD-04 o 05 con los dos Finf.
- **F0 0,2.** La regla congelada lo marca «identificado» (WELL_CONSTRAINED, INTERIOR), pero sólo en este sentido:
  - sus vecinos, 0,15 y 0,25, se exploraron en P2I-2Y con τ ≤ 60;
  - con τ 90 y 120 la docencia fijó F0 en 0,2 y no se exploró ningún vecino.

  No es un valor aprobado ni elegido.
- **Finf 0,05–0,1.** PARTIALLY_CONSTRAINED e INTERIOR. Sus vecinos (0 y 0,15) también se exploraron sólo con τ ≤ 60.
- **τ 30–120.**
  - El lado inferior lo acota una restricción (τ 15 falla), y τ 30 sólo sobrevive con Finf 0,1.
  - El lado superior queda abierto en el borde de la grilla. No está identificado.
- **Sin «mejor combinación».** No se elige ningún punto ni se marca nada FACULTY_APPROVED.

## 3. Trayectorias de 1 L y 2 L

<!-- generado:trayectorias -->
Sangre del representativo medio de P2I-2V-R (tasa 5, posición superior de la banda), sangrado en curso, bolsa en 20 min desde el minuto 0. Contexto: no filtra.

| Punto | Caso | Volumen | Aporte inicial | Retenido 30′ / 60′ / 120′ | Dilución 20′ / 30′ / 60′ / 120′ (g/dL) | Pico | Reversión a 120′ | Gasto 20′ / 120′ | DO2 20′ / 120′ | Déficit 20′ / 120′ | Estado 120′ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F0 0,2 · Finf 0,05 · τ 60 | 57m | 1 L | 0,18 | 0,16 / 0,11 / 0,07 | 0,28 / 0,24 / 0,17 / 0,10 | 0,28 | 65 % | 1,05 / 0,66 | 0,34 / 0,22 | 0,15 / 0,46 | crítica |
| F0 0,2 · Finf 0,05 · τ 60 | 57m | 2 L | 0,18 | 0,16 / 0,11 / 0,07 | 0,54 / 0,48 / 0,33 / 0,19 | 0,54 | 65 % | 1,16 / 0,72 | 0,36 / 0,23 | 0,10 / 0,42 | crítica |
| F0 0,2 · Finf 0,05 · τ 60 | 72f | 1 L | 0,18 | 0,16 / 0,11 / 0,07 | 0,27 / 0,23 / 0,17 / 0,09 | 0,27 | 65 % | 1,03 / 0,78 | 0,34 / 0,25 | 0,16 / 0,37 | crítica |
| F0 0,2 · Finf 0,05 · τ 60 | 72f | 2 L | 0,18 | 0,16 / 0,11 / 0,07 | 0,52 / 0,46 / 0,31 / 0,18 | 0,52 | 65 % | 1,10 / 0,81 | 0,34 / 0,26 | 0,14 / 0,35 | crítica |
| F0 0,2 · Finf 0,05 · τ 90 | 57m | 1 L | 0,18 | 0,17 / 0,14 / 0,09 | 0,29 / 0,26 / 0,20 / 0,13 | 0,29 | 56 % | 1,05 / 0,68 | 0,34 / 0,22 | 0,14 / 0,45 | crítica |
| F0 0,2 · Finf 0,05 · τ 90 | 57m | 2 L | 0,18 | 0,17 / 0,14 / 0,09 | 0,57 / 0,52 / 0,39 / 0,25 | 0,57 | 57 % | 1,16 / 0,75 | 0,36 / 0,24 | 0,10 / 0,40 | crítica |
| F0 0,2 · Finf 0,05 · τ 90 | 72f | 1 L | 0,18 | 0,17 / 0,14 / 0,09 | 0,28 / 0,25 / 0,20 / 0,12 | 0,28 | 56 % | 1,04 / 0,79 | 0,34 / 0,26 | 0,16 / 0,36 | crítica |
| F0 0,2 · Finf 0,05 · τ 90 | 72f | 2 L | 0,18 | 0,17 / 0,14 / 0,09 | 0,54 / 0,49 / 0,37 / 0,23 | 0,54 | 57 % | 1,11 / 0,83 | 0,34 / 0,27 | 0,14 / 0,34 | crítica |
| F0 0,2 · Finf 0,05 · τ 120 | 57m | 1 L | 0,19 | 0,18 / 0,15 / 0,11 | 0,30 / 0,28 / 0,22 / 0,15 | 0,30 | 49 % | 1,06 / 0,69 | 0,34 / 0,22 | 0,14 / 0,44 | crítica |
| F0 0,2 · Finf 0,05 · τ 120 | 57m | 2 L | 0,19 | 0,18 / 0,15 / 0,11 | 0,58 / 0,54 / 0,42 / 0,29 | 0,58 | 50 % | 1,17 / 0,77 | 0,36 / 0,25 | 0,09 / 0,39 | crítica |
| F0 0,2 · Finf 0,05 · τ 120 | 72f | 1 L | 0,19 | 0,18 / 0,15 / 0,11 | 0,29 / 0,26 / 0,21 / 0,15 | 0,29 | 49 % | 1,04 / 0,80 | 0,34 / 0,26 | 0,16 / 0,36 | crítica |
| F0 0,2 · Finf 0,05 · τ 120 | 72f | 2 L | 0,19 | 0,18 / 0,15 / 0,11 | 0,55 / 0,51 / 0,40 / 0,28 | 0,55 | 50 % | 1,11 / 0,85 | 0,35 / 0,27 | 0,14 / 0,33 | crítica |
| F0 0,2 · Finf 0,1 · τ 60 | 57m | 1 L | 0,18 | 0,17 / 0,14 / 0,12 | 0,29 / 0,27 / 0,22 / 0,17 | 0,29 | 44 % | 1,05 / 0,70 | 0,34 / 0,23 | 0,14 / 0,44 | crítica |
| F0 0,2 · Finf 0,1 · τ 60 | 57m | 2 L | 0,18 | 0,17 / 0,14 / 0,12 | 0,57 / 0,52 / 0,41 / 0,31 | 0,57 | 45 % | 1,16 / 0,79 | 0,36 / 0,25 | 0,10 / 0,38 | crítica |
| F0 0,2 · Finf 0,1 · τ 60 | 72f | 1 L | 0,18 | 0,17 / 0,14 / 0,12 | 0,28 / 0,26 / 0,21 / 0,16 | 0,28 | 44 % | 1,04 / 0,80 | 0,34 / 0,26 | 0,16 / 0,35 | crítica |
| F0 0,2 · Finf 0,1 · τ 60 | 72f | 2 L | 0,18 | 0,17 / 0,14 / 0,12 | 0,54 / 0,50 / 0,39 / 0,30 | 0,54 | 45 % | 1,11 / 0,86 | 0,34 / 0,27 | 0,14 / 0,32 | crítica |
| F0 0,2 · Finf 0,1 · τ 90 | 57m | 1 L | 0,19 | 0,18 / 0,16 / 0,13 | 0,30 / 0,28 / 0,24 / 0,19 | 0,30 | 39 % | 1,06 / 0,71 | 0,34 / 0,23 | 0,14 / 0,43 | crítica |
| F0 0,2 · Finf 0,1 · τ 90 | 57m | 2 L | 0,19 | 0,18 / 0,16 / 0,13 | 0,58 / 0,55 / 0,45 / 0,35 | 0,58 | 40 % | 1,17 / 0,80 | 0,36 / 0,25 | 0,09 / 0,37 | crítica |
| F0 0,2 · Finf 0,1 · τ 90 | 72f | 1 L | 0,19 | 0,18 / 0,16 / 0,13 | 0,29 / 0,27 / 0,23 / 0,18 | 0,29 | 39 % | 1,04 / 0,81 | 0,34 / 0,26 | 0,16 / 0,35 | crítica |
| F0 0,2 · Finf 0,1 · τ 90 | 72f | 2 L | 0,19 | 0,18 / 0,16 / 0,13 | 0,55 / 0,52 / 0,43 / 0,33 | 0,55 | 40 % | 1,11 / 0,87 | 0,35 / 0,27 | 0,14 / 0,32 | crítica |
| F0 0,2 · Finf 0,1 · τ 120 | 57m | 1 L | 0,19 | 0,18 / 0,17 / 0,14 | 0,31 / 0,29 / 0,25 / 0,20 | 0,31 | 34 % | 1,06 / 0,72 | 0,34 / 0,23 | 0,14 / 0,42 | crítica |
| F0 0,2 · Finf 0,1 · τ 120 | 57m | 2 L | 0,19 | 0,18 / 0,17 / 0,14 | 0,59 / 0,56 / 0,47 / 0,37 | 0,59 | 36 % | 1,17 / 0,82 | 0,36 / 0,26 | 0,09 / 0,36 | crítica |
| F0 0,2 · Finf 0,1 · τ 120 | 72f | 1 L | 0,19 | 0,18 / 0,17 / 0,14 | 0,29 / 0,27 / 0,24 / 0,19 | 0,29 | 34 % | 1,04 / 0,81 | 0,34 / 0,26 | 0,16 / 0,35 | crítica |
| F0 0,2 · Finf 0,1 · τ 120 | 72f | 2 L | 0,19 | 0,18 / 0,17 / 0,14 | 0,56 / 0,54 / 0,45 / 0,36 | 0,56 | 36 % | 1,11 / 0,88 | 0,35 / 0,27 | 0,14 / 0,31 | crítica |
<!-- /generado:trayectorias -->

### 3.1 Lectura

- **Con más τ:** queda más volumen retenido a los 120 min y la dilución se revierte menos.
  - Con 1 L en 57m y Finf 0,05, la reversión baja de 65 % (τ 60) a 49 % (τ 120); con Finf 0,1, de 44 % a 34 %.
  - El gasto a los 120 min sube poco: de 0,66 a 0,69 con Finf 0,05 y de 0,70 a 0,72 con Finf 0,1.
- **Estado de extracción:** con la sangre del representativo medio sigue en extracción crítica en todos los casos.
- **Corridas:** ninguna se detiene.
- **Alcance:** son consecuencias secundarias; no filtran ni seleccionan.

## 4. Comprobaciones estructurales

<!-- generado:estructura -->
Tres representativos de P2I-2V-R × dos casos, posición superior, 120 min sin tratamiento (y 2 L de 0,2|0,1|60 para ρ). Tolerancia 1e-09 (redondeo de punto flotante).

| Comprobación | Resultado | Mayor diferencia |
|---|---|---|
| la cinética del lactato (ganancia y τ del lactato) no mueve la hemodinámica ni D | sí | hemodinámica 0,0e+00; D 0,0e+00 |
| la cinética de la deuda y la deuda de llegada no mueven la hemodinámica | sí | hemodinámica 0,0e+00 |
| la frecuencia intrínseca no mueve la hemodinámica, D ni el lactato | sí | hemodinámica 0,0e+00; D 0,0e+00; lactato 0,0e+00 |
| ρ (banda re-anclada) no mueve D ni el lactato | sí | D 7,1e-15; lactato 8,9e-16 |
| ρ sí mueve el índice de entrega (lo que lee la adecuación) | sí | índice de entrega 1,1e-01 |
<!-- /generado:estructura -->

### 4.1 Lectura

- **Qué muestran, en 6 estados fijos** (tres representativos × dos casos, sin tratamiento):
  - **Lactato:** la ganancia y la τ del lactato sólo mueven el lactato. Coincide con el código: `lactate_after_minute`
    lee D y nada lee el lactato para la hemodinámica.
  - **Deuda:** la τ de la deuda, la deuda por déficit y la deuda de llegada mueven D y el lactato, no la hemodinámica.
  - **Frecuencia intrínseca:** no mueve nada de lo que se lee; el gasto del núcleo no depende de la FC.
  - **ρ:** con la banda re-anclada (relación / ρ), ρ se cancela en D y en el lactato (diferencias de 1e-14, redondeo).
    Sí mueve el índice de entrega que lee la adecuación de las restricciones del lactato.
- **Qué permiten:** son la base del diseño factorizado de §6. La hemodinámica (y con ella el déficit efectivo) se
  simula una vez por estado de sangre, escenario y nivel de entrega de llegada. Lo del lado del lactato se aplica
  después con la misma recursión del núcleo.
- **Qué no demuestran:** que valga en todos los estados.
  - 4 de los 6 estados tienen la tasa 2,5 (representativos bajo y alto), fuera de {5, 6}.
  - Falta una comprobación de que ρ no mueve la hemodinámica, que el diseño de E necesita. La revisión la sondeó en el
    scratchpad (diferencia 0,0 con ρ 2 y 3, en los dos escenarios), pero no está en el registro. El próximo paquete debe comprobar, en una muestra, que el
  posproceso iguala la corrida completa antes de usarlo. Ya lo sugiere el propio `lactate_slice`: «el modelo del
  lactato es lineal dado el camino del déficit».

## 5. Preparación para reconstruir el lactato (P2I-2Z-7)

<!-- generado:preparacion -->
| Criterio | Resultado |
|---|---|
| BloodState compartido activo | cumple |
| modelo de DO2 y extracción vigente | cumple |
| región de precarga compatible con el caso definida | cumple |
| borde de la tasa de sangrado caracterizado | cumple |
| región candidata del cristaloide caracterizada | **no cumple** |
| ninguna sonda de hemorragia activa y obsoleta evita el BloodState | cumple |
| parámetros ocultos sin aprobar y soporte candidato explícito | cumple |

**Veredicto: NOT_READY** — región candidata del cristaloide caracterizada.
<!-- /generado:preparacion -->

### 5.1 Lectura

**NOT_READY — región candidata del cristaloide caracterizada:** el lado superior de τ queda OPEN_UPPER_GRID_EDGE en 120.

- **Criterio congelado:** pedía una región robusta no vacía, con sólo candidatos activos y el lado superior de τ acotado
  por una restricción. Los otros seis criterios se cumplen:
  - **BloodState compartido activo:** el estado del núcleo lleva `blood`, y las corridas sin tratamiento pierden sangre
    por él (volumen y pérdida acumulada).
  - **DO2 y extracción vigentes:** el perfil tiene la reserva de extracción (P2I-2P, aceptada en P2I-2Q), y ρ sólo llega
    a D como producto.
  - **Precarga compatible:** las bandas son 57m 0,2–0,5 y 72f 0,3–0,6. Los sobrevivientes conjuntos con las tasas 5 y
    6 están dentro, en 0,5 y 0,6.
  - **Tasa:** ROBUST_BOUNDARY, y U-OUT no lee la bolsa.
  - **Sondas:** las cinco escrituras directas de nivel 1 son SYNTHETIC_STATE_PERTURBATION, la sonda de banda de
    hemorragia es `BloodLoss` (por el BloodState) y las HISTORICAL_PROBES están fuera del arnés.
    - La sonda de P2I-2Q que restaba V directamente es un registro histórico: una prueba comprueba que ningún módulo
      activo importa los módulos de P2I-2P, 2Q ni 2S.
  - **Sin aprobaciones:** ningún parámetro del registro está FACULTY_APPROVED, no hay valores por familia ni mapeos de
    caso, y el soporte candidato está explícito.
- **Debilidades de la lógica congelada, sin efecto hoy:**
  - el criterio de precarga usa `all()` sobre las posiciones con sobrevivientes, que sería verdadero también sin
    ninguna; hoy hay una por caso y por tasa;
  - el criterio de sondas mira registros conocidos, no recorre el código. Por ejemplo, `decision_pack.preload_edge`
    (análisis P2G-9 del paquete P2G, registro cerrado) resta V directamente, pero no es una sonda del arnés activo.
- **Qué lo destraba:** una decisión docente sobre τ. Puede ser autorizar una extensión por encima de 120, congelada
  antes de evaluar, o aceptar τ ≤ 120 como soporte candidato con el borde abierto declarado. No lo decide este paquete.

## 6. Espacio de entrada del próximo paquete del lactato (P2I-2Z-8, borrador)

**DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY** (decisión docente, P2I-2AA). No es una entrada
certificada: el espacio vigente está en `docs/revision/P2I2AA_CIERRE_TAU_Y_SEMANTICA_LACTATO.md`, y sólo puede leerse
como entrada con `blood_fluid_tau_closure.certified_input`, que lo rechaza mientras el veredicto no sea READY.

<!-- generado:lactato -->
Estado: **BORRADOR (no se cumple la preparación)**. No se ejecuta.

| | Fuente | Valores |
|---|---|---|
| A. Sangre | sobrevivientes conjuntos de P2I-2Y con las tasas 5 y 6 | 3423 y 2268 conjuntos; 45 claves de 5 dimensiones; P1 (L1, L2) 45–135; P3 (L3) 120–1215 |
| B. Posición | la única con sobrevivientes conjuntos | 57m 0,5; 72f 0,6 |
| C. Tasa | registro docente | 5, 6 |
| D. Cristaloide | región robusta de P2I-2Z | F0 0,2 · Finf 0,05 · τ 60, F0 0,2 · Finf 0,05 · τ 90, F0 0,2 · Finf 0,05 · τ 120, F0 0,2 · Finf 0,1 · τ 30, F0 0,2 · Finf 0,1 · τ 60, F0 0,2 · Finf 0,1 · τ 90, F0 0,2 · Finf 0,1 · τ 120 |
| E. Extracción de O2 | ρ candidata 2,0–3,0, banda re-anclada | trayectorias con ρ 2,5; adecuación leída con ρ 2, 2,5, 3 |
| F. Lactato | registro de calibración y bandas del caso | τ de la deuda 30, 60, 120; ganancia 2, 6, 12; τ del lactato 45, 120, 240; exceso de llegada inf./medio/sup.; 5 pares (deuda, entrega) de llegada |

| Recuento (antes de simular) | Mínimo | Máximo |
|---|---|---|
| Candidatos (conjuntos) | 1020600 | 10333575 |
| Simulaciones del núcleo, diseño factorizado | 2880 | 13770 |
| Simulaciones del núcleo, producto ingenuo | 18370800 | 186004350 |
| Posprocesos de cinética y exceso por trayectoria y nivel de deuda de llegada (sin simular; más 3 lecturas de adecuación, una por ρ) | 81 | 81 |

Factorización válida según las comprobaciones estructurales: **sí**.
<!-- /generado:lactato -->

### 6.1 Lectura del borrador

No se ejecuta nada: es la especificación, con los recuentos, que el próximo paquete usaría si se destraba la
preparación. **Se construye desde la fisiología actual y no reutiliza la región histórica de P2F de 1054 conjuntos.**

**Desviación declarada.** El encargo decía «si READY, preparar». El veredicto es NOT_READY y aun así se preparó este
borrador, sin ejecutar nada. Se hizo porque sus reglas quedaron congeladas antes de evaluar y porque sólo D depende del
bloqueo. Si la docencia prefiere no tenerlo hasta destrabar la preparación, se retira (§11).

- **A. Sangre.**
  - **Fuente:** los sobrevivientes conjuntos certificados de P2I-2Y con las tasas 5 y 6 (3423 y 2268), con sus
    coordenadas viejas del cristaloide reemplazadas por D y la reserva por E.
  - **Por qué vale la sustitución:**
    - FD-BLD-04 y 05 sólo leen la bolsa;
    - FD-BLD-06 es la única restricción de sangre que lee el cristaloide, y los 7 puntos de D la cumplen en todas las
      claves certificadas;
    - ninguna restricción lee la reserva.

    Así, la sustitución no quita conjuntos de A. Queda la otra dirección: que ninguna clave haya quedado fuera sólo por
    la grilla vieja del cristaloide. La revisión adversarial lo comprobó en el scratchpad, no en el registro: en las 117
    claves no certificadas de las tasas 5 y 6, al menos uno de los 9 cristaloides viejos que cumplen FD-BLD-04 y 05 pasa
    FD-BLD-06 en los dos casos. El próximo paquete debe confirmarlo al enumerar A.
  - **Proyecciones:**
    - P1 = (tasa, B0, λ/κ, meta, τ y capacidad del relleno), que basta para L1 y L2: entre 45 y 135 conjuntos;
    - P3 = P1 × (Hb y volumen de la unidad de glóbulos rojos), para L3: entre 120 y 1215.
      - El mínimo de 120 que da el código congelado es válido pero holgado: divide por 54, como si pasaran los 18
        cristaloides viejos.
      - Como sólo 9 cumplen FD-BLD-04 y 05, que no dependen de la tasa, el mínimo ajustado es 225. Eso da al menos
        1 913 625 candidatos y 3510 simulaciones.
  - **Enumeración exacta:** el registro de P2I-2Y guarda sólo las claves de 5 dimensiones. La enumeración exacta se hace
    una vez, con la lógica congelada de P2I-2Y.
- **B. Posición:** 57m 0,5 y 72f 0,6, las únicas con sobrevivientes conjuntos. Las demás posiciones de la banda no
  tienen ninguno en ninguna tasa.
- **C. Tasa:** {5, 6}, el registro docente.
- **D. Cristaloide:** los 7 puntos robustos de §2. Sólo entra en L2 (2 L en 20 min con sangrado en curso). Depende de
  la decisión sobre τ.
- **E. Extracción de O2:**
  - las trayectorias se simulan con ρ 2,5, porque D y el lactato no dependen de ρ (§4);
  - la adecuación se lee después con ρ 2,0, 2,5 y 3,0, la banda candidata aceptada;
  - ρ 1,0, que sigue en la región de sangre porque ninguna restricción la lee, queda fuera de esa banda.
- **F. Parámetros propios del lactato:**
  - **Explorados:** τ de la deuda 30/60/120; ganancia 2/6/12; τ del lactato 45/120/240; exceso de llegada
    inferior/medio/superior; y los 5 pares (deuda, entrega) de llegada de P2F.
  - **Fijos con sensibilidad:** la deuda por déficit (canónica 1,0; 0,5 y 2) y la demanda basal (1,0; 0,9 y 1,1).
  - **Fuera:** la frecuencia intrínseca, porque no llega a nada de lo que se lee.
  - **Puntuales, sin explorar antes:** la fracción con IBP (0,8) y tras la hemostasia (0,1), que afectan a L3; y el
    minuto de la endoscopía, que da la regla del motor.
- **Recuentos antes de simular:**
  - 1 020 600 a 10 333 575 candidatos;
  - 2880 a 13 770 simulaciones del núcleo con el diseño factorizado, contra 18 370 800 a 186 004 350 con el producto
    ingenuo, que simula cada candidato, con los tres niveles de la frecuencia intrínseca, en cada escenario y caso;
  - por cada trayectoria simulada (un nivel de entrega de llegada), 81 posprocesos de cinética y exceso por cada nivel
    de deuda de llegada que forma par con ella (1 o 2), más 3 lecturas de adecuación, una por ρ; nada de eso se simula.
- **Diseño eficiente propuesto, en orden:**
  1. enumerar P1 y P3 una vez;
  2. simular por caso y nivel de entrega de llegada L1 (P1), L2 (P1 × D) y L3 (P3);
  3. validar en una muestra que el posproceso de D y del lactato iguala la corrida completa;
  4. posprocesar la cinética, el exceso y la deuda de llegada;
  5. leer la adecuación con las tres ρ;
  6. filtrar en secuencia (L1 primero y L2 y L3 sólo para lo que sobrevive);
  7. correr la sensibilidad sólo sobre los sobrevivientes.

## 7. Estado de la tasa de sangrado

- **Confirmado:** ROBUST_BOUNDARY, con TESTED_VIABLE_RATE_REGION = {5, 6} y FIRST_TESTED_NONVIABLE_RATE = 7, como
  información candidata.
- **No hizo falta ninguna simulación de tasa.** U-OUT lee la corrida sin tratamiento, que no lleva bolsa (una prueba lo
  fija). Este paquete no cambia ninguna fisiología: el núcleo sólo suma este módulo y dos listas de exclusión.

## 8. Prueba permanente de robustez (P2I-2Z-5)

**Decisión: no se agrega ninguna prueba.** La comprobación de 17 × 45 de P2I-2Y que está sólo en el scratchpad fue
corroborativa: ninguna conclusión comprometida depende sólo de ella.

- **Primario de P2I-2Y (17):** es igual a FD-BLD-04 ∧ 05, que lo fija el recuento del registro con su prueba. Agregar
  claves de sangre sólo puede sumar sondas donde pasa, y el techo ya es 17.
- **Robusto de P2I-2Y (3):** lo fija la prueba comprometida, que lee los 3 robustos en las 81 claves, y el robusto
  sólo puede achicarse.
- **Patrón por B0 en las 45 claves, para los 17 primarios de P2I-2Y:** sigue existiendo sólo en el scratchpad, con el
  rótulo de la sesión que ya tenía en el informe de P2I-2Y. Ninguna conclusión comprometida depende de él: los bordes de
  F0 salen de las 14 sondas comprometidas, y el robusto sólo puede achicarse.
- **Lo que sí cubre este registro:** los 6 puntos de τ 60 a 120 pasan en las 48 claves. El 7.º punto de D, 0,2|0,1|30,
  lo cubren la prueba comprometida de P2I-2Y (81 claves) y las 14 sondas de su registro.

## 9. Auditoría de dependencias (P2I-2Z-6)

- **De dónde viene la carga transitiva** de `legacy_adapter`, `calibration` y `bands`: no de la importación de
  `lactate_slice` que hace `blood_fluid_calibration.py` para leer `DOWNSTREAM_REPORTS`. Viene del arnés de sangre:
  `blood_constraints` → `blood_anchors` → `calibration` y `lactate_slice`. Y ahí se usan:
  - `calibration.case_values` y `REGISTRY`, para los valores del caso y la escala de precarga;
  - `lactate_slice.scenario_inputs`, para las entradas del caso producidas por el motor a través de `legacy_adapter`;
  - `bands.BloodLoss`.
- **Sin ganancia posible:** quitar la importación directa no descarga ningún módulo, porque `blood_constraints` ya los
  carga, y tocaría módulos congelados. No se hizo.
- **Lo que sí se aseguró:**
  - el módulo nuevo no importa `lactate_slice` (usa `freeze_sources` de P2I-2Y);
  - una prueba en un intérprete nuevo comprueba que no carga el motor de familias ni las restricciones del lactato.
- **Deuda registrada: TD-89.** El registro `DOWNSTREAM_REPORTS` vive en `lactate_slice`.
- **TD-88** sigue abierta: no bloquea los resúmenes, el barrido de τ ni la evaluación de la preparación.

## 10. Qué no hace

- **Restricciones:** no cambia ninguna (`blood_constraints.py` idéntico byte a byte, con una prueba).
- **Aprobaciones:** no aprueba, no elige y no interpola ningún parámetro oculto. No hay «mejor combinación».
- **Tasa:** no la vuelve a escanear ni la densifica.
- **τ:** no agrega valores por encima de 120. No cambia F0, Finf, la sangre ni la velocidad de infusión.
- **Lactato:** no ejecuta el filtro, y no usa como meta ningún lactato, PAS, PAM ni trayectoria heredada.
- **Otros límites:** no calibra la presión ni la FC, no activa el colapso, no migra ni integra nada.

## 11. Decisiones pendientes (docencia)

- **τ por encima de 120:** si se autoriza una extensión (qué valores, congelados antes de evaluar), o si se acepta
  τ 30–120 como soporte candidato con el borde superior abierto declarado. Esto destraba la preparación.
- **Adecuación con ρ:** con la reserva, la «entrega adecuada» que leen las restricciones del lactato, ¿es la entrega
  normal (ADEQUATE) o la ausencia de déficit (ADEQUATE o COMPENSATED)? Es lo único que ρ cambia.
- **Tasa 2,5:** confirmar que queda fuera del espacio del lactato. Sobrevivió en P2I-2V-R, pero no está en el
  registro docente {5, 6}.
- **Parámetros puntuales de L3:** si la fracción con IBP (0,8) y tras la hemostasia (0,1) deben explorarse antes del
  lactato.
- **Borrador del espacio de entrada:** si se conserva mientras el veredicto sea NOT_READY, o se retira (§6).
