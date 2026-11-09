"""Contrato de causalidad de manejo — P3-104.

Una sola norma reutilizable para las seis familias certificadas. Es **especificación**: no importa nada,
no conoce ninguna familia y **no lleva ningún valor numérico de enfermedad**. Quien evalúa una familia trae
sus propias trayectorias y sus propias bandas; este módulo dice qué significa que una intervención esté
suficientemente modelada, y ofrece los predicados genéricos para comprobarlo.

Por qué no importa nada: `test_shadow_core_isolation` declara la capa de comparación como un conjunto de
cinco módulos nombrados, y un módulo nuevo de la raíz no puede importar `clinical_core` ni esa capa. Y la
guarda de la fontanería es **textual**, no de import: un módulo de la raíz que no sea `app.py` ni
`pilot_acceptance.py` no puede ni **nombrar** esa capa, ni en una docstring. Así que la evaluación que
necesita el núcleo vive donde corresponde: dentro de la capa, o en un archivo de prueba.
"""
from __future__ import annotations

#: Las nueve propiedades del estándar educativo, en el orden en que la docencia las fijó.
STANDARD = ("DIRECTION", "TEMPORALITY", "CAUSAL_SPECIFICITY", "MAGNITUDE_PLAUSIBILITY",
            "DOSE_ORDERING", "REVERSIBILITY", "TIME_WITHOUT_ACTION", "CROSS_FAMILY_CONSISTENCY", "SAFETY")

#: Lo que hay que declarar por cada par enfermedad/intervención. Ocho campos, ninguno numérico aquí.
MANAGEMENT_CAUSALITY_CONTRACT = {
    "A_target_mechanism": "el canal común que la intervención escribe, nombrado; nunca una variable de "
                          "lectura",
    "B_expected_direction": "el signo del efecto sobre ese canal, y el signo esperado aguas abajo",
    "C_onset": "cuándo empieza el efecto, y de quién es el reloj: el del motor, el del escritor, o ninguno",
    "D_persistence": "cuánto dura y si revierte; si no hay semántica de reversión, se declara",
    "E_dose_ordering": "si más intervención da más efecto, y dónde satura; NOT_APPLICABLE si la acción es "
                       "de dosis fija",
    "F_downstream_observables": "qué lecturas deberían moverse, y en qué orden causal",
    "G_must_not_change": "qué NO debe moverse directamente: el atajo que delataría el mecanismo equivocado",
    "H_boundary_behaviour": "qué pasa en el borde: sin efecto posible, saturación, o fallo declarado",
}

#: Estados de una intervención en la matriz. Son los del encargo, sin añadidos.
CAUSALLY_READY = "CAUSALLY_READY"
READY_WITH_REGION = "READY_WITH_REGION"
STRUCTURAL_ONLY = "STRUCTURAL_ONLY"
MISSING_TREATMENT_WRITER = "MISSING_TREATMENT_WRITER"
MISSING_COMMON_MECHANISM = "MISSING_COMMON_MECHANISM"
PARAMETER_REGION_MISSING = "PARAMETER_REGION_MISSING"
NOT_REQUIRED_FOR_INITIAL_VALIDATION = "NOT_REQUIRED_FOR_INITIAL_VALIDATION"
STATUSES = (CAUSALLY_READY, READY_WITH_REGION, STRUCTURAL_ONLY, MISSING_TREATMENT_WRITER,
            MISSING_COMMON_MECHANISM, PARAMETER_REGION_MISSING, NOT_REQUIRED_FOR_INITIAL_VALIDATION)

#: Estados de una familia en el punto de control.
FAMILY_READY = "MANAGEMENT_CAUSALITY_READY"
FAMILY_ONE_GAP = "READY_WITH_ONE_MINIMUM_GAP"
FAMILY_MULTIPLE_GAPS = "MULTIPLE_GAPS"
FAMILY_STRUCTURAL = "STRUCTURAL_COMMON_MECHANISM_MISSING"

#: Clasificación de un peligro declarado por la puntuación.
DANGER_SUPPORTED = "PHYSIOLOGICALLY_SUPPORTED_DANGER"
DANGER_SCORING_ONLY = "SCORING_ONLY_DANGER"
DANGER_MISSING = "MISSING_PHYSIOLOGIC_MECHANISM"

#: Etiquetas que una decisión de desarrollo puede llevar, y las que no.
DEVELOPMENT_CANDIDATE = "DEVELOPMENT_CLINICAL_CANDIDATE"
DEVELOPMENT_REGION = "DEVELOPMENT_CLINICAL_REGION"
FORBIDDEN_LABELS = ("CLINICALLY_VALIDATED", "PRODUCTION_APPROVED",
                    "FACULTY_APPROVED_FOR_CLINICAL_TRUTH")


# -- predicados genéricos: una serie es {minuto: valor} ------------------------------------------------

def _at(series, minute):
    return series[minute]


def no_effect_before(treated, untreated, activation, *, tolerance: float = 0.0) -> bool:
    """TEMPORALITY, mitad dura: antes de la activación las dos series son la misma. Sin fuga del futuro."""
    shared = sorted(set(treated) & set(untreated))
    return all(abs(treated[m] - untreated[m]) <= tolerance for m in shared if m < activation)


def effect_starts_at(treated, untreated, activation, *, tolerance: float = 0.0) -> int | None:
    """El primer minuto en que las series difieren. None si nunca difieren."""
    for m in sorted(set(treated) & set(untreated)):
        if abs(treated[m] - untreated[m]) > tolerance:
            return m
    return None


def direction(treated, untreated, minute, *, better: str) -> bool:
    """DIRECTION: `better` es 'higher' o 'lower' y dice qué significa mejorar en esa lectura."""
    delta = treated[minute] - untreated[minute]
    if better == "higher":
        return delta > 0.0
    if better == "lower":
        return delta < 0.0
    raise ValueError("better debe ser 'higher' o 'lower'")


def monotone_after(series, activation, *, rising: bool) -> bool:
    """PERSISTENCE: tras la activación el efecto no se da media vuelta."""
    xs = [series[m] for m in sorted(series) if m >= activation]
    pairs = zip(xs, xs[1:])
    return all((b >= a) if rising else (b <= a) for a, b in pairs)


def dose_ordered(by_dose, minute, *, better: str) -> bool:
    """DOSE_ORDERING: más intervención, no menos efecto. `by_dose` es {dosis: serie}, dosis creciente."""
    doses = sorted(by_dose)
    values = [by_dose[d][minute] for d in doses]
    pairs = zip(values, values[1:])
    return all((b >= a) if better == "higher" else (b <= a) for a, b in pairs)


def waiting_has_cost(now, later, minute, *, better: str) -> bool:
    """TIME_WITHOUT_ACTION: tratar ahora no puede ser peor que tratar más tarde, en el mismo minuto."""
    return direction(now, later, minute, better=better)


def untouched(treated, untreated, *, tolerance: float = 0.0) -> bool:
    """G del contrato: la lectura que NO debería moverse directamente, no se mueve."""
    shared = set(treated) & set(untreated)
    return all(abs(treated[m] - untreated[m]) <= tolerance for m in shared)


def inside(series, minute, low: float, high: float) -> bool:
    """MAGNITUDE_PLAUSIBILITY contra una banda que quien llama declara. No hay bandas por omisión."""
    if not low <= high:
        raise ValueError("la banda va de menor a mayor")
    return low <= series[minute] <= high


def no_paradox(treated, untreated, activation, *, better: str) -> bool:
    """SAFETY: la intervención no empeora nunca, en ningún minuto desde su activación."""
    shared = sorted(set(treated) & set(untreated))
    return all(not direction(untreated, treated, m, better=better)
               for m in shared if m >= activation)
