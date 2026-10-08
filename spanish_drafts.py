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
#: The engine sentences (``ENGINE``) were decided by the faculty on 2026-10-07 (packet, block A: A-1 to A-18,
#: with A-2 and A-6 revised and the 49m's edge states approved) and are active since B-5, IG-5 (2026-10-08):
#: their Spanish is in ``language`` (``_ENGINE_FINDINGS_ES`` and the A-1 rule). This module keeps them as the
#: record of what was reviewed; nothing here is read by the room.
ENGINE_STATUS = "approved_active"

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
     "spanish": "Paro circulatorio por una hemorragia no controlada. El sangrado no se había detenido; la "
                "reposición de volumen no sustituye el control del sangrado activo.",
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
     "spanish": "Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de "
                "aire, con sibilancias espiratorias residuales.",
     "note": "neumotórax descomprimido; «left» → «izquierdo», y la segunda parte es cualquiera de las dos del asma"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n}/min, provided by the assisted ventilation currently in progress.",
     "example": "Respiratory rate 12/min, provided by the assisted ventilation currently in progress.",
     "spanish": "Frecuencia respiratoria {n}/min, dada por la ventilación asistida en curso.",
     "note": "family_engine.current_findings, opioides"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n}/min; breaths remain shallow.",
     "example": "Respiratory rate 6/min; breaths remain shallow.",
     "spanish": "Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales.",
     "note": "family_engine.current_findings, opioides"},
    {"kind": "examination", "cases": ["opioid"], "seen": False,
     "english": "Respiratory rate {n}/min; spontaneous breaths have greater depth.",
     "example": "Respiratory rate 14/min; spontaneous breaths have greater depth.",
     "spanish": "Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas.",
     "note": "family_engine.current_findings, opioides"},
    # The access findings (glucose_rescue.access_finding): language already says them in
    # Spanish in an entry; the examination panel, where they are read, does not.
    {"kind": "examination", "cases": ["hypoglycemia_54m_thiamine"], "seen": True,
     "english": "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.",
     "example": "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está "
                "levemente aumentada de volumen y fría.",
     "note": "vía fallida antes de usarla; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.",
     "example": "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni "
                "dolor a la palpación.",
     "note": "vía que funciona; el español ya está en language, no en el panel"},
    {"kind": "examination", "cases": ["hypoglycemia"], "seen": False,
     "english": "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.",
     "example": "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.",
     "spanish": "Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de "
                "volumen, pálido, frío y doloroso a la palpación.",
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
     "spanish": "El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo.",
     "note": "también por la cánula nueva del antebrazo derecho o por la aguja intraósea; el español ya está en "
             "language, no en el panel"},
    # Approved in the packet itself (block A, 2026-10-07), not in R-4: the R-4 sheets leave them out.
    # A-2 (faculty, 2026-10-07; B-5, IG-4): the same congestion once the patient is exhausted.
    {"kind": "examination", "cases": ["pulmonary_edema"], "seen": False, "review": "packet, block A (2026-10-07)",
     "english": "Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with "
                "exhaustion.",
     "example": "Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with "
                "exhaustion.",
     "spanish": "Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz, "
                "compatible con agotamiento.",
     "note": "family_engine.current_findings, edema pulmonar con el paciente agotado (A-2)"},
    # A-6b, A-7-49m and A-8a (faculty, 2026-10-07; B-5, IG-4): the 49m while its obstruction has not improved.
    # A-6a is the case's own arrival finding, whose Spanish is its approved narrative.
    {"kind": "examination", "cases": ["asthma_49m"], "seen": False, "review": "packet, block A (2026-10-07)",
     "english": "Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze.",
     "example": "Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze.",
     "spanish": "Tubo endotraqueal instalado: el murmullo pulmonar sigue muy disminuido en forma bilateral, con "
                "solo sibilancias tenues.",
     "note": "asthma_49m intubado, obstrucción sin mejorar (A-6b)"},
    {"kind": "examination", "cases": ["asthma_49m"], "seen": False, "review": "packet, block A (2026-10-07)",
     "english": "Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left "
                "remains very poor, with only faint wheeze.",
     "example": "Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left "
                "remains very poor, with only faint wheeze.",
     "spanish": "Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; en el lado izquierdo el "
                "murmullo pulmonar sigue muy disminuido, con solo sibilancias tenues.",
     "note": "asthma_49m con el neumotórax sin descomprimir y la obstrucción grave (A-7-49m)"},
    {"kind": "examination", "cases": ["asthma_49m"], "seen": False, "review": "packet, block A (2026-10-07)",
     "english": "Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, "
                "with only faint wheeze.",
     "example": "Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, "
                "with only faint wheeze.",
     "spanish": "Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; sigue muy disminuido "
                "en forma bilateral, con solo sibilancias tenues.",
     "note": "asthma_49m tras la descompresión, obstrucción grave sin mejorar (A-8a)"},
)

#: R-4 (faculty, 2026-09-30): the 18 engine sentences are reviewed first, one by one. For each, the clinical
#: moment it describes, the reading for the review and what a Spanish reader could still meet. The faculty's
#: second response (2026-09-30) settled the terms -- the volume replacement of row 1, «reaparece» and
#: «hemitórax», which rate row 9 shows, «aumento de volumen», «dolor a la palpación» and «suero glucosado» -- and
#: asked for the 18 final phrases together: they are drafts still, and none is approved or shown.
ENGINE_REVIEW = {
    "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been stopped, and no volume "
    "replaces a source that is still open.": (
        "Final del trauma cuando el sangrado nunca se controló (entrada de la sala)",
        "Aprobar la versión final: «la reposición de volumen no sustituye el control del sangrado activo» (redacción "
        "docente del 2026-09-30)",
        "Ninguna"),
    "Bilateral inspiratory crackles with increased respiratory effort.": (
        "Edema pulmonar (75f) al examinar, antes de tratar",
        "Aprobar",
        "Ninguna en el español. Desde A-2 (2026-10-07; implementada el 2026-10-08), con el paciente agotado el "
        "motor escribe la frase de la fila siguiente"),
    "Bilateral crackles remain, with reduced respiratory effort.": (
        "Edema pulmonar que mejora con el tratamiento",
        "Aprobar: el motor la escribe sólo con la congestión en mejoría, y nunca junto al agotamiento (lo verifica "
        "una prueba del motor); «menor esfuerzo» describe ese estado registrado",
        "Ninguna mientras se mantenga esa regla del motor"),
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
        "Aprobar la versión final: «Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; …»",
        "Ninguna"),
    "Respiratory rate {n}/min, provided by the assisted ventilation currently in progress.": (
        "Intoxicación por opioides durante la ventilación con bolsa y mascarilla o la intubación",
        "Aprobar la versión final: la frecuencia que muestra el motor durante la asistencia es la de la ventilación "
        "asistida (fija en 12/min), no la espontánea; el español lo dice, y desde A-9 (2026-10-07) también el inglés",
        "Ninguna"),
    "Respiratory rate {n}/min; breaths remain shallow.": (
        "Intoxicación por opioides con hipoventilación persistente",
        "Aprobar",
        "Ninguna"),
    "Respiratory rate {n}/min; spontaneous breaths have greater depth.": (
        "Intoxicación por opioides que responde a la naloxona",
        "Aprobar",
        "Ninguna; «más profundas» se lee respecto del examen anterior"),
    "Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool.": (
        "Hipoglicemia (54m): la vía de llegada infiltrada antes de usarla, la pista que el residente puede "
        "notar",
        "Aprobar la versión final: «…levemente aumentada de volumen y fría»; la sala ya usa el mismo término",
        "Ninguna: «aumento de volumen» en las filas 12, 13 y 14"),
    "Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness.": (
        "Hipoglicemia: la vía que funciona",
        "Aprobar la versión final: «…sin aumento de volumen ni dolor a la palpación»; la sala ya usa el mismo "
        "término",
        "Ninguna"),
    "Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender.": (
        "Hipoglicemia: la vía fallida después de pasar la glucosa (extravasación)",
        "Aprobar la versión final: «…aumentado de volumen, pálido, frío y doloroso a la palpación»; la sala ya usa "
        "el mismo término",
        "Ninguna"),
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
        "Aprobar la versión final: «El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo "
        "izquierdo». El verbo dice que la infusión está pasando, como lo decía la sala antes del 2026-09-30 (D-6, "
        "2026-10-02); la sala ya usa la misma frase",
        "Ninguna: es un estado, no una indicación, y no se confunde con la glicemia del paciente"),
    "Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with "
    "exhaustion.": (
        "Edema pulmonar con la congestión sin mejorar y el paciente agotado (el mismo criterio que escribe «Agotado» "
        "en el trabajo respiratorio)",
        "Aprobar: redacción final docente de A-2 (2026-10-07), en inglés y en español",
        "Ninguna: un esfuerzo menor es agotamiento, no mejoría"),
    "Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze.": (
        "asthma_49m intubado con la obstrucción todavía en el estado grave de llegada",
        "Aprobar: A-6b, redacción aprobada por la docencia el 2026-10-07",
        "Ninguna: «sigue» no sugiere mejoría"),
    "Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left remains very "
    "poor, with only faint wheeze.": (
        "asthma_49m con el neumotórax a tensión sin descomprimir y la obstrucción grave",
        "Aprobar: A-7-49m, redacción docente del 2026-10-07",
        "Ninguna"),
    "Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, with only "
    "faint wheeze.": (
        "asthma_49m tras una descompresión eficaz, con la obstrucción grave sin mejorar",
        "Aprobar: A-8a, redacción aprobada por la docencia el 2026-10-07",
        "Ninguna"),
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
    # acs_61m_posterior (criteria revised by R-2, 2026-09-30)
    "ST depression in V1-V3 with a regional wall-motion abnormality reported on POCUS (posterior hypokinesis): with "
    "the ECG and the posterior leads, the reported wall motion can support prioritising reperfusion for an occlusion "
    "the 12-lead understates (decision A); in the engine the wall motion evolves with the ischaemic minutes. Two "
    "limits: an isolated regional wall-motion abnormality is subtle, and the written report states it rather than "
    "the resident recognising it, so recognising it is not required; and a non-dilated aortic root and descending "
    "aorta on POCUS do not exclude an aortic dissection.":
        "Infradesnivel del ST en V1-V3 con una alteración de la motilidad regional informada en el POCUS (hipocinesia "
        "posterior): junto con el ECG y las derivaciones posteriores, la motilidad informada puede apoyar la prioridad "
        "de la reperfusión de una oclusión que el ECG de 12 derivaciones subestima (decisión A); en el motor, la "
        "motilidad evoluciona con los minutos de isquemia. Dos límites: una alteración aislada de la motilidad "
        "regional es sutil, y el informe escrito la entrega en lugar de que el residente la reconozca, así que "
        "reconocerla no se exige; y una raíz aórtica y una aorta descendente no dilatadas en el POCUS no descartan "
        "una disección aórtica.",
    "Using the reported regional wall motion, with the ECG and the posterior leads, to prioritise the reperfusion "
    "decision.":
        "Usar la motilidad regional informada, junto con el ECG y las derivaciones posteriores, para priorizar la "
        "decisión de reperfusión.",
    "requests POCUS and relates the reported wall motion to the ECG":
        "solicita POCUS y relaciona la motilidad informada con el ECG",
    "uses it with the ECG and the posterior leads to treat the pattern as an occlusion":
        "la usa junto con el ECG y las derivaciones posteriores para tratar el patrón como una oclusión",
    "activates or expedites reperfusion":
        "activa o acelera la reperfusión",
    # acs_52m_de_winter (wording aligned with the 61m by D-7, 2026-10-02)
    "Using the reported regional wall motion to prioritise the reperfusion decision.":
        "Usar la motilidad regional informada para priorizar la decisión de reperfusión.",
    "Akinesis of the anterior wall and apex supports treating the de Winter pattern as an anterior occlusion "
    "(decision A); in the engine the wall motion evolves with the ischaemic minutes. The report states the wall "
    "motion; recognising it is not required. POCUS never delays reperfusion: activating it from the ECG alone is "
    "correct and is not a C14 deficit.":
        "La acinesia de la pared anterior y del ápex apoya tratar el patrón de de Winter como una oclusión anterior "
        "(decisión A); en el motor, la motilidad evoluciona con los minutos de isquemia. El informe entrega la "
        "motilidad; no se exige reconocerla. El POCUS nunca demora la reperfusión: activarla sólo por el ECG es "
        "correcto y no es un déficit de C14.",
    "requests POCUS and relates the reported anterior akinesis to the ECG pattern as an occlusion":
        "solicita POCUS y relaciona la acinesia anterior informada con el patrón del ECG como una oclusión",
    # acs_48m_wellens
    "The right decision -- angiography and no provocation test -- does not depend on POCUS, and a normal resting "
    "POCUS cannot reasonably guide it. Not being reassured by it is diagnostic reasoning, not C14 (decision B).":
        "La decisión correcta —coronariografía y ninguna prueba de provocación— no depende del POCUS, y un POCUS "
        "normal en reposo no puede guiarla razonablemente. No tranquilizarse por él es razonamiento diagnóstico, no "
        "C14 (decisión B).",
    # acs_70f_left_main (criteria revised by R-2, 2026-09-30, and D-8, 2026-10-02)
    "Borderline pressure with incipient hypoperfusion (104/66, cool extremities, capillary refill 3 s) and "
    "intermediate POCUS findings: globally mildly reduced contraction, scattered basal B-lines and an IVC of 1.9 cm "
    "with about 50% collapse. No single answer follows from them: withholding volume, a small bolus with its limit "
    "stated and reassessed, or early support can each be justified, and the engine answers large volumes poorly in "
    "this profile. C14 observes whether the volume, support and urgency decisions are made with the global LV "
    "function in view and adapted to the response. In this simulator a volume past the ventricle's tolerance "
    "shows only as a pressure that stops answering and a message in the room; the lungs, the examination, the "
    "saturation and a repeat POCUS do not change. The adaptation is judged on those signals: detecting overload on "
    "the examination or POCUS is not required, and when the only response the resident looked for is one the "
    "simulator does not show, that part of the observation is not evaluable rather than missing.":
        "Presión limítrofe con hipoperfusión incipiente (104/66, extremidades frías, llene capilar de 3 s) y "
        "hallazgos intermedios en el POCUS: contracción global levemente disminuida, líneas B basales dispersas y "
        "una VCI de 1,9 cm con cerca de 50 % de colapso. De ellos no se deduce una única respuesta: no dar volumen, "
        "un bolo pequeño con su límite declarado y reevaluado, o un soporte precoz pueden justificarse, y en este "
        "perfil el motor responde mal a volúmenes grandes. C14 observa si las decisiones de volumen, soporte y "
        "urgencia se toman con la función global del VI a la vista y se adaptan a la respuesta. En este simulador, "
        "un volumen que supera la tolerancia del ventrículo se ve sólo en una presión que deja de responder y en un "
        "mensaje de la sala; el pulmón, el examen, la saturación y un POCUS de control no cambian. La adaptación se "
        "juzga con esas señales: no se exige detectar sobrecarga por examen ni por POCUS, y cuando la única "
        "respuesta que buscó el residente es una que el simulador no muestra, esa parte de la observación no es "
        "evaluable, en vez de faltar.",
    "Deciding volume, support and urgency with the global LV function in view, and adapting them to the response.":
        "Decidir el volumen, el soporte y la urgencia con la función global del VI a la vista, y adaptarlos a la "
        "respuesta.",
    "requests POCUS and relates the global LV function, the B-lines and the IVC to the volume decision":
        "solicita POCUS y relaciona la función global del VI, las líneas B y la VCI con la decisión de volumen",
    "withholds volume, or gives a small bolus with its limit stated and reassesses it, or escalates support, and "
    "says why":
        "no da volumen, o da un bolo pequeño con su límite declarado y lo reevalúa, o escala el soporte, y dice por qué",
    "adapts the plan to the response and relates it to the urgency of reperfusion":
        "adapta el plan a la respuesta y lo relaciona con la urgencia de la reperfusión",
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
