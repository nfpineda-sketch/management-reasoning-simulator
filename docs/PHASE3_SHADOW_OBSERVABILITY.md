# Fase 3 · Sombra en vivo observable, persistente y con fallos visibles (ciclo del 2026-11-10)

Rama `phase-3-runtime-integration`, desde `1e18594`. Registro: `shadow_observability_record.py`. Pruebas:
`test_shadow_observability.py` y `test_shadow_sensitivity.py`; cada cifra del registro se recalcula ahí. Este
documento resume; no sustituye al registro.

**Numeración.** El encargo numera los paquetes de este ciclo P3-147 a P3-155, a continuación de P3-146; ningún
paquete histórico se renumera (FD-NEW-5). En código y pruebas llevan la etiqueta `p3o`.

Todo es **sombra de desarrollo sin autoridad**. `COMMON_CORE_RUNTIME_AUTHORITY = False`. Nada de lo que sigue
lo ve un residente, entra en la puntuación ni toca el primer piloto. **En este ciclo no cambió ninguna
fisiología del núcleo común:** `clinical_core/` es byte a byte el de `1e18594`. No se afirma validación
clínica y nada se ajusta a las curvas del motor heredado.

## 1 · Decisiones docentes y de arquitectura que abrieron el ciclo

| Decisión | Contenido | Fila |
|---|---|---|
| FD-NEW-1 | La comprobación de identidad exacta de la llegada del opioide es una **guarda de elegibilidad de la sombra en vivo** (`LIVE_SHADOW_ELIGIBILITY_GUARD`), **no** semántica clínica de mapeo nueva: no transforma ni infiere estado clínico; sólo permite el mapeo certificado ya existente mientras el estado del runtime sea exactamente la llegada redactada. Cualquier diferencia rechaza la apertura de la sombra. El opioide **sigue** en `LIVE_FAMILIES`. | FD-P3-139 |
| FD-NEW-2 | Un mapeo de llegada sólo vale antes de: cualquier avance positivo del tiempo, cualquier intervención ejecutada, cualquier mutación que signifique que el paciente ya no está en la llegada redactada. Un turno de cero minutos **no** crea una llegada nueva. Un paciente ya tratado no se vuelve a mapear como llegada. Vale para toda familia en vivo, GI incluido. | FD-P3-140 |
| FD-NEW-3 | Corregir en este ciclo el desfase de un minuto del adaptador de desarrollo fuera de línea del edema, con la misma semántica de tiempo que el camino en vivo corregido del opioide. Sin cambio de fisiología común. | FD-P3-141 |
| FD-NEW-4 | Las bandas de llegada y las tasas de profundización y de recuperación del opioide **no** entran automáticamente en el conjunto por región. Primero, una auditoría acotada de sensibilidad; un parámetro sólo se promueve si su incertidumbre puede cambiar materialmente un veredicto. Si no, sigue declarado `SYNTHETIC_ONLY`. | FD-P3-142 |
| FD-NEW-5 | Continuar con P3-147 en adelante. No se renumeran paquetes históricos. | FD-P3-143 |

## 2 · Ciclo de vida compartido de la sesión de sombra (P3-147)

**El defecto.** La sesión decidía «¿sigue siendo este mi encuentro?» con una regla compartida por todas las
familias: *es otro encuentro si el reloj está en cero y ya vi un turno*. Un turno que no consume tiempo deja el
reloj en cero, así que la página soltaba la sesión y abría otra **sobre el paciente ya tratado**, como si
fuera la llegada; la acción de ese turno y su hueco declarado se perdían del espejo. Reproducido en las dos
familias con órdenes reales que el motor ejecuta sin mover el reloj: en GI, colocar una vía, la interconsulta
o un sedante; en opioide, un sedante o colocar una vía.

**La regla, una sola, en la capa de sesión (`runtime_shadow.arrival_eligibility`): `ARRIVAL_ELIGIBLE`.** Un
estado se mapea como llegada sólo si se cumplen las cinco condiciones. El reloj es una de cinco:

| Condición | Qué compara |
|---|---|
| `clock_at_arrival` | el reloj del encuentro y el del motor están en 0 (el reloj mismo, no sus minutos enteros) |
| `engine_state_is_a_fresh_arrival` | el estado del motor, campo por campo, contra el mismo caso inicializado de nuevo |
| `monitor_is_the_authored_arrival` | lo que muestra el monitor contra la llegada redactada del caso, que tiene que existir |
| `nothing_administered` | el registro de administraciones, el historial de órdenes, la disposición y la línea de tratamientos están vacíos |
| `nothing_on_the_diagnostic_record` | el registro diagnóstico está vacío |

**Comportamiento.**

- Una sesión se **conserva** mientras sea el mismo caso, el reloj no retroceda y el estado no sea una llegada
  intacta vista *después* de que el encuentro de esa sesión dejó la suya. Un turno de cero minutos ya no la
  suelta: una sola sesión por encuentro, con la acción de ese turno en el espejo.
- Es **otro encuentro** una llegada intacta después de que el de la sesión dejó la suya (segundo intento,
  reinicio, encuentro regenerado).
- Una sesión a la que se le pide abrirse sobre un estado que **no** es una llegada intacta se abre **sin
  corrida** y con un fallo registrado (`ArrivalNotEligible`) que nombra cada diferencia. El encuentro queda
  sólo con el motor heredado, que es la lectura honesta, y se ve. Antes, un reloj pasado de cero no abría
  sesión alguna, en silencio.
- Se corrigió **una vez, en la capa compartida**. Ninguna familia lleva regla de ciclo de vida propia; la
  identidad de llegada del opioide delega la parte común en esta regla y conserva sólo lo suyo (el caso
  redactado que lee su mapeo certificado).

**Controles negativos, todos rechazados de forma explícita y sin autoridad:** paciente ya tratado; paciente
con tiempo avanzado; signos de llegada alterados; estado del motor tocado; administración en el registro;
estado previo de sombra reabierto como llegada nueva (la sesión vieja no se reutiliza ni se toca, y no hay
función que reabra una sesión desde una traza guardada); familia incompatible (ninguna sesión para una familia
que no está en vivo; `NoCertifiedAdapter` para un caso reetiquetado); variante no soportada.

**Residuo declarado.** Un turno sin tiempo y **sin huella en el paciente** (una orden diagnóstica cuyo
resultado aún no llegó) no marca el encuentro como salido de la llegada. Un segundo intento del mismo caso
justo después, sin el reinicio explícito de la página, se lee como la misma sesión. La fisiología de ambos es
la misma llegada. Lo que puede mezclarse es una fila no fisiológica del espejo; y, sólo donde un arnés
reutiliza identificadores de orden entre intentos, una acción del segundo intento puede tomarse por una ya
reflejada y quedar fuera (los identificadores de la página son únicos, así que ahí no se espera).

**Lo que la regla no puede comparar.** No hay referencia redactada para el estado `hidden` del motor ni para
claves de nivel superior que la llegada no tiene: un estado sintético alterado sólo ahí se lee como llegada.
Ningún turno real produjo uno en los 962 intentos de la revisión independiente.

**Veredicto: `SHARED_LIVE_SHADOW_LIFECYCLE_VALIDATED`.**

## 3 · Almacén de trazas de investigación de la sombra (P3-148)

`runtime_shadow_store.py`: el `SHADOW_RESEARCH_TRACE_STORE`. **No** es el almacén de artefactos de autoridad:
ninguno de los dos acepta los registros del otro.

- **Apagado por omisión.** Sólo escribe si el entorno del proceso de una ejecución docente o de desarrollo
  nombra un directorio absoluto y fuera del repositorio (`MRS_PHASE3_SHADOW_TRACE_STORE`). Un secreto de
  despliegue no puede nombrarlo, igual que no puede encender la sombra. Un directorio relativo o dentro del
  repositorio se rechaza, y el rechazo se registra una vez como fallo de persistencia.
- **Contenido de una traza:** familia; identidad del caso; versión y digesto del linaje (núcleo vigente, cierre
  histórico y capa de la Fase 3) y si el linaje está certificado; huella de la llegada y su elegibilidad;
  secuencia de acciones con minuto de la orden, minuto efectivo y disposición; por cada corrida, su papel, su
  testigo y el valor de su parámetro, sus minutos con el digesto del estado, el de las lecturas y los canales,
  y **su propio artefacto de replay**; fallos; estado estructurado; digesto de la traza.
- **Etiquetas de procedencia en el propio registro:** `NONAUTHORITATIVE_SHADOW` y `DEVELOPMENT_ONLY`;
  `resident_visible: false`; `selected_witness: null`.
- **Corridas.** GI: la de la sesión. Opioide: la de la sesión y **LOW, CENTER_REFERENCE y HIGH**, tres
  trayectorias enteras y aparte. Ninguna se elige, se prefiere ni se promedia.
- **Inmutable y sólo de creación:** un registro por estado de la sesión (crece turno a turno). La identidad se
  toma de las **entradas** (la llegada y lo hallado en ella, la secuencia de acciones, el artefacto de cada
  corrida, lo que falló y por qué, el registro anterior, el núcleo y la capa), nunca de lo registrado: las
  mismas entradas son el mismo registro (guardar dos veces no escribe nada) y las mismas entradas con otro
  contenido registrado son una **colisión que se rechaza**, que es como se vería una corrida no determinista.
  No lleva identidad de participante. Un registro se escribe **entero o nada**, sólo directamente dentro del
  directorio del almacén y bajo un nombre que ningún campo de la traza puede dirigir.
- **Intentos.** La huella de la llegada es la misma para todo intento de un caso, así que no los distingue.
  Cada registro nombra el registro que su propia sesión guardó antes, y esa cadena sí: `heads()` devuelve el
  estado más lejano de cada intento guardado; dos intentos que empiezan igual comparten sus primeros registros.
- **Lectura tolerante.** Un archivo que no se puede leer como registro se lista como `UNREADABLE`, y un
  registro que no pasa la verificación se lista como `NOT_VERIFIED`, nunca con el estado que lleva escrito.
- **Testigo fallido:** queda fallido en su último minuto válido, con su fallo. Nada se inventa después, y su
  replay llega hasta donde llegó. Los otros testigos y la corrida de la sesión siguen.
- **Persistir → recargar → reproducir:** exacto, por digesto de estado, digesto de lecturas y cada canal
  guardado en cada minuto, para GI y para las cuatro corridas del opioide. Una traza que no pasa la verificación, o registrada en otro núcleo o en
  uno sin certificar, **no se compara: se rechaza**.
- **Integridad:** un digesto de contenido **más la coherencia interna de la traza**: cada corrida es la que su
  nombre dice y corrió el valor que su testigo declara; cada corrida mide lo que su registro dice y una corta
  está marcada como fallida; el estado registrado es el que resulta de lo registrado; las acciones son las que
  recibió la corrida; las etiquetas y los testigos esperados son los de la familia. Juntos detectan un cambio
  accidental y una edición resellada que ya no cuenta una sola historia. Una falsificación rehecha para ser
  coherente en todas sus partes queda fuera de su alcance: **no se afirma firma alguna**. El número de turnos
  no se contrasta con nada.

**Veredicto: `SHADOW_TRACE_PERSISTENCE_VALIDATED`.**

## 4 · Observador docente, de sólo lectura (P3-149)

`runtime_shadow_observer.py`. **Superficie:** un informe de sólo lectura construido desde una traza guardada
por una herramienta docente o de desarrollo, **fuera de la página del encuentro**. No es una pantalla de la
app: una guarda vigente prohíbe que la página pinte la sombra, y ningún módulo que ve un residente puede leer
el almacén ni el observador. El primer piloto y la página no se tocan.

```
python3 -m runtime_shadow_observer --store DIR --list            # * marca el estado más lejano de cada intento
python3 -m runtime_shadow_observer --store DIR --id ID --out /ruta/absoluta/informe.html
```

**Muestra:** familia y caso; linaje; elegibilidad de la llegada, condición por condición; línea de acciones con
minuto de la orden, minuto efectivo y disposición; cada corrida aparte; canales clave en el tiempo; estado de
fallos; estado del replay. Para el opioide, como mínimo: disponibilidad central, FR, W, PaCO2, SpO2 y DO2.

- LOW, CENTER_REFERENCE y HIGH van rotulados **«DEVELOPMENT TEST WITNESS»**. CENTER_REFERENCE **no** se presenta
  como «la respuesta». La envolvente (mínimo a máximo de los testigos) se dibuja sólo como **resumen derivado**,
  detrás de las trayectorias y rotulada como tal: no es una trayectoria.
- **Verifica siempre.** Toda vista, con replay o sin él, verifica la traza; una que no pasa nunca se muestra
  con el estado que lleva, y la página dice `TRACE NOT VERIFIED` con el motivo.
- **Tolera datos rotos.** Sólo dibuja números finitos, normaliza las filas y nunca levanta por una traza
  malformada; el bloque de datos de la página no contiene `<`, `>` ni `&`.
- **Sólo lectura, por construcción y por prueba:** no da órdenes, no altera estado, no elige autoridad, no
  toca la puntuación, no elige un testigo y no escribe de vuelta en el almacén. La traza que recibe no cambia;
  el almacén queda byte a byte igual; la sesión y el paciente, también. La página generada no tiene formulario,
  botón, enlace, red ni almacenamiento, y todo texto que viene de los datos va escapado.
- **Invisible para el residente:** con la sombra y el almacén encendidos, lo autoritativo del encuentro es
  idéntico a con todo apagado; `app.py` no nombra ni el almacén ni el observador.

**Veredicto: `FACULTY_ONLY_SHADOW_OBSERVER_VALIDATED`.**

## 5 · Visibilidad de fallos (P3-150)

Un fallo de sombra es visible en la **traza**, en el **observador** y en el **replay**; nunca para el
residente, la puntuación ni el motor. Siete códigos distintos:

| Código | Cuándo |
|---|---|
| `ARRIVAL_REJECTED` | la sesión no pudo abrirse sobre ese estado (no es una llegada intacta, o no hay adaptador certificado, o la identidad del caso no coincide) |
| `UNSUPPORTED_ACTION` | una acción ejecutada no tiene representación en la sombra (hueco declarado) |
| `WITNESS_FAILED` | un testigo falló, se quedó atrás o falta |
| `REPLAY_MISMATCH` | el replay no reproduce lo registrado, o la traza no pasa la verificación |
| `LINEAGE_REJECTED` | el núcleo no es un miembro certificado, o la traza es de otro núcleo |
| `TRACE_PERSISTENCE_FAILED` | la traza no pudo guardarse |
| `INTERNAL_SHADOW_ERROR` | cualquier otro fallo dentro de la sombra |

- **Sin éxito sin calificar.** No existe un estado «éxito». Los estados son `COMPLETE` (todas las corridas
  llegaron al minuto del encuentro y no se informó nada), `COMPLETE_WITH_UNSUPPORTED_ACTIONS`, `PARTIAL`,
  `FAILED` y `REJECTED`. Un encuentro con un testigo requerido fallido nunca queda en `COMPLETE`.
- **Sin pérdida silenciosa.** Cada acción **reflejada** tiene exactamente una disposición: `BUILT`,
  `SKIPPED_NO_PHYSIOLOGY`, `DECLARED_GAP` o `APPLIED_AS_A_STOP`. Una acción soportada que no produjo ni un
  contribuyente ni un hueco declarado queda `UNACCOUNTED` y se informa como error interno. El defecto anterior
  del oxígeno (listado como mapeado y descartado por tres adaptadores) queda bajo prueba de regresión por esa
  vía, en todos los adaptadores. Dos filas más mantienen entera la línea de acciones: `FROM_ENGINE_STATE`, un
  contribuyente que la corrida lleva y que ninguna orden explica (la hemostasia de GI, leída de cuándo la hizo
  el motor), y `NOT_MIRRORED`, una orden que la sesión nunca reflejó.
- **Órdenes retenidas.** Una orden que el motor retiene hasta que llega un resultado no se refleja, y el motor
  puede ejecutarla después: la corrida de sombra **no lleva su efecto**. Ya era un hueco declarado antes de
  este ciclo; ahora además es una fila `NOT_MIRRORED` y el estado nunca queda en `COMPLETE`. Reflejar esa
  ejecución tardía no se construyó.
- **Falla cerrado.** Un código de estado que la capa no conoce, o un replay que no dice explícitamente que
  reproduce, nunca se leen como «nada».
- **Aislamiento entre testigos.** Una excepción inesperada en un testigo ya no corta a los testigos siguientes
  en ese turno ni se registra contra la sesión: es el fallo de ese testigo.

**Residuo declarado.** La visibilidad es de consulta: alguien abre el almacén o el informe; nada avisa. Un
almacén que no se puede escribir en absoluto queda registrado en la sesión y lo informa la herramienta, y en
ningún otro sitio.

**Veredicto: `SHADOW_FAILURE_VISIBILITY_VALIDATED`.**

## 6 · Auditoría de sensibilidad de los parámetros sintéticos (P3-151)

Sólo lectura y cálculo. La serie de seis vías del opioide en los tres testigos, fuera de línea, moviendo **un**
parámetro sintético a la vez sobre un adaptador de desarrollo; el adaptador registrado, el perfil comprometido
y el núcleo no se tocan. **Sólo se usaron valores que el repositorio ya tiene; ninguno se inventó.**

| Parámetro | Valores usados (origen) | ¿Hay intervalo defendible? | Hallazgo | Veredicto |
|---|---|---|---|---|
| Bandas de llegada | `lower` · `midpoint` · `upper` (los puntos declarados del mapeo de referencia certificado) | Sí | La cadena sin tratar y la cota de la región son las mismas en los tres puntos, salvo redondeo de coma flotante; todos los veredictos son iguales; sólo se mueven magnitudes de la rama tratada | `SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT` |
| Tasa de recuperación | 0,10 (comprometido) · 0,5 · 0,9 (sondas estructurales de las pruebas certificadas) | No: el repositorio no declara intervalo | En esos valores no cambia ningún veredicto, y la cota de la región no la lee. No se afirma nada entre ellos ni más allá | `SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION` |
| Tasa de profundización | 0,005 (comprometido) · 0,02 (sonda de recurrencia) · 0,03 (sonda de dirección de colapso) | No: la procedencia del propio adaptador dice que no hay intervalo declarado | **La cota superior de la región de transmisión es condicional a esta tasa** (ver abajo) | `SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION` |

**La cota y la tasa de profundización.** La cota sale de la rama sin tratar: es inversamente proporcional a la
subida de PaCO2 que la tasa produce en 60 minutos (producto cota × subida constante en los tres valores).

| Tasa de profundización | Cota superior de la región | Testigos dentro de la cota | Criterios de materialidad que cambian |
|---|---|---|---|
| 0,005 (comprometida) | 0,060621 | LOW, CENTER_REFERENCE, HIGH | — |
| 0,02 | 0,009010 | ninguno | dirección causal (especificidad del oxígeno en HIGH); intersección con la región |
| 0,03 | 0,004076 | ninguno | dirección causal (oxígeno en CENTER_REFERENCE y HIGH); frontera (la saturación toca su piso en HIGH); intersección con la región |

Se sostiene en todos los valores: la dirección y el minuto del efecto de la reversión (21 para una orden del
minuto 20), que esperar no es un tratamiento, que lo temprano supera a lo tardío, el contrato de ocho puntos en
el testigo central y el replay. En el testigo LOW no cambia ningún veredicto ni en la sonda más severa.
Derivada local en el punto comprometido: d ln(cota) / d ln(tasa) ≈ −1,16.

**Lo que NO se hizo, y la decisión que queda abierta.** FD-NEW-4 promueve un parámetro cuya incertidumbre puede
cambiar una frontera, y a la vez prohíbe inventar un intervalo. La tasa de profundización es material en las
sondas y no tiene intervalo declarado. **No se promovió**: el conjunto sigue teniendo una dimensión y tres
testigos. La región (0; 0,060621] debe leerse como la región **a la tasa de profundización comprometida**. O
la docencia declara un intervalo para esa tasa (entonces es `ENSEMBLE_REQUIRED` y la región se rederiva en
conjunto), o acepta la región como válida sólo en el punto comprometido.

**Veredicto: `SENSITIVITY_AUDITED_NO_PARAMETER_PROMOTED_ONE_DECISION_OPEN`.**

## 7 · Corrección del minuto del edema (P3-152)

Sólo el adaptador de **desarrollo fuera de línea**. El adaptador registrado sigue declarando el hueco y la
familia sigue sin estar en vivo.

- **Antes:** el tratamiento decongestivo empezaba en el propio minuto de la orden (con piso en 1).
- **Ahora:** empieza el minuto siguiente. Una orden que el motor ejecutó en el minuto m está por primera vez en
  el estado del minuto m + 1, como ya lo estaban el oxígeno y la reversión en vivo del opioide. Una regla de
  tiempo para toda orden mapeada.
- **La magnitud no cambió** (testigos 0,0025 · 0,005 · 0,01) **ni la fisiología común.** La corrida de hoy con
  la orden en el minuto 30 es, estado por estado, la de antes con la orden en el 31.

| | Primer efecto (orden en el 30) | Vuelta a la congestión de llegada: LOW · CENTER_REFERENCE · HIGH |
|---|---|---|
| Antes | minuto 30 | 79 · 55 · 43 |
| Ahora | minuto 31 | 81 · 57 · 44 |

No es exactamente un minuto en los testigos lentos: un minuto más de progresión sin tratar añade agua pulmonar
que la tasa más lenta tarda otro minuto en retirar. **Ningún veredicto del contrato de seis vías cambió** (los
ocho puntos, iguales); el error de tiempo no ocultaba otro problema. Cierra TD-133 (1).

**Veredicto: `PULMONARY_EDEMA_TIMING_CORRECTED_NO_VERDICT_CHANGE`.**

## 8 · Certificación adversarial integrada (P3-153)

Cubre: sombra en vivo de GI y de opioide, persistencia de la traza, replay, ciclo de vida de la sesión,
visibilidad de fallos, aislamiento del observador docente y el minuto del edema fuera de línea.

**Ataques, todos con prueba propia:** apertura repetida; turnos de cero minutos; acciones duplicadas; acciones
no soportadas; acción en la frontera exacta (una orden en el último minuto antes de que el motor detenga al
paciente); replay tras un fallo; traza de otra familia; linaje viejo; testigo ausente; llegada mutada.

**Secuencias aleatorias acotadas:** seis semillas fijas por familia, de 3 a 8 turnos tomados de un conjunto
fijo de órdenes reales (con turnos de cero minutos, duplicados y una orden no modelada). La misma semilla da la
misma secuencia. En cada una, con la sombra y el almacén encendidos frente a todo apagado: **estado heredado
idéntico, entradas de la puntuación idénticas, destino de cada orden idéntico, salidas visibles para el
residente idénticas**; una sola sesión para todo el encuentro; cada acción con su disposición; la traza
guardada se verifica y se reproduce corrida por corrida. `COMMON_CORE_RUNTIME_AUTHORITY = False`.

**Mutantes.** 35 mutaciones del comportamiento nuevo, fuera del repositorio (la regla vieja de sesión, la
elegibilidad reducida al reloj o a minutos enteros, cualquier estado como llegada, el almacén dentro del
repositorio o encendido por un secreto, un nombre de registro sin sanear, un testigo elegido, un testigo fallido
rellenado, el replay sin canales o sin linaje, la verificación sin coherencia interna, el listado que confía en
el registro, `COMPLETE` con un testigo fallido, una acción sin cuenta leída como omitida, una orden retenida
fuera de la línea de acciones, un fallo de persistencia callado o que levanta, el observador sin escapar o
cambiando su entrada, la envolvente con la corrida de la sesión, el edema fechado en la orden, entre otras):
**35 de 35 detectadas** por las dos suites nuevas.

**Comprobación visual del informe** (Chromium, claro y oscuro, y a ancho de teléfono): encontró y se corrigió
un defecto real — un testigo fallido en el minuto 1 se dibujaba con una guía que cruzaba todo el gráfico y se
leía como una trayectoria. Ahora es un anillo en su último minuto válido con su rótulo al lado, y hay una
prueba que lo fija.

**Revisión adversarial independiente** (un subagente de sólo lectura, sobre el candidato sin commitear, antes
de la certificación final):

Sólo lectura, sobre el árbol sin commitear; unos 30 minutos y 89 llamadas de herramienta.

**Se sostuvo.** Aislamiento en 1 200 secuencias sembradas (630 de opioide y 570 de GI, cuatro casos, de 1 a 10
turnos, con turnos de cero minutos, duplicados, órdenes no soportadas e ilegibles, y esperas hasta el minuto
264), cada una jugada apagada, encendida y encendida con el almacén: 3 600 encuentros con el registro
autoritativo, el estado, el destino de las órdenes, el minuto y el paro **idénticos en todos**. Ciclo de vida
en 500 semillas y 962 intentos por un mismo ayudante de página sin reinicio: ninguna sesión mapeada sobre un
estado tocado y ninguna conservada entre intentos tras dejar la llegada (21 reutilizaciones, todas dentro del
residuo declarado). La regla de elegibilidad no levantó en 790 estados malformados. Replay determinista en tres
procesos; el minuto efectivo coincide con el primer minuto que difiere en 32 de 32 casos. Los límites del
almacén, el observador de sólo lectura y su escapado (10 cadenas hostiles en cada campo, y Chromium sin red),
el edema (sólo cambia el minuto de inicio; el adaptador registrado es idéntico a la base en 88 casos) y que
ninguna prueba adaptada quedó más floja.

**Hallazgos: 5 medios, 12 bajos y 2 informativos.** Cada uno se confirmó antes de corregirlo y tiene prueba
propia (`test_p3o_r…`).

| | Sev. | Hallazgo | Qué se hizo |
|---|---|---|---|
| R1 | Media | Un testigo que falla **al abrir** dejaba la traza entera sin guardar (lo introdujo un cambio hecho durante la propia revisión) | Corregido: esa corrida queda en la traza como fallida y sin minutos; las demás siguen |
| R2 | Media | El nombre del archivo salía de campos de la traza sin validar: un caso con separadores de ruta podía escribir fuera del directorio del almacén | Corregido: nombre saneado y comprobación de que el archivo queda directamente dentro del almacén |
| R3 | Media | Una orden que el motor retiene hasta un resultado y ejecuta después nunca se refleja (rama anterior a este ciclo); la afirmación «toda acción ejecutada tiene una disposición» era más fuerte que el código | Corregido en parte: fila `NOT_MIRRORED` en la línea de acciones, el estado nunca es `COMPLETE`, y la afirmación del registro se estrechó a «toda acción **reflejada**». Reflejar la ejecución tardía no se construyó: TD-134 (3) |
| R4 | Media | Ediciones reselladas pasaban por `COMPLETE` y «replays exactly»: testigos intercambiados, los tres iguales al central, un testigo truncado, el estado reescrito | Corregido: la verificación comprueba la coherencia interna de la traza (cada corrida es la que su nombre dice y corrió el valor que su testigo declara; longitudes; el estado recalculado; las acciones contra el artefacto; las etiquetas). Doce ediciones reselladas bajo prueba. Una falsificación coherente en todas sus partes sigue fuera de alcance: no hay firma |
| R5 | Media | El digesto sólo se comprobaba dentro del replay: el listado y la vista sin replay mostraban el estado de un archivo editado | Corregido: el listado y toda vista verifican y dicen `NOT VERIFIED` |
| R6 | Baja | La segunda mitad del enganche de persistencia no estaba guardada: una respuesta del almacén que no fuera un diccionario levantaba dentro del encuentro | Corregido y probado con seis respuestas |
| R7 | Baja | Un archivo JSON malformado rompía el listado | Corregido: se lista como `UNREADABLE` |
| R8 | Baja | La herramienta decía «replay: exact» para una llegada rechazada | Corregido: «nothing to replay» |
| R9 | Baja | La página levantaba con `inf`, valores de texto o filas cortas; `<!--<script>` en un nombre dejaba muerta la capa interactiva (sin ejecución) | Corregido: sólo números finitos, filas normalizadas, y ningún `<`, `>` ni `&` en el bloque de datos |
| R10 | Baja | `heads()` ocultaba un intento terminado en un turno sin acción ejecutada | Corregido: cada registro nombra al anterior de su propia sesión |
| R11 | Baja | Colisión de identidad entre dos sesiones rechazadas distintas | Corregido: la identidad lee los mensajes de fallo y lo hallado en la llegada |
| R12 | Baja | «Una vez por razón» no valía si el mensaje llevaba el nombre del archivo | Corregido: una vez por clase de razón |
| R13 | Baja | Una tautología y una cláusula floja en las pruebas; dos bordes de las funciones de estado fallaban abiertos | Corregido: fallan cerrados, con prueba |
| R14 | Baja | Puntos ciegos de la elegibilidad, sólo con estados sintéticos | Corregido en parte: ahora lee la fracción de minuto, el historial de órdenes y la disposición, y exige una llegada redactada. El estado `hidden` y las claves de nivel superior desconocidas no tienen referencia redactada: declarado |
| R15 | Baja | Sólo en el arnés y dentro del residuo declarado: si los identificadores de orden se repiten entre intentos, una acción del segundo intento se omite | Declarado con precisión; la página usa identificadores únicos |
| R16 | Info | La hemostasia de GI es un contribuyente de la corrida sin fila en la línea de acciones | Corregido: fila `FROM_ENGINE_STATE` |
| R17 | Baja | Escritura no atómica: un registro truncado bloqueaba su identidad | Corregido: se escribe entero o nada |
| R18 | Info | Costo por turno con el almacén: opioide 74 ms (minuto 7) → 201 ms (minuto 99, turno 21); GI 34 ms → 131 ms (minuto 240, turno 45). Apagado: 0,01–0,05 ms. Un encuentro: 21 registros y 4,08 MB (opioide), 45 y 5,74 MB (GI) | Declarado: TD-134 (5) |
| R19 | Baja | `write_report` levantaba si el destino era un directorio | Corregido: devuelve el motivo |

**Incidencias de proceso.** (1) El candidato se editó mientras la revisión corría (cinco momentos); uno de esos
cambios introdujo R1. La revisión re-ejecutó cada hallazgo contra el último estado que vio, y cada uno se
volvió a comprobar después de corregirlo. (2) Las sondas de la revisión escribieron tres archivos **fuera de su
carpeta y fuera del repositorio** (trazas sintéticas de casos del banco), por rutas mal contadas; el entorno
bloqueó su borrado y no se borraron en su nombre: quedan a decisión de quien administra el entorno. (3) Una
ejecución de `git status --ignored` con la salida filtrada: nada bajo `validation/` se mostró ni se leyó.

**Certificación final, una sola, sobre el candidato estable:**

- **Candidato:** rama `phase-3-runtime-integration`, base `1e18594`, árbol de trabajo con huella
  `c5bf2631e3167a38…` (HEAD + diff + archivos nuevos), **idéntica al empezar y al terminar** la corrida.
- **Conjunto de certificación:** 50 archivos de prueba (la capa de la Fase 3, las series de manejo y las
  pruebas que leen documentos y registros): **1 446 aprobadas, 0 fallidas, 0 omitidas**. Uno de los 50
  archivos (`test_core_certification_preview.py`) no recoge pruebas, igual que en la base.
- **Las dos suites nuevas:** `test_shadow_observability.py` 92 y `test_shadow_sensitivity.py` 16.
- **Regresiones:** 56 de 56 activas aprobadas; 10 retiradas (las que el propio ejecutor declara).
- **Sin tocar:** `clinical_core/`, `app.py`, `pilot_acceptance.py`, `family_engine.py`,
  `runtime_authority.py`, `runtime_authority_store.py`, `runtime_shadow_evidence.py`, `CLAUDE.md` y
  `validation/` son byte a byte los de `1e18594`.
- **No se corrió:** la suite completa del repositorio ni la de la enmienda de la Fase 2 (80 a 112 minutos):
  `clinical_core/` no cambió, así que su resultado sobre código equivalente sigue vigente.
- Después de esta corrida sólo se añadieron esta sección y dos filas del Decision File; las pruebas que leen
  esos dos documentos se repitieron.

## 9 · Las nueve compuertas, releídas (P3-154)

| Compuerta | Antes | Ahora | Lo que falta |
|---|---|---|---|
| Exposición en tiempo de ejecución | `BLOCKED` | `BLOCKED` | no hay instantánea aprobada; la autoridad es, por diseño, sólo presión de GI |
| Exposición en la interfaz | `BLOCKED` | `BLOCKED` | nada de cara al residente está construido ni diseñado; **un observador docente no la pone en verde** |
| Captura de traza | `PARTIAL` | `GREEN` | — (alcance: entornos docentes y de desarrollo; un almacén duradero para un piloto desplegado no está diseñado) |
| Aislamiento de la puntuación | `GREEN` | `GREEN` | — |
| Flujo de revisión docente | `PARTIAL` | `PARTIAL` | el informe es una herramienta fuera de la app y no registra decisiones docentes; siguen abiertas las decisiones de los paquetes anteriores y la de la tasa de profundización |
| Selección de casos | `NOT_YET_EVALUATED` | `NOT_YET_EVALUATED` | una selección docente, tras revisión |
| Visibilidad de fallos | `PARTIAL` | `GREEN` | — (alcance: de consulta; nada avisa) |
| Vuelta atrás | `GREEN` | `GREEN` | — |
| Seguridad frente al residente | `BLOCKED` | `BLOCKED` | sin transición terminal ni mapeo de consciencia; regiones de desarrollo |

Tres preguntas, sin mezclar:

- **Preparación del motor de simulación:** `LIVE_SHADOW_OBSERVABLE_PERSISTENT_AND_REPLAYABLE_FOR_DEVELOPMENT`.
  No se añadió ni cambió fisiología.
- **Preparación de la revisión docente:** `READY_FOR_FACULTY_REVIEW_OF_SHADOW_TRACES_IN_DEVELOPMENT`. Es una
  herramienta de desarrollo, no una pantalla de la app; no captura decisiones.
- **Preparación de despliegue con residentes:** **`NOT_READY_FOR_RESIDENT_PILOT_REVIEW`** (4 verdes, 1
  parcial, 3 bloqueadas, 1 sin evaluar). Las tres bloqueadas son las mismas que antes.

## 10 · Hoja de ruta (P3-155)

Bloqueadores restantes, ordenados por criticidad para el piloto y, a igual criticidad, por costo de
arquitectura más riesgo y luego por valor educativo (0 a 3). El orden no es el camino: el camino respeta de
qué depende cada uno.

| # | Bloqueador | Criticidad | Costo de arquitectura | Valor educativo | Riesgo | Qué necesita |
|---|---|---|---|---|---|---|
| 1 | Decisiones docentes abiertas sobre lo que ahora es revisable: las dos regiones de desarrollo, las tasas sintéticas (sobre todo el intervalo de la tasa de profundización) y los paquetes anteriores | 3 | 0 | 2 | 0 | una sesión de revisión docente sobre trazas guardadas; sin código |
| 2 | No hay diseño de cara al residente para una lectura del núcleo común | 3 | 2 | 3 | 2 | una decisión de diseño, después de decidir la autoridad |
| 3 | No hay instantánea aprobada por la docencia: ni autoridad ni exposición | 3 | 1 | 1 | 3 | una aprobación docente que depende de las filas 1 y 4 |
| 4 | El núcleo común no tiene transición terminal ni mapeo de consciencia | 3 | 3 | 2 | 3 | una enmienda del núcleo común, que este ciclo no estaba autorizado a hacer |
| 5 | Ningún caso seleccionado para un piloto posterior | 2 | 0 | 2 | 0 | una selección docente, informada por la sesión de revisión |
| 6 | El informe docente es una herramienta fuera de la app y el almacén es un directorio de desarrollo | 1 | 2 | 1 | 1 | sólo si la docencia pide revisión dentro de la app o un almacén desplegado |
| 7 | ACS no tiene mapeo de llegada en vivo | 1 | 2 | 2 | 2 | semántica de llegada redactada para seis variantes; no autorizada y fuera del camino crítico |
| 8 | Más familias de fisiología (tratamiento del asma, embolia) | 0 | 3 | 2 | 2 | fisiología nueva; fuera del camino crítico y **no** el paso siguiente por omisión |

**Camino crítico más corto recomendado:**

1. Una **revisión docente de trazas guardadas** de GI y de opioide con el informe, para decidir las regiones y
   las tasas sintéticas (incluido si la tasa de profundización recibe un intervalo). No necesita código.
2. Una **decisión docente** sobre si autorizar el trabajo de transición terminal y consciencia en el núcleo
   común, que es de lo que depende la seguridad frente al residente.
3. Sólo entonces, instantánea aprobada, autoridad y diseño de cara al residente.

El paso siguiente **no** es otra familia de fisiología. Esto es una recomendación de diseño, no una selección.

## 11 · Límites declarados

- **Sin fisiología nueva y sin validación clínica.** Las regiones son de desarrollo; los testigos son de
  prueba; ninguno es «el valor».
- La región de transmisión del opioide es la región **a la tasa de profundización comprometida** (§6).
- El observador es una herramienta fuera de la app. No hay pantalla docente dentro de la app, ni control de
  acceso más allá de quién puede ejecutar la herramienta y leer el directorio.
- El almacén es un directorio nombrado por el entorno: sin política de retención, sin almacenamiento duradero
  para un despliegue, integridad por digesto y coherencia interna y no por firma. Un registro por turno, cada
  uno con toda la historia: medido por la revisión, de 74 a 201 ms por turno de opioide (minuto 7 a 99) y de 34
  a 131 ms por turno de GI (minuto 1 a 240) con el almacén encendido, y unos 4 MB por encuentro de opioide de
  21 turnos y 5,7 MB por uno de GI de 45. Apagado, que es lo normal: 0,01 a 0,05 ms por turno.
- Una orden retenida hasta un resultado y ejecutada después por el motor no entra en la corrida de sombra (§5).
- La serie en vivo se jugó con `pilot_acceptance.Encounter`, la rama de familias del camino de órdenes de la
  página sin Streamlit, y con una emulación de las tres sentencias del ayudante de sesión de la página, fijadas
  por prueba. La página en un navegador no se ejercitó en este ciclo.
- El residuo del ciclo de vida de §2 y el de visibilidad de §5.
- El opioide sigue sin golden y el núcleo común sin transición terminal (TD-133 (5) y (6), sin cambio).
