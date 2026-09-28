# Matriz de oportunidades del banco · caso × objetivo

Ciclo 5 del AI Advisor · instrucción docente 59D · 2026-09-28. Actualizada en el ciclo 7: C14 revisado
en los 31 casos y C4 declarado NO en todos.

**Estado: BORRADOR. Generado por `generar_matriz.py`; no se edita a mano.**

- **Qué es.** Cobertura de oportunidades de observación que ofrece el banco de 31 casos, objetivo por
  objetivo. **No es cobertura del constructo de un residente** y no calcula competencia de nadie.
- **De dónde sale.** Las columnas TD1 a C3 son el borrador de `BORRADOR_TDFC.md` (tabla «Estados por
  caso»). C4 y C14 son lo que el banco declara (`case_assessment_bank.C4_DECLARATIONS` y
  `C14_DECLARATIONS`). Los Decision Challenges salen de `curriculum.CHALLENGES`: un desafío es TARGET
  en los casos de sus `families`.
- **DRAFT ≠ APPROVED OPPORTUNITY.** En el banco, toda celda DRAFT sigue hoy NOT REVIEWED y abierta por
  la regla de transición (TD1, F1, C1 y C3 son observables en todo encuentro). TDFC-1 a 6 y 8 están
  aprobadas conceptualmente (ciclo 7), sin escribir todavía en el banco.

## Leyenda

| Código | Valor | Qué significa aquí |
|---|---|---|
| TARGET | TARGET | La familia del caso está en las `families` del desafío: el encuentro generado para ese desafío puede usar este caso. |
| DECL+ | DECLARED YES | El caso declara la oportunidad, con revisión docente (hoy sólo C14). |
| DECL− | DECLARED NO | El caso declara que no la hay: no evaluable, nunca una falla. |
| NR | NOT REVIEWED | Nadie la declaró. En un desafío: no se ofrece fuera del encuentro generado para él. |
| DRAFT+ | DRAFT YES | Este borrador propone oportunidad. |
| DRAFT− | DRAFT NO | Este borrador propone que no la hay. |
| DRAFT? | DRAFT UNCERTAIN | Depende de una decisión clínica (TDFC-1 a TDFC-8). |

## Matriz

| Caso | Familia | R1-03 | R1-04 | R1-05 | R1-06 | R1-07 | R2-01 | R2-02 | R2-03 | R2-04 | R2-05 | R3-01 | TD1 | F1 | C1 | C3 | C4 | C14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `acs_54m_inferior` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT? | DRAFT− | DECL− | DECL− |
| `acs_66f_nonst` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT? | DRAFT− | DRAFT− | DRAFT− | DECL− | DECL− |
| `acs_61m_posterior` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT? | DRAFT− | DRAFT− | DRAFT− | DECL− | DECL+ |
| `acs_52m_de_winter` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT? | DRAFT− | DRAFT− | DRAFT− | DECL− | DECL+ |
| `acs_48m_wellens` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT− | DRAFT− | DRAFT− | DRAFT− | DECL− | DECL− |
| `acs_70f_left_main` | acs | NR | NR | NR | NR | TARGET | NR | TARGET | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT? | DECL− | DECL+ |
| `anaphylaxis_29f` | anaphylaxis | NR | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL− |
| `anaphylaxis_63m_betablocked` | anaphylaxis | NR | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT? | DECL− | DECL− |
| `asthma_24f` | asthma | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT? | DRAFT? | DECL− | DECL− |
| `asthma_49m` | asthma | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL− |
| `bradycardia_ccb_68m` | bradycardia | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL− |
| `bradycardia_avb3_78f` | bradycardia | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL− |
| `bradycardia_bb_54f` | bradycardia | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL− |
| `bradycardia_hyperk_63m` | bradycardia | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL− |
| `gi_bleed_57m` | gi_bleed | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL+ |
| `gi_bleed_72f` | gi_bleed | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL+ |
| `hypoglycemia_28m` | hypoglycemia | NR | NR | NR | TARGET | TARGET | NR | NR | NR | NR | NR | NR | DRAFT+ | DRAFT? | DRAFT− | DRAFT− | DECL− | DECL− |
| `hypoglycemia_76f` | hypoglycemia | NR | NR | NR | TARGET | TARGET | NR | NR | NR | NR | NR | NR | DRAFT+ | DRAFT? | DRAFT− | DRAFT− | DECL− | DECL− |
| `hypoglycemia_54m_thiamine` | hypoglycemia | NR | NR | NR | TARGET | TARGET | NR | NR | NR | NR | NR | NR | DRAFT+ | DRAFT? | DRAFT− | DRAFT− | DECL− | DECL− |
| `opioid_35m` | opioid | NR | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL− |
| `opioid_67f` | opioid | NR | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL− |
| `pneumonia_46f` | pneumonia | NR | NR | TARGET | NR | NR | NR | NR | TARGET | NR | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT? | DECL− | DECL+ |
| `pneumonia_83m` | pneumonia | NR | NR | TARGET | NR | NR | NR | NR | TARGET | NR | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT? | DECL− | DECL+ |
| `pulmonary_edema_58m` | pulmonary_edema | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL+ |
| `pulmonary_edema_75f` | pulmonary_edema | NR | NR | TARGET | NR | NR | NR | NR | NR | NR | NR | TARGET | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT+ | DECL− | DECL+ |
| `pulmonary_embolism_33f` | pulmonary_embolism | NR | NR | NR | NR | NR | NR | TARGET | TARGET | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT? | DRAFT? | DECL− | DECL+ |
| `pulmonary_embolism_61m` | pulmonary_embolism | NR | NR | NR | NR | NR | NR | TARGET | TARGET | TARGET | NR | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT? | DECL− | DECL+ |
| `renal_colic_34m` | renal_colic | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | DRAFT− | DRAFT− | DRAFT− | DRAFT− | DECL− | DECL− |
| `obstructive_pyelonephritis_58f` | renal_colic | NR | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT+ | DRAFT− | DECL− | DECL+ |
| `trauma_limb_hemorrhage_27m` | trauma | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT? | DRAFT− | DECL− | DECL+ |
| `trauma_hemothorax_41m` | trauma | NR | NR | NR | NR | NR | NR | NR | NR | TARGET | TARGET | NR | DRAFT+ | DRAFT+ | DRAFT? | DRAFT− | DECL− | DECL+ |

## Totales por objetivo

| Objetivo | TARGET | DECLARED YES | DECLARED NO | NOT REVIEWED | DRAFT YES | DRAFT NO | DRAFT UNCERTAIN | Casos |
|---|---|---|---|---|---|---|---|---|
| R1-03 | 0 | 0 | 0 | 31 | 0 | 0 | 0 | 31 |
| R1-04 | 0 | 0 | 0 | 31 | 0 | 0 | 0 | 31 |
| R1-05 | 4 | 0 | 0 | 27 | 0 | 0 | 0 | 31 |
| R1-06 | 7 | 0 | 0 | 24 | 0 | 0 | 0 | 31 |
| R1-07 | 9 | 0 | 0 | 22 | 0 | 0 | 0 | 31 |
| R2-01 | 0 | 0 | 0 | 31 | 0 | 0 | 0 | 31 |
| R2-02 | 8 | 0 | 0 | 23 | 0 | 0 | 0 | 31 |
| R2-03 | 4 | 0 | 0 | 27 | 0 | 0 | 0 | 31 |
| R2-04 | 14 | 0 | 0 | 17 | 0 | 0 | 0 | 31 |
| R2-05 | 8 | 0 | 0 | 23 | 0 | 0 | 0 | 31 |
| R3-01 | 6 | 0 | 0 | 25 | 0 | 0 | 0 | 31 |
| TD1 | 0 | 0 | 0 | 0 | 26 | 2 | 3 | 31 |
| F1 | 0 | 0 | 0 | 0 | 23 | 5 | 3 | 31 |
| C1 | 0 | 0 | 0 | 0 | 18 | 8 | 5 | 31 |
| C3 | 0 | 0 | 0 | 0 | 6 | 18 | 7 | 31 |
| C4 | 0 | 0 | 31 | 0 | 0 | 0 | 0 | 31 |
| C14 | 0 | 14 | 17 | 0 | 0 | 0 | 0 | 31 |

- **Desafíos sin `families`:** R1-03, R1-04, R2-01. Se sirven con encuentros generados
  (`encounter_generator.SUPPORTED_CHALLENGES`); ningún caso del banco es su TARGET.
- **Casos que son TARGET de al menos un desafío:** 31 de 31.
- **C14:** 14 DECLARED YES, 17 DECLARED NO y 0 NOT REVIEWED (ciclo 7: `acs_54m_inferior` NO).
- **C4:** 31 DECLARED NO: la razón es del entorno de observación, no de los casos (TDFC-7/8, H4).

## Dudas del borrador y la decisión que las resuelve

| Decisión | Pregunta | Celdas DRAFT UNCERTAIN |
|---|---|---|
| TDFC-1 | TD1 · SCA estable con un ECG que exige intervención inmediata | `acs_61m_posterior` TD1, `acs_52m_de_winter` TD1, `acs_66f_nonst` TD1 |
| TDFC-2 | F1 · Hipoglicemia con vía aérea, ventilación y circulación conservadas | `hypoglycemia_28m` F1, `hypoglycemia_76f` F1, `hypoglycemia_54m_thiamine` F1 |
| TDFC-3 | C1 · Hipoxemia grave sin shock que la primera línea suele estabilizar | `pulmonary_embolism_33f` C1, `asthma_24f` C1 |
| TDFC-4 | C1 · Trauma mientras C2 sigue deshabilitada | `trauma_limb_hemorrhage_27m` C1, `trauma_hemothorax_41m` C1 |
| TDFC-5 | C1 y C3 · Deterioro por diseño durante la espera de la reperfusión | `acs_54m_inferior` C1, `acs_70f_left_main` C3 |
| TDFC-6 | C3 · Oxígeno ante hipoxemia sin falla ventilatoria ni amenaza de vía aérea | `pneumonia_46f` C3, `pneumonia_83m` C3, `pulmonary_embolism_33f` C3, `pulmonary_embolism_61m` C3, `asthma_24f` C3, `anaphylaxis_63m_betablocked` C3 |
| TDFC-7 | C4 · Sedoanalgesia para un procedimiento que el caso trae y no declara | `bradycardia_avb3_78f` C4, `trauma_hemothorax_41m` C4, `trauma_limb_hemorrhage_27m` C4 |
| TDFC-8 | C4 · Analgesia del cuadro, sin procedimiento | `renal_colic_34m` C4 |

## Qué dejarían las respuestas (YES / NO / UNCERTAIN)

Derivado con la misma lógica que `c14_review.derive`: una celda dudosa toma el resultado de su
decisión; sin respuesta, sigue en duda. No es una recomendación de aprobar en bloque.

| Objetivo | Borrador actual | Si se aprueban las 8 recomendaciones | Si se rechazan las 8 |
|---|---|---|---|
| TD1 | 26 / 2 / 3 | 26 / 5 / 0 | 29 / 2 / 0 |
| F1 | 23 / 5 / 3 | 26 / 5 / 0 | 23 / 8 / 0 |
| C1 | 18 / 8 / 5 | 19 / 12 / 0 | 22 / 9 / 0 |
| C3 | 6 / 18 / 7 | 13 / 18 / 0 | 6 / 25 / 0 |
| C4 | 0 / 27 / 4 | 0 / 31 / 0 | 4 / 27 / 0 |

## Fuentes leídas

Leídas como texto y analizadas con `ast`: no se importó ni ejecutó ningún módulo del repositorio.

| Archivo | sha256 (12) |
|---|---|
| `case_assessment_bank.py` | 09a1d7fc7d38 |
| `cognitive_catalog.py` | 919baeb78f97 |
| `curriculum.py` | 8dda19ce4af9 |
| `clinical_cases.py` | 27f0eeb7e3d0 |
| `hypoglycemia_catalog.py` | d4e5f7fb6893 |
| `c14_review.py` | 625312d5b486 |
| `BORRADOR_TDFC.md` (esta carpeta) | 3afaa555e03f |
