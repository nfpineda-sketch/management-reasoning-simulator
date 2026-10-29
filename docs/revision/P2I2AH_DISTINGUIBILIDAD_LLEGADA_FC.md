# P2I-2AH · Auditoría de distinguibilidad fisiológica de la FC de llegada

Auditoría de diagnóstico, sin cambios de código ni nuevo congelamiento. Funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión ni la FR, no activa el colapso;
- no aprueba parámetros de FC;
- no ajusta nada al motor heredado: no lo lee.

Punto de partida: HEAD local `ca75297` (P2I-2AG, bloqueada por la reconstrucción de la llegada). La rama remota sigue en
`79a3895`.

## Resumen

- **Pregunta:** por qué el modelo de FC recibe la misma fisiología de llegada para dos pacientes clínicamente distintos.
- **Respuesta:** la FC de llegada lee sólo tres cosas además del ritmo y el betabloqueo:
  - la intrínseca;
  - la razón de entrega de llegada (de la que sale la señal aguda);
  - la deuda de llegada D0.
  Las tres son parámetros por paciente en la arquitectura, pero el diseño de candidatos da a ambos casos el mismo nivel
  de cada banda, y en esas tres bandas los números coinciden en los dos casos. Todo lo demás que difiere entre los casos
  (PA, Hb, lactato, relleno capilar, POCUS) queda en la referencia propia de cada paciente o en estados que la FC no lee
  en la llegada.
- **Clasificación de la procedencia:** B (niveles comunes por diseño) y D (información del caso que existe arriba y la
  FC no consume). No es un error de representación.
- **Intrínseca:** por arquitectura es una propiedad basal de cada paciente (B). El diseño de candidatos la ata entre los
  casos, pero eso es una simplificación del diseño, no fisiología.
- **Severidad de llegada:** la evidencia registrada indica que 57m llega más grave que 72f. El diseño la colapsa a
  niveles comunes. Diagnóstico analítico, sin certificar: con la intrínseca común pero un nivel de llegada propio de cada
  caso, 18 de 5625 combinaciones reproducen las dos llegadas, siempre con 57m más grave.
- **Intrínseca por caso:** como sensibilidad, reutilizando P2I-2AG, sobreviven 5 de 2025. Son una sola predicción,
  porque la ganancia de deuda no actúa con D0 = 0: LOW, 57m con 80 y 72f con 60, ganancia aguda 5,58 y techo 150.
- **Clasificación del bloqueo: BOTH_CONTRIBUTE.** La docencia autoriza la intrínseca por caso sólo si no se colapsa
  fisiología de llegada relevante, y aquí se colapsa. Por eso no se aplica la intrínseca por caso como solución.
  Restaurar la severidad por caso necesita una decisión docente nueva y toca el dominio de D y lactato. No se implementa
  ni se certifica nada, y no hay push.

## 1. Comparación de la llegada: datos registrados (P2I-2AH-1)

Fuente: `clinical_core/gi_reference.py` (INVENTORY, verdad del repositorio).

| Dato registrado | 57m | 72f | Clase |
|---|---|---|---|
| FC | 124 | 112 | DIFFERENT · AUTHORED_CASE_TRUTH |
| PA / PAM | 88/54 · 65,3 | 98/62 · 74,0 | DIFFERENT · AUTHORED_CASE_TRUTH |
| Hb (g/dL) | 6,7 | 6,4 | DIFFERENT · AUTHORED_CASE_TRUTH |
| SpO2 (%) | 97 | 96 | DIFFERENT · AUTHORED_CASE_TRUTH |
| Lactato (mmol/L) | 4,4 | 3,4 | DIFFERENT · AUTHORED_CASE_TRUTH |
| Relleno capilar (s), extremidades | 5, frías | 4, frías | DIFFERENT · AUTHORED_CASE_TRUTH |
| POCUS VI / VCI | casi obliterado en sístole / 0,9 cm, colapso casi completo | hiperdinámico / 1,1 cm, colapso > 50 % | DIFFERENT · AUTHORED_CASE_TRUTH |
| FR, gasometría | 26; pH 7,37, HCO3 17,3 | 24; pH 7,40, HCO3 19,8 | DIFFERENT · AUTHORED_CASE_TRUTH |
| Ritmo / betabloqueo | sinusal / ninguno | sinusal / ninguno | SAME · AUTHORED_CASE_TRUTH |
| Glucemia | 118 | 130 | DIFFERENT · AUTHORED_CASE_TRUTH |

Todos los signos de perfusión, salvo la Hb, señalan a 57m como más grave: PAM menor, lactato mayor, relleno más lento,
VI casi obliterado, VCI menor y bicarbonato más bajo.

## 2. Comparación de la llegada: estado del núcleo (P2I-2AH-1)

Representantes de P2I-2AD, construidos como el núcleo (`hr_shock.full_run`), modo primario. Para cada representante
los valores son:

| Campo | 57m | 72f | Clase |
|---|---|---|---|
| intrínseca declarada | 80 | 80 | SAME · CANDIDATE_DISCRETIZATION (lee la FC) |
| D0 = D en la llegada (LOW / MID / HIGH) | 0 / 20 / 60 | 0 / 20 / 60 | SAME · CANDIDATE_DISCRETIZATION (lee la FC) |
| razón de entrega de llegada (÷ 2,5) | 0,24 / 0,34 / 0,40 | 0,24 / 0,34 / 0,40 | SAME · CANDIDATE_DISCRETIZATION (lee la FC) |
| déficit efectivo / demanda = señal aguda | 0,40 / 0,15 / 0 | 0,40 / 0,15 / 0 | SAME · DERIVED (lee la FC) |
| impulso de llegada | igual | igual | SAME · DERIVED |
| ritmo, betabloqueo | sinusal, 0 | sinusal, 0 | SAME · AUTHORED_CASE_TRUTH (lee la FC) |
| gasto, presión y entrega relativos | 1 | 1 | SAME · DERIVED (normalizados a la propia llegada) |
| V (coordenada), P, T | 0, 1, 1 | 0, 1, 1 | SAME · DERIVED |
| demanda | 1 | 1 | SAME · CANDIDATE_DISCRETIZATION |
| hipoxemia, hipoglucemia (relativas a la llegada) | 0 | 0 | SAME · DERIVED |
| Hb del estado | 6,7 | 6,4 | DIFFERENT · NOT_USED_BY_HR en la llegada (fija la referencia) |
| posición de precarga (LOW / MID / HIGH) | 0,5 | 0,6 | DIFFERENT · NOT_USED_BY_HR en la llegada |
| exceso de lactato declarado | 3,6 / 3,4 / 3,4 | 2,6 / 2,4 / 2,4 | DIFFERENT · NOT_USED_BY_HR |
| PA y PAM registradas | 88/54 | 98/62 | DIFFERENT · NOT_USED_BY_HR (la presión es relativa, 1 en la llegada) |

Señales idénticas que llegan a la FC: intrínseca, D0, razón de entrega (y con ella la señal aguda), ritmo y
betabloqueo; la presión vale 0 en la llegada. Señales distintas que la FC no usa en la llegada: Hb, posición de
precarga, exceso de lactato, PA y PAM, relleno capilar y POCUS.

## 3. Procedencia de la predicción idéntica (P2I-2AH-2, -3)

- `clinical_core/calibration.py:778`: `GICandidate` es «for both cases the same level of each case band».
  `case_values` (`calibration.py:797`) toma cada valor de la banda de cada caso con ese único nivel.
- `clinical_core/gi_reference.py:340-350`: la banda de deuda de llegada es 0 / 20 / 60, «the same for both» (ningún
  caso indica una duración).
- `gi_reference.py:353-359`: la banda de razón de entrega es 0,6 / 0,85 / 1,0, igual para ambos: «the case does not
  measure delivery». Su justificación cita evidencia de cada caso (relleno, Hb, perfusión), pero los números son los
  mismos.
- `gi_reference.py:255-261`: la banda intrínseca es 60 / min(80, FC) / min(100, FC). Como las dos llegadas superan 100,
  coincide en ambos casos.
- En cambio, `gi_reference.py:246-252` (exceso de lactato) y `gi_reference.py:280` (precarga) son bandas propias de cada
  caso, y difieren.
- `clinical_core/blood_fluid_readiness.py:426-428` → `lactate_rebuild.py:394`: los pares (deuda, entrega) de llegada son
  los cinco pares P2F sin cambios. Cada punto del espacio fuente se aplica a ambos casos.
  `lactate_rebuild.py:398` fija la intrínseca en la mitad de su banda para el trabajo de lactato.
- Los representantes LOW / MID / HIGH salen de la región conjunta de P2I-2AD: ambos casos con el mismo punto.
- `hr_shock.py:359`: la razón de entrega se reancla por la reserva de extracción, 2,5, igual para ambos.
- `derived.py:536`: la entrega efectiva es `arrival_delivery_ratio × delivery_rel`, y `delivery_rel` vale 1 en la
  llegada.
- `derived.py:998`: el objetivo simpático suma aguda, presión (0 en la llegada), deuda, hipoxemia e hipoglucemia (0 en la
  llegada).

Clasificación (P2I-2AH-2): la predicción idéntica viene de **B** (el diseño usa intencionalmente niveles comunes de D y
de entrega, y la intrínseca también común) y de **D** (la información del caso existe arriba, pero la FC no la consume
en la llegada). No es A como verdad del caso: que ambos pacientes compartan la fisiología normalizada es un supuesto del
diseño. No es C: no hay una discretización que borre un valor medido, porque ningún caso mide la entrega ni la deuda.

P2I-2AH-3: los pares de deuda y entrega son estados candidatos abstractos y comunes aplicados a ambos casos. Con la
misma etiqueta, los valores fisiológicos son idénticos, y el reanclaje es el mismo.

## 4. Semántica de la intrínseca (P2I-2AH-4)

- **Arquitectura: B, propiedad basal latente de cada paciente.**
  - Pertenece a la capa `physiological_reference` (`state.py:266`): «the patient's non-acute reference».
  - Es un parámetro de caso (`state.py:252`), su banda se define por paciente como «the patient's non-acute resting
    sinus rate» y figura en `FACULTY_DECISIONS`.
- **Uso común:** que la intrínseca sea común viene sólo del diseño de candidatos (un nivel para ambos casos) y de la regla
  de lactato (punto medio). No hay un desajuste de arquitectura que corregir.
- **HR1 y HR2** usan la intrínseca declarada de cada llegada, caso por caso. Su semántica es coherente con una
  intrínseca propia de cada paciente y no cambia (P2I-2AH-10).

## 5. Sensibilidad con intrínseca por caso (P2I-2AH-5, reutilizada de P2I-2AG, no aprobada)

Usa el código congelado de P2I-2AG sobre la misma fisiología; no se volvió a correr la superficie.

| | Resultado |
|---|---|
| combinaciones conjuntas | 5 de 2025 (sólo el representante LOW) |
| par de intrínsecas | 57m 80 · 72f 60 (los otros 8 pares: 0) |
| ganancia aguda (común) | sólo 5,58 |
| ganancia de deuda (común) | las 5, pero no actúa: LOW tiene D0 = 0, así que es una sola predicción |
| techo | sólo 150 |
| FC predicha y desajuste | 126,4 (+2,4) · 109,6 (−2,4) |
| peor desajuste mínimo con intrínseca común | LOW 9,49 · MID 6,86 · HIGH 6,58 lpm |

Es una única solución en el borde de la superficie: el techo más bajo y una sola ganancia aguda. Además explica la
diferencia entre los casos con la basal, no con la severidad. Que sobreviva no la hace correcta.

## 6. La severidad de llegada colapsada (P2I-2AH-6)

- **Señal perdida:** el estado dinámico de llegada (`arrival_delivery_ratio` y `arrival_oxygen_debt`).
  - Es propio de cada paciente por arquitectura (`state.py:268`) y es lo único que da a la FC una severidad de llegada
    absoluta.
  - El diseño lo iguala entre los casos, aunque la evidencia registrada difiere.
  - El exceso de lactato, en cambio, sí se ancla a cada caso. Esa asimetría muestra la información que no llega a D0.
- **Diagnóstico analítico.** Reutiliza la tabla de llegada del registro P2I-2AF (`adb3767b…`), con intrínseca común,
  ganancias y techo comunes, y los cinco pares P2F. No está certificado: los pares desatados no tienen su D y su lactato
  validados.

  | Diseño | Conjuntos compatibles |
  |---|---|
  | el mismo par para ambos casos | 0 de 1125 |
  | un par propio de cada caso | 18 de 5625 |

  En los 18, 57m tiene el par más grave: (deuda superior, entrega inferior), con x0 0,4 y D0 60, o (medio, medio), con
  0,15 y 20. 72f tiene uno menos grave. Hay apoyo en los tres techos (7 / 7 / 4), en la intrínseca 60 o 100, en tres
  ganancias agudas y en dos de deuda.
- **Qué haría falta para restaurarla:** una **NEW FACULTY PARAMETER** (decisión docente): niveles de llegada propios de
  cada caso, o un mapeo de la evidencia de perfusión registrada a esos niveles.
  - No es un arreglo de representación: nada se calcula mal, y el atado y las bandas comunes están declarados.
  - Además toca el dominio de D y lactato, porque D0 y la entrega mueven D y el lactato. P2I-2AD certificó la fisiología
    con los niveles atados, así que habría que volver a certificarla. Por eso no se implementa aquí.

## 7. Clasificación y próxima acción (P2I-2AH-9)

**BOTH_CONTRIBUTE.**
- La intrínseca es por arquitectura una propiedad de cada paciente, y atarla es una elección del diseño.
- La severidad de llegada, también propia de cada paciente, está colapsada a niveles comunes pese a la evidencia de que
  los casos difieren.
- Cada una, desatada por separado, deja algunos sobrevivientes. La de severidad deja más y en la dirección clínica.

**Próxima acción:**
- Decisión docente sobre la severidad de llegada propia de cada caso: si se permite, y cómo se fija sin ajustarla a la
  FC. Por ejemplo, un mapeo de la evidencia de perfusión registrada a niveles de deuda y entrega, decidido antes de ver
  la FC.
- Con autorización explícita, revisar la certificación de D y lactato con esos niveles.
- Sólo después, reevaluar la superficie primaria, con la intrínseca por caso como candidata si la docencia lo confirma.
- La intrínseca por caso no se autoriza como solución mientras la severidad siga colapsada (política docente de
  P2I-2AH).

## 8. Estado

- HR1 y HR2 sin cambios. La presión sigue DEFERRED y no se usó. La tolerancia sigue en ±5. Las ganancias siguen
  comunes.
- 150 / 175 / 200 siguen siendo techos sinusales totales: HR_RESERVE = techo − intrínseca.
- Sin cambios de código ni nuevo congelamiento. No se corrieron la certificación final ni la revisión adversarial, y no
  hay push: el bloqueo sigue abierto.
