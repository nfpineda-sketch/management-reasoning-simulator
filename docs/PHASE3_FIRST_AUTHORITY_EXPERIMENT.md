# Fase 3 · P3-40 a P3-45 · Primer experimento de autoridad en desarrollo

Rama `phase-3-runtime-integration`, desde `4a420eb`. Cierre de la Fase 2 `d2cca46`, digesto
`22b90a6f…6ce6a`, **sin cambios**.

**Lo que este documento no dice:** que ninguna magnitud sea clínicamente válida. La instantánea quedó
aprobada **para un experimento de desarrollo**, con los estados `EXPERIMENTAL_AUTHORITY_SNAPSHOT` y
`DEVELOPMENT_ONLY`, y **no** `CLINICALLY_VALIDATED`, `CLINICALLY_CALIBRATED`, `PRODUCTION_APPROVED` ni
`RESIDENT_APPROVED`. El éxito técnico no establece calibración clínica.

## 1 · La decisión registrada (P3-40)

| | |
|---|---|
| Identificador | `gi_pressure_committed` |
| Propósito | `DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY` |
| Estado docente | `APPROVED_FOR_DEVELOPMENT_EXPERIMENT` |
| Referencia | decisiones docentes A y G del 2026-11-08 (Decision File FD-P3-42) |
| Punto que corrió | `phase2_committed_default_profile`, el mismo con el que se produjo todo artefacto certificado de la Fase 2 |

Los siete valores, con su estado de evidencia medido en P3-31:

| Magnitud | Valor | Estado de evidencia |
|---|---|---|
| `preload_curve_scale_ml` | 833,3333333333334 | `GI_IDENTIFIABLE` — mueve la SBP hasta 33,673 mmHg en 34/34 escenarios |
| `arrival_preload_fraction` | 0,5 | `GI_IDENTIFIABLE` — hasta 62,802 mmHg en 34/34 |
| `afterload_sensitivity` | 0,3 | `NOT_GI_IDENTIFIABLE_EXTERNALLY_CONSTRAINED` — en GI T ≡ 1 en los 1638 minutos medidos; ACS y TEP sí lo restringen, con ≤0,4 mmHg |
| `pump_preload_coupling` | 1,0 | `NOT_GI_IDENTIFIABLE_STRUCTURALLY_WEAK` — necesita pump deprimido **y** cambio de volumen; ninguna familia certificada tiene las dos cosas |
| `low_output_pressure_knee` | 0,5 | `NOT_GI_IDENTIFIABLE_NOT_READ_BY_THE_CORE` — salió de la ecuación en P2J-1; sobrevive como guarda de admisibilidad |
| `sbp_per_pressure_deficit` | 45,0 | `NOT_GI_IDENTIFIABLE_NOT_READ_BY_THE_CORE` — sólo lo lee un diagnóstico que reconstruye la presión cruda del legado |
| `dbp_per_pressure_deficit` | 25,0 | `NOT_GI_IDENTIFIABLE_NOT_READ_BY_THE_CORE` — no se lee fuera del registro de calibración |

**Aprobar el punto no es aprobar siete magnitudes validadas**, y el registro lo dice magnitud por
magnitud: `registered_snapshot_is_complete` rechaza una entrada que omita las anotaciones, que declare
otro propósito, que permita producción o piloto, o que reclame en cualquier parte de su texto una
validación que ninguna decisión concedió. Si una entrada deriva, el módulo **no importa** y la
aplicación no arranca.

### 1.1 El alcance que la concesión fija

| | |
|---|---|
| Familia | `gi_bleed`, y sólo ella |
| Casos | `gi_bleed_57m`, `gi_bleed_72f` |
| Dominio | `sbp` y `dbp` comunes; `map` derivado con la convención de la pantalla |
| Entornos | `development` y `faculty` |
| Piloto, producción, visibilidad al residente | **excluidos** |
| Puntuación | legado, sin cambio |
| Toda la fisiología no presión | autoridad del legado |
| Almacén de artefactos | obligatorio, ruta absoluta fuera del repositorio |

La región de la aprobación se comprueba **además** de las constantes del portón: un entorno de
producción se rechaza dos veces, por la condición `environment` y por el alcance declarado de la propia
aprobación. Ampliar una constante no amplía una aprobación ya concedida.

## 2 · La revisión adversarial de P3-40 (antes de correr)

Catorce ataques; **13 bloqueados** y **1 hallazgo real, corregido antes del experimento**.

| Ataque | Resultado |
|---|---|
| Aprobación de desarrollo usada en producción | bloqueado: `production`, `prod`, `staging`, vacío y `PRODUCTION` rechazan por las dos vías |
| **Sustitución de instantánea (mismo id, otros valores)** | **HALLAZGO**: la forma pasaba y el portón concedía. Corregido: `APPROVED_POINT_DIGESTS` fija el digesto de los valores **fuera** de la entrada, y `approved_snapshot` lo recomputa; la guarda de importación rechaza un registro cuyos valores se movieron |
| Registro público escribible / valores mutables en sitio | bloqueado (`TypeError`) |
| Entorno falseado desde el estado del encuentro | bloqueado |
| Activación por secretos de Streamlit | bloqueado, con motivo declarado |
| Acceso del piloto (bandera y marcas de despliegue) | bloqueado por las dos vías; falla cerrado si la congelación no se lee |
| Fuga del mecanismo sólo-pruebas al registro | bloqueado: el registro tiene exactamente un id |
| Ampliación del dominio más allá de SBP/DBP/MAP | bloqueado en las cinco variantes probadas |
| Autoridad en otra familia | bloqueado |
| Elusión de acción no soportada | bloqueado en seis clases y en el caso «no declarado» |
| Elusión del almacén | bloqueado con ruta vacía, relativa, del repositorio y de `docs/` |
| Regreso silencioso en el rechazo | bloqueado: el modo cae a sombra **con** motivos |
| Fuga de propiedad no presión | bloqueado: únicos dueños comunes `sbp` y `dbp`; `map` derivado |

**Limitación aceptada, no defecto:** el almacén acepta cualquier ruta absoluta fuera del repositorio,
incluido un directorio personal. La política autorizada pide «absoluta y fuera del repositorio» y eso se
cumple; el almacén confía en el directorio que elige quien opera. No inventé una restricción que la
decisión no pidió.

## 3 · El primer experimento (P3-41)

| | |
|---|---|
| Caso | `gi_bleed_57m` |
| Escenario | `B_delayed_management`, de la batería de aceptación |
| Por qué elegible | `ELIGIBLE_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT`; clases de acción `blood`, `consult`, `fluid`, `ppi`, `reassessment`, todas soportadas; `live_equals_replay`; sin fallo de sombra, sin frontera, sin divergencia inesperada, sin vacío de espejo |
| Acciones | turno 1 «Reassess in 30 minutes»; turno 2 el paquete correcto (cristaloide + sangre + PPI + consulta) con «Reassess in 15 minutes»; después reevaluación hasta el minuto 60 |
| Instantánea | `gi_pressure_committed` |
| Almacén | ruta absoluta fuera del repositorio, superficie docente/investigación |
| Dominio | `sbp`, `dbp` comunes; `map` derivado |
| Coste | 0,6 s de reloj |

El enganche corre en el punto exacto del sitio de producción, con los mismos cinco argumentos
—la captura previa de la sombra, el estado que el motor acaba de comprometer, la sesión de sombra, las
acciones cuyo destino liquidó el pipeline y el identificador de envío—, envolviendo
`ShadowSession.observe`, que los recibe todos. El cableado de Streamlit lo cubre la suite de AppTest.

### 3.1 La trayectoria

Ancla autorizada del caso: SBP 88 / DBP 54.

| Minuto | Acciones del turno | Presión **común** escrita | Contrafáctico **legado** | Compromiso | Replay |
|---|---|---|---|---|---|
| 30 | reevaluación (30 min de hemorragia sin tratar) | **80 / 49 / 59** | 84 / 52 / 63 | atómico, `['dbp','map','sbp']` | exacto |
| 45 | **paquete**: cristaloide, sangre, PPI, consulta | **101 / 62 / 75** | 95 / 58 / 70 | atómico | exacto |
| 60 | reevaluación | **112 / 68 / 83** | 102 / 62 / 75 | atómico | exacto |

Tres minutos de autoridad sobre 60 minutos simulados; la granularidad es **un turno, una transacción**,
que es la del sitio de producción. Estado final del encuentro: SBP 112, DBP 68, MAP 83, sin arresto.
Clase de divergencia en los tres minutos: `EXPECTED_ARCHITECTURAL_DIVERGENCE`.

**Veredicto: `FIRST_DEVELOPMENT_AUTHORITY_EXPERIMENT_COMPLETED`.** Ninguna condición de parada se
disparó: sin `CoreInvariantError`, sin `UnresolvedBoundary`, sin acción no soportada, sin digesto
distinto, sin replay distinto, sin fallo del almacén, sin cambio de configuración, sin violación de
propiedad y sin intento de compromiso parcial.

### 3.2 Un defecto que encontró el propio experimento, y su corrección

En el minuto 30 el núcleo da una media de 59,538. El compromiso **deriva** la media del par de enteros
que escribe —`(80 + 2·49)/3 = 59,33 → 59`— y eso es lo que quedó en el estado y lo que la pantalla
muestra. Pero el **registro** daba forma a la media del núcleo por separado —`round(59,538) = 60`— y el
**replay forense** tenía una **segunda copia** de la misma regla, con el mismo error. Es decir: el
artefacto declaraba haber escrito un número que no escribió, exactamente en los minutos donde el redondeo
del par cruza un límite.

El estado y la pantalla siempre fueron coherentes; lo que estaba mal era la cuenta que el artefacto daba
de sí mismo, que es justamente para lo que existe. Corregido con **una sola definición** en `apply_shape`,
que leen el compromiso, el registro y el replay, y fijado con dos pruebas, una de ellas por conteo en el
texto fuente para que nadie vuelva a escribir una segunda copia. El experimento se volvió a correr
completo con el código corregido, y las cifras de §3.1 son las del código corregido.

## 4 · Validación forense (P3-42)

Desde el artefacto persistido y nada más.

| Comprobación | Resultado |
|---|---|
| Registros en el almacén | 3 por experimento, uno por minuto de autoridad, inmutables y de crear-sólo |
| Digesto verificado | sí | 
| Identidad coincide | sí |
| Completo | sí, sin minutos incompletos |
| `candidate_matches` | 3/3 |
| `transaction_matches` | 3/3 |
| `pressures_match` | 3/3 |
| `written_matches` | 3/3 |
| `outcome_consistent` | 3/3 |
| Veredicto del replay | «every committed minute reproduces» |
| El artefacto persistido contra la ejecución en vivo | **idénticos** en minuto, resultado, candidato común, candidato escrito, contrafáctico y clases de divergencia |

**Revisión causal:** la hemorragia baja la presión (80 contra la llegada de 88); la intervención la sube
(80 → 101 → 112); **no hay respuesta antes de la acción** —el paquete se ordena en el minuto 30 y la
primera subida es el minuto 45—; no hay ninguna respuesta paradójica; y no hay fuga de propiedad: los
únicos campos comprometidos son `sbp`, `dbp` y `map`, con `map` marcado `derived_in_display_from_common` y
todo lo demás en legado o sólo-comparación.

**Veredicto: `AUTHORITY_ARTIFACT_REPLAYS_EXACTLY`.**

## 5 · Reproducibilidad (P3-43)

Segunda corrida desde un encuentro limpio, en un proceso nuevo, con la misma instantánea, el mismo
entorno, la misma configuración y la misma secuencia, con identidad de experimento propia.

| | |
|---|---|
| Minutos | 3 contra 3 |
| Campos por minuto comparados | 15, incluidos `input_digest`, `candidate_digest`, `replay_digest`, `transaction_digest`, `written_digest` y `precommit_observable_digest` |
| Diferencias | **0** |
| Campos de cabecera comparados | 15 (caso, familia, dominio, entorno, instantánea, digesto de la Fase 2, versiones, propiedad, política de fallo, estado, minutos) |
| Diferencias | **0** |
| Difieren a propósito | `experiment_id` y `artifact_digest`, que son la identidad del intento |

**Veredicto: `DEVELOPMENT_AUTHORITY_RUN_REPRODUCIBLE`.**

## 6 · Revisión del primer experimento (P3-44)

### 6.1 Software

| Pregunta | Respuesta |
|---|---|
| ¿Funcionó el portón? | Sí: concede sólo en la configuración autorizada y rechaza las trece variantes atacadas |
| ¿Funcionó la propiedad? | Sí: sólo `sbp` y `dbp` comunes, `map` derivado, nada más movido |
| ¿Funcionó la atomicidad? | Sí: los tres minutos comprometen los tres campos juntos o nada |
| ¿Funcionó la procedencia? | **Con un vacío declarado**: el artefacto lleva 30/30 campos de cabecera y 20/20 por minuto, y las **clases** de acción por minuto, pero los **destinos** (`fate`) y los identificadores de orden salen vacíos (§6.4) |
| ¿Funcionó la persistencia? | Sí: tres registros inmutables por experimento, recuperables y verificables |
| ¿Funcionó el replay? | Sí: exacto en las cinco comprobaciones, en los dos experimentos |
| ¿Fue reproducible la segunda corrida? | Sí, digesto por digesto |
| ¿Se comportó la política de fallo? | **No se ejerció en vivo**: ninguna condición de parada se disparó. Su comportamiento está cubierto por las pruebas certificadas de detención (H1–H8, S14–S20) sobre este mismo HEAD |

### 6.2 Modelo causal

Sangrado ↓, tratamiento ↑, efecto estrictamente posterior a la acción, sin paradoja, sin frontera
estructural. Ver §4.

### 6.3 Calibración clínica

**ESTE EXPERIMENTO NO ESTABLECE CALIBRACIÓN CLÍNICA.** No se debe inferir validez clínica del éxito
técnico. Lo que quedó demostrado es que la tubería hace en vivo lo que hace en sombra, de forma atómica,
reproducible y auditable, con un punto nombrado y bajo mirada docente. Que los números sean los correctos
para un paciente es una pregunta distinta, y sigue abierta.

### 6.4 Vacíos de procedencia encontrados

1. **Los destinos de las acciones salen vacíos.** En la secuencia del sitio de producción,
   `authority.minute(...)` corre **antes** de `order_pipeline.settle(...)`, así que en ese instante el
   pipeline todavía no ha liquidado los destinos: el artefacto registra las clases de acción y deja
   `fate` y `order_id` en blanco. La vía certificada de la batería lee las órdenes del libro **después**
   del turno y sí los tiene, así que las dos vías no coinciden y la de producción es la más débil. Es un
   vacío de forense, no de seguridad, y moverlo es una decisión arquitectónica sobre el sitio de llamada
   autorizado: **no lo cambié**.
2. **El artefacto de un encuentro real no lleva clasificación de elegibilidad.** `open_site` no adjunta
   la fila de elegibilidad que la batería sí adjunta, así que el campo queda nulo.

**Veredicto de P3-44: `A · DEVELOPMENT_AUTHORITY_PIPELINE_VALIDATED`**, con los dos vacíos de procedencia
declarados y ninguno de ellos en el camino de la seguridad.

## 7 · Recomendación de la etapa siguiente (P3-45)

**Primaria: (1) repetir más escenarios de autoridad GI en desarrollo**, empezando por cerrar los dos
vacíos de §6.4 y por ejercer **en vivo** al menos una parada dura. Razón: el experimento validó la
tubería en un camino feliz de tres minutos; lo que falta para confiar en ella no es más fisiología, es
más cobertura de su propia máquina —las 26 trayectorias elegibles, los destinos de acción, y la política
de fallo ejercida de verdad y no sólo en pruebas—. Es barato, no toca fisiología y no pide ninguna
decisión clínica.

Alternativas, ordenadas:

| | Siguiente paso | Por qué no primero |
|---|---|---|
| 2 | Paquete de calibración clínica de la presión | Es el único camino a una afirmación clínica, pero necesita material y decisiones docentes que no existen; no se puede empezar con lo que hay |
| 3 | Atender los tratamientos GI no soportados (anticoagulación, antiagregante, vasopresor) | Desbloquea los 8 escenarios inelegibles, pero es fisiología nueva y decisión clínica |
| 4 | Añadir CRT al dominio de autoridad | Técnicamente contiguo, pero amplía el alcance antes de haber agotado el actual |
| 5 | Extender la autoridad en vivo a otra familia | Ninguna otra familia tiene su sombra en vivo lista; además `afterload_sensitivity` sí actúa ahí y no está identificado |
| 6 | Preparar la integración con el piloto visible al residente | Prohibido hoy, y prematuro: no hay calibración clínica |
| 7 | Detener o revisar la arquitectura | No hay motivo: la tubería se comportó |

**Límite duro:** aun con todo en verde, no se habilita autoridad visible al residente ni en producción,
no se modifica el primer piloto, no se amplía la autoridad más allá de la presión GI, no se implementa
fisiología de tratamiento no soportada y la instantánea **no** queda declarada clínicamente validada.
