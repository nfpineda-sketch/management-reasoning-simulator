"""Draft notes for the faculty's case-by-case review of the arrival POCUS of the C14 YES cases (R-2).

Faculty decision of 2026-09-30 (R-2): the POCUS of the 14 C14 YES cases is reviewed clinically before the
pilot, case by case, not signed as a block. These notes were prepared by the AI Advisor to make that review
fast. They are a proposal and approve nothing: no case changes, no image or video, and nothing that residents
or faculty run reads this module. ``tools_review_sheets.r2_sheet`` joins them to what each case declares
(arrival state, POCUS and E-FAST findings, C14) in ``docs/revision/R2_POCUS_C14.md``.

The ACEP 2016 alignment follows ``docs/ACEP_POCUS_FRAMEWORK.md``: qualitative LV function, IVC and volume,
B-lines, pleural fluid, DVT compression and the E-FAST are established; regional wall motion and the RV are
not. The simulator gives a written report, so acquisition and recognition in the image are not observed.
"""
STATUS = "draft_for_faculty_review"
DATE = "2026-09-30"
RECOMMENDATIONS = ("CONFIRM", "MODIFY", "DISCUSS")

#: The pre-pilot closure (faculty, 2026-10-02, D-7): the criteria of the table were accepted, with the
#: conditions below already applied; the signature of each final card stays pending.
ACCEPTANCE = ("Criterios de la tabla aceptados por el docente el 2026-10-02 (D-7), con sus condiciones ya aplicadas. "
              "La firma de cada ficha final sigue pendiente: nada aquí marca CONFIRMO ni firma.")

#: The faculty's criteria applied to the C14 declarations (``case_assessment_bank``): R-2 for two cases
#: (2026-09-30) and the pre-pilot closure (2026-10-02). They approve criteria, not the case's card.
FACULTY_CRITERIA = {
    "acs_61m_posterior": ("R-2, 2026-09-30: «Aorta no dilatada» en el POCUS no se presenta como disección "
                          "descartada. La hipocinesia posterior aislada es un hallazgo sutil que el informe escrito "
                          "entrega: no se exige reconocerla, sino usar la motilidad informada con el ECG y las "
                          "derivaciones posteriores."),
    "acs_70f_left_main": ("R-2, 2026-09-30: un bolo pequeño, justificado y con reevaluación no se penaliza "
                          "automáticamente: se evalúa en su contexto y por la adaptación posterior. Hallazgos "
                          "intermedios no tienen una sola respuesta obligatoria. D-8, 2026-10-02: el exceso de volumen "
                          "se ve sólo en la presión que deja de responder y en el mensaje de la sala; el pulmón, el "
                          "examen, la saturación y el POCUS de control no cambian. Se evalúa con esas señales: no se "
                          "exige detectar sobrecarga por examen ni por POCUS, y si la única respuesta que buscó el "
                          "residente es una que el simulador no muestra, esa parte no es evaluable."),
    "acs_52m_de_winter": ("D-7, 2026-10-02: la motilidad la entrega el informe escrito; no se exige reconocerla. El "
                          "POCUS nunca demora la reperfusión: activarla sólo por el ECG es correcto y no es un déficit "
                          "de C14."),
    "trauma_hemothorax_41m": ("D-1, 2026-10-02: el E-FAST muestra sus cinco ventanas en la sala, el Trace y los "
                              "documentos; el hemotórax izquierdo es visible y el control tras el drenaje muestra el "
                              "abdomen y la pelvis. Ficha lista para su confirmación."),
    "trauma_limb_hemorrhage_27m": ("D-1, 2026-10-02: el E-FAST muestra sus cinco ventanas en la sala, el Trace y los "
                                   "documentos, todas negativas. Ficha lista para su confirmación."),
}

_WMA = ("Motilidad regional: NO establecida por ACEP 2016 ni en la lista de la EPA C14; se aceptó por alcance "
        "local (decisión A). Informe escrito: no se observa la adquisición ni el reconocimiento en la imagen.")
_VOLUME = ("VI cualitativo y VCI para el volumen: ESTABLECIDOS por ACEP 2016 (el método de la VCI no se "
           "especifica); repetir el examen para monitorizar la respuesta también está establecido.")
_RV = ("TVP por compresión: ESTABLECIDA. VD, signo D y McConnell: NO establecidos por ACEP 2016 ni en la lista "
       "de la EPA; se aceptaron por alcance local (decisión G).")
_EFAST = "E-FAST de cinco ventanas: ESTABLECIDO por ACEP 2016 para el trauma con hipotensión."

NOTES = {
    "acs_52m_de_winter": {
        "application": "Cardíaca focalizada: motilidad regional del VI, como apoyo del ECG",
        "interpret": "Acinesia anterior y apical, territorio de la DA, concordante con el patrón de de Winter "
                     "como equivalente de oclusión",
        "management": "Activar o acelerar la reperfusión sin esperar la troponina; el ECG basta para decidir y "
                      "el POCUS lo apoya",
        "acep": _WMA,
        "issue": "El hallazgo es coherente con la clínica y el ECG. Riesgo docente, ya escrito en la declaración "
                 "(D-7): demorar la activación por hacer el POCUS",
        "recommendation": "CONFIRM",
    },
    "acs_61m_posterior": {
        "application": "Cardíaca focalizada (motilidad regional) y aorta torácica en un dolor torácico con "
                       "irradiación al dorso",
        "interpret": "Motilidad regional informada (hipocinesia posterior), compatible con un infarto posterior que "
                     "el ECG de 12 derivaciones subestima (infradesnivel V1–V3). Una aorta no dilatada en el POCUS "
                     "no descarta una disección",
        "management": "Derivaciones posteriores y activar la reperfusión",
        "acep": _WMA + " La dilatación de la raíz aórtica y de la aorta descendente sí está establecida",
        "issue": "Criterio docente aplicado a la declaración C14 (R-2): la motilidad sutil no se exige reconocer y el "
                 "límite de la aorta queda escrito. Falta su revisión de la ficha completa",
        "recommendation": "CONFIRM",
    },
    "acs_70f_left_main": {
        "application": "Cardíaca (función global del VI), pulmonar (líneas B) y VCI en un SCA con hipoperfusión "
                       "incipiente",
        "interpret": "Contracción global levemente disminuida, sin defecto focal, y líneas B basales dispersas: "
                     "isquemia difusa con congestión inicial, no edema franco. La VCI es intermedia",
        "management": "Volumen prudente o ninguno, soporte precoz si progresa la hipoperfusión y reperfusión "
                      "urgente (tronco); un bolo pequeño con su límite y reevaluación es defendible",
        "acep": _VOLUME + " Las líneas B también están establecidas",
        "issue": "Criterios docentes aplicados a la declaración C14 (R-2 y D-8): se evalúa la decisión en contexto, "
                 "con las señales que el residente tiene. La sobrecarga no cambia el pulmón, el examen ni el POCUS "
                 "(TD-53, sin corregir para el piloto). Falta su firma de la ficha",
        "recommendation": "CONFIRM",
    },
    "gi_bleed_57m": {
        "application": "Hipotensión indiferenciada: corazón y VCI (volumen)",
        "interpret": "VI pequeño e hiperdinámico con obliteración sistólica y VCI colapsada: shock hipovolémico "
                     "o hemorrágico, sin causa obstructiva ni cardiogénica",
        "management": "Transfusión y volumen, control de la fuente (endoscopía) y POCUS repetido tras reanimar",
        "acep": _VOLUME,
        "issue": "Coherente. La VCI no debe demorar los hemoderivados",
        "recommendation": "CONFIRM",
    },
    "gi_bleed_72f": {
        "application": "Hipotensión por sangrado: corazón y VCI (volumen)",
        "interpret": "VI hiperdinámico y VCI de 1,1 cm con más de 50 % de colapso: hipovolemia por hemorragia",
        "management": "Transfusión y volumen, con reevaluación por POCUS",
        "acep": _VOLUME,
        "issue": "Coherente. En una paciente de 72 años conviene reevaluar tras cada bolo",
        "recommendation": "CONFIRM",
    },
    "obstructive_pyelonephritis_58f": {
        "application": "Shock séptico: corazón y VCI para la estrategia de fluidos",
        "interpret": "VI vigoroso y VCI de 1,0 cm colapsable, sin líneas B: shock distributivo que tolera "
                     "volumen",
        "management": "Volumen con reevaluación, antibiótico precoz, vasopresor si persiste la hipotensión y "
                      "descompresión urgente de la vía urinaria",
        "acep": _VOLUME + " La ecografía renal (hidronefrosis) es aplicación core de ACEP, pero aquí es un "
                          "estudio formal (decisión H)",
        "issue": "Coherente. Límite declarado: el POCUS repetido muestra la VCI de llegada (el motor no modela "
                 "su respuesta aquí), así que C14 no espera la reevaluación",
        "recommendation": "CONFIRM",
    },
    "pneumonia_46f": {
        "application": "Shock séptico con hipoxemia: corazón y VCI, más pulmón (consolidación y líneas B)",
        "interpret": "VI vigoroso y VCI colapsable sin líneas B difusas (tolera volumen); consolidación basal "
                     "derecha con broncograma dinámico, compatible con neumonía",
        "management": "Volumen con reevaluación (la aparición de líneas B difusas es señal de detenerse), "
                      "antibiótico, oxígeno y vasopresor si no responde",
        "acep": _VOLUME + " Líneas B: establecidas. Consolidación: parcial (decisión F: no hace la oportunidad "
                          "por sí sola)",
        "issue": "Coherente. Con SpO2 89 %, reevaluar tras el volumen es lo que protege: la VCI y la saturación "
                 "muestran el exceso, pero el pulmón del POCUS no muestra líneas B nuevas con la sobrecarga de "
                 "cristaloides (TD-54); no se exige verlas",
        "recommendation": "CONFIRM",
    },
    "pneumonia_83m": {
        "application": "Hipotensión en un anciano derivado como «deshidratado»: corazón y VCI, más pulmón",
        "interpret": "VI conservado y VCI colapsable (tolera volumen); consolidación basal izquierda con "
                     "broncograma: el foco séptico que la derivación no nombró",
        "management": "Volumen prudente con reevaluación, antibiótico y oxígeno",
        "acep": _VOLUME + " Consolidación: parcial (decisión F)",
        "issue": "Coherente. «air bronchograms» sin «dynamic» se mantiene (D-7, 2026-10-02): agregarlo sería un "
                 "hallazgo nuevo, no una mejora editorial",
        "recommendation": "CONFIRM",
    },
    "pulmonary_edema_58m": {
        "application": "Disnea aguda: pulmón (líneas B), corazón y VCI",
        "interpret": "Líneas B difusas bilaterales, VI moderadamente disminuido y VCI pletórica: edema pulmonar "
                     "cardiogénico hipertensivo",
        "management": "Nitrato en dosis altas, VNI y diurético; no dar volumen",
        "acep": _VOLUME + " Líneas B: establecidas",
        "issue": "Coherente. En español, hasta aprobar el relato del caso, la línea se ve entera en inglés (TD-46, "
                 "corregido el 2026-09-30)",
        "recommendation": "CONFIRM",
    },
    "pulmonary_edema_75f": {
        "application": "Disnea aguda en IC con FE reducida: pulmón, corazón y VCI",
        "interpret": "Líneas B difusas, VI gravemente disminuido, VCI pletórica y derrames pequeños: IC "
                     "descompensada con edema pulmonar",
        "management": "Nitrato (presión de 164), VNI y diurético; no dar volumen; vigilar el bajo gasto",
        "acep": _VOLUME + " Líneas B y derrame: establecidos",
        "issue": "Coherente con sus comorbilidades (IC con FE reducida, ERC)",
        "recommendation": "CONFIRM",
    },
    "pulmonary_embolism_33f": {
        "application": "Disnea súbita posoperatoria: TVP por compresión, VD y VCI",
        "interpret": "TVP poplítea proximal en el lado operado y VD levemente dilatado (VD ≈ VI) sin signo D: "
                     "enfermedad tromboembólica, sin shock",
        "management": "Anticoagular antes de la angio-TC (o dejarlo explícito como pendiente de ella) y no "
                      "trombolizar con hemodinamia estable",
        "acep": _RV,
        "issue": "Coherente: la relación VD/VI cercana a 1 ya es dilatación. La TVP poplítea cuenta como "
                 "proximal",
        "recommendation": "CONFIRM",
    },
    "pulmonary_embolism_61m": {
        "application": "Shock indiferenciado: VD (RUSH), VCI y TVP",
        "interpret": "VD mayor que el VI, septum aplanado (signo D), signo de McConnell, VI pequeño y VCI "
                     "pletórica, más TVP poplítea: shock obstructivo por TEP de alto riesgo",
        "management": "Anticoagulación y reperfusión sin esperar la angio-TC, volumen limitado, vasopresor y "
                      "evitar intubar si se puede",
        "acep": _RV,
        "issue": "Coherente con la guía (con el paciente inestable, el VD en el eco basta para decidir la "
                 "reperfusión cuando la TC no es inmediata)",
        "recommendation": "CONFIRM",
    },
    "trauma_hemothorax_41m": {
        "application": "E-FAST en trauma cerrado con hipotensión",
        "interpret": "Líquido en el receso pleural izquierdo (colección ecogénica): hemotórax; sin neumotórax, "
                     "sin líquido abdominal ni pericárdico",
        "management": "Tubo pleural, hemoderivados, controlar el débito (toracotomía si es masivo) y reevaluar",
        "acep": _EFAST,
        "issue": "Coherente. Un FAST abdominal negativo no descarta una lesión retroperitoneal o pélvica. El "
                 "E-FAST de control repite los hallazgos de llegada y la VCI del POCUS de control no cambia (TD-54): "
                 "no se exige ver en ellos un cambio que el simulador no muestra",
        "recommendation": "CONFIRM",
    },
    "trauma_limb_hemorrhage_27m": {
        "application": "E-FAST en trauma de extremidad con shock",
        "interpret": "Cinco ventanas negativas: no hay sangrado en cavidades que explique el shock; la fuente es "
                     "el muslo",
        "management": "Compresión o torniquete primero, hemoderivados, ácido tranexámico y control quirúrgico; "
                      "repetir el E-FAST si se deteriora sin explicación",
        "acep": _EFAST,
        "issue": "Coherente. El E-FAST no debe preceder al control de la hemorragia externa, y su sensibilidad "
                 "precoz es limitada (el caso lo pide: «states what would change that»). La VCI del POCUS de "
                 "control no cambia tras el control y la sangre (TD-54): no se exige verla llenarse",
        "recommendation": "CONFIRM",
    },
}
