# Fase 3 · Traza de manejo de extremo a extremo en la hemorragia digestiva (desarrollo)

**Ciclo P3-503 a P3-517 · decisiones docentes FD-MTRACE-01 a FD-MTRACE-10 · 2026-11-22.**

**Qué es.** Un encuentro de **desarrollo** del choque hemorrágico por hemorragia digestiva alta, con la autoridad viva de desarrollo de presión de GI y el control manual de norepinefrina tal como están publicados. Diez caminos de manejo, del mismo arribo, muestran que **decisiones distintas producen trayectorias causalmente distintas** y que **el mismo estado con la misma acción produce el mismo resultado**. Cada encuentro se lee como una **traza de manejo** (estado → prioridad → acción → efecto esperado → respuesta observada → reevaluación → nuevo estado) derivada de los eventos del propio encuentro, y se entrega a la facultad como una revisión interactiva.

**Qué no es.** No es una calibración de curvas, ni fisiología nueva, ni control de fuente, ni autoridad de consciencia o terminal, ni despliegue a residentes, ni validación clínica. Nada de `clinical_core/`, del lector, del motor, de las concesiones ni de las instantáneas se tocó. `COMMON_CORE_RUNTIME_AUTHORITY = False`.

## 1. Auditoría de capacidades (P3-503, sólo lectura, verificada en código y con sondas en la autoridad viva)

| Capacidad | Estado | Evidencia (código y sonda) |
|---|---|---|
| Cristaloide (bolo, infusión lenta) | SUPPORTED | `runtime_shadow_families.gi_interventions` → entrega común con el núcleo del cristaloide de la instantánea ratificada; sonda: 1 L/15 min sube la PAS de 88 a 94 en 15 min. |
| Glóbulos rojos | SUPPORTED_WITH_LIMITATION | mismo camino de entrega; respuesta en el extremo bajo (`GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE`, monitoreada). |
| Sangrado continuo | SUPPORTED | la tasa ratificada corre en todos los minutos; ningún camino la detiene. |
| Norepinefrina: inicio, aumento, reducción, suspensión, reinicio | SUPPORTED | concesión `GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1`; tasas absolutas explícitas en mcg/min; todo lo demás falla cerrado de forma permanente. |
| Esperar / reevaluar | SUPPORTED | `Reassess in N minutes` gobierna el turno (máximo 120 min por paso; más largo se rechaza, nunca se acorta). |
| Parada efectiva | SUPPORTED | límite de colapso, orden no soportada o mal formada, cualquier falla dura; sin retroceso. |
| Artefacto y repetición | SUPPORTED | `runtime_authority.verify_artifact` y `replay_site_artifact` sobre cada camino. |
| Observar | SUPPORTED_WITH_LIMITATION | la presión es la de la autoridad; FC, estado mental y demás vienen del motor heredado (§8, hallazgo H2). |
| Persistir | SUPPORTED | la página escribe la traza del residente (`management_trace_v1` + `phase0_v1`); la autoridad, su artefacto sellado. |
| IBP (pantoprazol) | SUPPORTED_WITH_LIMITATION | modelado (reduce el sangrado al 80 %), **nunca revisado** por la facultad en una trayectoria: identificado como mejora posible sin fisiología nueva, **no** usado en los caminos. |
| Interconsulta de gastroenterología → endoscopia | **alcanzable, no revisado** | el motor heredado hace la endoscopia 60 min después de la interconsulta si la PAS ≥ 90 y el núcleo común aplica `EndoscopicHemostasis`; sonda: con norepinefrina, endoscopia al minuto 75 y presión plana 105/64 hasta el 180. Ver §2 y hallazgo H1. |
| Control de fuente definitivo como manejo revisado | UNSUPPORTED (para este paquete) | fuera de la frontera (FD-MTRACE-05). |

## 2. Frontera del encuentro de desarrollo (P3-504)

**Entrada.** Llegada predefinida (`AUTHORED`) de `gi_bleed_57m` o `gi_bleed_72f`, minuto 0, sin orden ejecutada, con la autoridad viva abierta bajo la concesión de norepinefrina (instantáneas de presión y de tono ratificadas).

**Salidas, deterministas.** La frontera es la **primera en el tiempo**: una solicitud cuenta en el minuto de la decisión; una parada, un cierre terminal o el horizonte, al final de su turno. Las demás salidas del mismo turno **se nombran** en el bloque de frontera («Also in this turn»), nunca se ocultan:

1. `DEFINITIVE_HAEMOSTASIS_REQUESTED`: una orden que pide el control definitivo del sangrado (interconsulta de gastroenterología, cirugía o radiología intervencionista, endoscopia o embolización), **cualquiera que sea su destino en el libro de órdenes**: ejecutada, registrada sin modelar («Consult GI.»), retenida o no reconocida («Page the gastroenterologist.»). Se lee en el texto y la forma canónica de la orden (no en todo el turno: «transfundir por la hemorragia digestiva» no es una solicitud), sólo en las clases interconsulta, endoscopia, procedimiento, plan y no reconocida. Una mención negada también cuenta: la frontera llega **antes**, que es la dirección conservadora de FD-MTRACE-05. La frontera es el minuto de la solicitud y **nada posterior** pertenece al encuentro.
2. `ENGINE_HAEMOSTASIS_EVENT`: un evento del motor que informa un procedimiento de control (defensa en profundidad), con su propio mensaje.
3. `AUTHORITY_STOP`: la parada efectiva de la autoridad, con su propia clase, en el turno en que ocurrió; **ningún turno posterior** pertenece al encuentro (la página tampoco deja continuar). Un minuto que la autoridad comprometió y luego desautorizó no es una observación.
4. `LEGACY_TERMINAL_STATE`: el motor heredado cerró el encuentro, con un mensaje propio que no lo interpreta.
5. `DEVELOPMENT_HORIZON`: minuto 120 (propuesto para la revisión; la existencia de la frontera es decisión docente, el número no). Un turno que cruza las dos horas se muestra completo y el mensaje lo dice.

**Mensaje.** «Development model boundary. This development encounter covers only the initial resuscitation of an upper gastrointestinal bleed, up to two hours after arrival. The bleeding has not been controlled in this encounter: definitive control of the bleeding source is outside this development model. Reaching this point does not mean that the patient has recovered, that the bleeding has stopped, that management is complete, or that discharge is safe.» Para la solicitud de control definitivo hay una variante que dice que la solicitud quedó registrada y que lo que sigue queda fuera del modelo.

## 3. Traza de manejo: esquema y procedencia (P3-505, P3-505A)

`development_management_trace.py` (puro: no importa Streamlit, motor, autoridad ni núcleo). Un paso por turno:

`decision_minute`, `response_minute`, `state` (presión y lectura), `priority` (`scenario` y `resident`, separados), `action` (texto y órdenes del libro con destino y disposición), `expected` (`model` y `resident`), `observed` (presión y el minuto comprometido de la autoridad: concesión, instantánea, digesto del candidato), `reassessment` (minuto, origen del intervalo, lectura, lo que dijo el residente), `new_state`, `limitations`.

**Cada valor lleva una sola clase de procedencia**, sin mezclarlas: `OBSERVED` (lo que produjo el encuentro), `AUTHORED` (escrito antes: la llegada, la acción de un camino guionizado, la prioridad o la categoría propuestas), `MODEL_DERIVED` (lectura fija de lo que el modelo representa o de un umbral fijo), `FACULTY_DEFINED` (la frontera), `RESIDENT_EXPRESSED` (lo que el residente escribió o respondió, tomado del registro de la propia página), `UNKNOWN`.

**Política del razonamiento del residente.** Sólo se toma de `reasoning` del evento de la página (`management_priority`, `expected_effect`, `reassessment_target`/`reassessment_plan`), **exactamente** y **con la procedencia que la propia página registra** (`reasoning_provenance`): lo escrito en la entrada o completado en la compuerta es del residente (lo completado se rotula «completed in the follow-up»); lo escrito en otro momento conserva su rótulo (antes en el encuentro, compartido con un plan, retrospectivo); **lo que la aplicación compuso** a partir de otras palabras nunca se muestra como del residente: queda `NOT_EXPRESSED` con una nota. Si no está, `NOT_EXPRESSED`. Nunca se infiere de la acción. La acción es la entrada del residente **sin** la transcripción que la página le anexa tras la compuerta («Guided reasoning completion», formato de la aplicación); una aclaración que el residente teclea después se conserva. La prioridad de un camino de desarrollo se guarda aparte, como `AUTHORED`, rotulada «proposed for faculty review». `trace_problems` rechaza una traza cuyo campo del residente no sea exactamente lo expresado bajo su procedencia, cuya acción no sea el texto del turno con su procedencia, cuya presión rotulada como de la autoridad no tenga su minuto comprometido, cuyo estado no sea el nuevo estado del paso anterior (o la llegada predefinida) con la misma procedencia, cuyos minutos retrocedan o cuyo digesto no recompute.

**Lo que nunca dice.** `claim_problems` rechaza «resuscitated», «shock corrected», «bleeding controlled», «stable», «recovered», «safe for discharge», «management complete» en toda lectura generada. Toda lectura dice que el sangrado no está controlado; con vasopresor, que es soporte temporal.

## 4. Contrato temporal (P3-509)

No hubo ambigüedad que exigiera la salida C. La regla es la del motor y es determinista:

- un **intervalo de reevaluación declarado** gobierna el turno (en la página, también el de la compleción guiada de la compuerta de razonamiento);
- sin intervalo, el turno dura **lo que dura lo administrado**: 1 L en 15 min = 15 min; **2 U de glóbulos = 60 min** (el residente no puede actuar durante esa hora: es un artefacto de semántica de turno, declarado);
- las actividades de información toman sus propios minutos; una espera de más de 120 min se rechaza;
- la presión se **observa al final de cada turno** (un minuto comprometido por la autoridad por turno); los minutos intermedios se **validan** pero no se observan.

Ventanas examinadas con sondas: órdenes en el mismo minuto (volumen y norepinefrina juntos; vía IV sin avance de reloj), 5, 10, 15, 20–30 y 60 min. Todos los caminos del paquete declaran su intervalo (15 min), de modo que la respuesta la decide la fisiología y no el turno.

## 5. Caminos A–J (P3-506, P3-507, P3-511)

Mismo arribo (57 años, 88/54, PAM 65, con acceso venoso ya colocado); pasos guionizados; cada turno no planificado es «Reassess in 15 minutes». Los pasos de B, D, E, I y J **dependen del estado observado** (se dan en la primera reevaluación con hipotensión, PAS < 90 o PAM < 65, o sin ella para el destete): así la acción responde al estado que tiene delante (P3-515, sin desajuste estado/acción). Lo esperado se escribió **antes** de la corrida certificada; una sonda exploratoria de la auditoría (P3-503) corrió antes y se declara. Categoría: **propuesta** para la revisión (FD-MTRACE-02), nunca mostrada antes de Q6.

| Camino | Categoría propuesta | Pasos dados (minuto) | PAS/PAD por minuto (0 · 15 · 30 · 60 · 75 · 90 · 105 · 120) | PAM pico | PAM final | Hipotenso al final |
|---|---|---|---|---|---|---|
| A volumen + sangre | REASONABLE | 0: 1 L SF/15 min + 2 U GR | 88/54 · 94/58 · 94/58 · 93/57 · 89/54 · 85/52 · 82/50 · 78/48 | 70 (15) | 58 | sí |
| B luego norepinefrina | REASONABLE | 0: volumen + GR; 75: NE 5 | … · 89/54 · 96/59 · 92/57 · 89/54 | 71 (90) | 66 | sí |
| C norepinefrina primero | TEMPORIZING | 0: NE 10; 30: volumen + GR | 88/54 · 100/61 · 95/58 · 104/64 · 105/64 · 105/64 · 100/62 · 96/59 | 78 (75) | 71 | no |
| D aumento de tasa | REASONABLE | 0: volumen + GR; 75: NE 2; 105: NE 8 | … · 89/54 · 91/56 · 87/53 · 92/56 | 70 (15) | 68 | no |
| E destete y suspensión | REASONABLE | 0: volumen + GR; 75: NE 10; 90: NE 5; 105: stop | … · 89/54 · 101/62 · 92/57 · 78/48 | 75 (90) | 58 | sí |
| F vasopresor solo | INCOMPLETE | 0: NE 10 | 88/54 · 100/61 · 95/58 · 84/52 · 79/49 · 74/46 · 69/43 · 64/40 | 74 (15) | 48 | sí |
| G cristaloide lento | TEMPORIZING | 0: 1 L SF/60 min | 88/54 · 85/52 · 82/51 · 76/47 · 71/44 · 67/41 · 62/38 · 57/35 | 65 (0) | 42 | sí |
| H sin tratamiento | CLEARLY_NONBENEFICIAL | — | 88/54 · 84/51 · 79/49 · 71/43 · 67/41 · 62/38 · 58/36 · 54/33 | 65 (0) | 40 | sí |
| I escalada sin volumen | CLEARLY_NONBENEFICIAL | 0: NE 5; 45: NE 10; 60: NE 15; 75: NE 20 | 88/54 · 95/58 · 90/55 · 84/52 · 82/50 · 78/48 · 73/45 · 68/41 | 70 (15) | 50 | sí |
| J suspendida demasiado pronto | INCOMPLETE | 0: volumen + GR; 75: NE 10; 90: stop | … · 89/54 · 101/62 · 82/50 · 78/48 | 75 (90) | 58 | sí |

**Orden causal (P3-511A), todo verificado por prueba y sin contradicción material:** volumen y sangre atienden el volumen (A > H); la norepinefrina sostiene la presión (B > A a la lectura siguiente; F, C > H a los 15 min); la norepinefrina sola no controla el sangrado (F e I terminan por debajo de A y siguen cayendo); el sangrado continuo erosiona toda ganancia (cada camino termina por debajo de su pico); reducir o suspender quita el soporte causalmente (E y J vuelven **exactamente** al curso de A); el cristaloide lento no alcanza (A > G ≥ H). **Determinismo:** B, E e I repetidos dan la misma trayectoria y el mismo digesto de traza; las diez trayectorias son distintas entre sí.

**Segundo caso (72 años, 98/62):** mismas relaciones; tras volumen y sangre la presión **no vuelve a ser hipotensa antes del minuto 120**, así que los pasos dependientes del estado de B, D, E y J **no se dan** (quedan registrados como no dados) y esos caminos son el curso de A. Es un hecho del modelo, no un ajuste.

## 6. Sólo autoridad viva (P3-508)

Cada transición de presión es un minuto **comprometido** del artefacto de la autoridad viva (concesión `GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1`, instantáneas `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` y `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`, rótulo `REAL_DEVELOPMENT_PRESSURE_AUTHORITY`); la traza guarda el digesto del candidato de cada minuto. No hay sustitución por la sombra, tabla precalculada ni atajo fármaco→presión. El ejecutor (`test_gi_management_trace_paths.DevelopmentEncounter`) es la composición de dos arneses certificados —`pilot_acceptance.Encounter.order` (la rama de familia del camino de órdenes de la página) y las llamadas del sitio del `Driver` certificado— y una prueba sobre la **página real** (AppTest) muestra que da las mismas presiones para las mismas órdenes.

## 7. Extracción, serialización, repetición y lectura docente (P3-512, P3-512A)

La traza se extrae de los eventos: los turnos (de la página: `turn_from_page_event`; del ejecutor: `turn_from_runner_entry`, los mismos campos) y el artefacto. Liga: id y versión del encuentro (digesto de su definición), camino y digesto del plan, concesión, instantáneas, digesto del artefacto, observaciones, órdenes, eventos, reevaluaciones, efectos, minutos y frontera. Sobrevive a la serialización JSON y se **reextrae** idéntica de sus insumos persistidos (una sesión que reinicia desde ellos lee la misma traza). El registro de revisión guarda, por camino, esos insumos (los turnos y la vista del artefacto que la extracción lee, `artifact_view`) y una prueba reextrae cada traza **sólo desde el registro**; los artefactos completos verifican y se repiten.

Ejemplo (camino E, paso 6, lectura docente):

> **6 · Minute 75 → 90** — *State* (model reading): BP 89/54 mmHg (MAP 66) · hypotensive (SBP below 90 mmHg or MAP below 65 mmHg) · bleeding not controlled. — *Scenario priority* (development path, proposed for faculty review): Support a perfusion pressure that is low again after volume and blood; the bleeding still needs definitive control. — *Resident reasoning*: not expressed. — *Action* (development path): Start norepinephrine at 10 mcg/min. Reassess in 15 minutes. — *Expected (model)*: A vasopressor supports the pressure while it runs. It does not replace volume and does not stop the bleeding. Time passes. The bleeding continues. — *Observed*: BP 101/62 mmHg (MAP 75) at minute 90. — *Reassessment*: MAP rose by 9 mmHg; not hypotensive at this reading; the pressure is partly vasopressor support: temporary, not control of the bleeding; the bleeding is not controlled in this encounter. — *New state*: BP 101/62 mmHg (MAP 75) · not hypotensive at this reading · on vasopressor support (temporary) · bleeding not controlled.

## 8. Auditoría de seguridad educativa (P3-513)

Las diez lecciones engañosas, medidas sobre los caminos (prueba `test_c4`): (1) la norepinefrina no reemplaza el volumen (F, I < A); (2) los glóbulos no detienen el sangrado (A se erosiona; cada paso lo dice); (3) una presión normal no es reanimación completa (toda lectura «not hypotensive» lleva «bleeding not controlled»); (4) **ningún** estado mental, consciencia ni FC aparece en la traza ni en la revisión; (5) la observación prolongada empeora (H, propuesto como claramente no beneficioso); (6) el control de fuente no ocurre en silencio (ninguna hemostasia dentro de un camino; una solicitud termina en la frontera); (7) ninguna acción no soportada pasa como manejo (ninguna parada); (8) ningún razonamiento atribuido (todo campo del residente de un camino guionizado es `NOT_EXPRESSED`); (9) ninguna respuesta temporal rotulada definitiva; (10) nada puntúa la presión.

**Hallazgos que requieren decisión docente (no bloquean este paquete; sí cualquier exposición a residentes):**

- **H1 · Control de fuente alcanzable en la página viva.** La premisa de FD-MTRACE-05 («el control de fuente no está representado») no coincide con el código: una interconsulta de gastroenterología lleva a una endoscopia del motor y a `EndoscopicHemostasis` del núcleo común, nunca revisadas. Este paquete la deja fuera (salida 1); bloquearla o revisarla en la página viva es una decisión docente.
- **H2 · Estado mental visible desacoplado de la presión bajo norepinefrina.** En la página viva el estado mental es del motor heredado, cuyo propio modelo de norepinefrina mantiene su presión: en F se ve 64/40 con «Alert» (la PAS heredada es 87), mientras sin vasopresor ya es «Drowsy» con 67/41. Es la limitación abierta `CONSCIOUSNESS_UNDER_TONE_UNRESOLVED`; aquí no se muestra.

## 9. Paquete de revisión docente (P3-514, P3-514A)

`GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW` (`docs/revision/PHASE3_GI_MANAGEMENT_TRACE_V1_REVIEW_SET.json`, sellado, versionado, indexado y fijado en `faculty_management_review.PINNED_SET_DIGEST`): los diez caminos del caso de 57 años, uno por pantalla, en la misma *Faculty Trajectory Review*: qué se juzga, contexto, qué se hizo, trayectoria de presión con cada intervención marcada, valores, **traza de manejo** con la procedencia de cada línea, **frontera**; Q1–Q5 y **Q6 · MANAGEMENT MEANING** (razonable, temporizador, incompleto, claramente no beneficioso), bloqueo irreversible, juicio global, resumen. La categoría propuesta y las limitaciones aparecen **sólo** en el resumen final. El lanzador la ofrece después de las retenciones anteriores (interruptor del operador `MRS_FACULTY_MANAGEMENT_GATE=off`). Sin parámetros, sin internos, sin FC ni estado mental.

## 10. Revisión adversarial independiente (P3-515)

Una revisión de sólo lectura atacó los quince frentes del encargo. Cada hallazgo material se **reprodujo antes** de corregirlo y quedó fijado por prueba:

- **M1 · Razonamiento compuesto mostrado como del residente.** La página compone una prioridad a partir de otras palabras (en la página real, de la respuesta de la compuerta) y la marca como compuesta; la traza la mostraba «as expressed». Ahora se lee la procedencia de la página (arriba, §3). La transcripción que la página anexa tras la compuerta tampoco es ya parte de la acción.
- **M2 · Solicitudes de control definitivo que no activaban la frontera** («Consult GI.», la de radiología intervencionista: registradas sin modelar). Ahora cuenta toda solicitud, cualquiera que sea su destino (§2).
- **M3 · La presión de llegada (predefinida) rotulada como observación de la autoridad** tras un turno que no mueve el reloj. Ahora el estado arrastra su procedencia y `trace_problems` comprueba la cadena.
- **M4 · El registro nombraba un código generador que no estaba en el árbol.** El conjunto se regeneró con el código final y la prueba exige `same_generating_code`.

Menores corregidos: el orden de salidas (una parada anterior a una solicitud ganaba la solicitud; una parada en el mismo turno quedaba oculta), mensajes propios para el evento de hemostasia del motor y el cierre terminal, la nota del turno que cruza el horizonte, el minuto desautorizado por la autoridad, la regla de turno rotulada `MODEL_DERIVED` (no `OBSERVED`), la orden «Place an IV line.» (el libro la ignoraba como ya hecha: acción que no correspondía al estado; se quitó de los caminos), los propósitos de F, H e I (adelantaban la conclusión que pregunta Q6) y la reextracción desde el registro solo. Antes de la revisión, las propias pruebas hallaron dos defectos de prueba: el ejecutor dejaba las banderas de la autoridad en el entorno del proceso (contaminaba las pruebas siguientes) y la prueba de página heredaba la reconstrucción histórica de la sesión de pruebas. **Declarado, no corregido:** cada bloque de un camino guionizado dice «Resident priority: not expressed» (la nota de la pantalla lo explica). Sin hallazgo en los demás frentes (repetición, determinismo, fuga al residente, variables ocultas, sobrescritura del registro).

## 11. Qué no se hizo

Sin fisiología nueva, sin control de fuente, sin recalibrar GI ni el tono, sin ampliar la autoridad en familias limitadas por la bomba, de consciencia ni terminal, sin despliegue a residentes, sin afirmación de validación clínica; `clinical_core/`, el lector, el motor, las concesiones y las instantáneas sin cambios.

## 12. Certificación y punto de control (P3-516, P3-517)

Una certificación completa sobre **una sola huella** (`46f637c3c34e70fab91b7fa77cd169f7f8315155257a41ad0e21a6889fbdad9c`, la misma al inicio y al final): suite particionada (24 particiones) con **14691 pruebas: 14584 aprobadas, 7 fallas, 0 errores, 99 omitidas, 1 xfail**. Las 7 fallas son el tiempo de espera de 20 s de AppTest bajo carga, en cuatro archivos de portales ajenos a este paquete; repetidos solos sobre la misma huella: **31 aprobadas, 0 fallas** (ambiental). `run_regressions.py`: **56/56 activas**, 10 retiradas según el propio ejecutor. Punto de control `GI_MANAGEMENT_TRACE_CHECKPOINT_V1` (`docs/revision/PHASE3_GI_MANAGEMENT_TRACE_CHECKPOINT.json`, sellado, versionado e indexado), veredicto **A · `GI_END_TO_END_MANAGEMENT_TRACE_READY_FOR_HUMAN_REVIEW`** (FD-P3-301). El registro, su entrada en el índice, el pin movido y FD-P3-301 se agregaron después de la huella certificada.

**Siguiente acción humana:** una persona docente entra en la revisión docente de desarrollo («Management trace review (GI paths)», que el lanzador abre una vez completas las revisiones anteriores) y revisa los diez caminos. Aparte, y sólo si se quiere: decidir H1 y H2.
