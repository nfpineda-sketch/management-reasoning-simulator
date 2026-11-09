# Fase 3 — Región de comportamiento de volumen: registro, transformada y cierre (P3-81 … P3-87)

Rama `phase-3-runtime-integration`, desde `bae13e7`. Un único paquete ejecutable (P3-81, que **registra**); el
resto es análisis y sólo lectura. No cambia fisiología, no cambia restricciones FD-BLD, **no aprueba ningún
punto de parámetros**, no toca `gi_pressure_committed`, no mueve autoridad
(`COMMON_CORE_RUNTIME_AUTHORITY = False`, `APPROVED_SNAPSHOTS` = 1). Ningún archivo de `clinical_core/` cambia.

Archivos nuevos, los dos fuera de `clinical_core` y del registro de autoridad, y sin importar ninguno de los
dos: `volume_behaviour_record.py` (el registro) y `test_volume_behaviour_record.py` (15 pruebas).

---

## §1 (P3-81) El registro, y una lectura de V-2 que conviene confirmar

| Campo | Valor registrado |
|---|---|
| `status` | **`FACULTY_DEFINED_BEHAVIORAL_REGION`** |
| `R30_range` | (0,15; 0,25) |
| `R120_range` | (0,05; 0,15) |
| `Rpeak_range` | (0,15; **0,27072**) |
| `fourth_observation_used` | `False` |
| `applies_to` | modelo de cristaloide del adulto GI certificado, con la semántica exacta del repositorio: fracción del volumen infundido retenida intravascularmente, bolsa de 1 L isotónico entrando en 20 min desde el minuto 0, con el sangrado del caso continuando |
| `provenance` | FD-BLD-04, 05 y 06 vigentes, más la decisión docente V-2 del 2026-11-09 que las acepta como región inicial. **Ningún número clínico nuevo** |

Los tres rótulos que este registro **no** puede llevar están declarados en el módulo y una prueba comprueba que
ningún campo los lleva y que el módulo no los asigna a nada: `CLINICALLY_VALIDATED_PARAMETER_POINT`,
`FACULTY_APPROVED_PARAMETER_POINT`, `CANONICAL_VOLUME_PARAMETER_SET`.

**La banda histórica de FD-BLD-04 no se reescribe.** `FD_BLD_04_HISTORICAL_PEAK = (0.15, 0.30)` queda en el
registro tal cual, comprobada contra el módulo congelado, y el techo efectivo más estrecho vive **aparte**, como
lo que es: la intersección de las restricciones vigentes sobre los dos casos GI certificados.

### La lectura de V-2 que hay que confirmar: FD-BLD-05@60

V-2 nombra tres coordenadas: `R30`, `R120` y `Rpeak`. El conjunto congelado tiene **cuatro** lecturas: también
`R60 ∈ [0,10; 0,20]`. Medido: **la caja de tres coordenadas NO implica la cuarta.** De 709 038 puntos probados
dentro de la caja, **10 976 (1,5 %)** violan `R60`:

| | (s, τ, e) | Rpico | R30 | **R60** | R120 |
|---|---|---|---|---|---|
| peor por abajo | (0,9; 13; 0,498994) | 0,27043 | 0,15209 | **0,06007** | 0,05000 |
| peor por arriba | (0,995; 175; 0,280657) | 0,26454 | 0,24992 | **0,21077** | 0,15000 |

Las tres coordenadas nombradas caen dentro de sus cajas y la cuarta queda fuera por mucho. Como V-2 acepta «las
restricciones de comportamiento **ya existentes** definidas por la docencia», y FD-BLD-05@60 **es** una de
ellas, el registro la lleva: `EFFECTIVE_REGION` son las cuatro lecturas. **Es una lectura de V-2, no una
ampliación**, y la señalo para que la docencia la confirme; sin ella, la región registrada admitiría puntos que
violan una restricción congelada.

> **Preparación P3-81: `FACULTY_VOLUME_BEHAVIOR_REGION_RECORDED`.**

### Validación de entradas, sin valores por omisión

`validate_entry` devuelve los motivos del rechazo, por nombre: `FALTA_<campo>` (no rellena nada),
`RANGE_INVERTED`, `UNREACHABLE_THE_MODEL_ONLY_DECAYS` (el techo de una lectura posterior no puede superar el de
una anterior: el modelo sólo decae), `UNREACHABLE_A_RETAINED_FRACTION_MUST_BE_POSITIVE` y
`OUTSIDE_THE_RECORDED_REGION`. Una entrada vacía se rechaza por los tres campos que faltan.

---

## §2 (P3-82) La región de parámetros

Con la transformada exacta de P3-77 y el intervalo cerrado de `e` por cada (s, τ):

| | Caja docente sola (pico, R30, R120) | **EFECTIVA** (+ FD-BLD-05@60) |
|---|---|---|
| pares (s, τ) admisibles | 236 346 | **235 876** |
| `e` | [0,150025; 1,000000] | [0,150025; 1,000000] |
| `s` | [0,005; 0,995] | [0,005; 0,995] |
| `τ` | [1; 600] min | [1; 600] min |

**§2.1 Representación.** La región es analítica en una dimensión y numérica en ninguna: para cada (s, τ),
`e ∈ [máx_k(inf_k/a_k), mín(mín_k(sup_k/a_k), 1,0)]` con `a_k(s,τ)` en forma cerrada. **No** es una lista de
puntos de rejilla: la rejilla sólo muestrea (s, τ), y en cada muestra el intervalo de `e` es exacto.

**§2.2 Componentes conexas, y la topología SÍ cambia.** La caja docente sola tiene hueco en τ para 12 valores de
`s`, concentrados en `s ∈ [0,825; 0,88]`. Al añadir FD-BLD-05@60 los huecos siguen siendo 12 pero **se
desplazan y se ensanchan hacia abajo**, empezando en `s = 0,80`:

| s | hueco en τ, caja sola | hueco en τ, EFECTIVA |
|---|---|---|
| 0,80 | — | (12,5; 17,0) |
| 0,81 | — | (10,5; 19,5) |
| 0,825 | (5,0; 8,0) | (5,0; 8,0) **y** (8,5; 22,0) |
| 0,83 | (4,5; 8,5) | (4,5; 23,0) |

Y en algunos (s, τ) la cuarta lectura no estrecha el intervalo sino que **lo vacía por completo**: en
(s = 0,9; τ = 13) —el peor contraejemplo de §1— la región efectiva es vacía. Esto es parte de por qué el
registro tiene que llevar @60.

**§2.3 Proyecciones** (ningún punto medio preferido): `e ∈ [0,150025; 1,000000]`; `s ∈ [0,005; 0,995]`, con los
199 valores explorados teniendo algún τ admisible; `τ ∈ [1; 600]` min, con los 1 199 valores teniendo algún `s`.
`@60` recorta el **interior** de los intervalos sin mover la proyección de `e`.

**§2.4 El punto provisional de referencia.** (e, s, τ) = (0,125; 0,6; 30):

| | valor | contra | situación |
|---|---|---|---|
| `Rpico` | 0,103833 | [0,15000; 0,27072] | **fuera por abajo** |
| `R30` | 0,088573 | [0,15000; 0,25000] | **fuera por abajo** |
| `R60` | 0,064190 | [0,10000; 0,20000] | **fuera por abajo** |
| `R120` | 0,051920 | [0,05000; 0,15000] | dentro |

Fuera en **tres** de las cuatro lecturas (en P3-77 eran dos de tres: la cuarta lectura lo empeora). Y a su propio
(s, τ) = (0,6; 30) el intervalo admisible es `e ∈ [0,211689; 0,325907]`: el 0,125 queda un **41 % por debajo**
del extremo inferior de su propia fibra. La expectativa previa era «fuera»; **verificado**.

---

## §3 (P3-83) Validación contra FD-BLD

18 testigos adaptativos, por clase, evaluados en **los dos casos** con el evaluador congelado — sin barrido
cartesiano. Clases cubiertas: cuatro interiores, bordes inferior y superior en dos fibras distintas, τ corto
(1 min) y largo (600 min) en interior y en borde, los dos lados del hueco (s = 0,8; τ = 12 y 17,5), `s` mínimo
(0,005) y máximo (0,995), y los testigos de `e` **mínimo** (0,150025) y **máximo** (1,000000) globales.

**§3.1 Resultado de volumen.** Los 15 testigos **interiores** satisfacen FD-BLD-04, 05 y 06 en los dos casos.
Los 3 puestos **exactamente sobre un borde** fallan FD-BLD-05, y la causa está medida y es de **último bit**:

```
borde @30 inferior:  evaluador R30 = 0.14999999999999988   forma cerrada = 0.15
                     delta = −1,110·10⁻¹⁶  contra el borde inclusivo 0,15  ->  falla
borde @120 superior: evaluador R120 = 0.15000000000000002  forma cerrada = 0.15
                     delta = +2,776·10⁻¹⁷  ->  falla por arriba
```

Metiendo el testigo **10⁻⁹ relativo hacia dentro**, los tres pasan las tres restricciones en los dos casos. Es
una propiedad declarada de la comparación —inclusiva sobre el valor **sin redondear**, que difiere de la forma
cerrada en ~10⁻¹⁶— y no un defecto. El registro la lleva como `WITNESS_INTERIOR_MARGIN`, y la consecuencia
operativa es: **la región se registra cerrada, y todo testigo numérico se pone estrictamente dentro.**

**§3.2 Lo que NO es un hallazgo de volumen.** `U-OUT` y `FD-BLD-02` fallan en los 18 testigos, en los dos casos.
No son restricciones de cristaloide: dependen de la tasa de sangrado y de (ν, f), que en estos testigos quedaron
en `REFERENCE` —un no-superviviente conocido para `U-OUT` desde P3-68, que sólo se satisface a 2,75 mL/min—.
Decirlo como «la región de volumen falla restricciones» sería un error de atribución.

**§3.3 Consistencia de la inversa.** Para los 18 testigos, parámetro → comportamiento → parámetro: **peor error
7,961·10⁻¹²**, y la mayoría por debajo de 10⁻¹⁴. Los peores son los de τ muy corto y muy largo, por la razón
de §4.3.

> **Veredicto P3-83: `VOLUME_BEHAVIOR_REGION_VALIDATED_AGAINST_FD_BLD`**, con las dos declaraciones de arriba:
> los testigos van estrictamente dentro, y los fallos de `U-OUT`/`FD-BLD-02` son del bloque de presión.
> Ninguna restricción se reemplazó: se evaluaron las originales congeladas.

---

## §4 (P3-84) Robustez y dependencia del caso

**§4.1 Los techos por caso se conservan, los dos.** Lo que difiere entre los dos casos certificados es su **Hb de
llegada redactada**: 6,7 g/dL (`gi_bleed_57m`) y 6,4 g/dL (`gi_bleed_72f`). Y eso explica los techos, porque la
dilución vale `Hb₀·ΔV/(V₀+ΔV)`: con menos Hb de partida, el mismo volumen diluye menos, así que el caso de Hb
más baja **tolera un `Rpico` más alto**.

| Caso | Hb₀ | techo de `Rpico` | producto techo × Hb₀ |
|---|---|---|---|
| `gi_bleed_57m` | 6,7 | **0,27072** | 1,8138 |
| `gi_bleed_72f` | 6,4 | 0,28518 | 1,8252 |

Los dos productos coinciden al **0,6 %**, que es la confirmación de que el mecanismo es ese y no otro.

La región **común** usa la intersección, 0,27072, porque tiene que valer en los dos casos. Eso **no hace
desaparecer** el techo del otro: los `Rpico ∈ (0,27072; 0,28518]` satisfacen `gi_bleed_72f` y **no**
`gi_bleed_57m`. Esa franja mide 0,01446 de `Rpico`, un **9,6 %** de la caja histórica de FD-BLD-04, y el
registro la expone como `case_only_peak_band`, con error si se pide un caso no certificado.

**§4.2 Dependencia del volumen de llegada.** Cuantificada en P3-76 como **sonda de sensibilidad**: el pico de
dilución a 1 L vale 0,4301 a 3000 mL, 0,3273 a 4000 y 0,2642 a 5000 — un factor 1,63. **No extrapolo de ahí**,
porque 3000 y 5000 no son valores redactados de ningún caso certificado: los dos casos comparten el volumen de
llegada de referencia y difieren en Hb₀ (§4.1). Lo que esa sonda sí establece es que **el techo es por caso**, y
que un tercer caso con otro volumen de llegada **o** con otra Hb₀ lo movería. Está declarado como TD-130 (29).

**§4.3 Estabilidad y condicionamiento.** La inversa divide por la separación `Rpico − R120`, que es lo que mide
cuánta curva hay. Número de condición medido:

| Punto | separación `Rpico − R120` | condición |
|---|---|---|
| τ = 20, interior | 0,061230 | 2,1·10³ |
| τ = 60, interior | 0,057460 | 2,0·10⁴ |
| τ = 200 | 0,025398 | 6,1·10⁵ |
| **τ = 600** | 0,007015 | **2,1·10⁷** |
| **s = 0,005** | 0,000514 | **2,6·10⁶** |
| s = 0,995, τ = 300 | 0,051320 | 7,0·10⁵ |

**La inversa está mal condicionada donde la curva de retención es casi plana**: τ muy largo o `s` muy bajo. Ahí
un comportamiento conocido con poca precisión da parámetros con muchísima menos. **No hay** saltos de frontera
ni cambios de topología dentro de la región registrada —las únicas discontinuidades son los huecos de §2.2, que
están en `s ≈ 0,80–0,88` y acotados—, pero esa subregión queda **marcada**.

**§4.4 No unicidad práctica.** La transformada es uno a uno para **tres coordenadas exactas**; la docencia
nombró **intervalos**, y un intervalo produce región. Qué direcciones quedan anchas y por qué:

- **`e`**: su **cota inferior es nítida** —`e > 0,15` es una desigualdad estricta analítica— y su cota superior
  la fija el dominio declarado (`e < 1`) en la esquina `s → 1`. Ancha en extensión, pero con un borde inferior
  duro.
- **`s` y `τ`**: **anchas**, y por la combinación de §4.3 con el ancho de las cajas: la anchura de 0,10 en `R30`
  y `R120` atraviesa una inversa cuyo condicionamiento llega a 10⁷, así que `s` cubre casi todo (0,1) y `τ`
  todo [1, 600] min. Estrechar las cajas es lo único que las estrecha (medido en P3-78: 60–70 % por envolvente).

---

## §5 (P3-85) Revisión adversarial

| Ataque | Veredicto | Por qué |
|---|---|---|
| Usar el techo de 57m como si fuera clínico universal | **`ROBUST`** (no se hace) | Está registrado como **intersección** de dos casos redactados, con los dos techos por caso conservados y la franja de 72f expuesta aparte. La `provenance` dice de dónde sale. Tratarlo como universal es un uso que el registro bloquea por construcción |
| Sobreajuste oculto a dos pacientes redactados | **`WEAK`, y declarado** | Nada se ajusta —no hay ningún número clínico nuevo— pero el **alcance** son dos pacientes: el techo deriva de dos valores de Hb₀ redactados (6,7 y 6,4), y un tercer caso lo movería. TD-130 (29) |
| Tratar los intervalos de comportamiento como evidencia empírica | **`ROBUST`** (no se hace) | `provenance` dice «FD-BLD-04/05/06 vigentes más la decisión docente V-2», y `fourth_observation_used = False`. Son **restricciones docentes**, no observaciones; el documento lo repite donde podría confundirse |
| La inversa creando falsa precisión | **`WEAK`, y cuantificado** | Es exacta a 2,1·10⁻¹⁴ **y** mal condicionada donde la curva es plana: condición hasta 2,1·10⁷ (§4.3). Un comportamiento preciso da parámetros precisos; un comportamiento **con incertidumbre** da parámetros con mucha más. Marcado, no escondido |
| Interpretar `e`, `s`, `τ` fisiológicamente más allá de su sentido operativo | **`WEAK`** | Son parámetros de un modelo reducido: `s` **no** es «la fracción intersticial» ni τ «una vida media de redistribución medida». El `applies_to` del registro fija el sentido operativo, y las preguntas docentes se hacen en comportamiento justamente para no pedir interpretación de parámetros |
| Dependencia del caso de FD-BLD-06 | **`ROBUST`** (reconocida y medida) | §4.1: el mecanismo es Hb₀, con los dos productos techo×Hb₀ coincidiendo al 0,6 %. Los dos techos se conservan |
| El supuesto de retención monótona | **`ROBUST`** | **No es un supuesto: es consecuencia** de las ecuaciones congeladas —tras la infusión la reserva decae geométricamente— y la inversa **rechaza** por nombre un comportamiento que suba (`UNREACHABLE_THE_MODEL_ONLY_DECAYS`), con prueba |
| Artefactos de topología o de región desconectada | **`ROBUST`** | Los huecos son reales, acotados por bisección a 10⁻¹², y la banda **se mueve** al añadir @60 (§2.2); en un caso el (s, τ) se vacía del todo. Se comprobó por refinamiento que no son resolución de rejilla |
| Descartar demasiado pronto la cuarta observación | **`WEAK`, con un matiz que importa** | P3-78 midió la colinealidad del **pico** de dilución (dispersión 0,01 % a `Rpico` constante). Pero la dilución **tardía** sí lleva (s, τ): dispersa 66,6 %. Se juzgó redundante **porque `R120` ya está acotado** — si la docencia estrechara `R120`, la dilución tardía se volvería **más** informativa, no menos. Y la decisión es reversible: `fourth_observation_used` es un campo, no un borrado |
| La instantánea de autoridad influyendo en la región | **`ROBUST`** (no influye) | Medido en las dos direcciones: los veredictos de presión y salida son **idénticos** en tres puntos que atraviesan la región de volumen (§7.1), y las lecturas de volumen son invariantes a `preload_scale_over_kappa_ml` y a la posición. `gi_pressure_committed` sin tocar, `APPROVED_SNAPSHOTS` = 1 |

**Ninguna conclusión `UNSUPPORTED` ni `CIRCULAR`.** Cinco `ROBUST`, cinco `WEAK` declaradas con su medida.

---

## §6 (P3-86) Cierre de la calibración de volumen

> **`A · VOLUME_BEHAVIORAL_CALIBRATION_REGION_CLOSED`**

La región está **acordada** (V-2) e **internamente consistente**: registrada con su estado y procedencia, con la
banda histórica intacta, validada contra las restricciones congeladas originales en los dos casos y en 18
testigos de clase, consistente en la inversa a 7,961·10⁻¹², con los techos por caso conservados y la subregión
mal condicionada marcada. **A no significa** que ningún punto esté clínicamente validado.

Lo único que señalo para confirmación docente es la lectura de §1: la región lleva **FD-BLD-05@60**, que V-2 no
nombró y que la caja de tres coordenadas no implica. No bloquea: @60 es una restricción docente **ya existente**,
y V-2 aceptó las existentes.

### §6.1 Tabla de estado

| | Estado |
|---|---|
| `e` | `DERIVED_REGION` · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` — cota inferior nítida (`e > 0,15`, analítica), cota superior en el dominio declarado |
| `s` | `DERIVED_REGION` · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` — dirección ancha (§4.4) |
| `τ` | `DERIVED_REGION` · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` — dirección ancha, e inversa mal condicionada a τ largo |
| `Rpico` | `FACULTY_CONSTRAINED` por abajo (FD-BLD-04) · techo `DERIVED_REGION` (intersección de FD-BLD-06 sobre los dos casos) · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` |
| `R30` | `FACULTY_CONSTRAINED` · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` |
| `R120` | `FACULTY_CONSTRAINED` · `NONUNIQUE` · `NOT_CLINICALLY_VALIDATED` |

(`R60` queda `FACULTY_CONSTRAINED` por la restricción congelada, pendiente de la confirmación de §1.)

### §6.2 El valor histórico

`crystalloid_effective_ml_per_ml = 0,125` queda clasificado formalmente como
**`HISTORICAL_PROVISIONAL_NON_SURVIVING_REFERENCE`**, en `volume_behaviour_record.HISTORICAL_REFERENCE`, con
`rewrites_frozen_history = False` y una prueba que comprueba que el valor **sigue intacto** en el módulo
congelado: esto **rotula, no reescribe**.

---

## §7 (P3-87) Vuelta a la presión

**§7.1 Qué restricciones de presión son independientes de la región de volumen.** **Todas las medidas.** Los
veredictos de `U-OUT`, `U-HB`, `FD-BLD-01`, `FD-BLD-02`, `SECOND-UNIT` y `FD-BLD-03` son **idénticos** en tres
puntos que atraviesan la región de volumen —(0,16; 0,2; 30), (0,22; 0,4; 60) y (0,33; 0,6; 30)— en los dos
casos. Razón: `U-OUT` lee el curso **sin tratar**, donde no hay cristaloide, y la vía de glóbulos no pasa por
(e, s, τ). Así que fijar el volumen **no informa** la presión, exactamente como V-4 advierte.

**§7.2 Qué sigue acoplado a la tasa de sangrado.** `U-OUT`, y con fuerza. Medido en el punto comprometido de
presión, con el cristaloide dentro de la región registrada:

| tasa (mL/min) | 2,0 | 2,25 | 2,5 | **2,75** | 3,0 | 3,25 | 3,5 |
|---|---|---|---|---|---|---|---|
| `gi_bleed_57m` | no | no | no | **sí** | sí | sí | sí |
| `gi_bleed_72f` | sí | sí | sí | **sí** | no | no | no |

Los dos casos aprietan la tasa **desde lados opuestos** y se cruzan en un único valor muestreado, 2,75. La tasa
es una coordenada **candidata**, no un dato, y fijar el volumen no la desacopla en absoluto.

**§7.3 ¿Puede la docencia juzgar pendiente y meseta sin ambigüedad del cristaloide?** Ahora **acotada**, no
eliminada. P3-68C reportaba que «por 100 mL infundidos» y «por 100 mL efectivos» difieren en un factor **8 a 20
y dependiente del tiempo**. Con la región registrada, 100 mL infundidos entregan entre **15,00 y 27,07 mL
efectivos** en el pico: un factor residual de **1,8048×**, acotado y sin dependencia temporal en el pico. Y
desaparece del todo si la pregunta se plantea en volumen **efectivo**, que es la coordenada propia del modelo, o
si se juzga contra el curso sin tratar y la vía de glóbulos, que es lo que `U-OUT` y `FD-BLD-02` ya hacen.

**§7.4 Qué decisiones exactas faltan antes de registrar una región de comportamiento de presión.**

1. **La tasa de sangrado.** Es candidata y los dos casos la cruzan en un solo valor muestreado. Hay que decidir
   si se fija por decisión docente, si se admite una banda por caso, o si `U-OUT` se relaja — y lo último es una
   decisión clínica, no técnica.
2. **Las cuatro de FD-P3-68**, intactas: en qué observable se juzga la presión (pendiente en mmHg por 100 mL
   **efectivos**, meseta, o ambas), con qué rango, en qué momento del encuentro, y qué hacer con la procedencia
   legado del canónico de `preload_curve_scale_ml` (TD-130 (23)).
3. **La mitad que falta de la razón identificable**: `volume_preload_kappa` sigue sin región declarada
   (TD-130 (24)), y sólo `ν = kappa/escala` es identificable, no las dos por separado.
4. **Si la pregunta se plantea en volumen efectivo**, confirmar que la docencia acepta juzgar «mmHg por 100 mL
   efectivos» — lo que hace irrelevante el factor 1,8048× — o si prefiere el infundido y acepta esa banda.

> **Veredicto P3-87: `B · PRESSURE_CALIBRATION_STILL_COUPLED_TO_BLEEDING_RATE`**

No es **A** porque la tasa de sangrado sigue siendo una coordenada candidata que los dos casos cruzan en un
único valor muestreado, y ninguna decisión de volumen cambia eso: la entrada docente de presión no se puede
plantear sin decidirla primero. No es **C** porque no falta evidencia clínica para **acotar** —las restricciones
existentes ya estrechan la presión a un 2–5 % de su rango declarado (FD-P3-64)—. No es **D** porque la ecuación
de presión no necesita revisión estructural: se reduce exactamente a dos parámetros (verificado a 2,2·10⁻¹⁶ en
P3-58).
