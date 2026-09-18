# Piloto curricular: encuentros asignados y variantes de PS001

Este incremento convierte tres desafíos de la matriz curricular en encuentros ejecutables con asignación interna. El residente recibe una presentación clínica neutral, explica sus decisiones y observa la evolución. El objetivo específico se muestra después de terminar el encuentro, durante la revisión. El docente puede elegir cualquiera de los tres desafíos en su espacio de prueba.

La matriz de **30 desafíos —10 por año— es una propuesta de desarrollo**. Este piloto implementa **tres desafíos de una sola familia clínica, PS001**. No ofrece todavía 30 familias clínicas ni cobertura completa de los conocimientos y competencias de Medicina de Urgencia.

## Los tres desafíos implementados

La siguiente correspondencia es un diseño educativo local basado en los documentos aportados. Los identificadores R1/R2 organizan la propuesta del programa; no son equivalencias oficiales de niveles ACGME ni de etapas del Royal College.

| ID interno y etapa local | Desafío | Evidencia que interesa revisar con el docente | Referencias curriculares |
| --- | --- | --- | --- |
| R1-03 · primer año | Relacionar la taquicardia con el estado del paciente | Explicar una hipótesis causal con hallazgos; vincular la prioridad con esa hipótesis; anticipar cambios en perfusión además del ritmo; comparar la respuesta observada. | ACGME PC4, PC5, MK2; Royal College Medical Expert 2.2 y 2.4. |
| R1-04 · primer año | Anticipar y comprobar el efecto de una intervención | Formular una expectativa verificable; elegir variables y un momento de reevaluación; distinguir la orden de su ejecución; comparar lo observado con lo esperado. | ACGME PC1 y PC6; Royal College Medical Expert 2.4 y 4.1. |
| R2-01 · segundo año | Separar presión, flujo y perfusión en un deterioro mixto | Integrar varios datos circulatorios; proponer un mecanismo y una acción dirigida; revisar el mecanismo y la prioridad según la respuesta. | ACGME PC1, PC4, MK1, MK2; Royal College Medical Expert 1.6 y 2.4. |

R1-03 presupone interpretación básica del ritmo y la perfusión. R1-04 presupone conocimiento del mecanismo y la temporalidad de la intervención elegida. Para R2-01, la matriz propone R1-01 y R1-03 o evidencia docente equivalente. Como R1-01 no está implementado, el programa debe revisar esos conocimientos al asignar el año; este piloto no verifica automáticamente esos prerrequisitos.

## Asignación y evidencia

El administrador asigna el año del residente. Primer año dispone de R1-03 y R1-04; segundo y tercer año disponen de esos dos desafíos y R2-01. No hay aún desafíos exclusivos de tercer año. Terminar casos no cambia el año ni acredita competencia.

La asignación da primero exposición a cada desafío disponible. Después revisa el último encuentro completado de cada desafío, cuenta qué tipos de evidencia explícita faltan y prioriza esos vacíos. Alterna respecto del último desafío completado cuando hay otra opción. La semilla de asignación se conserva para poder explicar la elección.

Solo los encuentros con revisión completada contribuyen a esa selección. Los encuentros activos, abandonados y las pruebas docentes quedan excluidos. Un buen o mal desenlace del paciente no se utiliza como sustituto de razonamiento, ni como aprobación o reprobación automática.

El resumen de evidencia registra presencia de una hipótesis, prioridad o expectativa escrita; una reevaluación interpretada como acción; y respuestas completas a los cuatro campos de reflexión. Las referencias numéricas corresponden a los ordinales de decisión mostrados en **Management Trace**, no a las posiciones brutas de todos los mensajes. Los mensajes que solo requieren aclaración no constituyen una decisión ejecutada. La ausencia de registro puede reflejar una limitación del reconocimiento del lenguaje, por lo que necesita revisión humana.

La presencia de un texto no demuestra que sea correcto, pertinente o suficientemente elaborado. El sistema no asigna un nivel de Milestones, una decisión de confianza profesional ni una calificación de dominio. El docente revisa el contenido, el contexto de las decisiones y la trayectoria antes de emitir una valoración formativa.

## Qué genera la IA en este incremento

La IA compone un encuentro seleccionando identificadores de un conjunto limitado: un perfil fisiológico y opciones de presentación en inglés. La aplicación transforma esas opciones en una presentación y un estado inicial. El modelo no puede introducir valores fisiológicos, tratamientos, dosis, nuevos diagnósticos o narración clínica libre.

| Perfil interno | Variación persistente en el motor | Lo que permite explorar |
| --- | --- | --- |
| `volume_limited` | Menor volumen efectivo, con inflamación y reserva contráctil inicial conservada. | Relación entre ritmo, volumen efectivo y respuesta a las intervenciones. |
| `rhythm_contributor` | Mayor contribución atribuida al ritmo, diferente volumen efectivo y mayor reserva cardiovascular inicial. | Una respuesta distinta a la corrección del ritmo, con enfermedad sistémica residual. |
| `mixed_low_flow` | Menor reserva contráctil y función cardíaca, mayor llenado inicial y menor respuesta al aumento de precarga. | Discordancia entre presión, flujo y signos de perfusión durante la evolución. |

Los tres perfiles conservan un hombre de 70 años con hipertensión, diabetes tipo 2, fibrilación auricular y un foco urinario. Mantener estos hechos evita contradicciones con la historia dirigida y los estudios que ya ejecuta PS001. El foco infeccioso no se anuncia en la presentación: aparece cuando el residente obtiene información pertinente. La IA cambia la composición del encuentro y algunos determinantes reales de su evolución, pero aún no crea enfermedades o historias enteramente nuevas.

La especificación guarda versión, semilla, opciones seleccionadas, hechos del paciente, cambios fisiológicos iniciales y procedencia. Las solicitudes y errores del proveedor no se guardan como texto libre. Si la respuesta de IA es incompleta, rechazada, inválida o no está disponible, se utiliza una variante local predefinida. Reanudar un encuentro usa la especificación y el estado guardados; no necesita volver a generar el caso.

Durante el caso, el motor existente calcula las consecuencias de las intervenciones y actualiza signos, estudios y ECG. La IA también puede ayudar a interpretar entradas en español o inglés. La información del paciente y las respuestas de la aplicación continúan en inglés.

## Alcance de la revisión docente

Los perfiles se comprueban con pruebas de software: coherencia entre presentación y signos iniciales, diferencias persistentes entre perfiles, ejecución de sedación y cardioversión, reevaluación inmediata, cambios de ECG, recuperación del estado y rechazo de respuestas de IA fuera de las opciones permitidas. Estas pruebas no equivalen a validación clínica o psicométrica.

La fisiología de PS001 tiene simplificaciones heredadas. Por ejemplo, sus reglas de cardioversión constituyen una simplificación del motor; la recuperación temprana depende del acoplamiento entre ritmo, llenado y flujo, además del parámetro de contribución de la fibrilación auricular. No se debe interpretar que un perfil representa una etiología pura ni que la respuesta de una simulación determina por sí sola cuál era la decisión clínica correcta.

Antes de usar estas variantes para evaluar residentes, el equipo docente debe revisar sus trayectorias, calibrar magnitud y demora de las respuestas y acordar criterios para valorar las explicaciones. El simulador textual puede aportar evidencia sobre razonamiento y planificación; no demuestra destreza manual, calidad real de adquisición ecográfica, liderazgo de un equipo clínico ni desempeño independiente con pacientes.

v0.11.0 agrega valoración docente y registro longitudinal de componentes simulados por objetivo, con metas y topes; ver [Registro por objetivo](OBJECTIVE_TRACKING.md). Los próximos incrementos del plan podrán agregar familias clínicas, prerrequisitos revisados por docentes y adaptación más fina del recorrido. Ninguna de esas capacidades se considera implementada por incluirla en la matriz.

## Documentos utilizados

Las páginas indicadas son páginas físicas del PDF, contando desde 1. Se usa la edición aportada para que el mapeo sea trazable; no se afirma que sea la edición vigente de acreditación.

1. **ACGME, Emergency Medicine Milestones**, archivo `emergencymedicinemilestones.pdf`, hoja de trabajo versión 2.1; segunda revisión de febrero de 2021, implementación el 1 de julio de 2021. PC1 *Emergency Stabilization*, p. 7; PC4 *Diagnosis*, p. 10; PC5 *Pharmacotherapy*, p. 11; PC6 *Reassessment and Disposition*, p. 12; MK1 *Scientific Knowledge*, p. 15; MK2 *Treatment and Clinical Reasoning*, p. 16. Las pp. 4–5 explican que los niveles no corresponden a años de residencia y que no deben ser la única base para decisiones de certificación. Las abreviaturas PC/MK se utilizan aquí como claves de visualización.
2. **Royal College of Physicians and Surgeons of Canada, Pathway to Competence in the Specialty of Emergency Medicine**, archivo `pathway-to-competence-emergency-medecine-e.pdf`, versión 1.0 de 2018, efectiva desde el 1 de julio de 2018. Medical Expert 1.6, pp. 9–10; 2.2, pp. 11–14; 2.4, pp. 15–17; 4.1, pp. 22–23. Sus etapas *Transition to Discipline*, *Foundations*, *Core* y *Transition to Practice* describen desarrollo por competencia y no se convierten automáticamente en R1/R2/R3.

El documento ACGME aportado no es un currículo de ACEP. Los dos documentos son referencias de competencias y desarrollo; no constituyen por sí solos una lista exhaustiva de conocimientos por enfermedad ni validan los perfiles fisiológicos de esta aplicación.
