# Preparación para el despliegue · piloto con residentes (2026-10-06)

**Encargo:** «PRE-DEPLOYMENT READINESS — RESIDENT PILOT» (2026-10-06). Determinar si el build congelado de la Fase 0
está listo para desplegarse en el entorno real del piloto. **No es la Fase 1, no reabre la Fase 0 y no despliega.**

**La Fase 0 quedó cerrada en `009aadb`** («PHASE 0 — CLOSED», 2026-10-06). Su informe
(`docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`) no se modifica: su sección 20 dice «Push: ninguno», y después el
push se autorizó y se hizo (merge `009aadb` sobre `bc99b41`, con los dos commits del remoto). Este documento no
cambia esa historia; la completa.

**Decisión:** **NOT READY FOR DEPLOYMENT** (sección 13). Bloqueos explícitos en la sección 10.

**Actualizado el 2026-10-06** (encargo «resolver sólo B-3, B-4 y B-6»): B-3, B-4 y B-6 quedan **RESUELTOS** en
commits locales, sin push (`87bbbe1`, `4d570a8` y `e200ccc`; sección 14). Siguen abiertos B-1, B-2 y B-5, y la
decisión sigue siendo **NOT READY FOR DEPLOYMENT**. Las secciones 1 a 13 conservan lo hallado sobre `009aadb`; donde
algo cambió, una nota «Resuelto» remite a la sección 14.

**Actualizado el 2026-10-07** (encargo «B-2 — define the pilot target deployment environment»): el entorno del piloto
queda definido en diseño (rama `pilot-residents-v1`, app y base propias, contrato de promoción), pero **B-2 queda
BLOCKED**: la app del piloto, su base, el Python de la plataforma y las vinculaciones de las apps existentes sólo se
conocen desde las cuentas (sección 15). Sigue **NOT READY FOR DEPLOYMENT**.

**Actualizado otra vez el 2026-10-07** (datos confirmados en los proveedores): **B-2 RESUELTO** (sección 16).
- Topología del piloto: rama `pilot-residents-v1`, app nueva `clinical-management-reasoning-pilot`, `app.py`,
  Python 3.11, y en Neon el proyecto `management-reasoning-simulator` (PostgreSQL 17) con la rama `pilot-residents-v1`.
- **B-1: READY TO EXECUTE / NOT YET EXECUTED** (16.8 y 16.9).
- **B-5: BLOCKED.**
- Sigue **NOT READY FOR DEPLOYMENT**.

**Actualizado por tercera vez el 2026-10-07** (intento de B-1 en el proveedor): **B-1 BLOCKED**, clasificado como
TEST ENVIRONMENT FAILURE.
- Desde este entorno no se llega a Neon: no hay conector ni credenciales, el proxy rechaza la API y no hay salida TCP
  a 5432.
- No se creó ni se tocó ningún recurso del proveedor.
- D-B2-5 confirmada: la consola ofrece «Branch schema only».
- Siguiente acción: correr B-1 desde un equipo con red directa (sección 17).
- Sigue **NOT READY FOR DEPLOYMENT**.

**Actualizado por cuarta vez el 2026-10-07** (rama de B-1 creada a mano): **B-1 READY TO EXECUTE**, a la espera de
los resultados del Mac (sección 18).
- La rama `pilot-b1-validation` se creó a mano en la consola: PostgreSQL 17, «Branch schema only», sin datos de
  producción y con borrado automático al día.
- Candidato de B-1: `e200cccc6487af807cab419595baed5b15dd6179`, el último commit de runtime y dependencias. Llega al
  Mac en un `git bundle`, sin push.
- El procedimiento del Mac se ensayó aquí de punta a punta. Suma dos resguardos: un `HOME` vacío y la comprobación
  del cómputo de la rama.
- Sigue **NOT READY FOR DEPLOYMENT**.

**Actualizado por quinta vez el 2026-10-07** (corrida en el proveedor): **B-1 STILL BLOCKED** (sección 19).
- **La corrida conjunta en Neon** (PostgreSQL 17.11, TLS) dio **21 passed y 2 errors**. Las dos fallas fueron por el
  límite de 180 s de AppTest al empezar el encuentro, y los cuerpos de esas pruebas no corrieron.
- **Las dos pruebas pasaron al correrlas solas.**
- **La causa está medida:** la latencia del enlace llevó ese arranque sobre base vacía a unos 170 s.
- **La aceptación vigente pide una corrida única 23/23.** Se propone, sin implementar, subir ese límite a 300 s en
  el fixture de PostgreSQL.
- Sigue **NOT READY FOR DEPLOYMENT**.

**Actualizado por sexta vez el 2026-10-07** (corrida final en el proveedor): **B-1 RESUELTO** (sección 20).
- **Corrida única en Neon:** 23 passed en 2208.13 s, sin fallas, errores ni omisiones.
- **Destino:** PostgreSQL 17.11, endpoint *pooled* de `pilot-b1-validation`, TLS, y `TARGET OK` antes y después.
- **SHA probado:** `8ff41a45a6ce60dfc652149b2ef774424304e49a`. Respecto de `e200ccc` sólo cambia el límite de AppTest
  en el fixture de PostgreSQL (de 180 s a 300 s); el runtime no cambia.
- Sigue **NOT READY FOR DEPLOYMENT**: queda B-5.

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
- **Actualizado (B-3, B-4 y B-6):** el candidato pasa a ser el último commit de ese encargo, que contiene `87bbbe1`,
  `4d570a8`, `e200ccc` y el commit de esta actualización. `git diff --stat 009aadb HEAD -- . ':(exclude)docs'` ya no
  sale vacío: lista sólo `tools_pilot_preflight.py` y su prueba, `requirements.txt` y los dos scripts de regresión.
  La app no importa ninguno de ellos: `app.py` y los módulos que carga son los de `009aadb`, y `requirements.txt`
  fija la versión de Streamlit con que se verificó todo (14.2).

## 3. Requisitos del entorno

Los Secrets del entorno del piloto **no son accesibles desde este entorno**: ningún valor actual se pudo leer. Los
valores secretos se informan sólo como PRESENT / MISSING / UNKNOWN; aquí, todos UNKNOWN.

### 3.1 Tabla de indicadores (manifiesto, runbook y readiness)

| Indicador | Valor exigido | Valor actual / disponible | Estado | Fuente del valor | ¿Bloqueo? |
|---|---|---|---|---|---|
| `.streamlit/config.toml` `[runner] fastReruns` | `false` | `false` en `009aadb` (archivo del repositorio) | OK en el código | Repositorio | NO (el preflight lo exige, leído del commit que se despliega, 14.1) |
| `MRS_OFFLINE_CASES` | `"1"` (texto o entero; **nunca** booleano TOML, ver 3.3) | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (el preflight falla si la app no queda sin conexión, 14.1) |
| `MRS_PAID_GENERATION` | `"off"` (texto; nunca booleano TOML) | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (en `009aadb` el preflight sólo lo recomendaba; desde `87bbbe1` lo exige) |
| `MRS_FREE_GENERATION` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (en `009aadb` el preflight sólo lo recomendaba; desde `87bbbe1` falla con cualquier valor) |
| `MRS_DEFAULT_VARIANT` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (salta la exclusión, 5.2; en `009aadb` el preflight sólo avisaba; desde `87bbbe1` falla con cualquier valor) |
| `MRS_REPLAY_CASE` | ausente | UNKNOWN | UNKNOWN | Secrets → entorno | **SÍ** hasta verificarlo (el preflight falla si está) |
| `MRS_CODE_VERSION` | el commit desplegado | UNKNOWN; candidato: el último commit del encargo B-3, B-4 y B-6 (sección 2) | UNKNOWN | Secrets → entorno; si falta, `git rev-parse` del checkout | **SÍ** hasta verificarlo (3.2; desde `87bbbe1` el preflight exige el commit que se despliega) |
| `MRS_IMAGE_REQUIRE_REVIEW` | `"on"` | UNKNOWN | UNKNOWN | Secrets (la app lo lee también de `st.secrets`) | **SÍ** hasta verificarlo |
| `MRS_AUTH_MODE` | `"accounts"` | UNKNOWN | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `MRS_DATABASE_URL` (secreto) | URL PostgreSQL del proveedor con `sslmode=require` | UNKNOWN (PRESENT/MISSING no verificable) | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `OPENAI_API_KEY` (secreto) | **ausente** (runbook §2: «retírela»; aquí, obligatorio por 3.3) | UNKNOWN | UNKNOWN | Secrets | **SÍ** hasta verificarlo (desde `87bbbe1`, si quedara, el preflight falla salvo que la app la retenga en todas partes, 14.1) |
| `MRS_ADMIN_USERNAME`, `MRS_ADMIN_PASSWORD_HASH` (secreto) | sólo hasta crear el primer administrador; después, ausentes | UNKNOWN | UNKNOWN | Secrets | NO (paso del runbook) |
| `MRS_ALLOW_LOCAL_SQLITE` | ausente | UNKNOWN | UNKNOWN | Secrets | **SÍ** hasta verificarlo |
| `MRS_SYNTHETIC_ACCOUNTS`, `MRS_BATCH_*` | ausentes | UNKNOWN en el destino. El contenedor de desarrollo de esta revisión sí tiene `MRS_BATCH_*` definidas: no es el destino | UNKNOWN | Secrets / entorno | **SÍ** hasta verificarlo |
| Python | 3.11 (probado: 3.11.15) | UNKNOWN: Streamlit Community Cloud lo fija al crear la app; el repositorio no lo fija | UNKNOWN | Configuración de la app | **SÍ** (sección 8; se elige al crear la app: B-2) |
| Streamlit | 1.64.0 (probado) | En `009aadb`, `requirements.txt` admitía `>=1.41,<2` y una instalación nueva tomaba **1.65.0** (PyPI), verificada en la Fase 0 y en 0D, no en la suite completa (9.4). **Desde `4d570a8`: `streamlit==1.64.0`** (14.2) | OK en el código | `requirements.txt` | NO (resuelto, B-4) |
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

  **Desarrollado en la sección 15** (B-2, 2026-10-07): la rama `pilot-residents-v1`, el contrato de promoción y
  el chequeo de encuentros abiertos.

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
- **Resuelto (B-3, `87bbbe1`; sección 14.1):** el preflight lee los Secrets con el analizador de Streamlit, los
  pasa al entorno con la regla de Streamlit y pregunta a los lectores de la app: con `MRS_OFFLINE_CASES = true`
  falla («la aplicación NO queda sin conexión») y da «NO LISTA». La app no cambió: con esa configuración haría lo
  mismo que arriba; lo que cambió es que el gate ya no la deja pasar.

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
- **Resuelto (B-3, `87bbbe1`; 14.1):** con `MRS_DEFAULT_VARIANT=trauma_hemothorax_41m`, o con cualquier otro valor,
  en los Secrets o en el entorno con que arranca la app, el preflight da «[FALLA] no_pinned_case», «NO LISTA» y
  código de salida 1 (prueba E). Esas cuatro reglas son obligatorias y la regla transitoria de arriba ya no hace
  falta. La app no cambió: con esa variable, R2-04 seguiría abriendo el caso excluido; lo impide la configuración,
  que el gate ahora exige.

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

**Actualización del 2026-10-07 (B-5, decisiones docentes):** el relato en español de los 30 casos y los
descriptores de la rúbrica en español se revisan antes de congelar el candidato final, que no se congela sin esas
revisiones; ya no quedan para después del despliegue. El relato aprobado entra en el candidato en
`case_text/es/approvals.json` (camino a; el archivo se crea después de la revisión docente), sin volver a
registrarlo a mano en la base del piloto. El mecanismo con que la rúbrica se activa en el candidato se identifica
antes de implementarla (Decision File, décima y undécima actualizaciones; TD-81).

**Actualización del 2026-10-07 (B-5, lotes 4 y 5):** de las frases de F0-11, K-1 a K-16 están aprobadas (K-5, K-6,
K-13 y K-14 con la regla de X1-0); faltan K-17 a K-21 y los eventos K-E1 a K-E17 (Decision File, duodécima
actualización).

**Actualización del 2026-10-07 (B-5, lote final de nivel 1):** K-17 a K-21 quedan decididas, y con ellas todo el
nivel 1. K-18 se revisa: es una corrección de texto del motor antes del candidato final (TD-82). De F0-11 quedan
los eventos K-E1 a K-E17, de nivel 2 (Decision File, decimotercera actualización).

**Actualización del 2026-10-07 (B-5, lote 1 de nivel 2):** A-6 se revisa: en la 49m, el examen respiratorio
conserva la gravedad de llegada mientras la obstrucción no mejore. Es un cambio del motor antes del candidato final
(TD-83). Quedan 33 decisiones, todas de nivel 2 (Decision File, decimocuarta actualización).

**Actualización del 2026-10-07 (B-5, lotes 2 y 3 de nivel 2):** quedan decididas A-14 a A-18, C-27 a C-33, C-35,
C-36, C-38, C-EFAST y K-E1 a K-E4. La redacción de los estados límite de la 49m (A-6a, A-6b, A-7-49m y A-8a) quedó
aprobada y entra en el mismo cambio del motor de TD-83, antes del candidato final. Quedan 13 decisiones, todas de
nivel 2: K-E5 a K-E17, y K-E5 trae un hallazgo (TD-82; Decision File, decimoquinta y decimosexta
actualizaciones).

**Actualización del 2026-10-07 (B-5, lote 4 de nivel 2):** K-E7 a K-E14 quedan aprobadas. K-E5 y K-E6 se revisan:
son cambios de texto del motor antes del candidato final (TD-82, TD-67). La elección entre A-6 y A-6b queda por el
estado del motor, no por el fármaco de inducción (TD-83). Quedan 3 decisiones, K-E15 a K-E17 (Decision File,
decimoséptima actualización).

**Actualización del 2026-10-07 (B-5, lote final de nivel 2):** K-E15 a K-E17 quedan aprobadas, y con ellas las 100
decisiones del paquete. H-62 e I-63 siguen sin firma a propósito, hasta el candidato final implementado. B-5 sigue
bloqueado: falta X-1 (98 de 105 decisiones, consolidadas en 28), la revisión del relato y de la rúbrica en español,
implementar lo decidido y verificar el candidato (Decision File, decimoctava actualización).

**Actualización del 2026-10-07 (B-5, lote 1 de X-1):** XR-01 a XR-14 quedan decididas: 9 APPROVE y 5 REVISE, sin
implementar. De X-1 quedan 38 de 105 decisiones, en el lote 2, y una contradicción abierta (L-09). B-5 sigue
bloqueado (Decision File, decimonovena actualización).

**Actualización del 2026-10-07 (B-5, lote 2 de X-1):** XR-15 a XR-28 quedan decididas (12 APPROVE y 2 REVISE) y
L-09, resuelta. X-1 queda decidida entera (105 de 105), sin implementar. La revisión del relato y de la rúbrica en
español quedó diseñada (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`). B-5 sigue bloqueado (Decision File, vigésima actualización).

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
| Python | 3.11.15 | UNKNOWN (se elige al crear la app; no hay `runtime.txt` ni equivalente) | Toda la verificación es sobre 3.11; elegirlo al crear la app es parte de B-2 |
| Streamlit | 1.64.0 | En `009aadb`, `>=1.41,<2` → hoy 1.65.0. **Desde `4d570a8`, `==1.64.0`** (14.2) | **Reruns, idempotencia y recuperación de sesión:** el envío seguro de la Fase 0 se diseñó y probó con la secuencia de Streamlit 1.64 (informe de la Fase 0, sección 11); fijada, un reinicio ya no instala otra versión. Resultado con 1.65.0 en la sección 9.4 |
| psycopg | 3.3.6 | `>=3.2,<4` → hoy 3.3.6 | Igual hoy; sin fijar (B-4 fija sólo Streamlit, 14.2) |
| reportlab, pypdf, openai | 4.5.1, 6.19.0, 2.54.0 | rangos sin fijar | Documentos PDF; `openai` no se llama sin conexión |
| Dependencias de Streamlit | Las de la instalación local | Sin fijar: un reinicio puede tomar versiones nuevas dentro de los rangos que declara Streamlit 1.64.0 | Limitación declarada (14.2) |
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
- **Resuelto (B-6, `e200ccc`; 14.3):** los tres textos esperados siguen al código de la Fase 0, con la misma
  intención; `run_regressions.py`: 56 de 56.

### 9.6 Seguridad y privacidad

- Pruebas existentes, todas aprobadas: permisos por rol (`test_role_permissions.py`, 5), cuentas y portal
  (`test_account_store.py`, 15; `test_account_portal.py`, 6), diagnósticos sin URL ni credenciales
  (`test_account_store_diagnostics.py`, 9; `test_check_database.py`, 13), preflight sin secretos
  (`test_tools_pilot_preflight.py`, 7; 70 desde `87bbbe1`), clave retenida sin conexión (`test_offline_cases.py`,
  17), foco oculto hasta la revisión (`test_learning_focus_waits_for_review.py`, 4), fotos que esperan su cuenta
  (`test_td56_…`, 4), cambios de cuenta auditados (7), integridad del store (9), exportación de cuentas inactivas (3),
  simulacro (2); en PostgreSQL con TLS, el error del driver registrado sólo por su clase.
- Archivos versionados: ninguna credencial real; las coincidencias son valores ficticios de las pruebas que verifican
  la redacción. `.streamlit/secrets.toml` no está versionado y está ignorado.
- El riesgo verificado es de configuración (3.3 y 5.2), no de código. El gate que lo cierra es el de 14.1.

## 10. Bloqueos y contradicciones

### 10.1 Bloqueos previos al despliegue

| # | Estado (2026-10-06) | Bloqueo | Por qué bloquea | Lo más pequeño que lo resuelve | ¿Invalida verificación de la Fase 0? |
|---|---|---|---|---|---|
| B-1 | **RESUELTO** (2026-10-07; sección 20): corrida única en Neon (PostgreSQL 17.11, endpoint *pooled*, TLS), con 23 passed sobre `8ff41a4`. Antes, STILL BLOCKED (sección 19), READY TO EXECUTE (sección 18) y BLOCKED (sección 17) | Prueba PostgreSQL del proveedor sin correr | La persistencia del piloto vive en el proveedor; sólo se probó PostgreSQL 16 local | Correr `test_phase0_submission_guard_on_postgres.py` (y los otros tres archivos de PostgreSQL) contra una base **descartable** del proveedor, de su misma versión mayor, desde un equipo con red directa (runbook §3, paso 0) | No |
| B-2 | **RESUELTO** (2026-10-07; sección 16) con los datos confirmados en los proveedores. Antes, BLOCKED (sección 15) | Entorno de destino sin identificar | No se sabe qué app, qué rama, qué base ni qué Python | Nombrar la app y la base del piloto; crear la app con Python 3.11; desplegar una rama propia fija en el commit aprobado (3.2) | No |
| B-3 | **RESUELTO** (`87bbbe1`; 14.1): opción (b), el preflight corregido; el runtime no cambió | El preflight puede dar «LISTA» con la app fuera de la configuración congelada (3.3 y 5.2) | El gate del runbook (paso 3) no garantiza lo que dice | **Decisión:** (a) procedimiento: `OPENAI_API_KEY` ausente, valores entre comillas y todo AVISO de los indicadores del manifiesto tratado como FALLA; o (b) corrección del preflight (sólo la herramienta, no el runtime): tratar un valor TOML no textual como ausente, como hace Streamlit, y volver obligatorias las reglas que el manifiesto exige (cambia `test_a_recommendation_warns_and_never_fails`) | No (no toca el runtime) |
| B-4 | **RESUELTO** (`4d570a8`; 14.2): `streamlit==1.64.0`. Python 3.11 se elige al crear la app y queda en B-2 | Dependencias sin fijar: Streamlit `>=1.41,<2` (hoy instalaría 1.65.0) y Python sin fijar | El envío seguro depende de la secuencia de reruns de Streamlit; una versión que aparezca durante el piloto entraría en el próximo reinicio | **Decisión:** fijar en `requirements.txt` una versión verificada, `streamlit==1.64.0` (la de la suite completa) o `1.65.0` (verificada hoy sólo en la Fase 0 y en 0D, 9.4), y crear la app con Python 3.11. Es un commit de dependencias; el runtime no cambia | No con 1.64.0. Con 1.65.0, la suite completa con esa versión |
| B-5 | **BLOCKED** | Firmas docentes pendientes (sección 6) | `READINESS` las exige antes del piloto; una firma que cambie un texto cambia el candidato | Las firmas, antes de construir el candidato final | Sólo si una firma cambia texto: se repiten las pruebas afectadas y la suite |
| B-6 | **RESUELTO** (`e200ccc`; 14.3): textos esperados actualizados con su justificación; 56 de 56 | 2 de las 56 regresiones activas fallan (9.5); `run_regressions.py` sale con código 1 | La verificación del proyecto exige las regresiones activas (las fuentes de verdad las nombran; los ciclos anteriores informaron 56 de 56); sin ellas, las pruebas no están en verde | **Decisión:** actualizar los 3 textos esperados en los 2 scripts al texto que la Fase 0 aprobó (`turn=None`; `interpreted_action` con `_untag`), con su justificación, o retirarlos con motivo como en P-11. No cambia el runtime | No: la suite de pytest y sus conclusiones siguen; agrega la corrida de regresiones que la Fase 0 omitió |

**Antes de abrir el piloto, después del despliegue (no bloquean el despliegue mismo):** TD-56 (sección 7), relato en
español aprobado en la base desplegada si el piloto corre en español, prueba de humo desplegada (sección 11) y la
autorización explícita (C).

**Actualización del 2026-10-07 (B-5, decisiones docentes):** el relato en español de los 30 casos y los
descriptores de la rúbrica en español se revisan antes de congelar el candidato final, que no se congela sin esas
revisiones; ya no quedan para después del despliegue. El relato aprobado entra en el candidato en
`case_text/es/approvals.json` (camino a; el archivo se crea después de la revisión docente), sin volver a
registrarlo a mano en la base del piloto. El mecanismo con que la rúbrica se activa en el candidato se identifica
antes de implementarla (Decision File, décima y undécima actualizaciones; TD-81).

### 10.2 Contradicciones entre fuentes (se informan; a y d quedaron resueltas con B-3, 14.1)

a. **Manifiesto frente a preflight.** `pilot_freeze.RUNTIME_FLAGS` exige `MRS_PAID_GENERATION=off`,
   `MRS_FREE_GENERATION` y `MRS_DEFAULT_VARIANT` ausentes y `MRS_CODE_VERSION` = commit desplegado;
   `tools_pilot_preflight.py` (C10-06) los trata como recomendación, y `MRS_CODE_VERSION` se da por cumplido si
   existe `.git`. Su prueba fija que «una recomendación avisa y nunca falla».
   **Resuelta (B-3, `87bbbe1`):** cada exigencia del manifiesto es una regla obligatoria del preflight, y
   `test_every_freeze_requirement_is_a_required_rule` falla si `RUNTIME_FLAGS` gana una exigencia sin su regla. La
   prueba de la recomendación sigue, ahora sobre `no_batch_settings`, la única recomendación que queda sobre la
   configuración del despliegue.
b. **Treinta casos, no treinta y uno** (manifiesto y decisión F0-2): siguen diciendo 31
   `docs/READINESS_PILOTO_FORMATIVO.md:158`, `docs/revision/CIERRE_PREPILOTO.md:133` («Ninguno se excluye»),
   `docs/GUIA_DOCENTE_PILOTO.md:20` y el mensaje de `tools_pilot_preflight.py:77`. El mensaje del preflight dice
   ahora «los 30 aceptados» (`87bbbe1`); los tres documentos siguen diciendo 31 y no se tocaron (fuera del alcance
   del encargo B-3, B-4 y B-6).
c. **Guías.** `docs/GUIA_DOCENTE_PILOTO.md:155` dice que un fármaco sin verbo «puede perderse sin aviso»; desde la
   Fase 0 queda UNRECOGNIZED con su recibo (salvo TD-69 d–f). Ninguna guía describe lo que la Fase 0 cambió en la
   sala: esperar N minutos, «reevaluar» como mirada de 2 minutos, órdenes para más tarde que no se ejecutan, el
   límite de 120 minutos, el fin de lo evaluable en un paro, el recibo «No se entendió», el envío interrumpido. Ambas
   esperan firma.
d. **Runbook §2:** «Si queda [la clave], `MRS_OFFLINE_CASES=1` la retiene en todas partes» sólo es cierto si el valor
   llega al entorno como texto o número (3.3). **Desde `87bbbe1` vale siempre que el preflight dé «LISTA»:** un
   `MRS_OFFLINE_CASES` que la app no activa lo hace fallar, y una clave que la app leería, también. El runbook no
   se cambió.
e. **Informe de la Fase 0, §20:** «Push: ninguno», superado por el push autorizado de `009aadb`. Historia cerrada; no
   se modifica.

## 11. Prueba de humo en el entorno desplegado (preparada, no ejecutada)

**Precondiciones:** bloqueos de 10.1 resueltos; despliegue autorizado; Secrets como en 3.1; preflight con esos mismos
Secrets en «LISTA» y sin AVISO en los indicadores del manifiesto; «Reboot app» hecho; TD-56 en «All 117 approvals…».
Desde `87bbbe1` los indicadores del manifiesto no pueden dar AVISO: fallan (14.1). Sigue sin bastar un AVISO de
`no_batch_settings`: el runbook pide que esas variables no estén.

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

Estado actualizado el 2026-10-07, después de resolver B-3, B-4 y B-6 (2026-10-06) y B-2 y B-1 (2026-10-07). Lo que valía
sobre `009aadb` se conserva en la columna «Por qué».

| Categoría | Estado | Por qué |
|---|---|---|
| A · Código y pruebas | **PASS** (sujeto a 14.4) | Sobre `009aadb`: suite completa 7.578/0, Fase 0 completa y prueba de humo automática en verde, y 2 de 56 regresiones activas fallaban (B-6). Ahora: 56 de 56 y las pruebas focalizadas en verde (14.4). La suite completa sobre el candidato final se corre después de este commit y se informa en la entrega del encargo: si no da 0 fallas, esta fila no vale |
| B · Base de datos | PASS WITH DECLARED LIMITATION | PostgreSQL 16 local con TLS: 23 de 23 y simulacro de respaldo aprobado. Proveedor (Neon, PostgreSQL 17.11, *pooled*, TLS): 23 de 23 en una corrida única sobre `8ff41a4` (B-1, sección 20). Limitación: el respaldo en PostgreSQL 17 no se probó (TD-76) |
| C · Configuración congelada | **BLOCKED** | El gate ya es confiable: falla cerrado ante cualquier exigencia del manifiesto (B-3 resuelto, 14.1). Falta correrlo con los Secrets reales del piloto, antes y después de crear la app (pasos 10 y 11 del contrato, 16.4 y 16.11) |
| D · Enrutamiento | PASS WITH DECLARED LIMITATION | 30 aceptados, excluido y PS001 fuera (5.1); `MRS_DEFAULT_VARIANT` sólo lo cierra la configuración (5.2), y el preflight falla si está definido (14.1) |
| E · Idioma y firmas docentes | **BLOCKED** | Todas pendientes (sección 6; B-5) |
| F · Imágenes y TD-56 | PASS WITH DECLARED LIMITATION | Procedimiento declarado y verificable; falla hacia la vista neutral (sección 7) |
| G · Entorno de despliegue | PASS WITH DECLARED LIMITATION | Definido y confirmado (B-2 resuelto, sección 16): rama `pilot-residents-v1`, app nueva `clinical-management-reasoning-pilot`, `app.py`, Python 3.11, Neon `management-reasoning-simulator` con PostgreSQL 17. Streamlit fijo en 1.64.0 (B-4, 14.2). Limitación: la app, la rama de Git y la rama de Neon se crean en la promoción (16.4) |
| H · Seguridad y acceso | PASS WITH DECLARED LIMITATION | Pruebas de permisos, aislamiento, diagnósticos y fotos en verde (9.6); sin credenciales versionadas. Limitación: la ausencia de `OPENAI_API_KEY` en los Secrets es obligatoria (3.3); desde `87bbbe1`, si quedara, el preflight falla salvo que la app la retenga (14.1) |
| I · Observabilidad | PASS WITH DECLARED LIMITATION | Base y fotos en el registro del servidor; conflictos, envíos interrumpidos e inconsistencias sólo en la sala y en el registro del encuentro (11.1) |
| J · Plan de humo desplegado | PASS (READY) | Sección 11; se ejecuta después de resolver los bloqueos y con autorización |

## 13. Recomendación

**NOT READY FOR DEPLOYMENT.** Sólo bloquea B-5 (BLOCKED): las firmas docentes (sección 6; detalle en 20.5).
- B-3, B-4 y B-6 se resolvieron el 2026-10-06 (sección 14); B-2 y B-1, el 2026-10-07 (secciones 16 y 20).
- Al escribir la primera versión de este documento bloqueaban B-1 a B-6.

- El runtime de `009aadb` no mostró un defecto de conducta: la suite completa, la Fase 0, PostgreSQL con TLS, el
  simulacro de respaldo y la prueba de humo automática pasan, y el envío seguro se comporta igual con Streamlit 1.65.0.
- Falta: las firmas docentes (B-5). Después, el contrato de
  promoción (16.4), con el preflight sobre los Secrets reales del piloto.
- B-3, B-4 y B-6 se resolvieron sin cambiar la conducta del runtime: el preflight (una herramienta que la app no
  importa), la versión de Streamlit con que ya se había verificado todo y dos scripts de regresión (sección 14).
- No se desplegó; no se hizo push, merge, PR ni release; no se empezó la Fase 1.

## 14. Resolución de B-3, B-4 y B-6 (2026-10-06)

Encargo: resolver sólo B-3, B-4 y B-6, sin desplegar, sin push y sin tocar la conducta clínica del runtime. Tres
commits de código y uno de documentación, locales. B-1, B-2 y B-5 no se trabajaron.

### 14.1 B-3 · El preflight falla cerrado (`87bbbe1`)

Cambian sólo `tools_pilot_preflight.py` (una herramienta: ningún módulo la importa) y su prueba. La app, el
manifiesto y `pilot_freeze.py` no cambiaron.

- **Lee la configuración como la app.** Los Secrets, con el analizador de Streamlit; al entorno pasan con la regla de
  Streamlit (sólo texto y números: un booleano TOML nunca llega); `st.secrets` se arma con los mismos valores.
  Después pregunta a los lectores de la app (`offline_cases`, `image_scene`, `account_portal`, `clinical_scene`) qué
  harían, y al terminar restaura el entorno y `st.secrets`.
- **Con `--secrets`, el archivo es toda la configuración del despliegue:** las variables locales `MRS_*`,
  `STREAMLIT_*` y `OPENAI_API_KEY` quedan fuera y se nombran, sin su valor, en el AVISO `local_environment`. La
  revisión adversarial propia lo encontró: sin esto, el entorno de quien corre el preflight podía tapar un error de
  los Secrets.
- **Cada exigencia del manifiesto es una regla obligatoria** (`FREEZE_RULES`, una por cada `RUNTIME_FLAGS`):

  | Exigencia del manifiesto | Regla | Falla si |
  |---|---|---|
  | `[runner] fastReruns = false` | `fast_reruns` | El `.streamlit/config.toml` del commit que se despliega (leído con `git show`) falta o no tiene el booleano `false`, ese commit no se puede determinar, o `STREAMLIT_RUNNER_FAST_RERUNS` lo sobrescribe |
  | `MRS_OFFLINE_CASES=1` | `offline_cases` | `offline_cases_enabled()` es falso con la configuración que la app recibe: booleano TOML, `"0"`, `"off"`, vacío o ausente |
  | `MRS_PAID_GENERATION=off` | `paid_generation_off` | `paid_generation_allowed` la abre a alguna cuenta. Se evalúa sin el modo sin conexión, que también la cierra: el congelamiento exige los dos |
  | `MRS_FREE_GENERATION` ausente | `free_generation_closed` | Tiene un valor, en los Secrets o en el entorno con que arranca la app |
  | `MRS_DEFAULT_VARIANT` ausente | `no_pinned_case` | Tiene un valor, cualquiera, en los Secrets o en el entorno con que arranca la app |
  | `MRS_REPLAY_CASE` ausente | `no_replay_case` | Tiene un valor |
  | `MRS_CODE_VERSION` = commit desplegado | `code_version` | No llega al entorno de la app, no tiene de 7 a 40 caracteres hexadecimales, no es el commit que se despliega (`--commit`, o el HEAD de la copia) o ese commit no se puede determinar |
  | `MRS_IMAGE_REQUIRE_REVIEW=on` | `image_review` | `review_required()` es falso para la app |

- **Siguen obligatorias:** `auth_mode`, `database_url`, `no_local_sqlite`, `admin_bootstrap` (si están esas claves) y,
  con `--connect`, `database_reachable`. `provider_key_withheld` falla si hay una clave del proveedor y la app la
  leería. Recomendaciones (AVISO, nunca FALLA): `no_batch_settings`, `local_environment` y, con `--connect`,
  `administrator`.
- **Falla cerrado.** Una regla que no se puede evaluar falla («no se pudo evaluar (<clase>)»). Unos Secrets
  ilegibles dan la FALLA `secrets_readable`, y sin ninguna regla evaluada el resultado es «NO LISTA». El código de
  salida es 0 sólo con «LISTA». Nunca imprime un valor, una clave, una URL ni un hash: un error se nombra sólo por su
  clase.
- **Pruebas A–J del encargo** (`test_tools_pilot_preflight.py`):

  | Prueba | Dónde |
  |---|---|
  | A · La configuración congelada pasa, sin imprimir secretos | `test_a_the_frozen_configuration_passes_and_no_secret_is_printed` |
  | B · `MRS_OFFLINE_CASES = true` (booleano TOML) falla | `test_b_offline_as_a_toml_boolean_fails` |
  | C · `MRS_OFFLINE_CASES` ausente falla | `test_c_offline_missing_fails` |
  | D · Cualquier variante fijada falla, en los Secrets o en el entorno | `test_d_any_pinned_case_fails` |
  | E · `MRS_DEFAULT_VARIANT=trauma_hemothorax_41m` nunca da un preflight exitoso | `test_e_the_excluded_haemothorax_can_never_pass_the_preflight`: con todo lo demás congelado, una sola FALLA, «NO LISTA» y código 1, también por `main()` |
  | F · `MRS_REPLAY_CASE` falla | `test_f_a_replay_case_fails` |
  | G · La revisión de fotos distinta de «on» falla | `test_g_image_review_not_on_fails` |
  | H · Generación pagada o libre fuera del congelamiento falla | `test_h_paid_and_free_generation_outside_the_freeze_fail` |
  | I · El commit que se despliega pasa | `test_i_the_commit_to_deploy_passes` |
  | J · Commit ausente, distinto, no hexadecimal o no determinable falla | `test_j_a_missing_or_different_commit_fails`, `test_j_without_the_commit_to_deploy_the_version_cannot_pass` |

  Además:
  - el preflight y el cargador real de Streamlit, en un proceso aparte, coinciden en el modo sin conexión y en la
    generación pagada;
  - `test_every_freeze_requirement_is_a_required_rule` falla si el manifiesto gana una exigencia sin su regla
    obligatoria;
  - `fastReruns` se lee del commit: `13592e4`, sin `config.toml`, falla;
  - el entorno local no tapa los Secrets;
  - el entorno y `st.secrets` quedan como estaban;
  - siguen las pruebas de C10-06.
- **Resultado:** 70 de 70, en el entorno del contenedor de desarrollo (con `MRS_BATCH_*` definidas) y en un entorno
  vacío.
- **Uso:** el del runbook (§3, paso 3), sin cambios: en una copia del commit aprobado,
  `python3 tools_pilot_preflight.py --secrets ruta/a/secrets.toml --connect`; desde otra copia, con
  `--commit <sha>`.

### 14.2 B-4 · Streamlit fijo en 1.64.0 (`4d570a8`)

- **`requirements.txt`:** `streamlit==1.64.0`, con su motivo en un comentario. Los demás rangos no cambian:
  `reportlab>=4.2,<5`, `pypdf>=5,<7`, `openai>=2,<3` y `psycopg[binary]>=3.2,<4`.
- **Por qué 1.64.0:** la Fase 0 certificó el envío seguro con 1.64.0: write-ahead, una ejecución por clic, recarga,
  recuperación y `fastReruns = false`. La suite completa también corrió con 1.64.0. La 1.65.0 se verificó sólo en las
  pruebas de la Fase 0 y en 0D (9.4). Una versión nueva se revisa después del piloto; no la instala un reinicio.
- **Verificación:**
  - una resolución desde cero de `requirements.txt` (entorno virtual vacío, Python 3.11,
    `pip install --dry-run --report`) da `streamlit 1.64.0`, entre 51 paquetes;
  - el entorno de las pruebas tiene 1.64.0 instalada, y `pip check` no encuentra conflictos;
  - las pruebas sensibles al envío y a Streamlit pasan, 55 de 55: `test_phase0_submission_guard.py`,
    `test_phase0_answer_parity.py` y `test_phase0_acceptance_page.py`;
  - `regression_v087_pdf_export.py`, que lee `requirements.txt`, pasa.
- **No se fijó, y queda declarado:**
  - Python: se elige al crear la app en Streamlit Community Cloud y queda en B-2;
  - los demás paquetes directos;
  - las dependencias de Streamlit: un reinicio puede tomar versiones nuevas dentro de los rangos que declara
    Streamlit 1.64.0.

  El encargo pidió no fijar dependencias ajenas sin necesidad.

### 14.3 B-6 · Las dos regresiones siguen al código de la Fase 0 (`e200ccc`)

| Script | Texto esperado antes | Ahora |
|---|---|---|
| `regression_v06020_management_trace.py` | `def record_management_trace(learner_input, parsed, result, state_before, state_after):` | `…, state_before, state_after, turn=None):` |
| `regression_v06020_management_trace.py` y `regression_v06021_management_trace_ui.py` | `"interpreted_action": deepcopy(parsed.get("actions", []))` | `"interpreted_action": [_untag(a) for a in deepcopy(parsed.get("actions", []))]` |

- **Misma intención:** cada script sigue exigiendo lo de antes:
  - la entrada;
  - la acción interpretada que dio el lector;
  - el estado antes y después;
  - el esquema `management_trace_v1`;
  - en v06021, la vista del desarrollador;
  - en v06020, el orden instantánea → ejecución → instantánea.

  `_untag` es `order_ledger.strip_tags`: quita sólo las claves internas del ledger, las que empiezan con «_». Cada
  script dice el motivo en un comentario.
- **No se debilitaron.** Se probaron cinco mutaciones de `app.py`, en una copia aparte; cada una hace fallar al menos
  un script:

  | Mutación | v06020 | v06021 |
  |---|---|---|
  | `interpreted_action` vacío, no lo que dio el lector | falla | falla |
  | `state_after` no se registra | falla | falla |
  | El registro pierde `state_after` de su firma | falla | pasa (sólo exige que la función exista, como antes) |
  | La instantánea posterior deja de tomarse después de ejecutar | falla | pasa (no mira el orden, como antes) |
  | Se quita la vista del desarrollador | pasa (no la mira, como antes) | falla |

- **Resultado:**
  - `run_regressions.py`: «PASS: 56/56 active regression scripts; 10 retired», código 0;
  - ninguna regresión se retiró; siguen retiradas las 10 de P-11;
  - `test_regression_scripts_are_active_or_retired.py` pasa, 3 de 3.

### 14.4 Recertificación

- **Pruebas focalizadas durante el trabajo** (Python 3.11.15, Streamlit 1.64.0):
  - preflight, 70 de 70;
  - envío, paridad y página, 55 de 55;
  - congelamiento y enrutamiento (los archivos de 9.1), 59 de 59, con 25 subpruebas;
  - contabilidad de regresiones, 3 de 3;
  - regresiones activas, 56 de 56.
- **Sobre el candidato final** (el commit de esta actualización, con el árbol limpio) se corren la suite completa,
  las pruebas de PostgreSQL 16 local con TLS y `run_regressions.py`. Sus resultados se informan en la entrega del
  encargo: anotarlos aquí cambiaría el candidato. La prueba en el proveedor sigue siendo B-1.

## 15. B-2 · Entorno de despliegue del piloto (2026-10-07)

**Superada por la sección 16 (2026-10-07)** en todo lo que dependía de las cuentas. Con los datos confirmados en los
proveedores, B-2 quedó resuelto. Esta sección se conserva como registro del estado anterior.

Encargo: definir dónde y cómo correrá el piloto congelado, para que el despliegue sea deliberado y reproducible. Sin
desplegar, sin push y sin crear ramas. **Resultado: B-2 BLOCKED.** El diseño queda definido, pero faltan datos que
sólo están en las cuentas de Streamlit y de Neon (15.12 y 15.13). Este encargo sólo agrega documentación: no cambió
el runtime, ninguna cuenta ni ninguna configuración.

### 15.1 Verificación inicial

| Comprobación | Resultado |
|---|---|
| Rama | `clinical-encounter-v0.13` |
| HEAD local | `5cbedf173eb4614a2e8a5553c3c2d618533ca39b` |
| `origin/clinical-encounter-v0.13` | `009aadb` (comprobado con `git ls-remote`) |
| Adelante / atrás | 5 / 0 |
| Árbol | Limpio |
| Cambios fuera de `docs/` desde `009aadb` | Sólo los de B-3, B-4 y B-6: el preflight y su prueba, `requirements.txt` y dos scripts de regresión |
| Fase 1 o núcleo común | Ninguno: una sola rama local, sin stash; los 5 commits son de preparación para el despliegue |
| Ramas del remoto | `main` (`9edb427`, ancestro de HEAD), `ai-integration-v0.9.0` y `clinical-encounter-v0.13` |

### 15.2 Mecanismo de despliegue actual

Clasificación:
- **VERIFICADO:** comprobado en el repositorio.
- **DOCUMENTADO, NO VERIFICADO:** lo dice el repositorio o la documentación del proveedor, pero no se comprobó en la
  cuenta. La documentación del proveedor se consultó por búsqueda, porque el proxy de este entorno bloquea
  `docs.streamlit.io`.
- **DESCONOCIDO:** requiere la interfaz o la cuenta.

| Elemento | Qué se sabe | Fuente | Clasificación |
|---|---|---|---|
| Plataforma | Streamlit Community Cloud (`share.streamlit.io`) | `docs/SETUP_v0.11.0.md`, `docs/TANDA_LOCAL.md`, `docs/TANDA_20_ESCENARIOS.md`; `account_portal._on_streamlit_cloud` (checkout bajo `/mount/src`) | DOCUMENTADO, NO VERIFICADO |
| Punto de entrada | `app.py`, en la raíz | El archivo; `.devcontainer/devcontainer.json` y las guías corren `streamlit run app.py` | El archivo: VERIFICADO. El que tiene configurado cada app: DESCONOCIDO |
| Apps existentes | **Desarrollo:** `clinical-management-reasoning-dev.streamlit.app`, sigue `clinical-encounter-v0.13`. **IA:** `clinical-management-reasoning-ai.streamlit.app`, sigue `ai-integration-v0.9.0` y guarda la clave del proveedor. Se nombran también una app «pública» o «de producción» y una «de validación», sin URL ni rama | Desarrollo: `docs/UPDATE_v0.13.1.md`, `docs/TANDA_LOCAL.md`, `docs/LONGITUDINAL_PROGRESS.md`. IA: `docs/UPDATE_v0.12.1.md`, `docs/DEMO_RESEARCH_2026-09-23.md`, `docs/SETUP_v0.11.0.md`. Las otras: `docs/TANDA_20_ESCENARIOS.md`, `docs/LONGITUDINAL_PROGRESS.md` | Desarrollo e IA: DOCUMENTADO, NO VERIFICADO. Pública y validación: DESCONOCIDO |
| Rama de la app del piloto | La app no está identificada en el repositorio | — | DESCONOCIDO |
| Push → redespliegue | La app sigue su rama y toma cada commit; un cambio de dependencias provoca un redespliegue completo | `docs/TANDA_LOCAL.md` (observado el 2026-09-25); proveedor | DOCUMENTADO, NO VERIFICADO |
| Reinicio | Tras un push, los módulos ya importados siguen corriendo hasta «Reboot app»; al reiniciar, el proveedor vuelve a resolver las dependencias | `docs/TANDA_LOCAL.md`, `docs/UPDATE_v0.12.1.md`; proveedor | DOCUMENTADO, NO VERIFICADO |
| Python | Ningún archivo lo fija: no hay `runtime.txt`, `.python-version`, `pyproject.toml`, `Pipfile`, `environment.yml` ni `uv.lock`. `.devcontainer` usa una imagen 3.11 sólo para Codespaces. El proveedor lo elige en «Advanced settings» al crear la app; para cambiarlo hay que borrar la app y volver a desplegarla; por omisión, 3.12 | Repositorio; proveedor | Repositorio: VERIFICADO. Proveedor: DOCUMENTADO, NO VERIFICADO. El de cada app: DESCONOCIDO |
| Dependencias | `requirements.txt` en la raíz, único archivo de dependencias, con `streamlit==1.64.0`; el proveedor usa el primero que encuentra | Repositorio; proveedor | Archivo: VERIFICADO. Instalación: DOCUMENTADO, NO VERIFICADO |
| Secrets | Panel «App settings → Secrets» de cada app (o «Advanced settings» al crearla). Las claves raíz de texto o número pasan al entorno; un booleano TOML no | `docs/SETUP_v0.11.0.md`; proveedor; código de Streamlit 1.64.0 (14.1) | Panel: DOCUMENTADO, NO VERIFICADO. Regla de copia: VERIFICADO |
| Base | `MRS_DATABASE_URL` de los Secrets; psycopg, una conexión por transacción, TLS según `sslmode`; `check_database.describe` rechaza una URL sin `sslmode` | Código | VERIFICADO |
| Imágenes y archivos | `assets/` viaja en el checkout (fotos, `approvals.json`, fuentes); el paquete de fotos se importa a la base al abrir la página; el disco de la plataforma es efímero | Código; `docs/SETUP_v0.11.0.md` | Código: VERIFICADO. Disco: DOCUMENTADO, NO VERIFICADO |

### 15.3 Topología propuesta

```
clinical-encounter-v0.13   desarrollo: sigue recibiendo commits (la Fase 1, cuando se abra); su app es la de desarrollo
        │
        │  promoción explícita de un SHA aprobado (15.8); nunca un merge automático
        ▼
pilot-residents-v1         rama del piloto: sólo promociones
        │
        │  la app del piloto sigue sólo esta rama (Python 3.11, app.py)
        ▼
app del piloto             Streamlit Community Cloud: una app nueva, con sus propios Secrets
        │
        │  MRS_DATABASE_URL, sólo en sus Secrets
        ▼
base del piloto            Neon: una base vacía usada sólo por el piloto; nunca la de desarrollo ni `production`
```

**Encaja con el mecanismo.** El proveedor documenta que cada app se vincula a un repositorio, una rama y un archivo
principal, y el repositorio ya usa una base de Neon por app, sin compartir cuentas (`docs/TANDA_20_ESCENARIOS.md`).
Con una rama propia, un push de desarrollo no llega a la app del piloto.

- **Nombre de la rama:** `pilot-residents-v1`.
- **Cuándo se crea:** en la promoción, no antes. Apunta exactamente al SHA candidato final, que descenderá de
  `5cbedf1` y se construirá después de cerrar B-5. Con tu autorización expresa:
  `git push origin <SHA>:refs/heads/pilot-residents-v1`. Eso sube sólo esa rama: no empuja `clinical-encounter-v0.13`
  ni redespliega la app de desarrollo.
- **Reglas:**
  - la rama avanza sólo por promoción, en avance rápido, a un SHA que cumplió el contrato (15.8);
  - nunca recibe un commit directo, un merge desde desarrollo ni trabajo de la Fase 1;
  - cada avance cambia `MRS_CODE_VERSION` en la misma ventana;
  - conviene protegerla en GitHub (sin force-push y con push restringido). Es una acción externa, y no se verificó qué
    permite el plan.
- **Correcciones urgentes:**
  1. una rama corta `pilot-hotfix-<tema>` desde el SHA del piloto, con el cambio mínimo;
  2. el contrato completo: suite, regresiones, B-1 si toca la base, firma si cambia un texto y preflight;
  3. una ventana sin encuentros abiertos (15.10);
  4. avance rápido de `pilot-residents-v1`, `MRS_CODE_VERSION` nuevo, «Reboot app» y prueba de humo corta;
  5. después, la corrección vuelve a desarrollo.
- **Que el desarrollo no redespliegue el piloto:** la app del piloto no sigue `clinical-encounter-v0.13`, y eso se
  confirma en su configuración antes del primer despliegue. Nadie empuja a `pilot-residents-v1` fuera de una
  promoción.

### 15.4 La app del piloto: DESCONOCIDA

Ninguna app documentada es la del piloto:
- la de desarrollo sigue la rama de desarrollo, justo lo que se quiere evitar;
- la de IA sigue `ai-integration-v0.9.0` y guarda la clave del proveedor;
- la pública y la de validación no tienen URL ni rama en el repositorio.

`docs/DEMO_RESEARCH_2026-09-23.md` ya recomendaba una app nueva para no tocar las existentes.

**Recomendación: una app nueva para el piloto:**
- repositorio `management-reasoning-simulator` (en GitHub);
- rama `pilot-residents-v1`;
- archivo principal `app.py`;
- Python 3.11;
- Secrets propios.

Hasta que se identifique, B-2 no puede resolverse. Lo mínimo que hace falta es la lista de 15.12.

### 15.5 Python 3.11

- **Hoy no está fijado.** No lo fija ningún archivo del repositorio, y el proveedor documenta sólo la elección en
  «Advanced settings»: según esa documentación, en esta plataforma ningún archivo lo impone.
- **Método:** al crear la app del piloto, elegir Python 3.11 en «Advanced settings» y confirmarlo en su configuración
  antes del preflight. Por omisión sería 3.12. Cambiarlo después obliga a borrar la app y volver a desplegarla, con
  su subdominio y sus Secrets.
- **Requiere** la configuración del proveedor, no un cambio del repositorio.
- **Verificación:** la app no registra la versión de Python en el encuentro, así que se comprueba en la plataforma, no
  en la exportación.

### 15.6 Base de datos

- **Proveedor documentado:** Neon, proyecto `management-reasoning-simulator` (`lingering-lab-61668857`)
  (`docs/CLINICAL_DEV_DATABASE.md`, 2026-09-13):

  | Rama de Neon | ID | Uso documentado |
  |---|---|---|
  | `production` | `br-plain-violet-auc7cg5w` | Producción. **Nunca** para pruebas ni para el piloto |
  | `development-validation` | `br-hidden-morning-aut38evw` | Validación; madre de la de desarrollo |
  | `clinical-encounter-v0.13` | `br-bitter-block-auena1gu` | Base `mrs`, preparada para la app de desarrollo |

- **Base del piloto: DESCONOCIDA.** No está identificada en el repositorio.
- **Cómo llega la conexión:** con `MRS_DATABASE_URL` en los Secrets de la app: la URL *pooled* del proveedor, con
  `sslmode=require` y nunca en Git.
- **Versión mayor de PostgreSQL:** DESCONOCIDA. Según el proveedor, es una sola por proyecto: todas sus ramas la
  comparten.
- **Acceso:** desde este entorno no se llega a Neon, porque el proxy no admite conexiones TCP a bases
  (`docs/IMAGENES_REGISTRO.md`), y esta sesión no tiene conector de Neon.
- **Lo que se exige:** una base vacía, usada sólo por la app del piloto, con su propio rol y su propia URL. Nunca en
  `production` y nunca con datos reales para pruebas.
- **Dos maneras, a tu decisión:**
  - (a) un proyecto de Neon aparte, sin datos heredados y con credenciales propias;
  - (b) una rama nueva del proyecto existente con una base nueva, `mrs_pilot`. Según el proveedor, una rama nueva
    hereda los datos de su madre: la app del piloto no usaría esa copia.

  B-1 va en el mismo proyecto que la base del piloto, para tener la misma versión mayor.
- **Convenciones del repositorio:** las respetan las dos: una base por app y sin cuentas compartidas.

### 15.7 Configuración del piloto (sólo nombres)

Desde aquí no se puede ver ningún valor del destino. Lo verifica el preflight cuando se corre con los Secrets del
destino (`--secrets <archivo> --commit <SHA> --connect`): ése es el gate.

| Setting | Valor o estado exigido | ¿Secreto? | Dónde | ¿Verificable ahora? | Regla del preflight |
|---|---|---|---|---|---|
| `MRS_AUTH_MODE` | `"accounts"` | NO | Secrets | NO | `auth_mode` |
| `MRS_DATABASE_URL` | URL *pooled* de la base del piloto, `sslmode=require` | **SÍ** | Secrets | NO | `database_url`; con `--connect`, `database_reachable` |
| `MRS_OFFLINE_CASES` | `"1"`, como texto | NO | Secrets | NO | `offline_cases` |
| `MRS_PAID_GENERATION` | `"off"`, como texto | NO | Secrets | NO | `paid_generation_off` |
| `MRS_FREE_GENERATION` | Ausente | NO | — | NO | `free_generation_closed` |
| `MRS_DEFAULT_VARIANT` | Ausente | NO | — | NO | `no_pinned_case` |
| `MRS_REPLAY_CASE` | Ausente | NO | — | NO | `no_replay_case` |
| `MRS_CODE_VERSION` | El SHA desplegado, como texto | NO | Secrets | NO | `code_version` |
| `MRS_IMAGE_REQUIRE_REVIEW` | `"on"` | NO | Secrets | NO | `image_review` |
| `OPENAI_API_KEY` | Ausente (runbook §2) | **SÍ** | — | NO | `provider_key_withheld` |
| `MRS_ALLOW_LOCAL_SQLITE` | Ausente | NO | — | NO | `no_local_sqlite` |
| `MRS_ADMIN_USERNAME`, `MRS_ADMIN_PASSWORD_HASH` | Sólo hasta crear el primer administrador; después, ausentes | El hash: **SÍ** | Secrets | NO | `admin_bootstrap` |
| `MRS_SYNTHETIC_ACCOUNTS`, `MRS_BATCH_*` | Ausentes | Contraseñas: **SÍ** | — | NO | `no_batch_settings` (AVISO) |
| `.streamlit/config.toml` `[runner] fastReruns` | `false` en el commit | NO | Repositorio | SÍ: `false` en `5cbedf1` | `fast_reruns` |
| `STREAMLIT_RUNNER_FAST_RERUNS` | Ausente | NO | — | NO | `fast_reruns` |
| `MRS_PUBLIC_APP_URL` | La URL pública de la app del piloto: https, sin credenciales. Sin ella, el enlace del PDF docente apunta a `clinical-management-reasoning-ai.streamlit.app` | NO | Secrets | NO | Ninguna (fuera del manifiesto; TD-75) |
| `MRS_IMAGE_BANK` | Ausente: el banco está activo por omisión. `off` devolvería la sala a las fotos de sesión, sin el banco aprobado ni el orden de TD-56 | NO | — | NO | Ninguna (fuera del manifiesto; TD-75) |
| `MRS_LANGUAGE` | Opcional: idioma inicial de la pantalla (`es` o `en`); el lector lo cambia. Decisión docente, con B-5 | NO | Secrets | — | Ninguna |
| `APP_PASSWORD` | Ausente (recomendado): con `accounts` no da acceso | **SÍ** | — | NO | Ninguna |
| `MRS_DEFAULT_CHALLENGE` | Ausente: con cuentas no cambia el desafío del residente, sólo el selector sin cuentas | NO | — | NO | Ninguna |
| `MRS_ANALYSIS_CORRECTIONS` | Ausente: cambiaría el texto de los informes guardados | NO | — | NO | Ninguna |
| `OPENAI_MODEL`, `MRS_*_MODEL`, `MRS_AI_*`, `MRS_IMAGE_BUDGET_*`, `MRS_DIAGNOSTIC_DIR` | Ausentes: sin clave y sin conexión no tienen efecto | NO | — | NO | Ninguna |

Para las fotos no hace falta ningún secreto: llegan con `assets/patient_images` y sus aprobaciones esperan la cuenta
que nombran (TD-56, sección 7).

### 15.8 Contrato de promoción

Nunca se despliega «lo último»: el piloto corre siempre un SHA conocido.

1. Firmas docentes completas (B-5).
2. Commit candidato final en `clinical-encounter-v0.13`, descendiente de `5cbedf1`, con el árbol limpio y su SHA
   completo anotado.
3. Suite completa con 0 FAILED sobre ese SHA, con Streamlit 1.64.0 y Python 3.11.
4. `run_regressions.py`: 56/56.
5. B-1 en verde: las cuatro pruebas de PostgreSQL, 23/23, contra la base descartable del proveedor (15.11).
6. Promoción: `pilot-residents-v1` se crea, o avanza, exactamente a ese SHA, con autorización expresa (15.3).
7. `MRS_CODE_VERSION` igual a ese SHA en los Secrets de la app del piloto.
8. Preflight con esos Secrets: `python3 tools_pilot_preflight.py --secrets <archivo> --commit <SHA> --connect`.
   Debe dar «LISTA», sin FALLA y sin AVISO de `no_batch_settings`.
9. Despliegue de la app del piloto sobre `pilot-residents-v1` (Python 3.11, `app.py`), y «Reboot app». Si la base
   ya tiene encuentros, la consulta de 15.10 debe dar 0 antes.
10. Prueba de humo desplegada (sección 11).
11. Fotos (TD-56): `check_database.py --photo-approvals` debe terminar en «All 117 approvals…».
12. GO explícito del docente responsable (condición C).

### 15.9 Riesgo de autodespliegue: **RISK**

- **Qué está documentado:** un push a `clinical-encounter-v0.13` redespliega la app de desarrollo,
  `clinical-management-reasoning-dev` (`docs/TANDA_LOCAL.md`, observado el 2026-09-25; el proveedor dice que cada app
  toma los commits de su rama).
- **Qué no se sabe:** si otra app sigue esa rama (DESCONOCIDO).
- **Qué haría un push hoy:** llevaría a la app de desarrollo los 5 commits locales, incluida la fijación de
  Streamlit, que provoca un redespliegue completo. Además cortaría cualquier encuentro abierto en esa app.
- **Regla:** no hacer push a `clinical-encounter-v0.13` hasta conocer qué apps siguen esa rama. Los 5 commits siguen
  sólo en local.

### 15.10 Encuentros abiertos antes de desplegar

- **No hay herramienta ni pantalla que los liste** (TD-74). La regla es de procedimiento.
- **Sí hay un método práctico:** tres consultas de sólo lectura sobre la base del piloto. Devuelven conteos, nunca
  identidades. Se probaron en PostgreSQL 16 local con el esquema de la app, sobre la base del simulacro:

  ```
  -- 1. Encuentros abiertos del piloto: debe ser 0 para desplegar
  SELECT COUNT(*) FROM mrs_attempts WHERE status = 'active' AND is_sandbox = 0;
  -- 2. De ellos, los tocados en las últimas 2 horas
  SELECT COUNT(*) FROM mrs_attempts WHERE status = 'active' AND is_sandbox = 0
     AND updated_at > EXTRACT(EPOCH FROM now())::bigint - 7200;
  -- 3. Residentes con una sesión sin vencer (la sesión dura 12 horas fijas, account_store)
  SELECT COUNT(DISTINCT s.user_id) FROM mrs_sessions s JOIN mrs_users u ON u.id = s.user_id
   WHERE u.role = 'resident' AND u.active = 1 AND s.expires_at > EXTRACT(EPOCH FROM now())::bigint;
  ```

- **Cómo correrlas:** con `psql "$MRS_DATABASE_URL" -Atc "<consulta>"`, con la URL en una variable y nunca impresa.
- **Límites:** la consulta 3 es una aproximación: dice quién entró en las últimas 12 horas, no quién tiene la página
  abierta. Las conexiones vivas de Streamlit no quedan en la base.
- **Chequeo mínimo del operador, justo antes de cada ventana:**
  1. avisar la ventana;
  2. correr las tres consultas;
  3. si la 1 no da 0, no desplegar. Se pide a la persona residente que cierre («Complete Encounter & Begin
     Review») o que termine el intento («End this attempt without completing review»), o se posterga. El
     administrador no puede cerrar un encuentro ajeno;
  4. anotar los conteos, la hora y el SHA en el registro del despliegue (runbook §4).

### 15.11 Objetivo de B-1 (preparado, no corrido)

Hoy no hay ninguna base descartable equivalente disponible, así que B-1 no se corrió. Así se correrá, una vez
identificado el proveedor de la base del piloto:

- **Dónde:** en el proyecto de Neon de la base del piloto, para tener la misma versión mayor:
  - una rama descartable nueva, `b1-disposable-AAAAMMDD`, cuya madre no tenga datos reales: nunca `production` ni la
    rama del piloto una vez que tenga encuentros;
  - dentro de ella, una base nueva y vacía, `mrs_b1`.

  Nunca la base `mrs` de desarrollo, nunca la del piloto y nunca `production`.
- **Conexión:** el mismo tipo de endpoint que usará la app (*pooled*), con `sslmode=require`.
- **Desde dónde:** desde un equipo con red directa a Neon. Este entorno no llega.
- **Comandos existentes:**

  ```
  export MRS_TEST_POSTGRES_URL='postgresql://…/mrs_b1?sslmode=require'   # sólo la base descartable
  python3 -m pytest -q test_phase0_submission_guard_on_postgres.py test_store_integrity_on_postgres.py \
    test_the_image_bank_on_postgres.py test_p07_75f_arrives_with_the_neutral_view.py
  ```

  Se esperan 23 aprobadas (10 + 5 + 4 + 4), como en PostgreSQL 16 local con TLS.
- **Opcional:** `python3 tools_backup_drill.py --postgres '<otra base vacía>'`, si el rol puede crear bases (crea
  `<nombre>_restored`).
- **Seguridad:** estas pruebas ejecutan `DROP SCHEMA public CASCADE` en la base que reciben. Antes de correrlas se
  confirma que la URL nombra `mrs_b1`. Ningún dato real entra: la base está vacía y la rama no viene de una con datos
  reales.
- **Limpieza:** se borra la rama descartable en la consola de Neon, y con ella sus bases. Se anotan el resultado, la
  versión mayor y la fecha.
- **Límite:** desde ese equipo no se reproduce la red entre Streamlit Cloud y Neon. Eso lo cubre la prueba de humo
  desplegada.

### 15.12 Acciones externas que faltan (sin contraseñas ni valores secretos)

**Streamlit Community Cloud**

- [ ] Lista de las apps del workspace con nombre o URL, repositorio, rama conectada, archivo principal y Python. Basta
  una captura de la lista o del «Settings» de cada una. Sobre todo: **¿qué apps siguen `clinical-encounter-v0.13`?**
- [ ] Decisión: app nueva para el piloto (recomendado) o una existente. Si es nueva, el subdominio que quieres y el
  workspace.
- [ ] Confirmar que «Advanced settings» ofrece Python 3.11 al crear una app (captura, sin Secrets).

**GitHub**

- [ ] Aprobar el nombre `pilot-residents-v1`. La rama se crea sólo en la promoción y con autorización.
- [ ] Decidir si se protege la rama: sin force-push y con push restringido.

**Neon**

- [ ] Dónde vive la base del piloto: (a) proyecto aparte o (b) rama del proyecto `management-reasoning-simulator`.
  Con su nombre.
- [ ] Versión mayor de PostgreSQL de ese proyecto (está en su configuración).
- [ ] Crear, o autorizar que se cree, la rama descartable de B-1 con una base vacía, y decir quién corre la prueba y
  desde qué equipo.
- [ ] Confirmar que `production` no se toca y que el plan permite las ramas o el proyecto nuevos.

### 15.13 Criterios de aceptación de B-2

| # | Criterio | Estado |
|---|---|---|
| 1 | Proveedor | Streamlit Community Cloud: DOCUMENTADO, NO VERIFICADO en la cuenta |
| 2 | App exacta del piloto | **NO**: no está identificada |
| 3 | Repositorio exacto | SÍ: `management-reasoning-simulator` (en GitHub) |
| 4 | Estrategia de rama | SÍ: `pilot-residents-v1`, sólo promociones (15.3); sin crear |
| 5 | Punto de entrada | SÍ: `app.py` |
| 6 | Python 3.11 | **NO VERIFICADO**: el método es la elección al crear la app (documentado por el proveedor); falta confirmarlo en la plataforma |
| 7 | Proveedor y proyecto de la base del piloto | **NO**: el proveedor es Neon (documentado); el proyecto, la rama y la base, sin identificar |
| 8 | Base descartable equivalente para B-1 | **NO**: el camino está definido (15.11), pero hay que crearla, y la versión mayor es desconocida |
| 9 | Lugar de los Secrets | SÍ: el panel de Secrets de la app del piloto; los nombres están en 15.7 |
| 10 | Autodespliegue entendido | **NO**: la app de desarrollo sigue la rama de desarrollo (documentado); las demás vinculaciones, desconocidas |
| 11 | El desarrollo no puede modificar el piloto | Por diseño, SÍ (rama y app propias); falta confirmarlo con 2 y 10 |
| 12 | Promoción de un SHA final | SÍ (15.8) |
| 13 | Chequeo de encuentros abiertos | SÍ (15.10): de procedimiento, con consultas probadas |
| 14 | Preflight contra el destino | SÍ, como capacidad (`--secrets`, `--commit` y `--connect`); falta el archivo de Secrets del destino |

**B-2: BLOCKED.** Falta la información externa de 15.12. Con ella se completan los criterios 2, 6, 7, 8, 10 y 11, y
B-2 puede revisarse.

## 16. B-2 resuelto y B-1 preparado (2026-10-07)

Encargo: cerrar B-2 con los datos que la persona responsable confirmó en las interfaces de los proveedores, y dejar
B-1 listo para correrse sin riesgo. Sin desplegar, sin push y sin crear la app, la rama de Git ni ramas de Neon. Sólo
documentación.

**Resultado:**
- B-2: **RESUELTO**.
- B-1: **READY TO EXECUTE / NOT YET EXECUTED**.
- B-5: **BLOCKED**.
- Sigue **NOT READY FOR DEPLOYMENT**.

### 16.1 Verificación inicial

| Comprobación | Resultado |
|---|---|
| Rama | `clinical-encounter-v0.13` |
| HEAD local | `82bdc51618a598d4b267a5bd9a118b8fb59698ce` |
| `origin/clinical-encounter-v0.13` | `009aadb` (comprobado con `git ls-remote`) |
| Adelante / atrás | 6 / 0 |
| Árbol | Limpio |
| Commits después de `009aadb` | Los seis son de preparación para el despliegue. Fuera de `docs/`, sólo el preflight y su prueba, `requirements.txt` y dos scripts de regresión |
| Fase 1 o núcleo común | Ninguno. Una sola rama local, sin stash; `pilot-residents-v1` no existe en el remoto |

### 16.2 Datos confirmados en los proveedores (2026-10-07)

Los confirmó la persona responsable en las interfaces de Streamlit y de Neon. No se verificaron desde este entorno,
que no tiene acceso a esas cuentas.

**Streamlit Community Cloud**
- Es el proveedor de alojamiento.
- Hay tres apps del repositorio `management-reasoning-simulator`, todas con `app.py`: una por cada rama
  (`ai-integration-v0.9.0`, `clinical-encounter-v0.13` y `main`).
- La app de desarrollo, `clinical-management-reasoning-dev`, sigue `clinical-encounter-v0.13` y usa Python 3.12.
- Al crear una app se puede elegir Python 3.11.
- La app de desarrollo no se modifica para el piloto.

**Neon**
- Proyecto `management-reasoning-simulator`, con PostgreSQL 17.
- Ramas visibles: `production` (por omisión), `development-validation` y `clinical-encounter-v0.13`. Las dos últimas
  están archivadas.

**Decisiones**
- El piloto usará una app nueva, `clinical-management-reasoning-pilot`: repositorio
  `management-reasoning-simulator`, rama `pilot-residents-v1`, `app.py` y Python 3.11. Todavía no existe.
- La base del piloto irá en el mismo proyecto de Neon, en una rama propia, `pilot-residents-v1`.
- B-1 usará una rama temporal, `pilot-b1-validation`, con la base `mrs_b1`. Se borra después, y sólo con
  autorización expresa.
- B-1 no usa datos de producción.

**Correcciones a la sección 15:** la app de `main` existe (15.2 no podía saberlo), y la versión mayor de PostgreSQL
es 17 (15.6 la daba por desconocida).

### 16.3 Topología final

| | Desarrollo | Piloto |
|---|---|---|
| Rama de Git | `clinical-encounter-v0.13` | `pilot-residents-v1` (sólo promociones; sin crear) |
| App de Streamlit | `clinical-management-reasoning-dev` (existe y no se toca) | `clinical-management-reasoning-pilot` (nueva; sin crear) |
| Archivo principal | `app.py` | `app.py` |
| Python | 3.12 | 3.11, elegido al crear la app |
| Proyecto de Neon | `management-reasoning-simulator` | `management-reasoning-simulator` |
| Rama de Neon | `clinical-encounter-v0.13`, archivada (según `docs/CLINICAL_DEV_DATABASE.md`) | `pilot-residents-v1` (sin crear; 16.10) |
| PostgreSQL | 17 | 17 |
| Uso | Sólo desarrollo. La Fase 1 seguirá aquí cuando se abra, con el piloto ya congelado | Sólo el piloto con residentes |

**Reglas:**
- `pilot-residents-v1` se promueve explícitamente desde un SHA conocido y aprobado (16.4).
- Ningún push ordinario de desarrollo puede actualizar la app del piloto, porque ésta no sigue
  `clinical-encounter-v0.13`.
- Una vez creada la app, la lista de apps de Streamlit debe mostrar que sólo `clinical-management-reasoning-pilot`
  sigue `pilot-residents-v1`.

### 16.4 Contrato de promoción

**`pilot-residents-v1` no es una rama de desarrollo.** Sólo recibe candidatos de despliegue aprobados explícitamente.
Nunca se despliega «lo último» ni un commit sin revisar. Este contrato reemplaza al de 15.8.

1. Cerrar las firmas docentes (B-5).
2. Crear el candidato final en `clinical-encounter-v0.13`, con el árbol limpio.
3. Correr la suite completa de pytest: 0 FAILED, con Python 3.11 y Streamlit 1.64.0.
4. Correr `run_regressions.py`: 56/56.
5. Correr B-1 en el proveedor sobre ese commit (16.8): 23/23.
6. Anotar el SHA aprobado exacto, de 40 caracteres.
7. Crear `pilot-residents-v1` en ese SHA, o avanzarla hasta él, con autorización:
   `git push origin <SHA>:refs/heads/pilot-residents-v1`. Sólo avance rápido; nunca force-push sin una decisión
   expresa.
8. Verificar que la rama contiene exactamente el candidato: `git ls-remote origin refs/heads/pilot-residents-v1`
   devuelve el SHA del paso 6.
9. Poner `MRS_CODE_VERSION = "<SHA>"` en los Secrets del piloto.
10. Correr el preflight contra la configuración del piloto (16.11):
    `python3 tools_pilot_preflight.py --secrets <archivo> --commit <SHA> --connect`. Debe dar «LISTA», sin FALLA y
    sin AVISO de `no_batch_settings`.
11. Desplegar la app nueva: repositorio, `pilot-residents-v1`, `app.py`, Python 3.11 en «Advanced settings» y los
    mismos Secrets.
12. Correr la prueba de humo desplegada (sección 11).
13. Verificar las fotos (TD-56): `check_database.py --photo-approvals` debe terminar en «All 117 approvals…».
14. GO explícito del docente responsable (condición C).

**En las promociones siguientes,** el push del paso 7 ya redespliega la app del piloto. Por eso los pasos 7 a 11 se
hacen en una sola ventana: primero la puerta de encuentros abiertos (16.12), y después `MRS_CODE_VERSION` nuevo y
«Reboot app».

### 16.5 Riesgo de autodespliegue

- **Confirmado:** `clinical-encounter-v0.13` → `clinical-management-reasoning-dev`. Un push redespliega desarrollo.
- **Los seis commits locales no se empujan sin tu autorización expresa.** Si se autoriza el push, conviene saber:
  - llevaría a la app de desarrollo el preflight, las regresiones y la fijación de Streamlit;
  - el cambio de `requirements.txt` provoca un redespliegue completo, según el proveedor;
  - antes conviene confirmar que nadie la está usando.
- **Crear `pilot-residents-v1` en GitHub no mueve `clinical-encounter-v0.13`,** así que no redespliega desarrollo.
- **Con el piloto creado:** `pilot-residents-v1` → sólo `clinical-management-reasoning-pilot`. Los commits de la Fase
  1 nunca se empujan a `pilot-residents-v1`.

### 16.6 Python: RESUELTO

- **Confirmado:**
  - Streamlit Community Cloud ofrece Python 3.11;
  - la app del piloto se creará con 3.11;
  - la de desarrollo sigue en 3.12 y no se cambia.
- **Hay que elegirla al crear la app:** según el proveedor, cambiar Python después obliga a borrar la app y volver a
  desplegarla.
- **Verificación:** la app no registra la versión de Python en el encuentro. Se comprueba en su configuración, y la
  captura queda en el registro del despliegue.

### 16.7 Topología de la base

| Elemento | Valor |
|---|---|
| Proveedor y proyecto | Neon, `management-reasoning-simulator` |
| PostgreSQL | 17 |
| Rama por omisión | `production`: producción. **Nunca** para pruebas ni para el piloto |
| Rama persistente del piloto | `pilot-residents-v1` (sin crear; 16.10) |
| Rama temporal de B-1 | `pilot-b1-validation` (sin crear; 16.9) |
| Base temporal de B-1 | `mrs_b1` |

**Reglas:**
- ni el piloto ni B-1 modifican `production`;
- B-1 es descartable y corre en el mismo proyecto, con PostgreSQL 17;
- la base del piloto queda aislada de desarrollo;
- ningún documento ni ninguna salida muestran credenciales.

**Lo que dice el proveedor** (documentación de Neon, consultada por búsqueda; no verificada en la cuenta):
- **Una rama normal hereda el esquema y todos los datos de su madre** en el momento de crearla. `production` es la
  rama por omisión y la única no archivada. **Por eso una rama normal creada desde `production` contendría una
  copia de los datos de producción.**
- **La opción «Schema only»** crea una rama con el esquema y sin filas. Es una rama raíz independiente, sin madre,
  dentro del mismo proyecto.
- **Todas las ramas de un proyecto comparten la versión de PostgreSQL.**
- **Crear una hija de una rama archivada la desarchiva,** junto con sus madres. Por eso las ramas archivadas de
  desarrollo no se usan como madre.

### 16.8 B-1: procedimiento exacto (preparado, no ejecutado)

**Dónde.** Desde un equipo con red directa a Neon (por ejemplo, tu Mac con una copia del repositorio). Desde este
entorno no es posible: su proxy sólo cursa HTTP(S), y las pruebas usan psycopg sobre TCP.

**Qué commit.** El código de persistencia probado tiene que ser el del candidato.
- Hoy, `009aadb` (que ya está en GitHub) y el HEAD local tienen idénticos todos los `.py`, salvo el preflight y dos
  scripts de regresión, e idénticos los activos (comprobado el 2026-10-07 con `git diff`).
- **Opción 1:** `009aadb` desde GitHub, más `pip install streamlit==1.64.0`, porque su `requirements.txt` admite
  1.65.0.
- **Opción 2:** el HEAD local exacto, mediante un `git bundle` y sin push, si lo pides.
- Se anota el SHA probado. En la promoción, el paso 5 vuelve a correr B-1 sobre el SHA final.

**Entorno.**
- Python 3.11, con `pip install -r requirements.txt`.
- Para J, `pg_dump` y `pg_restore` de la versión 17 o mayor: un `pg_dump` 16 no respalda un servidor 17.

**Credenciales.** La URL nunca va a un archivo del repositorio, al chat ni a un registro. Se pega sin eco:

```
read -rs MRS_TEST_POSTGRES_URL; export MRS_TEST_POSTGRES_URL   # URL pooled de mrs_b1; no se muestra
```

Se usa la URL *pooled*, la que usará la app. El pooler del proveedor es comportamiento propio de Neon, y la prueba
local no lo ejercitó. Si algo falla sólo con la URL pooled, se repite con la directa para aislar la causa, y se anotan
las dos.

**Paso 1 · Comprobar el destino.** Falla cerrado, imprime sólo lo de abajo y nunca la URL. Se probó en PostgreSQL 16
local: con el destino correcto dice `TARGET OK`; con otra base u otra versión, `STOP`; sin TLS, no conecta.

```
EXPECT_DB=mrs_b1 EXPECT_MAJOR=17 python3 - <<'PY'
import os, sys
from urllib.parse import urlsplit
import psycopg
url = os.environ.get("MRS_TEST_POSTGRES_URL", "")
part = urlsplit(url)
print("endpoint:", (part.hostname or "").split(".")[0], "| database in URL:", part.path.lstrip("/"),
      "| sslmode=require in URL:", "sslmode=require" in (part.query or ""))
try:
    with psycopg.connect(url, connect_timeout=10) as conn:
        db, version, num = conn.execute("select current_database(), current_setting('server_version'), "
                                        "current_setting('server_version_num')::int").fetchone()
        tables = conn.execute("select count(*) from information_schema.tables where table_schema = 'public'").fetchone()[0]
        tls = conn.pgconn.ssl_in_use
except Exception as error:
    print("connection failed:", type(error).__name__); sys.exit(1)
print("database:", db, "| server:", version, "| major:", num // 10000, "| tables in public:", tables, "| client TLS:", tls)
ok = db == os.environ["EXPECT_DB"] and num // 10000 == int(os.environ["EXPECT_MAJOR"]) and tls
print("TARGET OK" if ok else "TARGET WRONG: STOP"); sys.exit(0 if ok else 1)
PY
```

- La primera vez debe mostrar `TARGET OK`, `tables in public: 0` y `client TLS: True`.
- El campo `endpoint` se compara con el endpoint de `pilot-b1-validation` en la consola.
- Con `TARGET WRONG` o `connection failed`, se detiene todo.

**Paso 2 · Crear el esquema por el camino del repositorio.** `check_database.py` imprime el host y el nombre de la
base, nunca la contraseña.

```
MRS_DATABASE_URL="$MRS_TEST_POSTGRES_URL" python3 check_database.py            # «Connected.» y «This user may create tables.»
MRS_DATABASE_URL="$MRS_TEST_POSTGRES_URL" python3 check_database.py --create   # «The application's store opened; its tables are in place.»
```

**Paso 3 · Las pruebas.**

```
python3 -m pytest -p no:cacheprovider -rA --junitxml=b1_junit.xml \
  test_phase0_submission_guard_on_postgres.py test_store_integrity_on_postgres.py \
  test_the_image_bank_on_postgres.py test_p07_75f_arrives_with_the_neutral_view.py 2>&1 | tee b1_pytest.log
```

**Paso 4 · Comprobar el destino otra vez.** Repetir el paso 1: debe seguir siendo `mrs_b1`, versión 17 y con TLS. Esta
vez ya habrá tablas.

**Paso 5 · J, recomendado.** Se corre sobre una segunda base vacía de la misma rama, `mrs_b1_drill`, con su URL
**directa**: `pg_dump` y `CREATE DATABASE` son operaciones de sesión, y así el pooler no se mezcla con el respaldo.

```
read -rs B1_DRILL_URL; export B1_DRILL_URL
python3 tools_backup_drill.py --postgres "$B1_DRILL_URL" --out b1_drill.json
```

El simulacro crea `mrs_b1_drill_restored` en la misma rama, desde la base `postgres`. Si el rol no puede crear bases,
J queda NOT RUN, sin tocar nada fuera de la rama.

**Qué demuestra cada parte:**

| Ítem | Qué demuestra | Prueba |
|---|---|---|
| A | El envío queda escrito antes de ejecutarse | `test_a_the_order_is_in_the_database_before_it_runs`, `test_a_an_order_is_saved_before_it_runs_runs_once_and_is_saved_processed` |
| B | Un ID de envío se ejecuta una vez | `test_b_a_second_click_on_the_same_form_executes_nothing_more` |
| C | Una recarga después del write-ahead y antes de procesar reanuda una vez | `test_c_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume` |
| D | Una recarga después de procesar no ejecuta de nuevo | `test_d_a_reload_after_processing_re_executes_nothing` |
| E | Un proceso interrumpido se deshace y corre una vez; interrumpido dos veces, se dice y no corre | `test_e_a_run_stopped_part_way_is_undone_and_the_order_runs_once`, `test_e_a_run_stopped_twice_is_said_once_and_never_repeated` |
| F | Un conflicto de revisión no duplica ni pierde nada en silencio | `test_f_two_sessions_on_one_encounter_never_run_an_order_twice_nor_lose_one_silently` |
| G | F0-12: una orden escrita después de una respuesta | `test_an_order_written_after_an_answer_is_saved_with_it_and_runs_once` |
| H | El esquema en una base nueva y su compatibilidad | `check_database.py --create`; cada fixture recrea `public` y la app crea sus tablas; `test_every_unique_key_is_an_index_of_a_new_database`, `test_an_old_repeat_no_longer_locks_the_store`, `test_the_directive_and_its_encounter_are_one_transaction`, `test_account_changes_are_written_with_author_and_time`, `test_the_encounter_is_kept_in_postgresql`, las 4 del banco de imágenes y la importación de la 75f |
| I | La conexión del proveedor, con TLS | `sslmode=require`; paso 1 (`client TLS: True`, PostgreSQL 17); `check_database.py` («Connected.»); URL pooled; `test_a_driver_failure_is_logged_by_class_not_by_message` |
| J | Respaldo y restauración en PostgreSQL 17 | `tools_backup_drill.py`. Recomendado: el plan vigente (runbook §3, paso 0) sólo exige el envío |

**PASS de B-1:**
- el paso 1 dice `TARGET OK` antes (`mrs_b1`, 17, TLS, 0 tablas) y después;
- `check_database.py` dice «Connected.» y «This user may create tables.», y `--create` abre el store;
- pytest da **23 passed, 0 failed, 0 errors y 0 skipped** (10 + 5 + 4 + 4);
- la evidencia queda guardada y ningún registro contiene un secreto.

J se informa aparte: PASS, FAIL o NOT RUN.

**FAIL de B-1:**
- cualquier falla o error;
- **cualquier prueba de PostgreSQL omitida**: quiere decir que la URL no llegó, y la corrida no cuenta;
- `TARGET WRONG` o una conexión sin TLS;
- otra rama u otra base que las indicadas;
- un secreto en un registro. En ese caso, además, se rota la contraseña del rol.

**Cómo se demuestra que producción no se tocó:**
1. Por construcción: la rama de B-1 es «Schema only», así que no contiene ninguna fila de producción. Las pruebas
   sólo reciben la URL de `mrs_b1` en esa rama.
2. Durante B-1 nadie obtiene ni usa la URL de producción.
3. El paso 1, antes y después, deja anotados el endpoint y la base, cotejados con la consola.
4. Según el proveedor, las ramas están aisladas: lo que se escribe en una no cambia otra.
5. Opcional: si la consola muestra la actividad o el tamaño de `production`, se anotan antes y después.

**Evidencia que se guarda.** Va en una subsección nueva de este informe, sin URLs, contraseñas ni hosts completos:
- el SHA probado y que el árbol estaba limpio;
- las versiones de Python, psycopg y Streamlit;
- la salida del paso 1, antes y después, y la de `check_database.py`;
- el resumen de pytest y su `b1_junit.xml`;
- `b1_drill.json`, si J corrió;
- de Neon: proyecto, rama y su tipo («Schema only»), base, tipo de endpoint, versión y horas de creación y de borrado;
- quién la corrió y en qué ventana.

### 16.9 Creación del recurso de B-1 (preparada; no ejecutar sin autorización)

1. En la consola de Neon, en el proyecto `management-reasoning-simulator`, ir a Branches → New branch:
   - nombre `pilot-b1-validation`;
   - origen `production`, con la opción **«Schema only»**: copia el esquema, sin datos.
   - No usar las ramas archivadas como origen.
   - Si la consola no ofrece «Schema only», **no crear una rama con datos de producción**: detenerse y decidir
     (alternativas en 16.10).
2. En esa rama, crear la base `mrs_b1`, cuya dueña sea el rol con que correrán las pruebas: las pruebas borran y
   recrean el esquema `public`, y eso exige ser dueño de la base. Para J, también `mrs_b1_drill`, con la misma dueña.
3. En «Connect», copiar la URL *pooled* de `mrs_b1` y, para J, la directa de `mrs_b1_drill` a un gestor de
   contraseñas. Nunca al repositorio, al chat ni a archivos.
4. Crear el esquema por el camino del repositorio: 16.8, paso 2.
5. Correr B-1: 16.8, pasos 1 a 5.
6. Registrar el proveedor, la versión de PostgreSQL, la rama, la base, el SHA probado y los resultados (evidencia de
   16.8), sin credenciales.
7. **Con tu aprobación,** borrar la rama `pilot-b1-validation`; con ella se van `mrs_b1`, `mrs_b1_drill` y
   `mrs_b1_drill_restored`. Se anota la hora. El borrado no es automático.

### 16.10 Base persistente del piloto (para después; no crear sin autorización)

**Recomendación: C, inicialización independiente y vacía.**
- `pilot-residents-v1` se crea como rama «Schema only»: una raíz independiente, sin datos.
- Dentro, una base nueva y vacía, `mrs_pilot`, cuya dueña sea un rol propio de la app del piloto. La app usa sólo esa
  base.
- Una base nueva, y no la heredada, porque la rama «Schema only» trae las definiciones de tablas de producción; así la
  app empieza sin estructura heredada y crea la suya.

**La app no necesita datos sembrados.** Lo crea todo al abrirse (verificado en el código):
- sus tablas `mrs_*`, con `CREATE TABLE IF NOT EXISTS`;
- las metas del programa, que `ProgressStore` siembra desde `objectives.py`;
- el paquete de fotos, que se importa desde `assets/patient_images` al abrir la página (`image_pack.ensure_imported`);
- el primer administrador, desde los Secrets de bootstrap.

Lo demás son acciones docentes dentro de la app, después del despliegue (secciones 6 y 7): la aprobación del relato
en español, los descriptores de la rúbrica y las aprobaciones de fotos de TD-56.

**Actualización del 2026-10-07 (B-5, decisiones docentes):** el relato en español de los 30 casos y los
descriptores de la rúbrica en español se revisan antes de congelar el candidato final, que no se congela sin esas
revisiones; ya no quedan para después del despliegue. El relato aprobado entra en el candidato en
`case_text/es/approvals.json` (camino a; el archivo se crea después de la revisión docente), sin volver a
registrarlo a mano en la base del piloto. El mecanismo con que la rúbrica se activa en el candidato se identifica
antes de implementarla (Decision File, décima y undécima actualizaciones; TD-81).

**Por qué no las otras:**
- **A, rama desde `production`:** copiaría los datos de producción al piloto con residentes.
- **B, rama desde las de desarrollo o validación:** están archivadas (crear una hija las desarchiva) y traen datos de
  desarrollo.

**Si «Schema only» no está disponible,** no se crea una rama con datos de producción. Decides tú entre:
- (i) crear la rama desde `production` y, sólo en esa rama hija y con autorización expresa, borrar las bases heredadas
  antes de usarla;
- (ii) un proyecto de Neon aparte, con PostgreSQL 17. Esto se aparta de la decisión de usar el mismo proyecto.

**Cuándo:** antes del paso 10 del contrato, porque `--connect` la necesita, y con autorización.

**Conexión:** la URL *pooled* de `mrs_pilot`, con `sslmode=require`, en los Secrets del piloto.

**Respaldos:** antes de cada despliegue y a diario (`docs/RESPALDO_Y_RESTAURACION.md`), con `pg_dump` 17 sobre la URL
directa (TD-76).

### 16.11 Contrato de Secrets de la app del piloto (sólo nombres)

**Dónde:** `clinical-management-reasoning-pilot` → Settings → Secrets, o «Advanced settings» al crearla. **El gate es
el preflight corregido.**
- **Antes de crear la app:** se corre el preflight con el archivo local cuyo texto se va a pegar.
- **Después de crearla:** se copian los Secrets tal como quedaron en la app a un archivo temporal y se corre otra vez
  (`--commit <SHA> --connect`).
- El despliegue no se da por listo hasta que las dos corridas digan «LISTA».
- El archivo nunca se versiona y se borra al terminar.

| Setting | Estado exigido en el piloto | ¿Secreto? | Regla del preflight |
|---|---|---|---|
| `MRS_DATABASE_URL` | URL *pooled* de `mrs_pilot` (rama `pilot-residents-v1`), `sslmode=require` | **SÍ** | `database_url`; con `--connect`, `database_reachable` |
| `MRS_AUTH_MODE` | `"accounts"` | NO | `auth_mode` |
| `MRS_OFFLINE_CASES` | `"1"` | NO | `offline_cases` |
| `MRS_PAID_GENERATION` | `"off"` | NO | `paid_generation_off` |
| `MRS_FREE_GENERATION` | Ausente | NO | `free_generation_closed` |
| `MRS_DEFAULT_VARIANT` | Ausente | NO | `no_pinned_case` |
| `MRS_REPLAY_CASE` | Ausente | NO | `no_replay_case` |
| `MRS_CODE_VERSION` | `"<SHA aprobado>"` | NO | `code_version` |
| `MRS_IMAGE_REQUIRE_REVIEW` | `"on"` | NO | `image_review` |
| `MRS_ADMIN_USERNAME`, `MRS_ADMIN_PASSWORD_HASH` | Sólo para crear el primer administrador; después se retiran | El hash: **SÍ** | `admin_bootstrap` |
| `OPENAI_API_KEY` | Ausente | **SÍ** | `provider_key_withheld` |
| `MRS_ALLOW_LOCAL_SQLITE` | Ausente | NO | `no_local_sqlite` |
| `MRS_SYNTHETIC_ACCOUNTS`, `MRS_BATCH_*` | Ausentes | Contraseñas: **SÍ** | `no_batch_settings` (AVISO) |
| `MRS_PUBLIC_APP_URL` | La URL que Streamlit asigne a la app; se espera `https://clinical-management-reasoning-pilot.streamlit.app/` | NO | Ninguna (TD-75) |
| `MRS_IMAGE_BANK` | Ausente: el banco de fotos aprobadas queda activo | NO | Ninguna (TD-75) |
| `MRS_LANGUAGE` | Opcional (`es` o `en`); decisión docente | NO | Ninguna |
| `APP_PASSWORD`, `MRS_DEFAULT_CHALLENGE`, `MRS_ANALYSIS_CORRECTIONS`, `OPENAI_MODEL`, `MRS_*_MODEL`, `MRS_AI_*`, `MRS_IMAGE_BUDGET_*`, `MRS_DIAGNOSTIC_DIR` y `STREAMLIT_*` | Ausentes | `APP_PASSWORD`: **SÍ** | `fast_reruns` vigila `STREAMLIT_RUNNER_FAST_RERUNS`; el resto, ninguna |
| `.streamlit/config.toml` `[runner] fastReruns` | `false` en el SHA | NO | `fast_reruns` |

**Para las fotos no hace falta ningún secreto:** basta `MRS_IMAGE_REQUIRE_REVIEW = "on"` y `MRS_IMAGE_BANK` ausente.
Las fotos llegan en `assets/`.

### 16.12 Puerta de encuentros abiertos

**NO SE DESPLIEGA CON ENCUENTROS DEL PILOTO ABIERTOS.**
- La puerta del operador son las tres consultas de sólo lectura y el chequeo mínimo de 15.10.
- Se aplica antes de cada despliegue, promoción o «Reboot app» de la app del piloto.
- En el primer despliegue la base es nueva, así que la consulta 1 da 0.
- No se implementa ningún bloqueo en el runtime.

### 16.13 Aceptación de B-2

| Criterio | Estado |
|---|---|
| Proveedor: Streamlit Community Cloud | SÍ (16.2) |
| App nueva dedicada: `clinical-management-reasoning-pilot` | SÍ (decidida; se crea en el paso 11) |
| Repositorio: `management-reasoning-simulator` | SÍ |
| Estrategia de rama: `pilot-residents-v1`, sólo promociones | SÍ (16.3, 16.4) |
| Archivo principal: `app.py` | SÍ |
| Python 3.11 | SÍ (16.6) |
| Proveedor y proyecto de Neon | SÍ: `management-reasoning-simulator` |
| PostgreSQL 17 | SÍ |
| Estrategia de la rama de base del piloto | SÍ (16.10; con alternativa si «Schema only» no está disponible) |
| Prueba descartable de B-1 | SÍ (16.8, 16.9) |
| Lugar de los Secrets | SÍ (16.11) |
| Autodespliegue entendido | SÍ (16.5) |
| Procedimiento de encuentros abiertos | SÍ (16.12) |
| Contrato de promoción del SHA | SÍ (16.4) |

**B-2: RESUELTO.**

### 16.14 Estado al cerrar el encargo

- **B-1: READY TO EXECUTE / NOT YET EXECUTED** al cerrar esta sección. Después quedó BLOCKED: el intento desde este
  entorno no pudo llegar a Neon (sección 17). Siguiente acción, con tu autorización:
  1. crear en Neon `pilot-b1-validation` («Schema only») y la base vacía `mrs_b1` (16.9);
  2. desde un equipo con red directa, correr los pasos 1 a 5 de 16.8.
- **B-5: BLOCKED.** No se cambió ningún texto que espera firma. El SHA final se construye sólo después de cerrarlo.
- **NOT READY FOR DEPLOYMENT:** faltan B-1 y B-5.

## 17. B-1: intento de ejecución en el proveedor (2026-10-07) — BLOCKED

Encargo: correr B-1 contra un PostgreSQL 17 descartable de Neon, en el proyecto que alojará el piloto. Estaba
autorizado crear sólo la rama `pilot-b1-validation` («Schema only») y la base `mrs_b1`. **Resultado: B-1 BLOCKED,
clasificado como TEST ENVIRONMENT FAILURE.** Desde este entorno no se puede llegar a Neon, así que no se creó ni se
tocó ningún recurso del proveedor y no corrió ninguna prueba contra él.

### 17.1 Verificación inicial

| Comprobación | Resultado |
|---|---|
| Rama | `clinical-encounter-v0.13` |
| HEAD local | `8cc054ff2d91b43dcc1917db70a3945d507c9a5b` |
| `origin/clinical-encounter-v0.13` | `009aadb` (comprobado con `git ls-remote`) |
| Adelante / atrás | 7 / 0 |
| Árbol | Limpio |
| Commits después de `009aadb` | Los siete son de preparación para el despliegue |
| Fase 1 o núcleo común | Ninguno |
| Cambios del runtime | Ninguno después de `009aadb`: salvo el preflight y su prueba y dos scripts de regresión, todos los `.py` son idénticos (`git diff`), y también los activos |
| SHA que se iba a validar | `8cc054ff2d91b43dcc1917db70a3945d507c9a5b`. Su código de persistencia es el de `009aadb` |

D-B2-5 queda **confirmada**: la persona responsable vio que la consola de Neon ofrece «Branch schema only» para el
proyecto `management-reasoning-simulator`, y que ese modo copia sólo el esquema, sin datos.

### 17.2 Por qué no pudo correrse aquí

| Requisito | Comprobación en este entorno | Resultado |
|---|---|---|
| Crear la rama y la base en Neon | No hay conector de Neon en esta sesión. Existe en el directorio de conectores, pero no está instalado ni habilitado. No hay credencial ni token de Neon en el entorno (sólo se buscaron nombres de variables, nunca valores) | Imposible |
| Llegar a la API de Neon | `https://console.neon.tech/api/v2/...`: el proxy del entorno rechaza el túnel (CONNECT 403) | Bloqueado por la política de red |
| Conectar las pruebas a PostgreSQL | psycopg usa TCP al puerto 5432. Sin salida directa a 5432 ni a 22 (timeout); el 443 sí sale. El proxy sólo cursa HTTP(S) | Bloqueado |
| Obtener una URL de conexión | Sin acceso a la consola ni a la API | Imposible |

**Clasificación:** TEST ENVIRONMENT FAILURE. No es un defecto del código, ni una mala configuración del proveedor, ni
un problema del esquema, de red o de TLS del proveedor, ni una falla de aislamiento de datos: la prueba no llegó a
empezar.

### 17.3 Qué no se hizo y qué no cambió

| Ítem | Estado |
|---|---|
| Rama `pilot-b1-validation` y base `mrs_b1` | **No creadas** |
| Ramas `production`, `development-validation` y `clinical-encounter-v0.13` | **No tocadas**: no hubo ninguna conexión al proveedor |
| Datos de producción copiados | **No**: no se creó nada |
| A–G | **NOT RUN** |
| Versión 17, TLS, esquema y transacciones en el proveedor | **NOT RUN** |
| J (respaldo y restauración) | **NOT RUN**. Para B-1 no es obligatorio: el plan vigente (runbook §3, paso 0) exige el envío; J está recomendado (16.8) y abre TD-76 |
| Limpieza | Nada que limpiar |
| Código, runtime, rama de Git del piloto, app de Streamlit y rama persistente de Neon | Sin cambios; nada creado |

### 17.4 Siguiente acción exacta

**Recomendado: correr B-1 desde tu Mac**, con red directa a Neon, siguiendo 16.9 y 16.8 tal como están:

1. En la consola de Neon (proyecto `management-reasoning-simulator`), crear la rama `pilot-b1-validation` desde
   `production` con «Branch schema only». Se acepta que se borre sola al día; en ese caso B-1 y su registro tienen que
   hacerse dentro de ese día.
2. En esa rama, crear la base `mrs_b1`. Su dueña tiene que ser el rol con que correrán las pruebas, porque éstas
   recrean el esquema `public`.
3. Copiar la URL *pooled* de `mrs_b1` a un gestor de contraseñas, y pegarla en la terminal sin eco
   (`read -rs MRS_TEST_POSTGRES_URL`).
4. **Elegir qué commit probar.** Los siete commits locales no están en GitHub, y no se empujan sin autorización:
   - `009aadb`, desde GitHub, con `pip install streamlit==1.64.0`. Tiene el mismo código de persistencia que
     `8cc054f`;
   - o `8cc054f` exacto, mediante un `git bundle` que puedo preparar sin push.
5. Correr los pasos 1 a 5 de 16.8: comprobación del destino, `check_database.py` y `--create`, las cuatro pruebas de
   PostgreSQL, la comprobación final y, si se puede, J.
6. Traer los resultados, sin URLs ni contraseñas:
   - la salida de la comprobación del destino, antes y después;
   - la salida de `check_database.py`;
   - el resumen de pytest y `b1_junit.xml`;
   - `b1_drill.json`, si J corrió;
   - el SHA probado.

   Con eso se registra B-1 en este informe, y queda RESUELTO sólo si se cumplen los 17 criterios del encargo.

**Alternativa, sin verificar:** dar a una sesión de este entorno un conector de Neon o un token guardado como variable
del entorno, y una red que permita `console.neon.tech` y conexiones directas a 5432. Hoy el contenedor no tiene salida
TCP fuera del 443, y no se sabe si la configuración de red lo permite. Por eso se recomienda el Mac.

## 18. B-1 listo para correr desde el Mac (2026-10-07)

Encargo: completar B-1 hasta donde lo permite este entorno. **B-1: READY TO EXECUTE.** Faltan la corrida en el Mac y su
evidencia; no se declara resuelto antes. Esta sección reemplaza, para B-1, el procedimiento de 16.8.

### 18.1 La rama de Neon

**Creada a mano y confirmada en la consola por la persona responsable:**
- proyecto `management-reasoning-simulator`, con PostgreSQL 17;
- rama `pilot-b1-validation`, con madre `production` y en modo «Branch schema only»;
- sin datos de producción;
- borrado automático al día. **La corrida tiene que hacerse antes de que venza**; si vence, se vuelve a crear igual.

**Desde este entorno no se pudo verificar.** Se volvió a comprobar hoy:
- no hay conector de Neon;
- el proxy rechaza `console.neon.tech` («CONNECT tunnel failed, response 403»);
- no hay salida TCP a 5432.

Por eso la rama se verifica desde el Mac, con la comprobación del destino (18.6, pasos 4 a 7). Desde aquí no se creó,
cambió ni borró nada en Neon.

### 18.2 SHA candidato

| | SHA | Qué es |
|---|---|---|
| A · Último commit de runtime y dependencias | `e200cccc6487af807cab419595baed5b15dd6179` | El último que cambia algo fuera de `docs/`. Trae el preflight (`87bbbe1`), `streamlit==1.64.0` (`4d570a8`) y las regresiones (`e200ccc`). El código de la app es el de `009aadb` |
| B · HEAD de documentación | El commit de esta actualización | Después de A sólo hay documentación |
| C · Candidato de B-1 | `e200cccc6487af807cab419595baed5b15dd6179` | Es lo que se desplegaría, salvo `docs/`: `git diff e200ccc HEAD -- . ':(exclude)docs'` está vacío |

- **A es lo que corre; B es lo que lo documenta.** B-1 se registra contra A.
- No se usa `009aadb`, aunque esté en GitHub: no trae la fijación de Streamlit, el preflight ni las regresiones.
- **GitHub sigue en `009aadb`** (comprobado con `git ls-remote`). Por eso el candidato viaja en un `git bundle`, sin
  push. Esto reemplaza las dos opciones de 16.8 («Qué commit»).
- En la promoción, el paso 5 del contrato (16.4) vuelve a correr B-1 sobre el SHA final.

### 18.3 Base de B-1: una nueva y vacía, `mrs_b1`

Lo decide lo que exige el repositorio, no una suposición:
- **Las pruebas exigen una base desechable:** borran y recrean el esquema `public`, y para eso el rol tiene que ser
  dueño de la base.
- **El respaldo exige otra base vacía, `mrs_b1_drill`:** el simulacro llena la base que recibe y crea
  `<base>_restored` a su lado.
- **El piloto usará una base nueva, creada por la app** (16.10). B-1 tiene que repetir ese arranque. La base que la
  rama copió trae las definiciones de tablas de producción, sin filas: arrancar ahí probaría una migración que el
  piloto no hará.

**Cómo crearla, en la consola de Neon:**
1. En la rama `pilot-b1-validation`, ir a las bases de datos y elegir «New database».
2. Nombre: `mrs_b1`.
3. Dueño: el rol que la consola ofrece en «Connect» para esa rama, el mismo con que vas a conectarte. La comprobación
   del destino exige `role owns database: True`.
4. Para el respaldo opcional, crear también `mrs_b1_drill`, con el mismo dueño.

No hace falta enviar ninguna contraseña.

### 18.4 Qué se copia de la consola

- **ID del cómputo de la rama:**
  - está en la página de `pilot-b1-validation` y empieza con `ep-`;
  - se escribe sin `-pooler`;
  - no es secreto;
  - la comprobación del destino lo exige: una URL de otra rama, producción incluida, no pasa.
- **URL de `mrs_b1`:**
  - en «Connect», elegir la rama `pilot-b1-validation`, la base `mrs_b1` y el rol dueño;
  - con **Connection pooling activado**: es la URL *pooled*, la que usará la app (16.11);
  - se copia la cadena que empieza con `postgresql://`, no el comando `psql`.
- **URL de `mrs_b1_drill`, opcional:** igual, pero con el pooling **desactivado** (la directa).
- **Dónde se pega:** cada URL va **sólo** en la terminal, cuando `read -rs` la pide; así no queda a la vista ni en el
  historial. Nunca al chat, a un archivo ni a la documentación.

### 18.5 Dos resguardos que 16.8 no tenía

**HOME vacío para cada comando de Python.** Es un hallazgo de esta preparación:
- el fixture de las pruebas de la Fase 0 sobre PostgreSQL le pasa la base a la app por una variable de entorno, y no
  fija `at.secrets`;
- sin `at.secrets`, Streamlit lee `~/.streamlit/secrets.toml`, y `account_portal._setting` prefiere ese archivo a la
  variable;
- si el Mac tiene ese archivo con `MRS_DATABASE_URL`, la app bajo prueba trabajaría sobre esa base y no sobre `mrs_b1`.

**Se comprobó con una base señuelo (18.10):**
- **Sin el `HOME` vacío**, `test_the_encounter_is_kept_in_postgresql` creó 7 tablas de cuentas (`mrs_users`,
  `mrs_sessions` y otras) en la base que nombraba `~/.streamlit/secrets.toml`. Después falló al preparar el encuentro.
- **Con el `HOME` vacío**, la base señuelo quedó con 0 tablas, y las 23 pruebas pasaron sobre `mrs_b1`.

Si ese archivo nombrara producción o desarrollo, la prueba habría escrito ahí.

Por eso el procedimiento corre cada comando de Python con `HOME` apuntando a una carpeta vacía. No se tocó el código.
Queda como propuesta, sin hacer: que `conftest.py` aísle `HOME`, o que el fixture fije `at.secrets`.

**El destino se comprueba antes de cada conexión y de cada escritura:**
- los dos ayudantes leen el ID del cómputo en la URL **antes de conectarse**. Si no es el de `pilot-b1-validation`,
  se detienen sin contactar el servidor, así que nunca se contacta otra rama, producción incluida;
- después de conectarse, `b1_target_check.py` exige además:
  - la base esperada;
  - PostgreSQL 17;
  - TLS;
  - que el rol sea dueño de la base;
- antes del arranque y para el respaldo, exige también que la base esté vacía;
- los pasos que escriben (5, 6 y 7) sólo corren si la comprobación pasa;
- en el paso 7 esto importa más: `tools_backup_drill.py` no verifica que su base esté vacía, sino que llena la que
  recibe.

### 18.6 Procedimiento en el Mac (zsh)

**Antes de empezar**, descargar del chat a `~/Downloads`:
- el paquete `mrs-b1-candidate.bundle`;
- `b1_target_check.py`;
- `b1_copy_rows_check.py`.

Los dos ayudantes imprimen sólo nombres de base y de rol, conteos, la versión, TLS y el ID del cómputo. Nunca la URL,
la contraseña ni el host completo. Su texto está en 18.10.

**Dónde se corre:**
- en el clon que ya tienes; `RUTA` es la carpeta que lo contiene, y el candidato queda al lado, en
  `RUTA/mrs-b1-e200ccc`;
- **todo en la misma ventana de terminal.** Si se cierra, las variables se pierden y los pasos siguientes se detienen
  solos. Para retomar:
  1. `cd` a `RUTA/mrs-b1-e200ccc`;
  2. repetir los pasos 2 y 3;
  3. seguir desde el paso donde quedó.

```
# 0 · Tu clon en el Mac. Si no tienes uno: git clone https://github.com/<cuenta>/management-reasoning-simulator.git
cd ~/RUTA/management-reasoning-simulator
git fetch origin                                     # trae 009aadb, la base del paquete

# 1 · El candidato exacto, aparte: sin push y sin tocar tu rama
git bundle verify ~/Downloads/mrs-b1-candidate.bundle
git fetch ~/Downloads/mrs-b1-candidate.bundle clinical-encounter-v0.13:refs/b1/bundle
git worktree add --detach ../mrs-b1-e200ccc e200cccc6487af807cab419595baed5b15dd6179
cd ../mrs-b1-e200ccc
git rev-parse HEAD                                   # debe decir e200cccc6487af807cab419595baed5b15dd6179
git status --porcelain                               # no debe imprimir nada

# 2 · Python 3.11 aparte (si falta: brew install python@3.11)
python3.11 -m venv ~/mrs-b1-venv && source ~/mrs-b1-venv/bin/activate
pip install -r requirements.txt "pytest==9.1.1"
B1_TOOLS=~/mrs-b1-tools B1_EV=~/mrs-b1-evidence B1_HOME=$(mktemp -d)   # B1_HOME: un HOME vacío para cada corrida
mkdir -p "$B1_TOOLS" "$B1_EV" && cp ~/Downloads/b1_target_check.py ~/Downloads/b1_copy_rows_check.py "$B1_TOOLS"/
python -c "import sys, streamlit, psycopg; print(sys.version.split()[0], streamlit.__version__, psycopg.__version__)" | tee "$B1_EV/b1_versions.txt"

# 3 · Sesión limpia y datos del destino. Nunca se define MRS_ALLOW_NETWORK_TESTS
for v in $(env | cut -d= -f1 | grep -E '^(MRS_|OPENAI_|STREAMLIT_|PG)'); do unset "$v"; done
printf "ID del computo de pilot-b1-validation (ep-..., sin -pooler): "; read -r EXPECT_ENDPOINT
printf "URL pooled de mrs_b1 (no se muestra): "; read -rs MRS_TEST_POSTGRES_URL; echo
export EXPECT_ENDPOINT MRS_TEST_POSTGRES_URL EXPECT_DB=mrs_b1 EXPECT_MAJOR=17 PYTHONDONTWRITEBYTECODE=1

# 4 · Destino, antes: tiene que decir TARGET OK; si no, parar aquí
HOME="$B1_HOME" EXPECT_EMPTY=1 python "$B1_TOOLS/b1_target_check.py" | tee "$B1_EV/b1_target_before.txt"

# 5 · Esquema con la herramienta del repositorio; el host queda tapado
if HOME="$B1_HOME" python "$B1_TOOLS/b1_target_check.py" > /dev/null; then
  HOME="$B1_HOME" MRS_DATABASE_URL="$MRS_TEST_POSTGRES_URL" python check_database.py | sed -E 's/host [^ ]+/host <host>/' | tee "$B1_EV/b1_check_database.txt"
  HOME="$B1_HOME" MRS_DATABASE_URL="$MRS_TEST_POSTGRES_URL" python check_database.py --create | sed -E 's/host [^ ]+/host <host>/' | tee -a "$B1_EV/b1_check_database.txt"
  HOME="$B1_HOME" python "$B1_TOOLS/b1_target_check.py" | tee "$B1_EV/b1_target_bootstrap.txt"
else echo "STOP: destino incorrecto"; fi

# 6 · Las 23 pruebas del proveedor
if HOME="$B1_HOME" python "$B1_TOOLS/b1_target_check.py" > /dev/null; then
  HOME="$B1_HOME" python -m pytest -p no:cacheprovider -rA --junitxml="$B1_EV/b1_junit.xml" \
    test_phase0_submission_guard_on_postgres.py test_store_integrity_on_postgres.py \
    test_the_image_bank_on_postgres.py test_p07_75f_arrives_with_the_neutral_view.py > "$B1_EV/b1_pytest.log" 2>&1
  tail -1 "$B1_EV/b1_pytest.log"
  grep -E "^(PASSED|FAILED|ERROR|SKIPPED) test_" "$B1_EV/b1_pytest.log" > "$B1_EV/b1_results.txt"; wc -l < "$B1_EV/b1_results.txt"
  HOME="$B1_HOME" python "$B1_TOOLS/b1_target_check.py" | tee "$B1_EV/b1_target_after.txt"
else echo "STOP: destino incorrecto"; fi

# 7 · Opcional (TD-76): respaldo y restauración en PostgreSQL 17, sobre mrs_b1_drill vacía
brew install postgresql@17                           # sólo se usan pg_dump y pg_restore
export PATH="$(brew --prefix postgresql@17)/bin:$PATH"; pg_dump --version | tee "$B1_EV/b1_pg_dump_version.txt"
printf "URL DIRECTA (sin pooling) de mrs_b1_drill (no se muestra): "; read -rs B1_DRILL_URL; echo
HOME="$B1_HOME" MRS_TEST_POSTGRES_URL="$B1_DRILL_URL" EXPECT_DB=mrs_b1_drill EXPECT_EMPTY=1 python "$B1_TOOLS/b1_target_check.py" > "$B1_EV/b1_target_drill.txt"; B1_DRILL_OK=$?; cat "$B1_EV/b1_target_drill.txt"
if [ "$B1_DRILL_OK" = 0 ]; then
  HOME="$B1_HOME" python tools_backup_drill.py --postgres "$B1_DRILL_URL" --out "$B1_EV/b1_drill.json" > /dev/null 2>&1; echo "drill exit: $?"
else echo "STOP: destino del respaldo incorrecto"; fi

# 8 · Opcional: una base que la rama copió de producción no trae filas (sólo lee; repetir por cada base que no sea mrs_b1*)
printf "URL de una base que la rama ya traía (no se muestra): "; read -rs B1_COPY_URL; echo
HOME="$B1_HOME" B1_COPY_URL="$B1_COPY_URL" python "$B1_TOOLS/b1_copy_rows_check.py" | tee -a "$B1_EV/b1_copy_rows.txt"

# 9 · Evidencia sin secretos y cierre de la sesión
git rev-parse HEAD | tee "$B1_EV/b1_sha.txt"
grep -cE "postgresql://|neon\.tech" "$B1_EV"/*       # todas las cuentas deben ser 0
unset MRS_TEST_POSTGRES_URL B1_DRILL_URL B1_COPY_URL; deactivate; rm -rf "$B1_HOME"
```

**Al terminar, cuando lo decidas:**
- en tu clon, `git worktree remove ../mrs-b1-e200ccc` y `git update-ref -d refs/b1/bundle`;
- la rama de Neon se borra sola al día, o antes con tu autorización.

### 18.7 Qué cubre cada parte

Las letras H–K siguen este encargo. En 16.8, la J era el respaldo; aquí va como opcional, y TD-76 sigue refiriéndose a
él.

| Ítem | Prueba o paso |
|---|---|
| A · Write-ahead | `test_a_the_order_is_in_the_database_before_it_runs`, `test_a_an_order_is_saved_before_it_runs_runs_once_and_is_saved_processed` |
| B · Un ID de envío corre a lo sumo una vez | `test_b_a_second_click_on_the_same_form_executes_nothing_more` |
| C · Reanudar antes de procesar: una vez | `test_c_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume` |
| D · Recargar después de procesar: nada se repite | `test_d_a_reload_after_processing_re_executes_nothing` |
| E · Proceso interrumpido | `test_e_a_run_stopped_part_way_is_undone_and_the_order_runs_once`, `test_e_a_run_stopped_twice_is_said_once_and_never_repeated` |
| F · Conflicto de revisión | `test_f_two_sessions_on_one_encounter_never_run_an_order_twice_nor_lose_one_silently` |
| G · F0-12 | `test_an_order_written_after_an_answer_is_saved_with_it_and_runs_once` |
| H · Esquema y arranque | Paso 5 (`check_database.py` y `--create`); `test_every_unique_key_is_an_index_of_a_new_database`, `test_the_encounter_is_kept_in_postgresql`, las 4 del banco de imágenes y la importación de la 75f. Cada fixture recrea el esquema |
| I · PostgreSQL 17 | Pasos 4 a 6: `major: 17` |
| J · TLS y proveedor | `sslmode=require` en la URL y `client TLS: True`; «Connected.»; URL pooled; `test_a_driver_failure_is_logged_by_class_not_by_message` |
| K · Transacciones y revisiones | F; `test_the_directive_and_its_encounter_are_one_transaction`; `test_an_old_repeat_no_longer_locks_the_store`; `test_concurrent_reservations_on_postgres_never_pass_the_limit`; la reversión de E |
| Opcional · Respaldo en PostgreSQL 17 (TD-76) | Paso 7 |
| Opcional · Aislamiento | Paso 8: 0 filas en las bases copiadas |

### 18.8 PASS y FAIL

**PASS de B-1, todo junto:**
- **Destino:** `TARGET OK` en los pasos 4, 5 y 6, con:
  - `database: mrs_b1`;
  - `matches EXPECT_ENDPOINT: True`;
  - `role owns database: True`;
  - `major: 17`;
  - `client TLS: True`;
  - en el paso 4, además, `tables in public: 0`.
- **Arranque:** el paso 5 dice «Connected.», «This user may create tables.» y «The application's store opened; its
  tables are in place.».
- **Pruebas:**
  - la última línea de pytest dice `23 passed`, sin `failed`, `error`, `skipped` ni `xfailed`;
  - `b1_results.txt` tiene 23 líneas, todas `PASSED`;
  - cubren A–G y H–K (18.7).
- **Producción sin tocar:** el ID del cómputo es el de `pilot-b1-validation`, no el de `production`. El resto de la
  prueba está en 16.8.
- **Sin secretos:** todas las cuentas del `grep -c` del paso 9 dan 0.
- **SHA:** `e200cccc6487af807cab419595baed5b15dd6179`.

**Dos líneas `ERROR` esperadas.** En el registro aparecen dos fallas que las pruebas provocan a propósito:
- «Uncaught app execution», de `test_a_the_order_is_in_the_database_before_it_runs`;
- «Account store transaction failed: UndefinedTable», de `test_a_driver_failure_is_logged_by_class_not_by_message`.

No empiezan con `ERROR test_`, así que no entran en `b1_results.txt`.

**FAIL de B-1:**
- cualquier `failed` o `error`;
- cualquier `skipped`: quiere decir que la URL no llegó, y la corrida no cuenta;
- `TARGET WRONG`, `connection failed` o «STOP»;
- otro SHA;
- un secreto en la evidencia. En ese caso, además, se rota la contraseña del rol en la consola.

**Si algo falla, no se reintenta a ciegas:** se trae la evidencia y se analiza. La latencia entre el Mac y Neon no es
la de la app desplegada, y puede hacer que una prueba tarde más que en el ensayo.

**Los opcionales se informan aparte, como PASS, FAIL o NOT RUN:**
- respaldo: `drill exit: 0` y `"passed": true` en `b1_drill.json`;
- aislamiento: `NO ROWS COPIED` en cada base copiada.

### 18.9 Evidencia que hay que traer

Nada de esto contiene URLs, contraseñas, tokens ni hosts completos:

| Qué | De dónde |
|---|---|
| SHA probado y árbol limpio | `b1_sha.txt`, y la salida vacía de `git status --porcelain` del paso 1 |
| Versiones de Python, Streamlit y psycopg | `b1_versions.txt` |
| Destino antes, después del arranque y después de las pruebas | `b1_target_before.txt`, `b1_target_bootstrap.txt` y `b1_target_after.txt` |
| Arranque | `b1_check_database.txt` |
| Pruebas | La última línea de `b1_pytest.log` y `b1_results.txt` |
| Revisión de secretos | La salida del `grep -c` del paso 9 |
| Opcional · Respaldo | `b1_pg_dump_version.txt`, `b1_target_drill.txt`, la línea `drill exit` y `b1_drill.json` |
| Opcional · Aislamiento | `b1_copy_rows.txt` |
| De la consola de Neon | Proyecto, rama y madre, modo «schema only», versión, tipo de endpoint (pooled), y horas de creación y de borrado automático. Si el ID del cómputo es el de `pilot-b1-validation`: sí o no |
| Quién y cuándo | Quién la corrió y en qué ventana horaria |

`b1_pytest.log` y `b1_junit.xml` quedan en el Mac, porque incluyen rutas locales y el nombre del equipo. Se traen sólo
si se piden.

### 18.10 Ensayo hecho aquí y ayudantes

**El bloque de 18.6 se corrió aquí tal cual, de punta a punta.** Se hizo en bash, en un entorno limpio, sobre el
PostgreSQL 16 local descartable con TLS. Sólo cambiaron cinco cosas:
- las URL, leídas de archivos en vez de `read -rs`;
- `EXPECT_ENDPOINT=127`, el primer tramo de `127.0.0.1`;
- `EXPECT_MAJOR=16`;
- `pg_dump` 16 en lugar de `brew`;
- un `HOME` simulado del Mac.

**Montaje del ensayo:**
- un clon que sólo tenía `009aadb`, traído de GitHub;
- el paquete armado igual que el definitivo, desde el HEAD de entonces;
- un rol **sin superusuario**, con `CREATEDB` y contraseña SCRAM, y `channel_binding=require`, como en Neon;
- un `~/.streamlit/secrets.toml` señuelo, que apunta a la base `b1_decoy`;
- `MRS_DATABASE_URL`, `OPENAI_API_KEY` y `PGPASSWORD` definidos de antemano, para comprobar que el paso 3 los borra.

| Paso | Resultado |
|---|---|
| 1 · Paquete y copia aparte | `is okay`, requiere `009aadb`; la copia queda en `e200ccc`; `git status --porcelain` vacío |
| 2 · venv nuevo desde `requirements.txt` | `3.11.15 1.64.0 3.3.6` |
| 4 · Destino antes | `TARGET OK`: `tables in public: 0`, `role owns database: True`, `client TLS: True` |
| 5 · Arranque | «Connected.», «This user may create tables.» y «The application's store opened…»; 7 tablas |
| 6 · Pruebas | **`23 passed in 217.04s (0:03:37)`**; `b1_results.txt` con 23 `PASSED`; después, 16 tablas y `TARGET OK` |
| 7 · Respaldo (opcional) | `TARGET OK` sobre `mrs_b1_drill` vacía; `drill exit: 0`; `"passed": true`, con 33 tablas y 690 filas, ninguna tabla distinta y encuentros y cambios de cuentas idénticos |
| 8 · Aislamiento (opcional) | `NO ROWS COPIED` en una base con 2 tablas vacías, como las que copia «schema only» |
| 9 · SHA y secretos | `e200cccc6487af807cab419595baed5b15dd6179`. Cero apariciones de la URL, `neon.tech`, la contraseña, `usuario:` o el host, en la evidencia, en la transcripción de la terminal y en el control |
| Resguardos | El paso 3 borró las variables puestas de antemano. La base señuelo quedó con 0 tablas. Sin `HOME` vacío, la misma prueba creó 7 (18.5). Con otro ID de cómputo, los dos ayudantes se detienen sin conectarse (`STOP (not connected)`) |

**Lo que el ensayo no cubre**, y queda para el Mac:
- PostgreSQL 17;
- el pooler de Neon (la URL *pooled*);
- la latencia real;
- zsh: el bloque se revisó para que valga igual en bash y en zsh, pero aquí corrió en bash.

**Además:**
- se volvió a comprobar que el guardia de red de `conftest.py` bloquea los sockets de Python (`BlockedNetworkCall`), pero
  no las conexiones de psycopg (libpq). Por eso las pruebas llegan al servidor remoto sin `MRS_ALLOW_NETWORK_TESTS`,
  que debe seguir sin definirse;
- todo lo del ensayo se borró: las bases, el rol, su línea en `pg_hba.conf`, el clon simulado y la contraseña
  descartable.

**`b1_target_check.py`**

```python
"""B-1: is MRS_TEST_POSTGRES_URL the disposable target? Prints no URL, password or full host; exit 0 only if so."""
import os
import sys
from urllib.parse import urlsplit

import psycopg

url = os.environ.get("MRS_TEST_POSTGRES_URL", "")
expect_db = os.environ.get("EXPECT_DB", "mrs_b1")
expect_major = int(os.environ.get("EXPECT_MAJOR", "17"))
expect_endpoint = os.environ.get("EXPECT_ENDPOINT", "")
expect_empty = os.environ.get("EXPECT_EMPTY") == "1"
part = urlsplit(url)
endpoint = (part.hostname or "?").split(".")[0]
endpoint_ok = bool(expect_endpoint) and endpoint.removesuffix("-pooler") == expect_endpoint
tls_in_url = "sslmode=require" in (part.query or "")
print("endpoint:", endpoint, "| matches EXPECT_ENDPOINT:", endpoint_ok, "| database in URL:",
      part.path.lstrip("/") or "?", "| sslmode=require in URL:", tls_in_url)
if not (endpoint_ok and tls_in_url and part.path.lstrip("/") == expect_db):
    print("TARGET WRONG: STOP (not connected)")  # another branch, production included, is never contacted
    sys.exit(1)
try:
    with psycopg.connect(url, connect_timeout=15) as conn:
        db, role, version, num = conn.execute(
            "select current_database(), current_user, current_setting('server_version'), "
            "current_setting('server_version_num')::int").fetchone()
        owner = conn.execute("select pg_get_userbyid(datdba) = current_user from pg_database "
                             "where datname = current_database()").fetchone()[0]
        tables = conn.execute("select count(*) from information_schema.tables "
                              "where table_schema = 'public'").fetchone()[0]
        tls = conn.pgconn.ssl_in_use
except Exception as error:  # the driver's message can carry the host: name only its class
    print("connection failed:", type(error).__name__)
    sys.exit(1)
print("database:", db, "| role:", role, "| role owns database:", owner, "| server:", version,
      "| major:", num // 10000, "| tables in public:", tables, "| client TLS:", tls)
ok = db == expect_db and num // 10000 == expect_major and tls and owner and (tables == 0 or not expect_empty)
print("TARGET OK" if ok else "TARGET WRONG: STOP")
sys.exit(0 if ok else 1)
```

**`b1_copy_rows_check.py`**

```python
"""B-1, optional: rows in a database the schema-only branch copied. Reads only; prints counts, never content."""
import os
import sys
from urllib.parse import urlsplit

import psycopg

url = os.environ.get("B1_COPY_URL", "")
expect_endpoint = os.environ.get("EXPECT_ENDPOINT", "")
endpoint = (urlsplit(url).hostname or "?").split(".")[0]
endpoint_ok = bool(expect_endpoint) and endpoint.removesuffix("-pooler") == expect_endpoint
print("endpoint:", endpoint, "| matches EXPECT_ENDPOINT:", endpoint_ok)
if not endpoint_ok:  # another branch, production included, is never contacted
    print("WRONG BRANCH: STOP (not connected)")
    sys.exit(1)
try:
    with psycopg.connect(url, connect_timeout=15) as conn:
        conn.execute("set transaction read only")
        db = conn.execute("select current_database()").fetchone()[0]
        tables = [row[0] for row in conn.execute(
            "select format('%I.%I', schemaname, relname) from pg_stat_user_tables").fetchall()]
        total = sum(conn.execute(f"select count(*) from {name}").fetchone()[0] for name in tables)
except Exception as error:  # the driver's message can carry the host: name only its class
    print("connection failed:", type(error).__name__)
    sys.exit(1)
print("database:", db, "| user tables:", len(tables), "| total rows:", total)
print("NO ROWS COPIED" if total == 0 else "ROWS PRESENT: STOP")
sys.exit(0 if total == 0 else 1)
```

### 18.11 Estado

- **B-1: READY TO EXECUTE.** Se marca RESUELTO sólo si la evidencia cumple 18.8.
- **B-5: BLOCKED.**
- Sigue **NOT READY FOR DEPLOYMENT**.

## 19. B-1: resultado de la corrida en el proveedor (2026-10-07) — STILL BLOCKED

Encargo: interpretar la corrida que la persona responsable hizo desde su Mac, sin cambiar código. **B-1: STILL
BLOCKED.** No se tocaron el runtime ni las pruebas. El cambio de 19.4 es sólo una propuesta.

### 19.1 Evidencia del proveedor, tal como se informó

**Entorno:**
- proyecto `management-reasoning-simulator`;
- rama `pilot-b1-validation`, en modo «schema only»;
- base `mrs_b1`;
- PostgreSQL 17.11, con TLS;
- el endpoint coincide con el cómputo de la rama, y el rol es dueño de la base;
- candidato `e200cccc6487af807cab419595baed5b15dd6179`;
- Python 3.11.9, Streamlit 1.64.0 y psycopg 3.3.6;
- `HOME` vacío.

**Destino y arranque:**
- antes: `TARGET OK`, con 0 tablas;
- arranque: «Connected.», el usuario puede crear tablas, y `--create` abrió el store;
- después del arranque: 7 tablas y `TARGET OK`;
- al final de todo: `TARGET OK`.

**Corrida conjunta de las cuatro pruebas: 21 passed, 2 errors, 0 skipped y 0 failed, en 2141.98 s (35:41).**
- Los dos errores fueron:
  - `test_c_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume`;
  - `test_e_a_run_stopped_twice_is_said_once_and_never_repeated`.
- Los dos ocurrieron en la preparación común (`gi_bleed`), en
  `next(b for b in at.button if b.label == "Begin Encounter").click().run()`, con «AppTest script run timed out
  after 180(s)».
- El cuerpo de esas dos pruebas no llegó a correr.

**Reejecuciones de diagnóstico, una prueba por vez:**
- C: `1 passed` en 186.44 s;
- E: `1 passed` en 185.16 s.

**Conexión:** el informe dice «direct». 16.8 y 18.4 piden la URL *pooled*, la que usará la app. Lo dice la línea
`endpoint:` de `b1_target_before.txt`: termina en `-pooler` sólo si la URL era la *pooled*.

### 19.2 Diagnóstico, hecho aquí sin tocar el repositorio

**El límite de 180 s es por ejecución del script, no por prueba.** AppTest corta cada `.run()` que supere
`default_timeout` (`streamlit/testing/v1/local_script_runner.py`). Por eso, que una prueba completa tarde 185–186 s
no muestra por sí solo que una ejecución haya pasado de 180 s.

**Medición local.** Se usó el PostgreSQL 16 descartable, el mismo SHA y un plugin de diagnóstico fuera del
repositorio. Así se midió la ejecución de «Begin Encounter»:

| Estado de la base | Conexiones | Sentencias | Datos enviados |
|---|---|---|---|
| Vacía (primer arranque) | 460, una por transacción (`account_store._transaction`) | 1.410 | 15,3 MB, el paquete de fotos |
| Ya cargada (otro residente en la misma base) | 28 | 79 | 43 KB |

Las demás ejecuciones de esas pruebas abren entre 3 y 19 conexiones. El peso está en la importación de la primera
vez, que el fixture repite en cada prueba porque recrea el esquema.

**Ajuste con los tiempos del Mac:**
- las dos reejecuciones dan un tiempo de ida y vuelta efectivo de 32 a 38 ms, coherente entre ambas;
- con ese valor, «Begin Encounter» sobre una base vacía tarda unos 168–175 s en ese enlace: entre el 93 % y el 97 %
  del límite de 180 s;
- el mismo modelo predice 2.215 s para las 23 pruebas, y la corrida conjunta tardó 2.142 s: una diferencia del 3 %.

**Clasificación: latencia del proveedor que choca con el límite del arnés.**
- No hubo falla de aserción, error de base de datos ni excepción de la app.
- Las dos fallas están en la misma línea del fixture. Ese mismo fixture terminó a tiempo en las otras 8 pruebas y en
  las dos reejecuciones.
- No hace falta otro mecanismo para explicarlo: la latencia medida deja esa ejecución a 3–7 % del límite.
- En ninguna corrida local de estas pruebas apareció un cuelgue.

**Repetir tal cual no basta.** Hubo 2 de 12 arranques sobre base vacía por encima de 180 s. Con esa proporción, que
diez seguidos terminen a tiempo pasa más o menos 1 vez de cada 6.

**Nota para el piloto, que no es parte de B-1.** El primer encuentro sobre la base nueva del piloto hará esa misma
importación. Cuánto tarde depende de la latencia entre la app desplegada y Neon; conviene medirlo en la prueba de humo
(sección 11).

### 19.3 Qué exige la aceptación vigente

| Fuente | Qué dice |
|---|---|
| 16.8 | PASS: «pytest da **23 passed, 0 failed, 0 errors y 0 skipped**». FAIL: «cualquier falla o error» |
| 18.8 | PASS: la última línea de pytest dice `23 passed`, sin `failed`, `error`, `skipped` ni `xfailed`. FAIL: cualquier `failed` o `error` |
| 16.4, paso 5 | «Correr B-1 en el proveedor sobre ese commit (16.8): 23/23» |

**Las fuentes piden una corrida única.**
- Las conductas A–G quedaron demostradas en el proveedor, sumando la corrida conjunta y las dos reejecuciones.
- Aceptar evidencia repartida entre corridas sería un criterio nuevo, adoptado después de ver el resultado.
- La corrida conjunta es FAIL según 16.8 y 18.8.

### 19.4 Cambio mínimo propuesto, sin implementar; requiere autorización

**Dónde y qué:** en `test_phase0_submission_guard_on_postgres.py`, línea 77 (fixture `gi_bleed`), cambiar
`AppTest.from_file(APP, default_timeout=180)` por `AppTest.from_file(APP, default_timeout=300)`.

**Por qué 300 s:**
- es 1,7 veces la ejecución sobre base vacía estimada para el enlace más lento usado hasta ahora, de unos 170 s;
- 240 s dejaría sólo 1,4 veces;
- un cuelgue real se sigue cortando a los cinco minutos.

**Por qué es sólo del arnés:**
- `default_timeout` sólo fija cuánto espera AppTest cada ejecución simulada;
- no lo leen la app, la configuración de Streamlit ni el runtime desplegado;
- no cambia ninguna aserción ni el cuerpo de ninguna prueba;
- el archivo se omite cuando falta `MRS_TEST_POSTGRES_URL`.

**Qué se vuelve a correr:**
- **local:** las cuatro pruebas de proveedor sobre el PostgreSQL descartable, con 23/23;
- **en Neon, desde el Mac:** una sola corrida de las cuatro pruebas, sobre el nuevo SHA y por la URL *pooled*, con
  23 passed y 0 errores;
- **suite completa:** este cambio no la exige, porque sólo toca un archivo que se omite sin URL. El contrato de
  promoción (16.4, paso 3) la corre igual sobre el candidato final.

**Candidato:** el cambio toca un archivo fuera de `docs/`, así que el candidato de B-1 pasa a ser ese commit nuevo. El
código de runtime sigue siendo idéntico al de `e200ccc`.

**Fase 0:** sigue válida. El cambio no toca runtime ni aserciones, y las pruebas que cita el cierre de la Fase 0
conservan su nombre y su contenido.

**Alternativa sin cambio:** correr desde un equipo con menos latencia hacia Neon. Desde el Mac, sin el cambio, la
corrida única no es fiable (19.2).

### 19.5 Secrets globales de Streamlit

- **No afectan esta evidencia.** La corrida usó un `HOME` vacío, que impide leer `~/.streamlit/secrets.toml`, y la
  comprobación del destino confirmó `mrs_b1` al final.
- **El aislamiento por `HOME` bastó para esta corrida.**
- **Corregir el arnés sigue siendo una tarea aparte**, de sólo pruebas, antes del despliegue.

### 19.6 Estado

- **B-1: STILL BLOCKED.**
- **Lo único que falta:** una corrida única en el proveedor con **23 passed, 0 errors y 0 skipped**. Tiene que ser
  sobre el SHA con el límite corregido y por la URL *pooled* de `mrs_b1`.
- Si la rama `pilot-b1-validation` ya venció, se vuelve a crear igual (18.1 y 18.3).
- **B-5: BLOCKED.**
- Sigue **NOT READY FOR DEPLOYMENT**.

## 20. B-1 resuelto (2026-10-07)

Encargo: registrar la corrida final en el proveedor y reevaluar la preparación. **B-1: RESUELTO.** Sigue **NOT READY
FOR DEPLOYMENT**: queda B-5.

### 20.1 Evidencia, informada por la persona responsable

| Qué | Resultado |
|---|---|
| SHA probado | `8ff41a45a6ce60dfc652149b2ef774424304e49a` |
| Entorno | Python 3.11.9, Streamlit 1.64.0 y psycopg 3.3.6, con `HOME` aislado |
| Proveedor | Neon: proyecto `management-reasoning-simulator`, rama `pilot-b1-validation` («schema only»), base `mrs_b1` |
| Conexión | Endpoint *pooled* del cómputo de la rama, PostgreSQL 17.11, TLS |
| Destino antes | `TARGET OK`: el cómputo coincide, la base es `mrs_b1`, el rol es su dueño, versión 17, TLS |
| Corrida única de las cuatro pruebas | **23 passed in 2208.13s (0:36:48)**: 23 resultados, sin fallas, errores ni omisiones |
| Destino después | `TARGET OK`, con lo mismo, servidor 17.11 y 16 tablas en `public` |
| Fecha | 2026-10-07 |

### 20.2 Frente a la aceptación vigente

| Criterio (16.8 y 18.8) | Evidencia |
|---|---|
| 23 passed, 0 failed, 0 errors y 0 skipped, en una sola corrida | La corrida final (20.1) |
| La URL *pooled*, la que usará la app (16.8 y 18.4) | El endpoint termina en `-pooler`, antes y después |
| PostgreSQL 17 y TLS | 17.11 y `client TLS: True` |
| `TARGET OK` antes y después, con producción sin tocar | Antes y después, el cómputo es el de `pilot-b1-validation` |
| Base vacía antes del arranque, y arranque con `check_database.py` | Se mostró en la primera corrida, sobre la misma base (19.1): 0 tablas antes; «Connected.», el usuario puede crear tablas y el store abrió; 7 tablas después. En la corrida final, cada prueba recrea el esquema vacío por la URL *pooled* |
| Ningún registro con secretos | La evidencia que llegó aquí no trae URL, contraseña ni host completo. El conteo del paso 6 no se informó: hay que confirmarlo al archivar la evidencia |

Esa corrida cubre A–G, H (esquema), I (PostgreSQL 17), J (TLS y proveedor) y K (transacciones y revisiones), según la
tabla de 18.7.

### 20.3 El candidato

- **El candidato de B-1 es `8ff41a4`.** Fuera de `docs/`, lo único que cambia respecto de `e200ccc` es la línea 77
  de `test_phase0_submission_guard_on_postgres.py` (de 180 s a 300 s; 19.4). El código de runtime es el mismo.
- **Si las firmas de B-5 cambian un texto activo, el candidato final cambia.** El contrato de promoción (16.4, pasos
  3 a 5) vuelve a correr la suite, las regresiones y B-1 sobre ese SHA.

### 20.4 La rama de Neon

- **`pilot-b1-validation` sigue siendo descartable y está lista para limpiarse.** Desde aquí no se borró, y borrarla
  requiere autorización.
- **Producción no se tocó:** todas las conexiones fueron al cómputo de esta rama.

### 20.5 Qué queda: B-5

Ninguna firma está hecha (sección 6). Las 64 filas de `docs/revision/CIERRE_PREPILOTO.md` (sección 2) siguen con «☐».

**Antes de construir el candidato final:**

| Filas | Qué | Estado | Dónde |
|---|---|---|---|
| 1–18 | R-4: 18 frases del motor | 1–11 en borrador, 12–18 activas | `docs/revision/R4_FRASES_MOTOR.md` |
| 19–26 | Notas de la TEP y aviso del sangrado | Activas | `CIERRE_PREPILOTO.md` |
| 27–38 | Líneas del examen y rótulos del E-FAST | En inglés, activos; en español, con el relato | `CIERRE_PREPILOTO.md` |
| 39–44 | Límites declarados | Activos en inglés | `CIERRE_PREPILOTO.md` |
| 45–46 | C14 de la 52m y de la 70f | Activos en inglés | `CIERRE_PREPILOTO.md` |
| 47–60 | R-2: 14 fichas POCUS C14 YES | — | `docs/revision/R2_POCUS_C14.md` |
| 61 | R-3: TDFC final | — | `docs/tdfc/TDFC_TABLA_FINAL.md` |
| 62–63 | Guía docente y guía del residente | Hay que actualizarlas antes de firmar: no describen lo que cambió la Fase 0 (10.2-c) | `docs/GUIA_DOCENTE_PILOTO.md`, `docs/GUIA_RESIDENTE_PILOTO.md` |
| 64 | Aviso de la foto | En inglés, activo; en español, en borrador | `CIERRE_PREPILOTO.md` |
| F0-11 | 19 frases nuevas de la Fase 0, si el piloto corre en español | Activas | `docs/revision/F0_11_FRASES_ES.md` |

**Después del despliegue, en la app:**
- los relatos de los casos en español, aprobados en el tablero docente de la base desplegada antes de jugar en
  español;
- los descriptores de la rúbrica en español; sin aprobación, se muestran en inglés.

**Actualización del 2026-10-07 (B-5, decisiones docentes):** el relato en español de los 30 casos y los
descriptores de la rúbrica en español se revisan antes de congelar el candidato final, que no se congela sin esas
revisiones; ya no quedan para después del despliegue. El relato aprobado entra en el candidato en
`case_text/es/approvals.json` (camino a; el archivo se crea después de la revisión docente), sin volver a
registrarlo a mano en la base del piloto. El mecanismo con que la rúbrica se activa en el candidato se identifica
antes de implementarla (Decision File, décima y undécima actualizaciones; TD-81).

**Y la condición C:** la autorización explícita del piloto (Decision File).

### 20.6 Estado

**Bloqueos:**
- B-1, B-2, B-3, B-4 y B-6: RESUELTOS;
- **B-5: BLOCKED.**

**NOT READY FOR DEPLOYMENT.** Después de B-5 viene el contrato de promoción (16.4):
1. el candidato final;
2. la suite y las regresiones;
3. B-1 de nuevo, si cambió el SHA;
4. la rama del piloto;
5. los Secrets, con TD-75;
6. el preflight;
7. el despliegue;
8. la prueba de humo, que incluye el primer encuentro sobre la base vacía (TD-78);
9. las fotos (TD-56);
10. el GO explícito.

**Sin corregir, sin bloquear el despliegue:**
- TD-76: el respaldo en PostgreSQL 17, antes del primer respaldo con datos;
- TD-77: el aislamiento de los Secrets en las pruebas;
- TD-78: el primer encuentro sobre una base vacía.
