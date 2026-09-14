"""Refresh one changed generator stack during a Streamlit hot update."""
import importlib
import sys
from threading import RLock


_LOCK = RLock()
_MODULES = (
    "generated_case_validation",
    "generated_engine",
    "generated_engine_diagnostics",
    "generated_case_schema",
    "generated_case_capabilities",
    "generated_case_errors",
    "generated_case",
    "encounter_generator",
)


def refresh_generation_modules(expected_version):
    """Keep compiler, exception classes and callback signatures from one release.

    A fresh process imports normally. Only a cached author/wrapper with an old
    release marker triggers this fixed dependency list; no session is reset and
    no case is generated here. The runtime UI imports its aliases afterwards.
    """
    with _LOCK:
        stale = any(
            name in sys.modules
            and getattr(sys.modules[name], "GENERATOR_VERSION", "") != expected_version
            for name in ("generated_case", "encounter_generator")
        )
        if not stale:
            return False
        for name in _MODULES:
            module = sys.modules.get(name)
            if module is None:
                importlib.import_module(name)
            else:
                importlib.reload(module)
        return True
