# FR-A · Hombre de 57 años · deterioro sin tratamiento — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_57m` (sintético). Duración estimada de este escenario: 6 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Muestra la dirección y el ritmo del deterioro sin tratamiento y es la revisión principal de la parada por límite de colapso: el experimento se detiene antes del estado del paciente que la autoridad de presión no sabe representar.

**Pregunta principal:** Sin tratamiento, ¿la presión se deteriora en una dirección coherente y a un ritmo aceptable, y la parada ocurre en un punto comprensible?

## 2 · Presentación y estado de llegada
*A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak.*

FC 124/min · PA 88/54 mmHg · FR 26/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 5 s · extremidades Cool

## 3 · Qué hacer en la pantalla (guion; hazlo al pie de la letra)
| # | Modo (selector «Management») | Qué escribes (exacto) | Botón | ¿Pide las cuatro preguntas? |
|---|---|---|---|---|
| 1 a 4 | Treat | `Reassess in 60 minutes.` | Send (repite hasta el aviso de parada) | no |

La parada debe aparecer en la cuarta orden. Si en la tercera todavía no apareció, envía la cuarta; si tras la cuarta no hubo aviso, anótalo en el resumen de la sesión.

Cuando una orden marque «sí» en la última columna, la página abrirá un formulario de cuatro preguntas antes de ejecutarla: responde con el texto sugerido de las instrucciones (04) y pulsa `Complete reasoning & execute held order`. **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los interpreta como esperas y cambiaría el recorrido.

## 4 · Trayectoria de la presión (autoridad experimental)
La pantalla la muestra como lista JSON bajo «Authority view (judge this first)»; esta tabla son los mismos números.

| Minuto | Presión (PAS/PAD, PAM) |
|---|---|
| 0 (llegada) | 88/54 |
| 60 | 73/45 (PAM 54) |
| 120 | 58/36 (PAM 43) |
| 180 | 43/27 (PAM 32) |

*Sólo estas tres cifras (PAS, PAD, PAM) vienen de la autoridad experimental. La frecuencia cardíaca, la respiratoria, la SpO₂, el relleno capilar y el estado mental vivo los calcula el motor vigente.*

## 5 · Manejo ejecutado
| Decisión en el minuto | Orden | Transcurrido (min) | Lo que hizo el simulador |
|---|---|---|---|
| 0 | Reassess in 60 minutes. | 60 | — |
| 60 | Reassess in 60 minutes. | 60 | — |
| 120 | Reassess in 60 minutes. | 60 | — |

## 6 · Ciclo de vida de la autoridad
**El experimento se detuvo.** Aviso en pantalla: `DEVELOPMENT AUTHORITY EXPERIMENT HALTED`. Motivo operativo: `COLLAPSE_BOUNDARY_REACHED: the common core reads ESTABLISHED collapse at minute 207 of the interval 181..240: an experiment boundary, never a patient state`.

El experimento se detuvo porque la comparación de consciencia (no autoritativa) del núcleo común establece colapso dentro del intervalo siguiente. Es un límite del experimento, no un estado del paciente.
Tras la parada no hay más tiempo clínico ni acciones en esa sesión; la lectura sigue disponible. Un paquete de revisión se crea solo.

La orden que habría llevado el reloj hasta el minuto 240 no se aplicó: por eso no existe una presión del minuto 240.

## 7 · Estado al final del guion (minuto 180)
FC 137/min · PA 43/27 mmHg · FR 34/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Obtunded · relleno capilar 7.2 s · extremidades Cold

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente? · Q6 ¿la parada ocurrió en un punto comprensible? · Q7 ¿la parada generó confusión educativa?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
