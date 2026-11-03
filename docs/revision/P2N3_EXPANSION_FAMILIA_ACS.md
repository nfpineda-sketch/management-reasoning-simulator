# P2N-3 · Expansión a la familia ACS: ¿generalizan los escritores de P2N-2?

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `b1d932a` (P2N-2 cerrado y publicado) · **Fecha:** 2026-11-03

Sólo lectura y sondas en sombra. No hay código nuevo, ningún valor se aprueba y nada llega al tiempo de ejecución.

Se aplicaron sin cambios a tres casos ACS más las reglas de mapeo de P2N-2, sus escritores de familia y el perfil de
referencia común, cambiando sólo el caso que se lee del banco. No se ajustó ningún valor. Las sondas están en el
apéndice.

## Resumen

**Veredicto: `ACS_FAMILY_GENERALIZATION_PARTIAL`.** Los escritores generalizan; el mapeo de llegada necesita tres reglas
nuevas, que son decisiones docentes, y el infarto con VD expone un hueco común de un solo ventrículo.

**Clasificación: `ACS_FAMILY_WRITERS_GENERALIZE_WITH_CASE_MAPPINGS`**, con un `COMMON_CORE_GAP_EXPOSED` declarado
(infarto con VD).

- **Los escritores de P2N-2 se reutilizan sin variantes.**
  - La bomba isquémica sobre P vale en los dos casos oclusivos.
  - La congestión sobre L puede encenderse o apagarse según la evidencia autorizada.
  - La reperfusión sigue sobre P.
  - El caso no oclusivo no lleva escritor.
  - No hace falta ningún escritor de familia nuevo.
- **Las reglas de llegada de GI no se trasladan.** Hacen falta tres reglas de mapeo que la verdad autorizada no fija
  sola:
  1. el punto de aporte de llegada cuando la perfusión está preservada;
  2. el exceso de lactato cuando el lactato cae dentro de la línea basal;
  3. la FC intrínseca fuera de la banda de reposo (bradicardia de 58 y taquicardia de 102 sin hipoperfusión).
- **La FC de llegada falla en el punto medio de la banda en los cuatro casos ACS:** 91,8 / 112, 70,6 / 58, 88,7 / 96 y
  88,7 / 102. Es una decisión de familia, no de un caso. Amplía la M5 de P2N-2.
- **El infarto inferior con VD expone un hueco común.** Un solo P y una sola precarga no separan el llenado de la
  aurícula derecha (lo que muestra la VCI) del llenado del VI. La dependencia de precarga se puede expresar bajando la
  precarga de llegada (+0,26 de gasto con 1000 mL frente a +0,09), pero eso contradice la VCI autorizada. No impide
  representar la llegada ni el curso sin tratar; sí la respuesta al tratamiento específica del VD (fluidos, nitratos).
- **La FR de llegada** queda de 3 a 5 rpm por debajo con la FR intrínseca media de P2K-2 (16). Con la candidata
  superior (20) da 23-25 frente a 22-24. El pH y la PaCO2 levemente alcalóticos autorizados (7,43 / 35) no se
  reproducen (7,40 / 37): un impulso no metabólico, como el dolor o la ansiedad, no existe en el núcleo
  (EXPECTED_RESPIRATORY_EXTENSION).

## A. Inventario

El banco agrupa seis casos en la familia `acs`. `pulmonary_edema` y `bradycardia` son familias aparte y no entran.
Sólo la llegada está autorizada (observables, exploraciones, examen y `engine.coronary`); no hay observaciones
posteriores. Todo lo que no es de llegada es MODEL_DERIVED.

| Caso | PA | FC / ritmo | SpO2 / FR | Lactato | Perfusión | ECG | POCUS VI | Pulmón | Oclusión |
|---|---|---|---|---|---|---|---|---|---|
| acs_70f_left_main (P2N-2) | 104/66 | 112 taquicardia sinusal | 94 / 26 | 3,1 | levemente alterada, fría, LLC 3 | descenso difuso del ST + aVR | globalmente reducida leve | líneas B basales | activa, tronco |
| acs_54m_inferior | 100/64 | 58 bradicardia sinusal | 96 / 22 | 2,1 | levemente alterada, fría, LLC 3 | ascenso inferior | hipocinesia inferior | líneas A | OMI inferior, compromiso de VD |
| acs_52m_de_winter | 128/78 | 96 sinusal | 95 / 24 | 2,2 | preservada, caliente, LLC 2 | de Winter | acinesia anterior y apical | líneas A | activa, anterior |
| acs_61m_posterior | 132/80 | 88 sinusal | 96 / 20 | 1,9 | preservada | infarto posterior | hipocinesia posterior | líneas A | activa, posterior |
| acs_66f_nonst | 146/86 | 102 taquicardia sinusal | 95 / 24 | 1,6 | preservada, caliente | descenso del ST | hipocinesia inferolateral leve | líneas A | no oclusivo (omi False) |
| acs_48m_wellens | 138/84 | 76 sinusal | 97 / 18 | 1,4 | preservada | Wellens | normal | líneas A | sin oclusión activa ni daño |

Ningún caso tiene betabloqueante autorizado (losartán, atorvastatina, metformina).

## B. Selección (escrita antes de simular)

Se escogieron tres casos que maximizan la diversidad frente al tronco: bomba alterada de otro tipo, precarga, ritmo,
hipotensión, perfusión preservada, no oclusión e hipertensión.

1. **acs_54m_inferior.**
   - Bomba alterada de otro tipo: inferior, con VD.
   - PA límite (100/64), sin congestión.
   - **Bradicardia sinusal de 58**, bajo la banda de reposo de GI.
   - Prueba la FC bajo la banda, la dependencia de precarga del VD con un solo P y la falla de bomba sin L.
2. **acs_52m_de_winter.**
   - Oclusión anterior proximal activa, con la pared anterior y el ápex acinéticos.
   - Llegada **preservada**.
   - Prueba el escritor isquémico desde una llegada compensada, el mapeo de aporte con perfusión preservada y la
     reperfusión.
3. **acs_66f_nonst.**
   - **No oclusivo e hipertenso**: PAM 106, por encima del punto de ajuste barorreflejo de 90.
   - Taquicardia de 102 con perfusión preservada.
   - Prueba un caso sin escritor de bomba, la FC sin hipoperfusión y la hipertensión de llegada.

No se escogieron dos casos:
- acs_61m_posterior: es mecánicamente el de Winter con menos territorio;
- acs_48m_wellens: sin oclusión activa ni daño, no añade mecanismo al NSTE.

## C. Prueba de reutilización

### C1. Llegada con las reglas de P2N-2 (punto medio de cada banda)

| Caso | PA | PAM | FC | SpO2 | FR | Lactato | pH / PaCO2 | Conciencia | Déficit / impulso |
|---|---|---|---|---|---|---|---|---|---|
| 54m inferior: autorizado | 100/64 | 76 | 58 | 96 | 22 | 2,1 | 7,43 / 35 | alerta | |
| 54m inferior: núcleo | 100/64 | 76,0 | **70,6** | 96 | 19,0 | 2,1 | 7,40 / 37,0 | alerta | 0,15 / 0,51 |
| 52m de Winter: autorizado | 128/78 | 94,7 | 96 | 95 | 24 | 2,2 | 7,39 / 36 | alerta | |
| 52m de Winter: núcleo | 128/78 | 94,7 | 88,7 | 95 | 21,2 | 2,2 | 7,40 / 34,9 | alerta | 0,15 / 0,35 |
| 66f NSTE: autorizado | 146/86 | 106 | 102 | 95 | 24 | 1,6 | 7,43 / 35 | alerta | |
| 66f NSTE: núcleo | 146/86 | 106,0 | 88,7 | 95 | 19,0 | 1,6 | 7,40 / 37,0 | alerta | 0,15 / 0,35 |

PA, PAM, SpO2, lactato y conciencia son exactos por construcción: son anclas autorizadas. Lo que discrimina es la FC,
la FR y los gases.

### C2. Las tres reglas de llegada que no se trasladan

- **Aporte con perfusión preservada.** La banda de GI (0,6-1,0, punto medio 0,85) da un déficit de llegada de 0,15 en
  los tres casos. En de Winter y NSTE eso contradice la perfusión preservada autorizada (caliente, LLC 2): sin ningún
  escritor, D sube de 20 a 38 y la FC de 88,7 a 93,2 en 120 min. Con el punto de adecuación de la misma banda (1,0;
  déficit 0) y D de llegada 0, la llegada es un estado estacionario. Sólo el lactato vuelve a la línea basal (2,2 →
  1,44 y 1,6 → 1,22), y la FC autorizada exige una intrínseca igual a la FC: 96, dentro de la banda, y 102, fuera de
  ella. Es una regla nueva: que la perfusión autorizada elija el punto de la banda (CASE_MAPPING_ONLY, a confirmar).
- **Exceso de lactato con lactato dentro de la línea basal.** En el NSTE (1,6) la regla de GI da una banda de −0,4 a
  0,8. El ancla rechaza el punto inferior («the clearable arrival lactate is between 0 and the arrival lactate»). La
  regla necesita su borde: exceso de 0 a lactato − 0,8 (CASE_MAPPING_ONLY).
- **FC intrínseca fuera de la banda de reposo.**
  - 54m: la banda queda vacía (60 > 58); la intrínseca que da 58 con el perfil de referencia es 45,4. Bradicardia
    vagal o nodal del infarto inferior.
  - NSTE: con perfusión preservada, la intrínseca debe ser 102, por encima de 100. Taquicardia por dolor o ansiedad,
    sin entrada simpática no hemodinámica en el núcleo.
  - En ambos, invertir la FC autorizada a través de una ganancia común incierta es una decisión metodológica. P2N-2 no
    invirtió nada.

### C3. Curso sin tratar (escritores de P2N-2, pérdida de referencia del 10 % por hora)

| Caso, configuración | P | PAM | FC | Déficit | D | Lactato | L | (120 min) |
|---|---|---|---|---|---|---|---|---|
| 54m, bomba + congestión | 0,80 | 64,4 | 85,3 | 0,337 | 49,2 | 2,06 | 0,508 | |
| 54m, sólo bomba (sin líneas B, VD) | 0,80 | 64,4 | 85,3 | 0,337 | 49,2 | 2,06 | 0 | |
| 54m, sin escritores | 1,00 | 76,0 | 75,0 | 0,15 | 38,0 | 1,97 | 0 | |
| 54m, intrínseca 45,4, sólo bomba | 0,80 | 64,4 | 72,8 | 0,337 | 49,2 | 2,06 | 0 | |
| de Winter, bomba + congestión | 0,80 | 80,2 | 103,0 | 0,337 | 49,2 | 2,09 | 0,508 | |
| de Winter, preservado (déficit 0, D 0) + escritores | 0,80 | 81,5 | 91,4 | 0,226 | 13,6 | 1,55 | 0,508 | |
| NSTE, sin escritor (no oclusivo) | 1,00 | 106,0 | 93,2 | 0,15 | 38,0 | 1,79 | 0 | |
| NSTE, escritores mal aplicados | 0,80 | 89,8 | 100,5 | 0,337 | 49,2 | 1,87 | 0,508 | |

- La trayectoria de P es la misma en todos los casos, porque el escritor no lee el caso. Lo demás depende de la llegada
  de cada caso y sigue por la fisiología común.
- Las direcciones son las de P2N-2: P, Q, PAM y aporte bajan; déficit, D y FC suben.
- El escritor de congestión añade L en proporción a 1 − P. En el infarto con VD y líneas A eso sería clínicamente
  impropio; apagarlo es configuración del escritor existente. La evolución de L no está autorizada en ningún caso
  (INSUFFICIENT_AUTHORED_TRUTH).
- Reperfusión a los 60 min, recuperación declarada 0,5: P 0,944 a los 120 min en los dos oclusivos.
  - 54m: PAM 73,0 y FC 78,8;
  - de Winter: PAM 90,9 y FC 96,1.

### C4. Fluidos y dependencia de precarga (1000 mL en 30 min, lectura a los 60 min)

| Caso | Bomba de llegada, precarga neutra | Bomba 0,7, precarga neutra | Precarga de llegada baja (0,25) |
|---|---|---|---|
| 54m inferior | +0,086 gasto, +4,3 PAM | +0,046, +3,2 | +0,259, +13,0 |
| de Winter | +0,086, +5,4 | +0,046, +4,0 | |
| NSTE | +0,086, +6,0 | +0,046, +4,5 | |

- Ningún caso congestiona con volumen: L queda en 0 y la posición de precarga se mantiene bajo la rodilla. Es la M4 de
  P2N-2.
- La dependencia de precarga del VD sólo aparece si la precarga de llegada se mapea baja, y la VCI de 1,8 cm con
  colapso del 50 % no lo apoya: el núcleo tiene una sola precarga.

### C5. FR con las candidatas de FR intrínseca de P2K-2 (12 / 16 / 20)

| Caso | 12 | 16 | 20 | Autorizada |
|---|---|---|---|---|
| 54m inferior | 15,0 | 19,0 | 23,0 | 22 |
| de Winter | 17,2 | 21,2 | 25,2 | 24 |
| NSTE | 15,0 | 19,0 | 23,0 | 24 |

El pH y la PaCO2 no cambian con la FR intrínseca (7,40 / 37,0 en 54m y NSTE, frente a 7,43 / 35).

## D. Clasificación de cada brecha

| Brecha | Caso | Clase |
|---|---|---|
| punto de aporte con perfusión preservada | de Winter, NSTE | CASE_MAPPING_ONLY (regla nueva, decisión docente) |
| borde del exceso de lactato dentro de la línea basal | NSTE | CASE_MAPPING_ONLY |
| FC intrínseca bajo la banda (bradicardia vagal o nodal) | 54m | CASE_MAPPING_ONLY (regla nueva; la evolución, como un bloqueo AV, es INSUFFICIENT_AUTHORED_TRUTH) |
| FC intrínseca sobre la banda sin hipoperfusión | NSTE | CASE_MAPPING_ONLY, o un impulso simpático no hemodinámico común (decisión docente) |
| FC de llegada en el punto medio de la banda | los cuatro | decisión de familia (amplía la M5 de P2N-2) |
| escritor de bomba isquémica | 54m, de Winter | EXISTING_FAMILY_WRITER_REUSABLE |
| escritor de congestión, encendido o apagado | 54m (apagado), de Winter (encendido) | EXISTING_FAMILY_WRITER_REUSABLE (configuración); su evolución es INSUFFICIENT_AUTHORED_TRUTH |
| sin escritor de bomba en un no oclusivo | NSTE | EXISTING_FAMILY_WRITER_REUSABLE (configuración por `omi` y `active_occlusion`) |
| reperfusión | 54m, de Winter | EXISTING_FAMILY_WRITER_REUSABLE |
| interdependencia VD / VI y precarga separada | 54m | COMMON_CORE_STRUCTURAL_GAP |
| acinesia regional sin efecto causal de llegada | de Winter | POSSIBLE_COMMON_CORE_GAP (la M4 de P2N-2) |
| FR, pH y PaCO2 por impulso no metabólico | los tres | EXPECTED_RESPIRATORY_EXTENSION |

## E. Clasificación de la generalización

**`ACS_FAMILY_WRITERS_GENERALIZE_WITH_CASE_MAPPINGS`.** Ningún caso pidió un escritor de familia nuevo. Todo lo que
falta en la llegada es mapeo de caso, pero con reglas que la docencia debe fijar.

Queda declarado, aparte, un `COMMON_CORE_GAP_EXPOSED`: el infarto con VD necesita separar el llenado de las dos
cámaras para la respuesta al tratamiento.

## F. Implementación

No hubo ninguna. Los mapeos de caso están autorizados si salen de la verdad autorizada, pero los de C2 exigen elegir
una regla:
- el punto de la banda según la perfusión;
- invertir la FC a través de una ganancia común incierta;
- el borde del lactato.

Elegir una regla es metodología, y aplicar sólo el borde del lactato no basta para cerrar ningún caso. No se tocó el
núcleo común, GI, el colapso ni el tiempo de ejecución.

## G. Colapso, legado y fronteras

- **Colapso:** no se evaluó más allá de P2N-2; sólo estructural. Siguen M1 (REQUIRED_BEFORE_ACTIVE_FAMILY_COLLAPSE) y
  M2 (REQUIRED_BEFORE_RUNTIME_TRACE_INTEGRATION).
- **Legado:** no se leyó ni se usó.
- **Fronteras:** las sondas usan los escritores congelados de P2N-2, que sólo escriben P y L.

## H. Veredicto

**`ACS_FAMILY_GENERALIZATION_PARTIAL`.** Los escritores de familia generalizan. El mapeo de llegada necesita tres reglas
docentes, y el infarto con VD expone un hueco común de un solo ventrículo, que no bloquea la llegada ni el curso sin
tratar.

## I. Decisiones pedidas a la docencia

1. **Punto de aporte de llegada según la perfusión autorizada.** Preservada: punto de adecuación, déficit 0 y D de
   llegada 0. Alterada: punto medio. Otra opción es otra regla.
2. **FC de llegada de la familia.** Opciones:
   - mapear la intrínseca por inversión desde la FC autorizada con el perfil de referencia (54m 45,4; NSTE 102; tronco
     ≈100);
   - mantener el punto medio y declarar la brecha;
   - revisar las ganancias simpáticas comunes, o añadir una entrada simpática no hemodinámica (dolor o ansiedad) al
     núcleo.

   Nunca un residual de SCA.
3. **Borde de la banda de exceso de lactato:** el exceso queda entre 0 y lactato − 0,8 cuando el lactato está dentro
   de la línea basal.
4. **Configuración del escritor de congestión** según la evidencia autorizada: apagado sin líneas B ni congestión, o
   con compromiso de VD.
5. **Interdependencia VD / VI** (COMMON_CORE_STRUCTURAL_GAP): si el núcleo debe separar el llenado de la AD del llenado
   del VI antes de un despliegue que enseñe el manejo del infarto con VD. Las alternativas son un segundo estado de
   llenado o un mapeo de observación de la VCI.
6. **Impulso respiratorio no metabólico** (FR, pH y PaCO2 de llegada): va a la extensión respiratoria.

## Apéndice: sondas reproducibles

Se ejecutan desde la raíz del repositorio con Python 3.11. Leen el banco y el núcleo, y no escriben nada.

```python
"""P2N-3 reuse probe (scratchpad, read-only to the repo): the P2N-2 mapping rules, writers and common reference,
applied unchanged to three more ACS cases. Nothing is tuned; every gap is reported."""
import sys, json
sys.path.insert(0, ".")
from dataclasses import replace
from clinical_core import acs_reference as ar, acs_migration as an, derived as dv
from clinical_core.state import CoreInvariantError

CASES = ("acs_54m_inferior", "acs_52m_de_winter", "acs_66f_nonst")
KEYS = ("P", "output_rel", "map", "sbp", "dbp", "hr", "deficit", "D", "lactate", "L", "T", "spo2", "rr", "ph", "paco2",
        "drive", "consciousness_level")

def use(case):
    ar.CASE = case
    ar.bank_case.cache_clear()

def short(r):
    return {k: (round(r[k], 3) if isinstance(r[k], float) else r[k]) for k in KEYS if k in r}

def hr_for(intrinsic, p):
    a = ar.anchors(intrinsic_sinus_rate=intrinsic)
    return an.row(dv.arrival_state(a, p), a, p)["hr"]

def solve_intrinsic(target, p, lo=1.0, hi=None):
    hi = target if hi is None else hi
    if hr_for(hi, p) < target: return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if hr_for(mid, p) < target: lo = mid
        else: hi = mid
    return (lo + hi) / 2

out = {}
p = ar.common_profile()
for case in CASES:
    use(case)
    t = ar.truth()
    res = {"truth": {k: t[k] for k in ("sbp", "dbp", "hr", "rhythm", "spo2", "respiratory_rate", "lactate_mmol_l",
                                         "abg_ph", "abg_paco2", "abg_hco3", "mental_status", "coronary")}}
    hist = ar.bank_case().get("history", {})
    res["medications"] = json.dumps(hist.get("medications", hist), default=str)[:300] if isinstance(hist, dict) else str(hist)[:300]
    b = ar.bands()
    res["bands"] = {k: (v.lower, v.midpoint, v.upper) for k, v in b.items()}
    try:
        a = ar.anchors()
        s0 = dv.arrival_state(a, p)
        r0 = an.row(s0, a, p)
        res["arrival_mid"] = short(r0)
        res["arrival_drive_terms"] = {"deficit": round(r0["deficit"], 3), "drive": round(r0["drive"], 3)}
        # HR: intrinsic alone across its band, and the intrinsic that reproduces the authored HR
        ib = b["intrinsic_sinus_rate"]
        res["hr_intrinsic_band"] = {pt: (round(hr_for(getattr(ib, pt), p), 1) if getattr(ib, pt) <= float(t["hr"]) else "EMPTY: point above the observed HR") for pt in ("lower", "midpoint", "upper")}
        x = solve_intrinsic(float(t["hr"]), p); res["intrinsic_for_authored_hr"] = None if x is None else round(x, 1)
        # delivery band: arrival deficit at its points
        db = b["arrival_delivery_ratio"]
        res["deficit_over_delivery_band"] = {pt: round(an.row(dv.arrival_state(ar.anchors(arrival_delivery_ratio=getattr(db, pt)), p), ar.anchors(arrival_delivery_ratio=getattr(db, pt)), p)["deficit"], 3) for pt in ("lower", "midpoint", "upper")}
        # untreated: writers per the P2N-2 configuration (occlusion -> pump + congestion writers); none for non-occlusive
        occl = bool(t["coronary"].get("omi")) and t["coronary"].get("active_occlusion", True)
        res["occlusion_reading"] = occl
        configs = {"no_writers": ()}
        if occl:
            configs["p2n2_writers"] = an.writers()
            configs["pump_only"] = an.writers()[:1]
            configs["p2n2_writers_reperfusion60"] = an.writers(reperfusion=an.REPERFUSION_MINUTE)
        else:
            configs["p2n2_writers_if_misapplied"] = an.writers()
        res["courses"] = {}
        for name, items in configs.items():
            st, _ = an.course(items, an.HORIZON, a, p)
            res["courses"][name] = {"60": short(an.row(st[60], a, p)), "120": short(an.row(st[-1], a, p))}
        # fluid at arrival (P=1) and at a weak pump 0.7, 1000 mL / 30 min, read at 60
        fl = {}
        for label, P in (("arrival_pump", 1.0), ("weak_pump_0.7", 0.7)):
            s = s0.evolve(P=P) if P != 1.0 else s0
            dry, _ = an.course((), 60, a, p, s); wet, _ = an.course((an._bag(),), 60, a, p, s)
            rd, rw = an.row(dry[-1], a, p), an.row(wet[-1], a, p)
            fl[label] = {"output_gain": round(rw["output_rel"] - rd["output_rel"], 3), "map_gain": round(rw["map"] - rd["map"], 1),
                         "L": round(wet[-1].L, 4), "position": round(dv.preload_position(wet[-1], a, p), 3)}
        res["fluid"] = fl
    except (CoreInvariantError, ValueError) as exc:
        res["error"] = f"{type(exc).__name__}: {exc}"
    out[case] = res
print(json.dumps(out, indent=1, default=str))
```

```python
"""P2N-3 probe 2 (scratchpad): the five questions the first probe left open. Sparse, no sweeps, nothing tuned."""
import sys, json
sys.path.insert(0, ".")
from clinical_core import acs_reference as ar, acs_migration as an, derived as dv
from clinical_core.state import CoreInvariantError
p = ar.common_profile()
K = ("P", "map", "hr", "deficit", "D", "lactate", "L", "rr", "ph", "paco2", "drive")
def use(c): ar.CASE = c; ar.bank_case.cache_clear()
def sh(r): return {k: round(r[k], 3) for k in K}
def course(items, a, minutes=an.HORIZON, start=None):
    st, _ = an.course(items, minutes, a, p, start); return st
out = {}
# (i) preserved perfusion read as the GI band's adequacy point (deficit 0) and arrival D at its lower point (0)
for c in ("acs_52m_de_winter", "acs_66f_nonst"):
    use(c); b = ar.bands()
    a = ar.anchors(arrival_delivery_ratio=b["arrival_delivery_ratio"].upper, arrival_oxygen_debt=0.0)
    s = dv.arrival_state(a, p); r0 = an.row(s, a, p)
    bare = course((), a); res = {"arrival": sh(r0), "no_writers_120": sh(an.row(bare[-1], a, p))}
    if c == "acs_52m_de_winter":
        res["p2n2_writers_120"] = sh(an.row(course(an.writers(), a)[-1], a, p))
    # intrinsic that reproduces the authored HR under this mapping
    lo, hi = 1.0, float(ar.truth()["hr"])
    f = lambda x: an.row(dv.arrival_state(ar.anchors(arrival_delivery_ratio=b["arrival_delivery_ratio"].upper, arrival_oxygen_debt=0.0, intrinsic_sinus_rate=x), p), a, p)["hr"]
    if f(hi) >= hi:
        for _ in range(60):
            m = (lo + hi) / 2; lo, hi = (m, hi) if f(m) < float(ar.truth()["hr"]) else (lo, m)
        res["intrinsic_for_authored_hr"] = round((lo + hi) / 2, 1)
    else:
        res["intrinsic_for_authored_hr"] = "not reachable at or below the observed HR"
    out[c] = res
# (ii) 54m with the intrinsic rate that reproduces 58 at the band-midpoint mapping (45.4): the untreated HR course
use("acs_54m_inferior")
a = ar.anchors(intrinsic_sinus_rate=45.4)
r0 = an.row(dv.arrival_state(a, p), a, p)
out["acs_54m_inferior"] = {"arrival_intrinsic_45.4": sh(r0),
                           "pump_only_60": sh(an.row(course(an.writers()[:1], a, 60)[-1], a, p)),
                           "pump_only_120": sh(an.row(course(an.writers()[:1], a)[-1], a, p))}
# (v) RV preload dependence: a low arrival preload (0.25, the P2N-2 preload-deficiency arm) vs neutral, 1000 mL
for label, frac in (("neutral", None), ("low_0.25", 0.25)):
    aa = a if frac is None else ar.anchors(intrinsic_sinus_rate=45.4, preload_fraction=frac)
    s = dv.arrival_state(aa, p)
    dry, wet = course((), aa, 60, s), course((an._bag(),), aa, 60, s)
    out["acs_54m_inferior"][f"fluid_{label}"] = {
        "output_gain": round(an.row(wet[-1], aa, p)["output_rel"] - an.row(dry[-1], aa, p)["output_rel"], 3),
        "map_gain": round(an.row(wet[-1], aa, p)["map"] - an.row(dry[-1], aa, p)["map"], 1),
        "arrival_position": round(dv.preload_position(s, aa, p), 3), "arrival_map": round(an.row(s, aa, p)["map"], 1)}
# (iii) NSTE lactate excess band: the GI rule's lower point
use("acs_66f_nonst")
try:
    ar.anchors("lower"); out["acs_66f_nonst"]["lactate_lower_point"] = "accepted"
except (CoreInvariantError, ValueError) as exc:
    out["acs_66f_nonst"]["lactate_lower_point"] = f"refused: {exc}"
out["acs_66f_nonst"]["lactate_band"] = vars(ar.bands()["arrival_lactate_excess"])["lower"]
# (iv) RR: the P2K-2 intrinsic RR candidates 12 / 16 / 20 at the three arrivals (band-midpoint mapping)
for c in ("acs_54m_inferior", "acs_52m_de_winter", "acs_66f_nonst"):
    use(c); rr = {}
    for x in (12.0, 16.0, 20.0):
        a = ar.anchors() if c != "acs_54m_inferior" else ar.anchors(intrinsic_sinus_rate=45.4)
        from dataclasses import replace
        a = replace(a, intrinsic_respiratory_rate=x)
        r = an.row(dv.arrival_state(a, p), a, p); rr[str(x)] = (round(r["rr"], 1), round(r["ph"], 3), round(r["paco2"], 1))
    out[c]["rr_by_intrinsic_rr"] = rr; out[c]["authored_rr_ph_paco2"] = (ar.truth()["respiratory_rate"], ar.truth()["abg_ph"], ar.truth()["abg_paco2"])
print(json.dumps(out, indent=1, default=str))
```
