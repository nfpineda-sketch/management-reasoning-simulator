# Fase 3 · Titulación y suspensión de norepinefrina por la vía común de tono vascular (P3-424 a P3-437)

> **Nota 2026-11-19 (revisión de titulación):** las trayectorias de titulación de la hemorragia digestiva que este documento deja listas para revisión humana tienen ya su revisión interactiva (`docs/PHASE3_NOREPINEPHRINE_TITRATION_REVIEW.md`, FD-TITREV-01 a FD-TITREV-13): cinco escenarios (aumento, reducción, suspensión, secuencia y reinicio), sólo capa de UX. **La revisión humana no se hizo.** Las frases de este documento sobre una revisión humana pendiente siguen siendo ciertas y **no se editan**.

Encargo del 2026-11-18; cerrado el 2026-11-19. Rama `phase-3-runtime-integration`; linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`); instantánea `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1` ratificada sólo para desarrollo; la norepinefrina sigue **fuera** de la autoridad viva.

**Esto es semántica de órdenes en la sombra de desarrollo. No cambia fisiología, constantes del tono, acoplamiento con la poscarga, autoridad, puntuación ni el primer piloto; no edita `clinical_core/`; no es validación clínica ni calibración.** Convierte la norepinefrina de «un inicio a tasa fija para siempre» en una intervención de manejo que se puede iniciar, aumentar, disminuir y suspender, por la **misma** vía: escritor de norepinefrina → soporte vasoconstrictor común → tono `T`.

## 0 · Decisiones docentes (2026-11-18; FD-TITRATE-01 a FD-TITRATE-13)

| Decisión | Contenido |
|---|---|
| **FD-TITRATE-01** | Se autoriza la capacidad de manejo siguiente: START, INCREASE, DECREASE y STOP de norepinefrina. |
| **FD-TITRATE-02** | Todas las operaciones actúan por la **misma** vía existente (`vascular_support.Norepinephrine` → soporte vasoconstrictor → `T` común). Sin segundo escritor de `T`, sin efecto directo fármaco → mmHg, sin reglas de presión por caso. |
| **FD-TITRATE-03** | La fisiología ratificada del tono queda **congelada**: `tone_gain` 0,6; `half_effect_rate_mcg_min` 10,0; `onset_tau_min` 1,5; `offset_tau_min` 2,5; acoplamiento con la poscarga sin tocar. |
| **FD-TITRATE-04** | Un cambio de tasa altera el soporte objetivo de forma continua, por la dinámica existente. Prohibido el salto instantáneo de presión por haber cambiado la dosis. |
| **FD-TITRATE-05** | STOP no borra el soporte al instante: usa la dinámica de cese ya definida y decae causalmente. |
| **FD-TITRATE-06** | Sólo tasas absolutas fijas en **mcg/min**. Sin mcg/kg/min, sin conversión por peso, sin algoritmos de titulación, sin protocolos de PAM objetivo, sin lazo cerrado. |
| **FD-TITRATE-07** | Una orden posterior **reemplaza** la tasa activa en su momento efectivo: una sola historia de infusión coherente, sin flujos duplicados simultáneos. |
| **FD-TITRATE-08** | Órdenes repetidas con la misma tasa: idempotentes o clasificadas explícitamente, nunca contadas dos veces. |
| **FD-TITRATE-09** | Cronología imposible, unidades no soportadas, tasa negativa o semántica mal formada: **fallo cerrado**. No se adivina. |
| **FD-TITRATE-10** | `HYPERTENSIVE_PULMONARY_EDEMA_NOREPI` se formaliza como `NEGATIVE_CONTROL_MANAGEMENT_SCENARIO`; no se altera su fisiología. |
| **FD-TITRATE-11** | `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` sigue abierta: no bloquea la titulación; sí bloquea la promoción educativa en familias limitadas por la bomba. |
| **FD-TITRATE-12** | `CONSCIOUSNESS_UNDER_TONE_UNRESOLVED` sigue abierta: no se expone ni se deriva consciencia visible al residente desde la presión con soporte activo. |
| **FD-TITRATE-13** | No se requiere revisión de sensibilidad LOW/HIGH; no se reabre la calibración del tono. |

## 1 · P3-424 · Auditoría de la semántica actual de órdenes (sólo lectura) — veredicto **B · `SMALL NOREPINEPHRINE EVENT ADAPTER_REQUIRED`**

| Aspecto | Hallazgo |
|---|---|
| Tipo de acción | `norepinephrine` (`family_parser`), con operación `start` / `adjust` / `continue` / `stop`. «Aumentar» y «disminuir» se leen como `adjust` con **una** tasa absoluta objetivo; un cambio relativo («subir en 5») o dos tasas en una orden reciben una aclaración y no se ejecutan. |
| Tasa y unidades | `rate` con `units` `mcg/min` o `mcg/kg/min` (`family_engine` valida 0,001–100 mcg/min o 0,001–1,5 mcg/kg/min). Un `stop` no necesita ninguna y puede llevar ambas («stop norepinephrine 10 mcg/min»): es una suspensión. Un `adjust` o un `continue` pueden **escribirse** sin unidades o sin tasa: el motor los completa desde la infusión en curso (`active_order_context`) antes de ejecutarlos. |
| Órdenes que no nombran el fármaco | «Stop the infusion» y «Increase the infusion rate to 20 mcg/min» se interpretan como otro tipo de acción, `infusion_adjustment`, que el motor **resuelve** a la única infusión en curso entre norepinefrina, nitroglicerina y dobutamina (y rechaza si no hay ninguna o hay más de una). |
| Lo que entrega el espejo | La acción **interpretada, tal como se escribió**, antes de que el motor la resuelva o la complete, con el recibo del motor emparejado por el tipo interpretado. Una orden de norepinefrina trae en su recibo la orden asentada por el motor; una orden que no nombra el fármaco llega como `infusion_adjustment` con el recibo **vacío**: nada en ella dice qué infusión cambió el motor. |
| Defecto heredado encontrado y **no tocado** | «Titrate norepinephrine to MAP 65» se interpreta como un ajuste a tasa 65 sin unidades, y el motor heredado lo ejecuta como **65 mcg/min** cuando hay una infusión en curso. Está fuera de este paquete; se informa. |
| Estado del motor | **Una** tasa absoluta activa por infusión (`family_state["norepinephrine"]`): cada orden ejecutada la reemplaza y un `stop` la pone en 0. Una tasa por peso la convierte el motor con el peso del caso. |
| Minuto | El espejo fecha la orden en el minuto del estado desde el que se dio (`sim_time` antes del turno). Una orden retenida se fecha en el minuto en que el motor la ejecutó. |
| Identidad y duplicados | Un id de sombra por (minuto, turno, posición, tipo) y el id del libro mayor; el mismo turno observado dos veces se refleja una vez; el mapeo cuenta un id una vez. |
| Órdenes diferidas | Una orden retenida hasta un resultado se refleja sólo cuando el motor la ejecuta; una que nunca corrió no se refleja. |
| Persistencia y serialización | La sesión conserva las acciones reflejadas; el artefacto de replay guarda la identidad de cada acción (nunca el texto del residente) y los contribuyentes del escenario como datos planos. |
| Replay | Cada avance recalcula desde la llegada con lo reflejado hasta entonces; un contribuyente que cambie un minuto ya registrado se rechaza (`HistoryRewritten`); el artefacto se repite por la misma función. |
| **Lo que faltaba** | El mapeo de desarrollo sólo construía el **primer** `start`, y el escritor del núcleo representa una tasa fija con suspensión opcional: una tasa que cambia no tenía representación. |

Las opciones eran A `EXISTING_GENERIC_INFUSION_SEMANTICS_SUFFICIENT`, B `SMALL NOREPINEPHRINE EVENT ADAPTER_REQUIRED`, C `GENERIC_INFUSION_MODEL_REQUIRES_SUCCESSOR`, D `CURRENT ORDER MODEL_CANNOT_REPRESENT_TITRATION_SAFELY`. Resultó **B**: el modelo genérico de órdenes ya representa inicio, cambio de tasa y suspensión con una sola tasa absoluta activa; sólo faltaba un adaptador de eventos pequeño del lado de la sombra. No se implementó nada antes de clasificar.

> **Corregido tras la revisión adversarial (§12).** La primera auditoría decía que un `stop` no lleva tasa ni unidades, y no encontró ni las órdenes que no nombran el fármaco ni que el espejo entrega la orden tal como se escribió. Las tres cosas están corregidas en la tabla. El veredicto **B** se mantiene; lo que cambió es el alcance del adaptador (§2, §3 y §8).

## 2 · P3-425 · Flujo de eventos

**Una** infusión por encuentro: un flujo ordenado `(t0, tasa0), (t1, tasa1), …, (t_stop, 0)`. La tasa ordenada en un instante es la del **último evento válido** en o antes de él; las tasas nunca se integran juntas.

| Operación | Significado | Cómo llega del motor |
|---|---|---|
| START | 0 → r (la corrida debe haberlo **visto**) | `start` con tasa en mcg/min |
| INCREASE | r → r′ mayor | `adjust` / `continue` / `start` con tasa absoluta mayor |
| DECREASE | r → r′ menor y mayor que 0 | ídem, con tasa absoluta menor |
| STOP | r → 0 | `stop` |
| RESTART | 0 → r tras una suspensión, la **misma** infusión | cualquier orden con tasa absoluta |
| `IDEMPOTENT_NO_CHANGE` | la misma tasa otra vez, una continuación sin tasa, o suspender una infusión ya suspendida | la infusión la lleva y no cambia nada |

Que una orden fuese un aumento o una disminución se lee contra la tasa **que corrió** antes de ella: el motor tiene una sola operación (`adjust`, con tasa absoluta) para ambas.

**La orden se lee como está escrita.** Debe decir ella misma `mcg/min`. La única excepción es un `continue` que no da tasa ni unidades: conserva la tasa ordenada antes (y el recibo del motor, cuando está, debe decir esa tasa). Cuando hay recibo, debe coincidir con la orden en operación, unidades y tasa; si no coincide, la orden se rechaza. Un número sin unidades **no** se lee como tasa, aunque el motor lo complete: puede ser un objetivo de presión.

**Lo que no lleva la infusión** también tiene nombre y razón, y es siempre una brecha declarada: `REFUSED_FAIL_CLOSED` (rechazada), `REPLACED_WITHIN_ITS_MINUTE` (reemplazada dentro de su minuto) o `NOTHING_TO_BUILD` (deja la infusión sin correr cuando nada había corrido).

## 3 · P3-426 · Contrato temporal y de supersesión

- **Minuto de la orden:** el minuto del estado desde el que se dio.
- **Primer efecto fisiológico:** el soporte se mueve por primera vez en (s, s + 1]; el tono, que sigue al estado un minuto por detrás, y la presión, en (s + 1, s + 2]. Es la regla que ya tenía toda intervención.
- **Sin cambio retroactivo:** nada cambia en o antes del minuto de la orden; el corredor rechaza un contribuyente que cambie un minuto ya registrado.
- **Sin mirar adelante:** el aporte de un minuto depende sólo de las órdenes anteriores a él.
- **Mismo minuto:** dentro de un minuto, la **última** orden válida (por posición en el espejo, nunca por la ortografía del id) es la que lleva algún intervalo modelado, y la **única** que lleva la infusión; las anteriores son brechas declaradas («reemplazada dentro de su minuto»), no órdenes construidas. Un `stop` y una tasa nueva en el mismo minuto de una infusión en curso son **un** cambio a la tasa nueva, no una caída seguida de un reinicio. Si la última orden del minuto es una que el mapeo rechaza, las válidas anteriores de **ese** minuto también quedan reemplazadas, y la historia que conserva la corrida termina antes de ese minuto.
- **El orden del motor es el del espejo:** las órdenes se leen en el orden en que el espejo las guarda (sus minutos nunca retroceden). Una orden fechada antes de otra que llegó primero es una contradicción que el mapeo no resuelve: no se mapea ninguna orden del tipo.
- **Una razón nunca deja de ser cierta:** las brechas de la sesión sólo se acumulan, así que una orden declarada nunca pasa a ser llevada cuando llegan más órdenes. Cada razón depende de la orden, de las anteriores y de si existe una orden posterior en su mismo minuto.
- **Límites de turno y reevaluación:** la trayectoria no depende de cómo se dividan los minutos en turnos, ni de que las órdenes lleguen de una vez o turno por turno.
- **Ejecución diferida:** una orden retenida actúa desde el minuto en que el motor la ejecutó, nunca desde el minuto en que se pidió.
- **La infusión tiene el id de la orden que inició lo que corrió**, cualesquiera sean las órdenes posteriores.

## 4 · P3-427 · Operaciones y dinámica

**Regla:** el aporte del escritor se acerca al soporte estacionario de la tasa ordenada (tasa / tasa de semiefecto), en primer orden, con la constante de **inicio** del propio escritor mientras está por debajo de él y con su constante de **cese** mientras está por encima. Ninguna constante nueva; ninguna constante cambiada.

**Por qué esta regla.** Coincide con la forma cerrada del núcleo en sus dos extremos (un inicio desde cero sube con la constante de inicio; una suspensión decae con la de cese) y es continua entre ellos: una disminución a una tasa casi nula se comporta como una suspensión, y un reinicio desde un residuo se comporta como un inicio. Es la regla más simple con esas propiedades, **no la única concebible**: es una elección de desarrollo que ninguna persona docente ha revisado todavía. Para un inicio, y para un inicio seguido de una suspensión, la aritmética es la del núcleo **bit a bit** (comprobado en los tres testigos, para varias tasas, minutos de inicio y de suspensión). Además se comprobó contra una integración numérica independiente de `dx/dt = (objetivo − x) / τ`, que no comparte aritmética con el escritor (diferencia máxima en las sondas de GI: 5 × 10⁻¹³).

**Qué significa «dirección», exactamente.** El aporte se mueve hacia la tasa ordenada y nunca la pasa (el valor que se **lee** está en la rejilla de los escritores, así que puede quedar a menos de un cuanto, 2⁻⁴⁰, de ese límite). Frente a la misma historia **sin** su última orden, nunca está por encima tras una disminución o una suspensión, ni por debajo tras un aumento o un reinicio. **No** significa que el aporte baje en cuanto se ordena una tasa menor: una disminución ordenada antes del efecto estacionario sigue subiendo, más despacio, hacia el estacionario de la tasa menor.

**Modelos descartados (y por qué, con las mismas constantes):**
- *Suspender la infusión anterior e iniciar otra* (dos flujos a la vez): tras 10 → 12 mcg/min el soporte llega a 1,339 cuando el estacionario nuevo es 1,2 (sobrepaso); tras 10 → 9 mcg/min el soporte **sube** a 1,112 antes de bajar a 0,9 (dirección equivocada ante una disminución).
- *Sumar una infusión por cada incremento:* integra varias tasas a la vez y no tiene forma exacta para una disminución antes del efecto estacionario.

**Sin objetivos de presión (P3-427A):** sólo tasas elegidas explícitamente por la persona clínica. «Titrate norepinephrine to MAP 65» llega del intérprete real como un `adjust` con tasa 65 y **sin unidades**; el mapeo la rechaza porque no dice `mcg/min` (fallo cerrado, con su razón), y nunca la lee como tasa. El motor heredado sí la ejecuta como 65 mcg/min cuando hay una infusión en curso: es el defecto heredado de §1, fuera de este paquete.

## 5 · P3-428 · Replay y persistencia

El artefacto de una corrida liga:
- la identidad, el minuto y el digesto del recibo de **cada** orden (`actions`);
- la historia de tasas `((minuto, tasa), …)` con sus unidades (`rate_units = "mcg/min"`);
- **cada orden que la infusión lleva**, una por minuto, con lo que hizo (`orders`: id, minuto, tasa ordenada, resultado);
- la versión del escritor (`writer_version = "norepinephrine_rate_history/P3-431"`);
- los valores del testigo y el miembro del linaje (procedencia de la instantánea) y el campo de perfil declarado.

El escritor **rechaza** una historia que sus órdenes no explican, un resultado que las tasas no dan, dos órdenes en un minuto, otra versión del escritor y otras unidades; y una especificación sólo se reconstruye si **nombra** `changes`, `orders`, `rate_units` y `writer_version` (ningún campo ausente se rellena con un valor por omisión): un artefacto alterado o recortado no se reconstruye a medias. Lo que el escritor **no** puede comprobar es que las órdenes que nombra sean las del encuentro: eso es del artefacto, que guarda las acciones reflejadas junto a los contribuyentes. El replay del núcleo tampoco coteja las constantes del testigo de una especificación con el testigo declarado (nunca lo hizo, para ningún contribuyente). **Los artefactos históricos de un solo inicio se repiten sin cambio**: un inicio único sigue construyendo el escritor propio del núcleo (`norepinephrine`), con la misma especificación; no se reescribió ningún registro. Una historia de tasas se repite en un proceso que haya cargado el módulo de desarrollo (ahí se registra su tipo); en otro, el artefacto se rechaza **por nombre**, nunca se aproxima. El tipo se registra al importar el módulo y el mapeo vuelve a registrar **los dos escritores que construye** —el del núcleo y la historia de tasas— cada vez que construye (`ensure_registered`), porque un registro sustituido por un rato no conserva el alta (la certificación encontró que eso le pasaba al escritor del propio núcleo: §13). Una vista histórica de un árbol anterior filtra el registro sólo por los tipos nuevos **del núcleo**; este tipo, que es de la capa de la Fase 3, sigue listado dentro de esa vista: nada lo construye allí.

## 6 · P3-429 · Matriz de casos límite

El resultado esperado de cada caso se escribió **antes** de ejecutar la matriz (`test_tone_titration_analysis.EDGE_EXPECTED`). Los 17 renglones de la primera matriz (los 14 del encargo, con el 11 y el 15 desdoblados) resultaron **como se esperaba**.

**Dicho sin rodeos, lo que cambió la revisión adversarial (§12):** una de esas 17 expectativas describía una regla equivocada. El renglón **7** se **revisó** —su expectativa original se conserva en el propio renglón del registro, junto a la razón—, y se **añadieron** cuatro renglones (15C, 16, 17 y 18), cinco variantes del 12 y un chequeo del 14. Cada expectativa nueva se escribió antes de correr el caso por el mapeo reparado. Hoy son **21 renglones, todos como se esperaba**. Nada se ajustó para que pasara.

| # | Caso | Resultado esperado y observado |
|---|---|---|
| 1 | Inicio desde cero | `STARTED`; escritor del núcleo; soporte 0 hasta el minuto de la orden y mayor que 0 al siguiente; replay exacto |
| 2 | Aumento | `STARTED`, `INCREASED`; un escritor; igual a la corrida sin la orden hasta su minuto; el soporte nunca baja ni pasa su estacionario |
| 3 | Disminución | `STARTED`, `DECREASED`; el soporte nunca sube ni pasa su estacionario |
| 4 | Suspensión | `STARTED`, `STOPPED`; no se borra en el minuto de la suspensión; bit a bit igual al escritor del núcleo con suspensión; vuelve a exactamente 0; nunca negativo |
| 5 | Reinicio tras suspender | `STARTED`, `STOPPED`, `RESTARTED`; un escritor; sube de nuevo sin pasar su estacionario |
| 6 | Tasa idéntica repetida | `IDEMPOTENT_NO_CHANGE`; estados iguales a los del inicio único; nada se cuenta dos veces |
| 7 | Dos órdenes en un minuto | **revisado:** gana la última, que es la única que lleva la infusión (`STARTED`, escritor del núcleo); la primera es una brecha declarada, `REPLACED_WITHIN_ITS_MINUTE`; estados iguales a un inicio único a la última tasa. *Antes:* se esperaban ambas llevadas (`STARTED`, `INCREASED`) y ninguna brecha |
| 8 | Unidad inválida | rechazada (fallo cerrado); ella y las posteriores son brechas declaradas; la corrida conserva lo que había mapeado y dice que ya no refleja el vasopresor |
| 9 | Dosis negativa | ídem |
| 10 | Suspender sin inicio previo | rechazada: la corrida nunca vio iniciar esa infusión; ningún escritor; ninguna orden posterior ocupa su lugar |
| 11 | Tasa por peso | como primera orden: ningún escritor; como cambio de tasa: rechazada, **nunca convertida** |
| 12 | Orden mal formada | doce variantes: las siete primeras (objetivo de presión, sin operación, sin acción, tasa en palabras, no numérica, infinita, cero sin ser suspensión) y **cinco añadidas** (objetivo de presión tal como lo entrega el intérprete, tasa sin unidades, tasa demasiado grande para ser un número, acción que no es una orden, recibo que dice otra tasa): todas rechazadas, ninguna lanza una excepción |
| 13 | Estado sin pulso | la corrida termina; el soporte es la forma cerrada del escritor con o sin pulso; no se informa presión sin pulso |
| 14 | Reinicio de sesión y replay | el artefacto sobrevive a JSON y se repite exacto; una corrida reconstruida de las mismas órdenes es la misma; cualquier división en turnos, y las órdenes llegando una a una, dan los mismos estados **y declaran las mismas brechas** (añadido) |
| 15 | Cronología | orden sin minuto entero: ninguna del tipo se mapea; orden fechada antes de un minuto ya registrado: el corredor la rechaza (`HistoryRewritten`); **15C (añadido):** órdenes contra el reloj: ninguna del tipo se mapea |
| 16 | **Añadido.** Orden que no nombra el fármaco | con la norepinefrina en curso, cierra la infusión: ella y las posteriores son brechas declaradas, la corrida conserva lo mapeado y dice que ya no refleja el vasopresor; sin norepinefrina en curso se deja como la declaró la familia y la infusión sigue |
| 17 | **Añadido.** Orden rechazada en el minuto de una válida | la válida de ese minuto nunca corrió: queda reemplazada; los estados son los del inicio único |
| 18 | **Añadido.** Órdenes de un mismo minuto llegando turno por turno | las brechas registradas turno por turno son las del flujo completo; ninguna orden queda a la vez declarada y construida |

## 7 · P3-430 · Gobernanza — veredicto **A · RUNTIME/ADAPTER ONLY**

Las opciones eran A sólo runtime/adaptador, B sólo configuración sucesora de la Enmienda 3, C sucesor nuevo del núcleo común, D Enmienda 4 con cambio de fisiología. Resultó **A**: ningún archivo de `clinical_core/` cambia; el estado común, su lector, la ecuación del tono, la poscarga y todas las constantes son los certificados. La historia de tasas es un escritor que **es** el escritor del núcleo (una subclase en el módulo de mapeo de desarrollo) y cumple su contrato de escritor (lee sus órdenes y el tiempo; ninguna lectura del estado). No hay Enmienda 4, ni miembro nuevo del linaje, ni concesión nueva: sigue `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3`.

## 8 · P3-431 · Implementación mínima

- `runtime_tone_support.py` (capa de la Fase 3, sólo lo importa código de prueba): `NorepinephrineRateHistory` (subclase de `clinical_core.vascular_support.Norepinephrine`, tipo `norepinephrine_rate_history`), `infusion_history`, `physical_history`, `outcome_of`, `order_disposition`, `map_orders`, `order_log` y `ensure_registered`. **Un** escritor de norepinefrina por corrida (una corrida que ya trajera uno se rechaza); **una** tasa ordenada y **una** orden llevada por minuto; transiciones causales; fallo cerrado; una entrada mal formada se declara y nunca lanza una excepción.
- `runtime_shadow_families.py`: `action_dispositions` reconoce las órdenes por las que responde un contribuyente (`carried_order_ids`), para que ninguna orden llevada por la infusión se informe como perdida. El vocabulario de disposiciones no creció.
- Un inicio único construye el escritor del núcleo, exactamente como antes. Ningún adaptador registrado declara el lector; `runtime_authority.SUPPORTED_ACTIONS` y la concesión viva no cambiaron.

## 9 · P3-432 · Sondas de desarrollo en hemorragia digestiva

Texto de orden real, por el intérprete y el motor reales y su espejo, sobre `gi_bleed_57m` (FR-F) con la instantánea ratificada de presión de GI y el testigo `CENTER_REFERENCE`. Primera orden en el minuto 2; las siguientes en los minutos 10, 18 y 25; lectura hasta el 32. **No se pide a la docencia una calibración en mmHg.** Presión mostrada PAS/PAD (PAM), en mmHg:

| Sonda | Historia (mcg/min) | min 10 | min 18 | min 25 | min 32 |
|---|---|---|---|---|---|
| Sin orden | — | 85/52 (63) | 83/51 (62) | 81/50 (60) | 79/48 (58) |
| **A** START | 5 | 96/59 (71) | 94/57 (69) | 91/56 (68) | 89/55 (66) |
| (comparador) START | 10 | 101/62 (75) | 99/61 (74) | 96/59 (71) | 94/58 (70) |
| **B** START → INCREASE | 5 → 10 (min 10) | 96/59 (71) | 99/61 (74) | 96/59 (71) | 94/58 (70) |
| **C** START → DECREASE | 10 → 4 (min 10) | 101/62 (75) | 93/57 (69) | 90/55 (67) | 88/54 (65) |
| **D** START → STOP | 10 → 0 (min 10) | 101/62 (75) | 85/52 (63) | 81/50 (60) | 79/48 (58) |
| **E** START → INCREASE → DECREASE → STOP | 5 → 10 → 4 → 0 | 96/59 (71) | 99/61 (74) | 91/56 (68) | 80/49 (59) |
| Reinicio | 10 → 0 → 10 (min 18) | 101/62 (75) | 85/52 (63) | 96/59 (71) | 94/58 (70) |

La hemorragia sigue sin tratar en todas: la presión de base cae de 87/54 a 79/48 mmHg, y el beneficio de la norepinefrina se lee sobre esa base que cae (la limitación ya registrada por la docencia en FR-F).

**Predicciones escritas antes de correr, todas cumplidas:**

| Chequeo | Qué se predijo | Resultado |
|---|---|---|
| Tiempo | Una orden en el minuto s no cambia nada en o antes de s; el soporte difiere por primera vez en s + 1; el tono y la presión, en s + 2 | Cumplido en los seis pares (11/12/12, 19/20/20, 26/27/27) |
| Dirección | Tras un aumento o un reinicio, soporte, tono y presión nunca están por debajo de la corrida sin esa orden; tras una disminución o una suspensión, nunca por encima | Cumplido |
| Orden | En E, el soporte al final de cada meseta ordena como las tasas (10 > 5 > 4 > suspendida ≥ 0), y la presión relativa a la corrida sin orden mapeada, igual | Cumplido (0,998 > 0,498 > 0,436 > 0,027; 1,192 > 1,131 > 1,124 > 1,016) |
| Suavidad | El soporte no se mueve en el minuto de una orden ni, en ningún minuto, más que su propio paso de primer orden; ningún cambio de tasa mueve el tono en un minuto más de lo que lo movió el inicio simple a 10 mcg/min | Cumplido (0,117 ≤ 0,196) |
| Persistencia y cese | Con tasa sin cambios el soporte se acerca a su estacionario y no lo pasa; tras suspender no se borra en ese minuto, decae sólo con la constante de cese (la forma cerrada del núcleo, bit a bit), nunca es negativo, queda menos del 1 % a los 12 minutos y al menos el 90 % del efecto de presión se fue a los 22 minutos | Cumplido (efecto de presión: 19,2 % en la suspensión → 2,4 % a 8 min → 0,15 % a 15 min → 0,01 % a 22 min) |
| Estado intacto | Volumen, bomba, hemoglobina y agua pulmonar idénticos, minuto a minuto, a la corrida sin orden mapeada | Cumplido |
| Histórico | El inicio simple construye el escritor del núcleo; la corrida con la orden sin mapear es la misma cualesquiera sean las órdenes | Cumplido |

**Fidelidad del espejo, en estos guiones:** al final de cada uno, la tasa activa del propio motor (0, 4, 5 o 10 mcg/min) es la tasa ordenada que lleva la corrida. Vale para órdenes que nombran el fármaco y dicen `mcg/min`; lo que pasa con las demás está en §9.1. **Compatibilidad histórica:** el inicio simple a 10 mcg/min en el minuto 2 da, minuto a minuto, la presión guardada en el candidato certificado de FR-F, con otros turnos.

### 9.1 · Las frases de la revisión adversarial, por el encuentro real (añadido en P3-435)

Mismo caso y mismo testigo; primera orden en el minuto 2 y la segunda en el 10. La expectativa de cada una se escribió después de ver cómo entrega el espejo estas órdenes y **antes** de correrlas por el mapeo reparado; las ocho resultaron como se esperaba. «Tasa del motor» es el estado propio del motor heredado al final; «tasa de la corrida», la que lleva la sombra.

| Sonda | Frase | Cómo llega | Qué hace el mapeo | Tasa del motor / de la corrida |
|---|---|---|---|---|
| R1 | «Stop the infusion.» | `infusion_adjustment`, recibo vacío | cierra la infusión y lo dice | 0 / 10 |
| R2 | «Increase the infusion rate to 20 mcg/min.» | `infusion_adjustment`, recibo vacío | cierra la infusión y lo dice | 20 / 10 |
| R3 | «Increase norepinephrine to 12.» y luego «Stop norepinephrine.» | `adjust` 12 sin unidades (el recibo dice mcg/min) | rechaza la primera y, por el cierre, también la suspensión; lo dice | 0 / 10 |
| R4 | «Continue norepinephrine.» | `continue` sin tasa ni unidades | `IDEMPOTENT_NO_CHANGE` | 10 / 10 |
| R5 | «Titrate norepinephrine to MAP 65.» | `adjust` 65 sin unidades | rechaza; nunca la lee como tasa; lo dice | **65** / 10 |
| R6 | «Start norepinephrine at 0.1 mcg/kg/min.» | `start` en mcg/kg/min | rechaza; **nunca convierte**; ningún escritor | 11,1 / 0 |
| R7 | «Stop norepinephrine 10 mcg/min.» | `stop` con tasa y unidades | `STOPPED` | 0 / 0 |
| R8 | «Start … at 5 mcg/min. Increase … to 10 mcg/min.» (un turno) | dos órdenes en el minuto 2 | la primera reemplazada; la segunda `STARTED` | 10 / 10 |

**Lo que esto muestra y hay que leer con cuidado.** En R1, R2, R3, R5 y R6 la corrida **ya no muestra lo que corre el motor**: lo declara (brecha con su razón; «ya no refleja el vasopresor») y sigue calculando la historia que había mapeado, a su última tasa, por el resto del encuentro. En R3 eso incluye **ignorar una suspensión explícita posterior**. Es fallo cerrado en el sentido de que nada se adivina y nada queda en silencio, **no** en el sentido de que la sombra siga siendo fiel. Ninguna corrida difiere del motor sin decirlo.

## 10 · P3-433 · No regresión multifamilia

La misma historia (5 → 10 → 4 → suspensión, en los minutos 5, 12, 19 y 25) en las familias que nombró la docencia, más la sonda sintética de bajo tono. PAS mostrada con la historia / sin orden mapeada:

| Familia | min 12 | min 19 | min 25 | min 32 |
|---|---|---|---|---|
| Hemorragia digestiva | 96 / 85 | 99 / 83 | 92 / 81 | 81 / 80 |
| Embolia pulmonar de alto riesgo | 98 / 85 | 103 / 84 | 96 / 84 | 85 / 83 |
| ACS (limitado por la bomba) | 118 / 102 | 124 / 102 | 116 / 101 | 102 / 100 |
| Edema pulmonar hipertenso (limitado por la bomba, congestivo) | 246 / 218 | 260 / 218 | 246 / 218 | 222 / 218 |

- **El soporte es el mismo, minuto a minuto, en todas las familias** (el escritor lee sus órdenes y el tiempo; lo que difiere es lo que el flujo, la precarga y la bomba de cada familia hacen con el tono).
- **Sin acción de tono, la trayectoria no cambia:** con el lector declarado y ninguna orden, toda lectura es idéntica a la del adaptador registrado.
- **El inicio único certificado no cambió:** en cada familia sigue construyendo el escritor del núcleo y da, número por número, lo guardado en `PHASE3_COMMON_TONE_PROBES.json`; la sonda sintética de bajo tono guardada también se reproduce.
- **Sonda de bajo tono** con la misma historia: la ganancia de presión ordena como las tasas y la presión nunca pasa la de llegada.
- **No se promueve el uso en familias limitadas por la bomba:** ACS y edema se corren sólo para no regresión; `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` sigue abierta.

## 11 · P3-434 · Control negativo de manejo

`docs/revision/NEGATIVE_CONTROL_HYPERTENSIVE_PULMONARY_EDEMA_NOREPI_V1.json`: `HYPERTENSIVE_PULMONARY_EDEMA_NOREPI` = **`NEGATIVE_CONTROL_MANAGEMENT_SCENARIO`** (FD-TITRATE-10, que formaliza FD-TONE-RATIFY-06). Propósito: mostrar que una respuesta presora fisiológicamente comprensible puede seguir siendo una acción de manejo clínicamente inapropiada. **Respuesta fisiológica ≠ manejo apropiado.**

- Evidencia humana: `REJECT` (Expected / Plausible / Too large / Incoherent / Yes), tal como se reportó; **no** se convierte en fallo del mecanismo ni se suaviza.
- Fisiología **sin alterar**: la trayectoria recalculada hoy (218/116 → 260/138 mmHg con la orden; 218/116 sin ella) es, minuto a minuto, la que revisó la docencia; el escritor es el del núcleo (el inicio único revisado, sin cambios de tasa).
- Es un **registro**: no está construido en la aplicación, no es visible al residente, no puntúa y la norepinefrina no se hizo indisponible. Construirlo como escenario es una decisión aparte.

## 12 · P3-435 · Revisión adversarial independiente

**Una** revisión, por un agente independiente de sólo lectura que no escribió el paquete, con la lista de ataques del encargo. Encontró defectos reales, incluido uno **bloqueante**. Cada hallazgo se reprodujo con una sonda antes de repararlo.

| # | Severidad | Hallazgo (confirmado) | Disposición |
|---|---|---|---|
| 1 | **Bloqueante** | «Stop the infusion.» y «Increase the infusion rate to 20 mcg/min.» las resuelve el motor a la norepinefrina en curso, pero el espejo las entrega como `infusion_adjustment` con recibo vacío. El mapeo sólo miraba el tipo `norepinephrine`: la sombra dejaba el vasopresor corriendo **sin decir nada** (fallo abierto). | **Reparado en el mapeo:** con la norepinefrina en curso, esa orden cierra la infusión y se declara con su razón. **No reparada la causa:** que el espejo entregue la orden sin resolver es de la capa compartida (`runtime_shadow`) y queda como decisión abierta. |
| 2 | Mayor | El mapeo juzga la orden interpretada, antes de que el motor la complete. «Increase norepinephrine to 12.» llega sin unidades, se rechaza, cierra la infusión y una suspensión posterior se ignora. El texto de la auditoría («un `stop` no lleva ninguna») era falso. Las pruebas de objetivo de presión usaban una forma que el intérprete nunca emite. | **Parcial, y así se declara.** Se **mantiene** la lectura «como está escrita» (no se lee una tasa sin unidades: la misma forma tiene «MAP 65»). Se añadió la continuación sin tasa, el cotejo con el recibo, la forma real del intérprete en las pruebas y las sondas de texto real; se corrigió la auditoría. **El cierre persistente sigue:** tras un rechazo, la sombra no sigue ni una suspensión explícita. Limitación declarada y decisión abierta. |
| 3 | Mayor | Una orden rechazada en el mismo minuto que una válida: la tasa válida de ese minuto, que nunca corrió, quedaba llevada para siempre. | **Reparado:** queda reemplazada, y la historia termina antes de ese minuto. |
| 4 | Mayor | Brechas obsoletas: tres órdenes llegando turno por turno dejaban brechas «nada que construir» junto a las **mismas** órdenes informadas como construidas. | **Reparado:** una orden declarada nunca pasa a ser llevada. Prueba de propiedad sobre 1 501 flujos de órdenes, prefijo a prefijo. |
| 5 | Menor | Las disposiciones informaban `BUILT`, con minuto efectivo, órdenes que nunca actuaron (reemplazadas dentro de su minuto). | **Reparado:** son brechas declaradas. |
| 6 | Menor | El escritor validaba sólo la proyección (minuto, tasa) de sus órdenes: aceptaba resultados mal rotulados, y una especificación sin unidades o sin versión se reconstruía con los valores por omisión. | **Reparado:** recalcula cada resultado, exige una orden por minuto y una especificación que nombre sus cuatro campos. Lo que no puede comprobar (que las órdenes nombradas sean las del encuentro) queda dicho en §5. |
| 7 | Menor | Entradas mal formadas lanzaban excepciones en vez de declararse (tasa 10⁴⁰⁰, acción que no es un mapeo, id que no es texto). | **Reparado:** cada una es una brecha declarada. |
| 8 | Menor | El alta del tipo al importar se filtra a las vistas históricas del linaje y se pierde si el registro se sustituye. | **Parcial:** el mapeo vuelve a registrar al construir. La presencia del tipo dentro de una vista histórica **sigue** y queda documentada (§5): nada lo construye allí. |
| 9–12 | Notas | El replay del núcleo no exige un solo escritor ni coteja las constantes del testigo. `_approach` podía pasar el objetivo por redondeo. Afirmaciones que las pruebas no demostraban: «nunca baja en un aumento ni sube en una disminución», una «forma cerrada independiente» que era una transcripción, un chequeo de presión calculado y no afirmado, «la única regla». Detalles: un ordenamiento que ocultaba contradicciones de llegada, un minuto truncado con `int()`, el tipo de la acción sin cotejar, textos de brecha concatenados sin puntuación. | **Reparado lo propio:** el límite se sostiene exacto (lo leído, en la rejilla, a menos de un cuanto); la dirección se enuncia como es (§4) y se prueba así; integración numérica independiente; el chequeo de presión se afirma; se retiró «la única»; la contradicción de llegada se rechaza; se cotejan tipo y tasas; puntuación corregida. **Declarado, sin cambio:** lo del replay es conducta del núcleo, que no se edita. Que las expectativas se escribieron antes de ejecutar es una declaración que ninguna prueba puede demostrar. |

**Sospechas del revisor.** Que la autoridad viva se detenga ante una orden que no nombra el fármaco: `infusion_adjustment` no está en `runtime_authority.SUPPORTED_ACTIONS`, igual que `norepinephrine` (leído de la tabla; **no** se corrió una sesión con autoridad). Contaminación del registro entre pruebas: la decide la suite completa (§13). Un `adjust` sobre una infusión suspendida: el motor real lo rechaza, así que no puede llegar; el mapeo lo lee como reinicio (decisión abierta 4).

**Fuera del cambio, informado.** El defecto heredado de «MAP 65» (§1). Los adaptadores registrados declaran `infusion_adjustment` como brecha («sin intervención del núcleo»), que es correcto para ellos: no mapean ningún vasopresor.

**Ataques que no prosperaron.** Dos escritores activos; doble conteo de cambios de tasa y errores de rejilla; suspensión que lleva `T` a la base al instante; suspensión que nunca decae; infusión anterior que persiste tras la supersesión; tasas y unidades inválidas aceptadas; mcg/kg/min leído como mcg/min; replay que pierde la historia; división en turnos o cambio de tipo de escritor que alteran la fisiología (digestos idénticos en 1 200 corridas del revisor); atajo fármaco → mmHg; deriva de los registros certificados; ampliación de la autoridad o conducta visible al residente.

**Tras la reparación:** 14 mutantes del mapeo reparado (uno por regla), todos detectados por las pruebas focalizadas.

## 13 · P3-436 · Certificación

Cambió comportamiento ejecutable (el mapeo de desarrollo y unas líneas de `runtime_shadow_families.py`), así que la certificación fue **completa**, sobre **una** huella congelada. Hubo **dos corridas completas**, y sólo la segunda cuenta.

**Primera corrida, no verde (no se reclama).** Huella `34ed90d8edba…`: 13 478 pruebas, **3 fallas**, 0 errores, 99 omitidas; regresiones 56/56 activas. Las tres fallas, clasificadas con evidencia:

| Prueba | Clasificación | Evidencia | Reparación |
|---|---|---|---|
| `test_runtime_shadow_ensemble.py::test_no_adapter_invents_a_magnitude_as_a_fallback` | **Regresión de este cambio** | Una guarda prohíbe `getattr` con valor por omisión en `runtime_shadow_families.py`; la línea que añadió P3-431 a `action_dispositions` lo usaba. Las corridas focalizadas previas no incluían ese archivo. | La línea pregunta con `hasattr` y lee el atributo: misma conducta, sin valor de reserva. |
| `test_phase3_tone_review_records.py::test_c3` y `::test_c3b` (una sola causa) | **Dependencia de orden previa, no causada por este cambio** | Se reproduce aislada corriendo antes `test_clinical_core_edema_migration.py`, y se reproduce **igual en la base `b087215`**, en un árbol limpio (1 falla, 36 aprobadas; `no contributor type 'norepinephrine'`). `integration.from_spec` importa `clinical_core.vascular_support` de forma perezosa; bajo la vista histórica de alcance de módulo de ese archivo, el escritor del núcleo se registra en el registro sustituido y falta en el vivo cuando la vista termina. Los archivos de prueba nuevos movieron los límites de las particiones y dejaron los dos archivos en el mismo proceso. | Sólo en la capa de la Fase 3: el mapeo registra los **dos** escritores que construye cada vez que construye. La causa está en `clinical_core/`, que no se edita: queda informada (`TD-158`, ítem 5). |

**Segunda corrida, la que certifica.**

- **Candidato:** rama `phase-3-runtime-integration`, base `b087215`, árbol de trabajo con huella `9a14a6ce2f96433f2ce458fe71e15d8cd04cba825fb94207bb58c97a0f0d78e0`: el mapeo reparado, las pruebas, el arnés, los registros de sondas y de control negativo con su índice y su ancla, este documento (§0 a §12 y §15), las filas FD-TITRATE-01 a 13 y FD-P3-273 a 275, `TD-158` y la cláusula de `CLAUDE.md`.
- **Suite completa:** 13 479 pruebas, **0 fallas, 0 errores**, 99 omitidas, 1 xfail, en 24 particiones; huella igual al inicio y al final (0 reanudaciones).
- **Regresiones:** `run_regressions.py`, **56/56** activas aprobadas; 10 retiradas, que el propio ejecutor conserva sin correr.
- **Antes de congelar:** tras las dos reparaciones, el conjunto focalizado de titulación, soporte de tono, ratificación, puntos de control, registros de la vía, revisión de tono, conjunto de la sombra, familias, evidencia, plomería, observabilidad, resolución, sincronización, aislamiento, linaje de la Enmienda 3 y versionado de registros: **679 aprobadas, 4 omitidas, 0 fallas**; el par que falló en la primera corrida, en ese orden (migración del edema y luego los registros de la revisión de tono): **53 aprobadas**; y, después de alinear el texto de diseño del arnés y la deuda y de generar otra vez los dos registros, las guardas de registros, versionado y documentos, el conjunto de la sombra y la prueba nueva de registro: **97 aprobadas, 2 omitidas** (las que esperan al punto de control); 14 mutantes del mapeo reparado, los 14 detectados.
- **Pruebas adaptadas (cuatro, declaradas):** las de `TD-158`, ítem 16.
- **Registros:** los de sondas y de control negativo se generaron de nuevo con el código corregido antes de congelar (nunca estuvieron en un commit); frente al primer borrador sólo cambió el digesto del artefacto del caso 14, que liga la capa que lo produjo.

**Lo que se añadió después de certificar, y no cambió nada ejecutable:** el registro del punto de control, su entrada en el índice con el ancla del índice, estas secciones 13 y 14 y la fila FD-P3-276. La suite completa corrió sobre el candidato de arriba, **no** sobre el árbol final. Sobre el árbol final se repitieron las pruebas que leen esos archivos: los registros y el punto de control de la titulación, el versionado y el índice de registros, la deuda que cita sus correcciones, el idioma de los documentos, los registros de la vía, de la revisión y de la ratificación del tono, y las pruebas de titulación (nueve archivos): **161 aprobadas, 2 omitidas, 0 fallas**; las dos omitidas son de `test_phase3_tone_pathway_records.py` y lo son por diseño (un registro escrito por otro código no se regenera, P3-388).

**No se verificó:** una sesión con la autoridad viva y una orden que no nombra el fármaco (se leyó `SUPPORTED_ACTIONS`; no se corrió); trayectorias LOW/HIGH de estas historias (FD-TITRATE-13); ninguna revisión humana de una trayectoria de titulación.

## 14 · P3-437 · Punto de control — **A · `NOREPINEPHRINE_TITRATION_AND_STOP_READY_FOR_HUMAN_DEVELOPMENT_REVIEW`**

Registro: `docs/revision/PHASE3_NOREPINEPHRINE_TITRATION_CHECKPOINT.json`. Las opciones eran A `NOREPINEPHRINE_TITRATION_AND_STOP_READY_FOR_HUMAN_DEVELOPMENT_REVIEW`, B `ORDER_SEMANTICS_REQUIRE_FACULTY_DECISION`, C `TITRATION_REQUIRES_GENERIC_INFUSION_REDESIGN`, D `REPLAY_SEMANTICS_NOT_CERTIFIABLE` y E `IMPLEMENTATION_REQUIRES_NEW_PHYSIOLOGY`.

**Por qué A.** Las cuatro operaciones funcionan por la misma vía, con la dinámica existente, sin constante nueva; la certificación completa está en verde; las trayectorias de desarrollo están listas para que una persona docente las mire.

**Por qué no B, dicho con su límite.** La semántica que este paquete necesitaba la fijaron FD-TITRATE-01 a 13, y está implementada y certificada para órdenes que nombran el fármaco y dicen `mcg/min`. Lo que queda abierto —seguir la orden asentada por el motor, volver a seguir una orden explícita tras un rechazo— amplía lo que la sombra sigue y no cambia las trayectorias por revisar. **Si la docencia considera que «stop the infusion» debe seguirse antes de cualquier revisión humana, la lectura correcta es B:** ese juicio es suyo, y es la primera decisión abierta de §15.

**Por qué no C, D ni E.** El modelo genérico de órdenes del motor ya representa inicio, cambio de tasa y suspensión (no C). Una historia de tasas sobrevive a JSON, se repite exacta y los artefactos de un solo inicio se repiten sin cambio (no D). No cambió ningún archivo de `clinical_core/` ni ninguna constante (no E).

**Siguiente acción humana.** Que una persona docente mire las trayectorias de titulación y suspensión de la hemorragia digestiva (dirección, tiempo, orden, suavidad, persistencia y cese; sin calibración en mmHg) y diga si la regla del cambio de tasa es aceptable para desarrollo.

**Se confirma:** sin recalibrar el tono, sin cambio del acoplamiento con la bomba, sin fisiología nueva, sin ampliar la autoridad, sin autoridad de consciencia ni terminal, sin despliegue a residentes y sin afirmación de validación clínica. **Alto** tras P3-437.

## 15 · Límites y decisiones docentes abiertas

**Límites.**
- Un solo testigo (`CENTER_REFERENCE`); no se corrieron estas historias en LOW/HIGH como trayectorias (FD-TITRATE-13). La aritmética del escritor sí se probó en los tres testigos.
- La regla del cambio de tasa (inicio al subir, cese al bajar) es la extensión continua del inicio ya revisado y de la suspensión del núcleo; **ninguna persona docente ha revisado todavía una trayectoria de titulación**.
- No se leen FC, relleno capilar, consciencia, gasto, entrega ni deuda. La consciencia bajo tono sigue sin resolver y no se deriva.
- **El espejo entrega la orden tal como se escribió, antes de que el motor la resuelva o la complete.** Por eso una orden que no nombra el fármaco («stop the infusion») y un ajuste escrito sin unidades («increase norepinephrine to 12») **cierran** la infusión: la corrida lo declara, sigue calculando la historia que había mapeado (la última tasa válida sigue corriendo) y desde ahí **no muestra lo que corre el motor**, ni siquiera ante una suspensión explícita posterior. No adivina la tasa real del motor. Reflejar la orden asentada por el motor es un cambio en el espejo compartido, que no se hizo aquí.
- El motor heredado ejecuta «titrate norepinephrine to MAP 65» como 65 mcg/min cuando hay una infusión en curso (defecto del intérprete heredado, fuera de este paquete). El mapeo rechaza esa orden.
- El escritor valida su contabilidad contra sí mismo; que las órdenes que nombra sean las del encuentro lo sostiene el artefacto, no el escritor.
- Una orden que el motor ejecutó en un intervalo que la sesión no observó la declara la sesión, no este mapeo: la corrida no puede saber que la infusión cambió.
- Una historia de tasas sólo se repite donde está cargado el módulo de desarrollo.
- El motor heredado conserva su propia regla de vasopresor y sigue siendo la única autoridad en tiempo de ejecución.

**Lo que queda abierto a decisión docente.**
1. Si las trayectorias de titulación y suspensión son aceptables para desarrollo (revisión humana de dirección, tiempo, orden, suavidad y cese; no hecha).
2. Si la sombra debe reflejar la orden **asentada** por el motor (para seguir «stop the infusion» y un ajuste escrito sin unidades) en vez de cerrar la infusión. Es un cambio de arquitectura en el espejo compartido, y antes hay que resolver el defecto heredado de «MAP 65».
3. Si la primera orden rechazada debe seguir cerrando la infusión por el resto del encuentro, o si una tasa explícita o una suspensión posteriores deben volver a seguirse.
4. Si un ajuste ordenado con la infusión suspendida debe seguir leyéndose como reinicio.
5. Si el escenario de control negativo se construye alguna vez en la aplicación.
6. Si las limitaciones de dependencia de la bomba y de consciencia exigen trabajo antes de cualquier uso educativo.

**No se hizo y no está autorizado:** objetivos automáticos de PAM, dosificación por peso, otro vasopresor, recalibración del tono, cambio del acoplamiento con la bomba, retorno venoso o inotropía, ampliación de la autoridad de norepinefrina, piloto con residentes.
