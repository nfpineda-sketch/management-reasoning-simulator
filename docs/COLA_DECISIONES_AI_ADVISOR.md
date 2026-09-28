# Decision / Recommendation File del AI Advisor

Es el archivo de la §3 de `docs/AI_ADVISOR_CHARTER.md`.

- **Qué contiene:** lo que requiere una decisión del docente, más el estado de
  lo ya decidido.
- **Formato:** el de la §40, con las clases de prioridad de la §3.
- **Actualizado:** 2026-09-28, al cerrar el ciclo 4 (sección «Cierre del ciclo
  4»). Las decisiones docentes que lo abrieron están en «Decisiones del
  2026-09-28».

## Pendientes de decisión

| ID | Clase | Tema | Estado |
|---|---|---|---|
| DF-13 | HIGH VALUE · CLINICAL REVIEW | Activar C14 caso por caso | **A–H listas para responder** (`docs/C14_DECISIONES_A_H.md`) · nada activado |
| DF-15 | HIGH VALUE · METHODOLOGICAL REVIEW | Piloto del validation corpus, Fase 1 | **Paquete listo, no enviado** (`validation/pilot_v1/`) · baseline congelado |
| DF-16 | HIGH (2) · MEDIUM (2) · LOW | Defectos del lector encontrados en el ciclo 3 | **a, b y c corregidos** · el resto, en el manifiesto de defectos conocidos del piloto |
| DF-19 | HIGH VALUE · LOW EFFORT | Arreglos baratos antes de la fase en inglés del piloto | **Propuesto para el ciclo 5** (KD-01; KD-04 si el piloto lo muestra frecuente) |
| DF-14 | METHODOLOGICAL REVIEW | Vínculos PARTIAL inactivos de R1-03, R1-04 y R2-01 | **Confirmado: siguen inactivos** · documentados para revisión posterior |
| DF-12 | STRUCTURAL | Regla de transición para objetivos NOT REVIEWED | **Aprobada como transitoria**, no permanente |
| DF-17 | METHODOLOGICAL REVIEW | *Faculty override*: registrar que una oportunidad no ocurrió | **DEFERRED:** se diseña después del piloto C14 |
| DF-4 | CLINICAL + METHODOLOGICAL REVIEW | C2 y los casos trauma | C2 deshabilitada · se revisa cuando haya un banco de trauma más amplio |
| DF-18 | LOW PRIORITY | Evidencia de fuentes externas (multisource) | Registrado · sin acción |
| DF-9 | METHODOLOGICAL REVIEW | −3, doble efecto de safety y varios eventos por una conducta | Registrado · sin decisión ahora |
| DF-11 | LOW PRIORITY | Residuos menores de la lectura | Registrado |
| DF-5 | — | C15 | Deshabilitada, sin acción |

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

### [HIGH VALUE · CLINICAL REVIEW] DF-13 · Activar C14 caso por caso

**PROBLEM**

C14 sigue observable en todo encuentro por la regla de transición (DF-12).
Ningún caso del banco declara todavía su oportunidad.

**EVIDENCE**

- **Borrador del ciclo 3:** `docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md`,
  con 31 casos: 6 YES, 6 NO y 19 UNCERTAIN.
- **Ciclo 4:** `docs/C14_DECISIONES_A_H.md` convierte las 19 dudas en ocho
  decisiones clínicas A–H, en el formato del §32. Cada una trae casos
  afectados, recomendación y consecuencias si se aprueba o se rechaza.
  `c14_review.derive` deriva las filas de las respuestas y no escribe nada.
- **Lo que reveló revisar el borrador contra los casos y el motor:**
  - los dos TEP traen una TVP proximal en el POCUS que el borrador omitía;
  - la pielonefritis séptica pertenece también a la pregunta de volumen;
  - el POCUS del bloqueo completo no refleja la captura;
  - el evento del neumotórax en el asma nombra su diagnóstico;
  - `acs_54m_inferior` declara compromiso del VD y su POCUS dice VD normal.
    Es una inconsistencia de datos para decidir; no se cambió.
- **Si se aprueban las ocho recomendaciones:** 14 SÍ, 16 NO y 1 UNCERTAIN. El
  UNCERTAIN es `acs_54m_inferior`, por esa inconsistencia.

**RECOMMENDATION**

1. Responder A–H: «A approve / B approve / C modify: … ».
2. Aprobar, modificar o rechazar la tabla de filas que resulte, con los casos
   claros.
3. El AI Advisor escribe en el bloque `objectives` sólo lo aprobado, con quién
   lo revisó y cuándo, y retira C14 de la regla de transición caso a caso.

**ALTERNATIVES**

- Activar sólo las 12 filas YES/NO ya claras y dejar las UNCERTAIN en
  transición.
- Mantener la transición completa.

**COST / EFFORT**

- **Docente:** minutos por caso.
- **AI Advisor:** una sesión corta para escribir y verificar.

**RISK**

- Un YES sin oportunidad real haría evaluable algo que el caso no ofrece.
- Un NO erróneo quitaría una oportunidad.
- Ambos riesgos se acotan a encuentros nuevos: la declaración se congela.

**DECISION NEEDED**

- Respuestas a A–H.
- Aprobación de las filas.
- Si se corrige el VD de `acs_54m_inferior`: es un dato clínico del caso y
  requiere autorización.

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

### [HIGH VALUE · LOW EFFORT] DF-19 · Arreglos baratos antes de la fase en inglés

**PROBLEM**

La comprobación con frases escritas después del fix (ciclo 4) encontró una
forma inglesa común que el lector no reconoce: la vía antes del fármaco y sin
verbo.

- **Ejemplos:** «IV morphine 4 mg», «Nebulized albuterol 2.5 mg», «Oral
  paracetamol 1 g», «IV fluids 1 L».
- **Qué pasa:** la orden vuelve como no reconocida y retiene el envío.
- **Por qué no se corrigió:** no está relacionada con DF-16, así que no cumple
  el criterio 1 del §71. Quedó documentada como KD-01.

**EVIDENCE**

- **Español:** la vía va después del fármaco y sí se lee, así que el piloto en
  español casi no la verá.
- **Inglés:** en la fase en inglés será probablemente frecuente.

**RECOMMENDATION**

- **Antes de recolectar documentos en inglés:** corregir la clase KD-01 con
  frases nuevas y medir antes y después. Es barato: la vía inicial no se salta
  hoy.
- **Si el piloto en español muestra frecuente «reevaluar … si …»** (KD-04), un
  arreglo de clase pequeño.
- **Ambos arreglos**, con el orden que fija el piloto: desarrollo sólo con
  development y nuevo baseline.

**ALTERNATIVES**

- Esperar a que el corpus inglés muestre el defecto. Costaría documentos
  independientes para descubrir algo ya conocido.

**COST / EFFORT**

Bajo: un ciclo corto, sin IA.

**RISK**

- Bajo con pruebas de frases nuevas y el corpus de ensayo.
- Cambia el lector, así que exige un nuevo baseline para la fase en inglés.

**DECISION NEEDED**

Autorizar KD-01 en el ciclo 5, o esperar el piloto.

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
  `transition_fallback`: TD1, F1, C1, C3, C4 y C14 en todo encuentro, y un
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
