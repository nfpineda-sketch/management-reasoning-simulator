# 04 · Instrucciones para la persona revisora

*Lenguaje llano. Los textos entre `comillas de código` son los que verás en la pantalla (en inglés) y debes teclear tal cual.*

## A · Antes de empezar
La persona operadora te da la dirección de la página y el usuario (y, la primera vez, un código de invitación para crear tu contraseña). Ten a mano: la **orientación** (03), la **lista de escenarios** (05), una **hoja de autoridad** por escenario (carpeta `paquetes`) y el **formulario de papel** (06).

## B · Entrar
1. Si es tu primera vez: pestaña `Create account` → código de invitación, usuario, contraseña (mínimo 12 caracteres, sólo tuya) → `Create account`. Si ya tienes cuenta: pestaña `Sign in`.
2. Verás el título **Faculty development review** y un aviso amarillo que dice que es un entorno controlado, sólo de docentes, no piloto y no producción. Eso es lo esperado.

## C · Para cada escenario (en el orden de la lista 05)
1. **Léelo.** Abre la hoja de autoridad (`paquetes/FR-x_hoja_autoridad.md`) hasta la sección 3. **No abras la hoja del comparador.**
2. **Elígelo.** En `Review encounter` selecciona el escenario y pulsa `Begin review encounter`. Verás el monitor de cabecera y los datos de llegada.
3. **Ejecuta el guion** (sección 3 de la hoja). El selector **Management** tiene `Talk`, `Examine`, `Tests` y `Treat`:
   - Preguntas: modo `Talk`, escribe en el cuadro y pulsa `Ask`.
   - Órdenes: modo `Treat`, escribe el texto **exacto** de la hoja y pulsa `Send`.
   - **No añadas plazos al texto** (por ejemplo «en 15 minutos»): la página los entiende como esperas y el recorrido cambiaría.
   - Si antes de ejecutar una orden la página muestra **cuatro preguntas**, contéstalas con el texto sugerido de abajo (puedes usar el tuyo, sin plazos) y pulsa `Complete reasoning & execute held order`.
4. **Termina el guion**, o hasta que aparezca el aviso `DEVELOPMENT AUTHORITY EXPERIMENT HALTED` (una parada es parte del escenario, no un fallo).
5. **Abre el panel** `FACULTY DEVELOPMENT REVIEW PANEL · not resident-facing` (tras una parada se abre solo). Si **no** hubo parada, pulsa `Create review bundle`. Debe aparecer `Review bundle <código> · stored: True`; anota ese código en el registro (07).
6. **Primera pasada, sin comparador.** Bajo `Authority view (judge this first)` verás la trayectoria como lista (la hoja de autoridad trae los mismos números en tabla). Responde las preguntas de la pantalla (Q1 a Q5, y las dos de parada si hubo parada) y, **en paralelo, en el formulario de papel (06)**, donde además puedes escribir tu impresión global libre. **Deja `Overall.` sin responder todavía.**
7. **Revela el comparador.** Cuando las preguntas ciegas estén respondidas se habilita `Reveal the nonauthoritative comparison`. Púlsalo: desde ese momento **tus respuestas de primera pasada quedan fijas** (no se pueden cambiar). Ahora abre la hoja del comparador (`paquetes/FR-x_hoja_comparador.md`).
8. **Segunda pasada.** Responde `Did the common consciousness comparison appear plausible?`, `Was there any contradiction between pressure, consciousness and management?` y `Overall.`; elige `Reviewer role` = `faculty`; escribe tus comentarios. Si cambias de opinión, **no borres tu texto previo**: añade una línea que empiece por `AFTER REVEAL:`.
9. Pulsa `Submit feedback`. Debe salir `Feedback stored: <código>`. Si sale un error rojo, léelo (por ejemplo: falta una respuesta, o el comentario parece contener un dato personal) y corrige.
10. **Sal del encuentro.** Tras una parada: `Exit the experimental encounter`. Si no hubo parada: menú `☰ Menu` → `End this attempt without completing review`. Vuelves a la lista de escenarios. **Hazlo siempre después de enviar el formulario**: al salir se pierde lo que no se guardó.

## D · Preguntas de la pantalla (para que sepas qué significan)
| Pregunta en pantalla | En español |
|---|---|
| `Did pressure evolve in a clinically coherent direction?` | ¿La presión evolucionó en una dirección clínicamente coherente? |
| `Did deterioration occur too early, appropriately or too late?` | ¿El deterioro ocurrió demasiado pronto, de forma apropiada o demasiado tarde? |
| `Did the response to treatment begin too early, appropriately or too late?` | ¿La respuesta al tratamiento empezó demasiado pronto, de forma apropiada o demasiado tarde? |
| `Were the magnitudes of the changes plausible for the authored scenario?` | ¿La magnitud de los cambios fue plausible para el escenario? |
| `Would any pressure trajectory mislead a resident?` | ¿Alguna trayectoria de presión podría confundir a un residente? (si respondes «posiblemente» o «sí», se te pide un comentario) |
| `Did the halt occur at an understandable point?` | ¿La parada ocurrió en un punto comprensible? |
| `Did the halt behaviour create educational confusion?` | ¿El comportamiento de la parada generó confusión educativa? |
| `Did the common consciousness comparison appear plausible?` | ¿La comparación de consciencia pareció plausible? |
| `Was there any contradiction between pressure, consciousness and management?` | ¿Hubo contradicción entre presión, consciencia y manejo? |
| `Overall.` | Global: `ACCEPT` (plausible y útil tal cual), `ACCEPT_WITH_LIMITATION` (utilizable con límites que explicas en el comentario), `RECALIBRATE` (la dirección sirve pero el momento o el tamaño necesitan ajuste: di cuál), `REJECT` (incoherente o engañoso para enseñar). |
Las traducciones son una ayuda informal; manda el texto de la pantalla. Las definiciones de `Overall.` son una propuesta para que todas las personas las lean igual y se pueden enmendar.

## E · Texto sugerido para el formulario de cuatro preguntas
| Campo | Texto |
|---|---|
| `What do you think is going on?` | `Haemorrhagic shock from an upper gastrointestinal bleed.` |
| `What are you going to do?` | (déjalo vacío) |
| `What do you expect to happen, or what are you trying to clarify?` | `A higher perfusion pressure while the source is controlled.` |
| `What will you check, and when?` | `Blood pressure, heart rate and capillary refill in 15 minutes.` |

## F · Qué ignorar
Los recuadros `Developer: …`, `Operational status`, `Image issue details` y los números técnicos (son para quien opera el entorno). En las paradas, uno de los recuadros `Developer` menciona que existe un comparador heredado: es sólo un indicador técnico, sin cifras. **No uses** `Complete Encounter & Begin Review` ni `Save & return to dashboard`; si por error sales sin abandonar, la pantalla mostrará `UNFINISHED ATTEMPT`: pulsa `Abandon the unfinished attempt`.

## G · Si algo falla
No repitas en bucle. Anota en el resumen de la sesión (08) qué hiciste y qué viste, y avisa a la persona operadora. Si lo que ves **difiere de la hoja de autoridad**, anótalo: es información técnica, no un error tuyo.

## H · Al terminar
Rellena el resumen de fin de sesión (08) y devuelve tus hojas de papel a la persona operadora.
