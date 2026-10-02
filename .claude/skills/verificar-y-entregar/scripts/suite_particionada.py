#!/usr/bin/env python3
"""verificar-y-entregar · suite completa en particiones, sobre un candidato fijo.

Uso:
  suite_particionada.py --salida DIR [--particiones N] [--patron 'test_*.py'] [--repo R]
                        [--timeout SEGUNDOS] [--pytest-extra '...']

Qué hace:
  1. Registra el candidato: rama, HEAD y una huella del árbol de trabajo (diff contra HEAD, cambios
     staged incluidos, más el contenido de los archivos nuevos no ignorados).
  2. Reparte los archivos de prueba en N particiones equilibradas por tamaño (N por defecto: núcleos
     disponibles, hasta 4).
  3. Corre las N en paralelo con `pytest -q -p no:cacheprovider --junitxml=…`; deja log, XML y código de
     salida por partición.
  4. Vuelve a calcular la huella. Si cambió, la corrida queda INVÁLIDA: el candidato cambió mientras se
     verificaba.
  5. Resume desde los JUnit XML: pruebas, fallas, errores, omitidas y xfail, con el identificador de cada
     falla o error. Nunca cuenta caracteres del progreso.

No depende del directorio actual: por defecto verifica el repositorio que contiene esta skill.
Crea sólo DIR, que no debe existir o debe estar vacío. No borra ni modifica nada fuera de DIR.
Dependencias: Python 3, git y pytest, ya instalados en el proyecto.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


AQUI = Path(__file__).resolve().parent


def git(repo, *args, binario=False):
    salida = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout
    return salida if binario else salida.decode().strip()


def huella(repo):
    """Commit más los cambios staged y unstaged y el contenido de los archivos nuevos no ignorados."""
    h = hashlib.sha256()
    h.update(git(repo, "rev-parse", "HEAD").encode())
    h.update(git(repo, "diff", "HEAD", "--binary", binario=True))
    for nombre in sorted(git(repo, "ls-files", "--others", "--exclude-standard").splitlines()):
        ruta = Path(repo, nombre)
        h.update(nombre.encode())
        if ruta.is_file():
            h.update(ruta.read_bytes())
    return h.hexdigest()


def particionar(archivos, n):
    """Mayor primero, cada archivo a la partición más liviana: tamaño en bytes como estimación."""
    grupos = [[] for _ in range(n)]
    pesos = [0] * n
    for archivo in sorted(archivos, key=lambda a: a.stat().st_size, reverse=True):
        i = pesos.index(min(pesos))
        grupos[i].append(archivo)
        pesos[i] += archivo.stat().st_size
    return [sorted(g) for g in grupos if g]


def resumen_junit(xml_path):
    cifras = {"pruebas": 0, "fallas": 0, "errores": 0, "omitidas": 0, "xfail": 0}
    problemas = []
    if not xml_path.exists():
        return cifras, ["(sin JUnit XML: la partición no terminó; ver su log)"]
    raiz = ET.parse(xml_path).getroot()
    for caso in raiz.iter("testcase"):
        cifras["pruebas"] += 1
        ident = f'{caso.get("classname", "")}::{caso.get("name", "")}'
        if caso.find("failure") is not None:
            cifras["fallas"] += 1
            problemas.append("FALLA " + ident)
        elif caso.find("error") is not None:
            cifras["errores"] += 1
            problemas.append("ERROR " + ident)
        else:
            omitida = caso.find("skipped")
            if omitida is not None:
                if "xfail" in (omitida.get("type", "") + omitida.get("message", "")).lower():
                    cifras["xfail"] += 1
                else:
                    cifras["omitidas"] += 1
    return cifras, problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", required=True, type=Path)
    ap.add_argument("--repo", type=Path, default=Path(git(AQUI, "rev-parse", "--show-toplevel")))
    ap.add_argument("--particiones", type=int, default=max(1, min(os.cpu_count() or 1, 4)))
    ap.add_argument("--patron", default="test_*.py")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--pytest-extra", default="")
    a = ap.parse_args()

    repo = a.repo.resolve()
    salida = a.salida.resolve()
    if salida.exists() and any(salida.iterdir()):
        sys.exit(f"{salida} ya existe y no está vacío: elige un directorio nuevo.")
    salida.mkdir(parents=True, exist_ok=True)

    candidato = {"rama": git(repo, "rev-parse", "--abbrev-ref", "HEAD"), "head": git(repo, "rev-parse", "HEAD"),
                 "cambios": git(repo, "status", "--short").splitlines(), "huella_inicio": huella(repo),
                 "inicio": time.strftime("%Y-%m-%dT%H:%M:%S")}
    archivos = sorted(repo.glob(a.patron))
    grupos = particionar(archivos, max(1, a.particiones))
    procesos = []
    for i, grupo in enumerate(grupos):
        xml = salida / f"particion-{i}.xml"
        log = open(salida / f"particion-{i}.log", "w")
        cmd = ["timeout", str(a.timeout), sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
               f"--junitxml={xml}", *a.pytest_extra.split(), *[str(f.relative_to(repo)) for f in grupo]]
        procesos.append((i, grupo, xml, log, subprocess.Popen(cmd, cwd=repo, stdout=log, stderr=subprocess.STDOUT)))

    total = {"pruebas": 0, "fallas": 0, "errores": 0, "omitidas": 0, "xfail": 0}
    detalle = []
    for i, grupo, xml, log, proceso in procesos:
        codigo = proceso.wait()
        log.close()
        cifras, problemas = resumen_junit(xml)
        for clave in total:
            total[clave] += cifras[clave]
        detalle.append({"particion": i, "archivos": len(grupo), "codigo_salida": codigo, **cifras,
                        "problemas": problemas})

    candidato["huella_fin"] = huella(repo)
    valida = candidato["huella_inicio"] == candidato["huella_fin"]
    informe = {"candidato": candidato, "valida": valida, "total": total, "particiones": detalle}
    (salida / "resumen.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False))

    print(f'Candidato {candidato["rama"]} @ {candidato["head"][:10]} · huella {candidato["huella_inicio"][:12]}'
          + ("" if not candidato["cambios"] else f' · {len(candidato["cambios"])} archivos con cambios sin commit'))
    for d in detalle:
        print(f'  partición {d["particion"]}: {d["pruebas"]} pruebas, {d["fallas"]} fallas, {d["errores"]} errores,'
              f' {d["omitidas"]} omitidas, {d["xfail"]} xfail · salida {d["codigo_salida"]}')
        for p in d["problemas"]:
            print("    " + p)
    print(f'TOTAL: {total["pruebas"]} pruebas · {total["fallas"]} fallas · {total["errores"]} errores · '
          f'{total["omitidas"]} omitidas · {total["xfail"]} xfail')
    if not valida:
        print("INVÁLIDA: el candidato cambió durante la corrida; repita la verificación sobre un candidato estable.")
    ok = valida and total["fallas"] == 0 and total["errores"] == 0 and all(d["codigo_salida"] == 0 for d in detalle)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
