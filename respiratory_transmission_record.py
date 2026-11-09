"""P3-117 y P3-118: el registro de la transmision hipoventilacion -> oxigenacion.

Especificacion y medicion, sin fisiologia: no importa el nucleo comun ni la capa de sombra, y **no adopta
ningun parametro**. El enlace comun (P2T-5) sigue UNSET en el nucleo congelado y este modulo no lo enciende.

Lo que hay aqui: la decision docente de desarrollo tal como se recibio, la ecuacion reconstruida, los tres
mandos candidatos con su veredicto medido, la region de transmision admisible por caso y en comun, los
testigos de asma y el dictamen. Documento: docs/PHASE3_RESPIRATORY_TRANSMISSION.md
"""
from __future__ import annotations

#: Lo que este registro ES. No adopta parametro alguno: mide y dictamina.
STATUS = "DEVELOPMENT_MEASUREMENT_NO_PARAMETER_ADOPTED"

#: Lo que este registro NUNCA es. Ninguna medicion de aqui vale como verdad clinica.
FORBIDDEN_STATUSES = (
    "CLINICALLY_VALIDATED",
    "FACULTY_APPROVED_CLINICAL_TRUTH",
    "PRODUCTION_TARGET",
    "PRODUCTION_APPROVED",
    "CANONICAL_RESPIRATORY_PARAMETER_SET",
)

# -- la decision docente, tal como se recibio -------------------------------------------------------------

#: Sólo para calibracion de DESARROLLO. No es verdad clinica ni objetivo de produccion.
FACULTY_DEVELOPMENT_DECISION = {
    "scenario": "hipoventilacion central por opioide grave: FR ~4-5/min, mecanica normal, aire ambiente, "
                "sin naloxona, sin soporte ventilatorio, ~60 min sin tratar",
    "quantity": "SpO2 a los 60 min",
    "region": (78.0, 88.0),
    "classification": "DEVELOPMENT_CLINICAL_REGION",
    "confidence": 0.84,
    "rationale": "una hipoventilacion grave deberia crear hipoxemia importante; el colapso universal hacia "
                 "~25% con transmision completa es demasiado extremo para el caso redactado como "
                 "sobrevivible; el modelo debe preservar la distincion entre el oxigeno que mejora la "
                 "oxigenacion y la naloxona que corrige la ventilacion central",
    "falsifier": "si ninguna region comun de transmision satisface esta conducta opioide preservando la "
                 "conducta respiratoria y de asma certificada, NO forzar la region: informar "
                 "COMMON_SINGLE_FACTOR_INSUFFICIENT y detener ese mecanismo",
    "is_clinical_truth": False,
}

# -- la ecuacion reconstruida (P3-117-1) ------------------------------------------------------------------

#: La cadena viva, eslabon por eslabon, con la procedencia que el propio nucleo declara para cada cantidad.
EQUATION = (
    ("FR expresada", "la composicion comun del impulso respiratorio (P2P-2)", "ADOPTED"),
    ("W = eficiencia x FR / FR_intrinseca / razon_de_demanda", "derived.alveolar_ventilation", "ADOPTED"),
    ("PaCO2 = paco2_reference_mmhg / W", "derived.respiration, candidato de mecanica comun (P2S-2)",
     "PROVISIONAL"),
    ("PaCO2_llegada = paco2_reference_mmhg / W_llegada", "derived.arrival_paco2_reference, del modelo y "
     "nunca el PaCO2 redactado", "PROVISIONAL"),
    ("delta = PaCO2 - PaCO2_llegada", "la forma relativa: Patm, PH2O y el gas alveolar absoluto se cancelan",
     "PROVISIONAL"),
    ("PaO2_latente = ODC^-1(SpO2_base)", "derived.pao2_from_oxygen_saturation (Severinghaus 1979, sin "
     "parametro ajustado)", "ADOPTED"),
    ("dPaO2 = -delta / respiratory_quotient", "derived.ventilated_oxygenation (P2T-5)", "UNSET"),
    ("SpO2 = ODC(PaO2_latente + dPaO2)", "derived.oxygen_saturation_from_pao2", "ADOPTED"),
)

#: SpO2_base es la via ya certificada G / L -> G / FiO2 (P2O-3). El enlace la mueve; no la reemplaza.
SPO2_BASE_SOURCE = "derived.oxygenation(gas_exchange, fio2, anchors, profile, credit)"

# -- los tres mandos candidatos (P3-117-1): ninguno es un coeficiente de transmision ----------------------

LEVER_USABLE = "IS_A_TRANSMISSION_SCALE_BUT_NOT_A_TRANSMISSION_COEFFICIENT"
LEVER_DISHONEST = "SCALES_THE_DELTA_BUT_FALSIFIES_ITS_OWN_DECLARED_QUANTITY"
LEVER_INERT = "MEASURED_INERT_FOR_THIS_CASE"

CANDIDATE_LEVERS = {
    "respiratory_quotient": {
        "how": "divide el delta: dPaO2 = -delta / R, luego f = 1/R es la fraccion de transmision",
        "committed": None,
        "declared_meaning": "el cociente respiratorio del enlace alveolar relativo comun (CO2 producido "
                            "sobre O2 consumido), fisiologicamente ~0.7-1.0",
        "required_for_the_region": 13.1968,
        "verdict": LEVER_USABLE,
        "why_not": "expresar f <= 0.075776 exige R >= 13.1968, que no es un cociente respiratorio: el campo "
                   "tiene nombre y significado declarados, y afirmar ese valor haria falsa la semantica "
                   "del propio modelo",
    },
    "paco2_reference_mmhg": {
        "how": "escala el delta linealmente: delta = ref x (1/W - 1/W_llegada)",
        "committed": 40.0,
        "declared_meaning": "el PaCO2 a W = 1, es decir el PaCO2 normal",
        "required_for_the_region": 3.03,
        "verdict": LEVER_DISHONEST,
        "why_not": "medido: con ref = 3.03 el PaCO2(60) del caso vale 7.061 mmHg, un valor imposible; "
                   "ademas el campo es comun a todas las familias y alimenta bicarbonato, pH y el impulso "
                   "acido",
    },
    "rr_ventilatory_floor": {
        "how": "hipotesis: fija la FR intrinseca de la composicion de llegada, y el delta es lineal en ella",
        "committed": 12.0,
        "declared_meaning": "la FR por debajo de la cual la FR de llegada no se lee como metabolica (TBD)",
        "required_for_the_region": None,
        "verdict": LEVER_INERT,
        "why_not": "hipotesis FALSIFICADA por medicion: el delta(60) de opioid_35m vale 24.2104 con el piso "
                   "en 0.0, 3.0, 6.0, 12.0 y 18.0; el piso no alcanza a la FR intrinseca de este caso",
    },
}

# -- la region de transmision admisible (P3-117-3) --------------------------------------------------------

#: Por caso: la SpO2 sin enlace, el delta real a los 60 min y la fraccion de transmision que aun respeta
#: el piso de 78 % de la decision docente. El techo de 88 % no ata: la transmision solo baja la SpO2.
PER_CASE = {
    "opioid_35m": {
        "arrival_paco2_reference_mmhg": 69.0,
        "paco2_at_60": 93.2104,
        "delta_at_60": 24.2104,
        "spo2_base_at_60": 80.0,
        "latent_pao2_at_60": 44.303,
        "admissible_pao2_drop_to_78": 1.8346,
        "transmission_fraction_max": 0.075776,
        "respiratory_quotient_min": 13.1968,
        "spo2_at_full_transmission_r_0_8": 25.2492,
    },
    "opioid_67f": {
        "arrival_paco2_reference_mmhg": 61.0,
        "paco2_at_60": 82.4034,
        "delta_at_60": 21.4034,
        "spo2_base_at_60": 84.0,
        "latent_pao2_at_60": 48.706,
        "admissible_pao2_drop_to_78": 6.2378,
        "transmission_fraction_max": 0.291441,
        "respiratory_quotient_min": 3.4312,
        "spo2_at_full_transmission_r_0_8": 37.2165,
    },
}

#: La region COMUN es la interseccion, no un punto medio: la ata el caso mas grave.
COMMON_REGION = {
    "transmission_fraction": (0.0, 0.075776),
    "equivalent_respiratory_quotient": (13.1968, None),
    "binding_case": "opioid_35m",
    "is_a_point": False,
    "midpoint_is_preferred": False,
    "second_case_alone_would_allow": 0.291441,
}

#: Y la region no esta vacia por una razon que hay que decir en voz alta: la SpO2 SIN enlace ya cae dentro
#: de [78, 88] en los dos casos (80.0 y 84.0). El modelo cumple el objetivo docente en NIVEL, no en
#: trayectoria: la SpO2 del opioide es plana (SpO2(1) == SpO2(60), exactamente).
TARGET_ALREADY_MET_WITH_THE_LINK_OFF = True
SPO2_HAS_NO_OPIOID_TRAJECTORY = True

# -- los testigos de asma (P3-120), medidos sin ajustar nada aparte --------------------------------------

ASTHMA_COMPATIBLE = "ASTHMA_COMPATIBLE"
ASTHMA_TENSION = "ASTHMA_TENSION"
ASTHMA_CONTRADICTION = "ASTHMA_CONTRADICTION"

ASTHMA_WITNESSES = {
    "asthma_49m": {
        "spo2_at_60_link_off": 89.0,
        "spo2_at_60_at_the_common_boundary": 88.6072,
        "shift_at_the_common_boundary": -0.3928,
        "spo2_at_60_at_full_transmission_r_0_8": 79.6511,
        "shift_at_full_transmission": -9.3489,
        "classification": ASTHMA_COMPATIBLE,
        "basis": "el desplazamiento en el borde de la region comun es de -0.39 puntos de SpO2 y la "
                 "direccion es la correcta (mas PaCO2, menos SpO2); la envolvente certificada de asma NO "
                 "se re-corrio, porque la region no se habilita",
    },
    "asthma_24f": {
        "spo2_at_60_link_off": 90.0,
        "spo2_at_60_at_the_common_boundary": 89.626,
        "shift_at_the_common_boundary": -0.374,
        "spo2_at_60_at_full_transmission_r_0_8": 80.8834,
        "shift_at_full_transmission": -9.1166,
        "classification": ASTHMA_COMPATIBLE,
        "basis": "igual que el testigo anterior: -0.37 puntos en el borde, sin re-correr la envolvente",
    },
}

# -- el lazo indirecto que el enlace cierra (hallazgo de P3-117) ------------------------------------------

#: P2T-5 rechaza el impulso hipoxemico por ser "un lazo que ninguna auditoria ha examinado"
#: (HYPOXEMIC_FEEDBACK_LOOP_DEFERRED), y exige el impulso acido para la mecanica. Medido: al encender el
#: enlace, el PaCO2 de la propia corrida CAMBIA, asi que el enlace no es el mapa de una sola via que su
#: documentacion sugiere. La letra de esa documentacion se sostiene (no hay escritura directa de vuelta);
#: el lazo es indirecto, por el deficit de oxigeno y la carga acida.
INDIRECT_LOOP = {
    "exists": True,
    "route": "SpO2 -> deficit de oxigeno / carga acida -> impulso respiratorio (acid_to_drive_gain) -> FR "
             "-> W -> PaCO2 -> SpO2",
    "refused_route_is_not_this_one": "hypoxaemic_drive_mapping, que sigue en None y rechazado",
    "continuous_not_a_threshold": True,
    "measured_at_r_0_8_opioid_35m": {
        "delta_without_the_link": 24.2104,
        "delta_with_the_link": 21.5026,
        "respiratory_rate_without_the_link": 4.4416,
        "respiratory_rate_with_the_link": 4.5745,
        "delivery_rel_without_the_link": 1.0,
        "delivery_rel_with_the_link": 0.3051,
        "consciousness_level": 2.0,
    },
    "note": "la consciencia vale 2.0 con y sin enlace y en todo el barrido de R, asi que no es un cruce de "
            "umbral de colapso; el desvio crece de forma continua con la transmision y a R = 1.0 ya es "
            "menor que 1e-4 en SpO2",
}

# -- las cuatro monotonias que P2T-5 declara (P3-117-5) ---------------------------------------------------

MONOTONICITY = {
    "M1_more_paco2_never_raises_spo2": True,
    "M2_less_paco2_never_lowers_spo2": True,
    "M3_worse_gas_exchange_never_raises_spo2": True,
    "M4_less_fio2_never_raises_spo2": True,
    "basis": "M1 y M2 sobre una malla de delta con SpO2_base fija, con igualdad exacta en delta = 0; M3 y "
             "M4 por la monotonia estricta del enlace en SpO2_base, que es la via por la que G y FiO2 "
             "entran",
}

# -- el dictamen (P3-117-6) -------------------------------------------------------------------------------

VERDICT = "C_EXISTING_INTERFACE_CANNOT_EXPRESS_PARTIAL_TRANSMISSION"
CONSEQUENCE = "D_FROZEN_COMMON_CORE_EXTENSION_REQUIRED"

VERDICT_REASONING = (
    "La region comun EXISTE y se midio: f en (0, 0.075776], o R >= 13.1968, y preserva asma dentro de "
    "-0.39 puntos de SpO2. Lo que no existe es una interfaz honesta para expresarla. El unico mando que "
    "escala la transmision es respiratory_quotient, cuyo nombre y documentacion lo declaran cociente "
    "respiratorio; afirmar 13.1968 seria ajustar un numero contra una cantidad que significa otra cosa. "
    "El segundo mando exige un PaCO2 normal de 3 mmHg y produce un PaCO2(60) de 7.061 mmHg. El tercero "
    "resulto inerte. Una transmision parcial honesta necesita un coeficiente de transmision propio, que "
    "es un parametro nuevo y una ecuacion modificada en el nucleo congelado: por la regla arquitectonica "
    "del encargo, eso es STOP y no se implementa."
)

#: Por que NO se usa la etiqueta del falsificador docente: el falsificador preveia que ninguna region
#: comun satisficiera la conducta. Si la satisface. Lo que falla es la interfaz, no la region, y decirlo
#: COMMON_SINGLE_FACTOR_INSUFFICIENT ocultaria una region medida que la docencia puede querer autorizar.
FALSIFIER_NOT_TRIGGERED = {
    "label_not_used": "COMMON_SINGLE_FACTOR_INSUFFICIENT",
    "why": "la condicion del falsificador es que NO exista region comun; la region existe y esta medida",
}

#: Y por eso P3-118 no se ejecuta: el encargo lo condiciona a que la interfaz existente alcance.
P3_118_EXECUTED = False
P3_118_REASON = "el encargo condiciona P3-118 a que una interfaz certificada existente alcance; no alcanza"


def transmission_region_of(case_id: str) -> tuple:
    """La region admisible de un caso como (f_min, f_max). Nunca un punto."""
    entry = PER_CASE[case_id]
    return (0.0, entry["transmission_fraction_max"])


def common_transmission_region() -> tuple:
    """La interseccion sobre los casos medidos, calculada y no copiada."""
    return (0.0, min(e["transmission_fraction_max"] for e in PER_CASE.values()))


def validate_entry(entry: dict) -> None:
    """Un registro por caso declara su delta, su SpO2 base y su region; nunca un punto preferido."""
    for key in ("delta_at_60", "spo2_base_at_60", "transmission_fraction_max", "respiratory_quotient_min"):
        if key not in entry:
            raise ValueError(f"falta {key}")
    if not 0.0 < entry["transmission_fraction_max"] < 1.0:
        raise ValueError("la fraccion de transmision admisible es una fraccion propia")
    if entry["delta_at_60"] <= 0.0:
        raise ValueError("una hipoventilacion sostenida sube el PaCO2 sobre el de llegada")
    if "preferred_value" in entry or "chosen_value" in entry:
        raise ValueError("este registro no elige un valor")
