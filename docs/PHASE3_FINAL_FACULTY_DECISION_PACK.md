# Fase 3 · P3-30 · Pack de decisión docente — versión definitiva

Sólo lectura. **No concede autoridad, no elige instantánea y no aprueba ninguna magnitud clínica.**
Reemplaza como versión vigente al pack de P3-24 (`docs/PHASE3_FACULTY_AUTHORITY_DECISION_PACK.md`), que
queda como el estado anterior a la resolución de la decisión F.

Se emite porque el veredicto de P3-29 es **A** (`TECHNICALLY_READY_FOR_EXPLICIT_FACULTY_AUTHORITY_GRANT`):
no queda ninguna pieza por construir. Lo que queda es decisión de personas.

## 1 · El experimento futuro, exactamente

| | |
|---|---|
| Familia | GI (`gi_bleed`) |
| Casos | sólo los certificados en lista: `gi_bleed_57m`, `gi_bleed_72f` |
| Dominio autoritativo | **sólo presión**: `sbp` y `dbp` comunes, `map` derivado como lo deriva la pantalla (`(sbp + 2·dbp)/3`, redondeado) |
| Entorno | `development` o `faculty`; nunca producción |
| Pilotaje | excluido por la compuerta (`no_pilot`), no por convención |
| Fallo | duro, visible en la superficie docente; el experimento queda `HALTED/INVALID_FOR_CONTINUATION`; **sin regreso silencioso al legado dentro del mismo encuentro** |
| Acciones no soportadas | el minuto no es elegible y no se compromete nada |
| Instantánea | **un** punto docente explícito, con los siete valores nombrados; sin él la compuerta rechaza |
| Resto del encuentro | el legado sigue siendo la única autoridad de todo lo que no es presión |
| Lo que ve el residente | nada del experimento, ni corriendo ni detenido |
| Puntuación y rúbricas | sin cambio alguno |

## 2 · Los candidatos que sobreviven (sin elegir)

Medido sobre la misma entrada inmutable de `gi_bleed_57m`, un curso tratado (1 L de salino en 15 min) y uno
no tratado, ambos a 240 minutos. Detalle en `docs/PHASE3_SNAPSHOT_CANDIDATE_HARDENING.md`.

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| `preload_curve_scale_ml` | 833,33… (2500/3) | 1500 |
| `arrival_preload_fraction` | 0,5 | 0,7 |
| `pump_preload_coupling` | 1,0 | 1,0 |
| `afterload_sensitivity` | 0,3 | 0,3 |
| `low_output_pressure_knee` | 0,5 | 0,5 |
| `sbp_per_pressure_deficit` | 45 | 45 |
| `dbp_per_pressure_deficit` | 25 | 25 |
| Procedencia Fase 2 | punto comprometido (`canonical`) del registro congelado; coincide con el midpoint declarado en 6 de las 7 magnitudes (la excepción es `pump_preload_coupling`) | el mismo punto, con las **dos** magnitudes identificables llevadas al borde **superior** de su región |
| Posición en la región | **interior** en las dos magnitudes identificables | **frontera** en las dos |
| Curso tratado (SBP, m30→240) | 89 → 80 → 65 → 37 | 88 → 86 → 83 → 77 |
| Curso no tratado (SBP, m30→240) | 80 → 73 → 58 → 29 | 86 → 84 → 81 → 75 |
| Matriz de candidatos (34 corridas del núcleo con ese perfil, P3-22C) | 34 / 34 `TECHNICALLY_VALID`; 0 fallos de frontera, de reejecución y de divergencia estructural | 34 / 34 `TECHNICALLY_VALID`; 0 fallos |
| Batería de autoridad (34 escenarios GI, P3-22) | 26 `TECHNICALLY_VALID` / 8 `NOT_ELIGIBLE` | idéntico: 26 / 8. El conteo **no depende del candidato**: los 8 los bloquea una acción no soportada, no la fisiología |
| Compatibilidad cruzada | 10 casos certificados de 6 familias, sin fallos | sin fallos |
| Sensibilidad (±10 % del ancho de región, dentro de ella) | sin frontera; el curso sigue cayendo en las cuatro perturbaciones | sin frontera; el curso sigue cayendo |
| Ventaja | tiene interior alrededor: hay margen para perturbar sin salir de la región | el curso tratado se mantiene alto, lo que hace más visible la diferencia con el legado |
| Límite | el deterioro es marcado; a 240 min el no tratado llega a SBP 29 | está en el borde: una perturbación hacia afuera sale de la región, y no hay interior de ese lado |
| Depende de magnitudes débilmente identificadas | las cinco inertes (en cursos de GI no mueven la presión) | igual |

`gi_pressure_preload_low` (600 / 0,3) **queda retirado por dominancia estructural**, no por criterio
clínico: alcanza una frontera que la Fase 2 no resuelve en los dos cursos (minutos 103 y 131), su
vecindario muestreado también la alcanza (minutos 150 y 152), y en la matriz de candidatos clasifica
32 `TECHNICALLY_VALID` / 2 `BOUNDARY_FAILURE` —las dos corridas de deterioro terminal, con
`UnresolvedBoundary` del propio núcleo—.

**La elección entre los dos que quedan es docente. La IA no la hace** y tampoco propone un tercer punto.

## 3 · Las decisiones docentes que faltan

La decisión **F** (política de fallo, dónde se muestra y dónde se guarda el artefacto) **está resuelta e
implementada**: falla dura visible en la superficie docente, experimento `HALTED/INVALID_FOR_CONTINUATION`,
sin trayectoria mixta posterior, sin mutación retrospectiva de los minutos ya comprometidos, y persistencia
en una superficie separada de investigación/depuración de la Fase 3, fuera del esquema congelado de la traza
de la Fase 2 y fuera del alcance del residente. Sale de la lista.

| | Decisión que falta | Qué desbloquea |
|---|---|---|
| **A** | **Instantánea**: elegir `gi_pressure_committed` o `gi_pressure_preload_high` —o pedir otro punto construido con la misma regla—, con los **siete** valores nombrados | la condición `approved_snapshot`; sin esto no hay activación posible |
| **B** | **Criterio de aceptación**: declarar qué hace aceptable el experimento. Hoy el criterio implementado es estructural y causal, con el legado como comparador y **sin ninguna tolerancia numérica**; si se quiere una, la fija docencia | la declaración de aceptación del experimento |
| **C** | **Exclusión por acción no soportada**: confirmar que bloquear `anticoagulation`, `aspirin`, `norepinephrine` y `not_modelled` (8 de 34 escenarios) es la política, en vez de modelar fisiología nueva | nada técnico: la regla ya falla cerrada |
| **D** | **Alcance sólo presión**: confirmar `sbp`/`dbp` comunes con `map` derivado, y CRT diferida | nada técnico: es el dominio implementado |
| **E** | **Entorno**: confirmar `development`/`faculty` con el primer piloto excluido | la activación misma |
| **G** | **Concesión expresa de autoridad**, por escrito, con las cinco anteriores resueltas | todo |

Ninguna de las seis es un problema de ingeniería. Las tres que no desbloquean nada técnico (C, D, E) se
piden igual porque el experimento no debería correr sin que docencia las haya mirado.

## 4 · Plantilla de autorización futura (no ejecutada)

Se incluye porque el veredicto de P3-29 es A. **Esto no es una autorización**: es el texto que docencia
tendría que emitir, completo, para que la activación fuese posible. Mientras los campos estén vacíos, el
registro de instantáneas aprobadas sigue vacío y la autoridad real sigue siendo imposible.

```text
AUTORIZACIÓN DOCENTE — PRIMER EXPERIMENTO DE AUTORIDAD LIMITADA (FASE 3)

Fecha:
Persona docente responsable:

A. INSTANTÁNEA APROBADA
   id:                              [ gi_pressure_committed | gi_pressure_preload_high | otro ]
   preload_curve_scale_ml:          [ valor ]
   arrival_preload_fraction:        [ valor ]
   pump_preload_coupling:           [ valor ]
   afterload_sensitivity:           [ valor ]
   low_output_pressure_knee:        [ valor ]
   sbp_per_pressure_deficit:        [ valor ]
   dbp_per_pressure_deficit:        [ valor ]
   Declaro que estos siete valores son una decisión docente y que entiendo que
   cinco de ellos no son identificables con la evidencia de GI disponible.

B. CRITERIO DE ACEPTACIÓN
   [ estructural y causal, con el legado como comparador, sin tolerancia numérica ]
   [ o bien: tolerancias numéricas explícitas, nombradas aquí ]

C. POLÍTICA DE ACCIONES NO SOPORTADAS
   Confirmo que anticoagulation, aspirin, norepinephrine y not_modelled dejan el
   minuto inelegible, y que no se modela fisiología nueva para este experimento.

D. ALCANCE
   Sólo sbp y dbp comunes, con map derivado por la pantalla. CRT diferida.
   Ninguna otra magnitud pasa a ser autoritativa.

E. ENTORNO
   [ development | faculty ]  · Primer piloto: excluido.
   Familia: gi_bleed · Casos: [ gi_bleed_57m | gi_bleed_72f ]

F. POLÍTICA DE FALLO (ya resuelta; se confirma)
   Falla dura visible en la superficie docente; experimento
   HALTED/INVALID_FOR_CONTINUATION; sin regreso silencioso al legado dentro del
   mismo encuentro; minutos ya comprometidos preservados sin mutación
   retrospectiva; artefacto persistido en la superficie docente de la Fase 3.

G. CONCESIÓN
   Autorizo correr el experimento de autoridad limitada descrito arriba, en el
   entorno indicado, con la instantánea indicada, y entiendo que el resultado no
   es evidencia de validez clínica.

   Firma docente:
```

## 5 · Qué pasaría después de esa autorización (sin autorizar nada)

El trabajo técnico que seguiría a una concesión completa no está hecho y no se hace aquí: cargar el punto
aprobado en el registro, correr el primer encuentro de autoridad en entorno docente, leer su artefacto y
comparar con el contrafactual del legado. Eso es un encargo futuro, no parte de este cierre.
