# Cierre formal de la Fase 2 · núcleo clínico común en sombra

Artefacto autoritativo del cierre (P2X-3). Rama `phase-2-clinical-core-shadow`.

```
PHASE 2 CLOSED
SHADOW PHYSIOLOGY ONLY
NO RESIDENT-VISIBLE RUNTIME CHANGE
PHASE 3 NOT STARTED
```

Las cuatro líneas de arriba se declaran porque los criterios de cierre se cumplen y porque cada una es
comprobable: `test_phase2_closure.py` recalcula del repositorio todo lo que este documento afirma, contra el
registro `docs/revision/P2X3_phase2_closure.json`. Un registro que se desactualice, o que declare más de lo que
el repositorio sostiene, falla. Este paquete no cambia fisiología ejecutable, no elige ninguna magnitud clínica,
**no se integra en tiempo de ejecución** y **no cambia lo que ve el residente**.

- **Cabeza ejecutable final certificada:** `4e8d1844ab5b3a80ecf589c5fc5d2e90c6985820`.
- **Cabeza autoritativa de la Fase 2:** el commit de cierre de P2X-3 sobre esa cabeza. Su contenido ejecutable es
  idéntico: ningún archivo de `clinical_core/` cambia aquí.
- **Digesto de la Fase 2:** `22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a`
  (sha256 del JSON canónico de `{ruta: sha256(bytes)}` de los 141 archivos `clinical_core/**/*.py`, sin exclusiones).

## 1. Qué se cerró

El objetivo de la Fase 2 era construir una fisiología común coherente, con regiones de incertidumbre explícitas,
sin contradicciones causales, suficientemente buena para migrar familias y probar generalización. Eso es lo que
queda cerrado: la fisiología común **en sombra**, con sus guardas ejecutables y su registro de incertidumbre. No
queda cerrada —ni empezada— su integración en la aplicación.

## 2. Inventario de familias migradas

Seis familias mecánicamente distintas, cada una con su módulo de contribución, su migración, sus pruebas y los
paquetes que la cerraron:

| Familia | Mecanismo | Módulo | Migración |
| --- | --- | --- | --- |
| `gi_haemorrhage` | hipovolemia por hemorragia; estado hemático compartido | `clinical_core/modules/gi_haemorrhage.py` | `clinical_core/legacy_adapter.py` |
| `acs_ischaemia` | cardiogénico; pérdida de bomba con congestión | `clinical_core/modules/acs_ischaemia.py` | `clinical_core/acs_migration.py` |
| `pulmonary_edema` | congestivo; agua pulmonar contra intercambio | `clinical_core/modules/pulmonary_edema.py` | `clinical_core/edema_migration.py` |
| `pulmonary_embolism` | obstructivo vascular; espacio muerto y poscarga | `clinical_core/modules/pulmonary_embolism.py` | `clinical_core/embolism_migration.py` |
| `asthma` | obstructivo de vía aérea; trabajo y mecánica, con distrés | `clinical_core/modules/asthma.py` | `clinical_core/asthma_migration.py` |
| `opioid` | depresión respiratoria central; impulso, con reversión | `clinical_core/modules/opioid.py` | `clinical_core/opioid_migration.py` |

Nueve trayectorias comprometidas (siete perfiles; `opioid` con dos casos) corren sin rechazo y son
byte-idénticas a las del predecesor.

## 3. Inventario de la fisiología común

Doce canales comunes: `V`, `T`, `P`, `R`, `L`, `G`, `W`, `D`, `N`, `HB`, `GLUCOSE`, `K`; más el estado auxiliar
compartido (hemático, de ritmo y de anclas).

El **núcleo que se ejecuta** son cinco archivos: `clinical_core/__init__.py`, `state.py`, `derived.py`,
`provenance.py` e `integration.py`. Todo lo demás del paquete es análisis, filtro, referencia o presentación.

Capas, con los paquetes que las construyeron:

- estado hemático compartido: volumen, hemoglobina, dilución y tasa común de sangrado (P2I-2T, P2I-2U);
- entrega de oxígeno, deuda `D` y lactato (P2I-2AC, P2I-2AD);
- frecuencia cardíaca: intrínseca, impulso simpático desde la deuda, barorreflejo y envolventes
  (P2I-2AE, P2I-2AF, P2J-4, P2V-1);
- presión y tono: bomba, `T`, MAP/SBP/DBP, lazo retardado del tono y su factor distributivo
  (P2J-1, P2J-2, P2W-1, P2X-1, P2X-1A);
- respiración: impulso, frecuencia, trabajo, mecánica y reclutamiento (P2K-1…P2K-5, P2P-2, P2S-2);
- intercambio gaseoso: agua pulmonar → cortocircuito → saturación, PaO₂ y PaCO₂ (P2O-1, P2O-2, P2O-3);
- equilibrio ácido-base: carga ácida, pH y compensación (P2K-2);
- consciencia: canal `N` y encefalopatía (P2L-1, P2L-2);
- distrés y activación, compartidos entre las familias respiratorias (P2T-1, P2T-1A, P2T-3);
- colapso: paro, flujo cero y ROSC (P2M-1, P2M-2);
- intervenciones: fluidos, oxígeno, modificadores y su temporización.

## 4. Incertidumbre y parámetros

58 parámetros registrados: **0 aprobados por docentes**, 52 con soporte de candidato, 2 sólo sintéticos y 4
valores por defecto sin mapear. Cerrar la Fase 2 no necesitó aprobar ninguna magnitud clínica, y la IA no
aprueba ninguna.

El principio se mantiene: una cantidad no identificable se conserva como región o con un estado de borde
explícito, nunca colapsada a un punto. Las regiones viven en los registros de `docs/revision/`.

## 5. Deuda aceptada de la Fase 2 (13)

`STEADY_STATE_W_ARRIVAL_TENSION` (TD-124), `OPIOID_HR_RESIDUAL` (TD-124), `COLLAPSE_THRESHOLDS` (TD-109),
`FIO2_MAGNITUDE` (TD-123), `RESPIRATORY_DISTRESS_CALIBRATION` (TD-121),
`SYSTEMIC_STRESS_CALIBRATION` (TD-125), `PRESSURE_TO_TONE` (TD-118),
`SIDED_PRELOAD_AND_INTERDEPENDENCE` (TD-118), `CUMULATIVE_FLOATING_POINT_CANCELLATION` (TD-121),
`PHYSICAL_PAO2_BOUNDARY` (TD-123), `HYPOXAEMIC_FEEDBACK_STABILITY` (TD-117),
`DISTRIBUTIVE_TONE_MAGNITUDE` (TD-126), `TONE_DOMAIN_LIMITS` (TD-127).

## 6. Deuda de integración de la etapa siguiente (3)

`CONSCIOUSNESS_WIRING` (TD-107), `RUNTIME_INTEGRATION` (TD-127), `RESIDENT_VISIBLE_BEHAVIOUR` (TD-127).

## 7. Deuda de investigación futura (5)

`MALDISTRIBUTION_AND_EXTRACTION`, `PLASMA_LEAK`, `UPPER_AIRWAY`, `DRUG_KINETICS`,
`ADDITIONAL_FAMILY_MIGRATIONS` (las cinco en TD-126).

Las 21 están en exactamente una clase, y ninguno de los dos bloqueos de cierre que la revisión de P2X-1
demostró (`P2X1_R_F1_CONDITIONAL_T_OWNERSHIP`, `P2X1_R_F4_CLAMP_IN_AN_ACCEPTED_MINUTE`) queda clasificado como
no bloqueante: los dos están cubiertos por sondas que corren.

## 8. Supersesión

La historia no se reescribe; se declara. Tres filas vigentes:
`TD120_HISTORICAL_SUPERSESSION_ACCEPTED`, `P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A`,
`P2J2_UPPER_ENDPOINT_PROBE_SUPERSEDED_BY_P2X1A`. Cada una verifica en disco el artefacto histórico y el
superesor, con su digesto.

## 9. Evidencia de certificación

Candidato `b7e6267`, huella `ccec42b95909…` idéntica al inicio y al final de la corrida:

- suite completa: 10 493 pruebas, 2 fallas, 0 errores, 93 omitidas, 1 xfail, en 4 particiones con 2 h de tiempo
  máximo cada una;
- las 2 fallas eran dos digestos de fuentes rancios, no fisiología: los dos registros se regeneraron con sus
  propios generadores y sus cuerpos salieron byte-idénticos; 118 pruebas focalizadas sobre las cuatro suites que
  los leen pasan;
- regresiones: 56/56 activas aprobadas, 10 retiradas conservadas sin correr;
- congelamientos, aislamiento, lector y Contracts: 47 pruebas, 0 fallas;
- golden directo y golden por Contracts v2: idénticos a los comprometidos;
- `git diff --check` limpio; árbol limpio.

## 10. Evidencia de aislamiento

`test_shadow_core_isolation.py` fija la superficie de importación del paquete, y ningún módulo de la aplicación
importa `clinical_core`. Las coincidencias en la raíz del repositorio son de `clinical_core_defaults`, un módulo
preexistente de la aplicación con un nombre parecido y sin relación.

## 11. Evidencia de reproducibilidad

- digestos que recalculan: calibración `c1eeb5538a4e…`, guarda de cierre P2X-1A `eca47d357674…`, rodaja de
  lactato `3c4648e7bdc5…`, paquete de decisiones `e0fdfbe33abe…`;
- el registro de P2X-1 se reproduce byte a byte sobre su propio árbol, y su digesto congelado
  `3afa71b2dfa0…` recalcula;
- las nueve trayectorias comprometidas son idénticas a las del predecesor.

## 12. Estado de las propiedades declaradas

P2X-1A devolvió `PHASE2_DECLARED_PROPERTIES_CLOSED` sobre 12 criterios ejecutables y 22 sondas (A1–A22), con dos
sondas dedicadas a la falsabilidad: mutar una fuente protegida del predecesor, o quitar una deuda del cuadro,
invierte el veredicto. P2X-2, la auditoría de salida de sólo lectura, devolvió
`PHASE2_READY_FOR_FINAL_FREEZE`.

## 13. Estado en tiempo de ejecución

`family_engine.py` sigue siendo la fuente de verdad del simulador. `clinical_core` funciona sólo en sombra: no
está integrado, no cambia la pantalla del residente y **la Fase 3 no está iniciada**. La integración, el cableado
de la consciencia y cualquier cambio visible para el residente son deuda de la etapa siguiente, no de ésta.

## 14. Lo que este cierre no dice

- No dice que la fisiología esté calibrada: 0 magnitudes aprobadas.
- No dice que las cuatro contradicciones declaradas se hayan vuelto a ejecutar aquí: cada una cita la sonda
  ejecutable que la probó en su paquete (P2W-1, P2X-1, P2J-2), y nueve comprobaciones de contradicción sí corren
  en cada evaluación de la guarda de cierre.
- No dice que las familias no migradas estén cubiertas: `ADDITIONAL_FAMILY_MIGRATIONS` sigue como deuda.
- No autoriza la etapa siguiente: eso es una decisión docente.

## 15. Decisiones docentes pendientes

1. Aceptar o no este cierre formal de la Fase 2 (la IA propone; la persona docente confirma).
2. La lectura declarada de P2X-1A sobre si «cualquier otra contribución» incluye las sondas sintéticas
   declaradas y las pruebas, que hoy quedan exentas de la propiedad del canal `T` por módulo de definición.
3. Si la Fase 3 abre, qué parte de la integración se autoriza y en qué orden.
