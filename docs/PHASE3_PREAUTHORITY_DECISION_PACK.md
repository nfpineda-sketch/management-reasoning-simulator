# Fase 3 · Paquete de decisión docente antes de cualquier autoridad (P3-12 y P3-13)

Sólo lectura y sólo diseño. No concede autoridad, no implementa un modo de autoridad y no aprueba ninguna
magnitud clínica. Rama `phase-3-runtime-integration`, sobre la cabeza de cierre de la Fase 2 `d2cca46`,
digesto `22b90a6f7f38…` intacto. La evidencia es la de P3-11: la batería de aceptación del repositorio sobre
los dos casos GI, 34 escenarios, jugada con la sombra apagada y encendida.

## P3-12 · Síntesis de la evidencia de preautoridad

### P3-12-1 · Política de parámetros: dos políticas distintas, y no se mezclan

| | Política de **evidencia en sombra** | Política de **instantánea de autoridad** |
|---|---|---|
| hoy | `SHADOW_REGION_WITNESSES_PREFERRED`: punto comprometido más las dos esquinas de la región declarada de 29 magnitudes de perfil | **no existe** |
| por qué | la sombra no es un paciente: puede correr tres trayectorias y comparar con la envolvente | un paciente tiene **una** trayectoria: una autoridad no puede mostrar una envolvente como vital |

Opciones para la autoridad futura:

- **A · una sola instantánea estructural nombrada** (el perfil comprometido, lo que ya corre en sombra).
  Ejecutable hoy, y exactamente lo que P3-11 midió. Pero el punto comprometido **es** un borde de su propia
  región en `lactate_per_output_deficit` (inferior), `hypoxaemia_threshold_spo2` y `pump_preload_coupling`
  (superior): presentarlo como la verdad del paciente es presentar un borde como valor clínico.
- **B · instantánea puntual aprobada por docencia**, magnitud por magnitud, sólo las del dominio que toma
  autoridad, con procedencia y guardada con cada encuentro. Para una autoridad hemodinámica de GI son
  **8 magnitudes** con región real: `preload_curve_scale_ml`, `arrival_preload_fraction`,
  `pump_preload_coupling`, `afterload_sensitivity`, `low_output_pressure_knee`,
  `sbp_per_pressure_deficit`, `dbp_per_pressure_deficit` y —sólo si CRT entra— `crt_per_output_deficit_s`.
  Las otras tres del camino (`volume_preload_kappa`, `preload_fraction`, `pump_reserve`) son estructurales y
  no tienen región que aprobar.
- **C · conjunto por región**: queda como política de **evidencia**, no de autoridad.
- **D · autoridad imposible hasta calibrar**: es la lectura correcta si la docencia no quiere aprobar
  magnitudes; entonces la fisiología común sigue en sombra indefinidamente y eso es una decisión legítima.

**Recomendación: B, acotada al dominio de autoridad**, con la tabla de regiones de P3-11 como entrada; la
sombra conserva C. No apruebo ninguna de las ocho.

### P3-12-2 · Marco de aceptación de divergencias: estructural ahora, numérico después

Separados a propósito:

**Aceptación estructural (decidible hoy, sin inventar números).** Las diez condiciones de P3-11-8, más:
cada diferencia clasificada, ninguna `UNEXPECTED` ni `SAFETY_CRITICAL`, vivo = replay digesto por digesto,
el artefacto reproduce, **ninguna acción del conjunto de acciones del dominio sin escritor**, y **una
lectura docente de cada diferencia que el golden declara sólo en algunos de sus escenarios** (hoy `hr`
19/20, `crt_s` 18/20, `V_ml_eq` 10/20 y `consciousness_level` 1/20; la última es la que la revisión
adversarial encontró silenciada y la que más importa, porque el golden dice que coincide en 19 de 20).

**Aceptación clínica numérica (decisión docente).** Hoy el repositorio dice «TBD» y P3-11 no inventó
ninguna tolerancia. Hay una alternativa que no necesita números y que la evidencia ya soporta: **usar la
región declarada como criterio** —«el valor que la autoridad muestra debe caer dentro de la región declarada
de la incertidumbre de la Fase 2 para su magnitud»— y tratar la comparación con el motor heredado como
**señal de vigilancia**, no como puerta, porque el legado no es verdad clínica de referencia.

Con una precisión que la revisión adversarial obligó a escribir: «dentro» es una afirmación conservadora y
sólida —los testigos son esquinas de la región, así que la región verdadera es al menos igual de ancha—,
pero «fuera» **no** es simétrica: el tramo que se compara es el mínimo y el máximo de tres corridas
nombradas sobre una caja de 29 magnitudes, y un valor fuera de ese tramo puede estar dentro de la región. Si
la docencia adopta la región como criterio, lo que se aprueba es el tramo de los testigos nombrados, no «la
región», y esa diferencia hay que decirla en la decisión.

Tabla de decisión propuesta (sin umbrales):

| Dominio | Criterio estructural | Señal de vigilancia | Qué detiene el experimento |
|---|---|---|---|
| hemodinámica (SBP, DBP, MAP) | dentro de la región aprobada | posición respecto del legado | salir de la región, o una invariante |
| CRT | igual | igual | igual |
| FC | **no entra**: su región está sostenida o nula | comparación en sombra | — |
| respiración y oxigenación | **no entran**: RR nunca cae dentro de la región; SpO₂ tiene región nula | comparación en sombra | — |
| metabólico | **no entra**: el lactato depende de una magnitud cuyo punto comprometido es un borde | comparación en sombra | — |
| consciencia y colapso | **no entran**: sin mapeo de categoría y sin umbrales | diagnóstico no autoritativo | — |

### P3-12-3 · Dónde cae el legado respecto de la región común

Sobre los **82 minutos comparados** de los 34 escenarios, no sólo el último de cada uno:

| Variable | Dentro | de ellos por coincidencia | Fuera | Región nula | Lectura |
|---|---|---|---|---|---|
| `sbp` | 78 | 2 | 4 | — | lo que el golden declara arquitectónico cae dentro de la región |
| `dbp` | 78 | 5 | 4 | — | igual |
| `map` | 79 | 5 | 3 | — | igual |
| `crt` | 72 | 32 | 10 | — | dentro en la mayoría, y casi la mitad por coincidencia exacta |
| `hr` | 40 | 16 | 6 | 36 | la ganancia FC/impulso está **sostenida** (25,0, sin región): la banda se cierra en 36 minutos |
| `respiratory_rate` | 6 | 8 | 44 | 32 | la región **no** la rescata: RR autorada contra impulso común es arquitectura, no incertidumbre |
| `spo2` | — | 82 | — | 82 | región nula y coincidencia exacta en todos: la SpO₂ no se mueve en estos minutos |

«Por coincidencia» cuenta los minutos en que la variable coincidía con el legado y el valor del legado hubo
que tomarlo del testigo estructural: esos no pueden caer fuera de su propia banda y van aparte para que un
«dentro» que es «idéntico» no infle la lectura.

Para cada caso «fuera» la pregunta de P3-12-3 se responde así: `respiratory_rate` es **comportamiento
específico del legado** (diferencia de arquitectura declarada en P2K-1/P2K-2), no incertidumbre de
parámetros; `hr` es **región sostenida** —la ganancia FC/impulso se adoptó del literal del motor en P2C y el
registro la sostiene— más seis minutos genuinamente fuera; `sbp`, `dbp` y `map` son **incertidumbre de
parámetros** en 78, 78 y 79 de los 82 minutos y, en los 4, 4 y 3 minutos fuera, una diferencia que ninguna
esquina de la región explica y que merece revisión antes de una autoridad; `crt` queda dentro en 72 minutos,
de los cuales 32 por coincidencia exacta, con 10 fuera. Ninguno de estos resultados dice que el núcleo tenga
razón.

### P3-12-4 · El dominio de autoridad más pequeño que es coherente

No se puede elegir una sola salida: MAP es función de SBP y DBP, y las tres salen del mismo déficit de
presión, que sale del gasto. El dominio mínimo coherente es:

**`{SBP, DBP, MAP}` con el gasto como variable interna**, y CRT como opción del mismo bloque (depende del
mismo déficit). Fuera: FC, RR, SpO₂, lactato, Hb, V, consciencia, colapso, paro, destino de órdenes,
puntuación y persistencia, que siguen siendo del motor heredado. V y Hb podrían ser comunes —el espejo de
intervenciones coincide exactamente— pero incluirlas no agranda la enseñanza y sí la superficie.

### P3-12-5 · Reversión

| Opción | Lectura |
|---|---|
| A · reversión por encuentro | la única que preserva una historia coherente, y sólo replayeando el encuentro desde su artefacto con autoridad del legado, nunca cambiando de motor a mitad |
| B · reversión por minuto | **la peor**: un paciente cuyas presiones saltan entre dos arquitecturas a mitad de encuentro enseña una mentira |
| C · reversión por dominio | no es reversión, es alcance: se decide antes del encuentro |
| D · fallo duro, visible para la docencia | correcto para el primer experimento: el encuentro se detiene, queda marcado y sale de la puntuación |

**Recomendación: D para el primer experimento** (entorno docente o de desarrollo), con A como la única forma
de rescatar una corrida: replay desde el artefacto inmutable.

### P3-12-6 · Política de fallo de una autoridad futura

| Fallo | Conducta propuesta |
|---|---|
| `CoreInvariantError` | sin escritura autoritativa, detención visible, encuentro marcado y excluido de la puntuación |
| `UnresolvedBoundary` | igual, clasificado como vacío declarado (clase de fallo esperada, no un error del núcleo) |
| desacuerdo replay/vivo | detiene el **experimento**, no sólo el encuentro: falsifica la propiedad de determinismo |
| divergencia inesperada contra el legado | no detiene el encuentro —el legado no es verdad— pero queda marcada para revisión docente |
| acción sin escritor (anticoagulación, antiagregante, vasopresor) | **rechazo previo**: un encuentro cuyo guion puede contener una acción de manejo sin escritor no corre con autoridad |

### P3-12-7 · Separación del piloto

Confirmada y sin cambios: el primer piloto corre con el motor congelado; la bandera no aparece en ninguna
superficie del piloto; el preflight no puede exigirla porque `pilot_freeze.py` está en el conjunto congelado
de la Fase 2 (`PILOT_PREFLIGHT_FLAG_GATE_DEFERRED`, TD-130), así que la separación es por entorno y por
ausencia, fijada por prueba. Un experimento de autoridad corre **fuera** del primer piloto.

### P3-12 · Decisiones docentes que hacen falta, exactamente

1. Aprobar (o no) una instantánea puntual para las **8 magnitudes** del dominio hemodinámico de GI, con
   procedencia; o decidir D (la fisiología común sigue en sombra).
2. Decidir el criterio de aceptación: **el tramo de testigos nombrados como criterio** (sin números) o una
   tolerancia numérica por variable, que sólo la docencia puede fijar.
3. Decidir qué hacer con los tres vacíos de tratamiento de GI: autorizar un paquete clínico que escriba
   anticoagulación/antiagregante y vasopresor, o aceptar el **rechazo previo** de los encuentros que los
   usan. Sin una de las dos, una autoridad hemodinámica en GI enseñaría un paciente que no responde a un
   vasopresor.
4. **Leer las cuatro diferencias parcialmente declaradas** (`hr`, `crt_s`, `V_ml_eq`,
   `consciousness_level`) y decir, para cada una, si la causa declarada de la Fase 2 la explica en los
   escenarios de esta batería o si entra en el dominio de autoridad como diferencia abierta. Ninguna cae en
   el dominio hemodinámico mínimo salvo `crt_s`, que es la razón de ofrecer CRT como opción separada.
5. Decidir el entorno del primer experimento y que el primer piloto queda excluido por configuración.
6. Conceder, por escrito, la autoridad limitada: ningún paquete se la concede a sí mismo.

### P3-12 · Veredicto

**A · `EVIDENCE_SUFFICIENT_FOR_FACULTY_AUTHORITY_DECISION`.**

La evidencia alcanza para decidir, y lo que la evidencia soporta hoy **no** es «enciéndelo como está»: el
vacío de tratamiento, la falta de una instantánea aprobada y la lectura pendiente de las cuatro diferencias
parcialmente declaradas son entradas de la decisión, no huecos de la evidencia. Nada que yo pueda producir
sin una decisión docente cambia esa decisión.

Lo que **no** sostengo: que la sombra de GI sea fiel en los seis escenarios con vacío de tratamiento, ni que
«ninguna divergencia inesperada» signifique fidelidad ahí; ni que el motor heredado tenga razón donde cae
fuera del tramo de testigos; ni que el golden explique las cuatro diferencias parcialmente declaradas en los
escenarios de esta batería. Las tres son lecturas docentes pendientes, y están nombradas como tales.

## P3-13 · Diseño del arnés de autoridad limitada (sin implementar)

### P3-13-1 · Modos

`LEGACY` → `SHADOW_COMPARE` → `LIMITED_COMMON_AUTHORITY` (este último **no** existe en el tiempo de
ejecución y este paquete no lo crea). Transiciones permitidas sólo en el arranque del encuentro, nunca a
mitad. El modo de autoridad exigiría, de forma conjunta: bandera de proceso explícita, identificador de una
instantánea **aprobada**, lista blanca de casos, y entorno marcado como docente o de desarrollo. Falta
cualquiera: el modo no abre y el encuentro corre en `LEGACY`.

### P3-13-2 · Alcance

Una familia (`gi_bleed`), los casos que el adaptador certifica, un dominio (`{SBP, DBP, MAP}`, con CRT como
opción declarada). Todo lo demás, del legado.

### P3-13-3 · Propiedad de las salidas

| Salida | Dueño |
|---|---|
| SBP, DBP, MAP (y CRT si entra) | **autoridad común** |
| gasto, déficit de presión | común, interno, no mostrado |
| FC, RR, SpO₂, lactato, Hb, V, consciencia | legado |
| pulso, ritmo, paro, colapso | legado |
| destino de órdenes, recibos, tiempos, puntuación, traza, persistencia | legado |
| comparación legado-contra-común | sólo lectura, para la docencia |

Sin propiedad compartida de ninguna salida: cada una tiene un dueño único y declarado.

### P3-13-4 · Propiedad de las entradas

El legado y los contratos siguen siendo autoritativos sobre órdenes, destinos, acciones, tiempos y control
del encuentro. El núcleo común recibe **sólo** entradas ya decididas, exactamente como hoy: la lista asentada
de acciones con la identidad del libro de órdenes.

### P3-13-5 · Frontera transaccional

Por minuto: capturar → calcular en común → **validar** → confirmar las salidas del dominio, o abortar.
Confirmar significa: los campos de presentación del dominio de autoridad se escriben desde el resultado común
de ese minuto, en una sola escritura, después de que la validación pase; nada más se toca. La validación
exige: invariantes del núcleo; valores dentro de la región declarada de la instantánea aprobada; ninguna
acción de manejo sin escritor en ese turno; el digesto del minuto recomputable desde el artefacto; y que el
motor heredado no haya declarado paro.

### P3-13-6 · Reversión

Atomicidad por minuto para la escritura y por encuentro para la decisión: si la validación falla, **no hay
confirmación parcial** —ni un campo— y el encuentro se detiene de forma visible (política D). Un fallo del
núcleo no puede dejar un estado autoritativo a medio actualizar porque la escritura ocurre después de la
validación y en un solo paso.

### P3-13-7 · Persistencia

Cada encuentro con autoridad guardaría: el identificador y la procedencia de la instantánea aprobada; el
digesto de cierre de la Fase 2; el digesto de la capa de la Fase 3; la salida común; la contrafactual del
legado; la divergencia clasificada; el resultado de la validación; y la decisión de reversión o detención.

### P3-13-8 · Puerta obligatoria antes de encender nada

Batería de aceptación completa de GI; prueba de la capa de aplicación —y de navegador **sólo si** la
autoridad llega a la pantalla del residente—; equivalencia de replay; pruebas de reversión; pruebas de acción
no soportada; inyección de fallos; prueba de piloto apagado; instantánea aprobada por docencia; y marco de
aceptación de divergencias aprobado por docencia.

### P3-13-9 · El paquete ejecutable siguiente, exacto (no ejecutado)

- **Archivos:** `runtime_authority.py` (modo, validación, frontera transaccional, persistencia) en la raíz,
  fuera de `clinical_core/`; `test_runtime_authority.py`; un cambio mínimo en `app.py` y en
  `pilot_acceptance.py` en el mismo punto donde hoy observa la sombra.
- **Modo:** `LIMITED_COMMON_AUTHORITY`, apagado por omisión, con las cuatro condiciones conjuntas.
- **Propiedad de estado:** la tabla de P3-13-3, con una prueba que falla si una salida tiene dos dueños.
- **Frontera:** la de P3-13-5, con una prueba de que no hay escritura parcial.
- **Instantánea:** la aprobada, por identificador; sin aprobación, el modo no abre.
- **Reversión:** D, con el encuentro marcado y fuera de la puntuación.
- **Pruebas:** las nueve de la puerta de P3-13-8.
- **Condiciones de parada:** falta la instantánea aprobada; falta el marco de aceptación; aparece una acción
  de manejo sin escritor; el replay no reproduce; o el primer piloto no está excluido por configuración.

### P3-13 · Veredicto

**`LIMITED_AUTHORITY_HARNESS_DESIGN_READY`** — el diseño está completo y no hay bloqueo estructural del
tiempo de ejecución. No autoriza nada: la autoridad exige las cinco decisiones docentes de P3-12.
