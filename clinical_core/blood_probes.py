"""P2I-2T: probes A-K of the shared haemorrhage state (read-only, synthetic, nothing approved).

    python -m clinical_core.blood_probes [--out <directory outside the repository>]
                                         [--golden-before <golden JSON of the model before P2I-2T>]
    python -m clinical_core.blood_probes --write <document> --json <probes JSON>

Shadow, offline and read-only. Every probe runs the core as it stands, from the GI 72f arrival the
golden uses (canonical anchors, every case parameter undeclared) with the canonical profile, whose
blood-state values are PROVISIONAL (SYNTHETIC/CANDIDATE, TBD); probe A switches plasma refill off.
Each probe reports, minute by minute at ``TIMES``, the shared blood state (shed volume, red-cell
content, circulating and plasma deviation, refill, crystalloid and red-cell contributions), the Hb
it derives, V, output, the delivery index, the extraction state and the effective deficit, read
with the canonical extraction reserve (1, TBD). The probes choose no value, change no default,
band, registry or rule, run no FD-LAC rule or filter and never compare with the family engine
except where the golden before / after is reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import calibration, gi_reference, lactate_slice
from .bands import BloodLoss
from .derived import (DEFAULT_PROFILE, blood_haemoglobin, derive, effective_delivery, oxygen_balance,
                      plasma_volume_deviation)
from .integration import run
from .legacy_adapter import PROVISIONAL_RED_CELL_UNIT_HB_G_DL
from .logistics import EndoscopicHemostasis

CASE = "gi_bleed_72f"
MINUTES = 240
TIMES = (0, 10, 20, 30, 60, 90, 120, 180, 240)
#: The acute loss of probes A and B: a synthetic 300 mL of whole blood over the first 10 minutes.
ACUTE_LOSS_ML, ACUTE_LOSS_MIN = 300.0, 10
NO_REFILL = {"plasma_refill_target_share": 0.0}
#: Probe K: haemostasis after two hours of untreated bleeding; probe D stops the bleeding fully then.
HEMOSTASIS_AT = 120


#: The declared whole-blood loss of probes A and B: the calibration harness's own (P2I-2U).
ScriptedBloodLoss = BloodLoss


def inputs() -> dict:
    """The probes' contributors: the GI module and the orders as the frozen family-engine path builds
    them for this case (lactate_slice L1-L3), retimed and resized for each probe."""
    items = {type(item).__name__: item for scenario in (lactate_slice.L1, lactate_slice.L2, lactate_slice.L3)
             for item in lactate_slice.scenario_inputs(CASE, scenario)}
    bleed, bag, unit = items["GIHaemorrhage"], items["Crystalloid"], items["PackedRedCells"]

    def saline(volume_ml):
        return replace(bag, id="probe-saline", start_minute=0, volume_ml=volume_ml, duration_min=20.0,
                       stop_minute=None, stopped_by=None, queued_ahead_ml=0.0)

    def red_cells(units, duration):
        return replace(unit, id="probe-prbc", start_minute=0, units=units, duration_min=duration, stop_minute=None,
                       queued_ahead_units=0.0)

    return {"bleed": bleed, "stopped": replace(bleed, fraction_after_hemostasis=0.0), "saline": saline,
            "red_cells": red_cells,
            "acute": ScriptedBloodLoss("acute", 0, ACUTE_LOSS_MIN, ACUTE_LOSS_ML / ACUTE_LOSS_MIN),
            "endoscopy": EndoscopicHemostasis("probe-endoscopy", HEMOSTASIS_AT)}


def probes() -> dict:
    """name -> (description, contributors, profile changes)."""
    items = inputs()
    bleed, endoscopy = items["bleed"], items["endoscopy"]
    return {
        "A": ("acute loss of 300 mL in 10 min, refill off", (items["acute"],), NO_REFILL),
        "B": ("acute loss of 300 mL in 10 min, with refill", (items["acute"],), {}),
        "C": ("ongoing GI bleeding (untreated) with refill", (bleed,), {}),
        "D": ("GI bleeding stopped at 120 min; refill continues", (items["stopped"], endoscopy), {}),
        "E": ("1 L crystalloid over 20 min, no bleeding", (items["saline"](1000.0),), {}),
        "F": ("2 L crystalloid over 20 min, no bleeding", (items["saline"](2000.0),), {}),
        "G": ("1 unit of packed red cells over 30 min, no bleeding", (items["red_cells"](1.0, 30.0),), {}),
        "H": ("2 units of packed red cells over 60 min, no bleeding", (items["red_cells"](2.0, 60.0),), {}),
        "I": ("2 units over 60 min during ongoing GI bleeding", (bleed, items["red_cells"](2.0, 60.0)), {}),
        "J": ("2 L crystalloid over 20 min during ongoing GI bleeding", (bleed, items["saline"](2000.0)), {}),
        "K": ("endoscopic haemostasis at 120 min after accumulated loss (10 % residual)", (bleed, endoscopy), {}),
    }


def _row(state, anchors, profile) -> dict:
    derived = derive(state, anchors, profile)
    delivery = effective_delivery(derived.delivery_rel, anchors)
    balance = oxygen_balance(delivery, state.aux.oxygen_demand, profile.oxygen_extraction_reserve)
    blood = state.blood
    return {"minute": state.minute, "shed_ml": blood.shed_ml, "red_cells": blood.red_cells,
            "circulating_ml": blood.volume_ml, "plasma_ml": plasma_volume_deviation(blood, anchors, profile),
            "refill_ml": blood.refill_ml, "crystalloid_ml": blood.crystalloid_in_ml - blood.crystalloid_out_ml,
            "transfused_ml": blood.transfused_ml, "transfused_red_cells": blood.transfused_red_cells,
            "hb": state.hb, "hb_from_blood": blood_haemoglobin(blood, anchors, profile), "V": state.V,
            "output_rel": derived.output_rel, "do2": delivery, "state": balance.state,
            "effective_deficit": balance.effective_deficit, "sbp": derived.sbp}


def anchors():
    return gi_reference.canonical_anchors(CASE)


def probe_rows(contributors, changes: dict, minutes: int = MINUTES) -> list:
    arrival, profile = anchors(), replace(DEFAULT_PROFILE, **changes)
    result = run(arrival, contributors, minutes, profile)
    return [_row(state, arrival, profile) for state in result.states]


def results() -> dict:
    out = {}
    for name, (description, contributors, changes) in probes().items():
        rows = probe_rows(contributors, changes)
        out[name] = {"description": description, "profile_changes": changes,
                     "points": {str(minute): rows[minute] for minute in TIMES},
                     "hb_lowest": min(row["hb"] for row in rows), "hb_highest": max(row["hb"] for row in rows),
                     "v_lowest": min(row["V"] for row in rows), "v_highest": max(row["V"] for row in rows)}
    return out


#: P2I-2T-7/8: (kappa, curve scale) pairs with the same ratio, and two arrival volumes.
GAUGE_PAIRS = ((1.0, DEFAULT_PROFILE.preload_curve_scale_ml), (2.0, 2 * DEFAULT_PROFILE.preload_curve_scale_ml),
               (0.5, 0.5 * DEFAULT_PROFILE.preload_curve_scale_ml))
ARRIVAL_VOLUMES = (3000.0, 4000.0, 5000.0)


def identifiability() -> dict:
    """Ongoing bleeding (probe C) under kappa / scale pairs of equal ratio, and under other arrival volumes."""
    bleed = (inputs()["bleed"],)
    pairs = {}
    for kappa, scale in GAUGE_PAIRS:
        rows = probe_rows(bleed, {"volume_preload_kappa": kappa, "preload_curve_scale_ml": scale}, 120)
        pairs[f"{kappa:g}/{scale:g}"] = {"V_120": rows[120]["V"], "output_120": rows[120]["output_rel"],
                                         "hb_120": rows[120]["hb"], "circulating_120": rows[120]["circulating_ml"]}
    volumes = {}
    for volume in ARRIVAL_VOLUMES:
        rows = probe_rows(bleed, {"arrival_circulating_volume_ml": volume}, 120)
        volumes[f"{volume:g}"] = {"V_120": rows[120]["V"], "output_120": rows[120]["output_rel"],
                                  "hb_120": rows[120]["hb"]}
    return {"pairs": pairs, "arrival_volumes": volumes}


def golden_before_after(before: dict, after: dict) -> dict:
    """Per golden run: the core's last sampled value before and after P2I-2T, and the engine's."""
    names = ("V_ml_eq", "hb_g_dl", "sbp", "hr", "lactate_mmol_l", "respiratory_rate", "crt_s")
    out = {}
    for key in sorted(after["scenarios"]):
        old, new = before["scenarios"][key], after["scenarios"][key]
        last = str(new["minutes"])
        row = {}
        for name in names:
            samples_old, samples_new = old["variables"][name]["samples"], new["variables"][name]["samples"]
            row[name] = {"legacy": samples_new[last][0], "before": samples_old[last][1], "after": samples_new[last][1],
                         "max_abs_diff_before": old["variables"][name]["max_abs_diff"],
                         "max_abs_diff_after": new["variables"][name]["max_abs_diff"]}
        out[key] = {"minutes": new["minutes"], "variables": row,
                    "mismatching_before": sorted(old["mismatching"]), "mismatching_after": sorted(new["mismatching"])}
    return out


def probes_digest() -> str:
    text = json.dumps({"sources": lactate_slice.slice_sources(), "freeze": calibration.frozen_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report(golden_before: Path | None = None) -> dict:
    from .shadow import GOLDEN
    data = {"probes_digest": probes_digest(), "case": CASE, "minutes": MINUTES, "times": list(TIMES),
            "profile": {name: getattr(DEFAULT_PROFILE, name) for name in (
                "arrival_circulating_volume_ml", "volume_preload_kappa", "plasma_refill_target_share",
                "plasma_refill_tau_min", "plasma_refill_capacity_ml", "preload_curve_scale_ml",
                "oxygen_extraction_reserve")},
            "red_cell_unit": {"volume_ml": inputs()["red_cells"](1.0, 30.0).volume_ml_per_unit,
                              "hb_g_dl": PROVISIONAL_RED_CELL_UNIT_HB_G_DL},
            "probes": results(), "identifiability": identifiability()}
    if golden_before is not None:
        before_text = golden_before.read_bytes()
        data["golden"] = {"before_sha256": hashlib.sha256(before_text).hexdigest(),
                          "after_sha256": hashlib.sha256(GOLDEN.read_bytes()).hexdigest(),
                          "runs": golden_before_after(json.loads(before_text), json.loads(GOLDEN.read_text("utf-8")))}
    return data


# Rendering (Spanish) ----------------------------------------------------------------------------

OPENING, CLOSING = "<!-- generado:estado-sanguineo -->\n", "<!-- /generado:estado-sanguineo -->"
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}
PROBES_ES = {
    "A": "pérdida aguda de 300 mL en 10 min, sin relleno",
    "B": "pérdida aguda de 300 mL en 10 min, con relleno",
    "C": "sangrado GI continuo (sin tratar) con relleno",
    "D": "sangrado GI detenido a los 120 min; el relleno continúa",
    "E": "1 L de cristaloide en 20 min, sin sangrado",
    "F": "2 L de cristaloide en 20 min, sin sangrado",
    "G": "1 unidad de GR en 30 min, sin sangrado",
    "H": "2 unidades de GR en 60 min, sin sangrado",
    "I": "2 unidades en 60 min durante sangrado GI continuo",
    "J": "2 L de cristaloide en 20 min durante sangrado GI continuo",
    "K": "hemostasia endoscópica a los 120 min tras pérdida acumulada (residual 10 %)",
}
GOLDEN_ES = {"V_ml_eq": "V", "hb_g_dl": "Hb", "sbp": "PAS", "hr": "FC", "lactate_mmol_l": "lactato",
             "respiratory_rate": "FR", "crt_s": "llenado capilar"}
VARIABLES_ES = {**GOLDEN_ES, "dbp": "PAD", "map": "PAM", "consciousness_level": "conciencia", "spo2": "SpO2"}


def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return STATES_ES.get(value, value)
    return lactate_slice._n(value, digits)


def render(data: dict) -> str:
    data = json.loads(json.dumps(data, sort_keys=True, default=str))
    profile, unit = data["profile"], data["red_cell_unit"]
    lines = []
    add = lines.append
    add(f"Generado desde las sondas `{data['probes_digest']}` (`python -m clinical_core.blood_probes`). Llegada GI "
        f"`{data['case']}` del golden (anclas canónicas, parámetros de caso sin declarar) y perfil canónico: volumen "
        f"circulante de llegada {_n(profile['arrival_circulating_volume_ml'], 0)} mL-eq, κ "
        f"{_n(profile['volume_preload_kappa'], 1)}, escala de la curva {_n(profile['preload_curve_scale_ml'], 0)} mL-eq, "
        f"relleno: meta {_n(100 * profile['plasma_refill_target_share'], 0)} % de lo perdido, τ "
        f"{_n(profile['plasma_refill_tau_min'], 0)} min, capacidad {_n(profile['plasma_refill_capacity_ml'], 0)} mL-eq; "
        f"unidad de GR {_n(unit['volume_ml'], 0)} mL-eq a {_n(unit['hb_g_dl'], 0)} g/dL; reserva de extracción "
        f"{_n(profile['oxygen_extraction_reserve'], 0)} (canónica). **Todos son valores PROVISIONALES "
        "(SYNTHETIC/CANDIDATE, TBD); ninguno está aprobado.** Los volúmenes son mL-eq de volumen circulante normalizado, "
        "no litros medidos; los GR, en unidades del contenido de llegada (llegada = 1).\n")
    add("### 4.1 Sondas A–K\n")
    add("Columnas: perdido (mL-eq) · GR (contenido) · desviación circulante C · desviación plasmática · relleno · "
        "cristaloide neto · GR transfundidos (mL-eq) · Hb (g/dL) · V · gasto relativo · índice de DO2 · estado de "
        "extracción · déficit efectivo.\n")
    for name in sorted(data["probes"]):
        probe = data["probes"][name]
        add(f"**{name} · {PROBES_ES[name]}.** Hb mínima {_n(probe['hb_lowest'])}, máxima {_n(probe['hb_highest'])}; "
            f"V mínima {_n(probe['v_lowest'], 0)}, máxima {_n(probe['v_highest'], 0)}.\n")
        add("| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | "
            "déficit |")
        add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for minute in data["times"]:
            row = probe["points"][str(minute)]
            add(f"| {minute} | {_n(row['shed_ml'], 0)} | {_n(row['red_cells'], 3)} | {_n(row['circulating_ml'], 0)} | "
                f"{_n(row['plasma_ml'], 0)} | {_n(row['refill_ml'], 0)} | {_n(row['crystalloid_ml'], 0)} | "
                f"{_n(row['transfused_ml'], 0)} | {_n(row['hb'])} | {_n(row['V'], 0)} | {_n(row['output_rel'])} | "
                f"{_n(row['do2'])} | {_n(row['state'])} | {_n(row['effective_deficit'], 3)} |")
        add("")
    gauge = data["identifiability"]
    add("### 4.2 Identificabilidad de κ y λ, y normalización del volumen\n")
    add("| κ / escala λ (mL-eq) | V a 120 min | C a 120 min | gasto a 120 min | Hb a 120 min |")
    add("|---|---|---|---|---|")
    for key, row in gauge["pairs"].items():
        add(f"| {key} | {_n(row['V_120'], 0)} | {_n(row['circulating_120'], 0)} | {_n(row['output_120'], 4)} | "
            f"{_n(row['hb_120'], 3)} |")
    add("")
    add("| Volumen circulante de llegada (mL-eq) | V a 120 min | gasto a 120 min | Hb a 120 min |")
    add("|---|---|---|---|")
    for key, row in gauge["arrival_volumes"].items():
        add(f"| {key} | {_n(row['V_120'], 0)} | {_n(row['output_120'], 4)} | {_n(row['hb_120'], 3)} |")
    add("")
    if "golden" in data:
        golden = data["golden"]
        add("### 4.3 Golden GI: antes / después\n")
        add(f"Antes: `{golden['before_sha256']}`; después: `{golden['after_sha256']}` (sha256 de "
            "`clinical_core/golden/gi_bleed_shadow.json`). Cada celda: motor heredado · núcleo antes → núcleo después, "
            "en el último minuto de la corrida.\n")
        add("| Corrida | min | " + " | ".join(GOLDEN_ES.values()) + " | Variables distintas del heredado: antes → después |")
        add("|---|---|" + "---|" * len(GOLDEN_ES) + "---|")
        for key, run_ in golden["runs"].items():
            cells = []
            for name in GOLDEN_ES:
                value = run_["variables"][name]
                digits = 0 if name == "V_ml_eq" else 1 if name in ("sbp", "hr", "respiratory_rate") else 2
                cells.append(f"{_n(value['legacy'], digits)} · {_n(value['before'], digits)} → {_n(value['after'], digits)}")
            before = set(run_["mismatching_before"])
            after = set(run_["mismatching_after"])
            change = (", ".join(f"+{VARIABLES_ES.get(name, name)}" for name in sorted(after - before))
                      + (", " if after - before and before - after else "")
                      + ", ".join(f"−{VARIABLES_ES.get(name, name)}" for name in sorted(before - after))) or "sin cambio"
            add(f"| {key} | {run_['minutes']} | " + " | ".join(cells) + f" | {change} |")
        add("")
    return "\n".join(lines)


def apply(document: str, block: str) -> str:
    start = document.index(OPENING) + len(OPENING)
    end = document.index(CLOSING)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--golden-before", type=Path)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    if args.write:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        args.write.write_text(apply(args.write.read_text(encoding="utf-8"), render(data)), encoding="utf-8")
        return 0
    text = json.dumps(report(args.golden_before), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "blood_probes.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
