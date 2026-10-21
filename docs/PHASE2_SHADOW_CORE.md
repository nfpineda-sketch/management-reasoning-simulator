# Fase 2 · Núcleo fisiológico común en modo sombra (preparación inicial)

| | |
|---|---|
| Rama | `phase-2-clinical-core-shadow` (local, sin push) |
| Base | `6fad3103af531689af7995a4db3838418581f1c0` = `origin/phase-1-contracts-v2`, el SHA final de la Fase 1 |
| HEAD del código de la Fase 2 | `3120e0cc343bed8fc6c7fe10922a62615ecba096`. Esta actualización del documento va en el commit siguiente |
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
| `legacy_adapter.py` | Único puente con el motor de familias: lo ejecuta sobre copias y lee sus entradas relevantes |
| `comparison.py`, `shadow.py`, `golden/gi_bleed_shadow.json` | Comparación heredado/núcleo y el resumen dorado comprometido |

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

Empates de redondeo informados aparte:
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
- No se modelan:
  - la sobrecarga transfusional (L);
  - la recuperación de la FC tras la hemostasia (KD-S2);
  - la meseta de precarga (KD-S4).
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

La rama ya parte de la Fase 1 final, pero el núcleo todavía **no importa** `contracts_v2`. La conexión es el paso
siguiente y necesita autorización propia.

| Contrato de la Fase 1 (`contracts_v2`) | Dónde se conecta | Qué reemplaza |
|---|---|---|
| WP1 `orders.OrderAction` | `legacy_adapter.interventions_from_orders` | La traducción desde las acciones del lector |
| WP2 `fates.FateReceipt` | `legacy_adapter.run_legacy` | La verificación de que cada turno corrió (`executed`, `elapsed_min`) |
| WP3 `timing.OrderTiming` y `TurnTime` | `interventions.timing` y `logistics.EndoscopicHemostasis` | El inicio fraccionario tomado del recibo y `endoscopy_at` tomado del motor de familias |
| WP4 `events.EventInterruption` | `provenance.CoreEvent` | Sólo mapeo; el núcleo no interrumpe turnos |
| WP5 `observations.ObservationSnapshot` | `legacy_adapter.snapshot`; `comparison.VARIABLES` y `_display` | El diccionario `observable` y la convención de pantalla copiada |
| WP6 `trace.TraceProvenance` | `provenance.MinuteRecord.to_dict` y `CoreEvent` | Ya tienen fuente, minuto, canal y causa; falta sólo el mapeo de nombres |
| Modelo terminal de la Fase 1 | `state.RhythmCode` y `NON_PERFUSING` | Etiquetas propias |

**Sigue sin haber gancho en tiempo de ejecución.** No se agregó ninguno y la Fase 2 no lo necesita.
- Si se autorizara uno, los únicos puntos de entrada del motor en la aplicación son, sobre `6fad310`:
  - `app.py:9187` y `app.py:9236` (`execute_family_bundle`);
  - `app.py:870` (`advance_clinical_time`).
- La recomendación es **no** tocarlos y correr la sombra fuera de línea, desde los encuentros persistidos (Trace v2
  más el ledger de órdenes). Así no hay riesgo para el residente.
