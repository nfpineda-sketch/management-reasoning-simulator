# Fase 3 — Tasa de sangrado GI y calibración de presión (P3-88 … P3-95)

Rama `phase-3-runtime-integration`, desde `260b131`. **Sólo lectura y análisis**, salvo el registro de la
confirmación docente sobre @60. No cambia fisiología, no cambia restricciones FD-BLD, **no aprueba ninguna
tasa ni ningún parámetro de presión**, no toca `gi_pressure_committed`, no mueve autoridad
(`COMMON_CORE_RUNTIME_AUTHORITY = False`, `APPROVED_SNAPSHOTS` = 1). Ningún archivo de `clinical_core/` cambia.

El bloque de volumen entra **cerrado** como `FACULTY_DEFINED_BEHAVIORAL_REGION`, con la confirmación docente de
que la región es los rangos registrados **intersecados** con todas las restricciones FD-BLD vigentes, incluida
la de 60 minutos. Eso queda registrado en `volume_behaviour_record.R60_INTERPRETATION` con
`is_a_new_clinical_constraint = False`, y cierra TD-130 (30).

---

## §1 (P3-88) Qué significa `bleed_ml_per_min`, y de quién es

### §1.1 Semántica, en las palabras del repositorio

| | |
|---|---|
| **Unidades** | **mL-equivalentes por minuto.** `lactate_rebuild_report.LABELS` la rotula «tasa de sangrado (mL-eq/min)» |
| **Campo real** | `blood_loss_ml_per_min`, en el objeto de sangrado; `blood_anchors` hace `replace(made["bleed"], blood_loss_ml_per_min=values["bleed_ml_per_min"])` |
| **Qué es** | **pérdida de sangre entera modelada, en equivalentes**, no mL literales medidos y no pérdida de glóbulos sola. Entra como `shed_ml += tasa` por minuto, y `shed_ml` es el término negativo del cierre contable de `volume_ml` |
| **Qué no es** | no es «volumen circulante efectivo perdido» (eso es `volume_ml`, que además recibe relleno y cristaloide); no es una coordenada de severidad de familia con otra escala: es el caudal del proceso `WHOLE_BLOOD_LOSS` |
| **Marco** | el mismo de `BloodState`: mL reales del compartimento, **antes** de la conversión `kappa` a la `V` canónica |

Que sean **equivalentes** importa: la pérdida retira volumen **y** masa de Hb en la misma proporción, que es por
qué la Hb sin tratar cae poco (0,027 g/dL a los 60 min en `gi_bleed_57m`) y por qué la dilución del cristaloide
es casi insensible a la tasa (§P3-70, 0,3 % entre 1,5 y 3,5 mL/min).

### §1.2 La cadena, con las ecuaciones exactas

```
tasa  ──►  shed_ml(t) = tasa · t                                   (proceso WHOLE_BLOOD_LOSS)
      ──►  volume_ml = cristaloide_in − cristaloide_out + transfundido + relleno − shed_ml
      ──►  relleno: objetivo = min(capacidad, share · shed_ml);
                    si gap ≤ 0 o −volume_ml ≤ 0  ⇒  0;  si no  min(gap·−expm1(−1/τ_relleno), −volume_ml)
      ──►  V = volume_preload_kappa · volume_ml + outside_v          (invariante, comprobado cada minuto)
      ──►  preload_position = −expm1(−máx(0, llenado) / (escala · P^acoplamiento))
      ──►  output_rel  ──►  pressure_rel  ──►  SBP = SBP_llegada · g(ΔVol),  g = [1−(1−f)e^{−ν·ΔVol}]/f
```

con `ν = volume_preload_kappa / preload_curve_scale_ml`. En GI el motor fija `P ≡ 1` y `T ≡ 1`, así que la
reducción de P3-58 vale exactamente (verificada a 2,2·10⁻¹⁶).

### §1.3 De quién es la tasa: dos decisiones, y no dicen lo mismo

`blood_constraints.CASE_DIMS = ("bleed_ml_per_min", "preload_fraction")` — **estructuralmente es una dimensión
de caso**, y `SHARED` es todo lo demás. Pero `blood_extension` define `COMMON = "bleed_ml_per_min|common"` y la
usa como **una** coordenada compartida, con la posición sí por caso. Las dos decisiones declaradas resuelven la
tensión, y hay que citarlas literales:

> **`bleed_rate_authority`** — «authority policy for the GI bleed rate: a verified **case-specific** rate or
> severity **wins**; an approved GI-family value is only a **fallback**; with neither, migration **fails
> closed**. The policy category only: **no numeric bleed rate is approved**». Política:
> `CASE_OVERRIDES_FAMILY_DEFAULT`. Parámetro: `blood_loss_ml_per_min`. Familia: `gi_bleed`.

> **`bleed_rate_analysis`** — «P2I-2V-R: **for this calibration analysis** the primary uses **one common
> GI-family candidate rate** for both cases (no case declares a verified rate, and **case differences are not
> to be explained prematurely by separate rates**); **case-specific rates are the sensitivity variant**. The
> production authority policy is unchanged and **no family default is populated**».

**¿Fue alguna vez una decisión docente que la tasa GI fuera compartida? No.** Lo compartido es una elección
**metodológica** de P2I-2V-R, declarada como tal y motivada por prudencia (no explicar diferencias entre casos
con tasas distintas antes de tiempo). La política de producción dice lo contrario: **el caso gana**. Y la
variante de sensibilidad existe y está vigente: `CASE_SPECIFIC = "V8_case_specific_bleed_rate"`, presente en
`VARIANTS`. (No aparece en los veredictos **por caso** porque una variante que cambia la tasa por caso no es
una lectura del mismo candidato; en el ciclo anterior leí esa ausencia como retiro, y era una lectura mía
equivocada, corregida aquí.)

### §1.4 Historia de los valores

| Valor / rango | Fuente | Estado | Razón declarada | Legado | Aprobado | Sintético | Provisional |
|---|---|---|---|---|---|---|---|
| **2,5** | `blood_anchors.REFERENCE` | valor de referencia | «the canonical **provisional** values (P2I-2T)» | no | **no** | no | **sí** |
| **(1,25; 2,5; 5,0)** | `blood_anchors.EXPLORATION` | rejilla de exploración | «**SYNTHETIC** exploration ranges: **neither** candidate bands **nor** approved values» | no | **no** | **sí** | — |
| **3,0 / 2,0** | `blood_constraints.PROBES` P1/P2 | sondas fuera de rejilla | pre-congelación, «off-grid probe points» | no | no | sí | — |
| **borde superior abierto** | `blood_extension.OPEN_EDGES[COMMON]` | estado de borde | P2I-2W declaró el borde superior **abierto** | no | no | — | — |
| **«2.5»** | `lactate_rebuild` / `blood_fluid_tau_closure` | clave de lectura marginal | reutilización de la rejilla, no una decisión | no | no | sí | — |
| **ninguno** | política de autoridad | — | «**no numeric bleed rate is approved**» y «**no family default is populated**» | — | — | — | — |

**Ningún valor numérico de tasa ha sido aprobado nunca, y no hay valor por omisión de familia poblado.**

> ### Veredicto P3-88
> **`C · BLEED_RATE_IS_A_SHARED_CANDIDATE_BUT_NOT_SEMANTICALLY_REQUIRED_TO_BE_COMMON`**
>
> Es una **dimensión de caso** por estructura (`CASE_DIMS`), la política de producción prefiere el caso
> (`CASE_OVERRIDES_FAMILY_DEFAULT`), y lo compartido es una convención **de análisis** de P2I-2V-R con su
> variante de sensibilidad declarada. No es **A** porque nunca se decidió que fuera común; no es **B** porque
> el análisis vigente sí la trata como candidata compartida y eso está declarado; no es **D** porque la
> semántica **no** es ambigua: está escrita en dos decisiones y en el campo del núcleo.

---

## §2 (P3-89) Qué identifica la tasa

### §2.1 Inventario de evidencia

| Evidencia | Etiqueta | Nota |
|---|---|---|
| Cantidad de hemorragia redactada | **`UNUSABLE`** hoy | ningún caso declara una tasa ni un volumen perdido verificados: lo dice `bleed_rate_analysis` («no case declares a verified rate») |
| Duración redactada | **`UNUSABLE`** hoy | misma razón |
| Hb seriada | **`FACULTY_BEHAVIORAL_CONSTRAINT`** (`U-HB`) | pero la pérdida es de sangre **entera**: retira volumen y masa a la vez, así que la Hb sin tratar apenas se mueve (0,027 g/dL a 60 min). Informa poquísimo sobre la tasa |
| Presión seriada | **`UNUSABLE` por decisión** | `blood_constraints` excluye **a propósito** SBP y MAP: «SBP / MAP stay context only» |
| Restricciones de salida (`U-OUT`) | **`FACULTY_BEHAVIORAL_CONSTRAINT`** | envolventes **por caso**, declaradas «clinical calibration envelopes, **not legacy targets**». Es la única evidencia no circular sobre la salida (FD-P3-61) |
| Restricciones de relleno (FD-BLD-07/08/09) | **`FACULTY_BEHAVIORAL_CONSTRAINT`** | leen el relleno, cuyo objetivo es `share · shed_ml`: dependen de la **pérdida acumulada**, no de la tasa instantánea |
| Momento del tratamiento | **`MODEL_DERIVED`** | lo fija el escenario, no observa la tasa |
| Narrativa del caso | **`UNUSABLE`** hoy | no hay tasa ni volumen declarados |
| Trayectoria del legado | **`LEGACY_COMPARATOR`** | no es evidencia clínica; ya declarado en FD-P3-61 |
| Supuestos sintéticos de familia | **`SYNTHETIC`** | `EXPLORATION` lo dice de sí misma |

**No hay ninguna evidencia `INDEPENDENT_CLINICAL_AUTHORED` sobre la tasa.** Es el hecho central de este
paquete.

### §2.2 Qué acota `U-OUT`, exactamente

Texto literal: «effective output relative to **the case's authored arrival output**, untreated active
bleeding», con envolventes **por caso**:

| | 30 min | 60 min | 120 min |
|---|---|---|---|
| `gi_bleed_57m` | (0,85; 0,95) | (0,70; 0,85) | (0,45; 0,65) |
| `gi_bleed_72f` | (0,90; 0,98) | (0,80; 0,92) | (0,60; 0,78) |

Y su implementación: «the case's GI bleed **at the candidate's rate** from minute 0, no treatment, **the
candidate's own haemodynamics**». Es decir: **lee la trayectoria conjunta**, tasa × estado de volumen × mapa de
presión. No acota la tasa por separado.

**Y se puede decir con precisión cuánto.** Medido por bisección adaptativa, el intervalo de tasas que satisface
`U-OUT`:

| Punto de presión | `gi_bleed_57m` | `gi_bleed_72f` | Intersección |
|---|---|---|---|
| comprometido (escala 833,33; f 0,5) | [2,5497; 3,7234] | [1,6894; 2,8038] | **[2,5497; 2,8038]** |
| escala 600, f 0,5 | [1,8358; 2,6809] | [1,2164; 2,0188] | [1,8358; 2,0188] |
| escala 1500, f 0,5 | [4,5894; 6,7021] | [3,0410; 5,0469] | [4,5894; 5,0469] |
| escala 833,33, f 0,3 | [1,1874; 1,7982] | [0,7655; 1,2345] | [1,1874; 1,2345] |
| escala 833,33, f 0,7 | [5,0721; 7,0146] | [3,5200; 5,6009] | [5,0721; 5,6009] |
| cresta P3-68 (1100; 0,45) | [2,8241; 4,1670] | [1,8562; 3,0538] | [2,8241; 3,0538] |

El intervalo se mueve un **factor 4,3** entre los extremos de los testigos de presión. Y hay un invariante
exacto: **el intervalo depende sólo de `tasa / escala`**, medido a nueve cifras —0,003059622, 0,003059623,
0,003059624, 0,003059622 para escalas 600, 833,33, 1100 y 1500—. Con `ν = kappa/escala`, eso significa que
`U-OUT` acota **el producto `tasa · ν`**, no la tasa.

### §2.3 Circularidad, explícita

Sí, y es **estructural**, no accidental:

1. `U-OUT` es la **única** evidencia docente no circular sobre la salida (FD-P3-61: las envolventes excluyen
   SBP y MAP a propósito, y el legado no es evidencia).
2. `U-OUT` acota **un** grado de libertad: el producto `tasa · ν`.
3. Elegir la tasa para satisfacer `U-OUT` y después calibrar `ν` contra el **mismo** `U-OUT` intenta extraer
   **dos** números de una restricción que sólo fija **uno**. El segundo número no sale de la evidencia: sale de
   lo que se fijó primero.

**Esto hace circular cualquier calibración secuencial de tasa y presión que use `U-OUT` dos veces.** No es una
objeción retórica: es una consecuencia del invariante medido en §2.2.

### §2.4 Sensibilidad analítica

`shed_ml(t) = tasa · t`, así que la tasa entra en el volumen **linealmente en el tiempo** y sólo por la
**pérdida acumulada**: dos tasas distintas no se distinguen en un instante, se distinguen por la **pendiente**
del descenso de volumen. Y como `g` es una función del `ΔVol` acumulado, la salida y la presión heredan eso:

- la tasa **no** es observable en un valor puntual de volumen, salida o presión;
- es observable en la **pendiente temporal** de la pérdida acumulada;
- pero esa pendiente llega a la salida **multiplicada por `ν`**, y ahí se confunde con el mapa de presión.

> ### Veredicto P3-89, por caso
> `gi_bleed_57m`: **`IDENTIFIABLE_ONLY_JOINTLY_WITH_PRESSURE`**
> `gi_bleed_72f`: **`IDENTIFIABLE_ONLY_JOINTLY_WITH_PRESSURE`**
>
> No es «parcialmente identificable»: la tasa **absoluta** no está acotada en absoluto por la evidencia
> vigente. Lo que está acotado es `tasa · ν`.

---

## §3 (P3-90) Compartida o por caso

### §3.1 Las tres hipótesis con las restricciones independientes vigentes

Usando **sólo** `U-OUT` (la única evidencia docente no circular sobre la salida) y sin usar el legado como
verdad, en el punto comprometido:

| Hipótesis | Resultado |
|---|---|
| **H1 · una tasa común** | **Factible**: la intersección es [2,5497; 2,8038], anchura 0,2542. No vacía en **ninguno** de los seis testigos de presión |
| **H2 · tasas por caso** | **Factible y más holgada**: 57m [2,5497; 3,7234] (anchura 1,174), 72f [1,6894; 2,8038] (anchura 1,114) |
| **H3 · región de familia con punto por caso** | **Factible**: la unión es [1,6894; 3,7234], y cada caso elige dentro de su propio subintervalo |

Forzar una tasa común descarta el **78 %** de la anchura admisible de cada caso (0,254 contra 1,174 y 1,114).

### §3.2 El cruce cerca de 2,75, refinado — y corrige el planteamiento

P3-87 muestreó 2,0 / 2,25 / 2,5 / 2,75 / 3,0 / 3,25 / 3,5 y encontró **un solo** valor compartido: 2,75. Con
bisección adaptativa, la banda común real en el punto comprometido es **[2,5497; 2,8038]**.

**El «único valor» era un artefacto del paso de 0,25 del muestreo.** La rejilla sólo contenía un punto de una
banda de anchura 0,254; 2,6; 2,7 y 2,8 también la satisfacen. Lo digo así porque el encargo anterior invitaba a
leer 2,75 como una intersección puntual, y no lo es. **Y sigue sin autorizar ningún valor**: una banda no es
una aprobación.

### §3.3 Estabilidad sobre la región cerrada de volumen

> **`ROBUST_TO_VOLUME_REGION`**

Medido en dos puntos muy distintos de la región cerrada —(e, s, τ) = (0,22; 0,4; 60) y (0,16; 0,2; 120)—: el
intervalo de tasa sale **idéntico a nueve decimales** en los dos casos. Y la razón es **estructural**, no
numérica: `U-OUT` lee el curso **sin tratar**, donde no hay cristaloide. No hubo que elegir ningún punto de
volumen.

### §3.4 Dependencia del punto de presión — esto es lo central

> **`STRONGLY_DEPENDENT`**, y de forma exactamente caracterizada.

El intervalo se mueve un factor 4,3 entre f = 0,3 y f = 0,7, y un factor 2,5 entre escala 600 y 1500 — pero
**sólo a través del producto**. En la coordenada `c = tasa / escala` el invariante es exacto:

| f | `c` admisible 57m | `c` admisible 72f | común | razón inferior 57m/72f |
|---|---|---|---|---|
| 0,30 | [0,00142490; 0,00215780] | [0,00091860; 0,00148140] | [0,00142490; 0,00148140] | 1,5512 |
| 0,40 | [0,00213814; 0,00318472] | [0,00139531; 0,00227831] | [0,00213814; 0,00227831] | 1,5324 |
| 0,45 | [0,00256734; 0,00378816] | [0,00168745; 0,00277623] | [0,00256734; 0,00277623] | 1,5214 |
| 0,50 | [0,00305962; 0,00446809] | [0,00202732; 0,00336460] | [0,00305962; 0,00336460] | 1,5092 |
| 0,60 | [0,00430231; 0,00613322] | [0,00290745; 0,00479178] | [0,00430231; 0,00479178] | 1,4798 |
| 0,70 | [0,00608656; 0,00841752] | [0,00422402; 0,00672113] | [0,00608656; 0,00672113] | 1,4409 |

**Dos lecturas que importan:** la común **nunca** es vacía; y **la razón entre las tasas que los dos casos
exigen es casi constante, 1,44–1,55**, aunque el nivel absoluto no esté acotado en absoluto. Es decir: la
evidencia vigente **identifica el cociente de tasas entre los dos casos** —la diferencia clínica redactada entre
los dos pacientes, expresada como tasa— y **no** identifica el nivel.

> ### Veredicto P3-90
> **`COMMON_REGION_WITH_CASE_POINTS_PREFERRED`**
>
> Una tasa común es factible en todos los testigos, así que H1 no está refutada; pero cuesta el 78 % de la
> anchura de cada caso, la política de producción declarada prefiere el caso
> (`CASE_OVERRIDES_FAMILY_DEFAULT`), y la evidencia identifica precisamente **el cociente entre casos**, que es
> lo que una región de familia con punto por caso representa. No es `COMMON_RATE_STRUCTURALLY_SUPPORTED`
> porque «factible» no es «respaldado estructuralmente»: nada en la estructura exige una tasa común, y la
> estructura (`CASE_DIMS`) dice lo contrario. No es `CASE_SPECIFIC_RATES_PREFERRED` a secas porque la cautela
> de P2I-2V-R sigue siendo buena: la región compartida es lo que evita explicar prematuramente las diferencias
> de caso con tasas libres. Y no es `CURRENT_EVIDENCE_CANNOT_DECIDE` porque sí decide la **estructura**,
> aunque no el nivel.

---

## §4 (P3-91) Región conjunta tasa × ν × f

### §4.1 Sin colapso a un punto

La eliminación es **analítica**: `U-OUT` depende de (tasa, escala) sólo por `c = tasa/escala`, verificado a
nueve cifras, así que la región conjunta de tres coordenadas es el producto de **una curva de intervalos en
`c`** por el eje `f`. No hace falta ninguna rejilla cartesiana en tres dimensiones: basta la bisección 1-D en
`c` para cada `f`, que es lo que da la tabla de §3.4.

### §4.2 Papel de cada restricción

| Restricción | Papel | Evidencia |
|---|---|---|
| **`U-OUT`** | **`JOINT_ONLY`**, y `CIRCULAR_IF_REUSED` | Acota `tasa · ν` y nada más; usarla dos veces es la circularidad de §2.3 |
| **`FD-BLD-02`** (vía de glóbulos) | **`JOINT_ONLY`**, asimétrica por caso | Medido: en `57m` su intervalo de tasa es **idéntico a escala 833 y 1500** ([0,2; 9,3258]), así que ahí es **sólo informativa de la tasa** y muy laxa; en `72f` es **vacía** a la escala comprometida y no vacía a 1500, así que ahí es **informativa del mapa de presión**. No se puede clasificar sin decir el caso |
| **`U-HB`** | `RATE_INFORMATIVE` en teoría, **inerte** en la práctica | La pérdida es de sangre entera: retira volumen y masa a la vez, así que la Hb sin tratar cae 0,027 g/dL a 60 min |
| **FD-BLD-07/08/09** (relleno) | `RATE_INFORMATIVE` por la **pérdida acumulada** | el objetivo de relleno es `share · shed_ml` |
| **FD-BLD-04/05/06** (cristaloide) | **`REDUNDANT`** para este problema | medido: invariantes a la tasa y a las coordenadas de presión (P3-70, P3-76) |
| SBP / MAP | **excluidas por decisión** | «SBP / MAP stay context only» |

### §4.3 Clasificación de la región

> **`JOINT_MANIFOLD_ONLY`** en las coordenadas crudas (tasa, ν, f), porque tasa y ν entran **sólo por su
> producto**. Equivalentemente, **`NONEMPTY_2D_REGION`** en las coordenadas identificables (`tasa · ν`, `f`),
> no vacía para todo `f ∈ [0,30; 0,70]` explorado.

No es `EMPTY_CONTRADICTION`, no es `DISCONNECTED_REGION` (la común es un intervalo en cada `f`), y no es
`NARROW_RATE_BAND_PLUS_PRESSURE_REGION`: no hay banda de tasa sin decir antes el punto de presión.

### §4.4 Dónde está el punto de desarrollo actual

El punto comprometido es escala 833,33 y f 0,5, y la tasa de referencia del repositorio es 2,5. Entonces
`c = 2,5 / 833,3333 = 0,00300000`, contra la banda común a f = 0,5, `[0,00305962; 0,00336460]`.

**Está fuera, justo por debajo: un 1,95 % por debajo del borde inferior.** Para entrar en la banda a esa escala
haría falta una tasa ≥ 2,549686. Es **descriptivo**: la región no se ajusta para incluirlo, y la tasa no se
mueve.

---

## §5 (P3-92) Coordenadas de comportamiento de presión

### §5.1 Qué se puede juzgar **sin** la tasa

De la forma cerrada `g(ΔVol) = [1 − (1−f)·e^{−ν·ΔVol}]/f`, verificada a 2,2·10⁻¹⁶ contra el núcleo congelado:

| Cantidad | Fórmula | ¿Depende de la tasa? |
|---|---|---|
| **Meseta** | `1/f` | **No.** Es el límite de `g` cuando `ΔVol → ∞`: una propiedad del mapa |
| **Pendiente cerca de la llegada** | `m = (1−f)·ν/f` por mL **efectivo** | **No.** Es `∂g/∂ΔVol` en `ΔVol = 0` |
| **Respuesta a una perturbación impuesta de volumen efectivo, a estado fijo** | `g(ΔVol₂)/g(ΔVol₁)` | **No.** Sólo entra `ΔVol`, que es el argumento impuesto |
| Curvatura relativa | `∂²g/∂ΔVol² / ∂g/∂ΔVol = −ν` | **No**, e identifica `ν` por sí sola **si** `ΔVol` se conoce |

La razón estructural: la tasa **no aparece en `g`**. Aparece sólo en cómo se llega a un `ΔVol` dado. Así que
**toda cantidad expresada por unidad de volumen efectivo es independiente de la tasa.**

### §5.2 Qué depende necesariamente de la tasa

Todo lo que se lea **en un minuto de la trayectoria**: la salida a los 30, 60 o 120 minutos; la SBP a una hora
dada; el tiempo hasta un umbral. Porque el `ΔVol` de ese minuto es `−tasa · t` más tratamiento. **A la docencia
no se le puede pedir juzgar esas cantidades como propiedades del mapa de presión**: son propiedades de la
trayectoria, y mezclan las dos capas. Es exactamente el error que `U-OUT` hace inevitable, y por eso `U-OUT` es
`JOINT_ONLY`.

### §5.3 Las preguntas docentes, una capa por pregunta

**Capa MAPA DE PRESIÓN** (independiente de la tasa; se pregunta por volumen **efectivo**):

- **M1.** En uno de estos adultos con hemorragia GI, **si se repusieran 100 mL efectivos de volumen
  intravascular**, ¿cuántos mmHg de sistólica debería subir, partiendo de su presión de llegada? *(hoy el punto
  comprometido da 10,56 y 11,76 mmHg por 100 mL efectivos en los dos casos)*
- **M2.** ¿Hasta dónde puede llegar la sistólica si se repusiera volumen **sin límite**, como múltiplo de la de
  llegada? *(hoy el punto comprometido da 2,0×, es decir 176 y 196 mmHg)* — y si la meseta **no** es una
  cantidad clínicamente juzgable porque nunca se observa saturación, decirlo: entonces `f` se decide por M1 más
  un rango de plausibilidad, no por M2.

**Capa TASA DE ENFERMEDAD** (no es el mapa; se pregunta por el proceso):

- **R1.** Para la severidad redactada de cada uno de estos dos casos, ¿qué **caudal de pérdida de sangre
  entera** es clínicamente defendible, en mL-eq/min? *(hoy ninguno está aprobado; el repositorio usa 2,5 como
  valor provisional)*
- **R2.** ¿Se acepta que los dos casos tengan **tasas distintas dentro de una región de familia**, como la
  política `CASE_OVERRIDES_FAMILY_DEFAULT` ya prevé? La evidencia vigente identifica el **cociente** entre
  ellas, 1,44–1,55; no el nivel.

**Ninguna pregunta mezcla las capas**, y ninguna pide `ν`, `f`, `escala` ni `kappa`.

---

## §6 (P3-93) Qué base de volumen usar para la presión

**§6.1 Base de volumen efectivo.** A favor: es el **argumento propio** del mapa (`g` es función de `ΔVol`), es
**independiente de la tasa** (§5.1) y la conversión es exacta. En contra: **no es observable clínicamente**;
nadie mide los mL efectivos.

**§6.2 Base de volumen infundido.** Traducción con la región **cerrada** de volumen, sin colapsar la banda:
100 mL infundidos entregan entre **15,00 y 27,07 mL efectivos** en el pico — factor **1,8048×**. Propagado a
la pendiente, con el punto comprometido como ilustración y **no** como recomendación: 10,56 mmHg por 100 mL
efectivos se convierte en **1,58 a 2,86 mmHg por 100 mL infundidos** en `gi_bleed_57m`, y 11,76 en **1,76 a
3,18** en `gi_bleed_72f`. La banda **no se colapsa**: es parte del resultado.

> ### Veredicto P3-93
> **`C · BOTH_SHOULD_BE_REPORTED_WITH_EFFECTIVE_VOLUME_PRIMARY`**
>
> La pregunta **primaria** va en volumen efectivo, porque es la única forma de preguntar por el mapa sin
> arrastrar la tasa ni la retención. Y se reporta **además** la traducción a volumen infundido con su banda de
> 1,8048×, porque es lo que una persona docente puede reconocer clínicamente. No es **A** porque pedir sólo lo
> no observable deja la pregunta sin anclaje reconocible; no es **B** porque el infundido arrastra una banda que
> no se puede ocultar; y no es **D** porque la decisión de formato no necesita más evidencia.

---

## §7 (P3-94) Revisión adversarial

| Ataque | Veredicto | Por qué |
|---|---|---|
| Fijar la tasa en 2,75 porque los casos se cruzan ahí | **`UNSUPPORTED`** — y este ciclo lo **refuta con medida**: el cruce no es un punto, es la banda [2,5497; 2,8038], y «2,75» era el único punto que el muestreo de paso 0,25 contenía. Además la banda se mueve un factor 4,3 con el punto de presión |
| Suponer que una tasa debe servir a los dos casos | **`UNSUPPORTED`** | `CASE_DIMS` la declara dimensión de caso y la política es `CASE_OVERRIDES_FAMILY_DEFAULT`. Lo compartido es una convención de análisis, declarada como tal |
| Usar `U-OUT` dos veces | **`CIRCULAR`**, y es el hallazgo central | `U-OUT` acota **un** grado de libertad (`tasa · ν`); extraer dos de ella es circular por construcción (§2.3) |
| Tasas por caso como sobreajuste | **`WEAK`** | Es un riesgo real —dos pacientes redactados, dos tasas libres explican cualquier diferencia— y es exactamente lo que la cautela de P2I-2V-R evita. Por eso el veredicto es **región común con punto por caso**, no tasas libres |
| Tratar la tasa del modelo como pérdida de sangre observada | **`WEAK`** | Son **mL-equivalentes** de sangre entera modelada, no un caudal medido. Ninguna evidencia `INDEPENDENT_CLINICAL_AUTHORED` la respalda, y así está etiquetado |
| Tratar el volumen efectivo como medido clínicamente | **`ROBUST`** (no se hace) | §6 lo dice explícitamente: no es observable, y por eso se reporta **además** la traducción al infundido con su banda |
| Fijar el punto de presión porque la autoridad de desarrollo ya lo usa | **`ROBUST`** (no se hace) | `gi_pressure_committed` se aprobó **sólo** para el experimento de desarrollo (FD-P3-42), y aquí se usa como **testigo**, uno de seis. Y su `c = 0,00300` queda **fuera** de la banda: si lo hubiera usado como ancla, el resultado habría sido el contrario |
| Usar la meseta sin haber observado nunca saturación | **`WEAK`**, y declarado | Es una objeción buena: la meseta `1/f` nunca se observa en estos cursos. Por eso M2 lleva la salida explícita de que, si no es juzgable, `f` se decide por M1 más plausibilidad |
| Usar la pendiente con la base de volumen incierta | **`WEAK`**, y acotado | La pendiente por mL **efectivo** es exacta e independiente de la tasa; la incertidumbre entra sólo al traducir a infundido, y es 1,8048×, reportada y no colapsada |
| Afirmar que dos casos redactados identifican un parámetro de familia | **`ROBUST`** (no se afirma) | Lo que se afirma es más débil y está medido: identifican el **cociente** entre sus tasas (1,44–1,55) y **no** el nivel |
| Estrechar la región conjunta con puntos medios escondidos | **`ROBUST`** (no se hace) | Los bordes salen de bisección sobre el evaluador congelado; no hay ningún punto medio en ningún resultado, y la región se reporta como intervalos |

Cinco `ROBUST`, cuatro `WEAK` declaradas, **una `CIRCULAR`** (la reutilización de `U-OUT`, que es el hallazgo
del ciclo) y **dos `UNSUPPORTED`** que este ciclo refuta con medida.

---

## §8 (P3-95) Pack de decisión docente

1. **Qué significa la tasa.** Caudal de pérdida de **sangre entera modelada**, en **mL-equivalentes por
   minuto**, en el proceso `WHOLE_BLOOD_LOSS` del estado sanguíneo compartido. Retira volumen y masa de Hb en
   la misma proporción. No es un caudal medido.
2. **Común, por caso o indeterminada.** **Por caso por estructura y por política**
   (`CASE_DIMS`, `CASE_OVERRIDES_FAMILY_DEFAULT`); lo compartido es una convención de análisis de P2I-2V-R con
   variante de sensibilidad declarada (V8). **Nunca fue una decisión docente.**
3. **Qué evidencia la acota.** Ninguna evidencia clínica independiente redactada. `U-OUT` acota el producto
   `tasa · ν`; `U-HB` es casi inerte porque la pérdida es de sangre entera; SBP y MAP están excluidas por
   decisión; el legado no es evidencia.
4. **Cuánto se acopla con la presión.** Totalmente: `U-OUT` depende de (tasa, escala) **sólo** por
   `tasa/escala`, verificado a nueve cifras. El intervalo de tasa se mueve un factor 4,3 entre los testigos de
   presión explorados.
5. **Región conjunta.** `JOINT_MANIFOLD_ONLY` en (tasa, ν, f); no vacía en todo `f ∈ [0,30; 0,70]`. La
   intersección entre casos nunca es vacía, y la razón entre sus tasas es 1,44–1,55.
6. **Dónde está el punto actual.** Tasa 2,5 con el punto comprometido da `c = 0,00300`, **un 1,95 % por debajo**
   de la banda común [0,00305962; 0,00336460]. Fuera, justo por debajo.
7. **Qué es independiente de la tasa.** La meseta `1/f`, la pendiente por mL **efectivo**, la respuesta a una
   perturbación impuesta de volumen efectivo y la curvatura relativa `−ν`. Porque la tasa no aparece en `g`.
8. **Qué depende de la tasa.** Todo lo leído en un minuto de la trayectoria: salida a 30/60/120, SBP a una hora
   dada, tiempo hasta un umbral. **No se le pueden presentar a la docencia como propiedades del mapa.**
9. **Base de volumen recomendada.** Efectivo como **primaria**, con la traducción a infundido y su banda de
   1,8048× reportada al lado (§6).
10. **Decisiones docentes que faltan.** M1 y M2 (capa mapa, en volumen efectivo), R1 y R2 (capa tasa), más las
    dos que siguen abiertas de antes: la procedencia legado del canónico de `preload_curve_scale_ml`
    (TD-130 (23)) y la región declarada de `volume_preload_kappa` (TD-130 (24)), sin la cual `ν` no se separa
    en sus dos factores.

> ### Veredicto P3-95
> **`C · RATE_AND_PRESSURE_MUST_BE_CALIBRATED_JOINTLY`**
>
> No es **A** porque nombrar la presión sola no cierra nada: `U-OUT` fijaría entonces la tasa, y eso es la
> circularidad de §2.3. No es **B** porque decidir la tasa primero tiene el problema **simétrico**: `U-OUT`
> fijaría entonces `ν`, con la misma circularidad, y no hay ninguna razón estructural para preferir un orden —
> la evidencia acota el producto, no un factor. No es **D** porque sí hay un camino sin evidencia nueva:
> **dos anclas docentes independientes, una en cada capa** (M1 en el mapa, R1 en la tasa), que juntas resuelven
> el producto sin usar `U-OUT` dos veces; `U-OUT` queda entonces como **comprobación**, que es su papel
> legítimo. No es **E** porque la ecuación no necesita revisión estructural.

### Interfaz de decisión conjunta — **diseño, no ejecutado**

Lo que el «IF C» pide. **No elige ningún punto.**

| Campo | Capa | Qué se pide | Hoy |
|---|---|---|---|
| `slope_mmHg_per_100ml_effective` | MAPA | rango, por caso o común | ilustración: 10,56 y 11,76 |
| `plateau_multiple_of_arrival` | MAPA | rango, **o** la marca `NOT_CLINICALLY_JUDGEABLE` | ilustración: 2,0× |
| `bleed_rate_ml_eq_per_min` | TASA | rango **por caso**, dentro de una región de familia | ninguno aprobado |
| `rate_structure` | TASA | `COMMON_POINT` / `COMMON_REGION_WITH_CASE_POINTS` / `CASE_SPECIFIC` | el análisis usa común; la política prefiere el caso |
| `volume_basis` | formato | `EFFECTIVE_PRIMARY_WITH_INFUSED_TRANSLATION` | recomendado en §6 |
| `provenance` | — | de dónde sale cada rango | — |

Reglas de la interfaz, para que no se cuele una aprobación encubierta:

- exige **al menos una** ancla en cada capa; con anclas en una sola capa **rechaza** y nombra la circularidad;
- con las dos anclas, **muestra** el `c = tasa·ν` implicado y si cae en la banda de `U-OUT` — como
  **comprobación**, nunca como fuente del valor;
- si las dos anclas son incompatibles con `U-OUT`, lo **reporta** en vez de ajustar ninguna de las dos;
- **no** propone valores por omisión, y marca toda cifra de hoy como ilustración.
