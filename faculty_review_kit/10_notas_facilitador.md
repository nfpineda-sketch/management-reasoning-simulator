# 10 · Notas de la persona operadora (no se entregan antes de revelar)

## 1 · Incertidumbres clave por escenario
**No se muestran a la persona revisora antes de su primera pasada** (evitan anclar el juicio). Aparecen en la hoja del comparador, **después** de revelar.
| Escenario | Incertidumbre clave |
|---|---|
| FR-B | El tamaño y la velocidad de la subida con 1 litro más 2 unidades: la autoridad sube la PAS 24 mmHg en 30 minutos desde la llegada; el modelo heredado, 14. |
| FR-A | El ritmo de caída de la PAS (88, 73, 58, 43 en tres horas) frente al del modelo heredado (88, 80, 72, 64); y que la parada llega por un criterio del experimento (colapso establecido por la comparación de consciencia), no por un estado de la presión. |
| FR-E | La PAS termina en 109 (minuto 160), por encima de la de llegada (98); y el estado mental de la comparación pasa de somnoliento a alerta (reversibilidad). |
| FR-G | La PAS baja de 98 a 92 durante la infusión y a 88 diez minutos después de terminarla; no sabemos si el sangrado en curso debe dominar tanto ni si el fin de la infusión debe notarse tan pronto. |
| FR-F | Un residente razonable podría pedir un vasopresor; el experimento se niega en lugar de simularlo. ¿Es aceptable en esta revisión inicial, donde esa limitación se declara a propósito? |
| FR-D (opc.) | La PAS cae de 98 a 48 en tres horas (el modelo heredado, de 98 a 74); la mujer parte de una presión mayor y termina más baja que el hombre de FR-A. |

## 2 · Por qué este conjunto
Se priorizó la **información educativa**, no la cobertura. Cinco escenarios núcleo cubren: deterioro sin tratamiento (FR-A), tratamiento precoz (FR-B), tratamiento tardío con recuperación (FR-E), tratamiento parcial e infusión larga (FR-G) y parada operativa (FR-F); la parada por límite de colapso está en FR-A. **FR-D** (opcional) separa «problema del caso» de «problema general». **FR-C** se excluyó por redundancia con FR-E. No se ajustó ninguna trayectoria.

## 3 · Avisos conocidos del entorno (todos verificados en un navegador real)
1. **La vista de autoridad es una lista JSON** en el panel; por eso existen las hojas de autoridad con la tabla.
2. **`Overall.` es visible antes de revelar**; la instrucción es dejarla para después. Sólo se guarda el valor final.
3. **En escenarios con parada**, el recuadro `Developer: Phase-3 authority experiment · HALTED` se abre y menciona `legacy_counterfactual_available: true`. **Sin cifras.** Se le pide a la persona ignorar los recuadros «Developer».
4. **La compuerta de razonamiento**: cuatro tipos de orden abren las cuatro preguntas antes de ejecutarse (verificado): el bolo, la sangre, la orden de infusión larga de FR-G y la de norepinefrina de FR-F; **nunca** la vía IV ni las esperas («Reassess in N minutes»). Las hojas de autoridad lo marcan paso a paso. El texto sugerido (04) reproduce el recorrido certificado.
5. **No añadir plazos** al texto de una orden («en 15 minutos»): la página los interpreta como esperas y el recorrido **ya no coincide** con la serie certificada (comprobado: un FR-B con ese texto llegó al minuto 60 en lugar del 30). El resumen lo señala como `DIFIERE`.
6. **Salir de un encuentro activo**: `☰ Menu` → `End this attempt without completing review` (vuelve al lanzador). Sólo tras una parada aparece `Exit the experimental encounter` en el panel. `Save & return to dashboard` deja un intento sin terminar (hay que pulsar `Abandon the unfinished attempt`).
7. **Hay que crear el paquete antes de salir** (en los escenarios sin parada) y enviar el formulario antes de salir: al salir se pierde lo no enviado.
8. **El formulario rechaza** identificadores en los comentarios (correos, números largos, fechas, nombres con título) y exige comentario si Q5 es POSSIBLY o YES.
9. El selector del lanzador lista **siete** escenarios; sólo se corren los de la lista 05.

## 3b · Limitaciones declaradas del entorno (no se corrigen aquí)
Registro y ancla sin firma; un proceso por almacén en disco local; ECG, cancelar pendientes y explicación retrospectiva bloqueados tras una parada; el aviso de parada está en inglés de desarrollo; el registro de sesión etiqueta mal el linaje (TD-146; la vista docente muestra el par correcto); la identidad del revisor no queda dentro del registro de retroalimentación (por eso: un almacén por revisor).

## 4 · Solución de problemas
| Síntoma | Qué hacer |
|---|---|
| `FACULTY DEVELOPMENT REVIEW UNAVAILABLE` y razones | Una condición no se cumple; lee la razón (`single_process`: hay otro proceso sobre el mismo almacén; `store`: el almacén no es escribible; etc.) |
| `UNFINISHED ATTEMPT` | Pulsa `Abandon the unfinished attempt`; lo no enviado se perdió; anótalo |
| El botón de revelar sigue deshabilitado | Faltan respuestas de las preguntas ciegas (Q1–Q5; Q6–Q7 si hubo parada) |
| `Submit feedback` da un error rojo | Lee el mensaje: respuesta faltante, comentario con identificador, o comentario obligatorio en Q5 |
| La parada no aparece en FR-A/FR-D | Envía una cuarta orden; si no hay aviso, anótalo |
| El resumen dice `DIFIERE` | Se tecleó otra cosa o se exploró; revisa el registro de órdenes del paquete; no es un error del revisor |
| El proceso murió | Reinicia; se pierde lo no enviado; `Abandon the unfinished attempt` |

## 5 · Lo que la persona operadora no hace
No responde por la persona revisora, no sugiere etiquetas, no revela el comparador, no cambia los guiones y no usa los datos de ensayo como respuestas.
