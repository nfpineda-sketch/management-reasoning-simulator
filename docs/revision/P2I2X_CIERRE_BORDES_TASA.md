# P2I-2X · Cierre de los bordes de verdad del caso y de dominio, y tasa de sangrado densificada

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución, no migra GI ni otra familia, no refiltra el lactato (P2I-2R sigue en pausa);
- no calibra la presión ni la FC, ni activa el colapso;
- no se ajusta al motor heredado y no elige ningún conjunto final de parámetros ocultos;
- no cambia ninguna restricción docente: usa exactamente las de P2I-2V-R.

Código: `clinical_core/blood_rate_boundary.py` (regla de verdad del caso, tasas, diseño, taxonomía, política y
evaluación; congelado antes de evaluar) y `clinical_core/blood_rate_report.py` (sólo este informe). Números:
`docs/revision/P2I2X_blood_rate_boundary.json`. Registros de partida, cerrados: P2I-2V-R (`a9ab10d8…`) y P2I-2W
(`5257b233…`).

## 1. Compatibilidad con la verdad del caso (decisiones docentes 1 y 2)

<!-- generado:verdad -->
| Caso | Verdad del repositorio (POCUS) | Banda candidata comprometida | Referencia euvolémica |
|---|---|---|---|
| 57m | pocus_lv: «small cavity, hyperdynamic, near-obliteration in systole» (`clinical_cases.py:154`); pocus_ivc: «0.9 cm, near-complete inspiratory collapse» (`clinical_cases.py:155`) | 0,2–0,5 (medio 0,35); inferencia candidata | 0,6–0,8 |
| 72f | pocus_lv: «hyperdynamic contraction» (`clinical_cases.py:156`); pocus_ivc: «1.1 cm, >50% inspiratory collapse» (`clinical_cases.py:156`) | 0,3–0,6 (medio 0,45); inferencia candidata | 0,6–0,8 |

Cajas de P2I-2W con una posición fuera de la banda del caso: sus candidatos quedan `REJECTED_BY_CASE_TRUTH_COMPATIBILITY` sin simular.

| Caja de P2I-2W | Caso fuera de banda | Sobrevivientes conjuntos | Sobrevivientes de cada caso solo (P2I-2W) |
|---|---|---|---|
| tasa = 10 · 57m = 0,65 | 57m | 0 | 57m 0 |
| tasa = 10 · 57m = 0,8 | 57m | 0 | 57m 0 |
| tasa = 10 · 72f = 0,75 | 72f | 0 | 72f 2394 |
| tasa = 10 · 72f = 0,9 | 72f | 0 | 72f 2394 |
| tasa = 20 · 57m = 0,65 | 57m | 0 | 57m 0 |
| tasa = 20 · 57m = 0,8 | 57m | 0 | 57m 0 |
| tasa = 20 · 72f = 0,75 | 72f | 0 | 72f 0 |
| tasa = 20 · 72f = 0,9 | 72f | 0 | 72f 0 |
| esquina (todos los primeros pasos) | 57m, 72f | 0 | 57m 0, 72f 798 |
| meta = 1 · 57m = 0,65 | 57m | 0 | 57m 411 |
| meta = 1 · 57m = 0,8 | 57m | 0 | 57m 0 |
| meta = 1 · 72f = 0,75 | 72f | 0 | 72f 399 |
| meta = 1 · 72f = 0,9 | 72f | 0 | 72f 0 |
| τ = 480 · 57m = 0,65 | 57m | 0 | 57m 0 |
| τ = 480 · 57m = 0,8 | 57m | 0 | 57m 0 |
| τ = 480 · 72f = 0,75 | 72f | 0 | 72f 0 |
| τ = 480 · 72f = 0,9 | 72f | 0 | 72f 0 |
| τ = 960 · 57m = 0,65 | 57m | 0 | 57m 0 |
| τ = 960 · 57m = 0,8 | 57m | 0 | 57m 0 |
| τ = 960 · 72f = 0,75 | 72f | 0 | 72f 0 |
| τ = 960 · 72f = 0,9 | 72f | 0 | 72f 0 |
| 57m = 0,65 | 57m | 0 | 57m 2340 |
| 57m = 0,65 · 72f = 0,75 | 57m, 72f | 2268 | 57m 2340, 72f 2394 |
| 57m = 0,65 · 72f = 0,9 | 57m, 72f | 0 | 57m 2340, 72f 0 |
| 57m = 0,8 | 57m | 0 | 57m 0 |
| 57m = 0,8 · 72f = 0,75 | 57m, 72f | 0 | 57m 0, 72f 2394 |
| 57m = 0,8 · 72f = 0,9 | 57m, 72f | 0 | 57m 0, 72f 0 |
| 72f = 0,75 | 72f | 0 | 72f 2394 |
| 72f = 0,9 | 72f | 0 | 72f 0 |

En total, 2268 sobrevivientes conjuntos de P2I-2W quedan rechazados por compatibilidad con la verdad del caso.
<!-- /generado:verdad -->

- **Qué es verdad y qué es interpretación.**
  - Verdad del repositorio: las líneas POCUS de cada caso (tabla), con su fuente. Describen un fenotipo de llenado bajo:
    VCI colapsada y VI pequeño o hiperdinámico.
  - Interpretación: los números de la banda (57m 0,2–0,5; 72f 0,3–0,6) y la referencia euvolémica (0,6–0,8). Las dos
    son inferencia candidata comprometida en `gi_reference` desde P2F, sin aprobación docente; la referencia es sólo
    diagnóstica, porque ningún caso la enuncia. `preload_fraction` sigue siendo una decisión docente pendiente.
- **Por qué alcanza para rechazar 0,65 y 0,75.**
  - La banda de cada caso queda en o por debajo del límite inferior de la referencia euvolémica (0,6).
  - 0,65 y 0,75 caen fuera de la banda del caso. Además caen dentro de la referencia euvolémica candidata, lo que no
    concuerda con el fenotipo de llenado bajo que el POCUS describe.
  - La regla sólo usa la banda comprometida; la referencia no entra en el código.
  - No se endureció la banda ni se infirió una posición exacta: toda la banda comprometida sigue siendo compatible.
- **Disposición de 0,65 / 0,75.** `REJECTED_BY_CASE_TRUTH_COMPATIBILITY`, sin simular. Lo mismo vale para 0,8 / 0,9.
  Los 2268 sobrevivientes conjuntos de P2I-2W con 57m en 0,65 y 72f en 0,75 dejan de ser candidatos del caso.
- **Por qué no se evaluó la terna «tasa 10, 57m 0,65, 72f 0,75»** (decisión docente 2). Sus posiciones ya están
  excluidas por la verdad del caso, así que no responde la pregunta clínica. La pregunta de la tasa se responde abajo
  con las posiciones compatibles.

## 2. Tasa de sangrado común entre 5 y 10 (decisión docente 3, P2I-2X-1)

<!-- generado:tasa -->
Congelamiento de P2I-2X: `668bad9903da9a4ee1d49a5e2be06f7be7795140091b98d898a169b8682c67a5`, comprometido antes de evaluar 6, 7, 8 y 9 (una prueba lo fija). Registros: P2I-2V-R `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893`, P2I-2W `5257b2336caa76819bdc1f5f3a946dc440dbff88c9e101d9ed25c38287772f6e`.

Región: la superviviente de P2I-2V-R, con 57m en 0,5 y 72f en 0,6: 52488 candidatos conjuntos por tasa. El prefiltro exacto (restricciones que no dependen de la tasa: FD-BLD-01, FD-BLD-02, SECOND-UNIT, FD-BLD-04, FD-BLD-05, FD-BLD-07, FD-BLD-09) rechaza 45036 sin simular ninguna tasa; se simulan 7452 por tasa.

«57m tras el prefiltro» y «72f tras el prefiltro»: cada caso por separado, pero sólo entre los candidatos que pasan el prefiltro exacto de los dos casos (sensibilidad acotada, no el recuento de cada caso con su propio prefiltro).

| Tasa (mL-eq/min) | Candidatos | Rechazo exacto | Simulados | Falla U-OUT 57m | Falla U-OUT 72f | Sobreviven | 57m tras el prefiltro | 72f tras el prefiltro | Ilegibles |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 52488 | 45036 | 7452 | 4698 | 4698 | 2268 | 2268 | 2394 | 0 |
| 6 (nueva) | 52488 | 45036 | 7452 | 5616 | 4698 | 1512 | 1512 | 2394 | 0 |
| 7 (nueva) | 52488 | 45036 | 7452 | 7452 | 6534 | 0 | 0 | 798 | 0 |
| 8 (nueva) | 52488 | 45036 | 7452 | 7452 | 7452 | 0 | 0 | 0 | 0 |
| 9 (nueva) | 52488 | 45036 | 7452 | 7452 | 7452 | 0 | 0 | 0 | 0 |
| 10 | 52488 | 45036 | 7452 | 7452 | 7452 | 0 | 0 | 0 | 0 |

Primera restricción que falla, por caso (entre los simulados), y dónde sale U-OUT de su envolvente (filas distintas, por minuto y lado):

| Tasa | 57m: primera falla | 72f: primera falla | U-OUT 57m | U-OUT 72f |
|---|---|---|---|---|
| 5 | U-OUT 4698 · FD-BLD-06 486 | U-OUT 4698 · FD-BLD-06 360 | 120:bajo (108), 30:bajo (108), 60:bajo (108) | 120:bajo (108), 30:bajo (108), 60:bajo (108) |
| 6 | U-OUT 5616 · FD-BLD-06 324 | U-OUT 4698 · FD-BLD-06 360 | 120:bajo (126), 30:bajo (108), 60:bajo (108) | 120:bajo (108), 30:bajo (108), 60:bajo (108) |
| 7 | U-OUT 7452 | U-OUT 6534 · FD-BLD-06 120 | 120:bajo (162), 30:bajo (108), 60:bajo (108) | 120:bajo (144), 30:bajo (108), 60:bajo (108) |
| 8 | U-OUT 7452 | U-OUT 7452 | 120:bajo (162), 30:bajo (162), 60:bajo (162) | 120:bajo (162), 30:bajo (162), 60:bajo (162) |
| 9 | U-OUT 7452 | U-OUT 7452 | 120:bajo (162), 30:bajo (162), 60:bajo (162) | 120:bajo (162), 30:bajo (162), 60:bajo (162) |
| 10 | U-OUT 7452 | U-OUT 7452 | 120:bajo (162), 30:bajo (162), 60:bajo (162) | 120:bajo (162), 30:bajo (162), 60:bajo (162) |

Envolventes de los sobrevivientes (los dos casos juntos):

| Tasa | Gasto sin tratar 30′ / 60′ / 120′ | Caída de Hb 60′ / 120′ |
|---|---|---|
| 5 | 0,90–0,94 / 0,80–0,87 / 0,56–0,74 | 0,03–0,07 / 0,08–0,27 |
| 6 | 0,88–0,92 / 0,75–0,84 / 0,50–0,68 | 0,04–0,09 / 0,16–0,33 |
| 7 | — / — / — | — / — |
| 8 | — / — / — | — / — |
| 9 | — / — / — | — / — |
| 10 | — / — / — | — / — |

**FACULTY-CONSTRAINED BLEED-RATE CANDIDATE INTERVAL.** Tasa más alta con al menos un sobreviviente conjunto: 6. Tasa más baja sin sobreviviente conjunto: 7. El límite queda entre dos tasas probadas contiguas. Los sobrevivientes no crecen con la tasa. No es un valor aprobado ni se interpola.

Las otras posiciones de cada banda, para cada caso solo (un sobreviviente conjunto necesita los dos casos):

| Caso y posición | Candidatos por tasa | Rechazo exacto | Tasa 5: cumple / falla U-OUT | Tasa 6: cumple / falla U-OUT | Tasa 7: cumple / falla U-OUT | Tasa 8: cumple / falla U-OUT | Tasa 9: cumple / falla U-OUT | Tasa 10: cumple / falla U-OUT |
|---|---|---|---|---|---|---|---|---|
| 57m 0,2 (inf.) | 52488 | 52488 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 57m 0,35 (medio) | 52488 | 49572 | 0 / 2916 | 0 / 2916 | 0 / 2916 | 0 / 2916 | 0 / 2916 | 0 / 2916 |
| 72f 0,3 (inf.) | 52488 | 52488 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 72f 0,45 (medio) | 52488 | 49734 | 0 / 2754 | 0 / 2754 | 0 / 2754 | 0 / 2754 | 0 / 2754 | 0 / 2754 |

Filas calculadas: 5031. Filas ilegibles: 8. Contradicciones en las comprobaciones cruzadas: 0.
<!-- /generado:tasa -->

**Lectura.**
- Con la tasa común y las posiciones compatibles, sobreviven 2268 candidatos con 5 y 1512 con 6. Con 7, 8, 9 y 10 no
  sobrevive ninguno.
- El límite que ponen las restricciones docentes queda entre 6 y 7 mL-eq/min, dos tasas probadas contiguas. Entre las
  tasas exploradas sobreviven 2,5, 5 y 6; 1,25 (P2I-2V-R) y 7 no. No se interpola ni se aprueba ningún valor.
- **El intervalo es condicional a dos cosas.**
  - A la región de P2I-2V-R (meta del relleno ≤ 0,75 y τ ≤ 240): el escaneo no cruzó las tasas 6–9 con los
    sobrevivientes de P2I-2W que siguen dentro de la banda (meta 1,0; τ 480).
  - A la posición en el borde superior de cada banda candidata (57m 0,5; 72f 0,6), que no está aprobada.
- Lo decide U-OUT por abajo: con 7, 57m queda bajo su envolvente en todos los candidatos simulados (a los 120 min,
  y a los 30 y 60 en parte de las filas). 72f solo tolera 7 en 798 candidatos, que no tienen pareja en 57m.
- FD-BLD-06 rechaza algunos candidatos más con 5, 6 y 7 (la dilución con 1 y 2 L).
- La Hb no decide la cota: U-HB, leída sola, se cumple en las 36 filas de cada caso con 6, 7 y 8 (comprobación
  aparte, con las funciones congeladas).
- **Sin filas ilegibles que cuenten.** Hay 8 filas ilegibles (57m, tasas altas), pero ningún candidato conjunto ni de
  un caso solo quedó ilegible: U-OUT ya los rechaza.
- **Las otras posiciones de la banda.**
  - Las posiciones inferiores (57m 0,2; 72f 0,3) caen enteras en el prefiltro exacto: alguna restricción que no
    depende de la tasa las rechaza a cualquier tasa (en 57m basta FD-BLD-02, como en P2I-2V-R).
  - Las medias (0,35; 0,45) quedan rechazadas por U-OUT a todas las tasas.
  - La interacción con la región de precarga compatible no abre ninguna tasa más.

### 2.1 Trayectorias representativas

<!-- generado:representativos -->
Los tres representativos de P2I-2V-R (su regla congelada), con sólo la tasa cambiada. Se muestra el medio; la PAS y el lactato no se leen.

**Tasa 5.** bajo: 57m no cumple U-OUT; 72f no cumple U-OUT · medio: 57m cumple todas; 72f cumple todas · alto: 57m no cumple U-OUT; 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,90 | 0,80 | 0,60 | 1,00 | 0,93 | 0,87 | 0,73 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,53 | 6,40 | 6,39 | 6,36 | 6,24 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 | 0 | -143 | -274 | -505 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,20 | 0,34 | 0,32 | 0,29 | 0,24 |
| déficit crítico efectivo | 0,15 | 0,24 | 0,33 | 0,50 | 0,15 | 0,21 | 0,27 | 0,39 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

**Tasa 6.** bajo: 57m no cumple U-OUT; 72f no cumple U-OUT · medio: 57m cumple todas; 72f cumple todas · alto: 57m no cumple U-OUT; 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,88 | 0,75 | 0,50 | 1,00 | 0,92 | 0,84 | 0,67 |
| Hb (g/dL) | 6,70 | 6,69 | 6,65 | 6,49 | 6,40 | 6,39 | 6,35 | 6,20 |
| volumen circulante C (mL-eq) | 0 | -172 | -329 | -606 | 0 | -172 | -329 | -606 |
| DO2 | 0,34 | 0,30 | 0,25 | 0,17 | 0,34 | 0,31 | 0,28 | 0,22 |
| déficit crítico efectivo | 0,15 | 0,25 | 0,36 | 0,59 | 0,15 | 0,22 | 0,29 | 0,45 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

**Tasa 7.** bajo: 57m no cumple U-OUT; 72f no cumple U-OUT · medio: 57m no cumple U-OUT; 72f no cumple U-OUT · alto: 57m no cumple U-OUT; 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,86 | 0,71 | 0,40 | 1,00 | 0,90 | 0,81 | 0,60 |
| Hb (g/dL) | 6,70 | 6,68 | 6,64 | 6,45 | 6,40 | 6,38 | 6,34 | 6,16 |
| volumen circulante C (mL-eq) | 0 | -201 | -384 | -707 | 0 | -201 | -384 | -707 |
| DO2 | 0,34 | 0,29 | 0,24 | 0,13 | 0,34 | 0,31 | 0,27 | 0,20 |
| déficit crítico efectivo | 0,15 | 0,27 | 0,40 | 0,67 | 0,15 | 0,23 | 0,32 | 0,51 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

**Tasa 8.** bajo: 57m no cumple U-OUT (ilegible: FD-BLD-06); 72f no cumple U-OUT · medio: 57m no cumple U-OUT; 72f no cumple U-OUT · alto: 57m no cumple U-OUT; 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,83 | 0,66 | 0,29 | 1,00 | 0,89 | 0,77 | 0,52 |
| Hb (g/dL) | 6,70 | 6,68 | 6,63 | 6,41 | 6,40 | 6,38 | 6,33 | 6,12 |
| volumen circulante C (mL-eq) | 0 | -230 | -439 | -808 | 0 | -230 | -439 | -808 |
| DO2 | 0,34 | 0,28 | 0,22 | 0,09 | 0,34 | 0,30 | 0,26 | 0,17 |
| déficit crítico efectivo | 0,15 | 0,29 | 0,45 | 0,77 | 0,15 | 0,25 | 0,35 | 0,57 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

**Tasa 9.** bajo: 57m no cumple U-OUT (ilegible: FD-BLD-06); 72f no cumple U-OUT · medio: 57m no cumple U-OUT; 72f no cumple U-OUT · alto: 57m no cumple U-OUT (ilegible: FD-BLD-06); 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,81 | 0,61 | 0,17 | 1,00 | 0,87 | 0,74 | 0,44 |
| Hb (g/dL) | 6,70 | 6,68 | 6,62 | 6,37 | 6,40 | 6,38 | 6,32 | 6,08 |
| volumen circulante C (mL-eq) | 0 | -258 | -494 | -909 | 0 | -258 | -494 | -909 |
| DO2 | 0,34 | 0,28 | 0,20 | 0,05 | 0,34 | 0,30 | 0,25 | 0,14 |
| déficit crítico efectivo | 0,15 | 0,31 | 0,49 | 0,86 | 0,15 | 0,26 | 0,38 | 0,64 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

**Tasa 10.** bajo: 57m no cumple U-OUT (ilegible: U-HB, FD-BLD-06); 72f no cumple U-OUT · medio: 57m no cumple U-OUT (ilegible: FD-BLD-06); 72f no cumple U-OUT · alto: 57m no cumple U-OUT (ilegible: U-HB, FD-BLD-06); 72f no cumple U-OUT.

| Medio, sin tratar | 57m 0′ | 57m 30′ | 57m 60′ | 57m 120′ | 72f 0′ | 72f 30′ | 72f 60′ | 72f 120′ |
|---|---|---|---|---|---|---|---|---|
| gasto relativo | 1,00 | 0,79 | 0,56 | 0,04 | 1,00 | 0,86 | 0,71 | 0,36 |
| Hb (g/dL) | 6,70 | 6,68 | 6,61 | 6,32 | 6,40 | 6,38 | 6,31 | 6,04 |
| volumen circulante C (mL-eq) | 0 | -287 | -549 | -1010 | 0 | -287 | -549 | -1010 |
| DO2 | 0,34 | 0,27 | 0,19 | 0,01 | 0,34 | 0,29 | 0,24 | 0,12 |
| déficit crítico efectivo | 0,15 | 0,33 | 0,53 | 0,97 | 0,15 | 0,27 | 0,41 | 0,71 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica | crítica | crítica | crítica |

<!-- /generado:representativos -->

## 3. Bordes e identificabilidad (decisiones docentes 4 y 5)

<!-- generado:bordes -->
Clase: la regla congelada (cuántos valores explorados compatibles sobreviven). Borde: cada lado por separado y su estado. «Identificado» sólo si la clase es WELL_CONSTRAINED y los dos lados los acotan las restricciones docentes.

| Parámetro | Explorados | Sobreviven | Clase | Lado inferior | Lado superior | Borde | Identificado |
|---|---|---|---|---|---|---|---|
| tasa de sangrado común (mL-eq/min) | 1,25, 2,5, 5, 6, 7, 8, 9, 10, 20 | 2,5, 5, 6 | PARTIALLY_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | no |
| posición de precarga de llegada (57m) | 0,2, 0,35, 0,5, 0,65, 0,8 | 0,5 | WELL_CONSTRAINED | acotado por restricción | verdad del caso | CASE_TRUTH_BOUND | no |
| posición de precarga de llegada (72f) | 0,3, 0,45, 0,6, 0,75, 0,9 | 0,6 | WELL_CONSTRAINED | acotado por restricción | verdad del caso | CASE_TRUTH_BOUND | no |
| B0 (mL-eq) | 3000, 4000, 5000 | 3000, 4000, 5000 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| λ/κ (mL-eq) | 600, 833, 1500 | 600, 833, 1500 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| meta del relleno (fracción de lo perdido) | 0,25, 0,5, 0,75, 1 | 0,5, 0,75, 1 | PARTIALLY_CONSTRAINED | acotado por restricción | límite del dominio | DOMAIN_UPPER_BOUND | no |
| τ del relleno (min) | 60, 120, 240, 480, 960 | 120, 240, 480 | PARTIALLY_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | no |
| capacidad del relleno (mL-eq) | 100, 500, 1000 | 100, 500, 1000 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| contenido de GR de la unidad (Hb, g/dL) | 18, 20, 22 | 18, 20, 22 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| volumen de la unidad (mL-eq) | 250, 300, 350 | 250, 300, 350 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| fracción intravascular inicial del cristaloide | 0,125, 0,2, 0,3 | 0,2, 0,3 | PARTIALLY_CONSTRAINED | acotado por restricción | abierto (borde de la cuadrícula) | OPEN_UPPER_GRID_EDGE | no |
| τ de redistribución del cristaloide (min) | 15, 30, 60 | 15, 30, 60 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| fracción transitoria del cristaloide | 0,4, 0,6, 0,8 | 0,4, 0,6, 0,8 | POORLY_IDENTIFIED | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| ρ (reserva de extracción) | 1, 2,5, 3 | 1, 2,5, 3 | NON_IDENTIFIABLE_SEPARATELY | abierto (borde de la cuadrícula) | abierto (borde de la cuadrícula) | OPEN_BOTH_GRID_EDGES | no |
| κ (por separado) | — | — | NON_IDENTIFIABLE_SEPARATELY | — | — | — | no (sólo λ/κ llega a alguna ancla; la Hb nunca lee κ) |
| λ (por separado) | — | — | NON_IDENTIFIABLE_SEPARATELY | — | — | — | no (sólo λ/κ llega a alguna ancla) |
<!-- /generado:bordes -->

- **Meta del relleno: DOMAIN_UPPER_BOUND (decisión docente 4).**
  - El núcleo exige 0 ≤ meta ≤ 1 (`derived.py`, invariante de `CoreProfile`; una prueba lo comprueba): 1,0 es el
    límite exacto del dominio.
  - Significa reponer, de forma asintótica, todo el volumen circulante perdido, y nunca más de la capacidad. No repone
    GR y no está garantizado dentro del horizonte simulado.
  - No es un valor aprobado y su clase de identificabilidad sigue aparte (PARTIALLY_CONSTRAINED).
- **Posición de llegada: CASE_TRUTH_BOUND.** Por abajo la acotan las restricciones docentes; por arriba, la banda del
  caso. Por recuento es WELL_CONSTRAINED (sobrevive un solo valor compatible), pero no está identificada: el lado
  superior es la verdad del caso, no una restricción.
- **Tasa común y τ del relleno: INTERIOR.** Las dos quedan acotadas por restricciones docentes en ambos lados, a la
  resolución explorada.
- **Fracción intravascular inicial del cristaloide** (el parámetro que P2I-2V-R rotulaba «fracción retenida», §5):
  sigue OPEN_UPPER_GRID_EDGE. Las dimensiones no extendidas siguen OPEN_BOTH_GRID_EDGES.
- **El intervalo de la tasa es condicional** (§2): a la región de P2I-2V-R y a la posición en el borde superior de la
  banda candidata.

## 4. Nivel 1, HR1 y sondas históricas (decisión docente 6, P2I-2X-3)

<!-- generado:auditoria -->
| Comprobación | Escribe | Cómo | Clase | Por qué |
|---|---|---|---|---|
| RR1 (`check_rr1`) | V | V −8 por minuto durante 40 min y +900 en el minuto 40, desde la llegada sintética de las sondas | SYNTHETIC_STATE_PERTURBATION | un shock genérico y su corrección sobre la coordenada de precarga, para comprobar que aclarar el lactato no lleva la FR bajo su piso ventilatorio; sin caso GI, sin GR, sin relleno y sin cambio de Hb |
| HR1-HR4 (`check_hr`) | V | V −8 por minuto durante 30 min y +640 en el minuto 30, desde la llegada declarada de cada caso GI | SYNTHETIC_STATE_PERTURBATION | las reglas son la respuesta cronotrópica al deterioro y a la recuperación hemodinámicos (KD-S2, P2E-1, P2D-3) y leen sólo la FC y el impulso simpático. La pérdida mueve sólo V (sin GR, sin relleno, Hb sin cambio) y la reposición no es ningún producto: es una perturbación hipovolémica de la coordenada de precarga, no una hemorragia. Pasarla por BloodState exigiría valores de relleno y de volumen de llegada que no están aprobados |
| PL1-PL3 (`check_preload`) | V | V fijada en 0, 250, 500 y 750 en el minuto 0 de la llegada neutra (lecturas estáticas) | SYNTHETIC_STATE_PERTURBATION | lee la forma de la curva de precarga y el límite que pone una bomba deprimida; sin pérdida ni producto |
| PL4 (`check_congestion`) | V | V +2900 en el primer minuto, desde una llegada sintética con reserva de bomba 0,3 | SYNTHETIC_STATE_PERTURBATION | alcanzabilidad del agua pulmonar con exceso de precarga y reserva limitada: una carga de volumen, no un producto (la cinética del cristaloide no está aprobada) ni una hemorragia |
| DM1 (`check_demand`) | Hb | Hb −30 % en el minuto 0 de la llegada neutra | SYNTHETIC_STATE_PERTURBATION | una anemia aislada que fija la entrega mientras cambia la demanda; no hay pérdida de sangre |

Ninguna es PHYSIOLOGICAL_HAEMORRHAGE_PROBE, así que ninguna se convierte a BloodState. Todas siguen escribiendo la coordenada de forma directa, rotuladas, y no son evidencia sobre la fisiología de la hemorragia, la Hb ni la DO2 (`NOT_EVIDENCE_FOR` = blood loss, haemorrhage severity, Hb, DO2, refill, PRBC, clinical case calibration).

| Sonda histórica de nivel 2 | Familia | Estado |
|---|---|---|
| `vasodilation_with_preload_loss` | sepsis | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `pump_failure_then_bolus` | ACS | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `preload_dependent` | RV infarct / PE | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `overload` | pulmonary oedema | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
<!-- /generado:auditoria -->

- **Clase confirmada.** La docencia confirmó la clase SYNTHETIC_STATE_PERTURBATION. `NOT_EVIDENCE_FOR` es ahora su
  lista: pérdida de sangre, gravedad de la hemorragia, Hb, DO2, relleno, GR y calibración de casos clínicos.
- **HR1 en la región de P2F (P2I-2X-3).**
  - `decision_pack.p2f_rejection` excluye la posición inferior de P2F (57m 0,2) porque la sonda HR1 vacía el
    ventrículo. Esa sonda mueve sólo V: sin pérdida de GR, sin hemorragia de BloodState, sin relleno y sin cambio de
    Hb. No puede, por sí sola, mostrar que esa posición es clínicamente imposible.
  - Su motivo queda rotulado `STRUCTURAL_HARNESS_OUTCOME` («no es evidencia clínica del caso»). La prueba HR1 sigue
    como prueba estructural.
  - No se readmite 0,2: la región estructuralmente admisible de P2F no cambia.
- **Otra evidencia sobre 0,2 en 57m.**
  - En P2I-2V-R, FD-BLD-02 por sí sola (con una unidad, el gasto sube más del 40 %) deja 0 candidatos de 57m en la
    posición inferior, también sin U-OUT.
  - Aquí, el prefiltro exacto la rechaza a todas las tasas.
  - Esa es evidencia de una restricción docente, no de HR1.
- **Sondas de bolo históricas:** siguen como HISTORICAL_PROBE, sin convertir, fuera de la evidencia de calibración
  activa y de todo recuento.

## 5. Cristaloide: auditoría semántica (P2I-2X-2; no se evalúa ninguna grilla)

- **Parámetro.** `crystalloid_effective_ml_per_ml` (en `Crystalloid`, `effective_ml_per_ml`), con valores explorados
  0,125, 0,2 y 0,3.
- **Ecuación** (`interventions/fluids.py`, `Crystalloid.contribute`), por minuto:
  - entra `ganancia = mL administrados × effective_ml_per_ml` como CRYSTALLOID_IN;
  - `transient_share × ganancia` va a un compartimento que sale con τ = `leak_tau_min` (CRYSTALLOID_OUT);
  - el resto no sale nunca en este modelo.
- **Qué representa.** Es la **fracción intravascular inicial**: la parte de cada mL que entra en el volumen circulante
  al administrarse. No es la fracción retenida, que es lo que leen FD-BLD-04 y 05. La fracción asintótica retenida es
  `effective × (1 − transient_share)`.
- **Dominio.** El código sólo exige que sea positivo; por definición es una fracción de lo administrado, (0, 1].
- **Relación con las observaciones aprobadas.**
  - FD-BLD-04 (0,15–0,30) lee el máximo retenido en los primeros 30 min: queda por debajo de la fracción inicial,
    según cuánto se redistribuya durante la infusión.
  - FD-BLD-05 (0,15–0,25 a los 30 min, 0,10–0,20 a los 60, 0,05–0,15 a los 120) depende de la fracción inicial, de la
    transitoria y de τ juntas.
  - FD-BLD-06 (la dilución de Hb con 1 y 2 L) depende de la ganancia frente a B0.
  - Ninguna lee la fracción inicial sola.
- **Por qué la continuación fue ambigua.**
  - 0,125 es el literal heredado convertido (`family_engine` `crystalloid_per_ml` 0,00015 × 300/0,36); 0,2 y 0,3 se
    agregaron en P2I-2U. No tienen paso ni razón constantes.
  - Además, la dimensión no es la cantidad que leen las observaciones: extenderla sola no tiene una interpretación
    fisiológica clara.
- **Propuesta para un paquete futuro (no evaluada, ningún valor aprobado).** Explorar las dos cantidades
  interpretables en lugar de la fracción transitoria:
  - fracción inicial f₀ ∈ {0,15; 0,20; 0,25; 0,30; 0,35} (diferencia constante 0,05), que cubre FD-BLD-04 con un
    paso más;
  - fracción asintótica retenida f∞ ∈ {0; 0,05; 0,10; 0,15; 0,20} (diferencia constante 0,05), con f∞ < f₀;
  - τ ∈ {15; 30; 60} (razón constante 2, como hoy).

  De ahí, `transient_share = 1 − f∞ / f₀`.
  - f∞ no es la lectura de FD-BLD-05 a los 120 min: a esa hora el compartimento transitorio todavía no se vació.
  - Por eso su grilla cruza los dos bordes de esa envolvente (0,05–0,15), y FD-BLD-05 puede rechazar en ambas
    direcciones.

## 6. Higiene de los resúmenes de informe (P2I-2X-4)

- **Problema.** El corte P2I-1, las sondas P2I-2T y las anclas P2I-2U fijaban todas las fuentes de `clinical_core`.
  Cambiar el texto de un informe de P2I-2V-R o P2I-2W obligaba a regenerarlos, aunque no puede cambiar sus números.
- **Decisión.** Salen de esos resúmenes los informes de artefactos posteriores: `blood_filter_report.py`,
  `blood_extension_report.py` y `blood_rate_report.py` (`lactate_slice.DOWNSTREAM_REPORTS`).
- **Condiciones que cumple la exclusión.**
  - La dirección de dependencia está probada: ningún módulo de `clinical_core` fuera de esa lista los importa (los
    informes sí se importan entre sí). Una prueba recorre los imports de todos; la guarda es estática, y hoy el núcleo
    no usa importaciones dinámicas.
  - Quedan también fuera del congelamiento de P2I-2X y del paquete P2G.
  - Sus funciones de presentación conservan su prueba de bloques generados contra su JSON.
- **Excepción.** `blood_filter_report.py` no es sólo de presentación: también contiene `diagnostic()`, que calculó el
  diagnóstico histórico de P2I-2V (`P2I2V_blood_diagnostic.json`).
  - Ese registro está cerrado y ningún módulo hasheado lo lee, así que la exclusión no cambia ningún artefacto.
  - Pero el código de `diagnostic()` ya no lo cubre ningún resumen.
  - El comentario «render-only» de `lactate_slice.DOWNSTREAM_REPORTS` es inexacto para ese módulo. Corregirlo toca un
    archivo congelado; queda registrado como deuda (TD-88).
- **Lo que no cambia.** Los renderizadores del propio corte y del paquete P2G siguen dentro, como antes.

## 7. Qué no hace

- No cambia ninguna restricción docente (`blood_constraints.py` byte a byte, una prueba lo fija), ni FD-BLD-03, que
  sigue cualitativa.
- No aprueba ni elige ningún parámetro oculto, ni interpola una tasa: el intervalo es una región candidata.
- No evalúa una grilla nueva de cristaloide ni extiende ninguna otra dimensión.
- No refiltra el lactato, no usa lactato, PAS ni PAM para filtrar, no calibra la presión ni la FC y no activa el
  colapso.
- No migra, no integra y no puebla ningún valor de familia.

## 8. Decisiones pendientes (docencia)

- Si se acepta la región candidata de la tasa común (sobreviven 2,5, 5 y 6; el límite queda entre 6 y 7), si se
  densifica entre 6 y 7, y si se cruzan las tasas 6–9 con la meta 1,0 y τ 480 (sobrevivientes de P2I-2W dentro de la
  banda).
- Si se adopta la grilla interpretable del cristaloide (§5) para un paquete posterior.
- Si la banda candidata de la posición de llegada se aprueba como banda de la verdad del caso (hoy es inferencia
  candidata).
- Si la región estructuralmente admisible de P2F (lactato, P2I-2R en pausa) debe revisarse ahora que HR1 no cuenta
  como evidencia clínica.
