# Paquete de revisión docente — divergencia de consciencia (núcleo común V1 frente al heredado)

**Solo lectura · sin decisiones · sin cambios al repositorio.** Rama `phase-3-runtime-integration`, HEAD `b297147`, punto de control A (`TECHNICAL_INFRASTRUCTURE_READY_FOR_FACULTY_AUTHORITY_DECISION`). `FACULTY_CONSCIOUSNESS_READINESS = NOT_READY`; `COMMON_CORE_RUNTIME_AUTHORITY = False`; sin concesión; `GI_DEVELOPMENT_SNAPSHOT_V1` ratificada sólo para experimentos de desarrollo, no aprobada para autoridad; ningún valor común se escribió en un encuentro real; el residente sigue viendo el estado mental heredado.

> **Coherencia mecanística ≠ aceptabilidad educativa.** Los 15 episodios del registro P3-200 son `MECHANISTICALLY_COHERENT_DIFFERENCE` (0 contradicciones estructurales): la categoría común sigue a sus causas declaradas. Eso **no** dice que la docencia la apruebe; este paquete reúne la evidencia para que decida.

## 0 · Cómo leer este paquete

* **Núcleo común = `GI_DEVELOPMENT_SNAPSHOT_V1`.** Categoría = escalón de F (carga de encefalopatía sistémica reversible): **NMOI** (`NO_MATERIAL_OBSERVABLE_IMPAIRMENT`, F < 0,25), **SOMNOLENT** (≥ 0,25), **OBTUNDED** (≥ 0,50), **UNRESPONSIVE** (≥ 0,80, o colapso ESTABLISHED, que fuerza UNRESPONSIVE). En el panel se leen como Alert / Drowsy / Obtunded / Unresponsive.
* **F** relaja hacia (0,75 − entrega relativa) / 0,25, acotada a [0, 1]; constante de subida 1,96 min y de bajada 8,51 min. **Entrega relativa** = entrega de oxígeno / la de llegada de ese paciente. **Perfusión relativa** alimenta la carga de colapso (0,55 → 0,35); IMPENDING con carga ≥ 0,37 y ESTABLISHED con carga ≥ 0,625 o sin pulso.
* **Heredado:** escalera de PAS **absoluta** — Drowsy con PAS < 80 mmHg, Obtunded con PAS < 65 (margen de salida de +2 mmHg); «Unresponsive» sólo en el paro. En estos encuentros la SpO2 está en 96–97 % y la escalera de oxígeno (< 87 %) no actúa.
* **Frontera de colapso = ESTABLISHED** (FD-AUTH-06; IMPENDING **no** es frontera). `BEFORE_COLLAPSE` = ningún minuto del episodio es ESTABLISHED; `AFTER_COLLAPSE_BOUNDARY` = todos lo son; `MIXED` = ambos. La frontera es de experimento, no una regla de muerte ni un desenlace del residente.
* **Duración** = minutos comparados (y, entre paréntesis, la extensión inicio–fin cuando hay minutos sin comparar). **Punto medio** = el minuto comparado central del episodio.
* **Qué es un episodio:** minutos `POTENTIAL_EDUCATIONAL_PROBLEM` contiguos = la palabra difiere en ≥ 2 bandas, o uno lee Alert y el otro no. Las diferencias de 1 banda no están en la tabla.
* **Selección:** los 9 episodios ya elegidos (el de mayor impacto de cada patrón distinto) cubren **264 de los 461** minutos comparados; los otros 6 son réplicas del mismo rango en otros escenarios (p. ej. 57m min 63–108 aparece en cuatro escenarios, porque la primera orden llega después).
* **Origen de los valores:** inicio, fin, PAS, dirección y manejo están en el registro `docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json`; el punto medio, la perfusión relativa, MAP, FC, lactato y TRC salen de las corridas ya registradas (`PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json`) y del curso físico ya registrado (`PHASE3_GI_SNAPSHOT_SENSITIVITY.json`) evaluado con V1. No se corrió fisiología nueva.

## 1 · Tabla única de los 9 episodios (17 campos)

Convenciones: el orden de los pares (común / heredado o al revés) se indica en cada encabezado; *ini / med / fin* = primer minuto, minuto medio y último minuto comparados.

| # | 1 Caso | 2 Escenario | 3 Inicio | 4 Fin | 5 Duración | 6 Manejo previo | 7 Heredado | 8 Núcleo común | 9 Dirección | 10 Entrega relativa ini / med / fin | 11 F ini / med / fin | 12 Perfusión relativa ini / med / fin | 13 Colapso | 14 Frontera | 15 Mecanismo (común) | 16 Mecanismo (heredado) | 17 Por qué difieren |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 72f | untreated — sin tratar | 158 | 240 | 83 min | Ninguna: sin orden desde la llegada (sin tratar). | Drowsy | UNRESPONSIVE | COMMON_MORE_IMPAIRED | 0,541 / 0,425 / 0,310 | 0,809 / 1,000 / 1,000 | 0,553 / 0,440 / 0,324 | NONE→IMPENDING→ESTABLISHED | MIXED (49 antes: min 158–206 · 34 después: min 207–240) | F ≥ 0,80 desde el min 158 (0,81) y satura en 1,0; entrega relativa 0,54 → 0,31 (bajo 0,50 desde el min 173). Colapso IMPENDING desde el 189 y ESTABLISHED desde el 207, que además fuerza UNRESPONSIVE. Pulso presente todo el rango. | Escalera heredada por PAS absoluta: Drowsy con PAS < 80, Obtunded con PAS < 65; UNRESPONSIVE sólo en paro. PAS heredada 77 → 66 (nunca < 65): Drowsy desde el min 138. Hay pulso. | Mismos hechos, dos escalas: el heredado mira la PAS absoluta (66–77 mmHg, sobre 65) y no pasa de Drowsy; el común mira la entrega perdida respecto de la llegada (−46 % → −69 %) y F satura. |
| 2 | 72f | severe_deterioration — deterioro grave (sólo 1 L a los 131) | 194 | 240 | 47 min | Min 131 (63 min antes del inicio): vía IV + 1 L de salina; sin sangre. Se dio cuando el testigo CENTER_REFERENCE leyó OBTUNDED por primera vez. | Drowsy | UNRESPONSIVE | COMMON_MORE_IMPAIRED | 0,539 / 0,468 / 0,403 | 0,811 / 1,000 / 1,000 | 0,566 / 0,494 / 0,427 | NONE→IMPENDING | BEFORE_COLLAPSE | Tras el litro (min 131) la entrega subió a 0,71 (min 151) y F bajó a 0,27 (min 156); luego volvió a caer (0,40 al min 240). F ≥ 0,80 desde el 194 (0,81) y 1,0 al final. IMPENDING desde el 226. Pulso presente. | Misma escalera. PAS heredada 75 → 68 (≥ 65): Drowsy; Obtunded exigiría < 65. Hay pulso. | Igual que la fila 1: PAS heredada 68–75 mmHg → Drowsy; el común, con 46–60 % de entrega perdida, lee F ≥ 0,80. |
| 3 | 72f | severe_deterioration — deterioro grave (sólo 1 L a los 131) | 109 | 168 | 41 min (extensión 60) | Ninguna antes del inicio. La misma orden (vía IV + 1 L de salina) cae dentro del episodio, en el min 131 (22 min después del inicio). | Alert | SOMNOLENT (OBTUNDED en 1 minuto, el 131) | COMMON_MORE_IMPAIRED | 0,680 / 0,623 / 0,631 | 0,251 / 0,480 / 0,435 | 0,688 / 0,633 / 0,662 | NONE | BEFORE_COLLAPSE | Entrega relativa 0,68 → 0,63 (bajo 0,75 desde el min 85); F 0,25 → 0,43: SOMNOLENT (0,25 ≤ F < 0,50). F ≥ 0,50 en los min 131–135 (OBTUNDED; sólo el 131 es minuto comparado) y bajó tras la orden. | Misma escalera. PAS heredada 83 → 80 (≥ 80, no < 80): Alert; Drowsy sólo desde el min 169. | La paciente llegó con PAS 98: su PAS heredada (83 → 80) sigue sobre el umbral absoluto 80, pero ya perdió 32–37 % de SU entrega de llegada, y F ≥ 0,25. |
| 4 | 57m | delayed_treatment — tratamiento tardío (min 120) | 63 | 108 | 46 min | Ninguna (sin tratar; el paquete llega en el min 120, 12 min después del fin). | Drowsy | NMOI | LEGACY_MORE_IMPAIRED | 0,813 / 0,746 / 0,683 | 0,000 / 0,001 / 0,240 | 0,817 / 0,752 / 0,691 | NONE | BEFORE_COLLAPSE | Entrega relativa 0,81 → 0,68 (cruza 0,75 en el min 85); F ≈ 0 hasta el 86 y 0,24 en el 108, justo bajo el corte 0,25: sin deterioro observable material. El corte se cruza en el min 109, y desde ahí ambas palabras coinciden. | Misma escalera. PAS heredada 79 → 73: Drowsy desde el min 63 (PAS 79 < 80; el minuto anterior era 80). Obtunded exigiría < 65. | El paciente llegó con PAS 88: cruza el umbral absoluto 80 en el min 63 con sólo 19 % de entrega perdida; el común no actúa hasta perder > 25 % (min 85) y espera a F ≥ 0,25 (min 109). |
| 5 | 57m | untreated — sin tratar | 158 | 174 | 17 min | Ninguna: sin orden desde la llegada (sin tratar). | Drowsy | UNRESPONSIVE | COMMON_MORE_IMPAIRED | 0,541 / 0,518 / 0,496 | 0,809 / 0,899 / 0,987 | 0,553 / 0,531 / 0,509 | NONE | BEFORE_COLLAPSE | F 0,81 → 0,99 (corte UNRESPONSIVE 0,80 cruzado en el min 158); entrega relativa 0,54 → 0,50; carga de colapso 0 → 0,17 (NONE). Pulso presente. | Misma escalera. PAS heredada 67 → 65 (≥ 65): Drowsy. Obtunded llega en el min 175 (PAS 64), justo después del episodio. | Entrega perdida 46–50 %; PAS heredada 67–65 (aún ≥ 65 → Drowsy) frente a F 0,81–0,99 (UNRESPONSIVE). |
| 6 | 57m | fluid_focused — sólo cristaloide (2 L) | 109 | 120 | 12 min | Vía IV + 1 L de salina en el min 10 y 1 L más en el min 40 (2 L de cristaloide; sin sangre), 99 y 69 min antes del inicio. | Drowsy | NMOI | LEGACY_MORE_IMPAIRED | 0,811 / 0,794 / 0,780 | 0,000 / 0,000 / 0,000 | 0,842 / 0,825 / 0,810 | NONE | BEFORE_COLLAPSE | Con 2 L la entrega relativa se sostiene (0,81 → 0,78; nunca baja de 0,75 en la corrida): F = 0 durante todo el rango; la señal aguas arriba nunca se activó. | Misma escalera. PAS heredada 79 → 78 (< 80): Drowsy desde el min 109. | La entrega relativa se sostiene (≥ 0,78) pero la PAS heredada queda bajo el umbral absoluto (79–78): el heredado lee el nivel absoluto de presión; el común, la entrega relativa a la llegada. |
| 7 | 72f | delayed_treatment — tratamiento tardío (min 120) | 109 | 120 | 12 min | Ninguna antes del inicio. El paquete (vía IV + salina + 2 U de GR) se da en el min 120, el último minuto del episodio. | Alert | SOMNOLENT | COMMON_MORE_IMPAIRED | 0,680 / 0,663 / 0,649 | 0,251 / 0,320 / 0,377 | 0,688 / 0,672 / 0,658 | NONE | BEFORE_COLLAPSE | Igual que la fila 3: entrega relativa 0,68 → 0,65 y F 0,25 → 0,38 (SOMNOLENT). | Misma escalera. PAS heredada 83 → 82 (≥ 80): Alert. | Igual que la fila 3: PAS heredada 83–82 sobre el umbral absoluto 80 frente a entrega relativa 0,68–0,65 y F ≥ 0,25. |
| 8 | 57m | severe_deterioration — deterioro grave (sólo 1 L a los 131) | 194 | 198 | 5 min | Min 131 (63 min antes del inicio): vía IV + 1 L de salina; sin sangre. | Drowsy | UNRESPONSIVE | COMMON_MORE_IMPAIRED | 0,539 / 0,533 / 0,526 | 0,811 / 0,837 / 0,863 | 0,566 / 0,559 / 0,553 | NONE | BEFORE_COLLAPSE | F 0,81 → 0,86 (0,011 a 0,063 sobre el corte 0,80), entrega relativa 0,54 → 0,53. Segundo descenso tras el cristaloide (F 0,27 en el min 156 → 0,81 en el 194). Pulso presente. | Misma escalera. PAS heredada 65 → 65 (≥ 65): Drowsy; Obtunded desde el min 199. | Igual que la fila 1: PAS heredada 65 (≥ 65 → Drowsy) frente a entrega perdida 46–47 % y F 0,81–0,86. |
| 9 | 57m | recovery_after_severe — recuperación tras grave (orden en 158) | 158 | 158 | 1 min | Ninguna antes. En este mismo minuto (158) se emite la orden (vía IV + 1 L de salina + 4 U de GR): el minuto comparado es el de la orden. | Drowsy | UNRESPONSIVE | TRANSIENT (el signo es común más deteriorado) | 0,541 / 0,541 / 0,541 | 0,809 / 0,809 / 0,809 | 0,553 / 0,553 / 0,553 | NONE | BEFORE_COLLAPSE | F = 0,809, a 0,009 sobre el corte UNRESPONSIVE (0,80); entrega relativa 0,54. Es el primer minuto de la corrida con F ≥ 0,80, y la orden de la serie se da en él. | Misma escalera. PAS heredada 67 (≥ 65): Drowsy; UNRESPONSIVE sólo en paro. | Igual que la fila 5 en el min 158, y F está a 0,009 del corte 0,80: un solo minuto comparado en el borde del corte. |

Relaciones leídas de la tabla (hechos, no juicios): 6 filas `COMMON_MORE_IMPAIRED` (1, 2, 3, 5, 7, 8), 2 `LEGACY_MORE_IMPAIRED` (4, 6), 1 `TRANSIENT` (9); ninguna `CROSSING`. Minutos de la tabla: 205 / 58 / 1. De los 264, **230 son BEFORE_COLLAPSE y 34 AFTER_COLLAPSE_BOUNDARY** (todos de la fila 1); 18 + 15 de esos minutos previos están en IMPENDING (filas 1 y 2), sin ser frontera.

## 2 · Evidencia por episodio para las cuatro preguntas (sin responderlas)

**Q1** ¿La categoría común comunicaría con plausibilidad la severidad fisiológica presente en ese momento? · **Q2** ¿El cambio común es implausiblemente temprano o tardío respecto del deterioro o la recuperación aguas arriba? · **Q3** ¿La diferencia con el heredado probablemente confundiría a un residente? · **Q4** ¿El episodio muestra un problema de semántica relativa a la llegada, de umbrales de categoría, de cinética de F, o ninguno?

*Cronología común a todas las corridas sin tratar (idéntica en ambos casos, porque es relativa a la llegada):* entrega relativa < 0,75 en el min 85 → F > 0 en el 86 → SOMNOLENT en el 109 → OBTUNDED en el 131 → UNRESPONSIVE en el 158 → entrega relativa ≤ 0,50 en el 173 → IMPENDING en el 189 → ESTABLISHED en el 207. *Heredado:* 57m Drowsy en el 63 y Obtunded en el 175; 72f Drowsy en el 138 y nunca Obtunded (PAS mínima 66). *Recuperación tras una orden:* 1 L de salina (min 131): la entrega sube de 0,62 a 0,71 en 20 min y F baja de 0,51 a 0,27 en 24 min (min 156), luego F vuelve a subir (≥ 0,25 en el 157, ≥ 0,50 en el 173, ≥ 0,80 en el 194); salina + 4 U de GR (min 158): F < 0,80 en el 161, < 0,50 en el 168, < 0,25 en el 174, entrega ≥ 0,75 en el 167; paquete de tratamiento en el 120: F < 0,25 en el 127, entrega ≥ 0,75 en el 125.

### Episodio 1 · 72f · untreated · min 158–240 · COMMON_MORE_IMPAIRED · MIXED
* **Q1 — evidencia (min 199, medio):** núcleo común → **UNRESPONSIVE** con PAS 43 / PAM 33 / FC 137 / índice de choque 3,19 / lactato 4,5 / TRC 6,2; entrega relativa 0,425, perfusión relativa 0,440, F 1,000, colapso IMPENDING, pulso presente. Heredado → **Drowsy** con PAS 71 / PAM 55 / FC 127 / índice de choque 1,79 / lactato 4,6 / TRC 6,4, pulso presente.
* **Q2 — evidencia:** F cruza 0,80 en el min 158, 27 min después de OBTUNDED (131) y 49 min antes de ESTABLISHED (207); la entrega relativa de ese minuto (0,54) aún no baja del nivel «grave» 0,50 (lo hace en el 173). El heredado cambia de Alert a Drowsy en el 138 (PAS 79) y no vuelve a cambiar en los 102 minutos siguientes.
* **Q3 — evidencia:** Par que vería el residente si el común fuera la fuente: PAS 43 / FC 137 / «Unresponsive» (min 199) frente al par de hoy: PAS 71 / FC 127 / «Drowsy». El heredado escribe «Unresponsive» sólo en el paro; el común lo escribe con pulso durante los 83 minutos del episodio. Siete lectores consecuentes de la palabra no están enrutados y el residente hoy sigue viendo el heredado (punto de control P3-237; FD-AUTH-08 y FD-AUTH-12).
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **umbrales de categoría y frontera de colapso** (la etiqueta UNRESPONSIVE con F = 0,81 y entrega 0,54, que se mantiene 83 min con pulso) y **cinética de F** (F 0,81 en el min 158, 0,99 en el 174 y 1,0 en el 189). Los 34 minutos ESTABLISHED son aparte (§6).

### Episodio 2 · 72f · severe_deterioration · min 194–240 · COMMON_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 217, medio):** núcleo común → **UNRESPONSIVE** con PAS 48 / PAM 37 / FC 136 / índice de choque 2,83 / lactato 4,6 / TRC 6,0; entrega relativa 0,468, perfusión relativa 0,494, F 1,000, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 72 / PAM 55 / FC 127 / índice de choque 1,76 / lactato 4,6 / TRC 6,3, pulso presente.
* **Q2 — evidencia:** La orden del min 131 produjo una mejora aguas arriba (entrega 0,62 → 0,71 en el 151) y F bajó a 0,27 (156), de modo que el común dejó OBTUNDED en el 136 (5 min tras la orden) y no volvió a UNRESPONSIVE hasta el 194, 63 min después. El heredado pasó a Drowsy en el 169.
* **Q3 — evidencia:** Par común: PAS 48 / FC 136 / «Unresponsive» (min 217) frente a PAS 72 / FC 127 / «Drowsy». Misma observación sobre «Unresponsive» con pulso (C5).
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **cinética de F** (la mejora tras 1 L dura ~25 min, con F mínima 0,27 en el 156, y F re-sube; τ de subida 1,96 min frente a τ de bajada 8,51 min) y **umbrales de categoría** (UNRESPONSIVE con pulso).

### Episodio 3 · 72f · severe_deterioration · min 109–168 · COMMON_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 129, medio):** núcleo común → **SOMNOLENT** con PAS 62 / PAM 47 / FC 126 / índice de choque 2,03 / lactato 3,8 / TRC 5,5; entrega relativa 0,623, perfusión relativa 0,633, F 0,480, colapso NONE, pulso presente. Heredado → **Alert** con PAS 81 / PAM 62 / FC 122 / índice de choque 1,51 / lactato 4,2 / TRC 5,5, pulso presente.
* **Q2 — evidencia:** SOMNOLENT en el 109 es 24 min después de que la entrega cruzó 0,75 (min 85). En la corrida sin tratar el heredado marca Drowsy en el 138 (29 min después); en ésta, tras la orden, en el 169. El OBTUNDED del 131 coincide con la orden; F baja de 0,50 en el 136 y el común vuelve a SOMNOLENT.
* **Q3 — evidencia:** Par común: PAS 62 / FC 126 / «Drowsy» (min 129) frente a PAS 81 / FC 122 / «Alert». La diferencia es de una banda hacia lo más alterado en un paciente con PAS heredada sobre 80.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **semántica relativa a la llegada** (la paciente que llegó con PAS 98 se altera con PAS heredada 83) y, en menor medida, **cinética de F** (24 min entre la caída de entrega y el primer escalón).

### Episodio 4 · 57m · delayed_treatment · min 63–108 · LEGACY_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 86, medio):** núcleo común → **NMOI** con PAS 66 / PAM 49 / FC 132 / índice de choque 2,00 / lactato 4,5 / TRC 6,0; entrega relativa 0,746, perfusión relativa 0,752, F 0,001, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 76 / PAM 57 / FC 130 / índice de choque 1,71 / lactato 4,9 / TRC 6,0, pulso presente.
* **Q2 — evidencia:** El heredado marca Drowsy en el 63; el común todavía no registra deterioro (entrega 0,81; cruzará 0,75 en el 85; SOMNOLENT en el 109): 46 min de adelanto del heredado. El episodio acaba cuando el común alcanza el corte 0,25.
* **Q3 — evidencia:** Par común: PAS 66 / FC 132 / «Alert» (min 86) frente a PAS 76 / FC 130 / «Drowsy»; el común muestra PAS 72 → 61 con consciencia conservada (índice de choque 1,8 → 2,2).
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **semántica relativa a la llegada** (el que llegó con PAS 88 cruza el umbral heredado con 19 % de entrega perdida) y el **corte 0,25** (F = 0,24 en el min 108).

### Episodio 5 · 57m · untreated · min 158–174 · COMMON_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 166, medio):** núcleo común → **UNRESPONSIVE** con PAS 47 / PAM 35 / FC 143 / índice de choque 3,04 / lactato 5,1 / TRC 6,9; entrega relativa 0,518, perfusión relativa 0,531, F 0,899, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 66 / PAM 50 / FC 136 / índice de choque 2,06 / lactato 5,4 / TRC 7,0, pulso presente.
* **Q2 — evidencia:** Mismo calendario común que la fila 1 (UNRESPONSIVE en el 158). El heredado llega a Obtunded en el 175, 17 min después; la diferencia pasa entonces a 1 banda y deja de ser episodio.
* **Q3 — evidencia:** Par común: PAS 47 / FC 143 / «Unresponsive» (min 166) frente a PAS 66 / FC 136 / «Drowsy». Observación sobre «Unresponsive» con pulso (C5), sin colapso establecido.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **umbrales de categoría** (corte 0,80) y la etiqueta con pulso sin colapso; el heredado también alcanza Obtunded 17 min después (min 175), con lo que la diferencia se reduce a 1 banda.

### Episodio 6 · 57m · fluid_focused · min 109–120 · LEGACY_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 115, medio):** núcleo común → **NMOI** con PAS 73 / PAM 54 / FC 130 / índice de choque 1,78 / lactato 4,5 / TRC 5,7; entrega relativa 0,794, perfusión relativa 0,825, F 0,000, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 79 / PAM 59 / FC 129 / índice de choque 1,63 / lactato 4,8 / TRC 5,8, pulso presente.
* **Q2 — evidencia:** No hay cambio común: con 2 L la entrega relativa nunca baja de 0,75 (0,78 en el min 120). El heredado marca Drowsy en el 109 porque su PAS cae a 79 mmHg; en las corridas sin tratar el mismo paciente ya lo marcaba en el 63.
* **Q3 — evidencia:** Par común: PAS 73 / FC 130 / «Alert» (min 115) frente a PAS 79 / FC 129 / «Drowsy» (heredado). Aquí es el heredado el que difiere por un umbral absoluto con entrega relativa sostenida.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **semántica relativa a la llegada** (entrega sostenida frente a PAS absoluta) y el comportamiento del común tras la reanimación con líquido.

### Episodio 7 · 72f · delayed_treatment · min 109–120 · COMMON_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 115, medio):** núcleo común → **SOMNOLENT** con PAS 66 / PAM 50 / FC 124 / índice de choque 1,88 / lactato 3,7 / TRC 5,3; entrega relativa 0,663, perfusión relativa 0,672, F 0,320, colapso NONE, pulso presente. Heredado → **Alert** con PAS 82 / PAM 63 / FC 121 / índice de choque 1,48 / lactato 4,1 / TRC 5,4, pulso presente.
* **Q2 — evidencia:** Mismo calendario que la fila 3: SOMNOLENT en el 109 (F 0,25); el heredado permanece Alert (PAS ≥ 80). El episodio acaba en el 120 con la orden; tras ella la entrega es ≥ 0,75 en el 125 y F < 0,25 en el 127 (sin minutos comparados justo después de la orden).
* **Q3 — evidencia:** Par común: PAS 66 / FC 124 / «Drowsy» (min 115) frente a PAS 82 / FC 121 / «Alert»; episodio corto (12 min) que termina con el tratamiento.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **semántica relativa a la llegada**, igual que la fila 3, y el corte 0,25 (F = 0,25 en el min 109).

### Episodio 8 · 57m · severe_deterioration · min 194–198 · COMMON_MORE_IMPAIRED · BEFORE_COLLAPSE
* **Q1 — evidencia (min 196, medio):** núcleo común → **UNRESPONSIVE** con PAS 49 / PAM 37 / FC 144 / índice de choque 2,94 / lactato 5,4 / TRC 6,8; entrega relativa 0,533, perfusión relativa 0,559, F 0,837, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 65 / PAM 49 / FC 137 / índice de choque 2,11 / lactato 5,4 / TRC 7,1, pulso presente.
* **Q2 — evidencia:** UNRESPONSIVE en el 194 es 63 min tras la orden del 131; el común mejoró (F 0,27 en el 156) y volvió a caer. El heredado llega a Obtunded en el 199, el minuto siguiente al fin del episodio (198).
* **Q3 — evidencia:** Par común: PAS 49 / FC 144 / «Unresponsive» (min 196) frente a PAS 65 / FC 137 / «Drowsy»; episodio de 5 minutos tras un tratamiento parcial.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **umbrales de categoría** (F a 0,011–0,063 del corte 0,80) y **cinética de F** (re-deterioro tras el líquido).

### Episodio 9 · 57m · recovery_after_severe · min 158–158 · TRANSIENT · BEFORE_COLLAPSE
* **Q1 — evidencia (min 158, medio):** núcleo común → **UNRESPONSIVE** con PAS 49 / PAM 36 / FC 142 / índice de choque 2,90 / lactato 5,0 / TRC 6,8; entrega relativa 0,541, perfusión relativa 0,553, F 0,809, colapso NONE, pulso presente. Heredado → **Drowsy** con PAS 67 / PAM 50 / FC 136 / índice de choque 2,03 / lactato 5,3 / TRC 6,9, pulso presente.
* **Q2 — evidencia:** El único minuto comparado es el 158, el primero con F ≥ 0,80 (margen 0,009) y el de la orden. Después de la orden, F < 0,80 en el 161 (3 min), < 0,50 en el 168 y < 0,25 en el 174; no hay minutos comparados justo después de la orden.
* **Q3 — evidencia:** Un solo minuto (158): común «Unresponsive» frente a «Drowsy», que el residente vería sólo si el común fuera la fuente en un turno de orden.
* **Q4 — evidencia (qué elementos operan; no se afirma que alguno sea un problema):** Elementos que intervienen: **umbrales de categoría** (margen 0,009 sobre el corte) y la **granularidad de muestreo**: un solo minuto comparado en un turno de orden.

## 3 · Resumen por dirección

Registro completo (15 episodios, 461 min): `COMMON_MORE_IMPAIRED` 8 episodios / 263 min; `LEGACY_MORE_IMPAIRED` 5 / 196; `TRANSIENT` 2 / 2; `CROSSING` 0. En la tabla: 6 / 205 min, 2 / 58 min, 1 / 1 min.

**A · LEGACY_MORE_IMPAIRED (filas 4 y 6).** *Patrón causal recurrente:* el paciente de 57 años llegó con PAS 88, a 8 mmHg del umbral absoluto 80. La PAS heredada cruza 80 en el min 63 con la entrega relativa todavía en 0,81 (19 % perdida), y el heredado pasa a Drowsy; el común sigue NMOI porque F sigue bajo 0,25 (lo cruza sólo en el min 109). Con 2 L de cristaloide (fila 6) la entrega relativa se sostiene (≈ 0,78 o más) y F no se activa nunca, pero la PAS heredada queda en 79–78. Es siempre antes de la frontera de colapso y en el paciente que llegó con la PAS más baja.

**B · COMMON_MORE_IMPAIRED (filas 1, 2, 3, 5, 7, 8).** *Dos patrones:* (i) **pérdida relativa antes del umbral absoluto** (filas 3 y 7): la paciente de 72 años, con PAS de llegada 98, tiene PAS heredada 83–80 (sobre el umbral) mientras ya perdió 32–37 % de su entrega y F ≥ 0,25: el común la lee SOMNOLENT y el heredado Alert; (ii) **UNRESPONSIVE con pulso frente a un heredado que no pasa de Drowsy** (filas 1, 2, 5, 8): F cruza 0,80 con entrega relativa ≈ 0,54 y el heredado, atado a la PAS absoluta (65–77), queda a dos bandas porque su escalera sólo escribe «Unresponsive» en el paro. Las filas 2 y 8 llegan a este estado después de una mejora parcial tras 1 L.

**C · TRANSIENT (fila 9).** *Patrón:* un único minuto comparado (el 158) que coincide con el primer minuto en que F cruza el corte 0,80 (margen 0,009) y con el minuto de la orden de recuperación; no hay minutos comparados después de la orden. El registro tiene dos episodios de este tipo (uno por caso, con la misma fisiología común).

## 4 · Contraste de casos: por qué 57m y 72f se separan del heredado en sentidos opuestos

| Dato (corridas sin tratar) | 57m | 72f |
|---|---|---|
| PAS de llegada (heredado = común) | 88 | 98 |
| Distancia al umbral absoluto heredado (80 mmHg) | 8 mmHg | 18 mmHg |
| Primer minuto heredado Drowsy (PAS < 80) | 63 (PAS 79; un minuto antes 80) | 138 (PAS 79; un minuto antes 80) |
| Entrega relativa en ese minuto (pérdida de la llegada) | 0,813 (19 %) | 0,597 (40 %) |
| Primer minuto común SOMNOLENT (F ≥ 0,25) | 109 | 109 |
| Entrega relativa / F en el minuto 109 | 0,680 / 0,2513 | 0,680 / 0,2513 |
| PAS heredada / común en el min 109 | 73 / 61 | 83 / 67 |
| Dirección en el inicio | LEGACY_MORE_IMPAIRED (heredado 46 min antes) | COMMON_MORE_IMPAIRED (común 29 min antes) |
| Primer Obtunded heredado | 175 (PAS 64) | nunca (PAS mínima 66) |
| Entrega relativa y F del común en cada minuto | idénticas a las de 72f | idénticas a las de 57m |

**Lectura mecanística (sin decir cuál es clínicamente superior):** con el mismo manejo, la entrega relativa y F del núcleo común son **idénticas** en los dos pacientes en cada minuto, porque el común mide la pérdida respecto de la llegada de **cada** paciente. Lo único que cambia entre los dos casos es el reloj del heredado, que lee la PAS **absoluta** contra un umbral fijo (80 mmHg): quien llega más bajo (88) lo cruza antes y con menos entrega perdida; quien llega más alto (98) lo cruza 75 min después. Por eso el mismo reloj común queda **después** del heredado en el 57m (el heredado «se adelanta») y **antes** en el 72f (el común «se adelanta»). La PAS que el común escribe sí difiere por caso (a los 109 min, 61 frente a 67), aunque la palabra sea la misma.

## 5 · C5 — `UNRESPONSIVE` con pulso presente

Episodios representativos con el común en UNRESPONSIVE y pulso presente: **1, 2, 5, 8 y 9**. En ningún minuto de las 9 filas el pulso común o heredado está ausente, ni el heredado está en paro. No se rotula ninguna fila como contradictoria.

| Fila | Caso · escenario | Tramo (min) · fase | Min | PAS / PAM común | PAS / PAM heredada | FC común / heredada | Pulso | Entrega relativa | F | Colapso | Heredado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 72f · untreated | 158–188 · NONE · previa a la frontera | 31 | 46–54 / 35–41 | 73–77 / 56–59 | 130–135 / 124–126 | presente (ambos) | 0,456–0,541 | 0,809–1,000 | NONE | ACTIVO: Drowsy, con pulso, sin paro |
| 1 | 72f · untreated | 189–206 · IMPENDING · previa a la frontera | 18 | 41–46 / 31–35 | 70–72 / 55–56 | 135–138 / 126–127 | presente (ambos) | 0,405–0,453 | 1,000–1,000 | IMPENDING | ACTIVO: Drowsy, con pulso, sin paro |
| 1 | 72f · untreated | 207–240 · ESTABLISHED · POSTERIOR A LA FRONTERA (§6) | 34 | 32–41 / 24–31 | 66–70 / 51–54 | 138–143 / 128–130 | presente (ambos) | 0,310–0,403 | 1,000 | ESTABLISHED | ACTIVO: Drowsy, con pulso, sin paro |
| 2 | 72f · severe_deterioration | 194–225 · NONE · previa a la frontera | 32 | 46–55 / 35–42 | 71–75 / 55–58 | 132–137 / 125–127 | presente (ambos) | 0,445–0,539 | 0,811–1,000 | NONE | ACTIVO: Drowsy, con pulso, sin paro |
| 2 | 72f · severe_deterioration | 226–240 · IMPENDING · previa a la frontera | 15 | 42–46 / 32–35 | 68–70 / 53–55 | 137–139 / 127–128 | presente (ambos) | 0,403–0,442 | 1,000–1,000 | IMPENDING | ACTIVO: Drowsy, con pulso, sin paro |
| 5 | 57m · untreated | 158–174 · NONE · previa a la frontera | 17 | 45–49 / 33–36 | 65–67 / 49–50 | 142–144 / 136–137 | presente (ambos) | 0,496–0,541 | 0,809–0,987 | NONE | ACTIVO: Drowsy, con pulso, sin paro |
| 8 | 57m · severe_deterioration | 194–198 · NONE · previa a la frontera | 5 | 49–50 / 36–37 | 65 / 49 | 144 / 137 | presente (ambos) | 0,526–0,539 | 0,811–0,863 | NONE | ACTIVO: Drowsy, con pulso, sin paro |
| 9 | 57m · recovery_after_severe | 158–158 · NONE · previa a la frontera | 1 | 49 / 36 | 67 / 50 | 142 / 136 | presente (ambos) | 0,541 | 0,809 | NONE | ACTIVO: Drowsy, con pulso, sin paro |

*Contexto registrado:* el heredado escribe «Unresponsive» sólo en el paro y varios lectores la tratan como incapacidad total (FD-P3-187). La docencia registró el 2026-11-12 que la fisiología común **puede** representar UNRESPONSIVE con pulso y que **no** se mapea de forma autoritativa en el `mental_status` vivo del heredado (FD-P3-188, 02); esa misma fila deja C5 abierta. El umbral común se alcanza con F ≥ 0,80, es decir con una pérdida de entrega ≥ 45 % (entrega relativa ≤ 0,55 en equilibrio), con PAS común 49–55 y pulso presente.

**Pregunta docente (C5):** ¿es `UNRESPONSIVE_WITH_PULSE` un estado fisiológico aceptable antes del colapso circulatorio o de la terminalidad? Sin respuesta propuesta.

## 6 · Evidencia posterior a la frontera de colapso (aparte; no es evidencia primaria para la semántica previa)

* **Único tramo posterior a la frontera dentro de las 9 filas:** fila 1, min 207–240 (34 min de 83), `AFTER_COLLAPSE_BOUNDARY`. Pulso común y heredado presentes; heredado Drowsy sin paro; común UNRESPONSIVE (F = 1,0 y, además, colapso ESTABLISHED, que lo fuerza).
* Primer minuto: min 207: PAS 41 / PAM 31 / FC 138 (común) frente a PAS 70 / PAM 54 / FC 128 (heredado); entrega relativa 0,403, perfusión relativa 0,417, F 1,000, carga de colapso 0,629.
* Último minuto: min 240: PAS 32 / PAM 24 / FC 143 (común) frente a PAS 66 / PAM 51 / FC 130 (heredado); entrega relativa 0,310, perfusión relativa 0,324, F 1,000, carga de colapso 1,000.
* Bajo FD-AUTH-06/07 un experimento **no** alcanzaría estos minutos (ventana = mínimo entre el límite de tiempo y el primer minuto ESTABLISHED, el 207): el registro los conserva sólo como observación.
* Las otras ocho filas no tienen minutos ESTABLISHED dentro del episodio (las filas 1 y 2 sí pasan por IMPENDING: 189–206 y 226–240).

## 7 · Hoja de decisión docente (en blanco)

Una respuesta no concede autoridad ni aprueba V1 para autoridad (ratificación ≠ concesión, FD-AUTH-11).

**C1-A.** ¿Son las trayectorias de consciencia del núcleo común **previas al colapso** educativamente aceptables?

☐ ACCEPT   ☐ ACCEPT_WITH_LIMITATION   ☐ RECALIBRATE   ☐ INSUFFICIENT_EVIDENCE

Limitación / nota: ______________________________________________

**C1-B.** ¿La consciencia relativa a la llegada sigue siendo aceptable en **ambos** casos de HDA?

☐ YES   ☐ YES_WITH_LIMITATION   ☐ NO

Limitación / nota: ______________________________________________

**C1-C.** ¿Son aceptables los límites actuales SOMNOLENT / OBTUNDED / UNRESPONSIVE para pruebas de autoridad **de desarrollo**?

☐ YES   ☐ YES_WITH_LIMITATION   ☐ NO

Limitación / nota: ______________________________________________

**C5.** ¿Es `UNRESPONSIVE_WITH_PULSE` aceptable como estado fisiológico del núcleo común antes de definir un mapeo terminal?

☐ YES   ☐ YES_BUT_NOT_RESIDENT_VISIBLE   ☐ NO

Limitación / nota: ______________________________________________

Persona docente: ____________________    Fecha: ____________

## 8 · Fuentes y reproducibilidad

`docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json` (episodios, tabla docente, dirección opuesta) · `docs/revision/PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json` (categorías, PAS/PAM/FC/pulso, lactato y TRC por minuto) · `docs/revision/PHASE3_GI_SNAPSHOT_SENSITIVITY.json` (curso físico) · `docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1.json` (valores de V1) · `docs/COLA_DECISIONES_AI_ADVISOR.md` (FD-P3-182, 187, 188) · `family_engine.py` (escalera heredada). La reconstrucción de los episodios con las funciones de prueba existentes reproduce **exactamente** los 15 episodios registrados.
