# Fase 3 · Escala absoluta de la tasa de sangrado GI, reabierta tras la primera revisión docente humana (P3-314 a P3-325, 2026-11-15)

> **Identificabilidad (P3-319): `B · BLEED_RATE_AND_PRESSURE_MAP_REQUIRE_JOINT_REGION`.**
> **Decisión de Enmienda 3 (P3-324): `B · JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED`. No se abre la Enmienda 3.**
> **`FR-G_V2_CANDIDATE`: NO generado** (la tasa sola no resuelve el conflicto; P3-323 prohíbe fabricarlo).

Rama `phase-3-runtime-integration`. **Sólo lectura y análisis** (`MODEL_ANALYSIS`): `gi_bleed_rate_analysis.py`, registro
`docs/revision/PHASE3_GI_BLEED_RATE_SCALE_ANALYSIS.json`, pruebas `test_phase3_bleed_rate_scale.py`. **No aprueba ninguna tasa, ningún parámetro de presión ni ninguna región.** No cambia
`clinical_core/` (el digesto vivo sigue siendo el certificado `a0af7d08…`), ni `family_engine.py`, ni la instantánea `gi_pressure_committed`, ni la autoridad, ni la región de cristaloide
cerrada. Los juicios humanos de la primera revisión quedan **exactamente** como estaban (registro `9ba80fa7…`). Sin norepinefrina, sin control de fuente nuevo, sin validación clínica.

Este ciclo **continúa** y no repite `docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md` (P3-88 a P3-95), cuyos resultados se **recalcularon y siguen vigentes**. Lo nuevo es la evidencia humana
del FR-G, que es la primera observación que alcanza la escala **absoluta**.

**Aviso de identificadores.** El encargo nombra sus decisiones «FD-BLD-01» a «FD-BLD-08». Esos identificadores **ya existen**: `FD-BLD-01` a `FD-BLD-09` son las restricciones docentes
congeladas de sangre (`clinical_core/blood_constraints.py`; p. ej. `FD-BLD-04` es el aporte temprano del cristaloide). Para no crear dos significados, las decisiones nuevas se registran
como **`FD-RATE-01` a `FD-RATE-08`**, citando el rótulo del encargo. En este documento `FD-BLD-0x` significa **siempre** la restricción congelada. *(Nombre confirmado el 2026-11-15 en el encargo siguiente; ver `docs/PHASE3_GI_JOINT_FEASIBILITY.md`.)*

---

## §1 · P3-315 · De dónde sale 2,5 mL/min

**2,5 mL/min = 0,003 × (300 / 0,36).** Es una **conversión de unidades de una magnitud didáctica heredada**, nunca redactada como pérdida de sangre:

| Valor | Fuente | Archivo · commit | Propósito | Estado |
|---|---|---|---|---|
| **0,003 por minuto** (variable adimensional «circulation»; no son mL) | `family_engine._minute`, rama `gi_bleed` | `family_engine.py`; primer commit `8f77d9a` (2026-09-13, v0.16.0), cuyo mensaje dice que las trayectorias numéricas «remain teaching models requiring faculty validation»; multiplicado por la fracción de sangrado desde `cec7942` (2026-09-19) | empeoramiento sin tratar de la variable de circulación heredada | **`UNKNOWN`**: ni el código, ni el commit, ni las notas registran una fuente clínica |
| **300 / 0,36 = 833,33 mL-eq** por unidad de esa variable | `clinical_core.derived.LEGACY_ML_PER_CIRCULATION_UNIT` | `clinical_core/derived.py`; `ec65728` (2026-10-21) | una unidad de glóbulos ≈ 300 mL (nota `TRANSFUSION`, pregunta docente del 2026-09-20) mueve la circulación heredada 0,36 | `ANALYTICAL_CONVENIENCE` |
| **2,5 mL-eq/min** | `clinical_core.legacy_adapter.haemorrhage_from_legacy` | `9d1d6df` (2026-10-27, P2I-2T); `migration.py`: «adopted for the comparison only» | la pérdida de sangre entera de la sombra y, por tanto, de la autoridad de presión y de **todas** las trayectorias revisadas | **`LEGACY_DERIVED`** |
| 2,5 | `blood_anchors.REFERENCE` | `9b09e30` (2026-10-27): «canonical **provisional** values» | punto de referencia del análisis | `SYNTHETIC_REFERENCE` |
| (1,25; 2,5; 5,0) | `blood_anchors.EXPLORATION` | `9b09e30` | rejilla: «**neither** candidate bands **nor** approved values» | `SYNTHETIC_REFERENCE` |
| 3,0 y 2,0 | `blood_constraints.PROBES` | P2I-2V | sondas fuera de rejilla | `EXPLORATORY_PROBE` |
| (5, 6, 7, 8, 9, 10) | `blood_rate_boundary.RATES` (P2I-2X) | `docs/revision/P2I2X_blood_rate_boundary.json` | densificar el borde superior abierto; registro: viables **{5, 6}**, primera no viable **7**, «no es una tasa aprobada» | `EXPLORATORY_PROBE` |
| (5, 6, 7) × relleno | P2I-2Y | `docs/revision/P2I2Y_CRISTALOIDE_Y_TASA.md` §1 | robustez frente al relleno | `EXPLORATORY_PROBE` |
| 2,0 a 3,5 de 0,25 en 0,25 | P3-87 | `docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md` §7.2 | `U-OUT` contra la tasa | `EXPLORATORY_PROBE` |
| [2,5497; 3,7234] · [1,6894; 2,8038] · común [2,5497; 2,8038] | P3-89 / P3-90 | `docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md` §2.2 | tasas que `U-OUT` admite **en el punto de presión comprometido** | `ANALYTICAL_CONVENIENCE` (derivada de envolventes docentes, condicional al punto de presión) |
| (2,5; 3,5; 5,0) | P3-305 | `frg_crystalloid_analysis.py` | sensibilidad del FR-G | `EXPLORATORY_PROBE` |
| **ninguno** | `blood_constraints.DECISIONS["bleed_rate_authority"]` | decisión docente del 2026-10-27 | la **política** (el caso gana; la familia es respaldo; sin ninguno, falla cerrada) | `FACULTY_DEFINED` (la política; «**no numeric bleed rate is approved**») |

No hay ningún registro `AUTHORED_CASE` ni ningún valor `FACULTY_DEFINED`. **Consecuencia exacta:** como la escala de precarga por omisión es la **misma** constante 833,33, `tasa / escala`
es literalmente el 0,003 heredado. El historial se leyó completo (el clon superficial se profundizó hasta el primer commit, 2026-09-09).

**Un antecedente que importa (historial, no evidencia clínica):** el 2026-09-18 la docencia ya pidió que el cristaloide solo hiciera **menos** que la sangre en la hemorragia GI activa
(`e860ed1`: «2 L of saline restored pressure … almost as well as a transfusion … magnitudes pending review»). El hallazgo del FR-G es la **segunda** vez que aparece la misma objeción.

## §2 · P3-316 · Qué dicen los casos redactados

| | `gi_bleed_57m` | `gi_bleed_72f` | Clase |
|---|---|---|---|
| Presión de llegada | 88/54 | 98/62 | `EXPLICIT_CASE_FACT` |
| FC · FR · SpO₂ | 124 · 26 · 97 % | 112 · 24 · 96 % | `EXPLICIT_CASE_FACT` |
| Relleno capilar · extremidades | 5 s · frías | 4 s · frías | `EXPLICIT_CASE_FACT` |
| Hb · lactato · BUN/creatinina | 6,7 · 4,4 · 48/1,3 | 6,4 · 3,4 · 43/1,2 | `EXPLICIT_CASE_FACT` |
| Ecografía | VCI 0,9 cm, colapso casi completo; VI pequeño e hiperdinámico | VCI 1,1 cm, colapso > 50 %; VI hiperdinámico | `EXPLICIT_CASE_FACT` |
| Síntomas · presíncope | casi se desmaya al ponerse de pie; debilidad profunda | fatiga, mareo; tuvo que detenerse al caminar | `EXPLICIT_CASE_FACT` |
| Fuente referida | heces negras y pegajosas, sin hematemesis; tacto rectal con melena | melena tres días, **otro episodio esta mañana**; sin hematemesis | `EXPLICIT_CASE_FACT` |
| Duración referida de la melena | «desde ayer» | «tres días» | `EXPLICIT_CASE_FACT` |
| Contexto | ibuprofeno dos semanas | naproxeno, úlcera previa, sin protector | `EXPLICIT_CASE_FACT` |
| Sangrado en curso | historia de melena continua; foco docente «monitoring ongoing blood loss» | ídem | `INFERRED_SEVERITY_ONLY` |
| Severidad de la hemorragia | hipotensión, taquicardia, lactato, anemia grave, VCI colapsable: pérdida grande **previa** a la llegada, implicada, no medida | ídem | `INFERRED_SEVERITY_ONLY` |
| Duración de la hipoperfusión | — | — | `NOT_SPECIFIED` |
| Cantidad de sangre perdida · tasa (mL/min, mL/h) · pérdida total | — | — | `NOT_SPECIFIED` |
| Peso o volemia del paciente | — (los 4000 mL-eq del modelo son un valor de referencia) | — | `NOT_SPECIFIED` |

> **`ABSOLUTE_BLOOD_LOSS_NOT_DIRECTLY_AUTHORED`.** Ninguna de las tres cantidades (mL/min, mL/h, pérdida total) se puede estimar con confianza ≥ 0,80. No se inventa ningún volumen clínico.

## §3 · P3-317 · La escala actual, en tres conceptos que no se mezclan

**A** = sangre entera perdida (`shed_ml = tasa·t`; el repositorio la llama mL-**equivalentes** de sangre modelada, no un caudal medido). **B** = déficit circulante efectivo (`volume_ml`:
lo perdido menos el relleno, más cristaloide y glóbulos). **C** = la coordenada `V` del modelo y su posición en la curva de precarga (`V/escala`): **lo único que lee la presión.**

| caso | min | A · perdido (mL) | A / volemia de referencia | relleno (mL) | B · déficit efectivo (mL-eq) | C · `V/escala` | flujo anterógrado | PAS | Hb (caída) |
|---|---|---|---|---|---|---|---|---|---|
| 57m | 30 | 75 | 1,9 % | 4,2 | 70,8 | −0,085 | 0,911 | 80,2 | 6,69 (−0,01) |
| 57m | 60 | 150 | 3,8 % | 15,7 | 134,3 | −0,161 | 0,825 | 72,6 | 6,67 (−0,03) |
| 57m | 120 | 300 | 7,5 % | 54,8 | 245,2 | −0,294 | 0,658 | 57,9 | 6,60 (−0,10) |
| 57m | 180 | 450 | 11,2 % | 108,0 | 342,0 | −0,410 | 0,493 | 43,3 | 6,51 (−0,19) |
| 72f | 30 | 75 | 1,9 % | 4,2 | 70,8 | −0,085 | 0,911 | 89,3 | 6,39 (−0,01) |
| 72f | 60 | 150 | 3,8 % | 15,7 | 134,3 | −0,161 | 0,825 | 80,9 | 6,37 (−0,03) |
| 72f | 120 | 300 | 7,5 % | 54,8 | 245,2 | −0,294 | 0,658 | 64,5 | 6,31 (−0,09) |
| 72f | 180 | 450 | 11,2 % | 108,0 | 342,0 | −0,410 | 0,493 | 48,3 | 6,22 (−0,18) |

**Consistencia aritmética, no diagnóstico clínico:**

* con el mapa comprometido, el curso sin tratar aceptado alcanza su estado de las 2 h tras perder el **7,5 %** de la volemia de referencia, y el límite de gasto cero del núcleo está a
  **578 mL-eq (14 %)** por debajo de la llegada (minuto 349). La lectura **literal** «150 mL/h» y la severidad del curso sólo son compatibles porque el mapa es así de sensible: son una
  sola cosa (`tasa/escala`), no dos hechos independientes;
* la Hb casi no se mueve (−0,03 g/dL a 60 min): la pérdida es de sangre entera. **La Hb no informa la tasa**;
* **en las unidades que la docencia ya aprobó:** `FD-BLD-04` dice que 1 L de cristaloide isotónico aporta ≈ 150–300 mL tempranos, y una unidad de glóbulos son 300 mL. A 2,5 mL-eq/min,
  **una hora de sangrado son 150 mL-eq = media unidad de glóbulos = lo que aportan 0,5 a 1,0 L de suero**. Ése es el hallazgo del FR-G dicho antes de cualquier mapa de presión.

## §4 · P3-318 · Inversión del curso sin tratar, con el mapa de presión ACTUAL

Reducción analítica (el curso lee `tasa·t`), sondas fijas (los bordes de las envolventes) y bisección 1-D a 10⁻⁴. Sin barrido cartesiano. Dos lecturas del comportamiento, ninguna con
valores de presión como objetivo:

* **`U-OUT`** (envolventes docentes congeladas del gasto sin tratar, por caso): 57m **[2,5497; 3,7234]**, 72f **[1,6894; 2,8038]**, común **[2,5497; 2,8038]**. Son exactamente las de P3-89:
  **siguen vigentes**. La referencia 2,5 queda **fuera, 1,95 % por debajo** del borde común.
* **Ventanas amplias** (lectura operativa de las frases del encargo; **no** es una restricción docente): el estado que el curso aceptado muestra a los 90 min debe alcanzarse entre 60 y
  120 min («deterioro mayor en 1–2 h») → [1,957; 3,575]; el de los 150 min, entre 120 y 180 («grave en 2–3 h») → [2,156; 3,007]. Intersección, igual en los dos casos: **[2,156; 3,007]**.

Testigos, cada uno con su razón (PAS sin tratar de 72f a 60 / 120 / 180 min; FR-G con el núcleo vigente y, a la derecha, con el punto menos protector de la región cerrada):

| Testigo | tasa | `U-OUT` 57m / 72f | PAS 72f sin tratar | perdido a 60 | retenido / perdido | ΔV neto a 60 | % de la caída evitada a 30 / 60 / 70 / 120 | clase | región cerrada (60 min) |
|---|---|---|---|---|---|---|---|---|---|
| `LOWER_72F_U_OUT_EDGE` (testigo bajo: la dirección) | 1,69 | no / sí | 87 / 76 / 67 | 101 | 0,81 | −10 | 97 / 89 / 70 / 34 | `NEAR_STABILIZATION` | 134 % |
| `BROAD_WINDOW_LOWER` | 2,16 | no / sí | 83 / 70 / 56 | 129 | 0,63 | −34 | 80 / 72 / 57 / 28 | `SUBSTANTIAL_PROTECTION` | 104 % |
| **`REFERENCE`** | **2,50** | no / sí | 81 / 64 / 48 | 150 | 0,55 | −52 | 69 / **63** / 50 / 25 | `SUBSTANTIAL_PROTECTION` | 95 % |
| `COMMON_U_OUT_LOWER` | 2,55 | sí / sí | 80 / 64 / 47 | 153 | 0,54 | −55 | 68 / 62 / 49 / 24 | `SUBSTANTIAL_PROTECTION` | 94 % |
| `COMMON_U_OUT_UPPER` (el más rápido admitido para 72f) | 2,80 | sí / sí | 79 / 60 / 41 | 168 | 0,49 | −69 | 62 / **57** / 45 / 22 | `SUBSTANTIAL_PROTECTION` | 89 % |
| `BROAD_WINDOW_UPPER` | 3,01 | sí / no | 77 / 56 / 35 | 180 | 0,45 | −80 | 58 / 53 / 42 / 21 | `SUBSTANTIAL_PROTECTION` | 84 % |
| `HIGH_57M_U_OUT_EDGE` (testigo alto: el más rápido que admite **alguna** envolvente) | 3,72 | sí / no | 71 / 44 / 15 (límite del núcleo: min 211) | 223 | 0,37 | −118 | 47 / 44 / 35 / 18 | `SUBSTANTIAL_PROTECTION` | 70 % |

Todos se mantienen por debajo de la llegada, empeoran de forma monótona y conservan el orden entre casos (57m por debajo de 72f).

**Respuesta con el mapa actual: la tasa sola NO resuelve el FR-G.** Ninguna tasa admitida para 72f baja de **57 %**. Para llegar a la mitad haría falta **3,22 mL/min** (72f sale de `U-OUT`:
PAS 75/53 a 60/120 min) y para un tercio **5,11** (el curso sin tratar de 72f se acaba en el minuto 143). Con un núcleo de la región cerrada: **5,50** (se acaba en el minuto 131) y
**9,20** (minuto 72). Subir la tasa sin tocar el mapa **rompe el curso sin tratar que la docencia aceptó**.

## §5 · P3-319 · Identificabilidad

Tres hechos medidos:

1. **El curso sin tratar lee sólo `tasa/escala`.** Multiplicando tasa y escala por el mismo factor (hasta ×3), la PAS sin tratar de los dos casos no cambia en 240 min:
   diferencia máxima **1,6·10⁻¹³ mmHg**. El intervalo de `U-OUT` en `c = tasa/escala` es el mismo a escala 833 y 1500 (diferencia 2,5·10⁻⁸).
2. **La protección de una infusión lee sólo la tasa, no el mapa.** A tasa fija, el % de la caída evitada a 60 min es igual en seis mapas de presión (escala 600 / 833 / 1500 / 2500; posición
   0,35 / 0,6): 0,62–0,64 a 2,5 mL/min y 0,35–0,38 a 4,5 mL/min. Es `retenido / perdido`, una razón de **mililitros reales**.
3. **Por tanto la dimensión efectiva es:** la evidencia sin tratar identifica **una** coordenada (`c`, más la posición `f`), y **nada** de la tasa absoluta. La escala absoluta sólo la alcanza
   el comportamiento **tratado** en mL reales: la región de retención del cristaloide (FR-G) y la unidad de glóbulos (`FD-BLD-02`).

> **`B · BLEED_RATE_AND_PRESSURE_MAP_REQUIRE_JOINT_REGION`.** No es **A**: la evidencia sin tratar no acota la tasa, sólo `tasa/escala`. No es **C**: la escala absoluta sí es alcanzable, por
> lo tratado. No es **D**: el mapa no vuelve ininterpretable la tasa; sobre la variedad conjunta todo es coherente, y lo que está fuera de las restricciones es el **punto** actual.
> Coincide con P3-89 y P3-95.

**P3-319A · Sin circularidad. Cada evidencia se usa una vez:**

| Evidencia | Se usa para | ¿Dos veces? |
|---|---|---|
| `U-OUT` | `tasa/escala`, y nada más | no |
| aceptación humana de FR-A y FR-D (sin tratar) | **la misma** coordenada: no es independiente de `U-OUT` y **no** se cuenta como segunda confirmación | no |
| juicio humano del FR-G (cualitativo) + retención del cristaloide en mL reales | la tasa **absoluta**, y nada más | no |
| `FD-BLD-02` | **comprobación** de la escala que una tasa implica; no selecciona nada | no |
| aceptación humana de FR-B, FR-C y FR-E (tratados) | no regresión cualitativa; leen la misma coordenada que `FD-BLD-02` | no |

## §6 · P3-320 · Tasa × cristaloide sobre la variedad conjunta

Con `c = 0,003` fijo (el curso sin tratar **exacto** que la persona revisora aceptó) y posición 0,5. Clases declaradas **antes** de clasificar; son una convención descriptiva de este
análisis, no una definición docente ni un objetivo de ajuste: `NEAR_STABILIZATION` ≥ 75 %; `SUBSTANTIAL_PROTECTION` 33–75 %; `MODEST_TRANSIENT_ATTENUATION` 10–33 % y decreciente a 120 min;
`MINIMAL_EFFECT` < 10 %; `WORSE_THAN_EXPECTED` < 0. «Más cerca de lo no tratado» se lee como < 50 %; «sustancialmente más cerca», como ≤ 1/3. **Se informan los dos bordes.**

| Testigo | escala | tasa | perdido a 60 | retenido/perdido (vigente / región) | ΔV neto a 60 | % evitado 30/60/70/120 · vigente | % evitado · región cerrada | mmHg por unidad de glóbulos (57m / 72f) | banda declarada |
|---|---|---|---|---|---|---|---|---|---|
| `REFERENCE` | 833 | 2,50 | 150 | 0,55 / 0,90 | −52 / −7 | 69 / **63** / 50 / 25 | 108 / **95** / 74 / 28 | 26,6 / 29,6 | dentro |
| `FD_BLD_02_EDGE_72F` | 841 | 2,52 | 151 | 0,54 / 0,89 | −54 / −8 | 69 / 62 / 49 / 25 | 107 / 95 / 73 / 27 | 26,4 / 29,4 | dentro |
| borde ½ · núcleo vigente | 1064 | 3,19 | 192 | 0,43 / 0,70 | −90 / −37 | 54 / **50** / 39 / 20 | 90 / 80 / 62 / 23 | 21,6 / 24,1 | dentro |
| `DECLARED_BAND_TOP` | 1500 | 4,50 | 270 | 0,30 / 0,50 | −160 / −107 | 39 / **36** / 28 / 14 | 65 / **58** / 45 / 17 | 16,0 / 17,8 | dentro (borde) |
| borde ⅓ · núcleo vigente | 1618 | 4,85 | 291 | 0,28 / 0,46 | −179 / −126 | 36 / **33** / 26 / 13 | 60 / 54 / 41 / 15 | 14,9 / 16,6 | **fuera** |
| borde ½ · región cerrada | 1750 | 5,25 | 315 | 0,26 / 0,43 | −200 / −147 | 33 / 31 / 24 / 12 | 56 / **50** / 38 / 14 | 13,9 / 15,4 | **fuera** |
| borde ⅓ · región cerrada | 2659 | 7,98 | 479 | 0,17 / 0,28 | −347 / −294 | 22 / 20 / 16 / 8 | 37 / **33** / 26 / 9 | 9,4 / 10,5 | **fuera** |

(Los testigos de borde están medio por ciento más allá del borde que nombran; los bordes exactos son 1059 / 1610 / 1741 / 2646 mL-eq, es decir 3,18 / 4,83 / 5,22 / 7,94 mL/min. El
cristaloide retenido a 60 min es 81,9 mL con el núcleo vigente y 134,6 mL con el punto menos protector de la región cerrada, en todos los testigos: no depende de la tasa.)

**La esquina más favorable de TODOS los dominios declarados** (escala 1500; cada caso en el borde superior de su banda de posición: 57m 0,5 y 72f 0,6; la tasa común más rápida que `U-OUT`
admite en los dos): **6,70 mL/min**, coherente con P2I-2X (6 viable, 7 no). Ahí el FR-G evita **25 %** con el núcleo vigente (`MODEST_TRANSIENT_ATTENUATION`) y **40 %** con la región cerrada
(`SUBSTANTIAL_PROTECTION`; por debajo de la mitad, por encima del tercio). `FD-BLD-02` se cumple en los dos casos (18,1 % y 12,1 % por unidad).

## §7 · P3-321 · Región de desarrollo: conjunta, no un intervalo de tasa

> **`GI_BLEED_RATE_PRESSURE_JOINT_DEVELOPMENT_REGION`** — región de **análisis**, **no aprobada** y **no** un intervalo de tasa. No se define `GI_BLEED_RATE_DEVELOPMENT_REGION` como intervalo
> porque la evidencia sin tratar acota `tasa/escala`: una tasa no significa nada hasta que se nombra su escala (P3-321: «do NOT collapse it»).

| Coordenada | Borde | Fuente | Punto actual |
|---|---|---|---|
| `c = tasa/escala` (posición 0,5, común a los dos casos) | [0,003060; 0,003365] min⁻¹ | `U-OUT`, envolventes docentes congeladas | 0,003000: **fuera**, 1,95 % por debajo |
| escala — borde inferior | ≥ 841,1 mL-eq | `FD-BLD-02`, 72f: una unidad no debe subir el gasto más de 30 % | 833,3: **fuera** (30,2 %) |
| escala — borde superior | 1500 mL-eq | banda `CANDIDATE` declarada de `preload_curve_scale_ml`: **dominio declarado, no evidencia; ABIERTO** | — |
| tasa absoluta implicada | esquina baja 2,57 · borde de la banda [4,59; 5,05] · esquina más favorable 6,70 | `c × escala` | 2,5 |

* **Rationale y evidencia:** restricciones docentes congeladas (`U-OUT`, `FD-BLD-02`), la región de cristaloide cerrada como ancla en mL, y la invariancia medida de §5.
* **El punto actual (2,5; 833,33; 0,5) está fuera, pegado a la esquina BAJA** de la región: ya era sabido para `c` (P3-91 §4.4) y para `FD-BLD-02` en 72f (P3-91 §4.2).
* **Compartida o por caso (P3-321A): una región de familia sirve a los dos casos.** La banda común de `U-OUT` no es vacía ni en la posición comprometida ni en el borde de la banda; el borde
  de escala lo pone 72f y el FR-G sólo se revisó en 72f. Ningún caso declara una tasa, así que **no** se introducen tasas por caso (la política `CASE_OVERRIDES_FAMILY_DEFAULT` queda como está).
* **Confianza (juicio del analista, no estadística):** 0,95 en que la tasa sólo se identifica junto con la escala; 0,90 en que el punto actual está fuera por la esquina baja; **0,80** en
  que una tasa absoluta admisible está claramente por encima de 2,5; **0,5** en cualquier número único para el borde del FR-G (una sola persona revisora, un escenario, un caso, y un límite
  de clase convencional).
* **Incertidumbre:** el propio núcleo del cristaloide está sin decidir (el vigente está fuera de la región cerrada; uno de la región protege más); la posición `f` se dejó en 0,5 salvo en la
  esquina declarada.
* **Falsadores:** (1) un ancla docente de respuesta a la sangre que mantenga la escala ≤ ~1500 mL-eq: entonces un núcleo de la región cerrada deja el FR-G entre 40 % y 58 % y el conflicto
  vuelve a la región de cristaloide; (2) una tasa o volumen verificado en algún caso; (3) una segunda persona revisora que acepte el FR-G actual; (4) evidencia de que la protección de una
  infusión dependa del mapa (medido: no depende).

## §8 · P3-322 · No regresión cualitativa y horizonte largo

Los juicios aceptados **no** son objetivos numéricos. Con `c = 0,003`: FR-A y FR-D son **idénticos** en todos los testigos (por construcción y medido); FR-F no cambia (la parada ocurre
antes de que importen tasa o mapa). El testigo de referencia reproduce las presiones comprometidas de las seis trayectorias revisadas.

| Testigo | tasa / escala | FR-B · PAS a 30 min (revisado 112) | FR-C · PAS a 150 (revisado 92) · % de la caída recuperada | FR-E · PAS a 160 (revisado 109) · % recuperado | FR-G · PAS 60 / 70 · % evitado |
|---|---|---|---|---|---|
| `REFERENCE` | 2,50 / 833 | 112 | 92 (112 %) | 109 (133 %) | 92 / 88 · 63 % |
| `DECLARED_BAND_TOP` | 4,50 / 1500 | 99 | 76 (59 %) | 89 (73 %) | 87 / 84 · 36 % |
| `DECLARED_BAND_TOP` · región cerrada | 4,50 / 1500 | 102 | 80 (72 %) | 92 (83 %) | 91 / 87 · 58 % |
| borde ⅓ · núcleo vigente | 4,85 / 1618 | 98 | 74 (54 %) | 87 (66 %) | 87 / 83 · 33 % |
| borde ⅓ · región cerrada | 7,98 / 2659 | 93 | 68 (33 %) | 77 (37 %) | 87 / 83 · 33 % |

**Cualitativamente, en todos los testigos:** lo no tratado se deteriora de forma progresiva; el FR-B sube por encima de la llegada; el rescate tardío de FR-C y FR-E sube tras el tratamiento.
**Pero las magnitudes de TODOS los cursos tratados se mueven**: con la escala del borde ⅓ de la región cerrada, el FR-E ya no vuelve a superar la llegada (64 → 77, no 109).

**P3-322A · Tratamiento temprano (órdenes del FR-B) hasta 240 min, sangrado continuo y sin control de fuente** (el sangrado es constante en todos los minutos de todas las corridas):

| Testigo | caso | llegada | pico (minuto; alza) | PAS 60 | PAS 120 | PAS 240 | vuelve a estar bajo la llegada |
|---|---|---|---|---|---|---|---|
| `REFERENCE` | 57m | 88 | 127,6 (65; +39,6) | 125,5 | 118,3 | 93,1 | > 240 (minuto 261) |
| `REFERENCE` | 72f | 98 | 142,1 (65; +44,1) | 139,8 | 131,7 | 103,7 | > 240 |
| `DECLARED_BAND_TOP` | 57m | 88 | 107,2 (65; +19,2) | 106,0 | 94,3 | 76,3 | **minuto 145** |
| `DECLARED_BAND_TOP` | 72f | 98 | 119,3 (65; +21,3) | 118,0 | 105,0 | 85,0 | minuto 145 |
| borde ⅓ · núcleo vigente | 57m | 88 | 104,9 (65; +16,9) | 103,9 | 91,7 | 74,0 | minuto 135 |
| borde ⅓ · región cerrada | 57m | 88 | 93,5 (65; +5,5) | 93,4 | 81,1 | 58,5 | **minuto 85** |
| borde ⅓ · región cerrada | 72f | 98 | 104,2 (65; +6,2) | 104,0 | 90,3 | 65,2 | minuto 85 |

Nunca hay meseta: la mejoría siempre se revierte. La limitación docente del FR-B («la reanimación no debe sugerir control definitivo») se cumple **mejor** al crecer la escala: la reversión
pasa de más de 4 h a 2 h 25 min en el borde de la banda. **El costo es el mismo mecanismo:** dos unidades de glóbulos y 1 L pasan de subir 40 mmHg a subir 19, y a 5,5 en el borde ⅓ de la
región cerrada.

## §9 · P3-323 y P3-324 · Candidato V2 y decisión de Enmienda 3

**`FR-G_V2_CANDIDATE`: no se generó.** P3-323 lo permite sólo si una región de tasa defendible **sola** resuelve el conflicto. No lo hace: la tasa no puede moverse sin la escala de presión,
y moverlas juntas cambia todas las trayectorias tratadas. Un V2 hoy sería elegir un punto por la docencia.

> **`B · JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED`. La Enmienda 3 no se abre: queda sin resolver.**

Razón exacta, en una frase: **el efecto del suero y el de la sangre son volumen en los mismos mililitros, así que la misma escala que vuelve «modesto» 1 L lento vuelve débil dos unidades
de glóbulos.** La tabla que decide (todo sobre el curso sin tratar aceptado):

| Si una unidad de glóbulos sube la PAS de 72f en la llegada… | escala · tasa | FR-G con el núcleo vigente | FR-G con la región cerrada | FR-B (57m): alza máxima · bajo la llegada | FR-E: PAS a 160 |
|---|---|---|---|---|---|
| ≈ +30 mmHg (hoy; **viola `FD-BLD-02`** en 72f) | 833 · 2,50 | 63 % | 95 % | +40 · > 4 h | 109 |
| ≈ +24 mmHg | 1064 · 3,19 | 50 % | 80 % | — | — |
| ≈ +18 mmHg (borde de la banda declarada) | 1500 · 4,50 | 36 % | 58 % | +19 · 2 h 25 | 89–92 |
| ≈ +17 mmHg | 1618 · 4,85 | 33 % | 54 % | +17 · 2 h 15 | 87 |
| ≈ +15 mmHg | 1750 · 5,25 | 31 % | 50 % | — | — |
| ≈ +10,5 mmHg | 2659 · 7,98 | 20 % | 33 % | +5,5 · 1 h 25 | 77 |

* No es **A**: con el mapa actual ninguna tasa admitida para 72f baja el FR-G de 57 %.
* No es **C** todavía: el conflicto no «persiste tras una escala defendible» porque la escala defendible **no está decidida**. **C pasa a ser el veredicto** si la docencia ancla la respuesta
  a la sangre en una escala donde un núcleo de la región cerrada sigue protegiendo de más (en todos los dominios declarados: 40–58 %). Entonces sí quedaría justificada una Enmienda 3 sobre
  la retención en infusión lenta.
* No es **D**: la escala absoluta es identificable por lo tratado. No es **E**: no se halló ningún defecto estructural (balance de masa, mapa y núcleo se comportan como declaran).

**Nota de implementación (no es parte del veredicto):** la escala es un campo del perfil, pero la tasa se calcula **dentro** de `clinical_core/legacy_adapter.py` (0,003 × 833,33). Aplicar
cualquier punto conjunto distinto exige, además de una instantánea de presión nueva, un sucesor certificado del núcleo o que la tasa pase a venir de la instantánea. Nada de eso se hizo.

## §10 · P3-325 · Punto de control y la pregunta docente que sigue

`docs/revision/PHASE3_BLEED_RATE_SCALE_CHECKPOINT.json`. Global: **`B · JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED`**.

**La siguiente pregunta docente (una sola, en la capa del mapa, sin mmHg del FR-G y sin curvas heredadas):**

> *En estos dos pacientes, en la llegada y con el sangrado controlado, ¿cuánto debe subir la presión sistólica **una unidad de glóbulos rojos**?* (hoy: +27 mmHg en 57m y +30 en 72f).

Es el ancla **M1** que P3-95 ya había diseñado, dicha en la forma que una persona docente reconoce. Con `U-OUT` fijando `tasa/escala`, la respuesta fija la escala, la tasa absoluta y —por la
tabla de §9— dónde cae el FR-G con cada núcleo de cristaloide. Si la respuesta deja un núcleo de la región cerrada por encima de lo que la docencia considera «modesto», el veredicto pasa a
**C** y la conversación vuelve a la retención del cristaloide; si no, basta una calibración conjunta y una **nueva revisión ciega de todas las trayectorias tratadas** (FR-B, FR-C, FR-E y FR-G).

## §11 · Límites

* `MODEL_ANALYSIS`: explica el modelo; no lo valida clínicamente y no decide ninguna verdad clínica.
* Una sola persona revisora, un escenario de infusión lenta, un caso. El juicio del FR-G es evidencia **cualitativa**, no un objetivo numérico; los límites de clase (½, ⅓) son convención.
* Las ventanas amplias de §4 son una lectura operativa de este análisis, no una restricción docente.
* La posición de llegada `f` se dejó en la comprometida (0,5), salvo en la esquina declarada (72f a 0,6). La banda de `c` depende de `f` (P3-90 §3.4).
* Los testigos fuera de la banda declarada de la escala (> 1500 mL-eq) son exploratorios: están dentro de las tasas que el repositorio ya había explorado (hasta 10 mL/min en P2I-2X), pero
  fuera del dominio `CANDIDATE` de la escala.
* El arnés reproduce las presiones comprometidas redondeadas de las seis trayectorias con serie; no sustituye a la página real.
* El legado no se usó para elegir nada: sigue siendo comparador no autoritativo.
