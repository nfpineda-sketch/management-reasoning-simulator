# Fase 3 · P3-52 a P3-57 · Linaje canónico orden → destino → acción, y cierre de la serie GI

Rama `phase-3-runtime-integration`, desde `3faee58`. Cierre de la Fase 2 `d2cca46`, digesto
`22b90a6f…6ce6a`, **sin cambios**. Instantánea `gi_pressure_committed`, aprobada **sólo** para el
experimento de desarrollo: no validada clínicamente, no aprobada para producción, no aprobada para
residentes. Nada de fisiología, de instantánea ni de alcance de autoridad cambia aquí.

**Lo que este documento cierra** es el único bloqueo que P3-51 dejó: la nota de procedencia que nadie
podía explicar. **Lo que no dice** es que ninguna magnitud sea clínicamente válida.

## 1 · P3-52 · La auditoría del linaje

### 1.1 El linaje real del tiempo de ejecución

```
texto del residente
  → family_parser                         produce las acciones del lector
  → order_ledger.tag(parsed, submission)  estampa _order_id = "<envio>:<indice>" EN LA ACCION
  → order_pipeline.open_turn              crea una orden por accion (order_from_action), o REUSA
                                          la del libro cuando la accion ya trae un _order_id conocido
  → execute_bundle / _execute             el motor recibe copias strip_tags (sin las claves "_")
                                          y devuelve run_actions: las ACCIONES ETIQUETADAS de parsed
  → shadow.observe
  → MINUTO DE AUTORIDAD                   recibe esos mismos run_actions: la identidad YA esta ahi
  → order_pipeline.settle                 _order_by_action(turn, action) resuelve por action["_order_id"]
                                          y aqui, y solo aqui, cada orden recibe su FATE
  → PROCEDENCIA                           lee las ordenes liquidadas y las liga por esa misma identidad
```

Dos hechos que esto fija, y que P3-50 no tenía:

1. **la identidad existe en el minuto de autoridad**, porque `_run_actions` son las acciones etiquetadas
   de `parsed` y el motor sólo recibe copias sin las claves internas;
2. **el destino no existe todavía** en ese momento, porque nace en la liquidación. Por eso la procedencia
   se finaliza después y el compromiso no se mueve.

### 1.2 Inventario de identificadores

| Identificador | Creado en | Persistido en | ¿Sobrevive al turno? | Cardinalidad | ¿Canónico para el linaje? |
|---|---|---|---|---|---|
| `submission_id` (`t0`, `t1`, …) | la página / `Encounter.order`, por contador de turno | `turn["submission"]["id"]`, prefijo de cada `order_id` | sí, como prefijo | 1 → N órdenes | sí, para el **turno**; **no** es único entre encuentros |
| `_order_id` en la acción | `order_ledger.tag` | no se persiste (lo quita `strip_tags`/`untagged`) | sí, «viaja con la acción a través de las retenciones» | 1 → 1 con la orden | **sí: es el enlace** |
| `order_id` en la orden | `order_from_action`, o literal en `plan_orders` / `unaccounted_orders` / palabras no leídas / retenidas | `order_ledger.snapshot`, la traza, el libro del encuentro | sí; `open_turn` reutiliza la orden por este id | 1 → 1 con la acción que la abrió | **sí**, dentro del libro de **un** encuentro |
| `fate` | **sólo** `order_pipeline.settle` (vía `order_ledger.set_fate`) | la orden, con su `history` | sí | 1 por orden, con historia | autoridad del destino |
| `written_at_min` | `order_from_action` (minuto en que se abrió el turno) | la orden | sí | 1 por orden | sí, para la creación |
| `executed_at_min` | `set_fate` al ejecutar | la orden | sí | 1 por orden | sí, para la activación |
| `receipt` | `settle` y `open_turn` | la orden | sí | 1 por orden | no (es texto para el residente) |
| `order_ledger.new_id()` | existe, **no** se usa para órdenes | — | — | — | no |
| `group`, `derived_from` | `group` **nadie** lo escribe; `derived_from` lo pone `app.py` por **entrada derivada del encuentro**, no por expansión de orden | la orden | sí | — | no |

Lo que **no** comparten: una orden reutilizada de un turno anterior conserva el `submission_id` **que la
abrió**, no el del turno que la ejecuta; y una orden puede existir sin acción que la corra (plan,
retenida, no reconocida).

### 1.3 Los dos desajustes, reproducidos

Medidos **dentro de `order_pipeline.settle`**, el único lugar donde el repositorio mismo empareja una
acción con su orden, sobre las dos baterías de aceptación completas: **86 llamadas, 170 acciones,
172 órdenes**.

| | Resultado |
|---|---|
| Acciones sin identidad | **0 de 170** |
| Acciones cuyo `_order_id` no está entre las órdenes de su turno | **0 de 170** |
| **B · orden abierta en un turno anterior, ejecutada después** | **0 casos** — la forma existe en el repositorio (`open_turn` reutiliza una orden retenida por su id) pero esta evidencia **no la ejercita** |
| **A · paquete dividido** | **2 turnos** (uno por caso): 5 acciones corridas y **6** órdenes; la sexta es `t0:p2000`, clase `not_modelled`, destino `RECORDED_NOT_MODELLED` — una orden de plan que el motor nunca corre |
| Uno-a-muchos | **0 turnos**: ningún `_order_id` aparece dos veces en un turno |
| Tipo de acción distinto de la clase de su orden | **2 de 170** |

**Esos 2 son la nota que P3-50 no pudo explicar, y mi explicación de P3-50 era falsa.** No venían de un
paquete dividido ni de una orden de un turno anterior —el segundo caso no ocurre ni una vez—. Vienen del
escenario `reload_resume` de `pilot_acceptance`:

```python
first  = _play(variant, [...])            # corre hasta el minuto 15
resumed = Encounter(variant)              # NUEVO: sim_time 0, la sombra ABRE, _turns = 0
resumed.state  = copia de first.state     # ahora corre desde el minuto 15
resumed.ledger = copia de first.ledger    # el libro ya contiene t0:0 (fluid, escrita en el minuto 0)
encounter.wait_until(target)              # su PRIMER turno se vuelve a llamar "t0"
```

Su primera acción toma `_order_id = "t0:0"` y `open_turn` **reutiliza la `t0:0` heredada** en vez de abrir
la suya. De ahí la huella exacta: acción `reassessment` con `_written_at_min` 15, orden clase `fluid` con
`written_at_min` 0 y `executed_at_min` 15.

| | Acción corrida | Orden liquidada |
|---|---|---|
| `order_id` | `t0:0` | `t0:0` |
| envío | `t0` | `t0` |
| clase / tipo | `reassessment` | `fluid` |
| minuto de escritura | **15** | **0** |
| destino | — (no existe aún) | `EXECUTED`, activada en 15 |

En la aplicación real esto **no puede** producir un minuto de autoridad: un encuentro reanudado tiene
`sim_time != 0` cuando la sesión abriría, y `ShadowSession.start` lo rechaza por esa misma razón
(FD-P3-18 (2)). La batería lo produce porque construye el `Encounter` en el minuto 0 —donde la sombra
abre— y le cambia el estado después.

### 1.4 Veredicto

> **B · `CANONICAL_LEDGER_LINEAGE_EXISTS_BUT_REQUIRES_TRAVERSAL`**

El enlace directo existe y resuelve **170 de 170**; pero `order_id` es único dentro del libro de **un**
encuentro y no entre encuentros, así que el linaje se resuelve por identidad y después **se comprueba**,
nunca se confía a ciegas.

### 1.5 Lo que el artefacto debe poder responder

«¿Qué orden autorizó **esta** acción?» — no «¿se abrió esta acción en este envío?». El registro distingue
las tres cosas por separado: el envío que **abrió** la orden (`source_submission`), el envío que la
**activó** (`activation_submission`) y de dónde viene (`SOURCE_ORDER_OPENED_THIS_SUBMISSION` o
`ACTIVE_PREVIOUS_ORDER`).

## 2 · P3-53 · La implementación

**La fisiología no se mueve.** El minuto de autoridad sigue donde estaba, ninguna activación se adelanta
ni se retrasa, y la trayectoria queda fijada contra lo que P3-41 midió antes de todo trabajo de
procedencia (80/49/59 · 101/62/75 · 112/68/83).

**La corrección de raíz:** `action_fates` buscaba `order_id`/`id` en la acción, pero la clave canónica del
lector es `_order_id` —la que usa `order_pipeline._order_by_action`—. Por eso la identidad salía vacía en
P3-44 y por eso P3-46 tuvo que reconstruirla filtrando el libro por envío. Ahora se lee la clave correcta.

### 2.1 El registro de linaje

Diez campos por acción consumida: `order_id`, `class`, `fate`, `source_submission`,
`activation_submission`, `order_written_at_min`, `action_written_at_min`, `activated_at_min`, `origin`,
`link`. Todos salen del libro o de la acción; ninguno se inventa y ninguno se deja vacío por conveniencia.

### 2.2 Los invariantes, nombrados y falsificables

| Nombre | Qué sería falso |
|---|---|
| `NO_CANONICAL_SOURCE_ORDER` | la acción no trae identidad (0 de 170 en la medición, así que **no** se admite como legítimo) |
| `LINEAGE_SOURCE_ORDER_ABSENT_FROM_THE_SETTLED_LEDGER` | el id no está en el libro liquidado |
| `LINEAGE_CLASS_DISAGREES_WITH_THE_SOURCE_ORDER` | la clase de la orden no es la de la acción (la colisión de §1.3) |
| `LINEAGE_SOURCE_ORDER_WRITTEN_AFTER_ITS_ACTIVATION` | la activación precede a la creación |
| `LINEAGE_SOURCE_ORDER_IS_NOT_THE_ONE_THIS_ACTION_OPENED` | misma clase, pero la orden se abrió en un minuto que esta acción no escribió |
| `LINEAGE_SOURCE_FATE_SAYS_THE_ORDER_DID_NOT_ACT` | el destino está en `order_ledger.NOT_ACTED` |

Más la comprobación de clase no soportada sobre el libro liquidado, que P3-48 añadió y que no cambia.
Una violación **detiene** el experimento, visible, y el minuto ya comprometido **no se reescribe**.

`provenance_notes` **desaparece**: no queda ninguna categoría de «hueco registrado del que no se concluye
nada».

### 2.3 Replay

El linaje se verifica desde el artefacto y nada más, en proceso nuevo: `lineage_valid`, `lineage_links` y
`lineage_violations` por minuto, y `lineage_valid_minutes` sobre el conjunto. Además, después de la
liquidación las dos copias del registro (`action_fates` y `action_lineage`) **son las mismas filas**, así
que falsificar cualquiera de las dos se detecta — lo que una prueba comprueba falsificando cada una.

### 2.4 Pruebas

`test_runtime_authority_lineage.py`, **14 pruebas**: L1 linaje del mismo turno · L2 orden de un turno
anterior, con su origen declarado · L3 paquete dividido, con la orden de plan que ninguna acción corre ·
L4 el mapeo uno-a-uno del tiempo de ejecución, y lo que el enlazador haría si hubiera expansión · L5 el
destino es el del libro · L6 un destino que no actuó no puede ser fuente de un tratamiento, probado
también en un encuentro real que **se detiene** · L7 la activación no puede preceder a su orden · L8 el
replay verifica el linaje desde el artefacto solo · L9 la trayectoria es la de P3-41 · L11 ninguna
superficie de puntuación · L12 el piloto sigue rechazado · L13 el digesto de la Fase 2 no se movió. Más
la colisión de §1.3 y la ausencia de identidad, cada una con su nombre.

**Veredicto: `CANONICAL_AUTHORITY_PROVENANCE_READY`.**

## 3 · P3-54 · La parada dura por el cableado de Streamlit

Nada se inyecta: la app abre su propio sitio con `_runtime_authority_site`, el residente escribe en el
área de texto de la página y la parada ocurre por lo que escribió. Caso `gi_bleed_57m` servido por la app
(reto `R2-05`, el único cuyas familias incluyen `gi_bleed`), entorno `development`, almacén en un
directorio temporal.

**Un hallazgo del propio P3-54:** una orden no soportada que la **compuerta de razonamiento** retiene no
llega nunca al minuto de autoridad —el reloj no avanza y no existe minuto que invalidar—, así que la
parada sólo es alcanzable una vez respondidas las cuatro preguntas de la compuerta. La prueba las
responde con los campos y el botón de la propia página.

| | |
|---|---|
| Sitio | lo abre la app en el primer envío; antes no existe ninguno |
| Minuto previo | **comprometido** por un turno limpio, por el cableado de la app |
| Minuto que falla | compromete **nada**; `UNSUPPORTED_AUTHORITY_ACTION` |
| Estado | `HALTED`, trayectoria mixta **declarada** |
| Compromiso posterior | ninguno; el legado sigue moviendo al paciente |
| Superficie docente | dibuja el fallo como **error**, con el estado, la razón, los minutos y la identidad del artefacto |
| Pantalla del residente | no contiene la razón, ni la instantánea, ni la palabra «authority», ni el estado del experimento |
| Artefacto | 30/30 campos, persistido, digesto verificado, replay exacto del minuto comprometido, linaje válido |

**Veredicto: `STREAMLIT_AUTHORITY_HARD_FAIL_E2E_READY`.**

## 4 · P3-55 · La serie, otra vez

Las dos baterías completas con la implementación final, un sitio por encuentro.

| | |
|---|---|
| Escenarios | **34** |
| Completados | **26** |
| Detenidos | **8** |
| Minutos de autoridad comprometidos | **66**; abortados 12 |
| Escenarios con ≥1 minuto comprometido | 28 |
| Fila de elegibilidad coherente | **34/34** |
| Replay exacto en todo minuto comprometido | **34/34** |
| Digesto verificado | **34/34**; ningún campo faltante; artefacto 17–113 KB |
| **Linaje válido en todo minuto comprometido** | **34 de 34** |
| Filas de linaje en la serie | **132**, todas `VALID_LINKED_LINEAGE` |
| Orígenes observados | `SOURCE_ORDER_OPENED_THIS_SUBMISSION` (el único que esta evidencia ejercita) |
| Destinos observados | `EXECUTED` y `RECORDED_NOT_MODELLED` |
| Clase de divergencia | `EXPECTED_ARCHITECTURAL_DIVERGENCE`, y sólo ella |
| Clases en los completados | reevaluación 26, cristaloide 14, PPI 14, sangre 12, consulta 12 |
| Coste | 7,8–8,7 s por caso |
| Reproducibilidad | dos series independientes, **0 diferencias** en 19 campos por escenario (los cuatro de linaje incluidos) |

**Sobre los 36 experimentos del almacén** —los 34 escenarios más los 2 encuentros de referencia—
**158 registros**: 136 filas de linaje `VALID_LINKED_LINEAGE` y **2**
`LINEAGE_CLASS_DISAGREES_WITH_THE_SOURCE_ORDER`, que son exactamente los dos `reload_resume` de §1.3,
ahora **detenidos visiblemente** con una violación nombrada en vez de llevar una nota inexplicada.
Paradas: 4 por norepinefrina, 2 por anticoagulación y antiagregante, 2 por clase no soportada en el libro
liquidado, 2 por la colisión de linaje.

**No queda ningún desajuste de procedencia sin explicar.**

**Veredicto: `GI_AUTHORITY_SERIES_WITH_CANONICAL_PROVENANCE_READY`.**

## 5 · P3-57 · Auditoría de cierre

| | Punto | Estado |
|---|---|---|
| 1 | Linaje canónico acción/orden | **cerrado**: enlace directo medido 170/170, invariantes nombrados, violación detectada y detenida |
| 2 | Elegibilidad | cerrada: la lectura certificada y el camino en vivo coinciden 8 = 8 |
| 3 | Transacción de autoridad | atómica sobre `sbp`/`dbp` con `map` derivado; 66 minutos, nada más comprometido |
| 4 | Caminos de éxito reales | 26 de 26 elegibles, los dos casos, cinco clases de manejo |
| 5 | Caminos de fallo reales | **cuatro** rutas en vivo: no soportada al primer turno, no soportada tras un compromiso, clase no modelada en el libro liquidado, y colisión de linaje |
| 6 | Parada por Streamlit | **cerrada** (P3-54), con la compuerta de razonamiento declarada |
| 7 | Replay | exacto, desde el artefacto, en proceso nuevo, linaje incluido |
| 8 | Reproducibilidad | 0 diferencias en 19 campos × 34 escenarios |
| 9 | Integridad del artefacto | 34/34 digestos, 30/30 campos, 158 registros |
| 10 | Diversidad | 16 de 26 con tratamiento, 10 de observación; el más largo 8 minutos |
| 11 | Aislamiento de la puntuación | ninguna superficie alcanzable, por AST y por inspección |
| 12 | Aislamiento del residente | la pantalla no nombra el experimento, probado por la app real |
| 13 | Aislamiento del piloto | rechazado por bandera y por sus propias marcas |
| 14 | Inmutabilidad de la Fase 2 | digesto `22b90a6f…` sin mover; `COMMON_CORE_RUNTIME_AUTHORITY = False` |
| 15 | Certificación final limpia | ver el informe del ciclo |

### Veredicto

> **A · `GI_DEVELOPMENT_AUTHORITY_SERIES_VALIDATED`**

La validación es **de ingeniería y de tiempo de ejecución**. **No** es calibración clínica, y no se debe
inferir de ella. Cinco de las siete magnitudes de la instantánea siguen sin quedar determinadas por la
evidencia de GI.

### Paso siguiente

> **Primario: calibración clínica de la presión GI.**

Es el único paso que cambia lo que el simulador afirma, y ahora es el que bloquea todo lo demás. Las
cuatro alternativas son más barriles del mismo tipo de evidencia que ya tenemos: más software validado
sobre parámetros que nadie ha mirado clínicamente. Concretamente, pide tres decisiones docentes que no
existen: qué material clínico se admite como referencia, qué tolerancia se declara aceptable por
magnitud, y quién firma. Nada de eso lo puede proponer la IA.

| | Alternativa | Por qué no primero |
|---|---|---|
| 2 | Escritores de tratamiento no soportados (anticoagulación, antiagregante, vasopresor) | desbloquea los 8 rechazos y es el siguiente paso **técnico** natural, pero es fisiología nueva y decisión clínica: calibrar lo que ya existe vale más que añadir lo que tampoco estará calibrado |
| 3 | Otra familia | ninguna otra tiene su sombra en vivo lista, y `afterload_sensitivity` actúa ahí sin estar identificado |
| 4 | CRT en el dominio | amplía el alcance antes de que el actual tenga significado clínico |
| 5 | Planificación del piloto | prohibida hoy, y prematura sin calibración |

**Límite duro:** no se habilita autoridad en producción ni visible al residente, no se modifica el primer
piloto, no se amplía más allá de la presión GI, no se añade CRT, no se implementa fisiología de
tratamiento no soportada, la instantánea **no** queda declarada clínicamente validada y la fisiología
congelada de la Fase 2 no se altera.
