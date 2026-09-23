# Rúbrica piloto 1.0 — verificaciones y limitaciones

> Qué se comprobó, dónde está la comprobación, y qué **no** demuestra.
> La validación técnica de esta implementación **no** equivale a validación educativa.

## Verificaciones dirigidas a los riesgos de esta función

Las nueve que pediste, cada una con el archivo que la sostiene.

| Riesgo | Cómo se comprueba | Dónde |
|---|---|---|
| **Cálculo correcto del total y mínimo de 0** | Suma de los cinco dominios; base 2 con dos eventos confirmados da **0**, no −4 | `test_rubric.py` |
| **Ausencia de total completo con dominios no evaluables** | Una parcial devuelve `base=None`, `adjusted=None`, `maximum=None`; conserva su subtotal sin normalizarlo; los PDF dicen "no comparable total" y la palabra "Base" no aparece | `test_rubric.py`, `test_rubric_reports.py` |
| **Distinción entre omisión y falta de oportunidad** | `NOT_ASSESSABLE` no cuenta como dominio evaluado; exige motivo antes de confirmarse; la pantalla lo pide y no guarda sin él | `test_rubric.py`, `test_rubric_store.py`, `test_rubric_portal.py` |
| **Ausencia de penalizaciones duplicadas** | El mismo identificador tres veces penaliza **una**; decidir el mismo evento dos veces se rechaza; proponerlo dos veces también | `test_rubric.py`, `test_rubric_store.py`, `test_rubric_analysis.py` |
| **Separación entre provisional y confirmada** | Sólo `status='confirmed'` penaliza; un borrador se guarda como borrador; confirmar exige los cinco dominios y resolver cada evento propuesto | `test_rubric.py`, `test_rubric_store.py`, `test_rubric_portal.py` |
| **Conservación de cambios docentes e historial** | Cada guardado es una revisión nueva con su número; tres guardados dejan tres filas; cambiar un puntaje propuesto exige justificación y ésta se guarda | `test_rubric_store.py`, `test_rubric_portal.py` |
| **Evidencia que corresponde a la decisión citada** | Las referencias son un enum construido desde el registro congelado; un dominio con puntaje sin referencias se rechaza | `test_rubric_analysis.py` |
| **Consistencia entre interfaz y PDF** | Los tres PDF se renderizan desde la **misma** `rubric_presentation.summary` que usa la app y se comparan en cada escenario | `test_rubric_reports.py`, `test_rubric_document.py` |
| **El informe de rúbrica no se entrega antes de tiempo** | Renderizarlo para el residente con la revisión en borrador, o sin revisión, falla; la negativa vive en el renderizador y no en quien lo llama | `test_rubric_document.py` |
| **Un hueco en el gráfico no es un cero** | Un dominio no evaluable no se dibuja en el centro, el contorno abierto no lleva relleno, y la pantalla lo dice además con palabras | `test_rubric_radar.py`, `test_rubric_profile_screen.py` |
| **Un perfil longitudinal no inventa lo que no observó** | Un borrador no entra; un encuentro sin evaluar está ausente y no en cero; cada dominio promedia sólo donde fue evaluable y lleva su conteo; un encuentro revisado tres veces cuenta una | `test_rubric_progress.py`, `test_rubric_profile_visibility.py` |
| **La historia no preguntada no excusa nada** | La información que el caso responde si le preguntan se declara aparte de la que tiene que estar en el registro; el tema prometido tiene que ser uno que el caso escribe; la regla viaja en la fuente y en las instrucciones | `test_history_is_part_of_the_record.py`, `test_case_assessment.py` |
| **El caso autorizado se encuentra en el payload que la app guarda** | Un payload construido campo por campo como lo arma `curriculum_runtime` devuelve su caso y, con él, sus eventos críticos definidos | `test_history_is_part_of_the_record.py` |
| **Leer una etiqueta no cuesta importar el bedside** | Un intérprete limpio importa `history_review` sin traer Streamlit ni PIL; las etiquetas viven en una hoja sin importaciones y `clinical_scene` las reexporta | `test_history_is_part_of_the_record.py` |
| **Ausencia de regresiones** | La suite completa del proyecto, incluidos challenges, Management Trace e informes existentes | suite completa |
| **La rúbrica no otorga ni revoca un challenge** | 15/15 confirmado no crea ninguna observación; 0/15 no revoca ninguna; ningún módulo de rúbrica importa `progress_store`, `progress_portal` ni `objectives`, ni al revés; las dos cosas viven en tablas distintas | `test_rubric_is_separate_from_challenges.py` |

## Verificaciones adicionales que el diseño hizo posibles

- **La IA no puede inventar un evento.** `event_id` es un enum de los definidos para ese caso; proponer uno ajeno se rechaza. Una preocupación no contemplada va a `concerns_for_review`, llega al docente y **no toca la aritmética**.
- **La IA no tiene dónde poner un total.** `total`, `base`, `adjusted`, `penalty` y `score_total` hacen fallar la validación. Hay una prueba por cada uno.
- **Un booleano no pasa como puntaje.** En Python `True == 1`; el validador lo rechaza explícitamente.
- **La declaración de un caso no puede prometer lo que el caso no ofrece.** Un estudio nombrado tiene que estar en sus investigaciones, una acción tiene que ser una que el motor ejecute, una región de examen tiene que ser una que el caso escriba. **21 de 21** casos, cero discrepancias.
- **Un identificador de evento significa lo mismo en todos los casos**, o es otro identificador.
- **Una rúbrica actualizada no recalifica hacia atrás.** Una revisión guardada bajo otra versión devuelve sus propios números con `recomputed: False`.
- **El documento del residente no lleva puntaje**, y el renderizador no acepta un argumento de evaluación para que no pueda pasársele por accidente.
- **Una falla del proveedor no deja un cero.** Deja el encuentro y los informes intactos y el estado como pendiente.
- **El historial no depende del azar.** Cada revisión lleva su número de secuencia, asignado dentro del bloqueo de escritura.

## Cómo se verificó, y con qué no

**Sin llamadas pagadas.** Todo lo anterior corre con encuentros sintéticos y clientes falsos. El ejemplo completo de [`docs/EJEMPLO_RUBRICA.md`](EJEMPLO_RUBRICA.md) usa una propuesta **ilustrativa**, escrita a mano con la forma exacta del esquema y validada contra él; el modelo figura como `ILLUSTRATIVE-NOT-A-MODEL-CALL`.

**Una corrida real, autorizada el 2026-09-23.** Una llamada a `gpt-5-mini`, ~3.500 tokens de entrada, 77 s, sin reintentos, costo estimado bajo US$0,03. Resultado y análisis en [`EJEMPLO_RUBRICA.md`](EJEMPLO_RUBRICA.md) §6. El modelo **no inventó ningún evento**, separó lo ejecutado de lo retenido, usó el canal de preocupaciones y declaró los límites del registro. **Discrepó en D5**: puntuó 1 donde la orden de destino existía pero el intérprete la había retenido, es decir, en la frontera exacta entre cero y no evaluable. Eso es lo que el docente confirma.

**Segunda corrida, 2026-09-23.** Una llamada más a `gpt-5-mini`, 54 s, sobre el tromboembolismo donde el residente trombolizó sin hipotensión sostenida en una paciente operada doce días antes. El modelo **propuso el evento definido** `pe_unindicated_thrombolysis` citando la decisión y revisando sus exclusiones, **no propuso** el otro evento definido del caso porque no aplicaba, y usó el descriptor de D3 como está escrito: 0 por una conducta claramente peligrosa. Con el docente confirmando: `Base 9/15 · Penalty -3 · Adjusted 6/15`, con el doble peso a la vista.

**Once corridas más, 2026-09-23 (madrugada).** Once encuentros nuevos, jugados a través del motor de producción con `tools_rubric_runs.py` y evaluados con una llamada cada uno. **Trece encuentros en total, trece solicitudes, cero reintentos, costo estimado bajo US$0,40.** El análisis completo está en [`RUBRICA_PILOTO_CORRIDAS.md`](RUBRICA_PILOTO_CORRIDAS.md). En resumen:

- **7 de 8 eventos esperados propuestos, 0 eventos propuestos sin motivo, 0 eventos inventados.** Cada propuesta cita la decisión, el minuto y los observables, y revisa las exclusiones declaradas antes de proponer.
- **El único que faltó, faltó con razón**, y el error fue del diseño del guión: `hypo_unsafe_discharge` exige que el registro contenga el agente causal, y el residente nunca preguntó por los medicamentos. El modelo se negó a asumirlo y mandó la preocupación al canal que existe para eso.
- **Cero usos de "no evaluable" en 65 puntajes de dominio.** Incluidos dos encuentros escritos para forzarlo, en uno de los cuales el propio modelo escribió que el encuentro cerró antes de la oportunidad y puntuó igual.
- **D3 es el único dominio que llega a 0**, y llega exactamente donde hay un evento. **D4 nunca bajó de 2** y **D5 nunca llegó a 3**, en trece encuentros.

**Decisión docente del 2026-09-23, y lo que destapó.** El evento se dispara igual cuando el residente nunca preguntó: la información disponible preguntando está disponible. Aplicarlo destapó dos defectos silenciosos, ambos corregidos con pruebas: **la historia era invisible para todo informe y para toda evaluación** (preguntar no es una orden, así que vive en los eventos y no en la traza, y nada miraba ahí), y **el caso autorizado era invisible en producción** (`case_id_of` leía sólo el campo que escribe la exportación, de modo que todo encuentro real parecía un caso sin oportunidades declaradas y **sin ningún evento crítico definido**; las pruebas ponían el campo a mano y por eso nada fallaba). Detalle en [`RUBRICA_PILOTO_CORRIDAS.md`](RUBRICA_PILOTO_CORRIDAS.md) §6.

**Lo que trece corridas siguen sin establecer:** concordancia entre evaluadores, comportamiento con residentes reales, y comparabilidad entre casos. Todas las corridas usan un solo modelo y un solo autor de guiones.

## Limitaciones que hay que declarar

**De la rúbrica como instrumento:**

- Es un **piloto pendiente de validación**. Sus puntajes no equivalen a niveles de ACGME, a etapas canadienses ni a niveles de supervisión de APC.
- La penalización de **−3** es una decisión inicial de diseño, no un valor validado. Está centralizada y versionada para poder cambiarla.
- La **ponderación igual** de los cinco dominios es una decisión inicial, no un hallazgo.
- Falta estudiar: **acuerdo entre evaluadores**, funcionamiento de los descriptores, efecto de las penalizaciones, y comparabilidad entre casos, idiomas y programas.

**De la cobertura:**

- Cobertura completa en los 21 casos es **requisito para comparar totales**, no prueba de dificultad equivalente ni validación psicométrica.
- Las ventanas temporales son decisiones clínicas declaradas caso a caso, no umbrales derivados de datos.
- **Lo disponible preguntando** se declara por evento como pares (tema de historia, qué le diría), y `verify` comprueba que el tema sea uno que el caso escribe. Es una decisión clínica declarada, no una derivación: que la historia de medicamentos sea lo que un alta insegura requiere es un juicio docente, no un umbral.
- El emparejamiento entre una pregunta escrita libremente y el tema que toca usa una tabla de patrones en `history_review.py`, deliberadamente amplia: acreditar de más una pregunta que el residente sí hizo es un error menor que decirle a un docente que nunca preguntó cuando sí lo hizo. El tema pedido con el control de temas es exacto.
- Los **casos generados por IA** no tienen declaración de cobertura: se puntúan los cinco dominios desde el registro, sin eventos críticos definidos. La app lo dice en pantalla.

**De la trazabilidad de las fuentes:**

- Las correspondencias canadienses **Medical Expert 2.2 y 2.3** no pudieron confirmarse en el texto extraído y **no se afirman**; ese contenido se cita por su texto textual y su página.
- **ACGME PC8** se cita con cobertura parcial: el motor no ejecuta la mayoría de los procedimientos manuales.
- **Colombia y México** no sostienen ninguna fila de la matriz.
- La equivalencia entre los resultados de aprendizaje de RCEM numerados en §3.2.1 y la numeración "SLO n" es lectura propia por correspondencia de enunciado.

**De la presentación:**

- El **Faculty Brief compacto creció de dos a tres páginas** con el perfil de cinco dominios. El contrato de informes dice que el compacto crece antes que recortar una justificación; ésta es esa situación. Si se prefiere, la rúbrica puede pasar a su propia página.
- El **Management Trace no lleva puntaje**, por la regla de visibilidad existente. Es una decisión deliberada con prueba, no un pendiente.

## Recuento

| | |
|---|---|
| Pruebas nuevas de la rúbrica | **145** |
| Casos del banco con cobertura completa | **21 de 21** |
| Discrepancias entre declaración y caso | **0** |
| Eventos críticos definidos | **16** |
| Llamadas pagadas realizadas | **2** (autorizadas, ~US$0,06 en total) |
