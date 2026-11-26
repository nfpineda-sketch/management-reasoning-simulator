# Fase 3 · Protocolo del piloto controlado de desarrollo de la traza de manejo de GI

**P3-555 · decisiones FD-FINALPILOT-01 a FD-FINALPILOT-10 · 2026-11-23.**

Este documento dice **cómo** correr el piloto. **No lo inicia.** Iniciarlo es una decisión docente.

Rige sólo si el punto de control `GI_FINAL_PILOT_CONVERGENCE_CHECKPOINT_V1` (`docs/revision/PHASE3_GI_FINAL_PILOT_CHECKPOINT.json`) tiene el veredicto **A**. El detalle técnico está en `docs/PHASE3_GI_FINAL_PILOT_CONVERGENCE.md`.

## 1. Qué es y qué no es

| Es | No es |
|---|---|
| un piloto **formativo** de desarrollo, pequeño y supervisado | validación clínica, aprobación de producción ni despliegue general |
| un caso sintético: `gi_bleed_57m` (hemorragia digestiva alta, varón de 57 años) | `gi_bleed_72f` (diferido) ni otros casos |
| presión de la autoridad viva de desarrollo, con norepinefrina manual en mcg/min | autoridad de consciencia, terminal ni en familias limitadas por la bomba |
| una traza de manejo para la conversación con el docente | un puntaje, una nota, un ranking ni una evaluación sumativa |

## 2. Diseño

| Elemento | Valor |
|---|---|
| Residentes | **2 a 4**, voluntarios, con cuenta individual |
| Docentes | **1** supervisor presente durante todo el encuentro |
| Caso | `gi_bleed_57m`, **un encuentro por residente** |
| Duración | hasta **120 minutos simulados** (el horizonte del piloto); en tiempo real, unos 20 a 40 minutos por encuentro, más 15 a 20 de conversación |
| Entorno | el entorno de **desarrollo**, un **solo proceso**, en una máquina controlada por el equipo; nunca el despliegue público ni el del primer piloto |
| Puntuación | ninguna: el encuentro no crea intento de cuenta ni llega a progreso ni evaluación |
| Después | conversación estructurada con el docente (§8) |

## 3. Lanzamiento (operador)

**Antes del día del piloto.**
1. Usar el árbol publicado y certificado de `phase-3-runtime-integration` sin cambios locales: `git status` limpio y `git rev-parse HEAD` igual al commit que nombra el punto de control.
2. Preparar la base de cuentas (PostgreSQL, o SQLite local sólo en la máquina de desarrollo) y crear, desde la página de administración, una invitación de **residente** por participante y una de **docente**. Nunca usar nombres de pacientes reales ni datos personales en el caso.
3. Elegir dos directorios **fuera del repositorio** y vacíos: uno para el registro del piloto y otro para el almacén de la autoridad.

**Variables de entorno** (todas obligatorias; si falta una o sobra algo no permitido, la página se niega y el docente ve la lista de problemas):

```bash
export MRS_PHASE3_GI_PILOT=on
export MRS_PHASE3_GI_PILOT_STORE=/ruta/fuera/del/repo/gi_pilot_store
export MRS_PHASE3_AUTHORITY=limited_common_authority
export MRS_PHASE3_AUTHORITY_SNAPSHOT=GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1
export MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT=COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1
export MRS_PHASE3_AUTHORITY_ENVIRONMENT=development
export MRS_PHASE3_SHADOW=shadow_compare
export MRS_PHASE3_AUTHORITY_STORE=/ruta/fuera/del/repo/authority_store
export MRS_OFFLINE_CASES=1
export MRS_IMAGE_BANK=off
# cuentas individuales (por Secrets de Streamlit o por entorno): MRS_AUTH_MODE=accounts, MRS_DATABASE_URL=...
```

**Lo que no debe estar definido:** ninguna clave de IA (`OPENAI_API_KEY` u otra), `MRS_PILOT_RESIDENTS`, `MRS_PILOT`, `MRS_FACULTY_DEVELOPMENT_REVIEW`, `MRS_IMAGE_REQUIRE_REVIEW`, ni `MRS_PHASE3_HISTORICAL_RECONSTRUCTION`.

**Arranque:** un solo proceso.

```bash
python3 -m streamlit run app.py --server.headless true --server.port 8501
```

No usar réplicas, varios procesos ni recarga automática: el no-op de aclaración se prueba dentro del turno de un proceso (contrato de un solo proceso).

**Comprobación previa (5 minutos, con una cuenta de prueba sintética):**
1. Entrar como docente: la página dice «GI development pilot · faculty supervision» y no muestra problemas de configuración.
2. Entrar como residente de prueba: se ve el inicio del piloto con el aviso y el botón «Begin the development pilot encounter». Al empezar, la sala muestra el monitor y, debajo, la fotografía del paciente con el rótulo «ED / Bed 03 · Patient on arrival» (FD-P3-311). Si en su lugar dice «Current patient image unavailable», el árbol no es el publicado: detener y revisar.
3. Hacer un encuentro corto: «Give 1 litre of normal saline over 15 minutes. Reassess in 15 minutes.», luego «Give normal saline.» (debe pedir el volumen y el encuentro sigue), luego «Complete Encounter» → «Finish now».
4. Como docente: elegir ese encuentro, «Review the replay» debe decir que todas las comprobaciones coinciden; marcarlo inutilizable con el motivo «prueba del operador».

**Durante el piloto:** no cambiar variables, no reiniciar el proceso salvo emergencia (un reinicio interrumpe los encuentros abiertos, que no se reanudan). **Después:** detener el proceso y conservar los dos directorios de registro fuera del repositorio. **No** subir registros, respuestas ni nombres al repositorio.

## 4. Lo que se dice a los residentes (instrucciones)

Lectura en voz alta antes de empezar, más el texto del propio lanzador:

> Esto es un piloto de desarrollo con un paciente sintético con una hemorragia digestiva alta. No es una evaluación: nada cuenta para ninguna nota. Maneja al paciente como lo harías normalmente: escribe tus órdenes y, cuando te lo pida, tu razonamiento.
>
> - Escribe cada orden completa: fármaco o líquido, dosis o volumen, duración o tasa con su unidad, y cuándo reevaluar. Por ejemplo: «Give 1 litre of normal saline over 15 minutes. Reassess in 15 minutes.»
> - Si una orden está incompleta, el simulador la retiene y te pregunta qué falta; no se hace nada y el encuentro sigue. Cuando te pida una tasa, **vuelve a escribir la orden completa** (por ejemplo: «Increase norepinephrine to 12 mcg/min.»), no sólo el número.
> - La norepinefrina se ordena con una tasa explícita en **mcg/min** (iniciar, cambiar, suspender, reiniciar). Un objetivo de presión, un cambio relativo o una tasa sin unidad se retienen y no se da nada.
> - El modelo de desarrollo **no** representa otros medicamentos u otros vasopresores, la norepinefrina en mg/min o mcg/kg/min, la sonda nasogástrica, la sonda vesical ni el monitoreo continuo: si los ordenas, el encuentro de desarrollo termina antes. No es un juicio sobre tu manejo.
> - Pedir el control definitivo del sangrado (gastroenterología, endoscopia, radiología intervencionista, cirugía) termina el encuentro en la **frontera del modelo de desarrollo**. No significa que el sangrado se detuvo ni que el paciente está estable.
> - La presión viene del modelo de desarrollo que revisaron los docentes. Los otros signos vienen del modelo anterior; tras la norepinefrina, el estado mental no se muestra.
> - La fotografía muestra al paciente **a su llegada** y no cambia durante el encuentro. Lo actual está en el monitor, en la línea de apariencia y en el examen.
> - No escribas datos personales. Puedes terminar cuando quieras con «Complete Encounter».
> - Al final verás tu traza de manejo para conversarla con el docente.

## 5. Lo que hace el docente (instrucciones)

**Durante el encuentro** (página «GI development pilot · faculty supervision», «Refresh» para actualizar):
- **Observar:** elegir el encuentro en «Encounter» y abrir «Observe: turns as recorded».
- **Detener:** «Stop this encounter» (se aplica en la siguiente acción o recarga del residente). Usarlo ante cualquier criterio de §7.
- **Señalar:** «Flag an output as unsafe or ambiguous», con dónde (paso, minuto o pantalla) y qué; sin datos reales.
- **No intervenir** en el manejo ni sugerir órdenes durante el encuentro, salvo que el residente quede bloqueado por la interfaz (por ejemplo, que no sepa cómo completar una orden retenida): entonces sólo se le recuerda la regla del §4.

**Después del encuentro:**
- «Inspect the trace» y «Review the replay» (debe decir que todas las comprobaciones coinciden).
- «Mark unusable», con el motivo, si el encuentro no sirve para la conversación (falla técnica, interrupción, confusión de la interfaz).
- Conducir la conversación del §8.

## 6. Datos que se recogen y lo que no se puntúa

**Se recoge** (sólo en los directorios fuera del repositorio):
- bitácoras seudónimas y encadenadas por hash del participante y del docente;
- el artefacto de la autoridad y la traza de manejo de cada encuentro;
- las señales, detenciones y marcas de inutilizable del docente;
- las notas de la conversación posterior, si el docente las toma, sin nombres.

**No se puntúa nada:** ni la traza, ni sus categorías (razonable, temporizador, incompleto, claramente no beneficioso), ni el tiempo, ni las órdenes. El encuentro no crea intento de cuenta ni llega a progreso, evaluación, radar o ranking. Las categorías son interpretaciones docentes para conversar, nunca puntajes (FD-FINALPILOT-07).

## 7. Criterios para abortar un encuentro (el docente lo detiene)

- El residente se angustia o pide parar.
- La pantalla muestra algo engañoso o inseguro (por ejemplo, un estado mental tras la norepinefrina, un identificador interno, una mejoría atribuida sin base): **detener y señalar**.
- El encuentro queda atascado por la interfaz más de 5 minutos reales pese a recordar la regla del §4.
- Aparece un error técnico en pantalla.

Las salidas que el propio piloto produce (frontera, detención de la autoridad por una orden no representada, registro no disponible, configuración no disponible) **no** son un aborto: el encuentro termina con su mensaje y se conversa igual.

## 8. Conversación posterior (estructurada, 15 a 20 minutos)

1. **Qué pensaste al llegar:** el estado inicial y la prioridad que te pusiste.
2. **Recorrido por la traza:** en cada paso, estado → prioridad → acción → efecto esperado → respuesta observada → reevaluación. El docente señala dónde el razonamiento expresado y la acción coinciden o difieren, sin inventar razonamiento que el residente no escribió.
3. **La frontera:** qué significa en este modelo de desarrollo y qué harías en la vida real.
4. **La interfaz:** qué órdenes te costó escribir, qué aclaraciones fueron claras o confusas.
5. **Cierre formativo:** una cosa que harías igual y una que cambiarías. Sin nota.

## 9. Criterios de éxito del piloto

- Cada residente completa un encuentro hasta una salida declarada sin intervención técnica del operador.
- Toda orden incompleta recibe su aclaración y el encuentro sigue.
- Ninguna solicitud de control definitivo llega a una hemostasia.
- Ningún estado mental aparece en pantalla tras la norepinefrina.
- Cada encuentro tiene una traza que verifica y una revisión de la repetición que coincide.
- El docente puede conversar la traza y ningún residente la vive como una calificación.

## 10. Criterios para detener el piloto completo

- Cualquier salida engañosa o insegura reproducible (estado mental, identificadores internos, hemostasia, dosis inventada).
- Una revisión de la repetición que no coincide en un encuentro auténtico.
- Una pérdida o corrupción de registros.
- Dos o más encuentros inutilizables por la interfaz.
- Cualquier dato personal o real escrito en el sistema.
- Que el docente lo decida.

Al detenerlo: no se corrige nada en caliente. Se preservan los registros fuera del repositorio, se documenta el hallazgo y se decide en un ciclo aparte.
