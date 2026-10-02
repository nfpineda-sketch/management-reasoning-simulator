#!/usr/bin/env python3
"""ux-antes-despues · aislamiento de los procesos de la app durante una corrida.

Como lanzador (lo usa entorno.py):
  aislamiento.py --log ARCHIVO [--semilla N] -m MODULO [args...]
  aislamiento.py --log ARCHIVO -c CODIGO [args...]
Como módulo (lo usa equivalencia.py): instalar_guardia, autoprueba, entorno_limpio, fijar_semilla, resumen_log.

Red. Dentro del proceso se bloquea toda conexión saliente IPv4/IPv6, también a loopback, donde escucha el proxy de
salida del entorno, y la resolución de nombres no locales. Las conexiones entrantes y los sockets UNIX siguen
funcionando: el servidor sigue atendiendo al navegador. Cada intento queda en el log (JSON por línea).

Autoprueba. Al instalarse, la guardia intenta resolver el nombre del proveedor y conectar a una IP de
documentación (RFC 5737) y a loopback. Los tres intentos deben quedar bloqueados por la guardia; si no, el
lanzador no arranca la app. Ni siquiera una guardia rota llegaría al proveedor: resolver un nombre no es
conectarse, y esa IP no es enrutable.

Credenciales. entorno_limpio() arma el entorno desde una lista permitida (PATH, idioma y zona horaria) más lo que
se le pase. No hereda claves, tokens ni proxies. HOME apunta a un directorio de la corrida, sin secrets.toml.

Semilla. Con --semilla, sólo curriculum_runtime ve, al importarse, un `secrets` cuyo randbelow devuelve la
semilla. El resto de la app usa el módulo real: tokens de sesión, contraseñas.
"""
import argparse
import errno
import importlib.abc
import importlib.machinery
import json
import os
import runpy
import socket
import sys
import time
import traceback

PERMITIDAS = ("PATH", "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR", "TERM")
SOSPECHOSAS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "PROXY", "OPENAI", "ANTHROPIC",
               "AWS_", "GOOGLE_", "AZURE_", "GITHUB", "GH_")
NOMBRES_LOCALES = {"localhost", "localhost.localdomain", "ip6-localhost", "::1", "::", "0.0.0.0", ""}
AUTOPRUEBA = (("resolver api.openai.com", "resolver", ("api.openai.com", 443)),
              ("conectar 192.0.2.1:443", "conectar", ("192.0.2.1", 443)),
              ("conectar 127.0.0.1:9", "conectar", ("127.0.0.1", 9)))
_estado = {"log": None, "autoprueba": False, "instalada": False}
_original = {}


class Bloqueada(ConnectionRefusedError):
    """Conexión o envío bloqueado por la guardia."""


class ResolucionBloqueada(socket.gaierror):
    """Resolución de un nombre no local bloqueada por la guardia."""


def entorno_limpio(home, extra=None):
    """El entorno de un proceso de la app: lo permitido, HOME propio y `extra`. Nada más se hereda."""
    env = {k: os.environ[k] for k in PERMITIDAS if k in os.environ}
    env["HOME"] = str(home)
    env.update({k: str(v) for k, v in (extra or {}).items()})
    return env


def sospechosas(nombres):
    """Los nombres de variables que parecen credenciales o proxies (sólo nombres, nunca valores)."""
    return sorted(n for n in nombres if any(s in n.upper() for s in SOSPECHOSAS))


def _anotar(entrada):
    entrada = {"hora": time.strftime("%H:%M:%S"), "pid": os.getpid(), **entrada}
    if _estado["log"]:
        with open(_estado["log"], "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False, default=repr) + "\n")


def _intento(tipo, destino):
    entrada = {"tipo": tipo, "destino": repr(destino), "autoprueba": _estado["autoprueba"]}
    if not _estado["autoprueba"]:
        entrada["origen"] = [f"{f.filename}:{f.lineno}" for f in traceback.extract_stack(limit=10)[:-2]]
    _anotar(entrada)


def _red(sock):
    return sock.family in (socket.AF_INET, socket.AF_INET6)


def _connect(self, direccion):
    if _red(self):
        _intento("connect", direccion)
        raise Bloqueada(errno.ECONNREFUSED, f"aislamiento: conexión saliente bloqueada a {direccion!r}")
    return _original["connect"](self, direccion)


def _connect_ex(self, direccion):
    if _red(self):
        _intento("connect_ex", direccion)
        return errno.ECONNREFUSED
    return _original["connect_ex"](self, direccion)


def _sendto(self, datos, *args):
    if _red(self):
        _intento("sendto", args[-1] if args else None)
        raise Bloqueada(errno.ECONNREFUSED, "aislamiento: envío saliente bloqueado")
    return _original["sendto"](self, datos, *args)


def _local(host):
    if host is None:
        return True
    nombre = (host.decode(errors="replace") if isinstance(host, bytes) else str(host)).lower()
    return nombre in NOMBRES_LOCALES or nombre.startswith("127.")


def _resolucion(nombre_funcion):
    original = getattr(socket, nombre_funcion)

    def resolver(host, *args, **kwargs):
        if not _local(host):
            _intento(nombre_funcion, host)
            raise ResolucionBloqueada(socket.EAI_NONAME, f"aislamiento: resolución bloqueada de {host!r}")
        return original(host, *args, **kwargs)
    return resolver


def instalar_guardia(log):
    """Bloquea la red saliente de este proceso desde ahora. Idempotente."""
    if _estado["instalada"]:
        return
    _estado["log"] = str(log) if log else None
    for nombre, reemplazo in (("connect", _connect), ("connect_ex", _connect_ex), ("sendto", _sendto)):
        _original[nombre] = getattr(socket.socket, nombre)
        setattr(socket.socket, nombre, reemplazo)
    for nombre in ("getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        setattr(socket, nombre, _resolucion(nombre))
    _estado["instalada"] = True


def autoprueba():
    """Los tres intentos deben quedar bloqueados por la guardia. Devuelve el resultado de cada uno."""
    resultado = {}
    _estado["autoprueba"] = True
    try:
        for nombre, accion, destino in AUTOPRUEBA:
            try:
                if accion == "resolver":
                    socket.getaddrinfo(*destino)
                else:
                    with socket.socket() as s:
                        s.settimeout(2)
                        s.connect(destino)
                resultado[nombre] = "NO BLOQUEADO"
            except (Bloqueada, ResolucionBloqueada):
                resultado[nombre] = "bloqueado"
            except OSError as error:
                resultado[nombre] = f"NO BLOQUEADO ({type(error).__name__})"
    finally:
        _estado["autoprueba"] = False
    _anotar({"tipo": "autoprueba", "resultado": resultado})
    return resultado


def autoprueba_ok(resultado):
    return bool(resultado) and all(v == "bloqueado" for v in resultado.values())


def resumen_log(ruta):
    """Por proceso: la autoprueba y los intentos bloqueados fuera de ella (con su destino y origen)."""
    procesos, intentos = {}, []
    if ruta and os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                entrada = json.loads(linea)
                if entrada["tipo"] == "autoprueba":
                    procesos[entrada["pid"]] = entrada["resultado"]
                elif not entrada.get("autoprueba"):
                    intentos.append(entrada)
    return {"autoprueba_por_proceso": procesos, "intentos_bloqueados": intentos}


class SecretsConSemilla:
    """La vista de `secrets` que ve sólo curriculum_runtime: randbelow devuelve la semilla; lo demás es real."""

    def __init__(self, real, semilla):
        self._real, self._semilla = real, int(semilla)

    def randbelow(self, limite):
        return self._semilla % limite

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)


class _SemillaAlImportar(importlib.abc.MetaPathFinder):
    def __init__(self, modulo, semilla):
        self.modulo, self.semilla = modulo, semilla

    def find_spec(self, nombre, ruta, destino=None):
        if nombre != self.modulo:
            return None
        spec = importlib.machinery.PathFinder.find_spec(nombre, ruta)
        if spec is None or spec.loader is None:
            return spec
        ejecutar, semilla = spec.loader.exec_module, self.semilla

        def exec_module(modulo):
            ejecutar(modulo)
            modulo.secrets = SecretsConSemilla(modulo.secrets, semilla)
        spec.loader.exec_module = exec_module
        return spec


def fijar_semilla(semilla, modulo="curriculum_runtime"):
    """Desde ahora, cada vez que se importe `modulo`, su `secrets` es la vista con semilla."""
    sys.meta_path.insert(0, _SemillaAlImportar(modulo, semilla))


def main():
    argv = sys.argv[1:]
    corte = next((i for i, x in enumerate(argv) if x in ("-m", "-c")), None)
    if corte is None or corte + 1 >= len(argv):
        sys.exit(__doc__)
    ap = argparse.ArgumentParser(prog="aislamiento.py")
    ap.add_argument("--log", required=True)
    ap.add_argument("--semilla", type=int)
    a = ap.parse_args(argv[:corte])
    modo, objetivo, resto = argv[corte], argv[corte + 1], argv[corte + 2:]
    instalar_guardia(a.log)
    resultado = autoprueba()
    if not autoprueba_ok(resultado):
        sys.exit(f"aislamiento: la autoprueba de red falló, la app no arranca: {resultado}")
    if a.semilla is not None:
        fijar_semilla(a.semilla)
    if modo == "-m":
        sys.argv = [objetivo, *resto]
        runpy.run_module(objetivo, run_name="__main__", alter_sys=True)
    else:
        sys.argv = ["-c", *resto]
        exec(compile(objetivo, "<aislamiento -c>", "exec"), {"__name__": "__main__"})


if __name__ == "__main__":
    main()
