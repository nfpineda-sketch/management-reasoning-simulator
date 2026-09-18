# Visual resuscitation bay v0.13.1

Development app only: clinical-management-reasoning-dev.streamlit.app.

The opening workspace now shows a schematic patient bed, a large bedside monitor,
the existing dynamic synthetic lead II strip, and a large ECG dialog. The orders
panel appears before the expandable full clinical chart. Arrival handover is
expanded initially and collapses after the first exchange; the latest exchange
remains visible in a scrollable panel. All original reports and examination data
remain accessible in the clinical chart.

Equipment overlays follow executed oxygen, NIV, invasive ventilation and
vasoactive treatment flags. Doses are displayed from the treatment record.
The illustration is a schematic equipment view, not a representation of physical
signs or diagnostic severity. No animated breathing or invented waveform is added.
Monitor observations update when the engine executes actions. The SVG uses the
existing engine's synthetic lead II rhythm strip, not a diagnostic 12-lead ECG.

This does not change physiological rules, reasoning requirements, authentication,
assessment or persistence. Only clinical-encounter-v0.13 is updated.
