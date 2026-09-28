# Auditoría del lector de órdenes y del Management Trace · ciclo 5

Ítems docentes **59G, 59H, 59O** · rama `clinical-encounter-v0.13` · 2026-09-28.
Sólo auditoría: **no se corrigió nada** (59I).

## Antes de leer

- **Las frases son INTERNAL AUDIT DATA.** Las escribió el auditor (un agente
  de IA). No son datos de médicos ni del corpus de validación, y no deben
  mezclarse con `validation/pilot_v1`. Están en
  `AUDITORIA_TRACE_FRASES_CICLO5.md`.
- **La frecuencia real es desconocida.** Que una estructura falle no dice
  cuántos residentes o médicos la escriben. Eso lo mide el piloto.
- **Ninguna falla es regresión del ciclo 5.** La sesión principal pasó las 90
  frases por el lector del SPANISH PILOT BASELINE (`939978a`) y por el actual:
  **las 90 se leen igual**. Por eso, según 59I, ninguna se corrige ahora y todas
  van a priorización futura (DF-22 en el Decision File).
- **Están presentes en los dos baselines.** El piloto puede encontrarlas. No se
  registraron como defectos conocidos: así el piloto conserva su capacidad de
  revelar fallas independientes (59I). Si se registran antes del piloto es una
  decisión suya (DF-22).
- **Verificación independiente** por la sesión principal, llamando al lector
  directamente, con su control:

  | Hallazgo | Frase | Resultado | Control | Resultado del control |
  |---|---|---|---|---|
  | C02 | «Anaphylaxis with stridor and facial swelling: epinephrine 0.5 mg IM in the thigh now, repeat in 5 minutes if no response.» | ninguna acción; toda la frase queda como plan de repetición (`of: None`) | la misma frase sin «Anaphylaxis …:» | adrenalina IM ahora + repetición de ella |
  | C01 | «Atropina 1 mg ev, si no responde, marcapaso transcutáneo a 70 lpm con 60 mA.» | ninguna acción; toda la frase queda como plan condicional | «Atropina 1 mg ev. Si no responde, …» | atropina ahora |
  | C02 | «…I think it's a massive hemothorax: left chest tube now and reassess vitals in 5 minutes.» | sólo la reevaluación; el tubo pleural se pierde | — | — |

**Por qué importa para la evaluación.** Cuando se pierde una orden, el Trace
muestra a un residente que no hizo lo que sí escribió. Es el caso «misma
actuación → distinta evidencia» que busca 59X. La rúbrica y el docente leen
ese Trace.

---

*El resto de este documento es el informe del agente auditor, sin cambios de
contenido.*

## Método

- **Qué se auditó.**
  - El lector (`parse_family_actions`).
  - La captura de razonamiento (`extract_explicit_reasoning`).
  - Los mensajes de lo no ejecutado (`unexecuted_items`).
  - El gate y el motor (`execute_family_bundle`).
  - El Management Trace guardado.
- **Frases.** 90 frases del auditor (46 EN, 44 ES), rotuladas INTERNAL AUDIT DATA. No son datos de médicos. Cada una está atada a un caso del banco.
- **Lector, gate y motor.** Las 90 frases pasaron por el lector, el gate y el motor sobre el estado real del caso (semilla 17).
- **Variantes.** Unas 150 variantes mínimas confirman que cada hallazgo es de clase.
- **Página.** 6 guiones en la página real (`tools_tanda20.rehearse`, `MRS_OFFLINE_CASES=1` sólo en el proceso):
  - 24 pasos y 23 entradas del Trace, leídas con `stored_encounter`;
  - 0 llamadas de IA, bases borradas.
- **Escala de severidad.**
  - **CRITICAL:** se ejecuta algo distinto; o se pierde en silencio una orden clave; o la página o el Trace dan por hecha una decisión que no ocurrió.
  - **HIGH:** se retiene o pierde una orden frecuente en contexto tiempo-crítico; o el Trace atribuye mal el razonamiento.
  - **MEDIUM:** captura parcial o fricción con mensaje claro.
  - **LOW:** cosmético.

## Cifras

| Medida | EN | ES | Total |
|---|---|---|---|
| Frases | 46 | 44 | 90 |
| Sin discrepancia nueva | 9 | 9 | 18 |
| Con ≥1 discrepancia nueva | 37 | 35 | 72 (64 sin contar M11) |
| Peor = CRITICAL | 8 | 9 | 17 |
| Peor = HIGH | 11 | 10 | 21 |
| Peor = MEDIUM | 16 | 13 | 29 |
| Peor = LOW | 2 | 3 | 5 |

- **Hallazgos nuevos:** 9 CRITICAL · 14 HIGH · 13 MEDIUM · 3 LOW.
- **Fricciones de jugabilidad:** 2 CRITICAL · 5 HIGH · 5 MEDIUM · 3 LOW.
- **Defectos conocidos reencontrados** (no se reportan como nuevos): KD-02, KD-06 (EN20, ES20), KD-08, KD-10, KD-12, KD-13.
  - KD-09 y KD-15 están relacionados, pero con otra causa.
  - No aparecieron KD-01, KD-03, KD-04, KD-05, KD-07, KD-11 ni KD-14.
- **Funcionó bien:**
  - listas simples con vía compartida (ES01, ES32, EN25);
  - repetición con condición tras la orden (ES14, EN37, ES41);
  - contingencia tras «;» (EN35);
  - alta con control y aviso (ES40);
  - titulación de NTG con verbo (ES33).
- **Por qué el corpus de ensayo dio 96/96:** no trae estas estructuras.

## Hallazgos 59G

V = variante; P = página.

| ID | Sev | Idioma | Clase | Esperado | Real (frases) | Ejecución | Traza | Causa probable | Recomendación | KD |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | CRITICAL | ES+EN | «X, si no responde, Y» | X ahora + Y plan | toda la oración es plan condicional; X no se da (ES35 atropina; V04 EN/ES) | 1.ª línea no administrada | plan con la orden dentro; `clarification_required` | `parse_family_actions`, rama condicional: sin nada entre la coma y «si», `split=None` y todo queda condicionado | si tras la condición viene «, orden», ejecutar la cabeza | — |
| C02 | CRITICAL | EN+ES | «Dx: orden» con dos puntos | modelo + orden | EN14: adrenalina IM archivada como repetición. EN23: tubo pleural perdido; la página sólo reevalúa. EN42: VMBM perdida. EN21: urología perdida. ES29, EN36, EN38, ES38: retenidas | acciones críticas no ocurren, varias sin aviso | el modelo guarda «Dx: orden»; «executed» sin la acción | «:» no es límite de oración ni de pieza; `_parse_piece_core` devuelve `[]` o `_unreadable`; `_order_free` no corta | «:» tras rótulo breve = límite de cláusula | — |
| C03 | CRITICAL | ES+EN | «Ahora X y luego repetir…» | X + repetición | toda la oración es `repeat` (`of: null`); X no se da (ES02, P1; V01 EN) | 1.ª dosis no dada | salbutamol figura como plan | `_repeat_split`: `standalone` porque la cabeza no se lee (H02) | retener y preguntar; no archivar la dosis | — |
| C04 | CRITICAL | ES | «Suspende el SF y cambia a Ringer 500 mL» | stop SF + RL 500 | dos suspensiones: «sin más volumen»; el RL no se inicia (P5) | orden invertida | «withholding further fluid» | `_ES_PERIPHRASIS`: «cambia a ringer» se lee como perífrasis (-er); la pieza hereda «suspender» | limitar la perífrasis a verbos de inicio con infinitivo real | — |
| C05 | CRITICAL | EN+ES | destino + «on/con» tratamiento | ingreso + infusión | sólo el destino (EN40 D10; V11 noradrenalina) | infusión no iniciada, sin aviso | sólo «admission» | `_parse_piece_core`, rama disposición | separar el tratamiento o preguntar | — |
| C06 | CRITICAL | ES | «Activo hemodinamia / código infarto» | hemodinamia | nada; la página ejecuta sólo el ECG (P6); EN funciona | reperfusión perdida | «executed» con ECG | «activo» excluido de `_ES_IMPERATIVES` | aceptar «activo» + servicio o código | KD-10 (el ECG) |
| C07 | CRITICAL | ES | «Por <razón> instalo/inicio <orden>» | modelo + orden | orden perdida; sólo la reevaluación: «PA 72/41» (P4; V08) | procedimiento no hecho | «executed» sin la acción | `_COMMAND` anclado al inicio; `_DECLARED_INTENTION` sólo corta ante «voy a» | abrir cláusula ante verbo de 1.ª persona tras «Por/Ante…» | KD-13 (modelo) |
| C08 | CRITICAL | EN+ES | TXA «en 10 min» en paquete urgente | torniquete + TXA | se rechaza el paquete entero; la página dice "Urgent intervention executed…" y ofrece retrospectiva; nada queda retenido (P3) | torniquete no aplicado; mensaje falso | `clarification_required` con gate `urgent_unheld` | `_validate` no acepta duración para TXA; `app.py` avisa antes de `execute_bundle`; `awaiting_explanation` no mira `execution_status` | aceptar la duración; avisar sólo tras ejecutar | — |
| C09 | CRITICAL | ES | escalar O2 + «satura 86% con la naricera» | reservorio 15 L | 2.ª orden fantasma (naricera); responder «15 litros» → reservorio + naricera 15 L/min, y queda la naricera (`checks2_59g`) | dispositivo equivocado | «Nasal cannula at 15 L/min» | herencia del verbo; «satura» no es signo; `complete_bundle` llena la orden fantasma | no heredar el verbo a piezas de estado | — |
| H01 | HIGH | EN+ES | conector + orden («, so give…», «, así que le paso…», «, por lo que…», «, entonces…») | orden | no reconocida, retiene (EN03, EN07, EN11; V03) | retención en asma, sepsis y shock | el modelo guarda la orden | sólo se quita then/luego; "I'm giving" no es intención | quitar conectores consecutivos | — |
| H02 | HIGH | ES+EN | «Ahora/Primero/Now/First» inicial | orden | no reconocida, incluso con verbo; «Primero E-FAST» se pierde (ES07, ES39, ES24; V01) | retención o pérdida | ES07: modelo = orden | `_parse_piece_core` no quita el adverbio | tratarlo como «luego» | — |
| H03 | HIGH | EN+ES | hallazgo o meta tras la orden ("target sats…", "she's bleeding…", "her BP is 95…", «está con PA…») | orden + razón | la cláusula hereda el verbo y queda «no reconocida» (EN09, EN31, EN34; V05) | orden correcta retenida | — | herencia + vocabulario cerrado | una pieza de estado no hereda | rel. KD-12 |
| H04 | HIGH | ES | «2 U de GR», «10 U» | transfusión | retiene (ES11, P5); «2 U GR» en silencio | transfusión retenida | — | falta «gr» y «u» como unidad | agregar GR y U | — |
| H05 | HIGH | ES | «pruebas cruzadas por 4 U de GR» | pruebas cruzadas | perdida en silencio (ES10) | reserva no registrada | — | `_TRANSFUSING` toma la preposición «de» como «dé» | excluir «de» | — |
| H06 | HIGH | EN+ES | estudio con x2, dos o artículo | hemocultivos, lactato | perdidos en silencio (EN06, ES06; V12) | bundle incompleto | modelo = «Blood cultures x2…» | diagnóstico sin verbo exige `fullmatch` | admitir conteo y artículo | — |
| H07 | HIGH | ES+EN | dosis compartida «cada uno/c-u/each» | ambos 1 g | se pierde el primero sin aviso (ES19; V17); EN46 retiene | ejecución parcial | — | regla KD-02; sin regla de dosis compartida | leer la dosis por ítem | KD-02 |
| H08 | HIGH | EN+ES | «más/plus» | 2 órdenes | retiene; el ketorolaco queda «no modelado» y no se da (EN15, ES06; V07) | analgésico no dado | registro falso de «no modelado» | falta separador; `_UNMODELED_ORDER` clasifica la pieza entera | separar por «más/plus» | — |
| H09 | HIGH | EN(+ES) | verbos y volúmenes coloquiales (hang, run, push, bump, «tírale», «un litro») | bolo o titulación | nada o no reconocida (EN17 P2, EN28) | volumen no dado en shock | sin acción | `_COMMAND` y volúmenes en palabras | ampliar vocabulario | rel. KD-15 |
| H10 | HIGH | ES+EN | marcapaso sin verbo; «el output a 80 mA» | marcapaso 70/60 | nada, o no reconocido (ES37; V08) | BAV sin marcapaso | — | `shorthand` sin marcapaso | agregarlo | — |
| H11 | HIGH | ES+EN | «insulina 10 U ev con SG 10%» | insulina registrada + glucosa | infusión de SG sin tasa; la insulina desaparece (ES36; V18) | responder la tasa da SG sola | insulina nunca registrada | insulina fuera de `_UNMODELED_ORDER` | registrarla como no modelada | — |
| H12 | HIGH | EN+ES | suspender heparina en curso | stop | "No infusion is running" (falso) o "needs an explicit new dose" (EN31) | callejón sin salida | — | stop de fármaco de dosis fija | permitir el stop de una dosis con duración | — |
| H13 | HIGH | ES+EN | suspender el fluido de un plan explicado | razón propia | hereda como «shared» «espero que suba la PA» y el gate no pregunta (checks_59o; P5) | — | expectativa atribuida a una decisión opuesta | `apply_plan` compara tipos, no la operación | no compartir con stop o adjust | — |
| H14 | HIGH | ES | «No más X: cambio a NBZ continua 10 mg/h» | NBZ continua | nada; mensaje genérico en inglés (ES05, P1) | escalada no hecha | — | la negación llega al fin de la oración; «cambio» no es verbo | cortar la negación en «:» | — |
| M01 | MEDIUM | EN+ES | vía compartida + «luego/then» en la oración | vía a todas | pide «vía para bronchodilator» (EN01, EN06, EN39; P1) | 1 vuelta extra | — | `_share_trailing_route` sale ante cualquier secuencia | mirar sólo entre la dosis y la vía | DF-16a |
| M02 | MEDIUM | EN+ES | reevaluación con BP/vitals + examen | control a N min | reevaluación a 0 min y lactato ahora; «signos vitales c/15» → "study not recognized" (EN07, EN11, EN45, ES44) | reloj no avanza | — | la lista de signos no tiene bp, vitals ni «signos vitales» | ampliar la lista | KD-10 (lactato) |
| M03 | MEDIUM | EN+ES | control «en 1 hora» | control a 60 min | no programado; queda en la expectativa y el gate pregunta (EN33, ES11) | pregunta innecesaria | expectativa contaminada | sólo acepta minutos | aceptar horas | rel. KD-13 |
| M04 | MEDIUM | EN+ES | contingencia con verbo fuera de lista ("place…", «50 mg en bolo») | plan | descartada sin aviso (EN24, EN29) | — | plan perdido | lista fija de verbos | guardar todo lo que sigue a «si» | — |
| M05 | MEDIUM | EN+ES | máximo, PRN/SOS sin «repetir», titulación, rango | dosis + esquema | «max 10 mg» retiene; esquema no registrado (EN44, ES43, ES28, EN41) | retención de analgesia | esquema ausente | `_REPEAT_START` exige verbo | leer q/c-N + PRN y el máximo | rel. KD-09 |
| M06 | MEDIUM | EN+ES | sinónimos (pip-tazo, BNP, coags, echo, «gastro/EDA», PTM, infusión de IBP) | orden o estudio | retiene o pide el servicio (EN21, EN30, ES10, ES12, ES22, ES30) | retenciones repetidas | — | vocabulario cerrado | ampliar; lo no modelado, registrarlo | — |
| M07 | MEDIUM | ES | «Cambia a mascarilla de reservorio a 15 L» | O2 | pide el dispositivo (V09) | retención | — | `_oxygen_order` lee «de… a…» | excluir «de reservorio» | — |
| M08 | MEDIUM | ES+EN | enoxaparina 1 mg/kg c/12 h | dosis por peso | "Specify the dose and the dose units" (ES31) | retención | esquema perdido | `_validate` no convierte kg | convertir o explicar | — |
| M09 | MEDIUM | ES | alta «consultar si…» | aviso de regreso | queda como plan condicional (ES20) | — | mal rotulado | `_ADVICE_CLAUSE` sin «consultar» | agregarlo | junto a KD-06 |
| M10 | MEDIUM | EN | repetición «…if she is still wheezing» | sin modelo | modelo = «still wheezing» (EN02) | el gate no pregunta | modelo atribuido | captura por hallazgo | excluir la condición | — |
| M11 | MEDIUM | EN+ES | entrada sólo con plan o retención | plan registrado | «Registrado como plan» + "Please specify…"; queda `clarification_required` (P2, P6) | — | un plan válido parece fallo | `_validate` sin acciones | estado propio «plan registrado» | — |
| M12 | MEDIUM | ES | mensajes en la interfaz española | español fiel | sin traducir o a medias; la cita del residente se altera («start» → «inicio») | — | sólo en pantalla | `language.MESSAGES`; `say()` reemplaza dentro de las comillas | completar y proteger las citas | rel. KD-08 |
| M13 | MEDIUM | EN | "D50 one amp" | 25 g | dosis nula (EN39) | retención | — | exige volumen | decisión docente: 1 ampolla = 50 mL | — |
| L01 | LOW | EN+ES | control diferido de examen | examen luego | examen ahora (EN07, EN36, EN38, ES27, ES38) | resultado antes de tiempo | — | alcance de DF-16b | como KD-10 | KD-10 |
| L02 | LOW | EN+ES | colas | cita limpia | «y lo», "and I'll", ", so"; `of` equivocado (EN27); corte a 80 caracteres («…2 hor») | — | cita no literal | patrón de efecto; `[:80]` | cortar en palabra | KD-13 |
| L03 | LOW | EN+ES | razón no capturada | modelo | ausente (EN05, EN16, EN36, EN43, ES16, ES17) | el gate puede preguntar | menor captura | vocabulario cerrado; «por» | medir | KD-12/13 |

## Fricción de jugabilidad (59O)

| ID | Sev | Dónde se traba el residente | Recomendación |
|---|---|---|---|
| 59O-01 | HIGH | "Please specify a question, investigation, treatment, or reassessment." no cita el texto y no está traducido (19 frases, 9 pasos de página). | Citar lo no leído y separar «sólo plan». |
| 59O-02 | HIGH | «Registrado como repetición/plan…» junto a "Please specify…", con una orden no dada dentro de la cita (P1, P2). | Decir «X no se administró» y retener. |
| 59O-03 | CRITICAL | "Urgent intervention executed" cuando nada corrió, y oferta de retrospectiva (P3). | Avisar sólo tras ejecutar. |
| 59O-04 | MEDIUM | El gate pide «¿qué vas a controlar?» ante «lo reevalúo en 15 min»; 4 líneas en inglés (KD-08); resumen «2000 mg». | Aceptar el control general o prellenar el campo. |
| 59O-05 | HIGH | «Las demás órdenes quedan retenidas» cuando nada quedó retenido (P2, P5). | Decir «reescribe la orden completa». |
| 59O-06 | CRITICAL | Preguntas atadas a acciones mal leídas: O2 fantasma, tasa de SG ante insulina, vía ya escrita. | Nombrar el fármaco o dispositivo y citar el texto. |
| 59O-07 | HIGH | Todo o nada: un fragmento dudoso retiene el torniquete, la BiPAP o el O2. | Ejecutar lo inequívoco y urgente; retener lo dudoso. |
| 59O-08 | HIGH | Formas frecuentes que obligan a reformular sin saber cuál se acepta. | Sugerir en el mensaje la forma aceptada. |
| 59O-09 | MEDIUM | Decisiones imposibles: parar heparina, NTG sublingual, infusión de IBP, insulina, «SV c/15 min». | Registrarlas como «indicado, no modelado». |
| 59O-10 | MEDIUM | Interfaz en español con inglés mezclado justo cuando el residente está trabado. | Completar las traducciones. |
| 59O-11 | MEDIUM | «3 ampollas de 20 mL» pide el total (por diseño). | Decisión docente. |
| 59O-12 | MEDIUM | Un plan válido queda `clarification_required`. | Estado propio. |
| 59O-13 | LOW | La reevaluación en horas pide minutos. | Aceptar horas. |
| 59O-14 | LOW | La cita se altera en pantalla. | Proteger la cita. |
| 59O-15 | LOW | Ítems no modelados «registrados» en una entrada retenida: si se reenvía, se duplican. | Registrar sólo al ejecutar. |

**Observación de la sesión principal sobre 59O-15:** es la única fricción que
toca la duplicación de evidencia (59AH). No se corrigió: registrar sólo al
ejecutar cambia qué guarda el Trace de una entrada retenida, y eso es una
decisión de diseño del Trace, no un bug inequívoco.

## Lectura

- **Las clases CRITICAL son de estructura de la oración.**
  - Son: «:», «, si no responde,», «Ahora… luego repetir», razón sin coma + 1.ª persona, «cambia a», «on/con» tras el destino, y un hallazgo tras coma.
  - El corpus de ensayo no las trae; por eso el baseline dio 96/96.
- **Pérdidas que la página muestra como ejecutadas.** En C02, C05, C06 y C07 la entrada figura como ejecutada porque corre otra acción de la misma entrada.
- **Lo que pesa en la traza:**
  - el modelo de trabajo guarda el texto de la orden (C02, H01, H02, H06);
  - el plan compartido se hereda en una decisión opuesta (H13);
  - la retrospectiva se ofrece para algo que no corrió (C08).
- **Límites.**
  - Las frases son de la IA y la estructura esperada es juicio del auditor; la frecuencia real en residentes es UNKNOWN.
  - La página se jugó en inglés; lo que ve la interfaz en español se obtuvo con `language.say(…, "es")`.
  - C09 se reprodujo con `pending_family_orders.complete_bundle`, la misma función que llama la página, no con un paso de página.
- **Dónde quedó la evidencia.** Los guiones y sus salidas quedaron en el
  espacio temporal de la sesión, fuera del repositorio. Cada hallazgo se
  reproduce pasando su frase por `family_parser.parse_family_actions`.
