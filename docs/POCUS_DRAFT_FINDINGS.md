# Hallazgos de POCUS — borrador pendiente de revisión docente

> **Estado: BORRADOR.** Estos hallazgos están redactados para ser coherentes con el diagnóstico, los signos vitales, la historia y el examen de cada caso. **No han sido revisados clínicamente.** En el código están marcados con `POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`.

Este documento se generó directamente desde `clinical_cases.py`: lo que lees es exactamente lo que ve el residente. Si corriges algo, corrígelo en el código (bloque `POCUS`) o dímelo y lo cambio.

## Criterios aplicados

- **Estructura fija**, siempre completa y en este orden: corazón, VCI, pulmón, aorta, venas.
- **Hallazgos, no interpretación.** Nunca *"responde a volumen"* ni *"taponamiento"*.
- **VI cualitativo**, sin FE.
- **VCI con diámetro y porcentaje de colapso.**
- Una estructura no documentada se muestra como *"Not documented"*, **nunca como normal**.
- Los textos están en **inglés** porque es el idioma de la app.

## Qué evoluciona con la fisiología — y qué no

Me pediste que la VCI, el VI, las líneas B y el VD evolucionen. **Solo está implementado en parte**:

| Estructura | Casos del banco (16) | PS001 y casos generados por IA |
|---|---|---|
| VCI | **Sí**, solo en neumonía y hemorragia digestiva, según el volumen administrado | **Sí**, según la precarga |
| Líneas B | **Sí**, solo en edema pulmonar | **Sí**, según la congestión |
| Contractilidad VI | **No** — el motor del banco no modela el VI | **Sí** |
| Tamaño VD | **No** | Solo si el caso generado lo declara en sus reglas |
| Aorta, venas, neumotórax, pericardio | Fijos | Fijos |

**Umbrales de la VCI en el banco** (iguales para todos los casos de neumonía y hemorragia digestiva, con independencia del valor inicial). Cada unidad de sangre cuenta como 300 mL:

- **≥ 500 mL:** `1.5 cm; about 50% inspiratory collapse`
- **≥ 1500 mL:** `2.0 cm; <50% inspiratory collapse`

Con VNI o ventilación invasiva, la VCI informa el diámetro y *"respiratory variation not assessable during positive-pressure support"*.

**Líneas B en edema pulmonar:** mientras la congestión no mejora se muestra el hallazgo del caso tal cual, con su distribución. Cuando mejora pasa a *"Fewer but persistent bilateral B-lines"*, conservando la distribución del caso (por ejemplo, *"in the anterior and lateral zones"*).

**Decisión para ti:** los umbrales son genéricos. En un caso que empieza con VCI de 0,9 cm, saltar a 1,5 cm con 500 mL puede ser demasiado. Dime si prefieres umbrales por caso.

## Casos del banco

### pneumonia · variante 0

**Community-acquired pneumonia with hypoxemia and impaired perfusion** · 46 años, female · PA 92/58 · FC 118 · SpO₂ 89% · FR 30 · llene capilar 4 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved, vigorous contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.0 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | Focal B-lines at the right base; no diffuse bilateral B-lines |
|  | Consolidation and pleural effusion | Right basal subpleural consolidation with dynamic air bronchograms; no pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Consolidación basal **derecha**, coherente con el crepitante y el dolor pleurítico derechos de la historia.

### pneumonia · variante 1

**Pneumonia presenting with acute encephalopathy and impaired perfusion** · 83 años, male · PA 96/60 · FC 108 · SpO₂ 91% · FR 28 · llene capilar 4 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.2 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | Focal B-lines at the left base; no diffuse bilateral B-lines |
|  | Consolidation and pleural effusion | Left basal consolidation with air bronchograms; no pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Paciente de 83 años, varón, hipertenso: dejé la aorta abdominal **normal**. Decide si quieres una dilatación incidental como hallazgo distractor.

### pulmonary_edema · variante 0

**Hypertensive acute cardiogenic pulmonary edema** · 58 años, male · PA 218/116 · FC 126 · SpO₂ 81% · FR 38 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Moderately reduced global contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 2.4 cm; <50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | Diffuse bilateral B-lines in the anterior and lateral zones |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- El caso original decía *"No large effusion"* en pericardio; lo escribí como **sin derrame**. Confirma que no querías un derrame pequeño.

### pulmonary_edema · variante 1

**Acute decompensated systolic heart failure with pulmonary edema** · 75 años, female · PA 164/92 · FC 114 · SpO₂ 84% · FR 32 · llene capilar 3 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Severely reduced global contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 2.5 cm; minimal inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | Diffuse bilateral B-lines in the anterior and lateral zones |
|  | Consolidation and pleural effusion | No consolidation; small bilateral pleural effusions |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Los derrames pleurales bilaterales pequeños del caso original van en la línea de consolidación y derrame.

### acs · variante 0

**Inferior ST-elevation myocardial infarction** · 54 años, male · PA 100/64 · FC 58 · SpO₂ 96% · FR 22 · llene capilar 3 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Reduced contraction of the inferior wall; the other walls contract normally |
|  | RV size and relation to LV | Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.8 cm; about 50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- IAM inferior con PA 100/64 y FC 58. Dejé el **VD normal**. Si quieres que el caso incluya compromiso del VD, cambian el VD y la VCI.
- Aorta abdominal **normal**: es relevante porque el dolor es epigástrico.

### acs · variante 1

**Non-ST-elevation acute coronary syndrome** · 66 años, female · PA 146/86 · FC 102 · SpO₂ 95% · FR 24 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Mild hypokinesis of the inferolateral wall; global contraction otherwise preserved |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.7 cm; about 50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Mantuve *"sin líneas B"* como en el original, aunque tiene disnea leve.

### pulmonary_embolism · variante 0

**Acute pulmonary embolism with hypoxemia, initially without hypotension** · 33 años, female · PA 110/70 · FC 124 · SpO₂ 90% · FR 30 · llene capilar 3 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 2.0 cm; <50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Non-compressible on the operated (symptomatic) side, with echogenic intraluminal material; compressible on the other side |

**Revisar:**

- **Lateralidad no definida.** La historia dice *"the operated side"* sin indicar derecha o izquierda. No la inventé: decide el lado.
- TVP **poplítea** no compresible con material ecogénico, y femoral compresible. El caso original decía *"proximal vein"*.
- Tiene dolor pleurítico **derecho**, pero no puse hallazgo pleural. Valora un derrame pequeño o una consolidación subpleural.

### pulmonary_embolism · variante 1

**High-risk pulmonary embolism with obstructive shock** · 61 años, male · PA 86/54 · FC 132 · SpO₂ 88% · FR 32 · llene capilar 5 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Small, underfilled cavity with vigorous contraction |
|  | RV size and relation to LV | Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing (McConnell sign) |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 2.3 cm; minimal inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Left popliteal vein non-compressible; right popliteal vein compressible |

**Revisar:**

- La historia dice *"left calf swelling"*: TVP **poplítea izquierda**, femoral compresible. Decide si también extiendes a la femoral.
- VD mayor que el VI, septum en D y **signo de McConnell presente**, coherente con *"reduced systolic contraction and septal flattening"* del original.

### asthma · variante 0

**Acute severe asthma exacerbation** · 24 años, female · PA 138/84 · FC 126 · SpO₂ 90% · FR 34 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.4 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

### asthma · variante 1

**Life-threatening asthma with fatigue and hypercapnia** · 49 años, male · PA 142/86 · FC 132 · SpO₂ 89% · FR 30 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.6 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Hipercapnia con fatiga. Dejé el deslizamiento pleural **presente**. Con hiperinsuflación podría verse disminuido, pero eso obliga a descartar neumotórax. Decide.

### gi_bleed · variante 0

**Upper gastrointestinal bleeding with hemorrhagic hypoperfusion** · 57 años, male · PA 88/54 · FC 124 · SpO₂ 97% · FR 26 · llene capilar 5 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 0.9 cm; near-complete inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- *"Near-obliteration of the cavity in systole"*: describe el ventrículo vacío en sístole.

### gi_bleed · variante 1

**Upper gastrointestinal bleeding presenting with symptomatic anemia and hypoperfusion** · 72 años, female · PA 98/62 · FC 112 · SpO₂ 96% · FR 24 · llene capilar 4 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Hyperdynamic contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.1 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

### hypoglycemia · variante 0

**Severe insulin-associated hypoglycemia with neuroglycopenia** · 28 años, male · PA 128/76 · FC 112 · SpO₂ 98% · FR 20 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.7 cm; about 50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

### hypoglycemia · variante 1

**Sulfonylurea-associated hypoglycemia with recurrence risk** · 76 años, female · PA 134/78 · FC 96 · SpO₂ 97% · FR 18 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.8 cm; about 50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

### opioid · variante 0

**Opioid toxidrome with respiratory depression following an uncertain tablet exposure** · 35 años, male · PA 106/64 · FC 68 · SpO₂ 80% · FR 6 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.8 cm; minimal respiratory variation with shallow breaths |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- VCI con *"minimal respiratory variation with shallow breaths"*: con FR 6 el colapso inspiratorio no es valorable. Revisa si esa redacción te parece correcta.

### opioid · variante 1

**Long-acting opioid-associated ventilatory depression with recurrence risk** · 67 años, female · PA 104/62 · FC 62 · SpO₂ 84% · FR 8 · llene capilar 2 s

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.9 cm; minimal respiratory variation with shallow breaths |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:**

- Igual que el anterior, con FR 8.

## PS001 — sepsis urinaria con fibrilación auricular

El VI, la VCI y las líneas B son **dinámicos**. Esta tabla muestra un momento de ejemplo. El resto de estructuras son fijas y también están en borrador.

| Sección | Estructura | Hallazgo |
|---|---|---|
| Heart | LV contractility | Preserved to hyperdynamic contraction |
|  | RV size and relation to LV | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign |
|  | Pericardium | No pericardial effusion |
| Inferior vena cava | IVC | 1.4 cm; >50% inspiratory collapse |
| Lungs | Pleural sliding | Present bilaterally; no pneumothorax |
|  | B-lines | No B-lines; A-line pattern bilaterally |
|  | Consolidation and pleural effusion | No consolidation or pleural effusion |
| Aorta | Aortic root | Not dilated |
|  | Descending thoracic aorta | Not dilated in the visible segment |
|  | Abdominal aorta | Normal calibre from the diaphragm to the iliac bifurcation |
| Veins · compression | Femoral veins | Compressible bilaterally |
|  | Popliteal veins | Compressible bilaterally |

**Revisar:** el VD siempre normal y la ausencia de derrame pericárdico, fijos durante todo el caso.
