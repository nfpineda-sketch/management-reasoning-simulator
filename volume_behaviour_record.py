"""Registro de la región de comportamiento de volumen que la docencia definió — P3-81.

Esto es un REGISTRO, no una aprobación de parámetros. Su estado es
`FACULTY_DEFINED_BEHAVIORAL_REGION` y nunca otro: la docencia aceptó rangos de **comportamiento
clínicamente interpretable**, no un punto (e, s, τ). Los tres rótulos que este registro **no** puede llevar
están declarados abajo y una prueba lo comprueba.

Qué no hace:

- no importa `clinical_core` ni el registro de autoridad;
- no reescribe ninguna restricción FD-BLD: la banda histórica de FD-BLD-04 queda aquí **tal cual**, y el techo
  efectivo más estrecho se guarda **aparte**, como lo que es: la intersección de las restricciones vigentes
  sobre los dos casos GI certificados;
- no elige ningún punto, no propone ningún punto medio y no trae valores por omisión para lo que la docencia
  tiene que nombrar.

La decisión docente que lo origina (V-2, 2026-11-09) aceptó las envolventes **ya existentes** como región
inicial. No hay ningún número clínico nuevo en este archivo.
"""
from __future__ import annotations

#: El único estado que este registro puede llevar.
STATUS = "FACULTY_DEFINED_BEHAVIORAL_REGION"
#: Rótulos que este registro NO puede llevar, por decisión docente expresa.
FORBIDDEN_STATUSES = ("CLINICALLY_VALIDATED_PARAMETER_POINT", "FACULTY_APPROVED_PARAMETER_POINT",
                      "CANONICAL_VOLUME_PARAMETER_SET", "FACULTY_APPROVED_PARAMETERS",
                      "CLINICALLY_VALIDATED")

#: La banda HISTÓRICA de FD-BLD-04, conservada byte a byte como está en el módulo congelado. No se reescribe.
FD_BLD_04_HISTORICAL_PEAK = (0.15, 0.30)
#: Techo del pico que implica FD-BLD-06 **por caso**, medido contra el evaluador congelado (P3-76).
#: La diferencia entre los dos casos es su Hb de llegada redactada (6,7 y 6,4 g/dL), no su volumen.
CASE_PEAK_CAPS = {"gi_bleed_57m": 0.27072, "gi_bleed_72f": 0.28518}
#: Para una región COMÚN a los dos casos rige la intersección, es decir el techo más restrictivo.
#: Esto no hace desaparecer el techo del otro caso: ver `case_only_peak_band`.
COMMON_PEAK_CAP = min(CASE_PEAK_CAPS.values())

#: El registro de P3-81. Cada rango es el que la docencia aceptó; ninguno es nuevo.
RECORD = {
    "status": STATUS,
    "R30_range": (0.15, 0.25),
    "R120_range": (0.05, 0.15),
    "Rpeak_range": (0.15, COMMON_PEAK_CAP),
    "fourth_observation_used": False,
    "applies_to": "modelo de cristaloide del adulto GI certificado, con la semántica exacta del repositorio: "
                  "fracción del volumen infundido retenida intravascularmente, bolsa de 1 L isotónico "
                  "entrando en 20 min desde el minuto 0, con el sangrado del caso continuando",
    "provenance": "FD-BLD-04, FD-BLD-05 y FD-BLD-06 vigentes, más la decisión docente V-2 del 2026-11-09 que "
                  "las acepta como región inicial de comportamiento. Ningún número clínico nuevo.",
    "decided_on": "2026-11-09",
}

#: Clasificación formal del valor provisional de referencia (P3-86-2). No reescribe nada congelado:
#: `blood_anchors.REFERENCE` conserva su 0,125 y sus artefactos históricos tal cual. Esto sólo lo rotula.
HISTORICAL_REFERENCE = {
    "parameter": "crystalloid_effective_ml_per_ml",
    "value": 0.125,
    "classification": "HISTORICAL_PROVISIONAL_NON_SURVIVING_REFERENCE",
    "why": "valor provisional de P2I-2T, anterior a las envolventes de P2I-2U; nunca candidato ni aprobado; "
           "TD-88 ya lo registraba como no superviviente desde P2I-2X; y `e > 0,15` es consecuencia "
           "analítica de `a_pico < 1`, así que ningún (s, τ) lo rescata",
    "rewrites_frozen_history": False,
}

#: La restricción congelada que la decisión docente **no nombró** y que la región tiene que llevar igual:
#: la caja de tres coordenadas NO la implica (10 976 de 709 038 puntos probados la violan, P3-82).
R60_RANGE_FROM_FROZEN_FD_BLD_05 = (0.10, 0.20)

#: La región EFECTIVA sobre la que se trabaja: la caja docente más esa cuarta lectura congelada.
EFFECTIVE_REGION = {
    "peak": RECORD["Rpeak_range"],
    30: RECORD["R30_range"],
    60: R60_RANGE_FROM_FROZEN_FD_BLD_05,
    120: RECORD["R120_range"],
}

#: Margen hacia dentro que necesita un testigo numérico. El evaluador congelado compara de forma inclusiva
#: sobre el valor sin redondear, y ese valor difiere de la forma cerrada en ~10⁻¹⁶, así que un testigo puesto
#: EXACTAMENTE sobre el borde puede caer a cualquier lado. Medido: 10⁻⁹ relativo basta (P3-83).
WITNESS_INTERIOR_MARGIN = 1e-9

UNREACHABLE_ORDER = "UNREACHABLE_THE_MODEL_ONLY_DECAYS"
UNREACHABLE_POSITIVE = "UNREACHABLE_A_RETAINED_FRACTION_MUST_BE_POSITIVE"
RANGE_INVERTED = "RANGE_INVERTED"
OUTSIDE_RECORDED_REGION = "OUTSIDE_THE_RECORDED_REGION"


def case_only_peak_band(case: str) -> tuple:
    """La franja de `Rpico` que ese caso admite y la región común no: por qué su techo no desaparece."""
    if case not in CASE_PEAK_CAPS:
        raise ValueError(f"caso no certificado: {case}")
    return (COMMON_PEAK_CAP, CASE_PEAK_CAPS[case])


def validate_entry(entry: dict) -> list:
    """Motivos por los que una entrada de comportamiento se rechaza. Lista vacía = aceptable.

    No rellena nada: una entrada que no nombre sus tres rangos se rechaza por lo que falta.
    """
    reasons = []
    for key in ("R30_range", "R120_range", "Rpeak_range"):
        if key not in entry:
            reasons.append(f"FALTA_{key}")
            continue
        lo, hi = entry[key]
        if not (0.0 < lo <= hi):
            reasons.append(f"{RANGE_INVERTED}:{key}")
    if reasons:
        return reasons
    peak, r30, r120 = entry["Rpeak_range"], entry["R30_range"], entry["R120_range"]
    # el modelo sólo produce decaimiento monótono estricto: el techo de una lectura posterior no puede
    # superar el suelo de una anterior
    if r30[1] > peak[1] or r120[1] > r30[1]:
        reasons.append(UNREACHABLE_ORDER)
    if r120[0] <= 0.0:
        reasons.append(UNREACHABLE_POSITIVE)
    for key, recorded in (("Rpeak_range", RECORD["Rpeak_range"]), ("R30_range", RECORD["R30_range"]),
                          ("R120_range", RECORD["R120_range"])):
        lo, hi = entry[key]
        if lo < recorded[0] or hi > recorded[1]:
            reasons.append(f"{OUTSIDE_RECORDED_REGION}:{key}")
    return reasons
