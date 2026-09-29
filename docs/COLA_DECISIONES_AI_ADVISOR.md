# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** lo que requiere una decisión del docente, más el estado de
  lo ya decidido.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-09-29, al cerrar el ciclo 8 (secciones «Cierre del
  ciclo 8» y «Apertura del ciclo 8»). Los ciclos 7, 6 y anteriores siguen más
  abajo.

## Pendientes de decisión

| ID | Clase | Tema | Estado al cierre del ciclo 8 |
|---|---|---|---|
| Piloto formativo | NEEDS NICOLÁS | Autorizar un piloto formativo controlado con residentes | **TECHNICALLY READY, WITH CONDITIONS** (`READINESS_PILOTO_RESIDENCIA.md`). La condición 5 suma TD-34, TD-36 y TD-39. Falta la prueba de humo en la base real |
| DF-20 | NEEDS NICOLÁS · CLINICAL REVIEW | `acs_54m_inferior`: el VD del caso frente al de su POCUS | Sin cambio: A/B/C/D. Sus filas de TDFC esperan esta decisión |
| DF-23 · 4a | NEEDS NICOLÁS · CLINICAL REVIEW | `acs_70f_left_main`: «No B-lines» frente a la congestión | Sin cambio. Basta una línea |
| TD-33 | NEEDS NICOLÁS · CLINICAL REVIEW | Residuo de TD-21: tras reponer con cristaloide, transfundir en trauma dispara la sobrecarga | Sin cambio. Recomendado: en esa regla, sólo la sangre repone el déficit (una línea) |
| DF-23 · 4b, 6, 7, 8 | CLINICAL REVIEW | Inconsistencias clínicas | Sin cambio (§31) |
| Baseline inglés | NEEDS NICOLÁS · METHODOLOGICAL | Qué commit mide los documentos ingleses | Candidatos documentados; el V2 ya nombra su commit (`9d2cd9e`). KD-05 sigue en ambos. Se elige **antes** de leer respuestas |
| KD-02 · TD-35 | NEEDS NICOLÁS | Lo que una lista nombra sin verbo y el lector no conoce | ¿Preguntarlo? Hoy se pierde sin aviso mientras lo demás corre |
| KD-15 | NEEDS NICOLÁS | Un fluido nombrado en palabras sin verbo («IV fluids 1 L») | Sin cambio |
| Medidas combinadas | CLINICAL REVIEW | Resto de TD-31: «direct pressure with packing» suma el efecto de dos medidas | Sin cambio |
| DC3 (mitad de la dosis) | CLINICAL REVIEW | Una dosis «IO» sin instalar la IO | Sin cambio |
| TDFC · dudas | NEEDS NICOLÁS · CLINICAL REVIEW | Las cuatro dudas residuales de las filas claras | Aplicadas como estaban; cada una se cambia en una línea (`tdfc/TDFC_TABLA_FINAL.md`) |
| TDFC · composiciones | NEEDS NICOLÁS | ¿Las composiciones de hipoglicemia heredan TD/F/C de su origen, como C14 (L-F07 B)? | Hoy conservan la transición |
| DF-15 | WAITING FOR EXTERNAL DATA | Piloto del validation corpus, español e inglés | Listo, no enviado; nada llegó en el ciclo 8 |
| TD-39 | HIGH · DEFERRED | Un alta con plazo o tras una observación corre ahora | Anterior al ciclo; también en `939978a`. Propuesto para el ciclo 9 |
| TD-14 · TD-34 · TD-35 · TD-36 · TD-37 · TD-40 | HIGH · MEDIUM | Lo que queda del lector | Documentado; el piloto lo mide |
| TD-38 | LOW | El aviso genérico tras un envío que sólo trae un plan | Documentado |
| Biblioteca POCUS | FUTURE ARCHITECTURE | Videos reales, adquisición y reconocimiento en la imagen | `ARQUITECTURA_POCUS_OBJETIVO.md`. No es deuda ni bug |
| DF-25 · DF-14 · DF-12 · DF-17 · DF-4 | — | Brechas del banco · PARTIAL · transición · *override* · C2 | Sin cambio |
| DF-18 · DF-9 · DF-11 · DF-5 | — | Multisource · −3 · residuos menores · C15 | Registrados, sin acción |

__CIERRE8__

## Apertura del ciclo 8 (2026-09-28)

**La instrucción, al cerrar el ciclo 7:**

- «Tengo que salir ahora, pero me gustaría dejarte trabajando en el siguiente
  ciclo».
- Luego: «que el ciclo 8 abarque más tareas que no requieran mucha aprobación
  por mí. Si algo lo requiere, me lo entregas en el informe final como lo hemos
  hecho hasta ahora».

**Alcance elegido por el AI Advisor,** sólo con trabajo ya aprobado o que no
pide una decisión clínica ni metodológica nueva:

1. **TDFC** (TD1, F1, C1 y C3):
   - aprobado conceptualmente en el ciclo 7 (§28), «según las recomendaciones
     actuales»;
   - con el modelo de C14 (§92);
   - las filas de `acs_54m_inferior` esperan DF-20, como dice la
     recomendación de TDFC-5;
   - C4 sigue fuera (§93).
2. **Lector, por clase y con el estándar A–J:**
   - TD-29: la condición «cuando/when/once»;
   - TD-30: órdenes sin verbo que se pierden sin aviso;
   - TD-31: la pregunta de la adrenalina IM sin dosis;
   - TD-32: los residuos LOW de TD-26;
   - KD-05: «OK to discharge».
3. **Deuda menor:** TD-27, TD-28, TD-25, TD-06 y TD-23.
4. **Verificación:**
   - el ensayo de los 20 escenarios ES/EN;
   - la suite completa y las 56 regresiones.

**Lo que no se toca** porque pide su decisión, y va al informe final:

- TD-33, DF-20 y DF-23 (4a, 4b, 6, 7, 8);
- KD-02 y KD-15;
- la regla de medidas combinadas (TD-31, segunda mitad);
- DC3 (la mitad de la dosis);
- el baseline inglés;
- el piloto con residentes y la prueba en la base real.

**Reglas que siguen:**

- sin PR, merge a `main`, release, producción ni staging;
- sin SEALED ni datos reales;
- sin contactar a nadie;
- push sólo a `clinical-encounter-v0.13`;
- el baseline español `939978a` y el V2 `9d2cd9e` quedan intactos;
- un solo reporte al final, y STOP: no se inicia el ciclo 9.

## Cierre del ciclo 7 (2026-09-28)

El ciclo cumplió lo autorizado en P0–P2. P3 (TDFC) pasó intacto al ciclo 8.
Detalle en los documentos citados; el reporte final resume.

### DECIDED + IMPLEMENTED

| Ítem | Qué quedó | Registro |
|---|---|---|
| TD-21 | Principio D: sin sobrecarga falsa mientras la hemorragia está activa; la regla vuelve con el sangrado controlado y la pérdida repuesta. La HDA no cambia | C-2026-09-28-12 · `TD21_SOBRECARGA_TRANSFUSIONAL.md` |
| TD-26 (C7-01) | Hemoderivados por clase, estándar A–J completo. En los conjuntos medidos, **0 pérdidas reales y 0 ejecuciones falsas** con el lector final | C-2026-09-28-13 · `TD26_HEMODERIVADOS_Y_C7_06.md` |
| C7-06 y TD-22 | Medidas de hemorragia, acceso IO y prueba de embarazo, EN/ES | C-2026-09-28-14 |
| C4 (H4) | C4 = NO en los 31 casos, en los generados y en PS001; es prospectivo | C-2026-09-28-10 |
| C14 (H3) | `acs_54m_inferior` NO. C14 queda en **14 YES, 17 NO y 0 NOT REVIEWED** | C-2026-09-28-11 |
| DF-24 | I-F02 A, L-F02 A (sólo qué revisión alimenta el radar), anulada A y retiro A (un aviso) | C-2026-09-28-15 |
| DF-24 · L-F07 B | Las 9 composiciones heredan el C14 NO de su origen | C-2026-09-28-16 |
| DF-23 · fila 3 | La prueba de embarazo, con C7-06 | C-2026-09-28-14 |
| C7-09 | Una corrida que mezcla ES y EN falla con claridad. El piloto inglés (EM07–EM12) está preparado y no enviado; su baseline no se eligió | `test_validation_language_separation.py` |
| C7-05 | PostgreSQL 16 local y descartable, verificado sobre el candidato final. El clúster se borró | TD-24 cerrado |
| C7-10 · ACEP | `ACEP_POCUS_FRAMEWORK.md` y la arquitectura POCUS futura, en `2899a01`. Los 6 casos REVIEW NEEDED no cambian | — |

### DECIDED + DEFERRED

- **TDFC-1 a 6 y 8 (C7-11), intacto al ciclo 8.** Es P3 y va todo o nada. No
  se cumplió su condición: aparecieron hallazgos HIGH del propio ciclo hasta
  el barrido final, y después del congelamiento no quedó capacidad
  significativa. Nada TD/F/C se escribió en el banco.
  - **Nota para el ciclo 8.** La proyección «aprobado» de
    `tdfc/MATRIZ_OPORTUNIDADES.md` usa las recomendaciones del borrador y da C3
    13/18. El TDFC-6 aprobado da C3 10/21: YES en 46f, 83m y 61m; NO en 33f,
    24f y 63m. Hay que regenerarla antes de implementar.
- **Fuera de DF-24:** I-F18 (TD-18) y la meta cambiada tras confirmar.
- **Otros defectos del lector (§8):** D5W, el antibiótico unido a un traslado y
  el resto de TD-14.
- **La mitad de dosis de DC3:** con la decisión 8.

### NEEDS NICOLÁS

1. Autorizar, o no, el piloto formativo controlado con sus condiciones.
2. DF-20: A, B, C o D.
3. DF-23, fila 4a: «4a: aplicar el texto propuesto» (u otro).
4. TD-33: «sólo la sangre repone el déficit de la regla de sobrecarga en
   trauma» (recomendado) u otra cosa.
5. El baseline del piloto inglés, antes de leer respuestas.
6. La propuesta del ciclo 8 (en el reporte final).
7. Cuando pueda: DF-23, filas 4b, 6, 7 y 8.

### WAITING FOR EXTERNAL DATA

- **Los documentos de los médicos, en español y en inglés.** Nada llegó ni se
  envió en el ciclo 7. SEALED no se tocó.
- **La fidelidad externa del lector:** ordena TD-14, TD-29, TD-30 y TD-32.

### FUTURE ARCHITECTURE

- **La biblioteca POCUS de videos reales** (`ARQUITECTURA_POCUS_OBJETIVO.md`).
  Hoy el POCUS es un informe escrito: su evidencia es una contribución PARCIAL.
- **La evidencia C4:** vendrá de simulación procedural u observación en el
  lugar de trabajo.

### Hallazgos nuevos del ciclo (§73)

- **Corregidos (CRITICAL/HIGH, dentro del alcance o regresiones del ciclo).**
  Los 16 CRITICAL de la revisión adversarial y lo que halló el barrido final:
  - «suspender/stop transfusión de …» corría las unidades;
  - un verbo que detiene borraba la medida que acompañaba;
  - un balance volvía a pasar el suero;
  - una proporción entre productos se perdía.

  Detalle en `TD26_HEMODERIVADOS_Y_C7_06.md`.
- **Documentados:**
  - TD-33 (HIGH, NEEDS NICOLÁS): un residuo de TD-21 que halló la prueba de la
    rúbrica sobre el lector final;
  - TD-29 (HIGH): la condición «cuando»;
  - TD-30 (MEDIUM): órdenes sin verbo;
  - TD-31 (MEDIUM): la adrenalina IM sin dosis y las medidas combinadas;
  - TD-32 (LOW): residuos de TD-26.
- **Proceso.** `1c4194b` y `c61daf6` se subieron con una prueba fallando (el
  catálogo de hipoglicemia desactualizado). Se regeneró.

### Baselines

- **SPANISH PILOT BASELINE `939978a`:** intacto. `validation/pilot_v1` y los 18
  DOCX no cambiaron.
- **DEVELOPMENT HARDENED BASELINE V1 (`72a4a53`) y V2:** en
  `validation/BASELINES.md`. Ninguno es un «validated engine».

## Decisiones del 2026-09-28 (apertura del ciclo 7)

El docente aprobó la propuesta del ciclo 7 con modificaciones y ordenó
ejecutarlo sin otra aprobación, con máxima autonomía dentro del alcance
aprobado (el docente está offline). Las reglas permanentes del lector y del
Trace quedaron además en el charter, addendum A2.

**Objetivo.** Dejar el simulador técnicamente apto para un piloto formativo
controlado con residentes, sin contaminar el piloto de validación, sin
modificar scoring, sin declarar competencia y sin ampliar features
innecesariamente. Prioridad: fidelidad del Management Trace → seguridad
clínica → jugabilidad → integridad de datos → calidad de la evidencia
observacional → preparación de la validación → costo-efectividad.

- **TD-21 · principio D aprobado, no la opción A.**
  - Mientras haya una hemorragia activa clínicamente significativa, con
    pérdida o déficit hemorrágico modelado en curso, una Hb ≥ 10 aislada **no
    basta** como evidencia de sobrecarga transfusional.
  - La regla genérica vuelve a ser evaluable cuando el sangrado está
    controlado, cuando ya no hay déficit hemorrágico modelado, o cuando existe
    otra evidencia clínicamente coherente de sobretransfusión.
  - No se crea una equivalencia «mL perdidos → unidades permitidas».
  - Antes de implementar se compara A con D (plausibilidad, complejidad,
    consecuencias no buscadas, reversibilidad, verificabilidad). Si D es
    pequeña, general y robusta, se implementa D; si exige reconstruir la
    fisiología, TD-21 se detiene y se documenta, y el ciclo sigue.
  - **Aceptación:** transfusión apropiada durante hemorragia activa
    significativa → sin sobrecarga falsa; transfusión claramente excesiva
    fuera de ese estado → el mecanismo actual sigue siendo posible. Se
    verifican trauma ×2, HDA ×2, casos sin sangrado y casos generados de
    sangrado. Sin cambios al −3 ni a la metodología de eventos críticos.
- **TD-26 (C7-01) · autorizado, CRITICAL.** Si la persona residente ordena
  con claridad un hemoderivado, el motor no puede perderlo en silencio.
  - **A** · glóbulos rojos (soportados): se ejecutan las unidades indicadas.
  - **B** · plasma, plaquetas, crioprecipitado, sangre total, si no están
    modelados: se registra fielmente que fueron indicados, «effect not
    modeled»; nunca se convierten en glóbulos rojos ni se inventan efectos.
  - **C** · protocolo de transfusión masiva: se registra que se activó; si el
    motor necesita saber qué dar ahora, se aclara; nunca se traduce en
    unidades ni proporciones inventadas, ni en un protocolo institucional que
    la persona residente no escribió.
  - **D** · una orden ambigua de hemoderivado: se aclara.
  - Estándar A–J completo. Regla: **una corrección del lector no está completa
    porque pasen sus ejemplos originales.**
- **C7-06 · aprobado en la misma tanda A–J:** la prueba de embarazo que
  retiene la tanda (TD-22), el lenguaje de control de hemorragia («pack the
  wound», «hold pressure») y el acceso IO («humeral IO»), con variantes
  naturales EN/ES. Lo que se ejecuta hace responder al paciente según el
  motor; lo que no se ejecuta no aparece como hecho en el Trace.
- **Otros defectos del lector: DEFERRED.** D5W / D5 half-normal, el
  antibiótico unido a un traslado a pabellón y el resto de TD-14, salvo que
  sean regresiones de C7-01/C7-06 o compartan exactamente la causa raíz y
  corregirlos sea una extensión trivial, general y segura. El ciclo 7 no es
  una limpieza general del lector.
- **PostgreSQL (H2) · autorizado un clúster PostgreSQL 16 local y
  descartable**, sin datos reales, en `/var/tmp/mrs-pg-c7` o equivalente, que
  se borra al terminar.
  - Ni producción ni Neon, si el local funciona.
  - Si hacen falta credenciales externas, infraestructura nueva, gasto o
    producción: se detiene PostgreSQL, se reporta BLOCKED y el ciclo sigue.
    Si el local falla tras un intento razonable, se documentan el bloqueo
    exacto y lo que habría que hacer en staging.
  - **Alcance:** L-F01, L-F04, unicidad de las observaciones, confirmación
    docente, persistencia de la rúbrica, Objective Progress, persistencia y
    procedencia del Trace, y la conducta de las oportunidades C4/C14. Una
    corrida temprana y otra sobre el candidato final. Sin infraestructura
    permanente.
- **C14 (H3) · `acs_54m_inferior` = NO**, con la razón basada en ACEP y
  concisa: la conclusión es sobre la **oportunidad de observación**, no sobre
  la posibilidad técnica («POCUS cannot evaluate the RV» sería demasiado
  fuerte). Después, 31/31 casos revisados: **14 YES / 17 NO / 0 NOT
  REVIEWED**; se retira la transición de C14 donde ya no corresponde y se
  regeneran la tabla y la matriz. C14 no tiene scoring que cambiar.
- **ACEP · resultado conceptual aceptado.** ACEP concibe la competencia en EUS
  como INDICATION → ACQUISITION → INTERPRETATION → INTEGRATION INTO
  MANAGEMENT. El simulador actual observa la indicación o selección
  (potencialmente), la interpretación clínica de un hallazgo POCUS descrito y
  la integración al manejo; **no** observa la adquisición ni el
  reconocimiento directo en la imagen, porque entrega un informe escrito. Su
  evidencia POCUS es una **contribución PARCIAL**, nunca competencia POCUS
  completa.
  - **Terminología:** mientras el POCUS sea texto, no se dice «resident
    recognized the ultrasound finding on imaging»; se dice «resident
    interpreted the provided POCUS finding» o «resident integrated the provided
    POCUS information into management». Vale para documentación, faculty
    briefs y afirmaciones metodológicas futuras, sin reescribir históricos.
  - **ACEP 2016 es una fuente metodológica y de diseño, no un mapping nuevo**,
    ni la definición única o final de la competencia POCUS contemporánea. Nada
    de puntajes, progreso, certificación ni estado de competencia ACEP. Puede
    informar C14, el diseño POCUS futuro, las descripciones de componentes y la
    biblioteca futura. No se abre una revisión bibliográfica nueva.
  - **Alcance cardíaco:** lo que la fuente sí respalda (ventanas estándar,
    actividad cardíaca, derrame y taponamiento, función cualitativa del VI,
    volumen o presión venosa central, VCI y evaluación hemodinámica
    pertinentes, integración al manejo) y lo que no establece como expectativa
    general (motilidad regional, el VD tal como lo usan algunos casos, eco
    cuantitativa avanzada) se marcan como SOURCE LIMITATION / REVIEW NEEDED.
    No se eliminan capacidades por no aparecer en el documento.
  - **Casos REVIEW NEEDED, sin cambio en el ciclo 7:** `acs_61m_posterior`,
    `acs_52m_de_winter`, `pulmonary_embolism_61m`, `renal_colic_34m`,
    `bradycardia_avb3_78f` y `acs_48m_wellens`. No bloquean TD-21 ni TD-26.
  - El C14 actual se evalúa con la capacidad actual (POCUS en texto). La
    biblioteca visual futura exigirá revisar C14 aparte, sin cambiar
    Objective Progress, la meta de 50 ni crear subpuntajes.
- **Arquitectura POCUS futura: FUTURE ARCHITECTURE, no deuda técnica ni bug.**
  Resumen en `docs/ARQUITECTURA_POCUS_OBJETIVO.md`. No se implementa nada en el
  ciclo 7.
- **C4 (H4) · C4 = NO en los 31 casos, en los casos generados y en PS001**,
  cuando comparten el entorno de observación actual. La razón es una
  limitación del entorno y del motor, no de los casos.
  - No se toca el motor para fabricar C4, ni se obtiene «C4 = PARTIAL» de una
    orden procedural.
  - Es prospectivo: los encuentros históricos conservan su contexto de
    evaluación; no se migran observaciones.
  - La evidencia C4 futura vendrá de simulación procedural y/u observación en
    el lugar de trabajo. C4 sigue fuera aunque se implementen los demás TDFC.
- **DF-24:** I-F02 A · **L-F02 A** (autorización explícita: sólo cambia qué
  revisión alimenta el radar, no el scoring, D1–D5 ni el promedio
  longitudinal) · observación anulada A · retiro de rúbrica confirmada A ahora
  (sin estado «retirada») · L-F07 B. Fuera: I-F18 y la meta cambiada tras
  confirmar. Cada cambio con falla actual, conducta esperada, prueba focalizada
  y compatibilidad hacia atrás, sin refactor del flujo longitudinal.
- **TDFC:** TDFC-1, 2, 3, 4, 5, 6 y 8 aprobados conceptualmente según las
  recomendaciones actuales; TDFC-7 ya estaba decidido.
  - La implementación es **P3**: sólo si TD-21, TD-26 y C7-06 están
    resueltos, PostgreSQL verificado o legítimamente bloqueado, C4/C14 y el
    DF-24 aprobado cerrados, sin nuevos bloqueos CRITICAL/HIGH y con capacidad
    significativa. Si no, pasa **intacta** al ciclo 8: todo lo aprobado de
    forma coherente, o nada.
  - Si se implementa: el modelo de C14 (borrador → decisión aprobada →
    declaración por caso → procedencia → congelada con el encuentro), con el
    componente observable y lo que queda fuera para TD1, F1, C1 y C3. Sin
    puntaje de competencia.
- **DF-23 · conservador.** La fila 3 entra con C7-06. La fila 4a
  (`acs_70f_left_main`, «No B-lines» frente a una congestión que progresa):
  se presenta el texto EN/ES y la señal que corrige; se implementa sólo si
  elimina una contradicción factual sin cambiar el Decision Challenge, con
  ANTES/DESPUÉS; si cambia la interpretación clínica, se difiere. Las filas 8,
  7, 4b y 6 siguen como decisiones clínicas. No se limpia la variabilidad
  plausible.
- **Piloto de validación español:** sigue como fue diseñado. El SPANISH PILOT
  BASELINE `939978a` es inmutable: no se modifican el baseline, los 18 DOCX ni
  los defectos conocidos retrospectivamente, no se usa SEALED y no se llevan
  al baseline las correcciones del ciclo 7.
  - Con respuestas humanas: MEASURE FIRST. Primero el corpus español contra
    `939978a`; después, cuando corresponda, los mismos datos de desarrollo
    contra el motor endurecido. Se reportan ambos; no se ocultan defectos del
    baseline porque ya estén corregidos.
- **Piloto de validación inglés:** existen versiones inglesas equivalentes de
  los 18 documentos. Será un corpus **separado**, con su idioma, versión de
  corpus, códigos de participante (EM07–EM12), asignación, baseline, versión
  de defectos conocidos y sorteo development/sealed propios.
  - Texto escrito naturalmente en inglés por clínicos que escriben en inglés;
    nunca una traducción. Nada se envía en el ciclo 7.
  - Se puede preparar su infraestructura si P0/P1 están completos y el costo
    marginal es bajo, reutilizando el pipeline existente. No se regeneran los
    DOCX ingleses si existen fuera del repositorio: se documenta «ENGLISH DOCX
    AVAILABLE EXTERNALLY / NOT PRESENT IN REPOSITORY», sin inventar su
    contenido. Al incorporarlos, se verifican contra los españoles (mismo caso,
    mismas instrucciones, misma asignación, otro idioma de respuesta).
  - **Separación de idiomas (C7-09a):** una validación determinística del
    manifiesto que haga fallar con claridad una corrida que mezcle ES y EN. Sin
    autodetección.
  - **Baseline externo inglés:** no se elige automáticamente el HEAD del ciclo
    7; se documentan los candidatos, y la elección se hace antes de recibir o
    leer respuestas inglesas.
- **Datos externos que lleguen durante el ciclo:** no se leen a mano para
  decidir qué corregir. STORE → SPLIT → BLINDED REFERENCE ANNOTATION →
  BASELINE RUN → MEASURE. Si falta la anotación humana, se prepara, se
  documenta y el ciclo sigue. SEALED, nunca.
- **Baselines, tres conceptos separados:** SPANISH PILOT BASELINE `939978a`;
  DEVELOPMENT HARDENED BASELINE V1 `72a4a53`; DEVELOPMENT HARDENED BASELINE V2
  = el candidato final del ciclo 7, sólo si cumple la definición de terminado.
  Ninguno se llama «validated engine».
- **El validation corpus evalúa el motor.** Nunca calibra puntajes de
  residentes, umbrales de competencia, comparaciones entre médicos ni
  benchmarks clínicos. Blind sets internos, datos externos de desarrollo y
  sellados quedan separados; nada sellado en logs, fixtures, snapshots ni
  reportes del repositorio.
- **Piloto con residentes:** sólo formativo, con confirmación docente
  obligatoria. El sistema produce evidencia observacional, no certificación,
  determinación de competencia, EPA completada ni milestone alcanzado. Al
  cerrar se distinguen TECHNICALLY READY FOR CONTROLLED FORMATIVE RESIDENCY
  PILOT, EXTERNAL VALIDATION PILOT READY y VALIDATED ASSESSMENT INSTRUMENT
  (se espera NO / NOT YET ESTABLISHED), y los bloqueos técnicos de las
  limitaciones metodológicas.
- **Sin cambios:** definiciones de eventos críticos, −3, puntaje ajustado,
  D1–D5, escala 0–3, metodología del radar (salvo la selección de L-F02),
  promedio longitudinal, DIRECT/PARTIAL (PARTIAL no es una penalidad) y la
  confirmación docente. Se verifica que TD-21/TD-26 no produzcan una acción
  peligrosa falsa ni una omisión crítica falsa.
- **Costo e IA:** el menor costo razonable que preserve la calidad,
  reutilizando el tooling del ciclo 6. IA sólo para frases ciegas, revisión
  adversarial y revisión independiente de código; nunca para videos POCUS,
  respuestas de validación ni verdad clínica de referencia. Regla del 130 %
  del charter, sin sacrificar pruebas.
- **Hallazgos nuevos:** CRITICAL se reproduce, se busca la causa, se documenta
  y se corrige si es inequívoco, pequeño y reversible; HIGH se corrige sólo si
  es regresión del ciclo, comparte causa con TD-26/C7-06 o amenaza la
  integridad de datos; MEDIUM/LOW se documentan y se difieren. Después del
  congelamiento del BASELINE V2, nada nuevo MEDIUM/LOW se corrige.
- **Fuera de alcance:** PR, merge a `main`, release, producción, SEALED y el
  ciclo 8 (se propone, no se inicia).

## Cierre del ciclo 6 (2026-09-28)

**Hecho.**

- **DF-22 · las nueve clases CRITICAL del lector, corregidas por clase**
  (C-2026-09-28-04).
  - C01 a C09 en inglés y español: el lector, el motor y el Management Trace.
  - Suite nueva `CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS`: 192 pruebas, 4 de
    ellas por la página real.
  - Tres conjuntos ciegos (258 frases que nadie del desarrollo vio), medidos
    **una vez**. Encontraron regresiones de las propias correcciones; se
    corrigieron después, y esos números son post hoc.
  - Con el código final, **ninguna de las 118 negativas ejecuta nada de más en
    el motor**. En las positivas, la mayoría de lo que no corre se retiene con
    una pregunta; quedan pérdidas sin aviso, sobre todo de hemoderivados
    (TD-26).
  - Corpus de ensayo: 238 decisiones idénticas al ciclo 5.
  - **Revisión adversarial del diff, después del primer commit (`39bac97`).**
    - Halló 13 regresiones de las propias correcciones que los conjuntos
      ciegos no vieron; por ejemplo, «Hold NS, O2 4 L NC» retiraba el oxígeno
      y «Should I give aspirin?» la administraba.
    - Una comparación completa con el lector del ciclo 5 halló dos más y un
      defecto anterior al ciclo: la activación de un servicio volvía
      interconsultas los antiagregantes que la seguían.
    - Todo se corrigió (C-2026-09-28-09).
    - Las 225 lecturas que difieren del ciclo 5 se revisaron una por una.
  - Detalle: `MEDICION_RECONOCIMIENTO_ORDENES.md`.
- **59O-03, completo** (C-2026-09-28-05). El aviso de ejecución urgente y la
  oferta de explicarla salen sólo de una ejecución real. Casos A–F de punta a
  punta en inglés y español.
- **Seguridad de la aclaración.**
  - «No sé» ya no hace desaparecer una orden retenida: la mantiene y repite la
    pregunta.
  - Lo unido a lo que hizo el equipo prehospitalario se pregunta, no se
    ejecuta.
- **L-F01, completo** (C-2026-09-28-06). Un encuentro se lee con los temas de
  historia de su caso congelado. Lo legacy sin caso queda UNAVAILABLE. A → B →
  reabrir da A.
- **L-F04, completo** (C-2026-09-28-07). La trayectoria sigue la fecha del
  encuentro; la de confirmación queda como metadato.
- **DF-23: dos correcciones que cumplen las seis condiciones**
  (C-2026-09-28-08).
  - De Winter conserva su acinesia con la arteria cerrada.
  - `bradycardia_bb_54f` llega somnolienta.
  - El resto queda para decisión.
- **Sin cambio:**
  - **`acs_54m_inferior`:** sin cambio de datos ni fisiología; sigue NOT
    REVIEWED.
  - **C14:** 14 YES y 16 NO.
  - **TD/F/C:** nada escrito en el banco.
- **Documentos de decisión:** `DF24_DECISIONS_FOR_NICOLAS.md` y
  `docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md`.
- **Readiness del piloto con residentes:** `READINESS_PILOTO_RESIDENCIA.md`.
  Respuesta: **WITH CONDITIONS**.
- **Baselines.**
  - El SPANISH PILOT BASELINE `939978a` no se tocó.
  - Se registró el **DEVELOPMENT HARDENED BASELINE V1**
    (`validation/BASELINES.md`). No es una versión validada.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 7 no se inició.

### Cola de decisiones al cierre del ciclo 6

**BLOCKING BEFORE RESIDENCY PILOT**

1. **TD-21 · Sobrecarga transfusional en trauma.**
   - El problema: con una hemorragia activa, la familia trauma no baja la
     hemoglobina y la regla de sobrecarga mira Hb ≥ 10. Enseña que la sangre
     daña en los dos casos de trauma.
   - Recomendación: excluir la hemorragia activa de la regla.
   - Evidencia: `AUDITORIA_DF23_CICLO6.md` §7.1.
2. **TD-26 · Hemoderivados que se pierden sin aviso.**
   - Ejemplos: «2 U de GR O negativo», «O-neg», el protocolo de transfusión
     masiva.
   - Recomendación: autorizar una corrección por clase, medida como DF-22.
3. **C4 = NO, escrito en el banco antes que el resto de TD/F/C.**
   - Está decidido (TDFC-7), pero la transición deja C4 valorable en todo
     encuentro.
   - Recomendación: escribirlo solo.
4. **El uso del piloto con residentes.**
   - La fidelidad del lector con texto externo no está medida.
   - Recomendación: formativo, con confirmación docente de cada rúbrica, hasta
     que el piloto de validación la mida.
5. **PostgreSQL (TD-24).**
   - L-F01 y L-F04 se probaron en SQLite.
   - Falta verificarlos en la base de staging, con su acceso.

**HIGH VALUE / NOT BLOCKING**

- **Enviar el piloto de validación v1 (DF-15):** revisar los 18 documentos,
  reclutar a los 6 médicos y enviar.
- **DF-24, en una línea:** «I-F02 A · L-F02 A · I-F18 B · L-F07 B (D después)
  · anulada A · retiro A · meta A».
- **TD-22:** registrar la prueba de embarazo como «no modelada». Cumple 6/6.
- **TD-23:** los avisos que quedan en inglés dentro de la interfaz en español.

**METHODOLOGICAL**

- **TDFC-1 a 6 y 8, en una línea:** «1 approve / 2 approve / 3 approve /
  4 approve / 5 approve (54m tras DF-20) / 6 approve / 8 approve».
- **Brechas del banco (DF-25):** R1-07, R2-02, R1-03, R1-04, R2-01 y C4, en
  ese orden. Una brecha no es trabajo automático.
- **DF-12, DF-14, DF-17 y DF-9:** sin cambio.
- **Regla para cuando lleguen datos humanos (§89):** MEASURE FIRST.
  BASELINE → MEASUREMENT → ANNOTATION → ADJUDICATION → ERROR CLASSIFICATION →
  PRIORITIZATION → APPROVED FIX.

**CLINICAL REVIEW**

- **`acs_54m_inferior` (DF-20):**
  - confirmar C14 **NO** (recomendado) o YES;
  - decidir si se agrega una nota docente sobre el VD.
- **DF-23, filas 3 a 11:**
  - embarazo: qué responde cada caso;
  - grado del VI y líneas B en `acs_70f_left_main`;
  - «Reduced → mildly reduced» en inferior y posterior;
  - la pared tras reperfundir;
  - FA en `anaphylaxis_63m_betablocked`;
  - foto de llegada de `bradycardia_bb_54f`;
  - menores.
- **TD-04:** confirmar el POCUS de los casos C14 YES; todo el POCUS del banco
  sigue marcado como borrador.

**WAITING FOR EXTERNAL DATA**

- **Los documentos del piloto de validación.** Se miden primero contra el
  SPANISH PILOT BASELINE y después contra el DEVELOPMENT HARDENED BASELINE V1.
- **La fidelidad externa del lector.** Con ella se priorizan TD-14 y el resto
  del manifiesto de defectos conocidos.

## Decisiones del 2026-09-28 (apertura del ciclo 6)

El docente aprobó el cierre del ciclo 5 y ordenó el ciclo 6: **endurecimiento,
consistencia clínica e integridad longitudinal**. El Management Trace sigue
siendo la fuente de verdad: lo que el residente escribió, el motor lo entiende,
la ejecución lo refleja y el Trace lo registra con fidelidad.

| Tema | Decisión |
|---|---|
| **DF-22** · las 9 clases CRITICAL del lector | **APROBADO para implementar**, por clase y no por frase: BEFORE, causa, corrección, frases nuevas independientes, controles negativos, ejecución, Trace, EN, ES y sin regresión. Suite nueva `CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS`. Las 90 frases de la auditoría no son la meta |
| **59O-03** · aviso falso de ejecución | **APROBADO.** El aviso de ejecución sale del estado real de ejecución, nunca del reconocimiento, del intento ni del lenguaje urgente. Casos A–F de punta a punta, EN/ES |
| **Seguridad de la aclaración** | Auditar el camino entrada ambigua → pregunta → respuesta → ejecución. Una aclaración no cambia en silencio la intención clínica; si no se resuelve con seguridad, se retiene. Sólo se corrigen defectos inequívocos; si cambia semántica clínica, se documenta |
| **SPANISH PILOT BASELINE `939978a`** | **Inmutable.** No se cambian sus métricas, su manifiesto de defectos conocidos ni los 18 documentos. La primera medición humana se hace contra él |
| **HEAD ≠ baseline de validación** | El HEAD de desarrollo quedará por delante del baseline español, a propósito. No se mezclan métricas |
| **DEVELOPMENT HARDENED BASELINE V1** | Se registra si todo queda verde. No reemplaza al baseline español ni se llama «validado» |
| **DF-20** · `acs_54m_inferior` | **Recomendación anterior modificada.** No se cambia todavía el tamaño ni la contractilidad del VD, la VCI ni la fisiología. Nueva pregunta: ¿hay de verdad una contradicción, o un IAM inferior con compromiso hemodinámico del VD puede coexistir con un POCUS cualitativo no diagnóstico? Para C14: ¿el POCUS crea una oportunidad significativa de guiar el manejo? El caso sigue NOT REVIEWED salvo evidencia inequívoca. «Sin cambios» es un resultado aceptable |
| **DF-23** · POCUS coronario y otras inconsistencias | **Auditoría focalizada aprobada.** Se corrige sólo lo inequívoco: una sola interpretación defendible, diseño claro, sin cambiar el Decision Challenge ni la metodología, con BEFORE/AFTER y pruebas. Con dos interpretaciones razonables, se documenta y no se elige |
| **C14** | Siguen 14 YES y 16 NO. No se cambian salvo que DF-23 demuestre que una inconsistencia invalida una oportunidad, y antes se documenta |
| **DF-24 · L-F01** | **APROBADO.** Un encuentro histórico se interpreta con lo que le perteneció, no con el banco actual. Sin inventar pasado: lo legacy queda LEGACY / UNKNOWN |
| **DF-24 · L-F04** | **DECIDIDO.** La trayectoria se ordena por la fecha y hora del encuentro. La fecha de confirmación se conserva como metadato de auditoría |
| **DF-24 · resto** (I-F02, L-F02, I-F18, L-F07 y las tres decisiones de corrección) | **No se implementan.** Documento de decisión `docs/DF24_DECISIONS_FOR_NICOLAS.md` |
| **TDFC-7 / C4** | **DECIDIDO: C4 = NO** en los casos propuestos. El motor no modela el componente procedural relevante; ordenar un procedimiento no es una oportunidad de C4. Se registra como brecha, sin cambiar el motor |
| **TDFC-1 a 6 y 8** | **No se implementan.** Documento corto de decisión `docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md`. Nada TD/F/C se escribe en el banco |
| **Brechas del banco** | Se conserva la auditoría. Se priorizan R1-07, R2-02, R1-03, R1-04, R2-01 y C4 sin implementar; una brecha no es backlog automático |
| **TD-09** · cola docente a escala | **No se optimiza** en el ciclo 6 |
| **PostgreSQL** | Probarlo sólo con infraestructura ya disponible y sin gasto; si no, NOT TESTED |
| **Sin cambios** | D1–D5, escala 0–3, eventos críticos, −3, puntaje ajustado, radar, confirmación docente y DIRECT/PARTIAL. Sin puntajes nuevos ni funciones nuevas |

## Cierre del ciclo 5 (2026-09-28)

- **C14 activado donde se aprobó (DF-13, cerrado).**
  - 30 casos declaran C14: **14 YES y 16 NO**, cada uno con quién lo revisó,
    cuándo, su grupo de decisión y la versión C14-REVIEW-1. Un NO lleva su
    razón.
  - La tabla derivada está en `docs/C14_TABLA_FINAL.md`, y una prueba la ata
    al banco.
  - La regla de transición se retiró sólo para C14 y sólo en esos 30 casos.
  - 16 pruebas nuevas (`test_c14_opportunities.py`) cubren §21, §22 y
    §36–§39.
- **`acs_54m_inferior` auditado (DF-20), sin cambios.**
  - Clasificación B: inconsistencia de datos del caso.
  - Recomendación A: el VD comprometido es el diseño.
  - Decisión pendiente.
- **KD-01 corregido por clase y verificado (DF-19, cerrado).**
  - La vía escrita antes del fármaco, también dentro de una lista.
  - 53 pruebas nuevas.
  - Corpus de ensayo idéntico en ES y EN.
- **Baselines.**
  - **SPANISH PILOT BASELINE `939978a`**, sin cambio.
  - **ENGLISH VALIDATION BASELINE `ec1c77f`:** 4956 pasan, 77 omitidas,
    2 xfail y 0 fallas; 56 de 56 regresiones.
  - Los reportes nombran el baseline y la versión de defectos conocidos: la
    lista es la versión 2, con KD-15 y KB-02 nuevos.
- **Piloto: tooling READY**, con una prueba de punta a punta sobre documentos
  sintéticos. Las etiquetas de defecto conocido ahora se validan contra la
  lista.
- **Una regresión del ciclo, corregida.** El catálogo publicado de
  hipoglicemia quedó desactualizado por las entradas nuevas del registro de
  correcciones. Se regeneró, y su generador nombra la corrección detrás de
  cada declaración nueva.
- **Sin cambios:**
  - D1–D5 y la escala;
  - eventos críticos, −3, puntaje ajustado y radar;
  - confirmación docente;
  - mappings (9 PARTIAL inactivos);
  - C2 y C15 deshabilitadas.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 6 no se inició.

## Extensión nocturna del ciclo 5 (2026-09-28)

Auditar y documentar (59A–59BU). Índice y detalle:
`docs/AUDITORIA_NOCTURNA_CICLO5.md`.

- **Una corrección, dentro del límite de 59BT (C-2026-09-28-03).** Un
  encuentro nuevo heredaba el cierre del anterior (59Z):
  - el aviso «How is this encounter ending?» abría el encuentro siguiente en
    el minuto 0;
  - el registro de cierre anterior se guardaba en el encuentro siguiente.
  - Reproducido en la página real y corregido en 2 líneas, con 3 pruebas. Los
    registros guardados no se reescribieron.
- **Suite completa sobre la corrección (`3f0524c`):** 4960 pasan, 1 falla,
  77 omitidas y 2 xfail; 56 de 56 regresiones.
  - La falla fue el catálogo publicado de hipoglicemia, que lista las
    correcciones.
  - Se regeneró (`b8eb421`), y sus pruebas pasan.
- **Suite completa final (`8c5d5a3`, con la documentación de la noche):**
  **4961 pasan, 0 fallas**, 77 omitidas y 2 xfail; 56 de 56 regresiones.
- **Lo más importante, sin corregir:**
  - **DF-22.** El lector pierde órdenes de primera línea por la forma de la
    oración, y la página dice «Urgent intervention executed» cuando nada
    corrió.
  - **DF-23.** El POCUS de las 4 oclusiones baja la severidad redactada sin
    reperfusión; en de Winter, C14 YES, acinesia pasa a «mildly reduced».
  - **DF-24.** Los temas de historia se leen del banco vivo, y el perfil ordena
    por confirmación.
- **Se sostienen:**
  - el aislamiento entre residentes (36 métodos);
  - la idempotencia, la concurrencia y las transacciones;
  - el oráculo longitudinal, que coincide en cada celda;
  - la escala hasta 5000 encuentros, salvo la cola docente completa (TD-09).
- **Borradores nuevos, nada en el banco:** TD/F/C (DF-21) y brechas del banco
  (DF-25).

## Decisiones del 2026-09-28 (apertura del ciclo 5)

El docente aprobó el cierre del ciclo 4 y ordenó iniciar el ciclo 5 sin otra
aprobación.

- **DF-13 · C14, decisiones A–H aprobadas**, con estas precisiones:
  - **A:** `acs_61m_posterior` y `acs_52m_de_winter` YES; `acs_66f_nonst` NO.
    `acs_54m_inferior` NO se activa: se audita la contradicción entre el VD
    declarado y el POCUS con VD normal. La auditoría no corrige el dato si
    corregirlo exige elegir entre las dos representaciones; recomienda y deja
    la decisión al docente.
  - **B:** `acs_48m_wellens` NO.
  - **C:** YES en `pneumonia_46f`, `pneumonia_83m`, `gi_bleed_57m`,
    `gi_bleed_72f` y `obstructive_pyelonephritis_58f`; NO en `anaphylaxis_29f`
    y `anaphylaxis_63m_betablocked`.
    - Principio: el POCUS cuenta cuando selecciona, limita, titula o reevalúa
      la estrategia de fluidos o hemodinámica.
  - **D:** asma ×2 NO, porque el evento revela el diagnóstico de neumotórax.
    No se cambia el evento para fabricar una oportunidad.
  - **E:** las tres bradicardias NO.
  - **F:** la consolidación sola no crea C14. Las neumonías son YES por C, con
    una sola oportunidad.
  - **G:** los dos TEP YES.
    - Se conserva qué componente concreto se observa: sobrecarga del VD, TVP
      proximal, integración con la hemodinamia, estrategia de reperfusión o
      anticoagulación.
    - POCUS realizado no es C14 demostrado.
  - **H:** `renal_colic_34m` NO. La pielonefritis 58f es YES por C, no por la
    ecografía renal formal.
  - **Filas claras del borrador:** se mantienen.
- **Metadata C14:**
  - antes de escribirla, la tabla final derivada;
  - cada fila con procedencia (`human_clinical_review`, Nicolás Pineda,
    2026-09-28, grupo de decisión, versión);
  - un NO se registra con su razón, nunca como ausencia;
  - `acs_54m_inferior` queda NOT REVIEWED;
  - el fallback se retira caso a caso, sin tocar el mecanismo global.
- **Pruebas C14 exigidas (§21):**
  - YES evaluable; NO no confirmable; NOT REVIEWED sólo transitorio;
  - YES sin evidencia automática;
  - confirmación docente;
  - observación incidental;
  - el target no decide C14;
  - históricos intactos;
  - congelado al iniciar.
  - Además: sin doble conteo (§22), la evidencia esperada no es lista cerrada
    (§36), NO no es falla (§37), YES no es OBSERVED (§38) y C14 incidental bajo
    otro R1/R2/R3 (§39).
- **DF-19 · KD-01 autorizado:** corrección por clase de vía + fármaco + dosis
  sin verbo, con la vía primero. Sólo vías soportadas. Pruebas positivas y
  negativas, EN y sin regresión ES, ejecución y Management Trace.
- **Baselines:**
  - **SPANISH PILOT BASELINE = `939978a`**; no se reemplaza retroactivamente.
  - Después de KD-01, con la suite completa en verde, el nuevo SHA se registra
    como **ENGLISH VALIDATION BASELINE**.
  - Cada corrida de validación registra CORPUS VERSION, LANGUAGE, ENGINE
    BASELINE y KNOWN DEFECTS VERSION.
  - La primera medición en español usa el baseline español.
- **Defectos conocidos:** actualizar la lista después de KD-01. No se corrigen
  KD-02 a KD-14 salvo que KD-01 resuelva alguno por la misma causa o aparezca
  una regresión.
- **DF-15 · piloto aprobado.** Los 18 documentos son PILOT MATERIAL V1.
  - No se modifican salvo error factual, spoiler, corrupción del DOCX o una
    inconsistencia que los vuelva inutilizables; y en ese caso se documenta,
    se versiona y se verifica de nuevo.
  - Se mantienen la anotación (clínico primario, 20 % doble, tercero o
    consenso) y VC-3.
  - La IA no hace de estándar de referencia.
  - **THE PHYSICIANS ARE NOT BEING ASSESSED.**
- **Se mantienen:**
  - DF-17 diferido;
  - C2 y C15 deshabilitadas;
  - los 9 PARTIAL inactivos.
- **Fuera de alcance del ciclo 5:**
  - corregir clínicamente `acs_54m_inferior` sin aprobación;
  - revisar TD1/F1/C1/C3/C4 caso por caso;
  - cambiar puntajes, D1–D5, eventos críticos o el −3;
  - override, fuentes externas, construct coverage;
  - correr el piloto sin respuestas humanas reales;
  - contactar, enviar o distribuir;
  - PR, merge o release;
  - iniciar el ciclo 6.

## Decisiones del 2026-09-28 (apertura del ciclo 4)

- **DF-12 · aprobada como regla TRANSITORIA.**
  - Mientras un caso u objetivo siga NOT REVIEWED, conserva el comportamiento
    previo para no perder oportunidades antes de la revisión clínica.
  - **No es la arquitectura final.** El estado objetivo es: CASO → OPORTUNIDADES
    REVISADAS EXPLÍCITAMENTE → SOLO LAS OPORTUNIDADES REALES SON EVALUABLES.
  - El fallback se retira progresivamente: C14 primero y después TD/F/C, a
    medida que se aprueben sus oportunidades. No se retiran otros fallbacks sin
    revisión clínica.
- **DF-14 · confirmado.**
  - Los 9 vínculos PARTIAL siguen inactivos y documentados para revisión
    posterior.
  - PARTIAL IS NOT A DEFECT: los PARTIAL activos y defendibles siguen activos.
  - Se prioriza lo significativo, interpretable y trazable sobre la cobertura
    máxima.
- **DF-16 · a y b autorizados para el ciclo 4**, por clase, EN/ES, con frases
  nuevas y BEFORE/AFTER.
  - Los residuos MEDIUM/LOW se corrigen solo si son deterministas, pequeños, de
    bajo riesgo y del mismo mecanismo: vía compartida, listas de órdenes,
    variantes comunes.
  - Los independientes («si» = «whether», texto tomado como respuesta,
    traducciones, «OK to discharge») se documentan primero. Si alguno resulta de
    alto valor y barato, se propone para el ciclo 5.
- **DF-13 · C14 no se activa todavía**, ni siquiera los 6 YES y 6 NO claros.
  - El ciclo 4 prepara las decisiones A–H agrupadas y puede mejorar el borrador.
  - C14 es el primer objetivo con el flujo: BORRADOR DEL AI ADVISOR → REVISIÓN
    CLÍNICA HUMANA → METADATA APROBADA.
- **DF-17 · DEFERRED / DESIGN AFTER C14 PILOT.**
  - Debe seguir siendo posible que el docente indique que la oportunidad
    declarada no ocurrió, o que reconozca una observación incidental.
  - No se agrega interfaz ni lógica.
- **DF-4 · C2 sigue deshabilitada.** No se fija un número artificial de casos;
  se revisa con un banco de trauma más amplio. No se trabaja en C2 en el ciclo 4.
- **DF-15 · piloto aprobado con modificaciones.**
  - 6 médicos de urgencia × 3 casos, unos 18 documentos. Cada idioma, escrito
    por quien lo escribe naturalmente; no se traduce.
  - Los seis casos propuestos.
  - Instrucción breve, alineada con la guía del residente: interpretación,
    acción, expectativa y reevaluación, en texto libre y sin cajas obligatorias.
  - **VC-1:** aprobado. Dejar listos los 18 documentos; el docente recluta y
    distribuye.
  - **VC-2:** anotación primaria por un clínico, 20 % doble por un segundo
    clínico, y desacuerdo por un tercero o por consenso explícito.
  - **VC-3:** las indicaciones de regreso son FOLLOW-UP / DISPOSITION SAFETY
    PLAN. Cuentan como contingencia solo si traen una condición explícita que
    modifica el plan.
  - **VC-4:** revisar de nuevo los textos en español y verificar los DOCX
    estructuralmente. La verificación visual en Word la hace el docente.
  - **Split development/sealed:** no se sortea antes de que vuelvan los
    documentos; el ciclo 4 define el procedimiento, reproducible y auditable.

## Cierre del ciclo 4 (2026-09-28)

- **PILOT BASELINE: `939978a5147ab859a6dc3566ef4e1a98611a5093`**, motor
  `0.24.13-clinical-encounter`.
  - **Suite completa:** 4877 pasan, 77 omitidas, 2 xfail y 0 fallas.
  - **Regresiones:** 56 de 56.
  - **Corpus de ensayo:** 96/96 órdenes en ES y EN, idéntico al ciclo 3
    decisión por decisión.
  - **Detalle:** `validation/pilot_v1/PILOT_BASELINE.md`.
- **DF-16a y DF-16b, corregidos por clase**, EN/ES, con la traza verificada.
  DF-16c quedó corregido con la vía compartida. Los restos están en el
  manifiesto de defectos conocidos (KD-01 a KD-14).
- **DF-13, C14:** ocho decisiones A–H listas para responder. **C14 no está
  activado**; la regla de transición sigue y es temporal (DF-12).
- **DF-15, piloto: listo para distribuir y no enviado.**
  - `validation/pilot_v1/`: 18 documentos VC2, **DOCX STRUCTURALLY VERIFIED**
    (no en Word);
  - el mensaje para los médicos, la matriz y el sorteo definido;
  - la anotación y la adjudicación, y el manifiesto de defectos conocidos.
- **Herramienta del validation corpus**, sin un segundo parser:
  - bug corregido: los planes se emparejaban con el tipo equivocado;
  - comando `split`;
  - hoja del segundo anotador;
  - taxonomía del §40;
  - columnas de impacto y de defecto conocido.
- **La primera corrida completa encontró 5 fallas dependientes del orden.** Las
  causó la prueba nueva de DF-16 por la página real, que dejaba la variable de
  modo offline en el proceso. Se reprodujo y se corrigió en las pruebas; el
  código de la aplicación no cambió.
- **Sin cambios:**
  - D1–D5 y la escala 0–3;
  - los eventos críticos y el −3, el puntaje ajustado y el spider;
  - la confirmación docente;
  - los mappings (los 9 PARTIAL siguen inactivos);
  - C2 y C15, deshabilitadas.
- **Nada se contactó, envió, fusionó ni publicó.** El ciclo 5 no se inició.

## Decidido e implementado

| ID | Tema | Estado |
|---|---|---|
| DF-13 | C14 caso por caso (decisiones A–H) | **Aplicado en el ciclo 5:** 14 YES y 16 NO con procedencia; `acs_54m_inferior` pasa a DF-20 |
| DF-19 | KD-01, la vía antes del fármaco | **Corregido y verificado en el ciclo 5**; es el ENGLISH VALIDATION BASELINE `ec1c77f` |
| 59Z | Un encuentro nuevo heredaba el cierre del anterior | **Corregido en la extensión nocturna** (C-2026-09-28-03), dentro del límite de 59BT |
| DF-1 | Observation opportunities (D-1 a D-6) | **Implementado y testeado.** C14 no activado: pasa a DF-13 |
| DF-2 | R1-03, R1-04 y R2-01 con contribución DIRECT/PARTIAL | **Implementado y testeado.** PARTIAL inactivos en DF-14 |
| DF-6 | Validation corpus | **Diseño cambiado por el docente** (Fase 1 en Word) · herramienta implementada · piloto en DF-15 |
| DF-16a/b/c | Listas de órdenes, orden + repetición + condición, vía compartida | **Implementado y testeado** (ciclo 4) |
| DF-10 | Seguimiento pegado al alta, EN/ES | **Implementado y testeado** |
| DOC-1 | §51 del charter | **Cerrado:** termina en «…del desempeño del residente.» |
| DF-7 | Fidelidad del razonamiento en el Management Trace | Cerrado en el ciclo 2 |
| DF-3 | MK1 | Cerrado; se usa como PARTIAL en R2-01 |

---

## Pendientes

### [HIGH VALUE · CLINICAL REVIEW] DF-20 · `acs_54m_inferior`: VD comprometido en el caso, VD normal en su POCUS

**PROBLEM**

- **El caso y el motor modelan un IAM inferior con compromiso del VD.** Lo
  sostienen:
  - la declaración coronaria;
  - el comentario del caso;
  - las decisiones docentes del 2026-09-19 y del 2026-09-21 (4, 7 y 10);
  - el guion «bueno» de la tanda 20.
- **Su POCUS dice VD normal**, con «RV free wall contracts normally», y una
  VCI de 1.8 cm con 50 % de colapso.
- **En un mismo encuentro el residente ve SDST en V4R y un VD normal.** Si
  confía en el POCUS y da nitroglicerina a 20 mcg/min, la PA cae de 100/64 a
  67/45 en 10 minutos.

**EVIDENCE**

- **Auditoría:** `docs/AUDITORIA_ACS_54M_INFERIOR.md`. Clasificación **B**:
  inconsistencia de datos del caso, visible en el juego. El POCUS es un
  borrador nunca revisado, y su propia nota dejó la pregunta abierta.
- **Impacto medido en copias descartables** (2,540 pruebas de SCA, POCUS y
  texto del caso):
  - con A falla 1 prueba, el texto en español;
  - con B fallan 2, las decisiones del VD.
- **Encuentros históricos:** ninguna opción los toca; el caso se congela con
  el encuentro.
- **Fuera del piloto de validación:** sus seis casos no incluyen SCA.

**RECOMMENDATION**

**Opción A.** Corregir el VD y la VCI del POCUS al compromiso del VD, con la
redacción que usted apruebe. Después:

- nueva traducción del pasaje en español;
- su decisión C14 (YES o NO) para el caso.

**ALTERNATIVES**

- **B:** quitar el compromiso del VD.
- **C:** mantener ambas, declarando el punto docente.
- **D:** dejarlo sin revisar.

**COST / EFFORT**

- **Docente:** aprobar dos líneas de texto y una fila C14.
- **AI Advisor:** una sesión corta.

**RISK**

- Mientras no se decida, el caso sigue mostrando datos contradictorios.
- C14 conserva la regla de transición en ese caso.

**DECISION NEEDED**

1. ¿Cuál representación es la correcta: A, B, C o D?
2. Si A, el texto del VD y de la VCI.
3. C14 YES o NO para el caso.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-15 · Piloto del validation corpus, Fase 1

**PROBLEM**

Hace falta lenguaje clínico auténtico, independiente del lector, para medir su
generalización (DF-6 modificado por el docente).

**EVIDENCE**

`docs/VALIDATION_CORPUS_FASE1.md`:

- plantilla Word ES/EN: 12 documentos del piloto en `validation/plantillas_v1/` (retirados en el ciclo 4; los reemplaza `validation/pilot_v1/`);
- ingesta DOCX determinista por la página real;
- anotación ciega, adjudicación, clases y métricas;
- 25 tests;
- una corrida sintética de punta a punta.

**CICLO 4 · PREPARADO, NO ENVIADO.** Todo está en `validation/pilot_v1/`
(empiece por su `README.md`):

- **Documentos.** Los 18 documentos VC2, personalizados, **DOCX STRUCTURALLY
  VERIFIED** y no verificados en Word.
- **Material de envío y de trabajo:**
  - la matriz de asignación;
  - el texto del mensaje en ES y EN;
  - la anotación (plantilla, guía y adjudicación);
  - el procedimiento del sorteo;
  - el manifiesto de defectos conocidos;
  - el baseline.
- **La propuesta del ciclo 3**, de abajo, queda como antecedente.

**RECOMMENDATION del ciclo 3** (piloto, §96)

- **Médicos y casos:**
  - 6 médicos en español, en 3 pares;
  - 3 casos cada uno, de C01–C06;
  - 45–60 min por médico;
  - 18 documentos, unas 150–270 entradas.
- **Inglés:** sólo con médicos que escriban naturalmente en inglés.
- **Subconjuntos:**
  - development y sealed 50/50 por médico;
  - sorteo dentro de cada par, después de recibir y antes de leer.
- **Anotación:**
  - ciega, antes de correr el motor;
  - doble en el 20 %;
  - adjudicación con propuesta determinista.

**ALTERNATIVES**

- Todo el piloto como development, sellando recién en la fase siguiente: más
  datos para diagnosticar y ninguna medición de generalización.
- 4 médicos: menos carga y menos variabilidad.

**COST / EFFORT**

- **Médicos:** unas 5–6 h en total.
- **Custodio:** 1,5–2 h.
- **Anotación:** 3–4,5 h, más ~1 h de doble anotación.
- **Adjudicación:** ~1–1,5 h por subconjunto.
- **IA:** US$0.

**RISK**

- **Texto del caso en español:** no confirmado aprobado.
- **Word real:** sin probar; se validó con python-docx, no con Word.
- **n chico:** las métricas del piloto son descriptivas.

**DECISION NEEDED** (VC-1 a VC-4 se decidieron el 2026-09-28)

- **Acción docente:**
  - abrir los 18 documentos en Word;
  - confirmar el texto en español de los seis casos, que es la aprobación para
    el piloto;
  - enviarlos.
- **Anotación:** decidir quién anota, quién hace la doble anotación y quién
  adjudica.

El AI Advisor no contacta a nadie ni envía nada.

---

### [HIGH VALUE · METHODOLOGICAL REVIEW] DF-22 · Clases del lector y de la página halladas por la auditoría nocturna

**PROBLEM**

- **El lector pierde órdenes de primera línea por la forma de la oración.**
  - «Anaphylaxis …: epinephrine 0.5 mg IM now, repeat in 5 minutes if no
    response» no da la adrenalina: toda la frase queda como plan de
    repetición.
  - «Atropina 1 mg ev, si no responde, marcapaso…» no da la atropina.
  - Con un punto en lugar de «:» o «,», ambas se ejecutan.
- **Son 9 clases CRITICAL.** Además de las anteriores:
  - «Ahora X y luego repetir»;
  - «Por … instalo …»;
  - «cambia a Ringer»;
  - destino «con/on» un tratamiento;
  - «Activo hemodinamia»;
  - TXA «en 10 min» en un paquete urgente;
  - un hallazgo tras la orden («satura 86 % con la naricera»).
- **La página dice más de lo que pasó:**
  - «Urgent intervention executed» cuando nada corrió (59O-03);
  - preguntas atadas a órdenes mal leídas, que al contestarlas pueden
    ejecutar lo equivocado (59O-06).

**EVIDENCE**

- `docs/AUDITORIA_TRACE_CICLO5.md`: 90 frases INTERNAL AUDIT DATA y 6
  guiones en la página real.
- La sesión principal reprodujo 3 en el lector, con su control.
- **No es regresión:** las 90 frases se leen igual en `939978a` y hoy. Están en
  los dos baselines.

**RECOMMENDATION**

1. **No corregir las clases del lector antes del piloto, ni registrarlas como
   defectos conocidos.** Así el piloto mide su frecuencia real sin sesgo (59I).
   Después, cada falla del piloto de una de estas clases se prioriza con
   `PRIORIZACION_POST_PILOTO.md`, anotando que la auditoría interna ya la
   había visto.
2. **Aparte, autorizar la corrección de 59O-03 antes de cualquier piloto con
   residentes:** avisar «ejecutada» sólo después de ejecutar. Es veracidad de
   la página, no lectura, y no cambia lo que mide el piloto de validación.

**ALTERNATIVES**

- Registrar las 9 como KD-16 a KD-24 antes del piloto. Las etiquetas serían
  fieles, pero el piloto contaría menos fallas nuevas.
- Corregirlas ahora. El piloto pierde independencia, y se corre el riesgo de
  ajustar el lector a frases escritas por una IA.

**COST / EFFORT**

- **Docente:** dos respuestas.
- **AI Advisor:** 59O-03 es una sesión corta.

**RISK**

Mientras tanto, quien escriba así recibe un encuentro distinto de lo que
escribió, y el Trace le atribuye la omisión.

**DECISION NEEDED**

1. ¿Piloto independiente (recomendado) o registrar las clases como
   conocidas?
2. ¿Se corrige 59O-03 antes del piloto con residentes?

---

### [CLINICAL REVIEW] DF-23 · Inconsistencias clínicas fuera de `acs_54m_inferior`

**PROBLEM**

| Caso | Contradicción |
|---|---|
| Las 4 oclusiones (de Winter, posterior, inferior, tronco) | El primer POCUS repetido baja la severidad redactada a «mildly reduced» con la arteria cerrada. En `acs_52m_de_winter`: «Akinesis» al llegar, «mildly reduced» a los 30 min, «akinetic» a los 100 |
| `bradycardia_bb_54f` | Somnolienta en la presentación, «Alert» en el monitor |
| `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m` | FA como antecedente; el monitor muestra ritmo sinusal, derivado de la FC |
| Mujeres en edad fértil (p. ej. `pulmonary_embolism_33f`) | El estado de embarazo no está redactado |
| Todo el POCUS del banco | Sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW`), también en los 14 casos C14 YES |

**EVIDENCE**

- La sesión principal verificó las tres primeras filas en el motor.
- Detalle en `docs/AUDITORIA_NOCTURNA_CICLO5.md`, sección 9.
- No se cambió ningún dato: cada fila exige elegir cuál representación es
  la correcta.

**RECOMMENDATION**

1. **Oclusiones:** decidir junto con DF-20, empezando por de Winter, que es
   C14 YES. Si la severidad redactada es la correcta, el POCUS repetido
   debería conservarla hasta la reperfusión.
2. **`bradycardia_bb_54f`:** que el monitor muestre lo que dice la
   presentación.
3. **FA:** decidir si el ritmo de llegada es FA (y entonces el ECG y el
   monitor la muestran) o si el antecedente se quita.
4. **Embarazo:** decidir qué responde el caso si se pregunta.
5. **POCUS:** confirmar el POCUS de los 14 casos C14 YES (TD-04).

**COST / EFFORT**

- **Docente:** revisar 5 puntos.
- **AI Advisor:** una sesión por punto aprobado, con sus pruebas.

**RISK**

En de Winter, la evidencia esperada de C14 descansa en la evolución de la
pared, y el motor la muestra de forma implausible.

**DECISION NEEDED**

Una respuesta por fila.

---

### [METHODOLOGICAL REVIEW] DF-24 · Integridad longitudinal: correcciones propuestas

**PROBLEM**

La auditoría longitudinal y la de integridad no encontraron nada CRITICAL ni
HIGH, pero dejaron correcciones que tocan informes, el radar o eventos
críticos. Ninguna se aplicó.

| ID | Qué | Toca |
|---|---|---|
| L-F01 | Los temas de historia se leen del banco vivo, no del caso congelado. Un cambio del banco reinterpreta encuentros antiguos, también el tamizaje de `bradycardia_cause_unexamined` | informes y tamizaje de eventos críticos |
| I-F02 / L-F02 | La exportación del residente no trae quién confirmó la rúbrica, y el perfil elige la «última» por hora y no por número de revisión | exportación y radar |
| L-F04 | El perfil ordena por fecha de confirmación: «último encuentro» y «cambio» pueden contradecir la trayectoria | radar |
| I-F18 | Al migrar una base antigua, la foto de una confirmación absorbe observaciones posteriores | confirmación |
| L-F07 | C14 sigue abierto por la transición en casos generados, en PS001 y en los 9 candidatos del catálogo de hipoglicemia, aunque los casos de hipoglicemia del banco dicen NO | oportunidades |
| TD-09 | La cola docente completa tarda 3 s con 1000 encuentros pendientes y 14,5 s con 5000 | rendimiento |

**RECOMMENDATION**

1. **Aprobar L-F01:** leer los temas del caso congelado. Devuelve el principio
   de que un encuentro se lee con su propio caso.
2. **Aprobar I-F02 y L-F02:** con un reloj normal dan los mismos resultados.
3. **L-F04:** ordenar el perfil por la fecha del encuentro. Es una decisión de
   producto, porque cambia qué significa «último».
4. **I-F18:** aprobar.
5. **L-F07:**
   - mantener la transición en casos generados y PS001, que no tienen
     declaraciones (DF-12);
   - llevar el NO de hipoglicemia a los candidatos del catálogo sólo si usted
     lo confirma.
6. **TD-09:** corregir antes de cohortes de más de unos 20 residentes. El
   piloto no lo necesita.

**Tres decisiones de corrección (59BC):**

1. **Observación anulada.** Hoy el residente ve el juicio anulado, las notas y
   el motivo. Se recomienda mantenerlo y decírselo al docente en el formulario
   de anulación.
2. **Retirar una rúbrica confirmada** hoy es imposible. Se recomienda un
   estado «retirada» que sólo se agrega, cuando haga falta. No es urgente.
3. **Meta subida después de confirmar.** Se recomienda marcarla como
   «confirmado con una meta anterior», sin cambiar nada automáticamente.

**COST / EFFORT**

- **AI Advisor:** L-F01, I-F02, L-F02 e I-F18 caben en una sesión con sus
  pruebas.
- **L-F04:** decisión y una sesión.

**RISK**

- **Hoy L-F01 es latente:** el registro no muestra cambios de temas de
  historia en el banco.
- **L-F02 y L-F04** sólo se notan con relojes desfasados o confirmaciones fuera
  de orden.

**DECISION NEEDED**

1. ¿Se aprueban L-F01, I-F02, L-F02 e I-F18?
2. L-F04: ¿fecha del encuentro o de la confirmación?
3. L-F07.
4. Las tres decisiones de corrección.

---

### [CLINICAL REVIEW (futuro)] DF-21 · Oportunidades de TD1, F1, C1, C3 y C4

**PROBLEM**

TD1, F1, C1, C3 y C4 siguen con la regla de transición: observables en todo
encuentro. Retirarla exige revisar caso por caso, como se hizo con C14.

**EVIDENCE**

- **El borrador está en `docs/tdfc/`.** No se escribió nada en el banco.
- **155 combinaciones:** 73 YES, 60 NO y 22 dudosas.
- **Las 22 dudosas caben en 8 decisiones** (TDFC-1 a TDFC-8), cada una con su
  recomendación.
- **Cada combinación dudosa depende de una sola decisión.**
  `generar_matriz.py` rederiva las cuentas y la matriz.

**RECOMMENDATION**

Resolver TDFC-1 a TDFC-8 cuando usted pueda. No bloquean el piloto.

**RISK**

- **Si se aprueban TDFC-7 y TDFC-8, ningún caso del banco ofrece C4.** Al
  retirar la transición, C4 dejaría de ser observable en el banco. Es una
  consecuencia, no una propuesta. DF-25 (G2) trata cómo darle oportunidades.
- **Las filas de `acs_54m_inferior`** esperan a DF-20.

**DECISION NEEDED**

TDFC-1 a TDFC-8 (`docs/tdfc/DECISIONES_TDFC.md`).

---

### [CLINICAL + METHODOLOGICAL REVIEW (futuro)] DF-25 · Banco de casos: asignación de desafíos y brechas

**PROBLEM**

Los desafíos se asignan por familia, pero lo que los hace observables está en
casos concretos, a veces fuera de esas familias.

- R1-07 trae su elemento explícito en 1 de sus 9 casos.
- R2-02 es SCA en un 75 %.
- R1-03, R1-04 y R2-01 no tienen casos del banco.
- C4 no tiene ningún contexto procedural declarado.

**EVIDENCE**

`docs/AUDITORIA_BRECHAS_BANCO_CICLO5.md`: 18 brechas, 8 de clase A, 2 B, 4 C y
4 D.

**RECOMMENDATION**

Las de clase A no piden casos nuevos:

- declarar R1-07 por caso en los 6 casos con impresión de entrega redactada;
- sortear primero la familia y luego la variante;
- revisar los 3 procedimientos dolorosos para C4;
- abrir R1-04 y R2-01 a casos del banco con declaración por caso.

**DECISION NEEDED**

Las 10 preguntas del final de esa auditoría. No bloquean el piloto.

---

### [HIGH · MEDIUM · LOW] DF-16 · Defectos del lector encontrados en el ciclo 3

**CICLO 4.**

- **a, b y c, corregidos por clase**, EN/ES, con frases nuevas, antes y
  después, y la traza verificada. Detalle en
  `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, sección «Ciclo 4 · DF-16».
- **d a i siguen documentados**, ahora como defectos conocidos del baseline
  del piloto: d = KD-03, e = KD-04, f = KD-05, g = KD-06, h = KD-07,
  i = KD-08.
- **Lo encontrado al verificar**, de KD-01 a KD-14, está en
  `validation/pilot_v1/KNOWN_DEFECTS.md`.

**PROBLEM**

Al probar DF-10 y la ingesta del validation corpus con frases sintéticas
escritas para las pruebas (no del corpus), aparecieron defectos distintos de los
autorizados. Por control de alcance se registran y no se corrigen (§63).

**EVIDENCE**

Cada fila se reprodujo con `parse_family_actions` o por la página real.

| # | Prioridad | Defecto | Ejemplo sintético |
|---|---|---|---|
| a | **HIGH** | Una lista de preparación pierde miembros según cómo empiece | «Monitor, vía venosa y oxígeno por mascarilla a 8 L/min» → sólo acceso venoso; sin «Monitor,» → sólo oxígeno |
| b | **HIGH** | Una cláusula de repetición condicional vuelve condicional la orden entera, y la orden queda como modelo de trabajo | «Salbutamol 5 mg + ipratropio 0.5 mg nebulizados ahora, repetir cada 20 minutos por 3 veces si persiste…» → nada se ejecuta ahora |
| c | MEDIUM | «nebulizados» (masculino plural) no se lee como vía; una vía compartida al final de una lista queda sólo en el último fármaco | «salbutamol + ipratropio … nbz» → salbutamol sin vía; se pide aclaración |
| d | MEDIUM | Un texto escrito con una aclaración pendiente se toma como su respuesta: la orden que trae no se ejecuta y su vía se asigna a la orden retenida | Aclaración de vía pendiente + «Hidrocortisona 200 mg ev» → salbutamol «IV», que se vuelve a rechazar; la hidrocortisona no se ordena |
| e | LOW | «si» como «whether» se lee como condicional | «reevaluar … si puede hablar frases completas» → plan condicional |
| f | MEDIUM | «OK to discharge with…» no se reconoce como alta | Registrado en DF-10 |
| g | MEDIUM | Una receta unida al alta con «with/con» se pierde | «con paracetamol», «with ibuprofen» |
| h | LOW | «con hora en policlínico» no se lee como cita | — |
| i | LOW | Cuatro líneas del mensaje de la orden retenida sin traducción | «I recognised…», «Still to state…», «In your own words…», «What you already wrote is kept.» |

**Qué no es un defecto.** Oxígeno sin flujo absoluto («O2 por mascarilla para
saturar sobre 94 %») se retiene por diseño. El piloto medirá si los clínicos lo
consideran una aclaración innecesaria.

**RECOMMENDATION**

- **a y b:** corregir por clase en el ciclo 4, con pruebas de frases nuevas.
  Ninguno viene del corpus, así que corregirlos no lo contamina.
- **d:** revisarlo junto con la Fase 2, porque es interacción en vivo.
- **Resto:** según capacidad.

**ALTERNATIVES**

- Esperar al piloto para dimensionarlos. Así el piloto mide un motor con
  defectos ya conocidos.

**COST / EFFORT**

- a y b: una sesión cada uno.
- c, e, f, g y h: horas.
- i: minutos.

**RISK**

- Tocar el lector compartido: se mitiga con regresiones, el corpus de ensayo
  EN/ES y la suite completa.

**DECISION NEEDED**

¿Autoriza corregir a y b, y cuáles más, en el ciclo 4?

---

### DF-19 · KD-01 · CERRADO en el ciclo 5

- **Qué se hizo:** la corrección por clase de la vía escrita antes del fármaco,
  incluida la misma confusión dentro de una lista.
- **Pruebas:**
  - 53 pruebas nuevas;
  - corpus de ensayo idéntico en ES y EN;
  - 56 de 56 regresiones;
  - suite completa verde en `ec1c77f`.
- **Detalle:** `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, sección del ciclo 5.
- **Lo que queda aparte:**
  - KD-15, el fluido nombrado en palabras (otra causa);
  - KB-02, «IN» antes del fármaco (por diseño);
  - KD-04, si el piloto lo muestra frecuente.

---

### [METHODOLOGICAL REVIEW] DF-14 · Vínculos PARTIAL inactivos

**PROBLEM**

La verificación del ciclo 2 encontró vínculos textuales cuya contribución no se
puede describir con claridad. Por la regla de §93 no se activaron.

**EVIDENCE**

`docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md` §6 lista 9 inactivos:

- **R1-03:** PC5 L3, ME 2.2 vía TD1 h8, ME 2.4.
- **R1-04:** PC6 L1/L4, ME 4.1 vía TP6 h4 y C1 h6, ME 2.4.
- **R2-01:** PC1 L3 (segunda oración), MK1 L3, ME 2.4.

Cada uno trae el motivo.

**RECOMMENDATION**

Mantenerlos inactivos. Activar alguno sólo si el docente puede enunciar el
componente observado y lo que queda fuera.

**ALTERNATIVES**

- Activar PC5 en R1-03 como PARTIAL condicionado a que la prioridad sea un
  fármaco. Exigiría una condición por encuentro que hoy no existe.

**COST / EFFORT**

- Revisión docente: minutos.
- Activar uno: una línea de datos y su test.

**RISK**

Evidencia más débil presentada como contribución.

**DECISION NEEDED**

¿Se mantienen inactivos?

---

### [STRUCTURAL] DF-12 · Regla de transición para objetivos NOT REVIEWED

**Qué se implementó** (§56, el mecanismo más conservador y reversible):

- Un objetivo sin declaración en un caso conserva la regla anterior, rotulada
  `transition_fallback`: TD1, F1, C1, C3 y C4 en todo encuentro (C14 ya sólo en
  `acs_54m_inferior`, el único caso sin revisar), y un
  Decision Challenge sólo en el encuentro generado para él.
- NOT REVIEWED nunca es NO.
- Los registros legados reciben la misma regla y nunca las declaraciones
  actuales.

**Evidencia:**

- `observation_opportunities.py`;
- `test_observation_opportunities.py` (19 tests);
- `docs/OBSERVATION_OPPORTUNITIES.md` §3.

**Efecto hoy:** ninguno sobre la elegibilidad, porque ningún caso declara
todavía.

**Cómo se retira:** caso por caso, al aprobar su declaración (DF-13).

**DECISION NEEDED:** confirmar la regla. Alternativa: cerrar C14 a los casos
no revisados, lo que quitaría oportunidades antes de revisarlas.

---

### [METHODOLOGICAL REVIEW] DF-17 · *Faculty override*: registrar que una oportunidad no ocurrió

**Hoy:**

- La evidencia esperable es guía, no lista blanca.
- El docente puede reconocer evidencia no prevista o simplemente no valorar.
- No hay un registro explícito de «la oportunidad declarada no ocurrió en este
  encuentro».

**No se implementó.** No hacía falta para el piloto (§ «no implementes
mecanismos complejos de override»).

**RECOMMENDATION:** esperar a que la activación de C14 muestre si hace falta.
Si hace falta, el diseño mínimo es un desenlace de valoración «oportunidad no
ocurrida», con motivo y auditado, que no cuente como observación.

**DECISION NEEDED:** ¿se necesita, y cuándo?

---

### [CLINICAL + METHODOLOGICAL REVIEW] DF-4 · C2

- **Sin cambios en el ciclo 3.** C2 sigue deshabilitada (`objective_not_enabled`
  en la resolución de oportunidades).
- **Evidencia:**
  - `docs/AUDITORIA_OPORTUNIDAD_C2.md`;
  - EPA Guide v1.1, p. 20: C2 pide variedad, incluido el trauma penetrante,
    el entorno clínico y los casos pediátricos;
  - el banco tiene 2 casos adultos.
- **RECOMMENDATION:** mantenerla deshabilitada. Si se habilita, que sea caso por
  caso mediante declaraciones de oportunidad.
- **DECISION NEEDED:** ¿qué amplitud de casos trauma consideraría suficiente? Es
  una decisión clínica; el AI Advisor no propone un número.

---

### [LOW PRIORITY] DF-18 · Evidencia de fuentes externas (multisource)

- **Por qué hoy no cabe:** la unidad de evidencia es una fila de
  `mrs_progress_observations`, con `attempt_id NOT NULL`. Sólo el simulador
  produce evidencia (`evidence_source: management_reasoning_simulator`).
- **Qué haría falta:** otra fuente (observación directa, OSCE) necesitaría su
  propia tabla con el mismo formato de contribución y su propio
  `evidence_source`.
- **No se implementó** (fuera de alcance, §52).
- **DECISION NEEDED:** ninguna ahora.

---

### [METHODOLOGICAL REVIEW] DF-9 · Penalidad −3, doble efecto de safety y varios eventos por una conducta

- **Se mantiene sin cambios** (charter §19 a §22 y §47):
  `max(0, base − 3 × eventos confirmados)`, el doble efecto sobre D3 y el total,
  y la acumulación de eventos.
- **Los eventos críticos siguen siendo una señal independiente.**
- **DECISION NEEDED:** ninguna ahora.

---

### [LOW PRIORITY] DF-11 · Residuos menores de la lectura

- **«since» en inglés.** No se lee como razón, porque también es temporal.
- **En inglés, «and I will».** «to reduce the congestion and I will recheck…»
  registra «and I will» dentro de la expectativa.
- **Hiperkalemia.** «Hyperkalemia with peaked T waves» e «Hiperkalemia con T
  picudas» no se leen como modelo: el vocabulario de hallazgos es cerrado.
- **Ortografía corregida en las citas.** «rythm» → «rhythm» y «urianalysis» →
  «urinalysis»; lo fijan las regresiones v0814 y v0816.
- **Guion 5, decisión 9.** «por» en español no se lee como causal.
- **`objectives.TARGET_SOURCE`.** Cita las páginas de la edición v1.0 de la EPA
  Guide.
- Los defectos nuevos del ciclo 3 están en DF-16.
- **DECISION NEEDED:** ninguna urgente.

---

### DF-5 · C15

Deshabilitada, sin cambios. No hay encuentros diseñados para cuidados al final
de la vida.

---

## Decidido en el ciclo 3 · registro

### DF-1 · Observation opportunities · IMPLEMENTADO

**Decisiones D-1 a D-6, como se aprobaron:**

- el bloque `objectives` en la declaración del caso;
- tres estados (YES / NO+RAZÓN / NOT REVIEWED);
- congelado con el encuentro;
- evidencia esperable como guía;
- borrador de C14 para revisión docente;
- observaciones incidentales posibles.

**Detalle:** `docs/OBSERVATION_OPPORTUNITIES.md`.

**Tests:**

- 19 en `test_observation_opportunities.py`;
- 15 en `test_foundation_challenges_as_objectives.py`;
- tests previos actualizados donde la especificación aprobada cambia la regla,
  con comentario.

### DF-2 · R1-03, R1-04 y R2-01 · IMPLEMENTADO

- **Vínculos:** 12 activos, cada uno con tipo, componente observado, lo que queda
  fuera, fuente, versión y página.
- **Etiquetas:** DIRECT y PARTIAL son etiquetas, no pesos.
- **Unidad de evidencia:** una observación confirmada, con sus contribuciones en
  la columna nueva `provenance_json`. No hay tabla nueva.
- **Automatismo:** el encuentro generado para el desafío es oportunidad, no
  evidencia.
- **Brief:** prompt 1.6. Los briefs anteriores conservan su lista de objetivos.
- **Inactivos:** en DF-14.

### DF-6 · Validation corpus · DISEÑO CAMBIADO E IMPLEMENTADO

- **Diseño:** el docente reemplazó las 240 frases por la Fase 1: médicos que
  escriben en Word a partir de casos.
- **Implementado:**
  - plantilla;
  - ingesta DOCX determinista por la página real, sin parser paralelo;
  - hojas de anotación y adjudicación;
  - métricas y trazabilidad;
  - guarda del sellado fuera del repositorio;
  - versionado y procedencia.
- **Complejidad de la ingesta:** no resultó mayor que lo previsto. El único
  hallazgo fue que el harness del ensayo resolvía una sola retención por paso.
  Se agregó `resolve_until_clear`, opcional; los 20 guiones no cambian.
- **Piloto:** en DF-15.

### DF-10 · Seguimiento pegado al alta · IMPLEMENTADO

- **Resultado:**
  - el seguimiento se conserva en EN y ES;
  - también las indicaciones de regreso;
  - el alta se ejecuta;
  - sin duplicarse, en el orden del texto y sin aclaraciones nuevas.
- **Antes/después:** de 10 altas con plan, el seguimiento se perdía en 7 y ahora
  se conserva en 9. La décima («OK to discharge») es otro defecto (DF-16 f).
- **Tests:** 17 nuevos.
- **Detalle:** `docs/MEDICION_RECONOCIMIENTO_ORDENES.md`, «Ciclo 3».
- **Test en rojo que se pasó por alto:** un test del ensayo esperaba el orden
  anterior del plan. Llegó en rojo al commit `9d35b00`, ya empujado. Se corrigió
  en `e54b919`, porque la secuencia aprobada es la del texto.

### DOC-1 · §51 · CERRADO

Se completó sólo con «residente.». Ningún otro bloque literal del charter
cambió. El addendum A1 (§102–§109) se agregó después de la §101.
