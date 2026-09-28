# Guía de adjudicación · clases de error, ubicación, impacto y desacuerdos

Qué se evalúa: **el motor**, no a los médicos (§62). La pregunta es si el motor
entendió, ejecutó y registró lo que el médico escribió. Si la decisión fue
buena no se pregunta.

## Secuencia completa (§74)

No se ejecuta nada de esto hasta que existan documentos reales.

1. **Baseline.** Confirmar el baseline del piloto (`../PILOT_BASELINE.md`).
2. **Sorteo.** Hacer el sorteo development/sealed (`../SPLIT_PROCEDURE.md`).
3. **Anotación a ciegas** del subconjunto development (`annotation_guide.md`),
   más la segunda anotación del 20 %.
4. **Correr el motor** sobre development: `run`.
5. **Hoja de adjudicación:** `adjudicate --second annotation_second.csv`.
6. **Acuerdo entre anotadores:** `report --second annotation_second.csv`. Se
   guarda **antes** de resolver los desacuerdos.
7. **Resolver los desacuerdos** (abajo), adjudicar cada fila y hacer el
   reporte final: `adjudicate` y `report`, sin `--second`.
8. **Priorizar** los defectos por tipo, importancia clínica, frecuencia y
   reproducibilidad (§59); no por un porcentaje global.
9. **Correcciones.** La docencia las autoriza, se hacen **sólo con
   development**, y se congela una versión candidata.
10. **Sealed.** Recién entonces se corre el subconjunto sealed, con la
    candidata congelada, y se mide la generalización.

Los comandos están en `../tools/README.md`.

## Roles (carga mínima suficiente, VC-2)

| Rol | Quién | Qué hace |
|---|---|---|
| Anotador primario | un clínico | anota todas las entradas, a ciegas |
| Segundo anotador | otro clínico | anota a ciegas el 20 % fijo (`annotation_second.csv`) |
| Adjudicador | un tercer revisor, o los dos anotadores en consenso explícito y registrado | resuelve desacuerdos y completa las columnas de revisión |

## La hoja de adjudicación

`adjudicate` pone lado a lado la anotación, lo que hizo el motor y columnas
para la revisión. Lo que hizo el motor ocupa estas columnas:

- **`engine_status`:** qué se ejecutó, qué se retuvo y qué se preguntó.
- **`engine_read`:** acciones, lo que se hizo y cada plan no ejecutado con su
  tipo:
  - `PLAN (conditional)`: plan condicional;
  - `PLAN (repeat)`: instrucción de repetición;
  - `PLAN (advice)`: indicación al paciente, como el regreso o el control;
  - `PLAN (not modelled)`: medicamento indicado cuyo efecto no se modela;
  - `PLAN (prescription)`: receta para la casa.
- **`clarification_asked`, `reasoning_gate`:** si el motor preguntó algo o
  retuvo la orden para pedir razonamiento.
- **`stated_slots`:** el razonamiento que quedó en el Management Trace como
  escrito por el médico.
- **`plans_not_executed`:** los planes, con su tipo, en el orden del lector.
- **`auto_flags`:** avisos automáticos. Por ejemplo, un razonamiento con
  palabras que el médico no escribió, una orden registrada como modelo de
  trabajo o un desacuerdo entre anotadores.

## Qué se cuenta en cada fila

| Columna | Qué se escribe |
|---|---|
| `n_recognized` | cuántos ítems anotados reconoció el motor |
| `n_complete` | de esos, cuántos con todo lo escrito correcto: dosis, vía, dispositivo, parámetros y momento |
| `n_partial` | de esos, cuántos con algo perdido o distinto |
| `extra_or_wrong_execution` | S si el motor ejecutó algo no escrito, o algo equivocado: otro fármaco, otra dosis, o un plan ejecutado ahora |

**Qué cuenta como reconocido.** Un ítem cuenta si el motor lo **ejecutó** o si
lo **registró como plan del tipo correcto sin ejecutarlo**. Por ejemplo, un
`REPEAT` aparece como `PLAN (repeat)`; un `RETURN` o un `FOLLOWUP`, como
`PLAN (advice)`. Una orden condicionada aparece como `PLAN (conditional)` y no
corre ahora.

## Clase (§40)

La herramienta propone una clase a partir de los conteos
(`proposed_classification`). El adjudicador la confirma o la cambia en
`classification`.

| Clase | Cuándo |
|---|---|
| `CORRECT` | todo reconocido y completo, sin nada ejecutado de más, sin preguntas innecesarias y con el razonamiento escrito recogido fielmente |
| `PARTIAL_ENGINE_ERROR` | algo se entendió y algo se perdió, quedó incompleto, se preguntó sin necesidad o quedó mal en el Trace |
| `ENGINE_ERROR` | no se reconoció nada de lo escrito, o se ejecutó algo equivocado |
| `AMBIGUOUS_INPUT` | el texto admite más de una lectura razonable y el motor no eligió una de las aceptables |
| `ANNOTATION_DISAGREEMENT` | los anotadores no coinciden y el desacuerdo no se resolvió |

## Ubicación (§40)

Va en la columna `locus`. Se escribe cuando ayuda; en `AMBIGUOUS_INPUT` y en
`ANNOTATION_DISAGREEMENT` no se usa.

| Ubicación | Cuándo |
|---|---|
| `parsing` | la lectura del texto: ítems perdidos o incompletos |
| `execution` | se ejecutó algo equivocado o no escrito |
| `trace` | el Management Trace perdió o deformó el razonamiento escrito |
| `clarification` | se preguntó algo que el texto ya decía con claridad |
| `other` | lo demás |

## Impacto (§60)

Va en la columna `impact`. Es opcional, y conviene llenarlo en toda fila que no
sea `CORRECT`. **Sirve para ordenar el trabajo; nunca es un puntaje.**

| Impacto | Significa |
|---|---|
| `CRITICAL` | la interpretación podría cambiar sustancialmente el manejo o registrar falsamente una decisión importante |
| `HIGH` | se pierde o distorsiona una intención clínica relevante |
| `MEDIUM` | la intención principal se conserva, pero se pierde información en parte |
| `LOW` | problema cosmético o de formulación, sin impacto relevante en la ejecución ni en el Trace |

## Defecto conocido (§73)

Va en la columna `known_defect`.

- **Si coincide con un defecto conocido,** se escribe su ID (`KD-01`…), de
  `../manifests/known_defects.json` o `../KNOWN_DEFECTS.md`.
- **Si no coincide,** se deja en blanco: es una **falla nueva**.
- **Nunca se fuerza la coincidencia.**
- **Conducta por diseño.** Una conducta marcada así (`KB-01`: oxígeno sin flujo
  absoluto) tampoco es una falla nueva, y se escribe su ID.

## Desacuerdos entre anotadores (el 20 %)

1. **Guardar el acuerdo en bruto.** Con `--second`, la herramienta marca cada
   desacuerdo en `auto_flags` y el reporte muestra el acuerdo por campo.
   Guarde ese reporte primero.
2. **Resolver cada desacuerdo.** Lo decide un tercer revisor, o los dos
   anotadores en consenso explícito.
3. **Registrar la resolución.** Se escribe el valor final en `annotation.csv`,
   con `note: consensus` o `note: third reviewer`.
4. **Reporte final sin `--second`.** Un desacuerdo que siga sin resolver se
   clasifica `ANNOTATION_DISAGREEMENT`.

## Lo que nunca se hace

- **No se modifica el motor automáticamente con los datos** (§45). La
  secuencia es: dato → medida → falla → revisión → autorización → corrección →
  prueba en development → validación en datos no vistos.
- **No se cambia el baseline** para que una respuesta pase (§57).
- **No se abre ni se usa el subconjunto sealed durante el desarrollo** (§42).
  Una entrada sealed usada para corregir algo sale de la validación: se
  registra en `retired_entries` del manifiesto del corpus, como RETIRED FROM
  VALIDATION.
- **No se producen puntajes, rankings** ni comparaciones de médicos (§62).
