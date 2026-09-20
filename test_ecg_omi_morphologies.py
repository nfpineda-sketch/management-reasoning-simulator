"""Electrocardiographic equivalents of an occluded artery (faculty, 2026-09-19).

Faculty statement: management changes with the ECG. There is ACS with ST
elevation, where the cath lab is activated to open the artery, and ACS without
it, managed differently. And there are equivalents that carry no ST elevation in
the 12-lead ECG yet must be studied aggressively with coronary angiography: an
isolated posterior infarct, de Winter T waves, diffuse ST depression with ST
elevation in aVR, and Wellens syndrome. The nomenclature is moving to OMI
precisely so these are not left out.

These tests measure the waveform the model generates, lead by lead. The ECG
carries no automated interpretation: the reader interprets it.
"""
import pytest

import ecg12

LEADS = ("I", "II", "aVR", "V1", "V2", "V3", "V4", "V5", "V6")


def measurements(profile, rate=70, seed=7):
    """ST deviation at the J point, T-wave peak, R and S amplitudes, per lead."""
    signals, pars, beats = ecg12._signals(rate, "sinus", profile, seed)
    qrs, qt, hz = pars["qrs_s"], pars["qt_s"], ecg12.SAMPLE_HZ
    start = beats[2]
    out = {}
    for lead in LEADS:
        at = lambda dt: int(round((start + dt) * hz))
        baseline = signals[lead][at(-.12)]
        window = signals[lead][at(qrs + .08):at(qt)]
        out[lead] = {
            "st": signals[lead][at(qrs + .01)] - baseline,
            "t": max(window, key=abs) - baseline,
            "r": max(signals[lead][at(0):at(qrs)]) - baseline,
            "s": min(signals[lead][at(0):at(qrs)]) - baseline,
        }
    return out


def test_every_profile_is_declared_and_renders():
    for profile in ecg12.PROFILES:
        assert set(measurements(profile)) == set(LEADS)


def test_an_isolated_posterior_infarct_is_a_mirror_image():
    m = measurements("posterior_infarct")
    # ST depression maximal in V2-V3, with a tall R and an upright T there.
    assert m["V2"]["st"] < -.15 and m["V3"]["st"] < -.15
    assert m["V2"]["r"] > abs(m["V2"]["s"]) and m["V3"]["r"] > abs(m["V3"]["s"])
    assert m["V2"]["t"] > .1 and m["V3"]["t"] > .1
    # No ST elevation anywhere: this is why it is missed.
    assert all(m[lead]["st"] < .05 for lead in LEADS)


def test_de_winter_pairs_j_point_depression_with_tall_symmetric_t_waves():
    m = measurements("de_winter")
    baseline = measurements("baseline")
    for lead in ("V2", "V3", "V4"):
        assert m[lead]["st"] < -.1
        assert m[lead]["t"] > baseline[lead]["t"] + .4
    assert m["aVR"]["st"] > 0


def test_diffuse_depression_elevates_avr_only():
    m = measurements("diffuse_st_depression_avr")
    assert m["aVR"]["st"] > .1
    for lead in ("I", "II", "V3", "V4", "V5", "V6"):
        assert m[lead]["st"] < -.1


def test_wellens_inverts_the_t_waves_without_moving_the_st_segment():
    m = measurements("wellens")
    baseline = measurements("baseline")
    for lead in ("V2", "V3", "V4"):
        assert m[lead]["t"] < -.2
        assert abs(m[lead]["st"]) < .03
        # R waves are preserved: there is no infarct yet, which is the point.
        assert m[lead]["r"] >= baseline[lead]["r"] - .02


@pytest.mark.parametrize("profile", ["posterior_infarct", "de_winter", "diffuse_st_depression_avr", "wellens"])
def test_an_equivalent_never_shows_st_elevation(profile):
    """These are the patterns that a search for ST elevation alone would discard."""
    assert all(values["st"] < .05 for lead, values in measurements(profile).items() if lead != "aVR")


def test_the_acquisition_carries_no_interpretation():
    state = {"sim_time": 0, "observable": {"hr": 70, "rhythm": "Sinus rhythm", "pulse_present": True},
             "ecg_profile": "de_winter", "seed": 3}
    snapshot = ecg12.acquire_ecg(state)
    assert snapshot["status"] == "available"
    text = " ".join(str(value).lower() for key, value in snapshot.items() if isinstance(value, str))
    for word in ("de winter", "infarct", "ischemia", "ischaemia", "occlusion", "stemi", "omi"):
        assert word not in text
