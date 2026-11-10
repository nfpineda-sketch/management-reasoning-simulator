# Fase 3 · Resolución de parámetros condicionales, órdenes retenidas y revisión de casos (ciclo del 2026-11-10)

Rama `phase-3-runtime-integration`, desde `f1f6034`. Registro: `shadow_resolution_record.py`. Pruebas:
`test_shadow_resolution.py` (etiqueta `p3r`); cada cifra del registro se comprueba ahí. Este documento resume;
no sustituye al registro.

**Numeración.** El encargo numera los paquetes P3-156 a P3-166 y las decisiones FD-151 a FD-156; en el Decision
File son las filas FD-P3-151 a FD-P3-159.

Todo es **sombra de desarrollo sin autoridad**. `COMMON_CORE_RUNTIME_AUTHORITY = False`;
`LIVE_FAMILIES = ("gi_bleed", "opioid")`. Nada de lo que sigue lo ve un residente, entra en la puntuación ni
toca el primer piloto. **No cambió ninguna fisiología del núcleo común:** `clinical_core/` es byte a byte el de
`f1f6034`. No se afirma validación clínica.

## 1 · Tasa de profundización del opioide: evidencia (P3-156)

Auditoría de sólo lectura. Procedencia de cada valor:

| Valor | Fuente | Estado | ¿Acota la tasa? |
|---|---|---|---|
| 0,005/min | `clinical_core/opioid_migration.py`, bajo «SYNTHETIC_ONLY» | `SYNTHETIC_REFERENCE` | No: es el punto comprometido |
| > 0 | Certificación P2U-1: el paciente sin tratar empeora de forma monótona | `CERTIFIED_BEHAVIORAL_CONSTRAINT` | Sólo el signo |
| 0,02 | Sonda de recurrencia de la migración | `EXPLORATORY_PROBE` | No |
| 0,03 | Sonda «severa» de la migración | `EXPLORATORY_PROBE` | No |
| 0,5 | Mutación inválida de una prueba | `EXPLORATORY_PROBE` | No |
| ninguno | Caso autorado: sin observaciones posteriores | `AUTHORED_CASE_CONSTRAINT` | No |
| paro al minuto 20 | Regla del motor heredado | `LEGACY_DERIVED` | No (nunca es objetivo de calibración) |
| ninguno | Decision File y documentos | `FACULTY_DEFINED` | No existe |
| f × ((1 − d)⁻⁶⁰ − 1) ≤ C | Fijación de desarrollo: SpO2 al minuto 60 sobre el piso | `CERTIFIED_BEHAVIORAL_CONSTRAINT` | Sólo en conjunto con f |

**Veredicto: C · `NOT_IDENTIFIABLE_WITH_EXISTING_EVIDENCE`.** No se adopta ninguna región de la tasa ni se
inventa un intervalo; las sondas exploratorias no se elevan a evidencia. Confianza del veredicto 0,9; la búsqueda
excluyó el corpus de validación, que esta etapa no abre. Lo que lo falsaría: una observación autorada posterior
del paciente sin tratar o una declaración docente de un tiempo.

**Pregunta docente exacta.** Para el paciente de desarrollo con opioide, sin tratar y al aire ambiente: ¿en qué
minuto debería haber caído la ventilación a una fracción dada de su valor de llegada —o, lo que es equivalente,
cuáles son el minuto más temprano y el más tardío en que aceptarías que el CO2 haya subido una cantidad dada—?
Un par así acota la tasa; sin él sigue siendo un único punto sintético.

## 2 · Análisis conjunto tasa × transmisión (P3-157)

Método: cota analítica → sondas fijas → bisección 1-D por testigo. Sin barrido cartesiano.

**Reparametrización.** La fijación depende de los dos parámetros sólo a través de **f × ((1 − d)⁻⁶⁰ − 1)**: la
disponibilidad central decae geométricamente, la subida del CO2 al minuto 60 es 69 × ((1 − d)⁻⁶⁰ − 1) y la
saturación con f = 0 no depende de d. No es f sola, ni d sola, ni el producto f × d (el producto en la cota
cambia de 0,000303 a 0,000122 entre las tasas probadas). La forma cerrada coincide con lo medido a 1e-9 relativo:

- f máxima admisible: `f_max(d) = 0,021270 / ((1 − d)⁻⁶⁰ − 1)`. En la tasa comprometida (única tasa
  justificada): **0,060621**. En las sondas exploratorias (no son testigos): 0,00901 a 0,02 y 0,004076 a 0,03.
- Tasa máxima que tolera cada testigo: LOW 0,014608 (2,92 × la comprometida); CENTER_REFERENCE 0,008892
  (1,78 ×); **HIGH 0,005045 (1,009 ×)**: HIGH queda a 0,9 % del borde.

**Veredicto: C · `CURRENT_REGION_VALID_ONLY_AT_COMMITTED_RATE`.** No se define región conjunta: haría falta una
cota justificada en las dos dimensiones y la tasa no tiene ninguna. La región pasa a clasificarse
**`CONDITIONAL_DEVELOPMENT_REGION`** (FD-151) en el código, en el registro del conjunto, en la procedencia de
cada testigo y en cada traza (`region.conditional_on`).

## 3 · Órdenes retenidas que el motor ejecuta después (P3-158)

**Antes.** Una orden «tras el resultado» era una brecha declarada y nunca se reflejaba; cuando el motor la
ejecutaba, la corrida de sombra no llevaba su efecto.

**Ahora, en la capa compartida de sesión** (ni el motor ni ningún adaptador cambiaron). Eventos:
`ORDER_PLACED`, `ORDER_HELD`, `ORDER_RELEASED`, `ORDER_EXECUTED`, `ORDER_CANCELLED` (reservado: el motor no
tiene cancelación) y `ORDER_TERMINAL_NOT_EXECUTABLE`.

- **Minuto real.** El recibo del motor trae el minuto de colocación, no el de ejecución. El de ejecución se lee
  del propio registro del motor (cuándo volvió el resultado esperado; si no, el fin del turno en que el motor la
  halló lista). Colocada en p, ejecutada en e: presente por primera vez en el estado e + 1. **Nunca desde p.**
- **Una sola vez.** Se empareja con el recibo por tipo, resultado esperado y minuto de colocación; volver a
  observar el turno no añade nada.
- **No soportada.** Ejecutada y sin representación en el núcleo: `DECLARED_GAP` con `UNSUPPORTED_ACTION`, sin
  efecto fingido.
- **No ejecutada.** Fila `HELD_NOT_EXECUTED` (octava disposición): a la sombra no le falta nada.
- **Sin recibo o sin minuto.** No se refleja y se dice (`NOT_MIRRORED`).

**Medido.** Opioide, naloxona retenida sobre un lactato: colocada en 0, ejecutada en 5, primer estado 6; en 20
maneras de trocear la espera el minuto reflejado es el sello del motor y la corrida es idéntica. GI: sangre,
fluido y oxígeno retenidos, igual. **Defecto hallado por las secuencias aleatorias de este ciclo y corregido:**
con el mismo estudio pedido varias veces el motor conserva sólo la hora del último resultado y libera con el
primero.

## 4 · Residuos de sesión (P3-159)

- **Generación del encuentro.** Existe un identificador explícito: el del registro de intento del que la página
  arranca cada encuentro con cuenta. La página se lo entrega a la sesión (tres líneas del ayudante de sombra de
  `app.py`, que sólo corren con la bandera encendida); la sesión guarda un resumen, nunca el identificador. Cierra
  el caso «segundo intento tras un primero que no dejó huella». **Residuo:** un encuentro sin registro de intento
  no tiene generación; ahí deciden las tres reglas de estado. No se añadió ninguna heurística.
- **Estado `hidden`.** `IRRELEVANT_TO_THE_CERTIFIED_MAPPING`: lo deriva el motor de estado que la regla ya
  compara, el mapeo certificado no lo lee y el caso no lo autora. No se añadió ningún valor autorado.
- **Integridad de la traza.** SHA-256 sobre la traza canónica más coherencia interna contra sus propios
  artefactos. **Protege:** corrupción o truncamiento; una edición sin recalcular; una edición re-sellada que
  contradiga los artefactos (estado, testigos, acciones, minutos, órdenes retenidas); un registro de otro linaje.
  **No protege:** el reemplazo por otro registro coherente (no hay clave, firma ni ancla externa); el borrado;
  quién escribió ni cuándo. No se añadió infraestructura criptográfica.

## 5 · Transición terminal y consciencia: auditoría de sólo lectura (P3-160)

| Concepto | Estado |
|---|---|
| Nivel de consciencia 0–3 (lectura derivada: piso de llegada, escaleras de presión y saturación) | `COMMON_CORE_EXISTS` |
| Estado neurológico N (nadie lo escribe ni lo lee en vivo) | `COMMON_CORE_EXISTS` |
| Deterioro por hipercapnia, acidemia, hipoxemia o bajo aporte (candidato P2L-2, magnitudes sin fijar) | `DEFERRED` |
| Depresión de la consciencia por fármaco | `MISSING` |
| Categoría observada del estado mental | `LEGACY_ONLY` |
| Pulso presente y ritmo | `COMMON_CORE_EXISTS` |
| Regla de colapso circulatorio (candidato P2M-2, límites sin fijar: apagada) | `DEFERRED` |
| Paro respiratorio: de la apnea a la pérdida de pulso | `MISSING` |
| Paro y desenlace terminal | `LEGACY_ONLY` |
| Señal terminal en la sombra (divergencia crítica de pulso y ritmo; orden retenida no ejecutable) | `SHADOW_ONLY` |
| Diagnóstico de ambas capas candidatas sobre un minuto de sombra (sin llamador) | `SHADOW_ONLY` |

**Aristas causales presentes:** presión → consciencia; saturación → consciencia; evento de ritmo guionado →
pulso. **Ausentes:** depresor central → consciencia; hipercapnia/acidemia → consciencia; deuda de aporte →
consciencia; apnea/hipoxemia → pérdida de pulso; carga de colapso → pérdida de pulso (apagada); estado del
núcleo → categoría observada.

**Contradicción posible hoy, medida:** opioide sin tratar; el motor heredado detiene al paciente en el minuto 20
(«Unresponsive», sin pulso) y el núcleo, en ese minuto, tiene pulso, PAS 106, SpO2 80 y el nivel de consciencia
de la llegada. **No es visible para un residente** (el núcleo no tiene autoridad ni se pinta); sería visible en
cuanto la tuviera.

**Representación mínima para que una simulación de cara al residente no se contradiga:** un estado terminal en
que coincidan los dos motores, con su causa; una lectura de consciencia con fuente causal por cada familia que
pueda moverla; el mapeo aprobado a la categoría observada; y la regla de qué motor decide mientras la autoridad
sea parcial.

**Veredicto: C · `COMMON_CORE_EXTENSION_REQUIRED`.** No basta un mapeo (el núcleo no calcula paro respiratorio,
efecto del fármaco ni categoría) y no hace falta rediseñar la representación (las variables existen; faltan
aristas y magnitudes). **No se implementó nada.**

## 6 · Camino real de la página en un navegador (P3-161)

Con la infraestructura del repositorio para comparaciones en navegador (servidores aislados de la página real,
sin red ni credenciales, cuentas sintéticas, Chromium): el mismo árbol con la bandera apagada y encendida.
Un encuentro de GI (`gi_bleed_57m`) y uno de opioide (`opioid_35m`), lanzados desde el sandbox docente con una
cuenta sintética de administración; cuatro pasos cada uno (llegada, una orden de cero minutos, un tratamiento,
una reevaluación), y una tercera corrida de GI con un almacén de trazas imposible de escribir.

**Resultado:** el texto renderizado de la página es idéntico con la sombra apagada y encendida en los 12 pasos;
sin errores de consola; una sola sesión por encuentro con su generación; acciones reflejadas; tres trazas
guardadas por encuentro, verificadas; el turno de cero minutos no abre otra sesión; con el almacén roto la
página no cambia. **Veredicto: `BROWSER_PATH_SHADOW_VALIDATED`.** No se creó ningún control visible.

Límites: compara texto renderizado y capturas por paso, no píxeles; no es una cuenta de residente ni llega al
cierre; la corrida vive fuera del repositorio y no forma parte de la suite. En las corridas con la bandera
encendida el registro de red del propio Chromium anotó intentos hacia su servicio de actualización de
componentes (no de la página): la página no hizo ninguna petición externa y los servidores bloquearon 0 intentos.

## 7 · Paquete de revisión docente de trazas (P3-162)

Herramienta externa (FD-154: nada dentro de la aplicación): `runtime_shadow_observer.py --review <dir>` escribe
un índice en markdown y una página por traza, nunca dentro del repositorio. Por traza: estado inicial, línea de
acciones, primer canal causal **esperado** y **observado**, secuencia aguas abajo, testigos de la región,
fallos, replay, parámetros sintéticos sin resolver y las preguntas que requieren juicio docente (ninguna sobre
la implementación).

El primer efecto se obtiene del propio artefacto de replay de la traza, quitando ese único tratamiento y
comparando canal por canal: sin fisiología nueva. **Hallazgo para la docencia:** en opioide todos los canales
aguas abajo de la reversión responden en el mismo minuto simulado; en GI el orden se ve (volumen y presiones,
luego deuda, luego lactato).

## 8 · Selección de casos: GI frente a opioide (P3-163)

Comparación de ingeniería en nueve criterios (claridad del mecanismo, discriminación del manejo, completitud del
runtime, incertidumbre de parámetros, acciones no soportadas, riesgo terminal, interpretabilidad de la traza,
confusión probable del residente, carga de calibración docente). **GI queda mejor en los nueve.**
**Orden: 1) GI, 2) opioide. No es una selección: la decide la docencia.**

- **Bloqueadores de GI:** sin instantánea de parámetros aprobada; mapeo de consciencia sin aprobar; sin
  representación terminal en el núcleo; nada diseñado de cara al residente.
- **Bloqueadores de opioide:** los anteriores, más: tasa de profundización sin evidencia; región condicional a
  esa tasa; el curso sin tratar termina en un paro heredado que el núcleo no representa; la ventilación asistida
  no está representada.

## 9 · Certificación adversarial integrada (P3-164)

**Ataques con prueba propia:** orden retenida que se ejecuta después; retenida que no se ejecuta nunca; recibo
duplicado; retenida no soportada; continuación de cero minutos; sesión vieja; traza de otra familia; traza
mutada y re-sellada; persistencia fallida; replay que no coincide; frontera exacta de la región sintética;
aislamiento encendido/apagado.

**Secuencias aleatorias acotadas:** seis semillas por familia, de 6 a 9 turnos con órdenes retenidas en el
conjunto. Con la sombra y el almacén encendidos frente a todo apagado: **estado heredado idéntico, entradas de la
puntuación idénticas, destino de cada orden idéntico, salidas visibles idénticas.** Autoridad `False`.

**Mutantes:** 24 mutaciones del comportamiento nuevo, fuera del repositorio; **24 de 24 detectadas.**

**Revisión adversarial independiente**, antes de la certificación final:

Un subagente de sólo lectura atacó el candidato sin commitear. Hallazgos confirmados y su destino:

- **F1 (alto) — corregido.** El motor también libera órdenes retenidas mientras pasa el tiempo de una pregunta o
  de un examen (`advance_clinical_time`), y ese camino no tiene turno de sombra. La orden salía de la lista sin
  recibo y la sesión la marcaba «cancelada», con la traza `COMPLETE`. El motor no tiene cancelación: esa orden
  corrió. Ahora queda como `ORDER_RELEASED`, fila `NOT_MIRRORED`, brecha declarada y estado nunca `COMPLETE`.
  **No se refleja** (no hay recibo del que reflejarla): es deuda declarada, TD-135 (2).
- **F2 (medio) — corregido.** La coherencia interna de la traza no ataba `held_orders` a la línea de acciones;
  una traza re-sellada podía re-etiquetar una orden retenida. Ahora cada orden retenida tiene exactamente una
  fila que dice lo mismo. Queda fuera, declarado: quitar la orden **y** su fila no deja nada que contradecir.
- **F3 (bajo) — corregido.** Volver a observar el turno de una liberación añadía una brecha falsa.
- **F4 (bajo) — corregido.** Una entrada malformada en la lista del motor detenía el avance de la sombra ese turno.
- **Sospechas atendidas sin reproducción:** el paquete de revisión ya no escribe a través de un enlace simbólico
  ni dentro del repositorio; el índice escapa enlaces, código y énfasis; una traza ilegible no cuesta el paquete.
- **Sospecha no atendida (S4):** una orden retenida sobre un ECG pedido en un turno posterior. No se pudo
  construir (el intérprete sólo retiene sobre un estudio nombrado en la misma orden). Declarada.

Lo atacado y hallado sólido por el revisor: 180 encuentros aleatorios de opioide con unas 200 órdenes retenidas
ejecutadas, **0 discrepancias** con el sello del motor; retenidas duplicadas y mixtas; GI; aislamiento
encendido/apagado; la generación. El revisor no probó `first_effects` ni corrió archivos de prueba.

**Certificación final, una sola, sobre el candidato estable:**

- 51 archivos de prueba (los 50 de la certificación anterior más `test_shadow_resolution.py`): **1 498 aprobadas,
  0 fallidas, 0 omitidas**; uno de los 51 (`test_core_certification_preview.py`) no contiene pruebas, igual que
  antes de este ciclo.
- Regresiones: **56 de 56 activas**; 10 retiradas, conservadas y no ejecutadas, como declara el propio ejecutor.
- Huella del candidato idéntica al inicio y al final de la corrida.
- Suite del núcleo común: `ALREADY_VALID_ON_EQUIVALENT_CODE` — `clinical_core/` no cambió desde `f1f6034`.
- Sin cambios en `clinical_core/`, `family_engine.py`, `pilot_acceptance.py`, `runtime_authority.py`,
  `runtime_authority_store.py`, `runtime_shadow_evidence.py` ni `CLAUDE.md`. `app.py`: tres líneas del ayudante
  de sombra.
- Navegador, repetido sobre el candidato final: 12 de 12 pasos con texto idéntico, 0 errores de consola.

## 10 · Las nueve compuertas, releídas (P3-165)

| Compuerta | Antes | Ahora |
|---|---|---|
| Exposición en tiempo de ejecución | `BLOCKED` | `BLOCKED` |
| Exposición en la interfaz | `BLOCKED` | `BLOCKED` (la herramienta docente de desarrollo no la pone en verde) |
| Captura de traza | `GREEN` | `GREEN` |
| Aislamiento de la puntuación | `GREEN` | `GREEN` |
| Flujo de revisión docente | `PARTIAL` | `PARTIAL` (hay paquete; ninguna revisión hecha) |
| Selección de casos | `NOT_YET_EVALUATED` | `PARTIAL` (comparación de ingeniería; sin decisión docente) |
| Visibilidad de fallos | `GREEN` | `GREEN` |
| Vuelta atrás | `GREEN` | `GREEN` |
| Seguridad frente al residente | `BLOCKED` | `BLOCKED` |

- **Preparación del motor de simulación:** `LIVE_SHADOW_SYNCHRONIZED_WITH_DEFERRED_ORDERS_FOR_DEVELOPMENT`.
- **Preparación de la revisión docente:** `READY_FOR_FACULTY_CASE_REVIEW_OF_SHADOW_TRACES_IN_DEVELOPMENT`.
- **Preparación de revisión de piloto con residentes:** **`NOT_READY_FOR_RESIDENT_PILOT_REVIEW`** (4 verdes,
  2 parciales, 3 bloqueadas). Bloqueadores exactos: sin representación terminal ni de consciencia en el núcleo;
  sin instantánea aprobada; tasa de profundización sin evidencia; ninguna revisión docente ni caso seleccionado;
  nada diseñado, construido ni revisado de cara al residente.

## 11 · Hoja de ruta (P3-166)

El paso siguiente **no** es otra familia de fisiología. Es un **paquete explícito de decisión docente sobre la
transición terminal y la consciencia en el núcleo común**: (1) si se autoriza la extensión; (2) qué fuentes
causales debe tener la consciencia; (3) el mapeo a la categoría observada; (4) qué termina un encuentro en el
núcleo y qué motor decide mientras la autoridad sea parcial. En paralelo, sin código: la revisión docente de las
trazas con el paquete, la pregunta de la tasa y la selección de casos. Después: instantánea aprobada, autoridad
más allá de la presión de GI, diseño de cara al residente.

## 12 · Límites declarados

Ver TD-135 en `docs/REGISTRO_DEUDA_TECNICA.md`. No se afirma validación clínica, preparación de residentes,
intervalo de la tasa, región conjunta, testigo seleccionado, caso seleccionado ni mapeo terminal implementado.
