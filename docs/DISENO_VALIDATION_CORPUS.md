# Diseño · corpus de validación bilingüe EN/ES, independiente del de desarrollo

Ciclo 2 del AI Advisor, punto 6 de la aprobación docente del 2026-09-27 (DF-6).

**Estado: PROPUESTA.** No se construyó nada ni se usaron datos reales de
residentes.

## 1. Para qué

**Qué cambia respecto del corpus de ensayo.** El corpus de ensayo (`tanda20` y
`tanda20_en`) es el corpus con el que se ajustó el lector: su 96/96 es una línea
base de regresión, no una tasa (`docs/MEDICION_RECONOCIMIENTO_ORDENES.md`).

**Qué debe medir este corpus**, sobre textos que el desarrollo nunca vio:

- cómo generaliza el lector (§57 y §90);
- órdenes y las cuatro categorías de razonamiento;
- en inglés y en español, con calidad comparable (§56).

## 2. Unidad y anotación

**Una entrada** es lo que un residente escribiría en un turno, en un idioma.

**Qué acompaña a cada entrada:**

- **Tarjeta de intención**, que es el estándar de oro: las acciones que el
  escritor quiso ordenar, con sus parámetros (tipo, fármaco, dosis, unidad, vía,
  ritmo, volumen, destino, momento de reevaluación).
- **Categorías marcadas por el propio escritor**, sobre su propio texto: modelo
  de trabajo, prioridad, efecto esperado, qué y cuándo reevaluar, y contingencia.
  Si no escribió una categoría, queda vacía.
- **Contexto mínimo** cuando el sentido lo exige: caso del banco, minuto,
  infusiones activas. Por ejemplo, «súbela a 0.2» sólo tiene sentido con una
  infusión corriendo. Esas entradas son como máximo el 20 %.

## 3. Tamaño y composición inicial

**Tamaño: 60 intenciones × 2 redacciones × 2 idiomas = 240 entradas**, 120 por
idioma.

**Qué permite ese tamaño.** Con 120 entradas por idioma, una tasa de falla
cercana al 5 % se estima con un IC 95 % de alrededor de ±4 puntos. Alcanza para
ver brechas grandes entre idiomas y clases de falla frecuentes. No alcanza para
diferencias finas; si hacen falta, el corpus crece en versiones siguientes.

| Categoría (por idioma) | Entradas |
|---|---|
| Orden simple | 20 |
| Varias órdenes en una entrada | 20 |
| Abreviaturas y taquigrafía clínica (IV/ev, VO/PO, SF/NS, nbz, NRB…) | 15 |
| Dosis, unidades y vías (mg/kg, mcg/kg/min, mL/h, concentraciones) | 15 |
| Errores de tipeo razonables | 10 |
| Reevaluación con qué y cuándo | 10 |
| Razonamiento explícito: modelo, expectativa y contingencia | 20 |
| Paráfrasis de una misma intención (3–4 maneras) | 10 |

**Cobertura.** Las 12 familias del banco, incluida trauma, que el corpus de
ensayo no tiene, con al menos 8 entradas por familia e idioma. La mitad de las
entradas de razonamiento incluyen además una orden, para medir que la orden no
quede registrada como modelo (DF-7).

## 4. Construcción

1. **Tarjetas.**
   - **Quién:** un docente, o un clínico que no haya trabajado en el lector.
   - **Qué:** escribe las 60 tarjetas de intención en forma estructurada y
     neutra, sin frases modelo. Por ejemplo: «iniciar noradrenalina a 0.1
     mcg/kg/min y reevaluar PAM en 10 min».
2. **Redacción independiente.**
   - **Quién:** dos escritores por idioma, nativos, que no escribieron `tanda20`
     y que no ven el código, las pruebas ni las reglas del lector.
   - **Qué:** cada uno redacta cada tarjeta como la escribiría en urgencias. Los
     escritores de inglés y de español trabajan por separado: no se traduce, se
     escribe.
3. **Anotación.**
   - Cada escritor marca en su texto las categorías que escribió.
   - Un segundo revisor controla el 20 % y se informa la concordancia.
4. **Congelamiento.**
   - El corpus se guarda versionado (`validation/corpus_v1`), con huella sha256
     y fecha.
   - Cada medición registra el commit que midió.

## 5. Evitar la contaminación

- **Mitad visible y mitad sellada.**
  - La mitad visible sirve para diagnosticar clases de falla.
  - La mitad sellada sólo se informa como métricas agregadas.
  - Nadie la lee para corregir el lector, tampoco el AI Advisor.
- **Del corpus a los tests sólo pasan clases.** Una falla se corrige por su
  clase, y la prueba se escribe con frases nuevas, nunca copiadas del corpus
  (§57). Es la regla que ya sigue `test_reasoning_fidelity_classes.py`.
- **Dónde vive la mitad sellada.** Fuera del repositorio, en custodia del
  docente. La herramienta la recibe como ruta en el momento de medir.
- **Si se usa para ajustar, se quema.** Queda marcada y se reemplaza por una
  nueva en la versión siguiente.
- **Los escritores no son los desarrolladores**, y no reciben retroalimentación
  sobre qué leyó o no el lector.

## 6. Métricas

Todas se dan por idioma, con su diferencia EN − ES e IC 95 %, emparejadas por
tarjeta, por familia y por categoría (§90).

| Métrica | Definición |
|---|---|
| Unrecognized order rate | Entradas con al menos una orden de la tarjeta que el lector no produjo |
| Partial interpretation rate | Se produjo la acción pero con un parámetro distinto (dosis, unidad, vía, ritmo, destino), o faltó parte de un conjunto |
| Incorrect execution rate | Se ejecutó una acción que la tarjeta no pedía, o de otro tipo |
| Unnecessary clarification rate | Retenciones o preguntas en entradas que la tarjeta considera completas (§92). Proxy de *repeated order rate* |
| Fidelidad de las categorías | Una categoría que no cita palabras del escritor; una orden registrada como modelo; un modelo escrito que no se registró |
| Paridad EN/ES | Diferencia de cada métrica entre idiomas sobre las mismas tarjetas |

## 7. Ejecución y costo

- **Herramienta.**
  - Un modo `--corpus FILE` en `tools_order_reading.py`: lee cada entrada por el
    mismo camino que la página (lector y extracción de razonamiento) y la compara
    con su tarjeta.
  - Es determinista, sin IA ni costo de proveedor.
  - Costo: una sesión de trabajo.
- **Tiempo humano estimado** (unas 9 a 12 h en total, entre 3 y 5 personas):
  - tarjetas: unas 2 h de un docente;
  - redacción: unas 2 h por escritor (4 escritores);
  - anotación y revisión: unas 3 h.
- **Datos:** sintéticos, sin datos de pacientes ni de residentes (§76). Ninguna
  entrada identifica a quien la escribió.

## 8. Decisiones necesarias (DF-6)

1. ¿Se aprueba el diseño y su tamaño inicial (240 entradas)?
2. ¿Quién escribe las tarjetas y quiénes redactan en cada idioma?
3. ¿Dónde se custodia la mitad sellada?
4. **Umbrales de aceptación.** No se proponen antes de la primera medición:
   fijarlos sin datos sería arbitrario (§48). Se discuten con el primer resultado
   (METHODOLOGICAL REVIEW).
5. **Encuentros reales de residentes.** Siguen fuera hasta una autorización
   posterior con revisión de privacidad.
