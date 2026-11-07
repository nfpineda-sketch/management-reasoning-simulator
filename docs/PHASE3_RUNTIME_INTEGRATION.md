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
| `gi_bleed` | `gi_bleed_57m`, `gi_bleed_72f` | sí | **sí** | fluido, sangre, oxígeno, IBP, endoscopia | — |
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

1. `LIVE_SHADOW_UNIFICATION_DEFERRED`: la sesión en vivo (P3-1) y el runner genérico (P3-4) son dos
   implementaciones; unificarlas vuelve «vivo = replay» una propiedad estructural. Hoy comparten el único
   mapeo de intervenciones de GI (`runtime_shadow_families.gi_interventions`), que es lo que impide que
   divergan en silencio.
2. `LIVE_SHADOW_IN_STREAMLIT_LAYER`: el enganche de `app.py` existe y es de una línea, pero ninguna prueba
   automática conduce Streamlit; lo que se prueba es el mismo camino de órdenes sin Streamlit.
3. Vacíos de tratamiento en las cinco familias no GI.
4. El mapeo de impairment a categoría mental y los umbrales del colapso siguen siendo decisión docente.
5. `PILOT_PREFLIGHT_FLAG_GATE_DEFERRED`: el preflight del piloto no puede exigir las banderas ausentes sin
   mover un digesto congelado de la Fase 2. Hoy el piloto queda protegido por que ninguna de sus superficies
   nombra la bandera y por que un entorno limpio no abre sesión.
