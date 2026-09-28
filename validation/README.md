# validation/

Sólo lo que se entrega a los médicos del validation corpus y lo que hace falta
para procesar sus respuestas. Este repositorio **nunca** guarda respuestas de
médicos: ni el subconjunto de desarrollo ni, sobre todo, el sellado (§73 del
ciclo 3, §42 del ciclo 4).

- **`pilot_v1/`.** El piloto aprobado el 2026-09-28 (DF-15): los 18 documentos
  listos para enviar, las instrucciones, la matriz de asignación, el
  procedimiento de sorteo, la anotación y los manifiestos. **Empiece por
  `pilot_v1/README.md`.**
- **Plantillas VC1 (`plantillas_v1/`) retiradas en el ciclo 4.** Las reemplaza
  la plantilla VC2, que tiene la instrucción breve del §13. Siguen en el
  historial de git, y la herramienta todavía lee documentos VC1.
- **Pruebas.** `test_pilot_package.py` verifica que los documentos sean
  exactamente lo que escribe el generador y que no contengan spoilers ni
  palabras internas. Si el texto de un caso cambia, la prueba falla y los
  documentos se regeneran (`pilot_v1/tools/README.md`).
