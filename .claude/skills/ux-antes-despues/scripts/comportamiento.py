#!/usr/bin/env python3
"""ux-antes-despues · comportamiento en navegador de un lado de la corrida.

  comportamiento.py --run RUN --tamano 1366x768 [--perfil PERFIL.json] [--lado despues] [--salida R.json]

No depende del directorio actual; el perfil por defecto es perfil_encuentro_clinico.json, junto a este script.
Corre sólo las comprobaciones que el perfil declara en 'comprobaciones_navegador', con la cuenta sintética de
comportamiento de ese tamaño, sobre el servidor de la corrida y con un Chromium sin red externa. Comprobaciones
disponibles:
  - un_solo_modo: un único modo marcado, y no sólo por color (marcador visible);
  - enter_agrega_linea: Enter agrega una línea y no envía;
  - borrador_en_vistas: el borrador y el modo se conservan al recorrer las pestañas del perfil;
  - menu_teclado_y_escape: el menú abre con clic y teclado, y cierra con Escape y con un clic fuera;
  - menu_no_mueve_nada: abrir el menú no mueve la escena ni la consola;
  - envio_limpia_cuadro: tras un envío real, el cuadro queda vacío.
Una comprobación que el perfil no declara no se corre: no se exige a una pantalla que no la tiene.
No crea cuentas ni toca bases. Escribe sólo el JSON de resultados.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import navegador

PERFIL = Path(__file__).resolve().parent / "perfil_encuentro_clinico.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--perfil", default=str(PERFIL))
    ap.add_argument("--tamano", required=True)
    ap.add_argument("--lado", default="despues")
    ap.add_argument("--salida")
    a = ap.parse_args()
    datos = navegador.corrida(a.run)
    perfil = json.loads(Path(a.perfil).resolve().read_text(encoding="utf-8"))
    from playwright.sync_api import sync_playwright

    et, sel, quiero = perfil["etiquetas"], perfil["selectores"], set(perfil["comprobaciones_navegador"])
    cuadro = f'textarea[aria-label="{et["cuadro"]}"]'
    resultados = {}

    def anotar(nombre, ok, detalle=""):
        resultados[nombre] = {"ok": bool(ok), "detalle": detalle}

    with sync_playwright() as pw:
        nav = navegador.Navegador(pw, a.tamano)
        page = nav.page
        p = nav.ingresar(datos["manifiesto"]["lados"][a.lado]["url"],
                         navegador.cuenta(datos, a.tamano, "comportamiento"))
        p.click(next(e for e in et["comenzar"] if p.has_button(e)))
        time.sleep(3)
        p.settle()
        marcados = lambda: page.evaluate(
            "(s) => [...document.querySelectorAll(s + ' input[type=radio]')].filter(i => i.checked)"
            ".map(i => i.closest('label').innerText.trim())", sel["modos"])
        borrador = lambda: page.locator(cuadro).first.input_value()
        caja = lambda s: page.locator(s).first.bounding_box()

        if "un_solo_modo" in quiero:
            marca = page.evaluate(
                "(s) => { const l = [...document.querySelectorAll(s + ' label[data-testid=\"stRadioOption\"]')]"
                ".find(l => l.querySelector('input').checked); return l ? getComputedStyle(l.querySelector('p'),"
                " '::before').content : ''; }", sel["modos"])
            anotar("un_solo_modo", len(marcados()) == 1 and marca not in ("", "none", "normal"), [marcados(), marca])
        if "enter_agrega_linea" in quiero or "borrador_en_vistas" in quiero:
            page.locator(cuadro).first.click()
            page.keyboard.type("Line one")
            page.keyboard.press("Enter")
            page.keyboard.type("line two")
            time.sleep(1.5)
            anotar("enter_agrega_linea", borrador() == "Line one\nline two", repr(borrador()))
        if "borrador_en_vistas" in quiero:
            antes = marcados()
            for pestana in perfil["pestanas"]:
                page.get_by_role("tab", name=pestana).first.click()
                time.sleep(0.5)
            anotar("borrador_en_vistas", borrador() == "Line one\nline two" and marcados() == antes, repr(borrador()))
        menu_etiqueta = next((e for e in et["menu"] if p.has_button(e)), None)
        if menu_etiqueta and ({"menu_teclado_y_escape", "menu_no_mueve_nada"} & quiero):
            menu = page.get_by_role("button", name=menu_etiqueta).first
            escena0, consola0 = caja(sel["escena"]), caja(sel["consola"])
            menu.click()
            time.sleep(0.8)
            abierto_clic = menu.get_attribute("aria-expanded") == "true"
            sin_mover = caja(sel["escena"]) == escena0 and caja(sel["consola"]) == consola0
            page.keyboard.press("Escape")
            time.sleep(0.8)
            cerrado_escape = menu.get_attribute("aria-expanded") == "false"
            menu.focus()
            page.keyboard.press("Enter")
            time.sleep(0.8)
            abierto_teclado = menu.get_attribute("aria-expanded") == "true"
            page.mouse.click(nav.ancho * 0.42, nav.alto * 0.8)
            time.sleep(0.8)
            cerrado_fuera = menu.get_attribute("aria-expanded") == "false"
            if "menu_teclado_y_escape" in quiero:
                anotar("menu_teclado_y_escape", abierto_clic and cerrado_escape and abierto_teclado and cerrado_fuera,
                       [abierto_clic, cerrado_escape, abierto_teclado, cerrado_fuera])
            if "menu_no_mueve_nada" in quiero:
                anotar("menu_no_mueve_nada", sin_mover)
        elif {"menu_teclado_y_escape", "menu_no_mueve_nada"} & quiero:
            anotar("menu", False, "el perfil declara un menú que esta pantalla no tiene")
        if "envio_limpia_cuadro" in quiero:
            page.locator(cuadro).first.fill("Troponin now.")
            page.get_by_role("button", name=next(e for e in et["enviar"] if p.has_button(e))).first.click()
            time.sleep(2)
            p.settle()
            anotar("envio_limpia_cuadro", borrador() == "", repr(borrador()))
        bloqueadas = nav.bloqueadas
        nav.cerrar()

    informe = {"lado": a.lado, "tamano": a.tamano, "comprobaciones": resultados,
               "red_externa_bloqueada_en_el_navegador": bloqueadas}
    texto = json.dumps(informe, indent=1, ensure_ascii=False)
    if a.salida:
        Path(a.salida).write_text(texto)
    print(texto)
    ok = all(r["ok"] for r in resultados.values())
    print("TODO OK" if ok else "HAY FALLAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
