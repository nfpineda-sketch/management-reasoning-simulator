# Enmienda 2 del núcleo común · Transición terminal y consciencia · PAQUETE DE DISEÑO (2026-11-10, A2-001 a A2-010)

**Estado: `AMENDMENT_2_BLOCKED_ON_FACULTY_THRESHOLDS`. No hay candidato. El núcleo común no cambió.**

Registro: `terminal_amendment_record.py`. Pruebas: `test_terminal_amendment_design.py`. Decisiones que lo
abrieron: FD-NEW-D, FD-NEW-E y FD-NEW-F del encargo del 2026-11-10 (filas FD-P3-163 a FD-P3-165 del Decision
File). No se afirma validación clínica y **no se eligió ningún umbral**.

## 1 · Linaje y espacio de trabajo (A2-001)

| | |
|---|---|
| Cierre histórico de la Fase 2 | `22b90a6f…`, inmutable, sin cambio |
| Padre | `PHASE2_AMENDMENT_1`, `10b45ce2…`, certificado sobre `0b3c4439…`; sin cambio |
| Rama de trabajo | `phase-2-amendment-2-terminal-consciousness`, creada desde `0c230f88…` (la cabeza de la rama de la Enmienda 1), **sin commits propios** |
| Núcleo activo en `phase-3-runtime-integration` | `PHASE2_AMENDMENT_1` (verificado por la compuerta de linaje) |
| Colisiones | `git fetch` antes de crear; no existía rama remota con ese nombre; sin push forzado |

Un sucesor exigiría lo mismo que la Enmienda 1: reversión declarada que reconstruya al padre byte a byte, entrada
de linaje y registro, contratos raíz, controles negativos de la compuerta, revisión adversarial y certificación
completa antes de promover. Nada de eso se inició: no hay candidato ejecutable.

## 2 · Grafo ejecutable de estado (A2-002)

Clasificación de cada arista en el registro (`GRAPH`, 28 aristas). Lo esencial:

- **Implementado en el núcleo:** flujos de sangre → V, Hb; V, P, T, ritmo → gasto; gasto × T → presión; FiO2 → SpO2;
  gasto, Hb, SpO2 → aporte; aporte → déficit → deuda D → lactato; D, presión, SpO2 → impulso simpático → FC;
  disponibilidad central → FR → W → PaCO2 → pH (sólo perfiles con ácido-base: opioide, no GI); PaCO2 → SpO2 (sólo
  donde el perfil declara la fracción de transmisión: los testigos); **escalera de PAS → consciencia y escalera de
  SpO2 → consciencia (adoptadas del motor heredado: reglas directas, no mecanismos)**; sin pulso → consciencia 3 y
  FR 0; evento de ritmo guionado → ritmo, pulso.
- **Diferido (existe, apagado o sin magnitudes):** regla de colapso del núcleo (gasto bajo → carga → ritmo sin
  pulso; ambos límites en `None`); capa candidata de colapso (PAM y déficit → señal → carga → terminal; todo sin
  fijar); capa candidata de encefalopatía (N; PAM, déficit, SpO2, pH, PaCO2, glucosa → estrés cerebral agudo →
  deterioro; todas las señales sin mapear).
- **Falta:** deterioro → categoría observada; depresor central → consciencia; PaCO2 → impulso simpático;
  ventilación ausente → pérdida de pulso; el fallo respiratorio como estado o predicado.
- **Sólo en el motor heredado:** la regla de paro por familia (opioide: 20 minutos sin soporte en fallo; **GI:
  ninguna**), el estado mental mostrado, el bloqueo del encuentro y la pantalla terminal.
- **Implementado en el runtime, este ciclo:** la frontera terminal de la traza (§6).
- **Sólo documentación:** la depresión farmacológica como modificador futuro del deterioro.

Dos correcciones a la auditoría anterior: el opioide **no** corre el perfil por omisión sino el de su migración
(mecánica respiratoria y ácido-base activos); y los testigos en vivo declaran el enlace de transmisión.

## 3 · Descomposición de la consciencia (A2-003)

| Contribuyente | Veredicto | Estructura | Magnitud |
|---|---|---|---|
| A · estado neurológico primario N | `STRUCTURALLY_JUSTIFIED` | la capa candidata lo lee como deterioro primario | no identificable: nadie escribe N |
| B · depresor central | `NEW_MECHANISM_REQUIRED` | la disponibilidad central sólo mueve la ventilación; si el fármaco deprime la consciencia por el mismo estado, por otro o sólo vía CO2 e hipoxemia es una decisión clínica que el repositorio no tiene | no identificable |
| C · deuda de aporte / carga hipóxica | `STRUCTURALLY_JUSTIFIED` | la capa candidata lee déficit agudo, PAM y SpO2 como señales de un mismo estrés | no identificable: sin mapear |
| D · carga hipercápnica | `STRUCTURALLY_JUSTIFIED` | lee pH y PaCO2 donde el perfil los calcula; diferido en GI | no identificable |
| E · colapso circulatorio | `STRUCTURALLY_JUSTIFIED` | ya ejecutado: sin pulso, nivel máximo; lo diferido es la regla que quita el pulso | no necesita |
| Escalera actual (PAS 80/65, SpO2 87/80) | **`DUPLICATIVE`** | es justo la regla directa que FD-NEW-E pide evitar | `LEGACY_DERIVED` |

**Doble conteo.** PAM y PAS son la misma presión relativa (una señal, no dos). La SpO2 entra en el aporte y por
tanto en el déficit, y además es señal propia: la capa candidata toma el **máximo** de sus señales, no la suma.
Lactato y deuda están aguas abajo del déficit: ninguno puede ser otra entrada. El impulso simpático ya lee deuda,
presión y SpO2: no es entrada de la consciencia. **El compuesto debe reemplazar a la escalera, no sumarse a ella.**

**Estructura identificable: sí. Magnitudes identificables: no.** Falta además el mapeo a categoría.

## 4 · Fallo y paro respiratorio (A2-004)

Existe: la FR expresada y la ventilación caen con la disponibilidad central, hacia cero; la PaCO2 sube sin cota y
no está definida en cero exacto; la disponibilidad está acotada a [0, 1] sin piso positivo y la pérdida del
escritor del opioide es proporcional, **así que nunca llega a cero** (medido: razón constante de 0,995 por
minuto); la frontera de apnea del enlace de oxigenación está declarada sin resolver. No existe: predicado o estado
de fallo respiratorio, una permanencia o carga de tiempo en fallo, arista alguna de la ventilación ausente al
ritmo, ni restricción autorada.

**Veredicto: `NEW_COMMON_STATE_REQUIRED`.** Las variables instantáneas bastan para *decir* que la ventilación es
baja, pero el paro es tiempo en fallo y su consecuencia: eso exige un estado que el núcleo no tiene, y tanto el
nivel que cuenta como fallo como la permanencia son umbrales que nadie ha fijado. Sin umbral, el único predicado
exacto es FR igual a cero, que el escritor comprometido no alcanza. Principio mantenido: predicado basado en
ventilación o impulso, nunca sólo en SpO2. **Ningún umbral elegido.**

## 5 · Colapso y paro circulatorio (A2-005)

Existe: un estado sin pulso tipado (ritmo, pulso, `terminal_since`) con su invariante; una regla en el núcleo de
gasto bajo a ritmo sin pulso, apagada; una capa candidata de PAM y déficit a evento terminal, sin fijar; la
memoria de la carga; y la detención de la corrida, por excepción, si el gasto llega a cero con pulso y sin regla.

**Veredicto: `EXISTING_VARIABLES_SUFFICIENT_STRUCTURE`.** Bloqueado en magnitudes: los rangos del registro de
calibración (0,2–0,4; 5–30) son `CANDIDATE` sin fuente y ninguno está aprobado; los casos de GI no los
identifican. Y en una elección estructural abierta: hay **dos** estructuras superpuestas (por gasto, en el núcleo;
por PAM y déficit, en la capa candidata) y no está decidido cuál es la regla. **Ningún umbral elegido.**

## 6 · Frontera núcleo común / runtime (A2-006)

- **Núcleo común:** el estado fisiológico; predicados estructurados (paro circulatorio, fallo respiratorio,
  deterioro severo de consciencia); un deterioro continuo con sus contribuyentes. Nunca el encuentro, la pantalla
  ni la categoría.
- **Runtime:** si un predicado termina el encuentro; qué motor decide mientras la autoridad es parcial; el mapeo
  del deterioro a la categoría visible; el comportamiento terminal del encuentro.
- **Motor heredado y sombra (hoy):** el heredado sigue decidiendo la terminación y el estado mental visible; la
  sombra registra, por traza, dónde está cada motor; nada del núcleo se muestra.

**Invariante exigido, implementado este ciclo fuera del núcleo y sin umbrales.** Cada traza lleva
`terminal_boundary` con uno de cinco estados (`TERMINAL_AGREEMENT`, `LEGACY_TERMINAL_CORE_ACTIVE`,
`CORE_TERMINAL_LEGACY_ACTIVE`, `BOTH_ACTIVE`, `TERMINAL_NOT_COMPARABLE`), el motivo, el lado heredado, el lado del
núcleo y tres predicados que sólo dicen lo que la lectura del núcleo ya resuelve sin magnitud (sin pulso: paro
circulatorio; FR exactamente cero con pulso: ventilación ausente; nivel máximo: deterioro severo) y
`NOT_DETERMINED` en todo lo demás. La verificación de la traza lo **recalcula**: una edición re-sellada no puede
falsearlo. El paquete de revisión docente lo muestra. No decide nada: `decides_the_encounter = legacy`.
Medido: opioide sin tratar → `LEGACY_TERMINAL_CORE_ACTIVE` desde el minuto 20.

Para un futuro runtime con autoridad: esa misma lectura debe ser **precondición** de la autoridad (un minuto con
frontera distinta de acuerdo o ambos activos debe detener la transacción). Diseñado; no construido.

## 7 · Identificabilidad (A2-007)

| Magnitud | Evidencia | ¿Sirve como umbral? |
|---|---|---|
| Escalera de consciencia PAS 80/65, SpO2 87/80 | `LEGACY_DERIVED` | No |
| Mapeos de señal de la encefalopatía | `NONE` | No |
| Constantes de tiempo de la carga de encefalopatía | `NONE` | No |
| Cortes deterioro → categoría | `NONE` | No |
| Umbral de gasto del colapso 0,2 / 0,3 / 0,4 | `SYNTHETIC` (rango candidato sin fuente) | No |
| Límite de carga del colapso 5 / 15 / 30 | `SYNTHETIC` | No |
| Valores de prueba de la regla de colapso (0,4; 10) | `EXPLORATORY` | No |
| Paro heredado del opioide: 20 min con FR ≤ 6, SpO2 ≤ 80 o supresión ≥ 0,85 | `LEGACY_DERIVED` | No |
| Nivel y permanencia del fallo respiratorio | `NONE` | No |
| Nivel de consciencia autorado a la llegada | `AUTHORED_CASE` (un piso, no un umbral) | No |
| Sin pulso ⇒ nivel máximo | `CERTIFIED_BEHAVIORAL` (un invariante, no una magnitud) | No |

**Regiones de desarrollo justificadas: ninguna.** No hay mecanismo con magnitud que esté a la vez aceptado y
respaldado por evidencia de una región amplia con confianza ≥ 0,80.

**Preguntas docentes exactas:**

1. **Consciencia.** ¿Aceptas reemplazar la escalera adoptada de presión y saturación por un único deterioro
   compuesto (el peor de: presión de perfusión, déficit de aporte de oxígeno, hipoxemia, acidemia/hipercapnia e
   hipoglucemia, más el estado neurológico primario)? Si sí, para cada señal: ¿en qué valor empieza el deterioro,
   en cuál es completo, y con qué rapidez se instala y se revierte?
2. **Categoría.** ¿Con qué deterioro el paciente está somnoliento, obnubilado y sin respuesta?
3. **Depresor central.** ¿Un opioide deprime la consciencia directamente, como estado propio, o su efecto sobre
   la consciencia lo llevan sólo la retención de CO2 y la hipoxemia?
4. **Colapso circulatorio.** ¿Cuál es la regla: gasto bajo sostenido, o presión de perfusión baja y déficit de
   aporte sostenidos? Para la elegida: el nivel, el tiempo que debe sostenerse y el ritmo en que se encuentra al
   paciente.
5. **Fallo respiratorio.** ¿Qué ventilación (fracción de la de llegada, o una frecuencia) cuenta como fallo,
   durante cuánto tiempo antes de ser paro, y un paro respiratorio quita el pulso sólo a través de la hipoxemia o
   por regla propia?
6. **Terminación.** Cuando el núcleo tenga autoridad, ¿qué predicados terminan un encuentro y cuáles sólo cambian
   lo que se muestra?

## 8 · Diseño mínimo (A2-008) e implementación (A2-009)

Contrato de salida preferido: deterioro de consciencia (valor continuo y contribuyente que lo fija); predicado de
colapso circulatorio; predicado de fallo respiratorio; predicado de deterioro severo de consciencia; cada uno
verdadero, falso o **no determinado** porque la regla que lo resolvería no está declarada. No un escalar terminal.

| Componente | Clase | Estado |
|---|---|---|
| Consciencia como compuesto de la capa candidata, **reemplazando** la escalera | Requerido ahora | Bloqueado: mapeos, constantes de tiempo y aceptación docente |
| Una regla de colapso circulatorio que pueda quitar el pulso | Requerido ahora | Bloqueado: elección entre las dos estructuras, nivel y permanencia |
| Los predicados estructurados como salida del núcleo | Requerido ahora | Bloqueado por los dos anteriores (sin nada declarado sólo repetirían el pulso) |
| La frontera terminal explícita en cada traza | Requerido ahora | **Hecho este ciclo, en el runtime** |
| Estado de fallo respiratorio con su permanencia (opioide) | Opcional después | — |
| Vía directa del depresor central a la consciencia (opioide) | Opcional después | — |
| Escritores de N; retorno de circulación; adopción de la fracción de transmisión | Opcional después | — |
| Un escalar terminal único | No justificado | — |
| Cualquier umbral tomado del motor heredado | No justificado | — |
| Mantener SpO2 → inconsciente o PAS → inconsciente como vía con autoridad | No justificado | — |
| Un paro definido sólo por SpO2 | No justificado | — |

**Implementación en el núcleo común: detenida a propósito.** Cada componente que cambiaría el núcleo certificado
depende de un umbral que nadie ha fijado o de una decisión docente que cambia su forma; un contrato de predicados
sin nada declarado no añadiría información y costaría una certificación completa de sucesor.

## 9 · Veredicto (A2-010)

**B · `AMENDMENT_2_BLOCKED_ON_FACULTY_THRESHOLDS`.** Para el caso preferido (GI) y para la contradicción terminal
misma, las estructuras ya existen en el núcleo y en sus capas candidatas; faltan sus magnitudes y una elección
estructural. Un mecanismo común nuevo sólo hace falta para las partes específicas del opioide (estado de fallo
respiratorio, vía directa del depresor), que el diseño deja para después y que son ellas mismas preguntas
docentes. **No se certificó nada; la certificación completa del núcleo no fue requerida ni se corrió.**
