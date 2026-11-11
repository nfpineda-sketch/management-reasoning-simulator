# Fase 3 · GI: superficie de autoridad, diseño del experimento, contrato de fallo, frontera, contrafactual y punto de control (P3-193 a P3-198) · registro (2026-11-11)

**Alcance.** Preparar el experimento, **no activarlo**. No se habilita autoridad (`COMMON_CORE_RUNTIME_AUTHORITY = False`; la puerta `gate({}, environ={})` sigue
rechazando), no se registra ninguna instantánea como aprobada (`APPROVED_SNAPSHOTS` conserva **sólo** `gi_pressure_committed`), no se expone nada al residente, la puntuación y el
primer piloto no cambian, no se inventa ninguna regla terminal, ningún encuentro lo termina el núcleo común y **no hay afirmación de validación clínica**.

| Punto | Resultado |
|---|---|
| P3-196 frontera | **B · `AUTHORITY_WINDOW_CAN_BE_SAFELY_BOUNDED_BEFORE_BOUNDARY`** |
| P3-198 punto de control | **A · `GI_READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_DESIGN_REVIEW`** (preparado para la **revisión del diseño**; **no** para activar) |

Registros: `docs/revision/PHASE3_GI_AUTHORITY_READINESS.json` y `docs/revision/PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json`; pruebas: `test_phase3_gi_authority_readiness.py` (24); arneses
`test_gi_authority_surface.py` y `test_gi_counterfactual.py`. Cada afirmación es `VERIFIED` (una prueba la recalcula del código o de un encuentro en vivo), `RECORDED` (tomada de un
registro anterior) o `DESIGN` (nada la implementa).

## 1 · P3-193 · Inventario de la superficie de autoridad (sólo lectura)
El dueño de **toda** salida en tiempo de ejecución es hoy `LEGACY_AUTHORITY`. La columna es el **mejor estado que tiene el núcleo común** para esa salida.

| Salida | Estado en el núcleo común | Evidencia | Hueco |
|---|---|---|---|
| SBP / DBP / MAP | `COMMON_CORE_CERTIFIED_BUT_NOT_AUTHORIZED` | núcleo de presión certificado; **un** punto aprobado `gi_pressure_committed` (sólo experimento de desarrollo, casos 57m y 72f) | corrió sobre el núcleo de **cierre** (`22b90a6f…`), no sobre el miembro activo; la PAS común baja de la mínima del heredado (50 / 58 mmHg) desde el minuto 153 (57m) / 144 (72f) sin tratar; sin tolerancia clínica |
| Frecuencia cardíaca | `COMMON_CORE_SHADOW_AVAILABLE` | `monitor_rate_bpm` en la sombra; variable `display`, tolerancia TBD | sin aprobación; hasta 17 lpm de diferencia esperada-arquitectónica en las 14 corridas; 3 min en sentido opuesto con sólo cristaloide |
| Pulso / ritmo | `COMMON_CORE_SHADOW_AVAILABLE` | el pulso coincide en los 1930 minutos comparados | la vía terminal del mismo estado es `UNRESOLVED_BOUNDARY` |
| SpO2 | `COMMON_CORE_SHADOW_AVAILABLE` | igual en los 1930 minutos | **concordar no es validar**: en GI no se ejerce la cadena de oxigenación (los dos motores mantienen el valor autorado) |
| Frecuencia respiratoria | `COMMON_CORE_SHADOW_AVAILABLE` | `display`; explicada por arquitectura en GI | tras tratar, sentido opuesto en 55 minutos comparados |
| Lactato | `COMMON_CORE_SHADOW_AVAILABLE` | `display`; explicado por arquitectura en GI | tras tratar, el laboratorio heredado baja y el común no: 62 minutos en sentido opuesto |
| Hemoglobina | `COMMON_CORE_SHADOW_AVAILABLE` | el heredado cae con la hemorragia sin tratar (6,69 → 4,54 g/dL al minuto 240) y el común queda ≈ 6,4; explicada por arquitectura (`PHASE3_RUNTIME_INTEGRATION`) aunque la tabla la llama `exact` | el `exact` vale sólo para las corridas de la comparación certificada, no para el curso GI en vivo |
| Llenado capilar | `COMMON_CORE_SHADOW_AVAILABLE` | diferido por la docencia fuera del primer dominio | sin aprobación |
| **Categoría de consciencia** | **`COMMON_CORE_CERTIFIED_BUT_NOT_AUTHORIZED`** | PHASE2_AMENDMENT_2 certificada, en la sombra GI con los tres testigos y `GI_DEVELOPMENT_SNAPSHOT_V1`; evaluador independiente bit a bit | el heredado y la aplicación **leen** el campo (abajo); 461 minutos `POTENTIAL_EDUCATIONAL_PROBLEM`; la puerta, la propiedad y `commit` son de presión numérica |
| Estado de colapso (ninguno / inminente / establecido) | `COMMON_CORE_SHADOW_AVAILABLE` | el predicado queda registrado junto al heredado en el bloque terminal de la traza | el heredado **no tiene** campo de colapso (sólo la bandera de paro): nada que comparar ni que escribir |
| **Estado terminal (paro / terminalización desde el núcleo)** | **`UNRESOLVED_BOUNDARY`** | el núcleo lanza `UnresolvedBoundary` en el minuto 349 sin tratar | no hay regla terminal declarada ni se inventa |
| Soporte respiratorio / trabajo respiratorio / extremidades | `MISSING_COMMON_CORE` | ninguna variable de la tabla de comparación certificada los lleva | son descriptores sólo del heredado |
| Glucosa / potasio / FiO2 / volúmenes administrados | `LEGACY_AUTHORITY` | variables `exact` que ambos motores sostienen desde las mismas entradas | no son salidas de una ley común |

### 1.1 Quién **lee** `mental_status` (lo que hace que la consciencia no sea una hoja)
Verificado por recorrido de los módulos de ejecución (36 módulos mencionan el campo; no se abre el corpus de validación). Los que importan para GI:
* **`family_engine.py`** (17 menciones): la **validación de órdenes** lee `observable.mental_status` para decidir si la vía oral es segura (`glucose_rescue.ORAL_SAFE_MENTAL`). Esa acción **no** está
  entre las `SUPPORTED_ACTIONS` de una autoridad de presión, así que dentro del conjunto soportado el lector del motor no cambia el resultado; pero es un lector **declarado y no auditado**.
* **`app.py`** (20): retroalimentación y comparaciones antes/después de la reevaluación, narrativa, exportación; `management_trace_analysis`, `cognitive_review`, `faculty_analysis`, `record_findings`,
  `coupled_encounter`, `image_consistency`, `image_pilot`, `patient_appearance`, `visual_observations`: lectores de **presentación o análisis**, no de fisiología.
* Los módulos `generated_*` y `hypoglycemia_*` pertenecen al motor de casos generados (`clinical_physiology`), que **no** está integrado y no se autoriza integrar.

## 2 · P3-193A · Reconciliación con el experimento de autoridad de presión
| | |
|---|---|
| **Validado** (`RECORDED`, con los hechos de la puerta verificados) | **sólo presión** (`sbp`, `dbp` escritas; `map` derivada por la pantalla); **sólo desarrollo** (entornos `development` y `faculty`); **los dos casos permitidos**; **una transacción por turno**: captura, cómputo, validación, compromiso atómico o aborto; **falla dura visible** (`HARD_FAIL_VISIBLE_TO_FACULTY`) sin cambio de motor dentro del encuentro; un primer experimento de 3 minutos de autoridad y una serie de 26 trayectorias elegibles (64 minutos), con replay exacto |
| **Sobre qué núcleo** | el **cierre** de la Fase 2 (`22b90a6f…`, 141 fuentes). El miembro activo es ahora `PHASE2_AMENDMENT_2` (`a0af7d08…`, 144). Nada se re-corrió en este ciclo |
| **No establecido** | consciencia, colapso o cualquier otra salida; la validez clínica de cualquier magnitud (0 de 58 regiones del registro de calibración aprobadas por la docencia); que el resultado de presión **siga valiendo** en el miembro activo; una nota de procedencia que la serie de 26 trayectorias dejó abierta (P3-51, veredicto B): su estado posterior **no se re-audita aquí** |

**No se supone que aquella certificación se extienda a consciencia ni a colapso.** La puerta lo impone: `AUTHORITY_DOMAIN` es exactamente `("sbp","dbp","map")`, `validate` exige
`tuple(self.domain) == AUTHORITY_DOMAIN`, y `commit` **rechaza** cualquier campo no numérico.

## 3 · P3-194 · Diseño del experimento futuro (nada de esto está implementado ni se puede activar)
### 3.1 P3-194A · Ranking de dominios por preparación (la autoridad incremental, de menor a mayor superficie)
| # | Dominio | Preparación | Por qué |
|---|---|---|---|
| 1 | presión (`sbp`, `dbp`, `map`) | `MACHINERY_READY` | único dominio con instantánea aprobada de desarrollo, puerta, transacción atómica, almacén y replay; falta re-validar en el miembro activo (barato, sin fisiología) |
| 2 | **consciencia, sólo junto con la presión** | `DESIGN_NEEDS_EXTENSION` | la categoría es función de la **misma** entrega y perfusión relativas que mueven la presión: escrita sola mostraría al residente una presión heredada junto a una consciencia común que vino de **otro curso**; el par es la superficie coherente más pequeña y repite la regla de que las tres presiones se poseen juntas |
| 3 | estado de colapso | `RECORD_ONLY` | no hay campo heredado que escribir ni comparar: queda en el artefacto como valor sólo de comparación, nunca se escribe ni se muestra |
| 4 | estado terminal / paro | `BLOCKED` | `UnresolvedBoundary`: sin regla terminal declarada ni autorizada |
| 5 | FC, FR, lactato, Hb, CRT | `NOT_YET` | sentidos opuestos tras tratar, explicaciones parciales o diferimiento docente explícito (CRT) |

### 3.2 Alcance propuesto: `GI_PRESSURE_PLUS_CONSCIOUSNESS_DEVELOPMENT_AUTHORITY_EXPERIMENT` (SÓLO DISEÑO)
* **Entornos** `development` y `faculty`; **casos** `gi_bleed_57m` y `gi_bleed_72f` (la lista actual: ninguna arquitectura demuestra un alcance más amplio y seguro); **piloto, residente y puntuación** excluidos.
* **Dominio escrito:** `sbp`, `dbp`, `map` (derivada por la pantalla) y `mental_status` (la palabra heredada de la categoría común). **Sólo registro:** el estado de colapso. **Nunca escritos:** FC, SpO2, FR, lactato, Hb, CRT, ritmo, pulso, paro.
* **Ventana:** escenarios guionados de **≤ 240 minutos simulados** (109 minutos antes de la frontera). El experimento termina por su propio guion; **el encuentro nunca lo termina el núcleo común**.
* **Etapas:** 0. re-correr la serie de autoridad de presión en el miembro activo; 1. preparación técnica (escritor categórico con regla de pareja, vínculo con la instantánea, auditoría de los lectores de `mental_status`, la capa capaz de correr la instantánea por identificador y huella); 2. **ensayo en seco**: captura, cómputo y validación del par en los 14 escenarios **sin compromiso** (el arnés contrafactual de este ciclo es su primera forma); 3. **sólo con una concesión docente escrita**: el primer compromiso de desarrollo, acotado como arriba.

### 3.3 P3-194B · Atomicidad
Se conserva `captura → cómputo → validación → compromiso atómico` **o** aborto. El par se escribe **en una transacción o en ninguna**, con **un** mapeo preparado y la puerta reevaluada **al comprometer**; ningún minuto queda mitad común, mitad heredado; tras
el primer compromiso el encuentro **no vuelve** al motor heredado. La validación suma a las diez comprobaciones existentes `snapshot_bound`, `pair_complete`, `consumers_declared` y `window_open`.

### 3.4 P3-194C · Vínculo con la instantánea (sin valores implícitos)
El experimento nombra `GI_DEVELOPMENT_SNAPSHOT_V1` por **identificador, huella de identidad, huella del registro, digesto del linaje y igualdad de **cada** valor** con el registro. El perfil de Amendment 2 se construye **desde el registro, nunca desde
los nombres de `systemic_consciousness.WITNESSES`**; un valor ausente o distinto rechaza. La instantánea **no** se registra como artefacto de autoridad.

## 4 · P3-195 · Contrato de fallo y reversión (la autoridad falla **cerrada**)
Reglas: falla cerrada; **sin retorno silencioso al heredado tras el primer compromiso**; **antes** del primer compromiso el heredado puede seguir porque la autoridad nunca empezó (P3-195A); **después**, parada dura con las semánticas experimentales
ya establecidas (`EXPERIMENT_HALTED`, `INVALID_FOR_CONTINUATION`), sin cambiar de motor (P3-195B); un experimento detenido sirve para replay y análisis, **nunca** para continuar; el núcleo común nunca termina un encuentro.

| Fallo | Detección | ¿Existe? | Antes del primer compromiso | Después del primer compromiso |
|---|---|---|---|---|
| desajuste de linaje | condición de puerta `phase2_digest`, reevaluada al comprometer | sí | la puerta rechaza: heredado desde el minuto 1; el rechazo queda registrado | parada dura; el experimento se **DETIENE**; sin cambio silencioso al heredado |
| desajuste de instantánea | `approved_snapshot` (presión) **y** el vínculo id + huellas + valores de la instantánea (**adición requerida**) | parcial | no se abre el sitio; heredado todo el encuentro | parada dura; un cambio de configuración dentro del encuentro también detiene (`CONFIGURATION_CHANGED`) |
| acción no soportada | `unsupported_among` sobre las acciones del turno, **antes** de buscar el candidato | sí | el encuentro es inelegible: heredado todo | parada dura (`UNSUPPORTED_AUTHORITY_ACTION`); el minuto ya comprometido no se reescribe |
| frontera no resuelta | validación `no_unresolved_boundary` sobre las fallas de la sesión de sombra | sí | se aborta el minuto con artefacto de reversión; el heredado continúa sólo si nunca hubo compromiso | parada dura: **parada del experimento, no regla terminal**; el encuentro no lo termina el núcleo común |
| falla de invariante del núcleo | validación `invariants_hold` y `no_core_failure` | sí | se aborta el minuto, nada se escribe | parada dura |
| desajuste de replay | validación `minute_reproducible` (digesto de replay = esperado) | sí | se aborta el minuto | parada dura; el artefacto conserva los dos digestos |
| falla parcial de salida | `commit` construye **un** mapeo preparado y lanza `AuthorityRefused` ante cualquier fallo, dejando el estado como se capturó (presión; un campo categórico es **adición requerida**) | parcial | nada se escribió: aborto | la transacción queda `ABORTED`, el compromiso previo se mantiene, el experimento se **DETIENE**; un par a medias no puede existir |
| falla de persistencia de la traza | el almacén es obligatorio (ruta absoluta fuera del repositorio); su falla es condición de parada | sí | el sitio no se abre: heredado todo | parada dura; el encuentro no continúa con el otro motor |

Probado (`VERIFIED`): una transacción que encuentra una `UnresolvedBoundary` **aborta, no escribe nada, deja artefacto de reversión** (`rescue`: «never continue the same encounter with the other engine») y **su `commit` lanza `AuthorityRefused`**.

## 5 · P3-196 · Auditoría de `UnresolvedBoundary`
**Veredicto: B · `AUTHORITY_WINDOW_CAN_BE_SAFELY_BOUNDED_BEFORE_BOUNDARY`.**

| Pregunta | Respuesta (medida en vivo, dos casos) |
|---|---|
| Disparador | `derived.py`: «effective output reached zero while a pulse is present and no declared terminal transition applied» (la regla de colapso está apagada o su criterio no se cumple) |
| Momento | **minuto 349**, sin tratar, en **los dos** casos y en las cuatro corridas (la sesión y los tres testigos) |
| Escenarios que lo alcanzan | **sólo** el curso sin tratar largo (380 min pedidos). Ninguno de los 14 requeridos (≤ 278 min), ni el rescate tardío (orden en el 215, jugado hasta el 336, sin fallas) |
| Qué queda indefinido | **toda** salida común de la sesión y de los tres testigos desde el 349 (las corridas **FALLAN**; sus filas hasta el 348 se conservan) |
| Antes o después del colapso establecido | **después**: el testigo instantánea llega a SIN RESPUESTA en el 158 y a colapso establecido en el 207; la frontera cae **142 min después** |
| Qué muestra el heredado ahí | pulso presente, sin paro, «Obtunded», PAS 50 / PAD 32 (57m) y 58 / 40 (72f); **sigue activo** |
| ¿Podría la autoridad terminar antes? | **No debe y no se propone**: terminar un encuentro desde el núcleo común no está autorizado ni se inventa una regla. Lo que sí hace una transacción que la encuentra es **abortar y detener el experimento** (probado) |
| ¿Hace falta un mapeo terminal antes de la autoridad? | **No** para la ventana acotada de desarrollo; **sí** antes de cualquier autoridad sin ventana o visible al residente. **No se inventa ninguno** |

**Lectura.** La frontera es una propiedad del curso **sin tratar** (la hemorragia compartida lleva el gasto efectivo a cero al 349). En una ventana **sin acotar** es alcanzable, así que el veredicto no es A; la ventana **puede acotarse** con el guion del propio experimento, con 109
minutos de margen. Una consideración distinta, **antes** de la frontera: la PAS común queda por debajo de 40 mmHg desde el minuto 194 (57m) / 211 (72f) y de 20 desde el 274 / 282, y por **debajo del mínimo del propio heredado** (50 / 58) desde el 153 / 144: es otra razón (bloqueo B9) para que la ventana acotada sea de 240 minutos y no mayor.

## 6 · P3-197 · Arnés contrafactual (legado autoritativo frente a lo que habría escrito la instantánea)
**Método.** Un encuentro con el heredado como **única autoridad** y la sombra al lado (que sólo observa). Por minuto y por dominio candidato: valor heredado (el que vería el residente), valor común candidato (la instantánea),
diferencia, fuente causal y validez. **No se compromete ningún valor común al encuentro.** Se probó que leer la sombra **no altera la trayectoria heredada** (42 muestras idénticas con la sombra encendida y apagada), que la puerta sigue cerrada y que las columnas guardadas se **re-derivan** de un encuentro en vivo.
Dos casos × siete escenarios = 14 corridas (1930 minutos comparados), más el curso sin tratar largo y el rescate tardío.

**Clasificación (declarada antes de leer la serie; estructural, sin tolerancia numérica clínica):** `MATCH`; `STRUCTURAL_CONTRADICTION` (el pulso, o el **sentido** en que se movió una cantidad, leído desde la llegada antes de la primera orden y desde el inicio de la primera orden después de ella); `POTENTIAL_EDUCATIONAL_PROBLEM` (la palabra de consciencia difiere en ≥ 2 bandas, o un lado dice Alerta y el otro no); `EXPECTED_MECHANISTIC_DIFFERENCE` (cualquier otra diferencia entre dos arquitecturas que mueven la cantidad en el mismo sentido); `UNRESOLVED` (sin valor comparable). **Una diferencia grande no es un fallo y no se ajusta (FD-GI-03).**

### 6.1 Minutos por clase, en las 14 corridas requeridas (1930 minutos)
| Dominio | MATCH | EXPECTED | STRUCTURAL | EDUCATIONAL | UNRESOLVED | Fuente causal del candidato común |
|---|---|---|---|---|---|---|
| SBP | 59 | 1859 | 12 | — | — | coordenada de presión salida × tono del volumen sanguíneo compartido |
| DBP | 93 | 1832 | 5 | — | — | la misma coordenada |
| MAP | 83 | 1836 | 11 | — | — | derivada de sus propias presiones |
| FC | 484 | 1443 | 3 | — | — | frecuencia de monitor por el impulso simpático de la deuda y la presión |
| SpO2 | 1930 | — | — | — | — | cadena de oxigenación (no ejercida en GI) |
| Frecuencia respiratoria | 192 | 1683 | 55 | — | — | impulso respiratorio de la carga ácida y la demanda |
| Lactato | 212 | 1656 | 62 | — | — | lactato de la deuda de entrega de oxígeno (D) |
| Hemoglobina | — | 1930 | — | — | — | llegada y dilución por el volumen administrado |
| CRT | 836 | 1086 | 8 | — | — | llenado capilar del estado de bomba y tono |
| **Categoría de consciencia** | 1224 | 245 | — | **461** | — | compuesto de PHASE2_AMENDMENT_2 (F, colapso) con la instantánea |
| Pulso | 1930 | — | — | — | — | estado de ritmo y pulso |
| Estado de colapso | 1796 | — | — | — | 134 | predicado de colapso de la enmienda; el heredado no tiene campo |

**Dos hechos estructurales:** (1) **en ningún curso sin tratar hay una contradicción estructural**: los dos motores coinciden en el sentido de toda la **deterioración**; (2) **toda** contradicción estructural aparece **después de la primera orden** (prueba).

### 6.2 Dónde están las diferencias de consciencia (57m; en el 72f las ventanas se desplazan: el heredado se altera en el 138, **después** del común, en el 109)
| Escenario | Ventanas `POTENTIAL_EDUCATIONAL_PROBLEM` (minutos) | Lectura |
|---|---|---|
| sin tratar | 63–108 y 158–174 | el heredado dice «Drowsy» desde el 63 y el común sigue Alerta hasta el 109 (46 min); desde el 158 el común dice SIN RESPUESTA y el heredado sigue en «Drowsy» hasta el 175 (2 bandas) |
| tratamiento tardío | 63–108 | sólo el inicio; la orden en el 120 devuelve a los dos a Alerta |
| sólo líquido | 109–120 | el heredado dice «Drowsy» y el común, que responde mejor a un litro de cristaloide, sigue Alerta |
| deterioro grave (sólo cristaloide en el 131) | 63–108 y 194–198 | el común mejora un tiempo (136: 2 → 1) y vuelve a empeorar (173, 194); el heredado sólo empeora (la primera muestra heredada tras la orden es el 151: la infusión ocupa el reloj) |
| recuperación tras lo grave | 63–108 y 158 | el heredado no se mueve durante la infusión de 120 min (una sola muestra) |
| tratamiento temprano, sólo sangre | ninguna | los dos motores dicen Alerta todo el tiempo |

### 6.3 Contradicciones de sentido (todas tras la primera orden)
* **Tratamiento tardío** (orden en el 120; minutos 180–200, tras el fin de la infusión): **lactato** y **frecuencia respiratoria** — el heredado **mejora** (5,1 → 3,9; 31 → 22) y el común **no mejora** (4,7 → 4,9; 27 → 28).
* **Deterioro grave con sólo cristaloide:** PAS, PAD, MAP, FC, CRT, lactato y FR durante 1–12 minutos en torno a la mejoría transitoria del núcleo común (151–176).
* **Hemoglobina:** sin contradicción de sentido, pero el heredado cae **todo el tiempo** (−2,15 g/dL en 240 min) y el común casi no se mueve (−0,3): diferencia esperada-arquitectónica ya documentada.

### 6.4 P3-197C · Clasificación del riesgo educativo (informativa; no se ajusta nada)
| Riesgo | Clase | Estado |
|---|---|---|
| El inicio de la consciencia difiere del heredado: 46 min en el 57m (heredado 63, común 109) y, al revés, 29 min en el 72f (común 109, heredado 138); la diferencia viene de que el heredado separa los casos por presión absoluta y el común no | `POTENTIAL_EDUCATIONAL_PROBLEM` | **ya decidido** por la docencia: FD-GI-01 (entrega relativa a la llegada) y FD-GI-03 (sin ajuste a los minutos heredados); sólo sería visible al residente con autoridad |
| El común llega a SIN RESPUESTA (158) y el heredado nunca pasa de «Obtunded» en 240 min | `POTENTIAL_EDUCATIONAL_PROBLEM` | misma decisión; el heredado no tiene colapso |
| Un litro de cristaloide mantiene Alerta al común y el heredado se altera (57m) | `POTENTIAL_EDUCATIONAL_PROBLEM` | **sin decisión docente**: es lo que el residente vería al «hacer lo correcto» con sólo líquido |
| Lactato y FR no mejoran tras el tratamiento en el común, y sí en el heredado | `STRUCTURAL_CONTRADICTION` (de sentido) | **sin decisión docente**; no se ajusta: el heredado no es la verdad clínica |
| PAS común por debajo de la mínima del heredado desde el 153 / 144 sin tratar | `EXPECTED_MECHANISTIC_DIFFERENCE` | ventana acotada en 240 min |
| Estado de colapso sin contraparte heredada | `UNRESOLVED` | sólo registro |
| Hemoglobina: caída heredada frente a casi constante común | `EXPECTED_MECHANISTIC_DIFFERENCE` | ya documentado en la integración |

Ninguna diferencia se clasifica como defecto ni motiva un ajuste.

## 7 · P3-198 · Punto de control
**A · `GI_READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_DESIGN_REVIEW`.** La región GI de desarrollo es coherente; la instantánea está elegida y registrada; el diseño es acotado, atómico y vinculado; el contrato de fallo cubre los ocho fallos; la frontera
se puede acotar; el contrafactual no encuentra defectos estructurales en el deterioro. **Es preparación para la revisión docente del diseño, no una concesión ni una preparación para activar.**

No es `B` (la frontera no bloquea una ventana acotada), no es `C` (ninguna invariante de la docencia se incumple en el comportamiento: lo que queda son diferencias respecto del heredado, que FD-GI-03 prohíbe ajustar) y no es `D` (el diseño **extiende** la maquinaria existente —un escritor categórico y una regla de pareja—, no la rediseña).

### 7.1 Bloqueos antes de activar cualquier autoridad
| # | Tipo | Bloqueo |
|---|---|---|
| B1 | decisión docente | una **concesión** de autoridad y su aprobación de una instantánea **para autoridad**: `GI_DEVELOPMENT_SNAPSHOT_V1` es de desarrollo y el registro sólo tiene el punto de presión |
| B2 | decisión docente | **ratificar** `GI_DEVELOPMENT_SNAPSHOT_V1` (la eligió una regla, como autoriza el encargo; la docencia no la ha visto correr) |
| B3 | técnico | la puerta, la propiedad y `commit` son de presión; faltan el campo categórico y la regla de pareja |
| B4 | técnico | la capa construye los testigos por **nombre**; no puede correr una instantánea por identificador y huella (cambio de la capa y su certificación) |
| B5 | auditoría | los lectores de `mental_status` están listados, **no auditados** |
| B6 | lectura docente | las diferencias educativas: 461 minutos de consciencia y las respuestas de sentido opuesto de lactato y FR |
| B7 | técnico | la serie de autoridad de presión corrió en el núcleo de cierre: re-correrla en el miembro activo |
| B8 | frontera | `UnresolvedBoundary` desde el 349: acotada por el guion; todo uso sin acotar o visible al residente exige una decisión de mapeo terminal |
| B9 | evidencia | la PAS común baja de la mínima heredada (153 / 144) y llega a ≤ 20 mmHg hacia el 274: ventana o lectura docente explícita |
| B10 | decisión docente | qué vería el residente, y el piloto: no concedido ni diseñado aquí |

### 7.2 Paso siguiente (sin ejecutar; requiere un encargo nuevo)
**Paquete de revisión docente del diseño:** presentar a la docencia §3 a §6 y pedirle B2, B6 y la dirección sobre B10; con eso, el trabajo técnico que **no** exige concesión es: **(0)** re-correr la serie de autoridad de presión en el miembro activo
(B7), **(1)** la auditoría de los lectores de `mental_status` (B5) y **(2)** el ensayo en seco del par sobre los 14 escenarios (sin compromiso). B3 y B4 se diseñan, pero se construyen y certifican sólo si la docencia aprueba el diseño. No se activa nada.

**Continuación (2026-11-11).** B2 quedó respondido (instantánea ratificada para experimentos de desarrollo), B5 (lectores) y B7 (presión en el núcleo activo) se hicieron, y el par se corrió en seco: `docs/PHASE3_GI_PREAUTHORITY_REVIEW.md`. **Corrección:** §2 decía que la nota de procedencia de P3-51 no se re-auditaba; estaba **cerrada desde P3-55** (linaje canónico). Este documento no se reescribe.
