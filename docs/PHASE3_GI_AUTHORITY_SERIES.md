# Fase 3 · P3-46 a P3-51 · Serie de validación de autoridad GI en desarrollo

Rama `phase-3-runtime-integration`, desde `2f1624b`. Cierre de la Fase 2 `d2cca46`, digesto
`22b90a6f…6ce6a`, **sin cambios**. Instantánea `gi_pressure_committed`, aprobada **sólo** para el
experimento de desarrollo: `DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY`, no validada clínicamente, no aprobada
para producción, no aprobada para residentes.

**Lo que este documento no dice:** que ninguna magnitud sea clínicamente válida. Lo validado es software
y estructura causal. El éxito técnico no establece calibración clínica.

## 1 · P3-46 · Reparación de procedencia

### 1.1 El orden real del tiempo de ejecución, auditado

```
apertura del turno (order_pipeline.open_turn)   -> las órdenes existen, con su identidad canónica
captura de la sombra (shadow.capture)
ejecución del motor (execute_bundle)            -> decide qué acciones corrieron
observación de la sombra (shadow.observe)
MINUTO DE AUTORIDAD (authority.minute)          -> captura, computa, valida, compromete la presión
order_pipeline.settle                           -> aquí, y sólo aquí, cada orden recibe su FATE
PROCEDENCIA (authority.settle_provenance)       -> identidad y fate canónicos, ya existentes
ledger_record / render / persistencia
```

La identidad de la orden ya existe cuando corre el minuto; **el fate no**. Por eso el sitio recibía
`run_actions`, que son acciones y no órdenes del libro, y el artefacto guardaba la clase con
`order_id` y `fate` vacíos.

### 1.2 La arquitectura mínima elegida

**Separar la procedencia del compromiso, sin mover el compromiso.** El minuto de autoridad sigue
exactamente donde estaba, antes de la liquidación, así que ninguna acción se activa un minuto antes o
después y la trayectoria, el contrafáctico y lo que vería un residente no cambian. Lo que se finaliza
después es el registro: `settle_provenance(submission_id, órdenes liquidadas)`, llamado donde `app.py`
llama a `order_pipeline.settle`, un enunciado después.

No se duplicó lógica de fate. El sitio **lee** `order_ledger.snapshot` y **lee**
`order_ledger.NOT_ACTED`; no decide ni infiere ninguno. Los campos que copia son los del libro:
`order_id`, `submission_id`, `class`, `fate`, `reason`, `executed_at_min`.

El orden está fijado por AST en `test_runtime_authority_site.py::test_d3`: dos bloques
`_authority is not None`, con exactamente una liquidación entre ellos.

### 1.3 Lo que la procedencia liquidada permite comprobar

| Guarda | Qué hace |
|---|---|
| Fate que no actuó | si toda orden liquidada de una clase que el minuto consumió tiene un fate de `order_ledger.NOT_ACTED`, es una contradicción: el experimento **se detiene**, visible, y el minuto ya comprometido **no se reescribe** |
| Clase no soportada | si el libro liquidado del turno trae una clase que el mapeo común no puede representar, la decisión docente C hace el encuentro inelegible y el experimento **se detiene** (§3.2) |
| Clase sin orden de su envío | **no** es contradicción: se registra como nota y no se concluye nada (§5.1) |

### 1.4 La fila de elegibilidad

`open_site` adjunta un registro inmutable de **17 campos** construido con **la misma** decisión del
portón que abrió el sitio: clasificación, familia, caso, dominio, instantánea, entorno, estado del
piloto con sus marcas, acciones no soportadas, digesto de la Fase 2, versión de la capa, almacén
configurado, resultado de la lista, concesión, las **nueve** condiciones, los motivos y el momento de la
decisión. No es una segunda lectura ni prosa. `eligibility_is_consistent` la compara contra el artefacto
en que viaja, y mutar cualquiera de las nueve condiciones la vuelve inconsistente —probado condición por
condición—.

### 1.5 Pruebas

`test_runtime_authority_provenance.py`, **13 pruebas**: A1 identidad canónica, A2 fate liquidado, A3 una
acción que no actuó no se consume como tratamiento, A4 fila presente, A5 fila idéntica al portón, A6 la
trayectoria no cambia —fijada contra lo que P3-41 midió **antes** de la reparación—, A7 ninguna acción se
activa antes o después, A7b una corrida sin el paso de procedencia tiene la misma trayectoria campo por
campo, A8 el replay valida identidad y fate, A9 la sombra no cambia, A10 ninguna superficie de puntuación
es alcanzable, A11 el piloto sigue rechazado, A12 el digesto de la Fase 2 no se movió.

**Veredicto: `AUTHORITY_PROVENANCE_COMPLETE`.**

## 2 · P3-47 · Parada dura real

**Condición elegida:** una acción no soportada, la clase de fallo determinista que la decisión docente C
ya declara, con el guion de vasopresor **del propio repositorio**. Nada sintético, nada corrompido, nada
de la fisiología congelada tocado.

**Curso:** un turno limpio de reevaluación (30 minutos de hemorragia sin tratar) que **compromete**, y
después el guion de norepinefrina.

| | `gi_bleed_57m` | `gi_bleed_72f` |
|---|---|---|
| Minutos de autoridad comprometidos antes del fallo | **1** (SBP 80) | **1** (SBP 89) |
| Minuto que falla | compromete **nada** | compromete **nada** |
| Motivo | `UNSUPPORTED_AUTHORITY_ACTION: ['norepinephrine']` | igual |
| Estado | `HALTED` | `HALTED` |
| Trayectoria mixta | **declarada** | **declarada** |
| Regreso silencioso al legado | ninguno | ninguno |
| Compromiso posterior | imposible: el sitio detenido no se reconstruye | igual |
| Artefacto | 30/30 campos, digesto verificado | igual |
| Contrafáctico legado | preservado | preservado |
| Procedencia del minuto comprometido | 1/1 coherente | 1/1 coherente |
| Replay desde el archivo | exacto en el minuto comprometido, y la transición de parada reconstruida | igual |
| Coste | 0,48 s | 0,16 s |

**Veredicto: `REAL_DEVELOPMENT_HARD_FAIL_VALIDATED`.**

## 3 · P3-48 · La serie multiescenario

Las dos baterías de aceptación completas, un sitio de autoridad por encuentro, con el minuto dentro del
turno y la procedencia después de la liquidación. La batería juega sus propios guiones.

### 3.1 Resumen

| | |
|---|---|
| Escenarios | **34** (17 por caso, los dos casos certificados) |
| Elegibles por la lectura certificada | **26** |
| Intentados | **34** (los 8 inelegibles como controles de rechazo) |
| Completados | **26** |
| Detenidos | **8** |
| Minutos de autoridad comprometidos | **66** (64 en los completados, 2 antes de una parada) |
| Minutos abortados | **12** |
| Procedencia liquidada y coherente | **26 de 26** completados, en **todos** sus minutos |
| Replay exacto en cada minuto comprometido | **34 de 34** escenarios |
| Digesto verificado | **34 de 34** |
| Fila de elegibilidad coherente | **34 de 34** |
| Campos de artefacto faltantes | **ninguno** |
| Clase de divergencia observada | `EXPECTED_ARCHITECTURAL_DIVERGENCE`, y sólo ella |
| Coste | **8,4–9,1 s** por caso; artefacto 17–108 KB; replay de los 36 experimentos del almacén en segundos |

### 3.2 El hallazgo HIGH de la serie, y su cierre

`H_unexpected_reasonable` es `INELIGIBLE_UNSUPPORTED` en la lectura certificada —por una orden
`not_modelled`— y **en vivo comprometía un minuto de autoridad**. La razón es estructural: una orden que
el motor no **modela** no produce acción para el turno, así que `run_actions` nunca la lleva y el sitio
nunca la vio. La lectura de evidencia la ve porque mira las clases **liquidadas**; el camino en vivo no
las tenía.

La reparación de P3-46 pone esa información al alcance: el libro liquidado del turno es el único lugar
donde la clase aparece, y ahora aparece ahí. El sitio aplica el **mismo** `unsupported_among` que aplica
la lectura de elegibilidad, y el encuentro se detiene. Después del cierre:

**8 inelegibles por la lectura certificada = 8 detenidos en vivo, escenario por escenario, sin
excepciones en ninguna dirección.**

Límite declarado: la información sólo existe **después** de la liquidación, así que en estos dos
escenarios el minuto ya se había comprometido. El resultado es el que la decisión F prescribe para un
fallo descubierto después de un compromiso: el minuto se preserva como ocurrió, la trayectoria mixta se
declara y nada más se compromete.

### 3.3 Diversidad del manejo

| | |
|---|---|
| Completados con al menos un tratamiento | **16** de 26 |
| Completados de sola observación o reevaluación | **10** |
| Clases en los completados | reevaluación 26, cristaloide 14, PPI 14, sangre 12, consulta 12 |
| Completados con ≥3 minutos de autoridad | **12** |
| El más largo | 8 minutos de autoridad (`terminal_deterioration`) |
| Clases en los rechazos | norepinefrina, anticoagulación, antiagregante, `not_modelled` |

### 3.4 Aceptación estructural

Los 26 completados cumplen las diez condiciones: portón válido, ninguna acción no soportada, ninguna
frontera no resuelta, ningún fallo de invariante, todos los compromisos atómicos sobre `sbp`, `dbp` y
`map`, procedencia completa, artefacto persistido, replay exacto, ninguna fuga de propiedad y ninguna
contaminación de puntuación ni de piloto. **Ningún umbral clínico numérico.**

**Veredicto: `GI_DEVELOPMENT_AUTHORITY_SERIES_COMPLETE`.**

## 4 · P3-49 · Replay y reproducibilidad

**Replay en un proceso nuevo**, que sólo abre los archivos del almacén y en el que se comprueba que
`pilot_acceptance` y `runtime_shadow_families` **no están cargados**: 36 experimentos, 160 registros,
**36 de 36** con digesto verificado, identidad coincidente y fila de elegibilidad coherente; 30 con
«every committed minute reproduces» y 6 sin minuto comprometido que reproducir (los rechazos que no
llegaron a comprometer). Ningún replay necesitó estado vivo.

**Reproducibilidad:** dos series independientes, en procesos distintos y almacenes distintos.
**0 diferencias** en 16 campos por escenario —parada, compromisos, minutos, trayectoria, contrafáctico,
clases de divergencia, clases de acción, fates, identidades de orden, procedencia, veredicto de replay—
sobre los 34 escenarios. Sólo difieren las identidades de experimento y de artefacto, que son la
identidad del intento.

**Veredicto: `AUTHORITY_SERIES_REPLAY_AND_REPRODUCIBILITY_READY`.**

## 5 · P3-50 · Revisión adversarial de la serie

| Ataque | Clase | Resultado |
|---|---|---|
| El fate se registra después y no es causal | `NOT_A_DEFECT` | el fate **nunca** alimenta la fisiología: el candidato y la presión se calculan antes de que exista. Sí es causal para la **parada**, que es su propósito |
| Fila de elegibilidad inconsistente con el portón | `NOT_A_DEFECT` | se construye con la misma decisión; mutar cualquiera de las nueve condiciones la vuelve inconsistente, probado una por una |
| El replay usa estado vivo por accidente | `NOT_A_DEFECT` | proceso nuevo, con la ausencia de los módulos de ejecución comprobada |
| Una acción duplicada entre legado y común | `NOT_A_DEFECT` | ningún `order_id` repetido en 160 artefactos; la autoridad no ejecuta acciones, sólo escribe presión |
| **Escenario elegible con una acción hermana no soportada** | **`HIGH`, corregido** | el hallazgo de §3.2: cerrado, y las dos lecturas coinciden 8 = 8 |
| **El almacén guardaba la versión previa a la liquidación** | **`MEDIUM`, corregido** | reescribir la misma identidad con otro contenido es una colisión, así que el registro durable no llevaba la procedencia. La etapa de liquidación entra en la identidad: dos registros inmutables por minuto, el de lo que se sabía al escribir la presión y el de lo que se sabía con los fates, y `records()` dice cuál es cuál |
| La parada se ejerció fuera del sitio de producción real | `MEDIUM`, **declarado** | la parada corrió por `site.minute` y `settle_provenance`, que son las entradas de producción, en la secuencia de producción; el cableado de Streamlit lo cubre la suite de AppTest y **no** se condujo en vivo para la parada |
| La segunda corrida hereda estado | `NOT_A_DEFECT` | procesos y almacenes separados, 0 diferencias, identidades distintas |
| Los éxitos concentrados en una clase trivial | `LOW` | 16 de 26 llevan tratamiento, 12 tienen ≥3 minutos de autoridad, el más largo 8; 10 son de sola observación, lo que es la mitad baja del espectro y queda dicho |
| Artefacto sin procedencia de tratamiento | `NOT_A_DEFECT` | cada minuto lleva identidad y fate canónicos; 26/26 coherentes |
| Fuga al residente o a la puntuación | `NOT_A_DEFECT` | ninguna clave de rúbrica, radar, penalidad, competencia o puntaje global en 160 artefactos; las claves de cabecera son exactamente las declaradas |
| Contaminación del piloto | `NOT_A_DEFECT` | rechazado por bandera y por las marcas de su propia congelación; la fila de elegibilidad lo registra |
| Éxito estructural presentado como validez clínica | `NOT_A_DEFECT` | el registro lleva su propio `not_established`, y este documento lo dice en su encabezado |

**Un defecto de mi propio arnés, encontrado y corregido:** una lista de envíos compartida entre
encuentros emparejaba el turno de uno con el libro de otro, lo que producía una contradicción y una
parada **espurias** mientras la autoridad se comportaba. La contabilidad se indexa ahora por sesión, que
es lo que `observe` recibe. Lo cuento porque las cifras de una serie dependen tanto del arnés como del
código que mide.

### 5.1 La rama que bajé de contradicción a observación

La guarda tenía una tercera rama: «el minuto registró esta clase y el libro liquidado de su envío no
trae ninguna orden de ella». En dos encuentros reales resultó **falsa**: hay turnos cuyas clases
ejecutadas y cuyas órdenes abiertas difieren legítimamente —un paquete que el pipeline divide, una orden
abierta en un turno anterior que se ejecuta después—, así que una clase sin orden del mismo envío **no**
demuestra que la acción no actuó. La bajé a nota registrada y **no concluyo nada de ella**. Las dos
guardas que sí protegen —fate que no actuó, clase no soportada— quedan intactas.

Esto es lo único que no queda cerrado en la procedencia, y es la razón del veredicto de §6.

### 5.2 Lo que la certificación completa encontró, y que no era de este ciclo

La suite completa —10 870 pruebas en cuatro particiones— dio **una** falla:
`test_offline_cases::test_no_key_resolver_bypasses_the_offline_rule`. **Falla igual en la base**
`2f1624b`, así que es previa a este ciclo: entró con `469f0a0` (P3-11) y ninguna certificación
posterior corrió ese archivo.

Es un **falso positivo de la guarda**, no una fuga. La guarda busca el idioma de los resolvedores de
secretos del repositorio en el cuerpo de cada función y exige que llamen a `withhold(`. De las diez
funciones que marcaba, nueve son resolvedores reales y las nueve lo llaman; la décima,
`runtime_shadow_evidence.shadow`, es un gestor de contexto que salva y restaura **dos banderas de
proceso** cuyos nombres son constantes de módulo, y caía sólo porque llamaba `name` a su variable de
bucle.

**La guarda no se tocó.** Exigir un parámetro `name` de primer nivel la habría debilitado, porque
`tools_image_bank._budget` cae por un resolver **anidado** y la guarda lo cubre a propósito. Lo que
cambió es el código, que ahora dice lo que hace: la variable se llama `flag`. El predicado sigue
cubriendo los nueve resolvedores reales —y lo demostró atrapando el primer comentario que escribí
para explicar el cambio, porque citaba el idioma literal—.

## 6 · P3-51 · Auditoría de madurez

| | Punto | Estado |
|---|---|---|
| 1 | Completitud de la procedencia | **cerrada para todo minuto comprometido de todo escenario certificado**; queda la nota de §5.1, no explicada |
| 2 | Corrección de la elegibilidad | cerrada: la lectura certificada y el camino en vivo coinciden 8 = 8 |
| 3 | Cobertura del camino de éxito | 26 de 26 elegibles, los dos casos, 64 minutos de autoridad, hasta 8 por encuentro |
| 4 | Cobertura del camino de fallo | **tres rutas de parada en vivo**: acción no soportada en el primer turno (6 escenarios), acción no soportada después de un compromiso (P3-47, 2 casos), clase no modelada después de un compromiso (2 escenarios) |
| 5 | Replay | exacto, desde el artefacto y nada más, en proceso nuevo |
| 6 | Reproducibilidad | 0 diferencias entre dos series independientes |
| 7 | Diversidad de escenarios | 5 clases de manejo en los completados; 16 con tratamiento, 10 de observación |
| 8 | Integridad del artefacto | 160 registros verificados, 30/30 campos, claves exactamente las declaradas |
| 9 | Observabilidad docente | la superficie dibuja desde `authority_status`; cubierta por sus pruebas certificadas, no reconducida este ciclo |
| 10 | Aislamiento de la autoridad | sólo `sbp` y `dbp` comunes, `map` derivado; nada más comprometido en 66 minutos |
| 11 | Aislamiento del piloto | rechazado por las dos vías, y declarado en cada artefacto |
| 12 | Aislamiento de la puntuación | ninguna superficie alcanzable, probado por AST y por inspección de los 160 artefactos |
| 13 | Incertidumbre fisiológica restante | **sin cambio**: cinco de las siete magnitudes no quedan determinadas por evidencia de GI, y no hay calibración clínica |

### Veredicto

> **B. `ONE_MORE_TECHNICAL_PACKAGE_REQUIRED`**

Doce de los trece puntos quedan cerrados, y la serie cumple lo que el encargo pedía: procedencia,
parada real, 26 escenarios, replay y reproducibilidad. Lo que falta es pequeño y concreto, y es el
punto 1: la nota de §5.1. Hay una forma de encuentro, reproducible, en la que la procedencia de un
minuto comprometido no se puede emparejar con el libro de su envío, y elegí **registrarla en vez de
concluir nada**. Mientras eso siga sin explicación, llamar a la serie «validada» sería decir más de lo
que medí. Es un paquete técnico, no una decisión clínica.

### Paso siguiente recomendado

**Primario: explicar y cerrar el emparejamiento de la procedencia** —qué turno abre una orden que otro
ejecuta, cómo se liga canónicamente una acción ejecutada con su orden cuando no comparten envío— y, con
eso cerrado, volver a correr la serie y emitir el veredicto A. Es barato, no toca fisiología y no pide
ninguna decisión docente.

| | Alternativa | Por qué no primero |
|---|---|---|
| 2 | Calibración clínica de la presión | único camino a una afirmación clínica, pero necesita material y decisiones que no existen |
| 3 | Tratamientos GI no soportados | desbloquea los 8 rechazos, pero es fisiología nueva y decisión clínica |
| 4 | Añadir CRT al dominio | amplía el alcance antes de cerrar el actual |
| 5 | Autoridad en vivo en otra familia | ninguna otra tiene su sombra en vivo lista, y `afterload_sensitivity` sí actúa ahí sin estar identificado |
| 6 | Planificación del piloto | prohibido hoy, y prematuro sin calibración |

**Límite duro:** aun con todo en verde, no se habilita autoridad en producción ni visible al residente,
no se modifica el primer piloto, no se amplía más allá de la presión GI, no se añade CRT, no se
implementa fisiología de tratamiento no soportada y la instantánea **no** queda declarada clínicamente
validada.
