# Fase 3 — Cierre analítico de la región de volumen sanguíneo (P3-76 … P3-80)

Rama `phase-3-runtime-integration`, desde `f5ae4fb`. **Sólo lectura y análisis.** No cambia fisiología, no
cambia restricciones FD-BLD, no aprueba ningún parámetro, no toca `gi_pressure_committed`, no mueve autoridad
(`COMMON_CORE_RUNTIME_AUTHORITY = False`). Ningún archivo de `clinical_core/` cambia: el digesto de cierre de la
Fase 2 (`22b90a6f…ce6a`) queda intacto.

Entra con las cuatro decisiones docentes del ciclo anterior: **V-1 aceptada** (el `0,125` es
`PROVISIONAL_PRE_P2I_2U` / `NON_SURVIVING_REFERENCE`), **V-2 aceptada en forma de comportamiento** (sin valor
numérico todavía), **V-3 diferida** (caracterizar primero la región completa), **V-4 aceptada** (volumen
primero, presión después, sin afirmar que lo uno identifique lo otro).

Herramienta nueva: `blood_volume_region.py`, fuera de `clinical_core` y del registro de autoridad, sin importar
ninguno de los dos, sin envolventes por omisión. Pruebas: `test_blood_volume_region.py` (14).

---

## §1 (P3-76-1) El conjunto exacto de parámetros, medido

| Restricción | Parámetros que **realmente** entran | Comprobación |
|---|---|---|
| **FD-BLD-04** | `e`, `s`, `τ` — **y nada más** | Las cuatro lecturas son idénticas **en todos los dígitos** al variar sangrado (1,5 / 2,5 / 3,5), objetivo y τ del relleno, capacidad del relleno, volumen de llegada (3000 / 4000 / 5000), unidad de glóbulos y escala de precarga |
| **FD-BLD-05** | `e`, `s`, `τ` — **y nada más** | La misma medida |
| **FD-BLD-06** | `e`, `s`, `τ`, **`arrival_circulating_volume_ml`** (fuerte), y **débilmente** `bleed_ml_per_min`, `plasma_refill_target_share`, `plasma_refill_tau_min`, `plasma_refill_capacity_ml` | Pico de dilución a 1 L: **0,4301** (llegada 3000) · 0,3273 (4000) · **0,2642** (5000) — un factor 1,63. Sangrado 1,5→3,5: 0,3278→0,3268 (0,3 %). Relleno 0,25→0,75: pico 1 %, valor a 120 min 11 %. Unidad de glóbulos y escala de precarga: **cero**, idénticos en todos los dígitos |

**El conjunto mínimo no son tres parámetros.** FD-BLD-04 y FD-BLD-05 sí leen exactamente (e, s, τ); FD-BLD-06
no, porque `Hb = masa / volumen` y el volumen de base lo fija el caso. A llegada 3000 el pico a 2 L vale
**0,8114**, por encima del techo 0,80 de su envolvente: por eso FD-BLD-06 falla ahí. **Esto corrige una frase
mía del ciclo anterior** (§10).

Dos parámetros del bloque **no tienen dominio declarado**: `crystalloid_transient_share` y
`crystalloid_leak_tau_min` no están en `blood_extension.DOMAIN`. Sus únicos límites son estructurales (`s` es
una fracción, `τ > 0`). Es la misma clase de hueco que TD-130 (24) registró para `volume_preload_kappa`, y
queda declarado como TD-130 (28).

## §2 (P3-76-2) Forma cerrada, exacta

Con λ = exp(−1/τ) y la bolsa entrando en **20 min desde el minuto 0** (semántica declarada por
`IMPLEMENTATION["crystalloid"]`, P2I-2U):

```
C(τ)  =  λ·(1 − λ²⁰) / (20·(1 − λ))                      ∈ (0, 1), creciente en τ
R(t)  =  retenido(t) / infundido  =  e · [ (1 − s) + s·C(τ)·λ^(t−20) ]      para t ≥ 20
Rpico =  R(20)  =  e · [ (1 − s) + s·C(τ) ]
```

Derivación: todo lo que entra al compartimento transitorio o fuga o sigue allí, así que
`Σfuga = s·Σganancia − reserva`, y por tanto `retenido = (1−s)·Σganancia + reserva`, con la reserva en
progresión geométrica de razón λ. De ahí el cierre.

**Verificado contra el evaluador congelado en seis puntos (e, s, τ) × cuatro lecturas: error máximo
1,110·10⁻¹⁶.** Es precisión de máquina, no aproximación. Consecuencias inmediatas:

- **R(t) es exactamente lineal en `e`.** Toda la vía del cristaloide lo es.
- **El pico no vale `e`, vale `C`-corregido**: con s = 0,6 y τ = 30, `Rpico/e = 0,830666`. Por eso FD-BLD-04
  exige `e ≥ 0,15/0,830666 = 0,181` **con esos (s, τ)**, y `e > 0,15` **con cualesquiera** (§4).
- `C(τ) ∈ (0,1)` creciente: comprobado monótono en τ = 1 … 6000 min.

## §3 (P3-76-3) Las tres superficies de restricción

Sea `a_k(s,τ)` el coeficiente de la lectura `k`, de modo que la lectura vale `e·a_k`.

| Restricción | Desigualdad explícita | Frontera |
|---|---|---|
| **FD-BLD-04** | `0,15 ≤ e·a_pico(s,τ) ≤ 0,30` | **analítica** |
| **FD-BLD-05** | `0,15 ≤ e·a₃₀ ≤ 0,25` · `0,10 ≤ e·a₆₀ ≤ 0,20` · `0,05 ≤ e·a₁₂₀ ≤ 0,15` | **analítica** |
| **FD-BLD-06** | `dil₁L(e,s,τ,caso) ∈ (0,20; 0,50)` y `dil₂L ∈ (0,40; 0,80)`, más `0 < dil(120) < pico` | **requiere evaluación numérica** |

Las cinco desigualdades analíticas colapsan, para cada (s, τ), a **un intervalo cerrado exacto en `e`**:

```
e ∈ [ máx_k (inferior_k / a_k) ,  mín( mín_k (superior_k / a_k), e_max ) ]
```

con `e_max = 1,0`, el borde del dominio declarado `blood_extension.DOMAIN`. Si el máximo supera al mínimo, el
intervalo es vacío. Eso es **eliminación analítica completa de una de las tres dimensiones**, sin una sola
llamada al evaluador.

**Por qué FD-BLD-06 no es analítica, con mecanismo medido:** la dilución vale
`Hb₀(t)·ΔV/(V₀(t)+ΔV)`, y `ΔV = 1000·R(t)` sí es analítico, pero `V₀` y `Hb₀` no, **porque el cristaloide apaga
el relleno de plasma** en un umbral que depende de (e, s, τ) — el mecanismo que P3-70 documentó. Prueba: con el
relleno prácticamente apagado (`plasma_refill_target_share = 10⁻⁹`, punto **interior** del dominio declarado
(0,1), sonda diagnóstica y nunca candidato), esa forma ajusta a **2,6·10⁻⁶ y 5,0·10⁻⁶**, y el ajuste devuelve
`H = 6,78 g/dL` y `V = 4074 mL`, que son la Hb y el volumen de llegada reales del caso. Con el relleno normal el
error del mismo ajuste es **1,6·10⁻³ y 9,2·10⁻²**. La no-analiticidad es **entera** del apagado del relleno.

**Pero FD-BLD-06 se reduce a una sola cota, y es analítica en espacio de comportamiento** (§6): a `Rpico`
constante, el pico de dilución a 1 L y a 2 L varía **0,01 %** mientras `R120` varía **68 %**. Es decir, el pico
de dilución es **función de `Rpico` solo**. Resolviendo por bisección contra el evaluador congelado:

| Caso | 1 L → `Rpico` | 2 L → `Rpico` | FD-BLD-06 conjunta | Liga |
|---|---|---|---|---|
| `gi_bleed_57m` | [0,12429; 0,32275] | [0,12724; **0,27072**] | `Rpico ≤ 0,27072` | **2 L**, arriba |
| `gi_bleed_72f` | [0,13021; 0,33907] | [0,13356; **0,28518**] | `Rpico ≤ 0,28518` | **2 L**, arriba |

Al exigirse en los dos casos, **FD-BLD-06 aporta exactamente una cosa: `Rpico ≤ 0,27072`**, que recorta un
**19,5 %** de la caja de FD-BLD-04. Su cota inferior queda subsumida por FD-BLD-04 (0,15 > 0,1272).

## §4 (P3-76-4) La región factible

Barrido analítico de 238 601 pares (s, τ) — `s ∈ (0,01; 0,995)`, `τ ∈ [1; 600]` cada 0,5 min — con el intervalo
exacto de `e` en cada uno. **Ni una llamada al evaluador.**

- **Extensión.** 236 360 de 238 601 pares (s, τ) admiten algún `e`. `e ∈ [0,150025; 1,000000]`.
- **`e` está acotado lejos del `0,125`, analíticamente.** Como `a_pico = (1−s) + s·C < 1` para todo (s, τ), la
  cota inferior `0,15/a_pico` es **siempre > 0,15**. El mínimo global medido es **0,150025 = 1,2002 × 0,125**:
  el valor provisional de referencia queda **16,7 % por debajo del menor `e` admisible**, y no por poco margen
  numérico sino por una desigualdad estricta.
- **Qué liga cada borde** (sobre los pares admisibles):

  | Borde | FD-BLD-05@30 | FD-BLD-05@60 | FD-BLD-05@120 | FD-BLD-04 (pico) | Dominio `e<1` |
  |---|---|---|---|---|---|
  | inferior | **232 457 (98,3 %)** | 2 507 | 1 396 | **0** | — |
  | superior | 9 557 | 7 003 | **216 787 (91,7 %)** | 3 010 (1,3 %) | 3 |

  La cota **inferior** de FD-BLD-04 **nunca** liga. Su cota superior liga en 1,3 %.
- **Redundancia por subregiones.** FD-BLD-05@60 es casi inerte: estrechar su envolvente al 50 % reduce la
  región **0,3 %** (las otras, 60–70 %: §7). FD-BLD-06 es redundante salvo en el borde superior de `Rpico`.
- **Ramas desconectadas: sí, y acotadas.** Para `s` entre ≈0,825 y ≈0,865 hay un **hueco real en τ**, acotado
  por bisección a 10⁻¹²:

  | s | hueco en τ (min) | anchura |
  |---|---|---|
  | 0,825 | (13,333232; 14,549602) | 1,22 |
  | 0,840 | (9,635384; 19,081944) | 9,45 |
  | 0,850 | (8,512891; 20,755089) | 12,24 |
  | 0,860 | (7,622438; 22,191381) | 14,57 |
  | 0,865 | (4,535445; 22,854507) | 18,32 |

  **Mecanismo**, en s = 0,85 y τ = 15: `FD-BLD-05@60` exige `e ≥ 0,5508` y `FD-BLD-04` permite `e ≤ 0,4967`.
  Así que **la cota superior de FD-BLD-04 sí hace trabajo real: es lo que desconecta la región.** (Una
  hipótesis alternativa mía —que el hueco venía del cociente `a₃₀/a₁₂₀`— quedó refutada en la misma medida:
  ese cociente está dentro de lo permitido en todo el hueco.)
- Para `s ≳ 0,9` lo que aparece **no** es un hueco sino un **suelo** en τ (31 min a s = 0,9; 46 a 0,95; 55 a
  0,995), con todo lo de arriba admisible. Suelo y hueco son cosas distintas y la prueba R6 las separa.
- **Conexión.** Fuera de la banda `s ∈ (0,825; 0,865)` la región es conexa en τ para cada `s`: 190 de 199
  valores de `s` sin hueco.

## §5 (P3-76-5) La rejilla de 62/200, como testigo

La región **no** se define por la rejilla. Usada sólo como testigo de validación: para los 200 puntos del ciclo
anterior, la predicción analítica (intervalo exacto de 04+05, más `Rpico ≤ 0,27072` por FD-BLD-06) se comparó
con el veredicto del evaluador congelado.

**200 de 200 coinciden. 62 supervivientes predichos, 62 medidos. Cero discrepancias.**

Y la región **explica** los 62: son los puntos de esa rejilla cuyo `e` cae en el intervalo cerrado de su (s, τ)
y cuyo `Rpico` no pasa de 0,27072. Nada más los seleccionaba.

---

## §6 (P3-77) Coordenadas de comportamiento

### §6.1 La transformada, y que es uno a uno

Con `p = e(1−s)` (fracción permanente), `q = e·s·C(τ)` (transitoria al final de la infusión) y λ:

```
Rpico = p + q        R30 = p + q·λ¹⁰        R120 = p + q·λ¹⁰⁰
```

La inversa es cerrada: `(Rpico−R30)/(Rpico−R120) = (1−λ¹⁰)/(1−λ¹⁰⁰)` es **monótona en λ**, así que λ sale por
bisección y luego `q = (Rpico−R30)/(1−λ¹⁰)`, `p = Rpico − q`, `τ = −1/ln λ`, `e = p + q/C`, `s = (q/C)/e`.

**Es UNO A UNO**, verificado de ida y vuelta en cinco puntos: error máximo **2,1·10⁻¹⁴**. No es finito-a-uno ni
un continuo: nombrar el comportamiento **determina** los tres parámetros.

La condición de alcanzabilidad es exactamente `Rpico > R30 > R120 > 0` con `p > 0`: el modelo sólo produce
**decaimiento monótono estricto**. No puede producir una fracción retenida que suba.

### §6.2 La región en espacio de comportamiento

| Coordenada | Rango alcanzado | Envolvente docente | Ocupación |
|---|---|---|---|
| `Rpico` | [0,1500; 0,3000] | [0,15; 0,30] | **100 %** |
| `R30` | [0,1500; 0,2500] | [0,15; 0,25] | **100 %** |
| `R120` | [0,0500; 0,1500] | [0,05; 0,15] | **100 %** |

Las **marginales llenan sus cajas por completo**: el modelo puede producir cualquier valor de cada coordenada
por separado. El acoplamiento conjunto es igual de permisivo en lo que importa — para **todo** `R30` en
[0,15; 0,25], el rango completo de `R120` [0,05; 0,15] es alcanzable:

| `R30` ≈ | `R120` alcanzable | `Rpico` alcanzable |
|---|---|---|
| 0,15 | [0,0500; 0,1500] | [0,1500; 0,3000] |
| 0,20 | [0,0500; 0,1500] | [0,2008; 0,3000] |
| 0,25 | [0,0500; 0,1500] | [0,2622; 0,3000] |

El único acoplamiento es el **estructural**: `Rpico ≥ R30`, que eleva el suelo de `Rpico` conforme sube `R30`.
Es decir:

> **La región factible, en espacio de comportamiento, es la caja docente entera, intersecada sólo con el
> decaimiento monótono y con `Rpico ≤ 0,27072` (FD-BLD-06).**

Las restricciones vigentes, leídas en comportamiento, **no imponen nada más allá de las propias envolventes que
la docencia escribió**. Ningún punto queda etiquetado como clínicamente correcto: el modelo sólo dice que
cualquiera de ellos es realizable, y por qué.

### §6.3 Dónde está el `0,125`, exactamente

Con los tres valores provisionales de `REFERENCE` (e = 0,125; s = 0,6; τ = 30):

| Coordenada | Valor | Envolvente | Situación |
|---|---|---|---|
| `Rpico` | **0,103833** | [0,15; 0,30] | **fuera, por abajo** — 30,8 % por debajo del suelo |
| `R30` | **0,088625** | [0,15; 0,25] | **fuera, por abajo** — 40,9 % por debajo del suelo |
| `R120` | 0,051868 | [0,05; 0,15] | dentro, y apenas: a 3,7 % del suelo |

Por qué, en una línea: `0,830666 × 0,125 = 0,103833 < 0,15`, y la desigualdad `Rpico ≥ 0,15` con
`a_pico < 1` fuerza `e > 0,15` **para cualesquiera (s, τ)**. Así que ningún par (s, τ) rescata el `0,125`: no
es que esté en una esquina mala de la región, es que **está fuera de la proyección de la región sobre `e`**.

### §6.4 La pregunta exacta para la docencia

No se pregunta por `e`, ni por `s`, ni por `τ`. Se pregunta por comportamiento, con la semántica exacta del
repositorio (`IMPLEMENTATION` de FD-BLD-04/05: fracción del volumen infundido retenida intravascularmente,
bolsa de 1 L isotónico entrando en 20 min desde el minuto 0, sangrado del caso continuando):

> **De 1 L isotónico en estos adultos hipovolémicos:**
>
> **(a)** ¿qué rango de **fracción retenida a los 30 minutos** es clínicamente defendible para este modelo?
> Hoy la envolvente dice 15–25 % (150–250 mL por litro).
>
> **(b)** ¿qué rango a los **120 minutos**? Hoy dice 5–15 % (50–150 mL por litro).
>
> **(c)** *opcional:* ¿qué rango en el **máximo**, que ocurre al terminar la infusión (minuto 20)? Hoy dice
> 15–30 %, y la dilución de Hb a 2 L lo recorta a ≤ 27,07 %.

Nombrar (a) y (b) deja una familia de un parámetro; nombrar también (c) **determina (e, s, τ) de forma única**,
por la inversa de §6.1. Estrechar los rangos es lo que estrecha la región (§7); no hace falta ninguna
observación nueva.

---

## §7 (P3-78) Ganancia de información de una cuarta observación

### §7.1 Anchura actual

- Pares (s, τ) admisibles: 236 360 de 238 601 explorados; `e ∈ [0,150; 1,000]`.
- En comportamiento: exactamente las cajas docentes (§6.2), con `Rpico ≤ 0,27072`.

Dicho sin eufemismo: en **parámetros crudos** la región es ancha (`e` abarca un factor 6,7 hasta el borde del
dominio, porque `s` puede acercarse a 1 compensando). En **comportamiento** es exactamente lo que la docencia
declaró. No se inventa ningún umbral de «demasiado ancha»: se describe. Y conviene notar que la magnitud que
actúa físicamente —el volumen retenido, que es lo que llega a la presión— **es** la coordenada de
comportamiento, no `e`: está acotada por las envolventes aunque `e` no lo esté por separado.

### §7.2 La dilución de Hb a 2 L, evaluada

- **Qué dirección restringe:** `Rpico`, y sólo `Rpico`. A `Rpico` constante su dispersión es **0,01 %** mientras
  `R120` varía 68 %.
- **¿Independiente de FD-BLD-04/05?** **No.** Es **colineal con FD-BLD-04**, que ya acota `Rpico`. Su lectura
  tardía (dilución a 120 min) sí lleva información de (s, τ) —dispersa 66,6 % a `Rpico` constante— pero es
  entonces colineal con `R120`, que **FD-BLD-05@120 ya acota**.
- **Cuánto estrecha:** su contribución actual es exactamente `Rpico ≤ 0,27072`, un **19,5 %** de la caja de
  FD-BLD-04. No reduce la **dimensión** de la región: sigue siendo 3.
- **¿Redundante?** Sí, en dirección. Aporta un techo útil, no una coordenada nueva.

### §7.3 Qué añadiría más información — ordenado por geometría, no por intuición

Reducción del número de pares (s, τ) admisibles (sin proponer **ningún** valor clínico; sólo anchuras):

**(a) Estrechar al 50 % una envolvente que ya existe:**

| Envolvente | Pares restantes | Reducción |
|---|---|---|
| FD-BLD-04 (pico) | 17 522 | **−70,2 %** |
| FD-BLD-05@120 | 18 883 | **−67,9 %** |
| FD-BLD-05@30 | 23 653 | **−59,8 %** |
| FD-BLD-05@60 | 58 668 | −0,3 % |

**(b) Añadir una lectura nueva en otro tiempo, con la misma anchura relativa (±50 %):**

| Tiempo nuevo | Reducción |
|---|---|
| 15 min | −0,8 % |
| 45 min | −0,0 % |
| 90 min | −0,0 % |
| 180 min | −0,9 % |
| 240 min | −1,5 % |
| 360 min | −3,1 % |

**Estrechar una envolvente existente informa entre 20 y 230 veces más que añadir un punto temporal nuevo.** La
razón es estructural y ya está dicha en §6.1: las cuatro lecturas son cuatro puntos de **la misma curva** de
tres parámetros, así que un quinto punto está casi determinado por los otros. El cuello de botella **no es el
número de observaciones: es la anchura de las envolventes.**

### §7.4 Veredicto P3-78

> **`A · EXISTING_THREE_CONSTRAINTS_ARE_SUFFICIENT_TO_DEFINE_A_USEFUL_REGION`**

«Útil» quiere decir, exactamente: la región es **no vacía**, **acotada**, **caracterizada en forma cerrada**,
**explica punto por punto** el testigo de 62/200, y en coordenadas de comportamiento coincide con las propias
envolventes docentes, de modo que nombrar un comportamiento dentro de ellas **determina de forma única** los
tres parámetros. No es **B** porque la cuarta observación propuesta es colineal y aporta ≤ 3 %. No es **C**
porque la transformada es uno a uno y no hay no-identificabilidad estructural: el rango es 3. No es **D** porque
no falta evidencia clínica para definir la región — falta una **decisión** sobre su anchura.

---

## §8 (P3-79) Pack de decisión de calibración de volumen

1. **Por qué se retira el `0,125` como referencia vigente.** Es un valor **provisional de P2I-2T**, anterior a
   las envolventes de P2I-2U; `blood_anchors.REFERENCE` se autodocumenta «canonical **provisional** values» y
   `EXPLORATION` «**neither** candidate bands **nor** approved values»; TD-88 ya lo registraba como no
   superviviente desde P2I-2X; y ahora está probado que **ningún** (s, τ) lo rescata, porque `e > 0,15` es una
   consecuencia analítica de `a_pico < 1`. Los artefactos históricos **se conservan**: nada de la historia
   congelada se reescribe (V-1).
2. **Semántica exacta de la retención.** Fracción del **volumen infundido** que permanece **intravascular**, en
   el marco de `BloodState` en mL reales, **antes** de la conversión `kappa` a la `V` canónica; al ser un
   cociente, es invariante a `kappa`. Bolsa de 1 L isotónico en 20 min desde el minuto 0, con el sangrado del
   caso continuando. **No** es `V`, **no** es equivalente de sangre entera, **no** es volumen plasmático,
   **no** es salida.
3. **Región analítica.** §2 a §5: forma cerrada exacta a 1,1·10⁻¹⁶; intervalo cerrado de `e` por cada (s, τ);
   `e ∈ [0,150025; 1,0]`; conexa salvo una banda `s ∈ (0,825; 0,865)`; 200/200 contra el testigo.
4. **Región en comportamiento.** §6.2: la caja docente entera, intersecada con el decaimiento monótono y
   `Rpico ≤ 0,27072`.
5. **Dónde está la referencia actual.** §6.3: fuera por abajo en `Rpico` (−30,8 %) y en `R30` (−40,9 %); dentro
   sólo en `R120`.
6. **Qué aporta cada restricción.** FD-BLD-05@30 liga el borde inferior en 98,3 % de la región; FD-BLD-05@120
   el superior en 91,7 %; FD-BLD-04 **nunca** liga por abajo, liga por arriba en 1,3 % **y es lo que desconecta
   la región** en `s ∈ (0,825; 0,865)`; FD-BLD-05@60 es casi inerte (0,3 %); FD-BLD-06 aporta exactamente
   `Rpico ≤ 0,27072`.
7. **¿Aporta información una cuarta observación?** No materialmente: §7. Colineal con FD-BLD-04, ≤ 3 % para
   cualquier tiempo nuevo, frente a 60–70 % por estrechar una envolvente existente.
8. **Las preguntas exactas de comportamiento.** §6.4: (a) fracción retenida a 30 min, (b) a 120 min, (c)
   opcional, el máximo. **Nunca se pregunta por `e`, `s` ni `τ`.**
9. **Qué queda incierto.** La anchura de las envolventes es una decisión, no un dato. Los dos casos GI son
   **dos pacientes redactados**, no una muestra clínica. La dependencia de FD-BLD-06 del volumen de llegada
   significa que su techo sobre `Rpico` es **por caso** (0,27072 y 0,28518): un tercer caso con otro volumen de
   llegada movería ese techo. `s` y `τ` no tienen dominio declarado.
10. **Por qué esto NO calibra la presión.** Medido en P3-72 y no contradicho aquí: las lecturas de FD-BLD-04 y
    05 son invariantes a `preload_scale_over_kappa_ml` y a la posición de precarga, y las de FD-BLD-06 también.
    Fijar el volumen **no aporta ninguna información sobre (ν, f)**. La presión seguirá necesitando las cuatro
    decisiones de FD-P3-68. V-4 queda confirmada en su orden y en su advertencia.

---

## §9 (P3-80) Punto de control de preparación

> **`A · FACULTY_CAN_NOW_DEFINE_VOLUME_BEHAVIORAL_REGION`**

La docencia puede nombrar un rango de comportamiento: la región está caracterizada en forma cerrada, la
transformada a parámetros es uno a uno y verificada, cualquier comportamiento dentro de las cajas es realizable,
la contribución de cada restricción está cuantificada, y no hace falta ninguna observación nueva para empezar.

### P3-81 — ENTRADA DE RESTRICCIÓN DE COMPORTAMIENTO DE VOLUMEN (**borrador, no ejecutado**)

Campos que la docencia rellena. **Ninguno pide un parámetro.**

| Campo | Qué se pide | Hoy | Obligatorio |
|---|---|---|---|
| `R30_range` | fracción retenida de 1 L a los **30 min**, como par (inferior, superior) | (0,15; 0,25) | **sí** |
| `R120_range` | ídem a los **120 min** | (0,05; 0,15) | **sí** |
| `Rpeak_range` | ídem en el **máximo** (minuto 20) | (0,15; 0,30), recortado por FD-BLD-06 a ≤ 0,27072 | opcional |
| `fourth_observation_used` | si se incorpora la dilución de Hb a 2 L como restricción adicional | ya está dentro, vía FD-BLD-06 | **sí** (sí/no) |
| `applies_to` | a qué casos aplica el techo de FD-BLD-06, que es por caso | `gi_bleed_57m`, `gi_bleed_72f` | **sí** |
| `provenance` | de dónde sale cada rango: literatura, consenso docente, o juicio declarado | — | **sí** |

Reglas de la entrada, para que no se cuele una aprobación encubierta:
- se exige `Rpico ≥ R30 ≥ R120` (el modelo no produce otra cosa) y se rechaza lo contrario con el motivo;
- si los tres rangos se nombran, la inversa de §6.1 da el (e, s, τ) único y la entrada lo **muestra**, sin
  aprobarlo: aprobar un punto sigue siendo una decisión aparte;
- si sólo se nombran dos, la entrada devuelve la familia de un parámetro, no un punto;
- **no** se propone ningún valor por omisión, y la herramienta rechaza responder sin envolventes (prueba R13).

**No se ejecuta.** Hace falta que la docencia responda §6.4 primero.

---

## §10 Corrección de una frase mía de P3-72

En `docs/PHASE3_BLOOD_VOLUME_SEMANTICS.md` §6 y en FD-P3-72 escribí, del bloque de volumen entero:

> «sus lecturas son invariantes a `preload_scale_over_kappa_ml`, a la posición de precarga, al volumen de
> llegada, al relleno y a la tasa de sangrado»

Es **exacto para FD-BLD-04 y FD-BLD-05**, que es lo que había medido (la fila `retained`). Es **falso para
FD-BLD-06**, que no había medido por separado: su dilución depende con fuerza del **volumen de llegada** (factor
1,63 entre 3000 y 5000 mL) y débilmente del sangrado y del relleno. El verdadero alcance de la medida de P3-72
eran las cuatro lecturas de retención, no las tres restricciones.

**Qué cambia y qué no.** El veredicto `SEPARABLE_CALIBRATION` **se mantiene**, y por la razón que importaba: el
bloque de volumen es invariante a las **coordenadas de presión** (`preload_scale_over_kappa_ml`, posición), y
eso sí se midió para las tres —incluida FD-BLD-06, idéntica en todos los dígitos (§1)—. Lo que **no** vale es
la palabra «invariante al volumen de llegada y al relleno» aplicada a FD-BLD-06. La consecuencia práctica es
real y está en §8.9: **el techo de `Rpico` que impone FD-BLD-06 es por caso**, no universal.

Corregido aquí, en `PHASE3_BLOOD_VOLUME_SEMANTICS.md` §6, en FD-P3-72 y en TD-130.
