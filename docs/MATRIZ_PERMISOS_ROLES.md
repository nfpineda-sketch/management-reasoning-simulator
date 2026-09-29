# Matriz de permisos por rol

Ciclo 9 · 2026-09-29 · §154B, §154C y §154CA–§154CE de la instrucción docente.
Describe lo que el código hace hoy, verificado en los stores (no sólo en la
interfaz), y las pruebas que lo sostienen. La auditoría completa de la interfaz
está en el reporte del ciclo 9.

**Principio.** El residente ve; el docente evalúa; el Admin gobierna; la IA
aconseja. Los tres miran la misma evidencia: cambian los permisos, no los datos
(§154C).

**Modos de acceso.**

- Por defecto, una contraseña compartida sin roles (`MRS_AUTH_MODE` sin definir):
  sirve para demostraciones y no guarda nada por persona.
- Con `MRS_AUTH_MODE=accounts`, cuentas individuales con los roles `resident`,
  `faculty` y `admin`. Esta matriz describe ese modo.

## Matriz

| Capacidad | Resident | Faculty | Admin | Dónde se verifica |
|---|---|---|---|---|
| Correr un encuentro asignado (ciego) | SÍ: ve «Asignado a mí» y la fecha, nunca el desafío, el caso, la razón ni quién lo asignó | NO (sus encuentros son sandbox, fuera del progreso) | NO (ídem) | `AccountStore.create_attempt`, `DirectiveStore.assigned` |
| Ver su propio perfil | SÍ | — | — | `RubricStore.progress`, `ProgressStore.get_progress` |
| Ver perfiles de residentes | SÓLO EL PROPIO | TODOS LOS RESIDENTES DEL PROGRAMA | TODOS | `_actor` + filtro por dueño en cada store |
| Ver evidencia confirmada | LA PROPIA | SÍ | SÍ | `RubricStore.released`, `ProgressStore` |
| Modificar evidencia confirmada | NO | SEMÁNTICA DOCENTE ACTUAL (reabrir, anular con razón, revisión versionada) | ÍDEM, sin borrar historia (§154DI) | `ProgressStore.reopen/void_observation`, `RubricStore.save_review` |
| Revisar un encuentro | NO | SÍ (no los propios) | SÍ (no los propios) | `RubricStore._record`, `FacultyBriefStore` |
| Confirmar la rúbrica | NO | SÍ | SÍ | `RubricStore.save_review` (STAFF) |
| Asignar un Clinical Challenge ciego | NO | SÍ, **con autorización del Admin para ese residente** | SÍ | `DirectiveStore.direct` (Admin o Faculty autorizado) |
| Autorizar a un docente a asignar | NO | NO | SÍ | `DirectiveStore.grant` |
| Ver o descargar el portafolio (documentos individuales y ZIP completo) | EL PROPIO | SÍ, de cualquier residente del programa | SÍ | `portfolio.owner_of` + stores de cada documento (Trace, rúbrica confirmada, registro) |
| Activar o desactivar cuentas | NO | NO | SÍ (tabla de estado ACTIVA/INACTIVA en «Account administration») | `AccountStore.update_user` (admin) |
| Invitar, listar o cambiar rol/año | NO | NO | SÍ | `AccountStore.create_invite/list_users/update_user` |
| Metas de observación del programa | NO | NO (sólo lectura) | SÍ | `ProgressStore.set_target` |
| Generar el AI Longitudinal Review | NO | NO | SÍ (especificado, no implementado) | `docs/AI_LONGITUDINAL_REVIEW_SPEC.md` |
| Ver el AI Longitudinal Review | NO | NO | SÍ, al comienzo | ídem |

**Diferencia con la matriz de la instrucción (§154CA), por la arquitectura:**
«View resident profiles: ASSIGNED/ALLOWED» para Faculty. Hoy Faculty lee a todos
los residentes del programa (piloto de un solo programa). Lo único que exige una
autorización por residente es asignarle un caso. No se amplió ningún permiso.

## Cómo se aplica

- **Cada lectura o escritura vuelve a verificar al llamador en la base,** dentro
  de su propia transacción: sesión vigente, cuenta activa y, cuando corresponde,
  el rol (`AccountStore._actor`). La interfaz es una segunda capa.
- **Desactivar no es borrar (§154AP).** Una cuenta inactiva no puede iniciar
  sesión y sus sesiones se cierran; sus encuentros, Traces, rúbricas, evidencia,
  progreso y revisiones se conservan, y Faculty y Admin siguen leyéndolos.
  Reactivarla devuelve el mismo registro, sin duplicar la cuenta.
- **Un residente inactivo no recibe casos nuevos** (desde el ciclo 9: el store
  rechaza la asignación y el selector no lo ofrece), y aparece como inactivo en
  las listas del docente.
- **La evidencia del residente es de sólo lectura para él** en el store, no sólo
  por controles deshabilitados.

## Pruebas que lo sostienen

- Aislamiento de residentes: `test_resident_owns_their_record.py`,
  `test_rubric_profile_visibility.py`, `test_the_photograph_and_its_agreement.py`,
  `test_management_trace_store.py`, `test_progress_store.py`.
- Sólo lectura del residente: `test_progress_portal.py`, `test_rubric_store.py`,
  `test_faculty_portal.py`, `test_faculty_analysis_store.py`.
- Ceguera del caso asignado: `test_a_resident_s_next_case_chosen_by_faculty.py`.
- Páginas del residente, vistas de evidencia y portafolio (ciclo 9, `test_resident_pages.py`):
  - el inicio anuncia la asignación sin describirla; `DirectiveStore.assigned` sólo
    devuelve la fecha, y sólo la propia;
  - nadie obtiene el portafolio de otro residente nombrándolo (`owner_of` rechaza);
    Faculty sí, y los documentos son los del residente;
  - el portafolio no incluye rúbricas en borrador y no llama al proveedor de IA;
  - «Mis encuentros» no nombra el desafío de un encuentro sin revisión.
- Cohorte docente (`test_faculty_cohort.py`): el residente nunca la ve.
- Gobierno de cuentas (nuevas en el ciclo 9, `test_role_permissions.py`):
  - Faculty es rechazado por el store al invitar, listar, cambiar un rol o un año,
    y desactivar o reactivar;
  - la administración de cuentas no aparece para Faculty;
  - la desactivación conserva la historia y Faculty/Admin la siguen leyendo; la
    reactivación devuelve el mismo registro (§154CE);
  - un residente inactivo no recibe una asignación.

## Riesgos que quedan (ninguno expone datos hoy)

- `DirectiveStore.waiting()` entrega al proceso del residente la razón y el caso
  del docente, porque el lanzamiento los necesita en el servidor. Nada los
  muestra: la pantalla del residente usa `DirectiveStore.assigned()`, que sólo
  devuelve la fecha.
- `ImageBank.exposures(user_id)` y `usage()` no piden token. Sólo se llaman por
  dentro, con el propio identificador.
- Los paneles de revisión del banco de imágenes y de textos en español se
  protegen en la interfaz: muestran personas sintéticas y texto de traducción, no
  datos de residentes.
