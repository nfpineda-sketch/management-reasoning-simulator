# P2I-2R · Restricciones docentes del lactato GI, aclaradas, aplicadas a la región candidata

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
  30 min, no hay un descenso sostenido y sustancial. No se exige subir, ni una subida mínima, ni `L60 ≥ L0`.
- **Qué pasa con el minuto 60 y después:** el valor de los 60 min lo juzgan las envolventes duras de FD-LAC-02/03. Después
  de los 60 min, la misma prohibición la aplica FD-LAC-06.
- **Sin un tramo así:** NOT_APPLICABLE, que no cuenta como contradicción. Sensibilidad: contarlo como falla.

**FD-LAC-02 / FD-LAC-03 (en L1), docentes.** Envolventes duras e inclusivas a los 60 min sin tratar:
- 57m: 4,4 ≤ L60 ≤ 7,0;
- 72f: 3,4 ≤ L60 ≤ 5,5.

Se compara el valor exacto del modelo, nunca la distancia al punto medio. Una corrida que termina antes del minuto 60
falla. Sensibilidad: el valor redondeado a un decimal.

**FD-LAC-04 (en L3).**
- **T\* (docente):** la más tardía entre (A) la hemostasia que registra el núcleo y (B) el inicio de una entrega adecuada
  que se mantiene adecuada al menos 30 min. Se toma el primer tramo así que siga en curso en la hemostasia o después.
  El reloj nunca arranca antes de la hemostasia ni con la entrega inadecuada, y la fisiología no se reinicia.
- **Clasificación, en este orden:**
  - **ALREADY_NORMALIZED (docente):** L(T\*) ≤ 2,0 mmol/L. Se da por satisfecha y no se exige otra caída.
  - **NOT_EVALUABLE (docente):** no hay T\*; o faltan 30 min de seguimiento después de T\*; o la entrega deja de ser
    adecuada en algún minuto entre T\* y T\* + 30. Nunca es FAIL y no cuenta como contradicción. Sensibilidad: contarlo
    como falla.
  - **PASS:** L(T\* + 30) < L(T\*) (docente) con una trayectoria compatible con un aclaramiento en curso. Esto último es
    propuesta: el lactato sigue bajando en el último intervalo de reevaluación, L(T\* + 30) ≤ L(T\* + 15). Una baja que
    vuelve a subir no es aclaramiento en curso. El lactato puede venir bajando desde antes de T\*: no se exige un pico
    nuevo. La referencia es L(T\*).
  - **FAIL:** en cualquier otro caso.
- **Se informa** la reducción real a los 30 min, (L(T\*) − L(T\* + 30)) / L(T\*), para cada candidato sobreviviente.
- **Sólo como sensibilidad, sin seleccionar candidatos:** caídas de ≥ 5 %, 10 % y 15 % en T\* + 30, la prueba sin la
  condición de aclaramiento en curso, y la entrega sostenida 15 o 60 min.

**FD-LAC-05 (en L3).**
- **Premisa (docente):** «tras un manejo definitivo exitoso con entrega adecuada sostenida». Hay T\* y la entrega es
  adecuada en todos los minutos desde T\* hasta el 120. Si no, NOT_EVALUABLE, que no cuenta como contradicción.
  Sensibilidad: contarlo como falla.
- **Prueba (docente), con la premisa cumplida:**
  - 57m: 1,5 ≤ L120 ≤ 4,0;
  - 72f: 1,2 ≤ L120 ≤ 3,5;
  - además L120 < L(T\*).
- **Lo que no hace:** no se ajusta al punto medio, admite valores bajo 2 mmol/L y no exige normalizar.
- **L120 < L(T\*) se aplica tal como está escrito.** Eximir un L(T\*) ya normal (≤ 2,0) es sólo sensibilidad.
- **Memoria de la deuda:** el lactato que una deuda de llegada grave (60) todavía deja a los 120 min se informa como
  verificación y no filtra.

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

- **Digests congelados en `lactate_constraints.py`, antes de volver a filtrar:**
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
<!-- /generado:restricciones-lactato -->

## 5. Limitaciones

- **Definiciones propuestas:** el 15 min de la grilla, el tratamiento de los tramos y la condición de aclaramiento en
  curso de FD-LAC-04 son propuestas del núcleo, sujetas a confirmación docente. Cambiarlas exige un recongelamiento
  documentado.
- **Envolventes de FD-LAC-05:** son de calibración para estos dos casos GI, no límites fisiológicos universales.
- **Ventana de FD-LAC-04 en L3:** la transfusión restaura la entrega antes de la hemostasia, así que el lactato puede
  venir bajando desde antes de T\*. La prueba lo admite, como pidió la docencia.

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
