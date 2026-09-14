# v0.24.3 — Monitorización no es soporte respiratorio

Las capturas del usuario muestran un rechazo que identifica explícitamente el
oxímetro, manguito y electrodos como soporte respiratorio y tratamiento no pedido.
La imagen mostrada no lleva una interfaz de oxígeno en nariz/boca. La corrección
se basa en esa evidencia, no en una suposición sobre la versión del despliegue.

El revisor devuelve un inventario tipado de dispositivos, hallazgos inesperados y
categoría de color de piel. El código compara las interfaces respiratorias con el
soporte prescrito. Oxímetro, manguito y electrodos siempre son monitorización
permitida, aunque estén conectados. Una interfaz no indicada, una requerida que
falta, sangrado, lesión u otro conflicto explícito sigue bloqueando la imagen.
La piel natural no distinguible de palidez leve genera una limitación visible;
no se fuerza despigmentación. Rubor marcado y cianosis siguen siendo conflictos.

Si al actualizar la sesión todavía retiene una imagen rechazada del mismo caso,
usuario, intento y apariencia, se vuelve a revisar esa imagen antes de generar
otra. No se acepta sin revisión, no se comparten imágenes entre pacientes y no se
crean reintentos ilimitados. Se mantiene una corrección máxima si la revisión falla.

Pruebas: 241 pruebas del flujo visual aprobadas, más la prueba añadida de que el
trabajo con candidato retenido no invoca la generación inicial (17 pruebas del
contrato específico aprobadas). Se reproduce la clasificación errónea reportada
con datos controlados. No se hicieron llamadas pagadas ni se certifica el resultado
de una futura revisión del proveedor en la sesión remota.
