import subprocess
import sys


ACTIVE_REGRESSIONS = [
    "regression_v06013.py",
    "regression_v06014.py",
    "regression_v06015.py",
    "regression_v06017_compound_commands.py",
    "regression_v06018_stop_label.py",
    "regression_v06019_neuro_hypotension.py",
    "regression_v06020_management_trace.py",
    "regression_v06021_management_trace_ui.py",
    "regression_v06022_reasoning_capture.py",
    "regression_v06023_reasoning_capture.py",
    "regression_v06024_learner_management_trace.py",
    "regression_v06025_management_trace_timeline.py",
    "regression_v06026_reflect_compare.py",
    "regression_v06028_trace_recognized_actions.py",
    "regression_v06033_reasoning_capture.py",
    "regression_v06034_turn_isolation.py",
    "regression_v06035_full_pipeline.py",
    "regression_v06036_reflect_compare_v2.py",
    "regression_v072_compound_order_integrity.py",
    "regression_v073_clinical_coherence.py",
    "regression_v074_reasoning_fidelity.py",
    "regression_v075_counterfactual_coherence.py",
    "regression_v076_treatment_continuity.py",
    "regression_v077_reasoning_state_visibility.py",
    "regression_v078_state_aware_respiratory.py",
    "regression_v079_temporal_reasoning_fidelity.py",
    "regression_v0710_context_aware_diagnostics.py",
    "regression_v0711_action_order_adaptation.py",
    "regression_v0712_target_aware_adaptive_reflection.py",
    "regression_v0713_longitudinal_intent_treatment_state.py",
    "regression_v0714_interactive_decision_review.py",
    "regression_v0715_compact_review_workflow.py",
    "regression_v0716_field_specific_adaptation_drafts.py",
    "regression_v080_delayed_expert_comparison.py",
    "regression_v081_carry_forward_repeat.py",
    "regression_v082_persistent_vitals.py",
    "regression_v083_cardioversion_intent_and_ps001_history.py",
    "regression_v084_antibiotic_intent.py",
    "regression_v085_dynamic_ps001_pocus.py",
    "regression_v086_ps001_classroom_review.py",
    "regression_v087_pdf_export.py",
    "regression_v088_fluid_oxygen_quantity_scope.py",
    "regression_v089_reasoning_gate_action_transparency.py",
    "regression_v0810_flexible_reasoning_completion.py",
    "regression_v0811_coreference_and_completion_display.py",
    "regression_v0812_natural_priority_phrase.py",
    "regression_v0813_direct_goal_priority.py",
    "regression_v0814_partial_reasoning_and_sedation_transparency.py",
    "regression_v0815_executable_procedural_sedation.py",
    "regression_v0816_flexible_gate_and_state_transparency.py",
    "regression_v0817_post_cardioversion_semantic_slots.py",
    "regression_v0818_reassessment_checkpoint_and_fluid_trajectory.py",
    "regression_v0819_trajectory_review_and_pdf.py",
    "regression_v0821_lower_initial_ps001_bp.py",
    "regression_v0821_dynamic_ecg_strip.py",
]


for regression in ACTIVE_REGRESSIONS:
    completed = subprocess.run([sys.executable, regression], check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)

print(f"PASS: {len(ACTIVE_REGRESSIONS)} active regression scripts")
