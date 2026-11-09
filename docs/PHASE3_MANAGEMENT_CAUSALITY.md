# Fase 3 — Causalidad de manejo entre familias (P3-104 … P3-116)

Rama `phase-3-runtime-integration`, desde `1de3706`. Trabajo de adaptadores de la **Fase 3**, fuera del núcleo
congelado: ningún archivo de `clinical_core/` cambia y el digesto de cierre de la Fase 2 queda intacto. No se
amplía autoridad de producción (`COMMON_CORE_RUNTIME_AUTHORITY = False`, `APPROVED_SNAPSHOTS` = 1), no se toca
el primer piloto, no se cambia puntuación y **no se afirma validación clínica de nada**.

El objetivo de este ciclo no es ajustar curvas: es que el manejo del residente produzca evolución **causal,
temporalmente correcta y clínicamente defendible**, y que eso **generalice**.

---

## §1 (P3-104) El contrato de causalidad de manejo

`management_causality.py`, módulo nuevo en la raíz. Es **especificación**: no importa `clinical_core` ni la capa
de sombra —no podría, porque `test_shadow_core_isolation` declara la capa como cinco módulos **nombrados**— y
**no lleva ningún valor numérico de enfermedad** (una prueba comprueba que ningún campo del contrato contiene un
dígito).

**Las nueve propiedades** del estándar educativo: `DIRECTION`, `TEMPORALITY`, `CAUSAL_SPECIFICITY`,
`MAGNITUDE_PLAUSIBILITY`, `DOSE_ORDERING`, `REVERSIBILITY`, `TIME_WITHOUT_ACTION`,
`CROSS_FAMILY_CONSISTENCY`, `SAFETY`.

**Los ocho campos** que hay que declarar por par enfermedad/intervención: A mecanismo objetivo (el **canal**,
nunca una variable de lectura) · B dirección esperada, en el canal y aguas abajo · C inicio, **y de quién es el
reloj** · D persistencia y reversión · E orden de dosis y saturación · F observables aguas abajo, **en orden
causal** · G **qué NO debe moverse directamente**, que es el atajo que delataría el mecanismo equivocado ·
H comportamiento en el borde.

Y los predicados genéricos que lo comprueban, sobre series `{minuto: valor}`: `no_effect_before`,
`effect_starts_at`, `direction`, `monotone_after`, `dose_ordered`, `waiting_has_cost`, `untouched`, `inside`
(exige que quien llama declare la banda: no hay bandas por omisión) y `no_paradox`.

## §2 (P3-105) Matriz de intervenciones, medida

Leída de los adaptadores reales y de los guiones de la batería de aceptación certificada, no de la intención.

| Familia | Intervención | Acción del motor | Objetivo común | Escritor de familia | Temporalidad | Región de magnitud | Replay | Sombra viva | Define el manejo | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| **GI** | cristaloide | `fluid` | ✔ `Crystalloid` | ✔ | del motor (recibo) | **región cerrada** (P3-81) | ✔ | ✔ | **sí** | **`CAUSALLY_READY`** |
| GI | sangre | `blood` | ✔ `PackedRedCells` | ✔ | del motor | punto comprometido | ✔ | ✔ | **sí** | **`CAUSALLY_READY`** |
| GI | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | ✔ | no | **`CAUSALLY_READY`** |
| GI | IBP | `ppi` | ✔ `ProtonPumpInhibitor` | ✔ | del motor | — | ✔ | ✔ | no | **`CAUSALLY_READY`** |
| GI | control de la fuente | `consult` → `family_state.endoscopy_at` | ✔ `EndoscopicHemostasis` | ✔ | **del motor** | — | ✔ | ✔ | **sí** | **`CAUSALLY_READY`** |
| GI | esperar | — | — | — | — | — | ✔ | ✔ | **sí** | **`CAUSALLY_READY`** |
| **ACS** | reperfusión | `consult` → `family_state.reperfusion_at` | ✔ `CoronaryReperfusion` | ✔ | **del motor** (puerta-balón 90 min) | — | ✔ | no (`live=False`) | **sí** | **`CAUSALLY_READY`** ← *nuevo en P3-107* |
| ACS | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | no | no | **`CAUSALLY_READY`** |
| ACS | antiagregante | `aspirin`, `p2y12` | ✘ | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |
| ACS | anticoagulación | `anticoagulation` | ✘ | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |
| ACS | nitrato | `nitroglycerin`, `nitroglycerin_bolus` | ✘ | ✘ | — | — | — | — | no | **`MISSING_COMMON_MECHANISM`** |
| ACS | fluido | `fluid` | ✔ (común) | ✘ sin mapeo ACS | — | — | — | — | no | **`MISSING_TREATMENT_WRITER`** |
| **Edema** | diurético | `diuretic` | ✔ **parámetro de construcción** de `EdemaCongestion` | ✔ | — | **ninguna** | — | no | **sí** | **`PARAMETER_REGION_MISSING`** |
| Edema | nitrato | `nitroglycerin` | ✔ el mismo parámetro | ✔ | — | **ninguna** | — | no | **sí** | **`PARAMETER_REGION_MISSING`** |
| Edema | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | no | no | **`CAUSALLY_READY`** |
| Edema | VNI | `niv`, `bag_mask`, `intubation` | ✘ (P2K-3 apagado) | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |
| **PE** | anticoagulación | `anticoagulation` | ✘ | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |
| PE | trombólisis | `thrombolysis` | ✘ | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |
| PE | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | no | no | **`CAUSALLY_READY`** |
| **Asma** | broncodilatador | `bronchodilator`, `continuous_bronchodilator` | ✘ `BRONCHODILATOR_WRITER_DEFERRED` | ✘ | — | — | — | — | **sí** | **`MISSING_TREATMENT_WRITER`** |
| Asma | corticoide | `steroid` | ✘ `STEROID_ACUTE_PHYSIOLOGY_DEFERRED` | ✘ | — | — | — | — | **sí** | **`MISSING_TREATMENT_WRITER`** |
| Asma | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | no | no | **`CAUSALLY_READY`** |
| **Opioide** | naloxona | `naloxone` | ✔ `NaloxoneReversal` | ✔ | **de la orden** | punto comprometido, `SYNTHETIC_ONLY` | ✔ | no | **sí** | **`CAUSALLY_READY`** ← *nuevo en P3-111* |
| Opioide | oxígeno | `oxygen` | ✔ `Oxygen` | ✔ | del motor | — | ✔ | no | no | **`CAUSALLY_READY`** |
| Opioide | soporte ventilatorio | `niv`, `bag_mask`, `intubation` | ✘ (P2K-3 apagado) | ✘ | — | — | — | — | **sí** | **`MISSING_COMMON_MECHANISM`** |

### Un defecto preexistente que la matriz destapó, y se corrigió

Tres adaptadores declaraban sus huecos bajo las claves **`"medicine"` y `"ventilation"`**, que **no son clases
de acción del motor**: la clase del motor **es el fármaco** (`_MEDICINES` está indexado por ella). Un hueco
declarado bajo una clave que ningún evento lleva **no puede dispararse nunca**, así que su razón declarada no
llegaba al registro — llegaba el texto genérico. Re-claveados a las clases reales en los seis adaptadores, con
las razones físicas intactas. Una prueba (`C12`) deriva las clases **del propio motor** y falla si alguna clave
declarada no existe; es la prueba que encontró, además, una clave `"nitrate"` que yo mismo había inventado.

---

## §3 (P3-106) Cierre causal de GI

Las diez propiedades, sobre los escenarios GI existentes y con el evaluador y el núcleo congelados:

| Propiedad | Resultado |
|---|---|
| el sangrado continúa → empeora | ✔ sin tratar la sistólica cae de 106 a **57,9** |
| esperar → progresión | ✔ y cuantificada: §3.1 |
| cristaloide → mejora | ✔ sin efecto antes del minuto de la orden, mejora después, **cero huecos declarados** |
| sangre → mejora | ✔ y con **orden de dosis**: 1, 2 y 4 unidades no dan menos efecto |
| control de la fuente → menos deterioro | ✔ endoscopia al minuto 40: cero efecto antes, mejor a los 120 |
| manejo combinado → mejor que una parte | ✔ el paquete bate al cristaloide solo y a nada |
| el efecto sigue a la acción | ✔ `effect_starts_at` ≥ el minuto de la orden en las cuatro intervenciones |
| sin efecto antes del tratamiento | ✔ `no_effect_before` exacto, tolerancia 0 |
| sin paradoja | ✔ `no_paradox` en todo minuto desde la activación |
| sin frontera común en las trayectorias previstas | ✔ cero fallos del núcleo en todas las corridas |

### §3.1 El coste de esperar está en la integral, no en el punto final

Medido, y conviene decirlo porque es contraintuitivo y cambia cómo se escribe la prueba:

| | nadir | **media del curso** | sistólica @90 | @120 |
|---|---|---|---|---|
| sin tratar | 57,89 | **72,60** | 65,20 | 57,89 |
| cristaloide al minuto 10 | 64,79 | **79,41** | 72,15 | 64,79 |
| cristaloide al minuto 60 | 66,65 | **77,19** | 76,37 | 66,65 |

Tratar pronto es mejor **en el área**, y **peor en el minuto 90 y en el 120**, porque el cristaloide es
transitorio: la bolsa puesta pronto ya fugó y la puesta tarde todavía actúa. Lo que el residente le quita al
paciente esperando es **el tiempo que pasó por debajo**, no su cifra final. Una prueba de coste de espera
escrita sobre un minuto tardío mide lo contrario de lo que pretende, y la primera versión de `C5` lo hizo.

> ### Decisión de desarrollo P3-106
> **`GI_MANAGEMENT_CAUSALITY_READY`**, y **`GI_NUMERIC_CALIBRATION_DEFERRED`**: se detiene la calibración
> numérica de GI. Las diez propiedades se sostienen con la región aceptada, y la precisión que falta —el
> producto `tasa·ν` de FD-P3-89— **no hace falta** para la validación educativa vigente. El punto de
> desarrollo de presión sigue sirviendo para probar autoridad, y **no se afirma que esté calibrado
> clínicamente**.

---

## §4 (P3-107) ACS

**Implementado**: la reperfusión queda mapeada. Y la decisión arquitectónica importa: el minuto en que la
arteria se abre **no se lee de la orden** —`consult` y `reperfusion_referral` están en `NOT_PHYSIOLOGICAL`— sino
de `family_state["reperfusion_at"]`, que el motor calcula con **su propio reloj puerta-balón** (90 min, 120 con
traslado, `acs_reperfusion.py`). Es el mismo patrón certificado con que GI lee `endoscopy_at`, así que **la
latencia es la del motor y no una inventada aquí**.

Medido con `reperfusion_at = 60`:

| minuto | 30 | 59 | **60** | 70 | 90 | 120 |
|---|---|---|---|---|---|---|
| Δ sistólica | 0,0000 | 0,0000 | **+0,3512** | +2,7405 | +6,7344 | **+11,8105** |
| Δ relleno capilar (s) | 0 | 0 | −0,0129 | −0,1458 | −0,3652 | **−0,6304** |
| Δ lactato | 0 | 0 | 0,0000 | −0,0001 | −0,0029 | −0,0198 |

Cero efecto antes; arranque **exacto** en el minuto 60; **gradual** —el primer minuto mueve 34 veces menos que
una hora después, así que no normaliza nada al instante— y llega **aguas abajo** al relleno capilar y al
lactato, no por una escritura directa de presión.

**Oxígeno**: medido, actúa **por intercambio gaseoso** (SpO₂ +5,7; entrega +0,065; lactato −0,058) y su efecto
sobre la presión es **negativo** (−1,15 a −1,77 mmHg), porque mejor oxigenación tisular significa **menos
impulso simpático**. Es decir: **ningún beneficio directo de bomba**, y su huella en la presión es cinco veces
menor que la de la reperfusión. La primera versión de la prueba exigía inmovilidad, que habría sido exigir que
el oxígeno no haga nada.

**Fluido**: sin mapeo ACS certificado; declarado. **Antiagregante, anticoagulación y nitrato**: sin objetivo
común; declarados por su clase real de acción.

> **Veredicto P3-107: `READY_WITH_GAPS`.** La intervención que define el manejo —la reperfusión— es causalmente
> correcta. Los huecos son antiagregante, anticoagulación, nitrato y fluido, y **los cuatro exigen mecanismo
> nuevo**, así que no se tocan.

## §5 (P3-108) Edema pulmonar

**No implementado, y por una razón precisa.** La descongestión **existe** como mecanismo certificado, pero es un
**parámetro de construcción** del escritor de familia: `edema_migration.writer(progression, decongestion)` →
`EdemaCongestion`. El contrato del adaptador separa `writers()` (se construyen al abrir, **sin** ver las
acciones) de `interventions()` (se construyen **de** las acciones). Un tratamiento que es parámetro del escritor
de enfermedad no cabe hoy en esa separación.

Lo que haría falta: una extensión del contrato del adaptador para que los escritores de familia se puedan
reconstruir con las acciones espejadas. Es trabajo de la **Fase 3** y no toca el núcleo congelado, pero **cambia
infraestructura compartida por las seis familias**, y además la magnitud de descongestión **no tiene ninguna
región declarada** — habría que elegirla. Dos decisiones, una arquitectónica y una clínica, así que **paro aquí
y lo declaro** en vez de improvisar las dos.

**Oxígeno** sí está mapeado y es causalmente correcto. **VNI**: `P2K-3` dejó el reclutamiento **apagado**, así
que no hay objetivo común; declarado y **no simulado**.

> **Veredicto P3-108: `READY_WITH_GAPS`** — oxígeno correcto; diurético y nitrato
> `PARAMETER_REGION_MISSING` más extensión de contrato; VNI `MISSING_COMMON_MECHANISM`.

## §6 (P3-109) Embolia pulmonar

**No implementado, y aquí la razón es terminal.** `embolism_migration.writers(loss, rate, name)` **no tiene
ningún parámetro de tratamiento**: ni anticoagulación ni trombólisis están modeladas, y P2Q-2 lo declara. No es
que falte el mapeo: **falta el mecanismo**. Representar «la anticoagulación estabiliza y reduce la progresión»
exige semántica de progresión de la enfermedad que el modelo común no tiene.

Por la regla de seguridad del encargo —si un escritor de tratamiento exige modificar la fisiología común
congelada, **se para esa familia**— **paro PE**. No se finge beneficio, no se añade un escritor directo de
presión, y la trombólisis no se modela como disolución instantánea porque no se modela en absoluto.

> **Veredicto P3-109: `READY_WITH_GAPS`** en sentido estricto —el oxígeno es correcto— pero la familia es
> **`STRUCTURAL_COMMON_MECHANISM_MISSING`** para lo que define su manejo.

## §7 (P3-110) Asma

**No implementado.** `clinical_core.modules.asthma` declara `BRONCHODILATOR_WRITER_DEFERRED` y
`STEROID_ACUTE_PHYSIOLOGY_DEFERRED`: los escritores están **diferidos**, no ausentes por descuido. El objetivo
correcto sería la **mecánica** (`mechanics_efficiency`) → W → PaCO₂, nunca bajar PaCO₂ directamente; y para el
corticoide, una representación **sin efecto inmediato** es preferible a un beneficio rápido falso, que es
exactamente lo que el diferimiento ya representa.

Y hay un segundo bloqueo, compartido con el opioide y medido en §8: **la cadena no llega a la SpO₂**.

> **Veredicto P3-110: `READY_WITH_GAPS`** — oxígeno correcto; broncodilatador y corticoide
> **`MISSING_TREATMENT_WRITER`** por diferimiento declarado.

## §8 (P3-111) Opioide

**Implementado**: la naloxona queda mapeada, y es el caso más limpio de todos porque `NaloxoneReversal` ya es un
**contribuidor certificado** (P2U-1) — se mapea por la vía `interventions()` que ya existía, **sin tocar el
contrato**. Su tasa es la comprometida de `opioid_migration.NALOXONE`, declarada allí `SYNTHETIC_ONLY`; **este
mapeo no la elige**.

Medido en `opioid_35m`, naloxona al minuto 20:

| minuto | 10 | 19 | **20** | 25 | 40 | 60 | 120 |
|---|---|---|---|---|---|---|---|
| Δ frecuencia respiratoria | 0,0000 | 0,0000 | **+1,0545** | +4,9165 | +9,3759 | +10,6930 | +11,9500 |

Cero efecto antes, arranque exacto en la orden, monótono y saturante. **Cero huecos declarados** en la corrida
tratada. Y escribe **sólo la disponibilidad central**: nunca FR, PaCO₂, SpO₂ ni estado mental, que llegan a la
lectura como consecuencias aguas abajo.

**Oxígeno**: medido, **no corrige la hipoventilación central** — la frecuencia respiratoria queda idéntica a
tolerancia 10⁻⁹ con y sin oxígeno. Es la distinción educativa por la que existe esta familia, y se sostiene.

### §8.1 El hueco que la cadena tiene, y por qué no lo cierro

Sin tratar, la frecuencia respiratoria cae de 5,97 a 4,44 y la **SpO₂ no se mueve**: 80,0 en los 60 minutos. La
razón está escrita en el núcleo congelado, en la docstring de `derived.oxygenation`: «It reads **no ventilation,
PaCO2, RR**… **hypoventilation reaches PaCO2, never G**». Y el enlace existe, declarado y **apagado**: «P2T-5:
the common **hypoventilation → oxygenation link** (`SYMMETRIC_RELATIVE_ALVEOLAR_LINK`, full transmission),
**UNSET**», con `respiratory_quotient: float | None = None`.

El perfil lo suministra el **adaptador** (Fase 3), así que encenderlo **no tocaría el núcleo**. Lo probé con el
cociente respiratorio estándar, 0,8:

| minuto | 1 | 20 | 40 | 60 |
|---|---|---|---|---|
| SpO₂ hoy (enlace apagado) | 80,0 | 80,0 | 80,0 | 80,0 |
| SpO₂ con el enlace a transmisión completa | 79,5 | 67,6 | 45,7 | **25,2** |
| Δ SpO₂ que devuelve la naloxona | — | +17,9 | +51,6 | **+72,2** |

La **dirección es correcta** y el mecanismo está certificado, pero una SpO₂ del **25 %** con pulso presente en
un caso redactado como sobrevivible **no es clínicamente defendible**, y una naloxona que devuelve 72 puntos
tampoco. Por los estándares 4 (`MAGNITUDE_PLAUSIBILITY`) y 9 (`SAFETY`) del propio encargo, **no lo enciendo**:
la fracción de transmisión es una decisión clínica con consecuencias de manejo materialmente distintas, no hay
envolvente docente para una transmisión parcial, y mi confianza en cualquier fracción concreta está **por debajo
de 0,80**. Queda como decisión docente, cuantificada.

> **Veredicto P3-111: `READY_WITH_GAPS`.** La naloxona es causalmente correcta en su canal y el oxígeno no la
> suplanta. El hueco es el final de la cadena: la hipoventilación no alcanza la oxigenación, y cerrarlo es una
> decisión docente de magnitud.

---

## §9 (P3-112) Esperar, retrasar, omitir

- **Orden temporal**: comprobado en las cuatro intervenciones mapeadas con tolerancia **exactamente 0**. Ningún
  efecto empieza antes de su activación. Sin fuga desde el futuro.
- **Retraso**: la misma intervención al minuto 10 contra el 60 (§3.1). El curso tardío arrastra el deterioro
  acumulado, y eso se ve **en la integral**: media 79,41 contra 77,19, con el sin tratar en 72,60.
- **Tratar tarde sigue siendo mejor que no tratar**: 66,65 contra 57,89 al minuto 120. No se fuerza deterioro
  donde el paciente debería mejorar.
- **Transitorio contra persistente, y es el hallazgo transversal del paquete.** El cristaloide es
  transitorio: esperar cuesta el **área** y el punto final favorece al tardío. La reperfusión es
  **persistente** —la arteria queda abierta— así que esperar cuesta **las dos cosas**: medido a 180 minutos,
  abrir al minuto 60 da media de curso 99,75 y sistólica final 100,33, contra 95,23 y 95,50 abriendo al 120,
  con el sin tratar en 92,00 y 79,09. **La métrica correcta del coste de esperar depende de si el tratamiento
  persiste**, y escribirla mal mide lo contrario de lo que pretende.
- **Lo que no se fuerza**: en el oxígeno de ACS y del opioide no hay coste de espera porque no hay deterioro que
  prevenir por esa vía; se declara `NOT_APPLICABLE` en vez de inventar uno.

## §10 (P3-113) Acciones peligrosas

| Caso de la batería | Peligro | Clasificación |
|---|---|---|
| GI: heparina y aspirina en una hemorragia activa | aumentar el sangrado | **`SCORING_ONLY_DANGER`** — `anticoagulation` y `aspirin` **no tienen objetivo común**: la fisiología no empeora, el peligro vive sólo en la puntuación |
| GI: norepinefrina en lugar de volumen | enmascarar la hipovolemia | **`MISSING_PHYSIOLOGIC_MECHANISM`** — sin escritor de vasopresor; TD-130 (8) ya lo declara |
| Edema: suero salino en congestión | empeorar la congestión | **`PHYSIOLOGICALLY_SUPPORTED_DANGER`** en potencia: el fluido **sí** tiene objetivo común (V → precarga → congestión), pero el adaptador de edema **no mapea fluido**, así que hoy no se ejerce |
| Opioide: no ventilar | hipoventilación mantenida | **`PHYSIOLOGICALLY_SUPPORTED_DANGER` a medias**: la FR cae de verdad (−26 % en 60 min) y la naloxona lo revierte; pero **la consecuencia en SpO₂ no aparece** (§8.1), así que el peligro está soportado en su canal y no en su observable |
| ACS: reperfusión retrasada | más miocardio perdido | **`PHYSIOLOGICALLY_SUPPORTED_DANGER`** — medido a 180 min: abrir al minuto 60 deja la sistólica en 100,3 y abrir al 120 en 95,5, con medias de curso 99,75 contra 95,23 |
| PE: fluido en fallo derecho | descompensar el ventrículo derecho | **`MISSING_PHYSIOLOGIC_MECHANISM`** — la batería lo marca (`EXCESS_HARM`) y el adaptador PE no mapea fluido |

**No se añadió daño a ninguna familia para justificar una regla de puntuación.** Donde el peligro es sólo una
etiqueta, se dice.

## §11 (P3-114) Suite de causalidad entre familias

`test_management_causality.py`, **13 pruebas, 13 aprobadas en 36 s**. Usa sólo casos certificados y **no puntúa
contra curvas del legado**.

| | GI | ACS | Opioide |
|---|---|---|---|
| `DIRECTION_PASS` | ✔ (cristaloide, sangre, fuente, paquete) | ✔ (reperfusión) | ✔ (naloxona) |
| `TEMPORALITY_PASS` | ✔ tolerancia 0 | ✔ arranque exacto en el minuto del motor | ✔ arranque exacto en la orden |
| `CAUSAL_TARGET_PASS` | ✔ | ✔ (oxígeno sin beneficio de bomba) | ✔ (oxígeno no corrige la hipoventilación) |
| `DOSE_ORDER_PASS` | ✔ (1, 2, 4 unidades) | `NOT_APPLICABLE` | `NOT_APPLICABLE` (dosis fija) |
| `WAIT_COST_PASS` | ✔ **en la integral** | ✔ **en la integral y en el punto final** | `NOT_APPLICABLE` |
| `NO_PARADOX_PASS` | ✔ | ✔ | ✔ |
| `BOUNDARY_PASS` | ✔ cero fallos del núcleo | ✔ | ✔ |
| `REPLAY_PASS` | ✔ (ya certificado en P3-49) | — no `live` | — no `live` |

**Ninguna región de desarrollo nueva hizo falta**: todas las magnitudes salieron de puntos ya comprometidos o
de regiones ya cerradas. Es el resultado preferible — no inventé ninguna banda.

## §12 Revisión adversarial

| Ataque | Veredicto |
|---|---|
| «La reperfusión funciona porque elegí el minuto» | **`ROBUST`**: el minuto es `family_state["reperfusion_at"]`, que el motor calcula con su puerta-balón. No lo elijo |
| «El oxígeno de ACS mejora la presión, luego da beneficio de bomba» | **`UNSUPPORTED`**: medido, la **baja** 1,2–1,8 mmHg, por menos impulso simpático, y cinco veces menos que la reperfusión |
| «La naloxona se ajustó para que saliera bien» | **`ROBUST`**: su tasa es la comprometida de P2U-1, `SYNTHETIC_ONLY`; este mapeo no la toca |
| «El coste de esperar se eligió la métrica que convenía» | **`WEAK`, y declarado**: sí cambié de métrica, **después** de que la primera (un minuto tardío) fallara — y la razón es física y está dicha: el tratamiento es transitorio. El punto final **se reporta también**, y favorece al tardío |
| «Cerrar GI numéricamente es conveniente» | **`WEAK`**: el cierre lo pidió la docencia en este mismo encargo; lo que yo aporto es la comprobación de las diez propiedades, y la ambigüedad `tasa·ν` queda **sin resolver y declarada** |
| «Encender el enlace alveolar habría cerrado dos familias» | **`ROBUST`**: y no lo encendí, porque da SpO₂ 25 % — el encargo prohíbe la magnitud imposible aunque mejore el ajuste |
| «Los huecos re-claveados esconden que nada se implementó» | **`UNSUPPORTED`**: dos familias ganaron su intervención definitoria, y el re-claveo **aumenta** lo que el registro declara, no lo reduce |

## §13 (P3-115) Punto de control de generalización

| Familia | Estado |
|---|---|
| **GI hemorragia** | **`MANAGEMENT_CAUSALITY_READY`** |
| **ACS / cardiogénico** | **`READY_WITH_ONE_MINIMUM_GAP`** — la reperfusión es causal; el resto exige mecanismo nuevo |
| **Opioide** | **`READY_WITH_ONE_MINIMUM_GAP`** — la naloxona es causal; falta el final de la cadena a la SpO₂ |
| **Edema pulmonar** | **`MULTIPLE_GAPS`** — región de magnitud ausente **y** extensión de contrato |
| **Asma** | **`MULTIPLE_GAPS`** — dos escritores diferidos **y** el mismo final de cadena |
| **Embolia pulmonar** | **`STRUCTURAL_COMMON_MECHANISM_MISSING`** — sin parámetro de tratamiento |

**¿Cuántas familias mecanísticamente distintas demuestran hoy que el manejo del residente cambia al paciente por
el camino causal previsto?** **Tres**: hemorragia GI (volumen y control de la fuente), ACS (reperfusión del
flujo coronario) y opioide (reversión del impulso central). Son tres mecanismos **distintos** —pérdida de
volumen, obstrucción de flujo, depresión central—, no tres variantes del mismo.

> ### Veredicto P3-115
> **`B · ONE_MORE_MANAGEMENT_PACKAGE_REQUIRED`**
>
> No es **A** porque tres de seis familias no demuestran todavía su intervención definitoria, y una de ellas
> (PE) no puede sin mecanismo nuevo. No es **C** porque no son «varios escritores» lo que falta en el camino
> corto: edema necesita **una** extensión de contrato más **una** región, y eso es un paquete. No es **D**
> porque el mecanismo común que falta —el enlace hipoventilación → oxigenación— **existe, está certificado y
> está apagado**: lo que falta es una decisión de magnitud, no una extensión estructural.

## §14 (P3-116) Hoja de ruta

Los huecos, ordenados por impacto educativo × generalización mecanística ÷ coste, con la seguridad como filtro:

1. **La fracción de transmisión del enlace hipoventilación → oxigenación.** Decisión **docente**, coste de
   implementación casi nulo (el mecanismo está certificado y el perfil lo da el adaptador), y **cierra la cadena
   en dos familias a la vez** (opioide y asma). Es el paso de mayor rendimiento del repositorio ahora mismo.
   Pregunta: «con una frecuencia respiratoria de 4–5 por minuto y una mecánica normal, ¿a qué SpO₂ debería caer
   este paciente en una hora?» — un rango, no un valor.
2. **La extensión del contrato del adaptador** para tratamientos que son parámetros del escritor de enfermedad,
   más la región de descongestión. Cierra **edema** (diurético y nitrato), y es trabajo de Fase 3 que no toca el
   núcleo. Un paquete.
3. **El broncodilatador del asma** sobre `mechanics_efficiency`, si la docencia levanta
   `BRONCHODILATOR_WRITER_DEFERRED`.
4. **VNI / soporte ventilatorio**: exige encender el reclutamiento de P2K-3. Afecta a tres familias; decisión
   estructural.
5. **Antiagregante, anticoagulación y vasopresor**: fisiología nueva y decisión clínica (TD-130 (8)). Es lo que
   bloquea una primera autoridad hemodinámica en GI.
6. **PE**: exige semántica de progresión de la enfermedad. El más caro y el último.

**El primer piloto no se toca**, y nada de esto pide tocarlo.

---

## §15 Decisiones de desarrollo tomadas

**Ninguna `DEVELOPMENT_CLINICAL_CANDIDATE` ni `DEVELOPMENT_CLINICAL_REGION` fue necesaria.** Las dos
intervenciones implementadas usan valores **ya comprometidos** (la tasa de naloxona de P2U-1) o **el reloj del
propio motor** (la puerta-balón de la reperfusión), así que no hubo ninguna magnitud que elegir. Es el resultado
preferible y se declara como tal: no se inventó ninguna banda.

**La decisión que sí se tomó fue NO tomar una**: no encender el enlace alveolar, por magnitud indefendible
(§8.1), con confianza **por debajo de 0,80** en cualquier fracción concreta y la falsación explícita — si la
docencia nombra un rango de SpO₂ para una hipoventilación de 4–5 por minuto, la fracción sale de ahí y la
decisión se revisa.
