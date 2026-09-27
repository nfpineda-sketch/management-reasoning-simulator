# Medición EN/ES del lector de órdenes · corpus de ensayo

Ciclo 1 del AI Advisor, quick win QW1, aprobado por el docente el 2026-09-27:
«medición determinista del reconocimiento de órdenes EN/ES utilizando
exclusivamente el corpus de ensayo existente».

- **Código medido:** commit `3719b0c`. La app no se modificó.
- **Herramienta:** `tools_order_reading.py`, con semilla fija 3000.
- **Corpus:** los 20 guiones de `tanda20.py` y su versión en inglés,
  `tanda20_en.py`.
- **Ejecución:** los 40 recorridos pasaron por la página real (`app.py`), sin
  clave de proveedor y con una base temporal.
- **Datos reales:** no se leyó ningún encuentro real de residentes.

## Conclusión

1. **Reconocimiento de órdenes: el corpus es insuficiente para una comparación
   EN/ES útil.** Da 96 de 96 en ambos idiomas, pero no es una tasa real.
   - Es el mismo corpus con el que se ajustó el lector
     (`docs/TANDA_20_ESCENARIOS.md` §2).
   - `test_the_twenty_in_english.py` ya exige que cada orden produzca los
     mismos tipos de acción en los dos idiomas.
   - Por eso el resultado es una línea base de regresión dentro de la muestra
     de ajuste, no una estimación de cuántas órdenes reales se leen mal.
   - Según la instrucción, esta parte se detuvo aquí sin ampliar la fuente de
     datos. Es la decisión pendiente DF-6 en `docs/COLA_DECISIONES_AI_ADVISOR.md`.
2. **Razonamiento que el Trace atribuye al residente: la comparación sí fue útil.**
   - Esa capa (las cuatro categorías) no estaba cubierta por el ajuste ni por
     aquel test.
   - En 6 de 119 decisiones los dos idiomas registran algo distinto.
   - Aparecen defectos deterministas de fidelidad, más frecuentes en español:
     texto cambiado, palabras truncadas y órdenes guardadas como «modelo de
     trabajo».
   - Es un hallazgo CRITICAL según la §3 del charter (fidelidad del Management
     Trace). No se corrigió: queda como R-1 en la cola de decisiones.
3. **Costo:** US$0, con 0 llamadas de IA registradas en los 40 encuentros
   (`ai_calls_spent` = 0) y 0 decisiones interpretadas por IA. El cómputo fue de
   unos 13 minutos locales.

## Resultados · órdenes (acciones que el motor ejecuta)

| Métrica (charter §90) | Español | Inglés |
|---|---|---|
| Órdenes enviadas (pasos «order») | 96 | 96 |
| Decisiones ejecutadas | 96 | 96 |
| Órdenes no reconocidas (UNRECOGNIZED ORDER RATE) | 0 / 96 | 0 / 96 |
| Decisiones aceptadas sin acción leída | 0 | 0 |
| Retenciones previstas por el guion (las cuatro preguntas) | 19 | 19 |
| Retenciones no previstas (proxy de REPEATED ORDER RATE) | 0 | 0 |
| Misma firma de acciones que el otro idioma (tipo y todos los parámetros) | 94 / 96 | 94 / 96 |
| Encuentros completos con revisión | 20 / 20 | 20 / 20 |
| Minuto de cierre distinto del otro idioma | 0 | 0 |

Las 2 firmas distintas son del mismo tipo:

- Cuando el residente responde «Reassessment: PA, FC…», el lector registra el
  foco de la reevaluación como `general` en español y como `perfusion` en inglés
  («BP, HR…»).
- Ocurre en el guion 4, decisión 4, y en el guion 16, decisión 5.
- Hay una divergencia más en las indicaciones de alta del guion 7, decisión 10:
  - en inglés se pierde «urology follow-up»;
  - «return precautions for fever, vomiting or uncontrolled pain» queda como
    «return precautions for fever»;
  - en español se registran las dos cosas completas.

**No medible con este corpus:**

- **PARTIAL / INCORRECT EXECUTION RATE (UNKNOWN):** requieren un estándar de
  referencia orden por orden, que no existe.
- **REPEATED ORDER RATE (UNKNOWN):** requiere un residente que repita. El guion
  no repite; las retenciones no previstas son sólo el proxy.

## Resultados · razonamiento registrado (las cuatro categorías)

| Métrica | Español | Inglés |
|---|---|---|
| Categorías registradas como «dichas por el residente» (`stated`) | 192 | 191 |
| … cuyo texto no aparece en lo que escribió el residente | **4** | 0 |
| «Modelo de trabajo» declarado (`problem_representation`, `stated`) | 30 | 29 |
| … que en realidad es una orden | **5** | 1 |
| Decisiones con procedencia distinta del otro idioma | 6 / 119 | 6 / 119 |

Defectos, con causa verificada en el código (KNOWN) y reproducibles sin la
página:

1. **«im» pasa a «I'm».**
   - **Dónde:** `extract_explicit_reasoning`, en `app.py:5687`, reescribe como
     «I'm» todo «im», «i.m» o «IM» aislado antes de extraer el razonamiento.
   - **Efecto en español:** «Doy adrenalina 0.5 mg im» queda registrado como
     *modelo de trabajo dicho por el residente*: «Doy adrenalina 0.5 mg I'm».
   - **Casos:** guion 19, decisión 2; guion 12, decisiones 1 y 4.
   - **Inglés:** en la misma decisión arrastra correctamente la hipótesis
     previa.
   - **Consecuencias:** el Trace le atribuye al residente un razonamiento que no
     escribió (§62) y altera sus palabras.
   - **Alcance:** la misma reescritura se aplica a «IM» en inglés.
2. **Palabras terminadas en «-so» se truncan.**
   - **Dónde:** las expresiones de límite de cláusula (`app.py:5708`, `5727`,
     `5743`, `5807`, `5942`, `5976`, `5980`, `5985`) buscan `\s*,?\s*so\b` sin
     un límite de palabra antes de «so».
   - **Efecto:** «un IAM inferior con posible compromiso del VD» queda como «un
     IAM inferior con posible compromi».
   - **Casos:** guion 3, decisión 1.
   - **Alcance:** afecta a cualquier palabra terminada en «so» (compromiso,
     caso, paso, peso, ingreso, acceso, uso). En inglés afectaría a «also».
3. **Una orden ocupa el lugar del modelo de trabajo.**
   - En el guion 19, decisión 4, el residente escribe «Toma betabloqueador, por
     eso no responde».
   - El Trace registra como modelo de trabajo «inicio adrenalina en infusion a
     0.1 mcg/kg/min».
   - En inglés, para la misma decisión, registra «not responding».
   - El guion 3, decisión 2, guarda en ambos idiomas «Consulto a hemodinamia …
     porque es un IAM con supradesnivel», mitad orden y mitad razón. Es igual en
     los dos idiomas.
4. **Actualizaciones del modelo que un idioma capta y el otro no.** Hay déficits
   en ambos sentidos:
   - **Guion 11, decisión 4 (falla en español):** no registra «una PaCO2 normal
     en una crisis así es agotamiento, es falla ventilatoria inminente». Arrastra
     «una crisis asmática». El inglés sí la registra.
   - **Guion 10, decisión 6 (falla en inglés):** no registra «she takes
     glimepiride: it can fall again for hours, so she cannot go home». Arrastra
     «hypoglycemia from eating little». El español sí la registra.
   - **Guion 5, decisión 9 (falla en inglés):** no arrastra ningún modelo de
     trabajo; el español arrastra el previo.
   - **Guion 7, decisión 10 (discrepancia de criterio):** el inglés registra los
     hallazgos («Mild pain, afebrile…») como modelo de trabajo; el español
     arrastra «un cólico renal derecho».

Por qué importa: el brief docente, la propuesta de rúbrica y los PDF leen estas
categorías como razonamiento del residente (§33, §62). Los defectos 1 y 2 son
de clase, no de frase (§57), y su corrección natural ocurre en la fuente
(`extract_explicit_reasoning`).

## Qué dice y qué no dice esta medición

**Lo que dice:**

- **KNOWN:** con el código actual, sobre este corpus, ambos idiomas ejecutan las
  mismas órdenes, con las mismas dosis y los mismos minutos.
- **KNOWN:** los defectos del razonamiento listados existen y se reproducen.

**Lo que no dice:**

- **INFERRED:** que el lector falle poco con residentes reales. El corpus está
  ajustado a sí mismo (§57, «no optimizar para los test cases»).
- **Cobertura del corpus:** 11 de las 12 familias del banco; no incluye
  **trauma**. Son 20 de 31 casos.
- **UNKNOWN:** la frecuencia real de órdenes no leídas, parciales o mal
  ejecutadas en encuentros de residentes.
- **UNKNOWN:** la latencia percibida. Los tiempos del runner en proceso (unos
  20 s por guion completo) no representan la experiencia en el navegador.

## Reproducir

```
python tools_order_reading.py --play es all --out DIR --seed 3000
python tools_order_reading.py --play en all --out DIR --seed 3000
python tools_order_reading.py --compare DIR     # escribe DIR/comparison.json
```

La herramienta se niega a correr si ve una clave de proveedor. Sus funciones de
comparación tienen pruebas en `test_tools_order_reading.py`.
