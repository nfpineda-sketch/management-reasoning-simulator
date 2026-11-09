"""Región factible del bloque de volumen (cristaloide), en forma cerrada — P3-76 y P3-77.

Herramienta de ANÁLISIS. No importa `clinical_core` ni el registro de autoridad, no toca fisiología, no
aprueba ningún parámetro y no decide nada clínico. Vive fuera del conjunto congelado de la Fase 2.

Qué hace, y qué no:

- da la forma cerrada EXACTA de la fracción retenida que leen FD-BLD-04 y FD-BLD-05, verificada contra el
  evaluador congelado a 1,1·10⁻¹⁶ (`test_blood_volume_region.py`);
- resuelve en forma cerrada el intervalo de `e` admisible para cada (s, τ), y dice qué restricción liga cada
  borde;
- transforma entre parámetros (e, s, τ) y comportamiento (Rpico, R30, R120), en los dos sentidos;
- **no** trae las envolventes docentes ni el techo de FD-BLD-06 como valores por omisión: hay que pasarlos.
  Quien llama declara de dónde salen. Así nadie obtiene una respuesta sin nombrar su evidencia.

FD-BLD-06 **no** se calcula aquí: su lectura es la dilución de Hb, que depende además del volumen de llegada
y, débilmente, del sangrado y del relleno, y no es analítica porque el cristaloide apaga el relleno. Lo que sí
cabe aquí es su CONSECUENCIA medida: el pico de dilución es función de Rpico solo (dispersión 0,01 % a Rpico
constante), así que FD-BLD-06 se reduce a un techo sobre Rpico, que se pasa como argumento.
"""
from __future__ import annotations

import math

#: Minutos que tarda la bolsa en entrar, según `blood_constraints.IMPLEMENTATION["crystalloid"]` (P2I-2U).
INFUSION_MINUTES = 20

EMPTY = "EMPTY"
DOMAIN_EDGE = "DOMAIN_EDGE"


def decay(tau_min: float) -> float:
    """λ = exp(−1/τ), el factor de fuga por minuto que usa `interventions.fluids`."""
    if tau_min <= 0.0:
        raise ValueError("tau_min debe ser > 0")
    return math.exp(-1.0 / tau_min)


def smearing(tau_min: float, *, minutes: int = INFUSION_MINUTES) -> float:
    """C(τ): cuánto del compartimento transitorio sobrevive al final de una infusión de `minutes`.

    C = λ(1 − λ^minutes) / (minutes · (1 − λ)). Está en (0, 1) y crece con τ: es la razón por la que el pico
    retenido vale 0,83·e y no `e` cuando τ = 30.
    """
    lam = decay(tau_min)
    return lam * (1.0 - lam ** minutes) / (minutes * (1.0 - lam))


def _share(s: float) -> float:
    if not 0.0 <= s <= 1.0:
        raise ValueError("crystalloid_transient_share debe estar en [0, 1]")
    return s


def coefficient(s: float, tau_min: float, t_min: float, *, minutes: int = INFUSION_MINUTES) -> float:
    """a(t) tal que retenido(t)/infundido = e · a(t). En el pico, t = `minutes`."""
    s = _share(s)
    if t_min < minutes:
        raise ValueError("la forma cerrada vale desde el final de la infusión")
    return (1.0 - s) + s * smearing(tau_min, minutes=minutes) * decay(tau_min) ** (t_min - minutes)


def retained_share(e: float, s: float, tau_min: float, t_min: float,
                   *, minutes: int = INFUSION_MINUTES) -> float:
    """Fracción del volumen infundido retenida en el minuto `t_min`. Exacta, lineal en `e`."""
    return e * coefficient(s, tau_min, t_min, minutes=minutes)


def peak_share(e: float, s: float, tau_min: float, *, minutes: int = INFUSION_MINUTES) -> float:
    """El máximo de la fracción retenida: cae en el final de la infusión."""
    return retained_share(e, s, tau_min, minutes, minutes=minutes)


def behaviour(e: float, s: float, tau_min: float, *, times=(30.0, 60.0, 120.0),
              minutes: int = INFUSION_MINUTES) -> dict:
    """Las coordenadas de COMPORTAMIENTO: el pico y la fracción retenida en cada tiempo pedido."""
    out = {"peak": peak_share(e, s, tau_min, minutes=minutes)}
    out.update({t: retained_share(e, s, tau_min, t, minutes=minutes) for t in times})
    return out


def e_interval(s: float, tau_min: float, envelopes: dict, *, e_max: float,
               minutes: int = INFUSION_MINUTES):
    """Intervalo EXACTO de `e` admisible a (s, τ) dado, y qué restricción liga cada borde.

    `envelopes` mapea cada lectura ("peak" o un tiempo en minutos) a su par (inferior, superior); son las
    envolventes docentes y hay que pasarlas. `e_max` es el borde del dominio declarado del parámetro.
    Devuelve `(lo, hi, liga_inferior, liga_superior)`, o `EMPTY` si la intersección es vacía.
    """
    if not envelopes:
        raise ValueError("hay que pasar las envolventes; esta herramienta no las trae por omisión")
    a = {k: (peak_share(1.0, s, tau_min, minutes=minutes) if k == "peak"
             else retained_share(1.0, s, tau_min, float(k), minutes=minutes)) for k in envelopes}
    lows = {k: envelopes[k][0] / a[k] for k in envelopes}
    highs = {k: envelopes[k][1] / a[k] for k in envelopes}
    lo_key = max(lows, key=lambda k: lows[k])
    hi_key = min(highs, key=lambda k: highs[k])
    lo, hi = lows[lo_key], highs[hi_key]
    if e_max < hi:
        hi, hi_key = e_max, DOMAIN_EDGE
    if lo > hi:
        return EMPTY
    return lo, hi, lo_key, hi_key


def invert(peak: float, r30: float, r120: float, *, minutes: int = INFUSION_MINUTES,
           iterations: int = 200):
    """(Rpico, R30, R120) → (e, s, τ). Uno a uno; verificada a 2,1·10⁻¹⁴ contra la ida.

    Con p = e(1−s), q = e·s·C y λ = exp(−1/τ): Rpico = p + q, R30 = p + q·λ¹⁰, R120 = p + q·λ¹⁰⁰. El
    cociente (Rpico−R30)/(Rpico−R120) es monótono en λ, así que λ sale por bisección y el resto en forma
    cerrada. Pide un decaimiento estricto: Rpico > R30 > R120 > 0.
    """
    if not peak > r30 > r120 > 0.0:
        raise ValueError("el modelo sólo produce decaimiento estricto: Rpico > R30 > R120 > 0")
    n30, n120 = 30.0 - minutes, 120.0 - minutes
    target = (peak - r30) / (peak - r120)
    ratio = lambda lam: (1.0 - lam ** n30) / (1.0 - lam ** n120)
    lo, hi = 1e-12, 1.0 - 1e-12
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        if ratio(mid) > target:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    q = (peak - r30) / (1.0 - lam ** n30)
    p = peak - q
    if p <= 0.0:
        raise ValueError("ese comportamiento exigiría una fracción permanente negativa")
    tau = -1.0 / math.log(lam)
    c = smearing(tau, minutes=minutes)
    e = p + q / c
    return e, (q / c) / e, tau


def behaviour_is_reachable(peak: float, r30: float, r120: float,
                           *, minutes: int = INFUSION_MINUTES) -> bool:
    """¿Puede el modelo producir ese comportamiento? Sin inventar nada: lo intenta invertir."""
    try:
        e, s, tau = invert(peak, r30, r120, minutes=minutes)
    except ValueError:
        return False
    return 0.0 < e and 0.0 <= s <= 1.0 and tau > 0.0


def peak_ceiling_from_dilution(ceiling: float) -> float:
    """Pasa a limpio el único aporte de FD-BLD-06: un techo sobre Rpico, medido, nunca supuesto.

    Se exige nombrarlo porque esta herramienta no puede calcularlo: la dilución no es analítica (el
    cristaloide apaga el relleno) y depende del volumen de llegada del caso.
    """
    if not 0.0 < ceiling < 1.0:
        raise ValueError("el techo de Rpico es una fracción medida en (0, 1)")
    return ceiling
