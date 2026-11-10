# Enmienda 2 · GI: consciencia y colapso circulatorio · A2-011 y A2-012 (2026-11-10)

**Estado: `AMENDMENT_2_CANDIDATE_NEEDS_FURTHER_FACULTY_DECISION`. Detenida en A2-012, antes de tocar el núcleo.**
No hay candidato; `clinical_core/` es byte a byte el de la Enmienda 1 certificada (`10b45ce2…`). Pruebas de sólo
lectura: `test_amendment_2_scale_audit.py`. No se afirma validación clínica.

Motivo de la detención, en una línea: la deuda `D` existente no expresa la temporalidad que la docencia pidió
para la consciencia sistémica, y la decisión A2-FD-004 ordena detenerse antes de crear un segundo acumulador.

## 1 · Escalas exactas (A2-011)

| Variable | Significado y escala | Llegada | Ecuación de actualización (paso de 1 minuto) | Topes | Quién la lee |
|---|---|---|---|---|---|
| `N` | estado neurológico primario, [0, 1] | 0 | nadie la escribe | guarda | sólo la capa candidata de encefalopatía |
| nivel de consciencia | entero 0–3, lectura derivada, sin memoria | el autorado (GI: 0) | `max(nivel de llegada, escalera(PAS), escalera(SpO2))`; sin pulso, 3 | — | observación |
| aporte relativo | DO2 respecto de la llegada | 1 | gasto × Hb × SpO2, relativo a la llegada | ≥ 0 | déficit, impulso simpático |
| índice de aporte | DO2 / DO2 normal de reposo = `arrival_delivery_ratio` × aporte relativo | la razón del caso (**GI: 1,0, no declarada**) | — | — | déficit |
| déficit efectivo | `max(0, demanda − reserva × índice de aporte)`, en unidades de consumo normal | 0 en GI | instantáneo | ≥ 0 | `D`, tono, carga ácida, señal aguda |
| `D` | deuda acumulada de aporte | 0 | con déficit > 0: `dD = g × déficit` (no repaga); con déficit = 0 al inicio y al final del minuto: `dD = −D/τ` | ≥ 0, sin techo | lactato, impulso simpático |
| presión | relativa a la llegada = gasto relativo × tono | 1 (GI: PAM 65 / 74 mmHg) | instantánea | — | escalera, barorreflejo |
| gasto / bomba | relativo a la llegada, de V, P, T y ritmo | 1 | instantáneo | 0 con pulso detiene la corrida | presión, aporte |
| tono `T` | relativo a la llegada | 1 | respuesta al déficit donde el perfil la declara (GI: constante) | — | presión |
| pulso / ritmo | estado tipado; `terminal_since` | con pulso | sólo por evento de ritmo guionado o por la regla de colapso | invariante | todo |
| carga de colapso (núcleo) | `aux.collapse_burden`, gravedad × tiempo de **gasto** bajo | 0 | apagada: ambos límites `None` | ≥ 0 | regla de colapso |
| capa candidata de colapso | señal = **máximo**(fallo de perfusión por PAM en mmHg, déficit) → carga con τ → terminal | — | todo sin fijar | [0, 1] | nadie en vivo |

Parámetros del perfil comprometido que usan los casos de GI: reserva de extracción 1,0; ganancia `g` 1,0 por minuto;
τ de repago 60 min. Los tres son `PROVISIONAL` («60 min is not approved»).

### 1A · La escalera directa (A2-011A)

`PAS < 80 → 1`, `PAS < 65 → 2`; `SpO2 < 87 → 1`, `SpO2 < 80 → 2`. Marcada `ADOPTED` del motor heredado
(`family_engine._PRESSURE_LEVELS` y `_OXYGEN_LEVELS`), sin el anclaje ni el margen de recuperación de la capa de
observación. La capa candidata de encefalopatía (P2L-2, 2026-11-01) ya la declaraba `LEGACY_REFERENCE_ONLY`.

- Pruebas que nombran sus campos: 4 archivos; que nombran el nivel de consciencia: 21; goldens con el nivel: 16.
- **Quitarla cambia familias comprometidas bajo la configuración por omisión:** en el curso sin tratar de GI el
  nivel pasa hoy de 0 a 1 hacia el minuto 45 y a 2 hacia el 120 sólo por esa escalera. No se quitó.

## 2 · ¿Expresan el déficit y `D` la conducta pedida? (A2-012)

La docencia pidió (A2-FD-004): deterioro que empieza con aporte ≈ 35–45 % sostenido 2–4 min; máximo con aporte
≤ 20–25 % sostenido 2–4 min; recuperación sólo con aporte > 50–60 % durante 3–5 min.

| Propiedad | Déficit instantáneo | `D` | Resultado |
|---|---|---|---|
| Gravedad | sí: es lineal en el aporte | **no**: el `D` de «3 min al 40 %» (1,8) se alcanza igual con 18 min al 90 % o 60 min al 97 % | `D` no distingue gravedad |
| Persistencia de 2–4 min | no: no tiene memoria | **no**: en el curso de GI el aporte baja ≈ 0,003 por minuto; al cruzar por fin el 45 % (después del minuto 180) `D` ya vale más de 25 veces ese valor. Cualquier condición sobre `D` está cumplida de antemano | no hay ventana |
| Retardo de recuperación de 3–5 min por encima del 50–60 % | no | **no**: con el aporte al 60 % sigue habiendo déficit y `D` **sube**; sólo repaga con aporte ≥ 100 %, y tras 5 min conserva el 92 % | semántica opuesta |

**Veredicto de A2-012: `EXISTING_DEBT_STATE_INSUFFICIENT_FOR_CONSCIOUSNESS_TEMPORALITY`.** `D` es una deuda
metabólica integrada sin techo y sin umbral de gravedad, hecha para el lactato; no es una memoria de deterioro
cerebral. Combinar «aporte actual bajo» con «`D` alto» tampoco sirve: da un deterioro instantáneo al cruzar el
umbral. Ningún otro estado del núcleo lleva esa memoria (el colapso sí tiene la suya, `aux.collapse_burden`).

Por instrucción expresa, **no se creó un segundo acumulador** y no se implementó nada.

### 2A · Segunda cuestión, independiente: el índice de aporte de GI no es «% de lo normal»

Los casos de GI no declaran `arrival_delivery_ratio`: el núcleo lee el aporte de la llegada como normal (1,0)
aunque el paciente llega con PAS 88 y lactato 4,4. Medido en el caso comprometido sin tratar: índice de aporte
0,82 al minuto 60, 0,65 al 120 y **0,48 al 180**, con PAM 32 mmHg. Con las regiones de la docencia leídas sobre ese
índice, el paciente de GI **no tendría ningún deterioro sistémico de consciencia en tres horas**. La contradicción
que la enmienda quiere quitar seguiría ahí. Falta declarar cuánto vale el aporte de la llegada respecto de lo
normal, o decir que las regiones se leen respecto de la llegada. Clasificación: `UNIDENTIFIABLE` con la evidencia
del repositorio.

## 3 · Qué representación sí expresa la conducta (en papel; no implementada)

La memoria que la docencia diseñó el 2026-11-01 en la capa candidata P2L-2: una carga `F` ∈ [0, 1] que relaja
hacia la señal aguda `S` (la rampa del déficit) con una constante de subida y otra, mayor, de bajada. Es el
«segundo acumulador» que la decisión de hoy pide aprobar antes de crear: habría que añadirlo al estado del núcleo.

Inversión analítica de la conducta, con las categorías de A2-FD-006 (0,25 / 0,50 / 0,80) y reserva 1:

| Magnitud interna | Región | Centro (sólo para pruebas) | Identificabilidad |
|---|---|---|---|
| Cota severa de la rampa (señal = 1) | déficit 0,75–0,80 (aporte 20–25 %) | 0,775 | `FACULTY_DEFINED_FROM_BEHAVIOR` |
| Constante de subida | 1,24–2,49 min (S = 1 lleva `F` a 0,80 en 2–4 min) | 1,86 | `DERIVED_FROM_EXISTING_EQUATION` |
| Cota normal de la rampa (señal = 0) | déficit 0,34–0,62 (aporte 38–66 %) | 0,52 (aporte 48 %) | `WEAKLY_IDENTIFIED`: depende de las otras tres |
| Constante de bajada | 6,4–10,6 min (de 0,80 a 0,50 en 3–5 min sin señal) | 8,5 | `WEAKLY_IDENTIFIED`: «recuperación significativa» leída como bajar una categoría |

Comprobado con las funciones de la capa candidata: con el centro, 3 min al 20 % dan `F` = 0,80; 3 min al 40 % dan
0,25; al 55 % la señal es 0; 4 min sin señal bajan de 0,80 a 0,50.

**Tensión que queda:** con esas constantes de subida, **un solo minuto** de fallo extremo ya da `F` entre 0,33 y
0,55 (somnoliento u obnubilado). Eso choca con «un transitorio breve da deterioro limitado o nulo». Con paso de un
minuto y memoria de primer orden no se cumplen las dos cosas a la vez; hay que decidir cuál prevalece.

La salida observable tendría que ser `max(N, F, colapso)`, **sin** la señal aguda `S` en el máximo (la capa
candidata sí la incluye hoy): con `S` dentro, el deterioro sería instantáneo y no habría persistencia.

## 4 · Colapso circulatorio: lo que la decisión pide de las dos estructuras (A2-014, sólo auditado)

- La regla del núcleo es **sólo por gasto**: es exactamente «gasto bajo solo → colapso», que A2-FD-007 rechaza.
- La capa candidata combina por **máximo**: basta una de las dos señales. A2-FD-007 exige **las dos**. Y mide la
  perfusión en **mmHg absolutos**, que A2-FD-008 pide evitar.
- Estructura canónica mínima que resultaría: la cinética de carga de la capa candidata sobre la memoria que el
  núcleo ya tiene (`aux.collapse_burden`), con señal = **mínimo**(fallo de perfusión normalizado, fallo de aporte),
  y la vía dura por ausencia de pulso tal como está. No necesita estado nuevo.
- Mismo problema de escala que en §2A: la presión del núcleo es relativa a una llegada que en GI ya es hipotensa.

No se implementó: A2-016 exige que A2-011 a A2-015 sean coherentes en conjunto, y la consciencia no lo es todavía.

## 5 · Decisiones docentes que desbloquean la enmienda

1. **Memoria de consciencia.** ¿Apruebas añadir al estado del núcleo la carga de encefalopatía sistémica `F` de
   P2L-2 (relaja hacia la señal del déficit, sube rápido y baja lento) como segundo estado acumulado, distinto de
   `D`?
2. **Escala del aporte en GI.** ¿Las regiones de 35–45 %, 20–25 % y 50–60 % se leen respecto del aporte normal
   —y entonces cuánto vale el aporte de llegada de cada caso de GI respecto de lo normal— o respecto del aporte
   de la llegada?
3. **Transitorio breve.** Con paso de un minuto: ¿prevalece «2–4 min de fallo extremo llevan al máximo» o «un
   minuto de fallo extremo no produce deterioro observable»? (Lo segundo exige una subida más lenta o un retardo.)
4. **Señal aguda.** ¿Confirmas que la salida observable no incluye la señal instantánea, sólo la memoria?
5. **Colapso.** ¿Confirmas la combinación por mínimo (las dos señales a la vez) sobre la memoria existente, y que
   la perfusión se mide relativa (a lo normal o a la llegada, según la respuesta 2)?

## 6 · Lo que no se ejecutó

A2-013 a A2-015 quedan como diseño en papel (§3 y §4). A2-016 a A2-021 no se iniciaron: no hay etapa sucesora, no
hay digesto de candidato, no se corrieron contratos raíz ni la suite completa. El cierre histórico y la Enmienda 1
no cambiaron.
