# P2I-2R · Restricciones docentes del lactato GI, aclaradas, aplicadas a la región candidata

> **PENDIENTE DE REFILTRADO (desde 2026-10-27).** Los resultados de §4 se filtraron con el núcleo anterior a P2I-2P
> (filtro `58e988cf6b1c3d5bebab254305fdeec97ace1c11775db4753b458781a888d1bb`) y quedan tal como se comprometieron. La
> docencia detuvo el filtrado («Do NOT continue filtering P2I-2R yet») hasta revisar la fisiología de entrega y extracción
> de O2 (P2I-2P, `docs/revision/P2I2P_FISIOLOGIA_ENTREGA_O2.md`) y operacionalizar la decisión FD-LAC-06 sobre la
> trayectoria (entrega persistente o en empeoramiento frente a recuperación todavía bajo el umbral). P2I-2P no cambia
> ninguna cifra canónica (reserva de extracción neutra 1), pero sí las fuentes del núcleo: el resumen de filtrado actual ya
> no coincide, y `python -m clinical_core.lactate_constraints` rehúsa producir resultados nuevos hasta que se autorice el
> refiltrado (`RESULTS_PENDING_REFILTER`).

Las decisiones FD-LAC-01 a FD-LAC-06 son **restricciones clínicas de comportamiento** aprobadas por la docencia
(FACULTY_APPROVED). Restringen lo que puede hacer la trayectoria observable del lactato. **No aprueban ningún valor de
parámetro oculto**:
- `arrival_oxygen_debt`, `arrival_lactate_excess`, τ_D, τ_L, la ganancia D→lactato y la ganancia déficit→D siguen
  CANDIDATE;
- el conjunto que sobrevive se llama **REGIÓN CANDIDATA RESTRINGIDA POR LA DOCENCIA** (FACULTY-CONSTRAINED CANDIDATE
  REGION) y no es una región aprobada.

Las restricciones viven en `clinical_core/faculty_constraints.py`, separadas de la autoridad de migración, de la
procedencia de los parámetros y del registro de calibración: ninguno de ellos las lee, y una prueba lo comprueba. No se
agregan a los registros de autoridad. GI no se migra, no hay integración en tiempo de ejecución y no se eligió ningún
conjunto final de parámetros.

**P2I-2R.** El 2026-10-26 la docencia aclaró FD-LAC-01, FD-LAC-04 y FD-LAC-05 (§1) y confirmó las definiciones operativas
comunes. Estos cambios son una aclaración docente de enunciados ya aprobados. No son reglas elegidas a partir del
resultado de P2I-2, que había dejado 66 sobrevivientes (§6). Las definiciones aclaradas se congelaron en un commit propio
antes de volver a filtrar (§3).

**Propósito, según la docencia:** el modelo debe reproducir la dirección fisiológica y la memoria sin hacer del lactato un
sustituto determinista exacto de la entrega de O2. El lactato conserva su propia dinámica de producción y aclaramiento, y
D y lactato no se funden en una sola variable.

## 1. Decisiones docentes y aclaraciones (texto vigente, citado tal cual)

Decididas el 2026-10-25 y aclaradas el 2026-10-26, versión «FD-LAC v2». El texto que rige es el original, en inglés.

| ID | Observable | Escenarios | Casos | Decisión (texto original) | Aclaración del 2026-10-26 (texto original) |
|---|---|---|---|---|---|
| FD-LAC-01 | trayectoria del lactato antes de los 60 min con sangrado activo y entrega inadecuada | L1 | 57m, 72f | «With ongoing active haemorrhage and persistently inadequate/worsening oxygen delivery, lactate should GENERALLY RISE. A brief period of stability is acceptable. A sustained fall should NOT be the typical trajectory when oxygen delivery remains inadequate. Do NOT interpret this as: "lactate must rise every minute." The clinically important requirement is the trajectory over meaningful reassessment intervals.» | «Do NOT encode: L60 >= L0 as a universal physiological law. Faculty intent is: With active haemorrhage AND persistent/significant inadequate oxygen delivery, a substantial sustained fall in lactate should not be the dominant/acceptable trajectory. Lactate should generally remain elevated or rise. The case-specific 60-min clinical envelopes remain: 57m: 4.4-7.0 mmol/L 72f: 3.4-5.5 mmol/L These envelopes are the hard 60-min clinical constraints. For the trajectory before 60 min: retain the approved rule against a sustained substantial decline during persistent inadequate delivery. Do not require monotonic rise. Do not require a fixed percentage increase. Do not treat a small transient decrease as automatically physiologically invalid. Operationalize "substantial sustained decline" using the previously frozen clinically meaningful reassessment-window concept and expose sensitivity to the chosen percentage threshold.» |
| FD-LAC-02 | lactato a los 60 min sin tratar | L1 | 57m | «APPROVED clinical band: arrival lactate: 4.4 mmol/L. 60-min untreated acceptable band: 4.4-7.0 mmol/L. Preferred direction: stable-to-rising, usually rising. Do NOT convert the midpoint of this band into a target. Values are a clinical acceptance envelope.» | sin cambios |
| FD-LAC-03 | lactato a los 60 min sin tratar | L1 | 72f | «APPROVED clinical band: arrival lactate: 3.4 mmol/L. 60-min untreated acceptable band: 3.4-5.5 mmol/L. Preferred direction: stable-to-rising, usually rising. Again, this is a clinical envelope, not a point target.» | sin cambios |
| FD-LAC-04 | lactato en T\* + 30 min frente a T\* | L3 | 57m, 72f | «After successful haemostasis AND adequate sustained restoration of oxygen delivery, a CLEAR downward lactate trend should begin within: 15-30 minutes. This means onset of a meaningful downward trend. It does NOT mean: normalization by 30 minutes; arbitrary fixed mmol/L decline; clearance independent of accumulated debt.» | «T* = the later of: A. haemostasis B. onset of adequate oxygen delivery that remains adequate for the required sustained period. Lactate may already be falling before T*; do not require a new peak after T*; do not reset physiology at haemostasis; use L(T*) as the reference; if the run does not provide 30 min of follow-up, mark NOT_EVALUABLE; if oxygen delivery ceases to be adequate during the 30-min interval, mark NOT_EVALUABLE rather than FAIL. Do NOT require: L(T* + 30) <= 0.90 * L(T*) as a faculty-approved physiological constant. Faculty intent is: After haemostasis AND sustained adequate restoration of oxygen delivery, a clearly downward lactate trajectory should be evident within 30 minutes. Therefore: by T* + 30 min: L(T* + 30) < L(T*) with a trajectory consistent with ongoing clearance. A fixed 10% reduction at 30 min is NOT yet faculty-approved. Report the actual percentage reduction at 30 min for each surviving candidate. Then separately evaluate candidate thresholds such as: any decrease, >=5%, >=10%, >=15% as SENSITIVITY ANALYSIS ONLY. If L(T*) <= 2.0 mmol/L: classify ALREADY_NORMALIZED and satisfy/not-applicable.» |
| FD-LAC-05 | lactato a los 120 min tras el manejo definitivo, con entrega adecuada sostenida | L3 | 57m, 72f | «Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT encode one fixed 120-min lactate target. The model should preserve memory of prior debt.» | «Faculty now approves case-specific 120-min clinical envelopes after successful definitive management with sustained adequate oxygen delivery. 57m: 1.5 <= L120 <= 4.0 mmol/L 72f: 1.2 <= L120 <= 3.5 mmol/L Additionally: L120 < L(T*) must hold when adequate oxygen delivery remained sustained after T*. These are clinical acceptance envelopes, NOT target values. Do not tune toward the midpoint. A value below 2 mmol/L is allowed. Normalization by 120 min is NOT required. Treat these as faculty clinical calibration envelopes for the current GI cases, not universal human physiological limits.» |
| FD-LAC-06 | trayectoria del lactato con sangrado activo, según la adecuación de la entrega | L1, L2, L3 | 57m, 72f | «ONLY IF OXYGEN DELIVERY IS ADEQUATE. Active haemorrhage by itself does not require lactate to rise. If resuscitation maintains/restores adequate oxygen delivery despite ongoing bleeding, lactate may fall. However: active bleeding + persistent/worsening inadequate oxygen delivery must NOT produce a sustained declining lactate trajectory. This rule takes precedence over diagnosis labels.» | sin cambios |

**Definiciones operativas confirmadas por la docencia (2026-10-26, texto original):**
- «inadequate delivery = oxygen delivery < oxygen demand»;
- «evaluation should use clinically meaningful reassessment intervals rather than minute-to-minute noise»;
- «sustained decline during inadequate delivery may be operationalized as a >=10% decline over a >=30-min interval»;
- «FD-LAC-06 applies according to physiology, not diagnosis label»;
- «active bleeding may coexist with falling lactate ONLY when delivery is adequate»;
- «D and lactate remain distinct state/observable concepts»;
- «arrival need not be steady state».

Sólo entran trayectorias producidas por el motor: L1 (sin tratar), L2 (2 L de salina en 20 min, el sangrado sigue) y L3
(manejo definitivo; el motor hace la endoscopia en el minuto 60). La composición contrafactual L4 de P2I-1 no entra.

## 2. Definiciones operativas (congeladas antes de filtrar)

Todo se lee de la trayectoria del propio núcleo, minuto a minuto: el lactato, la entrega efectiva de O2, la demanda de
O2, D y el minuto en que su módulo GI registra la hemostasia. El lactato del motor heredado nunca entra. D nunca reemplaza
a la entrega y el lactato no se lee como un sustituto de la entrega.

Cada pieza indica su origen:
- **docente:** fijada por la decisión, la aclaración o la confirmación;
- **propuesta:** elegida por el núcleo en sombra y sujeta a confirmación docente.

### 2.1 Piezas comunes

| Pieza | Definición exacta | Origen | Sensibilidad |
|---|---|---|---|
| Entrega adecuada (minuto *m*) | entrega efectiva del estado al final de *m* ≥ demanda de *m* | docente (entrega < demanda es inadecuada). El núcleo acumula la deuda de cada minuto con la entrega al comienzo de ese minuto; la relectura con esa convención se informa como robustez y no filtra | tolerancia de 5 % y 10 % |
| Entrega persistentemente inadecuada con sangrado activo | cada tramo máximo de minutos consecutivos con el sangrado activo (antes de la hemostasia que registra el núcleo) y la entrega inadecuada en **todos** los minutos | propuesta | por la tolerancia |
| Intervalo de reevaluación | la trayectoria se juzga en los dos extremos de cada tramo y en cada múltiplo de 15 min dentro de él; nada minuto a minuto | docente (intervalos de reevaluación); 15 min es propuesta | 10 y 30 min |
| Descenso sostenido y sustancial | dentro de un tramo, dos puntos de reevaluación separados al menos 30 min, con el lactato del posterior ≤ 90 % del anterior. Una baja menor, o que se recupera antes de 30 min, no lo es | docente (≥ 10 % en ≥ 30 min) | umbral de 5 %, 15 % y 20 %; lapso de 15, 45 y 60 min |

### 2.2 Cada decisión

**FD-LAC-01 (en L1, para 57m y 72f).**
- **Prueba:** hasta el minuto 60, en cada parte de un tramo de sangrado activo con entrega inadecuada que dure al menos
  30 min, no hay un descenso sostenido y sustancial. FD-LAC-01 no exige subir, ni una subida mínima, ni `L60 ≥ L0`.
  Pero como el límite inferior de las envolventes de FD-LAC-02/03 es el lactato de llegada, L60 ≥ L0 sí rige de hecho
  en estos dos casos a través de esas envolventes duras. FD-LAC-01 no elimina a nadie por sí sola (§4.1), porque lo que
  prohíbe también lo prohíbe FD-LAC-06.
- **Qué pasa con el minuto 60 y después:** el valor de los 60 min lo juzgan las envolventes duras de FD-LAC-02/03. Después
  de los 60 min, la misma prohibición la aplica FD-LAC-06.
- **Sin un tramo así:** NOT_APPLICABLE, que no cuenta como contradicción. Sensibilidad: contarlo como falla.

**FD-LAC-02 / FD-LAC-03 (en L1), docentes.** Envolventes duras e inclusivas a los 60 min sin tratar:
- 57m: 4,4 ≤ L60 ≤ 7,0;
- 72f: 3,4 ≤ L60 ≤ 5,5.

Se compara el valor exacto del modelo, nunca la distancia al punto medio. Una corrida que termina antes del minuto 60
falla. Sensibilidad: el valor redondeado a un decimal.

**FD-LAC-04 (en L3).**
- **T\*:** la más tardía entre (A) la hemostasia que registra el núcleo y (B) el inicio de una entrega adecuada que se
  mantiene adecuada durante el período sostenido requerido (docente). Hay dos propuestas aquí:
  - ese período son 30 min (la docencia no fijó el número; se mantiene el de P2I-2);
  - se toma el primer tramo así que siga en curso en la hemostasia o después.
  El reloj nunca arranca antes de la hemostasia ni con la entrega inadecuada, y la fisiología no se reinicia.
- **Clasificación, en este orden:**
  - **ALREADY_NORMALIZED (docente):** L(T\*) ≤ 2,0 mmol/L. Se da por satisfecha y no se exige otra caída.
  - **NOT_EVALUABLE:** faltan 30 min de seguimiento después de T\*, o la entrega deja de ser adecuada en algún minuto
    entre T\* y T\* + 30 (docente). Agregar «no hay T\*» a esta lista es propuesta. Nunca es FAIL y no cuenta como
    contradicción. Sensibilidad: contarlo como falla.
  - **PASS:** L(T\* + 30) < L(T\*) (docente) con una trayectoria compatible con un aclaramiento en curso. Esto último es
    propuesta: el lactato sigue bajando en el último intervalo de reevaluación, L(T\* + 30) ≤ L(T\* + 15). Una baja que
    vuelve a subir no es aclaramiento en curso. El lactato puede venir bajando desde antes de T\*: no se exige un pico
    nuevo. La referencia es L(T\*).
  - **FAIL:** en cualquier otro caso.
- **Se informa** la reducción real a los 30 min, (L(T\*) − L(T\* + 30)) / L(T\*), para cada candidato sobreviviente.
- **Sólo como sensibilidad, sin seleccionar candidatos:** caídas de ≥ 5 %, 10 % y 15 % en T\* + 30, la prueba sin la
  condición de aclaramiento en curso, y la entrega sostenida 15 o 60 min.

**FD-LAC-05 (en L3).**
- **Premisa:** «tras un manejo definitivo exitoso con entrega adecuada sostenida» (docente). Leerla como «hay T\* y la
  entrega es adecuada en todos los minutos desde T\* hasta el 120» es propuesta. Si no se cumple, NOT_EVALUABLE, que no
  cuenta como contradicción (también propuesta). Sensibilidad: contarlo como falla.
- **Prueba (docente), con la premisa cumplida:**
  - 57m: 1,5 ≤ L120 ≤ 4,0;
  - 72f: 1,2 ≤ L120 ≤ 3,5;
  - además L120 < L(T\*).
- **Lo que no hace:** no se ajusta al punto medio, admite valores bajo 2 mmol/L y no exige normalizar.
- **L120 < L(T\*) se aplica tal como está escrito.** Eximir un L(T\*) ya normal (≤ 2,0) es sólo sensibilidad.
- **Memoria de la deuda.** La decisión original sigue vigente: el residual debe «depend materially on accumulated oxygen
  debt» y el modelo debe «preserve memory of prior debt». En P2I-2 eso filtraba; en P2I-2R el lactato que una deuda de
  llegada grave (60) todavía deja a los 120 min sólo se informa. La aclaración docente fijó la prueba de FD-LAC-05 (la
  envolvente y L120 < L(T\*)), pero no dijo nada sobre la memoria. Bajarla de filtro a verificación es una propuesta y
  queda como decisión pendiente (§5). Con los datos de §4.4 no tiene efecto:
  - en los sobrevivientes, la memoria va de 0,95 a 3,15 mmol/L, sobre el umbral de P2I-2 (10 % del lactato de llegada);
  - en la región, todos los pares con más deuda dejan más residual.

**FD-LAC-06 (en L1, L2 y L3), docente.** En todo tramo de sangrado activo con entrega inadecuada de al menos 30 min, no hay
un descenso sostenido y sustancial. Con entrega adecuada el lactato puede bajar aunque se siga sangrando. La regla se lee
de la entrega, nunca del diagnóstico.

Un candidato sobrevive a una decisión cuando la cumple en todos los casos en que se aplica, y a todas cuando cumple las
seis.

### 2.3 Disociación D–lactato

Se revisan los casos de P2I-1 en que D sube mientras el lactato baja (L1, de 0 a 60 y de 0 a 120 min). Se clasifican
otra vez con las reglas vigentes:
- **B INACEPTABLE:** dentro del lapso hay un descenso sostenido y sustancial en un tramo de sangrado activo con entrega
  inadecuada.
- **A ACEPTABLE:** si no es B, y el lactato sólo baja en minutos con entrega adecuada.
- **C TRANSITORIA O AMBIGUA:** el resto.

### 2.4 Reglas de informe, congeladas con las definiciones

- **Identificabilidad, por parámetro, con los niveles que sobreviven:**
  - NO IDENTIFICADO: la región no lo varía, o la proporción de cada nivel cambia ≤ 5 puntos;
  - POCO IDENTIFICADO: sobreviven todos los niveles, pero con un cambio mayor;
  - PARCIALMENTE RESTRINGIDO: se elimina algún nivel;
  - BIEN RESTRINGIDO: queda un solo nivel, dentro de la grilla explorada.
  - Nunca se destaca el nivel más frecuente.
- **Representantes:** entre los candidatos que cumplen las seis, por caso, el más bajo, la mediana y el más alto del
  lactato a los 60 min en L1 y del lactato a los 120 min en L3. Los empates se rompen por la clave del candidato.
- **Referencia heredada:** se ubica después del filtro y nunca entra en él.
- **Congelamiento:** conteos, resultados por caso, sensibilidad, disociación, región, resúmenes, reducciones,
  representantes y referencia heredada quedan fijados por el digest de informe (§3).

## 3. Recongelamiento antes de filtrar

- **Digests congelados en `lactate_constraints.py`, en el commit de recongelamiento `9601ce9`, antes de volver a
  filtrar:**
  - definiciones: `092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a` (`faculty_constraints.definitions_digest`, el módulo completo: decisiones,
    aclaraciones, confirmaciones, pruebas, ajustes, sensibilidad y reglas);
  - canalización: `4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394`
    (`lactate_constraints.pipeline_digest`, sin cambios respecto de P2I-2);
  - reglas de informe: `9316d312946cb4b03b6f0ec29c396b312d8518c0a5eeceee7f2f9ecf63b62be2` (`lactate_constraints.reporting_digest`).
- **El filtro se niega a correr** si cambia alguno, y los resultados guardan los tres.
- **Qué hay en el commit de recongelamiento:** las decisiones aclaradas, las definiciones y las reglas, sin ningún
  resultado revisado. La §4 se calculó después.
- **Lo que se sabía al recongelar:**
  - las tablas de P2I-1;
  - el resultado de P2I-2, con 66 sobrevivientes y sus resúmenes, que motivó la consulta a la docencia.
  - No se calculó ningún conteo con las reglas revisadas antes del recongelamiento.

<!-- generado:restricciones-lactato -->
## 4. Resultados (región admisible de P2F, sin candidatos nuevos)

Generado desde el filtro `58e988cf6b1c3d5bebab254305fdeec97ace1c11775db4753b458781a888d1bb` con las definiciones congeladas `092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a`, la canalización `4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394` y las reglas de informe `9316d312946cb4b03b6f0ec29c396b312d8518c0a5eeceee7f2f9ecf63b62be2`, sobre el congelamiento de calibración `152abc6cf3e2812fcade237f60db0430df78749e09f4199b0a0fff13a0dd4338`. Los números están en `docs/revision/P2I2_lactate_constraints.json`.

### 4.1 Sobrevivientes

| | Candidatos | Elimina | Elimina ella sola | Sobreviven sin ella |
|---|---|---|---|---|
| Antes del filtro | 1054 | | | |
| FD-LAC-01 | 414 (39 %) | 640 | 0 | 72 |
| FD-LAC-02 | 243 (23 %) | 811 | 54 | 126 |
| FD-LAC-03 | 306 (29 %) | 748 | 3 | 75 |
| FD-LAC-04 | 1000 (95 %) | 54 | 0 | 72 |
| FD-LAC-05 | 772 (73 %) | 282 | 60 | 132 |
| FD-LAC-06 | 312 (30 %) | 742 | 21 | 93 |
| **Las seis juntas** | **72 (7 %)** | | | |

«Elimina ella sola»: candidatos que fallan sólo esa decisión. «Sobreviven sin ella»: los que cumplen las otras cinco. Resultado de cada corrida, por caso (NOT_APPLICABLE, NOT_EVALUABLE y ALREADY_NORMALIZED no cuentan como contradicción):

| Caso | Decisión | Pasan | Resultados |
|---|---|---|---|
| gi_bleed_57m | FD-LAC-01 | 414 | falla: 640; pasa: 414 |
| gi_bleed_57m | FD-LAC-02 | 243 | falla: 811; pasa: 243 |
| gi_bleed_57m | FD-LAC-04 | 1042 | ALREADY_NORMALIZED: 75; falla: 12; pasa: 967 |
| gi_bleed_57m | FD-LAC-05 | 793 | falla: 261; pasa: 793 |
| gi_bleed_57m | FD-LAC-06 | 312 | falla: 742; pasa: 312 |
| gi_bleed_72f | FD-LAC-01 | 565 | falla: 489; pasa: 565 |
| gi_bleed_72f | FD-LAC-03 | 306 | falla: 748; pasa: 306 |
| gi_bleed_72f | FD-LAC-04 | 1000 | ALREADY_NORMALIZED: 102; falla: 54; pasa: 898 |
| gi_bleed_72f | FD-LAC-05 | 826 | falla: 228; pasa: 826 |
| gi_bleed_72f | FD-LAC-06 | 456 | falla: 598; pasa: 456 |

### 4.2 Sensibilidad (una definición por vez; ninguna variante selecciona candidatos)

| Variante | FD-LAC-01 | FD-LAC-02 | FD-LAC-03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | Las seis |
|---|---|---|---|---|---|---|---|
| **Definición principal** | 414 | 243 | 306 | 1000 | 772 | 312 | **72** |
| umbral de descenso 5 % | 294 | 243 | 306 | 1000 | 772 | 210 | 48 |
| umbral de descenso 15 % | 574 | 243 | 306 | 1000 | 772 | 435 | 87 |
| umbral de descenso 20 % | 706 | 243 | 306 | 1000 | 772 | 540 | 90 |
| tolerancia de adecuación 5 % | 435 | 243 | 306 | 1000 | 772 | 333 | 78 |
| tolerancia de adecuación 10 % | 456 | 243 | 306 | 1000 | 772 | 351 | 78 |
| reevaluación cada 10 min | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| reevaluación cada 30 min | 417 | 243 | 306 | 1000 | 772 | 318 | 75 |
| sostenido en 15 min | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| sostenido en 45 min | 423 | 243 | 306 | 1000 | 772 | 318 | 78 |
| sostenido en 60 min | 714 | 243 | 306 | 1000 | 772 | 336 | 84 |
| FD-LAC-01: lo no aplicable cuenta como falla | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-02/03 con el valor redondeado a un decimal | 414 | 264 | 330 | 1000 | 772 | 312 | 90 |
| FD-LAC-04: caída ≥ 5 % en T*+30 (sólo sensibilidad) | 414 | 243 | 306 | 781 | 772 | 312 | 54 |
| FD-LAC-04: caída ≥ 10 % en T*+30 (sólo sensibilidad) | 414 | 243 | 306 | 406 | 772 | 312 | 27 |
| FD-LAC-04: caída ≥ 15 % en T*+30 (sólo sensibilidad) | 414 | 243 | 306 | 195 | 772 | 312 | 18 |
| FD-LAC-04 sin la condición de aclaramiento en curso | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-04: entrega sostenida 15 min | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-04: entrega sostenida 60 min | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-04: lo no evaluable cuenta como falla | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-05 con el valor redondeado a un decimal | 414 | 243 | 306 | 1000 | 787 | 312 | 84 |
| FD-LAC-05: sin exigir L120 < L(T*) si L(T*) ≤ 2,0 | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |
| FD-LAC-05: lo no evaluable cuenta como falla | 414 | 243 | 306 | 1000 | 772 | 312 | 72 |

### 4.3 FD-LAC-01 y FD-LAC-04 en detalle

| Caso | FD-LAC-01: descenso sustancial sostenido antes de los 60 min | Sin tratar: pasa FD-LAC-01 pero baja de forma sostenida después de los 60 min (lo juzga FD-LAC-06) |
|---|---|---|
| gi_bleed_57m | 640 | 48 |
| gi_bleed_72f | 489 | 73 |

**FD-LAC-04: T\*, primer minuto con entrega adecuada en L3 y reducción a los 30 min**

| Caso | T* (minuto: corridas) | Primer minuto con entrega adecuada | Reducción en T*+30 (corridas evaluadas) | Reducción en T*+30 (sobrevivientes) | Sobrevivientes que alcanzarían: cualquier descenso / ≥ 5 % / ≥ 10 % / ≥ 15 % |
|---|---|---|---|---|---|
| gi_bleed_57m | 60: 1054 | desde la llegada: 405, min 1–30: 244, min 31–59: 405 | sin descenso: 12, 0–5 %: 126, 5–10 %: 417, 10–15 %: 229, ≥ 15 %: 195 | 5–10 %: 39, 10–15 %: 15, ≥ 15 %: 18 | 72 / 72 / 33 / 18 (de 72 evaluados) |
| gi_bleed_72f | 60: 1054 | desde la llegada: 405, min 1–30: 244, min 31–59: 405 | sin descenso: 54, 0–5 %: 219, 5–10 %: 375, 10–15 %: 211, ≥ 15 %: 93 | 0–5 %: 18, 5–10 %: 27, 10–15 %: 9, ≥ 15 %: 18 | 72 / 54 / 27 / 18 (de 72 evaluados) |

Los umbrales de ≥ 5 %, 10 % y 15 % se informan sólo como sensibilidad: ninguno está aprobado ni selecciona candidatos. La reducción de cada sobreviviente está en el anexo (§4.9).

**Robustez de la convención de minuto (no filtra).** El núcleo acumula la deuda de cada minuto con la entrega al comienzo de ese minuto; la definición congelada lee la entrega al final del minuto, uno antes. Releyendo todas las corridas con la entrega al comienzo del minuto: FD-LAC-01 417, FD-LAC-02 243, FD-LAC-03 306, FD-LAC-04 1000, FD-LAC-05 772, FD-LAC-06 312; las seis juntas, 72; candidatos que cambian de grupo, 0.

### 4.4 FD-LAC-05: envolvente a los 120 min y memoria de la deuda

| Caso | Residual de los sobrevivientes a los 120 min | Mediana del residual por deuda de llegada | Sobrevivientes > 2,0 mmol/L a los 120 min | Lactato que deja una deuda de 60 a los 120 min (región) | Pares de la región: más deuda → más residual |
|---|---|---|---|---|---|
| gi_bleed_57m | 1,88 a 3,93 | inferior 3,30, medio 3,25, superior 3,68 | 69 de 72 | 0,24 a 3,15 | 324 de 324 |
| gi_bleed_72f | 1,82 a 3,49 | inferior 3,00, medio 3,00, superior 3,32 | 69 de 72 | 0,24 a 3,15 | 324 de 324 |

### 4.5 Disociación D–lactato de P2I-1, reclasificada con las reglas vigentes

| Caso | Patrón | Región: A aceptable | B inaceptable | C transitoria | Región restringida: A | B | C |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 0 | 531 | 111 | 0 | 0 | 0 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 0 | 517 | 60 | 0 | 0 | 0 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 0 | 378 | 129 | 0 | 0 | 0 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 0 | 397 | 45 | 0 | 0 | 0 |

### 4.6 Región candidata restringida por la docencia (sigue CANDIDATE)

| Parámetro | Niveles: región → sobrevivientes | Rango P2F (57m; 72f) | Rango tras FD-LAC (57m; 72f) | Identificabilidad |
|---|---|---|---|---|
| `arrival_oxygen_debt` | inferior (0/0): 486 → 9; medio (20/20): 244 → 51; superior (60/60): 324 → 12 | 0,00–60,00; 0,00–60,00 | 0,00–60,00; 0,00–60,00 | POCO IDENTIFICADO |
| `arrival_lactate_excess` | inferior (2,4/1,4): 351 → 21; medio (3,4/2,4): 352 → 24; superior (3,6/2,6): 351 → 27 | 2,40–3,60; 1,40–2,60 | 2,40–3,60; 1,40–2,60 | NO IDENTIFICADO |
| τ_D `debt_clearance_tau_min` | 30 (30/30): 243 → 36; 60 (60/60): 406 → 36; 120 (120/120): 405 → 0 | 30,00–120,00; 30,00–120,00 | 30,00–60,00; 30,00–60,00 | PARCIALMENTE RESTRINGIDO |
| ganancia déficit→D `debt_per_delivery_deficit` | 1 (1/1): 1054 → 72 | 1,00–1,00; 1,00–1,00 | 1,00–1,00; 1,00–1,00 | NO IDENTIFICADO |
| ganancia D→lactato G `lactate_per_output_deficit` | 2 (2/2): 351 → 0; 6 (6/6): 352 → 18; 12 (12/12): 351 → 54 | 2,00–12,00; 2,00–12,00 | 6,00–12,00; 6,00–12,00 | PARCIALMENTE RESTRINGIDO |
| τ_L `lactate_clearance_tau_min` | 45 (45/45): 351 → 21; 120 (120/120): 352 → 27; 240 (240/240): 351 → 24 | 45,00–240,00; 45,00–240,00 | 45,00–240,00; 45,00–240,00 | NO IDENTIFICADO |
| `arrival_delivery_ratio` | inferior (0,6/0,6): 405 → 18; medio (0,85/0,85): 244 → 51; superior (1/1): 405 → 3 | 0,60–1,00; 0,60–1,00 | 0,60–1,00; 0,60–1,00 | POCO IDENTIFICADO |
| `metabolic_demand_baseline` | fijo (1/1): 1054 → 72 | 1,00–1,00; 1,00–1,00 | 1,00–1,00; 1,00–1,00 | NO IDENTIFICADO |

### 4.7 Trayectorias representativas de la región restringida

**gi_bleed_57m · sin tratar (L1), por el lactato a los 60 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 0, exceso 3,4, entrega 0,60, τ_D 30, G 12, τ_L 240 | 4,40 (D 0; entrega 0,60, inadecuada) | 4,26 (D 5; entrega 0,54, inadecuada) | 4,23 (D 9; entrega 0,48, inadecuada) | 4,41 (D 15; entrega 0,35, inadecuada) | 4,81 (D 19; entrega 0,22, inadecuada) | 5,36 (D 23; entrega 0,10, inadecuada) | tramo inadecuado 0–60 |
| mediana | deuda 20, exceso 3,6, entrega 0,85, τ_D 30, G 12, τ_L 240 | 4,40 (D 20; entrega 0,85, inadecuada) | 4,59 (D 14; entrega 0,76, inadecuada) | 4,68 (D 12; entrega 0,67, inadecuada) | 4,78 (D 13; entrega 0,50, inadecuada) | 4,98 (D 16; entrega 0,32, inadecuada) | 5,36 (D 21; entrega 0,14, inadecuada) | tramo inadecuado 0–60 |
| más alto | deuda 20, exceso 3,4, entrega 0,85, τ_D 30, G 12, τ_L 45 | 4,40 (D 20; entrega 0,85, inadecuada) | 5,36 (D 14; entrega 0,76, inadecuada) | 5,60 (D 12; entrega 0,67, inadecuada) | 5,68 (D 13; entrega 0,50, inadecuada) | 6,19 (D 16; entrega 0,32, inadecuada) | 7,30 (D 21; entrega 0,14, inadecuada) | tramo inadecuado 0–60 |

**gi_bleed_57m · manejo definitivo (L3), por el lactato a los 120 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 20, exceso 3,6, entrega 0,85, τ_D 30, G 12, τ_L 45 | 4,40 (D 20; entrega 0,85, inadecuada) | 5,22 (D 13; entrega 1,11) | 5,08 (D 8; entrega 1,36) | 3,87 (D 3; entrega 1,84) | 2,69 (D 1; entrega 1,82) | 1,88 (D 0; entrega 1,81) | hemostasia 60, T* 60, pasa; L(T*) 3,87 → L(T*+30) 2,69 (30,6 %) |
| mediana | deuda 20, exceso 2,4, entrega 0,85, τ_D 60, G 12, τ_L 45 | 4,40 (D 20; entrega 0,85, inadecuada) | 4,76 (D 16; entrega 1,11) | 4,78 (D 13; entrega 1,36) | 4,37 (D 8; entrega 1,84) | 3,78 (D 5; entrega 1,82) | 3,25 (D 3; entrega 1,81) | hemostasia 60, T* 60, pasa; L(T*) 4,37 → L(T*+30) 3,78 (13,5 %) |
| más alto | deuda 60, exceso 3,6, entrega 1,00, τ_D 60, G 6, τ_L 240 | 4,40 (D 60; entrega 1,00) | 4,51 (D 47; entrega 1,31) | 4,53 (D 36; entrega 1,60) | 4,43 (D 22; entrega 2,16) | 4,21 (D 13; entrega 2,14) | 3,93 (D 8; entrega 2,12) | hemostasia 60, T* 60, pasa; L(T*) 4,43 → L(T*+30) 4,21 (5,1 %) |

**gi_bleed_72f · sin tratar (L1), por el lactato a los 60 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 0, exceso 2,4, entrega 0,60, τ_D 30, G 12, τ_L 240 | 3,40 (D 0; entrega 0,60, inadecuada) | 3,32 (D 5; entrega 0,55, inadecuada) | 3,34 (D 9; entrega 0,51, inadecuada) | 3,60 (D 14; entrega 0,42, inadecuada) | 4,01 (D 17; entrega 0,33, inadecuada) | 4,53 (D 20; entrega 0,23, inadecuada) | tramo inadecuado 0–60 |
| mediana | deuda 20, exceso 2,6, entrega 0,85, τ_D 60, G 12, τ_L 45 | 3,40 (D 20; entrega 0,85, inadecuada) | 3,74 (D 18; entrega 0,79, inadecuada) | 3,90 (D 17; entrega 0,72, inadecuada) | 4,12 (D 19; entrega 0,59, inadecuada) | 4,52 (D 23; entrega 0,46, inadecuada) | 5,19 (D 28; entrega 0,33, inadecuada) | tramo inadecuado 0–60 |
| más alto | deuda 20, exceso 2,4, entrega 0,85, τ_D 30, G 12, τ_L 45 | 3,40 (D 20; entrega 0,85, inadecuada) | 4,64 (D 14; entrega 0,79, inadecuada) | 5,05 (D 12; entrega 0,72, inadecuada) | 5,19 (D 11; entrega 0,59, inadecuada) | 5,49 (D 13; entrega 0,46, inadecuada) | 6,22 (D 16; entrega 0,33, inadecuada) | tramo inadecuado 0–60 |

**gi_bleed_72f · manejo definitivo (L3), por el lactato a los 120 min**

| Representante | Parámetros | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min | Detalle |
|---|---|---|---|---|---|---|---|---|
| más bajo | deuda 20, exceso 2,6, entrega 0,85, τ_D 30, G 12, τ_L 45 | 3,40 (D 20; entrega 0,85, inadecuada) | 4,52 (D 13; entrega 1,04) | 4,60 (D 8; entrega 1,22) | 3,64 (D 3; entrega 1,57) | 2,57 (D 1; entrega 1,55) | 1,82 (D 0; entrega 1,54) | hemostasia 60, T* 60, pasa; L(T*) 3,64 → L(T*+30) 2,57 (29,3 %) |
| mediana | deuda 20, exceso 1,4, entrega 0,85, τ_D 30, G 6, τ_L 120 | 3,40 (D 20; entrega 0,85, inadecuada) | 3,62 (D 13; entrega 1,04) | 3,67 (D 8; entrega 1,22) | 3,51 (D 3; entrega 1,57) | 3,25 (D 1; entrega 1,55) | 3,00 (D 0; entrega 1,54) | hemostasia 60, T* 60, pasa; L(T*) 3,51 → L(T*+30) 3,25 (7,4 %) |
| más alto | deuda 20, exceso 1,4, entrega 0,85, τ_D 60, G 12, τ_L 120 | 3,40 (D 20; entrega 0,85, inadecuada) | 3,67 (D 16; entrega 1,04) | 3,82 (D 13; entrega 1,22) | 3,85 (D 8; entrega 1,57) | 3,71 (D 5; entrega 1,55) | 3,49 (D 3; entrega 1,54) | hemostasia 60, T* 60, pasa; L(T*) 3,85 → L(T*+30) 3,71 (3,8 %) |

### 4.8 REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN

Se ubica después del filtro y nunca entró en él. El motor de familias no tiene una entrega de O2 como la del núcleo, así que sólo se ubican las partes que dependen del lactato: los descensos se cuentan como si la entrega fuera inadecuada en todo momento, y T* se toma en el minuto de su propia endoscopia.

| Caso | Sin tratar: 0, 15, 30, 60, 90, 120 min | 60 min frente a la envolvente | Descensos sustanciales sostenidos (antes de 60; 0–120) | Manejo definitivo: 0, 15, 30, 60, 90, 120 min | T* + 30 | 120 min frente a la envolvente | L120 < L(T*) |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 4,4; 4,5; 4,6; 4,8; 4,9; 5,1 | 4,8: dentro de 4,4–7,0 | 0; 0 | 4,4; 4,1; 3,8; 3,2; 3,3; 3,3 | T* 60: 3,2 → 3,3 (no baja; reducción -3,1 %) | 3,3: dentro de 1,5–4,0 | no |
| gi_bleed_72f | 3,4; 3,5; 3,6; 3,8; 3,9; 4,1 | 3,8: dentro de 3,4–5,5 | 0; 0 | 3,4; 3,1; 2,8; 2,2; 2,3; 2,3 | T* 60: 2,2 → 2,3 (no baja; reducción -4,5 %) | 2,3: dentro de 1,2–3,5 | no |

### 4.9 Anexo: reducción del lactato en T\* + 30 min de cada sobreviviente

| Candidato | gi_bleed_57m: T*, L(T*) → L(T*+30), reducción | gi_bleed_72f: T*, L(T*) → L(T*+30), reducción |
|---|---|---|
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=lower;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,87 → 3,53, 8,8 % | T* 60: 3,41 → 3,23, 5,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,76 → 4,30, 9,7 % | T* 60: 4,17 → 3,84, 7,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=midpoint;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,87 → 3,53, 8,8 % | T* 60: 3,41 → 3,23, 5,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,76 → 4,30, 9,7 % | T* 60: 4,17 → 3,84, 7,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=upper;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,87 → 3,53, 8,8 % | T* 60: 3,41 → 3,23, 5,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,76 → 4,30, 9,7 % | T* 60: 4,17 → 3,84, 7,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,77, 13,7 % | T* 60: 3,78 → 3,32, 12,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,77, 13,7 % | T* 60: 3,78 → 3,32, 12,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,77, 13,7 % | T* 60: 3,78 → 3,32, 12,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,29 → 3,67, 14,5 % | T* 60: 3,70 → 3,21, 13,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,29 → 3,67, 14,5 % | T* 60: 3,70 → 3,21, 13,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,29 → 3,67, 14,5 % | T* 60: 3,70 → 3,21, 13,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=lower;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,11 → 3,72, 9,6 % | T* 60: 3,51 → 3,25, 7,4 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=lower;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,11 → 3,72, 9,6 % | T* 60: 3,51 → 3,25, 7,4 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=lower;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,11 → 3,72, 9,6 % | T* 60: 3,51 → 3,25, 7,4 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=lower;intrinsic=lower;preload=midpoint;debt=lower;delivery=lower` | T* 60: 4,11 → 3,90, 5,1 % | T* 60: 3,41 → 3,31, 2,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=lower;intrinsic=midpoint;preload=midpoint;debt=lower;delivery=lower` | T* 60: 4,11 → 3,90, 5,1 % | T* 60: 3,41 → 3,31, 2,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=lower;intrinsic=upper;preload=midpoint;debt=lower;delivery=lower` | T* 60: 4,11 → 3,90, 5,1 % | T* 60: 3,41 → 3,31, 2,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,88 → 3,59, 7,7 % | T* 60: 3,18 → 3,00, 5,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,41 → 4,09, 7,3 % | T* 60: 3,64 → 3,41, 6,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,88 → 3,59, 7,7 % | T* 60: 3,18 → 3,00, 5,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,41 → 4,09, 7,3 % | T* 60: 3,64 → 3,41, 6,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=lower;delivery=lower` | T* 60: 3,88 → 3,59, 7,7 % | T* 60: 3,18 → 3,00, 5,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,41 → 4,09, 7,3 % | T* 60: 3,64 → 3,41, 6,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 4,03, 7,8 % | T* 60: 3,60 → 3,35, 6,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 4,03, 7,8 % | T* 60: 3,60 → 3,35, 6,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 4,03, 7,8 % | T* 60: 3,60 → 3,35, 6,9 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=lower;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,25 → 4,03, 5,3 % | T* 60: 3,48 → 3,34, 3,8 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=lower;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,25 → 4,03, 5,3 % | T* 60: 3,48 → 3,34, 3,8 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=lower;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,25 → 4,03, 5,3 % | T* 60: 3,48 → 3,34, 3,8 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,02 → 2,86, 28,8 % | T* 60: 3,79 → 2,75, 27,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,02 → 2,86, 28,8 % | T* 60: 3,79 → 2,75, 27,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,02 → 2,86, 28,8 % | T* 60: 3,79 → 2,75, 27,5 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,87 → 2,69, 30,6 % | T* 60: 3,64 → 2,57, 29,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,87 → 2,69, 30,6 % | T* 60: 3,64 → 2,57, 29,3 % |
| `debt_clearance_tau_min=30,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,87 → 2,69, 30,6 % | T* 60: 3,64 → 2,57, 29,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,45 → 4,17, 6,3 % | T* 60: 3,85 → 3,71, 3,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,45 → 4,17, 6,3 % | T* 60: 3,85 → 3,71, 3,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=lower;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,45 → 4,17, 6,3 % | T* 60: 3,85 → 3,71, 3,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,05 → 3,64, 10,2 % | T* 60: 3,46 → 3,18, 8,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,05 → 3,64, 10,2 % | T* 60: 3,46 → 3,18, 8,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,05 → 3,64, 10,2 % | T* 60: 3,46 → 3,18, 8,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,97 → 3,53, 11,1 % | T* 60: 3,38 → 3,07, 9,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,97 → 3,53, 11,1 % | T* 60: 3,38 → 3,07, 9,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,97 → 3,53, 11,1 % | T* 60: 3,38 → 3,07, 9,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=upper;intrinsic=lower;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,57 → 4,17, 8,8 % | T* 60: 4,01 → 3,76, 6,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=upper;intrinsic=midpoint;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,57 → 4,17, 8,8 % | T* 60: 4,01 → 3,76, 6,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=6;excess=upper;intrinsic=upper;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,57 → 4,17, 8,8 % | T* 60: 4,01 → 3,76, 6,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,22 → 3,98, 5,7 % | T* 60: 3,45 → 3,30, 4,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,22 → 3,98, 5,7 % | T* 60: 3,45 → 3,30, 4,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,22 → 3,98, 5,7 % | T* 60: 3,45 → 3,30, 4,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,17 → 3,92, 6,1 % | T* 60: 3,40 → 3,24, 4,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,17 → 3,92, 6,1 % | T* 60: 3,40 → 3,24, 4,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,17 → 3,92, 6,1 % | T* 60: 3,40 → 3,24, 4,8 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=upper;intrinsic=lower;preload=midpoint;debt=upper;delivery=upper` | T* 60: 4,43 → 4,21, 5,1 % | T* 60: 3,65 → 3,52, 3,6 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=upper;intrinsic=midpoint;preload=midpoint;debt=upper;delivery=upper` | T* 60: 4,43 → 4,21, 5,1 % | T* 60: 3,65 → 3,52, 3,6 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=240,lactate_per_output_deficit=6;excess=upper;intrinsic=upper;preload=midpoint;debt=upper;delivery=upper` | T* 60: 4,43 → 4,21, 5,1 % | T* 60: 3,65 → 3,52, 3,6 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=lower;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,78, 13,5 % | T* 60: 4,13 → 3,66, 11,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=lower;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,78, 13,5 % | T* 60: 4,13 → 3,66, 11,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=lower;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 4,37 → 3,78, 13,5 % | T* 60: 4,13 → 3,66, 11,2 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,63 → 2,91, 19,7 % | T* 60: 3,39 → 2,80, 17,4 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,63 → 2,91, 19,7 % | T* 60: 3,39 → 2,80, 17,4 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=midpoint;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,63 → 2,91, 19,7 % | T* 60: 3,39 → 2,80, 17,4 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=lower;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,48 → 2,74, 21,3 % | T* 60: 3,24 → 2,62, 19,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,48 → 2,74, 21,3 % | T* 60: 3,24 → 2,62, 19,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=12;excess=upper;intrinsic=upper;preload=midpoint;debt=midpoint;delivery=midpoint` | T* 60: 3,48 → 2,74, 21,3 % | T* 60: 3,24 → 2,62, 19,0 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=midpoint;intrinsic=lower;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,69 → 3,82, 18,5 % | T* 60: 4,53 → 3,80, 16,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,69 → 3,82, 18,5 % | T* 60: 4,53 → 3,80, 16,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=midpoint;intrinsic=upper;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,69 → 3,82, 18,5 % | T* 60: 4,53 → 3,80, 16,1 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=upper;intrinsic=lower;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,54 → 3,65, 19,7 % | T* 60: 4,38 → 3,62, 17,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=upper;intrinsic=midpoint;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,54 → 3,65, 19,7 % | T* 60: 4,38 → 3,62, 17,3 % |
| `debt_clearance_tau_min=60,lactate_clearance_tau_min=45,lactate_per_output_deficit=6;excess=upper;intrinsic=upper;preload=midpoint;debt=upper;delivery=lower` | T* 60: 4,54 → 3,65, 19,7 % | T* 60: 4,38 → 3,62, 17,3 % |

<!-- /generado:restricciones-lactato -->

## 5. Limitaciones

- **Definiciones propuestas, sujetas a confirmación docente.** Cambiarlas exige un recongelamiento documentado. Son:
  - el intervalo de 15 min de la grilla y el tratamiento de los tramos;
  - en FD-LAC-04:
    - los 30 min del período sostenido de T\*;
    - la regla del primer tramo en curso en la hemostasia o después;
    - «no hay T\*» como NOT_EVALUABLE;
    - la condición de aclaramiento en curso;
  - en FD-LAC-05:
    - la lectura de la premisa como «entrega adecuada en todos los minutos de T\* a 120»;
    - su NOT_EVALUABLE contado como pase;
    - la memoria de la deuda como verificación, no como filtro.
- **Casos latentes, hoy sin efecto** (T\* = 60 en todas las corridas y la entrega queda adecuada hasta el 120):
  - si el tramo adecuado que cubre la hemostasia termina menos de 30 min después, FD-LAC-04 y FD-LAC-05 quedan
    NOT_EVALUABLE aunque un tramo posterior permitiría evaluarlas;
  - basta un minuto de entrega inadecuada entre T\* y 120 para que la envolvente de 120 min deje de aplicarse;
  - la razón «no T\* within the run» también rotula una corrida que termina antes del minuto 120;
  - la clasificación de la disociación juzga la adecuación al comienzo del minuto; con A = 0 no cambia nada.
- **Envolventes de FD-LAC-05:** son de calibración para estos dos casos GI, no límites fisiológicos universales.
- **Ventana de FD-LAC-04 en L3:** la transfusión restaura la entrega antes de la hemostasia. T\* cae en el minuto 60 en
  todas las corridas y el lactato puede venir bajando desde antes. La prueba lo admite, como pidió la docencia. Por eso
  no hubo ningún caso NOT_EVALUABLE ni en FD-LAC-04 ni en FD-LAC-05 (§4.1).
- **Condición de aclaramiento en curso:** quitarla no cambia ningún conteo (§4.2). Hoy no discrimina.
- **Reducción en T\* + 30:** en la región restringida va de menos del 5 % a más del 15 % (§4.3 y §4.9). Cualquier umbral
  porcentual exigiría una nueva decisión docente, y la sensibilidad muestra cuánto restringiría.
- **Referencia heredada:** queda dentro de las envolventes de 60 y 120 min. Pero después de su endoscopia no baja en
  T\* + 30 y su L120 no queda bajo L(T\*), así que, leída sólo por el lactato, no cumpliría FD-LAC-04 ni FD-LAC-05
  (§4.8). Es información de referencia: nunca entró en el filtro.

## 6. Historia

- **P2I-2:** las definiciones se congelaron en `9301a6a` y los resultados se publicaron en `0f6aed1`. Exigían:
  - en FD-LAC-01, subir ≥ 10 % hacia el final;
  - en FD-LAC-04, una caída ≥ 10 % hacia el final de la corrida desde el pico posterior a T\*;
  - en FD-LAC-05, una memoria de la deuda material y la ausencia de normalización brusca.
  Sobrevivían 66 de 1054. La docencia indicó que FD-LAC-01 y FD-LAC-04 no representaban fielmente sus decisiones y aprobó
  las envolventes de FD-LAC-05.
- **Aclaración del 2026-10-26, refinada antes de ejecutarse:** una primera versión proponía `L60 ≥ L0` en FD-LAC-01 y
  `L(T* + 30) ≤ 0,90 × L(T*)` en FD-LAC-04. La docencia la refinó antes de que se implementara o corriera, y ninguna de
  las dos se usó. Rigen las aclaraciones de la §1.
