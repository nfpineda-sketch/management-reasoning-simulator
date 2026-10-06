# Decisiones metodológicas · vista compacta (ciclos 1–5)

Ciclo 5 del AI Advisor (59BP), 2026-09-28.

- **Qué es:** una vista para entender la metodología vigente en pocos minutos.
- **Qué no es:** no reemplaza el Decision File
  (`docs/COLA_DECISIONES_AI_ADVISOR.md`) ni el registro de correcciones
  (`corrections_registry.py`), donde está el detalle.

| Decisión | Fecha | Por qué | Estado | Implementada en | ¿Reversible? | ¿Requiere validación futura? |
|---|---|---|---|---|---|---|
| **Oportunidad ≠ desempeño.** Un encuentro puede ofrecer un objetivo; sólo el desempeño, leído por un docente, lo observa | 2026-09-27 (DF-1) | Que el caso no «otorgue» evidencia | Vigente | `observation_opportunities.py`, `progress_store.assess` | Sí, pero es la base del modelo | Sí: acuerdo entre docentes sobre qué oportunidades son reales |
| **Tres estados: yes / no / not_reviewed.** Not reviewed nunca se lee como no | 2026-09-27 (DF-1) | La falta de metadata no es una decisión clínica | Vigente | ídem | Sí | No |
| **Regla de transición** para lo no revisado; se retira caso por caso | 2026-09-28 (DF-12) | No perder oportunidades antes de la revisión clínica | **Transitoria**: C14 retirada en 30 casos; TD1/F1/C1/C3/C4 la conservan | `TRANSITION_OBJECTIVES` | Sí, por diseño | No |
| **C14 revisado caso por caso** (14 YES, 16 NO, 1 sin revisar) | 2026-09-28 (DF-13, A–H) | Primer objetivo con el flujo borrador → revisión clínica → metadata | Aplicado en el ciclo 5 | `case_assessment_bank.C14_DECLARATIONS` | Sí, con una nueva revisión | Sí: si las oportunidades declaradas ocurren de verdad |
| **La confirmación docente es obligatoria.** Nada se observa sin un docente; la IA propone, nunca registra | Diseño base (charter) | Validez de la evidencia | Vigente | `progress_store` (sólo staff), `rubric_store` (sólo lo confirmado cuenta) | No debería | Sí: acuerdo entre docentes |
| **Una observación por encuentro y objetivo.** Varios vínculos de marco son contribuciones de la misma unidad | 2026-09-27 (DF-2) | No contar dos veces | Vigente | índice único parcial `mrs_progress_current_observation`; `provenance.contributions` | Sí | No |
| **PARTIAL es una contribución válida**, no un defecto; dice qué queda fuera | 2026-09-27/28 (DF-2, DF-14) | Lo significativo y trazable antes que la cobertura máxima | Vigente; 9 PARTIAL inactivos | `competency_mapping.py` | Sí | Sí: si el componente observado es el que dice el vínculo |
| **Construct coverage ≠ competencia.** No se calcula cobertura del constructo ni se determina competencia o entrustment | Charter; reiterado 2026-09-28 | El simulador observa componentes, no EPAs completas | Vigente: no implementado a propósito | — | — | Sí, antes de cualquier afirmación |
| **Los eventos de seguridad van aparte del radar**: se cuentan, nunca se promedian | Rúbrica piloto, antes del ciclo 1 del AI Advisor | Un evento no es un nivel de dominio | Vigente | `rubric_progress`, reportes | Sí | Sí |
| **Penalidad −3 por evento crítico confirmado** | Vigente desde la rúbrica piloto | Marcar la seguridad en el total | **Retenida pendiente de validación** (DF-9) | `rubric_store` | Sí | **Sí** |
| **No evaluable ≠ cero.** Un dominio sin oportunidad no entra al promedio ni al total comparable | Rúbrica piloto, antes del ciclo 1 del AI Advisor | No leer falta de datos como mal desempeño | Vigente | rúbrica y perfil | No debería | No |
| **Autonomía no determinada** acumula observaciones y no cumple ninguna autonomía exigida | Decisión D10 | Honestidad del registro | Vigente | `progress_store` | Sí | No |
| **Base de evaluación congelada con cada encuentro.** Un cambio posterior no reinterpreta el pasado; la reevaluación es explícita y guarda las dos | 2026-09-25 | Reproducibilidad longitudinal | Vigente | `evaluation_basis.py` | No debería | No |
| **C2 deshabilitada** | 2026-09-27 (DF-4) | Banco de trauma insuficiente para una oportunidad real | Vigente | `objectives` (`supported: False`) | Sí | Se revisa con más trauma |
| **C15 deshabilitada** | 2026-09-27 (DF-5) | Sin acción | Vigente | ídem | Sí | — |
| **El validation corpus mide el motor, no a los médicos.** Anotación clínica ciega, 20 % doble, SEALED fuera del repositorio; la IA no es estándar de referencia | 2026-09-27/28 (DF-6, DF-15) | Validez externa de la lectura | Vigente; piloto listo, no enviado | `validation_corpus.py`, `validation/pilot_v1/` | — | Es la validación misma |
| **Baselines que nunca se reemplazan** (español `939978a`; inglés tras KD-01) | 2026-09-28 (ciclo 5) | Medir contra el motor que leyó | Vigente | `validation/baselines.json` | No | No |
| **El lector se corrige por clase, no por frase**, con frases nuevas y guardas | 2026-09-28 (ciclo 4, §57) | No sobreajustar al corpus | Vigente | pruebas por clase | — | El piloto dirá si generaliza |
| **Defectos conocidos etiquetados** KNOWN vs NEW | 2026-09-28 (ciclo 4, §73) | No esconder fallas | Vigente, versión 2 | `known_defects.json` | — | — |
| **Idioma del encuentro fijado al iniciar.** Textos del caso en español sólo tras aprobación docente | 2026-09-26/27 | Consistencia y revisión clínica de la traducción | Vigente | `document_language`, `case_text` | Sí | Sí: equivalencia entre idiomas no demostrada |
| **Una limitación nunca es una omisión** (Fase 0, guardas A–E). Una orden no leída, retenida, registrada sin modelo o ejecutada tarde por el simulador vuelve «reading» lo que habría sido «met»; nada después de un paro no modelado es evaluable; un evento con guion, una limitación del motor o un evento precedido por una orden que el simulador no ejecutó nunca apoya una retroalimentación negativa | 2026-10-06 (Fase 0) | Que el registro no atribuya al residente lo que decidió el simulador | Vigente; puntajes, rúbrica, D1–D5 y penalidades sin cambio | `rubric_screening` (`may_support_negative_feedback`), `pilot_freeze` | Sí | Sí: F0-5 a F0-7 del Decision File |
