# v0.22.0 — Cardioversión según ritmo y evolución posterior

Destino exclusivo: clinical-encounter-v0.13.

## Comportamiento

- Las reglas nuevas de cardioversión especifican ritmo previo, ritmo posterior
  y energía. Se seleccionan usando el ritmo al ejecutar cada choque, incluso
  dentro de una misma entrada con varias órdenes.
- Tras una conversión, otro choque no vuelve a sumar automáticamente su beneficio.
  Si existe una respuesta específica para el ritmo actual, puede representar
  ausencia de beneficio o un efecto adverso. Si falta esa respuesta, se explica
  la limitación del caso y no se ejecuta ninguna orden de esa entrada.
- Un choque fallido se distingue de una conversión: conserva el ritmo y puede
  repetirse o escalarse de acuerdo con las respuestas declaradas.
- Para especificaciones antiguas sin ritmo previo declarado se conserva la
  respuesta inicial. La protección nueva impide repetirla mientras persiste el
  ritmo de una conversión previa. No se inventan efectos adversos para esos casos.
- La recurrencia puede declararse con un intervalo mínimo relativo a la
  cardioversión y condiciones numéricas adicionales. Se comprueba cada minuto
  mientras persiste el ritmo posterior. Corregir el desencadenante puede impedir
  que se cumplan las condiciones. Sin recurrencia declarada, no se introduce una.
- La recurrencia sustituye el efecto numérico de esa conversión por el desenlace
  declarado respecto del estado inicial. Conserva deriva, medicamentos y efectos
  adversos independientes. Una nueva conversión sustituye el beneficio anterior
  y reinicia su propio reloj; no acumula sucesivas reducciones de frecuencia.
- Los registros de ritmo incluyen momento, ritmo previo/posterior y energía del
  choque. Un ECG obtenido antes de la recurrencia conserva su ritmo original,
  aunque su resultado aparezca después. El monitor utiliza el estado actual.
- Se reconoce también la indicación abreviada `Synchronized cardioversion 200 J`.

## Contrato y alcance

La generación exige ritmos previo y posterior y rechaza respuestas ambiguas para
el mismo ritmo/energía. `recurrence: null` expresa ausencia de recurrencia modelada;
una recurrencia declarada incluye `after_min`, `when`, `rhythm_after` y `delta`.
Se validan ritmos con pulso, intervalos, condiciones y límites numéricos.
Los coeficientes del paciente fijo PS001 no se convierten en reglas universales.
No se añaden FV, paro, desfibrilación ni un modelo electrofisiológico completo.

Los casos guardados conservan sus especificaciones, con la protección contra
repetir beneficios de conversión. La recurrencia y los efectos específicos por
ritmo requieren un caso que los declare: generar uno nuevo bajo v0.22.0.

## Verificación

- 477 pruebas de integración y 14 subpruebas aprobadas.
- Pasada posterior de parser/autor/recarga: 163 pruebas aprobadas.
- 15 pruebas finales específicas de cardioversión: choque repetido, daño separado,
  fracaso y reintento, atomicidad de órdenes compuestas, tiempo relativo,
  reconversión, prevención de recurrencia, ECG histórico, estabilidad, validación
  y compilación del esquema de generación.
- Siete regresiones históricas de main/IA aprobadas.
- Compilación y diff verificados; sin llamadas reales de generación IA para probar.
- Publicar el código no verifica por sí solo el proceso remoto de Streamlit.
