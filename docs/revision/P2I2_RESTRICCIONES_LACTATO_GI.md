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
| Entrega adecuada (minuto *m*) | entrega efectiva del estado al final de *m* ≥ (1 − ε) × demanda de *m*, con ε = 0 | en el modelo, es el límite exacto por debajo del cual se acumula deuda de O2 nueva; no hace falta inventar otro | ε = 5 % y 10 % |
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
    (`lactate_constraints.pipeline_digest`: cómo una corrida del núcleo se vuelve trayectoria y cómo se evalúa la región).
- **Cómo se cumple:**
  - los dos quedaron fijados en `lactate_constraints.py`, en el commit de congelamiento, antes de cualquier filtrado de la
    región;
  - el filtro se niega a correr si alguno cambió;
  - los resultados guardan los dos digests.
- **Lo que se sabía al definirlas:** las tablas agregadas de P2I-1, ya publicadas para la docencia. No se había calculado
  ningún conteo de P2I-2: ni sobrevivientes ni proporciones por decisión.

<!-- generado:restricciones-lactato -->
<!-- /generado:restricciones-lactato -->
