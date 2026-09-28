# Readiness del piloto de validación v1 (ciclo 5)

Autorización docente del 2026-09-28 (§26, §47).

**Estado: PILOT TOOLING READY**, con documentos sintéticos.

- **Nada se corrió sobre respuestas reales**: no hay ninguna.
- **No se inventó ninguna respuesta clínica.** La prueba de punta a punta usa
  las plantillas del piloto, llenadas con frases que las pruebas ya usaban, y
  una anotación de prueba.
- **No se afirma ningún resultado.**

**THE PHYSICIANS ARE NOT BEING ASSESSED.** Se evalúa el motor: si entendió,
ejecutó y registró bien lo que el médico escribió.

## Los diez criterios

La prueba de punta a punta es
`test_validation_readiness.py::test_from_the_returned_documents_to_the_report`:
split → ingest → hojas → corrida por la página real → adjudicación → reporte.

| # | Criterio | Estado | Dónde se prueba |
|---|---|---|---|
| 1 | El sorteo es reproducible | **LISTO**: mismo sorteo con los mismos bytes; nunca se sortea dos veces sobre archivos distintos | punta a punta; `test_validation_corpus.py` (sorteo) |
| 2 | SEALED queda fuera del repositorio | **LISTO**: `check_outside` rechaza un sealed dentro del checkout, también en `local-data/` | punta a punta; `test_the_sealed_subset_stays_outside_the_repository` |
| 3 | La ingesta conserva el texto y el orden | **LISTO**: cada párrafo es una entrada, en el orden escrito, con identificador estable | punta a punta; `test_ingest_gives_stable_identifiers_and_provenance` |
| 4 | Archivos de anotación | **LISTO**: `annotation.csv` ciega, sin columnas del motor, y `annotation_second.csv` | punta a punta; `test_the_annotation_sheet_is_blind` |
| 5 | Segunda anotación reproducible | **LISTO**: un quinto de cada documento, al menos una entrada, elegido por SHA-256 | punta a punta; `test_a_fifth_of_each_document_goes_to_the_second_annotator` |
| 6 | La corrida usa el pipeline real | **LISTO**: la página real, sin modelo (0 llamadas de IA) y sin entradas perdidas | punta a punta; `test_each_entry_is_read_by_the_real_page…` |
| 7 | La adjudicación conserva el desacuerdo | **LISTO**: ANNOTATION_DISAGREEMENT exactamente en las entradas donde los anotadores difieren; lo que el revisor ya escribió se conserva | punta a punta |
| 8 | El reporte distingue las cinco clases | **LISTO**: CORRECT, PARTIAL_ENGINE_ERROR, ENGINE_ERROR, AMBIGUOUS_INPUT, ANNOTATION_DISAGREEMENT | punta a punta; `test_the_proposed_class_follows_the_reviewers_counts` |
| 9 | Los defectos conocidos se pueden etiquetar | **LISTO**: la etiqueta llega a la trazabilidad. **Nuevo en el ciclo 5:** una etiqueta que no está en la lista se rechaza | punta a punta; `test_impact_and_known_defect_order_the_work_and_are_checked` |
| 10 | El baseline queda registrado | **LISTO**: el reporte registra el commit, los cambios sin guardar, `engine_baseline` y `known_defects_version` | punta a punta; `test_validation_baselines.py` |

## Lo que la readiness no cubre

- **La verificación visual en Word** de los 18 documentos. Queda para el
  docente (`README.md`, punto 5).
- **El reclutamiento, el envío y la llave código ↔ persona.** Son del docente;
  nada se contactó ni se envió.
- **La anotación clínica real y su acuerdo.** Los hacen clínicos; la IA no
  hace de estándar de referencia.

## Cuando vuelvan los documentos

La secuencia está en `README.md`, punto 6:

**RETURNED DOCX → STORE UNOPENED → SPLIT → DEVELOPMENT / SEALED → BLINDED
REFERENCE ANNOTATION → DEVELOPMENT RUN → ADJUDICATION → ERROR ANALYSIS.**

SEALED no se corre durante el ciclo de desarrollo.
