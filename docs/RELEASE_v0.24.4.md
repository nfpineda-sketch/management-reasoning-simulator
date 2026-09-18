# v0.24.4 — Reparación dirigida de casos rechazados

Las capturas muestran autoría, corrección de contrato y rechazo clínico en v0.24.3.
El código anterior no devolvía esas objeciones al autor: cancelaba el caso, perdía
el detalle y podía haber comenzado una imagen de un caso que nunca se aprobó.
No se pueden reconstruir los motivos clínicos de esos intentos a partir del
mensaje genérico que conservaron.

Cambios:
- Una única reparación clínica del mismo borrador con el informe completo y la
  trayectoria real del núcleo; posterior validación estructural y nueva revisión.
- Todas las comprobaciones permanecen activas. Un segundo rechazo impide iniciar
  el encuentro. Se conserva la corrección estructural existente: máximo tres
  llamadas al autor y dos al revisor, sin bucles ni casos sustitutos silenciosos.
- Instrucciones del revisor alineadas con la disponibilidad global de tratamientos
  nativos; ausencia de deltas, compartimentos declarados o grillas de ventilador
  no implica tratamiento no implementado en main_ia_v1.
- La imagen comienza después de la aprobación clínica. Reduce gasto en borradores
  rechazados, a cambio de perder el solapamiento anterior entre imagen y revisión.
- Errores clínicos exponen solo nombres permitidos de controles fallidos. Borrador,
  informe y tiempos se adjuntan al error y conservan privadamente en la sesión del
  usuario. Docentes/administradores pueden descargar su propio diagnóstico en la
  pantalla de inicio tras actualizarla. No se filtran datos del caso en logs o
  widgets de residentes. Esto no es persistencia en base de datos: reiniciar el
  proceso o perder la sesión puede perder el diagnóstico.
- El uso registrado agrega ambas revisiones cuando hay reparación.

Verificación: 209 pruebas y 21 subpruebas aprobadas; incluye reparación exitosa,
rechazo persistente, datos privados, núcleo, recarga, inicio y ausencia de trabajo
de imagen antes de aprobar. Compilación y diff sin errores. Pruebas con respuestas
controladas, sin llamadas pagadas. No se ha verificado una generación real en la
sesión remota ni se garantiza aprobación universal por el revisor.
