# Auditoría DF-23 · Consistencia clínica fuera de la decisión DF-20, y la nueva pregunta sobre `acs_54m_inferior`

Ciclo 6 del AI Advisor · rama `clinical-encounter-v0.13` · 2026-09-28.

**Estado: AUDITADO. NO CORREGIDO. Esta auditoría no modificó nada del repositorio.**

> **Qué se aplicó después (sesión principal, mismo día).** Sólo las dos
> correcciones de datos clínicos que cumplen las seis condiciones, medidas otra
> vez en el motor antes y después, con pruebas
> (`test_the_case_says_what_the_patient_shows.py`) y registro
> (`corrections_registry`, C-2026-09-28-08):
>
> 1. **`acs_52m_de_winter`** (§1.7): el POCUS repetido conserva «Akinesis of
>    the anterior wall and apex…» mientras la arteria sigue cerrada y el modelo
>    no llega a acinesia (a +35 y +95 min; antes decía «mildly reduced»).
>    Abierta la arteria, manda el modelo, como antes. PA, FC y SpO₂ idénticas;
>    los otros cinco SCA, idénticos.
> 2. **`bradycardia_bb_54f`** (§2.5): llega «Drowsy». Ya no «empeora» sola a
>    los 5 minutos. Su foto de llegada aprobada (dibujada «alert») deja de
>    coincidir desde el minuto 0; antes dejaba de coincidir desde el minuto ~5.
>
> **No se aplicó** la tercera (la prueba de embarazo en el intérprete, §4.5):
> es un cambio del lector que no pertenece a las nueve clases de DF-22 (regla
> §64 del ciclo 6: un hallazgo HIGH se corrige sólo si se relaciona
> directamente). Queda como decisión en la cola, con la sobrecarga
> transfusional del trauma (§7.1), que no cumple la condición 1.

- Todo se verificó con el motor real, sin red y sin proveedor (`MRS_OFFLINE_CASES=1`, sin clave, sockets bloqueados).
- Las dos correcciones clínicas que cumplen las seis condiciones (de Winter y `bradycardia_bb_54f`) se probaron **sólo en copias descartables del código**, fuera del repositorio (sección 8). La tercera, del intérprete, no se probó: `family_parser.py` lo está editando otra sesión.
- Otra sesión editaba `family_engine.py`, `family_parser.py`, `app.py` y otros módulos mientras se escribía esto (sección 8). Los números de línea de esos archivos corresponden a la lectura final y pueden correrse unas líneas.
- Al final hay una fila por decisión pendiente («Decisiones que se piden»). Le pido a usted una respuesta por fila.
- Criterios aplicados: los principios docentes de DF-23 (variabilidad plausible no se «limpia»; se marca sólo lo implausible, lo que contradice el diseño, lo que da una señal educativa falsa o lo que hace responder incoherentemente al motor) y la prioridad de fuentes (motor → caso → desafío → eventos críticos → pruebas → documentación histórica).

## Resumen

| CASO | PROBLEMA | FUENTE A | FUENTE B | IMPACTO CLÍNICO | CLASIFICACIÓN | RECOMENDACIÓN (seis condiciones) |
|---|---|---|---|---|---|---|
| `acs_52m_de_winter` (C14 YES) | La severidad del VI **retrocede** con la arteria cerrada | POCUS de llegada redactado: «Akinesis of the anterior wall and apex…» | POCUS a +30 min: «The anterior wall and apex show mildly reduced contraction…» (modelo, parte en 0.82 para todos) | Señal falsa de reperfusión espontánea en el caso cuya evidencia C14 es «names the anterior akinesis»; puede bajar la urgencia | **INCONSISTENCIA REAL** | **Corregir: cumple 6/6.** Piso de texto sólo para de Winter (§1.7). Sin efecto en C14, eventos críticos ni encuentros históricos |
| `acs_61m_posterior` (C14 YES) | «Hypokinesis» pasa a «mildly reduced contraction» | llegada: «Hypokinesis of the posterior wall…» | +30 min: «The posterior wall shows mildly reduced contraction…» | Ninguno: hipocinesia leve sigue siendo hipocinesia; después empeora de forma monótona | **VARIACIÓN PLAUSIBLE** | Sin cambio |
| `acs_70f_left_main` (C14 YES) | «Globally reduced» pasa a «globally mildly reduced» | llegada: «Globally reduced contraction without a single focal defect» | +30 min: «Contraction is globally mildly reduced…» | «Leve» debilita la señal «limitar volumen» del C14 en una paciente hipoperfundida y congestiva | **AMBIGUO** | Decisión docente: qué grado quiso decir «reduced». No cumple la condición 1 |
| `acs_70f_left_main` (C14 YES) | Pulmón del POCUS sin líneas B | examen «scattered basal crackles»; radiografía «Mild pulmonary congestion» | POCUS «No B-lines; A-line pattern bilaterally» (valor por defecto `_B_LINES_NONE`, no redactado) | El POCUS sugiere tolerancia a volumen justo donde el C14 pide limitarlo | **INCONSISTENCIA REAL** | Decisión docente sobre el texto exacto (y su traducción). Cumple 5/6: falta la redacción aprobada |
| `acs_54m_inferior` | «Reduced contraction» pasa a «mildly reduced» | llegada: «Reduced contraction of the inferior wall…» | +30 min: «The inferior wall shows mildly reduced contraction…» | Bajo; ya registrado como LOW en la auditoría anterior | **AMBIGUO** | Sin cambio en este ciclo |
| 4 oclusiones | Tras reperfundir, la pared llega a «contract normally» | evento: «The affected wall recovers only partly» | POCUS a las ~2–3 h de abrir: «…contract normally…» (techo 0.85 = umbral «normal») | Recuperación completa en < 3 h; el texto del evento dice lo contrario | **AMBIGUO / DOCUMENTACIÓN** | Decisión docente (decisión 3 del 2026-09-21 pide terminar mejor que al llegar) |
| `acs_54m_inferior` (nueva pregunta) | VD comprometido en la fisiología; VD normal en el POCUS | motor: `rv_involvement`, NTG 20 mcg/min → 66/44, V4R +1.5 mm | POCUS: «RV free wall contracts normally»; VCI «1.8 cm; about 50%» | Coexistencia atípica pero posible; la conducta correcta (V4R, sin nitratos, volumen prudente) no depende del POCUS | **VARIACIÓN PLAUSIBLE** (atípica) | **NO CHANGE RECOMMENDED.** C14: se recomienda **NO**; sigue **NOT REVIEWED** hasta confirmación docente |
| `bradycardia_bb_54f` | Somnolienta en todo el texto, «Alert» en el estado | presentación «found drowsy», examen «drowsy but rousable», «Opens eyes to voice, follows simple commands slowly» | observable `mental_status` = «Alert» (valor por defecto de `_observable`) | Al llegar el examen generado dice «Alert… engages in conversation»; a los ~5 min «empeora» a Drowsy sin cambio real | **INCONSISTENCIA REAL** | **Corregir: cumple 6/6.** `mental="Drowsy"` en el `_observable` del caso (§2.5) |
| `anaphylaxis_63m_betablocked` | FA en el caso, ritmo sinusal regular en monitor y ECG | examen «Irregular pulse…», historia «irregular heart rhythm», apixabán | monitor «Sinus rhythm» y ECG `rhythm: sinus` a 64/min | El pulso palpado contradice el monitor en el mismo minuto | **INCONSISTENCIA REAL** | Decisión docente (FA en monitor y ECG, o pulso regular). No cumple la condición 1 |
| `bradycardia_ccb_68m` | FA en la historia, bradicardia sinusal en el monitor | «irregular heart rhythm treated for years», palpitaciones | monitor «Sinus bradycardia»; examen «Very slow regular pulse» | FA paroxística hoy en sinusal: coherente | **VARIACIÓN PLAUSIBLE** (+ documentación) | Sin cambio; opcional precisar «paroxysmal» en la historia |
| Mujeres de 24–46 años | Embarazo no redactado; la prueba de embarazo **retiene** la tanda de órdenes | — | intérprete: «This order was not recognized… The other orders in this submission are held» | En `pulmonary_embolism_33f` pedir β-hCG junto con la angio-TC deja la angio-TC retenida | **DOCUMENTACIÓN** (contenido) + **INCONSISTENCIA** con la regla docente del 2026-09-24 (intérprete) | Contenido: decisión docente. Intérprete: registrar la prueba como «no modelada»; cumple 6/6 (coordinar con quien edita `family_parser.py`) |

**Hallazgos incidentales** (sección 7, fuera de lo pedido, con evidencia): la sobrecarga transfusional se dispara en **shock hemorrágico traumático** («the haemoglobin was already adequate», con 2900 mL perdidos) — **INCONSISTENCIA REAL de alto impacto** en dos casos C14 YES; y hallazgos menores (§7.2).

**Correcciones que cumplen las seis condiciones:**

1. `acs_52m_de_winter`: conservar el texto redactado del VI mientras la arteria siga cerrada y el modelo no alcance ese grado (§1.7).
2. `bradycardia_bb_54f`: `mental="Drowsy"` en su llegada (§2.5).
3. Intérprete: reconocer la prueba de embarazo como estudio «no modelado» (§4.5). No es un dato clínico.

---

## 1. POCUS en las oclusiones coronarias

### 1.1 Cómo modela el motor la pared, y cuándo actúa la reperfusión

| Pieza | Qué hace | Dónde |
|---|---|---|
| Texto de llegada | El primer POCUS copia el texto redactado del caso | `family_engine.py:2363` (`deepcopy(case["investigations"][diagnostic]["result"])`) |
| Relevo por el modelo | Desde el primer minuto de isquemia (`ischemic_min` ≥ 1), el VI se reemplaza por el texto del modelo, **sin mirar el grado redactado**. Comentario: *«The arrival scan is the authored one; the model takes over once the infarct has had minutes to evolve.»* | `family_engine.py:2420-2423` |
| Valor de partida | `ARRIVAL_LV = .82  # the wall the case already describes as reduced`, **el mismo para los cuatro casos** | `acs_reperfusion.py:67`, `:238` (`setdefault`) |
| Pérdida con la arteria cerrada | −0.0025/min hasta el piso 0.45 | `acs_reperfusion.py:42-43`, `:253` |
| Grados | ≥ 0.85 «contracts normally» · ≥ 0.70 «mildly reduced» · ≥ 0.58 «moderately reduced» · menos, «akinetic» (tronco: «severely reduced») | `acs_reperfusion.py:70-75`, `:347`, `:350-360` |
| Línea de tiempo resultante | 0.82 es «leve»: leve hasta el minuto 48 de isquemia, moderado 48–96, acinético desde el 96 | cálculo desde las constantes; confirmado en el motor |
| Reperfusión | Hemodinamia: abre 90 min después de activarla (120 con traslado). Trombolisis: 60 min. Al abrir, el ECG vuelve a basal y el evento dice *«The affected wall recovers only partly.»* | `acs_reperfusion.py:24-26`, `:211-219`, `:240-249` |
| Recuperación | +0.0015/min hasta el techo 0.85, **que es exactamente el umbral «normal»** | `acs_reperfusion.py:44-45`, `:266-272` |
| Congestión | Usa 0.82 como cero: *«Zero while the wall is where the case wrote it, so the authored words stand on arrival»*. El 0.82 es un índice **relativo**; lo que choca es el texto absoluto que se deriva de él | `acs_reperfusion.py:97-113` |
| Documentación | «Parte en 0.82 y cae 0.0025/min…», «≥ 0.85 normal, ≥ 0.70 leve…», revisadas por la facultad | `docs/ACS_PHYSIOLOGY_MAGNITUDES.md:53-54` |

El texto se calcula en el minuto del pedido y se entrega 2 minutos después. En las tablas, el tiempo es el del informe.

### 1.2 `acs_52m_de_winter` (C14 YES, decisión A)

| TIEMPO | ESTADO CORONARIO | ESTADO HEMODINÁMICO | HALLAZGO POCUS · VI (texto exacto) | INTERVENCIÓN | RESPUESTA FISIOLÓGICA ESPERADA |
|---|---|---|---|---|---|
| Llegada (2) | DA proximal ocluida, 40 min de dolor | 128/78 · FC 96 · SpO₂ 95 · FR 24 · llene 2 s · alerta | «Akinesis of the anterior wall and apex; the inferior wall contracts normally» | — | Acinesia anterior y apical temprana: plausible con PA conservada |
| +30 sin reperfusión (34) | ocluida · VI 0.735 | 125/76 · 98 · 93 · 26 · 2.3 | **«The anterior wall and apex show mildly reduced contraction; the other walls contract normally»** | ninguna | La acinesia persiste o se extiende; **no mejora sin reperfusión** |
| +60 sin reperfusión (60) | ocluida · 0.67 | 122/75 · 99 · 91 · 28 · 2.5 | «…show moderately reduced contraction…» | ninguna | ídem |
| +100 sin reperfusión (106) | ocluida · 0.555 | 118/72 · 102 (taquicardia sinusal) · 89 · 32 · 2.9 | «The anterior wall and apex are akinetic; the other walls contract normally» | ninguna | Acinesia; congestión creciente; FV del modelo a los 120 min |
| Hemodinamia activada a los 3 min → arteria abierta a los 93 (97) | abierta · 0.596 | 119/73 · 101 · 90 · 31 · 2.8 | «…show moderately reduced contraction…» | aspirina + activación | ST resuelto; aturdimiento: mejoría parcial y lenta |
| 129 / 191 | abierta · 0.64 / 0.74 | 121/74 · 100 / 125/76 · 98 | «…moderately reduced…» / «…mildly reduced…» | — | Mejoría lenta y parcial |
| 341 (≈250 min tras abrir) | abierta · 0.85 (techo) | 129/79 · 95 · 96 | «The anterior wall and apex contract normally; the other walls contract normally» | — | Recuperación **parcial** según el propio evento |
| Tenecteplasa al llegar (abre a los 60): 37 / 69 / 131 | ocluida / abierta / abierta | 124/76 / 123/75 / 126/77 | «mildly reduced» / «moderately reduced» / «mildly reduced» | tenecteplasa 40 mg | La misma lectura falsa de mejoría **antes** de que abra |

- **Secuencia sin reperfusión:** acinesia → leve → moderada → acinesia. La primera repetición se lee como una reperfusión espontánea que no ocurrió.
- **Secuencia con angioplastia:** acinesia → leve (cerrada) → moderada (recién abierta) → leve → normal. El paciente parece **empeorar al abrir la arteria**.

### 1.3 `acs_61m_posterior` (C14 YES, decisión A)

| TIEMPO | ESTADO CORONARIO | ESTADO HEMODINÁMICO | HALLAZGO POCUS · VI | INTERVENCIÓN | RESPUESTA ESPERADA |
|---|---|---|---|---|---|
| Llegada (2) | circunfleja/CD posterior ocluida, 2 h de dolor | 132/80 · 88 · 96 · 20 · 2 | «Hypokinesis of the posterior wall; the anterior and lateral walls contract normally» | derivadas posteriores: «ST elevation of 1 mm in V7 to V9…» | Hipocinesia posterior |
| +30 (34) | ocluida · 0.735 | 129/78 · 90 · 95 · 21 · 2.3 | «The posterior wall shows mildly reduced contraction; the other walls contract normally» | ninguna | Igual o peor |
| +100 (106) | ocluida · 0.555 | 122/74 · 94 · 93 · 23 · 2.9 | «The posterior wall is akinetic; the other walls contract normally» | ninguna | Peor |
| Abierta a los 93 (97) | abierta · 0.596 | 123/75 · 93 · 94 · 23 · 2.8 | «The posterior wall shows moderately reduced contraction; the other walls contract normally» | hemodinamia a los 3 min | Parcial |
| 191 | abierta · 0.737 | 129/78 · 90 · 95 | «…shows mildly reduced contraction…» | — | Parcial |

«Hypokinesis» no tiene grado; «mildly reduced contraction» es hipocinesia leve. La secuencia se lee monótona: no implica reperfusión.

### 1.4 `acs_70f_left_main` (C14 YES, fila clara)

| TIEMPO | ESTADO CORONARIO | ESTADO HEMODINÁMICO | HALLAZGO POCUS · VI · pulmón | INTERVENCIÓN | RESPUESTA ESPERADA |
|---|---|---|---|---|---|
| Llegada (2) | tronco o tres vasos | 104/66 · 112 · 94 · 26 · 3 · lactato 3.1 · «scattered basal crackles» · Rx «Mild pulmonary congestion» | «Globally reduced contraction without a single focal defect» · **«No B-lines; A-line pattern bilaterally»** | — | Disfunción global con congestión: líneas B esperables |
| +30 (34) | ocluida · 0.735 | 101/64 · 114 · 92 · 29 · 3.3 | «Contraction is globally mildly reduced, without a single focal defect» · sin líneas B | ninguna | Igual o peor |
| +100 (106) | ocluida · 0.555 | 94/60 · 118 · **87** · **35** · 3.9 | «Contraction is globally severely reduced, without a single focal defect» · **sin líneas B** | ninguna | Peor, con más congestión (el modelo resta 7 puntos de SpO₂) |
| 500 mL en 15 min (informe 35) | ocluida | 102/65 · 113 · 92 · 29 | «globally mildly reduced» · VCI «1.9 cm; about 50% inspiratory collapse», sin cambio | 500 mL | La PA casi no responde (perfil «lv»: tolerancia 700 mL, fracción 0.25) |
| Abierta a los 93 (97) / 191 | abierta · 0.596 / 0.737 | 95/61 · 117 · 88 / 101/64 · 114 · 92 | «…globally moderately reduced…» / «…globally mildly reduced…» | hemodinamia a los 3 min | Parcial |

Si la activación se retrasa a los 35 min, la FV de los 120 min de isquemia llega antes que la apertura (probado: FV a los ~122, apertura a los 125).

### 1.5 `acs_54m_inferior`

| TIEMPO | ESTADO CORONARIO | ESTADO HEMODINÁMICO | HALLAZGO POCUS · VI · VD · VCI | INTERVENCIÓN | RESPUESTA ESPERADA |
|---|---|---|---|---|---|
| Llegada (2) | CD ocluida con VD comprometido | 100/64 · 58 (bradicardia sinusal) · 96 · 22 · 3 | «Reduced contraction of the inferior wall; the other walls contract normally» · «Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign» · «1.8 cm; about 50% inspiratory collapse» | — | — |
| +30 (34) | ocluida · 0.735 | 96/62 · 60 · 96 · 22 · 3.4 | «The inferior wall shows mildly reduced contraction; the other walls contract normally» · VD y VCI iguales | ninguna | Igual o peor |
| +100 (106) | ocluida · 0.555 · BAV completo desde el min 45 | 77/51 · **42 (BAV completo)** · 95 · 23 · 4.2 · somnoliento | «The inferior wall is akinetic; the other walls contract normally» · VD y VCI iguales | ninguna | Peor; FV a los 120 |
| Nitroglicerina 20 mcg/min desde el min 6 | ocluida | min 16: **66/44** · 59 · somnoliento | min 18: VI «mildly reduced…» · VD «RV free wall contracts normally» · VCI «1.8 cm; about 50%…» | NTG | Caída por dependencia de precarga; la VCI debería achicarse. **El motor no mueve la VCI en SCA** |
| Suspender + 500 mL | ocluida | min 28: 104/66 · 56 · alerta | min 42: VD y VCI iguales | suero | Rescate por volumen |
| Abierta a los 93 (97) / 191 | abierta, BAV resuelto | 89/58 · 64 sinusal / 96/62 · 60 | «…moderately reduced…» / «…mildly reduced…» | hemodinamia a los 3 min | Parcial |

`acs_66f_nonst` y `acs_48m_wellens` **no aplican**: sin oclusión activa no hay `lv_function` y el texto redactado se mantiene hasta el final, con o sin hemodinamia (verificado a los 2, 34, 97, 129 y 191 min).

### 1.6 Causa raíz, clasificación y seis condiciones

**Causa raíz.** El relevo de `family_engine.py:2420-2423` supone que el texto redactado y 0.82 dicen lo mismo. Es cierto para un texto «leve» y falso para «Akinesis». En de Winter el caso redactó el grado más grave de la escala y el modelo arranca dos grados más arriba.

| Caso | Clasificación | Por qué |
|---|---|---|
| de Winter | **INCONSISTENCIA REAL** | La mejoría con la arteria cerrada no tiene explicación clínica. Contradice el diseño: rasgo clave *«Anterior and apical akinesis on POCUS»* (`clinical_cases.py:666`), comentario *«…with the apex already failing»* (`:120`) y la fila C14 (*«names the anterior akinesis»*). Señal educativa falsa: sugiere reperfusión espontánea |
| posterior | **VARIACIÓN PLAUSIBLE** | «Hypokinesis» sin grado → «mildly reduced»: refinamiento de redacción, no reversión |
| tronco | **AMBIGUO** | «Globally reduced» sin grado → «globally mildly reduced». Con hipoperfusión y congestión, «leve» es posible pero debilita la señal del C14 |
| inferior | **AMBIGUO** | Igual que el tronco (ya registrado LOW en `docs/AUDITORIA_ACS_54M_INFERIOR.md`) |
| las cuatro, tras reperfundir | **AMBIGUO / DOCUMENTACIÓN** | El techo 0.85 da «contract normally»; el evento dice «recovers only partly». La decisión 3 (2026-09-21) pide terminar mejor que al llegar, pero no dice si la pared vuelve a normal en menos de 3 horas |

| Condición | de Winter | posterior | tronco | inferior |
|---|---|---|---|---|
| 1 · Una sola interpretación razonable | **Sí.** Nada sostiene «leve» para de Winter; 0.82 es un valor genérico. Y la única corrección que conserva el estado de llegada redactado es de texto: un 0.82 propio de de Winter (p. ej. 0.55) daría congestión y «shock» (≤ 0.55) desde el minuto 0, contra 95 % y «Alert» redactados | no hay nada que corregir | **No**: «reduced» puede ser leve o moderado | **No**: ídem |
| 2 · Diseño original claro | Sí | — | Parcial | Parcial |
| 3 · No cambia el Decision Challenge | Sí | — | — | — |
| 4 · Sin metodología nueva | Sí: aplica la convención existente («the authored words stand») y el precedente del edema pulmonar, que conserva el pulmón redactado hasta que el modelo lo mejora (`family_engine.py:2399-2405`) | — | — | — |
| 5 · ANTES/DESPUÉS demostrable | Sí (abajo) | — | — | — |
| 6 · Protegible con pruebas | Sí | — | — | — |
| **Resultado** | **CUMPLE 6/6** | sin cambio | decisión docente | decisión docente |

### 1.7 Corrección mínima propuesta para de Winter (no aplicada)

**Regla:** mientras la arteria siga cerrada, el POCUS repetido conserva el texto redactado del VI hasta que el grado del modelo sea igual o más grave que el redactado. Al abrir la arteria, manda el modelo, como hoy.

```python
# acs_reperfusion.py, junto a WALL_MOTION
GRADES = ("normal", "mildly reduced", "moderately reduced", "akinetic")

def grade_index(lv):
    """0 normal .. 3 akinetic (global: severely reduced), con los umbrales de WALL_MOTION."""
    for index, (threshold, _, _) in enumerate(WALL_MOTION):
        if lv >= threshold:
            return index
    return len(WALL_MOTION) - 1

def authored_grade_index(spec):
    """El grado que declara el texto de llegada; por defecto, la banda de ARRIVAL_LV."""
    named = (spec or {}).get("arrival_wall_grade")
    return GRADES.index(named) if named in GRADES else grade_index(ARRIVAL_LV)

# family_engine.py, rama POCUS (hoy 2420-2423): una condición más
if spec is not None and spec.get("omi") and "lv" in result and f.get("ischemic_min", 0) and (
        acs_reperfusion.is_open(f)
        or acs_reperfusion.grade_index(f.get("lv_function", acs_reperfusion.ARRIVAL_LV))
        >= acs_reperfusion.authored_grade_index(spec)):
    result["lv"] = acs_reperfusion.wall_motion(f, spec)

# clinical_cases.py:670-671, declaración coronaria de acs_52m_de_winter: un campo más
"pci_capable": True, "symptom_onset_min": 40, "arrival_wall_grade": "akinetic"},
```

- Sin el campo, el grado por defecto es el de 0.82 («leve»): **los otros tres casos no cambian**. Verificado: posterior, tronco, inferior, Wellens y 66f dan textos idénticos antes y después.
- **La fisiología no cambia:** PA, FC, SpO₂ y `lv_function` idénticos antes y después, en todos los escenarios.
- **Variante para decisión docente, no incluida:** usar `>` en vez de `>=` conservaría también «Reduced…», «Hypokinesis…» y «Globally reduced…» hasta que el modelo llegue a «moderado» (minuto 48). Cambia los otros tres casos, por eso no es mínima.

**ANTES/DESPUÉS medido** (copia descartable con la corrección):

| Momento | ANTES | DESPUÉS |
|---|---|---|
| Llegada (2) | «Akinesis of the anterior wall and apex; the inferior wall contracts normally» | igual |
| +30 cerrada (34) | «The anterior wall and apex show mildly reduced contraction; the other walls contract normally» | «Akinesis of the anterior wall and apex; the inferior wall contracts normally» |
| +60 y +80 cerrada | «…show moderately reduced contraction…» | «Akinesis of the anterior wall and apex; the inferior wall contracts normally» |
| Tenecteplasa, +37 cerrada | «…mildly reduced…» | «Akinesis…» |
| +100 cerrada (106) | «The anterior wall and apex are akinetic; the other walls contract normally» | igual |
| Abierta a los 93 (97) | «…show moderately reduced contraction…» | igual: la mejoría aparece **después** de abrir |
| 191 / 341 | «…mildly reduced…» / «…contract normally…» | igual |

**Pruebas.** Con la corrección, 15 archivos relacionados (369 pruebas + 176 subpruebas: SCA, POCUS, C14, texto del caso, español, eventos) pasan sin fallas. En la suite completa con ambas correcciones pasan 4959 pruebas, con las mismas 2 fallas de entorno que sin ellas (§8). Prueba protectora propuesta para `test_acs_reperfusion.py`:

```python
def test_the_de_winter_akinesis_stands_until_the_artery_opens(engine):
    closed, _ = course(engine, ["Reassess in 30 minutes.", "Order a POCUS. Reassess in 5 minutes."], DE_WINTER)
    assert closed["diagnostics"]["pocus"]["lv"].startswith("Akinesis")
    opened, _ = course(engine, ["Activate the cath lab. Reassess in 95 minutes.", "Order a POCUS. Reassess in 5 minutes."], DE_WINTER)
    assert "moderately reduced" in opened["diagnostics"]["pocus"]["lv"]
    posterior, _ = course(engine, ["Reassess in 30 minutes.", "Order a POCUS. Reassess in 5 minutes."], POSTERIOR)
    assert "mildly reduced" in posterior["diagnostics"]["pocus"]["lv"]   # sin cambio
```

**Efectos:**

| Sobre | Efecto |
|---|---|
| C14 de Winter (YES, decisión A) | El estado no cambia. La evidencia esperada «names the anterior akinesis» queda disponible en cualquier POCUS repetido antes de reperfundir. La frase del fundamento *«in the engine the wall motion evolves with the ischaemic minutes»* queda algo inexacta para de Winter (evoluciona tras reperfundir); no obliga a tocar la fila |
| C14 posterior y tronco | Ninguno |
| Eventos críticos | Ninguno: `acs_no_antiplatelet` y `acs_provocation_test` no leen el POCUS |
| Decision Challenge | Ninguno |
| Encuentros históricos | **Ninguno.** El texto se calcula al pedir el estudio y se guarda (`family_engine.py:2463` y `diagnostic_history`). Todo lo que se muestra después lo lee de ahí: `pocus_report.format_pocus` (`pocus_report.py:54-88`), `family_reports.format_result` (`:53-56`) y los resúmenes del Trace en `app.py` (`format_pocus(pocus, compact=True)`, ~993 y ~1081). `acs_reperfusion.wall_motion` tiene un único llamador (`family_engine.py:2423`). Probado: cambiar `lv_function` después del pedido no cambia el texto mostrado. Además la declaración coronaria se lee del caso congelado (`acs_reperfusion.coronary`), así que un encuentro anterior no tiene `arrival_wall_grade` y conserva el comportamiento de hoy aunque se reanude |
| Español | El texto redactado tiene traducción en `case_text/es/acs.json` («Acinesia de la pared anterior y del ápex; la pared inferior se contrae normalmente»); las frases del modelo no la tienen (sección 7) |

---

## 2. `bradycardia_bb_54f`: somnolienta en el texto, «Alert» en el estado

### 2.1 Lo que dice el caso

| Fuente | Texto | Dónde (`clinical_cases.py`) |
|---|---|---|
| Presentación | «…brought in after being found **drowsy** at home beside an empty blister pack. She is cold and very slow.» | :1290 |
| Historia (inicio) | «…was found **drowsy** at about seven this morning.» | :1297 |
| Examen, aspecto general | «Cold and pale; **drowsy but rousable**, with no rash.» | :1307 |
| Examen neurológico | «**Opens eyes to voice, follows simple commands slowly**, moves all limbs.» | :1308 |
| Estado de llegada | `_observable(80, 48, 40, 97, 16, crt=4, extremities="Cool", temperature=36.4, glucose=96, perfusion="impaired")`: **no pasa `mental`**, así que rige el defecto `mental="Alert"` | :1286-1287; defecto en :194-195 |
| Convención del banco | El mismo texto neurológico, palabra por palabra, en `bradycardia_avb3_78f` va con `mental="Drowsy"` (:1245, :1268). «Opens eyes to voice and follows simple commands slowly» en `anaphylaxis_63m_betablocked` también (:1073) | — |

### 2.2 De dónde sale el estado mental observable y qué ve quien juega el caso

- El estado de llegada es el `observable` del caso congelado en el encuentro. Después lo recalcula el motor cada minuto: rama bradicardia «Alert» si PAS ≥ 95 (`family_engine.py:2111`); regla genérica **PAS < 80 o SpO₂ < 87 con «Alert» → «Drowsy»** (`:2265`); recuperación de un paso (`:258-277`).
- El examen **no muestra el texto redactado**: `current_findings` reemplaza el neurológico por uno generado desde el observable (`family_engine.py:2739`).

**Probado en el motor, hoy:**

| Momento | Estado | Lo que se muestra |
|---|---|---|
| Llegada | 80/48 · FC 40 · **Alert** | Neurológico: «Current mental status: Alert. The patient engages in conversation and follows commands.» · Aspecto: «Mental status: Alert. Expression: uncomfortable. Color: mild pallor. Diaphoresis: absent.» · foto: contrato «alert» |
| Atropina 1 mg (min 1) | 80/48 · 40 · Alert | — |
| Reevaluar 5 min (min 6) | 78/47 · 38 · **Drowsy** | La respuesta informa «Mental status: alert → drowsy»: un empeoramiento que no ocurrió |

### 2.3 Qué influye el estado mental en el motor

| Uso | Efecto en este caso | Dónde |
|---|---|---|
| Examen generado (neurológico y aspecto) | «Alert… engages in conversation» al llegar | `family_engine.py:2733-2743`; `patient_appearance.py` |
| Foto de la sala | Contrato visible «alert»; la foto de llegada aprobada de V08 está dibujada «alert, uncomfortable» | `visual_observations.py:173`; `image_bank.contract_key`; `assets/patient_images/manifest.json` |
| Respuesta a cada orden, Trace y análisis | Delta «alert → drowsy»; el Trace guarda «Alert» como llegada; el análisis docente lo lee | `app.py` `_trace_observable_delta` (~1364), `management_state_snapshot` (~681) |
| Vía oral | Permitida mientras «Alert»; retenida si no: probado *«paracetamol withheld by mouth: the patient is drowsy and swallowing is not safe»* | `family_engine.py:1022-1027`, `:531`, `:642` |
| Historia | **Sin efecto**: sólo `unresponsive`, `obtunded` o `sedated` impiden hablar, y la fuente ya es la pareja | `app.py` (~10047) |
| Vía aérea | **Sin efecto**: ninguna orden de vía aérea depende del estado mental; bajo ventilación invasiva el motor lo calcula (salida, no entrada). La glucosa oral pide aclarar «airway protection» si no está alerta | `airway_pharmacology.py:122`; `family_engine.py:531-532` |
| Alta | Alarma «found drowsy at home» si vuelve somnolienta | `family_engine.py:1649` |
| Eventos críticos | **Sin efecto**. `bradycardia_no_support` dice en su gatillo «…hypotension **or an altered mental state**», pero el tamizaje no lee el estado mental (`rubric_screening.py:722-726`); `bradycardia_cause_unexamined` tampoco | `case_assessment_bank.py:1078-1095` |
| Registro | `record_findings.OBSERVED` lo lista como «alertness» (descriptor inerte) | `record_findings.py:36` |

### 2.4 Clasificación y seis condiciones

**INCONSISTENCIA REAL.** Cuatro textos redactados dicen somnolienta; el único «Alert» es un argumento omitido. Crea una señal falsa (un deterioro a los 5 min que era el estado de llegada) y el motor la contradice solo, a los pocos minutos.

| Condición | ¿Se cumple? |
|---|---|
| 1 · Una sola interpretación | Sí: presentación, inicio, aspecto y examen neurológico coinciden; la convención del banco usa «Drowsy» para ese mismo examen |
| 2 · Diseño claro | Sí |
| 3 · No cambia el Decision Challenge | Sí (R2-04: la causa está en los blísteres; el estado mental no la cambia) |
| 4 · Sin metodología nueva | Sí: un valor de un parámetro existente |
| 5 · ANTES/DESPUÉS | Sí (abajo) |
| 6 · Protegible | Sí |
| **Resultado** | **CUMPLE 6/6** |

### 2.5 Corrección mínima propuesta (no aplicada)

`clinical_cases.py:1286`: agregar `mental="Drowsy"` al `_observable` del caso:

```python
_o = _observable(80, 48, 40, 97, 16, crt=4, extremities="Cool", mental="Drowsy", temperature=36.4,
                 glucose=96, perfusion="impaired")
```

**ANTES/DESPUÉS medido** (copia descartable):

| Momento | ANTES | DESPUÉS |
|---|---|---|
| Llegada | Alert · «Current mental status: Alert. The patient engages in conversation and follows commands.» | Drowsy · «Current mental status: Drowsy. Engagement is reduced; interpret alongside respiratory and circulatory findings.» · foto «drowsy» |
| Min 6 (78/47) | Drowsy: salto «alert → drowsy» | Drowsy, sin salto |
| Glucagón 5 mg, min 11 (102/60 · FC 52) | Alert | Alert |
| Min 21 (92/55 · FC 45, el antídoto se desvanece) | Alert | **Drowsy**: coherente con D5 («the antidote fades») |
| Paracetamol 1 g PO | administrado | «withheld by mouth: the patient is drowsy…» |

**Efectos:**

- **C14** (NO, decisión E): sin cambio. **Eventos críticos:** sin cambio. **Fisiología:** frecuencia y presión idénticas; sólo cambia la conciencia.
- **Pruebas:** 18 archivos relacionados (643 pruebas + 177 subpruebas) pasan, y la suite completa no cambia (§8). De 10 archivos de sala, imagen y encuentros (278 pruebas), pasan 273; las otras 5 fallaron por el entorno de la auditoría (`MRS_OFFLINE_CASES=1`): fallan igual sin la corrección y pasan con la corrección sin esa variable.
- **Imágenes (salida dependiente, no condición):** la foto de llegada aprobada de V08 queda sin estado compatible y la sala mostraría su vista neutra con aviso (*«The current state or nothing»*, `image_scene.py`), o pediría una foto nueva si el rol permite pagar. Hoy ocurre lo mismo desde el minuto ~5.
- **Encuentros históricos:** ninguno; el observable de llegada viaja congelado con cada encuentro.
- **Español:** «Drowsy» se muestra «Somnoliento» (`language.py:199`), en masculino, también para esta paciente y para `bradycardia_avb3_78f`. Es menor y de idioma.

### 2.6 Observación relacionada: el primer minuto contradice la llegada en otros casos

Barrido de los 31 casos: estado de llegada y estado 2 minutos después, sin ninguna orden.

| Caso | Llegada redactada | A los 2 min | Causa | Clasificación |
|---|---|---|---|---|
| `bradycardia_bb_54f` | Alert (80/48) | Drowsy (79/47) | regla genérica, PAS < 80 | el motor corrige un dato mal redactado (§2.4) |
| `bradycardia_ccb_68m` | Alert (74/44); «alert but slow to answer» | Drowsy (73/44) | regla genérica, PAS < 80 | **AMBIGUO**: el texto o la regla |
| `pulmonary_edema_58m` | Alert (SpO₂ 81); «Awake, oriented and distressed» | Drowsy | regla genérica, SpO₂ < 87 | **AMBIGUO** |
| `pulmonary_edema_75f` | Alert (SpO₂ 84); «Awake and oriented…» | Drowsy | ídem | **AMBIGUO** |
| `anaphylaxis_29f` | Alert (84/46 · SpO₂ 91) | Drowsy (83 · SpO₂ 85) | la reacción progresa | variación plausible |
| `hypoglycemia_28m`, `_54m_thiamine` | Drowsy | Obtunded | conciencia por glucosa | ya documentado (DC1, criterio T12 de `docs/CATALOGO_HIPOGLICEMIA.md`) |

Ninguna de las ambiguas cumple la condición 1. El proyecto ya tiene el criterio para hipoglicemia (T12: *«El estado de conciencia autorado al llegar es el que el motor muestra al minuto 1»*); extenderlo a las otras familias es una decisión docente.

---

## 3. FA frente a ritmo sinusal

| | `anaphylaxis_63m_betablocked` | `bradycardia_ccb_68m` |
|---|---|---|
| Comorbilidades | «hypertension», «atrial fibrillation» (`clinical_cases.py:1078`) | ídem (`:1209`) |
| Historia | «His wife reports high blood pressure and **an irregular heart rhythm**.» (`:1083`) | «His daughter reports high blood pressure and an irregular heart rhythm **treated for years**.» (`:1214`) |
| Medicamentos | «His wife lists **atenolol and apixaban**, taken every morning; he took both today.» (`:1084`) | «verapamil, which he doubled last week… She thinks he may have taken extra today because of **palpitations**.» (`:1215-1216`); sin anticoagulante |
| Examen cardíaco | «**Irregular pulse** at a rate that does not rise with the low pressure; peripheries warm.» (`:1093`) | «Very slow **regular** pulse; peripheries cool with delayed capillary refill; no murmur.» (`:1224`) |
| Informe de ECG redactado | ninguno (perfil `baseline`; el ECG dibuja el ritmo del observable) | ninguno |
| Monitor (probado) | «Sinus rhythm», FC 64; tras adrenalina, 65, sinusal | «Sinus bradycardia», 38; tras calcio 3 g, «Sinus rhythm» 79 |
| ECG de 12 derivaciones (probado) | `rhythm: sinus`, 64/min; repetido a los 13 min: sinus, 65 | `rhythm: sinus`, 38; tras calcio: sinus, 64 |
| Origen del «sinusal» | `_observable` deriva el ritmo de la FC (`clinical_cases.py:204-205`); el motor lo mantiene (`family_engine.py:2320-2321`) | ídem |
| ¿Paroxística, persistente o permanente? | No se dice. El apixabán sugiere FA establecida y anticoagulada | No se dice. Las palpitaciones sugieren episodios paroxísticos |
| **Clasificación** | **INCONSISTENCIA REAL**: el pulso palpado es irregular y el monitor y el ECG, regulares y sinusales, en el mismo minuto. Una FA paroxística hoy en sinusal sería plausible, pero entonces el examen no diría «irregular» | **VARIACIÓN PLAUSIBLE**: FA paroxística hoy en sinusal, con bradicardia sinusal por verapamilo. Examen y monitor coinciden. **Documentación:** el tipo de FA no está escrito |
| Seis condiciones | **No cumple la 1**: dos arreglos razonables (FA en monitor y ECG, o pulso regular en el examen). **Dudosa la 3**: una FA en el monitor de un paciente hipotenso agrega un distractor (control de frecuencia, cardioversión) a un caso cuya palanca es el betabloqueo y el glucagón | No aplica |
| **Recomendación** | Decisión docente. Cuatro fuentes sostienen FA ahora; el motor puede mostrarla (`ecg12` dibuja `af` con RR irregular; `family_engine.py:2302` conserva un ritmo de llegada no sinusal, como hace `bradycardia_avb3_78f` con «Complete AV block»). Si se elige FA, revisar la intención de `test_cognitive_encounters.py` (que ninguna variante muestre «AF» en el ritmo) | Sin cambio. Opcional: precisar «paroxysmal» en la historia |

---

## 4. Embarazo

### 4.1 Mujeres en edad reproductiva del banco

| Caso | Edad | Fuente de la historia | Relación con embarazo en el caso | Relevancia clínica del estado de embarazo |
|---|---|---|---|---|
| `asthma_24f` | 24 | paciente | nada | Baja-moderada: el tratamiento agudo no cambia; importa si se intuba o se irradia |
| `anaphylaxis_29f` | 29 | paciente | nada | Baja para la primera decisión (adrenalina IM igual); posición y vigilancia fetal |
| `pulmonary_embolism_33f` (C14 YES) | 33 | paciente | «I use an estrogen-containing contraceptive» (`clinical_cases.py:755`) | **Alta**: antes de la angio-TC (radiación, contraste); en el embarazo una TVP proximal por compresión permite tratar sin angio-TC, justo la oportunidad C14 del caso; y el embarazo es un factor de riesgo. Heparina y enoxaparina, lo que el motor ejecuta, son compatibles con el embarazo: el anticoagulante no cambia |
| `pneumonia_46f` (C14 YES) | 46 | paciente | metotrexato semanal | Baja-moderada: metotrexato teratogénico; elección de antibiótico |
| `bradycardia_bb_54f` (límite) | 54 | pareja | intoxicación intencional | Baja por edad; en intoxicaciones intencionales el test es rutinario en edad fértil |

Ninguna tiene estado de embarazo redactado, y la historia no tiene un tema para él (`history_topics.py`). Los dos casos de trauma (`trauma_limb_hemorrhage_27m`, `trauma_hemothorax_41m`) son hombres: ahí no aplica.

### 4.2 Qué pasa cuando se pregunta

**Camino:** «Talk» en `app.py` (~10063) → `clinical_scene.answer_history` → `patient_conversation.answer_from_sources` → coincidencia local (`local_question_ids`). Si la coincidencia local falla:

- sin clave (modo sin conexión): `NO_MATCH` (`patient_conversation.py:182`);
- con clave: el proveedor **sólo elige números de frases redactadas**, validados; la instrucción es *«If not documented, select none»*.

**Probado sin conexión**, las mismas preguntas en las cinco pacientes:

| Pregunta | `pulmonary_embolism_33f` | `asthma_24f` | `anaphylaxis_29f` | `pneumonia_46f` |
|---|---|---|---|---|
| «Are you pregnant?», «Could you be pregnant?», «Is there any chance you might be pregnant?», «Do you use contraception?», «¿Está embarazada?», «¿Podría estar embarazada?», «¿Hay posibilidad de embarazo?», «¿Fecha de última menstruación?» | `NO_MATCH` | `NO_MATCH` | `NO_MATCH` | `NO_MATCH` |
| «When was your last menstrual period?», «¿Cuándo fue su última regla?» | **«The breathing and chest discomfort started abruptly about two hours ago. The breathlessness started suddenly while I was sitting.»** | «This information is not documented in the case.» | «It began about fifteen minutes into the meal and has worsened since. I ate a dish with a satay sauce…» | «The cough began three days ago… I take methotrexate weekly…» |
| «Could you be pregnant, and what medications do you take?», «¿Usa pastillas anticonceptivas?» | «I use an estrogen-containing contraceptive and occasional acetaminophen.» | «I have used my reliever repeatedly today; my preventer inhaler ran out last week.» | «I take no regular medication. I have no adrenaline autoinjector.» | «I take methotrexate weekly and folic acid; no antibiotic has been started.» |
| «Any chance of pregnancy or any bleeding?» | «I have not coughed blood or had other recent bleeding.» | «This information is not documented in the case.» | «I have not coughed or vomited blood.» | «I have not coughed blood, vomited blood or passed black stools.» |

- `NO_MATCH` = «I couldn't match that question to the recorded history. Please rephrase it or use History topics.» En español: «No pude relacionar esa pregunta con la historia registrada. Reformúlala o usa los temas de la anamnesis.»
- **La pregunta por la última regla cae en el patrón de «inicio»** (el `\bwhen\b` genérico de `local_question_ids`) y devuelve el comienzo de los síntomas: una respuesta que parece responder y no responde.
- **Lo que registra el Trace:** cada pregunta cuesta 2 minutos clínicos (`clinical_time.py:40`) y queda como actividad de información: `activity_kind: "history_question"`, la pregunta, `information_obtained` con la respuesta (también el texto de `NO_MATCH`), estado antes y después (`app.py` `record_information_activity`, ~813).
- **¿Se puede inventar algo?** No. Sin conexión, sólo frases redactadas o los dos mensajes fijos. Con conexión, el proveedor sólo elige números de frases. El motor nunca inventa resultados de estudios.

### 4.3 Qué pasa cuando se pide una prueba de embarazo

| Orden | Resultado |
|---|---|
| «Order a pregnancy test.» · «Order a serum beta-hCG.» · «Order a urine pregnancy test.» | *«This order was not recognized: "order a pregnancy test". Replace it with a supported intervention, dose/settings and route, or say cancel. The other orders in this submission are held until then.»* |
| «Pide una prueba de embarazo.» · «Solicita beta-hCG.» | *«The requested study was not recognized. Specify one supported study per order.»* |
| «Order a pregnancy test and a CT pulmonary angiogram.» | **`executed: False`: la angio-TC queda retenida** |
| Comparación: «Order a toxicology screen and a CT pulmonary angiogram.» | *«Study requested; not modelled in this version of the simulator: Toxicology. The request is recorded with its time; no result will be produced and none is invented.»* y la angio-TC corre |

Es decir, la conducta prudente en `pulmonary_embolism_33f` (pedir β-hCG antes de la angio-TC) **retiene la tanda completa**. La regla docente del 2026-09-24 (`test_a_study_the_simulator_does_not_model.py`) dice lo contrario para un estudio que el simulador no produce: *«the intention is recognised and the request is recorded… and the rest of the submission runs»*.

### 4.4 Clasificación

- **Contenido (qué responde cada caso): DOCUMENTACIÓN.** Nada se contradice y nada se inventa; falta el dato. Qué responde cada caso es una decisión clínica: embarazo sí, no, o no lo sabe, lo que exige el test. Por eso **no cumple la condición 1**.
- **Intérprete (la prueba retiene la tanda): INCONSISTENCIA** con una regla docente vigente. No es un dato clínico.

### 4.5 Recomendación

1. **La facultad decide qué responde** `pulmonary_embolism_33f` (prioridad alta), y después las otras tres. Sugerencia de forma, no de contenido: una frase que la paciente sabe («my last period…») en un tema que la coincidencia local reconozca.
2. **Intérprete, corrección mínima: cumple 6/6.** Agregar `"pregnancy_test"` a `family_parser._DIAGNOSTICS` (`family_parser.py:103`, junto a `"toxicology"`, `:118`), con un patrón en inglés y en español: pregnancy test, beta-hCG, hCG, prueba o test de embarazo. Sumar su etiqueta en `family_reports.TEST_LABELS`.
   - Sin resultado redactado, el motor la registra como «Study requested; not modelled…» (`family_engine.py:376-399`) y el resto de la tanda corre.
   - **Condiciones:** 1 sí (aplica la regla existente; modelar un resultado sería una ampliación, no una alternativa), 2 sí, 3 sí, 4 sí, 5 sí (retenida → registrada), 6 sí (mismo patrón que `test_a_study_the_simulator_does_not_model.py`).
   - Coordinar con la sesión que edita `family_parser.py`.
3. **Opcional:** que una pregunta sobre la última regla no caiga en el patrón genérico de «inicio».

---

## 5. POCUS de los 14 casos C14 YES

Casos YES según `case_assessment_bank.C14_DECLARATIONS` (`:1519`). Para cada uno se pidió el POCUS (o el E-FAST) al llegar, se hizo la intervención principal y se repitió el estudio.

- **A** · ¿disponible a tiempo?
- **B** · ¿hallazgos coherentes con el estado?
- **C** · ¿evolución coherente con intervenciones y curso?
- **D** · ¿puede guiar de verdad una decisión?
- **E** · ¿recibe quien juega información suficiente para usarlo?
- **F** · ¿evita regalar la decisión que C14 quiere observar?

Todo el POCUS del banco sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`, `clinical_cases.py:64`). Esta revisión no reemplaza la confirmación docente que pide TD-04, y un REVIEW **no es una recomendación de cambiar C14**.

| Caso | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| `acs_61m_posterior` | PASS: informe a los 2 min; V7–V9 también | PASS: hipocinesia posterior, 132/80, sin congestión | **REVIEW**: «Hypokinesis» → «mildly reduced» (redacción); tras abrir llega a «contract normally», contra «recovers only partly» | PASS: junto con V7–V9, prioriza reperfundir (decisión A) | PASS | PASS: hallazgos, sin diagnóstico |
| `acs_52m_de_winter` | PASS | PASS: acinesia con PA conservada es plausible temprano | **INCONSISTENT**: «Akinesis» → «mildly reduced» a los 30 min con la arteria cerrada (§1) | PASS (decisión A) | PASS al llegar (la acinesia se nombra); el POCUS repetido engaña (ver C) | PASS |
| `acs_70f_left_main` | PASS | **INCONSISTENT**: pulmón «No B-lines; A-line pattern bilaterally» (defecto) contra «scattered basal crackles» y «Mild pulmonary congestion» | **REVIEW**: «Globally reduced» → «globally mildly reduced»; el pulmón sigue sin líneas B con SpO₂ 87 y FR 35 | **REVIEW**: la función global limita el volumen, pero el pulmón «seco» apunta a tolerancia | **REVIEW**: VI sin grado al llegar | PASS |
| `gi_bleed_57m` | PASS | PASS: VI pequeño e hiperdinámico, VCI 0.9 cm con colapso casi completo, 88/54 | **REVIEW**: tras 2 U + 1 L, VCI «2.0 cm; <50% inspiratory collapse» con el VI todavía «near-obliteration of the cavity in systole» y FC 110 | PASS (decisión C) | PASS | PASS |
| `gi_bleed_72f` | PASS | PASS: VI hiperdinámico, VCI 1.1 cm >50 %, 98/62 | **REVIEW**: VCI 2.0 cm <50 % tras 1.6 L equivalentes; VI fijo «Hyperdynamic contraction» | PASS | PASS | PASS |
| `pneumonia_46f` | PASS | PASS: VI vigoroso, VCI 1.0 cm >50 %, líneas B focales y consolidación derecha | PASS: VCI 1.0 → 1.5 cm (~50 %) con 1 L → 2.0 cm (<50 %) con 2 L | PASS | PASS | PASS: consolidación sin decir «neumonía» |
| `pneumonia_83m` | PASS | PASS: VCI 1.2 cm >50 %, VI conservado, consolidación izquierda | PASS: 1.2 → 1.5 → 2.0 cm | PASS | PASS | PASS |
| `obstructive_pyelonephritis_58f` | PASS | PASS: VI vigoroso, VCI 1.0 cm >50 %, 94/54 | **REVIEW**: VCI fija en 1.0 cm tras 1 L (ya declarado en su fila C14) | PASS (estrategia inicial) | PASS | PASS |
| `pulmonary_edema_58m` | PASS | PASS: VI moderadamente reducido, VCI 2.4 cm <50 %, líneas B difusas | PASS: con CPAP la VCI dice «respiratory variation not assessable during positive-pressure support»; líneas B aún difusas a los 35 min (retraso plausible) | PASS | PASS | PASS |
| `pulmonary_edema_75f` | PASS | PASS: VI severamente reducido, VCI 2.5 cm, derrames pequeños | PASS: ídem | PASS | PASS | PASS |
| `pulmonary_embolism_33f` | PASS: POCUS a los 2 min; angio-TC a los ~20 | PASS: VD levemente dilatado ≈ VI sin signo D; poplítea no compresible «on the operated (symptomatic) side» (el lado nunca se nombra, en ninguna fuente) | PASS: VD y TVP fijos tras heparina, plausible a 30 min | PASS (decisión G) | PASS | PASS |
| `pulmonary_embolism_61m` | PASS | PASS: VD > VI, signo D, McConnell, VCI 2.3 cm, TVP izquierda | PASS: tras trombolisis indicada, 85/53 → 98/61; VD igual a los 40 min, plausible | **REVIEW**: decidir reperfusión antes de la angio-TC es la evidencia esperada, pero el motor no disuelve el trombo si la trombolisis se da antes de 15 min de PAS < 90 **contados desde la llegada**: *«…the bleeding risk is taken without the indication, and the obstruction is unchanged»* (regla docente del 2026-09-20, `pe_obstruction.py:22`, `:83-94`) | PASS | PASS |
| `trauma_limb_hemorrhage_27m` | PASS: E-FAST a los 4 min | PASS: cinco ventanas sin líquido; POCUS con VI vacío y VCI 0.7 cm colapsada | **REVIEW**: tras 2 U el motor anuncia sobrecarga transfusional con crepitantes y SpO₂ 89 %; el POCUS repetido sigue «No B-lines» y VCI 0.7 cm con colapso completo (§7.1) | PASS (fila clara) | PASS | PASS: «No free fluid…» sin decir «FAST negativo» |
| `trauma_hemothorax_41m` | PASS: E-FAST a los 4 min (la PA cae de 88/50 a 75/43 en ese lapso) | PASS: «Fluid in the left pleural recess»; POCUS «Left pleural effusion with echogenic contents»; VCI 0.8 cm | PASS: tras el tubo (1200 mL, «continues to fill») el E-FAST repetido sigue con líquido, coherente con sangrado activo | PASS (fila clara) | PASS | PASS: «Fluid…», no «haemothorax» |

**Sólo dos INCONSISTENT, ambos ya descritos:** de Winter C (§1) y tronco B (el pulmón por defecto). Los REVIEW son límites del modelo que no invalidan la oportunidad declarada.

**Pulmón del tronco (INCONSISTENT en B).**

- `POCUS["acs"][5]` (`clinical_cases.py:127-128`) sólo redacta VI y VCI; el pulmón toma el valor por defecto `_B_LINES_NONE` (`:69`).
- Tres fuentes dicen congestión: el examen «scattered basal crackles» (`:729`), la radiografía «Mild pulmonary congestion without focal consolidation.» (`:735`) y el rasgo clave «Ongoing rest pain with hypoperfusion and congestion».
- **Seis condiciones: 5/6.** La 1 se cumple en la dirección (hay líneas B), pero la extensión y el texto exacto (basales bilaterales o difusas) son una elección clínica. Las otras cinco se cumplen: refuerza la fila C14 en vez de cambiarla, no toca la fisiología, el ANTES/DESPUÉS es directo y una prueba lo fija.
- Falta la redacción aprobada, y el pasaje español de `case_text/es/acs.json` volvería a aprobación (`test_case_text.py` lo exige).
- Aun corregido, el texto seguiría fijo: el motor no mueve el pulmón en SCA.

---

## 6. `acs_54m_inferior` bajo la nueva pregunta docente

**La pregunta cambió.** La facultad no autoriza cambiar el tamaño del VD, su contractilidad, la VCI ni la fisiología. Ya no se pregunta cuál representación corregir (opciones A y B de `docs/AUDITORIA_ACS_54M_INFERIOR.md`). Se pregunta si un IAM inferior con compromiso hemodinámico del VD puede coexistir con un POCUS cualitativo de urgencias normal o no diagnóstico en ese momento, y si el POCUS de este caso ofrece una oportunidad significativa de guiar el manejo. No se repite aquí lo que esa auditoría ya documentó (fuentes del VD, mecanismos del motor, pruebas dependientes).

### 6.1 Evidencia nueva, medida en el motor

| Hallazgo | Evidencia |
|---|---|
| **El POCUS repetido no responde ni al nitrato ni al volumen** | NTG 20 mcg/min: PA 100/64 → **66/44** en 10 min; el POCUS a los 18 min sigue diciendo VD «RV free wall contracts normally» y VCI «1.8 cm; about 50% inspiratory collapse». Tras suspender y dar 500 mL (104/66), igual. En SCA el motor sólo mueve el texto del VI (con el tiempo) y la VCI bajo presión positiva (`family_engine.py:2408-2426`) |
| **El compromiso del VD es latente en reposo** | Llegada 100/64 · FC 58 · llene 3 s · lactato 2.1 · SpO₂ 96, con pulmones limpios. La magnitud aparece al quitar precarga (NTG) y responde al volumen: 500 mL → 106/67 (perfil «rv»: tolerancia 1600 mL, fracción precarga-dependiente 1.0; `preload_response.py:24-28`) |
| **La VCI es indeterminada, no pletórica** | «1.8 cm; about 50%»: una presión auricular derecha no muy elevada, compatible con la respuesta a volumen que el motor modela. Una VCI pletórica habría ido **en contra** de dar volumen |
| **La prueba discriminante está en el caso** | Derivadas derechas: «ST elevation of 1.5 mm in V4R, with 1 mm in V3R. The inferior elevation is unchanged in this tracing.» (`acs_reperfusion.py:399-400`); se resuelve al abrir la arteria |
| **La regla de casos generados pide lo contrario** | `nitrate_hazard.cue_present` exige que el POCUS muestre un VD dilatado o hipocinético. Con los datos de este caso, un caso generado sería rechazado: *«NITRATE_HAZARD_UNDISCOVERABLE: … the resident cannot discover it: ecg_profile is st_elevation_inferior and the POCUS RV finding describes a dilated or hypokinetic right ventricle.»* Esa regla (2026-09-18) es anterior a las derivadas derechas (decisión 7, 2026-09-21), que son la pista descubrible del caso del banco. Pesa como convención histórica (prioridad 6), no como diseño del caso |
| **El guion «bueno» no usa POCUS** | `tanda20.py:132-141`: ECG, derivadas derechas, aspirina y clopidogrel, sin nitratos, hemodinamia, traslado monitorizado |

### 6.2 Análisis clínico (conocimiento clínico general, no citas)

- El compromiso del VD es frecuente en el IAM inferior por oclusión proximal de la coronaria derecha (clásicamente, entre un tercio y la mitad), y sólo una fracción es hemodinámicamente significativa.
- **La prueba recomendada al lado de la cama son las derivadas derechas** (SDST ≥ 1 mm en V4R). Es más informativa temprano y puede resolverse en horas.
- Los signos ecográficos (VD dilatado, pared libre hipocinética, TAPSE bajo, VCI pletórica) son más evidentes en infartos extensos y en ecocardiografía formal.
  - Temprano, con compromiso limitado o con hipovolemia relativa (sudoración, náuseas, poca ingesta), **el VD puede verse de tamaño normal y la VCI no estar distendida**.
- **La evaluación cualitativa de la función del VD en el POCUS de urgencias tiene sensibilidad limitada**, sobre todo para la hipocinesia regional de la pared libre.
  - El nivel de POCUS del simulador es cualitativo y sin TAPSE (*«Findings, not interpretation… The LV is described qualitatively»*, `pocus_report.py:1-16`).
- La hipotensión por nitratos en el IAM inferior refleja dependencia de precarga (compromiso del VD, bradicardia, volemia) y puede ocurrir sin disfunción visible en un examen cualitativo.
- **La práctica habitual evita nitratos** en el IAM inferior con PA limítrofe, bradicardia o sospecha de VD hasta registrar derivadas derechas, **sea cual sea el POCUS**.

**Conclusión clínica.** La coexistencia es **plausible, aunque atípica** por la magnitud de la caída con 20 mcg/min. Un ecocardiograma formal a menudo mostraría el VD; un examen cualitativo al lado de la cama puede no verlo.

El único rasgo que va más allá de «no diagnóstico» es la afirmación «RV free wall contracts normally», que no es el texto normal por defecto (`_RV_NORMAL`, `clinical_cases.py:66`). Aun así, un falso negativo cualitativo de la pared libre es un fenómeno real.

### 6.3 Desafío, manejo esperado y función educativa del POCUS

| Elemento | Relación con el VD del POCUS |
|---|---|
| R1-07 (nota de triaje «indigestion?», `clinical_cases.py:1473`) | Ninguna |
| R2-04 (presentación epigástrica) | Ninguna |
| **R2-02** (buscar hallazgos que discriminen, incluso los que debilitan la hipótesis) | Un VD de aspecto normal frente a un V4R positivo es la evidencia que *«fitted it least well»* (pregunta de debriefing 2). Integrarla bien es R2-02. La auditoría anterior dijo que R2-02 «sufre» porque la discordancia no fue diseñada; con los principios de DF-23, una discordancia plausible no se limpia: se declara |
| Manejo esperado (D3) | Antiagregación y reperfusión *«with the preload caution an inferior territory carries»*; alternativa aceptada: *«withholding a nitrate, which in this territory is a defensible choice»* (`case_assessment_bank.py:128-133`). Nada exige POCUS |
| D4 | Observa la respuesta al nitrato o al volumen en los signos vitales, no en el POCUS |
| Eventos críticos | `acs_no_antiplatelet`, `acs_provocation_test`: ninguno depende del VD ni del POCUS |
| **Función del POCUS aquí** | (1) pared inferior: redundante con el ECG; (2) excluir derrame o aorta anormal ante dolor epigástrico con hipotensión: útil pero común a todo SCA; (3) sin líneas B: ya lo dicen el examen y la radiografía; (4) VD: **no contributivo**, y engañoso para quien le crea más que al V4R |

**¿Señal educativa falsa?** No, mientras el caso no enseñe ni premie «un VD normal en el POCUS excluye el infarto de VD». No lo hace:

- el V4R es positivo;
- D3 acepta retener el nitrato;
- la fisiología castiga el nitrato;
- la lección que queda (un VD de aspecto normal en un POCUS cualitativo no excluye su compromiso; los nitratos se deciden con el ECG, el V4R y la hemodinamia) es verdadera.

**Riesgo residual:** la afirmación categórica del texto, y que el caso no diga en ninguna parte que la discordancia es intencional. Quien revise un encuentro podría leer el daño del nitrato tras un «VD normal» como una trampa injusta. Eso es un **problema de documentación**, no de datos.

### 6.4 La pregunta C14: ¿crea el POCUS de este caso una oportunidad significativa de guiar el manejo?

| Componente del manejo | ¿Puede cambiarlo razonablemente el POCUS aquí? |
|---|---|
| Estrategia de volumen | **Débil.** La VCI es indeterminada, los pulmones limpios ya están en el examen, y el POCUS repetido no cambia con volumen ni nitrato: no sirve para titular. Compare con la decisión C: VCI de 0.9–1.2 cm que colapsan y, en neumonía y HDA, se llenan al repetir |
| Evitar nitratos | **No.** El VD «normal» no lo sostiene; lo sostienen el V4R y la PA |
| Interpretación hemodinámica | **Parcial.** VI conservado salvo la pared inferior y sin líneas B: la hipotensión no es falla de bomba del VI. Pero el ECG, la bradicardia, los pulmones limpios y el V4R ya lo dicen |
| Reevaluación | **No.** VD, VCI y pulmón fijos; sólo el VI cambia con el tiempo |
| Reperfusión | **No.** El SDST ya la decide, igual que en la decisión A para `acs_66f_nonst` |

- **Recomendación: C14 NO.** El manejo correcto depende sobre todo del ECG, del V4R, del contexto y de la respuesta hemodinámica, que es el criterio docente para NO.
- **Es coherente con dos decisiones aprobadas:**
  - la decisión A: el ECG establece el cuadro y la motilidad no cambia la vía;
  - la decisión B: un POCUS normal que no debe tranquilizar; no tranquilizarse es razonamiento diagnóstico, no C14.
- **No es inequívoca.** El argumento más fuerte por YES es la interpretación hemodinámica (VI conservado y pulmón seco permiten un bolo prudente) y la exclusión de disección o derrame antes de antitrombóticos. Ambos valen para todo SCA y las decisiones A–H no los contaron.
- **Por eso el caso sigue NOT REVIEWED** hasta la confirmación docente; toda fila C14 lleva procedencia docente (`reviewed`).
- **Si se confirma NO:**
  - fila `_c14_no(...)` en `C14_DECLARATIONS`;
  - la decisión A de `c14_review.py` deja `acs_54m_inferior` en «uncertain» (`:70-78`);
  - pruebas a actualizar: `test_c14_opportunities.py:25`, `test_c14_review.py:37` y `:54`, `test_observation_opportunities.py:76`;
  - regenerar `docs/C14_TABLA_FINAL.md`;
  - ajustar la verificación de `docs/tdfc/generar_matriz.py:241`.
- Fundamento sugerido (la redacción final es docente): *«Inferior STEMI with right ventricular involvement: the ECG, the right-sided leads and the haemodynamic response decide the antiplatelet, the nitrate and the cautious volume. The qualitative POCUS shows the inferior wall and a right ventricle that looks normal, which cannot exclude its involvement, and in the engine its RV and IVC do not change with volume or nitrate. Not being reassured by it is diagnostic reasoning, not C14 (decisions A and B).»*

### 6.5 Conclusión

**NO CHANGE RECOMMENDED** para los datos y la fisiología.

- **Clasificación:** VARIACIÓN PLAUSIBLE (atípica).
- **La coexistencia no es una contradicción que haya que corregir,** siempre que C14 no se declare YES.
- **Documentación opcional:** una nota docente que diga que el VD del POCUS es intencionalmente no contributivo y que el V4R es la prueba discriminante. Protege la lectura de R2-02 y la revisión de los encuentros.
- **La recomendación A de la auditoría anterior queda superada** por la restricción docente. La lectura que ahora se sostiene es su opción C («las dos cosas coexisten»), con el C14 NO que esa misma auditoría anticipaba para C.

---

## 7. Hallazgos incidentales (fuera de lo pedido, verificados)

### 7.1 Sobrecarga transfusional en shock hemorrágico traumático · INCONSISTENCIA REAL · impacto alto

**Mecanismo:**

- La regla dispara la sobrecarga si la hemoglobina **antes** de la unidad es ≥ 10 g/dL (`family_engine.py:1754-1758`; umbral `TRANSFUSION["unnecessary_above_g_dl"] = 10.0`, `:217-225`).
- La familia trauma **no baja la hemoglobina del modelo con la pérdida** (`family_engine.py:1737-1741`; `trauma_hemorrhage.py` no la toca).

| Caso | Secuencia | Resultado del motor |
|---|---|---|
| `trauma_limb_hemorrhage_27m` (C14 YES) | Torniquete (700 mL perdidos, 96/54 · FC 132), 2 U en 20 min | Hb del modelo 10.2 → 11.9. *«Transfusion-associated circulatory overload: the haemoglobin was already adequate, so the units added volume rather than oxygen-carrying capacity…»*. SpO₂ 97 → 89, FR 34, examen *«New bibasal inspiratory crackles since the transfusion…»*. El POCUS repetido sigue «No B-lines» y VCI 0.7 cm con colapso completo |
| `trauma_hemothorax_41m` (C14 YES) | 2 U en 20 min desde la llegada | Pierde 2200 → 2900 mL, PA 52/30 → 50/25, y el motor anuncia la misma sobrecarga, *«the haemoglobin was already adequate»*, en un paciente que se desangra |

- **Por qué importa:** enseña que transfundir un shock hemorrágico hace daño, en los dos casos de trauma, donde la sangre es el tratamiento central (la prueba `test_blood_replaces_what_was_lost_and_crystalloid_less_of_it` espera que la sangre rinda más que el cristaloide).
- **Seis condiciones: no se cumplen ahora.** Hay dos arreglos razonables: excluir la hemorragia activa o el trauma de la regla, o hacer que la hemoglobina del trauma baje con la pérdida, que cambia más salidas.
- **Se recomienda abrir una decisión aparte.**

### 7.2 Menores

| Hallazgo | Evidencia | Clasificación |
|---|---|---|
| HDA: VCI llena con VI vacío en el POCUS repetido | La VCI cambia por volumen entregado (≥ 1500 mL → «2.0 cm; <50%»; cada unidad cuenta 300 mL; `family_engine.py:2408-2413`), sin mirar el déficit. El VI redactado no cambia | AMBIGUO / REVIEW |
| Frases del modelo sin traducción | `language.say(…, "es")` da *«The anterior wall and apex show mildly reducido contraction; the other walls contract normally»*. `case_text/es/acs.json` sólo traduce los textos redactados, no las frases que genera `wall_motion` | DOCUMENTACIÓN / idioma (bajo) |
| TEP de alto riesgo: la trombolisis antes de 15 min no disuelve | La regla docente del 2026-09-20 cuenta los minutos desde la llegada; el texto dice *«the obstruction is unchanged»*. El efecto del fármaco sobre el trombo no depende del reloj | AMBIGUO (decisión docente vigente) |
| Congestión coronaria sin correlato en examen ni POCUS | de Winter a los 100 min: SpO₂ 89, FR 31, esfuerzo *«Exhausted: shallow and ineffective effort»*. El examen respiratorio sigue *«Mildly increased effort; no crackles or wheeze.»* y el POCUS «No B-lines» | REVIEW |
| Pulmón por defecto en el tronco | ya descrito en §5: «No B-lines» contra crepitantes y congestión radiográfica | INCONSISTENCIA REAL |

---

## Decisiones que se piden

| # | Decisión | Estado de la evidencia |
|---|---|---|
| 1 | `acs_52m_de_winter`: aplicar la corrección de §1.7 | Cumple 6/6; ANTES/DESPUÉS y pruebas medidos · **Aplicada en el ciclo 6 (C-2026-09-28-08)** |
| 2 | `bradycardia_bb_54f`: aplicar `mental="Drowsy"` (§2.5), y decidir la foto de llegada (vista neutra o foto nueva) | Cumple 6/6; la foto es una salida dependiente · **`Drowsy` aplicado en el ciclo 6 (C-2026-09-28-08); la foto sigue pendiente** |
| 3 | Intérprete: registrar la prueba de embarazo como «no modelada» (§4.5) | Cumple 6/6; coordinar con quien edita `family_parser.py` |
| 4 | `acs_70f_left_main`: grado del VI («reduced» = ¿leve o moderado?) y texto de las líneas B | Pulmón: 5/6, falta la redacción; VI: ambiguo |
| 5 | Inferior y posterior: ¿se mantiene el paso «Reduced / Hypokinesis → mildly reduced»? (variante `>` de §1.7) | Ambiguo / plausible |
| 6 | Tras reperfundir: ¿puede la pared volver a «normal» a las 2–3 h, o el techo debe quedar bajo el umbral? ¿Y el texto «recovers only partly»? | Ambiguo; toca la decisión 3 del 2026-09-21 |
| 7 | `anaphylaxis_63m_betablocked`: FA en monitor y ECG, o pulso regular en el examen | Inconsistencia real; dos arreglos razonables |
| 8 | Embarazo: qué responde cada caso, empezando por `pulmonary_embolism_33f` | Falta el dato |
| 9 | `acs_54m_inferior`: confirmar C14 **NO** (recomendado) o YES; y si se agrega la nota docente sobre el VD | Sin cambio de datos; sigue NOT REVIEWED |
| 10 | Trauma: sobrecarga transfusional durante una hemorragia activa (§7.1) | Inconsistencia real de alto impacto; decisión aparte |
| 11 | Primer minuto (`bradycardia_ccb_68m`, edema pulmonar), trombolisis del TEP antes de 15 min, VCI y VI en la HDA, traducción de las frases del modelo | Ambiguos o menores |

---

## 8. Evidencia, método y limpieza

**Sondas** (en `probes/`, sólo lectura; `_guard.py` bloquea sockets, quita la clave y fija `MRS_OFFLINE_CASES=1`):

| Sonda | Qué mide | Salida |
|---|---|---|
| `p1_coronary.py` | 6 casos SCA: llegada, +30, +100 sin reperfusión; hemodinamia al llegar | `p1_dewinter.json`, `p1_rest.json`, `p1_rest.txt` |
| `p2_coronary_more.py` | de Winter: angioplastia larga, tenecteplasa, POCUS a 60 y 80; inferior: NTG, suero | `p2.json` |
| `p3_brady_af.py` | `bradycardia_bb_54f`, `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m`: examen, monitor, ECG | consola |
| `p4_pregnancy.py`, `p4b_orders.py` | 13 preguntas en 5 pacientes; órdenes de prueba de embarazo | consola |
| `p5_c14yes.py` | 14 casos C14 YES: estudio al llegar, intervención principal, estudio repetido | `p5.json`, `p5.txt` |
| `p6_trauma_taco.py` | sobrecarga transfusional en trauma | consola |
| `p7_bb_fix.py` | `bradycardia_bb_54f` antes y después | consola |
| `p8_mental_tick.py` | estado mental de llegada frente al minuto 2, 31 casos | consola |
| `p1_coronary.py` y `p2_coronary_more.py` con `MRS_PROBE_ROOT` en la copia A | DESPUÉS de la corrección de de Winter; los otros cinco SCA sin cambios | `pA_after.json`, `pA_after2.json`, `pA_after_p2.json` |

Para repetir: `cd probes && PYTHONDONTWRITEBYTECODE=1 python3 -B p1_coronary.py acs_52m_de_winter`. Con `MRS_PROBE_ROOT=<copia>` la misma sonda corre contra una copia corregida.

**Copias descartables** (sin `.git` ni `local-data`, ~23 MB cada una): `copy_base` (sin cambios), `copy_A` (de Winter), `copy_B` (`bradycardia_bb_54f`), `copy_AB` (ambas). **Se borraron al terminar.**

| Corrida | Archivos | Resultado |
|---|---|---|
| Base, subconjunto de ambas correcciones | 31 | 890 pasan, 176 subpruebas |
| Corrección A, subconjunto SCA/POCUS/C14/texto | 15 | 369 pasan, 176 subpruebas |
| Corrección B, subconjunto bradicardia/imagen/texto | 18 | 643 pasan, 177 subpruebas |
| Corrección B, sala/imagen/encuentros | 10 | 273 pasan; 5 fallan por `MRS_OFFLINE_CASES=1` (fallan igual sin la corrección; pasan sin esa variable) |
| **Suite completa, base** | 245 | 4959 pasan · **2 fallan** · 77 omitidas · 2 xfail · 266 subpruebas (24 min) |
| **Suite completa, A + B** | 245 | 4959 pasan · **las mismas 2 fallan** · 77 omitidas · 2 xfail · 267 subpruebas (24 min) |

**Las 2 fallas son de la copia sin `.git`,** con y sin correcciones:

- `test_tools_reclassify.py::test_what_the_analyses_read_is_computed_by_the_code_named_and_ignores_identity` intenta `git worktree add`, que sale con 128 porque ni la copia ni sus carpetas superiores son un repositorio (el repositorio real no se tocó);
- `test_validation_readiness.py::test_from_the_returned_documents_to_the_report` exige el commit del motor en la procedencia (`provenance["engine"]["commit"]`).

**Limpieza y garantías:**

- **Esta auditoría no escribió en el repositorio.** Las sondas corren con `-B` y `sys.dont_write_bytecode`; pytest sólo corrió en las copias; las correcciones se editaron sólo en las copias. No se ejecutó ningún comando git sobre el repositorio; la única invocación la hizo una prueba dentro de una copia, y falló por falta de repositorio.
- **La lista de archivos del repositorio sí cambió durante la sesión, por la otra sesión:** de 1300 a 1308 archivos (4 pruebas nuevas y sus `.pyc` de pytest), y se modificaron `app.py`, `family_parser.py`, `language.py` y otros siete módulos.
- **Los hallazgos clave se volvieron a verificar al final contra el estado actual del repositorio:** el POCUS de de Winter, `bradycardia_bb_54f`, las preguntas y órdenes de embarazo y la traducción. Todos se mantienen.
- Los directorios vacíos `/tmp/reclassify-*` que dejó esa prueba se borraron.
- No se creó ninguna base SQLite fuera de los directorios temporales de pytest, que se borraron con las copias.
- En `df23/` quedan este documento, las sondas y sus salidas, y los registros de las corridas (`baseline_subset.txt`, `fixA_subset.txt`, `fixB_subset.txt`, `fixB_subset2.txt`, `full_copy_base.txt`, `full_copy_AB.txt`), las listas de archivos del repositorio (`repo_files_before.txt`, `repo_files_after.txt`) y `probes/p4_err.txt`, que muestra que la historia corrió por la vía sin proveedor (`category=not_configured`).

---

## Ciclo 7 (2026-09-28): C7-08, DF-23 conservador

Decisión docente del ciclo 7, §31: fila 3 con C7-06; fila 4a sólo si es
inequívoca; filas 8, 7, 4b y 6 siguen siendo decisiones clínicas.

### Fila 3 · la prueba de embarazo: hecha con C7-06

La prueba de embarazo se registra como estudio pedido con su resultado no
modelado, y no retiene la angio-TC ni ninguna otra orden. Detalle en
`docs/TD26_HEMODERIVADOS_Y_C7_06.md`, TD-22.

### Fila 4a · el pulmón del POCUS de `acs_70f_left_main`: propuesta, no aplicada

**La contradicción.** El POCUS dice «No B-lines; A-line pattern bilaterally».
Ese texto no se redactó para el caso: es el valor por defecto `_B_LINES_NONE`
(`clinical_cases.py`). Tres fuentes del mismo caso dicen congestión:

- el examen: «Mildly increased effort; scattered basal crackles»;
- la radiografía: «Mild pulmonary congestion without focal consolidation»;
- el rasgo clave: «Ongoing rest pain with hypoperfusion and congestion».

**Texto propuesto** (su extensión es la del examen del propio caso):

| | Hoy | Propuesto |
|---|---|---|
| EN | No B-lines; A-line pattern bilaterally | Scattered B-lines at both bases; no diffuse B-line pattern |
| ES | Sin líneas B; patrón de líneas A bilateral | Líneas B dispersas en ambas bases; sin patrón difuso de líneas B |

**Qué señal corrige.**

- Hoy el POCUS sugiere un pulmón seco, que tolera volumen, justo donde la fila
  C14 del caso (YES) pide limitar el volumen.
- Con el texto propuesto, el POCUS dice lo mismo que el examen y la
  radiografía, y refuerza la fila C14 en vez de contradecirla.

**Qué no cambia.**

- El desafío de decisión, la fila C14, la fisiología y los eventos críticos.
- El VI («Globally reduced…») es la fila 4b y sigue como decisión clínica.
- El pulmón seguiría fijo en el tiempo: el motor no mueve el pulmón en SCA.

**Por qué no se aplicó en este ciclo.**

- La auditoría del ciclo 6 dejó la extensión exacta como elección clínica
  (5/6 condiciones: faltaba la redacción aprobada). Proponer el texto no es
  aprobarlo.
- Cambiar el inglés invalida el texto español aprobado del caso completo
  (`case_text`: una aprobación vale para una versión exacta de los pasajes).
  Hasta una nueva aprobación, el caso se mostraría en inglés a quien juega en
  español.

**Estado: NEEDS NICOLÁS.** Basta una línea: «4a: aplicar el texto propuesto»
(u otro). Con esa respuesta se aplica en una sesión corta:

1. cambiar el valor en `POCUS["acs"][5]`;
2. `tools_case_text.py extract` y el borrador español de arriba;
3. una prueba que fije la coherencia pulmón–examen–radiografía;
4. una entrada en el registro de correcciones.

La aprobación del texto español la registra quien lo revise, en la página de
revisión. Nunca se registra en nombre de nadie.

### Filas 8, 7, 4b y 6

Siguen como decisiones clínicas, sin cambios (§31). No se limpió variabilidad
plausible.
