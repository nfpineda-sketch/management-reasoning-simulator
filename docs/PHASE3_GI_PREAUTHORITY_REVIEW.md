# Fase 3 · GI: ratificación de la instantánea y revisión docente y de arquitectura previa a la autoridad (P3-199 a P3-209) · registro (2026-11-11)

**Alcance.** Determinar si el par **presión + consciencia** de GI está listo para un experimento de autoridad de desarrollo. **No se habilita autoridad**
(FD-AUTH-03): `COMMON_CORE_RUNTIME_AUTHORITY = False`, el registro de instantáneas aprobadas para autoridad conserva **sólo** `gi_pressure_committed`, la
transacción del par se construyó **en seco** y nunca llama a `commit`, ningún valor del núcleo común se escribe en un encuentro, el estado visible al
residente sigue siendo el heredado (FD-AUTH-08), la puntuación y el primer piloto no cambian, no se inventa ninguna regla terminal y **no hay afirmación de
validación clínica**. No cambió ningún byte de `clinical_core/`, de la capa, del motor heredado ni de la aplicación.

| Punto | Resultado |
|---|---|
| P3-201 lectores | **`CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS`** |
| P3-202 presión | **`GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE`** |
| P3-208 revisión adversarial | independiente y de sólo lectura: **18 entradas** · 5 bloqueados · **11 hallazgos corregidos** · 1 declarado · 1 no comprobable (§9) |
| P3-209 punto de control | **B · `PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY`** (definitivo; con dos límites nuevos que también atan a la presión: C9 y C10) |

Registros: `docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json`, `docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json`,
`docs/revision/PHASE3_GI_PAIR_DRY_RUN.json`. Pruebas: `test_phase3_gi_preauthority_review.py`. Arneses (del lado de las pruebas):
`test_gi_snapshot_binding.py`, `test_gi_pair_dry_run.py`, `test_gi_preauthority_review.py`, `test_gi_preauthority_record.py`.

## 0 · Decisiones de la docencia que abren el ciclo (2026-11-11)
| Decisión | Contenido |
|---|---|
| FD-AUTH-01 | Se **ratifica** `GI_DEVELOPMENT_SNAPSHOT_V1` para **experimentos de desarrollo** (`RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS`). No es calibración clínica, ni perfil de producción, ni perfil de residentes, ni instantánea aprobada para autoridad. Se conservan LOW · V1 · HIGH como testigos de sensibilidad; la región no se reemplaza. |
| FD-AUTH-02 | Por qué se acepta: cumple H1–H7, es interior a toda región, maximiza el margen mínimo, la regla no usó ninguna salida del heredado, `CENTER_REFERENCE` no se eligió por defecto (y de hecho incumple un criterio de cota), el orden causal es estable en los dos casos y la recuperación cumple FD-P3-176. La selección **no se reabre** salvo una contradicción estructural nueva. |
| FD-AUTH-03 | Sin autoridad todavía. |
| FD-AUTH-04 | La consciencia es el asunto principal de revisión: los 461 minutos se revisan explícitamente. Diferir del heredado **no** es fallar. |
| FD-AUTH-05 | Auditar **todos** los lectores de `mental_status` antes de cualquier autoridad de consciencia; no suponer que son sólo de presentación. |
| FD-AUTH-06 | Un experimento futuro **no continúa** la autoridad más allá del colapso circulatorio establecido del núcleo común: es una frontera de seguridad del experimento, **no** una regla de muerte, ni un umbral clínico terminal, ni un desenlace visible al residente. |
| FD-AUTH-07 | La ventana termina en `min(límite de tiempo, primera frontera de colapso establecido)`. |
| FD-AUTH-08 | En todo este ciclo, lo que ve el residente es el heredado. |

## 1 · P3-199 · Registro de ratificación
`GI_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json` (huella `123135b3…8f64`, fijada por prueba; se reconstruye idéntica desde la versión 1). **La versión 1 no se
editó** (su SHA-256 `d9de4800…4803` sigue fijado): la ratificación es un registro **aparte** que la nombra por identificador, versión, SHA-256 del archivo,
huella de identidad (`1f292d01…ec40`) y huella del registro (`9e258ab5…cdc9`). Contiene los diez valores, el digesto de la Enmienda 2 (`a0af7d08…6ce2`), los
criterios de selección, los márgenes a las cotas (0,5 en las diez magnitudes), los testigos LOW y HIGH (los del núcleo, sin cambio), las decisiones docentes,
la incertidumbre y los falsadores. **No se añadió a ningún registro de instantáneas aprobadas para autoridad.**

## 2 · P3-200 · Revisión de la divergencia de consciencia
Los **461** minutos `POTENTIAL_EDUCATIONAL_PROBLEM` del contrafactual son **15 episodios contiguos** (14 corridas requeridas). **No se modificó fisiología.**

### 2.1 Dirección (P3-200B)
| Dirección | Episodios | Minutos comparados | Dónde |
|---|---|---|---|
| `LEGACY_MORE_IMPAIRED` | 5 | 196 | **sólo** en el caso de 57 años, y sólo antes del inicio propio de la instantánea (63–108; con líquido, 109–120) |
| `COMMON_MORE_IMPAIRED` | 8 | 263 | el caso de 72 años en **todos** sus episodios; el de 57 desde el minuto 158 |
| `TRANSIENT` | 2 | 2 | el minuto 158, en el que se ordena la recuperación |
| `CROSSING` | 0 | 0 | — |

**Los dos casos divergen en sentidos opuestos al inicio, y está explicado** (`ABSOLUTE_PAS_LEGACY_THRESHOLD_VERSUS_RELATIVE_TO_ARRIVAL_SEMANTICS`, probado):

| | 57 años | 72 años |
|---|---|---|
| PAS heredada de llegada | 88 | 98 |
| El heredado dice «Drowsy» por primera vez | minuto **63** (PAS 80 → **79**) | minuto **138** (PAS 80 → **79**) |
| La instantánea dice SOMNOLIENTO por primera vez | minuto **109** | minuto **109** |
| Entrega relativa en ese minuto | 0,679989 | 0,679989 |

El heredado usa un umbral **absoluto** (`_PRESSURE_LEVELS`: somnoliento bajo 80 mmHg, obnubilado bajo 65; **nunca** «Unresponsive» por presión): quien llega más
bajo lo cruza antes. El núcleo común lee la entrega **relativa a la llegada de cada paciente** (FD-GI-01): los dos lo cruzan en el mismo minuto. No hay un tercer factor.

### 2.2 Coherencia causal (P3-200C)
Los **15 episodios** son `MECHANISTICALLY_COHERENT_DIFFERENCE`; **0** `STRUCTURAL_CONTRADICTION`. En cada uno se comprobó, minuto a minuto: (1) la categoría mostrada es la
del compuesto que sostiene el mecanismo (F, o colapso establecido); (2) F se mueve **hacia** su objetivo y nunca en contra; (3) la entrega relativa no sube antes de ninguna orden.
La comprobación **puede fallar**: una categoría falsa, una F que se aleja de su objetivo y una entrega que sube sin tratar se detectan cada una (prueba). El heredado
**no** se tomó por correcto en ningún punto.

**Fuera de los episodios también** (corrección de P3-208): las mismas tres comprobaciones se corren sobre **cada** minuto comparado de las 14 corridas (**1930 minutos**), no sólo dentro de las
ventanas de divergencia: **0** violaciones. La revisión plantó una contradicción en un minuto donde las dos palabras coinciden y ningún episodio la vio; ahora se ve (prueba).

### 2.3 P3-200D · Tabla para la docencia (nueve episodios representativos, de mayor a menor impacto)
Para **cada** fila la docencia responde: **(a)** ¿sería defendible mostrar este estado a un residente? **(b)** ¿la alteración llega demasiado pronto o tarde?
**(c)** ¿la recuperación llega demasiado pronto o tarde? **(d)** ¿la categoría comunica bien la gravedad fisiológica? **No las respondo: es juicio clínico-docente.**

| # | Caso · escenario | Minutos | Heredado muestra | La instantánea mostraría | Mecanismo al inicio → al final (entrega rel. · F · carga de colapso) | PAS heredada / común |
|---|---|---|---|---|---|---|
| 1 | 72 a · sin tratar | 158–240 (83) | Drowsy | **Unresponsive** | 0,54 → 0,31 · 0,81 → 1,00 · 0,00 → 1,00 | 77 → 66 / 54 → 32 |
| 2 | 72 a · sólo cristaloide en el 131 | 194–240 (47) | Drowsy | **Unresponsive** | 0,54 → 0,40 · 0,81 → 1,00 · 0,00 → 0,58 | 75 → 68 / 55 → 42 |
| 3 | 72 a · antes de tratar | 109–168 (41) | **Alert** | Drowsy → Obtunded | 0,68 → 0,63 · 0,25 → 0,43 · 0 | 83 → 80 / 67 → 65 |
| 4 | 57 a · antes de tratar | 63–108 (46) | **Drowsy** | Alert | 0,81 → 0,68 · 0,00 → 0,24 · 0 | 79 → 73 / 72 → 61 |
| 5 | 57 a · sin tratar | 158–174 (17) | Drowsy | **Unresponsive** | 0,54 → 0,50 · 0,81 → 0,99 · 0,00 → 0,17 | 67 → 65 / 49 → 45 |
| 6 | 57 a · sólo líquido (2 L) | 109–120 (12) | **Drowsy** | Alert | 0,81 → 0,78 · 0 · 0 | 79 → 78 / 74 → 71 |
| 7 | 72 a · tratamiento tardío | 109–120 (12) | **Alert** | Drowsy | 0,68 → 0,65 · 0,25 → 0,38 · 0 | 83 → 82 / 67 → 64 |
| 8 | 57 a · sólo cristaloide en el 131 | 194–198 (5) | Drowsy | **Unresponsive** | 0,54 → 0,53 · 0,81 → 0,86 · 0 | 65 → 65 / 50 → 49 |
| 9 | 57 a · minuto de la orden de recuperación | 158 (1) | Drowsy | **Unresponsive** | 0,54 · 0,81 · 0 | 67 / 49 |

Lo que la tabla pone delante de la docencia, sin decidirlo:
* **Filas 1, 2, 5, 8 y 9 (dos bandas):** la instantánea llega a SIN RESPUESTA con pulso; el heredado **no puede** pasar de «Obtunded» por presión. En la fila 1, además, 34 de los 83 minutos
  (207–240) quedan **después** de la frontera de colapso establecido: bajo FD-AUTH-06 un experimento **no los alcanzaría**.
* **Filas 3 y 7:** el paciente de 72 años se altera en la instantánea con PAS heredada 83 (por encima del umbral heredado) porque ya perdió un tercio de **su** entrega de llegada.
* **Filas 4 y 6:** el paciente de 57 años sigue Alerta en la instantánea con PAS heredada 79 y PAS **común 72–61**: presión baja con consciencia conservada mientras la entrega relativa supera 0,75.
* **La palabra:** el heredado escribe «Unresponsive» **sólo** en el paro. Que la misma palabra valga con pulso es una decisión docente (bloqueo C5).

## 3 · P3-201 · Auditoría de lectores de `mental_status`
**Método.** Recorrido por **AST** de todos los módulos de ejecución (no se abren pruebas, regresiones, herramientas ni el corpus de validación). Se distingue la **mención** de la
**lectura ejecutable**, y la lectura del **observable vivo** de la lectura de la **llegada autorada**. El inventario queda fijado: una prueba vuelve a recorrer el AST y falla si aparece un sitio sin clasificar.

**Límite del método (declarado tras P3-208).** El recorrido encuentra la clave **literal**. No ve: una clave guardada en una variable o construida en ejecución; un bucle sobre todo el observable
(`.items()`, `**`, comparar el observable entero); un `getattr` o un ayudante que recibe la clave (lo encuentra, pero sin contarlo como lectura); ni el consumidor de un valor **derivado** de la palabra.
Por eso la **clase** puesta a mano decide si un sitio es lector, los consumidores indirectos se listan a mano y se verifican por su importación, y **el inventario no es una prueba de que ningún otro código lea la palabra**.

| | |
|---|---|
| Módulos con un uso sintáctico | **54** (más 7 que sólo lo nombran en texto) |
| Sitios (módulo · función) clasificados | **119**, 0 sin clasificar |
| **Lectores ejecutables del observable vivo en un encuentro GI** | **32** |

### 3.1 Los 32 lectores vivos, por clase
| Clase | N | Lectores | Consecuencia |
|---|---|---|---|
| A · sólo pantalla | 3 | `app._vitals_cells`; vista y reporte de la traza | muestran la palabra |
| B · generación de texto | 10 | `family_engine.current_findings`, `clinical_update`; `app.format_clinical_update`, `_trace_*`; `cognitive_review`; `patient_appearance`; `image_broker.edit_prompt` | texto de examen, de actualización clínica y de la traza; **el prompt de una edición de imagen** (puede ser una llamada pagada) |
| C · ramificación clínica | 8 | `app.observable_state_changed`; `_expected_response_prompt`, `_critical_adaptation_prompt`, `_reasoning_data_alignment_prompt`; `_trajectory_expert_model`; `image_consistency`; `visual_observations` (función y tabla del módulo) | añade o no una tarjeta de actualización; **elige** las preguntas de reflexión adaptativa; contrato visual del paciente |
| **D · puntuación (indirecta)** | 3 | `management_trace_analysis`, `faculty_analysis`; **`record_findings`** (y sus consumidores `faculty_portal`, `faculty_report`, `management_trace_report`) | la palabra de **cada** estado de la traza entra en el **payload del análisis de IA y docente**; y decide si el portal docente **retiene** una sugerencia de IA (ver §3.3) |
| **E · terminación** | 1 | `family_engine._discharge_alarm` | tras un alta, un paciente no despierto «es hallado … en casa» y vuelve |
| **F · elegibilidad de órdenes y acciones** | 3 | `family_engine._validate` (dextrosa y carbohidrato orales), `_order` (antipirético oral), `app._clinical_encounter_workspace` | órdenes rechazadas o retenidas; **la anamnesis deja de estar disponible** con «obtunded» o «unresponsive» |
| G · persistencia | 3 | `app.learner_vitals_snapshot`, `management_state_snapshot`; `trace_phase0` | la palabra queda en eventos, traza e intento |
| H · código muerto | 1 | `app._perfusion_response_direction` | sin llamador |

### 3.2 Lo que **no** lee la palabra viva (verificado)
* **La fisiología del motor heredado.** `_surface` **reescribe** `mental_status` desde su propia escalera; sus lecturas son de la **línea base autorada**. La afirmación ya no es una constante
  del registro: se **deriva** del código (por AST, las cuatro lecturas de la clave en `_surface` tienen a `base` por receptor; una superficie sintética que lee el observable vivo la vuelve falsa) y de una
  **sonda diferencial en vivo**: doce turnos soportados en los dos casos, con la palabra forzada antes de cada turno («Unresponsive», «Obtunded», «Drowsy»): **0** diferencias en signos, estado de familia y libro
  de órdenes. **Precisión que la revisión encontró:** la palabra escrita se sobrescribe en el siguiente turno que **avanza el reloj**; en un turno de **cero minutos** (una interconsulta) **persiste** en el
  estado, en la entrada y en su instantánea de observación. Dentro del motor, sólo cinco funciones leen el observable vivo.
* **El resto de módulos** (88 sitios): otra familia del motor, el motor de casos generados (no integrado), autoría, catálogos, registros y los módulos de migración de `clinical_core/`.
* **Otros campos de consciencia visibles al residente:** no existen; `learner_vitals_snapshot` expone sólo `mental_status` (no hay GCS ni AVPU autorados).

### 3.3 P3-201A/B · Efectos aguas abajo y veredicto
La autoridad sobre la consciencia **podría alterar indirectamente**: el flujo del escenario (9 lectores), la puntuación (3 lectores y 3 consumidores, indirecta), las acciones disponibles (3), la terminación (1) y el texto visible al residente (13).

**`CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS`.** Superficies exactas y guardas:

| Superficie | Guarda requerida | ¿Existe? |
|---|---|---|
| Elegibilidad de órdenes en el motor (dextrosa, carbohidrato y antipirético orales) y desenlace del alta | esas clases están **fuera** de `SUPPORTED_ACTIONS`: el turno detiene el experimento. A declarar: en el turno que detiene, la orden ya se decidió con la palabra escrita | **sí** |
| Disponibilidad de la anamnesis en la página | **nueva:** correr el experimento sólo por el arnés guionado (sin página), o aceptación docente explícita | no |
| Texto y pantalla visibles (examen, actualización, tarjetas, signos, descripción visual) | **nueva:** superficie sólo de desarrollo; es el efecto **buscado** de una autoridad, así que es una decisión de exposición, no un defecto | no |
| Contrato y prompt de imagen | **nueva:** generación de imágenes apagada en el entorno del experimento | no |
| Instantáneas de la traza y de los eventos | **nueva:** el encuentro de un experimento se marca y queda fuera de los registros de residentes | no |
| Payloads del análisis de IA y docente | **nueva:** sin análisis de IA ni rúbrica sobre un encuentro de experimento, o etiqueta obligatoria; la puntuación sigue siendo heredada | no |
| **Retención de una sugerencia de IA en la superficie de evaluación docente** (`record_findings.inert_observables` → portal y reportes) | **nueva (hallazgo de P3-208):** la misma regla, o calcular la retención con la palabra heredada. Con la palabra heredada **constante** el portal muestra «Requires faculty review»; con una palabra que **se mueve**, la misma sugerencia se muestra como propuesta | no |
| Preguntas de reflexión y comparación con experto | **nueva:** no se muestran para un encuentro de experimento, o se declaran | no |
| Comparación propia de la sombra (`legacy_adapter.snapshot`) | **nueva en el par:** capturar la palabra heredada **antes** del compromiso, como ya se hace con las presiones | no |

## 4 · P3-202 · Recertificación de la autoridad de presión en el núcleo activo
**Arnés existente, sin tocar:** `test_runtime_authority_series._play_the_battery_with_authority`, los dos casos, la batería de aceptación completa, la misma instantánea
`gi_pressure_committed`, el mismo dominio, la misma política de fallo. Se corrió **dos veces**: sobre el árbol del commit `e0c9ae5` (núcleo de **cierre**, la última serie antes de integrar la
primera enmienda) y sobre la cabeza actual (núcleo activo `PHASE2_AMENDMENT_2`). La autoridad no se habilitó globalmente: las banderas viven sólo dentro del arnés.

| | Núcleo de cierre | Núcleo activo |
|---|---|---|
| Escenarios · completados · detenidos | 34 · 26 · 8 | 34 · 26 · 8 |
| Minutos comprometidos | 66 | 66 |
| Huellas verificadas · replay cubre cada minuto · trayectoria mixta declarada al detener tras un compromiso | sí · sí · sí | sí · sí · sí |

**P3-202A · Comparación campo a campo** (34 escenarios, 78 registros de minuto): **idénticos** el candidato común, las presiones comunes, lo escrito, el contrafactual heredado, las
huellas del candidato, del replay, de lo escrito y del estado, el resultado, los motivos de detención y el linaje de acciones. **Difieren sólo 15 campos, todos explicados:** identidad del
intento, nombre y digesto del miembro del linaje, digesto de la guarda de cierre y de la capa, los **dos campos de perfil nuevos** (`amendment_2` y la fracción de transmisión de la Enmienda 1,
**ambos `None`**: apagados en el perfil comprometido) y las huellas que los incluyen. **0 diferencias sin explicar, 0 fallos de coincidencia obligatoria. Sin reajuste.**

**Veredicto: `GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE`.** Además, las **253** pruebas de los diez archivos `test_runtime_authority*.py` pasan en el núcleo activo. Una prueba nueva
vuelve a correr la serie del caso de 57 años y la compara, minuto a minuto, con la huella del núcleo de cierre guardada en el registro.

*Corrección de mi registro anterior:* dije que la nota de procedencia de P3-51 seguía abierta sin re-auditar. **Está cerrada desde P3-55** (linaje canónico; `test_s7`), y la serie de hoy lo confirma.

## 5 · P3-203 · Diseño del par (sólo diseño; nada se compromete)
| Dominio | Qué se escribiría | Fuente |
|---|---|---|
| **Presión** | `sbp`, `dbp`; `map` derivada por la pantalla | el punto de presión de la corrida ligada, con la forma de la pantalla heredada |
| **Consciencia** | `mental_status` = la palabra heredada de la categoría común (0 Alert · 1 Drowsy · 2 Obtunded · 3 Unresponsive) | el compuesto de la Enmienda 2 bajo V1, leído de la **misma** corrida que las presiones |
| Colapso | **nada** (se registra y se compara) | — |
| Terminal | **nada** (no hay regla y no se inventa) | — |

**P3-203A · Atomicidad.** El par se valida como **una** transacción (18 comprobaciones; si una falla, **nada** se escribiría); los cuatro campos saldrían de **un** mapeo preparado; las dos mitades
deben ser **el mismo curso físico** (parten de las mismas anclas de llegada y toda lectura que no depende de las diez magnitudes es igual en las dos corridas en **cada** minuto del turno); tras el primer
rechazo el experimento queda detenido. Tras P3-208: una transacción que **lanza** es un rechazo con registro y detención (nunca una vuelta silenciosa al heredado, y nunca una excepción dentro del turno
heredado); y un turno que la transacción **no vio**, o que llega por una ruta **sin sitio de autoridad**, es un rechazo.
**¿Lo garantiza la arquitectura?** **Sí en la transacción en seco** (verificado en cada minuto de la serie y atacado: presión pasa y consciencia falla, y al revés). **Todavía no en la capa:**
`AUTHORITY_DOMAIN`, la propiedad y `commit` aceptan sólo presión numérica. No es motivo de `STOP`: la garantía existe en el diseño probado; lo que falta es construirlo dormido en la capa (bloqueo C3).

## 6 · P3-204 · Vínculo con la instantánea y construcción del perfil
**Hallazgo de la auditoría:** la capa construye los testigos **por nombre** (`systemic_consciousness.WITNESSES[nombre]`); «el testigo central» es lo que ese diccionario tenga al arrancar.

**Contrato (`bind`):** identificador, versión, SHA-256 del archivo, huella de identidad, huella del registro, huella del registro **entero** (con su bloque de inmutabilidad), huella de los diez valores,
huella del **perfil construido**, linaje del núcleo (el declarado, el vivo **y los bytes del núcleo**) y la ratificación **por su propia huella fijada**. El `CoreProfile` es el **perfil comprometido por omisión** (verificado como el punto que fija `gi_pressure_committed`) **más un campo**, `amendment_2`, construido **sólo** con los diez valores del
registro. No se lee ningún nombre de testigo ni `development_profile()`. Huella del perfil ligado: `c167b45e…cc89`. Cada minuto se vuelve a comprobar que la corrida en mano es la ligada.

**P3-204A · Controles de manipulación (15 variantes, todas rechazadas con su código):**

| Ataque | Código |
|---|---|
| identificador o versión equivocados | `WRONG_SNAPSHOT_ID`, `WRONG_VERSION` |
| un parámetro modificado (también **recalculando las huellas dentro del registro**) | `MODIFIED_PARAMETER` |
| huella equivocada, cuerpo editado, bytes distintos | `WRONG_DIGEST` |
| linaje equivocado (en el registro, en el núcleo vivo, en sus bytes, o no certificado) | `WRONG_CORE_LINEAGE` |
| instantánea parcial, parámetro de más, texto o booleano por número | `PARTIAL_SNAPSHOT` |
| **LOW, HIGH o CENTER_REFERENCE sustituidos por V1** | `WITNESS_SUBSTITUTED_FOR_THE_SNAPSHOT` |
| sin ratificar, ratificación «para autoridad», valores distintos en la ratificación | `NOT_RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS` |
| registrada como artefacto de autoridad | `NOT_A_DEVELOPMENT_SNAPSHOT_RECORD` |

**Endurecido tras P3-208 (cuatro vías que pasaban y ya no pasan, cada una con su prueba):**

| Vía que pasaba | Qué se hace ahora |
|---|---|
| un `BoundSnapshot` **hecho a mano** con los valores de LOW o HIGH y la identidad de V1 daba `WOULD_COMMIT` (la comprobación comparaba la corrida con el objeto ligado, no con lo fijado) | `bound_is_v1` re-deriva cada identidad y las huellas de los diez valores y del perfil **desde el objeto** y las compara con constantes fijadas; lo rechazan `PairDryRun`, el adaptador y `run`, y se repite cada minuto |
| un registro cuyos números **respondían una cosa al verificar y otra al construir** (subclase de `float` o de `dict`) quedaba ligado con otros valores | el registro se reduce a datos JSON planos **antes** de verificarlo, y el perfil construido debe dar la huella fijada: se verifica **lo construido**, no sólo lo ofrecido |
| el nivel de llegada de la corrida ligada, subido después de abrir, daba `WOULD_COMMIT` escribiendo «Drowsy», «Obtunded» o «Unresponsive» con el heredado en «Alert» | las anclas de llegada se fijan al abrir y se comparan cada minuto con las de la corrida de la sesión |
| una ratificación de nueve campos escritos a mano, o la real con las decisiones reescritas, se aceptaba; un registro con `superseded_by` puesto, también | la ratificación debe ser el registro commiteado **entero**; el registro de la instantánea se fija entero |

**Linaje:** se **lee** cada minuto (el veredicto de la capa y los bytes del núcleo). Un linaje que ofrece quien llama **sólo puede añadir** un rechazo; antes lo **sustituía**.

**Límite, dicho una vez:** son comprobaciones dentro de un proceso de Python. Rechazan un registro o un objeto equivocado, modificado, parcial o forjado; **no** pueden rechazar código que reescriba el
propio verificador en el mismo proceso. Eso lo resuelve la capa cuando el vínculo viva allí.

**Dónde vive:** del lado de las pruebas. La capa necesita esta regla dentro, certificada (bloqueo C4).

## 7 · P3-205 · Guarda de la frontera de colapso
**Regla.** Si la corrida ligada lee colapso **establecido** en **cualquier** minuto que una transacción cubriría, la transacción aborta y el experimento se detiene **antes** de comprometer ese minuto.

* **P3-205A · Qué significa:** *el experimento no es válido más allá de esta frontera fisiológica.* **No** significa que el paciente murió, **no** es un umbral clínico terminal, **no** es un desenlace
  visible al residente y **no** termina un encuentro. **No se asigna ningún texto terminal.**
* **P3-205B · Precompromiso: sí es posible.** El predicado de colapso es parte del candidato, así que se conoce durante `compute`, antes de que termine `validate`. No hace falta comprometer y detener después.
* **Cubre todos los minutos del turno:** una infusión avanza el reloj del motor dentro de **un** turno; la guarda revisa cada minuto desde el último despejado. Un colapso establecido en un minuto
  **intermedio** que ya cedió al final del turno **sigue siendo** un rechazo (prueba).
* **Falla cerrada:** un minuto que la corrida no puede mostrar no es un minuto despejado (prueba).
* **Colapso inminente:** no detiene; sólo el establecido es la frontera.
* **Tipo del estado (tras P3-208):** un estado que no sea exactamente uno de los tres del núcleo (un booleano, un decimal, un texto) es un minuto **no mostrado**.
* **Por diseño:** un minuto que un turno anterior ya despejó no se vuelve a leer (una corrida cuya historia cambia es su propio fallo).
* **Comprobado con fisiología real por la revisión:** 57 a sin tratar, un litro de cristaloide ordenado en el 206 hace **un** turno 206→226 en el que el colapso está establecido en 207–208 y ya cedió en el 226: `WOULD_ABORT`, primer minuto establecido 207.
* **FD-AUTH-07:** `fin de la ventana = min(240, primer minuto de colapso establecido)`; son dos comprobaciones de la misma transacción.

## 8 · P3-206 y P3-207 · Transacción en seco y serie de manejo
**Transacción (18 comprobaciones, en orden):** la transacción terminó sin lanzar → el estado del encuentro quedó intacto → el turno llegó por una ruta con sitio de autoridad → ningún turno pasó sin verse →
captura → cómputo con V1 exacta → linaje → instantánea → caso → acción soportada → un minuto, una transacción → candidato de presión presente →
**presión validada por la transacción existente** (`AuthorityTransaction.capture/compute/validate`, con sus diez comprobaciones) → candidato de consciencia presente → reproducible → el par es un solo curso →
frontera de colapso → ventana → la corrida común no falló → sólo se moverían los cuatro campos del par. Veredicto `WOULD_COMMIT` o `WOULD_ABORT`; después del primer rechazo, `EXPERIMENT_HALTED`.
Además, la regla de liquidación del sitio real (una clase no soportada que sólo aparece en el libro liquidado) se aplica tras cada orden.
**Por cada minuto** el registro guarda el estado heredado autoritativo, el candidato común, el veredicto y el motivo.

**No interferencia (probada en vivo):** la transacción trabaja sobre una **copia** del estado, así que lo que se le entrega no puede alcanzar el encuentro; el estado se resume antes y después (una
diferencia es un error del arnés: queda **registrada**, rechaza el turno y `run` la lanza **después** de terminar el encuentro, nunca dentro del turno heredado); la trayectoria heredada es
**idéntica**, minuto a minuto, a la del mismo guion con la sombra apagada y sin arnés; los parches se restauran también si el bloque lanza; dos corridas dan la misma huella. La serie de 20 encuentros se
**volvió a correr** con el arnés endurecido: las filas son idénticas a las de antes en todas sus columnas.

### 8.1 Matriz de dos casos (idéntica en los dos; límite 240 min)
| Escenario | Primer `WOULD_COMMIT` | Último `WOULD_COMMIT` | Primer `WOULD_ABORT` | Motivo |
|---|---|---|---|---|
| sin tratar | 1 | **206** | **207** | `collapse_boundary_not_reached` (colapso establecido en el 207) |
| tratamiento temprano (10) | 1 | 120 | — | — |
| tratamiento tardío (120) | 1 | 200 | — | — |
| sólo líquido | 1 | 120 | — | — |
| sólo sangre | 1 | 120 | — | — |
| deterioro grave (cristaloide en el 131) | 1 | **240** | — | no llega a colapso establecido en 240 min |
| recuperación tras lo grave (1 L + **4 U** en el 158) | 1 | 158 | **278** | `window_open`: el turno de la orden termina en el 278 |
| rescate tardío (orden en el 215) | 1 | 206 | **207** | la frontera llegó **8 minutos antes** de la orden |
| *extra:* recuperación dentro de la ventana (1 L + **2 U** en el 158) | 1 | 240 | — | el turno termina en el 218 |
| *extra:* «Place an IV line.» + tratamiento (10) | 1 | 10 | **70** | `supported_management`: `vascular_access` |

### 8.2 P3-207A · Ventana de `WOULD_COMMIT` en el deterioro sin tratar
Minutos **1 a 206** (206 transacciones); `WOULD_ABORT` en el **207** con la autoridad ya empezada: parada dura, el encuentro quedaría `INVALID_FOR_CONTINUATION` y **no** vuelve al heredado; los 33 minutos
restantes quedan `EXPERIMENT_HALTED`. Para referencia de sensibilidad, la frontera caería en el 195 con HIGH y en el 219 con LOW (región: 189–225).

### 8.3 Tres hallazgos de la serie
1. **«Place an IV line.» detiene el experimento.** Es la clase `vascular_access`, fuera de `SUPPORTED_ACTIONS` y con un hueco declarado en la sombra. Líquidos y sangre se ejecutan sin esa orden, así que la
   serie usa guiones sin ella; pero es la orden más habitual de un caso GI (bloqueo C6).
2. **Un turno es una transacción, y una infusión cabe en un turno.** Cuatro unidades avanzan el reloj 120 minutos: ordenada en el 158, la recuperación termina en el 278, **fuera de la ventana**, y sus 120 minutos
   intermedios se cubren con **una** comprobación de frontera en vez de comprometerse minuto a minuto. Con dos unidades (60 min) cabe (bloqueo C7).
3. **El residente vería un salto.** En la recuperación dentro de la ventana, la palabra pasa de «Unresponsive» (158) a «Alert» (218) sin fila intermedia: es la granularidad del turno, igual que hoy en el heredado.

## 9 · P3-208 · Revisión adversarial independiente
**Quién y cómo.** Un revisor **independiente y de sólo lectura**: escribió sus sondas fuera del repositorio, no editó nada y **no corrió ninguna autoridad real**. Recibió el código, no las conclusiones.
Cada hallazgo se **confirmó volviendo a correr su sonda** antes de corregir, y se volvió a correr después. Registro: `adversarial_review` en `docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json`
(18 entradas, cada una con su evidencia y, si se corrigió, el antes, el después y sus pruebas de regresión).

### 9.1 Los doce ataques del encargo
| # | Ataque | Resultado | Qué se encontró y qué se hizo |
|---|---|---|---|
| 1 | Instantánea V1 alterada | **HALLAZGO ALTO · corregido** | cuatro vías pasaban (§6): `BoundSnapshot` hecho a mano, registro que miente al construir, anclas de llegada movidas, ratificación forjada o registro con `superseded_by`. Todas rechazadas ahora |
| 2 | Linaje equivocado | **HALLAZGO MEDIO · corregido** | un linaje ofrecido por quien llama **sustituía** la lectura viva, y los bytes del núcleo se leían **una vez** al abrir. Ahora se leen cada minuto y lo ofrecido sólo puede añadir un rechazo |
| 3 | Lector de consciencia con cambio oculto de puntuación | **HALLAZGO MEDIO · corregido en la auditoría** | la fisiología **no** se falsó (0 diferencias en 12 turnos, 2 casos, 3 palabras). Sí: `record_findings` estaba clasificado como persistencia y decide si el portal **retiene** una sugerencia de IA; el recorrido tenía puntos ciegos; una afirmación era una constante. Reclasificado, con su guarda (la novena; no existe), sus tres consumidores y los límites del método declarados |
| 4 | Acción no soportada tras el primer compromiso | bloqueado · **un hallazgo bajo corregido** | en el turno: `WOULD_ABORT`, `authority_had_begun` cierto y todo lo posterior `EXPERIMENT_HALTED`. En la liquidación se saltaban las filas sin clase y el libro ilegible: ahora detienen |
| 5 | Presión pasa, consciencia falla | **bloqueado** | nunca se informa una presión sola |
| 6 | Consciencia pasa, presión falla | bloqueado · **un hallazgo bajo corregido** | un fallo de la sesión en un minuto **anterior** del mismo turno no se leía (regla **heredada del sitio**). La transacción en seco lee ya todo el turno; la regla del sitio se declara (C10) |
| 7 | Colapso entre captura y compromiso | **bloqueado** | con fisiología real (§7) e inyectado en el primer minuto, uno intermedio, el último y uno no mostrado |
| 8 | Reproducción que no coincide | **bloqueado** | en cada mitad, también en un minuto intermedio |
| 9 | Compromiso duplicado | **bloqueado** | segunda vez `WOULD_ABORT`, tercera `EXPERIMENT_HALTED` |
| 10 | Vuelta al heredado tras el primer compromiso | **HALLAZGO MEDIO · corregido** | (a) una **excepción** dentro del minuto no era un rechazo: sin registro, sin detención, y el minuto siguiente daba `WOULD_COMMIT`; además salía al turno heredado y **faltaban su entrada y sus filas del libro**. (b) el tiempo clínico **fuera de un turno de orden** no se observaba. Ahora ambos son rechazos con registro |
| 11 | Cambios visibles para el residente | **bloqueado** | estado, entradas, libro, llegada y sesión de sombra idénticos con y sin arnés (57 a con una orden no soportada; 72 a, 61 minutos). La única vía era 10(a) |
| 12 | Autoridad heredada alterada durante la corrida en seco | bloqueado · **un hallazgo bajo corregido** | testigos, registro de instantáneas aprobadas, banderas y `COMMON_CORE_RUNTIME_AUTHORITY = False` intactos tras ~45 ataques. Un observador **anidado** evaluaba cada turno dos veces: ahora se rechaza |

### 9.2 Hallazgos fuera de los doce
| Hallazgo | Resultado |
|---|---|
| `only_the_pair_would_move` **no podía fallar por sí sola**: el arnés elegía él mismo los cuatro campos; un candidato con frecuencia, saturación y lactato daba `WOULD_COMMIT` | **corregido**: se aplica todo lo que trae la mitad de presión y el conjunto debe ser exactamente el par |
| La **comparación de presión de P3-202 pasaba en vacío**: dos series vacías, una serie que perdía minutos o sin campos obligatorios leían `RECERTIFIED` | **corregido**; la comparación real **no cambia**: 34 escenarios, 78 minutos, 0 diferencias fuera de las explicadas |
| El límite de tiempo no tenía techo; la guarda de estado **detectaba pero no prevenía** y lanzaba dentro del turno heredado | **corregido** (§8) |
| Una contradicción **fuera** de los episodios no la veía nadie | **corregido** (§2.2: 1930 minutos, 0 violaciones) |
| **Dos límites del sitio de presión que ya existe** (no del arnés) | **aceptado y declarado**, no corregido: la capa no se edita en este ciclo (§9.3) |
| Lo que la revisión no pudo comprobar | una edición **real** de los bytes del núcleo (se simuló); la **página** del encuentro (sus lectores se leyeron, no se ejecutaron); las bifurcaciones de ataque en 72 a (se corrieron en 57 a; la serie de manejo sí cubre los dos); la suite completa |

### 9.3 Dos límites del sitio de autoridad de presión que ya existe (C9 y C10)
Son propiedades de la **capa dormida**, leídas de su código y **no modificadas**. La serie de desarrollo no las ejercita, porque juega turnos de orden por el arnés guionado; por eso la recertificación de
§4 **no dice nada** sobre ellas.

* **C9 · El tiempo clínico fuera de un turno de orden no pasa por el sitio.** Una pregunta de anamnesis o un examen avanzan el reloj del motor por `app.spend_clinical_time` (3 llamadores), que avisa a la
  sombra (`observe_time`) y **nunca** al sitio de autoridad; y el sitio no tiene regla que note un turno que no vio. **Lectura del código, no una trayectoria medida:** con una autoridad activa, un minuto que
  pase por esa ruta conservaría las presiones del motor heredado mientras los turnos de orden llevan las comunes. **No se ejecutó con autoridad** (este ciclo lo prohíbe). En la transacción en seco, esa
  ruta y cualquier turno no visto se rechazan.
* **C10 · El sitio lee los fallos de la sombra del último minuto del turno.** Un fallo registrado en un minuto intermedio de un turno de varios minutos no rechazaría el compromiso. Sólo se alcanzó por
  inyección: en los caminos propios de la capa, un avance que falla no registra minutos posteriores.

**Consecuencia para el veredicto:** «presión lista» vale para la ruta que la serie juega (**turnos de orden por el arnés guionado**), no para la página del encuentro.

## 10 · P3-209 · Punto de control
**B · `PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY`.**

* **Presión: lista, en la ruta que la serie juega.** La serie de autoridad de desarrollo es idéntica en el núcleo activo (turnos de orden por el arnés guionado). La revisión añadió dos límites del sitio
  que también atan a la presión **antes de cualquier uso en la página del encuentro** (C9, C10).
* **Consciencia: no lista.** Lo medido es favorable (15 de 15 episodios coherentes y 1930 minutos sin contradicción, vínculo exacto, transacción en seco correcta), pero faltan cosas que no son de medir.
* **La revisión adversarial no cambió ninguna de las dos mitades del veredicto.** Encontró defectos en once de sus dieciocho entradas, todos en los arneses y en la auditoría de este ciclo (del lado de las pruebas), ya corregidos y
  con su prueba de regresión, y los dos límites del sitio. El veredicto deja de ser provisional.
* No es `A`: quedan la revisión docente, las guardas de los lectores y el camino de compromiso. No es `C`: la transacción **diseñada** funciona y resistió la revisión una vez corregida; lo que no está
  listo es la consciencia. No es `D`: no hace falta fisiología nueva ni rediseño; hace falta **extender** la capa.

### 10.1 Bloqueos exactos
| # | Tipo | Bloqueo |
|---|---|---|
| C1 | revisión docente | FD-AUTH-04: las respuestas a la tabla de §2.3 están pendientes |
| C2 | guardas | FD-AUTH-05: la autoridad de consciencia **tiene** efectos aguas abajo; **ocho de las nueve** guardas no existen (§3.3). El inventario encuentra los sitios que **nombran** la palabra; no prueba que ningún otro código la lea |
| C3 | técnico | el camino de compromiso del par no existe en la capa (`AUTHORITY_DOMAIN`, propiedad y `commit` son de presión numérica): construirlo **dormido** y certificarlo, como se hizo con la presión |
| C4 | técnico | el vínculo con la instantánea está del lado de las pruebas: la capa construye testigos por nombre |
| C5 | decisión docente | la palabra «Unresponsive» con pulso (el heredado sólo la escribe en el paro; la instantánea la lee desde el minuto 158 sin tratar) |
| C6 | decisión docente o de ingeniería | «Place an IV line.» (`vascular_access`) detiene el experimento |
| C7 | diseño | granularidad del turno frente a la infusión: la recuperación de 4 U termina fuera de la ventana y sus minutos intermedios no se comprometen |
| C8 | decisión docente | la concesión de autoridad y la aprobación de una instantánea **para autoridad** (el registro sigue con sólo `gi_pressure_committed`) |
| **C9** | técnico (P3-208; **ata también a la presión**) | el tiempo clínico fuera de un turno de orden (`app.spend_clinical_time`) no pasa por el sitio de autoridad, y el sitio no nota un turno que no vio (§9.3) |
| **C10** | técnico (P3-208; **ata también a la presión**) | el sitio lee los fallos de la sombra del **último** minuto del turno (§9.3) |

### 10.2 Paso siguiente (sin ejecutar; requiere un encargo nuevo)
1. La docencia responde la tabla de §2.3 (C1) y las dos preguntas de palabra y de acción (C5, C6).
2. Con esas respuestas: diseñar y construir **dormidos, en la capa**, las guardas de los lectores (C2), el camino de compromiso del par (C3), el vínculo con la instantánea (C4), un sitio o un rechazo
   explícito para el tiempo fuera de un turno de orden (C9) y la regla de fallos de todo el turno (C10), con sus mutantes y **una** certificación integrada de la capa; decidir la granularidad del turno (C7).
3. Repetir esta serie en seco por el camino dormido de la propia capa. Sólo entonces una decisión docente (C8) podría autorizar el experimento.

Independiente y ya posible: el experimento de autoridad de desarrollo **sólo de presión** en el núcleo activo, **por el arnés guionado (sólo turnos de orden)**; no en la página del encuentro hasta cerrar C9.
