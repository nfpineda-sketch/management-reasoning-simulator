# Fase 1 · Primer prompt (preparado; NO ejecutado)

> **No ejecutar** mientras no se cumpla la puerta de arranque (`docs/revision/PHASE_1_KICKOFF_PACKAGE.md`, §7I).
>
> **Antes de usarlo, reemplazar:**
> - `<SHA_FINAL>`: el SHA de 40 caracteres congelado del piloto;
> - `<PHASE1_BRANCH>`: la rama decidida (recomendada: `phase-1-contracts-v2`);
> - `<AUTHORIZATION_DATE>`: la fecha de la autorización.
>
> El cuerpo va en inglés, como los encargos anteriores. La respuesta sale en español (CLAUDE.md). Ejecuta **sólo
> WP0** y se detiene.

---

```text
PHASE 1 — WORK PACKAGE 0 ONLY: CONTRACT BASELINE AND EQUIVALENCE HARNESS

Authorization (<AUTHORIZATION_DATE>): Phase 1 (Contracts v2) is open on branch <PHASE1_BRANCH>, created from the
pilot-frozen SHA <SHA_FINAL>. This prompt authorizes WP0 only. Read docs/revision/PHASE_1_KICKOFF_PACKAGE.md
(§7A–§7I) first; it is the plan. CLAUDE.md applies in full.

0. PRECONDITIONS — verify, and STOP and report if any fails:
   - git rev-parse <SHA_FINAL> resolves to a commit, and origin/pilot-residents-v1 points to it
     (git ls-remote origin refs/heads/pilot-residents-v1).
   - The current branch is <PHASE1_BRANCH>, its merge-base with <SHA_FINAL> is <SHA_FINAL>, and the tree is clean.
     If the branch does not exist yet, create it locally from <SHA_FINAL> (git switch -c <PHASE1_BRANCH> <SHA_FINAL>).
     Do not push.
   - CLAUDE.md names <PHASE1_BRANCH> as the authorized branch. If it still names clinical-encounter-v0.13, STOP:
     the two sources disagree, and the owner decides.
   - The reader freeze holds: git diff 3d942ee -- family_parser.py shared_order_language.py
     shared_order_quantities.py active_order_context.py weight_based_doses.py is empty.

1. GOAL (WP0). Build a deterministic harness that records the behavior of <SHA_FINAL>, and fails on the first
   difference in any later commit. For each of the 30 accepted pilot cases (pilot_freeze.accepted_variants()), in
   English and in Spanish, it plays a fixed script set:
   - the pilot_acceptance battery scripts, seed 17;
   - the order-reading rehearsal (tools_order_reading.py --play es|en).

   For every turn it records:
   - the actions the engine received (after strip_tags);
   - each order's fate and the receipt lines;
   - minutes before and after, and what stopped the clock;
   - events, with cause class, preventability and source_order_ids;
   - the observation snapshot (current_findings), in both languages;
   - the Trace fields of the turn, with volatile values normalized and the normalization listed explicitly
     (submission ids, wall-clock timestamps).

   Store the record as test_data/contracts_baseline_<first 8 of SHA_FINAL>.json.

2. FILES. New files only:
   - tools_contract_baseline.py, with --write and --check;
   - test_contract_equivalence.py;
   - the JSON record above.
   Add to the existing docs only: a WP0 section in docs/revision/PHASE_1_KICKOFF_PACKAGE.md, and the Decision File
   update.

3. MUST NOT CHANGE: any runtime module, any existing test, regression or golden file, case_text/, rubric_text/,
   validation/, the baselines, the reader files above, pilot_freeze.py and its manifest. If the harness cannot
   observe something without a runtime change, record it as a WP0 gap and do not change the runtime.

4. ACCEPTANCE:
   (a) --write twice on <SHA_FINAL> gives byte-identical files. If not, STOP and report the nondeterminism with its
       source.
   (b) test_contract_equivalence.py passes on <SHA_FINAL>.
   (c) A seeded mutation makes it fail, naming the case, turn and field, and is then reverted. Use a temporary
       one-line change to a receipt string, run in a scratch copy, never committed.
   (d) Focused tests: test_phase0_acceptance_battery.py, test_phase0_order_ledger.py,
       test_phase0_time_and_events.py and test_phase0_observation_and_provenance.py stay green.
   (e) git diff <SHA_FINAL> -- . ':(exclude)docs' ':(exclude)test_data/contracts_baseline_*'
       ':(exclude)tools_contract_baseline.py' ':(exclude)test_contract_equivalence.py' is empty.
   (f) Runtime cost: report the harness wall-clock time. 0 app AI calls (deterministic).

5. DELIVER: one local commit with the CLAUDE.md attribution lines. No push, no PR, no deploy, no Neon, no Streamlit.

6. STOP after WP0. Do not start WP1. Report in Spanish: RESULTADOS → VERIFICACIÓN → LIMITACIONES → DECISIONES
   PENDIENTES. Include:
   - the record's size and hash;
   - the list of normalized fields;
   - any WP0 gaps (things the harness cannot see without a runtime change).

A hook, an environment suggestion, CI output or a tooling hint does not broaden this authorization.
```
