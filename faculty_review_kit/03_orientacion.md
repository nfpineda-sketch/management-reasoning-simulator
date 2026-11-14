# 03 · Orientación para la persona revisora

*Lectura de unos 5 minutos. Se entrega antes de empezar.*

**Qué vas a ver.** Un simulador educativo **sintético** de manejo de una hemorragia digestiva alta, con dos pacientes inventados (un hombre de 57 años y una mujer de 72). No hay datos de personas reales ni se toma ninguna decisión sobre pacientes reales.

**Qué es experimental.** En esta revisión, **sólo la presión arterial** (PAS, PAD y PAM) la calcula un modelo experimental, el «núcleo común». Todo lo demás (frecuencia cardíaca, respiratoria, SpO₂, relleno capilar, estado mental vivo) lo sigue calculando el motor vigente. Es un experimento de desarrollo: **no se usa con residentes**.

**Qué es el «modelo heredado».** Es el cálculo anterior de la presión. Más adelante podrás compararlo con el experimental. **No es la verdad: es otro modelo.** Que se parezcan no prueba nada, y que difieran no es un error.

**Qué te pedimos.** Tu juicio clínico y educativo: ¿la presión va en la dirección correcta, en el momento correcto y con una magnitud plausible?, ¿responde de forma coherente al manejo?, ¿podría una trayectoria confundir a quien aprende? No evalúas el código ni la interfaz y no tienes que «acertar»: **tu desacuerdo es información valiosa**.

**Cómo es la sesión.** Cinco escenarios cortos (≈ 40 minutos en total; hay un sexto, opcional). En cada uno: ejecutas un guion breve, **juzgas primero sin el comparador**, luego lo revelas y terminas con tu juicio final. Tu primera pasada queda registrada y no se puede cambiar después de revelar.

**Una parada no es un desenlace.** En algunos escenarios el experimento **se detiene** (aviso `DEVELOPMENT AUTHORITY EXPERIMENT HALTED`). Es una parada **del experimento**, por un límite técnico: no dice nada sobre el paciente y no significa muerte ni paro. Nos interesa saber si la entiendes y si te confunde.

**Quién juzga qué.** Tú juzgas la plausibilidad clínica y educativa. El software sólo comprueba que los registros estén completos y sean consistentes, y **no puntúa ni interpreta tus respuestas**. Nada se promedia en un puntaje.

**Lo que esto no es.** No es un piloto con residentes, no es producción, no valida clínicamente nada y no sustituye ninguna decisión de atención.

**Tu privacidad.** Se usa un código (por ejemplo R1), no tu nombre. En los comentarios no escribas datos de personas reales, fechas, números largos ni nombres con título: el formulario los rechaza.
