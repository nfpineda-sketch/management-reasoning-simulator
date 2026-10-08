# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** lo que requiere una decisión del docente, más el estado de
  lo ya decidido.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-10-07, con la preparación para el despliegue (sección «Preparación para el despliegue», la
  vigente: NOT READY FOR DEPLOYMENT. De los seis bloqueos, B-3, B-4 y B-6 se resolvieron el 2026-10-06 y B-2 el
  2026-10-07, con los datos confirmados en los proveedores; B-1 se resolvió el 2026-10-07 con una
  corrida única 23/23 en Neon, y sigue B-5, bloqueado; X-1 quedó cerrada el 2026-10-07: el piloto corre en inglés y
  en español, sin interfaz mezclada en el candidato final; las 100 decisiones del paquete (niveles 1, 2 y 3) y la redacción de los estados límite de la 49m quedaron tomadas, el español
  que falta para X-1 está redactado y sus decisiones de base, tomadas; el relato y la rúbrica en español se revisan
  antes de congelar el candidato, y el relato aprobado entra en él en `case_text/es/approvals.json`). Antes, con el cierre de la Fase 0 (sección «Cierre de la Fase 0»: F0-1 a F0-12 cerradas). La
  sección «Fase 0 · Seguridad de la medición antes del piloto», con las preguntas tal como se abrieron, sigue debajo. El cierre del paquete prepiloto (2026-10-02,
  D-1 a D-11 decididas y aplicadas), la revisión clínica prepiloto, la segunda y la primera respuesta al paquete
  del ciclo 10, el ciclo 10, el estado posterior a V3, la tabla del cierre del ciclo 9 y los ciclos anteriores
  siguen más abajo, como estaban.

## Preparación para el despliegue (2026-10-06)

Encargo «PRE-DEPLOYMENT READINESS — RESIDENT PILOT». No es la Fase 1 y no reabre la Fase 0. Informe:
`docs/revision/PRE_DEPLOYMENT_READINESS_2026_10_06.md`.

**Resultado: NOT READY FOR DEPLOYMENT.** Candidato del runtime: `009aadb`. Su suite completa (7.578, 0 fallas),
PostgreSQL 16 local con TLS (23 de 23, respaldo y restauración), la prueba de humo automática y el envío seguro con
Streamlit 1.65.0 pasan. No se desplegó ni se empujó nada, y no se aplicó ninguna corrección.

**Actualizado el 2026-10-06** (encargo «resolver sólo B-3, B-4 y B-6»). Lo decidido en el encargo:

- **B-3:** corregir la herramienta (opción b).
- **B-4:** fijar `streamlit==1.64.0`, no 1.65.0, sin fijar otras dependencias.
- **B-6:** actualizar los textos esperados sin debilitarlos.

Los tres quedan resueltos en commits locales, sin push: `87bbbe1`, `4d570a8` y `e200ccc`; el detalle está en la
sección 14 del informe. La conducta del runtime no cambió. **Sigue NOT READY FOR DEPLOYMENT:** faltan B-1, B-2 y
B-5. No se desplegó, no se hizo push y no se empezó la Fase 1.

**Actualizado el 2026-10-07** (encargo «B-2 — define the pilot target deployment environment»): **B-2 BLOCKED.** Está
definido el diseño (informe, sección 15): una rama `pilot-residents-v1` que sólo recibe promociones de un SHA
aprobado, una app nueva de Streamlit Community Cloud con Python 3.11 y una base vacía propia en Neon, además del
contrato de promoción, el chequeo de encuentros abiertos y el plan de B-1. Lo demás está en las cuentas, y desde aquí
no se ve. **Mientras no se sepa qué apps siguen `clinical-encounter-v0.13`, no se hace push a esa rama:** está
documentado que la app de desarrollo se redespliega con cada push. Decisiones y datos que se necesitan de ti:

- **D-B2-1 · App del piloto:** nueva (recomendado) o una existente. Si es nueva, subdominio y workspace; si es
  existente, su URL, rama, archivo principal y Python.
- **D-B2-2 · Base del piloto:** un proyecto de Neon aparte, o una rama del proyecto `management-reasoning-simulator`
  con una base vacía `mrs_pilot`. Nunca `production`.
- **D-B2-3 · Rama:** aprobar el nombre `pilot-residents-v1`, que se crea sólo en la promoción, y decidir si se
  protege en GitHub.
- **D-B2-4 · B-1:** quién crea la rama descartable con una base vacía, en el proyecto de la base del piloto, y quién
  corre la prueba y desde qué equipo.
- **Datos:** las apps del workspace con su rama, archivo principal y Python, y la versión mayor de PostgreSQL del
  proyecto.

**Actualizado otra vez el 2026-10-07: B-2 RESUELTO.** Los datos los confirmaste en las interfaces de los
proveedores (informe, sección 16):

- Streamlit Community Cloud tiene tres apps, una por rama (`ai-integration-v0.9.0`, `clinical-encounter-v0.13` y
  `main`), todas con `app.py`.
- La de desarrollo, `clinical-management-reasoning-dev`, sigue `clinical-encounter-v0.13` y usa Python 3.12; ofrece
  Python 3.11 al crear una app.
- En Neon, el proyecto `management-reasoning-simulator` usa PostgreSQL 17. Sus ramas son `production` (por omisión)
  y dos de desarrollo, archivadas.

Las decisiones de B-2 quedan así:

- **D-B2-1:** una app nueva, `clinical-management-reasoning-pilot` (repositorio, rama `pilot-residents-v1`, `app.py`,
  Python 3.11). La de desarrollo no se toca.
- **D-B2-2:** el mismo proyecto de Neon, con una rama propia, `pilot-residents-v1`.
- **D-B2-3:** el nombre `pilot-residents-v1`; la rama de Git se crea sólo en la promoción. Proteger la rama en GitHub
  queda como recomendación, sin decidir.
- **D-B2-4:** B-1 en `pilot-b1-validation`, con la base `mrs_b1`, temporal y borrada sólo con autorización, sin
  datos de producción.

Sigue pendiente de ti:

- **D-B2-5 · Origen de las ramas de Neon:** «Schema only», sin datos, con una base nueva y vacía (`mrs_b1` para B-1,
  `mrs_pilot` para el piloto). Es lo recomendado: una rama normal desde `production` copiaría sus datos (informe 16.7
  y 16.10). Si la consola no ofrece «Schema only», decides la alternativa.
- **B-1 · READY TO EXECUTE / NOT YET EXECUTED.** Con tu autorización, se crea la rama y la base, y se corre 16.8
  desde un equipo con red directa a Neon. Este entorno no llega.
- **Push:** sigue prohibido sin autorización expresa, porque está confirmado que un push a `clinical-encounter-v0.13`
  redespliega desarrollo.
- **B-5:** BLOCKED.

**Actualizado por tercera vez el 2026-10-07: B-1 BLOCKED (TEST ENVIRONMENT FAILURE).**

- **D-B2-5, confirmada:** la consola de Neon ofrece «Branch schema only» para el proyecto; ese modo copia sólo el
  esquema, sin datos.
- **El intento de correr B-1 desde este entorno no llegó a Neon:**
  - no hay conector de Neon instalado ni credenciales;
  - el proxy rechaza `console.neon.tech` (CONNECT 403);
  - no hay salida TCP a 5432.
- **No se creó ni se tocó nada en el proveedor**, y producción quedó intacta: no hubo ninguna conexión (informe,
  sección 17).
- **Decisión que se necesita:** quién corre B-1 desde un equipo con red directa, como tu Mac (informe 17.4), y sobre
  qué commit:
  - `009aadb`, desde GitHub, con `streamlit==1.64.0`. Tiene el mismo código de persistencia;
  - o `8cc054f` mediante un `git bundle`, sin push.

**Actualizado por cuarta vez el 2026-10-07: B-1 READY TO EXECUTE.**

- **La rama `pilot-b1-validation` se creó a mano**, y la persona responsable la confirmó en la consola:
  - proyecto `management-reasoning-simulator`, con PostgreSQL 17;
  - madre `production`, en modo «Branch schema only»;
  - sin datos de producción;
  - borrado automático al día.
- **Commit, decidido por el encargo:** el candidato real del piloto, con los cambios aprobados antes del despliegue.
  - Es `e200cccc6487af807cab419595baed5b15dd6179`, el último commit de runtime y dependencias.
  - No es `009aadb`.
  - Llega al Mac en un `git bundle`, sin push.
- **Base:** una nueva y vacía, `mrs_b1`, cuyo dueño es el rol con que se conecta.
- **Procedimiento:** en el informe, sección 18, ensayado aquí de punta a punta.
- **Falta:** correrlo en el Mac y traer la evidencia de 18.9.

**Actualizado por quinta vez el 2026-10-07: B-1 STILL BLOCKED** (informe, sección 19).

- **Corrida en Neon:** PostgreSQL 17.11, con TLS y `HOME` vacío. Dio 21 passed y 2 errors.
- **Las dos fallas:**
  - fueron por el límite de 180 s de AppTest al empezar el encuentro;
  - el cuerpo de esas pruebas no corrió;
  - al correrlas solas, las dos pasaron.
- **Causa medida:** sobre una base vacía, ese arranque abre 460 conexiones y sube 15 MB. Con la latencia del Mac,
  tarda unos 170 s.
- **Aceptación vigente (16.8, 18.8 y 16.4):** pide una corrida única con 23 passed y 0 errores.
- **Decisión que se necesita:** autorizar el cambio mínimo del arnés, o correr desde un equipo con menos latencia.
  - El cambio es subir a 300 s el `default_timeout` del fixture de `test_phase0_submission_guard_on_postgres.py`.
  - Es sólo de pruebas y no toca la Fase 0.

**Actualizado por sexta vez el 2026-10-07: B-1 RESUELTO** (informe, sección 20).

- **Corrida única en Neon:** 23 passed en 2208.13 s, sin fallas, errores ni omisiones.
- **Destino:** PostgreSQL 17.11, endpoint *pooled* de `pilot-b1-validation`, TLS, y `TARGET OK` antes y después.
- **SHA probado:** `8ff41a45a6ce60dfc652149b2ef774424304e49a`.
  - Respecto de `e200ccc`, sólo cambia el límite de AppTest en el fixture de PostgreSQL, de 180 s a 300 s, aprobado
    el 2026-10-07.
  - El runtime es el mismo.
- **La rama `pilot-b1-validation`:** sigue siendo descartable y está lista para limpiarse con autorización. No se
  borró.
- **Queda B-5:** las firmas docentes (informe, 20.5).

**Actualizado por séptima vez el 2026-10-07: B-5 · X-1 CERRADA; guías actualizadas para la firma** (detalle en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`).

- **X-1, decisión docente:** el piloto de residentes corre en inglés y en español. De ella sigue:
  - el español entra en el candidato final, y F0-11 es un requisito previo al candidato;
  - todo texto activo de la Fase 0 que ve el residente debe estar en ambos idiomas antes de congelar el
    candidato;
  - los códigos y destinos que lee la máquina son canónicos y no se traducen;
  - todavía no se activa ni se reescribe texto clínico.
- **Hecho, sólo documentación y sin push:**
  - las dos guías, actualizadas con las correcciones H-1 a H-11 e I-1 a I-9 del paquete (H-6 e I-9 siguen
    siendo ciertas y no cambian), **no aprobadas**;
  - la tabla de la brecha bilingüe y el primer lote de diez decisiones de nivel 1.
- **La brecha:**
  - las 21 frases K y los 17 eventos ya se ven en español;
  - las filas 12–18 de R-4 no: el panel del examen las muestra en inglés, y hace falta un cambio de código
    después de su firma;
  - fuera de F0-11, la mayoría de las preguntas de aclaración anteriores a la Fase 0 se ven en inglés o
    mezcladas (TD-79, nueva), y varios rótulos de la sala siguen en inglés (TD-61).
- **Decisiones que se necesitan:**
  - el alcance de X-1 fuera de las frases de la Fase 0: filas 1–11 de R-4, aviso de la foto (J), preguntas de
    aclaración (TD-79) y rótulos (TD-61);
  - las firmas del paquete, empezando por el nivel 1;
  - la firma de las dos guías.
- **B-5: BLOCKED.**

**Actualizado por octava vez el 2026-10-07: B-5 · decisiones docentes del lote 1 de nivel 1 y alcance de X-1.**
Registradas también en el paquete (`docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`). **Ninguna está
implementada.**

- **X-1, cerrada con alcance ampliado (decisión docente):**
  - el piloto es bilingüe;
  - en el candidato final, todo texto que ve el residente durante un encuentro en español es enteramente
    español, salvo los nombres canónicos de fármacos y los códigos que se dejan sin cambiar a propósito;
  - incluye F0-11, las filas 1–18 de R-4, el aviso de la foto, las preguntas de aclaración, el texto de la
    compuerta de razonamiento y los rótulos que ve el residente;
  - no se acepta una interfaz mezclada en inglés y español en el candidato final.

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| A-1 | APPROVE | Nada en el inglés. Su español (borrador) entra con X-1 |
| A-2 | REVISE: la traducción está bien, pero el examen no debe seguir diciendo «increased respiratory effort» cuando el estado es de agotamiento; el examen respiratorio que se muestra debe ser coherente con el estado | Cambio del motor o del examen (TD-51), con su redacción en inglés y en español para firmar antes de implementarlo. **Adelanta TD-51**, que D-9 (2026-10-02) había dejado para después del piloto: ahora va antes del candidato final |
| A-9 | REVISE: se mantiene el español; el inglés pasa a «Respiratory rate {n}/min, provided by the assisted ventilation currently in progress.» | Cambio del texto inglés en el código (TD-52 a) |
| B-19 a B-25 | APPROVE | Nada: activas en inglés y en español |

- **Lo que X-1 agrega al trabajo antes del candidato final** (todo es código, salvo la redacción, y por lo tanto
  un SHA nuevo, con el contrato de promoción 16.4: suite, regresiones y B-1):
  - el panel del examen debe mostrar el español aprobado de las filas 1–18 de R-4;
  - las filas 2–8, 10 y 11 de R-4 todavía esperan la firma de su español (nivel 2), y la fila 64 (aviso de la
    foto, J), la suya;
  - las preguntas de aclaración (TD-79), el texto de la compuerta y los rótulos (TD-61) no tienen español
    redactado: hay que redactarlo y firmarlo (TD-46: sin traducción automática) antes de implementarlo;
  - los modos Talk, Examine, Tests y Treat son rótulos que ve el residente: entran.
- **Consecuencias que conviene decidir:**
  - el relato en español de cada caso se aprueba en el tablero después del despliegue (paquete, sección 4); con
    X-1, un relato sin aprobar mostraría inglés en un encuentro en español. Corregir una traducción del relato
    es un cambio del repositorio (nuevo SHA). Falta decidir si se revisa antes de congelar el candidato o antes
    del GO, como dice la sección 4;
  - al implementar, las guías cambian: H-6 e I-9 (aviso de la foto), H-10, I-2, el punto «Idioma (X-1)», la
    limitación TD-51 de la guía docente y la mención de los modos en inglés en la guía del residente.
- **B-5: BLOCKED.** Quedan 89 de las 100 decisiones: 45 de nivel 1, 43 de nivel 2 y 1 de nivel 3 (J).

**Actualizado por novena vez el 2026-10-07: B-5 · lote 2 de nivel 1, relato en español y borrador del español de
X-1.** Registradas también en el paquete. **Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| B-26, C-37, D-39, D-40, D-41, D-43, E-45, E-46, F-47 | APPROVE | Nada en el código ni en el banco: siguen activos como están |
| D-42 | REVISE: se mantienen el sentido del inglés y el comportamiento del motor. El español de D-42 debe decir, para las dos neumonías, que el POCUS de control muestra la VCI que se llena con el volumen, que no muestra líneas B nuevas por la sobrecarga de cristaloides y que la saturación sí cae; no sirve el párrafo de la guía que junta el trauma y la neumonía | Firmar el español propuesto en el paquete (bloque D-42) y llevarlo a la guía docente: sólo documentación (S-C) |

- **El relato en español (decisión docente):**
  - se revisa después del despliegue y antes del GO del piloto;
  - no necesita estar en el SHA precandidato en lo que es contenido de la base (la aprobación de cada caso);
  - el piloto bilingüe no abre hasta completar esa revisión;
  - el texto del relato está en el repositorio (`case_text/es/`): corregir una traducción es un SHA nuevo y otro
    despliegue (paquete, 4.3).

  Responde la consecuencia que la octava actualización dejaba por decidir. **Reemplazado en la décima
  actualización:** el relato se revisa antes de congelar el candidato final.
- **El español que falta para X-1 (decisión docente):** autorizado para redactarse y revisarse, no para
  implementarse. Borrador: `docs/revision/X1_ESPANOL_PROPUESTO.md`:
  - 100 formulaciones únicas y 7 vocabularios, cada una con las fuentes que cubre;
  - las preguntas de aclaración van en 34 plantillas para las 73 frases que un residente del piloto puede ver;
  - 11 textos ya tienen español y sólo falta aplicarlo;
  - la redacción de A-2 con el paciente agotado, en inglés y en español (§9);
  - fuera del alcance, con su evidencia: el relato, 40 preguntas del motor heredado que ningún caso del piloto
    alcanza, las herramientas del personal y la ruta sin cuentas.
- **Hallazgo del inventario:** las 40 preguntas de `app.py` que TD-79 contaba entre las pendientes son del motor
  heredado. Los 31 casos del banco usan el motor por familias, que vuelve antes de llegar a ellas. TD-79 queda
  acotada a las del motor por familias.
- **Siguiente lote de nivel 1:** F-48 a F-57, las fichas POCUS de 61m, 70f, 57m, 72f, 58f, 46f, 83m, 58m, 75f y
  33f.
- **B-5: BLOCKED.** Quedan 79 de las 100 decisiones: 35 de nivel 1, 43 de nivel 2 y 1 de nivel 3 (J). Aparte,
  las 103 decisiones del borrador de X-1, que no estaban entre las 100.

**Actualizado por décima vez el 2026-10-07: B-5 · lote 3 de nivel 1, decisiones de base de X-1, A-2, calendario
del relato y claves internas.** Registradas también en el paquete y en `docs/revision/X1_ESPANOL_PROPUESTO.md`.
**Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| F-48, F-50, F-51, F-52, F-55, F-56 y F-57 | APPROVE | Nada: las fichas y sus declaraciones C14 siguen como están |
| F-49 | APPROVE. El límite aprobado en D-41 y E-46 es vinculante: no se exige detectar la sobrecarga por examen ni por POCUS cuando el motor no la modela; la adaptación se juzga con las señales que el simulador entrega | Nada en el banco: es la regla de la revisión docente |
| F-53 y F-54 | APPROVE, vinculadas a D-42: la respuesta al volumen se juzga con la VCI y la saturación; nunca se exigen líneas B nuevas, que el simulador no modela | Ídem |
| J | APPROVE, en «tú»: «Una fotografía fija no muestra todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.» | Mostrarlo en español (X-1) |
| D-42, español | APPROVE de la traducción propia | Llevarla a la guía docente (sólo documentación) |
| A-2 | Sigue en REVISE, con redacción final docente: EN «Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with exhaustion.»; ES «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz, compatible con agotamiento.» Con el criterio del motor ya propuesto | Cambio del motor y de su español (TD-51) |
| X1-0 | APPROVE, con una aclaración: en un encuentro en español, los fármacos que el motor inserta en un texto que ve el residente también se muestran con su nombre en español; el identificador canónico puede seguir en inglés. Así queda la convención de K-13, sin cambiar su valor guardado | Redactar V-9 (los nombres en español); al implementarse cambian K-13, K-14 y, con un fármaco, K-5 y K-6 |
| I-10 | APPROVE: el resumen de la orden retenida reusa las etiquetas del registro; V-8 no se construye salvo que aparezca una acción sin etiqueta | Implementación |
| L-01 | APPROVE: Conversar · Examinar · Exámenes · Tratar | Implementación y guía del residente |
| V-4 | APPROVE: Respiración y Pulmonar, regiones distintas | Implementación |
| M-02 | APPROVE: Urgencias / Cama 03 | Implementación |
| Claves internas | Antes del candidato final se limpian las claves internas que ve el residente (por ejemplo, `beta_blocker` → beta blocker / betabloqueador; `ORDER_CANCELLED` → ORDER CANCELLED / ORDEN CANCELADA). Sólo presentación: las claves canónicas no cambian | TD-80. L-17 queda decidida así |
| Relato en español | **Reemplaza la decisión de la novena actualización.** Se revisa el de los 30 casos antes de congelar el candidato final, y el candidato bilingüe no se congela sin esa revisión. Motivo: el texto vive en el repositorio, y corregirlo después del despliegue daría un SHA nuevo y otro despliegue | Revisión docente antes del congelamiento; falta decidir cómo llega la aprobación al piloto (abajo) |

- **Cuentas:**
  - paquete: 32 de las 100 decididas; quedan 68 (25 de nivel 1 y 43 de nivel 2);
  - borrador de X-1: 7 de 105 decididas, quedan 98. Eran 103: V-4 se decidió aparte de los demás vocabularios, y la
    aclaración de X1-0 agrega V-9.
- **Contradicciones y huecos que crean estas decisiones:**
  1. **Cómo llega al piloto la aprobación del relato.** La sala muestra el relato en español de un caso sólo si su
     versión exacta está aprobada en la base del despliegue o en `case_text/es/approvals.json`, que el código ya
     lee (`case_text.pack_approvals`) y hoy no existe. Revisar antes del congelamiento no basta: sin una de las dos,
     el piloto bilingüe mostraría el relato en inglés. Hay dos caminos:
     - (a) exportar las aprobaciones a ese archivo dentro del candidato. No hay herramienta de exportación, y el
       archivo no debe llevar nombres de médicos (CLAUDE.md);
     - (b) volver a registrar las mismas aprobaciones en el tablero de la base del piloto después del despliegue,
       sin cambiar el SHA, como paso mecánico antes del GO.

     La revisión misma se hace en un entorno que no sea el del piloto: la app de desarrollo o una local.
  2. **La rúbrica en español (4.2) tiene la misma propiedad** (`rubric_text/es/`, en el repositorio, con su propio
     `approvals.json`) y la decisión no la nombra: corregirla después del despliegue también da un SHA nuevo.
  3. **Las guías (H-62 e I-63) ya no describen el candidato final:**
     - dicen que las preguntas, el aviso de la orden retenida, el aviso de la foto y algunos rótulos se ven en
       inglés, y nombran los modos en inglés;
     - dicen que el relato puede verse en inglés;
     - citan TD-51 como diferida;
     - juntan el trauma y la neumonía en el párrafo de TD-54 que D-42 reemplaza.

     Firmarlas ahora sería firmar un texto que dejará de ser cierto.
  4. **La hoja F0-11** (`docs/revision/F0_11_FRASES_ES.md`, tercera regla) dice que los nombres de fármacos son
     iguales en ambos idiomas; la aclaración de X1-0 la reemplaza. Quedó anotado con fecha en la hoja. Las frases
     activas (K-13 y K-14) siguen en inglés hasta implementar.
  5. **Alcance de la aclaración de X1-0 fuera del encuentro:** los documentos en español que el residente
     descarga nombran hoy los fármacos en inglés. Si la decisión los incluye, el cambio es mayor.

  **Resueltas en la undécima actualización:** la 1, la 2, la 3 y la 5. La 4 sigue anotada en la hoja F0-11 hasta
  implementar X1-0.
- **Siguiente lote de nivel 1:** F-58, F-60, G-61, H-62, I-63, K-1 y K-2 (una decisión), K-3, K-4, K-5 y K-6.
- **B-5: BLOCKED.**

**Actualizado por undécima vez el 2026-10-07: B-5 · lote 4 de nivel 1 y decisiones sobre el relato, la rúbrica, las
guías y los documentos en español.** Registradas también en el paquete y en `docs/revision/X1_ESPANOL_PROPUESTO.md`.
**Ninguna está implementada, y `case_text/es/approvals.json` no se creó.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| F-58, F-60 y G-61 | APPROVE | Nada: las fichas, sus declaraciones C14 y la tabla TDFC siguen como están |
| K-1 y K-2 (una decisión), K-3 y K-4 | APPROVE | Nada: las frases están activas en los dos idiomas |
| K-5 y K-6 | APPROVE. Cuando la orden insertada contiene un fármaco reconocido, rige X1-0: en un encuentro en español, el residente lo lee con su nombre en español, y el valor canónico guardado no cambia | Implementación, con V-9 |
| H-62 e I-63 | DEFER de la firma. No es un rechazo: las guías todavía no se pueden firmar. Deben describir el candidato final real, después de implementar X-1, los cambios de A-2 y A-9, la redacción final de D-42, la limpieza de la interfaz bilingüe y la revisión y activación del relato y de la rúbrica en español | Actualizarlas (sólo documentación) cuando todo eso esté hecho, y volver a firma |
| L-17 | Confirmada: EN ORDER CANCELLED, ES ORDEN CANCELADA; la clave canónica no cambia | Implementación (TD-80) |
| M-02 | Confirmada para el renglón entero: «Urgencias / Cama 03», «Imagen del paciente · estado actual», «Actualizando la apariencia del paciente» e «Imagen actual del paciente no disponible» | Implementación |
| X1-0 en los documentos | Alcanza también a los documentos que se ofrecen expresamente en español al residente: los fármacos visibles llevan su nombre en español, y los identificadores canónicos no cambian. No exige traducir lo que se guarda en inglés por diseño, como el ledger o el Trace canónico | Al implementar, la lista de esos documentos y su prueba (TD-80) |
| Relato en español: cómo llega al piloto | **Camino (a).** Terminada la revisión docente de los 30 casos, las versiones aprobadas entran en el candidato final en `case_text/es/approvals.json`. Requisitos: en el repositorio y determinista; comprobable antes del congelamiento; sin nombres de médicos ni de revisores, sin identificadores personales y sin metadatos de revisión innecesarios; sólo lo que ata la aprobación al caso, la versión y el texto exactos. El archivo no se crea todavía: primero se completa la revisión. Así se evita volver a registrar las aprobaciones a mano después del despliegue (el camino b queda descartado) | La exportación y su prueba (TD-81) |
| Rúbrica en español (D1–D5) | **REVIEW BEFORE FINAL CANDIDATE FREEZE.** Vive en el repositorio: la docencia la revisa, y su español para residentes y docentes queda listo antes de congelar el SHA final del despliegue. No se difiere a después del despliegue | Identificar, antes de implementarla, el mecanismo exacto con que se activa en el candidato, comprobable de forma determinista (TD-81) |

- **Lo que ya hace el código para el relato** (comprobado el 2026-10-07, sin cambiarlo):
  - `case_text.pack_approvals` lee `case_text/es/approvals.json` y toma sus filas con `"decision": "approved"`;
  - `case_text.status` ata cada fila a su caso por `variant_id` y al texto exacto por `version`, el SHA-256 de
    todos los pasajes del caso en los dos idiomas;
  - para el lector actual basta una fila `{"variant_id", "version", "decision"}`, y ningún otro campo se usa;
  - una revisión registrada después en la base del piloto, sobre la misma versión, prevalece sobre el archivo.

  Para la rúbrica, `rubric_text.py` tiene la misma forma (`domain_id` y `version`, y su propio
  `rubric_text/es/approvals.json`, que tampoco existe). Es un dato, no la decisión del mecanismo.
- **Cuentas:**
  - paquete: 42 de las 100 decididas; quedan 58 (15 de nivel 1, K-7 a K-21, y 43 de nivel 2). H-62 e I-63 tienen
    decisión (DEFER) pero no firma: las firmas abiertas son 60;
  - borrador de X-1: 7 de 105 decididas, quedan 98. L-17 y M-02 se confirmaron sin cambiar la cuenta, y el alcance
    de X1-0 en los documentos no agrega decisiones.
- **Contradicciones de la décima actualización:** la 1 (camino del relato), la 2 (rúbrica), la 3 (guías) y la 5
  (documentos) quedan resueltas por estas decisiones. La 4 (regla 3 de la hoja F0-11) sigue anotada en la hoja
  hasta implementar X1-0: K-13 y K-14 todavía muestran los fármacos en inglés.
- **Abierto, sin contradicción:**
  - el mecanismo de activación de la rúbrica;
  - dónde se hace la revisión previa (la app de desarrollo o una local) y cómo se exporta sin la cuenta de quien
    revisa;
  - la lista exacta de los documentos que se ofrecen en español (al implementar).
- **Siguiente lote de nivel 1:** K-7 a K-16.
- **B-5: BLOCKED.**

**Actualizado por duodécima vez el 2026-10-07: B-5 · lote 5 de nivel 1 (K-7 a K-16).** Registradas también en el
paquete, en la hoja F0-11 (`docs/revision/F0_11_FRASES_ES.md`) y en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`.
**Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| K-7, K-8, K-10, K-11, K-12 y K-15 | APPROVE | Nada: las frases están activas en los dos idiomas |
| K-9 | APPROVE. La mayúscula tras «sin pulso:» es cosmética y no pide revisión | Nada |
| K-13 y K-14 | APPROVE con X1-0: en un encuentro en español, los fármacos reconocidos que ve el residente llevan su nombre en español; el valor canónico guardado no cambia | Implementación, con V-9 (como K-5 y K-6) |
| K-16 | APPROVE. Se conserva la semántica de F0-12: una orden escrita después de responder la aclaración se procesa como orden propia, con su propio destino y su propio recibo. La guía del residente puede explicar «recibo» cuando se actualicen H-62 e I-63; eso no bloquea la aprobación | Nada en el código |

- **Cuentas:**
  - paquete: 52 de las 100 decididas; quedan 48 (5 de nivel 1, K-17 a K-21, y 43 de nivel 2). Con H-62 e I-63,
    que tienen decisión pero no firma, las firmas abiertas son 50;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Contradicciones que crean estas decisiones:** ninguna.
  - K-15 sigue siendo la excepción de TD-70 (a): si la respuesta deja algo retenido, la otra orden no corre. K-16
    describe el caso en que la respuesta completa la orden retenida. Las dos son F0-12.
  - La divergencia ya anotada de la regla 3 de la hoja F0-11 sigue igual: K-5, K-6, K-13 y K-14 están aprobadas con
    X1-0, pero K-13 y K-14 muestran todavía los fármacos en inglés hasta implementar.
  - Dato corregido: la guía del residente actualizada (sin firmar) ya explica «recibo» (I-6) y el caso de K-16
    (I-3). El paquete y el documento B5 decían que no lo explicaba; quedó anotado.
- **Hallazgo para el lote final (K-18):**
  - la traducción es fiel, pero el inglés describe un curso que no siempre ocurrió;
  - en `anaphylaxis_63m_betablocked`, con una sola dosis de adrenalina y espera, la reacción nunca mejora y el paro
    (minuto 71) dice que el efecto «se agotó» y que la reacción «había vuelto». Comprobado en la sala real
    (`pilot_acceptance`), sin cambiar código; en `anaphylaxis_29f` la frase es exacta;
  - recomendación: REVISE con una frase cierta en los dos cursos (paquete, K-18). Registrado como TD-82.
- **Siguiente lote de nivel 1, el último:** K-17 a K-21.
- **B-5: BLOCKED.**

**Actualizado por decimotercera vez el 2026-10-07: B-5 · lote final de nivel 1 (K-17 a K-21) y nivel 1 completo;
primer lote de nivel 2 preparado.** Registradas también en el paquete, en la hoja F0-11 y en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`. **Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| K-17, K-19, K-20 y K-21 | APPROVE | Nada: activas en los dos idiomas |
| K-18 | REVISE. EN «Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier did not keep the reaction under control. Nothing else that was given acts on the reaction.» · ES «Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.» Motivo: es cierta cuando la adrenalina ayudó y después perdió su efecto, y cuando la dosis previa nunca controló bien la reacción, también en el caso con betabloqueo | Corrección de texto antes del candidato final: la frase del motor y su español, con sus pruebas (TD-82). No se implementa todavía |

- **Nivel 1 completo:** las 55 decisiones de nivel 1 están tomadas. H-62 e I-63 siguen sin firma a propósito,
  hasta que exista el candidato final implementado. No es un rechazo y no reabre el nivel 1.
- **Cuentas:**
  - paquete: 57 de las 100 decididas; quedan 43, todas de nivel 2. Con H-62 e I-63, las firmas abiertas son 45;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Primer lote de nivel 2, propuesto:** A-3 a A-8 y A-10 a A-13, las frases del motor de R-4 (el examen
  respiratorio y la vía de la hipoglicemia). Ninguna es idéntica a otra, así que no se agrupan; A-5, A-6 y A-8 se
  marcan VINCULADAS. Comprobado el 2026-10-07: su inglés y su español coinciden con el motor, los borradores y la
  hoja R-4.
- **Hallazgo del lote (A-6, TD-83):**
  - en `asthma_49m`, la llegada describe un tórax casi silente («very poor bilateral air entry and only faint
    wheeze»);
  - desde la primera orden, aun con oxígeno solo, el examen muestra A-6 («Reduced bilateral air entry with
    prolonged expiration and wheeze»), sin cambio fisiológico. Comprobado con el motor, sin cambiar código;
  - recomendación: REVIEW CLOSELY, con dos opciones (paquete, A-6).
- **Precisión (A-4):** la frase de la sobrecarga por transfusión aparece en todas las familias salvo asma, edema
  pulmonar y opioides, cuya línea respiratoria la reemplaza.
- **B-5: BLOCKED.**

**Actualizado por decimocuarta vez el 2026-10-07: B-5 · primer lote de nivel 2 (A-3 a A-8, A-10 a A-13).**
Registradas también en el paquete y en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`. **Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| A-3, A-4, A-5, A-7, A-8, A-12 y A-13 | APPROVE | Nada en el inglés; su español se muestra con X-1 |
| A-10 y A-11 | APPROVE | Con X-1. Normalización cosmética: al implementar A-9, A-10 y A-11, la frecuencia se escribe «{n}/min». No es otra decisión |
| A-6 | REVISE. En `asthma_49m`, conservar el examen respiratorio grave de llegada («very poor bilateral air entry and only faint wheeze») mientras la obstrucción no haya mejorado. Una orden que no mejora la obstrucción, tampoco el oxígeno solo, no puede hacer que el examen parezca menos grave. La frase no cambia por la sola ejecución de una orden; A-6 aparece sólo cuando describe el estado actual del motor; A-5 sigue siendo la mejoría real tras la respuesta al broncodilatador. Es redacción coherente con el estado, no un cambio de la trayectoria clínica ni de la respuesta al tratamiento | Cambio del motor antes del candidato final (TD-83), abajo |

- **Consecuencia para implementar A-6 (no autorizada todavía):**
  1. En `asthma_49m`, mientras la obstrucción del motor siga en su nivel de llegada, el examen respiratorio
     conserva la línea de llegada del caso («Severe effort with very poor bilateral air entry and only faint
     wheeze…»; en español, la del relato del caso).
  2. La frase cambia sólo cuando cambia el estado del motor, nunca por la sola ejecución de una orden.
  3. A-6 aparece sólo cuando describe el estado actual; A-5, sólo con la mejoría real tras el broncodilatador.
  4. No cambian la trayectoria, la respuesta al tratamiento, los signos vitales ni los eventos: sólo la redacción
     del examen.
  5. Lugar: `family_engine.current_findings`, rama del asma (`family_engine.py:3227–3229`).
  6. Pruebas:
     - la 49m con oxígeno solo conserva la línea de llegada;
     - con broncodilatadores pasa a A-5;
     - los valores del motor son idénticos antes y después del cambio.
  7. Es un cambio del motor: SHA nuevo y contrato 16.4.
- **Por resolver al implementar A-6, con aprobación docente de cualquier texto nuevo:**
  - si la 49m se intuba sin que la obstrucción mejore (comprobado con el motor: con etomidato y rocuronio, la
    obstrucción no baja), la línea de llegada habla de esfuerzo y de flujo espiratorio máximo, que ya no
    describen a un paciente intubado. Hay que conservar la gravedad (entrada de aire muy pobre, sibilancias apenas
    audibles) sin esas partes;
  - A-8 compone su segunda parte con el examen respiratorio vigente. En la 49m sin mejoría, esa parte no puede ser
    la línea de llegada entera.
- **Cuentas:**
  - paquete: 67 de las 100 decididas; quedan 33, todas de nivel 2. Con H-62 e I-63, las firmas abiertas son 35;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Siguiente lote de nivel 2:** A-14 a A-18 y C-27 a C-31.
- **B-5: BLOCKED.**

**Actualizado por decimoquinta vez el 2026-10-07: B-5 · segundo lote de nivel 2 (A-14 a A-18, C-27 a C-31) y
redacción propuesta para los estados límite de A-6 y A-8.** Registradas también en el paquete y en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`. **Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| A-14, A-15, A-16, A-17 y A-18 | APPROVE | Su español se muestra con X-1 |
| C-27, C-28, C-29 y C-30 | APPROVE (el inglés) | Su español llega con el relato de cada caso (paquete, 4.1) |
| C-31 | APPROVE: una sola decisión para `renal_colic_34m` y `bradycardia_bb_54f` | Ídem |
| Lector | Las dos formas de pedir una segunda vía que el lector no lee no cambian A-15 y quedan sólo en TD-45. El lector congelado no se toca | Nada en esta tarea |
| A-6 | Sigue en REVISE. Antes de implementarla, redactar en inglés y en español, para la firma docente, los estados límite: la 49m con respiración espontánea y con tubo, y A-8 tras la descompresión | Redacción propuesta, abajo y en el paquete (bloque A) |

- **Redacción propuesta para la firma (paquete, bloque A, «A-6 y A-8 · Estados límite»):**
  - **A-6a** · 49m con respiración espontánea, obstrucción sin mejorar: la línea de llegada del caso, sin cambio.
    EN «Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable
    peak-flow maneuver.» · ES, la del relato: «Esfuerzo respiratorio severo, con murmullo pulmonar muy disminuido en
    forma bilateral y solo sibilancias tenues. No logra completar una maniobra confiable de flujo espiratorio
    máximo.»
  - **A-6b** · 49m intubado, obstrucción sin mejorar: EN «Endotracheal tube in place: air entry remains very poor
    bilaterally, with only faint wheeze.» · ES «Tubo endotraqueal instalado: el murmullo pulmonar sigue muy
    disminuido en forma bilateral, con solo sibilancias tenues.»
  - **A-8a** · 49m tras la descompresión, obstrucción grave sin mejorar: EN «Breath sounds returning on the right
    after decompression; air entry remains very poor bilaterally, with only faint wheeze.» · ES «Reaparece el
    murmullo pulmonar en el hemitórax derecho tras la descompresión; sigue muy disminuido en forma bilateral, con
    solo sibilancias tenues.»
  - A-8 con mejoría real tras el broncodilatador no necesita otra línea: es el texto de A-8 ya aprobado. El motor
    elige la segunda parte por el estado de la obstrucción y nunca agrega «improved» si no mejoró. Con la
    obstrucción en el nivel de A-6, queda la variante ya aprobada con A-8. La 24f no necesita texto nuevo.
- **Cuentas:**
  - paquete: 77 de las 100 decididas; quedan 23, todas de nivel 2. Con H-62 e I-63, las firmas abiertas son 25.
    Aparte, 3 redacciones de A-6 y A-8 esperan su firma;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Siguiente lote de nivel 2:** C-32, C-33, C-35, C-36, C-38, C-EFAST y K-E1 a K-E4.
- **B-5: BLOCKED.**

**Actualizado por decimosexta vez el 2026-10-07: B-5 · tercer lote de nivel 2 (C-32, C-33, C-35, C-36, C-38,
C-EFAST, K-E1 a K-E4) y redacción aprobada de los estados límite de la 49m (A-6a, A-6b, A-7-49m, A-8a).**
Registradas también en el paquete y en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`. **Ninguna está
implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| C-32, C-33, C-35 y C-36 | APPROVE (el inglés) | Su español llega con el relato de cada caso (paquete, 4.1) |
| C-38 y C-EFAST | APPROVE | Nada: ya activos en inglés y en español |
| K-E1, K-E2, K-E3 y K-E4 | APPROVE | Nada: ya activos en inglés y en español (hoja F0-11) |
| A-6a | APPROVE. EN «Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver.» · ES «Esfuerzo respiratorio severo, con murmullo pulmonar muy disminuido en forma bilateral y solo sibilancias tenues. No logra completar una maniobra confiable de flujo espiratorio máximo.» Mientras siga la respiración espontánea y la obstrucción no haya mejorado desde la llegada; la ventilación no invasiva cuenta como respiración espontánea | Implementar A-6 (TD-83). Su español es el del relato del caso |
| A-6b | APPROVE. EN «Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze.» · ES «Tubo endotraqueal instalado: el murmullo pulmonar sigue muy disminuido en forma bilateral, con solo sibilancias tenues.» Con ventilación invasiva y la obstrucción todavía en el estado grave de llegada | Ídem. Frase nueva del motor, con su español |
| A-8a | APPROVE. EN «Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, with only faint wheeze.» · ES «Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; sigue muy disminuido en forma bilateral, con solo sibilancias tenues.» Tras una descompresión eficaz, mientras la obstrucción grave no haya mejorado. Con mejoría real tras el broncodilatador sigue el texto de A-8 ya aprobado | Ídem |
| A-7 | Se reabre sólo para `asthma_49m` con la obstrucción todavía en el estado grave de llegada: es una revisión acotada de A-7, no una trayectoria clínica nueva. A-7 aprobada sigue en `asthma_24f`. Variante A-7-49m, redacción docente aprobada: EN «Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left remains very poor, with only faint wheeze.» · ES «Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; en el lado izquierdo el murmullo pulmonar sigue muy disminuido, con solo sibilancias tenues.» No cambia el momento del neumotórax, la fisiología de la obstrucción, la respuesta al broncodilatador ni a la descompresión, los signos vitales ni los eventos críticos: es sólo coherencia del examen con el estado | Ídem (TD-83) |

- **Consecuencia para implementar A-6 con estas redacciones (no autorizada todavía).** Completa la de la
  decimocuarta actualización:
  1. En la rama del asma de `family_engine.current_findings`, la 49m elige su examen respiratorio con dos datos
     del estado actual: cómo respira (espontánea, que incluye la ventilación no invasiva, o con ventilación
     invasiva) y si el índice de obstrucción bajó de su valor de llegada.
  2. Sin mejoría: A-6a, A-6b, A-7-49m o A-8a, según el momento. Con mejoría: las frases ya aprobadas (A-5, A-6, A-7
     y A-8). Cada condición se lee en cada examen, sobre el estado de ese momento, como la segunda parte de A-8.
  3. No cambian la trayectoria, la respuesta al tratamiento, el momento del neumotórax, los signos vitales ni los
     eventos: sólo la redacción del examen.
  4. Comprobado con el motor, sin cambiar código:
     - el neumotórax del asma ocurre sólo con ventilación invasiva y siempre a la derecha, así que A-7-49m y A-8a
       son siempre de la 49m intubada;
     - intubada con etomidato y rocuronio, el índice no baja de su valor de llegada (1,01 a los dos minutos):
       rige A-6b;
     - intubada con ketamina, el índice sí baja (0,81 a los dos minutos, con 150 mg indicados), porque el motor
       modela su efecto broncodilatador: es una mejoría parcial y rige A-6, ya aprobada.
  5. Pruebas:
     - la 49m con oxígeno solo conserva A-6a;
     - intubada sin mejoría, A-6b;
     - con el neumotórax sin descomprimir, A-7-49m; tras descomprimir, A-8a;
     - con broncodilatadores, A-5 y A-8 ya aprobadas;
     - la 24f, sin cambio;
     - los valores del motor, idénticos antes y después del cambio.
  6. Es un cambio del motor: SHA nuevo y contrato 16.4. El español de A-6b, A-7-49m y A-8a entra con la
     implementación, por el mismo camino que las demás frases del motor (X-1). El de A-6a es el del relato y se ve
     cuando se aprueba el relato de la 49m (4.1).
- **Cuentas:**
  - paquete: 87 de las 100 decididas; quedan 13, todas de nivel 2 (K-E5 a K-E17). Con H-62 e I-63, las firmas
    abiertas son 15. Las 4 redacciones de los estados límite quedaron aprobadas; no suman a las 100;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Hallazgo al preparar el lote siguiente, sin decidir (TD-82):** K-E5, la etiqueta del paro de la anafilaxia en
  la espera interrumpida, dice «circulatory arrest from untreated anaphylaxis» también cuando ya se dio adrenalina.
  Comprobado en la sala real, sin cambiar código: en la 63m con betabloqueo y una dosis IM, la misma entrada trae
  K-18 («…without effective adrenaline…») y esa etiqueta. Es el defecto que llevó a revisar K-18. Recomendación:
  NEEDS REVISION, con una propuesta cierta en los dos cursos (paquete, K-E5).
- **Siguiente lote de nivel 2:** K-E5 a K-E14; después, K-E15 a K-E17.
- **B-5: BLOCKED.**

**Actualizado por decimoséptima vez el 2026-10-07: B-5 · cuarto lote de nivel 2 (K-E5 a K-E14) y aclaración
de A-6 y A-6b.** Registradas también en el paquete, en la hoja F0-11 y en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`. **Ninguna está implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| K-E5 | REVISE. EN «circulatory arrest from anaphylaxis without effective adrenaline» · ES «paro circulatorio por anafilaxia sin adrenalina eficaz». La etiqueta del evento debe ser cierta tanto si no se dio adrenalina como si se dio y no logró un control eficaz. «Untreated anaphylaxis» no se usa como etiqueta general: es falsa cuando ya se administró adrenalina. K-21 sigue siendo la frase de la anafilaxia realmente no tratada | Cambiar la etiqueta del evento (`event_provenance.FLAG_EVENTS["arrested"]`), su regla en español (`language.py`, `_PHASE0_RULES`) y sus pruebas, antes del candidato final (TD-82) |
| K-E6 | REVISE. EN «circulatory arrest from profound bradycardia» · ES «paro circulatorio por bradicardia profunda». Más clara y clínicamente natural que «loss of circulation from the falling rate» · «pérdida de la circulación por la frecuencia que cae». Es el mismo evento terminal del motor: no cambian su disparador, su prevenibilidad ni su fisiología | Ídem para `FLAG_EVENTS["bradycardia_arrest"]` (TD-67) |
| K-E7 a K-E14 | APPROVE | Nada: ya activos en inglés y en español (hoja F0-11) |
| A-6 y A-6b | La elección es por estado. La intubación sola no fuerza A-6b. Si la ketamina produce una reducción real de la obstrucción del motor, rige el examen de ese estado mejorado; con ventilación invasiva y la obstrucción en el estado grave de llegada, A-6b. El examen refleja el estado actual del motor, no el fármaco de inducción | Ya era la consecuencia de la decimosexta actualización. No cambian la fisiología de la ketamina ni la respuesta al tratamiento (TD-83) |

- **Cuentas:**
  - paquete: 97 de las 100 decididas; quedan 3, las últimas de nivel 2 (K-E15 a K-E17). Con H-62 e I-63, las
    firmas abiertas son 5;
  - borrador de X-1: 7 de 105 decididas, quedan 98 (sin cambio).
- **Lote final de nivel 2:** K-E15, K-E16 y K-E17 (`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, 3.11).
- **B-5: BLOCKED.**

**Actualizado por decimoctava vez el 2026-10-07: B-5 · lote final de nivel 2 (K-E15 a K-E17), las 100
decididas, y X-1 consolidada en lotes.** Registradas también en el paquete, en la hoja F0-11, en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md` y en `docs/revision/X1_ESPANOL_PROPUESTO.md` (§12). **Ninguna está
implementada.**

| ID | Decisión docente (2026-10-07) | Qué exige, sin implementar todavía |
|---|---|---|
| K-E15 y K-E17 | APPROVE | Nada: ya activos en inglés y en español |
| K-E16 | APPROVE. La diferencia del inglés «84 %» / «84%» es cosmética: al implementar se normaliza la presentación de forma coherente, sin otra decisión docente; no cambian el disparador ni el sentido del evento | La normalización, al implementar |

- **Las 100 decisiones originales:** todas decididas; los niveles 1, 2 y 3, completos.
  - 91 APPROVE; A-7, con la revisión acotada para la 49m (A-7-49m).
  - 7 REVISE: A-2, A-9, D-42, K-18, A-6, K-E5 y K-E6.
  - 2 DEFER de la firma: H-62 e I-63.
- **Firmas abiertas:** H-62 e I-63, a propósito, hasta que exista el candidato final implementado, porque las guías
  deben describirlo.
- **B-5 no está resuelto (BLOCKED).** Falta:
  - decidir el español de X-1;
  - revisar el relato y la rúbrica en español;
  - implementar lo decidido y verificar el candidato final;
  - firmar H-62 e I-63 sobre ese candidato.
- **X-1, siguiente frente (encargo docente del 2026-10-07):**
  - las 98 decisiones pendientes quedan consolidadas en 28 (XR-01 a XR-28), en 2 lotes de 14, sin juntar
    significados clínicos distintos (X-1, §12);
  - V-9, los nombres de fármacos para mostrar, queda redactada para el primer lote;
  - al preparar el lote se comprobó, sin cambiar código, que X1-C01 nombra la clase aunque el residente haya nombrado
    el fármaco (TD-80).
- **Cuentas:** paquete, 100 de 100. X-1, 7 de 105; las 98 restantes, en 28 decisiones consolidadas.
- **Siguiente lote:** X-1, lote 1 (XR-01 a XR-14).
- **B-5: BLOCKED.**

**Actualizado por decimonovena vez el 2026-10-07: B-5 · lote 1 de X-1 (XR-01 a XR-14).** Registrado también en
`docs/revision/X1_ESPANOL_PROPUESTO.md` (§12.2, con el texto final en cada fila), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-61, TD-79 y
TD-80). **Nada está implementado.**

| XR | Decisión docente (2026-10-07) | Texto final de lo que cambia |
|---|---|---|
| XR-01 | REVISE | G-02: «Todavía falta indicar: {lista}.» · G-06: «Hay una orden entendida que está retenida. El estado del paciente no ha cambiado; completa el razonamiento con tus palabras o con los campos guiados.» El resto, aprobado |
| XR-02, XR-03 y XR-04 | APPROVE | — |
| XR-05 | APPROVE, opción b | Si el residente nombró un fármaco reconocido, la pregunta lo repite («the ceftriaxone dose» · «la dosis de ceftriaxona»); si sólo se reconoció una clase, usa la etiqueta de la clase. Aprobados también la limpieza inglesa de las claves de V-1, el español de V-1 y V-2, y los ajustes del calcio y de la sedación del procedimiento. Los identificadores canónicos e internos no cambian |
| XR-06 | APPROVE: V-9 entera, como se propuso | Los identificadores canónicos guardados no cambian |
| XR-07 | REVISE | Sólo la unidad de la cardioversión: «Indica la energía de la cardioversión entre 1 y 360 J.» El resto de los rangos y límites, y X1-C14, aprobados |
| XR-08 y XR-09 | APPROVE | — |
| XR-10 | REVISE | L-02: «Ingresa tu razonamiento clínico y/o tus acciones.» L-03, aprobada |
| XR-11 | REVISE | L-04: «Pregúntale al paciente» · «Pregunta al informante disponible». L-09: «Fuente de información: {fuente}». L-10, segunda frase: «El paciente no puede responder por ahora. Las preguntas se dirigen al informante disponible.» El resto, aprobado |
| XR-12 y XR-13 | APPROVE | — |
| XR-14 | REVISE | T-08: «— inicio {hh:mm} · último ajuste {hh:mm}», sin «(ajustado)». T-06: «Sedación para el procedimiento: etomidato {n} mg en total + midazolam {n} mg en total». El resto, aprobado |

- **Cuentas:** de las 28 decisiones consolidadas, 14 decididas (9 APPROVE y 5 REVISE) y 14 por decidir. De las 105
  originales de X-1, 67 decididas y 38 por decidir, todas en el lote 2.
- **Contradicción informada, sin resolver (L-09):** «Fuente de información» choca con «Fuente de la historia», la
  etiqueta que la docencia fijó el 2026-09-26 (C-2026-09-26-25) y que la sala usa también en la línea de llegada. El
  corpus de la validación externa lee ese mismo marco y no se toca. Opciones y recomendación en X-1, §12.2 (XR-11). No
  se eligió. **Resuelta el mismo día con la opción (c)** (vigésima actualización).
- **Hallazgo al preparar el lote 2, sin cambiar código:** X1-C11 y las tres frases de X1-C30 ya salen enteras en
  español (`language.py`); el inventario las había contado entre las que faltan. Se decide entre el español activo y
  el borrador (XR-15 y XR-22).
- **Siguiente lote:** X-1, lote 2 (XR-15 a XR-28; X-1, §12.3).
- **B-5: BLOCKED.**

**Actualizado por vigésima vez el 2026-10-07: B-5 · L-09 resuelta, lote 2 de X-1 (XR-15 a XR-28) y X-1 decidida
entera.** Registrado también en `docs/revision/X1_ESPANOL_PROPUESTO.md` (§12.2 y §12.3), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda. **Nada está
implementado.**

| ID | Decisión docente (2026-10-07) | Texto final o regla |
|---|---|---|
| L-09 | Opción (c) | «Fuente de la historia: {fuente}». No se implementa «Fuente de información». Razones: una sola etiqueta formal para el mismo concepto; se conserva la redacción aprobada de la llegada; no se modifica ni se separa el texto de llegada que lee el corpus congelado de la validación externa; «informante disponible» sigue aprobado en L-04 y L-10 como prosa |
| XR-15 | APPROVE | X1-C10, como se propuso. X1-C11, con el español que ya estaba activo: no se cambia «Indica» por «Escribe» |
| XR-16, XR-17, XR-19 y XR-20 | APPROVE | — |
| XR-18 | REVISE | EN: «The patient is {state} and cannot safely swallow. Use an intravenous or intramuscular route until oral administration is safe.» · ES: «El paciente está {estado} y no puede tragar con seguridad. Usa una vía intravenosa o intramuscular hasta que sea seguro administrar por vía oral.» V-5, aprobada. Sólo redacción: no cambian la lógica de la vía ni el estado clínico |
| XR-21 | APPROVE | Etiquetas en vez de claves internas, en los dos idiomas; X1-C27 y X1-C28 como se propusieron; X1-C29: «Esta versión reconoce, pero no ejecuta: {lista}. Las acciones soportadas de la misma orden siguen por separado.» Las claves canónicas e internas no cambian |
| XR-22 | APPROVE | X1-C30, con el español que ya estaba activo; no se reemplaza por el borrador sólo por estilo |
| XR-23 | REVISE (menor) | Primera frase de X1-C31, neutra en género: «La orden de {fármaco} se interpretó como {forma}{ de {dosis}}.» V-6 y el resto, aprobados |
| XR-24, XR-25, XR-27 y XR-28 | APPROVE | — |
| XR-26 | APPROVE | «Registro» para «Acquisition», no «Toma»; «ECG» en vez de la clave cruda DIAGNOSTIC |

- **Cuentas, contadas en el borrador con un script, no supuestas:**
  - 28 de 28 decisiones consolidadas: 21 APPROVE y 7 REVISE (XR-01, XR-07, XR-10, XR-11, XR-14, XR-18 y XR-23);
  - 105 de 105 decisiones originales, con la tabla conjunta de vocabularios cerrada por V-5 y V-6;
  - **la revisión docente de X-1 está completa, y X-1 no está implementada.**
- **Contradicciones de X-1:** ninguna abierta; L-09 quedó resuelta con la opción (c).
- **Al implementar (no autorizado):** X1-C24 cambia también en inglés, y ese texto está en el registro de preservación
  de la hipoglicemia. El cambio se declara en `corrections_registry.py`, como pide ese registro (X-1, §10).
- **Siguiente etapa, preparada sin implementar:** la revisión del relato de los 30 casos y de la rúbrica en español
  (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`):
  - 30 casos y 5 dominios como unidades de aprobación, cada uno con el hash de lo que se leyó;
  - un lote 0 de frases comunes y terminología, 6 lotes de casos y un lote de rúbrica;
  - 4 decisiones de terminología (T-1 a T-3 en el relato, R-1 en la rúbrica);
  - 18 pasajes que fija el corpus de la validación externa: se aprueban tal cual o su corrección espera.
- **B-5: BLOCKED.** Falta:
  - la revisión del relato y de la rúbrica;
  - implementar lo decidido (X-1, los 7 REVISE del paquete y las claves internas) y verificar el candidato final;
  - sobre ese candidato, la firma de H-62 e I-63.

**Actualizado por vigesimoprimera vez el 2026-10-07: B-5 · diseño de la revisión del relato y de la rúbrica,
aprobado.** Registrado también en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-81). **Nada está
implementado.**

| Decisión docente (2026-10-07) | Qué fija |
|---|---|
| Diseño de la revisión | APPROVE (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`) |
| Relato: unidad de aprobación | El caso entero; cada aprobación ata `variant_id`, `version` (el hash ya definido del contenido bilingüe exacto revisado) y `decision = approved`, sin nombres ni identificadores personales. `case_text/es/approvals.json` se genera sólo cuando los 30 casos terminen su revisión |
| T-1, T-2 y T-3 | «crépitos» (como R-4), «defensa» y «confundido», aplicados de forma coherente en la revisión |
| Los 18 pasajes que fija el corpus de la validación externa | Aprobados tal cual para este candidato; sin cambios de redacción en esta revisión; el estilo espera al cierre formal de la validación externa; un error clínicamente relevante se escala igual |
| Rúbrica D1–D5 | El mismo principio: una aprobación por dominio, con `domain_id`, `version` y `decision = approved`, sin nombres. No se crean todavía. Antes de congelar el candidato, se identifica y se prueba el camino de activación que ya usa la app |
| R-1 | «revisar» para «check»; «vigilar» sólo para «watch»; el vocabulario de razonamiento de X-1 donde el constructo es el mismo, sin cambiar sentido, niveles, puntaje ni estructura |
| Orden | Lote 0, RUB, R1, R2, R3, R4, R5 y R6 |

- **Lote 0, preparado para la revisión docente** (`docs/revision/B5_RELATO_LOTE_0.md`):
  - 47 frases comunes, con 527 apariciones en los 30 casos, en 11 decisiones por grupo;
  - recomendación APPROVE AS IS en las 11, sin observaciones semánticas ni clínicas;
  - las 527 apariciones quedan trazables por caso y ruta.
- **Siguiente lote:** RUB, después de la decisión docente sobre el lote 0.
- **B-5: BLOCKED.**

**Actualizado por vigesimosegunda vez el 2026-10-07: B-5 · lote 0 del relato aprobado; lote RUB para revisión.**
Registrado también en `docs/revision/B5_RELATO_LOTE_0.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y
en el registro de deuda (TD-81). **Nada está implementado.**

- **Lote 0 (docente, 2026-10-07):**
  - APPROVE en los 11 grupos: 47 de 47 frases comunes aprobadas; sus 527 apariciones siguen trazables por caso y
    ruta;
  - se mantienen «susceptibilidad» (L0-21) y «Campos pulmonares limpios; sin consolidación ni edema.» (L0-26);
  - T-1 a T-3 siguen como se aprobaron, y los 18 pasajes del corpus no se tocan.
- **Lote RUB, preparado para la revisión docente** (`docs/revision/B5_RUBRICA_RUB.md`):
  - 5 decisiones, una por dominio, cada una con el hash de la versión que se presenta;
  - R-1 aplicada en D4: cambian 3 descriptores;
  - recomendación: APPROVE AS IS en D1 a D4, y REVIEW CLOSELY en D5. En español, «seguimiento» nombra el D4 y también
    el «follow-up» del nivel 3 de D5. Opción (b): «un control posterior» en ese nivel;
  - sin conflicto con X-1 después de R-1.
- **Siguiente lote:** R1, después de la decisión docente sobre RUB.
- **B-5: BLOCKED.**

**Actualizado por vigesimotercera vez el 2026-10-07: B-5 · rúbrica en español decidida (5 de 5); lote R1A para
revisión.** Registrado también en `docs/revision/B5_RUBRICA_RUB.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md` y en el
registro de deuda (TD-81). **Nada está implementado.**

| Dominio | Decisión docente (2026-10-07) | Versión que ata la aprobación |
|---|---|---|
| D1, D2 y D3 | APPROVE AS IS | `552618f3…`, `0393ca0d…` y `bf7395c3…` |
| D4 | APPROVE AS IS con R-1: «revisar» para «check», «vigilar» para «watch» | `041597d9…` |
| D5 | APPROVE de la opción (b): en el nivel 3, «…un traspaso de la atención o un control posterior que explicite los asuntos pendientes.» No se usa «seguimiento» para «follow-up», porque D4 ya usa «Seguimiento» para «Monitoring» | `52958f1c…` |

- **Rúbrica:** 5 de 5 decisiones.
  - Los niveles 0–3, el puntaje, la estructura de dominios y la rúbrica en inglés no cambian.
  - La terminología en español queda alineada con X-1.
  - No se crean las aprobaciones ni se toca `rubric_text/es`.
  - Al implementar, el texto de cada dominio tiene que dar exactamente su versión aprobada.
  - Antes de congelar el candidato, se identifica y se prueba el camino de activación que ya usa la app.
- **R1, dividido por decisión docente** en R1A y R1B, en el orden canónico del banco. **R1A, preparado para la
  revisión docente** (`docs/revision/B5_RELATO_R1A.md`):
  - casos `acs_54m_inferior`, `acs_66f_nonst` y `acs_61m_posterior`;
  - 49 pasajes propios, y 56 cubiertos por el lote 0;
  - ningún pasaje fijado por el corpus;
  - T-2 y T-1 aplicadas en un pasaje cada una;
  - recomendación APPROVE en los 3 casos.
- **Siguiente lote:** R1B, después de la decisión docente sobre R1A.
- **B-5: BLOCKED.**

**Actualizado por vigesimocuarta vez el 2026-10-07: B-5 · R1A aprobado (3 de 30 casos); R1B para revisión.**
Registrado también en `docs/revision/B5_RELATO_R1A.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y
en el registro de deuda (TD-81). **Nada está implementado.**

| Caso | Decisión docente (2026-10-07) | Versión objetivo aprobada |
|---|---|---|
| `acs_54m_inferior` | APPROVE WHOLE CASE, con T-2 (guarding → defensa) | `e1afcda52d3e3fab6853c2b1bd44bf07c4e6ef04296cdde9f7fe87723a48076a` |
| `acs_66f_nonst` | APPROVE WHOLE CASE, con T-1 (crackles → crépitos) | `d64dc72663d6d94f4b919ab8529e2314263cbb010d4de66e52738a1221eb95c1` |
| `acs_61m_posterior` | APPROVE WHOLE CASE | `a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890` |

- **Regla de versión (docente):** la aprobación ata la versión objetivo presentada en la revisión, no la que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente. Vale para todos los casos con un término aplicado.
- **Relato:** 3 de 30 casos aprobados; ningún archivo de aprobación creado.
- **R1B, preparado para la revisión docente** (`docs/revision/B5_RELATO_R1B.md`):
  - casos `acs_52m_de_winter`, `acs_48m_wellens` y `acs_70f_left_main`;
  - 44 pasajes propios, y 61 cubiertos por el lote 0;
  - ningún pasaje fijado por el corpus;
  - T-1 aplicada en un pasaje de la 52m y en uno de la 70f;
  - recomendación APPROVE en los 3.
- **Siguiente lote:** R2, después de la decisión docente sobre R1B.
- **B-5: BLOCKED.**

**Actualizado por vigesimoquinta vez el 2026-10-07: B-5 · R1B aprobado (bloque de SCA 6 de 6; relato 6 de 30); R2A
para revisión.** Registrado también en `docs/revision/B5_RELATO_R1B.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-81). **Nada está
implementado.**

| Caso | Decisión docente (2026-10-07) | Versión objetivo aprobada |
|---|---|---|
| `acs_52m_de_winter` | APPROVE WHOLE CASE, con T-1 (crackles → crépitos) | `daf766118b4ae254ae6fa4261bebb40a96eb3ce6d3a4d92f3048d0f5acdc4056` |
| `acs_48m_wellens` | APPROVE WHOLE CASE; coincide con la versión del repositorio | `13a569872e3a88cf1f01537ee50544f5057cc21942bd10d4e3b3ba03681ab04d` |
| `acs_70f_left_main` | APPROVE WHOLE CASE, con T-1 y su concordancia («crépitos basales dispersos») | `c94b56ee409f799557c53b017e5144c4c076549426d9a75aaec6cd314bddb552` |

- **Regla de versión (docente):** la misma de R1A. Rige para las versiones objetivo que difieren de la del
  repositorio (aquí, la 52m y la 70f).
- **Estado del relato:**
  - R1A, 3 de 3; R1B, 3 de 3; bloque de SCA, 6 de 6;
  - relato del piloto, 6 de 30 casos aprobados;
  - ningún archivo de aprobación creado.
- **R2, dividido por decisión docente** en R2A y R2B, en el orden canónico del banco (`clinical_cases.FAMILIES`:
  neumonía, edema pulmonar y asma). **R2A, preparado para la revisión docente** (`docs/revision/B5_RELATO_R2A.md`):
  - casos `pneumonia_46f`, `pneumonia_83m` y `pulmonary_edema_58m`;
  - 53 pasajes propios, y 50 cubiertos por el lote 0;
  - 3 pasajes fijados por el corpus, en `pneumonia_46f`, marcados y sin cambios;
  - T-1 en los 3 casos (en la 58m, con «crépitos bilaterales difusos») y T-2 en la 46f;
  - recomendación APPROVE en los 3.
- **Siguiente lote:** R2B (`pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`), después de la decisión docente sobre
  R2A.
- **B-5: BLOCKED.**

**Actualizado por vigesimosexta vez el 2026-10-07: B-5 · R2A aprobado (relato 9 de 30); R2B para revisión.**
Registrado también en `docs/revision/B5_RELATO_R2A.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y
en el registro de deuda (TD-81). **Nada está implementado.**

| Caso | Decisión docente (2026-10-07) | Versión objetivo aprobada |
|---|---|---|
| `pneumonia_46f` | APPROVE WHOLE CASE, con T-1 y T-2; los 3 pasajes fijos del corpus siguen exactamente como están | `d16cb3330fc87b73abb6d2e03eae76b428b4f61c0c33b9848cff27caa22977ca` |
| `pneumonia_83m` | APPROVE WHOLE CASE, con T-1 | `45a84e879f0a33e8167bf2de5937d23d7eb8ef4068439f77f162563640cd0c1b` |
| `pulmonary_edema_58m` | APPROVE WHOLE CASE, con T-1 y su concordancia («crépitos bilaterales difusos») | `dffcae29509ba47cbea4b30959c62e9093d6bce2df1099d724495a6238f804ae` |

- **Regla de versión (docente):** la misma de R1A; rige para las 3 versiones, que difieren de la del repositorio.
- **Estado del relato:**
  - R1, 6 de 6; R2A, 3 de 3;
  - relato del piloto, 9 de 30 casos aprobados;
  - ningún archivo de aprobación creado.
- **R2B, preparado para la revisión docente** (`docs/revision/B5_RELATO_R2B.md`):
  - casos `pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`;
  - 49 pasajes propios, y 50 cubiertos por el lote 0;
  - 3 pasajes fijados por el corpus, en `asthma_24f`, marcados y sin cambios;
  - T-1 en la 75f;
  - una observación de sentido en la 24f (P-1: «crushing», hoy «opresivo», propuesto «aplastante»), con las dos
    versiones objetivo;
  - la intersección de la 49m con A-6a, A-6b, A-7-49m y A-8a: el examen de llegada es el texto exacto de A-6a, y
    nada del relato las contradice; no pide decisión nueva. No se implementa nada del motor (TD-83);
  - recomendación: APPROVE la 75f y la 49m; APPROVE con P-1 la 24f.
- **Siguiente lote:** R3 (TEP y bradicardias), después de la decisión docente sobre R2B.
- **B-5: BLOCKED.**

**Actualizado por vigesimoséptima vez el 2026-10-07: B-5 · R2B aprobado (bloque respiratorio 6 de 6; relato 12 de 30);
R3A para revisión.** Registrado también en `docs/revision/B5_RELATO_R2B.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-81). **Nada está
implementado.**

| Caso | Decisión docente (2026-10-07) | Versión objetivo aprobada |
|---|---|---|
| `pulmonary_edema_75f` | APPROVE WHOLE CASE, con T-1; la revisión A-2 del motor sigue igual y no es parte de esta aprobación | `4695ee50cfa00208c0c9fa70b527e7495119392cf279487b72a5880d25d2d06c` |
| `asthma_24f` | APPROVE WHOLE CASE **con P-1**: «…no un dolor aparte que sea localizado o aplastante.»; los 3 pasajes fijos del corpus, sin cambios | `844d280d53271a3444adc8293a73f42ec5aac090a08d4af839d5100a5fbc4615` |
| `asthma_49m` | APPROVE WHOLE CASE; el examen respiratorio de llegada no se cambia (es A-6a, alineado con A-6b, A-7-49m y A-8a) | `6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540` |

- **P-1, motivo docente:** «crushing» no se traduce «opresivo» en la 24f, porque el caso ya usa «opresión» para
  «tightness», y la negación podría parecer que contradice el síntoma de presentación.
- **Terminología:** «murmullo pulmonar» y «entrada de aire» siguen aceptados en sus contextos ya aprobados; no hace
  falta decisión nueva.
- **Regla de versión (docente):** cada versión del español tiene que dar exactamente su hash aprobado al implementar;
  si da otro, se detiene y vuelve a revisión docente.
- **Estado del relato:**
  - R1, 6 de 6; R2, 6 de 6;
  - relato del piloto, 12 de 30 casos aprobados;
  - ningún archivo de aprobación creado.
- **Cambios del relato aprobados, para implementar:** T-1, T-2 y T-3 donde corresponda, y P-1 en `asthma_24f`.
- **R3, dividido por decisión docente** en R3A y R3B, en el orden canónico del banco (`clinical_cases.FAMILIES`: TEP,
  después bradicardias). **R3A, preparado para la revisión docente** (`docs/revision/B5_RELATO_R3A.md`):
  - casos `pulmonary_embolism_33f`, `pulmonary_embolism_61m` y `bradycardia_ccb_68m`;
  - 57 pasajes propios, y 53 cubiertos por el lote 0;
  - ningún pasaje fijado por el corpus;
  - T-1 a T-3 ya rigen en los 3; ninguna versión cambia;
  - P-1 revisada: el «presión opresiva» de la 61m no reproduce el problema de la 24f;
  - recomendación APPROVE en los 3.
- **Siguiente lote:** R3B (`bradycardia_avb3_78f`, `bradycardia_bb_54f` y `bradycardia_hyperk_63m`), después de la
  decisión docente sobre R3A.
- **B-5: BLOCKED.**

**Actualizado por vigesimoctava vez el 2026-10-07: B-5 · R3A aprobado (relato 15 de 30); R3B para revisión.**
Registrado también en `docs/revision/B5_RELATO_R3A.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y
en el registro de deuda (TD-81). **Nada está implementado.**

| Caso | Decisión docente (2026-10-07) | Versión aprobada |
|---|---|---|
| `pulmonary_embolism_33f` | APPROVE WHOLE CASE. El texto aprobado es el del repositorio («…arterias pulmonares derecha e izquierda…»); el «derechas e izquierdas» del chat fue un error de transcripción | `d3a826e9c4679a8944e2a5eb5e174f36ba800ca0c91a48bd7a14f8afbe05e5ab` |
| `pulmonary_embolism_61m` | APPROVE WHOLE CASE. Se conservan «defensa muscular» (equivalente a T-2) y «presión opresiva sostenida» (P-1 no se aplica aquí) | `71c15c2b2811acd747993f8bb4e5d6f0cad5083ceaf035655fe7aba055ebd714` |
| `bradycardia_ccb_68m` | APPROVE WHOLE CASE | `10b926936212c922ccd2a3ce699c4d87df4f76d4c50e456bbf0c628d3f8932c4` |

- **Regla de versión (docente):** la aprobación ata la versión exacta revisada. Si la implementación cambia el hash
  de un caso aprobado, se detiene y vuelve a revisión docente.
- **Estado del relato:**
  - R1, 6 de 6; R2, 6 de 6; R3A, 3 de 3;
  - relato del piloto, 15 de 30 casos aprobados;
  - ningún archivo de aprobación creado.
- **R3B, preparado para la revisión docente** (`docs/revision/B5_RELATO_R3B.md`):
  - casos `bradycardia_avb3_78f`, `bradycardia_bb_54f` y `bradycardia_hyperk_63m`;
  - 54 pasajes propios, y 56 cubiertos por el lote 0;
  - ningún pasaje fijado por el corpus;
  - T-1 ya rige en la 63m; ninguna versión cambia;
  - comprobación pedida: «confused» no aparece (T-3 no se aplica; la 78f usa el sustantivo «confusión»); propranolol y
    betabloqueador coinciden con V-9, y el relato no nombra antídotos; el relato no dice «bradycardia» ni «arrest», así
    que no choca con K-E6 (que no se implementa);
  - recomendación APPROVE en los 3.
- **Siguiente lote:** R4 (hipoglicemia y opioides), después de la decisión docente sobre R3B.
- **B-5: BLOCKED.**

**Actualizado por vigesimonovena vez el 2026-10-08: B-5 · R3B aprobado (bloque de TEP y bradicardias 6 de 6; relato
18 de 30); R4A para revisión.** Registrado también en `docs/revision/B5_RELATO_R3B.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-81). **Nada está
implementado.**

| Caso | Decisión docente (2026-10-08) | Versión aprobada |
|---|---|---|
| `bradycardia_avb3_78f` | APPROVE WHOLE CASE. El sustantivo «confusión» queda; T-3 rige «confused» → «confundido» y no obliga a cambiarlo | `677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7` |
| `bradycardia_bb_54f` | APPROVE WHOLE CASE. «Muy lenta» queda: refleja la ambigüedad del inglés «very slow», y el examen identifica el pulso como muy lento | `45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9` |
| `bradycardia_hyperk_63m` | APPROVE WHOLE CASE. «Carbonato de calcio» queda como medicación crónica, distinta de las sales de calcio de V-9 para el tratamiento agudo | `89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8` |

- **Regla de versión (docente):** la aprobación ata la versión exacta revisada. Si la implementación cambia el hash
  de un caso aprobado, se detiene y vuelve a revisión docente.
- **T-3, V-9 y K-E6:** no requieren ninguna decisión docente adicional para estos 3 casos.
- **Estado del relato:**
  - R1, 6 de 6; R2, 6 de 6; R3, 6 de 6;
  - relato del piloto, 18 de 30 casos aprobados;
  - ningún archivo de aprobación creado.
- **R4, en dos partes por decisión docente**, en el orden canónico del banco (`clinical_cases.FAMILIES`: hipoglicemia,
  después opioides). **R4A, preparado para la revisión docente** (`docs/revision/B5_RELATO_R4A.md`):
  - casos `hypoglycemia_28m`, `hypoglycemia_76f` y `hypoglycemia_54m_thiamine`;
  - 48 pasajes propios, y 51 cubiertos por el lote 0;
  - ningún pasaje fijado por el corpus;
  - T-3 en el examen neurológico de la 28m («Somnoliento y confundido»); las otras dos versiones no cambian;
  - comprobación pedida: el relato no menciona ninguna vía venosa (A-12 a A-18 son frases del motor, sin texto en
    común), no nombra glucosa, dextrosa, glucagón ni naloxona (V-9), y no contiene órdenes ni tratamientos ya
    administrados (F0-12 y la Fase 0); no pide decisión nueva;
  - recomendación APPROVE en los 3.
- **Siguiente lote:** R4B (`opioid_35m` y `opioid_67f`), después de la decisión docente sobre R4A.
- **B-5: BLOCKED.**

**Actualizado por trigésima vez el 2026-10-08: B-5 · R4A aprobado (relato 21 de 30); R4B, R5 y R6 preparados (los 9
casos que faltan); integridad de los 30; TD-84 propuesta.** Sesión autónoma de documentación, sin decisión docente
nueva. Registrado también en `docs/revision/B5_RELATO_R4A.md`, `docs/revision/B5_RELATO_R4B.md`, `docs/revision/B5_RELATO_R5.md`, `docs/revision/B5_RELATO_R6.md`, `docs/revision/B5_RELATO_INTEGRIDAD_30.md`, en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md` (§8), en
`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, en el paquete (1.5) y en el registro de deuda (TD-81, TD-84). **Nada
está implementado.**

| Caso | Decisión docente (estado del 2026-10-08) | Versión aprobada |
|---|---|---|
| `hypoglycemia_28m` | APPROVE WHOLE CASE, con T-3 («Somnoliento y confundido») | `65cae7edde83847fd6641ca77a94b034da1ced9e1228df8894f9cbe09ab61950` |
| `hypoglycemia_76f` | APPROVE WHOLE CASE | `a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845` |
| `hypoglycemia_54m_thiamine` | APPROVE WHOLE CASE | `cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a` |

- **Fuente de esta decisión:** el estado docente del 2026-10-08 («R4A = 3/3 approved; TOTAL = 21/30»). No repitió los
  hashes; por la regla de versión, ata las versiones presentadas en R4A. Si la docencia quiso otra cosa, se corrige aquí.
- **Precisión posterior (sin cambio de decisión):** en la hipoglicemia, el bloque de llegada agrega una frase del motor
  sobre la vía venosa (`language.ENGINE_SENTENCES`), que sigue al relato y no entra en el hash del caso.
- **R4B, R5 y R6, preparados para la revisión docente (9 casos):**
  - R4B (`opioid_35m`, `opioid_67f`), R5 (`gi_bleed_57m`, `gi_bleed_72f`, `anaphylaxis_29f`,
    `anaphylaxis_63m_betablocked`) y R6 (`renal_colic_34m`, `obstructive_pyelonephritis_58f`,
    `trauma_limb_hemorrhage_27m`), en el orden canónico del banco;
  - 188 pasajes propios (31, 80 y 77) y 12 pasajes fijos del corpus (6 en R5, 6 en R6), sin cambios;
  - los 9, categoría A: ningún cambio de texto; versión objetivo = la del repositorio; recomendación APPROVE;
  - `trauma_hemothorax_41m`, excluido del piloto (F0-2), no se revisó ni cuenta.
- **Integridad de los 30 (`docs/revision/B5_RELATO_INTEGRIDAD_30.md`):** 21 aprobados, 9 revisados pendientes, 0 sin revisar; ningún duplicado ni faltante;
  las 30 versiones objetivo se reproducen; lote 0 sin diferencias; 18 pasajes fijos intactos; 0 cifras distintas; 0 inglés
  en el español.
- **Decisión docente nueva que se propone:** TD-84 (propuesta, sin decidir): en `opioid_35m` y `opioid_67f`, el examen neurológico que compone el motor pierde en inglés «small reactive» antes de «pupils» (`family_engine.py:3210–3218`); el español conserva «Pupilas pequeñas y reactivas». VERIFICADO con el motor, sólo lectura. No es del relato. Ver
  `docs/revision/B5_IMPLEMENTATION_READINESS_MAP.md`.
- **Siguiente:** la decisión docente sobre R4B, R5 y R6 (9 casos) y sobre TD-84.
- **B-5: BLOCKED.**

**Actualizado por trigésima primera vez el 2026-10-08: B-5 · plan de implementación, de promoción y de la Fase 1
(sesión autónoma, sólo documentación).** Sin decisión docente nueva. **Nada está implementado, empujado ni
desplegado.** Documentos nuevos:
- `docs/revision/B5_IMPLEMENTATION_READINESS_MAP.md`:
  - 21 ítems decididos sin implementar, con su mapa al código (archivo, función, actual, objetivo, tipo de cambio,
    pruebas);
  - la activación del relato y de la rúbrica (§4 y §5), con el diseño del exportador y sus pruebas;
  - 8 grupos atómicos (IG-0 a IG-7) y su secuencia;
  - la matriz de recertificación (A, B, C).
- `docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md` (6A–6H): puerta de promoción, Git, Neon, Streamlit con la
  matriz de configuración, prueba de humo de 25 pasos, después del despliegue, vuelta atrás y evidencia.
- `docs/revision/PHASE_1_KICKOFF_PACKAGE.md` (Contratos v2; 11 paquetes WP0 a WP10) y
  `docs/revision/PHASE_1_FIRST_PROMPT.md` (sólo WP0; **no ejecutado**).

**Lo que se propone a decisión:**
- **TD-85 (propuesta, sin decidir):** dos frases del motor llegan en inglés a la sala en español, sin borrador ni
  inventario:
  - el paro de la bradicardia (`bradycardia_toxicology.ARREST_TEXT`, los 4 casos de bradicardia);
  - la reacción bifásica de la anafilaxia (`anaphylaxis_reaction.BIPHASIC_TEXT`, `anaphylaxis_29f`).
  VERIFICADO con el motor. Con el español propuesto en el mapa (§3) y en el registro de deuda. Muestra que el
  inventario de X-1 no era exhaustivo: el centinela del español es obligatorio.
- **TD-84** sigue propuesta (trigésima actualización).

**Lo que decide la persona responsable (no clínico):**
- **Rama de la Fase 1:** el readiness (§16.3) dice que la Fase 1 sigue en `clinical-encounter-v0.13`; el encargo del
  2026-10-08 propone `phase-1-contracts-v2`. Se recomienda `phase-1-contracts-v2`. Al autorizar la Fase 1, actualizar
  la línea de la rama de CLAUDE.md.
- **La propuesta de arquitectura** que cita el código («proposal §9.4», «Phase 4») no está en `docs/`. Se recomienda
  agregarla antes de WP1.

**Diferencias halladas, sin cambio de código:**
- el preflight acepta una clave del proveedor presente pero retenida, y §16.11 exige ausencia: el runbook agrega la
  comprobación manual;
- `docs/RUNBOOK_PILOTO.md` está desactualizado frente a §16;
- el ayudante `b1_target_check.py` no está en el repositorio: se recrea desde §18.6;
- ninguna prueba comprueba `F0_11_FRASES_ES.md`.

**Siguiente:** la decisión docente sobre R4B, R5 y R6 (9 casos), TD-84 y TD-85; después, la autorización de la ronda
de implementación (mapa, §7).
- **B-5: BLOCKED.**

| Bloqueo | Estado | Qué falta | Decisión que se necesita |
|---|---|---|---|
| B-1 | **Resuelto** (2026-10-07; informe, sección 20): corrida única en Neon (PostgreSQL 17.11, *pooled*, TLS), con 23 passed sobre `8ff41a4`. Antes, bloqueado (sección 19) | Nada | Ninguna. Si las firmas cambian el SHA final, el contrato de promoción vuelve a correrla (16.4, paso 5) |
| B-2 | **Resuelto** (2026-10-07; informe, sección 16), con D-B2-1 a D-B2-4 decididas. Antes, bloqueado por datos de las cuentas | La app, la rama, la base y el Python del piloto no están identificados | Cuál app y cuál base; una rama propia fija en el commit aprobado; Python 3.11 |
| B-3 | **Resuelto** (`87bbbe1`): el preflight falla cerrado ante cada exigencia del manifiesto, con la semántica de la app (TD-71) | El preflight puede decir «LISTA» fuera de la configuración congelada (TD-71); el manifiesto exige lo que el preflight sólo recomienda | Procedimiento (sin clave del proveedor, valores entre comillas, AVISO = FALLA) o corrección de la herramienta |
| B-4 | **Resuelto** (`4d570a8`): `streamlit==1.64.0`; el Python de la app queda en B-2 (TD-72 a) | Dependencias sin fijar: hoy se instalaría Streamlit 1.65.0 (TD-72) | Fijar 1.64.0 o 1.65.0 |
| B-5 | **Bloqueado** | Las firmas docentes. El 2026-10-07 quedaron decididos X-1, J, las 100 decisiones del paquete (niveles 1, 2 y 3) y la redacción de los estados límite de la 49m (A-6a, A-6b, A-7-49m y A-8a), sin implementar; H-62 e I-63, decididas DEFER, siguen sin firma a propósito hasta el candidato final implementado (2 firmas abiertas). El español de X-1, decidido entero el 2026-10-07 (105 de 105; `docs/revision/X1_ESPANOL_PROPUESTO.md`), sin implementar; L-09 resuelta con la opción (c) | Revisar el relato de los 30 casos y la rúbrica en español antes de congelar el candidato, con el diseño aprobado el 2026-10-07 (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`; lote 0, rúbrica, R1, R2, R3 y R4A aprobados, 21 de 30 casos; R4B, R5 y R6 en revisión; plan de implementación en `docs/revision/B5_IMPLEMENTATION_READINESS_MAP.md`); llevar las aprobaciones del relato al candidato en `case_text/es/approvals.json` (camino a) e identificar el mecanismo de la rúbrica; implementar lo decidido antes de construir el candidato final; actualizar y firmar las guías sobre ese candidato |
| B-6 | **Resuelto** (`e200ccc`): 56 de 56 (TD-73) | 2 de 56 regresiones activas fallan por texto que la Fase 0 cambió (TD-73) | Actualizar sus textos esperados con justificación o retirarlas con motivo |

**Contradicciones informadas, sin resolver** (informe, 10.2): «31 casos» en `READINESS_PILOTO_FORMATIVO.md`,
`CIERRE_PREPILOTO.md` y `GUIA_DOCENTE_PILOTO.md`, frente a los 30 del manifiesto (F0-2; el preflight ya dice 30);
la guía docente dice que un fármaco sin verbo «puede perderse sin aviso»; ninguna guía describe la conducta nueva
de la sala.

## Cierre de la Fase 0 (2026-10-06)

**Instrucción del 2026-10-06** («Phase 0 is APPROVED IN PRINCIPLE»): cerrar la Fase 0 sin reabrir su diseño y sin
empezar la Fase 1 ni el núcleo fisiológico común. Registro: `INSTRUCTION_2026_10_06_PHASE0_CLOSURE` y
C-2026-10-06-12 a C-2026-10-06-14 en `corrections_registry.py`. Informe: `docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`,
sección «Cierre de la Fase 0». Commits locales, sin push, despliegue, merge ni release.

| ID | Decisión docente (2026-10-06) | Estado | Qué quedó |
|---|---|---|---|
| F0-1 | Aprobada: el lector V3 sigue congelado; la capa posterior al lector es de la sala | **CERRADA CON LIMITACIÓN DECLARADA** (G-READER-V3; TD-69) | El lector y sus baselines no cambiaron; el cierre de la cobertura (C-2026-10-06-12) también es de esa capa |
| F0-2 | `trauma_hemothorax_41m` fuera del piloto de residentes; sin modelar el pabellón | **CERRADA CON LIMITACIÓN DECLARADA** (C-NO-THEATRE) | 30 casos aceptados; el caso queda en el sandbox docente; el manifiesto registra la decisión |
| F0-3 | Aprobada como resuelta | **CERRADA** | TD-45 (g) resuelta en la sala; el lector, igual |
| F0-4 | Aceptada: R1-03, R1-04 y R2-01 fuera de la asignación automática; PS001 no vuelve para completar el currículo | **CERRADA CON LIMITACIÓN DECLARADA** (rutas heredadas excluidas) | Hueco curricular aceptado para el primer piloto: esos desafíos y MK1 no se observan |
| F0-5 | Aprobada: «reassess» sin número es una mirada inmediata en la cabecera (2 minutos); «dar X y reevaluar» es X más esa mirada, dicho así; una orden para más tarde no corre ahora; el límite de 120 minutos queda, explicado | **CERRADA CON LIMITACIÓN DECLARADA** (G-LATER-ORDERS, G-STEP-120) | Sin cambios |
| F0-6 | Aprobada; un evento de causa UNKNOWN sigue protegido de toda inferencia negativa | **CERRADA CON LIMITACIÓN DECLARADA** (G-INTERRUPTIONS) | Sin cambios |
| F0-7 | Aprobada; un evento con guion o NOT_PREVENTABLE_IN_SIMULATOR nunca sostiene una retroalimentación negativa | **CERRADA** | Sin cambios |
| F0-8 | Aprobada | **CERRADA** | Sin cambios; el texto, ahora también en español (F0-11) |
| F0-9 | Aprobada: mascarilla con reservorio a 15 L/min por omisión, dicho y registrado | **CERRADA** | Sin cambios; el recibo, también en español |
| F0-10 | Aprobada como está. **Una demora causada por la compuerta de razonamiento es de la compuerta y nunca se lee como demora del residente** | **CERRADA** | Registrado aquí. Una orden retenida por la compuerta queda HELD_REASONING con el minuto en que se escribió; si corre después, la regla B (0I) atribuye la demora al simulador |
| F0-11 | El piloto corre también en español: traducir antes del despliegue todos los textos nuevos de la Fase 0 que ve el residente, sin traducir códigos ni campos internos | **CERRADA** (firma docente pendiente) | Hecho (C-2026-10-06-14): cada frase nueva se dice entera en español y las palabras citadas de la persona residente quedan intactas. La autorización no es su firma: la redacción está a la firma docente en `docs/revision/F0_11_FRASES_ES.md` |
| F0-12 | Paridad del punto de entrada si es pequeña y segura | **CERRADA CON LIMITACIÓN DECLARADA** (paridad implementada; G-ANSWER-ORDER, TD-70) | C-2026-10-06-13: la respuesta completa sola la orden retenida y la orden escrita después se lee a continuación como orden propia (compuerta, preguntas, destino y recibo propios), con el minuto en que se escribió. Queda un caso protegido y declarado (TD-70): si la respuesta deja algo retenido, la orden de después conserva el recibo «Not run» |

**Cobertura (sección 2 de la instrucción).** Una cláusula escrita como se escribe una orden ya no desaparece porque
el nombre de la intervención esté fuera del vocabulario: queda UNRECOGNIZED con su recibo, en la capa posterior al
lector (C-2026-10-06-12). Las palabras que también podrían ser una nota, una descripción o un verbo suelto quedan
en el registro sin recibo, y ninguna omisión se lee contra ellas. Quedan tres formas estrechas sin destino propio
ni guarda (TD-69 d–f), declaradas en el congelamiento (G-READER-V3); la respuesta a Q1 y Q15 del informe dice la
garantía exacta.

**Estados.** «CERRADA CON LIMITACIÓN DECLARADA»: la decisión acepta una conducta que el manifiesto de congelamiento
declara como limitación del piloto, con su guarda.

**Prueba de humo en PostgreSQL (sección 5).** Hecha en una base PostgreSQL 16 local y descartable del entorno de
desarrollo, nunca en producción: A–F pasan (`test_phase0_submission_guard_on_postgres.py`, con
`MRS_TEST_POSTGRES_URL`).

## Fase 0 · Seguridad de la medición antes del piloto (2026-10-06)

**Instrucción del 2026-10-06** «PHASE 0 — PRE-PILOT MEASUREMENT SAFETY»: que el piloto sobre el motor de familias
actual no pueda atribuir al razonamiento del residente una limitación del motor, del lector, de la pantalla o del
tiempo. Sin núcleo fisiológico común ni Fase 1; sin cambios de puntaje, rúbrica, D1–D5, penalidades, objetivos ni
reportes; sin push, merge, despliegue ni release. Registro: `INSTRUCTION_2026_10_06_PHASE0` y C-2026-10-06-01 a
C-2026-10-06-11 en `corrections_registry.py`. Informe: `docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`. Manifiesto
generado: `docs/revision/PILOT_FREEZE_MANIFEST.md`.

- **Implementado y probado** (detalle y pruebas en el informe):
  - cada orden termina con un destino registrado y un recibo; las órdenes independientes corren y sólo esperan
    los grupos dependientes;
  - R1-03, R1-04 y R2-01 (motor heredado PS001) fuera de la asignación automática y de las directivas;
  - un envío se guarda antes de correr, corre una vez y no se pierde por doble clic ni recarga;
  - esperar avanza el reloj, «reassess» sin número es una mirada de 2 minutos, una orden para más tarde no corre
    ahora y un evento crítico corta la espera;
  - un paro es un paro (sin pulso ni presión, mensaje acordado, nada más ejecutable); el potasio del laboratorio
    es el del motor; cada evento dice su causa, severidad y prevenibilidad;
  - guardas deterministas A–E antes de todo análisis;
  - batería de aceptación de los 31 casos (motor y página real): 30 aceptados (12 ACCEPT, 18 ACCEPT WITH
    DECLARED LIMITATION) y 1 excluido, `trauma_hemothorax_41m`.
- **Sin cambios:** el lector (`family_parser.py`, `shared_order_language.py`), el corpus de validación, V3 y los
  baselines; los puntajes, las rúbricas, D1–D5 y las penalidades.
- **Commits locales**, sin push ni despliegue.

### Contradicciones entre fuentes, señaladas y no resueltas en silencio

| ID | Fuentes | Qué hay mientras tanto | Decisión pedida |
|---|---|---|---|
| F0-1 | El lector queda congelado durante la validación externa (CLAUDE.md; fila «Validación externa») frente a «You MAY modify parser/action handling» (Fase 0) | El lector no cambió (0 líneas de diferencia; baselines intactos). Lo nuevo es una capa de la sala, después del lector: las palabras de tiempo, el mapa de cobertura (lo no leído queda UNRECOGNIZED con su recibo), el nombre de la infusión en «Stop the epinephrine infusion» y el flujo de la mascarilla con reservorio | Confirmar que la capa es de la sala y no del lector que mide la validación, o pedir que se retire hasta la ingesta externa |
| F0-2 | Cierre prepiloto C-2026-10-02-08 («ningún caso excluido») frente a la regla de exclusión de la Fase 0 (§17) | `trauma_hemothorax_41m` excluido: desde que el paro es verdadero (0G), tras el drenaje el paciente para hacia el minuto 60 haga lo que haga, porque el pabellón no está modelado; la decisión evaluada después del drenaje (`trauma_drained_and_never_looked_again`, ventana 10–180) nunca sería evaluable. No se sortea ni se ofrece en las directivas; sigue en el sandbox docente | (a) mantenerlo excluido en el primer piloto (**recomendado**); (b) aceptarlo con el paro declarado: su decisión central quedaría sin evaluar; (c) representar el pabellón: es fisiología, fuera de la Fase 0 |

### Decisiones docentes abiertas

| ID | Decisión | Qué hay ahora | Recomendación |
|---|---|---|---|
| F0-3 | TD-45 (g) | La sala detiene «Stop the dextrose infusion» y «Suspender la infusión de glucosado» por la capa de F0-1; el lector y `test_reader_gaps_registered.py` siguen igual | Confirmar: (g) queda resuelta en la sala y pendiente en el lector |
| F0-4 | Hueco curricular de PS001 | Un residente de primer año recibe R1-05, R1-06 y R1-07; R1-03, R1-04 y R2-01 no se observan en el piloto, y MK1 (ACGME) sólo se vincula a R2-01 | Aceptar para el primer piloto; casos del banco para esos desafíos, después |
| F0-5 | Tiempo | Mirada inmediata de 2 minutos (una región examinada); una espera de más de 120 minutos se rechaza y se explica; una orden para más tarde se registra sin programarse y se pide escribirla cuando corresponda | Confirmar para el piloto |
| F0-6 | Umbrales de interrupción | Un evento declarado del motor, una PAS < 70 que cayó ≥ 20 sostenida 2 minutos o una SpO₂ < 85 que cayó ≥ 5 sostenida 2 minutos cortan la espera | Confirmar |
| F0-7 | Prevenibilidad declarada | Bloqueo AV de la 54m y FV de las oclusiones: con guion, nunca evidencia negativa (la FV se juzga por la decisión de reperfusión, no por su minuto); bifásica: NOT_PREVENTABLE_IN_SIMULATOR; sangrado mayor tras la lisis: UNKNOWN; paro del hemotórax: ENGINE_LIMITATION; paro del miembro sin tratar (~13 min): PREVENTABLE | Confirmar |
| F0-8 | Dos correcciones de la batería | El paro de la bradicardia se lee de la frecuencia que muestra el monitor (C-2026-10-06-08); el paro de la anafilaxia tras una dosis que se agotó lo dice así (C-2026-10-06-09) | Confirmar; el texto nuevo, en inglés, espera su español (TD-46) |
| F0-9 | Valores por omisión de la sala | Mascarilla con reservorio sin flujo: 15 L/min, dicho en el recibo; una infusión sin nombre toma el de la única que sus palabras nombran | Confirmar |
| F0-10 | Compuerta de razonamiento | Sigue reteniendo el envío completo que retiene (metodología sin cambio; una intervención urgente nunca se retiene: decisión docente 12 del 2026-09-25); cada orden queda HELD_REASONING y una orden nueva escrita al responder recibe su destino | Confirmar que la regla de paquete no alcanza a la compuerta |
| F0-11 | Textos nuevos en inglés | Recibos del ledger, mensajes de tiempo, de espera interrumpida, de paro y de envío interrumpido, etiquetas de eventos y el texto nuevo de la anafilaxia: en inglés, sin traducción automática (TD-46) | Revisión docente del español antes del piloto en español |
| F0-12 | Orden nueva escrita al responder una aclaración | La respuesta completa sólo la orden retenida («1000 mL»); una orden escrita junto a ella («…and give ceftriaxone 2 g IV») no corre y queda UNRECOGNIZED, con un recibo que dice por qué y pide escribirla como orden nueva. En la respuesta a la compuerta de razonamiento, en cambio, la orden nueva corre (0A-0B) | Mantener para el piloto: leer órdenes en una respuesta arriesga dar dos veces lo retenido |

## Cierre del paquete prepiloto (2026-10-02)

**Instrucción docente del 2026-10-02:** avanzar con D-1 a D-11, TD-56 y TD-59 para cerrar el paquete prepiloto;
corregir los bloqueos y verificar el recorrido afectado; sin otro ciclo de auditoría ni ampliar el alcance; sin
pedir de nuevo autorización para lo aprobado; sin desplegar ni ejecutar la prueba de humo contra datos reales.
Registro: `INSTRUCTION_PREPILOT_CLOSURE` en `corrections_registry.py`. Las firmas pendientes, en una sola tabla,
están en `docs/revision/CIERRE_PREPILOTO.md`.

| ID | Decisión docente | Qué se hizo | Registro |
|---|---|---|---|
| D-1 · TD-48 | **Aprobado.** Todas las ventanas del E-FAST disponibles, coherentes en sala, Trace e informes; sin inventar hallazgos | Cinco ventanas, «Not documented» si el caso no la documenta; un resultado anterior conserva su línea. El hemotórax de la 41m se ve y las dos C14 de trauma son observables | C-2026-10-02-02 |
| D-2 · TD-50 | **Aprobado.** El examen refleja el estridor del estado actual; no deducirlo de la SpO₂; comprobar tras intubar | El examen sigue la bandera del motor; la 63m declara sin compromiso de vía aérea alta; el estridor se cobra respecto de la llegada | C-2026-10-02-04 |
| D-3 · TEP | **Mantener la fisiología para el piloto, con alcance limitado** | Sin recalibrar. El límite de la 33f queda en su declaración y en la rúbrica y los objetivos: esa respuesta no se evalúa ni juzga el rescate hemorrágico; nada se cobra por no revertirla. Ningún caso excluido: su objetivo central sigue evaluable | C-2026-10-02-08 |
| D-4 · Shock | **Aprobado** | Nota con el criterio completo; el shock no espera 15 minutos; concordante con `pe_obstruction.basis` | C-2026-10-02-05 |
| D-5 · Notas TEP | **Ajustes menores autorizados**; la autorización no es su firma | «administrada», «Trombólisis», fármacos en español, aviso del sangrado traducido. Versiones finales presentadas juntas para su firma | C-2026-10-02-05 |
| D-6 · R-4 | **Autorizado** | La frase 18 recupera «pasa», sin cambiar dosis, concentración, vía ni velocidad; las 18 en una tabla | C-2026-10-02-06 |
| D-7 · R-2 | **Criterios aceptados, con condiciones** | Redacción de la 52m aplicada; las dos fichas de trauma listas tras TD-48; sin «dynamic»; sin atribuir adquisición ni lectura de imágenes. La aceptación queda registrada en las fichas; su firma sigue pendiente | C-2026-10-02-07 |
| D-8 · 70f | **Aviso docente y regla de evaluación para el piloto** | Sin corregir la fisiología (TD-53). Se juzga con las señales visibles; un bolo pequeño justificado y reevaluado es aceptable; lo que el simulador no muestra no es evaluable | C-2026-10-02-07, C-2026-10-02-08 |
| D-9 · TD-49/51 | **TD-49 corregida si es la misma pérdida de información; TD-51 después** | TD-49: era la misma dosis escrita dos veces; ahora una fila por dosis, sin contenido clínico nuevo. TD-51 diferida | C-2026-10-02-03 |
| D-10 · R-3 | **T-2 con C1 YES; T-3 y T-4 NO**, según el paquete | Decisión de alcance registrada en `docs/tdfc/TDFC_TABLA_FINAL.md`; sin cambiar declaraciones ni agregar la frase opcional; nada confirma observaciones ni niveles; firma pendiente | — |
| D-11 · Guías | **Actualizar** con etiquetas en español, el paso de eventos críticos y los avisos de foto y POCUS | Las dos guías describen el funcionamiento comprobado y quedan listas para su firma | — |
| TD-56 | Documentar y verificar el orden; no fabricar aprobadores | Una aprobación espera la cuenta que nombra; `check_database.py --photo-approvals` verifica antes de abrir encuentros (runbook §3) | C-2026-10-02-09 |
| TD-59 | Recuperar los hallazgos propios sin concatenar texto que contradiga la evolución | Estables, como fragmentos literales; la herida de la 27m según su control; lo que no tiene evolución, documentado sin inventarla | C-2026-10-02-10, C-2026-10-02-11 |

## Revisión clínica prepiloto (2026-10-02)

Instrucción docente «PRE-PILOT CLINICAL REVIEW» (no es el ciclo 11): presentar, revisar y decidir antes del primer
piloto formativo, sin reabrir el lector, la validación externa, V3 ni la metodología.

- **El paquete:** `docs/revision/PRE_PILOT_REVIEW_PACKET.md`.
  - Secciones A–L: R-2, R-4, el español y la fisiología de la TEP, TD-48 a TD-52, R-3, R-5 y la checklist.
  - Al final, «DECISIONS NEEDED FROM NICOLÁS»: D-1 a D-11, abiertas.
- **Implementado** (regla B, un error de presentación determinista): el tipo de cada evento crítico y sus decisiones
  se muestran en español en el portal docente en español (C-2026-10-02-01).
- **Registrado sin corregir:** TD-53 a TD-59 (`docs/REGISTRO_DEUDA_TECNICA.md`).
- **BLOCKERS propuestos:** TD-48 para los dos casos de trauma; TD-50 para `anaphylaxis_29f`.
- **Nada clínico cambió.** No se desplegó y no se ejecutó la prueba de humo.

| ID | Decisión abierta | Recomendación |
|---|---|---|
| D-1 | TD-48: el E-FAST con sus cinco ventanas | Sí, opción A, antes del piloto |
| D-2 | TD-50: el examen de la anafilaxia sigue al estridor | Sí a la opción 1 (o excluir la 29f) |
| D-3 | Fisiología de la TEP | KEEP FOR PILOT, con aviso docente |
| D-4 | La glosa del shock en la nota 1 de la TEP | Sí, el criterio completo |
| D-5 | El español de las 7 notas de la TEP y del aviso del sangrado | Sí, con los cambios menores |
| D-6 | Las 18 frases de R-4 | Sí; la fila 18, con su verbo |
| D-7 | Las fichas R-2 | Sí; la redacción de la 52m |
| D-8 | La sobrecarga de la 70f que no se ve (TD-53) | (a) aviso y regla para el piloto |
| D-9 | TD-49 con TD-48; TD-51 después | Sí |
| D-10 | R-3: T-2, T-3 y T-4 | Firmar como están |
| D-11 | Los cambios requeridos de las guías (R-5) | Sí, y firmar tras D-1 a D-8 |

## Segunda respuesta al paquete del ciclo 10 (2026-09-30)

**Instrucción docente del 2026-09-30:** avanzar con las decisiones de abajo, conservar lo implementado, limitar el
trabajo a estos puntos y reutilizar escenarios y respuestas guardadas; no reiniciar una auditoría completa. **No es
un ciclo nuevo.** Sin llamadas pagadas, sin regenerar la tanda de encuentros ni los PDF, sin publicar en la app
pública. Los hallazgos nuevos quedan como pendientes, sin ampliar la tarea.

| ID | Decisión docente | Qué se hizo | Registro |
|---|---|---|---|
| P-04 | **B con condiciones.** La lisis puede reperfundir aunque la indicación sea errónea; efecto fisiológico, riesgo hemorrágico y evaluación, separados; ni la mejoría ni el sangrado garantizados por el solo hecho de dar el fármaco; mecanismos existentes, sin sistema probabilístico nuevo ni tasas de PEITHO en la 33f; la indicación se juzga con lo disponible al decidir | La disolución ya no exige la indicación; el sangrado sigue con sus mecanismos; las notas de la sala no prometen mejoría; el aviso del sangrado ya no afirma que cae la presión; el tamizaje dice que lo que siguió no cambia el juicio | C-2026-09-30-06 |
| P-05 | **D, como simplificación explícita.** Sin sangrado de magnitud arbitraria ni beneficio sin respaldo; distinguir completar el esquema de un segundo curso; la primera dosis sigue su curso; registrar la exposición y su riesgo, sin describir una hemorragia no modelada | El registro de cada dosis lleva agente, dosis y curso (versión 3); el resto de un esquema de alteplasa completa la primera dosis; otra dosis es un segundo curso con su exposición y sin efecto propio, dicho como simplificación; cada dosis se lista una vez | C-2026-09-30-07 |
| P-06 | **Corregir la definición.** Incluir la necesidad de vasopresor, distinguir la hipotensión persistente del shock obstructivo (vasopresor necesario, llenado adecuado, hipoperfusión); sin esperar 15 minutos en un shock establecido; no cualquier vasopresor prueba un shock por TEP; revisar la concordancia texto, motor y evaluación; conservar las versiones históricas | La redacción nueva va en D3 y el evento de la 33f, en D3, su alternativa y C1 de la 61m, y en el tamizaje; vive junto a la regla (`pe_obstruction.CRITERION_TEXT`). El motor ya aplicaba esa regla; no modela un estado de llenado aparte, y eso queda escrito. Los encuentros anteriores leen la redacción con que se congelaron | C-2026-09-30-08 |
| P-07 · 75f | **Vista neutral a la llegada** hasta que una imagen aprobada represente su dificultad respiratoria; no borrar V34; sin cambios clínicos; su aprobación queda pendiente para este estado; sin generaciones pagadas | Revisión clínica «pending» de V34 en el paquete de imágenes, bajo la cuenta del docente, después de sus aprobaciones; con las dos revisiones exigidas (piloto) la sala muestra la vista neutral | C-2026-09-30-09 |
| R-2 | **Criterios de dos casos**, no sus fichas. 61m: «aorta no dilatada» no descarta una disección; límites de la motilidad sutil; no exigir reconocer lo que la representación no deja observar. 70f: no penalizar automáticamente un bolo pequeño justificado con reevaluación; evaluar en contexto y por la adaptación; no convertir hallazgos ambiguos en una respuesta obligatoria. Las otras 12, pendientes; sin CONFIRMO ni firma; la misma hoja | Las dos filas C14, sus borradores en español y la hoja R-2 (criterio aprobado; ficha pendiente) | C-2026-09-30-12 |
| R-3 · T-1 | **Evidencia parcial de C3**: reconocer la amenaza, anticipar, pedir ayuda, preparar y reevaluar la vía aérea; no atribuir la ejecución competente ni el cumplimiento completo de C3; usar los niveles existentes, y si no alcanzan sin sobredeclarar, mantener PARCIAL y documentarlo | La fila C3 de TDFC de la 29f observa esa anticipación, dice lo que no observa y la regla de confirmación. TDFC no tiene un nivel parcial por observación: la limitación queda documentada en la fila, en la tabla final y en la hoja T-1 | C-2026-09-30-11 |
| TD-47 | Coherente con una intubación exitosa, sin resolver la anafilaxia ni normalizar la fisiología, sin vía aérea difícil | Con el tubo no se ausculta ni se cobra estridor; el examen lo dice; la reacción sigue | C-2026-09-30-10 |
| R-4 | **Aplicar los ajustes propuestos**, más: la reposición de volumen no sustituye el control del sangrado activo; la FR espontánea o asistida según el motor; «menor esfuerzo» sólo con el estado registrado; «suero glucosado al {n} %», «aumento de volumen» y «dolor a la palpación»; entregar las 18 juntas; sin aprobación global | Las 18 frases finales, juntas, en `docs/revision/R4_FRASES_MOTOR.md`, sin mostrarse. La fila 9 dice que la FR es la de la ventilación asistida: el motor la fija en 12/min durante la asistencia. Una prueba verifica que «menor esfuerzo» nunca aparece junto al agotamiento. Las frases de la sala que ya tenían español usan la terminología acordada | C-2026-09-30-13 |
| TD-46 | **Aprobado**: línea del POCUS entera en inglés mientras no haya traducción aprobada, sin mezclas, sin traducciones nuevas | Implementado en `language.say` para el POCUS y el E-FAST del caso | C-2026-09-30-05 |
| R-5 | **Firma pendiente.** Actualizar las guías con estas decisiones, distinguiendo lo autorizado, lo implementado y lo pendiente | `docs/GUIA_DOCENTE_PILOTO.md` y `docs/GUIA_RESIDENTE_PILOTO.md`, marcadas como borrador | — |

**Pendientes que requieren su revisión:**

- **R-4:** las 18 frases finales (`docs/revision/R4_FRASES_MOTOR.md`).
- **R-2:** las 14 fichas (`docs/revision/R2_POCUS_C14.md`); en la 61m y la 70f sólo se aprobó el criterio.
- **R-5:** las dos guías y su firma.
- **P-07:** una imagen aprobada de la 75f con su dificultad respiratoria, cuando haya presupuesto y revisión.
- **Español activo de las notas nuevas del TEP:** siete frases, como las anteriores del TEP, en `language.py`.
- **Dos preguntas del TEP** (`docs/PULMONARY_EMBOLISM_MAGNITUDES.md`):
  - la pérdida oculta tras cualquier dosis, decidida el 2026-09-20, se conservó. ¿Es un sangrado garantizado
    por el solo hecho de dar el fármaco?
  - en la 33f, con las magnitudes actuales, la disolución pesa más que el sangrado en la presión (la Hb baja
    3,2 g/dL en 105 minutos y la PAS sube). ¿Se ajusta la magnitud?
- **Hallazgos nuevos, pendientes y sin corregir** (registro de deuda):
  - **TD-48:** el E-FAST de la sala muestra sólo la ventana pericárdica; en el 41m no se ve el derrame pleural
    izquierdo. Recomendable antes del piloto.
  - **TD-49:** el SCA lista dos veces cada trombolítico.
  - **TD-50:** el examen de la anafilaxia no evoluciona, y en la 63m el estridor se cobra sin estar en su
    examen.
  - **TD-51:** «increased respiratory effort» junto al agotamiento en el edema sin tratar.
  - **TD-52:** textos menores.

**Verificación:**

- **Pruebas focalizadas** de lo modificado (28 archivos): 1132 pasan, 0 fallan. Cubren:
  - el efecto y el juicio de la lisis, por separado;
  - el esquema inicial frente al segundo curso;
  - el shock sostenido con vasopresor;
  - C3 parcial;
  - el estado tras intubar;
  - la conservación histórica.
- **PostgreSQL 16 local y desechable:** 13 de 13. Incluyen la importación del paquete de imágenes de P-07, el
  banco de imágenes y la integridad del store.
- **TD-46 sobre los eventos guardados de la cosecha anterior**, sin volver a jugar la tanda: 154 líneas del
  POCUS o del E-FAST salían mezcladas; ahora son 0.
- **Regresiones:** 56/56 activas pasan; 10 retiradas, que no se corren.
- **Suite completa en 4 grupos:** TOTAL 6581 = **6497 passed / 83 skipped / 1 xfailed / 0 failed**.
  - Omisiones: 55 por el dolor de llegada, 18 por el encuentro de demostración, que no está en esta copia, y 10 de
    PostgreSQL. Las 10 de PostgreSQL corrieron aparte y pasaron.
  - La xfailed: la brecha conocida del lector «Reviso la vía venosa».
- **Revisión adversarial del diff:** encontró dos cosas, ambas corregidas antes de la suite final:
  - un estado de lisis anterior al 2026-09-29, sin dosis registradas, que habría fallado al registrar otra dosis;
  - marcadores invisibles en el código de TD-46, que ahora se escriben como secuencias de escape.

**Sin cambios:** lector, `validation/`, V3 y los baselines. No hubo llamadas pagadas, ni se regeneró la tanda ni
los PDF. Tampoco hubo despliegue ni publicación.

## Respuesta al paquete del ciclo 10 (2026-09-30)

**Instrucción docente del 2026-09-30** sobre `docs/PAQUETE_DECISIONES_CICLO10.md`: implementar sólo las decisiones
aprobadas explícitamente (P-01, P-06, P-10 y P-11, y la documentación de P-02, P-03, P-08, P-09, P-12 y R-1);
verificar P-04 y P-05 sin implementarlos; preparar el material de P-07 (75f), R-2, T-1 y R-4; esperar en R-5. **No
es un ciclo nuevo** (no es el ciclo 11): sin funciones, casos, arreglos del lector, corpus sintéticos, arquitectura
de POCUS, puntajes ni analíticas nuevas. Sin respuestas externas, sin tocar el lector, el corpus de validación, V3
ni los baselines (`939978a`, `3d942ee`), sin despliegue ni piloto.

| ID | Decisión docente | Qué se hace |
|---|---|---|
| P-01 · DC6 | **A.** La tiamina es una medida complementaria de D3. Su omisión aislada **no baja D3 de 2** si la corrección prioritaria de la hipoglicemia fue adecuada; su administración apropiada **puede contribuir a D3 = 3** cuando el resto del desempeño también lo justifica. Principio: reconocer la tiamina sin penalizar la prioridad correcta de la glucosa. Sólo prospectivo; ninguna evaluación histórica se reinterpreta | Implementar en la declaración de D3 |
| P-02 · DC7 | **A.** No reevaluar de oficio encuentros históricos confirmados; se conservan la evaluación original y su versión y base. Si un encuentro lo necesitara: un mecanismo explícito con motivo, persona, fecha y procedencia, que conserve la original. Sin pantalla nueva para un caso hipotético | Registrar |
| P-03 · DC8 | **A.** 5–60 min y **sólo D4**; no se agrega a D2. Reconocer que la respuesta esperada no ocurrió y adaptarse a una vía fallida es evidencia de reevaluación y adaptación; la misma conducta no se cuenta dos veces | Registrar (es lo vigente) |
| P-04 | **Dirección conceptual B, sin implementar.** El fármaco no deja de actuar porque la indicación fue errónea: una lisis no indicada puede reducir la obstrucción y causar daño y sangrado; la mala decisión se refleja en D3, C1, el evento de seguridad y el balance riesgo/beneficio, no en una farmacología artificial. Antes, verificar la evidencia | Verificar y volver con una recomendación |
| P-05 | **B provisional, sin implementar.** Hipótesis: segunda dosis → sin beneficio de reperfusión adicional automático + riesgo de sangrado adicional; sin suponer, sin evidencia, «exactamente un sangrado completo más» | Verificar y volver con una recomendación |
| P-06 | **B.** Redacción prospectiva «Obstructive shock attributable to the PE, or sustained hypotension (SBP < 90 mmHg for 15 consecutive minutes).» (en español: «Shock obstructivo atribuible al TEP, o hipotensión sostenida (PAS < 90 mmHg durante 15 minutos consecutivos).») en D3, C1 y TDFC. Sin tocar las notas que el tamizaje lee en encuentros antiguos ni el motor | Implementar |
| P-07 · 54f | **A.** Vista neutral hasta que exista una imagen clínicamente apropiada, revisada por personas y aprobada; no se genera ninguna ahora | Registrar |
| P-07 · 75f | **Sin decidir:** el docente revisará V34 | Preparar V34 y su contexto |
| P-08 | **A por ahora.** «No documentado» en `asthma_24f`, `anaphylaxis_29f`, `pulmonary_embolism_33f` y `pneumonia_46f` cuando no hay información escrita; no se inventan FUM, embarazo, adherencia anticonceptiva ni resultado; la prueba de embarazo queda pedida y sin resultado modelado. TD-22 no se reabre | Registrar |
| P-09 | **B**, para cuando se implemente (Fase 2): las leen los docentes autorizados y el administrador, nunca un residente; cada nota conserva autor y fecha y hora; no modifican la rúbrica, el radar, Objective Progress, la evidencia ni los eventos de seguridad; no son unidades de evidencia | Registrar |
| P-10 | **A como regla técnica de permisos.** Con la cuenta del residente inactiva, el docente sigue inspeccionando el registro histórico con sus permisos normales; el portafolio completo para entregar al exusuario lo prepara y descarga **sólo el administrador**; nada del historial se borra ni cambia | Implementar, con pruebas |
| P-11 | **B.** Los 10 scripts, retirados con su motivo y conservados; cada script queda activo o retirado con motivo; los informes dicen «56/56 activas pasan · 10 retiradas», no «56/66» | Implementar |
| P-12 | **B por ahora.** Las 392 guías siguen en inglés (sólo las leen docentes; mucho trabajo de revisión; riesgo de divergencia; poco valor para el primer piloto). Si el piloto muestra que afecta la usabilidad: A o C | Registrar |
| R-1 · DC9 | **Diferida.** Las 36 filas siguen propuestas, pendientes de revisión humana y sin exponerse; las nueve composiciones no se habilitan | Registrar |
| R-2 · TD-04 | **Revisión humana prioritaria antes del piloto**, caso por caso, no en bloque | Preparar la hoja de los 14 |
| R-3 | **No se firman las cuatro en bloque.** T-1 primero; T-2, T-3 y T-4 siguen provisionalmente como están, sin firma final | Preparar el brief de T-1 |
| R-4 | Primero las 18 frases del motor que ve el residente; ninguna se activa. Los 67 textos de C14 después | Preparar la hoja de las 18 |
| TD-46 | Sigue abierto. No mostrar traducciones híbridas si hay una forma segura de dejar el texto entero en inglés hasta que se apruebe su traducción; sin traducciones nuevas automáticas; se puede proponer un arreglo de presentación «todo en inglés hasta aprobar» que no cambie contenido clínico | Proponer, no implementar |
| R-5 | Pendiente de revisión humana; la firma, después de resolver P-07 (75f), sobre las guías finales | Esperar |
| IA del primer piloto | Sin IA automática durante el encuentro: determinista y con casos offline, sin generación automática de imágenes, sin modificación de casos por IA y sin interpretación automática por IA | Sin cambios |
| Validación externa | No tocar el lector, el corpus de validación, V3 ni los baselines; no abrir respuestas externas; esperar «BEGIN EXTERNAL VALIDATION INGESTION» | Sin cambios |

### Resultado (2026-09-30)

**Implementado, sólo en encuentros nuevos donde corresponde:**

- **P-01**, C-2026-09-30-01: la declaración de D3 de las configuraciones con déficit de tiamina.
- **P-06**, C-2026-09-30-02: la redacción en D3 y el evento de la 33f, y en D3 y la fila C1 de TDFC de la 61m. El
  motor, sus notas y el tamizaje no cambian; la instantánea 1.0 sigue igual para los registros antiguos.
- **P-10**, C-2026-09-30-03: el ZIP completo de una cuenta inactiva, sólo para el administrador; el docente sigue
  inspeccionando.
- **P-11**, C-2026-09-30-04: `RETIRED_REGRESSIONS` con su motivo y una prueba de «activo o retirado».

**Registrado:** P-02, P-03, P-08, P-09, P-12 y R-1.

**Preparado:**

| Qué | Dónde |
|---|---|
| P-04 y P-05 | `docs/VERIFICACION_P04_P05.md` |
| P-07 (75f) | `docs/revision/P07_75F_V34.md` |
| R-2 | `docs/revision/R2_POCUS_C14.md`: 12 CONFIRM, 2 DISCUSS |
| T-1 | `docs/revision/T1_ANAPHYLAXIS_29F_C3.md`: recomienda un YES acotado, o NO |
| R-4 | `docs/revision/R4_FRASES_MOTOR.md`: 11 aprobar, 7 cambiar |
| TD-46 | Una propuesta de presentación, en el registro de deuda |

**Nuevo en el registro de deuda, sin corregir:** TD-47, el estridor que sigue después de intubar en la 29f.

**Verificación:**

- Pruebas focalizadas primero.
- **Regresiones:** 56/56 activas pasan; 10 retiradas, que no se corren.
- **Suite completa en 4 grupos, sobre el candidato:** TOTAL 6531 = **6448 passed / 82 skipped / 1 xfailed / 0
  failed**.
  - Las 82 omisiones son las mismas del cierre del ciclo 10: 55 por el dolor de llegada, según lo que describe
    cada caso; 18 por el encuentro de demostración, que no está en esta copia; y 9 de PostgreSQL sin base.
  - La xfailed: la brecha conocida del lector «Reviso la vía venosa».
- La única falla de la corrida focalizada fue una lista esperada de diferencias con la instantánea 1.0. Era
  consecuencia directa de P-06, y la lista se actualizó con su referencia.

**Sin cambios:** lector, `validation/`, V3 y los baselines. No hubo llamadas al proveedor, despliegue ni piloto.

## Ciclo 10 (2026-09-29) — cerrado

**Aprobación docente, 2026-09-29:** «apruebo todo, incluir todo lo propuesto», sobre la propuesta del ciclo 10
(formato §18 A–K). Entra todo, **también C10-09**, que la propuesta condicionaba a un «B» explícito: DC4-F queda
**aprobada en la opción B mínima** (el glucagón y el octreótido dados por la cánula infiltrada se absorben desde el
tejido como una dosis subcutánea; el motor ya les da ese perfil, así que ninguna trayectoria cambia y cambia sólo
el registro técnico).

**Objetivo:** dejar el piloto formativo listo para desplegarlo, operarlo y respaldarlo con datos reales, y reunir las
decisiones abiertas en un solo paquete, sin tocar el lector, los baselines ni la validación externa.

| ID | Tarea | Estado |
|---|---|---|
| C10-00 | Apertura y conciliación de registros (TD-19, resto de TD-31, TD-41; prueba que cruza TD y correcciones) | **Hecho** (`test_debt_register_cites_its_corrections.py`) |
| C10-01 | Diagnóstico de los 10 scripts de regresión heredados (sin cambios) | **Hecho**: ninguno está en `ACTIVE_REGRESSIONS` (56/56 activos pasan); a decisión en P-11 |
| C10-02 | Paquete único de decisiones y revisiones docentes | **Hecho**: `docs/PAQUETE_DECISIONES_CICLO10.md` (P-01 a P-11, R-1 a R-5), hojas en `docs/revision/` |
| C10-03 | Integridad del store: TD-18 sin I-F18 | **Hecho** (C-2026-09-29-24): I-F09 una transacción, I-F10 errores registrados por clase, I-F06 e I-F19 claves únicas sin bloquear una base con repeticiones (`check_database.py --integrity`), I-F20 filas ilegibles señaladas; PostgreSQL en C10-05 |
| C10-04 | Fase 2, paso 1: auditoría de activar y desactivar cuentas (TD-44) | **Hecho** (C-2026-09-29-25): estado, rol y año con autor y hora; sólo el administrador lo lee; PostgreSQL en C10-05 |
| C10-05 | Respaldo y restauración probados en SQLite y PostgreSQL | **Hecho**: `docs/RESPALDO_Y_RESTAURACION.md`; simulacro idéntico en SQLite y PostgreSQL 16 (33 tablas, 691 filas, encuentros releídos, nada cambia al abrir); `tools_backup_drill.py --compare` para una restauración real; C10-03 y C10-04 pasan en PostgreSQL |
| C10-06 | Runbook, preflight y guías del piloto | **Hecho**: `docs/RUNBOOK_PILOTO.md`, `tools_pilot_preflight.py` (sin imprimir secretos; 7 pruebas), guías del residente y del docente (revisión R-5 del paquete) |
| C10-07 | Pantallas del piloto: TD-42, TD-43, TD-38 | **Hecho** (C-2026-09-29-26): encuentros parecidos numerados; ZIP vencido retirado; clave duplicada fuera; radar de las tarjetas a su ancho; «Through» de ancho medio; evidencia bajo la ficha (sin clic extra, §154DV); un plan solo se dice registrado, sin pregunta genérica. El lector no cambia |
| C10-08 | Español de las frases del motor (resto de DF-23 fila 11) y TD-07; nada activo sin aprobación | **Hecho**: cosecha sin proveedor de la sala (`tools_engine_spanish.py`, 31 corridas); 18 frases del motor y 67 textos de C14 como borradores inactivos (`spanish_drafts.py`), revisión R-4 en `docs/revision/ES_BORRADORES.md`; P-12 (el resto de TD-07) y TD-46 (el POCUS mezclado de un relato sin aprobar) al paquete y a la deuda |
| C10-09 | DC4-F, opción B mínima (aprobada) | **Hecho** (C-2026-09-29-27): por la cánula fallida el glucagón y el octreótido actúan como una dosis subcutánea; ninguna trayectoria cambia (el motor no distingue su inicio por vía) y el registro técnico lo dice; probado en las 6 configuraciones con vía fallida |
| C10-10 | Deuda menor: TD-05, TD-10, TD-03 y, si queda tiempo, TD-09 | **Hecho** (C-2026-09-29-28): el commit en cada turno del Trace; vínculos de marco congelados con la observación; la cola docente lee la base una vez por encuentro (2,9 → 0,3 ms); TD-05 ya no aplicaba y una prueba lo mantiene |
| C10-11 | Cierre: suite completa, regresiones, prueba de humo, docs, commit, push y reporte | **Hecho**: suite completa en 4 grupos sobre `351dcab`, **TOTAL 6507 = 6424 passed / 82 skipped / 1 xfailed / 0 failed** (las 5 omisiones nuevas son las pruebas de PostgreSQL de C10-05 sin base; la xfailed es la brecha conocida del lector «Reviso la vía venosa»). La primera corrida, sobre `5bc7162`, dio 1 falla: dos cambios de cuenta del mismo segundo se listaban en cualquier orden (código de C10-04); se corrigió en `351dcab` con una prueba que fallaba sin el arreglo. Regresiones: 56/56 activas; las 10 heredadas siguen inactivas (P-11). Prueba de humo del piloto en `351dcab`: sin cambios sin commit, 0 intentos de llamar al proveedor. Lector, `validation/`, V3 y los baselines sin cambios en el ciclo |

**Fuera del ciclo:** el lector (TD-45, KD-02·TD-35, KD-15, «suero glucosado», TD-14, TD-37, TD-40); la validación
externa (nada se abre, lee ni procesa, y la ingesta no se prepara); V3 y los baselines; todo cambio clínico sin
decisión; aprobar DC9, TD-04, las dudas de TDFC, el español, las guías o fotos; llamadas a proveedores de IA,
imágenes, videos y AI Longitudinal Review; los pasos 2 a 4 de la Fase 2; despliegue, PR, merge y release; datos
reales y nombres de médicos.

## Estado posterior a V3 (2026-09-29) — ciclo cerrado

**El ciclo posterior a V3 se cerró formalmente el 2026-09-29** con las decisiones del mensaje de cierre (DF-23 filas 6, 7 y 8; el español de `acs_70f_left_main`; la vía de llegada neutra; la IA del primer piloto; los baselines). No se abrió otro ciclo. Ninguna decisión abierta sale de esta tabla por no haber entrado en el ciclo.

Instrucción docente del 2026-09-29 que cierra las decisiones clínicas analizadas
después de V3 y su ampliación no clínica. **Implementado no es validado:**
nada de esto tiene todavía revisión clínica externa. Detalle clínico:
`docs/POST_V3_CAMBIOS_CLINICOS.md`.

| ID | Decisión | Alcance | Estado | Dependencia | Evidencia | Criterio de cierre |
|---|---|---|---|---|---|---|
| TEP · D revisada | Un shock obstructivo atribuible al TEP indica la reperfusión sin espera; la hipotensión sin hipoperfusión exige 15 min consecutivos; la noradrenalina sola no crea indicación | Familia TEP, banco y generados; encuentros nuevos | **IMPLEMENTADO** | — | C-2026-09-29-10; `test_pe_obstruction.py`, `test_pe_thrombolysis_screening.py` | Revisión clínica externa |
| TEP · 61m | La lisis en 61m es indicada desde la llegada por shock obstructivo | `pulmonary_embolism_61m` | **IMPLEMENTADO y verificado** en el motor (98/61 a los 45 min) | — | `docs/PULMONARY_EMBOLISM_MAGNITUDES.md` | Revisión clínica externa |
| TEP · noradrenalina innecesaria | Ya no produce una «hipotensión sostenida» falsa ni vuelve indicada la lisis (33f) | Familia TEP | **IMPLEMENTADO** | — | ídem | Revisión clínica externa |
| TEP · farmacología de la lisis no indicada | Hoy una lisis no indicada no disuelve nada | Familia TEP | **DIFERIDO** | Decisión clínica con fuente | `docs/PULMONARY_EMBOLISM_MAGNITUDES.md` («Qué quedó aparte») | Decisión docente registrada |
| TEP · repetición de dosis | Una segunda dosis se registra como repetición sin efecto propio | Familia TEP | **DIFERIDO** | Decisión de seguridad y efecto | ídem | Decisión docente registrada |
| D3 / C1 / TDFC · «sustained hypotension» | Redacción de las declaraciones aprobadas | Declaraciones de TEP | **PENDIENTE**; no se tocó (la referencia aprobada no cambia) | Decisión de redacción | ídem | Nueva redacción aprobada, sólo para encuentros nuevos |
| DC1 | La conciencia escrita al llegar es la que muestra el motor; se deteriora sólo si la fisiología empeora | Motor de familias; encuentros nuevos | **IMPLEMENTADO** | — | C-2026-09-29-11; `test_arrival_consciousness.py` | Revisión clínica externa |
| DC2 | La cánula de llegada existe y se puede examinar | Hipoglicemia, 12 configuraciones | **IMPLEMENTADO** | — | C-2026-09-29-14; `test_hypoglycemia_lines.py` | Revisión clínica externa |
| DC3 | Una dosis IO válida instala su aguja y llega entera | Hipoglicemia | **IMPLEMENTADO** (el lector no cambió: «IO, then D50» sigue retenido, TD-45f) | — | ídem | Revisión clínica externa |
| DC4 | La falla es de la vía: llega el 15 % de lo que corre por la cánula infiltrada | Hipoglicemia | **IMPLEMENTADO** (variante de b; el 15 % es abstracción docente) | — | ídem | Revisión clínica externa |
| DC4-F | Glucagón y octreótido por la cánula infiltrada | Hipoglicemia | **DECIDIDA (B mínima) e IMPLEMENTADA** (C-2026-09-29-27): actúan como una dosis subcutánea | — | `docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md`; `test_dc4f_failed_line_as_subcutaneous.py` | — |
| DC5 | Una infusión que corría pasa a la vía siguiente | Hipoglicemia | **IMPLEMENTADO** | — | C-2026-09-29-14 | Revisión clínica externa |
| DC6 | Peso de la tiamina en D3 | Hipoglicemia | **DIFERIDO** | Decisión docente | ídem | Peso decidido |
| DC7 | Reevaluar evaluaciones confirmadas de la 54m | Evaluaciones ya confirmadas | **DIFERIDO**; nada confirmado se tocó | Decisión docente y pantalla de reevaluación | ídem | Decisión registrada |
| DC8 | Ventana de la oportunidad de D4 | Hipoglicemia | **DIFERIDO** | Decisión docente | ídem | Ventana decidida |
| DC9 | Filas TD/F/C de las composiciones: las del origen como propuesta pendiente | 9 composiciones, 36 filas | **PROPOSED · PENDING HUMAN REVIEW · NOT EXPOSED TO RESIDENTS**; nada se aprueba automáticamente; la referencia TDFC confirmada no cambia | Revisión docente de 36 filas | C-2026-09-29-19; `test_tdfc_composition_proposals.py` | Cada fila revisada con firma |
| «Suero glucosado» sin concentración | ¿10 % o preguntar? | Lector | **DIFERIDO** (lector congelado) | Ciclo del lector | `docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md` G | Decisión y ciclo aprobado |
| DF-23 · fila 11 | Primer minuto, TEP antes de 15 min, VCI y VI en la HDA, traducción de las frases del modelo | Varios | **Tres partes IMPLEMENTADAS** (DC1, D revisada, POCUS de la HDA C-2026-09-29-12); **la traducción de las frases del modelo: borradores en R-4 (C10-08), sin activar** | — | POST_V3 §2–§3; `docs/revision/ES_BORRADORES.md` | Aprobar R-4 |
| DF-23 · 4b | Grado del VI de `acs_70f_left_main` | 1 caso | **IMPLEMENTADO** (leve; C-2026-09-29-15) | — | `test_acs_left_main_arrival.py` | Revisión del español (abajo) |
| DF-23 · fila 6 | **B:** la pared reperfundida queda aturdida; a lo sumo «mildly reduced» dentro del encuentro | Familia SCA | **IMPLEMENTADO** (sólo la descripción; lv_function, circulación y tiempos iguales) | — | C-2026-09-29-20; `test_reperfused_wall_stays_stunned.py` | Revisión clínica externa |
| DF-23 · fila 7 | **A:** FA en monitor y ECG de `anaphylaxis_63m_betablocked`, FC 64 | 1 caso | **IMPLEMENTADO**; fisiología idéntica; el caso sigue en el piloto | — | C-2026-09-29-21; `test_betablocked_anaphylaxis_rhythm.py` | Revisión clínica externa |
| DF-23 · fila 8 | **A modificada:** embarazo/FUM/LMP/menstruación como tema propio, nunca inicio de síntomas; sin dato, «Not documented.» / «No documentado.»; sin β-hCG | Historia de todos los casos | **IMPLEMENTADO**; TD-22 sin cambio | — | C-2026-09-29-22; `test_pregnancy_history_topic.py` | Revisión clínica externa |
| `pulmonary_embolism_33f` · embarazo | Sin historia inventada: «No documentado» hasta decidir qué contiene el caso; prueba de embarazo solicitada y sin resultado modelado | 1 caso | **IMPLEMENTADO** (comportamiento por defecto) | Decisión docente sobre el contenido del caso | ídem | Decisión registrada sobre embarazo/FUM del caso |
| `acs_70f_left_main` · español | Aprobada: «Contracción globalmente levemente disminuida sin un defecto focal único.» = «Globally mildly reduced contraction without a single focal defect.» | 1 caso | **APROBADO** (2026-09-29) y fijado por prueba; `lv_function` 0,82 y el shock sin cambio | La sala usa el español de un caso cuando su versión está aprobada en la base desplegada (tablero docente) | `test_acs_left_main_arrival.py` | Aprobación de la versión del caso en la base desplegada |
| Hipoglicemia · vía de llegada | Neutra: «Peripheral IV in place in the left forearm.» / «Vía venosa periférica instalada en el antebrazo izquierdo.»; sin inventar paramédicos | 12 configuraciones | **IMPLEMENTADO** | — | C-2026-09-29-23; `test_arrival_line_is_neutral.py` | — |
| Imágenes · V34 (`pulmonary_edema_75f`) y `bradycardia_bb_54f` (DF-23 fila 2) | Foto de llegada | 2 casos | **PENDIENTE**; nada generado ni aprobado; 75f muestra V34 (aprobada, mismo contrato), 54f la vista neutral | Decisión docente | `docs/IMAGENES_DECISIONES_CLINICAS.md` | Decisión registrada |
| KD-31 | El tamizaje cita el tratamiento previo como contexto | Tamizaje | **IMPLEMENTADO** | — | C-2026-09-29-18; `test_prior_treatment_in_screening.py` | Revisión docente del uso |
| §154AB · foco de aprendizaje | Oculto al residente hasta la revisión docente | Páginas del residente | **IMPLEMENTADO** | — | C-2026-09-29-16 | — |
| TD-41 · traducciones | Sólo el pedido del lector traduce; nada al abrir | Páginas y PDF | **IMPLEMENTADO** | — | C-2026-09-29-17 | — |
| Baseline inglés | V3 `3d942ee` | Validación externa inglesa | **DECIDIDO, REGISTRADO y CONFIRMADO** | — | `validation/BASELINES.md` | — |
| TD-45 · deuda del lector | Las ocho brechas se mantienen documentadas; el lector no se reabre | Lector congelado | **REGISTRADO**; se comprobará cuáles aparecen en el lenguaje médico externo | Validación externa | `test_reader_gaps_registered.py` | Medición externa y ciclo del lector aprobado |
| KD-02 · TD-35 | Lo que una lista nombra sin verbo y el lector no conoce se pierde sin aviso | Lector congelado | **PENDIENTE** | Validación externa | TD-45a; `validation/KNOWN_DEFECTS_V3.md` | Decisión tras medir el lenguaje externo |
| KD-15 | Un fluido nombrado sin verbo («IV fluids 1 L») se retiene | Lector congelado | **PENDIENTE** | Validación externa | TD-45b | Decisión tras medir el lenguaje externo |
| Roles · Fase 2 | TD-44 → notas privadas → descarga selectiva e inactivos → AI Longitudinal Review a pedido | Roles | **ORDEN REGISTRADO**; nada implementado | Presupuesto y decisiones de acceso | `docs/EXPERIENCIA_POR_ROL.md` | Cada paso con pruebas de permisos |
| TDFC · cuatro dudas residuales | Declaraciones aplicadas como estaban | 4 filas | **PROVISIONAL, no validado** | Revisión docente | `tdfc/TDFC_TABLA_FINAL.md` | Cada fila confirmada o cambiada |
| TD-04 · POCUS del banco | POCUS de los 14 casos C14 YES | 14 casos | **PENDING HUMAN CLINICAL REVIEW**; no se aprueba automáticamente; no se generan imágenes ni videos | Revisión docente | — | Cada caso confirmado |
| Piloto formativo | Piloto limitado, formativo, con supervisión docente | 31 casos del banco; sin composiciones, casos por IA ni PS001/PS002 | **TECHNICALLY READY WITH CONDITIONS** | A. desplegar el candidato y la configuración aprobados; B. prueba de humo en el entorno desplegado; C. autorización docente explícita | `docs/READINESS_PILOTO_FORMATIVO.md`; `tools_pilot_smoke.py` | A, B y C cumplidas; nunca se inicia automáticamente |
| IA durante el encuentro (primer piloto) | **CLINICAL ENCOUNTER AI = OFF**: sin llamadas automáticas; sin generar una foto nueva al abrir el caso; banco de casos, fotos aprobadas y motor determinista | Piloto | **DECIDIDO** (`MRS_OFFLINE_CASES=1`: 0 llamadas medidas) | — | Prueba de humo | Otra decisión docente para habilitar algo |
| IA posterior al encuentro | Propuesta de rúbrica, análisis del Trace, AI Longitudinal Review y traducción, **cada una por separado** | Piloto | **NO AUTORIZADA**; ninguna se habilita automáticamente | Decisión docente, una por una | — | Decisión por función |
| Foco de aprendizaje | El residente lo ve después de la revisión docente; el docente, durante la revisión | Páginas | **CONFIRMADO** (2026-09-29) | — | C-2026-09-29-16 | — |
| Baselines de validación externa | ES = `939978a` (SPANISH PILOT BASELINE); EN = V3 `3d942ee` | Validación externa | **CONFIRMADOS FORMALMENTE** (2026-09-29); no cambian después de leer respuestas | — | `validation/BASELINES.md` | — |
| V3 | `3d942ee` congelado; todo lo posterior es desarrollo posterior a V3 | Motor | **CONGELADO**; el HEAD no es el motor de la medición externa | — | `validation/BASELINES.md` | — |
| Validación externa | Validación del lenguaje de médicos externos | ES y EN | **ESPERANDO** «BEGIN EXTERNAL VALIDATION INGESTION»; nada se abre, lee ni procesa | Instrucción explícita | `docs/VALIDACION_EXTERNA_PREPARACION.md` | Instrucción recibida |
| Fuera de alcance | DF-15, DF-25, DF-14, DF-12, DF-17, DF-4, DF-18, DF-9, DF-11, DF-5, biblioteca POCUS | — | **Sin cambio** | — | — | — |

## Pendientes al cierre del ciclo 9 (histórico)

| ID | Clase | Tema | Estado al cierre del ciclo 9 |
|---|---|---|---|
| Baseline inglés | NEEDS NICOLÁS · METHODOLOGICAL | Qué commit mide los documentos ingleses | **Recomendado: V3.** Se elige antes de leer cualquier respuesta inglesa (`validation/BASELINES.md`) |
| Piloto formativo | NEEDS NICOLÁS | Autorizar un piloto formativo controlado con residentes | A (motor) = YES; B (fidelidad externa) = NOT YET MEASURED. Falta la prueba de humo en la base real (`READINESS_PILOTO_RESIDENCIA.md`) |
| Español de `acs_70f_left_main` | NEEDS NICOLÁS · CLINICAL REVIEW | Su POCUS cambió (fila 4a) | Si su texto en español estaba aprobado en la base desplegada, vuelve a esperar su revisión |
| DF-23 · 4b, 6, 7, 8 | CLINICAL REVIEW | Inconsistencias clínicas | Sin cambio (§19) |
| KD-02 · TD-35 | NEEDS NICOLÁS | Lo que una lista nombra sin verbo y el lector no conoce | ¿Preguntarlo? Hoy se pierde sin aviso mientras lo demás corre |
| KD-15 | NEEDS NICOLÁS | Un fluido nombrado en palabras sin verbo («IV fluids 1 L») | Sin cambio |
| KD-31 | NEEDS NICOLÁS · METHODOLOGICAL | El tamizaje de eventos críticos no cita un tratamiento previo registrado | Nuevo. El docente lo ve en el Trace; ningún evento se acepta solo |
| Medidas combinadas | CLINICAL REVIEW | Resto de TD-31: «direct pressure with packing» suma el efecto de dos medidas | Sin cambio |
| DC3 (mitad de la dosis) | CLINICAL REVIEW | Una dosis «IO» sin instalar la IO | Sin cambio |
| TDFC · dudas | NEEDS NICOLÁS · CLINICAL REVIEW | Las cuatro dudas residuales de las filas claras | Aplicadas como estaban; cada una se cambia en una línea (`tdfc/TDFC_TABLA_FINAL.md`) |
| TDFC · composiciones | NEEDS NICOLÁS | ¿Las composiciones de hipoglicemia heredan TD/F/C de su origen, como C14 (L-F07 B)? | Hoy conservan la transición |
| DF-15 | WAITING FOR EXTERNAL DATA | Piloto del validation corpus, español e inglés | Ingesta lista y ensayada sin respuestas reales; nada llegó ni se abrió |
| TD-14 (KD-28) · KD-16 a KD-31 | HIGH (fricción) · MEDIUM · LOW | Lo que queda del lector y de la sala al congelar V3 | Estado de V3 (`validation/KNOWN_DEFECTS_V3.md`); el piloto lo mide |
| Biblioteca POCUS | FUTURE ARCHITECTURE | Videos reales, adquisición y reconocimiento en la imagen | `ARQUITECTURA_POCUS_OBJETIVO.md`. No es deuda ni bug |
| DF-25 · DF-14 · DF-12 · DF-17 · DF-4 | — | Brechas del banco · PARTIAL · transición · *override* · C2 | Sin cambio |
| DF-18 · DF-9 · DF-11 · DF-5 | — | Multisource · −3 · residuos menores · C15 | Registrados, sin acción |
| Roles · foco de aprendizaje | NEEDS NICOLÁS · METHODOLOGICAL | El foco de aprendizaje (el desafío) se muestra al residente al cerrar el encuentro, antes de la revisión docente; §154AB pide no mostrar el objetivo antes de la revisión | Sin cambio. `docs/EXPERIENCIA_POR_ROL.md` |
| Roles · Fase 2 | NEEDS NICOLÁS | AI Longitudinal Review (especificada), notas privadas docentes, auditoría de activar/desactivar, descarga selectiva del portafolio, portafolio de cuentas inactivas | Diferidos con su razón. `docs/EXPERIENCIA_POR_ROL.md` |
| Roles · traducción automática | NEEDS NICOLÁS | Con clave y documento en español, la revisión del encuentro y los PDF docentes piden traducción al cargar la página (previo al ciclo 9; §154FT) | «My progress» ya no lo hace; el resto sin cambio |

**Cerrados en el ciclo 9:** DF-20 (sin cambios), DF-23 · 4a (aplicada), TD-33
(aplicado) y TD-39, TD-34 y TD-36 (corregidos).

**Fase de roles y pantallas, posterior a V3 (§154A–§154GL):** en commits propios,
sin tocar el motor ni la metodología. Permisos en los stores
(`docs/MATRIZ_PERMISOS_ROLES.md`), cohorte docente con tarjetas, vista del
residente, inicio del residente con la asignación ciega, «My progress» en seis
vistas, «My encounters», portafolio con ZIP sin llamadas de IA, estado de las
cuentas para el Admin, y la AI Longitudinal Review especificada y diferida
(`docs/AI_LONGITUDINAL_REVIEW_SPEC.md`). Resumen, diferidos y revisión visual en
`docs/EXPERIENCIA_POR_ROL.md`.

## Cierre del ciclo 9 (2026-09-29)

El ciclo cumplió el alcance registrado en su apertura. El motor quedó congelado
como **DEVELOPMENT PRE-VALIDATION BASELINE V3** (`3d942ee`,
`validation/BASELINES.md`). Ninguna respuesta externa se abrió, leyó ni
procesó. El detalle está en los documentos citados.

### DECIDED + IMPLEMENTED

| Ítem | Qué quedó | Registro |
|---|---|---|
| TD-39 | Un alta para más tarde (con su plazo, tras una observación o un resultado, o con una condición) es un **plan de destino**: se registra con las palabras del residente, no cierra el encuentro, no es un alta ejecutada para los eventos críticos, y el Trace dice «plan de destino; no se realizó ahora». El alta inmediata, negada, preguntada o de otro servicio no cambia | C-2026-09-29-01, -07 |
| TD-34 | Una reevaluación en horas espera sus minutos: 1 h = 60 en el lector, el motor, el reloj y el Trace (una sola fuente, `delay_min`). Lo que no se lee se pregunta, nunca se toma como «ahora» | C-2026-09-29-02, -07 |
| TD-36 | Lo recibido antes de la atención del residente es **historia**: se registra con qué, dosis, vía, quién y cuándo, y nunca se da de nuevo ni es orden del residente | C-2026-09-29-03, -07 |
| TD-33 | En la regla de sobrecarga transfusional en trauma, sólo la sangre repone el déficit; el cristaloide conserva su efecto hemodinámico y la sobretransfusión real se sigue detectando | C-2026-09-29-04 |
| DF-20 | **CERRADO, sin cambios** en el caso. Las filas TDFC de `acs_54m_inferior` quedaron declaradas (TD1, F1, C1 YES; C3 NO), ninguna sobre el POCUS. TDFC completo en 31 casos: TD1 26/5, F1 26/5, C1 19/12, C3 10/21; tabla y matriz regeneradas | C-2026-09-29-05 |
| DF-23 · 4a | Aplicado: «Scattered B-lines at both bases; no diffuse B-line pattern», con su borrador en español. No cambian el desafío, el objetivo, los eventos críticos ni TDFC | C-2026-09-29-06 |
| Ingesta externa | Inventario RAW con SHA-256, metadatos por nombre, copia de trabajo que sólo limpia propiedades, frontera de respuesta, vacíos y parciales, duplicados y conflictos, decisiones de una persona, preparación por idioma, procedencia de la anotación y de cada corrida (§132), y las marcas SILENT_LOSS, FALSE_EXECUTION, TRACE_DISTORTION y APPROPRIATE_CLARIFICATION | `VALIDACION_EXTERNA_PREPARACION.md` |
| Defectos conocidos de V3 | Estado propio (versión 3), sin reescribir la lista del piloto; TD-39, TD-34 y TD-36 se pueden etiquetar en una corrida de `939978a` como conocidos al analizar (§67) | `validation/KNOWN_DEFECTS_V3.md` |
| Principio de saturación | Charter, addendum A3 (§116–§117) | — |

### Validación de las correcciones

- **Pruebas focalizadas y controles negativos:** las pruebas del ciclo (`test_cycle9_prevalidation_hardening.py`, 198 casos, EN/ES) cubren altas inmediatas, planes, negadas, preguntadas y de otro servicio; intervalos; tratamiento previo y sus controles; la ejecución, el cierre del encuentro, el Trace y la entrada de los eventos críticos. Los 75 archivos de prueba del lector: 2887 pasan.
- **Revisión adversarial independiente** (sin leer el código del lector):
  - 130 frases preregistradas: ninguna fila peor que el ciclo 8; 0 CRITICAL y
    1 HIGH, anterior al ciclo y corregido después («Discharge at 1800»);
  - 54 frases posteriores: 3 filas peores que el ciclo 8 (dos corregidas; la
    tercera queda como plan por diseño, KB-04) y fallas de la misma clase,
    corregidas según §90 (C-2026-09-29-07);
  - lo demás que halló es anterior al ciclo y quedó como deuda (KD-16 a KD-31).
- **Revisión pequeña de las correcciones del triage:** 70 frases preregistradas,
  0 CRITICAL y 8 HIGH. Siete de las ocho se corrigieron (C-2026-09-29-08):
  seis eran regresiones de las correcciones del triage (DN01–DN04, DA01 y
  OR19) y una, anterior al ciclo, es de la clase de TD-39 (DA02). La octava
  (OR16) registra una historia verdadera y pierde el «repetir», que es KD-21.
  También se corrigió una regresión MEDIUM (DN08). Al volver a correr todas
  las frases de las dos revisiones y los controles, cambiaron exactamente esas
  8 filas.
- **Comparación con el lector anterior:** cada frase se leyó con el lector del
  ciclo 8 y con el V2; los 16 cambios frente a lo revisado son las correcciones
  buscadas.
- **Suite completa y regresiones sobre V3:** 6134 pasan, 77 omitidas, 1 xfail, 0 fallas sobre `3d942ee`; 56/56 regresiones.

### DECIDED + DEFERRED

- **Todo lo MEDIUM y LOW hallado** queda como deuda técnica con su
  identificador del estado de V3 (§90, §112). El lector no se toca después de
  V3.
- **TD-14, TD-29, TD-30 y TD-40** esperan los datos externos (§20).

### NEEDS NICOLÁS

1. **El baseline inglés,** antes de leer respuestas: recomendado **V3**
   (`validation/BASELINES.md`, «Recomendación del baseline inglés»).
2. **Autorizar, o no, el piloto formativo controlado:** A = YES, B = NOT YET
   MEASURED.
3. **El español de `acs_70f_left_main`,** si estaba aprobado en la base
   desplegada: volver a revisarlo.
4. **Sin cambio:** DF-23 (4b, 6, 7, 8), KD-02 y TD-35, KD-15, la regla de
   medidas combinadas, DC3, las dudas de TDFC y las composiciones.
5. **Nuevo, cuando pueda:** KD-31, si el tamizaje debe citar un tratamiento
   previo registrado.

### WAITING FOR EXTERNAL DATA

- Los documentos de los médicos, español e inglés, como dos corpus. Nada llegó
  ni se abrió en el ciclo 9. SEALED no se tocó.

### Baselines

- **SPANISH PILOT BASELINE `939978a`:** intacto (fijo, §116). No cambiaron sus
  18 DOCX, sus manifiestos ni `PILOT_BASELINE.md`; la guía de anotación y el
  README de herramientas del piloto ganaron texto de proceso, sin etiquetas
  nuevas.
- **ENGLISH VALIDATION BASELINE `ec1c77f`, V1 y V2:** intactos.
- **V3 `3d942ee`:** registrado en `validation/BASELINES.md`, no en
  `validation/baselines.json` hasta que el docente lo elija.

## Apertura del ciclo 9 (2026-09-29)

**La instrucción, al aprobar el cierre del ciclo 8:**

- «Apruebo el cierre del Ciclo 8. Ya estoy recolectando el EXTERNAL VALIDATION
  CORPUS con médicos de urgencia. Habrá DOS CORPUS INDEPENDIENTES: SPANISH
  EXTERNAL VALIDATION CORPUS y ENGLISH EXTERNAL VALIDATION CORPUS».
- La estrategia cambia a: PRE-VALIDATION HARDENING → FREEZE → EXTERNAL
  MEASUREMENT → ERROR ANALYSIS → DATA-DRIVEN DEVELOPMENT.

**Decisiones registradas (no se vuelven a pedir):**

| Decisión | Qué dice | § |
|---|---|---|
| DF-20 | **CERRADO, sin cambios:** un compromiso fisiológico del VD puede coexistir con un POCUS cualitativo de urgencias normal o no diagnóstico. No cambian el tamaño ni la función del VD, la VCI ni el modelo hemodinámico; C14 sigue NO. Las filas TDFC de `acs_54m_inferior` dejan de esperar y usan la decisión TDFC ya aprobada | §16, §17, §46, §47 |
| TD-33 | **Aprobado:** para la regla de sobrecarga transfusional en trauma, sólo la sangre repone el déficit hemorrágico; cambio mínimo | §14, §15, §45 |
| DF-23 · 4a | **Autorizado si es claro:** aplicar el texto propuesto en el ciclo 7 si la única contradicción es «No B-lines» frente a la congestión y no cambia el desafío, el objetivo, los eventos críticos ni TDFC; si no, diferir. 4b, 6, 7 y 8 siguen en la cola | §18, §19, §49 |
| Baseline español | **SPANISH EXTERNAL VALIDATION BASELINE = `939978a`.** «No pedir nuevamente esta decisión.» Los defectos hallados después se etiquetan en el análisis; el baseline no cambia | §23, §66, §116 |
| Baseline inglés | El AI Advisor **recomienda** V2 o V3 al cierre, antes de leer cualquier respuesta inglesa | §24, §65, §115 |
| Principio de saturación | El desarrollo interno con lenguaje sintético llegó a un punto de saturación temporal; la expansión del lector se guía por lenguaje humano independiente | §21 (charter, addendum A3, §116–§117) |
| TD-29, TD-30, TD-40, TD-14 | No se amplían en el ciclo 9, salvo una regresión de TD-39/34/36 | §20 |

**Alcance autorizado (§40):** TD-39, TD-34, TD-36 y TD-33; DF-20 cerrado y las
filas TDFC de `acs_54m_inferior` con la tabla regenerada; DF-23 4a si es claro;
las herramientas de ingesta externa sin leer respuestas reales; el congelamiento
V3 si cumple §111; la documentación; la recomendación del baseline inglés; y,
después de V3, la fase de roles e interfaz (§154A–§154GL) en commits aparte.

**Reglas que siguen:**

- no abrir, buscar ni usar respuestas externas hasta «BEGIN EXTERNAL VALIDATION
  INGESTION»; si aparecen, informar su presencia sin leerlas;
- no guardar respuestas crudas ni nombres de médicos en el repositorio;
- no usar IA para respuestas externas, anotación de referencia, verdad clínica
  ni traducción de respuestas;
- sin cambios en D1–D5, 0–3, −3, eventos críticos, puntaje ajustado, radar,
  confirmación docente, DIRECT/PARTIAL, C4, casos nuevos ni biblioteca POCUS;
- sin otro conjunto ciego interno; después de V3, el lector no se toca;
- sin PR, merge a `main` ni release; push sólo a `clinical-encounter-v0.13`;
- un solo reporte al final, y STOP: no se inicia el ciclo 10.

## Cierre del ciclo 8 (2026-09-29)

El ciclo cumplió el alcance registrado en su apertura. Lo que pide una
decisión quedó fuera y va al reporte final. El detalle está en los documentos
citados.

### DECIDED + IMPLEMENTED

| Ítem | Qué quedó | Registro |
|---|---|---|
| TDFC | TD1, F1, C1 y C3 declarados caso por caso en 30 casos, con el modelo de C14 (TD1 25 YES / 5 NO, F1 25/5, C1 18/12, C3 10/20). TDFC-6 sigue la recomendación. `acs_54m_inferior` espera DF-20 y conserva la transición | C-2026-09-28-17 · `tdfc/TDFC_TABLA_FINAL.md` |
| TD-29 | «Cuando/when/once…» hacen de una orden un plan cuando nombran el estado del paciente. Una descripción de lo que el residente vio no es condición, y «once» ante una razón es una dosis | C-2026-09-28-19 · `CICLO8_LECTOR.md` |
| TD-30 | Interconsultas sin verbo, la endoscopía pedida, hemocultivos y urocultivo, vías por su número o calibre, «RL» | C-2026-09-28-20 |
| TD-31 (1.ª mitad) | La adrenalina IM sin dosis pregunta su dosis en mg. «Epi» sólo con dosis o vía, nunca la de otro o de antes | C-2026-09-28-21 |
| TD-32 | «2 U. GR», la desactivación del PTM registrada, las plaquetas según recuento, el estado de las pruebas cruzadas y el tiempo por unidad | C-2026-09-28-22 |
| KD-05 | «OK to discharge» y «ok para alta» son un alta, y el alta conserva su receta. Con plazo, observación, condición o de otro servicio, no es alta ahora. Sigue presente en los dos baselines registrados | C-2026-09-28-23 |
| TD-06 | El registro nombra DF-7, DF-10 y DF-16a/b/c | C-2026-09-27-13/14, C-2026-09-28-18 |
| TD-23, TD-25, TD-27, TD-28 | El español de la movilidad parietal y de los avisos, el nombre de la prueba, los espacios y la cita textual | C-2026-09-28-24 |
| Baseline inglés (dato) | El candidato V2 del piloto inglés nombra su commit registrado, `9d2cd9e` | `validation/pilot_v1_en/` |

### Validación A–J del lector

- **A · Conjunto independiente:** 79/80. El V2, 31/80.
- **B · Conjunto ciego 1, medido una vez:** 41/70. El V2, 29/70.
- **C · Post hoc, rotulado:** 52/70. El V2, 30/70.
- **D · Controles negativos:** 0 ejecuciones falsas.
- **E · Dos revisiones adversariales:**
  - la primera, unas 390 frases: 6 CRITICAL, 10 HIGH y 7 MEDIUM, corregidos;
  - la segunda, 301 frases: 73 filas peores que el V2. Se corrigieron;
    quedan 2 ambiguas y 1 defecto anterior al ciclo (TD-39).
- **F · Comparación con el V2 sobre el repositorio:** 13 221 textos. Los 96
  que se leen distinto fuera de las pruebas del ciclo se revisaron.
- **G · Conjuntos del ciclo 7:** sin cambios, salvo un desacuerdo de etiqueta.
- **H · Suite completa y regresiones:** 5900 pruebas pasan, 77 se omiten, 1 falla como se espera y 0 fallan; 56/56 regresiones.
- **I · Ensayo de los 20 escenarios:** español e inglés, 20/20 guiones y 96/96 órdenes, 0 retenciones no anticipadas, 0 llamadas de IA; las 238 decisiones, iguales a las del ciclo 6.
- **J · Conjunto ciego 2, medido una vez con el lector final:** 33/50 (V2: 16/50), con 1 ejecución falsa (V2: 4) y ninguna frase peor que en el V2. Sobre las 42 limpias, 29 (V2: 13). Lo que falla está en TD-40 y TD-14.

### DECIDED + DEFERRED

- Nada del alcance quedó a medias.
- Lo hallado fuera de las clases quedó registrado: TD-34 a TD-40.

### NEEDS NICOLÁS

1. **El piloto formativo controlado:** autorizarlo o no. Está TECHNICALLY
   READY, WITH CONDITIONS; antes, la prueba de humo en la base real.
2. **DF-20** (A/B/C/D): `acs_54m_inferior`. Sus filas de TDFC la esperan.
3. **DF-23:**
   - la fila 4a, que es una línea;
   - cuando pueda, las filas 4b, 6, 7 y 8.
4. **TD-33:** que sólo la sangre reponga el déficit en la regla de sobrecarga.
   Es lo recomendado.
5. **El baseline inglés:** elegirlo antes de leer respuestas. KD-05 sigue en
   ambos candidatos.
6. **KD-02 y TD-35:** ¿preguntar lo que una lista nombra sin verbo y el lector
   no conoce?
7. **KD-15:** el fluido nombrado en palabras sin verbo.
8. **La regla de medidas combinadas** (resto de TD-31).
9. **DC3:** la dosis «IO» sin instalar la IO.
10. **TDFC:**
    - las cuatro dudas residuales de las filas claras;
    - si las composiciones de hipoglicemia heredan TD/F/C de su origen.

### WAITING FOR EXTERNAL DATA

- **Los documentos de los médicos, en español y en inglés.** Nada llegó ni se
  envió en el ciclo 8. SEALED no se tocó.
- **La fidelidad externa del lector.** Ordena TD-14 y TD-34 a TD-40.

### FUTURE ARCHITECTURE

- Sin cambio: la biblioteca POCUS de videos reales y la evidencia C4.

### Hallazgos nuevos del ciclo (§73)

Todos son anteriores al ciclo; el ciclo los encontró.

| ID | Clase | Qué |
|---|---|---|
| TD-34 | HIGH | «Reevaluar en 1 h» corre a los 0 minutos |
| TD-36 | HIGH | Una dosis escrita antes de quien la dio se da de nuevo |
| TD-39 | HIGH | Un alta con plazo o tras una observación corre ahora; también en `939978a` |
| TD-35 | MEDIUM | Exámenes abreviados y nombres comerciales en una lista sin verbo se pierden |
| TD-37 | MEDIUM | La receta del alta escrita en lista |
| TD-40 | MEDIUM | Lo que dejó la segunda revisión adversarial, igual que en el V2 |
| TD-38 | LOW | El aviso genérico tras un envío que sólo trae un plan |

### Baselines

- **SPANISH PILOT BASELINE `939978a`:** intacto. No cambiaron
  `validation/pilot_v1`, sus 18 DOCX ni el manifiesto de defectos conocidos
  (versión 2).
- **DEVELOPMENT HARDENED BASELINES V1 (`72a4a53`) y V2 (`9d2cd9e`):**
  intactos. El lector del ciclo 8 se midió contra el V2.

## Apertura del ciclo 8 (2026-09-28)

**La instrucción, al cerrar el ciclo 7:**

- «Tengo que salir ahora, pero me gustaría dejarte trabajando en el siguiente
  ciclo».
- Luego: «que el ciclo 8 abarque más tareas que no requieran mucha aprobación
  por mí. Si algo lo requiere, me lo entregas en el informe final como lo hemos
  hecho hasta ahora».

**Alcance elegido por el AI Advisor,** sólo con trabajo ya aprobado o que no
pide una decisión clínica ni metodológica nueva:

1. **TDFC** (TD1, F1, C1 y C3):
   - aprobado conceptualmente en el ciclo 7 (§28), «según las recomendaciones
     actuales»;
   - con el modelo de C14 (§92);
   - las filas de `acs_54m_inferior` esperan DF-20, como dice la
     recomendación de TDFC-5;
   - C4 sigue fuera (§93).
2. **Lector, por clase y con el estándar A–J:**
   - TD-29: la condición «cuando/when/once»;
   - TD-30: órdenes sin verbo que se pierden sin aviso;
   - TD-31: la pregunta de la adrenalina IM sin dosis;
   - TD-32: los residuos LOW de TD-26;
   - KD-05: «OK to discharge».
3. **Deuda menor:** TD-27, TD-28, TD-25, TD-06 y TD-23.
4. **Verificación:**
   - el ensayo de los 20 escenarios ES/EN;
   - la suite completa y las 56 regresiones.

**Lo que no se toca** porque pide su decisión, y va al informe final:

- TD-33, DF-20 y DF-23 (4a, 4b, 6, 7, 8);
- KD-02 y KD-15;
- la regla de medidas combinadas (TD-31, segunda mitad);
- DC3 (la mitad de la dosis);
- el baseline inglés;
- el piloto con residentes y la prueba en la base real.

**Reglas que siguen:**

- sin PR, merge a `main`, release, producción ni staging;
- sin SEALED ni datos reales;
- sin contactar a nadie;
- push sólo a `clinical-encounter-v0.13`;
- el baseline español `939978a` y el V2 `9d2cd9e` quedan intactos;
- un solo reporte al final, y STOP: no se inicia el ciclo 9.

## Cierre del ciclo 7 (2026-09-28)

El ciclo cumplió lo autorizado en P0–P2. P3 (TDFC) pasó intacto al ciclo 8.
Detalle en los documentos citados; el reporte final resume.

### DECIDED + IMPLEMENTED

| Ítem | Qué quedó | Registro |
|---|---|---|
| TD-21 | Principio D: sin sobrecarga falsa mientras la hemorragia está activa; la regla vuelve con el sangrado controlado y la pérdida repuesta. La HDA no cambia | C-2026-09-28-12 · `TD21_SOBRECARGA_TRANSFUSIONAL.md` |
| TD-26 (C7-01) | Hemoderivados por clase, estándar A–J completo. En los conjuntos medidos, **0 pérdidas reales y 0 ejecuciones falsas** con el lector final | C-2026-09-28-13 · `TD26_HEMODERIVADOS_Y_C7_06.md` |
| C7-06 y TD-22 | Medidas de hemorragia, acceso IO y prueba de embarazo, EN/ES | C-2026-09-28-14 |
| C4 (H4) | C4 = NO en los 31 casos, en los generados y en PS001; es prospectivo | C-2026-09-28-10 |
| C14 (H3) | `acs_54m_inferior` NO. C14 queda en **14 YES, 17 NO y 0 NOT REVIEWED** | C-2026-09-28-11 |
| DF-24 | I-F02 A, L-F02 A (sólo qué revisión alimenta el radar), anulada A y retiro A (un aviso) | C-2026-09-28-15 |
| DF-24 · L-F07 B | Las 9 composiciones heredan el C14 NO de su origen | C-2026-09-28-16 |
| DF-23 · fila 3 | La prueba de embarazo, con C7-06 | C-2026-09-28-14 |
| C7-09 | Una corrida que mezcla ES y EN falla con claridad. El piloto inglés (EM07–EM12) está preparado y no enviado; su baseline no se eligió | `test_validation_language_separation.py` |
| C7-05 | PostgreSQL 16 local y descartable, verificado sobre el candidato final. El clúster se borró | TD-24 cerrado |
| C7-10 · ACEP | `ACEP_POCUS_FRAMEWORK.md` y la arquitectura POCUS futura, en `2899a01`. Los 6 casos REVIEW NEEDED no cambian | — |

### DECIDED + DEFERRED

- **TDFC-1 a 6 y 8 (C7-11), intacto al ciclo 8.** Es P3 y va todo o nada. No
  se cumplió su condición: aparecieron hallazgos HIGH del propio ciclo hasta
  el barrido final, y después del congelamiento no quedó capacidad
  significativa. Nada TD/F/C se escribió en el banco.
  - **Nota para el ciclo 8.** La proyección «aprobado» de
    `tdfc/MATRIZ_OPORTUNIDADES.md` usa las recomendaciones del borrador y da C3
    13/18. El TDFC-6 aprobado da C3 10/21: YES en 46f, 83m y 61m; NO en 33f,
    24f y 63m. Hay que regenerarla antes de implementar.
- **Fuera de DF-24:** I-F18 (TD-18) y la meta cambiada tras confirmar.
- **Otros defectos del lector (§8):** D5W, el antibiótico unido a un traslado y
  el resto de TD-14.
- **La mitad de dosis de DC3:** con la decisión 8.

### NEEDS NICOLÁS

1. Autorizar, o no, el piloto formativo controlado con sus condiciones.
2. DF-20: A, B, C o D.
3. DF-23, fila 4a: «4a: aplicar el texto propuesto» (u otro).
4. TD-33: «sólo la sangre repone el déficit de la regla de sobrecarga en
   trauma» (recomendado) u otra cosa.
5. El baseline del piloto inglés, antes de leer respuestas.
6. La propuesta del ciclo 8 (en el reporte final).
7. Cuando pueda: DF-23, filas 4b, 6, 7 y 8.

### WAITING FOR EXTERNAL DATA

- **Los documentos de los médicos, en español y en inglés.** Nada llegó ni se
  envió en el ciclo 7. SEALED no se tocó.
- **La fidelidad externa del lector:** ordena TD-14, TD-29, TD-30 y TD-32.

### FUTURE ARCHITECTURE

- **La biblioteca POCUS de videos reales** (`ARQUITECTURA_POCUS_OBJETIVO.md`).
  Hoy el POCUS es un informe escrito: su evidencia es una contribución PARCIAL.
- **La evidencia C4:** vendrá de simulación procedural u observación en el
  lugar de trabajo.

### Hallazgos nuevos del ciclo (§73)

- **Corregidos (CRITICAL/HIGH, dentro del alcance o regresiones del ciclo).**
  Los 16 CRITICAL de la revisión adversarial y lo que halló el barrido final:
  - «suspender/stop transfusión de …» corría las unidades;
  - un verbo que detiene borraba la medida que acompañaba;
  - un balance volvía a pasar el suero;
  - una proporción entre productos se perdía.

  Detalle en `TD26_HEMODERIVADOS_Y_C7_06.md`.
- **Documentados:**
  - TD-33 (HIGH, NEEDS NICOLÁS): un residuo de TD-21 que halló la prueba de la
    rúbrica sobre el lector final;
  - TD-29 (HIGH): la condición «cuando»;
  - TD-30 (MEDIUM): órdenes sin verbo;
  - TD-31 (MEDIUM): la adrenalina IM sin dosis y las medidas combinadas;
  - TD-32 (LOW): residuos de TD-26.
- **Proceso.** `1c4194b` y `c61daf6` se subieron con una prueba fallando (el
  catálogo de hipoglicemia desactualizado). Se regeneró.

### Baselines

- **SPANISH PILOT BASELINE `939978a`:** intacto. `validation/pilot_v1` y los 18
  DOCX no cambiaron.
- **DEVELOPMENT HARDENED BASELINE V1 (`72a4a53`) y V2:** en
  `validation/BASELINES.md`. Ninguno es un «validated engine».

## Decisiones del 2026-09-28 (apertura del ciclo 7)

El docente aprobó la propuesta del ciclo 7 con modificaciones y ordenó
ejecutarlo sin otra aprobación, con máxima autonomía dentro del alcance
aprobado (el docente está offline). Las reglas permanentes del lector y del
Trace quedaron además en el charter, addendum A2.

**Objetivo.** Dejar el simulador técnicamente apto para un piloto formativo
controlado con residentes, sin contaminar el piloto de validación, sin
modificar scoring, sin declarar competencia y sin ampliar features
innecesariamente. Prioridad: fidelidad del Management Trace → seguridad
clínica → jugabilidad → integridad de datos → calidad de la evidencia
observacional → preparación de la validación → costo-efectividad.

- **TD-21 · principio D aprobado, no la opción A.**
  - Mientras haya una hemorragia activa clínicamente significativa, con
    pérdida o déficit hemorrágico modelado en curso, una Hb ≥ 10 aislada **no
    basta** como evidencia de sobrecarga transfusional.
  - La regla genérica vuelve a ser evaluable cuando el sangrado está
    controlado, cuando ya no hay déficit hemorrágico modelado, o cuando existe
    otra evidencia clínicamente coherente de sobretransfusión.
  - No se crea una equivalencia «mL perdidos → unidades permitidas».
  - Antes de implementar se compara A con D (plausibilidad, complejidad,
    consecuencias no buscadas, reversibilidad, verificabilidad). Si D es
    pequeña, general y robusta, se implementa D; si exige reconstruir la
    fisiología, TD-21 se detiene y se documenta, y el ciclo sigue.
  - **Aceptación:** transfusión apropiada durante hemorragia activa
    significativa → sin sobrecarga falsa; transfusión claramente excesiva
    fuera de ese estado → el mecanismo actual sigue siendo posible. Se
    verifican trauma ×2, HDA ×2, casos sin sangrado y casos generados de
    sangrado. Sin cambios al −3 ni a la metodología de eventos críticos.
- **TD-26 (C7-01) · autorizado, CRITICAL.** Si la persona residente ordena
  con claridad un hemoderivado, el motor no puede perderlo en silencio.
  - **A** · glóbulos rojos (soportados): se ejecutan las unidades indicadas.
  - **B** · plasma, plaquetas, crioprecipitado, sangre total, si no están
    modelados: se registra fielmente que fueron indicados, «effect not
    modeled»; nunca se convierten en glóbulos rojos ni se inventan efectos.
  - **C** · protocolo de transfusión masiva: se registra que se activó; si el
    motor necesita saber qué dar ahora, se aclara; nunca se traduce en
    unidades ni proporciones inventadas, ni en un protocolo institucional que
    la persona residente no escribió.
  - **D** · una orden ambigua de hemoderivado: se aclara.
  - Estándar A–J completo. Regla: **una corrección del lector no está completa
    porque pasen sus ejemplos originales.**
- **C7-06 · aprobado en la misma tanda A–J:** la prueba de embarazo que
  retiene la tanda (TD-22), el lenguaje de control de hemorragia («pack the
  wound», «hold pressure») y el acceso IO («humeral IO»), con variantes
  naturales EN/ES. Lo que se ejecuta hace responder al paciente según el
  motor; lo que no se ejecuta no aparece como hecho en el Trace.
- **Otros defectos del lector: DEFERRED.** D5W / D5 half-normal, el
  antibiótico unido a un traslado a pabellón y el resto de TD-14, salvo que
  sean regresiones de C7-01/C7-06 o compartan exactamente la causa raíz y
  corregirlos sea una extensión trivial, general y segura. El ciclo 7 no es
  una limpieza general del lector.
- **PostgreSQL (H2) · autorizado un clúster PostgreSQL 16 local y
  descartable**, sin datos reales, en `/var/tmp/mrs-pg-c7` o equivalente, que
  se borra al terminar.
  - Ni producción ni Neon, si el local funciona.
  - Si hacen falta credenciales externas, infraestructura nueva, gasto o
    producción: se detiene PostgreSQL, se reporta BLOCKED y el ciclo sigue.
    Si el local falla tras un intento razonable, se documentan el bloqueo
    exacto y lo que habría que hacer en staging.
  - **Alcance:** L-F01, L-F04, unicidad de las observaciones, confirmación
    docente, persistencia de la rúbrica, Objective Progress, persistencia y
    procedencia del Trace, y la conducta de las oportunidades C4/C14. Una
    corrida temprana y otra sobre el candidato final. Sin infraestructura
    permanente.
- **C14 (H3) · `acs_54m_inferior` = NO**, con la razón basada en ACEP y
  concisa: la conclusión es sobre la **oportunidad de observación**, no sobre
  la posibilidad técnica («POCUS cannot evaluate the RV» sería demasiado
  fuerte). Después, 31/31 casos revisados: **14 YES / 17 NO / 0 NOT
  REVIEWED**; se retira la transición de C14 donde ya no corresponde y se
  regeneran la tabla y la matriz. C14 no tiene scoring que cambiar.
- **ACEP · resultado conceptual aceptado.** ACEP concibe la competencia en EUS
  como INDICATION → ACQUISITION → INTERPRETATION → INTEGRATION INTO
  MANAGEMENT. El simulador actual observa la indicación o selección
  (potencialmente), la interpretación clínica de un hallazgo POCUS descrito y
  la integración al manejo; **no** observa la adquisición ni el
  reconocimiento directo en la imagen, porque entrega un informe escrito. Su
  evidencia POCUS es una **contribución PARCIAL**, nunca competencia POCUS
  completa.
  - **Terminología:** mientras el POCUS sea texto, no se dice «resident
    recognized the ultrasound finding on imaging»; se dice «resident
    interpreted the provided POCUS finding» o «resident integrated the provided
    POCUS information into management». Vale para documentación, faculty
    briefs y afirmaciones metodológicas futuras, sin reescribir históricos.
  - **ACEP 2016 es una fuente metodológica y de diseño, no un mapping nuevo**,
    ni la definición única o final de la competencia POCUS contemporánea. Nada
    de puntajes, progreso, certificación ni estado de competencia ACEP. Puede
    informar C14, el diseño POCUS futuro, las descripciones de componentes y la
    biblioteca futura. No se abre una revisión bibliográfica nueva.
  - **Alcance cardíaco:** lo que la fuente sí respalda (ventanas estándar,
    actividad cardíaca, derrame y taponamiento, función cualitativa del VI,
    volumen o presión venosa central, VCI y evaluación hemodinámica
    pertinentes, integración al manejo) y lo que no establece como expectativa
    general (motilidad regional, el VD tal como lo usan algunos casos, eco
    cuantitativa avanzada) se marcan como SOURCE LIMITATION / REVIEW NEEDED.
    No se eliminan capacidades por no aparecer en el documento.
  - **Casos REVIEW NEEDED, sin cambio en el ciclo 7:** `acs_61m_posterior`,
    `acs_52m_de_winter`, `pulmonary_embolism_61m`, `renal_colic_34m`,
    `bradycardia_avb3_78f` y `acs_48m_wellens`. No bloquean TD-21 ni TD-26.
  - El C14 actual se evalúa con la capacidad actual (POCUS en texto). La
    biblioteca visual futura exigirá revisar C14 aparte, sin cambiar
    Objective Progress, la meta de 50 ni crear subpuntajes.
- **Arquitectura POCUS futura: FUTURE ARCHITECTURE, no deuda técnica ni bug.**
  Resumen en `docs/ARQUITECTURA_POCUS_OBJETIVO.md`. No se implementa nada en el
  ciclo 7.
- **C4 (H4) · C4 = NO en los 31 casos, en los casos generados y en PS001**,
  cuando comparten el entorno de observación actual. La razón es una
  limitación del entorno y del motor, no de los casos.
  - No se toca el motor para fabricar C4, ni se obtiene «C4 = PARTIAL» de una
    orden procedural.
  - Es prospectivo: los encuentros históricos conservan su contexto de
    evaluación; no se migran observaciones.
  - La evidencia C4 futura vendrá de simulación procedural y/u observación en
    el lugar de trabajo. C4 sigue fuera aunque se implementen los demás TDFC.
- **DF-24:** I-F02 A · **L-F02 A** (autorización explícita: sólo cambia qué
  revisión alimenta el radar, no el scoring, D1–D5 ni el promedio
  longitudinal) · observación anulada A · retiro de rúbrica confirmada A ahora
  (sin estado «retirada») · L-F07 B. Fuera: I-F18 y la meta cambiada tras
  confirmar. Cada cambio con falla actual, conducta esperada, prueba focalizada
  y compatibilidad hacia atrás, sin refactor del flujo longitudinal.
- **TDFC:** TDFC-1, 2, 3, 4, 5, 6 y 8 aprobados conceptualmente según las
  recomendaciones actuales; TDFC-7 ya estaba decidido.
  - La implementación es **P3**: sólo si TD-21, TD-26 y C7-06 están
    resueltos, PostgreSQL verificado o legítimamente bloqueado, C4/C14 y el
    DF-24 aprobado cerrados, sin nuevos bloqueos CRITICAL/HIGH y con capacidad
    significativa. Si no, pasa **intacta** al ciclo 8: todo lo aprobado de
    forma coherente, o nada.
  - Si se implementa: el modelo de C14 (borrador → decisión aprobada →
    declaración por caso → procedencia → congelada con el encuentro), con el
    componente observable y lo que queda fuera para TD1, F1, C1 y C3. Sin
    puntaje de competencia.
- **DF-23 · conservador.** La fila 3 entra con C7-06. La fila 4a
  (`acs_70f_left_main`, «No B-lines» frente a una congestión que progresa):
  se presenta el texto EN/ES y la señal que corrige; se implementa sólo si
  elimina una contradicción factual sin cambiar el Decision Challenge, con
  ANTES/DESPUÉS; si cambia la interpretación clínica, se difiere. Las filas 8,
  7, 4b y 6 siguen como decisiones clínicas. No se limpia la variabilidad
  plausible.
- **Piloto de validación español:** sigue como fue diseñado. El SPANISH PILOT
  BASELINE `939978a` es inmutable: no se modifican el baseline, los 18 DOCX ni
  los defectos conocidos retrospectivamente, no se usa SEALED y no se llevan
  al baseline las correcciones del ciclo 7.
  - Con respuestas humanas: MEASURE FIRST. Primero el corpus español contra
    `939978a`; después, cuando corresponda, los mismos datos de desarrollo
    contra el motor endurecido. Se reportan ambos; no se ocultan defectos del
    baseline porque ya estén corregidos.
- **Piloto de validación inglés:** existen versiones inglesas equivalentes de
  los 18 documentos. Será un corpus **separado**, con su idioma, versión de
  corpus, códigos de participante (EM07–EM12), asignación, baseline, versión
  de defectos conocidos y sorteo development/sealed propios.
  - Texto escrito naturalmente en inglés por clínicos que escriben en inglés;
    nunca una traducción. Nada se envía en el ciclo 7.
  - Se puede preparar su infraestructura si P0/P1 están completos y el costo
    marginal es bajo, reutilizando el pipeline existente. No se regeneran los
    DOCX ingleses si existen fuera del repositorio: se documenta «ENGLISH DOCX
    AVAILABLE EXTERNALLY / NOT PRESENT IN REPOSITORY», sin inventar su
    contenido. Al incorporarlos, se verifican contra los españoles (mismo caso,
    mismas instrucciones, misma asignación, otro idioma de respuesta).
  - **Separación de idiomas (C7-09a):** una validación determinística del
    manifiesto que haga fallar con claridad una corrida que mezcle ES y EN. Sin
    autodetección.
  - **Baseline externo inglés:** no se elige automáticamente el HEAD del ciclo
    7; se documentan los candidatos, y la elección se hace antes de recibir o
    leer respuestas inglesas.
- **Datos externos que lleguen durante el ciclo:** no se leen a mano para
  decidir qué corregir. STORE → SPLIT → BLINDED REFERENCE ANNOTATION →
  BASELINE RUN → MEASURE. Si falta la anotación humana, se prepara, se
  documenta y el ciclo sigue. SEALED, nunca.
- **Baselines, tres conceptos separados:** SPANISH PILOT BASELINE `939978a`;
  DEVELOPMENT HARDENED BASELINE V1 `72a4a53`; DEVELOPMENT HARDENED BASELINE V2
  = el candidato final del ciclo 7, sólo si cumple la definición de terminado.
  Ninguno se llama «validated engine».
- **El validation corpus evalúa el motor.** Nunca calibra puntajes de
  residentes, umbrales de competencia, comparaciones entre médicos ni
  benchmarks clínicos. Blind sets internos, datos externos de desarrollo y
  sellados quedan separados; nada sellado en logs, fixtures, snapshots ni
  reportes del repositorio.
- **Piloto con residentes:** sólo formativo, con confirmación docente
  obligatoria. El sistema produce evidencia observacional, no certificación,
  determinación de competencia, EPA completada ni milestone alcanzado. Al
  cerrar se distinguen TECHNICALLY READY FOR CONTROLLED FORMATIVE RESIDENCY
  PILOT, EXTERNAL VALIDATION PILOT READY y VALIDATED ASSESSMENT INSTRUMENT
  (se espera NO / NOT YET ESTABLISHED), y los bloqueos técnicos de las
  limitaciones metodológicas.
- **Sin cambios:** definiciones de eventos críticos, −3, puntaje ajustado,
  D1–D5, escala 0–3, metodología del radar (salvo la selección de L-F02),
  promedio longitudinal, DIRECT/PARTIAL (PARTIAL no es una penalidad) y la
  confirmación docente. Se verifica que TD-21/TD-26 no produzcan una acción
  peligrosa falsa ni una omisión crítica falsa.
- **Costo e IA:** el menor costo razonable que preserve la calidad,
  reutilizando el tooling del ciclo 6. IA sólo para frases ciegas, revisión
  adversarial y revisión independiente de código; nunca para videos POCUS,
  respuestas de validación ni verdad clínica de referencia. Regla del 130 %
  del charter, sin sacrificar pruebas.
- **Hallazgos nuevos:** CRITICAL se reproduce, se busca la causa, se documenta
  y se corrige si es inequívoco, pequeño y reversible; HIGH se corrige sólo si
  es regresión del ciclo, comparte causa con TD-26/C7-06 o amenaza la
  integridad de datos; MEDIUM/LOW se documentan y se difieren. Después del
  congelamiento del BASELINE V2, nada nuevo MEDIUM/LOW se corrige.
- **Fuera de alcance:** PR, merge a `main`, release, producción, SEALED y el
  ciclo 8 (se propone, no se inicia).

## Cierre del ciclo 6 (2026-09-28)

**Hecho.**

- **DF-22 · las nueve clases CRITICAL del lector, corregidas por clase**
  (C-2026-09-28-04).
  - C01 a C09 en inglés y español: el lector, el motor y el Management Trace.
  - Suite nueva `CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS`: 192 pruebas, 4 de
    ellas por la página real.
  - Tres conjuntos ciegos (258 frases que nadie del desarrollo vio), medidos
    **una vez**. Encontraron regresiones de las propias correcciones; se
    corrigieron después, y esos números son post hoc.
  - Con el código final, **ninguna de las 118 negativas ejecuta nada de más en
    el motor**. En las positivas, la mayoría de lo que no corre se retiene con
    una pregunta; quedan pérdidas sin aviso, sobre todo de hemoderivados
    (TD-26).
  - Corpus de ensayo: 238 decisiones idénticas al ciclo 5.
  - **Revisión adversarial del diff, después del primer commit (`39bac97`).**
    - Halló 13 regresiones de las propias correcciones que los conjuntos
      ciegos no vieron; por ejemplo, «Hold NS, O2 4 L NC» retiraba el oxígeno
      y «Should I give aspirin?» la administraba.
    - Una comparación completa con el lector del ciclo 5 halló dos más y un
      defecto anterior al ciclo: la activación de un servicio volvía
      interconsultas los antiagregantes que la seguían.
    - Todo se corrigió (C-2026-09-28-09).
    - Las 225 lecturas que difieren del ciclo 5 se revisaron una por una.
  - Detalle: `MEDICION_RECONOCIMIENTO_ORDENES.md`.
- **59O-03, completo** (C-2026-09-28-05). El aviso de ejecución urgente y la
  oferta de explicarla salen sólo de una ejecución real. Casos A–F de punta a
  punta en inglés y español.
- **Seguridad de la aclaración.**
  - «No sé» ya no hace desaparecer una orden retenida: la mantiene y repite la
    pregunta.
  - Lo unido a lo que hizo el equipo prehospitalario se pregunta, no se
    ejecuta.
- **L-F01, completo** (C-2026-09-28-06). Un encuentro se lee con los temas de
  historia de su caso congelado. Lo legacy sin caso queda UNAVAILABLE. A → B →
  reabrir da A.
- **L-F04, completo** (C-2026-09-28-07). La trayectoria sigue la fecha del
  encuentro; la de confirmación queda como metadato.
- **DF-23: dos correcciones que cumplen las seis condiciones**
  (C-2026-09-28-08).
  - De Winter conserva su acinesia con la arteria cerrada.
  - `bradycardia_bb_54f` llega somnolienta.
  - El resto queda para decisión.
- **Sin cambio:**
  - **`acs_54m_inferior`:** sin cambio de datos ni fisiología; sigue NOT
    REVIEWED.
  - **C14:** 14 YES y 16 NO.
  - **TD/F/C:** nada escrito en el banco.
- **Documentos de decisión:** `DF24_DECISIONS_FOR_NICOLAS.md` y
  `docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md`.
- **Readiness del piloto con residentes:** `READINESS_PILOTO_RESIDENCIA.md`.
  Respuesta: **WITH CONDITIONS**.
- **Baselines.**
  - El SPANISH PILOT BASELINE `939978a` no se tocó.
  - Se registró el **DEVELOPMENT HARDENED BASELINE V1**
    (`validation/BASELINES.md`). No es una versión validada.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 7 no se inició.

### Cola de decisiones al cierre del ciclo 6

**BLOCKING BEFORE RESIDENCY PILOT**

1. **TD-21 · Sobrecarga transfusional en trauma.**
   - El problema: con una hemorragia activa, la familia trauma no baja la
     hemoglobina y la regla de sobrecarga mira Hb ≥ 10. Enseña que la sangre
     daña en los dos casos de trauma.
   - Recomendación: excluir la hemorragia activa de la regla.
   - Evidencia: `AUDITORIA_DF23_CICLO6.md` §7.1.
2. **TD-26 · Hemoderivados que se pierden sin aviso.**
   - Ejemplos: «2 U de GR O negativo», «O-neg», el protocolo de transfusión
     masiva.
   - Recomendación: autorizar una corrección por clase, medida como DF-22.
3. **C4 = NO, escrito en el banco antes que el resto de TD/F/C.**
   - Está decidido (TDFC-7), pero la transición deja C4 valorable en todo
     encuentro.
   - Recomendación: escribirlo solo.
4. **El uso del piloto con residentes.**
   - La fidelidad del lector con texto externo no está medida.
   - Recomendación: formativo, con confirmación docente de cada rúbrica, hasta
     que el piloto de validación la mida.
5. **PostgreSQL (TD-24).**
   - L-F01 y L-F04 se probaron en SQLite.
   - Falta verificarlos en la base de staging, con su acceso.

**HIGH VALUE / NOT BLOCKING**

- **Enviar el piloto de validación v1 (DF-15):** revisar los 18 documentos,
  reclutar a los 6 médicos y enviar.
- **DF-24, en una línea:** «I-F02 A · L-F02 A · I-F18 B · L-F07 B (D después)
  · anulada A · retiro A · meta A».
- **TD-22:** registrar la prueba de embarazo como «no modelada». Cumple 6/6.
- **TD-23:** los avisos que quedan en inglés dentro de la interfaz en español.

**METHODOLOGICAL**

- **TDFC-1 a 6 y 8, en una línea:** «1 approve / 2 approve / 3 approve /
  4 approve / 5 approve (54m tras DF-20) / 6 approve / 8 approve».
- **Brechas del banco (DF-25):** R1-07, R2-02, R1-03, R1-04, R2-01 y C4, en
  ese orden. Una brecha no es trabajo automático.
- **DF-12, DF-14, DF-17 y DF-9:** sin cambio.
- **Regla para cuando lleguen datos humanos (§89):** MEASURE FIRST.
  BASELINE → MEASUREMENT → ANNOTATION → ADJUDICATION → ERROR CLASSIFICATION →
  PRIORITIZATION → APPROVED FIX.

**CLINICAL REVIEW**

- **`acs_54m_inferior` (DF-20):**
  - confirmar C14 **NO** (recomendado) o YES;
  - decidir si se agrega una nota docente sobre el VD.
- **DF-23, filas 3 a 11:**
  - embarazo: qué responde cada caso;
  - grado del VI y líneas B en `acs_70f_left_main`;
  - «Reduced → mildly reduced» en inferior y posterior;
  - la pared tras reperfundir;
  - FA en `anaphylaxis_63m_betablocked`;
  - foto de llegada de `bradycardia_bb_54f`;
  - menores.
- **TD-04:** confirmar el POCUS de los casos C14 YES; todo el POCUS del banco
  sigue marcado como borrador.

**WAITING FOR EXTERNAL DATA**

- **Los documentos del piloto de validación.** Se miden primero contra el
  SPANISH PILOT BASELINE y después contra el DEVELOPMENT HARDENED BASELINE V1.
- **La fidelidad externa del lector.** Con ella se priorizan TD-14 y el resto
  del manifiesto de defectos conocidos.

## Decisiones del 2026-09-28 (apertura del ciclo 6)

El docente aprobó el cierre del ciclo 5 y ordenó el ciclo 6: **endurecimiento,
consistencia clínica e integridad longitudinal**. El Management Trace sigue
siendo la fuente de verdad: lo que el residente escribió, el motor lo entiende,
la ejecución lo refleja y el Trace lo registra con fidelidad.

| Tema | Decisión |
|---|---|
| **DF-22** · las 9 clases CRITICAL del lector | **APROBADO para implementar**, por clase y no por frase: BEFORE, causa, corrección, frases nuevas independientes, controles negativos, ejecución, Trace, EN, ES y sin regresión. Suite nueva `CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS`. Las 90 frases de la auditoría no son la meta |
| **59O-03** · aviso falso de ejecución | **APROBADO.** El aviso de ejecución sale del estado real de ejecución, nunca del reconocimiento, del intento ni del lenguaje urgente. Casos A–F de punta a punta, EN/ES |
| **Seguridad de la aclaración** | Auditar el camino entrada ambigua → pregunta → respuesta → ejecución. Una aclaración no cambia en silencio la intención clínica; si no se resuelve con seguridad, se retiene. Sólo se corrigen defectos inequívocos; si cambia semántica clínica, se documenta |
| **SPANISH PILOT BASELINE `939978a`** | **Inmutable.** No se cambian sus métricas, su manifiesto de defectos conocidos ni los 18 documentos. La primera medición humana se hace contra él |
| **HEAD ≠ baseline de validación** | El HEAD de desarrollo quedará por delante del baseline español, a propósito. No se mezclan métricas |
| **DEVELOPMENT HARDENED BASELINE V1** | Se registra si todo queda verde. No reemplaza al baseline español ni se llama «validado» |
| **DF-20** · `acs_54m_inferior` | **Recomendación anterior modificada.** No se cambia todavía el tamaño ni la contractilidad del VD, la VCI ni la fisiología. Nueva pregunta: ¿hay de verdad una contradicción, o un IAM inferior con compromiso hemodinámico del VD puede coexistir con un POCUS cualitativo no diagnóstico? Para C14: ¿el POCUS crea una oportunidad significativa de guiar el manejo? El caso sigue NOT REVIEWED salvo evidencia inequívoca. «Sin cambios» es un resultado aceptable |
| **DF-23** · POCUS coronario y otras inconsistencias | **Auditoría focalizada aprobada.** Se corrige sólo lo inequívoco: una sola interpretación defendible, diseño claro, sin cambiar el Decision Challenge ni la metodología, con BEFORE/AFTER y pruebas. Con dos interpretaciones razonables, se documenta y no se elige |
| **C14** | Siguen 14 YES y 16 NO. No se cambian salvo que DF-23 demuestre que una inconsistencia invalida una oportunidad, y antes se documenta |
| **DF-24 · L-F01** | **APROBADO.** Un encuentro histórico se interpreta con lo que le perteneció, no con el banco actual. Sin inventar pasado: lo legacy queda LEGACY / UNKNOWN |
| **DF-24 · L-F04** | **DECIDIDO.** La trayectoria se ordena por la fecha y hora del encuentro. La fecha de confirmación se conserva como metadato de auditoría |
| **DF-24 · resto** (I-F02, L-F02, I-F18, L-F07 y las tres decisiones de corrección) | **No se implementan.** Documento de decisión `docs/DF24_DECISIONS_FOR_NICOLAS.md` |
| **TDFC-7 / C4** | **DECIDIDO: C4 = NO** en los casos propuestos. El motor no modela el componente procedural relevante; ordenar un procedimiento no es una oportunidad de C4. Se registra como brecha, sin cambiar el motor |
| **TDFC-1 a 6 y 8** | **No se implementan.** Documento corto de decisión `docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md`. Nada TD/F/C se escribe en el banco |
| **Brechas del banco** | Se conserva la auditoría. Se priorizan R1-07, R2-02, R1-03, R1-04, R2-01 y C4 sin implementar; una brecha no es backlog automático |
| **TD-09** · cola docente a escala | **No se optimiza** en el ciclo 6 |
| **PostgreSQL** | Probarlo sólo con infraestructura ya disponible y sin gasto; si no, NOT TESTED |
| **Sin cambios** | D1–D5, escala 0–3, eventos críticos, −3, puntaje ajustado, radar, confirmación docente y DIRECT/PARTIAL. Sin puntajes nuevos ni funciones nuevas |

## Cierre del ciclo 5 (2026-09-28)

- **C14 activado donde se aprobó (DF-13, cerrado).**
  - 30 casos declaran C14: **14 YES y 16 NO**, cada uno con quién lo revisó,
    cuándo, su grupo de decisión y la versión C14-REVIEW-1. Un NO lleva su
    razón.
  - La tabla derivada está en `docs/C14_TABLA_FINAL.md`, y una prueba la ata
    al banco.
  - La regla de transición se retiró sólo para C14 y sólo en esos 30 casos.
  - 16 pruebas nuevas (`test_c14_opportunities.py`) cubren §21, §22 y
    §36–§39.
- **`acs_54m_inferior` auditado (DF-20), sin cambios.**
  - Clasificación B: inconsistencia de datos del caso.
  - Recomendación A: el VD comprometido es el diseño.
  - Decisión pendiente.
- **KD-01 corregido por clase y verificado (DF-19, cerrado).**
  - La vía escrita antes del fármaco, también dentro de una lista.
  - 53 pruebas nuevas.
  - Corpus de ensayo idéntico en ES y EN.
- **Baselines.**
  - **SPANISH PILOT BASELINE `939978a`**, sin cambio.
  - **ENGLISH VALIDATION BASELINE `ec1c77f`:** 4956 pasan, 77 omitidas,
    2 xfail y 0 fallas; 56 de 56 regresiones.
  - Los reportes nombran el baseline y la versión de defectos conocidos: la
    lista es la versión 2, con KD-15 y KB-02 nuevos.
- **Piloto: tooling READY**, con una prueba de punta a punta sobre documentos
  sintéticos. Las etiquetas de defecto conocido ahora se validan contra la
  lista.
- **Una regresión del ciclo, corregida.** El catálogo publicado de
  hipoglicemia quedó desactualizado por las entradas nuevas del registro de
  correcciones. Se regeneró, y su generador nombra la corrección detrás de
  cada declaración nueva.
- **Sin cambios:**
  - D1–D5 y la escala;
  - eventos críticos, −3, puntaje ajustado y radar;
  - confirmación docente;
  - mappings (9 PARTIAL inactivos);
  - C2 y C15 deshabilitadas.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 6 no se inició.

## Extensión nocturna del ciclo 5 (2026-09-28)

Auditar y documentar (59A–59BU). Índice y detalle:
`docs/AUDITORIA_NOCTURNA_CICLO5.md`.

- **Una corrección, dentro del límite de 59BT (C-2026-09-28-03).** Un
  encuentro nuevo heredaba el cierre del anterior (59Z):
  - el aviso «How is this encounter ending?» abría el encuentro siguiente en
    el minuto 0;
  - el registro de cierre anterior se guardaba en el encuentro siguiente.
  - Reproducido en la página real y corregido en 2 líneas, con 3 pruebas. Los
    registros guardados no se reescribieron.
- **Suite completa sobre la corrección (`3f0524c`):** 4960 pasan, 1 falla,
  77 omitidas y 2 xfail; 56 de 56 regresiones.
  - La falla fue el catálogo publicado de hipoglicemia, que lista las
    correcciones.
  - Se regeneró (`b8eb421`), y sus pruebas pasan.
- **Suite completa final (`8c5d5a3`, con la documentación de la noche):**
  **4961 pasan, 0 fallas**, 77 omitidas y 2 xfail; 56 de 56 regresiones.
- **Lo más importante, sin corregir:**
  - **DF-22.** El lector pierde órdenes de primera línea por la forma de la
    oración, y la página dice «Urgent intervention executed» cuando nada
    corrió.
  - **DF-23.** El POCUS de las 4 oclusiones baja la severidad redactada sin
    reperfusión; en de Winter, C14 YES, acinesia pasa a «mildly reduced».
  - **DF-24.** Los temas de historia se leen del banco vivo, y el perfil ordena
    por confirmación.
- **Se sostienen:**
  - el aislamiento entre residentes (36 métodos);
  - la idempotencia, la concurrencia y las transacciones;
  - el oráculo longitudinal, que coincide en cada celda;
  - la escala hasta 5000 encuentros, salvo la cola docente completa (TD-09).
- **Borradores nuevos, nada en el banco:** TD/F/C (DF-21) y brechas del banco
  (DF-25).

## Decisiones del 2026-09-28 (apertura del ciclo 5)

El docente aprobó el cierre del ciclo 4 y ordenó iniciar el ciclo 5 sin otra
aprobación.

- **DF-13 · C14, decisiones A–H aprobadas**, con estas precisiones:
  - **A:** `acs_61m_posterior` y `acs_52m_de_winter` YES; `acs_66f_nonst` NO.
    `acs_54m_inferior` NO se activa: se audita la contradicción entre el VD
    declarado y el POCUS con VD normal. La auditoría no corrige el dato si
    corregirlo exige elegir entre las dos representaciones; recomienda y deja
    la decisión al docente.
  - **B:** `acs_48m_wellens` NO.
  - **C:** YES en `pneumonia_46f`, `pneumonia_83m`, `gi_bleed_57m`,
    `gi_bleed_72f` y `obstructive_pyelonephritis_58f`; NO en `anaphylaxis_29f`
    y `anaphylaxis_63m_betablocked`.
    - Principio: el POCUS cuenta cuando selecciona, limita, titula o reevalúa
      la estrategia de fluidos o hemodinámica.
  - **D:** asma ×2 NO, porque el evento revela el diagnóstico de neumotórax.
    No se cambia el evento para fabricar una oportunidad.
  - **E:** las tres bradicardias NO.
  - **F:** la consolidación sola no crea C14. Las neumonías son YES por C, con
    una sola oportunidad.
  - **G:** los dos TEP YES.
    - Se conserva qué componente concreto se observa: sobrecarga del VD, TVP
      proximal, integración con la hemodinamia, estrategia de reperfusión o
      anticoagulación.
    - POCUS realizado no es C14 demostrado.
  - **H:** `renal_colic_34m` NO. La pielonefritis 58f es YES por C, no por la
    ecografía renal formal.
  - **Filas claras del borrador:** se mantienen.
- **Metadata C14:**
  - antes de escribirla, la tabla final derivada;
  - cada fila con procedencia (`human_clinical_review`, Nicolás Pineda,
    2026-09-28, grupo de decisión, versión);
  - un NO se registra con su razón, nunca como ausencia;
  - `acs_54m_inferior` queda NOT REVIEWED;
  - el fallback se retira caso a caso, sin tocar el mecanismo global.
- **Pruebas C14 exigidas (§21):**
  - YES evaluable; NO no confirmable; NOT REVIEWED sólo transitorio;
  - YES sin evidencia automática;
  - confirmación docente;
  - observación incidental;
  - el target no decide C14;
  - históricos intactos;
  - congelado al iniciar.
  - Además: sin doble conteo (§22), la evidencia esperada no es lista cerrada
    (§36), NO no es falla (§37), YES no es OBSERVED (§38) y C14 incidental bajo
    otro R1/R2/R3 (§39).
- **DF-19 · KD-01 autorizado:** corrección por clase de vía + fármaco + dosis
  sin verbo, con la vía primero. Sólo vías soportadas. Pruebas positivas y
  negativas, EN y sin regresión ES, ejecución y Management Trace.
- **Baselines:**
  - **SPANISH PILOT BASELINE = `939978a`**; no se reemplaza retroactivamente.
  - Después de KD-01, con la suite completa en verde, el nuevo SHA se registra
    como **ENGLISH VALIDATION BASELINE**.
  - Cada corrida de validación registra CORPUS VERSION, LANGUAGE, ENGINE
    BASELINE y KNOWN DEFECTS VERSION.
  - La primera medición en español usa el baseline español.
- **Defectos conocidos:** actualizar la lista después de KD-01. No se corrigen
  KD-02 a KD-14 salvo que KD-01 resuelva alguno por la misma causa o aparezca
  una regresión.
- **DF-15 · piloto aprobado.** Los 18 documentos son PILOT MATERIAL V1.
  - No se modifican salvo error factual, spoiler, corrupción del DOCX o una
    inconsistencia que los vuelva inutilizables; y en ese caso se documenta,
    se versiona y se verifica de nuevo.
  - Se mantienen la anotación (clínico primario, 20 % doble, tercero o
    consenso) y VC-3.
  - La IA no hace de estándar de referencia.
  - **THE PHYSICIANS ARE NOT BEING ASSESSED.**
- **Se mantienen:**
  - DF-17 diferido;
  - C2 y C15 deshabilitadas;
  - los 9 PARTIAL inactivos.
- **Fuera de alcance del ciclo 5:**
  - corregir clínicamente `acs_54m_inferior` sin aprobación;
  - revisar TD1/F1/C1/C3/C4 caso por caso;
  - cambiar puntajes, D1–D5, eventos críticos o el −3;
  - override, fuentes externas, construct coverage;
  - correr el piloto sin respuestas humanas reales;
  - contactar, enviar o distribuir;
  - PR, merge o release;
  - iniciar el ciclo 6.

## Decisiones del 2026-09-28 (apertura del ciclo 4)

- **DF-12 · aprobada como regla TRANSITORIA.**
  - Mientras un caso u objetivo siga NOT REVIEWED, conserva el comportamiento
    previo para no perder oportunidades antes de la revisión clínica.
  - **No es la arquitectura final.** El estado objetivo es: CASO → OPORTUNIDADES
    REVISADAS EXPLÍCITAMENTE → SOLO LAS OPORTUNIDADES REALES SON EVALUABLES.
  - El fallback se retira progresivamente: C14 primero y después TD/F/C, a
    medida que se aprueben sus oportunidades. No se retiran otros fallbacks sin
    revisión clínica.
- **DF-14 · confirmado.**
  - Los 9 vínculos PARTIAL siguen inactivos y documentados para revisión
    posterior.
  - PARTIAL IS NOT A DEFECT: los PARTIAL activos y defendibles siguen activos.
  - Se prioriza lo significativo, interpretable y trazable sobre la cobertura
    máxima.
- **DF-16 · a y b autorizados para el ciclo 4**, por clase, EN/ES, con frases
  nuevas y BEFORE/AFTER.
  - Los residuos MEDIUM/LOW se corrigen solo si son deterministas, pequeños, de
    bajo riesgo y del mismo mecanismo: vía compartida, listas de órdenes,
    variantes comunes.
  - Los independientes («si» = «whether», texto tomado como respuesta,
    traducciones, «OK to discharge») se documentan primero. Si alguno resulta de
    alto valor y barato, se propone para el ciclo 5.
- **DF-13 · C14 no se activa todavía**, ni siquiera los 6 YES y 6 NO claros.
  - El ciclo 4 prepara las decisiones A–H agrupadas y puede mejorar el borrador.
  - C14 es el primer objetivo con el flujo: BORRADOR DEL AI ADVISOR → REVISIÓN
    CLÍNICA HUMANA → METADATA APROBADA.
- **DF-17 · DEFERRED / DESIGN AFTER C14 PILOT.**
  - Debe seguir siendo posible que el docente indique que la oportunidad
    declarada no ocurrió, o que reconozca una observación incidental.
  - No se agrega interfaz ni lógica.
- **DF-4 · C2 sigue deshabilitada.** No se fija un número artificial de casos;
  se revisa con un banco de trauma más amplio. No se trabaja en C2 en el ciclo 4.
- **DF-15 · piloto aprobado con modificaciones.**
  - 6 médicos de urgencia × 3 casos, unos 18 documentos. Cada idioma, escrito
    por quien lo escribe naturalmente; no se traduce.
  - Los seis casos propuestos.
  - Instrucción breve, alineada con la guía del residente: interpretación,
    acción, expectativa y reevaluación, en texto libre y sin cajas obligatorias.
  - **VC-1:** aprobado. Dejar listos los 18 documentos; el docente recluta y
    distribuye.
  - **VC-2:** anotación primaria por un clínico, 20 % doble por un segundo
    clínico, y desacuerdo por un tercero o por consenso explícito.
  - **VC-3:** las indicaciones de regreso son FOLLOW-UP / DISPOSITION SAFETY
    PLAN. Cuentan como contingencia solo si traen una condición explícita que
    modifica el plan.
  - **VC-4:** revisar de nuevo los textos en español y verificar los DOCX
    estructuralmente. La verificación visual en Word la hace el docente.
  - **Split development/sealed:** no se sortea antes de que vuelvan los
    documentos; el ciclo 4 define el procedimiento, reproducible y auditable.

## Cierre del ciclo 4 (2026-09-28)

- **PILOT BASELINE: `939978a5147ab859a6dc3566ef4e1a98611a5093`**, motor
  `0.24.13-clinical-encounter`.
  - **Suite completa:** 4877 pasan, 77 omitidas, 2 xfail y 0 fallas.
  - **Regresiones:** 56 de 56.
  - **Corpus de ensayo:** 96/96 órdenes en ES y EN, idéntico al ciclo 3
    decisión por decisión.
  - **Detalle:** `validation/pilot_v1/PILOT_BASELINE.md`.
- **DF-16a y DF-16b, corregidos por clase**, EN/ES, con la traza verificada.
  DF-16c quedó corregido con la vía compartida. Los restos están en el
  manifiesto de defectos conocidos (KD-01 a KD-14).
- **DF-13, C14:** ocho decisiones A–H listas para responder. **C14 no está
  activado**; la regla de transición sigue y es temporal (DF-12).
- **DF-15, piloto: listo para distribuir y no enviado.**
  - `validation/pilot_v1/`: 18 documentos VC2, **DOCX STRUCTURALLY VERIFIED**
    (no en Word);
  - el mensaje para los médicos, la matriz y el sorteo definido;
  - la anotación y la adjudicación, y el manifiesto de defectos conocidos.
- **Herramienta del validation corpus**, sin un segundo parser:
  - bug corregido: los planes se emparejaban con el tipo equivocado;
  - comando `split`;
  - hoja del segundo anotador;
  - taxonomía del §40;
  - columnas de impacto y de defecto conocido.
- **La primera corrida completa encontró 5 fallas dependientes del orden.** Las
  causó la prueba nueva de DF-16 por la página real, que dejaba la variable de
  modo offline en el proceso. Se reprodujo y se corrigió en las pruebas; el
  código de la aplicación no cambió.
- **Sin cambios:**
  - D1–D5 y la escala 0–3;
  - los eventos críticos y el −3, el puntaje ajustado y el spider;
  - la confirmación docente;
  - los mappings (los 9 PARTIAL siguen inactivos);
  - C2 y C15, deshabilitadas.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 5 no se inició.

## Decidido e implementado

| ID | Tema | Estado |
|---|---|---|
| DF-13 | C14 caso por caso (decisiones A–H) | **Aplicado en el ciclo 5:** 14 YES y 16 NO con procedencia; `acs_54m_inferior` pasa a DF-20 |
| DF-19 | KD-01, la vía antes del fármaco | **Corregido y verificado en el ciclo 5**; es el ENGLISH VALIDATION BASELINE `ec1c77f` |
| 59Z | Un encuentro nuevo heredaba el cierre del anterior | **Corregido en la extensión nocturna** (C-2026-09-28-03), dentro del límite de 59BT |
| DF-1 | Observation opportunities (D-1 a D-6) | **Implementado y testeado.** C14 no activado: pasa a DF-13 |
| DF-2 | R1-03, R1-04 y R2-01 con contribución DIRECT/PARTIAL | **Implementado y testeado.** PARTIAL inactivos en DF-14 |
| DF-6 | Validation corpus | **Diseño cambiado por el docente** (Fase 1 en Word) · herramienta implementada · piloto en DF-15 |
| DF-16a/b/c | Listas de órdenes, orden + repetición + condición, vía compartida | **Implementado y testeado** (ciclo 4) |
| DF-10 | Seguimiento pegado al alta, EN/ES | **Implementado y testeado** |
| DOC-1 | §51 del charter | **Cerrado:** termina en «…del desempeño del residente.» |
| DF-7 | Fidelidad del razonamiento en el Management Trace | Cerrado en el ciclo 2 |
| DF-3 | MK1 | Cerrado; se usa como PARTIAL en R2-01 |

---

## Pendientes

### [HIGH VALUE · CLINICAL REVIEW] DF-20 · `acs_54m_inferior`: VD comprometido en el caso, VD normal en su POCUS

> **CERRADO en el ciclo 9 (2026-09-29): sin cambios en el caso** (§16, §17). Un compromiso fisiológico del VD
> puede coexistir con un POCUS cualitativo de urgencias normal o no diagnóstico; C14 sigue NO y las filas TDFC
> quedaron declaradas (C-2026-09-29-05). Lo que sigue es el registro de la decisión.

**PROBLEM**

- **El caso y el motor modelan un IAM inferior con compromiso del VD.** Lo
  sostienen:
  - la declaración coronaria;
  - el comentario del caso;
  - las decisiones docentes del 2026-09-19 y del 2026-09-21 (4, 7 y 10);
  - el guion «bueno» de la tanda 20.
- **Su POCUS dice VD normal**, con «RV free wall contracts normally», y una
  VCI de 1.8 cm con 50 % de colapso.
- **En un mismo encuentro el residente ve SDST en V4R y un VD normal.** Si
  confía en el POCUS y da nitroglicerina a 20 mcg/min, la PA cae de 100/64 a
  67/45 en 10 minutos.

**EVIDENCE**

- **Auditoría:** `docs/AUDITORIA_ACS_54M_INFERIOR.md`. Clasificación **B**:
  inconsistencia de datos del caso, visible en el juego. El POCUS es un
  borrador nunca revisado, y su propia nota dejó la pregunta abierta.
- **Impacto medido en copias descartables** (2,540 pruebas de SCA, POCUS y
  texto del caso):
  - con A falla 1 prueba, el texto en español;
  - con B fallan 2, las decisiones del VD.
- **Encuentros históricos:** ninguna opción los toca; el caso se congela con
  el encuentro.
- **Fuera del piloto de validación:** sus seis casos no incluyen SCA.

**RECOMMENDATION**

**Opción A.** Corregir el VD y la VCI del POCUS al compromiso del VD, con la
redacción que usted apruebe. Después:

- nueva traducción del pasaje en español;
- su decisión C14 (YES o NO) para el caso.

**ALTERNATIVES**

- **B:** quitar el compromiso del VD.
- **C:** mantener ambas, declarando el punto docente.
- **D:** dejarlo sin revisar.

**COST / EFFORT**

- **Docente:** aprobar dos líneas de texto y una fila C14.
- **AI Advisor:** una sesión corta.

**RISK**

- Mientras no se decida, el caso sigue mostrando datos contradictorios.
- C14 conserva la regla de transición en ese caso.

**DECISION NEEDED**

1. ¿Cuál representación es la correcta: A, B, C o D?
2. Si A, el texto del VD y de la VCI.
3. C14 YES o NO para el caso.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-15 · Piloto del validation corpus, Fase 1

**PROBLEM**

Hace falta lenguaje clínico auténtico, independiente del lector, para medir su
generalización (DF-6 modificado por el docente).

**EVIDENCE**

`docs/VALIDATION_CORPUS_FASE1.md`:

- plantilla Word ES/EN: 12 documentos del piloto en `validation/plantillas_v1/` (retirados en el ciclo 4; los reemplaza `validation/pilot_v1/`);
- ingesta DOCX determinista por la página real;
- anotación ciega, adjudicación, clases y métricas;
- 25 tests;
- una corrida sintética de punta a punta.

**CICLO 4 · PREPARADO, NO ENVIADO.** Todo está en `validation/pilot_v1/`
(empiece por su `README.md`):

- **Documentos.** Los 18 documentos VC2, personalizados, **DOCX STRUCTURALLY
  VERIFIED** y no verificados en Word.
- **Material de envío y de trabajo:**
  - la matriz de asignación;
  - el texto del mensaje en ES y EN;
  - la anotación (plantilla, guía y adjudicación);
  - el procedimiento del sorteo;
  - el manifiesto de defectos conocidos;
  - el baseline.
- **La propuesta del ciclo 3**, de abajo, queda como antecedente.

**RECOMMENDATION del ciclo 3** (piloto, §96)

- **Médicos y casos:**
  - 6 médicos en español, en 3 pares;
  - 3 casos cada uno, de C01–C06;
  - 45–60 min por médico;
  - 18 documentos, unas 150–270 entradas.
- **Inglés:** sólo con médicos que escriban naturalmente en inglés.
- **Subconjuntos:**
  - development y sealed 50/50 por médico;
  - sorteo dentro de cada par, después de recibir y antes de leer.
- **Anotación:**
  - ciega, antes de correr el motor;
  - doble en el 20 %;
  - adjudicación con propuesta determinista.

**ALTERNATIVES**

- Todo el piloto como development, sellando recién en la fase siguiente: más
  datos para diagnosticar y ninguna medición de generalización.
- 4 médicos: menos carga y menos variabilidad.

**COST / EFFORT**

- **Médicos:** unas 5–6 h en total.
- **Custodio:** 1,5–2 h.
- **Anotación:** 3–4,5 h, más ~1 h de doble anotación.
- **Adjudicación:** ~1–1,5 h por subconjunto.
- **IA:** US$0.

**RISK**

- **Texto del caso en español:** no confirmado aprobado.
- **Word real:** sin probar; se validó con python-docx, no con Word.
- **n chico:** las métricas del piloto son descriptivas.

**DECISION NEEDED** (VC-1 a VC-4 se decidieron el 2026-09-28)

- **Acción docente:**
  - abrir los 18 documentos en Word;
  - confirmar el texto en español de los seis casos, que es la aprobación para
    el piloto;
  - enviarlos.
- **Anotación:** decidir quién anota, quién hace la doble anotación y quién
  adjudica.

El AI Advisor no contacta a nadie ni envía nada.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-22 · Clases del lector y de la página halladas por la auditoría nocturna

**PROBLEM**

- **El lector pierde órdenes de primera línea por la forma de la oración.**
  - «Anaphylaxis …: epinephrine 0.5 mg IM now, repeat in 5 minutes if no
    response» no da la adrenalina: toda la frase queda como plan de
    repetición.
  - «Atropina 1 mg ev, si no responde, marcapaso…» no da la atropina.
  - Con un punto en lugar de «:» o «,», ambas se ejecutan.
- **Son 9 clases CRITICAL.** Además de las anteriores:
  - «Ahora X y luego repetir»;
  - «Por … instalo …»;
  - «cambia a Ringer»;
  - destino «con/on» un tratamiento;
  - «Activo hemodinamia»;
  - TXA «en 10 min» en un paquete urgente;
  - un hallazgo tras la orden («satura 86 % con la naricera»).
- **La página dice más de lo que pasó:**
  - «Urgent intervention executed» cuando nada corrió (59O-03);
  - preguntas atadas a órdenes mal leídas, que al contestarlas pueden
    ejecutar lo equivocado (59O-06).

**EVIDENCE**

- `docs/AUDITORIA_TRACE_CICLO5.md`: 90 frases INTERNAL AUDIT DATA y 6
  guiones en la página real.
- La sesión principal reprodujo 3 en el lector, con su control.
- **No es regresión:** las 90 frases se leen igual en `939978a` y hoy. Están en
  los dos baselines.

**RECOMMENDATION**

1. **No corregir las clases del lector antes del piloto, ni registrarlas como
   defectos conocidos.** Así el piloto mide su frecuencia real sin sesgo (59I).
   Después, cada falla del piloto de una de estas clases se prioriza con
   `PRIORIZACION_POST_PILOTO.md`, anotando que la auditoría interna ya la
   había visto.
2. **Aparte, autorizar la corrección de 59O-03 antes de cualquier piloto con
   residentes:** avisar «ejecutada» sólo después de ejecutar. Es veracidad de
   la página, no lectura, y no cambia lo que mide el piloto de validación.

**ALTERNATIVES**

- Registrar las 9 como KD-16 a KD-24 antes del piloto. Las etiquetas serían
  fieles, pero el piloto contaría menos fallas nuevas.
- Corregirlas ahora. El piloto pierde independencia, y se corre el riesgo de
  ajustar el lector a frases escritas por una IA.

**COST / EFFORT**

- **Docente:** dos respuestas.
- **AI Advisor:** 59O-03 es una sesión corta.

**RISK**

Mientras tanto, quien escriba así recibe un encuentro distinto de lo que
escribió, y el Trace le atribuye la omisión.

**DECISION NEEDED**

1. ¿Piloto independiente (recomendado) o registrar las clases como
   conocidas?
2. ¿Se corrige 59O-03 antes del piloto con residentes?

---

### [CLINICAL REVIEW] DF-23 · Inconsistencias clínicas fuera de `acs_54m_inferior`

> **Ciclo 9 (2026-09-29):** la fila 4a (`acs_70f_left_main`, «No B-lines» frente a la congestión) se aplicó
> con el texto propuesto (C-2026-09-29-06). Las filas 4b, 6, 7 y 8 siguen pendientes.

**PROBLEM**

| Caso | Contradicción |
|---|---|
| Las 4 oclusiones (de Winter, posterior, inferior, tronco) | El primer POCUS repetido baja la severidad redactada a «mildly reduced» con la arteria cerrada. En `acs_52m_de_winter`: «Akinesis» al llegar, «mildly reduced» a los 30 min, «akinetic» a los 100 |
| `bradycardia_bb_54f` | Somnolienta en la presentación, «Alert» en el monitor |
| `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m` | FA como antecedente; el monitor muestra ritmo sinusal, derivado de la FC |
| Mujeres en edad fértil (p. ej. `pulmonary_embolism_33f`) | El estado de embarazo no está redactado |
| Todo el POCUS del banco | Sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW`), también en los 14 casos C14 YES |

**EVIDENCE**

- La sesión principal verificó las tres primeras filas en el motor.
- Detalle en `docs/AUDITORIA_NOCTURNA_CICLO5.md`, sección 9.
- No se cambió ningún dato: cada fila exige elegir cuál representación es
  la correcta.

**RECOMMENDATION**

1. **Oclusiones:** decidir junto con DF-20, empezando por de Winter, que es
   C14 YES. Si la severidad redactada es la correcta, el POCUS repetido
   debería conservarla hasta la reperfusión.
2. **`bradycardia_bb_54f`:** que el monitor muestre lo que dice la
   presentación.
3. **FA:** decidir si el ritmo de llegada es FA (y entonces el ECG y el
   monitor la muestran) o si el antecedente se quita.
4. **Embarazo:** decidir qué responde el caso si se pregunta.
5. **POCUS:** confirmar el POCUS de los 14 casos C14 YES (TD-04).

**COST / EFFORT**

- **Docente:** revisar 5 puntos.
- **AI Advisor:** una sesión por punto aprobado, con sus pruebas.

**RISK**

En de Winter, la evidencia esperada de C14 descansa en la evolución de la
pared, y el motor la muestra de forma implausible.

**DECISION NEEDED**

Una respuesta por fila.

---

### [METHODOLOGICAL REVIEW] DF-24 · Integridad longitudinal: correcciones propuestas

**PROBLEM**

La auditoría longitudinal y la de integridad no encontraron nada CRITICAL ni
HIGH, pero dejaron correcciones que tocan informes, el radar o eventos
críticos. Ninguna se aplicó.

| ID | Qué | Toca |
|---|---|---|
| L-F01 | Los temas de historia se leen del banco vivo, no del caso congelado. Un cambio del banco reinterpreta encuentros antiguos, también el tamizaje de `bradycardia_cause_unexamined` | informes y tamizaje de eventos críticos |
| I-F02 / L-F02 | La exportación del residente no trae quién confirmó la rúbrica, y el perfil elige la «última» por hora y no por número de revisión | exportación y radar |
| L-F04 | El perfil ordena por fecha de confirmación: «último encuentro» y «cambio» pueden contradecir la trayectoria | radar |
| I-F18 | Al migrar una base antigua, la foto de una confirmación absorbe observaciones posteriores | confirmación |
| L-F07 | C14 sigue abierto por la transición en casos generados, en PS001 y en los 9 candidatos del catálogo de hipoglicemia, aunque los casos de hipoglicemia del banco dicen NO | oportunidades |
| TD-09 | La cola docente completa tarda 3 s con 1000 encuentros pendientes y 14,5 s con 5000 | rendimiento |

**RECOMMENDATION**

1. **Aprobar L-F01:** leer los temas del caso congelado. Devuelve el principio
   de que un encuentro se lee con su propio caso.
2. **Aprobar I-F02 y L-F02:** con un reloj normal dan los mismos resultados.
3. **L-F04:** ordenar el perfil por la fecha del encuentro. Es una decisión de
   producto, porque cambia qué significa «último».
4. **I-F18:** aprobar.
5. **L-F07:**
   - mantener la transición en casos generados y PS001, que no tienen
     declaraciones (DF-12);
   - llevar el NO de hipoglicemia a los candidatos del catálogo sólo si usted
     lo confirma.
6. **TD-09:** corregir antes de cohortes de más de unos 20 residentes. El
   piloto no lo necesita.

**Tres decisiones de corrección (59BC):**

1. **Observación anulada.** Hoy el residente ve el juicio anulado, las notas y
   el motivo. Se recomienda mantenerlo y decírselo al docente en el formulario
   de anulación.
2. **Retirar una rúbrica confirmada** hoy es imposible. Se recomienda un
   estado «retirada» que sólo se agrega, cuando haga falta. No es urgente.
3. **Meta subida después de confirmar.** Se recomienda marcarla como
   «confirmado con una meta anterior», sin cambiar nada automáticamente.

**COST / EFFORT**

- **AI Advisor:** L-F01, I-F02, L-F02 e I-F18 caben en una sesión con sus
  pruebas.
- **L-F04:** decisión y una sesión.

**RISK**

- **Hoy L-F01 es latente:** el registro no muestra cambios de temas de
  historia en el banco.
- **L-F02 y L-F04** sólo se notan con relojes desfasados o confirmaciones fuera
  de orden.

**DECISION NEEDED**

1. ¿Se aprueban L-F01, I-F02, L-F02 e I-F18?
2. L-F04: ¿fecha del encuentro o de la confirmación?
3. L-F07.
4. Las tres decisiones de corrección.

---

### [CLINICAL REVIEW (futuro)] DF-21 · Oportunidades de TD1, F1, C1, C3 y C4

**PROBLEM**

TD1, F1, C1, C3 y C4 siguen con la regla de transición: observables en todo
encuentro. Retirarla exige revisar caso por caso, como se hizo con C14.

**EVIDENCE**

- **El borrador está en `docs/tdfc/`.** No se escribió nada en el banco.
- **155 combinaciones:** 73 YES, 60 NO y 22 dudosas.
- **Las 22 dudosas caben en 8 decisiones** (TDFC-1 a TDFC-8), cada una con su
  recomendación.
- **Cada combinación dudosa depende de una sola decisión.**
  `generar_matriz.py` rederiva las cuentas y la matriz.

**RECOMMENDATION**

Resolver TDFC-1 a TDFC-8 cuando usted pueda. No bloquean el piloto.

**RISK**

- **Si se aprueban TDFC-7 y TDFC-8, ningún caso del banco ofrece C4.** Al
  retirar la transición, C4 dejaría de ser observable en el banco. Es una
  consecuencia, no una propuesta. DF-25 (G2) trata cómo darle oportunidades.
- **Las filas de `acs_54m_inferior`** esperan a DF-20.

**DECISION NEEDED**

TDFC-1 a TDFC-8 (`docs/tdfc/DECISIONES_TDFC.md`).

---

### [CLINICAL + METHODOLOGICAL REVIEW (futuro)] DF-25 · Banco de casos: asignación de desafíos y brechas

**PROBLEM**

Los desafíos se asignan por familia, pero lo que los hace observables está en
casos concretos, a veces fuera de esas familias.

- R1-07 trae su elemento explícito en 1 de sus 9 casos.
- R2-02 es SCA en un 75 %.
- R1-03, R1-04 y R2-01 no tienen casos del banco.
- C4 no tiene ningún contexto procedural declarado.

**EVIDENCE**

`docs/AUDITORIA_BRECHAS_BANCO_CICLO5.md`: 18 brechas, 8 de clase A, 2 B, 4 C y
4 D.

**RECOMMENDATION**

Las de clase A no piden casos nuevos:

- declarar R1-07 por caso en los 6 casos con impresión de entrega redactada;
- sortear primero la familia y luego la variante;
- revisar los 3 procedimientos dolorosos para C4;
- abrir R1-04 y R2-01 a casos del banco con declaración por caso.

**DECISION NEEDED**

Las 10 preguntas del final de esa auditoría. No bloquean el piloto.

---

### [HIGH · MEDIUM · LOW] DF-16 · Defectos del lector encontrados en el ciclo 3

**CICLO 4.**

- **a, b y c, corregidos por clase**, EN/ES, con frases nuevas, antes y
  después, y la traza verificada. Detalle en
  `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, sección «Ciclo 4 · DF-16».
- **d a i siguen documentados**, ahora como defectos conocidos del baseline
  del piloto: d = KD-03, e = KD-04, f = KD-05, g = KD-06, h = KD-07,
  i = KD-08.
- **Lo encontrado al verificar**, de KD-01 a KD-14, está en
  `validation/pilot_v1/KNOWN_DEFECTS.md`.

**PROBLEM**

Al probar DF-10 y la ingesta del validation corpus con frases sintéticas
escritas para las pruebas (no del corpus), aparecieron defectos distintos de los
autorizados. Por control de alcance se registran y no se corrigen (§63).

**EVIDENCE**

Cada fila se reprodujo con `parse_family_actions` o por la página real.

| # | Prioridad | Defecto | Ejemplo sintético |
|---|---|---|---|
| a | **HIGH** | Una lista de preparación pierde miembros según cómo empiece | «Monitor, vía venosa y oxígeno por mascarilla a 8 L/min» → sólo acceso venoso; sin «Monitor,» → sólo oxígeno |
| b | **HIGH** | Una cláusula de repetición condicional vuelve condicional la orden entera, y la orden queda como modelo de trabajo | «Salbutamol 5 mg + ipratropio 0.5 mg nebulizados ahora, repetir cada 20 minutos por 3 veces si persiste…» → nada se ejecuta ahora |
| c | MEDIUM | «nebulizados» (masculino plural) no se lee como vía; una vía compartida al final de una lista queda sólo en el último fármaco | «salbutamol + ipratropio … nbz» → salbutamol sin vía; se pide aclaración |
| d | MEDIUM | Un texto escrito con una aclaración pendiente se toma como su respuesta: la orden que trae no se ejecuta y su vía se asigna a la orden retenida | Aclaración de vía pendiente + «Hidrocortisona 200 mg ev» → salbutamol «IV», que se vuelve a rechazar; la hidrocortisona no se ordena |
| e | LOW | «si» como «whether» se lee como condicional | «reevaluar … si puede hablar frases completas» → plan condicional |
| f | MEDIUM | «OK to discharge with…» no se reconoce como alta | Registrado en DF-10 |
| g | MEDIUM | Una receta unida al alta con «with/con» se pierde | «con paracetamol», «with ibuprofen» |
| h | LOW | «con hora en policlínico» no se lee como cita | — |
| i | LOW | Cuatro líneas del mensaje de la orden retenida sin traducción | «I recognised…», «Still to state…», «In your own words…», «What you already wrote is kept.» |

**Qué no es un defecto.** Oxígeno sin flujo absoluto («O2 por mascarilla para
saturar sobre 94 %») se retiene por diseño. El piloto medirá si los clínicos lo
consideran una aclaración innecesaria.

**RECOMMENDATION**

- **a y b:** corregir por clase en el ciclo 4, con pruebas de frases nuevas.
  Ninguno viene del corpus, así que corregirlos no lo contamina.
- **d:** revisarlo junto con la Fase 2, porque es interacción en vivo.
- **Resto:** según capacidad.

**ALTERNATIVES**

- Esperar al piloto para dimensionarlos. Así el piloto mide un motor con
  defectos ya conocidos.

**COST / EFFORT**

- a y b: una sesión cada uno.
- c, e, f, g y h: horas.
- i: minutos.

**RISK**

- Tocar el lector compartido: se mitiga con regresiones, el corpus de ensayo
  EN/ES y la suite completa.

**DECISION NEEDED**

¿Autoriza corregir a y b, y cuáles más, en el ciclo 4?

---

### DF-19 · KD-01 · CERRADO en el ciclo 5

- **Qué se hizo:** la corrección por clase de la vía escrita antes del fármaco,
  incluida la misma confusión dentro de una lista.
- **Pruebas:**
  - 53 pruebas nuevas;
  - corpus de ensayo idéntico en ES y EN;
  - 56 de 56 regresiones;
  - suite completa verde en `ec1c77f`.
- **Detalle:** `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, sección del ciclo 5.
- **Lo que queda aparte:**
  - KD-15, el fluido nombrado en palabras (otra causa);
  - KB-02, «IN» antes del fármaco (por diseño);
  - KD-04, si el piloto lo muestra frecuente.

---

### [METHODOLOGICAL REVIEW] DF-14 · Vínculos PARTIAL inactivos

**PROBLEM**

La verificación del ciclo 2 encontró vínculos textuales cuya contribución no se
puede describir con claridad. Por la regla de §93 no se activaron.

**EVIDENCE**

`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md` §6 lista 9 inactivos:

- **R1-03:** PC5 L3, ME 2.2 vía TD1 h8, ME 2.4.
- **R1-04:** PC6 L1/L4, ME 4.1 vía TP6 h4 y C1 h6, ME 2.4.
- **R2-01:** PC1 L3 (segunda oración), MK1 L3, ME 2.4.

Cada uno trae el motivo.

**RECOMMENDATION**

Mantenerlos inactivos. Activar alguno sólo si el docente puede enunciar el
componente observado y lo que queda fuera.

**ALTERNATIVES**

- Activar PC5 en R1-03 como PARTIAL condicionado a que la prioridad sea un
  fármaco. Exigiría una condición por encuentro que hoy no existe.

**COST / EFFORT**

- Revisión docente: minutos.
- Activar uno: una línea de datos y su test.

**RISK**

Evidencia más débil presentada como contribución.

**DECISION NEEDED**

¿Se mantienen inactivos?

---

### [STRUCTURAL] DF-12 · Regla de transición para objetivos NOT REVIEWED

**Qué se implementó** (§56, el mecanismo más conservador y reversible):

- Un objetivo sin declaración en un caso conserva la regla anterior, rotulada
  `transition_fallback`: TD1, F1, C1, C3 y C4 en todo encuentro (C14 ya sólo en
  `acs_54m_inferior`, el único caso sin revisar), y un
  Decision Challenge sólo en el encuentro generado para él.
- NOT REVIEWED nunca es NO.
- Los registros legados reciben la misma regla y nunca las declaraciones
  actuales.

**Evidencia:**

- `observation_opportunities.py`;
- `test_observation_opportunities.py` (19 tests);
- `docs/OBSERVATION_OPPORTUNITIES.md` §3.

**Efecto hoy:** ninguno sobre la elegibilidad, porque ningún caso declara
todavía.

**Cómo se retira:** caso por caso, al aprobar su declaración (DF-13).

**DECISION NEEDED:** confirmar la regla. Alternativa: cerrar C14 a los casos
no revisados, lo que quitaría oportunidades antes de revisarlas.

---

### [METHODOLOGICAL REVIEW] DF-17 · *Faculty override*: registrar que una oportunidad no ocurrió

**Hoy:**

- La evidencia esperable es guía, no lista blanca.
- El docente puede reconocer evidencia no prevista o simplemente no valorar.
- No hay un registro explícito de «la oportunidad declarada no ocurrió en este
  encuentro».

**No se implementó.** No hacía falta para el piloto (§ «no implementes
mecanismos complejos de override»).

**RECOMMENDATION:** esperar a que la activación de C14 muestre si hace falta.
Si hace falta, el diseño mínimo es un desenlace de valoración «oportunidad no
ocurrida», con motivo y auditado, que no cuente como observación.

**DECISION NEEDED:** ¿se necesita, y cuándo?

---

### [CLINICAL + METHODOLOGICAL REVIEW] DF-4 · C2

- **Sin cambios en el ciclo 3.** C2 sigue deshabilitada (`objective_not_enabled`
  en la resolución de oportunidades).
- **Evidencia:**
  - `docs/AUDITORIA_OPORTUNIDAD_C2.md`;
  - EPA Guide v1.1, p. 20: C2 pide variedad, incluido el trauma penetrante,
    el entorno clínico y los casos pediátricos;
  - el banco tiene 2 casos adultos.
- **RECOMMENDATION:** mantenerla deshabilitada. Si se habilita, que sea caso por
  caso mediante declaraciones de oportunidad.
- **DECISION NEEDED:** ¿qué amplitud de casos trauma consideraría suficiente? Es
  una decisión clínica; el AI Advisor no propone un número.

---

### [LOW PRIORITY] DF-18 · Evidencia de fuentes externas (multisource)

- **Por qué hoy no cabe:** la unidad de evidencia es una fila de
  `mrs_progress_observations`, con `attempt_id NOT NULL`. Sólo el simulador
  produce evidencia (`evidence_source: management_reasoning_simulator`).
- **Qué haría falta:** otra fuente (observación directa, OSCE) necesitaría su
  propia tabla con el mismo formato de contribución y su propio
  `evidence_source`.
- **No se implementó** (fuera de alcance, §52).
- **DECISION NEEDED:** ninguna ahora.

---

### [METHODOLOGICAL REVIEW] DF-9 · Penalidad −3, doble efecto de safety y varios eventos por una conducta

- **Se mantiene sin cambios** (charter §19 a §22 y §47):
  `max(0, base − 3 × eventos confirmados)`, el doble efecto sobre D3 y el total,
  y la acumulación de eventos.
- **Los eventos críticos siguen siendo una señal independiente.**
- **DECISION NEEDED:** ninguna ahora.

---

### [LOW PRIORITY] DF-11 · Residuos menores de la lectura

- **«since» en inglés.** No se lee como razón, porque también es temporal.
- **En inglés, «and I will».** «to reduce the congestion and I will recheck…»
  registra «and I will» dentro de la expectativa.
- **Hiperkalemia.** «Hyperkalemia with peaked T waves» e «Hiperkalemia con T
  picudas» no se leen como modelo: el vocabulario de hallazgos es cerrado.
- **Ortografía corregida en las citas.** «rythm» → «rhythm» y «urianalysis» →
  «urinalysis»; lo fijan las regresiones v0814 y v0816.
- **Guion 5, decisión 9.** «por» en español no se lee como causal.
- **`objectives.TARGET_SOURCE`.** Cita las páginas de la edición v1.0 de la EPA
  Guide.
- Los defectos nuevos del ciclo 3 están en DF-16.
- **DECISION NEEDED:** ninguna urgente.

---

### DF-5 · C15

Deshabilitada, sin cambios. No hay encuentros diseñados para cuidados al final
de la vida.

---

## Decidido en el ciclo 3 · registro

### DF-1 · Observation opportunities · IMPLEMENTADO

**Decisiones D-1 a D-6, como se aprobaron:**

- el bloque `objectives` en la declaración del caso;
- tres estados (YES / NO+RAZÓN / NOT REVIEWED);
- congelado con el encuentro;
- evidencia esperable como guía;
- borrador de C14 para revisión docente;
- observaciones incidentales posibles.

**Detalle:** `docs/OBSERVATION_OPPORTUNITIES.md`.

**Tests:**

- 19 en `test_observation_opportunities.py`;
- 15 en `test_foundation_challenges_as_objectives.py`;
- tests previos actualizados donde la especificación aprobada cambia la regla,
  con comentario.

### DF-2 · R1-03, R1-04 y R2-01 · IMPLEMENTADO

- **Vínculos:** 12 activos, cada uno con tipo, componente observado, lo que queda
  fuera, fuente, versión y página.
- **Etiquetas:** DIRECT y PARTIAL son etiquetas, no pesos.
- **Unidad de evidencia:** una observación confirmada, con sus contribuciones en
  la columna nueva `provenance_json`. No hay tabla nueva.
- **Automatismo:** el encuentro generado para el desafío es oportunidad, no
  evidencia.
- **Brief:** prompt 1.6. Los briefs anteriores conservan su lista de objetivos.
- **Inactivos:** en DF-14.

### DF-6 · Validation corpus · DISEÑO CAMBIADO E IMPLEMENTADO

- **Diseño:** el docente reemplazó las 240 frases por la Fase 1: médicos que
  escriben en Word a partir de casos.
- **Implementado:**
  - plantilla;
  - ingesta DOCX determinista por la página real, sin parser paralelo;
  - hojas de anotación y adjudicación;
  - métricas y trazabilidad;
  - guarda del sellado fuera del repositorio;
  - versionado y procedencia.
- **Complejidad de la ingesta:** no resultó mayor que lo previsto. El único
  hallazgo fue que el harness del ensayo resolvía una sola retención por paso.
  Se agregó `resolve_until_clear`, opcional; los 20 guiones no cambian.
- **Piloto:** en DF-15.

### DF-10 · Seguimiento pegado al alta · IMPLEMENTADO

- **Resultado:**
  - el seguimiento se conserva en EN y ES;
  - también las indicaciones de regreso;
  - el alta se ejecuta;
  - sin duplicarse, en el orden del texto y sin aclaraciones nuevas.
- **Antes/después:** de 10 altas con plan, el seguimiento se perdía en 7 y ahora
  se conserva en 9. La décima («OK to discharge») es otro defecto (DF-16 f).
- **Tests:** 17 nuevos.
- **Detalle:** `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, «Ciclo 3».
- **Test en rojo que se pasó por alto:** un test del ensayo esperaba el orden
  anterior del plan. Llegó en rojo al commit `9d35b00`, ya empujado. Se corrigió
  en `e54b919`, porque la secuencia aprobada es la del texto.

### DOC-1 · §51 · CERRADO

Se completó sólo con «residente.». Ningún otro bloque literal del charter
cambió. El addendum A1 (§102–§109) se agregó después de la §101.
