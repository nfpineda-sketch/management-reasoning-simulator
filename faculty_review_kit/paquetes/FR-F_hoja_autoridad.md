# FR-F · Hombre de 57 años · una acción que el experimento no puede juzgar — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_57m` (sintético). Duración estimada de este escenario: 5 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Cubre la parada operativa (no clínica): se ordena un vasopresor que la autoridad de presión no representa. Evalúa si la parada se entiende y si confunde. Aporta poca información de presión: se incluye por la experiencia de la parada.

**Pregunta principal:** ¿La parada por una acción que el experimento no puede juzgar es comprensible, está libre de lenguaje clínico o terminal y no confunde a quien aprende?

## 2 · Presentación y estado de llegada
*A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak.*

FC 124/min · PA 88/54 mmHg · FR 26/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 5 s · extremidades Cool

## 3 · Qué hacer en la pantalla (guion; hazlo al pie de la letra)
| # | Modo (selector «Management») | Qué escribes (exacto) | Botón | ¿Pide las cuatro preguntas? |
|---|---|---|---|---|
| 1 | Talk | `What brought you in today?` | Ask | no |
| 2 | Treat | `Start norepinephrine at 10 mcg/min.` | Send | **sí** |
| 3 | Talk | `What brought you in today?` | Ask *(la página lo bloqueará tras la parada: es lo esperado)* | — |

El aviso de parada debe aparecer al enviar la orden de norepinefrina. Después de la parada, la página no deja hacer más preguntas ni órdenes: es lo esperado (no es un fallo).

Cuando una orden marque «sí» en la última columna, la página abrirá un formulario de cuatro preguntas antes de ejecutarla: responde con el texto sugerido de las instrucciones (04) y pulsa `Complete reasoning & execute held order`. **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los interpreta como esperas y cambiaría el recorrido.

## 4 · Trayectoria de la presión (autoridad experimental)
La pantalla la muestra como lista JSON bajo «Authority view (judge this first)»; esta tabla son los mismos números.

| Minuto | Presión (PAS/PAD, PAM) |
|---|---|
| 0 (llegada) | 88/54 |
| 2 | 87/54 (PAM 65) |

*Sólo estas tres cifras (PAS, PAD, PAM) vienen de la autoridad experimental. La frecuencia cardíaca, la respiratoria, la SpO₂, el relleno capilar y el estado mental vivo los calcula el motor vigente.*

## 5 · Manejo ejecutado
| Decisión en el minuto | Orden | Transcurrido (min) | Lo que hizo el simulador |
|---|---|---|---|
| 0 | What brought you in today? | 2 | — |

## 6 · Ciclo de vida de la autoridad
**El experimento se detuvo.** Aviso en pantalla: `DEVELOPMENT AUTHORITY EXPERIMENT HALTED`. Motivo operativo: `UNSUPPORTED_AUTHORITY_ACTION: ['norepinephrine']`.

El experimento se detuvo porque se ordenó una acción que la autoridad de presión no representa (norepinefrina). Es un límite operativo del experimento, no un estado del paciente.
Tras la parada no hay más tiempo clínico ni acciones en esa sesión; la lectura sigue disponible. Un paquete de revisión se crea solo.

## 7 · Estado al final del guion (minuto 2)
FC 124/min · PA 87/54 mmHg · FR 26/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 5.0 s · extremidades Cool

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente? · Q6 ¿la parada ocurrió en un punto comprensible? · Q7 ¿la parada generó confusión educativa?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
