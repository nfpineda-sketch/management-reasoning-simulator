# Fase 3 · Control manual de norepinefrina promovido a autoridad viva de desarrollo (P3-488 a P3-502)

> **Qué es.** La semántica manual de tasa de norepinefrina que la facultad ratificó (FD-NR-01, 2026-11-20: iniciar, aumentar, disminuir, suspender y reiniciar con **tasas absolutas explícitas en mcg/min**) pasa de ser una **sonda de desarrollo en la sombra** a ser **autoridad viva de desarrollo** sobre la **presión** (`sbp`, `dbp`, `map`) de los dos casos de hemorragia digestiva (`gi_bleed_57m`, `gi_bleed_72f`). Decisiones: FD-AUTHNE-01 a FD-AUTHNE-12 (2026-11-21).
>
> **Qué no es.** No es fisiología nueva, ni recalibración del tono, ni cambio del acoplamiento con la bomba, ni autoridad de consciencia ni terminal, ni despliegue a residentes, ni titulación automática, ni dosis por peso, ni otro vasopresor, ni validación clínica. `COMMON_CORE_RUNTIME_AUTHORITY` sigue en `False`; el motor de familias heredado sigue siendo la única autoridad fuera de esta excepción acotada. `clinical_core/` no se editó.

## 1. Por qué la norepinefrina seguía fuera (auditoría P3-488, sólo lectura)

En un encuentro real de GI bajo la concesión vigente (V3), «Start norepinephrine at 10 mcg/min» se espejaba como clase `norepinephrine` y el sitio se detenía con `UNSUPPORTED_AUTHORITY_ACTION: ['norepinephrine']` (el resultado certificado de FR-F). Cinco causas a la vez:

1. `unsupported_among` es una lista de permitidos **global** (soportadas + estructurales + sin fisiología común) que usan la compuerta, el sitio, la liquidación, la elegibilidad y el evaluador en seco; no contenía `norepinephrine` ni `infusion_adjustment`.
2. El adaptador GI no mapea ningún vasopresor: cada orden era un hueco declarado.
3. Las concesiones V1/V2/V3 dicen que la norepinefrina **no** está concedida y sus cuerpos están fijados por huella: no se editan.
4. El mapeo de tono (`runtime_tone_support`) era `DEVELOPMENT_SHADOW_ONLY`: una **copia de desarrollo** del adaptador que toma el **nombre** de un testigo del núcleo, nunca el registro ratificado, y que ningún adaptador registrado usa.
5. `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1` era un registro sellado que ningún ejecutable leía (`live_configuration.bound = false`).

Además, la superposición V1 de consciencia —que lleva la guarda de la frontera de colapso y la comprobación `one_course` contra las lecturas de la sesión— se construía sin el contribuyente de norepinefrina: con norepinefrina en la sesión y no en la superposición, la presión difería y **todo minuto** habría fallado `one_course`. La superposición debe correr la **misma hemodinámica** que la presión (invariante P3-380).

Lo que ya era autocontenido y no cambió: la repetición del candidato (se reconstruye del escenario serializado), la repetición de la superposición, la transacción de turno controlado por la autoridad, la parada efectiva y el ancla de procedencia.

## 2. Qué se añadió (clasificación del cambio)

| Clase | Cambio |
|---|---|
| GRANT | `runtime_ne_grant.py`: `GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1` (sólo datos, fijada por huella `d79637c4…a45fb7`, con guarda de importación). **No** muta ni reemplaza la V3. |
| GRANT / OPERADOR | Selector `MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT` = `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1` (id exacto; nunca desde un Secret). Nunca abre la concesión **solo**: exige también el snapshot de presión ratificado. |
| RUNTIME_BINDING | `runtime_tone_snapshot.py`: lee y verifica el registro ratificado del tono (huella de archivo, digesto del registro, segunda copia tipificada, igualdad con el `CENTER_REFERENCE` del núcleo, `LOW`/`HIGH` nunca se leen), objeto congelado que cada consumidor re-deriva. |
| RUNTIME_BINDING | `runtime_ne_authority.py`: contrato de la orden **propio de la autoridad** (independiente del mapeo de la sombra y comparado con él), adaptador ligado al tono, superposición con la misma hemodinámica, artefacto y repetición. |
| RUNTIME_BINDING | `runtime_authority.py` (compuerta, `open_site`, clasificación por concesión, minuto, artefacto, repetición), `runtime_shadow.py` (adaptador de la sesión), `runtime_authority_pair.py` (un parámetro opcional de la repetición de la superposición), `runtime_authority_session.py` (el selector forma parte de la configuración de una sesión). |
| ARTIFACT / REPLAY | El artefacto nombra la concesión nueva, el bloque `norepinephrine_authority` y el contrato de cada minuto; `real_artifact_problems`, `verify_artifact` y la repetición resuelven ambos registros de concesiones. |
| UI / OPERADOR | **Sin cambio**: la página no nombra el selector ni los módulos; el entorno docente de revisión sigue exigiendo la configuración de sólo presión. |

## 3. La concesión

Ámbito exacto: **sólo** `sbp`, `dbp`, `map` (más el soporte de tono como **estado interno** de la corrida: no es un dominio, no lo ve el residente, no se puntúa). Casos `gi_bleed_57m` y `gi_bleed_72f` (cumplen el mismo contrato); entorno `development`; ventana de 240 minutos; núcleo `PHASE2_AMENDMENT_3` (`867bac09…`). Liga: el snapshot de presión `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` (digesto de configuración `70e6826c…`), el snapshot de tono (`bdc90a17…`), el sucesor de orden segura del lector (`a71a3888…`), la versión del escritor (`norepinephrine_rate_history/P3-431`), las operaciones y unidades permitidas y la identidad de repetición. Lista lo que **no** concede (producción, residentes, piloto, consciencia, `mental_status`, terminal, colapso, validación clínica, recalibración, dosis por peso, titulación automática, otro vasopresor, familias limitadas por la bomba, edema pulmonar, control de fuente, cualquier dominio no presión, variable de tono visible, puntuación).

## 4. Camino de ejecución

orden cruda → lector certificado (sucesor 2) → espejo → **contrato propio de la autoridad** → historia de tasa (`NorepinephrineRateHistory`, el escritor del núcleo) → soporte vasoconstrictor común → tono común `T` → presión. **No hay camino directo fármaco → mmHg.** Los valores (`tone_gain`, `half_effect_rate_mcg_min`, `onset_tau_min`, `offset_tau_min`) salen del registro ratificado, por el **único** campo de perfil y por las constantes del escritor que la orden construye; ninguno se recalculó ni se cambió.

## 5. Contrato de la orden y falla cerrada permanente

Se lee la orden **como se escribió** (frontera orden cruda; el lector sigue siendo la barrera correcta). La autoridad la verifica **de forma independiente**: tipo, operación (`start`/`adjust`/`continue`/`stop`), unidad exacta `mcg/min`, tasa finita positiva, una sola tasa, recibo coherente, una suspensión sin tasa, el primer movimiento un inicio, una cronología íntegra y una tasa que el escritor representa. Después compara la historia que leyó con la de la sombra: si difieren, o la sombra rechazó una orden que el contrato lee, o hay un hueco de la sombra que el contrato no explica, es un problema. Sólo son benignos los huecos «reemplazada dentro de su minuto» y «suspensión de nada», **y sólo si el contrato los explica**.

| Orden | Resultado |
|---|---|
| inicio, aumento, disminución, suspensión, reinicio con tasa absoluta explícita en mcg/min | soportada (equivale a las trayectorias certificadas) |
| mcg/kg/min, otra unidad, tasa sin unidad, tasa cero o negativa o no finita, suspensión con tasa, continuación **sin** tasa, ajuste/continuación antes de un inicio, orden que no nombra el fármaco, otro vasopresor, tasa fuera de lo que el escritor representa | **PERMANENT_FAIL_CLOSED**: el sitio se detiene con `UNSUPPORTED_AUTHORITY_ACTION` nombrando la clase; sin recuperación, sin retroceso silencioso al heredado ni a la concesión anterior |
| objetivo de PAM/PAS, aritmética relativa, número sin unidad | el lector las convierte en **pregunta** (no se ejecuta nada): la sesión continúa con la infusión que ya tenía |

Antes del primer compromiso real, la falla deja el encuentro heredado intacto (`EXPERIMENT_HALTED`); después, `INVALID_FOR_CONTINUATION` (parada efectiva, sin semántica terminal).

## 6. Superposición de consciencia bajo tono (limitación abierta)

La superposición V1 corre ahora la **misma** hemodinámica (con el contribuyente de norepinefrina). No es autoridad, no escribe `mental_status`, no es visible al residente y no se usa como calibración. Lo que dice de la consciencia **bajo tono** está **sin resolver** (`CONSCIOUSNESS_UNDER_TONE_UNRESOLVED`, limitación abierta de FD-TONE-RATIFY) y se declara en el artefacto; se usa **sólo** como la guarda de frontera de colapso que ya era. Esa combinación **no ha sido revisada por la facultad**: ver decisiones pendientes.

## 7. Artefacto y repetición

Un artefacto bajo esta concesión nombra su identidad y huella, el bloque `norepinephrine_authority` (configuración de tono, escritor, alcance, limitaciones, lector), y cada minuto compromete un contrato limpio con su digesto. La repetición reconstruye candidato, minutos y superposición **desde el artefacto solo** (también en un proceso nuevo); un artefacto renombrado, rotulado de otro modo, con el bloque quitado o añadido a otra concesión, con la configuración de tono, la ganancia, el escritor o la historia alterados, **falla aunque se recompute su digesto**. Los artefactos V1/V2/V3 se verifican y se repiten como antes.

## 8. Qué se probó (ver `test_phase3_ne_authority.py` y el punto de control)

* Equivalencia exacta minuto a minuto (32 minutos cada uno, 0 diferencias) con **FR-F** (`CENTER_REFERENCE` revisado por humanos) y con **TIT-1 a TIT-5**, en el camino vivo; ambos casos de GI.
* Sin norepinefrina, la serie es la de la concesión anterior **al último dígito** (ambos casos, tres órdenes de manejo).
* Matriz de falla cerrada, parada permanente, reapertura, selector que no liga, tono sin la presión ratificada, lector cambiado.
* `LOW`/`HIGH` nunca se leen; los mutantes del registro del tono, los de la concesión y los del artefacto se rechazan (secciones A, B y G de la prueba); los del artefacto fallan **con el digesto recomputado**; un mutante de la comprobación del rótulo que sobrevivía a la primera pasada se cerró con una prueba directa.
* Aislamiento: sólo `sbp`/`dbp`/`map` se mueven; ninguna clave nueva en lo que ve el residente; `mental_status` es el del motor heredado; la página no nombra el selector.

## 8 bis. Revisión adversarial independiente (una, de sólo lectura)

Se reprodujo cada hallazgo **antes** de corregirlo. Uno fue material (A1): un encuentro de norepinefrina **rotulado como la concesión anterior**, con una superposición honesta «injertada», pasaba la verificación; ahora la concesión que el artefacto nombra decide, y el contenido debe concordar (g8). Los demás: las filas del contrato son las órdenes del escritor y su semántica se **recomputa** (A2, g9); la clase acarreada está **modelada**, no «no soportada», en las disposiciones del artefacto (A3, g10); el contrato lee la clase como el sitio y nunca aprueba lo que no ve (A4, d9); verificar un artefacto anterior no registra nada nuevo en el núcleo (A5, g11, en un proceso nuevo); y el artefacto lleva el rótulo que la concesión nombra (A6, g12). **A7 se declara, no se repara** (detención dura): una orden compuesta con cláusulas de titulación («q5 min increase by 2», «(max 20)», «at 5 to 10 mcg/min») la lee el lector congelado sin esas cláusulas; ver las decisiones pendientes.

## 9. Limitaciones y decisiones pendientes

1. **Superposición de consciencia bajo tono** (§6): sin revisión docente; decidir si la guarda de frontera de colapso es aceptable bajo tono o debe revisarse antes de ampliar.
2. **«Continue norepinephrine» sin tasa** es hoy falla cerrada (no está en la lista ratificada; la sombra lo leía como «sin cambio»): decidir si se acepta como no-op.
3. **`COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED`** sigue monitoreada: no se promovió en familias limitadas por la bomba.
4. **Revisión humana de la autoridad viva:** las trayectorias que la facultad revisó eran de la sombra; que la autoridad viva las reproduce es una igualdad **medida**, no un nuevo juicio humano.
5. Sin firma del registro de punto de control (mismo límite que `TD-153`, ítem 7).
6. **Órdenes compuestas con cláusulas de titulación (A7):** el lector congelado deja fuera esas cláusulas y la orden se ejecuta como la tasa explícita que sí contiene; reparar el lector exigiría una tercera sucesión y una decisión docente, y **no** se hizo. Tampoco se probó de extremo a extremo una orden de norepinefrina **retenida** por la cola de órdenes pendientes.
7. Sigue **sin** implementarse, por mandato: familias limitadas por la bomba, titulación por objetivo, dosis por peso, otro vasopresor, autoridad de consciencia o terminal, piloto con residentes.
