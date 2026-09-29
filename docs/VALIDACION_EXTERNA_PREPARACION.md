# Validación externa · preparación de la ingesta (ciclo 9)

Ciclo 9 del AI Advisor · 2026-09-29. **Ninguna respuesta de un médico se abrió, se leyó ni se procesó para
preparar esto.** Todo se probó con las plantillas en blanco del piloto y con frases que las pruebas ya usaban
(`test_external_ingestion_readiness.py`, `test_validation_readiness.py`).

Este es el documento de referencia del tema. El procedimiento del sorteo sigue en
`validation/pilot_v1/SPLIT_PROCEDURE.md`, la anotación en `validation/pilot_v1/annotation/`, y el diseño original
en `docs/VALIDATION_CORPUS_FASE1.md`.

## 1. Dos corpus, nunca uno

| | Español | Inglés |
|---|---|---|
| Corpus | `VALIDATION_CORPUS_V1` | `VALIDATION_CORPUS_V1_EN` |
| Manifiesto del piloto | `validation/pilot_v1/manifests/pilot_manifest.json` | `validation/pilot_v1_en/manifests/pilot_manifest.json` |
| Participantes | EM01–EM06 | EM07–EM12 |
| Baseline del motor | SPANISH PILOT BASELINE `939978a` (fijo) | por elegir **antes** de leer respuestas; recomendado: **V3** (ver `validation/BASELINES.md`) |
| Sorteo, anotación, corrida, métricas | propios | propios |

- El mismo caso (C01…C06) puede aparecer en los dos corpus: el código del participante, el corpus y el idioma los
  distinguen, y no se cruzan.
- Cada manifiesto declara su idioma; las herramientas rechazan un corpus que mezcle idiomas
  (`corpus_language`). Una traducción nunca es dato primario de validación.
- La comparación entre idiomas es descriptiva y debe decir en primer lugar si los dos motores eran distintos.

## 2. Dónde guardar los documentos

**Recomendación práctica.** Fuera de este repositorio y de cualquier carpeta sincronizada con él, en una carpeta
institucional de acceso restringido (una unidad cifrada o un espacio de la universidad con acceso sólo del
custodio y de quien anota), con esta forma por idioma:

```
VALIDACION_EXTERNA/
  ES/
    raw/        los .docx tal como llegaron; sólo lectura; nunca se editan
    admin/      raw_manifest.json, readiness.json y .md, decisions.json
    working/    copias de trabajo (propiedades limpias); lo que entra al sorteo
    corpus/     manifest.json, split.json, development/, sealed/
    out_dev/    entries.json, hojas de anotación, engine_output.json, informe
    out_sealed/ lo mismo para sellado, sólo al final, una vez
  EN/
    (igual)
```

- `raw/` en sólo lectura una vez copiado (por ejemplo, `chmod -R a-w raw`), con una copia de respaldo en otro
  medio controlado.
- `sealed/` y `out_sealed/` nunca dentro del repositorio: las herramientas lo impiden (`check_outside`).
  `development` puede vivir en `local-data/` (ignorado por git), pero la recomendación es la misma carpeta externa.
- El repositorio guarda sólo herramientas, plantillas, manifiestos de planificación e instrucciones; **nunca** una
  respuesta real.

### Cómo entregarlos

1. **Nada entra al repositorio.** Los `.docx` devueltos van a `VALIDACION_EXTERNA/ES/raw/` o `EN/raw/`, fuera del
   repositorio, tal como llegaron (sin abrirlos ni renombrarlos; si un nombre no sigue `EM01_C01_es.docx`, el
   inventario lo marca y una persona decide).
2. **Un idioma por vez, cada uno completo o con una nota de lo que falta.** Español e inglés nunca en la misma
   carpeta.
3. **La frase que abre el trabajo:** «BEGIN EXTERNAL VALIDATION INGESTION», con el idioma y la ruta de la carpeta
   `raw/` (y, para el inglés, el baseline elegido). Sin esa frase, el AI Advisor no abre, no lista por contenido ni
   usa ningún documento, aunque aparezca en una carpeta: informa su presencia y se detiene.
4. **Si el entorno de trabajo es un contenedor en la nube,** la carpeta debe estar disponible dentro del contenedor
   y fuera del repositorio (por ejemplo, subida a una ruta de trabajo aparte); el repositorio sigue sin guardarla.

## 3. Del archivo devuelto al corpus congelado

Los comandos son de `tools_validation_corpus.py`; ninguno lee el contenido clínico para decidir nada.

1. **Inventario RAW** (checksum, propiedades, estructura, problemas; nunca altera un archivo):
   `inventory --pilot PILOTO.json --raw ES/raw --received-on AAAA-MM-DD --out ES/admin`
2. **Revisión del informe de preparación** (`ES/admin/readiness.md`): esperados, recibidos, faltantes,
   duplicados, conflictos, vacíos, parciales, códigos o idioma equivocados, propiedades por limpiar y lo que una
   persona debe mirar (comentarios, cambios con control).
3. **Decisiones de una persona**, con su razón, en `ES/admin/decisions.json`, y un nuevo inventario con
   `--decisions`. Decisiones posibles: `KEEP`, `EXCLUDED`, `WITHDRAWN`, `INVALID`. Nada se elige, se excluye ni se
   reemplaza solo; nunca «el más reciente».
4. **Copias de trabajo:** `deidentify --raw ES/raw/X.docx --out ES/working/X.docx` para cada documento con
   propiedades personales; los demás se copian tal cual. El texto queda byte a byte igual al del archivo RAW.
5. **Congelar la versión del corpus y sortear** (development/sealed por participante, una vez):
   `split --pilot PILOTO.json --returned ES/working --baseline SHA --corpus ES/corpus --collected-on AAAA-MM-DD`
6. **Ingesta de development:** `ingest --corpus ES/corpus --subset development --out ES/out_dev`
7. Anotación a ciegas, corrida del motor en su baseline, adjudicación, informe (§6 y §7).

## 4. Lo que registra el inventario

`raw_manifest.json` (versión `RAW-INVENTORY-1`), un registro por archivo:

| Campo pedido | Clave |
|---|---|
| CORPUS | `corpus_version`, `pilot_id`, `language` |
| PARTICIPANT CODE · CASE ID · LANGUAGE | `participant`, `case`, `file_language` (del nombre, nunca del texto) |
| ORIGINAL FILENAME | `original_filename` |
| SHA-256 | `sha256` (del archivo RAW) |
| INGESTION DATE | `ingestion_date` (la fecha dada al tomar el inventario) |
| RAW / WORKING STATUS | `raw_status` (`RAW`), `working_status` (`WORKING_COPY_NEEDED`, `RAW_IS_WORKING`) |
| METADATA REVIEW STATUS | `metadata_review_status` (`NO_PERSONAL_PROPERTIES`, `WORKING_COPY_NEEDED`, `HUMAN_REVIEW`) |
| Problemas | `problems`, `duplicate_of`, `conflicts_with`, `decision` |

- **Sin nombres.** Las propiedades se informan por nombre (`creator`, `lastModifiedBy`, `Company`, `Manager`,
  `title`, `subject`, `description`, `keywords`, `category`, propiedades personalizadas), nunca por valor. Los
  comentarios y los cambios con control se cuentan y se señalan si nombran a su autor; su texto no se lee.
- **Un inventario no se reescribe.** Si llegan documentos nuevos o corregidos después de congelar, se toma otro
  inventario en otra carpeta y se registra como enmienda (V1.1): la versión congelada no cambia en silencio.
- **Retiro o documento inválido** (§97): se registra la decisión (`WITHDRAWN`, `INVALID`, `EXCLUDED`) con su razón;
  un retiro después del sorteo se registra además en `retired_entries` del manifiesto del corpus, que ya lo
  soporta (la entrada sale de las métricas y dice por qué).

## 5. La respuesta del médico, tal como la escribió

- **La frontera.** Sólo se leen las cajas «Su manejo / Your management»: cada párrafo no vacío es una entrada.
  La viñeta, las instrucciones, el monitor, la ficha y el texto de las evoluciones son de la plantilla y nunca
  son entradas; lo escrito fuera de las cajas se informa y no se lee como entrada (`read_document`).
- **Se conserva:** ortografía, abreviaturas, puntuación, mayúsculas, comas decimales, acentos, tabulaciones y los
  saltos de línea dentro de un párrafo. No se corrige, no se expanden abreviaturas, no se traduce, no se normaliza
  el lenguaje médico.
- **Diferencias técnicas documentadas (no cambian el contenido):** el espacio duro pasa a espacio común; las
  líneas en blanco repetidas dentro de un párrafo quedan en una; se quitan los espacios al inicio y al final de
  cada línea; se toma el texto visible de los cambios con control (lo insertado sí, lo borrado no); el texto de un
  cuadro de texto no se lee y se avisa.
- **Vacío, parcial, estructura inesperada:** se señalan en el inventario (`EMPTY`, `PARTIAL`,
  `UNEXPECTED_STRUCTURE`) y bloquean el sorteo hasta que una persona decida.
- **Datos personales dentro del texto clínico** (un correo, un teléfono): se señalan en la ingesta y **no** se
  borran; una persona decide.

## 6. La anotación de referencia

- **La unidad** es la entrada (un párrafo) con sus ítems `TIPO: qué`, que llevan dosis, vía, parámetros y momento
  tal como se escribieron, más las marcas S/N (`validation/pilot_v1/annotation/annotation_guide.md`). Cómo cubre lo
  pedido, sin etiquetas nuevas:

| Pedido | En la hoja |
|---|---|
| INPUT TEXT SEGMENT | `entry_id`, `text` |
| INTENDED ACTION / PLAN / REASONING | `intended_items`, `rationale`, `expectation` |
| EXECUTE NOW? | el momento escrito en el ítem («ahora», «en 2 horas») |
| CONDITIONAL? | la condición en el ítem y `contingency: S` |
| PRIOR / HISTORICAL? | `HX: recibió …` (aclaración del ciclo 9) |
| NOT MODELED? | se anota la intención igual; si el simulador la modela lo dice el motor, no la hoja |
| DOSE · ROUTE · TIMING | dentro del ítem, como se escribieron |
| REASSESSMENT | `REEVAL: …` y `reassessment: S` |
| DISPOSITION | `DISP: …` (ahora o planificado, con su momento) |

- **A ciegas y antes del motor.** Primero «¿qué quiso hacer o decir el médico?»; después se compara con el motor.
- **La corrección clínica no es la etiqueta:** una orden discutible pero clara se anota como está escrita.
- **La ambigüedad se preserva:** `ambiguous: S` con `acceptable_readings`; no se obliga a una sola intención.
- **Procedencia** (§98): `annotation_provenance.json`, junto a las hojas: código del anotador, fecha, si anotó sin
  ver el motor, si es la segunda anotación; código del revisor y fecha de la adjudicación. Nunca nombres.
- **Doble anotación del 20 %:** una quinta parte fija de cada documento, elegida por el SHA-256 del identificador
  antes de que nadie la lea (`double_annotation_sample`); nunca «las difíciles».
- **Adjudicación:** las dos anotaciones quedan como se hicieron; el desacuerdo se marca y la referencia final se
  escribe en la hoja de adjudicación. El acuerdo entre anotadores se podrá calcular después con esos datos
  (`agreement`); no se eligió todavía una estadística.
- **La IA no crea la referencia.** Puede ayudar después a comparar o resumir, cuando se autorice, nunca a anotar.

## 7. Lo que medirá el informe

- **Por idioma, nunca combinado.** Un corpus es un idioma; el informe no muestra «todos los idiomas» cuando hay uno.
- **Procedencia de cada corrida (§132):** identificador del corpus (el piloto), versión, subconjunto, semilla y
  baseline del sorteo, commit del motor, si tenía cambios sin guardar, su configuración (`MRS_*`, sin secretos),
  semilla, fecha, idioma, baseline registrado y las listas de defectos conocidos vigentes al analizar (la del piloto,
  versión 2, y el estado de V3, versión 3) (`_provenance`, `baseline_of`). La misma corrida sobre el mismo corpus,
  el mismo commit y la misma configuración da lo mismo.
- **Taxonomía.** Cinco clases excluyentes (`CORRECT`, `PARTIAL_ENGINE_ERROR`, `ENGINE_ERROR`, `AMBIGUOUS_INPUT`,
  `ANNOTATION_DISAGREEMENT`) y, **contadas aparte** para que ninguna se esconda en una clase: `SILENT_LOSS`
  (intención clara perdida sin pregunta), `FALSE_EXECUTION` (se ejecutó lo que no se pidió), `TRACE_DISTORTION` (el
  registro dice lo que el médico no expresó) y `APPROPRIATE_CLARIFICATION` (preguntó ante lo ambiguo o
  insuficiente). La aclaración innecesaria ya tenía su tasa. Una entrada puede llevar varias marcas.
- **Denominadores de la metodología existente:** ítems intencionados, entradas anotadas y adjudicadas.
- **Defecto conocido:** el revisor lo etiqueta por su identificador, de la lista del piloto o del estado de V3
  (`validation/KNOWN_DEFECTS_V3.md`). En una corrida de `939978a`, un error de la clase de TD-39, TD-34 o TD-36 se
  etiqueta así: *known at time of analysis but present in frozen baseline* (§67). La etiqueta da contexto; el error
  sigue en las métricas y nada se corrige hacia atrás.
- **Ninguna cifra sola.** Qué falló, cuántas veces, cuán importante, si afectó la ejecución, el Trace o la
  jugabilidad; por caso (qué depende del contexto clínico) y por participante sólo como variabilidad de estilo,
  **nunca** un ranking ni un puntaje de médicos.
- **Ejemplos de error:** el fragmento mínimo, con el código del participante; nunca respuestas completas en
  documentos públicos. Para una prueba de regresión, una reproducción mínima desidentificada; el original queda en
  el corpus protegido.

### Plantilla del informe externo (sin números)

1. ¿Cuántas respuestas de médicos? 2. ¿Cuántas acciones o unidades intencionadas? 3. ¿Con qué frecuencia el motor
las entendió? 4. ¿Con qué frecuencia aclaró bien? 5. ¿Cuántas pérdidas silenciosas? 6. ¿Cuántas ejecuciones
falsas? 7. ¿Cuántas distorsiones del Trace? 8. ¿Qué clases de error aparecieron? 9. ¿Cuáles eran defectos conocidos
del baseline? 10. ¿Cuáles son nuevos? 11. ¿Cuáles importan clínicamente? 12. ¿Mostraron el español y el inglés
patrones distintos? (Si los motores eran distintos, dicho primero.)

Y la descripción de la muestra: número de médicos, de respuestas, idioma, asignación de casos y forma de
reclutamiento, sin identificar a nadie y sin inferir representatividad.

## 8. Development y sealed

- **Development** sirve para el análisis de errores, los arreglos aprobados y la iteración, **después** de la
  medición del baseline: anotación → corrida del baseline → adjudicación → informe → análisis de errores.
- **Sealed** no sirve para diseñar reglas, prompts ni el lector, ni se inspecciona durante el desarrollo. Se corre
  **una vez** sobre un candidato congelado y responde una pregunta: ¿las mejoras generalizaron al lenguaje de médicos
  que no se usó para desarrollar? Si hace falta otra ronda, hace falta otro corpus.
- **Salvaguardas contra la fuga de sealed:** las carpetas sealed fuera del repositorio (`check_outside`); la línea de
  comandos imprime sólo agregados de una corrida sealed; los registros y salidas quedan en la carpeta del custodio;
  nada de sealed entra en pruebas, fixtures, capturas, documentos ni prompts de desarrollo.
- **Arreglo derivado de development** (cuando se autorice): ejemplo original como evidencia fuera de las pruebas
  públicas → reproducción mínima desidentificada → clase o causa raíz → arreglo por clase → ejemplos independientes y
  controles negativos → development → comparación con el baseline congelado → candidato congelado → sealed una vez.
  Un error que aparece en un solo idioma no se generaliza solo al otro, pero siempre se prueba la regresión cruzada.
- **Prioridad** (cualitativa, sin puntaje): frecuencia (ocurrencias, participantes, casos, idioma), importancia
  clínica, efecto en el Trace y en la jugabilidad, reproducibilidad y riesgo del arreglo. La severidad es el impacto,
  no la dificultad del arreglo. Un error raro y ambiguo puede quedar como aclaración apropiada o limitación aceptada.

## 9. Qué no se afirma

- Los resultados de los ciclos 7 y 8 son **datos sintéticos internos de desarrollo**, nunca validación externa.
- Un primer corpus pequeño detecta modos de falla reales y estima su frecuencia **en esa muestra**; no mide un
  rendimiento poblacional ni una robustez universal del lenguaje.
- Validar el lector valida la **fidelidad del lenguaje y del Trace** del motor, no el instrumento de evaluación, la
  rúbrica, las inferencias longitudinales ni la comparabilidad entre programas: cada una requiere su propio estudio.
- Formulación preferida: «El simulador registra evidencia observacional estructurada del razonamiento de manejo en
  encuentros simulados, con confirmación docente». No «demuestra competencia» ni «mide competencia».
