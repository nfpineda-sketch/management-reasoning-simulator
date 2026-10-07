# B-5 · Paquete de firma docente prepiloto

> **Material de revisión, no de aprobación.** Este paquete ordena lo que espera su firma antes del piloto con
> residentes. No aprueba nada, no marca ninguna casilla y no cambia ningún texto: cada decisión queda en blanco
> (APPROVE · REVISE · DEFER). Las recomendaciones son del AI Advisor; decide usted.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · textos leídos en `f5096ae` (el runtime es el del candidato de B-1,
> `8ff41a4`). Fase 0 cerrada. B-1, B-2, B-3, B-4 y B-6 resueltos. **B-5: BLOCKED** hasta estas decisiones.

**En una mirada:** 100 decisiones antes del candidato final, más 3 opcionales de la 41m.

- **TIER 1 — REVISAR CON CUIDADO:** 55.
- **TIER 2 — redacción clínica:** 43.
- **TIER 3 — redacción operativa o de pantalla:** 2.
- **Deben actualizarse antes de firmarse:** las dos guías.
- **Antes de congelar el candidato final:** el relato en español de los 30 casos y la rúbrica en español
  (decisiones docentes del 2026-10-07). El relato aprobado entra en el candidato en
  `case_text/es/approvals.json` (4.1).
- **Después del despliegue, antes del GO:** ningún texto de este paquete; sólo lo de 4.4.
- **Decididas al 2026-10-07:** 87 de las 100: todo el nivel 1 y 30 de nivel 2; quedan 13, todas de nivel 2 (K-E5 a
  K-E17). H-62 e I-63 se decidieron DEFER de la firma: siguen sin firmar a propósito, así que las firmas abiertas
  son 15. Aparte, la redacción de los estados límite de la 49m (A-6a, A-6b, A-7-49m y A-8a) quedó aprobada, sin
  implementar (bloque A).

Los criterios de cada nivel están en 0.4.

**Fuentes, sin reemplazarlas:**

- `docs/revision/CIERRE_PREPILOTO.md` §2 (64 filas y el E-FAST);
- `docs/revision/R4_FRASES_MOTOR.md`, `docs/revision/F0_11_FRASES_ES.md`, `docs/revision/R2_POCUS_C14.md`, `docs/tdfc/TDFC_TABLA_FINAL.md`;
- las dos guías;
- el código que tiene los textos activos;
- las filas B-5 y F0 del Decision File;
- `docs/revision/PRE_DEPLOYMENT_READINESS_2026_10_06.md` (6, 10.1, 10.2, 16.4, 18.2, 20.5).

Las casillas «☐» del §2 y de las hojas siguen siendo el registro de la firma. Este paquete sólo las ordena y agrega lo que la Fase 0 cambió.

## 0. Cómo leer este paquete

### 0.1 Estado de cada texto

| Estado | Qué quiere decir |
|---|---|
| **ACTIVE** | Está en el código y la sala (o el portal docente) ya lo muestra |
| **DRAFT** | Está escrito, como borrador en el código o sólo en un documento, y no se muestra hasta activarlo con un cambio registrado |
| **DOCUMENTATION ONLY** | Un documento (guía, ficha, tabla) que la app no muestra; firmarlo no cambia el runtime |
| **POST-DEPLOYMENT REVIEW** | Se aprueba en la base desplegada (tablero docente), después del despliegue y antes del GO del piloto. Desde el 2026-10-07 ningún texto de este paquete queda en este estado: el relato y la rúbrica pasaron a antes del candidato final (sección 4) |

Cuando el inglés y el español están en estados distintos, cada ítem dice los dos (por ejemplo, «EN ACTIVE · ES DRAFT»).

### 0.2 Su decisión y el SHA final

Cada ítem tiene un campo en blanco: **APPROVE** (tal como está) · **REVISE** (diga el cambio) · **DEFER** (más adelante). Qué le pasa al SHA final del despliegue en cada caso:

- **S-A · texto ACTIVE en el código.** APPROVE: el SHA no cambia. REVISE: cambio de código → nuevo SHA final → suite, regresiones y B-1 de nuevo (contrato de promoción, 16.4). DEFER: el texto sigue activo sin firma; B-5 sólo se cierra con él si usted acepta expresamente pilotear así.
- **S-B · borrador en el código (`spanish_drafts.py`) o sólo en un documento.** APPROVE: por sí sola no cambia el SHA (el borrador sigue sin mostrarse). Mostrarlo es activarlo (X-1): cambio de código → nuevo SHA → 16.4. REVISE: si el borrador está en `spanish_drafts.py` (fuera de `docs/`), cambiarlo da un nuevo SHA y, por la regla de 18.2, B-1 de nuevo; si sólo está en un documento (el aviso de la foto), es un cambio de documentación (S-C). DEFER: sin cambio; la sala sigue en inglés.
- **S-C · DOCUMENTATION ONLY bajo `docs/`.** APPROVE: sin cambio. Actualizarlo es un commit sólo de documentación: el SHA cambia, el runtime no, y B-1 sigue válido si `git diff 8ff41a4 <final> -- . ':(exclude)docs'` queda vacío (18.2). Ninguna prueba lee las guías.
- **S-D · documento generado desde el código (fichas R-2, tabla TDFC).** APPROVE: sin cambio. REVISE: cambia el banco o el caso (runtime) o las notas de revisión (`pocus_review_notes.py`, fuera de `docs/`), y la hoja se regenera → nuevo SHA → 16.4 y B-1 de nuevo (18.2).
- **S-E · POST-DEPLOYMENT REVIEW en la base desplegada.** Aprobar en el tablero: sin cambio de SHA. «Pedir cambios»: el caso (o el dominio) sigue en inglés. Corregir el texto es un cambio del repositorio (`case_text/es/*.json`, `rubric_text/es/descriptors.json`) → nuevo SHA → 16.4 completo y un nuevo despliegue. Desde el 2026-10-07 no se aplica a ningún texto de este paquete: el relato y la rúbrica se revisan antes de congelar el candidato final (sección 4).

### 0.3 Recomendación (del AI Advisor, no es una decisión)

- **APPROVE AS IS**: fiel y sin problema conocido.
- **REVIEW CLOSELY**: correcto en lo que se pudo verificar, pero con una ambigüedad, una limitación del motor o una convención que usted debe mirar.
- **NEEDS UPDATE BEFORE SIGN-OFF**: no puede firmarse como está.

### 0.4 Niveles de revisión

- **TIER 1 — REVISAR CON CUIDADO** (55 decisiones). Puede cambiar la interpretación del residente, una decisión de manejo, la validez de la evaluación, el sentido de una limitación del motor o su puntaje. Es nivel 1 un texto que:
  - dice si algo se dio, se hizo, se programó o se repitió;
  - gobierna el reloj;
  - atribuye una causa o juzga el manejo;
  - declara un límite o lo que no se evalúa;
  - es un criterio de evaluación (C14, R-2, TDFC);
  - tiene una ambigüedad conocida o un sentido distinto en inglés y en español.
  - Las dos guías también son nivel 1.
- **TIER 2 — redacción clínica** (43): hallazgos y rótulos clínicos con el mismo sentido en ambos idiomas, sin ambigüedad conocida.
- **TIER 3 — redacción operativa o de pantalla** (2): avisos, activación y alcance.

### 0.5 Cómo se cuenta

- Una decisión es un campo «Decisión docente» en blanco.
- Textos idénticos comparten una decisión: «UNA DECISIÓN → …».
- No se juntan textos parecidos con distinto sentido clínico, ni el mismo criterio con otra redacción: se marcan «VINCULADA» para decidirlos a la vez.
- Las correcciones de cada guía se marcan una por una, pero cada guía es una decisión.
- Las tres filas sólo de `trauma_hemothorax_41m` llevan su campo, pero son opcionales: el caso está fuera del piloto de residentes (F0-2; sección 3).

## 1. Resumen

### 1.1 Decisiones antes del candidato final

| Bloque | Requeridas | TIER 1 | TIER 2 | TIER 3 | Opcionales (41m) |
|---|---|---|---|---|---|
| X-1 · Activación del español | 1 | 0 | 0 | 1 | — |
| A · R-4: 18 frases del motor | 18 | 3 | 15 | 0 | — |
| B · Notas de la TEP y aviso del sangrado | 8 | 8 | 0 | 0 | — |
| C · Líneas del examen y E-FAST | 12 | 1 | 11 | 0 | 1 |
| D · Límites declarados | 5 | 5 | 0 | 0 | 1 |
| E · C14 de la 52m y la 70f | 2 | 2 | 0 | 0 | — |
| F · R-2: 14 fichas POCUS | 13 | 13 | 0 | 0 | 1 |
| G · R-3: TDFC final | 1 | 1 | 0 | 0 | — |
| H · Guía docente | 1 | 1 | 0 | 0 | — |
| I · Guía del residente | 1 | 1 | 0 | 0 | — |
| J · Aviso de la foto | 1 | 0 | 0 | 1 | — |
| K · F0-11: frases nuevas de la Fase 0 | 37 | 20 | 17 | 0 | — |
| **Total** | **100** | **55** | **43** | **2** | **3** |

Recomendación del AI Advisor sobre las 100 requeridas:

- APPROVE AS IS: 89;
- REVIEW CLOSELY: 9;
- NEEDS UPDATE BEFORE SIGN-OFF: 2.

Actualización del 2026-10-07: con X-1 cerrada, A-9 pasa de REVIEW CLOSELY a NEEDS REVISION del inglés (`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, sección 3). Al preparar sus lotes, tres más dejaron APPROVE AS IS por hallazgos comprobados en el motor: K-18 (REVISE; TD-82), A-6 (REVIEW CLOSELY; TD-83) y K-E5 (NEEDS REVISION; TD-82).

**Decisiones docentes registradas (2026-10-07):**

- X-1: APPROVE (a), con el alcance ampliado (sección 2, X-1).
- Lote 1 de nivel 1: A-1 y B-19 a B-25, APPROVE; A-2 y A-9, REVISE.
- Lote 2 de nivel 1: B-26, C-37, D-39, D-40, D-41, D-43, E-45, E-46 y F-47, APPROVE; D-42, REVISE, con su
  español propio, aprobado después (bloque D-42).
- Lote 3 de nivel 1: F-48 a F-57, APPROVE. F-49, F-53 y F-54 llevan sus límites vinculantes (D-41, E-46 y D-42).
- J (aviso de la foto): APPROVE, con el español en «tú».
- A-2: redacción final docente para el estado de agotamiento (bloque A).
- Lote 4 de nivel 1: F-58, F-60, G-61, K-1 y K-2 (una decisión), K-3 y K-4, APPROVE; K-5 y K-6, APPROVE, con la
  regla de X1-0 cuando la orden nombra un fármaco; H-62 e I-63, DEFER de la firma: no es un rechazo, se firman
  cuando describan el candidato final.
- L-17 y M-02, confirmadas (sección 2, X-1).
- Lote 5 de nivel 1: K-7 a K-16, APPROVE. K-13 y K-14, con la regla de X1-0; en K-9, la mayúscula tras «sin
  pulso:» es cosmética; K-16 conserva la semántica de F0-12.
- Lote final de nivel 1: K-17, K-19, K-20 y K-21, APPROVE; K-18, REVISE con la redacción docente (TD-82), sin
  implementar.
- **Nivel 1 completo (2026-10-07):** todas sus decisiones están tomadas. H-62 e I-63 siguen sin firma a
  propósito, hasta que exista el candidato final implementado: no es un rechazo y no reabre el nivel 1.
- Lote 1 de nivel 2: A-3, A-4, A-5, A-7, A-8, A-10, A-11, A-12 y A-13, APPROVE; A-6, REVISE: en la 49m, el
  examen respiratorio conserva la gravedad de llegada mientras la obstrucción no mejore (TD-83), sin implementar.
  Al implementar A-9, A-10 y A-11, la frecuencia se escribe «{n}/min» (cosmético, no es otra decisión).
- Lote 2 de nivel 2: A-14 a A-18 y C-27 a C-31, APPROVE; C-31 es una sola decisión para sus dos casos.
- A-6 sigue en REVISE: la redacción de sus estados límite y de A-8 se propuso para la firma (bloque A, «A-6 y
  A-8 · Estados límite»), sin implementar.
- Lote 3 de nivel 2: C-32, C-33, C-35, C-36, C-38, C-EFAST y K-E1 a K-E4, APPROVE.
- Estados límite de la 49m (bloque A): A-6a, A-6b y A-8a, APPROVE, con sus condiciones de uso. A-7 se reabre sólo
  para la 49m con la obstrucción todavía en el estado grave de llegada: es una revisión acotada, con la variante
  docente A-7-49m, y no una trayectoria clínica nueva. A-6 sigue en REVISE hasta implementarse; nada de esto está
  implementado (TD-83).
- Quedan 13 de las 100, todas de nivel 2 (K-E5 a K-E17). Con las firmas de H-62 e I-63 son 15 firmas abiertas.
- El relato en español de los 30 casos se revisa antes de congelar el candidato final, que no se congela sin esa
  revisión (4.1). Reemplaza la decisión anterior del mismo día (después del despliegue). Su aprobación entra en el
  candidato en `case_text/es/approvals.json` (camino a, 4.1).
- La rúbrica en español también se revisa antes de congelar el candidato final (4.2).
- X1-0 alcanza también a los documentos que se ofrecen al residente en español (sección 2, X-1).
- El español que falta para X-1 está redactado para revisión (`docs/revision/X1_ESPANOL_PROPUESTO.md`); sus
  decisiones de base están en la sección 2, X-1.
- Antes del candidato final se limpian las claves internas que ve el residente, sin cambiar las canónicas
  (sección 2, X-1).
- Ninguna revisión está implementada.

Además (sección 4):

- **antes de congelar el candidato final** (decisiones docentes del 2026-10-07): el relato en español de los 30
  casos, que incluye el español de las filas 27–36, y los descriptores de la rúbrica en español;
- **después del despliegue y antes del GO:** ningún texto de este paquete; sólo lo de 4.4.

### 1.2 Decisiones agrupadas (texto idéntico)

Son 3:

1. **UNA DECISIÓN → K-1 y K-2** (filas 1 y 2 de F0-11): la misma frase «No se entendió…»; sólo cambia la cita. Agrupada en este paquete.
2. **UNA DECISIÓN → C-31** en `renal_colic_34m` y `bradycardia_bb_54f` («No rash.» / «Sin erupción.»). El §2 ya la agrupaba.
3. **UNA DECISIÓN → D-42** en `pneumonia_46f` y `pneumonia_83m`. El §2 ya la agrupaba.

**VINCULADAS, no agrupadas** (decidirlas a la vez; su texto o su sentido difieren):

- D-41 ↔ E-46: el criterio D-8 de la 70f, en dos redacciones;
- E-45 ↔ F-47: el componente y la evidencia C14 de la 52m;
- F-53 ↔ F-54 y F-55 ↔ F-56: el mismo texto C14 en las dos neumonías y en los dos edemas pulmonares; cada ficha revisa además su propio POCUS de llegada, por eso no se agrupan;
- B-26 ↔ D-40: el sangrado tras la lisis en la 33f;
- A-1 ↔ K-E4 ↔ K-7: tres nombres del mismo paro, también en inglés;
- K-18 ↔ K-21: el paro de la anafilaxia;
- J ↔ H-6 ↔ I-9: el aviso de la foto y las guías que lo citan.

### 1.3 Deben actualizarse antes de poder firmarse

- **H · Guía docente** (fila 62): 11 correcciones, 2 de nivel 1, entre ellas una sección nueva sobre la sala de la Fase 0.
- **I · Guía del residente** (fila 63): 9 correcciones, 6 de nivel 1.

Ninguna se editó aquí. Ningún otro ítem necesita cambios para poder firmarse.

**2026-10-07:** las correcciones H e I se aplicaron a las guías, que siguen sin firma. El ANTES → DESPUÉS y los
desvíos están en `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, sección 1.

### 1.4 Hallazgos verificados en el código que cambian la lectura del §2

1. **Filas 12–18 de R-4 («activo» en el §2).**
   - El español está en `language.py`, pero sólo lo usa `language.say`, que traduce las entradas de la sala.
   - El panel del examen, donde se leen esas frases, usa `language.examination`, que no las conoce. En un encuentro en español se ven enteras en inglés.
   - El propio código lo anota en `spanish_drafts.py`.
   - Comprobado: `language.examination(<fila 12>, "es")` devuelve el inglés y `language.say(...)` el español.
   - Activas en inglés, sí; en español, sólo si la frase llega en una entrada.
2. **Filas 1–11 de R-4 («borrador»).** El inglés está activo. En un encuentro en español se ven enteras en inglés: en el panel del examen, y la fila 1 como entrada. Comprobado: ninguna aparece dentro de una entrada traducida; no hay líneas mezcladas.
3. **30 casos, no 31.** El §3 del cierre dice «los 31 casos»; F0-2 deja fuera `trauma_hemothorax_41m`. Las filas 34, 44 y 59 son sólo de ese caso. Este paquete no corrige el cierre, que es un registro histórico.
4. **Aviso de la foto (fila 64).** El español propuesto no está en el código; existe sólo en el §2.
5. **Fila 26.** El código tiene dos variantes más del sitio del sangrado, que ningún caso del banco usa.
6. **Límites.** El encabezado de la fila 39 también encabeza las limitaciones que los 31 casos declaraban antes del cierre prepiloto, todas en inglés (por ejemplo, «The engine does not perform angiography; a referral is recorded, not its result.»). No están en la lista de firmas del §2, y este paquete no las agrega.
7. **Relato y rúbrica en español.** El tablero sólo permite aprobar o pedir cambios; no edita el texto. Corregir una traducción es un cambio del repositorio, y por lo tanto un SHA nuevo (sección 4).

### 1.5 Qué bloquea B-5 y qué no

- **Bloquean:** las 100 decisiones requeridas de la sección 2. Si se difiere un texto activo, hace falta además su acuerdo expreso de pilotear con él sin firma.
- **No bloquean:** las 3 opcionales de la 41m si se difieren (sin cambio de SHA) y `MRS_LANGUAGE`, una configuración de los Secrets que no es un texto ni cambia el SHA.
- **No están entre las 100, pero el candidato final no se congela sin ellas** (decisiones docentes del 2026-10-07): la revisión del relato en español (4.1) y la de la rúbrica en español (4.2).
- **Orden recomendado:**
  1. las decisiones de nivel 1;
  2. X-1, una vez decididos A y J;
  3. las correcciones de H e I;
  4. la firma de las guías actualizadas, cuando describan el candidato final (H-62 e I-63, DEFER de la firma,
     2026-10-07).
- **Después:** el candidato final se construye con lo aprobado (16.4). Las guías se actualizan y se firman sobre ese
  candidato: es un cambio sólo de documentación (18.2).

## 2. ANTES DEL CANDIDATO FINAL

### X-1 · Activación del español que hoy no se muestra

Decisión transversal de los bloques A y J. **TIER 3.**

- **Qué es:** aprobar un texto en español no lo muestra. Hoy, en un encuentro en español, se ven enteros en inglés: las filas 1–11 de R-4 (borrador), las filas 12–18 de R-4 en el panel del examen (su español existe, pero sólo para las entradas; 1.4) y el aviso de la foto (fila 64; su español sólo está en el §2).
- **Opciones:** (a) activar antes del candidato todo el español que usted apruebe en A y J; (b) no activar: el piloto en español los muestra en inglés, línea por línea entera, y la guía del residente lo dice (I-2, I-9); (c) activar una parte (diga cuál).
- **Qué infiere el residente:** con (b), lee esos hallazgos del examen y ese aviso en inglés; el sentido no cambia, pero la lectura cuesta más.
- **SHA:** (a) y (c) son un cambio de código registrado, con sus pruebas → nuevo SHA → 16.4 (suite, regresiones y B-1). (b) no cambia el SHA.
- **Decide:** usted (qué ve el residente) y la persona responsable del encargo (autoriza el cambio de código).
- **Recomendación:** REVIEW CLOSELY — decidirla después de A y J; la opción (b) no bloquea B-5.
- **Decisión docente (2026-10-07):** ☒ APPROVE = (a), con el alcance ampliado de abajo · ☐ REVISE = (c) · ☐ DEFER = (b).
- **Alcance decidido:**
  - el piloto es bilingüe;
  - en el candidato final, todo texto que ve el residente durante un encuentro en español es enteramente español,
    salvo los nombres canónicos de fármacos y los códigos que se dejan sin cambiar a propósito;
  - incluye F0-11, las filas 1–18 de R-4, el aviso de la foto, las preguntas de aclaración, el texto de la
    compuerta de razonamiento y los rótulos que ve el residente;
  - no se acepta una interfaz mezclada en inglés y español en el candidato final.
- **Sin implementar.** Lo que falta está en el Decision File (2026-10-07, octava actualización) y en
  `docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, 2.5.
- **Borrador del español que falta** (autorizado el 2026-10-07 para revisión, no para implementar):
  `docs/revision/X1_ESPANOL_PROPUESTO.md`, con 100 formulaciones únicas, 7 vocabularios y la fuente de cada frase.
- **Decisiones de base del borrador (docente, 2026-10-07), sin implementar:**
  - APPROVE: X1-0 (convenciones), I-10 (el resumen de la orden retenida reusa las etiquetas del registro), L-01
    (Conversar · Examinar · Exámenes · Tratar), V-4 (Respiración y Pulmonar, regiones distintas), M-02 (Urgencias /
    Cama 03) y L-17 (ORDER CANCELLED / ORDEN CANCELADA);
  - aclaración de X1-0: en un encuentro en español, los fármacos que el motor inserta en un texto también se
    muestran con su nombre en español; el identificador canónico guardado puede seguir en inglés (K-13);
  - A-2: redacción final docente (bloque A).
- **Claves internas (docente, 2026-10-07):** antes del candidato final se limpian las claves internas que ve el
  residente, en inglés y en español (por ejemplo, `beta_blocker` → beta blocker / betabloqueador;
  `ORDER_CANCELLED` → ORDER CANCELLED / ORDEN CANCELADA). Es sólo presentación: las claves canónicas no cambian
  (TD-80).
- **Documentos que se descargan (docente, 2026-10-07):** X1-0 rige también los documentos que la app ofrece
  expresamente en español al residente: en ellos, los fármacos visibles llevan su nombre en español, y los
  identificadores canónicos no cambian. No exige traducir lo que se guarda en inglés por diseño, como el ledger o
  el Trace canónico.
- **L-17 y M-02, confirmadas (docente, 2026-10-07, lote 4):** L-17, ORDER CANCELLED / ORDEN CANCELADA, con la
  clave canónica sin cambio; M-02, el renglón entero: «Urgencias / Cama 03», «Imagen del paciente · estado
  actual», «Actualizando la apariencia del paciente» e «Imagen actual del paciente no disponible».

### A. R-4 · Las 18 frases del motor (filas 1–18)

- **Dónde:** fila 1, entrada de la sala (CLINICAL UPDATE) al paro hemorrágico, `trauma_hemorrhage.py:75`. Filas 2–11, panel del examen, región «Respiratory», `family_engine.py:3225–3247`. Filas 12–18, panel del examen, región «Vascular access» de la hipoglicemia, `glucose_rescue.py:202`. Borradores: `spanish_drafts.py:33` (`ENGINE`). Español activo de 12–18: `language.py:1197–1211`, que sólo usa `language.say`.
- **Estado:** filas 1–11, EN ACTIVE · ES DRAFT. Filas 12–18, EN ACTIVE · ES ACTIVE sólo en las entradas: el panel del examen, donde se leen, las muestra en inglés (`spanish_drafts.py:96`; 1.4).
- **SHA:** el inglés, S-A. El español 1–11, S-B. El español 12–18: APPROVE no cambia el SHA; mostrarlo en el panel es X-1; REVISE cambia `language.py` → nuevo SHA (16.4).
- **Columnas:** EN y ES exactos (`{n}` = número). «Se infiere»: lo que leerá el residente.

| # | Casos | EN exacto | ES exacto | Se infiere | Recomendación | Nivel | Decisión docente |
|---|---|---|---|---|---|---|---|
| A-1 | 27m (41m: sandbox) | Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume replaces a source that is still open. | Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido; la reposición de volumen no sustituye el control del sangrado activo. | El paro siguió a un sangrado que nunca se detuvo; reponer volumen no reemplaza controlar la fuente. Atribuye una causa. | **APPROVE AS IS** — redacción docente del 2026-09-30. En la 27m sin control el paro llega hacia el minuto 13 (C-LIMB-ARREST-13) y la frase es exacta. VINCULADA con K-E4 y K-7: el mismo paro se nombra «cardiac arrest from uncontrolled haemorrhage» al cortar una espera y «Cardiac arrest occurred at minute…» en el mensaje acordado, también en inglés. | TIER 1 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-2 | 75f | Bilateral inspiratory crackles with increased respiratory effort. | Crépitos inspiratorios bilaterales, con aumento del esfuerzo respiratorio. | Esfuerzo aumentado: el paciente todavía compensa. | **REVIEW CLOSELY** — TD-51 (diferida): sin tratamiento, el motor muestra esta frase durante 12–13 minutos en que el esfuerzo ya es «Exhausted»; el residente puede leer compensación donde hay agotamiento. La traducción es fiel; el problema es del motor y la guía docente lo declara (líneas 232–233). | TIER 1 | ☒ **REVISE** (docente, 2026-10-07): la traducción está bien, pero el examen no debe seguir diciendo «increased respiratory effort» cuando el estado es de agotamiento; el examen respiratorio que se muestra debe ser coherente con el estado. Sin implementar. Redacción final docente (2026-10-07) para el estado de agotamiento, con el criterio del motor de `X1_ESPANOL_PROPUESTO.md`, §9: EN «Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with exhaustion.» · ES «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz, compatible con agotamiento.» |
| A-3 | 58m, 75f | Bilateral crackles remain, with reduced respiratory effort. | Persisten crépitos bilaterales, con menor esfuerzo respiratorio. | La congestión mejora; el menor esfuerzo es mejoría, no agotamiento. | **APPROVE AS IS** — una prueba del motor fija que sólo aparece con la congestión en mejoría y nunca junto al agotamiento. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-4 | transfusión, cualquier familia | New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze. | Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin sibilancias. | Sobrecarga circulatoria por la transfusión, no broncoespasmo. | **APPROVE AS IS** — precisión del 2026-10-07: «cualquier familia» son todas salvo asma, edema pulmonar y opioides, cuya línea respiratoria la reemplaza (`family_engine.py:3222–3247`). Aparece al transfundir con hemoglobina de 10 g/dL o más y sin una hemorragia activa que reponer, y se instala en unos 30 minutos | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-5 | 24f, 49m | Improved air entry with residual expiratory wheeze. | Mejor entrada de aire, con sibilancias espiratorias residuales. | Responde a los broncodilatadores; persiste una obstrucción leve. | **APPROVE AS IS** — comprobado el 2026-10-07: aparece con broncodilatadores (minuto 6 con salbutamol e ipratropio), nunca con oxígeno solo. VINCULADA con A-8, que la repite | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-6 | 24f, 49m | Reduced bilateral air entry with prolonged expiration and wheeze. | Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias. | Obstrucción grave al llegar o sin respuesta. | **REVIEW CLOSELY** (2026-10-07; antes, APPROVE AS IS) — en `asthma_49m` la llegada dice «Severe effort with very poor bilateral air entry and only faint wheeze» (tórax casi silente). Desde la primera orden, aun con oxígeno solo, el motor muestra esta frase sin cambio fisiológico: el motor no distingue la gravedad de la 49m de la de la 24f. El examen se lee menos grave, y la vuelta de las sibilancias puede leerse como mejoría; la gravedad sigue en «General appearance» (somnoliento, esfuerzo «Severe»). Opciones: (a) APPROVE tal cual; (b) que el motor conserve el examen de llegada del caso mientras la obstrucción siga como llegó (cambio del motor, nuevo SHA). TD-83. VINCULADA con A-8 | TIER 2 | ☒ **REVISE** (docente, 2026-10-07): en `asthma_49m`, el examen respiratorio conserva la gravedad de llegada («very poor bilateral air entry and only faint wheeze») mientras la obstrucción no haya mejorado. Ninguna orden que no la mejore, tampoco el oxígeno solo, lo hace parecer menos grave: la frase no cambia por la sola ejecución de una orden. A-6 aparece sólo cuando describe el estado actual del motor, y A-5 sigue siendo la mejoría real tras el broncodilatador. Es redacción coherente con el estado: no cambia la trayectoria clínica ni la respuesta al tratamiento. Sin implementar (TD-83). Redacción de sus estados límite, aprobada el 2026-10-07: A-6a y A-6b (abajo) |
| A-7 | 24f, 49m | Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side. | Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado. | Neumotórax a tensión de ese lado: hay que descomprimir. | **APPROVE AS IS** — el motor escribe el lado del caso (`family_engine.py:3235`); el borrador cubre «izquierdo» para «left» (`spanish_drafts.py:72`). «En el otro lado» es claro. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07). Reabierta el mismo día sólo para `asthma_49m` con la obstrucción todavía en el estado grave de llegada: ahí rige la variante A-7-49m (abajo), una revisión acotada de la redacción y no una trayectoria clínica nueva. En `asthma_24f` y en cualquier otro estado sigue esta frase. Sin implementar (TD-83) |
| A-8 | 24f, 49m | Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze. | Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de aire, con sibilancias espiratorias residuales. | La descompresión funcionó; queda la obstrucción. | **APPROVE AS IS** — el lado, como en la fila 7. Su segunda parte es A-5 o, si la obstrucción sigue, A-6 (`family_engine.py:3233`): VINCULADA con las dos | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07). En la 49m, tras la descompresión con la obstrucción grave sin mejorar, rige A-8a (aprobada el 2026-10-07; abajo); con mejoría real tras el broncodilatador, este texto |
| A-9 | 35m, 67f | Respiratory rate {n} /min; assisted ventilation is in progress. | Frecuencia respiratoria {n}/min, dada por la ventilación asistida en curso. | EN: «12/min» puede leerse como respiración espontánea. ES: dice que es la frecuencia de la ventilación asistida. | **REVIEW CLOSELY** — TD-52 (a): el inglés activo no dice que la frecuencia es la de la ventilación asistida (el motor la fija en 12/min); el español sí. Aprobados tal cual, los dos idiomas dicen cosas distintas; corregir el inglés es un cambio de código (nuevo SHA). Actualizada el 2026-10-07, con X-1 cerrada (se mostrarán las dos versiones): **NEEDS REVISION** del inglés (`B5_GUIAS_Y_BRECHA_BILINGUE.md`, sección 3). | TIER 1 | ☒ **REVISE** (docente, 2026-10-07): se mantiene el español; el inglés pasa a «Respiratory rate {n}/min, provided by the assisted ventilation currently in progress.» Sin implementar |
| A-10 | 35m, 67f | Respiratory rate {n} /min; breaths remain shallow. | Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales. | Hipoventilación persistente: la naloxona o la ventilación todavía hacen falta. También es el examen de llegada, donde «siguen siendo» supone una mirada previa (sin cambiar el sentido). | **APPROVE AS IS** — nota cosmética del 2026-10-07: el inglés escribe «{n} /min» con un espacio que la redacción aprobada de A-9 no lleva; comparten el comienzo en el código, así que al implementar A-9 conviene escribir «{n}/min» en las tres, sin cambiar el sentido | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07); al implementar A-9, la frecuencia se escribe «{n}/min» en las tres (cosmético, sin otra decisión) |
| A-11 | 35m, 67f | Respiratory rate {n} /min; spontaneous breaths have greater depth. | Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas. | Responde a la naloxona («más profundas» que en el examen anterior). | **APPROVE AS IS** — nota cosmética del 2026-10-07: el inglés escribe «{n} /min» con un espacio que la redacción aprobada de A-9 no lleva; comparten el comienzo en el código, así que al implementar A-9 conviene escribir «{n}/min» en las tres, sin cambiar el sentido | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07); al implementar A-9, la frecuencia se escribe «{n}/min» en las tres (cosmético, sin otra decisión) |
| A-12 | 54m | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría. | La vía de llegada puede estar infiltrada: una pista para no usarla. | **APPROVE AS IS** — terminología R-4 («aumento de volumen»). En español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-13 | hipoglicemia | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación. | La vía funciona. | **APPROVE AS IS** — en español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-14 | hipoglicemia | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y doloroso a la palpación. | La vía falló al pasar la glucosa (extravasación). | **APPROVE AS IS** — en español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-15 | hipoglicemia | A second peripheral cannula in the right forearm; the site is clean. | Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio. | Hay una segunda vía, limpia. | **APPROVE AS IS** — en español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. Precisión del 2026-10-07: el motor pone la segunda vía siempre en el antebrazo derecho, aunque el residente nombre otro sitio; la sala lo dice en la nota del procedimiento. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-16 | hipoglicemia | An intraosseous needle in place (humeral). | Una aguja intraósea instalada (humeral). | Acceso intraóseo instalado (también tibial, esternal o femoral). | **APPROVE AS IS** — en español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. Comprobado el 2026-10-07: los cuatro sitios salen enteros en español («sternal» → «esternal»). | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-17 | hipoglicemia | An intraosseous needle in place; no site was recorded. | Una aguja intraósea instalada; no se registró el sitio. | Acceso intraóseo sin sitio registrado. | **APPROVE AS IS** — en español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |
| A-18 | hipoglicemia | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo. | La glucosa está pasando por esa vía: un estado, no una indicación. | **APPROVE AS IS** — redacción D-6 («pasa»), igual en la sala y en el borrador (`test_pe_notes_and_row_18.py`). En español hoy se ve en inglés en el panel del examen (1.4); mostrarla es X-1. El motor escribe siempre el 10 %; las tres vías posibles (la de llegada, la nueva y la aguja intraósea) salen enteras en español. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |

**A-6 y A-8 · Estados límite de la 49m** (con la variante de A-7) — redacción propuesta el 2026-10-07 y aprobada
por la docencia el mismo día; A-7-49m es redacción docente. Es la redacción que A-6 (REVISE) necesita antes de
implementarse; no suma decisiones a las 100. Sin implementar (TD-83).

| ID | Estado | EN propuesto | ES propuesto | Por qué | Decisión docente |
|---|---|---|---|---|---|
| A-6a | `asthma_49m`, respiración espontánea, obstrucción sin mejorar | Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver. | Esfuerzo respiratorio severo, con murmullo pulmonar muy disminuido en forma bilateral y solo sibilancias tenues. No logra completar una maniobra confiable de flujo espiratorio máximo. | Es el hallazgo de llegada del caso, sin cambio; su español es el del relato del caso (4.1). Sigue a la vista mientras el paciente respira solo y la obstrucción no mejora: una orden que no la mejora no hace parecer mejor el examen | ☒ **APPROVE** (docente, 2026-10-07): mientras siga respirando solo y la obstrucción no haya mejorado desde la llegada; la ventilación no invasiva cuenta como respiración espontánea |
| A-6b | `asthma_49m` intubado, obstrucción sin mejorar | Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze. | Tubo endotraqueal instalado: el murmullo pulmonar sigue muy disminuido en forma bilateral, con solo sibilancias tenues. | Conserva la gravedad de la obstrucción; «remains» y «sigue» no sugieren mejoría; no habla de esfuerzo espontáneo ni de flujo espiratorio máximo; empieza como C-28 y C-29, las frases con tubo de la anafilaxia | ☒ **APPROVE** (docente, 2026-10-07): con ventilación invasiva y la obstrucción todavía en el estado grave de llegada |
| A-7-49m | `asthma_49m` con el neumotórax a tensión sin descomprimir y la obstrucción todavía en el estado grave de llegada | Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left remains very poor, with only faint wheeze. | Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; en el lado izquierdo el murmullo pulmonar sigue muy disminuido, con solo sibilancias tenues. | Redacción docente. El examen no se lee menos grave que el estado, como pasaba con «wheeze on the other side». No cambia el momento del neumotórax, la fisiología de la obstrucción, la respuesta al broncodilatador ni a la descompresión, los signos vitales ni los eventos críticos: es sólo coherencia del examen con el estado | ☒ **APPROVE** (docente, 2026-10-07): revisión acotada de A-7 para `asthma_49m`, no una trayectoria clínica nueva |
| A-8a | `asthma_49m` tras la descompresión, obstrucción grave sin mejorar | Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, with only faint wheeze. | Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; sigue muy disminuido en forma bilateral, con solo sibilancias tenues. | Vuelve el murmullo del lado derecho, y la segunda parte dice el estado actual de la obstrucción, sin «improved» | ☒ **APPROVE** (docente, 2026-10-07): tras una descompresión eficaz, mientras la obstrucción grave no haya mejorado; con mejoría real tras el broncodilatador sigue el texto de A-8 ya aprobado |

- **A-8 tras la descompresión, con mejoría real por el broncodilatador:** no hace falta otra línea (confirmado por la
  docencia el 2026-10-07). Es el texto de A-8 ya aprobado («…; improved air entry with residual expiratory
  wheeze.»). El motor elige la segunda parte por el estado de la obstrucción (`family_engine.py:3229–3233`): nunca
  agrega «improved» si la obstrucción no mejoró.
- **A-8 tras la descompresión, con la obstrucción en el nivel de A-6** (la 24f, o la 49m con mejoría parcial): sin
  cambio, la variante ya aprobada con A-8 («…; reduced bilateral air entry with prolonged expiration and wheeze.»).
- **En la 24f**, A-6 ya describe su estado de llegada, con tubo o sin él: no necesita texto nuevo.
- **A-7 en la 49m (decidido el 2026-10-07):** la observación anterior de este bloque («wheeze on the other side»,
  entre A-6b y A-8a, se leía menos grave que «only faint wheeze») llevó a reabrir A-7 sólo para el estado grave de
  llegada de la 49m, con la variante A-7-49m. A-7 aprobada sigue en la 24f y en la 49m con la obstrucción ya mejorada.
- **Condiciones, para implementar** (aprobadas con cada redacción): «sin mejorar» y «estado grave de llegada»
  quieren decir que el índice de obstrucción del motor no bajó de su valor de llegada; «intubado», ventilación
  invasiva; la ventilación no invasiva cuenta como respiración espontánea. Cada condición se lee sobre el estado
  actual del motor en cada examen, como la segunda parte de A-8.
- **Comprobado en el motor (2026-10-07):** el neumotórax del asma ocurre sólo con ventilación invasiva y siempre a
  la derecha (`asthma_complications.step`, `family_engine.py:2392–2398`). A-7-49m y A-8a son, por lo tanto, de la
  49m intubada, y su lado fijo es exacto. Intubada con etomidato y rocuronio, el índice no baja de su valor de
  llegada y rige A-6b; con ketamina sí baja (el motor modela su efecto broncodilatador): es una mejoría parcial y
  rige A-6, ya aprobada.

### B. Notas de la TEP y aviso del sangrado (filas 19–26)

- **Estado:** ACTIVE en inglés y en español (D-4, D-5).
- **Dónde:** entrada de la sala al dar la trombólisis en `pulmonary_embolism_33f` y `pulmonary_embolism_61m`. EN `pe_obstruction.py:220` (notas 1–2), `:272` (3–5), `:249` (6–7), `:337` (aviso). ES `language.py:1060` (P-04/P-05), `:1081` (D-4), `:1092` (D-5).
- **SHA:** S-A. **Nivel:** TIER 1 las ocho (juzgan la indicación, atribuyen una causa o declaran una simplificación del motor).

**B-19 · Fila 19 · Nota 1 · shock obstructivo** — TIER 1 · ACTIVE
- EN: Systemic thrombolysis given in obstructive shock: systolic below 90 mmHg, or a vasopressor needed to reach 90 mmHg, with signs of hypoperfusion. In shock it is indicated as soon as the shock is present; the 15 consecutive minutes apply only to a hypotension without those signs. The drug acts on the clot over about half an hour; what it changes is seen on reassessment.
- ES: Trombólisis sistémica administrada en shock obstructivo: sistólica bajo 90 mmHg, o un vasopresor necesario para llegar a 90 mmHg, con signos de hipoperfusión. En shock está indicada desde que el shock está presente; los 15 minutos consecutivos aplican sólo a una hipotensión sin esos signos. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar.
- Se infiere: la lisis estaba indicada desde que el shock estaba presente; no había que esperar 15 minutos. Lo que cambie se verá al reevaluar.
- Recomendación: **APPROVE AS IS** — es el criterio D-4, el mismo del motor (`test_pe_notes_and_row_18.py`).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-20 · Fila 20 · Nota 2 · hipotensión sostenida** — TIER 1 · ACTIVE
- EN: Systemic thrombolysis given for sustained hypotension: systolic below 90 mmHg, or a vasopressor needed to keep it at 90 mmHg or above, for 15 consecutive minutes. The drug acts on the clot over about half an hour; what it changes is seen on reassessment.
- ES: Trombólisis sistémica administrada por hipotensión sostenida: sistólica bajo 90 mmHg, o un vasopresor necesario para mantenerla en 90 mmHg o más, durante 15 minutos consecutivos. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar.
- Se infiere: indicada por 15 minutos consecutivos de hipotensión sin signos de hipoperfusión.
- Recomendación: **APPROVE AS IS** — criterio D-4.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-21 · Fila 21 · Nota 3 · sin indicación, presión baja** — TIER 1 · ACTIVE
- EN: Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg with no sign of hypoperfusion, low for {m} of the 15 consecutive minutes a hypotension without them requires. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment.
- ES: Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg sin signos de hipoperfusión, baja durante {m} de los 15 minutos consecutivos que exige una hipotensión sin ellos. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar.
- Se infiere: durante el encuentro, la sala dice que se trombolizó antes de cumplir el criterio y que el riesgo de sangrado se asumió sin indicación: es una retroalimentación inmediata sobre la indicación.
- Recomendación: **APPROVE AS IS** — P-06 y D-4; los valores son los del minuto de la orden.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-22 · Fila 22 · Nota 4 · vasopresor innecesario** — TIER 1 · ACTIVE
- EN: Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg on a vasopressor the pressure does not need, with no hypotension from the embolism. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment.
- ES: Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg con un vasopresor que la presión no necesita, sin hipotensión por la embolia. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar.
- Se infiere: la presión no necesitaba el vasopresor y no había hipotensión por la embolia: sin indicación.
- Recomendación: **APPROVE AS IS** — el §2 abrevia «(sigue como la 3)»; aquí va el texto completo del código.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-23 · Fila 23 · Nota 5 · normotensión** — TIER 1 · ACTIVE
- EN: Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg, with no hypotension from the embolism. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment.
- ES: Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg, sin hipotensión por la embolia. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar.
- Se infiere: sin hipotensión por la embolia: sin indicación.
- Recomendación: **APPROVE AS IS** — el §2 abrevia «(sigue como la 3)»; aquí va el texto completo del código.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-24 · Fila 24 · Nota 6 · resto del esquema** — TIER 1 · ACTIVE
- EN: alteplase {n} mg recorded as part of the initial regimen begun at minute {t} ({total} mg in all). It completes the first dose rather than starting a new one, and the first dose keeps acting as before.
- ES: Se registran {n} mg de alteplasa como parte del esquema inicial comenzado en el minuto {t} ({total} mg en total): completan la primera dosis en lugar de iniciar una nueva, y la primera dosis sigue actuando como antes.
- Se infiere: lo que se dio completa la primera dosis; no es un segundo curso.
- Recomendación: **APPROVE AS IS** — el fármaco va en español («alteplasa»), como pidió D-5; las etiquetas de órdenes de la Fase 0 lo dejan en inglés (ver K-13).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-25 · Fila 25 · Nota 7 · segundo curso** — TIER 1 · ACTIVE
- EN: A second course of systemic thrombolysis is recorded (alteplase {n} mg); the first course began at minute {t}. Its added bleeding risk is recorded as exposure. This simulator represents neither additional reperfusion from a second course nor any bleeding of its own; that is a simplification, not evidence that repeating has no effect. The first dose keeps acting as before.
- ES: Se registra un segundo curso de trombólisis sistémica (alteplasa {n} mg); el primero comenzó en el minuto {t}. Su riesgo adicional de sangrado queda registrado como exposición. Este simulador no representa una reperfusión adicional por un segundo curso ni un sangrado propio; es una simplificación, no evidencia de que repetir no tenga efecto. La primera dosis sigue actuando como antes.
- Se infiere: el segundo curso queda registrado como exposición; el simulador no le da efecto propio, y lo dice como simplificación.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**B-26 · Fila 26 · Aviso del sangrado (33f)** — TIER 1 · ACTIVE
- EN: Bleeding from the surgical site operated on twelve days ago: the haemoglobin is falling. This is the risk the thrombolytic carries, and it was taken in a patient who had a reason to bleed.
- ES: Sangrado del sitio operado hace doce días: la hemoglobina está bajando. Es el riesgo que conlleva el trombolítico, y se asumió en una persona que tenía un motivo para sangrar.
- Se infiere: el sangrado es el riesgo del trombolítico, asumido en una paciente con un motivo para sangrar: atribuye la causa a la decisión.
- Recomendación: **APPROVE AS IS** — redacción D-5. El código tiene dos variantes más del sitio («an uncontrolled arterial pressure», «the declared site»), con su español, que ningún caso del banco usa hoy: sólo la 33f declara un riesgo de sangrado. VINCULADA con D-40 (la respuesta a ese sangrado no se evalúa).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

### C. Líneas del examen y rótulos del E-FAST (filas 27–38 y E-FAST)

- **Filas 27–36:** EN ACTIVE (panel del examen) · ES POST-DEPLOYMENT REVIEW: el español es un pasaje del relato del caso (`case_text/es/<familia>.json`) y se muestra cuando usted aprueba ese relato en el tablero de la base desplegada (sección 4; §4 del cierre). **Lo que se decide ahora es el inglés.** SHA: EN, S-A; ES, S-E.
  - Actualización del 2026-10-07: ese español se revisa con el relato antes de congelar el candidato final, y su aprobación entra en el candidato en `case_text/es/approvals.json` (4.1); ya no es POST-DEPLOYMENT REVIEW.
- **Filas 37, 38 y E-FAST:** ACTIVE en inglés y en español. SHA: S-A.

| # | Caso · dónde | EN exacto | ES exacto | Se infiere | Recomendación | Nivel | Decisión docente |
|---|---|---|---|---|---|---|---|
| C-27 | 29f · panel del examen, «Respiratory» (TD-50); EN `anaphylaxis_reaction.py:93`; ES `case_text/es/anaphylaxis.json` | Increased effort with widespread expiratory wheeze; no stridor heard now. | Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas; ya no se escucha estridor. | La reacción bajó y ya no hay estridor: el examen sigue la bandera del motor, no la SpO₂. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-28 | 29f intubada · «Respiratory» (TD-47); EN `anaphylaxis_reaction.py:84`; ES `case_text/es/anaphylaxis.json` | Endotracheal tube in place: no stridor through the tube; widespread expiratory wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias espiratorias difusas. | Con el tubo no se ausculta estridor; las sibilancias dicen que la reacción sigue. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-29 | 63m intubado · «Respiratory» (TD-47); EN `anaphylaxis_reaction.py:84`; ES `case_text/es/anaphylaxis.json` | Endotracheal tube in place: no stridor through the tube; widespread wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias difusas. | Igual que la 28. | **APPROVE AS IS** — no se agrupa con la 28: dice «widespread wheeze», sin «expiratory». | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-30 | `anaphylaxis_63m_betablocked` · «General appearance» (TD-59); EN `clinical_cases.py:1511`; ES `case_text/es/anaphylaxis.json` | A sting site on the right forearm. | Sitio de picadura en el antebrazo derecho. | La puerta de entrada: una picadura. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-31 | `renal_colic_34m` y `bradycardia_bb_54f` · «General appearance»; EN `clinical_cases.py:1512`; ES `case_text/es/bradycardia.json` y `case_text/es/renal_colic.json` | No rash. | Sin erupción. | Una negativa que el caso escribe: sin erupción. | **APPROVE AS IS** — UNA DECISIÓN → `renal_colic_34m`, `bradycardia_bb_54f` (el §2 ya la agrupa). Después del despliegue, el español se aprueba caso por caso, con cada relato. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés): una sola decisión para `renal_colic_34m` y `bradycardia_bb_54f` |
| C-32 | `bradycardia_ccb_68m` · «General appearance»; EN `clinical_cases.py:1513`; ES `case_text/es/bradycardia.json` | No rash or swelling. | Sin erupción ni edema. | Una negativa: sin erupción ni edema. | **APPROVE AS IS** — para el relato (sección 4): «swelling» es «edema» aquí y «aumento de volumen» en R-4 (filas 12–14); contextos distintos. | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-33 | `bradycardia_hyperk_63m` · «General appearance»; EN `clinical_cases.py:1515`; ES `case_text/es/bradycardia.json` | A dialysis fistula in the left forearm. | Una fístula de diálisis en el antebrazo izquierdo. | Paciente en diálisis: una pista de la hiperkalemia. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-34 | `trauma_hemothorax_41m` · «General appearance»; EN `clinical_cases.py:1519`; ES `case_text/es/trauma.json` | Seatbelt marking across the chest and abdomen. | Marca del cinturón de seguridad que cruza el tórax y el abdomen. | Huella del cinturón: mecanismo de alta energía. | **APPROVE AS IS** — OPCIONAL (F0-2): el caso está fuera del piloto de residentes. | OPCIONAL (F0-2) | ☐ APPROVE · ☐ REVISE · ☐ DEFER (EN) |
| C-35 | 27m sin nada aplicado · «General appearance» (TD-59); EN `clinical_cases.py:1518`; ES `case_text/es/trauma.json` | A soaked dressing over a deep right thigh wound that is bleeding. | Apósito empapado sobre una herida profunda del muslo derecho que está sangrando. | La herida sangra activamente: hay que controlarla. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-36 | 27m con una medida aplicada · «General appearance»; EN `clinical_cases.py:1517`; ES `case_text/es/trauma.json` | A deep right thigh wound. | Una herida profunda del muslo derecho. | La herida, sin el apósito empapado; el estado del sangrado lo dice la fila 37. | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07; el inglés) |
| C-37 | 27m · «General appearance» tras aplicar una medida (TD-59, TD-31); EN `trauma_hemorrhage.py:119` · ES `language.py:1343` (`_EXAMINATION_SENTENCES_ES`, el panel del examen) | The external bleeding is reduced, not stopped. / The external bleeding is stopped. | El sangrado externo está disminuido, sin detenerse. / El sangrado externo está detenido. | La medida redujo el sangrado sin detenerlo (hay que escalar) / lo detuvo. | **APPROVE AS IS** | TIER 1 | ☒ **APPROVE** (docente, 2026-10-07) |
| C-38 | 29f y 63m · resumen «General appearance»; ES `language.py:1340` (`_SKIN_ES`) | Color: flushed | Color: enrojecimiento | Piel enrojecida (anafilaxia). | **APPROVE AS IS** | TIER 2 | ☒ **APPROVE** (docente, 2026-10-07) |

**C-EFAST · Títulos y rótulos del E-FAST (D-1)** — TIER 2 · ACTIVE
- Dónde: resultado del E-FAST en la sala, el estado del Management Trace y los documentos (un solo formateador, `efast_report.py:145`). ES `language.py:880` y siguientes.
- EN: E-FAST · performed at minute {n}; RIGHT UPPER QUADRANT, LEFT UPPER QUADRANT, SUPRAPUBIC, SUBXIPHOID, LUNG; Morison's pouch (hepatorenal), Right subdiaphragmatic space, Right pleural recess, Splenorenal space, Left subdiaphragmatic space, Left pleural recess, Longitudinal view, Transverse view, Pericardium, Right lung sliding, Left lung sliding, M-mode; Not documented
- ES: E-FAST · realizado en el minuto {n}; CUADRANTE SUPERIOR DERECHO, CUADRANTE SUPERIOR IZQUIERDO, SUPRAPÚBICA, SUBXIFOIDEA, PULMÓN; Espacio de Morison (hepatorrenal), Espacio subdiafragmático derecho, Receso pleural derecho, Espacio esplenorrenal, Espacio subdiafragmático izquierdo, Receso pleural izquierdo, Vista longitudinal, Vista transversal, Pericardio, Deslizamiento pulmonar derecho, Deslizamiento pulmonar izquierdo, Modo M; No documentado
- Se infiere: las cinco ventanas, en doce líneas. «Not documented / No documentado» quiere decir que el caso no documenta esa ventana; no es un hallazgo negativo.
- Recomendación: **APPROVE AS IS** — con el relato sin aprobar, la línea del hallazgo de cada ventana se ve entera en inglés, rótulo incluido (TD-46): nunca una línea en dos idiomas.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

### D. Límites declarados del motor (filas 39–44)

**D-39 · Encabezado y aviso** — TIER 1 · ACTIVE (EN y ES)
- Dónde: la rúbrica y los objetivos (portal docente), sobre los límites de cada caso: EN `encounter_limits.py:23`, ES `report_language.py:1443`.
- EN: What the simulator cannot show or treat in this case · Never count these against the resident: what the simulator cannot show is not evidence, and a measure written for it is not an omission.
- ES: Lo que el simulador no puede mostrar ni tratar en este caso · Nunca las cuente contra el residente: lo que el simulador no puede mostrar no es evidencia, y una medida escrita para ello no es una omisión.
- Se infiere (docente): lo listado nunca se cobra; una medida escrita para ello no es una omisión.
- Recomendación: **APPROVE AS IS** — un texto en dos pantallas, una decisión. Encabeza también las limitaciones que los 31 casos declaraban antes del cierre prepiloto (1.4).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**D-40 · Fila 40 · `pulmonary_embolism_33f`** — TIER 1 · EN ACTIVE · ES DOCUMENTATION ONLY
- Dónde: la rúbrica y los objetivos de cada caso, bajo D-39; `case_assessment_bank.py:1787`.
- EN: After a thrombolytic the bleeding from the operated site does not stop in this simulator: the haemoglobin keeps falling while the pressure can stay reassuring. The room cannot stop an alteplase infusion; tranexamic acid and cryoprecipitate are recorded without a modelled effect, and fibrinogen concentrate is not recognised. The response to that bleeding is not evaluated and is never used to judge haemorrhage rescue: not reversing it is never charged, and a measure written for it is never an omission. The decision to give the thrombolytic is judged as before, on the minute it was given.
- ES (§2): (en inglés, como toda declaración del banco; la guía docente lo dice en español) El equivalente está en `docs/GUIA_DOCENTE_PILOTO.md`, líneas 118–123.
- Se infiere (docente): la respuesta al sangrado tras la lisis no se evalúa ni juzga el rescate hemorrágico; la decisión de trombolizar sí, en su minuto.
- Recomendación: **APPROVE AS IS** — D-3 (TD-55). VINCULADA con B-26.
- SHA: S-A (el inglés); S-C (la guía). — Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**D-41 · Fila 41 · `acs_70f_left_main`** — TIER 1 · EN ACTIVE · ES DOCUMENTATION ONLY
- Dónde: la rúbrica y los objetivos de cada caso, bajo D-39; `case_assessment_bank.py:1794`.
- EN: A volume past this ventricle's tolerance shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the saturation and a repeat POCUS do not change. Detecting overload on the examination or POCUS is not required; when the only response the resident looked for is one the simulator does not show, that part is not evaluable rather than missing.
- ES (§2): (ídem) El equivalente está en `docs/GUIA_DOCENTE_PILOTO.md`, líneas 112–116.
- Se infiere (docente): el exceso de volumen sólo se ve en la presión y en un mensaje; no se exige detectarlo por examen ni POCUS; lo no visible es no evaluable.
- Recomendación: **APPROVE AS IS** — D-8 (TD-53). VINCULADA con E-46: el mismo criterio con otra redacción; decidirlas juntas.
- SHA: S-A (el inglés); S-C (la guía). — Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**D-42 · Fila 42 · `pneumonia_46f` y `pneumonia_83m`** — TIER 1 · EN ACTIVE · ES DOCUMENTATION ONLY
- Dónde: la rúbrica y los objetivos de cada caso, bajo D-39; `case_assessment_bank.py:1799, 1802`.
- EN: A repeat POCUS shows the IVC filling with volume, but its lungs show no new B-lines with crystalloid overload; the saturation does fall. Seeing new B-lines is not required.
- ES (§2): (ídem) El equivalente está en `docs/GUIA_DOCENTE_PILOTO.md`, líneas 156–159.
- Se infiere (docente): un POCUS de control no muestra líneas B nuevas con cristaloides (la saturación sí cae); no se exige verlas.
- Recomendación: **APPROVE AS IS** — TD-54. UNA DECISIÓN → `pneumonia_46f`, `pneumonia_83m` (el §2 ya la agrupa). Ver F-53 y F-54.
- SHA: S-A (el inglés); S-C (la guía). — Decisión docente: ☐ APPROVE · ☒ **REVISE** · ☐ DEFER — docente, 2026-10-07: se mantienen el sentido del inglés y el comportamiento del motor; el español de D-42 no es el párrafo de la guía que junta el trauma y la neumonía, sino uno propio (abajo). Sin implementar
- **ES aprobado para D-42** (docente, 2026-10-07; sin implementar; una decisión para `pneumonia_46f` y `pneumonia_83m`): «Un POCUS de control muestra que la VCI se llena con el volumen, pero en los pulmones no muestra líneas B nuevas por la sobrecarga de cristaloides; la saturación sí cae. No se exige ver líneas B nuevas.» Al implementarse, reemplaza la parte de la neumonía del párrafo de TD-54 de la guía docente (líneas 156–159), que hoy no dice que la VCI se llena; la frase del trauma queda igual (S-C, sólo documentación).

**D-43 · Fila 43 · `trauma_limb_hemorrhage_27m`** — TIER 1 · EN ACTIVE · ES DOCUMENTATION ONLY
- Dónde: la rúbrica y los objetivos de cada caso, bajo D-39; `case_assessment_bank.py:1805`.
- EN: A repeat POCUS shows the arrival IVC whatever the volume or the haemorrhage control, and a repeat E-FAST repeats the arrival windows: a change the simulator does not show is not required.
- ES (§2): (ídem) El equivalente está en `docs/GUIA_DOCENTE_PILOTO.md`, líneas 156–159.
- Se infiere (docente): la VCI y el E-FAST de control repiten la llegada; no se exige ver un cambio.
- Recomendación: **APPROVE AS IS** — TD-54.
- SHA: S-A (el inglés); S-C (la guía). — Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**D-44 · Fila 44 · `trauma_hemothorax_41m`** — OPCIONAL (F0-2) · EN ACTIVE · ES DOCUMENTATION ONLY
- Dónde: la rúbrica y los objetivos de cada caso, bajo D-39; `case_assessment_bank.py:1808`.
- EN: A repeat POCUS shows the arrival IVC whatever the volume, and a repeat E-FAST repeats the arrival windows, the drained pleural recess included: what it adds is the other cavities still clear.
- ES (§2): (ídem) El equivalente está en `docs/GUIA_DOCENTE_PILOTO.md`, líneas 156–159.
- Se infiere (docente): el control repite la llegada, incluido el receso drenado; lo que agrega es que las otras cavidades siguen limpias.
- Recomendación: **APPROVE AS IS** — TD-54. OPCIONAL (F0-2): el caso está fuera del piloto de residentes.
- SHA: S-A (el inglés); S-C (la guía). — Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### E. Declaraciones C14 cambiadas (filas 45–46)

- **Estado:** EN ACTIVE (la declaración C14 del caso en el banco; se congela con cada encuentro nuevo) · ES DRAFT inactivo (TD-07: el portal docente muestra C14 en inglés también en español).
- **SHA:** EN, S-A; ES, S-B. **Nivel:** TIER 1 (criterio de evaluación).

**E-45 · Fila 45 · `acs_52m_de_winter`** — TIER 1
- Dónde: `case_assessment_bank.py:1607`; borrador `spanish_drafts.py:274`.
- §2: Component: «Using the reported regional wall motion to prioritise the reperfusion decision.» Evidence: «requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion; activates or expedites reperfusion». Rationale adds: «The report states the wall motion; recognising it is not required. POCUS never delays reperfusion: activating it from the ECG alone is correct and is not a C14 deficit.»
- EN · componente: Using the reported regional wall motion to prioritise the reperfusion decision.
- EN · evidencia: requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion
- EN · evidencia: activates or expedites reperfusion
- EN · fundamento completo: Akinesis of the anterior wall and apex supports treating the de Winter pattern as an anterior occlusion (decision A); in the engine the wall motion evolves with the ischaemic minutes. The report states the wall motion; recognising it is not required. POCUS never delays reperfusion: activating it from the ECG alone is correct and is not a C14 deficit.
- ES · componente: Usar la motilidad regional informada para priorizar la decisión de reperfusión.
- ES · evidencia: solicita POCUS y relaciona la acinesia anterior informada con el patrón del ECG como una oclusión
- ES · evidencia: activa o acelera la reperfusión
- ES · fundamento: La acinesia de la pared anterior y del ápex apoya tratar el patrón de de Winter como una oclusión anterior (decisión A); en el motor, la motilidad evoluciona con los minutos de isquemia. El informe entrega la motilidad; no se exige reconocerla. El POCUS nunca demora la reperfusión: activarla sólo por el ECG es correcto y no es un déficit de C14.
- Se infiere (docente): no se exige reconocer la motilidad; activar la reperfusión sólo por el ECG es correcto y no es un déficit de C14.
- Recomendación: **APPROVE AS IS** — D-7. VINCULADA con F-47 (mismo componente y evidencia; la ficha decide además la interpretación y el manejo).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**E-46 · Fila 46 · `acs_70f_left_main`** — TIER 1
- Dónde: `case_assessment_bank.py:1570`; borrador `spanish_drafts.py:298`.
- §2: Rationale adds: «In this simulator a volume past the ventricle's tolerance shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the saturation and a repeat POCUS do not change. The adaptation is judged on those signals: detecting overload on the examination or POCUS is not required, and when the only response the resident looked for is one the simulator does not show, that part of the observation is not evaluable rather than missing.»
- EN · fundamento completo: Borderline pressure with incipient hypoperfusion (104/66, cool extremities, capillary refill 3 s) and intermediate POCUS findings: globally mildly reduced contraction, scattered basal B-lines and an IVC of 1.9 cm with about 50% collapse. No single answer follows from them: withholding volume, a small bolus with its limit stated and reassessed, or early support can each be justified, and the engine answers large volumes poorly in this profile. C14 observes whether the volume, support and urgency decisions are made with the global LV function in view and adapted to the response. In this simulator a volume past the ventricle's tolerance shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the saturation and a repeat POCUS do not change. The adaptation is judged on those signals: detecting overload on the examination or POCUS is not required, and when the only response the resident looked for is one the simulator does not show, that part of the observation is not evaluable rather than missing.
- ES · fundamento: Presión limítrofe con hipoperfusión incipiente (104/66, extremidades frías, llene capilar de 3 s) y hallazgos intermedios en el POCUS: contracción global levemente disminuida, líneas B basales dispersas y una VCI de 1,9 cm con cerca de 50 % de colapso. De ellos no se deduce una única respuesta: no dar volumen, un bolo pequeño con su límite declarado y reevaluado, o un soporte precoz pueden justificarse, y en este perfil el motor responde mal a volúmenes grandes. C14 observa si las decisiones de volumen, soporte y urgencia se toman con la función global del VI a la vista y se adaptan a la respuesta. En este simulador, un volumen que supera la tolerancia del ventrículo se ve sólo en una presión que deja de responder y en un mensaje de la sala; el pulmón, el examen, la saturación y un POCUS de control no cambian. La adaptación se juzga con esas señales: no se exige detectar sobrecarga por examen ni por POCUS, y cuando la única respuesta que buscó el residente es una que el simulador no muestra, esa parte de la observación no es evaluable, en vez de faltar.
- Se infiere (docente): la adaptación se juzga con la presión que deja de responder y el mensaje de la sala; no se exige ver la sobrecarga; lo no visible es no evaluable, no ausente.
- Recomendación: **APPROVE AS IS** — D-8. VINCULADA con D-41: el mismo criterio con otra redacción; decidirlas juntas.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

### F. R-2 · Las 14 fichas POCUS C14 YES (filas 47–60)

- **Estado:** DOCUMENTATION ONLY (la ficha, generada por `tools_review_sheets.py` desde el banco y `pocus_review_notes.py`) sobre textos ACTIVE (el POCUS de llegada del caso, en la sala; la declaración C14, en el portal docente). El español de C14 es DRAFT inactivo (TD-07); el del informe POCUS va con el relato (sección 4).
- **Ficha completa:** `docs/revision/R2_POCUS_C14.md` (estado clínico, hallazgo, qué interpretar, cómo guía el manejo, ACEP, posible problema, criterio aprobado). Abajo, lo que se califica: el componente y la evidencia C14, exactos, del banco.
- **SHA:** S-D. **Nivel:** TIER 1 (criterio de evaluación). Firmar las fichas no cambia `POCUS_DRAFT_PENDING_FACULTY_REVIEW = True` (`clinical_cases.py:64`): marca el POCUS de los 31 casos y el runtime no lo lee.
- Los criterios de la tabla R-2 quedaron aceptados el 2026-10-02 (D-7); falta la firma de cada ficha.

**F-47 · Fila 47 · `acs_52m_de_winter`** — TIER 1 · ficha «CONFIRM» · Cardíaca focalizada: motilidad regional del VI, como apoyo del ECG
- EN · componente: Using the reported regional wall motion to prioritise the reperfusion decision.
- EN · evidencia: requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion
- EN · evidencia: activates or expedites reperfusion
- ES · componente (borrador): Usar la motilidad regional informada para priorizar la decisión de reperfusión.
- ES · evidencia (borrador): solicita POCUS y relaciona la acinesia anterior informada con el patrón del ECG como una oclusión
- ES · evidencia (borrador): activa o acelera la reperfusión
- Se infiere (docente): basta usar con el ECG la motilidad que entrega el informe; no se exige reconocerla, y activar la reperfusión sólo por el ECG no es un déficit.
- Recomendación: **APPROVE AS IS** — redacción D-7 aplicada. VINCULADA con E-45 (mismo componente y evidencia).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-48 · Fila 48 · `acs_61m_posterior`** — TIER 1 · ficha «CONFIRM» · Cardíaca focalizada (motilidad regional) y aorta torácica en un dolor torácico con irradiación al dorso
- EN · componente: Using the reported regional wall motion, with the ECG and the posterior leads, to prioritise the reperfusion decision.
- EN · evidencia: requests POCUS and relates the reported wall motion to the ECG
- EN · evidencia: uses it with the ECG and the posterior leads to treat the pattern as an occlusion
- EN · evidencia: activates or expedites reperfusion
- ES · componente (borrador): Usar la motilidad regional informada, junto con el ECG y las derivaciones posteriores, para priorizar la decisión de reperfusión.
- ES · evidencia (borrador): solicita POCUS y relaciona la motilidad informada con el ECG
- ES · evidencia (borrador): la usa junto con el ECG y las derivaciones posteriores para tratar el patrón como una oclusión
- ES · evidencia (borrador): activa o acelera la reperfusión
- Se infiere (docente): se observa usar la motilidad informada con el ECG y las derivaciones posteriores; no se exige reconocer la hipocinesia sutil.
- Recomendación: **APPROVE AS IS** — no se exige reconocer la hipocinesia posterior sutil que entrega el informe; una aorta no dilatada no descarta una disección.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-49 · Fila 49 · `acs_70f_left_main`** — TIER 1 · ficha «CONFIRM» · Cardíaca (función global del VI), pulmonar (líneas B) y VCI en un SCA con hipoperfusión incipiente
- EN · componente: Deciding volume, support and urgency with the global LV function in view, and adapting them to the response.
- EN · evidencia: requests POCUS and relates the global LV function, the B-lines and the IVC to the volume decision
- EN · evidencia: withholds volume, or gives a small bolus with its limit stated and reassesses it, or escalates support, and says why
- EN · evidencia: adapts the plan to the response and relates it to the urgency of reperfusion
- ES · componente (borrador): Decidir el volumen, el soporte y la urgencia con la función global del VI a la vista, y adaptarlos a la respuesta.
- ES · evidencia (borrador): solicita POCUS y relaciona la función global del VI, las líneas B y la VCI con la decisión de volumen
- ES · evidencia (borrador): no da volumen, o da un bolo pequeño con su límite declarado y lo reevalúa, o escala el soporte, y dice por qué
- ES · evidencia (borrador): adapta el plan a la respuesta y lo relaciona con la urgencia de la reperfusión
- Se infiere (docente): se observa decidir volumen, soporte y urgencia con la función del VI a la vista y adaptarlos a la respuesta; la sobrecarga no se ve y no se exige.
- Recomendación: **REVIEW CLOSELY** — D-8: el exceso de volumen no cambia pulmón, examen, saturación ni POCUS (TD-53). La evidencia pide relacionar el VI, las líneas B y la VCI de llegada con la decisión y adaptar el plan a la respuesta: confirmar que la ficha no exige ver la sobrecarga.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: el límite aprobado en D-41 y E-46 es vinculante. No se exige detectar la sobrecarga por examen ni por POCUS cuando el motor no la modela; la adaptación se juzga con las señales que el simulador sí entrega.

**F-50 · Fila 50 · `gi_bleed_57m`** — TIER 1 · ficha «CONFIRM» · Hipotensión indiferenciada: corazón y VCI (volumen)
- EN · componente: Using the POCUS volume assessment to guide and reassess resuscitation.
- EN · evidencia: requests POCUS and names the empty, hyperdynamic LV and the collapsed IVC
- EN · evidencia: relates them to transfusion or volume
- EN · evidencia: reassesses with POCUS after resuscitation
- ES · componente (borrador): Usar la evaluación del volumen por POCUS para guiar y reevaluar la reanimación.
- ES · evidencia (borrador): solicita POCUS y nombra el VI vacío e hiperdinámico y la VCI colapsada
- ES · evidencia (borrador): los relaciona con la transfusión o el volumen
- ES · evidencia (borrador): reevalúa con POCUS después de la reanimación
- Se infiere (docente): se observa nombrar el VI vacío e hiperdinámico y la VCI colapsada, relacionarlos con la transfusión o el volumen y reevaluar con POCUS.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-51 · Fila 51 · `gi_bleed_72f`** — TIER 1 · ficha «CONFIRM» · Hipotensión por sangrado: corazón y VCI (volumen)
- EN · componente: Using the POCUS volume assessment to guide and reassess resuscitation.
- EN · evidencia: requests POCUS and names the hyperdynamic LV and the collapsing IVC
- EN · evidencia: relates them to transfusion or volume
- EN · evidencia: reassesses with POCUS after resuscitation
- ES · componente (borrador): Usar la evaluación del volumen por POCUS para guiar y reevaluar la reanimación.
- ES · evidencia (borrador): solicita POCUS y nombra el VI hiperdinámico y la VCI que colapsa
- ES · evidencia (borrador): los relaciona con la transfusión o el volumen
- ES · evidencia (borrador): reevalúa con POCUS después de la reanimación
- Se infiere (docente): lo mismo que en la 57m, con la VCI que colapsa.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-52 · Fila 52 · `obstructive_pyelonephritis_58f`** — TIER 1 · ficha «CONFIRM» · Shock séptico: corazón y VCI para la estrategia de fluidos
- EN · componente: Guiding the fluid and haemodynamic strategy with POCUS in septic shock.
- EN · evidencia: requests POCUS and names the volume findings (the IVC and the LV)
- EN · evidencia: gives, limits or titrates volume, or moves to a vasopressor, because of them
- ES · componente (borrador): Guiar con POCUS la estrategia de fluidos y hemodinámica en el shock séptico.
- ES · evidencia (borrador): solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI)
- ES · evidencia (borrador): da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos
- Se infiere (docente): se observa nombrar la VCI y el VI y decidir por ellos el volumen o el vasopresor; la VCI de control no cambia.
- Recomendación: **APPROVE AS IS** — la VCI de control no cambia (TD-54) y su C14 ya lo declara; la evidencia no exige reevaluar con POCUS.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-53 · Fila 53 · `pneumonia_46f`** — TIER 1 · ficha «CONFIRM» · Shock séptico con hipoxemia: corazón y VCI, más pulmón (consolidación y líneas B)
- EN · componente: Guiding and reassessing the fluid and haemodynamic strategy with POCUS.
- EN · evidencia: requests POCUS and names the volume findings (the IVC and the LV)
- EN · evidencia: gives, limits or titrates volume, or moves to a vasopressor, because of them
- EN · evidencia: reassesses with POCUS after volume
- ES · componente (borrador): Guiar y reevaluar con POCUS la estrategia de fluidos y hemodinámica.
- ES · evidencia (borrador): solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI)
- ES · evidencia (borrador): da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos
- ES · evidencia (borrador): reevalúa con POCUS después del volumen
- Se infiere (docente): se observa decidir el volumen o el vasopresor por la VCI y el VI, y reevaluar con POCUS; en el control, la VCI se llena pero no aparecen líneas B nuevas.
- Recomendación: **REVIEW CLOSELY** — una evidencia pide reevaluar con POCUS tras el volumen; el control muestra la VCI que se llena, pero ninguna línea B nueva (TD-54, fila 42): confirmar que se juzga con la VCI y la saturación, nunca con las líneas B. VINCULADA con F-54: el mismo texto C14.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07, vinculada expresamente a D-42: la respuesta al volumen se juzga con la VCI y la saturación; nunca se exigen líneas B nuevas, porque el simulador no las modela.

**F-54 · Fila 54 · `pneumonia_83m`** — TIER 1 · ficha «CONFIRM» · Hipotensión en un anciano derivado como «deshidratado»: corazón y VCI, más pulmón
- EN · componente: Guiding and reassessing the fluid and haemodynamic strategy with POCUS.
- EN · evidencia: requests POCUS and names the volume findings (the IVC and the LV)
- EN · evidencia: gives, limits or titrates volume, or moves to a vasopressor, because of them
- EN · evidencia: reassesses with POCUS after volume
- ES · componente (borrador): Guiar y reevaluar con POCUS la estrategia de fluidos y hemodinámica.
- ES · evidencia (borrador): solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI)
- ES · evidencia (borrador): da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos
- ES · evidencia (borrador): reevalúa con POCUS después del volumen
- Se infiere (docente): lo mismo que en la 46f.
- Recomendación: **REVIEW CLOSELY** — igual que la 46f; sin «dynamic» (D-7). VINCULADA con F-53: el mismo texto C14.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: el mismo límite de F-53 y D-42.

**F-55 · Fila 55 · `pulmonary_edema_58m`** — TIER 1 · ficha «CONFIRM» · Disnea aguda: pulmón (líneas B), corazón y VCI
- EN · componente: Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC.
- EN · evidencia: requests POCUS and names the diffuse B-lines and the depressed LV
- EN · evidencia: withholds volume because of them
- EN · evidencia: gives nitrate, diuretic or NIV because of them
- ES · componente (borrador): Decidir nitrato, diurético o VMNI, y no dar volumen, a partir de las líneas B, el VI y la VCI.
- ES · evidencia (borrador): solicita POCUS y nombra las líneas B difusas y el VI deprimido
- ES · evidencia (borrador): no da volumen por esos hallazgos
- ES · evidencia (borrador): da nitrato, diurético o VMNI por esos hallazgos
- Se infiere (docente): se observa nombrar las líneas B difusas y el VI deprimido, no dar volumen y dar nitrato, diurético o VMNI por ellos.
- Recomendación: **APPROVE AS IS** — VINCULADA con F-56: el mismo texto C14; cada ficha revisa su propio POCUS de llegada.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-56 · Fila 56 · `pulmonary_edema_75f`** — TIER 1 · ficha «CONFIRM» · Disnea aguda en IC con FE reducida: pulmón, corazón y VCI
- EN · componente: Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC.
- EN · evidencia: requests POCUS and names the diffuse B-lines and the depressed LV
- EN · evidencia: withholds volume because of them
- EN · evidencia: gives nitrate, diuretic or NIV because of them
- ES · componente (borrador): Decidir nitrato, diurético o VMNI, y no dar volumen, a partir de las líneas B, el VI y la VCI.
- ES · evidencia (borrador): solicita POCUS y nombra las líneas B difusas y el VI deprimido
- ES · evidencia (borrador): no da volumen por esos hallazgos
- ES · evidencia (borrador): da nitrato, diurético o VMNI por esos hallazgos
- Se infiere (docente): lo mismo que en la 58m.
- Recomendación: **APPROVE AS IS** — llega con la vista neutral (P-07); la ficha no depende de la foto. VINCULADA con F-55: el mismo texto C14.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-57 · Fila 57 · `pulmonary_embolism_33f`** — TIER 1 · ficha «CONFIRM» · Disnea súbita posoperatoria: TVP por compresión, VD y VCI
- EN · componente: Integrating the RV and a proximal DVT with the haemodynamic stability: anticoagulation before confirmation, and no thrombolysis.
- EN · evidencia: requests POCUS and names the proximal DVT or the RV
- EN · evidencia: anticoagulates, or states it as pending the angiogram, because of it
- EN · evidencia: withholds thrombolysis with the stable haemodynamics and the RV stated
- ES · componente (borrador): Integrar el VD y una TVP proximal con la estabilidad hemodinámica: anticoagulación antes de la confirmación, y sin trombólisis.
- ES · evidencia (borrador): solicita POCUS y nombra la TVP proximal o el VD
- ES · evidencia (borrador): anticoagula, o la plantea como pendiente de la angio-TC, por ese hallazgo
- ES · evidencia (borrador): no da trombólisis, y explicita la estabilidad hemodinámica y el VD
- Se infiere (docente): se observa integrar la TVP o el VD con la estabilidad: anticoagular antes de confirmar y no trombolizar.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-58 · Fila 58 · `pulmonary_embolism_61m`** — TIER 1 · ficha «CONFIRM» · Shock indiferenciado: VD (RUSH), VCI y TVP
- EN · componente: Deciding reperfusion and anticoagulation from RV strain and a proximal DVT in shock.
- EN · evidencia: requests POCUS and names the dilated RV with a D-sign or McConnell's sign, or the DVT
- EN · evidencia: anticoagulates and decides reperfusion because of it
- EN · evidencia: acts without waiting for the angiogram
- ES · componente (borrador): Decidir la reperfusión y la anticoagulación a partir de la sobrecarga del VD y una TVP proximal en shock.
- ES · evidencia (borrador): solicita POCUS y nombra el VD dilatado con signo D o signo de McConnell, o la TVP
- ES · evidencia (borrador): anticoagula y decide la reperfusión por ese hallazgo
- ES · evidencia (borrador): actúa sin esperar la angio-TC
- Se infiere (docente): se observa decidir la reperfusión y la anticoagulación por el VD o la TVP en shock, sin esperar la angiografía.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**F-59 · Fila 59 · `trauma_hemothorax_41m`** — OPCIONAL (F0-2) · ficha «CONFIRM» · E-FAST en trauma cerrado con hipotensión
- EN · componente: Deciding the drain and its reassessment from the haemothorax on the E-FAST.
- EN · evidencia: requests the E-FAST and names the left haemothorax
- EN · evidencia: places a chest tube because of it
- EN · evidencia: reassesses after the drain with the E-FAST, a film or surgery
- ES · componente (borrador): Decidir el drenaje y su reevaluación a partir del hemotórax en el E-FAST.
- ES · evidencia (borrador): solicita el E-FAST y nombra el hemotórax izquierdo
- ES · evidencia (borrador): instala un tubo pleural por ese hallazgo
- ES · evidencia (borrador): reevalúa después del drenaje con el E-FAST, una radiografía o cirugía
- Se infiere (docente): se observa decidir el drenaje por el hemotórax del E-FAST y reevaluar después.
- Recomendación: **APPROVE AS IS** — OPCIONAL (F0-2): el caso está fuera del piloto de residentes.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**F-60 · Fila 60 · `trauma_limb_hemorrhage_27m`** — TIER 1 · ficha «CONFIRM» · E-FAST en trauma de extremidad con shock
- EN · componente: Directing haemorrhage control with the absence of cavity bleeding on the E-FAST.
- EN · evidencia: requests the E-FAST and names it negative
- EN · evidencia: keeps haemorrhage control on the limb rather than searching a cavity
- EN · evidencia: states what would change that
- ES · componente (borrador): Dirigir el control de la hemorragia con la ausencia de sangrado cavitario en el E-FAST.
- ES · evidencia (borrador): solicita el E-FAST y lo nombra negativo
- ES · evidencia (borrador): mantiene el control de la hemorragia en la extremidad en vez de buscar en una cavidad
- ES · evidencia (borrador): dice qué cambiaría eso
- Se infiere (docente): se observa nombrar el E-FAST negativo y mantener el control de la hemorragia en el miembro.
- Recomendación: **APPROVE AS IS** — tras TD-48 la E-FAST muestra sus doce ventanas negativas; el control repite la llegada (TD-54, fila 43) y la evidencia no exige ver un cambio.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

### G. R-3 · Tabla TDFC final (fila 61)

**G-61 · `docs/tdfc/TDFC_TABLA_FINAL.md`** — TIER 1 · DOCUMENTATION ONLY (generada por `tdfc_review.final_table_markdown()`; las declaraciones que lista son ACTIVE: se congelan con cada encuentro nuevo)
- §2: `docs/tdfc/TDFC_TABLA_FINAL.md`: T-2 C1 YES; T-3 y T-4 NO; sin frase opcional
- Texto que se firma: la tabla de TD1, F1, C1 y C3 de los 31 casos declarados (filas en inglés, del banco) y sus decisiones: T-2, C1 YES en opioides y bradicardias tóxicas; T-3, `hypoglycemia_76f` C1 NO; T-4, `acs_52m_de_winter` F1 y C3 NO; sin la frase aclaratoria opcional de T-2; `anaphylaxis_29f` C3 YES como oportunidad parcial (R-3). Totales: TD1 26 YES / 5 NO · F1 26 / 5 · C1 19 / 12 · C3 10 / 21.
- ES: la prosa del documento está en español; las filas, en inglés.
- Se infiere (docente): qué oportunidades declara cada caso. YES observa un componente, nunca la EPA completa; NO no quiere decir falla.
- Recomendación: **APPROVE AS IS** — criterios aceptados en D-10; la tabla coincide con el banco (`test_tdfc_opportunities.py`). Los totales cuentan los 31 casos; las cuatro filas de la 41m no se ejercen en el piloto de residentes (F0-2).
- SHA: S-D. — Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

### H. Guía docente (fila 62)

**H-62 · `docs/GUIA_DOCENTE_PILOTO.md`** — TIER 1 · DOCUMENTATION ONLY · **NEEDS UPDATE BEFORE SIGN-OFF**

- **Estado:** «lista para firma, no aprobada» desde el 2026-10-02; anterior a la Fase 0. Este paquete no la edita.
- **Idioma:** la guía sólo existe en español; las etiquetas de la pantalla llevan el inglés entre paréntesis.
- **SHA:** S-C. Ninguna corrección toca el código.
- **Cómo se decide:** marque cada corrección (✓ acepto · ✎ cambio · ✗ no). Con las aceptadas, la guía se actualiza en un commit sólo de documentación y vuelve a usted para la firma: la guía es una decisión.
- **Se infiere:** hoy, quien evalúa lee una sala anterior a la Fase 0: espera 31 casos, cree que un fármaco sin verbo puede perderse sin aviso (hoy tiene recibo) y no encuentra las reglas con que se lee el registro (tiempo, interrupciones, paro, guardas A–E). Puede tomar por omisión del residente lo que es un límite del simulador.
- **Texto actual:** exacto, con los saltos de línea del archivo unidos.

| # | Líneas | Tipo | Texto actual | Redacción corregida propuesta | Por qué | Nivel | ✓ · ✎ · ✗ |
|---|---|---|---|---|---|---|---|
| H-1 | 6–8 | No coincide (fecha y alcance) | **Estado (cierre prepiloto, 2026-10-02): lista para su firma, no aprobada.** Describe el funcionamiento comprobado al cierre del paquete prepiloto (D-1 a D-11), con las etiquetas de la pantalla en español y, entre paréntesis, en inglés. | **Estado (Fase 0 cerrada el 2026-10-06): lista para su firma, no aprobada.** Describe el funcionamiento comprobado al cierre del paquete prepiloto (D-1 a D-11) y lo que cambió la Fase 0 (F0-1 a F0-12), con las etiquetas de la pantalla en español y, entre paréntesis, en inglés. | La guía describe la sala anterior a la Fase 0; quien firma debe saber qué sala describe. | TIER 3 | ☐ · ☐ · ☐ |
| H-2 | 20–21 | No coincide (F0-2, F0-4) | **Casos:** los 31 del banco, asignados por desafío y año de formación. Las composiciones de hipoglicemia, los casos escritos por IA y PS001/PS002 no se usan. | **Casos:** 30 de los 31 del banco, asignados por desafío y año de formación. `trauma_hemothorax_41m` queda fuera del piloto de residentes (F0-2): el pabellón no está modelado y, tras el drenaje, el paciente hace un paro hacia el minuto 60 haga lo que haga; sigue en el sandbox docente y no se ofrece al dirigir un caso. Las composiciones de hipoglicemia, los casos escritos por IA y PS001/PS002 no se usan, y R1-03, R1-04 y R2-01 no se asignan (F0-4). | Decisiones F0-2 y F0-4 (Decision File); el informe de preparación lo registró (10.2-b). | TIER 3 | ☐ · ☐ · ☐ |
| H-3 | 86–88 | No coincide (alcance, F0-2) | En la 41m se ve el líquido en el receso pleural izquierdo. | En la 41m (sólo en el sandbox docente, F0-2) se ve el líquido en el receso pleural izquierdo. | El caso ya no está en el piloto de residentes. | TIER 3 | ☐ · ☐ · ☐ |
| H-4 | 120–121 | Incompleta (dónde firmar) | Las 18 frases finales del motor esperan su firma (`docs/revision/CIERRE_PREPILOTO.md`). | Las 18 frases finales del motor esperan su firma (`docs/revision/CIERRE_PREPILOTO.md`, ordenadas en `docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`). | Este paquete reúne todas las firmas de B-5. | TIER 3 | ☐ · ☐ · ☐ |
| H-5 | 128–130 | No coincide desde la Fase 0 | **No cambió nada de lo que se registra:** las mismas entradas producen la misma interpretación, ejecución, tiempo, estado y registro (comprobado antes/después). | **El cambio de pantalla no cambió nada de lo que se registra:** las mismas entradas producían la misma interpretación, ejecución, tiempo, estado y registro (comprobado antes/después, 2026-10-02). La Fase 0, después, sí cambió la ejecución y el tiempo: ver «La sala desde la Fase 0». | Leída hoy, dice que la sala interpreta y mide el tiempo como antes; la Fase 0 cambió ambos. | TIER 3 | ☐ · ☐ · ☐ |
| H-6 | 137–140 | Condicional (J y X-1) | esa nota todavía se ve en inglés | Si se activa el español (X-1): «en un encuentro en español, esa nota se ve en español». Si no: sin cambio. | Depende de J y X-1. | TIER 3 | ☐ · ☐ · ☐ |
| H-7 | 145–148 | No coincide (alcance, F0-2) | un E-FAST de control repite las ventanas de llegada, también el receso drenado de la 41m. | un E-FAST de control repite las ventanas de llegada (en la 41m, sólo en el sandbox docente, también el receso drenado). | El caso ya no está en el piloto de residentes. | TIER 3 | ☐ · ☐ · ☐ |
| H-8 | 155–156 | No coincide (Fase 0, TD-69) | Un fármaco o un examen nombrado en una lista sin verbo, que el lector no conoce, puede perderse sin aviso. | Desde la Fase 0, toda orden termina con un destino y un recibo. Un fármaco o un examen nombrado sin verbo ni dosis («- Aspirin» en una lista, «Cefepime now»), o que ningún vocabulario conoce («Zyvox IV»), queda como orden no entendida (UNRECOGNIZED) y la sala lo dice: «No se entendió: «…». No se administró ni se hizo nada por ello.» Quedan formas sin recibo (TD-69). Guardadas en silencio, sin que la regla A lea una omisión: un nombre tras «with/con» que sigue a un nombre conocido («Give ceftriaxone with zyvox»); un nombre escrito solo, como verbo o participio («Suctioning.», «Lavado.»); una etiqueta con dos puntos («Sepsis: zyvox.»), una condición sin verbo («If hypotensive, zyvox.»), un número sin unidad («Zyvox 600») o un nombre unido a la nota con «y». Sin guarda propia: una orden de una sola palabra del vocabulario de notas («Vitals.», «Airway.»), un nombre justo después de otro conocido sin «with/con» («Give ceftriaxone zyvox») o uno que una acción absorbe («Reassess BP and zyvox in 10 minutes»). El registro guarda el texto entero del turno: léalo. | Fase 0 (informe, §4) y TD-69; el informe de preparación lo registró (10.2-c). Lo que parece una omisión puede ser del lector. | TIER 1 | ☐ · ☐ · ☐ |
| H-9 | — | Falta (Fase 0) | — | Sección nueva «La sala desde la Fase 0 (2026-10-06)», antes de «Limitaciones conocidas» (línea 150). Texto propuesto: H.2, abajo. | Ninguna guía describe lo que la Fase 0 cambió (10.2-c), y usted evalúa con esas reglas. | TIER 1 | ☐ · ☐ · ☐ |
| H-10 | 168–169 | Incompleta (F0-11 y R-4) | **Relato en español:** sólo se muestra el de los casos cuya traducción usted aprobó en el tablero docente. El resto se ve en inglés, línea por línea entera, también en el POCUS y el E-FAST. | **Relato en español:** sólo se muestra el de los casos cuya traducción usted aprobó en el tablero docente. El resto se ve en inglés, línea por línea entera, también en el POCUS y el E-FAST. Las frases nuevas de la Fase 0 se dicen siempre en español en un encuentro en español (F0-11). Mientras no se activen (X-1), las frases del motor de R-4 (la auscultación y las vías venosas, entre otras) y el aviso de la foto se ven en inglés. | F0-11 y lo verificado en el código (1.4); la última frase depende de X-1. | TIER 3 | ☐ · ☐ · ☐ |
| H-11 | 175–176 | Incompleta (dónde firmar) | Lo pendiente de su firma está en `docs/revision/CIERRE_PREPILOTO.md`. | Lo pendiente de su firma está en `docs/revision/CIERRE_PREPILOTO.md` y `docs/revision/F0_11_FRASES_ES.md`, ordenado en `docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`. | F0-11 agregó una hoja de firma. | TIER 3 | ☐ · ☐ · ☐ |

**H.2 · Redacción propuesta para la sección nueva (H-9).** Sólo hechos del informe de la Fase 0 (§4, §6, §7, §9, §11, §12, §15, §21) y del Decision File (F0-1 a F0-12):

> ## La sala desde la Fase 0 (2026-10-06)
>
> Lo que cambió la Fase 0 y cómo leerlo al evaluar. Vale para encuentros nuevos.
>
> - **Cada orden tiene un destino y un recibo.** El registro y el Management Trace guardan qué pasó con cada orden escrita (por ejemplo EXECUTED, HELD_CLARIFICATION, HELD_REASONING, RECORDED_NOT_MODELLED, UNRECOGNIZED o TERMINAL_NOT_EXECUTABLE), con el minuto en que se escribió, y la sala se lo dijo al residente. En un envío con varias órdenes, las independientes corren y el recibo dice qué corrió y qué no.
> - **Tiempo (F0-5).** «Esperar u observar N minutos» (también en español) avanza el reloj N minutos. «Reevaluar» sin número es una mirada a la cabecera de 2 minutos; «dar X y reevaluar» es X más esa mirada, y la sala dice si X tuvo tiempo de actuar. Una orden para más tarde («en 30 minutos») no se ejecuta ni se programa: queda registrada y la sala lo dice. Un volumen «en 20 minutos» es un ritmo. Un paso del reloj llega a 120 minutos como máximo.
> - **Interrupciones (F0-6).** Un evento del motor detiene la espera en su minuto: bloqueo AV, fibrilación o ectopia ventricular, paro, reacción bifásica, sangrado mayor tras la lisis, neumotórax a tensión, falla del VD por volumen, hipotensión sostenida de la obstrucción, convulsiones o la vuelta tras el alta. También la detienen dos cambios vigilados: una sistólica bajo 70 mmHg que cayó 20 o más, o una SpO₂ bajo 85 % que cayó 5 puntos o más, durante 2 minutos seguidos. La causa de esos dos es desconocida y nunca se usa sola en contra del residente.
> - **Paro (F0-8).** En la anafilaxia, la hemorragia y la bradicardia el paro es verdadero: sin pulso ni presión, con el mensaje acordado («Cardiac arrest occurred at minute X. Resuscitation management is not modelled in this pilot. Subsequent management is not assessable.»). Ninguna orden posterior se ejecuta y nada posterior es evaluable.
> - **Guardas del registro (A–E).** Antes de toda propuesta o lectura del registro: una orden escrita que el simulador no ejecutó (retenida, no entendida, registrada sin modelo, para más tarde, tras un paro) nunca es una omisión (A); una demora del simulador cuenta desde que el residente escribió, y la de la compuerta de razonamiento es de la compuerta, nunca del residente (B, F0-10); no se exige reconocer lo que no estaba disponible o lo contradecía (C); un evento con guion, una limitación del motor, un evento de causa desconocida o uno precedido por una orden no ejecutada nunca sostiene una retroalimentación negativa (D, F0-7); nada después de un paro no modelado es evaluable (E). Un «met» que el registro no puede resolver pasa a «reading», con su motivo: decide usted.
> - **Respuesta a una aclaración (F0-12).** La respuesta completa sólo la orden retenida. Otra orden escrita en la misma respuesta se lee a continuación como orden propia, con su compuerta, sus preguntas, su destino y su recibo, y con el minuto en que se escribió. Si la respuesta deja algo retenido, esa otra orden no corre y su recibo lo dice (TD-70).
> - **Envío.** Un doble clic o una recarga no repiten una orden. Una ejecución detenida se deshace y corre una vez más; si se detiene dos veces, queda marcada como interrumpida, la sala lo dice y no se repite.
> - **Oxígeno (F0-9).** Una mascarilla con reservorio sin flujo escrito usa 15 L/min, y la sala lo dice.
> - **Idioma (F0-11).** En un encuentro en español, las frases nuevas de la Fase 0 se dicen enteras en español; el registro las guarda en inglés.
> - **Casos y límites por caso.** El piloto usa 30 casos (F0-2). El manifiesto de congelamiento (`docs/revision/PILOT_FREEZE_MANIFEST.md`) declara las limitaciones de cada caso; por ejemplo, C-LIMB-ARREST-13: sin tratamiento, la 27m llega al paro hacia el minuto 13.

**Lo que sigue vigente** (revisado, sin corrección): lo esencial sobre la IA (apagada en el encuentro, no autorizada después), los pasos para revisar un encuentro, elegir el caso de un residente, la trombólisis en la TEP, la anafilaxia, la 27m, «General appearance», los criterios C14, la 33f, las fotos y el POCUS, el fluido sin verbo retenido («IV fluids 1 L»), la transfusión (30 minutos por unidad salvo velocidad o reevaluación; el motor lo hace así), el «suero glucosado» sin concentración, TD-51 y TD-59.

- **Recomendación:** **NEEDS UPDATE BEFORE SIGN-OFF** — 11 correcciones (2 de nivel 1), una de ellas una sección nueva.
- **Actualización del 2026-10-07:** las correcciones se aplicaron (`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, sección 1), pero las decisiones de ese día (X-1, J, L-01, D-42, A-2 y el relato antes del candidato) vuelven a dejar la guía desactualizada respecto del candidato final. Recomendación: **DEFER** la firma hasta implementar X-1 y revisar el relato; las frases afectadas están en la sección 3.4 de ese documento.
- **Decisión docente sobre la guía actualizada:** ☐ APPROVE · ☐ REVISE · ☒ **DEFER de la firma** — docente, 2026-10-07. No es un rechazo: la guía docente todavía no se puede firmar. Debe describir el candidato final real, después de implementar X-1, los cambios de A-2 y A-9, la redacción final de D-42, la limpieza de la interfaz bilingüe y la revisión y activación del relato y de la rúbrica en español. Entonces se actualiza (sólo documentación) y vuelve a firma. — Firma y fecha: ________

### I. Guía del residente (fila 63)

**I-63 · `docs/GUIA_RESIDENTE_PILOTO.md`** — TIER 1 · DOCUMENTATION ONLY · **NEEDS UPDATE BEFORE SIGN-OFF**

- **Estado:** «lista para firma, no aprobada» desde el 2026-10-02; anterior a la Fase 0. Este paquete no la edita.
- **Idioma:** la guía sólo existe en español; las etiquetas de la pantalla llevan el inglés entre paréntesis.
- **SHA:** S-C. Ninguna corrección toca el código.
- **Cómo se decide:** marque cada corrección (✓ acepto · ✎ cambio · ✗ no). Con las aceptadas, la guía se actualiza en un commit sólo de documentación y vuelve a usted para la firma: la guía es una decisión.
- **Se infiere:** hoy, el residente no sabe que «reevaluar» sin número es una mirada de 2 minutos, que una orden para más tarde no se ejecuta ni se programa, que la sala retiene una orden de manejo sin razonamiento, qué dice cada recibo ni que tras un paro nada se ejecuta. Puede creer que algo se dio o se programó cuando no fue así.
- **Texto actual:** exacto, con los saltos de línea del archivo unidos.

| # | Líneas | Tipo | Texto actual | Redacción corregida propuesta | Por qué | Nivel | ✓ · ✎ · ✗ |
|---|---|---|---|---|---|---|---|
| I-1 | 3–4 | No coincide (fecha y alcance) | **Estado (cierre prepiloto, 2026-10-02): lista para la firma docente, no aprobada.** | **Estado (Fase 0 cerrada el 2026-10-06): lista para la firma docente, no aprobada.** | Describe la sala anterior a la Fase 0. | TIER 3 | ☐ · ☐ · ☐ |
| I-2 | 16–19 | Incompleta (R-4; condicional X-1) | Parte del relato de un caso, como su informe POCUS, puede verse en inglés mientras su traducción no esté aprobada; cada línea se ve entera en un solo idioma. | Parte del relato de un caso, como su informe POCUS, puede verse en inglés mientras su traducción no esté aprobada, y también algunas líneas del examen que escribe el simulador (por ejemplo, la auscultación o las vías venosas); cada línea se ve entera en un solo idioma. (Si X-1 activa todo el español de R-4: sin cambio.) | Verificado en el código (1.4): hoy esas líneas se ven en inglés en un encuentro en español. | TIER 3 | ☐ · ☐ · ☐ |
| I-3 | 30 | Incompleta (F0-12, TD-70) | si una orden es ambigua, la sala te pregunta, y la pregunta no consume minutos. | si una orden es ambigua, la sala te pregunta, y la pregunta no consume minutos. Tu respuesta completa sólo esa orden: si en la misma respuesta escribes otra, la sala la lee a continuación como una orden aparte y te dice qué pasó con ella; si tu respuesta deja algo sin completar, esa otra orden no se ejecuta y la sala te lo dice: escríbela de nuevo. | F0-12 y TD-70 (K-15, K-16). | TIER 1 | ☐ · ☐ · ☐ |
| I-4 | 31–33 | No coincide (compuerta de razonamiento; F0-10) | **Explica tu razonamiento cuando puedas:** tu modelo de trabajo, tu prioridad, qué respuesta esperas y cuándo reevaluarás. El registro del encuentro (el Management Trace) guarda lo que escribiste y lo que pasó. | **Explica tu razonamiento con tus órdenes de manejo:** qué crees que está pasando, qué esperas que ocurra y qué vas a revisar. Si falta alguna de esas tres cosas, la sala retiene todo el envío y te las pide («ORDEN RETENIDA — FALTA EL RAZONAMIENTO»). Tu prioridad y cuándo reevaluarás también se registran, pero su falta no retiene la orden. Una intervención urgente (ventilar con bolsa y mascarilla, descomprimir el tórax, controlar una hemorragia o poner un cinturón pélvico) nunca se retiene, y puedes explicarla después. El registro del encuentro (el Management Trace) guarda lo que escribiste y lo que pasó. | «Cuando puedas» sugiere que es opcional; la sala retiene el envío completo sin esas tres partes (la compuerta es anterior a la Fase 0, que la confirmó para el piloto: F0-10). | TIER 1 | ☐ · ☐ · ☐ |
| I-5 | 34–35 | Incompleta (tiempo; F0-5, F0-6) | **El paciente responde a lo que haces:** el tiempo avanza con tus órdenes y reevaluaciones. El examen dice lo que se encuentra en el momento en que examinas: para reevaluar, vuelve a examinar. | **El paciente responde a lo que haces:** el tiempo avanza con tus órdenes, tus esperas y tus reevaluaciones. «Espera 15 minutos» (u «observa 15 minutos») avanza el reloj 15 minutos; «reevalúa» sin un número es una mirada a la cabecera de 2 minutos; «da X y reevalúa» es X más esa mirada, y la sala te dice si X alcanzó a actuar. Para ver el efecto de un tratamiento, espera o reevalúa con un intervalo («reevalúa en 15 minutos»). El reloj avanza como máximo 120 minutos de una vez: para más, vuelve a esperar. Si durante una espera ocurre algo importante, la espera se corta en ese minuto, la sala te dice qué pasó y recuperas el control. El examen dice lo que se encuentra en el momento en que examinas: para reevaluar, vuelve a examinar. | F0-5 y F0-6 (K-4 a K-6, K-17); el informe de preparación lo registró (10.2-c). | TIER 1 | ☐ · ☐ · ☐ |
| I-6 | 56–58 | Incompleta (recibos) | Bajo los modos, la sala te dice qué pasó con tu última orden. Si una orden queda retenida o la sala te pregunta algo, el aviso queda a la vista hasta que respondas. | Bajo los modos, la sala te dice qué pasó con tu última orden (su recibo). Por ejemplo: «No se entendió: …» (no se dio ni se hizo nada: escríbela de nuevo con otras palabras); «Registrado como tu decisión, no administrado» (el simulador no modela esa respuesta en este caso: nada cambió); «No se hizo ahora» (una orden para más tarde no se ejecuta ni se programa: escríbela cuando quieras que se haga); o, en un envío con varias órdenes, qué se ejecutó y qué no. Si una orden queda retenida o la sala te pregunta algo, el aviso queda a la vista hasta que respondas. | Recibos de la Fase 0 (K-1, K-3, K-10, K-13, K-14); 10.2-c. | TIER 1 | ☐ · ☐ · ☐ |
| I-7 | — | Falta (paro, F0-8) | — | Nuevo punto en «El encuentro», después del 5: «**Si el paciente hace un paro,** la sala lo dice. La reanimación no está modelada en este piloto: nada de lo que escribas después se ejecuta ni se evalúa.» | F0-8 (K-7, K-8); 10.2-c. | TIER 1 | ☐ · ☐ · ☐ |
| I-8 | — | Falta (envío) | — | Nuevo punto en «La pantalla del encuentro», después de «Manejo»: «**Envía una vez:** «Enviar» se desactiva mientras la sala procesa. Un doble clic o recargar la página no repiten una orden. Si un envío se interrumpe, la sala te lo dice y no lo repite: revisa el estado del paciente y envíalo de nuevo si todavía hace falta.» | Seguridad del envío de la Fase 0 (K-11, K-12); 10.2-c. | TIER 1 | ☐ · ☐ · ☐ |
| I-9 | 65–67 | Condicional (J y X-1) | La sala lo recuerda junto a la foto (por ahora, en inglés). | Si se activa el español (X-1): «La sala lo recuerda junto a la foto.» Si no: sin cambio. | Depende de J y X-1. | TIER 3 | ☐ · ☐ · ☐ |

**Lo que sigue vigente** (revisado, sin corrección): la cuenta, la foto y las iniciales, «sin datos reales», cómo comenzar, terminar con un destino, la revisión de decisiones, la pantalla (el monitor sobre la foto, las cuatro vistas, el «☰ Menú» sin barra lateral durante el encuentro), el POCUS y el E-FAST como informes escritos, y «Después». Las limitaciones del lector no se dicen al residente como instrucciones (guía docente, línea 152).

- **Recomendación:** **NEEDS UPDATE BEFORE SIGN-OFF** — 9 correcciones (6 de nivel 1).
- **Actualización del 2026-10-07:** las correcciones se aplicaron (`docs/revision/B5_GUIAS_Y_BRECHA_BILINGUE.md`, sección 1), pero las decisiones de ese día (X-1, J, L-01, D-42, A-2 y el relato antes del candidato) vuelven a dejar la guía desactualizada respecto del candidato final. Recomendación: **DEFER** la firma hasta implementar X-1 y revisar el relato; las frases afectadas están en la sección 3.4 de ese documento.
- **Decisión docente sobre la guía actualizada:** ☐ APPROVE · ☐ REVISE · ☒ **DEFER de la firma** — docente, 2026-10-07. No es un rechazo: la guía del residente todavía no se puede firmar. Debe describir el candidato final real, después de implementar X-1, los cambios de A-2 y A-9, la redacción final de D-42, la limpieza de la interfaz bilingüe y la revisión y activación del relato y de la rúbrica en español. Entonces se actualiza (sólo documentación) y vuelve a firma. — Firma y fecha: ________

### J. Aviso de la foto (fila 64)

**J-64 · Aviso junto a cada foto vigente** — TIER 3 · EN ACTIVE · ES DRAFT (sólo en el §2; no está en el código)
- Dónde: leyenda bajo la foto del paciente, igual en todas (`clinical_scene.py:207`, `STILL_VIEW_NOTE`).
- EN: A still photograph does not show every clinical sign; examine the patient to assess what it cannot carry.
- ES (§2): Propuesta, sin activar: «Una fotografía fija no muestra todos los signos clínicos; examine al paciente para evaluar lo que no puede mostrar.»
- Se infiere: una foto fija no muestra todos los signos; hay que examinar. Es igual en todas las fotos, así que su presencia no dice nada del paciente.
- Recomendación: **REVIEW CLOSELY** — el inglés está activo y es constante a propósito. La propuesta en español trata de «usted» («examine al paciente») y la sala tutea al residente («Escríbelo de nuevo», «revisa el estado del paciente», «pediste»): conviene decidir el trato antes de activarla (X-1); con «tú» diría «examina al paciente para evaluar lo que no puede mostrar». Las guías citan el aviso (H-6, I-9). El §4 del cierre lo dejó como pendiente que no bloquea.
- Actualización del 2026-10-07: la versión con «tú», coherente con la sala, está en `docs/revision/X1_ESPANOL_PROPUESTO.md`, §2. Aprobada el mismo día (abajo).
- SHA: el inglés, S-A. El español es una propuesta que sólo vive en el §2: revisarla es un cambio de documentación (S-C); mostrarla es X-1, un cambio de código (nuevo SHA).
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: el español, con «tú»: «Una fotografía fija no muestra todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.» El inglés activo no cambia. Mostrarlo es X-1, sin implementar

### K. F0-11 · Las frases nuevas de la Fase 0 en español

- **Hoja:** `docs/revision/F0_11_FRASES_ES.md`, generada desde el código (`test_phase0_spanish.py` comprueba que coincide). Los ejemplos llevan valores de muestra; las palabras entre «» son las del residente y no se traducen.
- **Estado:** ACTIVE en inglés y en español desde el 2026-10-06 (C-2026-10-06-14). La autorización activó las frases; **no es su firma** (F0-11).
- **Firma:** la hoja agrupa la firma en dos filas («Redacción de las frases de la sala», K-1 a K-21; «Eventos que cortan una espera», K-E1 a K-E17). Aquí cada texto lleva su decisión, para cambiar uno sin reabrir el resto.
- **SHA:** S-A. Corregir una frase es cambiar su regla en `language.py` (`_PHASE0_RULES`) y su prueba en `test_phase0_spanish.py`.
- **Revisión del español:** fiel en las 21 frases y los 17 eventos; ninguna dice algo distinto del inglés ni engaña. Observaciones, sin reescribir: (1) dos criterios para los nombres de fármacos (K-13); (2) masculino genérico («el paciente», «traído»), también con pacientes mujeres, como en toda la sala; (3) mayúscula tras dos puntos en K-6 y K-9, cosmética; (4) «recibo» no se explica al residente (K-16, I-6); (5) un calco en K-E6.
- **Nombres de fármacos (X1-0, docente, 2026-10-07):** en un encuentro en español, los fármacos que nombra el motor se muestran con su nombre en español; el identificador canónico guardado no cambia. Resuelve la observación (1). Sin implementar: hoy K-13 y K-14 los muestran en inglés, y K-5 y K-6 también cuando la orden es un fármaco. K-5, K-6, K-13 y K-14 se aprobaron con esta regla (lotes 4 y 5).

**K-1 y K-2 · UNA DECISIÓN → filas 1 y 2 · Orden no entendida (UNRECOGNIZED)** — TIER 1 · ACTIVE
- Dónde: recibo bajo los modos · EN `order_ledger.py:1381` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN (fila 1): Not understood: "Zyvox IV". Nothing was given or done for it. Write it again in other words if you still want it.
- EN (fila 2): Not understood: "Stop the infusion". Nothing was given or done for it. Write it again in other words if you still want it.
- ES (fila 1): No se entendió: «Zyvox IV». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres.
- ES (fila 2): No se entendió: «Stop the infusion». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres.
- Se infiere: esa orden no se ejecutó; no se dio ni se hizo nada; hay que reescribirla.
- Revisión: fiel. «Por ello» puede leerse como «por esa razón»; el sentido (no se dio ni se hizo nada) no cambia. La fila 2 sólo muestra que la cita queda como se escribió: es el mismo texto.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-3 · Fila 3 · Registrada, no administrada (RECORDED_NOT_MODELLED)** — TIER 1 · ACTIVE
- Dónde: recibo bajo los modos (RECORDED_NOT_MODELLED) · EN `order_pipeline.py:505` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Recorded as your decision, not given: "Stop the infusion". This simulator does not model a response to it in this case, so nothing changed.
- ES: Registrado como tu decisión, no administrado: «Stop the infusion». Este simulador no modela una respuesta a ello en este caso, así que nada cambió.
- Se infiere: la orden quedó registrada como decisión, sin efecto en el paciente: no se dio nada.
- Revisión: fiel. «no administrado» también cuando la decisión no es un fármaco, igual que «not given» en inglés.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-4 · Fila 4 · Reevaluación inmediata (mirada en la cabecera)** — TIER 1 · ACTIVE
- Dónde: entrada tras «reevaluar» sin número · EN `time_semantics.py:282` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: On reassessment at the bedside, 2 minutes later, BP 100/60 mmHg.
- ES: Al reevaluar en la cabecera, 2 minutos después, PA 100/60 mmHg.
- Se infiere: pasaron 2 minutos; los valores son de esa mirada, no el resultado de un tratamiento.
- Revisión: fiel. «En la cabecera» = a pie de cama.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-5 · Fila 5 · Mirada inmediata después de una orden** — TIER 1 · ACTIVE
- Dónde: entrada tras «dar X y reevaluar» · EN `time_semantics.py:294` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Normal saline 1000 mL. On reassessment at the bedside 1 minute after the order, BP 100/60 mmHg.
- ES: Suero fisiológico 1000 mL. Al reevaluar en la cabecera, 1 minuto después de la orden, PA 100/60 mmHg.
- Se infiere: la orden se dio y se miró un minuto después: los valores son de los primeros minutos, no su efecto.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Actualización del 2026-10-07 (X1-0): si la orden es un fármaco, su nombre se mostrará en español al implementarse; el ejemplo, un fluido, ya está en español.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: cuando la orden insertada contiene un fármaco reconocido, rige X1-0: en un encuentro en español, el residente lo lee con su nombre en español, y el valor canónico guardado no cambia.

**K-6 · Fila 6 · Espera interrumpida por un evento** — TIER 1 · ACTIVE
- Dónde: entrada al cortarse una espera · EN `time_semantics.py:258` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Given: Normal saline 1000 mL. The wait was interrupted after 7 minutes of the 15 you asked for, at minute 7: systolic pressure 62 mmHg and falling. Now, BP 62/30 mmHg.
- ES: Administrado: Suero fisiológico 1000 mL. La espera se interrumpió tras 7 min de los 15 que pediste, en el minuto 7: presión sistólica de 62 mmHg y en descenso. Ahora, PA 62/30 mmHg.
- Se infiere: la espera se cortó en el minuto del evento; lo pedido no corrió entero y el control vuelve al residente.
- Revisión: fiel. Mayúscula tras «Administrado:» (cosmética; la hoja F0-11 ya la anota).
- Recomendación: **APPROVE AS IS**
- Actualización del 2026-10-07 (X1-0): si la orden es un fármaco, su nombre se mostrará en español al implementarse; el ejemplo, un fluido, ya está en español.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: la misma regla de X1-0 que K-5.

**K-7 · Fila 7 · Paro: mensaje acordado** — TIER 1 · ACTIVE
- Dónde: entrada al paro (mensaje acordado F0-8) · EN `observation_consistency.py:14` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Cardiac arrest occurred at minute 12. Resuscitation management is not modelled in this pilot. Subsequent management is not assessable.
- ES: Se produjo un paro cardíaco en el minuto 12. El manejo de la reanimación no está modelado en este piloto. El manejo posterior no es evaluable.
- Se infiere: hubo un paro; la reanimación no está modelada; lo que siga no se evalúa.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-8 · Fila 8 · Orden escrita después del paro** — TIER 1 · ACTIVE
- Dónde: recibo de una orden tras el paro (TERMINAL_NOT_EXECUTABLE) · EN `order_pipeline.py:434` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Not executed: "Give 1 L LR". The patient is in cardiac arrest; resuscitation management is not modelled in this pilot.
- ES: No se ejecutó: «Give 1 L LR». El paciente está en paro cardíaco; el manejo de la reanimación no está modelado en este piloto.
- Se infiere: nada se ejecuta después del paro.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-9 · Fila 9 · Actualización sin pulso** — TIER 1 · ACTIVE
- Dónde: espera cortada por el paro · EN `time_semantics.py:258` y el estado sin pulso · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: The wait was interrupted after 3 minutes, at minute 3: cardiac arrest, pulse lost. Now, No pulse: Ventricular fibrillation on the monitor; no blood pressure; not breathing; unresponsive.
- ES: La espera se interrumpió tras 3 min, en el minuto 3: paro cardíaco, sin pulso. Ahora, sin pulso: Fibrilación ventricular en el monitor; sin presión arterial; sin respiración; sin respuesta.
- Se infiere: la espera se cortó por el paro; el monitor y el examen muestran paro.
- Revisión: fiel. Mayúscula tras «sin pulso:» (cosmética). En inglés queda «Now, No pulse:» (informe de la Fase 0, §16), sin efecto en el registro.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: la mayúscula tras «sin pulso:» es cosmética y no pide revisión.

**K-10 · Fila 10 · Orden para más tarde, no programada** — TIER 1 · ACTIVE
- Dónde: recibo de una orden para más tarde · EN `time_semantics.py:161` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Not done now: "Give aspirin 300 mg in 30 minutes". An order for a later time is not carried out in this pilot: nothing was given and nothing was scheduled. Write it again when you want it done.
- ES: No se hizo ahora: «Give aspirin 300 mg in 30 minutes». En este piloto, una orden para más tarde no se ejecuta: no se administró nada ni se programó nada. Escríbela de nuevo cuando quieras que se haga.
- Se infiere: no se dio ni se programó: hay que escribirla cuando corresponda.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-11 · Fila 11 · Envío interrumpido (nada aplicado)** — TIER 1 · ACTIVE
- Dónde: aviso de un envío interrumpido · EN `submission_guard.py:350` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Your order "Give the normal saline" was interrupted while it was being processed, and nothing of it was applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed.
- ES: Tu orden «Give the normal saline» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria.
- Se infiere: el envío se interrumpió y no se aplicó nada; no se repetirá solo.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-12 · Fila 12 · Envío interrumpido (quizá aplicado en parte)** — TIER 1 · ACTIVE
- Dónde: aviso de un envío interrumpido · EN `submission_guard.py:350` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Your order "Give 1 L LR" was interrupted while it was being processed, and part of it may have been applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed.
- ES: Tu orden «Give 1 L LR» se interrumpió mientras se procesaba, y es posible que una parte de ella se haya aplicado. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria.
- Se infiere: puede haberse aplicado una parte: revisar el estado antes de reenviar.
- Revisión: fiel; «es posible que una parte de ella se haya aplicado» conserva la incertidumbre del inglés.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-13 · Fila 13 · Paquete parcial: parte no ejecutada** — TIER 1 · ACTIVE
- Dónde: recibo de un paquete parcial · EN `order_pipeline.py:371` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: **PART OF THIS ORDER WAS NOT CARRIED OUT** /  / Executed now: **aspirin 300 mg PO**. / Not carried out: **norepinephrine**. Nothing of it has been given; write it again as a new order if you still want it.
- ES: **PARTE DE ESTA ORDEN NO SE EJECUTÓ** /  / Ejecutado ahora: **aspirin 300 mg PO**. / No ejecutado: **norepinephrine**. No se ha administrado nada de ello; escríbelo de nuevo como una orden nueva si aún lo quieres.
- Se infiere: una parte se ejecutó y otra no; lo no ejecutado no se dio.
- Revisión: fiel. Los fármacos que nombra el motor quedan en inglés («aspirin», «norepinephrine»), los fluidos se traducen («suero fisiológico», K-5, K-6, K-14) y las notas de la TEP traducen el fármaco («alteplasa», B-24, B-25). Es la convención declarada de la sala (hoja F0-11, regla 3), pero conviven dos criterios: confirmarlos.
- Recomendación: **APPROVE con la regla de X1-0**, como la docencia decidió K-5 y K-6 (ajustada el 2026-10-07, lote 4; antes, REVISE, que lleva al mismo texto) — la frase es fiel; en un encuentro en español, los fármacos que nombra el motor se muestran con su nombre en español («Ejecutado ahora: **aspirina 300 mg PO**», «No ejecutado: **noradrenalina**»), y el valor canónico guardado no cambia. Sin implementar: hoy se ven en inglés.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07, con la regla de X1-0: en un encuentro en español, los fármacos reconocidos que ve el residente llevan su nombre en español; el valor canónico guardado no cambia.

**K-14 · Fila 14 · Paquete parcial: parte retenida** — TIER 1 · ACTIVE
- Dónde: recibo de un paquete parcial · EN `order_pipeline.py:378` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: **PART OF THIS ORDER IS HELD — CLARIFICATION REQUIRED** /  / Executed now: **aspirin 300 mg PO**. / Held until you answer: **normal saline**. Nothing of it has been given.
- ES: **PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN** /  / Ejecutado ahora: **aspirin 300 mg PO**. / Retenido hasta que respondas: **suero fisiológico**. No se ha administrado nada de ello.
- Se infiere: una parte se ejecutó y otra espera una aclaración; lo retenido no se ha dado.
- Revisión: fiel; la misma convención que K-13.
- Recomendación: **APPROVE con la regla de X1-0**, como K-5, K-6 y K-13 (precisada el 2026-10-07, lote 4; antes, APPROVE AS IS con esta nota) — al implementarse, «aspirin 300 mg PO» se mostrará «aspirina 300 mg PO»; el valor canónico guardado no cambia.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07, con la regla de X1-0, como K-13.

**K-15 · Fila 15 · Orden junto a la respuesta, cuando algo sigue retenido** — TIER 1 · ACTIVE
- Dónde: recibo de una orden escrita en la respuesta · EN `order_pipeline.py:153` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Not run: "ceftriaxone 2 g IV" was written in the answer to the question above, which completes the held order only. Write it again as a new order if you still want it.
- ES: No se ejecutó: «ceftriaxone 2 g IV» se escribió en la respuesta a la pregunta anterior, que solo completa la orden retenida. Escríbelo de nuevo como una orden nueva si aún lo quieres.
- Se infiere: la orden de la respuesta no corrió porque algo sigue retenido: hay que reescribirla.
- Revisión: fiel. Es el caso protegido de TD-70 (a).
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-16 · Fila 16 · Orden después de la respuesta, leída a continuación (F0-12)** — TIER 1 · ACTIVE
- Dónde: aviso tras la respuesta (F0-12) · EN `app.py:11240` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Also in your answer: "give 500 mL LR". The answer completes the held order only; this order is read next, as an order of its own, with its own receipt.
- ES: También en tu respuesta: «give 500 mL LR». La respuesta solo completa la orden retenida; esta orden se lee a continuación, como una orden propia, con su propio recibo.
- Se infiere: la otra orden de la respuesta se lee después, como orden propia, con su propio aviso.
- Revisión: fiel. «Recibo» (y «receipt») es el término de la sala para el aviso de qué pasó con una orden; la guía del residente no lo explica hoy (I-6).
- Recomendación: **APPROVE AS IS**
- Actualización del 2026-10-07: la guía del residente actualizada (I-3 e I-6, sin firmar) ya explica «recibo» y este caso; la nota de arriba es anterior a esa actualización.
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07: se conserva la semántica de F0-12; una orden escrita después de responder la aclaración se procesa como orden propia, con su propio destino y su propio recibo. La guía del residente puede explicar «recibo» cuando se actualicen H-62 e I-63; eso no bloquea esta aprobación.

**K-17 · Fila 17 · Límite de 120 minutos por paso** — TIER 1 · ACTIVE
- Dónde: respuesta a una espera de más de 120 minutos · EN `family_engine.py:626` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Specify a reassessment interval from 0 to 120 minutes. The simulator moves the clock at most 120 minutes in one step (a limit of this pilot): write a wait or a reassessment of 120 minutes or less, and wait again afterwards if you need more time.
- ES: Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 minutos de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o menos, y vuelve a esperar después si necesitas más tiempo.
- Se infiere: no se avanza más de 120 minutos de una vez: hay que esperar en tramos.
- Revisión: fiel.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-18 · Fila 18 · Paro de la anafilaxia tras una dosis que se agotó** — TIER 1 · ACTIVE
- Dónde: entrada al paro de la anafilaxia · EN `anaphylaxis_reaction.py:148` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier had worn off and the reaction had come back. Nothing else that was given acts on the reaction.
- ES: Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes había perdido su efecto y la reacción había vuelto. Nada más de lo administrado actúa sobre la reacción.
- Se infiere: la adrenalina se dio, su efecto se agotó y la reacción volvió; lo demás no actúa sobre la reacción. No dice «nunca dada». (Con la redacción revisada: la adrenalina se dio y no controló la reacción.)
- Revisión: fiel. VINCULADA con K-21 (su hermana).
- Recomendación: **REVISE** (actualizada el 2026-10-07, al preparar el lote final; antes, APPROVE AS IS) — la traducción es fiel, pero el inglés describe un curso que no siempre ocurrió. Comprobado en la sala real, sin cambiar código (`pilot_acceptance`): en `anaphylaxis_63m_betablocked`, con una sola dosis de adrenalina IM y espera, la reacción nunca mejora (empeora desde la llegada) y el paro llega en el minuto 71 con esta frase, que dice que el efecto «se agotó» y que la reacción «había vuelto». En `anaphylaxis_29f` es exacta: la reacción mejora y después vuelve. Es el curso que el caso enseña (una respuesta menor que la esperada por el betabloqueo). Opciones: (a) APPROVE tal cual, aceptando esa imprecisión en la 63m; (b) una frase cierta en los dos cursos: EN «Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier did not keep the reaction under control. Nothing else that was given acts on the reaction.» · ES «Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.»; (c) dos frases según el curso, la actual si la reacción había mejorado y otra si nunca mejoró. (b) y (c) cambian el texto del motor y su español: nuevo SHA (16.4). Se recomienda (b), la más simple.
- Decisión docente: ☐ APPROVE · ☒ **REVISE** · ☐ DEFER — docente, 2026-10-07. Redacción nueva: EN «Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier did not keep the reaction under control. Nothing else that was given acts on the reaction.» · ES «Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.» Motivo docente: es cierta cuando la adrenalina ayudó al principio y después perdió su efecto, y cuando la dosis previa nunca controló bien la reacción, también en el caso con betabloqueo. Corrección de texto antes del candidato final (TD-82); sin implementar.

**K-19 · Fila 19 · Flujo por omisión de la mascarilla con reservorio** — TIER 1 · ACTIVE
- Dónde: recibo de la mascarilla con reservorio sin flujo (F0-9) · EN `order_pipeline.py:93` · ES `language.py:349–471` (`_PHASE0_RULES`).
- EN: oxygen non-rebreather mask 15 L/min: no flow was written; the standard non-rebreather flow, 15 L/min, was used.
- ES: Oxígeno por mascarilla con reservorio a 15 L/min: no se escribió un flujo; se usó el flujo habitual de la mascarilla con reservorio, 15 L/min.
- Se infiere: sin flujo escrito, se usó 15 L/min.
- Revisión: fiel. Mayúscula inicial en español («Oxígeno»); en inglés empieza con la etiqueta del motor.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-20 · Examen de cualquier región tras el paro** — TIER 1 · ACTIVE
- Dónde: el panel del examen, cualquier región, tras el paro · EN `observation_consistency.py:47` · ES `language.py:1347` (`_EXAMINATION_SENTENCES_ES`, el panel) y `_PHASE0_RULES` (las entradas).
- EN: Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest. Resuscitation is not modelled in this pilot.
- ES: Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está modelada en este piloto.
- Se infiere: el paciente está en paro y la reanimación no está modelada.
- Revisión: fiel. A diferencia de las filas 12–18 de R-4, se ve en español también en el panel del examen.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-21 · Paro de la anafilaxia sin tratar (frase anterior a la Fase 0, hermana de la 18)** — TIER 1 · ACTIVE
- Dónde: entrada al paro de la anafilaxia sin tratar · EN `anaphylaxis_reaction.py:141` · ES `_PHASE0_RULES`.
- EN: Circulatory arrest after twenty-five minutes of untreated anaphylaxis. Adrenaline was the treatment that was missing; nothing else that was given acts on the reaction.
- ES: Paro circulatorio tras veinticinco minutos de anafilaxia no tratada. La adrenalina era el tratamiento que faltaba; nada más de lo administrado actúa sobre la reacción.
- Se infiere: el paro se debió a una anafilaxia sin adrenalina.
- Revisión: fiel. Es anterior a la Fase 0 (no estaba en R-4); se tradujo con su hermana (K-18) para que el paro de la anafilaxia no se lea en dos idiomas.
- Recomendación: **APPROVE AS IS**
- Decisión docente: ☒ **APPROVE** · ☐ REVISE · ☐ DEFER — docente, 2026-10-07

**K-E1 a K-E17 · Eventos que cortan una espera** — TIER 2 · ACTIVE. Aparecen dentro de la frase de K-6. EN `event_provenance.py:41` y siguientes (eventos y los dos cambios vigilados) y `time_semantics.py:257` («a critical change») · ES `_PHASE0_RULES`. Se infiere: qué evento cortó la espera y en qué minuto; en los dos cambios vigilados (K-E15, K-E16) la causa es desconocida y nunca se usa sola en contra del residente (F0-6).

| # | EN exacto | ES exacto | Revisión | Recomendación | Decisión docente |
|---|---|---|---|---|---|
| K-E1 | complete atrioventricular block | bloqueo auriculoventricular completo | Fiel. | **APPROVE AS IS** | ☒ **APPROVE** (docente, 2026-10-07) |
| K-E2 | ventricular fibrillation, pulse lost | fibrilación ventricular, sin pulso | Fiel. | **APPROVE AS IS** | ☒ **APPROVE** (docente, 2026-10-07) |
| K-E3 | cardiac arrest, pulse lost | paro cardíaco, sin pulso | Fiel. | **APPROVE AS IS** | ☒ **APPROVE** (docente, 2026-10-07) |
| K-E4 | cardiac arrest from uncontrolled haemorrhage | paro cardíaco por hemorragia no controlada | VINCULADA con A-1 (el mismo paro, otro nombre, también en inglés). | **APPROVE AS IS** | ☒ **APPROVE** (docente, 2026-10-07) |
| K-E5 | circulatory arrest from untreated anaphylaxis | paro circulatorio por anafilaxia no tratada | Fiel. Hallazgo del 2026-10-07, comprobado en la sala real sin cambiar código (`pilot_acceptance`): la etiqueta es la misma con adrenalina o sin ella. En `anaphylaxis_63m_betablocked`, con una dosis IM, la espera se corta en el minuto 71 con «circulatory arrest from untreated anaphylaxis», en la misma entrada que K-18 («…without effective adrenaline…»); en `anaphylaxis_29f` con una dosis, igual (minuto 93). Es el mismo defecto que llevó a revisar K-18 (TD-82). Propuesta, a decisión docente, cierta en los dos cursos: EN «circulatory arrest from anaphylaxis without effective adrenaline» · ES «paro circulatorio por anafilaxia sin adrenalina eficaz». Otra opción: dos etiquetas, según se haya dado adrenalina o no. Cualquiera de las dos cambia el motor y su regla en español (SHA nuevo) | **NEEDS REVISION** (2026-10-07; antes, APPROVE AS IS) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E6 | loss of circulation from the falling rate | pérdida de la circulación por la frecuencia que cae | Calco del inglés («from the falling rate»); se entiende. Opcional y sin cambiar el sentido: «por la caída de la frecuencia». No es necesario cambiarlo. | **REVIEW CLOSELY** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E7 | generalized seizure | convulsión generalizada | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E8 | the anaphylactic reaction returns | la reacción anafiláctica vuelve | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E9 | tension pneumothorax on the ventilator | neumotórax a tensión con el ventilador | «Con el ventilador» se entiende («en ventilación mecánica» sería más usual). | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E10 | major bleeding after thrombolysis | hemorragia mayor tras la trombólisis | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E11 | frequent ventricular ectopy on dobutamine | extrasístoles ventriculares frecuentes con dobutamina | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E12 | right ventricle failing under fast volume | falla del ventrículo derecho con volumen rápido | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E13 | sustained hypotension from the obstruction | hipotensión sostenida por la obstrucción | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E14 | brought back after discharge | traído de vuelta tras el alta | Masculino genérico, como «el paciente» en toda la sala, también con pacientes mujeres. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E15 | systolic pressure 62 mmHg and falling | presión sistólica de 62 mmHg y en descenso | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E16 | saturation 84 % and falling | saturación de 84 % y en descenso | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| K-E17 | a critical change | un cambio crítico | Fiel. | **APPROVE AS IS** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

## 3. Fuera del piloto de residentes (F0-2): las filas de la 41m

`trauma_hemothorax_41m` quedó fuera del piloto de residentes y sigue en el sandbox docente (F0-2). Tres filas son sólo de ese caso: **C-34** (marca del cinturón), **D-44** (su límite) y **F-59** (su ficha R-2). Llevan su decisión en su bloque.

- Firmarlas sólo hace falta si el caso se usará en el sandbox docente.
- DEFER no cambia el SHA y no bloquea B-5: no cuentan entre las decisiones requeridas.
- REVISE sí es un cambio de código (nuevo SHA), y por eso, si se hace, va antes del candidato final.
- La fila 1 de R-4 (A-1) también nombra la 41m, pero se usa en la 27m: es requerida.

## 4. DESPUÉS DEL DESPLIEGUE, ANTES DEL GO DEL PILOTO

**Actualización del 2026-10-07:** por decisión docente, el relato (4.1) y la rúbrica (4.2) pasaron a antes de
congelar el candidato final; después del despliegue sólo queda lo de 4.4. El relato aprobado entra en el candidato
en `case_text/es/approvals.json` (4.1); el mecanismo de la rúbrica se identifica antes de implementarla (4.2).

Antes de esas decisiones no bloqueaban B-5: el contrato de preparación los ponía después del despliegue y antes de abrir el piloto (informe de preparación, 10.1 y 20.5; §4 del cierre, punto 2), y se aprobaban en el tablero docente de la base desplegada. Ahora no están entre las 100 decisiones, pero el candidato final no se congela sin ellos (1.5).

**4.1 · El relato en español de cada caso** — ANTES DEL CANDIDATO FINAL desde el 2026-10-07 (antes, POST-DEPLOYMENT REVIEW) · S-E

- Qué es: 1.119 pasajes de los 31 casos (presentación, respuestas de la historia, examen, informes de estudios; `case_text/es/<familia>.json`).
- En el piloto se revisan los 30 casos aceptados; la 41m, sólo si se usará en el sandbox.
- Dónde: «Case narrative in Spanish (faculty review) · Narrativa de los casos en español», en el panel docente.
- Cómo se decide: caso por caso, «aprobar» o «pedir cambios» con una nota.
- La aprobación nombra la versión exacta que se leyó: un cambio posterior en cualquier idioma deja el caso pendiente otra vez.
- Sin aprobación, el caso se ve en inglés, línea por línea entera.
- Incluye el español de las filas 27–33, 35 y 36 (columna ES del bloque C) y el de la 34 si se usa la 41m.
- Una frase que comparten dos casos (la fila 31) se aprueba con cada caso.
- Si el piloto corre en español, va antes de jugar en español.
- **Decisión docente (2026-10-07), que reemplaza la anterior del mismo día** (que la ponía después del
  despliegue): el relato en español de los 30 casos del piloto se revisa **antes de congelar el candidato final**,
  y el candidato bilingüe no se congela sin esa revisión. Motivo: el texto vive en el repositorio
  (`case_text/es/`), y corregirlo después del despliegue daría un SHA nuevo y otro despliegue.
- **Cómo llega la aprobación al piloto: camino (a)** (decisión docente del 2026-10-07). Terminada la revisión
  docente de los 30 casos, las versiones aprobadas entran en el candidato final en `case_text/es/approvals.json`.
  Así no hace falta volver a registrarlas a mano en la base del piloto después del despliegue (camino b,
  descartado). Requisitos:
  - en el repositorio y determinista;
  - comprobable con una prueba antes de congelar el candidato;
  - sin nombres de médicos ni de revisores, sin identificadores personales y sin metadatos de la revisión que no
    hagan falta;
  - sólo lo necesario para atar la aprobación al caso, la versión y el texto exactos que se aprobaron.
- **El archivo todavía no se crea:** primero se completa la revisión docente.
- **Lo que ya hace el código** (comprobado el 2026-10-07, sin cambiarlo):
  - `case_text.pack_approvals` lee el archivo y toma sus filas con `"decision": "approved"`;
  - `case_text.status` ata cada fila a su caso por `variant_id` y al texto exacto por `version`, el SHA-256 de
    todos los pasajes del caso en los dos idiomas (`case_text.version`);
  - una fila `{"variant_id", "version", "decision"}` basta para el lector actual, que no usa ningún otro campo. El
    `reviewer` que nombra la documentación de `pack_approvals` no hace falta, y el archivo no lo llevará;
  - un cambio posterior en cualquiera de los dos idiomas cambia la versión y devuelve el caso al inglés;
  - una revisión registrada después en la base del piloto, sobre la misma versión, prevalece sobre el archivo.
- **Falta, al implementar (no autorizado todavía):**
  - la exportación que escriba sólo esos campos: no hay herramienta, y la base donde se revise guarda la cuenta de
    quien revisa, que no se exporta;
  - la prueba que, con la base vacía, compruebe que los 30 casos del piloto se leen aprobados en español sólo por
    el archivo, y que el archivo no tiene otros campos.
- El archivo vive fuera de `docs/`: entra con el candidato y su contrato 16.4.

**4.2 · Los descriptores de la rúbrica en español** — ANTES DEL CANDIDATO FINAL desde el 2026-10-07 (antes, POST-DEPLOYMENT REVIEW)

- Qué es: qué evalúa cada uno de los 5 dominios (D1–D5) y sus niveles 0–3 (`rubric_text/es/descriptors.json`, rúbrica 1.0-pilot).
- Cómo se decide: dominio por dominio, en el tablero.
- Sin aprobación, el dominio se ve en inglés. Los puntajes y los criterios siguen en inglés, que son la norma.
- **Decisión docente (2026-10-07): REVIEW BEFORE FINAL CANDIDATE FREEZE.** La rúbrica en español vive en el
  repositorio (`rubric_text/es/descriptors.json`). La docencia la revisa, y su español, el que leen residentes y
  docentes, queda listo antes de congelar el SHA final del despliegue. No se difiere a después del despliegue.
- **Sin implementar.** Antes de implementar, falta identificar el mecanismo exacto con que la rúbrica aprobada se
  activa en el candidato, de modo que se compruebe de forma determinista en él. Dato del código, no una decisión:
  `rubric_text.py` tiene la misma forma que el relato (revisión por dominio, atada a un hash de sus descriptores en
  los dos idiomas) y ya lee `rubric_text/es/approvals.json` (`rubric_text.pack_approvals`), que hoy no existe.

**4.3 · Cómo evitar un SHA nuevo después del despliegue.** Resuelto el 2026-10-07: el relato (4.1) y la rúbrica
(4.2) se revisan antes del candidato, y esa revisión ya no es opcional. Lo que sigue queda como antecedente.

- El tablero no edita textos: corregir una traducción es un cambio del repositorio, con un candidato nuevo y otro despliegue (S-E).
- Leer antes del candidato final los relatos de los casos que se jugarán en español, y los descriptores, permite corregirlos dentro del mismo SHA.
- Es opcional y no bloquea B-5.

**4.4 · También después del despliegue, fuera de B-5:**

- las fotos (TD-56);
- la prueba de humo, que incluye el primer encuentro sobre la base vacía (TD-78);
- `MRS_LANGUAGE`, el idioma inicial de la pantalla, que se fija en los Secrets (15.7, «con B-5»; no cambia el SHA);
- la autorización explícita del piloto (condición C).

## 5. Impacto en el SHA final

| Bloque | APPROVE tal cual | REVISE | DEFER |
|---|---|---|---|
| X-1 | (a) activar: nuevo SHA | (c) parcial: nuevo SHA | (b) sin cambio |
| A (EN) · B · C (EN y activos) · D-39 · K | Sin cambio | Nuevo SHA (código) | Sin cambio; texto activo sin firma |
| A (ES 1–11) · E (ES) | Sin cambio (sigue sin mostrarse) | Nuevo SHA (`spanish_drafts.py`; B-1 por 18.2) | Sin cambio |
| J (ES) | Sin cambio (sigue sin mostrarse) | Sólo documentación (la propuesta vive en el §2) | Sin cambio |
| A (ES 12–18) | Sin cambio; mostrarlo en el panel es X-1 | Nuevo SHA (`language.py`) | Sin cambio |
| D-40 a D-43 · E (EN) | Sin cambio | Nuevo SHA (banco) | Sin cambio |
| F · G | Sin cambio | Nuevo SHA (banco o notas; hoja regenerada) | Sin cambio |
| H · I | — | Commit sólo de documentación: SHA nuevo, runtime igual; B-1 sigue válido (18.2) | — |
| Sección 4 | Sin cambio (base desplegada) | Corregir = nuevo SHA y nuevo despliegue | El caso o el dominio siguen en inglés |

Actualización del 2026-10-07: el relato (4.1) y la rúbrica (4.2) se revisan antes del candidato final. Corregirlos
entonces cambia el SHA antes de congelarlo, no después del despliegue, y la fila «Sección 4» ya no se aplica a
ellos. El archivo de aprobaciones del relato (`case_text/es/approvals.json`) también entra antes del congelamiento:
está fuera de `docs/`, así que va con el contrato 16.4.

Si el SHA final cambia por código, el contrato de promoción (16.4) vuelve a correr la suite, las 56 regresiones y B-1 sobre ese SHA. Si sólo cambia `docs/`, B-1 sigue valiendo para `8ff41a4` (18.2).

## 6. Cómo se armó y verificó este paquete

- Cada texto EN/ES citado sale, sin copia manual, de las hojas del repositorio (`CIERRE_PREPILOTO.md` §2, `R4_FRASES_MOTOR.md`, `F0_11_FRASES_ES.md`, `R2_POCUS_C14.md`) o del banco y los borradores (`case_assessment_bank.py`, `spanish_drafts.py`). Las 18 frases de R-4 coinciden entre la hoja R-4 y el §2.
- Cada texto se buscó en el código para confirmar su estado y su lugar. Los números de línea se calcularon desde los archivos en `f5096ae`.
- Se comprobó en el código, llamando a las funciones de la sala:
  - `language.examination` (panel del examen) deja en inglés las filas 2–18 de R-4; `language.say` (entradas) traduce las 12–18;
  - la fila 1 queda entera en inglés;
  - ninguna frase en borrador aparece dentro de una entrada traducida (no hay líneas mezcladas);
  - la fila 37 y K-20 están en español en el panel del examen.
- Las guías se citan por número de línea, y cada «texto actual» se comprobó contra el archivo.
- **No se hizo:**
  - recorrer la sala en español en un navegador (AppTest no selecciona la opción traducida; informe de la Fase 0, §16);
  - abrir el tablero docente de una base desplegada;
  - cambiar texto, código, pruebas, guías o casos.

## 7. Firma

| Bloque | Decisiones requeridas | Resultado | Fecha | Firma |
|---|---|---|---|---|
| X-1 · Activación del español | 1 | | | |
| A · R-4: 18 frases del motor | 18 | | | |
| B · Notas de la TEP y aviso del sangrado | 8 | | | |
| C · Líneas del examen y E-FAST | 12 (+1 opcional) | | | |
| D · Límites declarados | 5 (+1 opcional) | | | |
| E · C14 de la 52m y la 70f | 2 | | | |
| F · R-2: 14 fichas POCUS | 13 (+1 opcional) | | | |
| G · R-3: TDFC final | 1 | | | |
| H · Guía docente | 1 | | | |
| I · Guía del residente | 1 | | | |
| J · Aviso de la foto | 1 | | | |
| K · F0-11: frases nuevas de la Fase 0 | 37 | | | |
| 4.1 · relato en español (30 casos) | Antes de congelar el candidato final; entra en `case_text/es/approvals.json` | | | |
| 4.2 · rúbrica en español | Antes de congelar el candidato final (mecanismo por identificar) | | | |
