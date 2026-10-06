"""ux-antes-despues · lo común de capturas.py y comportamiento.py.

Lee la corrida de entorno.py, elige la cuenta sintética por tamaño y uso, y abre un Chromium sin red externa, en
dos capas:
  - la página: toda petición HTTP y todo WebSocket que no vayan al servidor local se abortan y se cuentan;
  - el navegador: el tráfico propio de Chromium (cuentas, GCM, hora de red, DNS sobre HTTPS, actualizaciones,
    autocompletar, contraseñas) no pasa por las rutas de la página. Chromium usa como proxy un sumidero (un puerto
    de loopback tomado y sin escuchar), no resuelve nombres no locales, apunta sus servicios de Google al sumidero
    y arranca con un perfil temporal que apaga el DNS sobre HTTPS, las consultas de hora, la predicción de red y el
    gestor de contraseñas.
Cada navegador escribe su net log; al cerrar se resume: destinos no locales intentados (deben ser 0) y servicios
de Chromium desviados al sumidero. Usa el ejecutable de `tanda20_runner` (BROWSER si existe; si no, el de
Playwright) y `Page` del árbol DESPUÉS de la corrida; `tanda20_runner.launch` no cambia para sus otros usos.
"""
import ipaddress
import json
import re
import shutil
import socket
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

LOCALES = {"127.0.0.1", "localhost", "::1"}
WS_EXTERNO = re.compile(r"^wss?://(?!(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?/)")
INGRESO = ("Username", "Password", "Sign in")       # el formulario de account_portal, en inglés
# Lo que Chromium decide sin URL propia, apagado antes de arrancar (net logs del 2026-10-05): DNS sobre HTTPS y
# consultas de hora en el Local State; en las preferencias, la predicción de red (preconexión al buscador) y el
# gestor de contraseñas con su revisión de filtraciones, que consulta a Google tras enviar el ingreso.
LOCAL_STATE = {"dns_over_https": {"mode": "off"},
               "network_time": {"network_time_queries_enabled": False}}
PREFERENCIAS = {"net": {"network_prediction_options": 2}, "credentials_enable_service": False,
                "profile": {"password_manager_leak_detection": False}}
URL_DE_RED = re.compile(r"\b(?:https?|wss?|ftp)://(\[[0-9a-fA-F:.]+\]|[A-Za-z0-9._~%-]+)", re.I)
DIRECCION = re.compile(r"^\[?([0-9a-fA-F:.]+?)\]?:\d+$")
# Campos del net log que describen el contexto de una petición, no su destino.
CONTEXTO = {"headers", "site_for_cookies", "network_anonymization_key", "network_isolation_key", "initiator",
            "top_frame_origin", "referrer"}


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


def rotulos_ingreso():
    """Los rótulos del ingreso en cada idioma de la app, de su propio catálogo de textos (report_language)."""
    juegos = [INGRESO]
    try:
        import report_language
    except ImportError:                                # un árbol sin catálogo sólo habla inglés
        return juegos
    for idioma in report_language.TABLES:
        juego = tuple(report_language.t(rotulo, idioma) for rotulo in INGRESO)
        if juego not in juegos:
            juegos.append(juego)
    return juegos


def _banderas(puerto):
    """Los servicios propios de Chromium, apuntados al sumidero; ningún nombre no local se resuelve."""
    s = f"http://127.0.0.1:{puerto}"
    return ["--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE localhost , EXCLUDE 127.0.0.1",
            "--disable-domain-reliability", "--no-pings",
            # vistos en el net log: ListAccounts, folae, checkin de GCM, el actualizador de componentes y las
            # predicciones de autocompletar de cada formulario
            f"--gaia-url={s}/", f"--google-base-url={s}/", f"--gcm-checkin-url={s}/checkin",
            f"--component-updater=url-source={s}/update", f"--autofill-server-url={s}/",
            # de las mismas familias, por si se activan
            f"--google-apis-url={s}/", f"--lso-url={s}/", f"--oauth-account-manager-url={s}/", f"--sync-url={s}/",
            f"--variations-server-url={s}/", f"--gcm-registration-url={s}/register",
            f"--gcm-mcs-endpoint=https://127.0.0.1:{puerto}", f"--search-provider-logo-url={s}/"]


def _local(host):
    host = host.strip("[]").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _host(valor):
    """El nombre de un 'host' del net log, con o sin puerto: a.b:443, [::1]:443, ::1."""
    if valor.startswith("["):
        return valor[1:].split("]", 1)[0]
    return valor.rsplit(":", 1)[0] if valor.count(":") == 1 else valor


def _cargar_net_log(ruta):
    texto = Path(ruta).read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(texto)
    except json.JSONDecodeError:                       # un net log sin cerrar: le falta el final
        return json.loads(texto.rstrip().rstrip(",") + "]}")


def resumen_net_log(ruta, puerto_sumidero):
    """Lo que Chromium intentó según su net log: destinos no locales (deben ser 0) y lo desviado al sumidero.

    Cuenta todo nombre o dirección de destino de los eventos: URLs http(s)/ws(s)/ftp, hosts que se resuelven o se
    conectan, y direcciones de conexiones TCP. Un connect UDP no envía nada (sólo elige la ruta, como el sondeo de
    IPv6 del resolvedor): cuenta sólo si ese socket envió bytes. Nunca registra las direcciones propias del equipo.
    """
    try:
        datos = _cargar_net_log(ruta)
    except (OSError, ValueError) as error:
        return {"legible": False, "error": f"{type(error).__name__}: {error}"[:200]}
    tipos = {v: k for k, v in datos["constants"]["logEventTypes"].items()}
    fuentes = {v: k for k, v in datos["constants"]["logSourceType"].items()}
    eventos = datos.get("events", [])
    udp, con_envio, vinculo = set(), set(), {}
    for e in eventos:
        fuente = e["source"]["id"]
        if fuentes.get(e["source"]["type"], "").startswith("UDP"):
            udp.add(fuente)
        if tipos.get(e["type"]) == "UDP_BYTES_SENT":
            con_envio.add(fuente)
        dependencia = (e.get("params") or {}).get("source_dependency")
        if isinstance(dependencia, dict):
            vinculo.setdefault(fuente, set()).add(dependencia.get("id"))
    for fuente in list(con_envio):                     # el socket UDP que envió y el que lo creó
        con_envio |= vinculo.get(fuente, set())
    no_locales, desviados, udp_sin_envio = Counter(), Counter(), Counter()

    def destino(host):
        if host and not _local(host):
            no_locales[host.strip("[]").lower()] += 1

    def recorrer(valor, clave, fuente):
        if isinstance(valor, dict):
            for k, v in valor.items():
                if k not in CONTEXTO and "local" not in k and "self" not in k:   # nunca la dirección propia
                    recorrer(v, k, fuente)
        elif isinstance(valor, list):
            for v in valor:
                recorrer(v, clave, fuente)
        elif isinstance(valor, str):
            if clave == "group_id":                    # "https://destino <clave de aislamiento>"
                valor = valor.split(" <", 1)[0]
            for host in URL_DE_RED.findall(valor):
                destino(host)
            if clave in ("address", "remote_address", "address_list") and (m := DIRECCION.match(valor)):
                if fuente in udp and fuente not in con_envio:
                    udp_sin_envio[m.group(1)] += 1
                else:
                    destino(m.group(1))
            elif clave in ("host", "hostname") and "://" not in valor:
                destino(_host(valor))

    for e in eventos:
        if tipos.get(e["type"]) == "UDP_LOCAL_ADDRESS":
            continue
        params = e.get("params") or {}
        recorrer(params, "", e["source"]["id"])
        if tipos.get(e["type"]) == "URL_REQUEST_START_JOB" and params.get("url"):
            partes = urlsplit(params["url"])
            if partes.hostname == "127.0.0.1" and partes.port == puerto_sumidero:
                desviados["/".join(partes.path.split("/")[:3]) or "/"] += 1   # el servicio, sin lo que envía
    return {"legible": True, "eventos": len(eventos), "no_locales": dict(no_locales.most_common()),
            "desviados_al_sumidero": dict(sorted(desviados.items())),
            "udp_connect_sin_envio": sum(udp_sin_envio.values())}


class Navegador:
    """Chromium del tamaño pedido, con la red externa de la página abortada y la del navegador en el sumidero."""

    def __init__(self, pw, tamano, net_log=None):
        from tanda20_runner import BROWSER
        self.ancho, self.alto = (int(x) for x in tamano.split("x"))
        self.bloqueadas = []
        self.red = None
        self.net_log = Path(net_log) if net_log else None
        # Tomado y sin escuchar: toda conexión se rechaza y ningún otro proceso puede escuchar ahí mientras tanto.
        self.sumidero = socket.socket()
        self.sumidero.bind(("127.0.0.1", 0))
        self.puerto = self.sumidero.getsockname()[1]
        self.perfil = Path(tempfile.mkdtemp(prefix="ux-antes-despues-chromium-"))
        (self.perfil / "Local State").write_text(json.dumps(LOCAL_STATE), encoding="utf-8")
        (self.perfil / "Default").mkdir()
        (self.perfil / "Default" / "Preferences").write_text(json.dumps(PREFERENCIAS), encoding="utf-8")
        banderas = _banderas(self.puerto) + ([f"--log-net-log={self.net_log}"] if self.net_log else [])
        opciones = {"headless": True, "args": banderas, "viewport": {"width": self.ancho, "height": self.alto},
                    "proxy": {"server": f"http://127.0.0.1:{self.puerto}", "bypass": "127.0.0.1,localhost"}}
        if Path(BROWSER).exists():                     # la misma elección que tanda20_runner.launch
            opciones["executable_path"] = BROWSER
        self.contexto = pw.chromium.launch_persistent_context(str(self.perfil), **opciones)
        self.contexto.route("**/*", self._http)
        self.contexto.route_web_socket(WS_EXTERNO, self._ws)
        self.page = self.contexto.pages[0] if self.contexto.pages else self.contexto.new_page()

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
        juegos = rotulos_ingreso()
        juego = next((j for j in juegos if self.page.get_by_label(j[0], exact=True).count()), None)
        if juego is None:
            raise RuntimeError(f"No hay formulario de ingreso con ninguno de estos rótulos: {juegos}")
        usuario, clave, boton = juego
        p.fill(usuario, cuenta["usuario"])
        p.fill(clave, cuenta["clave"])
        p.click(boton)
        p.settle()
        return p

    def cerrar(self):
        """Cierra Chromium, resume su net log y borra el perfil temporal. Idempotente."""
        if self.contexto is None:
            return self.red
        try:
            self.contexto.close()
        finally:
            self.contexto = None
            self.sumidero.close()
            shutil.rmtree(self.perfil, ignore_errors=True)
        if self.net_log:
            self.red = {"net_log": str(self.net_log), **resumen_net_log(self.net_log, self.puerto)}
        return self.red


def red_limpia(red):
    """Un resumen de net log sin destinos no locales. Sin net log legible no se puede afirmar."""
    return bool(red) and red.get("legible") and not red.get("no_locales")
