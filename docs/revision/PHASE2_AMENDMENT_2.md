# Enmienda 2 · GI: consciencia sistémica reversible y colapso circulatorio · registro (2026-11-10)

**Estado: `CERTIFICADA (2026-11-11)`.** Sucesor formal de `PHASE2_AMENDMENT_1`, sólo en sombra: apagado por omisión
(`CoreProfile.amendment_2 = None`), sin autoridad en tiempo de ejecución, invisible para el residente y ausente de la
puntuación. **No hay afirmación de validación clínica:** toda magnitud es una `FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`
(testigos `LOW`, `CENTER_REFERENCE`, `HIGH`), nunca una calibración.

Digesto del núcleo enmendado: `a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2` (144 fuentes). Predecesores, reconstruidos exactos desde los archivos vivos:
Enmienda 1 `10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635` y cierre de la Fase 2
`22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a`. Registro ligado: `PHASE2_AMENDMENT_2.json`.

## 1 · Decisiones de la docencia que implementa (A2-FD-011 a A2-FD-022)
| Decisión | Implementación |
|---|---|
| Segundo estado acumulado `F` (carga de encefalopatía sistémica reversible), distinto de `D` y `N` | `aux.systemic_encephalopathy_burden`; relajación de primer orden P2L-2 (`τ_subida < τ_bajada`) hacia la señal |
| Aporte **relativo a la llegada** (sin DO2 sano inferido) | `aporte_relativo = aporte_efectivo_actual / aporte_efectivo_de_llegada` (=1 a la llegada); denominador ≤ 0 → el motor se niega |
| Temporalidad: 1 min de señal extrema → `F` < 0,50; 2–4 min → `F` ≥ 0,80; la recuperación cruza una categoría en ≈ 3–5 min | constantes de subida y bajada separadas, dentro de la región `FACULTY_DEFINED` |
| Deterioro observable = máx(`N` primario con piso del nivel de llegada, `F`, aporte del colapso); la señal instantánea **no** entra | `readout`; cortes <0,25 ninguno / 0,25–0,50 SOMNOLIENTO / 0,50–0,80 OBNUBILADO / ≥0,80 SIN RESPUESTA; sin GCS |
| Quitar la escalera directa PAS/SpO2 del comportamiento activo | `derive` usa la compuesta cuando el perfil declara la enmienda; la reconstrucción histórica sigue reproduciendo la escalera exactamente |
| Colapso blando tipo Y: `min(fallo de perfusión, fallo de aporte)`, nunca máximo | `collapse_signal`; perfusión relativa a la llegada (sin mmHg absolutos); reutiliza `aux.collapse_burden` (sin tercera memoria) |
| Sin pulso sigue siendo un camino DURO inmediato, aparte | `collapse_state`: sin pulso → `ESTABLISHED` por `NO_PULSE`; la carga blanda no se mueve sin pulso |
| GI primero; mecanismos específicos de opioides diferidos | ningún identificador de opioide, saturación, naloxona ni GCS en el código nuevo (prueba AST) |

## 2 · Regiones de desarrollo (no calibraciones)
`| Magnitud | Región | Origen | LOW | CENTER | HIGH |
|---|---|---|---|---|---|
| `delivery_normal` | 0.7 – 0.8 | FACULTY_DEFINED_FROM_BEHAVIOR | 0.7 | 0.75 | 0.8 |
| `delivery_severe` | 0.45 – 0.55 | FACULTY_DEFINED_FROM_BEHAVIOR | 0.45 | 0.5 | 0.55 |
| `burden_rise_tau` | 1.443 – 2.485 | DERIVED_FROM_EXISTING_EQUATION | 1.5 | 1.65 | 1.85 |
| `burden_clear_tau` | 6.38 – 10.64 | DERIVED_FROM_EXISTING_EQUATION | 6.4 | 8.5 | 10.5 |
| `perfusion_normal` | 0.5 – 0.6 | FACULTY_DEFINED_FROM_BEHAVIOR | 0.5 | 0.55 | 0.6 |
| `perfusion_severe` | 0.3 – 0.4 | FACULTY_DEFINED_FROM_BEHAVIOR | 0.3 | 0.35 | 0.4 |
| `collapse_rise_tau` | 1.5 – 2.2 | WEAKLY_IDENTIFIED | 1.5 | 2.0 | 2.2 |
| `collapse_clear_tau` | 6.0 – 8.0 | WEAKLY_IDENTIFIED | 6.0 | 8.0 | 8.0 |
| `impending_burden` | 0.35 – 0.39 | WEAKLY_IDENTIFIED | 0.35 | 0.39 | 0.38 |
| `established_burden` | 0.55 – 0.7 | WEAKLY_IDENTIFIED | 0.55 | 0.65 | 0.7 |`

## 3 · Qué cambia en el núcleo y qué no
* Cuatro archivos comunes reciben inserciones **declaradas** (`derived.py`, `state.py`, `integration.py`, `decision_pack.py`);
  `clinical_core/amendment_2.py` guarda la reversión y las SHA de la Enmienda 1 (`CORE_AT_AMENDMENT_1`), de modo que el árbol de
  la Enmienda 1 y el del cierre se reconstruyen exactos y cada digesto recalcula a su valor certificado.
* Archivo propio nuevo: `clinical_core/systemic_consciousness.py` (la fisiología). Entra en el digesto del pack de decisión
  (es una dependencia de `integration.py`); `amendment_2.py` queda excluido, como `amendment_1.py`.
* Apagado por omisión: campo de perfil `amendment_2=None`; campo auxiliar `systemic_encephalopathy_burden=None`, fuera de
  `AUXILIARY_FIELDS` y de `to_dict` mientras es `None`: todo estado, digesto y dorado comprometido queda idéntico.
* La compuerta de linaje del runtime (`runtime_shadow_evidence.core_lineage_verdict`) lee `CORE_LINEAGE` (fuera de `clinical_core/`):
  la entrada `PHASE2_AMENDMENT_2` es `CANDIDATE` hasta que su registro diga `CERTIFIED` con la evidencia.

## 4 · Pruebas propias (esta enmienda)
`test_phase2_amendment_2_physiology.py` (cinéticas por testigo, aporte relativo, compuesta, colapso Y, controles negativos:
gasto bajo solo / aporte solo / perfusión sola / episodio breve, histéresis, sin pulso, validación, apagado por omisión),
`test_phase2_amendment_2_gi_matrix.py` (ambos casos GI × 3 testigos, orden causal y recuperación, sin ajuste por caso),
`test_phase2_amendment_2_families.py` (no interferencia en ocho cursos de seis familias: idénticos salvo el nivel),
`test_phase2_amendment_2_mutants.py` + `test_amendment_2_mutants_plugin.py` (10 mutantes, todos detectados),
`test_phase2_amendment_2_lineage.py` (compuerta de linaje y cierre histórico). Las pruebas de la Enmienda 1 que leen su propio
árbol usan `amendment_2.amendment_1_tree`; las de los paquetes cerrados, `amendment_2.chain/tree`.

## 5 · Limitaciones declaradas
1. **Opioides no resueltos** (diferidos por la docencia): la compuesta sólo lee aporte, perfusión y `N`; no hay mecanismo de
   consciencia por depresión respiratoria ni escalera de SpO2.
2. **Sólo GI es un uso soportado.** Declarada en edema pulmonar o embolia, la compuesta lee más bajo (esos cursos tienen hoy el
   nivel por la escalera directa de SpO2, que la docencia retiró); ningún perfil comprometido la declara fuera de GI.
3. El colapso blando **no** mueve el ritmo ni termina el encuentro (eso decide el runtime); el límite existente
   `UnresolvedBoundary` (gasto cero con pulso y sin regla terminal) no se modificó.
4. La semántica de la ranura `aux.collapse_burden` cambia (parte adimensional de la señal combinada) **sólo** cuando el perfil
   declara la enmienda; la regla heredada del núcleo (`collapse_burden_limit` None) sigue apagada.
5. `F` no se registra como `AuxiliaryChange` (la cantidad no está en `AUXILIARY_FIELDS`, a propósito, para no mover los
   artefactos comprometidos).
6. Se interpretó «la recuperación cruza una categoría en ≈ 3–5 min» como 0,80 → < 0,50 en 3–5 min; el piso del nivel de llegada
   se pliega a la contribución primaria; el colapso ESTABLECIDO aporta 1,0 y el inminente 0.
7. Dos digestos de congelación de la Enmienda 1 (`closure_guard_P2X1A`, `tone_domain`) ya no se recalculan sobre el árbol de la
   Enmienda 1 en `test_phase2_amendment_lineage.py` (sus valores registrados no cambian; los del cierre sí se recalculan).

## 5b · Certificación (2026-11-11)
Candidato `ad7bf815e57e63c892ad2be7a63c5a8302a3e688` (huella `0f3632bc7585…`, sin cambios al inicio ni al final), Python 3.11.17,
complemento `test_core_certification_preview` con `MRS_CORE_CERTIFICATION_PREVIEW=PHASE2_AMENDMENT_2` (la entrada de linaje fue
CANDIDATE durante toda la corrida; las pruebas marcadas `real_core_lineage` leen el estado real).

* Suite completa: particiones 0, 1 y 3 terminaron en la primera corrida (3721 + 2276 + 2873 pruebas, 0 fallas). La partición 2 llegó
  al límite de 7200 s al 89 % sin ninguna falla (pruebas lentas de reconstrucción de congelaciones, no un bloqueo); sus mismos 112
  archivos se corrieron hasta el final **sobre el mismo candidato sin cambios**, divididos en 4 sub-particiones paralelas
  (761 + 640 + 523 + 565 = 2489 aprobadas, 5 omitidas, 0 fallas). Total: 11 359 pruebas, 0 fallas, 0 errores, 93 omitidas, 1 xfail.
  El `resumen.json` del lanzador cuenta 8870 porque no incluye la partición 2 (terminó por tiempo); la cifra completa es la suma
  descrita aquí, no una cifra única del lanzador.
* Regresiones: 56/56 activas; 10 retiradas (conservadas, no corridas). Contratos raíz: 85 archivos, 0 fallas.
* Revisión adversarial independiente: 2 hallazgos altos y 3 medios confirmados y corregidos antes del candidato; los bajos, corregidos o
  declarados en la sección 5.
* Promoción: sólo metadatos y documentación; ningún archivo ejecutable cambió después del candidato.

## 6 · No reclamado
Sin autoridad en tiempo de ejecución; sin cambios visibles al residente; sin efecto en la puntuación; sin integración en la
Fase 3; sin terminación del encuentro desde el núcleo común; sin paro respiratorio; sin umbrales terminales absolutos de presión
ni umbrales directos de SpO2 para la consciencia; sin validación clínica.
