# Fase 3 · Cierre de la sincronización de ejecución de la sombra en vivo (ciclo del 2026-11-10, P3-167 a P3-171)

Rama `phase-3-runtime-integration`, desde `cb0b2c8`. Registro: `terminal_amendment_record.py` (bloques
`SYNCHRONIZATION`, `CASE_REVIEW`, `PILOT_IMPACT`, `ROADMAP`). Pruebas: `test_shadow_synchronization.py` (etiqueta
`p3s`) y `test_terminal_amendment_design.py` (etiqueta `a2`). El diseño de la Enmienda 2 está en `docs/revision/PHASE2_AMENDMENT_2_DESIGN.md`.

Todo es **sombra de desarrollo sin autoridad**. `COMMON_CORE_RUNTIME_AUTHORITY = False`. Nada lo ve un residente,
nada entra en la puntuación, el primer piloto no cambia. **`clinical_core/` y `family_engine.py` son byte a byte
los de `cb0b2c8`.** No se afirma validación clínica.

## 1 · Órdenes que el motor ejecuta durante una actividad de información (P3-167, FD-NEW-B)

**Camino real del motor.** Una sola función deja pasar tiempo clínico fuera de un turno de órdenes:
`family_engine.advance_clinical_time`. Dentro de su bucle de minutos, cuando vuelve un resultado pendiente,
ejecuta toda orden retenida que lo esperaba y devuelve su recibo entre los resúmenes de acción. La página la
llama desde `spend_clinical_time`, con tres llamadores: dos de pregunta de historia y uno de examen físico.
**Revisar un resultado ya disponible no avanza el tiempo del motor ni llama a ninguna función suya:** ahí no hay
camino de liberación que observar.

**Qué se hizo.** El ayudante de la página captura el estado antes, deja que el motor avance, y entrega a la
sesión el estado y los recibos del intervalo (`ShadowSession.observe_time`). La sesión lee **sólo** los recibos
de liberación: ni la pregunta, ni la respuesta, ni la región examinada llegan a ella. Cada orden liberada se
refleja **una vez**, en el minuto en que volvió el resultado (leído del registro del motor), presente desde el
estado e + 1: la misma regla y **la misma corrida, resumen por resumen,** que una liberación dentro de un turno
de órdenes. Luego la sombra avanza al minuto del motor.

**Aislamiento.** El motor no cambió. El observador copia lo que lee, no ejecuta nada y un fallo suyo queda en él.
Estado heredado, entradas de la puntuación y destino de órdenes idénticos con la sombra encendida y apagada.

**Controles negativos, cada uno con prueba:** sigue retenida; pasa a no ejecutable por paro; observación
duplicada; el mismo estudio pedido varias veces; liberación en actividades distintas y con la actividad troceada
de cualquier manera; acción ejecutada no soportada (brecha declarada, sin efecto fingido).

**En el navegador real** (Chromium, servidores aislados, sandbox docente con cuenta sintética): caso de GI con un
fluido retenido sobre un lactato, cuatro preguntas, un examen y dos preguntas más. La orden quedó
`HELD_NOT_EXECUTED` hasta el minuto 5 y desde el turno de la pregunta en que volvió el lactato figura `BUILT` en el
minuto 5 (colocada en 0), estado `COMPLETE`. En opioide el paciente no puede responder y la página no ofrece
preguntas: ese caso se cubrió por el arnés, no por el navegador.

## 2 · Cierre de la sincronización (P3-168)

Secuencias aleatorias acotadas, seis semillas por familia (GI y opioide), de 7 a 10 pasos que mezclan ejecución
ordinaria, ejecución diferida en turnos de órdenes, ejecución diferida en actividades de información,
observación duplicada y acciones no soportadas. En todas: toda acción ejecutada se refleja exactamente una vez,
en su minuto; ninguna no ejecutada toca la sombra; ningún recibo sin orden ni orden sin recibo; contra el sello
del motor donde existe; traza verificada y reproducida; aislamiento exacto.

**Veredicto: `LIVE_SHADOW_EXECUTION_SYNCHRONIZATION_COMPLETE`.** Cubre los dos caminos por los que la página deja
pasar el tiempo. **No cubre:** un intervalo avanzado sin el ayudante de la página (sigue declarado
`NOT_MIRRORED`); y el minuto de ejecución se sigue leyendo del registro del motor porque su recibo no lo trae.

## 3 · GI, caso preferido para una futura revisión de preparación de piloto (P3-169, FD-NEW-C)

Decisión docente: **GI es el caso preferido; orden GI, opioide.** No modifica el primer piloto congelado y no
despliega nada. Comparación actualizada:

| Criterio | GI | Opioide |
|---|---|---|
| Completitud causal | una cadena ejecutada de volumen a lactato, con orden visible | ventilación, CO2 y pH; la oxigenación sólo en los testigos condicionales; nada llega a la consciencia ni a un estado terminal |
| Preparación del runtime | golden comprometido, divergencias clasificadas, sincronización completa | sin golden; frontera terminal `LEGACY_TERMINAL_CORE_ACTIVE` cuando el curso sin tratar termina |
| Acciones no soportadas | acceso vascular e interconsultas | ventilación asistida, vía aérea y sedación |
| Incertidumbre de parámetros | un perfil de desarrollo, sin región condicional | tasa sin evidencia, región condicional, recuperación sintética |
| Dependencia terminal/consciencia | **el motor heredado no tiene regla de paro en GI: hoy no hay contradicción terminal**; queda la lectura de consciencia | paro heredado al minuto 20 que el núcleo no representa; consciencia inmóvil |
| Interpretabilidad de la traza | una corrida | una corrida y tres testigos; todo en el mismo minuto |
| Carga de calibración docente | magnitudes del perfil y mapeo de consciencia | todo lo de GI más tasa, región, fallo respiratorio y efecto directo del fármaco |

## 4 · Impacto en la preparación de piloto (P3-170)

Sólo las compuertas afectadas: **seguridad frente al residente** sigue `BLOCKED` (la Enmienda 2 está bloqueada en
umbrales docentes; la contradicción ahora es explícita en cada traza, no eliminada); **selección de casos** pasa
de `PARTIAL` a `GREEN` con alcance (preferencia docente para una revisión futura; ningún caso desplegado);
**captura de traza** sigue `GREEN`.

- **GI: `NOT_READY_FOR_RESIDENT_PILOT_REVIEW`.** Sin contradicción terminal hoy. Queda: la consciencia es una
  escalera heredada adoptada; no hay regla de colapso (un paciente de GI no puede quedar sin pulso en el núcleo);
  sin instantánea aprobada; nada de cara al residente.
- **Opioide: `NOT_READY_FOR_RESIDENT_PILOT_REVIEW`.** Con contradicción terminal. Queda además: tasa sin
  evidencia, ventilación asistida no representada.
- **Requiere docencia, no código:** cada pregunta de umbral de la enmienda, la instantánea de parámetros, la
  revisión de trazas.

## 5 · Hoja de ruta a `READY_FOR_RESIDENT_PILOT_REVIEW` (P3-171)

Camino crítico más corto, **para GI**; no es despliegue y no incluye otra familia de fisiología:

1. La docencia responde las tres preguntas de GI: compuesto de consciencia, categoría, regla de colapso.
2. Enmienda 2 sólo para GI (compuesto que reemplaza la escalera y una regla de colapso), como sucesor certificado
   de la Enmienda 1.
3. Revisión docente de trazas de GI e instantánea de parámetros aprobada.
4. Autoridad para GI más allá de la presión, tras la compuerta existente, con la frontera terminal como
   precondición.
5. Diseño de cara al residente para GI y su revisión.

Fuera del camino crítico: la tasa de profundización del opioide, el fallo respiratorio y el efecto directo del
depresor, cualquier otra familia.

## 6 · Certificación

**Mutantes:** 14 contra la suite de sincronización y 4 contra la frontera terminal, fuera del repositorio;
18 de 18 detectados.

**Revisión adversarial independiente** (subagente de sólo lectura, sobre el candidato sin commitear):

- **F1/F2 (medio-alto) — corregido en lo que la coherencia interna puede ver; el resto, declarado.** La
  verificación recalculaba la frontera terminal a partir de sus propios campos: una traza re-sellada podía
  reescribir entero el lado heredado. Ahora un paro heredado borrado se detecta, porque la propia corrida registró
  la divergencia de pulso. Queda fuera, declarado en el registro: reescribir el registro heredado de forma
  coherente (otro minuto), quitar la clave, o editar los canales del último minuto (eso sólo lo ve el replay).
- **F3 (medio, defecto anterior a este ciclo) — corregido.** Dos órdenes retenidas idénticas, liberadas cada una
  al final de su propio turno de cero minutos del mismo minuto, se reflejaban una sola vez (la clave que
  distingue una observación repetida de un turno nuevo colisionaba). Ahora la clave incluye el estado del motor
  alrededor del turno. Con prueba propia, y las secuencias aleatorias incluyen ya ese tipo de orden.
- **F4 (bajo) — corregido.** Tipos anómalos en la frontera (frecuencia `False`, pulso `None` o `0`, minutos
  mezclados) ya no fabrican un predicado ni un estado, y el motivo no afirma que los límites estén sin fijar.
- **F5 (bajo) — corregido.** La prueba de re-sellado sólo probaba ediciones incoherentes; ahora prueba las
  coherentes y fija cuáles se ven y cuáles no.
- **F6 (bajo, por diseño) — declarado.** Tras un intervalo que nadie observó, la lectura heredada de la frontera
  queda antigua.

Hallado sólido por el revisor: 600 intercalados aleatorios en los cuatro casos (unas 700 liberaciones del motor,
con un oráculo sobre la propia función de liberación), **0 fallos atribuibles al candidato**; toda liberación en
una actividad de información coincidió en minuto, tipo, estudio y colocación, exactamente una vez; aislamiento
encendido/apagado exacto; 700 combinaciones de basura sin una excepción; ningún umbral en la frontera; ocho
afirmaciones del registro de diseño contrastadas con el núcleo. No cubrió: el camino real de la página bajo
Streamlit (cubierto aparte en el navegador con GI), la salida del observador y tres afirmaciones del registro
(regla de paro heredada del opioide, que nadie escribe N, pérdida proporcional), las dos últimas con prueba propia.

**Certificación final, una sola, sobre el candidato estable:**

- 53 archivos de prueba (los 51 de la certificación anterior más `test_shadow_synchronization.py` y
  `test_terminal_amendment_design.py`): **1 556 aprobadas, 0 fallidas, 0 omitidas**; uno de los 53
  (`test_core_certification_preview.py`) no contiene pruebas, igual que antes.
- Regresiones: **56 de 56 activas**; 10 retiradas, conservadas y no ejecutadas, como declara el propio ejecutor.
- Huella del candidato idéntica al inicio y al final de la corrida.
- Suite completa del núcleo común: **no requerida ni corrida** — `clinical_core/` no cambió
  (`ALREADY_VALID_ON_EQUIVALENT_CODE`); la compuerta de linaje verifica `PHASE2_AMENDMENT_1` certificado.
- Sin cambios en `clinical_core/`, `family_engine.py`, `pilot_acceptance.py`, `runtime_authority*.py`,
  `runtime_shadow_evidence.py` ni `CLAUDE.md`.
- Navegador (GI, actividad de información): 10 de 10 pasos con texto idéntico con la sombra apagada y encendida,
  0 errores de consola, 9 trazas. Corrida hecha antes de las correcciones de la revisión, que no tocan lo que la
  página muestra; no se repitió después.
