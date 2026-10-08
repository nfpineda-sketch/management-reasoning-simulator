# Runbook del piloto formativo

> **SUPERADO PARA EL PILOTO (2026-10-08, B-5, IG-6).** La promoción y el despliegue se hacen con
> `docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md`, que sigue el contrato de readiness §16. Este documento quedó
> desactualizado frente a §16: nombra `clinical-encounter-v0.13` como la rama desplegada (la del piloto es
> `pilot-residents-v1`), su paso 0 corre una sola prueba, no lista `MRS_FREE_GENERATION`, y la prueba de humo ya no
> corre en la base del piloto sino en un destino descartable. Se conserva como registro del ciclo 10; donde difiera,
> rige el runbook de promoción.

Ciclo 10, tarea C10-06 (2026-09-29). Cómo cumplir las condiciones **A** (desplegar el candidato y la
configuración aprobados) y **B** (prueba de humo en el entorno desplegado) de
`docs/READINESS_PILOTO_FORMATIVO.md`, y cómo operar el piloto.

**Este documento no autoriza nada.** Desplegar, invitar residentes e iniciar el piloto son decisiones
del docente responsable (condición **C**). El piloto nunca se inicia automáticamente.

## 1. Lo que se necesita

- **El código:** el commit aprobado de la rama `clinical-encounter-v0.13`, con Python 3.11 y
  `requirements.txt`.
- **La aplicación:** Streamlit, como en `docs/SETUP_v0.11.0.md`.
- **La base:** PostgreSQL persistente, con conexión cifrada (`sslmode=require`) y un usuario que pueda
  crear las tablas `mrs_*`.
- **La configuración:** un lugar privado para los Secrets de la aplicación. Nunca GitHub. En una copia
  local, `.streamlit/secrets.toml` ya está excluido del repositorio.

## 2. La configuración del piloto

| Variable | Valor | Por qué |
|---|---|---|
| `MRS_AUTH_MODE` | `accounts` | Una cuenta por persona y permisos en la base |
| `MRS_DATABASE_URL` | La URL PostgreSQL del proveedor, con `sslmode=require` | Todo el estado vive ahí |
| `MRS_OFFLINE_CASES` | `1` | Casos del banco; ninguna llamada a un proveedor de IA durante el encuentro (0 medidas) |
| `MRS_IMAGE_REQUIRE_REVIEW` | `on` | Sólo fotos con sus dos revisiones humanas aprobadas |
| `MRS_PAID_GENERATION` | `off` | Cierra la generación pagada una segunda vez |
| `MRS_CODE_VERSION` | El commit desplegado | Cada encuentro registra el código que lo produjo |
| `MRS_ADMIN_USERNAME` y `MRS_ADMIN_PASSWORD_HASH` | Salida de `python setup_accounts.py --print-bootstrap` | Crean el primer administrador. **Retírelas una vez creado** |

**No deben estar:**

- `MRS_ALLOW_LOCAL_SQLITE`;
- `MRS_REPLAY_CASE` (serviría un caso escrito por IA);
- `MRS_DEFAULT_VARIANT` (fijaría un caso);
- `MRS_SYNTHETIC_ACCOUNTS` y `MRS_BATCH_*` (cuentas y contraseñas del lote de prueba).

**Congelamiento del piloto (Fase 0, 2026-10-06):** el piloto corre sobre `docs/revision/PILOT_FREEZE_MANIFEST.md`: los casos aceptados con sus huellas, los desafíos permitidos, las versiones, los indicadores y las limitaciones declaradas. `.streamlit/config.toml` conserva `[runner] fastReruns = false` (un segundo clic nunca inicia una ejecución concurrente). No despliegue mientras haya encuentros abiertos: cada encuentro y cada turno registran el código con que corrieron.

**`OPENAI_API_KEY`:** para el piloto, retírela de los Secrets. Si queda, `MRS_OFFLINE_CASES=1` la
retiene en todas partes, pero sin ella no hay nada que retener.

## 3. Desplegar (condición A)

0. **Antes del primer despliegue del commit aprobado (cierre de la Fase 0):** la prueba del envío sobre
   PostgreSQL, en una base **descartable** (nunca la del piloto: la prueba borra y recrea su esquema), de la misma
   versión mayor que la del proveedor:

   ```
   MRS_TEST_POSTGRES_URL='postgresql://…/base_descartable' python3 -m pytest -q test_phase0_submission_guard_on_postgres.py
   ```

   Debe terminar con 10 pruebas aprobadas (A–F y la orden escrita después de una respuesta). En el cierre se corrió
   sobre PostgreSQL 16 local (`docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`, sección 21).
1. **Respaldar** la base si ya existe (`docs/RESPALDO_Y_RESTAURACION.md`).
2. **Poner los Secrets** de la tabla anterior.
3. **Correr el preflight con esos mismos Secrets.** En una copia local del commit aprobado, con los
   Secrets en un archivo que no se versiona:

   ```
   python3 tools_pilot_preflight.py --secrets ruta/a/secrets.toml --connect
   ```

   Debe terminar en «Configuración del piloto: LISTA.». Nunca imprime una clave, una URL ni un hash: sólo
   qué regla se cumple. Una **FALLA** detiene el despliegue; un **AVISO** es una recomendación.
4. **Desplegar** el commit aprobado y abrir la aplicación. Las tablas se crean al abrir; las nuevas del
   ciclo 10 también, sin tocar las existentes.
5. **Entrar como administrador** y retirar de los Secrets `MRS_ADMIN_USERNAME` y
   `MRS_ADMIN_PASSWORD_HASH`. Al abrir su página, la aplicación importa el paquete de fotos; sus
   aprobaciones esperan la cuenta que nombran y no se registran bajo nadie más (TD-56).
6. **Cuenta aprobadora de las fotos (TD-56), antes de cualquier encuentro.** Las 117 aprobaciones de
   `assets/patient_images/approvals.json` nombran una sola cuenta docente. El administrador crea una
   invitación de docente y **la persona que dio esas aprobaciones** registra su propia cuenta con
   **exactamente** ese nombre de usuario (el paso 7 lo muestra). Nunca se crea esa cuenta para otra persona,
   ni se renombra otra cuenta para que coincida, ni se usa la del administrador: la aprobación es de quien la
   dio. Esa persona entra una vez; al abrir su página se registran sus aprobaciones.
7. **Verificar el orden, sólo leyendo:**

   ```
   MRS_DATABASE_URL='…' python3 check_database.py --photo-approvals
   ```

   Debe terminar en «All 117 approvals are recorded under the accounts they name.» y decir el rol de la
   cuenta («as faculty»). Si dice que esperan una cuenta, que tienen su cuenta pero no están registradas, o
   que hay alguna registrada bajo otra cuenta: **no se crea ninguna invitación de residente ni se abre un
   encuentro**. Sin las aprobaciones, todas las llegadas se verían en vista neutral. Si la cuenta correcta no
   puede crearse, es un bloqueo del despliegue: se informa antes de seguir.
8. Sólo entonces, la prueba de humo en la aplicación desplegada (§4) y las invitaciones de los residentes.

## 4. Prueba de humo (condición B)

**Automática, con el mismo commit.** No toca la base del piloto: crea la suya, temporal.

```
python3 tools_pilot_smoke.py --configuration pilot --out smoke.json
```

Debe mostrar:

- 0 intentos de llamar al proveedor;
- encuentros `completed`;
- la rúbrica confirmada y el foco visible sólo después de la revisión;
- los documentos en español;
- los permisos respetados.

**En la aplicación desplegada, con cuentas de prueba sin nombres reales,** después de los pasos 6 y 7 de §3
(la cuenta aprobadora de las fotos ya existe y `check_database.py --photo-approvals` terminó en «All … recorded»):

1. El administrador crea una invitación de residente de año 1 y otra de docente.
2. El residente entra, cambia su contraseña, decide su foto e iniciales, pulsa «Begin Encounter», juega
   el caso y lo cierra.
3. El docente abre la revisión, confirma la rúbrica y comprueba que el residente ve el foco sólo después.
4. El administrador desactiva ambas cuentas de prueba. El cambio queda en «Account change history».
5. Se anota el resultado, fecha y commit, en `docs/READINESS_PILOTO_FORMATIVO.md`.

**Restauración de prueba:** antes del piloto, restaure un respaldo en una base nueva y compare con
`tools_backup_drill.py --compare` (`docs/RESPALDO_Y_RESTAURACION.md`).

## 5. Operar

- **Cuentas:**
  - las personas entran sólo por invitación («Create invitation»);
  - desactivar no borra nada;
  - todo cambio de estado, rol o año queda con autor y hora en «Account change history».
- **Quién elige casos:** el administrador autoriza a un docente para un residente («Who may choose a
  resident's cases»). El docente elige el próximo caso con un motivo, y el residente no lo sabe.
- **Respaldos:** diarios, y antes de cada despliegue.
- **Revisión docente:** `docs/GUIA_DOCENTE_PILOTO.md`. Los residentes reciben
  `docs/GUIA_RESIDENTE_PILOTO.md`.

## 6. Si algo falla

- **Un residente ve un error:** anote la hora, la cuenta y el encuentro. La aplicación le muestra un
  mensaje genérico. El registro del servidor guarda la clase del error y dónde ocurrió, nunca su
  contenido, así que un error de programación ya no se confunde con una caída de la base.
- **Integridad:** `python3 check_database.py --integrity` lista las claves repetidas, sin datos
  personales. No edite la base a mano sin un respaldo previo.
- **Las llegadas se ven en vista neutral:** `python3 check_database.py --photo-approvals` dice si las
  aprobaciones de las fotos esperan su cuenta (TD-56). Una vez creada la cuenta correcta, basta abrir la
  página docente, o `python3 tools_image_bank.py import --database-url "$MRS_DATABASE_URL" --pack
  assets/patient_images`, y volver a verificar.
- **La base no abre:** `python3 check_database.py` dice por qué, sin imprimir la URL.
- **Volver atrás:**
  - redesplegue el commit anterior;
  - el esquema del ciclo 10 sólo agrega tablas e índices, y un código anterior los ignora;
  - si hay que volver a los datos de antes, restaure el último respaldo en una base nueva y apunte
    `MRS_DATABASE_URL` a ella.

## 7. Al terminar

- Cada residente puede descargar su registro completo.
- La retención de los datos la decide el programa.
- La base y sus respaldos contienen información de residentes: se guardan cifrados y con acceso
  restringido.
