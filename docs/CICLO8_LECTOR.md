# Ciclo 8 · Lector: TD-29, TD-30, TD-31, TD-32 y KD-05

Ciclo 8 · 2026-09-28 · alcance registrado en `COLA_DECISIONES_AI_ADVISOR.md`,
«Apertura del ciclo 8».
Registro: C-2026-09-28-19 (TD-29), -20 (TD-30), -21 (TD-31), -22 (TD-32) y
-23 (KD-05).
Pruebas: `test_cycle8_reader_classes.py`.

**Principio, el mismo del ciclo 7.** Lo que la persona residente indica con
claridad nunca se pierde en silencio:

- se ejecuta, si el motor lo modela;
- se registra, si no lo modela o si es un plan;
- se pregunta, si es de verdad ambiguo.

Y lo que no es una orden ahora (un plan, un relato, lo ya hecho, lo de otro,
una pregunta) no se ejecuta.

**El lector de comparación** es el V2 congelado (`9d2cd9e`, HARDENED BASELINE
V2). Todas las frases de este documento son **INTERNAL DEVELOPMENT DATA**: nada
aquí estima cuántas órdenes reales de un residente se leen bien.

## Qué hace ahora el lector

| Clase | Qué escribe la persona residente | Antes (V2) | Ahora |
|---|---|---|---|
| **TD-29** | «When BP drops, give NS 500 mL», «Cuando baje la PA, bolo SF 500 mL», «Transfundir 2 U GR cuando Hb < 7», «Once stable, transfer to the ward», «Apenas la HGT baje de 70, pasar glucosa al 30% 60 mL» | Corría ahora (la sangre, en cambio, preguntaba) | **Plan condicional**, registrado y no ejecutado, como ya pasaba con «si/if» |
| TD-29 | «Cuando puedas…», «as soon as possible», «When I examined him his BP was 80/50, give 1 L NS», «Once intubated, start propofol», «Apenas mejora la PA con volumen, iniciar noradrenalina» | Corría ahora | Igual: corre ahora |
| TD-29 | «When blood arrives, transfuse 2 units» (algo que se espera, sin valor por alcanzar) | Preguntaba | Igual: pregunta |
| TD-29 | Lo que una condición manda y el lector no sabe ejecutar: «Once MAP is above 65: stop the bolus and run NS at 100 mL/h», «if bleeding continues, place a second one», «Si persiste hipotensa, agregar vancomicina 25 mg/kg ev» | Se perdía sin aviso o se citaba | **Plan condicional**, si la condición gobierna toda la frase |
| TD-29 | «Lo doy de alta. Regresar si tiene fiebre.» | Se perdía el aviso | **Indicación al paciente** |
| **TD-30** | «Surgery consult», «GI consult», «IC a urología», «IC uro», «cards consult», «Hemorrhage control: surgery consult» | Se perdía | **Interconsulta** a su servicio; «cirugía/surgery» es cirugía general; una subespecialidad («vascular surgery») sigue preguntando cuál |
| TD-30 | «Endoscopía urgente», «EDA urgente», «urgent upper endoscopy», «solicitar endoscopía», «urgent scope» | Se perdía o era «estudio no reconocido» | **Interconsulta a gastroenterología**, que en el motor hace la endoscopía una hora después si el paciente está reanimado |
| TD-30 | «Hemocultivos x2», «take blood cultures x2 from two sites», «Blood cultures x2, then ceftriaxone» | Se perdían los cultivos | **Hemocultivos**, junto al antibiótico |
| TD-30 | «2 large-bore IVs (16G)», «two 18G IVs» | Se perdía o se citaba | **Vía venosa** |
| TD-30 | «RL 500 ml ev», «Mientras tanto RL 500 ml», «Meanwhile NS 500 bolus» | Se perdía o se citaba | **Ringer lactato / el fluido** |
| TD-30 | Lo ya hecho o pendiente: «Surgery already saw him», «la interconsulta ya fue respondida», «EDA de ayer normal», «Scope done», «Blood cultures pending», «hemocultivos x2 y urocultivo ya tomados», «ya tiene 2 VVP» | Varias se leían como pedido | Nada se pide |
| **TD-31** | «Epinephrine IM now», «Adrenalina IM ya», «Epi 1:1000 IM», «Adrenalina 1 mg/mL IM», «IM epi stat» | Una infusión que preguntaba mcg/min, o nada | **La orden IM sin dosis**: el motor pregunta la dosis IM en mg |
| TD-31 | «Give IM epi, anterolateral thigh» | El sitio se citaba y retenía la orden | El sitio es de la inyección |
| **TD-32** | «2 U. GR», «2 U. PRBCs» | Se perdía o preguntaba el número | **2 unidades** |
| TD-32 | «Deactivate MTP», «Desactivar PTM», «stand down the MTP» | Se perdía o se citaba | **Registrado como protocolo desactivado**, sin revertir ninguna unidad |
| TD-32 | «Platelets if count < 50», «plaq 1 U c/10 kg si recuento < 50 mil» | Se perdía | **Plan condicional** |
| TD-32 | «Type and cross pending», «pruebas cruzadas en curso» | Pedía otra prueba cruzada | Nada se pide |
| TD-32 | «2 U GR en 2 horas c/u», «2u PRBC over 2h each», «Transfundir 2 U GR, pasar en 2 hrs c/u» | 2 horas en total, o se preguntaba | **4 horas**: el tiempo de cada unidad se suma |
| **KD-05** | «OK to discharge home», «ok for d/c home», «he's ok to go home», «OK para alta», «ok para la casa» | No se leía | **Alta** |
| KD-05 | «Not ok to dc», «ok to go home?», «todavía no está OK para alta», «exámenes OK» | — | Nada |
| KD-05 | «Discharge home with an EpiPen prescription», «Alta, paracetamol 1 g c/8 h», «Ok para alta, …, prednisona 40 mg x 5 días» | **El alta se perdía** en la receta, o la receta se leía como dosis y su pregunta retenía el alta | El alta corre y **la receta se registra como receta** |

## Correcciones tras la revisión adversarial (post hoc)

La revisión adversarial halló que las reglas nuevas rompían lecturas que el V2
hacía bien: 6 CRITICAL, 10 HIGH y 7 MEDIUM, todas del propio ciclo. Se
corrigieron antes de medir el segundo conjunto ciego, y cada frase marcada se
volvió a leer con el lector y con el motor.

| Qué se rompió | Ejemplo | Ahora |
|---|---|---|
| **Una descripción con «cuando» se volvía condición** y la orden se perdía sin aviso | «Mareada cuando la PA baja a 80/50, SF 500 ml ev», «Presyncope when BP drops below 90 on standing, epinephrine 0.5 mg IM now» | Lo que el residente vio no es condición: corre la orden, como en V2 |
| Relatos en indicativo o en pasado, con el residente como sujeto o con «once again» | «Cuando se acuesta la saturación cae a 85%, …», «When I examine her she is hypotensive, give 1 L NS», «Once again BP low, NS 500 mL bolus» | Igual: son descripciones. En español, la condición va en subjuntivo («cuando baje») o es un umbral («cuando Hb < 7») |
| El estado de un examen se llevaba la orden siguiente | «Hemocultivos tomados y ceftriaxona 2 g ev», «Lactate pending so give 30 mL/kg LR» | El estado cierra en «y», «then», «so», un guion o una orden; la orden corre |
| **«OK to d/c …» era un alta** | «OK to d/c IV fluids», «OK to dc norepi» | Suspender no es dar de alta: nada, como en V2 |
| Una autorización pospuesta, negada o de otro daba el alta ahora | «OK to dc home after 4 h observation», «OK to discharge: no», «Per surgery, OK to discharge», «Ok para alta dosis de salbutamol» | Nada. Con un curso del paciente es un plan: «OK for d/c home once afebrile» |
| **«Epi» daba la adrenalina de otro o de antes** | «Epi 0.5 mg IM given by EMS», «Epi 0.3 mg IM 20 min ago», «Epi IM q5-15 min PRN» | No se da. «Epi» es adrenalina sólo con su dosis con unidad o su vía, nunca ante un puntaje («Epi 8/10 pain») |
| Una interconsulta pedida con verbo se perdía si algo más estaba «ya» | «Consult urology for decompression since she is already septic», «Llamar nuevamente a cirugía que ya lo vio» | Es interconsulta |
| La interconsulta sin verbo corría negada, diferida o comentada | «Surgery consult not needed», «GI consult in AM», «IC a cirugía pendiente», «Surgery consult?» | No se pide |
| Una derivación tras el alta retenía el alta | «Discharge home with allergy referral», «Alta con interconsulta a inmunología» | El alta corre y la derivación es su plan |
| «IC con FE…» era una interconsulta; «blood cx», cirugía; «Social work consult» retenía el antibiótico | — | Insuficiencia cardiaca, cultivos y un servicio no clínico, como antes |
| Una endoscopía de los antecedentes llamaba a gastroenterología | «EDA por várices hace 1 año», «EGD for banding last year» | Sin verbo, la endoscopía pide su urgencia |
| El control en horas era el tiempo del tratamiento | «Furosemida 40 mg ev con control de diuresis en 2 h» corría en 2 horas | El control no es duración |
| Unidades que suman más de 120 min quedaban retenidas con un mensaje genérico | «2 U GR en 2 horas c/u» | El motor lo dice: «2 units over 4 h in all…», en ambos idiomas, como ya con un fluido; también «SF 1000 ml ev durante 8 h» |
| El punto de «U.» unía dos frases | «Transfuse PRBC 2 U. Platelets if count < 50.» | Sólo se salta ante glóbulos rojos no nombrados antes |
| La desactivación del PTM se registraba preguntada o como tiempo | «Stop MTP?», «Once we stop MTP, recheck labs» | No se registra |
| El propósito de las pruebas cruzadas era su estado | «Type and cross 4 units to be ready for the OR» | Se piden, como en V2 |
| «Consultar cirugía si…» y «Volver a controlar…» eran consejo al paciente | — | Un plan y nada, como en V2 |
| «Hemocultivos x2, urocultivo y ceftriaxona» retenía el antibiótico preguntando por el urocultivo | — | El urocultivo se registra como pedido, sin resultado, como la prueba de embarazo |

Y dentro de las clases, lo que el V2 ya fallaba y la revisión encontró:

- **Planes que corrían ahora:**
  - «Discharge home when afebrile x 24 h», «Alta cuando esté asintomático y
    tolere VO»;
  - «Intubar cuando se agote», «Intubate once she becomes drowsy»;
  - «D50 50 mL IV when FSBG < 60», «Paracetamol 1 g ev cuando T° > 38,5».
- **Repeticiones con su condición:** «NS 500 mL bolus now then repeat when SBP
  < 90» y «Salbutamol 5 mg NBZ ahora, cuando la sat baje de 92% repetir». La
  primera dosis corre y la repetición queda como plan.
- **Receta del alta:** «Ok para alta con adrenalina autoinyectable» ahora
  registra la receta.

## Correcciones tras la segunda revisión adversarial (post hoc)

Un segundo revisor independiente atacó esas correcciones con 301 frases EN/ES,
por el lector y por el motor, en las ocho familias. Halló 73 filas peores que
el V2, de unas nueve causas, y otras donde el V2 y el lector fallaban igual
dentro de las clases. Todo se corrigió post hoc, rotulado en el registro
(C-2026-09-28-19, -20, -22 y -23):

| Qué pasaba | Ejemplos | Ahora |
|---|---|---|
| **«Once» como «una dosis», ante una razón, hacía un plan** | «Epinephrine 0.5 mg IM once since she is hypotensive», «Ceftriaxone 2 g IV once since she's febrile» | Corre ahora, como en V2. «Once» es condición sólo con el valor o el estado del paciente justo después |
| **Una autorización con plazo, observación o condición daba el alta ahora** | «OK to dc home in 4 h», «OK para alta post observación de 6 horas», «OK to discharge home, pending repeat lactate», «Ok para alta siempre que tolere VO», «OK para alta por urología» | Nada, como en V2. Lo que el alta manda a la casa conserva sus tiempos: «Ok para alta, control en APS en 48 h, prednisona 40 mg x 5 días» da el alta |
| **Lo que el paciente hace, seguido de lo que se vio, hacía un plan** | «O2 NC 2 L, when she walks her sats drop», «SF 500 ml ev ahora, cuando se para la PA baja», «NS 500 mL IV now, when SBP < 90 she gets dizzy» | La orden corre, como en V2 |
| El estado de otro examen se tomaba como el de las pruebas cruzadas | «Pruebas cruzadas 4 U mientras hemograma pendiente»; «type and cross 2 units - sent» retenía el bolo | Sólo cuenta el estado escrito con ellas, y no se pregunta |
| Las unidades de otro fármaco pasaban a los glóbulos rojos | «Insulina 10 U. GR 2 U» | Se transfunde, como en V2 |
| Una suspensión del PTM negada o pospuesta se registraba | «Can't stop MTP yet», «Aún no suspender PTM», «Stop MTP after this cooler» | No se registra; con su condición es un plan |
| Una interconsulta pospuesta o ya hecha corría | «Surgery consult after CT», «IC a cirugía, ya la vio», «Urgent endoscopy for varices, done yesterday» | No se pide |
| Un torniquete «ya puesto» se ponía de nuevo | «Suspender PTM, torniquete ya puesto» | No se pone |

Dentro de las clases, lo que el V2 ya fallaba y ahora se lee:

- **Planes:** «Alta cuando esté afebril», «Alta una vez controlado el dolor»,
  «Discharge home once tolerating PO», «once she ambulates with SpO2 > 92%».
- **Interconsultas:** «IC a cirugía ya» y «consult for recs» la piden.
- **Altas:** «OK to dc pt home», «OK to d/c home - no need for admission» y
  «OK para alta pero con control en 48 h» dan el alta; «adrenalina
  autoinyectable 0,3 mg IM SOS» tras el alta es su receta.
- **Otros:** «c/u en 1 h» suma el tiempo de cada unidad; «Volver a SAR si…» y
  «Consultar a su médico si…» son indicación al paciente.

**Qué queda:**

- «Observe 6 h then discharge home» y «Alta en 2 horas» dan el alta ahora. Es
  anterior al ciclo y está también en `939978a` (TD-39, HIGH).
- Dos lecturas ambiguas se mantienen: «When rechecked FSBG < 60, D50 50 mL IV
  now» queda como plan (el V2 daba la glucosa), y «EDA hoy por gastro, sin
  sangrado activo» llama a gastroenterología.
- Lo que el V2 también falla está en TD-40.

**Rendimiento.** Una nota larga con cientos de «when» tardaba 8 s en leerse.
Las ventanas nuevas quedaron acotadas, como las demás, y ahora baja de medio
segundo (TD-27).

## Qué no cambió

- Los eventos críticos, el −3, los puntajes, D1–D5 y el radar.
- La fisiología: nada nuevo tiene efecto propio. La interconsulta a
  gastroenterología y la vía venosa ya existían en el motor.
- «Si/if» se leen como antes. Lo único nuevo en ellos: se guarda como plan lo
  que una condición manda aunque el lector no sepa ejecutarlo, y el «if» tras
  «check/decidir/preguntar» no es una condición.
- Un envío que sólo trae un plan no ejecuta ni retiene nada. La sala dice
  «Recorded as a conditional plan, not executed now: …» y el Trace lo registra.
  Después agrega el aviso genérico «Please specify…», como ya pasaba con «si»
  (TD-38).

## Validación A–J

Cada frase de los conjuntos lleva sus etiquetas: qué debe correr ahora, qué
debe quedar registrado, qué no debe correr y si una pregunta es aceptable. El
puntaje automático corre cada frase por el lector y por el motor, en un caso de
su familia. «OK» quiere decir que todo eso se cumple.

| Paso | Qué se hizo | Resultado |
|---|---|---|
| **A · Conjunto independiente** | 80 frases EN/ES escritas para estas clases antes de desarrollar, con controles negativos | V2: 31/80 (25 perdidas, 9 ejecuciones falsas). **Lector final: 79/80**, 0 perdidas y 0 falsas; la que falta es de otra clase: «está con PA 85/50» citada como orden |
| **B · Conjunto ciego 1, medido una vez** | 70 frases que el lector no había visto; md5 registrado al recibirlo y al medir | V2: 29/70. **Lector medido: 41/70**: 10 perdidas, 18 retenidas con una pregunta, 1 pregunta mal contada (error del puntaje automático, abajo) y 0 ejecuciones falsas |
| **C · Cambios post hoc, rotulados** | Tras el ciego 1, las formas que halló dentro de las clases. Tras la revisión adversarial, las correcciones de la sección anterior | Ciego 1 post hoc: **52/70** (V2 con el mismo puntaje: 30/70). Quedan 3 perdidas y 15 retenidas, todas de otras clases (TD-14, TD-35) |
| **D · Controles negativos** | En los conjuntos: relatos, «cuando puedas», lo ya hecho, lo de otro, preguntas, autorizaciones negadas | 0 ejecuciones falsas en el independiente y en el ciego 1 post hoc |
| **E · Revisión adversarial** | Un revisor independiente escribió unas 390 frases para romper las reglas nuevas | 6 CRITICAL, 10 HIGH y 7 MEDIUM, todas regresiones del ciclo, corregidas. Cada frase marcada se lee hoy igual que en V2 o mejor. Una **segunda revisión**, sobre esas correcciones (301 frases), halló 73 filas peores que el V2: tras corregirlas, 63 se leen como el V2 y 7 mejor; 2 quedan ambiguas y 1 es un defecto anterior al ciclo (TD-39, TD-40). Las 436 filas de la primera revisión se leen igual que antes de la segunda ronda, salvo una que ahora queda como plan |
| **F · Comparación con V2 sobre todo texto del repositorio** | 13 221 textos (pruebas, herramientas, conjuntos y corpus anteriores) | 96 se leen distinto fuera de las pruebas del ciclo, y todas se revisaron: son mejoras de clase o citas textuales (TD-28). Apareció una regresión (un relato prehospitalario con «iban a iniciar»), que se corrigió. La segunda ronda sumó dos, correctas: «Una vez estable: TAC de abdomen» queda como plan |
| **G · Conjuntos del ciclo 7** | 149 frases de hemoderivados, re-puntuadas | Totales iguales a V2, salvo H-ES-20 («vendaje compresivo apenas disminuya el sangrado»): el lector lo guarda como plan y la etiqueta del ciclo 7 lo pedía ahora. Es un desacuerdo de etiqueta; se mantiene la lectura gramatical |
| **H · Suite completa y 56 regresiones** | Cuatro particiones, más las regresiones | __SUITE__ |
| **I · Ensayo de los 20 escenarios ES/EN** | Por la página real, semilla 3000, 0 llamadas de IA | __REHEARSAL__ |
| **J · Conjunto ciego 2, medido una vez con el lector final** | 50 frases, reservadas hasta el final | __H2__ |

**El error del puntaje automático.** Contaba como pregunta equivocada que una
infusión de adrenalina escrita sin velocidad pidiera su velocidad, que es lo
correcto. Se corrigió después del ciego 1 y antes del ciego 2, en el puntaje del
lector nuevo y en el del V2. Por eso el ciego 1 medido dice 41 y no 42.

## Límites documentados

- **Todas las frases son INTERNAL DEVELOPMENT DATA.** Las escribieron agentes
  independientes, no residentes. Ningún número de aquí estima la fidelidad del
  lector con texto real; eso lo medirá el piloto.
- **El ciego 1 ya no es ciego después de medirlo.** Sus formas guiaron cambios
  post hoc, y 23 de sus frases comparten texto con pruebas del ciclo. Por eso su
  resultado post hoc se da aparte del medido.
- **El ciego 2 no quedó intacto del todo.** Antes de medirlo, una búsqueda accidental sobre el directorio de trabajo mostró el texto de 5 de sus 50 frases (H2-C29-EN-03, H2-C31-EN-01, H2-C31-EN-03, H2-C31-EN-04 y H2-C31-EN-05). Ninguna regla se ajustó sobre ellas. Otras 3 (H2-C30-EN-03, H2-C31-ES-02 y H2-C32-ES-02) contienen entera una frase de 20 caracteres o más de las revisiones adversariales o de las pruebas del ciclo; se comprobó sólo por identificador, sin mostrar el texto, y otra vez tras la segunda ronda, sin casos nuevos. El resultado se da entero, sobre las 42 limpias y sobre las 8 marcadas.
- **La gramática decide casos ambiguos, y puede errar.**
  - En español, «cuando» con indicativo («cuando la PA baja a 80/50, SF 500
    ml») se lee como descripción y la orden corre, como en V2. La condición
    se escribe en subjuntivo («cuando baje»).
  - En inglés no hay esa marca. Cuentan como descripción la primera persona,
    el pasado, y una acción del paciente seguida de lo que se vio («when she
    walks her sats drop», «when he talks his sats drop to 88%»). Con un umbral
    es condición («once she ambulates with SpO2 > 92%»). «When BP drops, give
    NS» sigue siendo plan.
  - «Once» ante una razón o «now» es «una vez», una dosis.
- **Lo que queda fuera de las clases** está en `REGISTRO_DEUDA_TECNICA.md`:
  - TD-14: vocabulario;
  - TD-34: «reevaluar en 1 h» corre a los 0 minutos;
  - TD-35: exámenes abreviados en una lista que se pierden;
  - TD-36: un estado leído como orden;
  - TD-37: la receta del alta en lista;
  - TD-38: el aviso de un envío que sólo trae un plan;
  - TD-39: un alta con plazo o tras una observación corre ahora;
  - TD-40: lo que la segunda revisión dejó, igual que en el V2.
- **KD-05 sigue presente en los dos baselines registrados.** El piloto se mide
  contra ellos.
