# Peso y talla de los casos: tabla cerrada, reglas aplicadas y decisiones pendientes (2026-09-27)

**Estado:** aplicado en desarrollo (rama `clinical-encounter-v0.13`), **sólo para encuentros nuevos**. No se
publicó en la app pública, no se fusionó a `main` y no se registró ninguna aprobación clínica ni visual en tu
nombre. Reemplaza a `PESOS_CASOS_PROPUESTA.md`, que queda como antecedente.

## En corto

- **Los 31 casos tienen peso y talla**, y la ficha dice cómo se obtuvo cada dato: medido, referido o estimado.
  El paciente en diálisis muestra además su peso seco previo, rotulado como tal. El motor usa los mismos números
  que muestra la ficha.
- **La tabla se cerró con tus restricciones.** Sale de un sorteo reproducible (`tools_case_bodies.py`, semilla
  `pesos-casos-2026-09-27`) que no mira fotos, antecedentes ni diagnósticos.
- **Encuentros ya realizados: intactos.** Un encuentro guardado antes del cambio, reproducido orden por orden, da
  resultados idénticos con el código anterior y con el nuevo (sección 6).
- **Aplicado:**
  - A: peso y talla en la ficha.
  - B: volumen corriente en mL/kg sobre el peso predicho, con la fórmula en el registro.
  - F: la misma regla de peso desde la interpretación hasta el efecto, visible en el registro.
- **Pendiente, sin cambios automáticos:**
  - ventilación minuto requerida y volumen corriente por defecto, que revisaste aparte de B;
  - bloqueantes (C), diuresis (D) e infusiones (E).

  La sección 4 las agrupa en una tabla breve.
- **Imágenes:**
  - Se retiró la regla rígida de 15 kg. De los 12 casos que habrían perdido su foto, 8 la conservan con la
    compatibilidad amplia.
  - Hicieron falta 6 sustituciones: 5 quedaron hechas (US$0,64, 7 solicitudes) y 1 (`asthma_24f`) queda para tu
    revisión.
  - Hay 46 fotos pendientes de tu revisión.

## 1. La tabla (cerrada)

**Cómo se sorteó** (`tools_case_bodies.py`; `python3 tools_case_bodies.py --check` muestra las condiciones):

1. **Contexturas como punto de partida educativo**, no como prevalencia a reproducir: 8 normales, 11 con
   sobrepeso, 6 con obesidad I, 4 con obesidad II y 2 con obesidad III.
2. **Se repartieron con una semilla fija.** El reparto se aceptó sólo si:
   - cada familia tiene al menos dos de normal / sobrepeso / obesidad;
   - hay obesidad antes de los 40 y desde los 70;
   - hay peso normal entre los 40 y los 69;
   - ambos sexos tienen obesidad;
   - la proporción de obesidad entre los casos graves y los demás no difiere en más de 20 puntos.

   Cumplió en el reparto 163.
3. **Talla:** distribución normal por sexo (hombres 1,72 m, DE 7,5 cm; mujeres 1,59 m, DE 7 cm; Chile ENS y
   NHANES quedan a ambos lados), acotada a 2,2 DE, con 1 cm menos por década desde los 50.
4. **Peso:** IMC uniforme dentro de la clase × talla². Ningún par de pacientes coincide en peso y talla.
5. **Cómo se obtuvo cada dato:**
   - Paciente alerta y estable: medido en triage.
   - Alerta pero muy enfermo: referido por el paciente o por el familiar que lo acompaña.
   - No puede responder: referido por el familiar que vino o, si nadie presente lo sabría, estimado por el
     equipo.

**Lo que no se hizo:**
- no se cambió ningún antecedente;
- ningún peso se eligió para salvar una foto;
- nadie quedó con peso normal por quimioterapia, alcohol o baja ingesta. `pulmonary_embolism_61m` salió con
  sobrepeso y `hypoglycemia_54m_thiamine` con peso normal, ambos por sorteo.

«Real ÷ ideal» ≥ 1,30 marca los 16 pacientes en que el lector pregunta el tipo de peso (sección 3).

| Caso | Edad · sexo | Contextura | Peso | Talla | IMC | Peso ideal/predicho | Real ÷ ideal | Cómo se obtuvo |
|---|---|---|---|---|---|---|---|---|
| `pneumonia_46f` | 46 · F | normal | 58 kg | 1,59 m | 22,9 | 51,5 kg | 1,13 | medido en triage |
| `pneumonia_83m` | 83 · M | sobrepeso | 77 kg | 1,71 m | 26,3 | 66,9 kg | 1,15 | referido por su hija |
| `pulmonary_edema_58m` | 58 · M | sobrepeso | 75 kg | 1,66 m | 27,2 | 62,4 kg | 1,20 | referido por el paciente |
| `pulmonary_edema_75f` | 75 · F | obesidad III | 120 kg | 1,66 m | 43,5 | 57,9 kg | 2,07 **(pregunta)** | referido por el paciente |
| `acs_54m_inferior` | 54 · M | obesidad I | 85 kg | 1,62 m | 32,4 | 58,7 kg | 1,45 **(pregunta)** | medido en triage |
| `acs_66f_nonst` | 66 · F | normal | 50 kg | 1,59 m | 19,8 | 51,5 kg | 0,97 | medido en triage |
| `acs_61m_posterior` | 61 · M | obesidad I | 99 kg | 1,72 m | 33,5 | 67,8 kg | 1,46 **(pregunta)** | medido en triage |
| `acs_52m_de_winter` | 52 · M | obesidad II | 96 kg | 1,62 m | 36,6 | 58,7 kg | 1,64 **(pregunta)** | medido en triage |
| `acs_48m_wellens` | 48 · M | obesidad I | 75 kg | 1,57 m | 30,4 | 54,2 kg | 1,38 **(pregunta)** | medido en triage |
| `acs_70f_left_main` | 70 · F | sobrepeso | 60 kg | 1,43 m | 29,3 | 36,9 kg | 1,63 **(pregunta)** | medido en triage |
| `pulmonary_embolism_33f` | 33 · F | normal | 47 kg | 1,54 m | 19,8 | 47,0 kg | 1,00 | medido en triage |
| `pulmonary_embolism_61m` | 61 · M | sobrepeso | 83 kg | 1,69 m | 29,1 | 65,1 kg | 1,27 | referido por el paciente |
| `asthma_24f` | 24 · F | sobrepeso | 83 kg | 1,70 m | 28,7 | 61,5 kg | 1,35 **(pregunta)** | medido en triage |
| `asthma_49m` | 49 · M | normal | 76 kg | 1,75 m | 24,8 | 70,6 kg | 1,08 | referido por su pareja |
| `gi_bleed_57m` | 57 · M | obesidad II | 111 kg | 1,76 m | 35,8 | 71,5 kg | 1,55 **(pregunta)** | referido por el paciente |
| `gi_bleed_72f` | 72 · F | sobrepeso | 75 kg | 1,65 m | 27,5 | 57,0 kg | 1,32 **(pregunta)** | medido en triage |
| `hypoglycemia_28m` | 28 · M | obesidad I | 102 kg | 1,73 m | 34,1 | 68,7 kg | 1,48 **(pregunta)** | estimado por el equipo |
| `hypoglycemia_76f` | 76 · F | obesidad I | 89 kg | 1,62 m | 33,9 | 54,2 kg | 1,64 **(pregunta)** | referido por su hijo |
| `hypoglycemia_54m_thiamine` | 54 · M | normal | 77 kg | 1,89 m | 21,6 | 83,3 kg | 0,92 | estimado por el equipo |
| `opioid_35m` | 35 · M | sobrepeso | 81 kg | 1,67 m | 29,0 | 63,3 kg | 1,28 | estimado por el equipo |
| `opioid_67f` | 67 · F | obesidad I | 82 kg | 1,55 m | 34,1 | 47,9 kg | 1,71 **(pregunta)** | referido por su cónyuge |
| `anaphylaxis_29f` | 29 · F | sobrepeso | 73 kg | 1,65 m | 26,8 | 57,0 kg | 1,28 | referido por el paciente |
| `anaphylaxis_63m_betablocked` | 63 · M | obesidad II | 115 kg | 1,72 m | 38,9 | 67,8 kg | 1,70 **(pregunta)** | referido por su esposa |
| `renal_colic_34m` | 34 · M | obesidad II | 109 kg | 1,68 m | 38,6 | 64,2 kg | 1,70 **(pregunta)** | medido en triage |
| `obstructive_pyelonephritis_58f` | 58 · F | sobrepeso | 78 kg | 1,69 m | 27,3 | 60,6 kg | 1,29 | medido en triage |
| `bradycardia_ccb_68m` | 68 · M | normal | 65 kg | 1,71 m | 22,2 | 66,9 kg | 0,97 | referido por su hija |
| `bradycardia_avb3_78f` | 78 · F | normal | 54 kg | 1,55 m | 22,5 | 47,9 kg | 1,13 | referido por su hijo |
| `bradycardia_bb_54f` | 54 · F | sobrepeso | 64 kg | 1,47 m | 29,6 | 40,6 kg | 1,58 **(pregunta)** | referido por su pareja |
| `bradycardia_hyperk_63m` | 63 · M | obesidad III | 122 kg | 1,64 m | 45,4 | 60,6 kg | 2,01 **(pregunta)** | medido en la balanza de la camilla; talla referida por el paciente; peso seco previo 117 kg (registro de diálisis) |
| `trauma_limb_hemorrhage_27m` | 27 · M | sobrepeso | 74 kg | 1,66 m | 26,9 | 62,4 kg | 1,19 | referido por el paciente |
| `trauma_hemothorax_41m` | 41 · M | normal | 56 kg | 1,70 m | 19,4 | 66,0 kg | 0,85 | referido por el paciente |

**Revisa en particular:**
- **`bradycardia_hyperk_63m`:** el peso seco previo (117 kg) lo derivé del antecedente de dos sesiones de
  diálisis perdidas con ingesta habitual: 5 kg sobre el peso seco. Es un dato nuevo, coherente con el caso, pero
  tuyo.
- **Tallas extremas:** hay dos mujeres de 1,43 y 1,47 m (70 y 54 años). Son plausibles, sobre todo en Santiago,
  y hacen visible el peso predicho bajo.

## 2. Qué ve el residente

- **Ficha → «Weight and height»**, en el panel del lado de la cama, con traducción al español. Por ejemplo:
  - «Weight 122 kg (measured on the bed scale)»
  - «Previous dry weight 117 kg (his dialysis unit's record, before the two missed sessions; not today's
    weight)»
  - «Weight 102 kg (estimated by the team; the patient could not be weighed)»
- **Dosis por kilo:** ya no se pregunta el peso que está en la ficha. La orden muestra el peso usado, su tipo y
  su origen, por ejemplo «enoxaparin 47 mg SC administered (1 mg/kg × 47 kg, actual body weight, measured at
  triage)». Una infusión muestra además cuánto es por minuto: «0.1 mcg/kg/min × 83 kg = 8.3 mcg/min».
- **Volumen corriente:** «Vt 8 mL/kg (8 mL/kg × 61.5 kg = 492 mL, on the predicted body weight: 45.5 + 0.91 ×
  (170 − 152.4) = 61.5 kg)».
- **Peso y talla no cambian durante el encuentro.** Si el residente escribe otro peso junto a la orden, se dosifica
  con el suyo y el registro dice «the chart records 47 kg».

## 3. Reglas aplicadas

**A. Ficha.** Descrita arriba. El peso seco nunca se usa como peso actual, salvo que el residente lo pida por
nombre.

**B. Volumen corriente** (`asthma_ventilation.settings`):
- Un volumen en mL/kg se calcula sobre el peso predicho (Devine/ARDSNet): hombres 50 + 0,91 × (talla en cm −
  152,4); mujeres 45,5 + 0,91 × (…). El registro muestra la fórmula.
- Si el residente nombra otro tipo de peso («6 ml/kg de peso real»), se respeta.
- **Un volumen absoluto se conserva tal como se escribió.** Esto corrigió un defecto: al pasar de mL/kg a mL en
  un ajuste, el valor por kilo arrastrado sobrescribía el absoluto.
- No cambian la ventilación minuto requerida ni el volumen corriente por defecto (sección 4).

**F. Dosis por kilo** (`weight_based_doses`). El peso sale, en este orden, de:
1. el tipo de peso que el residente escribe con la orden;
2. el que eligió antes en el encuentro para el mismo fármaco y la misma clase de orden (un bolo y una infusión
   del mismo agente son órdenes distintas: la elección de una no se extrapola a la otra);
3. una regla acordada para ese fármaco y contexto (hoy ninguna, salvo B);
4. el peso real de la ficha, dicho en el registro.

**La pregunta (revisada el 2026-09-26, punto 1 de tu instrucción).** El desnivel real/ideal ya no pregunta por
sí solo. Sin tipo nombrado ni regla acordada, la dosis corre sobre el peso real de la ficha; cuando el desnivel
es material (real ≥ 1,30 × ideal), el registro añade que es la convención del motor mientras el tipo de peso del
fármaco está pendiente, y la observación queda marcada para el alcance de la evaluación (`model_conventions`).
El lector pregunta sólo cuando falta un dato que una regla o un tipo nombrado necesitan (la talla para un peso
ideal; un peso seco no registrado), conservando la orden completa, sin mover el reloj y pidiendo únicamente el
dato faltante; una orden nueva completa reemplaza a la retenida en vez de repetirse la pregunta. Los encuentros
lanzados bajo la primera revisión del sello («2026-09-27») conservan su pregunta de entonces, para que lo
guardado se reproduzca igual; el sello vigente es «2026-09-27.2».

**Un mismo efecto por la misma cantidad.** El efecto simulado se mide contra un único peso por paciente: el real
de la ficha, como convención provisional hasta que decidas C y E. Así, 56,4 mg de rocuronio duran lo mismo
escritos como «1,2 mg/kg» que como «56,4 mg». Ninguna regla de evaluación juzga dosis por kilo de forma directa,
pero la convención tiene efectos indirectos (sección 6, redacción corregida): por eso cada encuentro lista sus
observaciones dependientes de convenciones en el Faculty Brief y junto a la rúbrica.

**Defectos corregidos de paso**, porque tocaban la interpretación del peso:
- «SF 30 ml/kg» se leía como 30 mL; ahora es 30 mL/kg sobre el peso.
- Una sedación en mg/kg/min se dividía dos veces por el peso.

**Coherencia necesaria al agregar el peso.** La dobutamina por kilo se convierte y se mide con el mismo peso. Sin
esto, un «5 mcg/kg/min» en un paciente de 122 kg se habría convertido con 122 kg y medido contra 70 kg.

**Encuentros anteriores.** Un encuentro lanzado antes del 2026-09-27 no lleva la marca `weight_rules` y sigue con
sus reglas: 70 kg para la fisiología y la pregunta del peso para las dosis por kilo. Los guardados no se tocan ni
se recalculan.

## 4. Decisiones clínicas pendientes

Nada de esto cambió de forma automática. Mientras decides, cada punto sigue la convención indicada en
«Comportamiento actual», visible en el registro.

**Cómo leer las fuentes.** Las reunió un agente de búsqueda. El proxy bloqueó la lectura directa de PubMed y de
las revistas, así que cada fuente se comprobó por su título, su identificador y el resumen, no por el texto
completo. Por eso lo marcado «(dato sin confirmar)» es sólo un número o una conclusión que no pudo cotejar; la
fuente en sí existe.

| Decisión | Comportamiento actual | Propuesta | Fuente | Efecto sobre el caso | Posible impacto en la evaluación |
|---|---|---|---|---|---|
| **VM requerida** (gases del asma) | 0,10 L/kg/min × 70 kg de referencia, igual que antes | 0,10 L/kg/min × **peso predicho**, el mismo peso del Vt por kilo | Fisiología: la producción de CO2 sigue a la masa metabólica, no a la grasa. No hay ensayos; ~100 mL/kg PBW/min vale sólo como punto de partida en no obesos | Ver nota 1 | Ninguna regla usa la PaCO2; el texto de hipercapnia aparece sobre 90 mmHg |
| **Vt por defecto** (intubación sin Vt escrito) | 8 mL/kg × 70 kg = 560 mL para todos | 6–8 mL/kg de **peso predicho**, o dejar 560 mL como «ajuste de fábrica» visible | ARDSNet, NEJM 2000;342:1301 (6 mL/kg PBW en SDRA; 6–8 fuera de SDRA, evidencia moderada) | `asthma_24f`: 492 mL en vez de 560; `asthma_49m`: 565 | Indirecto: más Vt, más atrapamiento y presión meseta en el modelo |
| **C · Rocuronio, secuencia rápida** | Dosis por kilo sobre peso real si no se nombra otro, con pregunta si real ≥ 1,3 × ideal. Duración medida sobre peso real | Ver nota 2 | Ver nota 2 | `bradycardia_hyperk_63m`: 1,2 mg/kg de peso ideal = 73 mg → hoy 27 min de bloqueo; medido sobre peso ideal serían 54 min | Indirecto: parálisis sin sedación, apnea sin ventilar |
| **C · Rocuronio/vecuronio, bolos posteriores** | Igual | Peso ideal o magro, titulado por tren de cuatro | Schwartz, Anesth Analg 1992;74:515 (vecuronio: farmacocinética similar normalizada a peso ideal); SCCM/ASHP 2016 | Duración de cada bolo | Igual |
| **C · Bloqueante en infusión** | No modelado como infusión | Peso ideal o ajustado, o tasa fija | SCCM/ASHP, Crit Care Med 2016;44:2079 (recomendación débil); ACURASYS y ROSE: cisatracurio 37,5 mg/h fijo | — | — |
| **C · Succinilcolina** | Peso real (pregunta si relevante) | Acordar **peso real** 1–1,5 mg/kg; así deja de preguntarse | Lemmens y Brodsky, Anesth Analg 2006;102:438 (ECA, n=45: con peso ideal, un tercio con malas condiciones) | Ninguno | Ninguno |
| **D · Diuresis basal** | 1,0 mL/kg/h × 70 kg = 70 mL/h, reducida por la carga circulatoria, más furosemida. La creatinina sólo reduce la respuesta a la furosemida. **Desde el 2026-09-26 (punto 4)**: un caso puede declarar su función renal basal (`engine.renal`): «minimal» (participación residual del 10%, convención provisional del simulador) o una basal absoluta en mL/h. El caso en diálisis la declara: hace ~7 mL/h, no 70, y la furosemida responde en esa proporción. La cifra exacta del residuo sigue siendo tuya | Ver nota 3 | KDIGO 2012 (0,5 mL/kg/h; no dice qué peso). Con peso real se sobrediagnostica oliguria en obesos (evidencia baja) | El paciente de 122 kg en diálisis ya no contradice su historia | La convención residual aparece en el Brief cuando el encuentro tocó la diuresis |
| **E · Noradrenalina y adrenalina** | mcg/kg/min × peso real → mcg/min. El efecto sale de los mcg/min absolutos (calibrados a 70 kg) | Referencia en mcg/min; si se escribe por kilo en obesidad, sobre peso ideal o ajustado | Radosevich, Am J Crit Care 2016;25:27 y Vadiei, Ann Pharmacother 2017;51:194 (observacionales, evidencia baja) | `anaphylaxis_63m` (115 kg): 0,1 mcg/kg/min = 11,5 mcg/min real (+13,8 mmHg) o 6,8 ideal (+8,1) | Indirecto: hipotensión sostenida |
| **E · Dobutamina** | mcg/kg/min sobre peso real; efecto por kilo del mismo peso | Peso real con tope, o ideal | Muy poca evidencia | Igual respuesta por kilo en cualquier peso | Indirecto |
| **E · Sedantes en infusión** | Por kilo sobre peso real; costo en PA medido sobre peso real | Ver nota 4 | Ingrande, Anesth Analg 2011;113:57 (propofol: inducción con peso magro); Servin, Anesthesiology 1993;78:657 (mantención con peso corregido) | Sólo cambia la PA (propofol: 12 mmHg a 3 mg/kg/h) | Indirecto |
| **Cristaloide 30 mL/kg** | Peso real (pregunta si relevante). Antes se leía como 30 mL | Peso ajustado si IMC > 30, o peso real | Surviving Sepsis 2021 no fija el peso; la medida SEP-1 acepta el ideal (evidencia muy baja, contradictoria) | `obstructive_pyelonephritis_58f`: 2340 mL real, 1818 ideal | Trauma: más de 2000 mL de cristaloide sin sangre se señala (cifra absoluta) |
| **Anticoagulantes** | Peso real (pregunta si relevante) | Acordar **peso real**: enoxaparina 1 mg/kg sin tope (0,8 mg/kg con anti-Xa si IMC ≥ 40); heparina en SCA 60 U/kg (máx. 4000) y 12 U/kg/h (máx. 1000) | Guía ACC/AHA SCA sin SDST 2014; ASH 2018 | La exposición anticoagulante del motor sigue los mg | Ninguno |
| **Umbral de la pregunta** | **Resuelto el 2026-09-26 (punto 1): retirado como disparador universal.** Sin tipo nombrado ni regla acordada, la dosis corre sobre el peso real y el registro declara la convención como decisión pendiente; los encuentros de la primera revisión conservan su pregunta | — | — | El umbral 1,30 sólo marca cuándo la diferencia es material para el registro y el alcance de la evaluación | La nota de convención aparece en el Brief y junto a la rúbrica |
| **Casos generados por IA** | **Resuelto el 2026-09-26 (punto 2): esquema v4** exige peso y talla con su origen; misma interpretación que el banco. Los generados antes de v4 conservan su versión histórica (talla no registrada; un tipo de peso que la necesite pregunta el dato faltante) | — | — | Sólo casos generados nuevos | — |
| **Peso seco en diálisis** | **Retirado el 2026-09-26 (punto 7): no registrado.** Los 117 kg eran una inferencia (122 − 5), no un antecedente. La ficha no muestra peso seco y una dosis «de peso seco» pregunta el dato faltante | Definir el peso seco del caso, con fuente propia del caso, si quieres que exista | — | Dato de la ficha; nada se dosifica con él | Ninguno |

**Nota 1 · Ventilación minuto requerida.** B ya aplicado cambia cuánto ventila un «8 mL/kg»: ahora sigue al peso
predicho. Si la ventilación requerida se queda en 70 kg, un paciente de talla baja ventila menos que antes para
la misma demanda. Con los gases del modelo, «8 mL/kg, FR 12, flujo 80» en la llegada (obstrucción máxima) da esta
PaCO2 (mmHg):

| Caso | Antes del cambio | VM en 70 kg (hoy) | VM en predicho | VM en real | VM en ajustado |
|---|---|---|---|---|---|
| `asthma_24f` (83 kg, predicho 61,5) | 52,2 | 59,3 | **52,1** | 70,3 | 59,4 |
| `asthma_49m` (76 kg, predicho 70,6) | 52,2 | 51,5 | **51,9** | 55,9 | 53,5 |

- **Con la VM en peso predicho**, una orden por kilo deja prácticamente la misma PaCO2 que antes en cualquier
  talla (52,1 y 51,9 frente a 52,2). Es la opción que no introduce ventajas ni castigos ocultos.
- **Con la VM en peso real**, un obeso necesitaría mucha más ventilación que la que el Vt por peso predicho le da.
- **Con Vt absolutos** (por ejemplo 450 mL, FR 12), nada cambió respecto de antes (64,8 mmHg). Con la VM en peso
  predicho, `asthma_24f` bajaría a 56,9.

**Nota 2 · Rocuronio en secuencia rápida.**
- **Evidencia de secuencia rápida en obesidad:** tres estudios pequeños y una cohorte de urgencia; casi todo lo
  demás viene de cirugía programada a 0,6 mg/kg, con la duración como resultado.
- **Alternativas defendibles:**
  - **(a) peso real, 1,0–1,2 mg/kg.**
    - La ficha técnica (Pfizer) dosifica sobre peso real. Con peso ideal, los obesos tardaron más, duraron menos
      y no lograron condiciones comparables.
    - Leykin, Anesth Analg 2004;99:1086: 0,6 mg/kg real dura 55 min, frente a 22 min con el ideal.
  - **(b) peso ideal o magro, con al menos 1,2 mg/kg.**
    - Gaszynski, Eur J Anaesthesiol 2011: 1,2 mg/kg de peso ideal en secuencia rápida dio buenas condiciones a los
      60 s, salvo en 2 pacientes (n sin confirmar).
    - McDowell, West J Emerg Med 2024;25:22 (urgencia, n=96): condiciones excelentes en 68,5% con peso real y
      73,8% con peso ideal, sin demostrar no inferioridad. La parálisis fue más corta con el ideal.
  - **(c) peso ajustado.** Meyhoff, Anesth Analg 2009: inicio y condiciones similares; duración creciente con el
    peso.
- **Evidencia en contra de bajar la dosis:**
  - de Almeida 2009: con 0,6 mg/kg de peso ideal, las condiciones a los 60 s no fueron aceptables.
  - En intubación de urgencia, las dosis mayores a 1,2 mg/kg de peso real se asociaron a más éxito al primer
    intento (April, AJRCCM 2026, n=1822; registro NEAR, CJEM 2021).
- **Lo que no se debe hacer:** extrapolar de bloqueo sostenido a secuencia rápida. El inicio depende de la dosis,
  así que usar peso ideal sólo es defendible si se sube a mg/kg ≥ 1,2.
- **Para el simulador**, una opción coherente:
  - si no se nombra, la dosis se convierte sobre peso real;
  - el efecto (duración) se mide sobre peso ideal;
  - una dosis de 1,2 mg/kg real en un obeso dura más, que es lo que describe la literatura.

**Nota 3 · Diuresis.**
- **Qué representa hoy:** una diuresis adulta fija de 70 mL/h (1 mL/kg/h de un adulto de 70 kg) que cae con la
  carga circulatoria (1,6 de la basal por unidad de carga, hasta cero) y sube con la furosemida. La creatinina sólo
  reduce la respuesta a la furosemida, no la basal. No cambia con el peso de la ficha.
- **Hueco:** el caso en diálisis, anúrico por historia («I pass almost no urine»), produce los mismos 70 mL/h que
  cualquier otro al llegar: el modelo no tiene función renal basal ni anuria.
- **Simplificación coherente:**
  - diuresis basal absoluta como convención explícita (70 mL/h adulto, o 1 mL/kg/h de peso predicho, que da 55–85
    mL/h);
  - modulada por perfusión, función renal y respuesta a volumen y diurético;
  - anuria explícita en ERC terminal;
  - mostrar mL/h y, si quieres, mL/kg/h sobre peso ideal y real.

**Nota 4 · Sedantes, por fármaco:**
- **Propofol:** inducción con peso magro; mantención con peso ajustado.
- **Midazolam:** bolo con peso real o ajustado y titular; infusión con peso ideal o ajustado.
- **Dexmedetomidina:** peso ajustado.
- **Ketamina:** peso ideal o ajustado.
- **Fentanilo:** bolo con peso magro (el real es aceptable en dosis única); infusión con peso magro o ideal.
- **Morfina:** dosis fijas tituladas.

La evidencia es baja o muy baja en todos; para una decisión conviene fijar sólo los que el motor modela con efecto:
propofol, midazolam, dexmedetomidina, fentanilo y ketamina en infusión.


## 5. Imágenes

**La regla nueva** (`image_identities.compatible`):
- **De una foto no se deduce un peso.** La sala encuadra al paciente de pecho hacia arriba, en cama y bajo la
  frazada: se ven cara, cuello, hombros, brazos y manos, y la talla no se aprecia acostado.
- **Se descarta sólo una contradicción clara** entre el cuerpo que muestra la foto y el peso y la talla de la ficha.
  Los rangos de IMC por contextura aparente son amplios:

  | Contextura aparente | IMC que puede representar |
  |---|---|
  | Delgada | < 28 |
  | Promedio | 17 a < 35 |
  | Más robusta | 22 a < 40 |
  | Obesa | ≥ 27 |
  | Obesa severa | ≥ 33 |

- **Desde el 2026-09-26 (punto 6): los rangos orientan, no excluyen por sí solos.** Una ficha a menos de 2
  puntos de IMC del rango de una contextura es una diferencia pequeña alrededor de un límite: la foto sigue
  usable, ordenada tras cualquier ajuste mejor (núcleo → rango → borde), y nunca motiva pagar un reemplazo.
  Sólo más allá de ese margen la contradicción es clara y excluye. De una foto no se deduce un peso exacto.
- **Entre dos personas que sirven**, primero la de cuerpo más cercano a la ficha, pero después de lo ya guardado:
  nunca se paga una foto sólo por estar más cerca.
- La identidad se mantiene durante todo el encuentro.

**Contextura aparente de las 22 personas fotografiadas.** Es una lectura mía, para tu revisión, no un peso:

| Se ven | Personas |
|---|---|
| Delgadas o en forma | V02, V03, V05, V09, V14, V17, V21, V29 |
| Promedio | V11, V12, V18, V22, V23, V24, V26, V27 |
| Más robustas | V01, V08, V19 |
| Obesas | V33, V35 |
| Obesa severa | V38 |

**Reevaluación.**
- **Los 12 casos que la regla de 15 kg dejaba sin foto:** con la tabla nueva y la compatibilidad amplia, 8
  conservan la suya (`pneumonia_46f`, `acs_66f_nonst`, `acs_61m_posterior`, `acs_48m_wellens`, `asthma_49m`,
  `opioid_35m`, `bradycardia_ccb_68m`, `trauma_hemothorax_41m`). Otros 4 sí la perdían por una contradicción
  clara.
- **Con la tabla nueva, 2 casos más** quedaron contradichos: `asthma_24f` (V03, muy delgada, para 83 kg y 1,70 m)
  y `bradycardia_hyperk_63m` (122 kg).
- **Sustituciones necesarias: 6.** No se generó nada por superar un umbral sin contradicción:

| Caso | Contradicción | Sustituta | Resultado |
|---|---|---|---|
| `gi_bleed_57m` (111 kg, IMC 35,8) | cuerpo promedio | V38 | foto nueva, aceptada |
| `bradycardia_hyperk_63m` (122 kg, IMC 45,4) | cuerpo promedio | V38 | la misma foto: igual estado de llegada, sin costo |
| `anaphylaxis_63m_betablocked` (115 kg, IMC 38,9) | cuerpo promedio | V38 | foto nueva, aceptada; no se ve el enrojecimiento |
| `renal_colic_34m` (109 kg, IMC 38,6) | cuerpo delgado | V19 | foto nueva, aceptada; la cara no muestra el malestar marcado |
| `bradycardia_bb_54f` (64 kg, 1,47 m, IMC 29,6) | cuerpo muy delgado | V08 | foto nueva, aceptada |
| `asthma_24f` (83 kg, 1,70 m) | cuerpo muy delgado | V01 (nueva) | referencia aceptada; las dos de llegada, rechazadas por el revisor (ver abajo) |

- **Costo:** US$0,64 y 7 solicitudes del saldo de la segunda autorización, que queda en US$3,64 y 23
  solicitudes. La tercera autorización (US$10, tope de 100 solicitudes) quedó registrada y sin gasto.
- **V38 es ahora la llegada de tres diagnósticos distintos**: no queda asociada a uno solo.
- **`pulmonary_edema_75f`** (120 kg) nunca tuvo foto. Sus dos candidatas (V11 y V12, contextura promedio)
  siguen fuera incluso con los rangos como orientación (IMC 43,5, contradicción clara). El 2026-09-26
  autorizaste que una imagen nueva no quede excluida del trabajo autorizado y la **tanda 7 corrió**: V34
  (identidad nueva, obesa, edad compatible), referencia y llegada generadas con el saldo de la segunda
  autorización y aceptadas por el revisor automático. **Aprobadas en las dos revisiones a tu pedido en el
  chat del 2026-09-26** («soluciona esos dos, aprueba»; `docs/IMAGENES_REGISTRO.md`): el caso ya muestra a
  V34. En el mismo pedido quedó aprobada la V01 `61898a34` de `asthma_24f`, por sobre el revisor automático
  conforme a la decisión 5. V12 mantiene su aprobación anterior para los casos donde su contextura sí
  calza; `compatible()` la excluye de éste sin tocar esa aprobación.

**Revisión por clases**, siguiendo tu criterio. Nada se rechazó por una cara tranquila o la boca cerrada, y ninguna
foto se leyó como prueba de una frecuencia respiratoria.

- **Compatible y completa:**
  - las 18 fotos de referencia;
  - los estados de V09 (`6b6eca45`), V11 (`ec9315a6`, `a734490c`), V12 (`fa2a94af`, `f69b7508`), V14
    (`ab017b3c`), V17 (`c0d772c1`), V18 (`a0ad2024`), V22 (`791a32bd`), V23 (`ad05d22b`, `2f626c73`), V24
    (`92c0a925`, `ed245064`), V26 (`df73eae5`), V27 (`868e3acf`) y V08 (`451721dd`).
- **Compatible, que necesita el monitor o el examen:** desde el 2026-09-26 (punto 6 de tu instrucción) la sala
  muestra junto a **toda** foto vigente la misma frase neutral («A still photograph does not show every clinical
  sign; examine the patient to assess what it cannot carry»), sin nombrar qué hallazgos faltan: nombrarlos
  revelaba qué define el caso antes de examinar. Los códigos específicos de esta tabla siguen guardándose en el
  registro de visualizaciones del encuentro y se muestran en tu portal de revisión.

  | Foto | No muestra |
  |---|---|
  | V02 `b5db3e20` (anafilaxia) | color de piel, esfuerzo |
  | V03 `f7b26ce2` (asma) | grado de malestar, esfuerzo |
  | V05 `5b68b30e` | malestar, esfuerzo |
  | V09 `88ab1e0e` | esfuerzo |
  | V17 `6138b1dc` (cólico) | malestar |
  | V21 `9cf84f16` | malestar, esfuerzo |
  | V21 `ca87e8ee` | malestar |
  | V26 `f9076976` (anafilaxia) | color de piel, esfuerzo |
  | V29 `e0fe0c84` | esfuerzo |
  | V19 `5653104a` (cólico, nueva) | malestar |
  | V38 `d230e5a6` (anafilaxia, nueva) | color de piel, esfuerzo |
  | V38 `9f73fef3` (nueva) | malestar |

  Son lecturas mías (`assets/patient_images/observations.json`), no revisiones.
- **Contradice claramente el estado:** ninguna de las pendientes. Las que sí contradicen ya estaban excluidas:
  - las diez con mascarilla de reservorio mal dibujada;
  - las cuatro de sudor marcado en piel oscura (decisión 6).

**Revisión (estado al 2026-09-26):**
- Las 46 fotos pendientes quedaron aprobadas en el lote que pediste el 2026-09-26 (`a2928f6`), y V34 y la
  V01 `61898a34` a tu pedido del mismo día en el chat («soluciona esos dos, aprueba»).
- **La llegada de `asthma_24f`: V01 `61898a34`.** El revisor automático la había rechazado por no ver tensión en
  cuello y hombros; es compatible pero parcial (el esfuerzo se evalúa al examinar). Aprobada en ambas revisiones
  a tu pedido, la sala la usa (decisión 5).
  - La otra, `452a7e36`, tiene equipo en la pared: sigue excluida y sin aprobar.
  - No se pagaron más intentos: el generador no dibuja bien el esfuerzo respiratorio marcado.
- **Las lecturas de contextura aparente** de la tabla de arriba: si alguna te parece mal, cambia qué casos puede
  mostrar esa persona.


## 6. Comprobaciones

Las comprobaciones que pediste en el punto 6. Reutilicé encuentros y pruebas guardadas donde las había.

| Comprobación | Cómo | Resultado |
|---|---|---|
| Peso y talla accesibles y consistentes en ficha, cálculos y documentación | `test_weight_and_height`: la tabla es el sorteo, la ficha rotula estimados y peso seco, y el motor usa el mismo número. La tabla de este documento sale de `patient_body.BODIES` | Pasa |
| El Vt por kilo usa el peso predicho | Pruebas de fórmula, de tipo de peso nombrado y de encuentro anterior (sigue en 70 kg) | Pasa |
| Dosis absolutas y tipos de peso explícitos se respetan | Vt absoluto conservado (defecto corregido); «peso real / ideal / ajustado / seco» en la orden; peso escrito con la orden; la misma cantidad tiene el mismo efecto | Pasa |
| Sin penalizaciones por supuestos ocultos | Ver lista abajo | **Corregido el 2026-09-26: la afirmación original era demasiado fuerte.** Que la rúbrica no puntúe mg/kg no elimina los efectos indirectos: una convención del motor cambia gases, presión, duración del bloqueo o diuresis, y por esa vía las decisiones posteriores y su lectura. Ahora cada encuentro lista sus observaciones dependientes de convenciones pendientes en el Faculty Brief y junto a la sugerencia de rúbrica (`model_conventions`), con la regla de no fundar una deficiencia sólo en ellas |
| Encuentros previos: datos y evaluaciones originales | Encuentro guardado el 2026-09-25 (`opioid_67f`): 10 órdenes (dosis por kilo, infusiones, bloqueante, sedación) desde su lanzamiento y desde su estado guardado, con el código anterior y el nuevo | Salida idéntica. Además, ningún código escribe un registro guardado y la base de evaluación sigue congelada |
| La selección de imágenes no depende de 15 kg | `test_image_identities`: la constante y sus funciones ya no existen; todo caso tiene alguien compatible; la persona más cercana va primero sin pagar | Pasa |

**Supuestos ocultos y efectos indirectos (redacción corregida el 2026-09-26):**
- Ninguna regla de evaluación juzga dosis, volúmenes, ventilación ni diuresis por kilo de forma directa. Lo
  revisé en rúbricas, declaraciones y análisis.
- **Pero los efectos indirectos existen**: una convención del motor puede cambiar gases, presión arterial,
  duración del bloqueo o evolución clínica y, por esa vía, afectar decisiones posteriores del residente y su
  evaluación. La afirmación original («sin penalizaciones») era demasiado fuerte.
- Desde el 2026-09-26, `model_conventions` identifica por encuentro las observaciones que dependen de una
  convención pendiente (tipo de peso por fármaco, efecto de infusiones, duración del bloqueante, VM y Vt por
  defecto, diuresis basal) y las muestra en el Faculty Brief y junto a la sugerencia de rúbrica, con su decisión
  pendiente y esta regla: no fundar una deficiencia sólo en una de esas salidas; el resto del encuentro se evalúa
  como siempre. El alcance es la observación, nunca el dominio completo.
- Hipoglicemia: ninguna de las 60 trayectorias registradas cambió; sólo aparece el campo nuevo `/patient/body`,
  declarado en el registro de correcciones.
- Los 11 guiones piloto conservan el estado de evaluación que declaran.

**Pruebas:**
- **Suite completa**, en cuatro partes:
  - **4427 pruebas pasan**, 77 omitidas por diseño y 2 fallas esperadas y marcadas. Las 453 afectadas por los
    últimos ajustes pasaron de nuevo.
  - **1 falla que no viene de este cambio:** `test_problem_launch::test_new_ai_case_is_persisted_and_resumed_without_reauthoring`.
    Falla sólo si corre después de `test_cognitive_encounters.py` en el mismo proceso, y falla igual con el código
    anterior en ese orden. Sola y en su propio archivo pasa. Queda como hallazgo 6 abajo.
- **Regresiones antiguas:** 56 de 56.
- **Lote de 20:** el escenario 19 (anafilaxia, 115 kg, adrenalina en mcg/kg/min) ahora recibe la pregunta del
  peso, como debe. Agregué la respuesta del residente al guion («Peso real.» / «Actual weight.») y el ensayo se
  completa sin detenciones en español y en inglés. Ningún otro guion del lote tiene órdenes por kilo; el guion
  piloto de `pulmonary_embolism_61m` no pregunta (peso real 1,27 veces el ideal, bajo el umbral).

**Hallazgos fuera de alcance (estado al 2026-09-26,** instrucción de cierre**):**
1. **Documento A — corregido** (C-2026-09-26-13). `history_review` lee también los `encounter_events` congelados
   que la carga de análisis sí trae, y la carga nombra su caso; «The history you took» se muestra por el
   recorrido real y la prueba ya no inyecta `session`.
2. **Fentanilo — corregido** (C-2026-09-26-14). Rango propio en microgramos, etiqueta en mcg, por kilo aceptado,
   equivalencia declarada aplicada.
3. **Motor antiguo PS001/PS002 — documentado, sin corregir a propósito.** No es accesible para ningún usuario en
   la aplicación actual: el selector no ofrece PS001/PS002, `generate_problem_config` rechaza todo id fuera de
   los desafíos, la reanudación exige `mrs_attempt_v1` (sólo encuentros del currículo) y `MRS_REPLAY_CASE`
   rechaza un estado sin `encounter_spec`, que los estados PS no tienen. Sólo la suite de regresiones lo
   ejecuta. Corregir sus lecturas mg/kg sería ampliar trabajo sobre código inalcanzable (tu punto 3).
4. **Diuresis del paciente en diálisis — corregido** (C-2026-09-26-16). Función renal residual declarable;
   el caso declara «minimal» y produce ~7 mL/h, no 70.
5. **Adrenalina IM y ácido tranexámico en mg/kg — corregido** (C-2026-09-26-15). Se entienden por kilo, se
   convierten con el peso de la ficha y el rango juzga la dosis resultante abiertamente.
6. **Pruebas que dependen del orden.** Pendiente de reproducir en esta sesión (requiere pytest, bloqueado por la
   red del entorno al escribir esto); ver el informe de cierre.

