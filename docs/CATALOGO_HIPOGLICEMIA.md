# Catálogo de hipoglicemia

> Generado por `tools_hypoglycemia_catalog.py` desde `hypoglycemia_catalog.py`, `hypoglycemia_battery.py` y `corrections_registry.py`. No se edita a mano.
> Catálogo 1.0.0 · batería 1.0 · mecanismo de glucosa 1.0 · declaraciones de evaluación 1.1.

Autorización docente del 2026-09-25, etapas 0–2. Las tres variantes del banco se expresan mediante el catálogo y el catálogo compone las otras nueve combinaciones de sus tres ejes. **Las nueve composiciones no se ofrecen a residentes**: sólo un docente o un administrador las abre, en el sandbox, para revisarlas.

Tres estados que no se mezclan:

- **Compatible**: cumple las relaciones del catálogo, pasa el contrato de los casos del banco, sus declaraciones de evaluación son alcanzables y se lanza en el motor real.
- **Probado**: la batería lo jugó en el motor real con acciones estructuradas y ninguna comprobación técnica encontró un defecto técnico. Una comprobación que choca con una decisión clínica pendiente no se cuenta como defecto ni como aprobada: se muestra aparte, con su decisión. Describe una cobertura concreta —los guiones y comprobaciones de abajo— y no equivale a validado. No prueba el lenguaje libre.
- **Revisado clínicamente**: sólo lo produce la acción registrada de un docente identificado, sobre una versión; se registra en la aplicación (panel del sandbox docente), no en este documento. Este documento no atribuye ninguna revisión.

## Resumen

| Combinaciones | Del banco | En revisión | Compatibles | Probadas | Defectos técnicos | Con decisión clínica pendiente |
|---|---|---|---|---|---|---|
| 12 | 3 | 9 | 12 | 12 | 0 | 8 |

## Ejes

- **Mecanismo** (`mechanism`): `insulin` Insulina; `sulfonylurea` Sulfonilurea; `alcohol_fasting` Alcohol y ayuno.
- **Acceso venoso** (`iv_access`): `working` Vía funcionante; `failed` Vía fallida.
- **Gravedad** (`severity`): `severe` Severa: glucosa bajo el umbral de convulsión del motor; `moderate` Moderada: glucosa en la banda somnolienta del motor.
- Bandas de gravedad, derivadas de los umbrales del motor (`glucose_rescue`): severa [25, 40) mg/dL; moderada [45, 70) mg/dL, con 52 mg/dL en las composiciones. Son bandas del simulador, no una clasificación clínica.

## Condiciones que el motor ya ejecuta

| Condición | Qué significa | Dónde vive | Decide el caso |
|---|---|---|---|
| `sulfonylurea_effect` | Efecto de sulfonilurea: la glucosa vuelve a caer hasta que el octreótido lo detiene | glucose_rescue.drift_per_min, glucose_rescue.octreotide_active | sí |
| `endogenous_insulin` | Secreción propia de insulina: una sobrecorrección sobre 200 mg/dL provoca un rebote | glucose_rescue.step (rebote tras sobrecorrección) | sí |
| `glycogen_depleted` | Reservas de glucógeno agotadas: el glucagón moviliza poco | glucose_rescue.treatment_gain (glucagón al 30 %) | sí |
| `thiamine_deficient` | Déficit probable de tiamina: segundo objetivo del manejo | sin efecto fisiológico (decisión docente 8, 2026-09-21); oportunidad de evaluación | sí |
| `iv_access_failed` | La vía con que llega no está en la vena: de la glucosa en bolo que se da por ella llega el 15 % (el alcance de la decisión 8; DC4) | glucose_rescue.delivered_share; family_engine (vascular_access) | sí |
| `diabetes` | Diabetes declarada en la historia | relato (historia y comorbilidades) | no |
| `arrival_glucose` | Glucosa al llegar (mg/dL) | family_engine._initialize (glucosa basal) | no |
| `arrival_mental_status` | Estado de conciencia autorado al llegar | estado observable autorado al llegar | no |

## Compatibilidades · Necesaria para la coherencia del modelo

| | Regla | Por qué |
|---|---|---|
| N1 | La sulfonilurea es el mecanismo si y sólo si el caso trae su efecto (la glucosa que vuelve a caer). | El motor representa la sulfonilurea sólo por ese efecto (recurrence_risk). |
| N2 | Una sulfonilurea supone secreción propia de insulina. | Actúa liberando la insulina del propio paciente; sin ella no tendría sobre qué actuar. |
| N3 | La hipoglicemia por alcohol y ayuno supone glucógeno agotado. | Es la definición del mecanismo: sin reservas agotadas el alcohol solo no la produce. |
| N4 | El eje de acceso venoso y el estado de vía fallida del motor coinciden. | El eje es el estado del motor, no una etiqueta aparte. |
| N5 | La gravedad es la banda del motor en que cae la glucosa de llegada. | Las bandas se derivan de los umbrales de glucose_rescue; no se reescriben. |
| N6 | Si hay efecto de sulfonilurea, el fármaco se nombra entre los medicamentos. | Descubribilidad: la misma regla que la compuerta de los casos generados. |
| N7 | Si hay déficit de tiamina, la historia dice el alcohol o el ayuno. | Descubribilidad: la misma regla que la compuerta de los casos generados. |
| N8 | Si el glucógeno está agotado, la historia dice los días sin comer. | Descubribilidad: el residente puede saber por qué el glucagón moviliza poco. |
| N9 | Un paciente que no está alerta tiene una fuente colateral para la historia. | La misma exigencia que el banco verifica en todos sus casos. |

## Compatibilidades · Supuesto particular de una configuración

| | Regla | Por qué |
|---|---|---|
| A1 | El tipo de diabetes se declara en cada configuración; no se deduce del mecanismo. | Una insulina o una sulfonilurea pueden aparecer sin diabetes (exposición accidental o facticia). |
| A2 | Las reservas de glucógeno se declaran en cada configuración; la diabetes tipo 1 no las fija. | Un paciente con tipo 1 que lleva días sin comer puede tenerlas agotadas: es una condición del escenario. |
| A3 | El déficit de tiamina se declara en cada configuración; el alcohol no lo impone. | Es un riesgo, no una certeza: una configuración de alcohol y ayuno puede no tenerlo. |

## Compatibilidades · Simplificación pendiente de revisión clínica

| | Regla | Por qué |
|---|---|---|
| S1 | En diabetes tipo 1 no hay secreción propia de insulina (se ignora la secreción residual). | Simplificación del modelo; pendiente de revisión clínica. |

## Parámetros del motor usados como referencia técnica

La batería los usa como referencia, nunca como criterio para juzgar a un residente, estén revisados o no. La última columna dice lo que el repositorio registra de cada uno: una magnitud revisada es un parámetro docente del simulador, no un criterio de evaluación. Sin revisión registrada: P5, P10, P11. Las preguntas están en `docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md`.

| | Parámetro | Valor actual | Revisión |
|---|---|---|---|
| P1 | `glucose_rescue.drift_per_min` | Caída espontánea de 0,08 mg/dL/min, igual para toda insulina y toda dosis; 0,6 mg/dL/min con sulfonilurea hasta el octreótido. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P2 | `glucose_rescue.SEIZURE_GLUCOSE, SEIZURE_AFTER_MIN, POST_ICTAL_MIN` | Convulsión tras 20 minutos acumulados bajo 40 mg/dL; el reloj se reinicia al subir de 40; 10 minutos postictales. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P3 | `glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE` | La conciencia depende sólo de la glucosa: alerta ≥70, somnoliento 45–69, obnubilado 25–44, sin respuesta <25. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P4 | `family_engine._minute (4 mg/dL por gramo, 10 g por minuto)` | Una ampolla de 25 g sube la glucosa unos 100 mg/dL en unos 3 minutos. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P5 | `glucose_rescue.GLUCAGON_*, GLYCOGEN_*, DEPLETED_GLYCOGEN_SHARE` | Glucagón: inicio a los 10 min, 1,6 mg/dL/min por 25 min; la segunda dosis moviliza la mitad y la tercera nada; con glucógeno agotado, 30 %. | Pendiente de revisión. La cinética y las dosis repetidas se revisaron el 2026-09-20; el 30 % con glucógeno agotado se implementó con la decisión 8 (docs/DECISIONES_3_4_8_MAGNITUDES.md) y esa magnitud no tiene revisión registrada. |
| P6 | `glucose_rescue.ORAL_*` | Carbohidrato oral sólo si está alerta: inicio a los 5 min, 1,2 mg/dL/min por 25 min. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P7 | `glucose_rescue.INFUSION_G_PER_ML` | Glucosado al 10 %: 100 mL/h suman 0,67 mg/dL/min. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P8 | `glucose_rescue.REBOUND_*` | Con secreción propia, una glucosa sobre 200 provoca a los 30 min una caída extra de 0,8 mg/dL/min hasta bajar de 100. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P9 | `glucose_rescue.OCTREOTIDE_*` | Octreótido de 25 a 500 mcg: inicio a los 15 min, dura 360 min y detiene por completo la caída de la sulfonilurea. | Magnitud revisada. Revisada por la facultad el 2026-09-20 como magnitud docente (docs/HYPOGLYCEMIA_MAGNITUDES.md). |
| P10 | `glucose_rescue.FAILED_ACCESS_SHARE, delivered_share` | Vía fallida: de la glucosa en bolo por vía endovenosa o intraósea llega el 15 % hasta que se instala una vía nueva; la infusión al 10 %, el glucagón, el octreótido y la tiamina endovenosos pasan enteros por ella (el alcance de la decisión 8). | Pendiente de revisión. El 15 % y el alcance se implementaron con la decisión 8 (docs/DECISIONES_3_4_8_MAGNITUDES.md); la magnitud no tiene revisión registrada y el alcance es la decisión pendiente DC4. |
| P11 | `family_engine._discharge_alarm, DISCHARGE_RETURN_DELAY_MIN` | Tras un alta, una glucosa bajo 60 hace que el paciente vuelva 20 minutos después. | Pendiente de revisión. El principio es de las decisiones docentes 1 y 2 del 2026-09-21 (un alta con el problema en curso trae de vuelta al paciente); el umbral de 60 mg/dL y los 20 minutos no tienen revisión registrada. |
| P12 | `decisión docente 8 (2026-09-21)` | La tiamina no despierta al paciente ni su ausencia lo deteriora. | Decisión docente, sin magnitud. Decisión docente 8 (2026-09-21); no tiene magnitudes propias. |

## Las doce combinaciones

| Configuración | Origen | Mecanismo · acceso · gravedad | Glucosa y conciencia al llegar | Condiciones | Compatible | Probado | Referencias | Pendiente |
|---|---|---|---|---|---|---|---|---|
| `hypoglycemia_28m` | banco | Insulina · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor | 34 mg/dL, Drowsy | — | sí | sí (6/7 técnicas; 1 en decisión pendiente) | 6/6 | DC1 |
| `hypoglycemia_76f` | banco | Sulfonilurea · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor | 38 mg/dL, Obtunded | `sulfonylurea_effect`, `endogenous_insulin` | sí | sí (8/8 técnicas) | 9/9 | — |
| `hypoglycemia_54m_thiamine` | banco | Alcohol y ayuno · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor | 32 mg/dL, Drowsy | `endogenous_insulin`, `glycogen_depleted`, `thiamine_deficient`, `iv_access_failed` | sí | sí (10/12 técnicas; 2 en decisión pendiente) | 6/6 | DC1, DC4 |
| `hypoglycemia_cfg_insulin_working_moderate` | en revisión | Insulina · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | — | sí | sí (7/7 técnicas) | 5/5 | — |
| `hypoglycemia_cfg_insulin_failed_severe` | en revisión | Insulina · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor | 34 mg/dL, Drowsy | `iv_access_failed` | sí | sí (9/11 técnicas; 2 en decisión pendiente) | 5/5 | DC1, DC4 |
| `hypoglycemia_cfg_insulin_failed_moderate` | en revisión | Insulina · Vía fallida · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | `iv_access_failed` | sí | sí (10/11 técnicas; 1 en decisión pendiente) | 5/5 | DC4 |
| `hypoglycemia_cfg_sulfonylurea_working_moderate` | en revisión | Sulfonilurea · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | `sulfonylurea_effect`, `endogenous_insulin` | sí | sí (8/8 técnicas) | 8/8 | — |
| `hypoglycemia_cfg_sulfonylurea_failed_severe` | en revisión | Sulfonilurea · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor | 38 mg/dL, Obtunded | `sulfonylurea_effect`, `endogenous_insulin`, `iv_access_failed` | sí | sí (11/12 técnicas; 1 en decisión pendiente) | 8/8 | DC4 |
| `hypoglycemia_cfg_sulfonylurea_failed_moderate` | en revisión | Sulfonilurea · Vía fallida · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | `sulfonylurea_effect`, `endogenous_insulin`, `iv_access_failed` | sí | sí (11/12 técnicas; 1 en decisión pendiente) | 8/8 | DC4 |
| `hypoglycemia_cfg_alcohol_fasting_working_severe` | en revisión | Alcohol y ayuno · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor | 32 mg/dL, Drowsy | `endogenous_insulin`, `glycogen_depleted`, `thiamine_deficient` | sí | sí (7/8 técnicas; 1 en decisión pendiente) | 7/7 | DC1 |
| `hypoglycemia_cfg_alcohol_fasting_working_moderate` | en revisión | Alcohol y ayuno · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | `endogenous_insulin`, `glycogen_depleted`, `thiamine_deficient` | sí | sí (8/8 técnicas) | 6/6 | — |
| `hypoglycemia_cfg_alcohol_fasting_failed_moderate` | en revisión | Alcohol y ayuno · Vía fallida · Moderada: glucosa en la banda somnolienta del motor | 52 mg/dL, Drowsy | `endogenous_insulin`, `glycogen_depleted`, `thiamine_deficient`, `iv_access_failed` | sí | sí (11/12 técnicas; 1 en decisión pendiente) | 6/6 | DC4 |

## Correspondencia de las tres variantes del banco

- `hypoglycemia_28m` → Insulina · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor. Condiciones: —. Supuestos de la configuración: Diabetes tipo 1, confirmada por su información de emergencia. Reservas de glucógeno no agotadas: estaba bien al empezar el turno y sólo omitió el almuerzo. Sin déficit de tiamina: ninguna exposición al alcohol ni ayuno.
- `hypoglycemia_76f` → Sulfonilurea · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor. Condiciones: `sulfonylurea_effect`, `endogenous_insulin`. Supuestos de la configuración: Diabetes tipo 2 tratada con glimepirida. Reservas de glucógeno no agotadas pese a dos días de ingesta escasa (supuesto de esta configuración). La enfermedad renal crónica está en el relato y no en el motor: la recurrencia la modela sólo el efecto de la sulfonilurea.
- `hypoglycemia_54m_thiamine` → Alcohol y ayuno · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor. Condiciones: `endogenous_insulin`, `glycogen_depleted`, `thiamine_deficient`, `iv_access_failed`. Supuestos de la configuración: Sin diabetes: su páncreas responde a una sobrecorrección. Déficit probable de tiamina en este paciente (supuesto de esta configuración, no una regla del alcohol). La vía con que llega no está en la vena; no se ve antes de usarla (pendiente de decisión docente).

## Preservación técnica

Comparación con el registro del 2026-09-25 (commit d184845), antes de que existiera el catálogo: el caso, su declaración de evaluación, su estado de lanzamiento y veinte guiones de acciones estructuradas en el motor real. Una coincidencia es regresión, no aceptación clínica.

| Variante | Caso | Declaración | Lanzamiento | Guiones distintos |
|---|---|---|---|---|
| `hypoglycemia_28m` | idéntico | idéntica | idéntico | ninguno de 20 |
| `hypoglycemia_76f` | idéntico | idéntica | idéntico | ninguno de 20 |
| `hypoglycemia_54m_thiamine` | `/faculty/discriminating_findings`, `/faculty/management_focus`, `/faculty/review_questions` | nueva versión (cobertura 1.1) | idéntico | ninguno de 20 |

Cada diferencia está declarada en el registro de correcciones; la prueba `test_hypoglycemia_preservation` acepta esas y ninguna otra.

## Correcciones intencionales

| | Corrección | Alcance | Tipo | Relevancia clínica | Versiones |
|---|---|---|---|---|---|
| C-2026-09-25-01 | Las tres variantes de hipoglicemia se expresan mediante el catálogo | familia hypoglycemia | refactor | none | catalog — → hypoglycemia 1.0.0 |
| C-2026-09-25-02 | Umbrales de conciencia y pistas del mecanismo de glucosa en un solo lugar | general | refactor | none | — |
| C-2026-09-25-03 | El foco docente de hypoglycemia_54m_thiamine contradecía la decisión 8 | variante hypoglycemia_54m_thiamine | text | clinical | catalog — → hypoglycemia 1.0.0 |
| C-2026-09-25-04 | Lo que la vía fallida agrega al texto docente de cada caso | familia hypoglycemia | text | clinical | — |
| C-2026-09-25-05 | hypo_no_thiamine deja de ser un evento crítico; nueva versión de las declaraciones (cobertura 1.1) | familia hypoglycemia | clinical_decision_applied | clinical | coverage 1.0 → 1.1 |
| C-2026-09-25-06 | Abrir la rúbrica o el análisis de un caso generado no interrumpe el circuito | general | technical_defect | none | — |
| C-2026-09-25-07 | Las declaraciones de evaluación se congelan con cada encuentro | general | technical_defect | none | — |
| C-2026-09-25-08 | Sin configuración explícita, sólo el administrador inicia una generación libre | general | policy | none | — |
| C-2026-09-25-09 | El lector: la infusión al 10 % en español y la glucosa escrita como solución | general | technical_defect | clinical | — |
| C-2026-09-26-01 | El panel de la rúbrica conserva sus botones, la telaraña su etiqueta superior y el rechazo nombra el evento | general | technical_defect | none | — |
| C-2026-09-26-02 | «My progress» reconstruye el Management Trace del residente desde el análisis guardado | general | technical_defect | none | — |
| C-2026-09-26-03 | El lector: órdenes de glucosa, vías e interconsultas escritas como en una ficha | general | technical_defect | clinical | — |
| C-2026-09-26-04 | La página docente pregunta menos a la base: de 20 a 12 transacciones por cambio en la rúbrica | general | refactor | none | — |

## La batería, configuración por configuración

Técnicas (T): el motor hace lo que el modelo dice; una falla es un defecto técnico, salvo que su arreglo exija una decisión clínica. Referencias (R): tiempos y magnitudes de los parámetros actuales, pendientes de revisión; se conservan para notar un cambio, no son criterios.

### `hypoglycemia_28m`

Insulina · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: infusión sin ampolla en una hipoglicemia severa (error frecuente); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 34 → 133 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 133 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 133 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | sin rebote sin secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ❌ (decisión clínica pendiente DC1) | llega 'Drowsy'; con 34 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 133 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 131 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | — | sin rebote en esta configuración | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |
| R9 | Una infusión sin ampolla no corrige una hipoglicemia severa | ✅ | 52 mg/dL tras 30 minutos de infusión sin ampolla | P7 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas.

### `hypoglycemia_76f`

Sulfonilurea · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: octreótido en vez de infusión (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: alta tras la primera ampolla (error frecuente); Recuperación: al volver, ampolla, infusión y hospitalización (recuperación); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: infusión sin ampolla en una hipoglicemia severa (error frecuente); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 37 → 131 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 132 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 131 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.60 mg/dL/min sin mantención | — |
| T10 | El octreótido detiene la caída de la sulfonilurea | ✅ | cae 0.08 mg/dL/min con octreótido activo | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Obtunded'; con 38 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 131 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 113 mg/dL | P2, P3, P4 |
| R5 | Dada de alta tras la primera ampolla, vuelve | ✅ | vuelve tras el alta | P1, P11 |
| R6 | Al volver, ampolla e infusión la mantienen sobre 70 | ✅ | mínimo 159 mg/dL tras hospitalizarla | P1, P7 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 1.45 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |
| R9 | Una infusión sin ampolla no corrige una hipoglicemia severa | ✅ | 40 mg/dL tras 30 minutos de infusión sin ampolla | P7 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas.

### `hypoglycemia_54m_thiamine`

Alcohol y ayuno · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: la misma corrección sin tiamina (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación); Error: tiamina sin glucosa (error frecuente).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 32 → 131 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 131 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 14.2 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 145 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 131 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T11 | La tiamina no despierta al paciente ni su ausencia lo deteriora (decisión 8) | ✅ | con tiamina Alert, sin tiamina Alert; la tiamina sola no cambia la conciencia | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ❌ (decisión clínica pendiente DC1) | llega 'Drowsy'; con 32 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 124 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 129 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 0.91 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 5.3 mg/dL en 20 minutos sin glucógeno (los parámetros dicen 5.3) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3).

### `hypoglycemia_cfg_insulin_working_moderate`

Insulina · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 52 → 151 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 151 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 151 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | sin rebote sin secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 151 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 149 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | — | sin rebote en esta configuración | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_insulin_failed_severe`

Insulina · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 34 → 133 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 133 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 14.2 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 147 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 133 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | sin rebote sin secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ❌ (decisión clínica pendiente DC1) | llega 'Drowsy'; con 34 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 133 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 131 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | — | sin rebote en esta configuración | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3). Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_insulin_failed_moderate`

Insulina · Vía fallida · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 52 → 151 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 151 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 14.2 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 165 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 151 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | sin rebote sin secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 151 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 149 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | — | sin rebote en esta configuración | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3). Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_sulfonylurea_working_moderate`

Sulfonilurea · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: octreótido en vez de infusión (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: alta tras la primera ampolla (error frecuente); Recuperación: al volver, ampolla, infusión y hospitalización (recuperación); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 51 → 145 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 146 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 145 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.60 mg/dL/min sin mantención | — |
| T10 | El octreótido detiene la caída de la sulfonilurea | ✅ | cae 0.08 mg/dL/min con octreótido activo | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 145 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 127 mg/dL | P2, P3, P4 |
| R5 | Dada de alta tras la primera ampolla, vuelve | ✅ | vuelve tras el alta | P1, P11 |
| R6 | Al volver, ampolla e infusión la mantienen sobre 70 | ✅ | mínimo 173 mg/dL tras hospitalizarla | P1, P7 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 1.45 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_sulfonylurea_failed_severe`

Sulfonilurea · Vía fallida · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: octreótido en vez de infusión (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: alta tras la primera ampolla (error frecuente); Recuperación: al volver, ampolla, infusión y hospitalización (recuperación); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 37 → 131 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 132 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 9.0 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 140 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 131 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.60 mg/dL/min sin mantención | — |
| T10 | El octreótido detiene la caída de la sulfonilurea | ✅ | cae 0.08 mg/dL/min con octreótido activo | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Obtunded'; con 38 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 131 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 113 mg/dL | P2, P3, P4 |
| R5 | Dada de alta tras la primera ampolla, vuelve | ✅ | vuelve tras el alta | P1, P11 |
| R6 | Al volver, ampolla e infusión la mantienen sobre 70 | ✅ | mínimo 159 mg/dL tras hospitalizarla | P1, P7 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 1.45 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3). Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_sulfonylurea_failed_moderate`

Sulfonilurea · Vía fallida · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: octreótido en vez de infusión (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: alta tras la primera ampolla (error frecuente); Recuperación: al volver, ampolla, infusión y hospitalización (recuperación); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 51 → 145 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 146 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 9.0 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 154 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 145 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.60 mg/dL/min sin mantención | — |
| T10 | El octreótido detiene la caída de la sulfonilurea | ✅ | cae 0.08 mg/dL/min con octreótido activo | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 145 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 127 mg/dL | P2, P3, P4 |
| R5 | Dada de alta tras la primera ampolla, vuelve | ✅ | vuelve tras el alta | P1, P11 |
| R6 | Al volver, ampolla e infusión la mantienen sobre 70 | ✅ | mínimo 173 mg/dL tras hospitalizarla | P1, P7 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 1.45 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 17.6 mg/dL en 20 minutos con glucógeno (los parámetros dicen 17.6) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3). Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_alcohol_fasting_working_severe`

Alcohol y ayuno · Vía funcionante · Severa: glucosa bajo el umbral de convulsión del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: la misma corrección sin tiamina (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: infusión sin ampolla en una hipoglicemia severa (error frecuente); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación); Error: tiamina sin glucosa (error frecuente).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 32 → 131 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 131 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 131 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T11 | La tiamina no despierta al paciente ni su ausencia lo deteriora (decisión 8) | ✅ | con tiamina Alert, sin tiamina Alert; la tiamina sola no cambia la conciencia | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ❌ (decisión clínica pendiente DC1) | llega 'Drowsy'; con 32 mg/dL el motor muestra 'Obtunded' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 124 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | convulsión al minuto 20 | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 129 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 0.91 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 5.3 mg/dL en 20 minutos sin glucógeno (los parámetros dicen 5.3) | P5 |
| R9 | Una infusión sin ampolla no corrige una hipoglicemia severa | ✅ | 50 mg/dL tras 30 minutos de infusión sin ampolla | P7 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_alcohol_fasting_working_moderate`

Alcohol y ayuno · Vía funcionante · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: la misma corrección sin tiamina (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación); Error: tiamina sin glucosa (error frecuente).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 52 → 151 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 151 mg/dL a los 10 minutos | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 151 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T11 | La tiamina no despierta al paciente ni su ausencia lo deteriora (decisión 8) | ✅ | con tiamina Alert, sin tiamina Alert; la tiamina sola no cambia la conciencia | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 144 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 149 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 0.91 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 5.3 mg/dL en 20 minutos sin glucógeno (los parámetros dicen 5.3) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

### `hypoglycemia_cfg_alcohol_fasting_failed_moderate`

Alcohol y ayuno · Vía fallida · Moderada: glucosa en la banda somnolienta del motor. Guiones: Glucosa capilar, ampolla por una vía que llega, mantención y destino (manejo adecuado); Alternativa: vía nueva antes de la primera dosis (manejo adecuado); Alternativa: la misma corrección sin tiamina (manejo adecuado); Alternativa: glucagón intramuscular sin usar la vía fallida (manejo adecuado); 25 minutos sin nada que suba la glucosa, luego el manejo adecuado (demora); Error: ampolla por la vía con que llegó, sin revisarla (error frecuente); Recuperación: tras la ampolla que no llegó, vía nueva y ampolla (recuperación); Error: infusión por la vía fallida (error frecuente); Error: doble ampolla (error frecuente); Glucagón intramuscular como única medida (error frecuente); Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos (demora); Error: carbohidrato oral a un paciente que no está alerta (error frecuente); Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega (recuperación); Error: tiamina sin glucosa (error frecuente).

| | Comprobación | Resultado | Observado | Parámetros |
|---|---|---|---|---|
| T1 | Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL | ✅ | 52 → 151 mg/dL tras la ampolla por una vía que llega | — |
| T2 | Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida) | ✅ | 151 mg/dL a los 10 minutos | — |
| T3 | La primera dosis por la vía fallida se informa como no llegada | ✅ | el motor dice que la glucosa no pasa | — |
| T4 | Por la vía fallida llega sólo la fracción del modelo | ✅ | sube 14.2 mg/dL; el 15% de la ampolla son 15 | — |
| T5 | Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene) | ❌ (decisión clínica pendiente DC4) | en 30 minutos aporta 20.0 mg/dL; entera aportaría 20 y por la vía fallida 3 | — |
| T6 | Tras reconocer la vía fallida, la vía nueva corrige la glucosa | ✅ | 165 mg/dL tras la vía nueva | — |
| T7 | La vía oral se rechaza a un paciente que no está alerta | ✅ | rechazado | — |
| T13 | Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa | ✅ | tras el rechazo, 151 mg/dL y Alert | — |
| T8 | El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina | ✅ | rebote con secreción propia | — |
| T9 | Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea | ✅ | cae 0.08 mg/dL/min sin mantención | — |
| T11 | La tiamina no despierta al paciente ni su ausencia lo deteriora (decisión 8) | ✅ | con tiamina Alert, sin tiamina Alert; la tiamina sola no cambia la conciencia | — |
| T12 | El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1 | ✅ | llega 'Drowsy'; con 52 mg/dL el motor muestra 'Drowsy' desde el primer minuto | — |
| R1 | Alerta a los 10 minutos de una ampolla efectiva | ✅ | Alert a los 10 minutos de la ampolla | P3, P4 |
| R2 | Con la mantención de su mecanismo no vuelve a bajar de 70 | ✅ | mínimo 144 mg/dL en las dos horas siguientes | P1, P6, P7, P9 |
| R3 | Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25 | ✅ | sin convulsión en 25 minutos | P1, P2 |
| R4 | Alerta a los 15 minutos de tratarla tras la demora | ✅ | a los 42 min: Alert, 149 mg/dL | P2, P3, P4 |
| R7 | La sobrecorrección se paga con una caída de 0,8 mg/dL/min | ✅ | cae 0.91 mg/dL/min tras el rebote | P8 |
| R8 | El glucagón moviliza poco sin glucógeno y bastante con él | ✅ | efecto de 5.3 mg/dL en 20 minutos sin glucógeno (los parámetros dicen 5.3) | P5 |

Sin observar: Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte. Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor). Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas. Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2). El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance que dejó la decisión 8 (DC4). La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3). Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.

## Revisarlas en desarrollo

1. Entrar con una cuenta docente o de administrador a la aplicación de desarrollo.
2. En el sandbox docente elegir el desafío R1-06 o R1-07 (los que incluyen hipoglicemia).
3. En «Case to open (faculty review)» elegir la configuración. Se abre sin generación y sin imagen pagadas, como encuentro de sandbox, fuera del progreso de los residentes.
4. En «Clinical review of the hypoglycemia catalogue (faculty)» registrar la decisión y una nota. La revisión queda atada a la versión de la configuración; un cambio clínicamente relevante posterior la marca como desactualizada.

