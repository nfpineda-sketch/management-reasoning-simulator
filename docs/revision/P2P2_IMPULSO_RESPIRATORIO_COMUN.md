# P2P-2 · Composición común del impulso respiratorio

Rama `phase-2-clinical-core-shadow`. Todo es sombra: nada llega al tiempo de ejecución ni cambia lo que ve el
residente. Los bloques entre marcadores `generado` salen del registro congelado
`docs/revision/P2P2_respiratory_drive.json` con `python -m clinical_core.respiratory_drive_report`. El congelamiento
`0c35a29` precede a la evaluación del registro.

## 1. Encargo y alcance

Es un paquete estructural pequeño, no una calibración del edema pulmonar. Crea en el núcleo común una composición del
impulso respiratorio que puede representar a la vez:

- el impulso excitatorio, ácido e hipoxémico;
- la depresión respiratoria central.

No usa ecuaciones de FR por enfermedad. Quedan fuera:

- la mecánica, la fatiga y la VNI;
- el gas alveolar;
- toda calibración del impulso hipóxico;
- la migración del opioide y del TEP.

## 2. La vía vigente, auditada (P2P-2-1)

La auditoría lee el `derived.py` de P2P-1 (`2cd0a12`), demostrado byte a byte por la reversión.

- **Candidata P2K-2** (la del perfil común de ACS y del edema):
  - FR = min(rr_max, intrínseca + S (1 − exp(−impulso / S)));
  - impulso = acid_to_drive_gain × carga ácida;
  - la carga ácida nace del déficit efectivo de O2 y se aclara con su constante de tiempo;
  - ventilación = eficiencia × FR / intrínseca / demanda, y la PaCO2 se ancla a la llegada.
- **Vía P2K-1** (perfil por defecto, golden GI): la FR multiplica max(0, 1 + min(0, W)). Un W negativo es la única
  depresión central, y además un W positivo es carga.
- **Lectores de la hipoxemia:**
  - la FC, relativa a la llegada;
  - la escalera de conciencia de `derive` (absoluta, 87 / 80);
  - la candidata de P2L-2, que no está cableada;
  - la FR no lee ninguna.

<!-- generado:auditoria -->
- `respiration` de P2P-1 lee SpO2: no; lee W: no; términos del impulso: acid_to_drive_gain; `rate_from_drive` lee una disponibilidad: no.
- La vía P2K-1 lee W: sí (factor de depresión `max(0, 1 + min(0, W))`).
- **Clasificación:** candidata P2K-2 `EXCITATORY_DRIVE_EXPLICIT (acid only) without a central-availability layer; the hypoxaemic slot declared and empty; drive (-> RR) and effective ventilation (efficiency) separate`; vía P2K-1 `MIXED_DRIVE_AND_OUTPUT (W read as both load and depression; lactate as the acid proxy)`.
<!-- /generado:auditoria -->

## 3. La composición común (P2P-2-2 a P2P-2-5)

```
impulso excitatorio = impulso ácido + impulso hipoxémico          (equivalentes de resp/min)
FR excitatoria      = intrínseca + S (1 − exp(−impulso excitatorio / S))   (rate_from_drive, sin cambios)
FR expresada        = disponibilidad central × FR excitatoria
```

- **Impulso basal:** la FR intrínseca, que la disponibilidad nunca reescribe.
- **Impulso ácido:** el de P2K-2, sin cambios.
- **Impulso hipoxémico:** la ganancia por la señal normalizada de la SpO2 **absoluta actual**. La señal sale de una
  tabla de puntos (SpO2, 0–1), lineal entre ellos. Por defecto la tabla y la ganancia son `None` (UNSET).
- **Disponibilidad central:** de 0 a 1, por defecto 1. Es una entrada estructural del perfil, como la eficiencia
  ventilatoria lo es del lado de la salida.
- **Agregación:** la suma conceptual de la docencia, en el hueco que P2K-2 declaró, antes de la única saturación
  común. Si la respuesta clínica es aditiva, máxima o sinérgica queda en ACID_HYPOXAEMIA_INTERACTION_UNSET. Las sondas
  sólo exigen una composición monótona.
- **Colocación:** la disponibilidad multiplica la FR excitatoria ya saturada (POST_SATURATION). Así, la FR nunca supera
  disponibilidad × (intrínseca + S), sea cual sea el impulso. Una disponibilidad ≤ intrínseca / (intrínseca + S)
  mantiene la FR en la intrínseca o por debajo, para todo impulso, sin valor alguno de las ganancias UNSET.
  - La alternativa previa a la saturación también baja el basal, pero un impulso hipoxémico lo bastante grande
    vencería cualquier depresión fija.
  - Se rechaza restar del impulso hipoxémico, bloquear sólo el incremento o competir tras sumar la intrínseca.
  - La atenuación es proporcional. Si la depresión embota el quimiorreflejo más que proporcionalmente queda en
    CENTRAL_DEPRESSION_RESPONSE_SHAPE_UNSET.
- **Ancla de PaCO2:** es la de P2K-2: la ventilación de llegada sólo con el impulso ácido, disponibilidad 1 y eficiencia
  de referencia (ARRIVAL_PACO2_ANCHOR_AT_THE_P2K2_REFERENCE). Se aplica al lado del impulso la regla que la revisión de
  P2K-2 fijó para la eficiencia: una depresión central o un impulso hipoxémico mueven la PaCO2 desde el ancla, nunca
  quedan absorbidos.
  - La hipoventilación central sube la PaCO2 y baja el pH.
  - La misma FR actual da la misma PaCO2 sea cual sea la SpO2 de llegada.
  - Con los valores por defecto, la PaCO2 de llegada es exacta. Con los términos nuevos activos se aparta de la autoral,
    como con una eficiencia menor, y se informa.
  - La alternativa, absorber la composición de llegada en el ancla, dejaba eucápnico a un paciente deprimido (revisión
    adversarial, H1) y se rechaza.

## 4. Sondas D1–D10 (P2P-2-6)

<!-- generado:sondas -->
| Sonda | Pregunta | Cumple |
|---|---|---|
| D1 | normal acid, normal oxygenation, availability 1: the baseline spontaneous drive (the intrinsic RR) | sí |
| D2 | acid drive only: the drive increases | sí |
| D3 | hypoxaemic drive only: the drive increases | sí |
| D4 | acid + hypoxaemia: never lower than either alone | sí |
| D5 | lower availability, excitatory inputs fixed: the expressed drive decreases | sí |
| D6 | strong central depression + hypoxaemia: no tachypnoea | sí |
| D7 | strong central depression + acid drive: no tachypnoea | sí |
| D8 | availability 1, hypoxaemic drive UNSET: the P2K / P2P respiratory behaviour reproduced exactly | sí |
| D9 | availability toward 0: severe bradypnoea / apnoea tendency, the intrinsic RR unchanged | sí |
| D10 | central depression changes drive only: G, SpO2, acid burden, DO2, D and lactate unchanged | sí |

- D1 FR 16,00 (intrínseca 16,0); D2 21,33; D3 21,33; D4 25,53 (subaditiva: sí).
- D5 (disponibilidad → FR, entradas fijas): 1,00 → 25,53, 0,75 → 19,15, 0,50 → 12,77, 0,25 → 6,38, 0,00 → 0,00.
- D6: disponibilidad 1 → 35,95, 0,30 → 10,79, con un impulso enorme → 12,30 (cota 12,30; disponibilidad que acota todo impulso a la intrínseca ≤ 0,390); D7: disponibilidad 1 → 35,95, 0,30 → 10,79, con un impulso enorme → 12,30 (cota 12,30; disponibilidad que acota todo impulso a la intrínseca ≤ 0,390).
- D8: 24 cursos comparados bit a bit contra el núcleo de P2P-1 (GI, ACS, edema, acidosis); idénticos: sí.
- D9 (disponibilidad → FR): 0,100 → 2,5530, 0,010 → 0,2553, 0,001 → 0,0255, 0,000 → 0,0000; lineal: sí; FR intrínseca intacta: sí.
- D10: estados idénticos sí; lecturas que cambian: respiratory_rate; G, D, L, carga ácida, SpO2, aporte, lactato, FC y conciencia sin cambio: sí; FR 19,35 → 5,81, PaCO2 33,07 → 110,23, pH 7,484 → 6,961; la depresión hipoventila (FR menor, PaCO2 mayor, pH menor): sí.
<!-- /generado:sondas -->

## 5. La señal hipoxémica es absoluta (P2P-2-3)

<!-- generado:absoluta -->
- Misma SpO2 actual con llegadas distintas: llegada 85 %: SpO2 actual 85,00, impulso 3,0000; llegada 91 %: SpO2 actual 85,00, impulso 3,0000; llegada 97 %: SpO2 actual 85,00, impulso 3,0000; misma PaCO2: sí.
- Una llegada a 81 % ya tiene impulso hipoxémico: 3,800; la composición de llegada es la del estado de llegada: sí.
- Las funciones hipoxémicas del núcleo leen la llegada: no.
<!-- /generado:absoluta -->

## 6. Edema pulmonar, sólo como diagnóstico (P2P-2-7, P2P-2-8)

Se usa `pulmonary_edema_58m` con el escritor de P2P-1 (progresión media), en aire ambiente y con FiO2 0,6. Se
comparan la línea base de P2P-1 (UNSET) y dos ganancias SYNTHETIC_ONLY predeclaradas, 5 y 10, sobre una tabla lineal
de 100 % (0) a 50 % (1). No se busca la FR 38 y ninguna ganancia sale del caso.

En la primera corrida exploratoria, antes del congelamiento, la FR neta del curso sin tratar seguía bajando aun con el
impulso hipoxémico. Por eso el diagnóstico se reformuló para leer por separado:

- la cuota hipoxémica;
- la cuota ácida;
- la FR neta.

La lectura no cambió la regla de preparación, que nunca dependió de este diagnóstico.

<!-- generado:edema -->
| Corrida | Minuto | SpO2 | FR | PaCO2 | Impulso ácido | Impulso hipoxémico |
|---|---|---|---|---|---|---|
| synthetic_10 | 0 | 81,00 | 21,49 | 41,70 | 2,400 | 3,800 |
| synthetic_10 | 30 | 80,29 | 21,18 | 42,30 | 1,867 | 3,941 |
| synthetic_10 | 60 | 79,67 | 20,95 | 42,77 | 1,453 | 4,066 |
| synthetic_10 | 90 | 79,12 | 20,78 | 43,12 | 1,130 | 4,176 |
| synthetic_10 | 120 | 78,63 | 20,66 | 43,38 | 0,879 | 4,273 |
| synthetic_5 | 0 | 81,00 | 19,95 | 44,92 | 2,400 | 1,900 |
| synthetic_5 | 30 | 80,29 | 19,56 | 45,82 | 1,867 | 1,971 |
| synthetic_5 | 60 | 79,67 | 19,25 | 46,54 | 1,453 | 2,033 |
| synthetic_5 | 90 | 79,12 | 19,02 | 47,12 | 1,130 | 2,088 |
| synthetic_5 | 120 | 78,63 | 18,84 | 47,56 | 0,879 | 2,137 |
| unset | 0 | 81,00 | 18,29 | 49,00 | 2,400 | 0,000 |
| unset | 30 | 80,29 | 17,80 | 50,35 | 1,867 | 0,000 |
| unset | 60 | 79,67 | 17,41 | 51,47 | 1,453 | 0,000 |
| unset | 90 | 79,12 | 17,10 | 52,39 | 1,130 | 0,000 |
| unset | 120 | 78,63 | 16,86 | 53,14 | 0,879 | 0,000 |

synthetic_10: FR de llegada 21,49 (brecha a 38: 16,51), cuota hipoxémica sube con la SpO2 sí, cuota ácida −1,521, FR neta −0,835, el O2 baja la FR sí; synthetic_5: FR de llegada 19,95 (brecha a 38: 18,05), cuota hipoxémica sube con la SpO2 sí, cuota ácida −1,521, FR neta −1,110, el O2 baja la FR sí; unset: FR de llegada 18,29 (brecha a 38: 19,71), cuota hipoxémica sube con la SpO2 no, cuota ácida −1,521, FR neta −1,424, el O2 baja la FR no.

FR de llegada sube con el impulso: sí; a más impulso, menos PaCO2: sí; dirección sensata: sí; ganancia tomada del caso: no.

NET_RR_TREND_DEPENDS_ON_UNSET_GAIN: the hypoxaemic share rises as SpO2 falls while the acid share falls as the arrival burden clears; which wins over the untreated course is a matter of the UNSET hypoxaemic gain, not of the architecture.

RESPIRATORY_MECHANICS_EFFICIENCY_GAP: a stronger drive gives a higher RR and a LOWER PaCO2 through P2K-2's ventilation, while the authored patient has RR 38 with PaCO2 49: drive alone cannot give high RR with high PaCO2 (EXPECTED_RESPIRATORY_MECHANICS_EXTENSION).
<!-- /generado:edema -->

## 7. Contraste opioide sintético (P2P-2-9)

Es un estado sintético con depresión central marcada (disponibilidad 0,3) e hipoxemia (SpO2 82), con el resto de la
fisiología de la sonda de bandas. No hay término, escritor ni caso de opioide.

<!-- generado:opioide -->
| Estado | SpO2 | Impulso hipoxémico | FR excitatoria | FR expresada | Intrínseca | PaCO2 | FC | Conciencia |
|---|---|---|---|---|---|---|---|---|
| hypoxaemia_intact | 82,0 | 3,60 | 19,35 | 19,35 | 16,0 | 33,07 | 80,0 | 1 |
| hypoxaemia_depressed | 82,0 | 3,60 | 19,35 | 5,81 | 16,0 | 110,23 | 80,0 | 1 |
| strong_hypoxaemic_drive_depressed | 82,0 | 360000,00 | 41,00 | 12,30 | 16,0 | 52,03 | 80,0 | 1 |

depression_dominates sí; depression_raises_paco2 sí; dominates_any_hypoxaemic_drive sí; hr_consciousness_unchanged sí; hypoxaemia_drives_when_intact sí; spo2_unchanged_by_depression sí.
<!-- /generado:opioide -->

## 8. Acidosis metabólica sintética (P2P-2-10)

<!-- generado:acidosis -->
| Disponibilidad | Impulso ácido | FR expresada | Intrínseca |
|---|---|---|---|
| 1,00 | 20,00 | 29,77 | 16,0 |
| 0,75 | 20,00 | 22,33 | 16,0 |
| 0,50 | 20,00 | 14,88 | 16,0 |
| 0,25 | 20,00 | 7,44 | 16,0 |

La acidemia sube el impulso con disponibilidad 1: sí; la depresión central lo atenúa: sí.
<!-- /generado:acidosis -->

## 9. FC, conciencia y lectores aguas abajo (P2P-2-11)

La FR no alimenta ningún estado: ni el integrador ni la FC la leen. Por eso la composición no escribe FC, N ni
conciencia, y sus efectos sólo llegan por la fisiología ya certificada (ventilación → PaCO2 → pH, en la lectura).

<!-- generado:aguas_abajo -->
- Las funciones de la composición escriben atributos: no.
- El integrador lee la respiración: no; la FC lee el impulso: no.
<!-- /generado:aguas_abajo -->

## 10. Sin valores clínicos, sin mecánica, sin términos de enfermedad

<!-- generado:limites -->
- Literales numéricos de la composición: 0.0.
- La composición lee la eficiencia ventilatoria: no.
- Valores por defecto: mapeo None, ganancia None, disponibilidad 1.0.
- Términos de enfermedad en las inserciones del núcleo: ninguno; estado nuevo: ninguno.
<!-- /generado:limites -->

## 11. Estado de los parámetros (P2P-2-12)

| Parámetro | Estado |
|---|---|
| Mapeo clínico de la hipoxemia | UNSET (`None`) |
| Ganancia hipoxémica | UNSET (`None`) |
| Mapeo de la depresión central por familia | UNSET |
| Disponibilidad central | 1 por defecto |
| Parámetros del impulso ácido | sin cambios (P2K-2) |
| k, s, r | UNSET (referencia SYNTHETIC_ONLY 1 / 5 / 0,5 sólo en sondas) |

Ningún parámetro respiratorio clínico queda aprobado.

## 12. L_rev, VCI, guarda de G y FC de llegada

- **L_rev:** queda en 0 para `pulmonary_edema_58m`. No hay observaciones autorales posteriores a la llegada que fijen
  una reserva reversible; que la congestión «can be reduced» apoya el concepto, no un valor. No se ajusta al legado.
- **VCI:** COMMON_IVC_TO_PRELOAD_RULE_DEFERRED. No hay regla universal VCI → V; un mapeo de llegada de familia puede
  leer la VCI.
- **Guarda de G:** no se modifica. Hoy:
  - el canal de G tiene su guarda del integrador;
  - con L_rev = 0 el crédito de intercambio sostiene G como en P2O-1;
  - con L_rev < 0, una G bajo 0 detiene la corrida.

  Es G_GUARD_SEMANTICS_DEBT y no bloquea la arquitectura del impulso.
- **FC de llegada:** ARRIVAL_HR_COMMON_GAP, observada ya de forma independiente en ACS y en el edema pulmonar. La FC no
  se reabre.

## 13. No regresión

<!-- generado:no_regresion -->
- GI (O12 de P2O-1) reproducido: sí.
- evaluación ACS de P2O-1 reproducido: sí.
- autoridad ACS (R7 de P2O-3) reproducido: sí.
- sobrecarga común (R8) reproducido: sí.
- curso sin tratar de P2P-1 reproducido: sí.
- oxígeno de P2P-1 reproducido: sí.
- respiración de P2P-1 reproducido: sí.
- FC de P2P-1 reproducido: sí.
- conciencia de P2P-1 reproducido: sí.
- Archivos comunes intactos: 25 de 25.
<!-- /generado:no_regresion -->

## 14. Demostración

<!-- generado:prueba -->
- Archivos reconstruidos byte a byte como los dejó P2P-1: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/lactate_slice.py` sí.
- Digest congelado de P2P-1 reproducido por la vista: sí; registro de P2P-1 intacto: sí; archivos comunes de P2P-1 intactos vistos desde P2P-1: 23 de 23.
<!-- /generado:prueba -->

## 15. Preparación (P2P-2-13)

<!-- generado:preparacion -->
| Criterio | Cumple |
|---|---|
| absolute hypoxaemic drive can enter (D3; same current SpO2, same drive; an 81 % arrival already drives) | sí |
| baseline, acid and hypoxaemic drive separable (D1, D2, D4; acidosis probe) | sí |
| central depression suppresses baseline and excitatory drive (D5, D7, D9; acidosis attenuation) | sí |
| default behaviour unchanged (D8) | sí |
| mechanics explicitly separate (D10; no new state; the composition reads no efficiency) | sí |
| no clinical gain, threshold or curve selected; no disease term in the core | sí |
| opioid-like hypoxaemia does not force tachypnoea (D6; cross-family probe) | sí |
| prior families unchanged (GI, ACS, the P2P-1 baseline; HR and consciousness; the P2P-1 tree proven and audited) | sí |

**Veredicto:** `COMMON_RESPIRATORY_DRIVE_ARCHITECTURE_READY`.

**Recomendación:** `PROCEED_TO_PE_GENERALIZATION_AUDIT` (no se inicia). Alcance de esa auditoría: direct G without L; obstructive / RV physiology without false pulmonary congestion; whether the hypoxaemic-drive architecture generalizes structurally. No PE migration in P2P-2.
<!-- /generado:preparacion -->

## 16. Ondulación sobre los paquetes cerrados

- Los paquetes cerrados leen el árbol de P2P-1 a través de `rd.chain` y `rd.p2p1_sources`. Lo hacen las 18 pruebas
  encadenadas, la de P2P-1 y la auditoría de P2O-2, que ahora pasa por la cadena.
- Sus registros no cambian.
- **Excepciones explícitas:**
  - la prueba de ACS excluye el módulo de P2P-2 de los lectores de la familia, porque sus pines nombran los archivos
    ACS;
  - la de RR lo excluye de los lectores de W y suma sus entradas de tupla;
  - la de aislamiento le admite `sys` y `types`, que la sonda D8 necesita para ejecutar el núcleo de P2P-1.
- **Golden:** sólo tres entradas de parámetros.
- **Registros históricos:** P2G, P2I, P2I-2T y P2I-2U se regeneraron (sólo los digests).

## 17. Revisión adversarial

Hubo una revisión independiente y de sólo lectura, sobre el candidato **antes** del congelamiento. Encontró un hallazgo
medio y uno bajo, ninguno alto, ambos confirmados con sondas. Los dos se corrigieron antes de `0c35a29`, así que el
paquete se congeló una sola vez.

- **H1 (media), el ancla de PaCO2 absorbía la composición de llegada:** con una disponibilidad estática, la depresión
  central no movía la PaCO2 ni el pH. Un paciente deprimido con FR 5,8 quedaba con PaCO2 40.
  - Corrección: el ancla vuelve a ser la de P2K-2 (sólo el impulso ácido, disponibilidad 1, eficiencia de referencia).
    Es la regla que la revisión de P2K-2 fijó para la eficiencia, aplicada al lado del impulso
    (ARRIVAL_PACO2_ANCHOR_AT_THE_P2K2_REFERENCE).
  - Resultado: la hipoventilación central sube la PaCO2 y baja el pH (D10, sonda opioide), y la misma FR actual da la
    misma PaCO2 sea cual sea la SpO2 de llegada (sonda absoluta).
  - Precio: con los términos nuevos activos, la PaCO2 de llegada se aparta de la autoral, igual que con una eficiencia
    menor. Con los valores por defecto sigue exacta.
- **H2 (baja):** el criterio 7 de preparación no decidía con su propia evidencia. Ahora la mecánica (criterio 6) y la
  ausencia de valores clínicos (criterio 7) se leen por separado, y la auditoría pasa al criterio 8.
- **Sospechas declaradas:**
  - D8 aplica el `derive` de P2P-1 sobre estados integrados por el núcleo vivo. Es válido porque el integrador está
    fijado por bytes y no lee ninguna función cambiada; dejaría de serlo si el integrador leyera la respiración.
  - Si la reversión fallara, la auditoría y D8 lanzarían un error en lugar de devolver NOT_READY: fallan cerradas.
- **Lo que se comprobó sólido:**
  - la reversión exacta y los 25 archivos comunes;
  - D8 discrimina una perturbación de 1e-12 del valor por defecto;
  - el impulso hipoxémico es absoluto (un mutante relativo a la llegada hace fallar la sonda);
  - la depresión llega bajo la intrínseca (un mutante que sólo bloquea el incremento hace fallar D6, D7 y D9);
  - no hay umbral, curva, opioide, mecánica ni estado nuevo;
  - la depresión no tiene efectos colaterales en G, SpO2, carga ácida, aporte, D, lactato, FC ni conciencia;
  - el edema se usó sólo para la dirección.

## 18. Brechas y decisiones pendientes

- **RESPIRATORY_MECHANICS_EFFICIENCY_GAP / EXPECTED_RESPIRATORY_MECHANICS_EXTENSION:** el impulso solo no da FR alta con
  PaCO2 alta (edema 58m: FR 38, PaCO2 49). A más impulso, menos PaCO2. Hace falta mecánica o fatiga, que se espera con más
  evidencia de familias.
- **Mapeo clínico de la hipoxemia y ganancia hipoxémica:** UNSET. Con las ganancias sintéticas, la FR neta del edema sin
  tratar todavía baja, porque el ácido de llegada se aclara (NET_RR_TREND_DEPENDS_ON_UNSET_GAIN).
- **ACID_HYPOXAEMIA_INTERACTION_UNSET** y **CENTRAL_DEPRESSION_RESPONSE_SHAPE_UNSET:** no se decide si la interacción es
  aditiva, máxima o sinérgica, ni si la atenuación es proporcional o más que proporcional.
- **CENTRAL_AVAILABILITY_PER_MINUTE_ROUTE_DEFERRED:** la disponibilidad es estática por corrida. Un escritor que la
  cambie en el tiempo, y su reversión, necesita un hueco de estado que decidirá otro paquete.
- **OPIOID_FAMILY_WRITER_DEFERRED:** sin mapeo de familia de la disponibilidad.
- **ONE_CENTRAL_DEPRESSION_SOURCE_ONLY:** la depresión por W < 0 de la vía P2K-1 queda en la vía sin ácido-base (el golden
  GI). En la integración en tiempo de ejecución debe quedar una sola fuente.
- **DRIVE_TO_VENTILATION_SEMANTICS_SPLIT:** P2K-2 lee la ventilación de la FR; P2K-3 recluta W sin la FR. El enlace de
  salida es una decisión posterior.
- **HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED:** sin gas alveolar, la hipoventilación sube la PaCO2 pero no baja la
  SpO2.
- **PaCO2 de llegada con los términos activos:** se aparta de la autoral, igual que con una eficiencia menor. Cuando una
  familia active el impulso, su mapeo de llegada tendrá que declararlo.
- **Sin cambios y sin bloquear:**
  - L_rev = 0 (edema 58m);
  - COMMON_IVC_TO_PRELOAD_RULE_DEFERRED;
  - G_GUARD_SEMANTICS_DEBT;
  - ARRIVAL_HR_COMMON_GAP (ACS y edema).
