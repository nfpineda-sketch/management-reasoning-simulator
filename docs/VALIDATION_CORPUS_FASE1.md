# Validation corpus · Fase 1: lenguaje clínico escrito por médicos de urgencia

Ciclo 3 del AI Advisor, decisiones docentes del 2026-09-27 (DF-6, §19–§25,
§42–§48, §64–§75, §95–§97).

**Reemplaza** a `docs/DISENO_VALIDATION_CORPUS.md` para la Fase 1. Ese diseño
del Ciclo 2 queda como antecedente: por decisión docente no se construyen las
240 frases artificiales.

## Estado

| Componente | Estado |
|---|---|
| Plantilla Word, ES y EN | **IMPLEMENTED y TESTED.** Hay 12 documentos del piloto en `validation/plantillas_v1/` y un generador. |
| Ingesta DOCX → texto → entradas → página real → salida estructurada → reporte | **IMPLEMENTED y TESTED** (`validation_corpus.py`, `tools_validation_corpus.py`, 25 tests). |
| Reference standard: anotación ciega, adjudicación y clases de error | Diseñado y con soporte en la herramienta. **Sin datos.** |
| Piloto | **PROPUESTO** (§4). No se envió nada ni se contactó a nadie (§97). |
| Datos de médicos | **Ninguno.** Todo texto usado en los tests es sintético y escrito para ellos. |

## 1. Fase 1 y Fase 2

**Fase 1 (este documento).** Mide lenguaje clínico libre, offline.

- Pregunta: *¿el motor entiende lenguaje clínico natural, escrito sin conocerlo?*
- Los médicos reciben un caso y escriben en Word cómo lo manejarían.
- No usan el simulador ni ven su sintaxis, sus reglas ni su respuesta.
- Después, la herramienta hace leer ese texto al producto real.

**Fase 2 (fuera del Ciclo 3).** Mide la usabilidad durante un encuentro real.

- Pregunta: *¿es natural y usable durante un encuentro dinámico?*
- Residentes o médicos corren encuentros completos.
- Se mide lo que la Fase 1 no puede ver:
  - órdenes repetidas;
  - adaptación del usuario al lector;
  - fricción y aclaraciones en vivo;
  - latencia;
  - acciones abandonadas;
  - fidelidad del Management Trace a lo largo de la dinámica.

Las dos validaciones no se mezclan.

## 2. Qué recibe el médico

**Un archivo Word por caso**, por ejemplo `EM01_C03_es.docx`. Lo genera
`validation_corpus.template` a partir del texto del banco, sin inventar nada.
Contiene lo mismo que el simulador muestra en la puerta:

- la presentación y el handover (`arrival_brief`: queja y comienzo, más quién
  da la historia cuando no es el paciente);
- los cuatro números del monitor (FC, SpO₂, PA y FR);
- el peso y la talla de la ficha, con cómo se obtuvieron.

**Lo que no contiene:**

- **Diagnóstico.** El caso aparece como un código (C01…C06), porque los
  identificadores del banco nombran el diagnóstico.
- **Examen físico, resultados, trazado del monitor ni fotografía.** Se obtienen
  preguntando, examinando o pidiendo. El documento lo dice: «si pediría algo,
  escríbalo; si su conducta dependería del resultado, puede decir qué haría
  según lo que encuentre».

**Instrucciones (ES):**

- Siguen el texto preferido de §66.
- Invitan, «según corresponda», a escribir los elementos de §21 en lenguaje
  clínico corriente. Nunca nombran las categorías internas (working model,
  expected effect, contingency, reassessment target). Nada es obligatorio.
- Incluyen literalmente: «Escriba exactamente como lo haría naturalmente. No
  existe un formato correcto y no intente adaptar su lenguaje a un sistema
  informático.»

**Versión en inglés.** Está escrita en inglés, no traducida frase a frase; el
recordatorio equivalente va igual de explícito.

**Encabezado.** Tiene cuatro campos:

- código de participante, que completa el custodio;
- idioma de la respuesta;
- caso;
- versión del documento (`VC1-ES` / `VC1-EN`).

**Respuesta.** Va en un cuadro amplio con la etiqueta «Su manejo». Cada párrafo
se lee como una entrada, en el orden escrito, y un salto de línea dentro de un
párrafo queda dentro de la entrada. El texto escrito después del último cuadro
se informa y no se lee como entrada.

**Evolución (opcional).** La plantilla admite texto de evolución escrito por el
docente, con un cuadro «Su manejo después de la evolución N» a continuación.
El piloto no la usa: escribir una evolución es contenido clínico y le
corresponde al docente.

**Texto del caso en español.** Viene de `case_text/es`. Su aprobación docente
vive en la base de datos del despliegue y **no se verificó**, y el generador lo
dice en `templates.json`. **Antes de enviar un documento en español hay que
confirmar que el caso está aprobado.**

### Verificación de la plantilla

- **python-docx 1.2.** Es una implementación independiente de OOXML, usada en
  un entorno temporal y no como dependencia. Abre la plantilla, encuentra sus
  dos tablas, permite escribir en el cuadro como lo haría un usuario y la
  guarda.
- **Lectura del archivo guardado.** El lector recupera código, caso y entradas.
  El nombre de autor que se escribió en las propiedades no aparece en la salida.
- **Word y LibreOffice no se probaron.** LibreOffice de este entorno no tiene
  Writer y no abre ningún documento, ni siquiera un `.txt`. Antes de enviar,
  abra un documento en Word: **pendiente para el docente**.

## 3. Del documento al reporte (ingesta, §46)

```
DOCX → TEXTO → SEGMENTACIÓN → PÁGINA REAL DEL PRODUCTO → SALIDA ESTRUCTURADA → REPORTE
```

1. **DOCX → texto.**
   - Solo `word/document.xml` se lee al corpus, en orden de documento.
   - El texto insertado con control de cambios se toma y el borrado no.
   - Se leen tablas, hipervínculos y controles de contenido. Los cuadros de
     texto se ignoran con aviso.
   - Comentarios, encabezados y propiedades nunca se leen. Las propiedades solo
     se miran para avisar que traen un nombre de autor, sin leerlo.
   - Un documento que declara DOCTYPE o entidades se rechaza.
2. **Segmentación.**
   - Un párrafo no vacío dentro de un cuadro de respuesta es una entrada.
   - Identificador estable: `EM01-C03-es-b1-e04` (participante, caso, idioma,
     cuadro, entrada).
3. **Página real.**
   - Cada documento es un encuentro de su caso del banco.
   - Cada entrada se envía, tal como fue escrita, al cuadro de órdenes de
     `app.py`, con el mismo `tools_tanda20.rehearse` del ensayo: Streamlit en
     proceso, base temporal, sin clave de proveedor y semilla fija.
   - **No hay parser paralelo** y el motor recibe solo el texto original (§44).
   - Un encuentro necesita un Decision Challenge para abrir. Se usa el primero,
     por identificador, que incluye la familia del caso; el lector no depende
     de él.
4. **Retenciones.** Nadie está ahí para responder, así que:
   - una orden retenida para pedir el razonamiento se completa con las
     respuestas neutras del ensayo. Quedan registradas como `completed` y nunca
     como `stated`, y el reporte las marca como del harness;
   - una orden retenida para una aclaración se cancela.
   - La opción `resolve_until_clear` resuelve hasta que no quede nada
     pendiente. Sin ella, la entrada siguiente se tomaba como respuesta a la
     aclaración pendiente, como se vio en este ciclo con una prueba sintética.
     Los 20 guiones del ensayo mantienen su comportamiento.
5. **Salida estructurada** (`engine_output.json`). Por entrada:
   - lo que la página dijo;
   - la retención y cómo se resolvió;
   - las entradas del Management Trace que produjo, emparejadas por el texto
     enviado.
   - Además registra el commit, si había cambios locales, la versión del
     simulador, la semilla y la fecha.
6. **Comparación con la anotación y reporte** (`report.json`, `report.md`):
   métricas y trazabilidad, §§5–7.

**Comandos.** Todos son deterministas y sin IA:

```
python tools_validation_corpus.py templates --out DIR [--language es|en|both] [--case C01] [--participant EM01]
python tools_validation_corpus.py ingest --corpus CARPETA --subset development|sealed --out SALIDA
python tools_validation_corpus.py run --out SALIDA [--seed 3000]
python tools_validation_corpus.py adjudicate --out SALIDA [--second anotacion_B.csv]
python tools_validation_corpus.py report --out SALIDA [--second anotacion_B.csv]
```

**Carpeta del corpus**, del custodio y fuera del repositorio:

```
VALIDATION_CORPUS_V1/
  manifest.json          sin datos personales
  development/           EM01_C01_es.docx …
  sealed/                EM02_C01_es.docx …
```

**Ejemplo de manifiesto:**

```json
{
  "corpus_version": "VALIDATION_CORPUS_V1",
  "cases": {"C01": "asthma_24f", "C02": "pneumonia_46f", "C03": "gi_bleed_57m",
            "C04": "anaphylaxis_29f", "C05": "renal_colic_34m", "C06": "trauma_limb_hemorrhage_27m"},
  "documents": [
    {"file": "EM01_C01_es.docx", "participant": "EM01", "case": "C01", "language": "es",
     "collected_on": "2026-10-12", "subset": "development"}
  ],
  "retired_entries": [
    {"entry_id": "EM02-C01-es-b1-e03", "on": "2026-11-02", "reason": "usada para corregir el lector (clase X)"}
  ]
}
```

**Controles de la ingesta:**

- **Manifiesto:**
  - participantes con código `EM` y dígitos;
  - casos declarados;
  - idiomas `es` o `en`;
  - **todos los documentos de un participante en un mismo subconjunto**.
- **Documento:** el código, el caso y el idioma escritos en el documento deben
  coincidir con el manifiesto.
- **Salida:** la misma entrada da el mismo `entries.json`, porque nada depende
  del reloj.

**Tiempo.** Cada documento tarda 15–40 s. En la prueba sintética, dos
documentos y ocho entradas tomaron 35 s en total.

**Limitaciones:**

- **Estado del motor.** El motor avanza con lo que ejecutó. Una entrada que
  depende del contexto («súbala a 0,2») se lee en el estado que dejaron las
  entradas anteriores, no en el de una evolución narrada. La anotación la
  marca con `context_dependent`.
- **Todo pasa por el cuadro de órdenes.** Las preguntas de historia y el examen
  escritos en texto libre también entran por ahí, porque el médico no eligió
  modo. Se informan aparte (`information_only_entries` y la tasa de aclaración
  «solo órdenes»); la Fase 2 medirá la elección de modo.
- **Retenciones completadas por el harness.** Las órdenes que siguen a una
  retención completada por el harness corren con respuestas neutras. Esas
  respuestas nunca cuentan como razonamiento del médico.
- **Vista del monitor.** El documento no muestra el trazado del monitor. Los
  casos donde la conducta inicial depende del ritmo (bradicardias) quedan fuera
  del piloto.

## 4. Piloto propuesto (§96)

Optimizado para **bajo costo humano, variabilidad útil e independencia del
desarrollo**.

**Médicos.** Seis médicos de urgencia en español (EM01–EM06), en tres pares.
Opcionalmente, 2–4 médicos que escriban **naturalmente en inglés** (EM07–EM10),
en pares, con los mismos casos. Si no hay, el inglés se posterga y **no se
afirma paridad** (§65).

**Casos.** Seis, propuestos y no decididos:

| Código | Caso del banco |
|---|---|
| C01 | asma grave |
| C02 | neumonía con hipotensión |
| C03 | HDA con shock |
| C04 | anafilaxia |
| C05 | cólico renal, con alta y seguimiento |
| C06 | hemorragia de extremidad por trauma |

La familia trauma no existe en el corpus de ensayo.

**Asignación.** Cada médico recibe tres casos, unos 15–20 min por caso y
**45–60 min en total**:

| Par | Médicos | Casos |
|---|---|---|
| P1 | EM01, EM02 | C01, C02, C03 |
| P2 | EM03, EM04 | C04, C05, C06 |
| P3 | EM05, EM06 | C01, C03, C05 |

**Volumen.** 18 documentos en español (+6 en inglés por cada par inglés).
Se esperan unas 8–15 entradas por documento, es decir **~150–270 entradas en
español**.

**Development y sealed, por médico y dentro de cada par.**

- **Cuándo:** con todos los documentos devueltos y **antes de que nadie los
  lea**.
- **Cómo:** el custodio sortea en cada par (una moneda) cuál médico va a
  development y cuál a sealed, y anota el sorteo en el manifiesto.
- **Resultado:** 9 documentos en cada lado, cada conjunto de casos en ambos.
  El estilo de un médico nunca cruza el límite.
- **Por qué 50/50 por médico y no por entrada:** las entradas de un mismo médico
  se parecen entre sí, y dividirlas filtraría su estilo al desarrollo. Con este
  n, 50/50 es lo mínimo para tener algo que validar. Si el piloto confirma el
  formato, las fases siguientes pueden sellar una proporción mayor.

**Cómo se envía.** Lo hace el docente; el AI Advisor no contacta a nadie (§97).

1. El custodio asigna los códigos y guarda la llave código ↔ persona **fuera del
   repositorio y sin compartirla**.
2. Escribe el código en cada documento (campo «Código de participante») o lo
   genera con `--participant EM01`. Nombra los archivos `EM01_C01_es.docx`.
3. Envía los tres archivos de cada médico por el canal que el docente elija.

**Qué devuelve el médico.** Los mismos tres archivos, escritos y con el mismo
nombre. No se pide nombre ni correo en el documento.

**Al recibir los documentos, el custodio:**

1. Elimina las propiedades con el nombre del autor (Word: *Archivo > Información
   > Inspeccionar documento*); la ingesta avisa si quedaron.
2. Revisa los avisos de correo o teléfono que la ingesta marca.
3. Hace el sorteo y ubica los archivos en `development/` o `sealed/`.
4. Completa el manifiesto.

**Cómo entran al pipeline.**

- **Development.** La carpeta puede quedar en el equipo del custodio o, si se
  quiere que el AI Advisor trabaje en ella, en `local-data/` (ignorada por git)
  de una sesión.
- **Sealed.** Queda en el equipo del custodio. Se corre solo cuando la versión
  candidata del lector está congelada, y la línea de comandos imprime solo
  agregados (§7).

**Costo humano estimado**, que el piloto mide:

- custodio: 1,5–2 h;
- anotación ciega: ~1 min por entrada, 3–4,5 h;
- doble anotación del 20 %: ~1 h de un segundo clínico;
- adjudicación: 30–45 s por entrada, ~1–1,5 h por subconjunto.

**Costo de IA: cero.**

**Qué responde el piloto (§64):**

| Pregunta | Cómo se responde |
|---|---|
| ¿Las instrucciones producen lenguaje natural? | Lectura docente de una muestra. |
| ¿El formato Word es práctico? | Documentos usables sin arreglos manuales y comentarios de los médicos. |
| ¿La extracción es reproducible? | Dos ingestas dan el mismo `entries.json` (sha256). |
| ¿El reference standard es construible? | Tiempo por entrada y acuerdo en el 20 % doble. |
| ¿Detecta errores nuevos? | Clases de error que el corpus de ensayo no tenía. |
| ¿La carga es razonable? | Horas por rol. |

## 5. Reference standard (§44, §67, §70)

**La anotación es ciega.**

- `ingest` escribe `annotation.csv` solo con el texto del médico y columnas
  vacías, sin nada del motor.
- Se anota **antes** de correr el motor; así no puede ocurrir «corpus revela
  falla → cambiar la respuesta esperada» (§95).
- La anotación **nunca** entra al motor.

**Intención clínica y redacción son cosas distintas (§67).**

- Se anota lo que el médico **quiso hacer** (`intended_items`), no cómo lo
  escribió.
- Dos redacciones distintas de la misma intención se anotan igual.
- La fidelidad textual se mide aparte, en el Management Trace (§6).

**Columnas.** Un Y/N vacío se lee como N; se acepta Y/S/Sí/N/No.

| Columna | Qué se anota |
|---|---|
| `intended_items` | Cada ítem que el médico quiso ordenar o pedir, separados por `;`, con etiqueta clínica, dosis, unidad, vía y momento tal como se entienden. Ejemplo: `MED: salbutamol 5 mg NBZ ahora; STUDY: gases venosos; REEVAL: FR y SpO₂ en 20 min`. Sin intención clínica (un «Plan:»): `—`. |
| `reassessment` | Escribió qué o cuándo reevaluar. Por decisión docente D1, el control después del alta cuenta como reevaluación. |
| `rationale` | Explicó por qué: hipótesis, prioridad o motivo. |
| `expectation` | Dijo qué espera que ocurra. |
| `contingency` | Dijo qué haría si la evolución no es la esperada. Las indicaciones de regreso al alta van en `disposition_followup`, por coherencia con DF-10 (**decisión docente pendiente**: VC-3). |
| `disposition_followup` | Destino, indicaciones al alta, control o signos de alarma. |
| `clinically_sufficient` | Un clínico podría ejecutarlo sin preguntar nada. **Obligatoria si hay ítems.** |
| `ambiguous` y `acceptable_readings` | Admite más de una lectura clínica razonable, y cuáles. |
| `context_dependent` | Solo tiene sentido con lo ocurrido antes («súbala»). |
| `annotator`, `annotation_version`, `note` | Código del anotador y versión (`VC1-ANNOTATION-1`). |

**Etiquetas de ítem.** Son palabras clínicas, no tipos del motor:

- `MED` medicamento;
- `FLUID` fluidos o hemoderivados;
- `O2` oxígeno, vía aérea o ventilación;
- `PROC` procedimiento;
- `STUDY` laboratorio, imagen, ECG o POCUS;
- `MON` monitorización;
- `CONSULT` interconsulta;
- `DISP` destino;
- `FOLLOWUP` indicaciones al alta o control;
- `REEVAL` reevaluación como acción;
- `HX` pregunta de historia;
- `EX` examen físico;
- `OTHER`.

**Doble anotación.**

- Un segundo clínico anota a ciegas el 20 % de las entradas.
- `agreement` informa el acuerdo por campo: cantidad de ítems, etiquetas,
  indicadores y suficiencia.
- Una discrepancia no resuelta propone `ANNOTATION_DISAGREEMENT`.

**Adjudicación.** `adjudicate` escribe `adjudication.csv`:

- **Contenido:** la anotación y el motor lado a lado.
  - Estado de ejecución y lectura del motor: acciones con sus parámetros,
    `ASKED:` y `CONDITIONAL PLAN:`.
  - Aclaraciones pedidas y retenciones de razonamiento.
  - Slots del Trace con procedencia `stated`.
  - Avisos automáticos: un slot que no cita al médico, una orden registrada
    como modelo de trabajo, razonamiento completado por el harness, una entrada
    sin Trace.
- **Qué llena el revisor:** `n_recognized`, `n_complete`, `n_partial` y
  `extra_or_wrong_execution`.
- **Propuesta:** la herramienta **propone** clase y locus con una regla
  determinista (`propose`).
- **Decisión:** el revisor puede escribir otra clase en `classification`; la
  suya es la que cuenta, y el reporte informa cuántas propuestas cambió.
- **Rehacer la hoja** conserva lo que el revisor ya escribió.

**Clases (§70).**

| Clase | Cuándo |
|---|---|
| CORRECT | Todos los ítems reconocidos y completos, sin ejecución extra ni errónea, sin aclaración innecesaria y con el razonamiento escrito capturado fielmente. |
| PARTIAL ENGINE ERROR | Algo reconocido, pero falta parte, un parámetro, una captura, o hubo una aclaración innecesaria. |
| ENGINE ERROR | Nada reconocido, o algo ejecutado que no se pidió o de forma errónea. |
| AMBIGUOUS INPUT | La entrada admite varias lecturas razonables y el motor no tomó una de ellas; no se fuerza una sola respuesta. |
| ANNOTATION DISAGREEMENT | Los anotadores discrepan y no se resolvió. |

**Locus:** `parsing`, `execution`, `reasoning_extraction`, `annotation` o
`ambiguous_human_input`.

## 6. Métricas (§68)

**Forma del reporte:**

- Por idioma, cuando hay n, y en total.
- Solo como conteos n/N y proporción, **sin intervalos ni pruebas**: con n de
  piloto dirían más de lo que los datos sostienen.
- Las entradas no anotadas o no adjudicadas se cuentan y quedan fuera de las
  tasas que las necesitan.

| Métrica | Definición |
|---|---|
| ORDER RECOGNITION RATE | ítems reconocidos / ítems anotados (adjudicado) |
| COMPLETE INTERPRETATION RATE | ítems completos (dosis, vía, momento, objeto, contexto) / ítems anotados |
| PARTIAL INTERPRETATION RATE | ítems parciales / ítems anotados |
| INCORRECT EXECUTION RATE | entradas con ejecución extra o errónea / entradas adjudicadas |
| UNNECESSARY CLARIFICATION RATE | entradas suficientes y no ambiguas en que el motor pidió aclaración / esas entradas. También sin las entradas solo de historia o examen. Las retenciones para pedir el razonamiento se informan aparte, porque piden razonamiento y no aclaran la orden. |
| TRACE FIDELITY RATE | slots `stated` que citan palabras del médico y no son una orden puesta como modelo / slots `stated` |
| MULTI-ORDER SUCCESS RATE | entradas con ≥ 2 ítems, todos reconocidos y sin ejecución errónea / entradas con ≥ 2 ítems |
| REASSESSMENT / RATIONALE / EXPECTATION / CONTINGENCY CAPTURE RATE | entradas anotadas con el elemento que el Trace capturó / entradas anotadas con el elemento; además, las capturas espurias |

**Qué cuenta como capturado:**

- **Reevaluación:** el slot `reassessment_target` declarado o una reevaluación
  programada con demora > 0, fuera de una retención completada por el harness.
- **Razón:** `problem_representation`, `rationale` o `management_priority`
  declarados.
- **Expectativa:** `expected_effect` declarado.
- **Contingencia:** `contingency` o `threshold` declarados, o un plan
  condicional registrado.

## 7. Trazabilidad, sellado, versiones y procedencia

**Trazabilidad (§69).** Cada entrada no clasificada CORRECT aparece en
`report.md` como:

- CASO
- → TEXTO LIBRE ORIGINAL
- → INTENCIÓN DE REFERENCIA
- → INTERPRETACIÓN DEL MOTOR
- → EJECUCIÓN
- → MANAGEMENT TRACE
- → CLASE
- → LOCUS

**Sealed (§45, §73).**

- **Custodia:** fuera del repositorio. La herramienta **rechaza** una ruta
  sellada dentro de este checkout, incluida `local-data/`.
- **Qué sale por consola:** solo agregados. Las entradas, la lectura del motor
  y la trazabilidad quedan en la carpeta de salida del custodio. El AI Advisor
  no la abre.
- **Contenido prohibido en el código:** el contenido sellado no se escribe en el
  código, en los tests ni en snapshots.
- **Cuándo se corre:** solo con la versión candidata congelada. El commit queda
  en el reporte.

**Retiro (§47, §74).**

- Una entrada sellada que se use para corregir el lector se anota en
  `retired_entries` con fecha y motivo.
- Queda como *RETIRED FROM VALIDATION / DEVELOPMENT* y sale de las métricas de
  validación.
- La evaluación siguiente usa datos no vistos.
- Una falla se corrige por clase, con tests de frases nuevas, nunca copiadas del
  corpus (§57).

**Versiones.**

- Corpus: `VALIDATION_CORPUS_V1`, con `DEVELOPMENT_SUBSET_V1` y
  `SEALED_SUBSET_V1`.
- Plantilla: `VC1-ES` / `VC1-EN`.
- Anotación: `VC1-ANNOTATION-1`.

**Procedencia (§48).** El reporte trae:

- versión del corpus y del subconjunto;
- tipo de fuente (`physician_free_text_docx`);
- idiomas, casos y fechas de recolección;
- versiones de plantilla y de anotación;
- motor (commit, cambios locales y versión);
- semilla y fecha de corrida;
- entradas retiradas.

## 8. Privacidad y minimización (§72)

- Un participante es un código. El documento pide no escribir datos personales.
- La herramienta no lee propiedades, comentarios ni autores de revisiones; de
  las propiedades solo avisa que traen un nombre.
- Marca correos y números con forma de teléfono para que el custodio los revise.
  **No altera el texto.**
- No se recolecta experiencia, edad ni idioma materno. Si más adelante se
  quiere estudiar alguna variable, se decide explícitamente cuál y por qué.

## 9. Decisiones necesarias

Están también en la cola de decisiones.

- **VC-1.** Aprobar o modificar el piloto:
  - número de médicos y casos;
  - pares y sorteo por par;
  - inglés sí o no.
- **VC-2.** ¿Quién anota y quién adjudica? Un clínico que no sea quien dirige
  las correcciones del lector.
- **VC-3.** ¿Las indicaciones de regreso al alta cuentan como contingencia o
  como seguimiento?
- **VC-4.** Confirmar la aprobación del texto en español de los seis casos y
  abrir un documento en Word antes de enviar.
