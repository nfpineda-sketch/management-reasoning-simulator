# P2I-2AE · Estructura de la FC y de la respuesta simpática

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión, el tono vascular ni la FR, ni fija números de FC; no activa el colapso;
- no elige ni aprueba parámetros ocultos ni se ajusta al motor heredado;
- no reabre el lactato (P2I-2AD cerrado: restricciones, rangos y ganancias intactos);
- no reutiliza la región histórica de P2F para el análisis: corre dentro de la guarda de P2I-2AB.

Código:
- `clinical_core/derived.py`: el impulso por deuda es `debt_to_sympathetic_gain × D`; τ_D ya no aparece en la FC; la
  descomposición de llegada separa la parte de la deuda (ganancia × D0) del resto, y una llegada que pediría una
  contribución simpática negativa detiene el núcleo;
- `clinical_core/decision_pack.py`, `clinical_core/lactate_slice.py`: lo construido sobre la región histórica lee las
  llegadas que el núcleo vigente rechaza sin impulso por deuda (ganancia 0), que no llega al lactato, la presión ni
  la FR, y las deja fuera de la FC de P2G; las cuenta;
- `clinical_core/hr_structure.py`: el análisis, congelado en `6052ffb` antes de leer ningún resultado de FC (byte a
  byte el mismo después de la revisión; sólo cambió el hash de fuentes del digest, §16);
- `clinical_core/hr_structure_report.py`: sólo este informe.

Números: `docs/revision/P2I2AE_hr_structure.json`. Registro de partida, cerrado: P2I-2AD (`5cb48163…`), cuyo módulo y
registro quedan fijados por sus pruebas.

## Resumen

- **τ_D ya no llega a la FC.** El término `sympathetic_per_debt × (D − D0) / τ_D` (SEMANTIC_LEAK) se reemplazó por
  `debt_to_sympathetic_gain × D`: 0 con D = 0, nunca decreciente en D, sin τ_D. Con D fija, τ_D 30 / 60 / 120 dan el
  mismo objetivo, el mismo impulso y la misma FC (sondas H5 y prueba de invariancia). τ_D sigue moviendo la FC sólo a
  través de la devolución de D (VALID_CAUSAL_PATH).
- **Equivalencia.** Con τ_D = 60 la ecuación nueva es numéricamente la anterior (ganancia por defecto 1/120 = 0,5/60):
  el golden directo sólo cambia en la metadata de parámetros y el de Contracts v2 es IDÉNTICO.
- **Llegada.** FC de llegada = intrínseca + parte de la deuda (ganancia × D0) + resto, ambas no negativas. Una
  declaración cuya deuda pediría una contribución negativa se rechaza analíticamente y el núcleo la detiene: 17 de 108
  combinaciones (caso × intrínseca × D0 × ganancia). En la región histórica P2F eso afecta a 108 de 1054 candidatos
  (72f con intrínseca 100 y deuda 60 a la ganancia por defecto). El paquete P2G y el corte P2I-1 los leen sin impulso
  por deuda: sus números de lactato, presión y FR son los de antes. Sólo la FC de P2G los deja fuera. El rechazo HR1 de
  P2F con τ_D 30 × deuda superior ya no se reproduce: era la fuga de τ_D.
- **Sin término agudo de oxígeno.** La FC responde a D (B), no al déficit efectivo instantáneo (A); el estímulo agudo
  que existe es el déficit de presión, relativo a la llegada. No se agregó ningún término nuevo.
- **Veredicto: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**, con dos hallazgos que el paquete numérico debe
  decidir (§15): el resto de llegada no se resuelve salvo por la presión, y no hay techo ni saturación de la FC.
- Nada se seleccionó ni aprobó; FR, presión y lactato no cambian.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `1b65d303831011014ca8cf8ce98e5fb880c5ea9cd3244f47773ce9d47b3712c8` (una prueba lo fija). Registro de partida: P2I-2AD `5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-29 |
| TD-92 (τ_D y FC) | tau_D = oxygen-debt repayment only; it must not define the sympathetic drive. D -> drive through an independent debt_to_sympathetic_gain, never derived from tau_D. |
| descomposición de la FC de llegada | arrival HR = intrinsic rhythm component + non-negative sympathetic contribution; no GI-specific HR decrement; legacy HR is not a target; the historical P2F HR1 rejection is not calibration evidence. |
| lactato | LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN accepted: lactate constraints, ranges and gains unchanged; the open upper edge of debt_to_lactate_gain is propagated uncertainty. |
| alcance | shadow only; no pressure / vascular-tone, RR or numeric HR calibration; no collapse, GI migration, second family or runtime integration; no hidden parameter selected or approved. |
<!-- /generado:decisiones -->

## 2. Auditoría de la ecuación de la FC (P2I-2AE-1, P2I-2AE-3)

<!-- generado:auditoria -->
Ecuación anterior (e0dffa8): sinus: HR = R.rate_bpm + hr_per_sympathetic_drive (25) x (1 - beta_blockade) x drive; non-sinus: HR = R.rate_bpm; no pulse: no pulse rate, drive 0. drive: rises at once to the target, decays toward it with exp(-1 / 5 min). target = max(0, S0 + 1.0 x (1 - pressure_rel) + 0.5 x (D - D0) / tau_D + 0.02 x delta hypoxaemia(SpO2 < 94) + 0.01 x delta hypoglycaemia(glucose < 70)), S0 = (HR_arrival - intrinsic) / (25 x (1 - beta)), intrinsic = the declared rate or the arrival HR, pressure_rel = output x tone relative to arrival.

Ecuación nueva: sinus: HR = R.rate_bpm + 25 x (1 - beta_blockade) x drive (unchanged); drive dynamics unchanged. target = max(0, S_rest + 1.0 x (1 - pressure_rel) + debt_to_sympathetic_gain x D + 0.02 x delta hypoxaemia + 0.01 x delta hypoglycaemia), S_rest = S0 - debt_to_sympathetic_gain x D0 >= 0 (else the arrival is inconsistent and the core stops). At arrival the target is S0, so the arrival HR is reproduced exactly; tau_D appears nowhere.

| Contribuyente | Estado |
|---|---|
| frecuencia intrínseca | R.rate_bpm = intrinsic_sinus_rate (case parameter; undeclared: the arrival HR, no sympathetic share). The sinus floor: the drive is never negative. |
| componente simpático | aux.sympathetic_drive x hr_per_sympathetic_drive (25 bpm per unit, ADOPTED) x (1 - beta_blockade). |
| contribución de D | debt_to_sympathetic_gain x D (P2I-2AE; was sympathetic_per_debt x (D - D0) / tau_D). |
| déficit directo | none: no term reads the instantaneous effective oxygen deficit or delivery. |
| estímulo agudo (presión) | sympathetic_per_pressure_deficit (1.0, PROVISIONAL) x (1 - pressure_rel), arrival-relative (the baroreflex stimulus; already separate from D). |
| otros estímulos | hypoxaemia (0.02 per SpO2 point below 94) and hypoglycaemia (0.01 per mg/dL below 70), arrival-relative. |
| resto de llegada | S_rest: the arrival drive the arrival debt does not explain (the arrival pressure deficit and anything unmodelled), constant; only the arrival-relative stimuli move the drive below it. |
| fármacos e intervenciones | none acts on HR directly: fluids, red cells, haemostasis and oxygen act through V, Hb, the bleed flow and SpO2; beta_blockade is a constant case parameter (0: none authored). |
| ritmo | authoritative: a non-sinus perfusing rhythm keeps its own rate; no pulse, no pulse rate; scripted rhythm events and the collapse rule (off) change R. |
| topes y pisos | floor: drive >= 0 (sinus HR >= intrinsic). No upper cap or saturation in the core (the family engine clamps its display to [42, 180]: LEGACY_REFERENCE only). |
| términos del caso | none: the GI module writes no HR or drive; no GI-specific decrement. |

| Vía τ_D → FC | Clase | Estado | Por qué |
|---|---|---|---|
| derived.sympathetic_target: sympathetic_per_debt x (D - D0) / tau_D | SEMANTIC_LEAK | removed (P2I-2AE) | at fixed D and lactate, tau_D rescaled the debt term. Before P2I-2AC, D settled at deficit x tau_D, so D / tau_D read as a lagged deficit; since P2I-2AC D does not repay under a deficit and the division only rescaled the debt's drive by the repayment time. |
| tau_D -> repayment of D across oxygen-adequate minutes -> debt_to_sympathetic_gain x D -> HR | VALID_CAUSAL_PATH | kept | tau_D sets how fast D repays; the drive reads D itself. |
| calibration.REGISTRY sympathetic_per_debt 0.25 / 0.5 / 1.0 'drive per unit D / tau_D' | LEGACY_ARTIFACT | kept for history; the core no longer reads it | its units carry tau_D: one point meant three different gains across the tau_D grid. |
| decision_pack.p2f_rejection: tau_D 30 x arrival debt upper rejected by HR1 (gi_bleed_72f) | LEGACY_ARTIFACT | written history; no longer reproduced by the current core | a case-specific historical outcome of the leak (the drive fell as D repaid at 1 / 30 per minute during a synthetic volume loss); the faculty does not read it as evidence. |
| calibration.check_hr HR1-HR4 over the tau_D levels; decision_pack HR effect tables over sympathetic_per_debt | LEGACY_ARTIFACT | historical harness and tables | probes and tables built on the leak; not current evidence. |
| gi_reference.arrival_debt_band rationale ('60 is the steady state ... at 60 min') | LEGACY_ARTIFACT | values unchanged (lactate closed) | a pre-P2I-2AC steady-state reading; reaches HR only through D0 in the arrival decomposition. |

Déficit directo frente a D (P2I-2AE-3): A (déficit efectivo instantáneo) no; B (D acumulada) sí; C (ambos) no. Término agudo existente: the pressure deficit (1 - pressure_rel), arrival-relative: an acute haemodynamic stimulus, separate from D before and after this package. ¿Hace falta un término nuevo? no: the faculty expectation (acute response to current shock, persistent drive with debt memory) is met structurally by the existing acute pressure term plus gain x D; an anaemia or hypoxaemic under-delivery at preserved pressure reaches the drive only through D (and SpO2 through hypoxaemia). Whether an oxygen-delivery term should be added is a faculty question, not a semantic error, so none is invented.

Lectura del código vigente: `arrival_rest_reads_tau_d` no; `rr_reads_drive_or_rate` no; `sinus_rate_reads_drive` sí; `target_reads_debt_to_sympathetic_gain` sí; `target_reads_effective_deficit` no; `target_reads_sympathetic_per_debt` no; `target_reads_tau_d` no; `update_reads_tau_d` no.
<!-- /generado:auditoria -->

## 3. Anclas de FC de la verdad del repositorio (P2I-2AE-4)

<!-- generado:anclas -->
| Caso | Dato | Valor | Etiqueta | Nota |
|---|---|---|---|---|
| 57m | arrival_hr | 124 | AUTHORED_OBSERVATION | clinical_cases.py:881 |
| 57m | core_hr_after_arrival | — | MODEL_DERIVED | this package's trajectories; not observations |
| 57m | family_engine_hr | — | LEGACY_REFERENCE | read only after the verdict (legacy_reference) |
| 57m | later_hr | not authored | AUTHORED_OBSERVATION | no HR after arrival is stated by the case |
| 57m | medications | ibuprofen most days for two weeks | AUTHORED_OBSERVATION | no beta-blocker or rate control authored: beta_blockade stays 0 |
| 57m | rhythm | Sinus tachycardia | AUTHORED_OBSERVATION | derived by the bank from HR > 100, not authored separately |
| 72f | arrival_hr | 112 | AUTHORED_OBSERVATION | clinical_cases.py:910 |
| 72f | core_hr_after_arrival | — | MODEL_DERIVED | this package's trajectories; not observations |
| 72f | family_engine_hr | — | LEGACY_REFERENCE | read only after the verdict (legacy_reference) |
| 72f | later_hr | not authored | AUTHORED_OBSERVATION | no HR after arrival is stated by the case |
| 72f | medications | naproxen recently; no gastroprotection | AUTHORED_OBSERVATION | no beta-blocker or rate control authored: beta_blockade stays 0 |
| 72f | rhythm | Sinus tachycardia | AUTHORED_OBSERVATION | derived by the bank from HR > 100 |
<!-- /generado:anclas -->

## 4. La banda intrínseca (P2I-2AE-7)

<!-- generado:intrinseca -->
Banda: 57m 60 / 80 / 100; 72f 60 / 80 / 100 lpm. ¿Derivada de HR1? no. Clasificación: **STILL_VALID_CANDIDATE_RANGE**. gi_reference.RESTING_HR is the resting adult sinus range (60 / 80 / 100), capped at the authored arrival HR; its rule reads no HR1 probe, no D, no tau_D and no gain. Under the current physiology it keeps one role: the sinus floor R.rate_bpm the drive falls back to (the arrival share is the authored HR less it). P2I-2AE adds only a joint constraint, intrinsic + 25 x gain x D0 <= arrival HR (non-negative S_rest), applied as an analytic rejection, never by moving the band.
<!-- /generado:intrinseca -->

## 5. El rango candidato de `debt_to_sympathetic_gain` (P2I-2AE-6)

<!-- generado:ganancia -->
Unidades: drive units per unit of D (index-minutes). Regla (congelada antes de cualquier resultado): The candidate range of debt_to_sympathetic_gain (drive units per unit of D), frozen before any HR outcome, from
    dimensional consistency (debt-driven drive = gain x D; 25 bpm per unit of drive, ADOPTED; D in the index-minutes
    of the arrival-debt band, unchanged since P2F), the authored arrival HR, the intrinsic band and the non-negative
    rule only:
    - highest gain: the largest gain any declared arrival can hold with a non-negative rest of the arrival drive, the
      maximum over cases, intrinsic levels and non-zero arrival-debt levels of (HR - intrinsic) / (25 x D0);
    - lowest gain: the largest declared arrival debt moves the arrival HR by the authored HR resolution (1 bpm),
      1 / (25 x max D0); below it the debt's share of the arrival HR is under what the case can show.
    Five points, log-spaced (equal ratios) between the two, both included; 0 is a synthetic reference (no debt-driven
    drive), never counted. Never read: tau_D, any trajectory, the legacy HR, the historical sympathetic_per_debt.

Extremos: 0,000667 (1 lpm a D0 = 60) y 0,128; razón 3,72. Puntos: 0,000667 · 0,00248 · 0,00924 · 0,0344 · 0,128; referencia sintética 0 (sin impulso por deuda, nunca contada). Ancla del corte intrínseco: 0,00924 (punto medio logarítmico, no una selección). Por debajo de 0,008 toda llegada declarada es coherente. El valor por defecto del perfil, 0,00833 (= 0,5 / 60), es un marcador de continuidad PROVISIONAL.

Rango anterior: OLD_SYMPATHETIC_PER_DEBT_RANGE_SEMANTICALLY_INVALID. sympathetic_per_debt (0.25 / 0.5 / 1.0) was a drive per unit of D / tau_D: one point meant a different gain at each tau_D, so the range carries tau_D in its units and cannot be translated into an independent gain. The gains it induced are reported for comparison only. Ganancias que inducía (sólo comparación): τ_D 120: 0,00208 / 0,00417 / 0,00833; τ_D 30: 0,00833 / 0,0167 / 0,0333; τ_D 60: 0,00417 / 0,00833 / 0,0167.
<!-- /generado:ganancia -->

## 6. Descomposición de la FC de llegada y rechazo analítico

<!-- generado:llegada -->
Before any run: for every case, intrinsic level, arrival-debt level and gain, the arrival drive S0 = (HR - intrinsic) / 25 must hold the debt's share gain x D0 (S_rest = S0 - gain x D0 >= 0, exact, as derived.arrival_non_debt_drive computes it). Otherwise ANALYTIC_REJECTION: the arrival would need a negative sympathetic contribution, and the core itself refuses it. No simulation reads such a pair.

Combinaciones: 108; ANALYTIC_REJECTION: 17; FC de llegada reproducida exactamente en todas las coherentes: sí; el núcleo rechaza exactamente las mismas: sí.

**57m** (FC de llegada 124): simpático = deuda + resto, en lpm, por intrínseca y D0 (filas) y ganancia (columnas).

| Intrínseca | D0 | 0,000667 | 0,00248 | 0,00924 | 0,0344 | 0,128 | 0 |
|---|---|---|---|---|---|---|---|
| 60 | 0 | 0,0 + 64,0 | 0,0 + 64,0 | 0,0 + 64,0 | 0,0 + 64,0 | 0,0 + 64,0 | 0,0 + 64,0 |
| 60 | 20 | 0,3 + 63,7 | 1,2 + 62,8 | 4,6 + 59,4 | 17,2 + 46,8 | 64,0 + 0,0 | 0,0 + 64,0 |
| 60 | 60 | 1,0 + 63,0 | 3,7 + 60,3 | 13,9 + 50,1 | 51,6 + 12,4 | rechazo analítico | 0,0 + 64,0 |
| 80 | 0 | 0,0 + 44,0 | 0,0 + 44,0 | 0,0 + 44,0 | 0,0 + 44,0 | 0,0 + 44,0 | 0,0 + 44,0 |
| 80 | 20 | 0,3 + 43,7 | 1,2 + 42,8 | 4,6 + 39,4 | 17,2 + 26,8 | rechazo analítico | 0,0 + 44,0 |
| 80 | 60 | 1,0 + 43,0 | 3,7 + 40,3 | 13,9 + 30,1 | rechazo analítico | rechazo analítico | 0,0 + 44,0 |
| 100 | 0 | 0,0 + 24,0 | 0,0 + 24,0 | 0,0 + 24,0 | 0,0 + 24,0 | 0,0 + 24,0 | 0,0 + 24,0 |
| 100 | 20 | 0,3 + 23,7 | 1,2 + 22,8 | 4,6 + 19,4 | 17,2 + 6,8 | rechazo analítico | 0,0 + 24,0 |
| 100 | 60 | 1,0 + 23,0 | 3,7 + 20,3 | 13,9 + 10,1 | rechazo analítico | rechazo analítico | 0,0 + 24,0 |

**72f** (FC de llegada 112): simpático = deuda + resto, en lpm, por intrínseca y D0 (filas) y ganancia (columnas).

| Intrínseca | D0 | 0,000667 | 0,00248 | 0,00924 | 0,0344 | 0,128 | 0 |
|---|---|---|---|---|---|---|---|
| 60 | 0 | 0,0 + 52,0 | 0,0 + 52,0 | 0,0 + 52,0 | 0,0 + 52,0 | 0,0 + 52,0 | 0,0 + 52,0 |
| 60 | 20 | 0,3 + 51,7 | 1,2 + 50,8 | 4,6 + 47,4 | 17,2 + 34,8 | rechazo analítico | 0,0 + 52,0 |
| 60 | 60 | 1,0 + 51,0 | 3,7 + 48,3 | 13,9 + 38,1 | 51,6 + 0,4 | rechazo analítico | 0,0 + 52,0 |
| 80 | 0 | 0,0 + 32,0 | 0,0 + 32,0 | 0,0 + 32,0 | 0,0 + 32,0 | 0,0 + 32,0 | 0,0 + 32,0 |
| 80 | 20 | 0,3 + 31,7 | 1,2 + 30,8 | 4,6 + 27,4 | 17,2 + 14,8 | rechazo analítico | 0,0 + 32,0 |
| 80 | 60 | 1,0 + 31,0 | 3,7 + 28,3 | 13,9 + 18,1 | rechazo analítico | rechazo analítico | 0,0 + 32,0 |
| 100 | 0 | 0,0 + 12,0 | 0,0 + 12,0 | 0,0 + 12,0 | 0,0 + 12,0 | 0,0 + 12,0 | 0,0 + 12,0 |
| 100 | 20 | 0,3 + 11,7 | 1,2 + 10,8 | 4,6 + 7,4 | rechazo analítico | rechazo analítico | 0,0 + 12,0 |
| 100 | 60 | 1,0 + 11,0 | 3,7 + 8,3 | rechazo analítico | rechazo analítico | rechazo analítico | 0,0 + 12,0 |

<!-- /generado:llegada -->

Lectura: el resto de llegada es todo lo que la deuda no explica de la taquicardia de llegada (la hipotensión de llegada,
la hipoperfusión de llegada y lo no modelado). Con D0 = 0 toda la parte simpática es resto; con la ganancia más alta del
rango y D0 = 20, en 57m con intrínseca 60, la deuda explica toda la parte simpática y el resto es 0 (el borde exacto).

## 7. Trayectorias H1–H4 (P2I-2AE-8)

<!-- generado:trayectorias -->
The (intrinsic level, gain) plane, 3 x 6 (five range points and the 0 reference), post-processed on each of the 18 representative runs (3 tags x 2 cases x L1 / L2 / L3): no simulation beyond the 18 runs and the validation reruns. Analytically rejected pairs are never read. The intrinsic slice is read at the gain anchor (the range's log-midpoint) and the gain slice at intrinsic midpoint; neither is a selection.

Aquí, cada representativo a la intrínseca media y la ganancia ancla (0,00924); los cortes completos de ganancia (cinco puntos y 0) e intrínseca (inferior, media, superior) están en el JSON (`trajectories`) y, por hito, en la superficie de decisión (§10). Columnas en lpm salvo D (índice·min), déficit efectivo, gasto relativo, sangrado (mL/min), glóbulos rojos dados (U) y cristaloide infundido (mL): FC = intrínseca + deuda + presión + resto + otros estímulos + piso + retardo. Hemostasia en el minuto 60 de L3.

### H1: untreated active bleed (L1)

**57m**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 124,0 | 80 | 0,0 | 0,0 | 44,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 126,3 | 80 | 0,7 | 1,6 | 44,0 | 0,0 | 3,1 | 0,438 | 0,94 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 30 | 128,7 | 80 | 1,5 | 3,2 | 44,0 | 0,0 | 6,6 | 0,477 | 0,87 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 60 | 133,7 | 80 | 3,3 | 6,4 | 44,0 | 0,0 | 14,3 | 0,555 | 0,74 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 90 | 139,1 | 80 | 5,4 | 9,7 | 44,0 | 0,0 | 23,2 | 0,636 | 0,61 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 120 | 144,8 | 80 | 7,7 | 13,1 | 44,0 | 0,0 | 33,3 | 0,717 | 0,48 | 2,50 | 0,00 | 0 |
| MID | medio | 0,00924 | 0 | 124,0 | 80 | 4,6 | 0,0 | 39,4 | 0,0 | 20,0 | 0,150 | 1,00 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 125,8 | 80 | 5,2 | 1,2 | 39,4 | 0,0 | 22,5 | 0,193 | 0,95 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 30 | 127,8 | 80 | 5,9 | 2,5 | 39,4 | 0,0 | 25,7 | 0,236 | 0,90 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 60 | 132,2 | 80 | 7,9 | 4,9 | 39,4 | 0,0 | 34,1 | 0,324 | 0,80 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 90 | 137,1 | 80 | 10,4 | 7,3 | 39,4 | 0,0 | 45,1 | 0,412 | 0,71 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 120 | 142,6 | 80 | 13,6 | 9,7 | 39,4 | 0,0 | 58,8 | 0,500 | 0,61 | 5,00 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 0 | 124,0 | 80 | 13,9 | 0,0 | 30,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 125,8 | 80 | 14,1 | 1,6 | 30,1 | 0,0 | 60,9 | 0,063 | 0,94 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 30 | 128,0 | 80 | 14,7 | 3,2 | 30,1 | 0,0 | 63,7 | 0,128 | 0,87 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 133,9 | 80 | 17,4 | 6,4 | 30,1 | 0,0 | 75,2 | 0,260 | 0,74 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 90 | 141,7 | 80 | 21,9 | 9,7 | 30,1 | 0,0 | 94,7 | 0,395 | 0,61 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 120 | 151,5 | 80 | 28,3 | 13,1 | 30,1 | 0,0 | 122,3 | 0,531 | 0,48 | 2,50 | 0,00 | 0 |

**72f**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 112,0 | 80 | 0,0 | 0,0 | 32,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 113,8 | 80 | 0,7 | 1,1 | 32,0 | 0,0 | 3,1 | 0,425 | 0,96 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 30 | 115,6 | 80 | 1,5 | 2,1 | 32,0 | 0,0 | 6,4 | 0,451 | 0,92 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 60 | 119,4 | 80 | 3,1 | 4,3 | 32,0 | 0,0 | 13,5 | 0,504 | 0,83 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 90 | 123,4 | 80 | 5,0 | 6,5 | 32,0 | 0,0 | 21,5 | 0,558 | 0,74 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 120 | 127,7 | 80 | 7,0 | 8,7 | 32,0 | 0,0 | 30,2 | 0,613 | 0,65 | 2,50 | 0,00 | 0 |
| MID | medio | 0,00924 | 0 | 112,0 | 80 | 4,6 | 0,0 | 27,4 | 0,0 | 20,0 | 0,150 | 1,00 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 113,4 | 80 | 5,2 | 0,8 | 27,4 | 0,0 | 22,5 | 0,179 | 0,97 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 30 | 114,9 | 80 | 5,9 | 1,7 | 27,4 | 0,0 | 25,3 | 0,208 | 0,93 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 60 | 118,1 | 80 | 7,5 | 3,3 | 27,4 | 0,0 | 32,5 | 0,269 | 0,87 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 90 | 121,8 | 80 | 9,6 | 4,9 | 27,4 | 0,0 | 41,4 | 0,332 | 0,81 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 120 | 125,9 | 80 | 12,1 | 6,4 | 27,4 | 0,0 | 52,3 | 0,395 | 0,74 | 5,00 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 0 | 112,0 | 80 | 13,9 | 0,0 | 18,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 113,2 | 80 | 14,0 | 1,1 | 18,1 | 0,0 | 60,6 | 0,042 | 0,96 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 30 | 114,7 | 80 | 14,4 | 2,1 | 18,1 | 0,0 | 62,5 | 0,086 | 0,92 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 118,6 | 80 | 16,2 | 4,3 | 18,1 | 0,0 | 70,2 | 0,175 | 0,83 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 90 | 123,9 | 80 | 19,2 | 6,5 | 18,1 | 0,0 | 83,3 | 0,267 | 0,74 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 120 | 130,4 | 80 | 23,6 | 8,7 | 18,1 | 0,0 | 102,0 | 0,360 | 0,65 | 2,50 | 0,00 | 0 |

### H2: crystalloid 2 L over 20 min with continued bleeding (L2)

**57m**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 124,0 | 80 | 0,0 | 0,0 | 44,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 118,3 | 80 | 0,6 | -8,1 | 44,0 | 1,9 | 2,4 | 0,247 | 1,32 | 2,50 | 0,00 | 300 |
| LOW | medio | 0,00924 | 30 | 116,7 | 80 | 1,0 | -8,2 | 44,0 | 0,0 | 4,1 | 0,250 | 1,33 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 60 | 122,9 | 80 | 2,0 | -3,1 | 44,0 | 0,0 | 8,6 | 0,355 | 1,12 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 90 | 129,1 | 80 | 3,4 | 1,7 | 44,0 | 0,0 | 14,7 | 0,460 | 0,93 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 120 | 134,8 | 80 | 5,2 | 5,7 | 44,0 | 0,0 | 22,3 | 0,552 | 0,77 | 2,50 | 0,00 | 400 |
| MID | medio | 0,00924 | 0 | 124,0 | 80 | 4,6 | 0,0 | 39,4 | 0,0 | 20,0 | 0,150 | 1,00 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 122,1 | 80 | 5,1 | -3,0 | 39,4 | 0,6 | 22,0 | 0,127 | 1,12 | 5,00 | 0,00 | 300 |
| MID | medio | 0,00924 | 30 | 122,5 | 80 | 5,6 | -2,4 | 39,4 | 0,0 | 24,1 | 0,154 | 1,10 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 60 | 127,2 | 80 | 6,9 | 0,9 | 39,4 | 0,0 | 30,0 | 0,243 | 0,96 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 90 | 131,6 | 80 | 8,9 | 3,3 | 39,4 | 0,0 | 38,4 | 0,323 | 0,87 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 120 | 136,3 | 80 | 11,4 | 5,5 | 39,4 | 0,0 | 49,2 | 0,399 | 0,78 | 5,00 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 0 | 124,0 | 80 | 13,9 | 0,0 | 30,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 113,5 | 80 | 8,3 | -8,6 | 30,1 | 3,6 | 36,1 | 0,000 | 1,35 | 2,50 | 0,00 | 300 |
| HIGH | medio | 0,00924 | 30 | 106,2 | 80 | 5,0 | -9,8 | 30,1 | 0,8 | 21,7 | 0,000 | 1,39 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 60 | 105,1 | 80 | 1,8 | -6,9 | 30,1 | 0,0 | 7,8 | 0,000 | 1,27 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 90 | 107,2 | 80 | 0,7 | -3,6 | 30,1 | 0,0 | 2,8 | 0,000 | 1,14 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 120 | 111,2 | 80 | 1,0 | 0,1 | 30,1 | 0,0 | 4,1 | 0,095 | 0,99 | 2,50 | 0,00 | 400 |

**72f**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 112,0 | 80 | 0,0 | 0,0 | 32,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 108,4 | 80 | 0,6 | -5,4 | 32,0 | 1,2 | 2,6 | 0,308 | 1,22 | 2,50 | 0,00 | 300 |
| LOW | medio | 0,00924 | 30 | 107,6 | 80 | 1,1 | -5,5 | 32,0 | 0,0 | 4,9 | 0,312 | 1,22 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 60 | 112,2 | 80 | 2,3 | -2,1 | 32,0 | 0,0 | 10,0 | 0,379 | 1,08 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 90 | 116,9 | 80 | 3,7 | 1,1 | 32,0 | 0,0 | 16,2 | 0,447 | 0,96 | 2,50 | 0,00 | 400 |
| LOW | medio | 0,00924 | 120 | 121,2 | 80 | 5,4 | 3,8 | 32,0 | 0,0 | 23,4 | 0,508 | 0,85 | 2,50 | 0,00 | 400 |
| MID | medio | 0,00924 | 0 | 112,0 | 80 | 4,6 | 0,0 | 27,4 | 0,0 | 20,0 | 0,150 | 1,00 | 5,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 110,9 | 80 | 5,1 | -2,0 | 27,4 | 0,4 | 22,3 | 0,158 | 1,08 | 5,00 | 0,00 | 300 |
| MID | medio | 0,00924 | 30 | 111,5 | 80 | 5,7 | -1,6 | 27,4 | 0,0 | 24,8 | 0,179 | 1,06 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 60 | 115,1 | 80 | 7,1 | 0,6 | 27,4 | 0,0 | 30,9 | 0,233 | 0,98 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 90 | 118,5 | 80 | 8,9 | 2,2 | 27,4 | 0,0 | 38,7 | 0,288 | 0,91 | 5,00 | 0,00 | 400 |
| MID | medio | 0,00924 | 120 | 122,2 | 80 | 11,1 | 3,7 | 27,4 | 0,0 | 48,2 | 0,343 | 0,85 | 5,00 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 0 | 112,0 | 80 | 13,9 | 0,0 | 18,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 103,6 | 80 | 8,3 | -5,8 | 18,1 | 2,9 | 36,1 | 0,000 | 1,23 | 2,50 | 0,00 | 300 |
| HIGH | medio | 0,00924 | 30 | 97,5 | 80 | 5,0 | -6,6 | 18,1 | 0,9 | 21,7 | 0,000 | 1,26 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 60 | 95,4 | 80 | 1,8 | -4,6 | 18,1 | 0,0 | 7,8 | 0,000 | 1,18 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 90 | 96,5 | 80 | 0,8 | -2,4 | 18,1 | 0,0 | 3,3 | 0,010 | 1,09 | 2,50 | 0,00 | 400 |
| HIGH | medio | 0,00924 | 120 | 99,7 | 80 | 1,4 | 0,1 | 18,1 | 0,0 | 6,2 | 0,093 | 1,00 | 2,50 | 0,00 | 400 |

### H3: PRBC before haemostasis (L3, 2 units over 0-60 min, PPI)

**57m**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 124,0 | 80 | 0,0 | 0,0 | 44,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,00 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 121,1 | 80 | 0,6 | -4,5 | 44,0 | 1,1 | 2,5 | 0,250 | 1,18 | 2,00 | 0,50 | 0 |
| LOW | medio | 0,00924 | 30 | 117,6 | 80 | 0,9 | -8,2 | 44,0 | 1,0 | 3,9 | 0,112 | 1,33 | 2,00 | 1,00 | 0 |
| LOW | medio | 0,00924 | 60 | 111,6 | 80 | 0,6 | -13,8 | 44,0 | 0,8 | 2,5 | 0,000 | 1,55 | 0,25 | 2,00 | 0 |
| MID | medio | 0,00924 | 0 | 124,0 | 80 | 4,6 | 0,0 | 39,4 | 0,0 | 20,0 | 0,150 | 1,00 | 4,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 123,5 | 80 | 5,0 | -1,1 | 39,4 | 0,2 | 21,6 | 0,054 | 1,04 | 4,00 | 0,50 | 0 |
| MID | medio | 0,00924 | 30 | 122,2 | 80 | 4,1 | -2,1 | 39,4 | 0,8 | 17,8 | 0,000 | 1,08 | 4,00 | 1,00 | 0 |
| MID | medio | 0,00924 | 60 | 117,4 | 80 | 1,5 | -4,0 | 39,4 | 0,6 | 6,4 | 0,000 | 1,16 | 0,50 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 0 | 124,0 | 80 | 13,9 | 0,0 | 30,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,00 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 117,2 | 80 | 8,3 | -3,7 | 30,1 | 2,4 | 36,1 | 0,000 | 1,15 | 2,00 | 0,50 | 0 |
| HIGH | medio | 0,00924 | 30 | 110,2 | 80 | 5,0 | -6,8 | 30,1 | 1,8 | 21,7 | 0,000 | 1,27 | 2,00 | 1,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 101,2 | 80 | 1,8 | -11,8 | 30,1 | 1,0 | 7,8 | 0,000 | 1,47 | 0,25 | 2,00 | 0 |

**72f**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 0 | 112,0 | 80 | 0,0 | 0,0 | 32,0 | 0,0 | 0,0 | 0,400 | 1,00 | 2,00 | 0,00 | 0 |
| LOW | medio | 0,00924 | 15 | 110,2 | 80 | 0,6 | -3,0 | 32,0 | 0,7 | 2,6 | 0,286 | 1,12 | 2,00 | 0,50 | 0 |
| LOW | medio | 0,00924 | 30 | 108,1 | 80 | 1,0 | -5,5 | 32,0 | 0,6 | 4,4 | 0,180 | 1,22 | 2,00 | 1,00 | 0 |
| LOW | medio | 0,00924 | 60 | 104,6 | 80 | 1,3 | -9,2 | 32,0 | 0,5 | 5,5 | 0,000 | 1,37 | 0,25 | 2,00 | 0 |
| MID | medio | 0,00924 | 0 | 112,0 | 80 | 4,6 | 0,0 | 27,4 | 0,0 | 20,0 | 0,150 | 1,00 | 4,00 | 0,00 | 0 |
| MID | medio | 0,00924 | 15 | 111,8 | 80 | 5,0 | -0,7 | 27,4 | 0,1 | 21,6 | 0,062 | 1,03 | 4,00 | 0,50 | 0 |
| MID | medio | 0,00924 | 30 | 111,0 | 80 | 4,4 | -1,4 | 27,4 | 0,6 | 19,2 | 0,000 | 1,06 | 4,00 | 1,00 | 0 |
| MID | medio | 0,00924 | 60 | 106,8 | 80 | 1,6 | -2,7 | 27,4 | 0,5 | 6,9 | 0,000 | 1,11 | 0,50 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 0 | 112,0 | 80 | 13,9 | 0,0 | 18,1 | 0,0 | 60,0 | 0,000 | 1,00 | 2,00 | 0,00 | 0 |
| HIGH | medio | 0,00924 | 15 | 106,1 | 80 | 8,3 | -2,4 | 18,1 | 2,1 | 36,1 | 0,000 | 1,10 | 2,00 | 0,50 | 0 |
| HIGH | medio | 0,00924 | 30 | 100,2 | 80 | 5,0 | -4,5 | 18,1 | 1,5 | 21,7 | 0,000 | 1,18 | 2,00 | 1,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 92,9 | 80 | 1,8 | -7,8 | 18,1 | 0,8 | 7,8 | 0,000 | 1,31 | 0,25 | 2,00 | 0 |

### H4: definitive management: haemostasis at 60 and restored adequacy (L3, 60-120 min)

**57m**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 60 | 111,6 | 80 | 0,6 | -13,8 | 44,0 | 0,8 | 2,5 | 0,000 | 1,55 | 0,25 | 2,00 | 0 |
| LOW | medio | 0,00924 | 90 | 110,6 | 80 | 0,2 | -13,7 | 44,0 | 0,0 | 0,9 | 0,000 | 1,55 | 0,25 | 2,00 | 0 |
| LOW | medio | 0,00924 | 120 | 110,6 | 80 | 0,1 | -13,5 | 44,0 | 0,0 | 0,3 | 0,000 | 1,54 | 0,25 | 2,00 | 0 |
| MID | medio | 0,00924 | 60 | 117,4 | 80 | 1,5 | -4,0 | 39,4 | 0,6 | 6,4 | 0,000 | 1,16 | 0,50 | 2,00 | 0 |
| MID | medio | 0,00924 | 90 | 116,2 | 80 | 0,5 | -3,8 | 39,4 | 0,1 | 2,3 | 0,000 | 1,15 | 0,50 | 2,00 | 0 |
| MID | medio | 0,00924 | 120 | 116,0 | 80 | 0,2 | -3,6 | 39,4 | 0,0 | 0,8 | 0,000 | 1,14 | 0,50 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 101,2 | 80 | 1,8 | -11,8 | 30,1 | 1,0 | 7,8 | 0,000 | 1,47 | 0,25 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 90 | 99,3 | 80 | 0,7 | -11,6 | 30,1 | 0,1 | 2,8 | 0,000 | 1,46 | 0,25 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 120 | 99,0 | 80 | 0,2 | -11,4 | 30,1 | 0,0 | 1,0 | 0,000 | 1,46 | 0,25 | 2,00 | 0 |

**72f**

| Rep. | Intr. | Ganancia | Min | FC | intr. | deuda | presión | resto | retardo | D | déficit | gasto | sangrado | GR (U) | cristaloide (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | medio | 0,00924 | 60 | 104,6 | 80 | 1,3 | -9,2 | 32,0 | 0,5 | 5,5 | 0,000 | 1,37 | 0,25 | 2,00 | 0 |
| LOW | medio | 0,00924 | 90 | 103,4 | 80 | 0,5 | -9,1 | 32,0 | 0,1 | 2,0 | 0,000 | 1,36 | 0,25 | 2,00 | 0 |
| LOW | medio | 0,00924 | 120 | 103,2 | 80 | 0,2 | -9,0 | 32,0 | 0,0 | 0,7 | 0,000 | 1,36 | 0,25 | 2,00 | 0 |
| MID | medio | 0,00924 | 60 | 106,8 | 80 | 1,6 | -2,7 | 27,4 | 0,5 | 6,9 | 0,000 | 1,11 | 0,50 | 2,00 | 0 |
| MID | medio | 0,00924 | 90 | 105,5 | 80 | 0,6 | -2,5 | 27,4 | 0,1 | 2,5 | 0,000 | 1,10 | 0,50 | 2,00 | 0 |
| MID | medio | 0,00924 | 120 | 105,2 | 80 | 0,2 | -2,4 | 27,4 | 0,0 | 0,9 | 0,000 | 1,10 | 0,50 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 60 | 92,9 | 80 | 1,8 | -7,8 | 18,1 | 0,8 | 7,8 | 0,000 | 1,31 | 0,25 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 90 | 91,2 | 80 | 0,7 | -7,7 | 18,1 | 0,1 | 2,8 | 0,000 | 1,31 | 0,25 | 2,00 | 0 |
| HIGH | medio | 0,00924 | 120 | 90,8 | 80 | 0,2 | -7,6 | 18,1 | 0,0 | 1,0 | 0,000 | 1,30 | 0,25 | 2,00 | 0 |

<!-- /generado:trayectorias -->

Lectura: sin tratamiento (H1) la FC sube con la caída de la presión y con D, que sólo acumula mientras dura el
déficit. Con cristaloide (H2) baja mientras dura el bolo y vuelve a subir porque el sangrado sigue. Con glóbulos rojos
antes de la hemostasia (H3) baja de forma gradual y distinta por caso y por estado. Tras la hemostasia y la
adecuación restaurada (H4, T* = 60 en todos) la parte de la deuda se devuelve con τ_D (aquí 30 min) y llega casi a 0 a
los 120 min; la FC queda por encima de la intrínseca por el resto de llegada, menos lo que la presión recuperada
descarga.

## 8. Sondas sintéticas H5

<!-- generado:sondas -->
| Caso | Sonda | Se cumple | Lectura |
|---|---|---|---|
| 57m | τ_D 30 / 60 / 120 con D fija | sí | objetivos iguales en D = 0, 20, 40, 80 |
| 57m | más D, todo lo demás fijo | sí | FC 119,4 → 120,5 → 121,7 → 124,0 → 128,6 → 137,9 → 156,3 para D 0 → 5 → 10 → 20 → 40 → 80 → 160 |
| 57m | déficit agudo mayor (bomba) | sí | objetivo 1,76 → 1,86 → 1,96 → 2,06 → 2,16 → 2,26; Hb sola: 1,76 → 1,76 → 1,76 (Hb alone leaves the target unchanged: no acute oxygen-delivery term; a lower Hb reaches the drive only through D) |
| 57m | piso intrínseco | sí | FC 80,0, intrínseca 80 |
| 57m | glóbulos rojos sin sangrado (2 U en 60 min) | ver abajo | FC 124,0 / 110,7 / 99,0 a 0 / 30 / 60 |
| 57m | cristaloide 500 mL, bomba 1,0 | ver abajo | ΔFC a 30 min -23,3, presión relativa 1,84 |
| 57m | cristaloide 500 mL, bomba 0,7 | ver abajo | ΔFC a 30 min -13,6, presión relativa 1,17 |
| 57m | AESP / marcapasos | sí | AESP: sin frecuencia de pulso, impulso 0; marcapasos 70 lpm |
| 72f | τ_D 30 / 60 / 120 con D fija | sí | objetivos iguales en D = 0, 20, 40, 80 |
| 72f | más D, todo lo demás fijo | sí | FC 107,4 → 108,5 → 109,7 → 112,0 → 116,6 → 125,9 → 144,3 para D 0 → 5 → 10 → 20 → 40 → 80 → 160 |
| 72f | déficit agudo mayor (bomba) | sí | objetivo 1,28 → 1,38 → 1,48 → 1,58 → 1,68 → 1,78; Hb sola: 1,28 → 1,28 → 1,28 (Hb alone leaves the target unchanged: no acute oxygen-delivery term; a lower Hb reaches the drive only through D) |
| 72f | piso intrínseco | sí | FC 80,0, intrínseca 80 |
| 72f | glóbulos rojos sin sangrado (2 U en 60 min) | ver abajo | FC 112,0 / 103,0 / 94,8 a 0 / 30 / 60 |
| 72f | cristaloide 500 mL, bomba 1,0 | ver abajo | ΔFC a 30 min -16,1, presión relativa 1,55 |
| 72f | cristaloide 500 mL, bomba 0,7 | ver abajo | ΔFC a 30 min -8,4, presión relativa 1,00 |
| 72f | AESP / marcapasos | sí | AESP: sin frecuencia de pulso, impulso 0; marcapasos 70 lpm |

Una unidad no fija un descenso: sí (ΔFC de la primera unidad -13,3 / -9,0); la segunda puede diferir: sí (ΔFC -11,7 / -8,2); el cristaloide responde a la fisiología, no a su identidad: sí. Escala de D (g, ganancia, D0) → (c g, ganancia / c, c D0): FC igual sí (brecha máxima 0, 0 lpm).
<!-- /generado:sondas -->

## 9. Direcciones fisiológicas (P2I-2AE-9)

<!-- generado:invariantes -->
| # | Dirección | Resultado |
|---|---|---|
| 1 | increasing D with all else fixed never lowers HR | PASA |
| 2 | a larger acute critical deficit never lowers the sympathetic drive | PASA |
| 3 | restoring adequate oxygen delivery permits sympathetic recovery | PASA |
| 4 | HR recovery may lag because D persists | PASA |
| 5 | haemostasis alone does not force immediate HR normalization | PASA |
| 6 | one PRBC unit does not force a fixed HR decrement | PASA |
| 7 | the second unit's effect may differ by state | PASA |
| 8 | the crystalloid HR response depends on the resulting physiology, not on the fluid's identity | PASA |
| 9 | the intrinsic rate is the floor of the sinus rate | PASA |
| 10 | zero output / no pulse stays consistent with the rhythm and pulse semantics | PASA |

Corridas L3 con ganancia positiva: 73; con T* y D(T*) > 0: 73. Structural flags only, declared before any run. No bpm threshold is used: none is committed, and the magnitudes (including the absence of any saturation) are reported on the decision surface for the faculty.

| Bandera estructural | Corridas |
|---|---|
| ARRIVAL_NOT_REPRODUCED | 0 |
| DRIVE_FALLS_AGAINST_ITS_TARGET | 0 |
| HR_BELOW_INTRINSIC | 0 |
| INSTANT_NORMALIZATION_AT_HAEMOSTASIS | 0 |
| NEGATIVE_CONTRIBUTION | 0 |
| NO_DEBT_RECOVERY_AFTER_ADEQUACY | 0 |
<!-- /generado:invariantes -->

## 10. Superficie de decisión docente (P2I-2AE-5)

<!-- generado:superficie -->
no committed numeric HR band exists; nothing here is an envelope or a target. Intrínseca en su punto medio; cada celda: FC de LOW / MID / HIGH (lpm).

**57m**

| Hito (escenario, min) | 0,000667 | 0,00248 | 0,00924 | 0,0344 | 0,128 | 0 |
|---|---|---|---|---|---|---|
| arrival (L1, 0) | 124 / 124 / 124 | 124 / 124 / 124 | 124 / 124 / 124 | 124 / 124 / rech. | 124 / rech. / rech. | 124 / 124 / 124 |
| untreated_30 (L1, 30) | 127 / 127 / 127 | 128 / 127 / 127 | 129 / 128 / 128 | 133 / 131 / rech. | 148 / rech. / rech. | 127 / 126 / 127 |
| untreated_60 (L1, 60) | 131 / 129 / 131 | 131 / 130 / 131 | 134 / 132 / 134 | 143 / 141 / rech. | 176 / rech. / rech. | 130 / 129 / 130 |
| untreated_120 (L1, 120) | 138 / 134 / 138 | 139 / 136 / 141 | 145 / 143 / 151 | 166 / 167 / rech. | 244 / rech. / rech. | 137 / 134 / 137 |
| after_crystalloid_30 (L2, 30) | 116 / 122 / 114 | 116 / 122 / 112 | 117 / 123 / 106 | 119 / 125 / rech. | 129 / rech. / rech. | 116 / 122 / 114 |
| crystalloid_120 (L2, 120) | 130 / 130 / 123 | 131 / 131 / 121 | 135 / 136 / 111 | 149 / 155 / rech. | 201 / rech. / rech. | 130 / 130 / 124 |
| after_prbc_unit_1 (L3, 30) | 117 / 122 / 118 | 117 / 122 / 116 | 118 / 122 / 110 | 120 / 122 / rech. | 128 / rech. / rech. | 117 / 122 / 118 |
| after_prbc_unit_2_and_haemostasis (L3, 60) | 111 / 120 / 112 | 111 / 120 / 110 | 112 / 117 / 101 | 113 / 110 / rech. | 120 / rech. / rech. | 111 / 120 / 113 |
| after_haemostasis_90 (L3, 90) | 110 / 120 / 111 | 110 / 119 / 109 | 111 / 116 / 99 | 111 / 105 / rech. | 114 / rech. / rech. | 110 / 120 / 112 |
| restored_adequacy_120 (L3, 120) | 110 / 120 / 112 | 111 / 119 / 109 | 111 / 116 / 99 | 111 / 104 / rech. | 112 / rech. / rech. | 110 / 120 / 113 |
| persistent_critical_120 (L1, 120) | 138 / 134 / 138 | 139 / 136 / 141 | 145 / 143 / 151 | 166 / 167 / rech. | 244 / rech. / rech. | 137 / 134 / 137 |

Inicio de la adecuación restaurada (T*) a la ganancia ancla: LOW min 60, FC 112; MID min 60, FC 117; HIGH min 60, FC 101

**72f**

| Hito (escenario, min) | 0,000667 | 0,00248 | 0,00924 | 0,0344 | 0,128 | 0 |
|---|---|---|---|---|---|---|
| arrival (L1, 0) | 112 / 112 / 112 | 112 / 112 / 112 | 112 / 112 / 112 | 112 / 112 / rech. | 112 / rech. / rech. | 112 / 112 / 112 |
| untreated_30 (L1, 30) | 114 / 114 / 114 | 115 / 114 / 114 | 116 / 115 / 115 | 120 / 118 / rech. | 134 / rech. / rech. | 114 / 114 / 114 |
| untreated_60 (L1, 60) | 117 / 115 / 116 | 117 / 116 / 117 | 119 / 118 / 119 | 128 / 126 / rech. | 160 / rech. / rech. | 116 / 115 / 116 |
| untreated_120 (L1, 120) | 121 / 119 / 121 | 123 / 120 / 123 | 128 / 126 / 130 | 147 / 146 / rech. | 217 / rech. / rech. | 121 / 118 / 121 |
| after_crystalloid_30 (L2, 30) | 107 / 110 / 105 | 107 / 111 / 103 | 108 / 111 / 97 | 111 / 115 / rech. | 122 / rech. / rech. | 107 / 110 / 105 |
| crystalloid_120 (L2, 120) | 116 / 116 / 111 | 117 / 117 / 109 | 121 / 122 / 100 | 136 / 140 / rech. | 191 / rech. / rech. | 116 / 116 / 112 |
| after_prbc_unit_1 (L3, 30) | 107 / 111 / 108 | 107 / 111 / 106 | 108 / 111 / 100 | 111 / 112 / rech. | 120 / rech. / rech. | 107 / 111 / 108 |
| after_prbc_unit_2_and_haemostasis (L3, 60) | 103 / 109 / 104 | 104 / 109 / 101 | 105 / 107 / 93 | 108 / 99 / rech. | 121 / rech. / rech. | 103 / 110 / 105 |
| after_haemostasis_90 (L3, 90) | 103 / 109 / 103 | 103 / 108 / 101 | 103 / 106 / 91 | 105 / 95 / rech. | 110 / rech. / rech. | 103 / 109 / 104 |
| restored_adequacy_120 (L3, 120) | 103 / 109 / 103 | 103 / 108 / 101 | 103 / 105 / 91 | 104 / 93 / rech. | 106 / rech. / rech. | 103 / 110 / 104 |
| persistent_critical_120 (L1, 120) | 121 / 119 / 121 | 123 / 120 / 123 | 128 / 126 / 130 | 147 / 146 / rech. | 217 / rech. / rech. | 121 / 118 / 121 |

Inicio de la adecuación restaurada (T*) a la ganancia ancla: LOW min 60, FC 105; MID min 60, FC 107; HIGH min 60, FC 93

<!-- /generado:superficie -->

Lectura: la llegada se reproduce siempre. La pendiente sin tratamiento crece con la ganancia: a los 120 min, 134–151
lpm (57m) y 119–130 lpm (72f) con las tres ganancias menores, 166–167 / 146–147 con 0,0344, y 244 / 217 con 0,128 (sólo
LOW es coherente ahí). El núcleo no tiene techo de FC sinusal: esas magnitudes no se filtran porque no hay una banda
numérica aprobada. Tras el manejo definitivo la FC a los 120 min queda en 99–120 lpm (57m) y 91–109 lpm (72f) según el
representativo y la ganancia (sin contar la referencia 0).

## 11. Identificabilidad (P2I-2AE-10)

<!-- generado:identificabilidad -->
Available HR observations: the authored arrival HR of each case only. Exact structure: while the drive is positive, HR(t) = HR_arrival + 25 x [gain x (D(t) - D0) + pressure, hypoxaemia and glucose deviations] with the decay lag, so the intrinsic rate cancels and reaches HR only where the floor binds; the arrival HR fixes intrinsic + 25 x (S_rest + gain x D0) and S_rest is free and non-negative, so it constrains only the sum intrinsic + 25 x gain x D0 <= HR_arrival.

Intrínseca frente a ganancia: **NON_IDENTIFIABLE**. Pares comparados 173, brecha máxima de FC 5,68e-14 lpm; pares con el piso activo 1. every consistent (intrinsic, gain) pair reproduces the arrival HR exactly; above the floor the intrinsic rate cancels (the HR gaps between intrinsic levels at the same gain are rounding only); no post-arrival HR is authored to separate the gain.

| Dimensión | Estado | Soporte |
|---|---|---|
| d_scale | NON_IDENTIFIABLE | (g, gain, D0) -> (c g, gain / c, c D0) leaves HR unchanged |
| debt_to_sympathetic_gain | NON_IDENTIFIABLE | [0.0006667, 0.128] less the analytic rejections; only gain x D0 at arrival and gain x g over a run reach HR |
| intrinsic_sinus_rate | NON_IDENTIFIABLE | the band (60 / 80 / 100, capped at the arrival HR) less the analytic rejections |
| saturation_or_cap | NO_PARAMETER | the core has no HR cap or saturation |
| sympathetic_decay_tau_min | NOT_VARIED | 5 min (PROVISIONAL) |
| sympathetic_per_pressure_deficit | NOT_EVALUATED_PRESSURE_DOMAIN | 1.0 (PROVISIONAL), not varied: it sets how far restored pressure unloads the arrival rest |
<!-- /generado:identificabilidad -->

## 12. FC y FR (P2I-2AE-11)

<!-- generado:fr -->
derived.respiratory_rate reads lactate and W only; no drive, pulse rate or rhythm rate. ¿La FR lee la FC? no. FR idéntica entre ganancias e intrínsecas en las recorridas de validación: sí. D y lactato idénticos al registro P2I-2AD: sí. ¿El cambio de FC altera la FR? no. FR calibrada: no.
<!-- /generado:fr -->

## 13. Referencia heredada (P2I-2AE-12)

<!-- generado:legado -->
LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's HR at 0, 15, 30, 60, 90 and 120 min, read after the verdict, never by the gain range, a flag, an invariant, identifiability or the verdict.

| Caso | Escenario | 0 | 15 | 30 | 60 | 90 | 120 |
|---|---|---|---|---|---|---|---|
| 57m | L1 | 124–124 (124) | 125–136 (125) | 127–148 (126) | 129–176 (128) | 132–208 (131) | 134–244 (133) |
| 57m | L2 | 124–124 (124) | 113–124 (120) | 106–129 (121) | 105–149 (125) | 107–173 (127) | 111–201 (130) |
| 57m | L3 | 124–124 (124) | 117–127 (120) | 110–128 (117) | 101–120 (109) | 99–120 (100) | 99–120 (95) |
| 72f | L1 | 112–112 (112) | 113–123 (113) | 114–134 (114) | 115–160 (116) | 117–187 (119) | 119–217 (121) |
| 72f | L2 | 112–112 (112) | 104–115 (108) | 97–122 (109) | 95–142 (113) | 97–165 (115) | 100–191 (118) |
| 72f | L3 | 112–112 (112) | 106–117 (108) | 100–120 (105) | 93–121 (97) | 91–110 (88) | 91–109 (83) |

Cada celda: rango del núcleo sobre ganancias y representativos (intrínseca media) y, entre paréntesis, la FC del motor de familias. Sólo referencia.
<!-- /generado:legado -->

## 14. Veredicto (P2I-2AE-13)

<!-- generado:veredicto -->
**HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**

| Comprobación | Resultado |
|---|---|
| la reconstrucción de la FC coincide con el núcleo completo | sí |
| τ_D ya no llega a la FC con D fija | sí |
| cada FC informada es la suma de sus contribuciones | sí |
| descomposición de llegada coherente | sí |
| las diez direcciones se cumplen | sí |
| sin banderas estructurales | sí |
| soporte explícito | sí |
| nada aprobado | sí |

Regla congelada: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION when every check holds: (1) tau_D no longer reaches HR (the core's source and the fixed-D probe at every tau_D level); (2) the contributors are explicit (the audit, and every reported minute's contributions add up to its HR within 1e-9); (3) the arrival decomposition is coherent (every consistent pair reproduces the arrival HR exactly, the analytic rejections are exactly the pairs the core refuses, and each case keeps a consistent pair with a positive gain at every arrival-debt level); (4) the ten directional invariants pass; (5) no structural patient-like flag in any read run; (6) the support is explicit (gain range and identifiability table); (7) nothing is approved (no value selected; the default profile unchanged); and the post-processing agrees with the full core. Otherwise HR_STRUCTURE_NOT_READY with the first blocker. No numeric HR band is required.

Siguiente paso: Next step (not started; needs its own authorization): a small faculty HR numeric-calibration package (intrinsic rate, debt_to_sympathetic_gain, whether a sinus-rate ceiling or saturation is wanted, and HR readings at the decision-surface landmarks). Pressure and vascular tone follow HR; not started.
<!-- /generado:veredicto -->

## 15. Hallazgos estructurales para el paquete numérico (no son bloqueos de esta regla)

1. **El resto de llegada no se resuelve con la oxigenación.** S_rest es constante. Sólo baja la FC por debajo de él el
   término de presión, relativo a la llegada (`sympathetic_per_pressure_deficit` 1,0, PROVISIONAL, del dominio de la
   presión). Por eso, tras la hemostasia y la adecuación restaurada, la FC queda en 99–120 lpm (57m) y 91–109 lpm (72f)
   a los 120 min, con D casi devuelta. Dentro de 120 min eso no es una contradicción con lo comprometido; sí lo sería
   si se mantuviera indefinidamente. Si la docencia quiere que la parte de shock o hipoperfusión de llegada se
   resuelva con la entrega restaurada, hace falta un término agudo de entrega o una referencia absoluta de presión.
   Cualquiera de las dos necesita su propio rango: es la condición de STOP de P2I-2AE-3, y aquí no se inventa.
2. **Sin techo ni saturación.** Con D creciente y sin tratamiento, la FC crece sin límite. En el extremo superior del
   rango de la ganancia llega a 244 / 217 lpm a los 120 min. El rango se construyó sólo con la descomposición de
   llegada; el paquete numérico debe decidir si hace falta un techo sinusal o una saturación, y estrechar la ganancia.
3. **No identificabilidad.** La intrínseca y la ganancia no se separan con las observaciones autorizadas (sólo la FC
   de llegada). Por encima del piso la intrínseca se cancela: misma FC con 60 / 80 / 100 a igual ganancia, hasta el
   redondeo (5,7e-14 lpm). Sólo la suma intrínseca + 25 × ganancia × D0 queda acotada por la FC de llegada.
4. **Región histórica.** 108 candidatos P2F ya no son llegadas coherentes a la ganancia por defecto. La región escrita
   de P2F (1054) y sus 163 rechazos quedan como historia. El recálculo completo de la región de
   `lactate_constraints.region` (histórico, su tubería está congelada) no se puede hacer para esos 108 con el núcleo
   vigente; no se corrió ni se cambió.
5. **Escala de D del rango (revisión, F3).** Los dos extremos del rango de la ganancia salen de la banda de deuda de
   llegada (20 y 60). La regla de no negatividad necesita una escala de D0, y esa banda es la vigente. Pero no está en
   la lista de entradas docentes, y su 60 se justificó como un estado estacionario con τ_D 60 (la misma observación que
   TD-92(2) para k). La docencia debe aceptar esa escala o reemplazarla (TD-93(6)). La docstring de `gain_design`
   («never read tau_D») vale para la regla: el bloque posterior a `old =` lee los puntos de τ_D del registro sólo para
   listar las ganancias del rango viejo.

## 16. Revisión adversarial

Una revisión independiente, de sólo lectura, sin BLOCKER:
- **F1, MAJOR (ejecutable), corregida.** Excluir las 108 llegadas rechazadas cambiaba los resúmenes históricos de
  lactato, presión y FR del paquete P2G y del corte P2I-1 (por ejemplo, 649 → 595 corridas). Ahora esas llegadas se
  leen sin impulso por deuda, que no llega a esas lecturas, y sólo la FC de P2G las deja fuera. Comprobado: el corte
  P2I-1 y las secciones de lactato, presión y FR de P2G son idénticos a los de `e0dffa8`. En el resto de P2G sólo
  cambian la FC y un redondeo de 1 ulp en la FC final de la tabla de volumen.
  El recongelamiento no tocó el diseño: `hr_structure.py` y el núcleo siguen byte a byte en `6052ffb`. La evaluación
  se volvió a correr e igualó la primera salvo el digest (`398ab817…` → `1b65d303…`).
- **F2, MAJOR (latente), declarada (TD-93(5)) y fijada por una prueba.** Una llegada no sinusal o con betabloqueo
  completo y D0 > 0 se rechaza siempre, porque la FC no revela el impulso. No afecta a los casos GI.
- **F3, MAJOR (metodológica), declarada:** §15.5 y TD-93(6).
- **F4, MINOR.** Varias comprobaciones son guardas estructurales que no pueden fallar por construcción:
  - `contributors_explicit` (el retardo es el residuo);
  - `DRIVE_FALLS_AGAINST_ITS_TARGET`;
  - `NEGATIVE_CONTRIBUTION` (las desviaciones de presión, SpO2 y glucosa pueden ser negativas por diseño);
  - la igualdad exacta de `INSTANT_NORMALIZATION_AT_HAEMOSTASIS`;
  - `nothing_approved` y `support_explicit`.

  El veredicto descansa en la factorización exacta, la sonda de τ_D con D fija, la coherencia de llegada y los
  invariantes 1, 2, 3, 9 y 10. Para el invariante 5, los datos muestran esto a los 90 min, 30 min después de la
  hemostasia:
  - con la intrínseca media, la FC sigue al menos 11 lpm sobre ella en todas las corridas leídas (§10);
  - con la intrínseca superior (100), 57m HIGH ya está en 100,003 lpm, prácticamente en el piso. Es el único par del
    plano donde el piso llega a activarse (§11).

  Al minuto siguiente de la hemostasia, el menor margen sobre la intrínseca en todo el plano leído es 0,99 lpm (72f
  HIGH, intrínseca 60, ganancia 0,0344). En el minuto 60 ya era 1,2 lpm: la FC llegó casi al piso por la reposición
  previa, no por la hemostasia. Esto es una sonda posterior a la revisión, no parte del registro. L3 no es «hemostasia
  sola»: incluye los glóbulos rojos.
- **F5, MINOR.** `sympathetic_per_debt` sigue en el registro y en las tablas históricas de P2G. Sus filas son
  idénticas por construcción, y el documento P2G ya lo anota (TD-93(7)).
- **F6, NIT, corregidos:**
  - 91–109 lpm en 72f, sin la referencia 0;
  - el orden de las secciones;
  - el alcance de la validación: en el extremo superior de la ganancia (0,128) sólo LOW (D0 = 0) es coherente y se
    compara; MID y HIGH se rechazan analíticamente en el núcleo y en la reconstrucción a la vez;
  - la nota de P2G lee del registro los niveles rechazados.
