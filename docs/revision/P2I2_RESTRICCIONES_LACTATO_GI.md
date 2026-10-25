# P2I-2 · Restricciones docentes del lactato GI aplicadas a la región candidata

Las decisiones FD-LAC-01 a FD-LAC-06 son las primeras **restricciones clínicas de comportamiento** aprobadas por la
docencia (FACULTY_APPROVED). Restringen lo que puede hacer la trayectoria observable del lactato. **No aprueban ningún
valor de parámetro oculto**:
- `arrival_oxygen_debt`, `arrival_lactate_excess`, τ_D, τ_L, la ganancia D→lactato y la ganancia déficit→D siguen
  CANDIDATE;
- el conjunto que sobrevive al filtro se llama **REGIÓN CANDIDATA RESTRINGIDA POR LA DOCENCIA** (FACULTY-CONSTRAINED
  CANDIDATE REGION) y no es una región aprobada.

Las restricciones viven en `clinical_core/faculty_constraints.py`, separadas de la autoridad de migración, de la
procedencia de los parámetros y del registro de calibración: ninguno de ellos las lee, y una prueba lo comprueba. No se
agregan a los registros de autoridad. GI no se migra, no hay integración en tiempo de ejecución y no se eligió ningún
conjunto final de parámetros.

**Las definiciones operativas de la §2 son una propuesta del núcleo en sombra, no una decisión docente.** Traducen
frases cualitativas a pruebas deterministas. Quedaron congeladas antes de filtrar cualquier candidato (§3) y la docencia
puede corregirlas.

## 1. Las decisiones docentes (texto vigente, citado tal cual)

Registradas el 2026-10-25, versión «FD-LAC v1». El texto que rige es el original, en inglés.

| ID | Observable | Escenarios | Casos | Decisión (texto original) |
|---|---|---|---|---|
| FD-LAC-01 | trayectoria del lactato con sangrado activo y entrega inadecuada | L1 | 57m, 72f | «With ongoing active haemorrhage and persistently inadequate/worsening oxygen delivery, lactate should GENERALLY RISE. A brief period of stability is acceptable. A sustained fall should NOT be the typical trajectory when oxygen delivery remains inadequate. Do NOT interpret this as: "lactate must rise every minute." The clinically important requirement is the trajectory over meaningful reassessment intervals.» |
| FD-LAC-02 | lactato a los 60 min sin tratar | L1 | 57m | «APPROVED clinical band: arrival lactate: 4.4 mmol/L. 60-min untreated acceptable band: 4.4-7.0 mmol/L. Preferred direction: stable-to-rising, usually rising. Do NOT convert the midpoint of this band into a target. Values are a clinical acceptance envelope.» |
| FD-LAC-03 | lactato a los 60 min sin tratar | L1 | 72f | «APPROVED clinical band: arrival lactate: 3.4 mmol/L. 60-min untreated acceptable band: 3.4-5.5 mmol/L. Preferred direction: stable-to-rising, usually rising. Again, this is a clinical envelope, not a point target.» |
| FD-LAC-04 | inicio de una tendencia clara a la baja tras la hemostasia y la restauración sostenida de la entrega | L3 | 57m, 72f | «After successful haemostasis AND adequate sustained restoration of oxygen delivery, a CLEAR downward lactate trend should begin within: 15-30 minutes. This means onset of a meaningful downward trend. It does NOT mean: normalization by 30 minutes; arbitrary fixed mmol/L decline; clearance independent of accumulated debt.» |
| FD-LAC-05 | lactato residual a los 120 min y su dependencia de la deuda acumulada | L3 | 57m, 72f | «Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT encode one fixed 120-min lactate target. The model should preserve memory of prior debt.» |
| FD-LAC-06 | trayectoria del lactato con sangrado activo, según la adecuación de la entrega | L1, L2, L3 | 57m, 72f | «ONLY IF OXYGEN DELIVERY IS ADEQUATE. Active haemorrhage by itself does not require lactate to rise. If resuscitation maintains/restores adequate oxygen delivery despite ongoing bleeding, lactate may fall. However: active bleeding + persistent/worsening inadequate oxygen delivery must NOT produce a sustained declining lactate trajectory. This rule takes precedence over diagnosis labels.» |

Sólo entran trayectorias producidas por el motor: L1 (sin tratar), L2 (2 L de salina en 20 min, el sangrado sigue) y L3
(manejo definitivo; el motor hace la endoscopia en el minuto 60). La composición contrafactual L4 de P2I-1 no entra.

## 2. Definiciones operativas (propuesta del núcleo; congeladas antes de filtrar)

Todo se lee de la trayectoria del propio núcleo, minuto a minuto: el lactato, la entrega efectiva de O2, la demanda de
O2, D y el minuto en que su módulo GI registra la hemostasia. El lactato del motor heredado nunca entra. D nunca reemplaza
a la entrega: «entrega inadecuada» significa entrega bajo la demanda, haga lo que haga D.

### 2.1 Piezas comunes

| Frase | Definición exacta | Fundamento clínico | Sensibilidad |
|---|---|---|---|
| Entrega adecuada (minuto *m*) | entrega efectiva del estado al final de *m* ≥ (1 − ε) × demanda de *m*, con ε = 0 | en el modelo, es el límite por debajo del cual se acumula deuda de O2 nueva; no hace falta inventar otro. El núcleo acumula la deuda de cada minuto con la entrega al comienzo de ese minuto, así que «inadecuada en *m*» equivale a deuda nueva en *m* + 1: un minuto de adelanto. La relectura con la convención del núcleo se informa como robustez (§4.3) y no filtra | ε = 5 % y 10 % |
| Entrega persistentemente inadecuada o en empeoramiento, con sangrado activo | cada tramo máximo de minutos consecutivos en que el sangrado sigue activo (antes de la hemostasia que registra el núcleo) y la entrega es inadecuada en **todos** los minutos | «persistente» = sin un solo minuto adecuado en el tramo; empeorar es un caso particular de seguir inadecuada | por ε |
| Intervalo de reevaluación | la trayectoria se juzga en los dos extremos de cada tramo y en cada múltiplo de 15 min dentro de él | la reevaluación de perfusión en el shock hemorrágico se hace cada pocos minutos; 15 min es la grilla de P2I-1 que la docencia ya leyó. No se exige nada minuto a minuto | 10 y 30 min |
| Cambio clínicamente significativo | 10 % del valor de referencia, siempre relativo y nunca un número fijo de mmol/L | es el umbral convencional de un cambio significativo del lactato (como en «aclaramiento del lactato ≥ 10 %») y supera la variación analítica habitual | 5 % y 20 % |
| Descenso sostenido | dentro de un tramo, dos puntos de reevaluación separados al menos 30 min, con el lactato del posterior ≤ 90 % del anterior | dura dos intervalos de reevaluación seguidos: no es una lectura aislada. Una baja que se recupera antes de 30 min es transitoria | 15, 45 y 60 min |

### 2.2 Cada decisión

**FD-LAC-01 (en L1, para 57m y 72f).** Se aplica a cada tramo de sangrado activo con entrega inadecuada de al menos
60 min. En cada uno:
- **(a)** no hay descenso sostenido;
- **(b) «en general sube»:** el lactato al final del tramo es ≥ 110 % del de su inicio.

La estabilidad se tolera: no se pide que suba ningún intervalo en particular. No se agrega un límite propio para «breve»,
porque FD-LAC-02/03 ya aceptan a los 60 min un valor igual al de llegada. Un límite más corto contradiría esas bandas, y
la estabilidad que dura hasta el final queda excluida por (b). Como sensibilidad, (c) exige que la fase estable termine
hacia arriba en 60 o en 90 min.

Si no hay ningún tramo así, la decisión **no se aplica** y no se cuenta como contradicha. Sensibilidad: contarlo como
falla.

**FD-LAC-02 / FD-LAC-03 (en L1).** Envolventes duras e inclusivas a los 60 min sin tratar:
- 57m: 4,4 ≤ lactato ≤ 7,0;
- 72f: 3,4 ≤ lactato ≤ 5,5.

Se compara el valor exacto del modelo. Nunca se mide la distancia al punto medio. Una corrida que termina antes del
minuto 60 falla. Sensibilidad: comparar el valor redondeado a un decimal, como se muestra.

**FD-LAC-04 (en L3).** El reloj no arranca en el minuto 0.
- **El disparador T\*** es el primer minuto desde la hemostasia que registra el núcleo (en L3, el 60) a partir del cual la
  entrega se mantiene adecuada durante 30 min seguidos. Nunca es antes de la hemostasia ni mientras la entrega siga
  inadecuada: si no está restaurada en la hemostasia, el reloj espera.
- **La tendencia empieza** en el pico posterior a T\*, es decir, el último minuto del lactato más alto entre T\* y el
  final. Desde ahí el lactato sólo queda por debajo. Si ya venía bajando, el pico es T\* mismo; en una meseta, la caída
  empieza al terminarla.
- **La tendencia es clara** cuando el lactato al final es ≤ 90 % del pico. Es una caída relativa y sostenida, sin un
  número fijo de mmol/L ni un plazo para normalizarse.
- **Pasa** si la tendencia es clara y empieza ≤ 30 min después de T\*. Un comienzo antes de los 15 min, o una baja que ya
  estaba en curso, no contradice «within 15-30 minutes».

No es evaluable, y no se cuenta como contradicha, si:
- no hay hemostasia con restauración sostenida;
- quedan menos de 60 min de observación después de T\*;
- el lactato en T\* ya está ≤ 2,0 mmol/L, el límite superior normal, porque no queda lactato elevado que aclarar.

Sensibilidad:
- comienzo ≤ 15 o ≤ 45 min;
- sólo entre 15 y 30 min;
- restauración sostenida durante 15 o 60 min;
- lo no evaluable contado como falla.

**FD-LAC-05 (en L3).** No se aplica una banda numérica a los 120 min, porque no hay ninguna aprobada.
- **(a) Memoria material de la deuda.** El lactato que una deuda de llegada grave (60, el extremo alto de la banda de P2F
  en ambos casos) todavía deja en el minuto 120 debe ser ≥ 10 % del lactato de llegada. Ese término es el exacto de las
  recurrencias del núcleo: depende de τ_D, τ_L y G, y no de la entrega, así que la restauración del flujo no lo borra.
- **(b) Sin normalización inmediata.** Un lactato claramente sobre 2,0 mmol/L en T\* (≥ 2,2) no llega a ≤ 2,0 en los
  15 min siguientes.

Nunca se exige normalizar, y un lactato que sigue elevado a los 120 min nunca es una falla. Sensibilidad: deuda de
referencia 20, y cambio significativo del 5 % o del 20 %.

**FD-LAC-06 (en L1, L2 y L3, para 57m y 72f).** En todo tramo de sangrado activo con entrega inadecuada de al menos
30 min, no hay descenso sostenido. Con entrega adecuada el lactato puede bajar aunque se siga sangrando. La regla se lee
de la entrega, nunca del diagnóstico.

Un candidato sobrevive a una decisión cuando la cumple en todos los casos en que se aplica, y a todas cuando cumple las
seis.

### 2.3 Disociación D–lactato (P2I-2.7)

Se revisan los casos de P2I-1 en que D sube mientras el lactato baja (L1, de 0 a 60 y de 0 a 120 min):
- **B INACEPTABLE:** dentro del lapso hay un descenso sostenido en un tramo de sangrado activo con entrega inadecuada. Es
  lo que FD-LAC-01/06 prohíben.
- **A ACEPTABLE:** si no es B, y el lactato sólo baja en minutos con entrega adecuada.
- **C TRANSITORIA O AMBIGUA:** el resto. El lactato baja con entrega inadecuada, pero demasiado poco o demasiado breve
  para ser un descenso sostenido.

### 2.4 Reglas de informe, también congeladas

Su texto es el del commit de congelamiento. El digest de informe (§3) se fijó después de la primera corrida, sobre ese
mismo texto sin cambios, y el filtro se niega a correr si cambia.

- **Identificabilidad, por parámetro, con los niveles que sobreviven:**
  - NO IDENTIFICADO: la región no lo varía, o la proporción de cada nivel cambia ≤ 5 puntos;
  - POCO IDENTIFICADO: sobreviven todos los niveles, pero con un cambio mayor;
  - PARCIALMENTE RESTRINGIDO: se elimina algún nivel;
  - BIEN RESTRINGIDO: queda un solo nivel, dentro de la grilla explorada.
  - Nunca se destaca el nivel más frecuente.
- **Representantes:** entre los candidatos que cumplen las seis, por caso, el más bajo, la mediana y el más alto del
  lactato a los 60 min en L1 y del lactato a los 120 min en L3. Los empates se rompen por la clave del candidato.
- **Referencia heredada:** se ubica después del filtro y nunca entra en él.

## 3. Congelamiento antes de filtrar

- **Digests congelados:**
  - definiciones: `ee1deb2578504d3c295d2c4a3552b2d781529064f94043f99b07f04d0fe258cc`
    (`faculty_constraints.definitions_digest`, el módulo completo);
  - canalización: `4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394`
    (`lactate_constraints.pipeline_digest`: cómo una corrida del núcleo se vuelve trayectoria y cómo se evalúa la región);
  - reglas de informe: `1b9e70365f7deea79733b3cbc59aa07abc5177fd4c81358853b951a70c723991`
    (`lactate_constraints.reporting_digest`: conteos, disociación, región e identificabilidad, representantes y
    sensibilidad). Se fijó después de la primera corrida, cuando la revisión adversarial notó que la §2.4 se declaraba
    congelada sin un digest. Es el digest del mismo texto de `9301a6a`, que no cambió.
- **Cómo se cumple:**
  - los dos quedaron fijados en `lactate_constraints.py` en el commit de congelamiento `9301a6a`, antes de cualquier
    filtrado de la región. Los resultados de la §4 se calcularon después y se agregaron en un commit posterior;
  - el filtro se niega a correr si alguno cambió;
  - los resultados guardan los dos digests.
- **Lo que se sabía al definirlas:** las tablas agregadas de P2I-1, ya publicadas para la docencia. No se había calculado
  ningún conteo de P2I-2: ni sobrevivientes ni proporciones por decisión.

<!-- generado:restricciones-lactato -->
## 4. Resultados (región admisible de P2F, sin candidatos nuevos)

Generado desde el filtro `5c72a62b19a18ee1841407821cb59f77100570448b965b79a951ccce5b585419` con las definiciones congeladas `ee1deb2578504d3c295d2c4a3552b2d781529064f94043f99b07f04d0fe258cc`, la canalización `4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394` y las reglas de informe `1b9e70365f7deea79733b3cbc59aa07abc5177fd4c81358853b951a70c723991`, sobre el congelamiento de calibración `152abc6cf3e2812fcade237f60db0430df78749e09f4199b0a0fff13a0dd4338`. Los números están en `docs/revision/P2I2_lactate_constraints.json`.

### 4.1 Sobrevivientes

| | Candidatos | Elimina | Elimina ella sola | Sobreviven sin ella |
|---|---|---|---|---|
| Antes del filtro | 1054 | | | |
| FD-LAC-01 | 234 (22 %) | 820 | 9 | 75 |
| FD-LAC-02 | 243 (23 %) | 811 | 6 | 72 |
| FD-LAC-03 | 306 (29 %) | 748 | 24 | 90 |
| FD-LAC-04 | 808 (77 %) | 246 | 87 | 153 |
| FD-LAC-05 | 862 (82 %) | 192 | 0 | 66 |
| FD-LAC-06 | 312 (30 %) | 742 | 12 | 78 |
| **Las seis juntas** | **66 (6 %)** | | | |

«Elimina ella sola»: candidatos que fallan sólo esa decisión. «Sobreviven sin ella»: los que cumplen las otras cinco. Por caso:

| Caso | FD-LAC-01 | FD-LAC-02/03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | FD-LAC-01 no aplicable | FD-LAC-04 no evaluable |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 234 | 243 (FD-LAC-02) | 928 | 862 | 312 | 0 | lactato ≤ 2,0 mmol/L en el disparador: 75 |
| gi_bleed_72f | 333 | 306 (FD-LAC-03) | 808 | 937 | 456 | 0 | lactato ≤ 2,0 mmol/L en el disparador: 102 |

### 4.2 Sensibilidad (una definición por vez)

| Variante | FD-LAC-01 | FD-LAC-02 | FD-LAC-03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | Las seis |
|---|---|---|---|---|---|---|---|
| **Definición principal** | 234 | 243 | 306 | 808 | 862 | 312 | **66** |
| cambio significativo 5 % | 234 | 243 | 306 | 970 | 1036 | 210 | 84 |
| cambio significativo 20 % | 195 | 243 | 306 | 390 | 658 | 540 | 30 |
| tolerancia de adecuación 5 % | 234 | 243 | 306 | 808 | 862 | 333 | 72 |
| tolerancia de adecuación 10 % | 231 | 243 | 306 | 808 | 862 | 351 | 72 |
| reevaluación cada 10 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| reevaluación cada 30 min | 234 | 243 | 306 | 808 | 862 | 318 | 69 |
| sostenido en 15 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| sostenido en 45 min | 243 | 243 | 306 | 808 | 862 | 318 | 72 |
| sostenido en 60 min | 255 | 243 | 306 | 808 | 862 | 336 | 81 |
| FD-LAC-01: lo no aplicable cuenta como falla | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| FD-LAC-01: la estabilidad termina, hacia arriba, en 60 min | 162 | 243 | 306 | 808 | 862 | 312 | 42 |
| FD-LAC-01: la estabilidad termina, hacia arriba, en 90 min | 195 | 243 | 306 | 808 | 862 | 312 | 57 |
| FD-LAC-02/03 con el valor redondeado a un decimal | 234 | 264 | 330 | 808 | 862 | 312 | 75 |
| FD-LAC-04: comienzo ≤ 15 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| FD-LAC-04: comienzo ≤ 45 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| FD-LAC-04: comienzo sólo entre 15 y 30 min | 234 | 243 | 306 | 75 | 862 | 312 | 0 |
| FD-LAC-04: restauración sostenida 15 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| FD-LAC-04: restauración sostenida 60 min | 234 | 243 | 306 | 808 | 862 | 312 | 66 |
| FD-LAC-04: lo no evaluable cuenta como falla | 234 | 243 | 306 | 706 | 862 | 312 | 66 |
| FD-LAC-05: deuda de referencia 20 | 234 | 243 | 306 | 808 | 514 | 312 | 66 |

### 4.3 FD-LAC-01 y FD-LAC-04 en detalle

**FD-LAC-01: por qué falla** (información para la docencia; no filtra)

| Caso | Con descenso sostenido | Sin descenso sostenido, pero sin subir ≥ 10 % hacia el final | De esos, dentro de la envolvente FD-LAC-02/03 |
|---|---|---|---|
| gi_bleed_57m | 688 | 132 | 36 |
| gi_bleed_72f | 562 | 159 | 48 |

**FD-LAC-04: cuándo arranca el reloj y cuándo se ve la caída**

| Caso | Disparador T* (minuto: corridas) | Primer minuto con entrega adecuada en L3 | Comienzo de la tendencia tras T* | La caída llega al 10 % | Sin tendencia clara | Fuera de plazo |
|---|---|---|---|---|---|---|
| gi_bleed_57m | 60: 1054 | desde la llegada: 405, min 1–30: 244, min 31–59: 405 | en T* (+0 min): 937, +1–14 min: 30, +15–30 min: 9, +31 min o más: 3 | ≤ +30 min: 424, +31–45 min: 327, +46–60 min: 102, no la alcanza: 126 | 126 | 3 |
| gi_bleed_57m, región restringida | | desde la llegada: 9, min 1–30: 36, min 31–59: 21 | en T* (+0 min): 66 | ≤ +30 min: 36, +31–45 min: 30 | | |
| gi_bleed_72f | 60: 1054 | desde la llegada: 405, min 1–30: 244, min 31–59: 405 | en T* (+0 min): 859, +1–14 min: 42, +15–30 min: 30, +31 min o más: 21 | ≤ +30 min: 304, +31–45 min: 195, +46–60 min: 207, no la alcanza: 246 | 246 | 21 |
| gi_bleed_72f, región restringida | | desde la llegada: 9, min 1–30: 36, min 31–59: 21 | en T* (+0 min): 66 | ≤ +30 min: 27, +31–45 min: 21, +46–60 min: 18 | | |

En L3 la transfusión restaura la entrega antes de la hemostasia, así que en casi todas las corridas el lactato ya baja cuando arranca el reloj (comienzo en T*). La definición principal juzga si la tendencia es clara al final de la corrida, no dentro de los 15–30 min: la columna «La caída llega al 10 %» muestra cuándo se alcanza. Es una decisión pendiente para la docencia.

**Robustez de la convención de minuto (no filtra).** El núcleo acumula la deuda de cada minuto con la entrega al comienzo de ese minuto; la definición congelada lee la entrega al final del minuto, uno antes. Releyendo todas las corridas con la entrega al comienzo del minuto: FD-LAC-01 231, FD-LAC-02 243, FD-LAC-03 306, FD-LAC-04 808, FD-LAC-05 862, FD-LAC-06 312; las seis juntas, 66; candidatos que cambian de grupo, 0.

### 4.4 FD-LAC-05: memoria de la deuda (sin banda numérica)

| Caso | Lactato que deja una deuda de 60 a los 120 min (región) | Pares de la región: más deuda → más lactato residual | Mediana del residual de los sobrevivientes por deuda de llegada | Residual de los sobrevivientes | Sobrevivientes > 2,0 mmol/L a los 120 min | Normalizaciones bruscas (región) |
|---|---|---|---|---|---|---|
| gi_bleed_57m | 0,24 a 3,15 | 324 de 324 | inferior 3,22, medio 3,21, superior 3,81 | 1,88 a 4,92 | 63 de 66 | 6 |
| gi_bleed_72f | 0,24 a 3,15 | 324 de 324 | inferior 2,79, medio 2,86, superior 3,77 | 1,82 a 4,55 | 63 de 66 | 0 |

### 4.5 Disociación D–lactato de P2I-1, reclasificada

| Caso | Patrón | Región: A aceptable | B inaceptable | C transitoria | Región restringida: A | B | C |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 0 | 531 | 111 | 0 | 0 | 0 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 0 | 517 | 60 | 0 | 0 | 0 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 0 | 378 | 129 | 0 | 0 | 0 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 0 | 397 | 45 | 0 | 0 | 0 |

En la región restringida los ceros son por construcción, no un hallazgo aparte: el patrón de 0–60 min exige un lactato a los 60 min bajo el de llegada, que FD-LAC-02/03 excluyen, y el de 0–120 min lo excluye FD-LAC-01(b). No hay ningún caso A: en L1 la entrega nunca es adecuada mientras el lactato baja.

### 4.6 Región candidata restringida por la docencia (sigue CANDIDATE)

| Parámetro | Niveles: región → sobrevivientes | Rango P2F (57m; 72f) | Rango tras FD-LAC (57m; 72f) | Identificabilidad |
|---|---|---|---|---|
| `arrival_oxygen_debt` | inferior (0/0): 486 → 6; medio (20/20): 244 → 36; superior (60/60): 324 → 24 | 0,00–60,00; 0,00–60,00 | 0,00–60,00; 0,00–60,00 | POCO IDENTIFICADO |
| `arrival_lactate_excess` | inferior (2,4/1,4): 351 → 12; medio (3,4/2,4): 352 → 27; superior (3,6/2,6): 351 → 27 | 2,40–3,60; 1,40–2,60 | 2,40–3,60; 1,40–2,60 | POCO IDENTIFICADO |
| τ_D `debt_clearance_tau_min` | 30 (30/30): 243 → 27; 60 (60/60): 406 → 30; 120 (120/120): 405 → 9 | 30,00–120,00; 30,00–120,00 | 30,00–120,00; 30,00–120,00 | POCO IDENTIFICADO |
| ganancia déficit→D `debt_per_delivery_deficit` | 1 (1/1): 1054 → 66 | 1,00–1,00; 1,00–1,00 | 1,00–1,00; 1,00–1,00 | NO IDENTIFICADO |
| ganancia D→lactato G `lactate_per_output_deficit` | 2 (2/2): 351 → 0; 6 (6/6): 352 → 15; 12 (12/12): 351 → 51 | 2,00–12,00; 2,00–12,00 | 6,00–12,00; 6,00–12,00 | PARCIALMENTE RESTRINGIDO |
| τ_L `lactate_clearance_tau_min` | 45 (45/45): 351 → 30; 120 (120/120): 352 → 27; 240 (240/240): 351 → 9 | 45,00–240,00; 45,00–240,00 | 45,00–240,00; 45,00–240,00 | POCO IDENTIFICADO |
| `arrival_delivery_ratio` | inferior (0,6/0,6): 405 → 21; medio (0,85/0,85): 244 → 36; superior (1/1): 405 → 9 | 0,60–1,00; 0,60–1,00 | 0,60–1,00; 0,60–1,00 | POCO IDENTIFICADO |
| `metabolic_demand_baseline` | fijo (1/1): 1054 → 66 | 1,00–1,00; 1,00–1,00 | 1,00–1,00; 1,00–1,00 | NO IDENTIFICADO |

### 4.7 Trayectorias representativas de la región restringida

**gi_bleed_57m · sin tratar (L1), por el lactato a los 60 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 0, exceso 3,4, entrega 0,60, τ_D 30, G 12, τ_L 240 | 4,40 (D 0; entrega 0,60, inadecuada) | 4,26 (D 5; entrega 0,54, inadecuada) | 4,23 (D 9; entrega 0,48, inadecuada) | 4,41 (D 15; entrega 0,35, inadecuada) | 4,81 (D 19; entrega 0,22, inadecuada) | 5,36 (D 23; entrega 0,10, inadecuada) | tramo inadecuado 0–120 |
| mediana | deuda 60, exceso 3,4, entrega 0,60, τ_D 60, G 6, τ_L 120 | 4,40 (D 60; entrega 0,60, inadecuada) | 4,66 (D 52; entrega 0,54, inadecuada) | 4,82 (D 47; entrega 0,48, inadecuada) | 4,96 (D 43; entrega 0,35, inadecuada) | 5,02 (D 43; entrega 0,22, inadecuada) | 5,11 (D 46; entrega 0,10, inadecuada) | tramo inadecuado 0–120 |
| más alto | deuda 60, exceso 3,6, entrega 1,00, τ_D 60, G 12, τ_L 120 | 4,40 (D 60; entrega 1,00) | 5,24 (D 47; entrega 0,90, inadecuada) | 5,73 (D 39; entrega 0,79, inadecuada) | 6,15 (D 31; entrega 0,58, inadecuada) | 6,32 (D 31; entrega 0,37, inadecuada) | 6,58 (D 36; entrega 0,16, inadecuada) | tramo inadecuado 1–120 |

**gi_bleed_57m · manejo definitivo (L3), por el lactato a los 120 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 20, exceso 3,6, entrega 0,85, τ_D 30, G 12, τ_L 45 | 4,40 (D 20; entrega 0,85, inadecuada) | 5,22 (D 13; entrega 1,11) | 5,08 (D 8; entrega 1,36) | 3,87 (D 3; entrega 1,84) | 2,69 (D 1; entrega 1,82) | 1,88 (D 0; entrega 1,81) | hemostasia 60, T* 60, comienzo 60 (+0 min) |
| mediana | deuda 0, exceso 2,4, entrega 0,60, τ_D 30, G 12, τ_L 120 | 4,40 (D 0; entrega 0,60, inadecuada) | 4,22 (D 4; entrega 0,78, inadecuada) | 4,14 (D 4; entrega 0,96, inadecuada) | 3,87 (D 1; entrega 1,30) | 3,53 (D 0; entrega 1,29) | 3,22 (D 0; entrega 1,27) | hemostasia 60, T* 60, comienzo 60 (+0 min) |
| más alto | deuda 60, exceso 3,6, entrega 1,00, τ_D 60, G 12, τ_L 120 | 4,40 (D 60; entrega 1,00) | 5,23 (D 47; entrega 1,31) | 5,69 (D 36; entrega 1,60) | 5,86 (D 22; entrega 2,16) | 5,50 (D 13; entrega 2,14) | 4,92 (D 8; entrega 2,12) | hemostasia 60, T* 60, comienzo 60 (+0 min) |

**gi_bleed_72f · sin tratar (L1), por el lactato a los 60 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 0, exceso 2,4, entrega 0,60, τ_D 30, G 12, τ_L 240 | 3,40 (D 0; entrega 0,60, inadecuada) | 3,32 (D 5; entrega 0,55, inadecuada) | 3,34 (D 9; entrega 0,51, inadecuada) | 3,60 (D 14; entrega 0,42, inadecuada) | 4,01 (D 17; entrega 0,33, inadecuada) | 4,53 (D 20; entrega 0,23, inadecuada) | tramo inadecuado 0–120 |
| mediana | deuda 20, exceso 2,6, entrega 0,85, τ_D 30, G 12, τ_L 120 | 3,40 (D 20; entrega 0,85, inadecuada) | 3,89 (D 14; entrega 0,79, inadecuada) | 4,13 (D 12; entrega 0,72, inadecuada) | 4,35 (D 11; entrega 0,59, inadecuada) | 4,62 (D 13; entrega 0,46, inadecuada) | 5,09 (D 16; entrega 0,33, inadecuada) | tramo inadecuado 0–120 |
| más alto | deuda 60, exceso 2,6, entrega 1,00, τ_D 60, G 12, τ_L 120 | 3,40 (D 60; entrega 1,00) | 4,36 (D 47; entrega 0,92, inadecuada) | 4,94 (D 38; entrega 0,85, inadecuada) | 5,47 (D 29; entrega 0,69, inadecuada) | 5,63 (D 26; entrega 0,54, inadecuada) | 5,77 (D 29; entrega 0,39, inadecuada) | tramo inadecuado 1–120 |

**gi_bleed_72f · manejo definitivo (L3), por el lactato a los 120 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 20, exceso 2,6, entrega 0,85, τ_D 30, G 12, τ_L 45 | 3,40 (D 20; entrega 0,85, inadecuada) | 4,52 (D 13; entrega 1,04) | 4,60 (D 8; entrega 1,22) | 3,64 (D 3; entrega 1,57) | 2,57 (D 1; entrega 1,55) | 1,82 (D 0; entrega 1,54) | hemostasia 60, T* 60, comienzo 60 (+0 min) |
| mediana | deuda 0, exceso 1,4, entrega 0,60, τ_D 30, G 12, τ_L 120 | 3,40 (D 0; entrega 0,60, inadecuada) | 3,34 (D 4; entrega 0,73, inadecuada) | 3,40 (D 5; entrega 0,86, inadecuada) | 3,41 (D 2; entrega 1,11) | 3,23 (D 1; entrega 1,10) | 3,00 (D 0; entrega 1,09) | hemostasia 60, T* 60, comienzo 60 (+0 min) |
| más alto | deuda 60, exceso 2,6, entrega 1,00, τ_D 60, G 12, τ_L 120 | 3,40 (D 60; entrega 1,00) | 4,35 (D 47; entrega 1,22) | 4,91 (D 36; entrega 1,44) | 5,26 (D 22; entrega 1,84) | 5,03 (D 13; entrega 1,83) | 4,55 (D 8; entrega 1,81) | hemostasia 60, T* 60, comienzo 60 (+0 min) |

### 4.8 REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN

Se ubica después del filtro y nunca entró en él. El motor de familias no tiene una entrega de O2 como la del núcleo, así que sólo se ubican las partes que dependen del lactato.

| Caso | Sin tratar: 0, 15, 30, 60, 90, 120 min | A los 60 min, frente a la envolvente | Sube ≥ 10 % hacia los 120 min | Descensos sostenidos | Manejo definitivo: 0, 15, 30, 60, 90, 120 min | Tras su endoscopia (min 60) |
|---|---|---|---|---|---|---|
| gi_bleed_57m | 4,4; 4,5; 4,6; 4,8; 4,9; 5,1 | 4,8: dentro de 4,4–7,0 | sí | 0 | 4,4; 4,1; 3,8; 3,2; 3,3; 3,3 | sin comienzo de una tendencia a la baja: el pico (regla congelada) es el minuto 120 |
| gi_bleed_72f | 3,4; 3,5; 3,6; 3,8; 3,9; 4,1 | 3,8: dentro de 3,4–5,5 | sí | 0 | 3,4; 3,1; 2,8; 2,2; 2,3; 2,3 | sin comienzo de una tendencia a la baja: el pico (regla congelada) es el minuto 120 |

<!-- /generado:restricciones-lactato -->

## 5. Limitaciones y decisiones pendientes

- **FD-LAC-04 no puede probar la ventana de 15–30 min con L3.** En L3, la transfusión restaura la entrega antes de la
  hemostasia del minuto 60, así que en casi todas las corridas el lactato ya baja cuando arranca el reloj. La definición
  principal juzga si la tendencia es clara al final de la corrida. Hace falta que la docencia decida si «clara» debe
  verse dentro de los 15–30 min (§4.3). Para aislar el tiempo hace falta un escenario con la restauración en el momento
  de la hemostasia, que no existe todavía.
- **FD-LAC-01 (b) «en general sube»** exige subir al menos un 10 % hacia el final. Elimina candidatos que están dentro de
  la envolvente de FD-LAC-02/03 y nunca tienen un descenso sostenido (§4.3). La docencia puede confirmar o corregir esa
  lectura.
- **FD-LAC-05 necesitará una banda numérica.** «Levemente elevado» no se puede verificar sin una; hoy sólo se comprueba
  la memoria de la deuda y la ausencia de normalización brusca.
- **Lo no evaluable:**
  - con la hemostasia en el minuto 60 y corridas de 120 min, un disparador posterior al 60 cae en «poca observación» y
    no se cuenta como contradicción;
  - una corrida demasiado corta para sostener la restauración se rotula como «sin hemostasia con restauración
    sostenida».
  - Hoy no ocurre ninguna de las dos (T\* = 60 en todas las corridas), pero hay que revisarlo si cambian los escenarios.
- **Las definiciones operativas son una propuesta** del núcleo y quedan sujetas a confirmación docente. Cambiarlas exige
  un recongelamiento documentado.
