"""Refresh changed generation and visual stacks during a Streamlit hot update."""
import importlib
import sys
from threading import RLock


# Keep the same lock when this bootstrap module itself is upgraded in a process
# that already has Streamlit sessions waiting on it.
_LOCK = globals().get("_LOCK") or RLock()
RELOAD_VERSION = "0.24.2"
_EXECUTION_RELEASE = "0.24.2"
_EXECUTION_MODULES = ('family_engine', 'generated_engine', 'coupled_encounter', 'clinical_physiology', 'generated_case_schema')
_MODULES = (
    "shared_order_language", "shared_order_quantities", "active_order_context",
    "family_parser", "family_engine", "pending_family_orders",
    "generated_case_validation",
    "generated_delivery", "generated_response", "generated_dynamics", "generated_rhythm", "pending_cancellation",
    "clinical_core_defaults", "clinical_physiology", "clinical_diagnostics", "generated_physiology", "coupled_encounter", "generated_engine",
    "generated_engine_diagnostics",
    "generated_case_coverage",
    "generated_case_schema",
    "generated_case_capabilities",
    "generated_case_errors",
    "generated_case",
    "encounter_generator",
)
_VISUAL_RELEASES = {
    "patient_appearance": ("APPEARANCE_VERSION", 4),
    "scene_pipeline": ("SCENE_PIPELINE_VERSION", 9),
    "clinical_scene": ("SCENE_RENDER_VERSION", 12),
    "resuscitation_room": ("ROOM_RENDER_VERSION", 8),
}
_VISUAL_MODULES = (
    "shared_order_language", "shared_order_quantities", "active_order_context",
    "family_parser", "family_engine", "pending_family_orders",
    "scene_errors", "patient_appearance", "image_consistency", "scene_jobs",
    "scene_repair", "scene_pipeline", "scene_preparation", "clinical_scene", "resuscitation_room",
)


def refresh_visual_modules():
    """Check and reload visual dependencies under the shared process lock."""
    with _LOCK:
        stale = any(
            name in sys.modules and getattr(sys.modules[name], marker, None) != version
            for name, (marker, version) in _VISUAL_RELEASES.items()
        )
        if not stale:
            return False
        for name in _VISUAL_MODULES:
            module = sys.modules.get(name)
            if module is None:
                importlib.import_module(name)
            else:
                importlib.reload(module)
        return True


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
        ) or any(
            name in sys.modules
            and getattr(sys.modules[name], "EXECUTION_VERSION", None) != _EXECUTION_RELEASE
            for name in _EXECUTION_MODULES
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
