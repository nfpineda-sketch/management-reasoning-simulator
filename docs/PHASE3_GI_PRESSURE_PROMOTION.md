# Promoción de la instantánea ratificada de presión de GI a autoridad viva de desarrollo (P3-375 a P3-386)

Fecha: 2026-11-16. Rama: `phase-3-runtime-integration`. Alcance: **configuración y vínculo de la capa de la Fase 3**; sin fisiología nueva.
Decisiones: FD-PROMOTE-01 a FD-PROMOTE-07 y FD-P3-252 a FD-P3-256 (`docs/COLA_DECISIONES_AI_ADVISOR.md`). Deuda: `TD-153` (y notas fechadas en `TD-152` y `TD-150`).

**Qué cambia y qué no.** La autoridad viva de desarrollo de presión de GI (`sbp`, `dbp`, `map` derivada; sólo `gi_bleed_57m` y `gi_bleed_72f`; sólo el entorno de desarrollo; con concesión explícita) pasa a ejecutar **exactamente** `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` (el `CENTER_REFERENCE` ratificado el 2026-11-16), en lugar del punto anterior `gi_pressure_committed`. Hasta este ciclo esa instantánea era **un registro que nada ejecutable leía**: «ratificada por humanos» no era «comportamiento vivo». Este ciclo elimina esa diferencia, y nada más. **No** hay calibración nueva, **no** se busca otro punto, **no** se promueve `LOW` ni `HIGH`, **no** se corrige la limitación monitoreada `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE`, **no** se abre la Enmienda 3, **no** se implementa norepinefrina ni control de fuente, **no** hay autoridad de consciencia ni terminal, **no** hay despliegue a residentes y **no** es validación clínica.

Distingo en todo el documento: **implementado** · **probado** (con la cifra) · **pendiente**.

## 0 · Decisiones (encargo del 2026-11-16)
| Decisión | Contenido |
|---|---|
| **FD-PROMOTE-01** | La autoridad viva ejecuta la instantánea exacta; sin recalibrar, optimizar ni elegir otro punto. |
| **FD-PROMOTE-02** | El linaje de la Fase 2 se conserva; si hiciera falta un núcleo sucesor sería **certificado** y con linaje explícito, y las reconstrucciones históricas seguirían posibles. |
| **FD-PROMOTE-03** | No es un experimento de fisiología nueva: sin mecanismo nuevo, sin Enmienda 3, sin norepinefrina, sin control de fuente, sin cambio de consciencia ni de terminalidad. |
| **FD-PROMOTE-04** | Alcance: `gi_bleed_57m` y `gi_bleed_72f`; dominios `sbp`, `dbp`, `map` derivada. |
| **FD-PROMOTE-05** | Concesión **versionada** que liga la instantánea y la huella de su sucesor certificado; la concesión anterior no se muta en silencio y sigue legible. |
| **FD-PROMOTE-06** | La autoridad viva debe **reproducir las trayectorias `CENTER_REFERENCE` ratificadas** dentro del contrato de redondeo existente; **no** se compara con la trayectoria de la autoridad anterior. |
| **FD-PROMOTE-07** | La limitación `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` sigue como limitación monitoreada: la promoción no la «arregla». |

## 1 · P3-375 · Auditoría de linaje (sólo lectura)
- **Núcleo vigente:** `PHASE2_AMENDMENT_2`, digesto `a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2` sobre 144 fuentes; el cierre histórico (`22b90a6f…`, 141 fuentes) y la Enmienda 1 (`10b45ce2…`, 142) se reconstruyen desde él. `clinical_core/` **no cambió** en este ciclo (diferencia vacía).
- **Dónde viven hoy los valores vivos de presión de GI:** **no** en una constante de `clinical_core/`. Salen de los literales del motor heredado traducidos al núcleo común por el adaptador de la Fase 3 (la escala es `LEGACY_ML_PER_CIRCULATION_UNIT`; la tasa es `0,003 × 833,33`; el kernel del cristaloide viene de `family_engine.GI_BLEED`), y se aplican sobre objetos que la **capa de la Fase 3** construye por sesión.
- **Aprobación vigente (la anterior):** `gi_pressure_committed`, concesión `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1` (`FD-P3-203`), huella de concesión fijada.

## 2 · P3-376 · Mapeo ejecutable (seis coordenadas)
| Coordenada ratificada | Valor ratificado | Valor vivo anterior | Dónde se ejecuta |
|---|---|---|---|
| Tasa de sangrado | **8,970853509** mL-eq/min | 2,5 mL/min (`0,003 × 833,33`) | `GIHaemorrhage.blood_loss_ml_per_min` (escritor de la familia) |
| Escala de precarga | **2697,136369656** mL-eq | 833,333 mL-eq | `CoreProfile.preload_curve_scale_ml` |
| `c = tasa / escala` | **0,003326066** /min | 0,003 /min | (derivada: la tasa **nunca** viaja sin su escala) |
| Posición de llegada | **0,5** | 0,5 | `CoreProfile.arrival_preload_fraction` (**igual**) |
| Kernel del cristaloide `e` | **0,213115961** | 0,125 | `Crystalloid.effective_ml_per_ml` |
| Kernel `s` | **0,835** | 0,6 | `Crystalloid.transient_share` |
| Kernel `tau` | **60,624** min | 30,0 min | `Crystalloid.leak_tau_min` |

**Cinco de las seis coordenadas difieren** (tasa, escala, `e`, `s`, `tau`); la posición de llegada ya era 0,5. Las magnitudes del perfil que **no** cambian (acoplamiento de bomba 1,0; sensibilidad a la poscarga 0,3; rodilla de bajo gasto 0,5; SBP/DBP por déficit de presión 45/25) son las del punto anterior. **Ninguna coordenada requirió fisiología nueva**: las seis tienen un campo existente y modificable en objetos de la capa. No hubo parada por «coordenada que exige fisiología nueva».

## 3 · P3-377 · Decisión de sucesor: **A · `CONFIG_ONLY_PROMOTION_SUFFICIENT`**
- Las seis coordenadas se aplican con `dataclasses.replace` sobre campos **existentes** en el adaptador de la capa de la Fase 3 (perfil, escritor de la hemorragia, contribuyentes de cristaloide). Ninguna vive en una constante de `clinical_core/`; por tanto **no se necesita un núcleo sucesor** (ni B ni C), y la instantánea **sí es ejecutable** con la arquitectura actual (no es D).
- **Huella del predecesor:** `PHASE2_AMENDMENT_2`, `a0af7d08…586ce2` (144 fuentes). **Huella del sucesor:** **no existe**: el núcleo activo es el mismo miembro certificado; la compuerta de linaje sigue exigiéndolo. El **digesto de la capa de la Fase 3** sí cambia (el módulo de vínculo entra en `LAYER_SOURCES`); no se escribe aquí (un documento no puede contener la huella del árbol que lo incluye).
- **Probado:** la igualdad con `CENTER_REFERENCE` por la página real (§7) es la prueba empírica de que la configuración basta.

## 4 · P3-378 y P3-380 · Vínculo vivo (implementado y probado)
**Módulo nuevo `runtime_pressure_snapshot.py`** (en `LAYER_SOURCES`): vincula la autoridad viva a la instantánea o **se niega**, sin retroceso.
- **Pins en el código:** el archivo del registro, el de la ratificación y el de la región por su `sha256`; el digesto de cada registro y el del registro humano de la re-revisión; el digesto de los seis valores y el de la **configuración completa**: `70e6826cb2844bace6e3249058638340d00d80f84f8fdd2a5a2e752028db0641`. Los seis valores están **tipeados una segunda vez** en el código y deben igualar al registro campo por campo.
- **Rechazos por nombre** (`PRESSURE_SNAPSHOT_*`): no es un registro; id o estado distintos; digesto distinto; parámetro modificado; tasa que no es `c × escala`; testigo de prueba (`LOW`/`HIGH`) en su lugar; ratificación o región que no son las fijadas; registro humano distinto; ilegible.
- **Cómo la usan las capas:** la sesión de sombra (`ShadowSession._open`) pide el vínculo sólo si el entorno nombra **exactamente** el id (recortado); si lo nombra y **no** vincula, **no abre corredor** (`PressureSnapshotNotBound`) y **no cae** al punto anterior; el adaptador de GI se configura con la configuración **verificada** (`GiHaemorrhageAdapter.configured`), que cada consumidor vuelve a comprobar contra los pins (un objeto armado a mano o con un campo forzado no se acepta); la superposición de consciencia (V1 exacta) y el conjunto de la región se vinculan a **esa misma** configuración, y una mezcla se rechaza. **Comprobación explícita y nombrada** (`PRESSURE_CONFIGURATION_MISMATCH`, clase de parada de configuración): antes de tomar el candidato, el sitio exige que la sesión haya corrido la configuración que nombra su instantánea aprobada (re-vinculada de los registros en cada minuto, sin caché); un sitio V2 con una sesión V1, o al revés, no compromete nada y dice por qué. La compuerta y `open_site` comparan además, **en tiempo de ejecución**, el digesto de configuración que fija la concesión con el que el vínculo ejecutaría (la comparación vive en la compuerta y no en el módulo de la concesión, que no importa nada del repositorio a propósito: `test_g12`). Si la sesión no pudo vincular, el motivo de «sin candidato» del propio registro de autoridad nombra `PressureSnapshotNotBound`.
- **Aprobación registrada:** `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` entra al registro de autoridad **junto** a `gi_pressure_committed`, con las siete magnitudes del perfil, y con la tasa y el kernel en `scenario_parameters`; el digesto de valores cubre ambos grupos. `LOW` y `HIGH` **no** están registrados.
- **Probado:** `test_phase3_pressure_promotion.py` `b1` a `b7` (identidad triple de valores; 12 mutaciones **selladas de nuevo** —tasa sola, escala sola, kernel sin identidad, tiempo `tau`, posición, id, testigo elegido, estado, miembro faltante, no numérico, `LOW`, `HIGH`—; digesto falso, bytes ajenos, región y ratificación ajenas con un byte de diferencia, raíz ilegible; objeto forzado; sólo el id exacto pide el vínculo; sólo cambian las seis magnitudes; sesión abierta con el adaptador promovido o ninguna).

## 5 · P3-379 · Concesión `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2`
| Campo | Valor |
|---|---|
| Identidad | `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2`, versión 2, `ACTIVE_FOR_DEVELOPMENT_EXPERIMENT`, `PRESSURE_ONLY`, propósito `DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY` |
| Huella | `8a91145dbfe899dffdc5de1ed28b116c61f4fa5b462a49979727ce8b05b3642f` (fijada en el código) |
| Instantánea ligada | `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`; digesto de valores `7270cf8599de0095088601acfe1df4d88b2aa9e38483fbdaf6844a1c2cce65c5`; digesto de configuración `70e6826c…0641` |
| Linaje | el miembro certificado `PHASE2_AMENDMENT_2` (`a0af7d08…`); sin sucesor |
| Casos / dominio / entorno | `gi_bleed_57m`, `gi_bleed_72f`; `sbp`, `dbp`, `map`; sólo `development` |
| Semántica de parada, ventana y frontera de colapso | **las de la versión 1, sin cambio** |
| Excluidos | los de la versión 1 (consciencia y colapso como autoridad; terminalidad; otros dominios) |

- **La versión 1 no se tocó:** su cuerpo y su huella (`GRANT_FINGERPRINT`) son los mismos; sigue **registrada y legible**. Cada concesión se juzga contra **su** instantánea (`grant_problems`, `grant_for_snapshot`): una instantánea pertenece a **una** versión, y un emparejamiento cruzado se rechaza.
- **La compuerta** (diez condiciones) concede la instantánea promovida sólo con su concesión V2; sin ella (o con otro entorno, otro caso, otro dominio) no concede.
- **Probado:** `g1` a `g5` (identidad y huella; V1 intacta; cruce V1/V2 rechazado; registro completo y acotado; compuerta con y sin concesión) y `test_phase3_pressure_grant.py` (45).

## 6 · P3-381 · Repetición y artefactos
- Toda corrida nueva con la instantánea promovida **se identifica como V2**: el artefacto, cada minuto y el resumen de concesión nombran `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2` y su huella; la versión de parámetros que reporta la capa de sombra es `gi_joint_pressure_development_snapshot_v1`.
- Las verificaciones y repeticiones **resuelven la concesión que el artefacto nombra** (`registered_grant`), de modo que un artefacto V1 se verifica y se repite bajo V1 y uno V2 bajo V2. **Ningún artefacto ni registro anterior se reescribió** (cero cambios bajo `docs/revision` salvo los registros nuevos de este ciclo; ver §9).
- **Endurecimiento hallado al probarlo y ampliado por la revisión (reproducido y reparado):** (1) un artefacto con la concesión V2 pero con el `snapshot_id` de nivel superior cambiado al id anterior —y vuelto a sellar— **seguía verificando como completo**; ahora toda identidad de instantánea que el artefacto declara (nivel superior, mapeo `snapshot` y cada minuto) debe ser la que **liga la concesión que nombra**. (2) La revisión mostró que **eso sólo comprobaba etiquetas**: un artefacto V1 renombrado de forma coherente como V2 (y al revés) y vuelto a sellar verificaba y se repetía. Reproducido con una sonda propia y reparado: `real_artifact_problems` exige ahora que **cada escenario capturado** (el del artefacto y el de cada minuto) lleve **los seis valores** de la instantánea que liga la concesión nombrada (`snapshot_values`, `scenario_has_the_values`; el punto anterior se fija con `OLDER_POINT`, que una prueba re-deriva del adaptador anterior), y la repetición del superpuesto decide «promovido» por esa concesión y no por lo que el artefacto dice de sí mismo. (3) La **procedencia dentro de la corrida** (`versions.parameter_snapshot` del artefacto y de cada minuto) decía `phase2_committed_default_profile` aunque los valores eran los promovidos: ahora nombra la instantánea promovida. No cambia ningún artefacto legítimo del punto anterior.
- **Probado:** `r1` (cuatro artefactos promovidos: verifican, se repiten desde sí mismos y cubren todo minuto comprometido), `r2` (un artefacto V1 de la página real sigue verificando y repitiéndose bajo V1 y la verificación no lo escribe), `r3` (V2 presentado como V1, V2 con id anterior y huella ajena: no verifican), `r4` (los registros ratificados son exactamente los bytes fijados).

## 7 · P3-382 · Igualdad con las trayectorias `CENTER_REFERENCE` por la autoridad real (criterio principal)
Se jugó cada encuentro revisado por la docencia (FR-B, FR-C, FR-E, FR-G) por la **página real** (`AppTest`), con la configuración autorizada de desarrollo bajo V2, y se leyó la presión **mostrada** (mmHg enteros; MAP derivada) en cada minuto comprometido, contra el `CENTER_REFERENCE` de `docs/revision/PHASE3_GI_JOINT_REGION_V1.json`. **No** se comparó con la autoridad anterior.

| Escenario | Caso | Minutos comprometidos | SBP/DBP/MAP mostrada = `CENTER_REFERENCE` |
|---|---|---|---|
| FR-B | `gi_bleed_57m` | 5, 10, 30 | 89/54/66 · 91/56/68 · 92/57/69 |
| FR-C | `gi_bleed_57m` | 60, 120, 125, 130, 150 | 71/43/52 · 54/33/40 · 56/34/41 · 59/36/44 · 64/39/47 |
| FR-E | `gi_bleed_72f` | 60, 120, 125, 130, 160 | 79/50/60 · 60/38/45 · 62/39/47 · 66/42/50 · 72/46/55 |
| FR-G | `gi_bleed_72f` | 60, 70 | 85/54/64 · 81/51/61 |

**Igualdad exacta en los 15 minutos comprometidos de los cuatro escenarios** (SBP, DBP y MAP); ninguno se detuvo; la parada esperada de cada candidato coincide. Probado: `test_phase3_pressure_promotion.py::test_e1…` (4) y `e2` (ningún rastro del id anterior en un artefacto promovido).

## 8 · P3-383 · No regresión
- **FR-A y FR-D (deterioro sin tratar):** bajo V2 siguen deteniéndose en la frontera de colapso con los **mismos minutos comprometidos** (60, 120, 180), último compromiso 180 y primer rechazo 240, para los dos casos. **El colapso se establece antes** (minuto 183 bajo V2 frente a 207 bajo V1): es la consecuencia esperada de la hemorragia más rápida de la instantánea ratificada; la cuadrícula de compromisos oculta la diferencia. No es una regresión: la semántica de la frontera no cambió.
- **FR-F (norepinefrina no soportada):** sigue siendo **parada correcta** (`HALTED_BY_UNSUPPORTED_ACTION`), sin implementarse nada.
- **Parada efectiva, reapertura, aborto previo al compromiso, filtración de texto:** las pruebas de la página de parada se **repiten bajo V2** sin copiarlas (`test_phase3_pressure_promotion_stop.py`: **42** pasan, incluida `m0` que prueba que el módulo corre la configuración promovida), incluyendo reapertura con las banderas puestas o quitadas, sitio perdido, quitar la configuración a mitad del encuentro y fallo tras el primer compromiso.
- **Entorno docente de revisión (un solo proceso):** exige la instantánea V2 y la concesión V2 en las sesiones **nuevas**; las siete corridas guionadas llegan a su desenlace certificado y los aislamientos de residente y de puntuación se mantienen (`test_phase3_faculty_review_page.py`: **31** pasan).
- **Aislamiento y alcance:** `COMMON_CORE_RUNTIME_AUTHORITY` sigue `False`; sin autoridad de consciencia ni terminal; la superposición V1 sigue sólo como comparación y no escribe `mental_status`; nada nuevo visible para el residente; la puntuación no se toca.

## 9 · Adaptaciones declaradas y registros históricos
- **Ningún registro histórico se regeneró ni se editó.** Varios registros derivados del código (`PHASE3_PRESSURE_CHECKPOINT`, `…EFFECTIVE_STOP…`, `…TURN…`, `…DORMANT_SITE…`, `…PRESSURE_AUTHORITY_SERIES`, `…DORMANT_PAIR_AUTHORITY`, `…FACULTY_REVIEW_CHECKPOINT`) están **encadenados por huella** (el del P3-300, inmutable y fijado por cuatro pruebas, embebe las huellas del punto de control de turno y de la serie), así que regenerarlos habría roto la cadena que prueba que la historia no se reescribió. Su única diferencia con lo que el código produce hoy es **una**: la lista de aprobaciones registradas ahora incluye la instantánea promovida. `test_phase3_promotion_record_delta.py` acepta **exactamente** ese delta y rechaza todo otro (con controles de mutación); cada prueba afectada lo usa y sigue fijando byte a byte todo lo demás. Un registro almacenado debe seguir sellado por su propio digesto.
- **Pruebas obsoletas que halló la revisión (mi barrida no las cubría):** `test_shadow_core_isolation.py` (error de colección: el conjunto exacto de la capa de sombra no incluía el módulo de vínculo), `test_faculty_review_layer.py` (su entorno nombraba la instantánea anterior, que el entorno de revisión ya rechaza), `test_gi_pressure_calibration_preview.py` y `test_shadow_observability.py` (lista de aprobaciones). Mismas reglas: conjunto exacto, nada más; todas pasan.
- **Aserciones «exactamente una aprobación/una concesión»** ahora dicen «exactamente estas dos» (aprobaciones) o «exactamente estas dos concesiones»: siguen siendo igualdades exactas.
- **Conjunto de módulos que nombran los registros ratificados (`t9`):** pasa a un conjunto **declarado exacto** por símbolo; la limitación monitoreada sólo la nombran dos módulos y sólo como texto declarado, y ningún ejecutable nombra el cierre ni el registro humano.
- **`LAYER_SOURCES`** incluye el módulo de vínculo (así lo cubre el digesto de la capa) y las dos pruebas que lo fijan por nombre lo declaran.
- **Estado de la nota «no vinculada a la autoridad viva»:** el registro de la instantánea y el de su ratificación dicen, **tal como se decidió el 2026-11-16**, que la instantánea **no** estaba vinculada a la autoridad viva y que nada ejecutable cambió. Siguen diciéndolo (son históricos y están fijados por huella). **Desde este ciclo la afirmación vigente es otra**: la autoridad viva de desarrollo **sí** ejecuta esa instantánea. `docs/PHASE3_GI_JOINT_REGION_RATIFICATION.md` y `CLAUDE.md` llevan una nota fechada.
- **Instrucciones de lanzamiento del operador:** el entorno de revisión exige ahora `MRS_PHASE3_AUTHORITY_SNAPSHOT=GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`; el kit del operador, `PHASE3_FACULTY_REVIEW_ENVIRONMENT.md` y `PHASE3_FACULTY_REREVIEW_INTERACTIVE.md` llevan una nota fechada (el valor anterior sigue documentado como histórico).

## 10 · Revisión adversarial independiente (una)
Una revisión independiente, de sólo lectura, sobre el árbol sin commit, con la lista de ataque del encargo. **Sin hallazgo ALTO; no rompió ninguna invariante dura** (`clinical_core/`, `COMMON_CORE_RUNTIME_AUTHORITY`, alcance, sin retroceso al punto anterior, `LOW`/`HIGH`, limitación monitoreada, Enmienda 3, aislamiento del residente y de la puntuación). Sus 9 puntos, cada uno **confirmado por mí con una sonda o lectura propia antes de actuar**:

| # | Severidad | Hallazgo | Confirmación propia | Resolución |
|---|---|---|---|---|
| 1 | MEDIA | La verificación de artefactos ligaba etiquetas de la instantánea a la concesión, no los **valores** de la corrida | reproducido: un artefacto V1 renombrado como V2 y resellado verificaba | valores por escenario capturado + repetición del superpuesto por la concesión; `r5`, `r6`, `r7`; mutantes 2, 3, 5 y 8 muertos |
| 2 | MEDIA | Pruebas obsoletas: error de **colección** en `test_shadow_core_isolation.py` y fallos en `test_faculty_review_layer.py` y dos más | reproducido (mi barrida sólo cubría `test_phase3_*` y `test_runtime_*`) | cuatro archivos adaptados (200 pasan); ver §9 |
| 3 | MEDIA | La única protección contra mezclar sesión y sitio era incidental (dentro de la superposición) | confirmado por lectura: nada fijaba una comprobación explícita | `PRESSURE_CONFIGURATION_MISMATCH` explícita antes del candidato; `m1`; mutante 1 muerto |
| 4 | BAJA | Procedencia dentro de la corrida con la etiqueta del perfil por omisión | reproducido | etiqueta corregida; `e2`; mutante 6 muerto |
| 5 | BAJA | «Entorno de revisión sólo V2» sin prueba; este documento nombraba mal la condición que rechaza V1 | confirmado por lectura y por el mutante 4 | `test_f2b`; la condición es `snapshot` (corregido); mutante 4 muerto |
| 6 | BAJA | Los digestos fijados por la concesión nunca se comparaban en ejecución con el vínculo | confirmado por lectura | comparación en la compuerta y en `open_site`; `m2`; mutante 7 muerto |
| 7 | BAJA | Un fallo de vínculo no se distinguía en el registro de autoridad | confirmado por lectura | el motivo nombra `PressureSnapshotNotBound`; `m3` |
| 8 | BAJA | Debilitamientos de pruebas: `b4` pasó a pertenencia; `s11` sin espejo | confirmado | `b4` vuelve a exacta; `s11` espejada |
| 9 | INFO | Literales duplicados sin igualdad; el evaluador en seco aún vincula el punto anterior; sin `.gitattributes` para los JSON fijados; una sesión de sombra corre la configuración promovida si el entorno la nombra aunque la bandera de autoridad esté apagada | confirmado | `m4` fija las igualdades; el resto queda **declarado** en §12 |

Un intento de resolver el 6 dentro del módulo de la concesión rompió `test_g12` (que existe para que ese módulo no importe nada del repositorio); la comparación se movió a la compuerta. Hallazgos **no** reproducidos por mí: el recuento exacto de mutantes sobrevivientes que informó el revisor (lo que sí hice fue matar con pruebas nuevas los ocho mutantes que importan).

## 11 · Certificación
Una sola certificación sobre un candidato congelado: la suite completa del repositorio por particiones (`suite_particionada.py`) y `run_regressions.py`, con **una** huella del árbol (HEAD + diferencia + archivos nuevos). **Las cifras y la huella no se escriben aquí** (un documento no puede contener la huella del árbol que lo incluye): están en el informe del ciclo y en los mensajes de los commits. `clinical_core/` no cambió (diferencia vacía), así que su certificación vigente sigue sobre código equivalente.

## 12 · Límites declarados y decisiones pendientes
1. **La versión 1 sigue registrada y ejecutable** (para repetir artefactos anteriores y para las suites de maquinaria que la usan); sólo el **entorno docente de revisión** exige V2 para sesiones nuevas. **Decisión pendiente (docente):** si la autoridad viva debe **retirar la V1 de la activación**, de modo que ninguna configuración nueva pueda arrancarla. No se hizo sin esa decisión.
2. **No es validación clínica** ni calibración clínica ni autoridad de producción ni despliegue a residentes. La limitación monitoreada `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` (la respuesta de presión a la reanimación con sangre queda en el extremo bajo de lo plausible) **sigue vigente** y sigue monitoreada; la promoción no la tocó.
3. **Sin firma de registros y un solo proceso** (límites heredados del entorno de revisión; no cambian).
4. **Siguiente prioridad (sin implementar):** la vía común de tono vascular / vasopresor (`FD-REVIEW-06`).
5. **Cosas que la revisión dejó como límites declarados:** (a) el evaluador en seco del par (`MRS_PHASE3_PAIR_DRY_RUN`) sigue vinculando el punto anterior aunque el entorno nombre V2; está dormido, sin autoridad y fuera del entorno de revisión. (b) No hay `.gitattributes` que fije LF en los JSON fijados por huella: un *checkout* con CRLF haría que el vínculo **se niegue** (falla cerrado). (c) Una sesión de sombra corre la configuración promovida siempre que el entorno nombra V2, aunque la bandera de autoridad esté apagada (no autoritativa).
6. **Los registros humanos de la re-revisión** siguen `REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE` (`TD-152`): la promoción descansa en la ratificación **tal como se registró**.

## 13 · Confirmaciones
Sin calibración nueva · sin fisiología de Enmienda 3 · sin norepinefrina · sin control de fuente · sin autoridad de consciencia · sin autoridad terminal · sin despliegue a residentes · sin afirmación de validación clínica · `clinical_core/` sin cambios · `COMMON_CORE_RUNTIME_AUTHORITY = False` · puntuación, piloto y pantalla del residente sin cambios.
