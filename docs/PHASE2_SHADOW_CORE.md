# Fase 2 · Núcleo fisiológico común en modo sombra (preparación inicial)

| | |
|---|---|
| Rama | `phase-2-clinical-core-shadow` |
| Base | `6fad3103af531689af7995a4db3838418581f1c0` = `origin/phase-1-contracts-v2`, el SHA final de la Fase 1 |
| HEAD del código de la Fase 2 | P2C (§9): `2f5778b` KD-S1, `e685031` KD-S2, `f75da42` KD-S4 y el commit de clasificación que trae esta actualización. Antes: `04283c4` (P2B, §8) |
| Fuente de la arquitectura | `docs/CLINICAL_ENGINE_ARCHITECTURE_PROPOSAL.md` §7–§14 |
| Estado | **Sombra solamente.** `family_engine.py` sigue siendo la fuente de verdad de todo encuentro. Ningún módulo de la aplicación importa `clinical_core`; nada cambia para el residente. **No hay gancho en tiempo de ejecución** (§7). |

### Realineación sobre la Fase 1 final (2026-10-21)

La Fase 2 se escribió primero sobre `49ee2267c40550ef263fd8a99724eb991d29c5a6` (`pilot-residents-v1`). Después se
recreó la rama desde `6fad310` y se aplicaron con *cherry-pick* (`-x`) los cinco commits, en orden y sin conflictos:

| Original (sobre `49ee226`) | Sobre `6fad310` | Contenido |
|---|---|---|
| `465c6ea` | `ec65728` | Primitivos del núcleo |
| `1cc7a1b` | `f87f4e5` | Módulo de hemorragia digestiva |
| `08deb2c` | `2243fde` | Intervenciones y su procedencia |
| `2260149` | `022b992` | Endurecimiento tras la revisión adversarial |
| `8b7df70` | `3120e0c` | Arnés de comparación heredado/núcleo |

- El parche de la Fase 2 es idéntico byte a byte antes y después: mismo SHA-256 de `git diff`.
- La rama anterior queda en la referencia local `backup/phase-2-clinical-core-shadow-49ee226` (`8b7df70`).
- `phase-1-contracts-v2` y `pilot-residents-v1` no se modificaron.
- La Fase 1 sólo agrega `contracts_v2/`, sus pruebas y observadores en sombra en `app.py` y `order_pipeline.py`; no
  toca `family_engine.py` ni `family_parser.py`.
- El informe dorado generado sobre `6fad310` es igual al comprometido. Las diferencias KD-S1 a KD-S4 (§3) no
  cambiaron.

## 1. Qué se construyó

Paquete `clinical_core/`, sin dependencias de la aplicación salvo su adaptador de sólo lectura al motor de familias:

| Archivo | Contenido |
|---|---|
| `state.py` | `CoreState` tipado, inmutable y serializable: canales C1–C12 de la propuesta (§7.2); `RhythmState` (C4) como máquina de estados que no admite combinaciones imposibles; `Anchors` (llegada escrita del caso, §7.4) |
| `provenance.py` | Procedencia de cada cambio aplicado: `ChannelDelta`, `RhythmTransition`, `SettingChange`, `CoreEvent`, `MinuteRecord`, `attribution()` |
| `derived.py` | Valores derivados para una futura capa de observación (números y códigos, nunca narrativa) y la tabla `PARAMETERS` con el origen de cada ganancia |
| `integration.py` | Integrador determinista minuto a minuto, cotas con registro de *clamp*, conservación por canal, trayectorias reproducibles y escenarios serializables |
| `modules/gi_haemorrhage.py` | Primer módulo de enfermedad: hemorragia digestiva alta (V−, Hb−) |
| `modules/rhythm_events.py` | Eventos guionados declarados sobre R y P (causa y prevenibilidad, §8.4) |
| `logistics.py` | Finalización de la endoscopia como proceso logístico (§10.3) |
| `interventions/` | Cristaloide, glóbulos rojos, oxígeno (FiO2 como ajuste) e IBP (modulador) |
| `legacy_adapter.py` | Ruta directa al motor de familias: lo ejecuta sobre copias y lee sus entradas relevantes |
| `comparison.py`, `shadow.py`, `golden/gi_bleed_shadow.json` | Comparación heredado/núcleo y el resumen dorado comprometido |
| `contracts_legacy.py` | El motor de familias por el camino de órdenes de la página (Fase 0), con los Contracts v2 de cada turno (§8) |
| `contracts_input.py` | Entradas del núcleo desde Contracts v2 solamente: `OrderAction`, `FateReceipt`, `TurnTime`, `EventInterruption` (§8) |
| `contracts_output.py` | Salida del núcleo en forma de Contracts v2, siempre como sombra: `EventInterruption`, `ObservationSnapshot`, `TraceProvenance` (§8) |
| `contracts_shadow.py` | La comparación dorada por Contracts v2 (§8) |

### Canales

Se usan las definiciones canónicas de `docs/CLINICAL_ENGINE_ARCHITECTURE_PROPOSAL.md` §7.2. Coinciden con
`clinical_core/state.py`:
- **W (C7) = Ventilation.** Es la ventilación alveolar relativa a la necesidad: impulso, mecánica y fatiga.
- **D (C8) = Oxygen-delivery debt.** Es la deuda de entrega de oxígeno: el déficit acumulado de la entrega frente a
  la demanda, en índice·min.

W no es «obstrucción de la vía aérea», y D no es un «déficit genérico de distribución o perfusión». No deben
reinterpretarse así.

| Canal | Representación | Escrito hoy por |
|---|---|---|
| V | mL-equivalente, desviación de la llegada | hemorragia digestiva, cristaloide, glóbulos rojos |
| T, P | multiplicadores (llegada = 1) | P: evento guionado de bomba (sólo pruebas) |
| R | máquina de estados (código, frecuencia, factor de gasto, pulso) | eventos guionados de ritmo (sólo pruebas) |
| L, G, W, N | desviaciones de la llegada | nadie todavía (el canal existe, integra y tiene cotas) |
| D | índice·min, desviación de la llegada | el acoplamiento del propio núcleo (entrega frente a llegada) |
| Hb, glucosa, K | valores absolutos del caso | Hb: hemorragia, cristaloide, glóbulos rojos; glucosa y K: nadie todavía |

## 2. Garantías y su evidencia

| Garantía | Cómo se garantiza | Prueba |
|---|---|---|
| Determinismo | Sin reloj ni azar; cada contribuyente es una especificación congelada; su memoria vive en `CoreState.internal` | `test_same_inputs_give_an_identical_trajectory`, `test_the_shadow_runs_are_deterministic` |
| Orden de la lista irrelevante (T3) | Todos los contribuyentes leen el mismo estado previo al minuto | `test_the_order_contributors_are_listed_in_cannot_change_the_result` |
| Pasos de tiempo (T2) | Una corrida larga es igual a dos cortas | `test_one_long_run_equals_two_shorter_runs` |
| Replay | El escenario serializado a JSON se reconstruye, también en un proceso nuevo, y da el mismo digest; los digests coinciden con `PYTHONHASHSEED` distintos | `test_a_serialized_scenario_replays_identically` |
| Sin mutación oculta | Dataclasses congeladas, `FrozenRecord`; el integrador devuelve estado nuevo | `test_nothing_the_integrator_is_given_is_changed` |
| Procedencia completa | Todo delta exige `Source`, minuto y descripción; un contribuyente sólo escribe con su propia fuente, debe ser una dataclass congelada y no puede reclamar los tipos reservados (*clamp*, acoplamiento); sólo recibe las señales que declara; los *clamps* quedan registrados; el cambio de cada canal es igual a la suma de sus deltas | `test_every_change_has_a_source…`, `test_changes_without_a_valid_source_fail_closed`, `test_a_bound_that_acts_is_recorded_as_a_clamp` |
| Invariantes de paro (§11.4) | Sin pulso ⇒ VF, TV sin pulso, asistolia o AESP; FC 0 ⇔ asistolia; sin pulso, la PA, la SpO2, el TLC y la frecuencia de pulso no son medibles; no hay retorno de pulso sin reanimación modelada; las transiciones contradictorias fallan cerradas | `test_the_rhythm_state_cannot_hold…`, `test_an_arrest_is_one_consistent_terminal_state`, `test_a_pulse_cannot_return…`, `test_derived_values_that_contradict…` |
| Tiempo de las intervenciones | Una orden dada en el minuto s actúa por primera vez en (s, s+1]; las bolsas con duración, sin duración y detenidas | `test_an_order_acts_only_from_the_minute_after_it_is_given` y siguientes |
| Aislamiento de la sombra | Ningún módulo de la aplicación importa el núcleo; el núcleo no importa sesión, Trace ni persistencia; la corrida heredada es idéntica con o sin sombra; no se muta nada de lo que recibe | `test_shadow_core_isolation.py` |

## 3. Comparación heredado/núcleo

Hay 10 escenarios × 2 casos (`gi_bleed_57m`, `gi_bleed_72f`):
- sin tratamiento;
- cristaloide 2 L;
- 2 U de GR;
- oxígeno con mascarilla de no reinhalación;
- manejo definitivo (GR + IBP + gastroenterología → endoscopia a los 60 min);
- cristaloide seguido de sangre;
- dos órdenes sin duración que comparten la línea;
- dos bolsas con duración en una orden (la segunda se encola);
- «Stop IV fluids» a los 20 min;
- volumen agresivo (4 U + 2 L).

El motor de familias corre primero y solo. El núcleo corre después, con las mismas entradas leídas de esa corrida.

- **Exactas (ruido de coma flotante 1e-9).** Coinciden en todos los minutos de los 20 escenarios: Hb, glucosa, K,
  FiO2 y volúmenes entregados. V (contra la circulación convertida) coincide en todos salvo en el volumen agresivo
  (KD-S4).
- La entrega sigue lo que el motor de familias hizo:
  - las órdenes sin duración de un mismo tipo comparten una línea a la tasa por defecto;
  - una segunda bolsa con duración empieza donde lo dice su recibo, aunque sea a mitad de minuto;
  - «Stop IV fluids» cierra todo cristaloide previo y queda registrado con el id de la orden que lo detuvo.
- **Visualizadas** (PAS, PAD, PAM, FC, SpO2, FR, TLC, lactato). Se proyectan con la convención de pantalla del
  motor de familias (redondeo y rango) y se comparan por igualdad.
  - No hay tolerancia acordada (Apéndice A9): **toda diferencia se informa**.
  - Las diferencias de un paso cuyo valor crudo cae sobre un límite .5 se listan aparte como `rounding_tie`; no
    cuentan como coincidencia.
- **Categóricas** (pulso, familia de ritmo, conciencia): iguales salvo KD-S3.

> **Estado previo a P2C.** Esta tabla y las dos que la siguen describen las diferencias antes de las decisiones del
> 2026-10-22. Desde P2C las cuatro tienen decisión; el estado vigente, la clasificación y las magnitudes nuevas
> están en §9.

| Id | Diferencia | Magnitud máxima | Decisión pendiente |
|---|---|---|---|
| KD-S1 | Lactato y FR. El núcleo acumula D con pago de primer orden (τ provisional 60 min), incluye Hb y SaO2 en la entrega y deriva la FR del lactato (§7.3). El motor de familias los fija al instante desde la circulación, con un piso de FR de 14 en esta familia. **Brecha del núcleo:** la FR no tiene cota inferior fisiológica; en el volumen agresivo baja a 8/min (57m) y 6/min (72f) a los 90 min | Lactato 0,9 mmol/L (1,2 en volumen agresivo); FR 7/min (9 en volumen agresivo) | Docencia: τ de D, ganancia de la FR y si la FR sigue al lactato |
| KD-S2 | FC tras la hemostasia. El motor de familias resta 20 lpm × alivio directamente del observable (un módulo escribiendo un observable, lo que §8.1 excluye); el núcleo no tiene canal para esa recuperación | 15 lpm durante 61 min | Docencia: qué canal lleva esa recuperación |
| KD-S3 | Conciencia en el umbral de 80 mmHg. El motor de familias compara la PAS redondeada (80) y el núcleo la cruda (79,9) | 1 nivel, 1 minuto (57m) | Observation v2 (Fase 1): umbral sobre estado crudo o valor mostrado |
| KD-S4 | Volumen por encima del *clamp* de circulación del motor de familias (+625 mL-eq). El motor de familias corta ahí; el núcleo aún no tiene meseta de precarga (§7.3 pide ganancias acotadas) | V 559 mL-eq; PAS 31; PAD 17; PAM 22; FC 17; TLC 0,5 s | Docencia: forma y valor de la meseta volumen → gasto |

Las cuatro diferencias quedan **registradas, no resueltas**. No se ajustó ninguna ganancia para acercar el núcleo al
motor de familias. Cada decisión pendiente es:
- **KD-S1:** la constante de tiempo de D y si la FR sigue al lactato.
- **KD-S2:** qué canal o estado lleva la recuperación de la FC tras la hemostasia.
- **KD-S3:** si el umbral se aplica sobre el estado crudo o sobre el valor mostrado.
- **KD-S4:** el comportamiento de la meseta volumen → gasto (precarga).

Su alcance, verificado sobre `6fad310` e igual al de `49ee226`:

| Id | Corridas afectadas (de 20) |
|---|---|
| KD-S1 | 20 |
| KD-S2 | 2 |
| KD-S3 | 1 |
| KD-S4 | 2 |

### Tolerancias del Apéndice A9: sin resolver

Ninguna variable visualizada tiene tolerancia acordada. En `comparison.VARIABLES` todas valen `TBD`:
- PAS, PAD, PAM y FC;
- SpO2, FR y TLC;
- lactato.

La prueba `test_no_displayed_quantity_is_given_an_invented_tolerance` impide inventar una. Hasta que la docencia
fije las bandas, toda diferencia visualizada se informa.

Empates de redondeo informados aparte (antes de P2C; después de P2C no queda ninguno, §9.5):
- PAD y FC en el minuto 20 (sin tratamiento y oxígeno, ambos casos), y también PAM en 57m;
- PAD en el minuto 20 (2 U de GR, 57m);
- TLC en el minuto 112 (manejo definitivo, 57m).

El detalle minuto a minuto se regenera con `python -m clinical_core.shadow --out <directorio fuera del repo>`.

## 4. Parámetros

Cada ganancia está en `clinical_core.derived.PARAMETERS`, con su estado y su origen:
- **Adoptadas:** magnitudes del motor de familias (`GI_BLEED`, `_surface`, `_minute`, `_diagnostic`), convertidas a
  mL-equivalente: 1 U = 300 mL = 0,36 de circulación. No se ajustó ninguna a una trayectoria.
- **Provisionales:** τ de D (60 min), FR por lactato (7,5/min por mmol/L) y todas las cotas de canal salvo Hb y
  glucosa.
- Desde P2C, la lista completa de parámetros provisionales y la decisión de la que depende cada uno están en §9.4.

Los literales del motor que no están en una tabla quedan copiados, con su lugar, en
`legacy_adapter.LEGACY_LITERALS`.

## 5. Lo que no se hizo (a propósito)

- Ninguna familia salvo la hemorragia digestiva.
- Ningún gancho en tiempo de ejecución.
- Ningún cambio en `app.py`, `family_engine.py`, `family_parser.py`, `shared_order_language.py`,
  `submission_guard.py`, `rubric_screening.py`, persistencia, puntaje ni rúbricas.
- El adaptador rechaza, con `UnsupportedScenario`, lo que todavía no sigue, en vez de descartarlo:
  - una orden fuera de la ventana del escenario o con un minuto que no es entero;
  - un tipo de orden sin intervención en el núcleo (p. ej., TXA, noradrenalina, furosemida);
  - una operación de fluidos distinta de «stop»;
  - una orden retenida hasta un resultado, que el motor libera más tarde;
  - la exposición a anticoagulante.
- No se modelaban antes de P2C (desde P2C, ver §9):
  - la sobrecarga transfusional (L): ahora hay congestión por exceso de precarga sin reserva de bomba, sin
    aclaramiento;
  - la recuperación de la FC tras la hemostasia (KD-S2): ahora sale del impulso simpático común;
  - la meseta de precarga (KD-S4): ahora es una curva saturable continua.
- Sin escenario todavía: el *clamp* superior de circulación del motor de familias (1,9, o −750 mL-eq). Se alcanza
  hacia los 300 min sin tratamiento, por fuera de los escenarios actuales, y produciría una diferencia como KD-S4.
- Ni el ritmo ni la bomba de una familia real están migrados. Sólo los primitivos y sus pruebas sintéticas: el SCA
  inferior acopla isquemia, reperfusión, logística del cateterismo, VD dependiente de precarga y nitratos, y no era
  seguro moverlo en esta etapa.

## 6. Revisión adversarial

Una revisión independiente, en sólo lectura, encontró tres defectos altos en el adaptador:
- la línea compartida sin duración;
- el inicio de la segunda bolsa encolada;
- las órdenes retenidas hasta un resultado.

Encontró además defectos medios y bajos:
- órdenes descartadas en silencio fuera de la ventana;
- empates de redondeo que no verificaban el lado heredado;
- «Stop IV fluids» sin soporte;
- registro dependiente de importaciones previas;
- parada del oxígeno ambigua;
- serialización anidada;
- piso de lactato que movía una llegada baja;
- contribuyentes mutables o con tipo de fuente reservado;
- etiquetas categóricas desconocidas tratadas como no comparables.

Todos están corregidos, con una prueba que falla sin la corrección. Los escenarios de §3 sobre línea compartida,
bolsas encoladas y «stop» los ejercitan contra el motor de familias.

## 7. Puntos de conexión con la Fase 1 (SHA final `6fad310`)

Desde el paquete P2B (§8), el núcleo consume y emite Contracts v2 **fuera de línea**:

| Contrato de la Fase 1 (`contracts_v2`) | Dónde se conecta | Estado |
|---|---|---|
| WP1 `orders.OrderAction` | `contracts_input.adapt` | Hecho: cada intervención nace de una `OrderAction` |
| WP2 `fates.FateReceipt` | `contracts_input.adapt` | Hecho: el destino decide si la orden actuó; el núcleo lo cita, nunca lo crea |
| WP3 `timing.TurnTime` | `contracts_input.adapt` | Hecho: se contrasta `executed_at_min` y se rechaza un turno interrumpido |
| WP4 `events.EventInterruption` | `contracts_input.logistics_from_events` (entrada); `contracts_output.shadow_events` (salida) | Hecho: la endoscopia viene de su evento logístico |
| WP5 `observations.ObservationSnapshot` | `contracts_output.shadow_observation` | Hecho, en sombra; la comparación sigue leyendo `legacy_adapter.snapshot` |
| WP6 `trace.TraceProvenance` | `contracts_output.shadow_trace` | Hecho, en sombra; no toca el Trace autoritativo |
| WP7 `submissions` | Sólo la identidad de envío (`submission_id`) en `OrderAction` y `FateReceipt` | No se usa el registro de envíos: no hace falta para la identidad |
| Modelo terminal de la Fase 1 | `state.RhythmCode` y `NON_PERFUSING` | Etiquetas propias; `shadow_observation` expone `arrested` y `arrest_minute` |

**Sigue sin haber gancho en tiempo de ejecución.** No se agregó ninguno y la Fase 2 no lo necesita.
- Si se autorizara uno, los únicos puntos de entrada del motor en la aplicación son, sobre `6fad310`:
  - `app.py:9187` y `app.py:9236` (`execute_family_bundle`);
  - `app.py:870` (`advance_clinical_time`).
- La recomendación es **no** tocarlos y correr la sombra fuera de línea, desde los encuentros persistidos (Trace v2
  más el ledger de órdenes). Así no hay riesgo para el residente.

## 8. Adaptadores de Contracts v2 fuera de línea (P2B, 2026-10-21)

Nada de esto corre en la aplicación:
- `app.py`, `family_engine.py`, `family_parser.py` y `submission_guard.py` no importan `clinical_core`;
- la prueba `test_contracts_v2_feeds_the_core_but_the_runtime_never_reaches_the_core` recorre el grafo de
  importaciones del tiempo de ejecución: llega a `contracts_v2` pero nunca a `clinical_core`;
- `contracts_v2` no importa `clinical_core`.

### 8.1 Inventario (P2B-1)

**Entrada: de Contracts v2 al núcleo**

| Dato del núcleo | Contrato | Campo | Transformación | ¿Sin pérdida? |
|---|---|---|---|---|
| Id de la intervención | `OrderAction` | `order_id` | Ninguna | Sí |
| Envío en que se escribió | `OrderAction`, `FateReceipt` | `submission_id` | Ninguna; se conserva al arrastrarse a otro turno | Sí |
| Qué se ordenó | `OrderAction` | `fields` (lo que recibió el motor) | Lista blanca de campos por clase; cualquier otro campo se rechaza | Sí, para las clases admitidas |
| Si actuó | `FateReceipt` | `fate`, `limitation` | `EXECUTED` actúa; `RECORDED_NOT_MODELLED`, `UNRECOGNIZED`, `DUPLICATE_IGNORED` y `TERMINAL_NOT_EXECUTABLE` quedan ligadas sin efecto; el resto se rechaza | Sí |
| Minuto de inicio | `FateReceipt` (y `TurnTime`, que debe coincidir) | `executed_at_min` | Ninguna | Sí |
| Inicio de una bolsa en cola | **Ninguno** | — | Regla de cola del motor (`queued_start`), verificada contra el resumen del motor | **No lo lleva el contrato** |
| FiO2 de un dispositivo | **Ninguno** (`OrderAction` lleva `device` y `flow_lpm`) | — | Tabla del motor (`OXYGEN_FIO2`), verificada contra la FiO2 que fijó el motor | **No lo lleva el contrato** |
| Fin de la endoscopia | `EventInterruption` | evento `endoscopy`, `cause_class` `LOGISTIC`, `minute` | Ninguna | Sí |
| Llegada del caso (anclas) y tasa de sangrado | **Ninguno** | — | Del estado del caso y de `GI_BLEED`, como antes (`legacy_adapter`) | No es un dato de turno |

**Salida: del núcleo a Contracts v2, siempre en sombra**

| Contrato | Qué lleva | Qué no lleva nunca |
|---|---|---|
| `EventInterruption` | Los `CoreEvent` del núcleo, con fuente, minuto, severidad, causa y prevenibilidad; `interrupted` siempre `None` | Ningún evento del motor de familias |
| `ObservationSnapshot` | Canales, ritmo, FiO2, valores derivados crudos, `arrested` y `arrest_minute` | `visible`, etiquetas o valores redondeados para pantalla |
| `TraceProvenance` | Vínculos orden → fuente del núcleo (con el destino citado como `cited_fate`), eventos, observación final, limitaciones, versiones y procedencia minuto a minuto | `FateReceipt`, recibos, texto para el residente |
| `FateReceipt` | **No se emite**: los destinos son del ledger de la Fase 0 | — |

Toda salida lleva `namespace: clinical_core_shadow` y `authoritative: false`. `check_shadow_payload` la rechaza si
parece autoritativa, si no es JSON plano o si trae una clave visible para el residente.

`EventInterruption` v2 no tiene un campo para el espacio de nombres en el contenedor: sin eventos, su registro
sería igual a uno autoritativo. Fuera del Trace en sombra, todo registro viaja dentro de `envelope()`, que sí lo
lleva.

### 8.2 Lo que se rechaza explícitamente (`UnsupportedContract`)

- Una orden con destino pendiente o condicional (`HELD_CLARIFICATION`, `HELD_REASONING`, `SCHEDULED`): nunca se lee
  como dada ahora.
- Una orden con `limitation` o con destino `CANCELLED`, `DUPLICATE_CONFIRMED` o desconocido.
- Una `OrderAction` sin `FateReceipt`, y una orden ejecutada sin `OrderAction`.
- Una clase sin equivalente en el núcleo (por ejemplo, vasopresores) o un campo fuera de la lista blanca (por
  ejemplo, `after_result`).
- Un líquido que no sea cristaloide, una vía distinta de IV o IO, una operación distinta de «stop», o un `rate_ml_h`
  que no coincide con la duración.
- Un dispositivo de oxígeno que el motor no nombra, y una cánula nasal sin flujo.
- Un turno interrumpido.
- Un evento logístico distinto de la endoscopia, un evento `SCRIPTED_NATURAL_HISTORY` y una endoscopia repetida.

`ContractInputError` cubre las contradicciones entre contratos:
- una identidad que cambia al arrastrarse;
- un `executed_at_min` distinto entre `TurnTime` y `FateReceipt`;
- una orden ya ejecutada que un recibo posterior informa de otro modo;
- un minuto que no es entero.

Una orden arrastrada desde un turno anterior entra en la línea y en la cola en el orden en que el motor la ejecutó
(minuto de ejecución y lugar en ese turno), no en el orden en que se escribió por primera vez.

Las reevaluaciones con campos de espera u objetivo (`wait`, `immediate`, `target`) también se rechazan. Es más
restrictivo de lo necesario, porque no cambian la fisiología, pero falla cerrado.

Los eventos del motor que no son entradas (por ejemplo, de fisiología) quedan listados como «no consumidos» en las
limitaciones del Trace en sombra.

### 8.3 Comparación dorada por Contracts v2 (P2B-4)

`python -m clinical_core.contracts_shadow` corre los 10 × 2 escenarios así:
1. el motor de familias por el camino de órdenes de la página (`pilot_acceptance.Encounter` sin Streamlit), un
   minuto por turno;
2. las intervenciones del núcleo desde los contratos de esos turnos.

Resultado:
- El informe dorado es **idéntico al comprometido**. La única transformación es escribir cada `order_id` del ledger
  en el nombre del adaptador heredado (`m<minuto>-<índice>-<tipo>`).
- Las coincidencias exactas no cambiaron, y KD-S1 a KD-S4 tampoco, con las mismas magnitudes.
- El curso del núcleo es idéntico, minuto a minuto, al de la ruta directa en todos los canales, el ritmo, la FiO2 y
  los valores derivados.
- El curso del motor por el camino de la página es idéntico al de la ruta directa.
- No se ajustó nada.

Una revisión adversarial de sólo lectura encontró tres defectos, todos corregidos y cada uno con una prueba que
falla sin la corrección. Ninguno afectaba los escenarios dorados:
- el orden de ejecución de una orden arrastrada;
- un recibo posterior que contradecía una orden ya ejecutada;
- el registro de eventos vacío sin espacio de nombres.

### 8.4 Lo que se pierde y lo que falta

- **Sin pérdida** para lo que el núcleo modela hoy: identidad, envío, momento, qué se ordenó y si actuó.
- **Dos datos que Contracts v2 no lleva** y que se reconstruyen por regla:
  - el inicio de una bolsa en cola;
  - la FiO2 de un dispositivo.

  La comparación los verifica contra el motor y falla cerrada si difieren. **Decisión pendiente:** si una versión
  futura del contrato debe llevarlos.
- **Fuera de los contratos de turno:** las anclas de llegada y los parámetros de la hemorragia (`GI_BLEED`). Siguen
  leyéndose del caso.
- El registro de envíos (WP7) no se usa: la identidad de envío ya viaja en `OrderAction` y `FateReceipt`.

## 9. P2C · Restricciones de calibración fisiológica (KD-S1, KD-S2, KD-S4; 2026-10-22)

- Base: `04283c4` (P2B cerrado).
- Commits: `2f5778b` KD-S1, `e685031` KD-S2, `f75da42` KD-S4 y el de clasificación y documentación que trae esta
  sección.
- Sigue todo en sombra y fuera de línea, sin gancho en tiempo de ejecución ni cambio visible para el residente.
  `family_engine` sigue siendo la fuente de verdad.
- Ningún parámetro se eligió para acercar el núcleo al golden. Los valores nuevos son provisionales (§9.4).

### 9.1 Decisiones y lo implementado

**KD-S1 · REVISE CORE.** D, lactato y FR.
- D no cambia: `dD = (1 − entrega_rel) − D/τ_D`. Acumula memoria y se paga de forma gradual.
- **Lactato.** El núcleo guarda el exceso X sobre la llegada en su propia memoria
  (`core_coupling:lactate_kinetics`).
  - Dinámica: `dX = k·D − X/τ_lac`, con `k = ganancia/(τ_D·τ_lac)`.
  - En estado estable conserva la ganancia adoptada: 2 mmol/L por unidad de déficit de entrega.
  - Lectura: lactato = llegada + X. El piso de 0,8 no mueve una llegada que ya está por debajo.
- **FR.** `FR = impulso × (parte ventilatoria × (1 + max(0, W)) + escala × M(lactato))`, con tope `rr_max`.
  - `impulso = max(0, 1 + min(0, W))`: una W deprimida (opioide) reduce las dos partes.
  - M es un impulso metabólico saturable por encima de un umbral (2 mmol/L), con máximo `rr_metabolic_max`.
  - La FR de llegada se reparte entre una parte ventilatoria, nunca menor que el piso de 12, y una metabólica. Al
    aclararse el lactato sólo baja la parte metabólica.
  - Una W aumentada suma sólo a la parte ventilatoria.
- Resultado: aclarar el lactato nunca causa bradipnea. Sólo un mecanismo explícito de W la causa.

**KD-S2 · ADOPT CORE DIRECTION.** FC.
- La FC sinusal es la frecuencia intrínseca de R más `respuesta × (1 − betabloqueo) × S`.
- S es un único impulso simpático común, guardado en la memoria del núcleo (`core_coupling:sympathetic_drive`).
  - Sube de inmediato al objetivo y baja con una constante de tiempo τ_S.
  - El objetivo suma, respecto de la llegada:
    - el déficit de presión;
    - D/τ_D;
    - la hipoxemia;
    - la hipoglucemia.
  - Tiene un piso de retirada.
- **Hipercapnia, dolor o agitación, fiebre y abstinencia** quedan declarados como entradas del mismo impulso. No se
  modelan: ningún estado del núcleo los lleva todavía.
- `GIHaemorrhage` sólo escribe V y Hb, y no hay regla de FC propia de ninguna familia. La hemostasia baja la FC sólo
  a través de la presión recuperada y la deuda pagada.
- Un ritmo no sinusal (bloqueo, escape, marcapasos) conserva la frecuencia que tiene.
- Declaración nueva del caso: `Anchors.beta_blockade`, de 0 a 1. El valor por defecto, 0, significa «no declarado».

**KD-S3 · RESUELTA, sin cambios.**
- La fisiología usa el estado sin redondear; la pantalla y la habilitación de oportunidades usan Observation v2.
- No se tocó el código del umbral de conciencia (`_level`, `pressure_levels`, `oxygen_levels`).
- Sí cambió dónde aparece la diferencia, por KD-S4; ver §9.5.

**KD-S4 · REVISE CORE.** Precarga y rendimientos decrecientes.
- **Posición en la curva:** `p(V) = 1 − exp(−max(0, x0 + V)/λ)`, con `x0 = −λ·ln(1 − p0)`. La curva es cóncava en
  todo su rango, sin *clamp*, y su meseta `P/p0` nunca se alcanza.
- **Gasto:** `gasto = P × factor de ritmo × p(V)/p0 × 1/(1 + a·(T − 1))`. La presión es `gasto × T`.
- **p0, la posición de llegada:** `Anchors.preload_fraction`; si no se declara, 0,5 (provisional).
  - Con λ = 833,33 mL-eq y p0 = 0,5, la pendiente en la llegada es 1/833,33 por mL: la del motor heredado (300 mL
    por 0,36 de circulación). Es la única ancla adoptada de la curva.
  - Un p0 bajo describe un paciente dependiente de precarga; uno alto, un corazón cerca de su meseta.
- **Congestión.** El acoplamiento del núcleo `core_coupling:preload_congestion` escribe L:
  `dL = g × max(0, (p − rodilla)/(1 − rodilla)) × max(0, 1 − reserva × P)`.
  - Una bomba con reserva plena y P normal nunca congestiona sólo por precarga.
  - No hay aclaramiento de L (§9.8).
- Declaración nueva del caso: `Anchors.pump_reserve`, de 0 a 1. El valor por defecto es 1.

### 9.2 Nivel 1 · Restricciones cualitativas

`test_clinical_core_calibration.py`, 38 pruebas. Todas comprueban dirección, monotonía, memoria, saturación y
ausencia de estados imposibles, nunca un número del golden.

- **KD-S1:**
  - los escenarios de aceptación 1 a 4;
  - ninguna FR < 10 por aclaramiento, con cuatro llegadas parametrizadas;
  - la bradipnea sólo por W.
- **KD-S2:**
  - las trayectorias A a E;
  - una reproducción sin módulo de hemorragia: los mismos V y Hb dan la misma FC en cada minuto;
  - una hipoglucemia de otra familia;
  - la memoria del impulso;
  - un ritmo con frecuencia propia.
- **KD-S4:**
  - concavidad en nueve curvas: posición 0,25, 0,5 y 0,8, cada una con bomba normal, bomba al 50 % y tono 1,8;
  - los escenarios de aceptación 1 a 7;
  - congestión sólo sin reserva o con una bomba que falla;
  - nada bajo la rodilla ni en shock;
  - la pendiente adoptada.
- **Nivel 2:** las bandas siguen TBD y las sondas son deterministas.

Pruebas adaptadas, que protegen lo mismo que antes:
- `test_a_rounding_tie_needs_both_sides_on_the_same_boundary` pone el empate a mano (PAD 52,5), porque las
  corridas ya no producen ninguno.
- `test_clinical_core_primitives` ignora las claves `core_coupling:*` en `internal_updates` (P2C-1).

### 9.3 Nivel 2 · Sondas por familia (preparado, no finalizado)

`python -m clinical_core.bands` corre sondas sintéticas sobre una llegada neutra común (PA 120/75, FC 80, FR 16, Hb
13). No son casos del banco. Cada sonda mueve sólo los canales declarados.

**Ninguna banda está fijada (`BANDS` = TBD). Las fija la docencia: la IA no fija bandas clínicas.** Lecturas con
los parámetros provisionales:

| Sonda | Familia | Qué mueve | Lectura del núcleo |
|---|---|---|---|
| `haemorrhage` | Hemorragia / trauma | V −10 mL/min y Hb −0,02/min durante 60 min | min 30: PAM 76, FC 92, gasto 0,57; min 60: PAM 58, FC 109, lactato 1,2, gasto 0,00 |
| `vasodilation` | Sepsis | T −0,01/min durante 40 min (hasta 0,6) | min 40: PAM 80, FC 88, gasto 1,14, D −2,1, lactato 1,0 |
| `pump_failure_then_bolus` | SCA | P hasta 0,7 en 30 min; 500 mL en el min 40 | min 30: PAM 80, gasto 0,70; tras 500 mL: PAM 91, gasto 1,02 |
| `preload_dependent` | VD / TEP | p0 0,25; −200 mL en el min 1; +250 mL en el min 20 | min 1: PAM 64, gasto 0,19; min 20: PAM 96, gasto 1,17 |
| `overload` | Edema pulmonar | p0 0,8, reserva 0,3, P −0,3; +20 mL/min durante 100 min | gasto 0,70 → 0,86 con 2 L; L 0 → 1,98 |
| `bronchospasm` | Asma | W +0,5 | FR 16 → 24 |
| `opioid` | Opioide | W −0,7 | FR 16 → 5 (bradipnea por W) |

Hallazgos para la docencia. No se corrigieron, porque eso sería ajustar parámetros TBD:
1. **Gasto 0 con pulso presente.**
   - Con unos 600 mL-eq bajo la llegada (p0 = 0,5), el gasto llega a 0. El pulso sigue presente y la PAM es 58,
     porque la presión se lee del gasto con la ganancia lineal adoptada.
   - El núcleo no tiene transición a paro por gasto nulo. El motor heredado lo oculta con su piso de circulación de
     0,25.
   - En el golden no ocurre: el V mínimo es −150 mL-eq y el gasto mínimo 0,80.
2. **Lactato bajo en shock profundo.** La ganancia adoptada (2 mmol/L por déficit pleno) y τ_lac = 60 dan 1,2 mmol/L
   a los 60 min de un shock con gasto nulo.
3. **Sepsis sin demanda.** La vasodilatación sola mejora el gasto por menor poscarga, y D queda negativa. La demanda
   metabólica no tiene canal.
4. **P sólo escala la curva.** Una bomba al 70 % sobre una llegada en p0 = 0,5 se compensa del todo con 500 mL
   (Frank–Starling).
   - No se puede compensar sólo si P < p0.
   - Queda por decidir si P también aplana la curva: es la «sensibilidad a P», TBD.
5. **Respuesta de FC acotada por la ganancia adoptada.** Son 25 lpm por unidad de impulso: con gasto nulo, la FC
   sube unos 29 lpm.

### 9.4 Parámetros que siguen TBD (ninguno se declara aprobado)

| Parámetro del encargo | En `derived.PARAMETERS` | Valor provisional |
|---|---|---|
| τ de recuperación de D | `debt_clearance_tau_min` | 60 min |
| déficit de entrega → D | integral directa de `1 − entrega_rel` (ganancia 1) | 1 |
| D → lactato | `lactate_per_output_deficit` (estado estable; adoptada del heredado) | 2 mmol/L |
| aclaramiento de lactato | `lactate_clearance_tau_min` | 60 min |
| impulso metabólico → FR | `rr_per_lactate`, `lactate_drive_threshold_mmol_l`, `rr_metabolic_max` | 7,5/min por mmol/L; 2 mmol/L; 25/min |
| cotas fisiológicas de FR | `rr_ventilatory_floor`, `rr_max` (cota de seguridad) | 12; 60 |
| déficit de PAM/gasto → impulso simpático | `sympathetic_per_pressure_deficit`, `sympathetic_per_debt` | 1; 0,5 |
| otras entradas del impulso | `sympathetic_per_hypoxaemia_point`, `hypoxaemia_threshold_spo2`, `sympathetic_per_hypoglycaemia_mg_dl`, `hypoglycaemia_threshold_mg_dl`, `sympathetic_withdrawal_limit` | 0,02; 94 %; 0,01; 70 mg/dL; 1 |
| tiempo de decaimiento simpático | `sympathetic_decay_tau_min` | 5 min |
| forma de la curva precarga → VS | exponencial saturable `1 − exp(−x/λ)` | — |
| punto medio / semisaturación | `preload_curve_scale_ml`, `arrival_preload_fraction` | 833,33 mL-eq; 0,5 |
| sensibilidad a P | P multiplica el gasto (exponente 1, sin parámetro propio) | 1 |
| sensibilidad a T / poscarga | `afterload_sensitivity` | 0,3 |
| umbral y ganancia V/precarga → L | `congestion_preload_knee`, `congestion_per_excess_preload` | 0,85; 0,05/min |

Siguen adoptadas del motor heredado, sin cambio de valor:
- `sbp_per_pressure_deficit`, `dbp_per_pressure_deficit`;
- `hr_per_sympathetic_drive` (25, antes `hr_per_pressure_deficit`);
- `crt_per_output_deficit_s`, `spo2_per_fio2`;
- `lactate_floor` y los umbrales de conciencia.

### 9.5 Nivel 3 · Golden antes y después, y clasificación

| Variable | Corridas antes (`04283c4`) | Máx. antes | Corridas después | Máx. después | Razón |
|---|---|---|---|---|---|
| Lactato | 20 | 1,2 mmol/L | 20 | 1,5 mmol/L | KD-S1 |
| FR | 20 | 9/min | 20 | 11/min | KD-S1 |
| FC | 4 | 17 lpm | 20 | 12 lpm | KD-S2 (18 corridas); KD-S4 en volumen agresivo (2) |
| PAS | 2 | 31 mmHg | 20 | 10 mmHg | KD-S4 |
| PAD | 2 | 17 mmHg | 20 | 6 mmHg | KD-S4 |
| PAM | 2 | 22 mmHg | 19 | 7 mmHg | KD-S4 |
| TLC | 1 | 0,5 s | 18 | 0,9 s | KD-S4 |
| V (mL-eq) | 2 | 559 | 2 | 559 | KD-S4 |
| Conciencia | 1 (1 min) | 1 nivel | 1 (6 min) | 1 nivel | KD-S3 (ver abajo) |

**Lectura de la tabla:**
- Pares (corrida, variable) con diferencia: 54 → 140.
- Las diferencias se generalizan, porque cada mecanismo aprobado ahora actúa en todas las corridas. A la vez
  bajan las magnitudes máximas de presión y FC.
- La FR mínima del núcleo en los escenarios pasó de 6–8/min a 20/min.

**Clasificación** (`shadow.classify`, guardada en el golden por escenario):
- 220 MATCH, 140 APPROVED DIFFERENCE y 0 UNRESOLVED DIFFERENCE.
- Cada diferencia aprobada lo es por su **dirección**. Su magnitud depende de parámetros TBD (§9.4) y de las
  tolerancias del Apéndice A9, que siguen sin fijar.

APPROVED DIFFERENCE, por decisión:
- **KD-S1:** lactato y FR en las 20 corridas.
- **KD-S2:** FC en 18 corridas: todas salvo el volumen agresivo.
- **KD-S3:** conciencia en 57m sin tratamiento.
- **KD-S4:**
  - PAS y PAD en 20 corridas;
  - PAM en 19 (no en oxígeno 72f);
  - TLC en 18 (no en los dos escenarios de oxígeno);
  - V y FC en volumen agresivo, en ambos casos.

Atribuciones mixtas, ambas aprobadas:
- **FC en volumen agresivo.** Va bajo KD-S4, la causa mayor, pero el impulso de KD-S2 también contribuye.
- **Conciencia en 57m sin tratamiento.**
  - El núcleo lee el umbral de 80 mmHg sobre la PAS cruda (KD-S3, sin cambios).
  - La curva de KD-S4 baja esa PAS menos de 1 mmHg, así que el cruce llega en el minuto 55 y no en el 60.
  - Minutos 55–57: la PAS mostrada coincide (80) y sólo difiere la lectura cruda (KD-S3).
  - Minutos 58–60: la PAS mostrada del núcleo ya es 79 (KD-S4).

UNRESOLVED DIFFERENCE: ninguna en el golden.
- La prueba `test_a_difference_without_an_approved_decision_stays_unresolved` asegura que una diferencia nueva sin
  decisión aprobada quede como UNRESOLVED.
- Lo que sigue sin resolver son magnitudes, tolerancias y los hallazgos de §9.3 y §9.8.

**Golden por Contracts v2:** sigue IDÉNTICO al comprometido (`python -m clinical_core.contracts_shadow`).

### 9.6 Brechas de contrato de P2B (registradas, sin rediseñar)

- **P2B-01.** Contracts v2 no lleva explícito el `actual_start_min` de una entrega en cola.
- **P2B-02.** Contracts v2 no lleva explícita la FiO2 efectivamente aplicada.
- **Mitigación vigente:**
  1. reconstrucción determinista;
  2. comparación con el motor autoritativo;
  3. falla cerrada si difieren (`check_rebuilt_against_engine`).
- **Objetivo futuro:** un contrato de ejecución o entrega (*Execution/Delivery*).
- En P2C no se modificaron `OrderAction` v2 ni `FateReceipt` v2.

### 9.7 Contradicción señalada (decisión pendiente)

- La propuesta (§7.3) dice que las cantidades derivadas «no se guardan».
- Pero KD-S1 pide un lactato «con producción y aclaramiento», y KD-S2 un tiempo de decaimiento simpático. Las dos
  cosas implican memoria.
- Se implementó como memoria del propio núcleo en `CoreState.internal`, bajo claves `core_coupling:*` que sólo
  escribe el integrador:
  - no es un canal nuevo;
  - ningún módulo puede escribirla;
  - se repite de forma determinista.
- Falta decidir si esa memoria debe ser un canal declarado de la propuesta.

### 9.8 Limitaciones

- Los hallazgos 1 a 5 de §9.3.
- **L no se aclara:** ningún mecanismo del núcleo reduce el agua pulmonar todavía.
- **Cota del canal V** en ±3000 mL-eq: es una guarda, no fisiología.
- **Declaraciones del caso sin mapear.** El adaptador heredado no traduce betabloqueo, posición de precarga ni
  reserva de bomba desde los casos del banco, y los casos GI quedan con los valores por defecto. El motor heredado
  tampoco los modela en esta familia.
- **Entradas simpáticas sin estado.** La hipercapnia, el dolor, la fiebre y la abstinencia no tienen estado en el
  núcleo.

### 9.9 Gancho en tiempo de ejecución

No hay ninguno. Ningún módulo de la aplicación importa `clinical_core`: `test_shadow_core_isolation.py` lo
comprueba, incluido el cierre de importaciones desde `app`, `family_engine`, `family_parser`, `submission_guard` y
`order_pipeline`.
