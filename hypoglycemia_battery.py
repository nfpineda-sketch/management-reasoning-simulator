"""The trajectory battery of the hypoglycaemia catalogue: every compatible configuration, played.

Faculty authorisation of 2026-09-25 (stage 2). Each configuration is played on
the real bank engine with structured actions -- the orders as the engine
receives them after the reader -- along four kinds of trajectory: adequate
management (with the defensible alternatives), delay, a frequent error, and
recovery after it. No provider is called and nothing is paid.

Two kinds of check, never merged:

* **technical** -- the engine does what the model says it does: a line that
  is not in the vein holds back the dextrose bolus given through it, the oral
  route is refused to a patient who cannot swallow, thiamine neither wakes nor
  harms (faculty decision 8). A failure is a technical defect to correct -- unless
  its correction needs a clinical choice, and then it is reported as a
  *pending clinical decision* and nothing is changed to make it pass;
* **reference** -- the times and magnitudes the current parameters produce
  (the seizure after twenty minutes below 40 mg/dL, the recurrence of a
  sulfonylurea, the rebound of an overcorrection...). They are a *technical
  reference*, kept so a change in behaviour is noticed. They are **not**
  approved clinical criteria, and each names the parameters it rests on
  (``hypoglycemia_catalog.SIMPLIFICATIONS``, with the review each has had:
  reviewed or not, a reference is never a criterion).

"Tested" means: these scripts ran and no technical check found a technical
defect; a check held by a pending clinical decision is shown apart, with its
decision. It is a statement about coverage. It is not "validated", and it says nothing about
free text: the reader is checked on its own (``test_hypoglycemia_reader``), and
a structured action proves nothing about the words that should produce it.
"""
from copy import deepcopy

import catalog_trajectories as trajectories
import glucose_rescue
import hypoglycemia_catalog as catalog
from hypoglycemia_preservation import (DEXTROSE_IV, DOUBLE_DEXTROSE_IV, GLUCAGON_IM, GLUCOSE, HOME, INFUSION,
                                       LINE, OBSERVATION, OCTREOTIDE_SC, ORAL, THIAMINE_IV, WARD, wait)

FAMILY = catalog.FAMILY
BATTERY_VERSION = "1.0"
TRAJECTORY_KINDS = {"adequate": "Manejo adecuado", "delay": "Demora", "error": "Error frecuente",
                    "recovery": "Recuperación"}

# Pending clinical decisions a technical check can run into (the document
# docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md explains each).
PENDING = {
    "DC1": "Estado de conciencia de llegada frente al umbral del motor",
    "DC4": "Alcance de la vía fallida: la decisión 8 la aplicó sólo a la glucosa en bolo",
}


# --- running ---------------------------------------------------------------------
def observe(configuration_id, turns):
    """Play the turns on a fresh launch; return a timeline and the final state."""
    state = trajectories.launch(configuration_id, FAMILY, allow_review_candidates=True)
    initial = deepcopy(state)
    rows = trajectories.run(state, turns)
    timeline = [{"t": 0, "glucose": float(initial["observable"]["glucose_mg_dl"]),
                 "mental": initial["observable"]["mental_status"], "executed": None, "labels": []}]
    for row in rows:
        f, o = row["state"]["family_state"], row["state"]["observable"]
        # A refused first turn leaves the engine uninitialised: the glucose is still the arrival one.
        glucose = f["glucose"] if "glucose" in f else o["glucose_mg_dl"]
        timeline.append({"t": row["state"]["sim_time"], "glucose": float(glucose), "mental": o["mental_status"],
                         "executed": bool(row["result"].get("executed")),
                         "clarification": row["result"].get("clarification"),
                         "labels": [s.get("label") for s in row["result"].get("action_summaries") or []]})
    final = rows[-1]["state"] if rows else initial
    return {"timeline": timeline, "final": final, "initial": initial}


def _labels(run):
    return [label or "" for step in run["timeline"] for label in step["labels"]]


def _f(run):
    return run["final"]["family_state"]


def _glucose_at(run, step):
    return run["timeline"][step]["glucose"]


# --- the scripts ---------------------------------------------------------------------
def _dose(configuration, dextrose=DEXTROSE_IV):
    """An ampoule by a route that reaches the patient: a new line first when the old one failed."""
    return [LINE, dextrose] if configuration["conditions"]["iv_access_failed"] else [dextrose]


def _maintenance(configuration):
    mechanism = configuration["axes"]["mechanism"]
    if mechanism == "sulfonylurea":
        return [INFUSION]
    if mechanism == "alcohol_fasting":
        return [THIAMINE_IV]
    return [ORAL]


def _destination(configuration):
    return [WARD] if configuration["axes"]["mechanism"] != "insulin" else [OBSERVATION]


def scripts(configuration):
    """Every script this configuration is played with, with what each is for."""
    c, found = configuration["conditions"], []
    mechanism = configuration["axes"]["mechanism"]
    failed, severe = c["iv_access_failed"], configuration["axes"]["severity"] == "severe"

    def add(identifier, kind, es, turns):
        found.append({"id": identifier, "kind": kind, "es": es, "turns": turns})

    add("adequate", "adequate", "Glucosa capilar, ampolla por una vía que llega, mantención y destino",
        [[GLUCOSE], [*_dose(configuration), wait(10)], [GLUCOSE], [*_maintenance(configuration), wait(30)],
         [GLUCOSE], [*_destination(configuration), wait(60)], [GLUCOSE]])
    add("adequate_new_line_first", "adequate", "Alternativa: vía nueva antes de la primera dosis",
        [[LINE, DEXTROSE_IV, wait(10)], [GLUCOSE], [wait(30)], [GLUCOSE]])
    if c["thiamine_deficient"]:
        add("adequate_without_thiamine", "adequate", "Alternativa: la misma corrección sin tiamina",
            [[GLUCOSE], [*_dose(configuration), wait(10)], [GLUCOSE], [wait(30)], [GLUCOSE],
             [*_destination(configuration), wait(60)], [GLUCOSE]])
    if mechanism == "sulfonylurea":
        add("adequate_octreotide", "adequate", "Alternativa: octreótido en vez de infusión",
            [[*_dose(configuration), OCTREOTIDE_SC, wait(20)], [GLUCOSE], [wait(60)], [GLUCOSE],
             [WARD, wait(60)], [GLUCOSE]])
    if failed:
        add("adequate_glucagon_first", "adequate", "Alternativa: glucagón intramuscular sin usar la vía fallida",
            [[GLUCAGON_IM, wait(20)], [GLUCOSE], [LINE, DEXTROSE_IV, wait(10)], [GLUCOSE]])
    add("delay", "delay", "25 minutos sin nada que suba la glucosa, luego el manejo adecuado",
        [[GLUCOSE], [wait(25)], [*_dose(configuration), wait(15)], [GLUCOSE],
         [*_maintenance(configuration), wait(30)], [GLUCOSE]])
    if failed:
        add("error_failed_line_used", "error", "Error: ampolla por la vía con que llegó, sin revisarla",
            [[DEXTROSE_IV, wait(10)], [GLUCOSE]])
        add("recovery_failed_line", "recovery", "Recuperación: tras la ampolla que no llegó, vía nueva y ampolla",
            [[DEXTROSE_IV, wait(10)], [GLUCOSE], [LINE, DEXTROSE_IV, wait(10)], [GLUCOSE]])
        add("error_infusion_through_failed_line", "error", "Error: infusión por la vía fallida",
            [[INFUSION, wait(30)], [GLUCOSE]])
    if mechanism == "sulfonylurea":
        add("error_early_discharge", "error", "Error: alta tras la primera ampolla",
            [[*_dose(configuration), wait(15)], [GLUCOSE], [HOME, wait(60)], [wait(60)], [wait(60)]])
        add("recovery_after_return", "recovery", "Recuperación: al volver, ampolla, infusión y hospitalización",
            [[*_dose(configuration), wait(15)], [HOME, wait(60)], [wait(60)],
             [DEXTROSE_IV, INFUSION, WARD, wait(30)], [GLUCOSE], [wait(60)], [GLUCOSE]])
    add("error_overcorrection", "error", "Error: doble ampolla",
        [[*_dose(configuration, DOUBLE_DEXTROSE_IV), wait(10)], [GLUCOSE], [wait(40)], [GLUCOSE], [wait(30)],
         [GLUCOSE]])
    add("error_glucagon_only", "error", "Glucagón intramuscular como única medida",
        [[GLUCAGON_IM, wait(20)], [GLUCOSE]])
    add("control_untreated", "delay", "Control: sin tratamiento, leído a los 20 y a los 30 minutos, para medir efectos",
        [[wait(20)], [wait(10)]])
    if severe and not failed:
        add("error_infusion_without_bolus", "error", "Error: infusión sin ampolla en una hipoglicemia severa",
            [[INFUSION, wait(30)], [GLUCOSE]])
    add("error_oral_while_not_alert", "error", "Error: carbohidrato oral a un paciente que no está alerta", [[ORAL]])
    add("recovery_after_refused_oral", "recovery", "Recuperación: tras la vía oral rechazada, la ampolla por una vía que llega",
        [[ORAL], [*_dose(configuration), wait(10)], [GLUCOSE]])
    if c["thiamine_deficient"]:
        add("error_thiamine_instead_of_glucose", "error", "Error: tiamina sin glucosa",
            [[THIAMINE_IV, wait(15)], [GLUCOSE]])
    return found


# --- the checks ----------------------------------------------------------------------
def _result(status, observed, **extra):
    return {"status": status, "observed": observed, **extra}


def _check_arrival(configuration, runs):
    run = runs["adequate"]
    authored = run["timeline"][0]["mental"]
    engine = glucose_rescue.consciousness(run["timeline"][0]["glucose"])
    ok = authored == engine
    return _result("passed" if ok else "failed",
                   f"llega '{authored}'; con {run['timeline'][0]['glucose']:g} mg/dL el motor muestra '{engine}' "
                   "desde el primer minuto")


def _check_raise(configuration, runs):
    run = runs["adequate"]
    before, after = _glucose_at(run, 1), _glucose_at(run, 2)
    return _result("passed" if after >= 70 and after - before >= 80 else "failed",
                   f"{before:.0f} → {after:.0f} mg/dL tras la ampolla por una vía que llega")


def _check_new_line(configuration, runs):
    run = runs["adequate_new_line_first"]
    labels = _labels(run)
    ok = run["timeline"][1]["glucose"] >= 70
    if configuration["conditions"]["iv_access_failed"]:
        ok = ok and glucose_rescue.NEW_ACCESS_TEXT in labels
    return _result("passed" if ok else "failed", f"{run['timeline'][1]['glucose']:.0f} mg/dL a los 10 minutos")


def _check_failed_line_reported(configuration, runs):
    labels = _labels(runs["error_failed_line_used"])
    ok = glucose_rescue.FAILED_ACCESS_TEXT in labels
    return _result("passed" if ok else "failed",
                   "el motor dice que la glucosa no pasa" if ok else "ningún aviso de la vía fallida")


def _check_failed_line_share(configuration, runs):
    run = runs["error_failed_line_used"]
    rise = _glucose_at(run, 1) - _glucose_at(run, 0)
    expected = glucose_rescue.FAILED_ACCESS_SHARE * 25 * 4
    return _result("passed" if rise <= expected + 2 else "failed",
                   f"sube {rise:.1f} mg/dL; el {glucose_rescue.FAILED_ACCESS_SHARE:.0%} de la ampolla son "
                   f"{expected:.0f}")


def _check_failed_infusion(configuration, runs):
    # The infusion's own effect: the glucose with it minus the same patient
    # untreated at the same minute, so a sulfonylurea's fall cannot hide it.
    effect = _glucose_at(runs["error_infusion_through_failed_line"], 1) - _glucose_at(runs["control_untreated"], 2)
    full = 100 / 60 * glucose_rescue.INFUSION_G_PER_ML * 4 * 30
    return _result("passed" if effect <= full * glucose_rescue.FAILED_ACCESS_SHARE + 1 else "failed",
                   f"en 30 minutos aporta {effect:.1f} mg/dL; entera aportaría {full:.0f} y por la vía fallida "
                   f"{full * glucose_rescue.FAILED_ACCESS_SHARE:.0f}")


def _check_recovery_line(configuration, runs):
    run = runs["recovery_failed_line"]
    ok = _glucose_at(run, 4) >= 70 and glucose_rescue.NEW_ACCESS_TEXT in _labels(run)
    return _result("passed" if ok else "failed", f"{_glucose_at(run, 4):.0f} mg/dL tras la vía nueva")


def _check_oral_refused(configuration, runs):
    step = runs["error_oral_while_not_alert"]["timeline"][1]
    ok = step["executed"] is False and bool(step.get("clarification"))
    return _result("passed" if ok else "failed", "rechazado" if ok else "ejecutado")


def _check_recovery_after_refusal(configuration, runs):
    run = runs["recovery_after_refused_oral"]
    ok = run["timeline"][1]["executed"] is False and run["timeline"][3]["mental"] == "Alert"
    return _result("passed" if ok else "failed",
                   f"tras el rechazo, {run['timeline'][3]['glucose']:.0f} mg/dL y {run['timeline'][3]['mental']}")


def _check_rebound(configuration, runs):
    own = configuration["conditions"]["endogenous_insulin"]
    rebound = _f(runs["error_overcorrection"]).get("rebound_at") is not None
    return _result("passed" if rebound == own else "failed",
                   ("rebote" if rebound else "sin rebote") + (" con" if own else " sin") + " secreción propia")


def _check_recurrence(configuration, runs):
    run = runs["adequate_new_line_first"]
    fall = (_glucose_at(run, 2) - _glucose_at(run, 3)) / 30
    sulfonylurea = configuration["conditions"]["sulfonylurea_effect"]
    ok = fall >= .4 if sulfonylurea else fall <= .1
    return _result("passed" if ok else "failed", f"cae {fall:.2f} mg/dL/min sin mantención")


def _check_octreotide(configuration, runs):
    run = runs["adequate_octreotide"]
    fall = (_glucose_at(run, 2) - _glucose_at(run, 3)) / 60
    return _result("passed" if fall <= .1 else "failed", f"cae {fall:.2f} mg/dL/min con octreótido activo")


def _check_thiamine_neutral(configuration, runs):
    with_ = [step["mental"] for step in runs["adequate"]["timeline"][:5]]
    without = [step["mental"] for step in runs["adequate_without_thiamine"]["timeline"][:5]]
    alone = runs["error_thiamine_instead_of_glucose"]
    unchanged = alone["timeline"][-1]["mental"] == glucose_rescue.consciousness(alone["timeline"][-1]["glucose"])
    ok = with_ == without and unchanged and "Alert" in without
    return _result("passed" if ok else "failed",
                   f"con tiamina {with_[-1]}, sin tiamina {without[-1]}; la tiamina sola no cambia la conciencia")


def _check_seizure_timing(configuration, runs):
    seizure = _f(runs["delay"]).get("seizure_at")
    if configuration["axes"]["severity"] == "severe":
        low, high = glucose_rescue.SEIZURE_AFTER_MIN - 1, glucose_rescue.SEIZURE_AFTER_MIN + 2
        ok = seizure is not None and low <= seizure <= high
        return _result("passed" if ok else "failed", f"convulsión al minuto {seizure}")
    ok = seizure is None
    return _result("passed" if ok else "failed",
                   "sin convulsión en 25 minutos" if ok else f"convulsión al minuto {seizure}")


def _check_recovery_after_delay(configuration, runs):
    run = runs["delay"]
    mental = run["timeline"][4]["mental"]
    return _result("passed" if mental == "Alert" else "failed",
                   f"a los {run['timeline'][4]['t']} min: {mental}, {run['timeline'][4]['glucose']:.0f} mg/dL")


def _check_alert_after_ampoule(configuration, runs):
    run = runs["adequate"]
    return _result("passed" if run["timeline"][2]["mental"] == "Alert" else "failed",
                   f"{run['timeline'][2]['mental']} a los 10 minutos de la ampolla")


def _check_stable_after_maintenance(configuration, runs):
    run = runs["adequate"]
    lowest = min(step["glucose"] for step in run["timeline"][2:])
    return _result("passed" if lowest >= 70 else "failed", f"mínimo {lowest:.0f} mg/dL en las dos horas siguientes")


def _check_return_after_discharge(configuration, runs):
    f = _f(runs["error_early_discharge"])
    ok = bool(f.get("discharge_return_reported"))
    return _result("passed" if ok else "failed", "vuelve tras el alta" if ok else "no vuelve")


def _check_recovery_after_return(configuration, runs):
    run = runs["recovery_after_return"]
    lowest = min(step["glucose"] for step in run["timeline"][5:])
    return _result("passed" if lowest >= 70 else "failed", f"mínimo {lowest:.0f} mg/dL tras hospitalizarla")


def _check_rebound_timing(configuration, runs):
    f = _f(runs["error_overcorrection"])
    if f.get("rebound_at") is None:
        return _result("not_observed", "sin rebote en esta configuración")
    run = runs["error_overcorrection"]
    fall = (_glucose_at(run, 3) - _glucose_at(run, 5)) / 30
    return _result("passed" if fall >= .8 else "failed", f"cae {fall:.2f} mg/dL/min tras el rebote")


def _check_glucagon(configuration, runs):
    # The effect of one dose: the glucose with it minus the glucose of the same
    # patient untreated over the same twenty minutes. What the current
    # parameters say it should be: their rate over the minutes of the window
    # that fall inside the twenty, times the share glycogen allows.
    effect = _glucose_at(runs["error_glucagon_only"], 1) - _glucose_at(runs["control_untreated"], 1)
    depleted = configuration["conditions"]["glycogen_depleted"]
    minutes = 20 - glucose_rescue.GLUCAGON_ONSET_MIN + 1
    expected = (glucose_rescue.GLUCAGON_MG_DL_PER_MIN * minutes
                * (glucose_rescue.DEPLETED_GLYCOGEN_SHARE if depleted else 1.0))
    return _result("passed" if abs(effect - expected) <= 1.5 else "failed",
                   f"efecto de {effect:.1f} mg/dL en 20 minutos " + ("sin glucógeno" if depleted else "con glucógeno")
                   + f" (los parámetros dicen {expected:.1f})")


def _check_infusion_alone(configuration, runs):
    run = runs["error_infusion_without_bolus"]
    return _result("passed" if _glucose_at(run, 1) < 70 else "failed",
                   f"{_glucose_at(run, 1):.0f} mg/dL tras 30 minutos de infusión sin ampolla")


def _applies(*conditions):
    return lambda configuration: all(condition(configuration) for condition in conditions)


def _failed(c):
    return c["conditions"]["iv_access_failed"]


def _sulfonylurea(c):
    return c["axes"]["mechanism"] == "sulfonylurea"


def _thiamine(c):
    return c["conditions"]["thiamine_deficient"]


def _severe_working(c):
    return c["axes"]["severity"] == "severe" and not c["conditions"]["iv_access_failed"]


CHECKS = (
    # technical
    {"id": "T1", "kind": "technical", "trajectory": "adequate", "check": _check_raise,
     "es": "Una ampolla por una vía que llega sube la glucosa sobre 70 mg/dL"},
    {"id": "T2", "kind": "technical", "trajectory": "adequate", "check": _check_new_line,
     "es": "Con una vía nueva lo que se da llega (y el motor lo dice si reemplaza una fallida)"},
    {"id": "T3", "kind": "technical", "trajectory": "error", "check": _check_failed_line_reported,
     "applies": _failed, "es": "La primera dosis por la vía fallida se informa como no llegada"},
    {"id": "T4", "kind": "technical", "trajectory": "error", "check": _check_failed_line_share,
     "applies": _failed, "es": "Por la vía fallida llega sólo la fracción del modelo"},
    {"id": "T5", "kind": "technical", "trajectory": "error", "check": _check_failed_infusion,
     "applies": _failed, "on_failure": "DC4",
     "es": "Una infusión por la vía fallida tampoco llega (el aviso de la vía dice que la infusión se detiene)"},
    {"id": "T6", "kind": "technical", "trajectory": "recovery", "check": _check_recovery_line,
     "applies": _failed, "es": "Tras reconocer la vía fallida, la vía nueva corrige la glucosa"},
    {"id": "T7", "kind": "technical", "trajectory": "error", "check": _check_oral_refused,
     "es": "La vía oral se rechaza a un paciente que no está alerta"},
    {"id": "T13", "kind": "technical", "trajectory": "recovery", "check": _check_recovery_after_refusal,
     "es": "Una orden rechazada no deja nada a medias: la siguiente, correcta, se ejecuta completa"},
    {"id": "T8", "kind": "technical", "trajectory": "error", "check": _check_rebound,
     "es": "El rebote de una sobrecorrección ocurre sólo con secreción propia de insulina"},
    {"id": "T9", "kind": "technical", "trajectory": "adequate", "check": _check_recurrence,
     "es": "Sin mantención la glucosa vuelve a caer sólo con efecto de sulfonilurea"},
    {"id": "T10", "kind": "technical", "trajectory": "adequate", "check": _check_octreotide,
     "applies": _sulfonylurea, "es": "El octreótido detiene la caída de la sulfonilurea"},
    {"id": "T11", "kind": "technical", "trajectory": "adequate", "check": _check_thiamine_neutral,
     "applies": _thiamine, "es": "La tiamina no despierta al paciente ni su ausencia lo deteriora (decisión 8)"},
    {"id": "T12", "kind": "technical", "trajectory": "adequate", "check": _check_arrival,
     "on_failure": "DC1", "es": "El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1"},
    # reference: current parameters, pending clinical review
    {"id": "R1", "kind": "reference", "trajectory": "adequate", "check": _check_alert_after_ampoule,
     "parameters": ("P3", "P4"), "es": "Alerta a los 10 minutos de una ampolla efectiva"},
    {"id": "R2", "kind": "reference", "trajectory": "adequate", "check": _check_stable_after_maintenance,
     "parameters": ("P1", "P6", "P7", "P9"), "es": "Con la mantención de su mecanismo no vuelve a bajar de 70"},
    {"id": "R3", "kind": "reference", "trajectory": "delay", "check": _check_seizure_timing,
     "parameters": ("P1", "P2"), "es": "Severa: convulsión a los 20 minutos bajo 40; moderada: sin convulsión en 25"},
    {"id": "R4", "kind": "reference", "trajectory": "delay", "check": _check_recovery_after_delay,
     "parameters": ("P2", "P3", "P4"), "es": "Alerta a los 15 minutos de tratarla tras la demora"},
    {"id": "R5", "kind": "reference", "trajectory": "error", "check": _check_return_after_discharge,
     "applies": _sulfonylurea, "parameters": ("P1", "P11"), "es": "Dada de alta tras la primera ampolla, vuelve"},
    {"id": "R6", "kind": "reference", "trajectory": "recovery", "check": _check_recovery_after_return,
     "applies": _sulfonylurea, "parameters": ("P1", "P7"), "es": "Al volver, ampolla e infusión la mantienen sobre 70"},
    {"id": "R7", "kind": "reference", "trajectory": "error", "check": _check_rebound_timing,
     "parameters": ("P8",), "es": "La sobrecorrección se paga con una caída de 0,8 mg/dL/min"},
    {"id": "R8", "kind": "reference", "trajectory": "error", "check": _check_glucagon,
     "parameters": ("P5",), "es": "El glucagón moviliza poco sin glucógeno y bastante con él"},
    {"id": "R9", "kind": "reference", "trajectory": "error", "check": _check_infusion_alone,
     "applies": _severe_working, "parameters": ("P7",), "es": "Una infusión sin ampolla no corrige una hipoglicemia severa"},
)

# What no script of this battery observes, and why.
UNOBSERVED_ALWAYS = (
    "Lenguaje libre: la batería usa acciones estructuradas; el lector se comprueba aparte.",
    "Tratamientos prehospitalarios, restricción de terapias y otras capacidades pendientes (no existen en el motor).",
    "Lo que ocurre después del horizonte del encuentro: la batería mira hasta tres horas.",
)
UNOBSERVED_FAILED = (
    "Si la vía fallida se ve antes de usarla: hoy sólo se revela al dar glucosa en bolo por ella (DC2).",
    "El glucagón y el octreótido endovenosos por la vía fallida no se juegan aquí: llegan enteros, el alcance "
    "que dejó la decisión 8 (DC4).",
    "La vía intraósea como alternativa: el motor la trata como la vía fallida (DC3).",
)
UNOBSERVED_COMPOSITION = (
    "Variación de superficie: la composición conserva el paciente y el relato de su caso de origen.",
)


def run_configuration(configuration):
    """Every script and check of one configuration, with the classification of each result."""
    played = {script["id"]: observe(configuration["id"], script["turns"]) for script in scripts(configuration)}
    results = []
    for check in CHECKS:
        applies = check.get("applies")
        if applies is not None and not applies(configuration):
            continue
        outcome = check["check"](configuration, played)
        classification = None
        if outcome["status"] == "failed":
            classification = ("pending_clinical_decision" if check.get("on_failure")
                              else "technical_defect" if check["kind"] == "technical"
                              else "differs_from_reference")
        results.append({"id": check["id"], "kind": check["kind"], "trajectory": check["trajectory"],
                        "es": check["es"], "parameters": list(check.get("parameters", ())),
                        "decision": check.get("on_failure"), "classification": classification, **outcome})
    unobserved = list(UNOBSERVED_ALWAYS)
    if configuration["conditions"]["iv_access_failed"]:
        unobserved += UNOBSERVED_FAILED
    if configuration["origin"] != "bank":
        unobserved += UNOBSERVED_COMPOSITION
    technical = [r for r in results if r["kind"] == "technical"]
    defects = [r["id"] for r in results if r["classification"] == "technical_defect"]
    pending = sorted({r["decision"] for r in results if r["classification"] == "pending_clinical_decision"})
    return {"configuration_id": configuration["id"], "origin": configuration["origin"],
            "axes": dict(configuration["axes"]),
            "scripts": [{"id": s["id"], "kind": s["kind"], "es": s["es"]} for s in scripts(configuration)],
            "checks": results, "unobserved": unobserved,
            "tested": not defects,
            "summary": {"technical_passed": sum(r["status"] == "passed" for r in technical),
                        "technical_total": len(technical), "technical_defects": defects,
                        "pending_decisions": pending,
                        "reference_within": sum(r["kind"] == "reference" and r["status"] == "passed" for r in results),
                        "reference_total": sum(r["kind"] == "reference" and r["status"] != "not_observed"
                                               for r in results),
                        "reference_differs": [r["id"] for r in results
                                              if r["classification"] == "differs_from_reference"]}}


def run(configurations=None):
    """The whole battery. Only compatible configurations are played."""
    report = {"battery_version": BATTERY_VERSION, "catalog_version": catalog.VERSION,
              "glucose_rescue_version": glucose_rescue.VERSION, "configurations": []}
    for configuration in configurations or catalog.configurations():
        compatibility = catalog.compatibility(configuration)
        entry = {"configuration_id": configuration["id"], "compatibility": compatibility}
        if compatibility["compatible"]:
            entry.update(run_configuration(configuration))
        else:
            entry.update({"tested": False, "checks": [], "scripts": [], "unobserved": ["No se jugó: no es compatible."]})
        report["configurations"].append(entry)
    return report
