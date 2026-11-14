# FR-D · Mujer de 72 años · deterioro sin tratamiento (OPCIONAL) — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_72f` (sintético). Duración estimada de este escenario: 5 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Reserva. Sólo si FR-A te deja una duda de dirección o de ritmo (separa «problema del caso» de «problema general») o si te sobra tiempo. Es el único deterioro sin tratamiento del segundo caso.

**Pregunta principal:** Lo mismo que en FR-A, para el segundo caso: dirección, ritmo y comprensibilidad de la parada.

## 2 · Presentación y estado de llegada
*A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint.*

FC 112/min · PA 98/62 mmHg · FR 24/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 4 s · extremidades Cool

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
| 0 (llegada) | 98/62 |
| 60 | 81/51 (PAM 61) |
| 120 | 64/41 (PAM 49) |
| 180 | 48/31 (PAM 37) |

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
FC 125/min · PA 48/31 mmHg · FR 32/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Drowsy · relleno capilar 6.2 s · extremidades Cold

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente? · Q6 ¿la parada ocurrió en un punto comprensible? · Q7 ¿la parada generó confusión educativa?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
