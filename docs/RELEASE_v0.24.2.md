# v0.24.2 — Coherencia de recarga y diagnóstico de rechazos visuales

Un pie de página actualizado no garantiza que las dependencias Python almacenadas
estén actualizadas. Se añadió verificación explícita de versión del ejecutor,
adaptador, núcleo y esquema, además de las marcas del generador. Una prueba aislada
reproduce generador actual con ejecutor antiguo; tras la recarga el caso nuevo
aplica O2 a 4 L/min, 1000 cc NS y reevaluación mediante el núcleo compartido.
La versión esperada del núcleo es independiente de cambios cosméticos del producto.

El revisor visual debe describir una observación concreta por rechazo. Las
observaciones contradictorias con sus booleanos son una respuesta inválida. La
sudoración leve no resoluble se trata como incertidumbre etiquetada; sudoración
claramente excesiva u otros hallazgos incompatibles siguen rechazándose. Las
observaciones se muestran como texto en Image issue details, asociadas a la imagen
rechazada de la sesión; no se registran en logs ni se ejecutan como instrucciones.
Se conserva el máximo de una corrección y no se añaden llamadas de revisión.

Validación: 262 pruebas aprobadas, incluyendo recarga, generación, ejecución de
órdenes, fisiología y flujo visual. Sin llamadas pagadas. Esto reproduce y corrige
una debilidad de recarga compatible con el síntoma informado, pero no demuestra
que fuera la causa exclusiva en la sesión remota. Tampoco se ha inspeccionado la
imagen rechazada original; la mejora de instrucciones no garantiza eliminar todos
los falsos rechazos. No se borra el historial ni se inventan perfiles para casos
antiguos incompatibles.
