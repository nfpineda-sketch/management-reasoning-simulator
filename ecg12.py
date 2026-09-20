"""Deterministic educational ECG signals and calibrated 12-lead acquisition.

This is a transparent waveform model, not a patient recording or a validated
cardiac electrophysiology solver. See ECG_MODEL.md before authoring new cases.
No diagnosis is inferred from a learner's question or from haemodynamic values.
"""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from html import escape

MODEL_VERSION = 1
LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
# Standard 3x4 sequential display: each column occupies a different 2.5 s.
LAYOUT = (("I", "aVR", "V1", "V4"), ("II", "aVL", "V2", "V5"), ("III", "aVF", "V3", "V6"))
# The four added in 2026-09-19 are the electrocardiographic equivalents of an
# occluded artery (OMI) that carry no ST elevation in the 12-lead ECG: an isolated
# posterior infarct, de Winter T waves, diffuse ST depression with ST elevation in
# aVR, and Wellens syndrome. They are morphologies only; the reader interprets them.
PROFILES = ("baseline", "st_elevation_anterior", "st_elevation_inferior", "st_elevation_lateral", "st_depression",
            "right_strain", "posterior_infarct", "de_winter", "diffuse_st_depression_avr", "wellens")
SAMPLE_HZ = 500
DURATION_SECONDS = 10.0
RHYTHMS = {
    "af": "af", "atrial fibrillation": "af",
    "sinus": "sinus", "sinus rhythm": "sinus",
    "sinus tachycardia": "sinus", "sinus bradycardia": "sinus",
    "svt": "svt", "supraventricular tachycardia": "svt",
    "atrial flutter": "flutter", "flutter": "flutter",
    "complete heart block": "complete_block", "complete av block": "complete_block",
    "third degree av block": "complete_block",
    "vt": "vt", "ventricular tachycardia": "vt", "monomorphic vt": "vt",
    "junctional": "junctional", "junctional rhythm": "junctional",
    "asystole": "asystole", "vf": "vf", "ventricular fibrillation": "vf",
}


def _finite(value, name):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Invalid {name}.")
    return result


def _rhythm(observable):
    value = str(observable.get("rhythm") or "").strip().lower()
    # PEA is a clinical state, not one electrical morphology. Require its rhythm.
    if value == "pea":
        value = str(observable.get("electrical_rhythm") or "").strip().lower()
        if not value:
            raise ValueError("Electrical morphology for PEA has not been specified.")
    if value not in RHYTHMS:
        raise ValueError("This electrical rhythm has no waveform model yet.")
    return RHYTHMS[value]


def _beat_times(rate, rhythm, duration, seed=0):
    """One shared ventricular clock for every lead; AF varies RR, not each lead."""
    if rhythm in ("asystole", "vf"):
        return []
    rr = 60.0 / rate
    # Normalize a deterministic irregular cycle to the requested mean rate.
    multipliers = [1.0] * 16
    if rhythm == "af":
        phase = (int(seed) % 997) * 0.017
        values = [1 + .27 * math.sin(i * 2.39 + phase) + .15 * math.sin(i * .83 + .6) for i in range(16)]
        mean = sum(values) / len(values)
        multipliers = [v / mean for v in values]
    times, t, i = [], -2 * rr, 0
    while t < duration + rr:
        times.append(t)
        t += rr * multipliers[i % len(multipliers)]
        i += 1
    return times


def _bump(t, center, halfwidth):
    """Compact-support cosine lobe. Defined boundaries make intervals measurable."""
    x = (t - center) / halfwidth
    return .5 * (1 + math.cos(math.pi * x)) if abs(x) < 1 else 0.0


def _plateau(t, onset, end):
    if t <= onset or t >= end:
        return 0.0
    ramp = .012
    return min(1.0, (t - onset) / ramp, (end - t) / .06)


def _parameters(rate, rhythm, profile):
    rr = 60 / rate if rate else 1
    qrs = .150 if rhythm == "vt" else .090
    # Rate adaptation is illustrative. It does not model drug/electrolyte QT effects.
    qt = max(qrs + .12, min(.48, .39 * rr ** (1 / 3)))
    pr = max(.120, min(.180, .16 * rr ** .12)) if rhythm == "sinus" else None
    axis = 115 if profile == "right_strain" else (-65 if rhythm == "vt" else 55)
    return {"qrs_s": qrs, "qt_s": qt, "pr_s": pr, "axis_deg": axis}


def _coefficients(profile, axis, rhythm):
    # Basis ordering: atrial, initial Q, dominant R, terminal S, T, injury/ST.
    # A common temporal source projects differently onto electrodes. Only I and
    # II are independent frontal leads; the remaining four are derived exactly.
    def frontal(angle):
        project = math.cos(math.radians(axis - angle))
        return [.14 * math.cos(math.radians(55 - angle)), -.065 * project,
                1.12 * project, -.20 * project, .29 * math.cos(math.radians(45 - angle)), 0.0]
    c = {"I": frontal(0), "II": frontal(60)}
    rs = ((.15, -.95), (.28, -1.05), (.65, -.65), (1.05, -.35), (1.18, -.16), (.95, -.09))
    for i, (r, s) in enumerate(rs, 1):
        c[f"V{i}"] = [.08 if i < 3 else .11, -.03 if i > 3 else 0, r, s,
                        (-.05, .17, .31, .34, .29, .23)[i - 1], 0]
    changes = {
        "st_elevation_anterior": (.04, 0, (.10, .30, .40, .30, .13, .07)),
        "st_elevation_inferior": (-.10, .20, (0, -.08, -.07, 0, 0, 0)),
        "st_elevation_lateral": (.20, .04, (0, 0, 0, .07, .20, .22)),
        "st_depression": (-.10, -.14, (0, -.07, -.12, -.17, -.18, -.15)),
    }
    if profile in changes:
        one, two, precordial = changes[profile]
        c["I"][5], c["II"][5] = one, two
        for i, st in enumerate(precordial, 1):
            c[f"V{i}"][5] = st
    if profile == "posterior_infarct":
        # Mirror image of a posterior injury current: ST depression with a tall R
        # and an upright, prominent T in the right precordial leads.
        for i, (st, t_wave, r) in enumerate(((-.12, .30, .55), (-.22, .42, 1.15), (-.18, .38, 1.35)), 1):
            c[f"V{i}"][5], c[f"V{i}"][4], c[f"V{i}"][2] = st, t_wave, r
        c["V1"][3], c["V2"][3], c["V3"][3] = -.35, -.40, -.35   # R/S ratio above one
        c["II"][5], c["I"][5] = -.03, -.02
    if profile == "de_winter":
        # Upsloping ST depression at the J point with tall, symmetric T waves; the
        # diffuse depression in I and II projects as ST elevation in aVR.
        for i, (st, t_wave) in enumerate(((-.10, .40), (-.16, .95), (-.16, 1.05), (-.14, .95), (-.10, .62), (-.07, .45)), 1):
            c[f"V{i}"][5], c[f"V{i}"][4] = st, t_wave
        c["I"][5], c["II"][5] = -.06, -.10
    if profile == "diffuse_st_depression_avr":
        # Global subendocardial ischaemia: depression everywhere, elevation in aVR.
        for i, st in enumerate((-.04, -.12, -.18, -.20, -.18, -.14), 1):
            c[f"V{i}"][5] = st
        c["I"][5], c["II"][5] = -.12, -.20
    if profile == "wellens":
        # Preserved R waves, no ST shift, deeply inverted or biphasic T waves in
        # the mid-precordial leads.
        for i, t_wave in enumerate((.05, -.28, -.45, -.40, -.10, .12), 1):
            c[f"V{i}"][4] = t_wave
            c[f"V{i}"][5] = 0.0
    if profile == "right_strain":
        c["I"][3] = -.45  # prominent terminal rightward forces
        c["I"][4], c["II"][4] = .04, -.19
        for i in range(1, 5):
            c[f"V{i}"][4] = (-.25, -.36, -.32, -.20)[i - 1]
        c["V1"][2], c["V1"][3] = .85, -.35
    if rhythm == "vt":
        for lead, weights in c.items():
            weights[0] = 0
            weights[4] = -.30 if weights[2] >= 0 else .30
    return c


def _signals(rate, rhythm, profile, seed, duration=DURATION_SECONDS, sample_hz=SAMPLE_HZ):
    pars = _parameters(rate, rhythm, profile)
    coeffs = _coefficients(profile, pars["axis_deg"], rhythm)
    times = _beat_times(rate, rhythm, duration, seed)
    # Complete block has an independent atrial clock (AV dissociation).
    atrial_times = _beat_times(75, "sinus", duration, seed) if rhythm == "complete_block" else []
    signals = {lead: [] for lead in LEADS}
    qrs, qt = pars["qrs_s"], pars["qt_s"]
    for index in range(int(duration * sample_hz) + 1):
        t = index / sample_hz
        basis = [0.0] * 6
        if rhythm == "vf":
            # Coarse VF is another common electrical source, not organized QRS.
            basis[2] = .32 * math.sin(2 * math.pi * 4.7 * t + .3 * math.sin(t * 1.7)) + .19 * math.sin(2 * math.pi * 7.1 * t)
            basis[3] = .21 * math.sin(2 * math.pi * 5.3 * t + .6)
        else:
            if rhythm == "af":
                basis[0] = .25 * math.sin(2 * math.pi * 6.8 * t + .6 * math.sin(t)) + .16 * math.sin(2 * math.pi * 9.2 * t + 1)
            elif rhythm == "flutter":
                # Fixed 2:1 illustrative flutter; atrial rate follows 2x ventricular.
                phase = (t * (rate * 2 / 60)) % 1
                basis[0] = -1.2 * (2 * phase - 1)
            elif rhythm == "complete_block":
                basis[0] = sum(_bump(t - start, .040, .040) for start in atrial_times if -.1 < t - start < .1)
            for start in times:
                dt = t - start
                if not -.25 < dt < qt + .02:
                    continue
                if rhythm == "sinus":
                    basis[0] += _bump(dt, -pars["pr_s"] + .040, .040)
                # Q, R and S occupy a shared QRS interval in every lead.
                basis[1] += _bump(dt, qrs * .14, qrs * .14)
                basis[2] += _bump(dt, qrs * .40, qrs * .23)
                basis[3] += _bump(dt, qrs * .76, qrs * .24)
                t_onset = qrs + .055
                basis[4] += _bump(dt, (t_onset + qt) / 2, (qt - t_onset) / 2)
                basis[5] += _plateau(dt, qrs - .005, qt)
        independent = {lead: sum(w * b for w, b in zip(weights, basis)) for lead, weights in coeffs.items()}
        i, ii = independent["I"], independent["II"]
        independent.update({"III": ii - i, "aVR": -(i + ii) / 2, "aVL": i - ii / 2, "aVF": ii - i / 2})
        for lead in LEADS:
            signals[lead].append(round(independent[lead], 6))
    return signals, pars, times


def acquire_ecg(state):
    """Freeze the current electrical state and acquisition time without mutation.

    Explicit profile keys live at state.ecg_profile (dynamic) or
    state.encounter_spec.ecg_profile (initial); absent means baseline morphology.
    Never pass a learner-selected suspected diagnosis as the profile.
    """
    snapshot = {"model_version": MODEL_VERSION, "status": "unavailable", "source": "educational_waveform_model",
                "acquired_at_minutes": deepcopy(state.get("sim_time", 0)),
                "sample_hz": SAMPLE_HZ, "duration_seconds": DURATION_SECONDS,
                "speed_mm_s": 25, "gain_mm_mv": 10}
    try:
        observable = deepcopy(state.get("observable", {}))
        rhythm = _rhythm(observable)
        rate = _finite(observable.get("hr"), "heart rate")
        if rhythm not in ("asystole", "vf") and not 20 <= rate <= 300:
            raise ValueError("Heart rate is outside this waveform model's range (20–300/min).")
        if rate < 0 or rate > 300:
            raise ValueError("Invalid heart rate.")
        profile = state.get("ecg_profile", state.get("encounter_spec", {}).get("ecg_profile", "baseline"))
        if profile not in PROFILES:
            raise ValueError("This ECG morphology profile has not been implemented.")
        if rhythm in ("vt", "vf", "asystole") and profile != "baseline":
            raise ValueError("This morphology/rhythm combination has not been implemented.")
        # Seed is fixed per encounter: repeat recordings at the same state agree.
        seed = int(state.get("seed") or state.get("encounter_spec", {}).get("seed") or 0)
        pars = _parameters(rate, rhythm, profile)
        snapshot.update({"status": "available", "profile": profile, "rhythm": rhythm,
                         "heart_rate": rate, "seed": seed,
                         "parameters": pars, "pulse_present": observable.get("pulse_present", True)})
        # This is provenance, not an automated diagnostic interpretation.
        digest_input = {"rate": rate, "rhythm": rhythm, "profile": profile, "seed": seed,
                        "time": snapshot["acquired_at_minutes"], "version": MODEL_VERSION}
        snapshot["recording_id"] = hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode()).hexdigest()[:16]
    except (TypeError, ValueError, OverflowError) as error:
        snapshot["reason"] = str(error)
    return snapshot


def ecg_signals(snapshot):
    """Reconstruct simultaneous mV samples from an immutable, compact snapshot."""
    if snapshot.get("status") != "available":
        return {}
    if snapshot.get("model_version") != MODEL_VERSION:
        raise ValueError("This recording requires its original waveform model version.")
    signals, _, _ = _signals(snapshot["heart_rate"], snapshot["rhythm"],
                             snapshot["profile"], snapshot["seed"],
                             snapshot["duration_seconds"], snapshot["sample_hz"])
    return signals


def _path(samples, start_s, seconds, hz, x, baseline, px_s, px_mv):
    first = round(start_s * hz)
    last = min(len(samples) - 1, round((start_s + seconds) * hz))
    points = [f"{x + (n / hz - start_s) * px_s:.2f},{baseline - samples[n] * px_mv:.2f}" for n in range(first, last + 1)]
    return "M" + " L".join(points)


def _time_label(minutes):
    try:
        total = max(0, round(float(minutes) * 60))
        return f"{total // 60:02d}:{total % 60:02d}"
    except (TypeError, ValueError, OverflowError):
        return "—"


def render_ecg_svg(snapshot):
    """Render 12 distinct leads with 10 s rhythm strip, grid and true calibration.

    Four display columns use successive 2.5 s portions of the simultaneous
    source recording. Source arrays retain all 10 s for every lead.
    """
    if snapshot.get("status") != "available":
        reason = escape(str(snapshot.get("reason", "Recording unavailable.")))
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 130" role="img" aria-label="ECG unavailable"><rect width="1120" height="130" fill="#fafafa"/><text x="24" y="50" font-size="22" fill="#333">ECG unavailable</text><text x="24" y="87" font-size="16" fill="#555">{reason}</text></svg>'
    # 4px = one printed mm; 100px = one second; 40px = one mV.
    mm, left, top, row_height = 4, 70, 75, 142
    width, height = 1120, 705
    suffix = escape(str(snapshot.get("recording_id", "ecg")), quote=True)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="280mm" height="176.25mm" style="width:100%;height:auto" role="img" aria-label="12-lead simulated ECG acquired at {_time_label(snapshot.get("acquired_at_minutes"))}">',
             f'<defs><pattern id="small-{suffix}" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M4 0H0V4" fill="none" stroke="#f2d9dd" stroke-width=".35"/></pattern><pattern id="grid-{suffix}" width="20" height="20" patternUnits="userSpaceOnUse"><rect width="20" height="20" fill="url(#small-{suffix})"/><path d="M20 0H0V20" fill="none" stroke="#dcadb4" stroke-width=".65"/></pattern></defs>',
             '<rect width="1120" height="705" fill="#fffdfb"/>',
             f'<rect x="20" y="58" width="1080" height="595" fill="url(#grid-{suffix})"/>',
             f'<text x="24" y="30" font-size="19" font-family="sans-serif" fill="#222">12-lead ECG · {_time_label(snapshot.get("acquired_at_minutes"))}</text>',
             '<text x="1094" y="30" text-anchor="end" font-size="15" font-family="sans-serif" fill="#333">25 mm/s · 10 mm/mV · 500 Hz</text>']
    signals, hz = ecg_signals(snapshot), snapshot["sample_hz"]
    for row in range(4):
        baseline = top + row * row_height + 89
        # 1 mV by 0.2 s rectangle; the pulse uses the exact same transforms.
        parts.append(f'<path class="calibration" data-mv="1" data-seconds="0.2" d="M30 {baseline}h6v-40h20v40h6" fill="none" stroke="#363035" stroke-width="1.25"/>')
        columns = [("II", 0)] if row == 3 else [(lead, col) for col, lead in enumerate(LAYOUT[row])]
        for lead, col in columns:
            x = left + col * 250
            duration, start = (10.0, 0) if row == 3 else (2.5, col * 2.5)
            parts.append(f'<text x="{x + 5}" y="{baseline - 62}" font-family="sans-serif" font-size="15" font-weight="600" fill="#362930">{lead}</text>')
            path = _path(signals[lead], start, duration, hz, x, baseline, mm * 25, mm * 10)
            parts.append(f'<path data-lead="{lead}" data-start-s="{start}" d="{path}" fill="none" stroke="#22252a" stroke-width="1.05" stroke-linejoin="round"/>')
            if row < 3 and col:
                parts.append(f'<path d="M{x} {baseline - 40}v70" stroke="#7a6570" stroke-width=".65"/>')
    parts.append('<text x="24" y="680" font-family="sans-serif" font-size="13" fill="#595257">Simulated recording · 3×4 sequential 2.5 s panels + 10 s lead II · Educational waveform model</text></svg>')
    return "".join(parts)


def monitor_wave_svg(observable, profile="baseline", seed=0):
    """Short bedside Lead-II display. Electrical activity does not imply a pulse."""
    try:
        rhythm = _rhythm(observable)
        rate = _finite(observable.get("hr"), "heart rate")
        if rhythm not in ("vf", "asystole") and not 20 <= rate <= 300:
            raise ValueError("Rate unavailable")
        if not 0 <= rate <= 300:
            raise ValueError("Rate unavailable")
        if profile not in PROFILES:
            raise ValueError("Morphology unavailable")
        if rhythm in ("vt", "vf", "asystole") and profile != "baseline":
            raise ValueError("Morphology/rhythm combination unavailable")
        signals, _, _ = _signals(rate, rhythm, profile, int(seed), duration=4, sample_hz=250)
        path = _path(signals["II"], 0, 4, 250, 10, 80, 145, 42)
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 132" role="img" aria-label="Bedside lead II monitor"><rect width="600" height="132" fill="#08131b"/><text x="12" y="22" fill="#71ef9b" font-size="16" font-family="monospace">II</text><path d="' + path + '" fill="none" stroke="#71ef9b" stroke-width="1.8" stroke-linejoin="round"/><style>@keyframes mrs-ecg-sweep {from {transform:translateX(0)} to {transform:translateX(632px)}} .mrs-ecg-sweep {animation:mrs-ecg-sweep 4s linear infinite} @media (prefers-reduced-motion:reduce) {.mrs-ecg-sweep {display:none}}</style><g class="mrs-ecg-sweep"><rect x="-32" y="28" width="24" height="101" fill="#08131b"/><path d="M-8 28v101" stroke="#71ef9b" stroke-opacity=".20" stroke-width="1"/></g></svg>'
    except (ValueError, TypeError, OverflowError):
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 132" role="img" aria-label="Electrical waveform unavailable"><rect width="600" height="132" fill="#08131b"/><text x="20" y="70" fill="#e8ca86" font-size="20" font-family="monospace">Electrical waveform unavailable</text></svg>'
