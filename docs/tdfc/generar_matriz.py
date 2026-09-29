"""Matriz de oportunidades del banco (instrucción docente 59D; declarada en el ciclo 8).

Lee, sin importar ni ejecutar nada del repositorio:

* la tabla de estados de BORRADOR_TDFC.md (entre los marcadores
  ``estados-tdfc``): el borrador de TD1, F1, C1, C3 y C4, fuente única;
* ``case_assessment_bank.C14_DECLARATIONS`` (qué declara el banco para C14) y
  ``tdfc_declarations.DECLARATIONS`` (TD1, F1, C1 y C3, desde el ciclo 8);
* ``cognitive_catalog.BIAS_CHALLENGES`` y ``curriculum._FOUNDATION_CHALLENGES``
  (los Decision Challenges y sus ``families``);
* ``clinical_cases.py``, ``hypoglycemia_catalog.py`` y ``c14_review.DRAFT``
  (los 31 casos, su familia y su orden).

Todo se lee con ``ast`` sobre el texto de los archivos: no se importa ningún
módulo del repositorio y no se escribe nada fuera de esta carpeta. Escribe
MATRIZ_OPORTUNIDADES.md junto a este script e imprime un resumen.

Es cobertura de oportunidades del banco de casos, no cobertura del constructo
de un residente: no calcula competencia de nadie.

Uso:  python3 -B generar_matriz.py [ruta_del_repositorio]
"""
from __future__ import annotations

import ast
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

AQUI = Path(__file__).resolve().parent
REPO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else AQUI.parents[1]
BORRADOR = AQUI / "BORRADOR_TDFC.md"
SALIDA = AQUI / "MATRIZ_OPORTUNIDADES.md"

TDFC = ("TD1", "F1", "C1", "C3", "C4")
VALORES = ("TARGET", "DECLARED YES", "DECLARED NO", "NOT REVIEWED",
           "DRAFT YES", "DRAFT NO", "DRAFT UNCERTAIN")
CODIGO = {"TARGET": "TARGET", "DECLARED YES": "DECL+", "DECLARED NO": "DECL−", "NOT REVIEWED": "NR",
          "DRAFT YES": "DRAFT+", "DRAFT NO": "DRAFT−", "DRAFT UNCERTAIN": "DRAFT?"}

# --- las ocho decisiones de DECISIONES_TDFC.md: qué deja cada respuesta ------------------
# Cada celda dudosa del borrador está en exactamente una decisión. "approve" es la
# recomendación; "reject", la regla contraria. Una respuesta "modify" se escribe a mano.
_YES, _NO = "yes", "no"


def _cells(pairs, approve, reject):
    return {"approve": {pair: approve for pair in pairs}, "reject": {pair: reject for pair in pairs}}


DECISIONES = {
    "TDFC-1": {"titulo": "TD1 · SCA estable con un ECG que exige intervención inmediata",
               **_cells([("acs_61m_posterior", "TD1"), ("acs_52m_de_winter", "TD1"), ("acs_66f_nonst", "TD1")],
                        _NO, _YES)},
    "TDFC-2": {"titulo": "F1 · Hipoglicemia con vía aérea, ventilación y circulación conservadas",
               **_cells([("hypoglycemia_28m", "F1"), ("hypoglycemia_76f", "F1"),
                         ("hypoglycemia_54m_thiamine", "F1")], _YES, _NO)},
    "TDFC-3": {"titulo": "C1 · Hipoxemia grave sin shock que la primera línea suele estabilizar",
               **_cells([("pulmonary_embolism_33f", "C1"), ("asthma_24f", "C1")], _NO, _YES)},
    "TDFC-4": {"titulo": "C1 · Trauma mientras C2 sigue deshabilitada",
               **_cells([("trauma_limb_hemorrhage_27m", "C1"), ("trauma_hemothorax_41m", "C1")], _NO, _YES)},
    "TDFC-5": {"titulo": "C1 y C3 · Deterioro por diseño durante la espera de la reperfusión",
               **_cells([("acs_54m_inferior", "C1"), ("acs_70f_left_main", "C3")], _YES, _NO)},
    # La recomendación aprobada difiere del borrador (que proponía YES en los seis): YES en
    # las dos neumonías y en pulmonary_embolism_61m, NO en los otros tres (ciclo 8).
    "TDFC-6": {"titulo": "C3 · Oxígeno ante hipoxemia sin falla ventilatoria ni amenaza de vía aérea",
               "approve": {("pneumonia_46f", "C3"): _YES, ("pneumonia_83m", "C3"): _YES,
                           ("pulmonary_embolism_61m", "C3"): _YES, ("pulmonary_embolism_33f", "C3"): _NO,
                           ("asthma_24f", "C3"): _NO, ("anaphylaxis_63m_betablocked", "C3"): _NO},
               "reject": {pareja: _NO for pareja in (
                   ("pneumonia_46f", "C3"), ("pneumonia_83m", "C3"), ("pulmonary_embolism_33f", "C3"),
                   ("pulmonary_embolism_61m", "C3"), ("asthma_24f", "C3"), ("anaphylaxis_63m_betablocked", "C3"))}},
    "TDFC-7": {"titulo": "C4 · Sedoanalgesia para un procedimiento que el caso trae y no declara",
               **_cells([("bradycardia_avb3_78f", "C4"), ("trauma_hemothorax_41m", "C4"),
                         ("trauma_limb_hemorrhage_27m", "C4")], _NO, _YES)},
    "TDFC-8": {"titulo": "C4 · Analgesia del cuadro, sin procedimiento",
               **_cells([("renal_colic_34m", "C4")], _NO, _YES)},
}
RECOMENDADO = {clave: "approve" for clave in DECISIONES}
# Casos cuyas filas TD/F/C esperan una decisión y conservan la transición (tdfc_review.PENDING).
# Ninguno desde que DF-20 se cerró (ciclo 9, 2026-09-29).
PENDIENTES = {}
TODO_RECHAZADO = {clave: "reject" for clave in DECISIONES}


class Inconsistencia(SystemExit):
    pass


def _texto(relativo):
    ruta = REPO / relativo
    return ruta.read_text(encoding="utf-8"), ruta


def _huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:12]


def _asignacion(arbol, nombre):
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nombre for t in nodo.targets):
            return nodo.value
    raise Inconsistencia(f"No encontré la asignación {nombre}.")


def _constante(nodo):
    if isinstance(nodo, ast.Constant):
        return nodo.value
    raise Inconsistencia(f"Se esperaba una constante en la línea {getattr(nodo, 'lineno', '?')}.")


# --- lectura del repositorio (sólo lectura, sin importar) ---------------------------------
def leer_c14():
    texto, ruta = _texto("case_assessment_bank.py")
    valor = _asignacion(ast.parse(texto), "C14_DECLARATIONS")
    declarados = {}
    for clave, llamada in zip(valor.keys, valor.values):
        funcion = llamada.func.id if isinstance(llamada, ast.Call) and isinstance(llamada.func, ast.Name) else None
        if funcion not in {"_c14_yes", "_c14_no"}:
            raise Inconsistencia(f"C14_DECLARATIONS: valor inesperado para {ast.dump(clave)}.")
        declarados[_constante(clave)] = {"estado": "yes" if funcion == "_c14_yes" else "no",
                                         "grupo": _constante(llamada.args[0])}
    return declarados, ruta


def leer_c4():
    """Si el banco declara C4 en todos sus casos (ciclo 7): C4_DECLARATIONS recorre CASES."""
    texto, ruta = _texto("case_assessment_bank.py")
    valor = _asignacion(ast.parse(texto), "C4_DECLARATIONS")
    recorre_banco = (isinstance(valor, ast.DictComp) and len(valor.generators) == 1
                     and isinstance(valor.generators[0].iter, ast.Name) and valor.generators[0].iter.id == "CASES")
    llamadas = {n.func.id for n in ast.walk(valor) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    if not recorre_banco or llamadas != {"_c4_no"}:
        raise Inconsistencia("C4_DECLARATIONS ya no declara NO en todos los casos del banco: revisar la matriz.")
    return True, ruta


def leer_tdfc():
    """Lo que el banco declara para TD1, F1, C1 y C3 (tdfc_declarations.DECLARATIONS, ciclo 8)."""
    texto, ruta = _texto("tdfc_declarations.py")
    valor = _asignacion(ast.parse(texto), "DECLARATIONS")
    declarados = {}
    for clave, filas in zip(valor.keys, valor.values):
        caso = _constante(clave)
        declarados[caso] = {}
        for objetivo, llamada in zip(filas.keys, filas.values):
            funcion = llamada.func.id if isinstance(llamada, ast.Call) and isinstance(llamada.func, ast.Name) else None
            if funcion not in {"_yes", "_no"}:
                raise Inconsistencia(f"tdfc_declarations: valor inesperado en {caso}.")
            grupo = _constante(llamada.args[1] if funcion == "_yes" else llamada.args[0])
            declarados[caso][_constante(objetivo)] = {"estado": "yes" if funcion == "_yes" else "no", "grupo": grupo}
    return declarados, ruta


def leer_desafios():
    texto, ruta_cc = _texto("cognitive_catalog.py")
    sesgo = _asignacion(ast.parse(texto), "BIAS_CHALLENGES")
    familias = {}
    for clave, cuerpo in zip(sesgo.keys, sesgo.values):
        campos = {_constante(k): v for k, v in zip(cuerpo.keys, cuerpo.values) if k is not None}
        familias[_constante(clave)] = tuple(_constante(e) for e in campos["families"].elts)
    texto, ruta_cu = _texto("curriculum.py")
    arbol = ast.parse(texto)
    fundacion = _asignacion(arbol, "_FOUNDATION_CHALLENGES")
    for clave, cuerpo in zip(fundacion.keys, fundacion.values):
        campos = {_constante(k) for k in cuerpo.keys if k is not None}
        if "families" in campos:
            raise Inconsistencia("Un desafío de fundación declara families: revisar la matriz.")
        familias[_constante(clave)] = ()
    compuesto = _asignacion(arbol, "CHALLENGES")
    nombres = {v.id for v in compuesto.values if isinstance(v, ast.Name)}
    if nombres != {"BIAS_CHALLENGES", "_FOUNDATION_CHALLENGES"}:
        raise Inconsistencia(f"curriculum.CHALLENGES ya no es BIAS + FOUNDATION: {nombres}.")
    return dict(sorted(familias.items())), (ruta_cc, ruta_cu)


def leer_casos():
    texto, ruta_cl = _texto("clinical_cases.py")
    casos = {}
    for nodo in ast.walk(ast.parse(texto)):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == "_case"
                and len(nodo.args) >= 2 and all(isinstance(a, ast.Constant) for a in nodo.args[:2])):
            casos[nodo.args[0].value] = nodo.args[1].value
    texto, ruta_hc = _texto("hypoglycemia_catalog.py")
    arbol = ast.parse(texto)
    try:
        familia = _constante(_asignacion(arbol, "FAMILY"))
    except Inconsistencia:
        familia = "hypoglycemia"
    plantillas = _asignacion(arbol, "_TEMPLATES")
    orden_banco = [_constante(e) for e in _asignacion(arbol, "BANK_ORDER").elts]
    por_mecanismo = {}
    for clave, cuerpo in zip(plantillas.keys, plantillas.values):
        campos = {_constante(k): v for k, v in zip(cuerpo.keys, cuerpo.values) if k is not None}
        por_mecanismo[_constante(clave)] = _constante(campos["id"])
    for mecanismo in orden_banco:
        casos[por_mecanismo[mecanismo]] = familia
    texto, ruta_c14 = _texto("c14_review.py")
    orden = [_constante(k) for k in _asignacion(ast.parse(texto), "DRAFT").keys]
    return casos, orden, (ruta_cl, ruta_hc, ruta_c14)


# --- el borrador ---------------------------------------------------------------------------
_CELDA = re.compile(r"^(YES|NO|UNCERTAIN)(?: \((TDFC-\d+(?:, TDFC-\d+)*)\))?$")


def leer_borrador():
    texto = BORRADOR.read_text(encoding="utf-8")
    inicio, fin = texto.index("<!-- estados-tdfc:inicio -->"), texto.index("<!-- estados-tdfc:fin -->")
    filas = [linea for linea in texto[inicio:fin].splitlines() if linea.startswith("| `")]
    borrador = {}
    for linea in filas:
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) != 2 + len(TDFC):
            raise Inconsistencia(f"Fila mal formada: {linea}")
        caso, familia = celdas[0].strip("`"), celdas[1]
        estados = {}
        for objetivo, celda in zip(TDFC, celdas[2:]):
            encontrado = _CELDA.match(celda)
            if not encontrado:
                raise Inconsistencia(f"{caso} {objetivo}: celda no reconocida «{celda}».")
            estado, letras = encontrado.group(1).lower(), encontrado.group(2)
            decisiones = tuple(letras.split(", ")) if letras else ()
            if (estado == "uncertain") != bool(decisiones):
                raise Inconsistencia(f"{caso} {objetivo}: una duda cita su decisión, y sólo una duda la cita.")
            estados[objetivo] = {"estado": estado, "decisiones": decisiones}
        borrador[caso] = {"familia": familia, "estados": estados}
    return borrador


# --- derivación (como c14_review.derive) ----------------------------------------------------
def cubre(caso, objetivo):
    return [clave for clave, d in DECISIONES.items() if (caso, objetivo) in d["approve"]]


def derivar(borrador, respuestas):
    """Estado de cada celda según las respuestas; el borrador donde no hay respuesta."""
    filas = {}
    for caso, fila in borrador.items():
        filas[caso] = {}
        for objetivo, celda in fila["estados"].items():
            claves = cubre(caso, objetivo)
            if not claves:
                filas[caso][objetivo] = celda["estado"]
                continue
            resultados = [DECISIONES[c][respuestas[c]][(caso, objetivo)] if respuestas.get(c) else "uncertain"
                          for c in claves]
            filas[caso][objetivo] = ("yes" if "yes" in resultados else
                                     "uncertain" if "uncertain" in resultados else "no")
    return filas


def conteo(filas, objetivo):
    c = Counter(fila[objetivo] for fila in filas.values())
    return c["yes"], c["no"], c["uncertain"]


# --- verificación cruzada -------------------------------------------------------------------
def verificar(borrador, casos_banco, orden, c14, tdfc=None):
    problemas = []
    if tdfc is not None:
        aprobado = derivar(borrador, RECOMENDADO)
        if set(tdfc) != set(borrador) - set(PENDIENTES):
            problemas.append(f"TDFC declarado en otros casos: {sorted(set(tdfc) ^ (set(borrador) - set(PENDIENTES)))}.")
        for caso, filas in tdfc.items():
            for objetivo, fila in filas.items():
                if fila["estado"] != aprobado.get(caso, {}).get(objetivo):
                    problemas.append(f"{caso} {objetivo}: el banco declara {fila['estado']} y las decisiones "
                                     f"aprobadas derivan {aprobado.get(caso, {}).get(objetivo)}.")
    if len(borrador) != 31:
        problemas.append(f"El borrador tiene {len(borrador)} casos, no 31.")
    if set(borrador) != set(casos_banco):
        problemas.append(f"Casos distintos del banco: {sorted(set(borrador) ^ set(casos_banco))}.")
    for caso, fila in borrador.items():
        if casos_banco.get(caso) != fila["familia"]:
            problemas.append(f"{caso}: familia {fila['familia']} en el borrador, {casos_banco.get(caso)} en el banco.")
    if list(borrador) != orden:
        problemas.append("El orden del borrador no es el de c14_review.DRAFT.")
    for caso, fila in borrador.items():
        for objetivo, celda in fila["estados"].items():
            if tuple(cubre(caso, objetivo)) != celda["decisiones"]:
                problemas.append(f"{caso} {objetivo}: el borrador cita {celda['decisiones']} y el script "
                                 f"{tuple(cubre(caso, objetivo))}.")
    if len(c14) != 31 or (c14.get("acs_54m_inferior") or {}).get("estado") != "no":
        problemas.append("C14_DECLARATIONS ya no son las 31 filas del ciclo 7 (acs_54m_inferior NO).")
    if problemas:
        raise Inconsistencia("\n".join(problemas))


# --- la matriz --------------------------------------------------------------------------------
def celdas_matriz(borrador, familias, c14, c4_declarado=True, tdfc=None):
    matriz = {}
    for caso, fila in borrador.items():
        valores = {}
        for desafio, fams in familias.items():
            valores[desafio] = "TARGET" if fila["familia"] in fams else "NOT REVIEWED"
        for objetivo in TDFC:
            valores[objetivo] = "DRAFT " + fila["estados"][objetivo]["estado"].upper()
            if tdfc is not None and objetivo != "C4":
                # Ciclo 8: el banco declara TD1, F1, C1 y C3; un caso pendiente conserva la transición.
                declarado_tdfc = (tdfc.get(caso) or {}).get(objetivo)
                valores[objetivo] = ("NOT REVIEWED" if declarado_tdfc is None
                                     else "DECLARED YES" if declarado_tdfc["estado"] == "yes" else "DECLARED NO")
        if c4_declarado:
            # Ciclo 7 (TDFC-7/8 y H4): el banco declara C4 NO en todos sus casos.
            valores["C4"] = "DECLARED NO"
        declarado = c14.get(caso)
        valores["C14"] = ("NOT REVIEWED" if declarado is None
                          else "DECLARED YES" if declarado["estado"] == "yes" else "DECLARED NO")
        matriz[caso] = valores
    return matriz


def _tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def escribir(borrador, familias, c14, fuentes, tdfc=None):
    matriz = celdas_matriz(borrador, familias, c14, tdfc=tdfc)
    columnas = list(familias) + list(TDFC) + ["C14"]
    ahora = derivar(borrador, {})
    aprobado = derivar(borrador, RECOMENDADO)
    rechazado = derivar(borrador, TODO_RECHAZADO)

    lineas_matriz = [(f"`{caso}`", borrador[caso]["familia"], *(CODIGO[matriz[caso][c]] for c in columnas))
                     for caso in borrador]
    totales = []
    for columna in columnas:
        c = Counter(matriz[caso][columna] for caso in matriz)
        totales.append((columna, *(c.get(v, 0) for v in VALORES), sum(c.values())))
    proyecciones = []
    for objetivo in TDFC:
        proyecciones.append((objetivo, "{} / {} / {}".format(*conteo(ahora, objetivo)),
                             "{} / {} / {}".format(*conteo(aprobado, objetivo)),
                             "{} / {} / {}".format(*conteo(rechazado, objetivo))))
    dudas = []
    for clave, decision in DECISIONES.items():
        celdas = ", ".join(f"`{caso}` {obj}" for caso, obj in decision["approve"])
        dudas.append((clave, decision["titulo"], celdas))
    sin_familias = [d for d, fams in familias.items() if not fams]
    objetivo_por_caso = sum(1 for caso in matriz if any(matriz[caso][d] == "TARGET" for d in familias))

    partes = [
        "# Matriz de oportunidades del banco · caso × objetivo",
        "",
        "Ciclo 5 del AI Advisor · instrucción docente 59D · 2026-09-28. Actualizada en el ciclo 7 (C14 revisado",
        "en los 31 casos y C4 declarado NO en todos), en el ciclo 8 (TD1, F1, C1 y C3 declarados en 30 casos) y",
        "en el ciclo 9 (`acs_54m_inferior` declarado al cerrarse DF-20: los 31 casos).",
        "",
        "**Generado por `generar_matriz.py`; no se edita a mano.**",
        "",
        "- **Qué es.** Cobertura de oportunidades de observación que ofrece el banco de 31 casos, objetivo por",
        "  objetivo. **No es cobertura del constructo de un residente** y no calcula competencia de nadie.",
        "- **De dónde sale.** TD1 a C3 son lo que el banco declara desde el ciclo 8",
        "  (`tdfc_declarations.DECLARATIONS`, derivado de `BORRADOR_TDFC.md` y de TDFC-1 a 6 y 8, aprobadas",
        "  conceptualmente en el ciclo 7). C4 y C14 son lo que el banco declara (`case_assessment_bank.C4_DECLARATIONS`",
        "  y `C14_DECLARATIONS`). Los Decision Challenges salen de `curriculum.CHALLENGES`: un desafío es TARGET",
        "  en los casos de sus `families`.",
        "- **`acs_54m_inferior`** declara TD1, F1, C1 y C3 desde el ciclo 9: DF-20 se cerró sin cambios en el",
        "  caso (2026-09-29), y sus oportunidades no descansan en el POCUS.",
        "",
        "## Leyenda",
        "",
        _tabla(("Código", "Valor", "Qué significa aquí"), [
            ("TARGET", "TARGET", "La familia del caso está en las `families` del desafío: el encuentro generado "
                                 "para ese desafío puede usar este caso."),
            ("DECL+", "DECLARED YES", "El caso declara la oportunidad, con su procedencia (decisión docente)."),
            ("DECL−", "DECLARED NO", "El caso declara que no la hay: no evaluable, nunca una falla."),
            ("NR", "NOT REVIEWED", "Nadie la declaró. En un desafío: no se ofrece fuera del encuentro generado "
                                   "para él."),
            ("DRAFT+", "DRAFT YES", "Este borrador propone oportunidad."),
            ("DRAFT−", "DRAFT NO", "Este borrador propone que no la hay."),
            ("DRAFT?", "DRAFT UNCERTAIN", "Depende de una decisión clínica (TDFC-1 a TDFC-8)."),
        ]),
        "",
        "## Matriz",
        "",
        _tabla(("Caso", "Familia", *columnas), lineas_matriz),
        "",
        "## Totales por objetivo",
        "",
        _tabla(("Objetivo", *VALORES, "Casos"), totales),
        "",
        f"- **Desafíos sin `families`:** {', '.join(sin_familias)}. Se sirven con encuentros generados",
        "  (`encounter_generator.SUPPORTED_CHALLENGES`); ningún caso del banco es su TARGET.",
        f"- **Casos que son TARGET de al menos un desafío:** {objetivo_por_caso} de {len(matriz)}.",
        "- **C14:** {} DECLARED YES, {} DECLARED NO y {} NOT REVIEWED (ciclo 7: `acs_54m_inferior` NO).".format(
            *(sum(1 for caso in matriz if matriz[caso]["C14"] == v)
              for v in ("DECLARED YES", "DECLARED NO", "NOT REVIEWED"))),
        "- **C4:** {} DECLARED NO: la razón es del entorno de observación, no de los casos (TDFC-7/8, H4).".format(
            sum(1 for caso in matriz if matriz[caso]["C4"] == "DECLARED NO")),
        "",
        "## Dudas del borrador y la decisión que las resuelve",
        "",
        _tabla(("Decisión", "Pregunta", "Celdas DRAFT UNCERTAIN"), dudas),
        "",
        "## Lo que dejan las respuestas (YES / NO / UNCERTAIN, sobre 31 casos)",
        "",
        "Derivado con la misma lógica que `c14_review.derive`: una celda dudosa toma el resultado de su",
        "decisión. «Aprobado» es lo que el docente aprobó (ciclo 7, §28); el banco lo declara en los 31 casos",
        "desde el ciclo 9.",
        "",
        _tabla(("Objetivo", "Borrador", "Aprobado (TDFC-1 a 8)", "Si se hubieran rechazado las 8"),
               proyecciones),
        "",
        "## Fuentes leídas",
        "",
        "Leídas como texto y analizadas con `ast`: no se importó ni ejecutó ningún módulo del repositorio.",
        "",
        _tabla(("Archivo", "sha256 (12)"), [(f"`{ruta.relative_to(REPO)}`", _huella(ruta)) for ruta in fuentes]
               + [("`BORRADOR_TDFC.md` (esta carpeta)", _huella(BORRADOR))]),
        "",
    ]
    SALIDA.write_text("\n".join(partes), encoding="utf-8")
    return ahora, aprobado, rechazado


def main():
    c14, ruta_c14 = leer_c14()
    leer_c4()
    tdfc, ruta_tdfc = leer_tdfc()
    familias, rutas_desafios = leer_desafios()
    casos, orden, rutas_casos = leer_casos()
    borrador = leer_borrador()
    verificar(borrador, casos, orden, c14, tdfc)
    fuentes = [ruta_c14, ruta_tdfc, *rutas_desafios, *rutas_casos]
    ahora, aprobado, rechazado = escribir(borrador, familias, c14, fuentes, tdfc)
    print(f"Escrito: {SALIDA}")
    print("Objetivo  borrador(Y/N/U)  aprobado(Y/N/U)  rechazado(Y/N/U)")
    for objetivo in TDFC:
        print(f"{objetivo:<8}  {conteo(ahora, objetivo)}  {conteo(aprobado, objetivo)}  {conteo(rechazado, objetivo)}")
    total = Counter(celda for fila in ahora.values() for celda in fila.values())
    print(f"Total borrador: {dict(total)} de {sum(total.values())} combinaciones")
    c = Counter(d["estado"] for d in c14.values())
    print(f"C14 declarado: {dict(c)}; no revisado: {sorted(set(casos) - set(c14))}")


if __name__ == "__main__":
    main()
