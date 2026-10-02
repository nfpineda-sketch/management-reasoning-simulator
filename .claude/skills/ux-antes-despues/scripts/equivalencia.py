#!/usr/bin/env python3
"""ux-antes-despues · equivalencia del registro con AppTest.

  equivalencia.py correr   --arbol DIR --salida SALIDA.json [--perfil PERFIL.json] [--semilla N]
  equivalencia.py comparar ANTES.json DESPUES.json [--normalizar RUTA ...] [--informe INFORME.json]

No depende del directorio actual; el perfil por defecto es perfil_encuentro_clinico.json, junto a este script.

'correr' ejecuta los pasos del perfil en la página real (AppTest) de UN árbol, en este proceso.
  - Tras cada paso vuelca los eventos, el Management Trace, el estado clínico, lo pendiente y el texto visible.
  - Al cierre vuelca el contenido clínico del registro guardado: los campos de REGISTRO_CLINICO, sin los
    metadatos de la fila de la base.
  - Usa una base SQLite temporal propia, borrada al terminar, y una cuenta sintética creada con la API pública
    del store.
  - Aislamiento (aislamiento.py): entorno sin claves ni proxies, HOME temporal, red saliente bloqueada en el
    proceso con autoprueba; revisión de imágenes activa.
  - Reproducibilidad acotada y reversible: durante la corrida, sólo curriculum_runtime ve un `secrets` cuyo
    `randbelow` devuelve la semilla. El resto de la app (tokens de sesión, contraseñas) usa el módulo real. El
    desafío se fija con un stub de prueba y ambos se restauran al terminar.
'comparar' informa toda diferencia de los pasos y del registro, con su ruta JSON.
  - Sólo normaliza las rutas enumeradas en NORMALIZAR_POR_DEFECTO y las que se pasen con --normalizar. La lista
    se amplía sólo con rutas calibradas: correr dos veces el MISMO árbol y comparar.
  - El informe lista cada ruta normalizada con su conteo.
  - Avisa si las corridas usaron semillas distintas.
  - Marca además los hechos clínicos visibles nuevos en DESPUÉS (minutos, cifras con unidad) que ANTES no
    mostraba en el mismo paso, para revisarlos a mano.
"""
import argparse
import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import aislamiento

PERFIL = Path(__file__).resolve().parent / "perfil_encuentro_clinico.json"
NORMALIZAR_POR_DEFECTO = (
    "pasos[*].management_trace[*].code_version",
    "registro.payload.session.encounter_closed_trace[*].code_version",
    "registro.encounter.evaluation_basis.frozen_at",
)
COMPARADOS = ("pasos", "registro")
REGISTRO_CLINICO = ("challenge_id", "status", "is_sandbox", "encounter", "payload")
ESTADO = ("sim_time", "observable", "treatments", "diagnostics", "diagnostic_history", "family_state", "hidden",
          "pending_investigations")
PENDIENTES = ("pending_reasoning", "pending_action", "pending_bundle", "close_pending", "encounter_ended")
VISIBLE = ("title", "header", "subheader", "markdown", "caption", "info", "warning", "error", "success")
HECHO = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:min|mg|mcg|g|mL|L/min|L|mmHg|mm Hg|%|/min|ng/L|mmol/L|s|kg|cm)\b"
                   r"|(?:expected at|al minuto|a los)\s+\d+", re.I)


@contextlib.contextmanager
def _acotado(modulo, nombre, valor):
    original = getattr(modulo, nombre)
    setattr(modulo, nombre, valor)
    try:
        yield
    finally:
        setattr(modulo, nombre, original)


def _widget(lista, etiqueta):
    return next(w for w in lista if w.label == etiqueta)


def _boton(at, etiquetas):
    for etiqueta in ([etiquetas] if isinstance(etiquetas, str) else etiquetas):
        for b in at.button:
            if b.label == etiqueta:
                return b
    raise LookupError(f"Ningún botón {etiquetas} en este paso")


def _paso(at, paso, et):
    accion = paso["accion"]
    if paso.get("modo"):
        _widget(at.radio, et["radio_modos"]).set_value(paso["modo"]).run()
    if accion == "comenzar":
        _boton(at, et["comenzar"]).click().run()
    elif accion == "enviar":
        _widget(at.text_area, et["cuadro"]).set_value(paso["texto"])
        _boton(at, et["enviar"]).click().run()
    elif accion == "preguntar":
        _widget(at.radio, et["radio_modos"]).set_value("Talk").run()
        _widget(at.text_input, et["preguntar_campo"]).set_value(paso["texto"])
        _boton(at, et["preguntar_boton"]).click().run()
    elif accion == "examinar":
        _widget(at.radio, et["radio_modos"]).set_value("Examine").run()
        _widget(at.selectbox, et["examinar_campo"]).set_value(paso["region"]).run()
        _boton(at, et["examinar_boton"]).click().run()
    elif accion == "campos":
        for etiqueta, valor in paso["valores"].items():
            _widget(at.text_area, etiqueta).set_value(valor)
        _boton(at, paso["boton"]).click().run()
    elif accion == "boton":
        _boton(at, paso["etiqueta"]).click().run()
    elif accion == "cerrar":
        _boton(at, et["cerrar"]).click().run()
        if any(b.label in et["terminar"] for b in at.button):
            _boton(at, et["terminar"]).click().run()
    else:
        raise ValueError(f"Acción desconocida: {accion}")


def correr(a):
    arbol = Path(a.arbol).resolve()
    destino = Path(a.salida).resolve()                     # antes de cambiar de directorio
    perfil = json.loads(Path(a.perfil).resolve().read_text(encoding="utf-8"))
    trabajo = Path(tempfile.mkdtemp(prefix="equivalencia-"))
    try:
        red = trabajo / "red.jsonl"
        aislamiento.instalar_guardia(red)
        prueba = aislamiento.autoprueba()
        if not aislamiento.autoprueba_ok(prueba):
            sys.exit(f"La autoprueba de red falló; no se corre: {prueba}")
        url = f"sqlite:///{trabajo}/cuentas.sqlite3"
        os.environ.clear()
        os.environ.update(aislamiento.entorno_limpio(trabajo, {
            "MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url, "MRS_ALLOW_LOCAL_SQLITE": "true",
            "MRS_OFFLINE_CASES": "1", "MRS_DEFAULT_VARIANT": perfil["variante"], "MRS_IMAGE_REQUIRE_REVIEW": "on"}))
        sys.path.insert(0, str(arbol))
        os.chdir(arbol)
        import secrets
        from streamlit.testing.v1 import AppTest
        from account_store import AccountStore, hash_password
        from resident_profile import ProfileStore
        import curriculum_runtime

        store = AccountStore(url, allow_sqlite=True)
        clave = secrets.token_urlsafe(16)
        store.bootstrap_admin("eq_admin", hash_password(clave))
        admin = store.authenticate("eq_admin", clave)
        token = store.register("eq_residente", secrets.token_urlsafe(16), store.create_invite(admin, "resident", 2))
        ProfileStore(store).decline(token)

        desafio = {"challenge_id": perfil["desafio"], "reason": "equivalencia", "assignment_seed": 17,
                   "competence_decision": "Not assessed automatically"}
        semilla = a.semilla if a.semilla is not None else perfil["semilla"]
        pasos = []
        with _acotado(curriculum_runtime, "secrets", aislamiento.SecretsConSemilla(secrets, semilla)), \
                _acotado(curriculum_runtime, "assign_challenge", lambda *x, **k: dict(desafio)):
            at = AppTest.from_file(str(arbol / "app.py"), default_timeout=180)
            at.session_state["_account_token"] = token
            at.run()
            for paso in perfil["pasos"]:
                _paso(at, paso, perfil["etiquetas"])
                if at.exception:
                    raise RuntimeError(f'{paso["id"]}: {at.exception}')
                s = at.session_state
                estado = s["state"] if "state" in s else {}
                pasos.append({
                    "paso": paso["id"],
                    "events": s["events"] if "events" in s else [],
                    "management_trace": s["management_trace"] if "management_trace" in s else [],
                    "estado": {k: estado.get(k) for k in ESTADO},
                    "pendientes": {k: (s[k] if k in s else None) for k in PENDIENTES},
                    "visible": [str(e.value) for tipo in VISIBLE for e in at.get(tipo)],
                })
        [intento] = store.list_attempts(token)
        guardado = store.get_attempt(token, intento["id"])
        intentos = aislamiento.resumen_log(red)["intentos_bloqueados"]
        salida = {"arbol": str(arbol), "semilla": semilla,
                  "aislamiento": {"autoprueba": prueba, "intentos_bloqueados": len(intentos),
                                  "destinos": sorted({i["destino"] for i in intentos})},
                  "pasos": pasos, "registro": {k: guardado.get(k) for k in REGISTRO_CLINICO}}
        destino.write_text(json.dumps(salida, indent=1, sort_keys=True, default=str, ensure_ascii=False))
        print("pasos:", len(pasos), "· eventos:", len(pasos[-1]["events"]), "· trace:",
              len(pasos[-1]["management_trace"]), "· red: autoprueba bloqueada, intentos bloqueados", len(intentos))
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)


def _patron(ruta):
    return re.compile("^" + re.escape(ruta).replace(r"\[\*\]", r"\[\d+\]") + "$")


def _diferencias(x, y, ruta, salida):
    if type(x) != type(y):
        salida.append((ruta, x, y))
    elif isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y:
                salida.append((f"{ruta}.{k}", x.get(k, "<ausente>"), y.get(k, "<ausente>")))
            else:
                _diferencias(x[k], y[k], f"{ruta}.{k}", salida)
    elif isinstance(x, list):
        if len(x) != len(y):
            salida.append((f"{ruta}.len", len(x), len(y)))
        for i, (p, q) in enumerate(zip(x, y)):
            _diferencias(p, q, f"{ruta}[{i}]", salida)
    elif x != y:
        salida.append((ruta, x, y))


def comparar(a):
    antes = json.loads(Path(a.antes).read_text(encoding="utf-8"))
    despues = json.loads(Path(a.despues).read_text(encoding="utf-8"))
    rutas = list(NORMALIZAR_POR_DEFECTO) + list(a.normalizar or [])
    patrones = [(r, _patron(r)) for r in rutas]
    diferencias, normalizadas = [], {r: 0 for r in rutas}

    def comparable(d):
        d = {k: d[k] for k in COMPARADOS}
        return {**d, "pasos": [{k: v for k, v in p.items() if k != "visible"} for p in d["pasos"]]}
    crudas = []
    _diferencias(comparable(antes), comparable(despues), "", crudas)
    for ruta, x, y in crudas:
        ruta = ruta.lstrip(".")
        regla = next((r for r, p in patrones if p.match(ruta)), None)
        if regla:
            normalizadas[regla] += 1
        else:
            diferencias.append({"ruta": ruta, "antes": str(x)[:200], "despues": str(y)[:200]})
    nuevos = []
    for p, q in zip(antes["pasos"], despues["pasos"]):
        vistos = set(HECHO.findall(" ".join(p["visible"])))
        for hecho in sorted(set(HECHO.findall(" ".join(q["visible"]))) - vistos):
            nuevos.append({"paso": q["paso"], "hecho_visible_nuevo": hecho})
    avisos = []
    if antes.get("semilla") != despues.get("semilla"):
        avisos.append(f"semillas distintas ({antes.get('semilla')} y {despues.get('semilla')}): "
                      "las diferencias pueden venir del azar del caso, no del código")
    informe = {"identico": not diferencias, "diferencias": diferencias, "normalizadas": normalizadas,
               "hechos_visibles_nuevos_para_revisar": nuevos, "avisos": avisos,
               "corridas": {lado: {"arbol": d.get("arbol"), "semilla": d.get("semilla"),
                                   "aislamiento": d.get("aislamiento")}
                            for lado, d in (("antes", antes), ("despues", despues))}}
    if a.informe:
        Path(a.informe).write_text(json.dumps(informe, indent=1, ensure_ascii=False))
    print("IDÉNTICO" if not diferencias else f"{len(diferencias)} DIFERENCIAS (ver el informe)")
    for aviso in avisos:
        print("  AVISO:", aviso)
    for regla, n in normalizadas.items():
        print(f"  normalizada {regla}: {n}")
    print(f"  hechos visibles nuevos para revisar a mano: {len(nuevos)}")
    sys.exit(0 if not diferencias else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("correr")
    c.add_argument("--arbol", required=True)
    c.add_argument("--perfil", default=str(PERFIL))
    c.add_argument("--salida", required=True)
    c.add_argument("--semilla", type=int)
    k = sub.add_parser("comparar")
    k.add_argument("antes")
    k.add_argument("despues")
    k.add_argument("--normalizar", nargs="*")
    k.add_argument("--informe")
    a = ap.parse_args()
    (correr if a.orden == "correr" else comparar)(a)


if __name__ == "__main__":
    main()
