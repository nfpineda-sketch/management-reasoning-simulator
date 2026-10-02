# PRE-PILOT HUMAN REVIEW PACKET

Revisión clínica y lingüística previa al primer piloto formativo. Fecha: 2026-10-02. Rama `clinical-encounter-v0.13`,
sobre `ad98005`. No es el ciclo 11.

> **Decidido y cerrado el 2026-10-02 (D-1 a D-11, TD-56 y TD-59).** Lo que se hizo, la tabla única de lo que espera su
> firma, los casos y los pendientes reales están en `docs/revision/CIERRE_PREPILOTO.md`. Este paquete queda como se
> presentó.

**Este paquete no aprueba ni cambia nada clínico.** Presenta el material; las decisiones son suyas. En esta fase sólo
se implementó un error de presentación determinista (regla B):

- el portal docente en español mostraba en inglés el tipo de cada evento crítico y sus decisiones («Not decided yet»,
  «Confirmed - applies the penalty»), aunque el catálogo ya tenía su traducción revisada;
- ahora pasan por ese catálogo (C-2026-10-02-01, con su prueba);
- no cambia qué se guarda ni la penalización.

Los hallazgos nuevos quedan en el registro de deuda como pendientes, sin corregir: TD-53 a TD-59
(`docs/REGISTRO_DEUDA_TECNICA.md`). No se abrió ninguna respuesta externa, no se desplegó nada y no se ejecutó la
prueba de humo.

**Clasificación usada:**

| Clase | Significa |
|---|---|
| **BLOCKER** | El caso o el flujo no puede entrar al piloto hasta decidir y corregir (o excluirlo) |
| **CONDITION** | El piloto puede correr si se cumple una condición: un aviso docente, un paso de despliegue o una regla de evaluación |
| **NON-BLOCKING DEBT** | Queda registrado; no afecta la seguridad clínica ni la evaluación del piloto |

**Qué observa un POCUS en texto:**

- **Sí observa:** la indicación (pedirlo y cuándo), la interpretación de hallazgos entregados por escrito, su
  integración en el manejo y la reevaluación.
- **No observa:** la adquisición, la destreza psicomotora ni el reconocimiento de imágenes.

---

## A. Resumen ejecutivo

1. **R-2:** de las 14 fichas POCUS, 10 son **CONFIRM**, 3 **MODIFY** y 1 **DISCUSS**.
   - **MODIFY:** los dos casos de trauma, por TD-48; y la redacción de la 52m.
   - **DISCUSS:** la 70f, porque su sobrecarga no se ve (TD-53).
   - El contenido POCUS escrito de los 14 es plausible y coherente entre ellos.
2. **BLOCKER 1 · TD-48 (trauma).**
   - Del E-FAST, la sala, el Trace y los documentos muestran sólo «Pericardium: No pericardial fluid».
   - Ninguna de las dos filas C14 de trauma puede cumplirse.
   - La 41m pierde su secuencia: drenar, volver a buscar y, sin otro sitio, pabellón.
   - Recomendación: corregirlo antes del piloto (opción A, de presentación).
3. **BLOCKER 2 · TD-50 (`anaphylaxis_29f`).**
   - Con la reacción ya resuelta, el examen sigue diciendo «audible inspiratory stridor».
   - Es información falsa justo donde C3 observa la reevaluación del estridor.
   - Recomendación: corregir el examen antes del piloto, o excluir la 29f.
   - En la 63m, la misma deuda es CONDITION.
4. **Fisiología de la TEP: KEEP FOR PILOT**, con condiciones.
   - En la 33f trombolizada, el sangrado no se detiene.
   - El ácido tranexámico no tiene efecto en esta familia, y la alteplasa no se puede suspender.
   - A los 180 min, la Hb es 6,7 g/dL con 115/73.
   - NEEDS SOURCE VERIFICATION antes de cualquier recalibración. No propongo ningún ajuste numérico.
5. **Español de la TEP:** las 7 notas son fieles. Propongo un cambio menor en todas: «administrada», la tilde, y el
   fármaco en español en las notas 6 y 7.
   - Señalo dos puntos: la glosa del shock omite la vía del vasopresor (es un tema del inglés), y el aviso del sangrado
     no tiene español.
6. **R-4:** 17 de las 18 frases, **APPROVE**; la fila 18, **MODIFY** (perdió su verbo).
7. **TD-49:** duplica la presentación y el registro, pero se ejecuta una sola vez. NON-BLOCKING.
8. **TD-51:** contradictoria al final de la vía sin tratamiento. NON-BLOCKING; se muestra el cambio mínimo.
9. **R-3:** en T-2, CONFIRM de C1 YES; T-3 y T-4 siguen NO. La C3 de la 29f sigue como PARCIAL documentada.
10. **R-5 y checklist:**
    - Las guías necesitan cambios: etiquetas en español, el paso de los eventos críticos (falta) y los avisos de foto y
      POCUS. R-5 no queda aprobado.
    - La checklist queda con 2 filas BLOCKED y una condición nueva de despliegue (TD-56): crear la cuenta docente que firmó
      las aprobaciones de fotos antes del primer encuentro, o reimportar el paquete de fotos.

---

## B. R-2

# R-2 POCUS HUMAN REVIEW PACKET

**Común a los 14 casos** (no se repite en cada ficha):

- **Disponibilidad y tiempo.** El POCUS se puede pedir desde el minuto 0 y tarda 2 min; el E-FAST tarda 4 min. El reloj
  corre mientras tanto.
- **Contenido del informe.** El informe da siempre el protocolo completo, los normales incluidos.
  - Campos: VI, VD, pericardio, VCI, deslizamiento pleural, líneas B, consolidación o derrame, raíz aórtica, aorta
    descendente, aorta abdominal, femoral y poplítea.
  - Normales típicos: RV "Smaller than the LV; no septal flattening (no D-sign); no McConnell sign"; pericardium "No
    pericardial effusion"; "Present bilaterally; no pneumothorax"; "No B-lines; A-line pattern bilaterally"; aorta "Not
    dilated"; "Compressible bilaterally".
- **Español.**
  - Hay borradores para todos los campos de los 14 casos; ninguno está aprobado (el repositorio no trae aprobaciones del
    relato).
  - En español, cada línea del POCUS o del E-FAST se ve entera en inglés (TD-46), hasta que el relato del caso se
    apruebe en la base desplegada.
- **ACEP.** Uso los rótulos de `docs/ACEP_POCUS_FRAMEWORK.md` (política ACEP de 2016): ESTABLISHED, PARCIAL o NOT
  ESTABLISHED BY THIS SOURCE. Este último no significa que esté prohibido.
  - La motilidad regional (decisión A) y el VD (tamaño, signo D y McConnell; decisión G) son SOURCE LIMITATION: usted ya
    los aprobó con el principio de alcance local.
- **Nunca observado:** la adquisición, la destreza, el reconocimiento de la imagen, la calidad de la ventana y los falsos
  negativos técnicos.
- **Coherencia interna de los 14:** sin contradicciones entre casos.
  - La misma lesión usa la misma palabra en todos.
  - La VCI pletórica se ve donde la presión venosa está alta (edemas y TEP) y colapsada donde falta volumen (HDA, sepsis
    y trauma).
  - Las respuestas dinámicas van en la misma dirección clínica.

| CASE | APPLICATION | C14 CURRENT | MAIN FINDING | RECOMMENDATION | ISSUE? |
|---|---|---|---|---|---|
| `acs_52m_de_winter` | Cardíaco, motilidad regional | YES · A | Akinesis of the anterior wall and apex | MODIFY (redacción, como la 61m) | Menor · NON-BLOCKING |
| `acs_61m_posterior` | Cardíaco, motilidad regional + aorta | YES · A · criterio R-2 aprobado | Hypokinesis of the posterior wall | CONFIRM | No |
| `acs_70f_left_main` | VI global + VCI + pulmón | YES · criterio R-2 aprobado | Globally mildly reduced contraction; scattered basal B-lines; IVC 1.9 cm | DISCUSS | Sí · la sobrecarga no se ve (TD-53) · CONDITION |
| `gi_bleed_57m` | VI + VCI (volumen) | YES · C | Small hyperdynamic LV; IVC 0.9 cm, near-complete collapse | CONFIRM | No |
| `gi_bleed_72f` | VI + VCI (volumen) | YES · C | Hyperdynamic LV; IVC 1.1 cm, >50% collapse | CONFIRM | No |
| `obstructive_pyelonephritis_58f` | VI + VCI (volumen) | YES · C (y H) | Vigorous LV; IVC 1.0 cm, >50% collapse | CONFIRM | Declarado · VCI de control estática (TD-54) · NON-BLOCKING |
| `pneumonia_46f` | VI + VCI; pulmón | YES · C (y F) | IVC 1.0 cm; right basal consolidation | CONFIRM | Menor · pulmón estático con sobrecarga (TD-54) |
| `pneumonia_83m` | VI + VCI; pulmón | YES · C (y F) | IVC 1.2 cm; left basal consolidation | CONFIRM (MODIFY opcional) | Menor · «air bronchograms» sin «dynamic» |
| `pulmonary_edema_58m` | Líneas B + VI + VCI | YES | Diffuse B-lines; moderately reduced LV; IVC 2.4 cm | CONFIRM | No |
| `pulmonary_edema_75f` | Líneas B + VI + VCI | YES | Diffuse B-lines; severely reduced LV; IVC 2.5 cm | CONFIRM | No |
| `pulmonary_embolism_33f` | VD + TVP | YES · G | RV mildly enlarged ≈ LV; popliteal non-compressible | CONFIRM | No |
| `pulmonary_embolism_61m` | VD + TVP | YES · G | RV > LV, D-sign, McConnell; popliteal non-compressible | CONFIRM | No |
| `trauma_hemothorax_41m` | E-FAST (+ POCUS) | YES | Fluid in the left pleural recess | MODIFY (TD-48) | **BLOCKER (TD-48)** |
| `trauma_limb_hemorrhage_27m` | E-FAST (+ POCUS) | YES | E-FAST negative in all windows | MODIFY (TD-48) | **BLOCKER (TD-48)** |

### 1 · `acs_52m_de_winter`

- **CASE ID:** `acs_52m_de_winter`
- **CLINICAL PROBLEM:** oclusión aguda de la descendente anterior con patrón de De Winter, un equivalente de IAM con
  supradesnivel del ST.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** a la llegada.
  - 128/78, FC 96, SpO₂ 95 %, FR 24, esfuerzo levemente aumentado, tibio y alerta.
  - 40 min de dolor torácico opresivo con sudoración.
- **POCUS APPLICATION:** cardíaco focalizado, con motilidad regional, dentro del protocolo completo.
- **CURRENT POCUS FINDING:** LV "Akinesis of the anterior wall and apex; the inferior wall contracts normally"; IVC
  "1.5 cm; about 50% inspiratory collapse". El resto, normal.
- **CURRENT SPANISH:** borrador, sin aprobar: «Acinesia de la pared anterior y del ápex; la pared inferior se contrae
  normalmente». En la sala se ve en inglés.
- **WHAT THE RESIDENT ACTUALLY SEES:** el informe completo.
  - Sin reperfusión, la pared sigue igual a los 60 min.
  - Reperfundida, queda aturdida y a lo sumo levemente disminuida (DF-23, fila 6).
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** una acinesia anterior y apical concordante con el ECG, que apoya leer el
  patrón como una oclusión.
- **EXPECTED MANAGEMENT CONSEQUENCE:** activar o acelerar la reperfusión. El POCUS no debe retrasarla.
- **C14 OBSERVABLE COMPONENT(S):** "Using regional wall motion to prioritise the reperfusion decision."
  - Evidencia: "requests POCUS and names the anterior akinesis"; "relates it to the ECG pattern as an occlusion";
    "activates or expedites reperfusion".
- **WHAT IS NOT OBSERVED:**
  - reconocer la acinesia en una imagen, porque el informe ya la escribe;
  - si el POCUS retrasaría la reperfusión en la práctica (aquí cuesta 2 min).
- **ACEP ALIGNMENT:** la motilidad regional es NOT ESTABLISHED, una SOURCE LIMITATION (decisión A, aprobada). El VI
  global, el pericardio y la VCI son ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** plausible. Una acinesia anterior y apical a los 40 min de una oclusión proximal es lo
  esperable. Sin líneas B y con SpO₂ normal es coherente.
- **POTENTIAL ISSUE:** es de redacción, no de contenido.
  - La evidencia todavía pide «names the anterior akinesis». La 61m ya dice que reconocer la motilidad no se exige,
    porque el informe la entrega. Aquí la acinesia no es sutil: nombrarla es leer el informe.
  - El ECG de De Winter basta para activar la reperfusión. La fila no dice que no usar POCUS no es un déficit, ni que el
    POCUS no debe retrasar la reperfusión.
- **RECOMMENDATION: MODIFY** (sólo redacción, alineada con el criterio aprobado de la 61m). NON-BLOCKING.
  - Evidencia propuesta: "requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion".
  - Agregar a la justificación: "The report states the wall motion; recognising it is not required. POCUS never delays
    reperfusion: activating it from the ECG alone is correct and is not a C14 deficit."

### 2 · `acs_61m_posterior`

- **CASE ID:** `acs_61m_posterior`
- **CLINICAL PROBLEM:** IAM posterior: depresión del ST en V1–V3, que las derivaciones posteriores aclaran. El dolor
  torácico y dorsal obliga a considerar una disección.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** a la llegada, 132/80, FC 88, SpO₂ 96 %. Opresión torácica y dorsal de
  2 h, con náuseas.
- **POCUS APPLICATION:** cardíaco (motilidad regional), raíz aórtica y aorta descendente.
- **CURRENT POCUS FINDING:**
  - LV "Hypokinesis of the posterior wall; the anterior and lateral walls contract normally";
  - IVC "1.6 cm; about 50% inspiratory collapse";
  - aortic root "Not dilated"; descending aorta "Not dilated in the visible segment".
- **CURRENT SPANISH:** borrador: «Hipocinesia de la pared posterior; las paredes anterior y lateral se contraen
  normalmente».
- **WHAT THE RESIDENT ACTUALLY SEES:** el informe completo. Sin reperfusión, a los 60 min: "The posterior wall shows
  moderately reduced contraction; the other walls contract normally".
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** la hipocinesia informada apoya, junto con el ECG y las derivaciones
  posteriores, una oclusión que el ECG de 12 derivaciones subestima. Una aorta no dilatada no descarta la disección.
- **EXPECTED MANAGEMENT CONSEQUENCE:** activar o acelerar la reperfusión.
- **C14 OBSERVABLE COMPONENT(S):** "Using the reported regional wall motion, with the ECG and the posterior leads, to
  prioritise the reperfusion decision." El criterio R-2 se aprobó el 2026-09-30: reconocerla no se exige, y la aorta no
  dilatada no descarta una disección.
- **WHAT IS NOT OBSERVED:** el reconocimiento de una alteración sutil (no se exige), y la exclusión de la disección (el
  POCUS no la hace).
- **ACEP ALIGNMENT:** la motilidad regional es NOT ESTABLISHED (SOURCE LIMITATION); la raíz y la aorta descendente son
  ESTABLISHED (dilatación).
- **CLINICAL PLAUSIBILITY:** plausible. "Posterior wall" es la nomenclatura antigua; la ASE la llama "inferolateral", y
  la antigua sigue siendo de uso común en urgencia. La evolución a los 60 min es coherente.
- **POTENTIAL ISSUE:** ninguno. Opcional: escribir "inferolateral (posterior)".
- **RECOMMENDATION: CONFIRM.**

### 3 · `acs_70f_left_main`

- **CASE ID:** `acs_70f_left_main`
- **CLINICAL PROBLEM:** isquemia de tronco o multivaso, con preshock cardiogénico.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 104/66, FC 112, SpO₂ 94 %, FR 26, llene capilar de 3 s, extremidades
  frías. Examen: "Mildly increased effort; scattered basal crackles."
- **POCUS APPLICATION:** VI global, VCI y pulmón.
- **CURRENT POCUS FINDING:**
  - LV "Globally mildly reduced contraction without a single focal defect";
  - IVC "1.9 cm; about 50% inspiratory collapse";
  - lungs "Scattered B-lines at both bases; no diffuse B-line pattern".
- **CURRENT SPANISH:** borradores:
  - «Contracción globalmente levemente disminuida sin un defecto focal único»;
  - «Líneas B dispersas en ambas bases; sin patrón difuso de líneas B»;
  - «1.9 cm; colapso inspiratorio de aproximadamente 50%».
- **WHAT THE RESIDENT ACTUALLY SEES:** a la llegada, lo anterior.
  - Después de 2000 mL, la presión deja de responder y aparece: "…mL of crystalloid is past what this ventricle is
    carrying: the pressure has stopped answering and the lungs are starting to. Reassess tolerance before the next
    bolus."
  - **La SpO₂, la FR, el examen y el POCUS no cambian.** El motor sube la congestión, pero la superficie del SCA no la
    lee (TD-53).
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** hallazgos intermedios. No hay una respuesta única: el volumen se decide
  con la función global a la vista.
- **EXPECTED MANAGEMENT CONSEQUENCE:** caben tres caminos, cada uno adaptado después a la respuesta y a la urgencia de la
  reperfusión:
  - retener el volumen;
  - dar un bolo pequeño, con su límite dicho, y reevaluarlo;
  - escalar el soporte.
- **C14 OBSERVABLE COMPONENT(S):** "Deciding volume, support and urgency with the global LV function in view, and
  adapting them to the response." Criterio R-2 aprobado: el bolo pequeño justificado y reevaluado no se penaliza por sí
  solo.
- **WHAT IS NOT OBSERVED:** la adquisición y la estimación cuantitativa.
- **ACEP ALIGNMENT:** el VI global, la VCI y las líneas B son ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** la llegada es plausible: la isquemia de tronco da hipocinesia global más que un defecto
  focal.
- **POTENTIAL ISSUE:** el criterio aprobado observa «adapts the plan to the response».
  - Quien reevalúa con POCUS o con el examen después de un exceso de volumen recibe información falsamente
    tranquilizadora: las mismas líneas B dispersas y la misma SpO₂.
  - Sólo la presión y el mensaje cuentan lo que pasó. CONDITION.
- **RECOMMENDATION: DISCUSS.** Recomiendo (a) para el piloto y (b) después de él:
  - **(a)** mantenerlo en el piloto, con aviso docente y una regla de evaluación: no penalizar a quien confió en un POCUS
    de control que no cambió;
  - **(b)** antes del piloto, que el pulmón del SCA lea la congestión (líneas B, examen y SpO₂), como en el edema
    pulmonar. Es un cambio clínico del motor.

### 4 · `gi_bleed_57m`

- **CASE ID:** `gi_bleed_57m`
- **CLINICAL PROBLEM:** hemorragia digestiva alta con shock hemorrágico.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 88/54, FC 124, llene capilar de 5 s.
- **POCUS APPLICATION:** VI y VCI (volumen).
- **CURRENT POCUS FINDING:** LV "Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole";
  IVC "0.9 cm; near-complete inspiratory collapse".
- **CURRENT SPANISH:** borradores: «Cavidad pequeña con contracción hiperdinámica; obliteración casi completa de la
  cavidad en sístole»; «0.9 cm; colapso inspiratorio casi completo».
- **WHAT THE RESIDENT ACTUALLY SEES:** después de 2 U, con 108/65: LV "Small cavity with hyperdynamic contraction; no
  obliteration in systole"; IVC "1.1 cm; >50% inspiratory collapse".
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** un VI vacío e hiperdinámico con la VCI colapsada: hipovolemia por
  sangrado.
- **EXPECTED MANAGEMENT CONSEQUENCE:** transfundir, controlar el sangrado (endoscopía) y reevaluar con POCUS.
- **C14 OBSERVABLE COMPONENT(S):** "Using the POCUS volume assessment to guide and reassess resuscitation."
  - Evidencia: "requests POCUS and names the empty, hyperdynamic LV and the collapsed IVC"; "relates them to transfusion
    or volume"; "reassesses with POCUS after resuscitation".
- **WHAT IS NOT OBSERVED:** la adquisición y la medición de la VCI.
- **ACEP ALIGNMENT:** ESTABLISHED (VI cualitativo, VCI, monitorización de la respuesta).
- **CLINICAL PLAUSIBILITY:** plausible; la respuesta a la sangre es coherente.
- **POTENTIAL ISSUE:** ninguno.
- **RECOMMENDATION: CONFIRM.**

### 5 · `gi_bleed_72f`

- **CASE ID:** `gi_bleed_72f`
- **CLINICAL PROBLEM:** hemorragia digestiva alta con hipotensión.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 98/62, FC 112, llene capilar de 4 s.
- **POCUS APPLICATION:** VI y VCI (volumen).
- **CURRENT POCUS FINDING:** LV "Hyperdynamic contraction"; IVC "1.1 cm; >50% inspiratory collapse".
- **CURRENT SPANISH:** borradores: «Contracción hiperdinámica»; «1.1 cm; colapso inspiratorio >50%».
- **WHAT THE RESIDENT ACTUALLY SEES:** después de 2 U, con 118/73: LV "Cavity of normal size with hyperdynamic
  contraction"; IVC "1.5 cm; about 50% inspiratory collapse".
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** un VI hiperdinámico con una VCI colapsable: falta volumen.
- **EXPECTED MANAGEMENT CONSEQUENCE:** transfusión, control del sangrado y reevaluación.
- **C14 OBSERVABLE COMPONENT(S):** el mismo de la 57m. Evidencia: "names the hyperdynamic LV and the collapsing IVC";
  "relates them to transfusion or volume"; "reassesses with POCUS after resuscitation".
- **WHAT IS NOT OBSERVED:** la adquisición.
- **ACEP ALIGNMENT:** ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** plausible.
- **POTENTIAL ISSUE:** ninguno.
- **RECOMMENDATION: CONFIRM.**

### 6 · `obstructive_pyelonephritis_58f`

- **CASE ID:** `obstructive_pyelonephritis_58f`
- **CLINICAL PROBLEM:** shock séptico por pielonefritis obstructiva. Necesita control del foco (descompresión),
  antibiótico, volumen y vasopresor.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 94/54, FC 118, llene capilar de 4 s.
- **POCUS APPLICATION:** VI y VCI (volumen). La ecografía renal es un estudio formal aparte (decisión H).
- **CURRENT POCUS FINDING:** LV "Preserved, vigorous contraction"; IVC "1.0 cm; >50% inspiratory collapse".
- **CURRENT SPANISH:** borradores: «Contracción conservada y vigorosa»; «1.0 cm; colapso inspiratorio >50%».
- **WHAT THE RESIDENT ACTUALLY SEES:** después de 2 L, con 111/63, la VCI sigue en "1.0 cm; >50% inspiratory collapse".
  El motor no modela su respuesta, y la fila C14 lo declara.
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** un VI vigoroso con una VCI pequeña y colapsable: es probable que
  responda al volumen.
- **EXPECTED MANAGEMENT CONSEQUENCE:** volumen con límite, vasopresor a tiempo y control del foco.
- **C14 OBSERVABLE COMPONENT(S):** "Guiding the fluid and haemodynamic strategy with POCUS in septic shock."
  - Evidencia: nombrar la VCI y el VI; dar, limitar o titular el volumen, o pasar a un vasopresor, por ellos.
  - No incluye la reevaluación, coherente con la limitación.
- **WHAT IS NOT OBSERVED:** la adquisición. Tampoco la hidronefrosis con POCUS: ACEP la incluye entre sus aplicaciones
  core (vía urinaria), pero aquí es un estudio formal.
- **ACEP ALIGNMENT:** el VI y la VCI son ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** la llegada es plausible. Una VCI que no cambia tras 2 L de shock séptico no es imposible,
  pero aquí la VCI no sigue al volumen.
- **POTENTIAL ISSUE:** el POCUS de control no cambia (TD-54). Ya está declarado. Puede empujar a dar más volumen, lo que en
  sepsis está dentro de lo aceptable. NON-BLOCKING, con una línea en la guía docente.
- **RECOMMENDATION: CONFIRM.**

### 7 · `pneumonia_46f`

- **CASE ID:** `pneumonia_46f`
- **CLINICAL PROBLEM:** neumonía basal derecha con shock séptico e hipoxemia.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 92/58, FC 118, SpO₂ 89 %, FR 30.
- **POCUS APPLICATION:** VI y VCI (volumen), y pulmón.
- **CURRENT POCUS FINDING:**
  - LV "Preserved, vigorous contraction";
  - IVC "1.0 cm; >50% inspiratory collapse";
  - lungs "Focal B-lines at the right base; no diffuse bilateral B-lines";
  - consolidation "Right basal subpleural consolidation with dynamic air bronchograms; no pleural effusion".
- **CURRENT SPANISH:** borrador, p. ej.: «Consolidación subpleural basal derecha con broncogramas aéreos dinámicos; sin
  derrame pleural».
- **WHAT THE RESIDENT ACTUALLY SEES:**
  - Desde 500 mL, la VCI mide 1,5 cm. Con 2 L: IVC "2.0 cm; <50% inspiratory collapse".
  - Con 6 L, la SpO₂ cae a 86 % y la paciente queda somnolienta, pero el pulmón y el examen no cambian: el motor de la
    neumonía no tiene sobrecarga por cristaloides.
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:**
  - una VCI pequeña con un VI vigoroso: dar volumen;
  - una VCI de 2,0 cm con poco colapso: es menos probable que responda; limitar o pasar a un vasopresor.
- **EXPECTED MANAGEMENT CONSEQUENCE:** volumen titulado y vasopresor a tiempo.
- **C14 OBSERVABLE COMPONENT(S):** "Guiding and reassessing the fluid and haemodynamic strategy with POCUS."
  - Evidencia: nombrar la VCI y el VI; actuar sobre el volumen por ellos; reevaluar con POCUS después del volumen.
- **WHAT IS NOT OBSERVED:** la adquisición, y las líneas B nuevas de una sobrecarga, que el motor no produce.
- **ACEP ALIGNMENT:** la VCI, el VI y las líneas B son ESTABLISHED. La consolidación es PARCIAL; por la decisión F, no
  crea la oportunidad.
- **CLINICAL PLAUSIBILITY:** plausible. El salto de 1,0 a 2,0 cm con 2 L es grande, pero posible.
- **POTENTIAL ISSUE:** el pulmón no muestra la sobrecarga (TD-54); la VCI y la SpO₂ sí la cuentan. NON-BLOCKING.
- **RECOMMENDATION: CONFIRM.**

### 8 · `pneumonia_83m`

- **CASE ID:** `pneumonia_83m`
- **CLINICAL PROBLEM:** neumonía basal izquierda con sepsis, en un adulto mayor derivado como «deshidratado». Es una
  trampa de anclaje.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 96/60, FC 108, SpO₂ 91 %, somnoliento.
- **POCUS APPLICATION:** VI y VCI (volumen), y pulmón.
- **CURRENT POCUS FINDING:**
  - LV "Preserved contraction";
  - IVC "1.2 cm; >50% inspiratory collapse";
  - lungs "Focal B-lines at the left base; no diffuse bilateral B-lines";
  - consolidation "Left basal consolidation with air bronchograms; no pleural effusion".
- **CURRENT SPANISH:** borrador, p. ej.: «Consolidación basal izquierda con broncogramas aéreos; sin derrame pleural».
- **WHAT THE RESIDENT ACTUALLY SEES:** con 1 L: IVC "1.5 cm; about 50% inspiratory collapse" (104/64). Con 2 L: "2.0 cm;
  <50% inspiratory collapse" (115/70).
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** lo mismo que en la 46f. Además, la consolidación desarma el anclaje en
  la deshidratación.
- **EXPECTED MANAGEMENT CONSEQUENCE:** volumen titulado, antibiótico y vasopresor si hace falta.
- **C14 OBSERVABLE COMPONENT(S):** el mismo de la 46f.
- **WHAT IS NOT OBSERVED:** la adquisición.
- **ACEP ALIGNMENT:** igual que en la 46f.
- **CLINICAL PLAUSIBILITY:** plausible.
- **POTENTIAL ISSUE:** dice "air bronchograms" sin "dynamic".
  - El broncograma dinámico distingue la neumonía de la atelectasia, y aquí la consolidación es la pista contra el
    anclaje.
  - No afecta C14 (decisión F).
- **RECOMMENDATION: CONFIRM.** MODIFY opcional: "…with dynamic air bronchograms…" (es texto del caso y pide su
  aprobación). NON-BLOCKING.

### 9 · `pulmonary_edema_58m`

- **CASE ID:** `pulmonary_edema_58m`
- **CLINICAL PROBLEM:** edema pulmonar agudo hipertensivo (SCAPE).
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 218/116, FC 126, SpO₂ 81 %, FR 38.
- **POCUS APPLICATION:** líneas B, VI y VCI.
- **CURRENT POCUS FINDING:** LV "Moderately reduced global contraction"; IVC "2.4 cm; <50% inspiratory collapse"; lungs
  "Diffuse bilateral B-lines in the anterior and lateral zones".
- **CURRENT SPANISH:** borradores: «Líneas B difusas bilaterales en las zonas anteriores y laterales»; «Contracción
  global moderadamente disminuida».
- **WHAT THE RESIDENT ACTUALLY SEES:** con tratamiento, el pulmón dice "Fewer but persistent…". Bajo presión positiva, la
  VCI dice "respiratory variation not assessable during positive-pressure support".
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** congestión: líneas B difusas, VI deprimido y VCI pletórica.
- **EXPECTED MANAGEMENT CONSEQUENCE:** nitrato, VNI y diurético; nunca volumen.
- **C14 OBSERVABLE COMPONENT(S):** "Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV
  and the IVC."
- **WHAT IS NOT OBSERVED:** la adquisición.
- **ACEP ALIGNMENT:** ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** plausible.
- **POTENTIAL ISSUE:** ninguno.
- **RECOMMENDATION: CONFIRM.**

### 10 · `pulmonary_edema_75f`

- **CASE ID:** `pulmonary_edema_75f`
- **CLINICAL PROBLEM:** insuficiencia cardíaca descompensada con FEVI muy reducida.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 164/92, FC 114, SpO₂ 84 %, FR 32. Llega con la vista neutral (P-07).
- **POCUS APPLICATION:** líneas B, VI y VCI.
- **CURRENT POCUS FINDING:**
  - LV "Severely reduced global contraction";
  - IVC "2.5 cm; minimal inspiratory collapse";
  - lungs "Diffuse bilateral B-lines in the anterior and lateral zones";
  - consolidation "No consolidation; small bilateral pleural effusions".
- **CURRENT SPANISH:** borradores: «Contracción global severamente disminuida»; «Sin consolidación; pequeños derrames
  pleurales bilaterales».
- **WHAT THE RESIDENT ACTUALLY SEES:** a los 45 min de CPAP y nitrato, el pulmón dice "Fewer but persistent…" y la VCI
  "respiratory variation not assessable during positive-pressure support".
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** lo mismo que en la 58m.
- **EXPECTED MANAGEMENT CONSEQUENCE:** lo mismo que en la 58m.
- **C14 OBSERVABLE COMPONENT(S):** el mismo de la 58m.
- **WHAT IS NOT OBSERVED:** la adquisición.
- **ACEP ALIGNMENT:** ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** plausible.
- **POTENTIAL ISSUE:** ninguno en el POCUS.
- **RECOMMENDATION: CONFIRM.**

### 11 · `pulmonary_embolism_33f`

- **CASE ID:** `pulmonary_embolism_33f`
- **CLINICAL PROBLEM:** TEP de riesgo intermedio en una paciente normotensa, 12 días después de una cirugía, con TVP
  proximal sintomática. No hay indicación de lisis, y el riesgo de sangrado está declarado.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 110/70, FC 124, SpO₂ 90 %, FR 30. Aumento de volumen de la pantorrilla
  del lado operado.
- **POCUS APPLICATION:** VD y TVP.
- **CURRENT POCUS FINDING:**
  - LV "Preserved contraction";
  - RV "Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign";
  - IVC "2.0 cm; <50% inspiratory collapse";
  - popliteal "Non-compressible on the operated (symptomatic) side, with echogenic intraluminal material; compressible
    on the other side".
- **CURRENT SPANISH:** borradores: «Levemente aumentado de tamaño, aproximadamente igual al VI; sin aplanamiento septal
  (sin signo D); sin signo de McConnell»; «No compresible en el lado operado (sintomático), con material ecogénico
  intraluminal; compresible en el otro lado».
- **WHAT THE RESIDENT ACTUALLY SEES:** los mismos hallazgos durante todo el encuentro.
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** la TVP proximal confirma la enfermedad tromboembólica antes del angioTC
  (20 min). Un VD sin shock no indica lisis.
- **EXPECTED MANAGEMENT CONSEQUENCE:** anticoagular, o dejarlo explícito mientras llega el angioTC, y no trombolizar.
- **C14 OBSERVABLE COMPONENT(S):** "Integrating the RV and a proximal DVT with the haemodynamic stability: anticoagulation
  before confirmation, and no thrombolysis."
- **WHAT IS NOT OBSERVED:** la adquisición y la maniobra de compresión.
- **ACEP ALIGNMENT:** la TVP es ESTABLISHED. El tamaño del VD y el signo D son NOT ESTABLISHED, una SOURCE LIMITATION
  (decisión G).
- **CLINICAL PLAUSIBILITY:** plausible. Una relación VD/VI cercana a 1, sin signo D y con una VCI algo pletórica, es
  coherente con un riesgo intermedio.
- **POTENTIAL ISSUE:** ninguno en el POCUS. La fisiología de la lisis va en la sección E.
- **RECOMMENDATION: CONFIRM.**

### 12 · `pulmonary_embolism_61m`

- **CASE ID:** `pulmonary_embolism_61m`
- **CLINICAL PROBLEM:** TEP de alto riesgo con shock obstructivo.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 86/54, FC 132, SpO₂ 88 %, llene capilar de 5 s. Ingurgitación yugular
  y aumento de volumen de la pantorrilla izquierda.
- **POCUS APPLICATION:** VD y TVP.
- **CURRENT POCUS FINDING:**
  - LV "Small, underfilled cavity with vigorous contraction";
  - RV "Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing
    (McConnell sign)";
  - IVC "2.3 cm; minimal inspiratory collapse";
  - popliteal "Left popliteal vein non-compressible; right popliteal vein compressible".
- **CURRENT SPANISH:** borradores: «Mayor que el VI; aplanamiento septal con VI en forma de D; contracción disminuida de
  la pared libre con preservación apical (signo de McConnell)»; «Vena poplítea izquierda no compresible; vena poplítea
  derecha compresible».
- **WHAT THE RESIDENT ACTUALLY SEES:** el POCUS es estático. A los 45 min de la lisis, el VD y la VCI siguen igual, con
  98/61.
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** una sobrecarga aguda del VD con TVP, en shock: TEP de alto riesgo.
- **EXPECTED MANAGEMENT CONSEQUENCE:** anticoagular y decidir la reperfusión sin esperar el angioTC.
- **C14 OBSERVABLE COMPONENT(S):** "Deciding reperfusion and anticoagulation from RV strain and a proximal DVT in shock."
- **WHAT IS NOT OBSERVED:** la adquisición y el reconocimiento del signo D en una imagen.
- **ACEP ALIGNMENT:** la TVP y la VCI son ESTABLISHED. El VD, el signo D y McConnell son NOT ESTABLISHED, una SOURCE
  LIMITATION (decisión G).
- **CLINICAL PLAUSIBILITY:** plausible. Que el VD no cambie a los 45 min de la lisis es realista: su mejoría tarda horas.
- **POTENTIAL ISSUE:** ninguno.
- **RECOMMENDATION: CONFIRM.**

### 13 · `trauma_hemothorax_41m`

- **CASE ID:** `trauma_hemothorax_41m`
- **CLINICAL PROBLEM:** trauma torácico cerrado por un choque a alta velocidad, con hemotórax izquierdo y shock
  hemorrágico.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 88/50, FC 126, SpO₂ 91 %, FR 28. Matidez y menor entrada de aire en
  la base izquierda.
- **POCUS APPLICATION:** el E-FAST con las cinco ventanas del protocolo docente; también el POCUS.
- **CURRENT POCUS FINDING:**
  - **E-FAST, 12 líneas escritas:** `luq_pleural` "Fluid in the left pleural recess". Las otras 11 son negativas, desde
    "No free fluid in the hepatorenal recess" hasta "Seashore sign bilaterally; comet tails seen".
  - **POCUS:**
    - "Left pleural effusion with echogenic contents; no consolidation";
    - LV "Vigorous contraction with near-obliteration in systole";
    - IVC "0.8 cm; complete inspiratory collapse".
- **CURRENT SPANISH:** borrador: «Líquido en el receso pleural izquierdo».
- **WHAT THE RESIDENT ACTUALLY SEES:**
  - **Con el E-FAST, sólo** "E-FAST: Performed at minute 4 · Pericardium: No pericardial fluid" (TD-48), en inglés y en
    español.
  - Con el POCUS, sí ve el derrame.
  - El E-FAST solo deja pasar 4 min: queda en 75/43, FC 136 y somnoliento.
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** un hemotórax izquierdo en un paciente en shock.
- **EXPECTED MANAGEMENT CONSEQUENCE:**
  - tubo pleural y transfusión;
  - si sigue inestable, volver a buscar otro sitio (E-FAST o radiografía de pelvis);
  - sin otro sitio, pabellón. El motor no tiene pabellón: el caso termina con ese destino.
- **C14 OBSERVABLE COMPONENT(S):** "Deciding the drain and its reassessment from the haemothorax on the E-FAST."
  - Evidencia: "requests the E-FAST and names the left haemothorax"; "places a chest tube because of it"; "reassesses
    after the drain with the E-FAST, a film or surgery".
- **WHAT IS NOT OBSERVED:** la adquisición de las ventanas y el reconocimiento del líquido. El orden de las ventanas sí se
  registra.
- **ACEP ALIGNMENT:** el E-FAST es ESTABLISHED (hemotórax, hemoperitoneo, neumotórax y pericardio).
- **CLINICAL PLAUSIBILITY:** el informe escrito es plausible y suficiente. Lo que la sala muestra, no.
- **POTENTIAL ISSUE:** **BLOCKER (TD-48).**
  - No se puede nombrar el hemotórax desde el E-FAST.
  - En el E-FAST de control tampoco se ve que el abdomen y la pelvis siguen negativos, que es el paso que lleva al
    pabellón.
  - Menores:
    - la VCI del POCUS de control no cambia (TD-54);
    - una transfusión escrita sin velocidad ni reevaluación avanza el reloj 30 min por unidad (TD-32, decidido): con
      4 U, 120 min, hasta 50/25.
- **RECOMMENDATION: MODIFY:** corregir TD-48 (sección F). El contenido escrito queda tal como está.

### 14 · `trauma_limb_hemorrhage_27m`

- **CASE ID:** `trauma_limb_hemorrhage_27m`
- **CLINICAL PROBLEM:** lesión por maquinaria en el muslo derecho, con hemorragia externa compresible y shock.
- **PATIENT STATE WHEN POCUS BECOMES AVAILABLE:** 96/54, FC 132; el apósito está empapado y la sangre escurre de la
  camilla.
- **POCUS APPLICATION:** E-FAST y POCUS.
- **CURRENT POCUS FINDING:**
  - **E-FAST:** las 12 líneas son negativas ("No free fluid in the hepatorenal recess", "No fluid in the left pleural
    recess", "No pericardial fluid", "Sliding present"…).
  - **POCUS:** IVC "0.7 cm; complete inspiratory collapse"; LV "Vigorous contraction with near-obliteration in systole".
- **CURRENT SPANISH:** hay borradores de las 12 líneas, p. ej. «Sin líquido libre en el receso hepatorrenal».
- **WHAT THE RESIDENT ACTUALLY SEES:**
  - Del E-FAST, sólo "E-FAST: Performed at minute 4 · Pericardium: No pericardial fluid" (TD-48).
  - Si el E-FAST va antes del torniquete, son 4 min más de sangrado: 70/40, FC 152, somnoliento.
  - Con torniquete y 2 U llega a 123/69. Un POCUS de control a 112/63 sigue mostrando la VCI en "0.7 cm; complete
    inspiratory collapse" (TD-54).
- **WHAT THE RESIDENT IS EXPECTED TO INTERPRET:** el E-FAST negativo en las cinco ventanas descarta una fuente cavitaria;
  el control va en la extremidad.
- **EXPECTED MANAGEMENT CONSEQUENCE:** el torniquete primero (la x de xABCDE). El E-FAST no debe retrasarlo.
- **C14 OBSERVABLE COMPONENT(S):** "Directing haemorrhage control with the absence of cavity bleeding on the E-FAST."
  - Evidencia: "requests the E-FAST and names it negative"; "keeps haemorrhage control on the limb rather than searching
    a cavity"; "states what would change that".
- **WHAT IS NOT OBSERVED:** la adquisición y el reconocimiento de la imagen.
- **ACEP ALIGNMENT:** el E-FAST es ESTABLISHED.
- **CLINICAL PLAUSIBILITY:** el informe escrito es plausible.
- **POTENTIAL ISSUE:** **BLOCKER (TD-48).**
  - Con una sola ventana a la vista, no se puede «nombrarlo negativo».
  - El propio protocolo docente dice que una ventana que falta en el informe es una ventana que nadie miró.
  - Menor: la VCI de control es estática (TD-54).
- **RECOMMENDATION: MODIFY:** corregir TD-48.

**Para la futura biblioteca POCUS** (sólo se registra; no se construye). Cada hallazgo debería llevar:

- el estado en que aparece: llegada, después del volumen, reperfusión o presión positiva;
- su regla dinámica, o la marca «estático por diseño» con su aviso al docente;
- su ventana y el orden del protocolo, con la regla «cardíaco primero» del E-FAST;
- su español aprobado, con la fecha;
- si se exige reconocerlo (la regla R-2 de la 61m);
- una ventana renal (hidronefrosis), hoy ausente del protocolo.

---

## C. R-4 · las 18 frases del motor

**Estado actual:**

- Ninguna se muestra en español en el panel de examen; se ven enteras en inglés, sin mezcla.
- Las filas 12 a 18 ya tienen su español en las entradas de la sala; las 12 a 14 y la 18 usan la terminología del
  2026-09-30.
- Si se aprueban, un cambio registrado las lleva a la sala y al panel.

**Columna «cuándo»:** «vista» significa que apareció en las corridas de ensayo; «en código» significa que sólo se alcanza
por esa vía.

**R4-01** · trauma 27m y 41m · vista · al final, si el sangrado nunca se controló y el paciente cae en paro.

- EN: "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume replaces a
  source that is still open."
- ES: «Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido; la reposición de volumen no
  sustituye el control del sangrado activo.»
- Significado: el paro es la consecuencia de no controlar la fuente, que el volumen no reemplaza.
- Ambigüedad: «no se había detenido» admite que no cesó solo; el inglés implica que nadie lo detuvo. Alternativa
  opcional: «no se había controlado», a costa de repetir «control».
- **APPROVE.**

**R4-02** · `pulmonary_edema_75f` · vista · examen antes de tratar.

- EN: "Bilateral inspiratory crackles with increased respiratory effort."
- ES: «Crépitos inspiratorios bilaterales, con aumento del esfuerzo respiratorio.»
- Significado: congestión con trabajo respiratorio aumentado.
- Ambigüedad: ninguna en español. El motor la mantiene aunque el paciente esté agotado (TD-51, sección I).
- **APPROVE.**

**R4-03** · edema pulmonar · en código · mejoría con el tratamiento.

- EN: "Bilateral crackles remain, with reduced respiratory effort."
- ES: «Persisten crépitos bilaterales, con menor esfuerzo respiratorio.»
- Significado: mejoría parcial.
- Ambigüedad: ninguna, mientras el motor la escriba sólo con la congestión en mejoría. Una prueba lo verifica.
- **APPROVE.**

**R4-04** · cualquier familia · en código · sobrecarga circulatoria por transfusión.

- EN: "New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze."
- ES: «Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin sibilancias.»
- Significado: sobrecarga por transfusión, distinta del broncoespasmo.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-05** · asma · en código · respuesta a broncodilatadores.

- EN: "Improved air entry with residual expiratory wheeze."
- ES: «Mejor entrada de aire, con sibilancias espiratorias residuales.»
- Significado: mejoría.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-06** · asma · en código · a la llegada o sin respuesta.

- EN: "Reduced bilateral air entry with prolonged expiration and wheeze."
- ES: «Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias.»
- Significado: obstrucción grave.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-07** · asma con neumotórax · en código.

- EN: "Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side."
- ES: «Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado.»
- Significado: neumotórax que hay que descomprimir.
- Ambigüedad: ninguna. Opcional: «en el hemitórax contralateral».
- **APPROVE.**

**R4-08** · asma · en código · después de la descompresión.

- EN: "Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze."
- ES: «Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de aire, con
  sibilancias espiratorias residuales.»
- Significado: la descompresión funcionó.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-09** · opioides · en código · durante la ventilación con bolsa y mascarilla o la intubación.

- EN: "Respiratory rate {n} /min; assisted ventilation is in progress."
- ES: «Frecuencia respiratoria {n}/min, dada por la ventilación asistida en curso.»
- Significado: la frecuencia mostrada (fija en 12/min) es la de la ventilación asistida, no la espontánea.
- Ambigüedad: el español es más preciso que el inglés y fiel al motor. El inglés no lo dice (TD-52a).
- **APPROVE** el español. Corregir el inglés después: NON-BLOCKING.

**R4-10** · opioides · en código · hipoventilación persistente.

- EN: "Respiratory rate {n} /min; breaths remain shallow."
- ES: «Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales.»
- Significado: no hubo respuesta suficiente.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-11** · opioides · en código · respuesta a la naloxona.

- EN: "Respiratory rate {n} /min; spontaneous breaths have greater depth."
- ES: «Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas.»
- Significado: hubo respuesta.
- Ambigüedad: «más profundas» se lee respecto del examen anterior.
- **APPROVE.**

**R4-12** · `hypoglycemia_54m_thiamine` · vista · la vía de llegada, infiltrada antes de usarla (la pista).

- EN: "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool."
- ES: «Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de
  volumen y fría.»
- Significado: está infiltrada; no sirve para glucosa hipertónica.
- Ambigüedad: ninguna clínica. De estilo, es más natural: «con leve aumento de volumen y frialdad alrededor del extremo
  del catéter».
- **APPROVE.** La alternativa es opcional; la sala ya usa la frase actual.

**R4-13** · hipoglicemia · en código · la vía que funciona.

- EN: "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness."
- ES: «Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la
  palpación.»
- Significado: una vía utilizable.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-14** · hipoglicemia · en código · extravasación después de pasar la glucosa.

- EN: "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender."
- ES: «Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y
  doloroso a la palpación.»
- Significado: la glucosa no llegó a la circulación y dañó el tejido.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-15** · hipoglicemia · en código · la vía nueva.

- EN: "A second peripheral cannula in the right forearm; the site is clean."
- ES: «Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio.»
- Significado: un acceso nuevo, utilizable.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-16** · hipoglicemia · en código · acceso intraóseo (también tibial, esternal o femoral).

- EN: "An intraosseous needle in place (humeral)."
- ES: «Una aguja intraósea instalada (humeral).»
- Significado: un acceso IO.
- Ambigüedad: ninguna; «colocada» también serviría.
- **APPROVE.**

**R4-17** · hipoglicemia · en código · IO sin sitio registrado.

- EN: "An intraosseous needle in place; no site was recorded."
- ES: «Una aguja intraósea instalada; no se registró el sitio.»
- Significado: hay un acceso; el registro no dice dónde.
- Ambigüedad: ninguna.
- **APPROVE.**

**R4-18** · hipoglicemia · en código · la infusión de glucosa en curso.

- EN: "Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm."
- ES: «Suero glucosado al {n} % a {n} mL/h por la cánula del antebrazo izquierdo.»
- Significado: un estado: la infusión está pasando.
- Ambigüedad: sin verbo, puede leerse como una indicación en vez de un estado. La línea activa de la sala decía «La
  glucosa al 10 % pasa a…» y perdió el verbo al cambiar a «suero glucosado» el 2026-09-30.
- **MODIFY:** «El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo.» Corregir también la
  línea activa de la sala.

---

## D. Español de la TEP · las 7 notas nuevas

> **Lo que puede alterar la interpretación clínica:**
>
> 1. **Definición de shock (nota 1, en inglés y en español):** la glosa «a hypotension with signs of hypoperfusion»
>    omite la vía del vasopresor. El criterio del motor (`CRITERION_TEXT`) es: sistólica < 90, o un vasopresor
>    necesario para llegar a 90 pese a un llenado adecuado, con signos de hipoperfusión. Si el shock se reconoce con un
>    vasopresor andando, el monitor muestra 90 o más y la nota dice «una hipotensión».
> 2. **Indicación de la trombólisis (notas 1 a 5):** sin «administrada», «Trombolisis sistémica sin la indicación
>    hemodinámica…» puede leerse como un juicio o un consejo, no como el registro del acto.
> 3. **Interpretación del sangrado:** el aviso del sangrado de la 33f no está entre las 7 y **no tiene español**: se ve
>    entero en inglés. La nota 7 declara correctamente que un segundo curso no tiene sangrado propio en el simulador.
> 4. **Reevaluación:** «lo que cambie se ve al reevaluar» es fiel. KEEP.
> 5. **Evento crítico:** ninguna nota nombra un evento ni cambia su tamizaje.

**Cambios comunes a las 7:**

- agregar «administrada»;
- escribir «Trombólisis» con tilde, como el tamizaje y C14. Hoy la sala escribe «Trombolisis» 13 veces, notas antiguas
  incluidas.

| # | English | Español actual | Propósito clínico | Recomendación |
|---|---|---|---|---|
| 1 | "Systemic thrombolysis given in obstructive shock, a hypotension with signs of hypoperfusion. The drug acts on the clot over about half an hour; what it changes is seen on reassessment." | «Trombolisis sistémica en shock obstructivo, una hipotensión con signos de hipoperfusión. El fármaco actúa sobre el trombo durante cerca de media hora; lo que cambie se ve al reevaluar.» | Registra la dosis indicada y su fundamento; la mejoría se juzga al reevaluar | **MODIFY:** «Trombólisis sistémica **administrada** en shock obstructivo…». La glosa es una decisión aparte (D-4) |
| 2 | "Systemic thrombolysis given for sustained hypotension (15 consecutive minutes). The drug acts…" | «Trombolisis sistémica por hipotensión sostenida (15 minutos consecutivos). El fármaco actúa…» | Lo mismo, con el fundamento de la hipotensión sostenida | **MODIFY:** «Trombólisis sistémica **administrada** por hipotensión sostenida…» |
| 3 | "Systemic thrombolysis given without the hemodynamic indication: systolic {n} mmHg with no sign of hypoperfusion, low for {m} of the 15 consecutive minutes a hypotension without them requires. The drug acts on the clot whether or not it was indicated, and its bleeding risk is taken without the indication; what it changes is seen on reassessment." | «Trombolisis sistémica sin la indicación hemodinámica: sistólica de {n} mmHg sin signos de hipoperfusión, baja durante {m} de los 15 minutos consecutivos que exige una hipotensión sin ellos. El fármaco actúa sobre el trombo esté o no indicado, y su riesgo de sangrado se asume sin la indicación; lo que cambie se ve al reevaluar.» | Registra una lisis no indicada y por qué, con el estado de su minuto | **MODIFY:** «Trombólisis sistémica **administrada** sin la indicación hemodinámica: …» |
| 4 | "…systolic {n} mmHg on a vasopressor the pressure does not need, with no hypotension from the embolism. The drug acts…" | «…sistólica de {n} mmHg con un vasopresor que la presión no necesita, sin hipotensión por la embolia. El fármaco actúa…» | Lo mismo, con un vasopresor innecesario | **MODIFY:** como la 3 |
| 5 | "…systolic {n} mmHg, with no hypotension from the embolism. The drug acts…" | «…sistólica de {n} mmHg, sin hipotensión por la embolia. El fármaco actúa…» | Lo mismo, en un paciente normotenso | **MODIFY:** como la 3 |
| 6 | "alteplase 50 mg recorded as part of the initial regimen begun at minute {t} (100 mg in all). It completes the first dose rather than starting a new one, and the first dose keeps acting as before." (el fármaco, tal como lo escribe el residente) | «alteplase 50 mg registrado como parte del esquema inicial comenzado en el minuto {t} (100 mg en total). Completa la primera dosis…» | Separa el resto del esquema de alteplasa de un segundo curso | **MODIFY:** el fármaco en español, con mayúscula y concordancia: «Alteplasa 50 mg registrada como parte del esquema inicial…». Hoy pasa «alteplase» en inglés |
| 7 | "A second course of systemic thrombolysis is recorded ({alteplase 100 mg}); the first course began at minute {t}. Its added bleeding risk is recorded as exposure. This simulator represents neither additional reperfusion from a second course nor any bleeding of its own; that is a simplification, not evidence that repeating has no effect. The first dose keeps acting as before." | «Se registra un segundo curso de trombolisis sistémica (alteplase 100 mg); el primero comenzó en el minuto {t}. Su riesgo adicional de sangrado queda registrado como exposición. Este simulador no representa una reperfusión adicional por un segundo curso ni un sangrado propio; es una simplificación, no evidencia de que repetir no tenga efecto. La primera dosis sigue actuando como antes.» | Registra la exposición adicional y declara la simplificación | **MODIFY:** tilde y fármaco en español («alteplasa 100 mg»). El resto queda igual |

**Aviso del sangrado de la 33f** (sin español hoy). Borrador para su revisión, sin implementar:

- EN: "Bleeding from the surgical site operated on twelve days ago: the haemoglobin is falling. This is the risk the
  thrombolytic carries, and it was taken in a patient who had a reason to bleed."
- ES propuesto: «Sangrado del sitio quirúrgico (cirugía de hace doce días): la hemoglobina está bajando. Es el riesgo que
  conlleva el trombolítico, y se asumió en una persona que tenía un motivo para sangrar.»

---

## E. Brief de fisiología de la TEP

**Modelo actual** (`pe_obstruction.py`, `INDICATION_VERSION = 3`; reglas en `docs/PULMONARY_EMBOLISM_MAGNITUDES.md`):

- **Disolución.** Cualquier primera dosis disuelve la parte embólica de la obstrucción, indicada o no.
  - Empieza a los 5 min, con una constante de 30 min, y va hacia 0,62.
  - Lo que eso cambia en el paciente depende de todo lo demás.
- **Pérdida oculta.** Tras cualquier dosis, la Hb baja 0,006 g/dL por minuto (unos 0,36 g/dL por hora).
  - Sólo se ve en el laboratorio, no tiene costo hemodinámico y no se detiene.
  - Viene de una decisión docente del 2026-09-20, mantenida en P-04 B.
- **Sangrado mayor.** Sólo ocurre si el caso declara `lysis_bleeding_risk`; hoy, la 33f, operada hace 12 días.
  - Empieza en el minuto 20 tras la dosis: −0,03 g/dL por minuto de Hb y +0,0015 de circulación por minuto.
  - Al empezar, la sala muestra un aviso. **No se detiene.**
- **Presión y frecuencia.** PAS = basal − (circulación − 1) × 45; FC + (circulación − 1) × 25.
- **Qué puede hacer el residente ante el sangrado** (sondas del 2026-10-02):
  - transfundir: sube la Hb unos 0,85 g/dL por unidad, a 30 min cada una;
  - ácido tranexámico: se registra, sin efecto en esta familia (sólo el trauma lo lee);
  - «Stop alteplase»: se rechaza con «This fixed-dose medication order needs an explicit new dose; stopping it is not a
    supported new administration.»;
  - «Stop the alteplase infusion»: responde «No infusion is running…»;
  - crioprecipitado: se registra sin efecto; el fibrinógeno no se reconoce;
  - la interconsulta a cirugía se registra.

**Qué está garantizado** (el motor es determinista):

- la pérdida oculta con toda dosis;
- en la 33f, el sangrado mayor desde el minuto 20, con tasas fijas;
- la disolución;
- el juicio de la indicación con el estado del minuto de la orden;
- los textos.

**Qué es estocástico o condicional:**

- nada es estocástico en esta familia;
- el sangrado mayor depende de que el caso lo declare;
- su efecto en la presión depende de lo que actúe en el mismo minuto (disolución, vasopresor, volumen). Por eso el aviso
  sólo dice que la Hb cae.

**Plausibilidad clínica.** La dirección es plausible y verificada (`docs/VERIFICACION_P04_P05.md`):

- en el riesgo intermedio, la lisis mejora la hemodinamia y sangra más (PEITHO, ESC 2019);
- que la 33f sangre con certeza es una decisión docente: el caso declara un motivo para sangrar.

**Por qué cae la Hb** (33f con lisis sola):

| Minuto | Presión | FC | Hb (g/dL) |
|---|---|---|---|
| 25 | 117/74 | 120 | 12,3 |
| 65 | 121/76 | 118 | 10,8 |
| 105 | 119/75 | 119 | 9,4 |
| 180 | 115/73 | 121 | 6,7 |

- Sin tratamiento, a los 105 min la Hb es 12,6.
- A los 105 min, de lo perdido, 0,63 g/dL es la pérdida oculta y 2,55 el sangrado mayor.

**Por qué sube la presión.**

- La disolución devuelve la parte embólica de la circulación: unos +20 mmHg frente a no tratar (119/75 frente a 105/67 a
  los 105 min).
- El costo del sangrado es chico y la disolución no lo compensa, porque sólo actúa sobre la parte embólica: −6 mmHg y
  +3 lpm a los 105 min; unos −11 mmHg a los 180 min.

**Coherencia interna: débil en los extremos.**

- Una caída de 5,9 g/dL de Hb (de 12,6 a 6,7) con 115/73 no es coherente: una pérdida así, una vez diluida, corresponde a
  una hemorragia mayor con hipotensión.
- La tasa de la Hb (0,03 por minuto) y la de la circulación (0,0015 por minuto) no están acopladas fisiológicamente.
- El motor trata la Hb como un marcador inmediato de la pérdida.

**Qué necesita evidencia antes de recalibrar** (NEEDS SOURCE VERIFICATION, después del piloto):

1. la relación entre la caída de la Hb y su costo circulatorio;
2. si se mantiene la pérdida oculta con toda dosis (decisión del 2026-09-20), además del riesgo que declara cada caso;
3. cuánto dura el sangrado tras la lisis, y el efecto de suspender la infusión, del antifibrinolítico, del crioprecipitado
   y de la hemostasia local;
4. el inicio en el minuto 20.

**Clasificación y recomendación: KEEP FOR PILOT** (CONDITION).

- Lisar a la 33f ya es un camino de error, y su enseñanza principal se conserva: el aviso del minuto 20 y la Hb que cae.
- Condición: la guía docente debe decir lo siguiente.
  - La presión puede tranquilizar mientras la Hb cae.
  - El sangrado no se detiene, el ácido tranexámico no tiene efecto y la alteplasa no se puede suspender en la sala.
  - Lo que el residente intentó queda en el Trace; juzgue la respuesta al sangrado con el registro.
- Sin ajuste numérico.

---

## F. TD-48 · el E-FAST

**Caso:** `trauma_hemothorax_41m`, y también `trauma_limb_hemorrhage_27m`.

**Por qué se pide:** en un trauma en shock, para buscar hemoperitoneo, hemotórax, neumotórax y líquido pericárdico.

- En la 41m decide el drenaje, y después la nueva búsqueda tras drenar, que lleva al pabellón.
- En la 27m descarta una fuente cavitaria y deja el control en la extremidad.

**Qué muestra hoy:** «E-FAST: Performed at minute 4 · Pericardium: No pericardial fluid». Se ve así:

- en la sala, en el Trace y en los documentos;
- en inglés, y también en español, porque la línea se mantiene entera por TD-46.

La causa: `family_reports.format_result` no tiene una rama para el E-FAST, y su ruta genérica sólo conoce el campo
`pericardium`.

**Qué falta:** 11 de las 12 líneas.

- En la 41m, «Fluid in the left pleural recess».
- En los dos casos, el abdomen, la pelvis y el pulmón negativos.

**¿Importa para el manejo?** Sí:

- en la 41m, para decidir el tubo pleural, y para ver en el control que no hay otro sitio antes del pabellón;
- en la 27m, para afirmar que no hay fuente cavitaria.

**¿Depende C14 de esto?** Sí.

- Depende el primer ítem de evidencia de las dos filas: «names the left haemothorax» y «names it negative».
- Además, la D2 de trauma afirma "The E-FAST reports all five windows".
- El evento `trauma_drained_and_never_looked_again` cuenta el pedido del control, no su lectura.

**Qué debe informar un E-FAST de urgencia:** las cinco ventanas, cada una positiva o negativa. Un hallazgo positivo se
describe por su sitio; el volumen o la ecogenicidad son opcionales. Es el protocolo docente (`efast_report.SECTIONS`), y
el contenido escrito de los dos casos ya lo cumple.

**Opciones:**

- **A (recomendada):** una rama del E-FAST que muestre las cinco ventanas en el orden del protocolo, como `format_pocus`.
  Vale para la sala, el Trace y los documentos.
- **B:** sólo las ventanas positivas, más «todas las demás, negativas». Es más corta, pero contradice el principio
  docente de que se informa cada ventana.
- **C:** dejarlo como está y excluir los casos de trauma, o avisar al docente. No la recomiendo.

**Recomendación:** A, antes del piloto. Clasificación: BLOCKER para los dos casos de trauma. Dos notas:

- **Trace.** El Trace vuelve a dibujar el resultado guardado. Un encuentro registrado antes de la corrección mostraría las
  cinco ventanas que el residente no vio. No hay encuentros del piloto, sólo de ensayo: queda documentado.
- **Español.** Las líneas del caso se ven enteras en inglés hasta que se apruebe el relato (TD-46). Los títulos de las
  ventanas no tienen español en el catálogo. Propongo, pendiente de su aprobación:
  - las ventanas: CUADRANTE SUPERIOR DERECHO · CUADRANTE SUPERIOR IZQUIERDO · SUPRAPÚBICA · SUBXIFOIDEA · PULMÓN;
  - los campos:
    - Espacio de Morison (hepatorrenal) · Espacio subdiafragmático derecho · Receso pleural derecho;
    - Espacio esplenorrenal · Espacio subdiafragmático izquierdo · Receso pleural izquierdo;
    - Vista longitudinal · Vista transversal;
    - Pericardio;
    - Deslizamiento pulmonar derecho · Deslizamiento pulmonar izquierdo · Modo M.

**BEFORE** (41m, sala y Trace, en inglés y en español):

```
E-FAST: Performed at minute 4 · Pericardium: No pericardial fluid
```

**AFTER** (opción A, en inglés; no implementado):

```
E-FAST · performed at minute 4
RIGHT UPPER QUADRANT
· Morison's pouch (hepatorenal): No free fluid in the hepatorenal recess
· Right subdiaphragmatic space: No free fluid above the liver
· Right pleural recess: No fluid in the right pleural recess
LEFT UPPER QUADRANT
· Splenorenal space: No free fluid in the splenorenal recess
· Left subdiaphragmatic space: No free fluid above the spleen
· Left pleural recess: Fluid in the left pleural recess
SUPRAPUBIC
· Longitudinal view: No free fluid behind or around the bladder
· Transverse view: No free fluid behind or around the bladder
SUBXIPHOID
· Pericardium: No pericardial fluid
LUNG
· Right lung sliding: Sliding present
· Left lung sliding: Sliding present
· M-mode: Seashore sign bilaterally; comet tails seen
```

**NO CORREGIDO.**

---

## G. TD-49 · la trombólisis del SCA, duplicada

**Dónde ocurre:**

| Capa | ¿Duplica? | Evidencia (52m y 66f) |
|---|---|---|
| Presentación (sala) | **Sí** | «Current treatments» muestra dos veces «tenecteplase 40 mg IV · minute 0» |
| Trace | **Sí, en el estado guardado** | `state_after` lleva las dos filas. `concurrent_treatments` se escribe en app.py:843 y nada lo lee |
| Ejecución | No | `acs_reperfusion.activate` es idempotente: la reperfusión se registra una vez |
| Fisiología | No | La reperfusión queda en el minuto 60, con una o con dos órdenes |
| Rúbrica | No | El SCA no tiene un evento crítico de lisis |
| Tamizaje | No | No hay eventos de lisis del SCA |

Una segunda orden deja 4 filas, sin un aviso de repetición, y la reperfusión no cambia.

- **Causa:** la rama del SCA agrega su propia fila, y la ruta genérica de medicamentos agrega otra. Es lo mismo que pasaba
  en la TEP hasta C-2026-09-30-07.
- **Corrección:** una línea, igual que en la TEP.
- **Clasificación:** NON-BLOCKING DEBT. No es una regresión del trabajo reciente.
- **No corregido.**

---

## H. TD-50 · el examen estático de la anafilaxia

**1. Casos afectados:** los dos de la familia.

- `anaphylaxis_29f`, que tiene C3 YES (parcial).
- `anaphylaxis_63m_betablocked`, que tiene C3 NO.

**2. Hallazgos estáticos:**

- Las regiones Respiratory, Cardiac y Abdomen muestran la línea que escribió el caso y no evolucionan. La única excepción
  es el tubo endotraqueal (TD-47).
- «General appearance» nunca muestra la línea del caso: la sala la reemplaza por el resumen del motor (TD-59, desde el
  2026-09-21).
  - Quedan fuera la urticaria y el edema de labios y párpados de la 29f, y la picadura de la 63m.
  - La presentación sí dice lo esencial: «a spreading rash, a swollen face and noisy breathing»; «flushed, wheezing…
    Handover notes a sting and a rash».

**3. Variables que evolucionan:** la reacción, la SpO₂, la presión, la FC, la FR, el esfuerzo, el estado mental, el llene
capilar, la bandera del estridor y el resumen del aspecto.

**4. ¿La sala afirma estridor cuando el caso no lo escribió?** No: en la 63m, el examen dice «no stridor heard». Pero el
motor sí lo cobra, oculto.

- En la 63m, la reacción de llegada (1,18) supera el umbral (0,80).
- Desde el minuto 1, el motor cobra el estridor: −6 de SpO₂ y un esfuerzo de al menos 1,5.
- Ningún texto lo dice.

**5. Qué queda tras intubar** (TD-47, corregido): «Endotracheal tube in place: no stridor through the tube; widespread
expiratory wheeze.» La reacción, el broncoespasmo y el shock siguen; el tubo no los resuelve.

**6. Clase del problema:**

| Caso y hallazgo | Evidencia | Clase | Clasificación |
|---|---|---|---|
| **29f · el estridor no se va** | Dos dosis de adrenalina IM con oxígeno; a los 31 min: 125/69, SpO₂ 99 %, alerta, reacción 0,00 y bandera falsa. El examen sigue: «Increased effort with widespread expiratory wheeze and audible inspiratory stridor.» | Información clínica falsa, que puede cambiar el manejo (intubar sin necesidad). **Evidencia falsa de C3:** quien reevalúa el estridor, justo lo que C3 observa, lo encuentra persistente. **Distorsión del Trace:** registra fielmente un examen falso | **BLOCKER** para la 29f |
| **Ambos · doble cobro al llegar** | La reacción vale 0 a la llegada y toma la gravedad del caso en el minuto 1; el −6 absoluto se suma a una llegada que ya incluía el estridor. 29f: SpO₂ 91 → 85 y de alerta a somnolienta en el minuto 1. 63m: 89 → 83 | Discontinuidad fisiológica: un deterioro brusco antes de que el residente actúe | **CONDITION** |
| **63m · el estridor oculto** | Lo descrito en el punto 4. Además, tras dos dosis de adrenalina, el esfuerzo dice «Exhausted: shallow and ineffective effort» mientras el examen sigue «Increased effort with widespread wheeze; no stridor heard.» | Fisiología oculta y una contradicción entre regiones. No es evidencia de C3 (C3 NO) | **CONDITION** |

**Opciones** (texto clínico pendiente de aprobación; no implementadas):

1. El examen respiratorio sigue al motor, sin umbrales nuevos. Usa la bandera del estridor, que ya existe (0,80), y la
   reacción en 0.
   - Con estridor: la línea del caso.
   - Sin estridor y con reacción > 0: «Increased effort with widespread expiratory wheeze; no stridor heard now.»
   - Con reacción en 0: «Mildly increased effort; no wheeze or stridor now.»
2. El cobro del estridor se vuelve relativo a la llegada: sólo cuesta el aumento sobre la gravedad declarada. Es
   estructural, no un ajuste numérico.
3. Que cada caso declare si tiene compromiso de la vía aérea alta. La 63m no lo tiene: sin cobro oculto.

**Recomendación:** la opción 1 antes del piloto; si no, excluir la 29f. Las opciones 2 y 3, antes del piloto si usted lo
aprueba; si no, quedan como condición con aviso docente.

---

## I. TD-51 · el esfuerzo en el edema pulmonar

**Clasificación: B (contradictorio)** en el texto. En la fisiología tardía es en parte A y en parte C.

**Fisiología reconstruida** (58m y 75f sin tratamiento):

- La carga respiratoria supera 1,25 desde el minuto 84, y el esfuerzo pasa a «Exhausted: shallow and ineffective
  effort» desde el minuto 109.
- La FR sigue subiendo (44 y 38), la SpO₂ cae a 75 y 78 %, y el paciente queda obnubilado.
- La presión y la FC quedan planas durante 2 h.
- El examen sigue: «Bilateral inspiratory crackles with increased respiratory effort.»
- Qué es compatible y qué no:
  - **A, compatible:** la respiración rápida y superficial antes del paro.
  - **B, contradictorio:** la región Respiratory contradice la del esfuerzo.
  - **C, poco granular:** el examen tiene sólo dos estados, y la presión y la FC no responden a la hipoxemia y al
    agotamiento.

**Cambio mínimo** (no implementado): un tercer estado del examen, sólo cuando el esfuerzo es «Exhausted».

- EN: "Bilateral inspiratory crackles; the effort is now shallow and ineffective."
- ES: «Crépitos inspiratorios bilaterales; el esfuerzo es ahora superficial e ineficaz.» (Requiere aprobación R-4.)
- La presión y la FC planas quedan para una revisión con fuentes; sin ajuste.

**Clasificación: NON-BLOCKING.** Sólo aparece después de unos 109 min sin ningún tratamiento, cuando los eventos críticos
ya se dispararon.

**TD-52 y otros menores:** sólo se listan y quedan diferidos.

- (a) el inglés de la frecuencia asistida (R4-09);
- (b) el aviso del sangrado sin español (sección D);
- (c) la etiqueta «given started over 120 min»;
- (d) «Repeat alteplase 100 mg IV» rechazado por el lector;
- el texto del riesgo `severe_hypertension` («Bleeding from an uncontrolled arterial pressure»), que el banco no usa;
- `searched_again` y `theatre_indicated` sólo los usan las pruebas (TD-58);
- el fármaco en inglés en las notas 6 y 7 (TD-57);
- «posterior» frente a «inferolateral» (61m).

---

## J. R-3 · T-2, T-3 y T-4

La C3 de la 29f sigue como **PARCIAL documentada**. TDFC sigue siendo binario: no hay un nivel parcial por observación.

| CASE | CURRENT DECLARATION | WHY QUESTIONED | OBSERVABLE COMPONENT | WHAT REMAINS OUTSIDE | RECOMMENDATION |
|---|---|---|---|---|---|
| **T-2** · `opioid_35m`, `opioid_67f`, `bradycardia_ccb_68m`, `bradycardia_bb_54f` | C1 YES (TDFC-REVIEW-1, «clear») | Su EPA propia es C8 (no habilitada). Cuentan por la insuficiencia respiratoria o el shock, y porque el motor obliga a revisar el plan. La evidencia incluye antídotos («gives the cause's antidote», «gives glucagon») | 35m: «Integrating ventilation, titration and recurrence, and deciding the observation.» 67f: «Integrating the recurrence into the plan: infusion and observation.» 68m: «Integrating antidote, support and its fading, and deciding the continuity.» 54f: «Integrating antidote, support and continuity.» | «Real team leadership; the full breadth of critical illness; procedural skills; the real clinical context.» | **CONFIRM C1 YES.** Opcional: agregar a lo que queda fuera «The toxicological reasoning that chooses the antidote is C8's (not enabled); C1 is confirmed by the resuscitation: recognising the failure, reassessing and escalating support or help.» El antídoto, como parte de la reanimación, sigue contando |
| **T-3** · `hypoglycemia_76f` | C1 NO: «The recurrence (infusion, octreotide, observation) is surveillance and continuity, which R1-06 looks for; hypoglycaemia is not a C1 condition.» | La recurrencia podría leerse como una revisión del modelo de trabajo | — (NO) | La recurrencia queda en R1-06, vigilancia y continuidad | **CONFIRM NO.** Revisar el modelo de trabajo no convierte la hipoglicemia en una condición de reanimación |
| **T-4** · `acs_52m_de_winter` | F1 NO y C3 NO: no necesita reanimación al llegar (SpO₂ 95 %). La congestión tardía del modelo general (SpO₂ < 90 % sólo después del minuto 80) quedó fuera por TDFC-5 | El motor congestiona pasado el minuto 80 | — (NO) | La hipoxemia tardía, que ni el caso ni su declaración sostienen | **CONFIRM NO** |

---

## K. R-5 · las guías

**Lo que ya está bien:**

- No hay nota global, ranking ni tabla de posiciones.
- La IA está apagada durante el encuentro y no está autorizada después.
- El foco de aprendizaje llega después de la revisión.
- El residente no sabe qué caso le eligieron ni por qué.
- El residente descarga su registro completo.
- La privacidad entre residentes.

**Cambios requeridos.**

**Guía docente:**

1. **Etiquetas.** La guía cita las etiquetas en inglés y el piloto se usará en español. Propongo el español primero y el
   inglés entre paréntesis:

   | Hoy en la guía | Propuesta |
   |---|---|
   | «Resident activity and recorded evidence» | «Actividad del residente y evidencia registrada» («Resident activity and recorded evidence») |
   | «Management reasoning rubric - pilot 1.0» | «Rúbrica de razonamiento de manejo - piloto 1.0» |
   | «Void assessment» | «Anular evaluación» |
   | «Who may choose a resident's cases» | «Quién puede elegir los casos de un residente» |
   | «Direct a resident's next encounter» | «Dirigir el próximo encuentro de un residente» |

2. **Falta un paso del flujo.** Hoy el paso 3 dice: «**Puntúe la rúbrica** (…), de 0 a 3 por dominio, o «No evaluable»
   si el encuentro no dio la oportunidad. Confírmela.» Agregar después:

   > «**Decida cada evento crítico** definido para el caso («Eventos críticos definidos para este caso»): «Confirmado -
   > aplica la penalización» (−3, que queda visible) o «Aún sin decidir». En el piloto la IA no propone eventos, así que
   > confirmar uno pide su motivo; la etiqueta dice «Por qué (la IA no propuso este)». La pantalla muestra lo que el
   > registro establece de cada evento; la decisión es suya.»

3. **Precisión.** Hoy dice: «La lisis actúa sobre el trombo esté o no indicada, y su riesgo de sangrado es el que ya
   declaraba el caso.» Agregar: «Toda dosis produce además una pérdida pequeña de hemoglobina, visible sólo en el
   laboratorio (decisión del 2026-09-20).»

4. **Limitaciones conocidas.** Quedan según sus decisiones:
   - quitar la línea de TD-48 una vez corregido;
   - TD-50, si no se corrige: el examen de la 29f mantiene el estridor; la 63m paga un estridor que no se oye;
   - la TEP de la 33f (sección E);
   - la 70f (TD-53);
   - los POCUS de control estáticos (TD-54);
   - la transfusión sin velocidad ni reevaluación: 30 min por unidad, y el reloj avanza hasta que termina (TD-32);
   - «General appearance» muestra el resumen del motor (TD-59);
   - TD-49 y TD-51.

5. **Recomendado, no requerido.** Una línea sobre el portafolio: «Si un residente deja el programa, el administrador
   puede descargar el portafolio completo de su cuenta inactiva (P-10).»

**Guía del residente:**

1. **Etiquetas, en español primero:**
   - «Cambia tu contraseña»;
   - «Comenzar encuentro»;
   - «Finalizar ahora»;
   - «Revisión de decisiones»;
   - «Mis encuentros», «Mi progreso», «Mi portafolio»;
   - «Descarga tu registro completo».
2. **Aviso de la foto.** Hoy dice: «Lee la llegada: la historia, los signos vitales, el examen y la foto o la vista
   neutral del paciente.» Agregar:

   > «La foto ayuda a ver al paciente; lo que no muestra, la sala lo escribe al lado. El monitor y el examen escritos
   > son los vigentes.»

3. **Aviso del POCUS.** Es nuevo. Requiere TD-48 corregido; si no se corrige, no puede decir «todas sus ventanas»:

   > «El POCUS y el E-FAST se informan por escrito, con todas sus ventanas. La sala te entrega los hallazgos; lo que
   > cuenta es cuándo lo pides, cómo lo interpretas y qué decides, no cómo adquieres ni reconoces la imagen.»

4. **Recomendado.** Hoy dice: «escribe las dosis, las vías y cuándo reevaluar». Agregar: «una orden con duración, como
   una transfusión, avanza el reloj hasta que termina, salvo que indiques cuándo reevaluar».

**R-5 sigue sin aprobar:** las guías no se modificaron. Se ajustan después de sus decisiones y se firman.

---

## L. PRE-PILOT CHECKLIST

| Área | Estado | Qué falta |
|---|---|---|
| Contenido clínico | **BLOCKED** | D-2 (29f) y D-1 (trauma). D-3, D-4 y D-8 son condiciones |
| POCUS | **BLOCKED** (trauma) · PENDING (resto) | D-1; la firma de las fichas (D-7) |
| Español | PENDING | D-5 y D-6. El relato de los casos sin aprobar se ve en inglés, línea entera: aceptable |
| Imágenes | PENDING | El orden de pasos de TD-56; V34 pendiente (la 75f en vista neutral); `MRS_IMAGE_REQUIRE_REVIEW=on` |
| Flujo docente | PENDING | Guía con el paso de los eventos críticos (D-11). Lo de la regla B ya está hecho |
| Flujo del residente | PENDING | Guía (D-11). Verificado técnicamente en la prueba de humo de `351dcab` |
| Permisos | READY | Prueba de humo: otro residente no lee ni lista; el residente no confirma ni invita; el docente no invita. TD-44 |
| IA sin conexión | READY | `MRS_OFFLINE_CASES=1`: 0 llamadas medidas. El preflight lo verifica |
| Base de datos | READY (técnico) · PENDING (despliegue) | PostgreSQL, respaldo y restauración probados. Faltan la base desplegada, su integridad y el simulacro |
| Portafolio | READY | P-10 implementado; el residente descarga su registro completo |
| Pruebas | PENDING | La suite completa pasó en `ad98005`. En esta fase, sólo las pruebas focalizadas del cambio B. Sobre el candidato final: las focalizadas, las 56 regresiones y la suite completa |
| Despliegue | PENDING | No desplegado, por instrucción |
| Prueba de humo | PENDING | La última fue en `351dcab`. Repetirla, automática y manual, sobre el candidato final y en el entorno desplegado |
| Aprobaciones humanas | PENDING | D-1 a D-11, y la condición C: la autorización explícita de inicio |

**DEPLOY → PREFLIGHT → SMOKE TEST.** Comandos de `docs/RUNBOOK_PILOTO.md`, más el paso 5 nuevo. **NO EJECUTADOS.**

```
# 0. Candidato: el commit aprobado de clinical-encounter-v0.13 (aún no definido).

# 1. Respaldo, si la base ya existe:
pg_dump --format=custom --no-owner --no-privileges --file=mrs-AAAAMMDD-HHMM.dump "$MRS_DATABASE_URL"

# 2. Secrets, en un lugar privado (nunca en GitHub):
#    MRS_AUTH_MODE=accounts · MRS_DATABASE_URL=…?sslmode=require · MRS_OFFLINE_CASES=1
#    MRS_IMAGE_REQUIRE_REVIEW=on · MRS_PAID_GENERATION=off · MRS_CODE_VERSION=<commit>
#    MRS_ADMIN_USERNAME y MRS_ADMIN_PASSWORD_HASH, de:
python setup_accounts.py --print-bootstrap
#    Sin OPENAI_API_KEY, MRS_ALLOW_LOCAL_SQLITE, MRS_REPLAY_CASE, MRS_DEFAULT_VARIANT,
#    MRS_SYNTHETIC_ACCOUNTS ni MRS_BATCH_*.

# 3. PREFLIGHT. Debe terminar en «Configuración del piloto: LISTA.»:
python3 tools_pilot_preflight.py --secrets ruta/a/secrets.toml --connect

# 4. DEPLOY: desplegar el commit aprobado (Streamlit), abrir la aplicación, entrar como
#    administrador y retirar MRS_ADMIN_USERNAME y MRS_ADMIN_PASSWORD_HASH.

# 5. Fotos (TD-56, nuevo): ANTES de abrir cualquier encuentro o el banco de imágenes, crear y
#    activar la cuenta docente que firmó assets/patient_images/approvals.json. Si algo se abrió antes:
python3 tools_image_bank.py import --database-url "$MRS_DATABASE_URL" --pack assets/patient_images

# 6. Integridad:
python3 check_database.py --integrity

# 7. SMOKE TEST automático (crea su propia base temporal; no toca la del piloto):
python3 tools_pilot_smoke.py --configuration pilot --out smoke.json

# 8. SMOKE TEST manual en la aplicación desplegada (runbook §4, pasos 1 a 5), con cuentas de
#    prueba sin nombres reales. La cuenta docente del paso 5 debe existir antes de que el
#    residente de prueba juegue.

# 9. Simulacro de restauración en una base nueva:
pg_restore --no-owner --no-privileges --exit-on-error --dbname="$URL_DE_LA_BASE_NUEVA" mrs-AAAAMMDD-HHMM.dump
python3 tools_backup_drill.py --compare "$MRS_DATABASE_URL" "$URL_DE_LA_BASE_NUEVA"
```

---

# DECISIONS NEEDED FROM NICOLÁS

| ID | Pregunta | Mi recomendación | Si se difiere |
|---|---|---|---|
| **D-1** | ¿Corregimos TD-48 antes del piloto con la opción A (las cinco ventanas del E-FAST en la sala, el Trace y los documentos, con los títulos en español propuestos)? | **Sí, opción A.** | Los dos casos de trauma quedan fuera del piloto: su C14 no se puede cumplir |
| **D-2** | ¿Corregimos TD-50 antes del piloto: el examen sigue al estridor del motor (opción 1), y además el cobro relativo a la llegada (2) y el estridor declarado por caso (3)? | **Sí a la 1** (BLOCKER de la 29f). **Sí a la 2 y la 3** si las aprueba; si no, quedan como condición | La 29f sale del piloto; la 63m queda con un aviso docente |
| **D-3** | ¿Mantenemos la fisiología actual de la TEP para el piloto (KEEP FOR PILOT, con aviso docente) y dejamos la verificación de fuentes para después? | **Sí.** | Queda igual, pero sin aviso en la guía: riesgo de juzgar mal la respuesta del residente al sangrado |
| **D-4** | ¿Cambiamos la glosa del shock de la nota 1 (inglés y español) por el criterio completo: hipotensión, o un vasopresor necesario para sostener la presión, con signos de hipoperfusión? | **Sí.** | La nota sigue omitiendo la vía del vasopresor. El motor y el juicio no cambian |
| **D-5** | ¿Aprobamos el español de las 7 notas de la TEP con los cambios menores («administrada», la tilde en todas las notas, el fármaco en español) y el borrador del aviso del sangrado? | **Sí.** | Siguen como están hoy, y el aviso del sangrado sigue en inglés |
| **D-6** | ¿Aprobamos las 18 frases de R-4 (17 tal como están y la fila 18 con su verbo, también en la línea activa de la sala)? | **Sí.** | Siguen en inglés en el panel de examen en español, sin mezcla |
| **D-7** | ¿Confirmamos las fichas R-2: 10 CONFIRM, la redacción de la 52m (MODIFY) y, opcionalmente, «dynamic» en la 83m? | **Sí; la 83m, opcional.** | Las filas siguen como se aprobaron el 2026-09-28, sin la firma de las fichas |
| **D-8** | Sobre la 70f, cuya sobrecarga no se ve (TD-53): ¿(a) aviso docente y regla de evaluación para el piloto, o (b) corregir el motor antes? | **(a)**, y (b) después del piloto | Sin aviso, el docente podría penalizar a un residente que confió en un POCUS de control falso |
| **D-9** | ¿Corregimos TD-49 (una línea) junto con TD-48, y dejamos TD-51 para después del piloto? | **Sí** a las dos | TD-49 sigue mostrando la lisis dos veces en «Current treatments». TD-51 queda en la guía |
| **D-10** | ¿Firmamos R-3: T-2 con C1 YES (y la frase aclaratoria opcional), T-3 NO y T-4 NO? | **Sí.** | Quedan provisionales, como hoy. No bloquea |
| **D-11** | ¿Aprobamos los cambios requeridos de las dos guías (sección K), para firmarlas después de D-1 a D-8? | **Sí.** | Las guías no se entregan y el piloto no puede empezar: R-5 es requisito |

Este paquete termina aquí. No implemento, no despliego y no inicio otro ciclo hasta recibir sus decisiones. Su silencio
no es una aprobación.
