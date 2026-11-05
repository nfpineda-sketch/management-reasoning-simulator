# P2T-5 · Enlace común mínimo hipoventilación → oxigenación (sombra, apagado por defecto)

Paquete estructural común, en sombra y apagado por defecto. No migra la familia de opioides. Rama
`phase-2-clinical-core-shadow`; base `2c88e0d` (P2T-3 READY y P2T-4 = A, `MINIMAL_ALVEOLAR_GAS_LINK_SUPPORTED`,
aceptados y cerrados).

- **Cambio común:** un campo nuevo del perfil, `respiratory_quotient`, UNSET (`None`) por defecto, con sus guardas. Se
  agregan también la relación de disociación estándar, su inversa exacta, la referencia de PaCO2 de llegada del modelo y
  el enlace relativo. `_perfusion` gana una sola inserción, que reemplaza la SpO2 que ya producen la regla de FiO2 y el
  camino de G.
- **Análisis:** `clinical_core/oxygenation_link.py`, congelado antes de la única evaluación.
- **Registro:** `docs/revision/P2T5_oxygenation_link.json`. Este documento se genera desde el registro
  (`clinical_core/oxygenation_link_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- **Enlace:** `SYMMETRIC_RELATIVE_ALVEOLAR_LINK` y `MINIMAL_RELATIVE_ALVEOLAR_GAS_LINK`.
  - ΔPAO2 = −ΔPaCO2 / R.
  - ΔPaCO2 se mide respecto de la PaCO2 de llegada **derivada por el modelo** (el camino mecánica / W de P2S-2), nunca
    respecto de la PaCO2 autorada como ancla oculta.
  - Patm, PH2O, la PAO2 absoluta y la altitud no son entradas activas: se cancelan.
- **Composición con G** (decisión docente durante el encargo):
  - `FULL_RELATIVE_ALVEOLAR_TRANSMISSION = ACCEPTED`: PaO2_final = ODC⁻¹(SpO2_base) − ΔPaCO2/R, y
    SpO2_final = ODC(PaO2_final);
  - `RETAINED_G_AS_ALVEOLAR_TRANSMISSION = REJECTED`: el desplazamiento no se multiplica por `oxygen_response_retained(G)`;
  - O5 revisado: con el mismo cambio de PaCO2, peor G nunca mejora la SpO2 final; la magnitud del cambio puede crecer, por
    la no linealidad de la curva.
- **R:** `None` = enlace apagado. Si se declara, debe ser finito y positivo. R = 0,8 sólo como
  `SYNTHETIC_PHYSIOLOGIC_REFERENCE` en las sondas; no hay valor clínico aprobado.
- **Guardas:**
  - el enlace con la mecánica apagada se rechaza;
  - el impulso hipoxémico sigue UNSET y se rechaza junto con el enlace (`HYPOXEMIC_FEEDBACK_LOOP_DEFERRED`).
- **PaO2:** sólo latente, sin estado.
- **Curva de disociación:** la relación estándar (Severinghaus), sin parámetro ajustado.
  - Sin techo arbitrario de PaO2 ni épsilon en SpO2 = 100 (`ODC_PLATEAU_IDENTIFIABILITY_DEBT`).
- **FiO2:** regla sin cambios (`FIO2_RESPONSE_MAGNITUDE_DEBT`).
- **Sin parámetros nuevos de otro tipo:** ni tau, ni ganancia, ni frontera de rechazo para la hipercapnia clínicamente
  plausible.

## 2. Auditoría del cambio

<!-- generado:auditoria -->
- Funciones nuevas en `derived.py`: `arrival_paco2_reference`, `hypoventilation_link_active`, `oxygen_saturation_from_pao2`, `pao2_from_oxygen_saturation`, `ventilated_oxygenation`; cambiadas: `__post_init__`, `_perfusion`; campo nuevo del perfil: respiratory_quotient.
- El enlace lee: `arrival_paco2_reference`, `oxygen_saturation_from_pao2`, `pao2_from_oxygen_saturation`, `respiration`, `respiratory_quotient`; no lee `oxygen_response_retained`, FiO2 ni G.
- Constantes numéricas: sólo las de la curva estándar y 0 / 1 (`arrival_paco2_reference` [1.0]; `oxygen_saturation_from_pao2` [0.0, 1.0, 3, 100.0, 150.0, 23400.0]; `pao2_from_oxygen_saturation` [0.0, 1.0, 2.0, 3.0, 4.0, 50.0, 100.0, 23400.0, 125000.0]; `ventilated_oxygenation` [0.0]); sin Patm, PH2O ni altitud (sí).
- `_perfusion` llama al enlace: sí. Pasa: sí.
<!-- /generado:auditoria -->

## 3. Curva de disociación y su inversa

<!-- generado:curva -->
- Severinghaus (1979), sin parámetro ajustado: PaO2 → SpO2 1.0 → 0,64, 10.0 → 9,65, 120.0 → 98,68, 30.0 → 57,38, 300.0 → 99,91, 45.0 → 80,71, 57.0 → 89,22, 600.0 → 99,99, 80.0 → 95,73.
- Inversa exacta (Cardano): SpO2 → PaO2 0.5 → 0,78, 20.0 → 15,27, 50.0 → 26,86, 80.0 → 44,30, 89.0 → 56,55, 95.0 → 75,67, 99.0 → 131,94, 99.9 → 285,76; ida y vuelta, error máximo 2.1e-14.
- Crecientes: directa sí, inversa sí; límites: PaO2 0 → 0, PaO2 ∞ → 100, SpO2 0 → 0, SpO2 100 → inf (ODC_PLATEAU_IDENTIFIABILITY_DEBT).
- Pares autorados PaO2 / SpO2 de 31 variantes: brecha máxima con la curva 1,71 puntos (pulmonary_edema_75f); sólo coherencia, no se ajusta nada.
- Pasa: sí.
<!-- /generado:curva -->

## 4. retained(G): semántica y rechazo como transmisión

<!-- generado:retenida -->
- retained(G) en G = −1, 0, 0,5, 1, 2: 1,000, 1,000, 0,800, 0,667, 0,500; 1 hasta la llegada sí, no creciente sí.
- Semántica: the share of the FiO2 benefit the existing G path keeps (P2O-1); stays in that path.
- Como transmisión alveolar: REJECTED (faculty): a retained(G) x dPAO2 cross-term can make a worse G raise SpO2 when PaCO2 rises (shown before implementation); el enlace la lee: no.
- Pasa: sí.
<!-- /generado:retenida -->

## 5. Sondas O1–O11 y guardas

Paciente de sonda: el de P2S-2 (mecánica encendida), con la referencia sintética de intercambio gaseoso de P2O-1 y
R = 0,8. Se fija el estado y se cambia la eficiencia mecánica (0,7 / 1 / 1,3 respecto de la llegada), la G y la FiO2.

<!-- generado:sondas -->
- O1 (apagado = camino previo, el enlace nunca se llama): sí (0 llamadas).
- O2 (llegada exacta con el enlace encendido; referencia = PaCO2 de llegada del modelo): sí.
- O3 (G neutra, PaCO2 40,00 → 57,14 → SpO2 97,00 → 93,58): sí.
- O4 (PaCO2 40,00 → 30,77 → SpO2 97,00 → 97,88): sí.
- O5 (con el mismo cambio de PaCO2, peor G nunca sube la SpO2 final): sí; with the same PaCO2 change a worse G never raises the final SpO2; the size of the SpO2 change need not shrink (a lower PaO2 sits on a steeper part of the curve).

| E relativa | G 0 | G 0,5 | G 1 | G 2 |
|---|---|---|---|---|
| 0.7 | 93,58 | 86,18 | 77,87 | 60,69 |
| 1.0 | 97,00 | 94,50 | 92,00 | 87,00 |
| 1.3 | 97,88 | 96,36 | 94,94 | 92,24 |

- O6 (peor G nunca mejora, también analítico en ΔPaCO2 −10…30): sí.
- O7 (más FiO2 nunca empeora): sí.
- O8 (sin escritura hacia W, FR, mecánica, impulso ni carga ácida): sí; no direct write; a lower SpO2 can still reach the acid burden through the existing delivery -> deficit -> acid path, one minute later, only when delivery falls below the extraction reserve.
- O9 (G no cambia la PaCO2): sí.
- O10 (sólo SpO2 y lo que la lee): sí; derivados movidos consciousness_level, delivery_rel, spo2; estado movido aux.sympathetic_drive; SpO2 -> delivery (D, lactate, acid burden one minute later when delivery falls below the extraction reserve); SpO2 -> the sympathetic target's hypoxaemia term (HR); SpO2 -> the ADOPTED consciousness ladder. No direct write to V, T, P, R, L, D, G, W or lactate.
- O11 (PaO2 latente, sin estado): sí.
- Guardas: mecánica apagada rechazada sí, perfil TEP comprometido rechazado sí, impulso hipoxémico rechazado sí, R no positivo rechazado sí, apnea sin resolver (APNOEA_BOUNDARY_UNRESOLVED) sí.
<!-- /generado:sondas -->

## 6. Depresión central tipo opioide (sintética)

<!-- generado:opioide -->
- FIXED_STATE_COMPARATIVE_PROBE, sintético (disponibilidad central 0.5 frente a 1.0, G 0): FR 8,0 frente a 16,0, W 0,500 frente a 1,000, PaCO2 80,0 frente a 40,0, SpO2 75,69 frente a 97,00.
- Mejora integrada en el núcleo (alivio mecánico): PaCO2 40,00 → 29,68, SpO2 97,00 → 97,96.
- CENTRAL_AVAILABILITY_IS_A_PROFILE_CONSTANT: depression / reversal over time needs an availability writer (opioid migration).
- Pasa: sí.
<!-- /generado:opioide -->

## 7. Asma 49m y 24f

Testigo medio de P2T-3 (k, ρ, g_FR y d), con R = 0,8 agregado; escritor `AirwayObstruction` de P2S-3 y G directa
sintética de P2T-3.

<!-- generado:asma -->
- **asthma_49m:** llegada exacta sí; obstrucción sin G: PaCO2 51,00 → 56,37, SpO2 con enlace 89,00 → 84,87 (sin enlace 89,00 → 89,00); con G directa sintética además: 83,99 (sólo G 88,40, sólo mecánica 84,87); composición serial sí; alivio: PaCO2 51,00 → 37,84, SpO2 89,00 → 94,47.
- **asthma_24f:** llegada exacta sí; obstrucción sin G: PaCO2 31,00 → 34,98, SpO2 con enlace 90,00 → 87,43 (sin enlace 90,00 → 90,00); con G directa sintética además: 86,63 (sólo G 89,00, sólo mecánica 87,43); composición serial sí; alivio: PaCO2 31,00 → 23,48, SpO2 90,00 → 93,29.
- Pasa: sí.
<!-- /generado:asma -->

## 8. TEP: ortogonalidad de G

<!-- generado:tep -->
- STRUCTURAL_PROBE (mechanics on); el perfil comprometido (mecánica apagada) rechaza el enlace: sí.
- G 0,00 → 0,75; G no mueve la PaCO2 en ningún estado: sí; composición serial sí.
- SpO2 con enlace 88,00 → 82,74, sin enlace 88,00 → 84,25; curso sin G con enlace 86,69.
- PaCO2 al minuto final: G con enlace 29,46, G sin enlace 29,58, sin G con enlace 29,75, sin G sin enlace 29,85; the committed mapping's arrival acid burden clears, the drive and RR fall and PaCO2 rises a little; with the link on, that model PaCO2 rise lowers SpO2 too (the plain course shows it without G); ruta indirecta existente: delivery -> deficit -> acid burden -> drive (minute-lagged; predates P2T-5) (compensadora sí).
- Pasa: sí.
<!-- /generado:tep -->

## 9. Edema: composición sin doble conteo

<!-- generado:edema -->
- STRUCTURAL_PROBE (mechanics on); llegada 81,0; curso sin escritores: PaCO2 51,47, SpO2 77,71.
- Sólo L: L 0,266, G 0,266, PaCO2 49,00 → 51,47 (igual al curso sin escritores sí), SpO2 76,11.
- Sólo mecánica: L y G 0 sí, PaCO2 49,00 → 58,04, SpO2 65,50.
- Ambos: L 0,266, G 0,266, PaCO2 58,04, SpO2 62,99; composición serial sin doble conteo sí.
- Pasa: sí.
<!-- /generado:edema -->

## 10. Enmascaramiento por FiO2 y meseta

<!-- generado:fio2 -->
| FiO2 | SpO2 base | SpO2 hipoventilando (E × 0,7) | Caída |
|---|---|---|---|
| 0.21 | 97,00 | 93,58 | 3,42 |
| 0.25 | 98,20 | 96,59 | 1,61 |
| 0.5 | 100,00 | 100,00 | 0,00 |
| 1.0 | 100,00 | 100,00 | 0,00 |

- FIO2_RESPONSE_MAGNITUDE_DEBT: the FiO2 rule is unchanged; regla de FiO2 intacta: sí.
- ODC_PLATEAU_IDENTIFIABILITY_DEBT: a SpO2_base of 100 gives an unresolved PaO2 (+inf) and no change.
- Pasa: sí.
<!-- /generado:fio2 -->

## 11. Aguas abajo: DO2 / D / lactato, FC, conciencia, ácido-base

<!-- generado:aguas_abajo -->
- Paciente de sonda, empeoramiento mecánico sintético 0.993/min por 60 min (PaCO2 61,0), con el enlace frente a sin él: SpO2 92,19 frente a 97,00; DO2 relativa 0,950 frente a 1,000; D 0,000 frente a 0,000; lactato 1,000 frente a 1,000; FC 80,9 frente a 80,0; conciencia 0 frente a 0.
- TEP (mecánica encendida), empeoramiento mecánico sintético 0.998/min por 60 min (PaCO2 33,3), con el enlace frente a sin él: SpO2 83,46 frente a 88,00; DO2 relativa 0,942 frente a 1,000; D 30,379 frente a 29,000; lactato 3,594 frente a 3,588; FC 101,2 frente a 97,8; conciencia 1 frente a 0.
- FC: existing: the sympathetic target's hypoxaemia term (relative to arrival); no new HR reader.
- Conciencia: CONSCIOUSNESS_INTEGRATION_DEBT; HYPERCAPNIA_SIGNAL_STRUCTURALLY_SUPPORTED_BOUNDS_NOT_IDENTIFIABLE; the ADOPTED ladder reads SpO2 only: a link-lowered SpO2 can move it; no CO2 narcosis is encoded.
- Ácido-base: respiration (W, PaCO2, pH, HCO3, acid burden, drive) never reads the link (O8).
- Bucle hipoxémico: HYPOXEMIC_FEEDBACK_LOOP_DEFERRED: the link refuses the hypoxaemic drive.
- Pasa: sí.
<!-- /generado:aguas_abajo -->

## 12. Parámetros

<!-- generado:parametros -->
- R en los perfiles comprometidos: None en todos sí (acs, asthma, asthma_p2t3, default, edema, gi, p2p2_probe, p2s2_probe, pe).
- Registro: provisional — UNSET (P2T-5): the respiratory quotient of the common relative alveolar link (dPAO2 = -dPaCO2 / R, from the model's own arrival PaCO2, full transmission to a latent PaO2 and the standard dissociation relation); None by default (the link off); needs the mechanics candidate; refuses the hypoxaemic drive; 0.8 only as a SYNTHETIC_PHYSIOLOGIC_REFERENCE in probes; not approved.
- R sintético 0.8 sólo como SYNTHETIC_PHYSIOLOGIC_REFERENCE; campos nuevos del perfil: respiratory_quotient.
- Siguen sin valor: respiratory_quotient (clinical value), hypoxaemic drive, FiO2 magnitude (unchanged), G parameters (unchanged), no tau / transmission / hypoventilation gain.
- Pasa: sí.
<!-- /generado:parametros -->

## 13. No regresión

<!-- generado:no_regresion -->
- Registro de P2T-3 reproducido sobre su árbol: sí (anida P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, GI, SCA, edema, TEP y P2P-2); intacto sí; su veredicto ASTHMA_SHADOW_MIGRATION_READY.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 14. Prueba contra el árbol de P2T-3

<!-- generado:prueba -->
- Archivos revertidos a los de P2T-3: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/lactate_slice.py` sí.
- Archivos comunes fijados por hash: 124, intactos sí.
- Vista de P2T-3: digest sí, su prueba sí, registro sí.
<!-- /generado:prueba -->

## 15. Veredicto

<!-- generado:veredicto -->
- sí — the relative symmetric alveolar link works (O3, O4) with full transmission and no new parameter (audit)
- sí — no new PaO2 state is required (O11) and the dissociation relation is the standard one, monotone, unfitted
- sí — arrival exact with the link on (O2) and the default off exact (O1)
- sí — G and hypoventilation compose independently and monotonically (O5, O6, O7, O9; asthma serial; edema)
- sí — opioid-like hypoventilation lowers SpO2 without G and better ventilation raises it (opioid probe)
- sí — asthma mixed physiology is representable (49m and 24f probes)
- sí — PE's G physiology stays orthogonal and edema avoids double counting
- sí — no feedback into PaCO2 or the drive (O8, the hypoxaemic loop refused) and the guards hold
- sí — the downstream SpO2 -> delivery -> D / lactate / HR directions hold through existing paths
- sí — the parameters stay UNSET clinically (R None everywhere committed; 0.8 synthetic only)
- sí — non-regression: P2T-3's record on its tree, every other file proven

**Veredicto: COMMON_HYPOVENTILATION_OXYGENATION_LINK_READY**
<!-- /generado:veredicto -->

## 16. Lectura

### 16.1 Qué deja este paquete

- Un enlace común hipoventilación → oxigenación, apagado por defecto (R = `None` en todo perfil comprometido).
  - Declarado, mueve la SpO2 por el cambio de PaCO2 respecto de la llegada del propio modelo, con transmisión completa a
    una PaO2 latente y la curva estándar.
  - Es exacto a la llegada y simétrico, sin parámetro nuevo salvo R.
- El enlace compone en serie con el camino de G (L → G y G directa) y con la FiO2. Con el mismo cambio de PaCO2, peor G
  nunca mejora la SpO2 final (O5 revisado).
- Lo que se puede representar en sombra:
  - la hipoventilación mecánica (asma);
  - la hipoventilación por caída del impulso, tanto en el núcleo integrado (curso de TEP sin escritores) como en la
    comparación de estado fijo de tipo opioide;
  - la composición con la G directa (TEP) y con L (edema).
- La regla congelada da `COMMON_HYPOVENTILATION_OXYGENATION_LINK_READY`. El criterio 8 se cumple como «sin escritura
  directa»: ver M1 abajo.

### 16.2 Revisión adversarial

Una sola revisión, de sólo lectura, sobre `ba9c64a`. Ningún hallazgo alto; 2 medios y 2 bajos, todos confirmados con
sondas propias. No se cambió ninguna fuente congelada y no se volvió a congelar: los refuerzos son sólo de pruebas
(`test_review_hardening_m1_…`, `_m2_…`, `_b1_…`, `_b2_…`).

- **M1 (media). Bucle metabólico cerrado.** Cuando la entrega cae bajo la reserva de extracción, la SpO2 que baja el
  enlace llega a la carga ácida, al impulso y a la FR por la ruta existente (un minuto de desfase), y de ahí otra vez a
  la PaCO2 y a la SpO2.
  - La ruta es previa, pero el bucle cerrado sólo existe con el enlace.
  - Es compensador y no oscila. Con SpO2 de llegada 85 y empeoramiento mecánico 0,985/min, a los 60 min: carga ácida
    2,66 frente a 0, FR 20,8 frente a 16 y PaCO2 76 frente a 99 sin el enlace.
  - El texto del criterio 8 («no feedback into PaCO2 or the drive») y la nota ácido-base lo exageran: O8 se probó en un
    paciente que no cruza la reserva.
  - **Decisión docente pendiente:** aceptarlo o diferirlo junto con `HYPOXEMIC_FEEDBACK_LOOP_DEFERRED`.
- **M2 (media). Suelo silencioso de la PaO2 latente.** Con transmisión completa, la PaO2 latente llega a 0 cuando
  ΔPaCO2 ≥ R × PaO2_latente. Desde SpO2 85, eso ocurre con +40 mmHg; desde 97, con +72.
  - La SpO2 queda entonces en 0 (dominio de la curva), sin `UnresolvedBoundary`, a diferencia de la apnea.
  - Simétrico: una SpO2_base ya en el piso 0 del camino de G se lee como PaO2 0, y la hiperventilación la levanta sea
    cual sea la G.
  - La monotonía se mantiene.
  - **Decisión docente pendiente:** frontera sin resolver, piso declarado u otra regla.
- **B1 (baja).** Cambios de PaCO2 de unos pocos ulp mueven la SpO2 unos pocos ulp en cualquier dirección (redondeo de la
  ida y vuelta, ≤ 2e-14). La dirección estricta vale más allá del redondeo; el «never» del docstring es exacto sólo ahí.
- **B2 (baja). Poder discriminante.**
  - O2, O9 y la parte «mismo estado» de O8 son confirmaciones estructurales que no pueden fallar.
  - La SpO2 deprimida de la sonda opioide sale de la aritmética del enlace, no de un curso del núcleo. Una depresión
    declarada en el perfil se absorbe en la referencia de llegada.
  - La «composición serial» de `_decomposed` repite el código. El doble conteo lo descartan `l_moves_no_paco2` y
    `mechanics_moves_no_g`.
  - Refuerzo añadido: hipoventilación por caída del impulso en el núcleo integrado, sin G y con la mecánica constante.

### 16.3 Limitaciones y deudas (TD-123)

- R sin valor clínico; 0,8 sólo `SYNTHETIC_PHYSIOLOGIC_REFERENCE`.
- `ODC_PLATEAU_IDENTIFIABILITY_DEBT` (meseta en 100 y piso en 0), `FIO2_RESPONSE_MAGNITUDE_DEBT` (en el paciente de
  sonda, la regla lineal satura a FiO2 0,5) y `APNOEA_BOUNDARY_UNRESOLVED`.
- `CENTRAL_AVAILABILITY_STATE_DEFERRED`: la disponibilidad central es una constante del perfil, así que la depresión y la
  reversión en el tiempo necesitan el escritor de la migración opioide.
- `HYPOXEMIC_FEEDBACK_LOOP_DEFERRED` y el bucle metabólico de M1; el suelo de M2.
- `CONSCIOUSNESS_INTEGRATION_DEBT` y `HYPERCAPNIA_SIGNAL_STRUCTURALLY_SUPPORTED_BOUNDS_NOT_IDENTIFIABLE`: la escalera
  ADOPTED lee sólo SpO2, de modo que una SpO2 bajada por el enlace puede moverla, pero no hay narcosis por CO2.
- TEP y edema sólo como sondas estructurales con la mecánica encendida: sus perfiles comprometidos la tienen apagada y
  rechazan el enlace.
- Pares autorados PaO2 / SpO2: brecha máxima con la curva estándar de 1,7 puntos. Sólo coherencia; no se ajustó nada.

### 16.4 Orden estratégico (no se inicia nada)

1. **Migración opioide**, precedida de una auditoría de sólo lectura (recomendada como próximo paquete). Debe cubrir:
   - el escritor de la disponibilidad central (`CENTRAL_AVAILABILITY_STATE_DEFERRED`);
   - la reversión con naloxona;
   - la llegada de 35m y 67f con la mecánica encendida (PaO2 45 y 50, PaCO2 69 y 61);
   - las decisiones M1 y M2;
   - qué conciencia se puede leer.
2. **Preparación de conciencia** (hipercapnia y narcosis): señal sostenida por la estructura, pero con cotas no
   identificables.
3. **Auditoría de `systemic_stress`**: residual de FC del SCA, β-agonista y anafilaxia.
4. **Otra familia**, con la mecánica encendida.
