# AI Longitudinal Review · especificación (diferida)

Ciclo 9 · 2026-09-29 · §154AT–§154BZ, §154CV–§154DI, §154EU–§154FL y §154FS de la
instrucción docente.

**Estado: ESPECIFICADO, NO IMPLEMENTADO.** La función está aprobada en concepto
(§154CV). Se difiere porque §154FS pide implementarla sólo si todo lo siguiente
se cumple, y el último punto no se cumple en este ciclo:

| Condición (§154FS) | Estado al cierre del ciclo 9 |
|---|---|
| V3 congelado | Sí |
| Ingesta externa lista | Sí |
| Permisos robustos | Sí, con las pruebas agregadas en esta fase (`docs/MATRIZ_PERMISOS_ROLES.md`) |
| Aislamiento de residentes verificado | Sí, en cada store (auditoría de interfaz del ciclo 9) |
| Evidencia confirmada consultable de forma fiable | Sí (ver «Contrato de datos») |
| Presupuesto suficiente | **No:** P1 y P2 de roles primero (§154FR: «No sacrifiques P1/P2 por P3») |

Una especificación robusta es preferible a una implementación rápida e insegura
(§154FS).

## 1. Qué es y qué no es

- **Pregunta que responde:** ¿qué patrones sostiene la evidencia observacional
  disponible de este residente? (§154AU)
- **No responde:** si el residente es competente, qué puntaje merece ni qué nivel
  de Milestone o EPA le corresponde.
- **Salida consultiva (ADVISORY OUTPUT ONLY).** No modifica el Management Trace,
  la rúbrica, D1–D5, el progreso por objetivo, la evidencia de Decision
  Challenges, TD/F/C, ACGME o Royal College, los eventos de seguridad, la
  confirmación docente ni el portafolio (§154BG).
- **Privada del Admin al comienzo.** No aparece en la cuenta del residente, no
  genera notificaciones ni correos (§154BI, §154DH). Faculty conserva toda la
  evidencia primaria.

## 2. Contrato de datos (paquete de evidencia)

Se arma de forma **determinística**, con los stores existentes y el token del
Admin, para **un solo residente** (§154BO, §154BP). Nada se lee sin pasar por la
verificación de rol de cada store.

| Bloque | Fuente (store, método) | Qué entra | Qué no entra |
|---|---|---|---|
| Encuentros | `AccountStore.list_attempts` filtrado por `user_id` del residente; `get_attempt` | id, fecha, desafío, estado, idioma, contexto clínico (familia/caso) | sandbox, intentos activos o abandonados, otros residentes |
| Rúbrica | `RubricStore.progress(token, user_id)` | revisiones **confirmadas**: puntajes D1–D5 (con «no evaluable»), eventos críticos confirmados, revisor, fechas | propuestas de IA, borradores |
| Observaciones | `ProgressStore.get_progress(token, user_id)` | observaciones confirmadas por objetivo (R*, TD1, F1, C1–C4, C14, C15), con su encuentro | anuladas; sugerencias pendientes |
| Contribuciones de marco | `competency_mapping` y los campos `acgme` / `royal_college` del desafío | vínculos DIRECT/PARTIAL ya aprobados | niveles, porcentajes o «completado» |
| Management Trace | `ManagementTraceStore` (análisis del residente) y el Trace del encuentro | extractos por referencia (§154FG: muestreo sin perder información: las decisiones que sostienen cada observación, no el Trace completo) | razonamiento de otros residentes |
| Seguridad | eventos críticos **confirmados** de las revisiones | evento, fecha, encuentro | candidatos de IA |

- **Cada ítem lleva un identificador** (`E-<attempt>`, `O-<observation>`,
  `R-<review>`, `S-<event>`). El modelo sólo puede citar identificadores del
  paquete (§154DA).
- **Corte de evidencia:** la fecha de la evidencia más reciente incluida (§154BK).
- **Tamaño:** se informa antes de generar (número de encuentros, observaciones,
  revisiones, tokens estimados de forma determinística), sin una llamada de IA
  para estimar otra (§154CX).

## 3. Prompt

- **Versión explícita:** `longitudinal_review_v1`; un cambio es una versión nueva
  y nunca reinterpreta revisiones anteriores (§154DE).
- **Instrucciones obligatorias:**
  - evidencia primero: toda conclusión cita identificadores del paquete (§154AV);
  - limitada ≠ débil: con poca evidencia, «evidencia insuficiente», nunca
    «debilidad» (§154AW, §154DC, §154BS); el dominio más bajo no es por sí una
    debilidad (§154BA);
  - sin tendencia con 1–2 observaciones y sin puntaje de progresión (§154BB);
  - seguridad como señal independiente, sin compensarla con promedios (§154BV);
  - contexto clínico descriptivo, sin puntaje de diversidad (§154BT); cronología
    descriptiva, sin ponderación temporal (§154BU);
  - discordancia entre docentes descrita, no resuelta (§154BW);
  - marcos: «se ha observado evidencia relacionada con C1 en…», nunca «C1
    logrado», nivel de Milestone ni EPA completa (§154BR);
  - observado frente a inferido, sin causalidad inventada (§154EV, §154EW).
- **Independencia de modelo:** paquete → prompt → modelo → revisión estructurada,
  con el proveedor como parámetro, sin una abstracción excesiva (§154CY).

## 4. Salida estructurada y su validación

```
EVIDENCE_AVAILABLE      encuentros, observaciones, n por dominio, marcos, eventos, rango de fechas
STRENGTHS[]             {pattern, evidence_ids[], domains/objectives, rationale}
AREAS_FOR_DEVELOPMENT[] {pattern, n_and_context, why_it_matters, evidence_ids[]}
LIMITED_EVIDENCE[]      {area, n, note}
LONGITUDINAL_PATTERNS[] {kind: improving|stable|inconsistent|persistent|insufficient, evidence_ids[]}
SAFETY_SIGNALS[]        {event, date, encounter_id, evidence_ids[]}
ACTION_PLAN[]           {goal, why, evidence_ids[], action, observe_next, useful_new_evidence}
EVIDENCE_REFERENCES[]   ids usados
```

- **Validación determinística:** cada identificador devuelto debe pertenecer al
  paquete; si no, la afirmación se marca **INSUFFICIENT SUPPORT** o se excluye,
  nunca se «arregla» (§154DA, §154DB).
- **Plan de acción dentro de sus límites:** más observación, simulación dirigida,
  un Clinical Challenge ciego, debriefing, práctica deliberada, simulación de
  procedimientos u observación en el lugar de trabajo. Nunca cambia un puntaje o
  una rúbrica, asigna competencia, asigna un desafío ni notifica (§154DD, §154BF).
- **Largo acotado** y sin precisión que no existe («18 % de mejora») (§154FD,
  §154FE, §154BM).

## 5. Persistencia y procedencia

Una tabla nueva (`mrs_longitudinal_reviews`), sólo de inserción:

| Campo | Contenido |
|---|---|
| `id`, `resident_user_id`, `requested_by` | quién pidió y de quién |
| `generated_at`, `evidence_cutoff` | cuándo y hasta qué evidencia (§154BK) |
| `n_encounters`, `n_confirmed_observations` | cuánto sustentó el análisis |
| `provider`, `model`, `prompt_version` | con qué (§154BK, §154DE) |
| `package_sha256` | la huella del paquete, para auditar qué sabía el sistema |
| `output_json`, `validation_json` | la salida tal como vino y lo que la validación marcó |
| `status` | `generated`, `failed`, `dismissed` |

- **Regenerar crea una revisión nueva;** nunca sobrescribe (§154DF, §154BL).
- **Una capa humana aparte** (`mrs_human_plans`) si el Admin acepta como
  referencia o redacta un plan: la salida original de la IA no se edita (§154DG,
  §154BH, §154BJ). El plan aprobado por una persona es otra cosa que la revisión
  de IA y es lo único que podría llegar al residente, en un ciclo futuro.

## 6. Permisos

| Acción | Resident | Faculty | Admin |
|---|---|---|---|
| Generar | NO | NO | SÍ, a pedido |
| Ver | NO | NO (por ahora) | SÍ |
| Descartar, crear nota o plan humano | NO | NO | SÍ |
| Abrir el flujo de asignación desde una sugerencia | NO | NO | SÍ: abre el selector normal; una persona elige (§154BZ) |

Todas se verifican en el store, con `_actor(connection, token, {"admin"})`, no
sólo en la interfaz (§154CB). El paquete de un residente no puede incluir
evidencia de otro: la consulta filtra por `user_id` dentro de la misma
transacción, y una prueba lo verifica con dos residentes sintéticos (§154BP).

## 7. Costo y ejecución

- **Sólo a pedido del Admin**, con una confirmación previa que dice: «Este
  análisis usa la evidencia confirmada por docentes disponible hasta [fecha]. Es
  consultivo y no modifica el registro del residente» (§154BX, §154BN).
- **Nunca automático:** ni al iniciar sesión, ni al cargar un perfil, ni tras un
  encuentro, una rúbrica o un portafolio (§154FT).
- **Una llamada por revisión,** con el paquete mínimo; sin llamadas para estimar
  costos (§154CX, §154FF).

## 8. Fallas

- **Falla del modelo** (tiempo, cuota, respuesta inválida): se registra como
  `failed`, con su causa; no se muestra nada como revisión y no se reintenta solo
  (§154FI).
- **Falla de validación** (identificadores inexistentes, esquema): la afirmación
  queda marcada o excluida; si nada sobrevive, se registra como falla de
  validación (§154FJ).
- **Rótulo humano** en todo resultado: «AI-GENERATED ADVISORY ANALYSIS · REQUIRES
  HUMAN REVIEW» (§154FK, §154BH). Nada de la revisión penaliza al residente
  (§154FL).

## 9. Interfaz

En la vista del residente del Admin, separada visualmente del registro oficial:

```
AI LONGITUDINAL REVIEW
Generated [fecha] · Evidence through [fecha] · longitudinal_review_v1 · [modelo]
Advisory — human review required.

Evidence available · Observed strengths · Areas for development · Limited evidence
Longitudinal patterns · Safety · Suggested action plan
[Ver evidencia]  [Crear nota o plan humano]  [Descartar]  [Abrir asignación de desafío]
```

## 10. Pruebas necesarias antes de habilitarla

1. Sólo el Admin genera y ve; Faculty y Resident son rechazados en el store.
2. Aislamiento: con dos residentes sintéticos, el paquete de A no contiene nada de B.
3. Sólo evidencia confirmada: propuestas, borradores, anuladas y sandbox quedan fuera.
4. Identificadores: una referencia inventada se marca como sin soporte.
5. Regenerar no sobrescribe; cada revisión guarda corte, modelo y versión del prompt.
6. Ninguna llamada automática: cargar perfiles, confirmar rúbricas o generar el
   portafolio no llama al proveedor (proveedor simulado que falla si se llama).
7. La salida no cambia D1–D5, la rúbrica, el progreso ni los eventos.
8. El residente no ve la revisión ni recibe notificaciones.
9. Pruebas sólo con datos sintéticos y salida simulada (§154CW); nunca con
   participantes de la validación externa ni residentes reales.
