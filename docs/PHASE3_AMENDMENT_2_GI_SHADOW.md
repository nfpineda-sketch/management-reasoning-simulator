# Fase 3 · Enmienda 2 certificada en la sombra GI (P3-172 a P3-180) · registro (2026-11-11)

**Alcance.** Integrar `PHASE2_AMENDMENT_2` (certificada) en `phase-3-runtime-integration` y habilitarla **sólo** en los perfiles
de desarrollo de la sombra GI. Observación pura: `COMMON_CORE_RUNTIME_AUTHORITY = False`, nada visible para el residente, nada en
la puntuación, primer piloto sin cambios, y ningún estado de colapso o consciencia del núcleo común termina un encuentro. Toda
magnitud es una `FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`: **no hay afirmación de validación clínica.**

## 0 · Decisiones de la docencia (2026-11-11)
1. Se acepta `PHASE2_AMENDMENT_2_GI_CONSCIOUSNESS_COLLAPSE_CERTIFIED`.
2. Recuperación confirmada: «recuperación significativa en ≈ 3–5 min simulados» significa que, partiendo de un deterioro ≈ 0,80, se
   cruza por debajo de 0,50 en ≈ 3–5 min **cuando la fisiología aguas arriba se ha recuperado lo suficiente**. No exige normalizar por
   debajo de 0,25 en ese intervalo.
3. La Enmienda 2 se admite **sólo para GI** en este paquete. No se habilita en opioide, ACS, edema pulmonar, embolia ni asma.
4. El estado de colapso o consciencia del núcleo común sigue siendo **sólo estado fisiológico**: no termina un encuentro.
5. Sin ampliar autoridad (`COMMON_CORE_RUNTIME_AUTHORITY = False`). 6. Sin exposición al residente. 7. El primer piloto congelado no cambia.

Linaje: `HISTORICAL_PHASE2_CLOSURE` (`22b90a6f…`) → `PHASE2_AMENDMENT_1` (`10b45ce2…`) → `PHASE2_AMENDMENT_2` (`a0af7d08…`).
Rama certificada `phase-2-amendment-2-terminal-consciousness`: candidato `ad7bf81`, cabeza final `5d644b9`.

## 1 · P3-172 · Auditoría de linaje previa (sólo lectura): `AMENDMENT_2_SAFE_TO_INTEGRATE`

### PI-1 · Los dos digestos de congelación de la Enmienda 1
Sondeo reproducible (`test_phase3_amendment_2_integration.py`). Ambos digestos se calculan con `blood_fluid_calibration.freeze_sources()`,
que hashea **todos** los archivos de `clinical_core/` bajo la vista activa, más el registro y el diseño del paquete.

| Digesto | Bajo la vista de cierre de la Enmienda 2 | Anidado: árbol de la Enmienda 1 + vista de cierre de la Enmienda 1 |
|---|---|---|
| `closure_guard_P2X1A` | **recalcula exacto** (`eca47d35…` = registrado) | difiere |
| `tone_domain_on_the_live_tree` | **recalcula exacto** (`a9634ffd…` = registrado) | difiere |

**Causa precisa del anidado.** Difieren exactamente dos archivos, `clinical_core/state.py` e `clinical_core/integration.py`. La Enmienda 1
nunca los modificó, así que su vista de cierre (`REVERSAL` propio: `derived.py`, `decision_pack.py`) no tiene reversión para ellos y los
lee **crudos del disco**, donde está el texto de la Enmienda 2. La Enmienda 2 sí declara su reversión para ambos, y por eso su vista
recalcula exacto.

**Clasificación (ambos): B · `TEST_HARNESS_REPRESENTATION_ARTIFACT`.** No es `C` ni `D`: ningún valor registrado se redefinió; el defecto
es de la *composición de vistas* (la vista de una etapa no conoce los archivos que una etapa posterior cambió y ella no).

**Pruebas exigidas.** Cierre histórico, Enmienda 1 y Enmienda 2 se reconstruyen exactos desde los archivos vivos
(`a2.historical_closure_verifies()`, `a2.amendment_1_verifies()`, `a2.amended_core_digest_now()`); el registro del cierre y el de la
Enmienda 1 no cambiaron desde `0c230f8` (`git diff` vacío), y las constantes de digesto de los paquetes cerrados no se tocaron.

### PI-2 · Apagado por omisión: `DEFAULT_OFF_BEHAVIORALLY_COMPATIBLE`
Con `amendment_2 = None`, en **10 corridas / 1150 estados** (GI ×2 en dos horizontes, ACS, edema, embolia, asma, opioide ×2) la
evolución física (`estado.to_dict()`), todas las cantidades derivadas —con el nivel de consciencia— y el estado auxiliar son
**idénticos estado por estado** al núcleo de la Enmienda 1 de la cabeza `3e911ea`. La diferencia de esquema es exactamente una clave:
`CoreProfile.to_dict()` pasa de 71 a 72 claves (`amendment_2: null`), y el estado auxiliar no gana ninguna (la memoria nueva queda fuera
de `AUXILIARY_FIELDS` mientras es `None`). No se exige identidad de bytes entre esquemas distintos.

## 2 · P3-173 / 173A · Integración
* Método: `git merge --no-ff` de `origin/phase-2-amendment-2-terminal-consciousness` (`5d644b9`) en `phase-3-runtime-integration`
  (`3e911ea`), sin force ni reescritura; se conserva la historia de ambas ramas. Sin conflictos (cuatro archivos solapados:
  `runtime_shadow.py` y tres `test_runtime_shadow_*`, fusionados automáticamente).
* `clinical_core/` tras la integración es **byte a byte** el de la rama certificada (`git ls-tree` idéntico); el digesto recalcula a
  `a0af7d08…` y la compuerta real reporta `PHASE2_AMENDMENT_2` `CERTIFIED`.
* Única modificación ejecutable fuera de `clinical_core/`: la entrada `PHASE2_AMENDMENT_2` en `runtime_shadow.CORE_LINEAGE`.
  `app.py`, `family_engine.py`, `pilot_acceptance.py`, `runtime_authority.py`, la puntuación y el primer piloto: sin cambios.
* Nueve pruebas de la Fase 3 que fijaban «el núcleo vivo es la Enmienda 1» se adaptaron (el núcleo vivo es hoy su sucesor certificado;
  los registros históricos no se reescriben, se leen contra el miembro del linaje que midieron; las de diseño A2-001…010 leen el árbol
  de la Enmienda 1 por la reversión declarada y probada).

## 3 · P3-174 · Perfil GI de desarrollo por testigos de región

**Arquitectura.** El adaptador registrado de GI (`GiHaemorrhageAdapter`) conserva el perfil comprometido, con la Enmienda 2 **apagada**:
la corrida propia de la sesión es la de siempre. Además, `region_witnesses()` abre en vivo, por sesión, **tres adaptadores de desarrollo**
(`GiHaemorrhageAdapter.witness("LOW" | "CENTER_REFERENCE" | "HIGH")`), cada uno con el perfil comprometido más **un solo campo**,
`amendment_2`, en el testigo correspondiente de `systemic_consciousness.WITNESSES`. Cada testigo es su propia trayectoria: no se elige,
no se promedia, no se prefiere (`CENTER_REFERENCE` no es un valor preferido) y el derivado `view` es sólo un mínimo y un máximo por
minuto junto a los valores individuales. Un conjunto no anida (un testigo no declara los suyos).

| Pieza | Qué hace |
|---|---|
| `runtime_shadow_families.RegionDeclaration` | Declara una vez qué es la región viva de una familia: el campo del perfil que mueven los testigos, el valor declarado de cada uno, lo que dice la traza de la región, las lecturas del derivado y las versiones del núcleo en que existe el campo. La declaración del opioide reproduce **exactamente** las constantes que ya usaban el conjunto y el almacén (ningún registro ni digesto del opioide cambia). |
| `GiHaemorrhageAdapter.region_declaration()` | `amendment_2`, `FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`, regiones por magnitud con su origen, grupos de procedencia, categorías observables y cortes, la lectura de la recuperación, `supported_family = gi_bleed`, `not_supported = opioid, acs, pulmonary_edema, pulmonary_embolism, asthma`, y «estado fisiológico sólo». Exige que el núcleo vivo sea `PHASE2_AMENDMENT_2` certificado (si no, el conjunto no abre y lo dice como falla `ensemble:lineage`). |
| `runtime_shadow_families.artifact_rows` | Añade, **sólo** a una corrida cuyo perfil declara la enmienda, los canales `systemic_encephalopathy_burden` (F), `collapse_burden`, `relative_delivery`, `relative_perfusion`, `category_index` y `collapse_state_index`. Una traza de cualquier otra corrida es la de siempre. |
| `runtime_shadow_store` | Los tres puntos que estaban cableados a la transmisión del opioide (el parámetro de cada corrida, el bloque `region` y la verificación de que el artefacto corrió el valor que el testigo declara) leen ahora la declaración de la familia. |
| `runtime_shadow_observer` | Canales de GI con los de la enmienda; preguntas docentes y parámetros no resueltos de la enmienda; bloque de frontera por testigo (§7). |

### P3-174A · Procedencia de cada testigo (todas `DEVELOPMENT_BEHAVIORAL_REGION`)
Cada testigo nombra, y el artefacto de cada corrida lleva, el origen de cada magnitud:

| Grupo | Magnitudes | Origen (`systemic_consciousness.IDENTIFIABILITY`) |
|---|---|---|
| Testigo de subida de F | `burden_rise_tau` | `DERIVED_FROM_EXISTING_EQUATION` |
| Testigo de bajada de F | `burden_clear_tau` | `DERIVED_FROM_EXISTING_EQUATION` |
| Umbrales de entrega relativa | `delivery_normal`, `delivery_severe` | `FACULTY_DEFINED_FROM_BEHAVIOR` |
| Umbrales de perfusión | `perfusion_normal`, `perfusion_severe` | `FACULTY_DEFINED_FROM_BEHAVIOR` |
| Persistencia y recuperación del colapso | `collapse_rise_tau`, `collapse_clear_tau`, `impending_burden`, `established_burden` | `WEAKLY_IDENTIFIED` |

| Magnitud | LOW | CENTER_REFERENCE | HIGH |
|---|---|---|---|
| `delivery_normal` / `delivery_severe` | 0,70 / 0,45 | 0,75 / 0,50 | 0,80 / 0,55 |
| `burden_rise_tau` / `burden_clear_tau` (min) | 1,5 / 6,4 | 1,65 / 8,5 | 1,85 / 10,5 |
| `perfusion_normal` / `perfusion_severe` | 0,50 / 0,30 | 0,55 / 0,35 | 0,60 / 0,40 |
| `collapse_rise_tau` / `collapse_clear_tau` (min) | 1,5 / 6,0 | 2,0 / 8,0 | 2,2 / 8,0 |
| `impending_burden` / `established_burden` | 0,35 / 0,55 | 0,39 / 0,65 | 0,38 / 0,70 |

Ninguna es una calibración ni está aprobada (`approved = False`, y el instantáneo del testigo lo dice en cada línea).

## 4 · P3-175 · Serie GI en vivo (dos casos, siete escenarios, tres testigos)
Encuentros reales con `pilot_acceptance.Encounter` y la sombra encendida (el motor heredado decide cada minuto). Mismas reglas en ambos
casos, ningún valor por caso. Los dos casos soportados: `gi_bleed_57m` y `gi_bleed_72f`. Resultados en
`docs/revision/PHASE3_GI_AMENDMENT_2_SERIES.json` (14 encuentros; 42 pares escenario×testigo).

| Escenario | Regla (fija) |
|---|---|
| sin tratar | sin órdenes, hasta el minuto 240 |
| tratamiento temprano | acceso, 1 L de cristaloide y 2 U de glóbulos rojos en el minuto 10 |
| tratamiento tardío | el mismo paquete en el minuto 120 |
| centrado en líquidos | 1 L en el minuto 10 y 1 L más en el 40 |
| centrado en sangre | 2 U de glóbulos rojos en el minuto 10 |
| deterioro grave | 1 L de cristaloide cuando el testigo `CENTER_REFERENCE` lee OBNUBILADO por primera vez |
| recuperación tras deterioro grave | cristaloide y 4 U cuando `CENTER_REFERENCE` lee SIN RESPUESTA por primera vez |

**Curso sin tratar (idéntico en ambos casos), minuto en que ocurre cada eslabón:**

| Testigo | entrega < cota | F > 0 | SOMNOLIENTO | OBNUBILADO | SIN RESPUESTA | colapso inminente | colapso establecido |
|---|---|---|---|---|---|---|---|
| LOW | 103 | 105 | 126 | 148 | 175 | 205 | 219 |
| CENTER_REFERENCE | 85 | 88 | 109 | 131 | 157 | 190 | 209 |
| HIGH | 68 | 71 | 92 | 114 | 140 | 172 | 195 |

El volumen ya está por debajo del de llegada desde el minuto 1 en todos los casos y testigos. La anchura de la región (de 140 a 175 para
llegar a SIN RESPUESTA; de 195 a 219 para el colapso establecido) es la incertidumbre que la docencia declaró, no una dispersión por caso.

### P3-175A · Orden causal exigido (medido)
Hemorragia → volumen, perfusión y entrega → F → deterioro observable de la consciencia, y sólo después el colapso. En las **22** corridas
testigo con deterioro observable de las 42: `volumen < entrega < F > 0 < SOMNOLIENTO` en ese orden (22/22); la categoría **nunca salta una banda al subir**
(42/42). En las **10** con colapso inminente (8 con establecido): el colapso llega **después** de la consciencia alterada y el minuto
anterior (o el propio) tenía **entrega y perfusión fallando a la vez** (10/10); ninguna lo hizo por una sola falla. Ninguna
entrada directa de PAS, SpO2, líquidos ni glóbulos rojos alcanza la consciencia: (a) ningún identificador de esos conceptos existe en el
módulo (prueba estática), (b) los dos casos, con PAS distinta a la llegada, leen **la misma** secuencia de categorías, (c) cada mutante
que los reinstala o rompe la cadena es detectado (§8).

### P3-175B · Recuperación (lectura de la docencia, 2026-11-11)
Medida desde el minuto en que la fisiología aguas arriba se recuperó (entrega relativa otra vez sobre su cota normal: la señal que
alimenta a F es cero), no desde la orden: transfundir y reponer tarda minutos en devolver la entrega, y eso es tiempo aguas arriba. F cae
entonces por su ley de primer orden, de modo que 0,80 → por debajo de 0,50 tarda `burden_clear_tau · ln(0,8/0,5)` = **3,0 / 4,0 / 4,9 min** (LOW / CENTER / HIGH),
dentro del 3–5 acordado, y la serie confirma que el cruce observado la sigue.

| Recuperación tras deterioro grave (72f; 57m idéntica) | LOW | CENTER_REFERENCE | HIGH |
|---|---|---|---|
| F al tratar | 0,60 | 0,80 | 0,99 |
| entrega recuperada (min) | 164 | 166 | 168 |
| F en ese momento | 0,37 | 0,50 | 0,62 |
| F < 0,50 (min) | 162 | 167 | 171 |
| minutos desde la entrega recuperada hasta F < 0,50 (observado / por la ley) | 0 / 0,0 | 1 / 0,0 | 3 / 2,3 |
| primer descenso de categoría (min tras el tratamiento) | 5 | 3 | 8 |
| categoría al final | 0 | 0 | 0 |

Del pico a F < 0,50, extremo a extremo (incluida la espera de la fisiología aguas arriba): 5 a 14 minutos desde la orden. **No se exigió
normalizar por debajo de 0,25 en ese intervalo.** Tratamiento tardío (en el 120): sólo HIGH queda con F ≥ 0,50 al tratar (0,58) y baja a
la categoría 0 en el 133; LOW y CENTER nunca superan 0,39 y vuelven al 0 sin llegar a OBNUBILADO. Tratamiento temprano, sólo líquidos y sólo sangre:
sin deterioro observable (F máxima 0,00; 0,06 para HIGH con cristaloide solo). Deterioro grave tratado sólo con cristaloide: **mejoría transitoria** (la
categoría baja y vuelve a subir: CENTER 2 → 1 en el 136 y de nuevo 2 en el 172, 3 en el 193; HIGH colapso establecido en el 232).

## 5 · P3-176 · Escalera heredada frente a la sombra mecanicista (comparación, no calibración)
Se compara la escalera de estado mental del motor heredado con la categoría de cada testigo, minuto a minuto, **sin** ajustar nada para
reproducir los tiempos heredados (el minuto 45 o el 120 de otros paquetes). Sólo se informa lo que difiere y se dejan las preguntas a la docencia.

| Sin tratar | heredado: primera alteración | heredado: secuencia | sombra: primera alteración (LOW / CENTER / HIGH) |
|---|---|---|---|
| `gi_bleed_57m` | 63 (DROWSY) | 63 → 1, 175 → 2 | 126 / 109 / 92 |
| `gi_bleed_72f` | 138 (DROWSY) | 138 → 1 | 126 / 109 / 92 |

Diferencias con valor educativo, todas medidas y ninguna ajustada:
1. **Los dos casos GI leen igual en la sombra** (secuencias de categoría y F idénticas en los 7 escenarios), porque la enmienda lee la
   entrega y la perfusión **relativas a la llegada de cada paciente** (decisión A2-FD-012), mientras que la escalera heredada los separa por PAS
   absoluta: el caso de 57 años (PAS 88 a la llegada) se altera a los 63 min en el heredado, el de 72 a los 138. La sombra altera **antes** que el
   heredado en 72f (92–126 frente a 138) y **después** en 57m (92–126 frente a 63).
2. **La sombra llega a SIN RESPUESTA (140–175 min) sin sedar al heredado**, que a los 240 min sigue en SOMNOLIENTO (72f) u OBNUBILADO (57m, desde el 175).
3. **Reversibilidad**: en la sombra la categoría baja en minutos tras restaurar la entrega (§4); la escalera heredada se observa de nuevo en ALERT
   en la primera muestra tras la orden (minuto 277 en `recovery_after_severe`: la orden corre sobre el reloj síncrono del motor y no hay muestras intermedias).
4. **Colapso**: el heredado nunca pierde el pulso en ninguna serie (0 minutos de contradicción en 14 encuentros); la sombra declara colapso
   inminente a partir del 172–205 y establecido a partir del 195–219 sin tratar, con el paciente heredado todavía activo (§7).
Limitación de la medida: durante la ejecución de una orden (una infusión corre 20–60 minutos en el reloj del motor) el valor heredado se
muestrea sólo al final, de modo que la comparación cubre los minutos muestreados (`minutes_compared` por testigo, en el registro).

## 6 · P3-177 · Paquete de revisión docente
Generado con las herramientas existentes de persistencia y observador (`runtime_shadow_observer.write_review_package`), fuera del
repositorio (sólo datos de ejecución) y sin acceso del residente: `test_gi_amendment_2_series.write_faculty_bundle(destino_absoluto)`.
Cuatro trayectorias representativas: 72f sin tratar, 57m deterioro grave con cristaloide solo, 72f tratamiento tardío, 57m recuperación tras
deterioro grave. Cada página muestra: la línea de tiempo de acciones, V / presión / entrega / perfusión / F / carga de colapso / categoría con
**los tres testigos separados** (y la corrida comprometida al lado), el estado de réplica (las cuatro **reproducen exactamente**), la región y
su procedencia, la frontera con el motor heredado y las preguntas. `legacy_beside_shadow.md` pone la escalera heredada **sólo como comparación**.
Preguntas a la docencia (juicio, no implementación): ¿la alteración aparece demasiado pronto o tarde (como dirección, no como velocidad)?; ¿la
recuperación es demasiado rápida o lenta una vez restaurada la entrega (3–5 min desde la fisiología aguas arriba) y debe contarse desde la
orden o desde la recuperación aguas arriba?; ¿la progresión de categorías es plausible paso a paso?; ¿el colapso aparece demasiado pronto o
tarde y es correcto que exija perfusión y entrega fallando a la vez?; ¿es aceptable que los dos casos lean igual en la sombra mientras el
heredado los separa por PAS absoluta?; ¿está claro en la traza que un colapso establecido es estado fisiológico y no un desenlace?;
¿alguna trayectoria confundiría a un residente?

## 7 · P3-178 · Frontera y estado explícito del colapso junto al motor heredado
**Frontera conocida (`UnresolvedBoundary`: gasto efectivo cero con pulso y sin regla terminal declarada).** Sin tratar, sesión y los tres
testigos la tocan **en el mismo minuto (349) en ambos casos**: la enmienda **no la mueve** (la física compartida es idéntica con y sin ella) y
tampoco la corrige: el núcleo no se tocó y la terminalización no está autorizada. En ese minuto cada corrida registra su falla
(`core` y `ensemble:<testigo>:core`, `COMMON_BOUNDARY`) y el estado de la traza es `FAILED` con la sesión parcial, nunca un éxito silencioso.
**Estado explícito** (`terminal_boundary.amendment_2`, recalculado en `verify` para que nadie lo edite aparte de sus dos lados): por testigo,
`COLLAPSE_ESTABLISHED_LEGACY_ACTIVE`, `COLLAPSE_IMPENDING_LEGACY_ACTIVE`, `NO_COLLAPSE_LEGACY_ACTIVE`, `LEGACY_TERMINAL_COLLAPSE_ESTABLISHED`,
`LEGACY_TERMINAL_WITHOUT_ESTABLISHED_COLLAPSE` (el motor termina por otra razón) y `WITNESS_NOT_COMPARABLE`. Sin tratar, del
minuto 219 al 348 los tres testigos están en `COLLAPSE_ESTABLISHED_LEGACY_ACTIVE` (HIGH desde el 195) con el heredado activo, con pulso y sin arresto: **cada uno lo declara**.
Nota fija: *estado fisiológico sólo; un colapso establecido no termina, bloquea ni altera el encuentro, que decide únicamente el motor heredado*.

## 8 · P3-179 · Certificación integrada
* **Pruebas focalizadas nuevas:** `test_phase3_amendment_2_integration.py` (8), `test_phase3_gi_amendment_2_shadow.py` (23),
  `test_phase3_gi_amendment_2_mutants.py` (8); mutantes del núcleo ampliados a 16 (`f_is_inert`, `direct_pressure_ladder_in_the_level`,
  `direct_saturation_ladder_in_the_level` nuevos).
* **Mutantes que deben ser detectados:** F inerte, F instantánea, escalera directa de PAS, escalera directa de SpO2, colapso por máximo (OR) y F que
  limpia tan rápido como sube (seis, por las pruebas de la capa integrada); testigo elegido, enmienda fuera de GI, autoridad encendida,
  réplica que no reproduce, la sombra que escribe en el paciente (cinco, por la capa); linaje no certificado y núcleo de otra versión (dos,
  por las compuertas del conjunto). Control sin mutante: verde.
* **Suite completa del núcleo común:** `ALREADY_VALID_ON_EQUIVALENT_CODE`. `clinical_core/` es byte a byte el del candidato certificado `ad7bf81`
  (`git diff ad7bf81 HEAD -- clinical_core` vacío; digesto `a0af7d08…`), y 442 de los 462 archivos de prueba son idénticos a los de ese candidato (la
  certificación de la Enmienda 2 corrió 11 359 pruebas, 0 fallas). Lo que difiere es la capa de la Fase 3 y sus pruebas, que sí se corrieron.
* **Certificación integrada (una, repetida una vez porque el candidato cambió):** 58 archivos de prueba (los 20 que difieren del candidato certificado,
  los que importan la capa de sombra o de autoridad, los de la Enmienda y el cierre, y los que leen el linaje), Python 3.11.17, 4 particiones, candidato
  `faf643e`, huella inicial = final, sin cambios sin commit. **Primera corrida** (`3e6b334`): 2475 pruebas, **6 fallas, todas regresiones propias** de este
  cambio en guardas de aislamiento (5 por un módulo de análisis en la raíz que lee almacén, observador y núcleo, donde sólo pueden hacerlo los módulos
  declarados de la capa; 1 por el literal «encephalopathy» en el observador). Corregidas sin relajar ninguna guarda (el módulo pasó a ser código de
  pruebas, `test_gi_amendment_2_series.py`; el observador toma el nombre del canal de la familia). **Segunda corrida** (`faf643e`): **2475 pruebas, 0 fallas, 0
  errores, 0 omitidas, válida.** Regresiones: 56/56 activas, 10 retiradas. Mutantes del núcleo (16) y de la capa (6 de fisiología + 7 de la capa): todos detectados.
* **No se corrió** la suite completa del repositorio (≈ 11 k pruebas, ≈ 2 h por partición lenta): innecesaria por equivalencia de código del núcleo y por
  no haber cambios en `app.py`, el motor heredado, la puntuación ni el primer piloto.

## 9 · P3-180 · Punto de control de preparación (sólo GI)
No se autoriza autoridad ni despliegue. Tres lecturas separadas:

| Lectura | Veredicto | Por qué |
|---|---|---|
| `SIMULATION_ENGINE_READINESS` | **`SHADOW_ENGINE_READY_FOR_FACULTY_REVIEW`**, no para autoridad | La Enmienda 2 certificada corre en vivo en la sombra GI, sin tocar nada visible; orden causal, recuperación y colapso coherentes en 14 encuentros; réplica exacta; mutantes detectados. Falta la terminalización desde el núcleo (frontera de gasto cero con pulso, minuto 349) y la autoridad. |
| `FACULTY_TRACE_REVIEW_READINESS` | **`READY`** | Paquete de cuatro trayectorias con testigos separados, réplica exacta, estado explícito del colapso junto al motor heredado y preguntas de juicio (§6). Se regenera con `test_gi_amendment_2_series.write_faculty_bundle`; vive fuera del repositorio. |
| `RESIDENT_PILOT_REVIEW_READINESS` | **`NOT_READY_FOR_RESIDENT_PILOT_REVIEW`** | Bloqueos abajo. |

**Bloqueos para la revisión de piloto con residentes, en orden:**
1. Respuestas docentes a las siete preguntas del paquete (inicio, recuperación, progresión de categorías, colapso, lectura relativa, frontera, riesgo de confundir al residente).
2. **Lectura relativa a la llegada**: los dos casos GI leen igual en la sombra y el heredado los separa por PAS absoluta. La docencia debe decir cuál es la intención educativa.
3. **Cuándo cuenta la recuperación de 3–5 min**: desde la recuperación aguas arriba (como se midió) o desde la orden (5–14 min con infusiones de 20–60 min).
4. **Frontera terminal**: `UnresolvedBoundary` (gasto cero con pulso) y la regla que termina un encuentro (el núcleo determina el estado, el runtime termina) siguen sin autorizarse.
5. **Instantánea de parámetros aprobada**: toda magnitud es región de desarrollo; ninguna está aprobada ni validada clínicamente.
6. **Decisión de autoridad y de exposición** (qué vería el residente, si algo) y el diseño de cara al residente.
7. Coste de cuatro corridas por turno en vivo (no medido bajo carga) y generación del paquete como paso manual.
8. Mecanismo de consciencia del opioide: diferido (otra familia).

**Paso más corto siguiente:** revisión docente del paquete de trazas (sin código), con las respuestas a las preguntas 1 a 3, que deciden si la Enmienda 2 necesita un ajuste de región antes de pedir una instantánea aprobada.

**Continuación (2026-11-11).** La docencia respondió a los bloqueos 2 y 3 (FD-GI-01 y FD-GI-02). La revisión exacta de la temporalidad de la
recuperación, su veredicto y la única pregunta que queda están en `docs/PHASE3_GI_RECOVERY_CALIBRATION_REVIEW.md` (filas FD-P3-173 a FD-P3-177). La docencia aprobó la recuperación graduada sin cambio del núcleo (FD-P3-177) y la región GI de desarrollo
quedó **lista para la selección de una instantánea**; el bloqueo 3 queda respondido. Este registro no se reescribe.
