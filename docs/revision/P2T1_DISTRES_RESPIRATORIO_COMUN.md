# P2T-1 · Arquitectura común mínima del distrés respiratorio

Paquete estructural común, en sombra e inerte por defecto. No migra el asma ni calibra nada. Rama
`phase-2-clinical-core-shadow`; base `ce78b5d` (P2S-2 aceptado; P2S-3 cerrado como NOT_READY — COMMON_CORE_BLOCKER_FOUND;
P2T-0X aceptado).

- Núcleo: `clinical_core/derived.py`, `state.py`, `integration.py` y `provenance.py`, más las dos tuplas de registro.
- Análisis: `clinical_core/respiratory_distress.py`, congelado antes de la única evaluación.
- Registro: `docs/revision/P2T1_respiratory_distress.json`. Este documento se genera desde el registro
  (`clinical_core/respiratory_distress_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- P2T-0X aceptado: **B**, `SEPARATE_RESPIRATORY_DISTRESS_AND_GENERAL_AROUSAL_SIGNALS_SUPPORTED`;
  `RR_GAP_RESPIRATORY_DISTRESS_DOMINANT`; `HR_GAP_MULTIFACTORIAL`.
- Sólo se implementa `respiratory_distress`. El estrés sistémico o activación general (dolor, contrarregulación de la
  hipoglucemia, estrés coronario, fiebre, agitación o ansiedad) queda `SYSTEMIC_STRESS_DEFERRED`.
- El distrés es activación aferente respiratoria no química: el desajuste entre la demanda respiratoria y la capacidad del
  sistema para cubrirla, más el estrés aferente pulmonar que la química de los gases no recoge. No es SpO2, PaCO2, pH,
  FR, el WOB observable, la eficiencia mecánica, G, L, el déficit de oxígeno, D, el shock, el dolor, la ansiedad general,
  el estrés sistémico ni la depresión central.
- Es una entrada auxiliar común, no un canal canónico nuevo.
- Es HÍBRIDO: un valor latente de llegada por caso o familia, más cambios escritos por las familias. Nunca se deriva
  entero de la mecánica (nunca `1 − E`).
- El WOB autoral es evidencia para ordenar, nunca una tabla numérica universal.
- La ranura mecánica → distrés existe sólo como posibilidad futura: magnitud UNSET, apagada, sin término activo.
- Dos lectores con ganancias propias, ambas UNSET:
  - el respiratorio entra antes de la saturación, junto al ácido y al hipoxémico; la disponibilidad central sigue siendo
    la compuerta de la expresión;
  - el simpático entra en el objetivo simpático, con la saturación y el β-bloqueo existentes.
- El impulso hipoxémico sigue UNSET y sin cambios. No se añade ninguna compuerta de la depresión central sobre la FC.

## 2. Auditoría de los puntos de inserción (P2T-1-1)

<!-- generado:auditoria -->
- **arrival_drive:** derived.arrival_drive_composition: the anchors' arrival distress
- **arrival_state:** derived.arrival_state: aux.respiratory_distress from the anchors, before the arrival sympathetic target is read
- **declared_unwired:** sympathetic_target's docstring: hypercapnia, pain or agitation, fever, withdrawal (no state); hypoxaemia and hypoglycaemia relative to arrival (unchanged)
- **integration:** integration.step: Contribution.distress collected, summed by _distress_after, recorded in MinuteRecord.distress, conserved by _check_conservation
- **respiratory_drive:** derived._composition: excitatory = acid (+ hypoxaemic) (+ gain x distress), then rate_from_drive (saturation), then x central_drive_availability (expressed_respiratory_rate)
- **state_drive:** derived.respiratory_drive_composition: the state's aux.respiratory_distress
- **sympathetic:** derived.sympathetic_target: after the acute-deficit, pressure, debt, hypoxaemia and hypoglycaemia terms, before the baroreflex and max(0, .); beta-blockade downstream in sympathetic_increment
- Lectores del distrés en `derived.py`: `respiratory_drive_composition`, `sympathetic_target`; del distrés de llegada: `arrival_drive_composition`, `arrival_state`.
- Lectores de las ganancias: respiratoria `__post_init__`, `_composition`, `respiratory_distress_read`; simpática `__post_init__`, `respiratory_distress_read`, `sympathetic_target`.
- Argumentos de distrés de la composición: `anchors.arrival_respiratory_distress`, `state.aux.respiratory_distress` (nunca la SpO2 ni la mecánica).
- El objetivo simpático lee de nuevo sólo `distress_to_sympathetic_gain`, `respiratory_distress`; el incremento lee el β-bloqueo: sí.
- La integración lee para el distrés sólo `amount`, `respiratory_distress` y suma: `respiratory_distress=_distress_after(state, distress, profile, minute)`.
- Pasa: sí.
<!-- /generado:auditoria -->

## 3. Representación y escritor (P2T-1-2, P2T-1-3)

El distrés no tiene una referencia mayor que 0 que escalar (0 es «ninguno»), así que los cambios son aditivos, con la
convención de un delta de canal y no la del factor de la mecánica. Un minuto que lo llevaría por debajo de 0 se rechaza;
no se recorta. No hay techo: no se eligió ningún límite clínico.

<!-- generado:representacion -->
- Campos añadidos: `Anchors`: `arrival_respiratory_distress`; `AuxiliaryState`: `respiratory_distress`; `Contribution`: `distress`; `CoreProfile`: `distress_to_respiratory_drive_gain`, `distress_to_sympathetic_gain`; `MinuteRecord`: `distress`.
- Rechazos: amount_boolean sí, amount_nan sí, arrival_without_reader sí, change_below_zero sí, change_without_reader sí, gain_boolean sí, gain_negative sí, gain_zero sí, infinite_arrival sí, nan_state sí, negative_arrival sí, negative_state sí, respiratory_gain_without_acid_base sí.
- Aditivo y persistente (dos escritores sintéticos, +1 en los minutos 1–3 y +0,5 en los minutos 1–2): 0,0, 1,5, 3,0, 4,0, 4,0, 4,0, 4,0; cambios registrados por minuto [2, 2, 1, 0, 0, 0]; fuente del cambio auxiliar `core_coupling:respiratory_distress`.
- El perfil por defecto declara algún lector: no. Escritores de familia en `clinical_core/modules`: ninguno.
- Pasa: sí.
<!-- /generado:representacion -->

## 4. Sondas D1–D12 (P2T-1-5)

Ganancias, distrés y estados SYNTHETIC_ONLY, predeclarados (respiratoria 1, simpática 0,05; segundo par 2 / 0,01; rejilla
de distrés 0 / 2,5 / 5 / 10). Ninguno se ajustó a un caso.

<!-- generado:sondas -->
| Sonda | Qué exige | Resultado | Pasa |
|---|---|---|---|
| D1 | distress 0: the readers declared change no RR and no HR | cursos de referencia releídos con los lectores declarados: acs sí, gi_57m sí, p2p2_hypoxaemic sí, pulmonary_edema sí, pulmonary_embolism sí; curso del SCA re-ejecutado: sí | sí |
| D2 | distress > 0 with the respiratory reader: the excitatory drive (and RR) increases; HR unchanged | distrés 0,0, 2,5, 5,0, 10,0: impulso excitador 0,00, 2,50, 5,00, 10,00; FR 16,0, 18,4, 20,5, 24,2; FC 80,0, 80,0, 80,0, 80,0 | sí |
| D3 | distress > 0 with the sympathetic reader: the sympathetic target (and HR) increases; RR unchanged | objetivo simpático 0,000, 0,125, 0,250, 0,500; FC 80,0, 83,1, 86,2, 92,4; FR 16,0, 16,0, 16,0, 16,0 | sí |
| D4 | same distress, different gains: the effectors respond independently | A (g_R 1.0, g_S 0.05): ΔFR 4,53, ΔFC 6,24; B (g_R 2.0, g_S 0.01): ΔFR 8,24, ΔFC 1,25; hr_only (g_R None, g_S 0.05): ΔFR 0,00, ΔFC 6,24; rr_only (g_R 1.0, g_S None): ΔFR 4,53, ΔFC 0,00 | sí |
| D5 | distress > 0 with the central drive availability reduced: RR expression suppressed, the distress present | disponibilidad 1,0, 0,5, 0,0: FR 20,5, 10,3, 0,0; distrés 5,0, 5,0, 5,0; término de distrés 5,0, 5,0, 5,0 | sí |
| D6 | central depression does not suppress the sympathetic reader (no gate added) | disponibilidad 1,0, 0,5, 0,0: FC 86,2, 86,2, 86,2 (sin distrés 80,0) | sí |
| D7 | distress 0 with severe hypoxaemia: no distress contribution from SpO2 | SpO2 80 → 79,5; distrés siempre 0: sí; cambios registrados 0; misma FR y FC: sí | sí |
| D8 | distress 0 with low mechanics efficiency: no distress contribution from the mechanics | E 0,250 → 0,204; PaCO2 160,0 → 195,8; distrés siempre 0: sí; misma FR y FC: sí | sí |
| D9 | a distress change alone moves only its readers' effectors (RR -> W, PaCO2, pH; HR) | both: se mueven `W`, `distress`, `distress_drive`, `excitatory_drive`, `excitatory_rr`, `hr`, `paco2`, `ph`, `rr`, `sympathetic_drive`, `sympathetic_target`; W sigue sólo a la FR sí; respiratory_reader: se mueven `W`, `distress`, `distress_drive`, `excitatory_drive`, `excitatory_rr`, `paco2`, `ph`, `rr`; W sigue sólo a la FR sí; sympathetic_reader: se mueven `distress`, `hr`, `sympathetic_drive`, `sympathetic_target`; W sigue sólo a la FR sí | sí |
| D10 | acid and distress drives compose before the existing saturation | impulso ácido 12,0 + distrés 5,0 = 17,0; FR 28,33 (si se sumara después de la saturación, 30,06; techo 41) | sí |
| D11 | the hypoxaemic and distress drives remain independently addressable | hypoxaemic_on_distress_on: hipoxémico 3,60, distrés 5,00; hypoxaemic_on_distress_unset: hipoxémico 3,60, distrés 0,00; hypoxaemic_unset_distress_on: hipoxémico 0,00, distrés 5,00; hypoxaemic_unset_distress_unset: hipoxémico 0,00, distrés 0,00; mapeo hipoxémico UNSET en los perfiles comprometidos: sí | sí |
| D12 | with both readers UNSET every prior candidate reading is exact (the P2S-3 core) | lectura exacta del núcleo de P2S-3: acs sí, asthma_49m sí, gi_57m sí, p2p2_hypoxaemic sí, p2s2_mechanics sí, pulmonary_edema sí, pulmonary_embolism sí; distrés 0 en todos: sí | sí |
<!-- /generado:sondas -->

## 5. Contrastes de casos (P2T-1-6)

Distrés sintético (5) y ganancias sintéticas sobre los mapeos de llegada ya comprometidos. Muestran qué puede
representar la arquitectura; no son valores clínicos.

<!-- generado:contrastes -->
- **Edema 58m** (mapeo de llegada comprometido, distrés 0 → sintético): FR 18,3 → 22,4, FC 80,0 → 86,2, PaCO2 49,0 → 40,0.
- **TEP 61m:** FR 25,5 → 28,3, FC 95,6 → 101,7, PaCO2 28,0 → 25,2; términos del shock (déficit agudo, deuda) sin cambio: sí; el objetivo sube exactamente g_S × distrés: sí.
- **TEP 33f:** FR 21,2 → 24,8, FC 81,9 → 88,1, PaCO2 30,0 → 25,6.
- **Asma 49m** (mecánica de llegada FAMILY_CANDIDATE de P2S-3): FR 16,0 → 20,5, FC 80,0 → 86,2, PaCO2 95,6 → 74,5; la mecánica no cambia: sí.
- **Contraste del opioide** (sondas sintéticas: SpO2 80, disponibilidad 0,3, distrés 0): FR 4,8 y FC 80,0 con los lectores declarados, 4,8 y 80,0 sin ellos: ni taquicardia ni taquipnea forzadas sí.
- **SCA 70f:** FC autoral 112, núcleo 91,8, residual 20,2 sin cambio con distrés 0 (SYSTEMIC_STRESS_DEFERRED).
- **hypoglycaemia_like** (estado sintético, distrés 0): FC autoral 112, núcleo 80,0, residual 32,0, sin cambio sí.
- **pain_like** (estado sintético, distrés 0): FC autoral 94, núcleo 80,0, residual 14,0, sin cambio sí.
- SYNTHETIC distress and gains on the committed arrival mappings; no value is calibrated or approved. Pasa: sí.
<!-- /generado:contrastes -->

## 6. β-bloqueo (P2T-1-7)

<!-- generado:beta -->
- β 0.0: ΔFC 6,24 (por `sympathetic_increment` sí); β 0.5: ΔFC 3,12 (por `sympathetic_increment` sí); β 1.0: ΔFC 0,00 (por `sympathetic_increment` sí).
- Pasa: sí.
<!-- /generado:beta -->

## 7. Ordenamiento por el WOB autoral (P2T-1-8)

Sólo orden. Las regiones candidatas no tienen escala clínica: cualquier reetiquetado estrictamente creciente da el mismo
resultado. No se usa la FR ni la FC.

<!-- generado:ordenamiento -->
| Caso | WOB autoral | Etiqueta ordinal | Rango |
|---|---|---|---|
| `pneumonia_46f` | Increased | Increased | 1 |
| `pneumonia_83m` | Increased | Increased | 1 |
| `pulmonary_embolism_33f` | Increased | Increased | 1 |
| `asthma_24f` | Markedly increased | Marked | 2 |
| `pulmonary_edema_75f` | Markedly increased | Marked | 2 |
| `pulmonary_embolism_61m` | Markedly increased | Marked | 2 |
| `asthma_49m` | Severe | Severe | 3 |
| `pulmonary_edema_58m` | Severe | Severe | 3 |

- Regiones candidatas (FAMILY_CANDIDATE / SYNTHETIC_ONLY, sólo cuenta su orden): Increased [0.0, 1.0]; Marked [1.0, 2.0]; Normal [0.0, 0.0]; Severe [2.0, None]; estrictamente ordenadas: sí.
- Orden no vacío: sí; pares que el WOB ordena: 21; empates (el WOB no los ordena): asthma_24f, pulmonary_edema_75f, pulmonary_embolism_61m; asthma_49m, pulmonary_edema_58m; pneumonia_46f, pneumonia_83m, pulmonary_embolism_33f.
- Los lectores preservan el orden: sí. Ajustado a la FR o la FC: no. Estado: ORDINAL_EVIDENCE_ONLY; WOB_NUMERIC_MAPPING_UNSET.
<!-- /generado:ordenamiento -->

## 8. Ortogonalidad mecánica / distrés (P2T-1-9)

La mecánica es la eficacia ventilatoria; el distrés, la activación aferente no química. Con el mismo distrés y distinta
mecánica, el impulso y la FR son los mismos y cambian W y la PaCO2. Con la misma mecánica y distinto distrés, cambian la FR
y la FC.

<!-- generado:ortogonalidad -->
- Misma mecánica, distinto distrés: distrés 0.0: FR 16,0, FC 80,0, W 0,418, PaCO2 95,6; distrés 5.0: FR 20,5, FC 86,2, W 0,537, PaCO2 74,5.
- Mismo distrés, distinta mecánica: E 0,314: término de distrés 5,0, FR 20,5, FC 86,2, W 0,403, PaCO2 99,4; E 0,523: término de distrés 5,0, FR 20,5, FC 86,2, W 0,671, PaCO2 59,6.
- Pasa: sí.
<!-- /generado:ortogonalidad -->

## 9. Observable, parámetros y estrés sistémico (P2T-1-10, P2T-1-11, P2T-1-4)

<!-- generado:parametros -->
- **approved:** none
- **arrival_distress_regions:** UNSET; FAMILY_CANDIDATE ordinal regions only in the WOB ordering test
- **beta_agonist_hr_effect:** UNSET (deferred)
- **distress_to_respiratory_drive_gain:** UNSET (None); SYNTHETIC_ONLY in probes
- **distress_to_sympathetic_gain:** UNSET (None); SYNTHETIC_ONLY in probes
- **fever_effect:** UNSET (deferred)
- **hypoglycaemia_absolute_mapping:** UNSET (the arrival-relative term unchanged)
- **hypoxaemic_gain_and_mapping:** UNSET (unchanged)
- **mechanics_to_distress_coupling:** UNSET, off (no structural term is active)
- **pain_effect:** UNSET (deferred)
- **systemic_stress_writers_and_gains:** SYSTEMIC_STRESS_DEFERRED
- **wob_to_distress_mapping:** UNSET (no numeric mapping)
- Lectores UNSET en los perfiles comprometidos: acs sí, asthma sí, default sí, edema sí, gi sí, p2p2_probe sí, p2s2_probe sí, pe sí.
- Distrés de llegada 0 en los mapeos comprometidos: sí.
- Observable: WOB_OBSERVABLE_MAPPING_DEFERRED; el núcleo lee el WOB: no.
- Estrés sistémico: SYSTEMIC_STRESS_DEFERRED; identificadores nuevos `distress_to_respiratory_drive_gain`, `distress_to_sympathetic_gain`, `respiratory_distress`, `arrival_respiratory_distress`, `respiratory_distress`; filtrados ninguno.
- Pasa: sí.
<!-- /generado:parametros -->

## 10. No regresión por defecto (P2T-1-12)

<!-- generado:no_regresion -->
- Registro de P2S-2 reproducido en vivo (a través de las vistas cerradas, que anidan P2Q-2, P2P-2, P2P-1, SCA y GI): sí.
- Registro de P2S-3 reproducido en vivo: sí; archivo intacto: sí; su veredicto congelado sigue siendo `ASTHMA_SHADOW_MIGRATION_READY`.
- Clasificación vigente de P2S-3: ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_CORE_BLOCKER_FOUND (COMMON_DRIVE_GAP); P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 11. Prueba contra el árbol de P2S-3

Los archivos `.py` de `clinical_core` que cambian son los cuatro del núcleo y las dos tuplas de registro; se reconstruyen
byte a byte como los dejó P2S-3. Todos los demás archivos `.py` de `clinical_core` existentes en `ce78b5d` están fijados por
hash. El golden cambia sólo por las dos entradas nuevas del registro de parámetros; lo cubren las pruebas del golden directo
y de Contracts v2.

<!-- generado:prueba -->
- Archivos con inserciones declaradas, probados contra P2S-3 (`ce78b5d`): `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí, `clinical_core/state.py` sí.
- Archivos comunes fijados por hash: 115, intactos sí.
- Vista de P2S-3: digest de congelación sí, su prueba contra P2S-2 sí, registro sí.
<!-- /generado:prueba -->

## 12. Preparación (P2T-1-13)

Regla predeclarada: READY si se cumplen todos los criterios; si no, NOT_READY con el primero que falla.

<!-- generado:veredicto -->
- sí — auxiliary distress exists (aux.respiratory_distress, its arrival value, its conservation and refusals)
- sí — it is distinct from mechanics, gases and shock (D7, D8, D9, orthogonality, the readers' audit)
- sí — a family writer interface exists (DistressChange; additive, persistent, recorded; no family writer yet)
- sí — the respiratory reader exists structurally (D2, D10)
- sí — the sympathetic reader exists structurally (D3)
- sí — the gains are separate and UNSET (D4; the parameter state)
- sí — the acid composition is structurally coherent (D10, D11)
- sí — the central availability still gates the RR, and not the HR (D5, D6)
- sí — beta-blockade remains downstream (the beta-blockade guard)
- sí — the default behaviour is exact (D1, D12, the closed records reproduced, the P2S-3 tree proven)
- sí — no systemic_stress implementation leaked in

**Veredicto: COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_READY**

Composición: STRUCTURAL_COMPOSITION_READY, CLINICAL_COMPOSITION_MAGNITUDE_UNSET.

**Recomendación: RETRY_ASTHMA_SHADOW_MIGRATION_AFTER_DISTRESS_ARCHITECTURE (a new package superseding P2S-3; not started here)**
<!-- /generado:veredicto -->

## 13. Lo que deja este paquete (para la docencia)

1. **Ahora existe el eslabón que bloqueó a P2S-3, pero vacío.** El núcleo ya puede representar un impulso excitador no
   químico común que sube la FR y la FC en familias respiratorias distintas (edema, TEP, asma) sin términos de enfermedad.
   Con las ganancias UNSET, nada cambia.
2. **Una señal, dos efectores, dos ganancias.** El mismo distrés mueve la FR y la FC con ganancias independientes (D4): no
   se impone ningún cociente FR / FC. P2T-0X mostró que ese cociente varía entre casos.
3. **La depresión central apaga la expresión respiratoria, no la señal ni la FC.** Con la disponibilidad en 0, la FR es 0,
   el distrés sigue presente y la FC no cambia (D5, D6). Si la depresión central debiera atenuar también la FC, eso sería
   una decisión aparte.
4. **El distrés no se fabrica.** Ni la hipoxemia grave ni una mecánica muy baja escriben distrés (D7, D8), y el distrés no
   mueve la SpO2, G, L, la mecánica, D, el lactato ni la hemodinámica (D9). En el opioide sintético, distrés 0 más
   depresión central no fuerzan taquicardia ni taquipnea.
5. **Mecánica y distrés no se confunden.** Mismo distrés con distinta mecánica: misma FR, distinta PaCO2. Misma mecánica
   con distinto distrés: distinta FR y FC (P2T-1-9).
6. **El WOB sólo ordena.** Las ocho llegadas de las cuatro familias respiratorias admiten un orden no vacío (Increased <
   Marked < Severe), con tres grupos empatados que el WOB no separa. Ningún valor queda aprobado.
7. **Una decisión antes de cualquier valor.** Con la mecánica apagada, un distrés de llegada desplaza la PaCO2 de llegada del ancla autoral (§15, hallazgo 1). Hay que elegir la semántica antes de remigrar el edema o el TEP con distrés.
8. **Lo que no se cierra, a propósito.** El residual de FC del SCA (+20) y los de la hipoglucemia y el dolor quedan para el
   estrés sistémico (SYSTEMIC_STRESS_DEFERRED).

## 14. Proceso

- Duración: inicio 23:39 UTC; congelación `d67cfba` a las 00:23; evaluación única a las 00:23 (15 s); revisión desde las
  00:24.
- Durante el desarrollo el análisis se ejecutó para depurar. Las correcciones fueron de construcción: declarar como
  `synthetic_probe` los parámetros de caso sintéticos, un ritmo coherente con la FC en los estados sustitutos, anidar las
  vistas de P2S-3 y P2S-2, y presentar a P2S-2 sus campos auxiliares. Ningún valor predeclarado cambió.
- Pruebas de Fase 2 antes de congelar, en 4 particiones: 1 789 pruebas. Fallaron 128 y hubo 90 errores por efecto dominó,
  esperables en un cambio del núcleo común (las guardas cerradas leen el árbol del núcleo). Se adaptaron con la vista de
  P2S-3 (`dm.chain`) y extendiendo, sin debilitarlas, seis listas fijas: aislamiento, lectores de W, tuplas de exclusión,
  lectores de T, capas de llegada y entradas de calibración. Además se regeneraron el golden (+2 entradas de registro) y
  los digests de cuatro documentos generados. Al reejecutar los 31 archivos afectados quedaron 14 fallos, todos de esas listas, del golden o de los digests; tras adaptarlos, las pruebas afectadas pasaron.
- Una sola evaluación, una sola revisión adversarial y una sola certificación final.

## 15. Revisión adversarial

Una revisión, independiente y de sólo lectura, sobre el candidato congelado y evaluado (00:24–00:35): ningún hallazgo
alto, 1 medio y 6 bajos. Cada uno se confirmó con una sonda. No se vuelve a congelar y el veredicto no cambia: ningún
criterio predeclarado falla y el comportamiento por defecto es exacto.

1. **Medio: con la mecánica apagada (ruta P2K-2), un distrés de llegada mueve la PaCO2 de llegada lejos de la autoral.**
   - El ancla de PaCO2 de P2K-2 lee la FR de llegada sólo del ácido. La FR de `respiration` ya incluye el distrés.
   - Sonda (edema 58m, ganancia respiratoria sintética 1): con distrés 0 / 5 / 20, la FR es 18,3 / 22,4 / 30,8 y la PaCO2
     49 / 40 / 29,1, con pH 7,29 / 7,38 / 7,52. La acidosis respiratoria autoral se vuelve alcalosis.
   - Es la convención que P2P-2 declaró para el impulso hipoxémico («lo mueve del ancla, nunca lo absorbe»), extendida a un
     latente cuyo uso previsto es justamente la FR de llegada.
   - Con la mecánica encendida (P2S-2, la ruta de las familias respiratorias) la PaCO2 es 40 / W y nunca lee ese ancla.
   - **Decisión docente pendiente, antes de elegir cualquier valor:** rechazar un distrés de llegada mayor que 0 con el
     lector respiratorio y la mecánica apagada, o incluir el término de distrés de llegada en la ventilación del ancla.
     Ninguna de las dos se implementa aquí.
2. **Bajo: un escritor que deshace sus propios cambios puede quedar rechazado por redondeo** (0,3 − 0,1 − 0,2 da
   −2,8e−17 y se rechaza como «por debajo de 0»). Queda como deuda: falta decidir una tolerancia o exigir la suma en un
   solo cambio.
3. **Bajo: `state.initial_state()` acepta un distrés de llegada y lo descarta en silencio.** La misma brecha ya existía
   para la mecánica de P2S-2. `run()` rechaza un minuto 0 incoherente, pero un `step()` directo correría con 0. Queda como
   deuda.
4. **Bajo: los informes de procedencia no muestran el distrés.** `heart_rate_decomposition` reparte el incremento sólo
   entre el déficit agudo y la deuda (ya omitía el barorreflejo), y `respiratory_rate_decomposition` no tiene término de
   distrés. Queda como deuda.
5. **Bajo: algunas comprobaciones pasan por construcción.**
   - `through_increment` repite la fórmula de `derive`; la guarda real es el orden 0 > 0,5 > 1 del β-bloqueo.
   - Los «sin cambio» del opioide, el SCA y los residuales repiten D1.
   - D7 y D8 valen porque nada escribe distrés: son guardas de regresión, y la evidencia de «no se deriva de la SpO2 ni de
     la mecánica» la dan la auditoría AST y la prueba de reversión.
   - La revisión de estrés sistémico mira sólo los nombres nuevos; la prueba es la reversión.
   - Aceptado: el registro se lee con esta cautela.
6. **Bajo: las regiones candidatas del WOB son una tabla numérica común a todas las familias.** No se usan más que para
   ordenar y aceptan extremos que se tocan. Queda como deuda: bastaría el índice ordinal o regiones por familia, y ningún
   número está aprobado.
7. **Bajo: cobertura.** Con la vista nueva, las pruebas cerradas de P2S-2 ejercitan el filtro de P2T-1 y no ya la función
   cerrada de P2S-2 (su archivo es idéntico byte a byte). Además, la prueba de bloqueo por criterio cubre 4 de los 11
   criterios. Queda como deuda.

Verificado sin hallazgos:

- la exactitud por defecto (todas las ramas nuevas tras `is not None`, el mismo orden en coma flotante, sin cambios
  auxiliares nuevos en un minuto por defecto);
- la reversión, que da exactamente `ce78b5d`; el golden sólo con las 2 entradas de registro;
- el digest congelado; el registro de P2S-3 idéntico y aún READY;
- las vistas en cadena, que fallan ante un archivo no probado y nunca pasan en vacío;
- las 23 pruebas cerradas con la vista nueva y las claves quitadas sólo en su referencia;
- la suma antes de la saturación, sin doble conteo del ácido;
- la disponibilidad sólo sobre la FR;
- el lector simpático antes del barorreflejo y de `max(0, ·)`, con β-bloqueo;
- los rechazos y la rama sin pulso;
- sin escritores de familia ni lectores del WOB o la SpO2.

## 16. Limitaciones

- Ningún valor está aprobado: las dos ganancias, las regiones de llegada y el mapeo WOB → distrés siguen UNSET. Lo de
  este paquete es SYNTHETIC_ONLY o FAMILY_CANDIDATE.
- La composición está lista sólo estructuralmente: `CLINICAL_COMPOSITION_MAGNITUDE_UNSET`. No se probó ninguna magnitud
  aditiva junto al ácido (la tensión de la anafilaxia de P2T-0X sigue abierta).
- Ninguna familia escribe distrés todavía. El asma no se volvió a migrar: P2S-3 sigue NOT_READY y su registro congelado
  sigue diciendo READY (P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT).
- Las brechas de FC del SCA, la hipoglucemia y el dolor quedan intencionalmente sin resolver (SYSTEMIC_STRESS_DEFERRED).
- El WOB observable no se genera desde el estado (WOB_OBSERVABLE_MAPPING_DEFERRED).
