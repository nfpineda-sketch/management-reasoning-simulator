# Registro de objetivos de manejo simulado

El catálogo separa los **objetivos longitudinales** de los desafíos locales que
asignan un encuentro (`R1-03`, `R1-04`, `R2-01`). Un mismo encuentro puede aportar
evidencia para varios objetivos, pero cada objetivo requiere una valoración
docente independiente. La asignación de un caso no implica que todos sus
objetivos posibles se hayan demostrado.

## Metas del programa y alcance

Los números siguientes fueron proporcionados por el responsable del programa.
Se incorporan como metas configurables de esta aplicación; no se han verificado
de forma independiente como requisitos numéricos oficiales de las EPAs. Los
documentos aportados —Pathway to Competence de 2018 y ACGME Emergency Medicine
Milestones de 2021— no permiten atribuir automáticamente estos umbrales a una
certificación oficial.

El registro acredita **componentes de razonamiento y manejo en simulación**. No
acredita el desempeño completo de una EPA en el lugar de trabajo.

| Objetivo vinculado | Meta inicial | Alcance disponible en este piloto |
| --- | ---: | --- |
| TD1 | 10 | Reconocer inestabilidad con los hallazgos suministrados y justificar soporte inicial y reevaluación. |
| F1 | 15 | Priorizar e iniciar las intervenciones de reanimación disponibles y valorar la respuesta. |
| C1 | 40 | Integrar decisiones de reanimación, reevaluación y revisión del modelo de trabajo. |
| C2 | 25 | Reservado; los encuentros de trauma crítico no están implementados. |
| C3 | 20 | Razonar sobre oxígeno, preparación de vía aérea y soporte ventilatorio disponibles. |
| C4 | 20 | Justificar la sedación disponible, anticipar sus consecuencias y reevaluar. |
| C14 | 50 | Solicitar los hallazgos POCUS suministrados y utilizar sus implicaciones para decidir. |
| C15 | 5 | Reservado; los encuentros de cuidados al final de la vida no están implementados. |

El piloto no observa destrezas manuales, adquisición de imágenes, colocación de
dispositivos, activación real de ayuda ni liderazgo de un equipo real. C4 cubre
un contexto limitado de sedación, sin representar todo el campo de analgesia.
Los objetivos reservados no admiten valoraciones en este motor.

## Evidencia y valoración

`evidence_items` presenta las decisiones realmente ejecutadas, con el texto del
residente, las acciones interpretadas, el razonamiento y los estados registrados
antes y después. También presenta reflexiones completas, preservando la versión
previa a la comparación con el modelo experto cuando existe. Los intentos de
acción no ejecutados, las aclaraciones y las órdenes diferidas no se presentan
como acciones realizadas.

Los identificadores `trace:N` usan la posición original en Management Trace;
la etiqueta «Decision N» conserva la numeración visible del encuentro. El
registro de valoración conserva la evidencia seleccionada y su procedencia.

La extracción no asigna objetivos ni emite aprobaciones. Una palabra clave,
un formulario lleno o una mejoría fisiológica no demuestran por sí solos un
desempeño satisfactorio. El docente debe seleccionar la evidencia pertinente y
fundamentar su valoración. La IA utilizada para generar el encuentro no sustituye
esa decisión docente.

## Conteo y profundidad

El contador representa observaciones valoradas como satisfactorias, hasta la meta
del objetivo. Cada encuentro puede aportar como máximo una observación computable
por objetivo. El resto de los objetivos del mismo encuentro conserva su propio
contador. Al alcanzar la meta, las demostraciones posteriores no incrementan ese
contador; la historia completa del encuentro continúa guardándose.

Las etiquetas de profundidad describen la observación concreta:

| Etiqueta local | Interpretación para el docente |
| --- | --- |
| `foundational` | Una decisión de manejo focalizada con evidencia explícita. |
| `integrated` | Decisiones relacionadas que integran respuesta, reevaluación y prioridades. |
| `complex` | Razonamiento frente a incertidumbre o problemas clínicos que evolucionan y compiten. |

Las etiquetas de autonomía son `guided` (guiado), `prompted` (requirió
indicaciones) e `independent` (sin ayuda adicional para el razonamiento
observado). El docente debe documentar la ayuda relevante que conozca; el texto
de una respuesta no permite inferir por sí solo autonomía.

Estas etiquetas son definiciones locales de la aplicación. No equivalen
automáticamente a un año de residencia, un nivel de Milestones ACGME ni una etapa
del Royal College. **La meta N se comparte entre profundidades**: C4 con meta 20
no se transforma en 20 observaciones por cada profundidad.

La meta numérica alcanzada y el logro confirmado por el docente son estados
distintos. Antes de confirmar el logro en el alcance simulado, el docente debe
revisar calidad, consistencia y variedad del registro. Esa confirmación tampoco
certifica automáticamente competencia clínica en pacientes reales.


## Cierre, correcciones y nuevas observaciones

- **Sin observaciones:** todavía no existe una valoración docente activa.
- **En desarrollo:** hay valoraciones, pero el contador satisfactorio no alcanza la meta.
- **Meta alcanzada:** el contador llegó al N; se bloquean nuevas valoraciones para ese objetivo, sin insertar una observación adicional. Esto también evita acumular por encima del N aunque se cambie la profundidad.
- **Confirmado:** el docente revisó el registro y fundamentó el logro del componente simulado. No es un ascenso automático de año ni una certificación profesional.
- **No disponible:** el objetivo está planificado, pero el motor actual no permite evaluarlo.

Para corregir una valoración, el docente la anula con un motivo. La valoración
original y su evidencia permanecen guardadas; deja de sumar y puede registrarse
una nueva valoración del mismo objetivo en ese encuentro. Si el objetivo estaba
confirmado, la anulación retira esa confirmación para que vuelva a revisarse.

Reabrir un objetivo conserva sus observaciones y su contador. No reinicia el
historial ni crea otra cuota por nivel. Si se necesitan nuevas observaciones
tras llegar al N, un administrador debe aumentar la meta. En este piloto las
metas son **del programa completo**: el cambio afecta a todos los residentes.
Aumentar una meta no retira por sí solo una confirmación docente previa; para
continuar registrando en ese residente también hay que reabrirla. No hay todavía
cuotas individuales de mantenimiento o ciclos de certificación.

Las valoraciones no satisfactorias registradas antes del cierre aparecen en el
historial y en el total de encuentros evaluados, pero no aumentan el contador de
desempeños satisfactorios. Un envío repetido o dos evaluadores simultáneos no
pueden crear dos observaciones activas del mismo objetivo para un encuentro.
Las revisiones docentes utilizan exclusivamente encuentros finalizados, con la
reflexión completada, y excluyen los casos de prueba del personal docente.

## Activación y relación con la asignación

El registro requiere cuentas individuales y una base de datos persistente.
Con la clave común no se acumula progreso personal. Las tablas se añaden sin
borrar usuarios, encuentros ni configuraciones existentes; los encuentros
antiguos completados quedan disponibles para revisión, sin créditos automáticos.

Cerrar un objetivo no elimina ese problema de futuros casos: puede reaparecer
junto a otros objetivos pendientes. La selección actual continúa trabajando con
los tres desafíos locales del piloto; no usa estos contadores como equivalencia
automática entre una EPA y un desafío R1/R2. La siguiente asignación permanece
oculta al residente hasta completar su encuentro.
