# PHASE2_AMENDMENT_1 · Forense de la certificación fallida y diseño del paquete formal

Rama `phase-2-amendment-1-respiratory-transmission`. Este documento es **sólo lectura y diseño**: no
actualiza ningún valor congelado, no regenera sondas ni goldens y no toca `derived.py`. La enmienda vive en
`d087cc3`; `phase-3-runtime-integration` fue restaurada por revert (`e1eb797`, mismo objeto tree que
`258e71f`).

## 1 · Qué falló, exactamente

Certificación completa sobre `d087cc3` (corrida válida, huella estable): **11 092 pruebas · 325 fallas ·
287 errores · 93 omitidas · 1 xfail**. Las 612 incidencias viven en 53 archivos (1 835 pruebas).

**Línea base real** (S4): los mismos 53 archivos más 5 de salud, sobre el árbol restaurado (≡ `258e71f`):
**1 890 pasaron, 0 fallas, 0 errores**. Cruzando identificador por identificador: las **612 son
`NEW_FROM_AMENDMENT`**; ninguna es preexistente ni mixta. (La revisión adversarial informó fallos «previos»
con una línea base simulada parcheando lecturas de archivo; la corrida real no los reproduce.)

La ecuación no es la causa: `None` y `1.0` dan resultados idénticos bit a bit e iguales a los previos,
ningún perfil comprometido cambia, y la serialización hace ida y vuelta. Lo confirmó también la revisión
independiente (809 100 pares IEEE-754 sin una diferencia).

## 2 · 612 incidencias, 6 contratos raíz

| # | Contrato raíz | Dónde vive | Qué congela | Propósito | Incidencias |
|---|---|---|---|---|---|
| C1 | **Cadena de reconstrucción histórica** | `clinical_core/distributive_tone.py` (`REVERSAL`, `CORE_AT_P2V1`, `proved`, `p2v1_text`), consumida por 15 módulos de etapa y 32 archivos de prueba vía `chain(patch)` / `tree(patch)` | inserción textual declarada + SHA del texto reconstruido | REPRODUCIBILITY_GUARD | **466** |
| C2 | **Condición de digesto del runtime** | `runtime_shadow_evidence.phase2_digest_now() == runtime_shadow.PHASE2_DIGEST` (`runtime_authority.py:541`; evidencia, líneas 403 y 545) | digesto del árbol vivo de `clinical_core` | CURRENT_ACTIVE_CORE_GUARD | **131** |
| C3 | Digestos de congelación de etapa | `test_clinical_core_{systemic_stress,distributive_tone,tone_domain,closure_guard}::test_the_package_is_frozen` y afines | digesto | HISTORICAL (tres) + cabeza P2X-1A (uno) | 10 |
| C4 | Goldens | golden directo y golden por Contracts v2 | salida comprometida | GOLDEN_CONTRACT | 2 |
| C5 | Documentos «generados del código actual» | `probes_digest`, `pack_digest`, `slice_digest`, `anchors_digest` | fuente + salida | PROBE_FRESHNESS_GUARD | 3 |
| C6 | Registro de cierre de la Fase 2 | `test_phase2_closure.py` contra `docs/revision/P2X3_phase2_closure.json` | mapa de 141 fuentes, digesto, 5 digestos de congelación | HISTORICAL_CLOSURE_GUARD | 0 en la corrida (el commit lo había adaptado); sin esa adaptación, falla |

**FAILURES_COUNT = 612 · ROOT_CONTRACTS_COUNT = 6.** Dos contratos explican el 97,5 %.

### C1 — por qué una línea rompe 466 pruebas

El repositorio reconstruye cada versión histórica del núcleo **a partir del archivo vivo**: cada etapa
declara en `REVERSAL` los trozos que insertó, y la etapa siguiente deshace esos trozos y prueba el
resultado por SHA. Para `derived.py`, el último eslabón es P2W-1 (7 trozos sobre el archivo de P2V-1); antes
lo tocaron P2O-1 y P2T-1 de la misma forma. `d087cc3` añadió texto a `derived.py` **sin declararse eslabón**,
así que `proved()` falla y con ella toda reconstrucción aguas arriba.

Respuesta a S5-1: el propósito de esta guardia **no** es que el archivo vivo quede fijo, sino que el archivo
histórico siga siendo **reconstruible exactamente**. Los SHA históricos (`CORE_AT_P2V1` y los 67 digestos de
etapa fijados) deben quedarse como están; el archivo vivo puede cambiar **si y sólo si** un eslabón sucesor
declara la reversión. No se actualiza ningún texto esperado: se añade un eslabón.

Respuesta a S5-2: las 93 incidencias «`_derived_at_*` has no attribute `CoreProfile`» son un **síntoma
secundario** de C1. `p2v1_core()` registra un módulo vacío en `sys.modules` antes de ejecutar el texto
reconstruido; cuando la prueba de reversión lanza, el módulo vacío queda en caché. No es una API antigua ni
una incompatibilidad con un campo aditivo: es una vista en sombra cuya construcción aborta aguas arriba.

### C2 — una constante con dos papeles

`PHASE2_DIGEST` es a la vez la identidad histórica del cierre y «el núcleo contra el que el runtime acepta
correr». Con el árbol enmendado, la compuerta de autoridad se cierra (falla cerrada: no es inseguro, pero
nada de la capa de autoridad puede abrir un sitio) y la condición de seguridad `phase2_digest_changed` se
dispara en todos los escenarios. `d087cc3` añadió constantes de linaje que **ningún código de producción
lee**.

### C4 — por qué cambian los goldens si la conducta es exacta

De los 9 bloques del informe golden, **8 son idénticos**; difiere sólo `parameters`, el inventario de
procedencia, que gana la entrada del campo nuevo (70 → 71). Causa: **metadatos**, no conducta.

### Serialización y esquema

`CoreProfile.to_dict()` itera los campos y `scenario_from_dict` construye con `CoreProfile(**datos)`.
Artefactos antiguos: se leen (el campo toma su valor por omisión). Artefactos nuevos: llevan una clave más,
así que cambia todo digesto que la cubra, y un núcleo sin enmienda **no puede leerlos** (argumento
desconocido).

## 3 · Hallazgos de la revisión adversarial sobre `d087cc3`

- **D5 (bajo, real):** con el enlace declarado y fracción 0, el caso límite sin ventilación lanza
  `UnresolvedBoundary` antes del retorno temprano, mientras que con el enlace apagado no lanza. «0 no
  transmite nada» no es exacto en ese borde. Inalcanzable hoy (ningún perfil declara el cociente); a
  corregir o documentar en el paquete formal.
- **Pruebas débiles (real):** con la fracción hecha inerte, 30 de las 39 pruebas de
  `test_phase2_amendment.py` siguen pasando; con la ecuación revertida, 26. T10 y T10b usan
  `pytest.raises(Exception)`, que también atrapa el `TypeError` de un campo inexistente; T1 es cierta por
  construcción; T11 y T12 no distinguen «no transmite». Hay que endurecerlas antes de certificar.
- Sin defecto: aplicación única de la fracción, alcance del invariante, perfiles comprometidos idénticos
  campo a campo, artefactos históricos del cierre sin modificar.

## 4 · Arquitectura de la enmienda formal

```
HISTORICAL_PHASE2_CLOSURE     HEAD d2cca46 · digesto 22b90a6f… · inmutable
        │   (se sigue recalculando DESDE el árbol vivo, deshaciendo trozos declarados)
        ▼
PHASE2_AMENDMENT_1            padre = el cierre · 1 fuente del núcleo cambiado (+ su módulo de etapa)
                              digesto enmendado propio · guardias sucesoras · sondas propias
```

**Diseño de dos niveles (S6-1).** No hace falta inventarlo: es el mecanismo que 15 etapas ya usan.

- *Nivel histórico:* el eslabón nuevo aporta la reversión de sus trozos, de modo que cada digesto histórico
  —incluido el del cierre, `22b90a6f…`— **recalcula sin cambiar** desde el árbol vivo. El registro de
  cierre ya contiene el mapa `ruta → sha` de los 141 fuentes, así que ni siquiera depende de que git
  conserve el commit.
- *Nivel vigente:* el eslabón tiene su propio digesto de congelación sobre el árbol enmendado, y los
  documentos «del código actual» se regeneran como en cada etapa. Los valores que tenían al cierre quedan
  en el registro de cierre, intactos.

**Puntero de núcleo vigente (S6-2).** Hoy no existe. Propuesta mínima, en `runtime_shadow.py`:

- `PHASE2_CLOSURE_HEAD` y `PHASE2_DIGEST`: literales históricos, sin tocar (3 pruebas los fijan).
- `CORE_LINEAGE`: tupla ordenada de registros `{id, parent, digest, record}`; `ACTIVE_CORE` es el último.
- La condición de seguridad pasa a ser de dos niveles: el digesto vivo debe igualar `ACTIVE_CORE.digest`
  **y** el digesto histórico debe recalcular a `PHASE2_DIGEST` por la reversión. Las dos, no una.
- Los artefactos de autoridad ganan el identificador del núcleo vigente; un artefacto sin él se lee como
  «cierre». Es un cambio de esquema de la capa de Fase 3 y hay que tratarlo como tal.

## 5 · Alcance exacto del paquete (S7)

| | Qué | Nota |
|---|---|---|
| A | Núcleo ejecutable | `clinical_core/derived.py`: los 4 trozos de `d087cc3`, más la decisión sobre D5 |
| B | Guardias sucesoras | un módulo de etapa nuevo en `clinical_core/` con `REVERSAL`, SHA del cierre, texto/bytes/fuentes del cierre, vista de `fields` sin el campo nuevo, `chain(patch)`/`tree(patch)`, digestos de la cabeza fijados como históricos; **una línea** en los ~32 fixtures de las pruebas cerradas |
| C | Registro de digesto | `docs/revision/PHASE2_AMENDMENT_1.json`, completado con el digesto de etapa y la evidencia |
| D | Sondas de la enmienda | las 4 de «código actual» regeneradas; `test_phase2_amendment.py` endurecida |
| E | Punteros vigentes | `runtime_shadow.py` (linaje), `runtime_shadow_evidence.py` (condición de dos niveles), campo en artefactos |
| F | Goldens | directo y Contracts v2: sólo `parameters` (+1), con una prueba que fije que ésa es la única diferencia |
| G | Documentación | Decision File, deuda técnica, documento de la enmienda |
| H | **Byte-idénticos para siempre** | `docs/revision/P2X3_phase2_closure.json` y su documento; los 67 digestos históricos fijados; los `REVERSAL`/`CORE_AT_*` de las 15 etapas; los literales `PHASE2_DIGEST` y `PHASE2_CLOSURE_HEAD`; `validation/`; la rama del piloto |

Por precedente, el módulo de etapa probablemente deba registrarse en `clinical_core/decision_pack.py`
(todas las etapas lo hicieron), lo que sería un segundo fuente del núcleo tocado. A confirmar al implementar.

## 6 · Veredicto y siguiente paquete

**`A · FORMAL_AMENDMENT_PATH_FEASIBLE_WITH_LOCALIZED_GUARD_SUCCESSORS`**, con una precisión que importa:
«localizado» significa **un paquete de etapa completo según la convención del propio repositorio**, no un
parche. Precedente medido: la etapa P2W-1, última que tocó `derived.py`, movió 49 archivos (+2900/−62; 32
de prueba, casi todos de una línea). El cierre histórico queda inmutable, los contratos raíz son 6, las
guardias sucesoras coexisten por diseño, la conducta por omisión es exacta y no hay rediseño amplio del
runtime — sí un cambio deliberado en una compuerta de seguridad de la Fase 3 (C2), pequeño en código y
relevante en gobernanza.

**P2-AMEND-1F — paquete de sucesión formal (diseñado, NO implementado):**

1. Módulo de etapa con la reversión y el arnés; onda de una línea en los fixtures.
2. Sucesor de dos niveles del registro de cierre; `test_phase2_amendment.py` endurecida (mutantes M1/M2).
3. Puntero de núcleo vigente y condición de dos niveles en la Fase 3; esquema de artefactos.
4. Regeneración de los 4 documentos y de `parameters` en los dos goldens, con diff revisado.
5. Certificación: focalizadas de la cadena → **una** suite completa → regresiones → revisión adversarial →
   registro.
6. Reversión: revert del paquete, como se hizo hoy. Los artefactos escritos bajo la enmienda no los lee un
   núcleo sin ella; como no hay autoridad en vivo ni exposición a residentes, el alcance es de desarrollo.

**Coste estimado:** 4–6 h de implementación más 1–1,5 h de certificación; 5–8 h en total, con riesgo de un
segundo ciclo de suite completa (+1 h). El arnés de composición de cadenas es la parte delicada.

## 7 · Lo que este paquete no hizo

No actualizó valores congelados, no regeneró sondas ni goldens, no tocó `derived.py`, no forzó ningún push,
no borró `d087cc3` y no continuó trabajo de funcionalidades de la Fase 3.
