"""Spanish drafts awaiting the faculty's review (cycle 10, C10-08). None of them is shown.

Two sets, reviewed together in packet R-4 (``docs/revision/ES_BORRADORES.md``):

* ``ENGINE``: sentences the engine composes that a Spanish reader still sees in
  English, or half in English (the rest of DF-23 row 11), found by playing the
  room offline (``tools_engine_spanish``). Each carries its English with the
  numbers written ``{n}`` and the resident's quoted words ``«…»``;
* ``C14``: the reason, the component and the expected evidence each bank case
  declares for C14, shown in English on the Spanish faculty portal (TD-07),
  keyed by the exact English they translate.

Nothing reads these into the room, the documents or the portal. A Spanish line
reaches a reader only once a faculty member approves it and a later, recorded
change moves it into ``language`` or the portal; ``test_spanish_drafts.py``
keeps it so, and says when a draft no longer matches the English it translates.
"""
STATUS = "draft_pending_faculty_review"

#: The offline harvest this set comes from (``tools_engine_spanish --harvest``, 2026-09-29): the
#: twenty rehearsal scripts and a probe of the eleven cases they do not play. Of the templates
#: that still read in English, 4 are the engine's own sentences (below), 4 are a case's POCUS
#: mixed word by word before its narrative is approved (TD-46) and 2 are the neurological
#: finding quoting the case's own words, which its approval translates.
HARVEST = {"date": "2026-09-29", "runs": 31, "entries": 583, "templates": 10,
           "engine": 4, "narrative_mixed": 4, "narrative_quoted": 2}

#: The English the room shows, with the Spanish proposed for it: the inventory
#: ``tools_engine_spanish`` wrote from the played room, and the examination findings
#: the engine composes that the harvest did not reach (``seen`` False, found in
#: ``family_engine.current_findings``). ``kind`` is how the room presents it:
#: ``language.say`` for an entry, ``language.examination`` for the examination panel.
ENGINE = (
    {"kind": "clinical_update", "cases": ["trauma_limb_hemorrhage_27m", "trauma_hemothorax_41m"], "seen": True,
     "english": "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume "
                "replaces a source that is still open.",
     "example": "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume "
                "replaces a source that is still open.",
     "spanish": "Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido, y ningún "
                "volumen reemplaza una fuente que sigue abierta.",
     "note": "trauma_hemorrhage.ARREST_TEXT; también como procedimiento"},
    {"kind": "examination", "cases": ["pulmonary_edema_75f"], "seen": True,
     "english": "Bilateral inspiratory crackles with increased respiratory effort.",
     "example": "Bilateral inspiratory crackles with increased respiratory effort.",
     "spanish": "Crépitos inspiratorios bilaterales, con aumento del esfuerzo respiratorio.",
     "note": "family_engine.current_findings, edema pulmonar"},
    {"kind": "examination", "cases": ["pulmonary_edema"], "seen": False,
     "english": "Bilateral crackles remain, with reduced respiratory effort.",
     "example": "Bilateral crackles remain, with reduced respiratory effort.",
     "spanish": "Persisten crépitos bilaterales, con menor esfuerzo respiratorio.",
     "note": "family_engine.current_findings, edema pulmonar"},
    {"kind": "examination", "cases": ["transfusión en cualquier familia"], "seen": False,
     "english": "New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze.",
     "example": "New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze.",
     "spanish": "Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin "
                "sibilancias.",
     "note": "family_engine.current_findings, sobrecarga por transfusión"},
    {"kind": "examination", "cases": ["asthma"], "seen": False,
     "english": "Improved air entry with residual expiratory wheeze.",
     "example": "Improved air entry with residual expiratory wheeze.",
     "spanish": "Mejor entrada de aire, con sibilancias espiratorias residuales.",
     "note": "family_engine.current_findings, asma"},
    {"kind": "examination", "cases": ["asthma"], "seen": False,
     "english": "Reduced bilateral air entry with prolonged expiration and wheeze.",
     "example": "Reduced bilateral air entry with prolonged expiration and wheeze.",
     "spanish": "Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias.",
     "note": "family_engine.current_findings, asma"},
    {"kind": "examination", "cases": ["asthma"], "seen": False,
     "english": "Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side.",
     "example": "Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side.",
     "spanish": "Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado.",
     "note": "neumotórax del asma; igual con «left» → «izquierdo»"},
    {"kind": "examination", "cases": ["asthma"], "seen": False,
     "english": "Breath sounds returning on the right after decompression; improved air entry with residual "
                "expiratory wheeze.",
     "example": "Breath sounds returning on the right after decompression; improved air entry with residual "
                "expiratory wheeze.",
     "spanish": "Vuelve el murmullo pulmonar en el lado derecho después de la descompresión; mejor entrada de aire, "
                "con sibilancias espiratorias residuales.",
     "note": "neumotórax descomprimido; «left» → «izquierdo», y la segunda parte es cualquiera de las dos del asma"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n} /min; assisted ventilation is in progress.",
     "example": "Respiratory rate 8 /min; assisted ventilation is in progress.",
     "spanish": "Frecuencia respiratoria {n}/min; se está dando ventilación asistida.",
     "note": "family_engine.current_findings, opioides"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n} /min; breaths remain shallow.",
     "example": "Respiratory rate 6 /min; breaths remain shallow.",
     "spanish": "Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales.",
     "note": "family_engine.current_findings, opioides"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n} /min; spontaneous breaths have greater depth.",
     "example": "Respiratory rate 14 /min; spontaneous breaths have greater depth.",
     "spanish": "Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas.",
     "note": "family_engine.current_findings, opioides"},
    # The access findings (glucose_rescue.access_finding): language already says them in
    # Spanish in an entry; the examination panel, where they are read, does not.
    {"kind": "examination", "cases": ["hypoglycemia_54m_thiamine"], "seen": True,
     "english": "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.",
     "example": "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; la piel alrededor de su punta está levemente hinchada "
                "y fría.",
     "note": "vía fallida antes de usarla; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.",
     "example": "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni "
                "dolor.",
     "note": "vía que funciona; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.",
     "example": "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está hinchado, pálido, "
                "frío y doloroso.",
     "note": "vía fallida ya usada; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "A second peripheral cannula in the right forearm; the site is clean.",
     "example": "A second peripheral cannula in the right forearm; the site is clean.",
     "spanish": "Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio.",
     "note": "vía nueva; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "An intraosseous needle in place (humeral).",
     "example": "An intraosseous needle in place (humeral).",
     "spanish": "Una aguja intraósea instalada (humeral).",
     "note": "también tibial, esternal o femoral; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "An intraosseous needle in place; no site was recorded.",
     "example": "An intraosseous needle in place; no site was recorded.",
     "spanish": "Una aguja intraósea instalada; no se registró el sitio.",
     "note": "el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm.",
     "example": "Dextrose 10% runs at 100 mL/h through the cannula in the left forearm.",
     "spanish": "La glucosa al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo.",
     "note": "también por la cánula nueva del antebrazo derecho o por la aguja intraósea; el español ya está en "
             "language, no en el panel"},
)

#: R-4 (faculty, 2026-09-30): the 18 engine sentences are reviewed first, one by one. For each, the AI
#: Advisor's reading for that review: the clinical moment it describes, a recommendation and the
#: ambiguity a Spanish reader could meet. A proposal like the drafts themselves: nothing here is shown.
ENGINE_REVIEW = {
    "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume "
    "replaces a source that is still open.": (
        "Final del trauma cuando el sangrado nunca se controló (entrada de la sala)",
        "Cambiar: «ningún volumen compensa un foco de sangrado que sigue activo»",
        "«Fuente» no es la palabra habitual para el origen de un sangrado; «foco» sí"),
    "Bilateral inspiratory crackles with increased respiratory effort.": (
        "Edema pulmonar (75f) al examinar, antes de tratar",
        "Aprobar",
        "Ninguna; «crépitos» es el uso local"),
    "Bilateral crackles remain, with reduced respiratory effort.": (
        "Edema pulmonar que mejora con el tratamiento",
        "Aprobar, o precisar que el esfuerzo bajó por mejoría",
        "«Menor esfuerzo» también puede leerse como agotamiento; el inglés tiene la misma ambigüedad"),
    "New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze.": (
        "Sobrecarga circulatoria por transfusión, en cualquier familia",
        "Aprobar",
        "Ninguna"),
    "Improved air entry with residual expiratory wheeze.": (
        "Asma que mejora con broncodilatadores",
        "Aprobar",
        "Ninguna; «entrada de aire» es de uso clínico común"),
    "Reduced bilateral air entry with prolonged expiration and wheeze.": (
        "Crisis asmática al llegar o sin respuesta",
        "Aprobar",
        "Ninguna"),
    "Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side.": (
        "Asma complicada con neumotórax (derecho o izquierdo)",
        "Aprobar",
        "«En el otro lado» es claro; «en el hemitórax contralateral» sería más formal"),
    "Breath sounds returning on the right after decompression; improved air entry with residual expiratory "
    "wheeze.": (
        "Neumotórax del asma después de la descompresión",
        "Cambiar: «Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; …»",
        "«Vuelve el murmullo» se entiende, pero «reaparece» es la forma habitual"),
    "Respiratory rate {n} /min; assisted ventilation is in progress.": (
        "Intoxicación por opioides durante la ventilación con bolsa y mascarilla",
        "Cambiar: «Frecuencia respiratoria {n}/min; con ventilación asistida en curso»",
        "No dice si la frecuencia es la espontánea o la asistida; el inglés tampoco. «Se está dando» es "
        "coloquial"),
    "Respiratory rate {n} /min; breaths remain shallow.": (
        "Intoxicación por opioides con hipoventilación persistente",
        "Aprobar",
        "Ninguna"),
    "Respiratory rate {n} /min; spontaneous breaths have greater depth.": (
        "Intoxicación por opioides que responde a la naloxona",
        "Aprobar",
        "Ninguna; «más profundas» se lee respecto del examen anterior"),
    "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.": (
        "Hipoglicemia (54m): la vía de llegada infiltrada antes de usarla, la pista que el residente puede "
        "notar",
        "Cambiar: «…la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría», "
        "y lo mismo en language para que el panel y la sala digan lo mismo",
        "«Hinchada» (aquí y en la 14) y «aumento de volumen» (en la 13) nombran el mismo signo con palabras "
        "distintas"),
    "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.": (
        "Hipoglicemia: la vía que funciona",
        "Cambiar: «…sin aumento de volumen ni dolor a la palpación»",
        "«Tenderness» es dolor a la palpación, no dolor espontáneo"),
    "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.": (
        "Hipoglicemia: la vía fallida después de pasar la glucosa (extravasación)",
        "Cambiar: «…aumentado de volumen, pálido, frío y doloroso a la palpación»",
        "La misma de las filas 12 y 13"),
    "A second peripheral cannula in the right forearm; the site is clean.": (
        "Hipoglicemia: la vía nueva que instaló el residente",
        "Aprobar",
        "Ninguna"),
    "An intraosseous needle in place (humeral).": (
        "Hipoglicemia: acceso intraóseo (también tibial, esternal o femoral)",
        "Aprobar",
        "Ninguna; «instalada» es el uso local, y «colocada» también serviría"),
    "An intraosseous needle in place; no site was recorded.": (
        "Hipoglicemia: acceso intraóseo sin sitio registrado",
        "Aprobar",
        "Ninguna"),
    "Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm.": (
        "Hipoglicemia: la infusión de glucosa en curso",
        "Cambiar: «Suero glucosado al {n} % a {n} mL/h por la cánula del antebrazo izquierdo»",
        "En un caso de hipoglicemia, «la glucosa» se confunde con la glicemia del paciente"),
}

#: The C14 declarations of the bank (``case_assessment_bank``), English -> Spanish draft.
C14 = {
    # acs_54m_inferior
    "The encounter does not create a meaningful opportunity to observe POCUS-guided management: recognising right "
    "ventricular involvement through the available POCUS is not an expectation the ACEP 2016 emergency ultrasound "
    "guideline used here establishes (pp. 25, 29), and the nitrate, antiplatelet and cautious-volume decisions are "
    "driven mainly by the ECG, the right-sided leads (V4R) and the haemodynamic context rather than by the POCUS "
    "finding.":
        "El encuentro no crea una oportunidad significativa de observar un manejo guiado por POCUS: reconocer el "
        "compromiso del ventrículo derecho con el POCUS disponible no es una expectativa que establezca la guía de "
        "ecografía de urgencia ACEP 2016 usada aquí (pp. 25, 29), y las decisiones sobre el nitrato, el antiplaquetario "
        "y el volumen cauteloso dependen sobre todo del ECG, de las derivaciones derechas (V4R) y del contexto "
        "hemodinámico, no del hallazgo del POCUS.",
    # acs_66f_nonst
    "The acute coronary syndrome is already established by the ECG and a troponin of 180 ng/L; the mild "
    "inferolateral hypokinesis does not change the pathway, with no occlusion and an angiography that can wait "
    "(decision A).":
        "El síndrome coronario agudo ya está establecido por el ECG y una troponina de 180 ng/L; la hipocinesia "
        "inferolateral leve no cambia la ruta, sin oclusión y con una coronariografía que puede esperar (decisión A).",
    # acs_61m_posterior
    "ST depression in V1-V3 with posterior hypokinesis on POCUS: the regional wall motion can prioritise reperfusion "
    "for an occlusion the 12-lead understates (decision A); in the engine the wall motion evolves with the ischaemic "
    "minutes.":
        "Infradesnivel del ST en V1-V3 con hipocinesia posterior en el POCUS: la motilidad regional puede priorizar la "
        "reperfusión de una oclusión que el ECG de 12 derivaciones subestima (decisión A); en el motor, la motilidad "
        "evoluciona con los minutos de isquemia.",
    "Using regional wall motion to prioritise the reperfusion decision.":
        "Usar la motilidad regional para priorizar la decisión de reperfusión.",
    "requests POCUS and names the posterior hypokinesis":
        "solicita POCUS y nombra la hipocinesia posterior",
    "uses it with the ECG and the posterior leads to treat the pattern as an occlusion":
        "la usa junto con el ECG y las derivaciones posteriores para tratar el patrón como una oclusión",
    "activates or expedites reperfusion":
        "activa o acelera la reperfusión",
    # acs_52m_de_winter
    "Akinesis of the anterior wall and apex supports treating the de Winter pattern as an anterior occlusion "
    "(decision A); in the engine the wall motion evolves with the ischaemic minutes.":
        "La acinesia de la pared anterior y del ápex apoya tratar el patrón de de Winter como una oclusión anterior "
        "(decisión A); en el motor, la motilidad evoluciona con los minutos de isquemia.",
    "requests POCUS and names the anterior akinesis":
        "solicita POCUS y nombra la acinesia anterior",
    "relates it to the ECG pattern as an occlusion":
        "la relaciona con el patrón del ECG como una oclusión",
    # acs_48m_wellens
    "The right decision -- angiography and no provocation test -- does not depend on POCUS, and a normal resting "
    "POCUS cannot reasonably guide it. Not being reassured by it is diagnostic reasoning, not C14 (decision B).":
        "La decisión correcta —coronariografía y ninguna prueba de provocación— no depende del POCUS, y un POCUS "
        "normal en reposo no puede guiarla razonablemente. No tranquilizarse por él es razonamiento diagnóstico, no "
        "C14 (decisión B).",
    # acs_70f_left_main
    "Borderline pressure with globally reduced contraction on POCUS: the global LV function, a state the EPA lists, "
    "is what should limit volume and prompt early support while reperfusion is arranged; the engine answers volume "
    "poorly in this profile.":
        "Presión limítrofe con contracción globalmente disminuida en el POCUS: la función global del VI, un estado "
        "que la EPA enumera, es lo que debe limitar el volumen y motivar un soporte precoz mientras se coordina la "
        "reperfusión; en este perfil, el motor responde mal al volumen.",
    "Deciding volume, support and urgency from the global LV function.":
        "Decidir el volumen, el soporte y la urgencia a partir de la función global del VI.",
    "requests POCUS and names the globally reduced contraction":
        "solicita POCUS y nombra la contracción globalmente disminuida",
    "limits or withholds volume, or escalates support, because of it":
        "limita o suspende el volumen, o escala el soporte, por ese hallazgo",
    "relates it to the urgency of reperfusion":
        "lo relaciona con la urgencia de la reperfusión",
    # asthma_24f, asthma_49m
    "Bronchodilation does not depend on POCUS. A pneumothorax appears only after ventilation with sustained high "
    "plateau pressures, and its event already names the diagnosis, so a POCUS would only confirm it (decision D). "
    "Redesigning that event is a separate case decision.":
        "La broncodilatación no depende del POCUS. Un neumotórax aparece sólo después de ventilar con presiones meseta "
        "altas y sostenidas, y su evento ya nombra el diagnóstico, así que un POCUS sólo lo confirmaría (decisión D). "
        "Rediseñar ese evento es otra decisión del caso.",
    # gi_bleed_57m
    "Haemorrhagic shock (88/54) with a small hyperdynamic LV and a near-completely collapsing IVC: the volume "
    "assessment is a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with "
    "volume and blood (decision C).":
        "Shock hemorrágico (88/54) con un VI pequeño e hiperdinámico y una VCI que colapsa casi por completo: la "
        "evaluación del volumen es un objetivo de la reanimación junto con la transfusión, y una ecografía repetida "
        "muestra la VCI llenándose con volumen y sangre (decisión C).",
    "Using the POCUS volume assessment to guide and reassess resuscitation.":
        "Usar la evaluación del volumen por POCUS para guiar y reevaluar la reanimación.",
    "requests POCUS and names the empty, hyperdynamic LV and the collapsed IVC":
        "solicita POCUS y nombra el VI vacío e hiperdinámico y la VCI colapsada",
    "relates them to transfusion or volume":
        "los relaciona con la transfusión o el volumen",
    "reassesses with POCUS after resuscitation":
        "reevalúa con POCUS después de la reanimación",
    # gi_bleed_72f
    "Hypotension from bleeding (98/62) with a hyperdynamic LV and a 1.1 cm collapsing IVC: the volume assessment is "
    "a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with volume and "
    "blood (decision C).":
        "Hipotensión por sangrado (98/62) con un VI hiperdinámico y una VCI de 1,1 cm que colapsa: la evaluación del "
        "volumen es un objetivo de la reanimación junto con la transfusión, y una ecografía repetida muestra la VCI "
        "llenándose con volumen y sangre (decisión C).",
    "requests POCUS and names the hyperdynamic LV and the collapsing IVC":
        "solicita POCUS y nombra el VI hiperdinámico y la VCI que colapsa",
    # hypoglycemia_28m, hypoglycemia_76f, hypoglycemia_54m_thiamine
    "The capillary glucose and the glucose treat it; the POCUS adds nothing to the management.":
        "Se maneja con la glicemia capilar y la glucosa; el POCUS no agrega nada al manejo.",
    "The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. The thiamine is "
    "decided by the history.":
        "Se maneja con la glicemia capilar y la glucosa; el POCUS no agrega nada al manejo. La tiamina se decide por "
        "la historia.",
    # opioid_35m, opioid_67f
    "Opioid respiratory depression is treated with naloxone and ventilation; the POCUS adds nothing to the "
    "management.":
        "La depresión respiratoria por opioides se trata con naloxona y ventilación; el POCUS no agrega nada al manejo.",
    # pneumonia_46f
    "Septic hypotension (92/58) with a 1.0 cm collapsing IVC, a vigorous LV and no diffuse B-lines: POCUS can select "
    "and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with volume "
    "(decision C). The consolidation may be named but does not by itself make the opportunity (decision F): one "
    "opportunity for the case.":
        "Hipotensión séptica (92/58) con una VCI de 1,0 cm que colapsa, un VI vigoroso y sin líneas B difusas: el "
        "POCUS puede elegir y titular la estrategia de fluidos y decidir el momento del vasopresor, y una ecografía "
        "repetida muestra la VCI llenándose con volumen (decisión C). La consolidación puede nombrarse, pero no crea "
        "por sí sola la oportunidad (decisión F): una oportunidad para el caso.",
    "Guiding and reassessing the fluid and haemodynamic strategy with POCUS.":
        "Guiar y reevaluar con POCUS la estrategia de fluidos y hemodinámica.",
    "requests POCUS and names the volume findings (the IVC and the LV)":
        "solicita POCUS y nombra los hallazgos de volemia (la VCI y el VI)",
    "gives, limits or titrates volume, or moves to a vasopressor, because of them":
        "da, limita o titula el volumen, o pasa a un vasopresor, por esos hallazgos",
    "reassesses with POCUS after volume":
        "reevalúa con POCUS después del volumen",
    # pneumonia_83m
    "An older patient referred as dehydrated, 96/60 with a 1.2 cm collapsing IVC and a preserved LV: POCUS can "
    "select and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with "
    "volume (decision C). The consolidation may be named but does not by itself make the opportunity (decision F): "
    "one opportunity for the case.":
        "Paciente mayor derivado como deshidratado, 96/60, con una VCI de 1,2 cm que colapsa y un VI conservado: el "
        "POCUS puede elegir y titular la estrategia de fluidos y decidir el momento del vasopresor, y una ecografía "
        "repetida muestra la VCI llenándose con volumen (decisión C). La consolidación puede nombrarse, pero no crea "
        "por sí sola la oportunidad (decisión F): una oportunidad para el caso.",
    # pulmonary_edema_58m, pulmonary_edema_75f
    "Diffuse B-lines, a moderately depressed LV and a plethoric IVC separate congestion from the other causes of "
    "this presentation; loading volume is a critical event of the case.":
        "Las líneas B difusas, un VI con depresión moderada y una VCI pletórica separan la congestión de las otras "
        "causas de este cuadro; cargar volumen es un evento crítico del caso.",
    "Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC.":
        "Decidir nitrato, diurético o VMNI, y no dar volumen, a partir de las líneas B, el VI y la VCI.",
    "requests POCUS and names the diffuse B-lines and the depressed LV":
        "solicita POCUS y nombra las líneas B difusas y el VI deprimido",
    "withholds volume because of them":
        "no da volumen por esos hallazgos",
    "gives nitrate, diuretic or NIV because of them":
        "da nitrato, diurético o VMNI por esos hallazgos",
    "Diffuse B-lines, a severely depressed LV, a plethoric IVC and small effusions separate congestion from the "
    "other causes of this presentation; loading volume is a critical event of the case.":
        "Las líneas B difusas, un VI con depresión severa, una VCI pletórica y derrames pequeños separan la congestión "
        "de las otras causas de este cuadro; cargar volumen es un evento crítico del caso.",
    # pulmonary_embolism_33f
    "Stable (110/70) with SpO2 90 %: a mildly enlarged RV without septal flattening and a non-compressible popliteal "
    "vein. The proximal DVT confirms thromboembolic disease before the CT angiogram (20 minutes) returns, and an RV "
    "without shock argues against thrombolysis, a dangerous action in this case (decision G).":
        "Estable (110/70) con SpO2 90 %: un VD levemente dilatado sin aplanamiento septal y una vena poplítea no "
        "compresible. La TVP proximal confirma la enfermedad tromboembólica antes de que vuelva la angio-TC "
        "(20 minutos), y un VD sin shock argumenta contra la trombólisis, una acción peligrosa en este caso "
        "(decisión G).",
    "Integrating the RV and a proximal DVT with the haemodynamic stability: anticoagulation before confirmation, and "
    "no thrombolysis.":
        "Integrar el VD y una TVP proximal con la estabilidad hemodinámica: anticoagulación antes de la confirmación, "
        "y sin trombólisis.",
    "requests POCUS and names the proximal DVT or the RV":
        "solicita POCUS y nombra la TVP proximal o el VD",
    "anticoagulates, or states it as pending the angiogram, because of it":
        "anticoagula, o la plantea como pendiente de la angio-TC, por ese hallazgo",
    "withholds thrombolysis with the stable haemodynamics and the RV stated":
        "no da trombólisis, y explicita la estabilidad hemodinámica y el VD",
    # pulmonary_embolism_61m
    "Obstructive shock (86/54, SpO2 88 %): an RV larger than the LV with a D-sign and McConnell's sign, and a "
    "non-compressible popliteal vein, justify treating a high-risk embolism and deciding reperfusion before the CT "
    "angiogram (decision G).":
        "Shock obstructivo (86/54, SpO2 88 %): un VD más grande que el VI con signo D y signo de McConnell, y una vena "
        "poplítea no compresible, justifican tratar una embolia de alto riesgo y decidir la reperfusión antes de la "
        "angio-TC (decisión G).",
    "Deciding reperfusion and anticoagulation from RV strain and a proximal DVT in shock.":
        "Decidir la reperfusión y la anticoagulación a partir de la sobrecarga del VD y una TVP proximal en shock.",
    "requests POCUS and names the dilated RV with a D-sign or McConnell's sign, or the DVT":
        "solicita POCUS y nombra el VD dilatado con signo D o signo de McConnell, o la TVP",
    "anticoagulates and decides reperfusion because of it":
        "anticoagula y decide la reperfusión por ese hallazgo",
    "acts without waiting for the angiogram":
        "actúa sin esperar la angio-TC",
    # anaphylaxis_29f
    "Adrenaline and volume are indicated whatever the POCUS shows; the hyperdynamic LV and the collapsing IVC "
    "confirm a distributive shock without changing its management (decision C).":
        "La adrenalina y el volumen están indicados muestre lo que muestre el POCUS; el VI hiperdinámico y la VCI que "
        "colapsa confirman un shock distributivo sin cambiar su manejo (decisión C).",
    # anaphylaxis_63m_betablocked
    "In this refractory reaction the case's lever is the medication history and glucagon; volume is given "
    "regardless, and the POCUS supports without guiding the decision (decision C).":
        "En esta reacción refractaria, la palanca del caso es la historia de medicamentos y el glucagón; el volumen se "
        "da de todos modos, y el POCUS apoya sin guiar la decisión (decisión C).",
    # renal_colic_34m
    "The renal ultrasound, the study that settles this disposition, is a formal study in the simulator and not "
    "POCUS; the POCUS proper does not change the management of a colic without shock (decision H).":
        "La ecografía renal, el estudio que resuelve este destino, es un estudio formal en el simulador y no POCUS; "
        "el POCUS propiamente tal no cambia el manejo de un cólico sin shock (decisión H).",
    # obstructive_pyelonephritis_58f
    "Septic shock from an infected obstruction (94/54) with a 1.0 cm collapsing IVC and a vigorous LV: POCUS can "
    "select and limit the fluid strategy and time the vasopressor (decision C). The renal ultrasound is a formal "
    "study in the simulator and does not count by itself (decision H). A repeat scan still shows the arrival IVC: "
    "the simulator does not model its response here.":
        "Shock séptico por una obstrucción infectada (94/54) con una VCI de 1,0 cm que colapsa y un VI vigoroso: el "
        "POCUS puede elegir y limitar la estrategia de fluidos y decidir el momento del vasopresor (decisión C). La "
        "ecografía renal es un estudio formal en el simulador y no cuenta por sí sola (decisión H). Una ecografía "
        "repetida sigue mostrando la VCI de la llegada: aquí el simulador no modela su respuesta.",
    "Guiding the fluid and haemodynamic strategy with POCUS in septic shock.":
        "Guiar con POCUS la estrategia de fluidos y hemodinámica en el shock séptico.",
    # bradycardia_ccb_68m, bradycardia_bb_54f
    "The POCUS is the same in the three toxic or metabolic bradycardias -- globally reduced contraction at a slow "
    "rate -- so it does not discriminate the cause, which the case separates by the history, the glucose and the "
    "ECG, and the modelled responses do not depend on it (decision E).":
        "El POCUS es el mismo en las tres bradicardias tóxicas o metabólicas —contracción globalmente disminuida a una "
        "frecuencia lenta—, así que no distingue la causa, que el caso separa por la historia, la glicemia y el ECG, y "
        "las respuestas modeladas no dependen de él (decisión E).",
    # bradycardia_avb3_78f
    "The decision is pacing, and the pulse and the pressure confirm its capture; the simulator's POCUS does not "
    "reflect the capture and would contradict the monitor after pacing (decision E).":
        "La decisión es el marcapaso, y el pulso y la presión confirman su captura; el POCUS del simulador no refleja "
        "la captura y contradiría al monitor después de iniciar el marcapaso (decisión E).",
    # bradycardia_hyperk_63m
    "Hyperkalaemia is treated with calcium, insulin with glucose and removal; the POCUS does not change that "
    "management.":
        "La hiperkalemia se trata con calcio, insulina con glucosa y la eliminación del potasio; el POCUS no cambia ese "
        "manejo.",
    # trauma_limb_hemorrhage_27m
    "Shock (96/54, HR 132) after a machinery injury to the thigh: a negative five-window E-FAST excludes a cavity "
    "source and keeps the control on the compressible limb. Free fluid, haemothorax, pneumothorax and the "
    "pericardium are states the EPA lists.":
        "Shock (96/54, FC 132) después de una lesión del muslo por maquinaria: un E-FAST negativo en las cinco "
        "ventanas descarta una fuente cavitaria y mantiene el control en la extremidad compresible. El líquido libre, "
        "el hemotórax, el neumotórax y el pericardio son estados que la EPA enumera.",
    "Directing haemorrhage control with the absence of cavity bleeding on the E-FAST.":
        "Dirigir el control de la hemorragia con la ausencia de sangrado cavitario en el E-FAST.",
    "requests the E-FAST and names it negative":
        "solicita el E-FAST y lo nombra negativo",
    "keeps haemorrhage control on the limb rather than searching a cavity":
        "mantiene el control de la hemorragia en la extremidad en vez de buscar en una cavidad",
    "states what would change that":
        "dice qué cambiaría eso",
    # trauma_hemothorax_41m
    "The E-FAST shows an echogenic left pleural collection in shock: a haemothorax, a state the EPA lists, that "
    "defines the drain; the case's critical events are the undrained haemothorax and the drained one never looked "
    "at again.":
        "El E-FAST muestra una colección pleural izquierda ecogénica en shock: un hemotórax, un estado que la EPA "
        "enumera, que define el drenaje; los eventos críticos del caso son el hemotórax no drenado y el drenado que "
        "nunca se vuelve a mirar.",
    "Deciding the drain and its reassessment from the haemothorax on the E-FAST.":
        "Decidir el drenaje y su reevaluación a partir del hemotórax en el E-FAST.",
    "requests the E-FAST and names the left haemothorax":
        "solicita el E-FAST y nombra el hemotórax izquierdo",
    "places a chest tube because of it":
        "instala un tubo pleural por ese hallazgo",
    "reassesses after the drain with the E-FAST, a film or surgery":
        "reevalúa después del drenaje con el E-FAST, una radiografía o cirugía",
}


def c14_texts():
    """Every C14 text the bank declares today: {English: [(case, field), ...]}, in bank order."""
    import case_assessment_bank as bank
    found = {}
    for case_id, entry in bank.CASES.items():
        block = (entry.get("objectives") or {}).get("C14") or {}
        for field in ("rationale", "reason", "observable_component", "outside_the_encounter"):
            if block.get(field):
                found.setdefault(block[field], []).append((case_id, field))
        for text in block.get("expected_evidence") or ():
            found.setdefault(text, []).append((case_id, "expected_evidence"))
    return found
