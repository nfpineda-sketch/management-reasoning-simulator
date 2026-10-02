# Readiness del piloto formativo limitado (posterior a V3, 2026-09-29)

Instrucción docente del 2026-09-29 (ampliación no clínica, punto 2). Actualiza
`docs/READINESS_PILOTO_RESIDENCIA.md` (ciclo 9), que queda como estaba.

**Este documento no autoriza nada.** No despliega, no invita residentes, no crea
cuentas reales y no inicia sesiones reales. Dice si el piloto está listo o
bloqueado, y por qué.

## Respuesta

**TECHNICALLY READY WITH CONDITIONS** (confirmado por el docente al cerrar el ciclo, 2026-09-29). Antes de
iniciarlo se requiere:

- **A.** desplegar el candidato y la configuración aprobados;
- **B.** la prueba de humo contra el entorno desplegado (la de abajo corrió en la versión real, en una base
  local desechable; `tools_pilot_smoke.py` crea su propia base temporal y puede correr en el servidor sin
  tocar sus datos);
- **C.** la autorización explícita del docente.

El piloto nunca se inicia automáticamente.

**Cómo cumplir A y B (ciclo 10):** `docs/RUNBOOK_PILOTO.md` — configuración, `tools_pilot_preflight.py` (dice si un despliegue está configurado como el piloto, sin imprimir secretos), prueba de humo automática y manual, respaldo y restauración probados (`docs/RESPALDO_Y_RESTAURACION.md`). Guías: `docs/GUIA_RESIDENTE_PILOTO.md` y `docs/GUIA_DOCENTE_PILOTO.md`, pendientes de su revisión.

**Al cerrar el ciclo 10 (2026-09-29):** la respuesta no cambia. Se agregaron integridad del store (TD-18 sin
I-F18), autor y hora de cada cambio de cuenta, respaldo y restauración probados en SQLite y PostgreSQL, el
runbook con su preflight, las guías, las pantallas del piloto (TD-42, TD-43, TD-38), DC4-F (opción B mínima) y
la deuda menor (TD-03, TD-05, TD-09, TD-10). La prueba de humo automática pasó en `351dcab`, sin llamadas al
proveedor. Lo que espera al docente está en `docs/PAQUETE_DECISIONES_CICLO10.md` (P-01 a P-12; revisiones R-1 a
R-5, entre ellas los borradores en español de R-4, que no se muestran hasta su aprobación).

**Respuesta docente al paquete (2026-09-30):** la respuesta sigue siendo la misma. Quedan implementados:

- P-01: la tiamina como medida complementaria de D3;
- P-06: el criterio de lisis del motor escrito en D3, C1 y TDFC;
- P-10: el portafolio completo de una cuenta inactiva, sólo para el administrador;
- P-11: 56/56 regresiones activas y 10 retiradas con su motivo.

Todo aplica sólo a encuentros nuevos donde corresponde; el detalle está en `docs/COLA_DECISIONES_AI_ADVISOR.md`.

**Segunda respuesta docente (2026-09-30):** la respuesta sigue siendo la misma. Quedan implementados, sólo en
encuentros nuevos:

- P-04, P-05 y P-06: la trombólisis del TEP;
- P-07: la 75f llega con la vista neutral;
- R-2: los criterios C14 de la 61m y la 70f;
- R-3: C3 parcial de la 29f;
- TD-46 y TD-47;
- R-4: la terminología de la sala.

El detalle está en `docs/COLA_DECISIONES_AI_ADVISOR.md`, sección «Segunda respuesta al paquete del ciclo 10».

**Antes de iniciar el piloto quedan estas revisiones humanas:**

- **R-2:** las 14 fichas POCUS de los casos C14 YES (`docs/revision/R2_POCUS_C14.md`); en la 61m y la 70f ya se
  aprobó el criterio, no la ficha.
- **R-4:** las 18 frases finales del motor en español (`docs/revision/R4_FRASES_MOTOR.md`).
- **R-5:** las dos guías y su firma (`docs/GUIA_DOCENTE_PILOTO.md`, `docs/GUIA_RESIDENTE_PILOTO.md`).

**Recomendado antes del piloto:** TD-48, el E-FAST de la sala que muestra sólo la ventana pericárdica (afecta los
dos casos de trauma). Está registrado, sin corregir. El piloto corre sin IA automática en el encuentro:
determinista y con casos offline.

**Revisión clínica prepiloto (2026-10-02):** la respuesta sigue siendo la misma.

- El paquete es `docs/revision/PRE_PILOT_REVIEW_PACKET.md`, con once decisiones abiertas (D-1 a D-11).
- TD-48 pasa de recomendable a **BLOCKER** para los dos casos de trauma; TD-50 es **BLOCKER** para
  `anaphylaxis_29f`. Ambos esperan su decisión.
- **Condición nueva de despliegue (TD-56):** la cuenta docente que firmó
  `assets/patient_images/approvals.json` debe existir antes del primer encuentro; si no, hay que
  reimportar el paquete de fotos.

**No es una validación.** La fidelidad del lector con texto externo sigue sin medirse (B = NOT YET MEASURED);
todo juicio lo confirma un docente.

## La IA en el primer piloto (decisión docente, 2026-09-29)

- **CLINICAL ENCOUNTER AI = OFF.** Ninguna llamada automática durante el encuentro y ninguna foto nueva
  generada al abrir el caso: banco de casos, fotos aprobadas y reutilizables, y el motor determinista. La
  configuración `MRS_OFFLINE_CASES=1` lo cumple: 0 llamadas medidas.
- **La IA posterior al encuentro no está autorizada:** propuesta de rúbrica, análisis del Trace, AI
  Longitudinal Review y traducción se deciden por separado, y ninguna se habilita automáticamente.
- **Objetivo del primer piloto:** reproducibilidad, trazabilidad y control.

## Prueba de humo (2026-09-29)

**Qué es.** `python3 tools_pilot_smoke.py`: base SQLite temporal, cuentas
propias sin nombres reales, la aplicación real (AppTest de Streamlit). Cada
intento de construir un cliente del proveedor de IA se registra y se rechaza.

**Dónde corrió.** Esta sesión, commit `d0cbeb8` (más la propia herramienta,
aún sin confirmar), `SIMULATOR_VERSION` `0.24.13-clinical-encounter`, motor de
familias 1, ejecución 0.24.2, `glucose_rescue` 2.0, rúbrica `1.0-pilot`,
cobertura 1.1, oportunidades 1.1. **No** en el entorno desplegado.

| Comprobación | Configuración del piloto | Configuración por defecto, con clave |
|---|---|---|
| Residente: abrir, comenzar, ordenar, cerrar, terminar | Sí, sin excepciones (inglés: `opioid_67f`; órdenes en español: `hypoglycemia_28m`) | Sí (`anaphylaxis_29f`; `hypoglycemia_54m_thiamine`) |
| Registro | Encuentro `completed`, Trace con su fila, `code_version` del commit y versiones de su evaluación congeladas | Igual |
| Foco de aprendizaje | Oculto al cerrar; visible para el residente después de la rúbrica confirmada (§154AB) | Igual |
| Revisión docente | Panel docente sin excepción; rúbrica confirmada por el docente | Igual |
| Páginas del residente (encuentros, progreso, portafolio), en inglés y en español | Sin excepciones | Sin excepciones |
| Documento del residente en español | Preparado sin llamar al proveedor | Igual |
| Permisos | Otro residente no lee ni lista el encuentro; el residente no confirma su rúbrica ni crea invitaciones; el docente no crea invitaciones; el docente lee el encuentro | Igual |
| **Intentos de llamar al proveedor** | **0** | **1: la foto de llegada (`image_broker`), al abrir el encuentro** |

**Lo que la prueba encontró y se corrigió antes de terminar:** el panel docente
fallaba («t() got multiple values for argument 'text'») en todo objetivo con
una fila TDFC YES, desde el ciclo 8. Corregido en `d0cbeb8`, con su prueba
(`test_screen_strings_name_their_values.py`). **Ninguna vulnerabilidad de
acceso encontrada.**

**Límites de la prueba.** AppTest no puede hacer clic con las pantallas en
español (busca el valor de un radio traducido entre sus opciones traducidas):
el encuentro en español se jugó con órdenes en español y pantallas en inglés, y
las pantallas en español se renderizaron aparte, sin clics. La reflexión se
escribió en el registro y se guardó por el store, como hace la prueba de la
aplicación completa. Son dos encuentros, no una medición de fidelidad.

## Configuración del piloto

| Variable | Valor | Por qué |
|---|---|---|
| `MRS_OFFLINE_CASES` | `1` | Casos autorados del banco y la clave del proveedor retenida en todas partes: **0 llamadas** medidas. Sin generación de casos ni de fotos, sin análisis por IA |
| `MRS_IMAGE_REQUIRE_REVIEW` | `on` | Sólo fotos con las dos revisiones humanas aprobadas (decisión 8 de imágenes) |
| `MRS_AUTH_MODE` | `accounts` | Cuentas por persona, permisos en los stores |

Con esta configuración **no hay** propuestas de rúbrica por IA, análisis del
Trace por IA ni traducciones a pedido: el docente puntúa y comenta. Habilitar
cualquiera de ellas es una decisión nueva (pregunta abajo).

## Casos, idiomas y versión

- **Casos:** los 31 casos del banco, que el currículo asigna por desafío y año
  de formación. `pulmonary_embolism_61m` **incluido**: corregido y verificado
  (lisis indicada por shock obstructivo desde la llegada, 98/61 a los 45 min).
- **Excluidos:**
  - las 9 composiciones de hipoglicemia (propuestas DC9 pendientes; no se
    exponen);
  - los casos escritos por IA (la configuración del piloto no los genera);
  - PS001/PS002 (motor antiguo, inaccesible).
- **Cerradas al final del ciclo (2026-09-29):** `anaphylaxis_63m_betablocked` muestra FA en el monitor y el
  ECG, coherente con su historia y su examen (DF-23 fila 7): **sigue incluido**; la pared reperfundida de los
  casos SCA queda aturdida, a lo sumo levemente disminuida (fila 6); una pregunta por embarazo o FUM responde
  «No documentado» si el caso no lo escribió, y la prueba de embarazo queda solicitada sin resultado (fila 8).
- **Casos con una limitación que el docente debe conocer** (se juegan igual):
  - `bradycardia_bb_54f` y `pulmonary_edema_75f`: vista neutral a la llegada (P-07; la aprobación clínica de
    V34 quedó pendiente para ese estado).
- **Idiomas:**
  - pantallas en inglés y en español;
  - órdenes en ambos idiomas, con la fidelidad externa sin medir;
  - el relato de cada caso en español sólo si un docente aprobó su traducción
    en la base desplegada. El paquete del repositorio no trae ninguna
    aprobación; en una base nueva el relato se ve en inglés.
  - `acs_70f_left_main`: su frase nueva en español está aprobada (2026-09-29); la sala la usa cuando la
    versión del caso está aprobada en la base desplegada.
- **Versión:**
  - cada encuentro congela al empezar su `code_version` (el commit desplegado
    o `MRS_CODE_VERSION`) y las versiones de su evaluación
    (`validation/BASELINES.md`, «Tres versiones distintas»);
  - un encuentro del piloto formativo no es una medición de validación
    externa.

## Supervisión docente

- Cada rúbrica la confirma un docente.
- La IA nunca asigna; no hay puntaje global, ranking ni tabla de posiciones.
- El foco de aprendizaje llega al residente después de la revisión.
- Las limitaciones conocidas son para el docente (`validation/KNOWN_DEFECTS_V3.md`,
  TD-45 en `docs/REGISTRO_DEUDA_TECNICA.md`), no instrucciones para el residente.

## Aprobaciones humanas que faltan

- Las condiciones A, B y C de arriba.
- Si el relato en español se usará: aprobar la versión de cada caso en la base desplegada (tablero docente).
- Cualquier función de IA, durante o después del encuentro: una decisión por función.
