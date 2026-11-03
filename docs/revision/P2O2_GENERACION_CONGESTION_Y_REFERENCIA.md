# P2O-2 · Generación común de congestión y semántica de referencia (auditoría)

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `524fcff` (P2O-1 aceptado y cerrado) · **Fecha:** 2026-11-03

Es una auditoría estructural de sólo lectura: ningún archivo de `clinical_core` cambia.
- Hay sondas de estado fijo y trayectorias mínimas.
- `acs_70f_left_main` sólo se usa como prueba de esfuerzo, después de las decisiones estructurales.
- k, s y r siguen en UNSET y no se elige ningún valor.
- Las afirmaciones estructurales quedan fijadas en `test_clinical_core_congestion_generation_audit.py`.
- La §18 resume la revisión adversarial; sus hallazgos se confirmaron con sondas y ya están incorporados al texto.

## Resumen

**Decisión: B, `CONGESTION_GENERATION_REMAINS_FAMILY_WRITER`.** Requisitos hidrostáticos:
`FAMILY_WRITER_PREFERRED_FOR_NOW`. Preparación: **`CONGESTION_GENERATION_STRUCTURE_READY_FOR_FACULTY_DECISION`**.

- **L es un índice de agua pulmonar relativo a la llegada** (`ARRIVAL_RELATIVE_CONGESTION_COORDINATE`). L = 0 es el
  estado pulmonar de llegada del paciente, no unos pulmones normales: el tronco ACS llega con líneas B y L = 0.
- **V no es un indicador de la presión de llenado izquierda** (`INSUFFICIENT_PROXY`).
  - Junto con P (la posición en la curva de la bomba actual), es un índice ordinal de precarga efectiva.
  - No tiene lado, no tiene distensibilidad y su ancla de llegada sale de la VCI (lado derecho).
- **El acoplamiento común de sobrecarga lee esa misma posición sin lado.**
  - Con el volumen de llegada (V = 0), ninguna P congestiona.
  - Con volumen añadido por encima de la rodilla, una P baja congestiona, aunque la reserva de llegada sea completa.
  - Así, una falla derecha (TEP, infarto de VD) más fluidos encharcaría los pulmones por ese acoplamiento.
- **Motivo principal de B: P no tiene lado** (la brecha VD / VI de TD-112 (3)). Llevar al núcleo la regla de familia
  «falla de bomba → L» haría que el TEP o el infarto de VD congestionaran el pulmón. Además, tratar la posición única
  como presión izquierda sería la equivalencia falsa, y contaría dos veces la falla de bomba con el escritor ACS.
- **La causa exacta en ACS depende de valores provisionales y de un mapeo no declarado.**
  - La llegada está a mitad de curva (0,5, valor por defecto del perfil, sin declaración del caso).
  - La rodilla de 0,85 exige +1003 mL-eq de V con P = 1 (+529 con P = 0,7).
  - El cristaloide aporta 0,125 mL-eq por mL: 4000 mL dan 386.
  - Con una fracción de llegada de 0,7, los mismos 4000 mL con P = 0,7 sí congestionan (L 0,66).

  Que sea «sobrecarga gruesa» es una propiedad de esos números, no de la estructura.
- **Por encima de la rodilla, la falla de bomba se cuenta dos veces en ACS:** en el núcleo (escala P^c y falta de
  reserva) y en el escritor de familia (1 − P). Con la llegada actual nunca ocurre.
- **Bajo la llegada: `BELOW_BASELINE_IMPROVEMENT_REQUIRED`**, antes de componer tratamientos descongestivos. La
  representación mínima es un crédito sólo en el término L → G, G_L = k·max(−L_rev, L), con L_rev ≥ 0 por caso (por
  defecto 0, lo de hoy). No pone suelo a L ni cambia el anclaje. El aclaramiento bajo la llegada queda como decisión
  docente.
- **G → SpO2 → FC: `VALID_EXISTING_REACHABILITY`.** En ACS, con la referencia sintética (k = 1, s = 5), son +1,72 lpm:
  - +1,16 del quimiorreflejo por SpO2;
  - +0,56 netos de la vía del aporte (déficit agudo y D suben; el barorreflejo resta un poco).

  Son mecanismos distintos, no un doble conteo.
- **G → SpO2 → conciencia.** Las dos escaleras ADOPTED (PAS y SpO2) son de `derive`, en sombra; P2L-2 ya las retiró de
  su candidato.
  - No se alcanzan en los cursos ACS congelados de 120 min.
  - En un curso sin tratar de 360 min con la referencia sintética, sí: SpO2 < 87 en el minuto 211 y < 80 en el 317.
  - Al integrar en tiempo de ejecución debe haber una sola fuente.
- **Una sola respuesta al O2** abarca de reactiva a refractaria según r, pero un solo r sirve a todas las familias:
  `FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT`.

## 1. L (P2O-2-1)

- **Definición:** «index deviation from arrival» (`state.CHANNEL_DEFINITIONS`). Agua pulmonar y congestión; índice
  adimensional.
- **Referencia:**
  - en la llegada L = 0 siempre, sea cual sea la congestión autorizada;
  - la congestión de llegada vive en las anclas autorizadas (SpO2, FR, gases).
- **Dominio:** [−10, 10], sólo como guarda. Su texto («only the core's congestion and clearance write L yet») está
  desactualizado desde P2N-2.
- **Escritores (§4):**
  - `derived.congestion_rate`, que el integrador escribe;
  - `derived.lung_water_clearance`;
  - el escritor de familia ACS `IschaemicCongestion`;
  - la sonda sintética `bands.Drift`.
- **Lectores en el núcleo:**
  - el propio aclaramiento (`max(0, L)`);
  - el acoplamiento L → G de P2O-1 (apagado por defecto).

  `contracts_output` exporta L como uno más de los canales escalares, sin interpretarlo, y ninguna capa de observación
  lo lee.
- **Clase: `ARRIVAL_RELATIVE_CONGESTION_COORDINATE`.** L = 0 es el estado pulmonar de llegada del paciente, nunca
  pulmones normales.

## 2. V (P2O-2-2)

- **Definición:** coordenada interna de precarga en mL equivalentes, desvío desde la llegada (κ × desvío del volumen
  circulante). No es el volumen de sangre medido.
- **Cómo actúa:**
  - posición = 1 − exp(−llenado / (escala × P^c));
  - llenado = llenado de llegada + V;
  - el llenado de llegada sale de la fracción de llegada del caso o, si no la declara, del valor por defecto 0,5. En
    ACS es el de la VCI neutral, sin declarar.
- **Indicador de la presión de llenado del VI, la AI o la PCP: `INSUFFICIENT_PROXY`.**
  - V, y la posición que forma con P, sólo ordena la precarga efectiva en una curva sin lado.
  - No hay distensibilidad ni capacitancia venosa.
  - No separa la derecha de la izquierda.
  - El ancla de llegada es derecha (VCI).
  - Es relativa a la llegada, mientras que la congestión hidrostática depende de la presión izquierda absoluta.
- **Más V no significa siempre congestión** (estado C con P = 1).

## 3. P y las cinco combinaciones (P2O-2-3)

Estados fijos sobre la llegada sintética neutral, con el perfil por defecto. V alta = +1500 mL-eq, V baja = −300 y
P baja = 0,6. Las cifras ordenan los estados; ningún umbral se elige.

| Estado | V / P | Posición (llegada 0,5) | Gasto | Congestión, reserva 1,0 | Congestión, reserva 0,5 | Lectura |
|---|---|---|---|---|---|---|
| A | normal / normal | 0,500 | 1,00 | 0 | 0 | sin congestión |
| B | normal / baja | 0,685 | 0,60 | 0 | 0 | falla de bomba sin congestión, por construcción |
| C | alta / normal | 0,917 | 1,84 | 0 | 0,011 / min | congestiona sólo si la reserva es limitada |
| D | alta / baja | 0,984 | 0,86 | 0,018 / min | 0,031 / min | sobrecarga sobre una bomba débil: congestiona incluso con reserva completa |
| E | baja / baja | 0,426 | 0,37 | 0 | 0 | infrallenado a pesar de la falla de bomba |

- **Distinción.** La arquitectura distingue los cinco estados por la posición y el gasto. E se separa de B: menos
  posición y menos gasto.
- **La caída de P con el volumen de llegada (V = 0) nunca congestiona.** El exceso se mide desde la posición del
  volumen de llegada sobre la curva actual, así que con V = 0 vale 0 para cualquier P. Está fijado en las pruebas con
  P de 1 a 0,2.
  - El revisor lo comprobó en 280 combinaciones.
  - Hay una excepción: un `ZeroDivisionError` si la posición de llegada sobre la curva actual redondea a 1 (por
    ejemplo, fracción 0,99 con P = 0,1). Es deuda del núcleo y no se alcanza en ningún caso congelado.
- **Con volumen añadido por encima de la rodilla, una P baja sí congestiona**, aunque la reserva sea 1,0 (C → D:
  0 → 0,018/min). La falta de reserva 1 − reserva·P sólo es nula mientras reserva·P ≥ 1.
- **P actúa por tres vías en la congestión de ACS por encima de la rodilla:**
  1. en la escala de la curva (P^c, que acerca la rodilla: 1003 → 529 mL-eq);
  2. en la falta de reserva;
  3. en el escritor de familia (1 − P).

  Con V = +1500 y P = 0,7, el núcleo pasa de 0,011 a 0,026/min y el escritor añade 0,015/min por la misma falla. Es un
  doble conteo latente, que no ocurre con la llegada ACS actual porque nunca llega a la rodilla.

## 4. Escritores de L y la limitación en ACS (P2O-2-4)

| Escritor | Clase |
|---|---|
| `derived.congestion_rate` (precarga añadida sobre la rodilla × falta de reserva) | COMMON_PHYSIOLOGY (KD-S4, provisional): sobrecarga de volumen sin lado |
| `derived.lung_water_clearance` (primer orden, τ 240 min, sólo por encima de la llegada) | COMMON_PHYSIOLOGY (P2D-6, provisional) |
| `modules/acs_ischaemia.IschaemicCongestion` (L ∝ 1 − P) | FAMILY_WRITER (P2N-2) |
| `bands.Drift` sobre L | SYNTHETIC_ONLY |
| el «lung» del motor heredado y su regla de sobrecarga por transfusión | LEGACY_ARTIFACT (fuera del núcleo; no se usa) |

**Limitación causal exacta en `acs_70f_left_main`:**
1. La fracción de llegada no está declarada: el núcleo usa el 0,5 por defecto. La VCI neutral no informa la presión
   izquierda, y las líneas B quedan en la SpO2.
2. Con la rodilla de 0,85 y la escala de 833 mL, alcanzarla exige +1003 mL-eq de V con P = 1 (+529 con P = 0,7).
3. El cristaloide aporta 0,125 mL-eq por mL con una parte transitoria: 1000 mL dan 97 mL-eq y 4000 mL, 386.
4. Con 4000 mL, la posición máxima (alcanzada hacia el minuto 30) es 0,686 con P = 1 y 0,808 con P = 0,7. Las dos
   quedan bajo la rodilla y L queda en 0. El 0,77 de P2N-2 es la posición del mismo escenario leída en el minuto 60.
5. **Sensibilidad a la fracción de llegada** (4000 mL):
   - con P = 0,7, L máximo es 0 con 0,5; 0,014 con 0,6; 0,66 con 0,7;
   - con P = 1 hace falta una fracción de al menos ~0,78.

   Un mapeo tomado de las líneas B encendería una congestión fuerte por volumen, y con ella el doble conteo de §3.

Así, que el acoplamiento sea «sobrecarga gruesa» describe los números provisionales (fracción 0,5, rodilla 0,85,
escala 833), no la estructura. También deja fuera un requisito transversal: la sobrecarga circulatoria por
transfusión. La regla heredada, de la pregunta docente del 2026-09-20, dice que en un paciente sin anemia las unidades
añaden volumen que va al pulmón. El acoplamiento común no la produce con volúmenes plausibles (dos unidades,
~600 mL-eq, frente a 1003 con P = 1). Queda como requisito, no como objetivo de calibración.

## 5. Fisiología hidrostática mínima (P2O-2-5)

Un generador común hidrostático verdadero necesitaría:
1. Un índice de presión de llenado **izquierda** que suba con el volumen y con la falla izquierda con el mismo retorno.
   La falla derecha (TEP, infarto de VD) no debe encharcar el pulmón.
2. Una relación volumen → presión (distensibilidad).
3. Un ancla de llegada para esa presión, porque ACS llega ya congestionado.
4. Una capacidad de aclaramiento; ya existe como τ provisional.
5. Persistencia; ya existe, porque L integra.

Con los canales actuales:
- (1) y (3) exigen tratar como presión izquierda una posición sin lado, anclada en la VCI;
- P no tiene lado;
- (2) no existe.

**Resultado: `FAMILY_WRITER_PREFERRED_FOR_NOW`.** Un generador común cardiogénico exigiría un estado común nuevo de
presión de llenado izquierda, o un P con lado (la condición C). Hoy no hace falta, así que no se propone.

## 6. Alternativa: escritor de familia (P2O-2-6)

- **Cómo queda la división:**
  - mecanismo de enfermedad: la familia (isquemia → falla izquierda → L);
  - fisiología aguas abajo: común (L → G → SpO2 → aporte → D / lactato / FC / conciencia / colapso).
- **La división es limpia:**
  - la familia escribe sólo P y L;
  - el núcleo no nombra la familia.

  La familia sabe que su falla es izquierda; el núcleo no puede saberlo.
- **Es suficiente para la generalización actual.** P2O-1 mostró en ACS un deterioro coherente y una respuesta al O2.
- **No hay duplicación bajo la rodilla.** Por encima, el escritor y el acoplamiento común cuentan los dos la falla de
  bomba (§3). Hoy es inalcanzable con la llegada ACS, pero lo sería con otro mapeo de la fracción de llegada.
- **Regla de frontera.** Si algún día se añade un generador común, el escritor de familia debe retirarse.

## 7. Bajo la llegada (P2O-2-7, P2O-2-8)

- **Hoy:**
  - G = k·max(0, L) y la SpO2 sólo baja por max(0, G);
  - L y G negativas no cambian nada (fijado con una deriva que lleva L bajo la llegada);
  - el aclaramiento sólo actúa por encima de la llegada.
- **¿Qué es coherente con el significado de L y G?**
  - Son desvíos desde la llegada, y su dominio admite negativos.
  - Si la llegada incluye congestión reversible (las líneas B del tronco), descongestionar por debajo de ella debe
    mejorar el intercambio respecto de la llegada.
  - Lo que falta es la cota: cuánto de la alteración de llegada es reversible.
- **Resultado: `BELOW_BASELINE_IMPROVEMENT_REQUIRED`**, antes de componer tratamientos descongestivos. Hasta entonces,
  la ausencia de crédito es una cota conservadora coherente y aislada.
- **Prueba en el caso.** Con reperfusión en el minuto 60 y la recuperación declarada parcial, P se estabiliza en 0,95.
  El escritor de familia mantiene una fuente de congestión, L sigue subiendo hasta 0,48 a los 360 min, y la SpO2 nunca
  pasa de 94. Esa persistencia es semántica de la familia.
- **Representación compatible más pequeña (sin implementar; decisión docente):**
  - una cota por caso en la capa de llegada, L_rev ≥ 0 (el agua pulmonar reversible de la llegada), que sale de la
    evidencia autorizada (CASE_MAPPING); por defecto 0, que es exactamente lo de hoy (GI 0);
  - el crédito va sólo en el término L → G: G_L = k·max(−L_rev, L). L no tiene suelo, porque un suelo sería un clamp de
    la guarda;
  - la SpO2 acredita G hasta −k·L_rev. Con una sola G el crédito se aplica a la G total, así que una familia que
    escribiera G por debajo de la llegada podría consumir ese margen. La regla debe ser que los escritores directos de
    G no escriben por debajo de la llegada, o que decida la docencia;
  - qué baja L por debajo de la llegada: sólo escritores descongestivos futuros. El aclaramiento sigue actuando sólo
    por encima de la llegada, así que L no vuelve sola hacia 0. Hacer que el aclaramiento tienda a −L_rev rompería el
    punto fijo de llegada; es decisión docente;
  - L = 0, G = 0 y la SpO2 autorizada siguen exactas en la llegada: no se reescribe el anclaje.

## 8. G → SpO2 → FC (P2O-2-9)

- **Ecuación** (`derived.sympathetic_target`, común desde KD-S2):

  impulso = ganancia aguda × déficit efectivo / demanda + ganancia de deuda × D + 0,02 × hipoxemia + barorreflejo,

  con hipoxemia = max(0, 94 − SpO2) − max(0, 94 − SpO2 de llegada).
- **Estado de los valores.** La ganancia de hipoxemia (0,02) y el umbral (94) son PROVISIONAL. Ya era fisiología
  común; ahora G la alcanza.
- **Descomposición en ACS a los 120 min, con la referencia sintética (k = 1, s = 5):**
  - FC 106,50 → 108,22 (+1,72);
  - sin el término de hipoxemia, 107,06;
  - el quimiorreflejo aporta +1,16;
  - la vía del aporte aporta +0,56 netos: impulso por déficit agudo +0,020 y por D +0,009; el barorreflejo resta
    −0,004, porque el tono y la PAM suben un poco.
- **No hay doble conteo:**
  - la vía del aporte sólo actúa cuando el déficit supera la reserva de extracción (ACS ya llega crítico);
  - el quimiorreflejo actúa sobre la SpO2 aunque el aporte esté compensado.

  La magnitud depende de los valores sintéticos k·s y de ganancias provisionales; no avala ningún valor.
- **Clase: `VALID_EXISTING_REACHABILITY`.** La ganancia y el umbral quedan para revisión futura de valores.

## 9. G → SpO2 → conciencia (P2O-2-10)

- **La escalera.** `derive` calcula `consciousness_level = max(nivel autorizado, escalera de PAS, escalera de SpO2)`.
  Las dos escaleras son ADOPTED del legado, absolutas (SpO2 87 → 1, 80 → 2).
- **Dónde actúa.** Sólo en la `derive` del núcleo en sombra, que no está en tiempo de ejecución.
- **El candidato de P2L-2.** No lee ninguna de las dos escaleras: P2L-2 las retiró de su candidato (§52,
  `encephalopathy_architecture.FORBIDDEN_READS`). Lee la SpO2 como señal propia de hipoxemia, que por defecto está
  UNMAPPED.
- **¿Se alcanza?**
  - No, en los cursos ACS congelados de 120 min (SpO2 mínima 88,9; nivel 0).
  - En el curso ACS sin tratar de 360 min con la referencia sintética, sí: SpO2 < 87 en el minuto 211 y < 80 en el 317.
    La escalera de PAS ya llega al nivel 1 hacia el minuto 175–184, sin G.
- **¿Doble conteo?** La agregación por máximo no suma: si escalera y candidato convivieran, habría dos fuentes con
  umbrales distintos para la misma hipoxemia, no una suma.
- **Requisito de integración en tiempo de ejecución** (`CONSCIOUSNESS_SINGLE_SOURCE_GUARD`). Al integrar P2L-2, retirar
  de la conciencia las dos escaleras de `derive` (PAS y SpO2), como ya dispuso P2L-2.

## 10. Una sola respuesta al O2 (P2O-2-11)

Con la misma alteración al aire ambiente (G = 1,2, SpO2 97 → 91):

| r | FiO2 0,4 | FiO2 1,0 |
|---|---|---|
| 0 (reactiva, tipo V/Q) | 96,7 | 100 |
| 0,5 | 94,6 | 100 |
| 2 (refractaria, tipo shunt) | 92,7 | 98,0 |

- **Estructura.** Una sola función cubre las tres formas por familia (edema, neumonía, TEP).
- **Límite.** Con un r común, todas responden igual por unidad de G.
- **Clase: `FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT`.** No es un fallo del núcleo, y no se añade ningún parámetro.

## 11. Prueba de esfuerzo ACS (P2O-2-12)

- **Basta con lo que mostró P2O-1, reutilizado sin reajustar:** el L escrito por la familia más L → G → SpO2 común
  producen un deterioro coherente:
  - SpO2 94 → 91,5 a los 120 min;
  - aporte −3 %, con D y lactato nunca bajo el control;
  - con O2 0,4 la SpO2 sube a 96–97,5.
- **El legado** es sólo referencia.
- **Nuevo en P2O-2:**
  - la reperfusión con recuperación parcial no descongestiona por debajo de la llegada (§7);
  - en cursos sin tratar más largos se alcanzan las escaleras de conciencia (§9).

## 12. GI (P2O-2-13)

- **El acoplamiento común es inerte en GI.** Las dos llegadas GI tienen reserva 1,0 y ningún escritor de P, así que P
  queda en 1 y la falta de reserva vale 0.
- **Lo que fija la prueba.** Los cursos GI (sin tratar y con 1000 mL) no escriben ninguna congestión. GI no tiene
  escritor de L. P2O-1 mostró GI idéntico en 16 de 16 cursos.
- **Para cualquier generador futuro.** Debe dejar GI exacto con P ≈ 1, L en la llegada y sin escritor. Ojo: el
  acoplamiento actual no es inerte en GI si una P baja coincidiera con volumen sobre la rodilla.

## 13. Taxonomía de familias (P2O-2-14)

Es una clasificación estructural; no migra ninguna familia.

| Familia (banco) | Escribe | Por qué |
|---|---|---|
| edema pulmonar cardiogénico (`pulmonary_edema`, y el SCA con falla izquierda) | L (escritor de familia) | agua pulmonar hidrostática izquierda; el núcleo no tiene lado |
| sobrecarga de volumen o renal | L, por V a través del acoplamiento común | no está en el banco (`renal_colic` no lo es); la sobrecarga por transfusión es un requisito (§4) |
| neumonía (`pneumonia`) | G directamente | consolidación, shunt |
| TEP (`pulmonary_embolism`) | G directamente (más W por espacio muerto, y P del VD) | V/Q, sin L. La P del VD más fluidos congestionaría por el acoplamiento sin lado: es un artefacto a vigilar |
| asma (`asthma`) / EPOC (no está en el banco) | ninguno como primario (W, mecánica); G secundaria | la mecánica domina; la W dinámica está diferida |
| anafilaxia (`anaphylaxis`) | G (más W, T y V por fuga) | L sólo si la familia declara edema por permeabilidad |
| hipoventilación por opioide (`opioid`) | ninguno (W) | sin agua pulmonar ni alteración del intercambio |
| trauma (`trauma`) | G (contusión, hemotórax); V por sangrado y transfusión | la sobrecarga por transfusión masiva sería L por V (§4) |

No hace falta ninguna ecuación de enfermedad en el núcleo.

## 14. Frontera común / familia (P2O-2-15)

**Decisión: B, `CONGESTION_GENERATION_REMAINS_FAMILY_WRITER`.**
- La generación cardiogénica de L se queda en el escritor de familia.
- El acoplamiento común se queda como mecanismo de sobrecarga sin lado, con sus limitaciones declaradas.
- L → G → SpO2 → aporte es común.

**Motivo exacto.** P no tiene lado. Una regla común «falla de bomba → L» congestionaría el pulmón en el TEP y en el
infarto de VD. La alternativa de leer la posición única de precarga como presión izquierda sería una equivalencia
falsa, anclada en la VCI. Además, contaría dos veces la falla de bomba con el escritor ACS, y necesitaría un ancla de
presión de llegada que no existe. La familia sabe qué lado falla; el núcleo no.

La condición para un generador común (C) es un estado común de presión de llenado izquierda, o un P con lado. No se
propone ni se inventa.

## 15. Preparación y recomendación (P2O-2-16)

**`CONGESTION_GENERATION_STRUCTURE_READY_FOR_FACULTY_DECISION`.**
- La semántica de L es explícita (§1).
- Los papeles de V y P son explícitos (§2, §3).
- La frontera común / familia es explícita (§14).
- La semántica bajo la llegada está resuelta y aislada (§7).
- Se entiende la nueva alcanzabilidad de la FC y de la conciencia (§8, §9).
- No se eligió ningún valor de P2O-1.
- GI no se tocó.

**Recomendación.** Seguir con escritores de familia y la fisiología aguas abajo común. El paquete siguiente sería la
migración en sombra de `pulmonary_edema` con su propio escritor de L, empezando por la decisión sobre L_rev (§7),
porque el valor docente del edema es la descongestión. No se inicia.

## 16. Decisiones pedidas a la docencia

1. Aceptar B: la generación cardiogénica de L queda como escritor de familia.
2. Si se quiere un generador común en el futuro, aprobar antes un estado de presión de llenado izquierda o un P con
   lado (la condición C).
3. **El acoplamiento común de sobrecarga:**
   - mantener o no los dos papeles de P (escala P^c y falta de reserva);
   - cómo se compone con el escritor de familia por encima de la rodilla (doble conteo latente);
   - la vigilancia del artefacto de lado (VD más fluidos).
4. **La fracción de precarga de llegada en ACS** (hoy 0,5 por defecto, sin declarar): ¿VCI o líneas B? Decide si el
   volumen congestiona (§4).
5. **La cota L_rev:**
   - el concepto, el crédito sólo en L → G y la regla de mapeo desde la evidencia autorizada;
   - si los escritores directos de G pueden bajar de la llegada;
   - cómo se comporta el aclaramiento bajo la llegada.
6. Confirmar la dirección de P2L-2: al integrar, retirar de la conciencia las escaleras de PAS y SpO2 de `derive`.
7. Si la neumonía y el TEP necesitan respuestas al O2 distintas (`FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT`).
8. La ganancia y el umbral del quimiorreflejo de la FC (0,02 por punto, 94), estructuralmente válidos y con valores
   provisionales.
9. Con recuperación parcial, el escritor ACS mantiene una fuente de congestión: confirmar esa semántica de familia.
10. La sobrecarga circulatoria por transfusión como requisito común (§4): con qué mecanismo se representaría.

k, s y r siguen siendo `STRUCTURALLY_DEFINED` y `CLINICALLY_UNIDENTIFIED`. No se infiere ni k ni s a partir de su
producto.

## 17. Limitaciones

- **Alcance.** Es una auditoría: no cambió el núcleo, no hubo congelamiento y no se corrió la suite completa.
- **Magnitudes.** Las de las sondas dependen de valores provisionales (escala, rodilla, c, ganancia, τ) y de la
  fracción de llegada no declarada.
- **Sin modelar.** No hay presión hidrostática, oncótica, distensibilidad ni linfa explícitas.
- **Taxonomía.** Es estructural: ninguna familia se migró.
- **Deuda del núcleo detectada.** El `ZeroDivisionError` de `congestion_rate` en el borde (§3) y el texto desactualizado
  de la guarda de L (§1). Ninguno se corrige aquí.

## 18. Revisión adversarial

Hubo una sola revisión, independiente y de sólo lectura: 6 hallazgos medios, 8 bajos y ninguno alto. Todos los números
del informe se reprodujeron. Los hallazgos se confirmaron con sondas y se incorporaron arriba.

- **Corregido en el texto:**
  - el acoplamiento sin lado congestiona con reserva completa cuando P < 1 y hay volumen sobre la rodilla, y el TEP o
    el VD más fluidos también lo harían. Por eso el motivo principal de B es que P no tiene lado;
  - el doble conteo latente de la falla de bomba por encima de la rodilla;
  - la dependencia de la fracción de llegada no declarada;
  - la representación L_rev refinada (crédito sólo en L → G, sin suelo en L, aclaramiento como decisión);
  - el alcance de la escalera de conciencia (minutos 211 / 317 y PAS) y la guarda para las dos escaleras;
  - el término opuesto del barorreflejo en la FC;
  - V como `INSUFFICIENT_PROXY`;
  - los contratos exportan L;
  - la taxonomía completada (opioide, trauma) y el requisito de sobrecarga por transfusión.
- **Pruebas reforzadas:**
  - GI ejecuta sus cursos y no escribe congestión;
  - una deriva lleva L bajo la llegada sin cambiar G ni la SpO2;
  - el escáner de escritores de L es por AST;
  - quedan fijados la congestión con reserva completa y P baja, el doble conteo, la sensibilidad a la fracción, el
    alcance de la escalera y el borde del `ZeroDivisionError`.
- **Sin defecto:**
  - V = 0 no congestiona con ninguna P (280 combinaciones);
  - no hay nombres de familia en el núcleo;
  - el legado no es objetivo;
  - k, s y r siguen en `None`;
  - VALID_EXISTING_REACHABILITY es defendible.
