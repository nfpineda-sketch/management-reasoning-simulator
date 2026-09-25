# Decisiones clínicas pendientes

Reúne en un solo lugar lo que requiere su criterio, clínico o educativo, surgido del
trabajo del 2026-09-24 y 2026-09-25 (hallazgos de la tanda de diez, ensayo de la tanda de
veinte y sondeos por la página real). Ninguna regla clínica ni criterio educativo se
cambió para que una prueba terminara. Cuando hubo que elegir para seguir trabajando, la
elección fue la más conservadora y reversible, y aparece aquí marcada **«provisional»**.

Cada punto dice: **dónde apareció**, **qué hace hoy el simulador**, **por qué**, **qué
impacto tiene**, **opciones** (con mi recomendación) y **si decidir distinto obliga a
repetir** algo.

Índice:

- A. Cambian lo que registra la tanda de 20 (idealmente antes de ejecutarla): 1-6
- B. Criterios de evaluación: 7-11
- C. Capacidades que el simulador no tiene: 12-13
- D. Funciones nuevas que necesitan su aprobación: 14-15

---

## A. Cambian lo que registra la tanda de 20

### 1. Un alta pide «qué va a controlar», y un control ambulatorio no cuenta

- **Dónde**: sondeo por la página real (`hypoglycemia_28m`, 2026-09-25). En la tanda dan
  alta los guiones 4, 7, 12, 13 y 18.
- **Hoy**: «Lo envío a su casa», con interpretación, prioridad y expectativa, queda
  retenido: *Still to state: what you will check*. «Lo envío a su casa **con control en
  policlínico en 48 horas**» también queda retenido: el control ambulatorio no se lee como
  lo que se va a controlar. (La orden retenida, además, decía «admission to home»; eso era
  un defecto de redacción y ya está corregido: ahora dice «discharge home».)
- **Por qué**: el destino está entre las acciones que exigen las cuatro categorías, y el
  lector busca un control dentro del encuentro.
- **Impacto**: un alta razonable con seguimiento hace una pregunta más al residente. Los
  eventos de alta insegura (`hypo_unsafe_discharge`, `opioid_unsafe_discharge`,
  `anaphylaxis_unsafe_discharge`) se juzgan por el alta ejecutada, no por esa respuesta.
- **Opciones**: (a) mantener; (b) aceptar un plan de seguimiento (control ambulatorio
  con plazo, signos de alarma, cuándo volver a consultar) como lo que se controla en un
  alta; (c) sacar el alta de la regla.
- **Recomendación**: (b). El seguimiento con plazo es la reevaluación que corresponde a
  un alta: mantiene la exigencia y no vuelve a preguntar lo que el residente ya dijo.
- **¿Repetir?**: no. Los guiones con alta responden la pregunta; (b) sólo cambia cuántas
  preguntas se hacen, no lo que se ejecuta.

### 2. Dosis escritas como concentración y volumen, o por kilo

- **Dónde**: sondeo 2026-09-25; guion 20 (se escribió «enoxaparina 60 mg sc» porque
  «1 mg/kg» se retiene); los guiones de hipoglicemia escriben «glucosa 25 g».
- **Hoy**: «Doy glucosa al 30% 50 ml ev» se retiene: *Please specify or confirm the
  dextrose dose in grams*. «Enoxaparina 1 mg/kg sc» y «heparina 80 UI/kg ev» se retienen:
  *Specify a supported fixed dose and route; this medication order uses weight or
  infusion-rate units*.
- **Por qué**: el motor dosifica en gramos y en dosis fijas; no calcula desde la
  concentración ni desde el peso.
- **Impacto**: la orden no se ejecuta hasta que se reescribe, y esos minutos cuentan para
  las ventanas (una hipoglicemia, un TEP).
- **Opciones**: (a) mantener, con un mensaje que muestre la conversión esperada; (b)
  calcular siempre: concentración × volumen para la glucosa (30 % × 50 ml = 15 g) y mg/kg
  con el peso del caso, mostrando en el registro la dosis calculada; (c) calcular sólo la
  glucosa (aritmética, sin juicio clínico) y seguir pidiendo dosis fija para lo que va por
  kilo.
- **Recomendación**: (c) ahora; (b) para el peso cuando cada caso declare un peso
  verificado.
- **¿Repetir?**: no. Los guiones usan dosis fijas.

### 3. Medicamentos sin efecto modelado: reconocidos y no ejecutados (provisional)

- **Dónde**: ensayo de la tanda; guiones 12 (clorfenamina; autoinyector al alta) y 18
  (lorazepam).
- **Hoy**: antihistamínicos, antagonistas H2, benzodiacepinas, antieméticos, autoinyector
  y recetas al alta se devuelven como *Recognized but not executed in this build* y quedan
  en el registro con la decisión; el resto de la entrega se ejecuta. Hasta el 24 retenían
  la entrega completa hasta que el residente los quitaba. Es la misma regla que usted fijó
  para un estudio no modelado.
- **Por qué**: el motor no tiene un efecto para ellos y no se inventa uno.
- **Impacto**: `anaphylaxis_antihistamine_only` se criba con los coadyuvantes que el
  motor ejecuta (corticoide, broncodilatador); un antihistamínico no ejecutado queda
  como texto reconocido y el cribado no lo ve como «dado». En el guion 18, la
  benzodiacepina no cambia nada en el paciente.
- **Opciones**: (a) mantener; (b) registrarlos como administrados, con hora y sin efecto
  fisiológico, para que el cribado y la rúbrica los vean como decisiones; (c) modelar
  efectos (por ejemplo, la sedación de una benzodiacepina).
- **Recomendación**: (b) para antihistamínicos y benzodiacepinas («sólo antihistamínico»
  es un error clásico que conviene ver en el registro); (a) para las recetas al alta.
- **¿Repetir?**: con (b) o (c), repetir el ensayo gratuito de los guiones 12 y 18 antes de
  la tanda; si la tanda ya se ejecutó, esos dos encuentros registrarían distinto.

### 4. «Lo dejo en observación N horas» es monitorización, no un destino (provisional)

- **Dónde**: ensayo; guiones 2 y 12. (El guion 10 hospitaliza «en sala para
  observación», que es un destino de sala.)
- **Hoy**: se registra como monitorización, una orden de apoyo sin fisiología propia; la
  duración no se modela y no cierra un destino. Hasta el 24 se perdía, o retenía la orden
  que la acompañaba.
- **Impacto**: en las altas de riesgo (sulfonilurea, opioide de larga acción, reacción
  bifásica) la observación prolongada es la alternativa segura; hoy queda registrada, pero
  el encuentro no tiene un destino «observación» y el cribado no la usa.
- **Opciones**: (a) mantener; (b) un destino «observación en urgencias» con duración, que
  cuente como alternativa segura en los eventos de alta; (c) monitorización por defecto,
  y destino cuando el residente la declara como destino.
- **Recomendación**: (c).
- **¿Repetir?**: sólo con (b): los guiones 2 y 12 cerrarían con otro destino.

### 5. Un líquido escrito sin verbo se ejecuta (provisional)

- **Dónde**: ensayo; guiones 5, 12 y 19.
- **Hoy**: «SF 1000 ml ev» se ejecuta como bolo, como se ejecuta un fármaco escrito
  igual. Hasta el 24 el líquido se retenía mientras el fármaco de al lado se ejecutaba.
  Una hipótesis o una negación no se ejecutan («Consideraría SF 1000 ml si baja la PA»,
  «Si baja la PA, SF 1000 ml», «No doy SF 1000 ml»: comprobado).
- **Por qué**: así se escribe una indicación en la hoja.
- **Opciones**: (a) mantener; (b) exigir un verbo sólo para los líquidos.
- **Recomendación**: (a).
- **¿Repetir?**: con (b), repetir el ensayo de los guiones 5, 12 y 19.

### 6. Tratamientos incorporados a la regla de las cuatro preguntas (provisional)

- **Dónde**: ensayo: «Doy atropina 1 mg ev» se ejecutaba sin expectativa mientras
  «Doy naloxona 0.1 mg ev» la pedía. En la tanda: guiones 2 (colación oral), 10 (infusión
  de glucosa), 16 y 19.
- **Hoy**: atropina, marcapaso transcutáneo, glucagón, calcio, tiamina, octreotide,
  trombólisis, ácido tranexámico, analgesia opioide, antipirético, carbohidrato oral,
  infusión de dextrosa, infusión de naloxona, bloqueo neuromuscular e infusión de sedación
  piden las cuatro categorías, igual que sus equivalentes. Quedan fuera a propósito: las
  órdenes de apoyo (vía venosa, monitorización, régimen cero, sondas), obtener información
  (prueba de esfuerzo, revisar un resultado), desconectar el ventilador y los
  procedimientos de trauma (punto 12).
- **Por qué**: la lista se escribió antes de que existieran esos tratamientos; su
  ausencia era un olvido, no una decisión. Una prueba impide que vuelva a pasar.
- **Opciones**: (a) mantener; (b) sacar los de menor riesgo (carbohidrato oral,
  antipirético).
- **Recomendación**: (a), con (b) a su criterio.
- **¿Repetir?**: no. Los guiones ya declaran las cuatro categorías en esas órdenes.

## B. Criterios de evaluación

### 7. Trombólisis sin anticoagulación en un TEP (encuentro 8 de la tanda de diez)

- **Dónde**: encuentro 8: un TEP trombolisado nunca fue anticoagulado y la propuesta no
  nombró `pe_no_anticoagulation`.
- **Hoy**: el veredicto por evento es obligatorio, así que ya no puede omitirse. El cribado
  deja ese evento en **lectura docente** cuando hubo trombólisis sin anticoagulación,
  porque la definición del caso acepta «pasar directamente a reperfusión con una razón
  declarada» y si hubo razón depende de lo que el residente escribió.
- **Opciones**: (a) mantener la alternativa y la lectura; (b) quitarla: una trombólisis
  no reemplaza la anticoagulación y el evento se cumple si no se anticoagula en la
  ventana; (c) mantenerla con una condición: anticoagular dentro de un plazo después de
  la trombólisis, que usted fija.
- **Recomendación**: (c). Es una pregunta clínica y el plazo es suyo.
- **¿Repetir?**: no para la tanda (ningún guion trombolisa). El encuentro 8 se puede
  volver a proponer con la regla nueva (una solicitud pagada).

### 8. Ventanas de dominio y «no evaluable»

- **Hoy**: cada caso declara una ventana por dominio (por ejemplo, D1 de 0 a 15 min). Si
  el encuentro cerró antes de que se abriera y no hubo acciones de ese dominio, el cribado
  sugiere **«no evaluable, no un cero»**. Si se abrió menos de 5 min antes del cierre y no
  hubo acciones, informa los minutos y no decide. La sugerencia no cambia ninguna propuesta
  ni ninguna decisión.
- **Opciones**: confirmar las ventanas declaradas (`case_assessment_bank.py`) y el umbral de
  5 minutos; o fijar otro umbral, o ninguno.
- **Recomendación**: confirmar, y revisar las ventanas de D4 y D5 en los casos más cortos.
- **¿Repetir?**: no. En los 20 ensayos se abrieron las cinco ventanas.

### 9. Cierre temprano por el residente

- **Dónde**: un encuentro de la tanda de diez cerró a los 13 minutos sin destino.
- **Hoy**: «Complete Encounter & Begin Review» se habilita con una sola decisión
  registrada y no pide destino ni advierte. El cierre temprano es un hecho que pertenece
  a los dominios cuya ventana estaba abierta; los demás quedan no evaluables.
- **Opciones**: (a) mantener; (b) advertir al cerrar sin destino, sin impedirlo; (c)
  impedir el cierre sin destino.
- **Recomendación**: (b). Conserva la decisión del residente y su evidencia, y evita un
  cierre accidental.
- **¿Repetir?**: no.

### 10. Autonomía «no determinada» y la meta del objetivo

- **Hoy**: una observación satisfactoria confirmada por el docente suma para la meta del
  objetivo con cualquier autonomía, incluida «no determinada»; la autonomía queda
  registrada al lado. La propuesta de IA nunca sugiere autonomía en una ejecución
  sintética ni sin declaración de asistencia.
- **Impacto**: si usted confirma objetivos de la tanda (sintética), sumarán en la cuenta
  de prueba con autonomía no determinada.
- **Opciones**: (a) mantener; (b) que sume sólo con una autonomía determinada; (c) que
  sume, mostrando aparte cuántas tienen autonomía no determinada.
- **Recomendación**: (c).
- **¿Repetir?**: no.

### 11. Qué dispersión entre lecturas del evaluador es aceptable

- **Hoy**: sin medir (no hay clave aquí). El encuentro es determinista; la diferencia 13/15
  frente a 9/15 viene del evaluador o de otra versión. No se declara estabilidad
  (`docs/REPRODUCIBILIDAD_PUNTAJE.md`).
- **Opciones**: fijar un umbral antes de medir (por ejemplo, ±1 en a lo sumo un dominio),
  o medir primero (5-10 solicitudes pagadas) y fijarlo después.
- **Recomendación**: medir primero y fijar el umbral con los datos.
- **¿Repetir?**: no.

## C. Capacidades que el simulador no tiene

### 12. Procedimientos de trauma a la cabecera, fuera de las cuatro preguntas (provisional)

- **Hoy**: la descompresión torácica, el control de hemorragia y la faja pélvica se
  ejecutan sin pedir las cuatro categorías.
- **Por qué**: son maniobras inmediatas; retener un torniquete para pedir una expectativa
  puede ser contraproducente. Pero son decisiones de manejo.
- **Opciones**: (a) exentos, como hoy; (b) ejecutar sin retener y registrar las
  categorías faltantes como anotación, igual que hoy se registra una prioridad no
  declarada; (c) exigir las cuatro, como cualquier tratamiento.
- **Recomendación**: (b).
- **¿Repetir?**: no. Ningún guion de la tanda es de trauma.

### 13. TC de cerebro y pruebas cruzadas

Detalle en `docs/CAPACIDADES_PENDIENTES.md`. Hoy la solicitud se registra como
«estudio solicitado; no modelado en esta versión del simulador», nunca como normal ni
como realizado, y el resto de la entrega se ejecuta.

- **Opciones**: (a) mantener; (b) un resultado autorizado en los casos que lo necesitan
  (por ejemplo, una TC de cerebro normal en la hipoglicemia con confusión persistente);
  (c) declarar en un escenario que el recurso no está disponible, con su razón.
- **Recomendación**: (b) para `hypoglycemia_54m_thiamine` y `pneumonia_83m`; (c) sólo
  cuando la restricción sea parte del caso.
- **¿Repetir?**: no para la tanda; el guion 17 (`pneumonia_83m`) no pide la TC.

## D. Funciones nuevas que necesitan su aprobación

### 14. Un docente elige el próximo caso de un residente

- **Por qué existe**: la tanda necesita 20 casos elegidos, jugados por la cuenta real del
  residente por el circuito real. Hasta el 24 sólo el currículo elegía el caso.
- **Cómo funciona**: en el panel docente, «Direct a resident's next encounter»: challenge,
  residente, caso del challenge y motivo obligatorio. Vale para un solo encuentro; una
  directiva nueva reemplaza a la que esperaba (las dos quedan en el historial); se puede
  cancelar. El encuentro registra quién lo dirigió, por qué y con qué versión del código.
  Sin directiva, el currículo elige como antes.
- **Opciones**: (a) aprobar como está; (b) limitarlo a administradores; (c) usarlo sólo
  para pruebas y retirarlo después.
- **Recomendación**: (a). Da al docente una forma explícita y trazable de asignar un caso.

### 15. El documento de rúbrica impreso desde la propuesta, antes de decidir

- **Por qué existe**: la tanda pide el documento D (rúbrica y spiderweb individual) de
  cada encuentro con la evaluación pendiente de su revisión.
- **Cómo funciona**: sólo en el panel docente, cuando hay propuesta y todavía no hay
  decisión. Encabezado «Sin decisión docente»; el spiderweb dice «Propuesta de IA (no es
  una decisión)»; cada puntaje se marca «· propuesta IA». No llega al residente ni al
  perfil acumulado, que sólo suma lo confirmado.
- **Opciones**: (a) aprobar; (b) quitarlo y entregar el documento D sólo tras su
  confirmación.
- **Recomendación**: (a).
