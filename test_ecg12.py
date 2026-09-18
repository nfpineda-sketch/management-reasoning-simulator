"""Signal-level regressions: these test numerical consistency, not clinical validity."""
import json
import re
import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from ecg12 import LEADS, PROFILES, SAMPLE_HZ, acquire_ecg, ecg_signals, render_ecg_svg, monitor_wave_svg


def state(rhythm="Sinus rhythm", hr=60, profile="baseline"):
    return {"seed": 17, "sim_time": 2.5, "observable": {"rhythm": rhythm, "hr": hr, "sbp": 90, "spo2": 93}, "ecg_profile": profile}


class ECGRecordingTests(unittest.TestCase):
    def test_compact_snapshot_frozen_and_json_serializable(self):
        live = state("AF", 162)
        before = deepcopy(live)
        recording = acquire_ecg(live)
        self.assertEqual(live, before)
        self.assertEqual(recording["status"], "available")
        self.assertEqual(recording["acquired_at_minutes"], 2.5)
        self.assertLess(len(json.dumps(recording)), 1500)
        original = render_ecg_svg(recording)
        live["sim_time"] = 8
        live["observable"].update(rhythm="Sinus rhythm", hr=75)
        second = acquire_ecg(live)
        self.assertEqual(original, render_ecg_svg(recording))
        self.assertNotEqual(original, render_ecg_svg(second))
        self.assertEqual(recording, json.loads(json.dumps(recording)))

    def test_limb_relationships_hold_sample_by_sample_for_all_profiles(self):
        for profile in PROFILES:
            with self.subTest(profile=profile):
                signals = ecg_signals(acquire_ecg(state("AF", 162, profile)))
                self.assertEqual(set(signals), set(LEADS))
                for index in range(0, len(signals["I"]), 7):
                    one, two = signals["I"][index], signals["II"][index]
                    for lead, expected in (("III", two - one), ("aVR", -(one + two) / 2), ("aVL", one - two / 2), ("aVF", two - one / 2)):
                        self.assertAlmostEqual(signals[lead][index], expected, delta=1.1e-6)

    def test_distinct_precordial_morphology_and_shared_activation(self):
        signals = ecg_signals(acquire_ecg(state()))
        # First QRS starts at 0.0. R dominates later precordials, S dominates V1.
        interval = slice(0, int(.09 * SAMPLE_HZ))
        r_peaks = []
        for i in range(1, 7):
            segment = signals[f"V{i}"][interval]
            r_peaks.append(max(segment))
            self.assertEqual(segment.index(max(segment)), 18)  # synchronized R
        self.assertLess(r_peaks[0], r_peaks[1])
        self.assertLess(r_peaks[1], r_peaks[2])
        self.assertLess(r_peaks[2], r_peaks[3])
        self.assertGreater(abs(min(signals["V1"][interval])), max(signals["V1"][interval]))
        self.assertGreater(max(signals["V6"][interval]), abs(min(signals["V6"][interval])))
        self.assertEqual(len({tuple(signals[f"V{i}"]) for i in range(1, 7)}), 6)

    def test_af_irregularity_and_rate_vs_sinus(self):
        def peaks(data):
            return [i / SAMPLE_HZ for i in range(1, len(data) - 1) if data[i] > .8 and data[i] > data[i - 1] and data[i] >= data[i + 1]]
        sinus = peaks(ecg_signals(acquire_ecg(state("Sinus rhythm", 120)))["II"])
        af = peaks(ecg_signals(acquire_ecg(state("AF", 120)))["II"])
        self.assertEqual(len(sinus), 20)
        rr_sinus = [b - a for a, b in zip(sinus, sinus[1:])]
        rr_af = [b - a for a, b in zip(af, af[1:])]
        self.assertLess(max(rr_sinus) - min(rr_sinus), .003)
        self.assertGreater(max(rr_af) - min(rr_af), .15)
        self.assertAlmostEqual(60 / (sum(rr_af) / len(rr_af)), 120, delta=6)

    def test_measurable_pr_qrs_and_st_profiles(self):
        recording = acquire_ecg(state())
        p = recording["parameters"]
        self.assertEqual(p["qrs_s"], .09)
        self.assertEqual(p["pr_s"], .16)
        # J+30 ms is after QRS and before T onset; amplitude = assigned ST.
        sample = round(.12 * SAMPLE_HZ)
        inferior = ecg_signals(acquire_ecg(state(profile="st_elevation_inferior")))
        self.assertGreater(inferior["II"][sample], .15)
        self.assertGreater(inferior["III"][sample], .25)
        self.assertLess(inferior["aVL"][sample], -.15)
        anterior = ecg_signals(acquire_ecg(state(profile="st_elevation_anterior")))
        for lead in ("V2", "V3", "V4"):
            self.assertGreater(anterior[lead][sample], .25)
        depressed = ecg_signals(acquire_ecg(state(profile="st_depression")))
        for lead in ("V4", "V5", "V6"):
            self.assertLess(depressed[lead][sample], -.10)
        strain = ecg_signals(acquire_ecg(state(profile="right_strain")))
        t_peak = round(((p["qrs_s"] + .055 + p["qt_s"]) / 2) * SAMPLE_HZ)
        for lead in ("V1", "V2", "V3", "V4"):
            self.assertLess(strain[lead][t_peak], -.15)

    def test_unknown_rhythm_pea_and_invalid_values_do_not_invent_recordings(self):
        for rhythm, rate in (("unknown", 80), ("PEA", 70), ("AF", float("nan")), ("Sinus rhythm", 0), ("AF", 700)):
            with self.subTest(rhythm=rhythm, rate=rate):
                recording = acquire_ecg(state(rhythm, rate))
                self.assertEqual(recording["status"], "unavailable")
                self.assertEqual(ecg_signals(recording), {})
                self.assertIn("ECG unavailable", render_ecg_svg(recording))
        live = state("PEA", 70)
        live["observable"]["electrical_rhythm"] = "Sinus rhythm"
        live["observable"]["pulse_present"] = False
        recording = acquire_ecg(live)
        self.assertEqual(recording["status"], "available")
        self.assertFalse(recording["pulse_present"])
        # Lack of a pulse never changes electrical activity to a flat line.
        self.assertGreater(max(ecg_signals(recording)["II"]), .9)

    def test_suspicion_and_low_pressure_do_not_select_morphology(self):
        live = state()
        del live["ecg_profile"]
        live.update(suspected_diagnosis="pulmonary embolism", learner_text="STEMI?")
        live["observable"].update(sbp=50, spo2=70)
        self.assertEqual(acquire_ecg(live)["profile"], "baseline")
        live["encounter_spec"] = {"ecg_profile": "right_strain"}
        self.assertEqual(acquire_ecg(live)["profile"], "right_strain")

    def test_svg_leads_order_grid_calibration_and_no_diagnostic_giveaway(self):
        svg = render_ecg_svg(acquire_ecg(state(profile="st_elevation_inferior")))
        root = ET.fromstring(svg)
        paths = [p for p in root.iter() if "data-lead" in p.attrib]
        self.assertEqual([p.attrib["data-lead"] for p in paths], ["I", "aVR", "V1", "V4", "II", "aVL", "V2", "V5", "III", "aVF", "V3", "V6", "II"])
        self.assertEqual([p.attrib["data-start-s"] for p in paths[:4]], ["0.0", "2.5", "5.0", "7.5"])
        pulses = [p for p in root.iter() if p.attrib.get("class") == "calibration"]
        self.assertEqual(len(pulses), 4)
        self.assertTrue(all("v-40h20v40" in p.attrib["d"] for p in pulses))
        self.assertIn('width="4" height="4"', svg)
        self.assertIn("25 mm/s · 10 mm/mV", svg)
        self.assertNotIn("st_elevation", svg)
        self.assertNotIn("STEMI", svg)

    def test_monitor_uses_same_explicit_profile_seed_and_has_reduced_motion(self):
        obs = {"rhythm": "AF", "hr": 162}
        baseline = monitor_wave_svg(obs, "baseline", 17)
        self.assertNotEqual(baseline, monitor_wave_svg(obs, "st_elevation_inferior", 17))
        self.assertNotEqual(baseline, monitor_wave_svg(obs, "baseline", 83))
        self.assertIn("prefers-reduced-motion", baseline)
        self.assertIn("waveform unavailable", monitor_wave_svg({"rhythm": "VT", "hr": 180}, "st_depression"))

    def test_supported_tachy_brady_and_arrest_waveforms(self):
        for rhythm, rate in (("Sinus bradycardia", 35), ("Sinus tachycardia", 170), ("SVT", 190), ("atrial flutter", 150), ("complete heart block", 35), ("VT", 180), ("junctional rhythm", 45), ("VF", 0), ("asystole", 0)):
            with self.subTest(rhythm=rhythm):
                recording = acquire_ecg(state(rhythm, rate))
                self.assertEqual(recording["status"], "available")
                signals = ecg_signals(recording)
                self.assertEqual(len(signals["II"]), 5001)
                ET.fromstring(monitor_wave_svg({"rhythm": rhythm, "hr": rate}))
                if rhythm == "asystole":
                    self.assertEqual(set(signals["II"]), {0.0})
                else:
                    self.assertGreater(max(signals["II"]) - min(signals["II"]), .1)


if __name__ == "__main__":
    unittest.main()
