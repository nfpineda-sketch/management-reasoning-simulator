# Fase 3 · P3-24 · Pack de decisión docente para una primera autoridad limitada

Sólo lectura. **No concede autoridad, no aprueba ninguna magnitud y no elige candidato.** Es el documento
que una docencia necesitaría para decidir, con todo medido y con cada ausencia nombrada.

Estado al escribirlo: `APPROVED_SNAPSHOTS` vacío, puerta de nueve condiciones refutando, digesto de cierre
de la Fase 2 `22b90a6f7f38…` intacto, `clinical_core/` sin cambios desde `d2cca46`, primer piloto congelado
y sólo con el motor heredado.

## 1 · Qué sería autoritativo exactamente

`sbp` y `dbp` del encuentro, calculados por el núcleo común, escritos juntos una vez por minuto. `map` se
escribe **como lo deriva la pantalla** de esas dos (`round((sbp + 2·dbp)/3)`), para que el estado, la
pantalla y la traza de manejo digan el mismo número. Nada más cambia de dueño.

Siguen siendo del motor heredado: `hr`, `respiratory_rate`, `spo2`, `crt_s`, hemoglobina, glucosa, potasio,
FiO₂, lactato, `V_ml_eq`, volumen entregado, unidades transfundidas, pulso, ritmo, consciencia, el colapso,
el paro, **la puntuación**, el destino de las órdenes y la persistencia. Cuatro magnitudes internas (`D`,
`delivery_rel`, `hemostasis_relief`, `transfusion_overload_units`) son sólo comparación.

## 2 · En qué familia y casos

Familia `gi_bleed`; casos `gi_bleed_57m` y `gi_bleed_72f`, lista cerrada. Entorno `development` o
`faculty`. El primer piloto excluido por su propia congelación. El modo se decide una vez, en el minuto 0:
no hay promoción ni retroceso a mitad de encuentro.

## 3 · Qué candidatos de instantánea quedan (P3-24A)

Siete magnitudes hay que nombrar; sólo dos son identificables con la evidencia de GI. CRT queda fuera con
prueba causal: mover su región deja `sbp`, `dbp` y `map` idénticos.

| Magnitud | Región congelada | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|---|
| `preload_curve_scale_ml` | 600 – 1500 | **833,3333…** (midpoint) | **1500** (borde superior) |
| `arrival_preload_fraction` | 0,3 – 0,7 | **0,5** (midpoint) | **0,7** (borde superior) |
| `pump_preload_coupling` | 0,0 – 1,0 | 1,0 (borde superior, punto comprometido) | 1,0 |
| `afterload_sensitivity` | 0,1 – 0,5 | 0,3 | 0,3 |
| `low_output_pressure_knee` | 0,3 – 0,6 | 0,5 | 0,5 |
| `sbp_per_pressure_deficit` | 35 – 55 | 45 (literal del legado adoptado en P2C) | 45 |
| `dbp_per_pressure_deficit` | 15 – 30 | 25 (literal del legado adoptado en P2C) | 25 |

Sin valores por omisión escondidos: las cinco magnitudes que no cambian la presión en estos cursos también
van nombradas, porque una autoridad corre un punto y no un hueco. `gi_pressure_preload_low` quedó retirado
en P3-21 por dominancia estructural (frontera no resuelta en los dos cursos y en todo su vecindario).

## 4 · Qué evidencia sostiene a cada uno (P3-24A)

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| Procedencia | punto adoptado de la Fase 2; midpoint del registro en 6 de 7 | bordes superiores del mismo registro |
| Posición | **interior** de las dos regiones | frontera superior de las dos |
| Batería GI (34 artefactos, mismo insumo) | **34 válidos** | **34 válidos** |
| Cruzado (10 casos certificados, 6 familias) | sin fallos | sin fallos |
| Vecindario ±10 % del ancho de región | 4 de 4 estables, sin frontera, el curso sigue cayendo | 2 de 2 estables |
| Curso no tratado a 240 min | SBP 80 → 29 (se deteriora) | SBP 86 → 75 (apenas se deteriora) |
| Identificabilidad de las otras cinco | ninguna con evidencia de GI | ninguna con evidencia de GI |

## 5 · Qué escenarios quedan excluidos (P3-24B)

De los 34 escenarios de la batería GI: **26 técnicamente válidos** y **8 inelegibles**, por clase de acción:

| Clase bloqueada | Escenarios | Por qué |
|---|---|---|
| `anticoagulation`, `aspirin` | `D_incorrect_treatment` ×2 | el mapeo común no tiene escritor; implementarlos es fisiología nueva y decisión clínica |
| `norepinephrine` | `F_start_stop` ×2, `K_combined_interventions` ×2 | ídem |
| `not_modelled` | `H_unexpected_reasonable` ×2 | el propio motor declara que no modela esa orden, así que un espejo exacto no existe. **Falla cerrado por decisión, no por defecto**: es conservador y la docencia puede revisarlo |

Los 26 válidos comprometen atómicamente, reproducen su minuto desde el artefacto y guardan el contrafactual
heredado: 26 de 26 en las tres cosas.

## 6 · Qué hace un fallo (P3-24 §6)

`HARD_FAIL_VISIBLE_TO_FACULTY`: la transacción aborta, no se escribe ninguna presión, el artefacto de
retroceso queda con lo necesario para reproducir el minuto, y **la autoridad del encuentro se detiene para
siempre** —no hay alternancia minuto a minuto con el legado—. Si el fallo llega después de un commit, la
trayectoria de presión del encuentro queda mezclada y el artefacto lo declara (`mixed_trajectory`): ese
encuentro se lee desde el artefacto y no se continúa.

## 7 · Qué se persistiría (P3-24 §7)

Hoy, **nada**: el artefacto vive en la sesión y el arnés no escribe en ningún sitio. Medido sobre un
experimento real: ~10 KB el primer minuto y ~3,2 KB por minuto adicional en forma completa; la forma
mínima quita lo que se repite y sigue reproduciendo. La recomendación técnica es conservar la entrada
inmutable —sin ella el artefacto describe un experimento que nadie puede reproducir—. **Dónde vive y cuánto
se retiene es decisión docente**, y es el único paquete técnico que queda (P3-20, fila 9).

## 8 · Cómo se replayea (P3-24 §8)

Desde el artefacto solo: cada minuto lleva su entrada inmutable, y `replay_site_artifact` recomputa las
presiones, el digesto del candidato, el de la transacción y lo escrito, y comprueba que el desenlace
grabado sea coherente. Un experimento de tres minutos reproduce sus tres minutos con tres digestos
distintos. Un artefacto editado deja de reproducir. Límite declarado: el digesto no lleva firma, así que
detecta un cambio y no a un falsificador con la misma función de digesto; firmar exige una clave, que es
decisión de infraestructura.

## 9 · Cómo se excluye el piloto (P3-24 §9)

Por su propia congelación: si el despliegue tiene puestas las banderas que `pilot_freeze.RUNTIME_FLAGS`
exige, la condición `no_pilot` falla; si esa congelación no se puede leer, **falla cerrada**. Ninguna
superficie del piloto nombra las banderas de autoridad, y un entorno limpio no abre sesión de autoridad.

## 10 · Qué sigue siendo del legado (P3-24 §10)

Todo lo de la §1 fuera de las dos presiones, y además: el motor heredado **sigue calculando** las presiones
en paralelo como comparador de cada minuto autoritativo, que es lo que hace posible el retroceso y la
lectura posterior. El legado no es verdad clínica de referencia en esa comparación.

## 11 · Qué divergencias quedan sin resolver (P3-24C, sólo dominio de presión)

| Lectura | Resultado |
|---|---|
| Clase de divergencia en los 26 minutos autoritativos | `EXPECTED_ARCHITECTURAL_DIVERGENCE` en los 26: el golden la declara arquitectónica en **todos** los escenarios de GI |
| `UNEXPECTED_STRUCTURAL_DIVERGENCE` | ninguna |
| `PARTIALLY_EXPLAINED_DIVERGENCE` en el dominio de presión | ninguna (las cuatro parcialmente declaradas son `hr`, `crt_s`, `V_ml_eq` y `consciousness_level`, fuera del dominio) |
| Frontera (`COMMON_BOUNDARY`) con el punto comprometido | ninguna en los 34 |
| Legado **dentro** del soporte estructural de la región | `sbp` 32/34, `dbp` 32/34, `map` 33/34 |
| Legado **fuera** del span de los testigos nombrados | `sbp` 2/34, `dbp` 2/34, `map` 1/34 — «fuera» significa fuera del span de los dos testigos, no fuera de la fisiología |
| No comparable | `spo2` (región nula) y `respiratory_rate` (16 de 34 con región nula) quedan fuera del dominio |

**Ninguna tolerancia numérica se definió** para ninguna de estas lecturas, y no la hay que proponer: el
criterio es estructural y declararlo aceptable es la decisión B de abajo.

## 12 · Registro de riesgos (P3-24D)

| Riesgo | Probabilidad | Impacto | Qué lo contiene hoy |
|---|---|---|---|
| **Incertidumbre de parámetros**: cinco magnitudes sin evidencia de GI y dos identificables con dispersión amplia (SBP 19–37 mmHg a las 4 h alrededor del punto) | alta | medio en desarrollo, alto si se extendiera | el dominio es sólo presión, el entorno es docente y la instantánea va nombrada en cada minuto del artefacto |
| **Acciones no soportadas**: cuatro clases bloqueadas | alta (ocurre en 8 de 34) | bajo | falla cerrado y lo dice por escenario |
| **Acoplamiento con las divergencias parciales**: `hr` y `crt_s` siguen siendo del legado mientras la presión sería común | media | medio: un residente podría ver una presión común y una frecuencia heredada que no se explican entre sí | las dos quedan medidas y declaradas; es lectura docente, no defecto |
| **Fallo en tiempo de ejecución**: el minuto cuesta 3–25 ms y recorre el núcleo entero | media | bajo | fallo duro, nada escrito, artefacto de retroceso |
| **Contaminación del piloto** | baja | muy alto | anclaje a la congelación del piloto, fallo cerrado si no se lee, entorno exigido |
| **Retroceso silencioso** | baja | alto | no existe: el fallo detiene la autoridad del encuentro y lo declara |
| **Integridad del artefacto** | baja | medio | digesto sobre todo el contenido, verificación y replay; sin firma, dicho |
| **Cobertura futura de tratamientos** | media | medio | ninguna de las tres terapias se implementó para desbloquear autoridad |

## 13 · Las decisiones docentes exactas que faltan (P3-24E)

| | Decisión | Qué queda bloqueado sin ella |
|---|---|---|
| **A** | **Instantánea**: `gi_pressure_committed` o `gi_pressure_preload_high` (o pedir otra construida con la misma regla), con los siete valores nombrados | la condición `approved_snapshot`: sin esto no hay activación posible |
| **B** | **Criterio de aceptación**: declarar aceptable un criterio estructural y causal, sin tolerancia numérica, con el legado como comparador | la declaración de aceptación del experimento |
| **C** | **Exclusión por acción no soportada**: confirmar que bloquear `anticoagulation`, `aspirin`, `norepinephrine` y `not_modelled` (8 de 34 escenarios) es la política, en vez de modelar fisiología nueva | nada técnico; la regla ya falla cerrada |
| **D** | **Alcance sólo presión**: confirmar `sbp`/`dbp` comunes con `map` derivado, y CRT diferida | nada técnico; es el dominio implementado |
| **E** | **Entorno**: confirmar `development`/`faculty`, con el primer piloto excluido | la activación misma |
| **F** | **Política de fallo**: confirmar el fallo duro visible, y decidir **dónde se muestra y dónde se guarda el artefacto** | el único paquete técnico que queda (P3-20, fila 9) |
| **G** | **Concesión expresa de autoridad**, por escrito, con las seis anteriores resueltas | todo |

**Ninguna de estas decisiones la toma este documento ni la toma el código.**
