"""Shared clinical physiology recovered from main/IA.

The legacy profile preserves its coefficients exactly. ContextVar callbacks keep
randomness and display formatting scoped to one invocation/session. Generated
profiles use the shared, parameterized numerical primitives below; never infer a
legacy hidden state from a diagnosis or learner reasoning.
"""
from copy import deepcopy
from contextvars import ContextVar
import math

_callbacks = globals().get("_callbacks") or ContextVar("physiology_callbacks", default=None)

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def rng():
    return _callbacks.get()[0]()

def sim_time_label(minutes):
    return _callbacks.get()[1](minutes)

def invoke(name, args, kwargs, rng_factory, time_label):
    token = _callbacks.set((rng_factory, time_label))
    try:
        return globals()[name](*args, **kwargs)
    finally:
        _callbacks.reset(token)

def classify_volume_state(ev):
    if ev < 0.45:
        return "markedly reduced"
    if ev < 0.60:
        return "moderately reduced"
    if ev < 0.75:
        return "near adequate"
    return "adequate / loaded"


def fluid_responsiveness(ev):
    """
    Smooth Frank-Starling-style remaining preload responsiveness.

    High when effective filling is low, then progressively saturates as preload
    approaches adequacy. This is intentionally continuous rather than a bolus lookup.
    """
    # v0.6.0.2: a broader Frank-Starling transition. Responsiveness still declines
    # continuously with filling, but does not collapse to near-zero after ~1 L.
    # This lets additional retained volume remain physiologically visible while
    # preserving diminishing returns.
    return clamp(1.0 / (1.0 + math.exp(8.0 * (ev - 0.62))), 0.06, 0.98)


def update_fluid_phenotype(state):
    """
    v0.6 preload / fluid-responsiveness phenotype.

    The state distinguishes:
      - retained intravascular crystalloid effect,
      - effective preload,
      - remaining preload responsiveness,
      - cumulative administered crystalloid.

    The learner never sees these internal variables. They drive stroke volume and
    effective cardiac output in recompute_coupled_physiology().
    """
    h = state["hidden"]
    total = state["treatments"]["cumulative_crystalloid_ml"]

    h["fluid_load"] = total / 5000.0

    # Effective preload is the physiologic filling state, not the lifetime total fluid.
    preload = clamp(h.get("effective_volume", 0.35))
    h["preload_state"] = preload

    # Continuous saturating Frank-Starling reserve. Tachycardia and congestion can
    # reduce useful responsiveness without turning fluid into a scripted penalty.
    base_resp = fluid_responsiveness(preload)
    congestion_modifier = clamp(1.0 - 0.55 * h.get("pulmonary_congestion", 0.0), 0.35, 1.0)
    h["preload_responsiveness"] = clamp(base_resp * congestion_modifier, 0.04, 0.98)

    # Keep the legacy key synchronized so existing debug/logic remains compatible.
    h["fluid_responsiveness"] = h["preload_responsiveness"]

    # Tolerance remains a soft physiologic descriptor only; there is no liter-count
    # threshold that directly causes deterioration or arrest.
    h["fluid_tolerance"] = clamp(
        0.66
        - 0.28 * max(0.0, preload - 0.60)
        - 0.22 * h.get("pulmonary_congestion", 0.0),
        0.18, 0.72
    )


def fluid_intolerance_pressure(state, incoming_ml):
    """
    Continuous hydrostatic overfilling signal.

    No cumulative-liter threshold is used. The signal emerges from:
      - current effective preload,
      - retained intravascular volume,
      - existing pulmonary congestion,
      - incoming bolus size.

    A patient can therefore retain several liters with little penalty while still
    preload deficient, but once filling is high, additional volume increasingly
    contributes to congestion and reduced effective forward flow.
    """
    h = state["hidden"]
    update_fluid_phenotype(state)

    preload = h.get("preload_state", h["effective_volume"])
    retained = h.get("effective_intravascular_fluid", 0.0)
    projected_retained = retained + 0.10 * max(0.0, incoming_ml) / 500.0

    preload_excess = max(0.0, preload - 0.72)
    retained_excess = max(0.0, projected_retained - 0.52)
    congestion = h.get("pulmonary_congestion", 0.0)
    bolus_size = max(0.0, incoming_ml - 1000.0) / 3000.0

    return clamp(
        1.20 * preload_excess
        + 0.55 * retained_excess
        + 0.45 * congestion
        + 0.08 * bolus_size,
        0.0,
        1.25,
    )


def pulmonary_clinical_signal(state):
    h = state["hidden"]
    congestion = h.get("pulmonary_congestion", 0.0)
    overfill = h.get("overfill_burden", 0.0)
    extravascular = h.get("extravascular_fluid_burden", 0.0)

    # Preserve early fluid responsiveness: none of these surfaces become relevant
    # while the patient remains on the ascending portion of the preload curve.
    # The signal is state-derived; there is no cumulative-liter threshold.
    overfill_surface = clamp((overfill - 0.14) / 0.72, 0.0, 0.88)
    interstitial_surface = clamp((extravascular - 0.06) / 0.28, 0.0, 0.92)
    return max(congestion, overfill_surface, interstitial_surface)


def congestion_stage(congestion):
    if congestion < 0.18:
        return "none"
    if congestion < 0.30:
        return "early"
    if congestion < 0.45:
        return "moderate"
    return "marked"


def update_decompensation(state, added_fluid_ml=0, elapsed_min=0):
    """
    Convert state-derived overfilling / pulmonary congestion into respiratory
    decompensation and worsening global perfusion.

    v0.6.0.6 separates three fluid compartments:
      1) useful effective preload,
      2) retained intravascular crystalloid,
      3) redistributed extravascular/interstitial fluid.

    This allows preload benefit to wane while pulmonary fluid burden continues to
    accumulate. No cumulative-liter threshold directly triggers harm.
    """
    h = state["hidden"]
    o = state["observable"]

    if h.get("cardiac_arrest"):
        return

    preload = h.get("preload_state", h["effective_volume"])
    retained = h.get("effective_intravascular_fluid", 0.0)
    extravascular = h.get("extravascular_fluid_burden", 0.0)
    perfusion_deficit = 1.0 - h["tissue_perfusion"]

    preload_excess = max(0.0, preload - 0.76)
    retained_excess = max(0.0, retained - 0.40)
    interstitial_excess = max(0.0, extravascular - 0.045)

    # Pulmonary congestion is now a continuously evolving hidden state.
    # Inflammatory capillary leak amplifies the effect of interstitial fluid.
    leak_amplifier = 0.75 + 0.45 * h.get("inflammatory_drive", 0.0)
    target_congestion = clamp(
        0.05
        + 1.70 * interstitial_excess * leak_amplifier
        + 0.55 * preload_excess
        + 0.28 * retained_excess,
        0.03,
        0.95,
    )

    congestion = h.get("pulmonary_congestion", 0.05)
    if target_congestion > congestion:
        congestion += 0.10 * (target_congestion - congestion) * max(elapsed_min, 1)
    else:
        congestion += 0.025 * (target_congestion - congestion) * max(elapsed_min, 1)
    h["pulmonary_congestion"] = clamp(congestion, 0.02, 0.95)
    congestion = h["pulmonary_congestion"]

    # The right side of Frank-Starling is represented as a continuous overfill
    # burden, now including redistributed tissue fluid.
    target_overfill = clamp(
        1.15 * preload_excess
        + 0.70 * retained_excess
        + 1.25 * interstitial_excess
        + 0.90 * max(0.0, congestion - 0.18),
        0.0,
        1.25,
    )

    burden = h.get("overfill_burden", 0.0)
    if target_overfill > burden:
        burden += 0.16 * (target_overfill - burden) * max(elapsed_min, 1)
    else:
        burden += 0.03 * (target_overfill - burden) * max(elapsed_min, 1)
    h["overfill_burden"] = clamp(burden, 0.0, 1.25)

    # Respiratory failure follows the same pulmonary signal, so low-flow shock
    # cannot make significant hydrostatic congestion invisible.
    pulmonary_signal = pulmonary_clinical_signal(state)
    primary_resp = clamp(h.get("primary_respiratory_burden", 0.0))
    target_resp = clamp(
        max(
            0.78 * pulmonary_signal + 0.38 * max(0.0, congestion - 0.20),
            primary_resp,
        ),
        0.0,
        1.0,
    )
    h["respiratory_failure_severity"] = clamp(
        h["respiratory_failure_severity"]
        + 0.12 * (target_resp - h["respiratory_failure_severity"])
        * max(elapsed_min, 1)
    )

    h["global_perfusion_failure"] = clamp(
        max(
            h["global_perfusion_failure"] * 0.985,
            perfusion_deficit * 0.40
            + h["respiratory_failure_severity"] * 0.42
            + max(0.0, h["overfill_burden"] - 0.35) * 0.30
        )
    )

    respiratory_surface = max(
        h["respiratory_failure_severity"],
        pulmonary_clinical_signal(state),
    )

    # Learner-facing respiratory phenotype. These are thresholds on the continuous
    # hidden pulmonary signal, not thresholds on administered fluid volume.
    if respiratory_surface >= 0.18:
        o["respiratory_rate"] = max(o["respiratory_rate"], 24)
        o["work_of_breathing"] = "Increased"
    if respiratory_surface >= 0.30:
        o["spo2"] = min(o["spo2"], 92)
        o["respiratory_rate"] = max(o["respiratory_rate"], 28)
        o["work_of_breathing"] = "Moderately increased"
    if respiratory_surface >= 0.42:
        o["spo2"] = min(o["spo2"], 89)
        o["respiratory_rate"] = max(o["respiratory_rate"], 32)
        o["work_of_breathing"] = "Markedly increased"
    if respiratory_surface >= 0.56:
        o["spo2"] = min(o["spo2"], 85)
        o["respiratory_rate"] = max(o["respiratory_rate"], 36)
        o["work_of_breathing"] = "Severe"
    if respiratory_surface >= 0.70:
        o["spo2"] = min(o["spo2"], 80)
        o["respiratory_rate"] = max(o["respiratory_rate"], 40)
        o["work_of_breathing"] = "Severe"
        if o["mental_status"] == "Alert":
            o["mental_status"] = "Drowsy"


def total_beta_blockade(state):
    """Total active beta-blocker pharmacologic load."""
    h = state["hidden"]
    return max(0.0, h.get("metoprolol_effect", 0.0) + h.get("propranolol_effect", 0.0))


def beta_av_nodal_effect(state):
    """
    Saturable AV-nodal component.
    Repeated dosing continues to increase drug load, but nodal slowing has
    diminishing returns and may plateau while myocardial depression continues.
    """
    load = total_beta_blockade(state)
    return 1.0 - math.exp(-0.95 * load)


def beta_myocardial_depression(state):
    """
    Progressive myocardial beta effect.

    AV-nodal slowing is saturable, but myocardial depression continues to increase
    with active cumulative beta-blocker exposure. Thus additional drug can worsen
    SV/CO even when ventricular rate changes very little.
    """
    load = max(0.0, total_beta_blockade(state))
    depression = 0.48 * (1.0 - math.exp(-0.58 * load)) + 0.035 * (load ** 1.45)
    return clamp(depression, 0.0, 0.96)


def total_av_nodal_suppression(state):
    h = state["hidden"]
    beta = beta_av_nodal_effect(state)
    dilt = h.get("diltiazem_effect", 0.0)
    amio = h.get("amiodarone_effect", 0.0)
    return max(0.0, beta + 0.90 * dilt + 0.35 * amio)


def af_substrate(state):
    """Current propensity to sustain/re-trigger AF from evolving physiology."""
    h = state["hidden"]
    perfusion_deficit = 1.0 - h["tissue_perfusion"]
    volume_deficit = 1.0 - h["effective_volume"]
    congestion = h["pulmonary_congestion"]
    return clamp(
        0.38 * h["inflammatory_drive"]
        + 0.32 * h["sympathetic_drive"]
        + 0.14 * perfusion_deficit
        + 0.08 * volume_deficit
        + 0.08 * congestion
    )


def af_ventricular_rate(state):
    """
    Ventricular response during AF. The rate is generated from current physiology
    plus active AV-nodal blockade, not from a fixed drug-dose lookup table.
    """
    h = state["hidden"]
    blockade = total_av_nodal_suppression(state)
    substrate = af_substrate(state)

    unblocked_target = (
        88
        + 56 * h["sympathetic_drive"]
        + 24 * h["inflammatory_drive"]
        + 20 * substrate
    )
    # Cumulative AV-nodal suppression with diminishing returns.
    # There is no artificial ~115 bpm floor: repeated beta blockade can continue
    # to slow ventricular response, while the coupled state engine simultaneously
    # applies increasing contractility/output costs.
    av_suppression = 104 * (1.0 - math.exp(-1.20 * blockade))
    target = unblocked_target - av_suppression
    return int(round(max(35, min(175, target))))


def advance_beta_pharmacodynamics(state, minutes=1):
    """
    One-compartment educational pharmacodynamic model with an effect-site onset.

    Drug initially enters a 'depot/effect-site input' and progressively transfers
    into active beta blockade. Active effect then decays more slowly. This creates
    onset -> peak -> decay instead of an instantaneous permanent HR decrement.
    """
    if minutes <= 0:
        return

    h = state["hidden"]
    o = state["observable"]

    for _ in range(int(minutes)):
        prior_active = total_beta_blockade(state)

        # Effect-site onset half-times (minutes), deliberately simplified.
        met_abs = math.exp(-math.log(2) / 3.5)
        prop_abs = math.exp(-math.log(2) / 3.0)

        old_met_depot = h.get("metoprolol_depot", 0.0)
        old_prop_depot = h.get("propranolol_depot", 0.0)

        new_met_depot = old_met_depot * met_abs
        new_prop_depot = old_prop_depot * prop_abs

        met_transfer = old_met_depot - new_met_depot
        prop_transfer = old_prop_depot - new_prop_depot

        h["metoprolol_depot"] = new_met_depot
        h["propranolol_depot"] = new_prop_depot

        # Effect half-lives are longer than onset.
        h["metoprolol_effect"] = (
            h.get("metoprolol_effect", 0.0) * math.exp(-math.log(2) / 60.0)
            + met_transfer
        )
        h["propranolol_effect"] = (
            h.get("propranolol_effect", 0.0) * math.exp(-math.log(2) / 90.0)
            + 1.08 * prop_transfer
        )

        h["metoprolol_effect"] = clamp(h["metoprolol_effect"], 0.0, 3.60)
        h["propranolol_effect"] = clamp(h["propranolol_effect"], 0.0, 3.60)

        # Diltiazem effect-site onset/decay.
        old_dilt_depot = h.get("diltiazem_depot", 0.0)
        dilt_abs = math.exp(-math.log(2) / 3.0)
        new_dilt_depot = old_dilt_depot * dilt_abs
        dilt_transfer = old_dilt_depot - new_dilt_depot
        h["diltiazem_depot"] = new_dilt_depot
        h["diltiazem_effect"] = clamp(
            h.get("diltiazem_effect", 0.0) * math.exp(-math.log(2) / 80.0) + dilt_transfer,
            0.0, 1.55
        )

        # Amiodarone has slower onset and long persistence.
        old_amio_depot = h.get("amiodarone_depot", 0.0)
        amio_abs = math.exp(-math.log(2) / 9.0)
        new_amio_depot = old_amio_depot * amio_abs
        amio_transfer = old_amio_depot - new_amio_depot
        h["amiodarone_depot"] = new_amio_depot
        h["amiodarone_effect"] = clamp(
            h.get("amiodarone_effect", 0.0) * math.exp(-math.log(2) / 240.0) + amio_transfer,
            0.0, 1.60
        )

        current_active = total_beta_blockade(state)
        rising_effect = max(0.0, current_active - prior_active)

        # Hemodynamic cost evolves as blockade comes on, especially when the patient
        # is still dependent on sympathetic compensation.
        if rising_effect > 0:
            perfusion_deficit = 1.0 - h["tissue_perfusion"]
            sympathetic_dependence = clamp(
                0.55 * h["sympathetic_drive"] + 0.45 * perfusion_deficit
            )
            pressure_cost = 10.0 * rising_effect * sympathetic_dependence
            perfusion_cost = 0.055 * rising_effect * sympathetic_dependence

            o["sbp"] = max(55, int(round(o["sbp"] - pressure_cost)))
            o["dbp"] = max(30, int(round(o["dbp"] - 0.55 * pressure_cost)))
            h["tissue_perfusion"] = clamp(h["tissue_perfusion"] - perfusion_cost)
            h["sympathetic_drive"] = clamp(
                h["sympathetic_drive"] - 0.045 * rising_effect
            )

        # Diltiazem can produce additional vasodilation/negative inotropy as effect rises.
        dilt = h.get("diltiazem_effect", 0.0)
        prior_dilt = max(0.0, dilt - dilt_transfer)
        dilt_rise = max(0.0, dilt - prior_dilt)
        if dilt_rise > 0:
            vulnerability = clamp(
                0.55 * (1.0 - h["tissue_perfusion"])
                + 0.45 * (1.0 - h["vasomotor_tone"])
            )
            pressure_cost = 9.0 * dilt_rise * (0.45 + vulnerability)
            o["sbp"] = max(55, int(round(o["sbp"] - pressure_cost)))
            o["dbp"] = max(30, int(round(o["dbp"] - 0.55 * pressure_cost)))
            h["tissue_perfusion"] = clamp(h["tissue_perfusion"] - 0.035 * dilt_rise * vulnerability)


def update_dynamic_rhythm(state, minutes=1):
    """
    Longitudinal rhythm evolution.

    Successful cardioversion creates a persistent sinus state. Recurrence requires
    both persistent AF substrate and erosion of post-conversion electrical stability.
    This prevents later interventions from silently resetting the rhythm to baseline.
    """
    if minutes <= 0:
        return

    h = state["hidden"]
    o = state["observable"]

    if h.get("cardiac_arrest"):
        return

    if o["rhythm"] == "Sinus rhythm" and h.get("minutes_since_cardioversion") is not None:
        h["minutes_since_cardioversion"] += minutes

        substrate = af_substrate(state)
        blockade = total_beta_blockade(state)

        # Electrical stability erodes faster when the underlying substrate remains
        # severe, and more slowly when the patient is physiologically improving.
        stability = h.get("sinus_stability", 1.0)
        destabilizing_drive = clamp(
            0.20
            + 0.62 * substrate
            + 0.20 * h.get("inflammatory_drive", 0.0)
            - 0.12 * min(blockade, 1.0),
            0.0,
            1.2,
        )
        stability -= 0.010 * destabilizing_drive * minutes
        h["sinus_stability"] = clamp(stability, 0.0, 1.0)

        excess_substrate = max(0.0, substrate - 0.52)
        recurrence_drive = clamp(
            excess_substrate
            * (1.0 - h["sinus_stability"])
            * (0.75 + 0.35 * h.get("inflammatory_drive", 0.0)),
            0.0,
            1.0,
        )
        h["af_recurrence_pressure"] = clamp(
            h.get("af_recurrence_pressure", 0.0)
            + 0.035 * recurrence_drive * minutes,
            0.0,
            1.0,
        )

        # Recurrence is state-thresholded rather than an isolated random minute.
        if (
            h["minutes_since_cardioversion"] >= 10
            and h["sinus_stability"] < 0.40
            and h["af_recurrence_pressure"] >= 0.55
            and substrate > 0.66
        ):
            o["rhythm"] = "AF"
            h["af_burden"] = clamp(0.48 + 0.32 * substrate)
            o["hr"] = af_ventricular_rate(state)
            h["minutes_since_cardioversion"] = None
            h["af_recurrence_pressure"] = 0.0
            h["sinus_stability"] = 0.0
        else:
            # Sinus rate remains dynamic with current sympathetic drive / blockade.
            nodal = total_av_nodal_suppression(state)
            target = 76 + 24 * h["sympathetic_drive"] - 22 * nodal
            o["hr"] = int(round(0.72 * o["hr"] + 0.28 * clamp(target, 50, 120)))

    elif o["rhythm"] == "AF":
        target = af_ventricular_rate(state)
        o["hr"] = int(round(0.72 * o["hr"] + 0.28 * target))

        amio = h.get("amiodarone_effect", 0.0)
        if amio > 0.18:
            substrate = af_substrate(state)
            conversion_hazard = clamp(
                0.010 + 0.075 * amio * max(0.15, 1.0 - substrate),
                0.0, 0.12
            )
            if rng().random() < conversion_hazard:
                o["rhythm"] = "Sinus rhythm"
                h["af_burden"] = 0.08
                h["minutes_since_cardioversion"] = 0
                h["af_recurrence_pressure"] = 0.0
                h["sinus_stability"] = 0.75
                nodal = total_av_nodal_suppression(state)
                sinus_target = 78 + 20 * h["sympathetic_drive"] - 22 * nodal
                o["hr"] = int(round(max(50, min(110, sinus_target))))

    elif o["rhythm"] == "Sinus rhythm":
        # Sinus tachycardia must remain longitudinally responsive even when it
        # did not follow cardioversion. The prior engine left PS002 fixed at
        # 124/min for the entire encounter. This target combines inflammatory
        # drive, compensatory tone, low-flow burden, and active catecholamine
        # support, with conservative smoothing to avoid implausible jumps.
        nodal = total_av_nodal_suppression(state)
        low_flow = clamp(h.get("low_flow_burden", 0.0), 0.0, 1.0)
        dobutamine = dobutamine_normalized(state)
        norepi = norepinephrine_normalized(state)
        target = (
            88
            + 25 * h.get("sympathetic_drive", 0.0)
            + 15 * h.get("inflammatory_drive", 0.0)
            + 10 * low_flow
            + 3 * (dobutamine / (1.0 + dobutamine))
            + 2 * (norepi / (1.0 + norepi))
            - 22 * nodal
        )
        o["hr"] = int(round(0.82 * o["hr"] + 0.18 * clamp(target, 50, 145)))


def norepinephrine_normalized(state):
    tr = state["treatments"]
    if not tr.get("norepinephrine"):
        return 0.0
    rate = tr.get("norepinephrine_rate", 0.0) or 0.0
    units = tr.get("norepinephrine_units")
    if units == "mcg/kg/min":
        return clamp(rate / 0.10, 0.0, 5.0)
    return clamp(rate / 10.0, 0.0, 5.0)


def dobutamine_normalized(state):
    tr = state["treatments"]
    if not tr.get("dobutamine"):
        return 0.0
    rate = tr.get("dobutamine_rate", 0.0) or 0.0
    # 5 mcg/kg/min = 1.0 normalized. Supports approximately 2.5-20.
    return clamp(rate / 5.0, 0.0, 4.0)


def oxygen_support_fraction(state):
    tr = state["treatments"]
    support = 0.0

    if tr.get("oxygen"):
        flow = tr.get("oxygen_flow_lpm", 0.0) or 0.0
        device = tr.get("oxygen_device") or "Nasal cannula"
        if device == "Non-rebreather mask":
            support = max(support, clamp(0.75 + 0.02 * min(flow, 15.0), 0.0, 1.0))
        elif device == "Simple face mask":
            support = max(support, clamp(0.30 + 0.055 * flow, 0.0, 0.80))
        else:
            support = max(support, clamp(0.08 + 0.075 * flow, 0.0, 0.60))

    if tr.get("niv"):
        pressure = tr.get("niv_pressure_cmh2o", 0.0) or 0.0
        fio2 = tr.get("niv_fio2_percent")
        base_fio = clamp(((fio2 or 40.0) - 21.0) / 79.0, 0.0, 1.0)
        niv_support = clamp(0.30 + 0.32 * base_fio + 0.030 * pressure, 0.35, 1.0)
        support = max(support, niv_support)

    if tr.get("invasive_ventilation"):
        fio2 = tr.get("ventilator_fio2_percent") or 40.0
        peep = tr.get("ventilator_peep_cmh2o") or 5.0
        base_fio = clamp((fio2 - 21.0) / 79.0, 0.0, 1.0)
        support = max(support, clamp(0.78 + 0.42 * base_fio + 0.025 * peep, 0.85, 1.45))

    return support


def recompute_coupled_physiology(state, elapsed_min=1):
    """
    Central Clinical State Engine.

    Treatments primarily modify hidden physiology. Observable BP, perfusion,
    oxygenation, and rate are then re-derived from the *current coupled state*.
    This prevents one intervention from simply overwriting another intervention's
    output and makes sequence/context matter.
    """
    h = state["hidden"]
    o = state["observable"]

    if h.get("cardiac_arrest"):
        return

    # ---- Vascular state ----
    norepi = norepinephrine_normalized(state)
    # v0.6.0.9: preserve a monotonic pressor dose-response through high-dose norepinephrine.
    # Previous code capped normalized norepinephrine at 3.0, so 0.3 and 0.4 mcg/kg/min
    # produced the same vascular support while the underlying low-flow state continued
    # to deteriorate. That could make BP fall after a dose increase. Use a saturating
    # but still increasing curve instead; pressure support rises at each clinically
    # meaningful step without treating vasoconstriction as increased cardiac output.
    exogenous_vascular_support = 0.30 * (norepi / (1.0 + 0.18 * norepi))
    nitrate_effect = h.get("nitroglycerin_effect", 0.0) if state["treatments"].get("nitroglycerin") else 0.0
    dobutamine_effect = h.get("dobutamine_effect", 0.0)
    procedural_sedation_effect = h.get("procedural_sedation_effect", 0.0)
    # Beta-1 inotropy with a modest beta-2 vasodilatory component. The latter means
    # dobutamine can improve flow while leaving MAP unchanged or slightly lower.
    # v0.6.0.13: dobutamine is primarily an inotrope, with enough beta-2
    # vasodilation to prevent recruited flow from behaving like an added pressor.
    dobutamine_vasodilation = 0.060 * (dobutamine_effect / (1.0 + 0.35 * dobutamine_effect))
    vascular_support = clamp(
        h["vasomotor_tone"]
        + exogenous_vascular_support
        - 0.12 * h["inflammatory_drive"]
        - 0.10 * nitrate_effect
        - dobutamine_vasodilation
        - 0.025 * procedural_sedation_effect
    )
    h["vascular_support"] = vascular_support
    h["pressure_support_state"] = clamp(exogenous_vascular_support - dobutamine_vasodilation, 0.0, 1.0)

    # ---- Rate → filling → stroke volume → forward-flow coupling ----
    rate = max(35, o.get("hr", 90))
    is_af = o.get("rhythm") == "AF"
    if dobutamine_effect > 0 and not is_af:
        chronotropic_target = clamp(rate + 7.0 * (dobutamine_effect / (1.0 + 0.6 * dobutamine_effect)), 50, 135)
        o["hr"] = int(round(0.82 * rate + 0.18 * chronotropic_target))
        rate = max(35, o["hr"])

    # Diastolic filling is explicitly rate-dependent. Very rapid rates shorten
    # filling time; excessive rate control can also reduce total forward flow.
    # AF carries an additional filling penalty from loss of coordinated atrial
    # contribution. The curve is intentionally broad rather than a single optimum.
    if rate >= 170:
        rate_fill = 0.52
    elif rate >= 150:
        rate_fill = 0.52 + (170 - rate) * 0.009
    elif rate >= 120:
        rate_fill = 0.70 + (150 - rate) * 0.007
    elif rate >= 80:
        rate_fill = 0.91 + (120 - rate) * 0.002
    elif rate >= 55:
        rate_fill = 0.99 - (80 - rate) * 0.004
    else:
        rate_fill = max(0.62, 0.89 - (55 - rate) * 0.010)

    atrial_factor = 0.90 if is_af else 1.0
    filling_efficiency = clamp(rate_fill * atrial_factor, 0.45, 1.02)
    h["diastolic_filling_efficiency"] = filling_efficiency

    congestion_penalty = 0.34 * h["pulmonary_congestion"]
    update_fluid_phenotype(state)

    # v0.6.0.2: retained intravascular crystalloid continues to contribute to
    # filling even after preload responsiveness has begun to saturate. This keeps
    # later boluses physiologically present without making them equally effective.
    retained_fluid = h.get("effective_intravascular_fluid", 0.0)
    base_preload = h["effective_volume"] * (1.0 - 0.38 * h["pulmonary_congestion"])
    preload_response = h.get(
        "preload_responsiveness",
        fluid_responsiveness(h["effective_volume"])
    )
    retained_preload = retained_fluid * (0.18 + 0.20 * preload_response)
    preload = clamp(base_preload + retained_preload, 0.05, 1.0)
    h["preload_state"] = preload

    # v0.8.18: preserve the observable early contribution of an actively retained
    # crystalloid bolus when the patient is still preload responsive and not
    # congested. The prior engine let falling contractile reserve erase the entire
    # short-term fluid signal, so a responsive 2000 mL bolus followed by a requested
    # 5-minute check could look identical to 18 minutes of untreated deterioration.
    # This term is bounded by retained fluid and current responsiveness, decays as
    # fluid redistributes, and disappears on the flat/right side of the curve.
    preload_reserve = clamp((0.75 - preload) / 0.25, 0.0, 1.0)
    shock_recruitment_window = clamp(
        (0.24 - h.get("tissue_perfusion", 0.0)) / 0.12,
        0.0,
        1.0,
    )
    acute_preload_recruitment = clamp(
        retained_fluid
        * preload_response
        * preload_reserve
        * shock_recruitment_window
        * clamp(1.0 - 1.4 * h.get("pulmonary_congestion", 0.0), 0.0, 1.0),
        0.0,
        0.22,
    )
    h["acute_preload_recruitment"] = acute_preload_recruitment

    # Smooth Frank-Starling contribution: preload matters most while reserve remains.
    preload_contribution = clamp(
        0.48 + 0.78 * preload - 0.22 * (preload ** 2)
    )
    filling = clamp(
        preload_contribution
        * (0.76 + 0.32 * filling_efficiency)
        * (0.90 + 0.10 * preload_response)
    )

    # Beta blockade has two competing effects: at extreme tachycardia it may
    # improve filling and stroke volume through rate control, but it also carries
    # a direct negative-inotropic cost. Therefore metoprolol is not intrinsically
    # pressor, and excessive blockade can reduce flow.
    beta_blockade = total_beta_blockade(state)
    beta_inotropy_penalty = beta_myocardial_depression(state)

    reserve = h.get("contractile_reserve", 1.0)
    overload = max(0.0, beta_inotropy_penalty - 0.28)
    # v0.6.0.32: once a starting norepinephrine infusion has restored usable
    # perfusion pressure, do not continue the same unconditional myocardial-reserve
    # decay that drives untreated shock. This represents stabilization/coronary and
    # venous-pressure recruitment, not direct inotropy; reserve can still fall if
    # pressure is inadequate or at higher pressor doses.
    pressor_preserving = (
        0.5 <= norepi <= 1.5
        and ((o.get("sbp", 0) + 2.0 * o.get("dbp", 0)) / 3.0) >= 62
    )
    base_reserve_loss = 0.003 if pressor_preserving else 0.020
    reserve_loss = (base_reserve_loss + 0.050 * overload) * max(elapsed_min, 1)
    reserve_recovery = 0.010 * max(0.0, 0.22 - beta_inotropy_penalty) * max(elapsed_min, 1)
    h["contractile_reserve"] = clamp(reserve - reserve_loss + reserve_recovery, 0.06, 1.0)

    # Inotropic support augments effective contractility without erasing the underlying
    # myocardial disease state. The response saturates and develops over time.
    # v0.6.0.13: moderate, saturating contractile recruitment. This preserves a
    # clinically useful forward-flow effect without producing an abrupt CO jump.
    inotrope_gain = 0.68 * (dobutamine_effect / (1.0 + 0.55 * dobutamine_effect))
    effective_contractility = clamp(h["contractile_reserve"] + inotrope_gain, 0.06, 1.35)
    # Preserve the current effective contractile state for learner-requested
    # imaging. Base cardiac_function is a patient phenotype; it must not make a
    # later POCUS ignore acquired low-output physiology or inotropic recruitment.
    h["effective_contractility"] = effective_contractility

    rhythm_penalty = (0.055 + 0.075 * h.get("af_burden", 0.0)) if is_af else 0.0
    if h.get("rhythm_coupling_v2"):
        rhythm_penalty *= clamp(h.get("af_causal_weight", 0.25) / 0.25, 0.0, 3.0)

    # Afterload can support pressure while opposing stroke volume at high vascular tone.
    high_pressor_afterload = 0.055 * max(0.0, norepi - 2.5)
    afterload = clamp(
        0.55 + 0.75 * vascular_support - 0.12 * nitrate_effect
        + high_pressor_afterload - 0.075 * dobutamine_effect,
        0.38,
        1.48
    )
    h["afterload_factor"] = afterload
    afterload_efficiency = clamp(1.14 - 0.28 * max(0.0, afterload - 0.82), 0.72, 1.12)

    # Right side of the fluid-response curve:
    # once effective filling is excessive, added preload no longer raises SV and
    # may progressively impair effective forward flow through hydrostatic burden.
    overfill_burden = h.get("overfill_burden", 0.0)
    overfill_penalty = clamp(
        0.22 * max(0.0, preload - 0.78)
        + 0.26 * overfill_burden
        + 0.10 * max(0.0, h["pulmonary_congestion"] - 0.30),
        0.0,
        0.42,
    )

    stroke_eff = clamp(
        h["cardiac_function"]
        * effective_contractility
        * (0.52 + 0.70 * filling)
        * (0.82 + 0.22 * filling_efficiency)
        * afterload_efficiency
        * (1.0 - rhythm_penalty - congestion_penalty - overfill_penalty)
        * max(0.02, 1.0 - beta_inotropy_penalty)
    )
    h["stroke_volume_efficiency"] = stroke_eff

    # Rate contribution to CO is non-monotonic: tachycardia initially supports
    # minute output, but extreme rates become inefficient because filling collapses;
    # bradycardia eventually lowers output despite a larger stroke volume.
    if rate < 55:
        rate_output = 0.55 + 0.008 * max(rate - 35, 0)
    elif rate <= 110:
        rate_output = 0.71 + 0.0053 * (rate - 55)
    elif rate <= 140:
        rate_output = 1.00 - 0.003 * (rate - 110)
    else:
        rate_output = 0.91 - 0.0065 * (rate - 140)
    rate_output = clamp(rate_output, 0.48, 1.02)
    h["rate_output_efficiency"] = rate_output

    cardiac_output = clamp(
        stroke_eff * rate_output * (0.80 + 0.26 * h["sympathetic_drive"])
        + 0.70 * acute_preload_recruitment
    )
    h["cardiac_output_index"] = cardiac_output
    h["forward_flow_state"] = cardiac_output

    burden = h.get("low_flow_burden", 0.0)
    if cardiac_output < 0.30:
        burden += (0.30 - cardiac_output) * 0.11 * max(elapsed_min, 1)
    else:
        burden -= 0.025 * max(elapsed_min, 1)

    # Once a usable perfusion pressure has been restored, accumulated low-flow
    # injury should wash out gradually rather than remain permanently latched.
    # This does NOT equate MAP with recovery: meaningful clearance requires at
    # least some forward flow, and severe low output can still keep burden high.
    current_map = (state["observable"]["sbp"] + 2 * state["observable"]["dbp"]) / 3.0
    flow_recovery_threshold = 0.34
    if current_map >= 65 and cardiac_output >= flow_recovery_threshold:
        h["adequate_perfusion_minutes"] = min(30.0, h.get("adequate_perfusion_minutes", 0.0) + max(elapsed_min, 1))
        inotrope_clearance = 0.024 * clamp(dobutamine_effect / 1.0, 0.0, 1.5)
        burden -= (
            0.006
            + 0.016 * clamp((current_map - 65.0) / 15.0)
            + 0.050 * clamp((cardiac_output - flow_recovery_threshold) / 0.24)
            + inotrope_clearance
        ) * max(elapsed_min, 1)
    elif current_map < 60 or cardiac_output < 0.18:
        h["adequate_perfusion_minutes"] = max(0.0, h.get("adequate_perfusion_minutes", 0.0) - 2.0 * max(elapsed_min, 1))
    else:
        h["adequate_perfusion_minutes"] = max(0.0, h.get("adequate_perfusion_minutes", 0.0) - 0.5 * max(elapsed_min, 1))
    h["low_flow_burden"] = clamp(burden, 0.0, 1.25)

    # Global perfusion depends more on flow/filling than on pressure alone.
    # Vasopressor support can restore perfusion pressure, but high vascular tone is
    # not treated as equivalent to increased forward flow.
    low_output_drag = (
        0.24 * max(0.0, 0.30 - cardiac_output)
        + 0.26 * h.get("low_flow_burden", 0.0)
    )

    recovery_minutes = h.get("adequate_perfusion_minutes", 0.0)
    # Sustained adequate pressure permits delayed microcirculatory recruitment,
    # but only when there is enough forward flow to use that pressure. The bonus
    # ramps over ~10 minutes and is intentionally modest.
    pressure_recovery_bonus = (
        0.12
        * clamp(recovery_minutes / 10.0)
        * clamp((cardiac_output - 0.30) / 0.28)
    )
    # v0.6.0.12: when an inotrope has actually recruited forward flow and pressure
    # is usable, tissue perfusion receives an additional delayed recruitment signal.
    # This is flow-dependent, not a direct MAP shortcut.
    inotrope_flow_recruitment = 0.0
    if current_map >= 62 and dobutamine_effect > 0.15 and cardiac_output >= 0.32:
        inotrope_flow_recruitment = (
            0.12
            * clamp(dobutamine_effect / 1.0, 0.0, 1.4)
            * clamp((cardiac_output - 0.30) / 0.28, 0.0, 1.0)
            * clamp((recovery_minutes + 2.0) / 12.0, 0.0, 1.0)
        )

    perfusion_target = clamp(
        0.04
        + 0.24 * filling
        + 0.07 * vascular_support
        + 0.64 * cardiac_output
        + pressure_recovery_bonus
        + inotrope_flow_recruitment
        + 0.70 * acute_preload_recruitment
        + 1.10 * retained_fluid * h.get("vasoplegia_severity", 0.0)
        # v0.6.0.31: low/moderate norepinephrine can recruit tissue perfusion
        # indirectly when it restores a usable perfusion pressure in a patient
        # whose forward flow is not profoundly depressed. This is deliberately
        # modest and conditional: norepinephrine is not a direct flow surrogate.
        + (
            0.11 * (norepi / (0.50 + norepi))
            * clamp((current_map - 55.0) / 15.0, 0.0, 1.0)
            * clamp((cardiac_output - 0.24) / 0.22, 0.0, 1.0)
        )
        - 0.17 * h["inflammatory_drive"]
        - 0.32 * h.get("vasoplegia_severity", 0.0)
        - 0.20 * h["pulmonary_congestion"]
        - low_output_drag
    )

    # Tissue perfusion moves toward the coupled target rather than jumping.
    alpha = clamp(0.18 * max(elapsed_min, 1), 0.18, 0.55)
    # Pressure may recover before microcirculatory flow. With substantial norepinephrine
    # and persistent low output, deliberately slow upward perfusion recovery; worsening
    # perfusion is never delayed by this rule.
    if perfusion_target > h["tissue_perfusion"] and norepi >= 2.0 and cardiac_output < 0.34:
        alpha *= 0.42
    elif perfusion_target > h["tissue_perfusion"] and dobutamine_effect > 0.20 and cardiac_output >= 0.34:
        # Forward-flow rescue recruits tissue perfusion over several reassessments,
        # not instantaneously.
        alpha *= 1.20
    h["tissue_perfusion"] = clamp(
        h["tissue_perfusion"] + alpha * (perfusion_target - h["tissue_perfusion"])
    )

    # v0.6.0.32: a clinically effective *starting* norepinephrine infusion may
    # restore perfusion pressure before it restores normal microcirculatory flow,
    # but it should not produce a deterministic peripheral/cerebral collapse solely
    # because untreated inflammatory physiology continues to drift during the same
    # 10-minute reassessment. When MAP is usable and forward flow is at least
    # marginal, preserve a low-but-viable tissue-perfusion floor. This is a
    # stabilization rule, not a cure: CRT can remain prolonged and the patient may
    # remain cool/drowsy. Higher pressor doses and profound low-output states do not
    # receive this floor.
    if 0.5 <= norepi <= 1.5 and current_map >= 62 and cardiac_output >= 0.18:
        h["tissue_perfusion"] = max(h["tissue_perfusion"], 0.24)

    # ---- Endogenous compensatory drive ----
    sympathetic_ceiling = clamp(
        1.0 - 0.42 * h.get("low_flow_burden", 0.0) - 0.22 * beta_inotropy_penalty,
        0.34, 1.0
    )
    sympathetic_target = clamp(
        0.34
        + 0.34 * h["inflammatory_drive"]
        + 0.38 * (1.0 - h["tissue_perfusion"])
        + 0.035 * norepi,
        0.0,
        sympathetic_ceiling
    )
    h["sympathetic_drive"] = clamp(
        h["sympathetic_drive"] + 0.10 * (sympathetic_target - h["sympathetic_drive"])
    )

    # ---- Blood pressure derived from coupled physiology ----
    # The untreated PS001 physiology trends toward its prior pressure equilibrium,
    # while the learner-visible case now deliberately enters at 90/54 mmHg.
    low_output_penalty = (
        44.0 * max(0.0, 0.32 - cardiac_output)
        + 24.0 * h.get("low_flow_burden", 0.0)
    )

    # v0.6.0.9: explicit pressure component from the active norepinephrine dose.
    # This is intentionally a PRESSURE effect, not a flow/perfusion effect. It keeps
    # dose escalation monotonic while CRT/mottling can remain abnormal in low-output shock.
    # v0.6.0.28: a clinically meaningful starting norepinephrine infusion must
    # exert a clear positive arterial-pressure effect even when the underlying
    # low-output/inflammatory state is still deteriorating. The prior quadratic
    # curve contributed only ~3.5 mmHg at 0.1 mcg/kg/min (normalized=1), allowing
    # natural decline to overwhelm the pressor signal during a 10-minute
    # reassessment. This saturating term is stronger at low/moderate doses, converges toward the prior high-dose effect, and is
    # monotonic. It changes PRESSURE only: forward flow and tissue
    # perfusion remain independently derived and may stay abnormal.
    norepi_pressure_bonus = 21.0 * norepi / (0.25 + norepi)

    # Offset the pressure generated indirectly by increased stroke volume: dobutamine
    # may leave MAP similar or slightly lower rather than acting as a second pressor.
    dobutamine_map_offset = 38.0 * (dobutamine_effect / (1.0 + 0.55 * dobutamine_effect))
    map_target = (
        73.0
        + 42.0 * (vascular_support - 0.298)
        + norepi_pressure_bonus
        - dobutamine_map_offset
        + 16.0 * (filling - 0.340)
        + 34.0 * (cardiac_output - 0.455)
        + 110.0 * acute_preload_recruitment
        + 190.0 * retained_fluid * h.get("vasoplegia_severity", 0.0)
        - 12.0 * (h["pulmonary_congestion"] - 0.05)
        - 40.0 * h.get("vasoplegia_severity", 0.0)
        - low_output_penalty
    )
    pulse_pressure = (
        40.0
        + 17.0 * (stroke_eff - 0.49)
        + 7.0 * (h["sympathetic_drive"] - 0.85)
        - 10.0 * (h["pulmonary_congestion"] - 0.05)
    )
    map_target = max(18.0, min(125.0, map_target))
    pulse_pressure = max(20.0, min(65.0, pulse_pressure))

    target_sbp = map_target + 0.67 * pulse_pressure
    target_dbp = map_target - 0.33 * pulse_pressure
    # Smooth observed pressure minute-to-minute.
    pressure_alpha = 0.34 + 0.24 * clamp(h.get("low_flow_burden", 0.0), 0.0, 1.0)
    o["sbp"] = max(28, int(round(o["sbp"] + pressure_alpha * (target_sbp - o["sbp"]))))
    o["dbp"] = max(15, int(round(o["dbp"] + pressure_alpha * (target_dbp - o["dbp"]))))
    h["effective_map"] = (o["sbp"] + 2.0 * o["dbp"]) / 3.0

    # ---- Oxygenation derived from pulmonary state + support ----
    support = oxygen_support_fraction(state)
    pulmonary_signal = pulmonary_clinical_signal(state)
    respiratory_burden = clamp(
        max(
            0.62 * pulmonary_signal
            + 0.38 * h["pulmonary_congestion"]
            + 0.48 * h["respiratory_failure_severity"],
            0.82 * h.get("primary_respiratory_burden", 0.0),
            0.10 * procedural_sedation_effect,
        )
    )
    target_spo2 = 94.0 - 16.0 * respiratory_burden + 7.0 * support
    target_spo2 = max(72.0, min(100.0, target_spo2))
    o["spo2"] = int(round(o["spo2"] + 0.45 * (target_spo2 - o["spo2"])))

    # ---- Oxygen delivery index (not shown to learner) ----
    h["oxygen_delivery"] = clamp(
        h["tissue_perfusion"] * (o["spo2"] / 100.0) * (0.70 + 0.35 * cardiac_output)
    )

    # ---- Observable perfusion surfaces ----
    update_perfusion_surface(state)

    # Cerebral status follows sustained low flow / oxygen delivery rather than BP alone.
    # This lets severe myocardial depression eventually produce clinically visible
    # deterioration even if MAP has not yet collapsed.
    neuro_burden = h.get("low_flow_burden", 0.0)
    recovery_minutes = h.get("adequate_perfusion_minutes", 0.0)
    current_map = (o["sbp"] + 2.0 * o["dbp"]) / 3.0

    # v0.6.0.19: severe *current* hypotension is an immediate cerebral danger
    # signal. Pressure is still not used as a shortcut for neurologic recovery,
    # but a patient cannot remain fully Alert through profound shock simply
    # because the slower low-flow burden integrator has not yet caught up.
    # The pressure thresholds therefore only accelerate DETERIORATION.
    if (current_map < 32 or o["sbp"] < 55) or h["oxygen_delivery"] < 0.070 or h["tissue_perfusion"] < 0.070 or neuro_burden >= 0.82:
        desired_mental = "Unresponsive"
    elif (current_map < 45 or o["sbp"] < 70) or h["oxygen_delivery"] < 0.115 or h["tissue_perfusion"] < 0.115 or neuro_burden >= 0.55:
        desired_mental = "Obtunded"
    elif (current_map < 55 or o["sbp"] < 85) or h["oxygen_delivery"] < 0.19 or h["tissue_perfusion"] < 0.20 or neuro_burden >= 0.30:
        desired_mental = "Drowsy"
    elif h["oxygen_delivery"] >= 0.26 and h["tissue_perfusion"] >= 0.28 and neuro_burden < 0.18:
        desired_mental = "Alert"
    else:
        desired_mental = o["mental_status"]

    # v0.6.0.14: neurologic recovery deliberately lags hemodynamic and peripheral
    # perfusion recovery. A restored MAP or improving CRT is not enough by itself:
    # the brain must see sustained forward flow and oxygen delivery before the
    # observable mental-status label advances. Worsening remains immediate.
    cerebral_ok = (
        h["oxygen_delivery"] >= 0.15
        and h["tissue_perfusion"] >= 0.20
        and cardiac_output >= 0.30
        and o["spo2"] >= 84
    )
    if cerebral_ok:
        h["cerebral_recovery_minutes"] = min(60.0, h.get("cerebral_recovery_minutes", 0.0) + 1.0)
    else:
        h["cerebral_recovery_minutes"] = max(0.0, h.get("cerebral_recovery_minutes", 0.0) - 1.5)

    if state.get("treatments", {}).get("invasive_ventilation"):
        # Sedation is an intervention state, not evidence of worsening cerebral
        # perfusion. Preserve it while invasive ventilation is active; arrest can
        # still override it below.
        o["mental_status"] = "Sedated"
    elif procedural_sedation_effect >= 0.35:
        # Procedural sedation is transient and is not interpreted as neurologic
        # deterioration. Once the effect-site signal decays, ordinary cerebral
        # recovery logic resumes from a drowsy state.
        o["mental_status"] = "Sedated"
    else:
        levels = ["Alert", "Drowsy", "Obtunded", "Unresponsive"]
        # When procedural sedation has just fallen below its active threshold,
        # ``desired_mental`` may still carry the intervention label "Sedated".
        # Resume neurologic physiology from Drowsy instead of indexing a label
        # that intentionally is not part of the perfusion-severity scale.
        if desired_mental not in levels:
            desired_mental = "Drowsy"
        current = o["mental_status"] if o["mental_status"] in levels else "Drowsy"
        if levels.index(desired_mental) > levels.index(current):
            # Deterioration is not delayed.
            o["mental_status"] = desired_mental
        elif levels.index(desired_mental) < levels.index(current):
            cerebral_minutes = h.get("cerebral_recovery_minutes", 0.0)
            # One neurologic level at a time. The first step requires sustained
            # recovery; a fully Alert state requires a longer period of adequate
            # cerebral oxygen delivery than peripheral CRT improvement does.
            if current == "Unresponsive" and cerebral_minutes >= 8:
                o["mental_status"] = "Obtunded"
            elif current == "Obtunded" and cerebral_minutes >= 16:
                o["mental_status"] = "Drowsy"
            elif current == "Drowsy" and cerebral_minutes >= 28:
                o["mental_status"] = "Alert"

    # Extreme low-flow physiology can progress to cardiac arrest. The trigger is
    # state-derived rather than dose-count-derived.
    if (
        h.get("cardiac_output_index", 1.0) < 0.095
        and h["tissue_perfusion"] < 0.095
        and h["oxygen_delivery"] < 0.080
        and o["sbp"] < 65
        and h.get("low_flow_burden", 0.0) >= 0.65
    ):
        h["cardiac_arrest"] = True
        h["terminal_collapse"] = True
        o["pulse_present"] = False
        o["peripheral_perfusion"] = "critical"
        # PEA is organized electrical activity without effective mechanical output.
        # Preserve the electrical ventricular rate at the moment of collapse rather
        # than incorrectly representing PEA as 0/min (which would imply asystole).
        o["hr"] = max(1, int(o.get("hr", 60)))
        o["rhythm"] = "PEA"
        o["sbp"] = 0
        o["dbp"] = 0
        # v0.6.0.16: once pulseless, pulse-dependent bedside measurements are
        # unavailable rather than continuing as ordinary vital signs.
        o["crt"] = None
        o["spo2"] = None
        # Collapse does not erase mottling already documented by the surface.
        # Do not invent mottling when it was not present.
        o["extremities"] = "Mottled/Cold" if o.get("extremities") == "Mottled/Cold" else "Cold"
        o["mental_status"] = "Unresponsive"


def update_perfusion_surface(state):
    h = state["hidden"]
    o = state["observable"]
    prior_extremities = o.get("extremities")

    # CRT/extremity temperature represent PERIPHERAL flow, not MAP alone.
    # Norepinephrine may improve perfusion pressure while simultaneously increasing
    # peripheral vasoconstriction. This deliberately decouples a normal MAP from
    # automatically warm extremities / normal CRT.
    norepi = norepinephrine_normalized(state)
    vascular_support = h.get("vascular_support", h["vasomotor_tone"])
    dob = h.get("dobutamine_effect", 0.0)
    vasoconstriction_penalty = (
        # v0.6.0.31: at a starting dose, pressure recruitment should not by
        # itself force a paradoxical collapse in peripheral flow. Vasoconstriction
        # penalty becomes progressively more important above the initial dose.
        0.025 * clamp(norepi / 1.0, 0.0, 1.0)
        + 0.055 * clamp((norepi - 1.0) / 2.0, 0.0, 1.5)
        + 0.025 * clamp((vascular_support - 0.55) / 0.45, 0.0, 1.0)
    )
    peripheral_flow = clamp(
        0.75 * h["tissue_perfusion"]
        + 0.42 * h.get("cardiac_output_index", 0.0)
        + 0.055 * (dob / (1.0 + 0.35 * dob))
        - vasoconstriction_penalty
        - 0.25 * h.get("vasoplegia_severity", 0.0)
    )
    h["peripheral_flow"] = peripheral_flow
    # Expose the existing flow bands for case-authored visual phenotypes. This
    # does not change physiology and precedes distributive warming of the skin.
    o["peripheral_perfusion"] = (
        "preserved" if peripheral_flow >= 0.70 else
        "mildly impaired" if peripheral_flow >= 0.52 else
        "impaired" if peripheral_flow >= 0.23 else
        "severely impaired" if peripheral_flow >= 0.08 else "critical"
    )

    # v0.6.0.16: CRT responds relatively quickly to current peripheral flow, while
    # extremity temperature has thermal/microcirculatory memory. Sustained forward
    # flow therefore produces a delayed Cool -> Warmer -> Warm recovery instead of
    # leaving the patient indefinitely cold after CRT has improved. Deterioration
    # remains immediate.
    peripheral_recovery_ok = (
        peripheral_flow >= 0.34
        and h.get("cardiac_output_index", 0.0) >= 0.32
        and h.get("tissue_perfusion", 0.0) >= 0.20
    )
    if peripheral_recovery_ok:
        h["peripheral_recovery_minutes"] = min(60.0, h.get("peripheral_recovery_minutes", 0.0) + 1.0)
    else:
        h["peripheral_recovery_minutes"] = max(0.0, h.get("peripheral_recovery_minutes", 0.0) - 2.0)

    recovery = h.get("peripheral_recovery_minutes", 0.0)
    if peripheral_flow >= 0.70:
        o["crt"] = 2
        o["extremities"] = "Warm"
    elif peripheral_flow >= 0.52:
        o["crt"] = 3
        o["extremities"] = "Warm" if recovery >= 24 else "Warmer"
    elif peripheral_flow >= 0.36:
        o["crt"] = 4
        o["extremities"] = "Warmer" if recovery >= 18 else "Cool"
    elif peripheral_flow >= 0.23:
        o["crt"] = 5
        o["extremities"] = "Cool"
    elif peripheral_flow >= 0.14:
        o["crt"] = 6
        o["extremities"] = "Cold"
    elif peripheral_flow >= 0.08:
        o["crt"] = 7
        o["extremities"] = "Very cold"
    else:
        o["crt"] = 8
        o["extremities"] = "Mottled/Cold"

    # v0.6.0.32: "Warmer" is a recovery descriptor, not a lower temperature
    # category than Warm. Never report Warm -> Warmer while CRT/flow are worsening.
    if prior_extremities == "Warm" and o.get("extremities") == "Warmer":
        o["extremities"] = "Warm"
    if h.get("vasoplegia_severity", 0.0) >= 0.60 and peripheral_flow >= 0.23:
        # Distributive shock may remain peripherally warm despite abnormal
        # capillary refill; temperature and microcirculatory transit are not the
        # same observable.
        o["extremities"] = "Warm"


def apply_natural_disease(state, minutes):
    """
    Advance the patient minute-by-minute so observation/reassessment is true
    state evolution, not merely a clock jump plus threshold checks.
    """
    if minutes <= 0:
        return

    # Terminal cardiovascular collapse is an absorbing state in this build.
    # Ordinary reassessment must not resume conventional circulation/vitals.
    if state["hidden"].get("terminal_collapse"):
        return

    whole_minutes = int(round(minutes))

    for _ in range(whole_minutes):
        # Pharmacology evolves continuously with time.
        advance_beta_pharmacodynamics(state, 1)

        # Dobutamine is a longitudinal inotrope: onset builds over several minutes
        # and washout is gradual. It primarily modifies forward flow, not MAP directly.
        h = state["hidden"]
        tr = state["treatments"]
        sedation_effect = h.get("procedural_sedation_effect", 0.0)
        if sedation_effect > 0:
            # Short effect-site decay: the intervention remains visible in the
            # treatment record even after its physiologic effect has waned.
            h["procedural_sedation_effect"] = max(
                0.0,
                sedation_effect * math.exp(-math.log(2) / 4.0),
            )
            h["procedural_sedation_minutes"] = min(
                60.0,
                h.get("procedural_sedation_minutes", 0.0) + 1.0,
            )
        target_dob = dobutamine_normalized(state) if tr.get("dobutamine") else 0.0
        current_dob = h.get("dobutamine_effect", 0.0)
        # v0.6.0.13: slower onset makes perfusion recovery visible over serial
        # reassessments rather than largely completing within the first 10 minutes.
        onset_alpha = 0.20 if target_dob > current_dob else 0.14
        h["dobutamine_effect"] = clamp(current_dob + onset_alpha * (target_dob - current_dob), 0.0, 4.0)
        if tr.get("dobutamine"):
            h["dobutamine_minutes"] = min(120.0, h.get("dobutamine_minutes", 0.0) + 1.0)
        else:
            h["dobutamine_minutes"] = max(0.0, h.get("dobutamine_minutes", 0.0) - 1.0)

        # Retained crystalloid effect redistributes gradually. This preserves a
        # meaningful transient preload effect without making a bolus permanent.
        h = state["hidden"]
        retained = h.get("effective_intravascular_fluid", 0.0)
        if retained > 0:
            redistributed = retained * (1.0 - math.exp(-math.log(2) / 28.0))
            h["effective_intravascular_fluid"] = max(0.0, retained - redistributed)

            # v0.6.0.6: redistributed crystalloid is not physiologically erased.
            # In an inflamed patient, a substantial fraction becomes interstitial/
            # extravascular fluid. This preserves the distinction between waning
            # preload benefit and accumulating hydrostatic/capillary-leak burden.
            leak_fraction = clamp(
                0.62 + 0.28 * h.get("inflammatory_drive", 0.0),
                0.55,
                0.90,
            )
            h["extravascular_fluid_burden"] = clamp(
                h.get("extravascular_fluid_burden", 0.0)
                + redistributed * leak_fraction,
                0.0,
                1.60,
            )

            # Most waning occurs through the retained-fluid compartment itself.
            # Only a smaller component is removed from effective filling.
            h["effective_volume"] = clamp(h["effective_volume"] - 0.22 * redistributed)

        # Extravascular fluid clears much more slowly than useful preload benefit.
        # This prevents a bolus from becoming permanently beneficial while still
        # allowing true overload to resolve over a longer timescale.
        extra = h.get("extravascular_fluid_burden", 0.0)
        if extra > 0:
            extra *= math.exp(-math.log(2) / 180.0)
            h["extravascular_fluid_burden"] = max(0.0, extra)

        # Active IV nitroglycerin primarily unloads the pulmonary circulation and
        # reduces vascular tone/afterload. The hemodynamic benefit is conditional on
        # adequate pressure; at low SBP the same vasodilatory action can worsen perfusion.
        nitro = h.get("nitroglycerin_effect", 0.0)
        if state["treatments"].get("nitroglycerin") and nitro > 0:
            pressure_factor = clamp((state["observable"].get("sbp", 90) - 80.0) / 45.0, 0.0, 1.0)
            h["pulmonary_congestion"] = max(
                0.02,
                h.get("pulmonary_congestion", 0.05) - 0.0045 * nitro * (0.55 + 0.45 * pressure_factor)
            )
            h["preload_state"] = max(0.05, h.get("preload_state", 0.35) - 0.0020 * nitro)
            h["vasomotor_tone"] = clamp(h.get("vasomotor_tone", 0.4) - 0.0017 * nitro)
            if state["observable"].get("sbp", 90) < 90:
                h["tissue_perfusion"] = clamp(h["tissue_perfusion"] - 0.0025 * nitro)

        # NIV improves alveolar recruitment and work of breathing while modestly
        # reducing venous return. It can therefore help pulmonary edema but can be
        # poorly tolerated in a severely preload-dependent/hypotensive patient.
        if state["treatments"].get("niv"):
            pressure = state["treatments"].get("niv_pressure_cmh2o", 0.0) or 0.0
            niv_strength = clamp(pressure / 10.0, 0.0, 1.4)
            h["respiratory_failure_severity"] = max(
                0.0,
                h.get("respiratory_failure_severity", 0.0) - 0.010 * niv_strength
            )
            h["pulmonary_congestion"] = max(
                0.02,
                h.get("pulmonary_congestion", 0.05) - 0.0025 * niv_strength
            )
            if state["observable"].get("sbp", 90) < 90:
                h["effective_volume"] = clamp(h["effective_volume"] - 0.0015 * niv_strength)

        if state["treatments"].get("invasive_ventilation"):
            peep = state["treatments"].get("ventilator_peep_cmh2o", 5.0) or 5.0
            vent_strength = clamp(peep / 10.0, 0.4, 1.4)
            h["respiratory_failure_severity"] = max(
                0.0, h.get("respiratory_failure_severity", 0.0) - 0.024 * vent_strength
            )
            if state["observable"].get("sbp", 90) < 90:
                h["effective_volume"] = clamp(h["effective_volume"] - 0.0018 * vent_strength)

        # Diuresis has delayed, progressive effects rather than an instantaneous reset.
        # It preferentially removes retained/extravascular fluid and can modestly reduce
        # effective circulating volume, so over-diuresis is not automatically beneficial.
        fx = h.get("furosemide_effect", 0.0)
        if fx > 0:
            onset = min(1.0, fx)
            h["extravascular_fluid_burden"] = max(0.0, h.get("extravascular_fluid_burden", 0.0) - 0.010 * onset)
            h["effective_intravascular_fluid"] = max(0.0, h.get("effective_intravascular_fluid", 0.0) - 0.004 * onset)
            h["effective_volume"] = clamp(h.get("effective_volume", 0.0) - 0.0015 * onset)
            h["furosemide_effect"] = fx * math.exp(-math.log(2) / 75.0)

        update_fluid_phenotype(state)

        # Untreated infectious physiology also evolves continuously.
        if not state["treatments"]["antibiotics"]:
            h = state["hidden"]
            h["inflammatory_drive"] = clamp(h["inflammatory_drive"] + 0.015 / 15.0)
            h["vasomotor_tone"] = clamp(h["vasomotor_tone"] - 0.012 / 15.0)
            h["effective_volume"] = clamp(h["effective_volume"] - 0.006 / 15.0)
            h["tissue_perfusion"] = clamp(h["tissue_perfusion"] - 0.010 / 15.0)
            h["sympathetic_drive"] = clamp(h["sympathetic_drive"] + 0.008 / 15.0)

        update_dynamic_rhythm(state, 1)
        update_decompensation(state, added_fluid_ml=0, elapsed_min=1)
        recompute_coupled_physiology(state, elapsed_min=1)
        if state["treatments"].get("invasive_ventilation") and not h.get("cardiac_arrest"):
            state["observable"]["respiratory_rate"] = 20
            state["observable"]["work_of_breathing"] = "Ventilator-supported"


def fluid_transition(state, volume_ml, fluid_type="Crystalloid", rate="standard"):
    """
    v0.6.0.1 crystalloid transition with single-pass clock integration.

    Fluid changes retained intravascular volume / preload. Observable BP, HR, CRT,
    mental status, and perfusion then emerge from the coupled physiology engine.
    No fixed BP increment or fixed HR decrement is applied here.
    """
    h = state["hidden"]
    tr = state["treatments"]

    update_fluid_phenotype(state)

    pre_ev = h["effective_volume"]
    pre_total = tr["cumulative_crystalloid_ml"]
    pre_cong = h["pulmonary_congestion"]
    pre_resp = h["preload_responsiveness"]
    pre_retained = h.get("effective_intravascular_fluid", 0.0)

    # Administration itself is saturating: larger single boluses do not create
    # linearly larger useful intravascular effects.
    bolus_units = max(0.0, volume_ml) / 500.0
    retained_increment = 0.135 * (1.0 - math.exp(-0.72 * bolus_units))

    # Later boluses still add intravascular volume, but their conversion into useful
    # effective filling falls as Frank-Starling reserve is exhausted. A nonresponsive
    # patient therefore retains volume without receiving the same forward-flow benefit.
    preload_gain = retained_increment * (0.34 + 0.66 * pre_resp)

    # Retained crystalloid is allowed to accumulate beyond the useful-preload
    # plateau. The useful filling state remains capped separately, so extra volume
    # can become hydrostatic burden rather than disappearing from the model.
    h["effective_intravascular_fluid"] = clamp(
        pre_retained + retained_increment, 0.0, 2.40
    )
    h["effective_volume"] = clamp(h["effective_volume"] + preload_gain, 0.05, 1.0)
    tr["cumulative_crystalloid_ml"] += volume_ml

    # Minimal congestion representation only. This is continuous and state-based,
    # not a penalty at a cumulative-liter threshold.
    intolerance = fluid_intolerance_pressure(state, volume_ml)
    # Ordinary crystalloid accumulation should show diminishing returns before it
    # shows a major adverse filling penalty. Congestion remains possible, but only
    # rises meaningfully when filling is already high or intolerance is substantial.
    # Complete the right side of the curve: while still fluid responsive, the
    # congestion increment remains small; after preload saturation, additional
    # retained volume increasingly becomes hydrostatic congestion.
    preload_now = h.get("preload_state", h["effective_volume"])
    saturation = max(0.0, preload_now - 0.74)
    retained_excess = max(0.0, h["effective_intravascular_fluid"] - 0.54)
    # Preserve the good 0–1 L response: congestion is minimal while preload
    # reserve remains. Once the plateau is reached, retained volume progressively
    # becomes hydrostatic congestion. This is state-derived, not a liter trigger.
    cong_gain = (
        0.002 * bolus_units
        + 0.026 * intolerance
        + 0.105 * saturation
        + 0.085 * retained_excess
        + 0.055 * max(0.0, 0.30 - pre_resp)
    )
    if rate == "rapid":
        cong_gain *= 1.15
    h["pulmonary_congestion"] = clamp(h["pulmonary_congestion"] + cong_gain)

    update_fluid_phenotype(state)

    # Administration time. Reassessment requested by the learner is handled by the
    # existing aligned-clock pathway; this duration represents infusion time only.
    duration = max(3, int(round(volume_ml / (180 if rate == "rapid" else 110))))
    duration = min(duration, 20)

    # IMPORTANT v0.6.0.1:
    # Do NOT advance/recompute time-dependent physiology here for `duration`.
    # execute_bundle() advances the clinical state minute-by-minute for the action /
    # reassessment interval after all interventions are registered. In v0.6.0 this
    # transition also recomputed with elapsed_min=duration, so a 5-minute fluid
    # action effectively exposed the patient to ~10 minutes of contractile/perfusion
    # deterioration. That made the post-fluid trajectory systematically worse than
    # untreated natural history after the transient preload benefit waned.
    #
    # This transition now only changes the fluid/preload state. The coupled engine
    # integrates preload -> SV -> CO -> BP/perfusion exactly once in the aligned
    # clinical clock via apply_natural_disease().
    return {
        "duration_min": duration,
        "pre_volume_state": classify_volume_state(pre_ev),
        "post_volume_state": classify_volume_state(h["effective_volume"]),
        "responsiveness": pre_resp,
        "post_responsiveness": h["preload_responsiveness"],
        "pre_retained_fluid_effect": pre_retained,
        "post_retained_fluid_effect": h["effective_intravascular_fluid"],
        "fluid_type": fluid_type,
        "volume_ml": volume_ml,
        "cumulative_ml": tr["cumulative_crystalloid_ml"],
        "congestion_stage": congestion_stage(h["pulmonary_congestion"]),
        "intolerance_pressure": intolerance,
    }


def beta_blocker_transition(state, agent, dose_mg, route):
    """
    Administer beta blocker into a time-resolved effect-site model.
    The dose does not instantly produce its full HR effect.
    """
    h = state["hidden"]
    o = state["observable"]
    tr = state["treatments"]

    if h.get("cardiac_arrest"):
        return {"duration_min": 0, "agent": agent, "dose_mg": dose_mg, "route": route}

    if agent == "metoprolol":
        ref_dose = 5.0 if route == "IV" else 25.0
    else:
        ref_dose = 1.0 if route == "IV" else 20.0

    dose_strength = clamp(dose_mg / max(ref_dose, 0.1), 0.10, 2.5)
    route_factor = 1.0 if route == "IV" else 0.55

    # Standard IV reference dose contributes ~1.0 normalized effect-site unit.
    input_effect = dose_strength * route_factor

    if agent == "metoprolol":
        h["metoprolol_depot"] = clamp(
            h.get("metoprolol_depot", 0.0) + input_effect,
            0.0,
            6.0,
        )
        tr["metoprolol_total_mg"] += dose_mg
    else:
        h["propranolol_depot"] = clamp(
            h.get("propranolol_depot", 0.0) + input_effect,
            0.0,
            6.0,
        )
        tr["propranolol_total_mg"] += dose_mg

    # The action itself consumes time; during these minutes the drug begins to act.
    duration = 5 if route == "IV" else 30

    return {
        "duration_min": duration,
        "agent": agent,
        "dose_mg": dose_mg,
        "route": route,
    }


def diltiazem_transition(state, dose_mg, route):
    h, tr = state["hidden"], state["treatments"]
    ref = 15.0 if route == "IV" else 60.0
    strength = clamp(dose_mg / ref, 0.10, 2.5)
    route_factor = 1.0 if route == "IV" else 0.55
    h["diltiazem_depot"] = clamp(h.get("diltiazem_depot", 0.0) + strength * route_factor, 0.0, 2.5)
    tr["diltiazem_total_mg"] += dose_mg
    return {"duration_min": 5 if route == "IV" else 30, "agent": "diltiazem", "dose_mg": dose_mg, "route": route}


def amiodarone_transition(state, dose_mg, route):
    h, tr = state["hidden"], state["treatments"]
    ref = 150.0 if route == "IV" else 200.0
    strength = clamp(dose_mg / ref, 0.10, 3.0)
    route_factor = 1.0 if route == "IV" else 0.50
    h["amiodarone_depot"] = clamp(h.get("amiodarone_depot", 0.0) + strength * route_factor, 0.0, 3.0)
    tr["amiodarone_total_mg"] += dose_mg

    # IV loading can transiently lower pressure, particularly in a poorly perfused patient.
    if route == "IV":
        vulnerability = clamp(1.0 - h["tissue_perfusion"])
        state["observable"]["sbp"] = max(55, int(round(state["observable"]["sbp"] - 3.0 * strength * vulnerability)))
        state["observable"]["dbp"] = max(30, int(round(state["observable"]["dbp"] - 1.5 * strength * vulnerability)))

    return {"duration_min": 10 if route == "IV" else 30, "agent": "amiodarone", "dose_mg": dose_mg, "route": route}


def _record_treatment_timing(state, key, operation="start"):
    """Record start/adjustment/stop times for learner-visible ongoing support."""
    timeline = state.setdefault("treatment_timeline", {})
    entry = timeline.setdefault(key, {})
    now = int(state.get("sim_time", 0))
    if operation == "stop":
        entry["active"] = False
        entry["stopped_min"] = now
        entry["last_changed_min"] = now
        return
    if operation == "continue":
        if "started_min" not in entry:
            entry["started_min"] = now
        entry["active"] = True
        return
    if not entry.get("active"):
        entry["started_min"] = now
    entry["active"] = True
    entry["last_changed_min"] = now
    entry.pop("stopped_min", None)


def _treatment_timing_suffix(state, key):
    entry = (state.get("treatment_timeline", {}) or {}).get(key) or {}
    started = entry.get("started_min")
    changed = entry.get("last_changed_min")
    if started is None:
        return ""
    parts = [f"started {sim_time_label(int(started))}"]
    if changed is not None and int(changed) != int(started):
        parts.append(f"last adjusted {sim_time_label(int(changed))}")
    return " — " + " · ".join(parts)


def dobutamine_transition(state, rate, units="mcg/kg/min", operation="start"):
    h, tr = state["hidden"], state["treatments"]
    if operation == "stop":
        old_rate = tr.get("dobutamine_rate", 0.0)
        tr["dobutamine"] = False
        tr["dobutamine_rate"] = 0.0
        _record_treatment_timing(state, "dobutamine", "stop")
        # Pharmacodynamic effect washes out rather than disappearing instantly.
        return {"duration_min": 1, "support_type": "dobutamine", "operation": "stop",
                "rate": old_rate, "units": "mcg/kg/min"}

    if units != "mcg/kg/min":
        # This build models weight-based dobutamine dosing. A bare start defaults to 5.
        units = "mcg/kg/min"
    rate = float(rate if rate is not None else 5.0)
    rate = clamp(rate, 2.5, 20.0)
    tr["dobutamine"] = True
    tr["dobutamine_rate"] = rate
    tr["dobutamine_units"] = units
    _record_treatment_timing(state, "dobutamine", operation)
    # Do not jump contractility/perfusion here: the effect is integrated minute by minute.
    h.setdefault("dobutamine_effect", 0.0)
    h.setdefault("dobutamine_minutes", 0.0)
    return {"duration_min": 1, "support_type": "dobutamine", "operation": operation,
            "rate": rate, "units": units}


def norepinephrine_transition(state, rate, units, operation="start"):
    tr = state["treatments"]
    was_active = bool(tr.get("norepinephrine"))
    old_rate = tr.get("norepinephrine_rate", 0.0)
    old_units = tr.get("norepinephrine_units")
    if operation == "stop":
        tr["norepinephrine"] = False
        tr["norepinephrine_rate"] = 0.0
        _record_treatment_timing(state, "norepinephrine", "stop")
        return {"duration_min": 1, "support_type": "norepinephrine", "operation": "stop", "rate": old_rate, "units": old_units}
    tr["norepinephrine"] = True
    tr["norepinephrine_rate"] = rate
    tr["norepinephrine_units"] = units
    _record_treatment_timing(state, "norepinephrine", operation)
    return {
        "duration_min": 2,
        "support_type": "norepinephrine",
        "operation": operation,
        "rate": rate,
        "units": units,
        "old_rate": old_rate if was_active else None,
        "old_units": old_units if was_active else None,
    }


def furosemide_transition(state, dose_mg, route):
    h, tr = state["hidden"], state["treatments"]
    tr["furosemide_total_mg"] = tr.get("furosemide_total_mg", 0.0) + dose_mg
    # IV onset is clinically meaningful over the next 10-20 min; PO is slower.
    potency = clamp(dose_mg / 40.0, 0.25, 2.0) * (1.0 if route == "IV" else 0.45)
    h["furosemide_effect"] = clamp(h.get("furosemide_effect", 0.0) + potency, 0.0, 2.5)
    return {"duration_min": 2 if route == "IV" else 5, "agent": "furosemide", "dose_mg": dose_mg, "route": route}


def oxygen_transition(state, device, flow_lpm):
    tr = state["treatments"]
    operation = "adjust" if tr.get("oxygen") else "start"
    tr["oxygen"] = True
    tr["oxygen_device"] = device
    tr["oxygen_flow_lpm"] = flow_lpm
    _record_treatment_timing(state, "oxygen", operation)
    return {"duration_min": 1, "support_type": "oxygen", "device": device, "flow_lpm": flow_lpm}


def nitroglycerin_transition(state, rate_mcg_min, operation="start"):
    h, tr = state["hidden"], state["treatments"]
    if operation == "stop":
        tr["nitroglycerin"] = False
        tr["nitroglycerin_rate_mcg_min"] = 0.0
        h["nitroglycerin_effect"] = 0.0
        _record_treatment_timing(state, "nitroglycerin", "stop")
        return {"duration_min": 1, "support_type": "nitroglycerin", "operation": "stop", "rate_mcg_min": 0.0}

    tr["nitroglycerin"] = True
    tr["nitroglycerin_rate_mcg_min"] = float(rate_mcg_min)
    _record_treatment_timing(state, "nitroglycerin", operation)
    # Effect is continuous and pressure-dependent; no direct canned BP response.
    h["nitroglycerin_effect"] = clamp(float(rate_mcg_min) / 120.0, 0.0, 1.5)
    return {
        "duration_min": 1,
        "support_type": "nitroglycerin",
        "operation": "start",
        "rate_mcg_min": float(rate_mcg_min),
    }


def niv_transition(state, mode, pressure_cmh2o, operation="start", ipap_cmh2o=None, epap_cmh2o=None, fio2_percent=None):
    tr = state["treatments"]
    if operation == "stop":
        tr["niv"] = False
        tr["niv_mode"] = None
        tr["niv_pressure_cmh2o"] = 0.0
        tr["niv_ipap_cmh2o"] = None
        tr["niv_epap_cmh2o"] = None
        tr["niv_fio2_percent"] = None
        _record_treatment_timing(state, "niv", "stop")
        return {"duration_min": 1, "support_type": "niv", "operation": "stop", "mode": mode, "pressure_cmh2o": 0.0}

    effective_pressure = epap_cmh2o if mode == "BiPAP" and epap_cmh2o is not None else pressure_cmh2o
    if effective_pressure is None:
        effective_pressure = 0.0
    timing_operation = "adjust" if tr.get("niv") else "start"
    if tr.get("oxygen"):
        _record_treatment_timing(state, "oxygen", "stop")
    tr["niv"] = True
    tr["oxygen"] = False
    tr["oxygen_device"] = None
    tr["oxygen_flow_lpm"] = 0.0
    tr["niv_mode"] = mode
    tr["niv_pressure_cmh2o"] = float(effective_pressure)
    tr["niv_ipap_cmh2o"] = float(ipap_cmh2o) if ipap_cmh2o is not None else None
    tr["niv_epap_cmh2o"] = float(epap_cmh2o) if epap_cmh2o is not None else None
    if fio2_percent is not None:
        tr["niv_fio2_percent"] = float(fio2_percent)
    _record_treatment_timing(state, "niv", timing_operation)
    return {
        "duration_min": 1, "support_type": "niv", "operation": "start", "mode": mode,
        "pressure_cmh2o": float(effective_pressure),
        "ipap_cmh2o": tr.get("niv_ipap_cmh2o"), "epap_cmh2o": tr.get("niv_epap_cmh2o"),
        "fio2_percent": tr.get("niv_fio2_percent"),
    }


def airway_preparation_transition(state):
    state["treatments"]["airway_prepared"] = True
    return {"duration_min": 2, "support_type": "airway_preparation", "operation": "prepare"}


def intubation_transition(state, ventilator_mode="VC/AC", fio2_percent=100.0, peep_cmh2o=8.0):
    tr = state["treatments"]
    if tr.get("niv"):
        _record_treatment_timing(state, "niv", "stop")
    if tr.get("oxygen"):
        _record_treatment_timing(state, "oxygen", "stop")
    tr["airway_prepared"] = True
    tr["invasive_ventilation"] = True
    tr["ventilator_mode"] = ventilator_mode
    tr["ventilator_fio2_percent"] = float(fio2_percent)
    tr["ventilator_peep_cmh2o"] = float(peep_cmh2o)
    tr["sedated_for_intubation"] = True
    tr["niv"] = False
    tr["niv_mode"] = None
    tr["niv_pressure_cmh2o"] = 0.0
    tr["niv_ipap_cmh2o"] = None
    tr["niv_epap_cmh2o"] = None
    tr["niv_fio2_percent"] = None
    tr["oxygen"] = False
    tr["oxygen_device"] = None
    tr["oxygen_flow_lpm"] = 0.0
    _record_treatment_timing(state, "invasive_ventilation", "start")
    state["observable"]["mental_status"] = "Sedated"
    return {
        "duration_min": 5,
        "support_type": "invasive_ventilation",
        "operation": "start",
        "ventilator_mode": ventilator_mode,
        "fio2_percent": float(fio2_percent),
        "peep_cmh2o": float(peep_cmh2o),
    }


def ventilator_adjustment_transition(state, ventilator_mode=None, fio2_percent=None, peep_cmh2o=None):
    """Adjust an existing invasive ventilator without repeating intubation."""
    tr = state["treatments"]
    old_mode = tr.get("ventilator_mode") or "VC/AC"
    old_fio2 = float(tr.get("ventilator_fio2_percent") or 40.0)
    old_peep = float(tr.get("ventilator_peep_cmh2o") or 5.0)
    pre_spo2 = state.get("observable", {}).get("spo2")
    if ventilator_mode is not None:
        tr["ventilator_mode"] = ventilator_mode
    if fio2_percent is not None:
        tr["ventilator_fio2_percent"] = float(fio2_percent)
    if peep_cmh2o is not None:
        tr["ventilator_peep_cmh2o"] = float(peep_cmh2o)
    _record_treatment_timing(state, "invasive_ventilation", "adjust")
    return {
        "duration_min": 1,
        "support_type": "invasive_ventilation",
        "operation": "adjust",
        "ventilator_mode": tr.get("ventilator_mode") or "VC/AC",
        "fio2_percent": float(tr.get("ventilator_fio2_percent") or 40.0),
        "peep_cmh2o": float(tr.get("ventilator_peep_cmh2o") or 5.0),
        "old_ventilator_mode": old_mode,
        "old_fio2_percent": old_fio2,
        "old_peep_cmh2o": old_peep,
        "pre_adjustment_spo2": pre_spo2,
    }


def ventilator_continuation_transition(state):
    """Acknowledge unchanged invasive support without a second procedure."""
    tr = state["treatments"]
    _record_treatment_timing(state, "invasive_ventilation", "continue")
    return {
        "duration_min": 0,
        "support_type": "invasive_ventilation",
        "operation": "continue",
        "ventilator_mode": tr.get("ventilator_mode") or "VC/AC",
        "fio2_percent": float(tr.get("ventilator_fio2_percent") or 40.0),
        "peep_cmh2o": float(tr.get("ventilator_peep_cmh2o") or 5.0),
    }


def procedural_sedation_transition(state, medications):
    """Administer a bounded, time-limited procedural-sedation regimen."""
    h, o, tr = state["hidden"], state["observable"], state["treatments"]
    administered = []
    etomidate_mg = 0.0
    midazolam_mg = 0.0
    for medication in medications or []:
        agent = str(medication.get("agent") or "").lower()
        dose = float(medication.get("dose") or 0.0)
        units = str(medication.get("units") or "mg").lower()
        if units in {"mcg", "µg", "ug"}:
            dose_mg = dose / 1000.0
        elif units == "g":
            dose_mg = dose * 1000.0
        else:
            dose_mg = dose
        item = {
            "agent": agent,
            "dose": dose,
            "units": units,
            "route": medication.get("route") or "IV",
        }
        administered.append(item)
        if agent == "etomidate":
            etomidate_mg += dose_mg
        elif agent == "midazolam":
            midazolam_mg += dose_mg

    tr["procedural_sedations"] = int(tr.get("procedural_sedations", 0)) + 1
    tr["etomidate_total_mg"] = float(tr.get("etomidate_total_mg", 0.0)) + etomidate_mg
    tr["midazolam_total_mg"] = float(tr.get("midazolam_total_mg", 0.0)) + midazolam_mg
    tr["last_procedural_sedation"] = deepcopy(administered)
    _record_treatment_timing(state, "procedural_sedation", "administer")

    # Reference doses create a short-lived effect-site signal. Etomidate has a
    # smaller modeled vascular penalty; midazolam contributes more persistence.
    effect = (
        0.55 * clamp(etomidate_mg / 10.0, 0.0, 2.0)
        + 0.75 * clamp(midazolam_mg / 2.0, 0.0, 2.0)
    )
    h["procedural_sedation_effect"] = clamp(
        h.get("procedural_sedation_effect", 0.0) + effect,
        0.15,
        1.50,
    )
    h["procedural_sedation_minutes"] = 0.0
    o["mental_status"] = "Sedated"
    return {
        "duration_min": 1,
        "support_type": "procedural_sedation",
        "operation": "administer",
        "medications": administered,
    }


def cardioversion_transition(state, energy_j):
    h, o, tr = state["hidden"], state["observable"], state["treatments"]
    r = rng()
    tr["cardioversions"] += 1
    pre_rhythm = o["rhythm"]
    # Deterministic vertical slice: >=150 J converts; 100-149 J converts on the first attempt; <100 J fails.
    success = energy_j >= 150 or (100 <= energy_j < 150 and tr["cardioversions"] == 1)
    if success and pre_rhythm == "AF":
        o["rhythm"] = "Sinus rhythm"
        h["af_burden"] = 0.05
        h["minutes_since_cardioversion"] = 0
        h["af_recurrence_pressure"] = 0.0
        h["sinus_stability"] = 1.0
        # Post-conversion sinus rate reflects residual sympathetic drive and active blockade.
        blockade = total_beta_blockade(state)
        sinus_target = 78 + 22 * h["sympathetic_drive"] - 24 * blockade
        o["hr"] = int(round(max(55, min(115, sinus_target + r.uniform(-4, 4)))))
        # Only the AF-attributable fraction of instability improves. In PS001 AF is mostly a marker/contributor.
        gain = h.get("af_causal_weight", 0.25)
        o["sbp"] = int(round(o["sbp"] + 5 * gain + r.uniform(-1, 1)))
        o["dbp"] = int(round(o["dbp"] + 3 * gain + r.uniform(-1, 1)))
        h["tissue_perfusion"] = clamp(h["tissue_perfusion"] + 0.05 * gain)
    duration = 3
    update_decompensation(state, added_fluid_ml=0, elapsed_min=duration)
    return {"duration_min": duration, "energy_j": energy_j, "cardioversion_success": success, "pre_rhythm": pre_rhythm}



def decay_fraction(half_life_min, minutes=1):
    """The same half-time law used for legacy redistribution and drug washout."""
    return math.exp(-math.log(2) * minutes / half_life_min)


def exposure_effect(load, curve):
    """Case-parameterized nodal saturation / progressive myocardial effect."""
    if not curve:
        return load
    def raw(x):
        return curve['saturating_weight'] * (1 - math.exp(-curve['rate'] * x)) + curve['progressive_weight'] * x ** curve['power']
    return raw(max(0, load)) / raw(1)


def advance_volume(compartments, incoming_ml, parameters, diuresis_ml):
    """Conservative redistribution, clearance and fluid removal, per minute.

    Values are mL, unlike the dimensionless legacy PS001 compartment scales.
    Removal exceeding available excess becomes a circulating volume deficit.
    """
    c = compartments
    c['fluid_retained_ml'] += incoming_ml
    redistributed = c['fluid_retained_ml'] * (1 - decay_fraction(parameters['redistribution_half_life_min']))
    c['fluid_retained_ml'] -= redistributed
    c['fluid_extravascular_ml'] += redistributed * parameters['extravascular_fraction']
    c['fluid_output_ml'] += redistributed * (1 - parameters['extravascular_fraction'])
    clearance = c['fluid_extravascular_ml'] * (1 - decay_fraction(parameters['clearance_half_life_min']))
    c['fluid_extravascular_ml'] -= clearance
    c['fluid_output_ml'] += clearance
    extra_removed = min(c['fluid_extravascular_ml'], diuresis_ml * parameters['diuresis_extravascular_fraction'])
    c['fluid_extravascular_ml'] -= extra_removed
    remaining = diuresis_ml - extra_removed
    retained_removed = min(c['fluid_retained_ml'], remaining)
    c['fluid_retained_ml'] -= retained_removed
    c['fluid_deficit_ml'] += remaining - retained_removed
    c['fluid_output_ml'] += diuresis_ml
    return c


def mark_terminal_collapse(state):
    """Original PEA surface: electrical activity persists without a pulse."""
    h, o = state.setdefault('hidden', {}), state['observable']
    h.update(cardiac_arrest=True, terminal_collapse=True)
    o.update(pulse_present=False, peripheral_perfusion='critical', rhythm='PEA',
             sbp=0, dbp=0, map=0, crt=None, spo2=None, mental_status='Unresponsive',
             extremities='Mottled/Cold' if o.get('extremities') == 'Mottled/Cold' else 'Cold')


def active_drug_fraction(age_min, onset_half_life_min, elimination_half_life_min):
    """Closed form of the legacy minute-by-minute depot/effect-site recurrence."""
    n=max(0, int(age_min))
    a=decay_fraction(onset_half_life_min)
    b=decay_fraction(elimination_half_life_min)
    if abs(a-b)<1e-12:
        return (1-a)*n*a**max(0,n-1)
    return max(0, (1-a)*(b**n-a**n)/(b-a))
