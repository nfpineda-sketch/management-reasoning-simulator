# B-5 · X-1 · Español propuesto para lo que falta en la sala

> **BORRADOR PARA REVISIÓN DOCENTE. No implementado.** La decisión docente del 2026-10-07 autoriza redactar
> este español para revisarlo, no implementarlo. Ningún texto de este documento está en el código ni lo ve un
> residente. Las casillas quedan en blanco.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · código leído en `af921a9` (el runtime es el de `8ff41a4`, el
> candidato de B-1). Alcance: X-1 con el alcance ampliado (paquete, sección 2, X-1; Decision File, 2026-10-07).

**En una mirada**

- **Formulaciones nuevas para aprobar: 100**, en 8 grupos (cuadro del §11). Las preguntas de aclaración son
  **34 plantillas** que cubren las **73 frases** del motor que un residente del piloto puede ver.
- **Una convención** (X1-0) y **una decisión de diseño** (I-10).
- **Ya redactado en otro documento, no se repite:** las filas 1–18 de R-4 (A-1 a A-18), el aviso de la foto
  (J-64) y las frases de la Fase 0 (K).
- **Sólo implementación (el español existe y el código no lo aplica): 11 puntos** (§3).
- **Fuera del alcance, con su motivo** (§1): el relato del caso, 40 preguntas del motor heredado que ningún caso
  del piloto alcanza, las herramientas del personal y la ruta sin cuentas.
- **A-2:** la redacción nueva del examen respiratorio con el paciente agotado está en el §9.

## 0. Cómo leer

- Cada formulación lleva su ID, el inglés tal como lo escribe el código (lo variable va entre llaves), el español
  propuesto, sus fuentes (archivo:línea de cada texto que cubre) y su casilla.
- Una plantilla cubre todas las frases que comparten la redacción: sólo cambian los valores. Si dos frases inglesas
  dicen lo mismo con otras palabras, se propone **un** español para ambas y se anota («unifica»).
- Los vocabularios del §4.10 dicen con qué se llena cada {valor}. Cada tabla se aprueba entera.
- Al implementarse, cada línea que hoy está en inglés o mezclada se reemplaza entera: nunca una línea en dos idiomas.

**X1-0 · Convenciones propuestas** — una decisión para todo el documento

1. Trato de «tú» al residente, como en el resto de la sala («Indica…», «¿Qué … quieres …?»).
2. Códigos y unidades sin cambio: IV, IO, IM, SC, PO, mL, L/min, mcg/min, mcg/kg/min, mg/h, cm H₂O, FiO₂, PEEP,
   CPAP, BiPAP, J, ECG, POCUS, E-FAST.
3. Siglas en español donde la sala ya las usa: VMNI, FC, FR, PA, PAM, PANI, UCI.
4. Nombres de fármacos en el texto fijo, en español (noradrenalina, adrenalina, nitroglicerina, salbutamol, ácido
   tranexámico, tenecteplasa), como en B-24. Los que inserta el motor ({fármaco}) siguen lo que se decida en K-13.
5. Dispositivos con los nombres que ya usa la sala: naricera, mascarilla simple, mascarilla con reservorio, aire
   ambiente.
6. Los números se escriben como los imprime el motor (punto decimal: «0.05 mcg/kg/min»), como en el resto de la
   sala.
7. Masculino genérico («el paciente»), como en toda la sala (paquete, K, observación 2).
8. «o di cancelar», como ya dice la sala (`family_parser.py:2252`).

- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

## 1. Método y alcance

**Cómo se armó el inventario** (sin IA: lectura del código y ejecución determinista, sin conexión):

- Árbol de sintaxis de `app.py`, `family_parser.py`, `family_engine.py` y `pending_family_orders.py`: 162 plantillas
  de pregunta o aviso sobre una orden. Con `language.say` y un relleno de muestra, 51 salen enteras en español y
  **111 no**: 67 en inglés y 44 mezcladas (4 de ellas parecían en español y no lo están).
- Las funciones que arman esos textos: `_held_message`, `_rate_complaint`, el bloque de la compuerta y el resumen
  de la orden retenida.
- 132 rótulos de pantalla de `app.py` y `resuscitation_room.py`, y los avisos de `clinical_scene.py`.
- 7 encuentros en español con AppTest y cuentas, de punta a punta, guardando todo texto visible en cada paso:
  `acs_61m_posterior`, `anaphylaxis_29f`, `bradycardia_avb3_78f`, `opioid_35m`, `pulmonary_edema_75f` (dos
  recorridos) y `trauma_limb_hemorrhage_27m`.
- Cada texto se probó contra `language.say`, `language.examination`, `report_language.t` y
  `history_topics.topic_label`. Así se separa lo que falta de lo que existe y no se aplica.

**Fuera del alcance:**

1. **El relato del caso**: presentación, respuestas de la historia, fuente de la historia, hallazgos escritos por el
   caso e informes de estudios. Su español existe (`case_text/es/`) y se aprueba en el tablero después del
   despliegue. Por decisión docente del 2026-10-07, el piloto bilingüe no abre sin esa revisión (paquete, 4.1).
2. **40 preguntas del motor heredado** (`app.py:5459–5699` y `app.py:9236–9404`; anexo A). Ningún caso del
   piloto llega a ellas:
   - los 31 casos del banco declaran `engine.family`;
   - `execute_bundle` vuelve dentro de la rama del motor por familias (`app.py:9132–9221`) antes de esas preguntas;
   - `try_resolve_pending_action` vuelve en la rama `family_bundle` (`app.py:5394–5448`);
   - los tipos pendientes que las disparan sólo los fija el motor heredado (`app.py:9243–9316`);
   - las 7 sondas sólo vieron preguntas del motor por familias.
3. **Herramientas del personal**: los paneles «Developer», el diagnóstico de la imagen
   (`resuscitation_room.py:161–193`) y el aviso de anulación del facilitador (`app.py:11158`; sólo con
   `faculty_access()`).
4. **La ruta sin cuentas**: «Choose a clinical problem», «Reset scenario» y su pantalla de inicio. El piloto corre
   con cuentas.
5. **Estados de la imagen que necesitan generarla** (preparando, corrigiendo, revisión fallida;
   `clinical_scene.py:249–276`): el piloto corre sin clave de imágenes. Los avisos de «sin foto» sí entran (§7).
6. **Partes que la sala del piloto no dibuja**:
   - la rama heredada de «Diagnostics» (`app.py:10496–10544`);
   - el bloque «Latest response» de la sala cerrada (`app.py:10712`);
   - «Clinical chart · examination · results · treatment record» (`app.py:10867`);
   - la habilitación de estudios en un caso guardado antes de modelarlos (`resuscitation_room.py:196–204`).

## 2. Ya redactado: se decide en el paquete

| Qué | Dónde se decide | Estado al 2026-10-07 |
|---|---|---|
| R-4, filas 1–11 (examen respiratorio y frecuencia respiratoria) | Paquete, A-1 a A-11 | A-1 APPROVE. A-2 REVISE (redacción nueva en el §9). A-9 REVISE del inglés. A-3 a A-8, A-10 y A-11 pendientes (nivel 2) |
| R-4, filas 12–18 (accesos vasculares) | Paquete, A-12 a A-18 | El español existe; mostrarlo es implementación (I-1) |
| Aviso de la foto | Paquete, J-64 | La propuesta del §2 del cierre trata de «usted». Con el trato de la sala (X1-0, 1): «Una fotografía fija no muestra todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.» |
| Frases nuevas de la Fase 0 | Paquete, K | Activas en los dos idiomas |

## 3. Sólo implementación: el español existe y el código no lo aplica

No piden redacción nueva. Las sondas los vieron en inglés.

| # | Qué se ve en inglés | Por qué | Español que ya existe |
|---|---|---|---|
| I-1 | Filas 12–18 de R-4 en el panel del examen | `language.examination` no las conoce | `language.py:1197–1211` |
| I-2 | Rótulos y valores de la cuadrícula de signos vitales de cada respuesta del paciente («SIM TIME», «BP · MAP», «HR», «SpO₂ · SUPPORT», «RR · WORK OF BREATHING», «CRT · EXTREMITIES», «MENTAL STATUS»; «Warm», «Alert», «Mildly increased», «Nasal cannula 2 L/min») | `_vitals_grid_html` (`app.py:9868`) no los traduce | `language.py:957–960` (TIEMPO SIM, PA · PAM, FC, SpO₂ · SOPORTE, FR · TRABAJO RESPIRATORIO, LLENE · EXTREMIDADES, ESTADO MENTAL); `language.py:221–222` (Tibias, Frías, Heladas, Moteadas); estados y dispositivos, con `language.say` |
| I-3 | Descripción bajo la vista neutral («Mental status: Alert. Expression: … Work of breathing: Normal») | `resuscitation_room.py:104` agrega «Work of breathing» al resumen; la línea completa ya no coincide con ninguna regla | El resumen y «Trabajo respiratorio: …», por separado (`language.examination`) |
| I-4 | «Reasoning clarification:» en las palabras de cada orden («Indicaciones») | `_render_order_words` (`app.py:10546`) | «Aclaración del razonamiento:» (`report_language.py:983`); el registro ya lo usa (`app.py:2891`) |
| I-5 | Temas de la historia en el modo de conversación | El selector usa los nombres ingleses (`app.py:10918`) | `history_topics.HISTORY_TOPIC_LABELS_ES` y `topic_label` |
| I-6 | Aviso de la orden descartada («The held order was discarded to run this one: …») | El tipo `order_cancelled` no está entre los eventos traducidos (`app.py:10056`) | «La orden retenida se descartó para ejecutar esta: … No se administró nada de ella.» (`language.say`). Su encabezado es nuevo (L-17) |
| I-7 | Cuatro preguntas de la explicación retrospectiva de una intervención urgente | `app.py:11114` no llama a `_lang.say` | «¿Qué crees que está pasando?», «¿Qué problema estás abordando primero? (opcional)», «¿Qué esperas que ocurra o qué buscas aclarar?», «¿Qué vas a revisar y cuándo?» (`language.say`). La quinta es nueva (G-13) |
| I-8 | Rótulos del plan que viene del intento anterior | `_render_carry_forward_plan` (`app.py:10340–10352`) no llama al catálogo | Señal clínica a vigilar, Umbral para cambiar de rumbo, Siguiente prioridad de manejo, Acción alternativa, Efecto esperado, Objetivo y momento de la reevaluación (`report_language.t`) |
| I-9 | Rótulo oculto del selector de modo («Encounter») | `app.py:10884` | «Encuentro» (`report_language.t`) |
| I-10 | Resumen de la orden retenida, traducido palabra por palabra: «Entendí: **inicio norepinephrine**», «oxygen», «synchronized cardioversion 100 J». Aparece en «Entendí: …», «**Held order:** …», «Retenido hasta que respondas: …» y en la orden descartada | `_reasoning_gate_action_summary` (`app.py:8204–8276`) arma frases inglesas | Ver la decisión de diseño de abajo |
| I-11 | La línea de ventilación invasiva de «Tratamientos en curso» («Invasive ventilation: VC/AC · FiO₂ … · PEEP …») | `app.py:10475` no llama a `language.say` | «Ventilación invasiva: …» (`language.say`) |

**I-10 · Decisión de diseño.** Recomendación: en un encuentro en español, el resumen usa las etiquetas de acción del
registro, que ya están en español y se ven en «Indicaciones» («Oxígeno 2 L/min por naricera», «Solicitud de
troponina», «Reevaluación»; `_trace_action_words`). No agrega texto nuevo. Si no se aprueba, hace falta el
vocabulario V-8 (§4.10).

- Decisión docente: ☐ APPROVE (reutilizar las etiquetas del registro) · ☐ REVISE (vocabulario V-8) · ☐ DEFER
  — Nota: ________

## 4. Preguntas y avisos sobre una orden (34 plantillas, 73 frases)

Salen en la entrada «ACLARACIÓN», bajo los modos y en el aviso que queda a la vista hasta que el residente
responde. Las fuentes son de `family_engine.py` (FE), `family_parser.py` (FP) y `app.py` (APP).

### 4.1 Pedir lo que falta

**X1-C01 · Indicar o confirmar una dosis o una velocidad** — 3 frases
- EN: (a) Please specify or confirm the {fármaco} dose in {unidad}. · (b) Specify or confirm {fármaco} dose and
  units (mcg/min or mcg/kg/min). · (c) Specify or confirm the {fármaco} rate in {unidad}.
- ES: (a) Indica o confirma la dosis de {fármaco} en {unidad}. · (b) Indica o confirma la dosis de {fármaco} y sus
  unidades (mcg/min o mcg/kg/min). · (c) Indica o confirma la velocidad de {fármaco} en {unidad}.
- Valores: {fármaco}, V-1; {unidad} de (a), V-2.
- Fuentes: FE:645 (a), FE:767 (b), FE:472 (c). La sonda de la 61m vio la (b): «Specify or confirm norepinephrine
  dose and units…».
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C02 · Qué fármaco de una clase**
- EN: Which {clase} medication would you like to administer?
- ES: ¿Qué {clase} quieres administrar? (por ejemplo, «¿Qué antibiótico quieres administrar?»)
- Valores: V-1. Fuente: FE:654.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C03 · Fármaco sin respuesta modelada**
- EN: The specified {clase} agent has no modeled response in this encounter. Please clarify the medication.
- ES: El fármaco indicado como {clase} no tiene una respuesta modelada en este encuentro. Aclara el fármaco.
- Valores: V-1. Fuente: FE:656.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C04 · Ajustar algo que no se ha dado**
- EN: No {fármaco} is recorded as given. Specify the dose and route to start it.
- ES: No hay registro de que se haya dado {fármaco}. Indica la dosis y la vía para iniciarlo.
- Valores: V-1. Fuente: FE:568.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C05 · Los datos que faltan, en una lista** — 3 frases
- EN: Specify the ventilator {lista}. · Specify {lista}. (anticoagulación) · Specify {lista}. (marcapasos)
- ES: Indica {lista}. Los elementos son los de V-3, unidos con «, » y « y ». Ejemplos: «Indica el modo del
  ventilador y la PEEP en cm H₂O.» · «Indica qué anticoagulante, la dosis y la vía.» · «Indica la corriente en mA.»
- Fuentes: FE:799, FE:815, FE:845.
- Con la lista completa, el español ya existe y coincide: «Indica el modo del ventilador, la FiO₂ en porcentaje y
  la PEEP en cm H₂O.» y «Indica la frecuencia del marcapasos en latidos por minuto y la corriente en mA.»
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| X1-C06 | FE:790 | Specify which side of the chest to decompress. | Indica qué lado del tórax quieres descomprimir. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C07 | FE:703 | Specify CPAP or BiPAP. | Indica CPAP o BiPAP. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C08 | FE:684 | Specify nasal cannula, a simple mask, a non-rebreather mask, or room air. | Indica naricera, mascarilla simple, mascarilla con reservorio o aire ambiente. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C09 | FE:686 | Specify the oxygen flow in L/min. | Indica el flujo de oxígeno en L/min. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C10 | FP:3342 | Specify the thrombolytic agent and dose, for example tenecteplase 40 mg IV. | Indica el trombolítico y la dosis; por ejemplo, tenecteplasa 40 mg IV. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C11 | FP:2574 | Write the total dextrose: the grams, or the concentration with the total volume. {n} ampoules with {ml} mL may mean {ml} mL in all or in each. | Escribe la glucosa total: los gramos, o la concentración con el volumen total. {n} ampollas con {ml} mL pueden ser {ml} mL en total o en cada una. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C12 | FP:2821 · FP:2830 | (a) Specify one quantity for the treatment to repeat. · (b) Specify explicit units for the quantity to repeat. | (a) Indica una sola cantidad para el tratamiento que quieres repetir. · (b) Indica las unidades de la cantidad que quieres repetir. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C13 | FP:3312 | Specify one target ventilator mode. | Indica un solo modo de ventilación. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C14 | FE:666 | Confirm the bolus volume in mL, up to 3000 mL per order. | Confirma el volumen del bolo en mL, hasta 3000 mL por orden. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C15 | FP:2991 · FE:583 | (a) Name the part of the examination to perform: {regiones}. · (b) That examination is not available in this encounter. You may examine {regiones}. | (a) Indica qué parte del examen quieres hacer: {regiones}. · (b) Ese examen no está disponible en este encuentro. Puedes examinar: {regiones}. — {regiones}: V-4, unidas con «, » y « o » | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C16 | FE:533 · FE:538 · APP:7141 · FE:440 | (a) Please specify a question, investigation, treatment, or reassessment. · (b) Please restate the order. · (c) Please clarify the order. / Please clarify the order before it is executed. | (a) Indica una pregunta, un examen, un tratamiento o una reevaluación. · (b) Escribe de nuevo la orden. · (c) Aclara la orden antes de que se ejecute. (unifica las dos de (c)) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

### 4.2 Fuera del rango que soporta el simulador — 1 plantilla, 16 frases

**X1-R01 · Rango**
- EN: tres formas, con el mismo sentido: «Specify {parámetro} from {mín} to {máx} {unidad}.», «Set {parámetro}
  between {mín} and {máx} {unidad}.» y «Specify {parámetro} in {unidad} ({mín} to {máx}).»
- ES: **Indica {parámetro} entre {mín} y {máx} {unidad}.** — unifica las tres. Dos frases llevan su nota de dosis
  habitual al final, entre paréntesis.
- Decisión docente (la plantilla y la tabla): ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

| Fuente | EN (frase completa) | ES (frase completa) |
|---|---|---|
| FE:675 | Specify the cardioversion energy in joules, from 1 to 360. | Indica la energía de la cardioversión entre 1 y 360 joules. |
| FE:693 | Specify the NIV expiratory pressure in cm H₂O, from 0 to 20. | Indica la presión espiratoria de la VMNI entre 0 y 20 cm H₂O. |
| FE:700 | Specify the NIV FiO₂ as a percentage, from 21 to 100. | Indica la FiO₂ de la VMNI entre 21 y 100 %. |
| FE:721 | Specify a tranexamic acid dose from 0.5 to 4 g. | Indica una dosis de ácido tranexámico entre 0.5 y 4 g. |
| FE:728 | Specify an intramuscular epinephrine dose from 0.05 to 2 mg (0.5 mg is the usual adult dose). | Indica una dosis de adrenalina intramuscular entre 0.05 y 2 mg (0.5 mg es la dosis habitual en adultos). |
| FE:735 | Specify an epinephrine IV bolus from 10 to 500 mcg (50-150 mcg is the usual diluted bolus). | Indica un bolo IV de adrenalina entre 10 y 500 mcg (50-150 mcg es el bolo diluido habitual). |
| FE:744 | Specify the continuous nebulized albuterol rate in mg/h (1 to 30). | Indica la velocidad de la nebulización continua de salbutamol entre 1 y 30 mg/h. |
| FE:747 | Specify a nitroglycerin IV bolus from 50 to 3000 mcg. | Indica un bolo IV de nitroglicerina entre 50 y 3000 mcg. |
| FE:776 | Specify the dextrose infusion rate in mL/h (10 to 500). | Indica la velocidad de la infusión de suero glucosado entre 10 y 500 mL/h. |
| FE:780 | Specify the naloxone infusion rate in mg/h (0.05 to 4). | Indica la velocidad de la infusión de naloxona entre 0.05 y 4 mg/h. |
| FE:801 | Specify a tidal volume from 200 to 900 mL. | Indica un volumen corriente entre 200 y 900 mL. |
| FE:803 | Specify a tidal volume from 3 to 12 mL/kg. | Indica un volumen corriente entre 3 y 12 mL/kg. |
| FE:805 | Specify a ventilator rate from 4 to 35 breaths per minute. | Indica una frecuencia del ventilador entre 4 y 35 respiraciones por minuto. |
| FE:807 | Specify an inspiratory flow from 20 to 120 L/min. | Indica un flujo inspiratorio entre 20 y 120 L/min. |
| FE:848 | Set a pacing rate between {mín} and {máx} beats per minute. | Indica una frecuencia del marcapasos entre {mín} y {máx} latidos por minuto. |
| FE:851 | Set a pacing output between 1 and {máx} mA. | Indica una corriente del marcapasos entre 1 y {máx} mA. |

La sonda de la 75f vio FE:693 mezclada («Indica NIV expiratory pressure in cm H₂O, from 0 to 20.») y la de la 35m,
FE:780 («Indica infusión de naloxone rate in mg/h (0.05 to 4).»).

### 4.3 Un valor absoluto, uno solo

**X1-C17 · Valor absoluto, no un cambio relativo** — 4 frases
- EN: (a) Specify the absolute target oxygen flow in L/min, not a relative change. · (b) Specify absolute target
  ventilator settings, not a relative change. · (c) Specify a single absolute target infusion rate; a relative change
  or several rates is ambiguous. · (d) Specify nitroglycerin as an absolute infusion rate in mcg/min.
- ES: (a) Indica el flujo de oxígeno que quieres, en L/min, como un valor absoluto y no como un cambio relativo. ·
  (b) Indica los parámetros del ventilador que quieres como valores absolutos, no como un cambio relativo. ·
  (c) Indica una sola velocidad de infusión, como un valor absoluto; un cambio relativo o varias velocidades son
  ambiguos. · (d) Indica la nitroglicerina como una velocidad de infusión absoluta, en mcg/min.
- Fuentes: FP:2644 (a), FP:3309 (b), FP:3433 (c), FP:3522 (d).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C18 · Un solo dispositivo o flujo de oxígeno** — 3 frases
- EN: (a) Specify one target oxygen device and its flow in L/min (for example, {ejemplos}). · (b) Specify one absolute
  target oxygen flow in L/min (for example, {ejemplos}). · (c) High-flow oxygen is not a supported device in this
  encounter. Specify an available oxygen device and flow (for example, {ejemplos}).
- ES: (a) Indica un solo dispositivo de oxígeno y su flujo en L/min (por ejemplo, {ejemplos}). · (b) Indica un solo
  flujo de oxígeno, como un valor absoluto en L/min (por ejemplo, {ejemplos}). · (c) El oxígeno de alto flujo no es
  un dispositivo disponible en este encuentro. Indica un dispositivo de oxígeno disponible y su flujo (por ejemplo,
  {ejemplos}).
- {ejemplos}: V-7. Fuentes: FP:2667 (a), FP:2674 (b), FP:2642 (c). Las sondas de la 35m y la 61m vieron (a) y (b)
  mezcladas («Indica un solo target oxygen device and its flow…»).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### 4.4 Un soporte que ya corre

**X1-C19 · Iniciar, ajustar, continuar o suspender** — 3 frases
- EN: Specify whether to start, adjust, continue, or stop {NIV · the continuous nebulization · the infusion}.
- ES: Indica si quieres iniciar, ajustar, continuar o suspender {la VMNI · la nebulización continua · la infusión}.
- Fuentes: FE:690, FE:742, FE:754.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### 4.5 Lo que la vía, el estado del paciente o el soporte no permiten

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| X1-C20 | FE:705 | Specify an inspiratory pressure at least as high as expiratory pressure. | Indica una presión inspiratoria igual o mayor que la espiratoria. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C21 | FE:793 | The patient is not on a ventilator, so there is no circuit to disconnect. | El paciente no está conectado a un ventilador, así que no hay un circuito que desconectar. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C22 | FE:731 | An intramuscular epinephrine dose is given IM or SC; for the intravenous route, order a diluted bolus or an infusion. | Una dosis de adrenalina intramuscular se da IM o SC; por vía intravenosa, indica un bolo diluido o una infusión. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C23 | FE:737 · FE:749 | A diluted epinephrine bolus is given IV in this encounter. · A nitroglycerin bolus is given IV in this encounter. | En este encuentro, un bolo diluido de adrenalina se da IV. · En este encuentro, un bolo de nitroglicerina se da IV. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C24 | FE:771 | The patient is {estado} and cannot safely swallow. Use an intravenous or intramuscular route until the airway is protected. | El paciente está {estado} y no puede tragar con seguridad. Usa una vía intravenosa o intramuscular hasta que la vía aérea esté protegida. — {estado}: V-5 | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C25 | FE:673 · FP:3300 | Specify that the cardioversion is synchronized; an unsynchronized shock is outside this encounter. · Specify synchronized cardioversion; defibrillation is outside this pulse-present encounter. | Indica una cardioversión sincronizada: una descarga no sincronizada (desfibrilación) está fuera de este encuentro, en que el paciente tiene pulso. (unifica las dos) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C26 | FE:677 | Cardioversion requires a pulse-present encounter. | La cardioversión requiere un encuentro en que el paciente tenga pulso. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

### 4.6 Lo que este encuentro no tiene o no ejecuta

**X1-C27 · No disponible o no ejecutable aquí** — 5 frases
- EN: (a) That study is not one this encounter carries. · (b) A stress test is not an executable study in this
  encounter. · (c) Chest decompression is not an executable intervention in this encounter. · (d) That neuromuscular
  blocker is not supported in this encounter. · (e) The requested action ({acción}) is not executable in this
  encounter. Please clarify the order.
- ES: (a) Este encuentro no incluye ese examen. · (b) Una prueba de esfuerzo no es un examen ejecutable en este
  encuentro. · (c) La descompresión torácica no es una intervención ejecutable en este encuentro. · (d) Ese
  bloqueador neuromuscular no está disponible en este encuentro. · (e) La acción solicitada ({acción}) no es
  ejecutable en este encuentro. Aclara la orden.
- Fuentes: FE:709 (a), FE:783 (b), FE:788 (c), FE:833 (d), FE:855 (e).
- En (e), {acción} es hoy una clave interna (por ejemplo, `ventilator_disconnect`), también en inglés. En español
  se propone su etiqueta del registro (I-10).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C28 · Examen pedido que el caso no tiene**
- EN: Requested study {examen} is unavailable. Available studies: {lista}; ecg. No orders in this submission were
  executed.
- ES: El examen {examen} no está disponible. Exámenes disponibles: {lista}; ECG. No se ejecutó ninguna orden de esta
  entrega.
- Fuente: FE:611. Hoy sale mezclada: el final ya está en español y el comienzo no.
- {examen} y {lista} son hoy claves internas de los estudios. En español se proponen sus nombres, que ya existen
  (por ejemplo, «Tomografía de cerebro», «Troponina»).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**X1-C29 · Reconocido, pero esta versión no lo ejecuta**
- EN: Recognized but not executed in this build: {lista}. Any supported actions in the same order continue
  separately.
- ES: Reconocido, pero esta versión no lo ejecuta: {lista}. Las acciones soportadas de la misma orden siguen por
  separado.
- Fuente: APP:11389.
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### 4.7 El límite de 120 minutos

**X1-C30 · Un fluido o una transfusión que pasarían en más de 120 min** — 3 frases
- EN: (a) {v} mL at {r} mL/h would run for {h} h; this simulator runs a fluid order over at most 120 min. Restate it
  as a bolus or a shorter infusion. · (b) {v} mL over {h} h: this simulator runs a fluid order over at most 120 min.
  Restate it as a bolus or a shorter infusion. · (c) {u} units over {h} h in all: this simulator runs a transfusion
  over at most 120 min. Restate it with a shorter time, or transfuse fewer units now.
- ES: (a) {v} mL a {r} mL/h pasarían en {h} h; este simulador pasa una orden de fluido en 120 min como máximo.
  Escríbela como un bolo o como una infusión más corta. · (b) {v} mL en {h} h: este simulador pasa una orden de
  fluido en 120 min como máximo. Escríbela como un bolo o como una infusión más corta. · (c) {u} unidades en {h} h
  en total: este simulador pasa una transfusión en 120 min como máximo. Escríbela con un tiempo más corto, o
  transfunde menos unidades ahora.
- Fuentes: FE:861 (a), FE:868 (b), FE:876 (c).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### 4.8 La nitroglicerina o un vasopresor escritos en otra forma

**X1-C31 · Una forma que este encuentro no da** — 2 frases
- EN: (a) {fármaco} was understood as a/an {forma}{ of {dosis}}. This encounter gives nitroglycerin as a continuous IV
  infusion or an IV bolus, so nothing was converted or executed. To give it, state an infusion rate in {unidad} or
  an IV bolus in mcg, or say cancel. · (b) This encounter gives {fármaco} only as a continuous IV infusion, so
  nothing was converted or executed. To give it, state an infusion rate in {unidad}, or say cancel.
- ES: (a) {fármaco} se entendió como {forma}{ de {dosis}}. Este encuentro da la nitroglicerina como infusión IV
  continua o como bolo IV, así que no se convirtió ni se ejecutó nada. Para darla, indica una velocidad de infusión
  en {unidad} o un bolo IV en mcg, o di cancelar. · (b) Este encuentro da {fármaco} sólo como infusión IV continua,
  así que no se convirtió ni se ejecutó nada. Para darla, indica una velocidad de infusión en {unidad}, o di
  cancelar.
- {forma}: V-6. {unidad}: «mcg/min» o «mcg/kg/min o mcg/min». Fuente: FP:3501 (las dos ramas).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

### 4.9 Órdenes pendientes

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| X1-C32 | APP:11175 | There are no pending orders to cancel. | No hay órdenes pendientes que cancelar. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| X1-C33 | APP:8455 | Pending orders cancelled before execution. No treatment administered; simulation time unchanged. | Órdenes pendientes canceladas antes de ejecutarse. No se administró ningún tratamiento; el tiempo simulado no cambió. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

### 4.10 Vocabularios para los valores

Cada tabla se aprueba entera. Decisión docente (V-1 a V-7): ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

**V-1 · Clases y fármacos que nombra el motor** ({fármaco}, {clase}; X1-C01 a X1-C04). Cuando el residente nombró
un fármaco, el motor usa ese nombre (K-13). Cuando sólo hay una clase, el inglés de hoy muestra la clave interna
(«beta_blocker»).

| Clave | ES | Clave | ES |
|---|---|---|---|
| antibiotics | antibiótico | diuretic | diurético |
| bronchodilator | broncodilatador | beta_blocker | betabloqueador |
| steroid | corticoide | diltiazem | diltiazem |
| dextrose | glucosa | amiodarone | amiodarona |
| naloxone | naloxona | procedural_sedation | sedación para el procedimiento |
| atropine | atropina | magnesium | magnesio |
| opioid | opioide | thrombolysis | trombolítico |
| antipyretic | antipirético | octreotide | octreotida |
| ppi | inhibidor de la bomba de protones | glucagon | glucagón |
| aspirin | aspirina | calcium | calcio |
| anticoagulation | anticoagulante | thiamine | tiamina |
| norepinephrine | noradrenalina | dobutamine | dobutamina |
| epinephrine | adrenalina | nitroglycerin | nitroglicerina |

**V-2 · Unidades escritas** (X1-C01 a): grams → gramos · milligrams → miligramos · micrograms → microgramos.

**V-3 · Elementos de una lista** (X1-C05):

| Orden | EN | ES |
|---|---|---|
| Ventilador | mode · FiO₂ as a percentage · PEEP in cm H₂O | el modo del ventilador · la FiO₂ en porcentaje · la PEEP en cm H₂O (si el modo no falta, «del ventilador» va con el primer elemento: «la FiO₂ del ventilador en porcentaje») |
| Anticoagulación | which anticoagulant · the dose · the dose units · the route | qué anticoagulante · la dosis · las unidades de la dosis · la vía |
| Marcapasos | the pacing rate in beats per minute · the output current in mA | la frecuencia del marcapasos en latidos por minuto · la corriente en mA |

**V-4 · Regiones del examen** (X1-C15 y el modo de examen, L-11):

| EN | ES | EN | ES |
|---|---|---|---|
| General appearance | Aspecto general | Abdomen | Abdomen |
| Breathing | Respiración | Neurological | Neurológico |
| Peripheral perfusion | Perfusión periférica | Extremities | Extremidades |
| Respiratory | Pulmonar | Vascular access | Accesos vasculares |
| Cardiac | Cardíaco | | |

«Breathing» (frecuencia y trabajo respiratorio) y «Respiratory» (auscultación) son regiones distintas del motor;
«Respiración» y «Pulmonar» las separan en español.

**V-5 · Estado de conciencia** (X1-C24): Drowsy → somnoliento · Obtunded → obnubilado · Unresponsive → sin
respuesta. Son las formas que ya usa la sala, en minúscula.

**V-6 · Formas de una dosis única** (X1-C31): sublingual dose → una dosis sublingual · bolus → un bolo · IV push →
un bolo IV directo · spray dose → una dosis en spray · tablet → un comprimido · single dose → una dosis única.

**V-7 · Ejemplos de oxígeno** (X1-C18; `family_parser.py:1949`): naricera 4 L/min, mascarilla simple 8 L/min o
mascarilla con reservorio 15 L/min.

**V-8 · Resumen de la orden retenida** — sólo si I-10 no se aprueba (`app.py:8204–8276`): start → iniciar ·
adjust → ajustar · continue → continuar · stop → suspender · crystalloid → cristaloide · unit(s) → unidad(es) ·
oxygen → oxígeno · synchronized cardioversion → cardioversión sincronizada · the running infusion at → la infusión en
curso a · prepare for intubation → preparar la intubación · intubation with invasive ventilation → intubación con
ventilación invasiva · ventilator adjustment → ajuste del ventilador · ventilator continuation → mantener el
ventilador · discharge home → alta a domicilio · admission to {destino} → hospitalización en {destino} · management
intervention → intervención de manejo · NIV → VMNI. Cualquier otro tipo de acción, con su etiqueta del registro.

## 5. Compuerta de razonamiento y explicación retrospectiva (16)

El bloque «ORDEN RETENIDA — FALTA EL RAZONAMIENTO» ya tiene en español su título, «Entendí: …», «La orden no se
ejecutó…» y «No necesitas repetir la orden.». Lo que sigue es lo que todavía sale en inglés.

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| G-01 | APP:8311 | I recognised {lista}. | Reconocí {lista}. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-02 | APP:8313 | Still to state: {lista}. | Todavía falta: {lista}. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-03 | `reasoning_questions.py:32–39` | {lista}, de: what you think is going on · what you want to do · what you expect to happen · what you will check · which problem you are addressing first · when you will check it | qué crees que está pasando · qué quieres hacer · qué esperas que ocurra · qué vas a revisar · qué problema estás abordando primero · cuándo lo vas a revisar (unidas con «, » y « y ») | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-04 | APP:8316 | In your own words, or in the fields on screen: | Con tus palabras o en los campos de la pantalla: | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-05 | APP:8328 | What you already wrote is kept. | Lo que ya escribiste se conserva. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-06 | APP:10993 | An understood order is being held. The patient state is unchanged; complete the reasoning in your own words or use the guided fields. | Hay una orden entendida en espera. El estado del paciente no ha cambiado; completa el razonamiento con tus palabras o con los campos guiados. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-07 | APP:10996 | **Held order:** {resumen} | **Orden retenida:** {resumen} | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-08 | APP:11098 | Or answer naturally below. You only need to add what is missing; you do not need to repeat the held order. | O responde con tus palabras abajo. Basta con agregar lo que falta; no necesitas repetir la orden retenida. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-09 | APP:11054 | e.g. HR and rhythm, BP/MAP, capillary refill, mental status | p. ej., FC y ritmo, PA/PAM, llene capilar, estado mental | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-10 | APP:11073 | Complete reasoning & execute held order | Completar el razonamiento y ejecutar la orden retenida | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-11 | APP:11154 | Cancel pending orders | Cancelar las órdenes pendientes | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-12 | APP:8573 | Complete the requested reasoning to continue. | Completa el razonamiento pedido para continuar. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-13 | APP:7701 | When will you check it? | ¿Cuándo lo vas a revisar? | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-14 | APP:11108 | Explain an urgent decision afterwards (optional, recorded as retrospective) | Explicar después una decisión urgente (opcional; queda registrada como retrospectiva) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-15 | APP:11109 | The intervention already ran. What you write here is recorded as written now, after the decision, and never as reasoning shown when it was taken. | La intervención ya se ejecutó. Lo que escribas aquí queda registrado como escrito ahora, después de la decisión, y nunca como un razonamiento expresado cuando se tomó. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| G-16 | APP:11117 | Save retrospective explanation | Guardar la explicación retrospectiva | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

G-12 sólo aparece si un residente escribe la frase de anulación del facilitador. G-14 a G-16 son el formulario de
la explicación retrospectiva; sus preguntas son I-7 y G-13. La sonda de la 27m los vio en inglés.

## 6. Rótulos de la sala (20)

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| L-01 | APP:10884 | Talk · Examine · Tests · Treat (los cuatro modos) | Conversar · Examinar · Exámenes · Tratar | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-02 | APP:11135 | Enter your clinical reasoning and/or actions (rótulo oculto, lo lee un lector de pantalla) | Tu razonamiento clínico y tus acciones | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-03 | APP:11139 | Describe your reasoning naturally. For example: I think...; I am addressing... first; I expect...; reassess ... in ... minutes. | Describe tu razonamiento con naturalidad. Por ejemplo: Creo que…; Primero abordo…; Espero que…; Reevalúo … en … minutos. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-04 | APP:10906 | Ask the patient · Ask the available history source | Pregúntale al paciente · Pregunta a la fuente de la historia disponible | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-05 | APP:10906 | What brought you in today? (ejemplo dentro del campo) | ¿Por qué consulta hoy? | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-06 | APP:10907 | Ask | Preguntar | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-07 | APP:10916 · APP:10918 · APP:10919 | History topics · Explore · Ask about this topic | Temas de la historia · Explorar · Preguntar por este tema | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-08 | APP:10918 | Presenting symptoms and onset (tema de reserva, si el caso no tiene los suyos) | Motivo de consulta e inicio (los otros dos de reserva ya tienen español: «Síntomas asociados», «Antecedentes») | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-09 | APP:10900 · APP:10669 | History source: {fuente} | Fuente de la historia: {fuente} ({fuente} es relato) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-10 | APP:10895 · APP:10902 | The patient cannot provide a history at present. Review the history already obtained in the clinical chart. · The patient cannot answer at present. Questions are directed to the available collateral source. | El paciente no puede dar su historia por ahora. Revisa la historia ya obtenida en la ficha clínica. · El paciente no puede responder por ahora. Las preguntas se dirigen a la fuente colateral disponible. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-11 | APP:10943 · APP:10944 · APP:10960 | Examine (selector) · Examine patient · Examine: {región} (la entrada «TÚ» del examen) | Examinar · Examinar al paciente · Examen: {región} — {región}: V-4 | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-12 | APP:11624 | Complete Encounter & Begin Review | Terminar el encuentro y comenzar la revisión | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-13 | APP:11665 · APP:11667 | Save & return to dashboard · End this attempt without completing review (en el menú) | Guardar y volver al inicio · Terminar este intento sin completar la revisión | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-14 | APP:10690 | Current treatments | Tratamientos en curso | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-15 | APP:10489 | Diagnostics | Resultados de exámenes | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-16 | APP:10689 · APP:10709 | Current support · {soporte} | Soporte actual · {soporte} — {soporte}: M-04 | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-17 | APP:10118 · APP:10753 | ORDER_CANCELLED (clave cruda como encabezado de la entrada) | ORDEN CANCELADA | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-18 | APP:10118 · `resuscitation_room.py:141` | DIAGNOSTIC (clave cruda; la entrada del ECG tomado) | ECG | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-19 | APP:10183 · APP:11681 | Management Reasoning Simulator · Clinical encounter v{n} | Management Reasoning Simulator · Encuentro clínico v{n} | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| L-20 | `account_portal.py:391` (barra lateral) | Resident (el rol de la cuenta) | Residente | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

- L-01: la guía del residente nombra hoy los modos en inglés («Talk, Examine, Tests, Treat»); se actualiza al
  implementar.
- L-17 y L-18 también salen crudos en inglés. Un rótulo inglés («ORDER CANCELLED», «ECG») es opcional y va aparte
  (§10).

## 7. Monitor, escena, ECG y tratamientos en curso (22)

### 7.1 Monitor y escena

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| M-01 | `resuscitation_room.py:55–65` | BEDSIDE MONITOR · HR · NIBP · RR (SpO₂ igual) | MONITOR DE CABECERA · FC · PANI · FR | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| M-02 | `clinical_scene.py:227–243` | ED / Bed 03 · {Patient illustration · current state / Updating patient appearance / Current patient image unavailable} | Urgencias / Cama 03 · {Imagen del paciente · estado actual / Actualizando la apariencia del paciente / Imagen actual del paciente no disponible} | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| M-03 | `clinical_scene.py:282–302` | Por qué no hay foto: 11 avisos, todos terminados en «The monitor and the examination are current.» | Ver la tabla de abajo; el final común: «El monitor y el examen están al día.» | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| M-04 | `resuscitation_room.py:6–19` | Soporte en curso: Ventilator · {modo} · FiO₂ {n}% · PEEP {n} · {NIV} · FiO₂ {n}% · {dispositivo / Oxygen} · {n} L/min · Norepinephrine / Dobutamine / Nitroglycerin · {n} {unidad} | Ventilador · {modo} · FiO₂ {n}% · PEEP {n} · VMNI · FiO₂ {n}% · {dispositivo / Oxígeno} · {n} L/min · Noradrenalina / Dobutamina / Nitroglicerina · {n} {unidad}. «Bag-mask ventilation» ya tiene su español («Ventilación con bolsa-mascarilla») | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

**M-03 · Avisos de «sin foto»** (`clinical_scene.py:282–302`; el de `NO_ACCOUNTS` queda fuera: el piloto corre
con cuentas).

| Código | EN (antes del final común) | ES (antes del final común) |
|---|---|---|
| NOT_ALLOWED | No photograph is prepared for this encounter. | No hay una fotografía preparada para este encuentro. |
| CONFIG | Patient image generation is not configured. | La generación de imágenes del paciente no está configurada. |
| UNSUPPORTED | No synthetic patient in the image bank fits this case. | Ningún paciente sintético del banco de imágenes corresponde a este caso. |
| CONTRACT | This appearance has no supported photograph. | Esta apariencia no tiene una fotografía disponible. |
| UNRENDERABLE | The image generator could not draw this appearance reliably, so no photograph is requested. | El generador de imágenes no pudo dibujar esta apariencia de forma confiable, así que no se pide una fotografía. |
| REVIEW_PENDING | The photograph of this appearance is awaiting faculty review. | La fotografía de esta apariencia espera la revisión docente. |
| PRICE | The configured image model has no verified price, so no photograph is requested. | El modelo de imágenes configurado no tiene un precio verificado, así que no se pide una fotografía. |
| BUDGET_DOLLARS · BUDGET_REQUESTS | The image budget of this environment is used up; saved photographs are still shown. | El presupuesto de imágenes de este entorno se agotó; las fotografías guardadas se siguen mostrando. |
| BUDGET_CONFIG | The image budget is not configured correctly. | El presupuesto de imágenes no está bien configurado. |
| INTERNAL | The saved photograph could not be read. | No se pudo leer la fotografía guardada. |

Las sondas vieron NOT_ALLOWED (61m) y UNRENDERABLE (27m).

### 7.2 ECG

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| E-01 | `resuscitation_room.py:134` | (ayuda del botón «ECG») Acquire a 12-lead ECG at the current simulation time. | Tomar un ECG de 12 derivaciones en el tiempo simulado actual. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| E-02 | `resuscitation_room.py:142` | 12-lead ECG acquired. Available in ECG recordings. | ECG de 12 derivaciones tomado. Está en «Registros de ECG». | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| E-03 | `resuscitation_room.py:153–157` | ECG recordings · Acquisition · View recording | Registros de ECG · Registro · Ver el registro | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| E-04 | `resuscitation_room.py:114–121` | ECG · 12 leads · Synthetic educational tracing · Clinical pattern validation pending. · Download ECG | ECG · 12 derivaciones · Trazado educativo sintético · Validación clínica del patrón pendiente. · Descargar el ECG | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| E-05 | `resuscitation_room.py:139` · `ecg12.py:44–283, 313–314` | Cuando no hay trazado: ECG unavailable for this electrical state. · ECG unavailable · Recording unavailable. · y los motivos del modelo (This electrical rhythm has no waveform model yet. · Heart rate is outside this waveform model's range (20–300/min). · Invalid heart rate. · This ECG morphology profile has not been implemented. · This morphology/rhythm combination has not been implemented. · Electrical morphology for PEA has not been specified. · This recording requires its original waveform model version. · Invalid {nombre}.) | No se puede tomar un ECG en este estado eléctrico. · ECG no disponible · Registro no disponible. · Este ritmo eléctrico todavía no tiene un modelo de trazado. · La frecuencia cardíaca está fuera del rango de este modelo de trazado (20–300/min). · Frecuencia cardíaca no válida. · Este perfil de morfología del ECG no está implementado. · Esta combinación de morfología y ritmo no está implementada. · La morfología eléctrica de la AESP no está especificada. · Este registro requiere la versión original de su modelo de trazado. · {nombre} no válido. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

La línea del ECG en «Resultados» ya está en español («Trazado de 12 derivaciones disponible en los registros de
ECG.»). E-02 y E-03 usan el mismo nombre: «Registros de ECG».

### 7.3 Tratamientos en curso («Tratamientos en curso», en «Indicaciones»)

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| T-01 | APP:10404 | Bag-mask assisted ventilation | Ventilación asistida con bolsa-mascarilla | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-02 | APP:10405 | Cumulative crystalloid: {n} mL | Cristaloide acumulado: {n} mL | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-03 | APP:10411 | Fluid order: {a} mL over {d} min; delivered {n} mL. | Orden de fluido: {a} mL en {d} min; pasados {n} mL. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-04 | APP:10414 | Crystalloid pending: {n} mL. Delivery continues as simulation time advances. | Cristaloide pendiente: {n} mL. Sigue pasando a medida que avanza el tiempo simulado. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-05 | APP:10418–10424 | Metoprolol / Propranolol / Diltiazem / Amiodarone: {n} mg total | Metoprolol / Propranolol / Diltiazem / Amiodarona: {n} mg en total | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-06 | APP:10426–10434 | Procedural sedation administered: Etomidate {n} mg total + Midazolam {n} mg total | Sedación para el procedimiento administrada: etomidato {n} mg en total + midazolam {n} mg en total | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-07 | APP:10436–10456 | Norepinephrine: {n} {unidad} · Dobutamine: {n} mcg/kg/min · Oxygen: {dispositivo} at {n} L/min · Nitroglycerin: {n} mcg/min | Noradrenalina: {n} {unidad} · Dobutamina: {n} mcg/kg/min · Oxígeno: {dispositivo} a {n} L/min · Nitroglicerina: {n} mcg/min | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-08 | `clinical_physiology.py:1596–1599` | — started {hh:mm} · last adjusted {hh:mm} | — iniciado {hh:mm} · último ajuste {hh:mm} | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-09 | APP:10472 | Airway equipment and team prepared for intubation | Equipo y personal preparados para la intubación | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-10 | APP:10481 | Disposition: {destino} | Destino: {destino} | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-11 | `family_reports.py:94–106` | {fármaco} {dosis} {unidad} {vía} · minute {t} · over {d} min · {a} of {o} {unidad} given so far (por omisión, «Medication») | {fármaco} {dosis} {unidad} {vía} · minuto {t} · en {d} min · {a} de {o} {unidad} dados hasta ahora (por omisión, «Medicamento») | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-12 | `family_reports.py:110–117` | Packed red cells: {d} of {t} units given so far · Packed red cells given: {n} unit(s) | Glóbulos rojos: {d} de {t} unidades transfundidas hasta ahora · Glóbulos rojos transfundidos: {n} unidad(es) | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| T-13 | APP:10447 | Furosemide administered: {n} mg total | Furosemida administrada: {n} mg en total | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

Las sondas vieron T-02, T-07 (oxígeno y nitroglicerina) y T-11 («aspirin 300 mg PO · minute 7»). Las líneas de
CPAP y BiPAP son siglas y valores. «Invasive ventilation: …» ya tiene su español; sólo falta aplicarlo (I-11).

## 8. Después del cierre (7)

| ID | Fuente | EN | ES propuesto | Decisión docente |
|---|---|---|---|---|
| P-01 | APP:10294 | Return to dashboard | Volver al inicio | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-02 | APP:10277 | **Expert comparison · faculty-validation draft** | **Comparación con el experto · borrador pendiente de validación docente** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-03 | APP:10332 | ### Attempt {n} · Carry-Forward Learning Goal | ### Intento {n} · Objetivo de aprendizaje del intento anterior | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-04 | APP:10334 | This prospective plan came from the previous attempt. Use it as an intention for action and reassessment; the new Management Trace records only what you actually do now. | Este plan prospectivo viene del intento anterior. Úsalo como una intención de acción y de reevaluación; el nuevo Management Trace registra sólo lo que haces ahora. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-05 | APP:10361 | **Previous attempt record · Attempt {n}** | **Registro del intento anterior · Intento {n}** | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-06 | APP:10362 | The completed prior trajectory remains separate and available for download. | La trayectoria anterior completa se mantiene aparte y disponible para descargar. | ☐ APPROVE · ☐ REVISE · ☐ DEFER |
| P-07 | APP:10365 · APP:10374 · APP:10383 | Previous PDF · Previous Markdown · Previous JSON | PDF anterior · Markdown anterior · JSON anterior | ☐ APPROVE · ☐ REVISE · ☐ DEFER |

P-03 a P-07 se ven en un intento repetido con el plan de adaptación del anterior (el botón «Siguiente encuentro con
este Plan de adaptación», ya en español). El resto de la pantalla de revisión ya está en español.

## 9. A-2 · Examen respiratorio con el paciente agotado (EN y ES)

**Qué cambia.** Hoy, en `pulmonary_edema_75f` sin tratamiento, la región «Respiratory» dice «Bilateral inspiratory
crackles with increased respiratory effort.» también durante los 12–13 minutos en que el trabajo respiratorio ya es
«Exhausted: shallow and ineffective effort» (TD-51; `family_engine.py:3237`). La decisión docente A-2 pide un
examen coherente con el estado.

**Cuándo se muestra.** En el edema pulmonar, con la congestión sin mejorar (la rama de `f["lung"] >= 0.7`) y el
paciente agotado según el mismo criterio del motor que pone «Exhausted» en el trabajo respiratorio de la respuesta
del paciente y del examen (`work_of_breathing.exhausted`: 25 minutos seguidos con carga alta y sin soporte). En
los demás estados, las frases de A-2 y A-3 siguen igual.

- **EN propuesto:** Bilateral inspiratory crackles; the respiratory effort is now exhausted: shallow and
  ineffective.
- **ES propuesto:** Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ya está agotado: es superficial e
  ineficaz.
- **Se infiere:** el paciente dejó de compensar; un esfuerzo menor no es mejoría. Coincide con el trabajo
  respiratorio que muestran la respuesta del paciente y el examen («Agotado: esfuerzo superficial e ineficaz»).
- **Alternativa:** «Bilateral inspiratory crackles.» / «Crépitos inspiratorios bilaterales.», sin hablar del
  esfuerzo, que ya dicen la frecuencia respiratoria y el examen general. Es más corta, pero quien lee sólo la
  auscultación no ve el agotamiento.
- **Recomendación:** la propuesta. Una prueba del motor fija hoy que A-3 («reduced respiratory effort») nunca aparece
  junto al agotamiento; al implementar, otra prueba debe fijar que en el agotamiento se lee esta frase y nunca
  «increased».
- **SHA:** cambio de código del motor y de su español (nuevo SHA; 16.4).
- Decisión docente: ☐ APPROVE · ☐ REVISE · ☐ DEFER — Nota: ________

## 10. Al implementar (no autorizado todavía)

- Cada formulación aprobada pasa a su regla en `language.py`, `report_language.py` o `screen_language.py`, con su
  prueba. Los textos de los motores no cambian en inglés salvo A-2 (y A-9).
- **Centinela del español:** recorrer los 30 casos del piloto en español con una batería de órdenes que dispare cada
  pregunta de este documento, y fallar ante cualquier línea visible con palabras inglesas fuera de los nombres
  canónicos y los códigos. Las 7 sondas de este inventario son el punto de partida. Es la prueba de que no queda
  nada fuera de este inventario, que no se puede asegurar sólo leyendo el código.
- Guías: la del residente dice que estas preguntas, el aviso de la orden retenida y algunos rótulos se ven en
  inglés, y nombra los modos en inglés. La docente cita TD-51 como diferida (línea 232). Se actualizan con la
  implementación.
- El cambio es de código: nuevo SHA y el contrato 16.4 (suite, 56 regresiones, B-1).
- **Opcional, en inglés (aparte de X-1):** cuatro textos ingleses muestran claves internas: la clase en X1-C01 a
  C04, la acción en X1-C27 (e), el estudio en X1-C28, y los encabezados L-17 y L-18. Corregirlos en inglés es una
  decisión aparte.

## 11. Resumen de decisiones

| Grupo | Formulaciones | Decisiones |
|---|---|---|
| X1-0 · Convenciones | — | 1 |
| I-10 · Resumen de la orden retenida (diseño) | — | 1 |
| 4 · Preguntas sobre una orden (X1-C01 a C33, X1-R01) | 34 plantillas (73 frases) | 34 |
| 4.10 · Vocabularios (V-1 a V-7; V-8 sólo si I-10 no se aprueba) | 7 tablas | 1 |
| 5 · Compuerta y explicación retrospectiva (G-01 a G-16) | 16 | 16 |
| 6 · Rótulos de la sala (L-01 a L-20) | 20 | 20 |
| 7 · Monitor, escena, ECG y tratamientos (M-01 a M-04, E-01 a E-05, T-01 a T-13) | 22 | 22 |
| 8 · Después del cierre (P-01 a P-07) | 7 | 7 |
| 9 · A-2 en agotamiento (EN y ES) | 1 | 1 |
| **Total** | **100 formulaciones, 7 vocabularios** | **103** |

Firma docente y fecha: ________________________

## Anexo A · Las 40 preguntas del motor heredado, fuera del alcance

Ningún caso del piloto las alcanza (§1, punto 2). Quedan en inglés; si un caso del banco dejara el motor por
familias, habría que traducirlas.

- `app.py`, `try_resolve_pending_action` (tipos pendientes heredados): 5459, 5491, 5497, 5534, 5553, 5568, 5573,
  5593, 5620, 5634, 5636, 5654, 5689, 5692, 5697, 5699.
- `app.py`, `execute_bundle` después de la rama por familias: 9245, 9257, 9270, 9280, 9284, 9294, 9298, 9304, 9308,
  9314, 9318, 9323, 9328, 9344, 9353, 9361, 9367, 9369, 9375, 9379, 9384, 9389, 9398, 9404.
