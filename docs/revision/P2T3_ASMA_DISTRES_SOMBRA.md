# P2T-3 · Migración en sombra del asma con la región común de distrés respiratorio

Reintento de la migración del asma en sombra. Reemplaza a P2S-3 hacia adelante, sin reescribir su historia: P2S-3 sigue
siendo `ASTHMA_SHADOW_MIGRATION_NOT_READY — COMMON_DRIVE_GAP`, con `P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT`. Rama
`phase-2-clinical-core-shadow`; base `a2e6227` (P2T-1A y P2T-2 aceptados y cerrados).

- **Sin fisiología común nueva:** se usan sin cambios la mecánica de P2S-2, la arquitectura de distrés de P2T-1 y P2T-1A
  y el escritor `AirwayObstruction` de P2S-3. Sólo las dos tuplas de registro ganan las entradas del paquete.
- **Análisis:** `clinical_core/asthma_distress_migration.py`, congelado antes de la única evaluación.
- **Registro:** `docs/revision/P2T3_asthma_distress_migration.json`. Este documento se genera desde el registro
  (`clinical_core/asthma_distress_migration_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- **Escala:** `d(asthma_49m) = 1`, `ANALYTIC_NORMALIZATION_ONLY`. No es un valor clínico, ni una escala universal, ni
  «distrés severo = 1», ni un mapeo del WOB. Toda conclusión se muestra invariante ante d → λ·d y ganancias → ganancias/λ.
- **Ganancia ácido → FR:** k ∈ [1, 2], en los puntos de soporte de P2K-4 dentro de ese intervalo (1, √2, 2).
  `P2T3_ANALYSIS_SUBREGION_OF_EXISTING_ACID_UNCERTAINTY`; el parámetro sigue PROVISIONAL / POORLY_IDENTIFIED.
- **ρ = g_FC / g_FR:** se lleva como intervalo condicional ρ_permitido(k), nunca como un punto.
- **TEP 33f:** su FC es sólo evidencia de compatibilidad / cota superior (dolor pleurítico, activación no modelada). Las
  restricciones de FC más limpias son el edema 58m y el TEP 61m, descontados los términos de shock existentes.
- **L1:** `ACCUMULATED_FLOAT_CANCELLATION_DEBT`, falla cerrado. Un escritor que vuelve a un objetivo escribe la diferencia
  exacta respecto del estado actual. No se amplía la tolerancia de P2T-1A.
- **Lo que no se toca:**
  - impulso hipoxémico UNSET en la región primaria;
  - disponibilidad central normal (la hipercapnia del 49m es falla ventilatoria mecánica);
  - sin fisiología del β-agonista sobre la FC ni systemic_stress;
  - sin acoplamiento mecánica → distrés;
  - sin integrar P2L-2;
  - colapso sólo estructural.

## 2. Verdad del caso (P2T-3-1)

<!-- generado:verdad -->
- **asthma_49m:** PA 142/86 (PAM 104,7), FC 132, SpO2 89 %, FR 30, WOB «Severe», Drowsy; gasometría arterial pH 7.3, PaCO2 51, PaO2 57, HCO3 24.2 (FiO2 21 %); venosa pH 7.26, PCO2 58; lactato 2.6; glucosa 121; flujo espiratorio: He cannot complete a reliable peak-flow maneuver; examen: «Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver.»; POCUS: No B-lines; A-line pattern bilaterally; radiografía: Hyperinflation without pneumothorax or focal air-space opacity.; β-agonista previo autorado sí.
- **asthma_24f:** PA 138/84 (PAM 102,0), FC 126, SpO2 90 %, FR 34, WOB «Markedly increased», Alert; gasometría arterial pH 7.45, PaCO2 31, PaO2 59, HCO3 20.8 (FiO2 21 %); venosa pH 7.41, PCO2 38; lactato 2.1; glucosa 116; flujo espiratorio: Peak expiratory flow is 35% of her documented personal best; examen: «Marked effort, prolonged expiration and widespread expiratory wheeze with reduced air entry. Peak expiratory flow is 35% of her documented personal best.»; POCUS: No B-lines; A-line pattern bilaterally; radiografía: Hyperinflation without focal consolidation or pneumothorax.; β-agonista previo autorado sí.
- Después de la llegada: NONE_AUTHORED: no oxygen, bronchodilator or steroid response and no later observation is authored.
- Igual a la verdad que leyó P2S-3: sí.
<!-- /generado:verdad -->

Clasificación:
- todo lo anterior es `AUTHORED_CASE_TRUTH`;
- la deriva de la obstrucción, la fatiga y el broncodilatador del motor heredado son `LEGACY_ENGINE_BEHAVIOR`;
- la FR expresada, W, la PaCO2, el pH, la FC predicha, el aporte y el nivel de conciencia son `MODEL_DERIVED`.

No hay verdad autoral posterior a la llegada.

## 3. Región (P2T-3-3, -4, -14)

El distrés de llegada es una región `FAMILY_CANDIDATE` que viene de la evidencia respiratoria autoral, no de la FR ni de la
FC:
- 49m: «Severe», entrada de aire muy pobre, no completa frases, somnolencia;
- 24f: «Markedly increased», frases cortas, PEF 35 %.

Con la normalización, la región previa es d(24f) ∈ (0, 1). La FR y la FC autorales sólo **prueban** qué parte de esa región
es compatible:
- x = g_FR·d es el producto que pide la FR autoral sobre la banda de FR intrínseca 12–20;
- y = g_FC·d, el que pide la FC sobre la banda de reposo 60–100, descontado el objetivo simpático que el mapeo
  comprometido ya pide;
- el orden de la evidencia se exige en las 25 llegadas de P2T-2 (las de familias anteriores y los controles).

<!-- generado:region -->
- Estado: **ASTHMA_FEASIBLE_SUBREGION_NONEMPTY**; no vacía en cada k llevado: sí; monótona en k: sí.

| k | ρ permitido (k) | Cota inferior | Cota superior | x(49m) = g_FR·d(49m) en ρ medio | d(24f) en ρ medio | E(49m) | E(24f) |
|---|---|---|---|---|---|---|---|
| 1,000 | [0,0231; 0,0981] | pulmonary_embolism_61m | pulmonary_edema_58m | [17,32; 31,82] | [0,544; 1,000] | [0,314; 0,458] | [0,575; 0,759] |
| 1,414 | [0,0232; 0,0998] | pulmonary_embolism_61m | pulmonary_edema_58m | [16,00; 31,82] | [0,503; 1,000] | [0,314; 0,475] | [0,563; 0,759] |
| 2,000 | [0,0261; 0,1021] | pulmonary_embolism_61m | pulmonary_edema_58m | [14,12; 31,82] | [0,444; 1,000] | [0,314; 0,502] | [0,547; 0,759] |

- Intersección robusta en k (DIAGNOSTIC_ONLY: the k-robust rho intersection; not a clinical prior): [0,0261; 0,0981].
<!-- /generado:region -->

## 4. Testigos en el núcleo vivo (P2T-3-5, -6, -15)

Sólo después de probar la región no vacía. Regla predeclarada: k y una fracción del intervalo efectivo de ρ; x(49m) y
x(24f) en el medio de sus intervalos admisibles, con x(24f) por debajo de x(49m). Son `REGION_WITNESS_ONLY`: no son un
ajuste ni un prior.

<!-- generado:testigos -->
- REGION_WITNESS_ONLY, regla predeclarada {'HIGH': [2.0, 0.75], 'LOW': [1.0, 0.25], 'MID': [1.4142135623730951, 0.5]}, aplicada después de probar la región no vacía.

| Testigo | k | ρ | g_FR·d(49m) | d(24f) | Caso | FR | PaCO2 | pH | W | E | FC (FC intrínseca 60) | FC autoral |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 1,000 | 0,0419 | 24,70 | 0,851 | asthma_49m | 30,00 | 51,00 | 7,299 | 0,784 | 0,374 | 85,4 | 132 |
| LOW | 1,000 | 0,0419 | 24,70 | 0,851 | asthma_24f | 34,00 | 31,00 | 7,450 | 1,290 | 0,702 | 81,7 | 126 |
| MID | 1,414 | 0,0615 | 23,91 | 0,835 | asthma_49m | 30,00 | 51,00 | 7,299 | 0,784 | 0,382 | 95,5 | 132 |
| MID | 1,414 | 0,0615 | 23,91 | 0,835 | asthma_24f | 34,00 | 31,00 | 7,450 | 1,290 | 0,698 | 90,0 | 126 |
| HIGH | 2,000 | 0,0831 | 22,97 | 0,807 | asthma_49m | 30,00 | 51,00 | 7,299 | 0,784 | 0,391 | 105,2 | 132 |
| HIGH | 2,000 | 0,0831 | 22,97 | 0,807 | asthma_24f | 34,00 | 31,00 | 7,450 | 1,290 | 0,691 | 97,2 | 126 |

- Todos soportados por el núcleo vivo, y la misma llegada con la mecánica apagada queda rechazada (M1): sí.
<!-- /generado:testigos -->

## 5. Cursos estructurales (P2T-3-5, -8, -12, -13)

Todos en el testigo medio y sólo de dirección:
- la obstrucción sin tratar, con el escritor de P2S-3;
- el alivio mecánico, con la sonda sintética de P2S-2 (`BRONCHODILATOR_WRITER_DEFERRED`);
- un alivio sintético del distrés, que va a un objetivo explícito y en el último minuto escribe la diferencia exacta;
- una G directa sintética.

<!-- generado:cursos -->
- **asthma_49m:** obstrucción sin tratar: E baja sí, PaCO2 sube sí, FR y distrés intactos sí, la familia sólo escribe mecánica sí; alivio mecánico: W sube y PaCO2 baja sí sin tocar distrés, FR ni FC sí; alivio del distrés (sintético): objetivo exacto sí, FR y FC bajan sí, mecánica intacta sí; G directa (sintética): SpO2 baja sí, L 0 sí.
- **asthma_24f:** obstrucción sin tratar: E baja sí, PaCO2 sube sí, FR y distrés intactos sí, la familia sólo escribe mecánica sí; alivio mecánico: W sube y PaCO2 baja sí sin tocar distrés, FR ni FC sí; alivio del distrés (sintético): objetivo exacto sí, FR y FC bajan sí, mecánica intacta sí; G directa (sintética): SpO2 baja sí, L 0 sí.
- Pasa: sí.
<!-- /generado:cursos -->

## 6. Invariancia de escala

<!-- generado:escala -->
- outputs depend on g_RR d and g_HR d only (two readers, no other reader of d): (lambda d, g / lambda) is the same physiology; rho and d(24f) / d(49m) are invariant.
- Diferencia máxima con λ potencia de 2: 0.0; con λ = 10: 3.55e-15 (cota de redondeo 2.27e-13).
- Pasa: sí.
<!-- /generado:escala -->

## 7. Ortogonalidad mecánica / distrés (P2T-3-7)

<!-- generado:ortogonalidad -->
- 24f con la mecánica fija (E 0,607): el distrés (x) cambia con k: k 1,000 → 28,62, k 1,414 → 27,30, k 2,000 → 25,42.
- 24f con el distrés fijo (x 20,0): la mecánica cambia: k 1,000 → E 0,717, k 1,414 → E 0,697, k 2,000 → E 0,672.
- Testigo medio: 49m E 0,382 y d 1; 24f E 0,698 y d 0,835: difieren en ambas sí.
- La composición del impulso no lee la mecánica: sí; ortogonalidad de P2T-1 en vivo sí; no mechanics -> distress coupling (UNSET, off); distress is never f(mechanics_efficiency).
- Pasa: sí.
<!-- /generado:ortogonalidad -->

## 8. Familias anteriores, controles y anafilaxia (P2T-3-16, -17, -18)

<!-- generado:familias -->
| k | Edema 58m | TEP 61m | TEP 33f (cota sup.) | Opioides (d 0) | GI (d 0) | Anafilaxia forzada | Residual SCA explicado (mín.) |
|---|---|---|---|---|---|---|---|
| 1,000 | sí | sí | sí | sí | sí | no | 6,1 % |
| 1,414 | sí | sí | sí | sí | sí | no | 0,0 % |
| 2,000 | sí | sí | sí | sí | sí | no | 0,0 % |

- Sensibilidad hipoxémica (SENSITIVITY_ONLY (P2P-2 SYNTHETIC_ONLY), ganancia 5.0): sigue no vacía sí; usada para el veredicto: no.
- Pasa: sí.
<!-- /generado:familias -->

## 9. Parámetros

<!-- generado:parametros -->
- Siguen UNSET: distress_to_respiratory_drive_gain, distress_to_sympathetic_gain, numeric arrival distress (any case), WOB -> distress mapping, mechanics -> distress coupling, hypoxaemic drive gain and mapping, beta-agonist HR effect, systemic_stress gains, bronchodilator / distress kinetics.
- Perfiles comprometidos sin lectores ni impulso hipoxémico: sí; campos nuevos del perfil: ninguno; distrés de llegada comprometido: {'asthma_24f': 0.0, 'asthma_49m': 0.0}.
- Pasa: sí.
<!-- /generado:parametros -->

## 10. No regresión (P2T-3-22)

<!-- generado:no_regresion -->
- Registro de P2T-1A reproducido sobre su árbol: sí; intacto sí.
- Registro de P2S-3 intacto: sí; ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_DRIVE_GAP; P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT (carried, not rewritten).
- Perfil del asma con la mecánica encendida (M1): sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 11. Prueba contra el árbol de P2T-1A

<!-- generado:prueba -->
- Tuplas revertidas a las de P2T-1A: `clinical_core/decision_pack.py` sí, `clinical_core/lactate_slice.py` sí.
- Archivos comunes fijados por hash: 123, intactos sí.
- Vista de P2T-1A: digest sí, su prueba sí, registro sí.
<!-- /generado:prueba -->

## 12. Veredicto

<!-- generado:veredicto -->
- sí — a non-empty asthma feasible subregion exists in the carried (k, rho) region: both cases, the evidence order, RR, PaCO2 / mechanics, HR compatibility and the cross-family order
- sí — mechanics and distress stay orthogonal (independent variation inside the region; no reader of the mechanics in the distress path; P2T-1's orthogonality live)
- sí — both asthma cases are supported at every region witness by the live core (authored RR and PaCO2 reproduced, HR at or below the authored, SpO2 anchored, M1 satisfied) and the structural courses hold
- sí — no common-core change is required (only the two tuple files differ from P2T-1A; every other file proven)
- sí — the previous respiratory families stay compatible (pulmonary edema 58m, PE 61m, PE 33f upper bound) and the anaphylaxis cases are not forced to overpredict
- sí — the opioid and GI controls stay valid (distress 0 admissible); the ACS residual is not closed
- sí — no clinical point calibration is required (the region carried as intervals; no optimization; witnesses after non-emptiness; scale invariance shown)
- sí — the hypoxaemic gain, the beta-agonist HR effect and the distress gains stay UNSET; systemic stress deferred
- sí — non-regression: P2T-1A's record on its tree, P2S-3's record untouched, the case truth P2S-3's

**Veredicto: ASTHMA_SHADOW_MIGRATION_READY** (ASTHMA_FEASIBLE_SUBREGION_NONEMPTY)
<!-- /generado:veredicto -->

## 13. Lectura

### 13.1 Qué deja este paquete

- **El asma cabe en la región común de distrés.**
  - Con k ∈ [1, 2], ρ ∈ [0,023; 0,098] con k = 1, [0,023; 0,100] con k = √2 y [0,026; 0,102] con k = 2.
  - Producto normalizado g_FR·d(49m) entre ~14–17 y 31,8, y d(24f) ∈ [0,44–0,54; 1).
  - El núcleo vivo reproduce exactamente la FR y la PaCO2 autorales de los dos casos (30 / 51 y 34 / 31). La FC queda
    por debajo de la autoral, y el resto se deja al β-agonista y a la activación no modelados.
  - El COMMON_DRIVE_GAP de P2S-3 queda resuelto hacia adelante, sin tocar ninguna ecuación común.
- **Sin contradicción causal en el 49m:** el distrés sube la FR y la mecánica baja la ventilación efectiva, así que FR alta y
  PaCO2 alta coexisten. Sin tratar, la obstrucción baja E y sube la PaCO2 sin mover la FR ni el distrés. El alivio
  mecánico sintético baja la PaCO2 sin tocar FR, FC ni distrés.
- **El 24f** queda con menos distrés (d < 1), mejor mecánica (E mayor) y PaCO2 baja.
- Las familias anteriores, los controles y la anafilaxia son compatibles en todo k llevado.

### 13.2 Revisión adversarial

Una, de sólo lectura, sobre el candidato congelado (`914ac31`) y su evaluación: ningún hallazgo alto, 2 medios y 5 bajos,
cada uno comprobado con una sonda. Las sondas del revisor confirman que las condiciones sustantivas se cumplen en toda la
región:
- 270 esquinas soportadas;
- k no vacío también en 1,1, 1,25, 1,5, 1,75 y 1,9;
- margen de la anafilaxia ≤ −4,8;
- cursos, escala, ortogonalidad y conciencia que pasan también en LOW y HIGH.

No se vuelve a congelar y el veredicto no cambia. Las debilidades son de la regla congelada.

1. **Medio: el criterio 3 no discrimina.** La FR, la PaCO2 y la SpO2 se reproducen por construcción, porque la FR
   intrínseca y E se despejan de lo autoral, y `supported` no comprueba ni la banda de FR intrínseca, ni E ≤ 1, ni el
   orden. **Se añadió en las pruebas, no en la fuente congelada,** el chequeo independiente: en los tres testigos la FR
   intrínseca queda en 12–20 (14,3–18,5), E en (0, 1] (0,37–0,70), d(24f) < 1 y E(49m) < E(24f). Queda como deuda: el
   próximo paquete congelado debe leerlo en su veredicto.
2. **Medio: el criterio 1 basta con un k no vacío.** El veredicto no lee `every_carried_k`, la monotonía ni el orden
   mecánico; con un k vacío, `witnesses()` fallaría por error en vez de cerrar NOT_READY. Hoy no influye (todo k es no
   vacío). **Se añadió en las pruebas** el chequeo de `every_carried_k`, la monotonía, la contigüidad y el orden mecánico en
   cada punto. Queda como deuda.
3. **Bajo: la variación independiente dentro de un caso depende de la carga ácida.**
   - Con k fijo, E y x quedan ligados a través de la FR intrínseca del mismo caso. Es un acoplamiento de identificabilidad,
     no fisiológico.
   - La ortogonalidad real es estructural: la composición del impulso no lee la mecánica, no hay distrés = f(E) y la
     ortogonalidad de P2T-1 vale en vivo.
4. **Bajo: el residual del SCA no queda forzado, pero tampoco excluido.**
   - El distrés mínimo admisible explica entre 0 y 6 % del residual.
   - La región, sin embargo, admite hasta un 167 % (k = 1), 140 % (k = √2) y 102 % (k = 2), con el ρ máximo y el x máximo
     del SCA 70f.
   - No se usa para cerrarlo (SYSTEMIC_STRESS_DEFERRED). Excluirlo exigiría una cota superior autoral del distrés del SCA
     («Mildly increased»), que no existe.
5. **Bajo:** los criterios 5 y 6 comparten el mismo booleano, así que el 6 nunca puede ser el bloqueante. Queda como deuda.
6. **Bajo:** `cross_family` se evalúa en el ρ medio. Las sondas del revisor muestran que vale en toda la región. Queda como
   deuda: evaluarlo también en los bordes.
7. **Bajo:** el orden autoral es estricto, pero el intervalo de d(24f) se informa como [lo; 1,0]. Debe leerse [lo; 1). Los
   testigos quedan por debajo de 1.

Hay además dos tautologías menores en la invariancia de escala y en `no_optimization`. La prueba sustantiva es la corrida
del núcleo con (λ·d, g/λ).

### 13.3 Proceso

- Una sola congelación (`914ac31`) antes de la única evaluación.
- Sin cambios en el núcleo común. El arrastre a los paquetes cerrados (25 archivos de prueba, la lista de permitidos del
  aislamiento, las listas de W y del filtro del SCA, cuatro digests de documentos) se resolvió a la primera. Las 68 pruebas
  de Fase 2 pasaron antes de congelar.
- Análisis por intervalos analíticos y eliminación monótona. Sólo búsqueda por bisección de los bordes de ρ (en una
  dimensión) y testigos dispersos. Ninguna grilla cartesiana sobre k × ρ × distrés × mecánica.

### 13.4 Limitaciones

- La escala absoluta del distrés sigue sin identificarse. La normalización d(49m) = 1 es sólo analítica.
- La FC del asma es sólo una cota. La parte de la taquicardia que viene del β-agonista no está determinada.
- La SpO2 queda anclada en la llegada y no baja cuando sube la PaCO2 (HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED).
- El nivel de conciencia no lee la PaCO2 (CONSCIOUSNESS_INTEGRATION_DEBT).
- No hay escritor de broncodilatador ni cinética del distrés, sólo sondas de dirección.
- Pendientes de la revisión: los hallazgos 1, 2, 5 y 6 sobre la regla congelada, y el 4 sobre el SCA.

### 13.5 Siguiente paquete (no se inicia)

Orden por recurrencia entre familias, centralidad causal, impacto en el manejo, valor informativo y riesgo de complejidad
prematura:

1. **Auditoría de sólo lectura hipoventilación → oxigenación (gas alveolar).**
   - Recurre en el asma 49m, los dos opioides y la hipercapnia del edema.
   - Es causalmente central: la SpO2 alimenta el aporte, la deuda y el lactato.
   - Tiene el mayor impacto en el manejo (oxígeno, ventilación no invasiva, vía aérea).
   - Cierra la cadena respiratoria abierta (FR → W → PaCO2 → PaO2 / SpO2).
   - Como auditoría, el riesgo es bajo.
2. **Auditoría de sólo lectura del estrés sistémico.**
   - Tiene la mayor recurrencia: residuales de FC en SCA, hipoglucemia, cólico renal, pielonefritis, TEP 33f y
     β-agonista.
   - Afecta sobre todo a la FC, con menos impacto en el manejo, y su semántica es más amplia.
3. **La siguiente familia ortogonal (opioide).** Prueba la disponibilidad central, pero depende del enlace hipoventilatorio.
4. **Preparación de la integración de la conciencia.** Depende de las dos primeras.
