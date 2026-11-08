# Fase 3 · P3-31 a P3-37 · Ciclo de evidencia previo a la autoridad

Sólo lectura y cómputo. **No aprueba ninguna instantánea, no concede autoridad, no cambia la fisiología que
ve el residente, no cambia la puntuación, no cambia el piloto y no toca la fisiología congelada de la
Fase 2.** `APPROVED_SNAPSHOTS` sigue vacío y `COMMON_CORE_RUNTIME_AUTHORITY` sigue en `False`.

Rama `phase-3-runtime-integration`, desde `f6b8408`. Cierre de la Fase 2: `d2cca46`, digesto
`22b90a6f…6ce6a`, sin cambios. Candidatos sobrevivientes: `gi_pressure_committed` y
`gi_pressure_preload_high`, los que P3-22C dejó en pie.

Todo lo numérico de aquí se midió esta noche con el núcleo congelado, replayando los artefactos inmutables
de los 34 escenarios GI certificados. Ninguna cifra se ajustó contra el legado y ninguna tolerancia clínica
se inventó.

## 1 · Qué puede mover la presión, de verdad (P3-31-2 y P3-31-3)

La instantánea docente nombra **siete** magnitudes. Medí cada una moviéndola sola a los dos extremos de su
región declarada, en los 34 escenarios, y comparando la trayectoria completa de SBP, DBP y MAP contra la
del candidato.

| Magnitud | Dependencia | Identificabilidad | Máx. \|ΔSBP\| en GI | Escenarios movidos |
|---|---|---|---|---|
| `arrival_preload_fraction` | `DIRECTLY_ACTIVE` · `COMMON_SHARED` | `IDENTIFIABLE_FROM_GI` | **62,802 mmHg** | 34/34 |
| `preload_curve_scale_ml` | `DIRECTLY_ACTIVE` · `COMMON_SHARED` | `IDENTIFIABLE_FROM_GI` | **33,673 mmHg** | 34/34 |
| `afterload_sensitivity` | `CONDITIONALLY_ACTIVE` · `COMMON_SHARED` | `CONSTRAINED_ONLY_BY_OTHER_FAMILIES` | 0,000 | 0/34 |
| `pump_preload_coupling` | `CONDITIONALLY_ACTIVE` en teoría · `COMMON_SHARED` | `STRUCTURALLY_UNIDENTIFIABLE_IN_CURRENT_DATA` | 0,000 | 0/34 |
| `low_output_pressure_knee` | `NOT_READ` desde P2J-1 | `STRUCTURALLY_UNIDENTIFIABLE` | 0,000 | 0/34 |
| `sbp_per_pressure_deficit` | `NOT_READ` desde P2J-1 | `STRUCTURALLY_UNIDENTIFIABLE` | 0,000 | 0/34 |
| `dbp_per_pressure_deficit` | `NOT_READ` desde P2J-1 | `STRUCTURALLY_UNIDENTIFIABLE` | 0,000 | 0/34 |

**El «cinco inertes» de P3-30 era cierto pero impreciso.** El por qué, término por término, desde la
ecuación vigente (`clinical_core/pressure_tone.py::EQUATIONS`, desde P2J-1):

```
SBP = SBP_llegada · max(0, p)      DBP = DBP_llegada · max(0, p)      MAP = (SBP + 2·DBP)/3
p   = Q · T
Q   = P · (factor del ritmo) · preload_rel · 1/(1 + a·(T − 1))
preload_rel = posición(V) / posición(0)  sobre  1 − exp(−x / (escala · P^c))
```

- **Las dos activas** entran en `preload_rel` y sólo actúan **a través del cambio de volumen**: son el
  reservorio efectivo del paciente. GI es la única familia certificada que mueve V (sangrado, cristaloide,
  sangre).
- **`afterload_sensitivity` (a)** entra sólo como `1/(1 + a·(T − 1))`. En GI el tono vascular **T ≡ 1**:
  lo verifiqué en los **1638 minutos** de los 34 escenarios, donde `pressure_rel == output_rel` **exacta­mente**,
  sin una sola excepción. Con T = 1 el término se multiplica por cero. En ACS y en TEP, donde T ≠ 1, **sí
  actúa**: mover a de 0,3 a 0,1 y a 0,5 cambia la SBP final en +0,287 / −0,335 mmHg (ACS) y +0,339 / −0,394
  (TEP). En edema pulmonar no actúa (T ≡ 1 también).
- **`pump_preload_coupling` (c)** entra sólo como `escala · P^c`. En GI **P ≡ 1,0** (un único valor en los
  34 escenarios, leído dentro de `derived.preload_position`), así que `1^c = 1` para cualquier c. Fuera de
  GI, donde ACS y TEP sí deprimen el pump (P ≈ 0,95), **V ≡ 0,0**, así que `preload_rel = posición(0)/posición(0) = 1`
  y la escala se cancela en el cociente. Hacen falta **a la vez** un pump deprimido y un cambio de volumen,
  y **ninguna familia certificada tiene las dos cosas**. De ahí `STRUCTURALLY_UNIDENTIFIABLE_IN_CURRENT_DATA`.
- **Las tres últimas no están en la ecuación.** La relación lineal con rodilla se retiró en P2J-1. Hoy:
  `dbp_per_pressure_deficit` no se lee en ninguna parte fuera del registro; `sbp_per_pressure_deficit` se
  lee en un único sitio, `clinical_core/shadow.py:243`, para **reconstruir la SBP cruda del motor legado**
  al atribuir una discrepancia de nivel de consciencia —diagnóstico, no fisiología del núcleo—;
  `low_output_pressure_knee` se lee en una **guarda de admisibilidad** (`derived.py:268`: `0 < rodilla < 1`,
  si no, el perfil se rechaza) y en una sonda de auditoría. Es decir: su valor importa para que la
  instantánea sea admisible, no para lo que pasa con la presión.

**Consecuencia para la decisión A:** la instantánea nombra siete valores, de los cuales **dos** determinan
el experimento GI, **uno** (`afterload_sensitivity`) afecta la sombra de ACS y TEP sin que GI pueda verlo,
**uno** no es identificable por construcción con los datos actuales, y **tres** no se leen. Esto debe ir
dicho en la autorización, no supuesto.

## 2 · Geometría (P3-31-5)

Posición normalizada en la región declarada y distancia al borde más cercano.

| Magnitud | `gi_pressure_committed` | pos. | dist. | `gi_pressure_preload_high` | pos. | dist. |
|---|---|---|---|---|---|---|
| `preload_curve_scale_ml` (600–1500) | 833,33… | 0,259 | 0,259 | **1500** | 1,000 | **0,000** |
| `arrival_preload_fraction` (0,3–0,7) | 0,5 | 0,500 | 0,500 | **0,7** | 1,000 | **0,000** |
| `pump_preload_coupling` (0,0–1,0) | **1,0** | 1,000 | **0,000** | **1,0** | 1,000 | **0,000** |
| `afterload_sensitivity` (0,1–0,5) | 0,3 | 0,500 | 0,500 | 0,3 | 0,500 | 0,500 |
| `low_output_pressure_knee` (0,3–0,6) | 0,5 | 0,667 | 0,333 | 0,5 | 0,667 | 0,333 |
| `sbp_per_pressure_deficit` (35–55) | 45 | 0,500 | 0,500 | 45 | 0,500 | 0,500 |
| `dbp_per_pressure_deficit` (15–30) | 25 | 0,667 | 0,333 | 25 | 0,667 | 0,333 |

- **Ninguno de los dos es interior estricto en las siete dimensiones**, porque `pump_preload_coupling = 1,0`
  está exactamente sobre el tope de su región en ambos. Esa dimensión es demostrablemente inerte hoy
  (§1), así que el borde no tiene consecuencia fisiológica; pero «interior» era una afirmación incompleta
  en P3-30 y queda corregida.
- En las **dos dimensiones que sí actúan**: `committed` es interior (distancias 0,259 y 0,500);
  `preload_high` está sobre el borde en las dos (distancia 0,000).
- Dimensiones en el borde: **1 de 7** en `committed`, **3 de 7** en `preload_high`.
- El punto comprometido coincide con el midpoint declarado en 6 de las 7 magnitudes; la excepción es
  `pump_preload_coupling` (canónico 1,0, midpoint 0,5).

## 3 · Sensibilidad local (P3-31-6)

Pasos de ±5 % y ±10 % del ancho admisible, una magnitud a la vez, sobre 8 clases de escenario × 2 casos
(16 corridas por fila). Los pasos que **salen** de la región se reportan como inadmisibles en vez de
recortarse: recortar esconde la asimetría.

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| ±5 % en las dos activas | 4 de 4 pasos admisibles; máx. ΔSBP final **5,519 mmHg** | 2 de 4 admisibles (sólo hacia dentro); máx. **1,368** |
| ±10 % en las dos activas | 4 de 4 admisibles; máx. ΔSBP final **11,518 mmHg** | 2 de 4 admisibles; máx. **2,819** |
| Las cinco restantes, ±5 % y ±10 % | ΔSBP = 0,000 en las 16 corridas de cada paso | igual |
| Pareado ±10 % de las dos activas (4 esquinas) | **4 de 4 esquinas admisibles**, las 4 `PLAUSIBLE_INTERIOR_TRAJECTORY` en 16/16 | **1 de 4 admisible**, `PLAUSIBLE` en 16/16 |
| Clasificaciones observadas | ninguna `PARADOXICAL_RESPONSE`, ninguna `UNRESOLVED_BOUNDARY` | igual |

Las dos activas interactúan de forma mecánicamente posible (ambas entran en `preload_rel`), que es la razón
declarada para hacer el pareado y no un barrido cartesiano.

Lectura: `preload_high` es **cuatro veces menos sensible**, y la mitad de las direcciones de perturbación
no se pueden ni mirar porque salen de la región. «No encontré frontera» significa distinto en cada
candidato.

## 4 · Frontera de robustez y núcleo robusto (P3-32)

Cada magnitud activa recorrida sola por siete posiciones de su región, y después una bisección al primer
`UnresolvedBoundary` en el escenario de 240 minutos.

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| `arrival_preload_fraction` hacia abajo | frontera a **0,4033**; margen **24,2 %** del ancho | **sin frontera en toda la región** |
| `preload_curve_scale_ml` hacia abajo | frontera a **620,71**; margen **23,6 %** | **sin frontera** |
| Hacia arriba, las dos | sin frontera | sin frontera |
| Dónde aparece | sólo en `terminal_deterioration` (240 min), minutos 152–237 según la posición | — |
| Núcleo robusto conjunto (rejilla 2D hacia abajo, pasos de 0 a 0,30 del ancho) | triángulo: limpio hasta (0,10 / 0,10); frontera en (0,15 / 0,15) y en (0,20 / 0,05) | **limpio en los 49 puntos muestreados** |

El núcleo robusto conjunto es **menor** que el margen de una sola dirección: la interacción cuenta. Para
`committed`, el margen efectivo cae de ~24 % (una dirección) a ~14 % (las dos a la vez). Para
`preload_high` no hay frontera alcanzable ni de una en una ni en pareja.

Esto **no** establece ninguna región nueva aprobada: describe lo que hace el núcleo congelado.

## 5 · Horizonte largo y plausibilidad causal (P3-33)

Las ocho clases se tomaron de la verdad del repositorio, sin inventar ninguna magnitud clínica:
`C_omission` (sin tratar), `B_delayed_management` (paquete al minuto 30), `E_excessive_treatment`
(cristaloide ×3), `A_correct_management` (paquete con sangre), `G_duplicate_treatment` (sólo control del
sangrado), `I_waiting` (observación), `K_combined_interventions` (reanimación combinada) y
`terminal_deterioration` (240 min). **No existe un curso de sangre aislada**: la sangre sólo aparece dentro
del paquete, así que su efecto no es separable y queda declarado como límite.

| Clase (caso 57m) | `committed` SBP₁ → final | `preload_high` SBP₁ → final | dirección |
|---|---|---|---|
| sin tratar (60 min) | 87,7 → **72,6** | 87,9 → **84,5** | ↓ ambos |
| tratamiento retardado | 87,7 → 111,5 (mín. 80,2 al min 30) | 87,9 → 94,0 (mín. 86,2) | ↓ y después ↑ |
| cristaloide ×3 (30 min) | 88,4 → 95,1 | 88,1 → 89,7 | ↑ ambos |
| paquete con sangre (60 min) | 89,5 → **130,3** | 88,4 → **99,5** | ↑ ambos |
| sólo control del sangrado | 87,8 → 85,9 | 88,0 → 87,5 | ↓ más lento |
| observación (20 min) | 87,7 → 82,8 | 87,9 → 86,8 | ↓ ambos |
| reanimación combinada | 89,5 → 106,9 | 88,4 → 92,7 | ↑ ambos |
| **deterioro terminal (240 min)** | 87,7 → **28,5**; 210 min <80; **150 min <65** | 87,9 → **75,5**; 94 min <80; **0 min <65** |  |

En el caso 72f el deterioro terminal termina en **31,8** con `committed` (177 min <80, 122 <65) y en
**84,0** con `preload_high`, que **nunca baja de 80**. Los umbrales 80 y 65 son los del propio repositorio
(`family_engine._PRESSURE_LEVELS`, magnitud adoptada del legado), no cortes que yo haya inventado.

**Preocupación estructural de `preload_high`:** dentro de su propio horizonte certificado, el escenario
llamado `terminal_deterioration` **no deteriora** hasta ningún nivel que el modelo declare relevante para
la consciencia. En uno de los dos casos no cruza ni el primer umbral.

### 5.1 Dirección causal, término por término

| Pregunta | Resultado |
|---|---|
| ¿El sangrado no tratado empeora la presión? | Sí: caída monótona, 0 subidas en 59 minutos, en los dos candidatos y los dos casos |
| ¿El volumen mejora la presión en la dirección correcta? | Sí: signo **+** en cristaloide, sangre y paquete combinado, 100 % de las corridas |
| ¿La sangre se comporta de forma coherente? | Sí dentro del paquete; **no es separable** (límite declarado) |
| ¿El control del sangrado frena la pérdida? | Sí y **cuantitativamente exacto**: pendiente sin tratar −0,2629 mmHg/min contra −0,2096 con PPI (razón **0,797**); en 72f −0,2928 contra −0,2334 (**0,797**); con `preload_high` −0,0621/−0,0496 (**0,799**) y −0,0692/−0,0553 (**0,799**). El contribuidor declara `fraction_with_ppi = 0,8`: la pendiente cae al 80 %, que es exactamente lo declarado |
| ¿El efecto llega **después** de la acción? | Sí, y de forma estricta: ver §5.2 |
| ¿La espera avanza la fisiología de forma monótona? | Sí en observación y en sangrado no tratado |
| ¿Alguna intervención produce una dirección paradójica? | **Ninguna** `PARADOXICAL_RESPONSE` en ninguna de las ~1 300 corridas de este ciclo |
| ¿El sobrepaso viene de un borde de parámetro? | No. Ver §5.3 |

### 5.2 Orden temporal (P3-33-2)

El paquete de tratamiento retardado se entrega al minuto 30. Comparando esa trayectoria con la del curso
**sin tratar**:

| | `committed` | `preload_high` |
|---|---|---|
| minutos 1–30 idénticos al curso sin tratar | **sí**, bit a bit, los dos casos | **sí**, los dos casos |
| primera divergencia del curso retardado | **minuto 31** | **minuto 31** |
| primera divergencia del paquete inmediato (minuto 0) | **minuto 1** | **minuto 1** |

Ninguna respuesta antes de la acción, ningún efecto antes de la activación, y la divergencia aparece en el
primer minuto posterior. Es la comprobación más limpia de `causa → estado → presión` que permiten los
escenarios certificados.

### 5.3 Sobrepaso: es propiedad declarada del modelo, no de un candidato

El paquete estándar (1 L + sangre + PPI) lleva la SBP por encima del ancla en los dos candidatos:
`p` máximo **1,4806** con `committed` (SBP 130,3 en 57m; 145,1 en 72f) y **1,1307** con `preload_high`
(99,5 y 110,8). El modelo **no tiene techo** por declaración explícita
(`pressure_tone.FLOORS_CAPS_KNEES["since_p2j1"]`: «no knee, no floor, no cap»).

La envolvente que el propio repositorio ya tenía registrada para el minuto 60 de ese curso en 57m dice:
región de SBP **[99,506 – 210,673]** con tres testigos, valor estructural **130,295**, legado **117**,
estado `LEGACY_WITHIN_COMMON_REGION`. Es decir: el motor legado **también** sube de 88 a 117 con ese
paquete, los dos candidatos caen dentro de la envolvente declarada, y `preload_high` coincide con su
**borde inferior**. Dejo las tres cifras como contexto declarado: **no las uso como criterio**, porque
«acercarse al legado» está prohibido como criterio de selección.

### 5.4 Veredicto de P3-33

| Candidato | Veredicto |
|---|---|
| `gi_pressure_committed` | `COHERENT_WITH_DECLARED_LIMITATION` — coherente en las ocho clases; límites: la sangre no es separable, y el margen conjunto a la frontera es ~14 % del ancho |
| `gi_pressure_preload_high` | `LONG_HORIZON_STRUCTURAL_CONCERN` — coherente en dirección y en orden temporal, pero el escenario de deterioro terminal no deteriora dentro de su horizonte certificado |

## 6 · Entre familias (P3-35)

Los 10 casos certificados de las 6 familias de la Fase 2, replayados 30 minutos con los valores del
candidato aplicados al perfil común.

| Familia / caso | admisión | SBP base | `committed` | `preload_high` |
|---|---|---|---|---|
| acs / acs_70f_left_main | ADMITTED | 104,0 → 100,3 | `NO_INFORMATION` | `NO_INFORMATION` |
| asthma / asthma_24f, asthma_49m | ADMITTED | 138,0 → 138,0 / 142,0 → 142,0 | `NO_INFORMATION` | `NO_INFORMATION` |
| gi_bleed / 57m, 72f | ADMITTED | 88,0 → 80,2 / 98,0 → 89,3 | `NO_INFORMATION` (es la base) | `WEAK_TENSION` (+5,982 / +6,662) |
| opioid / opioid_35m, opioid_67f | ADMITTED | 106,0 / 104,0 sin cambio | `NO_INFORMATION` | `NO_INFORMATION` |
| pulmonary_edema / 58m | ADMITTED | 218,0 → 218,0 | `NO_INFORMATION` | `NO_INFORMATION` |
| pulmonary_embolism / 61m, 33f | ADMITTED | 86,0 → 83,4 / 110,0 → 104,5 | `NO_INFORMATION` | `NO_INFORMATION` |

Cero `CONTRADICTION`, cero fronteras nuevas, cero reversiones de comportamiento certificado, cero
invariantes violados. Y cero apoyo: **ninguna otra familia restringe las dos magnitudes activas**, porque
V ≡ 0 fuera de GI (§1). La única magnitud de la instantánea que otras familias **sí** restringen es
`afterload_sensitivity`, con una huella de ≤0,4 mmHg en ACS y TEP.

**Veredicto de P3-35:** ningún candidato tiene una razón entre familias para ser rechazado, y ninguno tiene
una razón entre familias para ser preferido.

## 7 · Simulacro de la tubería completa (P3-34)

Con el mecanismo de aprobación **sólo-pruebas** ya certificado (una entrada en el registro privado que vive
en un proceso y muere con él), entorno `development`, almacén en un directorio temporal fuera del
repositorio, y el piloto apagado.

### 7.1 Candidato 1, `gi_pressure_committed`: completo

| Paso | Resultado |
|---|---|
| Escenarios GI | **34**: **26 `TECHNICALLY_VALID`**, **8 `NOT_ELIGIBLE`** (los bloquea una acción sin semántica común, no la fisiología) |
| Compromiso atómico | **26 de 26** |
| Contrafáctico legado capturado | **26 de 26** |
| Replay exacto del minuto | **26 de 26** |
| Artefactos persistidos y recuperados | **26 de 26** |
| Digesto verificado e identidad coincidente | **26 de 26** |
| Replay desde el archivo | **26 de 26**, veredicto «every committed minute reproduces» |
| Completitud del artefacto | **30 de 30** campos de cabecera, **20 de 20** por minuto |
| Coste | 38,7 s la batería completa |

### 7.2 Candidato 2, `gi_pressure_preload_high`: la fisiología sí, la composición no

Dos resultados nuevos:

1. **Equivalencia con un punto ya certificado.** En los **34** escenarios GI, `gi_pressure_preload_high`
   produce trayectorias de SBP **idénticas bit a bit** a las del testigo de región `upper` completo
   (las siete magnitudes en su tope), porque las otras cinco son inertes en GI. Es decir: el candidato 2 es,
   en lo que a presión GI respecta, el testigo `gi_region_upper` que la Fase 2 ya certificó.
2. **No es alcanzable en vivo con el código actual.** `ShadowSession.start` abre
   `ShadowPhysiologyRunner.open(familia, caso, state=…, scenario_id=…)` **sin** argumento `point`, así que
   el único punto que la aplicación puede correr es `committed_default`, que **es** el candidato 1. Y
   `runtime_shadow_evidence._play_battery(variant, mode)` tampoco acepta un punto, así que la batería no
   puede conducir la transacción sobre esa fisiología.

Por eso **detuve este subpaquete en vez de escribir código**, como pide el encargo. Lo que falta no es un
comportamiento desconocido: es una **composición no ejercida** (transacción × fisiología `upper`). La
transacción es independiente del candidato por construcción, y la fisiología del candidato 2 está ejercida
en los 34 escenarios por P3-22C y por la prueba N4 de la certificación. Pero no lo ejercí junto, y no lo
afirmo.

### 7.3 Un enlace que hay que mirar antes de aprobar el candidato 2

`snapshot_is_wellformed` exige que `runtime_parameter_snapshot_id` de la aprobación sea el punto que la capa
de sombra corrió, y lo compara contra `runtime_shadow.PARAMETER_SNAPSHOT_ID`, que es un **literal de módulo**
(`"phase2_committed_default_profile"`), no una función del punto que el runner abrió. Hoy eso es exacto,
porque producción sólo puede abrir el punto comprometido. **Deja de serlo en el momento en que un punto
distinto sea ejecutable en vivo:** la novena condición de la compuerta quedaría vacía justo para el
candidato 2. Es deuda técnica nueva, no un fallo actual.

### 7.4 Rutas de fallo y aislamiento posterior (P3-34-4 y P3-34-5)

Las rutas de fallo —acción no soportada, frontera, instantánea inválida, entorno equivocado, piloto,
digesto distinto, configuración cambiada y excepción interna— están cubiertas por la certificación de P3-28
sobre este mismo HEAD y con las mismas entradas. Las volví a correr una vez como confirmación:
**196 aprobadas en 132,8 s** sobre `test_runtime_authority.py`, `…_site.py`, `…_surface.py`,
`…_certification.py`, `…_e2e.py` y `…_battery.py`.

Después del simulacro, con la aprobación retirada: `APPROVED_SNAPSHOTS` = `{}`, registro privado = `{}`,
almacén sin configurar, bandera de autoridad ausente del entorno, y `unreachable_because()` devuelve
«APPROVED_SNAPSHOTS is empty: no faculty-approved authority snapshot exists».

**Veredicto de P3-34:** `DRY_RUN_PIPELINE_READY_FOR_CANDIDATE_1`; para el candidato 2,
`BLOCKED_BY_MISSING_POINT_SELECTION` (no por la fisiología, que corre y replayea).

## 8 · Separación piloto / producción (P3-37)

| Comprobación | Resultado |
|---|---|
| Entorno limpio | no abre sitio; almacén sin configurar; sombra `off`; motivo declarado |
| Entorno «lo mejor posible» (todas las banderas puestas) | **no concede**: la única condición que falla es `approved_snapshot` |
| Piloto por bandera explícita (`MRS_PILOT`, `MRS_PILOT_RESIDENTS`) | `no_pilot` **falla** → rechazo |
| Piloto por sus propias marcas de despliegue (`MRS_OFFLINE_CASES` + `MRS_IMAGE_REQUIRE_REVIEW`, leídas de `pilot_freeze`) | `no_pilot` **falla** → rechazo |
| Si la congelación del piloto no se puede leer | **falla cerrado**: se asume piloto |
| Entornos aceptados | sólo `development` y `faculty` (y su variante en mayúsculas); `production`, `prod`, `staging` y sin fijar **rechazan** |
| Bandera de autoridad nombrada en los secretos de Streamlit | **no se honra**: la condición `authority_flag` falla y el motivo se declara |
| Almacén dentro del repositorio o en ruta relativa | **rechazado** con su motivo: «an artifact store must be an absolute path outside the repository» |
| Puntuación y rúbricas | sin alcance: probado por AST en N2 y N3 de la certificación; un minuto de autoridad no mueve ningún dato de puntuación |
| Lo que ve el residente | nada: la superficie está detrás de `faculty_access()` y `RESIDENT_READERS_FORBIDDEN` tiene prueba por AST |
| Conjunto de investigación | el almacén es una superficie separada, de crear-sólo, fuera del esquema congelado; sus registros no llevan valores clínicos |

**Veredicto de P3-37:** `DEVELOPMENT_AUTHORITY_EXPERIMENT_ISOLATED`.

## 9 · Revisión adversarial de la evidencia (P3-36)

Ataqué cada conclusión de este ciclo, incluidas las mías.

| Ataque | Marca | Por qué |
|---|---|---|
| Ajuste accidental contra el legado | `ROBUST` | El criterio nunca estuvo disponible: `legacy_final` del escenario terminal no lleva presiones (sólo minuto, `arrested: false` y un digesto). Las tres cifras de la envolvente (§5.3) se reportan y **no** se usan como criterio |
| La procedencia de `committed` es «el punto comprometido» | `WEAK` | Es el punto con el que se produjo todo artefacto certificado de la Fase 2, y ese trabajo incluyó comparación con el legado. La ventaja de procedencia hereda esa influencia: es parcialmente circular |
| Preferencia encubierta por el midpoint | `WEAK` | `committed` **es** el midpoint declarado en 6 de 7 magnitudes. Lo que lo separa de «preferir el medio» no es la geometría, es que es el único punto que producción puede correr (§7.2) |
| Geometría de región confundida con validez clínica | `UNSUPPORTED` como lectura clínica | Las regiones son tramos **declarados**, con estado `CANDIDATE`; 0 de 58 entradas del registro son `FACULTY_APPROVED`. La geometría dice cuánto espacio hay, nunca si está bien |
| Magnitudes débiles presentadas como respaldadas | `ROBUST` tras la corrección de §1 | Ninguna de las cinco no activas queda respaldada; `afterload_sensitivity` sólo tiene una huella de ≤0,4 mmHg en dos familias |
| Inferencia de GI a fisiología común | `WEAK` | Las dos activas son comunes (`per_case: false`) pero sólo GI mueve V, así que sólo GI las ve. El `NO_INFORMATION` entre familias **no es apoyo**: es ausencia de contradicción |
| Rango de sensibilidad demasiado estrecho | `ROBUST` en las dos activas | No me quedé en ±10 %: recorrí la región completa, hice una rejilla 2D hasta el 30 % del ancho y bisecté la frontera. Lo estrecho no es el rango: es que sólo dos magnitudes se pueden variar informativamente |
| Los casos de estrés no estresan | `ROBUST`, y corta contra `preload_high` | Con `preload_high` el escenario terminal termina en 75,5 / 84,0 y no cruza el umbral declarado de 65 en ninguno de los dos casos. Con `committed` llega a 28,5 / 31,8 |
| La ventaja de un candidato viene de un mecanismo desactivado | `WEAK` para **las dos** ventajas geométricas | La robustez de `preload_high` es la robustez de un modelo **menos** responsivo: está lejos de la zona empinada de la curva de precarga, y la responsividad es justo el mecanismo bajo prueba. Simétricamente, la evidencia de dos lados de `committed` viene de un interior cuyo ancho fue **declarado**, no medido |
| Comparación que usa resultados no disponibles al decidir | `ROBUST` | Todo lo medido es calculable antes de cualquier corrida con autoridad: geometría, replay del núcleo congelado y simulacro de la tubería |
| Uso circular de las pruebas de autoridad como validación de fisiología | `CIRCULAR` si se lee así; `ROBUST` como validación de software | Los 26/26 compromisos y 26/26 replays dicen que la **tubería** funciona. No dicen nada sobre si las presiones comprometidas son correctas |

### 9.1 Qué sobrevive

Después de los ataques, **dos** argumentos quedan `ROBUST`, y los dos favorecen a `gi_pressure_committed`:

1. **Es el único punto que producción puede correr hoy** sin cambiar código en la capa de la Fase 3
   (§7.2). Hecho verificable, no juicio.
2. **Es el único candidato con el que el escenario certificado de deterioro terminal deteriora** dentro de
   su propio horizonte, usando los umbrales que el propio repositorio declara (§5).

Todos los argumentos geométricos de los dos lados bajan a `WEAK`. La ventaja de margen de frontera de
`preload_high` baja a `WEAK` por la razón del mecanismo aplanado. Nada de esto es evidencia clínica.

## 10 · Qué NO establece este ciclo

- **Ningún punto de parámetros es clínicamente válido.** 0 de 58 entradas del registro son
  `FACULTY_APPROVED`; las dos magnitudes activas tienen estado `CANDIDATE`.
- **No hay ninguna tolerancia numérica de aceptación** y no inventé ninguna. El criterio sigue siendo
  estructural y causal, con el legado como comparador y no como verdad.
- **Cinco de las siete magnitudes no quedan determinadas por esta evidencia**, y de ellas tres no se leen.
- **La sangre no es separable** del paquete en los escenarios certificados.
- **El horizonte es el del repositorio** (240 minutos como máximo); no extendí ninguno, porque eso sería
  inventar material clínico.
- **Que el experimento sea deseable no es una pregunta técnica.**
