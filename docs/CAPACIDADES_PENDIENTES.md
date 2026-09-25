# Capacidades pendientes de implementación

Decisión docente del 2026-09-24. Dos estudios que el banco no tiene quedan
**pendientes como capacidades**; lo que cambió es cómo se trata su solicitud en la
interacción y en los informes. Este documento dice qué escenarios los necesitan y si
su ausencia impide completar una trayectoria de manejo razonable.

## Cómo se trata hoy una solicitud de un estudio no modelado

- Se reconoce la intención, se registra la solicitud con su hora y su estado:
  **«Estudio solicitado; no modelado en esta versión del simulador»**.
- El resto de la entrega se ejecuta. Hasta hoy, pedir «glicemia capilar y TAC de
  cerebro» rechazaba **toda** la entrega y la glicemia se perdía con la tomografía.
- No se inventa un resultado, no se informa como normal y no se registra como
  realizado. La solicitud no consume tiempo clínico propio.
- Queda en el Management Trace («no modelado en esta versión del simulador») y en la
  evidencia docente; el brief y la rúbrica reciben la instrucción de evaluar la
  pertinencia y la oportunidad de pedirlo, nunca la imposibilidad técnica de obtenerlo.
- «No disponible en el servicio» existe sólo como decisión del escenario: un caso que
  declare `resources_unavailable: {"head_ct": "<razón>"}` muestra «No disponible en este
  servicio: …» con su razón. Ningún caso actual lo declara.

## 1. Grupo y pruebas cruzadas

**Reconocido desde hoy** como `crossmatch`: «grupo y pruebas cruzadas», «pruebas
cruzadas», «grupo y Rh», «grupo sanguíneo», «tipificación», «pruebas de
compatibilidad», «reservar 2 unidades de sangre», «type and screen», «type and
crossmatch», «crossmatch». Antes, «order crossmatch for 2 units of blood» se ejecutaba
**como una transfusión de 2 unidades**; ahora es la solicitud del estudio. Sólo un verbo
que da la sangre («transfundir», «pasar», «dar») la convierte en transfusión. «Pido 2
unidades de glóbulos rojos», que puede ser cualquiera de las dos cosas, pregunta cuál.

| Escenario | Por qué lo necesita | ¿Su ausencia impide una trayectoria razonable? |
|---|---|---|
| `gi_bleed_57m`, `gi_bleed_72f` | Anticipar la transfusión es parte de la reanimación de una hemorragia digestiva | **No.** La transfusión (`blood`) se ejecuta sin estudio previo. Falta el tiempo del banco de sangre y la decisión entre sangre O negativo inmediata y sangre compatibilizada. |
| `trauma_limb_hemorrhage_27m`, `trauma_hemothorax_41m` | Activación de transfusión masiva, O negativo frente a compatibilizada | **No bloquea**, pero la decisión de liberar sangre de emergencia no se puede observar. |
| Cualquier caso con trombólisis o anticoagulación | Preparación ante sangrado | No. |

Lo que no se puede observar hoy: que el residente **anticipe** la necesidad de sangre (el
dominio 1 en su nivel 3 pide «contingencias»). Ahora la solicitud queda registrada, así
que la anticipación es visible aunque el estudio no devuelva nada.

## 2. Tomografía de cerebro

**Ya reconocida** como `head_ct`; desde hoy también «TC de cráneo», «TAC cerebral»,
«tomografía cerebral», «tomografía computada de encéfalo», «scanner cerebral», «CT of
the head». Ningún caso del banco la trae; sólo los casos generados pueden traerla.

| Escenario | Por qué lo necesita | ¿Su ausencia impide una trayectoria razonable? |
|---|---|---|
| `hypoglycemia_54m_thiamine` | Sólo si la conciencia no se recuperara tras corregir la glucosa. En este caso la glucosa que llega al paciente corrige la hipoglicemia y la conciencia, con o sin tiamina (decisión docente 8 del 2026-09-21); la TC no tiene indicación dentro del caso | **No.** Pedirla queda registrado. No se reintroduce una encefalopatía de Wernicke establecida para darle un motivo: el objetivo acordado es reconocer y corregir la hipoglicemia, con la tiamina como segundo objetivo. |
| `hypoglycemia_28m`, `hypoglycemia_76f` | Si la conciencia no se recupera, o tras una convulsión o una caída | No en las trayectorias actuales (la glucosa corrige el cuadro). |
| `pneumonia_83m` | El evento `pneumonia_unexamined_altered_state` cuenta «imagen de cerebro» como una forma de estudiar el compromiso de conciencia | **No.** Desde hoy pedirla cuenta como haber estudiado el compromiso (la verificación del registro lo trata así), y la imposibilidad de obtener el resultado no penaliza. |
| Trauma con TEC | No existe todavía un caso con trauma encefálico | — |

## Decisión docente 13 (2026-09-25): mantener la opción A por ahora

- **Se mantiene lo de hoy**: la solicitud se registra con su hora y su limitación
  («estudio solicitado; no modelado en esta versión del simulador») y el resto de la
  entrega se ejecuta. No se inventa un resultado ni se informa como normal.
- **No se agrega una TC normal por defecto** para cerrar este pendiente.
- **Incorporar un estudio exige**, caso por caso: su indicación dentro del caso, un
  resultado coherente con el caso, el tiempo en que está disponible y sus
  consecuencias en la evolución y en la evaluación.
- **Una restricción real de recursos** («no hay tomógrafo», «no hay banco de sangre»)
  sólo existe si el escenario la declara explícitamente (`resources_unavailable`);
  nunca se deduce de que el simulador no modele el estudio.
- **La hipoglicemia con déficit de tiamina** (`hypoglycemia_54m_thiamine`) no recupera
  una encefalopatía de Wernicke establecida para dar indicación a una TC: su objetivo
  acordado sigue siendo reconocer y corregir la hipoglicemia (decisión 8 del
  2026-09-21).

Pendiente, sin fecha: definir, para los casos que lo necesiten, indicación, resultado,
disponibilidad y consecuencias de la TC de cerebro y de las pruebas cruzadas antes de
incorporarlas.
