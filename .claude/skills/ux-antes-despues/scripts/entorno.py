#!/usr/bin/env python3
"""ux-antes-despues · entornos ANTES/DESPUÉS aislados y sintéticos.

  entorno.py preparar --dir RUN --base REF --candidato (REF|TRABAJO) [--repo R]
                      [--tamanos 1440x900,1366x768,1000x768] [--anio-residente 2]
  entorno.py iniciar  --dir RUN [--perfil PERFIL.json] [--variante V] [--semilla N] [--idioma en|es]
                      [--puerto-antes 8601] [--puerto-despues 8603] [--sin-revision-imagenes "MOTIVO"]
  entorno.py detener  --dir RUN
  entorno.py limpiar  --dir RUN

No depende del directorio actual. Por defecto, el repositorio es el que contiene esta skill y el perfil es
perfil_encuentro_clinico.json, junto a este script.

Crea sólo RUN, fuera del repositorio, que no debe existir o debe estar vacío:
  - RUN/antes y RUN/despues: los dos árboles. Un commit se copia con `git archive`; el árbol de trabajo, con
    `git ls-files -co --exclude-standard`. Ninguno lleva .streamlit/secrets.toml ni otros archivos ignorados.
  - RUN/antes.sqlite3 y RUN/despues.sqlite3: bases sintéticas, creadas con AccountStore y ProfileStore de su
    propio árbol. Nunca datos reales ni la base de un despliegue.
  - RUN/credenciales.json: cuentas sintéticas de esta corrida, con claves aleatorias; por tamaño, una cuenta para
    las capturas y otra para el comportamiento.
  - RUN/manifiesto.json, RUN/pids.json, RUN/home-*, los logs y los registros de red.

'iniciar' corre cada servidor bajo aislamiento.py:
  - entorno desde una lista permitida, sin claves ni proxies, con HOME dentro de RUN;
  - red saliente bloqueada en el proceso, con autoprueba;
  - escucha sólo en 127.0.0.1;
  - revisión de imágenes activa, como en el piloto;
  - semilla del perfil, la misma en los dos lados.
  Se detiene si la autoprueba falla o si el entorno del proceso muestra una variable sospechosa. Sólo
  '--sin-revision-imagenes MOTIVO' apaga la revisión, únicamente en este entorno temporal, y el motivo queda en el
  manifiesto.
'detener' termina sólo los grupos de procesos que registró 'iniciar', tras comprobar que siguen corriendo dentro
de RUN, e informa los intentos de red bloqueados.
'limpiar' borra RUN sólo si contiene el marcador de esta herramienta con el identificador de la corrida y no
quedan procesos vivos.
"""
import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import aislamiento

AQUI = Path(__file__).resolve().parent
PERFIL = AQUI / "perfil_encuentro_clinico.json"
LANZADOR = AQUI / "aislamiento.py"
MARCADOR = ".ux-antes-despues"
LADOS = ("antes", "despues")
USOS = ("capturas", "comportamiento")

CREAR_CUENTAS = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from account_store import AccountStore, hash_password
from resident_profile import ProfileStore
plan = json.loads(sys.argv[3])
s = AccountStore("sqlite:///" + sys.argv[2], allow_sqlite=True)
s.bootstrap_admin(plan["admin"]["usuario"], hash_password(plan["admin"]["clave"]))
admin = s.authenticate(plan["admin"]["usuario"], plan["admin"]["clave"])
for cuenta in plan["residentes"]:
    token = s.register(cuenta["usuario"], cuenta["clave"], s.create_invite(admin, "resident", plan["anio"]))
    ProfileStore(s).decline(token)
print("cuentas:", len(plan["residentes"]))
"""


def repo_por_defecto():
    """El repositorio que contiene esta skill, sea cual sea el directorio actual."""
    return Path(subprocess.run(["git", "-C", str(AQUI), "rev-parse", "--show-toplevel"], check=True,
                               capture_output=True, text=True).stdout.strip())


def _json(path, data=None):
    path = Path(path)
    if data is None:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def _run_dir(texto, crear=False, repo=None):
    run = Path(texto).resolve()
    if len(run.parts) < 4 or run == Path.home().resolve():
        sys.exit(f"Directorio de corrida demasiado general: {run}")
    if repo is not None and run.is_relative_to(repo):
        sys.exit(f"La corrida debe quedar fuera del repositorio ({repo}): {run}")
    if crear:
        if run.exists() and any(run.iterdir()):
            sys.exit(f"{run} ya existe y no está vacío.")
        run.mkdir(parents=True, exist_ok=True)
    elif not (run / MARCADOR).exists():
        sys.exit(f"{run} no fue creado por esta herramienta (falta {MARCADOR}).")
    return run


def _copiar(repo, ref, destino):
    repo, destino = Path(repo).resolve(), Path(destino).resolve()
    destino.mkdir()
    tar = destino.parent / f".{destino.name}.tar"
    if ref == "TRABAJO":
        lista = subprocess.run(["git", "-C", str(repo), "ls-files", "-co", "--exclude-standard", "-z"],
                               check=True, capture_output=True).stdout
        # Un archivo versionado que se borró en el árbol de trabajo no se copia: el candidato no lo tiene.
        lista = b"\0".join(r for r in lista.split(b"\0") if r and os.path.lexists(Path(repo, os.fsdecode(r))))
        subprocess.run(["tar", "--null", "-cf", str(tar), "-T", "-"], input=lista, cwd=repo, check=True)
        commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True,
                                text=True).stdout.strip() + "+árbol de trabajo"
    else:
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tar), ref], check=True)
        commit = subprocess.run(["git", "-C", str(repo), "rev-parse", ref], check=True, capture_output=True,
                                text=True).stdout.strip()
    subprocess.run(["tar", "-xf", str(tar)], cwd=destino, check=True)
    tar.unlink()
    return commit


def preparar(a):
    repo = Path(a.repo).resolve() if a.repo else repo_por_defecto()
    run = _run_dir(a.dir, crear=True, repo=repo)
    corrida = secrets.token_hex(8)
    (run / MARCADOR).write_text(corrida)
    tamanos = [t.strip() for t in a.tamanos.split(",") if t.strip()]
    credenciales = {"admin": {"usuario": "ux_admin", "clave": secrets.token_urlsafe(16)},
                    "anio": a.anio_residente,
                    "residentes": [{"usuario": f"ux_{uso[:4]}_{t.replace('x', '_')}",
                                    "clave": secrets.token_urlsafe(16), "tamano": t, "uso": uso}
                                   for t in tamanos for uso in USOS]}
    manifiesto = {"corrida": corrida, "repo": str(repo), "creado": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "tamanos": tamanos, "lados": {}}
    for lado, ref in zip(LADOS, (a.base, a.candidato)):
        commit = _copiar(repo, ref, run / lado)
        base = run / f"{lado}.sqlite3"
        home = run / f"home-{lado}"
        home.mkdir()
        subprocess.run([sys.executable, str(LANZADOR), "--log", str(run / f"red-{lado}.jsonl"),
                        "-c", CREAR_CUENTAS, str(run / lado), str(base), json.dumps(credenciales)],
                       check=True, cwd=run / lado, env=aislamiento.entorno_limpio(home))
        manifiesto["lados"][lado] = {"ref": ref, "commit": commit, "base": str(base), "home": str(home)}
    _json(run / "credenciales.json", credenciales)
    os.chmod(run / "credenciales.json", 0o600)
    _json(run / "manifiesto.json", manifiesto)
    print(json.dumps(manifiesto, indent=1, ensure_ascii=False))


def _libre(puerto):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def _responde(url, segundos=90):
    abrir = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # el servidor local, sin proxy
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            with abrir.open(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def _variables(pid):
    """Los nombres (nunca los valores) del entorno con que corre el proceso."""
    crudo = Path(f"/proc/{pid}/environ").read_bytes()
    return sorted(e.split(b"=", 1)[0].decode(errors="replace") for e in crudo.split(b"\0") if e)


def iniciar(a):
    run = _run_dir(a.dir)
    manifiesto = _json(run / "manifiesto.json")
    pids = _json(run / "pids.json") or {}
    if any(_vivo(pid) for pid in pids.values()):
        sys.exit("Ya hay servidores de esta corrida en marcha; usa 'detener' primero.")
    perfil = json.loads(Path(a.perfil).resolve().read_text(encoding="utf-8"))
    variante = a.variante or perfil["variante"]
    semilla = a.semilla if a.semilla is not None else perfil["semilla"]
    manifiesto["servidor"] = {"variante": variante, "semilla": semilla, "idioma": a.idioma,
                              "revision_imagenes": "off" if a.sin_revision_imagenes else "on",
                              "motivo_excepcion": a.sin_revision_imagenes}
    if a.sin_revision_imagenes:
        print("AVISO: revisión de imágenes desactivada sólo en este entorno sintético temporal. Motivo:",
              a.sin_revision_imagenes)
    ocupados = [puerto for puerto in (a.puerto_antes, a.puerto_despues) if not _libre(puerto)]
    if ocupados or a.puerto_antes == a.puerto_despues:
        sys.exit(f"Puertos no disponibles: {ocupados or [a.puerto_antes]}. No se inició ningún servidor.")
    pids = {}
    for lado, puerto in zip(LADOS, (a.puerto_antes, a.puerto_despues)):
        datos = manifiesto["lados"][lado]
        extra = {"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": "sqlite:///" + datos["base"],
                 "MRS_ALLOW_LOCAL_SQLITE": "true", "MRS_OFFLINE_CASES": "1", "MRS_DEFAULT_VARIANT": variante,
                 "MRS_IMAGE_REQUIRE_REVIEW": "off" if a.sin_revision_imagenes else "on"}
        if a.idioma:
            extra["MRS_LANGUAGE"] = a.idioma
        red = run / f"red-{lado}.jsonl"
        log = open(run / f"servidor-{lado}.log", "w")
        proceso = subprocess.Popen(
            [sys.executable, str(LANZADOR), "--log", str(red), "--semilla", str(semilla),
             "-m", "streamlit", "run", "app.py", "--server.port", str(puerto), "--server.address", "127.0.0.1",
             "--server.headless", "true", "--server.fileWatcherType", "none",
             "--browser.gatherUsageStats", "false"],
            cwd=run / lado, env=aislamiento.entorno_limpio(datos["home"], extra), stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
        pids[lado] = proceso.pid
        datos["url"] = f"http://127.0.0.1:{puerto}"
        datos["red"] = str(red)
    _json(run / "pids.json", pids)
    problemas = []
    for lado in LADOS:
        datos, pid = manifiesto["lados"][lado], pids[lado]
        listo = _responde(datos["url"])
        prueba = aislamiento.resumen_log(datos["red"])["autoprueba_por_proceso"].get(pid, {})
        nombres = _variables(pid) if _vivo(pid) else []
        datos["aislamiento"] = {"autoprueba": prueba, "variables": nombres,
                                "sospechosas": aislamiento.sospechosas(nombres)}
        print(f"{lado} {datos['url']}: {'listo' if listo else 'NO RESPONDE (ver el log)'} · autoprueba "
              f"{'bloqueada' if aislamiento.autoprueba_ok(prueba) else 'FALLÓ'} · variables {', '.join(nombres)}")
        if not listo:
            problemas.append(f"{lado}: no responde")
        if not aislamiento.autoprueba_ok(prueba):
            problemas.append(f"{lado}: autoprueba de red {prueba or 'ausente'}")
        if datos["aislamiento"]["sospechosas"]:
            problemas.append(f"{lado}: variables sospechosas {datos['aislamiento']['sospechosas']}")
    _json(run / "manifiesto.json", manifiesto)
    if problemas:
        detener(a)
        sys.exit("No se usa esta corrida: " + "; ".join(problemas))


def _vivo(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _es_de_la_corrida(pid, run):
    try:
        return Path(f"/proc/{pid}/cwd").resolve().is_relative_to(run) and \
            b"streamlit" in Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False


def detener(a):
    run = _run_dir(a.dir)
    pids = _json(run / "pids.json") or {}
    for lado, pid in list(pids.items()):
        if not _vivo(pid):
            pids.pop(lado)
            continue
        if not _es_de_la_corrida(pid, run):
            print(f"{lado}: el PID {pid} ya no es un servidor de esta corrida; no se toca.")
            pids.pop(lado)
            continue
        os.killpg(pid, signal.SIGTERM)
        for _ in range(20):
            if not _vivo(pid):
                break
            time.sleep(0.5)
        if _vivo(pid):
            os.killpg(pid, signal.SIGKILL)
        pids.pop(lado)
        print(f"{lado}: detenido")
    _json(run / "pids.json", pids)
    for lado in LADOS:
        intentos = aislamiento.resumen_log(run / f"red-{lado}.jsonl")["intentos_bloqueados"]
        print(f"{lado}: intentos de red bloqueados fuera de la autoprueba: {len(intentos)}")
        for intento in intentos:
            print(f"  {intento['tipo']} {intento['destino']} ← {(intento.get('origen') or ['?'])[-1]}")


def limpiar(a):
    run = _run_dir(a.dir)
    manifiesto = _json(run / "manifiesto.json") or {}
    if (run / MARCADOR).read_text().strip() != manifiesto.get("corrida"):
        sys.exit("El marcador no coincide con el manifiesto: no se borra nada.")
    if any(_vivo(pid) and _es_de_la_corrida(pid, run) for pid in (_json(run / "pids.json") or {}).values()):
        sys.exit("Quedan servidores de esta corrida en marcha: usa 'detener' primero.")
    shutil.rmtree(run)
    print("borrado", run)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--dir", required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--candidato", required=True)
    p.add_argument("--repo")
    p.add_argument("--tamanos", default="1440x900,1366x768,1000x768")
    p.add_argument("--anio-residente", type=int, default=2)
    p = sub.add_parser("iniciar")
    p.add_argument("--dir", required=True)
    p.add_argument("--perfil", default=str(PERFIL))
    p.add_argument("--variante")
    p.add_argument("--semilla", type=int)
    p.add_argument("--puerto-antes", type=int, default=8601)
    p.add_argument("--puerto-despues", type=int, default=8603)
    p.add_argument("--idioma", choices=("en", "es"))
    p.add_argument("--sin-revision-imagenes", metavar="MOTIVO")
    for orden in ("detener", "limpiar"):
        sub.add_parser(orden).add_argument("--dir", required=True)
    a = ap.parse_args()
    {"preparar": preparar, "iniciar": iniciar, "detener": detener, "limpiar": limpiar}[a.orden](a)


if __name__ == "__main__":
    main()
