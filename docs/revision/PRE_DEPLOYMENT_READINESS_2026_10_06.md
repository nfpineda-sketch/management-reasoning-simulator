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
| B-1 | **ABIERTO** | Prueba PostgreSQL del proveedor no corrida (BLOCKED / NOT RUN) | La persistencia del piloto vive en el proveedor; sólo se probó PostgreSQL 16 local | Correr `test_phase0_submission_guard_on_postgres.py` (y los otros tres archivos de PostgreSQL) contra una base **descartable** del proveedor, de su misma versión mayor, desde un equipo con red directa (runbook §3, paso 0) | No |
| B-2 | **BLOCKED** (2026-10-07; sección 15): diseño definido; faltan la app, la base, el Python y las vinculaciones de las apps (15.12) | Entorno de destino sin identificar | No se sabe qué app, qué rama, qué base ni qué Python | Nombrar la app y la base del piloto; crear la app con Python 3.11; desplegar una rama propia fija en el commit aprobado (3.2) | No |
| B-3 | **RESUELTO** (`87bbbe1`; 14.1): opción (b), el preflight corregido; el runtime no cambió | El preflight puede dar «LISTA» con la app fuera de la configuración congelada (3.3 y 5.2) | El gate del runbook (paso 3) no garantiza lo que dice | **Decisión:** (a) procedimiento: `OPENAI_API_KEY` ausente, valores entre comillas y todo AVISO de los indicadores del manifiesto tratado como FALLA; o (b) corrección del preflight (sólo la herramienta, no el runtime): tratar un valor TOML no textual como ausente, como hace Streamlit, y volver obligatorias las reglas que el manifiesto exige (cambia `test_a_recommendation_warns_and_never_fails`) | No (no toca el runtime) |
| B-4 | **RESUELTO** (`4d570a8`; 14.2): `streamlit==1.64.0`. Python 3.11 se elige al crear la app y queda en B-2 | Dependencias sin fijar: Streamlit `>=1.41,<2` (hoy instalaría 1.65.0) y Python sin fijar | El envío seguro depende de la secuencia de reruns de Streamlit; una versión que aparezca durante el piloto entraría en el próximo reinicio | **Decisión:** fijar en `requirements.txt` una versión verificada, `streamlit==1.64.0` (la de la suite completa) o `1.65.0` (verificada hoy sólo en la Fase 0 y en 0D, 9.4), y crear la app con Python 3.11. Es un commit de dependencias; el runtime no cambia | No con 1.64.0. Con 1.65.0, la suite completa con esa versión |
| B-5 | **ABIERTO** | Firmas docentes pendientes (sección 6) | `READINESS` las exige antes del piloto; una firma que cambie un texto cambia el candidato | Las firmas, antes de construir el candidato final | Sólo si una firma cambia texto: se repiten las pruebas afectadas y la suite |
| B-6 | **RESUELTO** (`e200ccc`; 14.3): textos esperados actualizados con su justificación; 56 de 56 | 2 de las 56 regresiones activas fallan (9.5); `run_regressions.py` sale con código 1 | La verificación del proyecto exige las regresiones activas (las fuentes de verdad las nombran; los ciclos anteriores informaron 56 de 56); sin ellas, las pruebas no están en verde | **Decisión:** actualizar los 3 textos esperados en los 2 scripts al texto que la Fase 0 aprobó (`turn=None`; `interpreted_action` con `_untag`), con su justificación, o retirarlos con motivo como en P-11. No cambia el runtime | No: la suite de pytest y sus conclusiones siguen; agrega la corrida de regresiones que la Fase 0 omitió |

**Antes de abrir el piloto, después del despliegue (no bloquean el despliegue mismo):** TD-56 (sección 7), relato en
español aprobado en la base desplegada si el piloto corre en español, prueba de humo desplegada (sección 11) y la
autorización explícita (C).

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

Estado actualizado el 2026-10-06, después de resolver B-3, B-4 y B-6. Lo que valía sobre `009aadb` se conserva en
la columna «Por qué».

| Categoría | Estado | Por qué |
|---|---|---|
| A · Código y pruebas | **PASS** (sujeto a 14.4) | Sobre `009aadb`: suite completa 7.578/0, Fase 0 completa y prueba de humo automática en verde, y 2 de 56 regresiones activas fallaban (B-6). Ahora: 56 de 56 y las pruebas focalizadas en verde (14.4). La suite completa sobre el candidato final se corre después de este commit y se informa en la entrega del encargo: si no da 0 fallas, esta fila no vale |
| B · Base de datos | **BLOCKED** | PostgreSQL 16 local con TLS: 23 de 23 y simulacro de respaldo aprobado; proveedor: BLOCKED / NOT RUN (B-1) |
| C · Configuración congelada | **BLOCKED** | El gate ya es confiable: falla cerrado ante cualquier exigencia del manifiesto (B-3 resuelto, 14.1). Falta correrlo con los Secrets del destino (runbook §3, paso 3), que no se conocen (B-2, sección 15) |
| D · Enrutamiento | PASS WITH DECLARED LIMITATION | 30 aceptados, excluido y PS001 fuera (5.1); `MRS_DEFAULT_VARIANT` sólo lo cierra la configuración (5.2), y el preflight falla si está definido (14.1) |
| E · Idioma y firmas docentes | **BLOCKED** | Todas pendientes (sección 6; B-5) |
| F · Imágenes y TD-56 | PASS WITH DECLARED LIMITATION | Procedimiento declarado y verificable; falla hacia la vista neutral (sección 7) |
| G · Entorno de despliegue | **BLOCKED** | Diseño definido: rama `pilot-residents-v1`, app nueva, base propia y contrato de promoción (sección 15). App, base, Python y vinculaciones de las apps sin identificar (B-2, 15.12). Streamlit fijo en 1.64.0 (B-4 resuelto, 14.2) |
| H · Seguridad y acceso | PASS WITH DECLARED LIMITATION | Pruebas de permisos, aislamiento, diagnósticos y fotos en verde (9.6); sin credenciales versionadas. Limitación: la ausencia de `OPENAI_API_KEY` en los Secrets es obligatoria (3.3); desde `87bbbe1`, si quedara, el preflight falla salvo que la app la retenga (14.1) |
| I · Observabilidad | PASS WITH DECLARED LIMITATION | Base y fotos en el registro del servidor; conflictos, envíos interrumpidos e inconsistencias sólo en la sala y en el registro del encuentro (11.1) |
| J · Plan de humo desplegado | PASS (READY) | Sección 11; se ejecuta después de resolver los bloqueos y con autorización |

## 13. Recomendación

**NOT READY FOR DEPLOYMENT.** Bloquean B-1, B-2 y B-5. B-3, B-4 y B-6 se resolvieron el 2026-10-06 (sección 14); al
escribir la primera versión de este documento bloqueaban B-1 a B-6.

- El runtime de `009aadb` no mostró un defecto de conducta: la suite completa, la Fase 0, PostgreSQL con TLS, el
  simulacro de respaldo y la prueba de humo automática pasan, y el envío seguro se comporta igual con Streamlit 1.65.0.
- Falta: la prueba en el proveedor (B-1), el entorno de destino, con el preflight corrido sobre sus Secrets (B-2:
  diseño definido y bloqueado por información de las cuentas, sección 15), y las firmas (B-5).
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
- repositorio `nfpineda-sketch/management-reasoning-simulator`;
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
| 3 | Repositorio exacto | SÍ: `nfpineda-sketch/management-reasoning-simulator` |
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
