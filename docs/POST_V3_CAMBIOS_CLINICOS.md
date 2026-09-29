# Cambios clínicos posteriores a V3 (2026-09-29)

Instrucción docente del 2026-09-29 que cierra las decisiones clínicas analizadas después de V3
(`3d942ee`). V3 conserva sus reglas; cada cambio de abajo tiene su entrada en `corrections_registry.py`,
sus pruebas y la evidencia antes/después medida en el motor real. **Implementado no es validado**: ninguno
de estos cambios tiene todavía revisión clínica externa.

| # | Decisión | Registro | Pruebas |
|---|---|---|---|
| 1 | TEP: D revisada (shock obstructivo, reloj consecutivo, noradrenalina) | C-2026-09-29-10 | `test_pe_obstruction.py`, `test_generated_pe.py`, `test_pe_thrombolysis_screening.py` |
| 2 | DC1: conciencia anclada a la llegada | C-2026-09-29-11 | `test_arrival_consciousness.py`, `test_hypoglycemia_battery.py` |
| 3 | POCUS de la HDA según el llenado efectivo | C-2026-09-29-12 | `test_gi_bleed_pocus.py` |
| 4 | TD-31: la hemostasia no es una suma; reducido frente a detenido | C-2026-09-29-13 | `test_hemostasis_is_not_a_sum.py` |
| 5 | Hipoglicemia DC2–DC5: la vía como propiedad del acceso (`glucose_rescue` 2.0) | C-2026-09-29-14 | `test_hypoglycemia_lines.py`, `test_hypoglycemia_battery.py` |
| 6 | `acs_70f_left_main`: el VI de llegada dice el grado leve, EN/ES | C-2026-09-29-15 | `test_acs_left_main_arrival.py` |
| 7 | DF-23 fila 6 (B): la pared reperfundida queda aturdida, a lo sumo levemente disminuida | C-2026-09-29-20 | `test_reperfused_wall_stays_stunned.py` |
| 8 | DF-23 fila 7 (A): FA en monitor y ECG de `anaphylaxis_63m_betablocked`, FC 64 | C-2026-09-29-21 | `test_betablocked_anaphylaxis_rhythm.py` |
| 9 | DF-23 fila 8 (A modificada): embarazo/FUM como tema propio; sin dato, «No documentado» | C-2026-09-29-22 | `test_pregnancy_history_topic.py` |
| 10 | Hipoglicemia: vía de llegada neutra, EN/ES | C-2026-09-29-23 | `test_arrival_line_is_neutral.py` |

## 1 · TEP

Detalle, fuentes y trayectorias en `docs/PULMONARY_EMBOLISM_MAGNITUDES.md` (sección «Criterio revisado»).

## 2 · DC1: la conciencia escrita al llegar

Sin tratamiento; «Reassess in 1 minute» tres veces y luego esperas.

| Caso | Llegada | Antes (V3), minuto 1 | Ahora, minutos 1–3 | Ahora, deterioro real |
|---|---|---|---|---|
| `bradycardia_ccb_68m` | Alert, PAS 74 | Drowsy | Alert | Drowsy con PAS 67 (min 25), Obtunded con 64 (min 35) |
| `pulmonary_edema_58m` | Alert, SpO₂ 81 | Drowsy | Alert | Drowsy con SpO₂ 80 (min 15), Obtunded bajo 80 |
| `pulmonary_edema_75f` | Alert, SpO₂ 84 | Drowsy | Alert | Drowsy bajo 82 (min 55) |
| `hypoglycemia_28m` | Drowsy, 34 mg/dL | Obtunded | Drowsy | convulsión en el min 20 como antes; Obtunded bajo 29,5 (min 60) |
| `hypoglycemia_54m_thiamine` | Drowsy, 32 mg/dL | Obtunded | Drowsy | convulsión en el min 20 como antes |

- **Regla.** Al empezar, el encuentro mueve sólo los umbrales que su llegada ya cruzaba, a medio camino entre
  el valor de llegada y el umbral siguiente, que se mantiene: PAS de *Drowsy* 80 → 69,5 en 68m; SpO₂ de
  *Drowsy* 87 → 80,5 en 58m y → 82 en 75f; glucosa de *Obtunded* 45 → 29,5 en 28m y → 28,5 en 54m. Se
  compara antes de redondear. Un nivel peor que el de llegada se deja sólo pasado un margen (PAS 2 mmHg,
  SpO₂ 1 punto, glucosa 1 mg/dL), para que un valor que ronda un umbral no haga parpadear el estado;
  mejorar más allá de la llegada usa el umbral de siempre (alerta con 70 mg/dL, como en 76f).
- **Una glucosa mejor ya no muestra un paciente peor.** Con 5 mL de D50, 28m pasa de 34 a 44 mg/dL: en V3
  quedaba *Obtunded* (peor que al llegar); ahora sigue *Drowsy*.
- **Se conserva:** el deterioro real, la convulsión y el estado postictal, la sedación (morfina 15 mg:
  *Drowsy*), la intubación y la recuperación. Los otros 26 casos del banco no llevan ancla y leen igual; un
  encuentro empezado antes conserva su regla.
- **Batería de hipoglicemia:** T12 pasa en las 12 configuraciones (antes fallaba en 4); ninguna otra
  comprobación cambió. La preservación dorada declara los guiones de 28m y 54m (lectura de llegada y
  estado del ancla); 76f no cambia.

## 3 · POCUS de la HDA

VCI y VI de `gi_bleed_57m` (y `gi_bleed_72f` donde se indica), medidos con el motor real.

| Escenario | Hemodinamia | Antes (V3) | Ahora |
|---|---|---|---|
| Llegada | 88/54 · 124 | 0,9 cm, colapso casi completo · VI pequeño, hiperdinámico, casi obliterado | igual (lo escrito) |
| 1 U de GR | 101/61 · 117 | igual que al llegar (300 mL < 500) | 1,1 cm, >50 % · VI pequeño hiperdinámico **sin obliteración** |
| 2 U de GR | 115/69 · 109 | 1,5 cm, ~50 % · VI **casi obliterado** | 1,5 cm, ~50 % · **cavidad normal con contracción hiperdinámica** |
| 2 U + endoscopía, recuperación en curso | PAS 113 · FC 98 → 93 | 1,5 cm · VI casi obliterado | 1,5 cm · cavidad normal con **contracción normal** |
| 1 L de cristaloide, a los 15 min | 91/56 · 122 | **1,5 cm, ~50 %** | 0,9 cm, colapso casi completo (el litro apenas quedó en los vasos) |
| 1 L de cristaloide, una hora después | **80/50** · 128 | **1,5 cm, ~50 %** | **0,7 cm, colapso completo** · obliteración completa |
| Noradrenalina sola | 102/64 · 125 | igual que al llegar | igual que al llegar (el vasopresor no llena) |
| Sin tratamiento 60 min | 80/49 · 129 | igual que al llegar | 0,7 cm, colapso completo |
| 72f, 2 U de GR | 125/77 · 97 | 1,5 cm, ~50 % · «Hyperdynamic contraction» | 2,0 cm, <50 % · cavidad normal con contracción hiperdinámica |
| Intubado | — | diámetro + «respiratory variation not assessable…» | igual, con el diámetro de la escala |

- **Regla.** La VCI y la cavidad del VI leen la circulación de la familia (`f["circulation"]`), que ya integra
  la reposición (sangre 0,36 por unidad; cristaloide 0,00015 por mL), el sangrado que sigue y el cristaloide
  que sale de los vasos (60 % con constante de 30 min). Un vasopresor no la cambia. Escala de vacío a lleno
  (0,7 · 0,9 · 1,1 · 1,5 · 2,0 cm); cada caso entra por su hallazgo escrito y se mueve una posición por cada
  0,30 de circulación ganada o perdida (**parámetro docente**).
- **Cavidad y contracción, separadas.** Llenar reduce y luego termina la obliteración; la contracción sigue
  hiperdinámica hasta que la recuperación que alivia la taquicardia (endoscopía y hemoglobina ≥ 7, alivio
  ≥ 0,5) está en curso.
- **Presión positiva:** se conserva el diámetro y la variación respiratoria se declara no evaluable.
- **Alcance:** sólo la familia `gi_bleed`; neumonía y las demás conservan su regla. Los textos nuevos
  tienen su español (`language.py`).

## 4 · TD-31: la hemostasia no es una suma

`trauma_limb_hemorrhage_27m` (fuente arterial del muslo, 145 mL/min a severidad completa). Control y
sangrado tras cada orden, con el motor real.

| Órdenes | Antes (V3) | Ahora |
|---|---|---|
| Compresión directa | 0,75 · 36 mL/min · «controlled» | 0,75 · 36 mL/min · «reduced, not stopped» |
| Compresión, luego «Maintain direct pressure» | **1,0 · 0 mL/min** | 0,75 · 36 mL/min · «stays reduced…; adds no control» |
| Compresión, luego «Hold firm pressure» | **1,0 · 0 mL/min** | 0,75 · 36 mL/min |
| «Pack the wound and hold pressure» (una orden) | **1,0 · 0 mL/min** | 0,75 · 36 mL/min: una sola intervención |
| Taponamiento, luego compresión (dos órdenes) | **1,0 · 0 mL/min** | 0,75 · 36 mL/min |
| Compresión, luego torniquete | 1,0 · 0 · «controlled» | 1,0 · 0 · «stopped; until now it was only reduced» |
| Torniquete, luego compresión | 1,0 · 0 · «controlled» | 1,0 · 0 · «was already stopped» |

- **Regla.** Una fuente conserva la mejor medida aplicada, nunca la suma. Magnitudes sin cambio y
  **provisionales**: compresión y taponamiento 0,75, torniquete 1,0 (C7-06). Sólo una técnica más eficaz
  sube el control.
- **Registro.** La sala y la traza dicen si el sangrado disminuye o se detiene, y cuándo una medida no
  agrega control; en español: «disminuye, pero no se detiene», «se detiene», «ya estaba detenido». Un
  registro anterior conserva «controlled» / «controlado».
- **Puntaje sin cambio.** El tamizaje de `trauma_no_hemorrhage_control` lee la acción ejecutada, no el
  nivel: compresión sola, taponamiento con compresión y torniquete dan el mismo resultado que antes.
- **El lector no cambia**: «Pack the wound and hold pressure» sigue siendo dos medidas escritas; el motor
  las cuenta como una intervención.

## 5 · Hipoglicemia DC2–DC5: la vía como propiedad del acceso

Un solo mecanismo en `glucose_rescue` (versión **2.0**; la evaluación congelada de cada encuentro la
registra). Medido en `hypoglycemia_54m_thiamine` (vía fallida) y `hypoglycemia_28m` (vía funcionante).

| Situación | Antes (1.0) | Ahora (2.0) |
|---|---|---|
| Llegada | nada dice que haya una vía | las 12 configuraciones: «A peripheral intravenous cannula is already in place in the left forearm.» |
| Examinar antes de tratar | no había región para la vía | región **Vascular access**: fallida «the skin around its tip is slightly swollen and cool»; funcionante «the site is clean» |
| 25 g de D50 IV por la cánula fallida | 32 → 47 mg/dL · aviso «does not run… slows to a stop. What was ordered is not what reached the patient.» | 32 → 47 mg/dL · observación «As it goes in, the skin around the forearm cannula swells.» (una vez) · 15 % sólo en el registro técnico |
| D10 a 100 mL/h por la cánula fallida, 30 min | +20 mg/dL (llegaba entera) | **+3 mg/dL**; convulsión a los 20 min como sin tratamiento |
| Vía nueva en la configuración **fallida** | «peripheral intravenous access **replaced**» + «The new line runs freely. What is given now reaches the circulation.» | «peripheral intravenous access placed» + «A new peripheral cannula is placed in the right forearm.» |
| Vía nueva en la configuración **funcionante** | «already in place; not repeated» (0 min) | igual que en la fallida: instalada, 3 min |
| Infusión corriendo y luego vía nueva | seguía igual (entera) | pasa a la vía nueva con acceso, velocidad y minuto |
| 25 g de D50 **IO** sin aguja | 15 % (como por la cánula fallida) · 32 → 46 | aguja instalada por la orden (minuto, sin sitio, +3 min) · entera · 32 → 131 |
| Aguja IO ordenada | «reparaba» la cánula: lo IV llegaba entero | acceso propio: lo IV sigue al 15 % por la cánula |
| Glucagón IV por la cánula fallida | efecto modelado | efecto modelado; registro técnico 15 % y «pending faculty decision (DC4-F)» |
| Tiamina IV por la cánula fallida | registrada | registrada con su acceso y fracción; sin efecto |
| Glucagón IM, octreótido SC | independientes | independientes (sin registro de acceso) |
| Glucagón IO, octreótido IO | rechazados | rechazados (la vía no se amplía) |

- **Batería:** las 12 configuraciones pasan todas sus comprobaciones técnicas (antes T5 fallaba en las 6
  fallidas como decisión pendiente DC4); T14 (dosis IO) y T15 (traslado de la infusión) son nuevas. Las
  referencias R1–R9 no cambiaron.
- **Preservación dorada:** los tres casos del banco declaran sus guiones: todo encuentro lleva ahora su
  cánula de llegada, y en la configuración funcionante una vía nueva se instala.
- **Compatibilidad:** un encuentro empezado con 1.0 (sin cánula de llegada en su estado) conserva la regla
  de 1.0, incluida la IO que reparaba la vía.
- **Pendiente:** DC4-F (farmacología de una fracción de glucagón u octreótido). El lector no cambió; sus
  brechas quedan en la deuda del lector.

## 6 · `acs_70f_left_main`: el grado del VI al llegar

| | Antes (V3) | Ahora |
|---|---|---|
| POCUS de llegada (EN) | «Globally reduced contraction…» sin grado | «Globally mildly reduced contraction without a single focal defect» |
| Español | «Contracción globalmente disminuida…» | «Contracción globalmente levemente disminuida sin un defecto focal único» |
| Hallazgo docente | sin grado | «Globally mildly reduced contraction on POCUS» |
| Controles del modelo | «Contraction is globally mildly reduced» | igual |

- **Leve, no moderado:** es el grado que el modelo ya mantenía. `lv_function` 0,82 es una posición docente
  del modelo, **nunca** una fracción de eyección de 82 %. El eje de congestión no se tocó.
- **La traducción del caso vuelve a revisión docente** antes de usarse en la sala, porque cambió un pasaje
  aprobado.
- `bradycardia_bb_54f` conserva la vista neutral; no se generó ni aprobó ninguna foto.

## 7 · Decisiones no clínicas de la ampliación

| Decisión | Estado | Registro · commit | Pruebas |
|---|---|---|---|
| Foco de aprendizaje oculto hasta la revisión docente (§154AB) | Implementado | C-2026-09-29-16 · `23afbb7`, `fc10159`, `e6c7af1` | `test_learning_focus_waits_for_review.py` |
| TD-41: ninguna página ni PDF traduce al abrirse; sólo el pedido del lector | Implementado | C-2026-09-29-17 · `c765d8f` | `test_translations_are_asked_for.py` |
| KD-31: el tamizaje cita el tratamiento previo como contexto | Implementado | C-2026-09-29-18 · `fa1d910` | `test_prior_treatment_in_screening.py` |
| DC9: propuestas TD/F/C de las composiciones, pendientes | Implementado como propuesta; **la revisión sigue pendiente** | C-2026-09-29-19 · `2824270` | `test_tdfc_composition_proposals.py` |
| Baseline inglés = V3 `3d942ee` | Registrado (entrada nueva) | `adf0def` | `test_validation_baselines.py`, `test_validation_language_separation.py` |
| Deuda del lector TD-45 | Registrada; el lector no cambió | `8f705ff` | `test_reader_gaps_registered.py` |
| Fase 2 de roles | Sólo el orden | `237cceb` | — |
| Imágenes pendientes (V34 · 75f, bb_54f) | Registradas; nada generado ni aprobado | `237cceb` | — |
| Piloto formativo: prueba de humo y readiness | Técnicamente listo; bloqueado por pasos de despliegue y autorización | `docs/READINESS_PILOTO_FORMATIVO.md` | `tools_pilot_smoke.py` |
| Panel docente: las líneas TDFC ya no rompen el traductor (hallado por la prueba de humo; falla desde el ciclo 8) | Corregido | `d0cbeb8` | `test_screen_strings_name_their_values.py` |

## 8 · Cierre del ciclo (2026-09-29)

| Decisión | Antes | Ahora |
|---|---|---|
| **DF-23 fila 6 (B)** | `acs_54m_inferior` a los 315 min de activar la sala: «The inferior wall contracts normally»; `acs_70f_left_main`: «Contraction is globally normal» | «The inferior wall shows mildly reduced contraction»; «Contraction is globally mildly reduced». `lv_function` (0,85), circulación, PA, FC, SpO2 y minutos de reperfusión idénticos con y sin la regla |
| **DF-23 fila 7 (A)** | Monitor y ECG: «Sinus rhythm» a 64 (el ritmo se derivaba de la FC) | «AF» a 64 en el monitor y el ECG. PA, FC, SpO2, FR, conciencia y llene tras adrenalina IM y glucagón IV: idénticos a la etiqueta sinusal |
| **DF-23 fila 8 (A modificada)** | «¿Cuándo fue su última regla?» y «When was your last menstrual period?» respondían con el inicio de los síntomas; «Are you pregnant?» no encontraba tema | Tema propio en EN/ES (embarazo, FUM, LMP, última regla, menstruación): lo que el caso escribió o «Not documented.» / «No documentado.»; nunca inicio, nunca el proveedor. La revisión de la historia no lo cuenta como inicio. «period of time» no es menstruación |
| **`pulmonary_embolism_33f`** | — | Sin historia de embarazo inventada: «No documentado». La prueba de embarazo sigue solicitada y sin resultado (TD-22) |
| **Español de `acs_70f_left_main`** | Pendiente de revisión | Aprobada la frase exacta «Contracción globalmente levemente disminuida sin un defecto focal único.» para «Globally mildly reduced contraction without a single focal defect.», fijada por prueba |
| **Vía de llegada (hipoglicemia)** | «A peripheral intravenous cannula is already in place in the left forearm.» | «Peripheral IV in place in the left forearm.» / «Vía venosa periférica instalada en el antebrazo izquierdo.»; sigue el idioma del relato aprobado del caso |
| **IA en el primer piloto** | — | Durante el encuentro: apagada. Después del encuentro: no autorizada, función por función |

Se mantienen sin cambio: TD-45 (ocho brechas, el lector no se reabre), DC9 (propuesto, pendiente de revisión
humana, no expuesto), las cuatro dudas residuales de TDFC, TD-04 (pendiente de revisión clínica humana; ninguna
imagen ni video) y el foco de aprendizaje tras la revisión docente.

**Suite completa al cerrar.** La primera corrida sobre `85de8bb` dio 6334 passed, 77 skipped, 1 xfailed y
**1 failed**: `test_cognitive_encounters.py::test_real_patient_variants_execute_their_management_without_af_state`
con `anaphylaxis_63m_betablocked`. **Clasificación: REGRESSION de este cierre** (ni legado ni entorno): la prueba
suponía que ningún paciente del banco muestra «AF», y la fila 7 aprobada lo cambia para ese paciente. Se comprobó
que la etiqueta no toca la fisiología antigua de FA: un encuentro de familia vuelve de `execute_bundle` antes de la
regla de cardioversión, y `family_engine` no importa `clinical_physiology`. La prueba admite «AF» sólo en ese caso,
exige que esté desde la llegada y no cambie, y sigue exigiendo que ningún otro paciente entre en FA; queda en las
pruebas de C-2026-09-29-21. El resultado sobre el HEAD final está en el reporte de cierre.

## Lo que no cambió

No cambiaron las evaluaciones confirmadas, D1–D5, los eventos críticos y sus pesos, el −3, C14 ni la
referencia TDFC aprobada; la única excepción autorizada es la adaptación del tamizaje del TEP, que lee el
motivo real de la reperfusión. Tampoco la variabilidad plausible ya cerrada, el lector (congelado) ni el baseline
español `939978a`. Las cuatro dudas residuales de TDFC siguen provisionales; TD-04 sigue caso a caso;
DC6–DC8, la revisión de DC9 y «suero glucosado» siguen diferidos.

