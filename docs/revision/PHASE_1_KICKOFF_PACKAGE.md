# Fase 1 · Paquete de arranque (Contratos v2)

> **Plan preparado; la Fase 1 NO empezó.** Sesión autónoma del 2026-10-08, rama `clinical-encounter-v0.13`.
> - No se creó ninguna rama ni se cambió código.
> - El primer prompt está en `docs/revision/PHASE_1_FIRST_PROMPT.md`, sin ejecutar.
> - Arrancar requiere la puerta de §7I y una autorización expresa.
>
> **Etiquetas:** VERIFICADO EN EL CÓDIGO (archivo y línea leídos sobre el runtime `8ff41a4`) · PROPUESTO ·
> SUPUESTO / POR DEFINIR.

## 1. Dos huecos que hay que cerrar antes de empezar

**(a) La rama de desarrollo de la Fase 1: dos fuentes se contradicen.**
- Readiness §16.3 (2026-10-07) dice: «Sólo desarrollo. La Fase 1 seguirá aquí [`clinical-encounter-v0.13`] cuando se
  abra, con el piloto ya congelado».
- El encargo del 2026-10-08 propone `phase-1-contracts-v2`.
- Según CLAUDE.md, no se elige en silencio: **decide la persona responsable.**

**Recomendación:** `phase-1-contracts-v2`, creada desde el SHA final congelado del piloto.
- `clinical-encounter-v0.13` despliega la app de desarrollo en cada push (§16.5); una rama nueva no despliega nada.
- La Fase 1 queda aislada de cualquier corrección urgente del piloto, que seguiría su propio camino de promoción.
- El historial de la Fase 1 empieza exactamente en lo que se certificó.

Con cualquiera de las dos, hay que actualizar la línea «Trabajar sólo en la rama autorizada… (hoy,
`clinical-encounter-v0.13`)» de CLAUDE.md al autorizar la Fase 1.

**(b) La propuesta de arquitectura no está en el repositorio.**
- El código la cita: «The bundle rule (proposal §9.4, Phase 0 default)» (`order_pipeline.py:11`); «the common core
  (proposal, Phase 4)» (`curriculum.py:41`).
- Ni la propuesta ni la expresión «Contracts v2» aparecen en `docs/`. `docs/ARQUITECTURA.md` es otro documento (ciclo
  5, «lo implementado y lo planificado»).
- El alcance de este paquete sale del encargo del 2026-10-08 (SUPUESTO hasta que la propuesta se agregue a `docs/` y
  se compare).

**Recomendación:** agregar la propuesta a `docs/` antes de WP1. WP0 no la necesita.

## 7A. Línea de base

| Elemento | Valor |
|---|---|
| SHA base | **El SHA final congelado del piloto** (`<SHA_FINAL>`, el promovido a `pilot-residents-v1` con GO). POR DEFINIR: hoy no existe; el último runtime certificado es `8ff41a4`, y la ronda de B-5 lo cambiará |
| Rama propuesta | `phase-1-contracts-v2`, desde `<SHA_FINAL>` (§1 a) |
| Lo que hereda | Suite completa, 56 regresiones, batería de aceptación (31 × 19, semilla 17), centinela del español, dorado de la hipoglicemia, manifiesto del congelamiento: todos en verde en `<SHA_FINAL>` (matriz A del mapa) |
| Lo que nunca recibe | `pilot-residents-v1` no recibe commits de la Fase 1 (§16.5) |

## 7B. Alcance

**Dentro: sólo Contratos v2.** Hacer explícitos, tipados y versionados los contratos que hoy son implícitos entre
el lector, la tubería de órdenes, el motor, el tiempo, los eventos, la observación, el Trace y la persistencia.
- Primero en sombra (se calculan junto a los actuales y se comparan).
- Después, con prueba de equivalencia, como la forma servida.

**Fuera:**
- el núcleo fisiológico común («Phase 4» en el código) y cualquier cambio de fisiología o de conducta clínica;
- el lector (`family_parser.py` y su familia), mientras siga la espera de la validación externa (CLAUDE.md);
- el corpus, V3 y los baselines;
- scoring, D1–D5, penalidades, conteos, radar y mappings;
- textos visibles: el español aprobado en B-5 no cambia;
- IA en el encuentro;
- el esquema persistido, salvo un paquete posterior que lo justifique y se autorice aparte;
- cualquier push a `pilot-residents-v1`.

## 7C. Inventario de contratos

Las afirmaciones de «actual» están VERIFICADAS EN EL CÓDIGO; las de «objetivo v2» son PROPUESTAS.

| Contrato actual | Limitación | Objetivo v2 | Archivos | Pruebas que lo protegen | Riesgo de migración |
|---|---|---|---|---|---|
| **Orden / acción:** `family_parser.parse_family_actions` (`family_parser.py:4291`) devuelve dicts sin tipo; `order_ledger.tag` / `strip_tags` (`order_ledger.py:1333, 1348`) agregan y quitan el id de la orden; esquema `order_ledger_v1` (`:37`) | La acción es un dict libre. El id de la orden se quita antes del motor (`strip_tags`), así que el motor no sabe qué orden ejecuta | Un tipo `OrderAction` (dataclass o TypedDict) **construido desde** la salida del lector, sin tocarlo, con el id de la orden, la clase, los campos y la versión | `order_ledger.py`, `order_pipeline.py` (`open_turn`, `:107`), módulo nuevo `contracts_v2/` | `test_phase0_order_ledger.py`, `test_phase0_unknown_names.py`, batería de aceptación | Medio: el adaptador debe reproducir exactamente lo que hoy recibe el motor |
| **Destino / recibo:** `order_pipeline.split_bundle` (`:287`), `settle` (`:418`) y `receipt_lines` (`:569`; `order_ledger.receipt_lines`, `:1449`) | El destino se deduce **comparando texto**: `_NOT_MODELLED_REFUSAL` (`:40`), «not repeated» (`:316`), «at most 120 minutes in one step» (`:452`, `:484`). El resumen se empareja con la acción **por tipo** (`_summary_for`, `:405–415`) | Códigos de resultado estructurados que el motor devuelve (p. ej. `NOT_MODELLED`, `NOT_REPEATED`, `STEP_LIMIT`), con el texto como presentación | `order_pipeline.py`, `family_engine.py` (sólo la forma del retorno) | `test_phase0_order_ledger.py`, `test_phase0_spanish.py` (recibos), batería | Medio: un mensaje cambiado hoy rompe el destino en silencio; v2 lo elimina |
| **Identidad de la orden dentro del motor** | Dos órdenes del mismo tipo en un paquete se emparejan por posición o tipo, no por id | El id de la orden viaja con la acción y vuelve en su resumen; emparejamiento por id | `order_pipeline.py`, `family_engine.py` | Batería (categoría de paquetes), `test_phase0_order_ledger.py` | Medio-alto: toca la frontera con el motor; en sombra primero |
| **Tiempo:** `clinical_time.ACTIVE_MINUTES` (`clinical_time.py:36`); `time_semantics.MAX_STEP_MIN = 120` (`time_semantics.py:39`), **duplicado** como literal 120 en `family_engine.py:624`; `family_engine.advance_clinical_time` (`:2960`) | Un mismo límite en dos lugares; el avance del reloj no devuelve un registro de qué pasó | Una sola constante y un registro `TimeAdvance` (pedido, aplicado, detenido por, eventos); **sin** conducta nueva de interrupción | `time_semantics.py`, `family_engine.py`, `clinical_time.py` | `test_phase0_time_and_events.py`, batería | Bajo-medio |
| **Evento / interrupción:** `event_provenance.FLAG_EVENTS`, `_event` (`event_provenance.py:227–240`); `source_order_ids` se completa por clase (`:196–207`) | La procedencia por orden se infiere por la clase de la causa, no por la orden que la produjo | `source_order_ids` desde el id real de la orden (depende de la identidad dentro del motor) | `event_provenance.py`, `order_pipeline.py` | `test_phase0_observation_and_provenance.py`, `test_phase0_time_and_events.py` | Medio |
| **Observación:** `family_engine.examination_finding` / `current_findings` (`:3168–3255`); `observation_consistency.py` | El examen es un dict de cadenas compuesto en el momento; qué es dinámico y qué viene del relato no está declarado (origen de TD-83 y TD-84) | Un `ObservationSnapshot` tipado que declara, por región, la fuente (relato o estado del motor) y la versión | `family_engine.py` (sólo la forma), `observation_consistency.py` | `test_phase0_observation_and_provenance.py`, `test_examination_orders.py`, batería (`observation_consistency`) | Medio: el texto visible no debe cambiar |
| **Trace / procedencia:** `app.record_management_trace` (`app.py:900`), con `trace_extensions = ["phase0_v1"]` (`:951`) | Los ids de turno son posicionales; dos versiones conviven (v1 y la extensión de la Fase 0) | Una vista de lectura unificada y versionada (`trace_v2`) **derivada** de lo guardado; ids de turno estables; sin cambiar lo que se persiste al principio | `app.py` (sólo extracción), módulo nuevo | `regression_v06021_management_trace_ui.py`, `test_phase0_*`, pruebas del Trace | Medio: los encuentros históricos deben leerse igual (L-F01) |
| **Persistencia / envío:** `submission_guard._SNAPSHOTS` en memoria, con tope de 64 (`submission_guard.py:62–63, 263–267`); `curriculum_runtime.write_session` (`:94`) con `PAYLOAD_VERSION = "mrs_attempt_v1"` (`:24`), un solo blob JSON; revisión optimista en `account_store` | Las instantáneas viven en memoria del proceso. Una exploración de esta sesión informó entradas al motor que no pasan por la guarda; no se confirmó en el código (la captura del botón «Send» sí pasa: `app.py:133–141`, `:11147`). SUPUESTO hasta que WP8 lo compruebe | Toda entrada por la guarda; las instantáneas con un límite declarado; **el formato persistido no cambia** en la Fase 1 | `submission_guard.py`, `app.py`, `curriculum_runtime.py` | `test_phase0_submission_guard.py`, `test_phase0_submission_guard_on_postgres.py`, `test_store_integrity_on_postgres.py` | Alto si toca el formato; por eso queda fuera |
| **Frontera app / motor:** `app.py` (11 683 líneas); 73 archivos de prueba cargan el motor por el AST de `app.py` (`load_engine`); `pilot_acceptance` (`:279–313`) repite la ejecución del paquete | La lógica del paquete vive en la página; las pruebas dependen de su estructura | La rama de la familia de `execute_bundle` en un módulo propio; `app.py` conserva envoltorios con el mismo nombre; `pilot_acceptance` llama al módulo | `app.py`, módulo nuevo, `pilot_acceptance.py` | Los 73 archivos con `load_engine`, batería, página de aceptación | Alto por superficie; se hace al final, con el arnés de WP0 como red |

## 7D. Invariantes que la Fase 1 no puede romper

1. **Ninguna orden se pierde:** cada orden tiene destino y recibo (Fase 0, 0A–0B).
2. **El envío es idempotente** y se escribe antes de ejecutar (0D).
3. **El tiempo:** el límite de 120 minutos se dice, nunca se aplica acortando la espera (`family_engine.py:625`).
   Un evento crítico interrumpe la espera (0E–0F).
4. **La observación es coherente con el estado:** sin pulso, sin examen de vivo (0G).
5. **Procedencia:** cada evento con su causa y su prevenibilidad (0H).
6. **El Trace** preserva lo expresado, lo ejecutado y la diferencia. No inventa razonamiento, acciones ni omisiones
   (charter A1 §103–§106).
7. **Inmutabilidad histórica:** un encuentro guardado se lee y se evalúa igual (L-F01). `mrs_attempt_v1` sigue
   legible.
8. **El texto visible** en inglés y en español no cambia: centinela y pruebas de idioma en verde.
9. **El lector congelado:** `git diff 3d942ee -- family_parser.py shared_order_language.py shared_order_quantities.py
   active_order_context.py weight_based_doses.py` vacío.
10. **Scoring y metodología:** D1–D5, penalidades, conteos, radar y mappings, sin cambio.
11. **Conducta del motor idéntica** en los 30 casos con la batería de aceptación, el dorado de la hipoglicemia y el
    arnés de WP0, salvo una corrección declarada en `corrections_registry`. En la Fase 1 no se espera ninguna.

## 7E. Compatibilidad y estrategia en sombra

- **Primero en sombra:** cada contrato v2 se calcula **junto** al v1, sin reemplazarlo. El arnés de WP0 compara los
  dos en cada turno de la batería y falla ante la primera diferencia.
- **El cambio, por contrato:** un paquete pasa a servir el v2 sólo con:
  - la equivalencia demostrada en los 30 casos;
  - la suite completa en verde;
  - la autorización del paso.
  El v1 queda como lectura hasta WP10.
- **La lectura acepta las dos formas:** lo guardado con v1 se lee siempre. Las vistas v2 de los encuentros
  históricos se **derivan**; nunca se reescriben.
- **Sin interruptor en el piloto:** el piloto no recibe la Fase 1, así que no hace falta un indicador de runtime para
  apagarla allí.
- **Persistencia:** sin cambio de esquema. Si un paquete posterior lo necesitara, se propone aparte, con migración
  aditiva y prueba en PostgreSQL 17.

## 7F. Criterios de aceptación de la Fase 1

1. Cada contrato del inventario (§7C) tiene un tipo v2 documentado, versionado y probado.
2. El arnés de WP0 da **0 diferencias** de conducta entre `<SHA_FINAL>` y el HEAD de la Fase 1, en los 30 casos y en
   los dos idiomas.
3. El destino de una orden ya no depende de comparar texto: ningún `in str(error)` o `in str(reason)` decide un
   destino (búsqueda en el código).
4. El id de la orden viaja por el motor, y `source_order_ids` sale de él.
5. Una sola constante para el límite del paso.
6. Toda entrada al motor pasa por la guarda del envío (prueba que recorre las entradas).
7. `app.py` ya no contiene la ejecución del paquete de la familia; las pruebas que cargan el motor siguen pasando.
8. Siguen en verde: la suite completa, 56/56, la batería, la página de aceptación, el centinela, la preservación de
   la hipoglicemia, el corpus y el lector congelado.
9. Ningún cambio de fisiología, de texto visible ni de scoring (diff revisado).

## 7G. Paquetes de trabajo

Tamaño del diff (PROPUESTO): S < 200 líneas, M 200–600, L > 600, sin contar los datos dorados.

| ID | Objetivo | Archivos | Diff | Pruebas | Detenerse si | No debe cambiar |
|---|---|---|---|---|---|---|
| **WP0** | Arnés de línea de base y de equivalencia: registra la conducta de `<SHA_FINAL>` (por caso y turno: acciones ejecutadas, destinos, recibos, tiempo, eventos, observación, campos del Trace) y la compara con el HEAD | Nuevos: `tools_contract_baseline.py`, `test_contract_equivalence.py`, `test_data/contracts_baseline_<sha8>.json` | M | La prueba nueva pasa en el SHA base; dos corridas dan el mismo archivo; una mutación sembrada la hace fallar | Dos corridas no dan lo mismo (no determinista); o el arnés necesita tocar el runtime | Todo el runtime y todas las pruebas existentes |
| **WP1** | Orden / acción v2: tipo `OrderAction` y adaptador desde la salida del lector, en sombra | `contracts_v2/orders.py` (nuevo), `order_pipeline.py` (llamada en sombra) | M | WP0 en 0 diferencias; pruebas del tipo; `test_phase0_order_ledger.py` | El adaptador necesita cambiar el lector | El lector; lo que recibe el motor |
| **WP2** | Destino / recibo v2: códigos de resultado estructurados en lugar de comparar texto | `order_pipeline.py`, `family_engine.py` (forma del retorno), `contracts_v2/fates.py` | M | WP0; pruebas por código; recibos EN/ES idénticos | Un recibo visible cambia | Texto de los recibos; destinos |
| **WP3** | El id de la orden a través del motor; emparejamiento por id | `order_pipeline.py`, `family_engine.py`, `order_ledger.py` | M–L | WP0; paquetes con dos órdenes del mismo tipo | Cambia el orden de ejecución o un resultado | Conducta del motor |
| **WP4** | Tiempo v2: una sola constante y el registro `TimeAdvance` | `time_semantics.py`, `family_engine.py`, `clinical_time.py` | S–M | WP0; `test_phase0_time_and_events.py` | Cambia un minuto en algún caso | Reloj y conducta de espera e interrupción |
| **WP5** | Evento / interrupción v2: procedencia por id de orden | `event_provenance.py`, `order_pipeline.py` | S–M | WP0; `test_phase0_observation_and_provenance.py` | Cambia una causa o una prevenibilidad | Etiquetas de eventos (las aprobadas en B-5) |
| **WP6** | Observación v2: instantánea tipada con la fuente declarada por región | `contracts_v2/observation.py`, `family_engine.py` (sólo forma), `observation_consistency.py` | M | WP0; `test_examination_orders.py`; centinela | Cambia un hallazgo visible | Texto del examen (EN y ES) |
| **WP7** | Trace / procedencia v2: vista de lectura unificada y versionada; ids de turno estables; sin cambiar lo persistido | `contracts_v2/trace.py`, `app.py` (extracción) | M | WP0; pruebas del Trace; lectura de encuentros históricos idéntica | Un encuentro histórico se lee distinto | El formato persistido y las evaluaciones guardadas |
| **WP8** | Frontera de persistencia: toda entrada por la guarda del envío; límite declarado de las instantáneas | `submission_guard.py`, `app.py` | S–M | `test_phase0_submission_guard.py` y su versión PostgreSQL | Cambia el formato persistido | `mrs_attempt_v1` y el esquema |
| **WP9** | Frontera app / motor: la ejecución del paquete en un módulo; envoltorios en `app.py`; `pilot_acceptance` lo usa | Módulo nuevo, `app.py`, `pilot_acceptance.py` | L | WP0; los 73 archivos con `load_engine`; batería; página de aceptación | Una prueba existente necesita cambiar su expectativa de conducta | Conducta y nombres públicos |
| **WP10** | Limpieza de compatibilidad: retirar los caminos v1 de **cálculo** que v2 ya sirve; la lectura v1 de lo guardado se queda | Los tocados en WP1–WP9 | M | Suite completa, 56/56, batería, centinela, corpus, lector congelado | Algo guardado deja de leerse | Lectura de encuentros históricos |

**Orden:** WP0 → WP1 → WP2 → WP3 → WP4 → WP5 → WP6 → WP7 → WP8 → WP9 → WP10.
- WP4 puede adelantarse (es independiente de WP1–WP3).
- WP5 depende de WP3.
- **Cada paquete se cierra con:** sus pruebas focalizadas, WP0 en 0 diferencias y un commit local.
- **La suite completa se corre:** al cerrar WP3, WP7 y WP10, y antes de cualquier push autorizado.

## 7H. Riesgos y decisiones abiertas

- **Rama (§1 a)** y **propuesta de arquitectura en `docs/` (§1 b):** decisiones de la persona responsable.
- **El lector sigue congelado** hasta «BEGIN EXTERNAL VALIDATION INGESTION». Si un contrato no puede construirse sin
  tocarlo, se detiene y se pide decisión.
- **WP9 es el de mayor superficie:** 73 archivos de prueba dependen del AST de `app.py`. Va al final, con el arnés
  como red.
- **Correcciones del piloto durante la Fase 1:** van por su propio camino (rama de desarrollo del piloto →
  recertificación → `pilot-residents-v1`) y se traen a la Fase 1 por merge, no al revés.
- **Costo:** WP0–WP10 son deterministas; 0 llamadas de IA de la app. El cómputo de la suite se mide en cada
  corrida, no se estima.

## 7I. Puerta de arranque

La Fase 1 empieza sólo cuando **todas** se cumplen:
1. Existe `<SHA_FINAL>`: el candidato del piloto, certificado (matriz A), promovido y con GO.
2. La rama de la Fase 1 está decidida y autorizada, y la línea de la rama de CLAUDE.md está actualizada.
3. La Fase 1 está autorizada expresamente, con su alcance (§7B).
4. Recomendado: la propuesta de arquitectura agregada a `docs/` (necesaria antes de WP1, no de WP0).
5. La espera de la validación externa sigue vigente: el lector, el corpus, V3 y los baselines no se tocan.

**Hoy (2026-10-08) no se cumple ninguna de las tres primeras.**
