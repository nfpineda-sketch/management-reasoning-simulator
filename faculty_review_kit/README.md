# Kit de la primera revisión docente (GI · autoridad de presión de desarrollo)

**Estado: preparado; la revisión NO ha empezado.** Este kit permite que una persona docente humana, invitada por la persona operadora, haga **manualmente** la primera revisión controlada. Nada en él responde por la persona revisora, ni juzga, ni puntúa.

Entorno: rama `phase-3-runtime-integration`, publicado en `e6f848f`. Alcance: autoridad de presión de **desarrollo** de GI (`gi_bleed_57m`, `gi_bleed_72f`). **No** es un piloto con residentes, ni producción, ni una validación clínica, ni una autoridad de consciencia.

## Qué hay aquí
| Archivo | Para quién | Qué es |
|---|---|---|
| `01_protocolo.md` | operador y comité docente | El protocolo: revisor objetivo, duración, orden, ciego, primera pasada, vínculos, privacidad, roles |
| `02_preparacion_operador.md` | operador | Cómo montar el entorno de **un** revisor (proceso único, almacén local, cuenta docente), ensayo y cierre |
| `03_orientacion.md` | revisor | Orientación de una página |
| `04_instrucciones_revisor.md` | revisor | Instrucciones exactas, en lenguaje llano |
| `05_escenarios.md` | revisor | Los 5 escenarios núcleo y 1 opcional: por qué y qué pregunta principal |
| `06_formulario_papel.md` | revisor | Espejo en papel; guarda la **primera pasada** |
| `07_registro_artefactos.md` | operador | Registro de códigos por escenario |
| `08_resumen_fin_de_sesion.md` | revisor | Formulario de cierre de sesión |
| `09_plan_analisis_posterior.md` | comité docente | **Sólo diseño** del análisis posterior (sin puntaje; el desacuerdo se muestra) |
| `10_notas_facilitador.md` | operador | Incertidumbres clave (no se muestran al revisor antes de revelar), avisos conocidos y solución de problemas |
| `paquetes/` | revisor | Por escenario: hoja de autoridad (antes de revelar) y hoja del comparador (después) |
| `tools/session_summary.py` | operador | Resumen técnico **de sólo lectura**: vínculos, verificación, repetición, coincidencia con el guion y completitud; tabula las respuestas sin interpretarlas |

## Quién juzga qué (FD-FR-08)
La persona docente juzga la **plausibilidad clínica y educativa**. El software juzga sólo **consistencia técnica, trazas, repetición, vínculos de artefactos y completitud del protocolo**. Los dos papeles no se mezclan.

## Qué se verificó antes de entregarlo (y qué no)
**Verificado** (en este equipo, con datos sintéticos y un almacén temporal aparte del real):
- el entorno certificado y publicado (suite completa 12 789 pruebas sin fallas; regresiones 56/56);
- **servidor Streamlit real + navegador real**: registro por invitación → entrada → lanzador → escenarios FR-B y FR-F hasta el final, creación del paquete, formulario ciego con el botón de revelar deshabilitado y sin comparador antes de revelar, aviso de parada, salida de un encuentro activo y de uno detenido;
- **dos servidores reales sobre el mismo almacén**: el segundo se niega (`single_process`) mientras el primero vive y toma el candado cuando el primero termina;
- las siete trayectorias de referencia coinciden con la serie certificada (también las ejecutadas en el navegador real);
- `tools/session_summary.py`: rutas positiva y negativa (vínculos, primera pasada, completitud) sobre datos temporales; el registro sintético de esa prueba se eliminó.

**No verificado:** que una **persona docente real** complete la sesión en ≈ 40 minutos (la duración es una estimación); la calidad de las traducciones informales al español de las preguntas; la creación de la invitación desde el proceso **de revisión** (sí se verificó en un arranque normal); ningún despliegue fuera de un equipo local.

## Qué NO hace este kit
No inicia la revisión, no contesta preguntas docentes, no marca ningún escenario como aceptado o rechazado, no calcula un puntaje global, no reclutó residentes y no toca la fisiología, el puntaje ni el primer piloto.
