# Cierre del paquete prepiloto (2026-10-02)

Instrucción docente del 2026-10-02: avanzar con D-1 a D-11, TD-56 y TD-59 para cerrar el paquete prepiloto
(`docs/revision/PRE_PILOT_REVIEW_PACKET.md`), corregir los bloqueos y verificar el recorrido afectado, sin otro
ciclo de auditoría ni ampliar el alcance. Rama `clinical-encounter-v0.13`, sobre `da38b92`. No se desplegó, no se
ejecutó la prueba de humo contra datos reales, no se abrió ninguna respuesta externa y no se generó ningún encuentro
pagado: todo lo verificado corre offline y determinista.

Registro: C-2026-10-02-02 a C-2026-10-02-11 (`corrections_registry.py`, instrucción
`INSTRUCTION_PREPILOT_CLOSURE`); decisiones en `docs/COLA_DECISIONES_AI_ADVISOR.md`, sección «Cierre del paquete
prepiloto»; deuda en `docs/REGISTRO_DEUDA_TECNICA.md`.

---

## 1. Cambios y verificación

| Decisión | Qué cambió | Cómo se verificó |
|---|---|---|
| **D-1 · TD-48** | El E-FAST muestra sus cinco ventanas (doce líneas), con «Not documented» si el caso no documenta una, en la sala, el estado del Management Trace y los documentos de revisión. Un resultado anterior conserva la línea única que su sala mostró | La 41m muestra «Left pleural recess: Fluid in the left pleural recess»; el E-FAST tras el drenaje muestra Morison, esplenorrenal y pelvis libres (C14 de la 41m observable); la 27m, las doce ventanas negativas (C14 de la 27m observable). Español: títulos y rótulos traducidos; las líneas del caso, enteras en inglés hasta aprobar su relato y enteras en español después (`test_td48_efast_window_by_window.py`, 7 pruebas) |
| **D-2 · TD-50** | El examen de la anafilaxia sigue la bandera de estridor del motor, nunca la SpO₂. Tras intubar se oye el tubo y la reacción sigue. El estridor de llegada no se cobra otra vez en el minuto 1; la 63m declara sin compromiso de la vía aérea alta | 29f: adrenalina + O₂ → reacción 0,74 y «…; no stridor heard now.»; sólo O₂ → SpO₂ 99 % con el estridor escrito; intubada → «Endotracheal tube in place: no stridor through the tube…», reacción 1,36 y 71/39. 63m: SpO₂ 89 % en el minuto 1, sin cobro (`test_td50_anaphylaxis_stridor_now.py`, 7 pruebas) |
| **D-3 · TEP** | Fisiología sin recalibrar. El límite de la 33f queda en su declaración y se muestra en la rúbrica y en los objetivos; no excluye el caso | Rúbrica y objetivos lo muestran con «Nunca las cuente contra el residente…» (EN/ES); un encuentro anterior conserva su declaración (`test_rubric_portal.py`, `test_progress_portal.py`, `test_evaluation_basis.py`) |
| **D-4 · D-5** | Nota del shock con el criterio completo; la de la hipotensión sostenida, con el vasopresor; en español «administrada», «Trombólisis», fármaco en español; el aviso del sangrado tiene su español | Concordancia con `pe_obstruction.basis`: en shock, indicada desde el minuto 0; sin signos, 14 min no indica y 15 sí (`test_pe_notes_and_row_18.py`, 7 pruebas) |
| **D-6 · R-4** | La frase 18 recupera «pasa»; dosis, concentración, vía y velocidad intactas | Sala y borrador dicen lo mismo |
| **D-7 · D-8** | 52m: motilidad informada, sin exigir reconocerla, y activar por el ECG es correcto. 70f: se juzga con la presión que deja de responder y el mensaje de la sala; lo que el simulador no muestra no es evaluable | Tabla C14 final, fichas R-2, borradores y matriz de cobertura regeneradas desde el código y comprobadas por sus pruebas |
| **D-9 · TD-49** | La trombólisis del SCA queda una vez por dosis. Defecto: la misma dosis escrita dos veces en los medicamentos administrados; no agrega contenido clínico. TD-51 diferida | 52m y 66f: una fila por dosis; una segunda indicación agrega una; la reperfusión no cambia (`test_td49_acs_thrombolysis_recorded_once.py`) |
| **D-10 · R-3** | Decisión de alcance registrada en `docs/tdfc/TDFC_TABLA_FINAL.md`; ninguna declaración cambia; no se agregó la frase opcional de T-2 | `test_tdfc_opportunities.py` |
| **D-11 · Guías** | Etiquetas en español, el paso de los eventos críticos, los avisos de foto y POCUS, el funcionamiento comprobado y los límites | Cada etiqueta citada se comprobó en el catálogo de la pantalla |
| **TD-56** | Una aprobación de foto espera la cuenta que nombra, nunca se registra bajo otra, y se registra en la primera apertura después de crearla. `check_database.py --photo-approvals` verifica, sólo leyendo. El runbook fija el orden | Hallazgo: la página del administrador abre el banco antes de que la cuenta docente pueda existir, así que el orden escrito no podía cumplirse sin este cambio. Probado en SQLite y en un PostgreSQL 16 local descartable: el administrador entra primero → 2 aprobaciones esperan, la verificación dice «Not ready»; la docente se registra → la siguiente apertura las registra bajo su cuenta → «All 2 approvals are recorded…». Una cuenta de residente con ese nombre nunca las recibe (`test_td56_photo_approvals_wait_for_their_account.py`, 4 pruebas) |
| **TD-59** | «General appearance» dice, bajo el resumen del motor, lo que el caso escribió y sigue siendo cierto; la herida de la 27m según su control | Cada línea es un fragmento literal de la línea del caso; la 27m sin nada → apósito empapado que sangra; con presión → «reduced, not stopped»; con torniquete → «stopped» (`test_td59_general_appearance_keeps_the_case.py`, 7 pruebas) |
| **Traducciones** | Un examen de varias líneas se traduce línea a línea; «flushed» tenía el resumen de la 29f y la 63m entero en inglés; las líneas del tórax que reescribe el motor (tubo, sin estridor) quedaban en inglés aun con el relato aprobado: ahora son pasajes del caso, con su borrador | Cada línea, entera en un idioma, con y sin relato aprobado |

**Consistencia sala · Trace · informes.** El E-FAST usa un solo formateador (`efast_report.format_efast`) en la sala, el
estado del Trace y los documentos. El examen (sala y órdenes escritas) usa `examination_finding` y se traduce con
`language.examination`. Los límites del simulador se leen de la declaración congelada del encuentro, igual en la
rúbrica y en los objetivos.

**Controles ejecutados:** las pruebas focalizadas de cada decisión; el registro de correcciones; el registro de
deuda; las hojas de revisión, los borradores en español, la tabla C14 final y la matriz de cobertura regeneradas
desde el código; la base de evaluación congelada; los textos de casos (`tools_case_text.py check`: completo); las
**56/56 regresiones activas**; y la **suite completa** en cuatro partes: 6.555 pruebas pasaron y 2 fallaron, ambas
de este cierre y mecánicas (la separación estructural entre rúbrica y objetivos, resuelta con el módulo neutral
`encounter_limits.py`; y el catálogo de hipoglicemia, que lista el registro de correcciones y se regeneró). Tras
corregirlas, la parte afectada y todo archivo que toca lo editado: 1.992 pasaron, 0 fallaron. El orden de las fotos
(TD-56) se probó además en un PostgreSQL 16 local descartable.

---

## 2. Tabla única de lo que requiere su firma

Estado: **activo** = la sala ya lo muestra; **borrador** = no se muestra hasta su firma; **con el relato** = se
muestra en español cuando usted aprueba el relato de ese caso en el tablero docente (hasta entonces, la línea entera
en inglés). Las fichas R-2 se firman en `docs/revision/R2_POCUS_C14.md`, que tiene su contenido completo.

| # | Qué | Texto final (EN) | Español final | Estado | Firma |
|---|---|---|---|---|---|
| **R-4** | **Las 18 frases del motor** (D-6) | | | | |
| 1 | Paro por hemorragia | Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume replaces a source that is still open. | Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido; la reposición de volumen no sustituye el control del sangrado activo. | borrador | ☐ |
| 2 | Edema pulmonar | Bilateral inspiratory crackles with increased respiratory effort. | Crépitos inspiratorios bilaterales, con aumento del esfuerzo respiratorio. | borrador | ☐ |
| 3 | Edema pulmonar | Bilateral crackles remain, with reduced respiratory effort. | Persisten crépitos bilaterales, con menor esfuerzo respiratorio. | borrador | ☐ |
| 4 | Sobrecarga por transfusión | New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze. | Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin sibilancias. | borrador | ☐ |
| 5 | Asma | Improved air entry with residual expiratory wheeze. | Mejor entrada de aire, con sibilancias espiratorias residuales. | borrador | ☐ |
| 6 | Asma | Reduced bilateral air entry with prolonged expiration and wheeze. | Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias. | borrador | ☐ |
| 7 | Neumotórax a tensión | Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side. | Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado. | borrador | ☐ |
| 8 | Tras descomprimir | Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze. | Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de aire, con sibilancias espiratorias residuales. | borrador | ☐ |
| 9 | Ventilación asistida | Respiratory rate {n} /min; assisted ventilation is in progress. | Frecuencia respiratoria {n}/min, dada por la ventilación asistida en curso. | borrador | ☐ |
| 10 | Opioide | Respiratory rate {n} /min; breaths remain shallow. | Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales. | borrador | ☐ |
| 11 | Opioide revertido | Respiratory rate {n} /min; spontaneous breaths have greater depth. | Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas. | borrador | ☐ |
| 12 | Vía infiltrándose | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría. | activo | ☐ |
| 13 | Vía funcionando | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación. | activo | ☐ |
| 14 | Vía fallida | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y doloroso a la palpación. | activo | ☐ |
| 15 | Segunda vía | A second peripheral cannula in the right forearm; the site is clean. | Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio. | activo | ☐ |
| 16 | Intraósea | An intraosseous needle in place (humeral). | Una aguja intraósea instalada (humeral). | activo | ☐ |
| 17 | Intraósea sin sitio | An intraosseous needle in place; no site was recorded. | Una aguja intraósea instalada; no se registró el sitio. | activo | ☐ |
| 18 | Infusión de glucosa | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo. | activo | ☐ |
| **TEP** | **Las 7 notas y el aviso del sangrado** (D-4, D-5) | | | | |
| 19 | Nota 1 · shock | Systemic thrombolysis given in obstructive shock: systolic below 90 mmHg, or a vasopressor needed to reach 90 mmHg, with signs of hypoperfusion. In shock it is indicated as soon as the shock is present; the 15 consecutive minutes apply only to a hypotension without those signs. The drug acts on the clot over about half an hour; what it changes is seen on reassessment. | Trombólisis sistémica administrada en shock obstructivo: sistólica bajo 90 mmHg, o un vasopresor necesario para llegar a 90 mmHg, con signos de hipoperfusión. En shock está indicada desde que el shock está presente; los 15 minutos consecutivos aplican sólo a una hipotensión sin esos signos. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar. | activo | ☐ |
| 20 | Nota 2 · hipotensión sostenida | Systemic thrombolysis given for sustained hypotension: systolic below 90 mmHg, or a vasopressor needed to keep it at 90 mmHg or above, for 15 consecutive minutes. The drug acts on the clot over about half an hour; what it changes is seen on reassessment. | Trombólisis sistémica administrada por hipotensión sostenida: sistólica bajo 90 mmHg, o un vasopresor necesario para mantenerla en 90 mmHg o más, durante 15 minutos consecutivos. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar. | activo | ☐ |
| 21 | Nota 3 · sin indicación, baja | Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg with no sign of hypoperfusion, low for {m} of the 15 consecutive minutes a hypotension without them requires. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment. | Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg sin signos de hipoperfusión, baja durante {m} de los 15 minutos consecutivos que exige una hipotensión sin ellos. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar. | activo | ☐ |
| 22 | Nota 4 · vasopresor innecesario | Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg on a vasopressor the pressure does not need, with no hypotension from the embolism. (sigue como la 3) | Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg con un vasopresor que la presión no necesita, sin hipotensión por la embolia. (sigue como la 3) | activo | ☐ |
| 23 | Nota 5 · normotenso | Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg, with no hypotension from the embolism. (sigue como la 3) | Trombólisis sistémica administrada sin la indicación hemodinámica: sistólica de {n} mmHg, sin hipotensión por la embolia. (sigue como la 3) | activo | ☐ |
| 24 | Nota 6 · resto del esquema | alteplase {n} mg recorded as part of the initial regimen begun at minute {t} ({total} mg in all). It completes the first dose rather than starting a new one, and the first dose keeps acting as before. | Se registran {n} mg de alteplasa como parte del esquema inicial comenzado en el minuto {t} ({total} mg en total): completan la primera dosis en lugar de iniciar una nueva, y la primera dosis sigue actuando como antes. | activo | ☐ |
| 25 | Nota 7 · segundo curso | A second course of systemic thrombolysis is recorded (alteplase {n} mg); the first course began at minute {t}. Its added bleeding risk is recorded as exposure. This simulator represents neither additional reperfusion from a second course nor any bleeding of its own; that is a simplification, not evidence that repeating has no effect. The first dose keeps acting as before. | Se registra un segundo curso de trombólisis sistémica (alteplasa {n} mg); el primero comenzó en el minuto {t}. Su riesgo adicional de sangrado queda registrado como exposición. Este simulador no representa una reperfusión adicional por un segundo curso ni un sangrado propio; es una simplificación, no evidencia de que repetir no tenga efecto. La primera dosis sigue actuando como antes. | activo | ☐ |
| 26 | Aviso del sangrado (33f) | Bleeding from the surgical site operated on twelve days ago: the haemoglobin is falling. This is the risk the thrombolytic carries, and it was taken in a patient who had a reason to bleed. | Sangrado del sitio operado hace doce días: la hemoglobina está bajando. Es el riesgo que conlleva el trombolítico, y se asumió en una persona que tenía un motivo para sangrar. | activo | ☐ |
| **Examen** | **Líneas nuevas del cierre** (TD-50, TD-47, TD-59) | | | | |
| 27 | 29f, sin estridor | Increased effort with widespread expiratory wheeze; no stridor heard now. | Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas; ya no se escucha estridor. | EN activo; ES con el relato | ☐ |
| 28 | 29f, intubada | Endotracheal tube in place: no stridor through the tube; widespread expiratory wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias espiratorias difusas. | EN activo; ES con el relato | ☐ |
| 29 | 63m, intubado | Endotracheal tube in place: no stridor through the tube; widespread wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias difusas. | EN activo; ES con el relato | ☐ |
| 30 | 63m (anafilaxia) | A sting site on the right forearm. | Sitio de picadura en el antebrazo derecho. | EN activo; ES con el relato | ☐ |
| 31 | 34m y 54f | No rash. | Sin erupción. | EN activo; ES con el relato | ☐ |
| 32 | 68m | No rash or swelling. | Sin erupción ni edema. | EN activo; ES con el relato | ☐ |
| 33 | 63m (hiperkalemia) | A dialysis fistula in the left forearm. | Una fístula de diálisis en el antebrazo izquierdo. | EN activo; ES con el relato | ☐ |
| 34 | 41m | Seatbelt marking across the chest and abdomen. | Marca del cinturón de seguridad que cruza el tórax y el abdomen. | EN activo; ES con el relato | ☐ |
| 35 | 27m, sin control | A soaked dressing over a deep right thigh wound that is bleeding. | Apósito empapado sobre una herida profunda del muslo derecho que está sangrando. | EN activo; ES con el relato | ☐ |
| 36 | 27m, con control | A deep right thigh wound. | Una herida profunda del muslo derecho. | EN activo; ES con el relato | ☐ |
| 37 | 27m, estado del motor | The external bleeding is reduced, not stopped. / The external bleeding is stopped. | El sangrado externo está disminuido, sin detenerse. / El sangrado externo está detenido. | activo | ☐ |
| 38 | Color del resumen | Color: flushed | Color: enrojecimiento | activo | ☐ |
| **E-FAST** | **Títulos y rótulos** (D-1) | E-FAST · performed at minute {n}; RIGHT UPPER QUADRANT, LEFT UPPER QUADRANT, SUPRAPUBIC, SUBXIPHOID, LUNG; Morison's pouch (hepatorenal), Right subdiaphragmatic space, Right pleural recess, Splenorenal space, Left subdiaphragmatic space, Left pleural recess, Longitudinal view, Transverse view, Pericardium, Right lung sliding, Left lung sliding, M-mode; Not documented | E-FAST · realizado en el minuto {n}; CUADRANTE SUPERIOR DERECHO, CUADRANTE SUPERIOR IZQUIERDO, SUPRAPÚBICA, SUBXIFOIDEA, PULMÓN; Espacio de Morison (hepatorrenal), Espacio subdiafragmático derecho, Receso pleural derecho, Espacio esplenorrenal, Espacio subdiafragmático izquierdo, Receso pleural izquierdo, Vista longitudinal, Vista transversal, Pericardio, Deslizamiento pulmonar derecho, Deslizamiento pulmonar izquierdo, Modo M; No documentado | activo | ☐ |
| **Límites** | **Lo que el simulador no muestra ni trata** (D-3, D-8, TD-54), en la rúbrica y los objetivos | | | | |
| 39 | Encabezado y aviso | What the simulator cannot show or treat in this case · Never count these against the resident: what the simulator cannot show is not evidence, and a measure written for it is not an omission. | Lo que el simulador no puede mostrar ni tratar en este caso · Nunca las cuente contra el residente: lo que el simulador no puede mostrar no es evidencia, y una medida escrita para ello no es una omisión. | activo | ☐ |
| 40 | 33f | After a thrombolytic the bleeding from the operated site does not stop in this simulator: the haemoglobin keeps falling while the pressure can stay reassuring. The room cannot stop an alteplase infusion; tranexamic acid and cryoprecipitate are recorded without a modelled effect, and fibrinogen concentrate is not recognised. The response to that bleeding is not evaluated and is never used to judge haemorrhage rescue: not reversing it is never charged, and a measure written for it is never an omission. The decision to give the thrombolytic is judged as before, on the minute it was given. | (en inglés, como toda declaración del banco; la guía docente lo dice en español) | activo | ☐ |
| 41 | 70f | A volume past this ventricle's tolerance shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the saturation and a repeat POCUS do not change. Detecting overload on the examination or POCUS is not required; when the only response the resident looked for is one the simulator does not show, that part is not evaluable rather than missing. | (ídem) | activo | ☐ |
| 42 | 46f y 83m | A repeat POCUS shows the IVC filling with volume, but its lungs show no new B-lines with crystalloid overload; the saturation does fall. Seeing new B-lines is not required. | (ídem) | activo | ☐ |
| 43 | 27m | A repeat POCUS shows the arrival IVC whatever the volume or the haemorrhage control, and a repeat E-FAST repeats the arrival windows: a change the simulator does not show is not required. | (ídem) | activo | ☐ |
| 44 | 41m | A repeat POCUS shows the arrival IVC whatever the volume, and a repeat E-FAST repeats the arrival windows, the drained pleural recess included: what it adds is the other cavities still clear. | (ídem) | activo | ☐ |
| **C14** | **Declaraciones cambiadas** (D-7, D-8); el texto completo y su borrador en español están en `docs/revision/TD04_POCUS_C14.md` y `docs/revision/ES_BORRADORES.md` | | | | |
| 45 | 52m | Component: «Using the reported regional wall motion to prioritise the reperfusion decision.» Evidence: «requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion; activates or expedites reperfusion». Rationale adds: «The report states the wall motion; recognising it is not required. POCUS never delays reperfusion: activating it from the ECG alone is correct and is not a C14 deficit.» | Borrador inactivo (TD-07) | activo (EN) | ☐ |
| 46 | 70f | Rationale adds: «In this simulator a volume past the ventricle's tolerance shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the saturation and a repeat POCUS do not change. The adaptation is judged on those signals: detecting overload on the examination or POCUS is not required, and when the only response the resident looked for is one the simulator does not show, that part of the observation is not evaluable rather than missing.» | Borrador inactivo (TD-07) | activo (EN) | ☐ |
| **R-2** | **Las 14 fichas POCUS** (D-7: criterios aceptados; cada ficha espera su firma) | | | | |
| 47 | `acs_52m_de_winter` | CONFIRM · redacción D-7 aplicada | | ficha lista | ☐ |
| 48 | `acs_61m_posterior` | CONFIRM · criterio R-2 | | ficha lista | ☐ |
| 49 | `acs_70f_left_main` | CONFIRM · criterios R-2 y D-8 | | ficha lista | ☐ |
| 50 | `gi_bleed_57m` | CONFIRM | | ficha lista | ☐ |
| 51 | `gi_bleed_72f` | CONFIRM | | ficha lista | ☐ |
| 52 | `obstructive_pyelonephritis_58f` | CONFIRM · su C14 declara la VCI de control | | ficha lista | ☐ |
| 53 | `pneumonia_46f` | CONFIRM · TD-54 declarado | | ficha lista | ☐ |
| 54 | `pneumonia_83m` | CONFIRM · sin «dynamic» (D-7); TD-54 declarado | | ficha lista | ☐ |
| 55 | `pulmonary_edema_58m` | CONFIRM | | ficha lista | ☐ |
| 56 | `pulmonary_edema_75f` | CONFIRM | | ficha lista | ☐ |
| 57 | `pulmonary_embolism_33f` | CONFIRM | | ficha lista | ☐ |
| 58 | `pulmonary_embolism_61m` | CONFIRM | | ficha lista | ☐ |
| 59 | `trauma_hemothorax_41m` | CONFIRM · lista tras TD-48 (D-1) | | ficha lista | ☐ |
| 60 | `trauma_limb_hemorrhage_27m` | CONFIRM · lista tras TD-48 (D-1) | | ficha lista | ☐ |
| **Otros** | | | | | |
| 61 | R-3 (D-10) | `docs/tdfc/TDFC_TABLA_FINAL.md`: T-2 C1 YES; T-3 y T-4 NO; sin frase opcional | | documento final | ☐ |
| 62 | Guía docente (D-11) | `docs/GUIA_DOCENTE_PILOTO.md` | | lista para firma | ☐ |
| 63 | Guía del residente (D-11) | `docs/GUIA_RESIDENTE_PILOTO.md` | | lista para firma | ☐ |
| 64 | Aviso de la foto | A still photograph does not show every clinical sign; examine the patient to assess what it cannot carry. | Propuesta, sin activar: «Una fotografía fija no muestra todos los signos clínicos; examine al paciente para evaluar lo que no puede mostrar.» | EN activo; ES borrador | ☐ |

---

## 3. Casos

**Incluidos: los 31 casos del banco.** Ninguno se excluye en este cierre: en cada uno, el objetivo central sigue siendo
evaluable con lo que el simulador muestra (D-3).

**Excluidos (como antes):** las 9 composiciones de hipoglicemia; los casos escritos por IA; PS001 y PS002.

**Con alcance de evaluación limitado y declarado** (se juegan igual; el docente lo ve donde evalúa o en su guía):

| Caso | Límite | Regla |
|---|---|---|
| `pulmonary_embolism_33f` | El sangrado tras la lisis no se detiene; no se puede suspender la alteplasa; ácido tranexámico y crioprecipitado sin efecto; fibrinógeno no reconocido (TD-55) | D-3: la respuesta al sangrado no se evalúa ni juzga el rescate hemorrágico; nada se cobra por no revertirla. La decisión de trombolizar se juzga en su minuto |
| `acs_70f_left_main` | La sobrecarga no cambia pulmón, examen, saturación ni POCUS (TD-53) | D-8: se juzga con la presión que deja de responder y el mensaje; un bolo pequeño justificado y reevaluado es aceptable; lo no visible no es evaluable |
| `pneumonia_46f`, `pneumonia_83m` | El POCUS de control no muestra líneas B nuevas con cristaloides (TD-54) | No se exige verlas |
| `trauma_limb_hemorrhage_27m`, `trauma_hemothorax_41m` | La VCI de control y el E-FAST de control repiten la llegada (TD-54) | No se exige ver un cambio |
| `obstructive_pyelonephritis_58f` | VCI de control sin cambio (TD-54, ya en su C14); enrojecimiento y escalofríos no se repiten (TD-59) | No se exige reevaluarlos |
| `anaphylaxis_29f` | C3 parcial (R-3); urticaria, enrojecimiento y edema no se repiten (TD-59) | C3 sólo por la anticipación de la vía aérea |
| `anaphylaxis_63m_betablocked` | Enrojecimiento y habones no se repiten (TD-59) | No se exige reevaluarlos |
| `renal_colic_34m` | La inquietud no se repite; el dolor lo informan las actualizaciones clínicas (TD-59) | — |
| `acs_52m_de_winter`, `acs_61m_posterior` | La motilidad la entrega el informe escrito | No se exige reconocerla (D-7, R-2) |
| `bradycardia_bb_54f`, `pulmonary_edema_75f` | Vista neutral a la llegada | Se juegan igual |

---

## 4. Pendientes reales antes de iniciar el piloto

1. **Sus firmas:** la tabla del punto 2 (R-4, notas de la TEP, líneas del examen, rótulos del E-FAST, límites, las dos
   declaraciones C14, las 14 fichas R-2, R-3 y las dos guías).
2. **El relato en español de cada caso**, si el piloto se jugará en español: se aprueba en el tablero docente de la base
   desplegada. Las líneas nuevas del examen (filas 27 a 36) se aprueban con él.
3. **A · Despliegue** del commit aprobado con la configuración del piloto, con el preflight en «LISTA».
4. **TD-56 en el despliegue:** la cuenta aprobadora creada por la persona que dio las aprobaciones, con ese nombre exacto,
   y `check_database.py --photo-approvals` en «All 117 approvals are recorded…» antes de cualquier invitación de
   residente (runbook §3, pasos 5 a 8). Si esa cuenta no puede crearse, es un bloqueo del despliegue.
5. **B · Prueba de humo** contra el entorno desplegado, sobre el candidato final.
6. **C · Su autorización explícita.**

El encargo de UX del encuentro recibido el 2026-10-02 cambiará la pantalla del residente: la prueba de humo (5) y la
guía del residente se comprueban sobre el candidato final que lo incluya.

**No bloquean, quedan registrados:** TD-51 (diferida), TD-52, TD-58, TD-45 y el lector, y el aviso de la foto en inglés
(fila 64).
