# Fase 3 · P3-18 · Auditoría de preparación para una activación de autoridad limitada

Sólo lectura. **No activa nada, no aprueba ninguna magnitud y no concede autoridad.** Inventaría qué
decisiones docentes faltan, qué bloqueos técnicos quedan de verdad y cuál sería el alcance exacto de una
primera autoridad limitada, después de la reducción del dominio a presiones (decisión docente del
2026-11-07).

Rama `phase-3-runtime-integration`. El motor heredado sigue siendo la única autoridad en tiempo de ejecución:
`COMMON_CORE_RUNTIME_AUTHORITY = False`, `runtime_authority.APPROVED_SNAPSHOTS == {}` y la puerta de nueve
condiciones refuta con `NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS`. Comprobado hoy, no supuesto.

## 1 · El alcance exacto que se activaría, si docencia lo concediera

| | |
|---|---|
| Familia | `gi_bleed`, y sólo ella |
| Casos | `gi_bleed_57m`, `gi_bleed_72f` (lista cerrada) |
| Variables con autoridad común | `sbp`, `dbp` |
| Variable derivada | `map`, calculada en pantalla a partir de las dos anteriores (`DERIVED_IN_DISPLAY`), no escrita por el núcleo |
| Entorno | `development` o `faculty`, con bandera por proceso; el primer piloto excluido por bandera propia |
| Momento de decisión del modo | una vez, en el minuto 0 del encuentro; nunca a mitad |
| Instantánea | un punto nombrado y aprobado por docencia, citado por id en cada minuto autoritativo |
| Elegibilidad | falla cerrada ante una acción de manejo sin escritor común (anticoagulante, antiagregante, vasopresor) |

Fuera del dominio, y por tanto del motor heredado en cualquier activación de este alcance: `crt_s`, `hr`,
`respiratory_rate`, `spo2`, `hb_g_dl`, lactato, `V_ml_eq`, consciencia, colapso, paro, ritmo, pulso, la
puntuación, el destino de las órdenes y la propiedad de la persistencia. CRT queda **diferida** por decisión
docente, aunque su divergencia esté medida.

Lo que una activación de este alcance **no** cambiaría: la puntuación, las rúbricas, el radar, los D1–D5, el
libro de órdenes, la traza de manejo, lo que ve un residente en cualquier familia que no sea GI, y el primer
piloto.

## 2 · Decisiones docentes que faltan (A–F)

Ninguna es técnica; ninguna la puede tomar la IA.

| | Decisión | Qué bloquea hoy | Material preparado |
|---|---|---|---|
| **A** | **El punto de la instantánea.** Siete magnitudes a nombrar; sólo dos son identificables con la evidencia de GI (`preload_curve_scale_ml`, `arrival_preload_fraction`). Tres candidatos, uno rechazado por el propio núcleo | La condición `approved_snapshot` de la puerta. Sin A no hay activación posible, y `APPROVED_SNAPSHOTS` no se puede llenar sin decisión expresa | `docs/PHASE3_AUTHORITY_SNAPSHOT_DECISION_PACK.md` (P3-16) |
| **B** | **La lectura de las cuatro diferencias parcialmente explicadas** (`hr` 19/20, `crt_s` 18/20, `V_ml_eq` 10/20, `consciousness_level` 1/20). Quedan fuera del dominio de presiones, pero FD-P3-17 las declaró bloqueantes de la **preparación de la evidencia**: hay que decidir si una autoridad limitada a presiones puede avanzar con ellas abiertas como diagnóstico en sombra | El veredicto de evidencia de P3-11, no la puerta | FD-P3-17; `runtime_shadow.golden_conditions`; matriz de 34 escenarios |
| **C** | **El criterio de aceptación de una autoridad.** Hoy es estructural y causal, sin ninguna tolerancia numérica inventada, y el legado es comparador, no verdad de referencia. Docencia decide qué haría declarable aceptable una trayectoria común, y con qué evidencia | La declaración de aceptación, no el código | P3-16 §5 (conducta medida de los tres candidatos); `legacy_against_region` |
| **D** | **Los tres tratamientos sin escritor común** (anticoagulante, antiagregante, vasopresor). Hoy la elegibilidad **falla cerrada**: 28 de los 34 escenarios de la batería GI son elegibles y 6 quedan fuera por acción no soportada. Docencia decide si eso basta para una primera autoridad o si pide fisiología nueva, que es decisión clínica | Nada técnico: la regla ya falla cerrada | `runtime_authority.eligibility_battery` (28/6); FD-P3-15; TD-130 (8) |
| **E** | **La política de fallo.** Hoy `HARD_FAIL_VISIBLE_TO_FACULTY`: un fallo de validación o de invariantes aborta la transacción, deja artefacto de retroceso y no degrada en silencio al legado. Docencia confirma que prefiere el fallo visible a un retroceso invisible | Nada técnico; es una elección pedagógica con consecuencias en pantalla | `runtime_authority.FAILURE_POLICY`, `rollback_artifact` |
| **F** | **El primer experimento.** Entorno docente o de desarrollo, quién observa, qué se registra, y la aceptación expresa de que en esa pantalla las presiones no vengan del motor heredado. El primer piloto sigue congelado y sólo con el legado | La activación misma: sin F no hay encuentro donde correrla | FD-P3-07; banderas `MRS_PILOT`, `MRS_PILOT_RESIDENTS` |

## 3 · Bloqueos técnicos reales

**Uno, y está deliberadamente ausente: el sitio de llamada en producción y su registro de procedencia.**

Hoy ningún módulo del tiempo de ejecución importa `runtime_authority` (comprobado por AST: cero
importadores), así que la máquina existe y es inalcanzable. Para una activación haría falta, en un solo
paquete:

1. **El enganche**: en el arranque del encuentro, `encounter_mode(...)`; y por minuto, dentro del único
   camino de ejecución en sombra, `capture → compute → validate → commit` sobre el estado que la página
   dibuja, con el fallo duro visible si la validación no pasa.
2. **La procedencia del minuto autoritativo**: modo, id de la instantánea, digesto de capa y digesto de la
   Fase 2 escritos en el almacenamiento autorizado de la ejecución. Hoy el arnés produce esos registros
   (`record()`, `rollback_artifact`) y nadie los escribe, porque la propiedad de la persistencia está
   expresamente fuera del dominio.

Tres obligaciones que la revisión adversarial de P3-17 deja escritas sobre ese mismo paquete, y que ninguna
prueba de hoy puede cumplir en su lugar: calcular de verdad los dos digestos de reproducibilidad del minuto
—`validate` exige forma sha256, pero valen lo que valga quien los pasa—; escribir el artefacto de retroceso
que `validate` materializa al refutar, que es lo que hace visible el fallo duro; y **no** anidar el registro
de autoridad dentro de la traza cerrada ni de los eventos cerrados, porque la carga útil de producción copia
esas dos claves tal cual.

No hace falta fisiología nueva, ni tocar `clinical_core/`, ni cambiar la puntuación, ni ampliar el dominio.
P3-17 ya probó, en la aplicación real, que una transacción comprometida se dibuja en pantalla y que una
rechazada deja las presiones del legado: lo que falta es el llamador, no la capacidad.

**Lo que NO es bloqueo técnico**, y conviene no confundirlo con uno:

- `APPROVED_SNAPSHOTS` vacío: es la decisión A, y llenarlo sin ella está prohibido.
- Las cuatro diferencias parcialmente explicadas: están fuera del dominio de presiones y son diagnóstico.
- Las cinco magnitudes inertes en los cursos de GI: no hay evidencia de GI que respalde su valor, y eso es la
  decisión A, no un defecto.
- CRT: diferida por docencia, con su divergencia medida.
- Los vacíos de tratamiento de las cinco familias no GI y la integración de `clinical_physiology`: fuera de
  alcance (`MULTIFAMILY_LIVE_SHADOW_READY_ONLY_FOR_GI`, `GENERATED_CASE_ENGINE_INTEGRATION_DEFERRED`).
- `PILOT_PREFLIGHT_FLAG_GATE_DEFERRED`: el preflight del piloto no puede nombrar las banderas porque
  `pilot_freeze.py` está en el conjunto congelado de la Fase 2; hoy protegen al piloto la condición `no_pilot`
  de la puerta, que ninguna superficie del piloto nombre la bandera, y que un entorno limpio no abra sesión.
- El extremo a extremo de la interfaz: cerrado en P3-17 (`UI_E2E_DEFERRED_BEFORE_AUTHORITY` ya no aplica).

## 4 · Lo que esta auditoría comprobó hoy

| Comprobación | Resultado |
|---|---|
| `APPROVED_SNAPSHOTS` | `{}` |
| `unreachable_because()` | `APPROVED_SNAPSHOTS is empty: no faculty-approved authority snapshot exists` |
| Puerta con la bandera y el entorno puestos, sin instantánea | `mode(...) == "legacy"` |
| Importadores de `runtime_authority` en el tiempo de ejecución | ninguno (AST) |
| Propiedad del dominio | `sbp`, `dbp` comunes; `map` derivada en pantalla; 16 variables heredadas; 4 sólo comparación |
| Elegibilidad en la batería GI | 28 elegibles por falta de instantánea, 6 inelegibles por acción no soportada |
| Digesto de la Fase 2 | `22b90a6f7f38…` recalculado sobre las 141 fuentes |
| `clinical_core/`, `family_engine.py`, `pilot_freeze.py` | sin cambios |
| Puerta con la bandera, el entorno y una instantánea de prueba, sin declarar las acciones | refuta: `no_unsupported_action` falla cerrado |
| Puerta con las banderas que exige la congelación del piloto | refuta: `no_pilot` anclado a `pilot_freeze.RUNTIME_FLAGS` |
| Instantánea con otra `runtime_parameter_snapshot_id` que la que corrió la capa | refuta: la procedencia no se puede suplantar |
| Encuentro propio de la aplicación (caso que no es GI) | refuta: la familia la decide el estado, no el llamador |

## Veredicto

**`ONE_TECHNICAL_PACKAGE_REMAINS`** — queda exactamente un paquete técnico, el sitio de llamada en producción
con su registro de procedencia, y está ausente a propósito porque su presencia haría activable la autoridad.
Todo lo demás que falta son las decisiones docentes A–F. La lista de verificación de autorización futura no se
emite aquí: corresponde al veredicto `TECHNICALLY_READY_FOR_EXPLICIT_FACULTY_AUTHORITY_GRANT`, y este no lo es.
