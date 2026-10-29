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
- **Sustituido en P2H-0 (§14).** La puerta ya no confía en la etiqueta: `explicit_case` exige que un mapeo registrado
  confirme el valor desde la verdad del caso, y `APPROVED_FAMILY_DEFAULTS` pasó a `clinical_core/migration_authority.py`.

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

## 12. P2F · Marco de calibración de Nivel 2 y estados de referencia GI (2026-10-23)

- Base: `f008951` (P2E aceptado y cerrado).
- Sigue todo en sombra y fuera de línea, sin gancho en tiempo de ejecución ni cambio visible para el residente.
- Lo que P2F no hace:
  - no migra el GI ni otra familia;
  - no aprueba ningún número;
  - no elige un conjunto de parámetros;
  - no optimiza contra el motor heredado.

### 12.1 Tres capas de llegada (P2F-1)

`state.ARRIVAL_LAYERS` asigna cada campo de `Anchors` a una sola capa. `derived.arrival_layers` las informa por
separado.

| Capa | Qué es | Campos |
|---|---|---|
| **A. Observación de llegada** | Lo que ve el residente en t = 0 | PAS, PAD, FC, SpO2, FR, TLC, lactato, Hb, glucosa, K, FiO2, ritmo, conciencia |
| **B. Referencia fisiológica** | La normalidad no aguda del paciente | frecuencia sinusal intrínseca, demanda basal, posición euvolémica, betabloqueo, reserva de bomba |
| **C. Estado dinámico de llegada** | La fisiología aguda ya presente | posición en la curva de precarga, D de llegada, lactato aclarable, razón de entrega de llegada (y, derivados, el impulso simpático y el déficit de volumen) |

- La observación de llegada nunca se lee como normalidad.
- `check_arrival_reconstruction` prueba que, declare lo que declare B o C, la llegada derivada reproduce
  exactamente lo que el caso autoriza.
- Ninguna capa es un canal nuevo.
- Parámetros nuevos, neutros y `default_unmapped` en el golden GI:
  - `arrival_oxygen_debt`: el valor de llegada de D. D ya no está forzada a 0.
  - `arrival_delivery_ratio`: la entrega efectiva de llegada en unidades de la entrega que cubre la demanda de
    referencia. Un déficit en curso se expresa por la entrega, no por la demanda.
  - `reference_preload_fraction`: la referencia euvolémica. Hace explícito el déficit de volumen; ningún mecanismo la
    lee.
- **El término de D del impulso simpático lee D por encima de su valor de llegada.** Así, una deuda de llegada ya está
  en el impulso de llegada, y repagarla baja la FC hacia la intrínseca.
- **La llegada no tiene que estar en estado estacionario.**
  - La consistencia de estado estacionario es una propiedad opcional de una sonda sintética de equilibrio.
  - La consistencia del estado de llegada es lo exigido en los casos reales:
    - signos y combinaciones posibles;
    - reconstrucción exacta de la observación;
    - respuesta coherente después.

### 12.2 Verdad del repositorio GI (P2F-2)

- **Inventario.** `gi_reference.INVENTORY` tiene 58 entradas, 29 por caso. Cada una lleva valor, línea exacta, un
  fragmento que debe estar en esa línea y el parámetro que restringe. Una prueba verifica las líneas y los valores
  contra el banco.
- **Lo que los casos no dicen** (no se infiere):
  - terapia previa a la llegada;
  - duración de la hipoperfusión;
  - frecuencia basal;
  - que no tomen betabloqueadores (sólo que no figuran);
  - potasio (es el valor por defecto del banco, 4,1; `clinical_cases.py:297`);
  - puntaje de dolor (2/10 es el valor por defecto de la familia; `analgesia.py:22`);
  - estado mental (`Alert` es el valor por defecto de `_observable`; `clinical_cases.py:202`).

| Dato | 57m (fuente) | 72f (fuente) | Restringe |
|---|---|---|---|
| FC, ritmo | 124, taquicardia sinusal (`:881`, `:211`) | 112 (`:910`) | techo de la intrínseca; parte simpática |
| PAS/PAD (PAM derivada) | 88/54 (65,3) (`:881`) | 98/62 (74,0) (`:910`) | anclas de presión; presión de pulso 34/36 |
| SpO2, FR | 97, 26 (`:881`) | 96, 24 (`:910`) | sin impulso hipoxémico; parte metabólica de la FR |
| Gasometría arterial | pH 7,37, PaCO2 31, PaO2 91 (`:901`); HCO3 17,3 calculado por el banco (`:251`) | 7,40, 33, 84 (`:930`); HCO3 19,8 calculado | inferencia candidata: acidosis metabólica compensada |
| TLC, perfusión | 5 s, frías, alterada (`:881-882`) | 4 s, frías, alterada (`:910-911`) | inferencia candidata: entrega de llegada baja |
| Hb, lactato | 6,7; 4,4 (`:900`) | 6,4; 3,4 (`:929`) | entrega; la suma de la basal y el lactato aclarable (no su reparto, ni la ganancia D → lactato, ni la D de llegada) |
| Temperatura, leucocitos, dolor | 36,5; 11,1; leve | 36,6; 10,3; leve | sin modificador de demanda |
| POCUS | VI pequeño hiperdinámico, VCI 0,9 cm (`:154-155`) | hiperdinámico, VCI 1,1 cm (`:156`) | inferencia candidata: precarga baja; reserva |
| Pulmón, troponina | radiografía sin edema y troponina 16 (`:903`); «sin líneas B» es el valor por defecto de `_pocus` (`:69`, `:83`), que el caso no cambia | radiografía y troponina 17 (`:932`); ídem | inferencia candidata: sin congestión ni lesión |
| Sangrado activo | melena desde ayer (`:890`) | tres días y hoy (`:921`) | fuente; duración no dicha |
| Medicación | ibuprofeno (`:889`) | naproxeno (`:918`) | betabloqueo |

### 12.3 Bandas candidatas por caso (P2F-3/4/5)

Todas las bandas son CANDIDATE (`gi_reference.case_bands`). Cada una tiene su propia justificación; ninguna se
deriva de una historia previa ni de las cinéticas.

| Banda | 57m | 72f | Justificación |
|---|---|---|---|
| Lactato aclarable (mmol/L) | 2,4 – 3,4 – 3,6 | 1,4 – 2,4 – 2,6 | lactato de llegada menos una basal no shock de 0,8–2,0 |
| D de llegada (índice-min) | 0 – 20 – 60 | 0 – 20 – 60 | escala de la variable; ninguno dice la duración. Corregido tras la revisión (los valores no cambian): la derivación escrita antes (déficit 0,5 durante unas dos horas con τ_D 60) da ≈ 26, no 60; 60 es el estacionario de un déficit total con τ_D 60, y con τ_D 30 ningún déficit sostiene más de 30 |
| Razón de entrega de llegada | 0,6 – 0,85 – 1,0 | 0,6 – 0,85 – 1,0 | perfusión alterada, hipotensión y anemia grave: igual o bajo la adecuación |
| Frecuencia intrínseca (lpm) | 60 – 80 – 100 | 60 – 80 – 100 | frecuencia de reposo no aguda (no la intrínseca farmacológica bajo bloqueo autonómico, que es mayor) |
| Impulso simpático de llegada | 0,96 – 1,76 – 2,56 (24–64 lpm) | 0,48 – 1,28 – 2,08 (12–52 lpm) | FC observada menos la intrínseca; nunca negativo |
| Demanda basal | 1 | 1 | hemorragia no complicada: afebril, alerta, dolor leve; el caso no respalda ningún modificador |
| Posición de precarga | 0,2 – 0,35 – 0,5 | 0,3 – 0,45 – 0,6 | POCUS |
| Reserva de bomba | 0,7 – 1,0 | 0,7 – 1,0 | sin evidencia de reserva reducida; la edad no se usa para inferirla |
| Posición euvolémica (diagnóstica) | 0,6 – 0,7 – 0,8 | ídem | ningún caso la dice; ningún mecanismo la lee |

- **La demanda no es un parámetro libre.** El caso no respalda ningún modificador de demanda, así que no hay ninguno.
- **Separación por caso** (`gi_reference.reference_mapping`):
  - A: verdad del repositorio;
  - B: inferencia candidata;
  - C: decisión docente.
- **Siguen como candidato o decisión docente**, aunque se puedan calcular a partir de otros candidatos:
  - la frecuencia intrínseca;
  - el impulso simpático de llegada;
  - la D de llegada;
  - el lactato aclarable;
  - la demanda basal.
- **Historias previas a la llegada.** Se reconstruyen sólo como `SYNTHETIC_PLAUSIBILITY_PROBE`
  (`pre_arrival_plausibility_probe`).
  - No son entrada de migración, ni verdad del caso, ni procedencia, ni evidencia de calibración.
  - Ninguna banda ni regla de aceptación se deriva de ellas.
  - La simulación empieza en la llegada autorizada.

### 12.4 Modelo de entrega de O2 (P2F-6)

- **La entrega es relativa y adimensional:** entrega = (Q/Q_llegada) × (Hb/Hb_llegada) × (SpO2/SpO2_llegada), por la
  razón de entrega de llegada. Así queda en unidades de la entrega que cubre la demanda de referencia.
- **No es un DO2 físico indexado.** No se mezclan las dos lecturas.
- Sondas a demanda fija (`calibration.delivery_probes`):

| Sonda | Entrega | Déficit con demanda 1 | Déficit con demanda 1,2 | D a 60 min |
|---|---|---|---|---|
| Gasto bajo aislado (0,6) | 0,60 | 0,40 | 0,60 | 15,2 |
| Anemia aislada (0,6) | 0,60 | 0,40 | 0,60 | 15,2 |
| Hipoxemia aislada (SpO2 × 0,85) | 0,85 | 0,15 | 0,35 | 5,7 |
| Gasto bajo + anemia | 0,36 | 0,64 | 0,84 | 24,3 |
| Anemia + hipoxemia | 0,51 | 0,49 | 0,69 | 18,6 |
| Las tres | 0,31 | 0,69 | 0,89 | 26,3 |

- Cada factor baja la entrega; combinados, se multiplican. A igual entrega, más demanda da más déficit.
- **Brecha.** En una corrida, la SpO2 sólo cambia con la FiO2 (G, L y W todavía no la alimentan).
  - La hipoxemia aislada se prueba perdiendo el oxígeno de una llegada con FiO2 0,4: la SpO2 baja de 97 a 91,3 y la
    entrega a 0,94.

### 12.5 Registro de bandas de Nivel 2 (P2F-7)

- **Qué es.** `calibration.REGISTRY` tiene 53 entradas. Cada una lleva:
  - grupo y destino (perfil, caso o familia);
  - banda (inferior – punto medio – superior) u opciones;
  - unidades, justificación y evidencia;
  - mecanismos afectados y restricciones;
  - estado y valor canónico.
- **Estados:**
  - **CANDIDATE:** 47 entradas.
  - **DEFAULT_UNMAPPED:** 4, los multiplicadores de demanda de sepsis, fiebre, convulsión y agitación o dolor (sin
    banda).
  - **SYNTHETIC_ONLY:** 2, los valores de colapso de las pruebas P2E-3 y el factor 1,3 de la sonda de demanda.
  - **FACULTY_APPROVED:** 0. Ningún número tiene una aprobación docente explícita previa. Los literales adoptados del
    motor heredado son CANDIDATE.
- **Banda de la ganancia D → lactato** (2 – 6 – 12). Se lee como el exceso estacionario por unidad de déficit
  sostenido: un déficit de 0,5 queda 1–6 mmol/L sobre la basal.
  - No se infirió del lactato de llegada GI.
  - Un borrador previo citaba esa factibilidad; se quitó con la corrección metodológica. Los límites no cambiaron.

### 12.6 Reglas de aceptación congeladas (antes del barrido final)

- `calibration.FROZEN_RULES`, con el digest `c7b2f4bb…d83a5634`. Cubre:
  - la tabla de reglas;
  - el código de cada prueba y de cada auxiliar que usa;
  - los grupos y los puntos de cada banda del registro;
  - las bandas de cada caso GI y la llegada de las sondas;
  - los escenarios GI y el código que convierte sus órdenes en entradas del núcleo. El motor de familias que ejecuta
    esas órdenes lo fija la prueba del golden, no el digest.
  - El primer congelamiento (digest `594e895d…c551320`, `b4040ba`) cubría sólo la tabla y el código de las pruebas.
    La revisión adversarial lo encontró incompleto y halló dos defectos de implementación (abajo).
- Quedaron congeladas y comprometidas antes de cada barrido final.
- Los tamaños de las sondas son operacionalizaciones candidatas de direcciones aprobadas, no números aprobados.
- Ninguna regla se eligió, mantuvo ni endureció por la cantidad de candidatos que deja pasar.

| Regla | Qué exige | Fuente | Sonda |
|---|---|---|---|
| DL1 | Un déficit sostenido peor nunca da menos D | KD-S1, P2D-4, P2E-2 | demanda × 1,1 / 1,3 / 1,5 durante 120 min, a igual entrega |
| DL2 | … ni menos exceso de lactato | KD-S1, P2D-4 | las mismas corridas |
| DL3 | La recuperación es gradual | KD-S1 | demanda × 1,3 durante 60 min y luego nada: D baja cada minuto; el lactato, desde su pico; ninguno se reduce a la mitad en 10 min, y ambos bajan en 4 h |
| DL4 | Nada negativo: D, exceso, lactato | P2E-2 | todas las corridas |
| RR1 | Corregir el shock no crea bradipnea patológica | KD-S1 | lactato aclarable, 40 min de pérdida y corrección 580 mL sobre la llegada: FR ≥ min(FR de llegada, 10) |
| HR1 | El deterioro puede subir la FC | KD-S2 | la llegada declarada completa de cada caso GI (la del candidato), pérdida de 8 mL/min durante 30 min |
| HR2 | La recuperación puede bajarla hacia la intrínseca | P2E-1 | la misma pérdida, luego 400 mL sobre la llegada: la FC termina bajo la de llegada |
| HR3 | Sin impulso simpático negativo | P2D-3 | todas las corridas de FC |
| HR4 | FC bajo la intrínseca sólo con un mecanismo explícito | P2E-1 | ídem: FC ≥ intrínseca |
| PL1 | Rendimiento decreciente de la precarga | KD-S4 | +250 / +500 / +750 mL |
| PL2 | Una bomba deprimida limita el rescate con volumen | P2D-5 | P 0,6: 500 mL no ganan más que con P 1 ni restauran el gasto de llegada |
| PL3 | Una bomba muy deprimida no se normaliza con poco volumen | P2D-5 | P 0,4 + 250 mL: gasto < 0,8 |
| PL4 | El exceso de precarga puede producir L con reserva limitada | KD-S4 | reserva 0,3, +2,9 L: L > 0 en 60 min |
| PR1 | La presión baja monótonamente con el gasto a tono fijo | P2E-4 | `pressure_rel` 1,3 → 0, llegadas neutra y GI |
| PR2 | La presión tiende a 0 con el gasto | P2E-4 | a 1e-6, ambas < 1 mmHg |
| PR3 | PAS nunca bajo PAD en el rango | §11.4 | ídem |
| CO1 | Un flujo bajo breve y moderado no tiene por qué parar | P2E-3 | 5 min al 90 % del umbral de colapso |
| CO2 | Un flujo bajo grave y prolongado puede llegar a la transición terminal | P2E-3 | gasto 0,1 durante 240 min |
| DM1 | Más demanda a igual entrega empeora el déficit | P2E-2 | por el integrador: Hb −30 %, demanda × 1 y × 1,2 durante 60 min; misma entrega, D nunca menor y al final mayor |
| AC1 | La llegada declarada reconstruye exactamente la observación | P2F-1 | ambas llegadas GI |
| AC2 | La llegada GI declarada responde coherentemente | P2F-1, P2E-2 | sin tratamiento y con manejo definitivo, minuto 60: el tratamiento nunca deja D ni lactato sobre la corrida sin tratamiento; nada negativo; FC ≥ intrínseca |

**Cambios antes de congelar, y por qué:**
- **AR2 quitada como regla.** Exigía que existiera una historia previa que reprodujera el lactato de llegada. Se
  convirtió en `SYNTHETIC_PLAUSIBILITY_PROBE`. La razón es metodológica: D y el lactato de llegada se declaran
  precisamente para no reconstruir una trayectoria previa desconocida. En el barrido preliminar todos los rechazos GI
  eran AR2.
- **CO1.** Se probó cambiarla a 10 min al 75 % tras ver un barrido preliminar que no rechazaba nada. Se revirtió a la
  definición escrita antes de cualquier barrido (5 min al 90 %, como en las pruebas P2E-3), porque el cambio estaba
  motivado por el resultado.
- **Estado estacionario.** No es una regla.

**Garantizadas por construcción** (`Rule.guaranteed`). Pasarlas no distingue un candidato de otro:
- por la forma del modelo: DL1, DL2, DL4, RR1, HR3, HR4, PL1, PR1, PR2, DM1, AC1, y las partes de signo y de
  intrínseca de AC2;
- por las bandas: DL3 (toda constante de tiempo ≥ 30 min), CO1 (a lo sumo unos 6 min con severidad 0,1 y ganancia 2
  dan ≈ 1,2, bajo el límite mínimo de 5) y CO2 (240 × 0,5 × 0,5 = 60, sobre el límite máximo de 30).
- **No garantizadas:** HR1, HR2, PL2, PL3, PL4, PR3 y la comparación con tratamiento de AC2.

**Cambios tras la revisión adversarial, antes del segundo barrido final, y por qué.** Son defectos de implementación:
la sonda no medía lo que la regla escrita decía. Ninguno se decidió por cuántos candidatos pasan. Ninguna regla cambió
de enunciado.
- **HR1–HR4: arnés.** La regla dice «ambas llegadas GI», pero la sonda declaraba sólo la frecuencia intrínseca del
  candidato. La D de llegada, el lactato aclarable, la razón de entrega y la posición de precarga quedaban en sus
  valores por defecto.
  - Ahora corre sobre la llegada declarada completa de cada caso.
  - La clave de caché incluye todos los valores declarados de ambos casos.
  - Consecuencia, prevista antes de correr: con τ_D = 30, una D de llegada de 60 en 72f está por encima de la que
    cualquier déficit puede sostener, así que la parte de la deuda en el impulso cae durante el sangrado y la FC no
    sube. HR1 debe rechazar esos conjuntos.
- **DM1: sonda vacía.** Probaba sólo la aritmética de max(0, ·), sin leer el perfil del candidato, así que no podía
  rechazar nada. Ahora pasa por el integrador.
- **Digest incompleto.** Ahora cubre también los auxiliares, las bandas, el diseño y los escenarios (arriba).
  - Un primer re-congelamiento (`7e68f55`, digest `99265a6f…6155aab`) olvidó los escenarios GI que usa AC2. Se notó
    durante el barrido, que se detuvo sin mirar resultados (no llegó a escribir el informe). Se amplió el digest, se
    comprometió y se repitió el barrido desde cero. Ninguna regla ni prueba cambió.
- **`Rule.guaranteed`.** Se agregó para decir qué reglas no discriminan. No cambia la aceptación.
- **Textos sin efecto en la aceptación**, pero dentro del digest porque cambian las bandas de caso:
  - el razonamiento de la banda de D de llegada (§12.3);
  - notas y citas del inventario (§12.2).

### 12.7 Barrido final (desde cero, con las reglas congeladas)

- **Corrida.** `python3 -m clinical_core.calibration`, desde cero, sobre `98e76a7` (el código es el de `8054987`), con
  el digest `c7b2f4bb…d83a5634` de §12.6: 18 min 43 s.
- **Reemplaza al primer barrido final** (`b4040ba`, digest `594e895d…c551320`). Ese barrido aceptaba los 1217
  conjuntos GI porque HR1–HR4 no corrían sobre la llegada del candidato (§12.12, hallazgo 1). Sus números ya no
  valen; sólo se citan abajo para mostrar qué cambió.
- **Dimensiones.** Cada grupo recorre en factorial los puntos de su banda (inferior, medio y superior); los demás
  parámetros quedan en su valor canónico.
  - D/lactato: τ_D, ganancia déficit → D, ganancia D → lactato, τ del lactato.
  - FR: ganancia metabólica, máximo metabólico, piso ventilatorio, τ del lactato.
  - Simpático: ganancias de presión y de D, decaimiento.
  - Precarga: escala, posición por defecto, acoplamiento bomba/precarga, sensibilidad a la poscarga.
  - Congestión: escala, rodilla, ganancia, τ de L.
  - Presión: rodilla y las dos ganancias.
  - Colapso: umbral, ganancia, límite, repago y ritmo terminal.
  - Demanda: SpO2 por FiO2.
- **Diseño GI.**
  - Las 27 cinéticas, de τ_D × ganancia D → lactato × τ del lactato.
  - Por 9 combinaciones de lactato aclarable × frecuencia intrínseca.
  - Por 5 combinaciones de D de llegada × razón de entrega:
    - nada (0, 1);
    - medio (20, 0,85);
    - grave (60, 0,6);
    - y las dos esquinas mixtas.
  - Más 2 variantes de la posición de precarga.
- **Conjuntos evaluados:** 543 en los grupos y 1217 GI, en total 1760.

| Grupo | Evaluados | Rechazados | Motivo |
|---|---|---|---|
| D/lactato | 81 | 0 | |
| FR | 81 | 0 | |
| Simpático | 27 | 0 | |
| Precarga | 81 | 18 | PL2: con la posición por defecto en 0,3 y una escala de 600 u 833 mL (cualquier acoplamiento y poscarga), 500 mL devuelven el gasto de llegada a una bomba al 60 % |
| Congestión | 81 | 0 | |
| Presión | 27 | 0 | |
| Colapso | 162 | 0 | |
| Demanda | 3 | 0 | |
| GI (A) | 1217 | 163 | 162 por HR1 en 72f y 1 por un estado inválido en la sonda de HR (abajo) |

- **Los 162 rechazos por HR1** son exactamente los conjuntos con τ_D = 30 y D de llegada = 60, en sus dos esquinas de
  entrega (0,6 y 1,0): las 9 cinéticas con τ_D = 30, por las 9 combinaciones de lactato aclarable y frecuencia
  intrínseca, por 2.
  - Con τ_D = 30 ningún déficit sostiene una D de más de 30, así que la deuda se repaga incluso durante el sangrado.
    La parte de la deuda en el impulso, (D − D_llegada)/τ_D, se vuelve negativa y contrarresta la parte por presión:
    la FC baja mientras la PAS cae.
  - En 57m la misma combinación pasa HR1 (se prueba antes que 72f y no falla); no se analizó por qué.
  - Es la combinación inalcanzable que señala la banda corregida de la D de llegada (§12.3). Si una regla de
    alcanzabilidad (D ≤ g × demanda × τ_D) debe excluirla de antemano es una decisión docente; no se agregó.
- **El rechazo por estado inválido** es el conjunto con la posición de precarga en su límite inferior (0,2) en 57m.
  - En el minuto 24 de la sonda HR1 (8 mL/min) el gasto efectivo llega a 0 con pulso, sin una transición terminal
    declarada, y la corrida se detiene (invariante P2D-2).
  - A esa posición, con la escala por defecto, sólo unos 186 mL-eq la separan de un ventrículo vacío.
  - Si eso descalifica la posición o indica que la sonda es demasiado grande para esa llegada es una decisión docente.
- **Región aceptable:** todas las bandas, salvo:
  - la posición 0,3 con escala de 833 mL o menos (PL2);
  - τ_D = 30 con D de llegada = 60 (HR1, en 72f);
  - la posición de precarga 0,2 en 57m (estado inválido).
- **Lo que dice PL2.** Tal como está operacionalizada (en la posición de llegada), choca con la dependencia de
  precarga: en una curva empinada el volumen sí rescata una bomba moderadamente deprimida.
  - Si eso contradice la dirección aprobada en un paciente dependiente de precarga es una decisión docente.
  - No se cambió la regla.
- **Las restricciones cualitativas actuales discriminan poco.** En el GI pasan 1054 de 1217 conjuntos sin mirar el
  golden heredado.
  - Todos los rechazos vienen de una sola regla (HR1) en una sola esquina inalcanzable, más una llegada al borde del
    vaciamiento.
  - 15 de las 21 reglas están garantizadas, total o parcialmente, por construcción o por las bandas (§12.6).
  - Es un resultado, no un defecto que haya que tapar. Para estrechar las bandas hacen falta restricciones docentes
    nuevas (§12.11).

**B. Trayectorias GI.** Valor al final de la corrida, rango entre los 1054 conjuntos aceptables:

| Corrida | PAS | FC | FR | Lactato | TLC |
|---|---|---|---|---|---|
| 57m `untreated_60` | 71,5 – 79,1 | 127 – 139 | 13 – 36 | 1,8 – 9,6 | 5,8 – 6,5 |
| 57m `definitive_management` | 107 – 124 | 93 – 110 | 13 – 31 | 1,0 – 6,0 | 1,8 – 3,3 |
| 57m `aggressive_volume` | 121 – 149 | 80 – 103 | 13 – 32 | 1,3 – 6,8 | 0 – 2,1 |
| 72f `untreated_60` | 87,2 – 92,1 | 112 – 124 | 15 – 38 | 1,5 – 9,2 | 4,5 – 5,0 |
| 72f `definitive_management` | 111 – 122 | 88 – 101 | 15 – 33 | 1,0 – 5,8 | 1,9 – 2,9 |
| 72f `aggressive_volume` | 120 – 138 | 80 – 100 | 15 – 34 | 1,1 – 6,7 | 0,4 – 2,1 |

- **Cómo terminan las corridas.** Ninguna corrida de un conjunto aceptable se detuvo en un límite no resuelto, y todas
  terminan con pulso.
- **Lactato con manejo definitivo.** Termina bajo la llegada en 958 de 1054 conjuntos en 57m y en 889 en 72f. Los
  demás son los conjuntos con aclaramiento lento o con un déficit de llegada grave.
- **Qué cambió respecto del primer barrido.** Los extremos de entonces (una PAS de 28 a los 60 min sin tratamiento y
  una de 219 con volumen agresivo, en 57m) venían del conjunto con la precarga en 0,2, que ahora se rechaza. Ya no
  aparece una FC que baja durante la hemorragia en 72f: era la de los 162 conjuntos rechazados.
- **Bandas anchas.** La FR al final va de 13 a 38 y el lactato sin tratamiento de 1,5 a 9,6. Ninguna regla aprobada
  acota eso; queda para las restricciones docentes.

**C. Diferencia con el golden heredado** (diagnóstico). Minutos distintos sumados en las 20 corridas, rango entre los
conjuntos aceptables:

| Variable | Rango |
|---|---|
| PAS | 1123 – 1254 |
| PAD | 1025 – 1084 |
| PAM | 1064 – 1157 |
| FC | 1038 – 1384 |
| FR | 1139 – 1510 |
| Lactato | 1207 – 1510 |
| TLC | 974 – 1068 |
| Conciencia | 6 – 30 |
| V | 130 (no cambia) |

Ningún conjunto se eligió, ordenó ni descartó por esta diferencia. `calibration.acceptable` lee sólo A, y una prueba
lo comprueba alterando C.

**Diagnósticos (no se usan para aceptar), sobre los 1217 conjuntos:**
- La sonda `SYNTHETIC_PLAUSIBILITY_PROBE` encuentra alguna historia previa constante en 812 conjuntos para 57m y en
  947 para 72f. En los demás, ninguna. Eso no dice nada contra el conjunto: la llegada se declara.
- dD/dt en la llegada va de −2,0 a +0,4 por minuto, y sólo es 0 en los 486 casos sin deuda ni déficit de llegada. La
  llegada evoluciona; no se exige estado estacionario.

### 12.8 Marco del Apéndice A9 (P2F-10)

`clinical_core/a9.py` asigna a cada variable un tipo de comparación. Todas las tolerancias numéricas siguen TBD. El
estado interno oculto no se mide con la lógica de los observables mostrados.

| Variable | Visible | Tipo | Además | Por qué |
|---|---|---|---|---|
| PAS | sí | diferencia absoluta acotada | categoría clínica | los umbrales 90/80/65 condicionan la conciencia y la logística |
| PAD | sí | diferencia absoluta acotada | | |
| PAM | sí | diferencia absoluta acotada | categoría clínica | 65 mmHg es un objetivo |
| FC | sí | diferencia absoluta acotada | tendencia | el impulso tiene memoria |
| FR | sí | diferencia absoluta acotada | categoría clínica | bradipnea y taquipnea marcada |
| SpO2 | sí | diferencia absoluta acotada | categoría clínica | niveles 94/87/80 |
| TLC | sí | diferencia absoluta acotada | categoría clínica | > 3 s |
| Conciencia | sí | categoría clínica | | el mismo nivel minuto a minuto |
| Lactato | sí | diferencia relativa acotada | tendencia | relativa en valores altos; dirección del aclaramiento |
| Hb | sí | coincidencia exacta | | aritmética adoptada del motor |
| Momento de los eventos | sí | momento exacto | | endoscopia, transfusión, paro |
| Pulso o paro | sí | coincidencia exacta | | minuto a minuto |
| V | no | divergencia estructural aprobada | coincidencia exacta dentro de la pinza | KD-S4 |
| D | no | tendencia | | sin equivalente en el motor |
| L | no | tendencia | | sondas |
| Gasto efectivo | no | tendencia | | dirección de la circulación del motor |
| Demanda de O2 | no | coincidencia exacta | | contabilidad de lo declarado |
| Impulso simpático | no | tendencia | | sin equivalente |
| Carga de colapso | no | tendencia | momento exacto de la transición | |

### 12.9 Ensayo en seco de la puerta de migración GI (P2F-11)

`migration.gate_dry_run`: los dos casos fallan la puerta en sus 12 parámetros requeridos. Nada se migra, y ningún
candidato se convierte en mapeo.

| Categoría | Parámetros |
|---|---|
| A. Mapeable desde la verdad del caso | sólo las anclas de llegada que el caso escribe (PAS, PAD, FC, SpO2, FR, TLC, lactato, Hb, glucosa, conciencia). No lo son, y van aparte como valores por defecto: el K del banco (`clinical_cases.py:297`), el ritmo que el banco deriva de la FC (`:211`) y el aire ambiente con que el motor empieza (`family_engine.py:973`) |
| B. Requiere un valor por defecto de familia aprobado | betabloqueo, reserva de bomba, los cuatro parámetros de la fuente hemorrágica |
| C. Requiere decisión docente | frecuencia intrínseca, D de llegada y razón de entrega de llegada (declaradas directamente por docentes, sin reconstruir una historia previa), lactato aclarable, demanda basal, posición de precarga |
| D. No requerido para GI | posición euvolémica |

Bloquean la migración los 12 parámetros requeridos, todos `default_unmapped` en la línea base en sombra.

### 12.10 Seguridad del golden canónico (P2F-12)

- El golden canónico cambió sólo en etiquetas (los parámetros nuevos y su procedencia, y la lista de bloqueos de la
  puerta). Ninguna trayectoria cambió.
- La clasificación sigue en 220 MATCH, 140 APPROVED_DIRECTION_MAGNITUDE_TBD y 0 UNRESOLVED.
- El golden directo y el de Contracts v2 son IDÉNTICOS.
- Los barridos corren sobre copias. Una prueba comprueba que no cambian el perfil por defecto, las anclas canónicas
  ni el archivo del golden.

### 12.11 Limitaciones y decisiones pendientes

- **Restricciones docentes para estrechar las bandas.** Las reglas aprobadas son estructurales y casi no
  discriminan. Harían falta restricciones como:
  - tiempo y cuantía del aclaramiento de lactato tras el manejo definitivo;
  - FC esperada al reanimar;
  - descenso de la PAS sin tratamiento en una hora;
  - permanencia antes del paro;
  - techo de PAS con volumen agresivo.
- **PL2 en pacientes dependientes de precarga.** Hay que decidir si la regla vale ahí (§12.7).
- **Alcanzabilidad de la D de llegada.** Hay que decidir si se agrega una regla D ≤ g × demanda × τ_D. Excluiría de
  antemano la esquina que hoy rechaza HR1 (§12.3, §12.7). No se agregó, porque sería una regla posterior al barrido.
- **Precarga de llegada en 0,2 en 57m.** La sonda HR1 la vacía en 24 min. Hay que decidir si eso descalifica la
  posición o si la sonda es demasiado grande para esa llegada (§12.7).
- **Valores de llegada GI** (decisión docente):
  - frecuencia intrínseca;
  - impulso simpático;
  - D de llegada;
  - lactato aclarable;
  - razón de entrega;
  - posición de precarga;
  - demanda basal.
- **Valores por defecto de familia por aprobar:**
  - betabloqueo con medicación sin betabloqueador;
  - reserva normal sin hallazgos cardíacos;
  - los cuatro parámetros de la fuente hemorrágica.
- **Normalización.** Umbral de colapso, demanda y entrega siguen relativos a la llegada (§11.9).
- **SpO2 en una corrida.** Sólo responde a la FiO2.
- **Lactato sin techo.** Con parámetros extremos fuera de las bandas (D de llegada 1e4) llega a 127 mmol/L (§12.12).

### 12.12 Revisión adversarial de P2F

Revisión de sólo lectura de `f008951..768feb3`, con sondas propias. Cada hallazgo se confirmó con una sonda antes de
corregirlo.

| # | Gravedad | Hallazgo | Resolución |
|---|---|---|---|
| 1 | Alta | HR1–HR4 corrían sobre una llegada que sólo declaraba la frecuencia intrínseca, no la del candidato; la clave de caché tampoco distinguía las llegadas | Arnés corregido y prueba nueva; re-congelado y barrido repetido (§12.6, §12.7). La sonda de la revisión predijo 162 rechazos HR1 en 72f (τ_D 30 con D de llegada 60) y una parada en un límite no resuelto en 57m |
| 2 | Media | La historia previa reaparecía como vía de migración de la D y de la razón de entrega de llegada, y el lactato decía restringir la ganancia D → lactato y la D de llegada | Textos corregidos: ambas se declaran directamente; el lactato sólo fija la suma de basal y exceso aclarable |
| 3 | Media | El techo de 60 de la banda de D de llegada no salía de su justificación escrita (daba ≈ 26) | Justificación corregida; valores sin cambio porque se congelaron antes del barrido. Queda como decisión docente, con un posible límite de alcanzabilidad (D ≤ g × demanda × τ_D) |
| 4 | Media-baja | El digest no cubría auxiliares, datos ni escenarios | Ampliado en dos pasos (§12.6) |
| 5 | Baja | DM1 no leía el perfil; HR3, HR4, CO1 y partes de AC2 no pueden fallar | DM1 pasa por el integrador; `Rule.guaranteed` marca las que no discriminan |
| 6 | Baja | Notas de inferencia presentadas como verdad del caso; citas del HCO3 y de «sin líneas B»; FiO2 y ritmo clasificados como verdad del caso; «no cardiac history» | Notas marcadas como inferencia candidata, citas corregidas, FiO2 y ritmo con los valores por defecto, «the case mentions no cardiac disease» |

Lo que la revisión encontró correcto, y no cambió:
- el inventario (58 entradas, verificadas contra el banco) y el registro (53: 47 CANDIDATE, 4 DEFAULT_UNMAPPED,
  2 SYNTHETIC_ONLY, 0 FACULTY_APPROVED);
- los números del primer barrido, recalculados por la revisión;
- sin optimización contra el motor heredado: la aceptación lee sólo A y nunca la sonda de plausibilidad;
- los goldens (sólo etiquetas nuevas; `contracts_shadow` IDENTICAL);
- las anclas nuevas: rechazan negativos, NaN e infinitos, y el objeto en caché no se puede alterar;
- los invariantes con parámetros extremos, y el aislamiento.

Nota de la revisión que queda como limitación (§12.11): el lactato no tiene techo; con parámetros extremos (D de
llegada 1e4) llega a 127 mmol/L.

### 12.13 Gancho en tiempo de ejecución

No hay ninguno. Ningún módulo de la aplicación importa `clinical_core`, incluidos `gi_reference`, `calibration` y
`a9`: `test_shadow_core_isolation.py` lo comprueba.

## 13. P2G · Paquete de decisiones docentes de calibración (2026-10-23)

- **Base:** `83cee15` (P2F aceptado y cerrado).
- **Naturaleza:** análisis y apoyo a decisiones. Nada se aprueba, nada pasa a FACULTY_APPROVED, el GI no migra, no hay
  gancho en tiempo de ejecución y no cambia ningún valor por defecto canónico.
- **El paquete para la docencia** es `docs/revision/P2G_DECISIONES_DOCENTES_CALIBRACION_GI.md`, con sus números en
  `docs/revision/P2G_decision_pack.json`. Aquí sólo queda lo que cambia en el núcleo.

### 13.1 El congelamiento de calibración cubre las entradas (P2G-1)

`calibration.digest_components()` separa el congelamiento en componentes, y `frozen_digest()` es el digest de todos.
Una prueba registra cada componente, así que un cambio dice dónde está.

| Componente | Qué cubre | Por qué | Antes (P2F, `c7b2f4bb…`) |
|---|---|---|---|
| `rules` | la tabla de reglas, el registro de pruebas, los grupos y cada función del arnés que una prueba o la aceptación GI llama (incluidos `_legacy` y `_legacy_run`) | deciden la aceptación | igual, salvo `run_legacy` y `contributors_from_legacy`, que pasan al componente del adaptador |
| `bands` | los puntos de cada banda del registro, las bandas de caso GI, la llegada de las sondas y los niveles | definen el diseño | igual |
| `harness_sources` | los archivos completos del arnés: `clinical_core/calibration.py` y `clinical_core/bands.py` | `rules` no veía el enlace de cada prueba con su función, los valores por defecto del diseño (`GICandidate`) ni las sondas (`Drift`, `Demand`); la segunda revisión lo encontró | **no cubierto** |
| `gi_reference` | el archivo completo `clinical_core/gi_reference.py`: inventario, bandas y anclas candidatas | es el mapeo GI de referencia | sólo `candidate_anchors`, `case_bands` y sus datos |
| `scenarios` | las definiciones de los escenarios GI | son las órdenes que corren | igual |
| `input_path_sources` | los 35 archivos del repositorio fuera de `clinical_core/` que corren (se importan o se llaman) mientras el motor de familias arma las llegadas GI y corre cada escenario: el lector congelado (`family_parser.py`), el motor (`family_engine.py`), el banco (`clinical_cases.py`), el generador de encuentros y sus módulos | pueden cambiar las entradas heredadas | **no cubierto**: sólo lo fijaba la prueba del golden |
| `input_adapter_sources` | `clinical_core/legacy_adapter.py` y `clinical_core/interventions/timing.py` | convierten la corrida del motor en entradas del núcleo | sólo dos funciones del adaptador |
| `scenario_inputs` | las entradas materializadas: por caso, las anclas canónicas; por escenario, los contribuyentes, las órdenes ejecutadas y las instantáneas del motor | atrapa cualquier cambio que altere una entrada, incluida una constante del núcleo que lea el adaptador | **no cubierto** |

- **Cómo se obtuvo la lista** de `INPUT_PATH_SOURCES`: trazando en un intérprete limpio (`sys.settrace` y el
  `audithook` de apertura de archivos) la construcción de todas las entradas.
  - El camino no abre ningún archivo de datos aparte de los `.py`; el banco es Python.
  - No lee variables de entorno (búsqueda en los 35 archivos).
  - Una prueba repite la traza y exige que la lista sea exactamente la que corre, en los dos sentidos.
- **Qué queda fuera, y por qué:**
  - el resto del repositorio, porque no corre en ese camino;
  - los archivos del modelo del núcleo, porque son lo que la calibración evalúa. Los fijan las pruebas de Fase 2 y el
    golden, y el componente `scenario_inputs` atrapa cualquier efecto suyo sobre las entradas. El digest del paquete
    de decisiones (§13.2) sí los cubre.
- **Pruebas** (`test_clinical_core_calibration_freeze.py`). Cambiar cualquiera de estas cosas cambia exactamente el
  componente esperado:
  - `family_engine.py`, `family_parser.py` o `clinical_cases.py`;
  - el adaptador o `gi_reference.py`;
  - `calibration.py` o `bands.py` (componente `harness_sources`);
  - un escenario;
  - una constante que altera una entrada materializada.

  Además, un escenario cambiado nunca se sirve de una caché vieja (la clave es su contenido), y el digest se
  reproduce en un intérprete limpio.
- **Digest nuevo:** `a7436fe8…37d39`. El primer cierre de P2G registró `0db3403d…d65f9`, sin `harness_sources`.
- **Ninguna regla, prueba, banda ni función de aceptación cambió.** En el código del arnés cambian la clave de la
  caché de las corridas heredadas (ahora el contenido del escenario en vez de su nombre) y el componente
  `harness_sources`, que sólo agrega cobertura al digest. Para los
  escenarios sin cambios da las mismas entradas. Por eso no se repitió el barrido de P2F: sus resultados (§12.7)
  siguen valiendo, y la región admisible que usa P2G es la suya.

### 13.2 Generador del paquete (P2G-2 a P2G-11)

- **`clinical_core/decision_pack.py`** calcula, sobre la región admisible de P2F (los 1054 conjuntos), las
  trayectorias de las decisiones 1 a 6.
  - Lactato, FC, PA sin tratamiento, colapso sintético, volumen agresivo y FR.
  - Envolventes, representantes bajo / medio / alto y efectos de un factor por vez.
  - El análisis de PL2, el de la alcanzabilidad de la D de llegada y el borde de precarga 0,2.
- **`p2f_rejection`** escribe el resultado del barrido de P2F (163 rechazos). No es una regla nueva: las pruebas lo
  contrastan con la aceptación congelada en los dos tipos de rechazo y en conjuntos admisibles.
- **Nunca elige, ordena ni recomienda.** «Bajo», «medio» y «alto» son posiciones para una lectura concreta. Una prueba
  revisa que no haya claves de selección ni FACULTY_APPROVED en la salida.
- **`clinical_core/decision_pack_markdown.py`** sólo presenta: escribe las tablas del documento a partir del JSON.
  Una prueba falla si el documento, el JSON o el código del paquete no coinciden con el congelamiento vigente.
- **`pack_digest()`** suma al digest de calibración los escenarios de decisión y el hash de cada fuente de
  `clinical_core/**/*.py` (`pack_sources()`): el modelo, el arnés y el propio generador. Sólo excluye el renderizador,
  que no cambia ningún número. Una prueba cambia `derived.py`, `integration.py` y `decision_pack.py` y exige un digest
  distinto; cambiar el renderizador no lo cambia.
- **Corrida completa:** 4 min 52 s en el primer cierre; 5 min 24 s con las tablas y marcas agregadas tras la segunda revisión.
  Ninguna llamada de IA de la app.

### 13.3 Hallazgos del modelo que la docencia necesita

Son evidencia del modelo, no recomendaciones. El detalle está en el paquete.
- **Lactato:** en el centro de la región, una hora de sangrado sin tratar no lo sube: el exceso de llegada se aclara
  más rápido de lo que el déficit produce lactato nuevo. Sube en el 25 % (57m) y el 34 % (72f) de la región, más de
  1 mmol/L en el 10 % y el 12 %.
- **FC:** la frecuencia intrínseca no cambia la trayectoria mientras dura el estímulo; sólo fija el piso de la
  recuperación. Por eso la velocidad de resolución se lee como «mitad de la caída», que no depende de ella mientras
  el impulso no llegue a cero (con intrínseca 100 en 72f, sí: 21–33 min frente a 29–41).
- **PA sin tratamiento:** la empuja sólo la fuente de 2,5 mL/min. Bajo la rodilla de presión cae rápido, y con el
  colapso apagado la corrida se detiene (57m, minuto 144).
- **Volumen agresivo:** no hay techo de presión sobre la llegada. La escala de la curva decide cuándo el líquido deja
  de servir.
- **FR:** el reparto de la FR de llegada fija el piso de la recuperación (10,0–21,5 sobre la cuadrícula), y
  `rr_per_lactate` lo mueve más que `rr_ventilatory_floor`. El techo teórico es FR de llegada − impulso metabólico de
  llegada + `rr_metabolic_max`, recortado por `rr_max`.
- **PL2:** sólo falla su segunda cláusula, y nunca se prueba sobre las llegadas GI.
- **Alcanzabilidad:** es una propiedad del repago de primer orden del modelo, no una condición física.
- **Precarga 0,2:** el propio sangrado del caso vacía el ventrículo en 75 min. La falla es una interacción, no sólo
  la sonda.
- **Puerta de migración:** el GI sigue fallando en sus 12 parámetros; FACULTY_APPROVED sigue en 0.

### 13.4 Segunda revisión adversarial (sólo lectura) y correcciones

Revisó el arnés final, la cobertura de los digests, las tablas docentes y la puerta de migración. Sin hallazgos de
gravedad alta; cada hallazgo se confirmó con una sonda antes de corregirlo.

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| 1 | media | el congelamiento no veía el enlace de cada prueba con su función, los valores por defecto de `GICandidate` ni las sondas de `bands.py` | componente `harness_sources` (archivos completos) y dos pruebas de mutación (§13.1) |
| 2 | media | `pack_digest` no cubría el modelo del núcleo | `pack_sources()`: cada `clinical_core/**/*.py` salvo el renderizador, con prueba de mutación (§13.2) |
| 3 | media, anterior a P2G | la puerta acepta un CANDIDATE reetiquetado como `explicit_case` | sin cambio de arquitectura: prueba estática de que ningún módulo del núcleo, salvo el vocabulario de la puerta, escribe esas fuentes; límite explicado en el paquete (§14) y decisión FD-49 |
| 4 | media | la «mitad simpática» de la FC depende de la intrínseca y el texto la daba como general | cuadrícula τ simpático × intrínseca y una lectura que no depende de la intrínseca («mitad de la caída»); texto y FD-06 reescritos |
| 5 | media | la fórmula del techo de la FR y las cifras de FD-18 estaban mal | `rr_bounds()` lee techo y piso de `derived.respiratory_rate` sobre la cuadrícula de bandas de FR; texto, FD-18 y FD-19 desde esas cifras |
| 6 | media | la tabla maestra omitía parámetros CANDIDATE | FD-41 a FD-48, lista de los que quedan fuera con su motivo y prueba de completitud contra el registro |
| 7 | baja | afirmaciones del lactato sin cifra | proporciones generadas de la región admisible y texto ajustado a ellas |
| 8 | baja | «los parámetros de FR mueven ~1 resp/min» era falso | texto corregido con el efecto máximo de la tabla |
| 9 | baja | los minutos «exactos» del colapso usaban techo en coma flotante (16 celdas con un minuto de más) | aritmética entera exacta y explicación de los minutos que agrega la simulación |
| 10 | baja | la minitabla de §4 no daba el rango a los 30 min | rango agregado |
| 11 | baja | «admisible» era ambiguo en §6 (celdas fuera del diseño de P2F) | definición en «Cómo leer», columna «En el diseño de P2F» y frase del renderizador corregida |

- **Lo que la revisión confirmó:** `p2f_rejection` coincide con la aceptación congelada en los 1217 conjuntos; el
  manifiesto de entradas es exacto, sin dependencia del entorno y estable con `PYTHONHASHSEED`; las descomposiciones
  suman; el JSON coincide con un recálculo; la puerta falla con 12 bloqueos por caso; FACULTY_APPROVED sigue en 0.
- **Sin barrido de P2F nuevo:** ninguna regla, prueba, banda ni función de aceptación cambió. `harness_sources` sólo
  agrega cobertura al digest.

**Verificación independiente de las correcciones** (sólo lectura, después de la tabla anterior). Confirmó 1, 2, 5, 6,
7 y 10; dejó 3, 4, 9 y 11 parciales y 8 sin corregir, y halló nueve puntos nuevos. Todos se confirmaron con sonda y se
corrigieron:

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| N1 | media | la frase del efecto de los parámetros de FR seguía mal (`rr_per_lactate` llega a 5,2 en 72f) | rangos por parámetro leídos de las filas de efecto |
| N2 | baja | la explicación de los minutos que agrega la simulación del colapso era errónea | un minuto por la caída del gasto y uno más cuando la cuenta es entera (suma en coma flotante) |
| N3 | baja | «las tablas lo dicen» era falso para las filas de efecto, casi todas fuera del diseño de P2F | `in_p2f_design` generado en cada fila de efecto y mostrado en el estado; FD-14 separa dentro y fuera del diseño |
| N4 | baja | FD-06 y §13.3 generalizaban la «mitad de la caída»; «pesa menos que las ganancias» no tenía cifra | excepción de intrínseca 100 en 72f; comparación quitada |
| N5 | baja | la prueba estática citaba FD-41 y afirmaba más de lo que comprueba | FD-49, texto acotado y una segunda comprobación: sólo `state.py` y `migration.py` leen los conjuntos de etiquetas |
| N6 | media | el límite de la puerta era más amplio de lo descrito: reetiquetar todo como `explicit_case`, también los parámetros de familia, pasa la puerta completa | §14 y FD-49 lo dicen; la puerta no cambia (decisión de arquitectura) |
| N7 | baja | §13.1 decía que el único cambio del arnés era la clave de la caché; el tiempo de la corrida no estaba al día | texto y tiempo actualizados |
| N8 | baja | `pack_sources()` leía cualquier `.py` del árbol, también ocultos o no regulares | sólo archivos regulares y no ocultos, en el digest y en la prueba estática |
| N9 | baja | la tabla de proporciones del lactato salía en orden alfabético | orden fijo |

## 14. P2H-0 · Integridad de la procedencia en la puerta de migración (2026-10-23)

- **Base:** `a4f33f2` (P2G aceptado y cerrado).
- **Naturaleza:** corrección de arquitectura acotada antes de las decisiones numéricas. No cambia la fisiología, las
  bandas, las reglas, los escenarios ni los adaptadores; no aprueba valores; el GI no migra; no hay integración en
  tiempo de ejecución.

### 14.1 El defecto (FD-49)

La puerta confiaba en la etiqueta de fuente declarada. Una sonda sobre `a4f33f2` (anclas candidatas de 57m con todo
reetiquetado como `explicit_case`, también los 4 parámetros de la fuente hemorrágica) hacía pasar
`check_migration_gate` completa. Era un defecto de frontera de confianza: el objeto candidato se autorizaba a sí
mismo.

### 14.2 El modelo nuevo: valor, reclamación y autoridad separados

| Capa | Dónde vive | Confianza |
|---|---|---|
| Valor del parámetro | `Anchors` (parámetros de caso) o `family_parameters` | lo entrega el candidato |
| Reclamación de procedencia | `Anchors.declared` y, opcional, `migration.ProvenanceClaim` (caso, familia, mapeo y versión, ruta fuente, aprobación y versión) | ninguna: sólo referencias |
| Autoridad | `clinical_core/migration_authority.py` | la única: verdad del caso y registros de confianza |

- **`AuthoritySession.authorize(parameter, value)`** no recibe la reclamación. Recalcula la autorización desde:
  - **A. verdad del caso + mapeo registrado** (`TRUSTED_CASE_MAPPINGS`). Cada mapeo fija:
    - id y versión;
    - familia y casos a los que aplica;
    - parámetro destino;
    - campos fuente del banco (rutas con punto);
    - precondición de completitud y regla determinista, como código del registro, nunca del candidato;
    - descripción de los requisitos.

    La autoridad lee el registro del caso en `clinical_cases.py` ella misma, congelado, comprueba la precondición,
    recalcula el valor y lo compara con el entregado.
  - **B. registro de valores por defecto aprobados** (`APPROVED_FAMILY_DEFAULTS`): familia, parámetro, valor o rango
    inclusivo, id y versión de la aprobación, y estado; sólo «approved» autoriza.
- **Verificación del caso, antes de A o B:**
  - las anclas son exactamente `Anchors` y el id es un `str` exacto de un caso del repositorio;
  - su familia en el banco es la de la puerta;
  - la llegada observada, en forma canónica de tipos exactos (números `int`/`float`, `RhythmState` y su código
    exactos), es la que el camino heredado congelado construye para ese caso. La llegada de referencia se guarda en
    caché por id y digest del registro del banco, así que una verdad del caso cambiada nunca se sirve vieja;
  - desde ahí sólo se usa el id del banco, nunca el objeto del candidato.
- **Lo único que la autoridad toma del candidato son valores primitivos exactos.** Un valor cuenta sólo si es un
  `int` o `float` exacto y finito: una subclase podría informar un número y llevar otro (`__float__`, `__eq__`).
- **Unanimidad de las fuentes de confianza (regla de cierre por defecto):** cada fuente aplicable debe estar de
  acuerdo con el valor. Un mapeo o un valor aprobado que dice otra cosa, o un mapeo roto (campo inexistente, regla o
  precondición que fallan, regla sin número exacto), bloquea. Un mapeo cuya precondición el caso no cumple no aplica.
  La precedencia entre la verdad del caso y un valor de familia queda para decisión metodológica; mientras tanto,
  cualquier discrepancia bloquea. **Sustituido en P2H-1 (§15):** entre el caso y la familia decide la política de
  autoridad del parámetro; siguen bloqueando dos mapeos que discrepan, un mapeo roto y dos valores aprobados.
- **Un parámetro sólo de diagnóstico** (`reference_preload_fraction`) no se exige; si se declara, se verifica como
  los demás.
- **La puerta** (`migration_gate`) autoriza un parámetro sólo si la autoridad lo confirma y la reclamación coincide:
  - la fuente reclamada exige el tipo de confirmación correspondiente (`explicit_case` → mapeo; `approved_family_default`
    → registro);
  - una referencia dada (familia, caso, mapeo, versión, ruta, aprobación) debe coincidir;
  - una referencia del otro tipo invalida la reclamación.

  La reclamación sólo restringe; `default_unmapped`, `synthetic_probe` y CANDIDATE nunca autorizan.
- **Registros:** los dos están vacíos. Son tuplas de registros `dataclass(frozen=True)`; las reclamaciones también son
  inmutables y tipadas.
- **Dónde vive la autoridad de migración:** fuera del objeto parámetro/procedencia del candidato, en la verdad del caso
  verificable de forma independiente o en los registros de aprobación de confianza.

### 14.3 Sondas de suplantación (`test_clinical_core_migration_gate.py`)

Todas fallan cerradas:
1. candidato reetiquetado como `explicit_case` sin evidencia del caso;
2. candidato reetiquetado como `approved_family_default` sin entrada en el registro (también con entradas de otra
   familia o de otro valor);
3. caso equivocado: anclas de 72f con id de 57m, un id inexistente, o un caso reclamado distinto;
4. familia equivocada: familia reclamada distinta, caso de otra familia, o un mapeo de otra familia;
5. campo fuente inexistente en el caso;
6. mapeo registrado cuyo valor fuente cambió en el banco;
7. valor por defecto distinto del registrado (y también un estado no aprobado o un rango que no lo contiene);
8. sonda sintética presentada como procedencia de un caso real (valores de sonda reetiquetados, o la llegada
   sintética `band_probe`).

Además:
- **Regresión de la propiedad exigida:** con la verdad del caso y los registros fijos, 144 combinaciones aleatorias
  con semilla fija de fuente, ruta, mapeo, aprobación, familia, caso reclamado e id de las anclas nunca hacen pasar a
  un candidato no autorizado.
- Cualquier fila migrable tiene una confirmación independiente de la autoridad.
- Sólo cambiar una fuente de confianza (registrar un mapeo que confirma, o cambiar la verdad del caso) cambia la
  autorización.
- **Las pruebas no son vacías:** con una autoridad mutante que lo confirma todo fallan 20 pruebas, entre ellas las 8
  sondas; cada uno de los 12 mutantes del revisor, y uno equivalente que afloja `exact_number`, hace fallar al menos
  una. Sobre los registros de producción vacíos, 1600 intentos de suplantación (etiquetas, reclamaciones, ids y
  valores adversarios) dan 0 filas migrables.
  La regresión declara los 8 parámetros de caso y alterna reclamaciones sin referencias, para que una puerta que
  confiara en la etiqueta no pueda pasarla; la prueba de confirmación independiente exige filas migrables.
- **Pruebas adaptadas, y por qué:** las de P2E-6 que daban por bueno un caso sintético sólo por sus etiquetas ahora
  instalan registros de confianza de prueba (mapeos y aprobaciones sintéticos) sobre un caso real. Lo que protegían
  (cierre por defecto con un `synthetic_probe` o un parámetro de familia ausente, valor aprobado distinto) sigue
  protegido; lo que cambió a propósito es que las etiquetas solas ya no pasan.

### 14.4 Revisión adversarial de suplantación (sólo lectura)

Con los registros de producción vacíos, ninguna suplantación tuvo éxito: 56 intentos sobre los dos casos GI, entre
ellos subclases de `str` y `float` que mienten, reclamaciones que cambian entre lecturas, `declared` y `case_id`
inyectados, NaN, `10**400` y booleanos. Al poblar registros en memoria, la revisión halló once puntos latentes;
todos se confirmaron con sonda y se corrigieron, cada uno con su prueba:

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| F1 | media | el valor autorizado podía no ser el que lleva el candidato (`__float__` de una subclase) | sólo `int`/`float` exactos |
| F2 | media | `verify_case` se engañaba con subclases que redefinen la igualdad | forma canónica de tipos exactos |
| F3 | media | un `case_id` subclase de `str` podía cruzar casos y la caché | `str` exacto; después, sólo el id del banco |
| F4 | media | mutantes que sobrevivían, una prueba vacía y una regresión de poca potencia | pruebas de precondición, `cases`, reglas rotas; regresión y prueba de confirmación reforzadas; los 12 mutantes del revisor fallan |
| F5 | media | el candidato elegía qué fuente contaba; fuentes que discrepaban autorizaban | unanimidad de las fuentes aplicables (precedencia: decisión pendiente; sustituida por la precedencia de P2H-1, §15) |
| F6 | baja | un parámetro sólo de diagnóstico declarado con valor de sonda no bloqueaba | se verifica si se declara |
| F7 | baja | la llegada de referencia en caché podía quedar vieja | clave con el digest del registro del banco |
| F8 | baja | `ApprovedDefault` no validaba tipos | números exactos y finitos |
| F9 | baja | etiquetas subclase de `str` confundían el tipo de autoridad | `str` exacto en reclamaciones y etiquetas |
| F10 | baja | excepciones de reglas y `10**400` no eran `MigrationBlocked` | se capturan y cierran |
| F11 | baja | la comprobación estática era débil | importa nada de la puerta en ninguna forma; no lee `declared`; `authorize` no nombra reclamaciones |

**Límites que quedan (endurecimiento, no defectos demostrados):**
- la puerta devuelve un informe, no anclas selladas: quien migre debe usar las anclas verificadas tal como se
  verificaron;
- los registros, `REQUIRED_AUTHORITY` y `FAMILY_GATES` son globales del módulo: el digest cubre su código, no su estado
  en ejecución;
- los `family_parameters` del informe no están ligados todavía a los literales que usa el módulo hemorrágico;
- la verificación del caso usa el camino heredado de GI: otra familia falla cerrada hasta adaptarlo.

### 14.5 Semántica del betabloqueo para la autoría (no decidida)

- **A.** Una fuente de medicación o antecedentes explícitamente completa que muestre que no hay betabloqueador podría
  mapearse a `beta_blockade` = 0 con un mapeo registrado cuya precondición sea esa completitud.
- **B.** Un betabloqueador simplemente no mencionado, o información de medicación incompleta, no es evidencia de
  `beta_blockade` = 0.
- **En el repositorio:** 57m declara ibuprofeno (`clinical_cases.py:889`) y 72f naproxeno, sin protector gástrico
  (`:918`). La fuente es lo que relata el paciente, y ningún campo dice que la lista esté completa. P2H-0 no decide
  si los casos cumplen A: queda para la docencia y la autoría (FD-20). No hay mapeo registrado, y `beta_blockade = 0`
  no se aprueba globalmente.
- La categoría del ensayo en seco de P2F-11 para `beta_blockade` («requiere valor por defecto de familia aprobado») no
  cambió; su texto ahora dice que la ausencia de mención no es evidencia de 0. Si esa categoría debe pasar a
  «requiere decisión docente» es parte de la misma pregunta. **P2H-1 la cambió por indicación del responsable del
  proyecto (§15.4).**

### 14.6 Digest y paquete

- **Nuevo componente `migration_sources`** del congelamiento: `clinical_core/migration.py` y
  `clinical_core/migration_authority.py` completos (las reglas de reclamación y los dos registros).
- `harness_sources` cambia porque `calibration.py` declara ese componente.
- `rules`, `bands`, `scenarios`, `input_path_sources`, `input_adapter_sources` y `scenario_inputs` no cambian: la
  aceptación de P2F es la misma y no se repitió su barrido.
- **El paquete de P2G se regeneró:** sus tablas numéricas son idénticas a las de `a4f33f2`; sólo cambian los digests.
- **Documento docente:** §14 describe la regla, FD-49 sale de las decisiones abiertas (resuelta aquí) y FD-20 recoge la
  semántica A/B.

## 15. P2H-1 · Precedencia de la autoridad de migración (2026-10-24)

- **Base:** `4164d66` (P2H-0 aceptado y cerrado; FD-49 resuelta en arquitectura).
- **Naturaleza:** semántica de la autoridad de migración. No cambia la fisiología, las bandas, las reglas, los escenarios
  ni los adaptadores; no aprueba valores ni elige políticas; el GI no migra; no hay integración en tiempo de ejecución.

### 15.1 La decisión aplicada

Decisión metodológica aprobada por el responsable del proyecto: un valor por defecto de familia es un **respaldo**, no
una fuente que compita con la verdad del paciente. Para un parámetro que admite que el caso lo sustituya:
1. verdad del caso verificada (`explicit_case`, por un mapeo registrado);
2. valor por defecto de familia aprobado;
3. sin resolver: cierra.

No se exige unanimidad entre el caso y el valor de familia. Esto sustituye la regla de unanimidad de §14.2 sólo entre
esas dos fuentes; siguen cerrando dos mapeos del caso que discrepan entre sí, un mapeo roto y dos valores aprobados para
un mismo parámetro.

### 15.2 Dónde vive la política y qué dice

- **Representación:** `migration_authority.AuthorityPolicy(family, parameter, policy, version, rationale)`, inmutable y de
  tipos exactos, en el registro de confianza `AUTHORITY_POLICIES`, junto a los mapeos y las aprobaciones. La autoridad
  la busca por familia y parámetro (`policy_for`).
- **Nunca en la metadata del candidato:** `ProvenanceClaim` no tiene campo de política; `Anchors.declared` sólo admite
  parámetros de caso; una entrada de familia es exactamente (valor, fuente).

| Política | Con verdad del caso verificada | Sin ella, con valor de familia aprobado | Caso ≠ familia |
|---|---|---|---|
| `CASE_OVERRIDES_FAMILY_DEFAULT` | autoriza el caso | autoriza el valor de familia | autoriza el caso; el valor de familia no veta; la diferencia se registra |
| `FAMILY_FIXED` | no decide: autoriza el valor de familia si coincide | autoriza el valor de familia | cierra: la sustitución por el caso no está permitida |
| `CASE_REQUIRED` | autoriza el caso | cierra: un valor de familia no es respaldo | autoriza el caso; la diferencia se registra |

- **Sin política declarada, o con más de una:** cierra. Una política desconocida no se puede construir.
- **Orden de `authorize(parameter, value)`:**
  1. registros de tipo exacto: una entrada que no es exactamente `AuthorityPolicy`, `CaseMapping` o `ApprovedDefault`
     cierra todo;
  2. política (se informa aunque ninguna fuente tenga el parámetro);
  3. fuentes de confianza del parámetro;
  4. valor exacto;
  5. caso verificado;
  6. mapeos recalculados desde la verdad del caso, sin mirar el valor entregado;
  7. integridad de los registros;
  8. selección según la política;
  9. comparación del valor entregado con lo que resuelve la autoridad seleccionada.

  La reclamación sigue sin ser una entrada: sólo restringe, en la puerta. Si reclama la autoridad que la política no
  seleccionó, se rechaza.
- **En producción `AUTHORITY_POLICIES` está vacío.** Qué política lleva cada parámetro GI no es una consecuencia de la
  regla, sino una decisión metodológica por parámetro (FD-50). Hasta entonces todos cierran por falta de política; ya
  cerraban por los registros vacíos.

### 15.3 Informe de procedencia

Cada fila de la puerta lleva en `authority`:
- **`kind`, `reference`, `version`:** la autoridad que la política seleccionó (mapeo o aprobación), también en un
  rechazo; `None` si no seleccionó ninguna;
- **`confirmed`:** si esa autoridad sostiene el valor entregado. Una fila puede tener `confirmed` y no ser migrable,
  si la reclamación no coincide;
- **`policy`;**
- **`resolved`:** el valor que la autoridad recalculó desde el caso, o el valor o rango aprobado;
- **`not_used`:** las fuentes de confianza que existían y no decidieron, con el motivo. Puede ser por precedencia, por una
  precondición no cumplida, por un mapeo limitado a otro caso, por un estado no aprobado o porque el respaldo no está
  permitido;
- **`conflicts`:** las discrepancias, también las que la precedencia resolvió.

Si varios mapeos coinciden, el orden del registro selecciona uno y los demás aparecen en `not_used`; una reclamación
que nombra otro de ellos se rechaza, porque sólo restringe. `authority` es `None` sólo cuando la autoridad no llegó a
consultarse (fuente no migrable o no declarada). Ninguna discrepancia se descarta en silencio.

### 15.4 Betabloqueo

- La categoría del ensayo en seco de `beta_blockade` pasa a `E. FACULTY AUTHORING DECISION REQUIRED`; antes era
  «requiere valor por defecto de familia aprobado».
- **Pregunta abierta (FD-20):** ¿la autoría GI debe exigir una conciliación de medicación explícitamente completa, capaz
  de probar `beta_blockade` = 0, o la docencia debe aprobar un valor por defecto de familia GI?
- P2H-1 no elige ni infiere 0 de la ausencia de mención.
- En términos de política, la primera opción sería `CASE_REQUIRED` con un mapeo cuya precondición es la completitud. La
  segunda sería un valor aprobado con `CASE_OVERRIDES_FAMILY_DEFAULT` o `FAMILY_FIXED` (FD-50).

### 15.5 Pruebas (`test_clinical_core_migration_gate.py`)

Con registros y políticas de prueba (`test_p2h1_*`):
1. la verdad del caso verificada prevalece sobre un valor de familia distinto con `CASE_OVERRIDES_FAMILY_DEFAULT`, y la
   discrepancia queda en `conflicts`;
2. el valor de familia se usa cuando no hay mapeo del caso, o el mapeo no aplica a ese caso;
3. `FAMILY_FIXED` rechaza la sustitución por un caso distinto, cualquiera sea el valor o la fuente reclamada. Con un
   caso que coincide autoriza la familia, y una reclamación `explicit_case` se rechaza;
4. `CASE_REQUIRED` rechaza el respaldo de familia y autoriza la verdad del caso;
5. la metadata del candidato no puede cambiar la política. No hay dónde ponerla: en una reclamación es un `TypeError`,
   en `declared` un `CoreInvariantError`, en una entrada de familia `MigrationBlocked`. Sesenta reclamaciones aleatorias
   por política no cambian la política, el valor resuelto ni los conflictos;
6. reclamar la precedencia contraria (que gane el valor de familia) no cambia la autorización: la política sigue
   seleccionando el caso;
7. una política no declarada, duplicada o de otra familia cierra, y una política desconocida no se construye;
8. el informe dice qué autoridad ganó, con su política, el valor resuelto y lo que no se usó, también en un rechazo.

Además, la producción no declara ninguna política y cada parámetro GI cierra por eso. Las pruebas `test_review_*` de
§15.7 cubren los bordes que halló la revisión.

- **Se mantienen intactas** las ocho sondas de suplantación de FD-49 y la regresión de 144 combinaciones.
- **Pruebas adaptadas, y por qué:**
  - el fixture `trust` instala, además de mapeos y aprobaciones, una tabla de políticas de prueba
    (`CASE_OVERRIDES_FAMILY_DEFAULT` para cada parámetro GI). Sin ella, todo cerraría por falta de política y las
    pruebas de P2H-0 dejarían de probar lo suyo;
  - la de F5 cubre ahora mapeos que discrepan y valores aprobados duplicados, porque caso contra familia es precedencia;
  - la de F4 lee el motivo también en `not_used`;
  - la del diccionario de autoridad incluye los campos nuevos.
- `test_clinical_core_calibration_framework.py` comprueba la categoría E de `beta_blockade`, y
  `test_clinical_core_decision_pack.py` admite el id retirado FD-49 sin reutilizarlo.

### 15.6 Digest y paquete

- **Nuevo componente `authority_registries`:** los tres registros tal como están cargados. Incluye las políticas; los
  mapeos, con id, versión, campos, requisitos, casos y el código de su precondición y su regla; y las aprobaciones
  (`migration_authority.registry_content`). Las políticas son parte de la frontera de confianza: cambiar sólo la
  política de un parámetro cambia el digest (`test_a_changed_authority_registry_changes_the_digest`).
- **Cómo se fija el código de un mapeo.** La precondición y la regla deben ser funciones Python normales definidas en
  el repositorio; un `partial`, un objeto invocable o un método ligado no se pueden construir. El digest las fija por
  su fuente (o su bytecode, si no hay fuente), sus constantes, sus valores por defecto (también los de sólo palabra
  clave), su closure y los globales que nombran. Los módulos y clases del repositorio se fijan por su archivo. Los
  conjuntos y diccionarios se ordenan, así que el digest es el mismo con cualquier `PYTHONHASHSEED`. Un contenido que
  no puede fijarse así (un objeto cuya repr lleva una dirección, por ejemplo) hace fallar el digest de forma explícita,
  en vez de omitirlo.
- **Cambian:**
  - `migration_sources` (`migration.py`, `migration_authority.py`);
  - `harness_sources`, porque `calibration.py` declara el componente nuevo;
  - el congelamiento: `d293793a…` pasa a `8048c04f…`.
- **No cambian** `rules`, `bands`, `scenarios`, `input_path_sources`, `input_adapter_sources` ni `scenario_inputs`, así
  que no se repitió el barrido de P2F.
- **El paquete de P2G se regeneró:** sus tablas numéricas son idénticas a las de `4164d66`; sólo cambian los digests.
- **Documento docente:**
  - §14 reemplaza la unanimidad por la precedencia y describe el informe;
  - FD-20 lleva la pregunta de autoría con sus dos opciones;
  - FD-50 es la política de cada parámetro;
  - quedan 49 decisiones abiertas.

### 15.7 Revisión adversarial de precedencia y política (sólo lectura)

La revisión confirmó que la precedencia era correcta en todos los escenarios probados. También halló seis puntos y
un endurecimiento. Cada uno se reprodujo con su sonda y se corrigió con su prueba (`test_review_m*`, `test_review_f*`,
`test_review_h1_*`):

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| F1 | media | 7 mutantes que rompían la política sobrevivían a las pruebas: FAMILY_FIXED recurría al caso; CASE_REQUIRED recurría al valor de familia si el mapeo no aplicaba; defaults duplicados tolerados si ganaba el caso; un rango nunca «difería»; precondición no cumplida que bloqueaba; rango exclusivo; conflicto con un rango descartado | pruebas para cada uno; hacen fallar al menos una prueba los 8 mutantes de la revisión que siguen aplicando, un equivalente de su M13 y 13 mutantes de las correcciones |
| F2 | media | el digest no veía un cambio en un default de sólo palabra clave, en una lambda sin fuente, en un invocable, en un método ligado ni en una tabla global que lee la regla; con un `partial` o un conjunto en el closure cambiaba entre intérpretes | funciones normales del repositorio, forma canónica (§15.6) y fallo explícito ante lo que no puede fijarse |
| F3 | media (decisión) | con FAMILY_FIXED y un rango aprobado, un valor dentro del rango se autorizaba aunque la verdad del caso, también dentro, fuera otra, sin dejar rastro | la diferencia queda en `conflicts`; la autorización no cambia: si debe rechazarse es parte de FD-50 |
| F4 | baja | un `int` que el float no representa exactamente (2⁵³ + 1) se autorizaba contra 2⁵³ | `exact_number` lo rechaza |
| F5 | baja | la puerta llamaba a `repr`/`str` del objeto del candidato: un `__repr__` que lanza escapaba como `RuntimeError` (también con los registros de producción vacíos) y uno mentiroso falseaba el motivo o la fuente | `migration_authority.shown`: nunca llama a métodos del candidato |
| F6 | baja | en un rechazo el informe no decía qué autoridad había seleccionado la política; un segundo mapeo que coincidía desaparecía del informe; la política no se informaba si no había fuentes | `selected` y `confirmed` en el informe; los mapeos que coinciden van a `not_used`; la política se informa siempre |
| H1 | endurecimiento | los registros se usaban sin comprobar el tipo de cada entrada: una tupla escapaba como `AttributeError` y un `SimpleNamespace` saltaba la validación | tipos exactos; si no, cierra todo y el digest falla |

**Lo que la revisión confirmó que resiste:**
- CASE_OVERRIDES: el caso gana sin unanimidad y el conflicto se registra.
- FAMILY_FIXED bloquea si el caso difiere, si no hay valor aprobado o si sólo hay un borrador.
- CASE_REQUIRED bloquea con un mapeo de otro caso o una precondición no cumplida, aunque haya valor de familia.
- Una política no declarada, duplicada o de otra familia cierra.
- La reclamación no llega a `authorize` y sólo restringe.
- Producción: 0 políticas, 0 mapeos y 0 valores aprobados; los dos casos GI fallan la puerta; `beta_blockade` está en
  la categoría E.

**Límites que quedan:**
- Una regla del repositorio puede leer un módulo de fuera del repositorio (la biblioteca estándar); de ese módulo el
  digest sólo fija el nombre.
- La revisión propuso restringir las reglas a funciones definidas en `MIGRATION_SOURCES`. No se adoptó: es una
  decisión de arquitectura. Hoy basta con que estén en el repositorio.
- Los registros de confianza siguen siendo globales del módulo, como en P2H-0. El digest fija ahora su contenido cargado.

### 15.8 Gancho en tiempo de ejecución

Ninguno. `clinical_core` sigue sólo en sombra; ningún módulo de la aplicación lo importa.

## 16. P2H-2 · Semántica de las políticas de autoridad y matriz GI (2026-10-24)

- **Base:** `b1fd5b9` (P2H-1 aceptado y cerrado).
- **Naturaleza:** semántica de la autoridad y apoyo a la decisión FD-50. No cambia la fisiología, las bandas, las
  reglas, los escenarios ni los adaptadores; no aprueba valores ni declara políticas; el GI no migra; no hay
  integración en tiempo de ejecución.

### 16.1 La ambigüedad de FAMILY_FIXED, resuelta

Con P2H-1, `FAMILY_FIXED` y un rango aprobado autorizaban cualquier valor dentro del rango. Si el valor difería de la
verdad del caso, sólo se registraba la diferencia (§15.7, F3). «Fijo» no quedaba claro. P2H-2 separa dos políticas y
el registro distingue el valor del rango:

| Política | Registro de familia que exige | Valor autorizado | Sin verdad del caso |
|---|---|---|---|
| `FAMILY_FIXED_VALUE` | un valor exacto (un rango cierra) | exactamente el valor de familia; un caso distinto cierra | el valor de familia |
| `FAMILY_ALLOWED_RANGE` | un rango (un valor exacto cierra) | el valor del caso, recalculado desde la verdad del caso y dentro del rango; fuera, cierra | sólo el respaldo explícito del rango, si existe; si no, cierra |
| `CASE_OVERRIDES_FAMILY_DEFAULT` | un valor exacto, o un rango con respaldo explícito | el valor del caso; el de familia no veta | el valor exacto o el respaldo; un rango sin respaldo cierra |
| `CASE_REQUIRED` | ninguno: se informa como no usado | el valor del caso | cierra |

- `ApprovedDefault` gana `fallback`: un valor exacto dentro del rango, aprobado explícitamente. Ningún respaldo se
  deriva, ni siquiera el punto medio.
- Un parámetro sin política, o con más de una, cierra. `FAMILY_FIXED` ya no existe; las políticas de producción
  siguen vacías, así que no hay nada que migrar.
- El valor entregado se compara siempre exactamente con el valor resuelto: un rango nunca es el valor.

### 16.2 Modelo de confianza de FAMILY_ALLOWED_RANGE

1. valor del candidato;
2. mapeo `explicit_case` registrado y caso verificado;
3. valor recalculado desde la verdad del caso;
4. rango de familia de confianza;
5. ¿el valor recalculado está dentro del rango?;
6. autorización.

- La autoridad seleccionada es el mapeo del caso: el valor sigue siendo del caso.
- El rango aparece en el informe como `envelope` (aprobación, versión y límites).
- Un candidato no pasa porque declare `approved_family_default` con un valor dentro del rango: el rango manda sobre
  los valores permitidos, no prueba el valor del paciente. Lo comprueban:
  - `test_p2h2_allowed_range_never_authorizes_a_value_merely_inside_the_range`: sin mapeo, con un mapeo de otro
    caso, o con un valor del rango distinto de la verdad del caso;
  - `test_p2h2_spoofed_metadata_cannot_widen_an_allowed_range`: 200 reclamaciones aleatorias, y sólo pasa el valor
    del caso declarado `explicit_case`.

### 16.3 Dónde puede vivir una regla de confianza

**Decisión del responsable del proyecto:** no se restringe por módulo. Así queda la propuesta de la revisión de P2H-1
(§15.7). Una regla puede vivir en cualquier archivo fuente versionado del repositorio si:
- está registrada explícitamente en `TRUSTED_CASE_MAPPINGS`;
- el digest cubre su implementación exacta: fuente, constantes, valores por defecto, closure y los globales que
  nombra;
- es determinista. La autoridad evalúa la precondición y la regla dos veces sobre la misma verdad congelada; si
  difieren, el mapeo está roto y cierra;
- cumple las restricciones de tipos exactos y de procedencia: es una función normal, devuelve un número exacto y
  lee sólo campos del banco.

Si el registro no puede fijarse de forma reproducible, `authorize` cierra todos los parámetros. Eso pasa, por ejemplo:
- con una regla, o una función que la regla llama, construida en tiempo de ejecución sin fuente en el repositorio;
- con un objeto cuya repr lleva una dirección;
- con un contenedor que se contiene a sí mismo;
- con cualquier otra falla al fijarlo.

La huella se toma una vez por sesión y se recalcula después de evaluar las reglas: si una regla cambió el estado que el
digest fija, cierra.

El código se fija por su fuente y por los nombres que esa fuente lee, no por sus constantes compiladas. Así el digest
es el mismo bajo la reescritura de aserciones de pytest y bajo el intérprete normal. Del código fuera del repositorio
(la biblioteca estándar) sólo se fija el nombre.

**Fundamento.** Restringir por módulo no agrega confianza: un archivo de migración también puede tener una regla mala.
Y sí obligaría a mover la lógica del caso a donde no corresponde. Lo que sostiene la confianza es:
- que la regla esté registrada, porque nada no registrado puede autorizar;
- que el digest congelado la fije, porque cualquier cambio se ve y hay que registrarlo;
- que la autoridad la verifique, recalculando desde la verdad del caso.

Ninguna de las tres depende de la ubicación. `test_p2h2_a_registered_rule_outside_the_migration_modules_is_valid` usa
una regla definida en el archivo de prueba.

### 16.4 Matriz FD-50

Está en el documento docente, §15: un renglón por parámetro que la puerta puede exigir, con su significado, la
procedencia actual, la evidencia directa del caso, si tiene sentido a nivel de familia, las opciones de política, una
categoría y el fundamento. No aprueba valores ni llena registros.
- **Clara por la arquitectura:** `fraction_with_ppi` y `fraction_after_hemostasis` (`FAMILY_FIXED_VALUE`).
- **Acotadas:**
  - `hb_loss_g_dl_per_min` sigue a `volume_loss_ml_per_min`;
  - en `preload_fraction` y `arrival_lactate_excess`, un valor fijo de familia contradice lo que muestra cada caso.
- **Decisión docente:** el resto.
- **`beta_blockade`:** FACULTY_AUTHORING_DECISION_REQUIRED, con la opción A (`CASE_REQUIRED` con conciliación completa)
  y la B (valor de familia GI como respaldo). Ninguna está elegida.

### 16.5 Pruebas

- **Nuevas (`test_p2h2_*`):**
  - las cuatro políticas, y que el nombre anterior no existe;
  - `FAMILY_FIXED_VALUE`: exige el valor exacto y rechaza un caso distinto;
  - `FAMILY_ALLOWED_RANGE`: el valor del caso dentro del rango pasa, fuera no, y un valor que sólo cae dentro del
    rango no pasa; el respaldo, sólo si la aprobación lo define; un valor exacto no sirve como rango;
  - las validaciones del respaldo;
  - `CASE_OVERRIDES_FAMILY_DEFAULT`, sin punto medio;
  - `CASE_REQUIRED`;
  - metadata suplantada;
  - una regla fuera de los módulos de migración es válida; una regla no fijable, no registrada o no determinista
    cierra.
- **De la revisión (`test_review_p2h2_*`):**
  - una función construida en tiempo de ejecución que la regla llama cierra todo;
  - un contenedor que se contiene a sí mismo es un rechazo cerrado;
  - una regla que cambia el estado que el digest fija se rechaza;
  - el digest es el mismo bajo pytest y bajo un intérprete normal;
  - el informe nombra el respaldo usado o no usado;
  - `FAMILY_FIXED_VALUE` rechaza un rango aunque tenga respaldo;
  - `CASE_OVERRIDES_FAMILY_DEFAULT` nunca inventa un límite ni el punto medio;
  - una precondición no determinista está rota;
  - el digest fija cada campo de una aprobación (respaldo, límites, estado) y de una política (versión, fundamento,
    política).
- **Se mantienen** las sondas de FD-49, la regresión de 144 combinaciones y las pruebas de precedencia de P2H-1.
- **Adaptadas al modelo nuevo, protegiendo lo mismo:**
  - el nombre `FAMILY_FIXED` pasa a `FAMILY_FIXED_VALUE`;
  - los rangos con `FAMILY_FIXED` pasan a `FAMILY_ALLOWED_RANGE`;
  - un rango sin respaldo ya no es un valor por defecto (antes autorizaba cualquier valor del rango);
  - la prueba de F3 comprueba ahora que el rango nunca autoriza un valor distinto de la verdad del caso;
  - una lambda sin fuente ya no se fija por su bytecode: se rechaza;
  - el informe gana `envelope`.

### 16.6 Digest

- `authority_registries` incluye ahora `policy_model` (el vocabulario de políticas) y el respaldo de cada aprobación.
  Los registros de producción siguen vacíos, pero el componente cambia por el vocabulario.
- `migration_sources` cambia (`migration.py` y `migration_authority.py`); el congelamiento pasa de `8048c04f…` a
  `152abc6c…`.
- `rules`, `bands`, `scenarios`, `input_path_sources`, `input_adapter_sources` y `scenario_inputs` no cambian: no se
  repitió el barrido de P2F.

### 16.7 Revisión adversarial de la semántica de políticas (sólo lectura)

**Lo que la revisión confirmó que resiste:**
- Producción: los dos casos GI fallan con 12 bloqueos y nada es migrable.
- `FAMILY_FIXED_VALUE` rechaza un rango, un caso distinto y una reclamación `explicit_case`.
- `FAMILY_ALLOWED_RANGE`:
  - nunca autoriza un valor sólo por caer dentro del rango;
  - no inventa el punto medio;
  - usa el respaldo sólo si existe y sólo sin valor del caso;
  - rechaza un registro exacto y un caso fuera del rango.
- Un mapeo roto bloquea aunque haya respaldo.
- Los mapeos de otro caso, familia o parámetro y los registros propuestos no autorizan.
- Las reclamaciones sólo restringen.

Halló estos puntos; cada uno se reprodujo con su sonda y se corrigió con su prueba:

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| F1 | media | una función construida en tiempo de ejecución que llama una regla del repositorio se fijaba sólo por su nombre: dos versiones con distinto resultado daban el mismo digest | sólo el código de fuera del repositorio se fija por nombre; el de un módulo del repositorio sin archivo fuente hace fallar la huella y cierra todo |
| F2 | baja | un contenedor que se contiene a sí mismo hacía escapar `RecursionError` de la puerta | detección de ciclos; cualquier falla al fijar la huella es un rechazo cerrado |
| F3 | baja | una regla que cambiaba el estado que fija el digest seguía autorizando con la huella ya desviada | la huella se recalcula después de evaluar las reglas; si cambió, cierra |
| F4 | baja | el digest de una regla de un módulo de prueba cambiaba bajo la reescritura de aserciones de pytest | el código se fija por su fuente y por los nombres que esa fuente lee |
| R1 | baja | con el respaldo de un rango, la aprobación ganadora figuraba también como «no usada» | ya no figura; `envelope` incluye el respaldo |
| R2 | baja | con un valor del caso dentro del rango, un respaldo existente no se informaba como no usado | se informa |
| T1–T5 | media/baja | sobrevivían mutantes: `FAMILY_FIXED_VALUE` con un rango con respaldo; `CASE_OVERRIDES_FAMILY_DEFAULT` inventando un límite; el digest sin respaldo, límites o versión y fundamento de la política; la precondición evaluada una vez; el respaldo no usado sin informar | pruebas nuevas. Hacen fallar al menos una prueba los 16 mutantes de la revisión que siguen aplicando (uno sustituido por su equivalente tras R1) y 5 mutantes de las correcciones |
| Doc1–3 | — | en la matriz FD-50: la banda intrínseca es 60–100 en los dos casos; 2,5 mL-eq/min es la conversión del adaptador del literal 0,003 de circulación por minuto; el POCUS es un borrador pendiente de revisión docente | corregido en el documento docente |

**Información:** un valor aprobado 0,0 acepta un -0,0 entregado, porque son iguales numéricamente.

### 16.8 Gancho en tiempo de ejecución

Ninguno. `clinical_core` sigue sólo en sombra.

## 17. P2I-1 · Corte de decisión docente: el lactato GI (2026-10-25)

- **Base:** `045ec43` (P2H-2 aceptado y cerrado; la fase de arquitectura para la calibración GI en sombra se considera
  completa).
- **Naturaleza:** apoyo a la decisión, no infraestructura. No cambia la fisiología, las bandas, las reglas
  congeladas, los escenarios del golden, el golden, la autoridad de migración ni los registros. FACULTY_APPROVED sigue
  en 0 y no hay integración en tiempo de ejecución.
- **Artefacto:** `docs/revision/P2I_DECISION_LACTATO_GI.md`, con sus números en `docs/revision/P2I_lactate_slice.json`.
  Lo genera `python -m clinical_core.lactate_slice` sobre la región admisible de P2G (1054 conjuntos) en cuatro
  escenarios de 120 min:
  - L1, sin tratar;
  - L2, salina sin hemostasia;
  - L3, manejo definitivo;
  - L4, hemostasia sin volumen. Es una **composición contrafactual manual**: el motor de familias difiere esa
    endoscopia y nunca produce esa hemostasia, que se agrega a mano con un identificador propio. Ninguna pregunta
    de la hoja de trabajo la usa.
- **Descomposición exacta del exceso de lactato**, dada la trayectoria del déficit: lo que queda del exceso de llegada,
  lo que produce la D de llegada y lo que produjo el déficit posterior. No es una atribución causal entre parámetros.
- **Hoja de trabajo docente:** FD-LAC-01 a FD-LAC-06, con la selección en blanco. Hasta que la docencia las responda
  no se abren FC, PA, FR, volumen ni colapso.
- **La referencia heredada** aparece aparte y al final. Ninguna tabla ni clase la lee, y una prueba lo comprueba.
- **Digests:**
  - el congelamiento de calibración no cambia, porque el módulo nuevo no es parte del arnés;
  - el paquete de P2G excluye el módulo de su digest, porque sus números no pueden depender de él: el corte lee el
    paquete, nunca al revés. Una prueba lo comprueba: corre la generación del paquete en un intérprete nuevo y
    verifica que nunca carga un módulo excluido, y que ningún módulo hasheado lo importa. Si un día lo importara, la
    prueba falla y la exclusión hay que quitarla;
  - ese cambio en `decision_pack.py` cambia una vez el digest del paquete, que se regeneró con tablas idénticas;
  - el digest propio del corte cubre todas las fuentes de `clinical_core`, renderizadores incluidos, más el
    congelamiento y las órdenes de los escenarios.
- **Gancho en tiempo de ejecución:** ninguno.

## 18. P2I-2 · Restricciones docentes del lactato GI aplicadas (2026-10-25)

- **Base:** `05cf1da` (P2I-1 aceptado y cerrado). La docencia respondió FD-LAC-01 a FD-LAC-06.
- **Qué son:** las primeras restricciones clínicas de comportamiento aprobadas (FACULTY_APPROVED), registradas tal cual
  en `clinical_core/faculty_constraints.py`. No aprueban ningún valor de parámetro oculto: el registro de calibración
  sigue con FACULTY_APPROVED = 0, los registros de autoridad siguen vacíos, la puerta de migración GI sigue fallando y
  ni la puerta, ni su autoridad, ni la calibración, ni las bandas leen el módulo (lo comprueba una prueba). El registro
  de la decisión está en la §12 de `docs/revision/P2I_DECISION_LACTATO_GI.md`, generado desde el registro.
- **Definiciones operativas:** son una propuesta del núcleo, no una decisión docente. Quedaron congeladas antes de
  filtrar, en el commit `9301a6a`, con su diseño de sensibilidad y las reglas de informe (identificabilidad y
  representantes). El filtro se niega a correr si cambian los digests de las definiciones, de la canalización o de las
  reglas de informe. Este último se fijó después de la primera corrida, sobre el texto de `9301a6a`, que no cambió.
- **Filtro:** `python -m clinical_core.lactate_constraints` sobre exactamente la región admisible de P2F (1054
  conjuntos), sin candidatos nuevos, en L1, L2 y L3, todas trayectorias producidas por el motor; la L4 contrafactual no
  entra. Sobreviven 66 a las seis: es la **región candidata restringida por la docencia**, que sigue CANDIDATE.
  Resultados, sensibilidad, disociaciones, identificabilidad, representantes y la referencia heredada (ubicada después
  del filtro, nunca dentro) están en `docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md` y
  `docs/revision/P2I2_lactate_constraints.json`.
- **Procedencia heredada:** una prueba envenena el lactato que calcula el motor de familias y vacía las cachés de sus
  corridas (`calibration._RUNS` y `lactate_slice._INPUTS`):
  - no cambia ninguna trayectoria, ningún veredicto ni ningún resultado del informe;
  - sólo cambian la referencia heredada y los digests de procedencia, que detectan el motor cambiado;
  - el lactato de llegada del núcleo es el valor escrito en el caso (verdad del repositorio).
  La prueba equivalente de P2I-1 dependía de corridas en caché; quedó reforzada.
- **Digests:**
  - el paquete P2G excluye los dos módulos nuevos, con la misma guarda que `lactate_slice.py`, y se regeneró con tablas
    idénticas;
  - el digest del corte de P2I-1, que cubre todo `clinical_core`, cambió por los módulos nuevos, y el corte se regeneró
    con números idénticos;
  - el congelamiento de calibración no cambia.
- **Gancho en tiempo de ejecución:** ninguno.

## 19. P2I-2R · Restricciones del lactato GI aclaradas por la docencia (2026-10-26)

- **Base:** `0f6aed1`. La docencia aclaró FD-LAC-01, FD-LAC-04 y FD-LAC-05 y confirmó las definiciones comunes. Lo hizo
  con texto propio, registrado tal cual en `clinical_core/faculty_constraints.py` (versión «FD-LAC v2»). Es una
  aclaración de decisiones ya aprobadas, no una regla elegida por el resultado de P2I-2 (66 sobrevivientes).
- **Qué cambió:**
  - **FD-LAC-01:** sólo prohíbe, antes de los 60 min, un descenso sostenido y sustancial (≥ 10 % en ≥ 30 min) con
    sangrado activo y entrega inadecuada; las envolventes de 60 min siguen siendo duras;
  - **FD-LAC-04:**
    - T\* es la más tardía entre la hemostasia y el inicio de la entrega adecuada sostenida;
    - L(T\*) ≤ 2,0 es ALREADY_NORMALIZED;
    - la falta de seguimiento, o una entrega que deja de ser adecuada, es NOT_EVALUABLE;
    - pasa con L(T\* + 30) < L(T\*) y un aclaramiento en curso;
    - los umbrales de 5, 10 y 15 % son sólo sensibilidad;
  - **FD-LAC-05:** con entrega adecuada sostenida, L120 dentro de 1,5–4,0 (57m) o 1,2–3,5 (72f) y L120 < L(T\*).
- **Recongelamiento antes de filtrar:** definiciones, canalización y reglas de informe quedaron fijadas en `9601ce9` sin
  ningún conteo revisado; después se filtró desde cero.
- **Resultado:** sobreviven 72 de los mismos 1054 candidatos. Sigue siendo la región candidata restringida por la
  docencia: CANDIDATE, sin aprobar valores. Detalle en `docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md` y
  `docs/revision/P2I2_lactate_constraints.json`.
- **Digests:**
  - el paquete P2G no cambia, porque los módulos nuevos están excluidos de su digest;
  - el corte de P2I-1 se regeneró con números idénticos;
  - el congelamiento de calibración no cambia.
- **Gancho en tiempo de ejecución:** ninguno.

## 20. P2I-2P · Fisiología de la entrega y la extracción de O2 (2026-10-27)

- **Base:** `26ed9f5`. La docencia detuvo el refiltrado de P2I-2R y pidió revisar si el balance de O2 confundía:
  - la entrega (DO2);
  - la demanda metabólica (VO2);
  - la entrega crítica.
- **Defecto:**
  - la demanda es un VO2 medido en «unidades de la entrega que la satisface»;
  - esa entrega se usaba como la mínima adecuada (banda GI, FD-LAC) y como la normal (llegada neutra, P2F-6);
  - sin reserva de extracción ambas coinciden, y toda entrega bajo lo normal acumulaba deuda.
- **Corrección, en sombra:**
  - índice de entrega = DO2 / DO2 normal;
  - índice de demanda = VO2 / VO2 normal;
  - reserva ρ = E_máx / E_normal (`oxygen_extraction_reserve`, PROVISIONAL, TBD);
  - déficit efectivo = máx(0, demanda − ρ·entrega), que es lo único que D integra;
  - estados ADEQUATE, COMPENSATED y CRITICAL (`derived.oxygen_balance`).
- **Reserva canónica 1:**
  - es el modelo previo, sin ninguna cifra canónica cambiada;
  - el diff del golden GI son sólo las 4 líneas de metadatos del parámetro nuevo;
  - Contracts v2 sigue IDÉNTICO.
- **Hallazgo estructural:** a D y al lactato sólo llega el producto ρ × `arrival_delivery_ratio`.
  - Leída como fue diseñada (en unidades de la entrega crítica, re-anclada como relación / ρ), la banda GI conserva
    exactamente la dinámica actual.
  - Leída como DO2 sobre lo normal (fija), una reserva hace bajar el lactato sin tratar, en contra de FD-LAC-01/02.
  - Reserva y banda se deciden juntas.
- **Hallazgos de P2I-2R:**
  - L3 recuperándose bajo el umbral: REINTERPRETADO, como el estado en recuperación de FD-LAC-06;
  - entrega sin tratar muy baja: SIGUE PRESENTE, por el mapeo volumen → gasto y el colapso apagado;
  - índice tras transfusión de 1,1–2,2: REINTERPRETADO, porque está en unidades de la entrega crítica.
  - Las dos reinterpretaciones dependen de adoptar la banda re-anclada, una decisión docente pendiente.
- **Guardas:**
  - `lactate_slice.slice_run` rehúsa una reserva distinta de 1 sin la lectura de la banda declarada;
  - la bandera del recorte «sin crédito» (`shadow.acting_mechanisms`) usa ρ × entrega;
  - `faculty_constraints.adequate` queda congelada hasta el refiltrado.
- **Detalle:** sondas A–J, interfaz con el colapso y lectura propuesta de FD-LAC-01/06 en
  `docs/revision/P2I2P_FISIOLOGIA_ENTREGA_O2.md` y `docs/revision/P2I2P_oxygen_probes.json`.
- **Sin cambiar:**
  - no se volvió a filtrar: P2I-2R queda PENDIENTE DE REFILTRADO;
  - el colapso canónico GI sigue apagado;
  - no se aprobó ningún valor.
- **Digests:**
  - el paquete P2G y el corte P2I-1 se regeneraron con cifras idénticas, y su digest cambia por las fuentes del núcleo;
  - el congelamiento de calibración no cambia.
- **Gancho en tiempo de ejecución:** ninguno.

## 21. P2I-2Q · Plausibilidad hemodinámica antes del refiltrado del lactato (2026-10-27)

- **Base:** `dcf3c09`. La docencia aceptó P2I-2P:
  - la semántica del oxígeno;
  - los estados ADEQUATE, COMPENSATED y CRITICAL;
  - FD-LAC-06 por trayectoria neta, sin orden de reanimación;
  - ρ candidata 2,0–3,0 (2,5) con la banda re-anclada.

  Pidió auditar la cadena V → precarga → gasto → presión → DO2 → déficit → colapso antes de volver a filtrar.
- **Paquete de sólo lectura:**
  - sondas en `clinical_core/hemodynamic_probes.py`; informe en `docs/revision/P2I2Q_PLAUSIBILIDAD_HEMODINAMICA.md` y
    `docs/revision/P2I2Q_hemodynamic_probes.json`;
  - ninguna fisiología, valor por defecto, banda, registro ni golden cambia;
  - no se vuelve a filtrar.
- **Hallazgo:** V es un desplazamiento de la precarga efectiva en mL-eq; su escala viene de una conversión heredada.
  - La llegada GI queda a 359 mL-eq (57m) y 498 mL-eq (72f) del gasto cero.
  - El sangrado de 2,5 mL-eq/min la consume en 2 h.
  - Incluso la euvolemia llega al flujo cero tras unos 1000 mL-eq.
- **Clasificación:** PARAMETER_SCALE_CALIBRATION_ERROR. La forma de la curva cumple los requisitos; λ candidata
  1500–2000 mL-eq, para la docencia.
- **Colapso:** la señal recomendada es el déficit crítico normalizado, con dosis propia, sin D y sin exigir gasto bajo.
- **Estado mental:** debería leer el déficit crítico agudo, con D como persistencia; no se cambió.
- **Gancho en tiempo de ejecución:** ninguno.

## 22. P2I-2S · Restricciones de calibración de la escala hemorragia / precarga (2026-10-27)

- **Base:** `ae2ebf7`. La docencia aceptó P2I-2Q (error de escala, no de forma).
  - Fijó que V es una coordenada interna de precarga efectiva en mL-eq, no volumen de sangre.
  - Exigió un proceso hemorrágico coherente para V, la Hb, el gasto y el DO2.
  - Dejó λ 1500–2000 sin aprobar.
- **Paquete de sólo lectura:**
  - sondas en `clinical_core/haemorrhage_probes.py`; informe en `docs/revision/P2I2S_ESCALA_HEMORRAGIA_PRECARGA.md` y
    `docs/revision/P2I2S_haemorrhage_probes.json`;
  - ninguna fisiología, valor por defecto, banda, registro ni golden cambia;
  - no se vuelve a filtrar.
- **Hallazgos:**
  - **dos derivas independientes:** el sangrado, la transfusión y el cristaloide mueven V y la Hb con constantes heredadas
    propias. Para que un solo sangrado diera la caída de Hb harían falta 2,5–3,5 veces la pérdida de V, con un relleno
    implícito que no se modela;
  - **la dilución del cristaloide no se revierte** con la fuga.
- **Clasificación:** SHARED_HAEMORRHAGE_STATE_NEEDED. Se propone, sin implementar, un balance de volumen circulante con la Hb
  por mezcla, el relleno y un único mapeo V = κ × C.
- **λ es una convención de unidades:** V entra sólo como V/λ, y duplicar λ y todas las entradas de V no cambia nada.
  - Lo fisiológico son las razones sangrado/λ, unidad/λ y salino/λ, que hoy son los literales heredados, junto con p₀.
  - No se propone ninguna región de λ.
- **Cuadrícula de razones × posición:**
  - regiones excluidas sólo según el criterio de la sonda;
  - el resto requiere anclas docentes en términos de paciente: tolerancia al sangrado y respuesta a una unidad;
  - decidir el mapeo antes que las razones.
- **Transfusión:** el +82 % de L3 es la razón unidad/λ (0,36) actuando en una llegada infrallenada. No se corrige por
  separado.
- **Gancho en tiempo de ejecución:** ninguno.

## 23. P2I-2T · Estado hemorrágico compartido (2026-10-27)

- **Base:** `8c2aaea`. La docencia aceptó P2I-2S, con su clasificación SHARED_HAEMORRHAGE_STATE_NEEDED, y decidió que dos
  derivas independientes (`V -= fijo`, `Hb -= fijo`) no son aceptables. Informe:
  `docs/revision/P2I2T_ESTADO_HEMORRAGICO_COMPARTIDO.md`; sondas A–K: `clinical_core/blood_probes.py` y
  `docs/revision/P2I2T_blood_probes.json`.
- **Estado compartido mínimo** (`state.BloodState`, `CoreState.blood`):
  - acumulados de sangre perdida, glóbulos rojos perdidos, cristaloide que entra y que sale, transfusión (volumen y
    contenido) y relleno plasmático;
  - de ellos salen la desviación del volumen circulante C y el contenido de glóbulos rojos;
  - se normaliza con B0 = `arrival_circulating_volume_ml`, provisional 4000 mL-eq, que no es un litro medido.
- **Una sola fuente:** el módulo GI declara un flujo de sangre total (`blood_loss_ml_per_min`), modulado por el IBP y la
  hemostasia; el integrador le quita los glóbulos rojos con la composición actual. Desaparecen `hb_loss_g_dl_per_min`,
  `hb_dilution_g_dl_per_ml` y `hb_g_dl_per_unit`.
- **Hb y V:**
  - **Hb** = Hb de llegada × contenido × B0 / (B0 + C), por el acoplamiento `blood_composition`.
  - **V** = κ × C (κ provisional 1), renombrado «Effective circulating volume / preload coordinate (V)».
  - Sólo κ/λ es identificable desde la hemodinámica, y λ no se aprueba por separado.
- **Procesos:**
  - **relleno** (núcleo): meta 0,5 × lo perdido, capacidad 1000 mL-eq, τ 120 min, todos provisionales. Sólo actúa
    mientras la circulación está bajo la llegada, sin glóbulos rojos, sin pasar la meta y continuando tras el sangrado;
  - **cristaloide:** la cinética de fuga existente, como flujos; su dilución se revierte en parte;
  - **unidad de GR:** 300 mL-eq a 20 g/dL provisional, una sola representación.
- **Contabilidad** (`integration._check_blood`). Falla cerrado si:
  - un campo no cambia exactamente según sus procesos;
  - V no es κ × el volumen movido;
  - la Hb se mueve sin un cambio de contenido o volumen;
  - un registro no lleva los glóbulos rojos que da la composición.
- **Escrituras directas.** Ningún módulo, orden ni proceso logístico puede escribir V o Hb directamente; sólo las sondas
  declaradas, y lo que mueven queda contabilizado (`outside_v`, `outside_hb`).
- **Identidades.** V = κ × C + `outside_v` y Hb = composición + `outside_hb` se comprueban cada minuto y al comenzar o
  reanudar una corrida.
- **Guardas.** Si el estado sanguíneo alcanza las guardas de V o Hb, la corrida se detiene; la de V va en volumen
  circulante.
- **Llegada:** estado sanguíneo cero, sin inferir pérdida previa desde la Hb. La tasa del sangrado queda como
  CASE_OVERRIDES_FAMILY_DEFAULT probable, no aprobada (FD-22).
- **Artefactos:**
  - **golden GI:** regenerado con el antes / después completo. La Hb difiere del motor en todas las corridas; V,
    donde actúa el relleno;
  - **traza de Contracts v2:** lleva `core_blood_state`;
  - **Contracts v2:** sigue idéntico a la sombra directa;
  - **diferencia conocida P2I-2T:** nueva; KD-S3 queda `DORMANT`;
  - **congelamiento de calibración:** re-registrado con su motivo; las reglas no cambian;
  - **puerta de migración:** 11 bloqueos por caso;
  - **P2G y P2I-1:** regenerados. En P2G, FD-22 pasa a la tasa de sangre total y FD-23 se retira (48 abiertas);
  - **P2I-2R:** sigue PENDIENTE DE REFILTRADO, con su congelamiento;
  - **P2I-2P, P2I-2Q y P2I-2S:** quedan como registros históricos que no se regeneran.
- **Revisión adversarial:** 12 hallazgos, cada uno confirmado con una sonda.
  - Corregidos: F1–F4, F6, F7, F9, F11 y F12.
  - F8 y F10 quedan como limitaciones registradas.
  - F5 (la sonda de banda de nivel 2 con dos derivas, en el arnés congelado) queda pendiente de autorización.
- **Lectura:** con una sola fuente a 2,5 mL-eq/min la Hb apenas cae (0,09 g/dL en 2 h; la deriva heredada caía 1,08). Es
  una consecuencia de valores TBD (tasa, B0, relleno, retención del cristaloide); no se corrigió hacia el motor.
- **Gancho en tiempo de ejecución:** ninguno.

## 24. P2I-2U · Arnés de calibración alineado y anclas docentes del estado hemorrágico compartido (2026-10-27)

- **Base:** `94501f5`. La docencia aceptó y cerró P2I-2T, y confirmó:
  - SHARED_HAEMORRHAGE_STATE_NEEDED;
  - que la tasa independiente de Hb es obsoleta y que FD-23 queda retirada;
  - que la sonda de nivel 2 «GI bleed / trauma» no puede conservar las dos derivas.
  Informe: `docs/revision/P2I2U_ANCLAS_HEMORRAGIA_COMPARTIDA.md`; superficies: `clinical_core/blood_anchors.py` y
  `docs/revision/P2I2U_blood_anchors.json`.
- **Sonda F5:** pasa de V −10 mL/min y Hb −0,02 g/dL/min a un flujo sintético de sangre total (`bands.BloodLoss`,
  10 mL-eq/min) a través de `BloodState`, rotulada SYNTHETIC_CROSS_FAMILY_HAEMORRHAGE_PROBE. No escribe V ni Hb.
- **Recongelamiento:** sólo cambia `harness_sources` (`bands.py`, `calibration.py`). Las reglas no cambian y el motivo
  queda registrado en la prueba. El paquete P2G, el corte P2I-1 y las sondas de P2I-2T se regeneran con las mismas cifras.
  Las sondas de nivel 2 que todavía escriben V directamente (líquidos y fugas) marcan su Hb con «†»: esa Hb no sigue
  al volumen. Si deben pasar por `BloodState` queda abierto.
- **FD-23:** RETIRED — INVALIDATED BY SHARED HAEMORRHAGE STATE. Quedan 48 decisiones abiertas en P2G y 9 FD-BLD nuevas:
  57 en total.
- **Constantes internas:** B0, κ, λ, el relleno, la unidad de GR y la retención del cristaloide no se aprueban por
  separado; las acotan las anclas de paciente FD-BLD-01 a 09 y A–D. κ es sólo contabilidad (λ/κ). En P2G, FD-08,
  FD-14 y FD-15 ofrecen `preload_curve_scale_ml`: se leen como λ/κ y acotan la misma razón que FD-BLD-02 a 04, así que
  las respuestas se concilian; ninguna fija λ.
- **Superficies:**
  - sangrado sin tratar en 57m y 72f. Las corridas que se detienen se cuentan (n por minuto) y se resumen
    también con gasto 0;
  - una y dos unidades de GR. Que la segunda unidad rinda menos gasto es estructural: con la curva exponencial,
    Δ2/Δ1 = exp(−volumen de la unidad / (λ/κ)). No es un hallazgo;
  - 1 y 2 L de cristaloide con sangrado continuo;
  - relleno tras una pérdida aguda y tras la hemostasia;
  - comparación de políticas de autoridad para la tasa de sangrado: las tres pedidas más FAMILY_ALLOWED_RANGE,
    que lista P2G. Se evalúa CASE_OVERRIDES_FAMILY_DEFAULT como preferida, sin adoptarla y sin poblar registros;
  - identificabilidad: κ, λ y ρ no son identificables por separado.
- **Sin filtro FD-LAC:** el lactato sólo da contexto.
- **Gancho en tiempo de ejecución:** ninguno.
- **Revisión adversarial:** sin bloqueantes. Se corrigieron:
  - el sesgo de supervivencia en las anclas sin tratar;
  - las anclas de FD-BLD-04 y 05, que ahora coinciden con la evidencia mostrada;
  - la cuadrícula del cristaloide, que ahora recorre la posición de llegada;
  - la lectura de λ en P2G;
  - la Hb de las sondas que escriben V directamente, ahora marcada;
  - el resumen propio de las anclas;
  - la redacción.

## 25. P2I-2V · Anclas docentes aprobadas del estado sanguíneo compartido y filtro de la región candidata (2026-10-27)

- **Base:** `898b4d6` (P2I-2U, aceptado y cerrado). Informe: `docs/revision/P2I2V_ANCLAS_APROBADAS_FILTRO.md`.
  Código: `clinical_core/blood_constraints.py` (congelado) y `clinical_core/blood_filter_report.py` (sólo informe).
- **Decisiones aplicadas:**
  - las envolventes sin tratar de gasto y de caída de Hb de cada caso;
  - FD-BLD-01 a 09 FACULTY_APPROVED: conducta clínica o envolvente aprobada, con los parámetros ocultos sin aprobar;
  - la regla de la segunda unidad, sin aprobar la razón ~0,70;
  - FD-23 sigue retirada;
  - la categoría `CASE_OVERRIDES_FAMILY_DEFAULT` para la tasa de sangrado, declarada en
    `migration_authority.AUTHORITY_POLICIES` sin tasa ni valor de familia: la tasa sigue cerrando la migración.
- **Decisiones abiertas:** 48, las de P2G. FD-50 sigue abierta para los demás parámetros.
- **Congelamiento antes del filtro** (commit `3f86464`, resumen `cfb8e508…`):
  - fija las decisiones transcritas, las lecturas operativas, diez variantes declaradas de antemano, las reglas de
    identificabilidad y de representativos, y todas las fuentes de `clinical_core` salvo el informe;
  - la sensibilidad y las pruebas de humo usaron sólo puntos fuera de la cuadrícula;
  - el conteo se verificó contra fuerza bruta.
- **Recongelamiento de calibración:** cambian `migration_sources` y `authority_registries` (la política), con motivo
  registrado. Las reglas no cambian.
- **Resultado del filtro:** ningún candidato sobrevive, ni en el conjunto (3^15), ni por caso (3^13), ni en ninguna
  de las nueve variantes evaluadas. V5 quedó declarada pero sin implementar; su recuento sería 0 igualmente.
  - Lo decide la caída de Hb sin tratar: la mayor caída que alcanza 57m a los 60 min en toda la cuadrícula es
    0,189 g/dL, y la envolvente pide 0,2–0,5.
  - Sin esa restricción quedan 2241 candidatos conjuntos.
  - El diagnóstico de §5.7 del informe, rotulado como tal, muestra ese conjunto y sus representativos.
  - En 57m el conflicto entre la caída de Hb y el relleno de FD-BLD-07 es estructural. En 72f se debe al rango
    explorado: con tasas más altas y λ/κ mayor se cumplen ambas (exploración de revisión, no del filtro).
- **Identificabilidad:** no evaluable sin sobrevivientes. κ, λ y ρ siguen NON_IDENTIFIABLE_SEPARATELY.
- **Sondas de nivel 2 de líquidos:** se informan, no se convierten, porque la conversión ampliaría el alcance.
- **Sin filtro de lactato**, sin elección de parámetros ocultos y sin gancho en tiempo de ejecución.

## 26. P2I-2V-R · Restricciones del estado sanguíneo compartido revisadas y nuevo filtro (2026-10-27)

- **Base:** `7057cc9`. P2I-2V queda aceptado como filtro diagnóstico y como registro histórico, sin regenerar.
  Informe: `docs/revision/P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md`.
- **Revisiones aplicadas:**
  - U-HB FACULTY_APPROVED v2: sin caída mínima de Hb sin tratar, y la Hb no sube por la hemorragia misma;
  - FD-BLD-03 FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER: se informa, no filtra;
  - V5 implementada tal como se declaró;
  - tasa de sangrado común como lectura primaria; tasas por caso como sensibilidad (V8);
  - FD-BLD-07 sin cambios.
- **Sondas de nivel 2:** las cuatro que escribían V directamente quedan como `HISTORICAL_PROBE`, fuera del arnés
  activo. Cambia `harness_sources`, con el motivo registrado. Las comprobaciones de nivel 1 que escriben V siguen
  siendo reglas congeladas, fuera de este encargo.
- **Congelamiento antes del filtro:** commit `7c073ad`, resumen `a9ab10d8…`. Sólo se usaron puntos fuera de la
  cuadrícula, y la cuadrícula no cambió.
- **Resultado:**
  - 4896 sobrevivientes conjuntos con tasa común (6030 con tasas por caso).
  - U-HB v2 no acota; sí acotan U-OUT, FD-BLD-07, 05, 02, 01 y 06.
  - La posición de llegada queda en el borde superior de cada banda.
  - Según el diagnóstico de FD-BLD-03, 3402 sobrevivientes llegarían a la referencia euvolémica con una unidad, en
    al menos uno de los dos casos.
- **Sin elegir parámetros ocultos**, sin filtro de lactato y sin gancho en tiempo de ejecución.

## 27. P2I-2W · Extensión de los bordes abiertos y auditoría semántica del arnés (2026-10-27)

- **Base:** `ce1c0fb`. P2I-2V-R queda aceptado y cerrado: su filtro, su sensibilidad y su documento son su registro
  (`a9ab10d8…`), sin regenerar, y `blood_constraints.py` queda fijado byte a byte. Informe:
  `docs/revision/P2I2W_EXTENSION_BORDES_AUDITORIA.md`.
- **Qué se extendió:** sólo las dimensiones que P2I-2V-R señaló abiertas, por su lado superior:
  - la tasa común (10 y 20);
  - la meta del relleno (1,0; 1,25 queda fuera del dominio);
  - la τ del relleno (480 y 960);
  - la posición de 57m (0,65 y 0,8) y la de 72f (0,75 y 0,9).

  La regla sigue el paso de cada dimensión y no lee recuentos. La fracción retenida del cristaloide tiene una
  continuación ambigua: no se extendió y queda para la docencia.
- **Diseño disperso:** 43 cajas (42 con algún punto extendido) y 2 375 082 candidatos extendidos (menos del 5 % de la
  cuadrícula extendida):
  - la caja superviviente, que reproduce los 4896;
  - cada punto solo;
  - los diez pares;
  - la esquina de los primeros pasos.
- **Congelamiento antes de evaluar:** commit `6a0d3b8`, resumen `5257b233…`. Las filas ilegibles nunca cuentan como
  cota. Ningún candidato conjunto quedó ilegible; por caso, 1944 de 57m (tasa 10, 0,65) y 1836 de 72f (tasa 20, 0,9).
- **Resultado:**
  - **Tasa común:** 10 y 20 rechazadas por U-OUT en todo el diseño, sin que el relleno las rescate. Borde INTERIOR,
    2,5–5, sólo dentro del diseño: la terna «tasa 10, 57m 0,65 y 72f 0,75» no se evaluó. Con 10 y 20, la lectura
    sanguínea congelada se detiene (5514 filas ilegibles).
  - **Posición:** 0,8 (57m) y 0,9 (72f) rechazadas por U-OUT por arriba. 0,65 y 0,75 sobreviven sólo juntas (2268, con
    tasa 5 y λ/κ 833), dentro de la banda euvolémica y fuera de la banda POCUS de cada caso. Borde INTERIOR, con una
    interacción fuerte.
  - **τ del relleno:** 960 rechazada por FD-BLD-07; 480 sólo con la meta en 1,0. Borde INTERIOR.
  - **Meta del relleno:** 1,0 sobrevive (663 sola, 1512 con τ 480). Sigue OPEN_UPPER, en el límite de su dominio.
  - Las dimensiones no señaladas siguen OPEN_BOTH sin extender.
- **Estado de borde:** INTERIOR / OPEN_LOWER / OPEN_UPPER / OPEN_BOTH, aparte de la clase de identificabilidad
  congelada.
- **Nivel 1:** RR1, HR1–HR4, PL1–PL3, PL4 (V) y DM1 (Hb) quedan rotuladas como SYNTHETIC_STATE_PERTURBATION en
  `calibration.LEVEL1_DIRECT_WRITES`. Ninguna es una sonda de hemorragia, así que ninguna se convierte a BloodState.
  La variable de HR1–HR4 deja de llamarse `bleed`. Cambian los componentes `rules` y `harness_sources` del congelamiento
  de calibración; ninguna regla.
- **Sondas de bolo:** siguen históricas y fuera de toda evidencia y recuento.
- **Sin elegir parámetros ocultos**, sin cambiar restricciones, sin filtro de lactato y sin gancho en tiempo de
  ejecución.

## 28. P2I-2X · Cierre de los bordes de verdad del caso y de dominio, y tasa densificada (2026-10-28)

- **Base:** `20fdcbe`. P2I-2W queda aceptado y cerrado como registro (`5257b233…`), sin regenerar. Informe:
  `docs/revision/P2I2X_CIERRE_BORDES_TASA.md`.
- **Verdad del caso:** la posición de llegada debe quedar en la banda candidata comprometida de cada caso, que fundan
  las líneas POCUS (57m 0,2–0,5; 72f 0,3–0,6). No se endurece ni se infiere un número exacto. 0,65 / 0,75 (y 0,8 /
  0,9) quedan `REJECTED_BY_CASE_TRUTH_COMPATIBILITY`, junto con los 2268 sobrevivientes de P2I-2W que las usaban. La
  terna «tasa 10, 57m 0,65, 72f 0,75» no se evaluó, porque ya no responde la pregunta clínica.
- **Congelamiento antes de evaluar:** commit `7f61e2e`, resumen `668bad99…`. Tasas 5–10, nuevas 6, 7, 8 y 9.
- **Diseño:** la región superviviente de P2I-2V-R, en sus posiciones compatibles. Un prefiltro exacto aplica las
  restricciones que no dependen de la tasa y rechaza 45 036 de 52 488 combinaciones sin simular.
- **Resultado:**
  - sobrevivientes conjuntos: 5 → 2268, 6 → 1512, y 0 con 7, 8, 9 y 10;
  - FACULTY-CONSTRAINED BLEED-RATE CANDIDATE INTERVAL: el límite queda entre 6 y 7, y lo pone U-OUT en 57m. Es
    condicional a la región de P2I-2V-R (meta ≤ 0,75; τ ≤ 240) y a la posición en el borde superior de la banda;
  - las otras posiciones de la banda no abren ninguna tasa.
- **Bordes:** taxonomía con DOMAIN_* y CASE_TRUTH_BOUND, aparte de la clase:
  - meta del relleno: DOMAIN_UPPER_BOUND (1,0 es el límite exacto del núcleo);
  - posición: CASE_TRUTH_BOUND, no identificada;
  - tasa y τ: INTERIOR;
  - cristaloide: OPEN_UPPER.
- **Cristaloide:** `effective_ml_per_ml` es la fracción intravascular inicial; FD-BLD-04 y 05 leen la retenida. Se
  propone una grilla interpretable (f₀, f∞, τ), sin evaluarla.
- **Deuda registrada (TD-88):** `blood_filter_report.py` también calcula el diagnóstico histórico de P2I-2V, aunque
  figura como informe de sólo presentación; hay comentarios inexactos en archivos congelados.
- **Nivel 1 y HR1:**
  - SYNTHETIC_STATE_PERTURBATION confirmada, y `NOT_EVIDENCE_FOR` con la lista docente;
  - los rechazos de P2F por HR1 quedan como STRUCTURAL_HARNESS_OUTCOME, sin readmitir nada;
  - 0,2 en 57m sigue excluida por FD-BLD-02, en la cuadrícula explorada de P2I-2V-R.
- **Higiene de resúmenes:** los informes de P2I-2V-R, P2I-2W y P2I-2X salen del corte P2I-1 (y por tanto de las
  sondas P2I-2T y las anclas P2I-2U), con una prueba de que ningún otro módulo los importa.
- **Sin elegir parámetros ocultos**, sin cambiar restricciones, sin filtro de lactato y sin gancho en tiempo de
  ejecución.

## 29. P2I-2Y · Superficie de calibración del cristaloide y robustez de la tasa de sangrado (2026-10-28)

- **Base:** `d233e27`. P2I-2X queda aceptado y cerrado como registro (`668bad99…`), sin regenerar. Informe:
  `docs/revision/P2I2Y_CRISTALOIDE_Y_TASA.md`; números: `docs/revision/P2I2Y_blood_fluid_calibration.json`.
- **Registro docente de la tasa:** TESTED_VIABLE_RATE_REGION = {5, 6}; FIRST_TESTED_NONVIABLE_RATE = 7. No es una tasa
  aprobada y no se densificó entre 6 y 7.
- **Congelamiento antes de evaluar:** commit `5ae6d70`, resumen `67e5b80a…`. Incluye el diseño de robustez, la grilla,
  las restricciones y las reglas de bordes.
- **Robustez de la tasa:**
  - **Diseño:** tasas 5, 6 y 7, cruzadas con la meta {0,5; 0,75; 1} y τ {120; 240; 480}, es decir, 9 pares (5
    nuevos). El resto de la sangre va en sus valores supervivientes de P2I-2V-R, en las posiciones compatibles de cada
    caso. Son 118 098 conjuntos compartidos; el prefiltro exacto de P2I-2X rechaza analíticamente 338 256 candidatos
    de 57m y 337 770 de 72f.
  - **Resultado:** sobreviven en conjunto 3423 con 5, 2268 con 6 y 0 con 7, con 0 ilegibles.
    - La tasa 6 conserva sus dos pares y gana 1|480.
    - 57m falla U-OUT con 7 en todas sus combinaciones.
  - **Conclusión: ROBUST_BOUNDARY.** Es condicional a la región de P2I-2V-R, a la banda compatible y a los puntos
    explorados. El límite lo pone U-OUT, que no lleva bolsa, así que no depende del cristaloide.
- **Cristaloide:**
  - **Superficie F0 / Finf / τ** (fracción circulante efectiva inicial, retenida a largo plazo y constante de
    redistribución):
    - se mapea exacto a `effective_ml_per_ml = F0`, `transient_share = 1 − Finf/F0` y `leak_tau_min = τ`;
    - Finf > F0 queda `ANALYTIC_REJECTION` (3 de 75).
  - **Filtro, sin cambiar FD-BLD-04, 05 ni 06:** quedan 54 con FD-BLD-04 y 17 con FD-BLD-05.
    - **Primario: 17 puntos (15 bolsas)**, con F0 0,15–0,35, Finf 0–0,15 y τ 15–60.
    - **Robusto: 3**, con F0 0,2, Finf 0,05–0,1 y τ 30–60.
    - **Aislado: 15.**
  - **FD-BLD-06 separa por B0:** la bolsa de menor F0 (aporte inicial 0,15) diluye de menos con B0 5000, y las de F0 ≥ 0,25 diluyen
    de más con B0 3000.
  - **Sin producto completo con la sangre:** el primario es igual a FD-BLD-04 ∧ 05 y no puede cambiar. Hay dos
    verificaciones posteriores al congelamiento, fuera de la inferencia; las dos dan los mismos 3 robustos:
    - una de la sesión, en el scratchpad: 17 puntos con las 45 claves certificadas de las tasas 5 y 6;
    - una prueba comprometida: los 3 robustos con esas 45 claves y con las 36 de la región de P2I-2V-R con tasa 2,5.
- **Bordes:**
  - F0 sólo queda acotado en el criterio robusto (0,2, interior).
  - Finf tiene el lado inferior en DOMAIN_LOWER_BOUND.
  - τ queda abierto: en el primario, a ambos lados; en el robusto, en el borde superior.
  - Nada se llama «identificado» por estar en un borde de la grilla.
- **Trayectorias y estado** (sólo contexto):
  - el aporte inicial va de 0,15 a 0,30 y la dilución pico con 1 L, de 0,23 a 0,46 g/dL;
  - la misma bolsa sube el gasto mucho más en la posición inferior que en la superior (con 1 L, entre 2 % y 49 %);
  - no se calibra ninguna regla fija de 1 L → X %.
- **Lactato:** el refiltrado futuro debe regenerarse desde la fisiología actual (BloodState compartido, DO2 y
  extracción corregidas, región de sangre docente, superficie del cristaloide y precarga compatible). No debe reutilizar
  la región histórica de P2F de 1054 conjuntos.
- **Sin elegir parámetros ocultos**, sin cambiar restricciones, sin filtro de lactato y sin gancho en tiempo de
  ejecución. TD-88 sigue abierta.

## 30. P2I-2Z · Borde de τ del cristaloide y preparación del lactato con la fisiología actual (2026-10-28)

- **Base:** `5c949d6`. P2I-2Y queda aceptado y cerrado como registro (`67e5b80a…`); su prueba de congelamiento pasa a
  fijar el módulo byte a byte y el resumen del registro. Informe: `docs/revision/P2I2Z_TAU_Y_PREPARACION_LACTATO.md`;
  números: `docs/revision/P2I2Z_blood_fluid_readiness.json`.
- **Decisiones docentes:**
  - la tasa queda ROBUST_BOUNDARY ({5, 6}; 7), información candidata, sin volver a simularla;
  - la región ROBUST de P2I-2Y es la base candidata preferida del cristaloide;
  - Finf < F0 para los candidatos activos del cristaloide isotónico estándar: Finf = F0 queda REFERENCE_ONLY.
- **Congelamiento antes de evaluar:** commit `a927301`, resumen `e89a248e…`. Incluye el diseño, la regla, el criterio
  robusto, la regla de parada, las comprobaciones estructurales, los criterios de preparación y las reglas del espacio
  de entrada.
- **τ:** F0 0,2 × Finf {0,05; 0,1} × τ {60; 90; 120}, con τ 60 reproduciendo P2I-2Y.
  - FD-BLD-06 se lee en 48 claves de sangre (las 14 sondas de P2I-2Y y las 45 claves certificadas de las tasas 5 y 6),
    en los dos casos.
    - Es exhaustivo sólo sobre las 5 claves que lee FD-BLD-06, no el producto con los 5691 conjuntos de sangre.
    - Son 576 filas: una interpretación declarada de «estados representativos y de borde».
  - **Resultado:** los 6 puntos son robustos y τ 120 sobrevive: τ queda **OPEN_UPPER_GRID_EDGE** y la extensión se
    detiene a la espera de la docencia.
  - **Región candidata:** 7 puntos, con F0 0,2, Finf 0,05–0,1 y τ 30–120.
- **Comprobaciones estructurales, en 6 estados fijos:**
  - la cinética del lactato y la de la deuda no mueven la hemodinámica;
  - la frecuencia intrínseca no mueve nada de lo que se lee;
  - ρ se cancela en D y en el lactato con la banda re-anclada, y sólo mueve el índice de entrega que lee la adecuación.
- **Preparación: NOT_READY**, con un único bloqueo: la región del cristaloide tiene el lado superior de τ abierto. Los
  otros seis criterios se cumplen.
- **Espacio de entrada del lactato:** queda como borrador, sin ejecutar y sin la región de 1054 de P2F.
  - Se preparó aunque el veredicto es NOT_READY: es una desviación declarada, y la docencia decide si queda.
  - Recuentos: de 1 020 600 a 10 333 575 candidatos.
  - Diseño factorizado: de 2880 a 13 770 simulaciones del núcleo, contra 18 a 186 millones con el producto ingenuo.
  - Los mínimos son holgados: el mínimo ajustado da al menos 1 913 625 candidatos y 3510 simulaciones.
- **Prueba permanente:** no se agrega; la comprobación de 17 × 45 del scratchpad fue corroborativa.
- **Dependencias:** la carga transitiva viene del arnés de sangre, que usa esos módulos; quitar la importación directa
  no descarga nada. Queda registrada como deuda (TD-89).
- **Sin elegir parámetros ocultos**, sin filtro de lactato y sin gancho en tiempo de ejecución. TD-88 sigue abierta.

## 31. P2I-2AA · Cierre del borde de τ del cristaloide y semántica de la preparación del lactato (2026-10-28)

- **Base:** `a109c19`. P2I-2Z queda aceptado y cerrado (`e89a248e…`), con su NOT_READY; su prueba de congelamiento
  fija el módulo byte a byte y el resumen del registro. Informe: `docs/revision/P2I2AA_CIERRE_TAU_Y_SEMANTICA_LACTATO.md`;
  números: `docs/revision/P2I2AA_blood_fluid_tau_closure.json`.
- **Decisiones docentes registradas, sin aplicarlas a ningún filtro:**
  - la adecuación del oxígeno para el lactato es déficit efectivo = 0 (ADEQUATE y COMPENSATED), sin exigir la entrega
    normal;
  - el futuro espacio del lactato incluye las tasas 2,5, 5 y 6;
  - los modificadores de L3 (0,8 y 0,1) quedan FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS y
    FACULTY_DECISION_PENDING (FD-24 y FD-25), sin rango inventado.
- **Congelamiento antes de evaluar:** commit `83996c5` (resumen `263efaba…`).
  - La revisión adversarial probó que omitía, para la tasa 2,5, los sobrevivientes de las cajas de P2I-2W dentro de
    la banda (meta 1,0: 264; meta 1,0 con τ 480: 756).
  - Se recongeló en `0b90ddf` (resumen `5087cf02…`) sin cambiar el diseño de τ ni ninguna regla, y todo lo de τ se
    reprodujo idéntico.
- **τ:** F0 0,2 × Finf {0,05; 0,1} × τ {120…240}; τ 120 reproduce P2I-2Z.
  - Con Finf 0,1 sobreviven 120 y 150; desde 180 falla FD-BLD-05 a los 120 min.
  - Con Finf 0,05 sobrevive hasta 240, con un margen de 0,005.
  - Resultado: **TAU_REMAINS_OPEN_AT_240**, y la extensión se detiene.
- **Identificabilidad práctica: CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN.** El límite τ → ∞ (Finf = F0) falla
  FD-BLD-05, así que existe una cota finita más allá de 240. Dentro del horizonte, Finf y τ se confunden: lo que acotan
  las restricciones es la curva de lo retenido.
- **Soporte del cristaloide:** 12 puntos, con F0 0,2, Finf 0,05–0,1 y τ 30–240.
  - Todos pasan FD-BLD-06 en las 63 claves de la tasa 2,5.
  - La sustitución no omite ninguna de las 387 claves exploradas.
- **Preparación: NOT_READY**, con un único bloqueo: el soporte del cristaloide, porque τ queda abierto con una
  restricción que depende de una cota más allá de 240. Los otros siete criterios se cumplen.
- **Espacio de origen del lactato:** DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY, protegido por
  `certified_input`.
  - La tasa 2,5 aporta 3648 conjuntos (P2I-2V-R y P2I-2W).
  - Recuentos: de 1 754 460 a 14 171 760 candidatos.
  - Diseño factorizado: de 2308 a 14 256 trayectorias hemodinámicas únicas, contra 94,7 a 765 millones de
    simulaciones del producto ingenuo.
- **Sin elegir parámetros ocultos**, sin filtro de lactato y sin gancho en tiempo de ejecución. TD-88 y TD-89 siguen
  abiertas.

## 32. P2I-2AB · Reconstrucción del lactato GI con la fisiología actual (2026-10-28)

- **Base:** `4d45757`. P2I-2AA queda aceptado y cerrado (`5087cf02…`); su prueba de congelamiento fija el módulo byte a
  byte y el resumen del registro. Informe: `docs/revision/P2I2AB_RECONSTRUCCION_LACTATO.md`; números:
  `docs/revision/P2I2AB_lactate_rebuild.json`.
- **Decisión docente:** el borde abierto de τ no bloquea. La preparación pasa a
  READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY; τ no se aprueba y los 12 puntos del
  cristaloide se propagan sin un τ preferido. La adecuación es déficit efectivo = 0, y FD-LAC-01 y 06 admiten la caída
  del lactato con un déficit crítico en recuperación.
- **Congelamiento antes de evaluar:**
  - `e234a54`: su propia comprobación detuvo la corrida dentro de la fuente de sangre, antes de cualquier lactato.
    Comparaba las tres posiciones con un conteo de P2I-2W que sólo exploró la superior.
  - Recongelamiento en `68b92de` (resumen `15d05c32…`): cada conteo certificado se compara donde se exploró; no cambió
    ninguna regla FD-LAC, ningún rango ni el orden del filtro.
- **Espacio de origen, sólo con la fisiología actual (la guarda impide leer la región de P2F):**
  - 87 conjuntos P1 y 458 conjuntos P3, con las tasas 2,5, 5 y 6;
  - 12 puntos del cristaloide y 1215 puntos del lado del lactato: 6 677 640 candidatos (×3 con ρ);
  - reproduce exactamente 3648, 3423 y 2268 conjuntos certificados;
  - con la tasa 2,5 y el relleno (1; 480) entran también las posiciones medias (0,35 / 0,45), que nadie había
    explorado y cumplen todas las restricciones de sangre vigentes.
- **Factorización:**
  - 3178 trayectorias del núcleo, contra 40 millones de corridas ingenuas;
  - 720 corridas completas coinciden exactamente con ρ 2,5, y con ρ 1 y 3 dentro de 7e-15 y con los mismos
    veredictos.
- **Filtro (L1 → L3 → L2):**
  - 439 291 sobrevivientes (6,6 %);
  - L1 rechaza 5 551 008, sobre todo por FD-LAC-02 en 57m;
  - L3 rechaza 558 936, sobre todo por FD-LAC-05;
  - L2 rechaza 128 405, por FD-LAC-06 en 57m;
  - ANALYTIC_REJECTION 0 y ninguna trayectoria detenida.
- **Sesgo de supervivencia:**
  - el 69 % de los sobrevivientes cumple FD-LAC-04/05 como NOT_EVALUABLE en al menos un caso; todos tienen la entrega
    de llegada inferior, con la que 2 unidades y la hemostasia no devuelven el déficit a 0 dentro de 120 min;
  - 135 115 (30,8 %) las cumplen evaluadas en los dos casos (cálculo posterior, fijado por una prueba);
  - el 16 % tiene una caída sostenida del lactato con déficit crítico persistente después de la hemostasia, que
    FD-LAC-06 no juzga.
- **Identificabilidad:**
  - ninguna dimensión queda bien acotada;
  - G × g y el par de llegada quedan parcialmente acotados;
  - τ_D, τ_L, el exceso y la sangre quedan mal identificados, con los bordes abiertos;
  - g y G, y ρ, no son identificables por separado;
  - sobreviven los 12 puntos del cristaloide.
- **Revisión adversarial:** sin BLOCKER. Su hallazgo MAJOR, la sensibilidad a la demanda basal, se informa como cálculo
  posterior: con ×0,9 sobreviven 274 960 y con ×1,1, 674 108; queda como decisión docente. Los detalles de código sin
  efecto en el registro quedan como TD-90.
- **Veredicto: LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED**, según la regla congelada. Las salvedades y las decisiones
  docentes están en el informe (§7.1 y §14). Próximo dominio recomendado, sin empezar: la calibración de la presión y
  la FC.
- **Sin elegir parámetros ocultos**, sin calibrar la presión ni la FC, sin colapso, sin migración y sin gancho en tiempo
  de ejecución. TD-88 y TD-89 siguen abiertas.

## 33. P2I-2AC · Deuda de oxígeno acumulada y adecuación de la reanimación L3 (2026-10-28)

- **Base:** `37e5df6`. P2I-2AB queda aceptado como reconstrucción técnicamente válida; su módulo y su registro
  (`15d05c32…`) quedan fijados por sus pruebas. Informe: `docs/revision/P2I2AC_DEUDA_Y_ADECUACION_L3.md`; números:
  `docs/revision/P2I2AC_lactate_adequacy.json`.
- **Decisiones docentes:**
  - D es deuda de entrega de O2 acumulada: con déficit > 0 no baja; sólo se devuelve, con τ_D, sin déficit;
  - L3_RESUSCITATION_ADEQUACY: la adecuación sostenida empieza a más tardar en el minuto 90; si no, es un rechazo
    propio, nunca un fallo de FD-LAC-04;
  - el sangrado en curso se lee por flujo real; tras la hemostasia el sangrado residual conserva la protección de
    FD-LAC-06;
  - la demanda 0,9 / 1,0 / 1,1 es incertidumbre informada, no un filtro;
  - ρ: banda 2,0–3,0 con 2,5 representativo, y 1 sólo como referencia sintética; no se cuenta;
  - FD-LAC-04 y 05 sin cambios.
- **Núcleo:**
  - corrección mínima en `integration._oxygen_debt`, con 7 invariantes (`test_clinical_core_debt_semantics.py`);
  - golden, paquete, corte, sondas y anclas regenerados; Contracts v2 IDENTICAL.
- **Congelamiento antes de evaluar:** `2a9129e`, un solo commit. La factorización se validó antes: 936 corridas
  completas, exactas con ρ 2,5 y demanda 0,9 / 1,0 / 1,1, y dentro de 2,1e-14 con ρ 1, 2 y 3.
- **Auditoría de P2I-2AB:**
  - las 71 661 caídas tras la hemostasia violarían FD-LAC-06 con el sangrado leído por flujo real;
  - con la D corregida, sólo 120 sobrevivientes de P2I-2AB lo harían.
- **Filtro (demanda 1,0):**
  - 345 490 sobrevivientes (5,2 %);
  - la adecuación L3 rechaza sola 375 720 candidatos;
  - frente a P2I-2AB se mantienen 42 225, salen 397 066 y entran 303 265;
  - ANALYTIC_REJECTION 0.
- **Región:**
  - todos los sobrevivientes recuperan la adecuación en el minuto 60 y pasan FD-LAC-04;
  - FD-LAC-05 queda NOT_EVALUABLE en 1512 sobrevivientes de 72f, porque la adecuación se pierde antes de los 120 min
    con el sangrado residual; 1008 de ellos tienen L120 sobre la envolvente.
- **Demanda:** de la región, 71 079 candidatos son ROBUST y 274 411 DEMAND-SENSITIVE. Sobreviven 404 371 con ×0,9 y
  367 703 con ×1,1.
- **Identificabilidad:** la D corregida no la mejora. G × g pasa a mal identificado y ninguna dimensión queda bien
  acotada; ρ es invariante.
- **Representativos:** D nunca baja con déficit leído por el núcleo; sin marcas de inverosimilitud.
- **Veredicto: LACTATE_PHYSIOLOGY_NOT_READY** — FD-LAC-04/05 se cumplen sólo como NOT_EVALUABLE en algunos
  sobrevivientes (los 1512 de 72f). No se recomienda ni se empieza otro dominio.
- **Revisión adversarial:** sin BLOCKER. Su hallazgo MAJOR, que la nueva D cambia la FC y la FR en L1 (hasta +31,8
  lpm y +10,4/min, con la entrega idéntica), queda informado; el rechazo HR1 de P2F ya no se reproduce en vivo. El
  retardo de inicio (27,7 % de la región) y los textos que suponían el estado estacionario de D quedan en el informe y
  en TD-91.
- **Sin elegir parámetros ocultos**, sin calibrar la presión ni la FC, sin colapso, sin migración y sin gancho en tiempo
  de ejecución. TD-91 registra la memoria de deuda de FD-LAC-05, la clase heredada de la deuda de llegada y los textos
  congelados que la nueva D dejó desactualizados.

## 34. P2I-2AD · Cierre semántico de D y del lactato (2026-10-29)

- **Base:** `1c01884`. P2I-2AC queda aceptado como análisis diagnóstico; la docencia coincide con su NOT_READY. Su
  módulo y su registro (`fc49efae…`) quedan fijados por sus pruebas. Informe:
  `docs/revision/P2I2AD_CIERRE_DEUDA_LACTATO.md`; números: `docs/revision/P2I2AD_lactate_closure.json`.
- **Decisiones docentes:**
  - la adecuación L3 persiste hasta 120; si se pierde, L3_RESUSCITATION_LOST, un rechazo propio y nunca un fallo de
    FD-LAC-05 ni un NOT_EVALUABLE que pase;
  - D sólo se devuelve en un minuto sin déficit al inicio ni al final;
  - τ_D no define la producción de lactato: hay una ganancia D → lactato propia;
  - el cambio de FC y FR se acepta como propagación causal, con las magnitudes pendientes;
  - la demanda 0,9 / 1,0 / 1,1 sigue como incertidumbre; ρ no se cuenta; FD-LAC-01..06 sin cambios.
- **Núcleo:**
  - `integration._no_repayment_across` y `debt_to_lactate_gain` (2 / 3600 por defecto, provisional);
  - G ya no llega al núcleo;
  - 8 invariantes de D y 4 pruebas de acople;
  - golden, paquete, corte, sondas y anclas regenerados; Contracts v2 IDENTICAL.
- **Rango de k:** el de G queda OLD_G_RANGE_SEMANTICALLY_INVALID. El nuevo se construyó antes de cualquier conteo,
  sólo con dimensiones, envolventes y sondas sintéticas: de 2,78e-5 a 2,17e-3, cinco puntos, cruzados con τ_D.
- **Congelamiento antes de evaluar:** `c9647c8`, un solo commit. Antes se validó la factorización (936 corridas
  completas exactas) y la suite del núcleo dio 913/913.
- **Cruce de umbral:** en la región de P2I-2AC, los 95 698 candidatos con entrega de llegada superior (27,7 %)
  pasaban hasta 63 minutos críticos bajo su D de llegada; con la D nueva, ninguno.
- **Filtro (demanda 1,0):**
  - 353 302 sobrevivientes de 11 129 400;
  - L3_RESUSCITATION_INADEQUATE rechaza sola 377 844 (379 320 con los que sólo tienen LOST);
  - L3_RESUSCITATION_LOST rechaza 9396 de 72f (1476 sólo por eso);
  - ANALYTIC_REJECTION 0.
- **Región:**
  - todos los sobrevivientes mantienen la adecuación desde T* = 60 hasta 120;
  - FD-LAC-04/05 pasan evaluadas en todos; ningún NOT_EVALUABLE.
- **Demanda:** 63 859 ROBUST_ACROSS_DEMAND y 289 443 DEMAND_SENSITIVE.
- **Identificabilidad:** sin mejora; g, k y D0 sólo llegan como k × g y k × D0. El borde superior de k queda abierto.
- **Representativos:** D nunca se devuelve en un intervalo crítico; sin marcas de inverosimilitud.
- **Veredicto: LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN.** Próximo dominio recomendado, sin empezar: FC y respuesta
  simpática, después presión y tono vascular.
- **Revisión adversarial:** sin BLOCKER.
  - Su MAJOR: el impulso simpático todavía lee D / τ_D, así que τ_D fija la ganancia D → FC. Es del dominio de la
    FC: queda informado y en TD-92.
  - Sus MINOR y NIT quedan en el informe, TD-91 y TD-92:
    - la escala del rango de k sale de la banda candidata de la deuda de llegada, y la región queda truncada arriba
      en k;
    - G sigue rotulado en los documentos históricos;
    - la procedencia con D = 0.
  - Se agregó una prueba de equivalencia con el núcleo para una unidad L3_RESUSCITATION_LOST.
- **Sin elegir parámetros ocultos**, sin calibrar la FC, la FR ni la presión, sin colapso, sin migración y sin gancho
  en tiempo de ejecución. TD-91 queda parcialmente resuelta, con un punto nuevo sobre G en los módulos históricos.

## 35. P2I-2AE · Estructura de la FC y de la respuesta simpática (2026-10-29)

- **Base:** `e0dffa8`. P2I-2AD queda aceptado (LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN) y cerrado: su módulo y su
  registro (`5cb48163…`) quedan fijados por sus pruebas. Informe: `docs/revision/P2I2AE_ESTRUCTURA_FC_SIMPATICA.md`;
  números: `docs/revision/P2I2AE_hr_structure.json`.
- **Decisiones docentes:**
  - τ_D es sólo devolución de D y no define el impulso simpático (TD-92);
  - FC de llegada = intrínseca + contribución simpática no negativa;
  - sin decremento de FC propio de GI; la FC heredada no es objetivo; el rechazo HR1 de P2F no es evidencia;
  - el lactato sigue cerrado.
- **Auditoría (antes de cambiar código):**
  - la vía `sympathetic_per_debt × (D − D0) / τ_D` era SEMANTIC_LEAK;
  - la devolución de D por τ_D sigue siendo VALID_CAUSAL_PATH;
  - el rango de `sympathetic_per_debt`, el rechazo HR1 con τ_D 30 y las tablas históricas son LEGACY_ARTIFACT;
  - no hay término del déficit efectivo instantáneo (A no; B, D acumulada, sí); el estímulo agudo existente es el
    déficit de presión, relativo a la llegada. No se agregó ningún término.
- **Núcleo:**
  - el impulso por deuda es `debt_to_sympathetic_gain × D` (1/120 por defecto = 0,5/60, provisional, nunca derivado
    de τ_D); `sympathetic_per_debt` ya no se lee;
  - el impulso de llegada se separa en la parte de la deuda (ganancia × D0) y el resto (`arrival_non_debt_drive`);
    una llegada que pediría una contribución negativa detiene el núcleo;
  - con el perfil por defecto las trayectorias no cambian: el golden sólo cambia en la metadata y Contracts v2 da
    IDENTICAL;
  - el núcleo rechaza 108 de los 1054 candidatos P2F (72f con intrínseca 100 y deuda 60) a la ganancia por defecto.
    El paquete P2G y el corte P2I-1 los leen sin impulso por deuda: el impulso no llega al lactato, la presión ni la
    FR, así que esos números son los anteriores. La FC de P2G los deja fuera (corrección tras la revisión, F1);
  - el rechazo HR1 con τ_D 30 × deuda superior ya no se reproduce.
- **Banda intrínseca 60 / 80 / 100:** STILL_VALID_CANDIDATE_RANGE (rango de reposo del adulto, no derivado de HR1).
- **Rango de la ganancia:** el de `sympathetic_per_debt` queda OLD_SYMPATHETIC_PER_DEBT_RANGE_SEMANTICALLY_INVALID. El
  nuevo se fijó antes de cualquier resultado, sólo con dimensiones, la FC de llegada, la banda intrínseca, la escala
  de D y la regla de no negatividad: de 6,67e-4 a 0,128, cinco puntos logarítmicos y 0 como referencia sintética.
- **Congelamiento antes de evaluar:** `6052ffb`, un solo commit.
  - Antes, una comprobación técnica corrió la reconstrucción de la FC en las 18 corridas: 90 recorridas exactas, sin
    leer ningún resultado de FC. La prueba congelada valida además una fisiología fuera de la grilla.
  - Las mismas 90 recorridas forman parte de la evaluación.
  - Tras la revisión, la corrección F1 tocó sólo módulos históricos (`decision_pack`, `lactate_slice`, el informe de
    P2G). `hr_structure.py` y el núcleo quedan idénticos a `6052ffb`: cambia el hash de fuentes del digest, no el
    diseño, y la evaluación se volvió a correr con el mismo resultado.
- **Evaluación** (análisis, después 1-D y el plano 3 × 6 post-procesado, sin barrido cartesiano):
  - 18 corridas representativas, 90 recorridas de validación (todas exactas);
  - D, lactato, déficit y gasto idénticos al registro P2I-2AD;
  - 17 de 108 descomposiciones de llegada con ANALYTIC_REJECTION, exactamente las que el núcleo rechaza;
  - las diez direcciones se cumplen; ninguna bandera estructural;
  - la FR no cambia.
- **Identificabilidad:** NON_IDENTIFIABLE para la intrínseca y la ganancia por separado. Por encima del piso la
  intrínseca se cancela; sólo ganancia × g y ganancia × D0 llegan a la FC; no hay techo de FC.
- **Veredicto: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION.** Siguiente paso recomendado, sin empezar: un
  paquete pequeño de calibración numérica de la FC con la docencia. Debe decidir:
  - la intrínseca y la ganancia;
  - si hace falta techo o saturación (en el extremo superior del rango, 244 / 217 lpm a los 120 min sin tratamiento);
  - si el resto de llegada debe resolverse con la entrega restaurada (hoy sólo lo baja la presión; tras el manejo
    definitivo la FC queda en 99–120 / 91–109 lpm). Esto necesitaría un término o una referencia nuevos con su rango;
  - si acepta la escala de D (banda de deuda de llegada) de la que salen los extremos del rango (TD-93(6)).
  La presión y el tono vascular siguen a la FC.
- **Sin elegir parámetros ocultos**, sin calibrar la FC, la FR ni la presión, sin colapso, sin migración y sin gancho
  en tiempo de ejecución.
- **Revisión adversarial (una):** sin BLOCKER.
  - MAJOR F1 (ejecutable), corregido: la exclusión de las 108 llegadas cambiaba los resúmenes históricos de lactato,
    presión y FR. Ahora esos candidatos se leen sin impulso por deuda.
  - MAJOR F2 (latente), declarado en TD-93(5) y fijado por una prueba: una llegada no sinusal o con betabloqueo
    completo y D0 > 0 se rechaza siempre.
  - MAJOR F3 (metodológico), declarado en TD-93(6): la escala de D del rango sale de la banda de deuda de llegada.
  - MINOR, declarados en TD-93(7)–(8): guardas tautológicas y `sympathetic_per_debt` en tablas históricas.
  - NIT, corregidos en los documentos: 91–109 lpm, orden de secciones y alcance de la validación en el extremo
    superior.

## 36. P2I-2AF · Impulso agudo del shock y saturación suave de la FC (2026-10-29)

- **Base:** `b8551d2`. P2I-2AE queda aceptado como auditoría estructural de la FC y desacople de τ_D, y cerrado: su
  módulo y su registro (`1b65d303…`) quedan fijados por sus pruebas. Es el último paquete estructural de la FC.
  Informe: `docs/revision/P2I2AF_SHOCK_AGUDO_Y_SATURACION_FC.md`; números: `docs/revision/P2I2AF_hr_shock.json`.
- **Decisiones docentes:**
  - la parte de shock de la FC de llegada se genera desde el estado actual y se resuelve con el shock: sin
    desplazamiento fijo por caso;
  - la señal aguda es el déficit efectivo de oxígeno sobre la demanda, sin referencia absoluta de presión;
  - el término de presión relativa: el texto registrado dice «puede quedarse si no cuenta dos veces» y el encargo pide
    auditarlo; la diferencia queda para la docencia (informe, §15);
  - la escala de D no está aprobada: `debt_to_sympathetic_gain` se lee con ella (D × c con ganancia / c da la misma
    FC) y el soporte de deuda de llegada es incertidumbre propagada, nunca un ancla;
  - saturación suave y monótona del incremento simpático, sin recorte y sin reserva final elegida;
  - la intrínseca 60 / 80 / 100 sigue STILL_VALID_CANDIDATE_RANGE; ningún valor aprobado.
- **Auditoría del resto (P2I-2AF-1):** `arrival_non_debt_drive` era un CASE_CALIBRATION_OFFSET.
  - Qué era: se despejaba de la FC registrada, era propio del caso y no tenía dinámica.
  - Cuánto pesaba: hasta el 100 % de la parte simpática de llegada (64 lpm en 57m y 52 en 72f).
  - Qué se hizo: se eliminó y su papel causal lo toma el término agudo.
- **Núcleo:**
  - objetivo = max(0, k_A · x + a_P (1 − P_rel) + k_S · D + hipoxemia + hipoglucemia), con x = déficit efectivo /
    demanda;
  - FC sinusal = intrínseca + HR_RESERVE · tanh(25 (1 − β) impulso / HR_RESERVE), con HR_RESERVE = techo − intrínseca;
  - la FC de llegada se predice desde la fisiología de llegada y su desajuste se informa;
    `check_arrival_reconstruction` reproduce exactamente todo lo demás;
  - la demanda del minuto se actualiza antes de que el impulso la lea;
  - por defecto, provisionales y no aprobados: `acute_deficit_to_sympathetic_gain` 0 (apagada),
    `debt_to_sympathetic_gain` 1/120, `sinus_rate_ceiling_bpm` 175. Golden: sólo metadata; Contracts v2: IDENTICAL.
- **Efectos sobre artefactos anteriores:**
  - HR1 y HR2 comparan con la FC de llegada de la propia corrida. HR2 pide a una llegada sin parte simpática (ya en la
    intrínseca) terminar en ella; registro de congelamiento de calibración `990f3ad8…`. Ningún estado de P2G cambia.
  - El paquete P2G registra el incremento simpático saturado y lee las 108 llegadas que P2I-2AE rechazaba: sus cifras
    de FC cambian; las de lactato, presión y FR, no.
  - El corte P2I-1, las sondas P2I-2T y las anclas P2I-2U sólo cambian sus digests y el conteo de llegadas leídas sin
    impulso por deuda (de 108 a 0).
- **Diseño predeclarado:** fijado antes de cualquier resultado, sin leer el motor heredado.
  - `acute_deficit_to_sympathetic_gain`: de 0,1 a 21,3, cinco puntos logarítmicos y 0.
  - `debt_to_sympathetic_gain`: de 6,67e-4 a 0,160, sobre el soporte de deuda 20 / 60.
  - Techo 150 / 175 / 200 lpm: fisiología general, por encima de toda FC registrada y casi lineal en la menor parte
    registrada.
  - El ancla de lectura es el punto medio logarítmico de cada rango, techo 175 e intrínseca media; no es una selección.
- **Congelamiento antes de evaluar:** `565e323`, un solo commit (digest `70106108…`).
- **Evaluación** (análisis, reconstrucción, 1-D y plano 6 × 6 post-procesado, sin barrido cartesiano):
  - 3240 descomposiciones de llegada analíticas, 0 rechazos;
  - 18 corridas representativas, 162 recorridas de validación (todas exactas) y 720 series post-procesadas;
  - D y lactato idénticos al registro P2I-2AD; la FR no lee la FC y no cambia;
  - las doce direcciones se cumplen y no se levanta ninguna bandera estructural. Varias banderas y las invariantes 5 y
    7 no pueden fallar por construcción; el veredicto descansa en la reconstrucción exacta, las sondas y las
    invariantes 1–4 y 8–12;
  - la llegada no sinusal o con betabloqueo completo y deuda (TD-93(5)) corre: RESOLVED_BY_P2I2AF
    (GENERALIZATION_BLOCKER_ONLY).
- **Hallazgos para la docencia:**
  - Con ganancias comunes y los mismos niveles de llegada, 57m y 72f reciben la misma FC predicha.
    - El desajuste tiene mediana de −24 lpm en 57m y −12 en 72f.
    - El menor peor desajuste conjunto sobre la superficie es 6,2 lpm con la misma intrínseca, o 2,4 lpm si la
      intrínseca puede diferir por caso (sólo el valor; no se elige ningún punto).
  - En L3, tras los GR y la hemostasia, el término de presión relativa se vuelve negativo y cancela la parte de deuda.
    - En el ancla, la FC vuelve a la intrínseca desde el minuto 60.
    - La taquicardia diferida sólo se ve con la mayor ganancia de deuda: 36 de 432 lecturas superan la intrínseca por
      más de 0,5 lpm en los minutos 90 y 120. El umbral es de presentación, fijado después de ver los resultados.
    - La invariante 5 la comprueba sobre la parte de deuda del impulso, no sobre la FC visible.
  - El término de presión queda NEEDS_PRESSURE_DOMAIN_REVIEW: correlación 0,75 con el agudo y 457 minutos en que
    descarga el impulso con un déficit presente.
  - Identificabilidad: todos los parámetros latentes son NON_IDENTIFIABLE por separado (intrínseca, ganancias, techo,
    escala de D); sólo se informan compuestos.
- **Veredicto: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION.** El diseño numérico docente sobre observables queda
  preparado, no ejecutado. Observables:
  - desajuste de llegada;
  - FC sin tratamiento;
  - FC con cristaloide;
  - FC con cada unidad de GR;
  - FC tras la adecuación;
  - taquicardia diferida.
  La docencia debe aportar: la tolerancia de llegada, las envolventes, si la intrínseca puede diferir por caso, el rango
  del techo y si el término de presión se queda.
- **Sin elegir parámetros ocultos**, sin calibrar la FC, la FR ni la presión, sin colapso, sin migración y sin gancho
  en tiempo de ejecución.
- **Revisión adversarial (una):** sin BLOCKER.
  - MAJOR, corregido (ejecutable): la banda simpática de llegada del paquete P2G restaba la llegada media a cada nivel
    de intrínseca y daba partes negativas. Ahora lee la llegada predicha de cada nivel; una prueba lo fija.
  - MAJOR, declarado (TD-94(6)): banderas e invariantes 5 y 7 tautológicas. Los documentos explicaban mal por qué
    pasaba la 7; se corrigió.
  - MAJOR, declarado (TD-94(7)): sin intrínseca declarada, la FC registrada es el piso (comportamiento previo de P2E-1).
    «Sin resto» vale con la intrínseca declarada; una prueba lo fija.
  - MAJOR, contradicción señalada (informe, §15): la condición registrada para el término de presión frente al
    encargo; decide la docencia.
  - MINOR, declarados (TD-94(8)–(9)): la detención por un techo no aprobado, el texto de AC1 y descripciones antiguas
    de `arrival_sympathetic_drive`.
  - MINOR, corregido: cifras de los documentos (umbral de presentación, FR, «debe confirmarlo la docencia»).
  - NIT, anotados en el informe (§18).
  - `hr_shock.py` queda idéntico a `565e323`. Cambia el hash de fuentes del digest (`decision_pack.py`), y la
    evaluación se volvió a correr.

## 37. P2I-2AG · Presión aplazada y superficie primaria de calibración de la FC (2026-10-29)

- **Base:** `79a3895`. P2I-2AF queda aceptado como paquete estructural de la FC y cerrado: su módulo queda fijado byte a
  byte y su registro (`adb3767b…`) por su digest. Informe: `docs/revision/P2I2AG_SUPERFICIE_PRIMARIA_FC.md`; números:
  `docs/revision/P2I2AG_hr_primary.json`.
- **Decisiones docentes:**
  - la contribución de presión queda DEFERRED en la calibración primaria de la FC: no elige ganancias, no compensa el
    impulso agudo ni el de deuda y no entra en la coincidencia de llegada ni en ningún orden;
  - no se rechaza: queda en la fisiología común para el dominio de la presión, sin referencia absoluta inventada;
  - toda calibración declara la intrínseca (60 / 80 / 100): `CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR`;
  - HR1 y HR2 son pruebas estructurales del modelo vigente;
  - tolerancia de llegada de ±5 lpm por caso (57m 124, 72f 112);
  - ganancias comunes y primero una intrínseca común; la intrínseca por caso, sólo como sensibilidad;
  - se mantienen la saturación y los candidatos de P2I-2AF; la escala de D no está aprobada.
- **Calibración** (registro de congelamiento `22bd65e4…`):
  - `check_hr` rechaza una llegada sin intrínseca declarada;
  - HR2 (a): una llegada sin contribución simpática predice exactamente la intrínseca declarada;
  - se actualizaron los textos de HR1, HR2 y AC1 y la descripción de `arrival_sympathetic_drive`;
  - los artefactos (P2G, P2I-1, P2I-2T, P2I-2U) sólo cambian sus digests; ningún estado cambia; el golden directo no
    cambia y Contracts v2 da IDENTICAL.
- **Modo primario:** el perfil de análisis de P2I-2AF con la ganancia de presión en 0. El valor de la presión se informa
  aparte (`PRESSURE_TERM_DIAGNOSTIC_ONLY`). Verificado así:
  - 54 recorridas exactas;
  - 2178 estados idénticos salvo el impulso (BloodState, V, Hb, D, lactato y demanda);
  - D y lactato iguales al registro P2I-2AD.
- **Congelamiento antes de evaluar:** `8eba7fc`, un solo commit (digest `94c94584…`).
- **Evaluación** (analítica en la llegada, sin barrido cartesiano):
  - 1350 descomposiciones (3 representantes × 225 candidatos × 2 casos);
  - compatibles con su caso: 57m 30, 72f 58;
  - conjuntamente compatibles con la intrínseca común: **0**. Los 675 candidatos conjuntos caen por un rechazo
    analítico exacto (IDENTICAL_PREDICTION_DISJOINT_WINDOWS): cada representante tiene la misma llegada en ambos casos,
    y las ventanas 119–129 y 107–117 no se superponen. El peor desajuste no puede bajar de 6 lpm.
- **Sensibilidad (no aprobada):** con una intrínseca propia de cada caso sobreviven 5 de 2025 combinaciones, todas con:
  - el representante LOW;
  - 57m con intrínseca 80 y 72f con 60;
  - ganancia aguda 5,58 y techo 150.
- **Presión (diagnóstico):**
  - correlación con la señal aguda 0,753;
  - en el 21 % de los minutos baja el impulso aunque haya déficit, con una cancelación mediana de 2,3 lpm;
  - suma una mediana de +4,4 lpm sin tratamiento a los 120 min y resta −2,2 tras los GR y la hemostasia;
  - invierte el orden de 383 de 18 000 pares de candidatos;
  - la llegada no cambia.
- **Veredicto: HR_NUMERIC_DECISION_SURFACE_NOT_READY — HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION.** El
  paquete se detiene como pide el encargo: sin paquete de trayectorias, sin propuesta de envolventes y sin certificación
  completa ni push.
- **Decisiones docentes pendientes:**
  - permitir una intrínseca propia de cada caso, o niveles de llegada propios de cada caso;
  - aclarar si 150 / 175 / 200 son techos o reservas literales;
  - si se certifica y se sube ya el cierre estructural.
- **Sin elegir ni aprobar parámetros**, sin calibrar la presión ni la FR, sin colapso, sin migración y sin gancho en
  tiempo de ejecución. El motor heredado no se leyó.
