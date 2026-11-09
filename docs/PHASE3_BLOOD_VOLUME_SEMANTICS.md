# Fase 3 — Capa semántica de volumen sanguíneo (P3-69 … P3-75)

Rama `phase-3-runtime-integration`, desde `fc698c5`. **Trabajo de sólo lectura y análisis.** No cambia fisiología,
no cambia restricciones FD-BLD, no aprueba parámetros, no toca `gi_pressure_committed`, no mueve autoridad
(`COMMON_CORE_RUNTIME_AUTHORITY = False`, `family_engine.py` sigue siendo la única autoridad en tiempo de
ejecución). Ningún archivo de `clinical_core/` cambia: el digesto de cierre de la Fase 2
(`22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a`, cabeza `d2cca46`) queda intacto.

La lectura docente que abrió el ciclo fue: «la calibración de presión está condicionada a resolver la capa de
semántica de volumen; el objetivo siguiente **no** es ajustar la presión». Este documento responde a eso.

---

## §1 (P3-69) Qué afirman exactamente FD-BLD-04, FD-BLD-05 y FD-BLD-06

Textos **literales** de `clinical_core/blood_constraints.py` (`DECISIONS` e `IMPLEMENTATION`), sin parafrasear.

| | **FD-BLD-04** | **FD-BLD-05** | **FD-BLD-06** |
|---|---|---|---|
| **Texto de la decisión** | «1 L isotonic crystalloid in these hypovolaemic adults: initial / early effective circulating contribution, as a share of the volume infused (~150-300 mL per litre); a clinical envelope, not an exact conversion; the output response stays state-dependent» | «share of the infused volume still contributing to the circulation; broad envelopes for this reduced model; no exact exponential is forced» | «temporary Hb reduction (g/dL) from crystalloid in these modelled adults, partially reversing as the intravascular effect redistributes; not universal human limits» |
| **Paquete de origen** | P2I-2U (definición), P2I-2V / P2I-2V-R (implementación del filtro) | P2I-2U, P2I-2V-R | P2I-2U, P2I-2V-R |
| **Lectura implementada** | «early contribution = the largest retained intravascular crystalloid (in − out) over minutes 0-30, over the volume infused (1 L)»; V5 lee en cambio «the largest net effect on C over minutes 0-30 (C with the bag − C without it, same bleeding)» | «retained intravascular crystalloid at minutes 30, 60 and 120 from the start of the infusion, over the volume infused (1 L)» | «dilution = Hb without the bag − Hb with it, same bleeding; its peak over minutes 0-120 inside the volume's envelope (1 L and 2 L); partial reversal: 0 < dilution at 120 < peak» |
| **Variables que restringe** | `crystalloid_effective_ml_per_ml` (e), `crystalloid_transient_share` (s), `crystalloid_leak_tau_min` (τ) | las mismas tres | las mismas tres |
| **Unidades** | adimensional (mL retenidos / mL infundidos) | adimensional | g/dL |
| **Marco de referencia** | el **componente de cristaloide del estado sanguíneo compartido** (`BloodState`: `crystalloid_in_ml − crystalloid_out_ml`), en mL reales, **antes** de la conversión `kappa` a la `V` canónica | el mismo | concentración derivada (`Hb` = masa / volumen) del mismo estado |
| **¿Qué magnitud, exactamente?** | **volumen intravascular retenido**, como cociente sobre el **volumen infundido**. **No** es `V` canónica, **no** es equivalente de sangre entera, **no** es volumen plasmático, **no** es salida (`output`) | el mismo | **Hb**, no volumen |
| **Momento** | **máximo** sobre los minutos 0–30 (un transitorio, no un asintótico) | minutos 30, 60 y 120 desde el inicio de la infusión | **máximo** sobre los minutos 0–120, más la reversión parcial al minuto 120 |
| **Contexto de tratamiento** | 1 L isotónico; «the case's GI bleed continues at the candidate's rate; the bag runs over 20 min from minute 0 (P2I-2U); compared with the same run without it» | 1 L, mismo contexto | 1 L **y** 2 L, mismo contexto |
| **Envolvente** | `(0,15, 0,30)` | `{30: (0,15, 0,25), 60: (0,10, 0,20), 120: (0,05, 0,15)}` | `{1000: (0,20, 0,50), 2000: (0,40, 0,80)}` |
| **Papel declarado** | **restricción clínica** («a clinical envelope, not an exact conversion») | **restricción clínica** («broad envelopes for this reduced model») | **restricción clínica** («not universal human limits») |

Distinciones semánticas que **no** se pueden colapsar:

1. **Retenido ≠ infundido.** La envolvente se expresa como cociente; el numerador es volumen retenido y el
   denominador es el litro infundido. Son dos marcos distintos unidos por un cociente, y es ese cociente, no
   ninguno de los dos volúmenes, lo que la docencia acotó.
2. **Transitorio ≠ asintótico.** FD-BLD-04 lee un **máximo** sobre 0–30 min; FD-BLD-05 lee **tres puntos** de la
   curva de decaimiento. Ninguna de las dos lee el valor permanente `e·(1−s)`.
3. **Volumen ≠ Hb.** FD-BLD-06 restringe una **concentración**, no un volumen: `Hb = masa / volumen` no es lineal
   en `e`, mientras las lecturas de 04 y 05 sí lo son (§4). Las tres restricciones comparten parámetros pero no
   comparten magnitud.
4. **`BloodState.volume_ml` ≠ `V` canónica.** `volume_ml` es el **cambio neto firmado** del volumen circulante
   desde la llegada (negativo tras sangrar: el relleno lee `deficit = -blood.volume_ml`); la `V` canónica es
   `kappa · volume_ml + outside_v`, en mL-equivalentes. Las lecturas de 04 y 05 son cocientes de un **componente**
   de `volume_ml`, así que `kappa` se cancela y la envolvente **no** se expresa en mL-equivalentes. El evaluador
   lo declara y se midió: §4, invariancia exacta.

## §2 (P3-69-1) Historia, supersesión y etiqueta por restricción

| Paquete | Qué hizo con esta capa | ¿Cambió la semántica de 04/05/06? |
|---|---|---|
| P2I-2T | Creó el estado sanguíneo compartido y los **valores provisionales canónicos** de `REFERENCE`, entre ellos `crystalloid_effective_ml_per_ml = 0,125`. **Anterior a las restricciones.** | — (todavía no existían) |
| P2I-2U | Definió FD-BLD-04/05/06 con sus envolventes y fijó el perfil de infusión de 20 min | Las creó |
| P2I-2V | Implementó el filtro y corrió la rejilla | No |
| P2I-2V-R | Revisó `U-HB`, volvió `FD-BLD-03` diagnóstica, hizo real V5, cambió la tasa común a primaria | No tocó 04/05/06 |
| P2I-2W | Añadió el campo de estado de borde y la extensión dispersa; `OPEN_EDGES` declara **abierto por arriba** a `crystalloid_effective_ml_per_ml` | No |
| P2I-2Z | Diseño de τ y regla `Finf < F0` (lactato) | No |
| P2I-2X | Revisión adversarial. **Registró en TD-88 que `crystalloid_effective_ml_per_ml` 0,125 no es superviviente** | No |

**Nada superó, reinterpretó ni redefinió FD-BLD-04, 05 ni 06 después de P2I-2U.** Tampoco cambió la retención, ni
el estado sanguíneo, ni el relleno, ni la semántica de `V` de forma que alterara su lectura: el evaluador declara
en `IMPLEMENTATION["blood_reading"]` que «blood quantities do not depend on lambda / kappa, position or rho», y
eso se midió en este ciclo (§4).

| Restricción | Etiqueta |
|---|---|
| FD-BLD-04 | **`CURRENT_AND_APPLICABLE`** |
| FD-BLD-05 | **`CURRENT_AND_APPLICABLE`** |
| FD-BLD-06 | **`CURRENT_AND_APPLICABLE`** |

Lo **obsoleto no es ninguna restricción: es el valor de referencia contra el que se las comparó.**
`blood_anchors.REFERENCE` se autodocumenta como «the canonical **provisional** values (P2I-2T)», y
`EXPLORATION` como «**SYNTHETIC** exploration ranges: **neither candidate bands nor approved values**». El
`0,125` es un valor provisional de P2I-2T, **anterior** a las envolventes de P2I-2U, nunca candidato y nunca
aprobado; TD-88 ya lo tiene registrado como no superviviente desde P2I-2X.

## §3 (P3-69-2) Auditoría del evaluador — sin corregir nada

Revisado: `bc.retained`, `bc.crystalloid`, las tres entradas de `IMPLEMENTATION` y `bc.passes`.

- **El cociente y su denominador son correctos**: el denominador es el litro infundido declarado, no el volumen
  retenido, no `V`.
- **El momento es correcto**: `early` es el máximo sobre 0–30, y `share` lee 30/60/120 desde el inicio de la
  infusión, tal como dice el texto.
- **El perfil de infusión es declarado, no implícito**: «the bag runs over 20 min from minute 0 (P2I-2U)». Por eso
  el máximo retenido vale **0,8307·e** y no `e` (medido, §4): la bolsa entra durante 20 minutos mientras ya fuga.
  **No es un defecto**: es la lectura declarada, y es lo que hace que FD-BLD-04 exija `e ≥ 0,15/0,8307 = 0,181`
  y no `e ≥ 0,15`.
- **Comparadores inclusivos sobre el valor sin redondear**, y «nothing is fitted to a midpoint».
- **No hay conflación de magnitudes**: la docstring del módulo dice «No lactate, no legacy trajectory, no SBP or
  MAP and no direct V or Hb write enters any constraint», y se comprobó leyendo las tres funciones.

**Ningún defecto de implementación encontrado. Nada corregido (no estaba autorizado y no hacía falta).**

---

## §4 (P3-70) Ecuaciones y auditoría de balance de masa

### Cristaloide (`clinical_core/interventions/fluids.py`, congelado)

```
gain = given · e                       # e = crystalloid_effective_ml_per_ml
pool += gain · s                       # s = crystalloid_transient_share
leak  = pool · (1 − exp(−1/τ))         # τ = crystalloid_leak_tau_min, por minuto
pool -= leak
```
`gain` suma a `crystalloid_in_ml`; `leak` suma a `crystalloid_out_ml`.

### Glóbulos rojos (`PackedRedCells`, congelado)

Dos parámetros propios: `volume_ml_per_unit` (300,0) y `unit_hb_g_dl` (20,0). Una unidad suma su volumen a
`transfused_ml` y su masa de Hb al compartimento de masa.

### Sangrado y relleno (`clinical_core/derived.py`, congelado)

```
shed_ml += bleed_ml_per_min             # por minuto
target  = min(plasma_refill_capacity_ml, plasma_refill_target_share · shed_ml)
gap     = target − refill_ml
deficit = −volume_ml
si gap ≤ 0 o deficit ≤ 0:  refill = 0
si no:                     refill = min(gap · −expm1(−1/plasma_refill_tau_min), deficit)
```

### Cierre contable (`clinical_core/integration.py:88-100`, congelado)

```
volume_ml = crystalloid_in_ml − crystalloid_out_ml + transfused_ml + refill_ml − shed_ml
V         = volume_preload_kappa · volume_ml + outside_v
```
La segunda identidad se compara **cada minuto** contra `state.V` dentro de `CONSERVATION_TOLERANCE` y levanta
`CoreInvariantError` si falla. Además `clinical_core/provenance.py:445-470` declara cinco procesos sanguíneos
(`WHOLE_BLOOD_LOSS`, `CRYSTALLOID_IN`, `CRYSTALLOID_OUT`, `RED_CELL_TRANSFUSION`, `PLASMA_REFILL`) con signo y
campo propio, y una guarda **en tiempo de importación** levanta `ProvenanceError` si no se cumple que cada campo
del estado sanguíneo pertenezca exactamente a los procesos que lo cambian.

### Resultados medidos (evaluador y núcleo congelados)

1. **Linealidad exacta en `e`.** Toda la vía del cristaloide es lineal en `given · e`, así que la lectura es
   `retenido(t) = e · φ(t; s, τ)`. Medido con s = 0,6 y τ = 30: `pico/e = 0,830666` y `share30/e = 0,708586`,
   **constantes** para e ∈ {0,16, 0,22, 0,30, 0,34}. La forma `φ` depende de (s, τ); la linealidad en `e`, no.
2. **FD-BLD-06 no es lineal en `e`**, porque `Hb = masa / volumen`. Por eso acota `e` por arriba donde 04 ya no.
3. **El relleno no se puede sumar dos veces con el cristaloide.** Medido sobre la ecuación exacta: con
   `shed = 500` y `C = −400` sin relleno previo da 2,0747 mL/min; con `C = −50` y 200 ya rellenados, 0,4149;
   con `C = +100`, **0,0000**; con 250 ya rellenados, **0,0000**. Es decir: en cuanto el cristaloide levanta
   `volume_ml` a no negativo, `deficit ≤ 0` y **el relleno se apaga**. No hay doble conteo: es exclusión mutua
   por construcción.
4. **Invariancia exacta de la lectura del cristaloide.** Con (e, s, τ) = (0,22, 0,6, 30), las cuatro lecturas
   (pico, 30, 60, 120) son **idénticas en todos los dígitos impresos** al variar `bleed_ml_per_min` (1,5 / 2,5 /
   3,5), `plasma_refill_target_share` (0,25 / 0,5 / 0,75), `plasma_refill_tau_min` (60 / 120 / 240),
   `arrival_circulating_volume_ml` (3000 / 4000 / 5000) y `preload_scale_over_kappa_ml` (600 / 833,33 / 1500).

**Veredicto P3-70: `MASS_BALANCE_COHERENT`.** El cierre no es «a precisión de máquina según mi cálculo»: es un
**invariante del núcleo congelado**, comprobado cada minuto de cada ejecución, con una guarda de procedencia que
además impide que un campo cambie sin su proceso. No hay residuos que explicar.

---

## §5 (P3-71) Descomposición del fallo, una restricción a la vez

Barrido de un parámetro a la vez, los demás en `REFERENCE`, exigiendo la restricción en **los dos** casos GI:

| Parámetro variado | Valores | ¿Alguno hace pasar 04/05/06? |
|---|---|---|
| `crystalloid_effective_ml_per_ml` | 0,10 · 0,125 · 0,15 · 0,18 · 0,22 · 0,26 · 0,30 · 0,40 | **Sí**: 06 desde 0,18; las tres desde 0,22; **ninguna** en 0,40 |
| `crystalloid_transient_share` | 0,0 … 1,0 (6 valores) | No, ninguno |
| `crystalloid_leak_tau_min` | 10 … 120 (6 valores) | No, ninguno |
| `plasma_refill_target_share` | 0,2 … 0,8 (5 valores) | No, ninguno |
| `plasma_refill_tau_min` | 30 … 240 (4 valores) | No, ninguno |
| `bleed_ml_per_min` | 1,5 … 3,5 (5 valores) | No, ninguno |
| `red_cell_unit_volume_ml` | 200 … 400 (5 valores) | No, ninguno |

Lectura: **`e` es el único parámetro que, por sí solo, mueve el veredicto**, y lo mueve en las dos direcciones
(demasiado bajo falla por debajo de la envolvente; 0,40 falla por encima). `s` y τ **sí** importan, pero sólo
**junto a** `e` (§7): a `e` fijo redistribuyen la curva sin alcanzar la envolvente.

| Restricción | Etiqueta |
|---|---|
| FD-BLD-04 | **`CAN_PASS_WITHIN_DECLARED_REGION`** |
| FD-BLD-05 | **`CAN_PASS_WITHIN_DECLARED_REGION`** |
| FD-BLD-06 | **`CAN_PASS_WITHIN_DECLARED_REGION`** |

La región declarada es `blood_extension.DOMAIN`: `crystalloid_effective_ml_per_ml ∈ (0,0, 1,0)`, «a share of the
volume infused», con el borde superior **abierto** en `OPEN_EDGES`. La rejilla sintética de exploración de
`blood_anchors.EXPLORATION` ya incluía `(0,125, 0,2, 0,3)`, así que los valores que satisfacen las envolventes
estaban dentro de lo explorado. **Ninguna región se amplió ni se inventó para este resultado.**

En el punto de `REFERENCE` el fallo es, en cambio, necesario: el pico vale 0,8307 · 0,125 = **0,1038**, por debajo
del 0,15 de FD-BLD-04 **por construcción**, y las lecturas de 30/60/120 valen 0,0886 / 0,0642 / 0,0519, con sólo
la de 120 dentro de su banda. Es `ALWAYS_FAILS` **en ese punto**, no en el modelo.

---

## §6 (P3-72) Identificabilidad conjunta sangrado–volumen–presión

### Grafo causal (sólo las aristas que el núcleo congelado tiene)

```
bleed_ml_per_min ──► shed_ml ──┬──► volume_ml ──► V ──► preload_position ──► pressure_rel ──► SBP/DBP/MAP
                               └──► refill (apagado si volume_ml ≥ 0)
e, s, τ ──► crystalloid_in/out ──► volume_ml   (y, vía masa/volumen, ──► Hb)
unidad GR (300 mL, 20 g/dL) ──► transfused_ml ──► volume_ml ; masa Hb ──► Hb
kappa, scale (ν = kappa/scale), f ──► sólo el tramo V ──► pressure_rel
```

### Composiciones identificables

| Bloque | Composición identificable | La leen |
|---|---|---|
| Volumen (cristaloide) | la **trayectoria de fracción retenida** `R(t) = e · φ(t; s, τ)` en sus cuatro lecturas | FD-BLD-04, 05, 06 |
| Presión | `ν = kappa / scale` (**no** `kappa` y `scale` por separado) y `m = (1−f)·ν/f` cerca de la llegada; `1/f` como meseta | `U-OUT`, FD-BLD-02 |
| Glóbulos | volumen por unidad × Hb por unidad, vía el salto de Hb | FD-BLD-02, `SECOND-UNIT` |

### Rango / Jacobiano, con restricciones independientes solamente

El bloque de volumen aporta **cuatro** lecturas independientes (pico, 30, 60, 120) sobre **tres** incógnitas
(e, s, τ): el Jacobiano tiene rango 3, es decir, **el bloque es estructuralmente identificable**. Lo que impide
un punto no es el rango: son las **envolventes anchas**. Cuatro desigualdades de banda sobre tres incógnitas dejan
una región de dimensión 3, no un punto (§7). Esa es la distinción que importa: **no es no-identificabilidad
estructural, es ancho de envolvente.**

### Acoplamiento de la tasa de sangrado

**Medido: nulo sobre 04/05/06.** La razón es semántica, no numérica: la lectura implementada compara «con la bolsa
contra sin la bolsa, **al mismo sangrado**», así que la tasa se cancela exactamente, y la lectura del componente
(in − out) no la contiene siquiera. Las cuatro lecturas salieron idénticas en todos los dígitos a 1,5 / 2,5 / 3,5
mL/min (§4.4). La tasa **sí** acopla con la presión, por `U-OUT`: ahí es una coordenada del candidato y no un dato
conocido, y eso quedó medido en P3-68 (el punto comprometido satisface `U-OUT` a una sola tasa, 2,75 mL/min).

**Veredicto P3-72: `SEPARABLE_CALIBRATION`.** El bloque de volumen se calibra **sin** las coordenadas de presión:
sus lecturas son invariantes a `preload_scale_over_kappa_ml`, a la posición de precarga, al volumen de llegada, al
relleno y a la tasa de sangrado. La estructura es **triangular**: volumen → presión, nunca al revés.

**Consecuencia que conviene decir aunque incomode:** resolver la semántica de volumen **es** necesario para la
coherencia del modelo, pero **no aporta información sobre (ν, f)**. La presión GI sigue exactamente donde la dejó
P3-68. El orden que fijó la docencia es correcto; el segundo paso no se desbloquea con el primero.

---

## §7 (P3-73) Región factible conjunta

### Región del bloque de volumen, con el evaluador congelado

200 puntos (e × s × τ = 10 × 4 × 5), los demás parámetros en `REFERENCE`, exigiendo las tres restricciones en
**los dos** casos GI, variante `primary`:

| `e` | FD-BLD-04 | FD-BLD-05 | FD-BLD-06 | las tres | (s, τ) admisibles (muestra) |
|---|---|---|---|---|---|
| 0,16 | 7/20 | 4/20 | 16/20 | **4** | (0,2; 60) (0,2; 90) (0,2; 120) (0,4; 120) |
| 0,18 | 16/20 | 10/20 | 19/20 | **10** | (0,2; 20) (0,2; 30) (0,4; 60) (0,4; 120) |
| 0,20 | 19/20 | 9/20 | 20/20 | **9** | (0,4; 30) (0,6; 60) (0,6; 120) |
| 0,22 | 20/20 | 10/20 | 20/20 | **10** | (0,4; 20) (0,6; 30) (0,6; 90) |
| 0,24 | 20/20 | 8/20 | 20/20 | **8** | (0,4; 20) (0,6; 60) (0,8; 60) |
| 0,26 | 20/20 | 7/20 | 20/20 | **7** | (0,6; 20) (0,6; 90) (0,8; 90) |
| 0,28 | 20/20 | 5/20 | 16/20 | **5** | (0,6; 20) (0,8; 60) (0,8; 90) |
| 0,30 | 20/20 | 5/20 | 7/20 | **4** | (0,6; 20) (0,8; 30) (0,8; 60) |
| 0,32 | 13/20 | 4/20 | 4/20 | **3** | (0,6; 20) (0,6; 30) (0,8; 30) |
| 0,34 | 6/20 | 3/20 | 3/20 | **2** | (0,6; 20) (0,8; 30) |
| **total** | **161/200** | **65/200** | **145/200** | **62/200** | |

**Clasificación: `NONEMPTY_FEASIBLE_REGION`.** 62 de 200 puntos satisfacen las tres en los dos casos. No hay
contradicción.

Matiz obligado: en las coordenadas crudas (e, s, τ) la región es una **cresta**, no un punto —`e` admisible cubre
todo [0,16; 0,34], un factor 2, con (s, τ) compensatorios— así que vale también
**`POORLY_IDENTIFIED_MANIFOLD`** si la pregunta es «¿queda un valor de `e`?». Lo que las envolventes identifican
es la **trayectoria** `R(t)`, no los tres parámetros por separado.

### Región conjunta con las doce restricciones

Cruzando la región del cristaloide con la cresta de `U-OUT` de P3-68 (48 combinaciones evaluadas), **8 puntos
satisfacen las doce restricciones en los dos casos**, todos en (tasa 3,0; escala/kappa 1100; f 0,45), por ejemplo:

```
tasa 3,0 · escala/kappa 1100 · f 0,45 · e 0,22 · s 0,4 · τ 60
```

Ese punto se verificó además en **las diez lecturas** (`primary` y las nueve variantes declaradas) y en los dos
casos: **ninguna restricción falla en ninguna de las veinte evaluaciones**.
**Esto es una demostración de consistencia, no una recomendación de parámetros y no una aprobación.**

### Dónde está el punto de desarrollo actual

**`OUTSIDE`.** `REFERENCE` (e = 0,125; s = 0,6; τ = 30) falla FD-BLD-04, 05 y 06 en los dos casos y en **las diez
lecturas**. Y lo hace necesariamente: 0,8307 · 0,125 = 0,1038 < 0,15.

### Contribución por restricción

| Restricción | Qué dimensión acota | Fuerza | ¿Redundante o contradictoria? |
|---|---|---|---|
| FD-BLD-04 | `e` por abajo (`e ≥ 0,181`) y por arriba (`e ≤ 0,361`) vía el pico | Débil en el medio (161/200): es la más laxa | Implicada en parte por FD-BLD-05@30; no contradictoria |
| FD-BLD-05 | la **forma** de la curva: `e` junto con (s, τ) en tres tiempos | **La que liga** (65/200) | Ninguna otra la implica; es la que fija la cresta |
| FD-BLD-06 | `e` por arriba por dilución de Hb, y exige reversión parcial (0 < dilución(120) < pico) | Fuerte sólo en los extremos (145/200) | **Información genuinamente nueva**: es la única en una magnitud no lineal en `e` (Hb, no volumen) |
| `U-OUT` | tasa de sangrado × (ν, f), curso **sin tratar** | Fuerte (una sola tasa en P3-68) | Ortogonal al bloque de volumen: no lo toca |
| FD-BLD-02 / `SECOND-UNIT` | la vía de glóbulos con (ν, f) | — | Ortogonal al cristaloide |

---

## §8 (P3-74) Revisión adversarial

| Ataque | Veredicto | Por qué |
|---|---|---|
| Reconstrucción semántica de FD-BLD | **`ROBUST`** | Textos citados literalmente de `DECISIONS` e `IMPLEMENTATION`; no se parafraseó ninguna distinción |
| Desajuste oculto de unidades | **`ROBUST`** (no hay) | Numerador y denominador son ambos mL del mismo marco; el cociente es adimensional y `kappa` se cancela. Medido: invariancia exacta a `preload_scale_over_kappa_ml` |
| Confusión transitorio / estado estacionario | **`ROBUST`** (no la hay) | FD-BLD-04 lee un **máximo** 0–30 y FD-BLD-05 tres puntos; ninguna lee `e·(1−s)`. El factor 0,8307 es el perfil de infusión de 20 min **declarado** por el propio evaluador. **Mi propio tamiz analítico previo sí erró aquí**: usó un bolo instantáneo y habría admitido `e = 0,15`; el evaluador congelado lo corrigió. La autoridad es el evaluador |
| Doble conteo de relleno y fuga de cristaloide | **`ROBUST`** (no lo hay) | Medido sobre la ecuación exacta: en cuanto el cristaloide lleva `volume_ml` a no negativo, `deficit ≤ 0` y el relleno da **0,0000**. Exclusión mutua por construcción |
| Conflación de volumen sanguíneo y masa de Hb | **`ROBUST`** (no la hay) | Procesos separados con campo propio y guarda de procedencia en tiempo de importación. Y se usa como **información**: 04/05 son lineales en `e`, 06 no |
| Tratar equivalentes de sangre entera como mL reales | **`ROBUST`** (no se hace) | Las envolventes viven en el marco de `BloodState` en mL reales, **antes** de `kappa`; al ser cocientes, son invariantes a él. Medido |
| Tratar el volumen efectivo como observable | **`WEAK` — y sigue en pie de P3-68** | El volumen efectivo **no** es observable. Lo que las envolventes acotan es un **cociente** cuyo denominador sí lo es. No resuelve el problema de P3-68C, lo circunscribe al bloque de presión |
| Pseudo-identificabilidad desde trayectorias generadas por el modelo | **`WEAK`** | Los 200 puntos son **evaluaciones del modelo**, no observaciones. No cuento ninguna como evidencia clínica independiente: prueban **consistencia** con envolventes docentes, nada más. La evidencia sigue siendo dos pacientes redactados |
| Usar la escala derivada del legado como evidencia de calibración | **`ROBUST`** (no se usa) | El bloque de volumen es invariante a `preload_scale_over_kappa_ml` (medido), así que la procedencia legado de ese canónico (TD-130 (23)) **no entra** aquí. Sigue contaminando el bloque de presión, no este |
| Suponer conocida la tasa de sangrado cuando es candidata | **`ROBUST`** | Medido: nulo acoplamiento con 04/05/06, porque la lectura compara al mismo sangrado. En el bloque de presión **sí** es candidata y así se reporta |
| Usar dos veces la misma restricción docente por variables derivadas | **`WEAK`** | FD-BLD-04 está parcialmente implicada por FD-BLD-05@30 (ambas leen la misma curva), así que «tres restricciones» son más bien **dos independientes más una** (06, en otra magnitud). Lo digo en la tabla de contribución en vez de contar tres |
| Concluir «contradicción del modelo» desde una restricción obsoleta | **`ROBUST` — y es exactamente el error que este ciclo corrige** | Ninguna restricción está obsoleta; el **valor de referencia** sí es provisional y anterior a ellas. Concluir contradicción habría sido el error, y es el que P3-68 cometió en su redacción (§10) |

### Un ataque trece, que no estaba en la lista y es mío

**Anclaje en mi propia hipótesis previa.** Antes de medir nada, al estimar el ciclo, escribí la bifurcación:
«si existe un punto de la rejilla de candidatos que satisfaga FD-BLD-04/05/06 a la vez, el "fallo" es de
**región de parámetros** —el punto de referencia nunca fue un superviviente—». Es exactamente la conclusión a la
que llegué. Quien lea esto debe saber que **la hipótesis precedió a los datos**, porque eso es precisamente la
condición en la que un análisis confirma lo que ya creía.

Lo que sostiene la conclusión **a pesar** de ese orden, y no por él:

- las etiquetas no las puse yo: las leí literalmente de `DECISIONS` e `IMPLEMENTATION`;
- el veredicto de cada punto lo emite el **evaluador congelado**, en las **diez** lecturas declaradas, no un
  criterio mío;
- mi propio tamiz analítico previo **se equivocó** en la dirección contraria a mi hipótesis (admitía `e = 0,15`;
  el evaluador lo rechazó por el perfil de infusión de 20 min), y lo reporto en la tabla de arriba;
- la invariancia que sostiene la separabilidad es **idéntica en todos los dígitos**, no una tolerancia elegida;
- y el resultado incluye algo que **contradice** la expectativa con que se abrió el ciclo: resolver el volumen
  **no** desbloquea la presión (§6).

Clasificación de este ataque: **`WEAK`** — real como sesgo de procedimiento, no sostenido por la evidencia
disponible. Si docencia quiere una verificación independiente de esta conclusión, la prueba más corta es volver
a correr la rejilla de 200 puntos y comprobar los 62 supervivientes contra el evaluador congelado:
`test_blood_volume_semantics.py` fija el testigo y el punto de referencia, y la rejilla completa está en §7.

**Conclusiones que quedan en pie:** el balance de masa; la separabilidad; la no vacuidad de la región; la
etiqueta `CURRENT_AND_APPLICABLE` de las tres restricciones; que el punto actual está fuera.
**Debilitadas y así reportadas:** la independencia entre FD-BLD-04 y FD-BLD-05; que las 200 evaluaciones no son
observaciones; que el volumen efectivo sigue sin ser observable.
**Ninguna conclusión `UNSUPPORTED` ni `CIRCULAR`.**

---

## §9 (P3-75) Pack de decisión docente

1. **¿Qué significa físicamente la coordenada de volumen hoy?** `BloodState.volume_ml` es el **cambio neto
   firmado del volumen circulante desde la llegada**, en mL, con cinco procesos de signo declarado. La `V`
   canónica es `kappa · volume_ml + outside_v`, en mL-equivalentes. No son la misma magnitud y el código no las
   confunde.
2. **¿Qué significan FD-BLD-04/05/06?** Tres envolventes clínicas sobre la **fracción del litro infundido que
   queda en la circulación**: su máximo en 0–30 min (04), su valor a 30/60/120 min (05), y la caída temporal de
   Hb que produce, con reversión parcial (06). §1 lo detalla sin parafrasear.
3. **¿Están violadas hoy?** **Sí, en el punto de referencia del repositorio**, en los dos casos y en las diez
   lecturas. **No** como propiedad del modelo.
4. **La violación es:** **`parameter-region`**. No es semántica (los marcos coinciden y el evaluador es fiel a su
   texto), no es de implementación (ningún defecto; el balance cierra como invariante del núcleo), y no es
   contradicción causal verdadera (62 de 200 puntos las satisfacen, y 8 satisfacen las doce). Es que
   `crystalloid_effective_ml_per_ml = 0,125` es un **valor provisional de P2I-2T, anterior a las envolventes de
   P2I-2U**, nunca candidato y nunca aprobado, ya registrado como no superviviente en TD-88.
5. **¿Qué parámetros de la vía de volumen importan?** Tres, y sólo tres: `e`, `s`, τ. Los cinco restantes del
   bloque sanguíneo (relleno ×3, unidad de glóbulos ×2) **no** mueven 04/05/06. Medido.
6. **¿Qué combinaciones son identificables?** La **trayectoria** `R(t) = e · φ(t; s, τ)`. Estructuralmente el
   rango es 3 (cuatro lecturas, tres incógnitas); el ancho de las envolventes deja una cresta, no un punto.
7. **¿Cómo se acopla la tasa de sangrado con la calibración de presión?** Con el **volumen**, de ninguna manera
   (la lectura compara al mismo sangrado: medido, idéntico en todos los dígitos). Con la **presión**, de forma
   fuerte y como coordenada **candidata**: `U-OUT` la liga a (ν, f), y el punto comprometido la satisface a una
   sola tasa (2,75 mL/min, P3-68).
8. **¿Existe región factible conjunta?** **Sí.** 62/200 en el bloque de volumen; 8 puntos con las doce
   restricciones en los dos casos y en las diez lecturas.
9. **¿Dónde está el punto de desarrollo actual?** **Fuera**, necesariamente: 0,8307 · 0,125 = 0,1038 < 0,15.
10. **¿Qué restricciones aportan información genuina?** FD-BLD-05 (la que liga la forma de la curva); FD-BLD-06
    (única en una magnitud no lineal en `e`); `U-OUT` (ortogonal, sobre el curso sin tratar); FD-BLD-02 /
    `SECOND-UNIT` (vía de glóbulos).
11. **¿Cuáles son redundantes o circulares?** FD-BLD-04 está **parcialmente implicada** por FD-BLD-05@30: añade
    sólo el momento del máximo. Ninguna es circular. Advertencia que sí aplica al bloque de presión y no a este:
    la procedencia legado del canónico de `preload_curve_scale_ml` (TD-130 (23)).
12. **¿Qué decisiones docentes hacen falta ahora?** Cuatro, y ninguna es «¿cuánto vale `e`?»:
    - **V-1.** ¿Se acepta que `blood_anchors.REFERENCE` dejó de ser el punto de desarrollo del bloque de
      cristaloide, y que su `0,125` queda rotulado explícitamente como **provisional pre-P2I-2U, no superviviente**
      (hoy sólo está dicho en TD-88)?
    - **V-2.** De la cresta admisible, ¿qué **comportamiento clínico** se prefiere? La pregunta interpretable es:
      «de 1 L isotónico en estos adultos, ¿cuánto queda a los 30 min y cuánto a las 2 h?», y de ahí sale (e, s, τ).
      **No** preguntamos «¿cuánto vale `transient_share`?».
    - **V-3.** ¿Hace falta una cuarta observación para colapsar la cresta a un punto, o se acepta trabajar sobre
      la cresta? Si hace falta, la de mayor información es la **dilución de Hb a 2 L** (FD-BLD-06 ya la tiene como
      envolvente, y es la única magnitud no lineal en `e`).
    - **V-4.** ¿Se confirma el orden? Medido: el bloque de volumen es **separable** y resolverlo **no** aporta
      información sobre (ν, f). La presión seguirá necesitando las cuatro decisiones de FD-P3-68.

### Veredicto P3-75

**`A · CURRENT_VOLUME_MODEL_CAN_BE_RECALIBRATED_WITH_EXISTING_CONSTRAINTS`**

Las envolventes docentes vigentes definen una región no vacía dentro del dominio declarado, sin necesidad de
evidencia clínica nueva, sin tocar fisiología y sin reinterpretar ninguna restricción. Lo que falta no es
información: es la **decisión docente** de elegir dentro de la región (V-1 a V-4) y la autorización para mover un
parámetro, que este ciclo **no** tiene y **no** se arroga.

---

## §10 Diseño de P3-76 — **no ejecutado**

Obligatorio por el «IF A» del encargo. **Diseño, no ejecución; no hay autorización para correrlo.**

**P3-76 — PAQUETE CONJUNTO DE CALIBRACIÓN SANGRE / VOLUMEN / PRESIÓN**

- **Puerta de entrada.** V-1 y V-2 respondidas por docencia. Sin V-2 el paquete no arranca: elegir dentro de la
  cresta sin decisión docente sería aprobar un parámetro.
- **P3-76-1** (sólo lectura). Traducir la respuesta a V-2 (dos porcentajes con su hora) al triple (e, s, τ) con la
  transformada inversa exacta, igual que se hizo para la presión en P3-68, y dar la **banda** compatible, no un
  punto.
- **P3-76-2** (computacional). Barrido fino **sólo dentro** de la banda de V-2 cruzado con la cresta de `U-OUT`,
  con las doce restricciones, los dos casos y las diez lecturas. Sin Cartesiano ciego.
- **P3-76-3** (sólo lectura). Verificar que el bloque de glóbulos y el de relleno siguen invariantes (son hoy, y
  deben seguir siendo, ortogonales al cristaloide).
- **P3-76-4** (sólo lectura). Decidir si la cresta residual de presión se estrecha al fijar el volumen.
  **Predicción medida de este ciclo: no se estrecha.** El paquete debe poder reportar ese «no».
- **P3-76-5.** Pack de aprobación de instantánea, con el estado de evidencia por magnitud, para que docencia
  apruebe o rechace. **Ningún parámetro cambia en el repositorio dentro de P3-76.**
- **Fuera de alcance explícito:** autoridad en tiempo de ejecución, lo que ve el residente, fisiología nueva,
  `clinical_physiology`, y cualquier escritura en `clinical_core/`.

---

## §11 Corrección de la redacción de P3-68

P3-68 escribió, y el Decision File (FD-P3-65) y TD-130 (26) repitieron:

> «el filtro congelado **rechaza** FD-BLD-04, 05 y 06 en los dos casos y en las nueve variantes, en **63 de 63**
> puntos del barrido […] el mapa de volumen infundido a efectivo está hoy **fuera de las envolventes que la
> docencia aprobó para él**».

**Dos defectos, y el segundo es material:**

1. Los 63 puntos de ese barrido variaban la tasa de sangrado y las coordenadas de presión, y **mantenían los tres
   parámetros del cristaloide en `REFERENCE`**. Son **un** punto del bloque de volumen repetido 63 veces, no 63
   refutaciones independientes. Las lecturas de 04/05/06 son invariantes a todo lo que ese barrido movía (§4.4):
   el «63 de 63» no podía ser otra cosa.
2. «El mapa está fuera de las envolventes» se lee como propiedad **del modelo**. Es falso: 62 de 200 puntos del
   bloque las satisfacen en los dos casos, y 8 satisfacen las doce en las diez lecturas. Lo que está fuera es el
   **valor de referencia provisional** (`e = 0,125`, pre-P2I-2U, ya registrado como no superviviente en TD-88).

La redacción correcta es: **el punto de referencia del repositorio está fuera de las envolventes; el modelo no.**
Corregido aquí, en FD-P3-65 y en TD-130 (26); FD-P3-69 a FD-P3-75 lo registran.
