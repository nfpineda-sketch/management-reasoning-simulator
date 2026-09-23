"""What thirteen real proposals said, written up from the proposals themselves.

Reads the raw runs under ``local-data/paid_runs`` (which is not in the
repository, because a run is data and not code) and writes
``docs/RUBRICA_PILOTO_CORRIDAS.md``. The prose lives here so that regenerating
the document cannot silently drop an appendix somebody added to it.

No paid call is made by this tool. The runs it reads were made by
``tools_rubric_runs.py --propose``, one request each.
"""
import json
from collections import Counter
from pathlib import Path

import case_assessment
import rubric

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "local-data" / "paid_runs"
PILOT = RUNS / "rubric_pilot"
EARLIER = (("acs_48m_wellens", RUNS / "2026-09-23_rubric_proposal_wellens.json"),
           ("pulmonary_embolism_33f", RUNS / "2026-09-23_rubric_proposal_embolism.json"))

# What each scripted encounter was written to do, so that "the model proposed
# the event" can be read against something other than the model's own output.
INTENT = {
    "asthma_24f": ("Manejo competente", None),
    "asthma_49m": ("Broncodilata y no soporta la ventilación", "asthma_no_ventilatory_support"),
    "gi_bleed_57m": ("Reanimación competente", None),
    "gi_bleed_72f": ("Estudia y nunca reanima", "gi_no_resuscitation"),
    "hypoglycemia_54m_thiamine": ("Glucosa sin tiamina", "hypo_no_thiamine"),
    "hypoglycemia_76f": ("Alta tras hipoglicemia por sulfonilurea", "hypo_unsafe_discharge"),
    "opioid_35m": ("Manejo competente", None),
    "pneumonia_83m": ("Trata la neumonía, no estudia el compromiso de conciencia",
                      "pneumonia_unexamined_altered_state"),
    "pulmonary_edema_58m": ("Soporta bien y luego carga volumen", "edema_volume_loading"),
    "acs_52m_de_winter": ("Encuentro truncado a los 15 minutos", None),
    "pulmonary_embolism_61m": ("Reconoce y nunca anticoagula", "pe_no_anticoagulation"),
    "acs_48m_wellens": ("Corrida 1 · entrega retenida por el intérprete", None),
    "pulmonary_embolism_33f": ("Corrida 2 · trombólisis sin hipotensión sostenida",
                               "pe_unindicated_thrombolysis"),
}


# Run after the rule changed, to verify it, and therefore not part of the
# thirteen that the first-pass table and the distribution describe. They are
# read in section 6 instead, where the comparison is the point.
VERIFICATIONS = ("opioid_67f",)

# The baseline of the one case that was both. Declared here because the
# verification of 2026-09-23 wrote over its own raw file before --propose
# learned not to; the numbers below are the ones that run printed, and its
# reasoning is quoted in section 6 from the same output. Every other row in the
# table is read from the raw file it came from.
SUPERSEDED = {
    "hypoglycemia_76f": {"scores": {"D1": 2, "D2": 2, "D3": 2, "D4": 2, "D5": 1},
                         "events": [], "seconds": 74.1},
}


def load():
    runs = []
    for path in sorted(PILOT.glob("*.json")):
        if path.name.endswith(".record.json") or path.stem in VERIFICATIONS:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        runs.append((payload["report"], payload.get("usage", {})))
    for _, path in EARLIER:
        if path.exists():
            runs.append((json.loads(path.read_text(encoding="utf-8")), {}))
    return runs


def _scores(report):
    return {row["domain_id"]: row["score"] for row in report["proposal"]["domains"]}


def _cell(value):
    return "n/e" if value == rubric.NOT_ASSESSABLE else str(value)


def main():
    runs = load()
    if not runs:
        raise SystemExit(f"No hay corridas en {PILOT}. Córrelas con tools_rubric_runs.py.")
    lines = [
        "# Rúbrica piloto: trece encuentros evaluados por un modelo real", "",
        f"Generado por `tools_rubric_findings.py` · rúbrica {rubric.VERSION} · "
        f"{len(runs)} encuentros.", "",
        "> **Once corridas nuevas**, una llamada pagada cada una, más las dos del 2026-09-23 "
        "que ya estaban documentadas. Ninguna se repitió y ninguna se reintentó. Cada encuentro "
        "se jugó con `MRS_OFFLINE_CASES=1`, es decir con la clave retenida en todos los "
        "resolvedores, de modo que jugar no costó nada y el único gasto fue la propuesta.", "",
        "## 1 · De dónde salen estos encuentros", "",
        "No están escritos a mano. Cada uno se jugó a través del intérprete y del motor de "
        "producción con `tools_rubric_runs.py`, así que el registro que ve el modelo es el que "
        "el motor mismo escribió: sus consecuencias, su reloj y su interpretación de cada orden. "
        "Lo único escrito por mí son las órdenes del residente.", "",
        "Cada guión se escribió **para provocar algo concreto**, y esa intención está en el "
        "código antes de ver la respuesta del modelo. Sin eso, \"el modelo propuso el evento\" "
        "no se puede leer contra nada.", "",
        "## 2 · Los trece encuentros", "",
        "> La fila de `hypoglycemia_76f` es la **primera** corrida. Ese caso se volvió a correr "
        "después, para verificar tu decisión; el antes y el después están en §6.", "",
        "| Caso | Qué se quiso provocar | D1 | D2 | D3 | D4 | D5 | Evento esperado | Evento propuesto |",
        "|---|---|:-:|:-:|:-:|:-:|:-:|---|---|",
    ]
    hits = misses = false_positives = 0
    for report, _ in runs:
        case_id = report["case_id"]
        baseline = SUPERSEDED.get(case_id)
        scores = baseline["scores"] if baseline else _scores(report)
        expected = INTENT.get(case_id, ("", None))
        proposed = (list(baseline["events"]) if baseline
                    else [row["event_id"] for row in report["proposal"]["critical_events"]])
        if expected[1]:
            if expected[1] in proposed:
                hits += 1
            else:
                misses += 1
        false_positives += len([e for e in proposed if e != expected[1]])
        lines.append(
            f"| `{case_id}` | {expected[0]} | " +
            " | ".join(_cell(scores[d]) for d in rubric.DOMAIN_IDS) +
            f" | {('`' + expected[1] + '`') if expected[1] else '—'} | "
            f"{', '.join('`' + e + '`' for e in proposed) or '—'} |")

    distribution = Counter()
    per_domain = {domain: Counter() for domain in rubric.DOMAIN_IDS}
    for report, _ in runs:
        baseline = SUPERSEDED.get(report["case_id"])
        for domain, value in (baseline["scores"] if baseline else _scores(report)).items():
            distribution[value] += 1
            per_domain[domain][value] += 1
    total = sum(distribution.values())
    seconds = sum(usage.get("seconds", 0) for _, usage in runs)
    requests = sum(usage.get("requests", 0) for _, usage in runs)

    lines += [
        "", f"**{hits} de {hits + misses} eventos esperados fueron propuestos. "
        f"{false_positives} eventos propuestos sin que el guión los buscara. "
        "Ningún evento inventado: el esquema sólo admite los definidos para el caso.**", "",
        "## 3 · Cómo se distribuyeron los puntajes", "",
        f"{total} puntajes de dominio en {len(runs)} encuentros.", "",
        "| | 0 | 1 | 2 | 3 | No evaluable | Media |", "|---|:-:|:-:|:-:|:-:|:-:|:-:|",
    ]
    for domain in rubric.DOMAIN_IDS:
        counts = per_domain[domain]
        numbers = [value for value, times in counts.items() if isinstance(value, int)
                   for _ in range(times)]
        mean = f"{sum(numbers) / len(numbers):.2f}" if numbers else "—"
        lines.append(
            f"| **Dominio {domain[1:]}** · {rubric.DOMAINS[domain]['title_es']} | "
            + " | ".join(str(counts[level]) for level in rubric.LEVELS)
            + f" | {counts[rubric.NOT_ASSESSABLE]} | {mean} |")
    lines.append("| **Total** | "
                 + " | ".join(str(distribution[level]) for level in rubric.LEVELS)
                 + f" | {distribution[rubric.NOT_ASSESSABLE]} | |")

    lines += ["", FINDINGS.strip(), "", "## 10 · Costo y procedencia", "",
              f"- **{requests or len(runs)} solicitudes pagadas** en la primera pasada, una "
              f"por encuentro, {round(seconds)} segundos en total de las once nuevas.",
              "- **Dos verificaciones más** después del cambio de regla, una por cada caso de "
              "alta insegura (`hypoglycemia_76f` y `opioid_67f`), 116 s en total.",
              "- **Quince solicitudes en total**, de las veinte autorizadas.",
              "- Modelo `gpt-5-mini`. Ningún reintento automático: el guión cuenta las "
              "solicitudes y aborta antes de una segunda, y una corrida nueva no sobrescribe "
              "una anterior: escribe el número siguiente al lado.",
              "- Costo estimado por debajo de US$0,45 en total.",
              "- Las propuestas crudas están en `local-data/paid_runs/rubric_pilot/`, junto con "
              "el registro jugado y la transcripción de cada encuentro.",
              "- Los guiones están en `tools_rubric_runs.py`; `--play` reproduce cualquier "
              "encuentro sin costo alguno.", ""]

    out = ROOT / "docs" / "RUBRICA_PILOTO_CORRIDAS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("escrito:", out)
    print(f"  {hits}/{hits + misses} eventos esperados · {false_positives} no buscados")
    return hits, misses, false_positives


FINDINGS = """
## 4 · El hallazgo principal: "no evaluable" no se usó nunca

**Sesenta y cinco puntajes de dominio, trece encuentros, cero usos de `not_assessable`.**

La instrucción está escrita, y el modelo la lee: *"Use 'not_assessable' when the case offered
no real opportunity, the record holds insufficient evidence, or the simulator could not observe
the performance"*, y en la línea siguiente *"'not_assessable' is NOT a zero"*.

Dos encuentros se escribieron precisamente para ponerla a prueba, y en los dos el modelo
puntuó en vez de declarar la falta de oportunidad:

- **`acs_48m_wellens`** (corrida 1): la única entrega que llevaba un destino fue retenida por
  el intérprete. El modelo reconoció que no se ejecutó y aun así puso D5 = 1.
- **`acs_52m_de_winter`**: encuentro truncado a los 15 minutos, dos decisiones. El modelo puso
  D5 = 1 y escribió, en el mismo campo de límites: *"No disposition, consultation, or
  reperfusion pathway activation is recorded before case closure"*.

Es decir: **el modelo sabe el hecho y aun así lo convierte en un puntaje.** No es que no lo
vea; es que la diferencia entre "no lo hizo" y "no pudo observarse" no le resulta accionable.

Esto no es un defecto del contrato. Es exactamente el juicio que la especificación dejó en
manos del docente, y trece encuentros muestran que lo va a necesitar en todos. Lo que sí
sugiere es que **el valor por defecto del selector no debería ser el puntaje propuesto cuando
el propio modelo declara que el encuentro cerró antes de la oportunidad** — pero ese es un
cambio a la rúbrica y queda para tu decisión.

## 5 · Los eventos críticos: el modelo los propone bien, y no dispara de más

Siete de los ocho eventos que los guiones buscaban fueron propuestos, cada uno citando la
decisión, el minuto y los observables, y cada uno revisando las exclusiones declaradas antes
de proponerlo. Dos ejemplos, en sus palabras:

> `edema_volume_loading` — *"POCUS at minute 12 showed diffuse bilateral B-lines... Despite
> these findings of congestion and no documented cause of hypovolaemia, a 500 mL normal saline
> IV bolus was executed at minute 23."* Exclusiones: *"No prior record established a
> hypovolaemic contributor before the bolus."*

> `pneumonia_unexamined_altered_state` — *"Arrival state shows mental_status 'Drowsy'. In the
> 0–60 min window there is no executed bedside glucose, no documented focused neurological
> examination, and no head imaging recorded."*

Y, sobre todo, **no propuso los que no correspondían**:

- en `pneumonia_83m` no propuso `pneumonia_no_antibiotic`, porque la ceftriaxona sí se dio;
- en `hypoglycemia_54m_thiamine` no propuso `hypo_no_glucose`, porque la glucosa sí se dio;
- en `asthma_49m` propuso la falta de soporte ventilatorio **aunque el motor mejoró al
  paciente** tras el broncodilatador. Puntuó la decisión, no el desenlace, que es lo que la
  instrucción pide.

## 6 · El único evento que faltó, por qué el modelo tenía razón, y lo que decidiste

`hypoglycemia_76f`: el residente corrige la glicemia y manda a la paciente a la casa. La
paciente toma glimepirida. El evento `hypo_unsafe_discharge` existe para eso, y el modelo **no
lo propuso**.

Escribí ese guión esperando que lo propusiera. Se equivocó mi diseño, no el modelo.

El evento declara `information_required: "The history of the causative agent"`, y el residente
nunca preguntó por los medicamentos. La glimepirida está en la historia del caso, pero sólo
aparece si alguien la pide. El modelo lo dijo con precisión:

> *"No explicit medication history in the encounter to confirm or exclude sulfonylurea or other
> long-acting hypoglycaemic agents."*

y en vez de asumirla, mandó la preocupación al canal que existe para eso:

> *"Discharge executed after severe hypoglycaemia without a documented plan for continued
> observation, medication review to exclude long-acting hypoglycaemic agents, or explicit
> handover — this may be unsafe depending on etiology."*

**Eso es el comportamiento correcto**, y es el mismo error que cometí yo el 2026-09-23 cuando
mi propuesta ilustrativa inventó un valor de troponina que el registro no contenía.

### Tu decisión, y lo que cambió por ella (2026-09-23)

Te planteé la pregunta y la respondiste: **el evento se dispara igual.** El paciente está ahí y
se le puede preguntar; si el residente no lo hace, eso debe ser un punto de análisis explícito
en el Management Trace y en el Faculty Brief, y debe reflejarse en el puntaje.

Eso es ahora una regla del instrumento, no un parche a un caso:

> **La información disponible preguntando está disponible, se haya preguntado o no.** El
> paciente, o la fuente colateral que el caso nombra, está presente todo el encuentro y
> responde. Un residente que nunca preguntó no fue privado de la información: omitió
> obtenerla. Una historia no preguntada **nunca excusa un evento crítico**, y no haberla
> preguntado es en sí una omisión que la evaluación nombra.

Cómo quedó implementada:

- Cada evento declara ahora, por separado, **lo que tenía que estar en el registro** (los
  observables, un resultado, una acción ejecutada) y **lo que el caso responde si le preguntan**
  —cada uno como un par (tema de historia, qué le diría)—. `case_assessment.verify` comprueba
  que el tema prometido sea uno que el caso realmente escribe, igual que ya comprobaba que un
  estudio prometido esté entre sus investigaciones. **21 de 21 casos, cero discrepancias.**
- Nueve de los dieciséis eventos tenían una exigencia de historia; todas se movieron.
- La regla viaja con cada solicitud y está en las instrucciones de la rúbrica y del brief.

### La verificación, con una llamada pagada (2026-09-23)

Corrí **el mismo encuentro otra vez**, sin cambiar una sola orden del residente, para que la
comparación fuera directa. Una llamada, 65 s.

| | Antes | Después |
|---|---|---|
| D1 | 2 | 2 |
| D2 | 2 | **3** |
| D3 | 2 | 2 |
| D4 | 2 | 2 |
| D5 | 1 | **0** |
| Evento | ninguno | **`hypo_unsafe_discharge`** |
| Con el docente confirmando | `Base 9/15` | `Base 9/15 · Penalización −3 · Ajustado 6/15` |

El modelo propuso el evento y citó la orden del residente en sus propias palabras:

> *"An executed discharge disposition was recorded (trace:3 decision at minute 26: 'La envio a
> su casa...')... The case provides that the hypoglycaemia is attributable to a sulfonylurea
> **available on asking**; failure to arrange observation after such an episode meets the event
> trigger."*

Vale la pena notar que esa orden sólo existe en el registro porque anoche se arregló que `a su
casa` fuera un alta. Antes, la orden se evaporaba en silencio y con ella el evento.

Y D5 pasó a 0 con el fundamento escrito como la regla:

> *"The case specifies the hypoglycaemia is attributable to a long-acting sulfonylurea
> (information available on asking); discharging without observation after such an episode is
> unsafe."*

**Dónde no funcionó todavía.** D2 **subió** de 2 a 3. El modelo sí nombró la omisión, en la
evidencia en contra —*"The learner did not ask about medications (medication history is
available on asking)"*— y en dos preocupaciones señaladas. Pero no dejó que moviera el número:
*"this omission does not negate that relevant diagnostic data were obtained"*.

Es decir: **la regla llegó al evento y a la continuidad; a la evaluación, en esta corrida, no.**
La segunda verificación, más abajo, matiza cuánto de eso es la regla y cuánto es este encuentro.

### La segunda verificación: otro caso, otra alta insegura

`opioid_67f`. Mujer de 67 años, morfina de liberación prolongada en su lista. El residente
ventila, revierte con naloxona, la paciente despierta, y la manda a la casa. Nunca pregunta qué
opioide tomaba. Una llamada, 51 s.

**Propuso `opioid_unsafe_discharge`**, y esta vez usó la regla como *argumento a favor* del
evento, no como algo que salvar:

> *"Naloxone 0.4 mg IV was given (trace:1) and a discharge home disposition was executed
> (trace:4) with no documented observation period or admission. **The case offered exposure
> details on asking (long-acting agent), which were not obtained.**"*

D5 = 0, *"given the information the case offered about exposure"*. Y notó lo que el residente
escribió creyendo que bastaba:

> *"The learner did state 'Reevaluo en 15 minutos' at the time of discharge, but this does not
> constitute a documented plan for observation, admission, or duration that would mitigate the
> known risk of recurrence following short-acting reversal."*

Con el docente confirmando: `Base 9/15 · Penalización −3 · Ajustado 6/15`, igual que el otro.

**D2 en las dos verificaciones.** Nombró la omisión las dos veces en la evidencia en contra
—aquí *"They did not ask about the specific opioid or formulation"*— y la puntuó distinto: 3 en
la hipoglicemia, 2 en el opioide. Nombrarla es consistente; dejar que mueva el número, no. Esa
sigue siendo la parte del juicio que el docente pone.

### Un tercer defecto del intérprete, encontrado al escribir el segundo guión

`La envio a su casa con indicacion de volver si se repite` no producía **nada**: el `si` de la
recomendación hacía condicional toda la frase, incluida el alta. El consejo lleva su propia
condición y la orden que lo precede no depende de ella. Leída como una sola condicional, la
disposición se evaporaba en silencio —y un alta es el disparador de dos eventos críticos
definidos, así que el evento se iba con ella.

Es la tercera vez en dos días que el mismo tipo de defecto aparece en la misma frase: la que
cierra el encuentro. Las tres estaban en español y las tres borraban el dominio 5.

Corregido para `con indicación de`, `con instrucciones de`, `indicándole`, `le indico`, `con
control en`, `with instructions to`, `advised to` y `return precautions`. Una orden que sí es
condicional —`hospitalizar en sala si empeora`, `doy oxígeno si baja la saturación`— sigue
siendo condicional, y hay pruebas de las dos cosas.

### Dos defectos silenciosos que la pregunta destapó

**La historia era invisible para todo.** Preguntar no es una orden: no consume tiempo simulado
y no cambia ningún observable, así que vive en los eventos del encuentro y no en la traza.
**Nada que construyera un análisis miraba ahí.** Cuando el modelo escribió *"No explicit
medication history in the encounter"* estaba diciendo la verdad sobre lo que le habían
mostrado, y algo falso sobre el encuentro. Ahora la historia obtenida, los temas ofrecidos y
los temas que nadie preguntó viajan en la misma fuente que leen los cuatro documentos.

**El caso también era invisible.** `case_id_of` leía sólo el campo que escribe la exportación, y
una sesión guardada no tiene ese campo: la app guarda sus campos de sesión y nada más. **Todo
encuentro real parecía un caso sin declaración: sin oportunidades declaradas y sin ningún evento
crítico definido.** Cada prueba que ejercitaba esa capa ponía el campo a mano, así que la suite
estaba verde mientras el camino de producción estaba muerto. Se lee ahora también desde el
estado que la sesión sí guarda, con una prueba que construye el payload campo por campo como lo
arma la app.

## 7 · Lo que el rango sugiere

- **D3 es el único dominio que llega a 0**, y llega exactamente donde hay un evento confirmado.
  El descriptor funciona como está escrito: *"ordena algo claramente peligroso"* o la omisión de
  una intervención esencial es un 0, no un 1.
- **D4 nunca bajó de 2** en trece encuentros. Declarar "reevalúo en 15 minutos" parece bastar
  para un 2, y ningún guión logró un 1 ahí, ni siquiera los que reevaluaron mal.
- **D5 nunca llegó a 3.** Ni el encuentro más competente lo alcanzó.
- Fuera de D3, las medias están todas entre 2,2 y 2,3. El instrumento discrimina bien la
  seguridad y discrimina poco el resto.

Con trece encuentros esto es una señal, no una medición. Pero si el piloto se corre con
residentes reales, **D4 y D5 son los descriptores que conviene mirar primero**.

## 8 · Dos cosas que siguen pendientes de ti

**El idioma del fundamento.** El contrato le pide al modelo que responda *en inglés*, y por eso
el informe de rúbrica en español lleva los rótulos, los dominios y la decisión docente en
español pero el fundamento del modelo en inglés. El documento ahora lo dice en vez de dejarlo
implícito. Cambiarlo es una llamada pagada por encuentro y una nueva versión de prompt, así que
no lo toqué.

**El valor por defecto del selector.** Hoy el selector del docente arranca en el puntaje que
propuso la IA. Dado que en trece encuentros la IA nunca eligió "no evaluable" —ni siquiera
donde ella misma escribió que el encuentro cerró antes de la oportunidad— ese valor por defecto
empuja hacia un puntaje. Es un cambio de una línea, pero cambia el comportamiento de la
rúbrica, así que queda para tu aprobación.

## 9 · Lo que se arregló en el camino

Escribir once encuentros en el español en que los escribe un residente encontró cinco
defectos del intérprete, todos en la misma frase: la que cierra el encuentro.

El español pone el pronombre **antes** del verbo. Nada lo leía, así que la frase no tenía verbo
inicial. `Le doy aspirina 300 mg vo` quedaba retenida como orden no reconocida, y
`lo hospitalizo en sala` y `le pido un electrocardiograma` **no producían ni acción ni
mensaje**. El silencio es peor que la retención, y caía sobre el destino del paciente, que es
todo el dominio 5: un dominio que no se puede puntuar porque la orden se evaporó no es un
residente que no decidió.

Los otros cuatro, en las mismas frases: `hospitalizar en sala para continuar broncodilatadores
y corticoides` se partía en "y" y el fragmento heredaba el verbo de ingreso, pedía un destino
que no tenía, y retenía toda la entrega; `a su casa` y `a domicilio` no eran un alta (sólo lo
era `a la casa`), y un alta es el disparador de un evento crítico definido, así que el silencio
se llevaba el evento con él; `angiotomografía de tórax` escrita completa se rechazaba; y el
equipo de tromboembolismo sólo existía por su sigla en inglés.

Los cinco están corregidos, con pruebas, en `test_spanish_pronoun_before_the_verb.py`.

### Y uno que introduje yo

Al hacer visible la historia, `history_review` alcanzaba las etiquetas de los temas a través de
`clinical_scene`, que importa Streamlit y PIL. Es decir: un PDF docente y una declaración de
rúbrica importaban Streamlit **para saber que `medications` se llama "Medications"**. Cuando un
hilo lo importaba mientras un hilo de script de Streamlit ya tenía tomado el lock de importación
de ese módulo, la suite completa se quedó detenida **dos horas** en
`test_exploring_patient_preserves_state_and_management_remains_reachable`.

Las etiquetas viven ahora en `history_topics.py`, una hoja sin ninguna importación, y
`clinical_scene` las reexporta para que ningún lector existente cambie. Hay una prueba que
arranca un intérprete limpio y verifica que importar `history_review` no traiga Streamlit ni
PIL.

Lo encontró la disciplina de correr la suite completa antes de cada commit, no una prueba: el
síntoma era una suite que no terminaba nunca, que es peor que una que falla.
"""


if __name__ == "__main__":
    main()
