# B-5 · Relato en español · Lote 0: frases comunes

> **PARA REVISIÓN DOCENTE. Nada implementado.** Primer lote de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`, aprobado por la docencia el 2026-10-07). Aprobar una frase aquí no
> aprueba ningún caso: la aprobación final es por caso entero, con su versión exacta, en su lote (R1 a R6). Este lote
> evita leer 527 veces lo que dicen 47 frases.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/*.json` contra el inglés vigente de
> cada caso (`case_text.current_english`), sin cambiar nada.

**En una mirada**

- **47 frases** que se repiten, iguales, en 2 casos o más: **527 apariciones** en los 30 casos del piloto.
- Cada frase tiene **un solo español** en todas sus apariciones; ninguna está traducida de dos formas.
- **11 decisiones docentes**, una por grupo (G1 a G11). Los grupos juntan frases de la misma sección y del mismo
  registro. Dentro de un grupo, cualquier frase se puede sacar con su número y una nota.
- **Recomendación para los 11 grupos: APPROVE AS IS.** La lectura no encontró ningún problema semántico ni clínico.
  Las notas en cursiva explican una elección de redacción; no son observaciones.
- **No están en este lote:**
  - los 18 pasajes que fija el corpus de la validación externa (aprobados tal cual el 2026-10-07);
  - los pasajes de la terminología decidida (T-1 a T-3; abajo).

**Cómo leer**

- «Apariciones · casos»: cuántas veces aparece la frase y en cuántos casos.
- «Dónde»: la ruta del pasaje y los casos. «Los 30 casos menos …» nombra los que no la tienen.
- Las 527 apariciones se reconstruyen exactamente desde esa columna; lo comprobó el script que genera este documento.

## 1. Frases comunes

### G1 · POCUS · venas (TVP) — 1 frase, 58 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-01 | Compressible bilaterally | Compresibles bilateralmente *Concuerda con el rótulo de la sala, «venas femorales (TVP)» y «venas poplíteas (TVP)».* | 58 · 30 | `/investigations/pocus/result/dvt_femoral`: los 30 casos<br>`/investigations/pocus/result/dvt_popliteal`: los 30 casos menos `pulmonary_embolism_33f` y `pulmonary_embolism_61m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G1): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G2 · POCUS · corazón y pericardio — 6 frases, 72 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-02 | No pericardial effusion | Sin derrame pericárdico | 30 · 30 | `/investigations/pocus/result/pericardium`: los 30 casos |
| L0-03 | Smaller than the LV; no septal flattening (no D-sign); no McConnell sign | Menor que el VI; sin aplanamiento septal (sin signo D); sin signo de McConnell *VD y VI, como los rótulos de la sala.* | 27 · 27 | `/investigations/pocus/result/rv`: los 30 casos menos `acs_54m_inferior`, `pulmonary_embolism_33f` y `pulmonary_embolism_61m` |
| L0-04 | Preserved contraction | Contracción conservada | 7 · 7 | `/investigations/pocus/result/lv`: `asthma_24f`, `asthma_49m`, `hypoglycemia_76f`, `opioid_35m`, `opioid_67f`, `pneumonia_83m`, `pulmonary_embolism_33f` |
| L0-05 | Preserved, vigorous contraction | Contracción conservada y vigorosa | 3 · 3 | `/investigations/pocus/result/lv`: `obstructive_pyelonephritis_58f`, `pneumonia_46f`, `renal_colic_34m` |
| L0-06 | Preserved, mildly hyperdynamic contraction | Contracción conservada, levemente hiperdinámica | 2 · 2 | `/investigations/pocus/result/lv`: `hypoglycemia_28m`, `hypoglycemia_54m_thiamine` |
| L0-07 | Globally reduced contraction at a slow rate; no regional difference identified | Contracción globalmente disminuida a frecuencia lenta; no se identifica diferencia regional | 3 · 3 | `/investigations/pocus/result/lv`: `bradycardia_bb_54f`, `bradycardia_ccb_68m`, `bradycardia_hyperk_63m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G2): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G3 · POCUS · vena cava inferior — 5 frases, 13 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-08 | 1.0 cm; >50% inspiratory collapse | 1.0 cm; colapso inspiratorio >50% | 2 · 2 | `/investigations/pocus/result/ivc`: `obstructive_pyelonephritis_58f`, `pneumonia_46f` |
| L0-09 | 1.1 cm; >50% inspiratory collapse | 1.1 cm; colapso inspiratorio >50% | 4 · 4 | `/investigations/pocus/result/ivc`: `anaphylaxis_63m_betablocked`, `gi_bleed_72f`, `hypoglycemia_28m`, `hypoglycemia_54m_thiamine` |
| L0-10 | 1.4 cm; >50% inspiratory collapse | 1.4 cm; colapso inspiratorio >50% | 2 · 2 | `/investigations/pocus/result/ivc`: `asthma_24f`, `renal_colic_34m` |
| L0-11 | 1.7 cm; about 50% inspiratory collapse | 1.7 cm; colapso inspiratorio de aproximadamente 50% | 2 · 2 | `/investigations/pocus/result/ivc`: `acs_66f_nonst`, `hypoglycemia_76f` |
| L0-12 | 1.9 cm; <50% inspiratory collapse | 1.9 cm; colapso inspiratorio <50% | 3 · 3 | `/investigations/pocus/result/ivc`: `bradycardia_bb_54f`, `bradycardia_ccb_68m`, `bradycardia_hyperk_63m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G3): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G4 · POCUS · pulmón y pleura — 4 frases, 84 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-13 | Present bilaterally; no pneumothorax | Presente bilateralmente; sin neumotórax | 30 · 30 | `/investigations/pocus/result/lung_sliding`: los 30 casos |
| L0-14 | No consolidation or pleural effusion | Sin consolidación ni derrame pleural | 27 · 27 | `/investigations/pocus/result/lung_consolidation`: los 30 casos menos `pneumonia_46f`, `pneumonia_83m` y `pulmonary_edema_75f` |
| L0-15 | No B-lines; A-line pattern bilaterally | Sin líneas B; patrón de líneas A bilateral | 25 · 25 | `/investigations/pocus/result/lungs`: los 30 casos menos `acs_70f_left_main`, `pneumonia_46f`, `pneumonia_83m`, `pulmonary_edema_58m` y `pulmonary_edema_75f` |
| L0-16 | Diffuse bilateral B-lines in the anterior and lateral zones | Líneas B difusas bilaterales en las zonas anteriores y laterales | 2 · 2 | `/investigations/pocus/result/lungs`: `pulmonary_edema_58m`, `pulmonary_edema_75f` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G4): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G5 · POCUS · aorta — 3 frases, 90 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-17 | Not dilated | No dilatada *Concuerda con «raíz aórtica».* | 30 · 30 | `/investigations/pocus/result/aorta_root`: los 30 casos |
| L0-18 | Not dilated in the visible segment | No dilatada en el segmento visible *Concuerda con «aorta descendente».* | 30 · 30 | `/investigations/pocus/result/aorta_descending`: los 30 casos |
| L0-19 | Normal calibre from the diaphragm to the iliac bifurcation | Calibre normal desde el diafragma hasta la bifurcación ilíaca | 30 · 30 | `/investigations/pocus/result/aorta_abdominal`: los 30 casos |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G5): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G6 · Laboratorio y microbiología — 4 frases, 90 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-20 | Single sample; interpret with symptoms and ECG. Serial testing requires a new sample. | Muestra única; interpretar junto con los síntomas y el ECG. La medición seriada requiere una nueva muestra. | 30 · 30 | `/investigations/troponin/result/report`: los 30 casos |
| L0-21 | Samples collected; culture identification and susceptibility results are pending. | Muestras tomadas; los resultados de identificación y susceptibilidad del cultivo están pendientes. | 30 · 30 | `/investigations/blood_cultures/result/report`: los 30 casos |
| L0-22 | No leukocyte esterase, nitrite or blood detected. | No se detectan esterasa leucocitaria, nitritos ni sangre. | 28 · 28 | `/investigations/urinalysis/result/report`: los 30 casos menos `obstructive_pyelonephritis_58f` y `renal_colic_34m` |
| L0-23 | Age-adjusted upper reference: 500 ng/mL FEU up to 50 years, age x 10 above it. Above the limit: this does not establish a diagnosis and does not exclude one. | Referencia superior ajustada por edad: 500 ng/mL FEU hasta los 50 años, y edad x 10 por encima. Sobre el límite: esto no establece un diagnóstico ni lo descarta. | 2 · 2 | `/investigations/d_dimer/result/report`: `pulmonary_embolism_33f`, `pulmonary_embolism_61m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G6): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G7 · Radiografía de tórax — 4 frases, 11 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-24 | No focal consolidation or pulmonary edema. | Sin consolidación focal ni edema pulmonar. | 5 · 5 | `/investigations/chest_xray/result/report`: `acs_52m_de_winter`, `acs_54m_inferior`, `acs_61m_posterior`, `gi_bleed_57m`, `pulmonary_embolism_61m` |
| L0-25 | No focal consolidation or edema. | Sin consolidación focal ni edema. | 2 · 2 | `/investigations/chest_xray/result/report`: `hypoglycemia_76f`, `opioid_67f` |
| L0-26 | Clear lung fields; no consolidation or edema. | Campos pulmonares limpios; sin consolidación ni edema. | 2 · 2 | `/investigations/chest_xray/result/report`: `bradycardia_avb3_78f`, `bradycardia_bb_54f` |
| L0-27 | No acute cardiopulmonary abnormality. | Sin alteraciones cardiopulmonares agudas. | 2 · 2 | `/investigations/chest_xray/result/report`: `acs_48m_wellens`, `gi_bleed_72f` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G7): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G8 · ECG · derivaciones adicionales — 2 frases, 12 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-28 | Posterior leads. | Derivaciones posteriores. | 6 · 6 | `/investigations/ecg_posterior/result/report`: `acs_48m_wellens`, `acs_52m_de_winter`, `acs_54m_inferior`, `acs_61m_posterior`, `acs_66f_nonst`, `acs_70f_left_main` |
| L0-29 | Right-sided leads. | Derivaciones derechas. | 6 · 6 | `/investigations/ecg_right/result/report`: `acs_48m_wellens`, `acs_52m_de_winter`, `acs_54m_inferior`, `acs_61m_posterior`, `acs_66f_nonst`, `acs_70f_left_main` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G8): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G9 · Fuente de la historia — 3 frases, 23 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-30 | Patient | Paciente | 19 · 19 | `/history_source`: `acs_48m_wellens`, `acs_52m_de_winter`, `acs_54m_inferior`, `acs_61m_posterior`, `acs_66f_nonst`, `acs_70f_left_main`, `anaphylaxis_29f`, `asthma_24f`, `bradycardia_hyperk_63m`, `gi_bleed_57m`, `gi_bleed_72f`, `obstructive_pyelonephritis_58f`, `pneumonia_46f`, `pulmonary_edema_58m`, `pulmonary_edema_75f`, `pulmonary_embolism_33f`, `pulmonary_embolism_61m`, `renal_colic_34m`, `trauma_limb_hemorrhage_27m` |
| L0-31 | Daughter | Hija | 2 · 2 | `/history_source`: `bradycardia_ccb_68m`, `pneumonia_83m` |
| L0-32 | Partner | Pareja | 2 · 2 | `/history_source`: `asthma_49m`, `bradycardia_bb_54f` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G9): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G10 · Historia — 5 frases, 40 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-33 | No known medication allergies are reported. | No se refieren alergias medicamentosas conocidas. | 30 · 30 | `/history/allergies/0`: los 30 casos |
| L0-34 | I have had no bleeding. | No he tenido ningún sangrado. | 4 · 4 | `/history/bleeding/0`: `acs_48m_wellens`, `acs_52m_de_winter`, `acs_61m_posterior`, `acs_70f_left_main` |
| L0-35 | I have no fever or productive cough. | No tengo fiebre ni tos productiva. | 2 · 2 | `/history/associated_symptoms/1`: `acs_70f_left_main`, `pulmonary_embolism_33f` |
| L0-36 | I have no burning or frequency when passing urine. | No tengo ardor al orinar ni orino más seguido. | 2 · 2 | `/history/urinary_symptoms/0`: `anaphylaxis_29f`, `pneumonia_46f` |
| L0-37 | I have no urinary burning or frequency. | No tengo ardor al orinar ni estoy orinando más seguido. | 2 · 2 | `/history/urinary_symptoms/0`: `gi_bleed_57m`, `pulmonary_edema_58m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G10): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

### G11 · Examen físico — 10 frases, 34 apariciones

| N.º | EN | ES propuesto | Apariciones · casos | Dónde (ruta: casos) |
|---|---|---|---|---|
| L0-38 | Soft and non-tender. | Blando e indoloro. | 15 · 15 | `/examination/Abdomen`: `acs_48m_wellens`, `acs_52m_de_winter`, `acs_61m_posterior`, `acs_66f_nonst`, `acs_70f_left_main`, `anaphylaxis_63m_betablocked`, `asthma_24f`, `asthma_49m`, `bradycardia_avb3_78f`, `bradycardia_bb_54f`, `bradycardia_ccb_68m`, `hypoglycemia_28m`, `opioid_67f`, `pulmonary_edema_58m`, `pulmonary_embolism_33f` |
| L0-39 | Soft without focal tenderness. | Blando, sin dolor focal a la palpación. | 2 · 2 | `/examination/Abdomen`: `hypoglycemia_76f`, `opioid_35m` |
| L0-40 | Normal effort with clear breath sounds. | Esfuerzo respiratorio normal, con murmullo pulmonar sin ruidos agregados. | 2 · 2 | `/examination/Respiratory`: `bradycardia_avb3_78f`, `renal_colic_34m` |
| L0-41 | Rapid regular pulse; elevated jugular venous pressure. | Pulso rápido y regular; presión venosa yugular elevada. | 2 · 2 | `/examination/Cardiac`: `pulmonary_edema_58m`, `pulmonary_embolism_61m` |
| L0-42 | Rapid regular pulse; no new murmur heard. | Pulso rápido y regular; no se ausculta soplo nuevo. | 2 · 2 | `/examination/Cardiac`: `pneumonia_46f`, `pneumonia_83m` |
| L0-43 | Regular palpable pulse. | Pulso regular y palpable. | 2 · 2 | `/examination/Cardiac`: `opioid_35m`, `opioid_67f` |
| L0-44 | Regular tachycardia; no new murmur. | Taquicardia regular; sin soplos nuevos. | 2 · 2 | `/examination/Cardiac`: `asthma_24f`, `pulmonary_embolism_33f` |
| L0-45 | Alert and oriented. | Alerta, con orientación conservada. *Neutra a propósito: la comparten un hombre y dos mujeres; «orientado» no serviría para las tres.* | 3 · 3 | `/examination/Neurological`: `acs_52m_de_winter`, `acs_70f_left_main`, `pulmonary_embolism_33f` |
| L0-46 | Opens eyes to voice, follows simple commands slowly, moves all limbs. | Abre los ojos al llamado verbal, obedece órdenes simples con lentitud, moviliza todas las extremidades. | 2 · 2 | `/examination/Neurological`: `bradycardia_avb3_78f`, `bradycardia_bb_54f` |
| L0-47 | No rash. | Sin erupción. | 2 · 2 | `/appearance_stable`: `bradycardia_bb_54f`, `renal_colic_34m` |

- Observaciones semánticas o clínicas: ninguna.
- Recomendación: **APPROVE AS IS**.
- Decisión docente (G11): ☐ APPROVE · ☐ REVIEW CLOSELY · ☐ NEEDS REVISION — N.º y nota: ________

## 2. Terminología ya decidida (T-1 a T-3, docente, 2026-10-07)

Ninguna de las 47 frases contiene estos términos. Se aplican en los lotes de casos, y cada pasaje se muestra allí ya
con el término aprobado.

| Decisión | Término | Pasajes que cambian | Dónde |
|---|---|---|---|
| T-1 | «crackles» → «crépitos», como en R-4 (A-3) | 7, que hoy dicen «crepitaciones» | `/examination/Respiratory` de `acs_52m_de_winter`, `acs_66f_nonst`, `acs_70f_left_main`, `pneumonia_46f`, `pneumonia_83m`, `pulmonary_edema_58m` y `pulmonary_edema_75f` |
| T-2 | «guarding» → «defensa» | 2, que hoy dicen «resistencia muscular» | `/examination/Abdomen` de `acs_54m_inferior` y `pneumonia_46f` |
| T-3 | «confused» → «confundido» | 1, que hoy dice «confuso» | `/examination/Neurological` de `hypoglycemia_28m` |

- **Qué se aprueba:** cada caso que cambia (9 casos) se revisa en su lote con el término aprobado, y su aprobación
  lleva la versión de ese contenido.
- **Cuándo cambia el repositorio:** `case_text/es` cambia al implementar. Su versión tiene que coincidir entonces con
  la aprobada.
- **Corpus:** ninguno de estos 10 pasajes está entre los 18 que fija el corpus de la validación externa.

## 3. Resumen de decisiones del lote 0

| Grupo | Frases | Apariciones | Recomendación | Decisión docente |
|---|---|---|---|---|
| G1 · POCUS · venas (TVP) | L0-01 | 58 | APPROVE AS IS | ☐ |
| G2 · POCUS · corazón y pericardio | L0-02 a L0-07 | 72 | APPROVE AS IS | ☐ |
| G3 · POCUS · vena cava inferior | L0-08 a L0-12 | 13 | APPROVE AS IS | ☐ |
| G4 · POCUS · pulmón y pleura | L0-13 a L0-16 | 84 | APPROVE AS IS | ☐ |
| G5 · POCUS · aorta | L0-17 a L0-19 | 90 | APPROVE AS IS | ☐ |
| G6 · Laboratorio y microbiología | L0-20 a L0-23 | 90 | APPROVE AS IS | ☐ |
| G7 · Radiografía de tórax | L0-24 a L0-27 | 11 | APPROVE AS IS | ☐ |
| G8 · ECG · derivaciones adicionales | L0-28 y L0-29 | 12 | APPROVE AS IS | ☐ |
| G9 · Fuente de la historia | L0-30 a L0-32 | 23 | APPROVE AS IS | ☐ |
| G10 · Historia | L0-33 a L0-37 | 40 | APPROVE AS IS | ☐ |
| G11 · Examen físico | L0-38 a L0-47 | 34 | APPROVE AS IS | ☐ |
| **Total** | **47** | **527** | | |

Siguiente lote, según el orden docente: RUB (rúbrica D1–D5).
