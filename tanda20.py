"""Twenty scenarios for the synthetic batch of 2026-09-24, the learner's side only.

The faculty's specification (section 3 and 5): twenty different scenarios,
chosen among the most developed and tested cases, played by an automated agent
on a test account and identified as such -- never as a person's performance.
Not every one is managed well. The category is the *intent* of the script, not
a grade: what the analysis says has to come from what the record shows.

    4  bueno        adequate, timely, efficient
    4  largo        longer paths: more information, less efficient, delays
    4  recuperacion early errors, later recognition and correction
    4  equivocado   wrong decisions or priorities that change the course
    2  deficiente   cues misread, a wrong hypothesis kept, reassessments wasted
    2  alternativa  clinically defensible paths other than the expected one

Each step is what a resident does on the page:

    ("ask", text)        Talk: ask the patient or the collateral source
    ("examine", area)    Examine: one area of the examination
    ("order", text)      Treat: the natural-language box, then Submit
    ("complete", {...})  the four questions of a held order, then execute it
    ("cancel",)          cancel the pending orders
    ("recover",)         save and return to the dashboard, then resume

Orders are written the way the application says it reads them, including
abbreviations, missing accents and grouped orders. Nothing here is
optimised for a score, and the consequences of a mistake are left in place.
The scripts are rehearsed offline (``tools_tanda20.py --rehearse``) through the
real page before any paid encounter; the batch itself must run on the
development app with the real accounts.
"""

CATEGORIES = {
    "bueno": "Manejo adecuado, oportuno y eficiente",
    "largo": "Camino más largo: información adicional, decisiones menos eficientes o demoras",
    "recuperacion": "Errores iniciales, reconocimiento posterior y corrección",
    "equivocado": "Decisiones o prioridades equivocadas que afectan la evolución",
    "deficiente": "Desempeño claramente deficiente: cues mal leídas, hipótesis equivocada sostenida",
    "alternativa": "Alternativa clínicamente defendible distinta del camino esperado",
}

# The challenge each case is launched under. A challenge offers only its own
# families, so the case decides it (cognitive_catalog / curriculum).
CHALLENGE_FOR_FAMILY = {
    "asthma": "R3-01", "hypoglycemia": "R1-06", "acs": "R2-02", "gi_bleed": "R2-05",
    "pneumonia": "R1-05", "opioid": "R1-06", "renal_colic": "R2-05",
    "pulmonary_edema": "R1-05", "anaphylaxis": "R1-06", "pulmonary_embolism": "R2-02",
    "bradycardia": "R2-04",
}


def _script(number, case_id, family, category, intent, steps, *, reflection, plan,
            comparison=None):
    return {"number": number, "case_id": case_id, "family": family, "category": category,
            "challenge": CHALLENGE_FOR_FAMILY[family], "intent": intent, "steps": steps,
            "reflection": reflection, "plan": plan,
            "comparison": comparison or {
                "alignment": "Coincidí en la prioridad inicial.",
                "adjustment": "Declararía antes el umbral para cambiar de plan."}}


SCRIPTS = [
    # --- 4 · bueno ------------------------------------------------------------
    _script(
        1, "asthma_24f", "asthma", "bueno",
        "Crisis asmática grave manejada a tiempo: broncodilatación y oxígeno de entrada, "
        "corticoide, magnesio ante respuesta parcial, destino con la respuesta observada.",
        [
            ("examine", "Breathing"),
            ("order", "Creo que es una crisis asmatica grave, porque habla en frases cortas, "
                      "FR 34 y satura 90%. Mi prioridad es broncodilatar y oxigenar ya. Doy "
                      "salbutamol 5 mg nebulizado + ipratropio 0.5 mg nbz; O2 por mascarilla a "
                      "6 L/min. Espero que baje el trabajo respiratorio y la sat suba sobre 94%. "
                      "Reevaluo en 15 min FR y saturacion."),
            ("order", "Doy hidrocortisona 200 mg ev para acortar la crisis; pido gases venosos. Espero "
                      "menos riesgo de recaida en las proximas horas. Reevaluo en 30 minutos FR y saturacion."),
            ("examine", "Breathing"),
            ("order", "Mejora parcial, persiste el esfuerzo. Mi prioridad es un segundo "
                      "broncodilatador sin demora. Doy sulfato de magnesio 2 g ev en 20 minutos. "
                      "Espero que ceda el esfuerzo respiratorio. Reevaluo en 20 minutos FR, saturacion "
                      "y si habla frases completas."),
            ("order", "Respondio bien: habla frases completas y satura 95%. Mi prioridad es un "
                      "destino con vigilancia. La hospitalizo en sala para seguir "
                      "broncodilatadores y corticoide. Espero que se mantenga estable. Reevaluo "
                      "en 30 minutos saturacion y trabajo respiratorio."),
        ],
        reflection={
            "working_model_update": "La gravedad estaba en el esfuerzo y el habla, no sólo en la saturación.",
            "priority_trigger": "Un tórax silencioso o somnolencia me habría hecho escalar a soporte ventilatorio.",
            "alternative_action": "Podría haber iniciado nebulización continua.",
            "expected_response_reassessment": "Esperaba menos esfuerzo; reevalué FR, saturación y habla.",
        },
        plan={"cue": "Habla entrecortada", "threshold": "Sat < 92% tras la segunda nebulización",
              "next_priority": "Escalar a soporte ventilatorio si no responde",
              "alternative_action": "Nebulización continua", "expected_effect": "Menos esfuerzo en 15 min",
              "reassessment_plan": "FR, saturación y habla cada 15 min"},
    ),
    _script(
        2, "hypoglycemia_28m", "hypoglycemia", "bueno",
        "Confusión con glicemia capilar como primer estudio, dextrosa ev inmediata, "
        "reevaluación de conciencia y glicemia, alimentación y causa preguntada.",
        [
            ("order", "Pido glicemia capilar"),
            ("order", "Creo que es una hipoglicemia sintomatica, porque esta somnoliento y "
                      "confuso con glicemia baja. Mi prioridad es corregirla ya. Instalo via "
                      "venosa periferica; doy glucosa 25 g ev. Espero que despierte y suba la "
                      "glicemia. Reevaluo en 10 minutos conciencia y glicemia."),
            ("ask", "¿Usa insulina o algún medicamento para el azúcar? ¿Comió hoy?"),
            ("order", "Pido glicemia capilar"),
            ("order", "Desperto y la glicemia es normal. Mi prioridad es que no vuelva a caer. "
                      "Le doy colacion oral y lo dejo en observacion 2 horas con glicemia "
                      "capilar seriada. Espero glicemia sobre 100. Reevaluo en 30 minutos glicemia "
                      "capilar y conciencia."),
        ],
        reflection={
            "working_model_update": "La confusión era hipoglicemia hasta que se demostrara otra cosa.",
            "priority_trigger": "Una nueva caída de glicemia me habría hecho iniciar infusión de glucosa.",
            "alternative_action": "Glucagón si no hubiera tenido acceso venoso.",
            "expected_response_reassessment": "Esperaba recuperación en minutos; medí glicemia y conciencia.",
        },
        plan={"cue": "Glicemia capilar", "threshold": "< 70 mg/dL", "next_priority": "Identificar la causa",
              "alternative_action": "Infusión de glucosa al 10%", "expected_effect": "Glicemia estable",
              "reassessment_plan": "Glicemia cada 30 min por 2 horas"},
    ),
    _script(
        3, "acs_54m_inferior", "acs", "bueno",
        "Molestia epigástrica con bradicardia e hipotensión leve: ECG precoz, derivadas "
        "derechas, antiagregación, sin nitratos, reperfusión solicitada.",
        [
            ("order", "Pido ECG de 12 derivaciones"),
            ("order", "Creo que es un IAM inferior con posible compromiso del VD, porque hay "
                      "supradesnivel inferior, FC 58 y PA 100/64. Mi prioridad es reperfundir y "
                      "no bajar la precarga. Doy aspirina 300 mg vo y clopidogrel 600 mg vo; pido "
                      "ECG con derivadas derechas. Espero documentar el VD sin que caiga la "
                      "presion. Reevaluo en 10 minutos PA y FC."),
            ("ask", "¿Tiene alergias o sangrado reciente? ¿Toma anticoagulantes?"),
            ("order", "Consulto a hemodinamia para angioplastia primaria porque es un IAM con "
                      "supradesnivel. Espero que acepten en menos de 90 minutos. Reevaluo en 10 "
                      "minutos dolor, PA y FC."),
            ("order", "Sigue estable, PA sobre 95. Mi prioridad es llegar a la sala de hemodinamia "
                      "monitorizado. Lo traslado a hemodinamia con monitor. Espero que no caiga la "
                      "presion en el traslado. Reevaluo en 15 minutos PA y ritmo."),
        ],
        reflection={
            "working_model_update": "El dolor 'dispéptico' con bradicardia era un infarto inferior.",
            "priority_trigger": "Una caída de presión me habría hecho dar volumen y evitar nitratos.",
            "alternative_action": "Heparina en la misma entrega si la sala tardaba.",
            "expected_response_reassessment": "Vigilé PA y FC mientras se activaba hemodinamia.",
        },
        plan={"cue": "Supradesnivel inferior", "threshold": "PAS < 90", "next_priority": "Reperfusión",
              "alternative_action": "Trombolisis si no hay sala", "expected_effect": "Sin hipotensión",
              "reassessment_plan": "PA y FC cada 5-10 min"},
    ),
    _script(
        4, "gi_bleed_57m", "gi_bleed", "bueno",
        "Hemorragia digestiva con hipoperfusión: accesos, volumen breve, transfusión "
        "precoz, IBP, endoscopia urgente y destino monitorizado.",
        [
            ("ask", "¿Ha tenido deposiciones negras o vómitos con sangre? ¿Toma algún medicamento?"),
            ("order", "Creo que es una hemorragia digestiva alta con hipoperfusion, porque tiene "
                      "melena, PA 88/54, FC 124 y llene capilar de 5 s. Mi prioridad es reponer "
                      "volumen y pedir sangre. Instalo 2 vvp gruesas; paso SF 500 ml ev en bolo; "
                      "pido hemoglobina, laboratorio basico y lactato. Espero que suba la PA y "
                      "mejore la perfusion. Reevaluo en 10 min PA, FC y llene capilar."),
            ("order", "Sigue hipotenso. Mi prioridad es transportar oxigeno. Transfundo 2 "
                      "unidades de globulos rojos; doy omeprazol 80 mg ev. Espero PAS sobre 90 y "
                      "FC bajo 110. Reevaluo en 15 minutos PA, FC y llene capilar."),
            ("order", "Consulto a gastroenterologia para endoscopia urgente"),
            ("complete", {"What do you expect": "Que hagan la endoscopia en las proximas horas y "
                                                "controlen el sangrado.",
                          "What will you check": "PA, FC y nueva melena o hematemesis",
                          "delay": 30}),
            ("examine", "Peripheral perfusion"),
            ("order", "Mejor perfundido, PA sobre 95. Mi prioridad es la hemostasia en un lugar "
                      "monitorizado. Lo hospitalizo en intermedio. Espero que no resangre antes "
                      "de la endoscopia. Reevaluo en 30 minutos PA, FC y hemoglobina."),
        ],
        reflection={
            "working_model_update": "La primera hemoglobina no mostraba la pérdida real.",
            "priority_trigger": "Una nueva caída de PA me habría hecho activar transfusión masiva.",
            "alternative_action": "Transfundir antes del cristaloide.",
            "expected_response_reassessment": "Medí PA, FC y llene capilar tras cada intervención.",
        },
        plan={"cue": "Llene capilar", "threshold": "PAS < 90 tras 2 unidades", "next_priority": "Endoscopia",
              "alternative_action": "Transfusión masiva", "expected_effect": "Perfusión recuperada",
              "reassessment_plan": "PA/FC cada 15 min"},
    ),
    # --- 4 · largo ------------------------------------------------------------
    _script(
        5, "pneumonia_46f", "pneumonia", "largo",
        "Neumonía con hipoperfusión: historia y examen detallados y estudio completo antes "
        "de tratar; antibiótico correcto pero tardío; se recupera.",
        [
            ("ask", "¿Desde cuándo tiene tos y fiebre? ¿Expectoración?"),
            ("ask", "¿Alergias a antibióticos? ¿Enfermedades previas?"),
            ("examine", "Breathing"),
            ("examine", "Peripheral perfusion"),
            ("order", "Pido rx de torax, hemocultivos, lactato y laboratorio basico"),
            ("order", "Reevaluo en 15 minutos"),
            ("order", "Creo que es una neumonia con sepsis e hipoperfusion, porque tiene fiebre "
                      "39.1, FR 30, sat 89% y llene de 4 s. Mi prioridad es antibiotico y oxigeno. "
                      "Doy ceftriaxona 2 g ev y azitromicina 500 mg ev; O2 por naricera 4 L/min; "
                      "SF 1000 ml ev. Espero que mejore la perfusion y suba la saturacion. "
                      "Reevaluo en 20 minutos perfusion y saturacion."),
            ("order", "Mejoro la perfusion y satura 94%. Mi prioridad es un destino con "
                      "vigilancia. La hospitalizo en sala. Espero que siga mejorando. Reevaluo "
                      "en 30 minutos."),
            ("answer", "Voy a mirar la saturacion, la FR y el llene capilar."),
        ],
        reflection={
            "working_model_update": "La hipoperfusión pedía antibiótico antes de completar el estudio.",
            "priority_trigger": "Llene capilar lento con fiebre debió disparar el antibiótico de inmediato.",
            "alternative_action": "Antibiótico y volumen en la primera entrega.",
            "expected_response_reassessment": "Reevalué perfusión y saturación después del tratamiento.",
        },
        plan={"cue": "Hipoperfusión con fiebre", "threshold": "Llene > 3 s", "next_priority": "Antibiótico en la primera hora",
              "alternative_action": "Vasoactivo si no responde al volumen", "expected_effect": "Mejor perfusión",
              "reassessment_plan": "Lactato de control"},
    ),
    _script(
        6, "opioid_35m", "opioid", "largo",
        "Depresión respiratoria: oxígeno primero, luego naloxona en dosis pequeñas repetidas "
        "hasta respuesta, con una pregunta al acompañante en medio; destino con observación.",
        [
            ("order", "Creo que es una depresion respiratoria por opioides, porque FR 6 y sat 80%. "
                      "Mi prioridad es oxigenar. Doy O2 por mascarilla de no recirculacion a 15 "
                      "L/min. Espero que suba la saturacion. Reevaluo en 5 minutos saturacion y FR."),
            ("ask", "¿Qué tomó? ¿Hace cuánto? ¿Tomó algo más?"),
            ("order", "Sigue con FR baja. Mi prioridad es revertir sin abstinencia. Doy naloxona "
                      "0.04 mg ev. Espero que suba la FR. Reevaluo en 3 minutos."),
            ("answer", "Voy a contar la frecuencia respiratoria y ver la saturacion."),
            ("order", "Doy naloxona 0.1 mg ev, reevaluo en 3 minutos FR"),
            ("complete", {"What do you expect": "Que suba la FR sin que despierte agitado"}),
            ("order", "Doy naloxona 0.4 mg ev. Espero FR sobre 12. Reevaluo en 5 minutos FR y "
                      "conciencia."),
            ("examine", "General appearance"),
            ("order", "Respira bien y esta despierto. Mi prioridad es vigilar la "
                      "renarcotizacion. Lo hospitalizo en intermedio con monitorizacion. Espero "
                      "que no vuelva a deprimirse. Reevaluo en 30 minutos FR y conciencia."),
        ],
        reflection={
            "working_model_update": "Era una intoxicación por opioides de duración incierta.",
            "priority_trigger": "Una FR menor de 10 me habría hecho ventilar con bolsa.",
            "alternative_action": "Ventilar con bolsa mascarilla antes de titular.",
            "expected_response_reassessment": "Conté la FR tras cada dosis.",
        },
        plan={"cue": "FR", "threshold": "< 10/min", "next_priority": "Ventilación antes que antagonista",
              "alternative_action": "Infusión de naloxona", "expected_effect": "FR > 12",
              "reassessment_plan": "FR y conciencia cada 15 min"},
    ),
    _script(
        7, "renal_colic_34m", "renal_colic", "largo",
        "Cólico renal: analgesia correcta, pero primero una imagen y dos preguntas; orina y "
        "temperatura antes del alta; alta con criterios de regreso.",
        [
            ("ask", "¿Cómo empezó el dolor? ¿Tiene fiebre o molestias al orinar?"),
            ("order", "Pido ecografia renal"),
            ("order", "Creo que es un colico renal derecho, porque el dolor es en oleadas y no "
                      "puede quedarse quieto. Mi prioridad es la analgesia. Doy ketorolaco 30 mg ev. "
                      "Espero que el dolor baje a menos de 4/10. Reevaluo en 20 minutos dolor."),
            ("order", "Pido examen de orina y temperatura"),
            ("order", "Reevaluo en 20 minutos"),
            ("order", "El dolor cedio, afebril y la orina no muestra infeccion. Mi prioridad es "
                      "un alta segura. Lo doy de alta con analgesia, control urologico y regresar "
                      "si tiene fiebre o dolor incontrolable. Espero que expulse el calculo. "
                      "Reevaluo en 15 minutos."),
        ],
        reflection={
            "working_model_update": "El cólico sin fiebre ni infección permitía el alta.",
            "priority_trigger": "Fiebre o infección urinaria me habrían hecho hospitalizar.",
            "alternative_action": "Analgesia antes de la imagen.",
            "expected_response_reassessment": "Reevalué el dolor y descarté infección antes del alta.",
        },
        plan={"cue": "Fiebre", "threshold": "T > 38", "next_priority": "Descartar infección obstructiva",
              "alternative_action": "Opioide si falla el AINE", "expected_effect": "Dolor < 4/10",
              "reassessment_plan": "Dolor cada 20 min"},
    ),
    _script(
        8, "pulmonary_edema_58m", "pulmonary_edema", "largo",
        "Edema pulmonar hipertensivo: oxígeno convencional primero con respuesta pobre, luego "
        "VMNI y nitroglicerina; un estudio en medio; mejora tarde.",
        [
            ("order", "Creo que es un edema pulmonar agudo, porque tiene PA 218/116, FR 38 y sat "
                      "81%. Mi prioridad es oxigenar. Doy O2 por mascarilla con reservorio a 15 "
                      "L/min. Espero que suba la saturacion. Reevaluo en 10 minutos."),
            ("complete", {"What will you check": "Saturacion, FR y esfuerzo respiratorio"}),
            ("order", "Pido rx de torax y POCUS"),
            ("order", "Sigue con sat 84% y mucho esfuerzo. Mi prioridad es soporte ventilatorio "
                      "y bajar la poscarga. Inicio VMNI CPAP 8 con FiO2 60%; nitroglicerina 50 "
                      "mcg/min ev. Espero que baje la FR y suba la sat. Reevaluo en 10 minutos FR, "
                      "saturacion y PA."),
            ("order", "Doy furosemida 40 mg ev"),
            ("answer", "Espero que aumente la diuresis y baje la congestion. Reevaluo en 20 "
                       "minutos diuresis y saturacion."),
            ("examine", "Breathing"),
            ("order", "Mejor: sat 93%, FR 24, PA 160/90. Mi prioridad es continuar el soporte en "
                      "un lugar monitorizado. Lo hospitalizo en la unidad coronaria. Espero que "
                      "siga bajando la congestion. Reevaluo en 30 minutos saturacion y PA."),
        ],
        reflection={
            "working_model_update": "Era un edema por poscarga; el oxígeno solo no bastaba.",
            "priority_trigger": "La saturación que no subía debió llevarme antes a VMNI.",
            "alternative_action": "VMNI y nitroglicerina desde la primera entrega.",
            "expected_response_reassessment": "Seguí FR, saturación y PA.",
        },
        plan={"cue": "Sat bajo 90 con oxígeno", "threshold": "Sin respuesta en 10 min", "next_priority": "VMNI",
              "alternative_action": "Intubación si falla", "expected_effect": "Menos esfuerzo",
              "reassessment_plan": "FR y sat cada 10 min"},
    ),
    # --- 4 · recuperacion -----------------------------------------------------
    _script(
        9, "acs_48m_wellens", "acs", "recuperacion",
        "Dolor que cedió: primero lo lee como atípico y espera una troponina sin antiagregar; "
        "al revisar el ECG reconoce el patrón de Wellens, antiagrega, anticoagula y pide "
        "cardiología. (Una prueba de esfuerzo aquí fibrila al paciente por decisión docente, "
        "así que no es un error del que se pueda volver.)",
        [
            ("ask", "¿Cómo era el dolor? ¿Cuánto duró cada episodio?"),
            ("order", "Pido ECG y troponina"),
            ("order", "Creo que puede ser dolor atipico sin isquemia activa, porque ahora esta "
                      "sin dolor. Mi prioridad es observar sin tratar todavia. Pido troponina de "
                      "control. Espero que salga negativa. Reevaluo en 30 minutos dolor."),
            ("order", "Revisando el ECG hay T negativas profundas en V2-V3: es un patron de "
                      "Wellens. Mi prioridad es tratarlo como sindrome coronario y NO provocar "
                      "esfuerzo. Doy aspirina 300 mg vo; heparina 5000 UI ev. Espero que no "
                      "reaparezca el dolor. Reevaluo en 15 minutos dolor y ECG."),
            ("order", "Consulto a cardiologia para coronariografia precoz"),
            ("answer", "Espero que la hagan hoy. Vigilo dolor y ECG cada 15 minutos."),
            ("order", "Sin dolor y estable. Mi prioridad es la coronariografia sin demora. Lo "
                      "hospitalizo en la unidad coronaria. Espero que no se ocluya antes. "
                      "Reevaluo en 30 minutos dolor y ECG."),
        ],
        reflection={
            "working_model_update": "El ECG de Wellens convierte un dolor que cedió en una estenosis crítica.",
            "priority_trigger": "Las T negativas profundas debieron cambiar el plan antes de pensar en esfuerzo.",
            "alternative_action": "Leer el ECG antes de decidir el estudio.",
            "expected_response_reassessment": "Vigilé dolor y ECG seriado.",
        },
        plan={"cue": "T negativas en V2-V3", "threshold": "Cualquier dolor nuevo", "next_priority": "Coronariografía",
              "alternative_action": "Anticoagulación plena", "expected_effect": "Sin recurrencia",
              "reassessment_plan": "ECG y troponina seriados"},
    ),
    _script(
        10, "hypoglycemia_76f", "hypoglycemia", "recuperacion",
        "Hipoglicemia corregida y alta decidida; antes de ejecutarla pregunta por los "
        "medicamentos, reconoce la sulfonilurea y cambia a observación con glucosa.",
        [
            ("order", "Pido glicemia capilar"),
            ("order", "Creo que es una hipoglicemia, porque esta obnubilada con glicemia baja. "
                      "Mi prioridad es corregirla. Instalo vvp; doy glucosa 25 g ev. Espero que "
                      "despierte. Reevaluo en 10 minutos conciencia y glicemia."),
            ("order", "Pido glicemia capilar"),
            ("ask", "¿Qué medicamentos toma para la diabetes?"),
            ("order", "Toma glibenclamida: puede volver a caer por horas. Mi prioridad es "
                      "evitar la recurrencia. Inicio infusion de glucosa al 10% a 100 ml/h y la "
                      "hospitalizo en sala para observacion con glicemia cada hora. Espero "
                      "glicemia sobre 100. Reevaluo en 30 minutos glicemia capilar."),
        ],
        reflection={
            "working_model_update": "No era sólo mala ingesta: la sulfonilurea explica la recurrencia.",
            "priority_trigger": "Saber el hipoglicemiante debió preceder cualquier plan de alta.",
            "alternative_action": "Octreotide si recurre pese a la glucosa.",
            "expected_response_reassessment": "Glicemia horaria en observación.",
        },
        plan={"cue": "Medicación hipoglicemiante", "threshold": "Sulfonilurea", "next_priority": "Observación prolongada",
              "alternative_action": "Octreotide", "expected_effect": "Sin recurrencia",
              "reassessment_plan": "Glicemia cada hora"},
    ),
    _script(
        11, "asthma_49m", "asthma", "recuperacion",
        "Asma grave con fatiga: broncodilata pero subestima la somnolencia; con los gases "
        "reconoce la falla ventilatoria y escala a soporte.",
        [
            ("order", "Creo que es una crisis asmatica, porque tiene sibilancias. Mi prioridad "
                      "es broncodilatar. Doy salbutamol 5 mg nbz + ipratropio 0,5 mg nbz. Espero "
                      "que ceda la obstruccion. Reevaluo en 20 minutos."),
            ("answer", "Voy a mirar la saturacion y las sibilancias."),
            ("order", "Pido gases arteriales"),
            ("order", "Reevaluo en 10 minutos"),
            ("order", "Los gases muestran retencion de CO2 y sigue somnoliento: es falla "
                      "ventilatoria. Mi prioridad es soporte ventilatorio. Inicio VMNI BiPAP "
                      "12/5 con FiO2 40%; doy hidrocortisona 200 mg ev. Espero que baje la PaCO2 "
                      "y despierte. Reevaluo en 15 minutos conciencia y gases."),
            ("order", "Consulto a UCI"),
            ("complete", {"What do you expect": "Que lo reciban para soporte ventilatorio "
                                                "monitorizado",
                          "What will you check": "Conciencia, FR y saturacion", "delay": 15}),
            ("order", "Lo hospitalizo en UCI"),
            ("answer", "Espero que siga mejorando con la VMNI. Reevaluo en 15 minutos conciencia "
                       "y FR."),
        ],
        reflection={
            "working_model_update": "La somnolencia y el silencio eran agotamiento, no mejoría.",
            "priority_trigger": "Somnolencia con asma debió disparar gases y soporte desde el inicio.",
            "alternative_action": "Preparar intubación en paralelo.",
            "expected_response_reassessment": "Gases de control y conciencia.",
        },
        plan={"cue": "Somnolencia", "threshold": "PaCO2 normal o alta", "next_priority": "Soporte ventilatorio",
              "alternative_action": "Intubación", "expected_effect": "Menos CO2",
              "reassessment_plan": "Gases en 30 min"},
    ),
    _script(
        12, "anaphylaxis_29f", "anaphylaxis", "recuperacion",
        "Anafilaxia: empieza con antihistamínico y corticoide; al no responder reconoce la "
        "anafilaxia y da adrenalina im, luego volumen; observación antes del destino.",
        [
            ("order", "Creo que es una reaccion alergica, porque tiene rash y edema facial. Mi "
                      "prioridad es controlar la alergia. Doy clorfenamina 10 mg ev y "
                      "hidrocortisona 200 mg ev. Espero que ceda el rash. Reevaluo en 10 minutos."),
            ("answer", "Veo si cede el rash y la hinchazon."),
            ("examine", "Breathing"),
            ("order", "Sigue hipotensa y con estridor: es una anafilaxia. Mi prioridad es la "
                      "adrenalina. Doy adrenalina 0.5 mg im; SF 1000 ml ev en bolo; O2 por "
                      "mascarilla 10 L/min. Espero que suba la PA y ceda el estridor. Reevaluo "
                      "en 5 minutos PA y estridor."),
            ("order", "Mejora parcial. Doy adrenalina 0.5 mg im. Reevaluo en 5 minutos PA y estridor."),
            ("answer", "Espero que termine de subir la presion y desaparezca el estridor."),
            ("order", "Estable, sin estridor y PA normal. Mi prioridad es observar la reaccion "
                      "bifasica. La dejo en observacion 6 horas y le indico autoinyector al alta. "
                      "Espero que no recurra. Reevaluo en 30 minutos PA y via aerea."),
        ],
        reflection={
            "working_model_update": "Hipotensión y estridor tras una exposición son anafilaxia: adrenalina primero.",
            "priority_trigger": "La hipotensión debió llevarme a la adrenalina en la primera entrega.",
            "alternative_action": "Adrenalina im antes que antihistamínicos.",
            "expected_response_reassessment": "PA y estridor cada 5 min.",
        },
        plan={"cue": "Hipotensión tras exposición", "threshold": "PAS < 90", "next_priority": "Adrenalina im",
              "alternative_action": "Infusión de adrenalina", "expected_effect": "PA recuperada",
              "reassessment_plan": "PA cada 5 min"},
    ),
    # --- 4 · equivocado -------------------------------------------------------
    _script(
        13, "opioid_67f", "opioid", "equivocado",
        "Revierte bien la depresión respiratoria pero da el alta sin observar un opioide de "
        "larga acción que nunca preguntó.",
        [
            ("order", "Creo que es una depresion respiratoria por opioides, porque FR 8 y sat "
                      "84%. Mi prioridad es ventilar. Ventilo con bolsa mascarilla con O2 100%. "
                      "Espero sat sobre 94%. Reevaluo en 5 minutos saturacion y FR."),
            ("order", "Mi prioridad es revertir. Doy naloxona 0.4 mg ev. Espero FR sobre 12. "
                      "Reevaluo en 5 minutos FR."),
            ("examine", "General appearance"),
            ("order", "Desperto y respira bien. Mi prioridad es liberar el box. La envio a su "
                      "casa con su esposo. Espero que no se repita. Reevaluo en 15 minutos."),
            ("answer", "Reviso que siga despierta antes de que se vaya."),
        ],
        reflection={
            "working_model_update": "Revertí sin saber qué opioide era.",
            "priority_trigger": "Una FR que vuelve a bajar me habría hecho repetir la naloxona.",
            "alternative_action": "Preguntar el fármaco y su formulación antes del destino.",
            "expected_response_reassessment": "Pedí volver si se repetía.",
        },
        plan={"cue": "Formulación del opioide", "threshold": "Liberación prolongada", "next_priority": "Observación",
              "alternative_action": "Infusión de naloxona", "expected_effect": "Sin renarcotización",
              "reassessment_plan": "FR cada 30 min por horas"},
    ),
    _script(
        14, "pulmonary_embolism_61m", "pulmonary_embolism", "equivocado",
        "TEP con shock: da volumen repetido y espera la tomografía; no anticoagula ni "
        "reperfunde mientras la presión sigue baja.",
        [
            ("order", "Creo que es un shock hipovolemico, porque esta hipotenso y taquicardico. "
                      "Mi prioridad es volumen. Paso SF 1000 ml ev en bolo. Espero que suba la "
                      "PA. Reevaluo en 15 minutos PA."),
            ("order", "Pido angiotomografia de torax y dimero D"),
            ("order", "Sigue hipotenso. Mi prioridad es mas volumen. Paso SF 1000 ml ev. Espero "
                      "PAS sobre 90. Reevaluo en 15 minutos PA y FC."),
            ("order", "Pido POCUS"),
            ("order", "El VD esta dilatado; espero la tomografia antes de decidir. Mi prioridad "
                      "es confirmar. Doy O2 por naricera 3 L/min. Espero que la sat suba. "
                      "Reevaluo en 20 minutos."),
            ("answer", "Voy a mirar la saturacion."),
            ("order", "Lo hospitalizo en UCI"),
            ("answer", "Espero que alli lo estabilicen. Reevaluo PA en 10 minutos."),
        ],
        reflection={
            "working_model_update": "No era hipovolemia: el VD dilatado era un shock obstructivo.",
            "priority_trigger": "El POCUS debió cambiar el plan hacia anticoagulación y reperfusión.",
            "alternative_action": "Anticoagular y considerar trombolisis ante hipotensión sostenida.",
            "expected_response_reassessment": "PA tras cada bolo.",
        },
        plan={"cue": "VD dilatado", "threshold": "Hipotensión sostenida", "next_priority": "Reperfusión",
              "alternative_action": "Trombolisis", "expected_effect": "PA estable",
              "reassessment_plan": "PA cada 10 min"},
    ),
    _script(
        15, "gi_bleed_72f", "gi_bleed", "equivocado",
        "Anemia por pérdida digestiva tratada como problema crónico: estudia y consulta sin "
        "reanimar, hospitaliza en sala mientras la perfusión empeora.",
        [
            ("ask", "¿Ha notado deposiciones negras? ¿Qué medicamentos toma?"),
            ("order", "Creo que es una anemia cronica, porque refiere cansancio de dias. Mi "
                      "prioridad es estudiar. Pido hemoglobina y laboratorio basico. Espero una "
                      "hemoglobina baja. Reevaluo en 20 minutos."),
            ("order", "Doy omeprazol 40 mg ev"),
            ("answer", "Espero proteger la mucosa. Reviso la hemoglobina en 30 minutos."),
            ("order", "Consulto a gastroenterologia"),
            ("complete", {"What do you expect": "Que programen una endoscopia",
                          "What will you check": "Hemoglobina de control", "delay": 30}),
            ("order", "La hospitalizo en sala"),
            ("answer", "Espero que la estudien. Reviso la hemoglobina mañana."),
        ],
        reflection={
            "working_model_update": "Era un sangrado activo con hipoperfusión, no una anemia crónica.",
            "priority_trigger": "El llene capilar lento debió hacerme reanimar.",
            "alternative_action": "Volumen y transfusión precoz.",
            "expected_response_reassessment": "Hemoglobina de control.",
        },
        plan={"cue": "Llene capilar", "threshold": "> 3 s", "next_priority": "Reanimación",
              "alternative_action": "Transfusión", "expected_effect": "Mejor perfusión",
              "reassessment_plan": "PA/FC cada 15 min"},
    ),
    _script(
        16, "bradycardia_ccb_68m", "bradycardia", "equivocado",
        "Bradicardia con shock por bloqueador de calcio: atropina repetida sin preguntar por "
        "los medicamentos; tarda en buscar la causa y no da antídoto.",
        [
            ("order", "Creo que es una bradicardia sintomatica, porque FC 38 y PA 74/44. Mi "
                      "prioridad es subir la frecuencia. Doy atropina 1 mg ev. Espero FC sobre "
                      "50. Reevaluo en 5 minutos FC y PA."),
            ("order", "Doy atropina 1 mg ev. Reevaluo en 5 minutos."),
            ("answer", "Espero que suba la FC. Miro FC y PA."),
            ("order", "Pido laboratorio basico y ECG"),
            ("order", "Sigue con FC 40. Mi prioridad es la presion. Paso SF 500 ml ev. Espero "
                      "PAS sobre 90. Reevaluo en 10 minutos PA y FC."),
            ("order", "Consulto a cardiologia para marcapaso"),
            ("complete", {"What do you expect": "Que instalen un marcapaso",
                          "What will you check": "FC y PA", "delay": 10}),
        ],
        reflection={
            "working_model_update": "La bradicardia refractaria tenía una causa tóxica que no busqué.",
            "priority_trigger": "La falta de respuesta a la atropina debió hacerme preguntar por los medicamentos.",
            "alternative_action": "Calcio y glucagón; marcapaso transcutáneo.",
            "expected_response_reassessment": "FC y PA tras cada intervención.",
        },
        plan={"cue": "Atropina sin respuesta", "threshold": "Dos dosis", "next_priority": "Buscar la causa",
              "alternative_action": "Antídoto", "expected_effect": "FC > 50",
              "reassessment_plan": "FC y PA cada 5 min"},
    ),
    # --- 2 · deficiente -------------------------------------------------------
    _script(
        17, "pneumonia_83m", "pneumonia", "deficiente",
        "Sigue la nota de 'deshidratación': da volumen repetido, no busca la causa de la "
        "somnolencia ni da antibiótico; deja pasar las reevaluaciones.",
        [
            ("order", "Creo que esta deshidratado, porque la nota dice que come poco. Mi "
                      "prioridad es hidratar. Paso SF 1000 ml ev. Espero que despierte. Reevaluo "
                      "en 30 minutos."),
            ("answer", "Voy a ver si despierta."),
            ("order", "Paso SF 1000 ml ev. Reevaluo en 30 minutos."),
            ("answer", "Espero que se hidrate. Veo si despierta."),
            ("order", "Pido laboratorio basico"),
            ("order", "Lo hospitalizo en sala para hidratacion"),
            ("answer", "Espero que se hidrate en la sala. Reviso la hidratacion mañana."),
        ],
        reflection={
            "working_model_update": "Seguí la hipótesis de la nota sin probarla.",
            "priority_trigger": "La fiebre y la saturación baja debían hacerme pensar en infección.",
            "alternative_action": "Glicemia, radiografía y antibiótico.",
            "expected_response_reassessment": "Esperaba que despertara con volumen.",
        },
        plan={"cue": "Somnolencia nueva", "threshold": "Cualquier alteración de conciencia", "next_priority": "Buscar la causa",
              "alternative_action": "Antibiótico precoz", "expected_effect": "Mejor conciencia",
              "reassessment_plan": "Conciencia y perfusión cada 15 min"},
    ),
    _script(
        18, "acs_66f_nonst", "acs", "deficiente",
        "Opresión torácica leída como ansiedad: sin ECG a tiempo, benzodiacepina, prueba de "
        "esfuerzo pedida; no antiagrega.",
        [
            ("order", "Creo que es ansiedad, porque esta taquicardica y nerviosa. Mi prioridad "
                      "es calmarla. Doy lorazepam 1 mg vo. Espero que baje la FC. Reevaluo en 30 "
                      "minutos."),
            ("order", "Pido prueba de esfuerzo"),
            ("order", "Pido ECG"),
            ("order", "La doy de alta con control ambulatorio"),
            ("answer", "Es ansiedad. Espero que se calme en la casa. Reviso los sintomas en el "
                       "control del policlinico en una semana."),
        ],
        reflection={
            "working_model_update": "Etiqueté de ansiedad un dolor opresivo con disnea.",
            "priority_trigger": "El ECG debió ser lo primero.",
            "alternative_action": "ECG en 10 minutos y aspirina.",
            "expected_response_reassessment": "Esperaba que se calmara.",
        },
        plan={"cue": "Dolor torácico opresivo", "threshold": "Cualquier cambio en el ECG", "next_priority": "ECG precoz",
              "alternative_action": "Aspirina", "expected_effect": "Isquemia tratada",
              "reassessment_plan": "ECG y troponina seriados"},
    ),
    # --- 2 · alternativa ------------------------------------------------------
    _script(
        19, "anaphylaxis_63m_betablocked", "anaphylaxis", "alternativa",
        "Anafilaxia refractaria en paciente betabloqueado: adrenalina, luego pregunta los "
        "medicamentos y usa glucagón e infusión de adrenalina.",
        [
            ("order", "Creo que es una anafilaxia por la picadura, porque tiene sibilancias, "
                      "rash y PA 76/42. Mi prioridad es la adrenalina. Doy adrenalina 0.5 mg im; "
                      "SF 1000 ml ev; O2 por mascarilla 10 L/min. Espero que suba la PA. "
                      "Reevaluo en 5 minutos PA y sibilancias."),
            ("order", "Doy adrenalina 0.5 mg im. Reevaluo en 5 minutos PA."),
            ("answer", "Espero que ahora si suba la presion."),
            ("ask", "¿Qué medicamentos toma? ¿Toma algo para la presión o el corazón?"),
            ("order", "Toma betabloqueador, por eso no responde. Mi prioridad es sortear el "
                      "bloqueo. Doy glucagon 1 mg ev; inicio adrenalina en infusion a 0.1 "
                      "mcg/kg/min. Espero que suba la PA. Reevaluo en 10 minutos PA y FC."),
            ("order", "Lo hospitalizo en UCI"),
            ("answer", "Espero que siga estable con la infusion. Reevaluo en 15 minutos PA."),
        ],
        reflection={
            "working_model_update": "La falta de respuesta tenía una causa: el betabloqueador.",
            "priority_trigger": "Dos dosis sin respuesta me hicieron buscar la causa.",
            "alternative_action": "Infusión de adrenalina antes del glucagón.",
            "expected_response_reassessment": "PA y FC cada 5 min.",
        },
        plan={"cue": "Adrenalina sin respuesta", "threshold": "Dos dosis", "next_priority": "Buscar betabloqueo",
              "alternative_action": "Glucagón", "expected_effect": "PA recuperada",
              "reassessment_plan": "PA cada 5 min"},
    ),
    _script(
        20, "pulmonary_embolism_33f", "pulmonary_embolism", "alternativa",
        "TEP probable sin shock: anticoagula antes de confirmar por alta sospecha clínica, "
        "con una recuperación de sesión en medio y resultados pendientes.",
        [
            ("ask", "¿Ha tenido cirugías recientes, viajes o dolor en una pierna?"),
            ("order", "Creo que es un tromboembolismo pulmonar, porque tiene disnea subita, "
                      "dolor pleuritico, FC 124 y sat 90%. Mi prioridad es anticoagular sin "
                      "esperar la imagen. Doy enoxaparina 60 mg sc; O2 por naricera 3 L/min; "
                      "pido angiotomografia. Espero que suba la sat y no empeore. Reevaluo en "
                      "20 minutos saturacion y FC."),
            ("recover",),
            ("examine", "Peripheral perfusion"),
            ("order", "Pido troponina"),
            ("order", "Estable, sat 95% con oxigeno. Mi prioridad es un destino monitorizado. La "
                      "hospitalizo en sala con anticoagulacion porque es un TEP sin shock. Espero "
                      "que se mantenga estable. Reevaluo en 30 minutos saturacion y PA."),
        ],
        reflection={
            "working_model_update": "Con alta probabilidad clínica anticoagulé antes de la imagen.",
            "priority_trigger": "Una hipotensión me habría hecho considerar trombolisis.",
            "alternative_action": "Esperar la angiotomografía si la sospecha fuera baja.",
            "expected_response_reassessment": "Saturación y PA.",
        },
        plan={"cue": "Hipotensión", "threshold": "PAS < 90", "next_priority": "Reperfusión si hay shock",
              "alternative_action": "Heparina no fraccionada", "expected_effect": "Estable",
              "reassessment_plan": "Sat y PA cada 30 min"},
    ),
]

BY_NUMBER = {script["number"]: script for script in SCRIPTS}
BY_CASE = {script["case_id"]: script for script in SCRIPTS}
