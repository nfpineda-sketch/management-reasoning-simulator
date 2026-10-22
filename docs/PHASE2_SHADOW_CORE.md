# Fase 2 · Núcleo fisiológico común en modo sombra (preparación inicial)

| | |
|---|---|
| Rama | `phase-2-clinical-core-shadow` |
| Base | `6fad3103af531689af7995a4db3838418581f1c0` = `origin/phase-1-contracts-v2`, el SHA final de la Fase 1 |
| HEAD del código de la Fase 2 | P2D (§10): `bd21780`, `c052c75`, `d3b498e`, `fc46711` y el commit de clasificación causal que trae esta actualización. Antes: `d543cd9` (P2C, §9) y `04283c4` (P2B, §8) |
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

> **Estado de P2C.** P2D (§10) cambia, entre otras cosas:
> - la clasificación: ya no hay «APPROVED DIFFERENCE», ahora es APPROVED_DIRECTION_MAGNITUDE_TBD;
> - el piso del impulso simpático y su consecuencia en la FC;
> - la curva de precarga, que ahora depende de P;
> - el aclaramiento de L;
> - la sonda de hemorragia, que ahora se detiene en un límite sin resolver.
>
> Donde §9 y §10 difieran, rige §10.

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
- **FR.** `FR = impulso × (parte ventilatoria × (1 + max(0, W)) + parte metabólica)`, con tope `rr_max`.
  - `impulso = max(0, 1 + min(0, W))`: una W deprimida (opioide) reduce las dos partes.
  - M es un impulso metabólico saturable por encima de un umbral (2 mmol/L), con máximo `rr_metabolic_max`.
  - La FR de llegada se reparte entre una parte ventilatoria, nunca menor que el piso de 12, y la parte metabólica
    que explica el lactato de llegada.
  - Un lactato que sube sobre la llegada suma todo su aumento de M.
  - Un lactato que baja quita, como mucho, la parte metabólica de llegada.
  - La respuesta es continua en el lactato actual y en el de llegada.
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
- Sin pulso no se guarda impulso. Si el pulso vuelve, el impulso parte de lo que pide el estado.
- Declaración nueva del caso: `Anchors.beta_blockade`, de 0 a 1. El valor por defecto, 0, significa «no declarado».

**KD-S3 · RESUELTA, sin cambios.**
- La fisiología usa el estado sin redondear; la pantalla y la habilitación de oportunidades usan Observation v2.
- No se tocó el código del umbral de conciencia (`_level`, `pressure_levels`, `oxygen_levels`).
- Sí cambió dónde aparece la diferencia, por KD-S4; ver §9.5.

**KD-S4 · REVISE CORE.** Precarga y rendimientos decrecientes.
- **Posición en la curva:** `p(V) = 1 − exp(−max(0, x0 + V)/λ)`, con `x0 = −λ·ln(1 − p0)` (calculado con
  `log1p`/`expm1`).
  - Mientras el ventrículo se llena (gasto > 0), la curva es cóncava y no tiene *clamp* superior. Su meseta `P/p0`
    nunca se alcanza.
  - Bajo el punto vacío el gasto es 0: es un piso, con quiebre.
  - Ninguna curva que nunca sea negativa puede ser cóncava para todo V. La regla «d(gasto)/dV decrece» rige
    donde el ventrículo se llena.
- **Gasto:** `gasto = P × factor de ritmo × p(V)/p0 × 1/(1 + a·(T − 1))`. La presión es `gasto × T`.
- **p0, la posición de llegada:** `Anchors.preload_fraction`; si no se declara, 0,5 (provisional).
  - Con λ = 833,33 mL-eq y p0 = 0,5, la pendiente en la llegada es 1/833,33 por mL: la del motor heredado (300 mL
    por 0,36 de circulación). Es la única ancla adoptada de la curva.
  - Un p0 bajo describe un paciente dependiente de precarga; uno alto, un corazón cerca de su meseta.
- **Congestión.** El acoplamiento del núcleo `core_coupling:preload_congestion` escribe L:
  `dL = g × max(0, (p − s)/(1 − s)) × max(0, 1 − reserva × P)`, con `s = max(rodilla, p0)`.
  - Sólo congestiona la precarga agregada sobre la llegada y sobre la rodilla: la «V adicional» de KD-S4. La
    llegada queda como punto fijo, igual que en los demás acoplamientos.
  - Una bomba con reserva plena y P normal nunca congestiona sólo por precarga.
  - No hay aclaramiento de L (§9.8).
- Declaración nueva del caso: `Anchors.pump_reserve`, de 0 a 1. El valor por defecto es 1.

### 9.2 Nivel 1 · Restricciones cualitativas

`test_clinical_core_calibration.py`, 45 pruebas. Todas comprueban dirección, monotonía, memoria, saturación y
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
- **Tras la revisión adversarial (§9.10):**
  - la continuidad de la FR en el lactato de llegada;
  - el aumento metabólico completo sobre una llegada acidótica;
  - una posición de llegada mínima que reproduce la llegada;
  - la llegada como punto fijo de la congestión;
  - ningún impulso guardado sin pulso.

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
- 220 MATCH, 140 APPROVED DIFFERENCE y 0 UNRESOLVED DIFFERENCE. (Desde P2D, «APPROVED DIFFERENCE» se llama
  APPROVED_DIRECTION_MAGNITUDE_TBD: lo aprobado es la dirección, no la magnitud; §10.9.)
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
  - Minutos 55–57: la PAS mostrada del núcleo es 80 (el heredado muestra 81, 80 y 80). Ese 80 no cruza el umbral:
    el cruce viene de la lectura cruda (KD-S3).
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
- **Pulso estrecho: la corrida falla cerrada.**
  - La caída de la PAS (45 por unidad de déficit) es mayor que la de la PAD (25), ambas adoptadas del heredado.
  - Con una presión de pulso de llegada PP, un déficit mayor que PP/20 rompe el invariante PAS > PAD, y `step`
    lanza `CoreInvariantError`.
  - Con la curva nueva ocurre antes. Llegada de 86/70 con sangrado de 10 mL/min: minuto 49, frente al 67 en
    `04283c4`.
  - El motor heredado lo evita con su piso de circulación de 0,25. En los casos GI del golden (PP 34) no ocurre.
- **Retirada simpática absoluta.** El piso de retirada (−25 lpm) no es relativo a la frecuencia intrínseca:
  - un sinusal de 40 puede bajar a 15 lpm;
  - uno de ≤ 25 con mucha retirada falla cerrado («a perfusing rhythm has a positive rate»).
  - Antes de P2C la bajada no tenía cota.
- **La clasificación sigue el mapeo variable → decisión, no la causa de cada diferencia.**
  - Una diferencia futura en una variable ya mapeada saldría APPROVED.
  - La protege el golden comprometido: cualquier cambio de magnitud hace fallar la prueba del golden y obliga a
    revisarlo.
  - Un empate de redondeo sin desajuste se clasifica MATCH, porque el valor crudo es el mismo. El resumen lo sigue
    informando aparte y nunca lo cuenta como coincidencia.

### 9.9 Gancho en tiempo de ejecución

No hay ninguno. Ningún módulo de la aplicación importa `clinical_core`: `test_shadow_core_isolation.py` lo
comprueba, incluido el cierre de importaciones desde `app`, `family_engine`, `family_parser`, `submission_guard` y
`order_pipeline`.

### 9.10 Revisión adversarial de P2C

Una revisión independiente, en sólo lectura, de `04283c4..9abc19a` no encontró defectos altos. Cada hallazgo se
confirmó con una sonda antes de tocarlo.

Corregidos, cada uno con una prueba que falla sin la corrección:
- **M1, FR.** La respuesta de la FR al lactato era discontinua en el lactato de llegada: con FR de llegada ≤ 12,
  pasar de 2,000 a 2,001 mmol/L la apagaba (29,5 → 12,0/min a lactato 6). Ahora es continua, y un aumento sobre la
  llegada recibe todo el impulso metabólico.
- **L2, precisión.** Una posición de llegada mínima perdía precisión (`log`/`exp`). Ahora se calcula con
  `log1p`/`expm1`.
- **L3, congestión.** Subía desde la llegada sin ninguna entrada cuando p0 superaba la rodilla. Ahora es la llegada
  como punto fijo.
- **L5, texto.** Faltaba precisión sobre los minutos de la conciencia, aquí y en `shadow.py`.
- **L6, impulso sin pulso.** El impulso se guardaba un minuto tras la pérdida de pulso. Ahora es 0 sin pulso.

Las correcciones no cambian el golden ni la tabla de sondas de §9.3. El golden por Contracts v2 sigue IDÉNTICO.

Quedan documentados (§9.8), no corregidos, porque arreglarlos inventaría fisiología o cambiaría ganancias
adoptadas:
- **M2:** pulso estrecho;
- **L1:** retirada simpática absoluta;
- **L4:** clasificación por mapeo.

## 10. P2D · Invariantes estructurales antes de la calibración de Nivel 2 (2026-10-22)

- Base: `d543cd9` (P2C aceptado en dirección).
- Commits:

  | Commit | Contenido |
  |---|---|
  | `bd21780` | P2D-1 |
  | `c052c75` | P2D-2/3 |
  | `d3b498e` | P2D-4/5/6 |
  | `fc46711` | P2D-8 |
  | commit de esta sección | P2D-7/9 y documentación |

- Sigue todo en sombra y fuera de línea, sin gancho en tiempo de ejecución ni cambio visible para el residente.
- P2D es estructural: no fija ningún número de Nivel 2 ni ajusta nada para acercarse al motor heredado.

### 10.1 Estado dinámico auxiliar explícito (P2D-1)

Tres capas:

| Capa | Qué es | Dónde vive |
|---|---|---|
| **Estado de canales del núcleo** | V, T, P, R, L, G, W, D, N, Hb, glucosa, K | Campos de `CoreState`; sólo cambian por deltas con procedencia |
| **Estado dinámico auxiliar** | Memoria que el núcleo necesita para derivar observables o respuestas en el tiempo: el exceso de lactato (KD-S1) y el impulso simpático (KD-S2) | `CoreState.aux`, un `AuxiliaryState` tipado, inmutable y serializable |
| **Observable derivado** | Función pura del estado de canales más el auxiliar: presión, FC, FR, lactato, TLC, conciencia | `derive()`; no se guarda |

- No es un canal nuevo (no hay C13 ni C14) ni un registro de un contribuyente. Sólo el integrador lo cambia.
- **Procedencia.** Cada cambio es un `AuxiliaryChange` (antes, después, fuente `core_coupling:*`, minuto) dentro del
  `MinuteRecord`. La verificación de conservación rechaza un cambio sin registro.
- **Serialización determinista.** `CoreState.to_dict`/`from_dict` y el digest lo incluyen.
- **Reproducción.** Una corrida retomada desde un estado serializado es la misma corrida, prueba con digest minuto a
  minuto.
- **Copia profunda.** `deepcopy` y `pickle` del estado fallaban por `FrozenRecord`; ahora funcionan.
- **Traza en sombra.** La `TraceProvenance` lo lleva como estado interno no autoritativo (`core_auxiliary_state`), y
  cada minuto con sus cambios. Nunca se muestra al residente.
- **Contradicción con la propuesta, resuelta.** Esto responde a la contradicción con la propuesta §7.3 señalada en
  §9.7: la memoria es explícita, tipada y separada de lo derivado.

### 10.2 Gasto cero, pulso y presión (P2D-2)

- Un pulso con gasto efectivo nulo, y una presión medible sin gasto, son estados prohibidos.
- `derive` lanza `UnresolvedBoundary` cuando el gasto llega al cero numérico (`OUTPUT_EPSILON` = 1e-9, una guarda
  numérica, no un umbral clínico) con pulso presente.
  - No hay una regla aprobada de transición terminal que aplique ahí: el umbral y la permanencia del paro siguen TBD.
  - Por eso la corrida falla cerrada en ese minuto, con un mensaje que nombra el límite, en vez de inventar un paro.
- `check()` rechaza:
  - un pulso sin gasto;
  - cualquier presión sin gasto.
- En un estado sin pulso:
  - PA, SpO2, TLC y frecuencia de pulso no son medibles;
  - una AESP conserva su frecuencia de monitor.
- Un evento de ritmo declarado (paro antes del límite) sí se usa: la corrida sigue sin pulso.
- La sonda de hemorragia de Nivel 2 se detiene en el minuto 58 y lo dice.
- **Queda sin resolver:** la franja entre el cero numérico y un umbral clínico de paro. Con la relación lineal
  adoptada, un gasto muy bajo todavía muestra una PAS cercana a llegada − 45.

### 10.3 El impulso simpático nunca es negativo (P2D-3)

- **Regla.** FC sinusal = frecuencia intrínseca de R + 25 × (1 − betabloqueo) × S, con S ≥ 0. Concretamente:
  - el objetivo del impulso tiene piso en 0;
  - desaparece el límite de retirada;
  - `AuxiliaryState` rechaza un S negativo.
- **Qué permite y qué no:**
  - El betabloqueo atenúa la parte positiva; nunca convierte la retirada en negativa.
  - Una FC menor que la intrínseca exige una fuente explícita que cambie R, por ejemplo un evento o un fármaco
    cronotrópico negativo declarado.
- **Consecuencia que requiere decisión.**
  - Como la llegada está anclada, la frecuencia intrínseca efectiva es la FC de llegada.
  - Tras reanimar, la FC ya no baja de la llegada, aunque esa taquicardia fuera compensadora.
  - En el golden sólo cambia la FC: 16 corridas, con máximos de diferencia que suben de 12 a 29 lpm (manejo
    definitivo).
  - Falta decidir si un caso puede declarar qué parte de su FC de llegada es tono simpático. No se inventó ese
    valor.

### 10.4 D y lactato: monotonía comparativa (P2D-4)

Sólo pruebas comparativas, sin un número objetivo:
- Con trayectorias iguales en todo lo demás, más deuda nunca da menos lactato.
- Una deuda grave sostenida lleva el lactato sobre la llegada.
- Restaurar la entrega inicia el aclaramiento sin borrar el lactato.
- Una mejoría transitoria no borra la deuda previa.

Las cinéticas lineales de D y del lactato garantizan el orden punto a punto. τ y la ganancia siguen TBD.

### 10.5 La bomba da forma a la respuesta a precarga (P2D-5)

- La escala de la curva es `preload_curve_scale_ml × P^c` (c provisional = 1).
  - Se lee respecto del llenado de llegada sobre la curva de la bomba actual, así que P sigue significando el gasto
    al llenado de llegada.
  - La congestión lee la misma curva, y también mide ahí la llegada. Sólo congestiona la V agregada sobre la
    llegada: una bomba deprimida sin volumen agregado no congestiona por este acoplamiento. Si debe hacerlo, es una
    decisión pendiente (§10.11).
  - c se valida en [0, 1]: sólo ahí valen las garantías de esta sección, comprobadas con c = 0, 0,5 y 1.
- Gasto relativo con la llegada GI por defecto:

| P | V = 0 | +500 mL | +1000 mL | +3000 mL | Ganancia por 500 mL |
|---|---|---|---|---|---|
| 1,0 | 1,00 | 1,45 | 1,70 | 1,97 | 0,45 |
| 0,7 | 0,70 | 0,94 | 1,04 | 1,11 | 0,24 |
| 0,4 | 0,40 | 0,47 | 0,48 | 0,49 | 0,07 |

- Una bomba más débil:
  - da menos gasto a cualquier V;
  - nunca gana más por mL;
  - tiene techo más bajo y curva más plana.
- 500 mL no normalizan una bomba al 70 %; ningún volumen dentro de las cotas normaliza una al 40 %.
- La magnitud del acoplamiento sigue TBD.

### 10.6 El agua pulmonar se aclara (P2D-6)

- **Mecanismo.**
  - L sobre la llegada se aclara en primer orden (τ provisional = 240 min) con su propia fuente
    `core_coupling:lung_water_clearance`.
  - Nunca agrega L.
- **Comportamiento:**
  - sin fuente, no sube;
  - quitada la fuente, se recupera de forma monótona y lenta, sin bajar de la llegada;
  - con fuente que persiste, se mantiene o empeora;
  - con sobrecarga adicional, empeora.
- Los diuréticos y la VNI no se modelan aquí.

### 10.7 Sepsis y poscarga: diagnóstico, no corrección (P2D-7)

| Sonda | Gasto | PAM | DO2 | D | TLC |
|---|---|---|---|---|---|
| `vasodilation` (T a 0,6) | 1,00 → 1,14 | 90 → 80 | 1,00 → 1,14 | 0 → −3,8 | 2,0 → 1,5 |
| `vasodilation_with_preload_loss` (T a 0,6 y −200 mL) | 1,00 → 0,83 | 90 → 74 | 1,00 → 0,83 | 0 → +4,7 | 2,0 → 2,7 |

- **Clasificación:** PHYSIOLOGICALLY_PLAUSIBLE_PENDING_MULTI_FAMILY_CALIBRATION.
- **Qué muestra:**
  - El aumento de gasto por menor poscarga no normaliza la PAM.
  - Con pérdida de precarga, el gasto no sube: no es automático.
- **Brecha estructural, a decidir.** El oxígeno que se demanda y se extrae no tiene estado, así que D mide la entrega
  contra la de llegada y no contra la demanda. Con vasodilatación sola, la DO2 sube con el flujo y D cae por debajo
  de la llegada. No se forzó ningún cambio.

### 10.8 Procedencia de los parámetros de caso (P2D-8)

- **Declaración.** `Anchors.declared` nombra la fuente de cada parámetro declarado: `explicit_case` o
  `synthetic_probe`. Uno no declarado es `default`. Los parámetros son `beta_blockade`, `preload_fraction` y
  `pump_reserve`.
- **Sin inferencia silenciosa.** Un valor distinto del neutro sin fuente se rechaza. Un parámetro declarado debe
  tener valor, así que el valor por defecto del perfil nunca se atribuye al caso.
- **Registro.** `case_parameter_provenance` informa, por parámetro, el valor, la fuente, si está calibrado (siempre
  no) y una nota. Lo llevan el golden y la traza en sombra.
- **Regla por familia.** `legacy_adapter.FAMILY_CASE_PARAMETER_RULES` guarda la regla de cada familia.
  - `gi_bleed`: valores neutros, sin mapeo desde el banco y sin calibrar.
  - Una familia sin regla se rechaza antes de migrarla: necesita mapeo explícito por caso o una regla por familia
    aprobada.
- No se tocó `clinical_cases.py`. Las pruebas y las sondas declaran sus valores como `synthetic_probe`.

### 10.9 Clasificación causal del golden (P2D-9)

- **Las cifras numéricas del golden no cambian por la clasificación.** De todo P2D, sólo P2D-3 movió la FC (§10.3).
- **Clases:**
  - **MATCH**;
  - **APPROVED_DIRECTION_MAGNITUDE_TBD:** cada causa candidata tiene una dirección aprobada, y la magnitud no está
    aprobada hasta las bandas de Nivel 2 y las tolerancias A9;
  - **UNRESOLVED.**
- **Recuento:** 220 MATCH, 140 APPROVED_DIRECTION_MAGNITUDE_TBD y 0 UNRESOLVED.
- **Causas candidatas** (`candidate_causes`): los mecanismos decididos que están en la vía causal de la variable en
  esa corrida. Son candidatas, no una medida de cuánto aporta cada una.

  | Variables | Causas candidatas | Diferencias |
  |---|---|---|
  | PAS, PAD, PAM, TLC, V | KD-S4 | 79 |
  | Lactato y FR | KD-S1 + KD-S4 (KD-S4 a través del gasto y D) | 40 |
  | FC | KD-S2 + KD-S4 | 20 |
  | Conciencia | KD-S3 + KD-S4 | 1 |

**Conciencia en 57m sin tratamiento, minuto a minuto** (`shadow.consciousness_attribution`). Se usan dos lecturas
contrafactuales contra el nivel del motor heredado:
- **KD-S3 sola:** la presión del propio motor leída cruda.
- **KD-S4 sola:** la presión del núcleo leída en su valor mostrado.

| Minuto | PAS núcleo cruda / mostrada | PAS motor cruda / mostrada | Causas | Modo |
|---|---|---|---|---|
| 55 | 79,93 / 80 | 80,58 / 81 | KD-S3 + KD-S4 | ambas necesarias juntas |
| 56 | 79,77 / 80 | 80,44 / 80 | KD-S3 + KD-S4 | ambas necesarias juntas |
| 57 | 79,61 / 80 | 80,31 / 80 | KD-S3 + KD-S4 | ambas necesarias juntas |
| 58 | 79,45 / 79 | 80,17 / 80 | KD-S4 | suficiente sola |
| 59 | 79,29 / 79 | 80,04 / 80 | KD-S4 | suficiente sola |
| 60 | 79,13 / 79 | 79,90 / 80 | KD-S3 o KD-S4 | cada una suficiente |

- La PAS cruda del motor se reconstruye con su circulación y la relación adoptada. Redondea a lo que el motor
  muestra en cada minuto (prueba).
- Sólo se atribuye a la presión una diferencia que la presión explica: ambos motores leen el mismo nivel de
  oxígeno, y con la SpO2 del motor la PAS cruda del núcleo sigue dando otro nivel.
- Un minuto sin pulso, o uno que la presión no explica, queda sin causa. Entonces la variable es UNRESOLVED.
- Una diferencia que la corrida no esperaba nunca se aprueba por la atribución.
- La frase de §9.5 («minutos 55–57: el cruce viene de la lectura cruda») queda precisada así: en 55–57 hacen falta
  las dos cosas.

### 10.10 Parámetros que siguen TBD

Todos los de §9.4, menos `sympathetic_withdrawal_limit`, que se eliminó. Además:
- `pump_preload_coupling`: acoplamiento bomba/precarga, c = 1;
- `lung_water_clearance_tau_min`: τ de aclaramiento de L, 240 min;
- el umbral clínico de gasto y la permanencia antes del paro (P2D-2).

`OUTPUT_EPSILON` es una guarda numérica, no un parámetro clínico.

### 10.11 Limitaciones y decisiones pendientes

- **Tono simpático de llegada** (§10.3): qué parte de la FC de llegada es simpática, para que la taquicardia
  compensadora pueda resolverse por debajo de la llegada.
- **Paro:** el umbral de gasto y la permanencia (§10.2).
- **Demanda y extracción de oxígeno** en sepsis (§10.7).
- **Mapeo de los parámetros de caso** antes de migrar otra familia (§10.8).
- **Congestión por bomba deprimida sin volumen agregado:** si una bomba que falla debe congestionar por sí sola.
  Hoy no lo hace, para respetar la regla aprobada de «V adicional».
- **La clasificación:** sigue el mapeo de vías causales; el golden congela las magnitudes.
- Siguen vigentes las limitaciones de §9.8 que P2D no tocó:
  - pulso estrecho, que falla cerrado;
  - lactato bajo en shock profundo;
  - entradas simpáticas sin estado.

### 10.12 Revisión adversarial de P2D

Una revisión independiente, en sólo lectura, de `d543cd9..2d0f957` no encontró defectos altos. Confirmé cada hallazgo
con una sonda y lo corregí con una prueba que falla sin la corrección:
- **M1, congestión.** Una bomba deprimida (P ≤ 0,39) sin volumen agregado, o incluso sangrando, congestionaba: la
  llegada se medía en la curva de P = 1. Ahora se mide en la curva actual.
- **M2, atribución de conciencia.** Tenía tres fallas:
  - se rompía con un minuto sin pulso;
  - atribuía a la presión diferencias que podían venir del oxígeno;
  - podía aprobar una diferencia que la corrida no esperaba.

  Ahora no se rompe, exige el mismo nivel de oxígeno y no aprueba lo inesperado.
- **L1, acoplamiento.** Las garantías de la bomba fallaban con c > 1. Ahora c se valida en [0, 1] y se prueba en
  0, 0,5 y 1.
- **L2, procedencia.** Un `preload_fraction` declarado sin valor atribuía al caso el valor por defecto del perfil.
  Ahora se rechaza.
- **L3, reanudación.**
  - Se reanudaba en silencio un estado anterior a P2D-1: sin `aux`, o con memoria del núcleo en `internal`.
  - Un `aux` parcial se completaba con ceros.

  Ahora los tres se rechazan.
- **L4, texto.** Un docstring de la congestión estaba desactualizado; quedó corregido.
- **Fuera de P2D:** las sondas de Nivel 2 no se podían reproducir desde su especificación. `Drift` quedó registrado.

Las correcciones no cambian el golden. El golden por Contracts v2 sigue IDÉNTICO.

### 10.13 Gancho en tiempo de ejecución

No hay ninguno. Ningún módulo de la aplicación importa `clinical_core`: `test_shadow_core_isolation.py` lo comprueba.

## 11. P2E · Estados de referencia, demanda de oxígeno y colapso terminal (2026-10-22)

- Base: `7daf894` (P2D aceptado y cerrado).
- Commits:

  | Commit | Contenido |
  |---|---|
  | `1dad6df` | P2E-1 |
  | `2e71cc2` | P2E-2 |
  | `c91feb9` | P2E-3/4/5 |
  | `9b5ce58` | P2E-6/7 y documentación |
  | commit de §11.10 | correcciones de la revisión adversarial |

- Sigue todo en sombra y fuera de línea, sin gancho en tiempo de ejecución ni cambio visible para el residente.
- P2E es estructural. No fija ningún número de Nivel 2, no migra ninguna familia real y no ajusta nada para acercarse
  al motor heredado. Todo valor de las pruebas es una sonda sintética.

### 11.1 La FC de llegada no es la FC intrínseca (P2E-1)

- **Regla.** FC sinusal observada = frecuencia intrínseca de R + 25 × (1 − betabloqueo) × S, con S ≥ 0.
- **Declaración.**
  - El caso puede declarar `intrinsic_sinus_rate`.
  - `arrival_state` pone esa frecuencia en R y el impulso de llegada S0 = (FC − intrínseca) / (25 (1 − β)) en
    `aux.sympathetic_drive`, de modo que la FC derivada en la llegada es la del caso.
  - `heart_rate_decomposition` muestra por separado las dos partes y la fuente.
- **Objetivo del impulso.** Pasa a ser absoluto: S0 más las desviaciones de los estímulos desde la llegada, con piso
  en 0.
- **Comportamiento:**
  - la FC puede bajar de la llegada a medida que se resuelven los estímulos, pero no de la intrínseca;
  - sólo una fuente cronotrópica negativa explícita que cambie R la baja más;
  - el betabloqueo atenúa la ganancia, no la frecuencia intrínseca.
- **Validación.** Se rechazan:
  - una intrínseca sin llegada sinusal a la FC observada;
  - una intrínseca mayor que la FC observada;
  - una parte simpática con betabloqueo completo.
- **Fuentes.** `explicit_case`, `approved_family_default` (nueva), `default_unmapped` (antes `default`) y
  `synthetic_probe`.
- **Ejemplo sintético.** FC 124 con intrínseca 90: parte simpática 34 lpm, S0 = 1,36. Sin declarar, la intrínseca
  es 124 y S0 = 0.
- **El GI no infiere ninguna intrínseca.** Queda `default_unmapped` y sus cifras no cambian.

### 11.2 Demanda metabólica de oxígeno (P2E-2)

- **Estructura:**
  - entrega = f(gasto, Hb, SaO2), relativa a la de llegada;
  - demanda = basal del caso × factores declarados para el minuto;
  - déficit = max(0, demanda − entrega);
  - dD = déficit − D / τ_D.
- **Sin canal nuevo.** No hay C13. La demanda es entrada auxiliar tipada:
  - `aux.oxygen_demand`, con su fuente `core_coupling:oxygen_demand`;
  - cada factor es un `DemandModifier` (factor > 0, tipo `disease` o `transient`, fuente, minuto, descripción),
    registrado en el `MinuteRecord`;
  - el delta de D nombra en `modulated_by` las fuentes de los factores sólo cuando cambiaron su tamaño, es decir,
    cuando el déficit contra la demanda modificada difiere del déficit contra la basal del caso;
  - un contribuyente sólo declara factores a su nombre y para su minuto.
- **Sin crédito.** La entrega por encima de la demanda no repaga más de lo acumulado. D nunca baja de 0:
  - la cota inferior de D es 0 y queda registrada si actúa;
  - `CoreState` rechaza una D negativa y `AuxiliaryState`, un exceso de lactato negativo;
  - τ_D y τ del lactato son de al menos un minuto, el paso del integrador.
- **Referencias de llegada nuevas, declarables y neutras por defecto:**
  - `metabolic_demand_baseline` (1): por encima de 1, el paciente llega ya en déficit y D crece desde la llegada;
  - `arrival_lactate_excess` (0): la parte del lactato de llegada que puede aclararse. Sin declarar, el lactato no
    baja de la llegada.
- **No se migró la sepsis.** Los multiplicadores de sepsis, fiebre y convulsión siguen TBD. La sonda nueva usa un
  factor sintético de 1,3.

Respuesta de D a las sondas (llegada neutra sintética; τ_D provisional = 60 min):

| Sonda | D a 30 min | D a 60 min |
|---|---|---|
| Demanda × 0,8 o × 1,0, misma entrega | 0 | 0 |
| Demanda × 1,2, misma entrega | 4,75 | 7,62 |
| Demanda × 1,5, misma entrega | 11,88 | 19,06 |
| Demanda × 1,3; Hb +0 / +1 / +2 g/dL (entrega 1,00 / 1,08 / 1,15) | — | 11,43 / 8,53 / 5,63 |
| Demanda × 1,3 durante 30 min y luego basal | 7,13 | 4,31 (2,60 a 90 min) |

- `vasodilation_with_demand` (sepsis sintética): el gasto sube a 1,14 y aun así D llega a 7,61 a los 60 min; quitado
  el factor, D baja a 2,77 a los 120 min.
- `vasodilation` sola: D queda en 0, ya no por debajo de la llegada (§10.7).

### 11.3 Carga de colapso y transición terminal (P2E-3)

- **Estado.** `aux.collapse_burden` (≥ 0), con fuente `core_coupling:collapse`.
- **Acumulación.** Cada minuto se suma la fracción en que el gasto cae bajo el umbral declarado: 0 en el umbral, 1
  sin gasto. Más profundo o más largo acumula más.
- **Recuperación.** Con el gasto de nuevo en el umbral o por encima, la carga se mantiene, o se repaga en primer
  orden si se declara un τ.
- **Transición.** Cuando la carga alcanza el límite declarado, el núcleo mueve R a AESP o asistolia con una
  `RhythmTransition` y un evento `terminal_collapse` (crítico; prevenibilidad «not assessed»).
  - La AESP conserva el ritmo organizado: el monitor sigue contando la frecuencia que tenía, sin pulso.
  - Si un contribuyente mueve el ritmo en ese mismo minuto, la transición espera un minuto y parte del ritmo nuevo.
- **Apagada por defecto.** Umbral y límite valen `None` en el perfil. Sólo las pruebas usan valores sintéticos.
  - El umbral declarado debe quedar bajo el gasto de llegada (< 1), para que la llegada siga siendo un punto fijo.
  - Si el gasto llega a cero antes de cumplir el criterio, la corrida sigue deteniéndose en el límite de P2D-2.
  - No se agregó ningún evento terminal al GI.

Sondas con umbral sintético 0,4 y límite 10:

| Sonda | Carga máxima | Resultado |
|---|---|---|
| P a 0,35 durante 5 min | 0,63 | sin paro; la carga se mantiene |
| P a 0,3 / 0,2 durante 5 min | 1,25 / 2,50 | sin paro (más profundo, más carga) |
| P a 0,3 durante 4 / 8 min | 1,00 / 2,00 | sin paro (más largo, más carga) |
| P a 0,1 durante 8 min y recuperación | 6,0 | sin paro; con τ 30 min la carga baja a 1,1 a los 60 min |
| P a 0,1 sostenido | 10,5 | AESP en el minuto 15, a 104,7 lpm; nada medible después |

### 11.4 Presión con gasto bajo (P2E-4)

- **Por encima de la rodilla** (`low_output_pressure_knee`, provisional 0,5 de `pressure_rel`): la relación lineal
  adoptada, sin cambios.
- **Por debajo:** PAS y PAD son los valores de la rodilla × `pressure_rel` / rodilla. Es decir, presión proporcional
  a flujo × resistencia.
- **Qué garantiza:**
  - continuidad;
  - monotonía con el gasto;
  - cero sin gasto, sin piso heredado;
  - PAS ≥ PAD bajo la rodilla, siempre que se cumpla en la rodilla.
- **Pulso estrecho.** Una presión de pulso de llegada menor que (45 − 25) × (1 − rodilla), 10 mmHg con los valores
  por defecto, todavía llega a PAS < PAD sobre la rodilla. Pasaba igual antes de P2E, y el minuto falla cerrado
  (§9.8).
- **Presión no es perfusión.** El tono sigue sosteniendo PAD y PAM, mientras que gasto, entrega, D y TLC leen el
  gasto.
- **Primera versión descartada.** Igualar la pendiente de la PAM en la rodilla dejaba unos 60 mmHg de PAS con el
  5 % del gasto, así que se descartó.

| `pressure_rel` | 1,0 | 0,8 | 0,5 | 0,3 | 0,1 | 0,05 | 0 |
|---|---|---|---|---|---|---|---|
| PAS/PAD antes | 120/75 | 111/70 | 97,5/62,5 | 88,5/57,5 | 79,5/52,5 | 77,2/51,2 | 75/50 |
| PAS/PAD ahora | 120/75 | 111/70 | 97,5/62,5 | 58,5/37,5 | 19,5/12,5 | 9,8/6,2 | 0/0 |

- El golden no baja nunca de 0,80, así que sus presiones no cambian (prueba).
- Cambia una sonda de Nivel 2: `preload_dependent`, minuto 1, con gasto 0,19. Su PAM pasa de 64 a 28.

### 11.5 Falla de bomba y congestión (P2E-5)

- **Sin código nuevo.** Se conserva la regla de P2D de «V agregada». Las pruebas nuevas son:
  - P baja con V baja no crea L;
  - la misma precarga agregada (+1500 mL) congestiona más con menos reserva: L a 60 min de 0 / 0,47 / 0,82 con
    reserva 1,0 / 0,6 / 0,3;
  - una bomba que falla tolera menos precarga agregada: con reserva 0,5, la congestión empieza con +1003 mL si
    P = 1,0 y con +529 mL si P = 0,7;
  - las fuentes de L se distinguen por procedencia: una fuga capilar declarada (módulo de enfermedad), la congestión
    por precarga y el aclaramiento suman exactamente la L final.
- **Pruebas que ya cubrían el resto:** aclaramiento lento al quitar la fuente (§10.6) y ausencia de congestión de una
  bomba deprimida sin volumen (§10.12, M1).

### 11.6 Puerta de migración de parámetros de caso (P2E-6)

- **Módulo.** `clinical_core/migration.py`. `FAMILY_GATES` dice qué declara cada familia antes de migrar.
- **`gi_bleed` exige:**
  - los seis parámetros de caso: betabloqueo, `preload_fraction`, reserva de bomba, frecuencia intrínseca, demanda
    basal y lactato aclarable;
  - los cuatro de su fuente: pérdida de volumen y de Hb por minuto, fracción con IBP y tras hemostasia.
- **Cierre por defecto.** `check_migration_gate` lanza `MigrationBlocked` si un parámetro requerido:
  - es `default_unmapped`;
  - es `synthetic_probe`;
  - dice `approved_family_default` sin una entrada con ese valor en `APPROVED_FAMILY_DEFAULTS`, que hoy está vacío.

  El error nombra todos los que bloquean.
- **También se rechazan:** una familia sin puerta, un parámetro de familia desconocido y una fuente desconocida.
- **El golden informa la puerta por corrida.** Las 20 corridas GI están bloqueadas en los 10 parámetros: el GI es una
  línea base en sombra, no una migración.
- No se tocó el banco de casos. El mapeo de la próxima familia es otro paquete.

### 11.7 Golden antes y después (P2E-7)

- **Clases sin cambios:** 220 MATCH, 140 APPROVED_DIRECTION_MAGNITUDE_TBD y 0 UNRESOLVED.
- **Golden por Contracts v2:** IDÉNTICO.
- **P2E-2 como causa candidata.** Es un mecanismo que depende de la corrida (`shadow.RUN_DEPENDENT`): figura como
  causa candidata de lactato, FR y FC sólo en las corridas donde algún minuto entregó más que su demanda, que son 15
  de 20 (`acting_mechanisms` por corrida).
- **Causas:**

  | Causas candidatas | Diferencias |
  |---|---|
  | KD-S4 | 79 |
  | KD-S1 + KD-S4 + P2E-2 | 30 |
  | KD-S1 + KD-S4 | 10 |
  | KD-S2 + KD-S4 + P2E-2 | 15 |
  | KD-S2 + KD-S4 | 5 |
  | KD-S3 + KD-S4 | 1 |

- **Qué cambió por paquete:**
  - P2E-1, P2E-3, P2E-4 y P2E-6: sólo etiquetas (procedencia de parámetros, parámetros nuevos y la puerta). Ningún
    valor de trayectoria.
  - P2E-2: los cambios de la tabla siguiente.

**Mecanismo.** En cada una de esas corridas la entrega subió sobre la llegada (sangre, volumen u oxígeno):
- **Antes:** D se volvía negativa, el exceso de lactato también, y el lactato y la FR bajaban de la llegada.
- **Ahora:** D tiene piso en 0 y no hay lactato aclarable declarado, así que el lactato vuelve a la llegada y no
  baja de ella, y la FR lo sigue.
- **Motor heredado:** baja el lactato bajo la llegada en cuanto mejora la circulación. La diferencia con él crece y
  se clasifica, no se corrige.

| Corrida | Lactato mostrado: minutos cambiados; último minuto antes → ahora (motor) | FR mostrada: minutos cambiados; último minuto antes → ahora (motor) |
|---|---|---|
| 57m `aggressive_volume` | 60 (31–90); 3,8 → 4,4 (3,1) | 45 (46–90); 23 → 26 (16) |
| 57m `definitive_management` | 81 (40–120); 3,8 → 4,4 (3,3) | 63 (58–120); 24 → 26 (18) |
| 57m `prbc_2u_over_60` | 50 (41–90); 4,1 → 4,4 (3,5) | 31 (60–90); 25 → 26 (19) |
| 57m `saline_then_blood` | 30 (91–120); 4,2 → 4,4 (3,4) | 13 (108–120); 25 → 26 (19) |
| 57m `untimed_shared_line` | 32 (59–90); 4,2 → 4,4 (3,2) | 10 (81–90); 25 → 26 (17) |
| 72f `aggressive_volume` | 60 (31–90); 2,7 → 3,4 (2,1) | 50 (41–90); 20 → 24 (14) |
| 72f `definitive_management` | 81 (40–120); 2,8 → 3,4 (2,3) | 69 (52–120); 21 → 24 (16) |
| 72f `prbc_2u_over_60` | 50 (41–90); 3,0 → 3,4 (2,5) | 38 (53–90); 22 → 24 (17) |
| 72f `saline_then_blood` | 29 (92–120); 3,2 → 3,4 (2,4) | 19 (102–120); 23 → 24 (17) |
| 72f `untimed_shared_line` | 32 (59–90); 3,2 → 3,4 (2,2) | 17 (74–90); 23 → 24 (15) |

- **FC, un minuto:** 72f `oxygen_non_rebreather`, minuto 19.
  - Pasa de 113 a 114; el motor muestra 113.
  - El oxígeno subió la entrega al principio. Sin crédito, D a los 19 min es 0,195 y no 0,063, así que el impulso
    pasa de 0,0592 a 0,0603 y la FC cruda cruza el redondeo: 113,48 → 113,51.
  - La FC de esa corrida pasa de 1 a 2 minutos distintos del motor y sigue en APPROVED_DIRECTION_MAGNITUDE_TBD.
- **Sólo D, sin valor mostrado distinto** (D no se compara con el motor): 57m `oxygen_non_rebreather`,
  `saline_2l_over_20` y `stop_fluids`, y 72f `saline_2l_over_20`.
- **Sin ningún cambio:** `untreated_60` y `queued_timed_bags` de ambas variantes, y 72f `stop_fluids`.

### 11.8 Parámetros que siguen TBD

Todos los de §10.10, y además:
- frecuencia intrínseca por defecto y fracción simpática de llegada;
- demanda basal, multiplicadores de sepsis, fiebre y convulsión, y la normalización de la entrega;
- lactato aclarable de llegada;
- umbral de gasto del colapso, límite y permanencia, repago de la carga, y la regla de selección del ritmo
  terminal;
- rodilla y forma de la presión con gasto bajo;
- todas las tolerancias A9.

### 11.9 Limitaciones y decisiones pendientes

- **Respuesta a §10.11.** P2E deja estructura para los cuatro primeros puntos: tono simpático de llegada, paro,
  demanda y mapeo. No pone ningún número.
- **Consecuencia en el GI sin mapear.** Con lactato aclarable `default_unmapped`, el lactato no baja de la llegada al
  reanimar. Para que baje hay que declarar el lactato aclarable de la familia, una decisión clínica.
- **Llegada en déficit.** Una demanda basal > 1 hace que D crezca desde la llegada. Pero D y el lactato no empiezan
  en un estado estacionario coherente con ese déficit: falta decidir si la llegada debe declararlo.
- **Normalización.** Umbral de colapso, demanda y entrega se leen relativos a la llegada, y su normalización es TBD.
  Un paciente que llega en shock tiene gasto relativo 1 en la llegada.
- **Gasto cero antes del criterio.** Detiene la corrida (P2D-2), aun con la regla de colapso declarada.
- **Ritmo terminal.** Es un parámetro del perfil, `pea` o `asystole`, no una regla de selección.
- **Estados guardados de P2D.** Un estado serializado sin los campos auxiliares nuevos se rechaza al reanudarlo
  (falla cerrada).
- **Llegada con referencias declaradas.** Se construye sólo con `arrival_state(anchors, profile)`:
  - `initial_state` la rechaza;
  - `run(initial=...)` rechaza un estado de minuto 0 distinto de esa llegada.

### 11.10 Revisión adversarial de P2E

Una revisión independiente, en sólo lectura, de `7daf894..9b5ce58` encontró 2 hallazgos medios y 5 bajos. Confirmé
cada uno con una sonda propia y lo corregí con una prueba que lo cubre:
- **Medio, llegada.** `initial_state`, y un estado de minuto 0 reanudado sin `aux`, arrancaban en los valores
  anclados aunque el caso declarara referencias. Con una intrínseca de 90 la FC saltaba de 124 a 158. Ahora
  `initial_state` rechaza esos casos y `run(initial=...)` exige que un minuto 0 sea `arrival_state`.
- **Medio, puerta.** Un parámetro de familia `explicit_case` sin valor, con NaN o con texto pasaba la puerta, y una
  entrada que no era una tupla rompía con `TypeError`. Ahora se exige una tupla (valor finito, fuente) y, si no, se
  lanza `MigrationBlocked`.
- **Bajo, texto.** La garantía PAS ≥ PAD era falsa con pulso estrecho. Se corrigió el texto (§11.4); el
  comportamiento es el de antes.
- **Bajo, umbral.** Un umbral de colapso ≥ 1 paraba a un paciente sin cambios. Ahora se rechaza.
- **Bajo, signos.** Con τ < 1 minuto, Euler explícito volvía negativo el exceso de lactato; además, se podía
  reanudar con D negativa. Ahora hay invariantes de signo y τ ≥ 1.
- **Bajo, demanda mal formada.** Una demanda que no fuera una tupla de `DemandModifier` daba `AttributeError`. Ahora
  da `ProvenanceError`.
- **Bajo, procedencia.** `modulated_by` nombraba factores que no habían cambiado D. Ahora sólo nombra los que la
  cambiaron.

Las correcciones no cambian el golden. El golden por Contracts v2 sigue IDÉNTICO.

### 11.11 Gancho en tiempo de ejecución

No hay ninguno. Ningún módulo de la aplicación importa `clinical_core`, incluido `clinical_core.migration`:
`test_shadow_core_isolation.py` lo comprueba.
