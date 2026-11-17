# Ratificación de la región conjunta de GI y cierre de la calibración de presión, para desarrollo (P3-367 a P3-374)

Fecha: 2026-11-16. Rama: `phase-3-runtime-integration`. Alcance: **sólo registros, decisiones y documentos**. **No** hay calibración nueva, **no** cambia la fisiología, **no** se busca un punto mejor, **no** se compara de nuevo con el motor heredado, **no** se toca ningún ejecutable, parámetro, candidato ni trayectoria, **no** se amplía la autoridad, **no** se abre la Enmienda 3, **no** se implementa norepinefrina ni control de fuente, **no** hay piloto con residentes y **no** es validación clínica.
Decisiones: FD-RATIFY-01 a FD-RATIFY-07 y FD-P3-248 a FD-P3-251 (`docs/COLA_DECISIONES_AI_ADVISOR.md`). Deuda: `TD-152` (y una nota en `TD-147`).

Distingo en todo el documento: **implementado** · **probado** (con la cifra) · **pendiente**.

> **Nota fechada (2026-11-16, ciclo de promoción; `docs/PHASE3_GI_PRESSURE_PROMOTION.md`):** este documento describe la situación **al momento de la ratificación**: la instantánea era un registro que nada ejecutable leía y **no** estaba vinculada a la autoridad viva. **Esa afirmación ya no es la vigente**: la autoridad viva de desarrollo de presión de GI ejecuta ahora `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` con la concesión `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2` (FD-PROMOTE-01 a FD-PROMOTE-07). El resto de lo decidido aquí (limitación monitoreada, `LOW`/`HIGH` sólo testigos, Enmienda 3 cerrada) sigue vigente.

## 0 · Qué se decidió (decisión docente del 2026-11-16)
| Decisión | Contenido |
|---|---|
| **FD-RATIFY-01** | La re-revisión ciega tiene `ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 3, `RECALIBRATE` 0, `REJECT` 0: `GI_JOINT_REGION_V1` es **aceptable para uso de desarrollo**. |
| **FD-RATIFY-02** | La limitación repetida en FR-B / FR-C / FR-E (la respuesta de presión a la reanimación con sangre queda en el **extremo bajo** de lo plausible) es una **limitación de desarrollo monitoreada**; **no** es motivo para recalibrar; no se reabre la calibración sólo para subir esas trayectorias unos mmHg. |
| **FD-RATIFY-03** | `CENTER_REFERENCE` se elige como `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`: está dentro de la región factible conjunta, maximiza el margen simultáneo a las restricciones de comportamiento, pasó la re-revisión humana ciega y ningún escenario recibió `RECALIBRATE` ni `REJECT`. Es una **instantánea de desarrollo**, no calibración clínica, ni autoridad de producción, ni validación con residentes. |
| **FD-RATIFY-04** | `LOW` y `HIGH` siguen siendo **testigos de prueba únicamente**; no se promueven. |
| **FD-RATIFY-05** | La Enmienda 3 sigue **cerrada**: la fisiología actual demostró una región conjunta factible y aceptable para humanos. |
| **FD-RATIFY-06** | No se compara de nuevo con el motor heredado como requisito de este cierre; el heredado sigue sin autoridad. |
| **FD-RATIFY-07** | La calibración de presión de GI se considera **cerrada para desarrollo**, salvo una contradicción entre familias, un efecto educativo peligroso, un fallo ante una intervención nueva o un fallo de generalización. Las diferencias numéricas menores de preferencia **no** la reabren. |

## 1 · P3-367 · Registro de la re-revisión humana (HECHO, con una salvedad de procedencia)
`docs/revision/PHASE3_HUMAN_FACULTY_REREVIEW.json` (`HUMAN_FACULTY_REREVIEW_RECORD`, sellado). Conjunto `GI_JOINT_REGION_V1_FACULTY_REREVIEW` (digesto `c30ab7f1…`), candidato `CENTER_REFERENCE` (la pantalla no lo nombraba), cuatro escenarios en el orden FR-B, FR-C, FR-E, FR-G, sólo presión en la primera pasada. Cada juicio lleva el digesto del ítem revisado.

| Escenario | Global | Q1 Dirección | Q2 Momento | Q3 Magnitud | Q4 Respuesta al manejo | Q5 Riesgo educativo |
|---|---|---|---|---|---|---|
| FR-B | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | **Too small** | Coherent | Maybe |
| FR-C | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | **Too small** | Coherent | Maybe |
| FR-E | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | **Too small** | Coherent | Maybe |
| FR-G | `ACCEPT` | Expected | Plausible | Plausible | Coherent | No |

Las interpretaciones docentes se transcriben **sin cambiar una palabra** (la instrucción «no recalibrar este escenario de forma aislada» queda como decisión, no como interpretación). Cuentas: `ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 3, `RECALIBRATE` 0, `REJECT` 0.

**Salvedad de procedencia (declarada, no escondida).** El encargo pedía **leer el registro persistido** y no inferir respuestas del propio encargo si difería. **Ese registro no está en este contenedor**: `~/faculty_review/R1/store` está vacío y los únicos almacenes de re-revisión que existen son sintéticos, de las pruebas del autor; no se usaron como evidencia humana. Se le preguntó a docencia y **eligió registrar lo reportado**, como se hizo con la primera revisión (P3-301). Por eso el registro lleva `verification = REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE` y declara **no verificados**: las respuestas contra los registros persistidos, el orden persistido de los escenarios, el estado de finalización persistido, los eventos de bloqueo y envío, y los comentarios libres (no se reportó ninguno). Si el almacén persistido llega a aportarse, comparar y, si difiere, **detener y reabrir** esta ratificación.

**Clases de evidencia separadas.** `HUMAN_FACULTY_REREVIEW` (este registro y las filas FD-RATIFY) · `MODEL_ANALYSIS` (el registro de la región, `PHASE3_GI_JOINT_REGION_V1.json`) · `TEST_RESULT` (las pruebas) · `LEGACY_COMPARATOR` (no se mostró ni se usó).
**La primera revisión humana queda intacta:** registro `9ba80fa7…`, mismo archivo byte a byte (huella `sha256` fijada), conjunto `f65d1127…`, siete escenarios con `ACCEPT` 1 / `ACCEPT_WITH_LIMITATION` 5 / `RECALIBRATE` 1 / `REJECT` 0; no se transfieren juicios de una a otra.

## 2 · P3-368 · Ratificación de la región (HECHO)
`GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1` (`docs/revision/PHASE3_GI_JOINT_REGION_V1.json`, digesto `bf7361a1…`) queda **`RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS`** (`docs/revision/GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json`). **No** es calibración clínica ni fisiología de producción aprobada por la autoridad.
**La estructura correlacionada se conserva.** La región es el objeto `c × escala` con el núcleo del cristaloide (la tasa **nunca** es una coordenada aparte: es `c × escala`); no se aplana en rangos independientes, porque una tasa de un extremo con una escala del otro queda **fuera** de la región. La ratificación fija el digesto y el `sha256` del registro de la región (no se editó), copia su estructura de coordenadas y su advertencia de proyecciones, y comprueba en cada punto de la red que `tasa = c × escala`.

## 3 · P3-369 · Instantánea `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` (HECHO)
`docs/revision/GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json`. Es el **enlace exacto ya certificado** de `CENTER_REFERENCE`, **copiado** del registro de la región (`witnesses.CENTER_REFERENCE.binding`), **no recalculado ni optimizado**, y no se consideró otro punto:

| Coordenada | Valor |
|---|---|
| tasa de sangrado | 8,970853509 mL-eq/min |
| `c` (tasa ÷ escala) | 0,003326066 /min |
| escala de precarga | 2697,136369656 mL-eq |
| núcleo del cristaloide | `e` 0,213115961 · `s` 0,835 · `tau` 60,624 min |
| posición de llegada | 0,5 |

Los cinco valores se eligieron y se hallaron **juntos**; ninguno se puede cambiar por el de otro testigo.
**Por qué `CENTER_REFERENCE`:** (a) es el punto **más alejado de toda frontera** de la región analizada (márgenes sin tratar, de una unidad, de cristaloide y de región cerrada iguales y los mayores posibles a la vez; menor margen normalizado 0,126), es decir, la máxima robustez dentro de la región factible ya analizada; y (b) **pasó la re-revisión humana ciega**. No se eligió por parecerse a ningún objetivo (FD-RATE-15).
**`LOW` y `HIGH`** conservan su rol `TEST_WITNESS_ONLY` (`promoted = false`); sus enlaces siguen siendo los del registro de la región y difieren del de la instantánea.

**Lo que esta instantánea NO es, y que conviene tener presente.** Es un **registro**. **Nada ejecutable lo lee.** La autoridad de desarrollo de presión de GI en vivo (instantánea `gi_pressure_committed`, con `GI_DEVELOPMENT_SNAPSHOT_V1`) **no cambió** y sigue corriendo la configuración que mostró la **primera** revisión: las trayectorias `CENTER_REFERENCE` que la docencia aceptó provienen del arnés de la región conjunta, no de la autoridad viva (el registro de la región reproduce la configuración actual y muestra que las presiones candidatas difieren de las revisadas antes). **Vincular la autoridad viva a esta instantánea sería un paso EJECUTABLE aparte, con su propia autorización y su propia recertificación; no es de este ciclo** (`TD-152`, ítem 3; decisión pendiente).

## 4 · P3-370 · Limitación monitoreada `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` (HECHO)
`docs/revision/GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE.json`. **Significado:** en FR-B, FR-C y FR-E la respuesta de presión tras cristaloide más glóbulos rojos está en el extremo bajo del rango plausible para la docencia (Q3 «Too small» en los tres, con Q1 Expected, Q2 Plausible y Q4 Coherent). **Estado:** `ACCEPTED_WITH_LIMITATION` · `MONITOR` · `NO_CURRENT_RECALIBRATION`. **Se reabre sólo si:** otra familia muestra el mismo déficit; el orden de las intervenciones se vuelve incorrecto; el riesgo educativo pasa a ser material; o una revisión docente nueva cambia el juicio. **No** es motivo para reabrir: subir esas trayectorias unos mmHg ni una preferencia numérica menor.

## 5 · P3-371 · Estado de la presión de GI (HECHO)
`GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED`. **Sólo para desarrollo.** **No** significa producción, validación clínica ni despliegue a residentes. Se reabre únicamente por las condiciones de FD-RATIFY-07.

## 6 · P3-372 · Siguiente prioridad de fisiología (REGISTRADA, no implementada)
**Vía común de tono vascular / vasopresor** (alta prioridad), motivada por la parada por acción no soportada de la norepinefrina en FR-F (primera revisión; parada correcta, `TD-147`, ítem 3). Arquitectura deseada: **norepinefrina → tono vascular común `T` → presión y perfusión → entrega y deuda posteriores**, con interacción con **volumen / precarga** y con **bomba / flujo anterógrado**. En este ciclo **no se diseñó ni se implementó**: ninguna orden nueva se soporta, ninguna parada cambia.

## 7 · P3-373 · Validación (HECHA; cifras abajo)
* **Pruebas nuevas** (`test_phase3_joint_region_ratification.py`, 9, y `test_phase3_joint_region_ratification_records.py`, 1): el registro humano sellado, distinto de las otras clases y fijado a lo revisado (`test_t1`); las respuestas exactamente como se reportaron y la procedencia que **no** finge verificación (`test_t2`); la primera revisión preservada, byte a byte (`test_t3`); el enlace de la instantánea igual al certificado, copiado y no recalculado (`test_t4`); lo que revisó la docencia es **exactamente** lo que el registro asigna a `CENTER_REFERENCE`, en los cuatro escenarios (`test_t5`); `LOW`/`HIGH` siguen siendo sólo de prueba (`test_t6`); la región ratificada con su estructura correlacionada y su registro intacto (`test_t7`); la limitación, su regla de reapertura y el estado cerrado (`test_t8`); nada ejecutable nombra los registros nuevos, sin ampliación de autoridad, Enmienda 3 cerrada (`test_t9`); las decisiones, la deuda, `CLAUDE.md`, este documento y el punto de control dicen lo mismo y el punto de control está sellado y fijado a los registros (`test_phase3_joint_region_ratification_records.py`).
* **Mutaciones** (re-selladas, para que no las atrape sólo el sello): 18 de 18 atrapadas, 11 sobre los registros y 7 sobre los documentos y el punto de control (enlace movido; respuesta cambiada; cuentas; procedencia «verificada»; `LOW` promovido; vínculo vivo declarado; regla de reapertura recortada; registro de la región editado en bytes; primera revisión editada; Enmienda 3 abierta; un ejecutable que nombra la instantánea; y, en la prueba de registros documentales, una fila de decisión, el ítem de deuda, el puntero de `CLAUDE.md` o la salvedad del vínculo vivo que desaparecen, y un punto de control con veredicto B, con vínculo vivo declarado o con una confirmación en falso). Una de las primeras, la del registro de la región, se atrapó tras repetirla con una edición real de bytes (la primera versión del script no cambiaba nada).
* **Sin cambio ejecutable (comprobado por diff):** sólo cambian documentos, registros, `CLAUDE.md` y una prueba nueva; ningún `.py` que no sea de prueba.
* **Costosas, clasificadas** (no se corrió la suite completa de ≈ 12 966 pruebas):
  * `REQUIRED`, ejecutadas: las pruebas nuevas; las que leen el Decision File, el registro de deuda o los registros de la revisión (la re-revisión y su punto de control, la región conjunta, el análisis de la primera revisión, la factibilidad conjunta, la escala de la tasa, las decisiones de presión, el lenguaje de los registros, la instantánea y la revisión previa a la autoridad de GI); las guardas que recorren el árbol (aislamiento, ingestión externa); `run_regressions.py`.
  * `NOT_REACHABLE`: la suite completa, porque no cambió ningún comportamiento ejecutable ni ningún módulo que no sea de prueba.
  * `ALREADY_VALID_ON_EQUIVALENT_CODE`: las guardas dormidas, las rutas del reloj, los casos sin conexión y el contrato de frontera v2 corrieron en verde sobre código idéntico (el ciclo anterior); el código no cambió desde entonces.
  * `UNKNOWN`: ninguno.

## 8 · P3-374 · Punto de control
`docs/revision/PHASE3_GI_PRESSURE_CALIBRATION_CLOSURE_CHECKPOINT.json`: **A · GI_PRESSURE_DEVELOPMENT_REGION_RATIFIED_AND_CLOSED**, **con la salvedad de §1**: el registro humano es **reportado, no verificado contra el almacén persistido** (elección expresa de docencia). Las otras opciones: B (el registro humano no coincide) no se pudo evaluar sin el almacén; C (el enlace de la instantánea no coincide) se descarta por prueba; D (la ratificación exige un cambio ejecutable) se descarta, porque es sólo un registro: vincular la autoridad viva sí sería ejecutable y **no** se hizo.

## 9 · Limitaciones y lo que sigue pendiente
* **Registro humano no verificado contra el almacén persistido** (§1). Es el punto más débil de esta ratificación. Una persona revisora, cuatro escenarios, dos casos de GI, sólo presión: **no** es validación clínica.
* **La instantánea no está vinculada a la autoridad viva** (§3): las trayectorias aceptadas no son las que hoy produce el simulador en vivo. Hasta que docencia autorice un paso ejecutable, el «cierre» es del **objeto de desarrollo** (región, instantánea y su limitación), no de lo que ve quien usa el entorno de revisión.
* **FC y relleno capilar** no se mostraron ni se juzgaron en esta re-revisión (pantalla sólo de presión, FD-REREVIEW-23): no hay juicio humano sobre su coherencia con la presión de esta configuración.
* **El extremo bajo de la respuesta a la sangre** es una limitación aceptada y monitoreada (§4), no resuelta.
* **El tono vascular / vasopresor** sigue sin existir (§6): hoy el simulador se detiene ante la orden.
* **Este ciclo no tocó** la primera revisión, el conjunto de la re-revisión, la región, `clinical_core/` (digesto vivo = `a0af7d08…`), `family_engine.py`, la fisiología, la autoridad, la concesión, la puntuación, el primer piloto, corpus, V3 ni baselines.

## 10 · Enunciados anteriores que este ciclo supera (los textos históricos no se reescriben)
* «La re-revisión humana sigue **sin hacerse**» (`CLAUDE.md`, `docs/PHASE3_FACULTY_REREVIEW_INTERACTIVE.md` §13 y §14, `PHASE3_FACULTY_REREVIEW_CHECKPOINT.json` y `…_BLINDNESS_PATCH_CHECKPOINT.json`, `TD-151`): era cierta cuando se escribió; hoy la re-revisión está **reportada como completada** (§1).
* «Candidatos `JOINT_REGION_V1_CANDIDATE` pendientes de re-revisión humana» (`CLAUDE.md`, `docs/PHASE3_GI_JOINT_REGION.md`, `TD-150`): resuelto por §1 y FD-RATIFY-01.
* «Sin punto elegido» (la región conjunta, `TD-149`, `TD-150`): desde FD-RATIFY-03 `CENTER_REFERENCE` es la **instantánea de desarrollo**; sigue sin ser un punto clínico ni de autoridad.
