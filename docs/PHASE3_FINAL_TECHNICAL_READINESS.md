# Fase 3 · P3-29 · Auditoría final de preparación técnica

Sólo lectura. **No concede autoridad, no aprueba ninguna magnitud clínica y no elige instantánea.**
Responde una sola pregunta: *¿queda algún bloqueador técnico antes de una concesión docente explícita de
autoridad?*

El inventario de abajo es el que pide P3-29. Cada fila nombra **dónde está implementado** y **qué prueba lo
demuestra** en este candidato; ninguna fila se apoya en una intención ni en un documento.

Convención: `READY` = implementado y probado; `READY_WITH_LIMITATION` = implementado y probado, con un
límite declarado que no impide la concesión; `TECHNICAL_BLOCKER` = falta algo que haya que construir antes.

## Inventario (18 puntos)

| # | Punto | Implementación | Prueba | Estado |
|---|---|---|---|---|
| 1 | Punto de llamada | `app.py::_runtime_authority_site()` (3 líneas) y un bloque de 3 sentencias junto a la observación en sombra; toda la decisión vive en `runtime_authority.site_for` | `d3`, `d15`, `d16`, `d17`, `s2`, `s10`, `e1`, `e13`, `e16` | READY |
| 2 | Compuerta | `AuthorityGate` y `gate()` con las nueve condiciones de `GATE_CONDITIONS`; `unreachable_because()` | `d1`, `n1` (11 controles negativos), `n1b`, `g8`–`g13`, `e4`, `e8`, `n5`, `e12` | READY |
| 3 | Mecanismo del registro de instantáneas | `APPROVED_SNAPSHOTS` (`MappingProxyType` sobre un dict vacío), `SNAPSHOT_REQUIRED_FIELDS`, `snapshot_is_wellformed()`, `approved_snapshot()` | `g20`, `g21`, `g9`, `e3`, `a*` del archivo de compuerta | READY — el **contenido** del registro es la decisión docente A, no una pieza que falte |
| 4 | Propiedad del dominio | `AUTHORITY_DOMAIN`, `ownership()`, `domain_is_coherent()`, `derived_map()`; `sbp`/`dbp` COMMON y `map` derivado como lo deriva la pantalla | `d7`, `d12`, `d20`, `e2`, `e5` | READY |
| 5 | Atomicidad | `AuthorityTransaction` con `PREPARED/VALIDATED/COMMITTED/ABORTED`, `capture→compute→validate→commit`, `rollback_artifact()` | `d7`, `d18`, `d23`, `g3`, `g7`, `g14`, `e14` | READY |
| 6 | Elegibilidad | `AuthorityEligibility`, `eligibility()`, `eligibility_battery()`; 34 escenarios GI, 26 `TECHNICALLY_VALID` / 8 `NOT_ELIGIBLE` | `g1`, `g2`, `g5`, `g6` | READY |
| 7 | Acciones no soportadas | `SUPPORTED_ACTIONS`, `STRUCTURAL_ACTIONS`, `action_kinds()`, `unsupported_among()`, condición `no_unsupported_action`; se comprueba **antes** de buscar el candidato del minuto | `d10`, `g4`, `g6`, `g16`, `s17`, `h6` | READY |
| 8 | Falla dura | `FAILURE_POLICY = HARD_FAIL_VISIBLE_TO_FACULTY`; `_hard_fail()` deja registro de reversión **también** sin transacción abierta; `_refusal()` con todos los campos de `ARTIFACT_MINUTE_FIELDS` | `d11`, `d13`, `e7`, `s5`, `s18`, `h1`, `h2` | READY |
| 9 | Semántica de detención | `EXPERIMENT_NOT_STARTED/ACTIVE/HALTED/REFUSED`, `INVALID_FOR_CONTINUATION`, `HALTED_KEY`; un sitio detenido no se reconstruye, un cambio de configuración detiene, la trayectoria mixta se declara | `h1`–`h5`, `s14`, `s15`, `s19`, `s24`, `d24` | READY |
| 10 | Visibilidad docente | `authority_status()` como lector único; `_render_authority_experiment()` dentro de `_render_staff_tools()`, detrás de `faculty_access()`; respaldo desde el almacén cuando la sesión se perdió | `s1`–`s5`, `s7`, `s24`, `h7`, `h8` | READY |
| 11 | Persistencia del artefacto | `runtime_authority_store.py`: directorio de registros JSON inmutables, apagado salvo que `MRS_PHASE3_AUTHORITY_STORE` nombre una ruta absoluta **fuera** del repositorio; crear-sólo, idempotente ante contenido idéntico, `COLLISION` ante el mismo identificador con otro contenido; `open_site()` no abre sin almacén configurado | `s6`–`s9`, `s13`, `s16`, `s21`, `s22`, `s23` | READY |
| 12 | Recuperación del artefacto | `store.paths/records/load/verify`; `verify_artifact()`, `minimal_artifact()`, `artifact_retention()` | `s11`, `s12`, `d8`, `d25`, `d27`, `g17`, `g18` | READY |
| 13 | Reejecución | `replay_input` **por minuto**, `replay_site_artifact()` con conteos y veredicto, `store.replay()` | `d14`, `d19`, `g15`, `g19`, `h6`, `s11`, `s20`, `n4` | READY |
| 14 | AppTest | Encuentro real de Streamlit: autoridad comprometida en pantalla, candidato rechazado, falla inyectada, pilotaje, encuentro propio de la app | `e1`, `e2`, `e5`, `e6`, `e7`, `e9`, `e13`, `e14`, `e16` | READY |
| 15 | Aislamiento de la puntuación | `n2` recorre el AST del camino de autoridad y no encuentra ninguna superficie de puntuación, rúbrica ni traza; `n3` corre un minuto de autoridad y compara los datos de puntuación antes y después | `n2`, `n3`, `s1`, `s9` | READY |
| 16 | Aislamiento del residente | El residente no ve el experimento ni cuando está detenido; la superficie vive detrás de la compuerta docente; `RESIDENT_READERS_FORBIDDEN` fija quién no puede leer el almacén | `h8`, `s2`, `s10`, `e2`, `e6` | READY |
| 17 | Exclusión del pilotaje | `PILOT_FLAGS`, `PILOT_REQUIRED_ON`, `looks_like_the_pilot()`, condición `no_pilot` | `e9`, `g11`, `n5`, y las superficies de pilotaje de `test_runtime_shadow_plumbing.py` | READY |
| 18 | Inmutabilidad de la Fase 2 | Condición `phase2_digest` sobre el digesto `22b90a6f…` de las 141 fuentes de `clinical_core/`; la capa de la Fase 3 vive fuera de `clinical_core/`; `DECLARED_CROSSINGS` fija los dos cruces declarados | `test_phase2_closure.py`, `test_shadow_core_isolation.py`, `g10`, `d9` | READY |

## Bloqueadores técnicos

**Ninguno.** El bloqueador que quedaba abierto al cerrar P3-25 —la superficie docente de la falla dura y la
persistencia del artefacto— está cerrado por los puntos 8, 10, 11, 12 y 13 de este inventario, con la
semántica que fijó la decisión docente F.

## Qué no demuestra esta auditoría

Esto es preparación **técnica**. No establece nada de lo siguiente, y ninguna de estas cosas se arregla con
más código:

- **Validez clínica de ningún punto de parámetros.** 0 de 58 regiones del registro de calibración de la
  Fase 2 están aprobadas por docencia.
- **Identificabilidad de cinco de las siete magnitudes de presión.** Con la evidencia de GI sólo
  `preload_curve_scale_ml` y `arrival_preload_fraction` mueven la presión (P3-21A); las otras cinco
  necesitan un valor nombrado que esta evidencia no distingue.
- **Tolerancias numéricas de aceptación clínica.** No existen y la IA no las inventa (decisión docente B).
- **Que un experimento de autoridad sea deseable.** La concesión es docente (decisión G).

## Veredicto final de P3-29

**A. TECHNICALLY_READY_FOR_EXPLICIT_FACULTY_AUTHORITY_GRANT**

Lectura exacta del veredicto: no queda ninguna pieza por construir para que una concesión docente explícita
pueda ejecutarse y ser auditada. La autoridad real sigue siendo **imposible** en este candidato: el registro
de instantáneas aprobadas está vacío y ninguna configuración que este repositorio pueda producir abre un
sitio de autoridad (`n1`, `n1b`, `n5`, `e12`, `g20`).
