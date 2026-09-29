# Registro de deuda técnica

Ciclo 5 del AI Advisor (59BQ), 2026-09-28, con la extensión nocturna.
**Actualizado al cierre del ciclo 9** (2026-09-29): TD-39, TD-34, TD-36 y TD-33
pasan a «Corregido en el ciclo 9», y TD-01 se cierra con DF-20. Lo conocido y no
corregido al congelar V3 entra con su identificador del estado de V3 (KD-16 a
KD-31, `validation/KNOWN_DEFECTS_V3.md`). Lo que dejó la fase de roles y
pantallas, posterior a V3, entra como TD-41 a TD-44 (`docs/EXPERIENCIA_POR_ROL.md`).
Los cierres de los ciclos 8, 7 y 6 siguen más abajo.
**Actualizado al abrir el ciclo 10** (2026-09-29): el resto de TD-31 y la parte de TD-19 que resolvieron las filas 7 y 8 de DF-23 pasan a «Corregido después de V3», y TD-41 cita su corrección. `test_debt_register_cites_its_corrections.py` exige que toda corrección cuyo título nombra un TD quede citada en una fila de ese TD.

**Qué es:** la consolidación de lo registrado en defectos conocidos (KD), el
Decision File (DF), las auditorías y las limitaciones conocidas, para que nada
importante se pierda entre documentos.

**Qué no hay:** deuda inventada. Cada fila cita dónde está la evidencia.

**Leyenda de «¿Bloquea el piloto?»:** el piloto de validación v1 (seis
casos, documentos en español, sin C14 ni SCA). Mide el lector: no lo bloquea
un defecto que el piloto puede medir.

## CRITICAL

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|

## HIGH

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| TD-14 (KD-28) | Lector | **Lo que queda tras DF-22, medido por los tres conjuntos ciegos del ciclo 6.** Vocabulario: «amp of D50», nitroglicerina SL o en infusión, heparina e insulina por kilo, «epi drip», «Narcan», «Page GI», «STEMI code», destinos (floor, OR, pabellón), fluidos (D5W, glucosalino, cristaloides), «run/hang/push», «5.000». Formas: una condición escrita como rótulo sin «si» (el rótulo ya no se salta, pero lo que sigue corre ahora); una retención después del fármaco («y alteplase tampoco por ahora»); una receta en lista tras el alta (KD-06); lo que hizo el equipo prehospitalario seguido de coma, o un pensamiento seguido de «y» («pensando en dar X y poner Y»); insulina con SG (H11); y las 14 clases HIGH de la auditoría del ciclo 5 (H01–H14). **Ciclo 8:** el conjunto ciego halló fuera de sus clases, casi todo retenido con una pregunta: exámenes abreviados («coags», «BMP», «BNP», «PCR», «TP/TTPA», «crea»), nombres comerciales y abreviados («protonix», «pip-tazo», «azithro», «duoneb», «solumedrol», «benadryl», «Mag sulfate», «Vitamin K», «SG 30 %»), el oxígeno «alto flujo» o «titrate 93–95 %», los horarios («q15min», «c/15 min», «may repeat in 5–15 min», «titulando a PAM > 65»), un hallazgo citado como orden («está con PA 85/50»), el verbo de una lista que no llega a lo siguiente («Pedir gases venosos, NBZ…») y el destino «medicina interna». Lo que de eso se pierde sin aviso está en TD-35 | En el motor, la mayoría se retiene con una pregunta (63 de 108 y 19 de 32 en los conjuntos ciegos); las tres lecturas falsas medidas quedaron retenidas | `MEDICION_RECONOCIMIENTO_ORDENES.md` (ciclo 6); `AUDITORIA_TRACE_CICLO5.md` (H01–H14) | ciclo 5 | No: el piloto las mide | Tras el piloto de validación, priorizadas por su medición |

## MEDIUM

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| KD-02 | Lector | Fármaco sin verbo ni dosis no es orden; en una lista se pierde sin aviso | Orden perdida en silencio | `KNOWN_DEFECTS.md` | ciclo 4 | No (medir) | Decisión docente: ¿preguntar la dosis? |
| KD-03 | Lector / interacción | Texto escrito con una aclaración pendiente se toma como su respuesta | Una orden nueva puede leerse como respuesta | ídem | ciclo 4 | No (la herramienta cancela) | Fase 2 |
| KD-11 | Trace | Una indicación de vigilancia queda como modelo de trabajo | Cita no fiel | ídem | ciclo 4 | No | Familia DF-7 |
| KD-15 | Lector | Fluido nombrado en palabras sin verbo («IV fluids 1 L») no es orden | Envío retenido | ídem | ciclo 5 | No (fase EN) | Clase de nombres de fluido, con decisión docente |
| TD-35 | Lector | **En una lista sin verbo, los exámenes abreviados y los nombres comerciales que el lector no conoce se pierden sin aviso** mientras lo demás corre: «CBC coags lactate now», «CBC BMP coags lactate», «hemgrama, TP/TTPA, BUN/crea», «protonix 80 IV». Igual en el V2. Es la clase de KD-02 con el vocabulario de TD-14 | Orden perdida sin aviso | conjunto ciego del ciclo 8 (H-C29-EN-01, H-C29-EN-02, H-C29-ES-01) | ciclo 8 (anterior al ciclo) | No (el piloto lo mide) | Con KD-02 (decisión: ¿preguntar?) y el vocabulario de TD-14 |
| TD-37 | Lector | **«Discharge prescription: prednisone 40 mg daily x 5 days, cetirizine 10 mg daily»:** el alta corre, la prednisona se pierde sin aviso y la cetirizina se registra como fármaco no modelado, no como receta. Igual en el V2 | Receta perdida | hallado en el ciclo 8 | ciclo 8 (anterior al ciclo) | No | Con las recetas del alta (KD-05, KD-06) |
| TD-40 | Lector | **Residuos de las clases del ciclo 8 que dejó la segunda revisión adversarial, iguales en el V2:** la endoscopía urgente con su propósito o su momento («EDA urgente para ligadura de várices», «EDA urgente previa estabilización», «Endoscopy within 24 h») y «IC urgente a cirugía ya» se pierden sin aviso; «Alta con adrenalina 0,3 mg IM SOS» pierde la receta; tras «hemocultivos tomados en SAPU y», una dosis contada como dada allá se da de nuevo (TD-36); en inglés, una condición con «we» o partida por «and» corre ahora («Norepinephrine 0.1 mcg/kg/min when MAP < 65 after we give 2 L», «Once she has had 30 mL/kg and MAP remains < 65, start norepinephrine»), y «when stridor recurs» también; «Return to OR if rebleeds» y «Reconsultar a cirugía si persiste el sangrado» se pierden. Dos lecturas quedan ambiguas y se mantienen: «When rechecked FSBG < 60, D50 50 mL IV now» queda como plan (el V2 lo daba) y «EDA hoy por gastro, sin sangrado activo» llama a gastroenterología. **El ciego 2 sumó, analizado después de medirlo:** «SatO2» no es un parámetro, y «Cuando la SatO2 baje de 92%, iniciar O2 por naricera» da el oxígeno ahora (su única ejecución falsa); «two sets of blood cultures» y «Evaluación por cardiólogo de turno» se pierden; «Adrenalina 1 mg/ml, 0,5 mg IM en el muslo, ahora» y un «, now» suelto tras el sitio de la inyección se preguntan; «pasar c/u en 1 hora» como cláusula propia se pregunta; «OK to send home», «OK for home», «Ok para irse a domicilio» y «Alta ok» no se leen; y «tras 6 h en observación», que ya ocurrió, se lee como observación ordenada | Orden perdida sin aviso o, en las condiciones, una orden que corre antes de tiempo | segunda revisión adversarial y ciego 2 del ciclo 8 (`docs/CICLO8_LECTOR.md`) | ciclo 8 (anterior al ciclo) | No (el piloto lo mide) | Con TD-14 y TD-36, por clase y con A–J |
| KD-16 | Lector | «d/c» y «dc» no se leen como alta: «d/c home» no lee nada; «Dc home w/ EpiPen x2» guarda la receta y pierde el alta sin aviso. «d/c NS» sigue deteniendo el suero | Alta perdida sin aviso | revisión adversarial del ciclo 9 (D01, D02, D05, D14, D15, D18, D34, H09) | ciclo 9 (anterior al ciclo) | No (el piloto lo mide) | Con los datos externos |
| KD-17 | Lector | Un alta escrita como intención, posibilidad o en pasado no corre ni se registra: «Plan to discharge home in 2 hours», «Planeo alta mañana», «Posible alta en unas horas», «Dada de alta» | Plan perdido sin registro | sondas y las dos revisiones del ciclo 9 (también «…, PEF 80%: alta», sin leer) | ciclo 9 (anterior al ciclo) | No (el piloto lo mide) | Con KD-16, como planes de destino |
| KD-18 | Lector | Una observación o un control sin «dejar en» no se lee: «Observe 6 h», «Observar 4 horas», «Control en 1 hora», «recheck in ED in 24 h» | Observación perdida | sondas del ciclo 9 | ciclo 9 (anterior al ciclo) | No | Con TD-14, por clase |
| KD-19 | Lector | Tras una reevaluación, lo que sigue en la oración se absorbe: «Reassess in 30 min, 2 L NS» pierde el suero; «…, discharge if improved» vuelve toda la oración un plan y la reevaluación no corre | Orden perdida sin aviso | sondas del ciclo 9 | ciclo 9 (anterior al ciclo) | No | Agrupación de la reevaluación, por clase |
| KD-20 | Lector | Intervalos fuera de horas y minutos: «20'» corre a los 0 minutos sin aviso; «a las 14 h» se lee como 840 minutos (el motor lo pregunta) | Reevaluación a destiempo | las dos revisiones del ciclo 9 (R20, R23, R26, H18; «en hora y media» se pregunta) | ciclo 9 (anterior al ciclo) | No | Si los datos externos traen esas formas |
| KD-21 | Lector · motor | Repetir o continuar lo recibido antes: «Repeat the epinephrine given by EMS» y «repetir adrenalina 0,5 mg IM» se retienen con una pregunta aun con la dosis escrita; «Continue NS started by EMS at 125 mL/h» pregunta un bolo | Adrenalina demorada por una pregunta | las dos revisiones del ciclo 9 (H27, S1–S3, P15–P17, P35, P36; «…en el SAPU, repetir» pierde el «repetir») | ciclo 9 (anterior al ciclo) | No | Repetición de un tratamiento previo como orden nueva |
| KD-22 | Lector | El segundo tratamiento de un relato prehospitalario: uno modelado se pregunta en vez de registrarse; uno no modelado queda como decisión del residente; tras un rótulo y «+», se pierde | Registro equivocado o ausente; nada se da de nuevo | las dos revisiones del ciclo 9 (P03, P13, H21–H24; la segunda dosis prehospitalaria y la nitroglicerina del SAMU no se registran) | ciclo 9 (anterior al ciclo) | No | El relato como un solo relato |
| KD-24 | Motor | Un fragmento no reconocido retiene todas las órdenes del envío, también la adrenalina: «Epi 0.5 mg IM now, already drawn up» | Orden urgente demorada por una pregunta | las dos revisiones del ciclo 9 (H29, H31, H32; «Segunda dosis de adrenalina…; la primera se la pusieron en el SAPU») | ciclo 9 (anterior al ciclo) | No | La prosa leída como prosa, por clase |
| KD-26 · KD-27 · KD-29 | Lector | TD-35, TD-37 y TD-40, con su identificador del estado de V3 (TD-14, arriba, es KD-28) | Ver sus filas | `validation/KNOWN_DEFECTS_V3.md` | ciclos 5–8 | No | Tras la medición externa |
| KD-31 | Tamizaje | El tamizaje de eventos críticos no cita un tratamiento previo registrado: la omisión de antiagregante (como lectura) o de adrenalina se propone aunque el residente haya registrado la dosis prehospitalaria. Ningún evento se acepta solo | Propuesta de evento sin el hecho que la matiza | revisión del tamizaje en el ciclo 9 | ciclo 9 | No | **Implementado después de V3 (2026-09-29, `fa1d910`), no validado:** el tamizaje cita el tratamiento informado como recibido antes (historia, no orden ni administración), con la fuente, la hora y el minuto que registró el lector, sin inventar hora; el evento, su peso y su resultado no cambian, y la fila marca `faculty_interpretation` (`test_prior_treatment_in_screening.py`). En V3 el defecto sigue presente |
| TD-02 | Evidencia | No existe «oportunidad ofrecida pero no demostrada»: se confunde con pendiente o con desempeño insuficiente | Lectura injusta del progreso | auditoría nocturna, anexo 59AJ | ciclo 5 | No | DF-17, tras el piloto C14 |
| TD-03 | Procedencia | Los vínculos de marco de los 8 Decision Challenges no se congelan con la observación, sólo la versión del mapping | Una exportación por hito leería los vínculos actuales | auditoría nocturna, anexo 59BG | ciclo 5 | No | Antes de cualquier exportación por marco |
| TD-04 | Datos clínicos | Todo el POCUS del banco sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`) | C14 declara oportunidades sobre hallazgos de POCUS que el código aún llama borrador | `clinical_cases.py:64` | antes del ciclo 1 | No | Que el docente confirme el POCUS de los casos C14 YES (DF-23) |
| TD-05 | Pruebas | `test_generation_reload.py` muta módulos globales al importarse | Posible contaminación entre pruebas si el `reload` falla | auditoría nocturna, anexo 59R | ciclo 5 | No | Cuando se toque ese archivo |
| TD-08 | Datos clínicos | **Oclusiones coronarias, lo que queda tras el ciclo 6.** De Winter se corrigió (C-2026-09-28-08). El pulmón del POCUS del tronco se corrigió en el ciclo 9 (DF-23 4a, C-2026-09-29-06). **Cerrado el 2026-09-29:** el grado de `acs_70f_left_main` es leve (C-2026-09-29-15, con su español aprobado) y la pared reperfundida queda aturdida, a lo sumo levemente disminuida (DF-23 fila 6 B, C-2026-09-29-20). Queda el «reduced» sin grado de la llegada de `acs_54m_inferior`, (DF-23 fila 5): variabilidad plausible, que no se limpia (decisión del ciclo 7) | — | `docs/AUDITORIA_DF23_CICLO6.md` §1 y §5 | ciclo 5 | No | Cerrado |
| TD-09 | Desempeño | La cola docente resuelve la elegibilidad objetivo por objetivo, verificando otra vez la huella 17 veces por encuentro: 3,2 s con 1000 encuentros pendientes y 14,5 s con 5000 | Página docente lenta con cohortes grandes | auditoría nocturna, sección 3 (perfilado) | ciclo 5 | No | Antes de cohortes de más de ~20 residentes (DF-24) |
| TD-41 | Pantallas · costo | **Resuelta el 2026-09-29 (decisión docente posterior a V3; C-2026-09-29-17).** Abrir o recargar una página, abrir la revisión del encuentro, o consultar o generar un PDF docente o del residente lee sólo las traducciones guardadas (`prose_translation.for_page`). Lo no traducido se muestra en su original inglés, el documento lo dice, y su lector puede pedirlo («Translate the AI reasoning into Spanish»): ese pedido, y sólo él, llama al proveedor, una vez y sólo por lo que falta; lo traducido se guarda y se reutiliza. Si el inglés de un documento cambió desde que se pidió su traducción, se marca **desactualizada** y no se vuelve a traducir sola (`mrs_prose_translation_documents`). Antes: con clave configurada, la revisión del encuentro y los PDF docentes pedían la traducción al cargar (§154FT) | — | `test_translations_are_asked_for.py` | anterior al ciclo 9 | No | Cerrada |
| TD-45 | Lector (congelado) | **Brechas registradas el 2026-09-29, con ejemplos reproducibles; el lector no se cambió.** (a) Fármaco sin verbo en una lista se pierde sin aviso mientras lo demás corre: «- Aspirin / - Ticagrelor 180 mg PO / - ECG now» y «Aspirin, heparin 5000 units IV, ECG» (KD-02). (b) «IV fluids 1 L» se retiene: «This order was not recognized» (KD-15); con verbo corre. (c) «Check the IV.» responde «The requested study was not recognized». (d) «Flush the IV.» y «Replace the IV.» responden la pregunta genérica. (e) «Get another IV.» responde «Specify which recorded drug or fluid to repeat». (f) «IO, then D50.» se retiene con la pregunta genérica (la forma completa «Place an IO, then give D50 50 mL IO» corre). (g) «Stop the dextrose infusion.» y «Suspender la infusión de glucosado.» con la infusión al 10 % corriendo responden «No infusion is running»; «Stop the D10.» la detiene. (h) «Epinephrine 0.5 mg IM given at OSH at 10:40» no separa la hora (queda en el texto) | Nada se ejecuta de más; órdenes perdidas o retenidas con una respuesta genérica o engañosa; en (g) la respuesta contradice lo que corre | `test_reader_gaps_registered.py` (fija la conducta actual: si una empieza a funcionar, la prueba falla y este registro se actualiza) | 2026-09-29 | No (el piloto las mide) | Ciclo del lector aprobado; (g) antes, si el docente lo prioriza |

## LOW

| ID | Área | Descripción | Evidencia | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|
| KD-04, KD-07, KD-08, KD-09, KD-10, KD-12, KD-13, KD-14 | Lector / Trace | Los residuos LOW de DF-16 y DF-11 | `KNOWN_DEFECTS.md` | No | Según el piloto |
| TD-07 | Idioma | La razón y la evidencia esperada de C14 se muestran en inglés en el portal docente en español | auditoría nocturna, sección 5 | No | Con revisión docente de la traducción |
| TD-10 | Observabilidad | El Trace no guarda el commit por turno, sólo al iniciar el encuentro | auditoría nocturna, anexo 59AP | No | Campo corto, cuando se toque el Trace |
| TD-11 | Lenguaje de docs | «validated trajectory» significa «probada», no validación clínica | README | No | En textos nuevos |
| TD-18 | Integridad | **Corregido en el ciclo 10 (C-2026-09-29-24):** directiva y encuentro en una transacción (I-F09); `sequence` con restricción única (I-F06); una observación vigente duplicada o un JSON corrupto ya no tiran la vista, y `check_database.py --integrity` lista las repeticiones (I-F19/20); los errores quedan registrados por su clase (I-F10). **Queda:** la foto de una confirmación absorbe observaciones posteriores al migrar (I-F18) | auditoría nocturna, sección 1 | No | DF-24 dejó fuera I-F18 (ciclo 7) |
| TD-19 | Clínica menor | `bradycardia_bb_54f` corregida (llega somnolienta, C-2026-09-28-08). Después de V3 se resolvieron la FA de `anaphylaxis_63m_betablocked` (C-2026-09-29-21) y la pregunta por embarazo, FUM o menstruación, que es un tema propio y responde «No documentado» si el caso no lo escribió (C-2026-09-29-22). **Queda:** qué dice cada caso sobre embarazo o FUM en `asthma_24f`, `anaphylaxis_29f`, `pulmonary_embolism_33f` y `pneumonia_46f` (hoy «No documentado») | `docs/AUDITORIA_DF23_CICLO6.md` §2–§4 | No | Decisión docente (paquete del ciclo 10) |
| KD-23 | Lector | Formas de tratamiento previo fuera del reconocedor: «s/p», «PTA», «El 112 le puso…», «por el 061», la vía puesta por el SAMU; no se da ni se registra nada | revisión adversarial del ciclo 9 | No | Con los datos externos |
| KD-30 | Lector | Una indicación para casa tras el alta se lee como orden ahora y la retiene con una pregunta («Discharge home, start prednisone tomorrow»); «Adrenalina autoinyectable para casa» sin alta pregunta la velocidad de una infusión | revisión adversarial y sondas del ciclo 9 | No | Con las recetas del alta |
| TD-42 | Pantallas | El selector «Encounter record» del docente rotula por minuto: dos encuentros del mismo desafío terminados en el mismo minuto se confundirían (la clase que se corrigió en las páginas nuevas del ciclo 9) | revisión visual del ciclo 9 | No | Cuando se toque la vista docente |
| TD-43 | Pantallas | Pendientes de la revisión visual: la página docente es larga (la evidencia por marco queda al final); los rótulos del radar de las tarjetas son pequeños; la columna «Through» es larga; un ZIP del portafolio ya preparado no se rehace en la misma sesión si después se confirma otro documento (su manifiesto lleva la hora); la clave `Working model` está duplicada en el catálogo de pantallas | `docs/EXPERIENCIA_POR_ROL.md` | No | Con el piloto formativo |
| TD-38 (KD-25) | Sala | Un envío que sólo trae un plan (una orden condicional o una indicación al paciente) no ejecuta ni retiene nada: la sala dice «Recorded as a conditional plan, not executed now: …» y el Trace lo registra, pero después agrega el aviso genérico «Please specify a question, investigation, treatment, or reassessment.», como ya pasaba con «si» | ciclo 8 (`docs/CICLO8_LECTOR.md`) | No | Mostrarlo como registrado, sin el aviso, cuando se toque la sala |

## Corregido en el ciclo 10 (2026-09-29)

| ID | Qué | Registro |
|---|---|---|
| TD-18 (parte) | I-F09, I-F06, I-F19/20 e I-F10; I-F18 sigue fuera (DF-24) | C-2026-09-29-24 |
| TD-44 | Activar, desactivar o cambiar el rol o el año de una cuenta queda con autor y hora; sólo el administrador lo lee (paso 1 de la Fase 2) | C-2026-09-29-25 |

## Corregido después de V3 (2026-09-29)

| ID | Qué | Registro |
|---|---|---|
| TD-31 (resto) | La hemostasia sobre una fuente externa no es una suma: la compresión y el taponamiento la reducen sin detenerla, y el registro dice si el sangrado quedó reducido o detenido | C-2026-09-29-13 |
| TD-19 (parte) | `anaphylaxis_63m_betablocked` muestra FA a 64 en el monitor y el ECG; embarazo, FUM y menstruación son un tema propio que responde «No documentado» si el caso no lo escribió | C-2026-09-29-21, C-2026-09-29-22 |
| TD-08 (resto) | El grado de `acs_70f_left_main` es leve y la pared reperfundida queda aturdida, a lo sumo levemente disminuida | C-2026-09-29-15, C-2026-09-29-20 |
| TD-41 | Ninguna página ni PDF pide una traducción al abrirse; sólo el pedido de su lector | C-2026-09-29-17 |

## Corregido en el ciclo 9

| ID | Qué | Registro |
|---|---|---|
| TD-39 | Un alta para más tarde (con su plazo, tras una observación o un resultado, o con una condición) es un plan de destino: se registra con las palabras del residente, no cierra el encuentro y el Trace lo distingue. El alta inmediata, negada, preguntada o de otro servicio no cambia. Tras la revisión adversarial: el reloj de cuatro cifras, el plazo al final de lo que el alta manda a casa, el «ahora» explícito y el valor medido | C-2026-09-29-01, C-2026-09-29-07 |
| TD-34 | Una reevaluación en horas espera sus minutos (h, hr, hora, hour, media hora, «1 h 30»); un solo valor va al motor, al reloj y al Trace | C-2026-09-29-02, C-2026-09-29-07 |
| TD-36 | Un tratamiento recibido antes de la atención del residente es historia: se registra con qué, dosis, vía, quién y cuándo, y nunca se da de nuevo. Tras la revisión adversarial: dónde se dio antes de urgencias y hace cuánto | C-2026-09-29-03, C-2026-09-29-07 |
| TD-33 | En la regla de sobrecarga transfusional en trauma, sólo la sangre repone el déficit hemorrágico (decisión docente) | C-2026-09-29-04 |
| TD-01 | Cerrado con DF-20, sin cambios en el caso: un compromiso fisiológico del VD puede coexistir con un POCUS cualitativo normal o no diagnóstico. Las filas TDFC de `acs_54m_inferior` quedaron declaradas | C-2026-09-29-05 |
| TD-08 (parte) | El pulmón del POCUS de `acs_70f_left_main` dice lo que dicen su examen y su radiografía (DF-23, fila 4a) | C-2026-09-29-06 |

## Corregido en el ciclo 8

| ID | Qué | Registro |
|---|---|---|
| TDFC | TD1, F1, C1 y C3 declarados caso por caso en 30 casos con el modelo de C14 (TD1 25 YES / 5 NO, F1 25/5, C1 18/12, C3 10/20). `acs_54m_inferior` espera DF-20 y conserva la transición | C-2026-09-28-17 |
| TD-29 | «Cuando», «when», «once», «en cuanto», «una vez que», «tan pronto como» (y «apenas» con subjuntivo) hacen de una orden un plan cuando nombran el estado del paciente. «Cuando puedas», un relato y lo que sólo se espera se leen como antes. Lo que una condición manda se guarda aunque el lector no pueda ejecutarlo. Tras la segunda revisión adversarial: «once» ante una razón es una dosis, y lo que el paciente hace seguido de lo que se vio es relato | C-2026-09-28-19 |
| TD-30 | Interconsultas sin verbo (también «IC uro», «cards», «gen surg»), la endoscopía pedida (una llamada a gastroenterología), los hemocultivos con su número, las vías por su número o calibre y «RL» ante un volumen. Lo ya hecho, pendiente o respondido no se pide, tampoco lo que se pide «después del TAC» | C-2026-09-28-20 |
| TD-31 (primera mitad) | La adrenalina IM sin dosis pregunta su dosis en miligramos, nunca una velocidad. La regla de medidas combinadas se corrigió después de V3 (C-2026-09-29-13, abajo) | C-2026-09-28-21 |
| TD-32 | «2 U. GR»; la desactivación del protocolo de transfusión masiva, registrada sin quitar ninguna unidad; las plaquetas según recuento como plan; el estado de las pruebas cruzadas, que no es un pedido; el tiempo de cada unidad, que se suma. Tras la segunda revisión adversarial: las unidades de otro fármaco no son glóbulos rojos, una suspensión negada o pospuesta no se registra y un torniquete «ya puesto» no se pone de nuevo | C-2026-09-28-22 |
| KD-05 | «OK to discharge» y «ok para alta» son un alta; el alta con su receta conserva el alta. Un plazo, una observación, una condición o el servicio que autoriza la posponen (segunda revisión adversarial). **Sigue presente en los dos baselines registrados:** el manifiesto de defectos conocidos no cambia hasta elegir uno nuevo | C-2026-09-28-23 |
| TD-06 | El registro nombra DF-7, DF-10 y DF-16a/b/c | C-2026-09-27-13, C-2026-09-27-14, C-2026-09-28-18 |
| TD-23 | La movilidad parietal del infarto, el aviso de intervención urgente y los de anulación docente, en español | C-2026-09-28-24 |
| TD-25 | La prueba se llama por lo que comprueba: `test_reperfusion_prevents_the_arrest_and_the_shock` | C-2026-09-28-24 |
| TD-27 | Los espacios seguidos se colapsan al leer: 8000 espacios bajan de 14 s a 0,001 s | C-2026-09-28-24 |
| TD-28 | La pregunta cita la orden como se escribió | C-2026-09-28-24 |
| — | El catálogo de hipoglicemia publicado se regeneró con las entradas nuevas del registro; la suite lo exige | ciclo 8 |

## Corregido en el ciclo 7

| ID | Qué | Registro |
|---|---|---|
| TD-21 | Transfundir una hemorragia activa en trauma ya no dispara una sobrecarga falsa (principio D); con el sangrado controlado y la pérdida repuesta, la regla vuelve. La HDA no cambia | C-2026-09-28-12 |
| TD-26 | Hemoderivados por clase, estándar A–J: glóbulos rojos en las unidades escritas; plasma, plaquetas, crioprecipitado y sangre total registrados como indicados, con su efecto no modelado; la activación del protocolo de transfusión masiva registrada, sin inventar nada; lo ambiguo, preguntado; nada que no sea una orden ahora transfunde. Residuos en TD-29, TD-30 y TD-32 | C-2026-09-28-13 |
| TD-22 | La prueba de embarazo se registra como pedida, sin resultado inventado, y no retiene nada | C-2026-09-28-14 |
| — | Control de hemorragia por medida y acceso intraóseo como tal (C7-06), EN/ES | C-2026-09-28-14 |
| DF-21 · C4 | C4 = NO en todo el entorno de observación | C-2026-09-28-10 |
| — | C14 NO en `acs_54m_inferior`: 31/31 casos revisados | C-2026-09-28-11 |
| TD-17 | La exportación dice quién confirmó (I-F02); el radar toma la revisión confirmada de mayor número (L-F02) | C-2026-09-28-15 |
| L-F07 | Las 9 composiciones de hipoglicemia heredan el C14 NO de su caso de origen | C-2026-09-28-16 |
| TD-24 | **PostgreSQL verificado** en un clúster PostgreSQL 16 local y descartable, sin datos reales, sobre el candidato final: 168 pruebas de persistencia pasan (115 bases creadas en PostgreSQL); las 3 que leen el archivo SQLite directamente no aplican, y su equivalente se comprobó a mano (la migración conserva las filas). El clúster se borró. Staging no se tocó (§9) | ciclo 7, C7-05 |
| — | El catálogo de hipoglicemia publicado estaba desactualizado desde `1c4194b` (no nombraba C-2026-09-28-10); `1c4194b` y `c61daf6` se subieron con esa prueba fallando. Regenerado | ciclo 7 |

## Corregido en el ciclo 6

| ID | Qué | Registro |
|---|---|---|
| TD-12 | Las nueve clases CRITICAL del lector (C01–C09), por clase. Después de medir, lo que hallaron los conjuntos ciegos en las correcciones mismas: el ácido tranexámico en una historia; lo unido con «y/and» a lo que hizo el equipo prehospitalario (se pregunta); un rótulo con umbral, estado o resultado; y la vía por la que pasa un suero («SF 500 mL por VVP», «via the PIV»), que perdía el bolo e instalaba una vía. Los residuos están en TD-14, TD-26 y `MEDICION_RECONOCIMIENTO_ORDENES.md` | C-2026-09-28-04 |
| KD-06 | La receta unida al alta con «con/with» queda como receta, nunca como dosis dada | C-2026-09-28-04 (clase C05) |
| 59O-06 (parte) | La pregunta por una orden fantasma: un hallazgo tras la orden («satura 86 % con la naricera») ya no es una segunda orden (C09). La vía ya escrita se había corregido en el ciclo 5 (KD-01). Queda la tasa de SG que se pregunta ante una insulina (H11, en TD-14) | C-2026-09-28-04 (clase C09) |
| TD-13 | «Urgent intervention executed» y la oferta de explicarla salen sólo de una ejecución real; «no sé» ante una orden retenida ya no la hace desaparecer | C-2026-09-28-05 |
| TD-15 | Los temas de historia se leen del caso congelado del encuentro (L-F01) | C-2026-09-28-06 |
| TD-16 | El perfil se ordena por la fecha del encuentro (L-F04) | C-2026-09-28-07 |
| — | Las regresiones de las propias correcciones que halló la revisión adversarial del diff: el «stop» prestado a la orden siguiente («Hold NS, O2 4 L NC» retiraba el oxígeno), la primera persona que ejecutaba preguntas, la prueba de historia que silenciaba órdenes comunes, el relato prehospitalario, el «RR» del ventilador, la sedación con su procedimiento, lo «ready», el tiempo de C01 y de C07, la página que caía al suspender un suero con duración, L-F01 con casos que eligió el modelo y «no se administra…». Y uno anterior al ciclo: la activación de un servicio se prestaba a los fármacos siguientes | C-2026-09-28-09 |
| TD-08 (parte) · TD-19 (parte) | De Winter conserva la acinesia con la arteria cerrada; `bradycardia_bb_54f` llega somnolienta | C-2026-09-28-08 |

## Corregido en la extensión nocturna

- **59Z · un encuentro nuevo heredaba el cierre del anterior**
  (C-2026-09-28-03).
  - El aviso de cierre abría el encuentro siguiente.
  - El registro de cierre se guardaba en él.
  - Corregido en `reset_session()`, con 3 pruebas en la página real.

## Conducta por diseño (no es deuda)

- **KB-01:** el oxígeno sin flujo absoluto se retiene para preguntar el flujo.
- **KB-02:** un «IN» suelto antes del fármaco no se lee como vía nasal.
- **KB-03 (ciclo 6):** tras lo que hizo el equipo prehospitalario, «y coloco…» o
  «y paso…» se pregunta: sin su tilde, el verbo es también el pasado del equipo
  («colocó», «pasó»). Una pregunta no pierde la orden.
- **Reenviar una orden es un turno nuevo.** Si el motor la repite depende del
  fármaco: una dosis única ya dada no se repite.
