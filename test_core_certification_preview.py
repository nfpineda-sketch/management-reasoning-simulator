"""PHASE2_AMENDMENT_1: la vista previa de certificacion, como plugin de pytest EXPLICITO.

Un sucesor del cierre de la Fase 2 es aceptado por el runtime solo cuando su propio registro dice CERTIFIED, y ese
registro se promueve solo DESPUES de una certificacion en verde. Por eso la corrida de certificacion tiene que
ejercitar el runtime tal como quedara una vez promovido, mientras el linaje real, sin promover, lo sigue rechazando.
Las dos cosas son ciertas a la vez asi:

  * la vista previa existe SOLO en este archivo de pruebas. Ningun modulo del runtime lee la bandera, ni conftest.py
    carga este plugin: nada fuera de una corrida de pruebas que lo nombre puede ser "previsualizado" a aceptacion;
  * hay que pedirla dos veces y de forma explicita: cargando el plugin en la linea de comandos y nombrando la version

        MRS_CORE_CERTIFICATION_PREVIEW=PHASE2_AMENDMENT_1 python3 -m pytest -p test_core_certification_preview ...

  * hace una sola cosa: para la UNICA version que la bandera nombra, un estado CANDIDATE se lee como CERTIFIED. No
    puede inventar una entrada del linaje, ni ligar un registro a un digesto que no declara, ni reparar un cierre
    historico roto: las otras tres condiciones de la compuerta se evaluan igual;
  * una prueba marcada ``real_core_lineage`` ve siempre el estado real: los controles negativos y la prueba de la
    compuerta real nunca se previsualizan.

Tras la promocion el registro mismo dice CERTIFIED y este plugin no cambia nada.

El nombre empieza por ``test_`` a proposito: es codigo de pruebas, y las guardas de aislamiento de la Fase 3 (R13,
H20) solo admiten que lean la capa sombra los dos puntos de cableado y el codigo de pruebas.
"""
import os

import pytest

CORE_CERTIFICATION_PREVIEW_FLAG = "MRS_CORE_CERTIFICATION_PREVIEW"


def _banner() -> str:
    wanted = os.environ.get(CORE_CERTIFICATION_PREVIEW_FLAG, "").strip()
    if not wanted:
        return f"core certification preview: plugin loaded, INACTIVE ({CORE_CERTIFICATION_PREVIEW_FLAG} is not set)"
    return (f"core certification preview: ACTIVE for {wanted} -- a CANDIDATE status of that version reads as "
            "CERTIFIED in unmarked tests; this run is NOT evidence that the real lineage accepts it")


def pytest_report_header(config):
    """Una corrida previsualizada lo dice: el plugin tambien puede cargarse por PYTEST_ADDOPTS o PYTEST_PLUGINS,
    asi que no basta con mirar la linea de comandos para saber si estuvo activo."""
    return _banner()


def pytest_terminal_summary(terminalreporter):
    """Y lo repite al final, que es lo unico que queda en el log de una corrida con ``-q``."""
    terminalreporter.write_line(_banner())


@pytest.fixture(autouse=True, scope="session")
def _core_certification_preview():
    wanted = os.environ.get(CORE_CERTIFICATION_PREVIEW_FLAG, "").strip()
    if not wanted:
        yield
        return
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    real = ev.successor_status

    def previewed(entry):
        status = real(entry)
        return rs.CERTIFIED if entry.version_id == wanted and status == rs.CANDIDATE else status

    previewed.real = real
    ev.successor_status = previewed
    yield
    ev.successor_status = real


@pytest.fixture(autouse=True)
def _real_core_lineage(request, monkeypatch):
    if request.node.get_closest_marker("real_core_lineage") is not None:
        import runtime_shadow_evidence as ev
        real = getattr(ev.successor_status, "real", None)
        if real is not None:
            monkeypatch.setattr(ev, "successor_status", real)
    yield
