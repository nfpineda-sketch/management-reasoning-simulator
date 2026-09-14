# v0.19.0 — Equivalencia funcional del encuentro generado

Comparación de referencia: `main` en `65336abcdab323bac0f2fb3ebff4cbb15c3a775b`,
`ai-integration-v0.9.0` en `d7835936de393e1b1e46c2dea656acb1f6390535` y desarrollo
v0.18.0 en `c2e2629c69e703f03331905c17d9ab9d1d1f0c12`.
Destino exclusivo: `clinical-encounter-v0.13`.

## Matriz de equivalencia y evidencia

| Conducta recuperada de main / IA | Implementación en casos generados | Evidencia automática |
| --- | --- | --- |
| Texto libre bilingüe, dosis, vías, O2, abreviaturas y órdenes compuestas | Primitivas compartidas; adaptador de órdenes; normalización IA existente; validación atómica | `test_free_text_orders.py`, `test_shared_encounter_management.py`, `test_family_parser.py` |
| `parse_contextual_followup`: repetir bolo o fármaco | Historial de órdenes comprometidas; selección por tratamiento; conservación de dosis, vía y duración; cantidades nuevas explícitas | `test_functional_equivalence.py`: repetición de fluidos/fármacos, negación, ambigüedad y repetición de estudios |
| Conversación para completar indicaciones | Dosis/vía y dispositivo/flujo; tasas y unidades; NIV e intubación; varias aclaraciones conservan el resto del conjunto pendiente | `test_functional_equivalence.py`: O2, norepinefrina, nitroglicerina, BiPAP |
| Administración y entrega acumulada separadas | Cola temporal de fluidos, sangre y fármacos de dosis fija con duración explícita; registro de dosis ordenada y realmente entregada | `test_functional_equivalence.py`: fluido en 20 minutos, amiodarona en 10 minutos y migración de sesión anterior |
| Reevaluación independiente | El intervalo solicitado gobierna el reloj aunque queden estudios pendientes; resultados conservan el momento de toma | `test_functional_equivalence.py`: laboratorio pendiente tras reevaluación al minuto |
| Continuidad y titulación de soporte | O2, NIV, ventilación, norepinefrina y nitroglicerina ya trasladados en v0.18; dobutamina añadida con tasa/unidades propias | `test_shared_encounter_management.py`, `test_functional_equivalence.py`: iniciar, aumentar, continuar y detener dobutamina |
| `procedural_sedation_transition`: efecto transitorio | Inicio, intensidad, umbral de sedación y recuperación declarados por caso; recuperación del estado basal o de la evolución subyacente; conservación de hallazgos focales | `test_functional_equivalence.py`: sedación, recuperación, segunda dosis y examen neurológico |
| `ventilator_adjustment_transition`: ajustes intermedios | Interpolación dentro de una malla FiO2/PEEP explícita, coherente y propia del paciente; conservación de parámetros no modificados | `test_functional_equivalence.py`: interpolación y rechazo atómico fuera de rango |
| `pocus_transition`: estudio dependiente de evolución | Actualizaciones narrativas condicionadas por fisiología, tiempo o volumen entregado; nueva adquisición conserva estudios anteriores | `test_functional_equivalence.py`: cambio de IVC/pulmón tras fluidos y conservación de historia |
| Registro docente de lo ejecutado | Cantidades, duración y administración parcial disponibles en análisis y trazas | `test_faculty_analysis.py`, `test_management_trace_analysis.py` |
| Aplicación transversal a casos nuevos | Contrato de generación exige cobertura de manejo, recuperación de sedación, malla ventilatoria cuando se incluye intubación y POCUS dinámico o explícitamente estable | `test_generated_case.py`, `test_generated_case_capabilities.py` |

## Alcance preciso

La equivalencia es de las conductas de manejo enumeradas, no identidad numérica
con el paciente fijo PS001. Las curvas antiguas de cardioversión, sedación,
ventilación y sobrecarga de fluidos dependen de ese paciente y no se copian como
reglas universales. Cada caso declara sus respuestas, intervalos y límites.
Las intervenciones sin respuesta declarada siguen identificándose como una
limitación del caso, sin afirmar que la indicación no se entendió ni ejecutar
parcialmente el resto de la orden.

Se conservan las especificaciones de casos previamente generados. Los nuevos
requisitos de cobertura se aplican al generar un caso nuevo en v0.19.0; abrir
una sesión antigua no inventa curvas que su especificación no contenía. Las
sesiones con fluidos pendientes conservan sus volúmenes al adoptar la nueva cola.
La interfaz muestra los estudios pendientes sin revelar sus resultados antes
de la disponibilidad. El motor sigue usando pasos de un minuto.

La ventilación no extrapola fuera de la malla del caso. La duración explícita
se admite para dosis fijas, fluidos y sangre; no equivale a un motor universal
de farmacocinética ni añade automáticamente infusiones no modeladas.

## Verificación de la entrega

- 251 pruebas focalizadas del motor, generación, cobertura, recarga, análisis docente y equivalencia funcional.
- 155 pruebas de texto libre, parser, repetición contextual y manejo compartido en la última pasada de integración.
- Siete regresiones históricas: `regression_v088_fluid_oxygen_quantity_scope.py`, `regression_v090_ai_interpreter.py`, `regression_v076_treatment_continuity.py`, `regression_v078_state_aware_respiratory.py`, `regression_v0815_executable_procedural_sedation.py`, `regression_v0818_reassessment_checkpoint_and_fluid_trajectory.py`, `regression_v0810_flexible_reasoning_completion.py`.
- Contratos y ejecución comprobados con casos de prueba locales; no se consumieron llamadas de generación IA para esta validación.

La revisión general ejecutó 1178 pruebas y 180 subpruebas (sin el archivo de
interfaz ejecutado por separado). Detectó una aserción antigua de texto en
`test_family_appearance.py`, ya presente antes de esta entrega: esperaba una
frase sustituida por el contrato de observaciones estáticas. Se actualizó para
comprobar el contrato vigente y conservar la comprobación de esfuerzo respiratorio
reducido; no se cambió el generador ni el revisor de imágenes.

La pasada posterior del archivo visual corregido, la interfaz y la equivalencia
funcional aprobó sus 53 pruebas.
