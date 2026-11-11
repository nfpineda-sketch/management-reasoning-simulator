"""P3-179: los mutantes de la fisiologia de la Enmienda 2 deben ser detectados TAMBIEN por las pruebas de la capa integrada.

Cada mutante rompe, en el modulo de fisiologia y solo durante una corrida de pytest, una conducta que la docencia exigio
(``test_amendment_2_mutants_plugin``: F inerte, F instantanea, escalera directa de PAS en el nivel, escalera directa de
SpO2 en el nivel, colapso por maximo -- el OR en vez del Y --, F que limpia tan rapido como sube). Aqui se corren las
pruebas de la sombra GI (la serie en vivo contra el registro medido) mas el archivo de familias del nucleo: la corrida de
control debe ser verde y cada mutante debe hacer fallar al menos una. Un superviviente seria una conducta sin proteger.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

import test_amendment_2_mutants_plugin as plugin

ROOT = Path(__file__).resolve().parent
SELECTED = ("f_is_inert", "f_is_the_instantaneous_signal", "direct_pressure_ladder_in_the_level",
            "direct_saturation_ladder_in_the_level", "collapse_by_maximum", "f_clears_as_fast_as_it_rises")
LAYER = ("test_phase3_gi_amendment_2_shadow.py::test_a_live_series_reproduces_what_was_recorded_digest_free_and_apart_per_witness",
         "test_phase3_gi_amendment_2_shadow.py::test_a_live_untreated_series_reproduces_the_recorded_onsets_and_the_collapse_through_minute_215",
         "test_phase2_amendment_2_families.py")


def _run(mutant: str):
    env = {**os.environ, plugin.FLAG: mutant, "PYTHONPATH": str(ROOT)}
    return subprocess.run([sys.executable, "-m", "pytest", "-x", "--tb=no", "-p", "no:cacheprovider", "-p",
                           "test_amendment_2_mutants_plugin", *LAYER], cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=1200)


def test_the_selected_mutants_are_all_known_to_the_plugin():
    assert set(SELECTED) <= set(plugin.MUTANTS)


def test_the_control_run_without_a_mutant_is_green_on_the_layer_tests():
    result = _run("")
    assert result.returncode == 0, result.stdout[-1500:]
    assert "INACTIVE" in result.stdout


@pytest.mark.parametrize("mutant", SELECTED)
def test_each_physiology_mutant_is_caught_by_the_integrated_layer_tests(mutant):
    result = _run(mutant)
    assert result.returncode != 0, f"mutant {mutant!r} SURVIVED the integrated layer: a required behaviour is not protected"
    assert f"ACTIVE: {mutant}" in result.stdout
