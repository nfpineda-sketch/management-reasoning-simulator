# Runbook de promoción y despliegue del piloto

> **Plan preparado; nada ejecutado.** Sesión autónoma del 2026-10-08, rama `clinical-encounter-v0.13`.
>
> - No se creó `pilot-residents-v1` ni la rama o la base del piloto en Neon, ni la app de Streamlit.
> - No se hizo push ni despliegue.
> - Cada paso con efecto externo (push, Neon, Streamlit, Secrets, «Reboot app», GO) necesita autorización expresa
>   en su momento. Una aprobación anterior no la sustituye.
>
> **De dónde sale:**
> - el contrato de promoción (`docs/revision/PRE_DEPLOYMENT_READINESS_2026_10_06.md`, §16.4);
> - la topología (§16.3), la base (§16.7 y §16.10) y el contrato de Secrets (§16.11);
> - la puerta de encuentros abiertos (§15.10 y §16.12) y la prueba de humo (§11);
> - B-1 (§18 y §20), el respaldo (`docs/RESPALDO_Y_RESTAURACION.md`) y el mapa de implementación
>   (`docs/revision/B5_IMPLEMENTATION_READINESS_MAP.md`).
>
> Este documento no cambia esas fuentes: las ordena en una sola secuencia ejecutable. Si alguna difiere, rige la
> fuente y se informa la diferencia.
>
> **Reemplaza para el piloto** a `docs/RUNBOOK_PILOTO.md`, que quedó desactualizado frente a §16:
> - nombra `clinical-encounter-v0.13` como la rama desplegada;
> - su paso 0 corre una sola prueba;
> - no lista `MRS_FREE_GENERATION`.
>
> Ese runbook se actualiza o se marca como superado en IG-6 del mapa.
>
> **Decisiones del 2026-10-08 («FINAL FACULTY DECISIONS + LOCAL IMPLEMENTATION AUTHORIZATION»), registradas aquí
> sin ejecutar nada:**
> - rama de la Fase 1: `phase-1-contracts-v2`, desde el mismo SHA congelado que `pilot-residents-v1` (6B); ninguna de
>   las dos se crea en esta ronda;
> - base de la prueba de humo: los 25 pasos corren en un destino descartable, nunca en `mrs_pilot` (6E);
> - visibilidad de la app del piloto: PRIVADA o RESTRINGIDA; si no se puede, detenerse antes del despliegue (6D);
> - `clinical-encounter-v0.13` no se empuja: empujarla redespliega la app de desarrollo (6B).
>
> No se creó ninguna base, rama de Neon ni app de Streamlit, y no hubo push ni despliegue.
>
> **Etiquetas:** VERIFICADO EN EL CÓDIGO · VERIFICADO CON PRUEBA · CONFIRMADO POR LA PERSONA RESPONSABLE (en los
> proveedores; no verificable desde aquí) · PROPUESTO · SUPUESTO / POR DEFINIR.

## 6A. Puerta de promoción

**No se promueve nada mientras falte una sola de estas condiciones.**

| N.º | Condición | Cómo se demuestra | Estado al 2026-10-08 |
|---|---|---|---|
| P-1 | Los 30 relatos aprobados por la docencia, cada uno en su versión exacta | `docs/revision/B5_RELATO_INTEGRIDAD_30.md` con 30 APROBADO | **30 de 30**, cada uno atado a su hash (docencia, 2026-10-08) |
| P-2 | TD-84 y TD-85 decididos por la docencia | Decision File | **Decididos** el 2026-10-08 e implementados en local (IG-4 e IG-3) |
| P-3 | Ronda de implementación autorizada y hecha (IG-0 a IG-7 del mapa) | Commits locales por grupo; pruebas focalizadas en verde | Autorizada el 2026-10-08; estado por grupo en `docs/revision/B5_CANDIDATO_LOCAL.md` |
| P-4 | Matriz A del mapa (§9) en verde sobre **un solo** SHA, con el árbol limpio | Evidencia de A-1 a A-14 (6H) | No corrida (no hay candidato) |
| P-5 | Guías H-62 e I-63 actualizadas al comportamiento final y firmadas | Firma registrada en el Decision File | DEFER (a propósito) |
| P-6 | Rama de desarrollo después del piloto decidida (`phase-1-contracts-v2` o seguir en `clinical-encounter-v0.13`) | Decision File | **Decidida** (2026-10-08): `phase-1-contracts-v2`, desde el mismo SHA congelado que `pilot-residents-v1`. No creada |
| P-7 | Autorizaciones de esta ventana: push de `pilot-residents-v1`; rama y base en Neon; app de Streamlit; Secrets; despliegue; GO | Cada una expresa y registrada | Ninguna concedida |

**SHA candidato:** `<SHA_FINAL>`, de 40 caracteres. Hoy POR DEFINIR: el último runtime certificado es `8ff41a4`
(B-1), y la ronda de B-5 lo cambiará (readiness §20.3).

## 6B. Plan de Git para `pilot-residents-v1`

**Reglas** (§16.3–§16.5):
- `pilot-residents-v1` sólo recibe candidatos aprobados;
- sólo se avanza por avance rápido (*fast-forward*);
- nunca force-push sin una decisión expresa;
- los commits de la Fase 1 nunca van a `pilot-residents-v1`.

**Pasos** (cada push, con autorización):

```sh
# 0. En el clon de trabajo, árbol limpio y SHA exacto
git status --short                      # vacío
git rev-parse HEAD                      # == <SHA_FINAL>
git cat-file -t <SHA_FINAL>             # commit

# 1. Primera promoción: crea la rama remota en ese SHA (no mueve clinical-encounter-v0.13)
git push origin <SHA_FINAL>:refs/heads/pilot-residents-v1

# 1'. Promociones siguientes: comprobar primero que es avance rápido
git fetch origin pilot-residents-v1
git merge-base --is-ancestor origin/pilot-residents-v1 <SHA_FINAL> && echo FAST-FORWARD   # si no lo imprime: detener
git push origin <SHA_FINAL>:refs/heads/pilot-residents-v1

# 2. Verificar que la rama remota es exactamente el candidato
git ls-remote origin refs/heads/pilot-residents-v1    # debe devolver <SHA_FINAL>
```

**Notas:**
- **El push de un SHA sube sus objetos.** La rama del piloto puede crearse sin empujar `clinical-encounter-v0.13`.
- **Empujar `clinical-encounter-v0.13` redespliega la app de desarrollo** (§16.5, confirmado). **Decisión del
  2026-10-08: no se empuja.** Sus commits locales siguen sin empujar; empujarla exige otra autorización expresa.
- **Rama de desarrollo después del piloto: decidida el 2026-10-08.** La Fase 1 va en `phase-1-contracts-v2`, creada
  desde el **mismo SHA congelado** que `pilot-residents-v1` (`<SHA_FINAL>`). Reemplaza lo que decía readiness §16.3
  («seguirá» en `clinical-encounter-v0.13`).
  - No se crea ni se empuja en esta ronda; crearla es parte de la autorización de la Fase 1.
  - Al autorizar la Fase 1, se actualiza la línea de la rama autorizada de CLAUDE.md (hoy,
    `clinical-encounter-v0.13`).
  - Paso, con autorización: `git push origin <SHA_FINAL>:refs/heads/phase-1-contracts-v2` y comprobar con
    `git ls-remote origin refs/heads/phase-1-contracts-v2` que devuelve `<SHA_FINAL>`.

## 6C. Plan de Neon

| Elemento | Valor | Fuente |
|---|---|---|
| Proyecto | `management-reasoning-simulator` (PostgreSQL 17) | §16.2, CONFIRMADO POR LA PERSONA RESPONSABLE |
| Rama | `pilot-residents-v1`, creada como **«Schema only»** (raíz independiente, sin filas) | §16.10, recomendación C |
| Base | `mrs_pilot`, **nueva y vacía**, cuya dueña es un rol propio de la app del piloto | §16.10 |
| Conexión de la app | URL *pooled* de `mrs_pilot`, `sslmode=require` | §16.10 y §16.11 |
| Conexión de respaldos | URL **directa** (no *pooled*), `pg_dump` 17 | §16.10; TD-76 |
| Nunca | `production`; las ramas archivadas como madre (crear una hija las desarchiva); una rama normal desde `production` (copiaría datos) | §16.7 |

**Pasos** (con autorización; en la consola de Neon):
1. Crear la rama `pilot-residents-v1` con «Schema only».
   - Si la opción no está disponible, **detenerse**: decide la persona responsable entre (i) y (ii) de §16.10.
2. Dentro de la rama, crear el rol de la app y la base `mrs_pilot` con ese rol como dueño. No usar la base heredada.
3. Copiar la URL *pooled* de `mrs_pilot` a un archivo local de Secrets, fuera del repositorio y nunca versionado.
   No se imprime ni se pega en ningún chat.
4. **Comprobar el destino antes de conectar la app.** El ayudante `b1_target_check.py` de readiness §18.10 **no
   está en el repositorio**; se recrea en la ventana desde el texto de §18.6, cambiando:
   - `mrs_b1` por `mrs_pilot`;
   - el ID del cómputo por el de `pilot-residents-v1`.

   Debe dar `TARGET OK`: cómputo correcto, base `mrs_pilot`, rol dueño, versión 17, TLS y `tables in public: 0`.
5. **Arranque del esquema:** `python3 check_database.py --create` (VERIFICADO EN EL CÓDIGO: «open the store as the
   application does, creating its tables»), con la URL del paso 3 en el entorno y sin imprimirla.
   - Debe decir «Connected.», que el usuario puede crear tablas y que el store abrió.
   - La app también crea sus tablas al abrirse (`CREATE TABLE IF NOT EXISTS`), las metas, el paquete de fotos y el
     primer administrador (§16.10). No se siembran datos.
6. **Respaldo cero:** `pg_dump --format=custom --no-owner --no-privileges` sobre la URL directa, con el
   procedimiento de `docs/RESPALDO_Y_RESTAURACION.md`.
   - **Se recomienda (TD-76, matriz C) el simulacro de restauración en PostgreSQL 17:** restaurar en una base vacía
     de la misma rama y comparar con `tools_backup_drill.py --compare`.
7. **Limpieza de B-1:** la rama `pilot-b1-validation` sigue en el proyecto (readiness §20.4). Borrarla requiere
   autorización expresa. No bloquea el piloto.

**La identidad de la base no queda en el registro del encuentro.** El runtime no la anota (VERIFICADO EN EL CÓDIGO:
el encuentro guarda `code_version`, no el destino de la base). Se verifica en los pasos 4 y 5, y otra vez en 6E-2.

## 6D. Plan de Streamlit

**App nueva** (§16.2 y §16.3; no existe todavía; con autorización):

| Campo de la app | Valor |
|---|---|
| Nombre / subdominio | `clinical-management-reasoning-pilot` → se espera `https://clinical-management-reasoning-pilot.streamlit.app/` |
| Repositorio | `management-reasoning-simulator` |
| Rama | `pilot-residents-v1` |
| Archivo principal | `app.py` |
| Python | **3.11**, elegido en «Advanced settings» al crearla. Cambiarlo después obliga a borrar la app y volver a desplegarla (§16.6). Ningún archivo del repositorio lo fija (VERIFICADO: no hay `runtime.txt`) |
| Dependencias | `requirements.txt` del SHA: `streamlit==1.64.0` (B-4), `psycopg[binary]>=3.2,<4`, etc. |
| Visibilidad de la app | **PRIVADA o RESTRINGIDA** (decisión del 2026-10-08). Si no está disponible o no es práctica, **detenerse antes del despliegue** e informar: nunca pasar en silencio a una app pública. La cuenta se exige además: `MRS_AUTH_MODE = "accounts"`. Ninguna acción en Streamlit está autorizada en esta ronda |
| La app de desarrollo | `clinical-management-reasoning-dev` no se toca |

**Matriz de configuración.** Los valores son cadenas entre comillas en el TOML de Secrets. Las reglas de la columna
«Chequeo del preflight» son las de `tools_pilot_preflight.py` (VERIFICADO EN EL CÓDIGO).

| Setting | Valor exigido | ¿Secreto? | Por qué | Chequeo del preflight | Modo de falla si está mal |
|---|---|---|---|---|---|
| `MRS_DATABASE_URL` | URL *pooled* de `mrs_pilot`, `sslmode=require` | **SÍ** | La única base del piloto | `database_url`; con `--connect`, la conexión | Apunta a otra base: encuentros en el lugar equivocado y sin rastro en el registro del encuentro. Por eso se comprueba en 6C-4 y 6E-2 |
| `MRS_AUTH_MODE` | `"accounts"` | NO | Cuentas individuales; sin contraseña compartida | `auth_mode` | Otro valor: la app se cierra con «Access is temporarily closed…» (`account_portal.py:49–54`) o queda en modo compartido |
| `MRS_OFFLINE_CASES` | `"1"` | NO | Sólo los casos del banco, sin generación | `offline_cases` | Generación de casos fuera del banco congelado |
| `MRS_PAID_GENERATION` | `"off"` | NO | Sin llamadas pagadas | `paid_generation_off` | Gasto e IA durante el encuentro (contra la fila «IA del primer piloto») |
| `MRS_FREE_GENERATION` | Ausente | NO | Generación cerrada | `free_generation_closed` | Igual que la anterior |
| `MRS_DEFAULT_VARIANT` | Ausente | NO | Salta la exclusión de casos (readiness §5.2) | `no_pinned_case` | Un caso fijo, incluido el excluido |
| `MRS_REPLAY_CASE` | Ausente | NO | Sin reproducción de un caso | `no_replay_case` | Un caso fijo |
| `MRS_CODE_VERSION` | `"<SHA_FINAL>"` | NO | Cada turno lleva el SHA | `code_version` (contra `--commit`) | Registros con un SHA falso: se pierde la trazabilidad |
| `MRS_IMAGE_REQUIRE_REVIEW` | `"on"` | NO | Sólo fotos con sus dos revisiones (TD-56) | `image_review` | Fotos sin revisar en la sala |
| `MRS_ADMIN_USERNAME`, `MRS_ADMIN_PASSWORD_HASH` | Sólo para crear el primer administrador; después se retiran | El hash: **SÍ** | Arranque | `admin_bootstrap` (`check_database.py --admin-hash` lo valida) | Sin administrador no hay invitaciones. Dejarlos amplía la superficie de acceso |
| `OPENAI_API_KEY` | **Ausente** | **SÍ** | Sin IA del proveedor en el piloto | `provider_key_withheld`. **Ojo:** la regla también pasa si la clave está presente y la app la retiene (`tools_pilot_preflight.py:217–218`); §16.11 exige ausencia. **Comprobación manual adicional** en 6E-1 | Una clave cargada en un entorno de residentes |
| `MRS_ALLOW_LOCAL_SQLITE` | Ausente | NO | En la nube, SQLite es efímero | `no_local_sqlite` | Datos que se pierden al reiniciar (en la nube se rechaza: `account_portal.py:126–134`) |
| `MRS_SYNTHETIC_ACCOUNTS`, `MRS_BATCH_*` | Ausentes | Contraseñas: **SÍ** | Sin cuentas sintéticas | `no_batch_settings` (AVISO; el contrato exige que no salga) | Cuentas de prueba en la base del piloto |
| `STREAMLIT_RUNNER_FAST_RERUNS` y `STREAMLIT_*` | Ausentes | NO | `fastReruns = false` certificado en la Fase 0 | `fast_reruns` | Envíos dobles o perdidos |
| `.streamlit/config.toml` `[runner] fastReruns` | `false` en el SHA | NO | Igual | `fast_reruns` | Igual |
| `MRS_PUBLIC_APP_URL` | La URL asignada (se espera la de arriba) | NO | Enlaces de invitación | Ninguna (TD-75) | Invitaciones con un enlace equivocado |
| `MRS_IMAGE_BANK` | Ausente | NO | El banco de fotos aprobadas queda activo | Ninguna (TD-75) | Sin fotos aprobadas |
| `MRS_LANGUAGE` | Opcional (`es` o `en`); decisión docente | NO | Idioma inicial | Ninguna | — |
| `APP_PASSWORD`, `MRS_DEFAULT_CHALLENGE`, `MRS_ANALYSIS_CORRECTIONS`, `OPENAI_MODEL`, `MRS_*_MODEL`, `MRS_AI_*`, `MRS_IMAGE_BUDGET_*`, `MRS_DIAGNOSTIC_DIR` | Ausentes | `APP_PASSWORD`: **SÍ** | Fuera del alcance del piloto | Ninguna | Configuración heredada de desarrollo |

**Preflight, dos veces** (§16.11):
- **antes de crear la app,** con el archivo local que se va a pegar;
- **después de crearla,** con los Secrets copiados de la app a un archivo temporal.

En las dos: `python3 tools_pilot_preflight.py --secrets <archivo> --commit <SHA_FINAL> --connect` → «Configuración
del piloto: LISTA.», sin `FALLA` y sin `AVISO` de `no_batch_settings`. El archivo se borra al terminar.

## 6E. Prueba de humo desplegada (25 pasos)

**Precondiciones:**
- 6A completa;
- las dos corridas del preflight en «LISTA»;
- «Reboot app» hecho;
- la puerta de encuentros abiertos en 0 (§15.10, consulta 1).

**Cuentas de prueba** (readiness §11):
- `prueba_humo_r2` (residente de año 2) y `prueba_humo_docente`;
- sin nombres reales;
- desactivadas al terminar.

**Destino de la prueba (decisión del 2026-10-08):** los 25 pasos corren **completos en un destino descartable**,
por ejemplo una rama de Neon «Schema only» con una base `mrs_pilot_smoke`, **nunca en la `mrs_pilot` prístina**. No hay
mecanismo de borrado, así que nada de la prueba debe quedar en `mrs_pilot`. En esa corrida, donde la tabla dice
`mrs_pilot` (pasos 2 y 25), se lee el destino descartable. Crear ese destino necesita la misma autorización que 6C; en
esta ronda no se creó ninguna base.

**Después de que los 25 pasos pasen**, en este orden:
1. cambiar el Secret `MRS_DATABASE_URL` a la URL *pooled* de `mrs_pilot` (sin imprimirla);
2. volver a correr el preflight (`tools_pilot_preflight.py --secrets <archivo> --commit <SHA_FINAL> --connect` →
   «LISTA»);
3. verificar la identidad de la base: `TARGET OK` sobre `mrs_pilot` (6C-4) y `python3 check_database.py`;
4. verificar el SHA: la rama desplegada y `MRS_CODE_VERSION` = `<SHA_FINAL>`;
5. correr sólo las comprobaciones que no escriben filas: el paso 1 (configuración de la app), el paso 2 (identidad de
   la base), `python3 check_database.py --photo-approvals` (del paso 19) y la puerta de encuentros abiertos
   (§15.10, consulta 1, en 0);
6. no crear cuentas de residente de prueba en `mrs_pilot` antes del GO.

| N.º | Acción | Esperado | Evidencia | Detener si |
|---|---|---|---|---|
| 1 | Identidad de la app: en Streamlit, Settings de `clinical-management-reasoning-pilot`; en Secrets, comprobar a ojo que `OPENAI_API_KEY` **no** está | Rama `pilot-residents-v1`, `app.py`, Python 3.11; ninguna clave del proveedor | Captura de la configuración, sin los valores de los Secrets | Otra rama, otro archivo, otro Python o una clave presente |
| 2 | Identidad de la base: el ayudante de destino (6C-4) y `python3 check_database.py`, con los Secrets de la app | `TARGET OK` sobre `mrs_pilot`, rama `pilot-residents-v1`, PG 17, TLS; «Connected.» | Salida sin URL ni host | Otra base, otro cómputo o `production` |
| 3 | Ingreso: el administrador crea dos invitaciones; cada cuenta se registra y cambia su contraseña | Ambas entran; ningún error | Captura | Error al entrar |
| 4 | Desafío permitido: el residente pulsa «Begin Encounter» sin directiva | `encounter.assignment.challenge_id` está entre los 7 de R2 (exportación del docente) | JSON exportado | Otro desafío |
| 5 | Caso aceptado | `evaluation_basis.case_id` es uno de los 30 aceptados | JSON | El excluido o uno fuera del manifiesto |
| 6 | SHA en los metadatos | `assignment.code_version` y `evaluation_basis.code_version` = `<SHA_FINAL>` | JSON | Otro SHA |
| 7 | Orden reconocida: una orden del caso con dosis y vía | Se ejecuta; el recibo lo dice | Captura | No se ejecuta o no hay recibo |
| 8 | Orden desconocida: «Zyvox IV.» | «No se entendió: …» en español («Not understood: …» en inglés); nada se administra | Captura | Se administra algo |
| 9 | Paquete mixto: una orden reconocida y «Zyvox IV.» en un envío | La reconocida corre; aviso de lo que no se hizo | Captura | Se pierde una de las dos |
| 10 | «Wait 20 minutes.» | El reloj avanza 20 min, o se detiene en un evento y lo dice | Captura | El reloj no avanza o salta sin aviso |
| 11 | «Reassess.» | Mirada de 2 min en la cabecera, dicha como tal | Captura | — |
| 12 | Evento que interrumpe: el docente dirige `acs_54m_inferior` (R2-04); el residente escribe «Wait 60 minutes.» antes del minuto 45 | La espera se detiene en el minuto 45 (bloqueo AV) y lo dice | Captura y JSON | La espera pasa el evento |
| 13 | Recarga a mitad del encuentro | Sigue igual; nada se ejecuta de nuevo | Captura | Se repite una orden |
| 14 | Doble clic en «Send» | La orden corre una vez (un solo turno en el Trace) | JSON | Dos turnos |
| 15 | Campos de la Fase 0 en el Trace | Cada turno con `trace_extensions`: `submission`, `orders`, `time_semantics`, `events`, `interrupted`, `observation_snapshot`, `limitations`, `versions` | JSON | Falta uno |
| 16 | Procedencia y limitaciones | El bloqueo AV con `SCRIPTED_NATURAL_HISTORY` y `NOT_PREVENTABLE_IN_SIMULATOR`; `scripted_event`; «Zyvox IV.» como `unrecognized_order` | JSON | Falta la procedencia |
| 17 | PS001 inalcanzable: formulario de directiva con R1-03, R1-04 y R2-01 | «Case» ofrece sólo «—»; guardar se rechaza | Captura | Se puede asignar |
| 18 | Caso excluido: formulario con R2-04 y R2-05 | `trauma_hemothorax_41m` no aparece | Captura | Aparece |
| 19 | Fotos (TD-56): llegadas de los dos encuentros; `python3 check_database.py --photo-approvals` | Foto aprobada o vista neutral; la herramienta termina en «All 117 approvals…» | Captura y salida | Una foto sin sus dos revisiones o menos de 117 |
| 20 | Relato en español activo: el panel docente «Case narrative in Spanish» con la sala en español | **30** aprobados y **1** pendiente (`trauma_hemothorax_41m`, sandbox; VERIFICADO: hay 31 borradores y 30 aceptados). Un encuentro en español muestra la llegada en español, p. ej. con T-1 «crépitos» | Captura del conteo y de la llegada | Menos de 30 aprobados, un caso del piloto en inglés o un pasaje mezclado |
| 21 | Rúbrica en español activa: el docente abre la evaluación por rúbrica con la interfaz en español | Sin la nota «Descriptors a faculty member has not yet approved…» (`rubric_portal.py:125–127`); D4 dice «Revisa» y D5 «control posterior» | Captura | Aparece la nota o un dominio en inglés |
| 22 | Inspección del español en la sala: en un encuentro en español, examen de todas las regiones, una orden con fármaco, una pregunta de aclaración, un recibo, el panel de tratamientos y la línea de soporte | Todo en español salvo las excepciones canónicas declaradas; el fármaco según V-9; ninguna clave interna | Capturas | Inglés no declarado o una clave cruda |
| 23 | Documentos descargables en español (PDF y Markdown del encuentro) | En español; el JSON queda como se guardó | Archivos descargados (sin datos reales) | Un documento mezclado |
| 24 | Guías: la docencia confirma que las guías distribuidas son las versiones firmadas (H-62 e I-63) y describen lo que se ve en 20–23 | Coinciden | Registro en el Decision File | Una guía describe otro comportamiento |
| 25 | Cierre: «Complete Encounter & Begin Review»; el docente confirma la rúbrica; el administrador desactiva ambas cuentas; puerta de encuentros abiertos | Foco visible sólo después de la rúbrica; cambio en «Account change history»; la consulta 1 de §15.10 da 0 | Captura, conteo y hora | El foco aparece antes, o una cuenta queda activa |

La parte automática (`tools_pilot_smoke.py --configuration pilot`) crea su propia base y no toca `mrs_pilot`. Se
corre en la recertificación (matriz A), no aquí.

## 6F. Después del despliegue y antes del GO

1. 6E completa en verde y su evidencia archivada (6H).
2. **Identidad:** SHA (6E-6), base (6E-2) y configuración (6E-1) coinciden con el candidato.
3. **Respaldo:** tomado después de la prueba de humo. Se recomienda el simulacro de restauración en PostgreSQL 17
   (TD-76).
4. **Retiro de los Secrets de arranque:** `MRS_ADMIN_USERNAME` y `MRS_ADMIN_PASSWORD_HASH` se retiran después de
   crear el administrador, y el preflight se repite.
5. **Puerta de encuentros abiertos** registrada: conteos, hora y SHA.
6. **GO explícito** del docente responsable (condición C), registrado en el Decision File con la fecha y el SHA.
   Sin GO no entran residentes.

## 6G. Vuelta atrás

**Sólo mecanismos que existen.** No se inventa un modo de mantenimiento ni un borrado.

| Paso | Qué | Cómo (mecanismo existente) | Evidencia |
|---|---|---|---|
| 1 | **DETENER EL PILOTO** | Avisar a residentes y docentes. El administrador **desactiva** las cuentas de residentes. VERIFICADO EN EL CÓDIGO: `account_store.update_user(..., active=False)` (`account_store.py:481–506`) borra sus sesiones y el ingreso rechaza una cuenta inactiva (`:413`). El cambio queda en «Account change history» y se revierte reactivando. Los encuentros abiertos quedan guardados como `active`; nada se borra. **PROPUESTO, con autorización:** si hay que cerrar la app a todos, incluido el administrador, un `MRS_AUTH_MODE` inválido la cierra con «Access is temporarily closed…» (`account_portal.py:49–54`, VERIFICADO EN EL CÓDIGO) y se revierte restaurando el valor | Hora, cuentas desactivadas (conteo) y motivo |
| 2 | **PRESERVAR LA BASE** | `pg_dump` inmediato sobre la URL directa (`docs/RESPALDO_Y_RESTAURACION.md`). Nunca restaurar sobre la base en uso, borrar filas ni recrear la rama | Archivo de respaldo fuera del servidor y su hora |
| 3 | **VOLVER AL ÚLTIMO SHA VERIFICADO** | Dos vías: **(a) recomendada, avance rápido:** revertir el cambio en la rama de desarrollo, recertificar (matriz A) y promover por avance rápido (6B-1'). **(b) Mover `pilot-residents-v1` hacia atrás:** no es avance rápido; exige una decisión expresa de force-push (§16.4). Con cualquiera de las dos: `MRS_CODE_VERSION` del SHA desplegado, puerta de encuentros abiertos y «Reboot app». **Antes de (b),** comprobar que los dos SHA tienen el mismo esquema (comparar sus `CREATE TABLE`; SUPUESTO hasta comprobarlo, porque el esquema se crea con `IF NOT EXISTS` y no hay migraciones) | `git ls-remote`; preflight «LISTA» |
| 4 | **INVESTIGAR** | Las señales de readiness §11.1: registros de la app, `check_database.py`, `submission_log`, limitaciones del Trace, la consulta de enrutamiento. Cada turno tiene su `code_version`, y un encuentro que cruzó dos versiones se declara así | Nota de incidente sin datos personales |
| 5 | **RECERTIFICAR** | La matriz A completa sobre el SHA de la corrección | Evidencia de A-1 a A-14 |
| 6 | **REDESPLEGAR** | 6B → 6D (preflight dos veces) → 6E → 6F, con autorización y con GO nuevo. Reactivar las cuentas sólo después del GO | Registro del despliegue |

## 6H. Paquete de evidencia

Se archiva en el registro del despliegue (`docs/READINESS_PILOTO_FORMATIVO.md`, runbook §4) **sin secretos, URL,
hosts, contraseñas ni nombres de personas**:

| N.º | Evidencia | De |
|---|---|---|
| E-1 | SHA final de 40 caracteres y `git status --short` vacío | Matriz A-14 |
| E-2 | Hashes del relato (30) y de la rúbrica (5) iguales a lo aprobado | Matriz A-2 |
| E-3 | Suite completa: conteo de passed, failed, skipped y xfail; Python 3.11 y Streamlit 1.64.0 | Matriz A-7 |
| E-4 | `PASS: 56/56` | Matriz A-6 |
| E-5 | Centinela del español: 0 líneas | Matriz A-3 |
| E-6 | Lector congelado: diff vacío contra `3d942ee` | Matriz A-4 |
| E-7 | B-1 sobre el SHA final: 23 passed, `TARGET OK` antes y después | Matriz A-11 |
| E-8 | Dos preflights «LISTA» y la comprobación manual de `OPENAI_API_KEY` | 6D; matriz A-12 |
| E-9 | `git ls-remote` de `pilot-residents-v1` = SHA final | 6B-2 |
| E-10 | `TARGET OK` y arranque de `mrs_pilot` | 6C-4 y 6C-5 |
| E-11 | Captura de la configuración de la app (rama, archivo, Python) | 6E-1 |
| E-12 | Los 25 pasos de la prueba de humo con su resultado, en el destino descartable | 6E |
| E-12b | Después de la prueba: Secret cambiado a `mrs_pilot`, preflight «LISTA», `TARGET OK`, SHA y `MRS_CODE_VERSION`, y las comprobaciones sin escritura | 6E, después de los 25 pasos |
| E-13 | «All 117 approvals…» | 6E-19 |
| E-14 | Respaldo y, si se hizo, simulacro de restauración en PG 17 | 6C-6 y 6F-3 |
| E-15 | Conteos de la puerta de encuentros abiertos, con su hora | 6F-5 |
| E-16 | GO del docente responsable, con la fecha y el SHA | 6F-6 |
