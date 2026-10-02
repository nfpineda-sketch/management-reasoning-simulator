"""ux-antes-despues · lo común de capturas.py y comportamiento.py.

Lee la corrida de entorno.py, elige la cuenta sintética por tamaño y uso, y abre un Chromium sin red externa:
toda petición HTTP y todo WebSocket que no vayan al servidor local se abortan y se cuentan. Usa
`tanda20_runner.launch` y `Page` del árbol DESPUÉS de la corrida.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

LOCALES = {"127.0.0.1", "localhost", "::1"}
WS_EXTERNO = re.compile(r"^wss?://(?!(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?/)")


def corrida(run):
    run = Path(run).resolve()
    datos = {"dir": run, "manifiesto": json.loads((run / "manifiesto.json").read_text(encoding="utf-8")),
             "credenciales": json.loads((run / "credenciales.json").read_text(encoding="utf-8"))}
    sys.path.insert(0, str(run / "despues"))          # tanda20_runner del candidato
    return datos


def cuenta(datos, tamano, uso):
    for c in datos["credenciales"]["residentes"]:
        if c["tamano"] == tamano and c.get("uso") == uso:
            return c
    sys.exit(f"La corrida no tiene una cuenta de {uso} para {tamano}: prepárala con --tamanos que lo incluya.")


class Navegador:
    """Chromium del tamaño pedido, con toda la red externa abortada y contada."""

    def __init__(self, pw, tamano):
        from tanda20_runner import launch
        self.ancho, self.alto = (int(x) for x in tamano.split("x"))
        self.bloqueadas = []
        self.navegador = launch(pw)
        self.contexto = self.navegador.new_context(viewport={"width": self.ancho, "height": self.alto})
        self.contexto.route("**/*", self._http)
        self.contexto.route_web_socket(WS_EXTERNO, self._ws)
        self.page = self.contexto.new_page()

    def _http(self, route):
        if (urlsplit(route.request.url).hostname or "") in LOCALES:
            route.continue_()
        else:
            self.bloqueadas.append(route.request.url[:160])
            route.abort()

    def _ws(self, ws):
        self.bloqueadas.append(ws.url[:160])
        ws.close()

    def ingresar(self, url, cuenta, timeout=180):
        from tanda20_runner import Page
        p = Page(self.page, timeout=timeout)
        self.page.goto(url, wait_until="networkidle")
        p.settle()
        p.fill("Username", cuenta["usuario"])
        p.fill("Password", cuenta["clave"])
        p.click("Sign in")
        p.settle()
        return p

    def cerrar(self):
        self.navegador.close()
