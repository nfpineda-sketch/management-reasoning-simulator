# Guía del residente · piloto formativo

> **Estado (2026-10-08): actualizada al candidato final local de B-5 (IG-6, con ES-P1 a ES-P13), para la firma
> docente (I-63); no está firmada.** Describe la sala implementada en local el 2026-10-08, todavía no desplegada. Se entrega a los
> residentes sólo después de la firma. Las etiquetas van como las muestra la pantalla en español y, entre
> paréntesis, en inglés.

Un simulador de razonamiento de manejo. Es **formativo**: no hay nota global, ranking ni tabla de
posiciones, y ninguna inteligencia artificial lo evalúa. Un docente revisa cada encuentro.

## Antes de empezar

- **Tu cuenta:** entras con tu usuario y contraseña. La cuenta se crea con una invitación. Cambia la
  contraseña la primera vez: «Cambia tu contraseña» («Change your password»), en la barra lateral.
- **Foto e iniciales:** son opcionales. Lee el acuerdo; puedes aceptarlo o no, y nada cambia en tus
  encuentros.
- **Idioma:** el piloto corre en español y en inglés; elígelo en «Idioma · Language». Las pantallas están en
  español o en inglés, y puedes escribir tus órdenes en cualquiera de los dos. Durante un encuentro el idioma
  queda fijo. En un encuentro en español, la sala te habla en español: el relato del caso (también el POCUS y
  el E-FAST), el examen, las preguntas sobre tus órdenes, el aviso de una orden retenida, los recibos, los
  rótulos y los documentos que descargas. Los fármacos se nombran en español («noradrenalina», «salbutamol»);
  las dosis, las unidades, las vías y las siglas se escriben igual (mg, mL/h, IV, FiO₂, CPAP). Lo que tú
  escribiste se muestra tal como lo escribiste, también cuando la sala lo cita dentro de una frase en español.
- **Sin datos reales:** no escribas nombres ni datos de pacientes reales. Todo es simulado.

## El encuentro

1. **Comienza** con «Comenzar encuentro» («Begin Encounter»). El programa elige el desafío y el caso según
   tu año de formación.
2. **Lee la llegada:** la historia, los signos vitales, el examen y la foto o la vista neutral del paciente.
3. **Actúa como lo harías en la práctica:**
   - pregunta, examina, pide estudios y da órdenes, en texto libre;
   - escribe las dosis, las vías y cuándo reevaluar;
   - si una orden es ambigua, la sala te pregunta, y la pregunta no consume minutos. Tu respuesta completa
     sólo esa orden: si en la misma respuesta escribes otra, la sala la lee a continuación como una orden
     aparte y te dice qué pasó con ella; si tu respuesta deja algo sin completar, esa otra orden no se ejecuta
     y la sala te lo dice: escríbela de nuevo.
4. **Explica tu razonamiento con tus órdenes de manejo:** qué crees que está pasando, qué esperas que ocurra
   y qué vas a revisar. Si falta alguna de esas tres cosas, la sala retiene todo el envío y te pide
   completarlas, con tus palabras o con las preguntas guiadas. Tu prioridad y cuándo reevaluarás también se
   registran, pero su falta no retiene la orden. Una intervención urgente (ventilar con bolsa y mascarilla,
   descomprimir el tórax, controlar una hemorragia o poner un cinturón pélvico) nunca se retiene, y puedes
   explicarla después.
   El registro del encuentro (el Management Trace) guarda lo que escribiste y lo que pasó.
5. **El paciente responde a lo que haces:** el tiempo avanza con tus órdenes, tus esperas y tus
   reevaluaciones. «Espera 15 minutos» (u «observa 15 minutos») avanza el reloj 15 minutos; «reevalúa» sin un
   número es una mirada a la cabecera de 2 minutos; «da X y reevalúa» es X más esa mirada, y la sala te dice si
   X alcanzó a actuar. Para ver el efecto de un tratamiento, espera o reevalúa con un intervalo («reevalúa en
   15 minutos»). El reloj avanza como máximo 120 minutos de una vez: para más, vuelve a esperar. Si durante una
   espera ocurre algo importante, la espera se corta en ese minuto, la sala te dice qué pasó y recuperas el
   control. El examen dice lo que se encuentra en el momento en que examinas: para reevaluar, vuelve a
   examinar.
6. **Si el paciente hace un paro,** la sala lo dice. La reanimación no está modelada en este piloto: nada de
   lo que escribas después se ejecuta ni se evalúa.
7. **Termina con un destino:** a dónde va el paciente y con qué plan. Si cierras sin destino, la sala te
   pregunta cómo termina el encuentro; puedes seguir o terminar: «Finalizar ahora» («Finish now»).
8. **Revisa tus decisiones** en la revisión que se abre al terminar: «Revisión de decisiones» («Decision
   Review»). Para algunas de ellas te pregunta qué cambió en tu modelo de trabajo, qué disparó tu prioridad,
   qué harías distinto y qué respuesta esperabas. Queda guardada con el encuentro.

## La pantalla del encuentro

- **A la izquierda, el paciente** y, sobre la foto, el monitor. Arriba a la derecha, «Tiempo simulado»
  («Simulated time»): es el único reloj, en minutos. El minuto de cada entrada dice cuándo se obtuvo esa
  información; el monitor muestra al paciente ahora.
- **A la derecha, arriba, cuatro vistas**, lo más reciente primero:
  - «Evolución» («Evolution»): lo que la sala te entregó (respuestas, examen, resultados, reevaluaciones);
  - «Historia y examen» («History & Exam»): lo que preguntaste y examinaste, cada cosa con su minuto;
  - «Resultados» («Results»): lo pedido, lo pendiente y lo disponible; «Ver ECG» («View ECG») abre ese
    trazado, el de su aviso, sin pedir otro ni mover el reloj;
  - «Indicaciones» («Orders»): qué pasó con cada orden (ejecutada, no ejecutada, a la espera de una aclaración,
    pendiente, cancelada, o indicada con su efecto no modelado) y los tratamientos en curso.
  Consultarlas no envía nada ni borra lo que estás escribiendo.
- **A la derecha, abajo, «Manejo»:** elige un modo («Conversar», «Examinar», «Exámenes» o «Tratar»; en inglés,
  Talk, Examine, Tests y Treat; el elegido lleva ✓), escribe
  y pulsa «Enviar» («Send»). Enter agrega una línea; no envía. Bajo los modos, la sala te dice qué pasó con tu
  última orden (su recibo). Por ejemplo: «No se entendió: …» («Not understood: …»): no se dio ni se hizo
  nada, escríbela de nuevo con otras palabras; «Registrado como tu decisión, no administrado» («Recorded as
  your decision, not given»): el simulador no modela esa respuesta en este caso y nada cambió; «No se hizo
  ahora» («Not done now»): una orden para más tarde no se ejecuta ni se programa, escríbela cuando quieras que
  se haga; o, en un envío con varias órdenes, qué se ejecutó y qué no. Si una
  orden queda retenida o la sala te pregunta algo, el aviso queda a la vista hasta que respondas.
- **Envía una vez:** «Enviar» se desactiva mientras la sala procesa. Un doble clic o recargar la página no
  repiten una orden. Si un envío se interrumpe, la sala te lo dice y no lo repite: revisa el estado del
  paciente y envíalo de nuevo si todavía hace falta.
- **«☰ Menú» («Menu»), arriba a la izquierda:** tu cuenta, tu contraseña, el idioma (fijo durante el encuentro)
  y salir del encuentro (guardar y volver, o terminar el intento). Se abre con un clic o con el teclado y se
  cierra con Escape o con un clic fuera. Durante el encuentro no hay barra lateral.

## La foto y el POCUS

- **La foto** es una imagen fija del paciente, revisada por un docente. No muestra todos los signos clínicos:
  examina al paciente para evaluar lo que una foto no puede mostrar. La sala lo recuerda junto a la foto.
  Algunos casos llegan con una vista neutral, sin foto: el monitor, el examen y los
  resultados dicen lo mismo de todos modos.
- **El POCUS y el E-FAST** se entregan como un informe escrito de hallazgos: no hay imágenes ni videos. Lo
  que cuenta es cuándo los pides, cómo interpretas esos hallazgos y cómo los usas en tu manejo.

## Después

- **Revisión docente:** un docente revisa tu encuentro. El **foco de aprendizaje** y la retroalimentación
  aparecen después de esa revisión, no al cerrar.
- **Tus páginas:**
  - «Mis encuentros» («My encounters»): tus encuentros y sus revisiones;
  - «Mi progreso» («My progress»): tu evidencia por objetivo;
  - «Mi portafolio» («My portfolio»): tus documentos.
- **Tu registro:** puedes descargarlo completo: «Descarga tu registro completo» («Download your complete
  record»).
- **Privacidad:** otro residente no ve nada tuyo.
- **Si algo falla:** anota la hora y avísale al docente responsable del piloto.

Firma docente y fecha: ________________________
