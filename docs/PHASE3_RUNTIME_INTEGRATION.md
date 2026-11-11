# Fase 3 · Integración en tiempo de ejecución, en sombra

Rama `phase-3-runtime-integration`, desde la cabeza de cierre formal de la Fase 2
`d2cca46626ed5d45a792ec9456d46fb75fe87731`, digesto `22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a`.

```
COMMON_CORE_RUNTIME_AUTHORITY = False
```

El motor heredado (`family_engine.py`) es la **única** autoridad en tiempo de ejecución. El núcleo común
puede leer, calcular, replayear, comparar, registrar y producir artefactos para docencia o investigación. No
puede controlar una vital, un estado mental, un paro, la disponibilidad de una acción, el destino de una
orden, la puntuación, una interrupción, la persistencia autoritativa ni la traza del residente. Cualquier
camino desde la salida en sombra hacia una conducta autoritativa es un bloqueo, no un detalle.

La Fase 2 es inmutable: ningún archivo de `clinical_core/` cambia en esta rama, y tres suites recalculan el
digesto de cierre en cada corrida.

> **Nota del 2026-11-10 (P3-INTEGRATE-AMEND1, FD-P3-119).** La frase anterior describe la rama hasta la
> integración de la enmienda formal. Desde el merge `534aa50`, `clinical_core/` es aquí el sucesor
> **certificado** `PHASE2_AMENDMENT_1` (142 fuentes, digesto `10b45ce2…`), no el núcleo del cierre. El cierre
> histórico (`d2cca46`, `22b90a6f…`, 141 fuentes) no se reescribe: se **reconstruye** desde el núcleo vivo y la
> compuerta exige que el núcleo activo sea un miembro certificado del linaje. Donde este documento dice más abajo
> «el digesto de la Fase 2» o «las 141 fuentes congeladas», léase a partir de esa fecha «un miembro certificado
> del linaje». La regla que sigue en pie: ningún paquete de la Fase 3 edita `clinical_core/`. Detalle:
> `docs/revision/PHASE2_AMENDMENT_1.md` y `docs/PHASE3_MANAGEMENT_GENERALIZATION.md` §1.

> **Nota del 2026-11-10 (segunda familia en sombra en vivo, FD-P3-131 a FD-P3-137).** Donde este documento dice
> que la sombra en vivo es sólo de GI, léase a partir de esa fecha `LIVE_FAMILIES = ("gi_bleed", "opioid")`. El
> opioide corre en sombra en vivo **sin autoridad**, con su llegada comprobada contra el caso redactado y su
> parámetro de transmisión como conjunto de tres testigos. La autoridad sigue teniendo su propia compuerta,
> que nombra sólo a GI y sigue cerrada. Detalle: `docs/PHASE3_SECOND_LIVE_FAMILY.md`.

> **Nota del 2026-11-10 (ciclo de observabilidad, FD-P3-139 a FD-P3-150).** Tres cosas de este documento se
> leen desde esa fecha así. **(1)** Una sesión de sombra se abre sólo sobre una llegada intacta, por una regla
> compartida de cinco condiciones; pedida sobre cualquier otro estado, se abre sin corrida y con el motivo
> registrado, y un turno de cero minutos ya no hace que la página la suelte. **(2)** La capa declarada
> (`LAYER_SOURCES`) tiene siete fuentes: se sumaron `runtime_shadow_store.py` (almacén de trazas de
> investigación de la sombra, apagado por omisión, distinto del de autoridad) y `runtime_shadow_observer.py`
> (informe docente de sólo lectura). Ninguno es un cruce nuevo: `app.py` y `pilot_acceptance.py` siguen siendo
> los únicos lectores de la capa, y ninguno de los dos importa esos módulos. **(3)** Nada de esto da autoridad
> ni llega al residente. Detalle: `docs/PHASE3_SHADOW_OBSERVABILITY.md`.

Un solo artefacto de la Fase 2 sí cambia, y no es fisiología: `test_phase2_closure.py`. Dos de las
reclamaciones del registro de cierre son del repositorio entero —qué tocó P2X-3 y qué módulos de aplicación
importan el paquete en sombra— y la prueba las leía del árbol de trabajo. El registro describe el commit de
cierre, así que ahora se leen de **ese** árbol (`git log --diff-filter=A` sobre el propio registro lo
localiza). Sin eso, el registro de una etapa terminada falla por la existencia de la etapa siguiente, que la
misma autorización docente abrió. El registro JSON no se toca: ni un byte. Las reclamaciones no se debilitan;
se recalculan sobre el árbol que describen, y la sonda de 21 mutaciones sigue detectándolas.

## Por qué la capa vive fuera de `clinical_core/`

El digesto formal de cierre cubre **todas** las fuentes del paquete. Un módulo de Fase 3 colocado ahí movería
el digesto de una etapa cerrada. Por eso toda la infraestructura vive en la raíz: `runtime_shadow.py` (P3-1) y
`runtime_shadow_families.py` (P3-4, P3-6, P3-8, P3-9).

## La bandera

| Estado | Qué hace |
|---|---|
| ausente, vacía o desconocida | **apagado**: el tiempo de ejecución es exactamente el motor congelado; no se abre sesión, no se inicializa nada, no cambia ningún registro |
| `MRS_PHASE3_SHADOW=shadow_compare` | el núcleo corre en paralelo, sin autoridad y sin visibilidad |

`MRS_PHASE3_SHADOW_FAMILIES` sólo puede **acotar** el alcance, nunca ampliarlo. La bandera es una variable de
entorno del proceso: no añade ninguna clave al estado del paciente, que es la garantía más fuerte de que
«apagado» es idéntico. Ninguna superficie del piloto la nombra —ni el preflight, ni el humo, ni el runbook, ni
el documento de readiness— y un entorno limpio no abre sesión; una prueba lee esas superficies y lo fija.

Lo que **no** se pudo hacer: añadir las dos banderas a `pilot_freeze.RUNTIME_FLAGS`, que haría que el
preflight del piloto fallara si alguien las exporta. `pilot_freeze.py` está dentro del conjunto congelado de
la Fase 2 (`clinical_core.calibration.INPUT_PATH_SOURCES`), así que esa fila mueve el digesto de la
congelación de calibración y dos documentos generados de la Fase 2. Es `PHASE2_FROZEN_INTERFACE_INSUFFICIENT`
para ese objetivo: se paró el camino y quedó declarado como `PILOT_PREFLIGHT_FLAG_GATE_DEFERRED` (TD-130), en
vez de reabrir una etapa cerrada por una comodidad. La prueba R15 afirma hoy las dos mitades: que el conjunto
congelado cubre `pilot_freeze.py` y que la fila no está.

## El puente declarado

Desde P3-1 el tiempo de ejecución alcanza el núcleo por **un** punto declarado, `runtime_shadow`, y por
ninguno más. `test_shadow_core_isolation.py` reformula el invariante de la Fase 2 en dos mitades:

1. ningún otro módulo del tiempo de ejecución importa `clinical_core`;
2. **cortando el puente, el aislamiento de la Fase 2 vale exactamente como valía**, y sólo dos módulos usan el
   puente: `app.py` y `pilot_acceptance.py`.

Lo que el veto de importación garantizaba —que el núcleo no puede tocar el encuentro— lo garantizan ahora
R1–R17: la bandera apagada por omisión, el registro autoritativo byte-idéntico encendida o apagada, y la
ausencia de cualquier lector de la salida en sombra.

## Cómo se alinea un minuto

El motor avanza sus minutos dentro de `execute_family_bundle`. Esta capa **no** se engancha en ese lazo y
**nunca** vuelve a ejecutar el motor: espeja lo que el motor ya decidió —las acciones ejecutadas, con los
minutos de inicio que informan sus propios recibos— y lleva el núcleo al mismo `sim_time`. El minuto N del
legado y el minuto N de la sombra son el mismo intervalo causal, contados desde la llegada; la comparación
ocurre donde existe una verdad del legado, en cada frontera de turno, y la sombra conserva todos los minutos
intermedios.

## El espejo consume la suerte que el libro de órdenes ya decidió

La sombra **no** vuelve a decidir si una orden ocurrió. Espeja sólo la lista asentada que el motor recibió
(`run` en `pilot_acceptance.order`, `run_actions` en `app.execute_bundle`), nunca `parsed["actions"]`:

- una orden retenida a la espera de una aclaración no se espeja, y queda como hueco declarado;
- el recibo de una entrega se empareja **por posición dentro de su propia clase**, como hace el mapeo
  certificado de la Fase 2 (`legacy_adapter._summaries`): la primera bolsa del turno toma el primer recibo;
- si el motor informa menos recibos que acciones de esa clase, la entrega **falla cerrado** como hueco, en vez
  de tomar un recibo ajeno;
- la identidad de una orden real es el `order_id` del libro: el mismo turno observado dos veces se espeja una
  vez. El identificador propio del evento lleva minuto, turno, posición y clase, así que dos turnos del mismo
  minuto nunca comparten uno.

## Qué hay implementado

| Pieza | Dónde | Estado |
|---|---|---|
| bandera y sesión en vivo (GI) | `runtime_shadow.py` | P3-1, certificado |
| espejo inmutable de acciones asentadas, idempotente por la identidad del libro | `runtime_shadow.py` | P3-1 |
| clasificación de divergencias contra el golden comprometido | `runtime_shadow.py` | sin umbrales inventados |
| runner genérico, contrato de adaptador, replay determinista | `runtime_shadow_families.py` | P3-4 |
| seis adaptadores de familia, diez casos certificados | `runtime_shadow_families.py` | replay offline |
| instantáneas por región con procedencia | `runtime_shadow_families.py` | P3-6 |
| envolvente y lectura legado-contra-región | `runtime_shadow_families.py` | P3-6 |
| diagnóstico no autoritativo de consciencia y colapso | `runtime_shadow_families.py` | P3-8 |
| traza de investigación, resumen y tamaños | `runtime_shadow_families.py` | P3-9 |

## Matriz de familias

| Familia | Casos | Replay offline | Sombra en vivo | Tratamientos mapeados | Vacíos declarados |
|---|---|---|---|---|---|
| `gi_bleed` | `gi_bleed_57m`, `gi_bleed_72f` | sí | **sí** | fluido, sangre, oxígeno, IBP, endoscopia | anticoagulación, antiagregante, vasopresor (P3-11) |
| `acs` | `acs_70f_left_main` | sí | no | oxígeno | reperfusión, fluido, fármacos |
| `pulmonary_edema` | `pulmonary_edema_58m` | sí | no | oxígeno | nitrato, diurético, VNI |
| `pulmonary_embolism` | `pulmonary_embolism_61m`, `_33f` | sí | no | oxígeno | anticoagulación, trombólisis |
| `asthma` | `asthma_49m`, `asthma_24f` | sí | no | oxígeno | broncodilatador, corticoide |
| `opioid` | `opioid_35m`, `opioid_67f` | sí | no | oxígeno | naloxona, ventilación |

La sombra en vivo es **sólo GI** a propósito: en las otras cinco, el tratamiento que define su manejo correcto
no tiene acción mapeada, y una sombra donde el residente trata y el paciente en sombra no responde produciría
divergencias que parecen un error del núcleo y son un escritor ausente.

## Clases de divergencia

`EXPECTED_ARCHITECTURAL_DIVERGENCE` (la diferencia que el golden declara en **todos** sus escenarios, con su
cita), `PARTIALLY_EXPLAINED_DIVERGENCE` (la declara en algunos y no en otros: se informa con el conteo),
`PARAMETER_DISABLED_DIVERGENCE`, `REGION_DIVERGENCE`, `MAPPING_GAP`, `TREATMENT_GAP`, `COMMON_BOUNDARY`,
`UNEXPECTED_STRUCTURAL_DIVERGENCE`, `SAFETY_CRITICAL_DIVERGENCE`, `NOT_COMPARABLE`. Ningún umbral numérico: la
línea base es el golden comprometido, que dice variable por variable qué diferencia explica cada una.

La distinción no es cosmética. El golden de GI tiene veinte escenarios y declara `hr` en diecinueve, `crt_s`
en dieciocho, `V_ml_eq` en diez y `consciousness_level` en uno. Unir los veinte en un solo conjunto
«explicado» silenciaba esas cuatro variables en los escenarios donde el golden **sí** espera coincidencia. Con
la regla de «todos los escenarios», lo explicado por arquitectura en GI queda en seis variables (`dbp`,
`hb_g_dl`, `lactate_mmol_l`, `map`, `respiratory_rate`, `sbp`) y el resto se informa con su conteo, sin
silencio y sin alarma falsa.

## Lo medido

| Magnitud | Valor | Cómo |
|---|---|---|
| sobrecosto de la doble corrida | +0,080 s sobre 0,210 s (×1,38), ≈20 ms por turno | encuentro GI de cuatro turnos, siete repeticiones, mediana, apagado contra `shadow_compare` |
| entrada de replay (75 minutos) | 5 740 bytes | `artifact_sizes` |
| traza mínima (75 minutos) | 11 594 bytes | `artifact_sizes` |
| traza verbosa (75 minutos) | 42 694 bytes | `artifact_sizes` |
| batería completa, legado contra legado+sombra | ×1,07 y ×1,27 (dos casos, una corrida cada uno) | `battery_evidence`, 19 categorías por caso |
| artefactos de la batería completa (34 escenarios) | replay 201 664 B · traza mínima 399 657 B · verbosa 1 116 664 B | `artifact_totals` |

El valor por omisión recomendado es la traza mínima: la verbosa guarda cada valor derivado de cada minuto, y
la mínima guarda el digesto, las divergencias y la entrada de replay, que reproduce todo lo demás exacto.

## Veredictos de los paquetes

| Paquete | Veredicto |
|---|---|
| P3-1 · plomería de la doble corrida en vivo | certificado (85 pruebas de la capa, verdes) |
| P3-2 · política de parámetros | `SHADOW_REGION_WITNESSES_PREFERRED` |
| P3-3 · preautoridad de consciencia y colapso | `CONSCIOUSNESS_SHADOW_WIRING_READY`, `COLLAPSE_SHADOW_DIAGNOSTIC_READY` |
| P3-4 · arnés multifamilia y replay | `MULTIFAMILY_SHADOW_HARNESS_READY` |
| P3-5 · punto de control | `PHASE3_SHADOW_READY_AFTER_ONE_MINIMUM_PACKAGE` |
| P3-6 · conjunto por región | `REGION_AWARE_SHADOW_ENSEMBLE_READY` |
| P3-7 · expansión en vivo multifamilia | **puerta no cumplida**: `MULTIFAMILY_LIVE_SHADOW_READY_ONLY_FOR_GI` |
| P3-8 · diagnóstico neuro y de colapso | `SHADOW_NEURO_COLLAPSE_DIAGNOSTICS_READY` |
| P3-9 · traza de investigación | `SHADOW_RESEARCH_TRACE_READY` |
| P3-10 · certificación de preautoridad | **B** · `ONE_MINIMUM_PACKAGE_BEFORE_AUTHORITY_DECISION` |
| P3-11 · un camino de ejecución y la batería completa | `LIVE_REPLAY_SINGLE_EXECUTION_PATH` y **`GI_FULL_LIVE_SHADOW_EVIDENCE_NOT_READY`** por tres vacíos de tratamiento |

El paquete mínimo que P3-10 recomienda antes de cualquier decisión de autoridad es «P3-11 · evidencia de la
sombra en vivo de GI sobre la batería de aceptación»: la misma plomería, sobre los encuentros completos del
arnés de aceptación, para que la decisión docente se tome sobre divergencias observadas y no sobre una
promesa de la arquitectura.

## Qué no hace

- No concede autoridad, ni la prepara por la puerta de atrás: no hay modo de autoridad.
- No enciende ningún mecanismo apagado ni aprueba ninguna magnitud: 60 parámetros siguen `provisional` y las
  58 magnitudes clínicas siguen con **0 aprobadas**.
- No cablea la consciencia ni el colapso al encuentro: son diagnósticos, sin categoría y sin umbrales.
- No integra el motor de casos generados (`clinical_physiology`): `GENERATED_CASE_ENGINE_INTEGRATION_DEFERRED`.
- No toca el piloto: su motor sigue congelado y la bandera queda apagada en su configuración.

## Deuda declarada de esta rama

1. ~~`LIVE_SHADOW_UNIFICATION_DEFERRED`~~ **cerrada en P3-11**: hay una sola primitiva de ejecución
   (`ShadowPhysiologyRunner.advance`) y una prueba estructural impide que otro módulo de la capa llame a
   `integration.run`.
2. ~~`LIVE_SHADOW_IN_STREAMLIT_LAYER`~~ **cerrada en P3-11** en lo que podía cerrarse sin navegador: una
   prueba conduce el enganche exacto de `app.py` (`_runtime_shadow_session`) y otra fija el orden del sitio
   de llamada por AST. Queda `UI_E2E_DEFERRED_BEFORE_AUTHORITY`, que **no** hace falta antes de la primera
   autoridad limitada: la sombra no dibuja nada. Si una autoridad llegara a tocar la pantalla del
   residente, la prueba de extremo a extremo pasa a ser obligatoria (puerta de P3-13).
3. **`GI_TREATMENT_GAPS`** (P3-11): la batería de GI ordena anticoagulación, antiagregante y vasopresor, y
   el mapeo común no tiene escritor para ninguno. Están declarados como `TREATMENT_GAP` escenario por
   escenario, y son el bloqueo de una autoridad hemodinámica en GI, no de la sombra.
4. Vacíos de tratamiento en las cinco familias no GI.
4. El mapeo de impairment a categoría mental y los umbrales del colapso siguen siendo decisión docente.
5. `PILOT_PREFLIGHT_FLAG_GATE_DEFERRED`: el preflight del piloto no puede exigir las banderas ausentes sin
   mover un digesto congelado de la Fase 2. Hoy el piloto queda protegido por que ninguna de sus superficies
   nombra la bandera y por que un entorno limpio no abre sesión.

El paquete de decisión docente que P3-12 y P3-13 producen, sólo lectura y sólo diseño, vive en
`docs/PHASE3_PREAUTHORITY_DECISION_PACK.md`.

## P3-11 · Un solo camino de ejecución, y la batería completa como evidencia

Desde P3-11 hay **una** primitiva de ejecución. La sesión en vivo captura las entradas autoritativas, arma
los eventos espejados inmutables y llama a `ShadowPhysiologyRunner.advance`; el replay offline carga esos
mismos eventos y llama al mismo runner. No hay segundo avance de minuto, ni segundo clasificador, ni segundo
artefacto de replay: `LIVE_REPLAY_SINGLE_EXECUTION_PATH`. Una prueba estructural lo fija —ningún módulo de
la capa salvo el runner puede llamar a `integration.run`—, así que «vivo = replay» dejó de depender de que
dos implementaciones coincidan: es la misma función del mismo dato inmutable, y las pruebas sólo lo
confirman.

Lo que la unificación **no** movió: los digestos de la sombra GI, las acciones espejadas, los minutos, las
divergencias ni el registro autoritativo. Los digestos finales de los dos casos GI quedaron fijados como
`BASELINE` en `test_runtime_shadow_evidence.py`, capturados **antes** del cambio.

### Lo que la batería completa encontró y dos turnos no podían encontrar

El artefacto de replay se construía llamando a `contributors()` **sin** el estado de mapeo, así que la
hemostasia endoscópica —que el núcleo recibe por `family_state.endoscopy_at`— faltaba en el artefacto: el
replay divergía del vivo en los cuatro escenarios que piden endoscopia. Con un caso y dos turnos, sin
endoscopia, P3-1 no podía verlo. El runner ahora recuerda el estado de mapeo con el que avanzó y construye
el artefacto con el mismo; la igualdad se comprueba digesto por digesto en los 34 escenarios.

### La evidencia

La batería es la del repositorio (`pilot_acceptance.battery`, 19 categorías por caso, A–K más las de curso y
de propiedades), jugada dos veces por caso: con la bandera apagada y en `shadow_compare`. Ningún escenario
es inventado aquí; lo único que se añadió a `pilot_acceptance.py` es una etiqueta por partida y un colector
apagado por omisión que ninguna categoría lee.

| | |
|---|---|
| escenarios con evidencia | **34** (17 por caso, dos casos GI) |
| las 19 categorías deciden lo mismo con la sombra encendida | **sí**, en los dos casos |
| vivo = replay, digesto por digesto | **34 de 34** |
| condiciones críticas de P3-11-8 disparadas | **ninguna** |
| divergencias `UNEXPECTED` o `SAFETY_CRITICAL` | **ninguna** |
| clases observadas | `EXPECTED_ARCHITECTURAL_DIVERGENCE` y `PARTIALLY_EXPLAINED_DIVERGENCE` |
| minutos comparados | **82** (de 1 604 minutos de sombra) |
| acciones totalmente espejadas | fluido, sangre, IBP, endoscopia (por `family_state`) |
| acciones sólo estructurales | consulta (la Fase 2 la declara no fisiológica) |
| acciones sin escritor común | **anticoagulación, antiagregante, vasopresor** |

El oxígeno no aparece: los guiones GI de la batería no piden oxígeno. Su brazo del mapeo se ejercita con una
prueba propia, por el mismo camino de órdenes.

### Los testigos de región, y lo que cambian

GI corría con un punto —el perfil comprometido— y la decisión docente prohíbe colapsar la incertidumbre de
la Fase 2 en un punto clínico. P3-11 añade dos testigos nombrados leídos del registro de calibración
congelado: `gi_region_lower` y `gi_region_upper`, las esquinas inferior y superior de la región declarada de
**29** magnitudes de perfil, más `gi_committed_default`. Tres reglas, todas negativas: una magnitud que el
registro sostiene (`lower == upper`) no es región y no se mueve; una magnitud que el perfil comprometido deja
sin valor es un mecanismo que la Fase 2 dejó **apagado** y un testigo nunca lo enciende; y ninguna magnitud
queda aprobada (0 de 58). Es una **esquina** de la región, no una distribución ni una afirmación de
correlación.

Por qué importa: el punto comprometido **es** un borde de su propia región en `lactate_per_output_deficit`
(inferior), `hypoxaemia_threshold_spo2` y `pump_preload_coupling` (superior), y está fuera del midpoint en
`lactate_clearance_tau_min`.

Dónde cae el motor heredado respecto de la región común, en **los 82 minutos comparados** de los 34
escenarios (no sólo en el último minuto de cada uno):

| Variable | Dentro | de los cuales por coincidencia exacta | Fuera | Región nula |
|---|---|---|---|---|
| `sbp` | 78 | 2 | 4 | — |
| `dbp` | 78 | 5 | 4 | — |
| `map` | 79 | 5 | 3 | — |
| `crt` | 72 | 32 | 10 | — |
| `hr` | 40 | 16 | 6 | 36 |
| `respiratory_rate` | 6 | 8 | 44 | 32 |
| `spo2` | — | 82 | — | 82 |

Y una advertencia que va en la lectura, no en una nota al pie: `LEGACY_WITHIN_COMMON_REGION` es
conservador y sólido —los testigos son esquinas de una región declarada, así que la región verdadera es al
menos igual de ancha—, pero `LEGACY_OUTSIDE_COMMON_REGION` **no** es la afirmación simétrica: el tramo es el
mínimo y el máximo de **tres** corridas nombradas sobre una caja de 29 magnitudes, así que un valor fuera de
ese tramo puede seguir estando dentro de la región declarada. Cada lectura lleva por eso el número de
testigos que abarca.

«Por coincidencia exacta» es la mitad honesta de la cuenta: cuando una variable **coincide** con el legado no
hay registro de divergencia del que leer el valor del legado, así que se usa el testigo estructural, y un
valor que ya es el testigo no puede caer fuera de su propia banda. Esas filas se cuentan aparte para que un
«dentro» que en realidad es «idéntico» no infle la lectura.

La lectura, que una comparación contra un punto no podía dar: el golden declara `sbp`, `dbp` y `map`
diferencias arquitectónicas en **todos** sus escenarios GI, y lo son contra el punto comprometido; contra la
región declarada caen **dentro** en 78, 78 y 79 de los 82 minutos, y sólo 2, 5 y 5 de esos son coincidencias.
Parte de lo que se lee como arquitectura es incertidumbre de parámetros. La frecuencia respiratoria es la
lectura contraria: 44 minutos fuera y la región no la rescata, porque la RR del legado es autorada donde la
común es impulsada (P2K-1, P2K-2); eso es arquitectura, no incertidumbre. Estar fuera de la región no dice
que el núcleo tenga razón: el motor heredado no es verdad clínica de referencia y ninguna magnitud de la
región está aprobada.

### El vacío de tratamiento, dicho sin adorno

En `D_incorrect_treatment` el residente da heparina y aspirina; en `F_start_stop` y
`K_combined_interventions` inicia y detiene noradrenalina. El motor heredado les da curso; el mapeo común no
tiene escritor para ninguno. En esos seis escenarios **no** aparece ninguna divergencia inesperada —el golden
ya declara arquitectónicas las presiones y la frecuencia—, así que «sin divergencias inesperadas» **no**
significa que la sombra sea fiel ahí. Por eso la cobertura se informa al lado de las clases, y por eso el
veredicto es:

**`GI_FULL_LIVE_SHADOW_EVIDENCE_NOT_READY`**, por dos bloqueos: el `TREATMENT_GAP` de anticoagulación,
antiagregante y vasopresor, y la lectura pendiente de las diferencias que el golden declara sólo en algunos
de sus escenarios (abajo). Todo lo demás que P3-11 pedía está cumplido: un camino de ejecución, la batería
completa, vivo = replay por construcción y por prueba, ningún escape de autoridad, los artefactos reproducen
y el digesto de la Fase 2 intacto. No inventé semántica para cerrar el vacío: un escritor de anticoagulación
o de vasopresor es fisiología nueva y decisión clínica, no una comodidad de este paquete.

### Lo que el golden declara en algunos escenarios y no en otros

Una declaración por escenario no es una probabilidad: el golden anota, escenario por escenario, qué variables
difirieron, y difieren **porque** ese escenario hizo algo. Así que «10 de 20» no explica nada por sí solo. La
clase `PARTIALLY_EXPLAINED_DIVERGENCE` deja de ser silencio: va con su conteo, los escenarios del golden que
la declaran y los que no, y **bloquea** la preparación hasta que una lectura docente la mire.

| Variable | Minutos | El golden la declara en | Escenarios de la batería |
|---|---|---|---|
| `hr` | 66 | 19 de 20 | 14 |
| `crt_s` | 50 | 18 de 20 | 11 |
| `V_ml_eq` | 46 | 10 de 20 | 9 |
| `consciousness_level` | 10 | **1 de 20** | 2 |

`consciousness_level` es el caso que forzó la regla y el que la revisión adversarial encontró silenciado: el
golden dice que **coincide** en 19 de sus 20 escenarios, así que llamar «parcialmente explicada» a una
diferencia suya era callar justamente la lectura que debe sonar fuerte. Su causa declarada es conocida —la
consciencia del núcleo es su escalera heredada, `LEGACY_REFERENCE_ONLY`, y P2L-2 no está cableado—, pero una
causa declarada no es una explicación de **este** escenario: eso lo decide la docencia.

### Comparabilidad por dominio, medida y no supuesta

Un dominio se leía `COMPARABLE` con que ninguna de sus variables fuera `NOT_COMPARABLE`, lo que también
cumple un escenario que nunca movió el dominio: el campo no decía nada. Ahora una variable cuenta sólo si
**alguno de los dos lados la movió**, y un dominio que nadie ejercitó lo dice:

| Dominio | Comparable | No ejercitado | No comparable |
|---|---|---|---|
| `HEMODYNAMICS` | 34 | — | — |
| `RESPIRATION` | 24 | 10 | — |
| `INTERVENTIONS` | 22 | 12 | — |
| `METABOLIC` | 18 | 16 | — |
| `HR_RHYTHM` | 16 | 18 | — |
| `CONSCIOUSNESS` | 4 | 30 | — |
| `OXYGENATION` | — | 34 | — |
| `COLLAPSE` | — | 34 | — |
| `ACID_BASE` | — | — | 34 |

`OXYGENATION` nunca se ejercita porque la batería GI no pide oxígeno; `COLLAPSE` tampoco, porque ningún
escenario GI llega al colapso; `ACID_BASE` no es comparable porque la tabla certificada de comparación no
tiene ninguna variable de ese dominio.

### Lo que cambió por la revisión adversarial de P3-11

Una revisión independiente de sólo lectura, con cuatro hallazgos ALTA y once MEDIA/BAJA. Los cuatro ALTA
eran reales y están corregidos con prueba propia; los once restantes también se atendieron.

| Hallazgo | Qué estaba mal | Qué rige ahora |
|---|---|---|
| ALTA · clasificación | `consciousness_level` se leía «parcialmente explicada» apoyándose en 1 de 20 escenarios del golden, es decir: el golden dice que coincide en 19 | la clase lleva su conteo y sus escenarios, y **bloquea** la preparación hasta que una lectura docente la mire |
| ALTA · identidad del encuentro | un segundo intento del **mismo** caso heredaba la sesión del primero: el generador es determinista, así que el id del caso no distingue dos intentos | la sesión se queda sólo mientras el reloj no retroceda ni vuelva a cero después de haber avanzado, y `reset_session` la suelta; la identidad del encuentro (digesto de la llegada) viaja en el artefacto |
| ALTA · apertura a mitad | una sesión abierta en el minuto N leía la llegada de un paciente ya tratado y rotulaba sus minutos como contados desde la llegada | una sesión sólo abre en el minuto 0; encender la bandera a mitad, recargar o reanudar corre sólo con el legado |
| ALTA · bandera por Secret | Streamlit copia cada secreto a `os.environ`, así que un `secrets.toml` podía encender la sombra sin que el preflight del piloto —que no puede llevar la fila— lo viera | una bandera que viene del archivo de secretos **no** se honra; es la puerta que reemplaza la fila que TD-130 no pudo añadir |
| MEDIA · digesto de la Fase 2 | la condición de seguridad comparaba la constante consigo misma: era verdadera por construcción | el digesto se **recalcula** sobre las 141 fuentes congeladas, y una prueba lo hace fallar a propósito |
| MEDIA · digesto del golden | toda la clasificación lee el golden y ningún digesto del artefacto lo cubría | el artefacto lleva el sha256 del golden de su familia |
| MEDIA · fallo de la sombra | ningún chequeo reportaba un fallo de sombra que **no** hubiera alcanzado el encuentro | la matriz publica los fallos y sus clasificaciones por escenario |
| MEDIA · `capture` fallido | si no se podía copiar el estado previo, las acciones del turno quedaban fechadas en el minuto 0 | no se espeja nada y el hueco dice por qué |
| MEDIA · comparabilidad | `COMPARABLE` lo cumplía también un escenario que nunca movió el dominio | cuenta sólo lo que alguno de los dos lados movió; lo demás es `NOT_EXERCISED` |
| MEDIA · nombre de la región | `OUTSIDE` nombraba la región completa | cada lectura dice cuántos testigos abarca, y el documento dice qué significa cada estado |
| MEDIA · procedimiento | cualquier recibo `procedure` se leía espejado en cuanto hubo una endoscopia | la lectura va atada al recibo de la endoscopia; otro procedimiento es un hueco |
| BAJA · minuto 0 del replay | el replay empezaba en el minuto 0 y cada lector le quitaba el primero a mano | `replay()` entrega los mismos minutos que el registro vivo y la llegada aparte |
| BAJA · tercer sitio de ejecución | el diagnóstico corría el núcleo por su cuenta | hay **un** sitio que deserializa un artefacto y lo corre, y los dos lectores pasan por él |
| BAJA · campo booleano | una condición devolvía una lista en vez de `False` | devuelve un booleano |
| BAJA · comentario obsoleto | «GI no lee banda» quedó falso al darle región a GI | describe la banda degenerada por variable que de verdad protege |

Las dos categorías que la revisión declaró limpias y vale la pena nombrar: ninguna acción espejada antes de
su destino ni dos veces dentro de un encuentro, y ningún artefacto serializado incompleto —los 34
reconstruyen sus digestos pasando por JSON, incluidos los que piden endoscopia y el de tres fluidos.

## P3-14 a P3-18 · La infraestructura dormida de autoridad limitada

Decisión docente del 2026-11-07: se autoriza **construir** la infraestructura de una primera autoridad
limitada, **no** activarla. Nada de lo que sigue cambia lo que ve un residente hoy, y el motor heredado sigue
siendo la única autoridad en tiempo de ejecución.

### El dominio, y lo que queda fuera

Familia `gi_bleed`, casos `gi_bleed_57m` y `gi_bleed_72f`, variables `sbp` y `dbp` con propiedad común y `map`
derivada en pantalla de las dos (`DERIVED_IN_DISPLAY`: el núcleo no la escribe). CRT queda diferida. Todo lo
demás —`hr`, `spo2`, `respiratory_rate`, `crt_s`, hemoglobina, lactato, `V_ml_eq`, consciencia, colapso, paro,
ritmo, pulso, la puntuación, el destino de las órdenes y la propiedad de la persistencia— es del legado, y
cuatro magnitudes internas (`D`, `delivery_rel`, `hemostasis_relief`, `transfusion_overload_units`) son sólo
comparación.

### La puerta: nueve condiciones, y una que no se puede cumplir

`authority_flag`, `approved_snapshot`, `family_and_case`, `environment`, `authority_domain`, `no_pilot`,
`no_unsupported_action`, `phase2_digest`, `layer_version`. `APPROVED_SNAPSHOTS` está **vacío a propósito**:
P3-14 no puede llenarlo, así que con la bandera y el entorno puestos el modo sigue siendo `legacy` y
`unreachable_because()` dice por qué. El modo se decide una vez, en el minuto 0.

### La transacción, y el fallo

`capture → compute → validate → commit`. Comprometer sin instantánea aprobada lanza `AuthorityRefused`; un
fallo de validación o de invariantes aborta, deja artefacto de retroceso con su razón y su historia y **no**
degrada en silencio (`HARD_FAIL_VISIBLE_TO_FACULTY`). El commit es atómico: o se escriben las dos presiones
comunes, o no se escribe ninguna; `map` se deriva de ellas al dibujar.

### La elegibilidad falla cerrada

Sobre los 34 escenarios de la batería GI: **28** quedan `ELIGIBLE_BUT_NO_SNAPSHOT` —elegibles en todo salvo en
la decisión docente que falta— y **6** `INELIGIBLE_UNSUPPORTED`, porque ordenan anticoagulación, antiagregante
o vasopresor y el mapeo común no tiene escritor. No se implementó ninguna de esas tres fisiologías para
desbloquear autoridad: sería fisiología nueva y decisión clínica. La comparación en sombra sigue corriendo en
los seis.

### El extremo a extremo, en la aplicación real

`test_runtime_authority_e2e.py` conduce `app.py` con `AppTest`: una transacción comprometida con una
instantánea inyectada **sólo para la prueba** cambia las tres presiones en pantalla y nada más; una rechazada
deja las del legado; seis fallos inyectados abortan; una sesión de piloto es inelegible; la traza de manejo no
cambia de dueño; y al terminar la prueba `APPROVED_SNAPSHOTS` vuelve a estar vacío. Que esa aprobación de
prueba no pueda existir en producción se verifica por AST (ningún escritor de `APPROVED_SNAPSHOTS` fuera de las
pruebas), por ausencia de artefacto y por el Decision File. Con esto queda cerrado
`UI_E2E_DEFERRED_BEFORE_AUTHORITY`.

### Lo que falta, y lo que no

El único paquete técnico que falta es el **sitio de llamada en producción** con el registro de procedencia del
minuto autoritativo, y está ausente a propósito: ningún módulo del tiempo de ejecución importa
`runtime_authority`. Lo demás son seis decisiones docentes (A–F), inventariadas con su material y su bloqueo en
`docs/PHASE3_ACTIVATION_READINESS_AUDIT.md`; el punto de la instantánea, con sus tres candidatos y el que el
propio núcleo rechaza, está en `docs/PHASE3_AUTHORITY_SNAPSHOT_DECISION_PACK.md`.

### Lo que cambió por la revisión adversarial de P3-17

Una revisión de sólo lectura sobre los nueve riesgos que el encargo nombró. Dos riesgos salieron limpios
—la interfaz no muestra salida común sin modo válido (`app.py` no menciona el arnés) y el commit no deja
el estado a medio escribir— y los otros siete traían hallazgos reales, con su sonda. Todos corregidos:

| Riesgo | Lo que encontró | Lo que ahora pasa |
|---|---|---|
| ALTA · elusión de la puerta | `AuthorityTransaction` tenía `state` como campo del constructor: construirla con `state=VALIDATED` saltaba la validación entera y comprometía frecuencia cardíaca, saturación y hemoglobina de un caso no permitido | `state` ya no es campo del constructor, y **`commit` vuelve a evaluar la puerta**: sin las nueve condiciones no escribe |
| ALTA · procedencia de la instantánea | `approved_snapshot` era una búsqueda por id: `{}` y hasta una cadena pasaban, y nada ataba el punto aprobado al punto que de verdad corrió | `snapshot_is_wellformed` exige forma, pertenencia al registro y **la misma `runtime_parameter_snapshot_id` que la capa reporta**; `validate` la usa |
| MEDIA · fuga de la aprobación de prueba | el registro era un `dict` de módulo: cualquier import podía llenarlo, y el escaneo de producción sólo veía el nombre desnudo | el registro se expone como `MappingProxyType` (escribirlo lanza), la inyección va a un nombre privado que el escaneo vigila, y el escaneo ve también las formas cualificadas, `update`, `setdefault` y los subdirectorios |
| MEDIA · propiedad mezclada | `commit` escribía `observable["map"]` aunque el contrato lo declara derivado: en 5 de 31 minutos de un escenario real el MAP guardado y el mostrado diferían en 1 mmHg | el commit escribe **sólo** lo que la tabla llama `common_authority`; el MAP de la pantalla es siempre función de esas dos presiones |
| MEDIA · acción no soportada ignorada | el argumento `unsupported` tenía valor por omisión, así que «nadie me dijo» se leía como «no hubo acción no soportada»; `SUPPORTED_ACTIONS` no lo leía nadie; y un gap declarado no bloqueaba la elegibilidad | el argumento **falla cerrado** sin valor; una clase marcada `FULLY_MIRRORED` que no esté en `SUPPORTED_ACTIONS` cuenta como no soportada; un gap declarado hace inelegible el escenario |
| MEDIA · el piloto habilitando autoridad | `MRS_PILOT` y `MRS_PILOT_RESIDENTS` no existen en ninguna otra parte del repositorio, así que un despliegue real del piloto cumplía `no_pilot` | la condición se ancla a las banderas que exige la **congelación del piloto** (`pilot_freeze.RUNTIME_FLAGS`) y falla cerrada si esa congelación no se puede leer |
| MEDIA · precedencia del espejo | en `_coverage`, «mapeado y espejado» se evaluaba antes que «hueco declarado», y `mirrored` es el conjunto de la sesión: una orden caída leía `FULLY_MIRRORED` porque otra de su clase sí se espejó | el hueco declarado gana; una acción sin tipo deja de desaparecer y se declara no soportada |
| BAJA · retroceso silencioso | `validate` devolvía `False` sin emitir nada, y `mode()` descartaba las razones de la puerta | `validate` **materializa** el artefacto de retroceso al refutar, y `mode_decision` devuelve el modo con su puerta y sus razones |
| BAJA · caché del digesto | `phase2_digest_now` estaba cacheado para todo el proceso: un cambio posterior en `clinical_core/` no podía disparar la condición | la caché va por nombre, tamaño y mtime de las 141 fuentes: un árbol cambiado es otra clave |

Tres hallazgos fuera de los nueve riesgos, también corregidos: el guardia «nada autoritativo lee la
sombra» quedaba auto-declarativo al excluir por `LAYER_SOURCES`, así que la prueba **fija la declaración
como literal**; la prueba de persistencia afirmaba más de lo que probaba, y ahora dice la verdad estrecha
—la carga útil es una lista blanca de claves de primer nivel y dos de ellas se copian **tal cual**, así
que no meter un registro de autoridad dentro de la traza cerrada es una obligación del sitio de llamada,
no una garantía del store—; y un `record()` con instantánea malformada lanzaba al intentar escribir su
propio artefacto de retroceso.

Lo que la revisión midió y conviene no perder: con cero configuración ya se cumplen seis de las nueve
condiciones, y con las tres variables de entorno puestas fallaba **sólo** la instantánea. Después de este
endurecimiento, además de la instantánea, una activación necesita declarar las acciones del minuto, correr
en un caso GI que el propio estado nombre, y pasar la puerta otra vez en el momento del commit.

## P3-19 a P3-25 · El sitio de llamada de producción, dormido

Decisión docente del 2026-11-07: se autoriza **construir** el punto de orquestación que faltaba, sin
activar nada. El motor heredado sigue siendo la única autoridad y ninguna configuración de este
repositorio puede abrir un sitio de autoridad.

### Lo que `app.py` hace, y lo que no

Una función de tres líneas (`_runtime_authority_site`) y un bloque de tres sentencias junto a la
observación en sombra. No decide nada: la bandera, la puerta de nueve condiciones, la instantánea que no
existe, la decisión de modo única y la memoria de la refutación viven todas en la capa. Una prueba fija el
bloque por AST, así que no puede crecer sin que se note.

Medido en la revisión adversarial: con la bandera apagada, **0,13 µs por turno y cero digestos de la Fase
2**. Con la bandera puesta y la puerta refutando, **un** digesto por llegada. El modo no puede aparecer a
mitad de encuentro, y un segundo intento del mismo caso no hereda el sitio del primero.

### Lo que un minuto de autoridad haría

`capture → compute → validate → commit`, con todos los digestos calculados **por el sitio**: el de la
entrada inmutable, el del candidato común, el del replay —que vuelve a correr el núcleo sobre el artefacto
serializado, de verdad— y el de la transacción. Se escriben `sbp` y `dbp` del núcleo común y la presión
media **como la deriva la pantalla**, para que el estado, la pantalla y la traza digan el mismo número.
Nada más se mueve, y el sitio lo comprueba comparando lo que llegó al estado con lo que el contrato
permite poseer.

### La batería completa, con la cuenta que salió

34 escenarios de la batería de aceptación de GI, conducidos por la lógica dormida con una instantánea sólo
de prueba: **26 técnicamente válidos** —26 de 26 comprometen atómicamente, reproducen su minuto y guardan
el contrafactual heredado— y **8 inelegibles**: seis por anticoagulación, antiagregante o vasopresor, y
**dos nuevos** por una orden que el propio motor declara que no modela. La cuenta anterior era 28 y 6; no
se forzó. Los tres candidatos de instantánea corridos sobre los mismos 34 artefactos: el comprometido y el
borde superior, 34 válidos cada uno; el borde inferior, 32 y dos fronteras no resueltas.

### El artefacto, y su límite

Cada minuto lleva su propia entrada inmutable, así que un experimento de tres minutos reproduce sus tres
minutos desde el artefacto solo. El digesto cubre todo el contenido y un artefacto editado deja de
reproducir; sin firma, detecta un cambio y no a un falsificador, y eso queda escrito. Un fallo duro
detiene la autoridad del encuentro para siempre y, si llega después de un commit, el artefacto declara la
trayectoria mezclada en vez de taparla.

### Lo que falta

Un paquete: **la superficie docente del experimento** —dónde se muestra un fallo duro y dónde se guarda el
artefacto— y la decisión docente de dónde vive. Las otras siete decisiones, con su material medido y su
registro de riesgos, están en `docs/PHASE3_FACULTY_AUTHORITY_DECISION_PACK.md`; la certificación final, en
`docs/PHASE3_PREAUTHORITY_FINAL_CERTIFICATION.md`.


## P3-26 a P3-30 · La superficie docente, el almacén del artefacto y el veredicto A

Cierra el último paquete técnico que quedaba abierto en P3-25, con la semántica que fijó la decisión docente
F. **Nada de esto concede autoridad**: el registro de instantáneas aprobadas sigue vacío.

### La superficie docente

`authority_status()` es la **única** lectura: devuelve modo, estado del experimento
(`NOT_STARTED` / `ACTIVE` / `HALTED` / `REFUSED`), id de la instantánea, dominio, intento, minuto, resultado,
razón del fallo, acciones no soportadas del minuto, minutos comprometidos, trayectoria mezclada,
disponibilidad del contrafactual del legado, identidad y digesto del artefacto, y política de fallo. La
superficie (`app.py::_render_authority_experiment`) **dibuja esa estructura y no deriva nada**: una prueba por
AST comprueba que no aparece ningún nombre de campo clínico en ella. Vive dentro de las herramientas de
personal, detrás de `faculty_access()`; el residente no la ve ni con el experimento detenido.

Si la sesión se perdió —un recargado, una sesión nueva— la superficie cae al almacén y lee los registros
durables en vez de mostrar «no hay experimento».

### El almacén del artefacto

`runtime_authority_store.py` es una superficie **separada** de investigación y depuración de la Fase 3:

- **Apagado por omisión.** Sólo existe si `MRS_PHASE3_AUTHORITY_STORE` nombra una **ruta absoluta fuera del
  repositorio**. Una ruta relativa, o cualquier ruta dentro del árbol, se rechaza con su motivo.
- **Crear-sólo.** Un registro nunca se sobreescribe. Volver a guardar contenido idéntico es idempotente;
  el mismo identificador con otro contenido es `COLLISION` y el primer registro queda como está.
- **Identidad determinista** sobre encuentro, experimento, intento, caso, último minuto, último resultado,
  número de minutos y sitio. **No** incluye el digesto del contenido, justamente para que un cambio de
  contenido bajo la misma identidad sea una colisión real y no un registro nuevo.
- **Versionado** (`STORE_VERSION`) y **reproducible**: cada minuto lleva su entrada inmutable, así que
  `store.replay(id)` reproduce el experimento completo desde el archivo.
- **Sin ampliar datos personales**: guarda lo que el artefacto del encuentro ya tenía.
- **Fuera del alcance del residente**: `RESIDENT_READERS_FORBIDDEN` nombra los módulos que no pueden leerlo
  y una prueba comprueba que el **único** lector es la superficie docente.
- `open_site()` **no abre un sitio** si no hay almacén configurado: un experimento sin dónde registrarse no
  empieza.

Nada de esto toca el esquema congelado de la traza de la Fase 2, la traza del residente, la salida del
encuentro, la puntuación ni los eventos críticos, y no hay ninguna migración de base de datos.

### La detención

Una falla dura deja el experimento en `HALTED/INVALID_FOR_CONTINUATION`. A partir de ahí: ningún minuto más
se compromete; el sitio **no se reconstruye** ni cambiando las banderas; un cambio de configuración dentro
del encuentro cuenta como falla y detiene visiblemente; los minutos ya comprometidos se preservan
exactamente como ocurrieron, sin mutación retrospectiva; si hubo commits antes de la falla, el artefacto
declara la trayectoria mezclada. Un encuentro nuevo, o un segundo intento del mismo caso, arranca un
experimento independiente. El encuentro detenido sirve para **reejecutar y analizar**, no para continuar.

### Lo que falta

Nada técnico. El veredicto de P3-29 es **A** (`TECHNICALLY_READY_FOR_EXPLICIT_FACULTY_AUTHORITY_GRANT`): los
18 puntos del inventario están `READY` y el detalle está en `docs/PHASE3_FINAL_TECHNICAL_READINESS.md`. Las
**seis** decisiones docentes que quedan (A instantánea, B criterio de aceptación, C exclusión por acción no
soportada, D alcance sólo presión, E entorno, G concesión expresa), la tabla de candidatos sobrevivientes y
la plantilla de autorización futura —no ejecutada— están en
`docs/PHASE3_FINAL_FACULTY_DECISION_PACK.md`.

### Enmienda 2 certificada en la sombra GI (2026-11-11)

El núcleo común vigente de esta rama es `PHASE2_AMENDMENT_2` (digesto `a0af7d08…`, integrado por merge sin fast-forward; el cierre
histórico y la Enmienda 1 se reconstruyen desde él). La enmienda está apagada por omisión y se declara **sólo** en tres testigos de
desarrollo de la sombra GI, cada uno su trayectoria; sin autoridad, sin exposición al residente, sin efecto en la puntuación, el primer
piloto sin cambios y sin que ningún estado de colapso o consciencia del núcleo termine un encuentro. Detalle, serie, comparación,
frontera y punto de control: `docs/PHASE3_AMENDMENT_2_GI_SHADOW.md` (filas FD-P3-167 a FD-P3-172). La revisión de la
temporalidad de la recuperación GI que le sigue: `docs/PHASE3_GI_RECOVERY_CALIBRATION_REVIEW.md` (filas FD-P3-173 a FD-P3-177). La instantánea de desarrollo de GI y la preparación de una autoridad de desarrollo (sin activarla):
`docs/PHASE3_GI_DEVELOPMENT_SNAPSHOT.md` y `docs/PHASE3_GI_AUTHORITY_READINESS.md` (filas FD-P3-178 a FD-P3-181). La ratificación de la instantánea y la revisión
previa a la autoridad (lectores de `mental_status`, presión en el núcleo activo, par en seco): `docs/PHASE3_GI_PREAUTHORITY_REVIEW.md` (filas FD-P3-182 a FD-P3-187).
