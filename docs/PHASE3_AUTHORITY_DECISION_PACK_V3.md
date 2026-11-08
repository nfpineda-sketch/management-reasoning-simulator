# Fase 3 · P3-38 y P3-39 · Pack de decisión docente de autoridad — versión 3

Sólo lectura. **No concede autoridad, no elige instantánea y no aprueba ninguna magnitud clínica.**
`APPROVED_SNAPSHOTS` sigue vacío; `COMMON_CORE_RUNTIME_AUTHORITY` sigue en `False`.

Reemplaza como versión vigente a `docs/PHASE3_FINAL_FACULTY_DECISION_PACK.md` (P3-30), que queda como el
estado anterior al ciclo de evidencia. La evidencia medida está en
`docs/PHASE3_SNAPSHOT_EVIDENCE_CYCLE.md` (P3-31 a P3-37); aquí va sólo lo que hace falta para decidir.

Rama `phase-3-runtime-integration`, desde `f6b8408`. Cierre de la Fase 2 `d2cca46`, digesto
`22b90a6f…6ce6a`, sin cambios.

## A · Qué está listo

| | Estado |
|---|---|
| Compuerta de nueve condiciones | lista; con todo puesto lo único que falla es `approved_snapshot` |
| Sitio de llamada en producción | existe y está dormido; el modo se decide una vez, al abrir el encuentro |
| Transacción atómica por minuto | lista; `capture → compute → validate → commit`, con contrafáctico legado |
| Artefacto, persistencia, recuperación y replay | **26 de 26** en el simulacro: compromiso atómico, digesto verificado, identidad coincidente, replay exacto; 30/30 campos de cabecera y 20/20 por minuto |
| Semántica de detención | lista: fallo duro visible, `HALTED/INVALID_FOR_CONTINUATION`, sin regreso silencioso, sin mutación retrospectiva |
| Superficie docente | lista, detrás de la compuerta docente, dibuja sólo lo que devuelve `authority_status()` |
| Aislamiento del piloto y de producción | `DEVELOPMENT_AUTHORITY_EXPERIMENT_ISOLATED`, con el piloto anclado a su propia congelación y fallando cerrado |
| Pruebas sobre este HEAD | 196 aprobadas en 132,8 s en los seis archivos de autoridad |
| **Listo para el candidato 1** | **sí, sin tocar código** |
| **Listo para el candidato 2** | **no**: falta selección de punto en vivo y que el identificador siga al punto (§B y evidencia §7.2–7.3) |

El veredicto A de P3-29 (`TECHNICALLY_READY_FOR_EXPLICIT_FACULTY_AUTHORITY_GRANT`) **se sostiene para la
máquina**, y este ciclo le añade una precisión que P3-29 no había examinado: la disponibilidad del primer
experimento **depende del candidato**.

## B · Los dos candidatos

| | `gi_pressure_committed` | `gi_pressure_preload_high` |
|---|---|---|
| `preload_curve_scale_ml` | **833,3333333333334** (2500/3) | **1500,0** |
| `arrival_preload_fraction` | **0,5** | **0,7** |
| `pump_preload_coupling` | 1,0 | 1,0 |
| `afterload_sensitivity` | 0,3 | 0,3 |
| `low_output_pressure_knee` | 0,5 | 0,5 |
| `sbp_per_pressure_deficit` | 45,0 | 45,0 |
| `dbp_per_pressure_deficit` | 25,0 | 25,0 |
| Procedencia | el punto comprometido del registro congelado (`clinical_core.derived.DEFAULT_PROFILE`); es el punto con el que se produjo **todo** artefacto certificado de la Fase 2 | el mismo punto con las dos magnitudes activas en el tope de su región; **equivale bit a bit**, en las 34 trayectorias de SBP de GI, al testigo ya certificado `gi_region_upper` |
| Identificabilidad | 2 magnitudes identificables desde GI; 1 restringida sólo por ACS y TEP; 1 no identificable por construcción; 3 no se leen | idéntico |
| Geometría | interior en las 2 activas (dist. 0,259 y 0,500); **1 de 7** dimensiones en el borde | **borde en las 2 activas** (dist. 0,000); **3 de 7** en el borde |
| Sensibilidad (±10 % del ancho) | 4 de 4 pasos admisibles; hasta **11,5 mmHg** en la SBP final; 4 de 4 esquinas pareadas admisibles | 2 de 4 admisibles (sólo hacia dentro); hasta **2,8 mmHg**; 1 de 4 esquinas |
| Margen a la primera `UnresolvedBoundary` | 24,2 % del ancho en arribo, 23,6 % en escala; **~14 % con las dos a la vez** | **sin frontera alcanzable** en toda la región |
| Horizonte largo | coherente en las 8 clases; sin tratar a 240 min llega a **28,5 / 31,8** con 150 / 122 minutos bajo 65 | coherente en dirección y orden, pero a 240 min llega a **75,5 / 84,0** y **no cruza 65 en ninguno de los dos casos** |
| Orden temporal | efecto estrictamente posterior a la acción; minutos previos idénticos bit a bit | idéntico |
| Control del sangrado | pendiente al 79,7 % de la del curso sin tratar, contra el 80 % declarado | 79,9 % |
| Entre familias | `NO_INFORMATION` en las 5 familias no GI; 0 contradicciones | igual, 0 contradicciones |
| Simulacro de la tubería | **completo**: 26/26 compromisos, replays y artefactos | **fisiología sí** (34/34 corridas válidas, replay determinista); **composición con la transacción no ejercida** |
| Beneficio principal | único punto ejecutable hoy sin cambiar código; el escenario de deterioro deteriora; evidencia de perturbación por los dos lados | núcleo robusto mucho mayor; sin frontera alcanzable |
| Riesgo principal | el margen conjunto a la frontera es ~14 % del ancho, y a 240 min sin tratar el curso llega muy abajo | el escenario llamado terminal no deteriora dentro de su horizonte; está en el borde, así que la mitad de las perturbaciones no son admisibles; y **requiere código** antes de ser ejecutable |

`gi_pressure_preload_low` (600 / 0,3) sigue retirado por dominancia estructural: alcanza una frontera que la
Fase 2 no resuelve, y su vecindario también.

**Dominancia estructural (P3-31-7): `NO_STRUCTURAL_DOMINANCE`.** Cada candidato gana en criterios
permitidos distintos: `committed` en procedencia, menos supuestos de borde, evidencia de dos lados y
respuesta causal plausible; `preload_high` en margen de frontera y estabilidad local. Ninguno es mejor o
igual en todos.

## C · Qué significa esta evidencia

Tres cosas distintas que no deben mezclarse:

| | Qué quedó establecido | Fuerza |
|---|---|---|
| **Validación de software** | la compuerta rechaza, la transacción es atómica, el artefacto está completo, se persiste, se recupera, se verifica y replaya exacto; la detención es definitiva y declarada; el piloto, la puntuación y el residente quedan fuera de alcance | **fuerte** |
| **Validación del modelo causal** | el sangrado baja la presión, el volumen la sube, el control del sangrado reduce la pendiente exactamente en la fracción declarada, el efecto llega después de la acción, los minutos previos son idénticos bit a bit, no hay ninguna respuesta paradójica en ~1 300 corridas | **moderada**, y valida la **estructura del núcleo**, no los números de ningún candidato |
| **Calibración clínica** | **nada** | **ninguna** |

Un primer experimento de autoridad en desarrollo **no es un estudio de validación clínica** y no debe
presentarse como tal. Es la comprobación de que la tubería hace en vivo lo que hace en sombra, con un punto
nombrado y bajo mirada docente.

## D · Recomendación (consultiva)

**`RECOMMEND_gi_pressure_committed`**, sólo para un primer experimento de desarrollo, y apoyada
exclusivamente en los dos argumentos que sobrevivieron a la revisión adversarial:

1. es el **único punto que la aplicación puede correr hoy** sin cambiar código en la capa de la Fase 3;
2. es el **único candidato con el que el escenario certificado de deterioro terminal deteriora** dentro de
   su propio horizonte, medido con los umbrales que el repositorio ya declara.

**No** está apoyada en validez clínica, **no** en geometría de región, **no** en cercanía al legado y
**no** en que sea el midpoint. La IA no elige: esto es una recomendación, y la decisión es docente.

Si la pregunta fuera «cuál es más robusto frente a la frontera», la respuesta sería la contraria, y está
dicha en §B.

## E · Decisiones docentes que faltan

| | Decisión | Qué desbloquea |
|---|---|---|
| **A** | **Instantánea**: elegir uno de los dos puntos —o pedir otro construido con la misma regla—, con los **siete** valores nombrados, sabiendo que dos determinan el experimento, uno afecta la sombra de ACS y TEP, uno no es identificable con los datos actuales y tres no se leen | la condición `approved_snapshot` |
| **G** | **Concesión expresa** de autoridad para el experimento de desarrollo | que la compuerta pueda abrir |
| **H** (nueva) | **Si la elección es el candidato 2**: autorizar el paquete técnico que falta —selección de punto en vivo y un identificador de instantánea que **siga** al punto, para que la novena condición no quede vacía— antes de cualquier concesión | que el candidato 2 sea ejecutable y su enlace verificable |

Las decisiones **B** (criterio de aceptación estructural y causal, sin tolerancia numérica), **C** (acción
no soportada excluye autoridad), **D** (alcance sólo presión, familia GI), **E** (entorno de desarrollo o
docente; primer piloto sólo legado) y **F** (fallo duro visible, sin regreso silencioso, detención
definitiva) **ya están resueltas** y no se vuelven a abrir aquí.

Este ciclo **no** encontró ninguna decisión residual de criterio de aceptación: el criterio estructural y
causal se pudo aplicar entero sin necesitar un número clínico.

## F · Dos borradores de autorización — **no ejecutados**

Ninguno de los dos bloques está firmado ni aplicado. Mientras sus campos estén en blanco, el registro de
instantáneas aprobadas sigue vacío y la autoridad real sigue siendo imposible.

### OPCIÓN 1 — concesión con `gi_pressure_committed`

```
AUTORIZACIÓN DOCENTE — PRIMER EXPERIMENTO DE AUTORIDAD EN DESARROLLO (OPCIÓN 1)

Instantánea aprobada
  identificador: gi_pressure_committed
  valores (los siete, nombrados):
    preload_curve_scale_ml    = 833.3333333333334
    arrival_preload_fraction  = 0.5
    pump_preload_coupling     = 1.0
    afterload_sensitivity     = 0.3
    low_output_pressure_knee  = 0.5
    sbp_per_pressure_deficit  = 45.0
    dbp_per_pressure_deficit  = 25.0
  entiendo que: dos de estos valores determinan el experimento GI; afterload_sensitivity
  afecta la sombra de ACS y TEP sin que GI pueda verlo; pump_preload_coupling no es
  identificable con los datos actuales; y los tres últimos no se leen hoy.

Alcance
  familia:            gi_bleed, y sólo gi_bleed
  casos:              sólo los certificados en lista: gi_bleed_57m, gi_bleed_72f
  dominio:            sólo presión — sbp y dbp comunes; map derivado como lo deriva la
                      pantalla, (sbp + 2·dbp)/3 redondeado
  todo lo demás:      sigue siendo autoridad del motor heredado

Entorno
  development o faculty; nunca producción
  el primer piloto de residentes queda excluido por la compuerta, no por convención
  almacén de artefactos: obligatorio, ruta absoluta fuera del repositorio

Acciones no soportadas
  anticoagulación, antiagregante, vasopresor, no modelado y cualquier acción futura
  relevante para el manejo sin semántica común certificada hacen el minuto
  INELIGIBLE_FOR_COMMON_AUTHORITY: no se compromete nada

Política de fallo
  HARD_FAIL_VISIBLE_TO_FACULTY: visible de inmediato en la superficie docente
  sin regreso silencioso al legado dentro del mismo encuentro
  sin continuación de una trayectoria mixta
  el experimento queda HALTED/INVALID_FOR_CONTINUATION, apto para reejecución y análisis
  los minutos ya comprometidos se preservan exactamente como ocurrieron

Criterio de aceptación
  estructural y causal; ninguna tolerancia clínica numérica
  el legado es comparador contrafáctico, nunca verdad a la que ajustar

Naturaleza del experimento
  es VALIDACIÓN DE DESARROLLO de la tubería, no un estudio de validación clínica

Firma docente: ____________________    Fecha: ____________
```

### OPCIÓN 2 — concesión con `gi_pressure_preload_high`

```
AUTORIZACIÓN DOCENTE — PRIMER EXPERIMENTO DE AUTORIDAD EN DESARROLLO (OPCIÓN 2)

Precondición técnica, antes de que esta opción sea ejecutable
  hoy la aplicación sólo puede correr el punto comprometido: ShadowSession.start abre el
  runner sin seleccionar punto, y el identificador que la compuerta compara es un literal
  de módulo. Esta opción requiere, autorizado aparte (decisión H):
    1. selección de punto en vivo en la capa de la Fase 3 (fuera de clinical_core);
    2. un identificador de instantánea que siga al punto realmente ejecutado, para que la
       condición «el punto aprobado es el punto que corrió» no quede vacía;
    3. el simulacro de la tubería completa a esa fisiología, que esta noche no se ejerció.
  Nota: en las 34 trayectorias de SBP de GI este punto es idéntico al testigo ya
  certificado gi_region_upper.

Instantánea aprobada
  identificador: gi_pressure_preload_high
  valores (los siete, nombrados):
    preload_curve_scale_ml    = 1500.0      (tope de su región)
    arrival_preload_fraction  = 0.7         (tope de su región)
    pump_preload_coupling     = 1.0
    afterload_sensitivity     = 0.3
    low_output_pressure_knee  = 0.5
    sbp_per_pressure_deficit  = 45.0
    dbp_per_pressure_deficit  = 25.0
  entiendo que: este punto está sobre el borde de la región en las dos magnitudes que
  actúan, así que ninguna perturbación hacia afuera es admisible; y que con él el
  escenario certificado de deterioro terminal no cruza el umbral declarado de 65 mmHg en
  ninguno de los dos casos dentro de su horizonte de 240 minutos.

Alcance, entorno, acciones no soportadas, política de fallo, criterio de aceptación y
naturaleza del experimento: idénticos a la OPCIÓN 1.

Firma docente: ____________________    Fecha: ____________
```

## P3-39 · Punto de control previo a la autoridad

**La afirmación honesta más fuerte que se puede hacer esta noche:**

> **A. `ONE_CANDIDATE_STRUCTURALLY_PREFERRED_FOR_DEVELOPMENT_AUTHORITY`**

**Confianza: 0,65.** La preferencia descansa en dos argumentos que resistieron el ataque —uno es un hecho
de código verificable, el otro una lectura estructural con los umbrales del propio repositorio— mientras
que las ventajas del alternativo se degradan al explicarse por un mecanismo aplanado. No es más alta
porque nada clínico quedó establecido y porque la preferencia podría invertirse si docencia decidiera que
lo que importa es el margen a la frontera y no que el escenario de deterioro deteriore.

**Lo que sigue sin saberse:**

- Si cualquiera de los dos puntos es **clínicamente** correcto. Nada en este ciclo lo toca.
- Qué valor debe tener `afterload_sensitivity`: sólo ACS y TEP lo restringen, con una huella de ≤0,4 mmHg,
  y ninguna de las dos familias corre con autoridad.
- Qué valor debe tener `pump_preload_coupling`: haría falta una familia con pump deprimido **y** cambio de
  volumen, y ninguna certificada tiene las dos cosas.
- Si las tres magnitudes que no se leen deben quedarse en el registro, retirarse o volver a entrar en una
  ecuación futura.
- Cuál es el criterio de aceptación **numérico**, si alguna vez hace falta uno. Hoy no hace falta y no se
  inventó.
- Si el deterioro de `committed` a 240 minutos (SBP 28,5) y el sobrepaso del paquete (SBP 130,3, dentro de
  la envolvente declarada y por encima del legado, que llega a 117) son clínicamente aceptables. Es juicio
  clínico, no medición.
- Qué pasa con la tubería completa sobre la fisiología del candidato 2: no se ejerció.
- Si el experimento es **deseable**. No es una pregunta técnica.
