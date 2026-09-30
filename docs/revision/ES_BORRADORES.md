# R-4 · Borradores en español: frases del motor y C14

Generado por `tools_review_sheets.py` desde `spanish_drafts.py`. **No se edita a mano** y **no aprueba
nada**: ningún borrador se muestra a un residente ni a un docente hasta que usted lo apruebe, y activarlo
después es un cambio aparte, registrado y con pruebas (`test_spanish_drafts.py`). La columna «Borrador» es
una propuesta para que usted la confirme o la cambie.

**Frases del motor (resto de DF-23 fila 11):** 18 · **Textos de C14 (TD-07):** 68 en 31 casos

## 1 · Frases del motor que hoy se leen en inglés

Encontradas jugando la sala sin proveedor el 2026-09-29: los 20 guiones del ensayo y una sonda de los 11
casos que no cubren (`tools_engine_spanish.py`), 31 corridas y 583 entradas. 10 plantillas se leen con
inglés: 4 son frases del motor; 4 son el POCUS del relato de un caso, que antes de su aprobación se lee
mezclado palabra por palabra (TD-46), y 2 son el examen neurológico que cita el relato del caso, que se
traduce al aprobarlo. La tabla suma las frases que el motor compone para el panel de examen y que la cosecha
no alcanzó. El relato de cada caso tiene su propia aprobación, caso por caso, en el tablero docente. Los
números se escriben `{n}`.

| # | Dónde | Texto del motor | Cómo se lee hoy en español | Borrador | Nota |
|---|---|---|---|---|---|
| 1 | entrada de la sala · trauma_limb_hemorrhage_27m, trauma_hemothorax_41m (visto al jugar) | Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume replaces a source that is still open. | Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume replaces a source that is still open. | Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido; la reposición de volumen no sustituye el control del sangrado activo. | trauma_hemorrhage.ARREST_TEXT; también como procedimiento |
| 2 | panel de examen · pulmonary_edema_75f (visto al jugar) | Bilateral inspiratory crackles with increased respiratory effort. | Bilateral inspiratory crackles with increased respiratory effort. | Crépitos inspiratorios bilaterales, con aumento del esfuerzo respiratorio. | family_engine.current_findings, edema pulmonar |
| 3 | panel de examen · pulmonary_edema (encontrado en el código) | Bilateral crackles remain, with reduced respiratory effort. | Bilateral crackles remain, with reduced respiratory effort. | Persisten crépitos bilaterales, con menor esfuerzo respiratorio. | family_engine.current_findings, edema pulmonar |
| 4 | panel de examen · transfusión en cualquier familia (encontrado en el código) | New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze. | New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze. | Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin sibilancias. | family_engine.current_findings, sobrecarga por transfusión |
| 5 | panel de examen · asthma (encontrado en el código) | Improved air entry with residual expiratory wheeze. | Improved air entry with residual expiratory wheeze. | Mejor entrada de aire, con sibilancias espiratorias residuales. | family_engine.current_findings, asma |
| 6 | panel de examen · asthma (encontrado en el código) | Reduced bilateral air entry with prolonged expiration and wheeze. | Reduced bilateral air entry with prolonged expiration and wheeze. | Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias. | family_engine.current_findings, asma |
| 7 | panel de examen · asthma (encontrado en el código) | Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side. | Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side. | Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado. | neumotórax del asma; igual con «left» → «izquierdo» |
| 8 | panel de examen · asthma (encontrado en el código) | Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze. | Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze. | Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de aire, con sibilancias espiratorias residuales. | neumotórax descomprimido; «left» → «izquierdo», y la segunda parte es cualquiera de las dos del asma |
| 9 | panel de examen · opioid (encontrado en el código) | Respiratory rate {n} /min; assisted ventilation is in progress. | Respiratory rate {n} /min; assisted ventilation is in progress. | Frecuencia respiratoria {n}/min, dada por la ventilación asistida en curso. | family_engine.current_findings, opioides |
| 10 | panel de examen · opioid (encontrado en el código) | Respiratory rate {n} /min; breaths remain shallow. | Respiratory rate {n} /min; breaths remain shallow. | Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales. | family_engine.current_findings, opioides |
| 11 | panel de examen · opioid (encontrado en el código) | Respiratory rate {n} /min; spontaneous breaths have greater depth. | Respiratory rate {n} /min; spontaneous breaths have greater depth. | Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas. | family_engine.current_findings, opioides |
| 12 | panel de examen · hypoglycemia_54m_thiamine (visto al jugar) | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría. | vía fallida antes de usarla; el español ya está en language, no en el panel |
| 13 | panel de examen · hypoglycemia (encontrado en el código) | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación. | vía que funciona; el español ya está en language, no en el panel |
| 14 | panel de examen · hypoglycemia (encontrado en el código) | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y doloroso a la palpación. | vía fallida ya usada; el español ya está en language, no en el panel |
| 15 | panel de examen · hypoglycemia (encontrado en el código) | A second peripheral cannula in the right forearm; the site is clean. | A second peripheral cannula in the right forearm; the site is clean. | Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio. | vía nueva; el español ya está en language, no en el panel |
| 16 | panel de examen · hypoglycemia (encontrado en el código) | An intraosseous needle in place (humeral). | An intraosseous needle in place (humeral). | Una aguja intraósea instalada (humeral). | también tibial, esternal o femoral; el español ya está en language, no en el panel |
| 17 | panel de examen · hypoglycemia (encontrado en el código) | An intraosseous needle in place; no site was recorded. | An intraosseous needle in place; no site was recorded. | Una aguja intraósea instalada; no se registró el sitio. | el español ya está en language, no en el panel |
| 18 | panel de examen · hypoglycemia (encontrado en el código) | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | Suero glucosado al {n} % a {n} mL/h por la cánula del antebrazo izquierdo. | también por la cánula nueva del antebrazo derecho o por la aguja intraósea; el español ya está en language, no en el panel |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

## 2 · C14: razón, componente y evidencia esperada (TD-07)

Lo que el portal docente en español muestra hoy en inglés al registrar una observación de C14. Los de
TD1, F1, C1, C3 y C4 no están aquí: son la decisión P-12 del paquete.

### `acs_48m_wellens`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The right decision -- angiography and no provocation test -- does not depend on POCUS, and a normal resting POCUS cannot reasonably guide it. Not being reassured by it is diagnostic reasoning, not C14 (decision B). | La decisión correcta —coronariografía y ninguna prueba de provocación— no depende del POCUS, y un POCUS normal en reposo no puede guiarla razonablemente. No tranquilizarse por él es razonamiento diagnóstico, no C14 (decisión B). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `acs_52m_de_winter`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Evidencia esperada | activates or expedites reperfusion | activa o acelera la reperfusión |
| Por qué sí | Akinesis of the anterior wall and apex supports treating the de Winter pattern as an anterior occlusion (decision A); in the engine the wall motion evolves with the ischaemic minutes. | La acinesia de la pared anterior y del ápex apoya tratar el patrón de de Winter como una oclusión anterior (decisión A); en el motor, la motilidad evoluciona con los minutos de isquemia. |
| Componente observable | Using regional wall motion to prioritise the reperfusion decision. | Usar la motilidad regional para priorizar la decisión de reperfusión. |
| Evidencia esperada | requests POCUS and names the anterior akinesis | solicita POCUS y nombra la acinesia anterior |
| Evidencia esperada | relates it to the ECG pattern as an occlusion | la relaciona con el patrón del ECG como una oclusión |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `acs_54m_inferior`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The encounter does not create a meaningful opportunity to observe POCUS-guided management: recognising right ventricular involvement through the available POCUS is not an expectation the ACEP 2016 emergency ultrasound guideline used here establishes (pp. 25, 29), and the nitrate, antiplatelet and cautious-volume decisions are driven mainly by the ECG, the right-sided leads (V4R) and the haemodynamic context rather than by the POCUS finding. | El encuentro no crea una oportunidad significativa de observar un manejo guiado por POCUS: reconocer el compromiso del ventrículo derecho con el POCUS disponible no es una expectativa que establezca la guía de ecografía de urgencia ACEP 2016 usada aquí (pp. 25, 29), y las decisiones sobre el nitrato, el antiplaquetario y el volumen cauteloso dependen sobre todo del ECG, de las derivaciones derechas (V4R) y del contexto hemodinámico, no del hallazgo del POCUS. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `acs_61m_posterior`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | ST depression in V1-V3 with a regional wall-motion abnormality reported on POCUS (posterior hypokinesis): with the ECG and the posterior leads, the reported wall motion can support prioritising reperfusion for an occlusion the 12-lead understates (decision A); in the engine the wall motion evolves with the ischaemic minutes. Two limits: an isolated regional wall-motion abnormality is subtle, and the written report states it rather than the resident recognising it, so recognising it is not required; and a non-dilated aortic root and descending aorta on POCUS do not exclude an aortic dissection. | Infradesnivel del ST en V1-V3 con una alteración de la motilidad regional informada en el POCUS (hipocinesia posterior): junto con el ECG y las derivaciones posteriores, la motilidad informada puede apoyar la prioridad de la reperfusión de una oclusión que el ECG de 12 derivaciones subestima (decisión A); en el motor, la motilidad evoluciona con los minutos de isquemia. Dos límites: una alteración aislada de la motilidad regional es sutil, y el informe escrito la entrega en lugar de que el residente la reconozca, así que reconocerla no se exige; y una raíz aórtica y una aorta descendente no dilatadas en el POCUS no descartan una disección aórtica. |
| Componente observable | Using the reported regional wall motion, with the ECG and the posterior leads, to prioritise the reperfusion decision. | Usar la motilidad regional informada, junto con el ECG y las derivaciones posteriores, para priorizar la decisión de reperfusión. |
| Evidencia esperada | requests POCUS and relates the reported wall motion to the ECG | solicita POCUS y relaciona la motilidad informada con el ECG |
| Evidencia esperada | uses it with the ECG and the posterior leads to treat the pattern as an occlusion | la usa junto con el ECG y las derivaciones posteriores para tratar el patrón como una oclusión |
| Evidencia esperada | activates or expedites reperfusion | activa o acelera la reperfusión |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `acs_66f_nonst`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The acute coronary syndrome is already established by the ECG and a troponin of 180 ng/L; the mild inferolateral hypokinesis does not change the pathway, with no occlusion and an angiography that can wait (decision A). | El síndrome coronario agudo ya está establecido por el ECG y una troponina de 180 ng/L; la hipocinesia inferolateral leve no cambia la ruta, sin oclusión y con una coronariografía que puede esperar (decisión A). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `acs_70f_left_main`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Borderline pressure with incipient hypoperfusion (104/66, cool extremities, capillary refill 3 s) and intermediate POCUS findings: globally mildly reduced contraction, scattered basal B-lines and an IVC of 1.9 cm with about 50% collapse. No single answer follows from them: withholding volume, a small bolus with its limit stated and reassessed, or early support can each be justified, and the engine answers large volumes poorly in this profile. C14 observes whether the volume, support and urgency decisions are made with the global LV function in view and adapted to the response. | Presión limítrofe con hipoperfusión incipiente (104/66, extremidades frías, llene capilar de 3 s) y hallazgos intermedios en el POCUS: contracción global levemente disminuida, líneas B basales dispersas y una VCI de 1,9 cm con cerca de 50 % de colapso. De ellos no se deduce una única respuesta: no dar volumen, un bolo pequeño con su límite declarado y reevaluado, o un soporte precoz pueden justificarse, y en este perfil el motor responde mal a volúmenes grandes. C14 observa si las decisiones de volumen, soporte y urgencia se toman con la función global del VI a la vista y se adaptan a la respuesta. |
| Componente observable | Deciding volume, support and urgency with the global LV function in view, and adapting them to the response. | Decidir el volumen, el soporte y la urgencia con la función global del VI a la vista, y adaptarlos a la respuesta. |
| Evidencia esperada | requests POCUS and relates the global LV function, the B-lines and the IVC to the volume decision | solicita POCUS y relaciona la función global del VI, las líneas B y la VCI con la decisión de volumen |
| Evidencia esperada | withholds volume, or gives a small bolus with its limit stated and reassesses it, or escalates support, and says why | no da volumen, o da un bolo pequeño con su límite declarado y lo reevalúa, o escala el soporte, y dice por qué |
| Evidencia esperada | adapts the plan to the response and relates it to the urgency of reperfusion | adapta el plan a la respuesta y lo relaciona con la urgencia de la reperfusión |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `anaphylaxis_29f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Adrenaline and volume are indicated whatever the POCUS shows; the hyperdynamic LV and the collapsing IVC confirm a distributive shock without changing its management (decision C). | La adrenalina y el volumen están indicados muestre lo que muestre el POCUS; el VI hiperdinámico y la VCI que colapsa confirman un shock distributivo sin cambiar su manejo (decisión C). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `anaphylaxis_63m_betablocked`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | In this refractory reaction the case's lever is the medication history and glucagon; volume is given regardless, and the POCUS supports without guiding the decision (decision C). | En esta reacción refractaria, la palanca del caso es la historia de medicamentos y el glucagón; el volumen se da de todos modos, y el POCUS apoya sin guiar la decisión (decisión C). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `asthma_24f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Bronchodilation does not depend on POCUS. A pneumothorax appears only after ventilation with sustained high plateau pressures, and its event already names the diagnosis, so a POCUS would only confirm it (decision D). Redesigning that event is a separate case decision. | La broncodilatación no depende del POCUS. Un neumotórax aparece sólo después de ventilar con presiones meseta altas y sostenidas, y su evento ya nombra el diagnóstico, así que un POCUS sólo lo confirmaría (decisión D). Rediseñar ese evento es otra decisión del caso. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `asthma_49m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Bronchodilation does not depend on POCUS. A pneumothorax appears only after ventilation with sustained high plateau pressures, and its event already names the diagnosis, so a POCUS would only confirm it (decision D). Redesigning that event is a separate case decision. | La broncodilatación no depende del POCUS. Un neumotórax aparece sólo después de ventilar con presiones meseta altas y sostenidas, y su evento ya nombra el diagnóstico, así que un POCUS sólo lo confirmaría (decisión D). Rediseñar ese evento es otra decisión del caso. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `bradycardia_avb3_78f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The decision is pacing, and the pulse and the pressure confirm its capture; the simulator's POCUS does not reflect the capture and would contradict the monitor after pacing (decision E). | La decisión es el marcapaso, y el pulso y la presión confirman su captura; el POCUS del simulador no refleja la captura y contradiría al monitor después de iniciar el marcapaso (decisión E). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `bradycardia_bb_54f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The POCUS is the same in the three toxic or metabolic bradycardias -- globally reduced contraction at a slow rate -- so it does not discriminate the cause, which the case separates by the history, the glucose and the ECG, and the modelled responses do not depend on it (decision E). | El POCUS es el mismo en las tres bradicardias tóxicas o metabólicas —contracción globalmente disminuida a una frecuencia lenta—, así que no distingue la causa, que el caso separa por la historia, la glicemia y el ECG, y las respuestas modeladas no dependen de él (decisión E). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `bradycardia_ccb_68m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The POCUS is the same in the three toxic or metabolic bradycardias -- globally reduced contraction at a slow rate -- so it does not discriminate the cause, which the case separates by the history, the glucose and the ECG, and the modelled responses do not depend on it (decision E). | El POCUS es el mismo en las tres bradicardias tóxicas o metabólicas —contracción globalmente disminuida a una frecuencia lenta—, así que no distingue la causa, que el caso separa por la historia, la glicemia y el ECG, y las respuestas modeladas no dependen de él (decisión E). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `bradycardia_hyperk_63m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Hyperkalaemia is treated with calcium, insulin with glucose and removal; the POCUS does not change that management. | La hiperkalemia se trata con calcio, insulina con glucosa y la eliminación del potasio; el POCUS no cambia ese manejo. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `gi_bleed_57m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Haemorrhagic shock (88/54) with a small hyperdynamic LV and a near-completely collapsing IVC: the volume assessment is a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with volume and blood (decision C). | Shock hemorrágico (88/54) con un VI pequeño e hiperdinámico y una VCI que colapsa casi por completo: la evaluación del volumen es un objetivo de la reanimación junto con la transfusión, y una ecografía repetida muestra la VCI llenándose con volumen y sangre (decisión C). |
| Componente observable | Using the POCUS volume assessment to guide and reassess resuscitation. | Usar la evaluación del volumen por POCUS para guiar y reevaluar la reanimación. |
| Evidencia esperada | requests POCUS and names the empty, hyperdynamic LV and the collapsed IVC | solicita POCUS y nombra el VI vacío e hiperdinámico y la VCI colapsada |
| Evidencia esperada | relates them to transfusion or volume | los relaciona con la transfusión o el volumen |
| Evidencia esperada | reassesses with POCUS after resuscitation | reevalúa con POCUS después de la reanimación |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `gi_bleed_72f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Componente observable | Using the POCUS volume assessment to guide and reassess resuscitation. | Usar la evaluación del volumen por POCUS para guiar y reevaluar la reanimación. |
| Evidencia esperada | relates them to transfusion or volume | los relaciona con la transfusión o el volumen |
| Evidencia esperada | reassesses with POCUS after resuscitation | reevalúa con POCUS después de la reanimación |
| Por qué sí | Hypotension from bleeding (98/62) with a hyperdynamic LV and a 1.1 cm collapsing IVC: the volume assessment is a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with volume and blood (decision C). | Hipotensión por sangrado (98/62) con un VI hiperdinámico y una VCI de 1,1 cm que colapsa: la evaluación del volumen es un objetivo de la reanimación junto con la transfusión, y una ecografía repetida muestra la VCI llenándose con volumen y sangre (decisión C). |
| Evidencia esperada | requests POCUS and names the hyperdynamic LV and the collapsing IVC | solicita POCUS y nombra el VI hiperdinámico y la VCI que colapsa |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `hypoglycemia_28m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. | Se maneja con la glicemia capilar y la glucosa; el POCUS no agrega nada al manejo. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `hypoglycemia_54m_thiamine`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. The thiamine is decided by the history. | Se maneja con la glicemia capilar y la glucosa; el POCUS no agrega nada al manejo. La tiamina se decide por la historia. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `hypoglycemia_76f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. | Se maneja con la glicemia capilar y la glucosa; el POCUS no agrega nada al manejo. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `obstructive_pyelonephritis_58f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Evidencia esperada | requests POCUS and names the volume findings (the IVC and the LV) | solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI) |
| Evidencia esperada | gives, limits or titrates volume, or moves to a vasopressor, because of them | da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos |
| Por qué sí | Septic shock from an infected obstruction (94/54) with a 1.0 cm collapsing IVC and a vigorous LV: POCUS can select and limit the fluid strategy and time the vasopressor (decision C). The renal ultrasound is a formal study in the simulator and does not count by itself (decision H). A repeat scan still shows the arrival IVC: the simulator does not model its response here. | Shock séptico por una obstrucción infectada (94/54) con una VCI de 1,0 cm que colapsa y un VI vigoroso: el POCUS puede elegir y limitar la estrategia de fluidos y decidir el momento del vasopresor (decisión C). La ecografía renal es un estudio formal en el simulador y no cuenta por sí sola (decisión H). Una ecografía repetida sigue mostrando la VCI de la llegada: aquí el simulador no modela su respuesta. |
| Componente observable | Guiding the fluid and haemodynamic strategy with POCUS in septic shock. | Guiar con POCUS la estrategia de fluidos y hemodinámica en el shock séptico. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `opioid_35m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Opioid respiratory depression is treated with naloxone and ventilation; the POCUS adds nothing to the management. | La depresión respiratoria por opioides se trata con naloxona y ventilación; el POCUS no agrega nada al manejo. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `opioid_67f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | Opioid respiratory depression is treated with naloxone and ventilation; the POCUS adds nothing to the management. | La depresión respiratoria por opioides se trata con naloxona y ventilación; el POCUS no agrega nada al manejo. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pneumonia_46f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Septic hypotension (92/58) with a 1.0 cm collapsing IVC, a vigorous LV and no diffuse B-lines: POCUS can select and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with volume (decision C). The consolidation may be named but does not by itself make the opportunity (decision F): one opportunity for the case. | Hipotensión séptica (92/58) con una VCI de 1,0 cm que colapsa, un VI vigoroso y sin líneas B difusas: el POCUS puede elegir y titular la estrategia de fluidos y decidir el momento del vasopresor, y una ecografía repetida muestra la VCI llenándose con volumen (decisión C). La consolidación puede nombrarse, pero no crea por sí sola la oportunidad (decisión F): una oportunidad para el caso. |
| Componente observable | Guiding and reassessing the fluid and haemodynamic strategy with POCUS. | Guiar y reevaluar con POCUS la estrategia de fluidos y hemodinámica. |
| Evidencia esperada | requests POCUS and names the volume findings (the IVC and the LV) | solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI) |
| Evidencia esperada | gives, limits or titrates volume, or moves to a vasopressor, because of them | da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos |
| Evidencia esperada | reassesses with POCUS after volume | reevalúa con POCUS después del volumen |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pneumonia_83m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Componente observable | Guiding and reassessing the fluid and haemodynamic strategy with POCUS. | Guiar y reevaluar con POCUS la estrategia de fluidos y hemodinámica. |
| Evidencia esperada | requests POCUS and names the volume findings (the IVC and the LV) | solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI) |
| Evidencia esperada | gives, limits or titrates volume, or moves to a vasopressor, because of them | da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos |
| Evidencia esperada | reassesses with POCUS after volume | reevalúa con POCUS después del volumen |
| Por qué sí | An older patient referred as dehydrated, 96/60 with a 1.2 cm collapsing IVC and a preserved LV: POCUS can select and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with volume (decision C). The consolidation may be named but does not by itself make the opportunity (decision F): one opportunity for the case. | Paciente mayor derivado como deshidratado, 96/60, con una VCI de 1,2 cm que colapsa y un VI conservado: el POCUS puede elegir y titular la estrategia de fluidos y decidir el momento del vasopresor, y una ecografía repetida muestra la VCI llenándose con volumen (decisión C). La consolidación puede nombrarse, pero no crea por sí sola la oportunidad (decisión F): una oportunidad para el caso. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pulmonary_edema_58m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Diffuse B-lines, a moderately depressed LV and a plethoric IVC separate congestion from the other causes of this presentation; loading volume is a critical event of the case. | Las líneas B difusas, un VI con depresión moderada y una VCI pletórica separan la congestión de las otras causas de este cuadro; cargar volumen es un evento crítico del caso. |
| Componente observable | Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC. | Decidir nitrato, diurético o VMNI, y no dar volumen, a partir de las líneas B, el VI y la VCI. |
| Evidencia esperada | requests POCUS and names the diffuse B-lines and the depressed LV | solicita POCUS y nombra las líneas B difusas y el VI deprimido |
| Evidencia esperada | withholds volume because of them | no da volumen por esos hallazgos |
| Evidencia esperada | gives nitrate, diuretic or NIV because of them | da nitrato, diurético o VMNI por esos hallazgos |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pulmonary_edema_75f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Componente observable | Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC. | Decidir nitrato, diurético o VMNI, y no dar volumen, a partir de las líneas B, el VI y la VCI. |
| Evidencia esperada | requests POCUS and names the diffuse B-lines and the depressed LV | solicita POCUS y nombra las líneas B difusas y el VI deprimido |
| Evidencia esperada | withholds volume because of them | no da volumen por esos hallazgos |
| Evidencia esperada | gives nitrate, diuretic or NIV because of them | da nitrato, diurético o VMNI por esos hallazgos |
| Por qué sí | Diffuse B-lines, a severely depressed LV, a plethoric IVC and small effusions separate congestion from the other causes of this presentation; loading volume is a critical event of the case. | Las líneas B difusas, un VI con depresión severa, una VCI pletórica y derrames pequeños separan la congestión de las otras causas de este cuadro; cargar volumen es un evento crítico del caso. |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pulmonary_embolism_33f`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Stable (110/70) with SpO2 90 %: a mildly enlarged RV without septal flattening and a non-compressible popliteal vein. The proximal DVT confirms thromboembolic disease before the CT angiogram (20 minutes) returns, and an RV without shock argues against thrombolysis, a dangerous action in this case (decision G). | Estable (110/70) con SpO2 90 %: un VD levemente dilatado sin aplanamiento septal y una vena poplítea no compresible. La TVP proximal confirma la enfermedad tromboembólica antes de que vuelva la angio-TC (20 minutos), y un VD sin shock argumenta contra la trombólisis, una acción peligrosa en este caso (decisión G). |
| Componente observable | Integrating the RV and a proximal DVT with the haemodynamic stability: anticoagulation before confirmation, and no thrombolysis. | Integrar el VD y una TVP proximal con la estabilidad hemodinámica: anticoagulación antes de la confirmación, y sin trombólisis. |
| Evidencia esperada | requests POCUS and names the proximal DVT or the RV | solicita POCUS y nombra la TVP proximal o el VD |
| Evidencia esperada | anticoagulates, or states it as pending the angiogram, because of it | anticoagula, o la plantea como pendiente de la angio-TC, por ese hallazgo |
| Evidencia esperada | withholds thrombolysis with the stable haemodynamics and the RV stated | no da trombólisis, y explicita la estabilidad hemodinámica y el VD |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `pulmonary_embolism_61m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Obstructive shock (86/54, SpO2 88 %): an RV larger than the LV with a D-sign and McConnell's sign, and a non-compressible popliteal vein, justify treating a high-risk embolism and deciding reperfusion before the CT angiogram (decision G). | Shock obstructivo (86/54, SpO2 88 %): un VD más grande que el VI con signo D y signo de McConnell, y una vena poplítea no compresible, justifican tratar una embolia de alto riesgo y decidir la reperfusión antes de la angio-TC (decisión G). |
| Componente observable | Deciding reperfusion and anticoagulation from RV strain and a proximal DVT in shock. | Decidir la reperfusión y la anticoagulación a partir de la sobrecarga del VD y una TVP proximal en shock. |
| Evidencia esperada | requests POCUS and names the dilated RV with a D-sign or McConnell's sign, or the DVT | solicita POCUS y nombra el VD dilatado con signo D o signo de McConnell, o la TVP |
| Evidencia esperada | anticoagulates and decides reperfusion because of it | anticoagula y decide la reperfusión por ese hallazgo |
| Evidencia esperada | acts without waiting for the angiogram | actúa sin esperar la angio-TC |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `renal_colic_34m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué no | The renal ultrasound, the study that settles this disposition, is a formal study in the simulator and not POCUS; the POCUS proper does not change the management of a colic without shock (decision H). | La ecografía renal, el estudio que resuelve este destino, es un estudio formal en el simulador y no POCUS; el POCUS propiamente tal no cambia el manejo de un cólico sin shock (decisión H). |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `trauma_hemothorax_41m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | The E-FAST shows an echogenic left pleural collection in shock: a haemothorax, a state the EPA lists, that defines the drain; the case's critical events are the undrained haemothorax and the drained one never looked at again. | El E-FAST muestra una colección pleural izquierda ecogénica en shock: un hemotórax, un estado que la EPA enumera, que define el drenaje; los eventos críticos del caso son el hemotórax no drenado y el drenado que nunca se vuelve a mirar. |
| Componente observable | Deciding the drain and its reassessment from the haemothorax on the E-FAST. | Decidir el drenaje y su reevaluación a partir del hemotórax en el E-FAST. |
| Evidencia esperada | requests the E-FAST and names the left haemothorax | solicita el E-FAST y nombra el hemotórax izquierdo |
| Evidencia esperada | places a chest tube because of it | instala un tubo pleural por ese hallazgo |
| Evidencia esperada | reassesses after the drain with the E-FAST, a film or surgery | reevalúa después del drenaje con el E-FAST, una radiografía o cirugía |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________

### `trauma_limb_hemorrhage_27m`

| Campo | Texto del caso | Borrador |
|---|---|---|
| Por qué sí | Shock (96/54, HR 132) after a machinery injury to the thigh: a negative five-window E-FAST excludes a cavity source and keeps the control on the compressible limb. Free fluid, haemothorax, pneumothorax and the pericardium are states the EPA lists. | Shock (96/54, FC 132) después de una lesión del muslo por maquinaria: un E-FAST negativo en las cinco ventanas descarta una fuente cavitaria y mantiene el control en la extremidad compresible. El líquido libre, el hemotórax, el neumotórax y el pericardio son estados que la EPA enumera. |
| Componente observable | Directing haemorrhage control with the absence of cavity bleeding on the E-FAST. | Dirigir el control de la hemorragia con la ausencia de sangrado cavitario en el E-FAST. |
| Evidencia esperada | requests the E-FAST and names it negative | solicita el E-FAST y lo nombra negativo |
| Evidencia esperada | keeps haemorrhage control on the limb rather than searching a cavity | mantiene el control de la hemorragia en la extremidad en vez de buscar en una cavidad |
| Evidencia esperada | states what would change that | dice qué cambiaría eso |

**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________
