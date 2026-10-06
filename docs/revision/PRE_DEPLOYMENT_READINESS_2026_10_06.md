# Preparación para el despliegue · piloto con residentes (2026-10-06)

**Encargo:** «PRE-DEPLOYMENT READINESS — RESIDENT PILOT» (2026-10-06). Determinar si el build congelado de la Fase 0
está listo para desplegarse en el entorno real del piloto. **No es la Fase 1, no reabre la Fase 0 y no despliega.**

**La Fase 0 quedó cerrada en `009aadb`** («PHASE 0 — CLOSED», 2026-10-06). Su informe
(`docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`) no se modifica: su sección 20 dice «Push: ninguno», y después el
push se autorizó y se hizo (merge `009aadb` sobre `bc99b41`, con los dos commits del remoto). Este documento no
cambia esa historia; la completa.

**Decisión:** **NOT READY FOR DEPLOYMENT** (sección 13). Bloqueos explícitos en la sección 10.

Fuente de verdad del congelamiento: el manifiesto ejecutable `docs/revision/PILOT_FREEZE_MANIFEST.md` (generado de
`pilot_freeze.py`). Donde un texto lo contradice, se informa en la sección 10.2 y no se corrige aquí.

## 1. Línea de base

| Comprobación | Resultado |
|---|---|
| Rama | `clinical-encounter-v0.13` |
| HEAD local = `origin/clinical-encounter-v0.13` | `009aadb4c527e34b893ed9b858d1158b7977dd53` (ambos) |
| Árbol de trabajo | Limpio al empezar y durante las corridas (`git status --porcelain` vacío) |
| `bc99b41` (cierre de la Fase 0) y `009aadb` en la historia | Sí; 0 commits después de `009aadb` al empezar |
| Lector (`family_parser.py`, `shared_order_language.py`, `active_order_context.py`), corpus de validación, V3, baselines | Sin tocar. No se abrió ninguna respuesta externa |

## 2. Commit candidato

- **Candidato del runtime: `009aadb`.** Es el build que la Fase 0 verificó y el que se verificó de nuevo aquí
  (sección 9).
- Este documento y su commit (`PRE-DEPLOYMENT`, local, sin push) sólo agregan documentación: el runtime de cualquier
  commit posterior que sólo toque `docs/` es idéntico al de `009aadb` (comprobable con
  `git diff --stat 009aadb HEAD -- . ':(exclude)docs'`, que debe salir vacío).
- `MRS_CODE_VERSION` debe ser el commit que efectivamente se despliegue (sección 3.2). Si se despliega un commit de
  sólo documentación, ése es el que se registra.

## 3. Requisitos del entorno

Los Secrets del entorno del piloto **no son accesibles desde este entorno**: ningún valor actual se pudo leer. Los
valores secretos se informan sólo como PRESENT / MISSING / UNKNOWN; aquí, todos UNKNOWN.

### 3.1 Tabla de indicadores (manifiesto, runbook y readiness)

| Indicador | Valor exigido | Valor actual / disponible | Estado | Fuente del valor | ¿Bloqueo? |
|---|---|---|---|---|---|
| `.streamlit/config.toml` `[runner] fastReruns` | `false` | `false` en `009aadb` (archivo del repositorio) | OK en el código | Repositorio | NO |
| `MRS_OFFLINE_CASES` | `"1"` (texto o entero; **nunca** booleano TOML, ver 3.3) | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo |
| `MRS_PAID_GENERATION` | `"off"` (texto; nunca booleano TOML) | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (el preflight sólo lo recomienda) |
| `MRS_FREE_GENERATION` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (el preflight sólo lo recomienda) |
| `MRS_DEFAULT_VARIANT` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** (salta la exclusión, 5.2; el preflight sólo avisa) |
| `MRS_REPLAY_CASE` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (el preflight falla si está) |
| `MRS_CODE_VERSION` | el commit desplegado | UNKNOWN; candidato `009aadb4c527` | UNKNOWN | Secrets → entorno; si falta, `git rev-parse` del checkout | **SÍ** hasta verificarlo (3.2) |
| `MRS_IMAGE_REQUIRE_REVIEW` | `"on"` | UNKNOWN | UNKNOWN | Secrets (la app lo lee también de `st.secrets`) | **SÍ** hasta verificarlo |
| `MRS_AUTH_MODE` | `"accounts"` | UNKNOWN | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `MRS_DATABASE_URL` (secreto) | URL PostgreSQL del proveedor con `sslmode=require` | UNKNOWN (PRESENT/MISSING no verificable) | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `OPENAI_API_KEY` (secreto) | **ausente** (runbook §2: «retírela»; aquí, obligatorio por 3.3) | UNKNOWN | UNKNOWN | Secrets | **SÍ** |
| `MRS_ADMIN_USERNAME`, `MRS_ADMIN_PASSWORD_HASH` (secreto) | sólo hasta crear el primer administrador; después, ausentes | UNKNOWN | UNKNOWN | Secrets | NO (paso del runbook) |
| `MRS_ALLOW_LOCAL_SQLITE` | ausente | UNKNOWN | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `MRS_SYNTHETIC_ACCOUNTS`, `MRS_BATCH_*` | ausentes | UNKNOWN en el destino. El contenedor de desarrollo de esta revisión sí tiene `MRS_BATCH_*` definidas: no es el destino | UNKNOWN | Secrets / entorno | **SÍ** hasta verificarlo |
| Python | 3.11 (probado: 3.11.15) | UNKNOWN: Streamlit Community Cloud lo fija al crear la app; el repositorio no lo fija | UNKNOWN | Configuración de la app | **SÍ** (sección 8) |
| Streamlit | 1.64.0 (probado) | `requirements.txt` admite `>=1.41,<2`; PyPI publica hoy **1.65.0**: una instalación nueva tomaría 1.65.0, verificada hoy en la Fase 0 y en 0D, no en la suite completa (9.4) | RIESGO | `requirements.txt` | **SÍ** (sección 8) |
| Rama que despliega la app | una rama fija en el commit aprobado, sin pushes durante el piloto | UNKNOWN: la app y la base del piloto no están identificadas en el repositorio | UNKNOWN | Configuración de la app | **SÍ** (3.2) |

### 3.2 Contrato de versión

- **Cómo se fija:** `curriculum_runtime.code_version()` lee `MRS_CODE_VERSION` del entorno (Streamlit copia ahí las
  claves raíz de texto de los Secrets); si falta, `git rev-parse --short=12 HEAD` del checkout; si tampoco, `unknown`.
  Se calcula una vez por proceso.
- **Dónde queda:**
  - al iniciar el encuentro, `encounter.assignment.code_version` (con `runtime_version`) y
    `evaluation_basis.code_version` (congelado con la declaración del caso);
  - en cada turno, `code_version` de la fila del Management Trace y `trace_extensions.versions.code_version`.
- **Quién lo ve:** el docente, sólo en la exportación JSON («Complete encounter record and export» → «Download
  faculty record»); la revisión renderizada no lo muestra.
- **Un encuentro conserva la versión con que empezó** (asignación y base congelada) y cada turno registra el código
  con que corrió: un despliegue a mitad de encuentro queda visible después en el registro (TD-10).
- **«No desplegar con encuentros del piloto abiertos»: la regla es sólo documental** (runbook §2). Ningún código ni
  herramienta la hace cumplir, y ninguna herramienta lista los encuentros abiertos. Además, según el propio
  repositorio (`docs/TANDA_LOCAL.md`, 2026-09-25):
  - la app de Streamlit Cloud se redespliega al recibir un push en la rama que sigue, y cortaría un encuentro en
    curso;
  - después de un push, la app sigue ejecutando los módulos ya importados hasta «Reboot app»: código viejo y nuevo
    pueden convivir en un mismo proceso;
  - con `MRS_CODE_VERSION` fijo en los Secrets, un redespliegue registraría un SHA que ya no es el que corre.
- **Procedimiento propuesto (documental, para decisión):**
  1. la app del piloto despliega una rama propia que apunta al commit aprobado y que nadie empuja durante el piloto
     (la de desarrollo, `clinical-encounter-v0.13`, sigue recibiendo commits);
  2. antes de cualquier redespliegue, contar los encuentros abiertos, sólo leyendo:
     `SELECT COUNT(*) FROM mrs_attempts WHERE status = 'active' AND is_sandbox = 0;` (debe ser 0);
  3. en la misma ventana: push, «Reboot app» y `MRS_CODE_VERSION` actualizado.

  Un encuentro que el residente deja abierto queda `active` indefinidamente: cómo cerrarlo antes de una ventana de
  mantenimiento es una decisión operativa pendiente.

### 3.3 Hallazgo verificado: el preflight puede decir «LISTA» sin que la app quede sin conexión

- **Qué pasa.** Streamlit copia al entorno sólo las claves raíz de los Secrets cuyo valor TOML es texto, entero o
  decimal; un booleano no se copia. `offline_cases.py` lee `MRS_OFFLINE_CASES` y `MRS_PAID_GENERATION` **sólo del
  entorno**. `tools_pilot_preflight.py` lee el archivo TOML y convierte cada valor a texto.
- **Reproducción** (valores ficticios, cargador real de Streamlit 1.64.0, en el directorio de trabajo de la sesión):
  con `MRS_OFFLINE_CASES = true` y una clave del proveedor ficticia:
  - el preflight: 12 reglas OK y «Configuración del piloto: LISTA.»;
  - la app: `MRS_OFFLINE_CASES` no llega al entorno, `offline_cases_enabled()` es falso y la clave **no** se
    retiene (`withhold`).
- **Consecuencia** (leída en el código; no se hizo ninguna llamada): con la clave presente, cada pregunta de historia
  del residente construiría el cliente del proveedor (`answer_history` → `patient_conversation.answer_from_sources`),
  en contra de «Sin IA automática durante el encuentro del primer piloto». Si además `MRS_PAID_GENERATION = false`
  (booleano), la generación pagada de fotos quedaría permitida y la de casos libres, abierta al administrador. Los
  casos del banco se siguen sorteando igual (`launch_options`). La prueba de humo en su configuración «default»
  (clave ficticia, sin modo sin conexión) no pasa por esos caminos: registró 0 intentos, lo que no prueba que no
  existan.
- **Sin la clave en los Secrets, nada de eso puede ocurrir.** Por eso aquí la ausencia de `OPENAI_API_KEY` es
  obligatoria, y los valores se escriben entre comillas: `MRS_OFFLINE_CASES = "1"`, `MRS_PAID_GENERATION = "off"`,
  `MRS_IMAGE_REQUIRE_REVIEW = "on"`, `MRS_AUTH_MODE = "accounts"`.
- No se verificó si Streamlit Community Cloud carga los Secrets por otro camino; el procedimiento de arriba vale en
  ambos casos.
- **Corrección propuesta, no aplicada** (sección 10.1, B-3).

## 4. Base de datos y proveedor

### 4.1 PostgreSQL local, descartable, con TLS obligatorio

- **Entorno:** PostgreSQL 16.13, clúster creado para esto en el contenedor de desarrollo, en 127.0.0.1:55432, sin
  red externa ni datos reales; **nunca producción**. En esta revisión se configuró como un proveedor alojado: la
  conexión TCP sin TLS se rechaza (`hostnossl … reject`) y la conexión con `sslmode=require` usa TLS 1.3
  (certificado autofirmado y descartable).
- **Resultados sobre `009aadb`** (árbol limpio; detalle en 9.2):
  - las cuatro pruebas de PostgreSQL del repositorio, **23 de 23**, con A–G del encargo: A guardado previo, B
    segundo clic, C recarga antes de correr, D recarga después, E ejecución detenida (una y dos veces), F conflicto de
    revisión entre dos sesiones y G la orden escrita después de una respuesta (F0-12);
  - el simulacro de respaldo y restauración (`tools_backup_drill.py --postgres`), **aprobado**;
  - las consultas de sólo lectura de 3.2 y 11.1, comprobadas.

### 4.2 Proveedor del piloto

**PROVIDER POSTGRES SMOKE — BLOCKED / NOT RUN.**

- No hay acceso desde este entorno a una base descartable equivalente a la del proveedor (Neon, según
  `docs/CLINICAL_DEV_DATABASE.md`; ese mismo documento y `docs/IMAGENES_REGISTRO.md` registran que este entorno no
  llega a Neon), y no se probó contra producción.
- La versión mayor de PostgreSQL del proveedor no está documentada en el repositorio (UNKNOWN).
- La latencia, la suspensión por inactividad del proveedor y su pooler no se midieron.
- Es un **bloqueo previo al despliegue** (B-1). El runbook ya pide esta prueba (§3, paso 0).

### 4.3 Esquema, transacciones y conexión

- **Esquema:** 33 tablas `mrs_*` (`docs/RESPALDO_Y_RESTAURACION.md`), creadas al abrir con
  `CREATE TABLE IF NOT EXISTS`; las migraciones están en el código (`ALTER TABLE … ADD COLUMN`: `revision` de
  `mrs_attempts`, campos de `mrs_progress_confirmations` y `provenance_json` de `mrs_progress_observations`). No hay
  herramienta de migración aparte. Cada store crea sus tablas al abrirse por primera vez. Cada clave única es un
  índice en una base nueva (`test_every_unique_key_is_an_index_of_a_new_database`, en PostgreSQL con TLS).
- **La Fase 0 no agregó tablas ni columnas:** el ledger, el registro de envíos y los campos nuevos del Trace viven
  dentro del JSON del encuentro (`git diff 13592e4 009aadb` no toca ningún `*_store.py`).
- **Volver atrás:** un código anterior ignora las tablas nuevas (runbook §6).
- **Transacciones:** una conexión por transacción (`psycopg.connect(url, connect_timeout=10)`); las escrituras toman
  `pg_advisory_xact_lock`, de alcance de transacción, compatible con un pooler en modo transacción; el guardado del
  encuentro compara `revision` y rechaza el más tardío («This encounter changed in another session. Reload it before
  continuing.»).
- **Conexión:** TLS según `sslmode` de la URL; `check_database.describe` rechaza una URL sin `sslmode`.
  `docs/CLINICAL_DEV_DATABASE.md` recomienda la conexión *pooled* del proveedor.

## 5. Enrutamiento y congelamiento

### 5.1 Configuración del piloto (`MRS_OFFLINE_CASES=1`, sin pin ni replay), sobre `009aadb`

| Comprobación | Resultado |
|---|---|
| Desafíos por año | R1: R1-05, R1-06, R1-07 · R2: además R2-02, R2-03, R2-04, R2-05 · R3: además R3-01 (= manifiesto) |
| Casos sorteables | R1: 17 · R2: 28 · R3: 30 = exactamente los 30 aceptados del manifiesto |
| `trauma_hemothorax_41m` | No se sortea en ningún desafío (R2-04: 13 casos, 400 semillas) ni se ofrece en las directivas |
| R1-03, R1-04, R2-01 (PS001) | No asignables en ningún año; la directiva no ofrece casos para ellos y el guardado los rechaza («That case is not one this challenge offers.») |
| Directivas docentes | Ofrecen exactamente los 30 aceptados |
| Sandbox docente | Conserva PS001 y el caso excluido (`test_the_legacy_challenges_are_kept_for_faculty_and_migration`) |
| `MRS_REPLAY_CASE` | El preflight falla si está definido |

### 5.2 Hallazgo verificado: `MRS_DEFAULT_VARIANT` salta la exclusión

- Con `MRS_DEFAULT_VARIANT=trauma_hemothorax_41m`, cada lanzamiento de R2-04 de un residente abre el caso excluido;
  un desafío que no contiene ese caso no puede lanzar el encuentro («This patient variant is not available for the
  selected challenge.»).
- El preflight, con ese valor y el resto correcto: «[AVISO] no_pinned_case: MRS_DEFAULT_VARIANT no está definido: el
  currículo elige el caso.» y **«Configuración del piloto: LISTA.»** (código de salida 0). El aviso describe la regla,
  no el valor encontrado.
- El manifiesto lo exige ausente; el preflight sólo lo recomienda (contradicción 10.2-a).
- Mientras se decide: toda línea **AVISO** de `no_pinned_case`, `free_generation_closed`, `paid_generation_off` o
  `code_version` detiene el despliegue.

## 6. Firmas y aprobaciones docentes

Ninguna firma se inventa aquí. Estado a la fecha, según `docs/revision/CIERRE_PREPILOTO.md` (sección 2, filas 1–64),
`docs/revision/F0_11_FRASES_ES.md` y `docs/READINESS_PILOTO_FORMATIVO.md`:

| Material | Estado | Dónde se firma |
|---|---|---|
| F0-11 · frases nuevas de la Fase 0 en español (activas en la sala en español; «no es su firma») | PENDING FACULTY SIGN-OFF (redacción y eventos que cortan una espera) | `docs/revision/F0_11_FRASES_ES.md` |
| R-4 · 18 frases del motor (filas 1–18) | PENDING FACULTY SIGN-OFF (1–11 borrador, 12–18 activas) | `docs/revision/R4_FRASES_MOTOR.md`, `CIERRE_PREPILOTO.md` |
| Notas de la TEP y aviso del sangrado (19–26) | PENDING FACULTY SIGN-OFF (activas) | `CIERRE_PREPILOTO.md` |
| Líneas del examen (27–38) y rótulos del E-FAST | PENDING FACULTY SIGN-OFF (EN activo; ES con el relato) | `CIERRE_PREPILOTO.md` |
| Textos de cierre: límites declarados (39–44) y C14 de la 52m y la 70f (45–46) | PENDING FACULTY SIGN-OFF (activos en inglés) | `CIERRE_PREPILOTO.md` |
| R-2 · 14 fichas POCUS C14 YES (47–60) | PENDING FACULTY SIGN-OFF | `docs/revision/R2_POCUS_C14.md` |
| R-3 · TDFC final (61) | PENDING FACULTY SIGN-OFF | `docs/tdfc/TDFC_TABLA_FINAL.md` |
| Guía docente y guía del residente (62–63) | PENDING FACULTY SIGN-OFF («lista para firma, no aprobada»); además desactualizadas (10.2-c) | `docs/GUIA_DOCENTE_PILOTO.md`, `docs/GUIA_RESIDENTE_PILOTO.md` |
| Aviso de la foto (64) | PENDING FACULTY SIGN-OFF (EN activo; ES borrador) | `CIERRE_PREPILOTO.md` |
| Relato de cada caso en español | PENDING: se aprueba en el tablero docente **de la base desplegada**, después del despliegue y antes de jugar en español | App desplegada |
| Descriptores de la rúbrica en español | UNKNOWN en la base del piloto: se aprueban en la app; sin aprobación se muestran en inglés | App desplegada |
| Autorización explícita del piloto (condición C) | PENDING | Decision File |

**Orden:** una firma que cambie un texto activo cambia el código y, con él, el candidato, que habría que verificar de
nuevo. Conviene firmar antes de construir el candidato final, no después de desplegarlo.

## 7. Imágenes y TD-56

**Clasificación: SAFE WITH DECLARED PROCEDURE.**

- `assets/patient_images/approvals.json`: 117 aprobaciones, todas bajo **una** cuenta docente (no se escribe su nombre
  aquí).
- La corrección de TD-56 (2026-10-02) hace que una aprobación espere la cuenta que nombra y nunca se registre bajo
  otra; sin las aprobaciones, la llegada se ve en vista neutral. Lo que falla, falla del lado seguro.
- `MRS_IMAGE_REQUIRE_REVIEW = "on"` exige las dos revisiones humanas.
- **Acciones humanas, después del despliegue y antes de cualquier invitación de residente** (runbook §3, pasos 5 a 7):
  1. el administrador entra y retira `MRS_ADMIN_USERNAME` y `MRS_ADMIN_PASSWORD_HASH` de los Secrets;
  2. crea una invitación de docente;
  3. **la persona que dio las aprobaciones** registra su propia cuenta con exactamente el nombre que nombra
     `approvals.json`, y entra una vez;
  4. `MRS_DATABASE_URL='…' python3 check_database.py --photo-approvals` termina en «All 117 approvals are recorded
     under the accounts they name.» con «as faculty».
- Si esa cuenta no puede crearse, es un bloqueo del despliegue (runbook §3, paso 7).

## 8. Diferencias de dependencias y de runtime

| Elemento | Local (verificado) | Destino | Efecto posible |
|---|---|---|---|
| Plataforma | Contenedor Linux; Streamlit local y AppTest | Streamlit Community Cloud (`docs/SETUP_v0.11.0.md`); app del piloto no identificada | — |
| Python | 3.11.15 | UNKNOWN (se elige al crear la app; no hay `runtime.txt` ni equivalente) | Toda la verificación es sobre 3.11 |
| Streamlit | 1.64.0 | `>=1.41,<2` → hoy 1.65.0 | **Reruns, idempotencia y recuperación de sesión:** el envío seguro de la Fase 0 se diseñó y probó con la secuencia de Streamlit 1.64 (informe de la Fase 0, sección 11). Resultado con 1.65.0 en la sección 9.4 |
| psycopg | 3.3.6 | `>=3.2,<4` → hoy 3.3.6 | Igual hoy; sin fijar |
| reportlab, pypdf, openai | 4.5.1, 6.19.0, 2.54.0 | rangos sin fijar | Documentos PDF; `openai` no se llama sin conexión |
| Paquetes del sistema | Ninguno (no hay `packages.txt`); fuentes de los PDF en `assets/fonts` | Igual | — |
| Punto de entrada | `streamlit run app.py` | Archivo principal `app.py` | — |
| Configuración de Streamlit | `.streamlit/config.toml` (`fastReruns = false`) | El mismo archivo del repositorio | Si la plataforma lo ignorara, volvería el doble clic concurrente; se comprueba en la prueba de humo (paso 12) |
| Persistencia | PostgreSQL 16 local (TLS) y SQLite en pruebas | PostgreSQL del proveedor | Sección 4 |
| Disco | — | Efímero | La app no necesita disco persistente: los diagnósticos de una generación fallida sólo se escriben si hay generación por IA, imposible sin conexión |
| Activos | `assets/` (13 MB: fotos, aprobaciones, fuentes) | El checkout | Las fotos se importan a la base al abrir la página |
| Actualizaciones | — | Push → redespliegue; módulos viejos hasta «Reboot app» | Sección 3.2 |
| Determinismo | Replay determinista en los 31 casos (batería) | Igual código | Sin cambio esperado |

## 9. Pruebas ejecutadas sobre `009aadb`

Ninguna prueba ni código se cambió para estas corridas. Todas sobre `009aadb`, con el árbol limpio. La suite completa
y las pruebas de PostgreSQL corrieron en el entorno habitual del contenedor de desarrollo (que define `MRS_BATCH_*`,
como en las corridas de la Fase 0); el preflight, la prueba de humo, el simulacro, las regresiones y las corridas con
Streamlit 1.65.0, sin esas variables.

### 9.1 Suite completa (Python 3.11.15, Streamlit 1.64.0)

**7.578 pasaron, 0 fallaron, 93 omitidas, 1 xfail** (275 subpruebas), en 4 particiones y sin
`MRS_TEST_POSTGRES_URL`. Es el mismo resultado de la corrida hecha sobre `009aadb` antes del push. Las 93 omisiones
son las 83 de siempre más las 10 de PostgreSQL, que corren aparte (9.2).

| Categoría del encargo | Archivos | Resultado |
|---|---|---|
| Fase 0: ledger y cobertura | `test_phase0_order_ledger.py` (29), `test_phase0_unknown_names.py` (107) | 136 de 136 |
| Enrutamiento y congelamiento | `test_phase0_routing.py` (5), `test_phase0_pilot_freeze.py` (4, consistencia del manifiesto), `test_cognitive_generator.py`, `test_curriculum_assignment.py`, `test_cognitive_catalog.py` | 59 de 59 |
| Envío e idempotencia | `test_phase0_submission_guard.py` (12), `test_phase0_answer_parity.py` (12) | 24 de 24 |
| Tiempo y eventos | `test_phase0_time_and_events.py` | 31 de 31 |
| Observación y procedencia | `test_phase0_observation_and_provenance.py` | 17 de 17 |
| Guardas del análisis | `test_phase0_guards.py` | 12 de 12 |
| Batería de aceptación | `test_phase0_acceptance_battery.py` (604), `test_phase0_acceptance_page.py` (31), `test_phase0_acceptance_findings.py` (81) | 716 de 716 |
| Idioma (F0-11) | `test_phase0_spanish.py` | 23 de 23 |
| Seguridad, acceso y privacidad (9.6) | 13 archivos | 101 de 101 |

### 9.2 PostgreSQL 16.13 con TLS obligatorio

| Archivo | Resultado |
|---|---|
| `test_phase0_submission_guard_on_postgres.py` (A–F y F0-12) | 10 de 10 |
| `test_store_integrity_on_postgres.py` (índices, transacción de la directiva, autor de los cambios de cuenta, error del driver registrado sólo por su clase) | 5 de 5 |
| `test_the_image_bank_on_postgres.py` | 4 de 4 |
| `test_p07_75f_arrives_with_the_neutral_view.py` (uno de los cuatro, en SQLite) | 4 de 4 |

- Las dos líneas `ERROR` de los registros capturados son fallas que las pruebas provocan a propósito (E: «the
  processing failed part way»; el error del driver que debe registrarse sólo por su clase).
- **Simulacro de respaldo** (`tools_backup_drill.py --postgres`, base vacía y descartable, con TLS): 33 tablas y
  690 filas; `pg_dump` de 11,5 MB en 1,2 s; restauración idéntica tabla por tabla; los 2 encuentros y los cambios de
  cuenta, idénticos al releerlos; abrir la copia no cambia ninguna fila. **Aprobado.**

### 9.3 Prueba de humo automática del runbook (`tools_pilot_smoke.py --configuration pilot`)

- Commit `009aadb4c527`, sin cambios sin confirmar; **0 intentos de llamar al proveedor**.
- Encuentros en inglés y con órdenes en español, completados; el registro guarda `code_version` `009aadb4c527`.
- El foco se oculta al cerrar y se ve después de la rúbrica confirmada; las cuatro pantallas del residente abren en
  español; los documentos en español se generan.
- Permisos: otro residente no lee ni lista el encuentro; el residente no confirma su rúbrica ni crea invitaciones;
  el docente no crea invitaciones y sí lee el encuentro.
- Límite conocido de la herramienta: AppTest no recorre la sala en español (selecciona el idioma de pantalla en
  inglés); la sala en español se verifica por sus frases (`test_phase0_spanish.py`).

### 9.4 Streamlit 1.65.0 (entorno virtual aislado, mismo código)

- **AppTest:** los 14 archivos `test_phase0_*.py`, **968 pasaron, 0 fallaron**, 10 omitidas (PostgreSQL).
- **Navegador real** (Chromium, dos servidores aislados de `009aadb`, sin red, base sintética, `acs_61m_posterior`;
  el arnés de la verificación 0D de la Fase 0):

  | Prueba | Resultado en los dos servidores |
  |---|---|
  | Doble clic sin intervalo | Ejecutada una vez |
  | Dos clics a 60 ms | Ejecutada una vez |
  | Cinco clics a 40 ms | Ejecutada una vez |
  | Recarga durante el proceso | Ejecutada una vez |
  | Recarga después del proceso | Nada |

  Sin conflictos de guardado, sin excepciones y 0 intentos de red. Es el resultado de la Fase 0 con 1.64.0.
- **No verificado:** la suite completa con 1.65.0, una versión de Streamlit posterior y un Python distinto de 3.11.

### 9.5 Regresiones activas (`run_regressions.py`): CODE FAILURE

- **54 de 56.** El ejecutor se detiene en la primera falla (código de salida 1); cada script se corrió por separado
  para ver el cuadro completo.
- Fallan dos comprobaciones de **texto fuente** de `app.py` que la Fase 0 cambió en `a6ab3a6` (0A-0B):
  - `regression_v06020_management_trace.py` busca `def record_management_trace(learner_input, parsed, result,
    state_before, state_after):` (la Fase 0 agregó `turn=None`) y `"interpreted_action":
    deepcopy(parsed.get("actions", []))` (la Fase 0 quita las etiquetas internas con `_untag`);
  - `regression_v06021_management_trace_ui.py` busca la misma línea de `interpreted_action`.
- Las dos pasan en `13592e4`, el commit de partida de la Fase 0. La verificación de la Fase 0 corrió la suite de
  pytest, no `run_regressions.py`, y su informe no lo menciona.
- **Lo que protegen sigue en pie** (cada aserción evaluada aparte): el Trace guarda la entrada, la acción
  interpretada, el estado antes y después, y el orden instantánea → ejecución → instantánea se cumple.
- Clasificación: **CODE FAILURE** de los activos de prueba (comprobaciones de texto que quedaron atrás de un cambio
  aprobado), no del entorno ni de un requisito externo. No se cambiaron (B-6).

### 9.6 Seguridad y privacidad

- Pruebas existentes, todas aprobadas: permisos por rol (`test_role_permissions.py`, 5), cuentas y portal
  (`test_account_store.py`, 15; `test_account_portal.py`, 6), diagnósticos sin URL ni credenciales
  (`test_account_store_diagnostics.py`, 9; `test_check_database.py`, 13), preflight sin secretos
  (`test_tools_pilot_preflight.py`, 7), clave retenida sin conexión (`test_offline_cases.py`, 17), foco oculto hasta la
  revisión (`test_learning_focus_waits_for_review.py`, 4), fotos que esperan su cuenta (`test_td56_…`, 4), cambios de
  cuenta auditados (7), integridad del store (9), exportación de cuentas inactivas (3), simulacro (2); en PostgreSQL
  con TLS, el error del driver registrado sólo por su clase.
- Archivos versionados: ninguna credencial real; las coincidencias son valores ficticios de las pruebas que verifican
  la redacción. `.streamlit/secrets.toml` no está versionado y está ignorado.
- El riesgo verificado es de configuración (3.3 y 5.2), no de código.

## 10. Bloqueos y contradicciones

### 10.1 Bloqueos previos al despliegue

| # | Bloqueo | Por qué bloquea | Lo más pequeño que lo resuelve | ¿Invalida verificación de la Fase 0? |
|---|---|---|---|---|
| B-1 | Prueba PostgreSQL del proveedor no corrida (BLOCKED / NOT RUN) | La persistencia del piloto vive en el proveedor; sólo se probó PostgreSQL 16 local | Correr `test_phase0_submission_guard_on_postgres.py` (y los otros tres archivos de PostgreSQL) contra una base **descartable** del proveedor, de su misma versión mayor, desde un equipo con red directa (runbook §3, paso 0) | No |
| B-2 | Entorno de destino sin identificar | No se sabe qué app, qué rama, qué base ni qué Python | Nombrar la app y la base del piloto; crear la app con Python 3.11; desplegar una rama propia fija en el commit aprobado (3.2) | No |
| B-3 | El preflight puede dar «LISTA» con la app fuera de la configuración congelada (3.3 y 5.2) | El gate del runbook (paso 3) no garantiza lo que dice | **Decisión:** (a) procedimiento: `OPENAI_API_KEY` ausente, valores entre comillas y todo AVISO de los indicadores del manifiesto tratado como FALLA; o (b) corrección del preflight (sólo la herramienta, no el runtime): tratar un valor TOML no textual como ausente, como hace Streamlit, y volver obligatorias las reglas que el manifiesto exige (cambia `test_a_recommendation_warns_and_never_fails`) | No (no toca el runtime) |
| B-4 | Dependencias sin fijar: Streamlit `>=1.41,<2` (hoy instalaría 1.65.0) y Python sin fijar | El envío seguro depende de la secuencia de reruns de Streamlit; una versión que aparezca durante el piloto entraría en el próximo reinicio | **Decisión:** fijar en `requirements.txt` una versión verificada, `streamlit==1.64.0` (la de la suite completa) o `1.65.0` (verificada hoy sólo en la Fase 0 y en 0D, 9.4), y crear la app con Python 3.11. Es un commit de dependencias; el runtime no cambia | No con 1.64.0. Con 1.65.0, la suite completa con esa versión |
| B-5 | Firmas docentes pendientes (sección 6) | `READINESS` las exige antes del piloto; una firma que cambie un texto cambia el candidato | Las firmas, antes de construir el candidato final | Sólo si una firma cambia texto: se repiten las pruebas afectadas y la suite |
| B-6 | 2 de las 56 regresiones activas fallan (9.5); `run_regressions.py` sale con código 1 | La verificación del proyecto exige las regresiones activas (las fuentes de verdad las nombran; los ciclos anteriores informaron 56 de 56); sin ellas, las pruebas no están en verde | **Decisión:** actualizar los 3 textos esperados en los 2 scripts al texto que la Fase 0 aprobó (`turn=None`; `interpreted_action` con `_untag`), con su justificación, o retirarlos con motivo como en P-11. No cambia el runtime | No: la suite de pytest y sus conclusiones siguen; agrega la corrida de regresiones que la Fase 0 omitió |

**Antes de abrir el piloto, después del despliegue (no bloquean el despliegue mismo):** TD-56 (sección 7), relato en
español aprobado en la base desplegada si el piloto corre en español, prueba de humo desplegada (sección 11) y la
autorización explícita (C).

### 10.2 Contradicciones entre fuentes (se informan; no se resolvieron)

a. **Manifiesto frente a preflight.** `pilot_freeze.RUNTIME_FLAGS` exige `MRS_PAID_GENERATION=off`,
   `MRS_FREE_GENERATION` y `MRS_DEFAULT_VARIANT` ausentes y `MRS_CODE_VERSION` = commit desplegado;
   `tools_pilot_preflight.py` (C10-06) los trata como recomendación, y `MRS_CODE_VERSION` se da por cumplido si
   existe `.git`. Su prueba fija que «una recomendación avisa y nunca falla».
b. **Treinta casos, no treinta y uno** (manifiesto y decisión F0-2): siguen diciendo 31
   `docs/READINESS_PILOTO_FORMATIVO.md:158`, `docs/revision/CIERRE_PREPILOTO.md:133` («Ninguno se excluye»),
   `docs/GUIA_DOCENTE_PILOTO.md:20` y el mensaje de `tools_pilot_preflight.py:77`.
c. **Guías.** `docs/GUIA_DOCENTE_PILOTO.md:155` dice que un fármaco sin verbo «puede perderse sin aviso»; desde la
   Fase 0 queda UNRECOGNIZED con su recibo (salvo TD-69 d–f). Ninguna guía describe lo que la Fase 0 cambió en la
   sala: esperar N minutos, «reevaluar» como mirada de 2 minutos, órdenes para más tarde que no se ejecutan, el
   límite de 120 minutos, el fin de lo evaluable en un paro, el recibo «No se entendió», el envío interrumpido. Ambas
   esperan firma.
d. **Runbook §2:** «Si queda [la clave], `MRS_OFFLINE_CASES=1` la retiene en todas partes» sólo es cierto si el valor
   llega al entorno como texto o número (3.3).
e. **Informe de la Fase 0, §20:** «Push: ninguno», superado por el push autorizado de `009aadb`. Historia cerrada; no
   se modifica.

## 11. Prueba de humo en el entorno desplegado (preparada, no ejecutada)

**Precondiciones:** bloqueos de 10.1 resueltos; despliegue autorizado; Secrets como en 3.1; preflight con esos mismos
Secrets en «LISTA» y sin AVISO en los indicadores del manifiesto; «Reboot app» hecho; TD-56 en «All 117 approvals…».

**Registros de prueba:** según la convención existente (runbook §4): cuentas de prueba sin nombres reales, creadas por
invitación, desactivadas al terminar (queda en «Account change history»). **No existe mecanismo de borrado:** sus
encuentros quedan en la base del piloto, visibles para el docente en las listas y exportaciones bajo esas cuentas.
Si eso no es aceptable, la alternativa es correr esta prueba con la app apuntando a una base descartable del
proveedor y repetir en la del piloto sólo los pasos 1 y 17 (decisión pendiente).

Cuentas: `prueba_humo_r2` (residente de año 2) y `prueba_humo_docente`, con la autorización «Who may choose a
resident's cases» de la segunda sobre la primera.

| # | Paso | Cómo | Resultado esperado |
|---|---|---|---|
| 1 | Ingreso | El administrador crea las dos invitaciones; cada cuenta se registra y cambia su contraseña | Ambas entran; ningún error |
| 2 | Desafío permitido | El residente pulsa «Begin Encounter» sin directiva | En la exportación del docente, `encounter.assignment.challenge_id` está entre los 7 de R2 |
| 3 | Caso aceptado | Ídem | `evaluation_basis.case_id` es uno de los 30 aceptados del manifiesto |
| 4 | SHA en los metadatos | Exportación JSON | `assignment.code_version` y `evaluation_basis.code_version` = commit desplegado |
| 5 | Orden reconocida | Una orden del caso con dosis y vía | Se ejecuta; el recibo lo dice |
| 6 | Recibo de orden desconocida | «Zyvox IV.» | «Not understood: "Zyvox IV". Nothing was given or done for it…» (en español, «No se entendió: …») |
| 7 | Paquete mixto | Una orden reconocida y «Zyvox IV.» en el mismo envío | La reconocida corre; «PART OF THIS ORDER WAS NOT CARRIED OUT» con lo que no se hizo |
| 8 | «Wait 20 minutes.» | Ídem | El reloj avanza 20 minutos (o se detiene en un evento y lo dice) |
| 9 | «Reassess.» | Ídem | Mirada de 2 minutos en la cabecera, dicha como tal |
| 10 | Evento que interrumpe | Encuentro 2: el docente dirige `acs_54m_inferior` (R2-04); el residente escribe «Wait 60 minutes.» antes del minuto 45 | La espera se detiene en el minuto 45 (bloqueo AV) y lo dice |
| 11 | Recarga y reanudación | Recargar el navegador a mitad del encuentro | El encuentro sigue igual; nada se ejecuta de nuevo |
| 12 | Sin duplicado | Doble clic en «Send» sobre una orden | La orden corre una vez (un solo turno en el Trace) |
| 13 | Campos de la Fase 0 en el Trace | Exportación JSON | Cada turno con `trace_extensions`: `submission`, `orders` (con destino), `time_semantics`, `events`, `interrupted`, `observation_snapshot`, `limitations`, `versions` |
| 14 | Procedencia y limitaciones | Ídem | El bloqueo AV con su causa y su prevenibilidad (`SCRIPTED_NATURAL_HISTORY`, `NOT_PREVENTABLE_IN_SIMULATOR`) y la limitación `scripted_event`; «Zyvox IV.» como `unrecognized_order` |
| 15 | PS001 inalcanzable | Formulario de directiva, desafíos R1-03, R1-04 y R2-01 | «Case» sólo ofrece «—»; guardar se rechaza («That case is not one this challenge offers.») |
| 16 | Caso excluido no asignable | Formulario de directiva, R2-04 y R2-05 | `trauma_hemothorax_41m` no aparece |
| 17 | Fotos | Llegadas de los dos encuentros | Foto aprobada o vista neutral; nunca una foto sin sus dos revisiones |
| 18 | Cierre | «Complete Encounter & Begin Review»; el docente confirma la rúbrica; el administrador desactiva ambas cuentas | Foco visible sólo después de la rúbrica; cambio en «Account change history»; resultado, fecha y commit anotados en `docs/READINESS_PILOTO_FORMATIVO.md` (runbook §4) |

La parte automática del runbook (`tools_pilot_smoke.py --configuration pilot`) no toca la base del piloto: crea la
suya. Su resultado sobre `009aadb` está en la sección 9.

### 11.1 Qué revisar si el piloto falla (observabilidad)

El runbook ya tiene «Si algo falla» (§6). Lo que la Fase 0 agrega y dónde se ve:

| Señal | Dónde se ve | Registro del servidor |
|---|---|---|
| La app no arranca | Registros de la app en Streamlit Cloud; mensaje «Access is temporarily closed…» si falta configuración | Sí (plataforma) |
| La base no responde | Mensaje genérico al usuario; `python3 check_database.py` dice la causa sin la URL | Sí: «Account store transaction failed: <clase> at <archivo:línea>», nunca el contenido |
| Conflicto de revisión | «This encounter changed in another session. Reload it before continuing.» | **No** |
| Envío atascado o interrumpido | El aviso en la sala; `submission_log` del encuentro (`processing` / `interrupted`) en la exportación JSON | **No** |
| Inconsistencia del motor | Limitación `engine_inconsistency` en el turno del Trace (la regla E lo vuelve no evaluable) | **No** |
| Órdenes no entendidas | Recibos en la sala; destinos `UNRECOGNIZED` en `orders` del Trace. No hay conteo agregado | **No** |
| Enrutamiento heredado | Sólo leyendo: `SELECT challenge_id, COUNT(*) FROM mrs_attempts WHERE is_sandbox = 0 GROUP BY challenge_id;` no debe mostrar R1-03, R1-04 ni R2-01 | — |
| Fotos | Vista neutral; `check_database.py --photo-approvals` | Sí: `image_pack_import_failed`, `image_scene_failed <clase>` |
| Versión | `code_version` por turno en la exportación JSON | — |

Las señales sin registro del servidor dependen de que la persona residente avise o de que el docente lea el
registro del encuentro: es una limitación declarada, no un defecto nuevo.

## 12. GO / NO-GO

| Categoría | Estado | Por qué |
|---|---|---|
| A · Código y pruebas | **BLOCKED** | Suite completa 7.578/0, Fase 0 completa y prueba de humo automática en verde; 2 de 56 regresiones activas fallan por texto que la Fase 0 cambió (B-6) |
| B · Base de datos | **BLOCKED** | PostgreSQL 16 local con TLS: 23 de 23 y simulacro de respaldo aprobado; proveedor: BLOCKED / NOT RUN (B-1) |
| C · Configuración congelada | **BLOCKED** | Secrets del destino sin verificar; el preflight puede decir «LISTA» fuera de la configuración (B-3) |
| D · Enrutamiento | PASS WITH DECLARED LIMITATION | 30 aceptados, excluido y PS001 fuera (5.1); `MRS_DEFAULT_VARIANT` sólo lo cierra la configuración (5.2) |
| E · Idioma y firmas docentes | **BLOCKED** | Todas pendientes (sección 6; B-5) |
| F · Imágenes y TD-56 | PASS WITH DECLARED LIMITATION | Procedimiento declarado y verificable; falla hacia la vista neutral (sección 7) |
| G · Entorno de despliegue | **BLOCKED** | App, rama, base y Python sin identificar; Streamlit sin fijar (B-2, B-4) |
| H · Seguridad y acceso | PASS WITH DECLARED LIMITATION | Pruebas de permisos, aislamiento, diagnósticos y fotos en verde (9.6); sin credenciales versionadas. Limitación: la ausencia de `OPENAI_API_KEY` en los Secrets es obligatoria (3.3) |
| I · Observabilidad | PASS WITH DECLARED LIMITATION | Base y fotos en el registro del servidor; conflictos, envíos interrumpidos e inconsistencias sólo en la sala y en el registro del encuentro (11.1) |
| J · Plan de humo desplegado | PASS (READY) | Sección 11; se ejecuta después de resolver los bloqueos y con autorización |

## 13. Recomendación

**NOT READY FOR DEPLOYMENT.** Bloquean B-1 a B-6.

- El runtime de `009aadb` no mostró un defecto de conducta: la suite completa, la Fase 0, PostgreSQL con TLS, el
  simulacro de respaldo y la prueba de humo automática pasan, y el envío seguro se comporta igual con Streamlit 1.65.0.
- Falta: la prueba en el proveedor (B-1), el entorno de destino (B-2), un gate de configuración confiable (B-3),
  dependencias fijas (B-4), las firmas (B-5) y dos regresiones que quedaron atrás de la Fase 0 (B-6).
- B-3, B-4 y B-6 se resuelven sin tocar el runtime y esperan una decisión: no se aplicó ninguna corrección.
- No se desplegó; no se hizo push, merge, PR ni release; no se empezó la Fase 1.
