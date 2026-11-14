# FR-G · Mujer de 72 años · infusión larga (sólo suero) — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_72f` (sintético). Duración estimada de este escenario: 6 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Es el único escenario de tratamiento parcial (suero sin sangre) y el más sensible al tiempo: un litro en 60 minutos mientras el sangrado continúa.

**Pregunta principal:** Con sólo suero y una infusión larga, ¿la trayectoria de la presión durante y después de la infusión es plausible?

## 2 · Presentación y estado de llegada
*A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint.*

FC 112/min · PA 98/62 mmHg · FR 24/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 4 s · extremidades Cool

## 3 · Qué hacer en la pantalla (guion; hazlo al pie de la letra)
| # | Modo (selector «Management») | Qué escribes (exacto) | Botón | ¿Pide las cuatro preguntas? |
|---|---|---|---|---|
| 1 | Treat | `Place an IV line.` | Send | no |
| 2 | Treat | `Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes.` | Send | **sí** |
| 3 | Treat | `Reassess in 10 minutes.` | Send | no |

Cuando una orden marque «sí» en la última columna, la página abrirá un formulario de cuatro preguntas antes de ejecutarla: responde con el texto sugerido de las instrucciones (04) y pulsa `Complete reasoning & execute held order`. **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los interpreta como esperas y cambiaría el recorrido.

## 4 · Trayectoria de la presión (autoridad experimental)
La pantalla la muestra como lista JSON bajo «Authority view (judge this first)»; esta tabla son los mismos números.

| Minuto | Presión (PAS/PAD, PAM) |
|---|---|
| 0 (llegada) | 98/62 |
| 60 | 92/58 (PAM 69) |
| 70 | 88/56 (PAM 67) |

*Sólo estas tres cifras (PAS, PAD, PAM) vienen de la autoridad experimental. La frecuencia cardíaca, la respiratoria, la SpO₂, el relleno capilar y el estado mental vivo los calcula el motor vigente.*

## 5 · Manejo ejecutado
| Decisión en el minuto | Orden | Transcurrido (min) | Lo que hizo el simulador |
|---|---|---|---|
| 0 | Place an IV line. | 0 | peripheral intravenous access already in place; not repeated |
| 0 | Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes. | 60 | normal saline 1000 mL started over 60 min |
| 60 | Reassess in 10 minutes. | 10 | — |

## 6 · Ciclo de vida de la autoridad
El experimento siguió activo hasta el final del guion; no hubo parada.

## 7 · Estado al final del guion (minuto 70)
FC 115/min · PA 88/56 mmHg · FR 26/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 4.5 s · extremidades Cool

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
