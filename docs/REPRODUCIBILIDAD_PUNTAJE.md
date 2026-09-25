# Reproducibilidad del puntaje · 2026-09-24

Pendiente §10/§11 del informe de la tanda: dos corridas del mismo guion obtuvieron
**13/15 y 9/15**. Este documento separa lo que se pudo demostrar aquí, sin llamadas
pagadas, de lo que requiere medir con la clave.

## 1. ¿Variabilidad del encuentro o del evaluador?

**El encuentro es determinista.** Los 12 guiones del piloto (`tools_rubric_runs.py`),
jugados tres veces cada uno por el intérprete y el motor de producción, dan registros
**idénticos byte a byte** (12/12). Se comprueba gratis con:

```
python tools_rubric_reproducibility.py --check-encounter opioid_67f
```

y queda como prueba (`test_tools_rubric_reproducibility.py::test_the_same_script_is_the_same_encounter`,
`test_a_score_rests_on_what_the_record_holds.py::test_same_script_same_record`).

Consecuencia: con el mismo código, un mismo guion no puede producir dos encuentros
distintos. Una diferencia de puntaje entre dos corridas del mismo guion viene de:

1. **el evaluador** (el modelo leyendo el mismo registro de dos maneras), o
2. **una versión distinta** del código o del prompt entre una corrida y otra (cada
   propuesta guardada nombra su `prompt_version` y su `source_hash`).

**Evidencia de variabilidad del evaluador ya registrada en el repositorio.** En la
verificación del 2026-09-23 (commit `8a1fee2`) se repitieron las mismas órdenes del
caso `opioid_67f`: el modelo nombró la misma omisión en la evidencia en contra las dos
veces, y puntuó D2 con **3 y con 2**. Mismo registro, dos lecturas.

**Lo que no se pudo comparar aquí.** Las dos corridas de 13/15 y 9/15 viven en la base o
en `local-data/`, fuera de este contenedor. Para compararlas dominio por dominio, con sus
registros al lado:

```
python tools_rubric_reproducibility.py --compare corrida_a.json corrida_b.json
```

Responde, sin costo: si leyeron **el mismo registro** (`source_hash`), las versiones de
prompt/rúbrica/modelo de cada una, el puntaje y la oportunidad de cada dominio, el
veredicto de cada evento, los totales, y —si los registros difieren— **la primera
decisión donde se separaron** y qué ventanas de dominio estaban abiertas en cada uno.

## 2. Medir la variabilidad del evaluador: traza congelada, N lecturas

`tools_rubric_reproducibility.py --case <guion> --times N --yes` (o `--record` con un
registro guardado) hace **N solicitudes independientes** sobre el **mismo** registro
congelado, con la misma rúbrica, prompt, esquema y modelo:

- Nada se reutiliza ni se cachea: cada lectura es una solicitud nueva; una propuesta
  ligada a otro registro anula la comparación; las solicitudes al proveedor se cuentan y
  no pueden pasar de N.
- Informa por dominio todos los puntajes, el rango, el acuerdo y la oportunidad; por
  evento, todos los veredictos; los totales si se aceptara todo lo propuesto; y las marcas
  que el registro levantó en cada propuesta.
- **Sólo declara acuerdo si todas las lecturas coincidieron.** Si no, nombra los dominios
  que variaron y el rango del total ajustado. Una lectura fallida se informa y no se
  reemplaza.

**No se ejecutó**: este entorno no tiene clave ni acceso a `api.openai.com`. Costo de la
medición mínima útil: 5 solicitudes sobre un registro (por ejemplo `opioid_67f`), o 10
sobre dos registros. Queda para cuando haya presupuesto autorizado disponible; no se usó
presupuesto nuevo.

## 3. Ambigüedades de criterio y anclaje corregidas

| Ambigüedad | Corrección | Dónde |
|---|---|---|
| El modelo decidía qué eventos mencionar | Veredicto obligatorio por cada evento definido | prompt de rúbrica 1.1 (`27490f7`) |
| Oportunidad de actuar implícita | Oportunidad por dominio (observada / sin oportunidad / registro insuficiente / limitación del simulador); cualquier otra que «observada» obliga a «no evaluable» | prompt 1.1 |
| Ventanas y órdenes ejecutadas leídas por el modelo | Hechos deterministas del registro (órdenes ejecutadas con su minuto, ventanas abiertas o no) enviados al modelo y mostrados al docente | `rubric_screening.py` |
| Un nivel leído «por impresión» | Anclas acumulativas: se nombra el nivel más alto cuyos elementos están todos en el registro y, en `next_level_gap`, lo que falta para el siguiente | prompt 1.1 |
| «Nombrar la omisión y no dejar que mueva el número» (D2: 3 y 2) | Marca determinista: **máximo propuesto nombrando algo que falta**, o **nivel bajo el máximo sin nombrar qué falta** | `rubric_screening.anchor_flags` (hoy) |
| Citas del residente no verificadas | Marca determinista: **palabras citadas que no están en la decisión citada** (traducción, paráfrasis u otra decisión) y **minuto que no es el de la decisión**; el prompt pide citas textuales, en el idioma del residente | `anchor_flags` + prompt 1.1 (hoy) |
| «No evaluable» confundido con cero | Regla explícita en el prompt; marca «puntuado aunque su ventana nunca se abrió» | prompt 1.1, `proposal_flags` |

Las marcas **no cambian ninguna propuesta ni ninguna decisión**: aparecen al docente
(pantalla y PDF docente) bajo «Revisar antes de decidir». Desde hoy **no aparecen en la
copia del residente**, que lee una decisión ya tomada.

Nada de esto fija un puntaje ni lo empuja hacia 13 ni hacia 9: el objetivo es que cada
número quede sustentado en evidencia verificable de la traza y que un desacuerdo entre
el número y su propia justificación quede a la vista.

## 4. Decisión docente 11 (2026-09-25): medir primero, sin adaptar el criterio

«Medir primero, pero no adaptar después el criterio para que “pase”». La herramienta
sigue ese orden y no fija ningún umbral:

1. **Primero, qué leyeron las dos corridas.** `--compare corrida_a.json corrida_b.json`
   abre con una tabla de identidad —registro (`source_hash`), versión de rúbrica, versión
   del prompt, modelo y versión de cobertura— y una conclusión: mismo registro y mismas
   versiones («toda diferencia es la lectura del evaluador»), mismo registro con otra
   versión («no se puede atribuir sólo al evaluador») u otro registro («los encuentros
   mismos difieren»; nombra la primera decisión donde se separan si están los dos
   registros). `--json` da lo mismo como JSON.
2. **Después, registros idénticos leídos de nuevo, con desempeños distintos.** `--case`
   se puede repetir: por ejemplo `--case opioid_35m --case opioid_67f --times 5` (un
   manejo competente y un alta insegura del mismo tipo de caso) o
   `--case asthma_24f --case asthma_49m`. Cada registro se congela y se lee N veces.
3. **Comparación por dominio, total, eventos críticos y no evaluable.** Cada resumen da,
   por lectura, los puntajes de cada dominio con su oportunidad, los veredictos de cada
   evento, el total si se aceptara todo, los eventos críticos propuestos y cuántos
   dominios quedaron «no evaluable».
4. **Una diferencia en el total se explica antes de comparar residentes.** Si el total
   difiere entre lecturas del mismo registro —o si una lectura puntuó un dominio que la
   otra dejó «no evaluable», de modo que los totales no son totales de lo mismo— el
   resumen dice: «Until this difference is explained, the score is not used to compare
   residents», y la descompone: qué dominios se leyeron distinto (con los puntos de cada
   uno), qué eventos cambiaron de veredicto y cuánto movió la penalización. La
   herramienta explica **de qué está hecha** la diferencia, nunca cuál debió ser el
   puntaje. Una diferencia de cuatro puntos, como 13/15 frente a 9/15, queda así
   descompuesta para el docente.
5. **Cinco a diez solicitudes son exploración, no validación.** Una invocación envía
   como máximo 10 solicitudes en total, sumando todos los registros (5 × 2, o 10 × 1), y
   cada resumen termina con «Exploration, not validation: N reading(s) of M record(s)».
6. **El gasto de estas llamadas se registra aparte de los encuentros.** Cada lectura se
   escribe al empezar y al terminar, con las solicitudes que realmente envió al
   proveedor, en `local-data/paid_runs/reproducibility/ledger.jsonl`, con
   `"kind": "evaluator_reading"` y `"paid_encounter": false`. No es el registro de la
   tanda (que cuenta sólo encuentros pagados, hasta 40) ni descuenta de él.
   `--spent` suma lo gastado; una lectura que empezó y no terminó cuenta como gastada.

Pruebas: `test_tools_rubric_reproducibility.py` (identidad primero, descomposición,
«no evaluable» frente a puntuado, lecturas que coinciden, nota de exploración, registro
aparte, límite de 10).

## 5. Pendiente real

- **Bloqueado por acceso**: comparar las dos corridas originales (13/15 y 9/15) con
  `--compare`. Viven en la base de la app o en `local-data/` de otra máquina; este
  entorno no tiene ni la base ni esos archivos.
- **Bloqueado por clave**: la exploración de §2/§4 (5-10 solicitudes). Este entorno no
  tiene clave del proveedor ni acceso a `api.openai.com`; no se envió ninguna solicitud
  y el registro de gasto de esta herramienta está vacío.
- Decisión docente, **después** de medir: qué dispersión entre lecturas se considera
  aceptable. Hasta que se mida y se explique, **no se declara estabilidad** y el puntaje
  no se usa para comparar residentes.
