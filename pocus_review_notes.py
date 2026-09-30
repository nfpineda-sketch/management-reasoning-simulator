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
        "issue": "El hallazgo es coherente con la clínica y el ECG. Riesgo docente: demorar la activación por "
                 "hacer el POCUS",
        "recommendation": "CONFIRM",
    },
    "acs_61m_posterior": {
        "application": "Cardíaca focalizada (motilidad regional) y aorta torácica en un dolor torácico con "
                       "irradiación al dorso",
        "interpret": "Hipocinesia posterior, compatible con un infarto posterior que el ECG de 12 derivaciones "
                     "subestima (infradesnivel V1–V3)",
        "management": "Derivaciones posteriores y activar la reperfusión",
        "acep": _WMA + " La dilatación de la raíz aórtica y de la aorta descendente sí está establecida",
        "issue": "La hipocinesia posterior aislada es un hallazgo sutil incluso para ecografistas expertos. "
                 "Con dolor al dorso, «aorta no dilatada» puede leerse como disección descartada, y el POCUS no "
                 "la descarta. Revisar si el caso debe decir ese límite",
        "recommendation": "DISCUSS",
    },
    "acs_70f_left_main": {
        "application": "Cardíaca (función global del VI), pulmonar (líneas B) y VCI en un SCA con hipoperfusión "
                       "incipiente",
        "interpret": "Contracción global levemente disminuida, sin defecto focal, y líneas B basales dispersas: "
                     "isquemia difusa con congestión inicial, no edema franco. La VCI es intermedia",
        "management": "Volumen prudente o ninguno, soporte precoz si progresa la hipoperfusión y reperfusión "
                      "urgente (tronco)",
        "acep": _VOLUME + " Las líneas B también están establecidas",
        "issue": "La hipoperfusión es incipiente (104/66, extremidades frías, llene de 3 s) y los hallazgos son "
                 "intermedios (VI levemente disminuido desde DF-23, VCI de 1,9 cm con 50 %). C14 espera «limitar "
                 "o retener volumen, o escalar soporte»: un bolo pequeño con reevaluación no debería juzgarse "
                 "como error. Confirmar que el texto «leve» y la expectativa van juntos",
        "recommendation": "DISCUSS",
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
        "issue": "Coherente. Con SpO2 89 %, la reevaluación pulmonar tras el volumen es lo que protege",
        "recommendation": "CONFIRM",
    },
    "pneumonia_83m": {
        "application": "Hipotensión en un anciano derivado como «deshidratado»: corazón y VCI, más pulmón",
        "interpret": "VI conservado y VCI colapsable (tolera volumen); consolidación basal izquierda con "
                     "broncograma: el foco séptico que la derivación no nombró",
        "management": "Volumen prudente con reevaluación, antibiótico y oxígeno",
        "acep": _VOLUME + " Consolidación: parcial (decisión F)",
        "issue": "Coherente. Detalle opcional: «air bronchograms» sin «dynamic» no distingue la neumonía de la "
                 "atelectasia (la 46f sí dice «dynamic»)",
        "recommendation": "CONFIRM",
    },
    "pulmonary_edema_58m": {
        "application": "Disnea aguda: pulmón (líneas B), corazón y VCI",
        "interpret": "Líneas B difusas bilaterales, VI moderadamente disminuido y VCI pletórica: edema pulmonar "
                     "cardiogénico hipertensivo",
        "management": "Nitrato en dosis altas, VNI y diurético; no dar volumen",
        "acep": _VOLUME + " Líneas B: establecidas",
        "issue": "Coherente. En español, antes de aprobar el relato del caso, esta línea se lee mezclada "
                 "(«Moderately reducido global contraction», TD-46)",
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
        "issue": "Coherente. Un FAST abdominal negativo no descarta una lesión retroperitoneal o pélvica",
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
                 "precoz es limitada (el caso lo pide: «states what would change that»)",
        "recommendation": "CONFIRM",
    },
}
