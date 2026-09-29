# Registro de deuda técnica

Ciclo 5 del AI Advisor (59BQ), 2026-09-28, con la extensión nocturna.
**Actualizado al cierre del ciclo 8** (2026-09-28): lo corregido pasa a
«Corregido en el ciclo 8», con su registro; lo nuevo (TD-34 a TD-40) lleva su
evidencia. Los cierres de los ciclos 7 y 6 siguen más abajo.

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
| TD-01 | Caso clínico | `acs_54m_inferior`: el caso y el motor tienen VD comprometido; el POCUS dice VD normal. **Ciclo 7:** su C14 es NO (C-2026-09-28-11), por la oportunidad de observación; **la contradicción de datos sigue** | El residente ve datos que se contradicen; si confía en el POCUS y da nitratos, la fisiología lo castiga | `AUDITORIA_ACS_54M_INFERIOR.md` | ciclo 4 (borrador C14) | No (sin SCA) | DF-20 A/B/C/D: NEEDS NICOLÁS |
| TD-33 | Motor · trauma | **Residuo de TD-21.** Con el sangrado controlado y la pérdida repuesta con cristaloide (torniquete + 3 L de SF), transfundir 2 U dispara la sobrecarga: la regla da la pérdida por repuesta con cristaloide y la familia trauma no diluye la Hb | Tras el error típico (cristaloide en vez de sangre), la sangre «hace daño»; no es un evento crítico ni toca el puntaje | `docs/TD21_SOBRECARGA_TRANSFUSIONAL.md`, residuo; sonda de rúbrica del ciclo 7 | ciclo 7 | No para el piloto de validación (sin trauma); para uno con residentes, avisar al docente o decidir | Decisión docente: que sólo la sangre reponga el déficit en esa regla (recomendado; una línea) |
| TD-14 | Lector | **Lo que queda tras DF-22, medido por los tres conjuntos ciegos del ciclo 6.** Vocabulario: «amp of D50», nitroglicerina SL o en infusión, heparina e insulina por kilo, «epi drip», «Narcan», «Page GI», «STEMI code», destinos (floor, OR, pabellón), fluidos (D5W, glucosalino, cristaloides), «run/hang/push», «5.000». Formas: una condición escrita como rótulo sin «si» (el rótulo ya no se salta, pero lo que sigue corre ahora); una retención después del fármaco («y alteplase tampoco por ahora»); una receta en lista tras el alta (KD-06); lo que hizo el equipo prehospitalario seguido de coma, o un pensamiento seguido de «y» («pensando en dar X y poner Y»); insulina con SG (H11); y las 14 clases HIGH de la auditoría del ciclo 5 (H01–H14). **Ciclo 8:** el conjunto ciego halló fuera de sus clases, casi todo retenido con una pregunta: exámenes abreviados («coags», «BMP», «BNP», «PCR», «TP/TTPA», «crea»), nombres comerciales y abreviados («protonix», «pip-tazo», «azithro», «duoneb», «solumedrol», «benadryl», «Mag sulfate», «Vitamin K», «SG 30 %»), el oxígeno «alto flujo» o «titrate 93–95 %», los horarios («q15min», «c/15 min», «may repeat in 5–15 min», «titulando a PAM > 65»), un hallazgo citado como orden («está con PA 85/50»), el verbo de una lista que no llega a lo siguiente («Pedir gases venosos, NBZ…») y el destino «medicina interna». Lo que de eso se pierde sin aviso está en TD-35 | En el motor, la mayoría se retiene con una pregunta (63 de 108 y 19 de 32 en los conjuntos ciegos); las tres lecturas falsas medidas quedaron retenidas | `MEDICION_RECONOCIMIENTO_ORDENES.md` (ciclo 6); `AUDITORIA_TRACE_CICLO5.md` (H01–H14) | ciclo 5 | No: el piloto las mide | Tras el piloto de validación, priorizadas por su medición |
| TD-34 | Lector | **Una reevaluación en horas abreviadas corre a los 0 minutos:** «Reevaluar en 1 h», «Reassess in 1 h», «in 1 hr», «en 2 h». El tiempo no avanza y no hay aviso. «1 hora» u «hour» sí preguntan los minutos. Además, «Control en 1 hora» y «Control en 30 min» no se leen; «Control en 1 h», que antes preguntaba por un examen, ahora tampoco, como «1 hora». Igual en el V2 | La reevaluación ocurre en el acto: el residente ve al paciente como si no hubiera pasado el tiempo | hallado en el ciclo 8 al revisar los residuos del conjunto ciego | ciclo 8 (anterior al ciclo) | No para el piloto de validación (lo mide); para uno con residentes, decirles que escriban los minutos | Próximo ciclo: «h/hr» como horas (se preguntan los minutos, como con «hora»), con A–J |
| TD-36 | Lector | **Un relato o un estado leído como orden:** una dosis escrita antes de quien la dio se da de nuevo («Epinephrine 0.5 mg IM given by EMS», «Aspirin 300 mg given by EMS»); «torniquete ok» pone un torniquete; «Epinephrine given at 10:32» inicia una infusión que pregunta su velocidad; «Adrenalina IM ya administrada por SAMU» pregunta una dosis IM (el V2, una velocidad). Igual en el V2. Con el equipo como sujeto («El SAMU dio aspirina 300 mg») se pregunta y no corre. En el ciclo 8, la forma abreviada («Epi 0.5 mg IM given by EMS») ya no corre | Una dosis dada dos veces, o una medida que nadie pidió | hallado en el ciclo 8 y en su revisión adversarial | ciclo 8 (anterior al ciclo) | No para el piloto de validación (lo mide); para uno con residentes, decirles que escriban lo recibido en ruta con su sujeto | Próximo ciclo: el participio de la dosis («given», «administrada», «dada») con quien la dio, como ya el relato con sujeto |
| TD-39 | Lector | **Un alta con plazo o tras una observación corre ahora:** «Discharge home in 2 hours», «Alta en 2 horas», «Alta tras 6 horas de observación», «Observe 6 h then discharge home» y, dentro de una lista, «Salbutamol 5 mg NBZ, OK to discharge home in 2 hours». Igual en el V2 y en el SPANISH PILOT BASELINE `939978a`. En el ciclo 8, «OK to discharge…» con plazo, sola en su oración, ya no da el alta (queda sin leer, como en el V2) | Un alta prematura, que en anafilaxia o asma puede disparar los eventos críticos ligados al alta | segunda revisión adversarial del ciclo 8; comprobado en `939978a` | ciclo 8 (anterior al ciclo) | No para el piloto de validación (lo mide); para uno con residentes, decirles que escriban el alta cuando corresponda darla | Próximo ciclo: el alta con plazo u observación como plan (o la observación de D4 seguida del alta), con A–J |

## MEDIUM

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| KD-02 | Lector | Fármaco sin verbo ni dosis no es orden; en una lista se pierde sin aviso | Orden perdida en silencio | `KNOWN_DEFECTS.md` | ciclo 4 | No (medir) | Decisión docente: ¿preguntar la dosis? |
| KD-03 | Lector / interacción | Texto escrito con una aclaración pendiente se toma como su respuesta | Una orden nueva puede leerse como respuesta | ídem | ciclo 4 | No (la herramienta cancela) | Fase 2 |
| KD-11 | Trace | Una indicación de vigilancia queda como modelo de trabajo | Cita no fiel | ídem | ciclo 4 | No | Familia DF-7 |
| KD-15 | Lector | Fluido nombrado en palabras sin verbo («IV fluids 1 L») no es orden | Envío retenido | ídem | ciclo 5 | No (fase EN) | Clase de nombres de fluido, con decisión docente |
| TD-31 | Motor | **Resto de TD-31:** «Direct pressure with packing» son dos medidas y el motor suma su efecto, que controla el sangrado como un torniquete (regla de medidas combinadas, sin cambio). La primera mitad, la adrenalina IM sin dosis, se corrigió en el ciclo 8 | Un control algo mayor que el de cada medida | revisión del ciclo 7 (T37) | ciclo 7 (anterior al ciclo) | No | Decisión docente: la regla de medidas combinadas |
| TD-35 | Lector | **En una lista sin verbo, los exámenes abreviados y los nombres comerciales que el lector no conoce se pierden sin aviso** mientras lo demás corre: «CBC coags lactate now», «CBC BMP coags lactate», «hemgrama, TP/TTPA, BUN/crea», «protonix 80 IV». Igual en el V2. Es la clase de KD-02 con el vocabulario de TD-14 | Orden perdida sin aviso | conjunto ciego del ciclo 8 (H-C29-EN-01, H-C29-EN-02, H-C29-ES-01) | ciclo 8 (anterior al ciclo) | No (el piloto lo mide) | Con KD-02 (decisión: ¿preguntar?) y el vocabulario de TD-14 |
| TD-37 | Lector | **«Discharge prescription: prednisone 40 mg daily x 5 days, cetirizine 10 mg daily»:** el alta corre, la prednisona se pierde sin aviso y la cetirizina se registra como fármaco no modelado, no como receta. Igual en el V2 | Receta perdida | hallado en el ciclo 8 | ciclo 8 (anterior al ciclo) | No | Con las recetas del alta (KD-05, KD-06) |
| TD-40 | Lector | **Residuos de las clases del ciclo 8 que dejó la segunda revisión adversarial, iguales en el V2:** la endoscopía urgente con su propósito o su momento («EDA urgente para ligadura de várices», «EDA urgente previa estabilización», «Endoscopy within 24 h») y «IC urgente a cirugía ya» se pierden sin aviso; «Alta con adrenalina 0,3 mg IM SOS» pierde la receta; tras «hemocultivos tomados en SAPU y», una dosis contada como dada allá se da de nuevo (TD-36); en inglés, una condición con «we» o partida por «and» corre ahora («Norepinephrine 0.1 mcg/kg/min when MAP < 65 after we give 2 L», «Once she has had 30 mL/kg and MAP remains < 65, start norepinephrine»), y «when stridor recurs» también; «Return to OR if rebleeds» y «Reconsultar a cirugía si persiste el sangrado» se pierden. Dos lecturas quedan ambiguas y se mantienen: «When rechecked FSBG < 60, D50 50 mL IV now» queda como plan (el V2 lo daba) y «EDA hoy por gastro, sin sangrado activo» llama a gastroenterología | Orden perdida sin aviso o, en las condiciones en inglés, una orden que corre antes de tiempo | segunda revisión adversarial del ciclo 8 (`docs/CICLO8_LECTOR.md`) | ciclo 8 (anterior al ciclo) | No (el piloto lo mide) | Con TD-14 y TD-36, por clase y con A–J |
| TD-02 | Evidencia | No existe «oportunidad ofrecida pero no demostrada»: se confunde con pendiente o con desempeño insuficiente | Lectura injusta del progreso | auditoría nocturna, anexo 59AJ | ciclo 5 | No | DF-17, tras el piloto C14 |
| TD-03 | Procedencia | Los vínculos de marco de los 8 Decision Challenges no se congelan con la observación, sólo la versión del mapping | Una exportación por hito leería los vínculos actuales | auditoría nocturna, anexo 59BG | ciclo 5 | No | Antes de cualquier exportación por marco |
| TD-04 | Datos clínicos | Todo el POCUS del banco sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`) | C14 declara oportunidades sobre hallazgos de POCUS que el código aún llama borrador | `clinical_cases.py:64` | antes del ciclo 1 | No | Que el docente confirme el POCUS de los casos C14 YES (DF-23) |
| TD-05 | Pruebas | `test_generation_reload.py` muta módulos globales al importarse | Posible contaminación entre pruebas si el `reload` falla | auditoría nocturna, anexo 59R | ciclo 5 | No | Cuando se toque ese archivo |
| TD-08 | Datos clínicos | **Oclusiones coronarias, lo que queda tras el ciclo 6.** De Winter se corrigió (C-2026-09-28-08). Quedan ambiguos: el grado de «reduced» en `acs_70f_left_main` y `acs_54m_inferior`; el pulmón por defecto «No B-lines» del tronco frente a crepitantes y congestión; y la pared que vuelve a «contract normally» a las 2–3 h de reperfundir mientras el evento dice «recovers only partly» | Textos que no dicen lo mismo que el resto del caso | `docs/AUDITORIA_DF23_CICLO6.md` §1 y §5 | ciclo 5 | No (sin SCA) | Decisión docente (cola de decisiones, CLINICAL REVIEW) |
| TD-09 | Desempeño | La cola docente resuelve la elegibilidad objetivo por objetivo, verificando otra vez la huella 17 veces por encuentro: 3,2 s con 1000 encuentros pendientes y 14,5 s con 5000 | Página docente lenta con cohortes grandes | auditoría nocturna, sección 3 (perfilado) | ciclo 5 | No | Antes de cohortes de más de ~20 residentes (DF-24) |

## LOW

| ID | Área | Descripción | Evidencia | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|
| KD-04, KD-07, KD-08, KD-09, KD-10, KD-12, KD-13, KD-14 | Lector / Trace | Los residuos LOW de DF-16 y DF-11 | `KNOWN_DEFECTS.md` | No | Según el piloto |
| TD-07 | Idioma | La razón y la evidencia esperada de C14 se muestran en inglés en el portal docente en español | auditoría nocturna, sección 5 | No | Con revisión docente de la traducción |
| TD-10 | Observabilidad | El Trace no guarda el commit por turno, sólo al iniciar el encuentro | auditoría nocturna, anexo 59AP | No | Campo corto, cuando se toque el Trace |
| TD-11 | Lenguaje de docs | «validated trajectory» significa «probada», no validación clínica | README | No | En textos nuevos |
| TD-18 | Integridad | Migración: la foto de una confirmación absorbe observaciones posteriores (I-F18); directiva y encuentro en dos transacciones (I-F09); `sequence` sin restricción única (I-F06); duplicados previos o un JSON corrupto tiran la vista (I-F19/20); errores sin registro (I-F10) | auditoría nocturna, sección 1 | No | DF-24 dejó fuera I-F18 (ciclo 7); el resto, sin decisión |
| TD-19 | Clínica menor | `bradycardia_bb_54f` corregida (llega somnolienta, C-2026-09-28-08). Quedan: `anaphylaxis_63m_betablocked` con pulso irregular y monitor sinusal (dos arreglos posibles); embarazo no redactado en 4 mujeres, y la pregunta por la última regla responde con el inicio de los síntomas | `docs/AUDITORIA_DF23_CICLO6.md` §2–§4 | No | Decisión docente |
| TD-38 | Sala | Un envío que sólo trae un plan (una orden condicional o una indicación al paciente) no ejecuta ni retiene nada: la sala dice «Recorded as a conditional plan, not executed now: …» y el Trace lo registra, pero después agrega el aviso genérico «Please specify a question, investigation, treatment, or reassessment.», como ya pasaba con «si» | ciclo 8 (`docs/CICLO8_LECTOR.md`) | No | Mostrarlo como registrado, sin el aviso, cuando se toque la sala |

## Corregido en el ciclo 8

| ID | Qué | Registro |
|---|---|---|
| TDFC | TD1, F1, C1 y C3 declarados caso por caso en 30 casos con el modelo de C14 (TD1 25 YES / 5 NO, F1 25/5, C1 18/12, C3 10/20). `acs_54m_inferior` espera DF-20 y conserva la transición | C-2026-09-28-17 |
| TD-29 | «Cuando», «when», «once», «en cuanto», «una vez que», «tan pronto como» (y «apenas» con subjuntivo) hacen de una orden un plan cuando nombran el estado del paciente. «Cuando puedas», un relato y lo que sólo se espera se leen como antes. Lo que una condición manda se guarda aunque el lector no pueda ejecutarlo. Tras la segunda revisión adversarial: «once» ante una razón es una dosis, y lo que el paciente hace seguido de lo que se vio es relato | C-2026-09-28-19 |
| TD-30 | Interconsultas sin verbo (también «IC uro», «cards», «gen surg»), la endoscopía pedida (una llamada a gastroenterología), los hemocultivos con su número, las vías por su número o calibre y «RL» ante un volumen. Lo ya hecho, pendiente o respondido no se pide, tampoco lo que se pide «después del TAC» | C-2026-09-28-20 |
| TD-31 (primera mitad) | La adrenalina IM sin dosis pregunta su dosis en miligramos, nunca una velocidad. La regla de medidas combinadas sigue abierta (arriba) | C-2026-09-28-21 |
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
