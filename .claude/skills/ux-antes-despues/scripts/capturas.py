#!/usr/bin/env python3
"""ux-antes-despues · capturas reales ANTES/DESPUÉS del mismo estado.

  capturas.py --run RUN --salida DIR [--perfil PERFIL.json] [--lados antes,despues] [--tamanos 1440x900,...]

No depende del directorio actual; el perfil por defecto es perfil_encuentro_clinico.json, junto a este script.
Usa los servidores y las cuentas sintéticas de captura de 'entorno.py' (RUN/manifiesto.json y
RUN/credenciales.json), y un Chromium sin red externa, ni de la página ni propia (navegador.py).

Para cada tamaño y lado:
  - ingresa con la cuenta de capturas de ese tamaño;
  - sigue los pasos del perfil y captura los listados en 'capturas';
  - opcionalmente captura el panel (menú o barra lateral) cerrado y abierto.

Junto a cada captura guarda la huella de la foto del paciente; si difiere entre lados, el informe marca la
comparación visual como NO controlada. Al final arma hojas ANTES | DESPUÉS y exige pares de dimensiones
idénticas. Con un solo lado (--lados antes o --lados despues) no hay pares: la hoja es de ese lado, no se
informan pares faltantes y la comparación visual no aplica.

Escribe las capturas y el informe en DIR, y el net log de cada navegador en RUN
(red-navegador-capturas-LADO-TAMANO.json). Un destino no local en un net log es un problema. No crea cuentas ni
toca bases: las de la corrida ya existen.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import navegador

PERFIL = Path(__file__).resolve().parent / "perfil_encuentro_clinico.json"
LADOS = ("antes", "despues")
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
    elif accion == "pestana":
        page.get_by_role("tab", name=paso["pestana"]).first.click()
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
        nav = navegador.Navegador(pw, tamano, net_log=datos["dir"] / f"red-navegador-capturas-{lado}-{tamano}.json")
        try:
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
        finally:
            red = nav.cerrar()
        notas.append({"lado": lado, "tamano": tamano, "paso": "red", "bloqueadas": nav.bloqueadas, "navegador": red})


def hojas(salida, tamanos, notas, lados):
    """Una hoja por tamaño: ANTES | DESPUÉS si se pidieron los dos lados; si no, la columna del lado pedido."""
    from PIL import Image
    problemas = []
    columnas = [lado for lado in LADOS if lado in lados]
    for tamano in tamanos:
        w, h = (int(x) for x in tamano.split("x"))
        pares = sorted({n["archivo"].split("_", 2)[2] for n in notas if n["tamano"] == tamano and "archivo" in n})
        escala, borde = 0.5, 16
        sw, sh = int(w * escala), int(h * escala)
        hoja = Image.new("RGB", (len(columnas) * (sw + borde) + borde, len(pares) * (sh + borde) + borde), "white")
        for fila, sufijo in enumerate(pares):
            for col, lado in enumerate(columnas):
                ruta = salida / f"{lado}_{tamano}_{sufijo}"
                if not ruta.exists():
                    problemas.append(f"falta {ruta.name}")
                    continue
                img = Image.open(ruta).convert("RGB")
                if img.size != (w, h):
                    problemas.append(f"{ruta.name}: {img.size} ≠ {(w, h)}")
                    continue
                hoja.paste(img.resize((sw, sh)), (borde + col * (sw + borde), borde + fila * (sh + borde)))
        hoja.save(salida / f"hoja_{tamano}_{'_'.join(columnas)}.jpg", quality=82)
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--perfil", default=str(PERFIL))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--lados", default="antes,despues")
    ap.add_argument("--tamanos")
    a = ap.parse_args()
    lados = [lado.strip() for lado in a.lados.split(",") if lado.strip()]
    if not lados or set(lados) - set(LADOS) or len(set(lados)) != len(lados):
        sys.exit(f"--lados admite antes, despues o los dos, sin repetir: {a.lados!r}")
    datos = navegador.corrida(a.run)
    perfil = json.loads(Path(a.perfil).resolve().read_text(encoding="utf-8"))
    salida = Path(a.salida).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    tamanos = a.tamanos.split(",") if a.tamanos else datos["manifiesto"]["tamanos"]
    notas = []
    for tamano in tamanos:
        for lado in lados:
            capturar(datos, perfil, salida, lado, tamano, notas)
    problemas = hojas(salida, tamanos, notas, lados)
    redes = [n for n in notas if n["paso"] == "red"]
    for n in redes:
        if not navegador.red_limpia(n["navegador"]):
            problemas.append(f"Chromium {n['lado']} {n['tamano']}: "
                             + (f"destinos no locales {n['navegador']['no_locales']}" if n["navegador"].get("legible")
                                else f"net log ilegible ({n['navegador'].get('error')})"))
    fotos = {}
    for n in notas:
        if "foto" in n:
            fotos.setdefault((n["tamano"], n["paso"]), {})[n["lado"]] = n["foto"]
    distintas = sorted(f"{t} {paso}" for (t, paso), v in fotos.items() if len(set(v.values())) > 1)
    controlada = not distintas if len(lados) == 2 else None      # con un solo lado no hay comparación
    bloqueadas = sorted({u for n in notas for u in n.get("bloqueadas", [])})
    no_locales = sorted({h for n in redes for h in n["navegador"].get("no_locales", {})})
    desviados = sorted({s for n in redes for s in n["navegador"].get("desviados_al_sumidero", {})})
    servidor = datos["manifiesto"].get("servidor", {})
    informe = {"lados": lados, "notas": notas, "problemas": problemas, "fotos_distintas": distintas,
               "comparacion_visual_controlada": controlada, "semilla": servidor.get("semilla"),
               "red_externa_bloqueada_en_el_navegador": bloqueadas,
               "chromium_destinos_no_locales": no_locales, "chromium_desviados_al_sumidero": desviados}
    (salida / "capturas.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False))
    visual = ("no aplica (un solo lado)" if controlada is None else "controlada" if controlada
              else f"NO controlada ({len(distintas)} estados)")
    print("capturas:", sum("archivo" in n for n in notas), "· problemas:", len(problemas),
          "· comparación visual", visual,
          "· semilla de los servidores:", servidor.get("semilla"),
          "· peticiones externas abortadas:", len(bloqueadas),
          "· Chromium, destinos no locales:", len(no_locales),
          "· servicios desviados al sumidero:", ", ".join(desviados) or "ninguno")
    for problema in problemas:
        print("  ", problema)
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
