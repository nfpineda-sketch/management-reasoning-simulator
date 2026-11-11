"""PHASE2_AMENDMENT_2 (A2-019R): the falsifiability mutants, as an EXPLICIT pytest plugin.

Each mutant breaks one behaviour the faculty required, in the physiology module only, for the life of one pytest run:

    MRS_A2_MUTANT=<name> python3 -m pytest -p test_amendment_2_mutants_plugin <focused amendment tests>

It is test code (its name starts with ``test_``), nothing loads it by default, and it never edits a file. The mutant suite
(``test_phase2_amendment_2_mutants.py``) runs the amendment's focused tests under every mutant and requires each run to
FAIL: a mutant that survives means a required behaviour is not protected.
"""
import os

import pytest

FLAG = "MRS_A2_MUTANT"


def _patches():
    from clinical_core import systemic_consciousness as sc
    from clinical_core.state import CoreInvariantError

    original = {name: getattr(sc, name) for name in ("collapse_signal", "relative_delivery", "collapse_state", "readout",
                                                     "primary_neurologic", "collapse_burden_after", "systemic_burden_after",
                                                     "category_index", "delivery_failure", "consciousness_level")}

    def collapse_is_max(perfusion, delivery):
        return max(perfusion, delivery)

    def delivery_is_absolute(delivery_rel, anchors):
        return anchors.arrival_delivery_ratio * delivery_rel

    def no_pulse_is_not_immediate(burden, pulse_present, profile):
        return original["collapse_state"](burden, True, profile)

    def level_includes_the_instantaneous_signal(state, anchors, core_profile, pressure_rel=None, delivery_rel=None):
        reading = original["readout"](state, anchors, core_profile, pressure_rel, delivery_rel)
        signal = reading["instantaneous"].get("delivery_failure", 0.0)
        reading = dict(reading)
        reading["impairment"] = max(reading["impairment"], signal)
        reading["category_index"] = original["category_index"](reading["impairment"])
        reading["category"] = original["readout"].__globals__["CATEGORIES"][reading["category_index"]]
        return reading

    def no_arrival_floor(state, anchors):
        from clinical_core import encephalopathy as en
        return en.primary_neurologic_impairment(state.N)

    def collapse_moves_without_a_pulse(state, anchors, core_profile):
        import dataclasses
        from clinical_core.state import RhythmState
        pulsed = dataclasses.replace(state, R=RhythmState(state.R.code, state.R.rate_bpm, state.R.output_factor, True),
                                     terminal_since=None) if False else state
        return min(1.0, state.aux.collapse_burden + 0.2)

    def f_clears_as_fast_as_it_rises(state, anchors, core_profile):
        from clinical_core import encephalopathy as en
        profile = core_profile.amendment_2
        signal = (original["delivery_failure"](sc._coordinates(state, anchors, core_profile)[0], profile)
                  if state.R.pulse_present else 1.0)
        memory = en.EncephalopathyProfile(burden_rise_tau=profile.burden_rise_tau, burden_clear_tau=profile.burden_rise_tau)
        return en.burden_after(sc.systemic_burden(state), signal, 1.0, memory)

    def f_reads_the_signal_instantly(state, anchors, core_profile):
        profile = core_profile.amendment_2
        return (original["delivery_failure"](sc._coordinates(state, anchors, core_profile)[0], profile)
                if state.R.pulse_present else 1.0)

    def f_is_inert(state, anchors, core_profile):
        return 0.0

    def a_direct_ladder_reaches_the_level(which):
        """P3-179: the retired direct ladders put back. The level is the composite OR the old ladder, whichever is higher."""
        def level(state, anchors, core_profile):
            import dataclasses
            from clinical_core import derived as dv
            composite = original["consciousness_level"](state, anchors, core_profile)
            legacy = dv.derive(state, anchors, dataclasses.replace(core_profile, amendment_2=None))
            ladder = (dv._level(legacy.sbp, core_profile.pressure_levels) if which == "sbp"
                      else dv._level(legacy.spo2, core_profile.oxygen_levels))
            return max(composite, ladder)
        return level

    def cuts_shifted(impairment):
        return sum(1 for cut in (0.30, 0.55, 0.85) if impairment >= cut)

    def delivery_failure_reads_pressure(value, profile):
        return original["delivery_failure"](min(value, 1.0) * 0.5 if value > 1.0 else value, profile)

    def no_hysteresis(burden, pulse_present, profile):
        if not pulse_present:
            return {"state": sc.ESTABLISHED, "basis": sc.NO_PULSE}
        if burden >= profile.established_burden:
            return {"state": sc.ESTABLISHED, "basis": sc.SOFT}
        return {"state": sc.NO_COLLAPSE, "basis": None}

    def f_also_reads_pressure(state, anchors, core_profile):
        from clinical_core import encephalopathy as en
        profile = core_profile.amendment_2
        delivery, perfusion = sc._coordinates(state, anchors, core_profile)
        signal = (max(original["delivery_failure"](delivery, profile), sc.perfusion_failure(perfusion, profile))
                  if state.R.pulse_present else 1.0)
        memory = en.EncephalopathyProfile(burden_rise_tau=profile.burden_rise_tau, burden_clear_tau=profile.burden_clear_tau)
        return en.burden_after(sc.systemic_burden(state), signal, 1.0, memory)

    def impending_counts(state, anchors, core_profile, pressure_rel=None, delivery_rel=None):
        reading = dict(original["readout"](state, anchors, core_profile, pressure_rel, delivery_rel))
        if reading["collapse"]["state"] == sc.IMPENDING:
            reading["impairment"] = 1.0
            reading["category_index"] = 3
            reading["category"] = original["readout"].__globals__["CATEGORIES"][3]
            reading["contributors"] = {**reading["contributors"], sc.COLLAPSE: 1.0}
        return reading

    def collapse_clears_as_fast(state, anchors, core_profile):
        from clinical_core import encephalopathy as en
        profile = core_profile.amendment_2
        if not state.R.pulse_present:
            return state.aux.collapse_burden
        delivery, perfusion = sc._coordinates(state, anchors, core_profile)
        signal = sc.collapse_signal(sc.perfusion_failure(perfusion, profile), original["delivery_failure"](delivery, profile))
        memory = en.EncephalopathyProfile(burden_rise_tau=profile.collapse_rise_tau, burden_clear_tau=profile.collapse_rise_tau)
        return en.burden_after(state.aux.collapse_burden, signal, 1.0, memory)

    return {
        "f_also_reads_pressure": lambda: setattr(sc, "systemic_burden_after", f_also_reads_pressure),
        "impending_counts_as_collapse": lambda: setattr(sc, "readout", impending_counts),
        "collapse_clears_as_fast_as_it_builds": lambda: setattr(sc, "collapse_burden_after", collapse_clears_as_fast),
        "collapse_by_maximum": lambda: setattr(sc, "collapse_signal", collapse_is_max),
        "delivery_against_an_absolute_baseline": lambda: setattr(sc, "relative_delivery", delivery_is_absolute),
        "no_pulse_not_immediate": lambda: setattr(sc, "collapse_state", no_pulse_is_not_immediate),
        "level_includes_the_instantaneous_signal": lambda: setattr(sc, "readout", level_includes_the_instantaneous_signal),
        "no_arrival_floor": lambda: setattr(sc, "primary_neurologic", no_arrival_floor),
        "collapse_burden_ignores_the_signal": lambda: setattr(sc, "collapse_burden_after", collapse_moves_without_a_pulse),
        "f_clears_as_fast_as_it_rises": lambda: setattr(sc, "systemic_burden_after", f_clears_as_fast_as_it_rises),
        "f_is_the_instantaneous_signal": lambda: setattr(sc, "systemic_burden_after", f_reads_the_signal_instantly),
        "f_is_inert": lambda: setattr(sc, "systemic_burden_after", f_is_inert),
        "direct_pressure_ladder_in_the_level": lambda: setattr(sc, "consciousness_level",
                                                              a_direct_ladder_reaches_the_level("sbp")),
        "direct_saturation_ladder_in_the_level": lambda: setattr(sc, "consciousness_level",
                                                                a_direct_ladder_reaches_the_level("spo2")),
        "category_cuts_shifted": lambda: setattr(sc, "category_index", cuts_shifted),
        "no_hysteresis_band": lambda: setattr(sc, "collapse_state", no_hysteresis),
    }


MUTANTS = ("collapse_by_maximum", "delivery_against_an_absolute_baseline", "no_pulse_not_immediate",
           "level_includes_the_instantaneous_signal", "no_arrival_floor", "collapse_burden_ignores_the_signal",
           "f_clears_as_fast_as_it_rises", "f_is_the_instantaneous_signal", "category_cuts_shifted", "no_hysteresis_band",
           "f_also_reads_pressure", "impending_counts_as_collapse", "collapse_clears_as_fast_as_it_builds",
           "f_is_inert", "direct_pressure_ladder_in_the_level", "direct_saturation_ladder_in_the_level")


def pytest_report_header(config):
    wanted = os.environ.get(FLAG, "").strip()
    return f"amendment 2 mutants: plugin loaded, {'ACTIVE: ' + wanted if wanted else 'INACTIVE'}"


def pytest_configure(config):
    wanted = os.environ.get(FLAG, "").strip()
    if not wanted:
        return
    table = _patches()
    if wanted not in table:
        raise pytest.UsageError(f"unknown amendment 2 mutant {wanted!r}")
    table[wanted]()
