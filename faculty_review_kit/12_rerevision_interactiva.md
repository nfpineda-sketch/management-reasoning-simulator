# 12 · Re-revisión de trayectorias en la pantalla (≈ 4 escenarios)

**Qué es.** La misma pantalla **Faculty Trajectory Review** de la primera revisión, con **trayectorias de presión nuevas** de cuatro escenarios: **FR-B, FR-C, FR-E y FR-G**. Casos sintéticos. **No** es validación clínica, ni un piloto con residentes, ni una puntuación. Tus juicios de la primera revisión se conservan aparte y **no** se transfieren a esta.

Esta pantalla **sustituye** a los archivos `.md` del kit `region_conjunta_v1/` como forma de hacer la re-revisión: no hay que abrir ni editar ningún archivo.

## Cómo entras
1. El operador arranca la aplicación (igual que en la primera revisión: `02_preparacion_operador.md`, paso 4). Inicia sesión con tu cuenta docente.
2. Se abre sola la pantalla **Faculty Trajectory Review** con **FR-B**. No hay nada que elegir ni ningún código que copiar.
   *(La primera revisión sigue disponible en «Review mode → Trajectory review (first review)». No la abras durante esta: te mostraría las trayectorias anteriores.)*

## Qué haces en cada escenario
1. Lee **What you are judging** (la pregunta de este escenario), el contexto, la tabla **What was done** y la trayectoria (gráfico y tabla de valores).
2. Contesta **Q1–Q5** (una pulsación cada una) y, si quieres, el comentario. Todo se guarda **solo**, también si escribes un comentario y pulsas directamente el botón siguiente.
3. Pulsa **LOCK FIRST IMPRESSION**. Desde ese momento tu primera impresión queda fija y **nadie puede cambiarla**, tampoco tú. No aparece ningún comparador ni ninguna otra trayectoria.
4. Elige el **Overall judgment** (ACCEPT / ACCEPT_WITH_LIMITATION / RECALIBRATE / REJECT) y, si quieres, un comentario.
5. Pulsa **SUBMIT & NEXT** (en el último, **SUBMIT & FINISH**). Pasas **sola/solo** al siguiente escenario.

Al terminar los cuatro aparece **RE-REVIEW COMPLETE · 4 / 4** con el recuento de tus juicios, la tabla por escenario y tus comentarios. Ahí termina este paso.

## Para consultar con una persona colega antes de bloquear
- Puedes enviar capturas **antes** de pulsar **LOCK FIRST IMPRESSION** y hablarlo con quien quieras: lo único que no se puede cambiar es lo que ya bloqueaste.
- Una captura útil son dos: (1) *What you are judging*, contexto, tabla de intervenciones, gráfico y tabla de valores; (2) las cinco preguntas, el comentario y el botón de bloqueo.
- Medido en un navegador real: en un monitor de 1080 p el escenario ocupa ≈ 2,3 pantallas; en una laptop de 768 px de alto, ≈ 3,3. Si quieres menos capturas, baja el zoom del navegador (Ctrl/Cmd −) al 67–80 %. No hay desplazamiento horizontal.
- **Ojo con lo que sale en la captura:** la barra lateral muestra el nombre de tu usuario. Usa un usuario no identificable o recórtala. La aplicación no controla lo que envías fuera de ella.

## Qué ves y qué no
- Ves: la pregunta, el contexto, qué se hizo y cuándo, la presión (PAS, PAD, PAM) y, **como contexto**, la frecuencia cardíaca y el relleno capilar. Estas dos las calcula el motor vigente del simulador; **no** forman parte de la trayectoria de presión que juzgas y **no se recalcularon para ella**: pueden no ser coherentes con la presión que ves.
- No ves: la revisión anterior, ningún comparador ni parámetros técnicos. Ninguna trayectoria es «la esperada».

## Si algo sale mal
- **Refrescas el navegador o se cierra:** la aplicación te pide iniciar sesión otra vez; al volver, tus respuestas guardadas y tu escenario actual están ahí.
- **Un escenario ya enviado** se puede **ver** (✓ en la barra superior), no cambiar.
- **Un error al guardar** se muestra en rojo y la pantalla **no avanza**: no se pierde nada; avisa a quien opera el entorno.
- **Si usas dos ventanas con la misma cuenta**, el bloqueo no se hace si lo que ves no coincide con lo guardado: la pantalla se reconstruye y te avisa; revisa tus respuestas y bloquea de nuevo.
- **Si un comentario no se guarda** (parece un identificador de paciente), el bloqueo espera: reescríbelo o bórralo.

## Notas
- **Tiempo:** ≈ 4 min por escenario es una **estimación** de quien escribió esto; no se ha medido con una persona.
- **Operador:** los registros están en `<almacén>/faculty_review/trajectory_rereview/` y `trajectory_rereviews/`, y el resumen técnico en `trajectory_rereview/session_summary_<ref>.json`. Los de la primera revisión están en otras carpetas y esta pantalla no las toca. Ningún dato de revisión entra al repositorio.
