# P2P-2 · Extensión respiratoria mínima: paquete de decisión (sin código)

Rama `phase-2-clinical-core-shadow`, sobre `86ad42f` (P2P-1 publicado). Documento de sólo lectura, preparado durante la autorización nocturna tras
P2P-1 = B (`PULMONARY_EDEMA_NEEDS_EXPECTED_RESPIRATORY_EXTENSION`). No se escribió código, no se eligió ningún valor y
no se abrió P2P-2. La verdad que se cita es la del banco de casos (`clinical_cases.py`), leída por ruta.

## 1. Por qué no se abrió P2P-2

La autorización exige que la extensión cumpla cinco condiciones a la vez. Ésta es la evaluación de la más pequeña de
las candidatas, un impulso respiratorio hipoxémico común:

| Condición de la autorización | ¿Se cumple? | Evidencia |
|---|---|---|
| Fisiología claramente común | sí | El quimiorreflejo hipoxémico es común a neumonía, TEP, edema, asma y anafilaxia (§2) |
| Motivada por paquetes previos | sí | Diferida en P2O-1 («impulso hipóxico de la FR»), TAREA 3 y P2K-1 |
| Sin estado canónico nuevo | sí para el impulso; **no** para mecánica o trabajo respiratorio | El impulso se suma al de `derived.respiration`; la mecánica necesita un estado de carga |
| Sin selección de parámetros clínicos | **no** | La forma estructural es una decisión clínica (§3), y con la ganancia UNSET la extensión es inerte |
| Sin ajuste por enfermedad | sí | — |

Además, el motivo decisivo de la letra B es la VNI, acción definitiva autoral del caso, y está fuera de los límites
duros de la autorización. Ninguna extensión permitida cambia la B de `pulmonary_edema_58m`. La migración ya es un
éxito de arquitectura (A o B cuentan como éxito), así que ninguna extensión es requisito para que «proceda».

Resultado: **P2P-2 NO SE ABRE — STOP_FOR_FACULTY** (`MINIMUM_RESPIRATORY_EXTENSION_REQUIRES_FACULTY_DECISION`).

## 2. Evidencia entre familias (verdad autoral de llegada)

| Familia | Caso | SpO2 | FR | Trabajo respiratorio | pH / PaCO2 / HCO3 |
|---|---|---|---|---|---|
| neumonía | pneumonia_46f | 89 | 30 | Increased | 7,42 / 31 / 19,4 |
| neumonía | pneumonia_83m | 91 | 28 | Increased | 7,41 / 33 / 20,2 |
| edema | pulmonary_edema_58m | 81 | 38 | Severe | 7,29 / 49 / 22,8 |
| edema | pulmonary_edema_75f | 84 | 32 | Markedly increased | 7,34 / 43 / 22,4 |
| TEP | pulmonary_embolism_33f | 90 | 30 | Increased | 7,47 / 30 / 21,1 |
| TEP | pulmonary_embolism_61m | 88 | 32 | Markedly increased | 7,43 / 28 / 18,0 |
| asma | asthma_24f | 90 | 34 | Markedly increased | 7,45 / 31 / 20,8 |
| asma | asthma_49m | 89 | 30 | Severe | 7,30 / 51 / 24,2 |
| opioide | opioid_35m | 80 | 6 | Reduced | 7,21 / 69 / 26,7 |
| opioide | opioid_67f | 84 | 8 | Reduced | 7,25 / 61 / 25,8 |
| anafilaxia | anaphylaxis_29f | 91 | 28 | Increased | 7,34 / 33 / 17,2 |
| anafilaxia | anaphylaxis_63m_betablocked | 89 | 26 | Increased | 7,29 / 36 / 16,7 |
| ACS (referencia) | acs_70f_left_main | 94 | 26 | Mildly increased | 7,36 / 33 / 18,0 |
| GI (referencia) | gi_bleed_57m | 97 | 26 | Normal | 7,37 / 31 / 17,3 |

La tabla es una selección: las familias respiratorias y la del opioide, más ACS y GI como referencia. Fuera de
ella, `trauma_hemothorax_41m` (SpO2 91, FR 28) también es hipoxémico con FR alta y no cambia la conclusión.

Lo que muestra la tabla:

- **Hipoxemia con FR alta** en neumonía, TEP, asma, anafilaxia y edema. Un impulso hipoxémico común tiene apoyo en
  cinco familias.
- **Hipoxemia con FR muy baja** en los opioides (SpO2 80–84 con FR 6–8). Un impulso hipoxémico tiene que poder quedar
  suprimido por la depresión central, que el núcleo representa en W y en el impulso. Sin esa composición, el impulso
  daría una FR alta a un paciente opioide: una contradicción causal.
- **Hipercapnia con FR alta** en edema 58m (PaCO2 49) y asma 49m (PaCO2 51). La ventilación falla por mecánica o
  fatiga, no por falta de impulso. Un impulso hipoxémico no lo explica; haría falta mecánica o fatiga, un estado nuevo
  que la autorización excluye.
- **La FR común de hoy** es la del impulso ácido-base (P2K-2). Con HCO3 casi normal queda en 16–18 (P2P-1: 18,3 en la
  llegada del edema), lejos de las FR autorales de 26 a 38.

## 3. Opciones mínimas y lo que debe decidir la docencia

| Opción | Señal y forma | Efecto en la llegada | Interacciones a decidir | Estado nuevo |
|---|---|---|---|---|
| O1 | Hipoxemia relativa a la llegada, como el término de hipoxemia de la FC (umbral 94 ya existente) | Ninguno: la FR de llegada sigue sin reproducirse | Depresión central; saturación con el impulso ácido | No |
| O2 | Hipoxemia absoluta bajo un umbral, como el impulso ácido (absoluto) | Cambia la FR de llegada de toda llegada hipoxémica; acerca la reconstrucción | Depresión central; umbral; ganancia (la docencia elige si y cuándo se activa) | No |
| O3 | Congestión (L) como impulso tipo receptor J | Ninguno (L = 0 en la llegada) | Sólo familias con agua pulmonar (edema, sobrecarga) | No |
| O4 | Carga o mecánica respiratoria (trabajo, fatiga, demanda de O2 muscular) | Depende de un ancla de carga | Hipercapnia con FR alta | Sí (excluida de noche) |

Lo que ninguna opción cubre: la VNI (fuera de límites) y la PaO2 o el gas alveolar (excluidos).

**Decisión mínima que se pide a la docencia:**

1. ¿El impulso hipoxémico común es relativo a la llegada (O1) o absoluto (O2)?
2. ¿Cómo se compone con la depresión central (opioide)?

Con esas dos respuestas, P2P-2 puede implementarse como un término común con la ganancia UNSET (apagado por
defecto), con sondas sintéticas en edema, neumonía, TEP, asma y opioides, y sin tocar GI ni ACS (sus SpO2 de llegada,
94–97, quedan en el umbral o por encima).

## 4. Qué no se hizo

- Sin código, sin valores, sin calibrar el impulso hipóxico, sin k, s ni r.
- Ni VNI, ni mecánica, ni fatiga, ni PaO2.
- No se corrió P2Q-1: la autorización sólo lo permite si P2P-1 es A.
