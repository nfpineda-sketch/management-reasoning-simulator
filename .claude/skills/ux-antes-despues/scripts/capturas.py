#!/usr/bin/env python3
"""ux-antes-despues · capturas reales ANTES/DESPUÉS del mismo estado.

  capturas.py --run RUN --salida DIR [--perfil PERFIL.json] [--lados antes,despues] [--tamanos 1440x900,...]

No depende del directorio actual; el perfil por defecto es perfil_encuentro_clinico.json, junto a este script.
Usa los servidores y las cuentas sintéticas de captura de 'entorno.py' (RUN/manifiesto.json y
RUN/credenciales.json), y un Chromium sin red externa (navegador.py).

Para cada tamaño y lado:
  - ingresa con la cuenta de capturas de ese tamaño;
  - sigue los pasos del perfil y captura los listados en 'capturas';
  - opcionalmente captura el panel (menú o barra lateral) cerrado y abierto.

Junto a cada captura guarda la huella de la foto del paciente; si difiere entre lados, el informe marca la
comparación visual como NO controlada. Al final arma hojas ANTES | DESPUÉS y exige pares de dimensiones
idénticas. Escribe sólo en DIR. No crea cuentas ni toca bases: las de la corrida ya existen.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import navegador

PERFIL = Path(__file__).resolve().parent / "perfil_encuentro_clinico.json"
HUELLA_FOTO = """(selectores) => {
  for (const sel of selectores) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const bg = getComputedStyle(el).backgroundImage;
    if (bg && bg !== 'none') return bg;
    const img = el.querySelector('img');
    if (img && img.src) return img.src;
  }
  return 'sin foto';
}"""


def _primer_boton(p, etiquetas):
    for etiqueta in etiquetas:
        if p.has_button(etiqueta):
            return etiqueta
    raise RuntimeError(f"Ningún botón {etiquetas}")


def _modo(page, p, nombre):
    page.locator('[data-testid="stMain"] label[data-testid="stRadioOption"]', has_text=nombre).first.click()
    time.sleep(1)
    p.settle()


def _cerrar_dialogo(page, p):
    """Un diálogo abierto (por ejemplo, el ECG) tapa la página: se cierra con Escape antes del paso siguiente."""
    dialogo = page.locator('[data-testid="stDialog"]')
    if dialogo.count() and dialogo.first.is_visible():
        page.keyboard.press("Escape")
        dialogo.first.wait_for(state="hidden", timeout=15000)
        p.settle()


def _paso(page, p, paso, et):
    accion = paso["accion"]
    _cerrar_dialogo(page, p)
    if paso.get("modo"):
        _modo(page, p, paso["modo"])
    if accion == "comenzar":
        p.click(_primer_boton(p, et["comenzar"]))
        time.sleep(3)
    elif accion == "enviar":
        page.locator(f'textarea[aria-label="{et["cuadro"]}"]').first.fill(paso["texto"])
        p.click(_primer_boton(p, et["enviar"]))
    elif accion == "preguntar":
        _modo(page, p, "Talk")
        page.get_by_label(et["preguntar_campo"]).first.fill(paso["texto"])
        p.click(et["preguntar_boton"])
    elif accion == "examinar":
        _modo(page, p, "Examine")
        page.locator('[data-testid="stSelectbox"]', has_text=et["examinar_campo"]).first.click()
        page.get_by_role("option", name=paso["region"]).first.click()
        time.sleep(0.8)
        p.click(et["examinar_boton"])
    elif accion == "campos":
        for etiqueta, valor in paso["valores"].items():
            p.fill(etiqueta, valor)
        p.click(paso["boton"])
    elif accion == "boton":
        p.click(paso["etiqueta"])
    elif accion == "cerrar":
        p.click(_primer_boton(p, et["cerrar"]))
        if any(p.has_button(e) for e in et["terminar"]):
            p.click(_primer_boton(p, et["terminar"]))
    else:
        raise ValueError(f"Acción desconocida: {accion}")
    time.sleep(1)
    p.settle()


def _panel(page, p, et):
    """Abre el panel de cada versión: el menú si existe; si no, pliega o despliega la barra lateral."""
    menu = next((e for e in et["menu"] if p.has_button(e)), None)
    if menu:
        page.get_by_role("button", name=menu).first.click()
        return "menu"
    page.locator('[data-testid="stSidebarHeader"]').first.hover()
    time.sleep(0.5)
    page.locator('[data-testid="stSidebarCollapseButton"] button').first.click(force=True)
    return "barra lateral"


def capturar(datos, perfil, salida, lado, tamano, notas):
    from playwright.sync_api import sync_playwright
    et = perfil["etiquetas"]
    with sync_playwright() as pw:
        nav = navegador.Navegador(pw, tamano)
        page = nav.page
        p = nav.ingresar(datos["manifiesto"]["lados"][lado]["url"], navegador.cuenta(datos, tamano, "capturas"))
        for paso in perfil["pasos"]:
            _paso(page, p, paso, et)
            if paso["id"] in perfil["capturas"]:
                nombre = f"{lado}_{tamano}_{paso['id']}.png"
                page.screenshot(path=str(salida / nombre))
                foto = page.evaluate(HUELLA_FOTO, perfil["selectores"]["foto"])
                notas.append({"lado": lado, "tamano": tamano, "paso": paso["id"], "archivo": nombre,
                              "foto": hashlib.sha256(foto.encode()).hexdigest()[:12]})
            if perfil.get("panel", {}).get("despues_de") == paso["id"]:
                page.screenshot(path=str(salida / f"{lado}_{tamano}_panel_cerrado.png"))
                cual = _panel(page, p, et)
                time.sleep(1)
                page.screenshot(path=str(salida / f"{lado}_{tamano}_panel_abierto.png"))
                notas.append({"lado": lado, "tamano": tamano, "paso": "panel", "control": cual})
                page.keyboard.press("Escape")
                time.sleep(0.8)
        notas.append({"lado": lado, "tamano": tamano, "paso": "red", "bloqueadas": nav.bloqueadas})
        nav.cerrar()


def hojas(salida, tamanos, notas):
    from PIL import Image
    problemas = []
    for tamano in tamanos:
        w, h = (int(x) for x in tamano.split("x"))
        pares = sorted({n["archivo"].split("_", 2)[2] for n in notas if n["tamano"] == tamano and "archivo" in n})
        escala, borde = 0.5, 16
        sw, sh = int(w * escala), int(h * escala)
        hoja = Image.new("RGB", (2 * sw + 3 * borde, len(pares) * (sh + borde) + borde), "white")
        for fila, sufijo in enumerate(pares):
            for col, lado in enumerate(("antes", "despues")):
                ruta = salida / f"{lado}_{tamano}_{sufijo}"
                if not ruta.exists():
                    problemas.append(f"falta {ruta.name}")
                    continue
                img = Image.open(ruta).convert("RGB")
                if img.size != (w, h):
                    problemas.append(f"{ruta.name}: {img.size} ≠ {(w, h)}")
                    continue
                hoja.paste(img.resize((sw, sh)), (borde + col * (sw + borde), borde + fila * (sh + borde)))
        hoja.save(salida / f"hoja_{tamano}_antes_despues.jpg", quality=82)
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--perfil", default=str(PERFIL))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--lados", default="antes,despues")
    ap.add_argument("--tamanos")
    a = ap.parse_args()
    datos = navegador.corrida(a.run)
    perfil = json.loads(Path(a.perfil).resolve().read_text(encoding="utf-8"))
    salida = Path(a.salida).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    tamanos = a.tamanos.split(",") if a.tamanos else datos["manifiesto"]["tamanos"]
    notas = []
    for tamano in tamanos:
        for lado in a.lados.split(","):
            capturar(datos, perfil, salida, lado, tamano, notas)
    problemas = hojas(salida, tamanos, notas)
    fotos = {}
    for n in notas:
        if "foto" in n:
            fotos.setdefault((n["tamano"], n["paso"]), {})[n["lado"]] = n["foto"]
    distintas = sorted(f"{t} {paso}" for (t, paso), v in fotos.items() if len(set(v.values())) > 1)
    bloqueadas = sorted({u for n in notas for u in n.get("bloqueadas", [])})
    servidor = datos["manifiesto"].get("servidor", {})
    informe = {"notas": notas, "problemas": problemas, "fotos_distintas": distintas,
               "comparacion_visual_controlada": not distintas, "semilla": servidor.get("semilla"),
               "red_externa_bloqueada_en_el_navegador": bloqueadas}
    (salida / "capturas.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False))
    print("capturas:", sum("archivo" in n for n in notas), "· problemas:", len(problemas),
          "· comparación visual", "controlada" if not distintas else f"NO controlada ({len(distintas)} estados)",
          "· semilla de los servidores:", servidor.get("semilla"),
          "· peticiones externas abortadas:", len(bloqueadas))
    for problema in problemas:
        print("  ", problema)
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
