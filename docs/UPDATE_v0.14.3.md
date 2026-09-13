# v0.14.3: problem-first launch

The development shared-access selector contains only implemented curriculum
problems. PS001 and PS002 fixed classroom cases are not launch options.
Every new encounter calls the bounded generator with the chosen problem ID.
Repeating an encounter also generates a new case from its stored problem ID,
while preserving the existing adaptation-plan workflow. Legacy selector values
are handled without exposing fixed cases. Account-based assignment is unchanged.
Internal PS001 family identifiers remain engine implementation details, not
selectable encounters. The generator still uses the implemented reviewed profile
set and local fallback if the provider is unavailable.

Validation: eight launch, repeat, exploration and rendering tests passed.
Only clinical-encounter-v0.13 is updated. No new secrets are required.
