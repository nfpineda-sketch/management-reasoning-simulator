# FR-E · Mujer de 72 años · tratamiento tardío y recuperación — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_72f` (sintético). Duración estimada de este escenario: 7 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Cubre el tratamiento tardío y la recuperación posterior: dos horas sin tratar y luego vía, 1 litro y 2 unidades. Segundo caso (otra edad y sexo), lo que ayuda a distinguir un problema del caso de uno general. Incluye la comparación de consciencia en un curso reversible.

**Pregunta principal:** Tras dos horas sin tratamiento, ¿el deterioro y la recuperación (momento, velocidad y tamaño) son plausibles?

## 2 · Presentación y estado de llegada
*A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint.*

FC 112/min · PA 98/62 mmHg · FR 24/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 4 s · extremidades Cool

## 3 · Qué hacer en la pantalla (guion; hazlo al pie de la letra)
| # | Modo (selector «Management») | Qué escribes (exacto) | Botón | ¿Pide las cuatro preguntas? |
|---|---|---|---|---|
| 1 | Treat | `Reassess in 60 minutes.` | Send | no |
| 2 | Treat | `Reassess in 60 minutes.` | Send | no |
| 3 | Treat | `Place an IV line.` | Send | no |
| 4 | Treat | `Give 1 litre of normal saline over 15 minutes.` | Send | **sí** |
| 5 | Treat | `Transfuse 2 units of packed red cells.` | Send | **sí** |
| 6 | Treat | `Reassess in 30 minutes.` | Send | no |

Cuando una orden marque «sí» en la última columna, la página abrirá un formulario de cuatro preguntas antes de ejecutarla: responde con el texto sugerido de las instrucciones (04) y pulsa `Complete reasoning & execute held order`. **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los interpreta como esperas y cambiaría el recorrido.

## 4 · Trayectoria de la presión (autoridad experimental)
La pantalla la muestra como lista JSON bajo «Authority view (judge this first)»; esta tabla son los mismos números.

| Minuto | Presión (PAS/PAD, PAM) |
|---|---|
| 0 (llegada) | 98/62 |
| 60 | 81/51 (PAM 61) |
| 120 | 64/41 (PAM 49) |
| 125 | 69/44 (PAM 52) |
| 130 | 80/51 (PAM 61) |
| 160 | 109/69 (PAM 82) |

*Sólo estas tres cifras (PAS, PAD, PAM) vienen de la autoridad experimental. La frecuencia cardíaca, la respiratoria, la SpO₂, el relleno capilar y el estado mental vivo los calcula el motor vigente.*

## 5 · Manejo ejecutado
| Decisión en el minuto | Orden | Transcurrido (min) | Lo que hizo el simulador |
|---|---|---|---|
| 0 | Reassess in 60 minutes. | 60 | — |
| 60 | Reassess in 60 minutes. | 60 | — |
| 120 | Place an IV line. | 0 | peripheral intravenous access already in place; not repeated |
| 120 | Give 1 litre of normal saline over 15 minutes. | 5 | normal saline 1000 mL started over 15 min |
| 125 | Transfuse 2 units of packed red cells. | 5 | Packed red cells 2 units started |
| 130 | Reassess in 30 minutes. | 30 | — |

## 6 · Ciclo de vida de la autoridad
El experimento siguió activo hasta el final del guion; no hubo parada.

## 7 · Estado al final del guion (minuto 160)
FC 111/min · PA 109/69 mmHg · FR 24/min · SpO₂ 96 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 3.9 s · extremidades Cool

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
