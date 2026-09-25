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
bastaba: los guiones son texto fijo y la simulación es determinista —salvo lo que
depende de la semilla que sortea cada lanzamiento (ver «Semilla» más abajo)—, así que
cada afirmación del «residente» tiene que ser lo que la pantalla le mostró en ese
momento.
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

**Semilla.** Cada lanzamiento sortea una semilla, y dos cosas dependen de ella: si el
paciente vomita con la morfina (dos de cada tres lanzamientos; `analgesia.py`) y el ruido
del trazado del ECG. Todo lo demás —acciones, tiempos, signos vitales, cribado— es igual
con cualquier semilla (comprobado con tres). El guion 7 afirmaba un vómito que un
encuentro pagado podía no mostrar; ahora dice sólo lo que vale en ambos casos. El ensayo
fija la semilla con `--seed N`, para comparar dos ensayos decisión por decisión.

**Después de sus decisiones del 2026-09-25** (`--seed 3000`, `3001` y `3002`): 20/20 con
revisión completa en las tres, sin retenciones no previstas y sin decisiones sin acción
leída. El cribado de cada evento definido y el minuto de cierre son los de la tabla de
§1, en los 20. Cinco guiones (6, 12, 16, 17 y 19) responden una pregunta menos: repetir
una dosis dentro de un plan ya explicado comparte ese plan (decisión 6); en el 18 el
control en policlínico cuenta como lo que se controla tras el alta (decisión 1); y los
guiones 2 y 12 cierran con la observación en urgencias como destino (decisión 4).

**Con las órdenes en inglés** (`tanda20_en.py`, `--language en`): los mismos 20 guiones,
paso por paso, con lo que escribe el residente en inglés («Give albuterol 5 mg neb», «NS
1000 mL IV bolus», «Admit her to intermediate care»…). Con la misma semilla, las 20
trayectorias son idénticas a las del español: mismas acciones, mismos minutos, mismos
signos vitales, mismo cierre. Llegar ahí encontró lo que el lector inglés no leía y el
español sí —una vía venosa («place a PIV», «start an IV»), una colación («oral snack»),
«put her on» una mascarilla, metamizol, «I prepare for intubation», un autoinyector con
guion, «send her home», la observación sin duración escrita («keep him under
observation»), la monitorización sin verbo— y un error de lectura: en «...RR 32 and more
effort» la descripción se tomaba como una orden de repetir algo y habría retenido la
entrega. También la respuesta «I will count the respiratory rate and look at the
saturation» no contaba como qué se va a controlar (en español sí). Todo corregido; una
prueba exige que cada orden y cada respuesta se lean igual en los dos idiomas
(`test_the_twenty_in_english.py`).

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
| Autorizar a esa cuenta docente para `residente_prueba_r3` | Desde la decisión 14 un docente sólo elige los casos de los residentes que un administrador le autorizó | En su cuenta de administrador: «Resident activity and recorded evidence» → «Who may choose a resident's cases» → docente de prueba, `residente_prueba_r3`, motivo → **Authorize**. Sin esto el ejecutor se detiene con ese aviso |
| La app de desarrollo en esta rama | Las correcciones, la dirección de casos y el documento de propuesta viven en `clinical-encounter-v0.13` | Que la app de desarrollo despliegue la rama en su último commit |
| `MRS_SYNTHETIC_ACCOUNTS=residente_prueba_r3` en los secretos de la app de desarrollo | Para que la cuenta pueda declarar la ejecución sintética | Agregarlo a los secretos de esa app |
| **Un lugar con red directa** (confirmado el 2026-09-25) | La página de Streamlit necesita un WebSocket (`/_stcore/stream`) y el proxy de las sesiones en la nube de Claude Code no admite WebSocket (su documentación, `/root/.ccr/README.md`: «WebSocket upgrades… not supported»). Ningún dominio permitido lo resuelve | Correr el ejecutor desde un computador o un Codespace de GitHub, que salen a internet sin ese proxy: ver «Correr la tanda con red directa» más abajo |
| Acceso de red a `share.streamlit.io` (visto el 2026-09-25) | Streamlit Community Cloud redirige toda visita a la app (303) a `share.streamlit.io/-/auth/app` antes de servirla; sin eso no hay sesión ni WebSocket (`/_stcore/stream` → 401) | Agregar `share.streamlit.io` a los dominios permitidos del entorno (o un nivel de acceso más amplio). Comprobar después que el proxy deja pasar el WebSocket de Streamlit: su documentación dice que no lo admite |
| Confianza de Chromium en la CA del proxy | El almacén NSS del contenedor estaba vacío (`ERR_CERT_AUTHORITY_INVALID`) | En cada sesión nueva: `apt-get install -y libnss3-tools` y `certutil -d sql:/root/.pki/nssdb -A -t "C,," -n ccr-agent-proxy -i /root/.ccr/agent-proxy-ca.crt` |
| Clave del proveedor en la app de desarrollo | Los tres documentos de IA se generan en el servidor | Ya debería estar; el ejecutor no la necesita localmente |

**Correr la tanda con red directa.** En un computador (por ejemplo, una sesión local de
Claude Code en la carpeta del repositorio) o en un Codespace de la rama:

```
git clone https://github.com/nfpineda-sketch/management-reasoning-simulator
cd management-reasoning-simulator && git checkout clinical-encounter-v0.13
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && python -m playwright install chromium
export MRS_BATCH_RESIDENT_PASSWORD=…  MRS_BATCH_STAFF_USER=…  MRS_BATCH_STAFF_PASSWORD=…
python tools_tanda20.py --preflight --base-url https://clinical-management-reasoning-dev.streamlit.app
python tools_tanda20.py --run 1 --base-url https://clinical-management-reasoning-dev.streamlit.app
```

El ejecutor usa el Chromium de Playwright cuando no existe el de la imagen en la nube.
Streamlit Community Cloud hace pasar cada visita por su propio inicio de sesión en
`share.streamlit.io`: una app pública lo atraviesa sola; si la app es privada, la
verificación previa lo dice, y para la tanda hay que dejarla visible para quien tenga
el enlace (el simulador sigue exigiendo sus propias cuentas).

**Las dos cuentas tienen que estar en la misma app, con la misma base.** Cada app
(pública, validación, desarrollo) usa su propia base en Neon y no comparten cuentas. Un
administrador ve todas las cuentas de su base en la barra lateral → «Account
administration» → «Manage an account». Si `residente_prueba_r3` no aparece ahí, esa
cuenta se creó en otra app: hay que crearla por invitación en la app donde está el
administrador (o usar la app donde ya existe, con un administrador de esa base). La
tabla «Resident activity and recorded evidence» lista encuentros, no cuentas: una cuenta
sin encuentros no aparece en ella.

**Verificación previa, gratis** (`python tools_tanda20.py --preflight --base-url <app>`):
inicia sesión con la cuenta docente de prueba y con `residente_prueba_r3` y sólo lee la
página —no inicia encuentros, no guarda directivas, no genera nada— para comprobar que
la cuenta docente es docente, que la app ejecuta esta rama (dirección de casos con
permiso acotado), que esa cuenta puede elegir los casos de `residente_prueba_r3` (misma
base y autorizada) y que el residente puede empezar un encuentro. Cada punto que falte
dice qué hacer. Probada contra una copia local de la app, con y sin autorización.

Con eso, la próxima sesión corre `--preflight`, luego `--run 1` y, si sale bien,
`--run 2,3,...`. El registro permite retomar.

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
Intento del 2026-09-25: la verificación previa (gratis) no llegó a la app por la red
(`share.streamlit.io` bloqueado, §4); no se inició ningún encuentro.

| # | Encuentro | Caso y trayectoria | Código | Duración clínica y estado | Documentos A-D | Revisión rúbrica / challenges | Visible residente / admin | Problemas | Consumo |
|---|---|---|---|---|---|---|---|---|---|

## 7. Qué necesita cada encuentro después de sus decisiones del 2026-09-25

Usted pidió no repetir la tanda automáticamente y distinguir tres casos. Se decide desde
los registros con `tools_reclassify.py`, no a mano:

- **Volver a ejecutar**: las mismas entradas, jugadas otra vez con el código actual,
  ejecutan otra cosa, en otro minuto, dejan al paciente en otro estado o cierran distinto.
- **Nuevo análisis**: la trayectoria es la misma, pero lo que el brief docente, la
  propuesta de rúbrica o el análisis del Management Trace leen **del registro guardado**
  cambió entre el código que lo produjo y el actual.
- **Sólo documentos**: lo demás. Se regeneran desde los datos guardados, sin costo.

Un cambio en las instrucciones comunes a todos (una versión nueva del prompt) se informa
aparte: hace más antiguo un análisis guardado, no lo hace erróneo sobre su registro.

**Los 20 guiones** (ensayo antes de las decisiones, código `2af52b0`, contra ensayo
después, misma semilla 3001): si la tanda se hubiera ejecutado antes de sus decisiones,

| Clase | Guiones | Por qué |
|---|---|---|
| Volver a ejecutar | 2 `hypoglycemia_28m`, 12 `anaphylaxis_29f` | «Lo dejo en observación N horas» pasó de monitorización a destino (decisión 4): cambia la acción ejecutada y el destino al cierre |
| Nuevo análisis | 7 `renal_colic_34m`, 18 `acs_66f_nonst` | El ondansetrón y el lorazepam ahora se leen como indicados por el residente, sin administración ni efecto modelados (decisión 3) |
| Nuevo análisis | 14 `pulmonary_embolism_61m`, 20 `pulmonary_embolism_33f` | La definición de `pe_no_anticoagulation` cambió: tras una trombólisis, un plan documentado o una razón explícita para diferir (decisión 7) |
| Sólo documentos | los otros 14 | Nada de lo que los análisis leen de su registro cambió; sus documentos se regeneran con los rótulos nuevos |

Instrucciones comunes que cambiaron para todos: la regla del cribado que recibe la
propuesta de rúbrica (prompt 1.1 → 1.2: indicaciones, explicación retrospectiva, cómo
terminó el encuentro, ventanas como apoyo). En seis guiones la página hace una pregunta
menos al residente (decisiones 1 y 6) y en el 13 la ventilación con bolsa-mascarilla se
registra como intervención urgente no retenida (decisión 12): no cambia la trayectoria y
no decide nada.

Como la tanda no se ejecutó (0 de 40), nada de esto obliga a gastar: la tanda se
ejecutará con el código actual. **Los nueve encuentros de la tanda de diez** viven en la
base de la app de desarrollo; donde esté esa base:
`python tools_reclassify.py --database "$MRS_DATABASE_URL" --account <cuenta> --since <revisión>`
los clasifica sin escribir nada (con `--reread`, nombra además las decisiones que el
lector actual ejecutaría distinto; es una relectura, no una repetición, y lo dice).

## 8. Tres ejemplos para Nate (preparados, no enviados)

Propuestos, para cuando existan los registros reales: **1 · asthma_24f** (buen manejo),
**9 · acs_48m_wellens** (error inicial con recuperación) y **17 · pneumonia_83m**
(desempeño deficiente), cada uno con sus límites (prueba sintética; rúbrica piloto sin
estudio de acuerdo entre evaluadores; reproducibilidad del evaluador no medida). No se
preparan con registros de ensayo: sólo existen en archivos locales.
