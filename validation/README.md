# validation/

Solo lo que se entrega a los médicos para la Fase 1 del validation corpus
(`docs/VALIDATION_CORPUS_FASE1.md`). Este repositorio **nunca** guarda
respuestas de médicos: ni el subconjunto de desarrollo ni, sobre todo, el
sellado (§73).

- **`plantillas_v1/`.** Los documentos en blanco de los seis casos propuestos
  para el piloto, en español y en inglés, tal como los escribe
  `python tools_validation_corpus.py templates`.
  - `templates.json` da, por documento, su sha256 y de dónde viene el texto del
    caso.
  - El código de participante se completa antes de enviar.
  - Hay que confirmar la aprobación docente del texto en español de cada caso
    antes de enviarlo.
- `test_validation_corpus.py` verifica que estos archivos sean exactamente lo
  que escribe el generador. Si el texto de un caso cambia, el test falla y los
  documentos se regeneran.
