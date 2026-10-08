"""The Spanish sentinel (X-1, §10; B-5, IG-0): a Spanish encounter shows no English it should not.

Each pilot case is walked on the real page in Spanish (``tools_spanish_sentinel.walk``):
the dashboard, the room, the conversation, every region of the examination, the reasoning
gate, the questions about an incomplete order, cancelling, the definitive treatment or the
family's turning point, a wait, a reassessment, the ECG and the close. A line with English
in it fails the case, except what the resident wrote, the canonical names the faculty kept
and the bilingual language selector. The detector itself is checked first, on lines whose
answer is known.
"""
import pytest

import pilot_freeze
import tools_spanish_sentinel as sentinel


@pytest.mark.parametrize("line, english", [
    ("Examine patient", {"examine", "patient"}),
    ("Specify or confirm norepinephrine dose and units (mcg/min or mcg/kg/min).", {"specify", "norepinephrine"}),
    ("Tras naloxone 0.4 mg IV, PA 106/64 mmHg.", {"naloxone"}),
    ("Respiratory rate 12 /min; breaths remain shallow.", {"respiratory", "shallow"}),
    ("Current treatments", {"current", "treatments"}),
])
def test_the_detector_finds_english(line, english):
    assert english <= set(sentinel.english_words(line)), sentinel.english_words(line)


@pytest.mark.parametrize("line", [
    "Examinar al paciente",
    "Tras noradrenalina 0.1 mcg/kg/min, PA 92/58 mmHg · FC 104/min.",
    "No has registrado un destino. ¿Quieres continuar o finalizar?",
    "Pupilas pequeñas y reactivas, y retiro bilateral breve ante un estímulo firme.",
    "El nuevo Management Trace registra sólo lo que haces ahora.",
    "Indica la dosis de «ceftriaxone» en miligramos.",
    "ECG · 12 derivaciones · FiO₂ 40% · PEEP 5 cm H₂O · CPAP · BiPAP · IV · IM · mL/h",
])
def test_the_detector_leaves_spanish_codes_and_quoted_words_alone(line):
    assert not sentinel.english_words(line)


def test_the_declared_exceptions_are_only_these():
    assert sentinel.CANONICAL == ("MANAGEMENT REASONING SIMULATOR", "Management Reasoning Simulator",
                                  "Management Trace")
    assert all("Idioma" in line or "Fijo durante" in line or line == "English" for line in sentinel.BILINGUAL)


@pytest.mark.xfail(strict=True, reason="B-5 IG-5 (X-1) is not implemented yet: the room still shows English")
@pytest.mark.parametrize("variant", pilot_freeze.accepted_variants())
def test_a_spanish_encounter_shows_no_english(variant, tmp_path):
    result = sentinel.walk(variant, tmp_path)
    assert not result["stopped"], result["stopped"]
    shown = "\n".join(f"[{row['step']}] {row['where']}: {row['line']}  ← {row['english']}"
                      for row in result["english"])
    assert not result["english"], f"{len(result['english'])} lines with English:\n{shown}"
