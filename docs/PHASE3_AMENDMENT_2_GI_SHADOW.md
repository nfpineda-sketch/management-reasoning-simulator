# Fase 3 · Enmienda 2 certificada en la sombra GI (P3-172 a P3-180) · registro (2026-11-11)

**Alcance.** Integrar `PHASE2_AMENDMENT_2` (certificada) en `phase-3-runtime-integration` y habilitarla **sólo** en los perfiles
de desarrollo de la sombra GI. Observación pura: `COMMON_CORE_RUNTIME_AUTHORITY = False`, nada visible para el residente, nada en
la puntuación, primer piloto sin cambios, y ningún estado de colapso o consciencia del núcleo común termina un encuentro. Toda
magnitud es una `FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`: **no hay afirmación de validación clínica.**

## 0 · Decisiones de la docencia (2026-11-11)
1. Se acepta `PHASE2_AMENDMENT_2_GI_CONSCIOUSNESS_COLLAPSE_CERTIFIED`.
2. Recuperación confirmada: «recuperación significativa en ≈ 3–5 min simulados» significa que, partiendo de un deterioro ≈ 0,80, se
   cruza por debajo de 0,50 en ≈ 3–5 min **cuando la fisiología aguas arriba se ha recuperado lo suficiente**. No exige normalizar por
   debajo de 0,25 en ese intervalo.
3. La Enmienda 2 se admite **sólo para GI** en este paquete. No se habilita en opioide, ACS, edema pulmonar, embolia ni asma.
4. El estado de colapso o consciencia del núcleo común sigue siendo **sólo estado fisiológico**: no termina un encuentro.
5. Sin ampliar autoridad (`COMMON_CORE_RUNTIME_AUTHORITY = False`). 6. Sin exposición al residente. 7. El primer piloto congelado no cambia.

Linaje: `HISTORICAL_PHASE2_CLOSURE` (`22b90a6f…`) → `PHASE2_AMENDMENT_1` (`10b45ce2…`) → `PHASE2_AMENDMENT_2` (`a0af7d08…`).
Rama certificada `phase-2-amendment-2-terminal-consciousness`: candidato `ad7bf81`, cabeza final `5d644b9`.

## 1 · P3-172 · Auditoría de linaje previa (sólo lectura): `AMENDMENT_2_SAFE_TO_INTEGRATE`

### PI-1 · Los dos digestos de congelación de la Enmienda 1
Sondeo reproducible (`test_phase3_amendment_2_integration.py`). Ambos digestos se calculan con `blood_fluid_calibration.freeze_sources()`,
que hashea **todos** los archivos de `clinical_core/` bajo la vista activa, más el registro y el diseño del paquete.

| Digesto | Bajo la vista de cierre de la Enmienda 2 | Anidado: árbol de la Enmienda 1 + vista de cierre de la Enmienda 1 |
|---|---|---|
| `closure_guard_P2X1A` | **recalcula exacto** (`eca47d35…` = registrado) | difiere |
| `tone_domain_on_the_live_tree` | **recalcula exacto** (`a9634ffd…` = registrado) | difiere |

**Causa precisa del anidado.** Difieren exactamente dos archivos, `clinical_core/state.py` e `clinical_core/integration.py`. La Enmienda 1
nunca los modificó, así que su vista de cierre (`REVERSAL` propio: `derived.py`, `decision_pack.py`) no tiene reversión para ellos y los
lee **crudos del disco**, donde está el texto de la Enmienda 2. La Enmienda 2 sí declara su reversión para ambos, y por eso su vista
recalcula exacto.

**Clasificación (ambos): B · `TEST_HARNESS_REPRESENTATION_ARTIFACT`.** No es `C` ni `D`: ningún valor registrado se redefinió; el defecto
es de la *composición de vistas* (la vista de una etapa no conoce los archivos que una etapa posterior cambió y ella no).

**Pruebas exigidas.** Cierre histórico, Enmienda 1 y Enmienda 2 se reconstruyen exactos desde los archivos vivos
(`a2.historical_closure_verifies()`, `a2.amendment_1_verifies()`, `a2.amended_core_digest_now()`); el registro del cierre y el de la
Enmienda 1 no cambiaron desde `0c230f8` (`git diff` vacío), y las constantes de digesto de los paquetes cerrados no se tocaron.

### PI-2 · Apagado por omisión: `DEFAULT_OFF_BEHAVIORALLY_COMPATIBLE`
Con `amendment_2 = None`, en **10 corridas / 1150 estados** (GI ×2 en dos horizontes, ACS, edema, embolia, asma, opioide ×2) la
evolución física (`estado.to_dict()`), todas las cantidades derivadas —con el nivel de consciencia— y el estado auxiliar son
**idénticos estado por estado** al núcleo de la Enmienda 1 de la cabeza `3e911ea`. La diferencia de esquema es exactamente una clave:
`CoreProfile.to_dict()` pasa de 71 a 72 claves (`amendment_2: null`), y el estado auxiliar no gana ninguna (la memoria nueva queda fuera
de `AUXILIARY_FIELDS` mientras es `None`). No se exige identidad de bytes entre esquemas distintos.

## 2 · P3-173 / 173A · Integración
* Método: `git merge --no-ff` de `origin/phase-2-amendment-2-terminal-consciousness` (`5d644b9`) en `phase-3-runtime-integration`
  (`3e911ea`), sin force ni reescritura; se conserva la historia de ambas ramas. Sin conflictos (cuatro archivos solapados:
  `runtime_shadow.py` y tres `test_runtime_shadow_*`, fusionados automáticamente).
* `clinical_core/` tras la integración es **byte a byte** el de la rama certificada (`git ls-tree` idéntico); el digesto recalcula a
  `a0af7d08…` y la compuerta real reporta `PHASE2_AMENDMENT_2` `CERTIFIED`.
* Única modificación ejecutable fuera de `clinical_core/`: la entrada `PHASE2_AMENDMENT_2` en `runtime_shadow.CORE_LINEAGE`.
  `app.py`, `family_engine.py`, `pilot_acceptance.py`, `runtime_authority.py`, la puntuación y el primer piloto: sin cambios.
* Nueve pruebas de la Fase 3 que fijaban «el núcleo vivo es la Enmienda 1» se adaptaron (el núcleo vivo es hoy su sucesor certificado;
  los registros históricos no se reescriben, se leen contra el miembro del linaje que midieron; las de diseño A2-001…010 leen el árbol
  de la Enmienda 1 por la reversión declarada y probada).
