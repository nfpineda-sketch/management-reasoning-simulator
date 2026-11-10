# PHASE2_AMENDMENT_1 · Registro formal de la enmienda

Rama `phase-2-amendment-1-respiratory-transmission`. Autorización: paquete **P2-AMEND-1F** (2026-11-10).
El registro legible por máquina es `docs/revision/PHASE2_AMENDMENT_1.json`; este documento lo explica y no lo
sustituye. El forense de la certificación fallida anterior está en `PHASE2_AMENDMENT_1_FORENSICS.md`.

**Estado:** <!-- estado -->**`PHASE2_AMENDMENT_1_CERTIFIED`.** La certificación final salió completamente en verde sobre el candidato congelado y la entrada del linaje se promovió a `CERTIFIED` (sólo metadatos; §10).<!-- /estado -->

No se afirma validación clínica, ni un valor docente aprobado para la fracción, ni autoridad de ejecución para
el núcleo común, ni cambio alguno en lo que ve el residente, en la puntuación o en el primer piloto.

## 1 · Cierre histórico (inmutable)

| | |
|---|---|
| Etapa | P2X-3, rama `phase-2-clinical-core-shadow` |
| HEAD | `d2cca46626ed5d45a792ec9456d46fb75fe87731` |
| Digesto | `22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a` sobre 141 fuentes de `clinical_core/` |
| Registro | `docs/revision/P2X3_phase2_closure.json` |

Nada de esto se reescribe. El cierre **se sigue recalculando desde los archivos vivos**: la etapa sucesora
declara las inserciones que la separan del cierre, las revierte y el resultado da, byte a byte, las fuentes del
registro de cierre y su digesto.

## 2 · La enmienda

| | |
|---|---|
| Versión | `PHASE2_AMENDMENT_1`, padre `PHASE2_CLOSURE` |
| Campo añadido | `CoreProfile.hypoventilation_oxygenation_transmission_fraction: float \| None = None` |
| Ecuación | antes `ΔPaO2 = −ΔPaCO2 / R`; ahora `ΔPaO2 = fracción × (−ΔPaCO2 / R)` |
| Dominio | `None`, o una fracción en [0, 1]; sólo se declara junto con `respiratory_quotient` |
| `None` | SIN ESCALAR: reproduce bit a bit la transmisión completa certificada en P2T-5 |
| `0` | no transmite nada **en todo estado**, también en el borde sin ventilación: equivale al enlace no declarado |
| `1` | la transmisión completa certificada |
| Fuentes del núcleo que cambian | `clinical_core/derived.py` (5 inserciones declaradas: el campo, su guarda, su entrada de registro y la expresión) y `clinical_core/decision_pack.py` (1: el registro de la etapa en `PACK_DIGEST_EXCLUDED`, como hicieron las 15 etapas anteriores) |
| Fuente añadida | `clinical_core/amendment_1.py` (la etapa sucesora; no contiene fisiología) |
| Digesto enmendado | el de `amended.core_digest` del registro JSON, sobre 142 fuentes (lo fija también `runtime_shadow.CORE_LINEAGE`) |
| HEAD del candidato | <!-- heads -->`0b3c44396ddac13a0e0f1c000113d14825d61f67` (árbol `f7bcdac45391…`); la promoción es el commit siguiente, que sólo cambia este registro y documentación<!-- /heads --> |

No se añade ninguna otra fisiología. La fracción no es un cociente respiratorio, ni un shunt, ni una ganancia de
FiO2, ni una retención de G, ni una eficiencia mecánica, ni una disponibilidad central; no multiplica
`retained(G)` y no escribe en FR, W, PaCO2, mecánica, G, L, estrés, distrés, FC ni tono.

**Compatibilidad hacia atrás: EXACTA.** Ningún perfil comprometido declara el enlace ni la fracción, así que
ninguna lectura se mueve. Con el enlace declarado (R = 0,8), `None` y `1,0` dan la SpO2 medida antes de la
enmienda bit a bit (25,249191654270817 en `opioid_35m`; 37,21648925248409 en `opioid_67f`).

## 3 · Los dos defectos reparados antes de congelar (A2)

**A2.1 · Fracción 0 ≠ enlace no declarado en un borde.** Causa: orden de las ramas. La función leía el PaCO2
antes de mirar la fracción; en el borde sin ventilación ese PaCO2 no existe y la lectura lanzaba
`UnresolvedBoundary`, mientras que con el enlace no declarado no se llegaba a leer. No era redondeo, ni la curva
de disociación, ni un tope, ni la serialización. Corrección: la fracción 0 se decide **primero** y devuelve la
SpO2 base. No cambia ninguna otra rama ni la ecuación. La prueba no se parcheó: se añadió el caso.

**A2.2 · Pruebas débiles.** Auditoría mecánica de las 39 pruebas originales de `d087cc3`, en una copia privada,
contra cinco mutantes externos de la fracción (ignorada, siempre cero, aplicada dos veces, complementada, y
«por omisión = 0,5»):

| Clase | Pruebas | Cuáles |
|---|---|---|
| `ACTUALLY_FALSIFIABLE` (la mata al menos un mutante) | 16 | t2, t3, t4, t5, t7–t9, t7b, t7c, t11, t12 |
| `ONLY_TESTS_VALIDATION` (la guarda del constructor) | 14 | t10, t10b, t10c |
| `ONLY_TESTS_EXISTENCE` (una frase del registro) | 2 | t3b, t14 |
| `ONLY_TESTS_SERIALIZATION` | 0 | — |
| `VACUOUS` respecto de la propiedad que nombra | 7 | t1, t6 (×3), t8b: ningún mutante las mata; t13, t13b: **omitidas**, nunca se ejecutaron |

Con el mutante «siempre cero», 30 de 39 no fallaban: la cifra de la revisión adversarial queda reproducida.
Además **ninguna** prueba original distinguía la fracción de su cuadrado (0 de 39 con «aplicada dos veces»).

La suite se reescribió (`test_phase2_amendment.py`, 59 pruebas): doce propiedades —fracción 0, fracción 1,
intermedia, la ecuación exacta en una rejilla de 11 fracciones × 7 minutos × 5 corridas (bit a bit, con deltas
mínimos, grandes y negativos), monotonía en hipercapnia, monotonía en hipocapnia, compatibilidad exacta por
omisión, sin efecto directo en la cadena ventilatoria (FR, W, PaCO2), sin efecto directo en el estado (G, L y el
resto), monotonía del oxígeno, comportamiento representable en opioide y en asma—, cada una con **control negativo
dentro de la suite**: 9 mutantes, 27 pares (mutante, propiedad) que deben fallar con `AssertionError`, y una
prueba que exige que toda propiedad tenga control y todo mutante sea matado. Todas caen también ante al menos uno
de los cinco mutantes externos independientes. La fracción inválida y la semántica de declarar o no el enlace se
prueban contra `CoreInvariantError`, etiquetadas como lo que son (validación). Resultado:
**`AMENDMENT_TESTS_FALSIFIABLE`**.

**Alcance exacto de «fracción 0 ≡ enlace no declarado».** Vale para toda lectura y todo estado del dominio
soportado. Lo que no se relaja son las precondiciones de *declarar* el enlace, que son de P2T-5 y no dependen de
la fracción: un perfil que declara el enlace —con fracción 0 igual que con 1— exige la mecánica respiratoria
común. Relajarlas para la fracción 0 cambiaría la validación certificada y no está autorizado; queda como
decisión docente (§11).

## 4 · La cadena existente (A3)

Quince etapas cerradas. Cada una es un módulo de `clinical_core/` con su tabla `REVERSAL` (las inserciones que
la separan de su predecesora), el digesto de congelación de la predecesora fijado como constante, una función
`p…_text` que reconstruye el texto de la predecesora desde el archivo vivo, su registro JSON congelado en
`docs/revision/` y su archivo de pruebas. Las pruebas de una etapa cerrada aplican en su *fixture* la cadena de
todas las posteriores, de modo que cada una lee el árbol tal como lo dejó.

| # | Etapa | Módulo | Revierte (archivo: inserciones) | Fija el digesto de | Reversión | Registro |
|---|---|---|---|---|---|---|
| 1 | P2O-3 | `lung_water_reference` | derived 3, integration 6, state 3, acs_ischaemia 2, pack 1, slice 1 | P2O-1 `22bb29b9…` | `p2o1_text` | `P2O3_lung_water_reference.json` |
| 2 | P2P-1 | `edema_migration` | pack 1, slice 1 | P2O-3 `3ae76680…` | `p2o3_text` | `P2P1_pulmonary_edema.json` |
| 3 | P2P-2 | `respiratory_drive` | derived 6, pack 1, slice 1 | P2P-1 `2c7dc8b1…` | `p2p1_text` | `P2P2_respiratory_drive.json` |
| 4 | P2Q-2 | `embolism_migration` | pack 1, slice 1 | P2P-2 `5e705336…` | `p2p2_text` | `P2Q2_pulmonary_embolism.json` |
| 5 | P2S-2 | `respiratory_mechanics` | derived 10, integration 9, state 6, provenance 4, pack 1, slice 1 | P2Q-2 `6eabb721…` | `p2q2_text` | `P2S2_respiratory_mechanics.json` |
| 6 | P2S-3 | `asthma_migration` | pack 1, slice 1 | P2S-2 `ba6e9997…` | `p2s2_text` | `P2S3_asthma_migration.json` |
| 7 | P2T-1 | `respiratory_distress` | derived 15, integration 10, state 6, provenance 4, pack 1, slice 1 | P2S-3 `652d7138…` | `p2s3_text` | `P2T1_respiratory_distress.json` |
| 8 | P2T-1A | `distress_closure` | derived 3, integration 3, pack 1, slice 1 | P2T-1 `773188d1…` | `p2t1_text` | `P2T1A_distress_closure.json` |
| 9 | P2T-3 | `asthma_distress_migration` | pack 1, slice 1 | P2T-1A `476e18f0…` | `p2t1a_text` | `P2T3_asthma_distress_migration.json` |
| 10 | P2T-5 | `oxygenation_link` | derived 5, pack 1, slice 1 | P2T-3 `3a648a9e…` | `p2t3_text` | `P2T5_oxygenation_link.json` |
| 11 | P2U-1 | `opioid_migration` | derived 7, integration 10, state 6, provenance 4, pack 1, slice 1 | P2T-5 `3a042f0f…` | `p2t5_text` | `P2U1_opioid_migration.json` |
| 12 | P2V-1 | `systemic_stress` | derived 8, integration 10, state 6, provenance 4, pack 1, slice 1 | P2U-1 `6638a22d…` | `p2u1_text` | `P2V1_systemic_stress.json` |
| 13 | P2W-1 | `distributive_tone` | derived 7, integration 11, state 6, provenance 4, pack 1, slice 1 | P2V-1 `00ce9e64…` | `p2v1_text` | `P2W1_distributive_tone.json` |
| 14 | P2X-1 | `tone_domain` | integration 3, provenance 1, pack 1, slice 1 | P2W-1 `345deb5d…` | `p2w1_text` | `P2X1_tone_domain.json` |
| 15 | P2X-1A | `closure_guard` | integration 5, provenance 1, pack 1, slice 1 | P2X-1 `3afa71b2…` | `p2x1_text` | `P2X1A_closure_guard.json` |
| **16** | **PHASE2_AMENDMENT_1** | **`amendment_1`** | **derived 5, pack 1** | **P2X-1A `eca47d35…`** | **`p2x1a_text`** | **`PHASE2_AMENDMENT_1.json`** |

La última etapa histórica que tocó `derived.py` es **P2W-1**; la cabeza de la cadena es **P2X-1A**. Dependen de la
cadena los cuatro documentos «generados del código actual» (§6) y los dos goldens.

## 5 · La etapa sucesora (A4)

`clinical_core/amendment_1.py` usa la misma semántica que las quince anteriores:

- `REVERSAL` declara las 6 inserciones; `proved` sólo acepta el archivo vivo si, revirtiéndolas —cada una debe
  aparecer exactamente una vez—, queda el archivo del cierre (su sha256 es el del registro de cierre). Una línea
  no declarada y la prueba falla.
- `p2x1a_text / bytes / sources` reconstruyen el árbol de P2X-1A, que es el del cierre.
- `chain(patch)` da a los paquetes cerrados la vista del cierre por **todos** los canales por los que observan el
  núcleo: texto (`_live`), bytes y mapas de fuentes, lectores por ruta (`ROOT`, `CORE_DIR`, `CORE`,
  `CANDIDATE_SOURCE`, `REPOSITORY`), `inspect`, el registro `PARAMETERS` (sea cual sea el orden en que se
  apliquen las cadenas), la lista de campos del perfil, su `repr` (una sonda cerrada lo incluye en un digesto), la
  copia de importación declarada (`oxygenation_link.P2T3_PARAMETERS`) y la tupla `PACK_DIGEST_EXCLUDED`.
  Es una vista de **lectura**: no cambia código ejecutado, y se restaura al salir.
- `historical_closure_verifies()` reúne las cuatro cosas que significan «el cierre sigue en pie»: reversión
  probada, archivos comunes intactos, digesto de cierre recalculado, y el registro de cierre todavía lo declara.

Resultado: los **67** digestos históricos fijados como constantes en `clinical_core/` no cambiaron ni uno; las
15 pruebas de etapa y la de la cabeza pasan contra sus registros congelados sin editar ningún valor esperado; el
digesto de cierre se recalcula a `22b90a6f…` y el de congelación de P2X-1A a `eca47d35…`. En los archivos de
prueba históricos lo único añadido es la importación de la etapa y su llamada al final de cada *fixture* de
cadena (más la vista explícita en las pruebas que comparan con un documento histórico).

**A5 · `SECONDARY_FAILURE_CONFIRMED`.** Los errores «`_derived_at_*` no tiene `CoreProfile`» de la certificación
fallida desaparecen por completo en cuanto la reconstrucción no aborta (0 apariciones en los 60 archivos de
contratos raíz). No se cambió ninguna API histórica.

## 6 · Artefactos (A6, A7, A8)

**Documentos generados.** Los cuatro históricos (`P2G_DECISIONES_DOCENTES_CALIBRACION_GI.md`,
`P2I_DECISION_LACTATO_GI.md`, `P2I2U_ANCLAS_HEMORRAGIA_COMPARTIDA.md`, `P2I2T_ESTADO_HEMORRAGICO_COMPARTIDO.md`)
y sus datos son idénticos byte a byte al commit de cierre y **no se regeneran**: siguen reproduciéndose bajo la
vista del cierre. El registro de la enmienda guarda, con versión explícita (`PHASE2_CLOSURE` /
`PHASE2_AMENDMENT_1`), el digesto que el mismo generador da sobre el árbol enmendado y qué fuentes de entrada se
movieron (sólo las declaradas). El digesto de congelación de la calibración no cambia.

**Golden.** El golden histórico (`clinical_core/golden/gi_bleed_shadow.json`) no se reescribe. Sobre el núcleo
enmendado, 8 de sus 9 bloques son idénticos —incluidos `scenarios` y `differences`, los de comportamiento—; el
bloque `parameters` gana exactamente una entrada (70 → 71), la del control nuevo, y no pierde ni cambia ninguna.
Esa única diferencia es la expectativa versionada, y tiene control negativo. Límite declarado: el golden es de
la familia GI, que no declara el enlace; demuestra la exactitud por omisión, no el enlace encendido (eso lo
prueban las propiedades de §3).

**Serialización.** `BACKWARD_READ_COMPATIBLE = true`: un artefacto escrito antes de la enmienda no trae la clave y
se lee con el valor por omisión. `FORWARD_READ_COMPATIBILITY = NOT_PROVIDED`: un artefacto escrito por el núcleo
enmendado trae la clave (aunque valga `None`) y el núcleo del cierre lo rechaza. Antes de la enmienda no existía
garantía hacia adelante y no se inventa una. Ambas cosas están probadas ejecutando el `derived.py` del cierre.

## 7 · Linaje certificado y compuerta del runtime (A9, A10)

`runtime_shadow.CORE_LINEAGE` es una tupla inmutable de `CoreVersion` congeladas (identificador, padre, digesto,
registro, HEAD, módulo de reversión). La **única** entrada certificada por construcción es la raíz: el cierre
histórico mismo, primero en la tupla, con su HEAD y su digesto y sin reversión —no «cualquier entrada sin padre»—.
El linaje tiene que estar bien formado (una raíz; cada sucesor con un padre **anterior** y su módulo de reversión;
ninguna versión ni digesto repetidos) o se rechaza entero. **El estado de un sucesor no está en el código:** se
lee de su registro, y sólo si ese registro está ligado a la entrada (misma versión, mismo digesto, mismo cierre
histórico). Y `CERTIFIED` sólo vale con la evidencia de la certificación en el propio registro: el digesto
certificado, el commit candidato, una suite completa sin fallos ni errores y regresiones sin fallos. Escribir un
digesto en la tupla, o una palabra en el registro, no autoriza nada.

La compuerta (`runtime_shadow_evidence.core_lineage_verdict`) exige cuatro condiciones a la vez:

1. `historical_closure_verifies` — el cierre histórico se sigue verificando desde los archivos vivos;
2. `active_core_in_lineage` — el digesto vivo es miembro del linaje;
3. `active_core_certified` — ese miembro está `CERTIFIED` (el cierre por construcción; un sucesor por su registro);
4. `active_core_recomputes` — los archivos recalculan a ese digesto, también por la definición del sucesor.

Los tres sitios que antes comparaban una constante preguntan ahora al linaje. Falla cerrado y no lanza: un
registro ausente, ilegible, de otra forma o no ligado, una reversión que no puede ejecutarse o un veredicto que no
puede calcularse son un rechazo. El motivo del rechazo dice qué condición falló; ya no afirma que «el digesto de
cierre no recalcula» cuando el cierre sigue en pie y lo que falta es la certificación.

Controles negativos (`test_phase2_amendment_lineage.py`, 56 pruebas; todas leen el linaje real, nunca la vista
previa): digesto que nadie certificó (NC1); digesto escrito en el linaje sin registro, o con registro ajeno
(NC1b); sucesor sin certificar, y sólo el estado decide (NC2); un registro certifica sólo el digesto que declara
(NC2b); una palabra no es una promoción (NC2c, 16 bloques incompletos); un registro de otra forma rechaza y no
lanza (NC2d, 10 formas); la compuerta responde «no» si el veredicto no puede calcularse (NC2e); un sucesor válido
no oculta un cierre roto (NC3), ni un registro de cierre manipulado (NC3b), ni un cambio no declarado (NC3c), ni
una inserción duplicada (NC3d); una inserción movida no es el sucesor certificado (NC3e); el sucesor debe
recalcular por su propia definición (NC4) y una entrada que no coincide con los archivos no es el núcleo activo
(NC4b); una entrada no es la raíz por no nombrar padre (NC5) y un linaje mal formado se rechaza entero (NC5b, 12
formas). Diez mutantes externos de la compuerta (entre ellos el comportamiento anterior a la corrección de NC5)
hacen fallar la suite.

**Estado previo a la certificación (A10.1).** La entrada permaneció `CANDIDATE` durante toda la implementación y
la certificación. Con el linaje real, 127 de las 391 pruebas de la capa de la Fase 3 fallan cerradas, como debe
ser. La corrida de certificación ejercita el runtime «como quedará» mediante un plugin de pruebas explícito
(`test_core_certification_preview.py`: hay que cargarlo con `-p` **y** nombrar la versión en una variable de
entorno); ningún módulo del runtime lee esa variable, `conftest.py` no carga el plugin, y sólo convierte
`CANDIDATE` en `CERTIFIED` para la versión nombrada. Las guardas de aislamiento de la Fase 3 (R13, H20) no se
tocaron.

`versions()` añade `core_version` y `core_digest`: un artefacto nombra el núcleo que lo produjo junto al cierre
del que parte.

## 8 · Contratos raíz (A11)

La certificación fallida de `d087cc3` dio 612 incidencias en 53 archivos, con 6 contratos raíz. Sobre esos 53
archivos más 7 de salud (60 archivos; 2 038 pruebas en la pasada previa al congelamiento, 0 fallos, 0 errores):

| Contrato raíz | Antes | Ahora |
|---|---|---|
| C1 cadena de reconstrucción | 466 | 0 |
| C2 compuerta de digesto del runtime | 131 | 0 con la vista previa; 127 rechazos correctos con el linaje real en `CANDIDATE` |
| C3 digestos de congelación de etapa | 10 | 0 |
| C4 goldens | 2 | 0 |
| C5 documentos generados | 3 | 0 |
| C6 registro de cierre | (contado dentro de C1 y C2) | 0 |

Seis fallos residuales de la primera pasada (una prueba del paquete de decisiones que recorre el directorio
vivo, tres que comparaban el digesto vivo con la constante histórica y dos guardas de aislamiento que detectaron
la vista previa en `conftest.py`) se corrigieron sin tocar ninguna guarda ni valor histórico.

## 9 · Revisión adversarial previa al congelamiento (A12)

Una revisión independiente, sobre el punto de control `c14c968`, con 17 ataques y copias privadas del árbol.

**Resistieron** (no reproducidos): historia reescrita (los únicos cambios bajo `clinical_core/` y
`docs/revision/` respecto del cierre son las 6 inserciones declaradas y los archivos nuevos; en las pruebas
históricas sólo se añadió la importación de la etapa y su llamada); reproducibilidad del cierre, recalculada con
código propio del revisor y comparada con `git show`; sucesor aceptado con el cierre roto; documentos y golden
sobrescritos; fracción 0 frente a enlace no declarado (44 trayectorias completas y 13 475 llamadas, 0
diferencias, borde sin ventilación incluido); fracción 1 y `None` frente a la transmisión histórica (13 475
llamadas y 305 estados, bit a bit); control encendido en algún perfil comprometido (7 perfiles, 2 de migración y
18 puntos de la Fase 3: todos `None`); golden; restauración de la vista (151 atributos, también si el cuerpo
lanza); vista previa inerte fuera de pytest.

**Confirmado y corregido.**

| Sev. | Hallazgo | Corrección |
|---|---|---|
| MEDIO | «Certificado por construcción» se decidía por `parent is None`: una entrada sin padre con el digesto vivo abría la compuerta sin registro (requería editar `runtime_shadow.py`) | sólo la raíz histórica lo es; linaje bien formado; NC5, NC5b |
| BAJO | Un registro JSON válido de otra forma lanzaba dentro de la compuerta, contra su contrato de no lanzar | rechaza; `core_lineage_ok` nunca lanza; NC2d, NC2e |
| BAJO | El motivo del rechazo decía siempre «el digesto de cierre no recalcula» | dice la condición que falló |
| BAJO | La promoción era una palabra en el registro | `CERTIFIED` exige la evidencia de la certificación; NC2c |
| BAJO | Mutantes vivos: saturación por arriba, banda muerta por abajo, umbral sobre el delta | propiedad de rejilla exacta y tres mutantes más |
| BAJO | `common_untouched` vacío, inserción duplicada y campos falsos del registro pasaban | se exige 139 fuentes; NC3d; el registro se recalcula |
| BAJO | Dos pruebas de artefactos eran tautologías | se recalculan las entradas movidas; 7 corrupciones del golden |
| BAJO | La entrada a la vista no era segura ante una excepción | restaura si falla |
| BAJO | Una corrida previsualizada no lo decía | lo anuncia en la cabecera y al final |
| BAJO | El digesto vivo de la guarda de cierre que lleva `versions()` no estaba registrado | los cinco digestos de congelación, con su valor sucesor |

**Declarado, sin cambio de código.**
- La reversión prueba que *quitando* lo declarado queda el cierre, no *dónde* está lo declarado: una inserción
  pura movida sigue reconstruyendo el cierre. La posición la fija el digesto enmendado, y la compuerta rechaza ese
  árbol (NC3e). Es la semántica de las 15 etapas anteriores.
- Dentro de la vista del cierre, copiar un perfil con fracción declarada perdería la fracción. Ningún módulo del
  runtime abre la vista (hay prueba) y los paquetes cerrados sólo manejan perfiles sin ella.
- La caché de digestos se indexa por nombre, tamaño y fecha de las fuentes: una edición que conserve ambos no se
  ve en el mismo proceso. Es anterior a la enmienda y no se debilitó.
- Del registro de cierre la compuerta fija `sources` y `phase2_digest`; sus demás campos no.
- La primera llamada a la compuerta importa la etapa (≈0,4 s en frío, ≈5 ms después).
- `test_respiratory_transmission.py` R9 cambió un valor esperado en `d087cc3`: es la rectificación declarada de
  P3-127 sobre un registro de la Fase 3, no un valor histórico de la Fase 2.

## 10 · Certificación final (A14) y promoción (A15)

<!-- certificacion -->**Candidato certificado:** `0b3c44396ddac13a0e0f1c000113d14825d61f67`, congelado una sola vez; huella de la corrida
`c043c38e607f0544…`, idéntica al inicio y al final (corrida **válida**). Python 3.11.17.

| Verificación | Resultado |
|---|---|
| Suite completa particionada (4 particiones, tope de 2 h por partición) | **11 195 pruebas · 0 fallas · 0 errores · 93 omitidas · 1 xfail** |
| Particiones | partición 0: 3029 pruebas, salida 0; partición 1: 2733 pruebas, salida 0; partición 2: 2336 pruebas, salida 0; partición 3: 3097 pruebas, salida 0 |
| Regresiones (`run_regressions.py`) | 56/56 activas aprobadas; 10 retiradas, no se corren |
| Contratos raíz (60 archivos, antes del congelamiento) | 2 038 pruebas, 0 fallos, 0 errores |
| `git diff --check` y `git status` | limpios |

La suite completa incluye, entre otras, las pruebas propias de la enmienda, las 16 de etapa de la cadena, las de
perfil y esquema, mecánica respiratoria, migraciones de opioide y de asma, oxigenación, DO2/deuda/colapso,
aislamiento, congelamiento del lector, los goldens históricos, la expectativa de golden de la enmienda y el golden
de Contracts v2.

La suite corrió con el plugin de vista previa cargado y la versión nombrada, porque el linaje real estaba —y debía
estar— en `CANDIDATE`; las pruebas marcadas `real_core_lineage` leyeron el estado real durante toda la corrida.

**Corrida anterior, invalidada por un fallo real.** La primera certificación, sobre el candidato
`ad5d941`, dio 11195 pruebas con **1 falla** y
0 errores: `test_shadow_core_isolation.py::test_the_core_imports_only_what_a_shadow_needs`. La guarda de aislamiento del núcleo exige que cada
módulo declare los módulos estándar que usa fuera de la lista común, y a la etapa nueva le faltaba la declaración
de `sys` y `types` que las siete etapas anteriores con vista propia sí tienen. Se añadió esa entrada —la guarda no
se relajó—, el candidato cambió y, como manda la regla, se corrió **una** certificación nueva, que es la de arriba.

**Promoción (A15).** Sólo cambian `certification` en el registro JSON y documentación; `git diff` entre el
candidato y la promoción no toca ningún archivo ejecutable ni de prueba. El bloque `certification` lleva la
evidencia que la compuerta exige para dar por válido `CERTIFIED`.

**Comprobación con el linaje real, ya sin vista previa.** Tras promover, y **sin** el plugin: 28 archivos —los 14 de la capa de la Fase 3, los de la enmienda y el cierre, la cabeza de la cadena, los dos goldens, aislamiento, congelamiento del lector y las pruebas que leen el Decision File y el registro de deuda—, **733 pruebas, 0 fallos, 0 errores**. Las 391 pruebas de la capa de la Fase 3 pasan por la compuerta real; antes de la promoción, 127 de ellas fallaban cerradas. No se repitió la suite completa después de promover: la promoción no toca ningún archivo ejecutable ni de prueba.<!-- /certificacion -->

## 11 · Deuda y límites declarados

- La vista del cierre cubre los canales de observación que hoy usan los paquetes cerrados. Una etapa futura que
  observe el núcleo por otro canal tendrá que extenderla; la prueba de copias de importación lo detecta para ese
  canal, no para todos.
- Compatibilidad hacia adelante de artefactos: no provista.
- Precondiciones de declarar el enlace con fracción 0: son las del enlace (§3). Relajarlas es decisión docente.
- La vista del cierre no debe usarse con perfiles que declaren la fracción (§9).
- La fracción no tiene valor docente aprobado. La región medida en P3-128 (`f ≤ 0,060621` con R = 0,8 declarado;
  sólo se identifica el cociente f/R) es una medición de la Fase 3, no una calibración.
- La integración en `phase-3-runtime-integration` no está hecha: su diseño es `P3_INTEGRATE_AMEND1_DISENO.md`.
