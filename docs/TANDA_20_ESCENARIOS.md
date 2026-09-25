# Tanda sintética de 20 escenarios · preparación y estado

Especificación docente del 2026-09-24. **Estado: preparada y ensayada; no ejecutada.**
Ningún encuentro pagado se ha consumido en esta tanda (0 de 40). Lo que falta para
ejecutarla son accesos que este entorno no tiene; están en «Bloqueos» con los pasos
exactos para destrabarlos.

Esta tanda es una **prueba sintética ejecutada por un agente en una cuenta de prueba**.
Cada encuentro queda declarado como tal en el registro («Prueba sintética: ejecución
automatizada sin asistencia externa») y no debe leerse como desempeño de una persona.

## 1. Los 20 escenarios

Todos son casos **establecidos** del banco (ninguna variante nueva, ninguna regla
fisiológica inventada), elegidos por madurez (pruebas y guiones previos) y diversidad:
11 familias, 20 presentaciones distintas. Cada caso declara ventanas para los cinco
dominios y sus eventos críticos (`case_assessment_bank`).

| # | Caso | Trayectoria (intención, no nota) | Challenge | Eventos definidos | Cribado del registro del ensayo | Cierre (min) |
|---|---|---|---|---|---|---|
| 1 | asthma_24f | bueno | R3-01 | asthma_no_bronchodilator | contradicho | 106 |
| 2 | hypoglycemia_28m | bueno | R1-06 | hypo_no_glucose | contradicho | 44 |
| 3 | acs_54m_inferior | bueno | R2-02 | acs_no_antiplatelet, acs_provocation_test | ambos contradichos | 38 |
| 4 | gi_bleed_57m | bueno | R2-05 | gi_no_resuscitation | contradicho | 89 |
| 5 | pneumonia_46f | largo | R1-05 | pneumonia_no_antibiotic | contradicho (antibiótico a los 24 min, ventana 0-60) | 94 |
| 6 | opioid_35m | largo | R1-06 | opioid_no_ventilatory_support | contradicho | 50 |
| 7 | renal_colic_34m | largo | R2-05 | colic_missed_infection | contradicho | 149 |
| 8 | pulmonary_edema_58m | largo | R1-05 | edema_no_ventilatory_support, edema_volume_loading | ambos contradichos | 74 |
| 9 | acs_48m_wellens | recuperación | R2-02 | acs_no_antiplatelet, acs_provocation_test | lectura docente / contradicho | 78 |
| 10 | hypoglycemia_76f | recuperación | R1-06 | hypo_no_glucose, hypo_unsafe_discharge | ambos contradichos | 74 |
| 11 | asthma_49m | recuperación | R3-01 | asthma_no_bronchodilator, asthma_no_ventilatory_support | ambos contradichos | 76 |
| 12 | anaphylaxis_29f | recuperación | R1-06 | anaphylaxis_no_epinephrine, anaphylaxis_antihistamine_only, anaphylaxis_unsafe_discharge | todos contradichos | 67 |
| 13 | opioid_67f | equivocado | R1-06 | opioid_no_ventilatory_support, opioid_unsafe_discharge | contradicho / **lectura** (alta ocurrió) | 27 |
| 14 | pulmonary_embolism_61m | equivocado | R2-02 | pe_no_anticoagulation | **cumplido** | 63 |
| 15 | gi_bleed_72f | equivocado | R2-05 | gi_no_resuscitation | **cumplido** | 53 |
| 16 | bradycardia_ccb_68m | equivocado | R2-04 | bradycardia_no_support, bradycardia_cause_unexamined | contradicho / **lectura** | 31 |
| 17 | pneumonia_83m | deficiente | R1-05 | pneumonia_no_antibiotic, pneumonia_unexamined_altered_state | **ambos cumplidos** | 61 |
| 18 | acs_66f_nonst | deficiente | R2-02 | acs_no_antiplatelet, acs_provocation_test | lectura / **cumplido** | 41 |
| 19 | anaphylaxis_63m_betablocked | alternativa | R1-06 | anaphylaxis_no_epinephrine, anaphylaxis_antihistamine_only, anaphylaxis_unexamined_refractory | contradichos / excluido (el tercero) | 37 |
| 20 | pulmonary_embolism_33f | alternativa | R2-02 | pe_no_anticoagulation, pe_unindicated_thrombolysis | ambos contradichos | 75 |

«Contradicho»: el registro muestra que el evento no ocurrió. «Cumplido»: el registro reúne
lo que define el evento. «Lectura»: el registro no decide solo y queda para su lectura
docente. «Excluido»: aplica una exclusión declarada del evento. Es el cribado
determinista que acompaña a la propuesta; no es una decisión.

Distribución pedida: 4 bueno · 4 largo · 4 recuperación · 4 equivocado · 2 deficiente ·
2 alternativa. En los 20 ensayos el encuentro siguió abierto después de que se abrieran
las cinco ventanas de dominio: los cinco dominios tuvieron oportunidad real.

Los guiones (`tanda20.py`) están escritos como escribe un residente: abreviaturas
(«nbz», «vvp», «SF»), sin tildes, órdenes agrupadas, respuestas a la pregunta de
seguimiento en texto libre y en el formulario de cuatro preguntas, un resultado
pendiente y una sesión guardada y retomada (escenario 20). Una prueba de esfuerzo en
el Wellens fibrila al paciente por decisión docente, así que el error recuperable de
ese guion es otro (omitir la antiagregación mientras espera una troponina).

## 2. Ensayo offline por la página real (gratis, no es evidencia de la tanda)

`python tools_tanda20.py --rehearse all` juega cada guion por `app.py` (Streamlit en
proceso, base temporal, sin clave, caso fijado) con una copia de ensayo de la cuenta.
Sirvió para encontrar lo que habría detenido a un residente antes de gastar un
encuentro. Corregido (commit `1b48b09`): «nbz», «vvp» y «SF 1000 ml ev» sin verbo no se
leían; «mascarilla de no recirculación» se ejecutaba como mascarilla simple; «Los gases
muestran…» y «Toma glibenclamida» se leían como órdenes de estudio; «Lo traslado a
hemodinamia» pedía una cama; «Lo dejo en observación» se perdía; antihistamínicos,
benzodiacepinas y recetas al alta retenían toda la entrega; tratamientos agregados
después de la regla de las cuatro preguntas (atropina, glucagón, trombolisis…) se
ejecutaban sin expectativa; «voy a mirar la saturación» no contaba como qué se va a
controlar y se volvía a preguntar.

**Contrastado con la pantalla (2026-09-25).** Que la página aceptara cada guion no
bastaba: los guiones son texto fijo y la simulación es determinista, así que cada
afirmación del «residente» tiene que ser lo que la pantalla le mostró en ese momento.
Nueve no lo eran: el asma «bien manejada» decía «respondió bien, satura 95 %» con FR 32
y esfuerzo marcado (y había dado un solo broncodilatador en 99 minutos); el cólico decía
«el dolor cedió» con dolor intenso; otros citaban cifras que no eran las mostradas, un
hipoglicemiante que no era el de la historia, somnolencia en un paciente alerta o
estabilidad con PA 96/53. Se corrigieron los guiones 1, 5, 7, 8, 10, 11, 12, 16 y 20
respondiendo a lo que la pantalla muestra, sin cambiar la trayectoria que cada uno
representa (el guion 1 repite el salbutamol y pasa a nebulización continua al recaer; el
7 escalona la analgesia antes del alta; el 10 incorpora el error inicial que declaraba,
planear el alta antes de preguntar por los medicamentos; el 20 espera la troponina para
decidir el destino). Los guiones «equivocado» y «deficiente» conservan sus errores.

Ese contraste encontró además defectos del lector que el ensayo no veía, todos
corregidos con pruebas: el alta del guion 7 («lo doy de alta con analgesia, control
urológico y regresar si tiene fiebre…») se perdía entera y en silencio; «Repito
salbutamol 5 mg nbz» se rechazaba («no matching administered treatment»); en «le doy
colación oral y la doy de alta si la tolera» la colación quedaba retenida con el alta;
«Preparo intubación» desaparecía; un alta retenida se leía «admission to home». El ensayo
ahora nombra toda decisión aceptada que no hizo nada («Decisiones sin acción leída»).

Resultado final: **20/20 con revisión completa**, sin retenciones no previstas por el
guion, sin decisiones sin acción leída, con la declaración de prueba sintética guardada.

## 3. El recorrido real y su ejecutor

`tanda20_runner.py`, llamado con `python tools_tanda20.py --run N --base-url URL`, hace
por el navegador lo que haría una persona:

1. **Docente de prueba**: dirige el próximo encuentro de `residente_prueba_r3` al caso
   del escenario, con su motivo («Tanda sintética 2026-09-24 · escenario N»).
2. **`residente_prueba_r3`**: inicia, pregunta, examina, ordena, responde las preguntas
   de seguimiento, cierra, reflexiona, compara, planifica, declara la prueba sintética;
   descarga el Management Trace analizado (documento A, pagado).
3. **Docente de prueba**: abre ese encuentro, genera **una vez** el brief docente y la
   propuesta de rúbrica (pagados) y descarga el brief completo (B), el compacto (C) y la
   rúbrica con su spiderweb (D). Todas las evaluaciones quedan **pendientes**.
4. **Registro**: una línea por intento en `local-data/tanda20/batch/ledger.jsonl`;
   rechaza un encuentro pagado número 41.

Nunca escribe en la base, nunca confirma una evaluación y se detiene con un hallazgo
cuando la página no lo deja seguir (incluida una pregunta de seguimiento que el guion no
responde: nunca la contesta con palabras inventadas).

**Verificado aquí** con `python tools_tanda20.py --local-check N` (Chromium real contra una
copia local offline de la app con cuentas de prueba): escenarios 7, 13 y 20 completos,
guardados como completados, en el caso dirigido, con la declaración sintética. **No
verificado aquí**: los pasos pagados (sin clave); sus botones y rótulos de descarga se
comprobaron en la página local.

## 4. Bloqueos y cómo destrabarlos

| Falta | Por qué hace falta | Qué hacer |
|---|---|---|
| Acceso de red a la app de desarrollo | El ejecutor usa la app real por el navegador | Agregar el host de la app de desarrollo a la política de red del entorno de la próxima sesión (hoy el proxy responde 403) |
| Contraseña de `residente_prueba_r3` | Iniciar sesión como la cuenta de prueba | Variable de entorno `MRS_BATCH_RESIDENT_PASSWORD` en el entorno de la sesión (nunca en el chat) |
| Una cuenta **docente de prueba** | Dirigir los casos y generar los borradores de IA sin atribuirlos a un docente real | Crearla desde su cuenta de administrador (invitación de rol faculty) y pasarla como `MRS_BATCH_STAFF_USER` / `MRS_BATCH_STAFF_PASSWORD` |
| La app de desarrollo en esta rama | Las correcciones, la dirección de casos y el documento de propuesta viven en `clinical-encounter-v0.13` | Que la app de desarrollo despliegue la rama en su último commit |
| `MRS_SYNTHETIC_ACCOUNTS=residente_prueba_r3` en los secretos de la app de desarrollo | Para que la cuenta pueda declarar la ejecución sintética | Agregarlo a los secretos de esa app |
| Clave del proveedor en la app de desarrollo | Los tres documentos de IA se generan en el servidor | Ya debería estar; el ejecutor no la necesita localmente |

Con eso, la próxima sesión corre `python tools_tanda20.py --local-check 1` (gratis),
luego `--run 1` y, si sale bien, `--run 2,3,...`. El registro permite retomar.

**Consumo previsto**: 20 encuentros si todo sale a la primera; el resto del límite de 40
queda para reintentos y reemplazos. Cada encuentro dirigido usa un caso del banco (sin
generación de caso); el costo pagado es la imagen del paciente, el análisis del
Management Trace, el brief docente y la propuesta de rúbrica.

## 5. Revisar y validar (su cuenta de administrador)

1. Panel docente → «Resident activity and recorded evidence»: la columna «Awaiting your
   review» dice qué falta en cada encuentro (rúbrica, objetivos, borradores).
2. Elegir el encuentro en «Encounter record». Arriba, la rúbrica con la propuesta y las
   marcas «Revisar antes de decidir»; debajo, el contexto de asistencia (verá la
   declaración de prueba sintética), el brief y sus PDF.
3. Rúbrica: decidir cada dominio (empieza en «no evaluable»), confirmar o descartar cada
   evento, **Confirmar**. Challenges: cargar la sugerencia, ajustar, **Registrar**. Son
   independientes.
4. Lo confirmado entra en el spiderweb acumulado del residente (sólo lo confirmado, una
   versión de rúbrica, con resultados individuales y fechas) y en su historial de
   challenges.

## 6. Índice de intentos

Se completa con el registro del ejecutor. Hoy está vacío: **0 intentos pagados**.

| # | Encuentro | Caso y trayectoria | Código | Duración clínica y estado | Documentos A-D | Revisión rúbrica / challenges | Visible residente / admin | Problemas | Consumo |
|---|---|---|---|---|---|---|---|---|---|

## 7. Tres ejemplos para Nate (preparados, no enviados)

Propuestos, para cuando existan los registros reales: **1 · asthma_24f** (buen manejo),
**9 · acs_48m_wellens** (error inicial con recuperación) y **17 · pneumonia_83m**
(desempeño deficiente), cada uno con sus límites (prueba sintética; rúbrica piloto sin
estudio de acuerdo entre evaluadores; reproducibilidad del evaluador no medida). No se
preparan con registros de ensayo: sólo existen en archivos locales.
