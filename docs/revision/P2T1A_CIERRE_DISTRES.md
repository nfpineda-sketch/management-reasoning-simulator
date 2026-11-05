# P2T-1A · Cierre semántico y numérico del distrés respiratorio

Paquete de mantenimiento pequeño, en sombra. Sólo resuelve los dos puntos autorizados de la revisión de P2T-1: M1 y L1.
No cambia ninguna otra fisiología, no migra el asma ni calibra nada. Rama `phase-2-clinical-core-shadow`; base `851a835`
(P2T-1 aceptado y cerrado como `COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_READY`).

- Núcleo: `clinical_core/derived.py` (la guarda M1) e `integration.py` (la suma L1), más las dos tuplas de registro.
- Análisis: `clinical_core/distress_closure.py`, congelado antes de la única evaluación.
- Registro: `docs/revision/P2T1A_distress_closure.json`. Este documento se genera desde el registro
  (`clinical_core/distress_closure_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- **M1, opción 1 — `DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT`.**
  - Con un distrés mayor que 0 y el lector respiratorio activo, la mecánica respiratoria común de P2S-2 (W) también tiene
    que estar activa.
  - Se rechaza en la llegada, cuando un escritor lo hace subir durante la evolución y en cualquier estado que llegue a la
    composición del impulso.
  - No se rechazan el lector simpático solo, un distrés de 0 ni el comportamiento por defecto.
  - Motivo: P2S-2 retiró el anclaje de la PaCO2 de llegada por paciente como forma de representar la mecánica. Con la
    mecánica apagada, el efecto del distrés sobre la FR movería la PaCO2 por esa vía obsoleta, lejos de la verdad autoral.
- **M1, opción 2 — `DISTRESS_IN_ANCHOR = REJECTED`.** El distrés no entra en el ancla de PaCO2 de llegada de P2K-2, no se
  recalcula una PaCO2 de referencia por caso para absorberlo y no se restaura el anclaje por paciente.
- **L1, sólo precisión numérica.** La suma del minuto es un único `math.fsum`. Un negativo que no se distingue de 0 a la
  escala de redondeo de las operaciones hechas queda en 0 exacto; un negativo material se rechaza como antes. Sin épsilon
  clínico ni umbral fisiológico.
- El registro de P2T-1 no se vuelve a congelar.

## 2. Funciones cambiadas (auditoría)

<!-- generado:auditoria -->
- `derived.py`: funciones cambiadas `_composition`, `arrival_state`; añadidas `check_distress_respiratory_effect`; retiradas ninguna.
- `integration.py`: funciones cambiadas `_check_conservation`, `_distress_after`; añadidas `distress_sum`; retiradas ninguna.
- La guarda la llaman `_composition`, `arrival_state` (`derived.py`) y `_distress_after` (`integration.py`); lee sólo `distress`, `distress_to_respiratory_drive_gain`, `respiratory_mechanics`.
- La suma la llaman `_check_conservation`, `_distress_after`; sus constantes numéricas son `0.0`, `1.0` y sus llamadas `abs`, `math.fsum`, `math.ulp`.
- Lectores del ancla de PaCO2 de llegada: `__post_init__`, `arrival_alveolar_ventilation`, `arrival_paco2`, `respiration`; idénticos a los de P2T-1: sí. La guarda no lee ningún ancla: sí.
- Pasa: sí.
<!-- /generado:auditoria -->

## 3. M1: el efecto respiratorio del distrés exige la mecánica común

La guarda (`derived.check_distress_respiratory_effect`) lee sólo el distrés, la ganancia respiratoria y el interruptor
de la mecánica. La llaman la llegada (`arrival_state`), la composición del impulso (`_composition`, por donde pasa todo
distrés que llega a la FR) y la integración del minuto (`_distress_after`).

<!-- generado:m1 -->
- Clasificación: **DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT**; opción 2: **DISTRESS_IN_ANCHOR = REJECTED**.
- Rechazos con la mecánica apagada y distrés 5 (sintético): any_state_composition sí, arrival_both_readers sí, arrival_drive_composition sí, arrival_respiratory_reader_only sí, evolving_writer sí.

| Mapeo comprometido | Mecánica | Lector respiratorio rechazado | Sólo simpático aceptado |
|---|---|---|---|
| asthma_49m | sí | no | sí |
| pulmonary_edema_58m | no | sí | sí |
| pulmonary_embolism_33f | no | sí | sí |
| pulmonary_embolism_61m | no | sí | sí |

- Sólo el lector simpático, mecánica apagada: FC 80,00 → 86,24; FR, PaCO2, pH y W sin cambio sí; escritor en evolución 1,0, 2,0.
- Distrés 0 con ambos lectores y la mecánica apagada: lectura idéntica a la de los lectores UNSET sí; un cambio de 0 aceptado sí.
- Mecánica encendida, distrés 5: FR 20,53; la PaCO2 (31,17) es la misma con PaCO2 de llegada 30.0 y 60.0: sí; escritor en evolución 1,0, 2,0.
- Por defecto: lectores UNSET sí; llegada aceptada sí.
- Pasa: sí.
<!-- /generado:m1 -->

## 4. L1: la suma del distrés y su tolerancia de redondeo

`integration.distress_sum` suma una sola vez, con `math.fsum`, el valor con que empieza el minuto y todos sus cambios. El
orden de los cambios dentro del minuto no importa.

La cota es la del redondeo binario64 de esa operación:
- `math.ulp(1.0)` (el épsilon de la máquina) por la suma de las magnitudes de los operandos;
- cubre el redondeo de cada operando y el de la suma.

No es un número fijo: escala con los operandos, y la decisión no cambia al multiplicarlos todos por una potencia de 2.

<!-- generado:l1 -->
- Tolerancia: math.ulp(1.0) x fsum(|operands|): each operand's rounding plus the sum's (binary64).
- **A.** +0,3 −0,1 −0,2: la suma binaria da -2.78e-17; en un minuto 0, en tres 0. Pasa: sí.
- **B.** Los 6 órdenes en un minuto dan 0; 8 secuencias por minutos terminan en 0 y 10 se rechazan, exactamente las que cierran algún minuto materialmente por debajo de 0: sí. Pasa: sí.

| Caso | Suma binaria | Cota de redondeo | Decisión |
|---|---|---|---|
| C (0.3, (-0.30000000000000004,)) | -5.55e-17 | 1.33e-16 | 0 |
| C (0.7, (-0.1, -0.6)) | -2.78e-17 | 3.11e-16 | 0 |
| D (0.0, (-1e-12,)) | -1e-12 | 2.22e-28 | refused |
| D (0.0, (-1e-300,)) | -1e-300 | 2.22e-316 | refused |
| D (0.3, (-0.31,)) | -0.01 | 1.35e-16 | refused |
| D (1.0, (-1.0000000000000009,)) | -8.88e-16 | 4.44e-16 | refused |
| E (0.0, (1e-12,)) | 1e-12 | — | 1e-12 |
| E (0.0, (5e-324,)) | 4.94e-324 | — | 4.94e-324 |
| E (0.3, (-0.2999999999,)) | 1e-10 | — | 1e-10 |

- **C** pasa sí; **D** pasa sí (la integración también los rechaza); **E** pasa sí.
- **F.** Campos del perfil iguales a los de P2T-1 sí; nombres del registro de parámetros iguales sí; constantes de la suma `0.0`, `1.0`; las decisiones no cambian al escalar todo por 1.0, 1099511627776.0, 9.094947017729282e-13. Pasa: sí.
- Pasa: sí.
<!-- /generado:l1 -->

## 5. No regresión

Las sondas D1–D12 y las demás secciones de P2T-1 se ejecutan con el núcleo vivo, es decir, con la guarda activa. Para
sus propias pruebas leen las fuentes de P2T-1.

El registro de P2T-1 se reproduce sobre su propio árbol: la vista lee las dos funciones nuevas como estaban en P2T-1 (sin
guarda y con la suma sin normalizar). La prueba de reversión muestra que ésa es la única diferencia.

<!-- generado:no_regresion -->
- D1–D12 de P2T-1 en vivo (con la guarda): D1 sí, D2 sí, D3 sí, D4 sí, D5 sí, D6 sí, D7 sí, D8 sí, D9 sí, D10 sí, D11 sí, D12 sí.
- Otras secciones de P2T-1 en vivo: beta_blockade sí, observable sí, ordering sí, orthogonality sí, parameters sí, representation sí, systemic_stress sí.
- Los contrastes de P2T-1 en vivo quedan rechazados por M1 (edema y TEP con la mecánica apagada): sí.
- El registro de P2T-1 se reproduce sobre su propio árbol: sí; su digest de congelación sí; el archivo intacto sí.
- Registros de P2S-2 y P2S-3 reproducidos: sí; veredicto histórico de P2S-3 `ASTHMA_SHADOW_MIGRATION_READY`, clasificación vigente `ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_CORE_BLOCKER_FOUND (COMMON_DRIVE_GAP); P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT`.
- Perfiles comprometidos con los lectores UNSET: sí. SYSTEMIC_STRESS_DEFERRED (nothing added).
- Pasa: sí.
<!-- /generado:no_regresion -->

## 6. Prueba contra el árbol de P2T-1

Cada archivo cambiado vuelve exactamente al de `851a835` al revertir sus inserciones declaradas. Todos los demás archivos
de `clinical_core` están fijados por hash.

<!-- generado:prueba -->
- Inserciones declaradas revertidas a los archivos de P2T-1: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí.
- Archivos comunes fijados por hash: 119, intactos sí.
- Vista de P2T-1: digest de congelación sí, su prueba contra P2S-3 sí, registro sí.
<!-- /generado:prueba -->

## 7. Preparación

<!-- generado:veredicto -->
- sí — M1: the respiratory effect of a distress above 0 is refused with the mechanics candidate off, at arrival, for an evolving writer and for any state (DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT)
- sí — M1: the sympathetic reader alone, a distress of 0, the mechanics candidate on and the default are accepted
- sí — M1: no PaCO2 anchoring returns: every anchor reader is P2T-1's and the mechanics-on PaCO2 ignores the arrival PaCO2 (DISTRESS_IN_ANCHOR = REJECTED)
- sí — L1: A-F (roundoff negatives are 0 exactly in any order; material negatives refused; small positives kept; no clinical parameter or threshold; scale invariant)
- sí — only the declared functions changed (the audit; the P2T-1 files and every common file proven)
- sí — non-regression: P2T-1's D1-D12 live, its record and digest on its tree, the P2S-2 / P2S-3 records, the committed profiles UNSET, no systemic stress

**Veredicto: P2T1A_SEMANTIC_CLOSURE_READY**

M1: DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT; DISTRESS_IN_ANCHOR = REJECTED.
<!-- /generado:veredicto -->

## 8. Lo que deja este paquete

- Un distrés con efecto respiratorio sólo existe junto con la mecánica común. Las familias respiratorias que lo usen
  (asma, edema, TEP, neumonía) tendrán que leerlo con la mecánica de P2S-2 encendida.
- Los contrastes de edema y TEP de P2T-1, hechos con la mecánica apagada, quedan rechazados en vivo. Siguen en su
  registro histórico, que no cambia.
- El lector simpático no exige la mecánica: un distrés puede subir la FC sin tocar la FR ni la PaCO2.
- Un escritor de familia puede deshacer sus cambios con cantidades decimales (+0,3 −0,1 −0,2) sin que el redondeo lo haga
  fallar, dentro de un minuto o en pocas operaciones. La deriva acumulada en cursos largos todavía puede provocar un
  rechazo (§10, hallazgo 1); para cerrar un curso, el escritor puede escribir el negativo exacto del valor actual. Un
  negativo material sigue siendo un error.

## 9. Proceso

- Iteración rápida con pruebas focalizadas y una sola congelación (`c4754cb`) antes de la única evaluación.
- Los cambios del núcleo tocan dos archivos comunes y dos tuplas, y se prueban contra `851a835` por reversión.
- El arrastre a los paquetes cerrados se resolvió con el patrón de P2T-1:
  - una vista del árbol de P2T-1 (`distress_closure.chain`, `p2t1_sources`) encadenada en los 24 archivos de prueba que
    ya encadenaban la de P2S-3;
  - una vista propia en la prueba de P2T-1;
  - las listas de nombres de W y del filtro del SCA, con la nueva entrada;
  - cuatro digests de documentos regenerados.
- Primera corrida de las 62 pruebas de Fase 2 afectadas: 5 fallos, todos de esas listas y de un `import sys` innecesario,
  que se quitó en lugar de ampliar la lista de permitidos del aislamiento. Tras las correcciones pasan.
- Ninguna sonda densa ni barrido: las sondas son puntos sintéticos predeclarados.
- Tras la revisión, sólo se cambió el modo de la vista en las pruebas cerradas (hallazgo 5). Las fuentes congeladas no se tocaron y no se volvió a congelar.

## 10. Revisión adversarial

Una revisión, independiente y de sólo lectura, sobre el candidato congelado y evaluado (`c4754cb`), centrada en los cinco
puntos del encargo. Resultado: ningún hallazgo alto, 1 medio y 5 bajos. Cada uno se comprobó con una sonda. El veredicto
no cambia: ningún criterio predeclarado falla, y ningún hallazgo muestra un negativo material oculto ni un anclaje de
PaCO2 que haya vuelto.

1. **Medio (L1, alcance): la cota cubre el redondeo del minuto, no la deriva acumulada en minutos anteriores.**
   - Un escritor simétrico (+0,1 por minuto durante 30 minutos y luego −0,1 durante 30) llega al último minuto con
     0,09999999999999981 y se rechaza por −1,9e−16.
   - 13 de 35 cursos simétricos probados se rechazan.
   - Falla cerrado: no oculta nada, y P2T-1 también lo rechazaba, así que no es una regresión. Pero el objetivo de L1 (que
     el redondeo nunca provoque un rechazo) sólo queda cubierto dentro del minuto y en las secuencias del trío.
   - Cubrirlo exigiría llevar entre minutos una cota de magnitud, un campo de estado nuevo. Eso queda fuera del alcance
     autorizado y no se implementa: **decisión docente pendiente**.
   - Mientras tanto, un escritor que cierra un curso puede escribir exactamente el negativo del valor actual, y eso da 0
     exacto.
2. **Bajo (L1): cancelaciones enormes y exactas ensanchan la cota.** Con escritores (1, 1e15, −1e15, −1,1) en un mismo
   minuto se acepta 0 en lugar de −0,1. Es la propiedad estándar de una cota relativa a Σ|operandos|. A escala clínica
   (operandos hasta 1e3) lo máximo que puede ocultar es del orden de 1e−12. Queda como deuda.
3. **Bajo (L1): la función auxiliar normaliza un −inf a 0.** `step` no puede producirlo, porque `DistressChange` y el
   estado rechazan los valores no finitos. Con operandos cercanos a 1e308, `fsum` lanza `OverflowError` en lugar del
   rechazo de procedencia. Queda como deuda (no devolver a 0 un valor no finito).
4. **Bajo (L1): al sumar el valor inicial dentro del mismo `fsum`, también cambian en 1 ulp algunos resultados
   positivos.** Afectó a unos 10 de cada 100 minutos aleatorios con dos o tres escritores, y sólo con algún lector
   declarado. Es numérico y no cambia ninguna decisión. Se declara aquí: L1 no se limita a normalizar los negativos;
   también fija una única suma correctamente redondeada.
5. **Bajo (pruebas, latente): las vistas de los paquetes cerrados leían la guarda y la suma como en P2T-1.** Hoy eso era
   neutro: ninguno usa el distrés. Pero una prueba futura de distrés en esos archivos no habría ejercido el núcleo vivo.
   **Corregido** (sólo en pruebas, sin tocar las fuentes congeladas): los 24 archivos cerrados usan
   `xm.chain(patch, historical=False)`, que lee las fuentes de P2T-1 con el comportamiento vivo. El modo histórico queda
   sólo en la prueba de P2T-1, para reproducir su registro.
6. **Bajo (M1): en un estado sin pulso, armado a mano, `derive` no llega a la guarda.** La composición devuelve antes una
   FR de 0, así que no hay efecto respiratorio que proteger. Ese estado no se alcanza: la llegada y la integración aplican
   la guarda con o sin pulso. Queda documentado.

Sin hallazgo en:
- el anclaje de la PaCO2: con el lector simpático solo, la PaCO2 y la ventilación de llegada no cambian; con la mecánica
  encendida, la PaCO2 no lee la PaCO2 de llegada;
- el distrés sólo simpático: ninguna ruta lo rechaza;
- el distrés 0: se acepta en toda ruta;
- un épsilon fijo: no lo hay. La cota es 2u·Σ|operandos|, entre 2 y 4 veces la suma de los medios ulp, holgada pero no
  laxa;
- cambios de fisiología ajenos al encargo: no los hay.

## 11. Limitaciones

- La guarda M1 es estructural: no elige ninguna ganancia ni valor de distrés.
- El edema y el TEP sólo podrán usar el lector respiratorio cuando sus mapeos lean la mecánica común (P2S-2); hoy usan la
  ruta P2K-2.
- L1 cubre el redondeo de las operaciones del minuto: cada operando y la suma.
  - No cubre la deriva acumulada en minutos anteriores (revisión, medio). Ese caso se rechaza, no se oculta.
  - Cancelaciones enormes y exactas ensanchan la cota; un −inf en la función auxiliar no se trata como no finito (bajos).
- Siguen abiertos los puntos de TD-121 que este paquete no tocaba:
  - ganancias y regiones UNSET;
  - acoplamiento mecánica → distrés;
  - SYSTEMIC_STRESS_DEFERRED;
  - WOB_OBSERVABLE_MAPPING_DEFERRED;
  - la magnitud de la composición con el ácido;
  - los bajos restantes de P2T-1 (`initial_state`, descomposiciones, cobertura).
