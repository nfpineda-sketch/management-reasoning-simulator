# FR-B · Hombre de 57 años · tratamiento precoz — HOJA DE AUTORIDAD

> **Lee esta hoja antes de revelar el comparador.** Contiene sólo la trayectoria de la presión de la autoridad experimental y el manejo. No hay en ella ninguna comparación con el modelo heredado.
> Caso `gi_bleed_57m` (sintético). Duración estimada de este escenario: 8 minutos, con tus respuestas.

## 1 · Por qué está en la revisión
Es el escenario más simple y sirve para familiarizarte con la pantalla. Cubre el tratamiento temprano y eficaz y la reposición de volumen con sangre (vía, 1 litro de suero fisiológico, 2 unidades de glóbulos rojos).

**Pregunta principal:** Con un tratamiento precoz y completo, ¿la presión empieza a responder en el momento adecuado y con un tamaño plausible?

## 2 · Presentación y estado de llegada
*A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak.*

FC 124/min · PA 88/54 mmHg · FR 26/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 5 s · extremidades Cool

## 3 · Qué hacer en la pantalla (guion; hazlo al pie de la letra)
| # | Modo (selector «Management») | Qué escribes (exacto) | Botón | ¿Pide las cuatro preguntas? |
|---|---|---|---|---|
| 1 | Treat | `Place an IV line.` | Send | no |
| 2 | Treat | `Give 1 litre of normal saline over 15 minutes.` | Send | **sí** |
| 3 | Treat | `Transfuse 2 units of packed red cells.` | Send | **sí** |
| 4 | Treat | `Reassess in 20 minutes.` | Send | no |

Cuando una orden marque «sí» en la última columna, la página abrirá un formulario de cuatro preguntas antes de ejecutarla: responde con el texto sugerido de las instrucciones (04) y pulsa `Complete reasoning & execute held order`. **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los interpreta como esperas y cambiaría el recorrido.

## 4 · Trayectoria de la presión (autoridad experimental)
La pantalla la muestra como lista JSON bajo «Authority view (judge this first)»; esta tabla son los mismos números.

| Minuto | Presión (PAS/PAD, PAM) |
|---|---|
| 0 (llegada) | 88/54 |
| 5 | 91/56 (PAM 68) |
| 10 | 98/60 (PAM 73) |
| 30 | 112/68 (PAM 83) |

*Sólo estas tres cifras (PAS, PAD, PAM) vienen de la autoridad experimental. La frecuencia cardíaca, la respiratoria, la SpO₂, el relleno capilar y el estado mental vivo los calcula el motor vigente.*

## 5 · Manejo ejecutado
| Decisión en el minuto | Orden | Transcurrido (min) | Lo que hizo el simulador |
|---|---|---|---|
| 0 | Place an IV line. | 0 | peripheral intravenous access already in place; not repeated |
| 0 | Give 1 litre of normal saline over 15 minutes. | 5 | normal saline 1000 mL started over 15 min |
| 5 | Transfuse 2 units of packed red cells. | 5 | Packed red cells 2 units started |
| 10 | Reassess in 20 minutes. | 20 | — |

## 6 · Ciclo de vida de la autoridad
El experimento siguió activo hasta el final del guion; no hubo parada.

## 7 · Estado al final del guion (minuto 30)
FC 116/min · PA 112/68 mmHg · FR 21/min · SpO₂ 97 % · ritmo Sinus tachycardia · estado mental (campo vivo) Alert · relleno capilar 3.8 s · extremidades Cool

## 8 · Qué contestas ahora (primera pasada, sin comparador)
Q1 dirección · Q2 momento del deterioro · Q3 momento de la respuesta al tratamiento · Q4 tamaño de los cambios · Q5 ¿podría confundir a un residente?
Usa la hoja de papel (06) o la pantalla; **deja «Overall» para después del revelado**. Cuando termines, pulsa `Reveal the nonauthoritative comparison` y abre la hoja del comparador.
