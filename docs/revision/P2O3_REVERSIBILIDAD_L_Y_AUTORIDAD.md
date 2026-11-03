# P2O-3 · Reversibilidad de L (L_rev) y autoridad del escritor de congestión

Rama `phase-2-clinical-core-shadow`. Todo es sombra: nada llega al tiempo de ejecución ni cambia lo que ve el
residente. Los valores de las sondas son SYNTHETIC_ONLY y ninguno queda aprobado. Los bloques entre marcadores
`generado` salen del registro congelado `docs/revision/P2O3_lung_water_reference.json` con
`python -m clinical_core.lung_water_reference_report`. El módulo es `clinical_core/lung_water_reference.py`; su
congelamiento (`7135e08`) precede a la única evaluación.

## 1. Encargo y alcance

Es un paquete estructural pequeño sobre la decisión B aceptada (la generación de congestión sigue siendo un escritor
de familia):

- **autoridad:** un escritor de L de familia puede declararse dueño de L. Mientras esté presente, el acoplamiento
  común de sobrecarga no añade nada;
- **L_rev:** cota inferior reversible de L por caso o familia (≤ 0, por defecto 0). El lector L → G usa
  max(L_rev, L) en lugar de max(0, L);
- **G negativa:** la SpO2 acredita una G bajo la llegada sólo hasta la parte que explica el agua pulmonar.

No se implementa una generación hidrostática común, no se migra `pulmonary_edema` y no se calibra nada.

## 2. Decisiones fijas de la docencia

- **B** (P2O-2, aceptada): no hay regla universal «P baja → L sube», porque P no tiene lado.
- **NEW_COMMON_FILLING_PRESSURE_STATE_DEFERRED:** no se añade presión de AI, PCP, PTDVI, venosa ni hidrostática.
- **V** es volumen circulante efectivo (coordenada de precarga), nunca presión de llenado izquierda. En ACS, la VCI
  informa V; las líneas B nunca (informan L).
- **FAMILY_CONGESTION_WRITER_OVERRIDES_COMMON_OVERLOAD_WRITER:** con un escritor de L de familia dueño, el
  acoplamiento común no añade una segunda contribución. El mecanismo común no se borra.
- **L** sigue relativa a la llegada: L = 0 es la congestión de llegada, no un pulmón seco normal.
- **L_rev:** CASE/FAMILY REFERENCE PARAMETER, ≤ 0, por defecto 0, sin valor aprobado. Con el valor por defecto
  reproduce P2O-1 exactamente.

## 3. Composición de L antes de P2O-3 (P2O-3-1)

`integration.step` junta en una lista todos los deltas del minuto: primero los del núcleo (congestión de precarga y
aclaramiento), después los de cada contribuyente. El cambio de un canal es la suma (`math.fsum`) de sus deltas, y
luego la guarda lo acota (un CLAMP registrado). Ningún escritor sobrescribe, toma el máximo ni secuencia a otro: el
orden cambia el registro, nunca la suma. Antes de P2O-3, el escritor ACS y el acoplamiento común se sumaban en el
mismo minuto (el doble conteo latente de P2O-2).

<!-- generado:composicion -->
Regla: **ADDS** (los deltas de L se suman con `fsum` y luego se acotan). En el escenario de sobrecarga de ACS, el clon sin autoridad escribe a la vez que el acoplamiento común en 113 minutos: L final 2,080, frente a 1,419 con la autoridad y 0,661 con el acoplamiento común solo.
<!-- /generado:composicion -->

## 4. Autoridad (P2O-3-2)

- **Declaración:** `Contributor.lung_water_authority`, un atributo de clase falso por defecto. Sólo un módulo de
  enfermedad puede declararlo. `_ordered` rechaza:
  - cualquier otro tipo;
  - un valor que no sea `True` o `False`;
  - un valor distinto del de su tipo registrado;
  - un segundo dueño en la misma corrida (un solo generador de L).
- **Efecto:** con un dueño presente, `step` no añade ningún delta de congestión de precarga (`congestion = 0.0`).
- **Alcance:** la corrida, por presencia, no el minuto. Un escritor de familia que no escribe en un minuto (P vuelve
  a 1) sigue siendo dueño de L: la sobrecarga común no vuelve a mitad del curso.
- **Sin cambio:** el aclaramiento, todos los lectores de L (aclaramiento, L → G, exportación de contratos), L → G y
  G → SpO2. Cualquier otro escritor de L (una sonda guionizada) sigue sumando.
- **Trazabilidad:** no hay campo nuevo en el registro del minuto. La autoridad es un atributo de clase del tipo
  registrado del contribuyente, así que una reproducción desde la especificación la recupera. Un minuto con dueño no
  lleva delta de congestión común.
- **Volumen:** bajo la autoridad, la L de la familia ya no responde al volumen a través del núcleo (el escritor ACS
  no tiene término de V). Un dueño con ganancia 0 suprime toda generación de L. Es una decisión docente, no un defecto.

<!-- generado:autoridad -->
- Declaran la autoridad: `acs_ischaemic_congestion` (tipo disease_module).
- Un evento guionizado que la declara se rechaza: sí.
- Un segundo dueño en la misma corrida se rechaza: sí.
- Una autoridad distinta de la del tipo registrado se rechaza: sí; una copia sintética con tipo propio, no registrado, se acepta: sí.
<!-- /generado:autoridad -->

## 5. L_rev y el lector L → G (P2O-3-3)

- `Anchors.reversible_lung_water` (L_rev) es un insumo candidato de la capa de referencia fisiológica. Sigue el
  precedente de P2K-2 y queda fuera del registro de parámetros de caso y de migración hasta que la docencia adopte
  L → G.
- Dominio: finito y ≤ 0; las anclas rechazan un valor positivo. Por defecto 0.
- **Ecuación:** dG = k × (max(L_rev, L después) − max(L_rev, L antes)). Sumada desde la llegada, la G que viene de L
  es k × max(L_rev, L): continua, nunca decreciente en L, 0 en la llegada y como mínimo k × L_rev bajo ella.
- L no tiene suelo en L_rev: sus escritores y su guarda [−10, 10] actúan como antes.
- Lectores de L_rev: sólo el acoplamiento L → G y la cota de crédito `lung_water_gas_credit`. Ningún otro
  consumidor de L cambia.

## 6. Signo de G (auditoría)

P2O-1 leía max(0, G): una G bajo la llegada contaba como la llegada, la escribiera quien la escribiera. P2O-3 cambia
el término de G:

SpO2 = min(100, max(0, A − s × max(c, G) + 30 × (beneficio(F) × retenido(G) − beneficio(F_a))))

con c = `lung_water_gas_credit` = k × min(0, max(L_rev, L)) ≤ 0 y retenido(G) = 1 / (1 + r × max(0, G)).

- **G = 0:** max(c, 0) = 0 para todo c ≤ 0 y retenido(0) = 1. La SpO2 es la de llegada exacta, sea cual sea L_rev.
- **Monotonía en G:** max(c, G) nunca baja al subir G, y retenido nunca sube. Bajar G bajo 0 nunca empeora la SpO2.
- **Acotada:** la ganancia sobre G = 0 es como mucho s × |c| ≤ s × k × |L_rev|, con el tope de 100. Con L_rev = 0 no
  hay ganancia.
- **FiO2:** beneficio(F) × retenido(G) nunca baja al subir F. Retenido lee max(0, G), así que la respuesta al O2
  nunca es mejor que en la llegada.
- **G directa:** c es la parte del agua pulmonar bajo la llegada. Una G por debajo de c no recibe más crédito, y con
  L ≥ 0 o L_rev = 0, c = 0 (el max(0, G) de P2O-1).
- **Lectura de L:** la cota c lee L a través de `_perfusion`. Con G fija, L mueve la SpO2 sólo donde G < c ≤ 0, es
  decir, sólo para negar un crédito que el agua pulmonar no explica. En la llegada o por encima, c = 0.
- **Condición:** lo anterior vale en una corrida desde la llegada (la parte pulmonar de G es k × max(L_rev, L)) con
  G dentro de su guarda.
  - Con L_rev < 0, el núcleo detiene la corrida si la guarda de G actúa (`UnresolvedBoundary`, como V y Hb; TD-113
    (10)).
  - Una corrida que empieza fuera de la llegada (L ≠ 0 con G = 0) puede acreditar la G de un escritor directo, hasta
    k × L_rev. Es un límite conocido (NON_ARRIVAL_START_CREDIT).

<!-- generado:signo_g -->
| Propiedad | Cumple |
|---|---|
| G = 0 reproduce la llegada exactamente | sí |
| la SpO2 nunca sube con G (bajar G bajo 0 nunca empeora) | sí |
| la SpO2 nunca baja con la FiO2 | sí |
| la mejora es a lo sumo s × |c| y queda en [0, 100] | sí |
| una G por debajo de c no recibe más crédito | sí |
| un crédito positivo se rechaza | sí |

Escritor directo de G con L = 0 y L_rev = −1: G −1,00, SpO2 97,0 (sin crédito: sí).

**Resultado:** `NEGATIVE_G_SUPPORTED_BOUNDED`.
<!-- /generado:signo_g -->

## 7. Escritores directos de G (P2O-3-4)

**DIRECT_G_REVERSIBILITY_DEFERRED.** Neumonía, TEP y anafilaxia no tienen cota reversible propia. Su G bajo la
llegada no se acredita porque c sólo cuenta agua pulmonar.

## 8. Sondas R1–R8 (P2O-3-5)

<!-- generado:sondas -->
| Sonda | Qué prueba | Cumple |
|---|---|---|
| R1 | L = 0 y L_rev = 0: P2O-1 idéntico | sí |
| R2 | L > 0: G y SpO2 empeoran | sí |
| R3 | L < 0 con L_rev = 0: sin crédito | sí |
| R4 | L < 0 con L_rev < 0: mejora | sí |
| R5 | L < L_rev: el crédito se detiene en L_rev | sí |
| R6 | subir la FiO2 nunca empeora la SpO2 | sí |
| R7 | escritor de familia y sobrecarga: sólo la familia cambia L | sí |
| R8 | sin escritor de familia: la sobrecarga común sigue disponible | sí |

- **R1:** acoplamiento y oxigenación iguales a P2O-1 en las rejillas; secciones congeladas de P2O-1 reproducidas: acs sí, cross_family sí, layers sí, probes sí.
- **R2:** L 1,639, G 1,639, SpO2 88,80; igual con todo L_rev: sí.
- **R3:** L −2,00, G 0,00, SpO2 97,0.
- **R4:** L_rev −1,0: L −0,500, G −0,500, SpO2 99,50.
- **R5:** L_rev −0,5: L −2,00, G −0,50, SpO2 99,50 (tope 99,50).
- **R7:** escrituras comunes 0; L igual al de la familia sola: sí; L final 1,419.
- **R8:** escrituras comunes 113; L final 0,661, G 0,661.
<!-- /generado:sondas -->

## 9. ACS: mapeo de llegada y descongestión (P2O-3-6, P2O-3-7)

- **V** viene de la VCI: `preload_fraction` sigue sin declarar (posición provisional del perfil); su clasificación
  cita la VCI de 1,9 cm con colapso de ~50 %. No se elige un valor final.
- **L** viene de la congestión: las líneas B bibasales y la congestión leve son la lectura de llegada (L = 0). Las
  líneas B no llegan a `preload_fraction`.
- **Hallazgo:** la banda de `pump_reserve` de ACS cita las líneas B como evidencia de reserva reducida. Es una
  referencia de P, no de V. `pump_reserve` sólo lo lee el acoplamiento común de sobrecarga (y el informe de capas),
  así que, con la autoridad del escritor ACS, ya no actúa en ACS.
- La descongestión se muestra con una sonda guionizada, no con un diurético; no hacen falta cinéticas.

<!-- generado:acs -->
- `preload_fraction`: sin declarar (declarada: no); la VCI informa V: sí; las líneas B no llegan a V: sí; las líneas B informan L: sí; L_rev en ACS: 0,0.
- `pump_reserve` lo leen sólo `arrival_layers`, `congestion_rate`; su banda cita las líneas B: sí; inerte en ACS bajo la autoridad: sí.
- Llegada: L 0,0, G 0,0, SpO2 94,0.
- Congestión (sin tratar, 120 min): L 0,508, G 0,508, SpO2 91,46.
- Descongestión (sonda guionizada, L_rev −0,5): L −1,20, G −0,50, SpO2 96,50 (tope 96,50); V sin cambio: sí; P sin cambio: sí.
<!-- /generado:acs -->

## 10. Recuperación parcial de P (P2O-3-8)

La recuperación de P nunca limpia L de golpe. Tras la reperfusión, la caída de L por minuto es como mucho la
fracción de primer orden del aclaramiento (τ 240 min), porque el escritor de familia sólo suma. La congestión
persiste (**CONGESTION_CLEARANCE_KINETICS_UNSET**).

<!-- generado:recuperacion -->
| Recuperación | P al reperfundir | P final | L al reperfundir | L máximo | L final | Caída máx./min | Acotada por el aclaramiento |
|---|---|---|---|---|---|---|---|
| 0.5 | 0,903 | 0,951 | 0,136 | 0,485 | 0,485 | −0,00044 | sí |
| 1.0 | 0,905 | 1,000 | 0,136 | 0,214 | 0,087 | 0,00066 | sí |
<!-- /generado:recuperacion -->

## 11. Deudas registradas (P2O-3-9)

- **TRANSFUSION_OR_VOLUME_OVERLOAD_CONGESTION:** TACO, sobrecarga de volumen y congestión renal. El acoplamiento
  común queda disponible para una familia futura (R8). Sin familia y sin calibración; rodilla, ganancia y
  `pump_reserve` siguen provisionales, y la división por cero en el borde de la curva (P2O-2) sigue como deuda
  conocida.
- **CONGESTION_CLEARANCE_KINETICS_UNSET:** el τ de 240 min es provisional. Nada lleva una L bajo la llegada de vuelta
  hacia ella. No se modelan diuréticos ni VNI.
- **DIRECT_G_REVERSIBILITY_DEFERRED** (§7).
- **L_REV_REGISTRY_ENTRY_DEFERRED:** L_rev queda fuera de `CASE_PARAMETERS`, sin fuente `declared` exigida, hasta que
  se adopte L → G.
- **PUMP_RESERVE_INERT_UNDER_AUTHORITY** (§9).
- **L_GUARD_REASON_TEXT_OUTDATED:** los textos de las guardas siguen desactualizados: el de L dice que sólo el
  núcleo escribe L, y el de G que ningún módulo escribe G (TD-113 (11)). Son sólo texto y no se tocan.
- **G_GUARD_WITH_L_TO_G** (TD-113 (10), redeclarada):
  - con L_rev < 0, la corrida se detiene en la guarda de G;
  - con L_rev = 0, la guarda sostiene G como en P2O-1 y puede separarla del agua pulmonar, sin crédito posible.
- **NON_ARRIVAL_START_CREDIT** (§6).
- **OWNER_SUPPRESSES_VOLUME_RESPONSE** y **SINGLE_OWNER** (§4).

## 12. FC (P2O-3-10)

G → SpO2 → FC sigue siendo válido y no se tocan ganancias. La sonda lee el signo en un estado con impulso positivo
(P = 0,7), porque el impulso nunca baja de 0 (P2D-3). Una G acreditada bajo la llegada nunca sube el objetivo, y el
término de hipoxemia nunca es positivo. No hace falta otra guarda.

<!-- generado:fc -->
| Llegada | Objetivo con pulmón de llegada | Objetivo mejorado | SpO2 mejorada | Término de hipoxemia |
|---|---|---|---|---|
| hypoxaemic_90 | 0,300 | 0,250 | 92,5 | −2,5 |
| neutral_97 | 0,300 | 0,300 | 99,5 | 0,0 |

P de la sonda 0,7; umbral 94.
<!-- /generado:fc -->

## 13. Conciencia y subtipos de G (P2O-3-11, P2O-3-12)

- **LEGACY_SPO2_CONSCIOUSNESS_LADDER_MUST_BE_DISABLED_ON_P2L2_INTEGRATION:** `derive` conserva la escalera ADOPTED de
  SpO2 (87 / 80), que el candidato de P2L-2 no lee. Al integrar P2L-2 debe retirarse junto con la de PAS. No se toca
  la conciencia en tiempo de ejecución; una SpO2 sobre la llegada sólo puede mantener o bajar el nivel de la
  escalera.
- **FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT:** una sola respuesta de G (s, r) sirve a todas las familias. La división
  en subtipos queda diferida.

## 14. Estado de los parámetros (P2O-3-13)

<!-- generado:parametros -->
- **family_writer_rates**: IschaemicCongestion's gain (share 0.5 / 1 / 2 x congestion_per_excess_preload): FAMILY_CANDIDATE, UNSET
- **lung_water_clearance_tau_min**: CONGESTION_CLEARANCE_KINETICS_UNSET (240 min, provisional, P2D-6)
- **lung_water_to_gas_exchange_gain**: k: UNSET (None by default); STRUCTURALLY_DEFINED / CLINICALLY_UNIDENTIFIED
- **oxygen_response_loss_per_gas_exchange_unit**: r: UNSET (None by default); STRUCTURALLY_DEFINED / CLINICALLY_UNIDENTIFIED
- **reversible_lung_water**: L_rev: semantics approved (P2O-3); default 0; every other value UNSET
- **spo2_per_gas_exchange_unit**: s: UNSET (None by default); STRUCTURALLY_DEFINED / CLINICALLY_UNIDENTIFIED

k, s y r en `None` por defecto: sí; L_rev por defecto 0,0 y en ACS 0,0.
<!-- /generado:parametros -->

## 15. GI y demostración (P2O-3-14)

Los seis archivos que P2O-3 cambió son los de P2O-1 más exactamente los reemplazos declarados (`REVERSAL`), byte a
byte. El digest congelado de P2O-1 se reproduce a través de esa vista. El golden directo de GI queda idéntico byte a
byte.

<!-- generado:prueba -->
- Archivos P2O-1 reconstruidos byte a byte: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/modules/acs_ischaemia.py` sí, `clinical_core/state.py` sí.
- Digest congelado de P2O-1 reproducido por la vista: sí.
- Registro de P2O-1 intacto: sí.
- GI: O12 de P2O-1 reproducido sí; otros dueños de L: 0.
<!-- /generado:prueba -->

## 16. Veredicto (P2O-3-15)

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| ACS V and L stay separate | sí |
| GI unchanged | sí |
| L stays arrival-relative | sí |
| L_rev = 0 preserves P2O-1 (R1) | sí |
| authority prevents double writing (R7, one owner) | sí |
| below-arrival improvement representable (R4, R5) | sí |
| common overload available without authority (R8) | sí |
| negative G coherent (G sign, R6, direct G uncredited) | sí |
| no value approved | sí |

**Veredicto:** `L_REFERENCE_AND_WRITER_AUTHORITY_READY`.

**Recomendación:** `MIGRATE_PULMONARY_EDEMA_SHADOW` (no se inicia).
<!-- /generado:veredicto -->

## 17. Ondulación sobre los paquetes cerrados

- **16 pruebas cerradas** (las adaptadas en P2O-1) leen los archivos P2O-1 a través de `lw.chain` y
  `lw.p2o1_sources`. Sus registros no cambian.
- **P2O-1:** lee los mismos bytes P2O-1 demostrados; su fijación de bytes se aplica a esa vista. En el núcleo vivo,
  la frontera de P2O-1 «L llega a la SpO2 sólo por G» deja de valer a propósito: `_perfusion` lee L para la cota de
  crédito. P2O-3 fija la frontera nueva (`boundaries`), y no hay diferencia numérica con L_rev = 0.
- **P2O-2:** el escaneo de lectores de L lee `derived.py` como lo dejó P2O-1.
- **P2N-2:** el registro congelado se compara sin el campo nuevo de las anclas, cuyo valor neutral (0) se comprueba.
- **Capas de llegada:** incluyen el insumo candidato de P2O-3.
- **Calibración:** `scenario_inputs` cambia por un campo neutral de las anclas, como en P2K-2; sin los cuatro campos
  es el digest de P2I-2AG.
- **Registros históricos:** P2G, P2I, P2I-2T y P2I-2U se regeneraron (sólo los digests).
- **Golden:** idéntico.

## 18. Revisión adversarial

Hubo una revisión independiente y de sólo lectura. Encontró 2 hallazgos medios, 5 bajos y ningún alto, todos
confirmados con sondas. El recongelamiento `fa42f2a` los incorpora. R1–R8, la composición, el signo de G y la G
directa no cambian respecto del registro de `7135e08`.

- **M1, dos dueños se sumaban:** ahora se rechaza un segundo dueño.
- **M2, en la guarda de G un escritor directo tomaba el crédito:** con L_rev < 0 la corrida se detiene.
- **Bajos:**
  - el límite del inicio fuera de la llegada queda declarado y fijado;
  - la etiqueta de cruce de la llegada;
  - la autoridad igual a la del tipo registrado, y tipos propios para las copias sintéticas;
  - la guarda de autoridad lee el registro;
  - dos docstrings actualizados.
- **Lo que se comprobó sólido:**
  - 28 escenarios contra la copia de `96b9d65`: idénticos byte a byte salvo los de sobrecarga con dueño;
  - 200 000 puntos de la SpO2 sin violaciones;
  - ninguna fuga de líneas B hacia V;
  - k, s y r en `None`;
  - GI idéntico.

<!-- generado:bordes -->
- La guarda de G detiene la corrida con L_rev < 0: sí; con L_rev = 0 la sostiene como en P2O-1: sí.
- Un minuto que cruza la llegada con L_rev < 0 se registra como cruce: sí.
- Límite conocido (inicio fuera de la llegada, L = L_rev con G = 0, escritor directo de G): G −0,50, SpO2 99,5 frente a 97,0 de llegada.
- Dueño con ganancia 0 en el escenario de sobrecarga: L final 0,000, frente a 0,661 con el acoplamiento común solo.
<!-- /generado:bordes -->

## 19. Límites y decisiones pendientes

- L_rev no tiene valor aprobado y los valores de las sondas no son clínicos.
- No hay aclaramiento bajo la llegada ni cinética de descongestión.
- La cota de crédito lee L; la alternativa (separar la G de cada origen) sería un cambio de estado mayor.
- La entrada de L_rev en el registro de parámetros de caso queda para cuando se adopte L → G.
- La deuda TD-114 (9), división por cero y texto de la guarda, sigue abierta: P2O-3 cambia el núcleo, pero el
  encargo lo limita a la autoridad y L_rev.
- Decisiones docentes:
  - si dos familias pueden compartir la autoridad sobre L;
  - si, bajo la autoridad, L debe responder al volumen;
  - si con L_rev = 0 la guarda de G también debe detener la corrida (TD-113 (10)).
- Siguiente paso recomendado, sin iniciar: `MIGRATE_PULMONARY_EDEMA_SHADOW`.
